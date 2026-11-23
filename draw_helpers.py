"""Reusable drawing helpers for the front page (Pillow).

Every size in this module is in 2x drawing units: the page is drawn at
2048x2048 and downscaled once to 1024x1024, so callers pass measurements
already multiplied by 2 (the spec's numbers are in final 1024-px units).

Design-system pieces come from section 3 of the spec: the badge, the
three certainty icons, the lead tag chip, the picture-panel frame, the
rich-text wrapper, the sky gradient, and the small reused shapes (flame,
smoke, drone).  TextRegistry is the overlap/out-of-bounds checker from
section 2.
"""

import os

from PIL import ImageFont

from data import CERTAINTY_COLORS, RED

# ------------------------------------------------------------------- fonts
# Font directories, overridable by environment variable, with the spec's
# installed paths as defaults.  Resolved lazily on first use so a caller
# may set the variables before importing this module or before calling
# font().
_DEFAULT_DIRS = {
    "liberation": "/usr/share/fonts/truetype/liberation",
    "dejavu": "/usr/share/fonts/truetype/dejavu",
    "condensed": "/home/hatch/workspace/fonts/dejavu-fonts-ttf-2.37/ttf",
}
_ENV_DIRS = {
    "liberation": "LIBERATION_FONT_DIR",
    "dejavu": "DEJAVU_FONT_DIR",
    "condensed": "DEJAVU_COND_FONT_DIR",
}
_DIRS = None


def _font_dirs():
    global _DIRS
    if _DIRS is None:
        _DIRS = {
            key: os.environ.get(_ENV_DIRS[key], _DEFAULT_DIRS[key])
            for key in _DEFAULT_DIRS
        }
    return _DIRS


# Font key -> (directory key, file name).  Fallback files are tried in
# order when the first file is missing.
_FONT_FILES = {
    "serif_b": ("liberation", ["LiberationSerif-Bold.ttf"]),
    "serif": ("liberation", ["LiberationSerif-Regular.ttf"]),
    "serif_i": ("liberation", ["LiberationSerif-Italic.ttf"]),
    "sans_b": ("liberation", ["LiberationSans-Bold.ttf"]),
    "dserif_b": ("condensed", ["DejaVuSerifCondensed-Bold.ttf"]),
    "cond": ("condensed", ["DejaVuSansCondensed.ttf"]),
    "cond_b": ("condensed", ["DejaVuSansCondensed-Bold.ttf"]),
}
# Fallback: the plain (non-condensed) DejaVu files, same family.
_FONT_FALLBACK = {
    "dserif_b": ("dejavu", "DejaVuSerif-Bold.ttf"),
    "cond": ("dejavu", "DejaVuSans.ttf"),
    "cond_b": ("dejavu", "DejaVuSans-Bold.ttf"),
}

_FONT_CACHE = {}


def font(key, size):
    """Return a Pillow font for a font key and a size in px (2x units).

    Keys: serif_b, serif, serif_i, dserif_b, cond, cond_b, sans_b.
    The font directories come from LIBERATION_FONT_DIR, DEJAVU_FONT_DIR
    and DEJAVU_COND_FONT_DIR, defaulting to the installed paths.
    """
    size = max(1, int(round(size)))
    cached = _FONT_CACHE.get((key, size))
    if cached is not None:
        return cached
    if key not in _FONT_FILES:
        raise ValueError("unknown font key: %r (want one of %s)"
                         % (key, sorted(_FONT_FILES)))
    dirs = _font_dirs()
    dir_key, names = _FONT_FILES[key]
    tried = []
    for name in names:
        path = os.path.join(dirs[dir_key], name)
        tried.append(path)
        if os.path.isfile(path):
            loaded = ImageFont.truetype(path, size)
            _FONT_CACHE[(key, size)] = loaded
            return loaded
    fallback = _FONT_FALLBACK.get(key)
    if fallback is not None:
        path = os.path.join(dirs[fallback[0]], fallback[1])
        tried.append(path)
        if os.path.isfile(path):
            loaded = ImageFont.truetype(path, size)
            _FONT_CACHE[(key, size)] = loaded
            return loaded
    raise FileNotFoundError(
        "no font file for %r; tried: %s" % (key, ", ".join(tried)))


# ------------------------------------------------------------------- badge
def badge(draw, cx, cy, r, number, colour, outline=2, number_size=None):
    """Filled circle in a region colour with a thin white outline and a
    white bold condensed number centred inside.

    draw: an ImageDraw object.  cx, cy: centre.  r: radius.  number: the
    story number.  colour: the region colour.  outline: white outline
    width in px (2x units).  number_size: font size in px; defaults to
    about 1.25x the radius.
    """
    draw.ellipse([cx - r, cy - r, cx + r, cy + r],
                 fill=colour, outline=(255, 255, 255), width=outline)
    if number_size is None:
        number_size = max(8, int(round(r * 1.25)))
    draw.text((cx, cy), str(number), font=font("cond_b", number_size),
              fill=(255, 255, 255), anchor="mm")


def square_badge(draw, cx, cy, r, number, colour, outline=2,
                 number_size=None):
    """Filled SQUARE in a region colour with a thin white outline and a
    white bold condensed number centred inside. `r` is half the side
    length, so the square matches the circle badge's overall size.
    Used for the brief rows' numbers (the user's order); lead, card
    and map badges stay circular."""
    draw.rectangle([cx - r, cy - r, cx + r, cy + r],
                   fill=colour, outline=(255, 255, 255), width=outline)
    if number_size is None:
        number_size = max(8, int(round(r * 1.25)))
    draw.text((cx, cy), str(number), font=font("cond_b", number_size),
              fill=(255, 255, 255), anchor="mm")


# ---------------------------------------------------------- certainty icon
def _ink_offset(text, f):
    """Offset from a draw.text origin (anchor 'mm') to the centre of the
    glyph's TRUE ink, measured by rendering to a temp RGBA image and
    cropping to the alpha bounding box. PIL's textbbox over-reports this
    glyph's box (for U+201D it claims ~100 px tall when the true ink is
    ~43 px), so textbbox/anchor centring shoves the marks upward; this
    measures the real ink. Returns (dx, dy): drawing the text at
    (cx - dx, cy - dy) with anchor 'mm' centres the true ink at
    (cx, cy)."""
    from PIL import Image, ImageDraw
    size = f.size
    W = size * 4 + 40
    H = size * 4 + 40
    tmp = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    td = ImageDraw.Draw(tmp)
    ox, oy = W // 2, H // 2
    td.text((ox, oy), text, font=f, fill=(255, 255, 255, 255),
            anchor="mm")
    bbox = tmp.getbbox()
    if bbox is None:
        return (0.0, 0.0)
    return ((bbox[0] + bbox[2]) / 2 - ox,
            (bbox[1] + bbox[3]) / 2 - oy)


def certainty_icon(draw, cx, cy, r, kind):
    """Circle in the certainty colour, with the mark for the kind:
    CONFIRMED gets a white check mark (three-point polyline, rounded
    joints); STATED gets two white quotation-mark blobs side by side;
    UNVERIFIED gets a white bold "?"."""
    colour = CERTAINTY_COLORS[kind]
    draw.ellipse([cx - r, cy - r, cx + r, cy + r], fill=colour)
    if kind == "CONFIRMED":
        # Variant A (the user's choice): the guide's exact check
        # geometry — a white polyline through three points, stroke
        # width 0.30 r, rounded joints.
        width = max(2, int(round(r * 0.30)))
        draw.line([(cx - 0.50 * r, cy + 0.02 * r),
                   (cx - 0.12 * r, cy + 0.42 * r),
                   (cx + 0.55 * r, cy - 0.40 * r)],
                  fill=(255, 255, 255), width=width, joint="curve")
    elif kind == "STATED":
        # Variant A (the user's choice): a real serif quotation mark,
        # written first as text and then used as the icon. The "
        # (U+201D) glyph in Liberation Serif Bold is a proper serif
        # double quote ("99"), facing downward. Written in white at
        # ratio 2.5 and centred by the glyph's TRUE ink bounding box
        # (textbbox/anchor centring shifts this glyph upward), so the
        # marks sit truly in the middle of the amber circle.
        size = max(8, int(round(r * 2.5)))
        f = font("serif_b", size)
        icx, icy = _ink_offset("\u201d", f)
        draw.text((cx - icx, cy - icy), "\u201d", font=f,
                  fill=(255, 255, 255), anchor="mm")
    elif kind == "UNVERIFIED":
        # Variant B (the user's choice): a white "?" in Liberation
        # Serif Bold — the SAME font as the STATED quotation mark —
        # at ratio 1.8 (large and bold), centred by the glyph's TRUE
        # ink bounding box (textbbox/anchor centring shifts this
        # glyph upward), so the mark sits truly in the middle of the
        # red circle.
        size = max(8, int(round(r * 1.8)))
        f = font("serif_b", size)
        icx, icy = _ink_offset("?", f)
        draw.text((cx - icx, cy - icy), "?", font=f,
                  fill=(255, 255, 255), anchor="mm")
    else:
        raise ValueError("unknown certainty kind: %r" % (kind,))


# --------------------------------------------------------------- tag chip
def tag_chip(draw, right, y, kind, extra=None, size=20):
    """White rounded pill for a lead story, right-aligned to `right` and
    starting at top `y`.  A 1.1-px outline in the certainty colour, the
    certainty icon at the left end, then the word (and optional extra
    text such as "WHO STRUCK") in bold condensed in the certainty colour.
    `size` is the text size in px (2x units).  Returns the pill's
    bounding box (left, top, right, bottom)."""
    colour = CERTAINTY_COLORS[kind]
    word = kind + (" \u00b7 " + extra if extra else "")
    text_font = font("cond_b", size)
    text_w = int(round(text_font.getlength(word)))
    icon_r = int(round(size * 0.55))
    gap = 8
    pad_x = 10
    pad_y = 6
    pill_h = size + 2 * pad_y
    pill_w = pad_x + 2 * icon_r + gap + text_w + pad_x
    left = right - pill_w
    top = y
    draw.rounded_rectangle([left, top, right, top + pill_h],
                           radius=pill_h // 2, fill=(255, 255, 255),
                           outline=colour, width=2)
    icon_cx = left + pad_x + icon_r
    icon_cy = top + pill_h // 2
    certainty_icon(draw, icon_cx, icon_cy, icon_r, kind)
    draw.text((left + pad_x + 2 * icon_r + gap, icon_cy), word,
              font=text_font, fill=colour, anchor="lm")
    return (left, top, right, top + pill_h)


# ------------------------------------------------------------ picture panel
def panel_inner_rect(box, place_size, bar_height=None):
    """The rectangle where a panel's illustration goes: the whole panel
    box minus the dark bar along the bottom.  `bar_height` defaults to
    about 1.6x the place size (same default as panel_frame)."""
    x0, y0, x1, y1 = box
    if bar_height is None:
        bar_height = int(round(place_size * 1.6))
    return (x0, y0, x1, y1 - bar_height)


def panel_frame(draw, box, place, sources, label,
                place_size, sources_size, label_size, bar_height=None):
    """Draw the frame of a picture panel (section 3) and return the inner
    rectangle where the illustration goes (the area above the bar).

    Draw the illustration FIRST, in the rectangle panel_inner_rect()
    returns, and call this function AFTER it: the dark bar, the red
    label box and the outline are drawn on top of the illustration, so
    the label is never covered by it.

    box: (x0, y0, x1, y1) of the whole panel, 2x units.  place: place-bar
    text (white bold condensed, left).  sources: source names in the
    light grey-blue, right-aligned; pass None for leads, where the
    sources line sits below the picture instead.  label: red label text
    (white bold sans on RED, 5-px padding, top-right corner, 6 px in).
    The three sizes are font sizes in px (2x units).  bar_height: height
    of the dark bar; defaults to about 1.6x the place size.  A 0.8-px
    dark outline goes round the panel.
    """
    from data import INK, PANEL_BAR, PANEL_SOURCE

    x0, y0, x1, y1 = box
    if bar_height is None:
        bar_height = int(round(place_size * 1.6))
    # Dark bar along the bottom.
    draw.rectangle([x0, y1 - bar_height, x1, y1], fill=PANEL_BAR)
    # Place name at the left of the bar, vertically centred.
    pad = 8
    bar_cy = y1 - bar_height // 2
    draw.text((x0 + pad, bar_cy), place, font=font("cond_b", place_size),
              fill=(255, 255, 255), anchor="lm")
    # Sources right-aligned in the bar (cards only).
    if sources:
        draw.text((x1 - pad, bar_cy), sources, font=font("cond", sources_size),
                  fill=PANEL_SOURCE, anchor="rm")
    # Red label box at the top-right corner, 6 px in (12 in 2x units).
    inset = 12
    label_pad = 10
    label_font = font("sans_b", label_size)
    label_w = int(round(label_font.getlength(label)))
    bbox = draw.textbbox((0, 0), label, font=label_font)
    text_h = bbox[3] - bbox[1]
    lx1 = x1 - inset
    lx0 = lx1 - label_w - 2 * label_pad
    ly0 = y0 + inset
    ly1 = ly0 + text_h + 2 * label_pad
    draw.rectangle([lx0, ly0, lx1, ly1], fill=RED)
    draw.text(((lx0 + lx1) // 2, (ly0 + ly1) // 2), label,
              font=label_font, fill=(255, 255, 255), anchor="mm")
    # Dark outline round the whole panel.
    draw.rectangle([x0, y0, x1, y1], outline=INK, width=2)
    # The illustration goes in the area above the bar.
    return panel_inner_rect(box, place_size, bar_height)


# --------------------------------------------------------- rich-text wrap
def wrap_runs(runs, max_width, line_height):
    """Word-wrap runs of (text, font, colour) to a maximum width.

    Words keep the font and colour of the run they come from, so a bold
    lead-in can run on into regular text.  Returns (lines, total_height):
    each line is a (segments, width) pair, where segments is a list of
    (text, font, colour, x_offset, width) and width is the line's total
    width; total_height is len(lines) * line_height.
    """
    # Flatten the runs into words, each carrying its font and colour.
    words = []
    for text, text_font, colour in runs:
        for part in text.split(" "):
            if part == "":
                continue
            words.append((part, text_font, colour))
    lines = []
    current = []          # list of (text, font, colour, x_offset, width)
    current_w = 0
    for word, word_font, colour in words:
        word_w = word_font.getlength(word)
        space_w = 0
        if current:
            space_w = current[-1][1].getlength(" ")
        if current and current_w + space_w + word_w > max_width:
            lines.append((current, current_w))
            current = []
            current_w = 0
            space_w = 0
        current.append((word, word_font, colour, current_w + space_w, word_w))
        current_w = current_w + space_w + word_w
    if current:
        lines.append((current, current_w))
    return lines, len(lines) * line_height


def draw_wrapped(draw, lines, x, y, line_height):
    """Draw wrapped lines from wrap_runs at (x, y) with the given line
    height.  Returns the height used."""
    for index, (segments, _width) in enumerate(lines):
        ly = y + index * line_height
        for text, text_font, colour, x_offset, _seg_w in segments:
            draw.text((x + x_offset, ly), text, font=text_font,
                      fill=colour, anchor="la")
    return len(lines) * line_height


# ------------------------------------------------------------ sky gradient
def sky_gradient(draw, box, top_colour, bottom_colour, bands=24):
    """Fill a rectangle with a vertical gradient made of horizontal bands
    interpolated between two colours (section 7: 24 bands)."""
    x0, y0, x1, y1 = box
    height = y1 - y0
    if height <= 0:
        return
    band_h = height / bands
    for i in range(bands):
        t = (i + 0.5) / bands
        colour = tuple(
            round(top_colour[c] + (bottom_colour[c] - top_colour[c]) * t)
            for c in range(3))
        by0 = int(round(y0 + i * band_h))
        by1 = int(round(y0 + (i + 1) * band_h))
        draw.rectangle([x0, by0, x1, by1], fill=colour)


# ------------------------------------------------------------------- flame
def flame(draw, cx, cy, size):
    """An orange zig-zag flame with a yellow inner flame, centred at
    (cx, cy).  `size` is the half-height in px (2x units).  Orange
    rgb(232, 96, 28), yellow rgb(250, 196, 60)."""
    shape = [(0.00, -1.00), (0.28, -0.55), (0.16, -0.30), (0.45, -0.05),
             (0.28, 0.25), (0.48, 0.55), (0.28, 0.85), (0.00, 1.00),
             (-0.28, 0.85), (-0.48, 0.55), (-0.28, 0.25), (-0.45, -0.05),
             (-0.16, -0.30), (-0.28, -0.55)]
    outer = [(cx + dx * size, cy + dy * size) for dx, dy in shape]
    draw.polygon(outer, fill=(232, 96, 28))
    inner_scale = 0.55
    inner_cy = cy + 0.28 * size
    inner = [(cx + dx * size * inner_scale,
              inner_cy + dy * size * inner_scale) for dx, dy in shape]
    draw.polygon(inner, fill=(250, 196, 60))


# ------------------------------------------------------------------- smoke
def smoke(draw, x, y, size, direction=-1):
    """A plume of four overlapping grey circles rising diagonally from
    (x, y).  `size` is the base radius in px (2x units).  direction -1
    drifts up-left, +1 up-right.  Circles grow and lighten as they rise."""
    for i in range(4):
        r = size * (0.32 + 0.09 * i)
        sx = x + direction * i * 0.38 * size
        sy = y - i * 0.55 * size
        shade = 168 + 8 * i
        draw.ellipse([sx - r, sy - r, sx + r, sy + r],
                     fill=(shade, shade, shade))


# ------------------------------------------------------------------- drone
def drone(draw, cx, cy, size, colour=(20, 22, 28)):
    """A small dark arrow-like triangle with a crossbar, centred at
    (cx, cy).  `size` is the half-length in px (2x units).  The triangle
    points right; the crossbar sits just behind its nose."""
    s = size
    draw.polygon([(cx + 0.65 * s, cy),
                  (cx - 0.50 * s, cy - 0.38 * s),
                  (cx - 0.50 * s, cy + 0.38 * s)], fill=colour)
    draw.line([(cx - 0.05 * s, cy - 0.60 * s),
               (cx - 0.05 * s, cy + 0.60 * s)],
              fill=colour, width=max(1, int(round(0.14 * s))))


# ------------------------------------------------------------ text registry
class TextRegistry:
    """Records text bounding boxes with an element name, and reports
    problems: boxes from different elements overlapping by more than
    0.6 px in both axes, and boxes leaving the canvas."""

    def __init__(self):
        self.boxes = []  # list of (name, (x0, y0, x1, y1))

    def record(self, name, box):
        """Record one text box (x0, y0, x1, y1) under an element name."""
        self.boxes.append((name, tuple(box)))

    def problems(self, width, height):
        """List of problem descriptions for a canvas of width x height.
        Empty means no overlap and nothing out of bounds."""
        issues = []
        for name, (x0, y0, x1, y1) in self.boxes:
            if x0 < 0 or y0 < 0 or x1 > width or y1 > height:
                issues.append(
                    "%s: box (%.1f, %.1f, %.1f, %.1f) leaves the %dx%d canvas"
                    % (name, x0, y0, x1, y1, width, height))
        for i in range(len(self.boxes)):
            for j in range(i + 1, len(self.boxes)):
                name1, box1 = self.boxes[i]
                name2, box2 = self.boxes[j]
                if name1 == name2:
                    continue
                overlap_x = min(box1[2], box2[2]) - max(box1[0], box2[0])
                overlap_y = min(box1[3], box2[3]) - max(box1[1], box2[1])
                if overlap_x > 0.6 and overlap_y > 0.6:
                    issues.append(
                        "%s overlaps %s by %.1f x %.1f px"
                        % (name1, name2, overlap_x, overlap_y))
        return issues
