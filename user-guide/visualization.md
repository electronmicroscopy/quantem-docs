---
title: Visualization
---

# Visualization

quantEM has two complementary ways to look at data. `quantem.core.visualization` makes static Matplotlib figures, suitable for papers and for scripts. `quantem.widget` provides interactive Jupyter viewers for exploring data, including 4D-STEM datasets too large to plot directly.

## Static figures

### Images

`show_2d` displays one or more 2D arrays in a grid. It accepts plain arrays, `Dataset2d` objects, and complex arrays, which it renders with amplitude as brightness and phase as hue.

```python
from quantem.core.visualization import show_2d

show_2d(image)
show_2d([image_a, image_b], title=["before", "after"])
show_2d([[a, b], [c, d]])
```

A flat sequence lays the panels out in a row, and a nested sequence lays them out as a grid.

`norm`, `scalebar`, `cmap`, `cbar`, and `title` accept either a single value applied to every panel, or a nested sequence matched to the panel grid.

```python
show_2d(
    image,
    norm="log_auto",
    scalebar={"sampling": 0.12, "units": "A"},
    cmap="turbo",
    axsize=(5, 5),
    save="figure.png",
)
```

Normalization presets cover the common cases. `"linear_auto"` clips to quantiles, `"log_auto"` suits diffraction data spanning orders of magnitude, and `"power_sqrt"` sits between them. A dict such as `{"power": 0.5}` sets an explicit exponent, and a `NormalizationConfig` object gives full control.

### Other static helpers

- `linescan`: extract and plot an intensity profile along a line
- `CustomNormalization`, `NormalizationConfig`: intensity normalization, including power and log scaling
- `ScalebarConfig`: scale bar placement and styling
- `turbo_black`: the turbo colormap modified to start at black, useful for diffraction
- `axes_with_inset`: figure layout for an image with an inset panel
- `ShowParams`: reusable bundle of display settings

Default colormaps, units, and the categorical color cycle come from the global configuration under the `viz` group. See [Configuration](../reference/configuration.md).

## Interactive widgets

The viewers are an optional dependency:

```bash
pip install "quantem[widgets]"
```

They render in Jupyter through [anywidget](https://anywidget.dev), which means they work in JupyterLab, Notebook, and VS Code.

### Show2D

`Show2D` displays a single image or a gallery, with optional FFT and histogram panels, interactive line profiles, and regions of interest.

```python
from quantem.widget import Show2D

Show2D(image, sampling=0.12, units="A", show_fft=True)
```

Pass a 3D array of shape `(N, height, width)` to get a gallery, and use `labels` and `ncols` to arrange it. Setting both `vmin` and `vmax` puts every panel on one intensity scale, which is what you want for A/B comparisons.

```python
Show2D(
    stack,
    labels=["0 mrad", "5 mrad", "10 mrad"],
    ncols=3,
    vmin=0.0,
    vmax=1.0,
    cmap="inferno",
    size=300,
)
```

`size` is the on-screen width of each panel in CSS pixels. It changes display only, and never resamples the underlying image.

Useful methods: `add_roi`, `set_profile`, `rotate`, `save_image` for a PNG, and `save` for the widget state.

### Show4DSTEM

`Show4DSTEM` is an interactive 4D-STEM browser. Move the probe position to update the diffraction pattern, and place virtual detectors to build virtual images. It reduces data in chunks on whatever device is configured, so transient memory stays bounded regardless of dataset size.

```python
from quantem.widget import Show4DSTEM

Show4DSTEM(dataset)
```

Given a `Dataset4dstem`, the widget reads the calibration and units automatically.

It also takes raw arrays, NumPy or torch, with calibration supplied explicitly:

```python
Show4DSTEM(
    array,
    sampling=(2.39, 2.39, 0.46, 0.46),
    units=["A", "A", "mrad", "mrad"],
    center=(64, 64),
    bf_radius=12,
)
```

The array axes are `(scan_row, scan_col, detector_row, detector_col)`. Passing `center` and `bf_radius` overrides the automatic bright-field disk estimate.

Flattened scans work by passing `scan_shape=(64, 64)`. A 5D array is treated as a series, labeled with `frame_dim_label="Tilt"` or `"Time"`.

For large datasets, bin in reciprocal space before viewing:

```python
Show4DSTEM(dataset.bin(2, axes=(2, 3)))
```

BF, ABF, LAADF, and HAADF virtual images are precomputed by default so preset switching is instant. Set `precompute_virtual_images=False` to save memory.

:::{note}
🚧 This page will gain embedded, interactive examples exported from the widgets, plus coverage of the 3D viewer as it lands. Runnable versions live in the [core tutorials](https://github.com/electronmicroscopy/quantem-tutorials/tree/main/tutorials/core).
:::
