import numpy

from ligo.scald import mock, utils


class TestMock(object):
    """
    Tests several aspects of mock.py to check basic functionality.
    """
    def test_random_trigger_value(self):
        far = mock.random_trigger_value('far', 1)
        assert numpy.issubdtype(far.dtype.type, float), 'expected type float for far'
        assert far <= 1e-2, 'expected far <= far threshold'

        snr = mock.random_trigger_value('snr', 1)
        assert numpy.issubdtype(snr.dtype.type, float), 'expected type float for snr'
        assert snr >= 0, 'expected snr >= 0'

        seg = mock.random_trigger_value('segment', 10)
        assert isinstance(seg, numpy.ndarray), 'expected segment to be numpy.ndarray'
        assert numpy.issubdtype(seg.dtype.type, int), 'expected type int for snr'
        assert numpy.all((seg == 1) | (seg == 0)), 'expected segment values to be either 0 or 1'

        runiform = mock.random_trigger_value('rand', 5)
        assert isinstance(runiform, numpy.ndarray), 'expected random uniform to be numpy.ndarray'
        assert numpy.issubdtype(runiform.dtype.type, float), 'expected type float for random uniform'
        assert numpy.all((runiform >= 0) & (runiform <= 1)), 'expected segment values to be between 0 and 1'


    def test_generate_timeseries(self):
        fields = ['snr']
        series = mock.generate_timeseries(0, 100, 'test', fields, 'max', 1)
        for key in ['name', 'columns', 'values']:
            assert key in series[0], 'expected {} in series'.format(key)
        for field in ['time', 'snr']:
            assert field in series[0]['columns'], 'expected {} in columns'.format(field)

        times = numpy.arange(0, 101, 1)
        assert len(series[0]['values']) == len(times), 'expected {} datapoints in series'.format(len(times))

        calc_times = numpy.array([row[0] for row in series[0]['values']])
        assert numpy.all((calc_times >= utils.gps_to_unix(0)) & (calc_times <= utils.gps_to_unix(100))), 'expected times to be in gps range specified'


    def test_generate_triggers(self):
        fields = ['far', 'snr']
        triggers = mock.generate_triggers(0, 100, 'test', fields, 1e-2, num_triggers=10)
        for key in ['name', 'columns', 'values']:
            assert key in triggers[0], 'expected {} in triggers'.format(key)
        for field in ['time', 'far', 'snr']:
            assert field in triggers[0]['columns'], 'expected {} in columns'.format(field)
        assert len(triggers[0]['values']) == 10, 'expected 10 triggers'

        times = numpy.array([row[0] for row in triggers[0]['values']])
        assert numpy.all((times >= utils.gps_to_unix(0)) & (times <= utils.gps_to_unix(100))), 'expected times to be in gps range specified'
