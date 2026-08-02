---
title: Hyperparameter optimization
---

# Hyperparameter optimization

Several parameters cannot be measured directly and must instead be determined by searching over plausible values. The defocus, the scan rotation, and the reciprocal pixel size all fall into this category, and each can be sufficiently in error to prevent a reconstruction from succeeding while still appearing reasonable.

`OptimizePtychography` applies [Optuna](https://optuna.org) to a complete reconstruction pipeline. Each trial constructs a new reconstruction on a private copy of the dataset, runs it for a small number of iterations, and reports the final loss.

## Searching on a cropped subset

We recommend performing the search on a small crop of the data, and applying the result to the full field of view. Reducing the time per trial from roughly 17 seconds to 2 seconds is often the difference between a search that can be run routinely and one that can be run only once.

```python
dc_crop = dset.crop(((0, 128), (0, 128)), axes=(0, 1), modify_in_place=False)
```

## Searching a reconstruction parameter

```python
from functools import partial
from quantem.diffractive_imaging import PtychoLite, PtychographyDatasetRaster
from quantem.diffractive_imaging.optimize_hyperparameters import (
    OptimizePtychography, OptimizationParameter,
)

optimizer = OptimizePtychography.from_constructors(
    constructors={"ptychography_class": PtychoLite.from_dataset},
    base_kwargs={
        "init": {
            "device": "gpu",
            "num_slices": 1,
            "num_probes": 1,
            "obj_type": "pure_phase",
            "energy": PROBE_ENERGY,
            "semiangle_cutoff": PROBE_SEMIANGLE,
            "defocus": OptimizationParameter(low=-212, high=-141),
        },
        "reconstruct": {"num_iters": 10, "batch_size": 128},
    },
    reconstruction_class="ptycholite",
    n_trials=20,
    direction="minimize",
)

optimizer.optimize().visualize()
print(optimizer.study.best_params)      # {"init.defocus": -210.1}
```

Each trial parameter is named according to its path within `base_kwargs`, so a defocus passed to the constructor appears as `init.defocus`. When using the full modular interface, arguments to the individual component models are addressed in the same manner, for example `probe.probe_params.defocus`.

Set `log=True` on an `OptimizationParameter` for any quantity spanning orders of magnitude, such as a learning rate.

## Searching over a calibration

Calibrations are established when the dataset is constructed, and searching over them therefore requires a dataset constructor:

```python
def make_pdset(reciprocal_pixel_size, dset):
    trial = dset.copy()
    trial.sampling[-2:] = [reciprocal_pixel_size] * 2
    return PtychographyDatasetRaster.from_dataset4dstem(trial, verbose=False)

optimizer = OptimizePtychography.from_constructors(
    constructors={"ptychography_class": PtychoLite.from_dataset},
    base_kwargs={"init": {...}, "reconstruct": {"num_iters": 5, "batch_size": 128}},
    dataset_constructor=partial(make_pdset, dset=dc_crop),
    dataset_kwargs={
        "reciprocal_pixel_size": OptimizationParameter(low=s0 * 0.9, high=s0 * 1.1),
    },
    dataset_preprocess_kwargs={
        "com_fit_function": "constant",
        "probe_energy": PROBE_ENERGY,
        "force_com_rotation": -169,
        "plot_rotation": False,
        "plot_com": False,
    },
    n_trials=20,
)
```

Dataset-level parameters are named without a prefix, and this one therefore appears as `reciprocal_pixel_size`.

:::{warning}
A bright-field disk fit can be in error by 10% or more, which is sufficient for the search to converge to the edge of a ±10% window. If the best value lies at a boundary of the search range, we recommend widening the range and repeating the search rather than accepting the result.
:::

## Searching over a few parameters at a time

In our experience, optimizing one or two parameters at a time is considerably more efficient than searching over all of them simultaneously. Studies can be chained using `from_optimizer`, which holds the previously optimized parameters at their best values and introduces new ones:

```python
next_study = OptimizePtychography.from_optimizer(
    previous_study=optimizer,
    new_params={"init.semiangle_cutoff": OptimizationParameter(20, 28)},
    n_trials=20,
)
```

## Grid search

To examine the full parameter landscape rather than only the optimum, assign each parameter an `n_points` and perform a grid search. Every reconstructed object is plotted, with the best result outlined:

```python
optimizer.grid_search(plot_objects=True)
```

We consider inspection of the resulting objects to be an essential part of this process. The loss is only a proxy for reconstruction quality, and visual assessment is frequently a better indicator of which result is correct.

## Which parameters to search, and in what order

1. **Calibrations first**, meaning the reciprocal pixel size and the scan rotation, since every subsequent step depends upon them.
2. **The probe next**, first the defocus and then the astigmatism. Direct ptychography will usually provide values close enough that only a narrow range requires searching, and we therefore recommend consulting [Direct ptychography](./direct-ptychography.md) before using a full reconstruction search for this purpose.
3. **Reconstruction parameters last**, such as learning rates and regularization weights. These generally have broad optima and rarely justify a careful search.

The structure of the model, meaning the number of slices and probe modes, is better determined by inspecting reconstructions than by searching. The loss will almost always improve as parameters are added, whether or not the additional structure is physically meaningful.

:::{seealso}
Worked examples in the tutorials repository:

- [Hyperparameter optimization for iterative ptychography](https://github.com/electronmicroscopy/quantem-tutorials/blob/main/tutorials/diffractive_imaging/ptycho_iter_06_hyperparameters.ipynb): chained studies and grid searches using `OptimizePtychography`.
- [Hyperparameter optimization for direct ptychography](https://github.com/electronmicroscopy/quantem-tutorials/blob/main/tutorials/diffractive_imaging/hyperparameter_optimization.ipynb): fitting aberrations and rotation before any iterative reconstruction.
:::
