import abc
import typing

import numpy
import itertools
import matplotlib.pyplot as plt

import cvtda.utils
import cvtda.logging
import cvtda.neural_network


class BaseLearner(abc.ABC):
    def __init__(self, n_jobs: int = -1):
        self.n_jobs_ = n_jobs

    
    @abc.abstractmethod
    def fit(self, train: cvtda.neural_network.Dataset, val: typing.Optional[cvtda.neural_network.Dataset]):
        pass

            
    def estimate_quality(
        self,
        dataset: cvtda.neural_network.Dataset,
        ax: typing.Optional[plt.Axes] = None
    ):
        def calculate_distance_(i: int, j: int):
            return (i, j, self.calculate_distance_(i, j, dataset))

        idxs = list(itertools.product(range(len(dataset)), range(len(dataset))))
        pbar = cvtda.logging.logger().pbar(idxs, desc = "Calculating pairwise distances")
        distances_flat = cvtda.utils.parallel(calculate_distance_, pbar, n_jobs = self.n_jobs_)

        correct_dists, incorrect_dists = {}, {}
        for i, j, distance in cvtda.logging.logger().pbar(distances_flat, desc = "Analyzing distances"):
            label1, label2 = dataset.get_labels([ i, j ])
            if label1 == label2:
                correct_dists[(i, j)] = distance
            else:
                incorrect_dists[(i, j)] = distance
        correct_dists_values = list(correct_dists.values())
        incorrect_dists_values = list(incorrect_dists.values())
        
        if ax is not None:
            ax.set_ylim(0, 1)
            ax.get_yaxis().set_ticks([])
            ax.plot(correct_dists_values, numpy.ones_like(correct_dists_values) * 0.35, 'x', label = "Same person")
            ax.plot(incorrect_dists_values, numpy.ones_like(incorrect_dists_values) * 0.65, 'x', label = "Different people")
        return correct_dists, incorrect_dists


    @abc.abstractmethod
    def calculate_distance_(self, first: int, second: int, dataset: cvtda.neural_network.Dataset):
        pass