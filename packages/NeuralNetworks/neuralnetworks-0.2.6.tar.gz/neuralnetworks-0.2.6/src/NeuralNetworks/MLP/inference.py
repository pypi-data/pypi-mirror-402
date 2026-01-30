# NeuralNetworks - Multi-Layer Perceptrons avec encodage Fourier
# Copyright (C) 2026 Alexandre Brun
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.

from ..Dependances import torch, np, device

def infer (net, x):
    results_list = [net.model (encoding (x)) for encoding in net.encodings]
    return net.f (torch.cat (results_list, dim = 1))