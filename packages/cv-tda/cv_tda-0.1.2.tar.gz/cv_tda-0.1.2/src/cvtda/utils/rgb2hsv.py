import numpy

import skimage.color

import cvtda.utils
import cvtda.logging


def rgb2hsv(images: numpy.ndarray, n_jobs: int = -1) -> numpy.ndarray:
    return numpy.stack(
        cvtda.utils.parallel(
            skimage.color.rgb2hsv, cvtda.logging.logger().pbar(images, desc = "rgb2hsv"),
            n_jobs = n_jobs, return_as = 'list', num_parameters = 1
        )
    )
