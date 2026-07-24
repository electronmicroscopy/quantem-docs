---
title: Overview
---

# Overview

quantEM (`quantem` on PyPI) is a Python toolkit for quantitative analysis of transmission electron microscopy data. It provides calibrated data structures, file readers, visualization utilities, and analysis pipelines for the main modalities of modern (scanning) transmission electron microscopy.

## Design goals

- **Quantitative**: data structures carry physical calibrations (sampling, units, origin) through every analysis step, so results come out in physical units.
- **One compute backend**: analysis code is built on [PyTorch](https://pytorch.org), so the same code runs on CPU, CUDA GPUs, and Apple-silicon (MPS) devices. See [GPU configuration](../reference/gpu.md).
- **Modular**: each experimental modality lives in its own subpackage, sharing common infrastructure from `quantem.core`.
- **Open**: MIT-licensed, developed as open source, ready for academics and vendors to use.
- **Tutorials Available**, many worked examples in the [tutorials repository](https://github.com/electronmicroscopy/quantem-tutorials).

## What's in the box

| Subpackage | Scope |
| --- | --- |
| `quantem.core` | Datasets, file I/O, visualization, configuration, fitting, and ML utilities shared by all modalities |
| `quantem.imaging` | Real-space imaging: drift correction, lattice analysis |
| `quantem.diffraction` | 4D-STEM diffraction: Bragg disk detection, model fitting, strain mapping |
| `quantem.diffractive_imaging` | Phase retrieval: iterative and direct ptychography |
| `quantem.tomography` | Tilt-series preprocessing and 3D reconstruction |
| `quantem.spectroscopy` | Spectroscopic signals (EDS) |

## Where to go next

- [Installation](./installation.md): install the released package or a development version.
- [Package structure](./package-structure.md): how the modules fit together and the import conventions used throughout these docs.
- The [User Guide](../user-guide/datasets.md): task-oriented guides for each modality, distilled from the tutorial notebooks.
