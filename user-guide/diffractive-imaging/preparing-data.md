---
title: Preparing 4D-STEM data
---

# Preparing 4D-STEM data

The calibrations established on this page determine whether any subsequent reconstruction can succeed. In our experience, the real-space sampling, the scan step, and the scan rotation are considerably more important than any reconstruction parameter, and an incorrect calibration is the most common reason that a reconstruction fails to converge.

## Select a device

```python
import quantem as em
from quantem.core import config

config.set_device(0)          # GPU index, or "cpu" / "mps"
print(config.get("device"))
```

## Record the microscope parameters

Declare the acquisition conditions explicitly at the top of the analysis, rather than relying on file metadata. Reconstruction settings then stay auditable.

```python
PROBE_ENERGY = 300e3      # eV
PROBE_SEMIANGLE = 25.0    # mrad
PROBE_DEFOCUS = -100.0    # Angstrom
SCAN_STEP_SIZE = 0.42     # Angstrom
```

Ptychography experiments typically fall into one of two regimes, which require substantially different acquisition settings:

| | Convergence angle | Defocus | Scan step |
| --- | --- | --- | --- |
| Atomic resolution materials | 20 to 30 mrad | tens to hundreds of Å | 0.2 to 0.5 Å |
| Low dose biological | 1 to 5 mrad | 1 to 15 µm | 10 to 30 Å |

## Load the data

`quantem.core.io` reads most vendor formats through RosettaSciIO:

```python
dset = em.io.read_4dstem("scan_master.h5", file_type="arina")
dset = em.io.read_4dstem("scan.xml", file_type="empad")
dset = em.io.load("scan.zip")                  # quantEM native
```

For an array you have already loaded, build the dataset directly. The array axes are (scan y, scan x, detector y, detector x):

```python
from quantem.core.datastructures import Dataset4dstem

dset = Dataset4dstem.from_array(
    data_array,
    name="my scan",
    sampling=(SCAN_STEP_SIZE, SCAN_STEP_SIZE, 1, 1),
    units=("A", "A", "pixels", "pixels"),
)
```

If gain correction has left negative counts, clip them with `data_array.clip(0)` before constructing the dataset. If the scan was acquired in a serpentine pattern, reverse every second row first, otherwise alternate rows will be spatially mirrored.

## Calibrate reciprocal space

Fit the bright-field disk in the mean diffraction pattern and convert its radius into the known convergence semi-angle:

```python
from quantem.core.utils.diffractive_imaging_utils import fit_probe_circle

dset.get_dp_mean()
probe_qy0, probe_qx0, probe_R = fit_probe_circle(dset.dp_mean.array, show=True)

dset.sampling[2] = PROBE_SEMIANGLE / probe_R
dset.sampling[3] = PROBE_SEMIANGLE / probe_R
dset.units[2:] = ["mrad", "mrad"]
```

We recommend always inspecting a single diffraction pattern alongside the mean pattern. Hot pixels, dead regions, and saturated pixels are typically visible in individual patterns, but are averaged away in the mean.

```python
em.visualization.show_2d(
    [dset[0, 0].array, dset.dp_mean.array],
    title=["single pattern", "mean pattern"],
)
```

For simulated data, where the sampling is already known exactly, we still run `fit_probe_circle` to obtain `probe_R` for the virtual detector geometry, but we leave the sampling unchanged.

## Check with virtual images

Virtual bright-field and dark-field images confirm that the scan was recorded correctly and that the disk fit is properly centered. These images are inexpensive to compute and are the most useful check available at this stage.

```python
dset.get_virtual_image(
    mode="circle",
    geometry=((probe_qy0, probe_qx0), probe_R * 1.1),
    name="BF", show=True,
)
dset.get_virtual_image(
    mode="annular",
    geometry=((probe_qy0, probe_qx0), (probe_R * 1.1, probe_R * 5)),
    name="DF", show=True,
)
dset.show_virtual_images(cmap="viridis")
```

At low dose, the contrast in these images will typically be weak. This is expected, and is precisely the situation where phase retrieval methods provide the most benefit.

## Clean up detector artifacts

```python
from quantem.core.utils.filter import filter_hot_pixels

dset.array = filter_hot_pixels(dset.array)
```

Compare the mean pattern before and after filtering. For electron-counted data in which some scan positions recorded zero counts, those positions can either be excluded during reconstruction using a `positions_mask`, or filled in from their neighbors.

## Crop and bin

Reducing the size of the dataset at this stage will accelerate every subsequent step. There are two behaviors worth noting.

First, slicing a dataset discards its stored virtual images, whereas `crop` retains them:

```python
small = dset.crop(((32, 480), (32, 480)), axes=(0, 1), modify_in_place=False)
small.regenerate_virtual_images()
```

Second, binning does not rescale the stored detector geometry, and so the virtual images should be regenerated afterwards using scaled coordinates:

```python
bin_k = 2
small = small.bin((1, 1, bin_k, bin_k))
small.get_virtual_image(
    mode="annular",
    geometry=((probe_qy0 / bin_k, probe_qx0 / bin_k),
              (probe_R / bin_k * 1.1, probe_R / bin_k * 5)),
    name="DF",
)
```

Binning reciprocal space by a factor of 2 is routine for detectors of 192 × 192 pixels and larger. The extent to which the data can be binned is limited by the probe, because the reciprocal pixel size determines the real-space extent of the probe array, and this array must be large enough to contain the probe without wraparound.

## Build the ptychography dataset

`PtychographyDatasetRaster` holds the scan geometry, fits the center of mass of every pattern, and determines the scan rotation.

```python
from quantem.diffractive_imaging import PtychographyDatasetRaster

pdset = PtychographyDatasetRaster.from_dataset4dstem(
    dset,
    learn_scan_positions=False,
    learn_descan=False,
)
pdset.preprocess(
    com_fit_function="constant",
    probe_energy=PROBE_ENERGY,
    plot_rotation=True,
    plot_com=True,
)
```

We use `com_fit_function="constant"` by default, and `"plane"` in cases where the descan drifts across the scan. If `force_com_rotation` is left unset, the rotation angle is fitted automatically and printed. Once the correct rotation is known, we recommend passing it explicitly so that subsequent runs are reproducible:

```python
pdset.preprocess(
    com_fit_function="constant",
    probe_energy=PROBE_ENERGY,
    force_com_rotation=94.0,      # degrees
    force_com_transpose=False,
)
```

:::{tip}
If the reconstructed phase is inverted, either add 180 degrees to the rotation angle or reverse the sign of the defocus. The rotation fit is determined only up to this ambiguity, which is conventionally resolved by requiring the phase of a known feature to be positive.
:::

Setting `learn_scan_positions=True` allows the probe positions to be refined during the reconstruction, which can correct for scan distortion and sample drift. Note that position refinement requires a corresponding entry in the optimizer parameters in order to take effect. We generally recommend enabling it only after the reconstruction is otherwise stable.

:::{seealso}
[Ptychography of a MOSS-6 metal-organic framework](https://github.com/electronmicroscopy/quantem-tutorials/blob/main/tutorials/diffractive_imaging/ptycho_iter_04_MOSS6.ipynb) in the tutorials repository carries out this full preparation sequence on raw experimental detector data, from file loading through to a preprocessed ptychography dataset.
:::
