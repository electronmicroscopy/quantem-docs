"""Make a dark-mode variant of a logo PNG.

Two modes, both preserving transparency and anti-aliasing:

``reverse`` (default)
    Recolours near-black, near-neutral ink to near-white and leaves brand
    colours alone. Right for marks whose only dark element is black text,
    such as the Toyota Research Institute lockup.

``lighten``
    Lifts every dark pixel toward white while preserving hue. Gentle, but
    low contrast on a dark background.

``contrast``
    Sends one brand hue to white and makes everything else vivid: value is
    lifted hard and saturation boosted. Right for the DOE lockup, where the
    dark green wordmark becomes white while the seal keeps its gold ring
    and blue shield. Pick the hue window with ``--white-hue``.

Examples
--------
    python scripts/make_dark_logo.py assets/funding/tri_light.png \
        assets/funding/tri_dark.png

    python scripts/make_dark_logo.py assets/funding/doe_light.png \
        assets/funding/doe_dark.png --mode contrast --white-hue 0.30,0.50
"""

import argparse
import colorsys
import os
import sys

try:
    from PIL import Image
except ImportError:  # pragma: no cover
    sys.exit("Pillow is required: pip install pillow")

WHITE = (242, 242, 242)


def _luma(r, g, b):
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def reverse(px, w, h, threshold):
    """Neutral dark ink -> white; coloured pixels untouched."""
    n = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            if (r + g + b) / 3 < threshold and max(r, g, b) - min(r, g, b) < 40:
                px[x, y] = (*WHITE, a)
                n += 1
    return n


def lighten(px, w, h, threshold, base, span):
    """Lift dark pixels toward white, keeping hue."""
    n = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            lum = _luma(r, g, b)
            if lum < threshold:
                k = base + span * (1 - lum / threshold)
                px[x, y] = (
                    min(255, int(r + (255 - r) * k)),
                    min(255, int(g + (255 - g) * k)),
                    min(255, int(b + (255 - b) * k)),
                    a,
                )
                n += 1
    return n


def contrast(px, w, h, hue_lo, hue_hi, sat_min, base, gain, sat_gain):
    """Target hue -> white; everything else lifted and saturated."""
    n = 0
    for y in range(h):
        for x in range(w):
            r, g, b, a = px[x, y]
            if a == 0:
                continue
            hue, sat, val = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
            if hue_lo < hue < hue_hi and sat > sat_min:
                px[x, y] = (255, 255, 255, a)
            else:
                val = min(1.0, base + gain * val)
                sat = min(1.0, sat * sat_gain)
                rr, gg, bb = colorsys.hsv_to_rgb(hue, sat, val)
                px[x, y] = (int(rr * 255), int(gg * 255), int(bb * 255), a)
            n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("src")
    ap.add_argument("dst")
    ap.add_argument(
        "--mode", choices=("reverse", "lighten", "contrast"), default="reverse"
    )
    # contrast only: hue window (0-1) sent to white, and how saturated a
    # pixel must be to qualify
    ap.add_argument("--white-hue", default="0.30,0.50")
    ap.add_argument("--sat-min", type=float, default=0.45)
    ap.add_argument("--gain", type=float, default=0.85)
    ap.add_argument("--sat-gain", type=float, default=1.25)
    # reverse: how dark a neutral pixel must be to count as ink
    # lighten: luma below which pixels get lifted
    ap.add_argument("--threshold", type=float, default=None)
    # lighten only: minimum lift, and extra lift applied to the darkest pixels
    ap.add_argument("--base", type=float, default=0.40)
    ap.add_argument("--span", type=float, default=0.55)
    a = ap.parse_args()

    im = Image.open(a.src).convert("RGBA")
    px, (w, h) = im.load(), im.size
    if a.mode == "reverse":
        n = reverse(px, w, h, a.threshold if a.threshold is not None else 110)
    elif a.mode == "contrast":
        lo, hi = (float(v) for v in a.white_hue.split(","))
        n = contrast(px, w, h, lo, hi, a.sat_min, 0.35, a.gain, a.sat_gain)
    else:
        n = lighten(
            px, w, h, a.threshold if a.threshold is not None else 175,
            a.base, a.span,
        )
    im.save(a.dst)
    print(f"{os.path.basename(a.dst)}: {a.mode}, {n} of {w * h} px changed")


if __name__ == "__main__":
    main()
