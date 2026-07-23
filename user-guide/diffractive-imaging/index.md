---
title: Diffractive imaging
---

# Diffractive imaging

`quantem.diffractive_imaging` implements phase retrieval from 4D-STEM data:

- [Ptychography](./ptychography.md): iterative gradient-based reconstruction, from a fast "lite" preview mode through full-featured reconstructions with mixed-state probes, multislice objects, constraints, and multi-GPU support.
- [Direct ptychography](./direct-ptychography.md): non-iterative (direct) reconstruction methods.

The iterative pipeline includes hyperparameter optimization (via [Optuna](https://optuna.org)) and HPC batch scripts for large reconstructions. The [diffractive imaging tutorials](https://github.com/electronmicroscopy/quantem-tutorials/tree/main/tutorials/diffractive_imaging) include complete worked examples on simulated and experimental datasets.
