"""Flagstone road: a straight strip of irregular stones that index.html bends onto the road curve.

X = lateral (+X toward the cliff), Y = distance along the road, Z = up, with Z=0 at the road
surface. useRoad() in index.html maps the strip's Y extent onto u=0..1, so LENGTH only needs
to be close to PATH_LEN. Each stone is a Voronoi cell of a jittered grid, so the joints come from
offsetting the cell walls, and the dark road bed underneath shows through them.
"""
import math
import random

from mathutils import Vector

from common import Part, clamp, export, fbm, material, mix, smooth, use_scene

HALF = 2.98      # a little wider than the road's HALF, so the outer stones tuck under the curbs
LENGTH = 167.0
COLS = 6         # stones across
ROW = 0.86       # spacing along the road
JITTER = 0.36
JOINT = (0.008, 0.024)  # half-width of a joint
CORNER = 0.11           # how far along each edge the corners are cut
BEVEL = 0.04
DEPTH = 0.15
MIN_EDGE = 0.13


def clip(poly, px, py, nx, ny, d):
    """Keep the part of a convex polygon where (p - (px,py)) . n <= d."""
    out = []
    for i, a in enumerate(poly):
        b = poly[(i + 1) % len(poly)]
        da = (a[0] - px) * nx + (a[1] - py) * ny - d
        db = (b[0] - px) * nx + (b[1] - py) * ny - d
        if da <= 0:
            out.append(a)
        if (da < 0) != (db < 0) and da != db:
            t = da / (da - db)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def cell(site, near, rnd):
    x, y = site
    poly = [(-HALF, y - 3), (HALF, y - 3), (HALF, y + 3), (-HALF, y + 3)]
    for ox, oy in near:
        dx, dy = ox - x, oy - y
        dist = math.hypot(dx, dy)
        if dist < 1e-6:
            continue
        poly = clip(poly, x, y, dx / dist, dy / dist, dist / 2 - rnd.uniform(*JOINT))
        if len(poly) < 3:
            return None
    return poly


def tidy(poly):
    """Drop slivers of edge, then cut the corners so stones look worn rather than cut."""
    pts = []
    for p in poly:
        if not pts or math.dist(p, pts[-1]) >= MIN_EDGE:
            pts.append(p)
    if len(pts) > 3 and math.dist(pts[0], pts[-1]) < MIN_EDGE:
        pts.pop()
    if len(pts) < 3:
        return None
    out = []
    for i, a in enumerate(pts):
        b = pts[(i + 1) % len(pts)]
        k = min(CORNER / math.dist(a, b), 0.3)
        out.append((a[0] + (b[0] - a[0]) * k, a[1] + (b[1] - a[1]) * k))
        out.append((b[0] + (a[0] - b[0]) * k, b[1] + (a[1] - b[1]) * k))
    return out


def area(poly):
    return abs(sum(a[0] * b[1] - b[0] * a[1] for a, b in zip(poly, poly[1:] + poly[:1]))) / 2


def add_stone(part, poly, rnd):
    n = len(poly)
    cx = sum(p[0] for p in poly) / n
    cy = sum(p[1] for p in poly) / n
    if sum((a[0] - cx) * (b[1] - cy) - (b[0] - cx) * (a[1] - cy) for a, b in zip(poly, poly[1:] + poly[:1])) < 0:
        poly = poly[::-1]
    h0 = rnd.uniform(-0.035, 0.0)
    tx, ty = rnd.uniform(-0.03, 0.03), rnd.uniform(-0.03, 0.03)

    def top(x, y):
        return h0 + tx * (x - cx) + ty * (y - cy)

    # worn pale band down the middle; greyer, darker and mossier toward the verges
    wear = 1 - smooth(0.7, 2.6, abs(cx + 0.5 * fbm((0, cy * 0.08, 3), 2)))
    tone = rnd.uniform(0.74, 1.2)
    base = mix((0.17, 0.155, 0.135), (0.33, 0.285, 0.225), clamp(wear * 0.75 + rnd.uniform(-0.1, 0.3)))
    if rnd.random() < 0.16:
        base = mix(base, (0.3, 0.2, 0.125), 0.55)    # a few rust-warm stones
    if rnd.random() < 0.14:
        base = mix(base, (0.15, 0.16, 0.17), 0.6)    # and a few cool ones
    base = tuple(c * tone for c in base)

    def colour(x, y, rim):
        k = 1 + fbm((x * 1.9, y * 1.9, 7), 3) * 0.75
        moss = smooth(0.0, 0.3, fbm((x * 0.8, y * 0.8, 21), 2)) * smooth(1.6, 2.8, abs(x)) * 0.5
        c = mix(base, (0.09, 0.115, 0.04), moss)
        return tuple(max(v * k * rim, 0.0) for v in c)

    verts, cols = [], []
    for x, y in poly:                                   # foot of the side wall
        verts.append(Vector((x, y, -DEPTH)))
        cols.append((0.03, 0.026, 0.022))
    for x, y in poly:                                   # shoulder, where the bevel starts
        verts.append(Vector((x, y, top(x, y) - BEVEL * 0.8)))
        cols.append(colour(x, y, 0.55))
    for x, y in poly:                                   # inner edge of the bevel
        d = math.hypot(cx - x, cy - y) or 1
        b = BEVEL * rnd.uniform(0.75, 1.3)
        ix, iy = x + (cx - x) / d * b, y + (cy - y) / d * b
        verts.append(Vector((ix, iy, top(ix, iy) + fbm((ix * 2.3, iy * 2.3, 13), 2) * 0.02)))
        cols.append(colour(ix, iy, 1.0))
    verts.append(Vector((cx, cy, top(cx, cy) + 0.004)))
    cols.append(colour(cx, cy, 1.08))

    faces = []
    for ring in (0, 1):
        for i in range(n):
            j = (i + 1) % n
            a, b = ring * n, (ring + 1) * n
            faces.append((a + i, a + j, b + j, b + i))
    for i in range(n):
        faces.append((2 * n + i, 2 * n + (i + 1) % n, 3 * n))
    part.add(verts, faces, cols)


def build():
    rnd = random.Random(23)
    scn = use_scene("Lumina_Road")
    part = Part("road_stones", material("road_stone", rough=0.86))

    # jittered grid: columns run past the edges so outer stones are cut off, not rounded off
    dx = 2 * HALF / COLS
    rows = int(LENGTH / ROW) + 1
    grid = []
    for r in range(rows):
        shift = rnd.uniform(0, dx)
        line = []
        for c in range(-1, COLS + 1):
            x = -HALF + (c + 0.5) * dx + shift - dx / 2 + rnd.uniform(-JITTER, JITTER) * dx
            y = (r + 0.5) * ROW + rnd.uniform(-JITTER, JITTER) * ROW
            line.append((x, y))
        grid.append(line)

    stones = 0
    for r, line in enumerate(grid):
        near = [p for q in grid[max(r - 3, 0):r + 4] for p in q]
        for site in line:
            if abs(site[0]) > HALF:
                continue
            poly = cell(site, near, rnd)
            poly = tidy(poly) if poly else None
            if poly and area(poly) > 0.05:
                add_stone(part, poly, rnd)
                stones += 1

    ob = part.to_object(scn, sharp_deg=24)   # low, so the bevel stays crisp and the tops read flat
    info = export([ob], "road.glb")
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    down = sum(1 for p in ob.data.polygons if p.normal.z < -0.2)
    info.update(stones=stones, tris=tris, facing_down=down)
    return (info,)
