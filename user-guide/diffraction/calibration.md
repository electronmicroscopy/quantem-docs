---
title: Calibration
---

# Calibration

```{image} ../../assets/diffraction/schematic-calibration-light.svg
:alt: Calibration in four steps: a plane fit to the direct beam position removes the descan, the curl of the center-of-mass field gives the detector-to-scan rotation, the pixel size and elliptic distortion are fit to the rings or spots of known phases, and every ring and phase is checked
:class: qem-only-light
:width: 100%
```

```{image} ../../assets/diffraction/schematic-calibration-dark.svg
:alt: Calibration in four steps: a plane fit to the direct beam position removes the descan, the curl of the center-of-mass field gives the detector-to-scan rotation, the pixel size and elliptic distortion are fit to the rings or spots of known phases, and every ring and phase is checked
:class: qem-only-dark
:width: 100%
```

Orientation matching and strain mapping compare the detected peaks with reciprocal lattice vectors in Å⁻¹, so the peak positions must first be converted from detector pixels. We calibrate in four steps: remove the descan, measure the rotation between the detector and the scan, fit the pixel size and elliptic distortion against known phases, and check every candidate phase. All steps operate on the detected peaks rather than the diffraction images, and the result is a `DiffractionCalibration` that can be saved and applied to other datasets.

The examples use the titanium dataset of [MacLaren et al. (2024)](https://doi.org/10.1111/jmi.13275), starting from the peaks found in [Bragg disk detection](./disk-detection.md).

## Removing the descan

Imperfect descan moves the direct beam across the detector as the probe scans. `measure_origins` takes the brightest peak near the detector center as the direct beam at each position and fits a plane over the scan. `correct_peak_origins` subtracts the fitted origins and returns a corrected copy of the peaks:

```python
origins = bv.measure_origins(search_radius=6.0)
bv_centered = bv.correct_peak_origins(origins, origin_ref=(0.0, 0.0))

fig, axs = bv.plot_origin_fit(origins, search_radius=6.0)
```

For the titanium scan, the residuals of the plane fit follow the shapes of the alpha laths, which suggests they come from the specimen rather than the descan:

```{image} ../../assets/diffraction/acom-origin-fit.png
:alt: Measured diffraction origin, plane fit, and residual over the scan, for the detector row and column coordinates
:width: 100%
```

If the direct beam is far from the detector center, pass its approximate position as `center`.

## Scan rotation

```{image} ../../assets/diffraction/schematic-scan-rotation-light.svg
:alt: Scan rotation: the center of mass of the direct beam is a gradient field in the scan frame; in the detector frame it is rotated and has curl, and the angle that removes the curl is the rotation, ambiguous by 180 degrees
:class: qem-only-light
:width: 100%
```

```{image} ../../assets/diffraction/schematic-scan-rotation-dark.svg
:alt: Scan rotation: the center of mass of the direct beam is a gradient field in the scan frame; in the detector frame it is rotated and has curl, and the angle that removes the curl is the rotation, ambiguous by 180 degrees
:class: qem-only-dark
:width: 100%
```

The detector axes are usually rotated relative to the scan axes. This rotation sets the in-plane orientations and strain directions, while zone axes and phases do not depend on it. `measure_scan_rotation` finds it from the center of mass of the direct beam, which in the scan frame is the gradient of the projected potential and therefore has no curl. Rotating the detector axes until the curl vanishes gives the angle, up to 180°, and a transposed detector is tested as well:

```python
rotation = bv.measure_scan_rotation(origins, plot=True)
```

```{image} ../../assets/diffraction/cal-scan-rotation.png
:alt: Mean squared curl and divergence of the center-of-mass field against the trial rotation angle for the titanium scan
:width: 60%
:align: center
```

The result is written to the dataset metadata, where `calibrate`, `calibrate_2d`, strain mapping, and ptychography read it. In crystalline specimens, diffraction contrast can dominate the center of mass. For the titanium scan the curl changes by less than a factor of two with angle, and `measure_scan_rotation` warns that its result of 23.5° is unreliable. We therefore use the 34° reported by [MacLaren et al. (2024)](https://doi.org/10.1111/jmi.13275), passed as `rotation_ccw_deg` below. A rotation measured by ptychography in the same session can be used the same way.

## Pixel size and elliptic distortion

```{image} ../../assets/diffraction/schematic-calibration-routes-light.svg
:alt: Two routes to the pixel size and ellipse. calibrate matches the maxima of the radial peak histogram to the allowed ring radii; calibrate_2d sums the peaks into one spot pattern, indexes it, and fits a 2 by 2 distortion to the paired spots
:class: qem-only-light
:width: 100%
```

```{image} ../../assets/diffraction/schematic-calibration-routes-dark.svg
:alt: Two routes to the pixel size and ellipse. calibrate matches the maxima of the radial peak histogram to the allowed ring radii; calibrate_2d sums the peaks into one spot pattern, indexes it, and fits a 2 by 2 distortion to the paired spots
:class: qem-only-dark
:width: 100%
```

Two routines fit the pixel size and elliptic distortion. Choose by the texture of the specimen:

| Routine | Use for | Fits |
| --- | --- | --- |
| `calibrate` | Many orientations: polycrystals, random or fiber textures | Maxima of the radial peak histogram against the allowed ring radii |
| `calibrate_2d` | One dominant orientation: a single crystal or matrix grain | The summed 2D spot pattern, indexed and fit with a 2 × 2 distortion |

Both take the candidate phases as `Crystal` objects with structure factors calculated:

```python
from ase.build import bulk
from quantem.diffraction import Crystal

ti_alpha = Crystal.from_ase(
    bulk("Ti", "hcp", a=2.9505, c=4.6855),
    name="Ti alpha",
).calculate_structure_factors(k_max=1.5)

ti_beta = Crystal.from_ase(
    bulk("Ti", "bcc", a=3.26, cubic=True),
    name="Ti beta",
).calculate_structure_factors(k_max=1.5)
```

### Rings: `calibrate`

`calibrate` matches the measured ring radii to the rings the reference crystals allow, using positions only. Every allowed ring counts equally and a missing ring costs nothing, so texture and dynamical intensities do not bias the scale. The scale is scanned within ±10% of the guess, the ellipse and scale are refined in turn, and each ring is then checked separately:

```python
cal = bv_centered.calibrate(
    [ti_alpha, ti_beta],
    pixel_size_guess=0.038,     # 1/Angstrom per pixel
    rotation_ccw_deg=34.0,
    plot=True,
)
print(cal)
```

```
DiffractionCalibration(pixel_size=0.038422 1/A/px, ellipse: e11 +0.00586 e12 +0.00605, rotation 34 deg, 12 rings, rms 0.18%)
```

The figure compares the measured peaks with the alpha rings before (left) and after (right) the fit, as a radial histogram (top) and as azimuth against scattering vector (bottom):

```{image} ../../assets/diffraction/cal-calibrate-1d.png
:alt: Radial histograms and azimuth plots of the measured peaks against the alpha titanium rings, before and after calibrate
:width: 100%
```

Ring radii repeat at fixed ratios, so a position-only match is unique only over a limited range of scales. Keep the guess within about 10%, and widen `scale_search` only for a guess that is far out. `calibrate` warns when the fit is unreliable, including when the peaks cover too few azimuths to fix the ellipse, which indicates that `calibrate_2d` is the better choice.

### Spots: `calibrate_2d`

When one orientation dominates the scan, the summed peaks form a single sharp spot pattern. `calibrate_2d` indexes this pattern against the candidate crystals, pairs the measured and simulated spots, and fits a 2 × 2 map from pixels to Å⁻¹. The symmetric part of the map gives the pixel size and ellipse, and the rotation part belongs to the crystal orientation:

```python
cal = bv_centered.calibrate_2d(
    [ti_alpha, ti_beta],
    pixel_size_guess=0.038,
    energy_ev=200e3,
    precession_deg=0.5,
    rotation_ccw_deg=34.0,
    plot=True,
)
print(cal)
```

```
DiffractionCalibration(pixel_size=0.038418 1/A/px, ellipse: e11 +0.00385 e12 +0.00483, rotation 34 deg, Ti beta, 27 spots, rms 0.0025 1/A)
```

The beta matrix of the titanium alloy is a single grain, so its spots dominate the summed pattern. The figure shows the beta rings (top) and the 2D histogram of every peak in red under the simulated spots in black (bottom), before and after the fit:

```{image} ../../assets/diffraction/cal-calibrate-2d.png
:alt: Ring comparison and 2D histogram of all peaks under the simulated beta titanium spots, before and after calibrate_2d
:width: 100%
```

`calibrate_2d` needs a guess within a few percent, which `calibrate` can provide. Within one zone axis, a lattice parameter error of the reference cannot be distinguished from detector ellipticity, so the reference should be a well-known structure. For this scan the two routines agree to 0.01%.

### Subsets of positions

```{image} ../../assets/diffraction/schematic-calibration-subsets-light.svg
:alt: Calibrating on a subset of positions: select a region of known phase, calibrate on its peaks only, and apply the calibration to every position
:class: qem-only-light
:width: 100%
```

```{image} ../../assets/diffraction/schematic-calibration-subsets-dark.svg
:alt: Calibrating on a subset of positions: select a region of known phase, calibrate on its peaks only, and apply the calibration to every position
:class: qem-only-dark
:width: 100%
```

Both routines accept `positions`, a list of (row, col) or an (R, C) boolean mask, to calibrate on a region whose crystallography is known, such as one grain or a standard particle in the field of view. The calibration is then applied to the whole scan. Here we use masks of each phase from a previous phase map:

```python
# mask_alpha, mask_beta: (R, C) boolean masks, e.g. cm.mask("Ti beta") > 0.5
cal_beta = bv_centered.calibrate_2d(
    ti_beta, 0.038, energy_ev=200e3, precession_deg=0.5, positions=mask_beta,
)
cal_alpha = bv_centered.calibrate(ti_alpha, 0.038, positions=mask_alpha)
```

The beta matrix alone gives 0.038425 Å⁻¹/px and the alpha laths alone give 0.038431 Å⁻¹/px, within 0.04% of the values from the whole scan.

### Applying and reusing a calibration

A `DiffractionCalibration` stores the pixel size, ellipse, rotation, and transpose, together with the evidence behind them: the matched rings or spots and their residuals. `apply_calibration` converts the centered peaks to Å⁻¹, and the returned `Vector` carries the calibration with it:

```python
peaks = bv_centered.apply_calibration(cal)
```

Calibrating against the specimen assumes its lattice parameters are known. For strained specimens, or phases whose lattice parameters vary with composition, we recommend calibrating on a standard such as nanocrystalline gold, saving the result, and applying it to the specimen. `rebin` converts a saved calibration to data with a different detector binning:

```python
gold = Crystal.from_ase(
    bulk("Au", "fcc", a=4.078, cubic=True),
    name="Au",
).calculate_structure_factors(k_max=1.5)

# bv_au_centered: detected and centered peaks of the gold standard
cal_au = bv_au_centered.calibrate(gold, pixel_size_guess=0.038)
cal_au.save("calibration_Au.zip")

from quantem.core.io.serialize import load

peaks = bv_centered.apply_calibration(load("calibration_Au.zip"))
```

## Checking every phase

A phase with the wrong lattice parameter can still give a good overall fit, and matching cannot recover from it, so we check each candidate phase before matching. `plot_ring_comparison` shows the radial histogram of the calibrated peaks against the rings of each crystal:

```python
from quantem.diffraction import CrystalMap

cm = CrystalMap.from_vectors(peaks, [ti_alpha, ti_beta], energy_ev=200e3, precession_deg=0.5)
fig, axs = cm.plot_ring_comparison()
```

```{image} ../../assets/diffraction/cal-ring-comparison.png
:alt: Radial histogram of the calibrated peaks against the alpha titanium rings (top) and beta titanium rings (bottom)
:width: 100%
```

Both phases line up with the measured peaks. The strongest alpha and beta rings nearly overlap, a consequence of the orientation relationship between the phases described in [orientation and phase mapping](./orientation-mapping.md). `plot_calibration` adds the azimuth of every peak, where a ring that wobbles with azimuth indicates remaining elliptic distortion, and `plot_bragg_rings` draws the rings over the Bragg vector map in 2D:

```python
fig, ax = cm.plot_bragg_rings(n_rings=6)
```

```{image} ../../assets/diffraction/cal-bragg-rings.png
:alt: Bragg vector map of the titanium scan with the six strongest alpha (red) and beta (blue) rings overlaid
:width: 55%
:align: center
```

## Refining the calibration from strain

```{image} ../../assets/diffraction/schematic-refine-calibration-light.svg
:alt: Refining the calibration from strain: the deformation at each position combines strain and calibration error, and the median over many grains leaves the scale and ellipse residual
:class: qem-only-light
:width: 100%
```

```{image} ../../assets/diffraction/schematic-refine-calibration-dark.svg
:alt: Refining the calibration from strain: the deformation at each position combines strain and calibration error, and the median over many grains leaves the scale and ellipse residual
:class: qem-only-dark
:width: 100%
```

After orientation mapping, the deformation fitted at each position by `calculate_strain` contains both the local strain and any global calibration error. `refine_calibration` takes the median deformation over many differently oriented grains, which averages the strain away and leaves the residual scale and ellipse:

```python
from quantem.diffraction import calibration

strain_maps = [cm[name].calculate_strain(mask=cm.mask(name) > 0.5) for name in cm.names]
residual = calibration.refine_calibration(strain_maps)
peaks = calibration.transform_peaks(peaks, residual["correction"])
```

For the titanium scan, the median over 17,715 positions gives a residual scale of 0.05% and a residual ellipticity below 0.1%, which confirms the calibration from `calibrate_2d`.

The detector rotation is absorbed into the fitted orientations and cannot be refined this way.

## Lower-level functions

The routines above are built from functions in `quantem.diffraction.calibration`, which can be used directly:

| Function | Purpose |
| --- | --- |
| `calibrate_pixel_size` | Scale from the overlap of the radial histogram with a simulated ring profile |
| `calibrate_pixel_size_matching` | Scale that maximizes the orientation matching correlation, which resolves ring ratio ambiguities |
| `calibrate_ellipse` | Elliptic distortion from the sharpness of the log-radius histogram, independent of the scale |
| `peaks_to_calibrated` | Pixel peaks to Å⁻¹ with a given pixel size, rotation, and ellipse |
| `apply_ellipse`, `scale_peaks`, `transform_peaks` | Apply an ellipse, a scale, or a general 2 × 2 map to calibrated peaks |
| `select_positions` | Restrict a peak `Vector` to a list or mask of positions |

:::{seealso}
[Orientation, phase and strain mapping of a titanium alloy](https://github.com/electronmicroscopy/quantem-tutorials/blob/main/tutorials/diffraction/acom_01_orientation_phase_strain_Ti.ipynb): the tutorial notebook for this dataset, including centering and calibration.
:::
