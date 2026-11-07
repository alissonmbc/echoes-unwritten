"""Roadside lamp post: timber post on a stone plinth, crossarm, iron scrollwork, hanging lantern.

The Lantern node's origin is its hook, so three.js can sway it. The banner hangs at
BANNER_X, BANNER_Y in index.html (three.js units) under the left arm.
"""
import math
import random

from mathutils import Vector

from common import (Part, box_corners, clamp, export, fbm, lathe, material, mix, stone, tube, use_scene)
import bpy

POST_H = 5.3
ARM_Z = 4.85
HOOK = (1.02, 0.0, 3.86)


def scroll(cx, cz, r0, turns, flip=1, y=0.0, n=34):
    """Flat spiral in the XZ plane, unwinding from its centre."""
    pts = []
    for i in range(n):
        t = i / (n - 1)
        a = t * turns * math.tau
        r = r0 * t
        pts.append((cx + flip * math.cos(a) * r, y, cz + math.sin(a) * r))
    return pts


def build():
    rnd = random.Random(5)
    scn = use_scene("Lumina_Lamp")
    wood = Part("lamp_wood", material("wood", rough=0.8))
    iron = Part("lamp_iron", material("iron", rough=0.5, metal=0.6))
    plinth = Part("lamp_stone", material("stone", rough=0.92))
    gold = Part("lamp_gold", material("gold", rough=0.35, metal=0.9))
    lan_iron = Part("lantern_iron", bpy.data.materials["iron"])
    glow = Part("lantern_glow", material("glow", color=(0.02, 0.01, 0), emissive=(1.0, 0.6, 0.22)))

    def grain(p, w, edge):
        k = fbm(Vector((p.x * 9, p.y * 9, p.z * 0.7)), 3)
        c = mix((0.028, 0.018, 0.012), (0.085, 0.052, 0.03), clamp(k * 1.6 + 0.5))
        return tuple(x * (0.75 if edge >= 2 else 1) for x in c)

    def rock(p, w, edge):
        k = fbm(p * 2.4, 3)
        c = mix((0.2, 0.185, 0.16), (0.42, 0.39, 0.33), clamp(k + 0.55))
        return mix(c, (0.08, 0.11, 0.03), 0.5 if (w > 0.9 and k > 0.0) else 0.0)

    # stepped plinth of four rough blocks plus a cap
    for (a, b, c, d) in ((-0.5, 0.02, -0.5, 0.02), (0.02, 0.5, -0.5, 0.02), (-0.5, 0.02, 0.02, 0.5), (0.02, 0.5, 0.02, 0.5)):
        stone(plinth, box_corners(a, b, c, d, -0.25, 0.32), 0.05, 3, 0.02, rock, rnd)
    stone(plinth, box_corners(-0.33, 0.33, -0.33, 0.33, 0.32, 0.62), 0.05, 3, 0.015, rock, rnd)

    # post: chamfered timber, slightly tapered, iron-banded
    h = 0.135
    post = box_corners(-h, h, -h, h, 0.6, POST_H)
    for i in (0, 1):
        for j in (0, 1):
            post[i][j][1] = post[i][j][1] * 1.0 - Vector((post[i][j][1].x, post[i][j][1].y, 0)) * 0.14
    stone(wood, post, 0.035, 8, 0.006, grain, rnd)
    for z in (0.74, 1.5, 3.3, ARM_Z - 0.3, ARM_Z + 0.2):
        stone(iron, box_corners(-h - 0.02, h + 0.02, -h - 0.02, h + 0.02, z, z + 0.09), 0.012, 1, 0, lambda p, w, e: (0.03, 0.03, 0.032), rnd)

    # crossarm
    stone(wood, box_corners(-1.28, 1.02, -0.085, 0.085, ARM_Z - 0.09, ARM_Z + 0.09), 0.025, 8, 0.006, grain, rnd)
    for x in (-1.28, 1.02):
        s = 1 if x > 0 else -1
        a, b = sorted((x - s * 0.05, x + s * 0.05))
        stone(iron, box_corners(a, b, -0.1, 0.1, ARM_Z - 0.11, ARM_Z + 0.11), 0.012, 1, 0, lambda p, w, e: (0.03, 0.03, 0.032), rnd)

    # timber braces under the arm
    for s in (-1, 1):
        tube(wood, [(s * 0.1, 0, ARM_Z - 0.85), (s * 0.82, 0, ARM_Z - 0.08)], 0.045, 6, (0.09, 0.055, 0.03))

    # lantern arm with scrollwork
    tube(iron, [(0.12, 0, 4.02), (0.55, 0, 4.03), (HOOK[0] - 0.12, 0, 4.0), (HOOK[0], 0, 3.94), (HOOK[0], 0, HOOK[2])], 0.022)
    tube(iron, scroll(0.46, 4.27, 0.2, 1.6), 0.012)
    tube(iron, scroll(0.74, 4.2, 0.13, 1.5, -1), 0.011)
    tube(iron, [(0.12, 0, 3.7), (0.32, 0, 3.78), (0.5, 0, 3.98)], 0.016)

    # finial: a small gilded four-point star on a spike
    tube(iron, [(0, 0, POST_H), (0, 0, POST_H + 0.22)], lambda t: 0.04 * (1 - t) + 0.008)
    star_v, star_f = [], []
    cz = POST_H + 0.42
    for i in range(8):
        a = i * math.pi / 4
        r = 0.2 if i % 2 == 0 else 0.055
        for y in (-0.02, 0.02):
            star_v.append(Vector((math.cos(a) * r, y, cz + math.sin(a) * r)))
    star_f.append([i * 2 for i in range(7, -1, -1)])
    star_f.append([i * 2 + 1 for i in range(8)])
    for i in range(8):
        j = (i + 1) % 8
        star_f.append([i * 2, j * 2, j * 2 + 1, i * 2 + 1])
    gold.add(star_v, star_f, [(0.95, 0.66, 0.2)] * len(star_v))

    # lantern, modelled around its hook at the origin
    dark = (0.03, 0.03, 0.032)
    seg = 6
    R = 0.15
    tube(lan_iron, [(0.03 * math.cos(a), 0, -0.05 + 0.04 * math.sin(a)) for a in [i * math.tau / 10 for i in range(11)]], 0.009)
    lathe(lan_iron, [(0.012, -0.08), (0.03, -0.11), (0.04, -0.13), (0.2, -0.26), (0.205, -0.28), (0.13, -0.29)], 0, 0, seg, lambda p, w, e: dark)
    lathe(lan_iron, [(0.13, -0.68), (0.19, -0.7), (0.19, -0.72), (0.1, -0.76), (0.02, -0.8)], 0, 0, seg, lambda p, w, e: dark)
    for i in range(seg):
        a = i / seg * math.tau
        tube(lan_iron, [(math.cos(a) * R, math.sin(a) * R, -0.28), (math.cos(a) * (R + 0.02), math.sin(a) * (R + 0.02), -0.48), (math.cos(a) * R, math.sin(a) * R, -0.69)], 0.01, 4, dark)
    lathe(glow, [(0.125, -0.3), (0.14, -0.48), (0.125, -0.68)], 0, 0, seg, lambda p, w, e: (1, 0.7, 0.3))

    lantern = lan_iron.to_object(scn)
    lantern.name = "Lantern"
    lantern.location = HOOK
    glass = glow.to_object(scn, parent=lantern)

    objs = [plinth.to_object(scn), wood.to_object(scn), iron.to_object(scn), gold.to_object(scn), lantern, glass]
    info = export(objs, "lamp.glb")
    info["tris"] = sum(sum(len(p.vertices) - 2 for p in o.data.polygons) for o in objs)
    return info, scn
