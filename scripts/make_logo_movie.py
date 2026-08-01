"""Render the animated quantEM logo to a perfectly-looping mp4.

Every animation on the landing page has its own period, so a naive capture
would never loop. Instead this bakes a dedicated movie whose periods all
divide the loop length T, computes each animation's state analytically for
every frame (no browser, fully deterministic), rasterises with cairosvg,
and encodes with ffmpeg. Frame N equals frame 0, so playback loops seamlessly.

    DYLD_FALLBACK_LIBRARY_PATH=/opt/homebrew/lib \
        python scripts/make_logo_movie.py

Output: assets/quantem-logo.mp4  (white background, 60 fps, 12 s loop)
"""

import math
import os
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

import cairosvg

import build_logo as B

SVG = B.SVG
HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.path.normpath(os.path.join(HERE, "..", "assets"))

# ---- movie parameters -----------------------------------------------------
FPS = 60
T = 12.0                 # loop length in seconds
N = int(round(FPS * T))  # frames (frame N == frame 0, so not rendered)
OUT_W = 1560             # px; height follows the 460.8x266.4 aspect
INK = "#1A1A1A"          # dark ink on the white background

# periods (seconds); each divides T so the loop is exact
EELS_P = 6.0
STRUCT_P = 6.0
TOMO_P = 4.0
DIF_P = 6.0              # enlarged lobe sweeps once every DIF_P s (2x per loop)
# dot scale-swing amplitude is per-dot (grows with radius); see build_logo.dif_dots


def bump(frac):
    """Smooth 0 -> 1 -> 0 over one period (raised cosine), exactly periodic."""
    return (1.0 - math.cos(2.0 * math.pi * frac)) / 2.0


def parse_rgb(s):
    v = [float(x) for x in s[s.index("(") + 1:s.index(")")].replace("%", "").split(",")]
    return v  # percentages 0..100


def lerp_rgb(a, b, f):
    ca, cb = parse_rgb(a), parse_rgb(b)
    m = [ca[i] + (cb[i] - ca[i]) * f for i in range(3)]
    return f"rgb({m[0]:.4f}%, {m[1]:.4f}%, {m[2]:.4f}%)"


# ---------------------------------------------------------------------------
# Element state builders (return SVG fragment strings for a given time t)
# ---------------------------------------------------------------------------
def eels_defs_and_body(defs, eels_els, t):
    grad = [d for d in defs if d.tag.endswith("linearGradient")][0]
    stops = [(float(s.get("offset")), s.get("stop-color")) for s in grad]
    mat = B.parse_matrix(grad.get("gradientTransform"))
    scale = mat[0] * B.EXTEND
    k = 1.0 / B.EXTEND
    offset = (t / EELS_P) % 1.0
    parts = [
        f'<linearGradient id="linear-pattern-0" gradientUnits="userSpaceOnUse" '
        f'x1="0" y1="0" x2="1" y2="0" spreadMethod="repeat" '
        f'gradientTransform="matrix({scale:.4f}, 0, 0, {scale:.4f}, '
        f'{mat[4]:.4f}, {mat[5]:.4f}) translate({offset:.5f} 0)">'
    ]
    for off, color in stops:
        parts.append(f'<stop offset="{off * k:.6f}" stop-color="{color}"/>')
    for off, color in ((0.898, B.VIOLET), (0.949, B.PURPLE), (1.0, stops[0][1])):
        parts.append(f'<stop offset="{off}" stop-color="{color}"/>')
    parts.append("</linearGradient>")
    clips = "".join(
        ET.tostring(d, encoding="unicode")
        for d in defs if d.tag.endswith("clipPath")
    )
    body = B.serialize(eels_els)
    return f"<defs>{clips}{''.join(parts)}</defs>" + body


def dif_body(els, t):
    # A moon crescent (two enlarged lobes, ARC_SEP apart) travels around the
    # pattern: each dot is scaled about its own centre by 1 + amp*profile, so it
    # swells as each lobe sweeps over it. The crescent goes once around every
    # DIF_P seconds; amp/_arc_profile come from build_logo (it rides the outer
    # rings). The black centre spot never scales.
    w = 2.0 * math.pi * t / DIF_P
    out = []
    for el, cx, cy, frac, rho, isc in B.dif_dots(els):
        fill = el.get("fill")
        f = INK if fill == B.BLACK else fill
        d = el.get("d")
        if isc:
            out.append(f'<path d="{d}" fill="{f}"/>')
            continue
        theta = 2.0 * math.pi * frac
        s = 1.0 + B.DIR_AMP * B._cres_amp(rho, theta + w)  # +w: CCW sweep
        out.append(
            f'<g transform="translate({cx:.3f} {cy:.3f}) scale({s:.4f}) '
            f'translate({-cx:.3f} {-cy:.3f})"><path d="{d}" fill="{f}"/></g>'
        )
    return "".join(out)


def _struct_clusters(els):
    faces = [e for e in els if e.get("fill") in B.BLUES]
    oxygens = [e for e in els if e.get("fill") == B.RED]
    rest = [e for e in els if e.get("fill") not in B.BLUES
            and e.get("fill") != B.RED]
    a_est = sorted(math.sqrt((b[2] - b[0]) * (b[3] - b[1]))
                   for b in (B.bbox_of(f) for f in faces))[len(faces) // 2]
    vmap = {}
    for f in faces:
        for x, y in B.face_points(f):
            vmap.setdefault((round(x * 2) / 2, round(y * 2) / 2), []).append(f)

    def centroid(f):
        ps = B.face_points(f)
        return (sum(p[0] for p in ps) / len(ps),
                sum(p[1] for p in ps) / len(ps))

    centers = []
    for (vx, vy), fs in vmap.items():
        if len(fs) < 3:
            continue
        if max(math.hypot(c[0] - vx, c[1] - vy)
               for c in map(centroid, fs)) < 0.7 * a_est:
            centers.append((vx, vy))

    def nearest(p):
        return min(centers, key=lambda c: (c[0] - p[0]) ** 2 + (c[1] - p[1]) ** 2)

    cl_faces, cl_oxy, loose = {}, {}, []
    for f in faces:
        cl_faces.setdefault(nearest(centroid(f)), []).append(f)
    for ox in oxygens:
        c = nearest(B.center(B.bbox_of(ox)))
        oc = B.center(B.bbox_of(ox))
        if math.hypot(c[0] - oc[0], c[1] - oc[1]) < 1.35 * a_est:
            cl_oxy.setdefault(c, []).append(ox)
        else:
            loose.append(ox)

    u, v = (25.65, 8.35), (-8.35, 25.65)
    ox0, oy0 = centers[0]
    signed = {}
    for (ccx, ccy) in set(cl_faces) | set(cl_oxy):
        du = ((ccx - ox0) * u[0] + (ccy - oy0) * u[1]) / (u[0] ** 2 + u[1] ** 2)
        dv = ((ccx - ox0) * v[0] + (ccy - oy0) * v[1]) / (v[0] ** 2 + v[1] ** 2)
        signed[(ccx, ccy)] = 8 if (round(du) + round(dv)) % 2 == 0 else -8
    return cl_faces, cl_oxy, loose, signed, rest


def struct_body(cl_faces, cl_oxy, loose, signed, rest, t):
    ang = math.sin(2.0 * math.pi * t / STRUCT_P)

    def group(cxy, members):
        a = signed[cxy] * ang
        return (f'<g transform="rotate({a:.4f} {cxy[0]:.2f} {cxy[1]:.2f})">'
                f"{B.serialize(members)}</g>")

    # faces (bottom), A-sites/misc, then oxygens (top)
    faces_layer = "".join(group(c, m) for c, m in cl_faces.items())
    oxy_layer = "".join(group(c, m) for c, m in cl_oxy.items())
    oxy_layer += B.serialize(loose)
    return faces_layer + B.serialize(rest) + oxy_layer


def _tomo_setup(els):
    wedges = [e for e in els if not e.get("stroke") and e.get("fill") != B.BLACK]
    rays = [e for e in els if e.get("stroke")]
    dome = [e for e in els if e.get("fill") == B.BLACK]
    db = B.group_bbox(dome)
    cx, cy = (db[0] + db[2]) / 2, db[3]

    def angle(el):
        px, py = B.center(B.bbox_of(el))
        return math.degrees(math.atan2(cy - py, px - cx))

    wedges.sort(key=angle)
    return wedges, rays, dome, cx, cy


def tomo_body(setup, view, t):
    wedges, rays, dome, cx, cy = setup
    n = len(wedges)
    pitch = 180.0 / n
    colors = [w.get("fill") for w in wedges]
    frac = (t / TOMO_P) % 1.0

    def paint(el, col):
        e = ET.fromstring(ET.tostring(el))
        e.set("fill", col)
        return ET.tostring(e, encoding="unicode")

    visible = "".join(
        paint(w, lerp_rgb(colors[i], colors[i - 1] if i else colors[0], frac))
        for i, w in enumerate(wedges)
    )
    hidden = "".join(
        paint(w, lerp_rgb(colors[n - 1 - i], colors[n - i] if i else colors[n - 1], frac))
        for i, w in enumerate(wedges)
    )
    vx, vy, vw, _ = (float(x) for x in view.split())
    clip = (f'<clipPath id="horizon"><rect x="{vx}" y="{vy}" width="{vw}" '
            f'height="{cy - vy:.1f}"/></clipPath>')
    ray_svg = B.serialize(rays, INK)
    rot = frac * pitch
    wheel = (
        f'<g clip-path="url(#horizon)">'
        f'<g transform="rotate({rot:.4f} {cx:.1f} {cy:.1f})">'
        f"{visible}{ray_svg}"
        f'<g transform="rotate(180 {cx:.1f} {cy:.1f})">{hidden}{ray_svg}</g>'
        f"</g></g>"
    )
    return f"<defs>{clip}</defs>" + wheel + B.serialize(dome, INK)


# ---------------------------------------------------------------------------
def main():
    defs, g = B.classify()
    view = f"0 0 {B.W} {B.H}"
    struct_pre = _struct_clusters(g["struct"])
    tomo_pre = _tomo_setup(g["tomo"])
    text = B.serialize(g["text"], INK)

    # Render frames to the system temp dir, NOT inside the repo: writing 720
    # PNGs into the tree makes the MyST dev server's file watcher thrash
    # (constant rebuild/live-reload while a preview is open).
    tmp = os.path.join(tempfile.gettempdir(), "qem_movie_frames")
    if os.path.isdir(tmp):
        shutil.rmtree(tmp)
    os.makedirs(tmp)

    out_h = int(round(OUT_W * B.H / B.W))
    print(f"rendering {N} frames at {OUT_W}x{out_h} ({T}s @ {FPS}fps)")
    for k in range(N):
        t = k / FPS
        frame = (
            f'<svg xmlns="{SVG}" xmlns:xlink="http://www.w3.org/1999/xlink" '
            f'viewBox="{view}">'
            f'<rect x="0" y="0" width="{B.W}" height="{B.H}" fill="#ffffff"/>'
            f'<g>{eels_defs_and_body(defs, g["eels"], t)}</g>'
            f'<g>{dif_body(g["dif"], t)}</g>'
            f'<g>{struct_body(*struct_pre, t)}</g>'
            f'<g>{tomo_body(tomo_pre, view, t)}</g>'
            f"{text}</svg>"
        )
        cairosvg.svg2png(
            bytestring=frame.encode(),
            write_to=os.path.join(tmp, f"f{k:04d}.png"),
            output_width=OUT_W,
            output_height=out_h,
            background_color="white",
        )
        if k % 60 == 0:
            print(f"  frame {k}/{N}")

    out = os.path.join(ASSETS, "quantem-logo.mp4")
    subprocess.run([
        "ffmpeg", "-y", "-framerate", str(FPS),
        "-i", os.path.join(tmp, "f%04d.png"),
        "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "17",
        "-movflags", "+faststart", out,
    ], check=True)
    shutil.rmtree(tmp)
    print(f"wrote {out}")


if __name__ == "__main__":
    main()
