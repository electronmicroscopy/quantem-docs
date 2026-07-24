---
title: GPU configuration
---

# GPU configuration

quantEM computes with PyTorch, so any device torch supports works: CPU, NVIDIA GPUs (CUDA), and Apple silicon (MPS). The default device is `cpu`.

## Selecting a device

```python
from quantem.core import config

config.set_device("gpu")
config.set_device("cuda:1")
config.set_device("mps")
config.set_device("cpu")
config.set_device(0)

config.get_device()
```

`"gpu"` selects the first CUDA device when one is available and falls back to MPS on Apple silicon. An integer is treated as a CUDA index, so `0` means `cuda:0`. `get_device` returns the current device as a string.

`set_device` accepts torch-style strings, integer indices, or `torch.device` objects, and validates that the requested device actually exists. Requesting `"gpu"` on a machine with neither CUDA nor MPS raises an error instead of falling back silently.

For temporary device changes, use the configuration context manager:

```python
with config.set({"device": "cuda:1"}):
    ...
```

To make a device the default across sessions, set it and write the config file. See [Configuration](./configuration.md).

## Precision

Numerical precision is controlled by the `precision` configuration key (`float32` by default, `float64` optional). Note that `float64` is slow on most consumer GPUs and unsupported on MPS.

## Multi-GPU

The iterative ptychography pipeline supports multi-GPU reconstructions; see the [ptychography guide](../user-guide/diffractive-imaging/ptychography.md) and the HPC scripts in the [tutorials repository](https://github.com/electronmicroscopy/quantem-tutorials/tree/main/tutorials/diffractive_imaging/hpc).
