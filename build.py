"""build.py -- draws "The World in One Day", Sunday 22 November 2026.

Front page for the make.fun bounty news-image-20261122: 42 stories on one
1024x1024 page.  Drawn at 2x (2048x2048) with Pillow, then downscaled once
with LANCZOS to 1024x1024.  Every measurement in the spec is in final
1024-px units; this file multiplies by S = 2 when drawing.

Content comes from data.py (stories, timeline, numbers, boxes).  Reusable
pieces come from draw_helpers.py (fonts, badge, certainty icon, tag chip,
picture-panel frame, rich-text wrap, TextRegistry).  The 13 flat
illustrations come from pictures.py.  The map comes from map_draw.py.

Deterministic: no randomness, no clock, no network.  Fixed fonts, fixed
data.  Run twice and the two entry.png files are byte-identical.

Usage:
    python3 build.py            # full page -> entry.png next to this file
    python3 build.py --upto 3   # stages 1..3 only -> /tmp/stage3.png
"""

import argparse
import hashlib
import json
import math
import os
import sys

from PIL import Image, ImageDraw

BASE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE)

import data
import draw_helpers as H
import map_draw
import pictures

S = 2                      # draw scale: 2x canvas
W = 1024                   # final width in spec units
Hh = 1024                  # final height in spec units
MARGIN = 12                # left/right margin (spec units)
RIGHT = 1012               # right content edge (spec units)

# Text registry: every text box drawn is recorded; problems() must be
# empty before the build is accepted.
reg = H.TextRegistry()


def X(v):
    """A spec-unit value -> 2x drawing units."""
    return v * S


def text(draw, name, x, y, s, key, size, fill, anchor="la"):
    """Draw text at spec-unit (x, y); record its bbox (2x units).

    x, y are in spec units; size is the spec-unit font size.  The
    ImageDraw textbbox call is the source of the recorded box, so the
    registry sees exactly what was drawn.
    """
    f = H.font(key, size * S)
    bbox = draw.textbbox((x * S, y * S), s, font=f, anchor=anchor)
    draw.text((x * S, y * S), s, font=f, fill=fill, anchor=anchor)
    reg.record(name, bbox)
    return bbox


def text_w(key, size, s):
    """Width of a string in spec units."""
    return H.font(key, size * S).getlength(s) / S


def record_text(draw, name, x, y, s, key, size, anchor="la"):
    """Record (without drawing) the bbox of text drawn by a helper.

    x, y in spec units; size in spec units.  Used for text that a helper
    (panel_frame, badge, tag_chip, draw_map) draws, so the registry still
    sees it.  The caller must pass the same coordinates, font and anchor
    the helper used.
    """
    f = H.font(key, size * S)
    bbox = draw.textbbox((x * S, y * S), s, font=f, anchor=anchor)
    reg.record(name, bbox)
    return bbox


def record_lines(draw, name, lines, x, y, line_height):
    """Draw wrapped lines (from wrap_runs) and record every word's box.

    lines: the (segments, width) pairs wrap_runs returns.  x, y in spec
    units; line_height in spec units.  Each word is drawn with anchor
    "la" at (x + x_offset, y + index * line_height).  All words share
    one element name, so the registry never flags a block against
    itself.  Returns the height used (spec units).
    """
    for index, (segments, _width) in enumerate(lines):
        ly = y + index * line_height
        for word, word_font, colour, x_offset, _seg_w in segments:
            # x_offset is already in 2x units (wrap_runs measured with
            # 2x fonts); only the spec-unit line origin needs scaling.
            wx = x * S + x_offset
            bbox = draw.textbbox((wx, ly * S), word,
                                 font=word_font, anchor="la")
            draw.text((wx, ly * S), word,
                      font=word_font, fill=colour, anchor="la")
            reg.record(name, bbox)
    return len(lines) * line_height


def wrap(text_runs, max_width, line_height):
    """wrap_runs with spec-unit sizes: fonts are already 2x, widths are
    converted.  Returns (lines, total_height) in spec units."""
    lines, total = H.wrap_runs(text_runs, max_width * S, line_height * S)
    return lines, total / S


def rect(draw, x0, y0, x1, y1, **kw):
    """Rectangle with spec-unit coordinates."""
    draw.rectangle([x0 * S, y0 * S, x1 * S, y1 * S], **kw)


def rule(draw, y, x0=MARGIN, x1=RIGHT, thickness=1.0, fill=None):
    """A horizontal rule at spec-unit y, thickness in spec units."""
    if fill is None:
        fill = data.INK
    draw.rectangle([x0 * S, y * S, x1 * S, (y + thickness) * S], fill=fill)


# ------------------------------------------------------------------ stage 1
def stage_top(draw):
    """Kicker, date masthead, double rule, deck line, background bar."""
    n_regions = len(data.REGIONS)
    n_topics = len(data.TOPICS)
    kicker_left = "THE WORLD IN ONE DAY \u00b7 CLOSING EDITION"
    kicker_right = ("%d STORIES \u00b7 %d REGIONS \u00b7 %d TOPICS \u00b7 TIMES IN UTC"
                    % (data.N, n_regions, n_topics))
    text(draw, "kicker_left", MARGIN, 4, kicker_left, "cond_b", 12.5, data.RED)
    text(draw, "kicker_right", RIGHT, 4, kicker_right, "cond_b", 12.5,
         data.INK, anchor="ra")

    text(draw, "masthead", 512, 19, "Sunday 22 November 2026",
         "serif_b", 72, data.INK, anchor="ma")

    rule(draw, 98, thickness=2.2)
    rule(draw, 101, thickness=0.7)

    text(draw, "deck", 512, 104, data.DECK_LINE, "serif_i", 17, data.RED,
         anchor="ma")

    # Background bar: 18 px high, label then text, vertically centred.
    rect(draw, MARGIN, 124, RIGHT, 142, fill=data.BACKGROUND_FILL)
    bar_cy = 124 + 9
    text(draw, "background_label", 14, bar_cy, "BACKGROUND", "cond_b", 11.5,
         data.NAVY, anchor="lm")
    label_w = text_w("cond_b", 11.5, "BACKGROUND")
    text(draw, "background_text", 14 + label_w + 8, bar_cy,
         data.BACKGROUND_TEXT, "cond", 11.5, data.INK, anchor="lm")
    return 142


# ------------------------------------------------------------------ stage 2
def stage_timeline_numbers(draw):
    """Timeline (y=145) and the numbers strip (y=189)."""
    # --- Timeline ---
    y = 145
    # Red box at the left: "THE DAY" / "UTC".
    rect(draw, MARGIN, y, 76, y + 40, fill=data.RED)
    text(draw, "timeline_box1", 44, y + 7, "THE DAY", "cond_b", 11.5,
         data.WHITE, anchor="ma")
    text(draw, "timeline_box2", 44, y + 20, "UTC", "cond_b", 11.5,
         data.WHITE, anchor="ma")
    # RULE line at y + 9, drawn first so the dots and times sit on it.
    draw.rectangle([84 * S, (y + 9) * S, RIGHT * S, (y + 9) * S + 2],
                   fill=data.RULE)
    col_w = (RIGHT - 84) / 8.0
    for i, (time_s, event, detail) in enumerate(data.TIMELINE):
        col_x = 84 + i * col_w
        text_x = col_x + 12
        # Red dot at the left, centred on the rule line.
        draw.ellipse([(col_x) * S, (y + 9 - 4) * S,
                      (col_x + 8) * S, (y + 9 + 4) * S], fill=data.RED)
        text(draw, "timeline_time_%d" % i, text_x, y + 1, time_s,
             "serif_b", 15, data.RED)
        text(draw, "timeline_event_%d" % i, text_x, y + 17, event,
             "cond_b", 10.8, data.INK)
        text(draw, "timeline_detail_%d" % i, text_x, y + 29, detail,
             "cond", 10.8, data.GREY)

    # Thin RULE separator between the timeline block and the numbers
    # strip: the timeline detail text ends at about y=185 and the
    # numbers' big figures start at about y=187, so y=186 sits in
    # the gap and touches neither.
    rule(draw, 186, thickness=0.8, fill=data.RULE)

    # --- Numbers strip ---
    y = 189
    rect(draw, MARGIN, y, 76, y + 36, fill=data.NAVY)
    text(draw, "numbers_box1", 44, y + 5, "THE DAY IN", "cond_b", 11.5,
         data.WHITE, anchor="ma")
    text(draw, "numbers_box2", 44, y + 18, "NUMBERS", "cond_b", 11.5,
         data.WHITE, anchor="ma")
    col_w = (RIGHT - 84) / 6.0
    for i, (figure, label) in enumerate(data.NUMBERS):
        cx = 84 + (i + 0.5) * col_w
        text(draw, "numbers_fig_%d" % i, cx, y - 2, figure, "serif_b", 28,
             data.RED, anchor="ma")
        text(draw, "numbers_label_%d" % i, cx, y + 23, label, "cond", 10.8,
             data.GREY, anchor="ma")
        if i:
            # Thin RULE separator between columns.
            sx = 84 + i * col_w
            draw.rectangle([sx * S, y * S, sx * S + 1, (y + 36) * S],
                           fill=data.RULE)
    rule(draw, y + 41, thickness=0.9)

    # --- Region bar: a full-width coloured strip, one segment per region,
    # its width in proportion to that region's story count.  The top
    # entries show coverage this way; our coverage table buried the same
    # numbers at the bottom of the page.  18 px tall, 2 px below the
    # numbers rule; the leads start 2 px below the bar.
    bar_y = y + 43
    bar_h = 18
    totals = data.region_totals()
    total = sum(totals.values())
    avail = RIGHT - MARGIN
    labels = {r: "%s %d" % (r, totals[r]) for r in data.REGIONS}
    raw = {r: avail * totals[r] / total for r in data.REGIONS}
    min_w = {r: text_w("cond_b", 10, labels[r]) + 10 for r in data.REGIONS}
    widths = {r: max(raw[r], min_w[r]) for r in data.REGIONS}
    over = sum(widths.values()) - avail
    if over > 0:
        slack = {r: widths[r] - min_w[r] for r in data.REGIONS}
        total_slack = sum(slack.values())
        for r in data.REGIONS:
            widths[r] -= over * slack[r] / total_slack
    # Integer boundaries (last pinned to RIGHT) so the segments tile
    # exactly with no gaps.
    bounds = [MARGIN]
    acc = 0.0
    for r in data.REGIONS[:-1]:
        acc += widths[r]
        bounds.append(int(round(MARGIN + acc)))
    bounds.append(RIGHT)
    for i, r in enumerate(data.REGIONS):
        x0, x1 = bounds[i], bounds[i + 1]
        rect(draw, x0, bar_y, x1, bar_y + bar_h,
             fill=data.REGION_COLORS[r])
        text(draw, "region_bar_%s" % r, (x0 + x1) / 2, bar_y + bar_h / 2,
             labels[r], "cond_b", 10, data.WHITE, anchor="mm")
    return y + 41


# ------------------------------------------- recording helper-drawn text
def record_box(name, bbox):
    """Record a bbox that is already in 2x drawing units."""
    reg.record(name, bbox)


def record_panel_texts(draw, name, box2, place, sources, label,
                       place_size2, sources_size2, label_size2):
    """Record the text boxes panel_frame draws (place, sources, label).

    box2 and the sizes are in 2x units, exactly as panel_frame takes
    them.  The geometry below mirrors panel_frame's own arithmetic
    (bar 1.6x the place size, 8-px side padding, label inset 12 px with
    10-px padding), so the recorded boxes are the drawn ones.
    """
    x0, y0, x1, y1 = box2
    bar_h = int(round(place_size2 * 1.6))
    bar_cy = y1 - bar_h // 2
    f = H.font("cond_b", place_size2)
    record_box(name + "_place",
               draw.textbbox((x0 + 8, bar_cy), place, font=f, anchor="lm"))
    if sources:
        fs = H.font("cond", sources_size2)
        record_box(name + "_sources",
                   draw.textbbox((x1 - 8, bar_cy), sources, font=fs,
                                 anchor="rm"))
    fl = H.font("sans_b", label_size2)
    label_w = int(round(fl.getlength(label)))
    tbb = draw.textbbox((0, 0), label, font=fl)
    text_h = tbb[3] - tbb[1]
    lx1 = x1 - 12
    lx0 = lx1 - label_w - 20
    ly0 = y0 + 12
    ly1 = ly0 + text_h + 20
    record_box(name + "_label",
               draw.textbbox(((lx0 + lx1) // 2, (ly0 + ly1) // 2), label,
                             font=fl, anchor="mm"))


def record_badge_number(draw, name, cx2, cy2, number, number_size2):
    """Record a badge's number text (drawn centred by badge())."""
    f = H.font("cond_b", number_size2)
    record_box(name, draw.textbbox((cx2, cy2), str(number), font=f,
                                   anchor="mm"))


def record_chip_text(draw, name, pill_bbox, kind, extra, size2):
    """Record a tag chip's word (drawn by tag_chip()).  pill_bbox is the
    (left, top, right, bottom) tag_chip returns, in 2x units.  For an
    UNVERIFIED chip the icon itself is a "?" glyph, recorded too."""
    left, top, _right, _bottom = pill_bbox
    word = kind + (" \u00b7 " + extra if extra else "")
    icon_r = int(round(size2 * 0.55))
    icon_cx = left + 10 + icon_r
    icon_cy = top + (size2 + 12) // 2
    if kind == "UNVERIFIED":
        f = H.font("cond_b", max(8, int(round(icon_r * 1.35))))
        record_box(name + "_icon",
                   draw.textbbox((icon_cx, icon_cy), "?", font=f,
                                 anchor="mm"))
    text_x = left + 10 + 2 * icon_r + 8
    f = H.font("cond_b", size2)
    record_box(name, draw.textbbox((text_x, icon_cy), word, font=f,
                                   anchor="lm"))


def record_icon_question(draw, name, cx2, cy2, r2):
    """Record the "?" of an UNVERIFIED certainty icon."""
    f = H.font("cond_b", max(8, int(round(r2 * 1.35))))
    record_box(name, draw.textbbox((cx2, cy2), "?", font=f, anchor="mm"))


def draw_panel(draw, img, name, box, place, sources, label, picture,
               place_size, sources_size, label_size):
    """Draw one picture panel: illustration first into the inner rect,
    then panel_frame on top (dark bar, red label, outline).  box and
    sizes are in spec units.  Returns the panel box in 2x units."""
    box2 = tuple(int(round(v * S)) for v in box)
    inner = H.panel_inner_rect(box2, place_size * S)
    pictures.PICTURES[picture](img, inner, H)
    H.panel_frame(draw, box2, place, sources, label,
                  place_size * S, sources_size * S, label_size * S)
    record_panel_texts(draw, name, box2, place, sources, label,
                       place_size * S, sources_size * S, label_size * S)
    return box2


# ------------------------------------------------------------------ stage 3
def stage_leads(draw, img):
    """The 3 lead stories (y=252).  Returns (cards_y, rule_y)."""
    y = 252
    col_w = 324
    gap = 14
    bottoms = []
    for i, s in enumerate(data.STORIES[:3]):
        x = MARGIN + i * (col_w + gap)
        colour = data.REGION_COLORS[s["region"]]
        # Picture panel, 61 px high.
        draw_panel(draw, img, "lead%d" % s["number"],
                   (x, y, x + col_w, y + 61), s["place"], None, s["label"],
                   s["picture"], 10.5, 10.4, 16)
        # Badge + kicker + tag chip at +65.
        by = y + 65
        badge_cx2 = (x + 9) * S
        badge_cy2 = (by + 5.5) * S
        H.badge(draw, badge_cx2, badge_cy2, 9 * S, s["number"], colour,
                outline=2, number_size=11 * S)
        record_badge_number(draw, "lead%d_badge" % s["number"],
                            badge_cx2, badge_cy2, s["number"], 11 * S)
        kicker = "%s \u00b7 %s" % (s["region"], s["field"])
        text(draw, "lead%d_kicker" % s["number"], x + 22, by, kicker,
             "cond_b", 11, colour)
        pill = H.tag_chip(draw, (x + col_w) * S, by * S, s["certainty"],
                          s.get("certainty_extra"), size=10 * S)
        record_chip_text(draw, "lead%d_chip" % s["number"], pill,
                         s["certainty"], s.get("certainty_extra"), 10 * S)
        # Headline at +86, serif_b 24, line height 25.2.
        hy = y + 86
        runs = [(s["headline"], H.font("serif_b", 24 * S), data.INK)]
        lines, _h = wrap(runs, col_w, 25.2)
        used = record_lines(draw, "lead%d_headline" % s["number"], lines,
                            x, hy, 25.2)
        # Body, serif 13.6, line height 15.6, 2 px below the headline.
        body_y = hy + used + 2
        runs = [(s["body"], H.font("serif", int(round(13.6 * S))), data.INK)]
        lines, _h = wrap(runs, col_w, 15.6)
        used = record_lines(draw, "lead%d_body" % s["number"], lines,
                            x, body_y, 15.6)
        # Sources line, 4 px below the body.
        src_y = body_y + used + 4
        bbox = text(draw, "lead%d_sources" % s["number"], x, src_y,
                    s["sources"], "cond_b", 10.4, data.GREY)
        bottoms.append(bbox[3] / S)
    rule_y = max(bottoms) + 2
    rule(draw, rule_y, thickness=1.4)
    return rule_y + 6, rule_y


# ------------------------------------------------------------------ stage 4
def stage_cards(draw, img, cards_y):
    """The 10 picture cards (2 rows x 5).  Returns (row_a_y, rule_y)."""
    card_w = 190.4
    step = card_w + 12
    row_h = 123.2
    for i, s in enumerate(data.STORIES[3:13]):
        r = i // 5
        c = i % 5
        x = MARGIN + c * step
        y = cards_y + r * row_h
        colour = data.REGION_COLORS[s["region"]]
        # Picture panel, 48 px high, sources in the place bar.
        draw_panel(draw, img, "card%d" % s["number"],
                   (x, y, x + card_w, y + 48), s["place"], s["sources"],
                   s["label"], s["picture"], 9.6, 9.6, 12)
        # Badge + topic kicker + certainty icon at +54 (moved down
        # 3 px so the badge clears the picture panel's bottom edge).
        ky = y + 54
        badge_cx2 = (x + 8) * S
        badge_cy2 = (ky + 5) * S
        H.badge(draw, badge_cx2, badge_cy2, 8 * S, s["number"], colour,
                outline=2, number_size=10 * S)
        record_badge_number(draw, "card%d_badge" % s["number"],
                            badge_cx2, badge_cy2, s["number"], 10 * S)
        topic = data.TOPIC_OF_FIELD[s["field"]]
        kicker = "%s \u00b7 %s" % (topic, s["field"])
        text(draw, "card%d_kicker" % s["number"], x + 18, ky, kicker,
             "cond_b", 10.4, colour)
        icon_cx2 = (x + card_w - 7) * S
        icon_cy2 = (ky + 5) * S
        H.certainty_icon(draw, icon_cx2, icon_cy2, 7 * S, s["certainty"])
        if s["certainty"] == "UNVERIFIED":
            record_icon_question(draw, "card%d_icon" % s["number"],
                                 icon_cx2, icon_cy2, 7 * S)
        # Headline at +67, dserif_b 14.2, line height 15.4, max 3 lines.
        runs = [(s["headline"], H.font("dserif_b", int(round(14.2 * S))),
                 data.INK)]
        lines, _h = wrap(runs, card_w, 15.4)
        if len(lines) > 3:
            raise ValueError("card %d headline needs %d lines"
                             % (s["number"], len(lines)))
        record_lines(draw, "card%d_headline" % s["number"], lines,
                     x, y + 67, 15.4)
    row2_y = cards_y + row_h
    rule_y = row2_y + 113.2 + 5
    rule(draw, rule_y, thickness=1.4)
    return rule_y + 5, rule_y


# ------------------------------------------------------------------ stage 5
COND_BOLD_PATH = ("/home/hatch/workspace/fonts/dejavu-fonts-ttf-2.37/ttf/"
                  "DejaVuSansCondensed-Bold.ttf")

HEADER_LINES = {
    "EUROPE": ["Europe"],
    "MIDDLE EAST": ["Middle", "East"],
    "ASIA-PACIFIC": ["Asia &", "Pacific"],
    "AFRICA": ["Africa"],
    "AMERICAS": ["Americas"],
    "WORLD": ["World"],
}


def blend_cell(region_colour, v):
    """Region colour blended toward white: strength grows with the count,
    so a big count is a saturated cell and a count of 1 is pale.  The
    number is white once the cell is more than 60% saturated."""
    s = min(1.0, 0.25 + 0.2 * v)
    colour = tuple(round(region_colour[c] * s + 255 * (1 - s))
                   for c in range(3))
    return colour, data.WHITE if s > 0.6 else data.INK


def coverage_columns():
    """Region column widths (spec section 9): each column is its widest
    header line + 5 px, plus an equal share of what is left after the
    63-px label column and the 26-px All column."""
    label_w = 63
    all_w = 26
    avail = 336 - label_w - all_w
    bases = {}
    for region in data.REGIONS:
        widest = max(text_w("cond_b", 10, line)
                     for line in HEADER_LINES[region])
        bases[region] = widest + 5
    share = (avail - sum(bases.values())) / len(data.REGIONS)
    widths = {region: bases[region] + share for region in data.REGIONS}
    return label_w, all_w, widths


def stage_row_a(draw, img, row_a_y):
    """Row A: map, How the day changed, Date check.
    Returns (briefs_header_y, rule_y)."""
    land = map_draw.load_land(os.path.join(BASE, "world_land.json"))
    h_a = 126
    # --- Box 1: map ---
    map_x0, map_w = MARGIN, 240
    text(draw, "map_title", map_x0, row_a_y,
         "WHERE ALL %d STORIES HAPPENED" % data.N, "cond_b", 11, data.INK)
    map_top = row_a_y + 15
    map_h = 104 * (map_w / 306.0)
    map_box = (map_x0, map_top, map_x0 + map_w, map_top + map_h)
    map_box2 = tuple(int(round(v * S)) for v in map_box)
    placed = map_draw.draw_map(img, map_box2, land, data.STORIES,
                               font_bold=COND_BOLD_PATH)
    # Record the map badge numbers (draw_map returns their centres).
    factor = (map_box2[2] - map_box2[0]) / 240.0
    badge_font = H.font("cond_b", int(round(8.8 * factor)))
    for number, (cx, cy) in sorted(placed.items()):
        record_box("map_badge%d" % number,
                   draw.textbbox((cx, cy), str(number), font=badge_font,
                                 anchor="mm"))
    # Key lines under the map.
    key1, key2 = map_draw.map_key_lines(data.STORIES)
    key_y = map_top + map_h + 4
    part1, part2 = key1.split("\u25cf")
    # Grey badge "7", then part 1, then a grey dot, then part 2.
    bx, by = map_x0 + 5, key_y + 5
    H.badge(draw, bx * S, by * S, 5 * S, 7, data.GREY, outline=2,
            number_size=7 * S)
    record_badge_number(draw, "map_key_badge", bx * S, by * S, 7, 7 * S)
    tx = map_x0 + 12
    text(draw, "map_key1a", tx, key_y, part1.strip(), "cond", 10.4, data.INK)
    tx += text_w("cond", 10.4, part1.strip()) + 6
    dx = tx + 2.6
    draw.ellipse([(dx - 2.6) * S, (by - 2.6) * S, (dx + 2.6) * S,
                  (by + 2.6) * S], fill=data.GREY)
    tx = dx + 2.6 + 4
    text(draw, "map_key1b", tx, key_y, part2.strip(), "cond", 10.4, data.INK)
    text(draw, "map_key2", map_x0, key_y + 13, key2, "cond", 10.4, data.GREY)

    # --- Box 3: How the day changed ---
    box3_x, box3_w = 264, 340
    rect(draw, box3_x, row_a_y, box3_x + box3_w, row_a_y + h_a,
         fill=data.HOW_CHANGED_FILL)
    draw.rectangle([box3_x * S, row_a_y * S,
                    (box3_x + box3_w) * S, (row_a_y + h_a) * S],
                   outline=data.NAVY, width=2)
    text(draw, "how_changed_head", box3_x + 8, row_a_y + 6,
         "HOW THE DAY CHANGED", "cond_b", 11, data.NAVY)
    ey = row_a_y + 23
    for j, (lead, rest) in enumerate(data.HOW_CHANGED):
        runs = [(lead, H.font("cond_b", int(round(11.4 * S))), data.NAVY),
                (rest, H.font("cond", int(round(11.4 * S))), data.INK)]
        lines, _h = wrap(runs, box3_w - 16, 13.2)
        used = record_lines(draw, "how_changed_%d" % j, lines,
                            box3_x + 8, ey, 13.2)
        ey += used + 4

    # --- Box 4: Date check ---
    box4_x, box4_w = 616, 396
    rect(draw, box4_x, row_a_y, box4_x + box4_w, row_a_y + h_a,
         fill=data.DATE_CHECK_FILL)
    draw.rectangle([box4_x * S, row_a_y * S,
                    (box4_x + box4_w) * S, (row_a_y + h_a) * S],
                   outline=data.RED, width=2)
    text(draw, "date_check_head", box4_x + 8, row_a_y + 6, "DATE CHECK",
         "cond_b", 11.8, data.RED)
    runs = []
    for lead, rest in data.date_check_lines():
        if lead:
            runs.append((lead, H.font("cond_b", int(round(11.8 * S))),
                         data.RED))
        runs.append((rest, H.font("cond", int(round(11.8 * S))), data.INK))
    lines, _h = wrap(runs, box4_w - 16, 13.2)
    record_lines(draw, "date_check", lines, box4_x + 8, row_a_y + 24, 13.2)

    rule_y = row_a_y + h_a + 4
    rule(draw, rule_y, thickness=1.2)
    return rule_y + 5, rule_y


# ------------------------------------------------------------------ stage 6
def shorten_what(what, max_w):
    """Shorten a brief's what-happened text to fit max_w (spec units),
    dropping whole words from the end and adding an ellipsis.  Returns
    the (possibly shortened) text."""
    if text_w("cond", 13.3, what) <= max_w:
        return what
    words = what.split(" ")
    while len(words) > 1:
        words.pop()
        trial = " ".join(words) + "\u2026"
        if text_w("cond", 13.3, trial) <= max_w:
            return trial
    return "\u2026"


def stage_briefs(draw, briefs_header_y):
    """Briefs header and the 29 briefs (stories 14-42), 3 columns."""
    n_more = data.N - 13
    text(draw, "briefs_header", MARGIN, briefs_header_y,
         "ALSO ON SUNDAY 22 NOVEMBER \u2014 %d MORE STORIES, BY REGION"
         % n_more, "cond_b", 11.4, data.NAVY)
    text(draw, "briefs_header_right", RIGHT, briefs_header_y,
         "place \u00b7 what happened \u00b7 source \u00b7 how sure", "cond",
         10.4, data.GREY, anchor="ra")
    briefs_y = briefs_header_y + 15
    row_h = (1000 - briefs_y) / 10.0
    col_w = 326.7
    # Thin RULE verticals between the columns.
    for sx in (MARGIN + col_w + 5, MARGIN + 2 * col_w + 15):
        draw.rectangle([sx * S, briefs_y * S, sx * S + 1, 1000 * S],
                       fill=data.RULE)
    briefs = data.STORIES[13:]
    for c in range(3):
        col_x = MARGIN + c * (col_w + 10)
        for i in range(10):
            idx = c * 10 + i
            if idx >= len(briefs):
                break
            s = briefs[idx]
            cy = briefs_y + (i + 0.5) * row_h
            colour = data.REGION_COLORS[s["region"]]
            bcx = (col_x + 8.8) * S
            bcy = cy * S
            H.square_badge(draw, bcx, bcy, 8.8 * S, s["number"], colour,
                           outline=2, number_size=10.2 * S)
            record_badge_number(draw, "brief%d_badge" % s["number"],
                                bcx, bcy, s["number"], 10.2 * S)
            # Place, in the region colour.
            place_x = col_x + 8.8 + 8.8 + 3
            place_w = text_w("cond_b", 13.3, s["place"])
            text(draw, "brief%d_place" % s["number"], place_x, cy, s["place"],
                 "cond_b", 13.3, colour, anchor="lm")
            # Source, right-aligned, ending 16 px before the column edge.
            src_right = col_x + col_w - 16
            src_w = text_w("cond", 11.4, s["source"])
            # What-happened text, shortened if it would reach the source.
            what_x = place_x + place_w + 3
            avail = (src_right - src_w - 4) - what_x
            what = shorten_what(s["what"], avail)
            text(draw, "brief%d_what" % s["number"], what_x, cy, what,
                 "cond", 13.3, data.INK, anchor="lm")
            text(draw, "brief%d_source" % s["number"], src_right, cy,
                 s["source"], "cond", 11.4, data.GREY, anchor="rm")
            # Certainty icon at the far right.
            icx = (col_x + col_w - 6.6) * S
            icy = cy * S
            H.certainty_icon(draw, icx, icy, 6.6 * S, s["certainty"])
            if s["certainty"] == "UNVERIFIED":
                record_icon_question(draw, "brief%d_icon" % s["number"],
                                     icx, icy, 6.6 * S)


# ------------------------------------------------------------------ stage 7
def stage_footer(draw):
    """Footer legend (y=1004)."""
    y = 1004
    x = MARGIN
    text(draw, "footer_how_sure", x, y, "HOW SURE", "cond_b", 12, data.INK)
    x += text_w("cond_b", 12, "HOW SURE") + 3
    for name, definition in data.CERTAINTY_DEFS:
        # Icon, then bold name + regular definition.  The defining line
        # is drawn in the icon's own colour, so each item stays tied
        # to its symbol and the items do not run into each other.
        colour = data.CERTAINTY_COLORS[name]
        icx = (x + 7.5) * S
        icy = (y + 6) * S
        H.certainty_icon(draw, icx, icy, 7.5 * S, name)
        if name == "UNVERIFIED":
            record_icon_question(draw, "footer_icon_%s" % name,
                                 icx, icy, 7.5 * S)
        x += 15 + 2
        name_text = name + ": "
        text(draw, "footer_%s_name" % name, x, y, name_text, "cond_b", 12,
             colour)
        x += text_w("cond_b", 12, name_text)
        text(draw, "footer_%s_def" % name, x, y, definition, "cond", 12,
             colour)
        x += text_w("cond", 12, definition) + 2
    text(draw, "footer_drawings", RIGHT, y, "Drawings, not photos", "cond",
         12, data.GREY, anchor="ra")


# ---------------------------------------------------------------------- main
def build_page():
    """Draw the whole front page at 2x and return the 2048x2048 image."""
    img = Image.new("RGB", (W * S, Hh * S), data.PAPER)
    draw = ImageDraw.Draw(img)
    stage_top(draw)
    stage_timeline_numbers(draw)
    cards_y, _rule_y = stage_leads(draw, img)
    row_a_y, _rule2_y = stage_cards(draw, img, cards_y)
    briefs_header_y, _rule3_y = stage_row_a(draw, img, row_a_y)
    stage_briefs(draw, briefs_header_y)
    stage_footer(draw)
    return img


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--upto", type=int, default=7,
                        help="render stages 1..N only (default: all)")
    parser.add_argument("--out", default=None,
                        help="output path (default: entry.png here)")
    args = parser.parse_args()

    img = Image.new("RGB", (W * S, Hh * S), data.PAPER)
    draw = ImageDraw.Draw(img)
    stage_top(draw)
    if args.upto >= 2:
        stage_timeline_numbers(draw)
    if args.upto >= 3:
        cards_y, _ = stage_leads(draw, img)
    if args.upto >= 4:
        row_a_y, _ = stage_cards(draw, img, cards_y)
    if args.upto >= 5:
        briefs_header_y, _ = stage_row_a(draw, img, row_a_y)
    if args.upto >= 6:
        stage_briefs(draw, briefs_header_y)
    if args.upto >= 7:
        stage_footer(draw)

    problems = reg.problems(W * S, Hh * S)
    print("text registry problems (%d):" % len(problems))
    for problem in problems:
        print("  " + problem)

    out = args.out or os.path.join(BASE, "entry.png")
    final = img.resize((W, Hh), Image.LANCZOS)
    final.save(out, optimize=True)
    size = os.path.getsize(out)
    digest = hashlib.sha256(open(out, "rb").read()).hexdigest()
    print("wrote %s: %dx%d, %d bytes, sha256 %s"
          % (out, W, Hh, size, digest))
    return 0 if not problems else 1


if __name__ == "__main__":
    sys.exit(main())





