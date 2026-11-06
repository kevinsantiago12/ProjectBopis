"""Offline check of the plan's building dressing. User 2026-11-04: "some of your patch placements and vent placements go into the
stairs, theres also a pipe that overlaps with another pipe". Exits 1 if anything fails. Lists:
- dressing on a wall the gallery stairs run against, lower than the stairs' top;
- downpipes closer than PIPE_GAP to each other, or two on one house ("for pipes, never 2 on the same house");
- patches, vents, air conditioners and racks a downpipe runs across, on any block;
- plywood patches with no other beside them ("place atleast 2 beside each other", "except the roof type, the wood one, yes do 2");
- the street dressing (user 2026-11-05: "do all that and add it to the tool"): nothing on a hollow-block face or a thin wall, nothing on the
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
PLAN = os.path.join(ROOT, "Saved", "BackAlleys", "plan3_[0-9]*.json")
LAYOUT = os.path.join(ROOT, "Design Document", "Arena_Slums_Layout.json")
PIPE_GAP = 70.0         # cm between two pipes' centres
STAIR_TOP = 520.0       # the top of the stairs' rails
STAIR_RUN = 7.0         # m: longer than the layout's footprint (gen_level.py STAIR_RUN)
PLATE_W = 162.0         # SM_MetalPlate_A's native width

items = []
for f in sorted(glob.glob(PLAN)):
    items += json.load(open(f, encoding="utf-8"))
L = json.load(open(LAYOUT, encoding="utf-8"))


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
    lx, ly = Y / 100.0 + 27.0, 24.0 - X / 100.0
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
    if t.get("mats") and "HollowBlocks" in t["mats"][0] and p["folder"] != "BackAlleys/Posters":     # posters may: "except hollow block, which yu can put posters on"
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
        lx_, ly_ = (a3[1] + b3[1]) / 200.0 + 27.0, 24.0 - (a3[0] + b3[0]) / 200.0
        d_ = L["deck"]
        if d_["x0"] < lx_ < d_["x1"] and d_["y0"] < ly_ < d_["y1"] or in_stairs((a3[0] + b3[0]) / 2, (a3[1] + b3[1]) / 2):
            low_over_deck.append(p["label"])
    mx, my, mz = (a3[0] + b3[0]) / 2, (a3[1] + b3[1]) / 2, (a3[2] + b3[2]) / 2
    for lab, x0, y0, x1, y1, top in lids:
        if x0 + 3.0 < mx < x1 - 3.0 and y0 + 3.0 < my < y1 - 3.0 and mz < top + 5.0:
            wires_in_house.append((p["label"], lab))
            break
# Signs: long boards only, wide enough for lettering. User: "square signage may fit chinese charachers but not alpha numberics".
short_signs = [p["label"] for p in by_folder("Signs") if not p["asset"].endswith("SM_Sign_A_001") or
               300.0 * abs(p["scale"][0]) < 2.59 * 84.0 * abs(p["scale"][2])]
print("signs that aren't long boards:", len(short_signs), short_signs[:20])
bad += len(short_signs)
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
    s0_, s1_ = {"Plane": (-50.0 * sc_, 50.0 * sc_), "SM_RollupDoor_A_001": (0.0, 190.9 * sc_), "SM_Metal_Gate_01": (0.0, 165.8 * sc_),
                "SM_TarpCover_A_002": (-111.5 * sc_, 111.5 * sc_), "SM_Sign_A_001": (-150.0 * sc_, 150.0 * sc_), "SM_ElectricBox_C_003": (-13.0, 13.0)}[mesh_]
    if c_ + s0_ < lo + FACE_EDGE - 3.0 or c_ + s1_ > hi - FACE_EDGE + 3.0:
        at_edge.append((p["label"], round(min(c_ + s0_ - lo, hi - c_ - s1_))))
print("too near the end of their wall:", len(at_edge), at_edge[:20])
bad += len(at_edge)
print("the same poster twice in a view:", len(near_same), near_same[:20])
bad += len(near_same)
print("posters:", len(posters), "designs:", len({p["mats"][0] for p in posters}))

# Every light beside its fitting.
no_fitting = [p["label"] for p in items if p.get("light") and p["label"].replace("Light_", "", 1) not in all_labels]
print("lights with no fitting:", len(no_fitting), no_fitting[:20])
bad += len(no_fitting)

# Power poles: the shaft on open ground, at least 2.8 m of lane beside it, clear of doors, the gallery and its stairs, awnings and gameplay points.
blocks_ = L["blocks"]
for f_ in glob.glob(os.path.join(ROOT, "Saved", "BackAlleys", "plan3_gameplay.json")):
    gp_ = json.load(open(f_, encoding="utf-8"))
keep_ = [tuple(s_["loc"][:2]) for s_ in gp_["spawns"]] + [tuple(w_["loc"][:2]) for w_ in gp_["wander"]] + [tuple(gp_["player_start"][:2])]


def on_block(X, Y):
    lx, ly = Y / 100.0 + 27.0, 24.0 - X / 100.0
    return not (0 < lx < L["arena"][0] and 0 < ly < L["arena"][1]) or any(b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] for b in blocks_)


poles = [p for p in by_folder("Poles") if "SM_Electric_Pole" in p["asset"]]
pole_bad = []
doors_ = [d_ for d_ in items if d_["asset"].endswith("SM_WallDoor_01") and d_["loc"][2] < 100.0]
for p in poles:
    x, y = p["loc"][0], p["loc"][1]
    lx, ly = y / 100.0 + 27.0, 24.0 - x / 100.0
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
quarters = {(x_ > 0.0, y_ > 0.0) for x_, y_ in water_lots.values()}
print("water meter lots:", len(water_lots), "too close:", len(near_lots), near_lots[:20], "quarters with some:", len(quarters))
bad += len(near_lots) + (4 - len(quarters))
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

print("FAILED" if bad else "clean")
sys.exit(1 if bad else 0)
