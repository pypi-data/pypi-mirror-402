import pytest

import numpy

from ligo.scald import utils


class TestUtils(object):
    """
    Tests several aspects of utils.py to check basic functionality.
    """
    @pytest.mark.parametrize("time, leap", [(0, 0), (1187000000, 18)])
    def test_leapseconds(self, time, leap):
        calc_leap = utils.leapseconds(time)
        assert calc_leap == leap, (
            'leapseconds expected: {}, '
            'got: {} for time: {}'.format(leap, calc_leap, time)
        )


    @pytest.mark.parametrize(
        "start, end, dt, span",
        [(0, 999, 1, (0, 1000)), (0, 382, 10, (0, 390))]
    )
    def test_span_to_process(self, start, end, dt, span):
        calc_span = utils.span_to_process(start, end, dt=dt)
        assert calc_span == span, (
            'span expected: {}, got: {}, '
            'for start: {}, end: {}, dt: {}'.format(span, calc_span, start, end, dt)
        )


    @pytest.mark.parametrize(
        "gps_time, unix", [
            (1187000000.123456, 1502964782123456000),
            (
                numpy.array([1187000000.123456, 1187100000]),
                numpy.array([1502964782123456000, 1503064782000000000])
            )
        ]
    )
    def test_gps_to_unix(self, gps_time, unix):
        calc_unix = utils.gps_to_unix(gps_time)
        equals = numpy.equal(calc_unix, unix)
        assert numpy.all(equals), (
            'unix time expected: {}, '
            'got: {} for time: {}'.format(unix, calc_unix, gps_time)
        )
