from collections import defaultdict
import itertools
import json
import logging
import os
import netrc
import urllib.parse

import numpy
import urllib3
import urllib3.exceptions
import yaml

from . import core
from . import line_protocol
from .. import utils


### only show warnings from urllib3
logging.getLogger("urllib3").setLevel(logging.WARNING)

### set up certificate verification
try:
    import certifi
    import urllib3.contrib.pyopenssl
    urllib3.contrib.pyopenssl.inject_into_urllib3()
except ImportError:
    pass

INFLUX_QUERY_TEMPLATE = 'SELECT {columns} FROM {measurement} {conditions}'
INFLUX_MEASUREMENT_TEMPLATE = '"{db}".{retention_policy}."{measurement}"'


logger = logging.getLogger('scald')


class Aggregator(object):
    """Handles the storing and aggregation of timeseries into InfluxDB.

    Parameters
    ----------
    hostname : `str`
        the hostname to connect to, defaults to localhost
    port : `int`
        the port to connect to, defaults to 8086
    db : `str`
        the database name, defaults to mydb
    auth : `bool`
        whether to use auth credentials, defaults to False
    https : `bool`
        whether to connect via HTTPS, defaults to False
    check_certs : `bool`
        whether to check SSL certificates, defaults to True
    reduce_dt : `int`
        how often to reduce data for lower dt + aggregated timeseries, defaults to 300s
    reduce_across_tags : `bool`
        whether to create timeseries that are aggregated across tags, defaults to True

    """
    def __init__(self, hostname='localhost', port=8086, db='mydb', auth=False, https=False, check_certs=True, reduce_dt=300, reduce_across_tags=True, **kwargs):
        self.hostname = hostname
        self.port = port
        self.db = db
        self.auth = auth
        self.https = https
        self.check_certs = check_certs

        ### reduction options
        self.reduce_dt = reduce_dt
        self.reduce_across_tags = reduce_across_tags

        ### set up client and database
        self.client = create_client(host=self.hostname, port=self.port, auth=self.auth, https=self.https, check_certs=self.check_certs)
        set_up_database(self.client, self.db)

        ### track reduced data to process
        self.span_processed = defaultdict(list)
        self.last_reduce = utils.gps_now()

        ### set up structure to store schemas
        self.schema = {}


    def load(self, path=None):
        """Loads schemas contained within a configuration file.

        Parameters
        ----------
        path : `str`
            the path to the configuration file

        """
        if not path:
            if 'SCALDRC_PATH' in os.environ:
                path = os.getenv('SCALDRC_PATH')
            else:
                raise KeyError('no configuration file found, please set your SCALDRC_PATH correctly using "export SCALDRC_PATH=path/to/config" or pass in path kwarg')

        ### load config
        config = None
        with open(path, 'r') as f:
            config = yaml.safe_load(f)

        ### register schemas
        for schema in config['schemas'].values():
            if 'schema1' in schema:
                if 'measurement' in schema:
                    measurement = schema['measurement']
                subschemas = {key: subschema for key, subschema in schema.items() if 'schema' in key}
                for subschema in subschemas.values():
                    if not 'measurement' in subschema:
                        subschema['measurement'] = measurement
                    self._load_schema(subschema)
            else:
                self._load_schema(schema)


    def register_schema(self, measurement, columns, column_key, tags=None, tag_key=None, aggregate=None, **kwargs):
        """Defines a schema for a measurement.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        columns : `str` or `tuple`
            the columns stored in a given measurement
        column_key : 'str'
            the column in which to do the aggregation across
        tags : `str` or `tuple`
            the tags stored in a given measurement
        tag_key : 'str'
            the tag in which to group by for aggregations
        aggregate : 'str'
            the aggregate to use

        Defines the layout for data of a given measurement, as well as
        how data will be aggregated when doing reductions.

        The column key defines which column to do aggregations across.

        If using tags, a tag key defines which tag to group by for aggregations,
        otherwise will just reduce over all data.

        """
        if tags or tag_key:
            assert tags and tag_key, 'if tags or tag_key is used, both must be defined'
        if tags and isinstance(tags, str):
            tags = (tags,)
        if isinstance(columns, str):
            columns = (columns,)

        self.schema[measurement] = {
            'columns': columns,
            'column_key': column_key,
            'tags': tags,
            'tag_key': tag_key,
            'aggregate': aggregate,
        }


    def store(self, data_type, *args, **kwargs):
        """A convenience function to call the other store methods by name.

        Parameters
        ----------
        data_type : `str`
            the type of data, e.g. timeseries
        *args : args to pass along
        **kwargs : kwargs to pass along

        """
        if data_type == 'rows':
            return self.store_rows(*args, **kwargs)
        elif data_type == 'columns':
            return self.store_columns(*args, **kwargs)
        elif data_type == 'triggers':
            return self.store_triggers(*args, **kwargs)
        elif data_type == 'snapshot':
            return self.store_snapshot(*args, **kwargs)
        else:
            raise NotImplementedError


    def store_rows(self, measurement, data, aggregate='max'):
        """Stores and aggregates incoming row-formatted timeseries.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        data : {`tuple` or `str` : `list`}
            see below for guide/formatting
        aggregate : `str`
            aggregate quantities to use in downsampling (options: min/median/max)
            if None, store raw timeseries

        Given M unique tags and N columns, data is passed in as follows:
            {(tag1, ..., tagM): rows}

        where a row is formatted in the following way:
            {'time': time, 'fields': {'col1': val1, ..., 'colN': valN}}

        NOTE: In the case where no tags are passed in,
              can pass in rows for data directly.

        FIXME: does not support zero tag case at the moment.

        """
        if aggregate:
            aggfunc = core.aggregate_to_func(aggregate)
        else:
            aggfunc = None

        lines = ''
        this_span = []
        for tag_vals, rows in data.items():
            if rows:
                if not isinstance(tag_vals, tuple):
                    tag_vals = (tag_vals,)
                tag_entry = {tag: tag_val for tag, tag_val in zip(self.schema[measurement]['tags'], tag_vals)}

                time = [row['time'] for row in rows]
                if not aggregate:  ### store raw timeseries
                    for row in rows:
                        row['tags'] = tag_entry
                    lines += _rows_to_line_protocol(measurement, rows, aggregate=None)

                else: ### reduce to 1s by default before storing timeseries
                    column_to_reduce = [row['fields'][self.schema[measurement]['column_key']] for row in rows]
                    reduced_idx, _, _ = core.reduce_data(time, column_to_reduce, aggfunc, dt=1)

                    ### add tags, bin time to reduced rows
                    reduced_rows = [rows[idx] for idx in reduced_idx]
                    for row in reduced_rows:
                        row['time'] = utils.floor_div(row['time'], 1)
                        row['tags'] = tag_entry

                    ### convert rows to line protocol, keeping track of spans
                    lines += _rows_to_line_protocol(measurement, reduced_rows, aggregate=aggregate)
                    this_span = self._update_spans(measurement, time, this_span, aggregate)

        ### store reduced rows
        _store_lines(self.client, self.db, lines, dt=1 if aggregate else None)

        ### reduce timeseries
        if this_span:
            self._reduce_all_dt(measurement, aggregate, this_span)


    def store_columns(self, measurement, data, aggregate='max'):
        """Stores and aggregates incoming column-formatted timeseries.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        data : {`tuple` or `str` : `list`}
            see below for guide/formatting
        aggregate : `str` or None
            aggregate quantities to use in downsampling (options: min/median/max)
            if None, store raw timeseries

        Given M unique tags and N columns, data is passed in as follows:
            {(tag1, ..., tagM): {'time': [...], 'fields': {'col1': [...], ..., 'colN': [...]}}}

        where each column is of the same length.

        NOTE: In the case where no tags are passed in, data is passed as a `dict`:
              {'time': [...], 'fields': {'col1': [...], ..., 'colN': [...]}}

        FIXME: does not support zero tag case at the moment.

        """
        if aggregate:
            aggfunc = core.aggregate_to_func(aggregate)
        else:
            aggfunc = None

        ### reduce by tag to 1s
        lines = ''
        this_span = []
        for tag_vals, data_entry in data.items():
            time = data_entry['time']
            columns = data_entry['fields']
            if len(time) > 0:

                if not isinstance(tag_vals, tuple):
                    tag_vals = (tag_vals,)
                tag_entry = {tag: tag_val for tag, tag_val in zip(self.schema[measurement]['tags'], tag_vals)}
                column_key = self.schema[measurement]['column_key']

                if not aggregate: ### store raw timeseries
                    raw_columns = {col: numpy.array(columns[col]).tolist() for col in columns.keys()}
                    lines += _columns_to_line_protocol(measurement, time, raw_columns, tags=tag_entry)

                else: ### reduce to 1s by default before storing timeseries
                    reduced_idx, reduced_time, reduced_key_column = core.reduce_data(time, columns[column_key], aggfunc, dt=1)
                    reduced_columns = {col: numpy.array(columns[col])[list(reduced_idx)].tolist() for col in columns.keys() if col not in column_key}
                    reduced_columns.update({column_key: reduced_key_column})

                    ### convert timeseries to line protocol, keeping track of spans
                    reduced_time = utils.floor_div(numpy.array(reduced_time), 1).tolist()
                    lines += _columns_to_line_protocol(measurement, reduced_time, reduced_columns, tags=tag_entry, aggregate=aggregate)
                    this_span = self._update_spans(measurement, time, this_span, aggregate)

        ### store reduced columns
        _store_lines(self.client, self.db, lines, dt=1 if aggregate else None)

        ### further reductions
        if this_span:
            self._reduce_all_dt(measurement, aggregate, this_span)


    def store_triggers(self, measurement, rows, far_key='far', time_key='end'):
        """Stores and aggregates incoming triggers.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        rows : `list`
            a list of triggers to store, formatted as a dictionary,
            with keys corresponding to columns

        NOTE: still in progress, very much in experimental stage. use at your own risk

        """
        ### filter out any rows with FAR above threshold
        rows = [row for row in rows if row[far_key] <= 1e-2]

        ### reduce incoming triggers to 1 Hz (based on lowest FAR)
        ### FIXME: should grab triggers from influx from the same span
        if rows:
            series = {col: [row[col] for row in rows] for col in (time_key, far_key)}
            idx, _, _ = core.reduce_data(series[time_key], series[far_key], min, dt=1)
            reduced_rows = numpy.array(rows)[list(idx)]
            if isinstance(reduced_rows, dict):
                reduced_rows = [reduced_rows]
            else:
                reduced_rows = reduced_rows.tolist()

            ### format triggers for storage
            reduced_rows = [{'time': utils.floor_div(row[time_key], 1), 'fields': row} for row in reduced_rows]

            ### store reduced triggers at highest far threshold
            lines =_rows_to_line_protocol(measurement, reduced_rows)
            _store_lines(self.client, self.db, lines, far=1e-2)

            ### store any relevant triggers into lower far threshold RPs
            for far in [1e-3, 1e-4, 1e-5, 1e-6, 1e-7]:
                reduced_rows = [row for row in reduced_rows if row['fields'][far_key] <= far]

                ### check if any triggers survive cut
                if not reduced_rows:
                    break

                ### store relevant triggers at this far threshold
                lines =_rows_to_line_protocol(measurement, reduced_rows)
                _store_lines(self.client, self.db, lines, far=far)


    def store_snapshot(self, measurement, data, dims, time, **attrs):
        """Stores a JSON-formatted snapshot to disk.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        data : `dict`
            a mapping from a column to 1-dim data
        dims : `dict`
            a mapping from a dimension (one of x, y, z) to a column,
            either 2-dim (x, y) or 3-dim (x, y, z).
        time : `int`
            the time the snapshot was taken

        NOTE: snapshots don't need to have a schema defined.

        """
        ### FIXME: attrs is not currently used, not sure the best way to encode this info
        snapshot = {
            'time': time,
            'fields': {'data': json.dumps(data), 'dims': json.dumps(dims)},
        }
        lines =_rows_to_line_protocol(measurement, [snapshot])
        _store_lines(self.client, self.db, lines)


    def _update_spans(self, measurement, time, this_span, aggregate):
        #-------------------------------------------------------
        ### internal utility to keep span of aggregations done
        start, end = numpy.floor(time[0]).astype(int), numpy.ceil(time[-1]).astype(int)

        ### keep track of spans processed
        if self.span_processed[(measurement, aggregate)]:
            prev_start, prev_end = self.span_processed[(measurement, aggregate)]
            self.span_processed[(measurement, aggregate)] = [min(start, prev_start), max(end, prev_end)]
        else:
            self.span_processed[(measurement, aggregate)] = [start, end]

        if this_span:
            this_span = [min(start, this_span[0]), max(end, this_span[1])]
        else:
            this_span = [start, end]

        return this_span


    def _reduce_all_dt(self, measurement, aggregate, this_span):
        #-------------------------------------------------------
        ### internal utility to reduce along and across each tag
        ### across all aggregated bins
        column_key = self.schema[measurement]['column_key']
        tag_key = self.schema[measurement]['tag_key']

        ### reduce across tag for dt=1
        if self.reduce_across_tags:
            start, end = utils.span_to_process(*this_span, dt=1)
            self._reduce_across_tags(measurement, start, end, aggregate, 1)

        ### only reduce higher dt every last_reduce seconds
        if utils.in_new_epoch(utils.gps_now(), self.last_reduce, self.reduce_dt):
            self.last_reduce = utils.gps_now()

            ### reduce by tag
            for dt in (10**power for power in range(core.DIRS - 1)):
                start, end = utils.span_to_process(*self.span_processed[(measurement, aggregate)], dt=10*dt)
                self._reduce_by_tag(measurement, start, end, aggregate, dt)

            ### reduce across tags
            if self.reduce_across_tags:
                for dt in (10**power for power in range(1, core.DIRS)):
                    start, end = utils.span_to_process(*self.span_processed[(measurement, aggregate)], dt=dt)
                    self._reduce_across_tags(measurement, start, end, aggregate, dt)

            ### reset processed spans
            self.span_processed[(measurement, aggregate)] = []

        this_span = []


    def _reduce_by_tag(self, measurement, start, end, aggregate, dt):
        #-------------------------------------------------------
        ### internal utility to reduce along each tag for a single dt
        column_key = self.schema[measurement]['column_key']
        tag = self.schema[measurement]['tag_key']

        rows_by_tag = _retrieve_rows_by_tag(self.client, self.db, measurement, self.schema[measurement], start, end, tag, aggregate=aggregate, dt=dt)

        reduced_dt = 10 * dt
        aggfunc = core.aggregate_to_func(aggregate)

        ### reduce by tag
        lines = ''
        for tag_val, rows in rows_by_tag.items():
            if rows:
                ### reduce by column key
                time = [row['time'] for row in rows]
                column_to_reduce = [row['fields'][column_key] for row in rows]
                reduced_idx, _, _ = core.reduce_data(time, column_to_reduce, aggfunc, dt=reduced_dt)

                ### format and store reduced rows
                reduced_rows = [rows[idx] for idx in reduced_idx]
                for row in reduced_rows:
                    row['time'] = utils.floor_div(row['time'], reduced_dt)
                lines += _rows_to_line_protocol(measurement, reduced_rows, aggregate=aggregate)

        _store_lines(self.client, self.db, lines, dt=reduced_dt)


    def _reduce_across_tags(self, measurement, start, end, aggregate, dt):
        #-------------------------------------------------------
        ### internal utility to reduce across tags for a single dt
        column_key = self.schema[measurement]['column_key']
        tag = self.schema[measurement]['tag_key']

        rows_by_tag = _retrieve_rows_by_tag(self.client, self.db, measurement, self.schema[measurement], start, end, tag, aggregate=aggregate, dt=dt)
        aggfunc = core.aggregate_to_func(aggregate)

        ### flatten data and prep to reduce
        rows = list(itertools.chain.from_iterable(rows_by_tag.values()))
        agg_measurement = '{}_across_{}s'.format(measurement, tag)

        ### reduce across tags
        lines = ''
        if rows:
            time = [row['time'] for row in rows]
            column_to_reduce = [row['fields'][column_key] for row in rows]
            reduced_idx, _, _ = core.reduce_data(time, column_to_reduce, aggfunc, dt=dt)

            ### remove tag where reduction takes place
            reduced_rows = [rows[idx] for idx in reduced_idx]
            for row in reduced_rows:
                del row['tags'][tag]

            lines += _rows_to_line_protocol(agg_measurement, reduced_rows, aggregate=aggregate)

        _store_lines(self.client, self.db, lines, dt=dt)


    def _load_schema(self, schema):
        #-------------------------------------------------------
        ### internal utility to format schemas from config file
        measurement = schema.pop('measurement')
        columns = schema.pop('column')
        if isinstance(columns, str):
            columns = (columns,)
        column_key = schema.pop('column_key', columns[0])
        if 'tag' in schema:
            tag = schema.pop('tag')
            schema['tags'] = tag

        self.register_schema(measurement, columns, column_key, **schema)


class Consumer(object):
    """Queries data from InfluxDB.

    Parameters
    ----------
    hostname : `str`
        the hostname to connect to, defaults to localhost
    port : `int`
        the port to connect to, defaults to 8086
    db : `str`
        the database name, defaults to mydb
    auth : `bool`
        whether to use auth credentials, defaults to False
    https : `bool`
        whether to connect via HTTPS, defaults to False
    check_certs : `bool`
        whether to check SSL certificates, defaults to True

    """
    def __init__(self, hostname='localhost', port=8086, db='mydb', auth=False, https=False, check_certs=True, **kwargs):
        self.hostname = hostname
        self.port = port
        self.db = db
        self.auth = auth
        self.https = https
        self.check_certs = check_certs

        ### set up client
        self.client = create_client(host=self.hostname, port=self.port, auth=self.auth, https=self.https, check_certs=self.check_certs)

        ### set up structure to store schemas
        self.schema = {}


    def load(self, path=None):
        """Loads schemas contained within a configuration file.

        Parameters
        ----------
        path : `str`
            the path to the configuration file

        """
        if not path:
            if 'SCALDRC_PATH' in os.environ:
                path = os.getenv('SCALDRC_PATH')
            else:
                raise KeyError('no configuration file found, please set your SCALDRC_PATH correctly using "export SCALDRC_PATH=path/to/config" or pass in path kwarg')

        ### load config
        config = None
        with open(path, 'r') as f:
            config = yaml.safe_load(f)

        ### register schemas
        for schema in config['schemas'].values():
            if 'schema1' in schema:
                if 'measurement' in schema:
                    measurement = schema['measurement']
                subschemas = {key: subschema for key, subschema in schema.items() if 'schema' in key}
                for subschema in subschemas.values():
                    if not 'measurement' in subschema:
                        subschema['measurement'] = measurement
                    self._load_schema(subschema)
            else:
                self._load_schema(schema)


    def register_schema(self, measurement, columns, column_key, tags=None, tag_key=None, aggregate=None, **kwargs):
        """Defines a schema for a measurement.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        columns : `str` or `tuple`
            the columns stored in a given measurement
        column_key : 'str'
            the column in which to do the aggregation across
        tags : `str` or `tuple`
            the tags stored in a given measurement
        tag_key : 'str'
            the tag in which to group by for aggregations
        aggregate : 'str'
            the aggregate to use

        Defines the layout for data of a given measurement, as well as
        how data will be aggregated when doing reductions.

        The column key defines which column to do aggregations across.

        If using tags, a tag key defines which tag to group by for aggregations,
        otherwise will just reduce over all data.

        """
        if tags or tag_key:
            assert tags and tag_key, 'if tags or tag_key is used, both must be defined'
        if tags and isinstance(tags, str):
            tags = (tags,)
        if isinstance(columns, str):
            columns = (columns,)

        self.schema[measurement] = {
            'columns': columns,
            'column_key': column_key,
            'tags': tags,
            'tag_key': tag_key,
            'aggregate': aggregate,
        }


    def query(self, schema, data_type, *args, **kwargs):
        """Query for data using an available schema.

        Parameters
        ----------
        schema : `str`
            the schema name
        data_type : `str`
            the type of data, e.g. timeseries
        *args : args to pass along
        **kwargs : kwargs to pass along

        """
        s = self.schema[schema]
        s['measurement'] = schema ### FIXME: fix this issue of tying schema to measurement name

        if data_type == 'rows':
            start, end = args
            return self.retrieve_rows_by_tag(s['measurement'], start, end, s['tag_key'], aggregate=s['aggregate'], **kwargs)
        elif data_type == 'heatmap':
            start, end = args
            return self.retrieve_binnedtimeseries_by_tag(s['measurement'], start, end, s['columns'][0], s['tag_key'], aggregate=s['aggregate'], **kwargs)
        elif data_type == 'latest':
            return self.retrieve_latest_by_tag(s['measurement'], s['columns'][0], tag_key=s['tag_key'], aggregate=s['aggregate'], **kwargs)
        elif data_type == 'timeseries':
            start, end = args
            return self.retrieve_timeseries(s['measurement'], start, end, s['columns'][0], aggregate=s['aggregate'], **kwargs)
        elif data_type == 'triggers':
            start, end = args
            return self.retrieve_triggers(s['measurement'], start, end, s['columns'], **kwargs)
        else:
            raise NotImplementedError


    def retrieve_rows_by_tag(self, measurement, start, end, tag, aggregate=None, dt=None, datetime=False):
        """Retrieve all rows with a given tag.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        start : `int`
            GPS start time
        end : `int`
            GPS end time
        tag : `str`:
            tag to match timeseries with
        aggregate : `str`
            aggregate quantities to use in downsampling (i.e. max)
        dt : `int`
            the retention policy in which to retrieve timeseries from,
            not used if aggregate is not specified

        Returns
        -------
        time : `list`
            time points spanning from start to end
        tag_values : `list`
            all tag values that matched tag
        data: `list` of `list`
            a list of timeseries, each one corresponding to a tag value ordered
            by tag_values

        NOTE: this method needs a schema to be registered for a particular measurement before use.

        """
        return _retrieve_rows_by_tag(self.client, self.db, measurement, self.schema[measurement], start, end, tag, aggregate=aggregate, dt=dt, datetime=datetime)


    def retrieve_binnedtimeseries_by_tag(self, measurement, start, end, column, tag_key, tags=None, aggregate=None, dt=None, datetime=False):
        """Retrieve all timeseries with a given tag, binned by tag and dt.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        start : `int`
            GPS start time
        end : `int`
            GPS end time
        tag_key : `str`:
            tag to match timeseries with
        tags : `str`:
            tag to filter timeseries by
        aggregate : `str`
            aggregate quantities to use in downsampling (i.e. max)
        dt : `int`
            the retention policy in which to retrieve timeseries from,
            not used if aggregate is not specified

        Returns
        -------
        timebins : `list`
            time bins spanning from start to end (inclusive) with spacing dt
        tag_values : `list`
            all tag values that matched tag
        binned_data: `list` of `list`
            a list of timeseries, each one corresponding to a tag value ordered
            by tag_values

        """
        timedata, tagdata, datadata = self.retrieve_timeseries_by_tag(
            measurement,
            start,
            end,
            column,
            tag_key,
            tags=tags,
            aggregate=aggregate,
            dt=dt,
            datetime=False,
        )

        ### create time bins
        if dt:
            binned_timedata = (numpy.arange((end-start)/dt+1)*dt + start).astype(int)
        else:
            binned_timedata = (numpy.arange(end-start) + start).astype(int)

        binned_datadata = numpy.zeros((len(tagdata), len(binned_timedata)), dtype="double") + float("nan")

        ### bin time and data
        for i, (time, tag, data) in enumerate(zip(timedata, tagdata, datadata)):
            if len(time) > 0:
                ix = numpy.digitize(time, binned_timedata) - 1
                binned_datadata[i,ix] = data

        ### convert to datetime (if requested)
        ### FIXME: need to create a gps_to_rfc3339 function
        if datetime:
            raise NotImplementedError('gps_to_rfc3339 functionality to do this is not currently implemented')
        #    binned_timedata = [utils.gps_to_rfc3339(t) for t in binned_timedata]

        return binned_timedata.tolist(), tagdata, binned_datadata.tolist()


    def retrieve_timeseries_by_tag(self, measurement, start, end, column, tag_key, tags=None, aggregate=None, dt=None, datetime=False):
        """Retrieve all timeseries with a given tag from InfluxDB.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        start : `int`
            GPS start time
        end : `int`
            GPS end time
        tag_key : `str`:
            tag to match timeseries with
        tags : `str`:
            tag to filter timeseries by
        aggregate : `str`
            aggregate quantities to use in downsampling (i.e. max)
        dt : `int`
            the retention policy in which to retrieve timeseries from,
            not used if aggregate is not specified

        Returns
        -------
        time : `list`
            time points spanning from start to end
        tag_values : `list`
            all tag values that matched tag
        data: `list` of `list`
            a list of timeseries, each one corresponding to a tag value ordered
            by tag_values

        """
        query = INFLUX_QUERY_TEMPLATE.format(
            columns=_format_influxql_columns(column, tags=tag_key),
            measurement=_format_influxql_measurement(self.db, measurement, dt=dt),
            conditions=_format_influxql_conditions(start=start, end=end, tags=tags, aggregate=aggregate),
        )

        try:
            _, points = _query_influx_data(self.client, self.db, query, datetime=datetime)
        except:
            return [], [], []
        else:
            tags = set()
            series = defaultdict(lambda: defaultdict(list))
            for time, data, tag_val in points:
                series[tag_val]['time'].append(time)
                series[tag_val][column].append(data)
                tags.add(tag_val)

            tagdata = sorted(list(tags))
            timedata = []
            datadata = []
            for tag_val in tagdata:
                timedata.append(series[tag_val]['time'])
                datadata.append(series[tag_val][column])

            ### convert to gps time
            if not datetime:
                timedata = [utils.unix_to_gps(numpy.array(time)).tolist() for time in timedata]

            return timedata, tagdata, datadata


    def retrieve_timeseries_latest(self, measurement, column, tags=None, aggregate=None, dt=None, datetime=False, num_latest=1):
        """Retrieve latest N timeseries points.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        column : `str`
            the column name
        tags : `str` or `list`:
            tags to match timeseries with
        aggregate : `str`
            aggregate quantities to use in downsampling (i.e. max)
        dt : `int`
            the retention policy in which to retrieve timeseries from,
            not used if aggregate is not specified
        num_latest : `int`
            latest N points of timeseries

        Returns
        -------
        time : `list`
            time points spanning from start to end
        data: `list`
            timeseries corresponding to column specified

        """
        query = INFLUX_QUERY_TEMPLATE.format(
            columns=_format_influxql_columns(column),
            measurement=_format_influxql_measurement(self.db, measurement, dt=dt),
            conditions=_format_influxql_conditions(aggregate=aggregate, tags=tags, limit=num_latest),
        )

        try:
            _, points = _query_influx_data(self.client, self.db, query, datetime=datetime)
        except:
            return [], []
        else:
            time = []
            data = []
            for t, d in points:
                time.append(t)
                data.append(d)

            ### convert to gps time
            if not datetime:
                time = utils.unix_to_gps(numpy.array(time)).tolist()

            return time, data


    def retrieve_latest_by_tag(self, measurement, column, tag_key, aggregate=None, dt=None, datetime=False, num_latest=1):
        """Retrieve latest N points for all values associated with a given tag.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        column : `str`
            the column name
        tag_key : `str`:
            tag to group on
        aggregate : `str`
            aggregate quantities to use in downsampling (i.e. max)
        dt : `int`
            the retention policy in which to retrieve timeseries from,
            not used if aggregate is not specified
        num_latest : `int`
            latest N points of timeseries

        Returns
        -------
        time : `list`
            time points spanning from start to end
        data: `list`
            timeseries corresponding to column specified

        """
        query = INFLUX_QUERY_TEMPLATE.format(
            columns=_format_influxql_columns([column, tag_key]),
            measurement=_format_influxql_measurement(self.db, measurement, dt=dt),
            conditions=_format_influxql_conditions(aggregate=aggregate, limit=num_latest, groupby=tag_key),
        )

        try:
            _, points = _query_influx_data_groupby(self.client, self.db, query, datetime=datetime)
        except:
            return [], [], []
        else:
            time, data, tags = zip(*points)

            ### convert to gps time
            if not datetime:
                time = utils.unix_to_gps(numpy.array(time)).tolist()

            return time, list(tags), list(data)


    def retrieve_timeseries(self, measurement, start, end, column, tags=None, aggregate=None, dt=None, datetime=False):
        """Retrieve timeseries corresponding to a specific column.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        start : `int`
            GPS start time
        end : `int`
            GPS end time
        column : `str`:
            the column name
        tags : `str` or `list`:
            tags to specify
        aggregate : `str`
            aggregate quantities to use in downsampling (i.e. max)
        dt : `int`
            the retention policy in which to retrieve timeseries from,
            not used if aggregate is not specified

        Returns
        -------
        time : `list`
            time points spanning from start to end
        data: `list`
            timeseries corresponding to column specified

        """
        query = INFLUX_QUERY_TEMPLATE.format(
            columns=_format_influxql_columns(column),
            measurement=_format_influxql_measurement(self.db, measurement, dt=dt),
            conditions=_format_influxql_conditions(start=start, end=end, aggregate=aggregate, tags=tags),
        )

        try:
            _, points = _query_influx_data(self.client, self.db, query, datetime=datetime)
        except:
            return [], []
        else:
            time = []
            data = []
            for t, d in points:
                time.append(t)
                data.append(d)

            ### convert to gps time
            if not datetime:
                time = utils.unix_to_gps(numpy.array(time)).tolist()

            return time, data


    def retrieve_triggers(self, measurement, start=None, end=None, columns=None, far=None, datetime=False):
        """Retrieve triggers.

        Parameters
        ----------
        measurement : `str`
            the measurement name
        start : `int`
            GPS start time
        end : `int`
            GPS end time
        columns : `list` or `str`:
            columns to specify
        far : `float`
            the far threshold in which to filter triggers on

        Returns
        -------
        data: `list` of `dict`
            a list of triggers, formatted as a `dict`, keyed by column

        """
        if isinstance(columns, str):
            columns = [columns]
        if not far:
            far = 1e-2

        ### FIXME: columns kwarg isn't doing anything, should be selecting specific columns instead
        query = INFLUX_QUERY_TEMPLATE.format(
            columns=_format_influxql_columns(columns) if columns else '*',
            measurement=_format_influxql_measurement(self.db, measurement, far=far),
            conditions=_format_influxql_conditions(start=start, end=end),
        )

        try:
            _, points = _query_influx_data(self.client, self.db, query, datetime=datetime)
        except:
            return []
        else:
            trigger_cols = ['time']
            trigger_cols.extend(columns)
            rows = [dict(zip(trigger_cols, point)) for point in points]

            ### convert to gps time
            ### FIXME: should find a faster way of doing time conversion
            if not datetime:
                for row in rows:
                    row['time'] = utils.unix_to_gps(row['time'])

            return rows

    def retrieve_snapshot(self, measurement, datetime=False):
        """Retrieves a JSON-formatted snapshot.

        Parameters
        ----------
        measurement : `str`
            the measurement name

        Returns
        -------
        time : `float`
            time corresponding to the snapshot
        data: `dict`
            a mapping from a column to 1-dim data
        dims: `dict`
            a mapping from a dimension (one of x, y, z) to a column,
            either 2-dim (x, y) or 3-dim (x, y, z).

        """
        query = INFLUX_QUERY_TEMPLATE.format(
            columns=_format_influxql_columns(['data', 'dims']),
            measurement=_format_influxql_measurement(self.db, measurement),
            conditions=_format_influxql_conditions(limit=1),
        )

        try:
            _, points = _query_influx_data(self.client, self.db, query, datetime=datetime)
            points[0] ### check if return query is nonempty
        except:
            return None, {}, {}
        else:
            time, data, dims = points[0]

            ### convert to gps time
            if not datetime:
                time = utils.unix_to_gps(time)

            return time, json.loads(data), json.loads(dims)

    def _load_schema(self, schema):
        #-------------------------------------------------------
        ### internal utility to format schemas from config file
        measurement = schema.pop('measurement')
        columns = schema.pop('column')
        if isinstance(columns, str):
            columns = (columns,)
        column_key = schema.pop('column_key', columns[0])
        if 'tag' in schema:
            tag = schema.pop('tag')
            schema['tags'] = tag

        self.register_schema(measurement, columns, column_key, **schema)


def set_up_database(client, db, timeseries=True, triggers=True):
    create_database(client, db)

    if timeseries:
        dts = [10**power for power in range(core.DIRS)]
        for dt in dts:
            create_timeseries_retention_policy(client, db, dt)

    if triggers:
        fars = [1e-2, 1e-3, 1e-4, 1e-5, 1e-6, 1e-7]
        for far in fars:
            create_trigger_retention_policy(client, db, far)


def create_timeseries_retention_policy(client, db, dt):
    query = ' CREATE RETENTION POLICY "{dt}s" ON "{db}" DURATION INF REPLICATION 1'.format(db=db, dt=dt)

    params = urllib.parse.urlencode({'q':query})
    headers = {"Content-Type": "application/json"}
    headers.update(client.headers)
    client.request('POST', '/query?{}'.format(params), headers=headers)


def create_trigger_retention_policy(client, db, far):
    query = ' CREATE RETENTION POLICY "{far}_hz" ON "{db}" DURATION INF REPLICATION 1'.format(db=db, far=far)

    params = urllib.parse.urlencode({'q':query})
    headers = {"Content-Type": "application/json"}
    headers.update(client.headers)
    client.request('POST', '/query?{}'.format(params), headers=headers)


def create_database(client, db):
    query = ' CREATE DATABASE "{db}"'.format(db=db)

    params = urllib.parse.urlencode({'q':query})
    headers = {"Content-Type": "application/json"}
    headers.update(client.headers)
    client.request('POST', '/query?{}'.format(params), headers=headers)


def create_client(host='localhost', port=8086, auth=False, https=False, check_certs=True):
    ### add basic auth if requested
    if auth:
        user = os.getenv('INFLUX_USERNAME')
        password = os.getenv('INFLUX_PASSWORD')
        if not user:
            ### look at default location for .netrc unless NETRC set
            if 'NETRC' in os.environ:
                netrc_info = netrc.netrc(os.getenv('NETRC'))
            else:
                netrc_info = netrc.netrc()

            auth_entry = netrc_info.authenticators(host)
            if auth_entry:
                user, _, password = auth_entry
            else:
                raise ValueError('auth enabled and no .netrc info or auth environment variables provided')

        userpass = '{}:{}'.format(user, password)
        headers = urllib3.make_headers(keep_alive=True, basic_auth=userpass)

    else:
        headers = urllib3.make_headers(keep_alive=True)

    if https and check_certs:
        if 'SCALD_SSL_CA_CERT' in os.environ:
            ca_certs = os.environ.get('SCALD_SSL_CA_CERT')
        else:
            ca_certs = certifi.where()
        return urllib3.HTTPSConnectionPool(
            host, port=port, maxsize=10, block=True, headers=headers,
            cert_reqs='CERT_REQUIRED', ca_certs=ca_certs
        )
    elif https:
        # disable insecure request warnings when disabling cert verification
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        return urllib3.HTTPSConnectionPool(host, port=port, maxsize=10, block=True, headers=headers, cert_reqs='CERT_NONE')
    else:
        return urllib3.HTTPConnectionPool(host, port=port, maxsize=10, block=True, headers=headers)


def _retrieve_rows_by_tag(client, db, measurement, schema, start, end, tag, aggregate=None, dt=None, datetime=False):
    query = INFLUX_QUERY_TEMPLATE.format(
        columns=_format_influxql_columns(schema['columns'], tags=schema['tags']),
        measurement=_format_influxql_measurement(db, measurement, dt=dt),
        conditions=_format_influxql_conditions(start=start, end=end, aggregate=aggregate),
    )

    try:
        columns, points = _query_influx_data(client, db, query, datetime=datetime)
    except:
        return {}
    else:
        rows = [_format_point(point, schema, datetime=datetime) for point in points]

        ### group by tag
        rows_by_tag = defaultdict(list)
        for row in rows:
            tag_val = row['tags'][tag]
            rows_by_tag[tag_val].append(row)

        return rows_by_tag


def _rows_to_line_protocol(measurement, rows, aggregate=None):
    ### format rows
    points = []
    for row in rows:
        point = {
            "measurement": measurement,
            "tags": row['tags'] if 'tags' in row else {},
            "time": utils.gps_to_unix(row['time']),
            "fields": row['fields'],
        }
        points.append(point)

    if aggregate:
        packet = {'points': points, 'tags': {'aggregate': aggregate}}
    else:
        packet = {'points': points}

    ### convert to line protocol
    return line_protocol.make_lines(packet)


def _columns_to_line_protocol(measurement, time, columns, tags=None, aggregate=None):
    ### convert to unix time
    time = [utils.gps_to_unix(t) for t in time]

    ### format timeseries
    points = []
    rows = [dict(zip(columns, row)) for row in zip(*columns.values())]
    for t, row in zip(time, rows):
        point = {
            "measurement": measurement,
            "tags": tags if tags else {},
            "time": t,
            "fields": row,
        }
        points.append(point)

    if aggregate:
        packet = {'points': points, 'tags': {'aggregate': aggregate}}
    else:
        packet = {'points': points}

    ### convert to line protocol
    return line_protocol.make_lines(packet)


def _store_lines(client, db, lines, dt=None, far=None):
    ### format query params
    param_dict = {'db': db}
    if dt:
        param_dict.update({'rp': '{}s'.format(dt)})
    elif far:
        param_dict.update({'rp': '{}_hz'.format(far)})

    params = urllib.parse.urlencode(param_dict)
    headers = {"Content-Type": "application/octet-stream"}
    headers.update(client.headers)

    ### push to client
    response = client.urlopen('POST', '/write?{}'.format(params), body=lines.encode('utf-8'), headers=headers)
    if response.status >= 400:
        logger.warning(f'urllib3 response status: {response.status} | response reason: {response.reason}')


def _format_influxql_measurement(database_name, measurement, dt=None, far=None):
    if dt:
        retention_policy = '"{}s"'.format(dt)
    elif far:
        retention_policy = '"{}_hz"'.format(far)
    else:
        retention_policy = ''

    return INFLUX_MEASUREMENT_TEMPLATE.format(
        db=database_name,
        retention_policy=retention_policy,
        measurement=measurement,
    )


def _format_influxql_conditions(start=None, end=None, aggregate=None, tags=None, limit=None, groupby=None):
    conditions = []
    if aggregate:
        conditions.append('aggregate = \'{aggregate}\''.format(aggregate=aggregate))
    if tags:
        conditions.extend(['{} = \'{}\''.format(tag_name, tag_val) for tag_name, tag_val in tags])
    if start:
        conditions.append('time >= {start}'.format(start=utils.gps_to_unix(start)))
    if end:
        conditions.append('time <= {end}'.format(end=utils.gps_to_unix(end)))

    if conditions:
        condition_str = 'WHERE ' + ' AND '.join(conditions)
    else:
        condition_str = ''

    if groupby:
        condition_str += ' GROUP BY {key}'.format(key=groupby)
    if limit:
        condition_str += ' ORDER BY time DESC LIMIT {limit}'.format(limit=limit)

    return condition_str


def _format_influxql_columns(columns, tags=None):
    if isinstance(columns, str):
        columns = [columns]
    if tags and isinstance(tags, str):
        tags = [tags]

    if tags:
        return ','.join(['"{}"'.format(field) for field in itertools.chain(*[columns, tags])])
    else:
        return ','.join(['"{}"'.format(field) for field in columns])


def _query_influx_data(client, db, query, datetime=False):
    if datetime:
        epoch = 'rfc3339'
    else:
        epoch = 'ns'

    fields = {'db':db, 'q':query, 'epoch':epoch}
    headers = {"Content-Type": "application/json"}
    headers.update(client.headers)

    response = client.request('GET', '/query', fields=fields, headers=headers)
    data = json.loads(response.data.decode('utf-8'))

    return data['results'][0]['series'][0]['columns'], data['results'][0]['series'][0]['values']


def _query_influx_data_groupby(client, db, query, datetime=False):
    if datetime:
        epoch = 'rfc3339'
    else:
        epoch = 'ns'

    fields = {'db':db, 'q':query, 'epoch':epoch}
    headers = {"Content-Type": "application/json"}
    headers.update(client.headers)

    response = client.request('GET', '/query', fields=fields, headers=headers)
    data = json.loads(response.data.decode('utf-8'))

    return data['results'][0]['series'][0]['columns'], [row['values'][0] for row in data['results'][0]['series']]


def _format_point(point, schema, datetime=False):
    if not datetime:
        return {
            'time': utils.unix_to_gps(point[0]),
            'fields': dict(zip(schema['columns'], point[1:(len(point)-len(schema['tags']))])),
            'tags': dict(zip(schema['tags'], point[(1+len(schema['columns'])):]))
        }
    else:
        return {
            'time': point[0],
            'fields': dict(zip(schema['columns'], point[1:(len(point)-len(schema['tags']))])),
            'tags': dict(zip(schema['tags'], point[(1+len(schema['columns'])):])),
        }
