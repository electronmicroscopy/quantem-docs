---
title: Diffractive imaging
---

# Diffractive imaging

Electrons pass through a thin specimen almost without absorption. What the specimen does is shift the phase of the electron wave, by an amount proportional to the projected electrostatic potential. Detectors record only intensity, so that phase is not measured directly. Recovering it is the phase retrieval problem, and `quantem.diffractive_imaging` solves it from 4D-STEM data.

A 4D-STEM scan gives you a full diffraction pattern at every probe position. That redundancy is what makes phase retrieval possible: neighboring probe positions illuminate overlapping regions of the sample, so the same piece of the object is encoded in many patterns under different illumination.

## Direct and iterative methods

quantEM implements two families of methods, and they trade speed against capability.

**Direct methods** reconstruct in a single pass. They assume the specimen is a weak phase object, meaning it shifts the phase only slightly, which makes the problem linear and lets a single filter solve it. Direct methods run in seconds, need no starting guess, and hold up well at low dose. Their resolution cannot exceed twice the probe convergence semi-angle.

**Iterative methods** build a model of the experiment and refine it by gradient descent until the simulated diffraction patterns match the measured ones. They need no weak phase assumption, they solve for the probe alongside the specimen, and they can resolve finer detail than direct methods allow. In exchange they take far more computation and have many more settings to get right.

| Method | Family | Best used when | Resolution limit |
| --- | --- | --- | --- |
| Center of mass (iCOM, DPC) | Direct | In focus, quick look during acquisition | Probe autocorrelation |
| Single sideband (SSB) | Direct | Aberrations known, weak phase object | 2 × semiangle |
| Optimum bright field (OBF) | Direct | Same as SSB, at low dose | 2 × semiangle |
| Matched filter (MF) | Direct | Same as SSB, least-squares optimal | 2 × semiangle |
| Parallax (tcBF) | Direct | Defocused data, fitting aberrations | 2 × semiangle |
| Iterative ptychography | Iterative | Highest resolution, thick or strongly scattering samples | Largest recorded scattering angle |

Single sideband, optimum bright field, and matched filter all recover the same amount of reliable information, so they differ in how they handle noise rather than in what they can resolve. Iterative ptychography is the only method whose resolution is set by the detector rather than by the aperture.

## The order to work in

Work through these stages in order. Each one produces calibrations that the next stage needs, so skipping ahead usually costs more time than it saves.

1. **Load and calibrate.** Set the real-space sampling from the scan step, then set reciprocal sampling by fitting the bright-field disk. Check virtual bright-field and dark-field images before going further. See [Preparing 4D-STEM data](./preparing-data.md).
2. **Run direct methods.** Compare all five kernels in one call, then fit the defocus, astigmatism, and scan rotation. This takes seconds and tells you whether the data is good. See [Direct ptychography](./direct-ptychography.md).
3. **Run a pixelated iterative reconstruction**, single slice, single probe, seeded with the aberrations from step 2. See [Iterative ptychography](./ptychography.md).
4. **Add model complexity only when the data demands it**: extra probe modes for partial coherence, extra slices for thick samples. See [Multislice and mixed-state](./multislice.md).
5. **Regularize**, either with explicit constraints on a pixelated object or with a deep generative prior. See [Regularization and deep priors](./regularization.md).
6. **Optimize hyperparameters** once the workflow is stable, on a cropped subset for speed. See [Hyperparameter optimization](./hyperparameters.md).
7. **Scale up** to the full field of view, multiple GPUs, or a cluster. See [Scaling up](./scaling.md).

If the direct methods in step 2 fail completely, an iterative reconstruction will almost certainly be unstable as well. That is a signal to fix the calibration, not to reach for a more powerful method.

## What the data has to provide

Three properties of the acquisition determine what any of these methods can recover.

**Probe overlap** is the most important one. Neighboring probe positions must illuminate substantially overlapping areas of the specimen, which you achieve either by scanning in fine steps or by defocusing to spread the probe out. Without enough overlap, nothing constrains the specimen between probe positions, and the reconstruction invents periodic structure on the scan grid.

**Dose** sets a hard floor on the finest detail that is recoverable, since detail below the noise level cannot be recovered by any algorithm. Note that insufficient dose and insufficient overlap are separate problems with separate fixes, and they produce different-looking failures: too little dose blurs fine features away, while too little overlap adds grid-aligned artifacts.

**Defocus** helps some methods and hurts others. Center-of-mass imaging transfers best exactly in focus. Parallax needs defocus and produces nothing without it. Iterative ptychography benefits from the extra overlap that defocus provides, but pays for it with a larger probe array and more computation.

## What the module provides

```python
from quantem.diffractive_imaging import (
    DirectPtychography,          # non-iterative reconstruction
    PtychographyDatasetRaster,   # scan geometry and preprocessing
    Ptychography,                # full iterative interface
    PtychoLite, PtychoLiteDIP,   # simplified iterative interface
    ObjectPixelated, ObjectDIP,  # object models
    ProbePixelated, ProbeDIP, ProbeParametric,
    DetectorPixelated,
)
```

Reconstructions are assembled from interchangeable models: an object, a probe, a detector, and a dataset that carries the scan geometry. Swapping a pixelated object for a neural-network object changes the regularization without touching the rest of the pipeline.

Complete worked examples live in the [diffractive imaging tutorials](https://github.com/electronmicroscopy/quantem-tutorials/tree/main/tutorials/diffractive_imaging).

:::{seealso}
The methods implemented here are described in [Varnavides et al. (2024)](https://arxiv.org/abs/2309.05250) for iterative phase retrieval, [Varnavides et al. (2026)](https://doi.org/10.1557/s43577-026-01100-3) for the direct methods, and [McCray et al. (2025)](https://arxiv.org/abs/2511.07795) for deep generative priors.
:::
