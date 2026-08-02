---
title: Troubleshooting
---

# Troubleshooting

Most failed reconstructions are calibration problems wearing a disguise. Work through the cheap checks before changing reconstruction parameters.

## The phase is inverted

Features that should be bright are dark, or the whole reconstruction looks like a photographic negative.

The scan rotation fit is only determined up to 180 degrees, and the sign of the defocus is entangled with it. Add 180 degrees to the rotation, or flip the sign of the defocus, and rerun:

```python
pdset.preprocess(..., force_com_rotation=fitted_angle + 180)
```

## Nothing converges at all

Check, in this order:

1. **Reciprocal sampling.** Refit the bright-field disk. A 10% error here is common and is enough to prevent convergence.
2. **Scan step.** Confirm it against the microscope, not the file metadata.
3. **Rotation.** Look at the plot from `preprocess`. If the center-of-mass field does not look like the gradient of a sensible potential, the rotation is wrong.
4. **Direct methods.** If none of the five kernels produces a recognizable image, the problem is in the data or calibration, not the reconstruction. Iterative methods will not rescue it.

## Periodic artifacts on the scan grid

A regular pattern with the periodicity of the scan step usually means insufficient probe overlap. The measurements do not constrain the object between probe positions, so the reconstruction invents structure there.

Fixes, in order of preference: acquire with a finer scan step, acquire with more defocus to spread the probe, or add a low-intensity extra probe mode to absorb the artifact. Enabling scan position refinement can also help when the cause is scan distortion rather than genuine undersampling.

## Atomic columns look like rings

Doughnut-shaped columns mean the phase has wrapped past 2π, which means the specimen is too thick for a single slice. Switch to a [multislice reconstruction](./multislice.md).

## The probe develops structure outside the aperture

Intensity beyond the aperture edge, or an aberration surface that is not smooth, indicates object features leaking into the probe. The two are being solved blindly and the split between them is not unique.

Constrain the probe. Fixing its Fourier amplitude to a measured vacuum probe is the most effective option, which is one reason a vacuum scan is worth acquiring alongside every dataset. Failing that, reduce the probe learning rate so the object absorbs less of the error.

## The reconstruction gets noisier the longer it runs

This is overfitting. Hold out validation positions and stop where the validation loss bottoms out:

```python
ptycho.preprocess(..., val_ratio=0.05, val_mode="random")
best_iter = int(np.argmin(ptycho.val_iter_losses))
```

Deep priors converge fast and overfit fast, so this matters more for them than for pixelated reconstructions. A shallower network, `num_layers=2`, is more resistant.

## Low frequencies never fill in

Pixelated reconstructions recover low spatial frequencies slowly, so a large particle can stay flat in the middle long after its edges are sharp. This is a known property of gradient descent on a pixel grid rather than a bug.

Either run many more iterations, or switch to a [deep generative prior](./regularization.md), which recovers the low frequencies almost immediately.

## Out of memory

See [Scaling up](./scaling.md) for the full accounting. The quick triage:

- Failing before the first forward pass means the diffraction targets do not fit. Bin reciprocal space, crop the scan, stream with `target_residency = "cpu"`, or add GPUs.
- Failing partway through an iteration means the transients are too large. Reduce `batch_size`.
- Between calls, `torch.cuda.empty_cache()` and `gc.collect()` release memory held by a previous reconstruction.

Upsampling in direct ptychography is memory hungry out of proportion to its cost elsewhere. Reduce `max_batch_size`, to 1 if necessary, before giving up on it.

## Alternate scan rows are mirrored

The scan was acquired in a serpentine pattern. Reverse every second row before building the dataset:

```python
for i in range(1, data_array.shape[0], 2):
    data_array[i] = np.flip(data_array[i], axis=0)
```

## Some diffraction patterns are empty

Electron-counted data sometimes contains scan positions with zero counts. Find them first:

```python
empty = dset.array.sum((2, 3)) == 0
print(f"{empty.sum()} empty patterns")
```

Iterative reconstructions can exclude these positions with a boolean `positions_mask` passed through dataset preprocessing. Direct ptychography has no position masking, so for that route fill each empty pattern with the mean of its neighbors instead.

## Fitted parameters look implausible

Aberration fits are not always right, particularly at very large defocus, where they have been seen to return values an order of magnitude too small. Compare fitted values against your nominal conditions and against an independent estimate, such as the center-of-mass rotation fit, before carrying them into a long reconstruction.
