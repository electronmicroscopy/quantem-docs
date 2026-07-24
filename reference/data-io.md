---
title: File I/O
---

# File I/O

quantEM reads two kinds of files: microscopy data from instrument vendors, and its own Zarr-backed format for saving analysis objects. Both live in `quantem.core.io`.

## Reading microscopy data

Instrument file reading is built on [RosettaSciIO](https://hyperspy.org/rosettasciio/), which supports most vendor formats: Gatan (DM3, DM4), Velox and Berkeley EMD, Quantum Detectors MIB, TIFF, MRC, SER, Blockfile, and many more. The [supported formats list](https://hyperspy.org/rosettasciio/supported_formats/index.html) is authoritative.

| Function | Returns | Use |
| --- | --- | --- |
| `read_2d(path)` | `Dataset2d` | Images and single diffraction patterns |
| `read_4dstem(path)` | `Dataset4dstem` | 4D-STEM scans |
| `read_emdfile_to_4dstem(path)` | `Dataset4dstem` | Legacy `emdFile` and py4DSTEM files |

```python
from quantem.core import io

image = io.read_2d("image.dm4")
scan = io.read_4dstem("scan.emd")
```

The reader is inferred from the file extension. Override it with `file_type` when the extension is ambiguous or missing:

```python
scan = io.read_4dstem("data.h5", file_type="emd")
```

`read_4dstem` takes two extra options worth knowing:

- `dataset_index`: pick one dataset when a file contains several
- `hot_pixel_filter=True`: remove hot detector pixels while reading

Remaining keyword arguments pass straight through to the RosettaSciIO reader.

### Calibrations

Readers propagate calibration metadata (pixel sizes, units, origins) into the returned `Dataset` where the file provides it. Always check after loading, since vendor metadata is not always reliable:

```python
print(scan.sampling, scan.units)

scan.sampling = (0.25, 0.25, 0.0021, 0.0021)
scan.units = ["A", "A", "A^-1", "A^-1"]
```

For a 4D-STEM scan the first two axes are real space, in Å here, and the last two are reciprocal space, in Å⁻¹.

## The quantEM file format

quantEM saves its own objects through `AutoSerialize`, which writes [Zarr](https://zarr.dev) hierarchies. Every class that inherits `AutoSerialize` (datasets, reconstructions, fitted models) saves and loads with no extra code, including nested objects and their metadata.

### Writing

```python
scan.save("scan.zip")
scan.save("scan_dir")
scan.save("scan.zip", mode="o")
```

A `.zip` path writes a single-file archive, and any other path writes a directory store. The full set of options:

- `mode`: `"w"` writes only when the target does not exist (default), `"o"` overwrites.
- `store`: `"auto"` (default) picks zip for a `.zip` path and a directory otherwise. Force it with `"zip"` or `"dir"`.
- `compression_level`: Zstandard level 0 to 9 via Blosc, default `4`. Use `0` for no compression, or `None` to disable the compressor entirely.
- `skip`: attribute names or types to leave out of the file. The skip list is stored in the file so `load` round-trips correctly.

A directory store is the better choice for very large objects and for partial reads. A zip archive is easier to copy and share.

### Reading

```python
from quantem.core import io

obj = io.load("scan.zip")
obj = io.load("scan.zip", skip="raw_data")
```

The `skip` argument leaves named attributes out at load time, which is useful for pulling a reconstruction back without its raw data. `load` reconstructs the original class, so a saved `Dataset4dstem` comes back as a `Dataset4dstem` and a saved reconstruction comes back ready to continue.

### Inspecting

Two tree printers help when you are not sure what is inside an object or a file.

```python
scan.print_tree()
io.print_file("scan.zip")
```

`print_tree` describes an object already in memory. `print_file` describes a file on disk without loading it, so it is the faster path for a large archive. Both accept the same display options:

- `depth`: limit how deep the tree prints
- `show_values`: print scalar values (on by default)
- `show_autoserialize_types`: include internal serialization keys and container types
- `show_class_origin`: print the full module path for each class

```python
io.print_file("reconstruction.zip", depth=2)
```
