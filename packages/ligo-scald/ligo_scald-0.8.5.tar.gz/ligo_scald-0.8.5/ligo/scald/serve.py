from collections import namedtuple
import json
import os

from . import resources

import bottle
import numpy
import yaml

from . import transforms, utils
from .io import influx

JSON_HEADER = {
    'Content-type': 'application/json',
    'Cache-Control': 'max-age=10',
}

### load templates
template_path = resources.get_resource_path('templates')
bottle.TEMPLATE_PATH.insert(0, template_path)

### instantiate app
app = bottle.Bottle()

### load configuration if available
app.config.update({'script_name': '', 'use_cgi': False})

if 'SCALDRC_PATH' in os.environ:
    with open(os.getenv('SCALDRC_PATH'), 'r') as f:
        app.config.update(yaml.safe_load(f))


Query = namedtuple('Query', 'columns tags tag_key tag_filters aggregate dt far fill scale datetime backend')


@app.route("/static/<file_>")
def static(file_):
    """Route to serve static files, e.g. css, js.

    Parameters
    ----------
    file_ : `str`
        the file to serve

    """
    static_dir = resources.get_resource_path('static')
    yield bottle.static_file(file_, root=static_dir)


@app.route("/")
@app.route("/<page>")
def dashboard(page='index'):
    """Route to serve a dashboard.

    """
    config = dict(app.config)
    page_config = config['pages'][page]
    static_dir = '../' if config['use_cgi'] else ''
    if page != 'index':
        static_dir += '../'

    ### determine if querying for online or historical data
    if 'type' in bottle.request.query:
        page_config['type'] = bottle.request.query['type']
    else:
        page_config['type'] = 'online'

    ### process online/historical query settings
    if page_config['type'] == 'online':
        if 'lookback' in bottle.request.query:
            page_config['lookback'] = int(bottle.request.query['lookback'])
        if 'delay' in bottle.request.query:
            page_config['delay'] = int(bottle.request.query['delay'])

        page_config['stop'] = int(utils.gps_now() - page_config['delay'])
        page_config['start'] = page_config['stop'] - page_config['lookback']
        page_config['refresh'] = 2000
    else:
        page_config['stop'] = int(bottle.request.query['end'])
        page_config['start'] = int(bottle.request.query['start'])
        page_config['refresh'] = -1

    ### fill in plot section for page with plot/schema info
    plots = page_config['plots']
    for plot in plots:
        plot_name = plot['plot']
        plot.update(config['plots'][plot_name])
        plot['schema'] = config['schemas'][plot['schema']]

    ### generate dashboard
    yield bottle.template(
        'dashboard.html',
        static_dir=static_dir,
        script_name=config['script_name'],
        dashboard_config=config['navbar'],
        page_config=config['pages'],
        current_page=page,
        plots=plots,
        plot_defaults=config['plotly'] if 'plotly' in config else {},
    )


@app.route("/api/timeseries/<measurement>/<start:int>/<end:int>")
def serve_timeseries(measurement, start, end):
    """Route to serve timeseries.

    Parameters
    ----------
    measurement : `str`
        the measurement name
    start : `int`
        GPS start time
    end : `int`
        GPS end time

    """
    query = parse_query(bottle.request.query)

    consumer = config_to_consumer(app.config['backends'][query.backend])
    response = []

    ### query for timeseries
    if query.tag_filters:
        for tag in query.tag_filters:
            time, data = consumer.retrieve_timeseries(
                measurement,
                start,
                end,
                query.columns,
                tags=[tag],
                aggregate=query.aggregate,
                dt=query.dt,
                datetime=query.datetime
            )
            response.append({'x':time, 'y':data, 'name': tag[1]})
    else:
        time, data = consumer.retrieve_timeseries(
            measurement,
            start,
            end,
            query.columns,
            tags=query.tag_filters,
            aggregate=query.aggregate,
            dt=query.dt,
            datetime=query.datetime
        )
        response.append({'x':time, 'y':data})

    ### return data
    return bottle.HTTPResponse(status=200, headers=JSON_HEADER, body=json.dumps(response).replace("NaN", query.fill))


@app.route("/api/segment/<measurement>/<start:int>/<end:int>")
def serve_segment(measurement, start, end):
    """Route to serve segment information.

    Parameters
    ----------
    measurement : `str`
        the measurement name
    start : `int`
        GPS start time
    end : `int`
        GPS end time

    """
    query = parse_query(bottle.request.query)

    consumer = config_to_consumer(app.config['backends'][query.backend])
    response = []

    ### query for segment plot
    if query.tag_filters:
        for tag in query.tag_filters:
            time, data = consumer.retrieve_timeseries(
                measurement,
                start,
                end,
                query.columns,
                tags=[tag],
                aggregate=query.aggregate,
                dt=query.dt,
                datetime=query.datetime
            )
            response.append({'x':time, 'y':[.5], 'z':[data], 'name': tag[1]})
    else:
        time, data = consumer.retrieve_timeseries(
            measurement,
            start,
            end,
            query.columns,
            tags=query.tag_filters,
            aggregate=query.aggregate,
            dt=query.dt,
            datetime=query.datetime
        )
        response.append({'x':time, 'y':[.5], 'z':[data]})

    ### return data
    return bottle.HTTPResponse(status=200, headers=JSON_HEADER, body=json.dumps(response).replace("NaN", query.fill))


@app.route("/api/snapshot/<measurement>/<start:int>/<end:int>")
def serve_snapshot(measurement, start, end):
    """Route to serve snapshots, i.e. structured data for a single timestamp.

    Parameters
    ----------
    measurement : `str`
        the measurement name
    start : `int`
        GPS start time
    end : `int`
        GPS end time

    """
    query = parse_query(bottle.request.query)

    consumer = config_to_consumer(app.config['backends'][query.backend])
    time, snapshot, dims = consumer.retrieve_snapshot(measurement)

    ### format request
    response = [{'x':snapshot[dims['x']], 'y':snapshot[dims['y']]}]

    ### return data
    return bottle.HTTPResponse(status=200, headers=JSON_HEADER, body=json.dumps(response))


@app.route("/api/heatmap/<measurement>/<start:int>/<end:int>")
def serve_heatmap(measurement, start, end):
    """Route to serve heatmaps.

    Parameters
    ----------
    measurement : `str`
        the measurement name
    start : `int`
        GPS start time
    end : `int`
        GPS end time

    """
    query = parse_query(bottle.request.query)

    assert (len(query.columns) == 1), 'column must contain only 1 element'
    column = query.columns[0]

    ### query for timeseries
    consumer = config_to_consumer(app.config['backends'][query.backend])
    times, tags, datum = consumer.retrieve_binnedtimeseries_by_tag(
        measurement,
        start,
        end,
        column,
        query.tag_key,
        tags=query.tag_filters,
        aggregate=query.aggregate,
        dt=query.dt,
        datetime=query.datetime
    )

    ### format request
    if query.scale == 'log':
        zdata = numpy.log(numpy.array(datum)).tolist()
        response = [{'x':times, 'y':tags, 'z':zdata, 'text':datum}]
    else:
        response = [{'x':times, 'y':tags, 'z':datum}]

    ### return data
    return bottle.HTTPResponse(status=200, headers=JSON_HEADER, body=json.dumps(response).replace("NaN", query.fill))


@app.route("/api/latest/<measurement>/<start:int>/<end:int>")
def serve_latest(measurement, start, end):
    """Route to serve the latest N points of a timeseries, keyed by tag.

    Parameters
    ----------
    measurement : `str`
        the measurement name
    start : `int`
        GPS start time
    end : `int`
        GPS end time

    """
    query = parse_query(bottle.request.query)

    tag = app.config['schemas'][measurement]['tag']
    default_value = app.config['schemas'][measurement]['default']
    transform = app.config['schemas'][measurement]['transform']
    y = []

    ### query for timeseries
    consumer = config_to_consumer(app.config['backends'][query.backend])
    current_gps = utils.gps_now()
    time, tag_ids, data = consumer.retrieve_latest_by_tag(
        measurement,
        query.columns[0],
        tag_key=tag,
        aggregate=query.aggregate,
        dt=query.dt,
        datetime=query.datetime
    )
    for i in range(len(tag_ids)):
        y.append(transform_data(time[i], data[i], transform, default_value, current_gps))

    ### format request
    response = [{'x':tag_ids, 'y':y}]

    ### return data
    return bottle.HTTPResponse(status=200, headers=JSON_HEADER, body=json.dumps(response))


@app.route("/api/table/<measurement>/<start:int>/<end:int>")
def serve_table(measurement, start, end):
    """Route to serve dynamic tables.

    Parameters
    ----------
    measurement : `str`
        the measurement name
    start : `int`
        GPS start time
    end : `int`
        GPS end time

    """
    query = parse_query(bottle.request.query)
    consumer = config_to_consumer(app.config['backends'][query.backend])
    response = []
    column_names = ['time']
    column_names.extend(query.columns)

    ### query for timeseries
    triggers = consumer.retrieve_triggers(measurement, start, end, query.columns, far=float(query.far), datetime=query.datetime)

    ### build field_dict
    field = []
    for col in column_names:
        field_dict = {'key': col, 'label': col, 'sortable': True}
        field.extend([field_dict])

    ### format request
    response = {'fields': field, 'items': triggers}

    ### return data
    return bottle.HTTPResponse(status=200, headers=JSON_HEADER, body=json.dumps(response).replace("NaN", query.fill))


@app.route("/api/nagios/<check>")
def serve_nagios(check):
    """Route to serve JSON-formatted status information for nagios.

    Parameters
    ----------
    check : `str`
        the nagios check to perform, used as a lookup in the app configuration

    """
    nagios_config = app.config['nagios'][check]
    backend = nagios_config.get('backend', 'default')

    ### time settings
    duration = nagios_config['lookback']
    end = utils.gps_now()
    start = end - duration
    dt = utils.duration_to_dt(duration)

    ### data settings
    schema = app.config['schemas'][check]
    measurement = schema['measurement']
    column = schema['column']
    tags = schema['tags'] if 'tags' in schema else []
    aggregate = schema['aggregate']

    ### alert settings
    alert_type = nagios_config['alert_type']
    alert_tags = utils.extract_alert_tags(schema)

    ### alert tracking
    alert_values = []
    now = utils.gps_now()

    ### retrieve data
    consumer = config_to_consumer(app.config['backends'][backend])
    for alert_tag in alert_tags:
        retrieve_tags = [alert_tag]
        retrieve_tags.extend(tags)
        time, data = consumer.retrieve_timeseries(measurement, start, end, column, tags=retrieve_tags, aggregate=aggregate, dt=dt)

        if alert_type == 'heartbeat':
            alert_values.append(transforms.latency(time, data, numpy.nan, t0=now))
        elif alert_type == 'threshold':
            threshold = nagios_config['alert_settings']['threshold']
            alert_values.append(transforms.cutoff(time, data, numpy.nan, threshold))

    ### format nagios response
    alert_values = numpy.array(alert_values)
    bad_status = numpy.sum(numpy.isnan(alert_values))
    if bad_status:
        if alert_type == 'heartbeat':
            text_status = "{num_tags} {alert_tag} more than {lookback} seconds behind".format(
                alert_tag=schema['tag_key'],
                num_tags=bad_status,
                lookback=duration,
            )
        elif alert_type == 'threshold':
            text_status = "{num_tags} {alert_tag} above {column} threshold = {threshold} {units} from gps times: {start} - {end}".format(
                alert_tag=schema['tag_key'],
                threshold=nagios_config['alert_settings']['threshold'],
                units=nagios_config['alert_settings']['threshold_units'],
                num_tags=bad_status,
                column=measurement,
                start=start,
                end=end,
            )

    else:
        if alert_type == 'heartbeat':
            text_status = "OK: Max delay: {delay} seconds".format(delay=numpy.nanmax(alert_values))
        elif alert_type == 'threshold':
            text_status = "OK: No {alert_tag}s above {column} threshold = {threshold} {units} from gps times: {start} - {end}".format(
                alert_tag=schema['tag_key'],
                threshold=nagios_config['alert_settings']['threshold'],
                units=nagios_config['alert_settings']['threshold_units'],
                column=measurement,
                start=start,
                end=end,
            )

    ### return response
    response = utils.status_to_nagios_response(text_status, bad_status=bad_status)
    return bottle.HTTPResponse(status=200, headers=JSON_HEADER, body=json.dumps(response, sort_keys=True, indent=4, separators=(',', ': ')))


def parse_query(query):
    columns = query.getall('column')
    tags = query.getall('tag')
    tag_key = query.get('tag_key', None)
    tag_filters = [(key, val) for key, val in bottle.request.query.allitems() if key in tags]

    far = query.get('far', None)
    aggregate = query.get('aggregate', None)
    dt = query.get('dt', None)
    if dt:
        dt = int(dt)

    if 'datetime' in query:
        datetime = query['datetime'] == 'true'
    else:
        datetime = False

    backend = query.get('backend', 'default')
    fill = query.get('fill', 'null')
    scale = query.get('scale', None)

    results = Query(
        columns=columns,
        tags=tags,
        tag_key=tag_key,
        tag_filters=tag_filters,
        aggregate=aggregate,
        dt=dt,
        far=far,
        fill=fill,
        scale=scale,
        datetime=datetime,
        backend=backend,
    )
    return results


def transform_data(time, data, transform, default, now):
    if transform == 'none':
        return transforms.identity(time, data, default)
    elif transform == 'latency':
        return transforms.latency(time, data, default, t0=now)
    else:
        raise NotImplementedError('transform {} not known/implemented'.format(transform))


def config_to_consumer(config):
    backend = config['backend']
    if backend == 'influxdb':
        return influx.Consumer(**config)
    else:
        raise NotImplementedError


def _add_parser_args(parser):
    parser.add_argument('-b', '--backend', default='wsgiref',
                        help="chooses server backend. options: [cgi|wsgiref]. default=wsgiref.")
    parser.add_argument('-p', '--port', type=int, default=8086,
                        help="select port to serve content on server. default = 8086")
    parser.add_argument('--hostname', default='localhost',
                        help="select hostname to serve content on server. default = localhost.")
    parser.add_argument('-c', '--config',
                        help="sets dashboard/plot options based on yaml configuration. if not set, uses SCALDRC_PATH.")
    parser.add_argument('-e', '--with-cgi-extension', default=False, action='store_true',
                        help="chooses whether scripts need to have a .cgi extension (if using cgi backend)")
    parser.add_argument('-n', '--application-name', default='scald',
                        help="chooses the web application name. default = scald.")


def main(args=None):
    """Serves data and dynamic html pages

    """
    if not args:
        parser = argparse.ArgumentParser()
        _parser_add_arguments(parser)
        args = parser.parse_args()

    ### parse args and set up configuration
    port = args.port
    hostname = args.hostname
    server_backend = args.backend
    app_name = args.application_name

    ### hacks to deal with running on apache and/or cgi
    use_cgi = (server_backend == 'cgi')
    if args.with_cgi_extension:
        app_name += '.cgi/'
    else:
        app_name += '/'
    script_name = app_name if use_cgi else ''

    ### load configuration
    if args.config:
        with open(args.config, 'r') as f:
            app.config.update(yaml.safe_load(f))
    elif not 'SCALDRC_PATH' in os.environ:
        raise KeyError('no configuration file found, please set your SCALDRC_PATH correctly using "export SCALDRC_PATH=PATH/TO/CONFIG" or add --config param (-c /path/to/config)')

    ### update configuration
    app.config.update({'script_name': script_name, 'use_cgi': use_cgi})

    ### start server
    if use_cgi:
        bottle.run(app, server=server_backend, debug=True)
    else:
        bottle.run(app, server=server_backend, host=hostname, port=port, debug=True)
