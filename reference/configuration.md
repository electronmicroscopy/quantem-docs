---
title: Configuration
---

# Configuration

quantEM has a global configuration system (`quantem.core.config`, modeled on Dask's config) controlling the compute device, numerical precision, and visualization defaults.

## Reading and setting values

```python
from quantem.core import config

config.get("device")            # read a value
config.get("viz.cmap")          # nested keys use dotted access

config.set({"precision": "float64"})   # set globally
```

`config.set` also works as a context manager for temporary overrides:

```python
with config.set({"device": "cuda:1"}):
    ...  # code here runs on cuda:1
# previous value is restored on exit
```

## Persistent configuration

The active configuration can be written to a YAML file that is loaded on import:

```python
config.write()   # writes ~/.config/quantem/config.yaml
```

The configuration directory can be relocated with the `QUANTEM_CONFIG` environment variable.

## Main keys

| Key | Default | Meaning |
| --- | --- | --- |
| `device` | `cpu` | Compute device (see [GPU configuration](./gpu.md)) |
| `precision` | `float32` | Float precision (`float32` or `float64`) |
| `dtype_real` / `dtype_complex` | `float32` / `complex64` | Real and complex dtypes |
| `verbose` | `1` | Global verbosity |
| `viz.cmap` | `gray` | Default image colormap |
| `viz.phase_cmap` | `magma` | Default colormap for phase images |
| `viz.real_space_units` | `A` | Default real-space units |
| `viz.reciprocal_space_units` | `A^-1` | Default reciprocal-space units |
| `viz.colors.set` / `viz.colors.paired` | (lists) | Categorical color cycles for plots |
| `mkl.threads` | `2` | MKL thread count |
| `cupy.fft-cache-size` | `0 MB` | CuPy FFT plan cache size |
