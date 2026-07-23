---
title: Installation
---

# Installation

quantEM requires **Python 3.11 or newer**.

## Install from PyPI

The released package is available on PyPI as [`quantem`](https://pypi.org/project/quantem/):

```bash
pip install quantem
```

To include the optional interactive Jupyter widgets:

```bash
pip install "quantem[widgets]"
```

## GPU support

quantEM uses PyTorch for computation. The default `pip install` pulls in a `torch` build appropriate for your platform:

- **Linux with NVIDIA GPUs**: the default PyPI wheels include CUDA support. If you need a specific CUDA version, follow the [PyTorch installation selector](https://pytorch.org/get-started/locally/) before installing quantEM.
- **Apple silicon (macOS)**: the default wheels support the MPS backend; no extra steps are needed.
- **CPU only**: everything works on CPU; it is simply slower for the larger reconstructions.

Device selection is described in [GPU configuration](../reference/gpu.md).

## Development install

Development uses [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/electronmicroscopy/quantem.git
cd quantem
uv sync
```

`uv sync --all-packages` also installs the `quantem.widget` workspace package. Full developer setup (pre-commit, ruff, dependency management) is described in [Contribute](../project/contribute.md) and in [CONTRIBUTORS.md](https://github.com/electronmicroscopy/quantem/blob/main/CONTRIBUTORS.md).

## Verify the installation

```python
import quantem
print(quantem.__version__)
```
