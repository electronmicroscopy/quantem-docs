---
title: Package structure
---

# Package structure

quantEM is organized as a core infrastructure package plus one subpackage per experimental modality.

```
quantem
├── core                  # shared infrastructure
│   ├── datastructures    #   Dataset, Dataset2d/3d/4d, Dataset4dstem, Vector
│   ├── io                #   file readers and (de)serialization
│   ├── visualization     #   show_2d, linescan, colormaps, scale bars
│   ├── config            #   global configuration (device, precision, viz defaults)
│   ├── fitting           #   fitting utilities
│   ├── ml                #   neural-network building blocks
│   └── utils             #   general helpers
├── imaging               # drift correction, lattice analysis
├── diffraction           # Bragg disks, model fitting, strain
├── diffractive_imaging   # iterative + direct ptychography
├── tomography            # tilt-series preprocessing + reconstruction
└── spectroscopy          # EDS and other spectra
```

## Import conventions

The top-level package re-exports the pieces most workflows need:

```python
import quantem

# core namespaces available directly:
quantem.io               # file readers, load/save
quantem.datastructures   # Dataset classes
quantem.visualization    # plotting helpers
```

Modality subpackages are imported explicitly, for example:

```python
from quantem.diffractive_imaging import ptychography
from quantem.core import config
```

## Datasets carry calibrations

All analysis operates on `Dataset` objects: thin wrappers around an array (NumPy or torch tensor) plus calibration metadata: `sampling`, `units`, `origin`, `name`, and `signal_units`. Dimension-specific subclasses (`Dataset2d`, `Dataset3d`, `Dataset4d`, `Dataset4dstem`) add modality-specific functionality, and `Vector` handles ragged point-like data such as detected Bragg peaks. See [Datasets & I/O](../user-guide/datasets.md).

## Relationship to the tutorials

The [quantem-tutorials](https://github.com/electronmicroscopy/quantem-tutorials) repository contains runnable Jupyter notebooks organized by the same modality names as the subpackages. The User Guide pages in this documentation are condensed versions of those notebooks; when you want a complete, executable walkthrough with data, use the tutorials.
