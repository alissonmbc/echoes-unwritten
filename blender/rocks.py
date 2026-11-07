"""Eight sculpted rock chunks plus two ivy curtains.

Each rock is a cluster of convex hulls, voxel-remeshed into one skin, displaced along
tilted strata, then decimated and vertex-coloured. Node names rock_0..7 and ivy_0..1
are what index.html looks up. Rocks are about 6-8 m across, sitting on z=0.
"""
import math
import random

import bmesh
import bpy
from mathutils import Matrix, Vector, noise
from mathutils.bvhtree import BVHTree

from common import Part, clamp, export, fbm, leaves, material, mix, smooth, use_scene

# (hull count, overall size x, y, z, strata tilt, target triangles)
SPECS = [
    (7, 7.0, 5.0, 11.0, 0.45, 12000),  # tall slabs for the cliff face
    (6, 8.0, 5.0, 9.0, -0.35, 12000),
    (8, 6.5, 6.0, 12.0, 0.6, 12000),
    (6, 9.0, 5.5, 7.5, 0.25, 11000),
    (5, 9.0, 6.0, 4.5, 0.12, 7000),    # ledges
    (5, 7.0, 7.0, 3.6, -0.15, 6000),
    (3, 3.2, 2.8, 2.2, 0.3, 3000),     # boulders
    (4, 3.6, 3.0, 2.8, -0.4, 3400),
]


def hull_cluster(rnd, n, sx, sy, sz, tilt):
    bm = bmesh.new()
    rot = Matrix.Rotation(tilt, 3, "Y")
    for i in range(n):
        c = Vector((rnd.uniform(-0.32, 0.32) * sx, rnd.uniform(-0.28, 0.28) * sy, rnd.uniform(0.2, 0.74) * sz))
        hx, hy, hz = (rnd.uniform(0.3, 0.55) * s for s in (sx, sy, sz * 0.75))
        vs = []
        for _ in range(rnd.randint(14, 20)):
            # points on a box surface give big flat planes rather than a pebble
            p = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1, 1)))
            a = rnd.randrange(3)
            p[a] = math.copysign(1, p[a])
            p = rot @ Vector((p.x * hx, p.y * hy, p.z * hz)) + c
            vs.append(bm.verts.new(p))
        bmesh.ops.convex_hull(bm, input=vs, use_existing_faces=False)
    # a wide foot keeps the rock from looking balanced on a point
    foot = [bm.verts.new((rnd.uniform(-0.55, 0.55) * sx, rnd.uniform(-0.5, 0.5) * sy, rnd.uniform(-0.3, 0.15) * sz * 0.3)) for _ in range(16)]
    foot += [bm.verts.new((rnd.uniform(-0.35, 0.35) * sx, rnd.uniform(-0.3, 0.3) * sy, rnd.uniform(0.2, 0.4) * sz)) for _ in range(8)]
    bmesh.ops.convex_hull(bm, input=foot, use_existing_faces=False)
    for v in [v for v in bm.verts if not v.link_faces]:
        bm.verts.remove(v)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return bm


def evaluated_copy(scn, ob, name):
    dg = bpy.context.evaluated_depsgraph_get()
    dg.update()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    me.name = name
    return me


def sculpt(scn, spec, idx, rnd):
    n, sx, sy, sz, tilt, target = spec
    me = bpy.data.meshes.new(f"_raw{idx}")
    bm = hull_cluster(rnd, n, sx, sy, sz, tilt)
    bm.to_mesh(me)
    bm.free()
    ob = bpy.data.objects.new(f"_raw{idx}", me)
    scn.collection.objects.link(ob)

    voxel = max(sx, sy, sz) / 90
    rm = ob.modifiers.new("remesh", "REMESH")
    rm.mode = "VOXEL"
    rm.voxel_size = voxel
    rm.use_smooth_shade = False
    skin = evaluated_copy(scn, ob, f"_skin{idx}")
    ob.modifiers.clear()
    ob.data = skin
    bpy.data.meshes.remove(me)

    axis = (Matrix.Rotation(tilt, 3, "Y") @ Vector((0, 0, 1))).normalized()
    off = Vector((idx * 13.1, idx * 7.7, idx * 3.3))
    bm = bmesh.new()
    bm.from_mesh(skin)
    bm.normal_update()
    size = max(sx, sy, sz)
    for v in bm.verts:
        v.co = v.co + v.normal * fbm(v.co * 0.16 + off, 2) * 0.9

    # chisel: rock fractures along joint sets, so snap the skin onto planes from three
    # families (bedding plus two steep joints) rather than adding round noise
    j1 = axis
    j2 = axis.cross(Vector((0.3, 1, 0.1))).normalized()
    j3 = j1.cross(j2).normalized()
    fams = (j1, j2, j3)
    cell = size / 11
    scales = (cell * 0.9, cell * 2.1, cell * 1.7)   # cells are thin across the bedding

    def patch_key(p, n):
        c = Vector((p.dot(j1) / scales[0], p.dot(j2) / scales[1], p.dot(j3) / scales[2])) + off
        f = noise.voronoi(c)[1][0]
        best = max(range(3), key=lambda i: abs(n.dot(fams[i])))
        return (round(f[0], 3), round(f[1], 3), round(f[2], 3), best, n.dot(fams[best]) > 0)

    groups = {}
    for v in bm.verts:
        groups.setdefault(patch_key(v.co, v.normal), []).append(v)
    for key, vs in groups.items():
        r = random.Random(hash(key))
        fam = fams[key[3]] * (1 if key[4] else -1)
        n = (fam + Vector((r.gauss(0, 0.2), r.gauss(0, 0.2), r.gauss(0, 0.2)))).normalized()
        mean = sum(v.co.dot(n) for v in vs) / len(vs)
        target_d = mean - r.uniform(0.0, 0.5) * cell
        for v in vs:
            e = v.co.dot(n) - target_d
            v.co = v.co - n * max(min(e, cell * 1.5), -cell * 1.5) * 0.93

    # thin bedding seams and a little surface tooth
    for v in bm.verts:
        p = v.co
        h = p.dot(axis) / size * 7 + fbm(p * 0.1 + off, 2) * 1.2
        seam = smooth(0.93, 0.995, abs((h % 1.0) - 0.5) * 2) * 0.13
        v.co = p - axis * seam + Vector((fbm(p * 0.9 + off, 2), fbm(p * 0.9 + off + Vector((8, 0, 0)), 2), fbm(p * 0.9 - off, 2))) * 0.09
    zcut = min(v.co.z for v in bm.verts) + 0.22 * sz
    for v in bm.verts:
        v.co.z = max(v.co.z, zcut)
    bm.to_mesh(skin)
    bm.free()

    dec = ob.modifiers.new("dec", "DECIMATE")
    dec.ratio = clamp(target / max(len(skin.polygons) * 2.0, 1), 0.01, 1)
    final = evaluated_copy(scn, ob, f"rock_{idx}")
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(skin)
    final.validate()

    # recentre on the footprint and put the base on z=0
    zs = [v.co.z for v in final.vertices]
    cx = sum(v.co.x for v in final.vertices) / len(final.vertices)
    cy = sum(v.co.y for v in final.vertices) / len(final.vertices)
    zmin = min(zs)
    for v in final.vertices:
        v.co -= Vector((cx, cy, zmin))
    final.update()

    # colour: cool grey stone, warm iron stains, darker cracks, moss on what faces up
    col = {}
    for p in final.polygons:
        up = p.normal.z
        for vi in p.vertices:
            a = col.setdefault(vi, [0.0, 0])
            a[0] += up
            a[1] += 1
    at = final.color_attributes.new("Color", "FLOAT_COLOR", "POINT")
    flat = []
    for v in final.vertices:
        p = v.co
        k = fbm(p * 0.33 + off, 3)
        c = mix((0.125, 0.122, 0.118), (0.40, 0.385, 0.355), clamp(k * 1.4 + 0.5))
        h = p.dot(axis) / size * 7 + fbm(p * 0.1 + off, 2) * 1.2
        band = abs((h % 1.0) - 0.5) * 2
        c = mix(c, (0.07, 0.066, 0.06), smooth(0.9, 1.0, band) * 0.55)
        c = mix(c, (0.37, 0.27, 0.17), smooth(0.05, 0.3, fbm(p * 0.17 + off + Vector((5, 5, 5)), 2)) * 0.42)
        s, m = col.get(v.index, (0.0, 1))
        up = s / max(m, 1)
        moss = smooth(0.42, 0.78, up) * clamp(fbm(p * 0.5 + off, 3) * 2.2 + 0.72)
        c = mix(c, (0.09, 0.125, 0.04), moss * 0.85)
        flat.extend((c[0], c[1], c[2], 1.0))
    at.data.foreach_set("color", flat)
    final.color_attributes.active_color = at
    final.shade_smooth()
    final.set_sharp_from_angle(angle=math.radians(58))
    final.materials.append(bpy.data.materials["rock"])
    out = bpy.data.objects.new(f"rock_{idx}", final)
    scn.collection.objects.link(out)
    return out


def ivy_on_rock(scn, rock_ob, idx, rnd):
    """Grow strands down the rock's own surface, so the ivy clings wherever it's instanced.

    Exported as ivy_<idx>; index.html gives it the same instance matrices as rock_<idx>.
    """
    me = rock_ob.data
    tree = BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    zmax = max(v.co.z for v in me.vertices)
    tops = [p.center.copy() for p in me.polygons if p.normal.z > 0.1 and p.center.z > zmax * 0.5]
    part = Part(f"ivy_{idx}", bpy.data.materials["leaf"])
    anchors = []
    for _ in range(7):
        seed = rnd.choice(tops)
        for _ in range(rnd.randint(5, 9)):
            p = seed + Vector((rnd.gauss(0, 0.8), rnd.gauss(0, 0.8), rnd.uniform(-0.3, 0.3)))
            ph = rnd.uniform(0, 9)
            for i in range(rnd.randint(18, 52)):
                p = p + Vector((math.sin(i * 0.25 + ph) * 0.05, math.cos(i * 0.21 + ph) * 0.05, -0.15))
                hit, nrm, _, dist = tree.find_nearest(p)
                if hit is None or hit.z < 0.5 or dist > 1.2:
                    break
                p = hit + nrm * 0.05
                for _ in range(2):
                    q = p + nrm * rnd.uniform(0, 0.16) + Vector((rnd.uniform(-0.2, 0.2), rnd.uniform(-0.2, 0.2), rnd.uniform(-0.12, 0.12)))
                    anchors.append((q, nrm))
    leaves(part, anchors, rnd, 0.1)
    return part.to_object(scn, flat=True)


def build():
    rnd = random.Random(23)
    scn = use_scene("Lumina_Rocks")
    material("rock", rough=0.95)
    material("leaf", rough=0.8, double=True)
    objs = [sculpt(scn, s, i, rnd) for i, s in enumerate(SPECS)]
    ivies = [ivy_on_rock(scn, objs[i], i, rnd) for i in range(4)]
    for i, o in enumerate(objs):
        o.location = ((i % 4) * 14 - 21, (i // 4) * 14, 0)
    for i, o in enumerate(ivies):
        o.location = objs[i].location
    objs += ivies
    info = export(objs, "rocks.glb")
    info["tris"] = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
    return info, scn
