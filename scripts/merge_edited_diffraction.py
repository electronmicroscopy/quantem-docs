"""Merge the hand-corrected diffraction pattern back into the logo source.

The diffraction dots were cleaned up in Illustrator, which rewrote the file:
colours moved to a CSS <style> block, the coordinate frame was cropped
(a pure translation), and the gradient/clip ids were renamed. Everything
except the diffraction was untouched, so we keep the pristine artwork for
EELS / structure / tomography / wordmark and only swap in the corrected dots.

    python scripts/merge_edited_diffraction.py

Inputs
    assets/src/logo_pristine.svg          regenerated from the source PDF
    assets/src/logo_illustrator_edit.svg  the hand-edited file (backup copy)
Output
    assets/src/logo53_exact.svg           merged source (build reads this)
"""

import os
import re
import xml.etree.ElementTree as ET

SVG = "http://www.w3.org/2000/svg"
ET.register_namespace("", SVG)
ET.register_namespace("xlink", "http://www.w3.org/1999/xlink")

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.normpath(os.path.join(HERE, "..", "assets", "src"))
PRISTINE = os.path.join(SRC, "logo_pristine.svg")
EDITED = os.path.join(SRC, "logo_illustrator_edit.svg")
OUT = os.path.join(SRC, "logo53_exact.svg")

# edited -> pristine frame (Illustrator cropped to the content bbox)
TX, TY = 14.11, 17.64

# diffraction vs structure seed points, in the pristine frame (from build_logo)
DIF_SEED = (129.6, 66.6)
STRUCT_SEED = (237.6, 91.8)


_TOKEN = re.compile(r"[MmLlHhVvCcSsQqTtAaZz]|-?\d*\.?\d+(?:e-?\d+)?")


def parse_path_points(d):
    """Absolute anchor + control points of a path, honouring relative commands.
    Good enough for a small dot's bounding box."""
    toks = _TOKEN.findall(d)
    i, cmd = 0, None
    cx = cy = sx = sy = 0.0
    pts = []

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                cx, cy = sx, sy
            continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            sx, sy = cx, cy
            pts.append((cx, cy))
            cmd = "l" if rel else "L"
        elif c == "L":
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            pts.append((cx, cy))
        elif c == "H":
            x = num()
            cx = cx + x if rel else x
            pts.append((cx, cy))
        elif c == "V":
            y = num()
            cy = cy + y if rel else y
            pts.append((cx, cy))
        elif c in ("C", "S", "Q", "T"):
            n = {"C": 3, "S": 2, "Q": 2, "T": 1}[c]
            for _ in range(n):
                x, y = num(), num()
                px, py = (cx + x, cy + y) if rel else (x, y)
                pts.append((px, py))
                lx, ly = px, py
            cx, cy = lx, ly
        elif c == "A":
            num(); num(); num(); num(); num()
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            pts.append((cx, cy))
        else:
            i += 1
    return pts


def path_pts(el, extra=(0.0, 0.0)):
    pts = parse_path_points(el.get("d"))
    t = el.get("transform")
    if t:
        m = re.match(r"matrix\(([^)]*)\)", t)
        if m:
            a, b, c, d, e, f = (float(x) for x in re.split(r"[,\s]+", m.group(1).strip()))
            pts = [(a * x + c * y + e, b * x + d * y + f) for x, y in pts]
    return [(x + extra[0], y + extra[1]) for x, y in pts]


def to_absolute(d, ox, oy):
    """Rewrite a path as absolute commands with (ox, oy) baked into every
    coordinate. Illustrator emits relative h/l/c/v; we flatten them so the dot
    needs no transform attribute (a CSS `transform: scale()` would otherwise
    override a translate attribute and drop the offset)."""
    toks = _TOKEN.findall(d)
    i, cmd = 0, None
    cx = cy = sx = sy = 0.0
    out = []

    def num():
        nonlocal i
        v = float(toks[i])
        i += 1
        return v

    def fmt(v):
        return f"{v:.4f}".rstrip("0").rstrip(".")

    while i < len(toks):
        t = toks[i]
        if t.isalpha():
            cmd = t
            i += 1
            if cmd in "Zz":
                out.append("Z")
                cx, cy = sx, sy
            continue
        rel = cmd.islower()
        c = cmd.upper()
        if c == "M":
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            sx, sy = cx, cy
            out.append(f"M{fmt(cx + ox)} {fmt(cy + oy)}")
            cmd = "l" if rel else "L"
        elif c == "L":
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            out.append(f"L{fmt(cx + ox)} {fmt(cy + oy)}")
        elif c == "H":
            x = num()
            cx = cx + x if rel else x
            out.append(f"L{fmt(cx + ox)} {fmt(cy + oy)}")
        elif c == "V":
            y = num()
            cy = cy + y if rel else y
            out.append(f"L{fmt(cx + ox)} {fmt(cy + oy)}")
        elif c in ("C", "S", "Q", "T"):
            n = {"C": 3, "S": 2, "Q": 2, "T": 1}[c]
            coords = []
            for _ in range(n):
                x, y = num(), num()
                px, py = (cx + x, cy + y) if rel else (x, y)
                coords.append(f"{fmt(px + ox)} {fmt(py + oy)}")
                cx, cy = px, py
            out.append(c + " ".join(coords))
        elif c == "A":
            rx, ry, rot, la, sw = num(), num(), num(), num(), num()
            x, y = num(), num()
            cx, cy = (cx + x, cy + y) if rel else (x, y)
            out.append(f"A{fmt(rx)} {fmt(ry)} {fmt(rot)} {int(la)} {int(sw)} "
                       f"{fmt(cx + ox)} {fmt(cy + oy)}")
        else:
            i += 1
    return "".join(out)


def bbox(pts):
    xs = [p[0] for p in pts]
    ys = [p[1] for p in pts]
    return min(xs), min(ys), max(xs), max(ys)


def is_diffraction(cx, cy, area):
    """Same discriminator build_logo uses to separate dots from structure.
    The area gate must clear the centre beam (~230 with control-point
    overshoot), the largest legitimate dot."""
    if cy > 160 or area > 400:
        return False
    d_dif = (cx - DIF_SEED[0]) ** 2 + (cy - DIF_SEED[1]) ** 2
    d_str = (cx - STRUCT_SEED[0]) ** 2 + (cy - STRUCT_SEED[1]) ** 2
    return d_dif < d_str


# ---------------------------------------------------------------------------
def pristine_dif_dstrings():
    """The exact set of path 'd' strings build_logo classifies as diffraction,
    obtained by running the real classifier on the pristine file."""
    import shutil
    shutil.copyfile(PRISTINE, OUT)          # classify() reads the fixed path
    import build_logo
    import importlib
    importlib.reload(build_logo)
    _, groups = build_logo.classify()
    return {e.get("d") for e in groups["dif"]}


def resolve_styles(root):
    """Turn Illustrator's `class="stN"` + <style> rules into inline fills."""
    css = {}
    for st in root.iter(f"{{{SVG}}}style"):
        for m in re.finditer(r"\.(st\d+)\s*\{([^}]*)\}", st.text or ""):
            css[m.group(1)] = m.group(2)
    for el in root.iter():
        cls = el.get("class")
        if not cls:
            continue
        for name in cls.split():
            body = css.get(name, "")
            fm = re.search(r"fill:\s*([^;]+)", body)
            if fm:
                el.set("fill", fm.group(1).strip())
            sm = re.search(r"stroke:\s*([^;]+)", body)
            if sm:
                el.set("stroke", sm.group(1).strip())


def main():
    drop = pristine_dif_dstrings()
    print(f"pristine diffraction paths to drop: {len(drop)}")

    # pristine tree, minus its diffraction dots (raw, so build re-derives all
    # transforms itself); keep defs, the EELS <g>, structure, tomo, wordmark
    ptree = ET.parse(PRISTINE)
    proot = ptree.getroot()
    kept = []
    for el in list(proot):
        tag = el.tag.split("}")[-1]
        if tag == "path" and el.get("d") in drop:
            proot.remove(el)
        else:
            kept.append(tag)
    print(f"pristine kept top-level: {kept.count('path')} paths + "
          f"{kept.count('g')} g + defs")

    # corrected diffraction dots from the edited file, mapped into the
    # pristine frame with inline fills
    etree = ET.parse(EDITED)
    eroot = etree.getroot()
    resolve_styles(eroot)
    added = 0
    for el in eroot.iter(f"{{{SVG}}}path"):
        if el.get("stroke") and el.get("stroke") != "none":
            continue
        fill = el.get("fill")
        if fill is None and not el.get("class"):
            # no class and no fill attribute: SVG renders it black. The
            # hand-drawn centre beam is such a path -- don't drop it.
            fill = "#000000"
        if not fill or fill == "none" or fill.startswith("url"):
            continue
        pts = path_pts(el, extra=(TX, TY))
        if not pts:
            continue
        x0, y0, x1, y1 = bbox(pts)
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        area = (x1 - x0) * (y1 - y0)
        if not is_diffraction(cx, cy, area):
            continue
        new = ET.SubElement(proot, f"{{{SVG}}}path")
        new.set("fill", fill)
        # bake the frame offset into absolute coordinates; no transform attr,
        # so a CSS scale() on the site can't drop the positioning
        new.set("d", to_absolute(el.get("d"), TX, TY))
        # explicit group tag: this is the hand-corrected diffraction, so the
        # classifier must not re-guess it as a structure oxygen
        new.set("data-qem", "dif")
        added += 1
    print(f"corrected diffraction dots added: {added}")

    ptree.write(OUT, encoding="unicode", xml_declaration=True)
    print(f"wrote merged source -> {os.path.relpath(OUT)}")


if __name__ == "__main__":
    main()
