import numpy

import skimage.color

import cvtda.utils
import cvtda.logging


def rgb2gray(images: numpy.ndarray, n_jobs: int = -1) -> numpy.ndarray:
    return numpy.stack(
        cvtda.utils.parallel(
            skimage.color.rgb2gray, cvtda.logging.logger().pbar(images, desc = "rgb2gray"),
            n_jobs = n_jobs, return_as = 'list', num_parameters = 1
        )
    )
