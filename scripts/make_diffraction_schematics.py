"""Generate the schematics at the top of the diffraction user guide pages.

Each schematic is written in a light and a dark variant, which the pages
switch between with the qem-only-light / qem-only-dark classes:

    python scripts/make_diffraction_schematics.py

writes assets/diffraction/schematic-<name>-{light,dark}.svg. The colors are
the quantEM logo palette, with gold and cyan for the alpha and beta phases
as in the orientation mapping figures.
"""

import math
import os
import random

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, "..", "assets", "diffraction"))

W, H = 1100, 330  # shared canvas, so text renders at one size on every page
P = 170  # panel size
TOP = 72  # panel top
FONT = "'Source Sans 3', 'Source Sans Pro', -apple-system, 'Segoe UI', Helvetica, Arial, sans-serif"

THEMES = {
    "light": dict(
        ink="#1A1A1A", muted="#5F6368", tint="#000000", tint_op=0.035, edge_op=0.10,
        red="#CC0202", blue="#0A85CE", navy="#003F7F", cyan="#05B5E6", green="#00A800",
        gold="#F2B705", grid="#000000", grid_op=0.10, det="#0D1117", det_edge="#0D1117",
    ),
    "dark": dict(
        ink="#F2F2F2", muted="#A9AEB5", tint="#FFFFFF", tint_op=0.06, edge_op=0.16,
        red="#E85149", blue="#3AA0E0", navy="#8DB8E8", cyan="#2CC4EE", green="#2BD12B",
        gold="#F5C542", grid="#FFFFFF", grid_op=0.14, det="#05080C", det_edge="#3A3F46",
    ),
}


# ---------------------------------------------------------------- primitives


class Svg:
    def __init__(self, t, label, h=H):
        self.t = t
        self.parts = []
        self.label = label
        self.h = h

    def add(self, s):
        self.parts.append(s)

    def text(self, x, y, s, size=18, color=None, anchor="middle", weight=400, italic=False):
        color = color or self.t["ink"]
        style = ' font-style="italic"' if italic else ""
        self.add(
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{style}>{s}</text>'
        )

    def panel(self, x, y, w=P, h=P, r=12):
        t = self.t
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{t["tint"]}" '
            f'fill-opacity="{t["tint_op"]}" stroke="{t["tint"]}" stroke-opacity="{t["edge_op"]}"/>'
        )

    def detector(self, x, y, w=P, h=P, r=12):
        t = self.t
        self.add(
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{t["det"]}" '
            f'stroke="{t["det_edge"]}"/>'
        )

    def title(self, cx, s, step=None, top=TOP):
        """Panel title centered above a panel, with an optional red step badge."""
        y = top - 22
        if step is None:
            self.text(cx, y, s, size=21, weight=600)
            return
        width = 0.5 * 21 * len(s)  # rough text width
        bx = cx - width / 2 - 16
        self.add(f'<circle cx="{bx:.1f}" cy="{y - 7:.1f}" r="12" fill="{self.t["red"]}"/>')
        self.text(bx, y - 1, str(step), size=16, color="#FFFFFF", weight=700)
        self.text(bx + 18, y, s, size=21, weight=600, anchor="start")

    def caption(self, cx, lines, top=TOP, size=P):
        for i, s in enumerate(lines):
            self.text(cx, top + size + 30 + 22 * i, s, size=18, color=self.t["muted"])

    def arrow(self, x1, y1, x2, y2, label=None, color=None, width=2.5, head=10):
        color = color or self.t["muted"]
        ang = math.atan2(y2 - y1, x2 - x1)
        bx, by = x2 - head * math.cos(ang), y2 - head * math.sin(ang)
        self.add(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{bx:.1f}" y2="{by:.1f}" stroke="{color}" '
            f'stroke-width="{width}" stroke-linecap="round"/>'
        )
        px, py = -math.sin(ang), math.cos(ang)
        pts = [
            (x2, y2),
            (bx + 0.55 * head * px, by + 0.55 * head * py),
            (bx - 0.55 * head * px, by - 0.55 * head * py),
        ]
        self.add(
            '<polygon points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts) + f'" fill="{color}"/>'
        )
        if label:
            self.text((x1 + x2) / 2, min(y1, y2) - 12, label, size=17, color=color)

    def symbol(self, cx, cy, s, size=40):
        self.text(cx, cy + size * 0.35, s, size=size, color=self.t["muted"], weight=300)

    def star(self, cx, cy, r=13):
        """The correlation operator, a five-pointed star."""
        pts = []
        for k in range(10):
            a = -math.pi / 2 + k * math.pi / 5
            rr = r if k % 2 == 0 else 0.45 * r
            pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a)))
        self.add(
            '<polygon points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
            + f'" fill="{self.t["muted"]}"/>'
        )

    def tag(self, x, y, s):
        """A small label in the corner of a panel."""
        self.text(x, y, s, size=15, color=self.t["muted"], anchor="start")

    def write(self, name, theme):
        defs = (
            "<defs>"
            '<radialGradient id="spot"><stop offset="0" stop-color="#FFFFFF"/>'
            '<stop offset="0.45" stop-color="#FFFFFF" stop-opacity="0.85"/>'
            '<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="halo"><stop offset="0" stop-color="#9FB7CC" stop-opacity="0.55"/>'
            '<stop offset="1" stop-color="#9FB7CC" stop-opacity="0"/></radialGradient>'
            '<radialGradient id="disk"><stop offset="0" stop-color="#FFFFFF"/>'
            '<stop offset="0.7" stop-color="#FFFFFF"/>'
            '<stop offset="1" stop-color="#FFFFFF" stop-opacity="0"/></radialGradient>'
            "</defs>"
        )
        svg = (
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {self.h}" role="img" '
            f'aria-label="{self.label}" font-family="{FONT}">'
            + defs
            + "".join(self.parts)
            + "</svg>\n"
        )
        path = os.path.join(OUT, f"schematic-{name}-{theme}.svg")
        with open(path, "w") as f:
            f.write(svg)


def panel_xs(n, size=P, margin=25):
    gap = (W - 2 * margin - n * size) / (n - 1)
    return [margin + i * (size + gap) for i in range(n)], gap


# ------------------------------------------------------- diffraction motifs


def hex_spots(scale=24.0, angle_deg=12.0, k_max=3.3, laue=(0.35, -0.2)):
    """Spot positions (unit: pixels from the pattern center) and intensities
    for a hexagonal zone axis pattern, with intensity falling off with |g|
    and with distance from a slightly off-center Laue circle."""
    a = math.radians(angle_deg)
    g1 = (math.cos(a), math.sin(a))
    g2 = (math.cos(a + math.pi / 3), math.sin(a + math.pi / 3))
    spots = []
    for i in range(-5, 6):
        for j in range(-5, 6):
            gx = i * g1[0] + j * g2[0]
            gy = i * g1[1] + j * g2[1]
            g = math.hypot(gx, gy)
            if g == 0 or g > k_max:
                continue
            excite = math.exp(-((gx - laue[0]) ** 2 + (gy - laue[1]) ** 2) / 9.0)
            inten = excite * math.exp(-g / 1.6) * (0.75 + 0.25 * ((i - j) % 3 == 0))
            spots.append((gx * scale, gy * scale, inten, g))
    return spots


def draw_pattern(svg, x, y, spots, size=P, halo=True, sharp=False, rings=None):
    """A diffraction pattern on a dark detector."""
    cx, cy = x + size / 2, y + size / 2
    svg.detector(x, y, size, size)
    if halo:
        svg.add(f'<circle cx="{cx}" cy="{cy}" r="{size * 0.33:.1f}" fill="url(#halo)"/>')
    imax = max(s[2] for s in spots)
    for sx, sy, inten, _ in spots:
        if abs(sx) > size / 2 - 7 or abs(sy) > size / 2 - 7:
            continue
        rel = inten / imax
        if rel < 0.04:
            continue
        r = (2.2 + 4.8 * math.sqrt(rel)) if not sharp else (1.6 + 3.0 * math.sqrt(rel))
        op = min(1.0, 0.35 + 0.9 * math.sqrt(rel))
        svg.add(
            f'<circle cx="{cx + sx:.1f}" cy="{cy + sy:.1f}" r="{r:.1f}" fill="url(#spot)" '
            f'fill-opacity="{op:.2f}"/>'
        )
    svg.add(
        f'<circle cx="{cx}" cy="{cy}" r="{8.5 if not sharp else 4.5}" fill="url(#spot)"/>'
    )


def lath_field(nx, ny, seed=3):
    """Phase and orientation labels on an nx x ny grid: alpha laths (rotated
    ellipses, each its own orientation) in a beta matrix."""
    laths = [
        (0.30, 0.30, 0.42, 0.09, 70, 0),
        (0.72, 0.45, 0.48, 0.10, -35, 1),
        (0.25, 0.78, 0.30, 0.08, 20, 2),
        (0.62, 0.86, 0.36, 0.08, 10, 0),
        (0.82, 0.12, 0.24, 0.07, 80, 2),
    ]
    out = []
    for j in range(ny):
        row = []
        for i in range(nx):
            u, v = (i + 0.5) / nx, (j + 0.5) / ny
            lab = -1
            for k, (cx, cy, a, b, ang, var) in enumerate(laths):
                c, s = math.cos(math.radians(ang)), math.sin(math.radians(ang))
                du, dv = u - cx, v - cy
                p, q = du * c + dv * s, -du * s + dv * c
                if (p / a) ** 2 + (q / b) ** 2 < 1:
                    lab = var
            row.append(lab)
        out.append(row)
    return out


def draw_map(svg, x, y, field, colors, size=P, highlight=None, gap=0.8):
    ny, nx = len(field), len(field[0])
    c = size / nx
    svg.add(
        f'<clipPath id="mapclip{int(x)}"><rect x="{x}" y="{y}" width="{size}" height="{size}" rx="12"/></clipPath>'
    )
    svg.add(f'<g clip-path="url(#mapclip{int(x)})">')
    for j in range(ny):
        for i in range(nx):
            col = colors(field[j][i], i, j)
            svg.add(
                f'<rect x="{x + i * c:.2f}" y="{y + j * c:.2f}" width="{c - gap:.2f}" '
                f'height="{c - gap:.2f}" fill="{col}"/>'
            )
    svg.add("</g>")
    if highlight:
        i, j = highlight
        svg.add(
            f'<rect x="{x + i * c - 1.5:.1f}" y="{y + j * c - 1.5:.1f}" width="{c + 2.2:.1f}" '
            f'height="{c + 2.2:.1f}" fill="none" stroke="{svg.t["red"]}" stroke-width="3"/>'
        )
    return c


def mix(c1, c2, f):
    a = [int(c1[k : k + 2], 16) for k in (1, 3, 5)]
    b = [int(c2[k : k + 2], 16) for k in (1, 3, 5)]
    return "#" + "".join(f"{round(a[k] + (b[k] - a[k]) * f):02X}" for k in range(3))


def ipf_color(u, v, w):
    """Inverse pole figure color: red, blue, green at the three corners."""
    m = max(u, v, w)
    r, g, b = u / m, w / m, v / m
    return "#" + "".join(f"{round(255 * (0.15 + 0.85 * c)):02X}" for c in (r, g, b))


ALPHA_VARIANTS = ["#F2B705", "#E8890C", "#F6D55C"]


# -------------------------------------------------------------- schematics


def acom_workflow(t):
    svg = Svg(
        t,
        "Orientation and phase mapping workflow: a diffraction pattern recorded at every probe "
        "position, Bragg disk detection, calibration against known rings, matching to simulated "
        "patterns, and the resulting phase and orientation map",
    )
    xs, gap = panel_xs(5, size=160)
    s = 160
    field = lath_field(14, 14)
    hi = (4, 4)

    # 0: 4D-STEM scan, one pattern per probe position
    svg.title(xs[0] + s / 2, "4D-STEM scan")
    draw_map(
        svg, xs[0], TOP, field,
        lambda lab, i, j: mix("#3A4350", "#C9D2DC", 0.75 if lab >= 0 else 0.35 + 0.05 * ((i + j) % 2)),
        size=s, highlight=hi,
    )
    svg.caption(xs[0] + s / 2, ["one diffraction pattern", "per probe position"])

    # 1: disk detection
    spots = hex_spots(scale=22.0)
    svg.title(xs[1] + s / 2, "Detect disks", step=1)
    draw_pattern(svg, xs[1], TOP, spots, size=s)
    cx, cy = xs[1] + s / 2, TOP + s / 2
    imax = max(sp[2] for sp in spots)
    for sx, sy, inten, _ in spots:
        if inten / imax > 0.12 and abs(sx) < s / 2 - 10 and abs(sy) < s / 2 - 10:
            svg.add(
                f'<circle cx="{cx + sx:.1f}" cy="{cy + sy:.1f}" r="7.5" fill="none" '
                f'stroke="{t["red"]}" stroke-width="1.8"/>'
            )
    svg.caption(xs[1] + s / 2, ["peak positions", "and intensities"])

    # 2: calibration, peaks on reference rings
    svg.title(xs[2] + s / 2, "Calibrate", step=2)
    svg.panel(xs[2], TOP, s, s)
    cx, cy = xs[2] + s / 2, TOP + s / 2
    shells = sorted({round(sp[3], 3) for sp in spots})[:4]
    for g in shells:
        svg.add(
            f'<circle cx="{cx}" cy="{cy}" r="{g * 22:.1f}" fill="none" stroke="{t["blue"]}" '
            f'stroke-width="1.5" stroke-dasharray="4 4"/>'
        )
    for sx, sy, inten, g in spots:
        if inten / imax > 0.12 and g <= shells[-1] + 1e-3:
            svg.add(f'<circle cx="{cx + sx:.1f}" cy="{cy + sy:.1f}" r="3.6" fill="{t["ink"]}"/>')
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{t["ink"]}"/>')
    svg.caption(xs[2] + s / 2, ["centered, in Å⁻¹,", "distortion removed"])

    # 3: matching, a simulated pattern over the measured peaks
    svg.title(xs[3] + s / 2, "Match", step=3)
    svg.panel(xs[3], TOP, s, s)
    cx, cy = xs[3] + s / 2, TOP + s / 2
    for sx, sy, inten, g in spots:
        if inten / imax > 0.12 and abs(sx) < s / 2 - 12 and abs(sy) < s / 2 - 12:
            svg.add(f'<circle cx="{cx + sx:.1f}" cy="{cy + sy:.1f}" r="4.2" fill="{t["ink"]}"/>')
    for sx, sy, inten, g in spots:
        if inten / imax > 0.08 and abs(sx) < s / 2 - 12 and abs(sy) < s / 2 - 12:
            svg.add(
                f'<path d="M{cx + sx - 8:.1f},{cy + sy:.1f}h5M{cx + sx + 3:.1f},{cy + sy:.1f}h5'
                f'M{cx + sx:.1f},{cy + sy - 8:.1f}v5M{cx + sx:.1f},{cy + sy + 3:.1f}v5" '
                f'stroke="{t["gold"]}" stroke-width="2.2" stroke-linecap="round"/>'
            )
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{t["ink"]}"/>')
    svg.caption(xs[3] + s / 2, ["to simulated patterns", "of each phase"])

    # 4: maps
    svg.title(xs[4] + s / 2, "Maps")

    def colors(lab, i, j):
        return t["cyan"] if lab < 0 else ALPHA_VARIANTS[lab]

    draw_map(svg, xs[4], TOP, field, colors, size=s, highlight=hi)
    svg.caption(xs[4] + s / 2, ["phase and orientation", "maps"])

    y = TOP + s / 2
    for k in range(4):
        svg.arrow(xs[k] + s + 10, y, xs[k + 1] - 10, y, label=None)
    return svg


def disk_detection(t):
    svg = Svg(
        t,
        "Bragg disk detection: the diffraction pattern is cross-correlated with a template of a "
        "single disk, the correlation has sharp maxima at the disk centers, and the maxima are "
        "refined to subpixel peak positions and intensities",
    )
    xs = [25, 290, 495, 905]
    spots = hex_spots(scale=24.0)
    y = TOP + P / 2

    svg.title(xs[0] + P / 2, "Diffraction pattern")
    draw_pattern(svg, xs[0], TOP, spots)
    svg.caption(xs[0] + P / 2, ["one probe position"])

    # template, a smaller tile
    ts = 100
    tx, ty = xs[1], TOP + (P - ts) / 2
    svg.title(tx + ts / 2, "Template")
    svg.detector(tx, ty, ts, ts, r=10)
    svg.add(f'<circle cx="{tx + ts / 2}" cy="{ty + ts / 2}" r="15" fill="url(#disk)"/>')
    svg.caption(tx + ts / 2, ["probe image or", "synthetic disk"])

    svg.title(xs[2] + P / 2, "Correlation")
    draw_pattern(svg, xs[2], TOP, spots, halo=False, sharp=True)
    svg.caption(xs[2] + P / 2, ["sharp maxima at", "every disk center"])

    # subpixel refinement of one maximum, between the panels
    zc = 21
    zx, zy = (xs[2] + P + xs[3]) / 2 - 1.5 * zc, TOP + 2
    vals = [[0.30, 0.62, 0.36], [0.55, 1.0, 0.74], [0.22, 0.52, 0.40]]
    for j in range(3):
        for i in range(3):
            svg.add(
                f'<rect x="{zx + i * zc:.1f}" y="{zy + j * zc:.1f}" width="{zc - 1.5}" height="{zc - 1.5}" '
                f'fill="{mix(t["det"], "#FFFFFF", vals[j][i])}"/>'
            )
    mx, my = zx + 1.5 * zc + 5, zy + 1.5 * zc + 2
    svg.add(
        f'<path d="M{mx - 7:.1f},{my:.1f}h14M{mx:.1f},{my - 7:.1f}v14" stroke="{t["red"]}" stroke-width="2.6"/>'
    )
    svg.text(zx + 1.5 * zc, zy + 3 * zc + 20, "subpixel", size=15, color=t["red"])
    svg.arrow(xs[2] + P + 12, y + 22, xs[3] - 12, y + 22, color=t["muted"])

    # detected peaks
    svg.title(xs[3] + P / 2, "Detected peaks")
    svg.panel(xs[3], TOP)
    cx, cy = xs[3] + P / 2, TOP + P / 2
    imax = max(s[2] for s in spots)
    for sx, sy, inten, _ in spots:
        rel = inten / imax
        if rel < 0.06 or abs(sx) > P / 2 - 8 or abs(sy) > P / 2 - 8:
            continue
        svg.add(
            f'<circle cx="{cx + sx:.1f}" cy="{cy + sy:.1f}" r="{1.6 + 3.2 * math.sqrt(rel):.1f}" fill="{t["ink"]}"/>'
        )
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="5" fill="{t["ink"]}"/>')
    svg.caption(xs[3] + P / 2, ["q_row, q_col, intensity", "at every position"])

    svg.star((xs[0] + P + xs[1]) / 2, y, r=14)
    svg.symbol((xs[1] + ts + xs[2]) / 2, y, "=", size=44)
    return svg


def descan_grid(svg, x, y, size=P, n=6):
    """Direct beam position over the scan, on a plane-fit color ramp."""
    t = svg.t
    c = size / n
    svg.add(f'<clipPath id="descan{int(x)}_{int(y)}"><rect x="{x}" y="{y}" width="{size}" height="{size}" rx="12"/></clipPath>')
    svg.add(f'<g clip-path="url(#descan{int(x)}_{int(y)})">')
    for j in range(n):
        for i in range(n):
            f = (i + 0.6 * j) / (n - 1 + 0.6 * (n - 1))
            col = mix(mix(t["blue"], "#FFFFFF", 0.55), mix(t["red"], "#FFFFFF", 0.55), f)
            svg.add(
                f'<rect x="{x + i * c:.1f}" y="{y + j * c:.1f}" width="{c - 1.5:.1f}" '
                f'height="{c - 1.5:.1f}" fill="{col}" fill-opacity="0.9"/>'
            )
            ccx, ccy = x + (i + 0.5) * c, y + (j + 0.5) * c
            svg.add(
                f'<path d="M{ccx - 7:.1f},{ccy:.1f}h14M{ccx:.1f},{ccy - 7:.1f}v14" stroke="#1A1A1A" '
                f'stroke-opacity="0.35" stroke-width="1.2"/>'
            )
            svg.add(
                f'<circle cx="{ccx + (i - 2.5) * 2.2:.1f}" cy="{ccy + (j - 2.5) * 1.4:.1f}" r="3.4" fill="#1A1A1A"/>'
            )
    svg.add("</g>")


def ring_dots(svg, x, y, size, spots, shells, stretch=1.0, squash=0.0, scale=24.0, rings=True):
    """Peaks over dashed reference rings, optionally scaled and elliptically distorted."""
    t = svg.t
    cx, cy = x + size / 2, y + size / 2
    if rings:
        for g in shells:
            svg.add(
                f'<circle cx="{cx}" cy="{cy}" r="{g * scale:.1f}" fill="none" stroke="{t["blue"]}" '
                f'stroke-width="1.6" stroke-dasharray="4 4"/>'
            )
    imax = max(sp[2] for sp in spots)
    a = math.radians(30)
    for sx, sy, inten, g in spots:
        if g > shells[-1] + 1e-3:
            continue
        p = sx * math.cos(a) + sy * math.sin(a)
        q = -sx * math.sin(a) + sy * math.cos(a)
        p, q = p * stretch * (1 + squash), q * stretch * (1 - squash)
        mx = p * math.cos(a) - q * math.sin(a)
        my = p * math.sin(a) + q * math.cos(a)
        r = 2.4 + 2.4 * math.sqrt(inten / imax)
        svg.add(f'<circle cx="{cx + mx:.1f}" cy="{cy + my:.1f}" r="{r:.1f}" fill="{t["ink"]}"/>')
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="4.5" fill="{t["ink"]}"/>')


def ring_check_plot(svg, x, y, size=P):
    """Per-ring scale factor against ring radius: flat inside a band, with a trend for contrast."""
    t = svg.t
    svg.panel(x, y, size, size)
    x0, x1 = x + 34, x + size - 14
    y0, y1 = y + 22, y + size - 34
    ym = (y0 + y1) / 2
    band = 14
    svg.add(f'<rect x="{x0}" y="{ym - band}" width="{x1 - x0}" height="{2 * band}" fill="{t["green"]}" fill-opacity="0.16"/>')
    svg.add(f'<line x1="{x0}" y1="{ym}" x2="{x1}" y2="{ym}" stroke="{t["green"]}" stroke-width="1.5"/>')
    svg.add(
        f'<line x1="{x0}" y1="{ym + 34}" x2="{x1}" y2="{ym - 40}" stroke="{t["red"]}" '
        f'stroke-width="1.8" stroke-dasharray="5 4"/>'
    )
    rnd = random.Random(4)
    for k in range(9):
        px = x0 + 10 + k * (x1 - x0 - 20) / 8
        svg.add(f'<circle cx="{px:.1f}" cy="{ym + rnd.uniform(-7, 7):.1f}" r="4" fill="{t["ink"]}"/>')
    svg.add(f'<line x1="{x0}" y1="{y0}" x2="{x0}" y2="{y1}" stroke="{t["muted"]}" stroke-width="1.5"/>')
    svg.add(f'<line x1="{x0}" y1="{y1}" x2="{x1}" y2="{y1}" stroke="{t["muted"]}" stroke-width="1.5"/>')
    svg.text(x0 - 10, ym + 6, "1.00", size=14, color=t["muted"], anchor="end")
    svg.text((x0 + x1) / 2, y1 + 22, "ring radius k", size=15, color=t["muted"])
    svg.text(x1 - 2, ym - 44, "trend", size=14, color=t["red"], anchor="end")


def frames(svg, cx, cy, theta_deg, length=46):
    """Scan axes (muted) and detector axes rotated by theta (red), with the angle arc."""
    t = svg.t
    svg.arrow(cx, cy, cx + length, cy, color=t["muted"], width=2.2, head=9)
    svg.arrow(cx, cy, cx, cy + length, color=t["muted"], width=2.2, head=9)
    svg.text(cx + length + 4, cy + 18, "c", size=15, color=t["muted"], anchor="start", italic=True)
    svg.text(cx - 6, cy + length + 4, "r", size=15, color=t["muted"], anchor="end", italic=True)
    a = math.radians(-theta_deg)  # counterclockwise on screen
    ex = (math.cos(a), math.sin(a))
    ey = (-math.sin(a), math.cos(a))
    svg.arrow(cx, cy, cx + length * ex[0], cy + length * ex[1], color=t["red"], width=2.4, head=9)
    svg.arrow(cx, cy, cx + length * ey[0], cy + length * ey[1], color=t["red"], width=2.4, head=9)
    rr = 26
    pts = [(cx + rr * math.cos(-math.radians(k)), cy + rr * math.sin(-math.radians(k))) for k in range(0, int(theta_deg) + 1, 3)]
    svg.add(
        '<polyline points="' + " ".join(f"{a_:.1f},{b_:.1f}" for a_, b_ in pts)
        + f'" fill="none" stroke="{t["red"]}" stroke-width="1.6"/>'
    )
    mid = -math.radians(theta_deg / 2)
    svg.text(cx + (rr + 10) * math.cos(mid) + 2, cy + (rr + 10) * math.sin(mid) + 6, "θ", size=17,
             color=t["red"], anchor="start", italic=True)


def com_field(svg, x, y, size, theta_deg, n=8):
    """Center-of-mass vectors over the scan: the gradient of a few potential
    bumps, rotated by theta. At theta = 0 the field is curl free."""
    t = svg.t
    bumps = [(0.5, 0.5, 1.0)]
    a = math.radians(theta_deg)
    c = size / n
    for j in range(n):
        for i in range(n):
            u, v = (i + 0.5) / n, (j + 0.5) / n
            gx = gy = 0.0
            for bx, by, amp in bumps:
                w = amp * math.exp(-((u - bx) ** 2 + (v - by) ** 2) / (2 * 0.30**2))
                gx += -(u - bx) * w
                gy += -(v - by) * w
            rx = gx * math.cos(a) - gy * math.sin(a)
            ry = gx * math.sin(a) + gy * math.cos(a)
            mag = math.hypot(rx, ry)
            if mag < 1e-6:
                continue
            L = min(0.42 * c, 0.42 * c * mag / 0.10)
            x0, y0 = x + (i + 0.5) * c, y + (j + 0.5) * c
            if L < 3:
                svg.add(f'<circle cx="{x0:.1f}" cy="{y0:.1f}" r="1.4" fill="{t["ink"]}"/>')
                continue
            dx, dy = rx / mag * L, ry / mag * L
            svg.arrow(x0 - dx, y0 - dy, x0 + dx, y0 + dy, color=t["ink"], width=1.6, head=5)


def grain_field(nx, ny, seeds, seed=7):
    """Nearest-seed grain labels on an nx x ny grid."""
    out = []
    for j in range(ny):
        row = []
        for i in range(nx):
            u, v = (i + 0.5) / nx, (j + 0.5) / ny
            row.append(min(range(len(seeds)), key=lambda k: (u - seeds[k][0]) ** 2 + (v - seeds[k][1]) ** 2))
        out.append(row)
    return out


def calibration(t):
    svg = Svg(
        t,
        "Calibration in four steps: a plane fit to the direct beam position removes the descan, "
        "the curl of the center-of-mass field gives the detector-to-scan rotation, the pixel size "
        "and elliptic distortion are fit to the rings or spots of known phases, and every ring "
        "and phase is checked",
    )
    xs, gap = panel_xs(4)
    y = TOP + P / 2

    svg.title(xs[0] + P / 2, "Remove descan", step=1)
    descan_grid(svg, xs[0], TOP)
    svg.caption(xs[0] + P / 2, ["plane fit to the", "direct beam position"])

    svg.title(xs[1] + P / 2, "Scan rotation", step=2)
    svg.panel(xs[1], TOP)
    frames(svg, xs[1] + 52, TOP + 52, 34, length=70)
    svg.caption(xs[1] + P / 2, ["detector axes", "relative to the scan"])

    spots = hex_spots(scale=24.0)
    shells = sorted({round(sp[3], 3) for sp in spots})[:4]
    svg.title(xs[2] + P / 2, "Scale and ellipse", step=3)
    svg.panel(xs[2], TOP)
    ring_dots(svg, xs[2], TOP, P, spots, shells)
    svg.caption(xs[2] + P / 2, ["fit to the rings or", "spots of known phases"])

    svg.title(xs[3] + P / 2, "Check", step=4)
    ring_check_plot(svg, xs[3], TOP)
    svg.caption(xs[3] + P / 2, ["every ring and", "every phase"])

    for k in range(3):
        svg.arrow(xs[k] + P + 12, y, xs[k + 1] - 12, y)
    return svg


def calibration_routes(t):
    svg = Svg(
        t,
        "Two routes to the pixel size and ellipse. calibrate, for many orientations, matches the "
        "maxima of the radial peak histogram to the allowed ring radii by position only. "
        "calibrate_2d, for one dominant orientation, sums the peaks into a 2D spot pattern, "
        "indexes it, and fits a 2 by 2 distortion to the paired spots",
        h=620,
    )
    s = 150
    x0 = 255
    xs = [x0 + k * (s + 72) for k in range(4)]
    rows = [TOP, TOP + 300]
    rnd = random.Random(11)

    # row labels
    for top, name, sub in [
        (rows[0], "calibrate()", ["many orientations:", "polycrystals, textures"]),
        (rows[1], "calibrate_2d()", ["one dominant orientation:", "a single crystal or grain"]),
    ]:
        svg.text(25, top + s / 2 - 12, name, size=23, weight=700, anchor="start")
        for k, line in enumerate(sub):
            svg.text(25, top + s / 2 + 16 + 22 * k, line, size=17, color=t["muted"], anchor="start")

    # ---- row 1: rings
    top = rows[0]
    seeds = [(rnd.random(), rnd.random()) for _ in range(16)]
    grains = grain_field(12, 12, seeds)
    palette = [ipf_color(rnd.random() + 0.1, rnd.random() + 0.1, rnd.random() + 0.1) for _ in seeds]
    svg.title(xs[0] + s / 2, "Many grains", top=top)
    draw_map(svg, xs[0], top, grains, lambda lab, i, j: palette[lab], size=s)
    svg.caption(xs[0] + s / 2, ["random or", "fiber texture"], top=top, size=s)

    svg.title(xs[1] + s / 2, "All peaks", top=top)
    svg.detector(xs[1], top, s, s)
    cx, cy = xs[1] + s / 2, top + s / 2
    ring_r = [26, 45, 52, 70]
    for r in ring_r:
        for _ in range(int(r / 2.4)):
            a = rnd.uniform(0, 2 * math.pi)
            rr = r + rnd.gauss(0, 0.8)
            svg.add(f'<circle cx="{cx + rr * math.cos(a):.1f}" cy="{cy + rr * math.sin(a):.1f}" r="2.1" fill="#FFFFFF" fill-opacity="0.85"/>')
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="6" fill="url(#spot)"/>')
    svg.caption(xs[1] + s / 2, ["peaks from every", "position, on rings"], top=top, size=s)

    svg.title(xs[2] + s / 2, "Radial histogram", top=top)
    svg.panel(xs[2], top, s, s)
    hx0, hx1 = xs[2] + 12, xs[2] + s - 12
    hy1 = top + s - 26
    kmax = 80.0
    pts = []
    heights = [1.0, 0.45, 0.8, 0.35]
    for k in range(121):
        r = k / 120 * kmax
        val = sum(hh * math.exp(-((r - rp) / 1.8) ** 2) for rp, hh in zip(ring_r, heights))
        pts.append((hx0 + r / kmax * (hx1 - hx0), hy1 - 92 * val))
    allowed = [26, 37, 45, 52, 64, 70]  # one allowed ring is absent from the data
    for rp in allowed:
        xx = hx0 + rp / kmax * (hx1 - hx0)
        svg.add(f'<line x1="{xx:.1f}" y1="{top + 14}" x2="{xx:.1f}" y2="{hy1}" stroke="{t["blue"]}" stroke-width="1.6" stroke-dasharray="4 3"/>')
    svg.add(
        '<polyline points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        + f'" fill="none" stroke="{t["red"]}" stroke-width="2.2" stroke-linejoin="round"/>'
    )
    for rp, hh in zip(ring_r, heights):
        xx = hx0 + rp / kmax * (hx1 - hx0)
        svg.add(f'<circle cx="{xx:.1f}" cy="{hy1 - 92 * hh:.1f}" r="4" fill="{t["red"]}"/>')
    svg.add(f'<line x1="{hx0}" y1="{hy1}" x2="{hx1}" y2="{hy1}" stroke="{t["muted"]}" stroke-width="1.5"/>')
    svg.text((hx0 + hx1) / 2, hy1 + 19, "|q|", size=15, color=t["muted"], italic=True)
    svg.caption(xs[2] + s / 2, ["maxima on allowed rings,", "by position only"], top=top, size=s)

    spots = hex_spots(scale=21.0)
    shells = sorted({round(sp[3], 3) for sp in spots})[:4]
    svg.title(xs[3] + s / 2, "Scale and ellipse", top=top)
    svg.panel(xs[3], top, s, s)
    ring_dots(svg, xs[3], top, s, spots, shells, scale=21.0)
    svg.caption(xs[3] + s / 2, ["every ring checked", "separately"], top=top, size=s)

    # ---- row 2: spots
    top = rows[1]
    one = grain_field(12, 12, [(0.5, 0.5), (0.08, 0.92)])
    svg.title(xs[0] + s / 2, "One grain", top=top)
    draw_map(svg, xs[0], top, one, lambda lab, i, j: t["cyan"] if lab == 0 else t["gold"], size=s)
    svg.caption(xs[0] + s / 2, ["one orientation", "dominates"], top=top, size=s)

    svg.title(xs[1] + s / 2, "Summed peaks", top=top)
    svg.detector(xs[1], top, s, s)
    cx, cy = xs[1] + s / 2, top + s / 2
    lat = hex_spots(scale=21.0, angle_deg=20.0)
    imax = max(sp[2] for sp in lat)
    meas = []
    for sx, sy, inten, g in lat:
        if abs(sx) > s / 2 - 10 or abs(sy) > s / 2 - 10 or inten / imax < 0.05:
            continue
        mx, my = sx * 1.035 + 0.03 * sy, sy * 0.975 + 0.03 * sx  # detector distortion
        meas.append((sx, sy, mx, my, inten))
        svg.add(f'<circle cx="{cx + mx:.1f}" cy="{cy + my:.1f}" r="{2.5 + 3 * math.sqrt(inten / imax):.1f}" fill="#FF5A4E"/>')
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="6" fill="url(#spot)"/>')
    svg.caption(xs[1] + s / 2, ["one sharp spot", "pattern in 2D"], top=top, size=s)

    svg.title(xs[2] + s / 2, "Index and pair", top=top)
    svg.panel(xs[2], top, s, s)
    cx, cy = xs[2] + s / 2, top + s / 2
    for sx, sy, mx, my, inten in meas:
        svg.add(f'<line x1="{cx + sx:.1f}" y1="{cy + sy:.1f}" x2="{cx + mx:.1f}" y2="{cy + my:.1f}" stroke="{t["muted"]}" stroke-width="1.2"/>')
        svg.add(f'<circle cx="{cx + mx:.1f}" cy="{cy + my:.1f}" r="3.2" fill="{t["red"]}"/>')
        svg.add(f'<circle cx="{cx + sx:.1f}" cy="{cy + sy:.1f}" r="5.2" fill="none" stroke="{t["ink"]}" stroke-width="1.6"/>')
    svg.caption(xs[2] + s / 2, ["measured spots paired", "with simulated spots"], top=top, size=s)

    svg.title(xs[3] + s / 2, "Fit q = M p", top=top)
    svg.panel(xs[3], top, s, s)
    cx, cy = xs[3] + s / 2, top + s / 2 - 8
    d = 40
    svg.add(
        f'<polygon points="{cx - d * 1.06 - 6:.1f},{cy - d * 0.95 + 4:.1f} {cx + d * 1.06 - 6:.1f},{cy - d * 0.95 - 4:.1f} '
        f'{cx + d * 1.06 + 6:.1f},{cy + d * 0.95 - 4:.1f} {cx - d * 1.06 + 6:.1f},{cy + d * 0.95 + 4:.1f}" '
        f'fill="none" stroke="{t["red"]}" stroke-width="1.8" stroke-dasharray="5 4"/>'
    )
    svg.add(f'<rect x="{cx - d}" y="{cy - d}" width="{2 * d}" height="{2 * d}" fill="none" stroke="{t["ink"]}" stroke-width="2"/>')
    svg.text(cx, top + s - 14, "P = √(MᵀM)", size=17, color=t["ink"])
    svg.caption(xs[3] + s / 2, ["pixel size and ellipse", "from the symmetric part"], top=top, size=s)

    for top in rows:
        yy = top + s / 2
        for k in range(3):
            svg.arrow(xs[k] + s + 12, yy, xs[k + 1] - 12, yy)
    svg.add(
        f'<line x1="25" y1="{rows[1] - 52}" x2="{W - 25}" y2="{rows[1] - 52}" stroke="{t["tint"]}" '
        f'stroke-opacity="{t["edge_op"]}" stroke-width="1.5"/>'
    )
    return svg


def scan_rotation(t):
    svg = Svg(
        t,
        "Scan rotation: the center of mass of the direct beam over the scan is a gradient field "
        "in the scan frame. In the detector frame it is rotated and has curl; rotating the "
        "detector axes until the curl vanishes gives the angle, which is ambiguous by 180 degrees",
    )
    xs = [25, 465, 905]
    y = TOP + P / 2

    svg.title(xs[0] + P / 2, "Detector frame")
    svg.panel(xs[0], TOP)
    com_field(svg, xs[0], TOP, P, 80)
    svg.caption(xs[0] + P / 2, ["CoM of the direct beam,", "curl ≠ 0"])

    svg.title(xs[1] + P / 2, "Scan frame")
    svg.panel(xs[1], TOP)
    com_field(svg, xs[1], TOP, P, 0)
    svg.caption(xs[1] + P / 2, ["a gradient field,", "curl = 0"])
    svg.arrow(xs[0] + P + 14, y, xs[1] - 14, y, label="rotate by θ")
    frames(svg, (xs[0] + P + xs[1]) / 2 - 30, y + 26, 34, length=40)

    svg.title(xs[2] + P / 2, "Curl vs angle")
    svg.panel(xs[2], TOP)
    cx0, cx1 = xs[2] + 16, xs[2] + P - 14
    cy0, cy1 = TOP + 20, TOP + P - 34
    pts = []
    for k in range(121):
        ang = -180 + 360 * k / 120
        val = 0.5 - 0.46 * math.cos(math.radians(2 * (ang - 34)))
        pts.append((cx0 + k / 120 * (cx1 - cx0), cy1 - val * (cy1 - cy0)))
    svg.add(
        '<polyline points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        + f'" fill="none" stroke="{t["ink"]}" stroke-width="2"/>'
    )
    for ang, col, lab in [(34, t["red"], "θ"), (34 - 180, t["muted"], "θ − 180°")]:
        xx = cx0 + (ang + 180) / 360 * (cx1 - cx0)
        svg.add(f'<circle cx="{xx:.1f}" cy="{cy1 - 0.04 * (cy1 - cy0):.1f}" r="4.5" fill="{col}"/>')
        svg.text(xx, cy1 + 21, lab, size=15, color=col, italic=True)
    svg.add(f'<line x1="{cx0}" y1="{cy1}" x2="{cx1}" y2="{cy1}" stroke="{t["muted"]}" stroke-width="1.5"/>')
    svg.caption(xs[2] + P / 2, ["minimum curl,", "ambiguous by 180°"])
    svg.arrow(xs[1] + P + 14, y, xs[2] - 14, y)
    return svg


def calibration_subsets(t):
    svg = Svg(
        t,
        "Calibrating on a subset of positions: select a region whose crystallography is known, "
        "calibrate on the peaks from that region only, and apply the calibration to every position",
    )
    xs = [25, 465, 905]
    y = TOP + P / 2
    field = lath_field(14, 14)

    svg.title(xs[0] + P / 2, "positions = mask")

    def sel(lab, i, j):
        return t["cyan"] if lab < 0 else mix(ALPHA_VARIANTS[lab], "#9AA0A6", 0.75)

    draw_map(svg, xs[0], TOP, field, sel)
    svg.caption(xs[0] + P / 2, ["a region of known phase,", "here the beta matrix"])

    svg.title(xs[1] + P / 2, "Calibrate on the region")
    draw_pattern(svg, xs[1], TOP, hex_spots(scale=24.0, angle_deg=0.0, laue=(0.0, 0.0)), halo=False)
    svg.caption(xs[1] + P / 2, ["calibrate or calibrate_2d", "with positions"])
    svg.arrow(xs[0] + P + 14, y, xs[1] - 14, y, label="sum its peaks")

    svg.title(xs[2] + P / 2, "Apply to all")
    draw_map(svg, xs[2], TOP, field, lambda lab, i, j: t["cyan"] if lab < 0 else ALPHA_VARIANTS[lab])
    svg.caption(xs[2] + P / 2, ["apply_calibration", "on the whole scan"])
    svg.arrow(xs[1] + P + 14, y, xs[2] - 14, y, label="apply")
    return svg


def refine_calibration_fig(t):
    svg = Svg(
        t,
        "Refining the calibration from strain: the deformation fitted at each position combines "
        "local strain and the global calibration error; the median over many differently "
        "oriented grains averages the strain away and leaves the scale and ellipse residual",
    )
    xs = [25, 465, 905]
    y = TOP + P / 2
    rnd = random.Random(5)
    bias = (1.012, 0.994, 0.004)  # global scale, ellipse

    def ellipse(cx, cy, r, sx, sy, ang, color, width=1.6, op=1.0):
        svg.add(
            f'<ellipse cx="{cx:.1f}" cy="{cy:.1f}" rx="{r * sx:.1f}" ry="{r * sy:.1f}" '
            f'transform="rotate({ang:.1f} {cx:.1f} {cy:.1f})" fill="none" stroke="{color}" '
            f'stroke-width="{width}" stroke-opacity="{op}"/>'
        )

    svg.title(xs[0] + P / 2, "Strain per position")
    svg.panel(xs[0], TOP)

    def compose(e, phi):
        """Bias ellipse (1.07, 0.93 at 20 deg) times a random strain, as ellipse parameters."""
        def sym(a, b, ang):
            c, s_ = math.cos(math.radians(ang)), math.sin(math.radians(ang))
            return [[a * c * c + b * s_ * s_, (a - b) * c * s_], [(a - b) * c * s_, a * s_ * s_ + b * c * c]]
        B, S = sym(1.07, 0.93, 20), sym(1 + e, 1 - e, phi)
        M = [[sum(B[i][k] * S[k][j] for k in range(2)) for j in range(2)] for i in range(2)]
        # ellipse of M applied to the unit circle: eigen-decomposition of M M^T
        a = M[0][0] ** 2 + M[0][1] ** 2
        b = M[0][0] * M[1][0] + M[0][1] * M[1][1]
        d = M[1][0] ** 2 + M[1][1] ** 2
        tr, det = a + d, a * d - b * b
        l1 = tr / 2 + math.sqrt(max(tr * tr / 4 - det, 0))
        l2 = tr / 2 - math.sqrt(max(tr * tr / 4 - det, 0))
        ang = math.degrees(0.5 * math.atan2(2 * b, a - d))
        return math.sqrt(l1), math.sqrt(l2), ang

    glyphs = []
    for j in range(4):
        for i in range(4):
            glyphs.append(compose(rnd.uniform(0.04, 0.16), rnd.uniform(0, 180)))
            sx, sy, ang = glyphs[-1]
            ellipse(xs[0] + 24 + i * 41, TOP + 24 + j * 41, 12, sx, sy, ang, t["ink"])
    svg.caption(xs[0] + P / 2, ["strain plus the", "calibration error"])

    svg.title(xs[1] + P / 2, "Median over grains")
    svg.panel(xs[1], TOP)
    cx, cy = xs[1] + P / 2, TOP + P / 2
    for sx, sy, ang in glyphs:
        ellipse(cx, cy, 52, sx, sy, ang, t["muted"], width=1.2, op=0.45)
    ellipse(cx, cy, 52, 1.07, 0.93, 20, t["red"], width=3)
    svg.caption(xs[1] + P / 2, ["the strain averages", "away"])
    svg.arrow(xs[0] + P + 14, y, xs[1] - 14, y, label="many orientations")

    svg.title(xs[2] + P / 2, "Residual")
    svg.panel(xs[2], TOP)
    cx, cy = xs[2] + P / 2, TOP + P / 2 - 10
    ellipse(cx, cy, 50, 1.07, 0.93, 20, t["red"], width=2.2)
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="50" fill="none" stroke="{t["ink"]}" stroke-width="2" stroke-dasharray="5 4"/>')
    svg.text(cx, TOP + P - 14, "scale, ellipse", size=16, color=t["ink"])
    svg.caption(xs[2] + P / 2, ["rotation is not", "observable this way"])
    svg.arrow(xs[1] + P + 14, y, xs[2] - 14, y, label="correction")
    return svg


def orientation_mapping(t):
    svg = Svg(
        t,
        "Orientation and phase mapping: the measured peaks are transformed to polar coordinates, "
        "correlated with a library of simulated patterns over the fundamental zone axis wedge, "
        "the best in-plane angle is found from the correlation, and refinement and a phase "
        "decision give the orientation and phase maps",
    )
    xs, gap = panel_xs(5, size=160)
    s = 160
    y = TOP + s / 2
    spots = hex_spots(scale=21.0, angle_deg=12.0)
    imax = max(sp[2] for sp in spots)
    kept = [sp for sp in spots if sp[2] / imax > 0.08 and abs(sp[0]) < s / 2 - 8 and abs(sp[1]) < s / 2 - 8]

    # 1: measured peaks
    svg.title(xs[0] + s / 2, "Measured peaks")
    draw_pattern(svg, xs[0], TOP, spots, size=s)
    svg.caption(xs[0] + s / 2, ["calibrated Bragg", "peaks, one position"])

    # 2: polar shells
    svg.title(xs[1] + s / 2, "Polar shells")
    svg.panel(xs[1], TOP, s, s)
    shells = sorted({round(sp[3], 3) for sp in kept})
    gmax = shells[-1]
    px0, px1 = xs[1] + 14, xs[1] + s - 14
    py0, py1 = TOP + 14, TOP + s - 26
    for g in shells:
        yy = py1 - (g / gmax) * (py1 - py0 - 6)
        svg.add(
            f'<rect x="{px0}" y="{yy - 4:.1f}" width="{px1 - px0}" height="8" fill="{t["blue"]}" fill-opacity="0.15"/>'
        )
        svg.add(
            f'<line x1="{px0}" y1="{yy:.1f}" x2="{px1}" y2="{yy:.1f}" stroke="{t["blue"]}" '
            f'stroke-width="1" stroke-dasharray="3 3"/>'
        )
    for sx, sy, inten, g in kept:
        th = (math.degrees(math.atan2(sy, sx)) + 360) % 360
        xx = px0 + th / 360 * (px1 - px0)
        yy = py1 - (g / gmax) * (py1 - py0 - 6)
        svg.add(f'<circle cx="{xx:.1f}" cy="{yy:.1f}" r="{2.2 + 2.6 * math.sqrt(inten / imax):.1f}" fill="{t["ink"]}"/>')
    svg.text((px0 + px1) / 2, py1 + 14, "azimuth", size=14, color=t["muted"])
    svg.caption(xs[1] + s / 2, ["only the shells that", "hold reflections"])

    # 3: library over the fundamental wedge
    svg.title(xs[2] + s / 2, "Library")
    svg.panel(xs[2], TOP, s, s)
    tx, ty = xs[2] + s / 2, TOP + 26
    bl = (xs[2] + 26, TOP + s - 34)
    br = (xs[2] + s - 26, TOP + s - 34)
    n = 10
    for a in range(n + 1):
        for b in range(n + 1 - a):
            c = n - a - b
            u, v, w = a / n, b / n, c / n  # top, bottom-left, bottom-right weights
            x = u * tx + v * bl[0] + w * br[0]
            yv = u * ty + v * bl[1] + w * br[1] + 9 * 4 * v * w  # bowed lower edge
            svg.add(f'<circle cx="{x:.1f}" cy="{yv:.1f}" r="3.6" fill="{ipf_color(u + 0.08, v + 0.08, w + 0.08)}"/>')
    svg.text(tx, ty - 8, "[0001]", size=14, color=t["muted"])
    svg.text(bl[0] - 4, bl[1] + 24, "[21̄1̄0]", size=14, color=t["muted"], anchor="start")
    svg.text(br[0] + 4, br[1] + 24, "[101̄0]", size=14, color=t["muted"], anchor="end")
    svg.caption(xs[2] + s / 2, ["zone axes over the", "symmetry wedge"])

    # 4: correlation over the in-plane angle
    svg.title(xs[3] + s / 2, "Correlation")
    svg.panel(xs[3], TOP, s, s)
    cx0, cx1 = xs[3] + 18, xs[3] + s - 14
    cy0, cy1 = TOP + 22, TOP + s - 30
    pts = []
    best = 0.62
    for k in range(121):
        f = k / 120
        val = 0.22 + 0.10 * math.cos(6 * 2 * math.pi * (f - best)) + 0.5 * math.exp(-((f - best) / 0.022) ** 2)
        val += 0.05 * math.sin(17 * 2 * math.pi * f + 1.0)
        pts.append((cx0 + f * (cx1 - cx0), cy1 - val * (cy1 - cy0)))
    svg.add(
        '<polyline points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in pts)
        + f'" fill="none" stroke="{t["ink"]}" stroke-width="2" stroke-linejoin="round"/>'
    )
    bx = cx0 + best * (cx1 - cx0)
    by = min(p[1] for p in pts)
    svg.add(f'<circle cx="{bx:.1f}" cy="{by:.1f}" r="5" fill="{t["red"]}"/>')
    svg.add(f'<line x1="{cx0}" y1="{cy1}" x2="{cx1}" y2="{cy1}" stroke="{t["muted"]}" stroke-width="1.5"/>')
    svg.text((cx0 + cx1) / 2, cy1 + 22, "in-plane angle", size=15, color=t["muted"])
    svg.text(bx, by - 10, "best", size=14, color=t["red"])
    svg.caption(xs[3] + s / 2, ["cosine similarity,", "FFT over the angle"])

    # 5: maps
    svg.title(xs[4] + s / 2, "Phase map")
    field = lath_field(14, 14)
    draw_map(
        svg, xs[4], TOP, field, lambda lab, i, j: t["cyan"] if lab < 0 else ALPHA_VARIANTS[lab], size=s
    )
    svg.caption(xs[4] + s / 2, ["after refinement and", "the phase decision"])

    svg.arrow(xs[0] + s + 10, y, xs[1] - 10, y)
    svg.star((xs[1] + s + xs[2]) / 2, y, r=14)
    svg.arrow(xs[2] + s + 10, y, xs[3] - 10, y)
    svg.arrow(xs[3] + s + 10, y, xs[4] - 10, y)
    return svg


def diffraction_simulation(t):
    svg = Svg(
        t,
        "Diffraction simulation: the Ewald sphere sets the excitation error of each reflection, "
        "kinematical patterns weight each reflection by its structure factor and excitation "
        "error, Bloch wave calculations add multiple scattering through the specimen thickness, "
        "and a convergent probe gives CBED and Kossel patterns",
    )
    xs = [25, 318, 611, 905]
    y = TOP + P / 2

    # 1: Ewald sphere and excitation error
    svg.title(xs[0] + P / 2, "Ewald sphere")
    svg.panel(xs[0], TOP)
    ox, oy = xs[0] + P / 2, TOP + P - 34  # reciprocal space origin
    d = 21
    R = 170  # exaggerated curvature
    for j in range(0, 4):
        for i in range(-3, 4):
            gx, gy = ox + i * d, oy - j * d
            if gy < TOP + 12:
                continue
            svg.add(f'<circle cx="{gx}" cy="{gy}" r="3" fill="{t["muted"]}" fill-opacity="0.8"/>')
    # sphere through the origin, center straight up the beam
    a0 = math.asin(min(1.0, (P / 2 - 8) / R))
    arc = [
        (ox + R * math.sin(a), oy - R + R * math.cos(a))
        for a in [(-a0 + 2 * a0 * k / 60) for k in range(61)]
    ]
    svg.add(
        '<polyline points="' + " ".join(f"{a:.1f},{b:.1f}" for a, b in arc)
        + f'" fill="none" stroke="{t["blue"]}" stroke-width="2.5"/>'
    )
    svg.add(f'<circle cx="{ox}" cy="{oy}" r="4.5" fill="{t["ink"]}"/>')
    # one reflection and its excitation error
    gx, gy = ox + 2 * d, oy - 1 * d
    sy = oy - R + math.sqrt(R * R - (2 * d) ** 2)
    svg.add(f'<circle cx="{gx}" cy="{gy}" r="4.5" fill="{t["red"]}"/>')
    svg.add(f'<line x1="{gx}" y1="{gy + 4}" x2="{gx}" y2="{sy:.1f}" stroke="{t["red"]}" stroke-width="2.5"/>')
    svg.text(gx + 9, (gy + sy) / 2 + 6, "s", size=18, color=t["red"], anchor="start", italic=True)
    svg.text(gx + 17, (gy + sy) / 2 + 11, "g", size=12, color=t["red"], anchor="start", italic=True)
    svg.arrow(ox, TOP + 12, ox, TOP + 64, color=t["muted"], width=2, head=9)
    svg.text(ox + 9, TOP + 32, "beam", size=14, color=t["muted"], anchor="start")
    svg.caption(xs[0] + P / 2, ["excitation error s", "of every reflection"])

    # 2: kinematical pattern
    svg.title(xs[1] + P / 2, "Kinematical")
    svg.panel(xs[1], TOP)
    cx, cy = xs[1] + P / 2, TOP + P / 2
    for i in range(-4, 5):
        for j in range(-4, 5):
            gxx, gyy = i * 20, j * 20
            g2 = gxx * gxx + gyy * gyy
            if g2 == 0 or abs(gxx) > P / 2 - 10 or abs(gyy) > P / 2 - 10:
                continue
            f2 = 1.0 if (i + j) % 2 == 0 else 0.35  # alternating structure factors
            env = math.exp(-g2 / 5200.0)
            r = 1.5 + 6.0 * math.sqrt(f2 * env)
            svg.add(f'<circle cx="{cx + gxx}" cy="{cy + gyy}" r="{r:.1f}" fill="{t["ink"]}"/>')
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="8" fill="none" stroke="{t["red"]}" stroke-width="2"/>')
    svg.caption(xs[1] + P / 2, ["|F|² × envelope in s,", "for orientation libraries"])

    # 3: Bloch waves through a slab
    svg.title(xs[2] + P / 2, "Bloch waves")
    svg.panel(xs[2], TOP)
    sx0, sx1 = xs[2] + 16, xs[2] + P - 16
    st, sb = TOP + 52, TOP + 112
    svg.add(
        f'<rect x="{sx0}" y="{st}" width="{sx1 - sx0}" height="{sb - st}" fill="{t["blue"]}" '
        f'fill-opacity="0.16" stroke="{t["blue"]}" stroke-opacity="0.6"/>'
    )
    cxs = xs[2] + P / 2
    svg.add(f'<line x1="{cxs}" y1="{TOP + 12}" x2="{cxs}" y2="{st}" stroke="{t["ink"]}" stroke-width="3"/>')
    # multiple scattering paths inside the slab
    z1, z2 = st + 20, st + 42
    paths = [
        (cxs, st, cxs, z1), (cxs, z1, cxs - 18, z2), (cxs, z1, cxs + 18, z2), (cxs, z1, cxs, sb),
        (cxs - 18, z2, cxs - 30, sb), (cxs - 18, z2, cxs - 6, sb), (cxs + 18, z2, cxs + 30, sb),
        (cxs + 18, z2, cxs + 6, sb), (cxs, st, cxs + 14, z1), (cxs + 14, z1, cxs + 2, z2),
    ]
    for x1, y1, x2, y2 in paths:
        svg.add(
            f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="{t["red"]}" '
            f'stroke-width="1.6" stroke-opacity="0.85"/>'
        )
    widths = {-60: 1.4, -30: 3.0, 0: 4.4, 30: 2.2, 60: 1.0}
    for dx, wdt in widths.items():
        svg.add(
            f'<line x1="{cxs + dx * 0.35:.1f}" y1="{sb}" x2="{cxs + dx:.1f}" y2="{TOP + P - 12}" '
            f'stroke="{t["ink"]}" stroke-width="{wdt}" stroke-linecap="round"/>'
        )
    svg.text(sx1 - 4, st + 20, "t", size=17, color=t["blue"], anchor="end", italic=True)
    svg.caption(xs[2] + P / 2, ["multiple scattering", "and absorption"])

    # 4: convergent beam, Kossel lines
    svg.title(xs[3] + P / 2, "Convergent beam")
    cx, cy = xs[3] + P / 2, TOP + P / 2
    svg.detector(xs[3], TOP)
    rr = P / 2 - 14
    svg.add(f'<clipPath id="kossel"><circle cx="{cx}" cy="{cy}" r="{rr}"/></clipPath>')
    svg.add(f'<circle cx="{cx}" cy="{cy}" r="{rr}" fill="#D9E4EE"/>')
    svg.add('<g clip-path="url(#kossel)">')
    for k, (ang, off, wdt) in enumerate(
        [(0, 0, 3.0), (60, 0, 3.0), (120, 0, 3.0), (0, 30, 1.8), (0, -30, 1.8), (60, 30, 1.8),
         (60, -30, 1.8), (120, 30, 1.8), (120, -30, 1.8), (30, 52, 1.2), (90, 52, 1.2), (150, 52, 1.2),
         (30, -52, 1.2), (90, -52, 1.2), (150, -52, 1.2)]
    ):
        a = math.radians(ang)
        nx, ny = -math.sin(a), math.cos(a)
        x0, y0 = cx + off * nx - 200 * math.cos(a), cy + off * ny - 200 * math.sin(a)
        x1, y1 = cx + off * nx + 200 * math.cos(a), cy + off * ny + 200 * math.sin(a)
        svg.add(
            f'<line x1="{x0:.1f}" y1="{y0:.1f}" x2="{x1:.1f}" y2="{y1:.1f}" stroke="#18222D" '
            f'stroke-width="{wdt}" stroke-opacity="0.8"/>'
        )
    svg.add("</g>")
    svg.caption(xs[3] + P / 2, ["CBED, LACBED,", "and Kossel patterns"])

    svg.arrow(xs[0] + P + 12, y, xs[1] - 12, y)
    svg.arrow(xs[1] + P + 12, y, xs[2] - 12, y)
    svg.arrow(xs[2] + P + 12, y, xs[3] - 12, y)
    return svg


FIGURES = {
    "acom-workflow": acom_workflow,
    "disk-detection": disk_detection,
    "calibration": calibration,
    "calibration-routes": calibration_routes,
    "scan-rotation": scan_rotation,
    "calibration-subsets": calibration_subsets,
    "refine-calibration": refine_calibration_fig,
    "orientation-mapping": orientation_mapping,
    "diffraction-simulation": diffraction_simulation,
}


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    for name, make in FIGURES.items():
        for theme, t in THEMES.items():
            make(t).write(name, theme)
            print(f"wrote schematic-{name}-{theme}.svg")
