---
title: Diffraction simulation
---

# Diffraction simulation

```{image} ../../assets/diffraction/schematic-diffraction-simulation-light.svg
:alt: Diffraction simulation: the Ewald sphere sets the excitation error of each reflection, kinematical patterns weight each reflection by its structure factor and excitation error, Bloch waves add multiple scattering through the thickness, and a convergent probe gives CBED and Kossel patterns
:class: qem-only-light
:width: 100%
```

```{image} ../../assets/diffraction/schematic-diffraction-simulation-dark.svg
:alt: Diffraction simulation: the Ewald sphere sets the excitation error of each reflection, kinematical patterns weight each reflection by its structure factor and excitation error, Bloch waves add multiple scattering through the thickness, and a convergent probe gives CBED and Kossel patterns
:class: qem-only-dark
:width: 100%
```

quantEM simulates electron diffraction from crystal structures with two models. Kinematical patterns are fast enough to build orientation libraries with thousands of zone axes. Bloch wave calculations include multiple scattering and absorption, and are needed when intensities depend on thickness, and for CBED, LACBED, and Kossel patterns.

An [interactive version of these simulations](https://colab.stanford.edu/interactive-diffraction) runs in the browser, using the same structure factors as quantEM. Drag the crystal to tilt it, and adjust the thickness, convergence, and precession. The same simulator runs in Jupyter as `quantem.widget.DiffractionSim`.

## Crystal structures

A `Crystal` is built from ASE or read from a CIF file with `Crystal.from_cif`. `calculate_structure_factors` computes the kinematical structure factors up to `k_max` from the scattering factors of [Lobato and Van Dyck (2014)](https://doi.org/10.1107/S205327331401643X):

```python
from ase.build import bulk
from quantem.diffraction import Crystal

si = Crystal.from_ase(
    bulk("Si", "diamond", a=5.431, cubic=True),
    name="Si",
).calculate_structure_factors(k_max=3.0)
```

## Kinematical patterns

An orientation is a unit quaternion, and `quat_from_zone_axis` puts a lattice direction [uvw], or [UVTW] for hexagonal crystals, along the beam:

```python
from quantem.diffraction.rotations import quat_from_zone_axis

q_011 = quat_from_zone_axis(si.direction_vector((0, 1, 1))[None])[0]
pattern = si.generate_pattern(q_011, energy_ev=200e3, k_max=1.5)
```

The intensity of each reflection is

$$
I_g = |F_g|^2 \exp\left(-\frac{s_g^2}{2\sigma^2}\right),
$$

where $F_g$ is the structure factor and $s_g$ is the excitation error, the distance from the reciprocal lattice point to the Ewald sphere. This is the model used for orientation matching.

```{image} ../../assets/diffraction/sim-si-kinematical.png
:alt: Kinematical diffraction patterns of silicon along the [001], [011], and [111] zone axes
:width: 100%
```

## Excitation error models

The Gaussian envelope above has a fixed width, `sigma_excitation`. The slab model, `excitation_model="slab"`, instead uses the rocking curve of a foil of thickness $t$, which is the thin crystal limit of the Bloch wave calculation. Either envelope can be averaged over a precession cone with `precession_deg`:

```python
import numpy as np
import torch
from quantem.diffraction.rotations import qmult, quat_from_axis_angle

x_axis = torch.tensor([1.0, 0.0, 0.0], dtype=torch.float64)
q_tilt = qmult(quat_from_axis_angle(x_axis, torch.tensor(np.deg2rad(1.5))), q_011)

settings = {
    "Gaussian, sigma 0.02 1/A": dict(sigma_excitation=0.02),
    "slab, t = 300 A": dict(excitation_model="slab", thickness_A=300.0),
    "slab, t = 300 A, 1 deg precession": dict(
        excitation_model="slab", thickness_A=300.0, precession_deg=1.0
    ),
}
patterns = [
    si.generate_pattern(q_tilt, energy_ev=200e3, k_max=1.5, **kwargs)
    for kwargs in settings.values()
]
```

For silicon [011] tilted by 1.5°, the slab model excites only reflections near the Laue circle, and precession restores reflections on all sides:

```{image} ../../assets/diffraction/sim-excitation-models.png
:alt: Silicon [011] tilted by 1.5 degrees, simulated with a Gaussian envelope, the slab model, and the slab model with 1 degree precession
:width: 100%
```

## Dynamical diffraction with Bloch waves

In thicker specimens, electrons scatter more than once and the intensities depart from kinematical values. quantEM computes dynamical intensities with the Bloch wave method of [Bethe (1928)](https://doi.org/10.1002/andp.19283921704), using the absorptive form factors of [Weickenmeier and Kohl (1991)](https://doi.org/10.1107/S0108767391004804). One eigendecomposition per orientation gives the intensities at every thickness:

```python
from quantem.diffraction import bloch

si.calculate_dynamical_structure_factors(energy_ev=200e3, k_max=3.0)

thicknesses = np.arange(0.0, 2001.0, 10.0)
dyn = bloch.dynamical_pattern(si, q_011, thicknesses, energy_ev=200e3, k_max=1.5)
```

The (200) reflections of silicon are kinematically forbidden, but appear in the dynamical patterns by double diffraction:

```{image} ../../assets/diffraction/sim-si-dynamical.png
:alt: Kinematical and dynamical diffraction patterns of silicon [011] at thicknesses of 100, 500, and 1500 Angstroms
:width: 100%
```

Each beam oscillates in intensity with thickness as it exchanges intensity with the others (Pendellösung), while absorption damps the oscillations:

```{image} ../../assets/diffraction/sim-pendellosung.png
:alt: Intensity of the 000, 1-11, 0-22, and 200 beams of silicon [011] as a function of thickness from 0 to 2000 Angstroms
:width: 65%
:align: center
```

## CBED and LACBED

`calculate_cbed` treats each incident direction in the probe as an independent plane wave, which fills each disk with the rocking curve of its reflection:

```python
cbed = bloch.calculate_cbed(
    si,
    q_011,
    [500.0, 1000.0, 2000.0],
    energy_ev=200e3,
    semiconv_mrad=3.0,
    n_rings=16,
    k_max=1.3,
)
```

```{image} ../../assets/diffraction/sim-cbed.png
:alt: Simulated CBED patterns of silicon [011] with a 3 mrad convergence semiangle at 500, 1000, and 2000 Angstroms
:width: 100%
```

`calculate_lacbed` maps the rocking curve of a single reflection over a larger aperture, without overlap from neighboring disks.

## Kossel patterns

At convergence angles well beyond the Bragg angles, the disks overlap completely. Each reflection at its Bragg condition then removes intensity from the bright field, producing a dark line:

```python
kossel = bloch.calculate_kossel(
    si,
    q_011,
    [500.0, 1500.0],
    energy_ev=200e3,
    semiconv_mrad=40.0,
    n_pixels=160,
    k_max=1.2,
)
```

```{image} ../../assets/diffraction/sim-kossel.png
:alt: Bright field Kossel patterns of silicon [011] over a 40 mrad aperture at 500 and 1500 Angstroms
:width: 70%
:align: center
```

The bright field depends only on the beam direction in the crystal, so one calculation over all directions covers every orientation, an approach used for EBSD master patterns by [Callahan and De Graef (2013)](https://doi.org/10.1017/S1431927613001840). `calculate_kossel_reference` stores this calculation, and `kossel_from_reference` extracts the pattern for any orientation in milliseconds:

```python
reference = bloch.calculate_kossel_reference(
    si, 500.0, energy_ev=200e3, angle_step_mrad=2.0, k_max=1.2,
)
lines = bloch.kossel_lines(si, 500.0, energy_ev=200e3, k_max=1.2)
fig, ax = bloch.plot_kossel_reference(reference, si, lines=lines, max_index=3)

pattern = bloch.kossel_from_reference(
    reference, q_011, semiconv_mrad=40.0, n_pixels=160,
)["bright_field"]
```

```{image} ../../assets/diffraction/sim-kossel-reference.png
:alt: Kossel reference pattern of silicon over the full hemisphere of incident directions, with low-index zone axes labeled
:width: 70%
:align: center
```

:::{seealso}
- [Kinematical and dynamical electron diffraction](https://github.com/electronmicroscopy/quantem-tutorials/blob/main/tutorials/diffraction/acom_02_diffraction_simulation.ipynb): the tutorial notebook for this page.
- [Interactive electron diffraction](https://colab.stanford.edu/interactive-diffraction): these simulations in the browser.
- [Bethe (1928)](https://doi.org/10.1002/andp.19283921704), *Theorie der Beugung von Elektronen an Kristallen*, Annalen der Physik **392**, 55.
- [Weickenmeier and Kohl (1991)](https://doi.org/10.1107/S0108767391004804), *Computation of absorptive form factors for high-energy electron diffraction*, Acta Crystallographica A **47**, 590.
- [Lobato and Van Dyck (2014)](https://doi.org/10.1107/S205327331401643X), *An accurate parameterization for scattering factors, electron densities and electrostatic potentials for neutral atoms that obey all physical constraints*, Acta Crystallographica A **70**, 636.
- [Callahan and De Graef (2013)](https://doi.org/10.1017/S1431927613001840), *Dynamical electron backscatter diffraction patterns. Part I: Pattern simulations*, Microscopy and Microanalysis **19**, 1255.
- De Graef, *Introduction to Conventional Transmission Electron Microscopy* (2003); Zuo and Spence, *Advanced Transmission Electron Microscopy* (2017); Kirkland, *Advanced Computing in Electron Microscopy* (2020).
:::
