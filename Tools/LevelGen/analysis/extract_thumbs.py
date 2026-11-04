"""Offline: copies the editor thumbnail (a JPEG the editor stores inside each .uasset) of every mesh in
Saved/LevelGen/visual/meshes.json to visual/thumbs/<group>/<name>.jpg. These show the mesh textured as Unreal renders
it, next to render_meshes_blender.py's views. Meshes without a stored thumbnail are listed.
Usage: python Tools/LevelGen/analysis/extract_thumbs.py"""
import json
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
VIS = os.path.join(ROOT, "Saved", "LevelGen", "visual")
missing = []
for e in json.load(open(os.path.join(VIS, "meshes.json"))):
    src = os.path.join(ROOT, "Content", e["path"][len("/Game/"):] + ".uasset")
    data = open(src, "rb").read()
    a = data.find(b"\xff\xd8\xff")
    b = data.find(b"\xff\xd9", a) if a >= 0 else -1
    if a < 0 or b < 0:
        missing.append(e["name"])
        continue
    os.makedirs(os.path.join(VIS, "thumbs", e["group"]), exist_ok=True)
    open(os.path.join(VIS, "thumbs", e["group"], e["name"] + ".jpg"), "wb").write(data[a:b + 2])
print("no thumbnail: %d %s" % (len(missing), missing[:20]))
