import torch

class Dataset:
    def __init__(self, images, features, masks):
        self.images = torch.tensor(images, dtype = torch.float32)
        if len(self.images.shape) == 4:
            if self.images.shape[-1] == 3:
                self.images = self.images.permute((0, 3, 1, 2))
        else:
            assert len(self.images.shape) == 3
            self.images = self.images.unsqueeze(1)

        self.masks = torch.tensor(masks, dtype = torch.float32).unsqueeze(1)
        self.features = torch.tensor(features, dtype = torch.float32)
