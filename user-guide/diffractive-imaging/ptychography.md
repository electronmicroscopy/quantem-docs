---
title: Iterative ptychography
---

# Iterative ptychography

Iterative ptychography works by simulating the experiment and adjusting the simulation until it matches what you measured. Each cycle does the same three things. For every probe position, multiply the current guess of the probe by the current guess of the specimen, propagate the result to the detector, and compare the simulated intensity against the recorded pattern. The difference between the two is then used to correct both guesses, and the cycle repeats.

Solving for the probe at the same time as the specimen is what makes this powerful. No weak phase assumption is needed, and lens aberrations are removed rather than merely tolerated, because they end up described by the recovered probe. The resolution limit becomes the largest scattering angle you recorded rather than the convergence angle, which is why ptychography routinely resolves finer detail than any direct method can.

## The quick path: PtychoLite

`PtychoLite` assembles a standard reconstruction from a single call, choosing the object, probe, and detector models for you. Use it for first passes and for hyperparameter searches.

```python
from quantem.diffractive_imaging import PtychoLite

ptycho = PtychoLite.from_dataset(
    dset=pdset,
    obj_type="pure_phase",
    num_slices=1,
    num_probes=1,
    energy=PROBE_ENERGY,
    defocus=PROBE_DEFOCUS,
    semiangle_cutoff=PROBE_SEMIANGLE,
    obj_padding_px=(32, 32),
    device="gpu",
)

ptycho.reconstruct(
    num_iters=50,
    reset=True,
    lr_obj=5e-2,
    lr_probe=5e-2,
    batch_size=125,
    scheduler_type="plateau",
).visualize()
```

The `reconstruct` method returns the reconstruction object, so calls can be chained. Calling it a second time continues from the current state, since `reset` defaults to `False`:

```python
ptycho.reconstruct(num_iters=200).visualize()
ptycho.show_obj(axsize=(8, 8), cmap="turbo")
```

We recommend running a short reconstruction first, inspecting the result, and then extending it. Approximately ten iterations are usually sufficient to determine whether the calibration is correct.

## The full interface: building the models yourself

A reconstruction is made of four parts: an object model for the specimen, a probe model for the illumination, a detector model, and a dataset holding the scan geometry. `PtychoLite` builds all four for you. The full interface has you construct them separately, which is what you need in order to configure anything `PtychoLite` does not expose, or to swap in a different representation of the object or probe.

```python
from quantem.diffractive_imaging import (
    Ptychography, ObjectPixelated, ProbePixelated, DetectorPixelated,
)
from quantem.core.ml import OptimizerParams, SchedulerParams

obj_model = ObjectPixelated.from_uniform(
    obj_type="pure_phase",
    num_slices=1,
)
probe_model = ProbePixelated.from_params(
    probe_params={
        "energy": PROBE_ENERGY,
        "defocus": PROBE_DEFOCUS,
        "semiangle_cutoff": PROBE_SEMIANGLE,
    },
    num_probes=1,
)

ptycho = Ptychography.from_models(
    dset=pdset,
    obj_model=obj_model,
    probe_model=probe_model,
    detector_model=DetectorPixelated(),
    rng=42,
)
ptycho.preprocess(obj_padding_px=(32, 32))

ptycho.reconstruct(
    num_iters=50,
    reset=True,
    optimizer_params={
        "object": OptimizerParams.Adam(lr=5e-2),
        "probe":  OptimizerParams.Adam(lr=5e-2),
    },
    scheduler_params={
        "object": SchedulerParams.Plateau(),
        "probe":  SchedulerParams.Plateau(factor=0.1),
    },
    batch_size=125,
    device="gpu",
).visualize()
```

### Choosing an object type

| `obj_type` | Stores | Use for |
| --- | --- | --- |
| `"complex"` | Complex transmission function | General case, when amplitude contrast is real |
| `"pure_phase"` | Phase only, amplitude fixed at 1 | Weak phase objects, biological samples, most thin specimens |
| `"potential"` | Real projected potential | Atomic resolution multislice, where positivity is physically meaningful |

Restricting the object to pure phase halves the number of unknowns, which usually makes the reconstruction more stable. Choose `"complex"` only when you have a specific reason to expect amplitude contrast.

### How much to pad the object

The object array has to be larger than the scanned area, so that the probe still has room around the edges and does not wrap around to the opposite side during propagation. `obj_padding_px=(32, 32)` suits most reconstructions. Increase it to 64 or 128 pixels for large probes, strong defocus, or thick multislice objects, since all three make the probe wider.

### Optimizers and learning rates

Optimizer and scheduler settings are the most important parameters you control. Both are given as dicts keyed by which part of the model they apply to: `"object"`, `"probe"`, and `"dataset"` for refining scan positions. Setting a part's optimizer to `"none"` freezes it, which is how you hold the probe fixed.

Good learning rates depend on the object type and on how accurately you know the probe. Reasonable starting points:

| Situation | Object lr | Probe lr |
| --- | --- | --- |
| Pixelated, well-calibrated probe | 1e-3 | 1e-3 |
| Pixelated, poorly known probe | 1e-4 | 1e-2 |
| Deep prior object (see [regularization](./regularization.md)) | 1e-4 | 1e-4 |

Raise the probe learning rate above the object's when the probe has a long way to travel from its initial guess. Use a plateau scheduler in almost every case, since it lowers the learning rate automatically whenever the loss stops improving and saves you from designing a decay schedule by hand.

### How to choose a batch size

The batch size determines how many probe positions contribute to each update. Larger batches produce more accurate updates, while smaller batches update the probe more frequently and therefore converge the probe faster, which is most relevant for mixed-state reconstructions. We use 128 as a starting point. If GPU memory is exceeded, we recommend reducing the batch size before adjusting any other parameter.

### Which loss function to use

`loss_type` controls what "matching the data" means. The default, `"l2_amplitude"`, suits nearly everything. Use `"poisson"` for shot-noise-limited counting data, where it is the statistically correct choice. The intensity variants `"l2_intensity"` and `"l1_intensity"` give bright detector pixels more influence than dim ones.

## Checking that a reconstruction is healthy

```python
ptycho.visualize()                                  # object, probe, and loss curve
ptycho.show_obj(axsize=(8, 8), cmap="turbo")
ptycho.show_probe()
ptycho.show_fourier_probe()
ptycho.show_obj_fft(pad=512)                        # spatial frequency transfer
ptycho.plot_losses()
```

Store intermediate states to inspect the trajectory:

```python
ptycho.reconstruct(num_iters=30, store_snapshots_every=1)
ptycho.show_iters(every_nth=5, show_probe=False)
snap = ptycho.get_snapshot_by_iter(20)
```

A reconstruction that is converging well shows three characteristics. The loss decreases steadily. The probe remains smooth and compact, with its intensity contained within the aperture. The object gains fine detail without developing periodic structure aligned to the scan grid. If any of these conditions is not met, see [Troubleshooting](./troubleshooting.md).

Running additional iterations is not always beneficial, since beyond a certain point the reconstruction begins to fit noise. To identify this point, we hold back a fraction of the probe positions and monitor how well the model predicts them:

```python
ptycho.preprocess(obj_padding_px=(32, 32), val_ratio=0.05, val_mode="random")
```

Stop at the iteration where this validation loss stops falling, even though the training loss keeps falling. That gap is the signature of overfitting.

## Saving and resuming

```python
ptycho.save("recon.zip", mode="o")
ptycho = PtychoLite.from_file("recon.zip", dset=pdset, device="gpu")
```

The saved file does not contain the diffraction patterns by default. Instead it records where the data came from and how it was preprocessed, and reloads it on demand. Pass `save_raw_data=True` to embed the patterns and produce a self-contained file, which is what you want before copying a preprocessed dataset to a cluster.

:::{seealso}
Worked examples in the tutorials repository:

- [Lite reconstructions](https://github.com/electronmicroscopy/quantem-tutorials/blob/main/tutorials/diffractive_imaging/ptycho_iter_01_lite.ipynb): the shortest end-to-end reconstruction, using `PtychoLite`.
- [Full reconstructions](https://github.com/electronmicroscopy/quantem-tutorials/blob/main/tutorials/diffractive_imaging/ptycho_iter_02_full.ipynb): the modular interface, with alternative object representations.
- [MOSS-6 metal-organic framework](https://github.com/electronmicroscopy/quantem-tutorials/blob/main/tutorials/diffractive_imaging/ptycho_iter_04_MOSS6.ipynb): a complete low dose experimental workflow from raw detector data.
:::
