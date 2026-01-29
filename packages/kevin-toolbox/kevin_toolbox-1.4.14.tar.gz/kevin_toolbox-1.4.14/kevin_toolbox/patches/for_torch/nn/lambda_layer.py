import torch
import torch.nn as nn


class Lambda_Layer(nn.Module):
    def __init__(self, func):
        super(Lambda_Layer, self).__init__()
        self.func = func

    def forward(self, x):
        return self.func(x)
