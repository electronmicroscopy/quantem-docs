"""Shared style for the quantEM architecture figure.

Vendored from the quantEM paper figure scripts (Open Color palette, gradient
boxes with white text and line icons, tinted bands with letterspaced labels),
so the documentation can regenerate the figure without the paper sources.
Changes for the web: SVG only (no PDF export), and the theme colors of the
container, foundations, and labels are passed in, so light and dark variants
can be written from one layout.
"""

import hashlib
import math

WIDTH = 460.8  # layout width in points, as in the paper
FONT = "Helvetica, Arial, sans-serif"

# Open Color shades used for each layer and stripe: (light, mid, dark, darkest)
PALETTE = {
    "gray":   ("#adb5bd", "#868e96", "#495057", "#343a40"),
    "black":  ("#495057", "#343a40", "#212529", "#000000"),
    "violet": ("#845ef7", "#7048e8", "#6741d9", "#5f3dc4"),
    "blue":   ("#74c0fc", "#339af0", "#228be6", "#1c7ed6"),
    "teal":   ("#20c997", "#0ca678", "#099268", "#087f5b"),
    "orange": ("#ff922b", "#f76707", "#e8590c", "#d9480f"),
    "pink":   ("#f06595", "#d6336c", "#c2255c", "#a61e4d"),
}
TINT = 0.07
EDGE = 0.35
STROKE_W = 1.1  # white icon line width (pt)


def esc(s):
    return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


class SVG:
    def __init__(self, width, height, label):
        self.w = width
        self.h = height
        self.label = label
        self.defs = {}
        self.layers = []  # (name, [elements])

    def layer(self, name):
        self.layers.append((name, []))
        return self.layers[-1][1]

    def grad(self, stops, horizontal=False, plateau=0.0):
        """Linear gradient from a list of colors, returned as url(#id).

        plateau > 0 holds each color flat over that fraction of its segment, which
        keeps blends between distant hues (e.g. teal to orange) short.
        """
        key = ("h" if horizontal else "d") + f"{plateau:.2f}" + "-".join(c.lstrip("#") for c in stops)
        gid = "g" + hashlib.md5(key.encode()).hexdigest()[:8]
        if gid not in self.defs:
            x2, y2 = ("1", "0") if horizontal else ("1", "1")
            n = len(stops) - 1
            if plateau > 0 and n > 0:
                k = len(stops)
                pos = []
                for i, c in enumerate(stops):
                    a = (i + 0.5 - plateau / 2) / k if i > 0 else 0.0
                    b = (i + 0.5 + plateau / 2) / k if i < k - 1 else 1.0
                    pos += [(a, c), (b, c)]
                st = "".join(f'<stop offset="{o:.3f}" stop-color="{c}"/>' for o, c in pos)
            else:
                st = "".join(f'<stop offset="{i / n:.3f}" stop-color="{c}"/>' for i, c in enumerate(stops))
            self.defs[gid] = f'<linearGradient id="{gid}" x1="0" y1="0" x2="{x2}" y2="{y2}">{st}</linearGradient>'
        return f"url(#{gid})"

    def render(self):
        out = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {self.w:.2f} {self.h:.2f}" '
            f'font-family="{FONT}" role="img" aria-label="{esc(self.label)}">',
            "<defs>" + "".join(self.defs.values()) + "</defs>",
        ]
        for name, elems in self.layers:
            out.append(f'<g id="layer-{name.lower().replace(" ", "-")}">')
            out.extend(elems)
            out.append("</g>")
        out.append("</svg>")
        return "\n".join(out) + "\n"

    def write(self, path):
        with open(path, "w") as f:
            f.write(self.render())
        print("wrote", path)


# ----- drawing primitives ---------------------------------------------------

def text(x, y, s, size=7, weight=400, fill="#212529", anchor="middle", spacing=0, opacity=1.0):
    w = ' font-weight="bold"' if weight >= 600 else ""
    ls = f' letter-spacing="{spacing}"' if spacing else ""
    op = f' fill-opacity="{opacity}"' if opacity < 1 else ""
    return (
        f'<text x="{x:.2f}" y="{y:.2f}" text-anchor="{anchor}" font-size="{size}"{w}{ls} '
        f'fill="{fill}"{op}>{esc(s)}</text>'
    )


def lines(cx, cy, rows, size=7, weight=400, fill="#fff", lead=1.18):
    """Centered block of text lines, vertically centered on cy."""
    n = len(rows)
    y0 = cy - (n - 1) * size * lead / 2 + size * 0.35
    return [text(cx, y0 + i * size * lead, r, size=size, weight=weight, fill=fill) for i, r in enumerate(rows)]


def shadow(x, y, w, h, rx, opacity=0.16):
    return (
        f'<rect x="{x:.2f}" y="{y + 1.0:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" '
        f'fill="#000" fill-opacity="{opacity}"/>'
    )


def box(x, y, w, h, fill, rx=5, title=None, sub=None, size=7, sub_size=5.6, fg="#fff", stroke=None,
        dashed=False, shade=True, stroke_w=0.6):
    """Rounded box with a vector shadow and centered text (white by default).
    dashed=True draws an outline only, for modules still in development."""
    dash = ' stroke-dasharray="2.4 1.8"' if dashed else ""
    st = f' stroke="{stroke}" stroke-width="{stroke_w}"{dash}' if stroke else ""
    out = [shadow(x, y, w, h, rx)] if shade else []
    out.append(f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{fill}"{st}/>')
    cx, cy = x + w / 2, y + h / 2
    if title is not None:
        rows = title if isinstance(title, list) else [title]
        if sub:
            subs = sub if isinstance(sub, list) else [sub]
            th = len(rows) * size * 1.18
            sh = len(subs) * sub_size * 1.25
            gap = 2.0
            top = cy - (th + gap + sh) / 2
            out += lines(cx, top + th / 2, rows, size=size, weight=700, fill=fg)
            ys = top + th + gap + sh / 2
            out += [
                t.replace(f'fill="{fg}"', f'fill="{fg}" fill-opacity="0.9"')
                for t in lines(cx, ys, subs, size=sub_size, lead=1.25, fill=fg)
            ]
        else:
            out += lines(cx, cy, rows, size=size, weight=500, fill=fg)
    return out


def band(x, y, w, h, color, label, rx=8, label_size=6.6, spacing=0.9, label_color=None):
    """Tinted container with a letterspaced uppercase label in the top-left corner."""
    out = [
        f'<rect x="{x:.2f}" y="{y:.2f}" width="{w:.2f}" height="{h:.2f}" rx="{rx}" fill="{color}" '
        f'fill-opacity="{TINT}" stroke="{color}" stroke-opacity="{EDGE}" stroke-width="0.6"/>'
    ]
    if label:
        out.append(
            f'<text x="{x + 8:.2f}" y="{y + 11:.2f}" font-size="{label_size}" font-weight="bold" '
            f'letter-spacing="{spacing}" fill="{label_color or color}">{esc(label)}</text>'
        )
    return out


# ----- icons (white line art, centered on cx, cy, about 12 pt across) --------

def _s(w=STROKE_W):
    return f'fill="none" stroke="#fff" stroke-width="{w}" stroke-linecap="round" stroke-linejoin="round"'


def icon(kind, cx, cy, s=1.0):
    k = s
    if kind == "imaging":
        return (
            f'<rect x="{cx - 6 * k:.2f}" y="{cy - 5 * k:.2f}" width="{12 * k:.2f}" height="{10 * k:.2f}" rx="{1.5 * k:.2f}" {_s()}/>'
            f'<path d="M{cx - 6 * k:.2f},{cy + 3 * k:.2f} L{cx - 2 * k:.2f},{cy - 1 * k:.2f} L{cx + 1 * k:.2f},{cy + 2 * k:.2f} L{cx + 3 * k:.2f},{cy:.2f} L{cx + 6 * k:.2f},{cy + 3 * k:.2f}" {_s()}/>'
        )
    if kind == "diffraction":
        out = f'<circle cx="{cx:.2f}" cy="{cy:.2f}" r="{1.9 * k:.2f}" fill="#fff"/>'
        for i in range(6):
            a = math.pi / 3 * i + math.pi / 6
            out += f'<circle cx="{cx + 5 * k * math.cos(a):.2f}" cy="{cy + 5 * k * math.sin(a):.2f}" r="{1.1 * k:.2f}" fill="#fff"/>'
        return out
    if kind == "tomography":
        return (
            f'<path d="M{cx - 3.5 * k:.2f},{cy - 1.5 * k:.2f} L{cx:.2f},{cy - 3.5 * k:.2f} L{cx + 3.5 * k:.2f},{cy - 1.5 * k:.2f} L{cx + 3.5 * k:.2f},{cy + 2.5 * k:.2f} L{cx:.2f},{cy + 4.5 * k:.2f} L{cx - 3.5 * k:.2f},{cy + 2.5 * k:.2f} Z" {_s()}/>'
            f'<path d="M{cx - 3.5 * k:.2f},{cy - 1.5 * k:.2f} L{cx:.2f},{cy + 0.5 * k:.2f} L{cx + 3.5 * k:.2f},{cy - 1.5 * k:.2f} M{cx:.2f},{cy + 0.5 * k:.2f} V{cy + 4.5 * k:.2f}" {_s(0.9)}/>'
            f'<path d="M{cx - 6.5 * k:.2f},{cy + 1 * k:.2f} A{6.5 * k:.2f},{6.5 * k:.2f} 0 0 1 {cx + 5 * k:.2f},{cy - 4.6 * k:.2f}" {_s(0.9)}/>'
        )
    if kind == "spectroscopy":
        return (
            f'<path d="M{cx - 6.5 * k:.2f},{cy + 4 * k:.2f} L{cx - 4 * k:.2f},{cy + 3 * k:.2f} L{cx - 2.6 * k:.2f},{cy - 4 * k:.2f} L{cx - 1.4 * k:.2f},{cy + 2 * k:.2f} L{cx + 1.5 * k:.2f},{cy + 1.5 * k:.2f} L{cx + 2.6 * k:.2f},{cy - 2 * k:.2f} L{cx + 3.6 * k:.2f},{cy + 2.6 * k:.2f} L{cx + 6.5 * k:.2f},{cy + 3.4 * k:.2f}" {_s()}/>'
        )
    if kind == "simulation":
        out = ""
        for dy in (-3.5, 0, 3.5):
            out += f'<path d="M{cx - 6 * k:.2f},{cy + dy * k + 1 * k:.2f} L{cx - 2 * k:.2f},{cy + dy * k - 1 * k:.2f} L{cx + 6 * k:.2f},{cy + dy * k - 1 * k:.2f} L{cx + 2 * k:.2f},{cy + dy * k + 1 * k:.2f} Z" {_s(0.9)}/>'
        return out
    if kind == "gradient":
        return (
            f'<path d="M{cx - 7 * k:.2f},{cy - 5 * k:.2f} Q{cx - 2 * k:.2f},{cy + 9 * k:.2f} {cx + 7 * k:.2f},{cy - 5 * k:.2f}" {_s()}/>'
            f'<circle cx="{cx - 4.6 * k:.2f}" cy="{cy - 1.2 * k:.2f}" r="{1.1 * k:.2f}" fill="#fff"/>'
            f'<circle cx="{cx - 2.2 * k:.2f}" cy="{cy + 1.4 * k:.2f}" r="{1.1 * k:.2f}" fill="#fff"/>'
            f'<circle cx="{cx - 0.2 * k:.2f}" cy="{cy + 2.0 * k:.2f}" r="{1.1 * k:.2f}" fill="#fff"/>'
        )
    if kind == "archive":
        return (
            f'<path d="M{cx - 5 * k:.2f},{cy - 6 * k:.2f} H{cx + 2.5 * k:.2f} L{cx + 5.5 * k:.2f},{cy - 3 * k:.2f} V{cy + 6 * k:.2f} H{cx - 5 * k:.2f} Z" {_s()}/>'
            f'<path d="M{cx - 2.6 * k:.2f},{cy - 1.5 * k:.2f} h{2.2 * k:.2f} M{cx + 0.4 * k:.2f},{cy - 1.5 * k:.2f} h{2.2 * k:.2f} M{cx - 2.6 * k:.2f},{cy + 1.2 * k:.2f} h{2.2 * k:.2f} M{cx + 0.4 * k:.2f},{cy + 1.2 * k:.2f} h{2.2 * k:.2f} M{cx - 2.6 * k:.2f},{cy + 3.9 * k:.2f} h{2.2 * k:.2f}" {_s(1.3)}/>'
        )
    raise ValueError(kind)
