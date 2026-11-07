"""Shared helpers for the Lumina asset scripts (run inside Blender).

Axis convention: Blender X = lateral (+X toward the cliff), -Y = toward the walker,
Z = up. The glTF exporter turns that into three.js +X, +Z, +Y, which matches
orient() in index.html.
"""
import math
import os
import random

import bmesh
import bpy
from mathutils import Vector, noise

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ASSETS = os.path.join(ROOT, "assets")


# ---------- scenes / materials / export ----------
def use_scene(name):
    """Switch to a scene owned by these scripts, emptying it first."""
    scn = bpy.data.scenes.get(name) or bpy.data.scenes.new(name)
    for o in list(scn.collection.all_objects):
        data = o.data
        bpy.data.objects.remove(o, do_unlink=True)
        if isinstance(data, bpy.types.Mesh) and data.users == 0:
            bpy.data.meshes.remove(data)
    wm = bpy.context.window_manager
    win = bpy.context.window or (wm.windows[0] if wm.windows else None)
    if win:
        win.scene = scn
    return scn


def material(name, color=None, rough=0.85, metal=0.0, emissive=None, double=False):
    """Principled material. color=None means base colour comes from vertex colours."""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    for n in list(nt.nodes):
        if n.type == "VERTEX_COLOR":
            nt.nodes.remove(n)
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    if color is None:
        vc = nt.nodes.new("ShaderNodeVertexColor")
        vc.layer_name = "Color"
        nt.links.new(vc.outputs["Color"], bsdf.inputs["Base Color"])
    else:
        bsdf.inputs["Base Color"].default_value = (*color, 1)
    if emissive:
        bsdf.inputs["Emission Color"].default_value = (*emissive, 1)
        bsdf.inputs["Emission Strength"].default_value = 3.0
    m.use_backface_culling = not double
    return m


def export(objs, filename):
    os.makedirs(ASSETS, exist_ok=True)
    path = os.path.join(ASSETS, filename)
    bpy.context.view_layer.update()
    for o in bpy.context.scene.objects:
        o.select_set(False)
    for o in objs:
        o.select_set(True)
    bpy.context.view_layer.objects.active = objs[0]
    bpy.ops.export_scene.gltf(
        filepath=path, export_format="GLB", use_selection=True, use_active_scene=True, export_apply=True,
        export_yup=True, export_vertex_color="ACTIVE", export_normals=True,
        export_texcoords=False, export_materials="EXPORT",
    )
    return {"file": filename, "kb": os.path.getsize(path) // 1024}


def preview(scn, path, loc, target, lens=35, size=(960, 600), sun=(-0.85, -0.5, 0.3)):
    """Eevee still for a quick look. The camera and sun are never exported."""
    cam = bpy.data.objects.new("_cam", bpy.data.cameras.new("_cam"))
    cam.data.lens = lens
    cam.data.clip_end = 3000
    cam.location = loc
    d = Vector(target) - Vector(loc)
    cam.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()
    lamp = bpy.data.objects.new("_sun", bpy.data.lights.new("_sun", "SUN"))
    lamp.data.energy = 4
    lamp.data.color = (1, 0.82, 0.62)
    lamp.rotation_euler = Vector(sun).to_track_quat("Z", "Y").to_euler()
    scn.collection.objects.link(cam)
    scn.collection.objects.link(lamp)
    if scn.world is None:
        scn.world = bpy.data.worlds.new("_w")
    scn.world.use_nodes = True
    bg = next(n for n in scn.world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs[0].default_value = (0.62, 0.68, 0.8, 1)
    bg.inputs[1].default_value = 0.9
    scn.camera = cam
    scn.render.engine = "BLENDER_EEVEE"
    scn.render.resolution_x, scn.render.resolution_y = size
    scn.render.resolution_percentage = 100
    scn.render.filepath = path
    scn.render.image_settings.file_format = "PNG"
    bpy.ops.render.render(write_still=True, scene=scn.name)
    return path


# ---------- noise ----------
def fbm(p, octaves=4, lac=2.03):
    p = Vector(p)
    s, a = 0.0, 0.5
    for _ in range(octaves):
        s += a * noise.noise(p)
        p = p * lac + Vector((1.7, 9.2, 3.1))
        a *= 0.5
    return s


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(a, b, x):
    t = clamp((x - a) / (b - a))
    return t * t * (3 - 2 * t)


def mix(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


# ---------- geometry accumulator ----------
class Part:
    """One mesh object built from many pieces, with per-vertex colour."""

    def __init__(self, name, mat):
        self.name, self.mat = name, mat
        self.V, self.F, self.C = [], [], []

    def add(self, verts, faces, cols):
        base = len(self.V)
        self.V.extend(verts)
        self.C.extend(cols)
        self.F.extend(tuple(i + base for i in f) for f in faces)

    def to_object(self, scn, sharp_deg=38, flat=False, parent=None):
        me = bpy.data.meshes.new(self.name)
        me.from_pydata([tuple(v) for v in self.V], [], self.F)
        me.update()
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        at = me.color_attributes.new("Color", "FLOAT_COLOR", "POINT")
        flatc = []
        for c in self.C:
            flatc.extend((c[0], c[1], c[2], 1.0))
        at.data.foreach_set("color", flatc)
        me.color_attributes.active_color = at
        if flat:
            me.shade_flat()
        else:
            me.shade_smooth()
            me.set_sharp_from_angle(angle=math.radians(sharp_deg))
        me.materials.append(self.mat)
        ob = bpy.data.objects.new(self.name, me)
        scn.collection.objects.link(ob)
        if parent:
            ob.parent = parent
        return ob


# ---------- rounded, chipped stone blocks ----------
_TOPO = {}


def _box_topo(m):
    """Vertex grid (index triples) and outward quads for a cube with m cells per edge."""
    if m in _TOPO:
        return _TOPO[m]
    idx, verts = {}, []

    def vid(i, j, k):
        key = (i, j, k)
        if key not in idx:
            idx[key] = len(verts)
            verts.append(key)
        return idx[key]

    faces = []
    for a in range(m):
        for b in range(m):
            q = [(a, b), (a + 1, b), (a + 1, b + 1), (a, b + 1)]
            faces.append([vid(m, y, z) for y, z in q])
            faces.append([vid(0, y, z) for y, z in reversed(q)])
            faces.append([vid(x, m, z) for z, x in q])
            faces.append([vid(x, 0, z) for z, x in reversed(q)])
            faces.append([vid(x, y, m) for x, y in q])
            faces.append([vid(x, y, 0) for x, y in reversed(q)])
    _TOPO[m] = (verts, faces)
    return _TOPO[m]


def _axis(m, b):
    """Grid positions in -1..1: bevel row, optional mid rows, bevel row."""
    if m == 1:
        return [-1.0, 1.0]
    inner = [-1 + 2 * b + (2 - 4 * b) * i / (m - 2) for i in range(m - 1)]
    return [-1.0] + inner + [1.0]


def stone(part, c, bevel=0.035, cells=3, chip=0.02, colfn=None, rnd=random):
    """c[i][j][k]: the 8 corners (i=u, j=v, k=w), right-handed. Trilinear-mapped rounded box."""
    dims = (
        max((c[1][0][0] - c[0][0][0]).length, (c[1][1][1] - c[0][1][1]).length, 1e-3),
        max((c[0][1][0] - c[0][0][0]).length, (c[1][1][1] - c[1][0][1]).length, 1e-3),
        max((c[0][0][1] - c[0][0][0]).length, (c[1][1][1] - c[1][1][0]).length, 1e-3),
    )
    h = [d / 2 for d in dims]
    b = min(bevel, min(h) * 0.45)
    ax = [_axis(cells, b / h[i]) for i in range(3)]
    grid, faces = _box_topo(cells)
    off = Vector((rnd.uniform(0, 90), rnd.uniform(0, 90), rnd.uniform(0, 90)))
    verts, cols = [], []
    for (i, j, k) in grid:
        p = [ax[0][i] * h[0], ax[1][j] * h[1], ax[2][k] * h[2]]
        q = [clamp(p[n], -(h[n] - b), h[n] - b) for n in range(3)]
        d = Vector([p[n] - q[n] for n in range(3)])
        if d.length > 1e-6:
            d = d.normalized() * b
        u, v, w = [((q[n] + d[n]) / h[n] + 1) / 2 for n in range(3)]
        pos = Vector()
        for a, wa in ((0, 1 - u), (1, u)):
            for e, we in ((0, 1 - v), (1, v)):
                for g, wg in ((0, 1 - w), (1, w)):
                    pos += c[a][e][g] * (wa * we * wg)
        if chip:
            n = Vector((noise.noise(pos * 1.7 + off), noise.noise(pos * 1.7 + off + Vector((31, 0, 0))),
                        noise.noise(pos * 1.7 + off + Vector((0, 57, 0)))))
            pos = pos + n * chip * 2
        verts.append(pos)
        edge = sum(1 for t in ((u, h[0]), (v, h[1]), (w, h[2])) if abs(t[0] - 0.5) > 0.5 - b / (2 * t[1]) - 1e-4)
        cols.append(colfn(pos, w, edge) if colfn else (0.5, 0.5, 0.5))
    part.add(verts, faces, cols)


def box_corners(x0, x1, y0, y1, z0, z1):
    return [[[Vector((x, y, z)) for z in (z0, z1)] for y in (y0, y1)] for x in (x0, x1)]


def prism_corners(p00, p10, p11, p01, y0, y1):
    """Quad in the XZ plane (u along p00->p10, w along p00->p01) extruded along Y."""
    def at(p, y):
        return Vector((p[0], y, p[1]))
    return [
        [[at(p00, y0), at(p01, y0)], [at(p00, y1), at(p01, y1)]],
        [[at(p10, y0), at(p11, y0)], [at(p10, y1), at(p11, y1)]],
    ]


def lathe(part, profile, cx, cy, segs=12, colfn=None, cap=True, squash=(1, 1)):
    """Surface of revolution from (radius, z) pairs."""
    verts, cols, faces = [], [], []
    for r, z in profile:
        for s in range(segs):
            a = s / segs * math.tau
            p = Vector((cx + math.cos(a) * r * squash[0], cy + math.sin(a) * r * squash[1], z))
            verts.append(p)
            cols.append(colfn(p, 0.5, 0) if colfn else (0.5, 0.5, 0.5))
    for i in range(len(profile) - 1):
        for s in range(segs):
            t = (s + 1) % segs
            faces.append([i * segs + s, i * segs + t, (i + 1) * segs + t, (i + 1) * segs + s])
    if cap:
        faces.append(list(range(segs - 1, -1, -1)))
        n = (len(profile) - 1) * segs
        faces.append([n + s for s in range(segs)])
    part.add(verts, faces, cols)


def tube(part, pts, radius, segs=6, col=(0.05, 0.05, 0.05)):
    """Sweep a circle along a polyline. radius may be a number or a function of 0..1."""
    pts = [Vector(p) for p in pts]
    verts, faces = [], []
    ref = Vector((0.13, 0.27, 0.95)).normalized()
    for i, p in enumerate(pts):
        t = (pts[min(i + 1, len(pts) - 1)] - pts[max(i - 1, 0)]).normalized()
        a = t.cross(ref).normalized()
        b = t.cross(a).normalized()
        r = radius(i / (len(pts) - 1)) if callable(radius) else radius
        for s in range(segs):
            th = s / segs * math.tau
            verts.append(p + (a * math.cos(th) + b * math.sin(th)) * r)
    for i in range(len(pts) - 1):
        for s in range(segs):
            t = (s + 1) % segs
            faces.append([i * segs + s, i * segs + t, (i + 1) * segs + t, (i + 1) * segs + s])
    faces.append(list(range(segs - 1, -1, -1)))
    n = (len(pts) - 1) * segs
    faces.append([n + s for s in range(segs)])
    part.add(verts, faces, [col] * len(verts))


def leaves(part, anchors, rnd, size=0.11, lo=(0.035, 0.075, 0.018), hi=(0.13, 0.2, 0.035)):
    """Two-triangle diamond leaves. anchors = [(position, outward_normal), ...]."""
    verts, faces, cols = [], [], []
    for p, n in anchors:
        n = Vector(n).normalized()
        d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(-1.5, 0.2))).normalized()
        s = n.cross(d).normalized()
        if s.length < 0.1:
            continue
        ln = size * rnd.uniform(0.7, 1.4)
        tip = d * ln * 2
        mid = d * ln + n * ln * 0.5 * rnd.uniform(-0.3, 1)
        base = len(verts)
        verts += [p, p + mid + s * ln * 0.7, p + tip, p + mid - s * ln * 0.7]
        faces.append([base, base + 1, base + 2, base + 3])
        t = rnd.random() ** 1.4
        c = mix(lo, hi, t)
        if rnd.random() < 0.06:
            c = (0.3, 0.26, 0.05)
        cols += [mix(c, lo, 0.6), c, c, c]
    part.add(verts, faces, cols)
