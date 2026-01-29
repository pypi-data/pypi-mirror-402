import typing

import torch

import cvtda.neural_network
from .BaseLearner import BaseLearner


class SimpleTopologicalLearner(BaseLearner):
    def fit(self, train: cvtda.neural_network.Dataset, val: typing.Optional[cvtda.neural_network.Dataset]):
        pass

    def calculate_distance_(self, first: int, second: int, dataset: cvtda.neural_network.Dataset):
        return torch.sqrt(torch.sum((dataset.features[first] - dataset.features[second]) ** 2))
