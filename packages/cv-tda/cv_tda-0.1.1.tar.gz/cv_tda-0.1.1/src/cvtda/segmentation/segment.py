import typing

import numpy
import torch
import pandas

import cvtda.logging
import cvtda.dumping
import cvtda.neural_network

from .Dataset import Dataset
from .MiniUnet import MiniUnet
from .estimate_quality import estimate_quality

def segment(
    train_images: numpy.ndarray,
    train_features: numpy.ndarray,
    train_masks: numpy.ndarray,

    test_images: numpy.ndarray,
    test_features: numpy.ndarray,
    test_masks: numpy.ndarray,

    random_state: int = 42,
    dump_name: typing.Optional[str] = None,
    only_get_from_dump: bool = False,

    device: torch.device = cvtda.neural_network.default_device,
    batch_size: int = 64,
    learning_rate: float = 1e-3,
    n_epochs: int = 100,
    remove_cross_maps: bool = False
):
    nn_train = Dataset(train_images, train_features, train_masks)
    nn_test = Dataset(test_images, test_features, test_masks)

    def try_one(model: MiniUnet, name: str, display_name: str):
        cvtda.logging.logger().print(f'Trying {name} - {model}')
        
        dumper = cvtda.dumping.dumper()
        model_dump_name = cvtda.dumping.dump_name_concat(dump_name, name)
        if only_get_from_dump or dumper.has_dump(model_dump_name):
            y_pred_proba = dumper.get_dump(model_dump_name)
        else:
            model.fit(nn_train, nn_test)
            y_pred_proba = model.predict_proba(nn_test)

            if model_dump_name is not None:
                dumper.save_dump(y_pred_proba, model_dump_name)

        result = { 'model': display_name, **estimate_quality(y_pred_proba, test_masks) }
        cvtda.logging.logger().print(result)
        return result

    unet_kwargs = dict(
        random_state = random_state,
        device = device,
        batch_size = batch_size,
        learning_rate = learning_rate,
        n_epochs = n_epochs,
        remove_cross_maps = remove_cross_maps
    )
    models = [
        MiniUnet(**unet_kwargs, with_images = False, with_features = False),
        MiniUnet(**unet_kwargs, with_images = True, with_features = False),
        MiniUnet(**unet_kwargs, with_images = False, with_features = True),
        MiniUnet(**unet_kwargs, with_images = True, with_features = True)
    ]

    names = [
        'no',
        'images',
        'topological',
        'combined'
    ]
    display_names = [
        'No features',
        'Without topological features',
        'Only topological features',
        'Combined features'
    ]

    return pandas.DataFrame([ try_one(*args) for args in zip(models, names, display_names) ])
