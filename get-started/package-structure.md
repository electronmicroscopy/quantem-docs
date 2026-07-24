---
title: Package structure
---

# Package structure

quantEM is organized as a core infrastructure package plus one subpackage per experimental modality. Core holds everything shared: data structures, file I/O, visualization, configuration, fitting, and machine learning building blocks. Each modality subpackage then holds the analysis specific to one kind of measurement.

```
quantem
├── core
│   ├── datastructures
│   ├── io
│   ├── visualization
│   ├── config
│   ├── fitting
│   ├── ml
│   └── utils
├── imaging
├── diffraction
├── diffractive_imaging
├── tomography
└── spectroscopy
```

Inside `core`: `datastructures` holds the `Dataset` classes and `Vector`; `io` holds the file readers and Zarr serialization; `visualization` holds `show_2d`, `linescan`, colormaps, and scale bars; `config` holds the global settings for device, precision, and plotting defaults; `fitting` holds least-squares fitting, backgrounds, and diffraction models; `ml` holds CNNs, autoencoders, implicit neural representations, loss functions, and distributed training; `utils` holds array helpers, filters, validators, and random number generation.

The modality subpackages cover, in order: real-space images, diffraction-space measurements, phase retrieval, tilt series, and spectra.

## What each modality covers

**`quantem.imaging`** works on real-space S/TEM images and image series.

- `drift`: measure and correct scan drift and distortion across an image series
- `lattice`: fit atomic lattices and map local lattice distortions

**`quantem.diffraction`** works on diffraction patterns, mainly nanobeam and 4D-STEM.

- `disk_detection`, `bragg_vectors`: locate Bragg disks at each probe position and store them as ragged `Vector` data
- `strain`, `strain_autocorrelation`: convert fitted lattice vectors into strain and rotation maps
- `model_fitting`: fit a forward model directly to the diffraction patterns, as an alternative to disk detection

**`quantem.diffractive_imaging`** recovers phase from 4D-STEM data.

- `ptychography`, `ptychography_lite`: iterative gradient-based reconstruction, from quick previews to multi-GPU runs
- `direct_ptychography`: non-iterative reconstruction
- interchangeable model components: `object_models`, `probe_models`, `detector_models`, `dataset_models`, `origin_models`
- `constraints`, `optimize_hyperparameters`: regularization and Optuna-driven hyperparameter search

**`quantem.tomography`** reconstructs 3D volumes from tilt series.

- `tomography`, `tomography_lite`: reconstruction, including implicit neural representations
- `preprocess`: alignment and preprocessing of the tilt series
- `radon`: forward and adjoint projection operators

**`quantem.spectroscopy`** analyzes spectroscopic signals, principally energy-dispersive X-ray spectroscopy (XEDS) and electron energy loss spectroscopy (EELS).

:::{note}
The spectroscopy subpackage is under active development. The XEDS workflow is being built out first; see the [spectroscopy guide](../user-guide/spectroscopy/index.md).
:::

## Import conventions

The top-level package re-exports the pieces most workflows need:

```python
import quantem

quantem.io
quantem.datastructures
quantem.visualization
```

These give the file readers and `load`/`save`, the `Dataset` classes, and the plotting helpers.

Modality subpackages are imported explicitly, for example:

```python
from quantem.diffractive_imaging import ptychography
from quantem.core import config
```

## Datasets carry calibrations

All analysis operates on `Dataset` objects: thin wrappers around an array (NumPy or torch tensor) plus calibration metadata such as `sampling`, `units`, `origin`, `name`, and `signal_units`. Dimension-specific subclasses (`Dataset2d`, `Dataset3d`, `Dataset4d`, `Dataset4dstem`) add modality-specific functionality, and `Vector` handles ragged point-like data such as detected Bragg peaks. See [Datasets & I/O](../user-guide/datasets.md).

## Relationship to the tutorials

The [quantem-tutorials](https://github.com/electronmicroscopy/quantem-tutorials) repository contains runnable Jupyter notebooks organized by the same modality names as the subpackages. The User Guide pages in this documentation are condensed versions of those notebooks. For a complete, executable walkthrough with data, use the tutorials.
