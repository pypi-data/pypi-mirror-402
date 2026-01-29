import numpy

from ligo.scald import transforms


class TestTransforms(object):
    """
    Tests several aspects of transforms.py to check basic functionality.
    """
    def test_identity(self):
        default = 1000
        identity = transforms.identity(1, 2, default)
        assert identity == 2, 'expected identity: {}, got: {}'.format(2, identity)

        identity = transforms.identity([], [], default)
        assert identity == default, 'expected identity: {}, got: {}'.format(default, identity)


    def test_latency(self):
        t0 = 20
        default = 1000
        latency = transforms.latency(12, 2.37, default, t0=t0)
        assert latency == t0 - 12, 'expected latency: {}, got: {}'.format(t0 - 12, latency)

        latency = transforms.latency([12.5, 13.2], [2.12, 3.13], default, t0=t0)
        assert numpy.around(latency, 3) == 6.8, 'expected latency: {}, got: {}'.format(6.8, latency)

        latency = transforms.latency([], [], default, t0=t0)
        assert latency == default, 'expected latency: {}, got: {}'.format(default, latency)


    def test_cutoff(self):
        threshold = 12
        default = 100
        cutoff = transforms.cutoff([0], [2.37], default, threshold)
        assert cutoff == 2.37, 'expected cutoff: {}, got: {}'.format(2.37, cutoff)

        cutoff = transforms.cutoff([0, 1, 2], [2.37, 6, 9], default, threshold)
        assert cutoff == 9, 'expected cutoff: {}, got: {}'.format(9, cutoff)

        cutoff = transforms.cutoff([0, 1, 2], [2.37, 13.2, 9], default, threshold)
        assert cutoff == default, 'expected cutoff: {}, got: {}'.format(default, cutoff)

        cutoff = transforms.cutoff([], [], default, threshold)
        assert cutoff == default, 'expected cutoff: {}, got: {}'.format(default, cutoff)
