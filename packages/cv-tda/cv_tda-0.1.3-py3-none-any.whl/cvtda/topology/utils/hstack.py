import typing

import numpy


def deduce_depth(data):
    if (isinstance(data, numpy.ndarray) or isinstance(data, list)) and len(data) > 0:
        return deduce_depth(data[0]) + 1
    return 0

def hstack(data: typing.List[numpy.ndarray], force_numpy: bool):
    if force_numpy:
        return numpy.hstack(data)
    else:
        data = [ item for item in data if len(item) > 0 ]
        if len(data) == 0: return []
        assert len(set([ len(item) for item in data ])) == 1

        for i in range(len(data)):
            if deduce_depth(data[i]) == 3:
                data[i] = numpy.expand_dims(data[i], 1)

            assert deduce_depth(data[i]) == 4, f"Bad depth: {deduce_depth(data[i])}"

        return [ sum([ list(item[i]) for item in data ], []) for i in range(len(data[0])) ]
