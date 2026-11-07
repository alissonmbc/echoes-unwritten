"""Eight sculpted rock chunks plus ivy curtains.

Each rock is a cluster of convex hulls, voxel-remeshed into one skin,
melted into a rounded mass, cut into flat-faced slabs with cracks between them, then
decimated and vertex-coloured. Node names rock_0..7, their cheap rock_N_lo copies and
ivy_0..3 are what index.html looks up. Rocks are about 6-8 m across, sitting on z=0.
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
    (7, 7.0, 5.0, 11.0, 0.45, 9000),   # tall slabs for the cliff face
    (6, 8.0, 5.0, 9.0, -0.35, 9000),
    (8, 6.5, 6.0, 12.0, 0.6, 9000),
    (6, 9.0, 5.5, 7.5, 0.25, 9000),
    (5, 9.0, 6.0, 4.5, 0.12, 6000),    # ledges
    (5, 7.0, 7.0, 3.6, -0.15, 5000),
    (3, 3.2, 2.8, 2.2, 0.3, 3000),     # boulders
    (4, 3.6, 3.0, 2.8, -0.4, 3400),
]
LO_TRIS = 1500   # the _lo copies, for the upper cliff rows and pillar crowns
CELL = 0.3       # slab width, as a fraction of a rock's longest side
SOFTEN = 30      # smoothing passes on the raw hulls; more gives a rounder mass


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


def slab_cell(p, off, size, tall):
    """Which slab p belongs to, and 0..1 for how far it sits from that slab's edge."""
    wobble = Vector((fbm(p * 0.3 + off, 2), fbm(p * 0.3 + off + Vector((3, 9, 0)), 2), 0)) * 0.45
    c = Vector((p.x / (size * CELL), p.y / (size * CELL), p.z / (size * CELL * tall))) + wobble + off
    dist, points = noise.voronoi(c)
    return tuple(round(x, 3) for x in points[0]), smooth(0.0, 0.09, dist[1] - dist[0])


def cut_slabs(bm, off, size, tall):
    """Flatten each Voronoi cell onto its own plane.

    The pull fades to nothing at a cell's edge, where a small dent makes the crack. Every cell
    reaches the same value there, so neighbouring slabs can't leave a hard step, and fitting the
    plane to the surface keeps the rock's overall size.
    """
    cells = {}
    for v in bm.verts:
        key, face = slab_cell(v.co, off, size, tall)
        cells.setdefault(key, []).append((v, face))
    for key, members in cells.items():
        r = random.Random(repr(key))
        n = sum((v.normal for v, _ in members), Vector())
        if n.length < len(members) * 0.4:      # wraps round a corner, so no single plane fits it
            n = None
        else:
            n = (n.normalized() + Vector((r.gauss(0, 0.13), r.gauss(0, 0.13), r.gauss(0, 0.13)))).normalized()
            plane = sum(v.co.dot(n) for v, _ in members) / len(members) + r.uniform(-0.25, 0.25)
        for v, face in members:
            dent = v.normal * (1 - face) * -0.2
            if n:
                v.co = v.co + n * clamp(plane - v.co.dot(n), -1.1, 1.1) * face * 0.94
            v.co = v.co + dent


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

    off = Vector((idx * 13.1, idx * 7.7, idx * 3.3))
    bm = bmesh.new()
    bm.from_mesh(skin)
    size = max(sx, sy, sz)

    # weathering first: melt the hulls into one rounded mass
    for _ in range(SOFTEN):
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.6, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    bm.normal_update()

    for v in bm.verts:
        v.co = v.co + v.normal * fbm(v.co * 0.16 + off, 2) * 0.7
    bm.normal_update()

    # then cut the slabs, soften their edges a touch, and add a very slight surface tooth
    cut_slabs(bm, off, size, 3.0 if idx < 4 else 1.15)   # cliff rocks split into upright slabs, the rest into blocks
    for _ in range(2):
        bmesh.ops.smooth_vert(bm, verts=bm.verts, factor=0.5, use_axis_x=True, use_axis_y=True, use_axis_z=True)
    for v in bm.verts:
        p = v.co
        v.co = p + Vector((fbm(p * 0.7 + off, 2), fbm(p * 0.7 + off + Vector((8, 0, 0)), 2), fbm(p * 0.7 - off, 2))) * 0.05
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

    # colour: warm ochre stone, broad grey weathering, dark cracks, moss low down on what faces up
    col = {}
    for p in final.polygons:
        up = p.normal.z
        for vi in p.vertices:
            a = col.setdefault(vi, [0.0, 0])
            a[0] += up
            a[1] += 1
    # cracks: a vertex sitting below the average of its neighbours is in a crevice
    near = [[Vector(), 0, 0.0] for _ in final.vertices]
    for e in final.edges:
        a, b = e.vertices
        pa, pb = final.vertices[a].co, final.vertices[b].co
        for i, q in ((a, pb), (b, pa)):
            near[i][0] += q
            near[i][1] += 1
            near[i][2] += (q - final.vertices[i].co).length
    at = final.color_attributes.new("Color", "FLOAT_COLOR", "POINT")
    flat = []
    for v in final.vertices:
        p = v.co
        k = fbm(p * 0.12 + off, 3)
        c = mix((0.24, 0.195, 0.145), (0.43, 0.345, 0.245), clamp(k * 1.3 + 0.5))
        c = mix(c, (0.25, 0.24, 0.225), smooth(0.0, 0.32, fbm(p * 0.07 + off + Vector((5, 5, 5)), 2)) * 0.55)
        total, count, length = near[v.index]
        if count:
            dent = (total / count - p).dot(v.normal) / max(length / count, 1e-4)
            c = mix(c, (0.05, 0.043, 0.036), smooth(0.04, 0.3, dent) * 0.85)
        s, m = col.get(v.index, (0.0, 1))
        up = s / max(m, 1)
        low = 1 - smooth(0.25, 0.55, p.z / max(sz, 0.01))
        moss = smooth(0.42, 0.78, up) * clamp(fbm(p * 0.5 + off, 3) * 2.2 + 0.72) * (0.35 + low * 0.65)
        c = mix(c, (0.09, 0.125, 0.04), moss * 0.85)
        flat.extend((c[0], c[1], c[2], 1.0))
    at.data.foreach_set("color", flat)
    final.color_attributes.active_color = at
    final.shade_smooth()
    final.set_sharp_from_angle(angle=math.radians(80))
    final.materials.append(bpy.data.materials["rock"])
    out = bpy.data.objects.new(f"rock_{idx}", final)
    scn.collection.objects.link(out)
    return out


def low_poly(scn, rock_ob):
    """A cheap copy with the same colours, for rocks that are never seen up close."""
    ob = bpy.data.objects.new("_lo", rock_ob.data.copy())
    scn.collection.objects.link(ob)
    dec = ob.modifiers.new("dec", "DECIMATE")
    dec.ratio = clamp(LO_TRIS / max(sum(len(p.vertices) - 2 for p in rock_ob.data.polygons), 1), 0.01, 1)
    me = evaluated_copy(scn, ob, rock_ob.name + "_lo")
    old = ob.data
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.meshes.remove(old)
    out = bpy.data.objects.new(rock_ob.name + "_lo", me)
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
    lows = [low_poly(scn, o) for o in objs]
    objs += ivies + lows
    info = export(objs, "rocks.glb")
    info["tris"] = {o.name: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs}
    return info, scn
