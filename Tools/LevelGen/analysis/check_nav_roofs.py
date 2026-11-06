"""Offline nav check of a generated plan: can the walkable tops of roofs, lids and terraces join the nav mesh the
players and NPCs use (ground, gallery deck, stairs)? Recast joins two surfaces only where they touch within the
agent's step height, so a roof island matters only if it comes within reach of the deck or the stairs. Also reports
the lowest roof piece over open ground, against the agent's height (an eave lower than that cuts the alley's nav).
Agent: the engine defaults (DefaultEngine.ini sets only RuntimeGeneration=Dynamic): radius 34, height 144, step 35.
Usage: python Tools/LevelGen/analysis/check_nav_roofs.py"""
import glob
import json
import math
import os

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
AGENT_H, STEP, REACH = 144, 35, 50      # cm; REACH: horizontal gap that still counts as touching (cell size ~19)
BOUNDS = {"SM_Cube": ((0, 0, 0), (100, 100, 100)), "SM_Ramp": ((0, 0, 0), (100, 100, 100)),
          "SM_Slate_01": ((-193, -112, 71.2), (189.7, 41.8, 79)),
          "SM_Wall_14": ((0, 0, 0), (20, 200, 106)), "SM_MainBorder_04": ((0, -13, -8), (150, 13, 8)),
          "SM_MetalPlate_A_001": ((-81.2, -2.4, -324.9), (81.2, 2.4, 0)),
          "SM_MetalPlate_A_002": ((-81.2, -2.4, -324.9), (81.2, 2.4, 0)),
          "SM_MetalPlate_A_003": ((-81.2, -2.4, -164.9), (81.2, 2.4, 0)),
          "SM_MetalPlate_A_004": ((-81.2, -2.4, -164.9), (81.2, 2.4, 0)),
          "SM_wooden_beams_01": ((-12.7, -368.8, -11.9), (12.7, 368.8, 11.9)),
          "SM_wooden_beams_02": ((-12.7, -368.8, -11.9), (12.7, 368.8, 11.9)),
          "SM_wooden_beams_03": ((-12.7, -368.8, -11.9), (12.7, 368.8, 11.9)),
          "SM_wooden_beams_05": ((-12.7, -368.8, -17.2), (12.7, 368.8, 17.2)),
          "SM_Balcony_A_003": ((-11.1, -5, -1.1), (317.4, 237.5, 399.4)),
          "SM_Balcony_B_004": ((-11.1, -5, -1.1), (624.4, 237.5, 399.4)),
          "SM_Balcony_B_006": ((-11.1, -5, -1.1), (624.4, 237.5, 399.4))}
WALKABLE = ("BackAlleys/Roofs", "BackAlleys/Lids", "BackAlleys/Terraces", "BackAlleys/Rooms")


def world_box(p):
    (x0, y0, z0), (x1, y1, z1) = BOUNDS[p["asset"].split("/")[-1]]
    P, Y_, R = (math.radians(a) for a in p["rot"])
    sx, sy, sz = p["scale"]
    SP, CP, SY, CY, SR, CR = math.sin(P), math.cos(P), math.sin(Y_), math.cos(Y_), math.sin(R), math.cos(R)
    # FRotationMatrix: the local axes in world space.
    ax = ((CP * CY, CP * SY, SP), (SR * SP * CY - CR * SY, SR * SP * SY + CR * CY, -SR * CP),
          (-(CR * SP * CY + SR * SY), CY * SR - CR * SP * SY, CR * CP))
    pts = []
    for lx in (x0, x1):
        for ly in (y0, y1):
            for lz in (z0, z1):
                v = (lx * sx, ly * sy, lz * sz)
                pts.append(tuple(p["loc"][k] + sum(v[i] * ax[i][k] for i in range(3)) for k in range(3)))
    return [min(q[k] for q in pts) for k in range(3)] + [max(q[k] for q in pts) for k in range(3)]


def ue_rect(r, z0, z1):
    """Layout rect (metres) to a UE box: X = (24 - ly) * 100, Y = (lx - 27) * 100."""
    return [(24 - r["y1"]) * 100, (r["x0"] - 27) * 100, z0, (24 - r["y0"]) * 100, (r["x1"] - 27) * 100, z1]


def gap(a, b):
    return math.hypot(max(0, a[0] - b[3], b[0] - a[3]), max(0, a[1] - b[4], b[1] - a[4]))


layout = json.load(open(os.path.join(ROOT, "Design Document", "Arena_Slums_Layout.json")))
deck = ue_rect(layout["deck"], 400, 400)
stairs = [(s["id"], ue_rect(s, 0, 400)) for s in layout["stairs"]]
for _, r in stairs:                     # gen_level's STAIR_RUN: 7 m north from the top edge, not the layout's 5 m
    r[3] = r[0] + 700
items = []
for f in sorted(glob.glob(os.path.join(ROOT, "Saved", "BackAlleys", "plan3_[0-9]*.json"))):
    items += [p for p in json.load(open(f)) if p["folder"] in WALKABLE and p["asset"].split("/")[-1] in BOUNDS]

touch = []
for p in items:
    b = world_box(p)
    if gap(b, deck) <= REACH and abs(b[5] - 400) <= STEP + 25:
        touch.append((p["label"], "deck", round(b[5]), round(gap(b, deck))))
    for sid, s in stairs:
        # the stair rises from 0 (north foot) to 400 (south top); any top in 0..400+step next to it could join
        if gap(b, s) <= REACH and b[5] <= 400 + STEP + 25:
            touch.append((p["label"], sid, round(b[5]), round(gap(b, s))))
print("%d walkable pieces (roofs, lids, terraces)" % len(items))
print("pieces within %d cm of the deck or stairs and within step reach: %d" % (REACH, len(touch)))
for t in touch:
    print("  ", t)
low = sorted((world_box(p)[2], p["label"]) for p in items if p["folder"] in ("BackAlleys/Roofs", "BackAlleys/Rooms"))
print("lowest roof pieces (bottom z, cm; agent height %d):" % AGENT_H, [(round(z), l) for z, l in low[:5]])
tops = sorted(round(world_box(p)[5]) for p in items)
print("walkable tops range %d..%d cm (ground 0, deck 400)" % (tops[0], tops[-1]))
