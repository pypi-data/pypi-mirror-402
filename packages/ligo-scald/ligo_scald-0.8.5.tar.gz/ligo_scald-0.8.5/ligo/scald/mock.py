import json

import bottle
import numpy

from . import utils

JSON_HEADER = {
    'Content-type': 'application/json',
    'Cache-Control': 'max-age=10',
}

NUM_JOBS = 200

app = bottle.Bottle()

@app.route("/query")
def mock_query():
    ### parse query
    try:
        database = bottle.request.query['db']
        query = bottle.request.query['q'].strip()
        epoch = bottle.request.query['epoch']
        start, end, measurement, fields, aggregate, tags, filters, latest, groupby = translate_query(query)
    except AssertionError as e:
        return bottle.HTTPResponse(status=400, headers=JSON_HEADER, body=json.dumps({'error': str(e), 'query': repr(query)}))

    start = utils.unix_to_gps(start)
    end = utils.unix_to_gps(end)

    ### parse qualified measurement
    _, measurement = measurement.split('.', 1)
    rp, meas_name = measurement.rsplit('.', 1)
    meas_name = meas_name.strip('"')

    if 'hz' in rp:
        far = float(rp.strip('"').split('_')[0])
        series = generate_triggers(start, end, meas_name, fields, far, epoch=epoch, latest=latest)
    else:
        dt = int(rp.strip('"')[:-1])
        series = generate_timeseries(start, end, meas_name, fields, aggregate, dt, tags=tags, filters=filters, epoch=epoch, latest=latest, groupby=groupby)
    ### generate fake data
    response = {'results': [{'statement_id':0, 'series':series}]}

    ### return data
    return bottle.HTTPResponse(status=200, headers=JSON_HEADER, body=json.dumps(response))


def translate_query(query_str):
    measurement, fields, conditions, limit, groupby = parse_query(query_str)

    ### FIXME: not handling multiple columns for now
    tags = fields[1:]

    if limit:
        end = utils.gps_now()
        start = end - 1000
        start, end = utils.gps_to_unix(start), utils.gps_to_unix(end)
    else:
        start = None
        end = None

    filters = []
    aggregate = None
    for column, symbol, val in conditions:
        val = val.strip("'")
        if column == 'time':
            assert symbol in ('>=', '<='), 'not a supported time comparison operator'
            if symbol == '>=':
                start = int(val)
            else:
                end = int(val)
        else:
            assert symbol == '=', 'tag only supports = operator'
            if column == 'aggregate':
                aggregate = val
            else:
                filters.append((column, val))

    return start, end, measurement, fields, aggregate, tags, filters, limit, groupby


def parse_query(query_str):
    query_str = query_str.strip().strip("'")

    ### parse limit if any
    query_str = query_str.replace('ORDER BY time DESC', '')
    if 'LIMIT' in query_str:
        query_str, limit = query_str.split('LIMIT')
        limit = int(limit)
    else:
        limit = 0

    ### parse group by if any
    if 'GROUP BY' in query_str:
        query_str, groupby = query_str.split('GROUP BY')
        groupby = groupby.strip()
    else:
        groupby = None

    ### parse conditions if any
    if 'WHERE' in query_str:
        query_str, conditions = query_str.split('WHERE')
        conditions = [condition.strip().split() for condition in conditions.split('AND')]
    else:
        conditions = []

    ### parse fields, measurement
    select, fields, from_, measurement = query_str.split()
    assert select == 'SELECT', 'SELECT not in correct location'
    assert from_ == 'FROM', 'FROM not in correct location'
    fields = [field.strip('"') for field in fields.split(',')]

    return measurement, fields, conditions, limit, groupby


def generate_timeseries(start, end, measurement, fields, aggregate, dt, tags=None, filters=None, epoch='ns', latest=0, groupby=None):
    ### format filters
    ### FIXME: doesn't do anything for now
    columns = []
    if filters:
        for filter_ in filters:
            tag, val = filter_
            columns.append(tag)

    ### create column name list
    column_names = ['time']
    column_names.extend(fields)

    ### format times
    if groupby and latest:
        if groupby == 'job':
            size = latest * NUM_JOBS
        else:
            size = latest
        times = numpy.random.uniform(start, high=end, size=size)
        times = utils.floor_div(times, int(dt))
        times = times[numpy.logical_and(times <= end, times >= start)]
    elif latest:
        times = numpy.random.uniform(start, high=end, size=latest)
        times = utils.floor_div(times, int(dt))
        times = times[numpy.logical_and(times <= end, times >= start)]
    else:
        mod_start = utils.floor_div(start, int(dt))
        if(mod_start != start):
            mod_start += int(dt)
        mod_end = utils.floor_div(end + int(dt), int(dt))
        times = numpy.arange(mod_start, mod_end, int(dt))

    ### generate timeseries
    series = []
    if groupby:
        times = _convert_gps_times(times, epoch)
        if groupby and groupby.strip('"') == 'job': ### FIXME: assume 1 tag max for now
            for job_id, time in zip(range(NUM_JOBS), times.tolist()):
                data = numpy.random.exponential(size=latest) + 1 ### FIXME: only works when latest = 1
                row = {'columns': column_names, 'name': measurement, 'values': [[time, data.tolist()[0], str(job_id).zfill(4)]]}
                series.append(row)
        ### format timeseries
        return series
    else:
        if times.size:
            times = _convert_gps_times(times, epoch)
            if tags and tags[0].strip('"') == 'job': ### FIXME: assume 1 tag max for now
                for job_id in range(NUM_JOBS):
                    data = numpy.random.exponential(size=times.size) + 1
                    series.extend([list(row) for row in zip(times.tolist(), data.tolist(), [job_id for i in range(times.size)])])
            else:
                data = random_trigger_value(fields[0], times.size)
                series.extend([list(row) for row in zip(times.tolist(), data.tolist())])
        ### format timeseries
        return [{
            'name': measurement,
            'columns': column_names,
            'values': series,
        }]


def generate_triggers(start, end, measurement, fields, far_threshold, epoch='ns', latest=0, num_triggers=100):
    ### format filters
    ### FIXME: doesn't do anything for now
    columns = []
    ### check for far
    assert ('far' in fields), 'far not found'

    ### format times
    if latest:
        times = numpy.random.randint(start, high=end, size=latest)
    else:
        times = numpy.arange(start, end, num_triggers)
    times = _convert_gps_times(times, epoch)

    ### generate triggers
    data = [random_trigger_value(field, times.size, far_threshold = far_threshold) for field in fields]
    series = [list(row) for row in zip(times.tolist(), *data)]

    ### create column name list
    column_names = ['time']
    column_names.extend(fields)

    ### format triggers
    return [{
        'name': measurement,
        'columns': column_names,
        'values': series,
    }]


def random_trigger_value(field, size, far_threshold = 1e-2):
    if(field == 'far'):
        return far_threshold * numpy.random.uniform(size=size)
    elif(field == 'snr'):
        return numpy.random.exponential(size=size) + 1
    elif field == 'segment':
        return numpy.random.randint(2, size=size)
    else:
        return numpy.random.uniform(size=size)


def _convert_gps_times(gps_times, epoch):
    if epoch == 'ns':
        return utils.gps_to_unix(gps_times)
    else:
        raise NotImplementedError


def _add_parser_args(parser):
    parser.add_argument('-b', '--backend', default='wsgiref',
                        help="chooses server backend. options: [cgi|wsgiref]. wsgiref starts a local server for development, default = wsgiref.")
    parser.add_argument('-p', '--port', type=int, default=8086,
                        help="select port to serve content on server. default = 8086")
    parser.add_argument('--hostname', default='localhost',
                        help="select hostname to serve content on server. default = localhost.")


def main(args=None):
    """Mocks an InfluxDB database

    """
    if not args:
        parser = argparse.ArgumentParser()
        _parser_add_arguments(parser)
        args = parser.parse_args()

    port = args.port
    hostname = args.hostname
    server_backend = args.backend

    bottle.run(app, server=server_backend, host=hostname, port=port, debug=True)
