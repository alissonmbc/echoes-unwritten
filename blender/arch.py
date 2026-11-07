"""Ruined stone archway: real ashlar courses, voussoirs, twin columns, ivy."""
import math
import random

from mathutils import Vector, noise

from common import (Part, box_corners, clamp, export, fbm, lathe, leaves, material, mix,
                    prism_corners, smooth, stone, tube, use_scene)

R, SPRING, TOP, W, D = 2.95, 5.2, 9.9, 4.75, 0.95
RING = 0.95
RO = R + RING + 0.08


def build():
    rnd = random.Random(11)
    scn = use_scene("Lumina_Archway")
    st = Part("arch_stone", material("stone", rough=0.92))
    iron = Part("arch_iron", material("iron", rough=0.5, metal=0.6))
    ivy = Part("arch_ivy", material("leaf", rough=0.8, double=True))

    def col_for(tone):
        def f(p, w, edge):
            k = fbm(p * 0.9 + Vector((3, 1, 7)), 3)
            base = mix((0.30, 0.27, 0.225), (0.56, 0.51, 0.42), clamp(tone + k * 0.8))
            c = tuple(x * (1 - 0.28 * min(edge, 2) / 2) for x in base)
            grime = smooth(3.0, -0.5, p.z) * 0.32 + smooth(0.1, 0.5, fbm(p * 0.35 + Vector((9, 0, 0)), 2)) * 0.22
            c = tuple(x * (1 - grime) for x in c)
            moss = (w > 0.9) * smooth(-0.1, 0.25, fbm(p * 0.7, 2)) * 0.75
            moss = max(moss, smooth(0.08, 0.3, fbm(p * 0.55 + Vector((0, 4, 0)), 3)) * smooth(4.5, 0.8, p.z) * 0.55)
            return mix(c, (0.075, 0.11, 0.03), moss)
        return f

    def block(x0, x1, y0, y1, z0, z1, bevel=0.04, cells=3, chip=0.018):
        stone(st, box_corners(x0, x1, y0, y1, z0, z1), bevel, cells, chip, col_for(rnd.uniform(0.25, 0.8)), rnd)

    def quad(p00, p10, p11, p01, y0=-D, y1=D, bevel=0.04, cells=3, chip=0.018):
        stone(st, prism_corners(p00, p10, p11, p01, y0, y1), bevel, cells, chip, col_for(rnd.uniform(0.25, 0.8)), rnd)

    # left-top is the ruined end; right side runs into the cliff
    def ruined(x, z):
        return z > TOP + 0.6 - max(0.0, -x - 1.5) * 0.42 + rnd.uniform(-0.35, 0.35)

    # foundations reach down past the road edge so the left pier doesn't float over the drop
    z = -7.0
    while z < -0.1:
        h = rnd.uniform(0.7, 1.0)
        for s in (-1, 1):
            spread = 0.35 - z * 0.05
            block(*sorted((s * (R + 0.15), s * (W + spread))), -D - spread, D + spread, z, min(z + h, 0.0), 0.06, 3, 0.03)
        z += h

    # piers: coursed ashlar up to the springing line
    z, course = 0.0, 0
    while z < SPRING - 0.2:
        h = rnd.uniform(0.52, 0.72)
        z1 = min(z + h, SPRING)
        if SPRING - z1 < 0.35:
            z1 = SPRING
        for s in (-1, 1):
            x = R
            first = 0.55 if course % 2 else 0.95
            while x < W - 0.01:
                w = first if x == R else rnd.uniform(0.7, 1.15)
                x1 = W if W - (x + w) < 0.4 else x + w
                block(*sorted((s * x, s * x1)), -D, D, z, z1)
                x = x1
        z, course = z1, course + 1

    # impost moulding at the springing line
    for s in (-1, 1):
        a, b = sorted((s * (R - 0.1), s * (W + 0.12)))
        block(a, b, -D - 0.12, D + 0.12, SPRING, SPRING + 0.3, 0.06, 3, 0.012)

    base = SPRING + 0.3

    # voussoirs, with a proud keystone
    n = 17
    for i in range(n):
        a0, a1 = math.pi * i / n + 0.006, math.pi * (i + 1) / n - 0.006
        key = i == n // 2
        out = R + (RING + 0.42 if key else RING + rnd.uniform(-0.06, 0.08))
        if key:
            a0, a1 = a0 - 0.02, a1 + 0.02
        P = lambda r, a: (math.cos(a) * r, base + math.sin(a) * r)
        inner = R - (0.08 if key else 0)
        y = D + (0.2 if key else rnd.uniform(0.02, 0.08))
        quad(P(inner, a0), P(out, a0), P(out * (1.04 if key else 1), a1), P(inner, a1), -y, y, 0.05, 3, 0.02)

    # thin archivolt moulding proud of the ring, missing on the ruined side
    for i in range(23):
        a0, a1 = math.pi * i / 23 + 0.004, math.pi * (i + 1) / 23 - 0.004
        if a0 > 2.2 and rnd.random() < 0.55:
            continue
        P = lambda r, a: (math.cos(a) * r, base + math.sin(a) * r)
        for y0, y1 in ((-D - 0.14, -D + 0.1), (D - 0.1, D + 0.14)):
            quad(P(R + RING, a0), P(R + RING + 0.17, a0), P(R + RING + 0.17, a1), P(R + RING, a1), y0, y1, 0.03, 1, 0.006)

    # spandrels and upper wall: courses clipped against the ring
    def edge_x(zz):
        d = zz - base
        return math.sqrt(max(RO * RO - d * d, 0.0))

    z, course = base, 0
    while z < TOP - 0.05:
        z1 = min(z + rnd.uniform(0.55, 0.7), TOP)
        if TOP - z1 < 0.3:
            z1 = TOP
        b0, b1 = edge_x(z), edge_x(z1)
        if b0 > 0.05:
            for s in (-1, 1):
                x, first = b0, True
                while x < W - 0.01:
                    x1 = x + rnd.uniform(0.8, 1.3)
                    x1 = W if W - x1 < 0.45 else x1
                    if s < 0 and ruined(-x1, z1):
                        x = x1
                        first = False
                        continue
                    lo = b1 if first else x
                    if s > 0:
                        quad((x, z), (x1, z), (x1, z1), (lo, z1))
                    else:
                        quad((-x1, z), (-x, z), (-lo, z1), (-x1, z1))
                    x, first = x1, False
        else:
            x = -W
            while x < W - 0.01:
                x1 = x + rnd.uniform(0.8, 1.35)
                x1 = W if W - x1 < 0.45 else x1
                if not ruined((x + x1) / 2, z1):
                    block(x, x1, -D, D, z, z1)
                x = x1
        z, course = z1, course + 1

    # cornice, broken away on the left
    x = -W - 0.15
    while x < W + 0.15:
        x1 = min(x + rnd.uniform(0.9, 1.5), W + 0.2)
        if not ruined((x + x1) / 2, TOP + 0.45) and x > -2.4:
            block(x, x1, -D - 0.2, D + 0.2, TOP, TOP + 0.34, 0.06, 3, 0.02)
            if rnd.random() < 0.75:
                block(x + 0.1, x1 - 0.1, -D - 0.02, D + 0.02, TOP + 0.34, TOP + 0.34 + rnd.uniform(0.3, 0.75), 0.06, 3, 0.035)
        x = x1

    # twin columns on both faces of each pier
    def column(cx, cy, h=SPRING):
        col = col_for(rnd.uniform(0.45, 0.8))
        block(cx - 0.47, cx + 0.47, cy - 0.47, cy + 0.47, 0, 0.36, 0.05, 1, 0.01)
        prof = [(0.45, 0.36), (0.45, 0.42), (0.40, 0.5), (0.34, 0.54)]
        zs = [0.54 + (h - 1.2) * t / 8 for t in range(9)]
        prof += [(0.33 - 0.04 * (t / 8) ** 2, zs[t]) for t in range(9)]
        prof += [(0.32, h - 0.62), (0.29, h - 0.56), (0.31, h - 0.5), (0.47, h - 0.2)]
        lathe(st, prof, cx, cy, 14, col)
        block(cx - 0.55, cx + 0.55, cy - 0.55, cy + 0.55, h - 0.2, h, 0.04, 1, 0.01)

    for s in (-1, 1):
        for cy in (-1.3, 1.3):
            column(s * (R + 0.48), cy)
            column(s * (W - 0.32), cy)

    # right wing wall running into the cliff, stepped down
    z = 0.0
    while z < 8.2:
        z1 = z + rnd.uniform(0.55, 0.72)
        x = W
        while x < W + 4.2:
            x1 = x + rnd.uniform(0.8, 1.3)
            if z1 < 8.3 - (x - W) * 0.75 + rnd.uniform(-0.6, 0.6):
                block(x, x1, -0.72, 0.72, z, z1, 0.05, 3, 0.03)
            x = x1
        z = z1

    # stump of a second, older column behind the wing
    z = 0.0
    while z < 15.2:
        h = rnd.uniform(0.9, 1.5)
        lathe(st, [(0.82 - z * 0.008, z), (0.8 - z * 0.008, z + h - 0.03)], 5.7, 1.5, 14, col_for(rnd.uniform(0.3, 0.75)))
        z += h

    # fallen stones
    for _ in range(9):
        x, y = rnd.uniform(3.2, 6.5), rnd.uniform(-3.5, -1.5)
        s = rnd.uniform(0.3, 0.6)
        c = box_corners(x - s, x + s, y - s * 0.8, y + s * 0.8, -0.1, s)
        stone(st, c, 0.07, 3, 0.05, col_for(rnd.uniform(0.2, 0.7)), rnd)

    # iron brackets that the two banners hang from
    for s in (-1, 1):
        cx = s * 3.6
        tube(iron, [(cx - 0.66, -1.16, 9.0), (cx + 0.66, -1.16, 9.0)], 0.03)
        for dx in (-0.6, 0.6):
            tube(iron, [(cx + dx, -0.95, 9.14), (cx + dx, -1.16, 9.0)], 0.02)

    # ivy curtains: strands that wander down the right of the wall and the wing
    anchors = []
    for _ in range(46):
        x = rnd.uniform(2.6, 8.8) if rnd.random() < 0.9 else rnd.uniform(-4.7, -3.6)
        topz = TOP + 0.5 - (max(x - W, 0) * 0.75 + (1.9 if x > W else 0))
        if x < 0:
            topz = 8.7
        p = Vector((x, -D - 0.1 + (0.2 if x > W else 0), topz))
        length = rnd.uniform(1.8, 6.2)
        steps = int(length / 0.09)
        ph = rnd.uniform(0, 9)
        for i in range(steps):
            p = p + Vector((math.sin(i * 0.22 + ph) * 0.03, 0, -0.09))
            if p.z < 0.15:
                break
            if rnd.random() < 0.8:
                q = p + Vector((rnd.uniform(-0.16, 0.16), -rnd.uniform(0.02, 0.2), rnd.uniform(-0.1, 0.1)))
                anchors.append((q, (rnd.uniform(-0.3, 0.3), -1, 0.25)))
    leaves(ivy, anchors, rnd, 0.1)

    objs = [st.to_object(scn), iron.to_object(scn), ivy.to_object(scn, flat=True)]
    info = export(objs, "archway.glb")
    info["tris"] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    return info, scn
