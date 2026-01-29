import typing

import numpy
import torch
import torch.utils.data
import torchph.nn.slayer

import cvtda.utils
import cvtda.logging

from .device import default_device


def transform(diagram: torch.Tensor, dim: int):
    dim_filter = (diagram[:, 2] == dim)
    non_degenerate_filter = (diagram[:, 0] < diagram[:, 1])
    rotation = torchph.nn.slayer.LogStretchedBirthLifeTimeCoordinateTransform(0.01)
    return rotation(diagram[dim_filter & non_degenerate_filter][:, 0:2])

def process_diagram(diags: torch.Tensor):
    diagrams, non_dummy_points = [], []
    for dim in diags[:, :, 2].unique(sorted = True):
        diags_dim = [ transform(diag, dim) for diag in diags ]
        processed = torchph.nn.slayer.prepare_batch(diags_dim)
        diagrams.append(processed[0].cpu())
        non_dummy_points.append(processed[1].cpu())
    return diagrams, non_dummy_points


class Dataset(torch.utils.data.Dataset):
    def __init__(
        self,
        images: numpy.ndarray,
        diagrams: typing.Optional[typing.List[numpy.ndarray]], # n_items x n_diagrams x n_points x 3
        features: numpy.ndarray,
        labels: typing.Optional[numpy.ndarray],

        n_jobs: int = -1,
        device: torch.device = default_device,
    ):
        self.n_jobs_ = n_jobs
        self.device_ = device

        if images is not None:
            self.images = torch.tensor(images, dtype = torch.float32)
            if len(self.images.shape) == 4:
                self.images = self.images.permute((0, 3, 1, 2))
            else:
                assert len(self.images.shape) == 3
                self.images = self.images.unsqueeze(1)
        
        if labels is not None:
            self.labels = torch.tensor(labels, dtype = torch.long)
        self.features = torch.tensor(features, dtype = torch.float32)
        self.raw_diagrams = diagrams
        
        if diagrams is None:
            return

        diagrams = [
            torch.tensor(numpy.array([ item[num_diagram] for item in diagrams ]), dtype = torch.float32)
            for num_diagram in range(len(diagrams[0]))
        ]
        pbar = cvtda.logging.logger().pbar(diagrams, desc = "Dataset: processing diagrams")
        diagrams = cvtda.utils.parallel(process_diagram, pbar, n_jobs = self.n_jobs_)

        self.diagrams, self.non_dummy_points = [], []
        for diag, ndp in diagrams:
            self.diagrams.extend(diag)
            self.non_dummy_points.extend(ndp)

        cvtda.logging.logger().print(
            f"Constructed a dataset of {len(self.images)} images of shape {self.images[0].shape} " +
            f"with {len(self.diagrams)} diagrams and {self.features.shape[1]} features"
        )

    def __len__(self):
        return len(self.images)

    def get_labels(self, idxs, device: typing.Optional[torch.device] = None):
        device = device if device is not None else self.device_
        return self.labels[idxs].to(device)
    
    def get_label(self, idx, device: typing.Optional[torch.device] = None):
        device = device if device is not None else self.device_
        return self.labels[idx].to(device)

    def get_diagrams(self, idxs, device: typing.Optional[torch.device] = None):
        device = device if device is not None else self.device_
        output = [ ]
        for diag, ndp in zip(self.diagrams, self.non_dummy_points):
            output.append(diag[idxs].to(device))
            output.append(ndp[idxs].to(device))
        return output

    def get_diagram(self, idx, device: typing.Optional[torch.device] = None):
        device = device if device is not None else self.device_
        output = [ ]
        for diag, ndp in zip(self.diagrams, self.non_dummy_points):
            output.append(diag[idx].to(device))
            output.append(ndp[idx].to(device))
        return output
