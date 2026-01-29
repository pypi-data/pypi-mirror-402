import argparse
import bisect
import functools
import time

from datetime import datetime
from dateutil.tz import tzutc
from dateutil.parser import parse as str_to_utc

import numpy

EPOCH_UNIX_GPS = 315964800

leapseconds_table = [
    46828800,   # 1981-Jul-01
    78364801,   # 1982-Jul-01
    109900802,  # 1983-Jul-01
    173059203,  # 1985-Jul-01
    252028804,  # 1988-Jan-01
    315187205,  # 1990-Jan-01
    346723206,  # 1991-Jan-01
    393984007,  # 1992-Jul-01
    425520008,  # 1993-Jul-01
    457056009,  # 1994-Jul-01
    504489610,  # 1996-Jan-01
    551750411,  # 1997-Jul-01
    599184012,  # 1999-Jan-01
    820108813,  # 2006-Jan-01
    914803214,  # 2009-Jan-01
    1025136015, # 2012-Jul-01
    1119744016, # 2015-Jul-01
    1167264017, # 2017-Jan-01
]

def leapseconds(gpstime):
    return bisect.bisect_left(leapseconds_table, gpstime)


def stats_on_data(data):
    return float(numpy.min(data)), float(numpy.percentile(data, 15.9)), float(numpy.percentile(data, 84.1)), float(numpy.max(data))


def gps_range_to_process(jobtime, dt=1):
    if jobtime:
        gpsblocks = set((floor_div(t, dt) for t in jobtime))
        if not gpsblocks:
            return [], []
        min_t, max_t = min(gpsblocks), max(gpsblocks)
        return zip(range(min_t, max_t + dt, dt), range(min_t + dt, max_t + 2*dt, dt))
    else:
        return None


def span_to_process(start, end, dt=1):
    return floor_div(start, dt), floor_div(end, dt) + dt


def duration_to_dt(duration):
    """
    Given a time duration, returns back the sampling rate of timeseries
    such that a maximum of 1000 points are plotted at a given time.

    This is used as a default if the user doesn't specify a dt explicitly.

    >>> duration_to_dt(900)
    1
    >>> duration_to_dt(11000)
    100

    """
    if duration <= 1000:
        dt = 1
    elif duration <= 10000:
        dt = 10
    elif duration <= 100000:
        dt = 100
    elif duration <= 1000000:
        dt = 1000
    elif duration <= 10000000:
        dt = 10000
    else:
        dt = 100000

    return dt


def in_new_epoch(new_gps_time, prev_gps_time, gps_epoch):
    """
    Returns whether new and old gps times are in different
    epochs.

    >>> in_new_epoch(1234561200, 1234560000, 1000)
    True
    >>> in_new_epoch(1234561200, 1234560000, 10000)
    False

    """
    return (new_gps_time - floor_div(prev_gps_time, gps_epoch)) >= gps_epoch


def floor_div(x, n):
    """
    Floor a number by removing its remainder
    from division by another number n.

    >>> floor_div(163, 10)
    160
    >>> floor_div(158, 10)
    150

    """
    assert n > 0

    if isinstance(x, int) or (isinstance(x, numpy.ndarray) and numpy.issubdtype(x.dtype, numpy.integer)):
        return (x // n) * n
    elif isinstance(x, numpy.ndarray):
        return (x.astype(float) // n) * n
    else:
        return (float(x) // n) * n


def gps_now():
    """
    Returns the current gps time.
    """
    gpsnow = time.time() - EPOCH_UNIX_GPS
    return gpsnow + leapseconds(gpsnow)


def gps_to_latency(gps_time):
    """
    Given a gps time, measures the latency to ms precision relative to now.
    """
    return numpy.round(gps_now() - gps_time, 3)


def rfc3339_to_gps(time_str):
    """
    converts an rfc3339-formatted string (UTC+0 only) to a valid gps time.
    """
    if time_str[-1] != 'Z':
        raise ValueError('missing Z indicating UTC+0')

    #utc = str_to_utc(time_str[:-1])
    utc = str_to_utc(time_str, tzinfos={'Z': 0})
    tdelta = utc - datetime.fromtimestamp(0, tzutc())
    gps_time = tdelta.total_seconds() - EPOCH_UNIX_GPS
    return gps_time + leapseconds(gps_time)


def gps_to_unix(gps_time):
    """
    Converts from GPS to UNIX time, allows use of numpy arrays or scalars.
    """
    if isinstance(gps_time, numpy.ndarray):
        leapsec = leapseconds(int(gps_time[0]))
        return ((gps_time + EPOCH_UNIX_GPS - leapsec) * 1e9).astype(int)
    else:
        leapsec = leapseconds(int(gps_time))
        return int((gps_time + EPOCH_UNIX_GPS - leapsec) * 1e9)


def unix_to_gps(unix_time):
    """
    Converts from UNIX to GPS time, allows use of numpy arrays or scalars.
    """
    ### FIXME: doesn't handle leapseconds correctly
    return (unix_time / 1e9) - EPOCH_UNIX_GPS + 18


def status_to_nagios_response(text_status, bad_status):
    return {
        "nagios_shib_scraper_ver": 0.1,
        "status_intervals": [{
            "num_status": 2 if bad_status else 0,
            "txt_status": text_status,
        }],
    }


def extract_alert_tags(schema):
    if 'tags' in schema:
        return schema['tags']
    else:
        tag_type = schema['tag_key']
        alert_tag_format = schema['tag_format']
        if 'digit' in alert_tag_format:
            num_digits = int(alert_tag_format[0])
            num_tags = int(schema['num_tags'])
            tag_start = int(schema['tag_start']) if 'tag_start' in schema else 0
            return [(tag_type, str(tag_num).zfill(num_digits)) for tag_num in range(tag_start, tag_start+num_tags)]
        else:
            raise ValueError('{} tag format not recognized'.format(alert_tag_format))


def append_subparser(subparser, cmd, func):
    assert func.__doc__, "empty docstring: {}".format(func)
    help_ = func.__doc__.split('\n')[0].lower().strip('.')
    desc = func.__doc__.strip()

    parser = subparser.add_parser(
        cmd,
        formatter_class=argparse.RawDescriptionHelpFormatter,
        help=help_,
        description=desc
    )

    parser.set_defaults(func=func)
    return parser


def unpack(func):
    """
    Unpacks an argument tuple and calls the target function 'func'.
    Used as a workaround for python 2 missing multiprocessing.Pool.starmap.

    Implemented from https://stackoverflow.com/a/52671399.

    """
    @functools.wraps(func)
    def wrapper(arg_tuple):
        return func(*arg_tuple)
    return wrapper
