---
title: Datasets & I/O
---

# Datasets & I/O

The `Dataset` classes in `quantem.core.datastructures` are the common currency of quantEM: file readers return them, analysis routines consume and produce them, and visualization functions know how to display them with correct physical units.

## The Dataset classes

| Class | Data | Typical use |
| --- | --- | --- |
| `Dataset` | N-dimensional array | Base class |
| `Dataset2d` | 2D array | Images, diffraction patterns |
| `Dataset3d` | 3D array | Image stacks, tilt series |
| `Dataset4d` | 4D array | Generic 4D data |
| `Dataset4dstem` | 4D array | 4D-STEM scans (probe positions × detector) |
| `Vector` | Ragged point data | Detected peaks, e.g. Bragg disk positions per probe position |

Each dataset stores its array together with calibration metadata:

- `sampling`: pixel size along each dimension
- `units`: units for each dimension (e.g. Å in real space, Å⁻¹ in reciprocal space)
- `origin`: coordinate origin along each dimension
- `name`, `signal_units`, `metadata`: descriptive metadata

The underlying data is accessible both as a NumPy array (`.array`) and as a torch tensor (`.tensor`), so datasets move cleanly between CPU-side plotting and GPU-side computation.

Constructing a dataset from an existing array:

```python
import numpy as np
from quantem.core.datastructures import Dataset2d

image = Dataset2d.from_array(
    np.random.rand(256, 256),
    sampling=(0.2, 0.2),
    units=("A", "A"),
    name="example image",
)
```

## Reading data from files

`quantem.core.io` provides file readers built on [RosettaSciIO](https://hyperspy.org/rosettasciio/supported_formats/index.html), which supports most vendor formats:

```python
from quantem.core import io

image = io.read_2d("image.dm4")
scan = io.read_4dstem("scan.h5")
legacy = io.read_emdfile_to_4dstem("data.emd")
```

`read_2d` handles images and single diffraction patterns, `read_4dstem` handles 4D-STEM scans, and `read_emdfile_to_4dstem` handles legacy `emdFile` and py4DSTEM files.

## Saving and loading quantEM objects

Datasets and analysis objects serialize to Zarr-backed files:

```python
from quantem.core import io

io.load("reconstruction.zip")
io.print_file("reconstruction.zip")
```

`load` reconstructs the saved object, and `print_file` prints its structure without loading it.

:::{note}
This page will be expanded from the `core/vector.ipynb` and `core/config.ipynb` tutorial notebooks.
:::
