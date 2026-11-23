"""Map drawing for "The World in One Day" (make.fun news-image-20261122).

Draws the small world map in Row A of the front page: ocean, land from
world_land.json, a dashed equator, region-coloured dots for stories 14+
and numbered badges for stories 1-13 with automatic de-conflicting
placement.

All sizes in the spec are in final 1024-px units. The page is drawn at
2x (2048x2048), so every function here receives a box in working units
and scales the spec constants by (box width / 240): the map box is
240 px wide in 1024 units. Nothing here assumes a fixed pixel size.

Story data comes in as a plain list of dicts:
    {"number": int, "region": str, "lon": float | None, "lat": float | None}
The real data lives in data.py (written by another agent); this module
never imports it, so it works with any list in that shape.
"""

import json
import math

from PIL import Image, ImageDraw

# --- Colours (spec section 3) -------------------------------------------
OCEAN = (222, 232, 241)
LAND = (206, 197, 178)
EQUATOR = (160, 176, 192)
OUTLINE = (150, 160, 172)
GREY = (96, 98, 106)
WHITE = (255, 255, 255)

REGION_COLORS = {
    "EUROPE": (34, 88, 166),
    "MIDDLE EAST": (190, 92, 14),
    "ASIA-PACIFIC": (18, 122, 132),
    "AFRICA": (40, 122, 72),
    "AMERICAS": (112, 60, 156),
    "WORLD": (88, 88, 96),
}

# --- Projection (spec section 8.2) --------------------------------------
LON_MIN, LON_MAX = -126.0, 180.0
LAT_TOP, LAT_BOTTOM = 61.0, -43.0
BOX_WIDTH_1024 = 240.0  # the map box is 240 px wide in 1024 units

# --- Sizes in 1024 units (spec section 8) --------------------------------
BADGE_R = 6.8        # numbered badge radius
BADGE_NUM = 8.8      # badge number text size
BADGE_OUTLINE = 1.2  # white outline of a badge (spec section 3)
DOT_R = 2.6          # dot radius for stories 14+
DOT_OUTLINE = 0.7    # white outline of a dot
PLACE_RINGS = (10, 14, 18, 22)  # offset rings tried for a badge
EDGE_MARGIN = 7.0    # badge must stay this far inside the box
BADGE_MIN_DIST = 14.0  # minimum centre distance between placed badges
TRUE_MIN_DIST = 8.0    # minimum distance to true points not yet placed
LEADER_W = 0.9       # leader line width
TRUE_DOT_R = 1.6     # dot drawn at the true point when a badge is offset
LAND_OUTLINE_W = 0.8
EQUATOR_DASH = 3.0   # dash length
EQUATOR_PERIOD = 6.0  # dash + gap

BADGE_MAX = 13  # stories 1..13 get numbered badges; 14+ get dots

DEFAULT_BOLD_FONT = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def load_land(path="world_land.json"):
    """Load the coastline rings: a list of rings of [lon, lat]."""
    with open(path, encoding="utf-8") as handle:
        return json.load(handle)


def _project(lon, lat, box, scale):
    """Equirectangular projection into working units for the given box."""
    x0, y0, _, _ = box
    x = x0 + (lon - LON_MIN) * scale
    y = y0 + (LAT_TOP - lat) * scale
    return x, y


def _scale_factor(box):
    """How many working units one 1024-unit pixel is."""
    x0, _, x1, _ = box
    return (x1 - x0) / BOX_WIDTH_1024


def _font(path, size):
    from PIL import ImageFont
    return ImageFont.truetype(path, max(1, int(round(size))))


def _place_badges(true_points, box, factor):
    """Place numbered badges so no two touch.

    true_points: {number: (x, y)} in working units.
    Most crowded pins first; try the true point, then offsets on rings
    of radius 10/14/18/22 (1024 units) in 8 directions. Accept the first
    spot that stays EDGE_MARGIN inside the box, is at least
    BADGE_MIN_DIST from every badge already placed, and at least
    TRUE_MIN_DIST from the true points of pins not yet placed.
    Returns {number: (x, y)} of chosen badge centres.
    """
    edge = EDGE_MARGIN * factor
    min_badge = BADGE_MIN_DIST * factor
    min_true = TRUE_MIN_DIST * factor
    x0, y0, x1, y1 = box

    def crowdedness(number):
        x, y = true_points[number]
        count = 0
        for other, (ox, oy) in true_points.items():
            if other == number:
                continue
            if math.hypot(x - ox, y - oy) <= 30.0 * factor:
                count += 1
        return count

    order = sorted(true_points, key=lambda n: (-crowdedness(n), n))
    placed = {}
    remaining = set(true_points)
    for number in order:
        remaining.discard(number)
        tx, ty = true_points[number]
        candidates = [(tx, ty)]
        for ring in PLACE_RINGS:
            radius = ring * factor
            for step in range(8):
                angle = math.radians(step * 45.0)
                candidates.append(
                    (tx + radius * math.cos(angle),
                     ty + radius * math.sin(angle)))
        chosen = None
        for cx, cy in candidates:
            # The badge centre stays EDGE_MARGIN inside the box.
            if not (x0 + edge <= cx <= x1 - edge):
                continue
            if not (y0 + edge <= cy <= y1 - edge):
                continue
            if any(math.hypot(cx - px, cy - py) < min_badge
                   for px, py in placed.values()):
                continue
            if any(math.hypot(cx - true_points[o][0],
                              cy - true_points[o][1]) < min_true
                   for o in remaining):
                continue
            chosen = (cx, cy)
            break
        if chosen is None:
            # Fallback: the tried spot furthest from badges already placed.
            best = None
            best_score = -1.0
            for cx, cy in candidates:
                score = min(
                    (math.hypot(cx - px, cy - py)
                     for px, py in placed.values()),
                    default=1e9)
                if score > best_score:
                    best_score = score
                    best = (cx, cy)
            chosen = best if best is not None else (tx, ty)
        placed[number] = chosen
    return placed


def draw_map(img, box, land, stories, font_bold=None):
    """Draw the world map with pins into img inside box (working units).

    land: list of rings of [lon, lat] (see load_land).
    stories: list of dicts with number, region, lon, lat.
    font_bold: path to a bold font for badge numbers (default DejaVu Sans Bold).
    Returns {story number: (x, y)} badge centres for stories 1..13.
    """
    x0, y0, x1, y1 = box
    width = int(round(x1 - x0))
    height = int(round(y1 - y0))
    factor = _scale_factor(box)
    scale = (x1 - x0) / (LON_MAX - LON_MIN)

    # --- Ocean, land, equator on a box-sized layer (clips to the box) ---
    layer = Image.new("RGB", (width, height), OCEAN)
    draw = ImageDraw.Draw(layer)
    outline_w = max(1, int(round(LAND_OUTLINE_W * factor)))
    for ring in land:
        points = []
        for lon, lat in ring:
            px, py = _project(lon, lat, box, scale)
            points.append((px - x0, py - y0))
        if len(points) < 3:
            continue
        draw.polygon(points, fill=LAND)
        draw.line(points + [points[0]], fill=OUTLINE, width=outline_w)
    # Dashed equator (lat 0): dashes of EQUATOR_DASH every EQUATOR_PERIOD.
    _, eq_y = _project(0.0, 0.0, box, scale)
    eq_y -= y0
    dash = EQUATOR_DASH * factor
    period = EQUATOR_PERIOD * factor
    pos = 0.0
    while pos < width:
        end = min(pos + dash, width)
        draw.line([(pos, eq_y), (end, eq_y)], fill=EQUATOR, width=1)
        pos += period
    img.paste(layer, (int(round(x0)), int(round(y0))))

    draw = ImageDraw.Draw(img)
    badge_font = _font(font_bold or DEFAULT_BOLD_FONT, BADGE_NUM * factor)
    badge_r = BADGE_R * factor
    dot_r = DOT_R * factor
    dot_outline = max(1, int(round(DOT_OUTLINE * factor)))

    # --- Dots for stories 14+ -------------------------------------------
    for story in stories:
        if story["number"] <= BADGE_MAX:
            continue
        lon, lat = story.get("lon"), story.get("lat")
        if lon is None or lat is None:
            continue
        cx, cy = _project(lon, lat, box, scale)
        colour = REGION_COLORS[story["region"]]
        draw.ellipse([cx - dot_r - dot_outline, cy - dot_r - dot_outline,
                      cx + dot_r + dot_outline, cy + dot_r + dot_outline],
                     fill=WHITE)
        draw.ellipse([cx - dot_r, cy - dot_r, cx + dot_r, cy + dot_r],
                     fill=colour)

    # --- Numbered badges for stories 1..13 ------------------------------
    true_points = {}
    for story in stories:
        if story["number"] > BADGE_MAX:
            continue
        lon, lat = story.get("lon"), story.get("lat")
        if lon is None or lat is None:
            continue
        true_points[story["number"]] = _project(lon, lat, box, scale)
    placed = _place_badges(true_points, box, factor)

    leader_w = max(1, int(round(LEADER_W * factor)))
    true_dot_r = TRUE_DOT_R * factor
    badge_outline = max(1, int(round(BADGE_OUTLINE * factor)))
    for story in stories:
        number = story["number"]
        if number not in placed:
            continue
        colour = REGION_COLORS[story["region"]]
        cx, cy = placed[number]
        tx, ty = true_points[number]
        if math.hypot(cx - tx, cy - ty) > 0.5 * factor:
            # Offset badge: leader line plus a dot at the true point.
            draw.line([(cx, cy), (tx, ty)], fill=colour, width=leader_w)
            draw.ellipse([tx - true_dot_r, ty - true_dot_r,
                          tx + true_dot_r, ty + true_dot_r], fill=colour)
        draw.ellipse([cx - badge_r - badge_outline,
                      cy - badge_r - badge_outline,
                      cx + badge_r + badge_outline,
                      cy + badge_r + badge_outline], fill=WHITE)
        draw.ellipse([cx - badge_r, cy - badge_r,
                      cx + badge_r, cy + badge_r], fill=colour)
        label = str(number)
        bbox = draw.textbbox((0, 0), label, font=badge_font)
        tw = bbox[2] - bbox[0]
        th = bbox[3] - bbox[1]
        draw.text((cx - tw / 2 - bbox[0], cy - th / 2 - bbox[1]),
                  label, font=badge_font, fill=WHITE)
    return placed


def map_key_lines(stories):
    """The two key strings printed under the map.

    Line 1: a grey badge "7" (drawn by the caller before this text) +
    "= stories {a}–{b} (cards)", then a grey dot + "= stories {c}–{N}
    (list)". The "●" in the returned string is the grey dot glyph.
    Line 2: "Colour = region, as in the bar above. No pin: {numbers without
    coordinates}." Ranges and the no-pin list are computed from the
    story data, never typed by hand.
    Returns (line1, line2).
    """
    numbers = sorted(s["number"] for s in stories)
    badge_nums = [n for n in numbers if n <= BADGE_MAX]
    dot_nums = [n for n in numbers if n > BADGE_MAX]
    no_pin = [s["number"] for s in stories
              if s.get("lon") is None or s.get("lat") is None]
    line1 = ("= stories %d–%d (cards)    \u25cf = stories %d–%d (list)"
             % (min(badge_nums), max(badge_nums),
                min(dot_nums), max(dot_nums)))
    line2 = ("Colour = region, as in the bar above. No pin: %s."
             % (", ".join(str(n) for n in sorted(no_pin)) or "none"))
    return line1, line2
