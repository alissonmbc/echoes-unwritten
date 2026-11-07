"""Lumina skyline. Origin = centre of the plateau top; -Y faces the road, +X is the viewer's right.

Nodes: city_stone, city_roof, city_win (emissive, swapped for an unlit bright material in
index.html), city_gold, city_rock. Tiers sit at z=0, 9 and 19. SPIRE_TOP is where the orb goes.
"""
import math
import random

from mathutils import Vector

from common import Part, clamp, export, fbm, lathe, material, mix, smooth, tube, use_scene

WALL_R = 84
T1_R, T1_Z = 58, 9
T2_R, T2_Z = 34, 19
SPIRE_TOP = 148


def build():
    rnd = random.Random(41)
    scn = use_scene("Lumina_City")
    stone = Part("city_stone", material("city_stone", rough=0.88))
    roof = Part("city_roof", material("city_roof", rough=0.55))
    win = Part("city_win", material("city_win", color=(0.02, 0.01, 0), emissive=(1, 0.65, 0.3)))
    gold = Part("city_gold", material("city_gold", color=(0.9, 0.62, 0.2), rough=0.3, metal=0.9))
    rock = Part("city_rock", material("rock", rough=0.95))

    def wall_col():
        return mix((0.42, 0.37, 0.3), (0.72, 0.65, 0.54), rnd.random())

    def slate():
        return mix((0.055, 0.085, 0.16), (0.14, 0.19, 0.32), rnd.random())

    def tint(c, z, z0, z1):
        return tuple(x * (0.72 + 0.28 * clamp((z - z0) / max(z1 - z0, 0.1))) for x in c)

    def ground(x, y):
        r = math.hypot(x, y)
        return T2_Z if r < T2_R else T1_Z if r < T1_R else 0

    def hbox(part, cx, cy, z0, w, d, h, rot=0.0, col=None, taper=1.0):
        col = col or wall_col()
        c, s = math.cos(rot), math.sin(rot)
        verts, cols = [], []
        for z, k in ((z0, 1.0), (z0 + h, taper)):
            for dx, dy in ((-1, -1), (1, -1), (1, 1), (-1, 1)):
                x, y = dx * w / 2 * k, dy * d / 2 * k
                verts.append(Vector((cx + x * c - y * s, cy + x * s + y * c, z)))
                cols.append(tint(col, z, z0, z0 + h))
        part.add(verts, [[3, 2, 1, 0], [4, 5, 6, 7], [0, 1, 5, 4], [1, 2, 6, 5], [2, 3, 7, 6], [3, 0, 4, 7]], cols)

    def gable(cx, cy, z0, w, d, h, rot=0.0, over=0.35, col=None):
        """Roof with its ridge along local Y (length d)."""
        col = col or slate()
        c, s = math.cos(rot), math.sin(rot)
        hw, hd = w / 2 + over, d / 2 + over

        def P(x, y, z):
            return Vector((cx + x * c - y * s, cy + x * s + y * c, z))
        v = [P(-hw, -hd, z0), P(hw, -hd, z0), P(hw, hd, z0), P(-hw, hd, z0), P(0, -hd, z0 + h), P(0, hd, z0 + h)]
        dark = tuple(x * 0.7 for x in col)
        roof.add(v, [[0, 1, 4], [1, 2, 5, 4], [2, 3, 5], [3, 0, 4, 5], [3, 2, 1, 0]], [dark, dark, dark, dark, col, col])

    def window(p, n, w=0.7, h=1.6, lit=None):
        """Lancet: five-point arch on a wall. p is the sill centre, n the outward horizontal normal."""
        n = Vector((n[0], n[1], 0)).normalized()
        s = Vector((-n.y, n.x, 0)) * w / 2
        up = Vector((0, 0, 1))
        p = Vector(p) + n * 0.09
        lit = rnd.random() < 0.62 if lit is None else lit
        c = mix((1.0, 0.62, 0.26), (1.0, 0.82, 0.5), rnd.random()) if lit else (0.018, 0.02, 0.035)
        verts = [p + s, p + s + up * h * 0.72, p + up * h, p - s + up * h * 0.72, p - s]
        win.add(verts, [[0, 1, 2, 3, 4]], [c] * 5)

    def spire(x, y, z, r, h, seg=8, tip=True):
        c = slate()
        lathe(roof, [(r * 1.22, z), (r * 0.62, z + h * 0.3), (r * 0.26, z + h * 0.68), (0.06, z + h)], x, y, seg,
              lambda p, w, e: tint(c, p.z, z - h * 0.2, z + h * 0.6))
        if tip:
            tube(gold, [(x, y, z + h * 0.97), (x, y, z + h + max(r * 0.5, 0.8))], lambda t: 0.16 * (1 - t) + 0.02, 4, (0.9, 0.6, 0.18))

    def tower(x, y, z, r, h, seg=8, roof_h=None, wins=True, band=True):
        c = wall_col()
        lathe(stone, [(r * 1.08, z), (r, z + 1), (r * 0.97, z + h)], x, y, seg, lambda p, w, e: tint(c, p.z, z, z + h), cap=False)
        if band:
            lathe(stone, [(r * 0.97, z + h), (r * 1.2, z + h + 0.4), (r * 1.2, z + h + 1.3), (r * 0.5, z + h + 1.3)], x, y, seg, lambda p, w, e: c, cap=False)
        spire(x, y, z + h + (1.2 if band else 0), r, roof_h or r * rnd.uniform(3.6, 5.2), seg)
        if wins:
            for zz in range(int(z + 4), int(z + h - 1), 4):
                for k in range(seg):
                    if rnd.random() < 0.34:
                        a = (k + 0.5) / seg * math.tau
                        n = (math.cos(a), math.sin(a))
                        window((x + n[0] * r * 0.92, y + n[1] * r * 0.92, zz), n, r * 0.24 + 0.2, r * 0.5 + 0.7)

    def house(x, y, z, w, d, h, rot):
        hbox(stone, x, y, z, w, d, h, rot)
        gable(x, y, z + h, w, d, rnd.uniform(0.7, 1.15) * w, rot)
        c, s = math.cos(rot), math.sin(rot)
        nx, ny = c, s
        for side in (-1, 1):
            n = (nx * side, ny * side)
            for fl in range(max(1, int(h / 3.4))):
                for t in (-0.26, 0.26):
                    if rnd.random() < 0.55:
                        px = x + n[0] * w / 2 + (-s) * d * t
                        py = y + n[1] * w / 2 + c * d * t
                        window((px, py, z + 1 + fl * 3.3), n, 0.8, 1.5)
        if rnd.random() < 0.3:
            hbox(stone, x + s * d * 0.25, y - c * d * 0.25, z + h, 0.7, 0.7, w * 0.9, rot, (0.3, 0.27, 0.24))

    # --- terraced ground ---
    gc = (0.34, 0.31, 0.25)
    lathe(stone, [(WALL_R + 2, -7), (WALL_R, 0), (T1_R + 0.6, 0), (T1_R, T1_Z), (T2_R + 0.6, T1_Z), (T2_R, T2_Z), (0.1, T2_Z)],
          0, 0, 48, lambda p, w, e: tint(gc, p.z, -7, 12))
    # arcades on the retaining walls
    for r, z, n in ((T1_R, 0, 44), (T2_R, T1_Z, 28)):
        for i in range(n):
            a = i / n * math.tau
            if math.sin(a) > 0.45:
                continue
            nrm = (math.cos(a), math.sin(a))
            window((nrm[0] * (r + 0.4), nrm[1] * (r + 0.4), z + 1.2), nrm, 2.0, 5.2, rnd.random() < 0.45)
            hbox(stone, nrm[0] * (r + 0.7), nrm[1] * (r + 0.7), z, 1.0, 1.0, 9.5 if z == 0 else 9.7, a)

    # --- curtain wall and towers ---
    def front(a):
        return math.sin(a) < 0.5     # the back of the city is never seen from the road
    n = 96
    for i in range(n):
        a = i / n * math.tau
        if not front(a):
            continue
        ax, ay = math.cos(a), math.sin(a)
        hbox(stone, ax * WALL_R, ay * WALL_R, -4, 6.0, 2.6, 13, a + math.pi / 2, (0.5, 0.45, 0.37))
        for t in (-1.6, 0, 1.6):
            hbox(stone, ax * WALL_R - ay * t, ay * WALL_R + ax * t, 9, 0.9, 2.8, 1.5, a + math.pi / 2, (0.56, 0.5, 0.42))
    for i in range(22):
        a = i / 22 * math.tau
        if front(a) and not (abs(a - 3 * math.pi / 2) < 0.1):
            r = rnd.uniform(2.6, 3.4)
            tower(math.cos(a) * WALL_R, math.sin(a) * WALL_R, -5, r, rnd.uniform(15, 19), 8, r * rnd.uniform(2.2, 3.0))
    # main gate facing the road
    for s in (-1, 1):
        tower(s * 8, -WALL_R - 1, -5, 3.8, 22, 10, 12)
    hbox(stone, 0, -WALL_R - 1, -4, 12, 5, 19, 0, (0.55, 0.49, 0.4))
    window((0, -WALL_R - 3.6, 0), (0, -1), 6, 9, True)

    # --- cathedral on the top tier ---
    Z = T2_Z
    cw = (0.74, 0.67, 0.56)
    hbox(stone, 0, 4, Z, 16, 58, 24, 0, cw)                     # nave
    gable(0, 4, Z + 24, 16, 58, 13, 0, 0.5)
    for s in (-1, 1):
        hbox(stone, s * 12, 4, Z, 8, 56, 13, 0, cw)             # aisles
        c0 = slate()
        verts = [Vector((s * 8, -24, Z + 19)), Vector((s * 16.6, -24, Z + 13)), Vector((s * 16.6, 32, Z + 13)), Vector((s * 8, 32, Z + 19))]
        roof.add(verts, [[0, 1, 2, 3]], [c0] * 4)
        for i in range(9):
            y = -22 + i * 6.4
            hbox(stone, s * 17.4, y, Z, 1.8, 2.0, 18, 0, cw, 0.6)         # buttress
            spire(s * 17.4, y, Z + 18, 0.9, 6, 4, False)
            window((s * 16, y + 3.2, Z + 2.5), (s, 0), 2.4, 8.5, True)
            window((s * 8, y + 3.2, Z + 15), (s, 0), 2.6, 7.5, True)
    # transept
    hbox(stone, 0, 10, Z, 48, 13, 24, 0, cw)
    gable(0, 10, Z + 24, 13, 48, 11, math.pi / 2, 0.5)
    for s in (-1, 1):
        window((s * 24, 10, Z + 5), (s, 0), 5, 15, True)
    # west front
    hbox(stone, 0, -25.5, Z, 18, 3, 30, 0, cw)
    window((0, -27, Z + 1), (0, -1), 5, 11, True)
    for s in (-1, 1):
        x = s * 11
        hbox(stone, x, -24, Z, 10, 10, 50, 0, cw, 0.92)
        for zz in (Z + 8, Z + 20, Z + 33):
            window((x, -29, zz), (0, -1), 2.4, 8, True)
        spire(x, -24, Z + 50, 4.4, 34, 8)
        for dx in (-1, 1):
            for dy in (-1, 1):
                spire(x + dx * 3.8, -24 + dy * 3.8, Z + 50, 0.9, 9, 4, False)
    # rose window
    lathe(gold, [(4.2, 0), (4.6, 0.25)], 0, 0, 20, lambda p, w, e: (0.9, 0.6, 0.18), cap=False)
    rose = [Vector((math.cos(i / 20 * math.tau) * 3.9, -27.15, Z + 22 + math.sin(i / 20 * math.tau) * 3.9)) for i in range(20)]
    win.add(rose, [list(range(19, -1, -1))], [(1, 0.8, 0.45)] * 20)
    # move the ring just built from the origin to the west front
    ring = gold.V[-40:]
    for i, v in enumerate(ring):
        gold.V[-40 + i] = Vector((v.x, -27.05 - v.z, Z + 22 + v.y))

    # crossing tower and the great spire
    CY = 10
    lathe(stone, [(9.5, Z + 24), (9, Z + 58), (10.4, Z + 59), (10.4, Z + 61), (7, Z + 62), (6.4, Z + 78), (7.4, Z + 79), (4.6, Z + 80)],
          0, CY, 8, lambda p, w, e: tint(cw, p.z, Z, Z + 50))
    spire(0, CY, Z + 80, 4.6, SPIRE_TOP - Z - 80 - 3, 8)
    for k in range(8):
        a = (k + 0.5) / 8 * math.tau
        n = (math.cos(a), math.sin(a))
        window((n[0] * 8.6, CY + n[1] * 8.6, Z + 30), n, 2.6, 9, True)
        window((n[0] * 6.1, CY + n[1] * 6.1, Z + 64), n, 1.6, 10, True)
        spire(n[0] * 9.6, CY + n[1] * 9.6, Z + 60, 1.0, 13, 4, False)
    # glowing clock face on the front of the tower
    fy = CY - 9.6
    cz = Z + 46
    face = [Vector((math.cos(i / 24 * math.tau) * 6, fy, cz + math.sin(i / 24 * math.tau) * 6)) for i in range(24)]
    win.add(face, [list(range(23, -1, -1))], [(1, 0.86, 0.55)] * 24)
    tube(gold, [(math.cos(i / 24 * math.tau) * 6.3, fy - 0.2, cz + math.sin(i / 24 * math.tau) * 6.3) for i in range(25)], 0.35, 5, (0.9, 0.6, 0.18))

    # flanking palace wings on the upper tier
    for s in (-1, 1):
        x = s * 29
        hbox(stone, x, -6, Z, 11, 24, 15, 0, cw)
        gable(x, -6, Z + 15, 11, 24, 8)
        for yy in (-16, -8, 0, 8):
            window((x - s * 0, yy - 4.0 if False else yy, Z + 0), (s, 0), 0.01, 0.01, False)
        tower(x, -19, Z, 3.6, 30, 8, 19)
        tower(x + s * 3, 6, Z, 3.0, 24, 8, 15)

    # --- clock tower on the right ---
    tx, ty, tz = 50, -33, 0
    hbox(stone, tx, ty, tz, 12, 12, 58, 0, (0.7, 0.63, 0.52), 0.86)
    hbox(stone, tx, ty, tz + 58, 12.4, 12.4, 12, 0, (0.68, 0.6, 0.5))
    hbox(stone, tx, ty, tz + 70, 14, 14, 1.2, 0, (0.6, 0.54, 0.44))
    for a in (0, 1, 2, 3):
        ang = a * math.pi / 2 - math.pi / 2
        n = (math.cos(ang), math.sin(ang))
        ctr = Vector((tx + n[0] * 6.3, ty + n[1] * 6.3, tz + 64))
        side = Vector((-n[1], n[0], 0))
        pts = [ctr + (side * math.cos(i / 20 * math.tau) + Vector((0, 0, 1)) * math.sin(i / 20 * math.tau)) * 4.2 for i in range(20)]
        win.add(pts, [list(range(19, -1, -1))], [(1, 0.8, 0.45)] * 20)
        tube(gold, [ctr + (side * math.cos(i / 20 * math.tau) + Vector((0, 0, 1)) * math.sin(i / 20 * math.tau)) * 4.5 + Vector((n[0], n[1], 0)) * 0.15 for i in range(21)], 0.28, 4, (0.9, 0.6, 0.18))
        for zz in (10, 22, 34, 46):
            window((tx + n[0] * 5.6, ty + n[1] * 5.6, tz + zz), n, 1.6, 5.5, True)
    spire(tx, ty, tz + 71, 7.4, 28, 4)
    for dx in (-1, 1):
        for dy in (-1, 1):
            spire(tx + dx * 6, ty + dy * 6, tz + 71, 1.3, 11, 6)

    # --- scattered towers ---
    placed = [(tx, ty, 12), (0, -40, 18)]
    for _ in range(46):
        a = rnd.uniform(0, math.tau)
        if not front(a):
            continue
        r = rnd.uniform(36, 80)
        x, y = math.cos(a) * r, math.sin(a) * r
        if any(math.hypot(x - p[0], y - p[1]) < p[2] for p in placed):
            continue
        placed.append((x, y, 7))
        tr = rnd.uniform(1.5, 2.8)
        tower(x, y, ground(x, y), tr, rnd.uniform(16, 44) * (1.2 - r / 110), rnd.choice((6, 8)), tr * rnd.uniform(4.5, 7))

    # --- houses in rings, packed towards the walls ---
    for r0, r1, step in ((37, 56, 9.5), (61, 80, 9.5)):
        r = r0
        while r < r1:
            circ = int(r * math.tau / 9.5)
            for i in range(circ):
                a = (i + rnd.uniform(-0.2, 0.2)) / circ * math.tau
                if not front(a) or rnd.random() < 0.1:
                    continue
                rr = r + rnd.uniform(-1.2, 1.2)
                x, y = math.cos(a) * rr, math.sin(a) * rr
                if any(math.hypot(x - p[0], y - p[1]) < p[2] * 0.75 for p in placed):
                    continue
                house(x, y, ground(x, y), rnd.uniform(5, 7.5), rnd.uniform(6, 9.5), rnd.uniform(6, 13), a + rnd.uniform(-0.2, 0.2))
            r += step

    # --- crags and viaducts ---
    def crag(cx, cy, ztop, zbot, r0, r1):
        rings, segs = 16, 24
        off = Vector((cx * 0.13, cy * 0.13, 4))
        verts, cols, faces = [], [], []
        for i in range(rings):
            t = i / (rings - 1)
            z = ztop + (zbot - ztop) * t
            for s in range(segs):
                a = s / segs * math.tau
                d = Vector((math.cos(a), math.sin(a), z * 0.03))
                rad = (r0 + (r1 - r0) * t) * (1 + fbm(d * 1.6 + off + Vector((0, 0, t * 2)), 3) * 0.9)
                p = Vector((cx + d.x * rad, cy + d.y * rad, z))
                verts.append(p)
                k = clamp(fbm(p * 0.09, 3) * 1.4 + 0.5)
                c = mix((0.1, 0.1, 0.1), (0.34, 0.31, 0.27), k)
                cols.append(mix((0.08, 0.13, 0.04), c, smooth(0.0, 0.12, t)))
        for i in range(rings - 1):
            for s in range(segs):
                u = (s + 1) % segs
                faces.append([i * segs + s, (i + 1) * segs + s, (i + 1) * segs + u, i * segs + u])
        faces.append(list(range(segs)))
        rock.add(verts, faces, cols)

    def viaduct(p0, direction, count, span, deck, base, width=7.0):
        d = Vector((direction[0], direction[1], 0)).normalized()
        side = Vector((-d.y, d.x, 0))
        p0 = Vector((p0[0], p0[1], 0))
        pw = span * 0.2
        ra = (span - pw) / 2
        spring = deck - ra - 1.6
        c0 = (0.62, 0.56, 0.47)
        rot = math.atan2(d.y, d.x)

        def slab(a, b):
            """a, b: (s, z_low, z_high) columns; builds the solid between them."""
            verts, cols = [], []
            for s, zl, zh in (a, b):
                for w_, z in ((-1, zl), (1, zl), (1, zh), (-1, zh)):
                    p = p0 + d * s + side * w_ * width / 2
                    verts.append(Vector((p.x, p.y, z)))
                    cols.append(tint(c0, z, deck - 40, deck))
            stone.add(verts, [[0, 1, 2, 3], [7, 6, 5, 4], [0, 4, 5, 1], [1, 5, 6, 2], [2, 6, 7, 3], [3, 7, 4, 0]], cols)

        for i in range(count + 1):
            s = i * span
            hbox(stone, *(p0 + d * s)[:2], base, pw, width + 2.4, spring - base + 0.5, rot, (0.56, 0.5, 0.42), 0.82)
            hbox(stone, *(p0 + d * s)[:2], spring, pw * 0.82, width + 0.2, deck - spring, rot, c0)
            if i < count:
                n = 12
                for k in range(n):
                    a0, a1 = math.pi * k / n, math.pi * (k + 1) / n
                    m = s + span / 2
                    slab((m - math.cos(a0) * ra, spring + math.sin(a0) * ra, deck), (m - math.cos(a1) * ra, spring + math.sin(a1) * ra, deck))
                # a second, smaller arch tier low on the piers
                z2 = spring - ra * 1.6
                if z2 > base + 8:
                    slab((s + pw * 0.4, z2 - 2.5, z2), (s + span - pw * 0.4, z2 - 2.5, z2))
            for t in (0.0, 0.5):
                if i == count and t:
                    continue
                q = p0 + d * (s + span * t)
                for w_ in (-1, 1):
                    l = q + side * w_ * (width / 2 - 0.2)
                    hbox(win, l.x, l.y, deck + 1.1, 0.5, 0.5, 0.8, rot, (1, 0.72, 0.36))
                    hbox(stone, l.x, l.y, deck, 0.3, 0.3, 1.1, rot, (0.2, 0.18, 0.16))
        for w_ in (-1, 1):
            q = p0 + d * (count * span / 2) + side * w_ * (width / 2 + 0.1)
            hbox(stone, q.x, q.y, deck, count * span, 0.5, 1.1, rot, c0)
        return p0 + d * (count * span)

    # right-hand viaduct, the one in the reference, ending at a fortified crag
    end = viaduct((WALL_R + 2, -14), (1, -0.14), 7, 21, 3, -105, 8)
    crag(end.x + 14, end.y - 2, 2, -135, 15, 34)
    tower(end.x + 8, end.y - 8, 2, 5, 24, 10, 20)
    tower(end.x + 20, end.y + 4, 2, 4, 15, 8, 13)
    hbox(stone, end.x + 16, end.y - 6, 2, 16, 11, 11, 0.2)
    gable(end.x + 16, end.y - 6, 13, 16, 11, 7, 0.2 + math.pi / 2)

    # lower viaduct on the left, leaving from below the walls
    end2 = viaduct((-WALL_R - 3, -30), (-1, -0.5), 3, 30, -30, -125, 8)
    crag(end2.x - 13, end2.y - 7, -30, -140, 15, 32)
    tower(end2.x - 9, end2.y - 8, -30, 5, 19, 10, 17)
    tower(end2.x - 20, end2.y - 2, -30, 3.8, 13, 8, 12)

    objs = [stone.to_object(scn, flat=True), roof.to_object(scn, flat=True), win.to_object(scn, flat=True),
            gold.to_object(scn, flat=True), rock.to_object(scn, sharp_deg=50)]
    info = export(objs, "city.glb")
    info["tris"] = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
    info["ends"] = {"right": [end.x, end.y], "left": [end2.x, end2.y]}
    return info, scn
