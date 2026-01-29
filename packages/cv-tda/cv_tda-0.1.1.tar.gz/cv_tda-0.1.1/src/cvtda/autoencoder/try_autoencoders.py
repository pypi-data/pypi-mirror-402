import typing

import numpy
import torch
import pandas
import torchvision

import cvtda.logging
import cvtda.dumping
import cvtda.neural_network

from .Autoencoder import Autoencoder
from .estimate_quality import estimate_quality

def try_autoencoders(
    train_images: numpy.ndarray,
    train_features: numpy.ndarray,
    train_diagrams: typing.Optional[typing.List[numpy.ndarray]],

    test_images: numpy.ndarray,
    test_features: numpy.ndarray,
    test_diagrams: typing.Optional[typing.List[numpy.ndarray]],

    n_jobs: int = -1,
    random_state: int = 42,
    dump_name: typing.Optional[str] = None,
    only_get_from_dump: bool = False,

    nn_device: torch.device = cvtda.neural_network.default_device,
    nn_batch_size: int = 128,
    nn_learning_rate: float = 1e-3,
    nn_epochs: int = 20,
    nn_latent_dim: int = 256,
    nn_base = torchvision.models.resnet34
):
    without_diagrams = (train_diagrams is None) and (test_diagrams is None)

    if (train_images is not None) and (not only_get_from_dump):
        nn_train = cvtda.neural_network.Dataset(
            train_images, train_diagrams, train_features, None, n_jobs = n_jobs, device = nn_device
        )
        nn_test = cvtda.neural_network.Dataset(
            test_images, test_diagrams, test_features, None, n_jobs = n_jobs, device = nn_device
        )

    def try_one(model: Autoencoder, name: str, display_name: str):
        if without_diagrams and name == 'diagrams':
            cvtda.logging.logger().print(f'Skipping {name} - {model}')
            return {}

        cvtda.logging.logger().print(f'Trying {name} - {model}')

        dumper = cvtda.dumping.dumper()
        encoded_dump_name = cvtda.dumping.dump_name_concat(dump_name, f'{name}_encoded')
        decoded_dump_name = cvtda.dumping.dump_name_concat(dump_name, f'{name}_decoded')
        if only_get_from_dump or dumper.has_dump(decoded_dump_name):
            decoded = dumper.get_dump(decoded_dump_name)
        else:
            model.fit(nn_train, nn_test)
            encoded = model.encode(nn_test)
            decoded = model.decode(encoded)

            if encoded_dump_name is not None:
                dumper.save_dump(encoded, encoded_dump_name)
            if decoded_dump_name is not None:
                dumper.save_dump(decoded, decoded_dump_name)
                
        result = { 'model': display_name, **estimate_quality(decoded, test_images) }
        cvtda.logging.logger().print(result)
        return result

    models = [
        Autoencoder(
            random_state = random_state,
            device = nn_device,
            batch_size = nn_batch_size,
            learning_rate = nn_learning_rate * 10,
            n_epochs = nn_epochs * 2,
            latent_dim = nn_latent_dim,
            skip_diagrams = True,
            skip_images = True,
            skip_features = False,
            base = nn_base,
        ),
        Autoencoder(
            random_state = random_state,
            device = nn_device,
            batch_size = nn_batch_size,
            learning_rate = nn_learning_rate,
            n_epochs = nn_epochs,
            latent_dim = nn_latent_dim,
            skip_diagrams = True,
            skip_images = False,
            skip_features = True,
            base = nn_base,
        ),
        Autoencoder(
            random_state = random_state,
            device = nn_device,
            batch_size = nn_batch_size,
            learning_rate = nn_learning_rate,
            n_epochs = nn_epochs,
            latent_dim = nn_latent_dim,
            skip_diagrams = True,
            skip_images = False,
            skip_features = False,
            base = nn_base,
        ),
        Autoencoder(
            random_state = random_state,
            device = nn_device,
            batch_size = nn_batch_size,
            learning_rate = nn_learning_rate,
            n_epochs = nn_epochs // 2,
            latent_dim = nn_latent_dim,
            skip_diagrams = False,
            skip_images = True,
            skip_features = True,
            base = nn_base,
        )
    ]

    names = [
        'features',
        'images',
        'features_images',
        'diagrams'
    ]
    display_names = [
        'FC over topological features',
        'Baseline model',
        'Combined neural network',
        'Trainable vectorization'
    ]
    return pandas.DataFrame([ try_one(*args) for args in zip(models, names, display_names) ])
