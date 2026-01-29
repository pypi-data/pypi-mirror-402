import numpy

def aggregate(diff: numpy.ndarray) -> float:
    axes = tuple(set(range(len(diff.shape))) - set([0]))
    return numpy.sum(diff, axis = axes).mean()


def estimate_quality(decoded: numpy.ndarray, original: numpy.ndarray) -> dict:
    decoded = numpy.squeeze(decoded)
    original = numpy.squeeze(original)
    return {
        'MAE': aggregate(numpy.abs(original - decoded)),
        'MSE': aggregate((original - decoded) ** 2)
    }
