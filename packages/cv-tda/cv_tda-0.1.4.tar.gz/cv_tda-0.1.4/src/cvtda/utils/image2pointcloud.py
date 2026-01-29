import numpy
import typing

import cvtda.utils
import cvtda.logging


def image2pointcloud(images: numpy.ndarray, n_jobs: int = -1) -> typing.List[numpy.ndarray]:
    def _impl(image: numpy.ndarray) -> numpy.ndarray:
        width, height = image.shape[0:2]
        x = numpy.indices((width, height))[0]
        y = numpy.indices((width, height))[1]
        return numpy.dstack([ x, y, image ]).reshape((width * height, -1))

    return cvtda.utils.parallel(
        _impl, cvtda.logging.logger().pbar(images, desc = "image2pointcloud"),
        n_jobs = n_jobs, return_as = 'list'
    )
