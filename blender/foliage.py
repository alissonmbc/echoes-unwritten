"""Trees, verge bushes and grass: real branches, clumps of leaf quads and curved blades.

Each plant is a pair of nodes, <name>_wood (trees only) and <name>_leaf, with its base at the
origin. useFoliage() in index.html instances them. A tree stands about 6 units tall at scale 1, like
the low-poly tree it replaces, and a bush about 1.2.

Leaf normals are baked to point out of the clump, not along each leaf, so a clump shades
like one soft mass instead of thousands of randomly lit flakes.
"""
import math
import random

from mathutils import Vector

from common import Part, export, material, mix, tube, use_scene

SUN = Vector((-0.85, 0.5, 0.24)).normalized()   # three.js SUN in Blender axes
UP = Vector((0, 0, 1))

GREENS = ((0.025, 0.042, 0.01), (0.11, 0.14, 0.024), (0.25, 0.25, 0.045))   # shade, body, sunlit olive-gold
DEEP = ((0.016, 0.034, 0.01), (0.06, 0.105, 0.022), (0.15, 0.2, 0.04))
BARK = (0.075, 0.05, 0.032)
BLOOMS = ((0.62, 0.48, 0.85), (0.88, 0.84, 0.92), (0.95, 0.72, 0.2))      # violet, white, gold


def rand_dir(rnd):
    while True:
        v = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))
        if 0.01 < v.length <= 1:
            return v.normalized()


def leaf_quad(part, normals, p, normal, size, col, rnd, tip=None):
    """One diamond leaf at p. `normal` is the baked shading normal, not the leaf's own."""
    d = (tip or rand_dir(rnd) + Vector((0, 0, -0.5))).normalized()
    side = d.cross(rand_dir(rnd))
    if side.length < 0.1:
        return
    side.normalize()
    ln = size * rnd.uniform(0.75, 1.3)
    a, b = p - d * ln, p + d * ln
    w = side * ln * 0.55
    part.add([a, p + w, b, p - w], [(0, 1, 2, 3)], [col] * 4)
    normals.extend([normal] * 4)


def clump(part, normals, centre, radius, count, size, crown, palette, rnd):
    """A squashed ball of leaves. `crown` is the plant's middle, used to bend normals outward."""
    lo, mid, hi = palette
    for i in range(count):
        d = rand_dir(rnd)
        inner = i < count * 0.25                   # big dark leaves fill the middle, so light can't pass through
        r = radius * (rnd.uniform(0.25, 0.6) if inner else rnd.uniform(0.62, 1.05))
        off = Vector((d.x * r, d.y * r, d.z * r * 0.78))
        p = centre + off
        out = (d * 0.75 + (p - crown).normalized() * 0.55 + UP * 0.35).normalized()
        lit = max(out.dot(SUN), 0) * 0.65 + (d.z * 0.5 + 0.5) * 0.35 + rnd.uniform(-0.12, 0.12)
        col = mix(lo, mid, min(lit * 2, 1)) if lit < 0.5 else mix(mid, hi, min((lit - 0.5) * 2, 1))
        if inner:
            col = mix(lo, col, 0.35)
        leaf_quad(part, normals, p, out, size * (1.5 if inner else 1), col, rnd)


def finish(part, normals, scn):
    ob = part.to_object(scn)
    me = ob.data
    me.normals_split_custom_set_from_vertices([tuple(n) for n in normals])
    return ob


def tree(scn, name, leaf_mat, wood_mat, rnd, per_clump, size):
    wood = Part(name + "_wood", wood_mat)
    leaf = Part(name + "_leaf", leaf_mat)
    normals = []
    lean = Vector((rnd.uniform(-0.3, 0.3), rnd.uniform(-0.3, 0.3), 0))
    trunk = [Vector((0, 0, -0.3)) + lean * (t / 6) ** 2 * 1.4 + UP * (t / 6) * 3.3 for t in range(7)]
    tube(wood, trunk, lambda t: 0.2 * (1 - t * 0.62), segs=6, col=BARK)
    crown = Vector((trunk[-1].x, trunk[-1].y, 4.2))
    clumps = [(crown + Vector((0, 0, 0.9)), 1.2)]
    n = 7
    for i in range(n):
        a = i / n * math.tau + rnd.uniform(-0.3, 0.3)
        start = trunk[rnd.randint(3, 6)]
        reach = rnd.uniform(1.2, 1.9)
        tip = crown + Vector((math.cos(a) * reach, math.sin(a) * reach, rnd.uniform(-0.7, 0.6)))
        midp = (start + tip) / 2 + Vector((0, 0, rnd.uniform(0.1, 0.4)))
        tube(wood, [start, midp, tip], lambda t: 0.08 * (1 - t * 0.7), segs=4, col=BARK)
        clumps.append((tip, rnd.uniform(0.85, 1.25)))
        side = tip + Vector((rnd.uniform(-0.8, 0.8), rnd.uniform(-0.8, 0.8), rnd.uniform(-0.1, 0.5)))
        clumps.append((side, rnd.uniform(0.6, 0.9)))
    for c, r in clumps:
        clump(leaf, normals, c, r, int(per_clump * r), size, crown, GREENS, rnd)
    return [wood.to_object(scn), finish(leaf, normals, scn)]


def bush(scn, name, leaf_mat, rnd, palette, flowers=0, bloom=None):
    leaf = Part(name + "_leaf", leaf_mat)
    normals = []
    crown = Vector((0, 0, 0.4))
    balls = [(Vector((0, 0, 0.62)), 0.62)]
    for i in range(5):
        a = i / 5 * math.tau + rnd.uniform(-0.4, 0.4)
        d = rnd.uniform(0.4, 0.72)
        balls.append((Vector((math.cos(a) * d, math.sin(a) * d, rnd.uniform(0.22, 0.5))), rnd.uniform(0.36, 0.52)))
    for c, r in balls:
        clump(leaf, normals, c, r, int(520 * r), 0.05, crown, palette, rnd)
    for _ in range(flowers):
        c, r = rnd.choice(balls)
        d = rand_dir(rnd)
        d.z = abs(d.z) * 0.8 + 0.2
        d.normalize()
        p = c + Vector((d.x * r * 1.04, d.y * r * 1.04, d.z * r * 0.86))
        col = tuple(v * rnd.uniform(0.85, 1.1) for v in bloom)
        leaf_quad(leaf, normals, p, (d + UP * 0.6).normalized(), 0.042, col, rnd, tip=d.cross(UP) + UP * 0.2)
    return [finish(leaf, normals, scn)]


def grass(scn, name, leaf_mat, rnd, root, body, tip, blades=12):
    """A tuft of curved, tapering blades. Normals lean up and out, so a tuft lights as one soft mass."""
    leaf = Part(name + "_leaf", leaf_mat)
    normals = []
    for _ in range(blades):
        a = rnd.uniform(0, math.tau)
        out = Vector((math.cos(a), math.sin(a), 0))
        side = Vector((-out.y, out.x, 0))
        start = out * rnd.uniform(0, 0.16)
        height = rnd.uniform(0.34, 0.82)
        lean = rnd.uniform(0.1, 0.42)
        width = rnd.uniform(0.016, 0.03)
        tone = rnd.uniform(0.75, 1.2)
        dry = rnd.random()
        end = tuple(c * tone for c in mix(tip, (0.5, 0.36, 0.12), dry * 0.6))
        mid = tuple(c * tone for c in body)

        def spine(t):
            return start + out * lean * t * t + UP * height * t

        verts, cols = [], []
        for t, c in ((0, root), (0.38, mix(root, mid, 0.8)), (0.72, mix(mid, end, 0.6))):
            w = side * width * (1 - t * 0.55)
            verts += [spine(t) - w, spine(t) + w]
            cols += [c, c]
        verts.append(spine(1))
        cols.append(end)
        leaf.add(verts, [(0, 1, 3, 2), (2, 3, 5, 4), (4, 5, 6)], cols)
        normals.extend([(out * 0.5 + UP).normalized()] * 7)
    return [finish(leaf, normals, scn)]


def build():
    rnd = random.Random(41)
    scn = use_scene("Lumina_Foliage")
    leaf_mat = material("leaf", rough=0.72, double=True)
    wood_mat = material("bark", rough=0.95)
    objs = []
    objs += tree(scn, "tree_0", leaf_mat, wood_mat, rnd, 230, 0.12)
    objs += tree(scn, "tree_1", leaf_mat, wood_mat, rnd, 230, 0.12)
    objs += tree(scn, "tree_far", leaf_mat, wood_mat, rnd, 60, 0.3)
    objs += bush(scn, "bush_0", leaf_mat, rnd, GREENS)
    objs += bush(scn, "bush_1", leaf_mat, rnd, DEEP)
    for i, bloom in enumerate(BLOOMS):
        objs += bush(scn, f"bloom_{i}", leaf_mat, rnd, DEEP, flowers=170, bloom=bloom)
    objs += grass(scn, "grass_0", leaf_mat, rnd, (0.05, 0.05, 0.016), (0.2, 0.17, 0.05), (0.4, 0.3, 0.09))
    objs += grass(scn, "grass_1", leaf_mat, rnd, (0.04, 0.05, 0.016), (0.13, 0.16, 0.04), (0.3, 0.3, 0.08))
    info = export(objs, "foliage.glb")
    info["tris"] = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
    return (info,)
