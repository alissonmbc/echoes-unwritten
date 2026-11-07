"""Write assets/web/<name>.gltf.json for each assets/<name>.glb.

Artifacts don't serve .glb, so the published page uses glTF's JSON form, with the binary
chunk embedded as a base64 data URI. index.html tries the .glb first and falls back to these.
Usage: python blender/glb_to_json.py
"""
import base64
import glob
import json
import os
import struct

root = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "assets")
out = os.path.join(root, "web")
os.makedirs(out, exist_ok=True)

for path in sorted(glob.glob(os.path.join(root, "*.glb"))):
    with open(path, "rb") as f:
        data = f.read()
    magic, version, _ = struct.unpack_from("<4sII", data, 0)
    assert magic == b"glTF" and version == 2, path
    pos, gltf, binary = 12, None, b""
    while pos < len(data):
        size, kind = struct.unpack_from("<I4s", data, pos)
        chunk = data[pos + 8:pos + 8 + size]
        if kind == b"JSON":
            gltf = json.loads(chunk)
        elif kind == b"BIN\0":
            binary = chunk
        pos += 8 + size
    assert len(gltf["buffers"]) == 1 and "uri" not in gltf["buffers"][0], path
    gltf["buffers"][0]["uri"] = "data:application/octet-stream;base64," + base64.b64encode(binary).decode()
    name = os.path.splitext(os.path.basename(path))[0]
    dest = os.path.join(out, name + ".gltf.json")
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(gltf, f, separators=(",", ":"))
    print(name, os.path.getsize(dest) // 1024, "KB")
