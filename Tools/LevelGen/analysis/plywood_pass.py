"""Offline: the plywood pass for Lvl_01_Slum (user 2026-11-13: "I added a Plywood texture on the content folder. Use that instead of
whatever you are using", "and use less boards on the Alley section"; then "Plywood room walls", "All bare plywood").

From Saved/LinearSlums/wood_pieces.json (analysis/wood_pieces_ue.py, read headless from the saved map), writes
Saved/LinearSlums/plywood_pass.json for the bridge to apply in the open editor:
  - merge:  the covered alley's (S5) plywood room walls, sheet by sheet until now, become one box per solid stretch of wall (between
            the openings). The first sheet of each stretch is kept and resized; the rest go.
  - remove: those other sheets, and the alley walls' studs but the two at each wall's ends (the studs stood at the sheet joints).
  - swap:   every plywood wall piece wearing the bare plywood (MI_BackAlleys_Ply_Natural / _Weathered) gets MI_BackAlleys_Plywood_World,
            the user's T_Plywood texture mapped from world position, so a long box reads as plywood without stretching. The wall
            patches (Patch_*) keep theirs (user, same night: "keep the patches as they are. The one I added is for actually plywood
            walls"); so do the green-painted plywood and the plywood doors.
Every SM_Cube here is unrotated with its pivot at its min corner (checked in the dump), so a box is pos .. pos + scale * 100.

Run: "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/ThirdParty/Python3/Win64/python.exe" -I Tools/LevelGen/analysis/plywood_pass.py"""
import json
import os
import re

ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
SRC = os.path.join(ROOT, "Saved", "LinearSlums", "wood_pieces.json")
OUT = os.path.join(ROOT, "Saved", "LinearSlums", "plywood_pass.json")
MAT_DIR = "/Game/ThirdPerson/BackAlleys/Materials/"
OLD = [MAT_DIR + "MI_BackAlleys_Ply_%s.MI_BackAlleys_Ply_%s" % (k, k) for k in ("Natural", "Weathered")]
NEW = MAT_DIR + "MI_BackAlleys_Plywood_World.MI_BackAlleys_Plywood_World"
CUBE = "/Game/LevelPrototyping/Meshes/SM_Cube.SM_Cube"
TOL = 1.0      # cm: sheets lap 0.4 cm and alternate 0.06 cm off the wall line

pieces = json.load(open(SRC))
by_name = {p["name"]: p for p in pieces}


def box(p):
    lo = p["pos"]
    return [lo[k] for k in range(3)], [lo[k] + p["scale"][k] * 100.0 for k in range(3)]


def merge_rects(rects):
    """Greedy: two rectangles (t0, t1, z0, z1, ids) merge when they share a side's full span and touch or overlap along the other."""
    rects = [list(r) for r in rects]
    changed = True
    while changed:
        changed = False
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                a, b = rects[i], rects[j]
                same_z = abs(a[2] - b[2]) < TOL and abs(a[3] - b[3]) < TOL
                same_t = abs(a[0] - b[0]) < TOL and abs(a[1] - b[1]) < TOL
                touch_t = a[1] >= b[0] - TOL and b[1] >= a[0] - TOL
                touch_z = a[3] >= b[2] - TOL and b[3] >= a[2] - TOL
                if (same_z and touch_t) or (same_t and touch_z):
                    rects[i] = [min(a[0], b[0]), max(a[1], b[1]), min(a[2], b[2]), max(a[3], b[3]), a[4] + b[4]]
                    del rects[j]
                    changed = True
                    break
            if changed:
                break
    return rects


plan = {"new_material": NEW, "old_materials": OLD, "merge": [], "remove": [], "swap": []}
merged_names = set()
alley = [p for p in pieces if p["sec"] == "S5" and p["label"].startswith("PLY_")]
groups = {}
for p in alley:
    groups.setdefault(re.sub(r"_(Ply|Stud)\d+$", "", p["label"]), []).append(p)
for g, ps in sorted(groups.items()):
    sheets = [p for p in ps if re.search(r"_Ply\d+$", p["label"])]
    studs = [p for p in ps if re.search(r"_Stud\d+$", p["label"])]
    assert all(p["mesh"] == CUBE and p["rot"] == [0, 0, 0] for p in ps), g
    lo0, hi0 = box(sheets[0])
    thin = min(range(3), key=lambda k: hi0[k] - lo0[k])
    t_ax = 1 if thin == 0 else 0
    rects = []
    n_lo, n_hi = 1e9, -1e9
    for p in sheets:
        lo, hi = box(p)
        rects.append((lo[t_ax], hi[t_ax], lo[2], hi[2], [p["name"]]))
        n_lo, n_hi = min(n_lo, lo[thin]), max(n_hi, hi[thin])
    for t0, t1, z0, z1, ids in merge_rects(rects):
        ids = sorted(ids, key=lambda n: (by_name[n]["pos"][t_ax], by_name[n]["pos"][2]))
        keep = by_name[ids[0]]
        lo, hi = [0.0] * 3, [0.0] * 3
        lo[t_ax], hi[t_ax], lo[2], hi[2], lo[thin], hi[thin] = t0, t1, z0, z1, n_lo, n_hi
        plan["merge"].append({"name": keep["name"], "label": keep["label"], "group": g, "sheets": len(ids),
                              "pos": [round(v, 3) for v in lo], "scale": [round((hi[k] - lo[k]) / 100.0, 5) for k in range(3)]})
        merged_names.update(ids)
        for n in ids[1:]:
            plan["remove"].append({"name": n, "label": by_name[n]["label"], "why": "merged into " + keep["label"]})
    if len(studs) > 2:
        studs.sort(key=lambda p: p["pos"][t_ax])
        for p in studs[1:-1]:
            plan["remove"].append({"name": p["name"], "label": p["label"], "why": "stud at a sheet joint"})
removed = {r["name"] for r in plan["remove"]}
for p in pieces:
    if p["name"] in removed or p["label"].startswith("Patch_"):
        continue
    if any(m in OLD for m in (p.get("override") or [])):
        plan["swap"].append({"name": p["name"], "label": p["label"], "sec": p["sec"]})
json.dump(plan, open(OUT, "w"), indent=0)
by_sec = {}
for s in plan["swap"]:
    by_sec[s["sec"]] = by_sec.get(s["sec"], 0) + 1
print("alley walls: %d, sheets %d -> %d boxes; studs %d -> %d" % (
    len(groups), sum(1 for p in alley if "_Ply" in p["label"].rsplit("_", 1)[-1] or re.search(r"_Ply\d+$", p["label"])),
    len(plan["merge"]), sum(1 for p in alley if re.search(r"_Stud\d+$", p["label"])),
    sum(1 for p in alley if re.search(r"_Stud\d+$", p["label"])) - sum(1 for r in plan["remove"] if r["why"].startswith("stud"))))
print("remove %d, swap %d by section %s" % (len(plan["remove"]), len(plan["swap"]), sorted(by_sec.items())))
print("bytes", os.path.getsize(OUT))
