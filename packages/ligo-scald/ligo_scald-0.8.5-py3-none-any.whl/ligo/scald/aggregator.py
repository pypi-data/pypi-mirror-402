import argparse
from collections import defaultdict
import logging
import os
import time
import timeit

import numpy
import yaml

from .io import influx, kafka


def parse_timeseries(messages, topics):
    """Parses timeseries-based Kafka messages into a format for storing into influx.

    """
    data = {t: defaultdict(lambda: {'time': [], 'fields': {'data': []}}) for t in topics}

    # retrieve timeseries for all routes and topics
    for message in messages:
        try:
            job = message.key
            route = message.topic
            data[route][job]['time'].extend(message.value['time'])
            data[route][job]['fields']['data'].extend(message.value['data'])
        except KeyError: ### no route in message
            pass

    # convert series to numpy arrays
    for route in topics:
        for job in data[route].keys():
            data[route][job]['time'] = numpy.array(data[route][job]['time'])
            data[route][job]['fields']['data'] = numpy.array(data[route][job]['fields']['data'])

    return data


def parse_triggers(messages):
    """Parses trigger-based Kafka messages into a format for storing into influx.

    """
    triggers = []
    for message in messages:
        triggers.extend(message.value)
    return triggers


def _add_parser_args(parser):
    parser.add_argument('-c', '--config',
                        help="sets dashboard/plot options based on yaml configuration. if not set, uses SCALDRC_PATH.")
    parser.add_argument('-b', '--backend', default='default',
                        help="chooses data backend to use from config. default = 'default'.")
    parser.add_argument('-d', '--data-type', default='timeseries',
                        help = "Sets the data type of metrics expected from [timeseries|triggers]. default = timeseries.")
    parser.add_argument('-u', '--uri', default='kafka://localhost:9092',
                        help="specify Kafka URI to read metrics from. default = kafka://localhost:9092.")
    parser.add_argument('-t', '--topic', action='append',
                        help="Specify topic to aggregate from. Can be given multiple times.")
    parser.add_argument('-s', '--schema', action='append',
                        help=("Specify schema corresponding to a topic to aggregate. Can be given multiple times. "
                              "If specified, needs to map one-to-one with topics. Else, assume schemas and topics are identical."))
    parser.add_argument('--across-jobs', action = 'store_true',
                        help = "If set, aggregate data across jobs as well.")
    parser.add_argument('--processing-cadence', default = 0.5,
                        help = "Rate at which the aggregator acquires and processes data. default = 0.5 seconds.")
    parser.add_argument('-v', '--verbose', action = 'store_true', help = 'Be verbose.')
    parser.add_argument('--tag', action = 'append', default = [], help = 'Set of tags to consume from kafka. Can be given multiple times.')


def main(args=None):
    """Aggregates and stores metrics to a data backend

    """
    if not args:
        parser = argparse.ArgumentParser()
        _add_parser_args(parser)
        args = parser.parse_args()

    topics = args.topic

    # set up logging
    log_level = logging.INFO if args.verbose else logging.WARNING
    logging.basicConfig(format='%(asctime)s | %(name)s : %(levelname)s : %(message)s')
    logger = logging.getLogger('scald')
    logger.setLevel(log_level)

    # sanity checking
    assert args.data_type in ('timeseries', 'triggers'), '--data-type must be one of [timeseries|triggers]'

    if args.data_type == 'triggers':
        assert len(topics) == 1, 'only one topic allowed if --data-type = triggers'

    if args.schema:
        assert len(topics) == len(args.schema), "schemas must correspond one-to-one with topics"
        schemas = args.schema
    else:
        schemas = topics

    # load configuration
    config = None
    if args.config:
        config_path = args.config
    else:
        config_path = os.getenv('SCALDRC_PATH')
    if not config_path:
        raise KeyError('no configuration file found, please set your SCALDRC_PATH correctly or add --config param')
    with open(config_path, 'r') as f:
        config = yaml.safe_load(f)

    # instantiate a consumer to subscribe to all of our topics, i.e., jobs
    client = kafka.Client(args.uri)
    client.subscribe(set(topics))

    # set up aggregator
    aggregator_settings = config['backends'][args.backend]
    aggregator_settings['reduce_across_tags'] = args.across_jobs
    aggregator = influx.Aggregator(**aggregator_settings)

    # register measurement schemas for aggregators
    aggregator.load(path=config_path)

    # update and aggregate data continuously
    try:
        while True:
            logger.info("retrieving data from kafka")
            start = timeit.default_timer()

            msgs = [msg for msg in client.query(tags=args.tag, max_messages=2000)]
            if args.data_type == 'timeseries':
                data = parse_timeseries(msgs, topics)
            elif args.data_type == 'triggers':
                data = parse_triggers(msgs)
            else:
                raise ValueError("--data-type not a valid option")

            retrieve_elapsed = timeit.default_timer() - start
            logger.info("time to retrieve data: %.1f s" % retrieve_elapsed)

            # store and reduce data for each job
            start = timeit.default_timer()
            for topic, schema in zip(topics, schemas):
                logger.info("storing and reducing metrics for schema: %s" % schema)
                if args.data_type == 'timeseries':
                    aggregator.store_columns(
                        schema,
                        data[topic],
                        aggregate=config['schemas'][schema]['aggregate']
                    )
                elif args.data_type == 'triggers':
                    far_key = config['schemas'][schema]['far_key']
                    time_key = config['schemas'][schema]['time_key']
                    aggregator.store_triggers(
                        schema,
                        [trg for trg in data if far_key in trg],
                        far_key=far_key,
                        time_key = time_key
                    )

            store_elapsed = timeit.default_timer() - start
            logger.info("time to store/reduce %s: %.1f s" % (args.data_type, store_elapsed))

            time.sleep(max(args.processing_cadence - store_elapsed - retrieve_elapsed, 0))
    finally:
        # close client connection
        client.close()
