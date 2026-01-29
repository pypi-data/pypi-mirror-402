import torch


if torch.cuda.is_available():
    default_device = torch.device('cuda')
elif torch.mps.is_available():
    default_device = torch.device('mps')
else:
    default_device = torch.device('cpu')
