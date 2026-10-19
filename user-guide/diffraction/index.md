---
title: Diffraction
---

# Diffraction

```{image} ../../assets/diffraction/schematic-acom-workflow-light.svg
:alt: Orientation and phase mapping workflow: a diffraction pattern at every probe position, Bragg disk detection, calibration against known rings, matching to simulated patterns of each phase, and the resulting phase and orientation maps
:class: qem-only-light
:width: 100%
```

```{image} ../../assets/diffraction/schematic-acom-workflow-dark.svg
:alt: Orientation and phase mapping workflow: a diffraction pattern at every probe position, Bragg disk detection, calibration against known rings, matching to simulated patterns of each phase, and the resulting phase and orientation maps
:class: qem-only-dark
:width: 100%
```

`quantem.diffraction` analyzes scanning nanobeam electron diffraction and 4D-STEM data, and simulates electron diffraction from crystal structures. Most of the analysis works on detected Bragg peaks rather than full diffraction images, which makes scans of tens of thousands of patterns fast to process.

## Orientation and phase mapping

Automated crystal orientation mapping (ACOM) finds the orientation and phase at every probe position by matching the measured Bragg disks to simulated patterns, in three steps:

1. **[Bragg disk detection](./disk-detection.md)**: find the disks in every pattern by template matching.
2. **[Calibration](./calibration.md)**: remove the descan, measure the scan rotation, and fit the pixel size and elliptic distortion to the rings or spots of known phases.
3. **[Orientation and phase mapping](./orientation-mapping.md)**: match each pattern to a simulated library, refine the orientations, decide the phase, and measure projected strain.

The examples use a two-phase titanium dataset from [MacLaren et al. (2024)](https://doi.org/10.1111/jmi.13275), shared by Ian MacLaren (University of Glasgow).

## Other capabilities

- [Strain mapping](./strain-mapping.md): strain and rotation maps from lattice fits to the detected disks, or from model fits to the patterns.
- [Diffraction simulation](./diffraction-simulation.md): kinematical patterns, and Bloch wave calculations of dynamical intensities, CBED, LACBED, and Kossel patterns.

:::{note}
Calibration, orientation and phase mapping, and the Bloch wave simulations are in [pull request #297](https://github.com/electronmicroscopy/quantem/pull/297) and are not yet part of a quantEM release.
:::

Runnable examples are in the [diffraction tutorials](https://github.com/electronmicroscopy/quantem-tutorials/tree/main/tutorials/diffraction).
