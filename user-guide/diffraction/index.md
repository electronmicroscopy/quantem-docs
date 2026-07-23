---
title: Diffraction
---

# Diffraction

`quantem.diffraction` covers analysis of diffraction-space data, primarily nanobeam and 4D-STEM measurements.

Current capabilities:

- [Bragg disk detection](./disk-detection.md): locate diffracted disks at each probe position, producing `Vector` datasets of peak positions and intensities.
- [Strain mapping](./strain-mapping.md): fit lattice vectors to detected disks (or fit a forward model directly to the patterns) and convert them to strain and rotation maps.

Runnable examples live in the [diffraction tutorials](https://github.com/electronmicroscopy/quantem-tutorials/tree/main/tutorials/diffraction).
