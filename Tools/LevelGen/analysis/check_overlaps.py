"""Offline check of a generated plan: boxes of wall pieces, bands and trims that overlap by more than a tolerance,
which shows up as z-fighting where their faces share a plane (user 2026-11-03: overlaps at corners and in the trims).
Usage: python Tools/LevelGen/analysis/check_overlaps.py"""
import glob
import json
import math
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
LOCAL = {"SM_MainBorder_04": (0, -13, -8, 150, 13, 8), "SM_Wall_14": (0, 0, 0, 20, 200, 106),
         "SM_Wall_Tile_Blue": (0, -20, 0, 225, 0, 300), "SM_Wall_Tile_01": (0, -20, 0, 225, 0, 300),
         "SM_Wall_Tile_03": (0, -20, 0, 112.5, 0, 300), "SM_WallDoor_01": (0, -20, 0, 225, 0, 300),
         "SM_Wall_Windows_01": (0, -20, 0, 225, 0, 300)}
TOL = 1.0   # cm: touching or 1 cm interpenetration is fine


def box(p):
    b = LOCAL[p["asset"].split("/")[-1]]
    x, y, z = p["loc"]
    yaw = math.radians(p["rot"][1])
    sx, sy, sz = p["scale"]
    c, s = round(math.cos(yaw)), round(math.sin(yaw))
    pts = [(x + (lx * sx) * c - (ly * sy) * s, y + (lx * sx) * s + (ly * sy) * c) for lx in (b[0], b[3]) for ly in (b[1], b[4])]
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    return min(xs), min(ys), z + b[2] * sz, max(xs), max(ys), z + b[5] * sz


items, columns = [], []
for f in sorted(glob.glob(os.path.join(ROOT, "Saved", "BackAlleys", "plan3_[0-9]*.json"))):
    plan = json.load(open(f))
    items += [p for p in plan if p["asset"].split("/")[-1] in LOCAL]
    # Corner columns (SM_Cube, pivot at its min corner, unrotated): what lies inside one can't be seen.
    columns += [(p["loc"][0], p["loc"][1], p["loc"][2], p["loc"][0] + p["scale"][0] * 100,
                 p["loc"][1] + p["scale"][1] * 100, p["loc"][2] + p["scale"][2] * 100)
                for p in plan if p["label"].startswith("Column_")]


def in_column(axis, plane, lo, hi, z0, z1):
    """A rectangle in an axis-aligned plane (axis 0: X = plane, spanning Y lo..hi) inside a column, give or take 1 cm."""
    for c in columns:
        a0, a1 = (c[0], c[3]) if axis == 0 else (c[1], c[4])
        b0, b1 = (c[1], c[4]) if axis == 0 else (c[0], c[3])
        if a0 - 1 <= plane <= a1 + 1 and b0 - 1 <= lo and hi <= b1 + 1 and c[2] - 1 <= z0 and z1 <= c[5] + 1:
            return True
    return False
boxes = [(p["label"], p["asset"].split("/")[-1], box(p)) for p in items]
yaws = [round(p["rot"][1]) % 360 if p["asset"].split("/")[-1] != "SM_Wall_14" else (round(p["rot"][1]) + 90) % 360
        for p in items]
grid = {}
for i, (_, _, b) in enumerate(boxes):
    for gx in range(int(b[0] // 300), int(b[3] // 300) + 1):
        for gy in range(int(b[1] // 300), int(b[4] // 300) + 1):
            grid.setdefault((gx, gy), []).append(i)
hits, seen = [], set()
for cell in grid.values():
    for a in cell:
        for b in cell:
            if b <= a or (a, b) in seen:
                continue
            seen.add((a, b))
            A, B = boxes[a][2], boxes[b][2]
            ov = [min(A[k + 3], B[k + 3]) - max(A[k], B[k]) for k in range(3)]
            if all(o > TOL for o in ov):
                kinds = tuple(sorted((boxes[a][1], boxes[b][1])))
                trims = kinds == ("SM_MainBorder_04", "SM_MainBorder_04")
                same_facing = yaws[a] == yaws[b] and "SM_MainBorder_04" not in kinds
                # Pieces facing different ways overlap only where one is buried in the other's body (inside
                # corners, by design). What z-fights: two trims crossing, or two same-facing pieces sharing a face.
                if not (trims or same_facing):
                    continue
                # A tile and its own band/trim share the seam by design (trim straddles it); skip same-label pairs.
                if boxes[a][0].split("_Trim")[0].split("_Band")[0] == boxes[b][0].split("_Trim")[0].split("_Band")[0]:
                    continue
                hits.append((boxes[a][0], boxes[b][0], kinds, [round(o) for o in ov]))
print("%d pieces checked, %d overlapping pairs" % (len(boxes), len(hits)))
from collections import Counter
print(Counter(h[2] for h in hits).most_common())
for h in hits[:60]:
    print(h)

# Coplanar faces between differently-facing walls: a piece's end cap lying in another piece's outer face (the corner
# z-fight). Faces are axis-aligned rectangles: (axis, plane, (lo, hi) along the other horizontal axis, (z0, z1)).
def faces(p, b):
    yaw = round(p["rot"][1]) % 360
    if p["asset"].split("/")[-1] == "SM_Wall_14":
        yaw = (yaw + 90) % 360
    x0, y0, z0, x1, y1, z1 = b
    along_x = yaw in (0, 180)                      # the run is along X: caps are X planes, the face is a Y plane
    normal = {0: (1, +1), 180: (1, -1), 90: (0, -1), 270: (0, +1)}[yaw]   # (axis, sign) of the outer face
    face = (1, y1 if normal[1] > 0 else y0, (x0, x1), (z0, z1)) if along_x else \
        (0, x1 if normal[1] > 0 else x0, (y0, y1), (z0, z1))
    caps = [(0, x0, (y0, y1), (z0, z1)), (0, x1, (y0, y1), (z0, z1))] if along_x else \
        [(1, y0, (x0, x1), (z0, z1)), (1, y1, (x0, x1), (z0, z1))]
    return face, caps


walls = [(boxes[i][0], faces(items[i], boxes[i][2])) for i in range(len(items))
         if boxes[i][1] != "SM_MainBorder_04"]
by_plane = {}
for label, (face, caps) in walls:
    by_plane.setdefault((face[0], round(face[1])), []).append((label, face))
cop = []
# A cap that meets another same-facing piece's cap in the same plane is a junction (two runs of one face meeting flush,
# gen_level.py 2026-11-03): sealed inside the wall, whatever else lies in that plane there.
caps_at = {}
for i, (label, (face, caps)) in enumerate(walls):
    for cap in caps:
        caps_at.setdefault((cap[0], round(cap[1])), []).append((label, face[1] - cap[1] > 0, cap))


def sealed(label, cap):
    for other, _, c in caps_at.get((cap[0], round(cap[1])), []):
        if other != label and min(c[2][1], cap[2][1]) - max(c[2][0], cap[2][0]) > 0.5 and \
                min(c[3][1], cap[3][1]) - max(c[3][0], cap[3][0]) > 0.5:
            return True
    return False


for label, (face, caps) in walls:
    for cap in caps:
        if sealed(label, cap):
            continue
        for other, f in by_plane.get((cap[0], round(cap[1])), []):
            if other == label or abs(f[1] - cap[1]) > 0.5:
                continue
            ov = min(f[2][1], cap[2][1]) - max(f[2][0], cap[2][0])
            oz = min(f[3][1], cap[3][1]) - max(f[3][0], cap[3][0])
            if ov > 0.5 and oz > 0.5 and not in_column(cap[0], cap[1], max(f[2][0], cap[2][0]),
                                                       min(f[2][1], cap[2][1]), max(f[3][0], cap[3][0]),
                                                       min(f[3][1], cap[3][1])):
                cop.append((label, other, round(ov, 1)))
print("end caps lying in another wall's face: %d" % len(cop))
for c in cop[:60]:
    print(c)

# A closed stall's wall has to stand behind the stall's frame: SM_Shop_A_001's frame and SM_HouseWall_A_001 share the planes local Y 0 and -20. User 2026-11-06: "Shop A 001, overlapping surfaces with wall".
whole = []
for f in sorted(glob.glob(os.path.join(ROOT, "Saved", "BackAlleys", "plan3_[0-9]*.json"))):
    whole += json.load(open(f))
by_label = {p["label"]: p for p in whole}
stall_cop = []
for p in whole:
    if p["label"].endswith("_Back") and p["label"][:-5] in by_label:
        shop = by_label[p["label"][:-5]]
        yaw = math.radians(shop["rot"][1])
        back = (p["loc"][0] - shop["loc"][0]) * -math.sin(yaw) + (p["loc"][1] - shop["loc"][1]) * math.cos(yaw)
        if back > -0.5:
            stall_cop.append((p["label"], round(back, 2)))
print("stall walls sharing their frame's plane: %d %s" % (len(stall_cop), stall_cop))

# Two stalls side by side must not lap: their frames share a plane.
shops = sorted((p for p in whole if p["asset"].endswith("/SM_Shop_A_001")), key=lambda p: (p["rot"][1], p["loc"][0], p["loc"][1]))
shop_cop = []
for i, a in enumerate(shops):
    yaw = math.radians(a["rot"][1])
    for b in shops[i + 1:]:
        along = (b["loc"][0] - a["loc"][0]) * math.cos(yaw) + (b["loc"][1] - a["loc"][1]) * math.sin(yaw)
        off = (b["loc"][0] - a["loc"][0]) * -math.sin(yaw) + (b["loc"][1] - a["loc"][1]) * math.cos(yaw)
        if a["rot"][1] == b["rot"][1] and abs(off) < 1.0 and abs(along) < 299.0:
            shop_cop.append((a["label"], b["label"], round(300.0 - abs(along), 1)))
print("stalls lapping on one plane: %d %s" % (len(shop_cop), shop_cop))
