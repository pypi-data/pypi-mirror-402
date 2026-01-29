import os
import typing

import numpy
import torch
import torchvision
import matplotlib.pyplot as plt

import cvtda.logging
import cvtda.dumping
import cvtda.neural_network

from .BaseLearner import BaseLearner
from .DiagramsLearner import DiagramsLearner
from .NNLearner import NNLearner
from .SimpleTopologicalLearner import SimpleTopologicalLearner

def learn(
    train_images: numpy.ndarray,
    train_features: numpy.ndarray,
    train_labels: numpy.ndarray,
    train_diagrams: typing.List[numpy.ndarray],

    test_images: numpy.ndarray,
    test_features: numpy.ndarray,
    test_labels: numpy.ndarray,
    test_diagrams: typing.List[numpy.ndarray],

    n_jobs: int = 1,
    random_state: int = 42,
    dump_name: typing.Optional[str] = None,

    nn_device: torch.device = cvtda.neural_network.default_device,
    nn_batch_size: int = 32,
    nn_learning_rate: float = 1e-3,
    nn_epochs: int = 25,
    nn_margin: int = 0.1,
    nn_latent_dim: int = 256,
    nn_length_before_new_iter: typing.Optional[int] = None,
    nn_base = torchvision.models.resnet34
):
    nn_train = cvtda.neural_network.Dataset(
        train_images, train_diagrams, train_features, train_labels, n_jobs = n_jobs, device = nn_device
    )
    nn_test = cvtda.neural_network.Dataset(
        test_images, test_diagrams, test_features, test_labels, n_jobs = n_jobs, device = nn_device
    )

    def classify_one(learner: BaseLearner, name: str, display_name: str, ax: plt.Axes):
        cvtda.logging.logger().print(f'Trying {name} - {learner}')
        learner.fit(nn_train, nn_test)
        ax.set_title(display_name)
        learner.estimate_quality(nn_test, ax)

    nn_kwargs = dict(
        n_jobs = n_jobs,
        random_state = random_state,
        device = nn_device,
        batch_size = nn_batch_size,
        learning_rate = nn_learning_rate,
        margin = nn_margin,
        latent_dim = nn_latent_dim,
        length_before_new_iter = nn_length_before_new_iter
    )
    classifiers = [
        SimpleTopologicalLearner(n_jobs = n_jobs),
        DiagramsLearner(n_jobs = n_jobs),
        NNLearner(**nn_kwargs, n_epochs = nn_epochs,      skip_diagrams = True,  skip_images = False, skip_features = True,  base = nn_base),
        NNLearner(**nn_kwargs, n_epochs = nn_epochs * 2,  skip_diagrams = True,  skip_images = True,  skip_features = False, base = nn_base),
        NNLearner(**nn_kwargs, n_epochs = nn_epochs,      skip_diagrams = True,  skip_images = False, skip_features = False, base = nn_base),
        NNLearner(**nn_kwargs, n_epochs = nn_epochs // 2, skip_diagrams = False, skip_images = True,  skip_features = True,  base = nn_base)
    ]

    names = [
        'SimpleTopologicalLearner',
        'DiagramsLearner',
        'NNLearner_images',
        'NNLearner_features',
        'NNLearner_features_images',
        'NNLearner_diagrams'
    ]
    display_names = [
        'Topological features',
        'Persistence diagrams',
        'Baseline model',
        'FC over topological features',
        'Combined neural network',
        'Trainable vectorization'
    ]

    figure, axes = plt.subplots(2, 3, figsize = (12, 5))
    for args in zip(classifiers, names, display_names, axes.flat):
        classify_one(*args)

    handles, labels = axes.flat[0].get_legend_handles_labels()
    figure.legend(handles, labels, loc = (0.35, 0.75))

    figure.tight_layout()

    dumper = cvtda.dumping.dumper()
    if (dump_name is not None) and isinstance(dumper, cvtda.dumping.NumpyDumper):
        file = dumper.get_file_name_(cvtda.dumping.dump_name_concat(dump_name, "distributions"))
        os.makedirs(os.path.dirname(file), exist_ok = True)
        figure.savefig(file[:-4] + ".svg")
        figure.savefig(file[:-4] + ".png")
    return figure