"""List the nodes, materials and attributes in each GLB. Usage: python blender/check_glb.py"""
import glob
import json
import os
import struct

root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
for path in sorted(glob.glob(os.path.join(root, "*.glb"))):
    with open(path, "rb") as f:
        f.read(12)
        n, _ = struct.unpack("<II", f.read(8))
        g = json.loads(f.read(n))
    meshes = g.get("meshes", [])
    attrs = sorted({a for m in meshes for p in m["primitives"] for a in p["attributes"]})
    print(os.path.basename(path), os.path.getsize(path) // 1024, "KB")
    print("  nodes:", [x.get("name") for x in g.get("nodes", [])])
    print("  materials:", [x.get("name") for x in g.get("materials", [])])
    print("  attributes:", attrs)
