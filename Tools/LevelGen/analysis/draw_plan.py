"""Offline: a top-down picture of a level's plan, no libraries (zlib PNG). For judging a build before placing it.

    python Tools/LevelGen/analysis/draw_plan.py [level] [--z lo hi] [--out file.png] [--px 8]

Draws every box-like piece seen from above (cubes by their boxes, meshes by their measured bounds when known), coloured by
folder, within the height band --z (cm, default everything). Lights are yellow dots. Writes Saved/LevelGen/plan_<level>.png."""
import json
import math
import os
import struct
import sys
import zlib
import glob

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_source  # noqa: E402

args = sys.argv[1:]
z_lo, z_hi, out, px = -1e9, 1e9, None, 8.0
if "--z" in args:
    i = args.index("--z")
    z_lo, z_hi = float(args[i + 1]), float(args[i + 2])
    del args[i:i + 3]
if "--out" in args:
    i = args.index("--out")
    out = args[i + 1]
    del args[i:i + 2]
if "--px" in args:
    i = args.index("--px")
    px = float(args[i + 1])
    del args[i:i + 2]
crop = None
if "--box" in args:                                # layout metres x0 y0 x1 y1 (needs the level's ORIGIN)
    i = args.index("--box")
    crop = [float(v) for v in args[i + 1:i + 5]]
    del args[i:i + 5]
name = plan_source.level_name(args)
items = []
for f in sorted(glob.glob(plan_source.plan_glob(name))):
    items += plan_source.normalise(json.load(open(f, encoding="utf-8")), name)
mb_path = os.path.join(plan_source.ROOT, "Saved", "LevelGen", "visual", "meshes.json")
bounds = {}
if os.path.exists(mb_path):
    for v in json.load(open(mb_path, encoding="utf-8")):
        if v.get("bounds_min") and v.get("bounds_max"):
            bounds[v["path"]] = (v["bounds_min"], v["bounds_max"])
FIX = {"/Game/LevelPrototyping/Meshes/SM_Cube": ((0, 0, 0), (100, 100, 100)), "/Engine/BasicShapes/Plane": ((-50, -50, 0), (50, 50, 0))}
COL = {"Blocks": (150, 150, 150), "Lids": (120, 120, 120), "Roofs": (160, 110, 90), "Terraces": (140, 140, 110), "Floors": (175, 175, 175),
       "GroundBody": (205, 200, 190), "Ground": (215, 210, 200), "Interiors": (40, 60, 70), "Lights": (250, 210, 40), "Gates": (40, 140, 60),
       "Decals": (90, 90, 90), "IntFloor": (232, 226, 214), "Rails": (40, 110, 220), "Stairs": (230, 130, 40), "Walls": (180, 30, 30)}
ORDER = ["GroundBody", "Ground", "Floors", "IntFloor", "Lids", "Terraces", "Roofs", "Blocks", "Decals", "Gates", "Stairs", "Interiors", "Walls", "Rails", "Lights"]


def corners(p):
    b = FIX.get(p["asset"]) or bounds.get(p["asset"])
    if b is None:
        return None
    (x0, y0, z0), (x1, y1, z1) = b
    sx, sy, sz = p["scale"]
    pi, ya, ro = (math.radians(a) for a in p["rot"])
    cp, sp, cy, sy_, cr, sr = math.cos(pi), math.sin(pi), math.cos(ya), math.sin(ya), math.cos(ro), math.sin(ro)
    M = [[cp * cy, cy * sp * sr - cr * sy_, -(cr * cy * sp + sr * sy_)],
         [cp * sy_, sy_ * sp * sr + cr * cy, cy * sr - cr * sp * sy_],
         [sp, -cp * sr, cp * cr]]
    pts = []
    for lx in (x0, x1):
        for ly in (y0, y1):
            for lz in (z0, z1):
                v = (lx * sx, ly * sy, lz * sz)
                pts.append(tuple(p["loc"][i] + M[i][0] * v[0] + M[i][1] * v[1] + M[i][2] * v[2] for i in range(3)))
    return pts


boxes = []
for p in items:
    kind = p["folder"].split("/")[-1]
    if p.get("light"):
        boxes.append(("Lights", p["loc"][0] - 25, p["loc"][1] - 25, p["loc"][0] + 25, p["loc"][1] + 25, p["loc"][2], p["loc"][2]))
        continue
    c = corners(p)
    if not c:
        continue
    zs = [q[2] for q in c]
    if max(zs) < z_lo or min(zs) > z_hi:
        continue
    if kind == "Interiors" and max(zs) - min(zs) < 40.0:
        kind = "IntFloor"                          # slabs and floors pale, so the walls on them show
    if "_Rail" in p["label"] or "_Well" in p["label"]:
        kind = "Rails"
    if p["label"].startswith(("CompoundWall_", "YardWall_")):
        kind = "Walls"
    if "_Stair" in p["label"] or p["label"].startswith("Step_"):
        kind = "Stairs"
    boxes.append((kind, min(q[0] for q in c), min(q[1] for q in c), max(q[0] for q in c), max(q[1] for q in c), min(zs), max(zs)))
X0, Y0 = min(b[1] for b in boxes), min(b[2] for b in boxes)
X1, Y1 = max(b[3] for b in boxes), max(b[4] for b in boxes)
if crop:
    ox, oy = plan_source.load_level(name).ORIGIN
    X0, X1 = (oy - crop[3]) * 100.0, (oy - crop[1]) * 100.0
    Y0, Y1 = (crop[0] - ox) * 100.0, (crop[2] - ox) * 100.0
k = px / 100.0
W_, H_ = int((Y1 - Y0) * k) + 2, int((X1 - X0) * k) + 2          # image x = UE Y (east), image y = -UE X (south)
img = bytearray(b"\xff\xff\xff" * W_ * H_)


def fill(x0, y0, x1, y1, col):
    i0, i1 = int((y0 - Y0) * k), int(math.ceil((y1 - Y0) * k))
    j0, j1 = int((X1 - x1) * k), int(math.ceil((X1 - x0) * k))
    for j in range(max(0, j0), min(H_, max(j1, j0 + 1))):
        row = j * W_ * 3
        for i in range(max(0, i0), min(W_, max(i1, i0 + 1))):
            img[row + i * 3:row + i * 3 + 3] = bytes(col)


for kind in ORDER + sorted({b[0] for b in boxes} - set(ORDER)):
    for b in boxes:
        if b[0] == kind:
            fill(b[1], b[2], b[3], b[4], COL.get(kind, (100, 100, 200)))
raw = b"".join(b"\x00" + bytes(img[j * W_ * 3:(j + 1) * W_ * 3]) for j in range(H_))


def chunk(t, d):
    return struct.pack(">I", len(d)) + t + d + struct.pack(">I", zlib.crc32(t + d) & 0xffffffff)


out = out or os.path.join(plan_source.ROOT, "Saved", "LevelGen", "plan_%s.png" % name)
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, "wb").write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", W_, H_, 8, 2, 0, 0, 0)) +
                      chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))
print("wrote", out, W_, "x", H_, "px;", len(boxes), "pieces; north up, east right")
