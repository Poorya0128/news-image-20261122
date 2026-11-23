"""Flat illustrations for "The World in One Day" (make.fun news-image-20261122).

One drawing function per picture from spec section 7. Every function takes:

    img     -- a Pillow RGB image (the 2x canvas, 2048x2048)
    box     -- (x0, y0, x1, y1) in 2x units: the INNER drawing area of the
               picture panel, i.e. the area above the dark place bar. The
               frame, place bar and red label are drawn by another module.
    helpers -- the draw_helpers module (may be None).

Each function draws only with rectangles, polygons, ellipses, lines and
text, on a separate transparent layer that is pasted back clipped to its
box, so nothing can leak outside the panel. All sizes are fractions of the
box width/height, so the same code works at any scale. The main element of
each picture sits in the LEFT 60% of the panel so the red label at the top
right never covers it.

Helpers (sky gradient, flame, smoke, drone) are taken from the helpers
module when it provides them under those names with the calling convention
documented below; otherwise small local implementations with the same
convention are used. The local fallbacks are my own code, written here.

Calling convention for the helpers (matches draw_helpers.py):
    sky_gradient(draw, box, top_rgb, bottom_rgb)   -- 24-band vertical fill
    flame(draw, cx, cy, size)                     -- flame centred at
                                                    (cx, cy), size is the
                                                    half-height
    smoke(draw, x, y, size, direction=-1)         -- plume rising from
                                                    (x, y), size is the
                                                    base radius
    drone(draw, cx, cy, size, colour)             -- dark arrow + crossbar,
                                                    size is the half-length
"""

import math

from PIL import Image, ImageDraw, ImageFont

# ---------------------------------------------------------------------------
# Colours (spec section 3)
# ---------------------------------------------------------------------------

NAVY = (16, 34, 64)
GREY = (96, 98, 106)
INK = (20, 22, 28)
RED = (176, 22, 30)
GOLD = (250, 206, 102)
WHITE = (255, 255, 255)

FLAME_ORANGE = (232, 96, 28)
FLAME_YELLOW = (250, 196, 60)

# ---------------------------------------------------------------------------
# Fonts (spec section 2). Sizes are given as a fraction of the box height
# by the caller; these paths are the installed Liberation / DejaVu copies.
# ---------------------------------------------------------------------------

_FONT_PATHS = {
    "sans_b": [
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ],
    "cond_b": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ],
    "cond": [
        "/usr/share/fonts/truetype/dejavu/DejaVuSansCondensed.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ],
}

_font_cache = {}


def _font(role, px):
    """Load a font of the given role at px height (2x units), cached."""
    px = max(6, int(round(px)))
    key = (role, px)
    if key in _font_cache:
        return _font_cache[key]
    font = None
    for path in _FONT_PATHS.get(role, []):
        try:
            font = ImageFont.truetype(path, px)
            break
        except Exception:
            continue
    if font is None:
        font = ImageFont.load_default()
    _font_cache[key] = font
    return font


# ---------------------------------------------------------------------------
# Local helper implementations (used when draw_helpers does not provide them,
# or when its signature differs from the convention above).
# ---------------------------------------------------------------------------

def _sky_gradient(draw, box, top, bottom):
    """Vertical gradient: 24 horizontal bands interpolated top -> bottom."""
    x0, y0, x1, y1 = box
    bands = 24
    h = float(y1 - y0)
    for i in range(bands):
        t0 = i / bands
        t1 = (i + 1) / bands
        col = tuple(
            int(round(top[c] + (bottom[c] - top[c]) * (t0 + t1) / 2.0))
            for c in range(3)
        )
        ya = y0 + int(round(h * t0))
        yb = y0 + int(round(h * t1))
        if yb > ya:
            draw.rectangle([x0, ya, x1, yb], fill=col)


def _flame(draw, cx, cy, size):
    """Flame: orange zig-zag polygon with a yellow inner polygon.

    Centred at (cx, cy); `size` is the half-height, so the flame spans
    cy - size (tip) to cy + size (base)."""
    base_y = cy + size
    h = 2.0 * size
    w = 0.62 * h
    outer = [
        (cx - 0.50 * w, base_y),
        (cx - 0.42 * w, base_y - 0.42 * h),
        (cx - 0.55 * w, base_y - 0.55 * h),
        (cx - 0.28 * w, base_y - 0.72 * h),
        (cx - 0.34 * w, base_y - 0.86 * h),
        (cx, base_y - h),
        (cx + 0.30 * w, base_y - 0.80 * h),
        (cx + 0.46 * w, base_y - 0.58 * h),
        (cx + 0.38 * w, base_y - 0.40 * h),
        (cx + 0.50 * w, base_y),
    ]
    draw.polygon(outer, fill=FLAME_ORANGE)
    iw = 0.55 * w
    ih = 0.62 * h
    inner = [
        (cx - 0.50 * iw, base_y),
        (cx - 0.38 * iw, base_y - 0.38 * ih),
        (cx - 0.18 * iw, base_y - 0.62 * ih),
        (cx, base_y - ih),
        (cx + 0.30 * iw, base_y - 0.55 * ih),
        (cx + 0.42 * iw, base_y - 0.30 * ih),
        (cx + 0.50 * iw, base_y),
    ]
    draw.polygon(inner, fill=FLAME_YELLOW)


def _smoke(draw, x, y, size, direction=-1):
    """Smoke plume: 4 overlapping grey circles rising diagonally from
    (x, y). `size` is the base radius; direction -1 drifts up-left,
    +1 up-right."""
    s = size
    circles = [
        (x, y, 0.34 * s, (150, 150, 152)),
        (x + direction * 0.30 * s, y - 0.48 * s, 0.40 * s, (168, 168, 170)),
        (x + direction * 0.62 * s, y - 0.96 * s, 0.46 * s, (186, 186, 188)),
        (x + direction * 0.95 * s, y - 1.45 * s, 0.52 * s, (202, 202, 204)),
    ]
    for cx, cy, r, col in circles:
        draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=col)


def _drone(draw, cx, cy, size, colour=(22, 26, 36)):
    """Small dark arrow-like triangle with a crossbar."""
    s = size
    draw.polygon(
        [
            (cx + 0.55 * s, cy),
            (cx - 0.45 * s, cy - 0.38 * s),
            (cx - 0.20 * s, cy),
            (cx - 0.45 * s, cy + 0.38 * s),
        ],
        fill=colour,
    )
    draw.line(
        [(cx - 0.75 * s, cy), (cx + 0.75 * s, cy)],
        fill=colour,
        width=max(1, int(round(0.10 * s))),
    )
    draw.ellipse(
        [cx - 0.10 * s, cy - 0.10 * s, cx + 0.10 * s, cy + 0.10 * s],
        fill=colour,
    )


_LOCAL = {
    "sky_gradient": _sky_gradient,
    "flame": _flame,
    "smoke": _smoke,
    "drone": _drone,
}

try:
    import draw_helpers as _DH
except ImportError:  # helpers module written in parallel; may not exist yet
    _DH = None


def _get(helpers, name):
    """Return the shared helper if present, else the local implementation."""
    for mod in (helpers, _DH):
        if mod is not None:
            fn = getattr(mod, name, None)
            if callable(fn):
                return fn
    return _LOCAL[name]


def _call(helpers, name, *args):
    """Call a helper; fall back to the local one on a signature mismatch."""
    fn = _get(helpers, name)
    local = _LOCAL[name]
    if fn is local:
        return local(*args)
    try:
        return fn(*args)
    except TypeError:
        return local(*args)


# ---------------------------------------------------------------------------
# Layer plumbing: draw on a transparent layer, paste back clipped to the box.
# ---------------------------------------------------------------------------

def _begin(img, box):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    layer = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    return layer, ImageDraw.Draw(layer), w, h


def _end(img, layer, box):
    x0, y0, _, _ = box
    img.paste(layer, (x0, y0), layer)


def _stars(d, W, H, points, colour=(235, 238, 245)):
    for fx, fy, r in points:
        x, y = fx * W, fy * H
        d.ellipse([x - r, y - r, x + r, y + r], fill=colour)


def _dashed(d, x0, y, x1, colour, dash=6, gap=5, width=2):
    x = x0
    while x < x1:
        xa = min(x + dash, x1)
        d.line([(x, y), (xa, y)], fill=colour, width=width)
        x = xa + gap


# ---------------------------------------------------------------------------
# Leads
# ---------------------------------------------------------------------------

def cop(img, box, helpers=None):
    """COP31, no deal: globe + thermometer left, torn document right.
    Geometry per the construction guide, section 7 (page units x2)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (206, 230, 236), (238, 244, 240))

    # Globe: centre (x0+70, y0+h/2+4), radius 40; top cut by the panel.
    gx, gy, gr = 140, H / 2 + 8, 80
    d.ellipse([gx - gr, gy - gr, gx + gr, gy + gr], fill=(70, 140, 200))
    # Land, four circles, offsets from (gx, gy).
    for dx, dy, r in ((-28, -20, 32), (24, 12, 28), (-8, 40, 20), (36, -36, 18)):
        d.ellipse([gx + dx - r, gy + dy - r, gx + dx + r, gy + dy + r],
                  fill=(96, 176, 96))

    # Thermometer at tx = cx + 54.
    tx = gx + 108
    d.rounded_rectangle([tx - 10, gy - 76, tx + 10, gy + 44], radius=10,
                        fill=WHITE, outline=(150, 150, 150), width=2)
    d.rectangle([tx - 5, gy - 40, tx + 5, gy + 40], fill=(200, 40, 40))
    d.ellipse([tx - 18, gy + 32, tx + 18, gy + 68], fill=(200, 40, 40))

    # Torn document: px0=x0+150, py0=y0+6, px1=x1-16, py1=y1-18.
    px0, py0 = 300, 12
    px1, py1 = W - 32, H - 36
    mid = (px0 + px1) / 2
    left = [(px0, py0), (mid - 8, py0), (mid + 8, py0 + 36),
            (mid - 12, py0 + 76), (mid + 4, py0 + 120),
            (mid - 16, py1), (px0, py1)]
    right = [(mid + 12, py0 + 8), (px1, py0 + 16), (px1 - 8, py1 + 4),
             (mid - 4, py1 - 8), (mid + 16, py0 + 124),
             (mid, py0 + 80), (mid + 20, py0 + 40)]
    # Shadow first (same polygon shifted +2,+3), then the white polygon.
    d.polygon([(x + 4, y + 6) for x, y in left], fill=(190, 186, 176))
    d.polygon([(x + 4, y + 6) for x, y in right], fill=(190, 186, 176))
    d.polygon(left, fill=WHITE)
    d.polygon(right, fill=WHITE)

    d.text((px0 + 16, py0 + 16), "COP31", font=_font("sans_b", 24),
           fill=NAVY, anchor="la")
    d.text((px0 + 16, py0 + 46), "FINAL TEXT", font=_font("cond_b", 17),
           fill=GREY, anchor="la")
    # Grey text lines on the right half (left-half lines fall under the bar).
    d.line([(mid + 32, py0 + 52), (px1 - 20, py0 + 60)],
           fill=(200, 200, 200), width=4)
    d.line([(mid + 32, py0 + 72), (px1 - 20, py0 + 80)],
           fill=(200, 200, 200), width=4)
    _end(img, layer, box)


def dymer(img, box, helpers=None):
    """Night drone strike: drones over a 5-floor block with a collapsed gap.
    Geometry per the construction guide, section 7 (page units x2)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (14, 22, 46), (44, 52, 86))

    # 12 stars: x = x0+14+((i*53) mod (W-20)), y = y0+8+((i*29) mod 40).
    for i in range(12):
        sx = 14 + ((i * 53) % (W // 2 - 20))
        sy = 8 + ((i * 29) % 40)
        d.ellipse([2 * sx - 2, 2 * sy - 2, 2 * sx + 2, 2 * sy + 2],
                  fill=(220, 220, 240))

    # Six drones with dashed amber trails.
    for fx, fy in ((0.15, 0.22), (0.32, 0.12), (0.52, 0.18),
                   (0.72, 0.10), (0.86, 0.26), (0.62, 0.34)):
        x, y = fx * W, fy * H
        for k in range(4):
            d.line([(x + 20 + 14 * k, y - 6 - 4 * k),
                    (x + 26 + 14 * k, y - 8 - 4 * k)],
                   fill=(230, 180, 80), width=2)
        _call(helpers, "drone", d, x, y, 19, (210, 214, 226))

    # Block: bx0=x0+90, bx1=x1-90, by0=y0+0.38h.
    bx0, bx1, by0 = 180, W - 180, 0.38 * H
    d.rectangle([bx0, by0, bx1, H], fill=(150, 146, 140))
    # Exactly 5 floors x 9 columns of windows.
    fh = (H - by0 - 6) / 5
    for f in range(5):
        for c in range(9):
            wx = bx0 + 16 + c * (bx1 - bx0 - 32) / 9
            wy = by0 + 4 + f * fh
            lit = (7 * c + 3 * f) % 5 != 0
            col = (250, 214, 120) if lit else (60, 62, 72)
            d.rectangle([wx, wy, wx + 16, wy + 0.55 * fh], fill=col)
    # Collapse gap.
    g0 = bx0 + 0.40 * (bx1 - bx0)
    g1 = bx0 + 0.62 * (bx1 - bx0)
    d.polygon([(g0, by0 - 4), (g1, by0 - 4), (g1 - 8, by0 + 36),
               (g1 + 4, by0 + 68), (g1 - 16, H), (g0 + 12, H),
               (g0 - 4, by0 + 60), (g0 + 8, by0 + 24)], fill=(30, 36, 60))
    # Rubble triangles at the foot of the gap.
    for k in range(7):
        rx = g0 + 8 + k * (g1 - g0 - 16) / 7
        d.polygon([(rx, H), (rx + 12, H - 20 - 10 * (k % 3)), (rx + 24, H)],
                  fill=(110, 104, 98))
    # Flames (guide flame(x, y, s): base at (x, y); shared helper takes
    # the centre and half-height, so the centre sits one half-height
    # above the base).
    _call(helpers, "flame", d, g0 + 36, H - 42, 22)
    _call(helpers, "flame", d, g1 - 32, H - 30, 18)
    _end(img, layer, box)


def benghazi(img, box, helpers=None):
    """Capsized warship: dawn sky, sea, quay cranes right, bow raised.
    Geometry per the construction guide, section 7 (page units x2)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (236, 150, 92), (250, 214, 168))

    # Sea from 66% down, with light wave dashes.
    sy = 0.66 * H
    d.rectangle([0, sy, W, H], fill=(36, 82, 120))
    for k in range(6):
        wy = sy + 12 + 10 * (k % 2)
        d.line([(20 + 104 * k, wy), (68 + 104 * k, wy)],
               fill=(90, 140, 176), width=2)

    # Quay with two harbour cranes at the right edge.
    d.rectangle([W - 220, sy - 12, W, sy + 6], fill=(120, 106, 92))
    for cx in (W - 192, W - 120):
        d.line([(cx, sy - 12), (cx, 8)], fill=(70, 62, 56), width=5)
        d.line([(cx - 20, 10), (cx + 32, 10)], fill=(70, 62, 56), width=5)

    # Main element, the capsized hull. No hull number.
    bx = 0.40 * W
    d.polygon([(bx - 160, sy + 2), (bx + 68, sy + 2), (bx + 100, 8),
               (bx + 80, 4), (bx - 40, sy - 0.32 * H)], fill=(98, 104, 112))
    d.polygon([(bx + 68, sy + 2), (bx + 100, 8), (bx + 112, 14),
               (bx + 88, sy + 2)], fill=(70, 76, 84))
    # Smoke then flame at the stern (guide smoke/flame take a scale s;
    # the shared helpers take a pixel size, converted here).
    _call(helpers, "smoke", d, bx - 112, sy - 20, 31, 1)
    _call(helpers, "flame", d, bx - 120, sy - 13, 15)
    # Foam lines.
    for k in range(5):
        d.line([(bx - 168 + 48 * k, sy + 6), (bx - 140 + 48 * k, sy + 6)],
               fill=(200, 220, 236), width=2)
    _end(img, layer, box)


# ---------------------------------------------------------------------------
# Cards
# ---------------------------------------------------------------------------

def power(img, box, helpers=None):
    """Rolling power cuts in Iran: dark skyline, dead bulb left.
    Geometry per the construction guide, section 7 (page units x2)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (18, 24, 48), (40, 46, 74))

    # Skyline: 11 buildings, X = x0+60+12k.
    for k in range(11):
        X = 120 + 24 * k
        hk = H * (0.45 + 0.4 * ((37 * k) % 5) / 5)
        d.rectangle([X, H - hk, X + 20, H], fill=(34, 40, 62))
        # Windows, rows of 6 px (page) starting 3 px below the roof.
        for j in range(int(hk / 12)):
            lit = k < 5 and (j + k) % 3 != 0
            col = (250, 214, 120) if lit else (52, 58, 80)
            d.rectangle([X + 6, H - hk + 6 + 12 * j,
                         X + 14, H - hk + 12 + 12 * j], fill=col)

    # Main element, the dead bulb.
    cx, cy, r = 56, 0.42 * H, 0.30 * H
    d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(240, 236, 210))
    d.rectangle([cx - 0.45 * r, cy + 0.85 * r, cx + 0.45 * r, cy + 1.45 * r],
                fill=(160, 160, 168))
    d.line([(cx - 1.25 * r, cy + 1.25 * r), (cx + 1.25 * r, cy - 1.25 * r)],
           fill=RED, width=6)
    _end(img, layer, box)


def tanker(img, box, helpers=None):
    """UKMTO tanker incident: red tanker left, flame and smoke on deck.
    Geometry per the construction guide, section 7 (page units x2)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (176, 196, 214), (220, 228, 232))
    sy = 0.70 * H
    d.rectangle([0, sy, W, H], fill=(42, 92, 128))

    # Main element, the tanker (left of x0+82, clear of the label).
    t0, t1 = 16, 164
    d.polygon([(t0, sy - 14), (t1, sy - 14), (t1 - 16, sy + 10),
               (t0 + 12, sy + 10)], fill=(150, 40, 36))
    d.rectangle([t0 + 8, sy - 20, t1 - 44, sy - 14], fill=(80, 84, 92))
    d.rectangle([t1 - 44, sy - 42, t1 - 16, sy - 14], fill=(236, 236, 236))
    # Smoke then flame on deck.
    _call(helpers, "smoke", d, t0 + 48, sy - 40, 23, 1)
    _call(helpers, "flame", d, t0 + 52, sy - 32, 14)
    _end(img, layer, box)


def westbank(img, box, helpers=None):
    """Settlers torch homes: three sand houses, flames on roofs, smoke.
    Geometry per the construction guide, section 7 (page units x2)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (40, 34, 58), (96, 62, 60))

    # Three houses, width 32, heights 0.55h / 0.62h / 0.50h.
    for X, hf in ((16, 0.55), (92, 0.62), (168, 0.50)):
        hh = hf * H
        d.rectangle([X, H - hh, X + 64, H], fill=(196, 170, 130))
        d.polygon([(X - 4, H - hh), (X + 32, H - hh - 14), (X + 68, H - hh)],
                  fill=(150, 110, 80))
        d.rectangle([X + 26, H - 16, X + 38, H], fill=(90, 60, 40))
    # Flames on the roofs, smoke above.
    _call(helpers, "flame", d, 124, H - 0.62 * H - 18, 18)
    _call(helpers, "flame", d, 48, H - 0.55 * H - 13, 13)
    _call(helpers, "smoke", d, 120, 16, 18, 1)
    _end(img, layer, box)


def ebola(img, box, helpers=None):
    """Fighting stalls the Ebola response: red virus, white clinic.
    Geometry per the construction guide, section 7 (page units x2)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (236, 244, 240), (250, 250, 246))

    # Main element, the virus: 12 spikes at 0, 30, ..., 330 degrees.
    cx, cy, R = 52, H / 2, 0.30 * H
    for k in range(12):
        ang = math.radians(30 * k)
        x1 = cx + math.cos(ang) * R
        y1 = cy + math.sin(ang) * R
        x2 = cx + math.cos(ang) * 1.4 * R
        y2 = cy + math.sin(ang) * 1.4 * R
        d.line([(x1, y1), (x2, y2)], fill=(176, 30, 40), width=3)
        d.ellipse([x2 - 4, y2 - 4, x2 + 4, y2 + 4], fill=(176, 30, 40))
    d.ellipse([cx - R, cy - R, cx + R, cy + R], fill=(214, 70, 70))

    # Clinic with a red cross.
    hx = 132
    d.rectangle([hx - 32, H - 0.70 * H, hx + 32, H], fill=WHITE,
                outline=(160, 160, 160), width=2)
    d.rectangle([hx - 5, H - 0.62 * H, hx + 5, H - 0.18 * H],
                fill=(200, 30, 40))
    d.rectangle([hx - 18, H - 0.43 * H, hx + 18, H - 0.33 * H],
                fill=(200, 30, 40))
    _end(img, layer, box)


def khartoum(img, box, helpers=None):
    """Drones hit Khartoum and a UN site: UN building left, town right.
    Geometry per the construction guide, section 7 (page units x2)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (238, 200, 150), (246, 226, 190))

    # Town: 8 blocks.
    for k in range(8):
        X = 140 + 32 * k
        ht = H * (0.35 + 0.12 * (k % 3))
        d.rectangle([X, H - ht, X + 26, H], fill=(204, 160, 110))

    # Main element, the UN building.
    u0, u1 = 16, 124
    d.rectangle([u0, H - 0.62 * H, u1, H], fill=WHITE,
                outline=(150, 150, 150), width=1)
    d.rectangle([u0, H - 0.62 * H, u1, H - 0.40 * H], fill=(70, 140, 220))
    d.text(((u0 + u1) / 2, H - 0.20 * H), "UN", font=_font("sans_b", 19),
           fill=(70, 140, 220), anchor="mm")
    # Flame on the roof, then two drones (default dark colour, scale 1).
    _call(helpers, "flame", d, u1 - 16, H - 0.60 * H - 13, 13)
    _call(helpers, "drone", d, 0.36 * W, 0.22 * H + 6, 19, (30, 30, 36))
    _call(helpers, "drone", d, 0.47 * W, 0.12 * H + 6, 19, (30, 30, 36))
    _end(img, layer, box)


def istanbul(img, box, helpers=None):
    """March for press freedom: FREE PRESS banner, nine marchers, mosque.
    Geometry per the construction guide, section 7 (page units x2)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (190, 206, 226), (232, 236, 240))

    # Mosque (background, right): dome + two minarets.
    cx = 300
    d.pieslice([cx - 32, H - 0.75 * H, cx + 32, H + 12], 180, 360,
               fill=(140, 150, 166))
    for mx in (cx - 48, cx + 48):
        d.rectangle([mx - 3, H - 0.85 * H, mx + 3, H], fill=(140, 150, 166))

    # Main element, the banner.
    d.rectangle([12, 6, 184, 28], fill=WHITE, outline=(176, 30, 40), width=2)
    d.text((98, 17.2), "FREE PRESS", font=_font("sans_b", 17),
           fill=(176, 30, 40), anchor="mm")

    # Nine marchers.
    bodies = [(176, 30, 40), (40, 60, 110), (60, 60, 66)]
    for k in range(9):
        px = 20 + 20 * k
        d.ellipse([px - 6, 30, px + 6, 42], fill=(70, 56, 50))
        d.rectangle([px - 7, 42, px + 7, H], fill=bodies[k % 3])
    _end(img, layer, box)


def hk(img, box, helpers=None):
    """Record turnout in Hong Kong: towers right, red ballot box left.
    Geometry per the construction guide, section 7 (page units x2)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (226, 232, 240), (244, 244, 244))

    # Eight towers.
    for k, f in enumerate((0.50, 0.80, 0.45, 0.90, 0.60, 0.70, 0.40, 0.85)):
        X = 140 + 30 * k
        d.rectangle([X, H - f * H, X + 22, H], fill=(176, 190, 210))

    # Main element, the ballot box.
    bx = 76
    d.rectangle([bx - 52, H - 0.45 * H, bx + 52, H], fill=(180, 28, 40))
    d.rectangle([bx - 22, H - 0.45 * H - 2, bx + 22, H - 0.45 * H + 4],
                fill=(60, 14, 20))
    # Ballot going in, with a green tick.
    d.polygon([(bx - 18, 4), (bx + 24, 8), (bx + 20, H - 0.42 * H),
               (bx - 20, H - 0.44 * H)], fill=WHITE)
    d.line([(bx - 8, 0.30 * H), (bx, 0.42 * H), (bx + 12, 0.14 * H)],
           fill=(30, 120, 70), width=4, joint="curve")
    _end(img, layer, box)


def seoul(img, box, helpers=None):
    """Minister quits over AI cheating chaos: exam sheet, AI chip, slash.
    Geometry per the construction guide, section 7 (page units x2).
    The chip centre cx = x0+84 already reflects the Seoul fix (the chip
    sits left so the "AI" text is fully visible)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (232, 236, 246), (246, 246, 246))

    # Exam sheet, p0 = x0+8.
    p0 = 16
    d.rectangle([p0 + 4, 8, p0 + 92, H], fill=(196, 196, 196))
    d.rectangle([p0, 4, p0 + 88, H - 2], fill=WHITE)
    d.text((p0 + 10, 8), "EXAM", font=_font("cond_b", 15),
           fill=NAVY, anchor="la")
    for k in range(3):
        yy = 30 + 10 * k
        d.line([(p0 + 10, yy), (p0 + 76, yy)], fill=(200, 200, 200), width=2)

    # Main element, the AI chip.
    cx, cy = 168, H / 2
    d.rounded_rectangle([cx - 30, cy - 22, cx + 30, cy + 22], radius=6,
                        fill=(40, 50, 72))
    for k in range(3):
        px = cx - 18 + 18 * k
        d.line([(px, cy - 30), (px, cy - 22)], fill=(40, 50, 72), width=3)
        d.line([(px, cy + 22), (px, cy + 30)], fill=(40, 50, 72), width=3)
    d.text((cx, cy), "AI", font=_font("sans_b", 22),
           fill=(120, 200, 255), anchor="mm")
    # Red slash across the chip.
    d.line([(cx - 40, cy + 28), (cx + 40, cy - 28)], fill=RED, width=6)
    _end(img, layer, box)


def house(img, box, helpers=None):
    """US House: white Capitol left, five seat blocks right (3 blue, 2 red)."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (120, 160, 214), (176, 204, 236))

    # White Capitol: wide base with columns, drum, dome, mast.
    d.rectangle([0.06 * W, 0.70 * H, 0.48 * W, 0.74 * H], fill=WHITE,
                outline=(180, 180, 180), width=1)
    d.rectangle([0.06 * W, 0.74 * H, 0.48 * W, 0.95 * H], fill=WHITE,
                outline=(180, 180, 180), width=1)
    for cx in (0.12, 0.20, 0.28, 0.36):
        d.rectangle([cx * W, 0.76 * H, (cx + 0.02) * W, 0.93 * H],
                    fill=(190, 190, 190))
    d.rectangle([0.20 * W, 0.56 * H, 0.34 * W, 0.70 * H], fill=WHITE,
                outline=(180, 180, 180), width=1)
    d.pieslice([0.20 * W, 0.20 * H, 0.34 * W, 0.56 * H], 180, 360, fill=WHITE,
               outline=(180, 180, 180))
    d.rectangle([0.20 * W, 0.38 * H, 0.34 * W, 0.56 * H], fill=WHITE)
    d.line([(0.27 * W, 0.20 * H), (0.27 * W, 0.10 * H)], fill=(120, 120, 120),
           width=2)
    d.polygon([(0.27 * W, 0.10 * H), (0.27 * W, 0.16 * H), (0.315 * W, 0.13 * H)],
              fill=(190, 30, 35))

    # Five small seat blocks: three blue, two red.
    tops = (0.76, 0.72, 0.70, 0.72, 0.76)
    cols = [(40, 90, 190), (40, 90, 190), (40, 90, 190),
            (196, 50, 50), (196, 50, 50)]
    for i, (topf, col) in enumerate(zip(tops, cols)):
        cx = (0.62 + i * 0.08) * W
        d.rectangle([cx - 0.03 * W, topf * H, cx + 0.03 * W, 0.88 * H],
                    fill=col, outline=(20, 22, 28), width=1)
    _end(img, layer, box)


def tennis(img, box, helpers=None):
    """ATP Finals: gold trophy left, blue court with white lines right."""
    layer, d, W, H = _begin(img, box)
    _call(helpers, "sky_gradient", d, (0, 0, W, H), (16, 30, 64), (28, 50, 100))

    # Blue court with white lines on the right (trapezoid, in perspective).
    court = [(0.48 * W, 0.88 * H), (0.98 * W, 0.88 * H),
             (0.92 * W, 0.40 * H), (0.56 * W, 0.40 * H)]
    d.polygon(court, fill=(50, 110, 200))
    d.line(court + [court[0]], fill=WHITE, width=2, joint="curve")
    t = (0.62 - 0.40) / 0.48
    d.line([(0.56 * W + (0.48 - 0.56) * t * W, 0.62 * H),
            (0.92 * W + (0.98 - 0.92) * t * W, 0.62 * H)],
           fill=WHITE, width=2)
    d.line([(0.74 * W, 0.40 * H), (0.73 * W, 0.88 * H)], fill=WHITE, width=2)

    # Gold trophy on the left.
    d.pieslice([0.12 * W, 0.28 * H, 0.28 * W, 0.56 * H], 0, 180, fill=GOLD,
               outline=(200, 160, 60), width=1)
    d.arc([0.08 * W, 0.32 * H, 0.16 * W, 0.52 * H], 90, 270, fill=GOLD, width=2)
    d.arc([0.24 * W, 0.32 * H, 0.32 * W, 0.52 * H], 270, 90, fill=GOLD, width=2)
    d.rectangle([0.185 * W, 0.56 * H, 0.215 * W, 0.70 * H], fill=GOLD)
    d.rectangle([0.13 * W, 0.70 * H, 0.27 * W, 0.78 * H], fill=(200, 160, 60))
    d.rectangle([0.11 * W, 0.78 * H, 0.29 * W, 0.82 * H], fill=(170, 135, 50))

    # Yellow-green ball on the court.
    bx, by, br = 0.74 * W, 0.62 * H, 0.055 * H
    d.ellipse([bx - br, by - br, bx + br, by + br], fill=(200, 220, 60),
              outline=(150, 170, 40), width=1)
    d.arc([bx - br, by - br, bx + br, by + br], 200, 340, fill=WHITE, width=2)
    _end(img, layer, box)


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

PICTURES = {
    "cop": cop,
    "dymer": dymer,
    "benghazi": benghazi,
    "power": power,
    "tanker": tanker,
    "westbank": westbank,
    "ebola": ebola,
    "khartoum": khartoum,
    "istanbul": istanbul,
    "hk": hk,
    "seoul": seoul,
    "house": house,
    "tennis": tennis,
}
