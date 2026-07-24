---
title: quantEM
site:
  hide_outline: true
  hide_title_block: true
---

:::{div}
:class: qem-logo-box

```{image} assets/anim/qem-base-light.svg
:class: qem-lbase qem-logo-light
:alt: quantEM
```

```{image} assets/anim/qem-base-dark.svg
:class: qem-lbase qem-logo-dark
:alt: quantEM
```

```{image} assets/anim/qem-eels.svg
:class: qem-el qem-el-eels
:alt: EELS spectrum
```

```{image} assets/anim/qem-struct.svg
:class: qem-el qem-el-struct
:alt: crystal structure
```

```{image} assets/anim/qem-dif-light.svg
:class: qem-el qem-el-dif qem-logo-light
:alt: diffraction pattern
```

```{image} assets/anim/qem-dif-dark.svg
:class: qem-el qem-el-dif qem-logo-dark
:alt: diffraction pattern
```

```{image} assets/anim/qem-tomo-light.svg
:class: qem-el qem-el-tomo qem-logo-light
:alt: tomography
```

```{image} assets/anim/qem-tomo-dark.svg
:class: qem-el qem-el-tomo qem-logo-dark
:alt: tomography
```

:::

:::{div}
:class: qem-tagline
**quantEM** is an open source Python toolkit for quantitative electron microscopy: imaging, diffraction, simulation, ptychography, tomography, and spectroscopy. It is built on PyTorch, runs on CPUs and GPUs, and integrates deep learning methods.
:::

::::{grid} 1 2 2 3

:::{card} 🚀 Get started
:link: ./get-started/overview.md
What quantEM is, how to install it, and how the package is organized.
:::

:::{card} 🔬 Imaging
:link: ./user-guide/imaging/index.md
Drift correction and lattice analysis for atomic resolution images.
:::

:::{card} 💠 Diffraction
:link: ./user-guide/diffraction/index.md
Bragg disk detection, model fitting, and strain mapping for 4D-STEM.
:::

:::{card} 🌀 Diffractive imaging
:link: ./user-guide/diffractive-imaging/index.md
Iterative and direct ptychography, from quick previews to multi-GPU reconstructions.
:::

:::{card} 🧊 Tomography
:link: ./user-guide/tomography/index.md
Alignment, preprocessing, and 3D reconstruction of tilt series.
:::

:::{card} 🌈 Spectroscopy
:link: ./user-guide/spectroscopy/index.md
Analysis of spectroscopic signals such as EDS.
:::

::::

---

quantEM is developed openly on [GitHub](https://github.com/electronmicroscopy/quantem), with worked examples in [quantem-tutorials](https://github.com/electronmicroscopy/quantem-tutorials). It is free software under the [MIT license](./project/license.md).
