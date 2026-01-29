from . import utils


def identity(time, data, default):
	return data if data else default


def latency(time, data, default, t0=None):
    if t0 is None:
        t0 = utils.gps_now()
    if time and isinstance(time, list):
        return max(t0 - time[-1], 0)
    elif time:
        return max(t0 - time, 0)
    else:
        return default


def cutoff(time, data, default, cutoff):
    if data:
        max_data = max(data)
        if max_data < cutoff:
            return max_data
        else:
            return default
    else:
        return default 
