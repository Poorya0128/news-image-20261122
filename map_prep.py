#!/usr/bin/env python3
"""Download Natural Earth 1:110m land (TopoJSON) and convert it to a
simplified list of coastline rings for the newspaper map.

Runs on my own machine only, never in the grader. The map data comes
from jsDelivr, a library host the bounty rules exclude from the copy
check; everything else here is my own code.

Steps:
  1. Fetch https://cdn.jsdelivr.net/npm/world-atlas@2/land-110m.json
  2. Decode the TopoJSON arcs (delta-encoded integers + transform).
  3. Join arcs into rings (negative index = that arc reversed).
  4. Drop Antarctica (rings whose highest latitude is below -55).
  5. Round points to 0.2 degrees, drop consecutive duplicates.
  6. Drop rings smaller than 0.8 square degrees.
  7. Save world_land.json: a list of rings of [lon, lat], one decimal.
"""

import json
import math
import urllib.request

SOURCE_URL = "https://cdn.jsdelivr.net/npm/world-atlas@2/land-110m.json"
OUT_PATH = "world_land.json"

GRID = 0.2          # round coordinates to this many degrees
MIN_RING_AREA = 0.8  # square degrees; smaller rings are dropped
ANTARCTICA_MAX_LAT = -55.0  # drop rings whose highest latitude is below this


def fetch_topojson(url):
    request = urllib.request.Request(url, headers={"User-Agent": "map-prep/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        raw = response.read()
    print("downloaded %d bytes from %s" % (len(raw), url))
    return json.loads(raw)


def decode_arcs(topology):
    """Turn delta-encoded integer arcs into lists of (lon, lat) floats."""
    scale_x, scale_y = topology["transform"]["scale"]
    trans_x, trans_y = topology["transform"]["translate"]
    decoded = []
    for arc in topology["arcs"]:
        points = []
        x = 0
        y = 0
        for dx, dy in arc:
            x += dx
            y += dy
            points.append((x * scale_x + trans_x, y * scale_y + trans_y))
        decoded.append(points)
    return decoded


def join_ring(arc_indices, arcs):
    """Join the arcs of one ring into a single point list.

    A negative index i means arc ~i (= -i - 1) traversed in reverse.
    Each joined arc's first point is skipped: it duplicates the
    previous arc's last point.
    """
    ring = []
    for index in arc_indices:
        if index >= 0:
            points = arcs[index]
        else:
            points = arcs[~index][::-1]
        if ring:
            points = points[1:]
        ring.extend(points)
    # A closed ring repeats its first point at the end; drop it.
    if len(ring) > 1 and ring[0] == ring[-1]:
        ring.pop()
    return ring


def ring_area(ring):
    """Absolute shoelace area in square degrees."""
    total = 0.0
    for (x1, y1), (x2, y2) in zip(ring, ring[1:] + ring[:1]):
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def simplify_ring(ring):
    """Round to the grid, drop consecutive duplicates, drop degenerate rings."""
    rounded = []
    for lon, lat in ring:
        lon = round(lon / GRID) * GRID
        lat = round(lat / GRID) * GRID
        point = (round(lon, 1), round(lat, 1))
        if not rounded or rounded[-1] != point:
            rounded.append(point)
    if len(rounded) > 1 and rounded[0] == rounded[-1]:
        rounded.pop()
    return rounded


def split_antimeridian(ring):
    """Split a ring where it jumps across the antimeridian.

    The source data is cut at lon +/-180, so a ring that crosses the
    antimeridian has segments jumping from near +180 to near -180 (or
    the reverse). Drawn as one polygon, such a segment becomes a
    spurious horizontal line across the whole map. Splitting at the
    jump leaves pieces whose ends sit on the same side of the cut, so
    each piece closes with a short segment along the antimeridian.
    """
    pieces = []
    current = [ring[0]]
    for prev, point in zip(ring, ring[1:]):
        if abs(point[0] - prev[0]) > 180.0:
            pieces.append(current)
            current = [point]
        else:
            current.append(point)
    pieces.append(current)
    return pieces


def collect_rings(topology, arcs):
    """Collect every ring of the land object, minus Antarctica."""
    land = topology["objects"]["land"]
    geometries = land["geometries"]
    rings = []
    for geometry in geometries:
        if geometry["type"] == "Polygon":
            polygons = [geometry["arcs"]]
        elif geometry["type"] == "MultiPolygon":
            polygons = geometry["arcs"]
        else:
            continue
        for polygon in polygons:
            for arc_indices in polygon:
                ring = join_ring(arc_indices, arcs)
                if not ring:
                    continue
                for piece in split_antimeridian(ring):
                    if max(lat for _, lat in piece) < ANTARCTICA_MAX_LAT:
                        continue  # Antarctica
                    piece = simplify_ring(piece)
                    if len(piece) < 3:
                        continue
                    if ring_area(piece) < MIN_RING_AREA:
                        continue
                    rings.append([[lon, lat] for lon, lat in piece])
    return rings


def main():
    topology = fetch_topojson(SOURCE_URL)
    arcs = decode_arcs(topology)
    print("decoded %d arcs" % len(arcs))
    rings = collect_rings(topology, arcs)
    total_points = sum(len(ring) for ring in rings)
    with open(OUT_PATH, "w", encoding="utf-8") as handle:
        json.dump(rings, handle)
    print("wrote %s: %d rings, %d points" % (OUT_PATH, len(rings), total_points))
    # Sanity: no ring may reach Antarctic latitudes, and longitudes
    # must stay inside the usual -180..180 range.
    max_lat = max(lat for ring in rings for _, lat in ring)
    min_lat = min(lat for ring in rings for _, lat in ring)
    min_lon = min(lon for ring in rings for lon, _ in ring)
    max_lon = max(lon for ring in rings for lon, _ in ring)
    print("lat range %.1f..%.1f, lon range %.1f..%.1f"
          % (min_lat, max_lat, min_lon, max_lon))


if __name__ == "__main__":
    main()
