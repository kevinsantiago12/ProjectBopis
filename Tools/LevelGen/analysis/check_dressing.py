"""Offline check of the plan's building dressing. User 2026-11-04: "some of your patch placements and vent placements go into the
stairs, theres also a pipe that overlaps with another pipe". Exits 1 if anything fails. Lists:
- dressing on a wall the gallery stairs run against, lower than the stairs' top;
- downpipes closer than PIPE_GAP to each other, or two on one house ("for pipes, never 2 on the same house");
- patches, vents, air conditioners and racks a downpipe runs across, on any block;
- plywood patches with no other beside them ("place atleast 2 beside each other", "except the roof type, the wood one, yes do 2");
- the street dressing (user 2026-11-05: "do all that and add it to the tool"): nothing on a hollow-block face but posters and big tags, nothing on a thin wall, nothing on the
  stair walls, nothing across a pipe, a wire too low, low over the gallery or through a house, a light with no fitting;
- posters, shutters, signs, meters, tarps and gates not within 40 cm of the ends of their wall, and no tarp over a door;
- posters: not across a pipe, not over a vent block, and the same movie poster or ad not twice in a view, nor side by side. Only candidates repeat;
- power poles on open ground with walking room left, clear of doors, the gallery, its stairs, awnings and gameplay points; water meters off the door openings;
  tyres lying on a roof sheet;
- graffiti: not over a poster, a door or a window, and the same image not twice in a view.

Usage (from the project root): python Tools/LevelGen/analysis/check_dressing.py"""
import glob
import json
import math
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import plan_source  # noqa: E402   a level's plan: check_dressing.py [level]
PLAN = plan_source.plan_glob()
LAYOUT = plan_source.layout_path()
PIPE_GAP = 70.0         # cm between two pipes' centres
STAIR_TOP = 520.0       # the top of the stairs' rails
STAIR_RUN = 7.0         # m: longer than the layout's footprint (gen_level.py STAIR_RUN)
PLATE_W = 162.0         # SM_MetalPlate_A's native width

items = []
for f in sorted(glob.glob(PLAN)):
    items += plan_source.normalise(json.load(open(f, encoding="utf-8")))
L = json.load(open(LAYOUT, encoding="utf-8"))
LEVEL = plan_source.load_level()
OX, OY = LEVEL.ORIGIN             # the layout point at the world origin: the arena's (27, 24)
# The ground the passes keep pieces on, in layout metres (x0, y0, x1, y1): the arena's rectangle, or a level's own footprint.
BOUNDS = L.get("bounds") or (0.0, 0.0, L["arena"][0], L["arena"][1])


def to_lay(X, Y):
    return Y / 100.0 + OX, OY - X / 100.0


def by_folder(*names):
    return [p for p in items if p["folder"] in ["BackAlleys/" + n for n in names]]


def run_dir(p):
    """The wall's run direction, from a piece's yaw (local X runs along the wall on the planes and tin)."""
    a = math.radians(p["rot"][1])
    return math.cos(a), math.sin(a)


def half_width(p):
    a = p["asset"].split("/")[-1]
    if a == "Plane":
        return abs(p["scale"][0]) * 50.0
    if a.startswith("SM_MetalPlate"):
        return abs(p["scale"][0]) * PLATE_W / 2
    return 0.0


def low_z(p):
    a = p["asset"].split("/")[-1]
    if a == "Plane":
        return p["loc"][2] - abs(p["scale"][1]) * 50.0
    if a.startswith("SM_MetalPlate"):
        return p["loc"][2] - abs(p["scale"][2]) * 165.0
    return p["loc"][2] - 100.0


def in_stairs(X, Y):
    lx, ly = to_lay(X, Y)
    return any(g["x0"] - 0.2 < lx < g["x1"] + 0.2 and g["y1"] - STAIR_RUN - 0.2 < ly < g["y1"] + 0.2 for g in L["stairs"])


bad = 0
stair_hits = []
for p in by_folder("Patches", "Vents", "WallACs", "Downpipes"):
    rx, ry = run_dir(p)
    hw = half_width(p)
    # 20 cm out from the wall, which way depends on the piece: test both sides. The stairs stand on one of them.
    nx, ny = -ry, rx
    x, y = p["loc"][0], p["loc"][1]
    if low_z(p) < STAIR_TOP and any(in_stairs(x + rx * k + nx * n, y + ry * k + ny * n)
                                    for k in (-hw, 0.0, hw) for n in (-20.0, 20.0)):
        stair_hits.append(p["label"])
print("dressing against the stairs:", len(stair_hits), stair_hits[:20])
bad += len(stair_hits)

# A pipe's centre: its pivot is 15.4 cm nearer the wall, and local +Y is outward. Measuring from the pivot missed a real overlap.
columns = {}
for p in by_folder("Downpipes"):
    a_ = math.radians(p["rot"][1])
    columns.setdefault(p["label"].rsplit("_", 1)[0], {"loc": (p["loc"][0] - math.sin(a_) * 15.4, p["loc"][1] + math.cos(a_) * 15.4)})
cols = list(columns.items())
pipe_hits = []
for i, (a, pa) in enumerate(cols):
    for b, pb in cols[i + 1:]:
        d = math.hypot(pa["loc"][0] - pb["loc"][0], pa["loc"][1] - pb["loc"][1])
        if d < PIPE_GAP:
            pipe_hits.append((a, b, round(d)))
print("downpipes too close:", len(pipe_hits), pipe_hits)
bad += len(pipe_hits)
per_house = {}
for a, _ in cols:
    bid = a.split("_")[1]
    per_house.setdefault(bid[:-1] if bid.endswith("b") else bid, []).append(a)
two_pipes = [v for v in per_house.values() if len(v) > 1]
print("houses with two downpipes:", len(two_pipes), two_pipes)
bad += len(two_pipes)

cross_hits = []
for p in by_folder("Patches", "Vents"):
    rx, ry = run_dir(p)
    hw = half_width(p)
    for a, pa in cols:
        dx, dy = pa["loc"][0] - p["loc"][0], pa["loc"][1] - p["loc"][1]
        along, off = dx * rx + dy * ry, abs(-dx * ry + dy * rx)
        if abs(along) < hw + 8.0 and off < 30.0:
            cross_hits.append((p["label"], a))
print("patches and vents under a downpipe:", len(cross_hits), cross_hits[:20])
bad += len(cross_hits)

# What stands proud of a wall and a pipe, on any block: air conditioners and racks.
proud_hits = []
for p in by_folder("WallACs", "Laundry"):
    a_ = p["asset"].split("/")[-1]
    yaw = math.radians(p["rot"][1])
    if a_ == "SM_DryingRack_A_002":             # local X along the wall for 271 cm, local -Y out
        rx, ry, ox, oy, lo, hi = math.cos(yaw), math.sin(yaw), math.sin(yaw), -math.cos(yaw), 0.0, 271.0 * p["scale"][0]
    elif a_ == "SM_Windows_04":                 # local Y along the wall from 0, local -X out
        rx, ry, ox, oy, lo, hi = -math.sin(yaw), math.cos(yaw), -math.cos(yaw), -math.sin(yaw), 0.0, 106.4 * p["scale"][1]
    elif a_.startswith("SM_Air_Conditioning"):  # the same, centred
        rx, ry, ox, oy, lo, hi = -math.sin(yaw), math.cos(yaw), -math.cos(yaw), -math.sin(yaw), -46.5 * p["scale"][1], 46.5 * p["scale"][1]
    else:
        continue
    for a, pa in cols:
        dx, dy = pa["loc"][0] - p["loc"][0], pa["loc"][1] - p["loc"][1]
        if lo - 8.0 < dx * rx + dy * ry < hi + 8.0 and -30.0 < dx * ox + dy * oy < 75.0:
            proud_hits.append((p["label"], a))
print("air conditioners and racks across a downpipe:", len(proud_hits), proud_hits[:20])
bad += len(proud_hits)

# Shots stop on a patch and play its own surface: wood for plywood, metal for tin (user 2026-11-07: "the sheet metals and wood on the walls are not playing the correct impact").
wrong_surface = [p["label"] for p in by_folder("Patches") if p["nocoll"] or p.get("coll") != "IgnoreOnlyPawn"
                 or not (p.get("phys") or "").endswith("/" + ("Wood" if "_Ply_" in p["mats"][0] else "Metal"))]
print("patches that don't stop shots or play the wrong surface:", len(wrong_surface), wrong_surface[:8])
bad += len(wrong_surface)

patches = [p for p in by_folder("Patches") if p["asset"].endswith("/Plane")]
alone = []
for p in patches:
    rx, ry = run_dir(p)
    hw = half_width(p)
    if not any(q is not p and abs((q["loc"][0] - p["loc"][0]) * rx + (q["loc"][1] - p["loc"][1]) * ry) < hw + half_width(q) + 6.0 and
               abs(-(q["loc"][0] - p["loc"][0]) * ry + (q["loc"][1] - p["loc"][1]) * rx) < 8.0 for q in patches):
        alone.append(p["label"])
print("plywood patches on their own:", len(alone), alone[:20])
bad += len(alone)

# --- Street dressing ---------------------------------------------------------------------------------------------------------------
STREET = ("Meters", "Shutters", "Gates", "Tarps", "Signs", "Sills", "Peel", "Lights", "Posters", "WaterMeters", "Graffiti")
WIRE_LOW = 560.0        # gen_level.py WIRE_LOW: the spans at the second floor, above the laundry
LOW_FLOOR = 300.0       # gen_level.py LOW_FLOOR: the low layer, above a head
DECK_CLEAR = 620.0      # gen_level.py DECK_CLEAR: over the gallery or its stairs, high enough to walk under
POSTER_GAP = 1000.0     # gen_level.py POSTER_GAP: the same movie poster or ad comes round again this far on
FACE_EDGE = 40.0        # gen_level.py FACE_EDGE: posters, shutters, signs, meters, tarps and gates, from the ends of their wall
tiles = {p["label"]: p for p in by_folder("Blocks")}
all_labels = {p["label"] for p in items}
thin_ids = {b["id"] for b in L["blocks"] if min(b["x1"] - b["x0"], b["y1"] - b["y0"]) <= 1.5}


def axes(p):
    """FRotationMatrix's local axes."""
    pi, ya, ro = (math.radians(a) for a in p["rot"])
    cp, sp, cy, sy, cr, sr = math.cos(pi), math.sin(pi), math.cos(ya), math.sin(ya), math.cos(ro), math.sin(ro)
    return ((cp * cy, cp * sy, sp), (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp), (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp))


def rod_ends(p):
    """A thin SM_Cube's two ends: its pivot is a corner, and its length is along local X."""
    X, Y, Z = axes(p)
    sx, sy, sz = (s * 100.0 for s in p["scale"])
    centre = tuple(p["loc"][i] + X[i] * sx / 2 + Y[i] * sy / 2 + Z[i] * sz / 2 for i in range(3))
    return tuple(centre[i] - X[i] * sx / 2 for i in range(3)), tuple(centre[i] + X[i] * sx / 2 for i in range(3))


def tile_of(label):
    """The wall tile a piece's label names: Meter_B7_E0_0_1_Box -> B7_E0_0_1."""
    q = label.split("_")[1:]
    while q and q[0] in ("Bulb", "Tube", "Lamp"):
        q = q[1:]
    for n_ in range(len(q), 0, -1):
        k = "_".join(q[:n_])
        if k in tiles:
            return tiles[k]
    return None


on_hollow, on_thin, street_stairs = [], [], []
for p in by_folder(*STREET):
    t = tile_of(p["label"])
    if t is None:
        continue
    # Posters may: "except hollow block, which yu can put posters on". So may the big tags: "yes do grafitti on hollow blocks, actually allowed to paint them big".
    if t.get("mats") and "HollowBlocks" in t["mats"][0] and p["folder"] != "BackAlleys/Posters" and not (p["folder"] == "BackAlleys/Graffiti" and p["label"].endswith("_Big")):
        on_hollow.append(p["label"])
    if t["label"].split("_")[0] in thin_ids:
        on_thin.append(p["label"])
    if p["asset"].split("/")[-1] != "SM_Cube" and not p.get("light") and p["folder"] != "BackAlleys/Sills" and p["loc"][2] < STAIR_TOP:
        rx, ry = run_dir(p)
        along = (-abs(p["scale"][0]) * 50.0, 0.0, abs(p["scale"][0]) * 50.0) if p["asset"].endswith("/Plane") else (0.0, 100.0)    # a plane's pivot is its middle
        if any(in_stairs(p["loc"][0] + rx * k + -ry * n, p["loc"][1] + ry * k + rx * n) for k in along for n in (-20.0, 20.0)):
            street_stairs.append(p["label"])
print("street dressing on hollow-block faces:", len(on_hollow), on_hollow[:20])
print("street dressing on thin walls:", len(on_thin), on_thin[:20])
print("street dressing against the stairs:", len(street_stairs), street_stairs[:20])
bad += len(on_hollow) + len(on_thin) + len(street_stairs)

# What climbs a wall or stands proud of it, against the pipes.
pipe_cross = []
for p in by_folder("Meters", "Shutters", "Gates", "Tarps"):
    a_ = p["asset"].split("/")[-1]
    if a_ == "SM_Cube" and "_Conduit" in p["label"]:
        (x0, y0, _), _b = rod_ends(p)
        hw, rx, ry, cx, cy = 3.0, 1.0, 0.0, x0, y0
    elif a_ == "SM_ElectricBox_C_003":
        rx, ry = run_dir(p)
        hw, cx, cy = 13.0, p["loc"][0], p["loc"][1]
    elif a_ == "SM_RollupDoor_A_001" or a_ == "SM_Metal_Gate_01":
        rx, ry = run_dir(p)
        w_ = (190.9 if a_ == "SM_RollupDoor_A_001" else 165.8) * p["scale"][0]
        hw, cx, cy = w_ / 2, p["loc"][0] + rx * w_ / 2, p["loc"][1] + ry * w_ / 2
    elif a_ == "SM_TarpCover_A_002":
        rx, ry = run_dir(p)
        hw, cx, cy = 111.5 * p["scale"][0], p["loc"][0], p["loc"][1]
    else:
        continue
    for a, pa in cols:
        dx, dy = pa["loc"][0] - cx, pa["loc"][1] - cy
        along, off = dx * rx + dy * ry, abs(-dx * ry + dy * rx)
        if a_ == "SM_Cube":
            if math.hypot(dx, dy) < 30.0:
                pipe_cross.append((p["label"], a))
        elif abs(along) < hw + 10.0 and off < 40.0:
            pipe_cross.append((p["label"], a))
print("street dressing across a downpipe:", len(pipe_cross), pipe_cross[:20])
bad += len(pipe_cross)

# Wires: the spans above the second floor, the low layer above a head, and nothing low over the gallery. Never through a house: its height is its lid's top.
lids = []
for p in by_folder("Lids"):
    if p["asset"].split("/")[-1] == "SM_Cube" and p["label"].startswith(("Lid_", "Core_")):
        x0, y0, z0 = p["loc"]
        lids.append((p["label"], x0, y0, x0 + p["scale"][0] * 100.0, y0 + p["scale"][1] * 100.0, z0 + p["scale"][2] * 100.0))
low_wires, wires_in_house, low_over_deck = [], [], []
for p in by_folder("Wires"):
    if p["asset"].split("/")[-1] != "SM_Cube":
        continue
    a3, b3 = rod_ends(p)
    lowest_ = min(a3[2], b3[2])
    if lowest_ < (LOW_FLOOR if p["label"].startswith(("LowSpan_", "Drape_", "ChainLow_", "PoleDropLow_")) else WIRE_LOW):
        low_wires.append(p["label"])
    if lowest_ < DECK_CLEAR:
        lx_, ly_ = to_lay((a3[0] + b3[0]) / 2, (a3[1] + b3[1]) / 2)
        d_ = L["deck"]
        if d_["x0"] < lx_ < d_["x1"] and d_["y0"] < ly_ < d_["y1"] or in_stairs((a3[0] + b3[0]) / 2, (a3[1] + b3[1]) / 2):
            low_over_deck.append(p["label"])
    mx, my, mz = (a3[0] + b3[0]) / 2, (a3[1] + b3[1]) / 2, (a3[2] + b3[2]) / 2
    for lab, x0, y0, x1, y1, top in lids:
        if x0 + 3.0 < mx < x1 - 3.0 and y0 + 3.0 < my < y1 - 3.0 and mz < top + 5.0:
            wires_in_house.append((p["label"], lab))
            break
# Signs: long boards only, wide enough for lettering. User: "square signage may fit chinese charachers but not alpha numberics". A lettered board (2026-11-07)
# has its image's shape instead: its front panel (291.4 x 78.6 of 300 x 84) within 2% of the board's columns in gen_level.py SIGN_BOARDS, so nothing stretches.
BOARD_COLS = {"06_Sari_Sari": (232, 1617), "07_Barberya": (174, 1674), "08_Patahian": (230, 1620), "09_Xerox": (254, 1594), "10_Carinderia": (252, 1597)}
short_signs, stretched, boards_used = [], [], []
for p in by_folder("Signs"):
    if not p["asset"].endswith("SM_Sign_A_001"):
        short_signs.append(p["label"])
        continue
    w_, h_ = 300.0 * abs(p["scale"][0]), 84.0 * abs(p["scale"][2])
    board_ = (p.get("mats") or [""])[0].split("MI_BackAlleys_SignBoard_")[-1] if "SignBoard" in (p.get("mats") or [""])[0] else None
    if board_:
        boards_used.append(board_)
        x0_, x1_ = BOARD_COLS[board_]
        want_ = (x1_ - x0_ + 1 - 4.0) / 498.0
        got_ = (w_ * 291.4 / 300.0) / (h_ * 78.6 / 84.0)
        if abs(got_ / want_ - 1.0) > 0.02:
            stretched.append((p["label"], round(got_, 2), round(want_, 2)))
    elif w_ < 2.59 * h_:
        short_signs.append(p["label"])
twice_ = sorted({b for b in boards_used if boards_used.count(b) > 1})
print("signs that aren't long boards:", len(short_signs), short_signs[:20])
print("lettered boards stretched:", len(stretched), stretched, "used:", sorted(boards_used), "twice:", twice_)
bad += len(short_signs) + len(stretched) + len(twice_)
print("wires too low:", len(low_wires), low_wires[:20])
print("low wires over the gallery or its stairs:", len(low_over_deck), low_over_deck[:20])
bad += len(low_over_deck)
print("wires through a house:", len(wires_in_house), wires_in_house[:20])
bad += len(low_wires) + len(wires_in_house)

# Posters: not across a pipe, and a movie poster or ad doesn't repeat within a view, unless it's the same row.
posters = by_folder("Posters")
poster_pipe = []
for p in posters:
    rx, ry = run_dir(p)
    for a, pa in cols:
        dx, dy = pa["loc"][0] - p["loc"][0], pa["loc"][1] - p["loc"][1]
        if abs(dx * rx + dy * ry) < abs(p["scale"][0]) * 50.0 + 8.0 and abs(-dx * ry + dy * rx) < 30.0:
            poster_pipe.append((p["label"], a))
print("posters across a downpipe:", len(poster_pipe), poster_pipe[:20])
bad += len(poster_pipe)


def wall_plane(p):
    """A plane on a wall: where it stands off, and its span along the wall and up it. Local X runs along the wall, local Y up."""
    along, off = (p["loc"][1], p["loc"][0]) if round(p["rot"][1]) % 180 == 90 else (p["loc"][0], p["loc"][1])
    return off, along - abs(p["scale"][0]) * 50.0, along + abs(p["scale"][0]) * 50.0, p["loc"][2] - abs(p["scale"][1]) * 50.0, p["loc"][2] + abs(p["scale"][1]) * 50.0


poster_vent = []
vent_planes = [(p["label"], round(p["rot"][1]) % 180, wall_plane(p)) for p in by_folder("Vents") if p["asset"].endswith("/Plane")]
for p in posters:
    yaw_ = round(p["rot"][1]) % 180
    o_, a0, a1, z0, z1 = wall_plane(p)
    for label, yaw2, (o2, b0, b1, y0, y1) in vent_planes:
        if yaw_ == yaw2 and abs(o_ - o2) < 8.0 and a0 < b1 and b0 < a1 and z0 < y1 and y0 < z1:
            poster_vent.append((p["label"], label))
print("posters over a vent block:", len(poster_vent), poster_vent[:20])
bad += len(poster_vent)

# No tarp over a door. User 2026-11-06: "dont put a tarp on the doors". SM_TarpCover_A_002 is 223 wide about its origin; SM_WallDoor_01's door is 110 wide about 111 along it.
tarp_door = []
for t_ in by_folder("Tarps"):
    if not t_["asset"].endswith("SM_TarpCover_A_002"):
        continue
    half_ = abs(t_["scale"][0]) * 111.5
    for d_ in items:
        if not d_["asset"].endswith("SM_WallDoor_01") or abs(((d_["rot"][1] - t_["rot"][1]) + 180.0) % 360.0 - 180.0) > 1.0:
            continue
        yaw_ = math.radians(d_["rot"][1])
        sx_ = d_["scale"][0]
        dx_, dy_ = d_["loc"][0] + math.cos(yaw_) * 111.0 * sx_ - t_["loc"][0], d_["loc"][1] + math.sin(yaw_) * 111.0 * sx_ - t_["loc"][1]
        along_ = abs(dx_ * math.cos(yaw_) + dy_ * math.sin(yaw_))
        off_ = abs(-dx_ * math.sin(yaw_) + dy_ * math.cos(yaw_))
        if off_ < 40.0 and along_ < half_ + 55.0 * abs(sx_) and abs(d_["loc"][2] - t_["loc"][2]) < 300.0:
            tarp_door.append((t_["label"], d_["label"]))
print("tarps over a door:", len(tarp_door), tarp_door[:20])
bad += len(tarp_door)
near_same = []
for i, p in enumerate(posters):
    if "/MI_BackAlleys_Poster_" not in p["mats"][0] or any(k in p["mats"][0] for k in ("Villareal", "Mercado", "de_Vera")):
        continue
    for q in posters[i + 1:]:
        # Side by side in one lot counts too: "you can put movie posters together side by side but not the same over and over, same goes for product ads".
        if q["mats"][0] == p["mats"][0] and math.hypot(p["loc"][0] - q["loc"][0], p["loc"][1] - q["loc"][1]) < POSTER_GAP - 200.0:
            near_same.append((p["label"], q["label"]))
# Distance from the ends of the wall: the tiles of one run share a name, and a tile is 225 cm wide natively, the half tile 112.5. The shop row is the AsiaSlum kit: 300 and 150.
runs_ = {}
for k, t in tiles.items():
    q = k.split("_")
    if len(q) == 4 and q[1][:1] in "NSEW" and q[1][1:].isdigit() and (q[3].isdigit() or q[3] == "half"):
        runs_.setdefault("_".join(q[:3]), []).append(t)
at_edge = []
for p in by_folder("Posters", "Shutters", "Gates", "Tarps", "Signs", "Meters"):
    mesh_ = p["asset"].split("/")[-1]
    if mesh_ not in ("Plane", "SM_RollupDoor_A_001", "SM_Metal_Gate_01", "SM_TarpCover_A_002", "SM_Sign_A_001", "SM_ElectricBox_C_003"):
        continue
    t = tile_of(p["label"])
    if t is None:
        continue
    rx, ry = math.cos(math.radians(t["rot"][1])), math.sin(math.radians(t["rot"][1]))
    lo, hi = None, None
    for o in runs_.get("_".join(t["label"].split("_")[:3]), [t]):
        m_ = o["asset"].split("/")[-1]
        w_ = abs(o["scale"][0]) * (150.0 if m_.endswith("_HalfA") else 300.0 if m_.startswith(("SM_Shop", "SM_House")) else 112.5 if m_ == "SM_Wall_Tile_03" else 225.0)
        a_ = o["loc"][0] * rx + o["loc"][1] * ry
        lo, hi = a_ if lo is None else min(lo, a_), a_ + w_ if hi is None else max(hi, a_ + w_)
    c_ = p["loc"][0] * rx + p["loc"][1] * ry
    # What a piece covers along the wall, from its pivot: the shutter and the gate start there, the rest are centred.
    sc_ = abs(p["scale"][0])
    # A gate is turned to show its sheet (2026-11-07): its pivot is then at the far end, and it runs back from there.
    gate_turned = mesh_ == "SM_Metal_Gate_01" and abs(((p["rot"][1] - t["rot"][1]) % 360.0) - 180.0) < 1.0
    s0_, s1_ = {"Plane": (-50.0 * sc_, 50.0 * sc_), "SM_RollupDoor_A_001": (0.0, 190.9 * sc_),
                "SM_Metal_Gate_01": (-164.1 * sc_, 1.7 * sc_) if gate_turned else (0.0, 165.8 * sc_),
                "SM_TarpCover_A_002": (-111.5 * sc_, 111.5 * sc_), "SM_Sign_A_001": (-150.0 * sc_, 150.0 * sc_), "SM_ElectricBox_C_003": (-13.0, 13.0)}[mesh_]
    if c_ + s0_ < lo + FACE_EDGE - 3.0 or c_ + s1_ > hi - FACE_EDGE + 3.0:
        at_edge.append((p["label"], round(min(c_ + s0_ - lo, hi - c_ - s1_))))
print("too near the end of their wall:", len(at_edge), at_edge[:20])
bad += len(at_edge)
print("the same poster twice in a view:", len(near_same), near_same[:20])
bad += len(near_same)
print("posters:", len(posters), "designs:", len({p["mats"][0] for p in posters}))

# Every light beside its fitting. A fill (street.py FILL_*, user 2026-11-09: a point light under every spot light) beside its spot light.
no_fitting = [p["label"] for p in items if p.get("light") and not p["light"].get("fill") and p["label"].replace("Light_", "", 1) not in all_labels]
no_fitting += [p["label"] for p in items if p.get("light") and p["light"].get("fill") and p["label"][:-len("_Fill")] not in all_labels]
spot_no_fill = [p["label"] for p in items if p.get("light") and p["light"]["kind"] == "SpotLight" and p["label"] + "_Fill" not in all_labels]
print("spot lights with no fill under them:", len(spot_no_fill), spot_no_fill[:20])
bad += len(spot_no_fill)
print("lights with no fitting:", len(no_fitting), no_fitting[:20])
bad += len(no_fitting)

# Power poles: the shaft on open ground, at least 2.8 m of lane beside it, clear of doors, the gallery and its stairs, awnings and gameplay points.
blocks_ = L["blocks"]
gp_ = {}
for f_ in glob.glob(os.path.join(ROOT, *LEVEL.OUT.split("/"), LEVEL.PREFIX + "gameplay.json")):
    gp_ = json.load(open(f_, encoding="utf-8"))
keep_ = [tuple(s_["loc"][:2]) for s_ in gp_.get("spawns", [])] + [tuple(w_["loc"][:2]) for w_ in gp_.get("wander", [])] +     ([tuple(gp_["player_start"][:2])] if "player_start" in gp_ else [])


def on_block(X, Y):
    lx, ly = to_lay(X, Y)
    return not (BOUNDS[0] < lx < BOUNDS[2] and BOUNDS[1] < ly < BOUNDS[3]) or any(b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] for b in blocks_)


poles = [p for p in by_folder("Poles") if "SM_Electric_Pole" in p["asset"]]
pole_bad = []
doors_ = [d_ for d_ in items if d_["asset"].endswith("SM_WallDoor_01") and d_["loc"][2] < 100.0]
for p in poles:
    x, y = p["loc"][0], p["loc"][1]
    lx, ly = to_lay(x, y)
    d_ = L["deck"]
    if on_block(x, y):
        pole_bad.append((p["label"], "on a house"))
    if d_["x0"] - 0.3 < lx < d_["x1"] + 0.3 and d_["y0"] - 0.3 < ly < d_["y1"] + 0.3 or in_stairs(x, y):
        pole_bad.append((p["label"], "gallery or stairs"))
    if any(math.hypot(x - k_[0], y - k_[1]) < 200.0 for k_ in keep_):
        pole_bad.append((p["label"], "on a gameplay point"))
    # The widest way past: the free width across the pole, whichever of the two axes the lane runs along. A lane is free on both sides of the shaft along it.
    free_ = []
    for ax_, ay_ in ((1.0, 0.0), (0.0, 1.0)):
        a_ = next((n_ for n_ in range(20, 1000, 10) if on_block(x + ax_ * n_, y + ay_ * n_)), 1000)
        b_ = next((n_ for n_ in range(20, 1000, 10) if on_block(x - ax_ * n_, y - ay_ * n_)), 1000)
        free_.append(max(a_, b_))
    if max(free_) < 280:
        pole_bad.append((p["label"], "no walking room", free_))
    for d_ in doors_:
        yaw_ = math.radians(d_["rot"][1])
        if math.hypot(d_["loc"][0] + math.cos(yaw_) * 111.0 * d_["scale"][0] - x, d_["loc"][1] + math.sin(yaw_) * 111.0 * d_["scale"][0] - y) < 130.0:
            pole_bad.append((p["label"], "at a door", d_["label"]))
    for a_ in by_folder("Awnings"):
        if a_["asset"].split("/")[-1].startswith("SM_MetalPlate") and math.hypot(a_["loc"][0] - x, a_["loc"][1] - y) < 40.0:
            pole_bad.append((p["label"], "through an awning", a_["label"]))
print("poles:", len(poles), "in the wrong place:", len(pole_bad), pole_bad[:20])
bad += len(pole_bad)

# Water meters clear of a door's opening, and tyres lying on a sheet of their own roof.
water_door = []
for p in by_folder("WaterMeters"):
    if "SM_Water_Meter" not in p["asset"]:
        continue
    for d_ in doors_:
        yaw_ = math.radians(d_["rot"][1])
        sx_ = d_["scale"][0]
        dx_, dy_ = p["loc"][0] - d_["loc"][0], p["loc"][1] - d_["loc"][1]
        along_, off_ = dx_ * math.cos(yaw_) + dy_ * math.sin(yaw_), abs(-dx_ * math.sin(yaw_) + dy_ * math.cos(yaw_))
        if off_ < 40.0 and 30.0 * sx_ - 16.0 < along_ < 195.0 * sx_ + 16.0:
            water_door.append((p["label"], d_["label"]))
print("water meters in a door's way:", len(water_door), water_door[:20])
bad += len(water_door)
# Spread out. User 2026-11-06: "the water meter needs to be distributed more". A lot is its first meter; every quarter of the arena has some.
water_lots = {}
for p in by_folder("WaterMeters"):
    if "SM_Water_Meter" in p["asset"]:
        water_lots.setdefault(p["label"].rsplit("_", 1)[0], (p["loc"][0], p["loc"][1]))
near_lots = [(a_, b_) for i, (a_, pa_) in enumerate(water_lots.items()) for b_, pb_ in list(water_lots.items())[i + 1:] if math.hypot(pa_[0] - pb_[0], pa_[1] - pb_[1]) < 500.0]
# The quarters about the arena's centre, the world origin; on a level with its own bounds, about the middle of its dressed ground
# (a story level dresses only some sections): the box round its posters, awnings, signs and meters.
if "bounds" in L:
    dressed_ = [p["loc"] for p in by_folder("Posters", "Awnings", "Signs", "WaterMeters")]
    qx_ = (min(q[0] for q in dressed_) + max(q[0] for q in dressed_)) / 2 if dressed_ else 0.0
    qy_ = (min(q[1] for q in dressed_) + max(q[1] for q in dressed_)) / 2 if dressed_ else 0.0
else:
    qx_ = qy_ = 0.0
quarters = {(x_ > qx_, y_ > qy_) for x_, y_ in water_lots.values()}
print("water meter lots:", len(water_lots), "too close:", len(near_lots), near_lots[:20], "quarters with some:", len(quarters))
bad += len(near_lots) + ((4 - len(quarters)) if water_lots else 0)     # a level with no water meters (yet) has nothing to spread
sheets_ = [p for p in by_folder("Roofs") if "SM_MetalPlate_A" in p["asset"] and p["label"].startswith("Roof_")]
tyre_off = []
for p in by_folder("Tyres"):
    best_ = None
    for q in sheets_:
        if q["label"].split("_")[1] != p["label"].split("_")[1]:
            continue
        X, Y, Z = axes(q)
        if Y[2] < 0.0:
            Y = (-Y[0], -Y[1], -Y[2])
        d3 = tuple(p["loc"][i] - q["loc"][i] for i in range(3))
        a_, m_, h_ = sum(d3[i] * X[i] for i in range(3)), -sum(d3[i] * Z[i] for i in range(3)), sum(d3[i] * Y[i] for i in range(3))
        len_ = (164.9 if q["asset"].endswith(("_003", "_004")) else 324.9) * abs(q["scale"][2])
        if abs(a_) <= 81.2 * abs(q["scale"][0]) and 0.0 <= m_ <= len_:
            best_ = h_ if best_ is None else max(best_, h_)
    top_ = p["label"].endswith("_Top")
    if best_ is None or not (5.0 < best_ < (35.0 if top_ else 18.0)):
        tyre_off.append((p["label"], best_ and round(best_, 1)))
print("tyres off their sheets:", len(tyre_off), tyre_off[:20])
bad += len(tyre_off)

# Graffiti: what shows of it, 92% of the width and 80% of the height of its square, clear of posters, doors and windows. The same image not twice within 10 m.
graf_bad, graf_same = [], []
graffiti = by_folder("Graffiti")
openings = [d_ for d_ in by_folder("Blocks") if d_["asset"].endswith(("SM_WallDoor_01", "SM_Wall_Windows_01"))]
for i, p in enumerate(graffiti):
    w_ = abs(p["scale"][1]) * 512.0
    z0, z1 = p["loc"][2] - w_ * 0.4, p["loc"][2] + w_ * 0.4
    ya_ = math.radians(p["rot"][1])
    nx_, ny_ = -math.cos(ya_), -math.sin(ya_)       # the decal looks into the wall
    rx_, ry_ = -ny_, nx_
    for q in posters:
        dx_, dy_ = q["loc"][0] - p["loc"][0], q["loc"][1] - p["loc"][1]
        hw_ = abs(q["scale"][0]) * 50.0
        if abs(dx_ * nx_ + dy_ * ny_) < 12.0 and abs(dx_ * rx_ + dy_ * ry_) < hw_ + w_ * 0.46 and q["loc"][2] - abs(q["scale"][1]) * 50.0 < z1 and z0 < q["loc"][2] + abs(q["scale"][1]) * 50.0:
            graf_bad.append((p["label"], q["label"]))
    for d_ in openings:
        ya2 = math.radians(d_["rot"][1])
        sx_ = d_["scale"][0]
        cx_, cy_ = d_["loc"][0] + math.cos(ya2) * 112.5 * sx_, d_["loc"][1] + math.sin(ya2) * 112.5 * sx_
        dx_, dy_ = cx_ - p["loc"][0], cy_ - p["loc"][1]
        if "Shutter" not in p["label"] and abs(dx_ * nx_ + dy_ * ny_) < 12.0 and abs(dx_ * rx_ + dy_ * ry_) < 82.5 * sx_ + w_ * 0.46 and d_["loc"][2] < z1 and z0 < d_["loc"][2] + 280.0:
            graf_bad.append((p["label"], d_["label"]))
    for q in graffiti[i + 1:]:
        if q["asset"].rsplit("_", 1)[0] == p["asset"].rsplit("_", 1)[0] and math.hypot(p["loc"][0] - q["loc"][0], p["loc"][1] - q["loc"][1]) < 1000.0:
            graf_same.append((p["label"], q["label"]))
print("graffiti:", len(graffiti), "over a poster or opening:", len(graf_bad), graf_bad[:20], "the same image twice in a view:", len(graf_same), graf_same[:20])
bad += len(graf_bad) + len(graf_same)

# Nothing pasted or painted behind a post: "there is no way he was able to stick that behind the post". Low graffiti and posters. And no square metal grates: "metal square grates are not common in the ph".
posts_ = [(p["loc"][0], p["loc"][1]) for p in items if p["asset"].endswith("SM_Pillar_01") or "Electric_Pole" in p["asset"]]
behind = []
for p in posters:
    pi_, ya_, ro_ = (math.radians(a_) for a_ in p["rot"])
    nx_ = -(math.cos(ro_) * math.sin(pi_) * math.cos(ya_) + math.sin(ro_) * math.sin(ya_))
    ny_ = math.cos(ya_) * math.sin(ro_) - math.cos(ro_) * math.sin(pi_) * math.sin(ya_)
    len_ = math.hypot(nx_, ny_) or 1.0
    nx_, ny_ = nx_ / len_, ny_ / len_
    for px_, py_ in posts_:
        if 0.0 < (px_ - p["loc"][0]) * nx_ + (py_ - p["loc"][1]) * ny_ < 90.0 and abs((px_ - p["loc"][0]) * -ny_ + (py_ - p["loc"][1]) * nx_) < abs(p["scale"][0]) * 50.0 + 30.0:
            behind.append(p["label"])
for p in graffiti:
    if p["label"].endswith("_Big") or "Shutter" in p["label"]:
        continue
    ya_ = math.radians(p["rot"][1])
    nx_, ny_ = -math.cos(ya_), -math.sin(ya_)
    w_ = abs(p["scale"][1]) * 512.0
    for px_, py_ in posts_:
        if 0.0 < (px_ - p["loc"][0]) * -nx_ + (py_ - p["loc"][1]) * -ny_ < 90.0 and abs((px_ - p["loc"][0]) * -ny_ + (py_ - p["loc"][1]) * nx_) < 0.46 * w_ + 30.0:
            behind.append(p["label"])
grates = [p["label"] for p in items if p["folder"] == "BackAlleys/GroundDirt" and p["asset"].split("/")[-1] in ("MI_Decal_01", "MI_Decal_05")]
print("posters and graffiti behind a post:", len(behind), behind[:20], "square grates:", len(grates))
bad += len(behind) + len(grates)

# Dirt against the houses. User 2026-11-06: "They either go above to the floor lining OR they do not hit the edge at all". A strip's dense edge lies just under the lining along its whole length, and no ground decal stands high enough to paint up a wall.
floor_b = [(p["loc"][0], p["loc"][1], p["loc"][0] + p["scale"][0] * 100.0, p["loc"][1] + p["scale"][1] * 100.0) for p in items if p["folder"] == "BackAlleys/Floors"]


def on_floor(x_, y_):
    return any(b_[0] <= x_ <= b_[2] and b_[1] <= y_ <= b_[3] for b_ in floor_b)


FOOT_EDGE = {"MI_BackAlleys_Grime_Soft": 0.985, "MI_BackAlleys_Grime_Grit01": 0.775, "MI_BackAlleys_Grime_Grit02": 0.69}
# A pour sits on the road (the arena: one road at 0) or, where the ground has heights (a story level), on its own slab:
# the GroundBody cube under it, measured from that slab's top. Ground decals are measured from the same.
_bodies = [(q["loc"][0], q["loc"][1], q["loc"][0] + q["scale"][0] * 100, q["loc"][1] + q["scale"][1] * 100, q["loc"][2] + q["scale"][2] * 100)
           for q in items if q["folder"] == "BackAlleys/GroundBody"]


def _road_at(x_, y_):
    tops = [t for x0_, y0_, x1_, y1_, t in _bodies if x0_ <= x_ <= x1_ and y0_ <= y_ <= y1_]
    return max(tops) if tops else 0.0


foot_off, gd_high = [], []
for p in items:
    if p["folder"] != "BackAlleys/GroundDirt":
        continue
    z_rel = p["loc"][2] - _road_at(p["loc"][0], p["loc"][1])
    if z_rel + abs(p["scale"][0]) * 128.0 > 1.2 or z_rel - abs(p["scale"][0]) * 128.0 > -0.1:     # "the decal shoud be super thin and hit just about the surface of the road"
        gd_high.append(p["label"])
    name_ = p["asset"].split("/")[-1]
    leak_ = "Grime_Leak" in name_
    if name_ not in FOOT_EDGE and not leak_:
        continue
    ya_ = math.radians(p["rot"][1])
    ux_, uy_ = math.cos(ya_), math.sin(ya_)
    # Along, and out from the wall. A strip is turned so its image's bottom edge lies against the wall, a stain so its top edge does.
    ox_, oy_ = (-math.sin(ya_), math.cos(ya_)) if leak_ else (math.sin(ya_), -math.cos(ya_))
    u_, v_ = abs(p["scale"][2]) * 512.0, abs(p["scale"][1]) * 512.0
    d_ = 0.5 * v_ if leak_ else (FOOT_EDGE[name_] - 0.5) * v_
    ex_, ey_ = p["loc"][0] - ox_ * d_, p["loc"][1] - oy_ * d_
    for k_ in range(7):
        t_ = (k_ / 6.0 - 0.5) * (u_ - 12.0)
        px_, py_ = ex_ + ux_ * t_, ey_ + uy_ * t_
        # Under the lining, and out of it again within a few cm.
        if not on_floor(px_ - ox_ * 0.5, py_ - oy_ * 0.5) or on_floor(px_ + ox_ * 3.0, py_ + oy_ * 3.0):
            foot_off.append(p["label"])
            break
pour_high = [p["label"] for p in items if p["folder"] == "BackAlleys/Ground" and p["loc"][2] - _road_at(p["loc"][0], p["loc"][1]) > 0.85]
print("dirt strips and stains off the lining's edge:", len(foot_off), foot_off[:20], "ground decals that reach up a wall or miss the road:", len(gd_high), gd_high[:10], "pours too high for them:", len(pour_high))
bad += len(foot_off) + len(gd_high) + len(pour_high)

# Props. User 2026-11-06: "wooden bench-stools, plastic seats and tables in some areas. Buckets, potted plants on the balconies". Nothing on the ground in a door's way or on the stairs; pots and their plants up on a terrace.
props_ = by_folder("Props")
prop_door, prop_stair, pot_low = [], [], []
stairs_ = [p for p in items if p["folder"] == "BackAlleys/Gallery" and "stair_" in p["label"] and p["asset"].endswith("SM_Stair_A_001")]
for p in props_:
    if p["loc"][2] > 30.0:
        continue
    if "_Pot_" in p["label"]:
        pot_low.append(p["label"])
        continue
    for d_ in openings:
        if not d_["asset"].endswith("SM_WallDoor_01"):
            continue
        ya2 = math.radians(d_["rot"][1])
        sx_ = d_["scale"][0]
        rx_, ry_ = math.cos(ya2), math.sin(ya2)
        cx_, cy_ = d_["loc"][0] + rx_ * 112.5 * sx_, d_["loc"][1] + ry_ * 112.5 * sx_
        dx_, dy_ = p["loc"][0] - cx_, p["loc"][1] - cy_
        if abs(dx_ * rx_ + dy_ * ry_) < 82.5 * sx_ and 0.0 < dx_ * -ry_ + dy_ * rx_ < 110.0 and d_["loc"][2] < 30.0:
            prop_door.append((p["label"], d_["label"]))
# Seats that have room: a chair is 58 x 65, so two nearer than 62 cm go through each other.
seats_ = [p for p in props_ if p["asset"].endswith(("SM_Monobloc_Chair_01", "SM_Monobloc_Stool_01", "SM_Monobloc_Stool_02")) and "Prop_Table_" in p["label"] and "Seat" in p["label"]]
seat_lap = [(a_["label"], b_["label"]) for i, a_ in enumerate(seats_) for b_ in seats_[i + 1:] if math.hypot(a_["loc"][0] - b_["loc"][0], a_["loc"][1] - b_["loc"][1]) < 62.0]
print("props:", len(props_), "in a door's way:", len(prop_door), prop_door[:12], "pots at street level:", len(pot_low), pot_low[:6], "seats through each other:", len(seat_lap), seat_lap[:6])
# "one of the chairs is into the wall too". A seat's, table's or bench's footprint clear of every house's slab, turned as it stands. The AsiaSlum table is bench or stool by its scale.
FOOT_HALF = {"SM_Monobloc_Chair_01": (29.0, 33.0), "SM_Monobloc_Chair_03": (65.0, 34.0), "SM_Monobloc_Stool_01": (20.0, 20.0), "SM_Monobloc_Stool_02": (19.0, 19.0), "SM_Table_01": (62.0, 37.0)}
floor_all = [(p["loc"][0], p["loc"][1], p["loc"][0] + p["scale"][0] * 100.0, p["loc"][1] + p["scale"][1] * 100.0) for p in items if p["folder"] == "BackAlleys/Floors"]
in_wall = []
for p in props_:
    name_ = p["asset"].split("/")[-1]
    if p["loc"][2] > 30.0:
        continue
    half_ = (abs(p["scale"][0]) * 107.0, abs(p["scale"][1]) * 58.0) if name_ == "SM_Table_B_001" else FOOT_HALF.get(name_)
    if not half_:
        continue
    c_, s_ = math.cos(math.radians(p["rot"][1])), math.sin(math.radians(p["rot"][1]))
    for ax_, ay_ in ((1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)):
        px_, py_ = p["loc"][0] + c_ * ax_ * half_[0] - s_ * ay_ * half_[1], p["loc"][1] + s_ * ax_ * half_[0] + c_ * ay_ * half_[1]
        if any(b_[0] <= px_ <= b_[2] and b_[1] <= py_ <= b_[3] for b_ in floor_all):
            in_wall.append(p["label"])
            break
# Nothing through a table; no table seat in a doorway.
tables_ = [p for p in props_ if p["asset"].endswith("SM_Table_01")]
under_table = [p["label"] for p in props_ if "Prop_DoorPot_" in p["label"] and "_Plant" not in p["label"] for t_ in tables_ if math.hypot(p["loc"][0] - t_["loc"][0], p["loc"][1] - t_["loc"][1]) < 80.0]
seat_door = [p["label"] for p in props_ if "Prop_Table_" in p["label"] and "_Seat" in p["label"] for c_ in [(d_["loc"][0] + math.cos(math.radians(d_["rot"][1])) * 112.5 * d_["scale"][0], d_["loc"][1] + math.sin(math.radians(d_["rot"][1])) * 112.5 * d_["scale"][0]) for d_ in openings if d_["asset"].endswith("SM_WallDoor_01")] if math.hypot(p["loc"][0] - c_[0], p["loc"][1] - c_[1]) < 140.0]
print("furniture into a wall:", len(in_wall), in_wall[:12], "pots under a table:", len(under_table), under_table[:6], "table seats in a doorway:", len(seat_door), seat_door[:6])
bad += len(in_wall) + len(under_table) + len(seat_door)
# "move the ricebags to the secured balconies". None on the street. "put some potted plants along the wall near doors": those stay near one.
rice_low = [p["label"] for p in items if "SM_Rice_Bag" in p["asset"] and p["loc"][2] < 100.0]
door_centres = [(d_["loc"][0] + math.cos(math.radians(d_["rot"][1])) * 112.5 * d_["scale"][0], d_["loc"][1] + math.sin(math.radians(d_["rot"][1])) * 112.5 * d_["scale"][0]) for d_ in openings if d_["asset"].endswith("SM_WallDoor_01")]
pot_far = [p["label"] for p in props_ if "Prop_DoorPot_" in p["label"] and min(math.hypot(p["loc"][0] - c_[0], p["loc"][1] - c_[1]) for c_ in door_centres) > 330.0]
print("rice sacks on the street:", len(rice_low), rice_low[:6], "door pots not near a door:", len(pot_far), pot_far[:6], "door pots:", sum(1 for p in props_ if "Prop_DoorPot_" in p["label"] and "_Plant" not in p["label"]))
bad += len(rice_low) + len(pot_far)
# "monobloc stool 02 is a chair, not a table". A seat stays seat-sized.
big_stool = [p["label"] for p in props_ if "SM_Monobloc" in p["asset"] and max(abs(v_) for v_ in p["scale"]) > 1.01]
print("monobloc pieces scaled up:", len(big_stool), big_stool[:6])
# The pack's monobloc instances with "Activate Random Color?" on take their colour from the world position, so a physical piece changes colour as it moves (user 2026-11-07). Every monobloc
# piece needs Chair_01a-c (random colour off), or a *_SpawnColour instance (colour from its seed, picked once) with a seed for the placers to write.
_mono_random = {"/Game/Philippines_Markets/Materials/MI_Monobloc_" + k_ for k_ in ("Chair_01", "Chair_01d", "Chair_03", "Chair_03a", "Stool_01", "Stool_01a", "Stool_01b", "Stool_02")}
mono_moving = [p["label"] for p in props_ if "SM_Monobloc" in p["asset"] and (not p["mats"] or any(m_ in _mono_random for m_ in p["mats"])
                                                                               or (p["mats"][0].endswith("_SpawnColour") and p.get("seed") is None))]
print("monobloc pieces whose colour moves with them:", len(mono_moving), mono_moving[:8])
bad += len(mono_moving)
bad += len(prop_door) + len(pot_low) + len(seat_lap) + len(big_stool)

# Physical pieces start clear of everything: "make sure whatevr is a physical object does not overlap initially to any other object, i saw a bucket overlapping pipes earilier".
# Boxes from the packs' measured bounds (Saved/LevelGen/visual/meshes.json), turned as placed. Static props touching something are listed too, but only physical ones fail.
try:
    _mb = {e_["path"]: (e_["bounds_min"], e_["bounds_max"]) for e_ in json.load(open("Saved/LevelGen/visual/meshes.json", encoding="utf-8"))}
except (OSError, ValueError, KeyError, TypeError):
    _mb = {}
_mb["/Game/LevelPrototyping/Meshes/SM_Cube"] = ((0.0, 0.0, 0.0), (100.0, 100.0, 100.0))
_mb["/Engine/BasicShapes/Plane"] = ((-50.0, -50.0, 0.0), (50.0, 50.0, 0.0))
for _src, _dst in (("SM_Garbage_bag_01", "SM_BackAlleys_GarbageBag_01"), ("SM_Garbage_bag_02", "SM_BackAlleys_GarbageBag_02"), ("SM_Garbage_bag_green_03", "SM_BackAlleys_GarbageBag_Green_03")):
    if "/Game/Megapack/Meshes/MiddleEast/" + _src in _mb:      # the physical bags are project copies of the pack's (gen_level.py LT_BAG_PHYS)
        _mb["/Game/ThirdPerson/BackAlleys/" + _dst] = _mb["/Game/Megapack/Meshes/MiddleEast/" + _src]
bags_ = [p for p in by_folder("Litter") if p.get("physics")]


def piece_box(p):
    if p.get("decal") or p.get("light") or p["asset"] not in _mb:
        return None
    lo_, hi_ = _mb[p["asset"]]
    sx_, sy_, sz_ = p["scale"]
    pr, yr, rr = (math.radians(a_) for a_ in p["rot"])
    cp, sp, cy, sy, cr, sr = math.cos(pr), math.sin(pr), math.cos(yr), math.sin(yr), math.cos(rr), math.sin(rr)
    X_, Y_, Z_ = (cp * cy, cp * sy, sp), (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp), (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp)
    pts = [tuple(p["loc"][k_] + X_[k_] * a_ * sx_ + Y_[k_] * b_ * sy_ + Z_[k_] * c_ * sz_ for k_ in range(3)) for a_ in (lo_[0], hi_[0]) for b_ in (lo_[1], hi_[1]) for c_ in (lo_[2], hi_[2])]
    z0_, z1_ = min(q_[2] for q_ in pts), max(q_[2] for q_ in pts)
    if abs(p["rot"][0]) < 0.5 and abs(p["rot"][2]) < 0.5:
        mx_, my_ = (lo_[0] + hi_[0]) / 2 * sx_, (lo_[1] + hi_[1]) / 2 * sy_
        return (p["loc"][0] + cy * mx_ - sy * my_, p["loc"][1] + sy * mx_ + cy * my_, abs(hi_[0] - lo_[0]) * abs(sx_) / 2, abs(hi_[1] - lo_[1]) * abs(sy_) / 2, p["rot"][1], z0_, z1_)
    xs_, ys_ = [q_[0] for q_ in pts], [q_[1] for q_ in pts]
    return ((min(xs_) + max(xs_)) / 2, (min(ys_) + max(ys_)) / 2, (max(xs_) - min(xs_)) / 2, (max(ys_) - min(ys_)) / 2, 0.0, z0_, z1_)


def boxes_meet(a_, b_, gap=0.5):
    if a_[5] + gap >= b_[6] or b_[5] + gap >= a_[6]:
        return False
    for box_ in (a_, b_):
        c_, s_ = math.cos(math.radians(box_[4])), math.sin(math.radians(box_[4]))
        for ax_, ay_ in ((c_, s_), (-s_, c_)):
            def reach(q_):
                cq, sq = math.cos(math.radians(q_[4])), math.sin(math.radians(q_[4]))
                return abs((cq * ax_ + sq * ay_) * q_[2]) + abs((-sq * ax_ + cq * ay_) * q_[3])
            if abs((b_[0] - a_[0]) * ax_ + (b_[1] - a_[1]) * ay_) + gap >= reach(a_) + reach(b_):
                return False
    return True


near_ = [(p["label"], p["folder"], piece_box(p)) for p in items if p["loc"][2] < 300.0 and p["folder"] not in ("BackAlleys/Ground", "BackAlleys/GroundDirt")]
near_ = [n_ for n_ in near_ if n_[2] and n_[2][5] < 160.0]
phys_touch, static_touch = [], []
# Physical pieces up off the street (pots on balconies) against everything within 3 m (gen_level.py does the same).
all_ = [(p["label"], p["folder"], piece_box(p)) for p in items if p["folder"] not in ("BackAlleys/Ground", "BackAlleys/GroundDirt")]
all_ = [n_ for n_ in all_ if n_[2]]
for p in props_ + bags_:
    box_ = piece_box(p)
    if box_ is None:
        continue
    phys_ = p.get("physics") or (p.get("weld_to") and not p["nocoll"])     # a pot's plant is only attached, with no collision
    high_ = box_[5] > 30.0
    if high_ and not phys_:
        continue
    pool_ = [n_ for n_ in all_ if abs(n_[2][0] - box_[0]) < 300.0 and abs(n_[2][1] - box_[1]) < 300.0] if high_ else near_
    mates = {p["label"], p.get("weld_to")} | {q_["label"] for q_ in props_ if q_.get("weld_to") == p["label"]}
    # A plant stands in its pot, a lid on its bucket, a cup on its table, a crate on a crate: those are meant. A pot among its neighbours' leaves too.
    stem_ = p["label"].replace("_Plant", "").replace("_Lid", "")
    pot_ = "Pot_" in p["label"] and not p["label"].endswith("_Plant")
    for l_, f_, b_ in pool_:
        if l_ in mates or l_.startswith(stem_) or stem_.startswith(l_.replace("_Plant", "")) or (pot_ and l_.endswith("_Plant")):
            continue
        if boxes_meet(box_, b_):
            (phys_touch if phys_ else static_touch).append((p["label"], l_))
            break
print("physical pieces touching something at start:", len(phys_touch), phys_touch[:10], "physical pieces:", sum(1 for p in props_ if p.get("physics")), "welded:", sum(1 for p in props_ if p.get("weld_to")),
      "physical bags:", len(bags_), "untested:", [p["label"] for p in bags_ if piece_box(p) is None])
bad += sum(1 for p in bags_ if piece_box(p) is None)
print("  static props touching something:", len(static_touch), static_touch[:12])
bad += len(phys_touch) + len(static_touch)

# AsiaSlum cables (passes/asia_cables.py, 2026-11-09): every bundle's two ends on a ring's centre or at a pole, its lowest point 4.8 m up or
# more (the ground is at most 1.8 m: 3 m over it, as the wires), and no bundle through a house. A bundle's centre line runs local X 0..401,
# 10 cm along local -Y; its sag is 45 cm (B_001) or 18 (B_003) at scale 1; a ring's centre hangs 47 cm along its local -Z.
cab_ = by_folder("Cables")
ring_c = []
for p in cab_:
    if p["asset"].endswith("SM_Cable_C_001"):
        X_, Y_, Z_ = axes(p)
        ring_c.append(tuple(p["loc"][k] - Z_[k] * 47.0 * p["scale"][2] for k in range(3)))
pole_xy = [tuple(p["loc"][:2]) for p in items if "Electric_Pole" in p["asset"]]
houses_ = L.get("houses", {})
cab_bad = []
for p in cab_:
    if "SM_Cable_B_00" not in p["asset"]:
        continue
    X_, Y_, Z_ = axes(p)
    s_ = p["scale"]
    a3 = tuple(p["loc"][k] - Y_[k] * 10.0 * s_[1] for k in range(3))
    b3 = tuple(a3[k] + X_[k] * 401.0 * s_[0] for k in range(3))
    sag_ = (45.0 if p["asset"].endswith("B_001") else 18.0) * s_[2]
    for e in (a3, b3):
        if not any(math.dist(e, c_) < 6.0 for c_ in ring_c) and not any(math.hypot(e[0] - q[0], e[1] - q[1]) < 40.0 for q in pole_xy):
            cab_bad.append((p["label"], "end not on a ring or pole", [round(v) for v in e]))
    if min(a3[2], b3[2]) - sag_ < 480.0:
        cab_bad.append((p["label"], "low", round(min(a3[2], b3[2]) - sag_)))
    for k in range(1, 10):
        u_ = k / 10.0
        q = (a3[0] + (b3[0] - a3[0]) * u_, a3[1] + (b3[1] - a3[1]) * u_, a3[2] + (b3[2] - a3[2]) * u_ - 4.0 * sag_ * u_ * (1.0 - u_))
        lx_, ly_ = to_lay(q[0], q[1])
        hit = next((h for h, v in houses_.items() if v["rf"][0] < lx_ < v["rf"][2] and v["rf"][1] < ly_ < v["rf"][3] and q[2] < v["top"] + 20.0), None)
        if hit:
            cab_bad.append((p["label"], "through", hit))
            break
print("cables:", sum(1 for p in cab_ if "SM_Cable_B_00" in p["asset"]), "bundles,", len(ring_c), "rings; wrong:", len(cab_bad), cab_bad[:12])
bad += len(cab_bad)

# Street lamps (user 2026-11-09: "Street lights are in someones balcony, that cannot happen"): from a lamp's fitting (on its wall or pole) out
# to its light, nothing under the arm: no house, balcony or terrace footprint (the layout's houses, final footprints).
by_label_ = {p["label"]: p for p in items}
lamp_over = []
for p in items:
    if not (p["label"].startswith("Lamp_") and p["asset"].endswith("SM_StreetLamp_02")):
        continue
    li_ = by_label_.get("Light_" + p["label"])
    if li_ is None:
        continue
    for k in range(1, 11):
        u_ = k / 10.0
        lx_, ly_ = to_lay(p["loc"][0] + (li_["loc"][0] - p["loc"][0]) * u_, p["loc"][1] + (li_["loc"][1] - p["loc"][1]) * u_)
        hit = next((h for h, v in houses_.items() if v["rf"][0] < lx_ < v["rf"][2] and v["rf"][1] < ly_ < v["rf"][3]), None)
        if hit:
            lamp_over.append((p["label"], hit))
            break
print("street lamps over a house, balcony or terrace:", len(lamp_over), lamp_over[:12])
bad += len(lamp_over)

# Over a main road (a level's ROAD_CLEAR; user 2026-11-09: "it needs the power cables a bit higher. Trucks should be able to pass through"): no
# wire, laundry line, conduit or cable bundle lower than that over the road panels (story_ground's Road_ planes; not the sidewalks).
road_clear_ = getattr(LEVEL, "ROAD_CLEAR", None)
if road_clear_:
    roads_ = [(p["loc"][0] - abs(p["scale"][0]) * 50, p["loc"][1] - abs(p["scale"][1]) * 50, p["loc"][0] + abs(p["scale"][0]) * 50,
               p["loc"][1] + abs(p["scale"][1]) * 50, p["loc"][2]) for p in by_folder("Ground") if p["label"].startswith("Road_")]
    under_ = []

    def road_low(lab, pts):
        for q in pts:
            r = next((r for r in roads_ if r[0] < q[0] < r[2] and r[1] < q[1] < r[3]), None)
            if r and q[2] - r[4] < road_clear_:
                under_.append((lab, round(q[2] - r[4])))
                return
    for p in by_folder("Wires", "Laundry", "Meters"):
        if p["asset"].split("/")[-1] == "SM_Cube":
            a3, b3 = rod_ends(p)
            road_low(p["label"], [tuple(a3[k] + (b3[k] - a3[k]) * u / 10 for k in range(3)) for u in range(11)])
    for p in cab_:
        if "SM_Cable_B_00" in p["asset"]:
            X_, Y_, Z_ = axes(p)
            s_ = p["scale"]
            a3 = tuple(p["loc"][k] - Y_[k] * 10.0 * s_[1] for k in range(3))
            b3 = tuple(a3[k] + X_[k] * 401.0 * s_[0] for k in range(3))
            sag_ = (45.0 if p["asset"].endswith("B_001") else 18.0) * s_[2]
            road_low(p["label"], [(a3[0] + (b3[0] - a3[0]) * u / 20, a3[1] + (b3[1] - a3[1]) * u / 20,
                                   a3[2] + (b3[2] - a3[2]) * u / 20 - 4 * sag_ * (u / 20) * (1 - u / 20)) for u in range(21)])
    print("under %.0f cm over the main road:" % road_clear_, len(under_), under_[:12])
    bad += len(under_)

print("FAILED" if bad else "clean")
sys.exit(1 if bad else 0)
