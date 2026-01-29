# Copyright (C) 2016  Kipp Cannon, Chad Hanna
#
# This program is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the
# Free Software Foundation; either version 2 of the License, or (at your
# option) any later version.
#
# This program is distributed in the hope that it will be useful, but
# WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU General
# Public License for more details.
#
# You should have received a copy of the GNU General Public License along
# with this program; if not, write to the Free Software Foundation, Inc.,
# 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.


import collections
import json
import os
import statistics

import numpy


MIN_TIME_QUANTA = 10000
DIRS = 6


_aggregate_func_map = {
    "median": statistics.median_high,
    "min": min,
    "max": max,
}


def aggregate_to_func(aggregate):
    """!
    Given an aggregate string, returns back a function that does that
    aggregation.
    """
    if aggregate not in _aggregate_func_map:
        raise NotImplementedError
    return _aggregate_func_map[aggregate]


def reduce_data(xarr, yarr, func, dt = 1):
    """!
    This function does a data reduction by powers of 10 where dt
    specifies the spacing.  Default is 1 e.g., data reduction over 1 second
    """
    datadict = collections.OrderedDict()
    assert len(yarr) == len(xarr), 'x and y arrays are not equal'
    for idx, (x, y) in enumerate(zip(xarr, yarr)):
        # reduce to this level
        key = int(x) // dt
        # we want to sort on y not x
        datadict.setdefault(key, []).append((y,x,idx))
    reduced = [func(value) for value in datadict.values()]
    reduced_data, reduced_time, reduced_idx = zip(*reduced)
    assert len(reduced_data) == len(reduced_time)
    sort_idx = numpy.argsort(reduced_time)

    return reduced_idx, list(numpy.array(reduced_time)[sort_idx]), list(numpy.array(reduced_data)[sort_idx])


def makedir(path):
    """!
    A convenience function to make new directories and trap errors
    """
    try:
        os.makedirs(path)
    except IOError:
        pass
    except OSError:
        pass


def gps_to_minimum_time_quanta(gpstime):
    """!
    given a gps time return the minimum time quanta, e.g., 123456789 ->
    123456000.
    """
    return int(gpstime) // MIN_TIME_QUANTA * MIN_TIME_QUANTA


def gps_range(jobtime):
    gpsblocks = set((gps_to_minimum_time_quanta(t) for t in jobtime))
    if not gpsblocks:
        return [], []
    min_t, max_t = min(gpsblocks), max(gpsblocks)
    return range(min_t, max_t+MIN_TIME_QUANTA, MIN_TIME_QUANTA), range(min_t+MIN_TIME_QUANTA, max_t+2*MIN_TIME_QUANTA, MIN_TIME_QUANTA)


def job_expanse(dataspan):
    if dataspan:
        min_t, max_t = min(dataspan), max(dataspan)
        return range(min_t, max_t+MIN_TIME_QUANTA, MIN_TIME_QUANTA), range(min_t+MIN_TIME_QUANTA, max_t+2*MIN_TIME_QUANTA, MIN_TIME_QUANTA)
    else:
        return [], []


def gps_to_leaf_directory(gpstime, level = 0):
    """Get the leaf directory for a given gps time.

    """
    return "/".join(str(gps_to_minimum_time_quanta(gpstime) // MIN_TIME_QUANTA // (10**level)))


def store_snapshot(webdir, measurement, data, dims, time, **attrs):
    """Stores a JSON-formatted snapshot to disk.

    Parameters
    ----------
    webdir : `str`
        the directory where snapshots are stored, should
        be web accessible (e.g. public_html)
    measurement : `str`
        the measurement name
    data : `dict`
        a mapping from a column to 1-dim data
    dims : `dict`
        a mapping from a dimension (one of x, y, z) to a column,
        either 2-dim (x, y) or 3-dim (x, y, z).
    time : `int`
        the time the snapshot was taken

    """
    ### set up JSON structure
    snapshot = {'time': time, 'measurement': measurement}
    snapshot.update(data)
    snapshot.update(dims)
    snapshot.update({'metadata': attrs})

    ### create directories
    leafdir = gps_to_leaf_directory(time)
    snapshot_dir = os.path.join(webdir, 'snapshots', leafdir)
    makedir(snapshot_dir)

    ### save snapshot to disk
    filename = '{}_{}.json'.format(measurement, time)
    filepath = os.path.join(snapshot_dir, filename)
    with open(filepath, 'w') as f:
        f.write(json.dumps(snapshot))

    ### symlink latest snapshot
    sympath = os.path.join(webdir, 'snapshots', 'latest', '{}.json'.format(measurement))
    try:
        os.symlink(filepath, sympath)
    except OSError:
        os.remove(sympath)
        os.symlink(filepath, sympath)
