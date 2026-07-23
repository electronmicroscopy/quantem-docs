---
title: Visualization
---

# Visualization

`quantem.core.visualization` provides plotting utilities designed for calibrated microscopy data: images with scale bars, perceptually-sensible normalizations, complex-valued displays, and line scans.

The main entry point is `show_2d`:

```python
from quantem.core.visualization import show_2d

show_2d(image)  # accepts Dataset2d objects or plain arrays
```

Other public utilities:

- `linescan`: extract and plot intensity profiles along a line
- `CustomNormalization`, `NormalizationConfig`: flexible intensity normalizations (e.g. power, log)
- `ScalebarConfig`: scale-bar styling
- `turbo_black`: a version of the turbo colormap that starts at black
- `axes_with_inset`: figure layout helper for images with inset panels

Default colormaps, units, and the categorical color cycle are set in the global configuration under the `viz` group. See [Configuration](../reference/configuration.md).

:::{note}
This page will be expanded from the `core/show.ipynb` tutorial notebook.
:::
