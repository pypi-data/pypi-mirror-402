import numpy

def spread_points(size: int, num_points: int):
    assert size % 2 == 0, 'Odd size is not implemented'
    
    center, spacing = size // 2, size // (num_points + 1)
    centers = numpy.array(range((spacing + 1) // 2, center, spacing + 1))
    centers = numpy.array([ *(center - centers - 1), *(center + centers) ])
    if num_points % 2 == 1:
        centers = numpy.array([ *centers, center ])
    centers.sort()
    return centers
