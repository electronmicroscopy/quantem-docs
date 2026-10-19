"""Architecture figure of quantEM for the documentation.

A web version of Figure 1 of the quantEM paper (make_fig_architecture.py in the
paper sources): open source foundations, the core engine, the shared physics
layer, five stripes, their modules, and combined modules spanning adjacent
stripes. Two changes for the docs:

- Light and dark variants, switched by the qem-only-light / qem-only-dark
  classes on the page.
- Development status: modules in IN_DEVELOPMENT are drawn as dashed outlines.
  Everything else is released, merged, or in an open pull request. Edit the set
  when a module lands.

Run with:  python scripts/architecture/make_architecture.py
Writes assets/architecture-light.svg and assets/architecture-dark.svg.
"""

import os
import re
from types import SimpleNamespace

from figstyle import PALETTE, WIDTH, SVG, band, box, icon, text

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "..", "assets"))

# ----- content (as in the paper) ------------------------------------------------

STRIPES = [
    ("IMAGING", "violet", "imaging"),
    ("DIFFRACTION", "blue", "diffraction"),
    ("TOMOGRAPHY", "teal", "tomography"),
    ("SPECTROSCOPY", "orange", "spectroscopy"),
    ("SIMULATION", "pink", "simulation"),
]

MODULES = {
    0: [["Drift correction"], ["Quantitative", "atomic fitting"], ["Geometric phase", "analysis"]],
    1: [["Orientation and", "phase mapping"], ["Strain mapping"], ["Semicrystalline", "Bragg analysis"],
        ["Pair distribution", "functions"]],
    2: [["Conventional", "reconstruction"], ["Differentiable and", "neural tomography"],
        ["Gaussian splatting", "tomography"], ["3D atom fitting"]],
    3: [["X-ray spectroscopy", "(XEDS)"], ["Energy-loss", "spectroscopy (EELS)"]],
    4: [["Bloch wave"], ["Multislice"], ["Tomographic", "projections"], ["Other forward", "models"]],
}

# combined modules: (first column, last column, tier, title, subtitle)
COMBINED = [
    (0, 1, 5, "Direct ptychography", "differential phase contrast, parallax, single sideband"),
    (0, 1, 6, "Iterative ptychography", "mixed-state, multislice, neural objects"),
    (2, 3, 5, "Spectroscopic tomography", "X-ray and energy-loss spectra in three dimensions"),
    (1, 2, 7, "Diffraction tomography", "scanning diffraction and bend contour tomography"),
    (0, 2, 8, "Ptychographic tomography", "multislice ptychography at many tilts, joint alignment"),
]

PHYSICS = ["Crystallography", "Scattering potentials", "Electron optics", "Calibration"]

LIBRARIES = [("PyTorch", "tensors, autograd, GPUs"), ("Zarr", "chunked array storage"),
             ("NumPy, SciPy", "CPU arrays"), ("Matplotlib", "static figures"),
             ("anywidget", "interactive widgets")]

CORE_SIDES = (["forward models, optimizers,", "constraints, neural representations,", "multi-GPU, custom CUDA kernels"],
              ["Zarr zip files for any analysis", "object, including models and", "optimizer states"])

# modules drawn as dashed outlines (in development or planned), by label
IN_DEVELOPMENT = {
    "Geometric phase analysis",
    "Gaussian splatting tomography",
    "Multislice",
    "Other forward models",
    "Spectroscopic tomography",
    "Diffraction tomography",
    "Ptychographic tomography",
}

THEMES = {
    "light": dict(
        container="#ffffff", container_edge=PALETTE["gray"][0], found=PALETTE["gray"][1],
        found_label=PALETTE["gray"][3], lib_fill="#ffffff", lib_fg="#212529", lib_edge="#212529",
        planned_shade=1, planned_text="#495057", logo="quantem-logo-light.svg",
    ),
    "dark": dict(
        container="#221f1d", container_edge="#57534e", found=PALETTE["gray"][0],
        found_label="#ced4da", lib_fill="#2b2826", lib_fg="#f1f3f5", lib_edge="#868e96",
        planned_shade=0, planned_text="#ced4da", logo="quantem-logo-dark.svg",
    ),
}

LOGO_BBOX = (14.1133, 17.6445, 431.962, 234.332)  # x, y, w, h of the drawn logo content
DARK = "#1b1e21"  # fill behind the white line art in the core band

SPEC = dict(
    width=WIDTH, margin=10.0, gap=6.0, row_h=22.0, row_g=4.0,
    h_head=30.0, h_phys=30.0, h_core=66.0, h_found=46.0,
    f_mod=6.6, f_comb=6.8, f_comb_sub=5.5, f_head=6.6, head_icon=0.85, head_icon_dy=10.0, head_label_dy=25.0,
    f_band=6.6, f_phys=6.6,
    card_w=72.0, card_gap=6.0, side_gap=8.0, core_icon=1.25, core_icon_dx=19.0, core_text_dx=32.0,
    f_core=7.8, f_core_sub=5.7, core_title_dy=22.0, core_sub_dy=33.0, core_sub_step=7.6,
    glyph=1.0, glyph_dy=17.0, card_title_dy=39.0, card_sub_dy=47.5,
    lib_dy=17.0, lib_h=24.0, f_lib=7.2, f_lib_sub=5.6,
)
NROW = 8


def layout(spec):
    """Positions in stack orientation (foundations at the bottom)."""
    g = SimpleNamespace(**spec)
    g.y_col_top = 10.0
    g.y_mod_bottom = g.y_col_top + 5.0 + NROW * g.row_h + (NROW - 1) * g.row_g
    g.y_head = g.y_mod_bottom + 5.0
    g.y_col_bot = g.y_head + g.h_head + 3.0
    g.y_phys = g.y_col_bot + 6.0
    g.y_core = g.y_phys + g.h_phys + 6.0
    g.y_qem_bot = g.y_core + g.h_core + 8.0
    g.y_found = g.y_qem_bot + 8.0
    g.H = g.y_found + g.h_found + 2.0
    g.W = g.width
    g.xl, g.xr = g.margin, g.W - g.margin
    g.cw = (g.xr - g.xl - g.gap * (len(STRIPES) - 1)) / len(STRIPES)
    g.col_x = lambda i: g.xl + i * (g.cw + g.gap)
    g.row_y = lambda k: g.y_mod_bottom - k * g.row_h - (k - 1) * g.row_g
    return g


def build(theme):
    t = THEMES[theme]
    g = layout(SPEC)
    W, H = g.W, g.H

    def Y(y, h):  # stack coordinates to output (top to bottom) coordinates
        return H - y - h

    svg = SVG(W, H, "Structure of quantEM: open source foundations, the core engine with automatic differentiation, "
                    "Dataset, Vector and automatic serialization, the shared physics layer, five stripes "
                    "(imaging, diffraction, tomography, spectroscopy, simulation) with their modules, and combined "
                    "modules spanning several stripes. Dashed modules are in development.")
    gr = PALETTE["gray"]

    lay = svg.layer("container")
    lay.append(
        f'<rect x="2.00" y="{Y(2.0, g.y_qem_bot - 2.0):.2f}" width="{W - 4.0:.2f}" height="{g.y_qem_bot - 2.0:.2f}" '
        f'rx="10" fill="{t["container"]}" stroke="{t["container_edge"]}" stroke-width="0.8"/>'
    )

    lay = svg.layer("modules")
    for i, rows in MODULES.items():
        color = STRIPES[i][1]
        for j, label in enumerate(rows):
            x, y = g.col_x(i), Y(g.row_y(j + 1), g.row_h)
            if " ".join(label) in IN_DEVELOPMENT:
                c = PALETTE[color][t["planned_shade"]]
                lay += box(x, y, g.cw, g.row_h, "none", rx=4, title=label, size=g.f_mod, fg=c, stroke=c,
                           dashed=True, shade=False, stroke_w=0.9)
            else:
                fill = svg.grad([PALETTE[color][1], PALETTE[color][2]])
                lay += box(x, y, g.cw, g.row_h, fill, rx=4, title=label, size=g.f_mod)

    lay = svg.layer("combined modules")
    for c0, c1, k, title, sub in COMBINED:
        x0, x1 = g.col_x(c0), g.col_x(c1) + g.cw
        y = Y(g.row_y(k), g.row_h)
        if title in IN_DEVELOPMENT:
            colors = [PALETTE[STRIPES[i][1]][t["planned_shade"]] for i in range(c0, c1 + 1)]
            stroke = svg.grad(colors, horizontal=True, plateau=0.6)
            lay += box(x0, y, x1 - x0, g.row_h, "none", rx=4, title=title, sub=sub, size=g.f_comb,
                       sub_size=g.f_comb_sub, fg=t["planned_text"], stroke=stroke, dashed=True, shade=False,
                       stroke_w=0.9)
        else:
            colors = [PALETTE[STRIPES[i][1]][1] for i in range(c0, c1 + 1)]
            fill = svg.grad(colors, horizontal=True, plateau=0.6)
            lay += box(x0, y, x1 - x0, g.row_h, fill, rx=4, title=title, sub=sub, size=g.f_comb,
                       sub_size=g.f_comb_sub)

    lay = svg.layer("stripes")
    yh = Y(g.y_head, g.h_head)
    for i, (name, color, ic) in enumerate(STRIPES):
        x = g.col_x(i)
        lay += box(x, yh, g.cw, g.h_head, svg.grad([PALETTE[color][2], PALETTE[color][3]]), rx=5)
        lay.append(icon(ic, x + g.cw / 2, yh + g.head_icon_dy, s=g.head_icon))
        lay.append(text(x + g.cw / 2, yh + g.head_label_dy, name, size=g.f_head, weight=700, fill="#fff",
                        spacing=0.6))

    lay = svg.layer("shared physics")
    yp = Y(g.y_phys, g.h_phys) + 3.0
    hp = g.h_phys - 6.0
    lay += box(g.xl, yp, g.xr - g.xl, hp, svg.grad([gr[1], gr[2]]), rx=6)
    lay.append(text(g.col_x(0) + g.cw / 2, yp + hp / 2 + g.f_band * 0.35, "SHARED PHYSICS", size=g.f_band,
                    weight=700, fill="#fff", spacing=0.9))
    for j, label in enumerate(PHYSICS, start=1):
        xd = g.col_x(j) - g.gap / 2
        lay.append(f'<path d="M{xd:.2f},{yp + 5:.2f} V{yp + hp - 5:.2f}" stroke="#fff" '
                   f'stroke-opacity="0.45" stroke-width="0.6"/>')
        lay.append(text(g.col_x(j) + g.cw / 2, yp + hp / 2 + g.f_phys * 0.35, label, size=g.f_phys, fill="#fff"))

    lay = svg.layer("core")
    core(svg, lay, g, Y(g.y_core, g.h_core))

    lay = svg.layer("foundations")
    yf = Y(g.y_found, g.h_found)
    lay += band(2.0, yf, W - 4.0, g.h_found, t["found"], "OPEN SOURCE FOUNDATIONS", rx=8,
                label_size=g.f_band, label_color=t["found_label"])
    for j, (title, sub) in enumerate(LIBRARIES):
        lay += box(g.col_x(j), yf + g.lib_dy, g.cw, g.lib_h, t["lib_fill"], rx=4, title=title, sub=sub,
                   size=g.f_lib, sub_size=g.f_lib_sub, fg=t["lib_fg"], stroke=t["lib_edge"])

    lay = svg.layer("logo")
    x0, x1 = g.col_x(3) + 4.0, g.xr - 4.0
    ya, yb = g.y_col_top + 5.0, g.row_y(5) - 6.0
    y0 = Y(ya, yb - ya)
    y1 = y0 + (yb - ya)
    bx, by, bw, bh = LOGO_BBOX
    sc = min((x1 - x0) / bw, (y1 - y0) / bh)
    tx = x0 + ((x1 - x0) - bw * sc) / 2
    ty = y0 + ((y1 - y0) - bh * sc) / 2
    lay.append(
        f'<g transform="translate({tx:.3f},{ty:.3f}) scale({sc:.5f}) translate({-bx:.4f},{-by:.4f})">'
        + logo_body(os.path.join(ASSETS, t["logo"])) + "</g>"
    )
    return svg


def core(svg, lay, g, y0):
    """The core band: automatic differentiation, Dataset, Vector, automatic serialization."""
    bk = PALETTE["black"]
    h = g.h_core
    lay += box(g.xl, y0, g.xr - g.xl, h, svg.grad([bk[1], bk[3]]), rx=7)
    cx_mid = (g.xl + g.xr) / 2
    x_cards = cx_mid - g.card_w - g.card_gap / 2
    x_right = x_cards + 2 * g.card_w + g.card_gap + g.side_gap
    side_w = x_cards - g.side_gap - g.xl
    ad_sub, ser_sub = CORE_SIDES
    for x, ic, title, sub in [(g.xl, "gradient", "Automatic differentiation", ad_sub),
                              (x_right, "archive", "Automatic serialization", ser_sub)]:
        lay.append(icon(ic, x + g.core_icon_dx, y0 + h / 2, s=g.core_icon))
        tx = x + g.core_text_dx + (side_w - g.core_text_dx - 2.0) / 2
        lay.append(text(tx, y0 + g.core_title_dy, title, size=g.f_core, weight=700, fill="#fff"))
        for i, line in enumerate(sub):
            lay.append(text(tx, y0 + g.core_sub_dy + g.core_sub_step * i, line, size=g.f_core_sub,
                            fill="#fff", opacity=0.9))
    for xd in (x_cards - g.side_gap / 2 - 0.5, cx_mid, x_right - g.side_gap / 2 + 0.5):
        lay.append(f'<path d="M{xd:.2f},{y0 + 12:.2f} V{y0 + h - 12:.2f}" stroke="#fff" '
                   f'stroke-opacity="0.25" stroke-width="0.6"/>')
    for j, (title, sub, glyph) in enumerate([("Dataset", "calibrated N-D arrays", dataset_glyph),
                                             ("Vector", "ragged data on a grid", vector_glyph)]):
        x = x_cards + j * (g.card_w + g.card_gap)
        y = y0 + 6.0
        lay.append(glyph(x + g.card_w / 2, y + g.glyph_dy, g.glyph))
        lay.append(text(x + g.card_w / 2, y + g.card_title_dy, title, size=g.f_core, weight=700, fill="#fff"))
        lay.append(text(x + g.card_w / 2, y + g.card_sub_dy, sub, size=g.f_core_sub, fill="#fff", opacity=0.9))


def dataset_glyph(cx, cy, s=1.0):
    """A stack of image frames with calibrated axes (sampling, units, origin)."""
    gr = PALETTE["gray"]
    fw, fh = 22.0 * s, 16.0 * s
    x0, y0 = cx - fw / 2 - 3.0 * s, cy - fh / 2 + 2.0 * s
    out = []
    for d in (6.0 * s, 3.0 * s):
        out.append(f'<rect x="{x0 + d:.2f}" y="{y0 - d:.2f}" width="{fw:.2f}" height="{fh:.2f}" rx="{s:.2f}" '
                   f'fill="{DARK}" stroke="{gr[0]}" stroke-width="0.6"/>')
    shades = ["#f1f3f5", "#ced4da", "#adb5bd", "#868e96", "#495057"]
    nx, ny = 5, 4
    cw, ch = fw / nx, fh / ny
    for i in range(nx):
        for j in range(ny):
            v = (i * 2 + j * 3 + (i * j) % 3) % len(shades)
            out.append(f'<rect x="{x0 + i * cw:.2f}" y="{y0 + j * ch:.2f}" width="{cw:.2f}" height="{ch:.2f}" fill="{shades[v]}"/>')
    out.append(f'<rect x="{x0:.2f}" y="{y0:.2f}" width="{fw:.2f}" height="{fh:.2f}" rx="{s:.2f}" fill="none" '
               f'stroke="#fff" stroke-width="0.6"/>')
    ya, xa = y0 + fh + 2.2 * s, x0 - 2.2 * s
    ticks = "".join(f" M{x0 + t * fw / 4:.2f},{ya:.2f} v{1.4 * s:.2f}" for t in range(5))
    ticks += "".join(f" M{xa:.2f},{y0 + t * fh / 4:.2f} h{-1.4 * s:.2f}" for t in range(5))
    out.append(f'<path d="M{x0:.2f},{ya:.2f} H{x0 + fw:.2f} M{xa:.2f},{y0:.2f} V{y0 + fh:.2f}{ticks}" '
               f'fill="none" stroke="#fff" stroke-width="{0.5 * max(1.0, s * 0.8):.2f}" stroke-linecap="round"/>')
    return "".join(out)


def vector_glyph(cx, cy, s=1.0):
    """A fixed grid of cells holding a variable number of entries (e.g. Bragg peaks)."""
    gr = PALETTE["gray"]
    n, cs, gp = 3, 7.6 * s, 1.2 * s
    tot = n * cs + (n - 1) * gp
    x0, y0 = cx - tot / 2, cy - tot / 2 + 0.5 * s
    pts = {
        (0, 0): [(0.3, 0.35), (0.7, 0.65)], (1, 0): [], (2, 0): [(0.5, 0.5)],
        (0, 1): [(0.25, 0.3), (0.7, 0.4), (0.45, 0.75)], (1, 1): [(0.55, 0.45)], (2, 1): [(0.3, 0.65), (0.72, 0.3)],
        (0, 2): [(0.6, 0.4)], (1, 2): [(0.3, 0.3), (0.7, 0.7)], (2, 2): [],
    }
    out = []
    for (i, j), dots in pts.items():
        x, y = x0 + i * (cs + gp), y0 + j * (cs + gp)
        out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{cs:.2f}" height="{cs:.2f}" rx="{s:.2f}" '
                   f'fill="{DARK}" stroke="{gr[0]}" stroke-width="0.5"/>')
        for u, v in dots:
            out.append(f'<circle cx="{x + u * cs:.2f}" cy="{y + v * cs:.2f}" r="{0.95 * s:.2f}" fill="#fff"/>')
    return "".join(out)


def logo_body(path):
    """Inner content of a logo SVG, with ids prefixed to avoid collisions."""
    src = open(path).read()
    inner = src[src.index(">", src.index("<svg")) + 1 : src.rindex("</svg>")]
    inner = re.sub(r'id="([^"]+)"', r'id="logo-\1"', inner)
    inner = re.sub(r'url\(#([^)]+)\)', r'url(#logo-\1)', inner)
    inner = re.sub(r'href="#([^"]+)"', r'href="#logo-\1"', inner)
    return inner


if __name__ == "__main__":
    for theme in THEMES:
        build(theme).write(os.path.join(ASSETS, f"architecture-{theme}.svg"))
