"""Build the quantEM logo assets from the original vector artwork.

Source: assets/src/logo53_exact.svg, converted losslessly from Colin's
logos_53.pdf with `pdftocairo -svg`. This script regroups the paths into
named elements (EELS, diffraction, structure, tomography, text) and emits:

  assets/quantem-logo-light.svg / -dark.svg   full static logo
  assets/anim/qem-base-{light,dark}.svg       wordmark only (landing base)
  assets/anim/qem-<el>-static[-mode].svg      per-element static layer
  assets/anim/qem-<el>-anim[-mode].svg        per-element animated layer

The per-element layers are stacked on the landing page; CSS swaps
static -> animated on hover. Run with --css to print the overlay CSS.

Canvas: viewBox 0 0 460.8 266.4 (the original PDF page).
"""

import copy
import math
import os
import re
import sys
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))
ANIM = os.path.join(ASSETS, "anim")
os.makedirs(ANIM, exist_ok=True)

W, H = 460.8, 266.4
BLACK = "rgb(0%, 0%, 0%)"
RED = "rgb(79.998779%, 0.799561%, 0.799561%)"
GREEN = "rgb(0%, 74.899292%, 0%)"
MAROON = "rgb(60.398865%, 0.799561%, 0.799561%)"
BLUES = {
    "rgb(1.998901%, 70.999146%, 90.19928%)",
    "rgb(3.898621%, 52.198792%, 80.799866%)",
    "rgb(0%, 24.699402%, 49.798584%)",
}
INKS = {"light": "#1A1A1A", "dark": "#F2F2F2"}
PAD = 4.0  # padding around per-element viewBoxes
TOMO_DY = -10.0  # lift the tomography element clear of the wordmark


def parse_matrix(t):
    """Compose a transform list into one matrix [a, b, c, d, e, f]."""
    if not t:
        return None
    out = [1, 0, 0, 1, 0, 0]
    for fn, args in re.findall(r"(matrix|translate)\(([^)]*)\)", t):
        vals = [float(x) for x in re.split(r"[,\s]+", args.strip())]
        m = vals if fn == "matrix" else [1, 0, 0, 1, vals[0], vals[1]]
        a1, b1, c1, d1, e1, f1 = out
        a2, b2, c2, d2, e2, f2 = m
        out = [
            a1 * a2 + c1 * b2, b1 * a2 + d1 * b2,
            a1 * c2 + c1 * d2, b1 * c2 + d1 * d2,
            a1 * e2 + c1 * f2 + e1, b1 * e2 + d1 * f2 + f1,
        ]
    return out


def bbox_of(el):
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*(?:e-?\d+)?", el.get("d"))]
    pts = list(zip(nums[0::2], nums[1::2]))
    mat = parse_matrix(el.get("transform"))
    if mat:
        a, b, c, d, e, f = mat
        pts = [(a * x + c * y + e, b * x + d * y + f) for x, y in pts]
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def center(bb):
    return (bb[0] + bb[2]) / 2, (bb[1] + bb[3]) / 2


def classify():
    tree = ET.parse(os.path.join(ASSETS, "src", "logo53_exact.svg"))
    root = tree.getroot()
    defs = root.find(f"{{{SVG}}}defs")
    groups = {"eels": [], "dif": [], "struct": [], "tomo": [], "text": []}
    for el in list(root):
        tag = el.tag.split("}")[-1]
        if tag == "defs":
            continue
        if tag == "g":  # the gradient-filled EELS spectrum
            groups["eels"].append(el)
            continue
        if tag != "path":
            continue
        bb = bbox_of(el)
        cx, cy = center(bb)
        area = (bb[2] - bb[0]) * (bb[3] - bb[1])
        if el.get("stroke"):  # projection rays
            g = "tomo"
        elif cy > 160:
            g = "text"
        elif cx > 286 or (
            cx > 270 and area > 40 and el.get("fill") in (MAROON, RED)
        ):  # detector wedges + dome
            g = "tomo"
        elif el.get("fill") in BLUES and area > 100 and cx > 190:
            # Octahedron faces are ~208 units; the next largest blue shapes
            # are ~30 unit diffraction dots, so 100 separates them cleanly.
            g = "struct"
        elif el.get("fill") == GREEN and area > 25:
            g = "struct"  # A-site cations (diffraction greens are tiny)
        else:
            g = "dif"  # provisional; dots are reassigned below
        groups[g].append(el)

    # dots (oxygens, A-sites) belong to the structure only if they touch an
    # octahedron face; everything else in the overlap zone is diffraction
    def dist_to_faces(bb):
        cx, cy = center(bb)
        best = 1e9
        for f in groups["struct"]:
            fb = bbox_of(f)
            dx = max(fb[0] - cx, 0, cx - fb[2])
            dy = max(fb[1] - cy, 0, cy - fb[3])
            best = min(best, math.hypot(dx, dy))
        return best

    keep_dif = []
    for el in groups["dif"]:
        bb = bbox_of(el)
        cx = center(bb)[0]
        ok_fill = el.get("fill") == RED  # only oxygens sit on the faces
        if cx > 175 and ok_fill and dist_to_faces(bb) < 3.0:
            groups["struct"].append(el)
        elif cx > 280:  # artifacts hidden under the detector wheel
            groups["tomo"].insert(0, el)
        else:
            keep_dif.append(el)
    groups["dif"] = keep_dif

    # raise the tomography element so it clears the top of the wordmark
    for el in groups["tomo"]:
        t = el.get("transform")
        el.set("transform", f"translate(0,{TOMO_DY}) {t}" if t else f"translate(0,{TOMO_DY})")
    return defs, groups


def ink_swap(el, ink):
    el = copy.deepcopy(el)
    for p in el.iter():
        if p.get("fill") == BLACK:
            p.set("fill", ink)
        if p.get("stroke") == BLACK:
            p.set("stroke", ink)
    return el


def group_bbox(els):
    bbs = [bbox_of(p) for el in els for p in el.iter(f"{{{SVG}}}path")
           if not p.get("clip-rule")]
    return (
        min(b[0] for b in bbs),
        min(b[1] for b in bbs),
        max(b[2] for b in bbs),
        max(b[3] for b in bbs),
    )


def serialize(els, ink=None):
    return "".join(
        ET.tostring(ink_swap(e, ink) if ink else e, encoding="unicode")
        for e in els
    )


def svg_doc(view, content, hit_rect=False):
    # hit_rect: invisible full-box rectangle so the inlined svg receives
    # hover events over its whole area, not only over painted shapes
    rect = ""
    if hit_rect:
        vx, vy, vw, vh = view.split()
        rect = (
            f'<rect x="{vx}" y="{vy}" width="{vw}" height="{vh}" '
            f'fill="transparent"/>'
        )
    return (
        f'<svg xmlns="{SVG}" xmlns:xlink="http://www.w3.org/1999/xlink" '
        f'viewBox="{view}">{rect}{content}</svg>\n'
    )


def write(path, content):
    with open(path, "w") as f:
        f.write(content)


def view_of(bb):
    x0, y0 = bb[0] - PAD, bb[1] - PAD
    return (
        f"{x0:.1f} {y0:.1f} {bb[2] - bb[0] + 2 * PAD:.1f} "
        f"{bb[3] - bb[1] + 2 * PAD:.1f}"
    )


# ----------------------------------------------------------------------------
# Per-element landing-page layers
#
# Each element is one SVG containing its (paused) animations. A small runtime
# injected by scripts/patch_theme.py inlines these into the page, then drives
# svg.pauseAnimations()/unpauseAnimations() (and the --qem-play CSS variable)
# on hover, so leaving an element freezes it in its current state.
# ----------------------------------------------------------------------------
VIOLET = "rgb(45%, 4%, 60%)"
PURPLE = "rgb(24%, 10%, 58%)"
EXTEND = 1.18   # gradient period extension holding the purple wrap segment
EELS_DUR = "9.5s"   # one period; half the speed of the original 4s design
TOMO_DUR = "5s"     # time to advance the wheel by exactly one panel


def namespace_ids(s, prefix):
    return s.replace('id="', f'id="{prefix}').replace("url(#", f"url(#{prefix}")


def eels_svg(defs, eels_els, view):
    """Spectrum with a periodic flowing gradient (SMIL, starts paused).

    The original 257-stop gradient is compressed into [0, 1/EXTEND] of an
    extended period; the remainder blends maroon -> violet -> purple back to
    the starting navy so the wrap is smooth. The extra segment sits outside
    the visible window at t=0, so the paused state matches the artwork.
    """
    grad = [d for d in defs if d.tag.endswith("linearGradient")][0]
    stops = [(float(s.get("offset")), s.get("stop-color")) for s in grad]
    mat = parse_matrix(grad.get("gradientTransform"))
    scale = mat[0] * EXTEND
    k = 1.0 / EXTEND
    parts = [
        f'<linearGradient id="linear-pattern-0" gradientUnits="userSpaceOnUse" '
        f'x1="0" y1="0" x2="1" y2="0" spreadMethod="repeat" '
        f'gradientTransform="matrix({scale:.4f}, 0, 0, {scale:.4f}, '
        f'{mat[4]:.4f}, {mat[5]:.4f})">'
    ]
    for off, color in stops:
        parts.append(f'<stop offset="{off * k:.6f}" stop-color="{color}"/>')
    for off, color in ((0.898, VIOLET), (0.949, PURPLE), (1.0, stops[0][1])):
        parts.append(f'<stop offset="{off}" stop-color="{color}"/>')
    parts.append(
        '<animateTransform attributeName="gradientTransform" type="translate" '
        f'additive="sum" from="0 0" to="1 0" dur="{EELS_DUR}" '
        'repeatCount="indefinite"/></linearGradient>'
    )
    clips = "".join(
        ET.tostring(d, encoding="unicode")
        for d in defs
        if d.tag.endswith("clipPath")
    )
    body = f"<defs>{clips}{''.join(parts)}</defs>" + serialize(eels_els)
    return svg_doc(view, body, hit_rect=True)


def dif_svg(els, view, ink):
    # class-scoped: inlined <style> applies to the whole page document
    css = (
        "<style>.qem-difg path{transform-box:fill-box;transform-origin:center;"
        "animation:qemPulse 3.5s ease-in-out infinite;"
        "animation-play-state:var(--qem-play,paused)}"
        "@keyframes qemPulse{0%{transform:scale(1)}40%{transform:scale(1.3)}"
        "75%{transform:scale(0.72)}100%{transform:scale(1)}}</style>"
    )
    return svg_doc(view, css + f'<g class="qem-difg">{serialize(els, ink)}</g>', hit_rect=True)


def face_points(el):
    nums = [float(x) for x in re.findall(r"-?\d+\.?\d*", el.get("d"))]
    pts = list(zip(nums[0::2], nums[1::2]))
    uniq = []
    for p in pts:
        if not any(abs(p[0] - q[0]) < 0.3 and abs(p[1] - q[1]) < 0.3 for q in uniq):
            uniq.append(p)
    return uniq


def struct_svg(els, view):
    """Octahedra oscillate rigidly in alternating senses (Glazer tilts).

    Each octahedron's faces share their center vertex, and that vertex is
    much closer to the face centroids (~0.47a) than any corner is (~0.75a),
    which identifies the rotation centers exactly.
    """
    faces = [e for e in els if e.get("fill") in BLUES]
    oxygens = [e for e in els if e.get("fill") == RED]
    rest = [e for e in els if e.get("fill") not in BLUES
            and e.get("fill") != RED]
    a_est = (
        sorted(
            math.sqrt((b[2] - b[0]) * (b[3] - b[1]))
            for b in (bbox_of(f) for f in faces)
        )[len(faces) // 2]
    )
    vmap = {}
    for f in faces:
        for x, y in face_points(f):
            vmap.setdefault((round(x * 2) / 2, round(y * 2) / 2), []).append(f)

    def centroid(f):
        ps = face_points(f)
        return (
            sum(p[0] for p in ps) / len(ps),
            sum(p[1] for p in ps) / len(ps),
        )

    centers = []
    for (vx, vy), fs in vmap.items():
        if len(fs) < 3:
            continue
        if max(math.hypot(cx - vx, cy - vy) for cx, cy in map(centroid, fs)) < 0.7 * a_est:
            centers.append((vx, vy))

    def nearest_center(p):
        return min(centers, key=lambda c: (c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2)

    clusters = {}
    for f in faces:
        c = nearest_center(centroid(f))
        clusters.setdefault(c, []).append(f)

    # Oxygens sit on the octahedron corners, so they must rotate with them.
    # A corner shared by two neighbours moves identically under the
    # antiphase pattern below, so attaching it to the nearest centre is
    # consistent for both.
    for ox in oxygens:
        c = nearest_center(center(bbox_of(ox)))
        d = math.hypot(c[0] - center(bbox_of(ox))[0],
                       c[1] - center(bbox_of(ox))[1])
        if d < 1.35 * a_est:
            clusters.setdefault(c, []).append(ox)
        else:
            rest.append(ox)

    u, v = (25.65, 8.35), (-8.35, 25.65)
    ox, oy = centers[0]
    parts = []
    for (cx, cy), members in clusters.items():
        du = ((cx - ox) * u[0] + (cy - oy) * u[1]) / (u[0] ** 2 + u[1] ** 2)
        dv = ((cx - ox) * v[0] + (cy - oy) * v[1]) / (v[0] ** 2 + v[1] ** 2)
        amp = 8 if (round(du) + round(dv)) % 2 == 0 else -8
        c = f"{cx:.1f} {cy:.1f}"
        parts.append(
            f"<g>{serialize(members)}"
            f'<animateTransform attributeName="transform" type="rotate" '
            f'values="0 {c};{amp} {c};0 {c};{-amp} {c};0 {c}" '
            f'keyTimes="0;0.25;0.5;0.75;1" calcMode="spline" '
            f'keySplines="0.45 0 0.55 1;0.45 0 0.55 1;0.45 0 0.55 1;'
            f'0.45 0 0.55 1" dur="6s" repeatCount="indefinite"/></g>'
        )
    return svg_doc(view, "".join(parts) + serialize(rest), hit_rect=True)


def tomo_svg(els, view, ink):
    """Detector wheel rotating by exactly one panel, colours fixed in space.

    Nine panels tile the visible half ring, so the pitch is exactly
    180/9 degrees and a copy rotated by 180 completes the wheel. Colour is a
    property of the *slot*, not the panel: each panel cross-fades to the
    colour of the slot it rotates into, so the red-orange-yellow-green-cyan-
    blue bands stay put while the hardware turns. The hidden half carries the
    mirrored sequence, so a panel rising on the left arrives already dark
    red rather than dragging navy around from the right. After one pitch the
    image is identical, which makes the loop seamless.
    """
    wedges = [e for e in els if not e.get("stroke") and e.get("fill") != BLACK]
    rays = [e for e in els if e.get("stroke")]
    dome = [e for e in els if e.get("fill") == BLACK]
    db = group_bbox(dome)
    cx, cy = (db[0] + db[2]) / 2, db[3]

    def angle(el):
        px, py = center(bbox_of(el))
        return math.degrees(math.atan2(cy - py, px - cx))

    wedges.sort(key=angle)          # index 0 = rightmost, n-1 = leftmost
    n = len(wedges)
    pitch = 180.0 / n
    colors = [w.get("fill") for w in wedges]

    def animate(el, frm, to):
        el = copy.deepcopy(el)
        el.set("fill", frm)
        a = ET.SubElement(el, f"{{{SVG}}}animate")
        a.set("attributeName", "fill")
        a.set("values", f"{frm};{to}")
        a.set("dur", TOMO_DUR)
        a.set("repeatCount", "indefinite")
        return el

    # Visible half: panel i sits in slot i and rotates into slot i-1.
    # Panel 0 leaves the visible arc into a hidden slot of its own colour.
    visible = [
        animate(w, colors[i], colors[i - 1] if i else colors[0])
        for i, w in enumerate(wedges)
    ]
    # Hidden half (rotated 180): mirrored colours, so slot i of that ring
    # holds colours[n-1-i] and feeds the left edge with dark red.
    hidden = [
        animate(w, colors[n - 1 - i], colors[n - i] if i else colors[n - 1])
        for i, w in enumerate(wedges)
    ]

    vx, vy, vw, _ = (float(x) for x in view.split())
    clip = (
        f'<clipPath id="horizon"><rect x="{vx}" y="{vy}" width="{vw}" '
        f'height="{cy - vy:.1f}"/></clipPath>'
    )
    ray_svg = serialize(rays, ink)
    wheel = (
        f'<g clip-path="url(#horizon)"><g>'
        f"{serialize(visible)}{ray_svg}"
        f'<g transform="rotate(180 {cx:.1f} {cy:.1f})">'
        f"{serialize(hidden)}{ray_svg}</g>"
        f'<animateTransform attributeName="transform" type="rotate" '
        f'additive="sum" from="0 {cx:.1f} {cy:.1f}" '
        f'to="{pitch:.4f} {cx:.1f} {cy:.1f}" dur="{TOMO_DUR}" '
        f'repeatCount="indefinite"/></g></g>'
    )
    return svg_doc(view, clip + wheel + serialize(dome, ink), hit_rect=True)


# ----------------------------------------------------------------------------
def main():
    defs, groups = classify()
    defs_s = ET.tostring(defs, encoding="unicode")
    order = ("eels", "dif", "struct", "tomo", "text")

    # full static logo
    for mode, ink in INKS.items():
        parts = [defs_s] + [
            f'<g id="qem-{n}">{serialize(groups[n], ink)}</g>' for n in order
        ]
        write(
            os.path.join(ASSETS, f"quantem-logo-{mode}.svg"),
            svg_doc(f"0 0 {W} {H}", "".join(parts)),
        )

    bbs = {n: group_bbox(groups[n]) for n in order}
    views = {n: view_of(bbs[n]) for n in order}

    # landing-page layers (one file per element, animations start paused)
    for mode, ink in INKS.items():
        write(
            os.path.join(ANIM, f"qem-base-{mode}.svg"),
            namespace_ids(
                svg_doc(f"0 0 {W} {H}", serialize(groups["text"], ink)),
                f"b{mode[0]}-",
            ),
        )
        write(
            os.path.join(ANIM, f"qem-dif-{mode}.svg"),
            namespace_ids(
                dif_svg(groups["dif"], views["dif"], ink), f"d{mode[0]}-"
            ),
        )
        write(
            os.path.join(ANIM, f"qem-tomo-{mode}.svg"),
            namespace_ids(
                tomo_svg(groups["tomo"], views["tomo"], ink), f"t{mode[0]}-"
            ),
        )
    write(
        os.path.join(ANIM, "qem-eels.svg"),
        namespace_ids(eels_svg(defs, groups["eels"], views["eels"]), "e-"),
    )
    write(
        os.path.join(ANIM, "qem-struct.svg"),
        namespace_ids(struct_svg(groups["struct"], views["struct"]), "s-"),
    )

    # overlay geometry for the landing page CSS
    for n in order:
        bb = bbs[n]
        x0, y0 = bb[0] - PAD, bb[1] - PAD
        w, h = bb[2] - bb[0] + 2 * PAD, bb[3] - bb[1] + 2 * PAD
        print(
            f"{n}: left {100 * x0 / W:.2f}% top {100 * y0 / H:.2f}% "
            f"width {100 * w / W:.2f}% height {100 * h / H:.2f}%"
        )
    print("counts:", {k: len(v) for k, v in groups.items()})


if __name__ == "__main__":
    main()
