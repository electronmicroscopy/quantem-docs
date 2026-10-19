---
title: Overview
---

# Overview

```{image} ../assets/architecture-light.svg
:alt: Structure of quantEM: open source foundations, the core engine, the shared physics layer, five stripes with their modules, and combined modules spanning several stripes. Dashed modules are in development.
:class: qem-only-light
:width: 100%
```

```{image} ../assets/architecture-dark.svg
:alt: Structure of quantEM: open source foundations, the core engine, the shared physics layer, five stripes with their modules, and combined modules spanning several stripes. Dashed modules are in development.
:class: qem-only-dark
:width: 100%
```

quantEM (`quantem` on PyPI) is an open source Python package for quantitative electron microscopy. It is organized in layers, from the most general to the most specialized:

- **Open source foundations.** PyTorch tensors for computation on CPUs and GPUs, and Zarr for storage, with NumPy, SciPy, Matplotlib, and anywidget.
- **Core engine.** Every module inherits automatic differentiation of forward models and automatic serialization of analysis objects. The two core data structures are `Dataset`, an N-dimensional array with calibrated axes, and `Vector`, ragged data on a fixed grid such as the Bragg peaks at each probe position.
- **Shared physics.** Crystallography, scattering potentials, electron optics, and calibration, used by more than one stripe.
- **Stripes.** Imaging, diffraction, tomography, spectroscopy, and simulation, each containing modules for specific analyses.
- **Combined modules.** Methods that span several stripes, built from the modules they combine. Ptychography, for example, records diffraction patterns and recovers an image.

Modules drawn with dashed outlines are in development.

## Design goals

- **One differentiable backend.** All numerical code uses PyTorch tensors, so every module runs on CPUs, CUDA GPUs, and Apple silicon GPUs, and any forward model can be optimized by gradient descent. See [GPU configuration](../reference/gpu.md).
- **Calibrations travel with the data.** Datasets store the origin, sampling, and units of each axis, and cropping, binning, and resampling update them.
- **Save everything.** Any quantEM object, including a reconstruction with its neural networks and optimizer states, can be saved to one file and resumed on another machine. See [File I/O](../reference/data-io.md).
- **Interchangeable representations.** Objects and probes can be pixel grids, deep image priors, implicit neural representations, or tensor decompositions behind the same interface.
- **Augment rather than replace.** quantEM reads vendor formats through RosettaSciIO, py4DSTEM files, and abTEM simulations, and is intended to be used alongside these packages.
- **Open.** The MIT license allows academic groups and instrument vendors to use, modify, and redistribute the code.

## What's in the box

| Subpackage | Scope |
| --- | --- |
| `quantem.core` | Datasets, `Vector`, file I/O, serialization, visualization, configuration, optimization, and neural networks |
| `quantem.imaging` | Drift correction and lattice analysis |
| `quantem.diffraction` | Bragg disk detection, calibration, orientation and phase mapping, strain mapping, and diffraction simulation |
| `quantem.diffractive_imaging` | Direct and iterative ptychography |
| `quantem.tomography` | Tilt series alignment and 3D reconstruction, including neural representations |
| `quantem.spectroscopy` | XEDS and EELS |

## Where to go next

- [Installation](./installation.md): install the released package or a development version.
- [Package structure](./package-structure.md): the subpackages and the import conventions used throughout these docs.
- The [User Guide](../user-guide/datasets.md): task-oriented guides for each modality, distilled from the [tutorial notebooks](https://github.com/electronmicroscopy/quantem-tutorials).
