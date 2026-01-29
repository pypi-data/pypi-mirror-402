import statistics

import pytest

import numpy

from ligo.scald.io import core


class TestIOCore(object):
    """
    Tests several aspects of mock.py to check basic functionality.
    """
    @pytest.mark.parametrize("agg, func", [('min', min), ('median', statistics.median_high), ('max', max)])
    def test_aggregate_to_func(self, agg, func):
        expected = core.aggregate_to_func(agg)
        assert expected == func


    @pytest.mark.parametrize("func, idx", [(min, 0), (statistics.median_high, 5), (max, 9)])
    def test_reduce_data(self, func, idx):
        xarr = numpy.arange(10)
        yarr = numpy.arange(10)
        reduced_idx, reduced_x, reduced_y = core.reduce_data(xarr, yarr, func, dt=10)
        reduced_idx = reduced_idx[0] # checking only single idx
        assert len(reduced_x) == 1, 'expected x length: {}, got: {}'.format(1, len(reduced_x))
        assert len(reduced_y) == 1, 'expected y length: {}, got: {}'.format(1, len(reduced_y))
        assert yarr[reduced_idx] == idx, 'expected aggregate: {}, got: {}'.format(idx, yarr[reduced_idx])
        assert reduced_idx == idx, 'expected aggregate idx: {}, got: {}'.format(idx, reduced_idx)
