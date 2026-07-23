---
title: Data I/O & file formats
---

# Data I/O & file formats

## Reading experimental data

File readers live in `quantem.core.io` and are built on [RosettaSciIO](https://hyperspy.org/rosettasciio/supported_formats/index.html), which handles most vendor formats (Gatan DM3/DM4, EMD, MIB, TIFF, HDF5-based formats, and many more):

| Function | Returns | Use |
| --- | --- | --- |
| `read_2d(path)` | `Dataset2d` | Images and single diffraction patterns |
| `read_4dstem(path)` | `Dataset4dstem` | 4D-STEM scans; optional hot-pixel filtering |
| `read_emdfile_to_4dstem(path)` | `Dataset4dstem` | Legacy `emdFile` / py4DSTEM HDF5 files |

The file type is inferred from the extension, or can be forced with the `file_type` argument.

## Saving and loading quantEM objects

quantEM objects (datasets and reconstruction classes) serialize through `AutoSerialize` to Zarr-backed archives:

```python
from quantem.core import io

obj = io.load("result.zip")     # load any saved quantEM object
io.print_file("result.zip")     # inspect a file without loading it
```

## Calibrations

Readers propagate calibration metadata (pixel sizes, units, origins) from the source files into the returned `Dataset` objects, where available. Always check `dataset.sampling` and `dataset.units` after loading. Vendor metadata is not always reliable. Fix calibrations by assigning to those attributes.
