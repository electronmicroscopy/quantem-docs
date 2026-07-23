---
title: API reference
---

# API reference

:::{note}
A full auto-generated API reference is planned. Until then, this page lists the main public entry points; docstrings in the source are the authoritative reference.
:::

## `quantem.core`

| Import | Contents |
| --- | --- |
| `quantem.core.datastructures` | `Dataset`, `Dataset2d`, `Dataset3d`, `Dataset4d`, `Dataset4dstem`, `Vector` |
| `quantem.core.io` | `read_2d`, `read_4dstem`, `read_emdfile_to_4dstem`, `load`, `print_file`, `AutoSerialize` |
| `quantem.core.visualization` | `show_2d`, `linescan`, `CustomNormalization`, `NormalizationConfig`, `ShowParams`, `ScalebarConfig`, `turbo_black`, `axes_with_inset` |
| `quantem.core.config` | `get`, `set`, `set_device`, `get_device`, `validate_device`, `write` (see [Configuration](./configuration.md)) |

## Modality subpackages

| Import | Contents |
| --- | --- |
| `quantem.imaging` | `drift`, `lattice` |
| `quantem.diffraction` | `disk_detection`, `bragg_vectors`, `model_fitting`, `strain` |
| `quantem.diffractive_imaging` | `ptychography`, `ptychography_lite`, `direct_ptychography`, model components (`object_models`, `probe_models`, `detector_models`, `dataset_models`, `origin_models`), `constraints`, `optimize_hyperparameters` |
| `quantem.tomography` | `tomography`, `tomography_lite`, `preprocess`, `radon` |
| `quantem.spectroscopy` | under development |

Browse the source on [GitHub](https://github.com/electronmicroscopy/quantem/tree/main/src/quantem) for the complete listing.
