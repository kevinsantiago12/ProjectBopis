"""Groups a dumped reference map's wall pieces into buildings and reports how each is put together: storeys,
materials per wall/storey, door and window mix, trims, slabs, corner pieces, wall decals and what's attached.
Input: Saved/LevelGen/dump_<map>.json (dump_map_ue.py). Usage: python analyse_buildings.py [Favela] [--detail]"""
import collections
import json
import math
import os
import re
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
MAP = next((a for a in sys.argv[1:] if not a.startswith("-")), "Favela")
D = json.load(open(os.path.join(ROOT, "Saved", "LevelGen", "dump_%s.json" % MAP)))
WALL = re.compile(r"SM_(Wall_Tile_|Wall_Windows_|WallDoor_|Wall_0\d|Wall_1[0-3])")


def short(p):
    return p.split(".")[-1].split("/")[-1] if p else None


pieces = []   # every mesh instance: name, xf, bounds, mats
decals = []
for a in D["actors"]:
    for c in a["comps"]:
        if "mesh" in c:
            for x in c.get("instances") or [c["xf"]]:
                pieces.append({"n": short(c["mesh"]), "xf": x, "b": c["bounds"], "mats": [short(m) for m in c["mats"]]})
        elif "decal" in c:
            decals.append({"m": short(c["decal"]), "xf": c["xf"], "size": c["size"]})


def seg(p):
    """A wall piece's base segment in world XY (its local X run), and its outward normal (local -Y)."""
    x, y, z, pitch, yaw, roll, sx, sy, sz = p["xf"]
    b = p["b"]
    c, s = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    def w(lx, ly):
        return (x + (lx * c - ly * s) * sx, y + (lx * s + ly * c) * sx if False else y + (lx * s * sx + ly * c * sy))
    a0 = (x + c * b[0] * sx, y + s * b[0] * sx)
    a1 = (x + c * b[3] * sx, y + s * b[3] * sx)
    return a0, a1, (s, -c), z, z + (b[5] - b[2]) * sz


walls = [p for p in pieces if WALL.match(p["n"])]
for p in walls:
    p["seg"] = seg(p)

# Union-find: wall pieces whose segments come within 40 cm of each other (any height) are one building.
parent = list(range(len(walls)))


def find(i):
    while parent[i] != i:
        parent[i] = parent[parent[i]]
        i = parent[i]
    return i


def d2(p, a, b):
    ax, ay = a
    bx, by = b
    vx, vy = bx - ax, by - ay
    t = max(0, min(1, ((p[0] - ax) * vx + (p[1] - ay) * vy) / (vx * vx + vy * vy or 1)))
    return math.hypot(p[0] - ax - t * vx, p[1] - ay - t * vy)


cell = collections.defaultdict(list)
for i, p in enumerate(walls):
    (a0, a1) = p["seg"][:2]
    for q in (a0, a1, ((a0[0] + a1[0]) / 2, (a0[1] + a1[1]) / 2)):
        cell[(int(q[0] // 300), int(q[1] // 300))].append(i)
for i, p in enumerate(walls):
    a0, a1 = p["seg"][:2]
    cx, cy = int(a0[0] // 300), int(a0[1] // 300)
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            for j in cell[(cx + dx, cy + dy)]:
                if j <= i or find(i) == find(j):
                    continue
                q0, q1 = walls[j]["seg"][:2]
                if min(d2(a0, q0, q1), d2(a1, q0, q1), d2(q0, a0, a1), d2(q1, a0, a1)) < 40:
                    parent[find(i)] = find(j)
groups = collections.defaultdict(list)
for i, p in enumerate(walls):
    groups[find(i)].append(p)
blds = sorted((g for g in groups.values() if len(g) >= 6), key=len, reverse=True)

# What sits near each building: non-wall pieces and decals within 60 cm of a wall segment.
others = [p for p in pieces if not WALL.match(p["n"])]
ocell = collections.defaultdict(list)
for p in others:
    ocell[(int(p["xf"][0] // 300), int(p["xf"][1] // 300))].append(p)
dcell = collections.defaultdict(list)
for dcl in decals:
    dcell[(int(dcl["xf"][0] // 300), int(dcl["xf"][1] // 300))].append(dcl)


def near(b, grid, reach):
    out, seen = [], set()
    for p in b:
        a0, a1, n, z0, z1 = p["seg"]
        for gx in range(int(min(a0[0], a1[0]) // 300) - 1, int(max(a0[0], a1[0]) // 300) + 2):
            for gy in range(int(min(a0[1], a1[1]) // 300) - 1, int(max(a0[1], a1[1]) // 300) + 2):
                for o in grid[(gx, gy)]:
                    if id(o) in seen:
                        continue
                    if d2(o["xf"][:2], a0, a1) < reach and z0 - 50 <= o["xf"][2] <= z1 + 50:
                        seen.add(id(o))
                        out.append(o)
    return out


summary = collections.Counter()
mat_per_bld = collections.Counter()
storey_mats = collections.Counter()
mix = collections.Counter()
for k, b in enumerate(blds):
    zs = sorted(set(round(p["xf"][2] / 10) * 10 for p in b))
    xs = [q[0] for p in b for q in p["seg"][:2]]
    ys = [q[1] for p in b for q in p["seg"][:2]]
    mats = collections.Counter(p["mats"][0] for p in b)
    by_z = collections.defaultdict(collections.Counter)
    for p in b:
        by_z[round(p["xf"][2] / 10) * 10][p["mats"][0]] += 1
    kinds = collections.Counter(re.sub(r"_\d+$|_Blue$", "", p["n"]) for p in b)
    att = collections.Counter(o["n"] for o in near(b, ocell, 80))
    dec = near(b, dcell, 60)
    wall_dec = [x for x in dec if abs(x["xf"][3]) < 30]
    mat_per_bld[len(mats)] += 1
    for z, mc in by_z.items():
        storey_mats[len(mc)] += 1
    for kname, v in kinds.items():
        mix[kname] += v
    if "--detail" in sys.argv or k < 12:
        print("=" * 100)
        print("Building %d: %d wall pieces, footprint %.1f x %.1f m, base z %d, storey z: %s" % (
            k, len(b), (max(xs) - min(xs)) / 100, (max(ys) - min(ys)) / 100, zs[0], [z - zs[0] for z in zs]))
        print("  pieces:", dict(kinds.most_common()))
        print("  materials:", dict(mats.most_common()))
        print("  per storey:", {z - zs[0]: dict(c) for z, c in sorted(by_z.items())})
        print("  attached:", dict(att.most_common(25)))
        print("  wall decals: %d (%s); ground/other decals %d" % (
            len(wall_dec), dict(collections.Counter(x["m"] for x in wall_dec).most_common(10)), len(dec) - len(wall_dec)))
        if wall_dec:
            print("    sizes:", collections.Counter(tuple(x["size"]) for x in wall_dec).most_common(5),
                  "height above base:", sorted(round(x["xf"][2] - zs[0]) for x in wall_dec)[:20])
print("=" * 100)
print("%d buildings (>= 6 wall pieces), %d wall pieces in them, %d wall pieces total" % (
    len(blds), sum(map(len, blds)), len(walls)))
print("materials per building:", sorted(mat_per_bld.items()))
print("materials per storey row:", sorted(storey_mats.items()))
print("piece mix:", dict(mix.most_common()))
