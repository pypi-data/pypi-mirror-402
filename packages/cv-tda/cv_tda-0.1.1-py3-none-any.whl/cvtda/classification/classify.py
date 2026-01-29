import os
import typing

import numpy
import torch
import pandas
import xgboost
import catboost
import torchvision
import sklearn.base
import sklearn.ensemble
import sklearn.neighbors
import matplotlib.pyplot as plt

import cvtda.logging
import cvtda.dumping
import cvtda.neural_network

from .NNClassifier import NNClassifier
from .estimate_quality import estimate_quality

def classify(
    train_images: numpy.ndarray,
    train_features: numpy.ndarray,
    train_labels: numpy.ndarray,
    train_diagrams: typing.Optional[typing.List[numpy.ndarray]],

    test_images: numpy.ndarray,
    test_features: numpy.ndarray,
    test_labels: numpy.ndarray,
    test_diagrams: typing.Optional[typing.List[numpy.ndarray]],

    label_names: typing.Optional[typing.List[str]] = None,
    confusion_matrix_include_values: bool = True,

    n_jobs: int = -1,
    random_state: int = 42,
    dump_name: typing.Optional[str] = None,
    only_get_from_dump: bool = False,

    knn_neighbours: int = 50,

    random_forest_estimators: int = 100,

    nn_device: torch.device = cvtda.neural_network.default_device,
    nn_batch_size: int = 128,
    nn_learning_rate: float = 1e-3,
    nn_epochs: int = 20,
    nn_base = torchvision.models.resnet34,

    grad_boost_max_iter: int = 20,
    grad_boost_max_depth: int = 4,
    grad_boost_max_features: float = 0.1,

    xgboost_n_classifiers: int = 25,
    xgboost_max_depth: int = 4,
    xgboost_device: str = 'gpu',

    catboost_iterations: int = 600,
    catboost_depth: int = 4,
    catboost_device: str = ('GPU' if torch.cuda.is_available() else 'CPU')
):
    without_diagrams = (train_diagrams is None) and (test_diagrams is None)

    if (train_images is not None) and (not only_get_from_dump):
        nn_train = cvtda.neural_network.Dataset(
            train_images, train_diagrams, train_features, train_labels, n_jobs = n_jobs, device = nn_device
        )
        nn_test = cvtda.neural_network.Dataset(
            test_images, test_diagrams, test_features, test_labels, n_jobs = n_jobs, device = nn_device
        )

    def classify_one(classifier: sklearn.base.ClassifierMixin, name: str, display_name: str, ax: plt.Axes):
        if without_diagrams and name == 'NNClassifier_diagrams':
            cvtda.logging.logger().print(f'Skipping {name} - {classifier}')
            return {}

        cvtda.logging.logger().print(f'Trying {name} - {classifier}')

        dumper = cvtda.dumping.dumper()
        model_dump_name = cvtda.dumping.dump_name_concat(dump_name, name)
        if only_get_from_dump or dumper.has_dump(model_dump_name):
            y_pred_proba = dumper.get_dump(model_dump_name)
        else:
            if type(classifier) == NNClassifier:
                classifier.fit(nn_train, nn_test)
                y_pred_proba = classifier.predict_proba(nn_test)
            else:
                classifier.fit(train_features, train_labels)
                y_pred_proba = classifier.predict_proba(test_features)

            if model_dump_name is not None:
                dumper.save_dump(y_pred_proba, model_dump_name)
                
        ax.set_title(display_name)
        result = {
            'classifier': display_name,
            **estimate_quality(
                y_pred_proba, test_labels, ax,
                label_names = label_names, confusion_matrix_include_values = confusion_matrix_include_values
            )
        }
        cvtda.logging.logger().print(result)
        return result

    classifiers = [
        sklearn.neighbors.KNeighborsClassifier(
            n_jobs = n_jobs,
            n_neighbors = knn_neighbours
        ),
        sklearn.ensemble.RandomForestClassifier(
            n_estimators = random_forest_estimators,
            random_state = random_state,
            n_jobs = n_jobs
        ),
        sklearn.ensemble.HistGradientBoostingClassifier(
            random_state = random_state,
            max_iter = grad_boost_max_iter,
            max_depth = grad_boost_max_depth,
            max_features = grad_boost_max_features,
            verbose = cvtda.logging.logger().verbosity()
        ),
        catboost.CatBoostClassifier(
            iterations = catboost_iterations,
            depth = catboost_depth,
            random_seed = random_state,
            loss_function = 'MultiClass',
            devices = '0-3',
            task_type = catboost_device,
            verbose = (cvtda.logging.logger().verbosity() != 0)
        ),
        xgboost.XGBClassifier(
            n_jobs = n_jobs,
            n_estimators = xgboost_n_classifiers,
            max_depth = xgboost_max_depth,
            device = xgboost_device
        ),
        NNClassifier(
            random_state = random_state,
            device = nn_device,
            batch_size = nn_batch_size,
            learning_rate = nn_learning_rate * 10,
            n_epochs = nn_epochs * 2,
            skip_diagrams = True,
            skip_images = True,
            skip_features = False,
            base = nn_base,
        ),
        NNClassifier(
            random_state = random_state,
            device = nn_device,
            batch_size = nn_batch_size,
            learning_rate = nn_learning_rate,
            n_epochs = nn_epochs // 2,
            skip_diagrams = False,
            skip_images = True,
            skip_features = True,
            base = nn_base,
        ),
        NNClassifier(
            random_state = random_state,
            device = nn_device,
            batch_size = nn_batch_size,
            learning_rate = nn_learning_rate,
            n_epochs = nn_epochs,
            skip_diagrams = True,
            skip_images = False,
            skip_features = True,
            base = nn_base,
        ),
        NNClassifier(
            random_state = random_state,
            device = nn_device,
            batch_size = nn_batch_size,
            learning_rate = nn_learning_rate,
            n_epochs = nn_epochs,
            skip_diagrams = True,
            skip_images = False,
            skip_features = False,
            base = nn_base,
        )
    ]
    names = [
        'KNeighborsClassifier',
        'RandomForestClassifier',
        'HistGradientBoostingClassifier',
        'CatBoostClassifier',
        'XGBClassifier',
        'NNClassifier_features',
        'NNClassifier_diagrams',
        'NNClassifier_images',
        'NNClassifier_features_images'
    ]

    display_names = [
        'KNN',
        'Random forest',
        'Histogram-based boosting',
        'CatBoost',
        'XGBoost',
        'FC over topological features',
        'Trainable vectorization',
        'Baseline model',
        'Combined neural network'
    ]

    figure, axes = plt.subplots(3, 3, figsize = (15, 15))
    df = pandas.DataFrame([ classify_one(*args) for args in zip(classifiers, names, display_names, axes.flat) ])
    figure.tight_layout()

    dumper = cvtda.dumping.dumper()
    if (dump_name is not None) and isinstance(dumper, cvtda.dumping.NumpyDumper):
        file = dumper.get_file_name_(cvtda.dumping.dump_name_concat(dump_name, "confusion_matrixes"))
        os.makedirs(os.path.dirname(file), exist_ok = True)
        figure.savefig(file[:-4] + ".svg")
        figure.savefig(file[:-4] + ".png")
        df.to_csv(dumper.get_file_name_(cvtda.dumping.dump_name_concat(dump_name, "quality_metrics.csv"))[:-4])
    return df, figure
