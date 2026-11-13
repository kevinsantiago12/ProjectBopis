"""Offline: the pieces for H4's back stair in Lvl_01_Slum (user 2026-11-11: "the drop will now be stairs down. Work on it now"). The
revised layout (2026-11-08) replaces H4's floor hole with a half-landing stair: a flight up 2 m west, a landing, a flight up 2 m east
(x 79.8-82.55, y 66.9-70.5), fitted here to the map's 3.5 m storey (1.75 m a flight). Built the way story_interiors builds the user's
stair (FITTED, TRAP_Stair3): the kit's flights at 0.538 x 1.015, each one step (of six) down the last, anchored at the top; balusters
and two pipe lengths on each open side; AsiaSlum's bar rail round the upper-floor opening, but where the stair arrives.

UE cm. Writes Saved/LinearSlums/h4_stair.json: pieces to add (each with a template actor to copy its materials and collision from),
pieces to remove, and Slab1_4's new extent. Placed by the bridge in the open editor; nothing here touches the map."""
import json
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, ".."))
from kit.core import axes_rot, v_add, v_cross, v_dot  # noqa: E402

OUT = os.path.join(HERE, "..", "..", "..", "Saved", "LinearSlums", "h4_stair.json")
AS = "/Game/AsiaSlum/FBX/"
CUBE = "/Game/LevelPrototyping/Meshes/SM_Cube"
PLANE = "/Engine/BasicShapes/Plane"
FLIGHT_RUN, FLIGHT_RISE, FLIGHT_STEP = 300.0 * 0.538, 114.9 * 1.015, 5.0 / 6.0
RAIL_SX, RAIL_SZ, RAIL_X0, RAIL_Z0 = 300 / 302.0, 105 / 177.9, 2.5, 3.9

Z0, Z1 = 18.0, 368.0                   # H4's ground floor and upper floor (finish tops)
ZL = (Z0 + Z1) / 2.0                   # the half landing, 193
WALL_W, PARTY_Y = -1029.0, -192.0      # the back wall's inner face (X), the H3/H4 party wall's face (Y)
EDGE_X = -675.0                        # the opening's room-side edge: the face of ROW_Slab1_3
LAND_Y, TOP_Y = 8.0, 250.0             # the landing's front edge; the stair's top end (the face of ROW_Slab1_5)
LOW = (-848.0, -675.0)                 # lower flight, room side (X), its foot by the back door
UP = (-1020.0, -852.0)                 # upper flight, along the back wall, clear of the window frame (to -1021)
add, n_ = [], {}


def piece(label, asset, loc, rot, scale, tmpl):
    add.append({"label": label, "asset": asset, "loc": [round(c, 2) for c in loc], "rot": [round(c, 3) for c in rot],
                "scale": [round(c, 4) for c in scale], "template": tmpl})


def flight(name, lane, top_y, top_z, down_y, rise):
    """Kit flights from the top end (top_y, top_z) down along down_y (+1 or -1, UE Y) until the steps reach top_z - rise."""
    D2 = (0.0, down_y)
    Ly = (-D2[1], D2[0])                                            # the flights' local +Y in the world
    width = lane[1] - lane[0]
    sy = width / 306.7
    ea, eb = (lane[0], top_y), (lane[1], top_y)
    piv = ea if ((eb[0] - ea[0]) * Ly[0] + (eb[1] - ea[1]) * Ly[1]) < 0 else eb     # local -Y must cross the width
    yaw = math.degrees(math.atan2(D2[1], D2[0]))
    nfl = max(1, math.ceil((rise - FLIGHT_RISE) / (FLIGHT_RISE * FLIGHT_STEP) - 1e-6) + 1)
    for k in range(nfl):
        d = FLIGHT_RUN * FLIGHT_STEP * k
        piece("%s_%d" % (name, nfl - 1 - k), AS + "SM_Stair_A_002",
              (piv[0] + D2[0] * d - Ly[0] * 3.5 * sy, piv[1] + D2[1] * d - Ly[1] * 3.5 * sy, top_z - FLIGHT_RISE * FLIGHT_STEP * k),
              (0.0, yaw, 0.0), (FLIGHT_RUN / 300.0, sy, FLIGHT_RISE / 114.9), "ROW_Stair1_0")
    return yaw, rise * FLIGHT_RUN / FLIGHT_RISE                     # the run the steps cover


def balusters(name, x_line, bottom_y, top_y, zb, rise, yaw):
    """story_interiors' balusters and two pipe lengths, on a line x_line, up the run from bottom_y to top_y."""
    run = abs(top_y - bottom_y)
    up = 1.0 if top_y > bottom_y else -1.0
    D3 = (0.0, -up, 0.0)                                            # downhill
    alpha, theta = math.atan2(206.9, 403.2), math.atan2(rise, run)
    dlt = theta - alpha
    Xw = (D3[0] * math.cos(dlt), D3[1] * math.cos(dlt), -math.sin(dlt))
    Zw = (D3[0] * math.sin(dlt), D3[1] * math.sin(dlt), math.cos(dlt))
    Yw = v_cross(Zw, Xw)

    def pt(s):
        return (x_line, bottom_y + up * s * 100.0)

    def surf(s):
        return zb + rise * s * 100.0 / run
    s_lo, s_hi = 0.25, run / 100.0 - 0.15
    n_posts = max(2, math.ceil((s_hi - s_lo) / 0.68) + 1)
    for i in range(n_posts):
        s = s_lo + (s_hi - s_lo) * i / (n_posts - 1)
        X, Y = pt(s)
        bot, top = surf(s) - 9.0, surf(s) + 92.0
        piece("%s_Post%d" % (name, i), AS + "SM_StairRail_C_002", (X, Y, bot), (0.0, yaw, 0.0), (1.0, 1.0, (top - bot) / 109.9),
              "ROW_Stair1_PostW0")
    for j in range(2):
        sa = s_lo + (s_hi - s_lo) * j / 2
        sb = s_lo + (s_hi - s_lo) * (j + 1) / 2
        Pa = pt(sa) + (surf(sa) + 90.0,)
        Pb = pt(sb) + (surf(sb) + 90.0,)
        k_ = math.dist(Pa, Pb) / 453.2
        X, Y, Z = Xw, Yw, Zw
        if v_dot(v_cross(X, Y), Z) < 0:
            X = (-X[0], -X[1], -X[2])
        off = (0.0, 0.0, 0.0)
        for ax, a in ((X, 43.6), (Y, 0.0), (Z, 17.0)):
            off = v_add(off, ax, a * k_)
        p = v_add(Pa, off, -1.0)
        piece("%s_Rail%d" % (name, j), AS + "SM_StairRail_A_001", p, axes_rot(X, Y, Z), (k_, k_, k_), "ROW_Stair1_RailW0")


def bar_rail(name, along, fixed, t0, t1, z):
    """AsiaSlum's bar rail (story_interiors _rail), modules of at most 3 m, on the line fixed, from t0 to t1 (cm) along X or Y."""
    L_ = abs(t1 - t0)
    m = max(1, math.ceil(L_ / 300.0 - 1e-6))
    sgn = 1.0 if t1 > t0 else -1.0
    for i in range(m):
        ta = t0 + (t1 - t0) * i / m
        sx = (L_ / m) / 302.0
        if along == "Y":        # local X along +Y: yaw 90
            loc, yaw = (fixed, ta + sgn * RAIL_X0 * sx, z + RAIL_Z0 * RAIL_SZ), 90.0 if sgn > 0 else -90.0
        else:                   # along X
            loc, yaw = (ta + sgn * RAIL_X0 * sx, fixed, z + RAIL_Z0 * RAIL_SZ), 0.0 if sgn > 0 else 180.0
        piece("%s_%d" % (name, i), AS + "SM_Rail_A_001", loc, (0.0, yaw, 0.0), (sx, 1.0, RAIL_SZ), "ROW_Well1_Y702_0")


# --- the landing: a solid block against the back and party walls, a finish plane on it ---------------------------------------------
lx0, ly0 = WALL_W + 0.2, PARTY_Y + 0.2
piece("ROW_Landing2", CUBE, (lx0, ly0, Z0 - 1.0), (0.0, 0.0, 0.0), ((EDGE_X - lx0) / 100.0, (LAND_Y - ly0) / 100.0, (ZL - 1.0 - (Z0 - 1.0)) / 100.0),
      "ROW_Slab1_4")
piece("ROW_Landing2_Floor", PLANE, ((lx0 + EDGE_X) / 2.0, (ly0 + LAND_Y) / 2.0, ZL), (0.0, 0.0, 0.0),
      ((EDGE_X - lx0) / 100.0, (LAND_Y - ly0) / 100.0, 1.0), "ROW_H4_UB_Floor1")

# --- the flights ---------------------------------------------------------------------------------------------------------------------
yaw_lo, run_lo = flight("ROW_Stair2", LOW, LAND_Y, ZL, 1.0, ZL - Z0)        # landing down to the back door
yaw_up, run_up = flight("ROW_Stair3", UP, TOP_Y, Z1, -1.0, Z1 - ZL)         # upper floor down to the landing
assert abs(LAND_Y + run_lo - TOP_Y) < 2.0 and abs(TOP_Y - run_up - LAND_Y) < 2.0, (run_lo, run_up)

# --- rails ---------------------------------------------------------------------------------------------------------------------------
balusters("ROW_Stair2", LOW[1] - 8.0, LAND_Y + run_lo, LAND_Y, Z0, ZL - Z0, yaw_lo)      # the lower flight's room side
balusters("ROW_Stair3", UP[1] - 8.0, TOP_Y - run_up, TOP_Y, ZL, Z1 - ZL, yaw_up)         # the upper flight's inner side
bar_rail("ROW_Landing2_Rail", "Y", EDGE_X - 6.0, PARTY_Y + 6.0, LAND_Y - 6.0, ZL)        # the landing's room edge
bar_rail("ROW_Well2_X", "Y", EDGE_X + 6.0, PARTY_Y + 6.0, TOP_Y - 6.0, Z1)              # the opening's room-side edge
bar_rail("ROW_Well2_Y", "X", TOP_Y + 6.0, LOW[0], EDGE_X - 6.0, Z1)                      # over the lower flight's foot

# --- slab edges on the opening's cut faces (as ROW_SlabEdge1_*) -----------------------------------------------------------------------
piece("ROW_SlabEdge2_0", CUBE, (EDGE_X - 1.0, PARTY_Y, 350.0), (0.0, 0.0, 0.0), (0.01, (TOP_Y - PARTY_Y) / 100.0, 0.18), "ROW_SlabEdge1_1_0")
piece("ROW_SlabEdge2_1", CUBE, (UP[1], TOP_Y - 1.0, 350.0), (0.0, 0.0, 0.0), ((EDGE_X - UP[1]) / 100.0, 0.01, 0.18), "ROW_SlabEdge1_1_0")
piece("ROW_SlabEdge2_2", CUBE, (WALL_W, PARTY_Y, 350.0), (0.0, 0.0, 0.0), ((EDGE_X - WALL_W) / 100.0, 0.01, 0.18), "ROW_SlabEdge1_1_0")

plan = {"add": add,
        "remove": ["ROW_Slab1_6", "ROW_SlabEdge1_1_0", "ROW_SlabEdge1_1_1", "ROW_SlabEdge1_1_2", "ROW_SlabEdge1_1_3",
                   "ROW_H4_UB_Floor1", "ROW_H4_UB_Floor3"],
        "modify": {"ROW_Slab1_4": {"location": [-1050.0, -980.0, 350.0], "scale": [3.75, round((PARTY_Y + 980.0) / 100.0, 4), 0.17]}},
        "tag": "S4", "folder": "Slums/Interiors"}
json.dump(plan, open(OUT, "w"), indent=1)
print(len(add), "pieces:", sorted({p["label"].rsplit("_", 1)[0] for p in add}))
print("runs: lower %.1f cm (landing %s to %s), upper %.1f cm" % (run_lo, LAND_Y, LAND_Y + run_lo, run_up))
for p in add:
    if "Stair" in p["label"] and "Post" not in p["label"] and "Rail" not in p["label"]:
        print("  ", p["label"], p["loc"], p["rot"], p["scale"])
