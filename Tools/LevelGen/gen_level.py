"""Lvl_BackAlleys, all-alley layout (Design Document/Arena_Slums_Layout.json, from the "Arena Level Design: Slums"
session; user: "remove the court, make it exclusively alleys"; "remove the grenade launcher"). Writes
Saved/BackAlleys/plan3_*.json.

Usage (from the project root): python Tools/LevelGen/gen_level.py [layout.json]. See README.md.

Blocks tile the solid area and touch their neighbours, so walls go per storey, on every 1.5 m cell of a block side
whose outside is open at that storey (open = inside the arena and not inside a block that tall). That covers a
2-storey block's upper floor above a 1-storey neighbour. Every coordinate is a multiple of 1.5 m, so runs fill exactly
with 3 m modules and 1.5 m halves. Layout metres: lx east, ly south, NW corner; Unreal: X = (24 - ly) * 100,
Y = (lx - 27) * 100."""
import json
import math
import os
import random
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
SRC = sys.argv[1] if len(sys.argv) > 1 else os.path.join(ROOT, "Design Document", "Arena_Slums_Layout.json")
OUT = os.path.join(ROOT, "Saved", "BackAlleys") + os.sep
os.makedirs(OUT, exist_ok=True)
AS, ME, PM = "/Game/AsiaSlum/FBX/", "/Game/Megapack/Meshes/", "/Game/Philippines_Markets/Props/"
CUBE = "/Game/LevelPrototyping/Meshes/SM_Cube"
RAMP = "/Game/LevelPrototyping/Meshes/SM_Ramp"   # min-corner pivot; 1 m tall at local y = 0, falling to 0 at y = 1 m
PK ="/Game/ThirdPerson/Blueprints/Pickups/"
L = json.load(open(SRC))
W, H = L["arena"]
BLOCKS = {b["id"]: b for b in L["blocks"]}
# --- Houses: long blocks split into a row of separate houses ------------------------------------------------------------
# User 2026-11-03 (a photo of a Philippine back street): "most philippine houses still use metal roofs even in stone
# houses. They also vary in height, is not consistently aligned with each other on the street, and 1 storey houses with
# currogated roof exists as well" ... "All four at once". A block >= 9 m long becomes a row of houses 4.5-7.5 m wide
# along its long axis (on the 1.5 m grid, each the block's full depth). Each house then gets its own storeys, storey
# height, setbacks and roof (below, after the balconies). The layout JSON (design canon) is not changed.
HOUSE_RNG = random.Random(71)    # its own sequence
HOUSE_W = (4.5, 6.0, 7.5)
NO_SPLIT = ("B2", "B10", "B11")  # the shop row, the 1.5 m stub, the gallery-deck block
_houses = {}
for _bid, _b in BLOCKS.items():
    _along_x = _b["x1"] - _b["x0"] >= _b["y1"] - _b["y0"]
    _a0, _a1 = (_b["x0"], _b["x1"]) if _along_x else (_b["y0"], _b["y1"])
    if _bid in NO_SPLIT or _a1 - _a0 < 9.0:
        _houses[_bid] = _b
        continue
    _cuts = [_a0]
    while _a1 - _cuts[-1] > 7.5:
        _cuts.append(_cuts[-1] + HOUSE_RNG.choice([w for w in HOUSE_W if _a1 - _cuts[-1] - w >= 4.5]))
    _cuts.append(_a1)
    for _k, (_c0, _c1) in enumerate(zip(_cuts, _cuts[1:])):
        _h = dict(_b, id="%sh%d" % (_bid, _k + 1))
        _h.update({"x0": _c0, "x1": _c1} if _along_x else {"y0": _c0, "y1": _c1})
        _houses[_h["id"]] = _h
BLOCKS = _houses
rnd = random.Random(11)
items = []
# Standing rule (user 2026-11-03): "forget all the dressings and, just make the building block outs. No other objects in
# the level besides building blockouts as a rule." Asked what else stays: the gameplay actors and the gallery deck +
# stairs. So cover (stand-ins, kiosk, barriers, drums), pickups, dressing and decals are off. The code for them stays
# behind these switches; turn one on only when the user asks for it.
COVER = False
PICKUPS = False
DRESSING = False
TERRACES = True   # user 2026-11-03: "Yes, build them" - covered roof terraces on the 1-storey blocks
STAINS = True     # user 2026-11-03: "I want stain decals next"; "forget the decals completely"; then "actually, bring it
#                   back but use decal dirt 8" - on, with MI_Decal_Dirt_08


def ue(lx, ly):
    return (24.0 - ly) * 100.0, (lx - 27.0) * 100.0


YAW = {"east": 0, "west": 180, "north": -90, "south": 90}
RUN = {"east": (1, 0), "west": (-1, 0), "north": (0, -1), "south": (0, 1)}     # UE
NORMAL = {"east": (0, 1), "west": (0, -1), "north": (1, 0), "south": (-1, 0)}  # UE
LNORM = {"east": (1, 0), "west": (-1, 0), "north": (0, -1), "south": (0, 1)}   # layout
FACING = {"east": 90, "west": -90, "north": 0, "south": 180}
FACE = {"S": "south", "N": "north", "E": "east", "W": "west"}


def put(label, asset, x, y, z, yaw=0.0, scale=(1, 1, 1), folder="BackAlleys", roll=0.0, nocoll=False, mat=None,
        vol=False, mats=None, decal=False):
    """mat: "interior" or "hidden" (special cases); mats: material paths per slot, as overrides; decal: asset is the
    decal material and a DecalActor is placed."""
    items.append({"label": label, "asset": asset, "loc": [round(x, 1), round(y, 1), round(z, 1)],
                  "rot": [0.0, float(yaw), float(roll)], "scale": [round(s, 4) for s in scale], "folder": folder,
                  "nocoll": nocoll, "mat": mat, "vol": vol, "mats": mats, "decal": decal})


def solid(lx, ly, s):
    if lx <= 0 or lx >= W or ly <= 0 or ly >= H:
        return True
    return any(b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] and b["storeys"] > s for b in BLOCKS.values())


# --- Balconies: upper storeys stepped back ----------------------------------------------------------------------------
# User 2026-11-03: "replace some of the block's second story as balconies instead". As Favela's stepped-back top floors:
# on a few 2-storey blocks, a BALCONY_D strip along one face loses its upper storey and becomes a covered balcony on
# the ground floor's roof (the terrace builder below: parapet, corrugated sheets, plank frame). The upper wall behind it
# gets doors and windows onto it. Only the generator's blocks change; the layout JSON (design canon) does not.
# A face qualifies when it is open along its whole length at both storeys, is >= 6 m long, the block is >= 4.5 m deep
# behind it, and it is not B2 (the shop fronts) or B11 (the gallery deck). One face per block.
BALCONIES = 6
BALCONY_D = 1.5
BALCONY_RNG = random.Random(23)   # its own sequence, so the choice doesn't shift the rest of the generator's randoms


def _face_open(b, side, s):
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    if side in ("north", "south"):
        ly = y0 - 0.75 if side == "north" else y1 + 0.75
        return all(not solid(x0 + (k + 0.5) * 1.5, ly, s) for k in range(int(round((x1 - x0) / 1.5))))
    lx = x0 - 0.75 if side == "west" else x1 + 0.75
    return all(not solid(lx, y0 + (k + 0.5) * 1.5, s) for k in range(int(round((y1 - y0) / 1.5))))


# Wide roof terraces (user 2026-11-03, with a reference picture: "the balcony you have is an extension on the
# building, we can use this, but what I really want is this", then "cut off the second story section completely and
# build on it"): on WIDE_TERRACES blocks >= 6 m deep, the upper storey's half along one face (on the 1.5 m grid, >= 3 m)
# is cut off and becomes an open roof terrace; the other half keeps its upper storey as the taller wall behind. The
# narrow 1.5 m balconies (the "extension", kept) go on other blocks.
WIDE_TERRACES = 4


def _cands(min_dep):
    out = []
    for bid, b in BLOCKS.items():
        if b["storeys"] != 2 or bid in ("B2", "B11"):
            continue
        for side in ("north", "south", "west", "east"):
            ln = (b["x1"] - b["x0"]) if side in ("north", "south") else (b["y1"] - b["y0"])
            dep = (b["y1"] - b["y0"]) if side in ("north", "south") else (b["x1"] - b["x0"])
            if ln >= 6.0 and dep >= min_dep and _face_open(b, side, 0) and _face_open(b, side, 1):
                out.append((bid, side, dep))
    BALCONY_RNG.shuffle(out)
    return out


BALCONY_FACES = []   # (block, side, strip depth)
for _bid, _side, _dep in _cands(6.0):
    if len(BALCONY_FACES) < WIDE_TERRACES and _bid not in [f[0] for f in BALCONY_FACES]:
        BALCONY_FACES.append((_bid, _side, max(3.0, math.floor(_dep / 2 / 1.5) * 1.5)))
_n_wide = len(BALCONY_FACES)
for _bid, _side, _dep in _cands(4.5):
    if len(BALCONY_FACES) < _n_wide + BALCONIES and _bid not in [f[0] for f in BALCONY_FACES]:
        BALCONY_FACES.append((_bid, _side, BALCONY_D))
for _bid, _side, _d in BALCONY_FACES:
    _b = BLOCKS[_bid]
    _strip = dict(_b, id=_bid + "b", storeys=1, balcony=_side)
    if _side == "north":
        _strip["y1"] = _b["y0"] + _d
        _b["y0"] += _d
    elif _side == "south":
        _strip["y0"] = _b["y1"] - _d
        _b["y1"] -= _d
    elif _side == "west":
        _strip["x1"] = _b["x0"] + _d
        _b["x0"] += _d
    else:
        _strip["x0"] = _b["x1"] - _d
        _b["x1"] -= _d
    BLOCKS[_strip["id"]] = _strip
print("balconies / terraces:", BALCONY_FACES)


def balcony_at(lx, ly):
    """True if (lx, ly) is on a balcony strip."""
    return any(b.get("balcony") and b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] for b in BLOCKS.values())


# --- Per house: storeys, storey height, setbacks, roof (see "Houses" above) ----------------------------------------------
# Fixed houses keep the layout's storeys, 4 m storey height and walls: those the gallery deck or a stair touches, those
# within reach of a spawn door's end wall (it is 2 storeys of 4 m and runs 1.1 m into the blocks either side), the shop
# row and the 1.5 m stub. Free houses: storey height 3.4-4.2 m; some 2-storey houses become 1-storey corrugated-roof
# houses (never at the arena edge - the arena's outer wall is its edge houses) and some get a third storey; street
# faces are set back 0, 0.3 or 0.6 m, inward only, so no alley gets narrower than the layout. Balcony parents and their
# strips keep their footprint and storeys (their terraces are built against them); the strip follows the parent's height.
STOREY_H = (340.0, 360.0, 380.0, 400.0, 420.0)   # cm
SHACK_H = (330.0, 350.0, 370.0)                   # 1-storey corrugated-roof houses
SHACKS, P_THIRD, P_FLAT = 4, 0.4, 0.1          # P_FLAT: houses keeping a flat concrete roof ("most" have metal)
SETBACKS = (0.0, 0.0, 0.3, 0.6)                    # m, per open street face
FIX_RNG = random.Random(73)


def _near(b, r, pad):
    return b["x0"] < r["x1"] + pad and r["x0"] - pad < b["x1"] and b["y0"] < r["y1"] + pad and r["y0"] - pad < b["y1"]


def _fixed(b):
    if b["id"] in NO_SPLIT or _near(b, L["deck"], 0.05) or any(_near(b, s, 0.05) for s in L["stairs"]):
        return True
    return any(_near(b, {"x0": d["x"], "x1": d["x"], "y0": d["y"], "y1": d["y"]}, 5.0) for d in L["doors"])


_parents = {f[0] for f in BALCONY_FACES}


def _inner(b):
    return not (b["x0"] <= 0 or b["y0"] <= 0 or b["x1"] >= W or b["y1"] >= H)


# The 1-storey corrugated-roof houses: SHACKS of the free, inner (not on the arena edge), 2-storey, non-balcony houses.
_shacks = set(FIX_RNG.sample(sorted(b["id"] for b in BLOCKS.values() if not _fixed(b) and _inner(b) and
                                    b["storeys"] == 2 and b["id"] not in _parents and not b.get("balcony")), SHACKS))
for _b in BLOCKS.values():
    _b["sh"], _b["fixed"] = 400.0, _fixed(_b)
    _strip = _b["id"].endswith("b") and _b.get("balcony")
    if _b["fixed"] or _strip:
        continue
    if _b["id"] in _shacks:
        _b["storeys"], _b["shack"], _b["sh"] = 1, True, FIX_RNG.choice(SHACK_H)
        continue
    if _b["storeys"] == 2 and _b["id"] not in _parents and FIX_RNG.random() < P_THIRD:
        _b["storeys"] = 3
    _b["sh"] = FIX_RNG.choice(STOREY_H)
for _b in BLOCKS.values():
    if _b["id"].endswith("b") and _b.get("balcony"):
        _b["sh"] = BLOCKS[_b["id"][:-1]]["sh"]
    # A 1-storey house of the layout (and every balcony strip) keeps its covered roof terrace; the rest get metal roofs.
    _b["roof"] = "terrace" if _b["storeys"] == 1 and not _b.get("shack") else \
        ("flat" if FIX_RNG.random() < P_FLAT else "metal")
_cuts = []   # setbacks: decided on the unmoved footprints, then applied
for _b in BLOCKS.values():
    if _b["fixed"] or _b["roof"] == "terrace" or _b["id"] in _parents:
        continue
    for _side in ("north", "south", "west", "east"):
        _d = FIX_RNG.choice(SETBACKS)
        if _d and _face_open(_b, _side, 0):
            _cuts.append((_b, _side, _d))
for _b, _side, _d in _cuts:
    _key = {"north": "y0", "south": "y1", "west": "x0", "east": "x1"}[_side]
    _span = (_b["y1"] - _b["y0"]) if _side in ("north", "south") else (_b["x1"] - _b["x0"])
    if _span - _d >= 3.0:
        _b[_key] += _d if _side in ("north", "west") else -_d
        _b.setdefault("setback", {})[_side] = _d
print("houses:", len(BLOCKS), "| 3-storey", sum(b["storeys"] == 3 for b in BLOCKS.values()),
      "| 1-storey metal", sum(bool(b.get("shack")) for b in BLOCKS.values()),
      "| flat", sum(b["roof"] == "flat" for b in BLOCKS.values()), "| setbacks", len(_cuts))


def cover_top(lx, ly, me=None):
    """Height (cm) of the tallest house over (lx, ly) other than `me`: 0 for open ground, huge outside the arena."""
    if lx <= 0 or lx >= W or ly <= 0 or ly >= H:
        return 1e9
    return max([b["storeys"] * b["sh"] for b in BLOCKS.values()
                if b is not me and b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"]] or [0.0])


def side_intervals(b, side, test):
    """Split one side of house b where other houses' edges (and the arena edge) cross it; for each piece, test(c) with
    c = cover_top 5 cm outside its middle. Returns [(t0, t1, result)] in metres from the side's min corner."""
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    p0 = {"north": (x0, y0), "south": (x0, y1), "west": (x0, y0), "east": (x1, y0)}[side]
    along_x = side in ("north", "south")
    length = (x1 - x0) if along_x else (y1 - y0)
    ts = {0.0, length}
    for o in list(BLOCKS.values()) + [{"x0": 0.0, "x1": W, "y0": 0.0, "y1": H}]:
        for v in ((o["x0"], o["x1"]) if along_x else (o["y0"], o["y1"])):
            t = v - (p0[0] if along_x else p0[1])
            if 0 < t < length:
                ts.add(round(t, 4))
    ts = sorted(ts)
    nlx, nly = LNORM[side]
    out = []
    for ta, tb in zip(ts, ts[1:]):
        if tb - ta < 0.01:
            continue
        tm = (ta + tb) / 2
        lx, ly = (p0[0] + tm, p0[1]) if along_x else (p0[0], p0[1] + tm)
        res = test(cover_top(lx + nlx * 0.05, ly + nly * 0.05, b))
        if out and abs(out[-1][1] - ta) < 1e-6 and out[-1][2] == res:
            out[-1] = (out[-1][0], tb, res)
        else:
            out.append((ta, tb, res))
    return out


# --- Walls ----------------------------------------------------------------------------------------------------------
# Favela kit (user 2026-11-03: "Favela walls, 4 m storeys"; patterns in Tools/LevelGen/LESSONS.md). A storey is a 3 m
# wall tile, a 1 m concrete band (the floor beam, or the parapet on the top storey) and a trim over the seam between
# them, with a second trim capping the top. Tiles are 2.25 m (half 1.125 m), stretched to fit each run exactly, as
# Favela does. Shop fronts on B2 keep the AsiaSlum pieces (3 m modules, 4 m tall).
FV = ME + "Favela/"
FM = "/Game/Megapack/Material/Favela/"
GLASS = "/Game/AsiaSlum/Material/MI_Glass_A_001"           # opaque since 2026-11-02; replaces the additive glass slots
# User 2026-11-03: "use mostly the concrete material"; "red brick walls... need to be non-red hollow blocks".
# Our materials (Tools/LevelGen/create_materials_ue.py) swap Favela's red brick for MiddleEast's grey blocks.
# User: "Make a CHB material" -> M_BackAlleys_CHB (Tools/LevelGen/create_chb_material_ue.py): procedural 40 x 20 cm
# hollow blocks in world space, optionally under a chipped concrete or paint render. All ours, no pack materials.
BM = "/Game/ThirdPerson/BackAlleys/Materials/"
# Picked once per block face (see favela_run): mostly concrete, some bare hollow block, a few paint accents.
# Picked per block face and storey (see the block loop). User 2026-11-03: "make more variant colors of
# MI_BackAlleys_CHB" -> concrete still leads (0.5), bare blocks 0.15, and 13 paint colours share 0.35.
PAINTS = ["White", "Yellow", "Blue", "Mint", "Pink", "SkyBlue", "Cream", "Peach", "Lime", "Lavender", "Teal", "Salmon",
          "PaleYellow"]
FACE_MATS = ([(BM + "MI_BackAlleys_CHB_Concrete", 0.24), (BM + "MI_BackAlleys_Concrete", 0.1),
              (BM + "MI_BackAlleys_CHB_ConcreteWarm", 0.08), (BM + "MI_BackAlleys_CHB_ConcreteDark", 0.08),
              (BM + "MI_BackAlleys_CHB_Bare", 0.07), (BM + "MI_BackAlleys_CHB_BareLight", 0.04),
              (BM + "MI_BackAlleys_CHB_BareDark", 0.04)] +
             [(BM + "MI_BackAlleys_CHB_Paint" + c, 0.35 / len(PAINTS)) for c in PAINTS])
SAME_AS_GROUND = 0.4      # chance an upper storey keeps the ground floor's material
# User 2026-11-03: "remove the material variation I asked you to do earlier" - asked which, "All of it: one material".
# Every wall face and storey uses WALL_MAT; the picks above still run (so the random sequence, and with it the window
# layout, stays the same) but their result is replaced. Set ONE_MATERIAL = False to bring the variation back.
ONE_MATERIAL = True
WALL_MAT = BM + "MI_BackAlleys_CHB_Concrete"
# Hollow blocks. User 2026-11-03: "only use them on walls with no windows or doors. They are not to be used for whole
# houses", "the only mixing rule is not to mix on the same face", and "make it 30% of windowless faces, following the
# rules still". A face is one side of a house, all its storeys, with its balcony strip's same side. A face with no door or
# window anywhere is hollow blocks P_HOLLOW of the time (see the pass before the chunks); everything else is WALL_MAT.
# Neighbouring faces may differ. Replaces the per-face-and-storey mixes and the per-house rule of the same day. Bands,
# parapets and columns stay concrete. Its own random sequence, so windows and doors don't move. (The texture sits on the
# Favela tiles' UV0, so it stretches with tile X scale.)
HOLLOW = BM + "MI_BackAlleys_HollowBlocks"
P_HOLLOW = 0.30
WALL_MIX_RNG = random.Random(107)   # 16 of 52 windowless faces (of seeds tried, the closest to 30%)
PLAIN_WALL = ("SM_Wall_Tile_01", "SM_Wall_Tile_Blue", "SM_Wall_Tile_03", "SM_Wall_14", "SM_MainBorder_04")
# Paint. User 2026-11-04: "One color per house, but some side can remain unpainted". P_PAINTED of the houses take one
# colour (MI_BackAlleys_PaintedWall_*, world-mapped, from the AssetGen thread). A face with a door or window always takes
# it; a windowless one takes it P_PAINT_SIDE of the time; hollow-block faces stay as they are. A face never mixes. Bands
# match the paint (user: "when the face is painted, the band looks off if left unpainted. It works for hollow blocks but
# not for painted"; P_BAND_CONTRAST, once 0.2 for variety, is off). Parapets follow
# their face, and a corner column takes the colour when both its faces have it. The door end walls, trims and timber
# don't change. The drip decals stay, over the paint.
PAINT_COLOURS = ("White", "Cream", "Yellow", "Peach", "Salmon", "Pink", "Mint", "AppleGreen", "SkyBlue", "Teal",
                 "Lavender", "Terracotta")
P_PAINTED, P_PAINT_SIDE = 0.5, 0.5
P_BAND_CONTRAST = 0.0
BAND_MIX_RNG = random.Random(137)
PAINT_RNG = random.Random(103)    # 21 of 41 houses (of seeds tried, the closest to half)
CONC = BM + "MI_BackAlleys_Concrete"
DOORS = [(FV + "SM_Door_01", FM + "MI_Door_01"), (FV + "SM_Door_01_Blue", FM + "MI_Door_Blue_01"),
         (FV + "SM_Door_01_Green", FM + "MI_Door_Green_01")]
# The user's five back-alley door textures (create_doors_ue.py), on planes in the wall door slots. Own random sequence.
PLANE_DOORS = ["MI_BackAlleys_Door_" + k for k in
               ("RoughTimber", "GreenPlywood", "BluePlywood", "CorrugatedMetal", "PaintedSteel")]
DOOR_RNG = random.Random(61)
# AsiaSlum steel doors fitted to the slot: local bounds (analysis/door_bounds_ue.py) and whether to turn them 180 so the
# hinges end up on the right seen from the alley ("right hand open") and inside ("make sure the hinges are on the
# inside"). B_003 (louvred, alone) already shows its hinges on the right; the grilles A_002/A_004/A_005 go in front of
# a plane door ("use that along with the metal doors in asian slums like so" ... "for doors 2 4 and 5").
STEEL_DOORS = {"SM_HouseDoor_B_003": ((-112.6, -8.9, 0.0), (2.3, 3.6, 228.0), False),
               "SM_HouseDoor_A_002": ((-114.2, -10.2, 5.2), (1.8, 4.2, 240.5), True),
               "SM_HouseDoor_A_004": ((-114.2, -10.2, 5.2), (1.8, 4.9, 240.5), True),
               "SM_HouseDoor_A_005": ((-160.0, -10.2, 0.0), (2.5, 4.9, 329.6), True)}
GRILLES = ["SM_HouseDoor_A_002", "SM_HouseDoor_A_004", "SM_HouseDoor_A_005"]
P_GRILLE = 0.5                                           # share of plane doors behind a grille
PLANE_HINGE_RIGHT = True                                 # the textures paint the hinges on the left: mirror them
TILE_W, HALF_W = 225.0, 112.5
TILE_LAP = 0.4                                              # cm; more than the plan's rounding, under 1 cm (check_overlaps)
HALF_MAX = 170.0                                            # narrower than this: the half tile, stretched
P_GROUND = {"door": 0.12, "window": 0.25}   # Favela: 12% doors, 9% windows; user 2026-11-03 "increase the number of windows"
P_UPPER = {"window": 0.40}                  # Favela 13%, raised (same request); no doors without a balcony
SPECIAL = {("B2", "south", 0): ["SM_Shop_A_001", "SM_HouseWindow_A_001", "SM_Shop_A_001", "SM_HouseWallDoorFrmae_A_002"]}
DECK_FACE = ("B11", "south", 1)                             # doors and windows onto the gallery deck, alternating
DOOR_FRAMES = ("SM_HouseWallDoorFrmae_A_001", "SM_HouseWallDoorFrmae_A_002")
DECALS = {"grime": [FM + "Decals/MI_Decal_02", FM + "Decals/MI_Decal_05", FM + "Decals/MI_Decal_08"],
          "dirt": [FM + "Decals/MI_Decal_Dirt_06", FM + "Decals/MI_Decal_Dirt_08"]}
DECAL_CAP = 200
BLK = "BackAlleys/Blocks"
ground_pieces, upper_runs, exposed_sides, wall_tiles = [], [], {}, []
wall_runs = []   # every visible wall run per storey: start (UE), length cm, side, base z; the stain decals cover these


def pick(weighted):
    r, acc = rnd.random(), 0.0
    if ONE_MATERIAL and weighted is FACE_MATS:
        return WALL_MAT                    # hollow blocks are chosen after the walls are built
    for v, w in weighted:
        acc += w
        if r < acc:
            return v
    return weighted[-1][0]


def at(px, py, side, s, n):
    """World point s cm along a piece's run and n cm along its outward normal."""
    (rx, ry), (nx, ny) = RUN[side], NORMAL[side]
    return px + rx * s + nx * n, py + ry * s + ny * n


def door_for(label, mesh, px, py, z, normal, folder):
    if mesh in DOOR_FRAMES:  # the AsiaSlum pack's own offset: frame-local (205, 5, 0)
        x, y = at(px, py, normal, 205, 5)
        put(label + "_Door", AS + "SM_HouseDoor_B_003", x, y, z, YAW[normal], folder=folder)   # (user: replaces A_004)


def thin(b):
    if b.get("balcony"):
        return False   # a balcony strip's street wall keeps its doors and windows
    return min(b["x1"] - b["x0"], b["y1"] - b["y0"]) <= 1.5 or b["id"] == "B10"


def fit(length_cm):
    """Half-tile count and stretch for a run: the count whose stretch is closest to 1 (Favela uses 0.82-1.29)."""
    u = length_cm / HALF_W
    h = min((k for k in (math.floor(u), math.ceil(u)) if k >= 1), key=lambda k: abs(math.log(u / k)))
    return h, u / h


# Window style per house (user 2026-11-03: "you can also use the old window as well, but make sure they are consistent
# house wise. IE all jalouse or all pull windows"): each block - its balcony/terrace strip ("<id>b") included - gets
# either the jalousie plane or Favela's SM_windows_02 insert on every window. Own random sequence, so nothing else moves.
WINDOW_JALOUSIE_SHARE = 0.5
WINDOW_RNG = random.Random(53)
_window_styles = {}


def shuffle_bag(rng, options):
    """Draws evenly from options in no fixed order: a shuffled bag, refilled when empty, never the same twice running.
    User 2026-11-04: "we are trying to have patterns in building but have the player not see patterns when playing"."""
    bag, last = [], [None]

    def draw():
        if not bag:
            bag.extend(rng.sample(list(options), len(options)))
            if bag[-1] == last[0]:
                bag[0], bag[-1] = bag[-1], bag[0]
        last[0] = bag.pop()
        return last[0]
    return draw


# Window grilles on the ground floor. User 2026-11-04: "find an appropriate window grill and put it in the first floor
# windows", "more variation is appreciated". One kind per house, so neighbours differ and a house matches itself. Fitted to
# the opening (112 x 128 cm, x the tile's stretch, centred 112 along and 156 up) with 5 cm on the wall around it, just off
# the face. Mesh: (local min, local max, the local axis it runs along, depth cm). No collision: they're thin and cheap.
WIN_GRILLES = {FV + "SM_Window_Frame_02": ((-109.9, -7.5, 0.0), (0.0, 0.0, 159.8), "x", 8.0),      # green steel bars
               ME + "MiddleEast/SM_Windows_grill_01": ((-0.5, 0.0, -0.5), (313.8, 11.6, 238.1), "x", 8.0),   # olive bars
               ME + "MiddleEast/SM_Windows_grill_02": ((-0.5, 0.0, -0.5), (313.8, 11.6, 238.1), "x", 8.0),   # dark grid
               ME + "MiddleEast/SM_metal_fence_01": ((5.6, -133.5, -0.5), (11.6, 0.5, 117.0), "y", 6.0),     # sparse bars
               AS + "SM_SecurityWinodw_A_001": ((-106.1, 2.7, -93.0), (106.1, 40.6, 93.2), "x", 14.0)}       # rusty, on brackets
_draw_grille = shuffle_bag(random.Random(127), sorted(WIN_GRILLES))
GRILLE_W, GRILLE_H, GRILLE_Z, GRILLE_OUT = 122.0, 138.0, 87.0, 0.5
BAND_OUT = 15.0
BAND_RNG = random.Random(131)
_house_grilles = {}


def window_grille(label, px, py, z, side, sx, folder):
    house = label.split("_")[0]
    house = house[:-1] if house.endswith("b") and house[:-1] in BLOCKS else house
    if house not in _house_grilles:                # a bag: a plain random pick came out 15 / 10 / 7 / 3 / 2
        _house_grilles[house] = _draw_grille()
    mesh = _house_grilles[house]
    (x0, y0, z0), (x1, y1, z1), axis, depth = WIN_GRILLES[mesh]
    w, s0 = GRILLE_W * sx, (112.0 - GRILLE_W / 2) * sx
    sz = GRILLE_H / (z1 - z0)
    if axis == "x":                                # local X along the run, local +Y outward
        sa, sd = w / (x1 - x0), depth / (y1 - y0)
        x, y = at(px, py, side, s0 - x0 * sa, GRILLE_OUT - y0 * sd)
        yaw_, scale = YAW[side], (sa, sd, sz)
    else:                                          # local Y along the run, local X inward (turned 90 less, as the bands)
        sa, sd = w / (y1 - y0), depth / (x1 - x0)
        x, y = at(px, py, side, s0 - y0 * sa, GRILLE_OUT + x1 * sd)
        yaw_, scale = YAW[side] - 90, (sd, sa, sz)
    put(label + "_Grill", mesh, x, y, z + GRILLE_Z - z0 * sz, yaw_, scale, folder=folder, nocoll=True)


def window_style(label):
    house = label.split("_")[0].rstrip("b")
    if house not in _window_styles:
        _window_styles[house] = "jalousie" if WINDOW_RNG.random() < WINDOW_JALOUSIE_SHARE else "insert"
    return _window_styles[house]


def steel_door(label, mesh, px, py, z, side, sx, front, folder):
    """An AsiaSlum steel door scaled to the Favela door slot (110 x 218 cm x the tile's stretch, centred 111 cm along),
    its front face `front` cm into the wall. Pivots sit at a bottom corner with the mesh along local -X and the outer
    face on local +Y. Turned ones (user 2026-11-03: "Turn the grilles", hinges to the inside) spin 180 and mirror
    along the run, so the hinges move to the inside face but stay on the right (right-hand). Returns the back face depth."""
    (x0, y0, z0), (x1, y1, z1), turn = STEEL_DOORS[mesh]
    sdx, sdz = 110.0 * sx / (x1 - x0), 218.0 / (z1 - z0)
    cx, cy, half = (x0 + x1) / 2 * sdx, (y0 + y1) / 2 * sdz, (y1 - y0) / 2 * sdz
    out = -(front + half)                                # bounds centre, outward from the wall face
    s = -1 if turn else 1                                # turned: local +Y points into the wall, local X still along
    x, y = at(px, py, side, 111 * sx - cx, out - s * cy)
    put(label, AS + mesh, x, y, z + 2 - z0 * sdz, YAW[side] + (180 if turn else 0), (s * sdx, sdz, sdz),
        folder=folder)
    return front + 2 * half


def favela_tile(label, kind, mat, px, py, z, side, sx, width, top, folder, t0=0.0, t1=0.0, sh=400.0, cover=0.0,
                j0=None, j1=None):
    """One storey of one tile: wall tile, opening parts, concrete band, trims. Pivot at the run start, bottom.
    t0/t1 lengthen the trims past the tile's start/end (outside corners, see corner_adjust). sh: storey height (cm) -
    the 3 m tile stays, the band above it takes the rest."""
    yaw = YAW[side]
    mesh = {"door": "SM_WallDoor_01", "window": "SM_Wall_Windows_01"}.get(kind) or \
        ("SM_Wall_Tile_03" if width < HALF_MAX else rnd.choice(("SM_Wall_Tile_Blue", "SM_Wall_Tile_01")))
    # SM_Wall_Tile_03 (the half tile) has two material slots; the second showed the pack's brick at corners (user
    # 2026-11-03 screenshot), so every slot gets the face material.
    # Each tile runs TILE_LAP past its slot, under the next one. Since houses left the 1.5 m grid (fractional widths),
    # plan rounding left gaps of up to 0.08 cm between tiles, seen as dark hairlines (user 2026-11-04: "seams on the
    # walls"). Half tile: its mesh is 112.5 wide; this was 113, which left it 0.5 cm short.
    put(label, FV + mesh, px, py, z, yaw, ((width + TILE_LAP) / (HALF_W if width < HALF_MAX else TILE_W), 1, 1),
        folder=folder,
        mats=[mat, mat] if mesh == "SM_Wall_Tile_03" else [mat])
    if kind == "door":
        # User 2026-11-03: "Heres a zip of 5 backalley "plane" doors" ... "get them in the game" (replacing the
        # SM_HouseDoor_B_003 mesh). The opening is what Favela's SM_Door_Jamb_01 filled: 110 x 218 cm (x the tile's
        # stretch), centred 111 cm along - the textures are 1:2 with their own frame, so the plane fills it exactly,
        # 2 cm in like the jalousie windows, set the same way (engine plane, roll +90). One of the five per door.
        rnd.choice(DOORS)                                   # keeps the random sequence (and the layout) as before
        door = DOOR_RNG.choice(PLANE_DOORS + [None])
        # User 2026-11-03: plane doors, some behind an AsiaSlum steel grille (A_002/004/005, the user's screenshot);
        # "you can still use the original door by itself" - None is the louvred SM_HouseDoor_B_003 alone.
        if door is None:
            steel_door(label + "_Door", "SM_HouseDoor_B_003", px, py, z, side, sx, 3.0, folder)
        else:
            depth = 2.0
            if DOOR_RNG.random() < P_GRILLE:
                depth = steel_door(label + "_Grille", DOOR_RNG.choice(GRILLES), px, py, z, side, sx, 2.0, folder) + 1
            x, y = at(px, py, side, 111 * sx, -depth)
            put(label + "_Door", "/Engine/BasicShapes/Plane", x, y, z + 109, yaw,
                ((-1.10 if PLANE_HINGE_RIGHT else 1.10) * sx, 2.18, 1), folder=folder, roll=90.0, mats=[BM + door])
    elif kind == "window":
        # User 2026-11-03: "Heres a Jalouse window texture, can you put it on a plane and use this instead of the mesh
        # window?" - the engine plane (1 x 1 m, facing +Z) with M_BackAlleys_Jalousie, in place of SM_windows_02: the
        # old insert's size (1.10 x 1.33 m) and centre (111 along, 0.9-2.2 m up), set 2 cm into the opening. Roll +90
        # stands it up facing out, so it shows from the alley only (-90 faced it into the wall: the user, "its facing
        # the wrong way", "flip it vertically 180 degrees"; checked in a capture).
        # 2 cm in, nearly flush (user: "push the windows more out, i can see some texture anomalies" - at 9 cm deep the
        # opening's sill showed, and the world-aligned wall material smears on horizontal faces)
        if window_style(label) == "jalousie":
            x, y = at(px, py, side, 111 * sx, -2)
            put(label + "_Win", "/Engine/BasicShapes/Plane", x, y, z + 90 + 66.5, yaw, (1.10 * sx, 1.33, 1),
                folder=folder, roll=90.0, mats=[BM + "MI_BackAlleys_JalousieDouble"])   # user: "Replace with this textures"
        else:   # Favela's own insert, where Favela puts it: 111 along, 11 in, 90 up, turned 180 (its frame covers the sill)
            x, y = at(px, py, side, 111 * sx, -11)
            put(label + "_Win", FV + "SM_windows_02", x, y, z + 90, yaw + 180, (sx, 1, 1), folder=folder,
                mats=[FM + "MI_Window_02", GLASS])
        if z == 0:
            window_grille(label, px, py, z, side, sx, folder)
    # Band: SM_Wall_14 runs along its local +Y with its thickness on local +X, so it turns 90 less than the tile.
    # Plain concrete here; the paint pass may recolour it (see P_BAND_CONTRAST).
    put(label + "_Band", FV + "SM_Wall_14", px, py, z + 300, yaw - 90,
        (1, (width + TILE_LAP) / 200.0, (sh - 300) / 106.0), folder=folder, mats=[CONC])
    items[-1]["band"] = (side, px, py, width, t0, t1, sh)     # for the protruding bands, in the pass before the chunks
    for zz in ((300, sh) if top else (300,)):
        if z + zz + 20 <= cover:   # inside the lower neighbour in front: it would only cross that house's trims
            continue
        # at a junction (see the wall loop): stop 17 cm short if the lower house's walls reach this trim's height
        e0 = t0 if j0 is None else (-17.0 if z + zz - 8 < j0 else 0.0)
        e1 = t1 if j1 is None else (-17.0 if z + zz - 8 < j1 else 0.0)
        x, y = at(px, py, side, -e0, -6)
        put(label + "_Trim%d" % (300 if zz == 300 else 400), FV + "SM_MainBorder_04", x, y, z + zz, yaw,
            ((width + e0 + e1) / 150.0, 1, 1), folder=folder)


COLUMNS = {}   # outside corners: (lx, ly) -> {"dirs": the two outward directions, "spans": [(z0, z1)] it covers}
COLUMN_PROUD = 0.02   # m the column stands out of each face


def solid_z(lx, ly, z1, me):
    """Something stands at (lx, ly) up to at least z1 (cm): the arena edge, or another house that tall."""
    return cover_top(lx, ly, me) >= z1 - 1


def corner_adjust(side, s, end, outward, me, z0, z1):
    """How a run end meets its neighbours, in cm: (shorten the run by, lengthen the trim by).
    Wall pieces are 20 cm thick behind their face, so where two walls meet their end caps would sit in the other
    wall's face and z-fight (user 2026-11-03: "overlapping faces... corners of the buildings").
    - Inside corner (the cell ahead, in front of the face, is solid: a neighbour's wall or the end wall): run on 10 cm
      so the end cap is buried in that wall. The north/south trim stops 7 cm short of the wall ahead, at the front of
      its trim; the east/west trim runs on into the wall.
    - Outside corner (the cell ahead behind the face line is open too): a 20 x 20 cm concrete corner column, 2 cm
      proud of both faces, is recorded in COLUMNS; both runs stop 10 cm inside it, so each face's material ends at
      the column. The east/west trim crosses it to 7 cm past the corner; the north/south trim stops behind.
    - Otherwise a neighbour continues the face in line: nothing.
    Houses (2026-11-03) are off the 1.5 m grid where set back and differ in height, so the probes sit 5 cm off the
    corner and ask whether something stands there up to this piece's top (z1).
    - Diagonal (houses touching at a corner point only): ahead in front is solid but ahead behind is open - an
      outside corner of this house (a column), not an inside one: running on would poke out of its other face.
    - A lower house in line, ahead behind the face: still an outside corner above it, but both trims stop behind the
      column, since that house's trims can sit at the same height."""
    (ex, ey), (ox, oy) = end, outward
    nlx, nly = LNORM[side]
    behind = (ex + ox * 0.05 - nlx * 0.05, ey + oy * 0.05 - nly * 0.05)
    if solid_z(ex + ox * 0.05 + nlx * 0.05, ey + oy * 0.05 + nly * 0.05, z1, me) and solid_z(*behind, z1, me):
        # Both trims stand 7 cm proud, so at an inside corner they'd cross (user: "overlaps happens in the trims as
        # well"): the east/west trim runs into the wall ahead, the north/south one stops at its front.
        return -10.0, (0.0 if side in ("east", "west") else -17.0)
    if not solid_z(*behind, z1, me):
        # User (screenshot): "This corner pattern is bad". Overlapping the walls 2 cm put one face's material on the
        # other face as a 20 cm strip. A corner column ends both faces cleanly, as on a real CHB house.
        # keyed by corner and its two outward directions: houses of different heights can share a corner point
        key = (round(ex, 3), round(ey, 3), tuple(sorted({(ox, oy), (nlx, nly)})))
        COLUMNS.setdefault(key, {"dirs": set(key[2]), "spans": []})["spans"].append((z0, z1))
        if side in ("north", "south") or cover_top(*behind, me) > z0 + 1:
            return 10.0, -9.0
        return 10.0, 17.0
    return 0.0, 0.0


def favela_run(bid, b, side, s, start, length_cm, name, face_mat, adj=((0.0, 0.0), (0.0, 0.0)), onto_balcony=False,
               buried=False, cover=0.0, junctions=(None, None)):
    """buried: a lower neighbour hides the bottom of this storey (it only shows above that roof) - plain wall, no
    openings, no stains. cover: the top (cm) of whatever stands in front, for trims hidden under it."""
    (cut0, ext0), (cut1, ext1) = adj
    rx, ry = RUN[side]
    start = (start[0] + rx * cut0, start[1] + ry * cut0)
    length_cm -= cut0 + cut1
    h, sx = fit(length_cm)
    widths = [TILE_W * sx] * (h // 2) + ([HALF_W * sx] if h % 2 else [])
    if not buried:
        wall_runs.append({"start": start, "len": length_cm, "side": side, "z": s * b["sh"], "name": name,
                          "widths": widths})
    kinds = []
    for i, w in enumerate(widths):
        if thin(b) or w < HALF_MAX or buried:
            kinds.append("plain")
        elif (bid, side, s) == DECK_FACE or onto_balcony:
            kinds.append("door" if i % 2 == 0 else "window")
        else:
            r = rnd.random()
            p = P_GROUND if s == 0 else P_UPPER
            prev = kinds[-1] if kinds else None
            k = "plain"
            if r < p.get("door", 0) and prev != "door":
                k = "door"
            elif r < p.get("door", 0) + p.get("window", 0):
                k = "window"
            kinds.append(k)
    full = [i for i, w in enumerate(widths) if w >= HALF_MAX]
    if not thin(b) and not buried and len(full) >= 3 and all(kinds[i] == "plain" for i in full):
        kinds[full[len(full) // 2]] = "window"            # a long blank run gets one window
    # One material for the whole block face, every storey and opening included (user 2026-11-03: "Keep the texturing
    # consistent per block face"). Favela's patchwork (patches, patched-in openings) is off.
    rx, ry = RUN[side]
    off = 0.0
    for i, (w, k) in enumerate(zip(widths, kinds)):
        mat = face_mat
        px, py = start[0] + rx * off, start[1] + ry * off
        label = "%s_%d" % (name, i)
        favela_tile(label, k, mat, px, py, s * b["sh"], side, sx, w, s == b["storeys"] - 1, BLK,
                    ext0 if i == 0 else 0.0, ext1 if i == len(widths) - 1 else 0.0, sh=b["sh"], cover=cover,
                    j0=junctions[0] if i == 0 else None, j1=junctions[1] if i == len(widths) - 1 else None)
        if not thin(b):
            wall_tiles.append({"label": label, "kind": k, "x": px, "y": py, "z": s * b["sh"], "side": side, "w": w,
                               "s": s, "top": s == b["storeys"] - 1})
        if s == 0:
            ground_pieces.append((label, k, px, py, side, w))
        off += w


seed = 0
for bid, b in BLOCKS.items():
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    sides = {"north": ((x0, y0), (x1, y0)), "south": ((x0, y1), (x1, y1)), "west": ((x0, y0), (x0, y1)),
             "east": ((x1, y0), (x1, y1))}
    # One material per block face and storey (user: "Keep the texturing consistent per block face"; "second floor
    # material can differ from ground floor"): an upper storey keeps the one below 40% of the time.
    face_mats = {}
    for side in sides:
        for s in range(b["storeys"]):
            below = face_mats.get((side, s - 1))
            face_mats[(side, s)] = below if below and rnd.random() < SAME_AS_GROUND else pick(FACE_MATS)
    for s in range(b["storeys"]):
        # A storey's wall shows wherever whatever stands outside it is lower than the storey's top; where that neighbour
        # still hides its bottom half metre or more ("buried"), it shows above that roof only and stays plain.
        z0, z1 = s * b["sh"], (s + 1) * b["sh"]
        for side, (p0, p1) in sides.items():
            nlx, nly = LNORM[side]
            length = abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])
            ux, uy = (p1[0] - p0[0]) / length, (p1[1] - p0[1]) / length
            # Neighbouring pieces that both show make one run (two runs meeting in line would each turn a corner
            # there and cross their trims): buried if any of it is, `cover` the lowest roof in front of it.
            # Where a run that shows fully meets one that shows only above a lower roof, the wall is one plane:
            # the two meet flush (a "junction", no corner), and trims at the lower house's height stop short of its
            # wall there (its own trims sit at the same heights).
            runs = []
            for t0, t1, c in side_intervals(b, side, lambda c: c):
                st = "hidden" if c >= z1 - 1 else ("buried" if c > z0 + 50 else "open")
                if st == "hidden":
                    continue
                if runs and abs(runs[-1][1] - t0) < 1e-6 and runs[-1][3] == st:
                    runs[-1][1], runs[-1][2] = t1, min(runs[-1][2], c)
                else:
                    runs.append([t0, t1, c, st])
            for r, (k0, k1, cov, res) in enumerate(runs):
                j_a = max(cov, runs[r - 1][2]) if r > 0 and abs(runs[r - 1][1] - k0) < 1e-6 else None
                j_c = max(cov, runs[r + 1][2]) if r + 1 < len(runs) and abs(runs[r + 1][0] - k1) < 1e-6 else None
                exposed_sides.setdefault(bid, set()).add(side)
                a = (p0[0] + ux * k0, p0[1] + uy * k0)
                c = (p0[0] + ux * k1, p0[1] + uy * k1)
                A, C = ue(*a), ue(*c)
                rx, ry = RUN[side]
                start = A if (C[0] - A[0]) * rx + (C[1] - A[1]) * ry > 0 else C
                n = int(round((k1 - k0) / 1.5))   # 1.5 m cells (the shop row stays on the grid)
                name = "%s_%s%d_%d" % (bid, side[0].upper(), s, r)
                seq = SPECIAL.get((bid, side, s))
                if seq is None:
                    ua = (-ux, -uy)                                   # beyond the a end, and beyond the c end
                    adj_a = (0.0, 0.0) if j_a is not None else corner_adjust(side, s, a, ua, b, z0, z1)
                    adj_c = (0.0, 0.0) if j_c is not None else corner_adjust(side, s, c, (ux, uy), b, z0, z1)
                    mid = ((a[0] + c[0]) / 2 + nlx * 0.75, (a[1] + c[1]) / 2 + nly * 0.75)
                    favela_run(bid, b, side, s, start, (k1 - k0) * 100.0, name, face_mats[(side, s)],
                               (adj_a, adj_c) if start == A else (adj_c, adj_a),
                               onto_balcony=s == 1 and balcony_at(*mid), buried=res == "buried", cover=cov,
                               junctions=(j_a, j_c) if start == A else (j_c, j_a))
                else:   # AsiaSlum shop fronts: 3 m modules and 1.5 m halves fill the run exactly
                    pieces = [("full", i) for i in range(n // 2)] + ([("half", n // 2)] if n % 2 else [])
                    for kind, i in pieces:
                        px, py = start[0] + rx * 300 * i, start[1] + ry * 300 * i
                        if kind == "full":
                            mesh = seq[(i + seed) % len(seq)]
                            label = "%s_%d" % (name, i)
                            put(label, AS + mesh, px, py, s * 400.0, YAW[side], folder=BLK)
                            door_for(label, mesh, px, py, s * 400.0, side, BLK)
                            if s == 0:
                                ground_pieces.append((label, "shop" if mesh == "SM_Shop_A_001" else "asia", px, py,
                                                      side, 300.0))
                        else:
                            put("%s_half" % name, AS + "SM_HouseWall_A_001_HalfA", px, py, s * 400.0, YAW[side],
                                folder=BLK)
                if s == 1 and side in ("south", "east") and n >= 3:
                    upper_runs.append((bid, side, a, c))
                seed += 1


# --- Corner columns at outside corners (see corner_adjust) ----------------------------------------------------------
for k, ((lx, ly, _dirs), col) in enumerate(sorted(COLUMNS.items())):
    (ax, ay), (bx, by) = sorted(col["dirs"])
    dx, dy = ax + bx, ay + by                     # the corner's outward diagonal, e.g. (1, -1)
    xa, xb = sorted((lx - dx * 0.2, lx + dx * COLUMN_PROUD))
    ya, yb = sorted((ly - dy * 0.2, ly + dy * COLUMN_PROUD))
    merged = []                                   # one piece per run of touching storeys
    for z0, z1 in sorted(col["spans"]):
        if merged and z0 <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], z1)
        else:
            merged.append([z0, z1])
    for s0, (z0, z1) in enumerate(merged):
        top = z1 + 5 + 2 * (k % 2)                # over the band's top; columns sharing a corner point differ
        X1, Y0 = ue(xa, ya)
        X0, Y1 = ue(xb, yb)
        put("Column_%d_%d" % (k, s0), CUBE, X0, Y0, z0, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, (top - z0) / 100.0),
            folder="BackAlleys/Blocks", mats=[CONC])

# --- Lids, cores, tin roofs on 1-storey blocks ------------------------------------------------------------------------
for bid, b in BLOCKS.items():
    x0, y0, x1, y1, st = b["x0"], b["y0"], b["x1"], b["y1"], b["storeys"]
    ex = exposed_sides.get(bid, set())
    inset = 0.3 if thin(b) or min(x1 - x0, y1 - y0) < 4.5 else 1.5
    cx0 = x0 + (inset if "west" in ex else 0)
    cx1 = x1 - (inset if "east" in ex else 0)
    cy0 = y0 + (inset if "north" in ex else 0)
    cy1 = y1 - (inset if "south" in ex else 0)
    # The lid's top sits 5 cm under the parapet band's top, so the two never share a plane.
    # The lid is inset 5 cm, so its sides don't lie in the walls' outer faces.
    top = st * b["sh"]
    for kind, (a0, b0, a1, b1), z, h, mat in (("Lid", (x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05), top - 25,
                                               0.2, None),
                                              ("Core", (cx0, cy0, cx1, cy1), 0.0, top / 100.0 - 0.2, "interior")):
        X1, Y0 = ue(a0, b0)
        X0, Y1 = ue(a1, b1)
        terrace_floor = kind == "Lid" and b["roof"] == "terrace" and TERRACES   # plain concrete, UV-mapped
        put("%s_%s" % (kind, bid), CUBE, X0, Y0, z, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, h),
            folder="BackAlleys/Lids", mat=mat, mats=[FM + "MI_Concrete_01"] if terrace_floor else None)
    if st == 1 and not TERRACES:   # tin sheets on top (seen from the deck): SM_MetalPlate_C_001 is 2 x 3 m, pivot at its min corner
        w, d = x1 - x0, y1 - y0
        nx_, ny_ = max(1, math.ceil(w / 2.0)), max(1, math.ceil(d / 3.0))
        for i in range(nx_):
            for j in range(ny_):
                X1, Y0 = ue(x0 + i * w / nx_, y0 + j * d / ny_)
                # sheet local x -> UE X (north), local y -> UE Y (east): its min corner is the SW corner in layout terms
                put("Roof_%s_%d_%d" % (bid, i, j), AS + "SM_MetalPlate_C_001", X1 - (d / ny_) * 100, Y0, 405.0, 0,
                    ((d / ny_) * 100 / 200.0, (w / nx_) * 100 / 300.0, 1), folder="BackAlleys/Lids")

# --- Covered roof terraces on the 1-storey blocks ---------------------------------------------------------------------
# User 2026-11-03: "study the balcony with currogated roof pattern in favela map", then "Yes, build them" (on the five
# 1-storey blocks). The Favela version (Tools/LevelGen/LESSONS.md): the flat roof of a lower part, a low parapet on its
# open sides, the taller wall behind, and flat corrugated sheets about 2.75 m up resting on the walls - with a plank
# frame (two planks back to back) where no wall carries them. Our 1-storey blocks are 1.5 m deep, so: one row of
# SM_Slate_01 lengthwise (1.54 m wide, about the depth), 30 cm end laps, 2 cm height steps; parapets (SM_Wall_14 in
# concrete, 1.06 m) on the sides open at storey 1; plank posts every <= 1.9 m on open long sides plus a beam under the
# sheet edge. The tin roof sheets are replaced. Water drums are dressing (the blockouts-only rule) and left out.
TER = "BackAlleys/Terraces"
WOOD = FV + "SM_Wooden_part_05"         # 190 x 4 x 16 cm, pivot at one end (the mesh runs along its local -X)
SHEET_UNDER = 275.0                    # sheet underside above the terrace floor (Favela median 276)
PARAPET_H = 106.0


def plank_pair(label, x, y, z, yaw, length, vertical):
    """The Favela plank member: two SM_Wooden_part_05 back to back (scale y +1 / -1). Vertical: a post standing up
    from (x, y, z) (pitch -90 turns the mesh's -X run upward); else a beam running length cm along yaw from (x, y, z)
    (turned 180, since the mesh runs along -X)."""
    for k, sy in enumerate((1.0, -1.0)):
        put("%s_%d" % (label, k), WOOD, x, y, z, yaw if vertical else yaw + 180, (length / 190.0, sy, 1), folder=TER)
        if vertical:
            items[-1]["rot"][0] = -90.0


AWN_D = 2.4          # m the lean-to awning reaches out from the taller wall
AWN_PITCH = 9.0      # degrees it falls outward
AWN_HIGH = 290.0     # sheet underside at the wall, above the terrace floor (under the upper storey's band)


def lean_to(bid, b, floor):
    """The reference picture's roof: corrugated sheets hung off the taller wall (the strip's inner edge, opposite its
    balcony side), running down the slope, side by side along the wall with 9 cm laps, held at the outer edge by plank
    posts standing on the terrace floor and a plank beam."""
    back = OPP[b["balcony"]]                               # the strip's side against the taller part of the block
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    ox, oy = LNORM[b["balcony"]]                           # outward, in layout terms
    if back in ("north", "south"):
        wall_y = y0 if back == "north" else y1
        p0, p1 = (x0, wall_y), (x1, wall_y)
    else:
        wall_x = x0 if back == "west" else x1
        p0, p1 = (wall_x, y0), (wall_x, y1)
    rl = abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])
    ux, uy = (p1[0] - p0[0]) / rl, (p1[1] - p0[1]) / rl
    depth = min(AWN_D, (abs(x1 - x0) if back in ("west", "east") else abs(y1 - y0)) - 0.6)
    tanp = math.tan(math.radians(AWN_PITCH))
    z_high = floor + AWN_HIGH
    yaw = math.degrees(math.atan2(ox, -oy))                # layout x -> UE +Y, layout y -> UE -X
    p = math.radians(-AWN_PITCH)
    sx, sy = (depth * 100 + 10) / 382.0, 1.0
    cov = rl * 100 - 20                                    # sheets stop 10 cm short of each end
    n = max(1, math.ceil((cov - 9) / 145.0))
    step = (cov - 154) / (n - 1) if n > 1 else 0.0
    for i in range(n):
        t = 10 + 77 + step * i if n > 1 else rl * 50       # cm along the wall to the sheet's centre
        lx = p0[0] + ux * t / 100 + ox * (depth / 2 + 0.05)
        ly = p0[1] + uy * t / 100 + oy * (depth / 2 + 0.05)
        cx, cy = ue(lx, ly)
        cz = z_high - tanp * (depth * 100 / 2) + 2 * (i % 2)
        vx, vy, vz = -2 * sx, -35 * sy, 72.0               # the sheet's underside centre in its local frame
        rx_ = vx * math.cos(p) - vz * math.sin(p)
        rz_ = vx * math.sin(p) + vz * math.cos(p)
        cyaw, syaw = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        put("Awning_%s_%d" % (bid, i), FV + "SM_Slate_01", cx - (rx_ * cyaw - vy * syaw), cy - (rx_ * syaw + vy * cyaw),
            cz - rz_, yaw, (sx, sy, 1), folder=TER)
        items[-1]["rot"][0] = -AWN_PITCH
    # posts and beam 15 cm inside the awning's outer edge
    out = depth - 0.15
    under = z_high - tanp * out * 100                      # sheet underside above the post line
    nposts = max(2, math.ceil((rl - 0.7) / 2.0) + 1)
    for i in range(nposts):
        f = 0.35 + (rl - 0.7) * i / (nposts - 1)        # 35 cm in from the ends: clear of side parapets
        X, Y = ue(p0[0] + ux * f + ox * out, p0[1] + uy * f + oy * out)
        plank_pair("AwnPost_%s_%d" % (bid, i), X, Y, floor, YAW[b["balcony"]], under - floor - 16, True)
    pieces = max(1, math.ceil(rl / 3.5))
    for i in range(pieces):
        X, Y = ue(p0[0] + ux * rl * i / pieces + ox * out, p0[1] + uy * rl * i / pieces + oy * out)
        X2, Y2 = ue(p0[0] + ux * rl * (i + 1) / pieces + ox * out, p0[1] + uy * rl * (i + 1) / pieces + oy * out)
        plank_pair("AwnBeam_%s_%d" % (bid, i), X, Y, under - 16, math.degrees(math.atan2(Y2 - Y, X2 - X)),
                   rl * 100 / pieces, False)


OPP = {"north": "south", "south": "north", "west": "east", "east": "west"}
BANISTER_SHARE = 0.4             # terraces edged with Favela's frame banister instead of the stone parapet
EDGE_RNG = random.Random(41)     # its own sequence


def spawn_wall_at(lx, ly, reach=0.8):
    """(lx, ly) is at a spawn door's end wall (2 storeys of 4 m across the alley end, 3.375 m either side of the
    door, on the arena edge) - within `reach` m of the edge line."""
    for d in L["doors"]:
        if d["face"] in ("N", "S") and abs(lx - d["x"]) <= 3.4 and abs(ly - d["y"]) <= reach:
            return True
        if d["face"] in ("E", "W") and abs(ly - d["y"]) <= 3.4 and abs(lx - d["x"]) <= reach:
            return True
    return False


def taller_at(lx, ly, z):
    """A house at least z (cm) tall covers (lx, ly), or a spawn door's end wall stands there - the bare arena edge
    doesn't count. (Was: a 2-storey block; the terraces pass their floor + 2 m since houses differ in height.)"""
    return spawn_wall_at(lx, ly) or any(b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] and
                                        b["storeys"] * b["sh"] >= z for b in BLOCKS.values())


def twin_terrace_at(lx, ly, me):
    """Another terrace house of about the same height (within 60 cm) with a lower id covers (lx, ly): the parapet
    between the two is that house's, so the two caps don't cross."""
    return any(b is not me and b["roof"] == "terrace" and b["id"] < me["id"] and abs(b["sh"] - me["sh"]) < 60 and
               b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] for b in BLOCKS.values())

if TERRACES:
    for bid, b in BLOCKS.items():
        if b["roof"] != "terrace":
            continue
        x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
        floor = b["sh"] - 5                                 # the lid's top
        zt = b["sh"] + 200.0                                # "taller": a wall at least 2 m over the terrace floor
        # Which sides are open at storey 1 (no taller neighbour or arena edge against them)?
        sides = {"north": ((x0, y0), (x1, y0)), "south": ((x0, y1), (x1, y1)), "west": ((x0, y0), (x0, y1)),
                 "east": ((x1, y0), (x1, y1))}
        open_runs = {}
        for side, (p0, p1) in sides.items():
            nlx, nly = LNORM[side]
            length = abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])
            ux, uy = (p1[0] - p0[0]) / length, (p1[1] - p0[1]) / length
            # open = no taller block there; the arena edge counts as open too, so terraces on edge blocks still
            # get a parapet on their outer side (visible from above)
            cells = [k for k in range(int(round(length / 1.5)))
                     if not taller_at(p0[0] + ux * (k + 0.5) * 1.5 + nlx * 0.75,
                                      p0[1] + uy * (k + 0.5) * 1.5 + nly * 0.75, zt) and
                     not twin_terrace_at(p0[0] + ux * (k + 0.5) * 1.5 + nlx * 0.75,
                                         p0[1] + uy * (k + 0.5) * 1.5 + nly * 0.75, b)]
            if cells:
                open_runs[side] = (p0, ux, uy, cells)
        # Edge style per terrace (user 2026-11-03: "use main border on top of a stone bannister. also the favela level
        # used a wooden window frame as banisters as well. Use that as variation"): a stone parapet capped with the
        # SM_MainBorder_04 trim, or (BANISTER_SHARE of them) Favela's frame banister.
        style = "banister" if EDGE_RNG.random() < BANISTER_SHARE else "parapet"
        # Parapets: per open run, SM_Wall_14 (runs along its local +Y, thickness inward), placed like the bands.
        # North/south parapets stop 20 cm short where an east/west side is open too (a butt joint: no coincident faces).
        for side, (p0, ux, uy, cells) in open_runs.items():
            runs = []
            for k in cells:
                if runs and runs[-1][1] == k:
                    runs[-1][1] = k + 1
                else:
                    runs.append([k, k + 1])
            for r, (k0, k1) in enumerate(runs):
                a = (p0[0] + ux * k0 * 1.5, p0[1] + uy * k0 * 1.5)
                c = (p0[0] + ux * k1 * 1.5, p0[1] + uy * k1 * 1.5)
                A, C = ue(*a), ue(*c)
                rx, ry = RUN[side]
                start = A if (C[0] - A[0]) * rx + (C[1] - A[1]) * ry > 0 else C
                RL = (k1 - k0) * 150.0
                # Each end: where a taller neighbour stands ahead (in front of the face, or in line behind it) run
                # 10 cm into its wall; where another parapet turns the corner, north/south parapets stop 20 cm short
                # (butt joint). Parapets sit 1 cm in from the face line, so running into an in-line neighbour never
                # puts the parapet's face in that neighbour's face.
                nlx, nly = LNORM[side]
                cuts = []
                for (ex, ey), (ox, oy) in ((a, (-ux, -uy)), (c, (ux, uy))):
                    # (taller_at, not solid: the arena edge is no wall to run into - the parapets turn the corner)
                    ahead_front = taller_at(ex + ox * 0.75 + nlx * 0.75, ey + oy * 0.75 + nly * 0.75, zt)
                    ahead_behind = taller_at(ex + ox * 0.75 - nlx * 0.75, ey + oy * 0.75 - nly * 0.75, zt)
                    if ahead_front or ahead_behind:
                        cuts.append(-10.0)
                    elif side in ("north", "south"):
                        cuts.append(20.0)
                    else:
                        cuts.append(0.0)
                cut_start, cut_end = cuts if start == A else cuts[::-1]
                start = (start[0] + rx * cut_start, start[1] + ry * cut_start)
                RL -= cut_start + cut_end
                inx, iny = NORMAL[side]
                if style == "banister":
                    # The wooden window as banister (user: "the banister window frame I was talking about was a wooden
                    # one"): Favela stands SM_windows_06 (172 x 12 x 80 cm, MI_Windows_02 wood) on the top of the wall
                    # below a roof edge (36 of its 40), at 1.66 / 1.66 / 1.24 - panels ~2.85 m wide, 1 m tall. Here:
                    # panels <= 2.85 m filling the run, 1 m tall, 12 cm deep. The mesh runs along its local -X with its
                    # depth on local -Y, so it turns 180 and its pivot sits 13 cm in (the panel fills 13 to 1 cm in).
                    n = max(1, math.ceil(RL / 285.0))
                    for i in range(n):
                        px = start[0] + rx * RL * i / n - inx * 13.0
                        py = start[1] + ry * RL * i / n - iny * 13.0
                        put("Banister_%s_%s%d_%d" % (bid, side[0].upper(), r, i), FV + "SM_windows_06", px, py,
                            b["sh"], YAW[side] + 180, (RL / n / 172.0, 1.0, 1.24), folder=TER)
                    continue
                pieces = max(1, math.ceil(RL / 200.0))
                for i in range(pieces):
                    px = start[0] + rx * RL * i / pieces - inx * 1.0
                    py = start[1] + ry * RL * i / pieces - iny * 1.0
                    put("Parapet_%s_%s%d_%d" % (bid, side[0].upper(), r, i), FV + "SM_Wall_14", px, py, b["sh"],
                        YAW[side] - 90, (1, RL / pieces / 200.0, 1), folder=TER, mats=[CONC])
                # The cap: SM_MainBorder_04 along the top, 5 cm in from the face (it spans 18 cm in to 8 cm out), as
                # Favela caps its parapets. At a corner where two parapets meet, the east/west cap runs 8 cm past
                # the corner and the north/south one (its parapet stopped 20 cm short) runs back 2 cm to meet it;
                # where the parapet runs into a neighbour's wall, the cap stops with it.
                ext = {20.0: 2.0, 0.0: 8.0, -10.0: 0.0}
                e0, e1 = ext[cut_start], ext[cut_end]
                for i in range(pieces):
                    seg = RL / pieces
                    t0 = e0 if i == 0 else 0.0
                    t1 = e1 if i == pieces - 1 else 0.0
                    px = start[0] + rx * (seg * i - t0) - inx * 5.0
                    py = start[1] + ry * (seg * i - t0) - iny * 5.0
                    put("ParapetCap_%s_%s%d_%d" % (bid, side[0].upper(), r, i), FV + "SM_MainBorder_04", px, py,
                        b["sh"] + PARAPET_H, YAW[side], ((seg + t0 + t1) / 150.0, 1, 1), folder=TER)
        if b.get("balcony") and min(x1 - x0, y1 - y0) >= 3.0:
            lean_to(bid, b, floor)
            continue
        # Sheets: one row along the long axis, the block's depth wide.
        along_x = (x1 - x0) >= (y1 - y0)
        RL, RD = ((x1 - x0), (y1 - y0)) if along_x else ((y1 - y0), (x1 - x0))
        n = max(1, math.ceil((RL * 100 + 20) / 350.0))
        seg = (RL * 100 + 20) / n                            # +10 cm overhang at each end
        sx = (seg + 30) / 382.0                              # 30 cm end laps
        sy = (RD * 100 + 10) / 154.0
        zp = floor + SHEET_UNDER - 72                        # SM_Slate_01's underside is 72 cm above its pivot
        yaw = 90 if along_x else 180                         # layout x runs along UE +Y, layout y along UE -X
        c, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        ox, oy = -2 * sx, -35 * sy                           # the sheet's centre, in its local frame, from the pivot
        for i in range(n):
            t = -0.1 + seg / 100.0 * (i + 0.5)               # m along the long axis from the block's start
            lx, ly = (x0 + t, (y0 + y1) / 2) if along_x else ((x0 + x1) / 2, y0 + t)
            cx, cy = ue(lx, ly)
            put("Sheet_%s_%d" % (bid, i), FV + "SM_Slate_01", cx - (ox * c - oy * s_), cy - (ox * s_ + oy * c),
                zp + 2 * (i % 2), yaw, (sx, sy, 1), folder=TER)
        # Plank frame along open long sides: posts on the parapet line every <= 1.9 m, a beam under the sheet edge.
        for side in (("north", "south") if along_x else ("west", "east")):
            if side not in open_runs:
                continue
            p0, ux, uy, cells = open_runs[side]
            nlx, nly = LNORM[side]
            post_in = 0.20 if style == "banister" else 0.12      # over the parapet, or clear behind the banister
            ends = (p0[0] - nlx * post_in, p0[1] - nly * post_in)
            nposts = max(2, math.ceil(RL / 1.9) + 1)
            for i in range(nposts):
                f = 0.1 + (RL - 0.2) * i / (nposts - 1)
                X, Y = ue(ends[0] + ux * f, ends[1] + uy * f)
                base = floor if style == "banister" else b["sh"] + PARAPET_H   # behind a banister: on the floor
                plank_pair("Post_%s_%s%d" % (bid, side[0].upper(), i), X, Y, base, YAW[side],
                           floor + SHEET_UNDER - base, True)
            pieces = max(1, math.ceil(RL / 3.5))
            for i in range(pieces):
                X, Y = ue(ends[0] + ux * RL * i / pieces, ends[1] + uy * RL * i / pieces)
                X2, Y2 = ue(ends[0] + ux * RL * (i + 1) / pieces, ends[1] + uy * RL * (i + 1) / pieces)
                plank_pair("Beam_%s_%s%d" % (bid, side[0].upper(), i), X, Y, floor + SHEET_UNDER - 16,
                           math.degrees(math.atan2(Y2 - Y, X2 - X)), RL * 100 / pieces, False)

# --- Metal roofs --------------------------------------------------------------------------------------------------------
# User 2026-11-03: "most philippine houses still use metal roofs even in stone houses" ... "also most metal roofs have at
# least a slight slope for water to slide on". Redone the same day from the user's reference photo (a shanty with
# lean-to roofs of mixed rusty and galvanised sheets, metal flashing, timber fascia) and "it shouldnt be just a metal
# slate on a sloped surface, theres usually a "kisame" there" -> "Both" (a flat ceiling with the roof on a frame above
# it, and boarded eaves).
# - Mostly single slopes (5-10 deg) falling toward open ground, never into a taller neighbour; a few wide free-standing
#   houses get two slopes (12-15 deg) and a ridge cap. Never flat (>= 3 deg).
# - Sheets: AsiaSlum's corrugated SM_MetalPlate_A (1.62 m wide, 3.25 m or 1.65 m long, four rust variants), in columns
#   down the slope with an 18 cm side lap (alternate columns 2 cm up) and 15 cm end laps (each upper sheet 1.5 cm over
#   the one below), long and short sheets mixed per column, a slight skew per sheet and a ragged eave.
# - The kisame: the walls stop at the flat ceiling (the concrete lid). The roof sits ROOF_CLEAR above the wall top on
#   a frame; the frame is closed by a timber fascia under every open eave (and an open high edge), level kisame boards
#   from the fascia back to the wall, barge boards under the open sloping edges, and horizontal weatherboards from the
#   wall top up to the kisame or the slope on every side that shows. One paint per house (natural, blue, green, brown:
#   MiddleEast's SM_wooden_beams). Each side is one board scaled to the full height (user, 2026-11-03: "the back of
#   the roof has 5 wood pieces, use one scaled board instead"). A sloping side is sealed up to the sheets ("close the
#   sides ... i mean seal it"): the board reaches the slope's lower end and an SM_Ramp wedge in the same paint fills
#   the triangle under each slope.
# - Galvanised flashing where a high edge meets a taller wall (a strip on the sheets and one up the wall).
# The flat concrete lid stays under the roof as the ceiling.
RF = "BackAlleys/Roofs"
PLATES = {"long": [AS + "SM_MetalPlate_A_001", AS + "SM_MetalPlate_A_002"],
          "short": [AS + "SM_MetalPlate_A_003", AS + "SM_MetalPlate_A_004"]}
PLATE_LEN = {"long": 324.9, "short": 164.9}   # pivot at the top end, centred in X and Y; hangs down local -Z
PLATE_W, PLATE_T = 162.4, 4.8                  # local X, local Y (corrugation depth)
SHEET_UP = 1                                   # which local Y faces up: +1 = +Y
SIDE_LAP, END_LAP = 18.0, 15.0
BEAMS = {"natural": ME + "MiddleEast/SM_wooden_beams_01", "blue": ME + "MiddleEast/SM_wooden_beams_02",
         "green": ME + "MiddleEast/SM_wooden_beams_03", "brown": ME + "MiddleEast/SM_wooden_beams_05"}
BEAM_SIZE = {p: (25.4, 737.6, 34.4 if p.endswith("_05") else 23.8) for p in BEAMS.values()}   # centred pivot, Y long
# The weatherboards and wedges use M_BackAlleys_Boards (create_board_material_ue.py), mapped from world position: the pack's
# wood textures are atlases, and a stretched beam or SM_Ramp's UVs land on the atlas's smeared padding (user: "roof
# textures are busted too", a wedge in grey streaks). The fascia, barge and kisame keep the beams' own UVs.
BOARD_MAT = {BEAMS["natural"]: BM + "MI_BackAlleys_Boards_Natural", BEAMS["blue"]: BM + "MI_BackAlleys_Boards_Blue",
             BEAMS["green"]: BM + "MI_BackAlleys_Boards_Green", BEAMS["brown"]: BM + "MI_BackAlleys_Boards_Brown"}
# Sheet finishes (AssetGen, 2026-11-03; user: "Yes, make them"): our own parent, a drop-in for the plates' slot 0.
# Each roof has a main finish; P_PATCH of its sheets are replacements in another finish, as in the user's photo.
SHEET_MATS = {f: BM + "MI_BackAlleys_MetalSheet_" + f for f in ("Galv", "RedOxide", "Rust")}
SHEET_MIX = (("Galv", 0.5), ("RedOxide", 0.3), ("Rust", 0.2))
P_PATCH = 0.25
FLASH_MAT = BM + "MI_BackAlleys_Flashing"       # world-mapped: the sheet atlas smeared on a cube
ROOF_RNG = random.Random(83)                   # its own sequence
MONO_PITCH, GABLE_PITCH, MIN_PITCH = (5.0, 10.0), (12.0, 15.0), 3.0
P_GABLE = 0.15
ROOF_CLEAR = 42.0                              # sheet underside over the wall top, at the low wall line
OVERHANG = {"low": 0.45, "lateral": 0.25, "high": 0.20}
FASCIA_H, FASCIA_T, SOFFIT_T = 20.0, 3.0, 2.0
BOARD_T = 2.5
FILL_IN = 2.0                                  # weatherboards' outer face, cm behind the wall face
DOWN = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}   # layout direction a side faces


def roof_kind(c, T):
    if c >= 1e8:
        return "edge"
    if c >= T + 100:
        return "wall"
    if c > T - 60:
        return "flush"
    return "open"


def side_summary(b, side, T):
    iv = side_intervals(b, side, lambda c: (roof_kind(c, T), c))
    kinds = [k for _, _, (k, _) in iv]
    walls = [c for t0, t1, (k, c) in iv if k == "wall" and t1 - t0 >= 0.3]
    kind = "wall" if walls else ("flush" if "flush" in kinds else ("edge" if "edge" in kinds else "open"))
    return kind, (min(walls) if walls else None), iv


def side_line(b, side):
    """(fixed coordinate of the side's line, its axis 'x' or 'y' along it, inward unit (layout))"""
    return {"north": (b["y0"], "x", (0, 1)), "south": (b["y1"], "x", (0, -1)),
            "west": (b["x0"], "y", (1, 0)), "east": (b["x1"], "y", (-1, 0))}[side]


# Small vector kit for pieces that tilt in more than yaw (UE axes, cm).
def v_add(a, b, k=1.0):
    return (a[0] + k * b[0], a[1] + k * b[1], a[2] + k * b[2])


def v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_rot(v, k, deg):
    """v rotated about the unit axis k (Rodrigues)."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    kv, kd = v_cross(k, v), v_dot(k, v)
    return tuple(v[i] * c + kv[i] * s + k[i] * kd * (1 - c) for i in range(3))


def ue_dir(a, b):
    """A layout direction (a east, b south) as a UE vector."""
    return (-float(b), float(a), 0.0)


def axes_rot(X, Y, Z):
    """The UE rotator [pitch, yaw, roll] whose local axes are X, Y, Z (FMatrix::Rotator)."""
    pitch = math.atan2(X[2], math.hypot(X[0], X[1]))
    yaw = math.atan2(X[1], X[0])
    sy_ = (-math.sin(yaw), math.cos(yaw), 0.0)     # the Y axis of (pitch, yaw, 0)
    roll = math.atan2(v_dot(Z, sy_), v_dot(Y, sy_))
    return [round(math.degrees(pitch), 3), round(math.degrees(yaw), 3), round(math.degrees(roll), 3)]


def put_axes(label, asset, X, Y, Z, scale, anchor_local, anchor_world, mats=None, nocoll=False):
    """Places asset with local axes X, Y, Z (right-handed: Z = X x Y) so that the local point anchor_local (unscaled)
    lands on anchor_world."""
    if v_dot(v_cross(X, Y), Z) < 0:
        # Turn X round to keep the axes right-handed. The anchor stays as it is: it names a point of the mesh (a cube's
        # centre is (50, 50, 50) whichever way X points). Negating it put SM_Cube strips one length off (2026-11-03).
        X = (-X[0], -X[1], -X[2])
    off = (0.0, 0.0, 0.0)
    for ax, a, s in ((X, anchor_local[0], scale[0]), (Y, anchor_local[1], scale[1]), (Z, anchor_local[2], scale[2])):
        off = v_add(off, ax, a * s)
    p = v_add(anchor_world, off, -1.0)
    put(label, asset, p[0], p[1], p[2], 0.0, scale, folder=RF, mats=mats, nocoll=nocoll)
    items[-1]["rot"] = axes_rot(X, Y, Z)


def put_board(label, asset, centre, X, Y, Z, dims, mats=None, nocoll=False):
    """A box-like piece by its centre and size (cm) along X, Y, Z: a beam (centred pivot) or SM_Cube (min corner)."""
    if asset == CUBE:
        size, anchor = (100.0, 100.0, 100.0), (50.0, 50.0, 50.0)
    else:
        size, anchor = BEAM_SIZE[asset], (0.0, 0.0, 0.0)
    put_axes(label, asset, X, Y, Z, tuple(dims[i] / size[i] for i in range(3)), anchor, centre, mats, nocoll)


def metal_roof(bid, b):
    T = b["storeys"] * b["sh"]
    sides = {s: side_summary(b, s, T) for s in ("north", "south", "west", "east")}
    dims = {"x": b["x1"] - b["x0"], "y": b["y1"] - b["y0"]}
    best = None
    for low in ("north", "south", "west", "east"):
        lk, hk = sides[low][0], sides[OPP[low]][0]
        if lk == "wall":
            continue
        span = dims["y"] if low in ("north", "south") else dims["x"]
        other = dims["x"] if low in ("north", "south") else dims["y"]
        score = {"open": 3, "edge": 2, "flush": 0}[lk] + {"wall": 2, "flush": 1, "edge": 1, "open": 0}[hk] + \
            (1 if span <= other else 0) + ROOF_RNG.random() * 0.5
        if best is None or score > best[0]:
            best = (score, low, span)
    if best is None:
        return False                                       # walled in on every side: the flat lid stays
    _, low, span = best
    high = OPP[low]
    lk, hk = sides[low][0], sides[high][0]
    gable = lk in ("open", "edge") and hk in ("open", "edge") and span >= 6.0 and ROOF_ROLL() < P_GABLE
    pitch = ROOF_RNG.uniform(*(GABLE_PITCH if gable else MONO_PITCH))
    run = span / 2 if gable else span                     # m from a low wall to the high edge / ridge
    max_rise = 160.0
    if not gable and hk == "wall":
        max_rise = min(max_rise, sides[high][1] - T - ROOF_CLEAR - 40)
    pitch = max(MIN_PITCH, min(pitch, math.degrees(math.atan2(max_rise, run * 100))))
    tanp, cosp, sinp = (f(math.radians(pitch)) for f in (math.tan, math.cos, math.sin))
    beam = BEAMS[ROOF_RNG.choice(sorted(BEAMS))]
    flash = [FLASH_MAT]
    finish = ROOF_RNG.choices([f for f, _ in SHEET_MIX], [w for _, w in SHEET_MIX])[0]

    def zu(d):                                             # sheet underside, d m upslope from a low wall line
        return T + ROOF_CLEAR + tanp * d * 100

    def ovh(side, role):
        k = sides[side][0]
        return {"open": OVERHANG[role], "edge": 0.05, "flush": -0.05, "wall": -0.10}[k]

    lats = [s for s in ("north", "south", "west", "east") if s not in (low, high)]
    lat0, lat1 = sorted(lats, key=lambda s: s in ("east", "south"))   # min side first
    halves = [(low, run)] + ([(high, run)] if gable else [])
    eave_top = {}                                          # side -> top of its weatherboards (cm), for the eaves
    k = 0
    for h, (hlow, hrun) in enumerate(halves):
        dx, dy = DOWN[hlow]                                # layout downslope
        line, axis, _ = side_line(b, hlow)                 # the low wall line
        U = ue_dir(-dx, -dy)                               # UE upslope, horizontal
        Lat = ue_dir(1, 0) if axis == "x" else ue_dir(0, 1)
        o_lo = ovh(hlow, "low")
        o_hi = 0.05 if gable else ovh(OPP[hlow], "high")
        d0, d1 = -o_lo, hrun + o_hi
        a0 = (b["x0"] if axis == "x" else b["y0"]) - ovh(lat0, "lateral")
        a1 = (b["x1"] if axis == "x" else b["y1"]) + ovh(lat1, "lateral")
        Wl = (a1 - a0) * 100

        def P(d, a, z):                                    # UE point at d m upslope, lateral coordinate a (layout)
            lx, ly = (a, line - dy * d) if axis == "x" else (line - dx * d, a)
            X, Y = ue(lx, ly)
            return (X, Y, z)

        # Sheets.
        up_slope = (U[0] * cosp, U[1] * cosp, sinp)        # along the slope, uphill
        normal = (-U[0] * sinp, -U[1] * sinp, cosp)        # the roof plane's up normal
        nc = max(1, math.ceil((Wl - SIDE_LAP) / (PLATE_W - SIDE_LAP)))
        w = (Wl + SIDE_LAP * (nc - 1)) / nc
        rows_max = 1
        for i in range(nc):
            ac = a0 + (w / 2 + i * (w - SIDE_LAP)) / 100 + ROOF_RNG.uniform(-0.012, 0.012)
            lo = d0 - ROOF_RNG.uniform(0.0, 0.05)          # ragged eave
            S = (d1 - lo) * 100 / cosp
            best_seq = None
            for _ in range(8):                             # long and short sheets; the mix closest to true length
                seq, rem = [], S
                while rem > 0:
                    pick = "long" if rem > 260 or (rem > 175 and ROOF_RNG.random() < 0.5) else "short"
                    seq.append(pick)
                    rem -= PLATE_LEN[pick] - END_LAP
                sz = S / (sum(PLATE_LEN[p] for p in seq) - END_LAP * (len(seq) - 1))
                if best_seq is None or abs(sz - 1) < abs(best_seq[1] - 1):
                    best_seq = (seq, sz)
            seq, sz = best_seq
            rows_max = max(rows_max, len(seq))
            s = 0.0                                        # cm down the slope from the high end
            for j, pick in enumerate(seq):
                d = d1 - s * cosp / 100
                lift = PLATE_T / 2 + 1.5 * (len(seq) - 1 - j) + 2.0 * (i % 2)
                top = v_add(P(d, ac, zu(d)), normal, lift)
                skew = ROOF_RNG.uniform(-1.0, 1.0)
                Zs = v_rot(up_slope, normal, skew)         # local +Z points uphill (the sheet hangs down -Z)
                Xs = v_rot(Lat, normal, skew)
                Ys = normal if SHEET_UP > 0 else (-normal[0], -normal[1], -normal[2])
                f = finish if ROOF_RNG.random() >= P_PATCH else \
                    ROOF_RNG.choice([g for g, _ in SHEET_MIX if g != finish])
                put_axes("Roof_%s_%d" % (bid, k), ROOF_RNG.choice(PLATES[pick]), Xs, Ys, Zs,
                         (w / PLATE_W, 1.0, sz), (0.0, 0.0, 0.0), top, mats=[SHEET_MATS[f]])
                k += 1
                s += (PLATE_LEN[pick] - END_LAP) * sz
        # Fascia and kisame under an open eave (this half's low edge), and under an open high edge (single slope).
        edges = [(hlow, d0, -1)] if sides[hlow][0] == "open" else []
        if not gable and sides[high][0] == "open":
            edges.append((high, d1, 1))
        for side, de, sgn in edges:
            ztop = zu(de) - 1
            n = max(1, math.ceil(Wl / 700))
            for m in range(n):
                am = a0 + (m + 0.5) * (a1 - a0) / n
                put_board("Fascia_%s_%s%d" % (bid, side[0].upper(), m), beam,
                          P(de - sgn * FASCIA_T / 200, am, ztop - FASCIA_H / 2), U, Lat, (0, 0, 1),
                          (FASCIA_T, Wl / n, FASCIA_H))
                width = abs(de) * 100 - FASCIA_T if sgn < 0 else (de - hrun) * 100 - FASCIA_T
                dm = (de - sgn * FASCIA_T / 100) / 2 if sgn < 0 else (hrun + de - FASCIA_T / 100) / 2
                put_board("Kisame_%s_%s%d" % (bid, side[0].upper(), m), beam,
                          P(dm, am, ztop - FASCIA_H + SOFFIT_T / 2), U, Lat, (0, 0, 1), (width, Wl / n, SOFFIT_T))
            eave_top[side] = ztop - FASCIA_H
        if hlow not in eave_top:
            eave_top[hlow] = zu(0) - 1
        if not gable and high not in eave_top:
            eave_top[high] = zu(hrun) - 1
        # Barge boards under the open sloping edges.
        for lat, a in ((lat0, a0 - 0.01 + FASCIA_T / 200), (lat1, a1 + 0.01 - FASCIA_T / 200)):
            if sides[lat][0] != "open":
                continue
            db = hrun if gable else d1                     # two slopes: the pair meet at the ridge, no overlap
            dm = (d0 + db) / 2
            c = v_add(P(dm, a, zu(dm)), normal, -(1 + FASCIA_H / 2))
            put_board("Barge_%s_%s%d" % (bid, lat[0].upper(), h), beam, c, Lat, up_slope, normal,
                      (FASCIA_T, (db - d0) * 100 / cosp, FASCIA_H))
        # Flashing where the high edge meets a taller wall: a strip on the sheets and one up the wall.
        if not gable and sides[high][0] == "wall":
            am = (a0 + a1) / 2
            sheet_top = PLATE_T + 1.5 * (rows_max - 1) + 2.0 + 0.6
            # The strip runs from 25 cm down the sheets to 2 cm off the wall, over the 10 cm the roof stops short, and
            # meets the upstand (the rebuild captures showed a 9 cm gap when it stopped at the sheet ends).
            dc = (d1 - 0.25 + hrun - 0.02) / 2
            put_board("Flash_%s_S" % bid, CUBE, v_add(P(dc, am, zu(dc)), normal, sheet_top + 0.5), up_slope, Lat,
                      normal, ((hrun - 0.02 - (d1 - 0.25)) * 100 / cosp, Wl, 1.0), mats=flash, nocoll=True)
            zb = zu(hrun - 0.02) + sheet_top - 1
            put_board("Flash_%s_W" % bid, CUBE, P(hrun - 0.015, am, zb + 12.5), U, Lat, (0, 0, 1), (1.0, Wl, 25.0),
                      mats=flash, nocoll=True)
        if gable and h == 0:                               # ridge cap over both halves' top rows
            put_board("Ridge_%s" % bid, CUBE, P(hrun, (a0 + a1) / 2, zu(hrun) + PLATE_T + 1.5 * 3 + 2 + 1.5),
                      U, Lat, (0, 0, 1), (36.0, Wl + 4, 1.5), mats=flash, nocoll=True)

    # Weatherboards between the wall tops and the kisame / the slope, on every side that shows.
    def lat_top(side, t):
        """Underside of the sheets over the lateral side's point t (m from its min corner), minus 1 cm."""
        line_l, axis_l, _ = side_line(b, side)
        c = (b["x0"] if axis_l == "x" else b["y0"]) + t
        ds = []
        for hlow, _ in halves:
            ln, ax, _ = side_line(b, hlow)
            dx, dy = DOWN[hlow]
            ds.append(-(c - ln) * (dx if ax == "y" else dy))
        return zu(min(ds)) - 1

    for side in ("north", "south", "west", "east"):
        line_s, axis_s, (ix, iy) = side_line(b, side)
        base = b["x0"] if axis_s == "x" else b["y0"]
        length = dims[axis_s]
        Run = ue_dir(1, 0) if axis_s == "x" else ue_dir(0, 1)
        In = ue_dir(ix, iy)
        inset = line_s + (ix + iy) * (FILL_IN + BOARD_T / 2) / 100

        def plank(row, r0, r1, z0, z1):                    # a level board over r0..r1 (m along the side), z0..z1 cm
            tm = (r0 + r1) / 2
            lx, ly = (base + tm, inset) if axis_s == "x" else (inset, base + tm)
            X, Y = ue(lx, ly)
            put_board("Board_%s_%s%d_%d" % (bid, side[0].upper(), n_, row), beam, (X, Y, (z0 + z1) / 2), In, Run,
                      (0, 0, 1), (BOARD_T, (r1 - r0) * 100, z1 - z0), mats=[BOARD_MAT[beam]])

        for n_, (t0, t1, (kind, _)) in enumerate(sides[side][2]):
            if kind in ("wall", "edge") or t1 - t0 < 0.05:
                continue
            ta = t0 + (0.03 if t0 < 1e-6 else 0.0)
            tb = t1 - (0.03 if abs(t1 - length) < 1e-6 else 0.0)
            zb = T - 8
            if side in eave_top:                           # an eave or a high edge: one board up to the level top
                if eave_top[side] - zb >= 3:
                    plank(0, ta, tb, zb, eave_top[side])
                continue
            # A sloping side: the board up to the slope's lower end, then a wedge under each slope, its top 1 cm under
            # the sheets. A run that starts partway up a slope gets a level filler under its wedge.
            ends = (lat_top(side, ta), lat_top(side, tb))
            tm = ta if ends[0] > ends[1] else tb           # the high end, or the ridge on two slopes
            if gable:
                tr = sum(side_line(b, hl)[0] for hl, _ in halves) / 2 - base
                tm = tr if ta + 0.05 < tr < tb - 0.05 else tm
            zlev = min(ends)
            plank(0, ta, tb, zb, zlev)
            row = 1
            for p0, p1 in ((ta, tm), (tm, tb)):
                if p1 - p0 < 0.05:
                    continue
                h0, h1 = lat_top(side, p0), lat_top(side, p1)
                zw = min(h0, h1)
                if zw - zlev > 1:
                    plank(row, p0, p1, zlev, zw)
                    row += 1
                if max(h0, h1) - zw < 1:
                    continue
                hi, lo = (p1, p0) if h1 > h0 else (p0, p1)
                lx, ly = (base + hi, inset) if axis_s == "x" else (inset, base + hi)
                X, Y = ue(lx, ly)
                # The ramp lies on its side: local +Y up (the tall edge), local +Z from the tall end down the slope. Its
                # triangle faces' grain runs along local Z; stood upright it read as vertical streaks in a capture.
                Zw = tuple(c * (1 if lo > hi else -1) for c in Run)
                put_axes("Wedge_%s_%s%d_%d" % (bid, side[0].upper(), n_, row), RAMP, In, (0.0, 0.0, 1.0), Zw,
                         (BOARD_T / 100, (max(h0, h1) - zw) / 100, p1 - p0), (50.0, 0.0, 0.0), (X, Y, zw),
                         mats=[BOARD_MAT[beam]])
                row += 1
    return True


def ROOF_ROLL():
    return ROOF_RNG.random()


_roofs = {"metal": 0, "flat": 0}
for bid, b in BLOCKS.items():
    if b["roof"] == "metal" and metal_roof(bid, b):
        _roofs["metal"] += 1
    elif b["roof"] != "terrace":
        _roofs["flat"] += 1
print("roofs:", _roofs)

# --- Spawn doors ------------------------------------------------------------------------------------------------------
# A Favela end wall across each dead end: a door tile centred on the door, a plain tile each side (4.5 m alley + 1.1 m
# into the blocks either side), a plain upper storey, bands and trims. A dark backer sits behind the door.
SP = "BackAlleys/SpawnDoors"
spawns = []
for d in L["doors"]:
    n = FACE[d["face"]]
    yaw, (rx, ry), (nx, ny) = YAW[n], RUN[n], NORMAL[n]
    cx, cy = ue(d["x"], d["y"])
    # The alley's side walls meet this wall 2.25 m either side of the door; its trims follow the same inside-corner
    # rule as the blocks: a north/south-facing end wall's trims stop 7 cm short of the side walls, an east/west one's
    # run 10 cm into them.
    reach = 218.0 if n in ("north", "south") else 235.0
    trim_cut = 337.5 - reach
    mats = [pick(FACE_MATS)]                                # one material per storey of the end wall
    mats.append(mats[0] if rnd.random() < SAME_AS_GROUND else pick(FACE_MATS))
    for s in (0, 1):
        mat = mats[s]
        for k, off in enumerate((-337.5, -112.5, 112.5)):
            kind = "door" if s == 0 and k == 1 else "plain"
            favela_tile("%s_S%d_%d" % (d["id"], s, k), kind, mat, cx + rx * off, cy + ry * off, s * 400.0, n, 1.0,
                        TILE_W, s == 1, SP, -trim_cut if k == 0 else 0.0, -trim_cut if k == 2 else 0.0)
    for s in (0, 1):   # the part of the end wall that shows: the 4.5 m alley between its side walls
        wall_runs.append({"start": (cx - rx * 225, cy - ry * 225), "len": 450.0, "side": n, "z": s * 400.0,
                          "name": "%s_S%d" % (d["id"], s), "widths": [225.0, 225.0]})
    bx, by = cx - rx * 112.5 - nx * 40, cy - ry * 112.5 - ny * 40
    X0, X1 = sorted((bx, bx + rx * 225 - nx * 20))
    Y0, Y1 = sorted((by, by + ry * 225 - ny * 20))
    put(d["id"] + "_Backer", CUBE, X0, Y0, 0.0, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, 3.0), folder=SP,
        mat="interior")
    spawns.append({"label": "Spawn_" + d["id"], "loc": [round(cx + nx * 160, 1), round(cy + ny * 160, 1), 100.0],
                   "yaw": FACING[n], "door": [cx, cy], "n": [nx, ny], "run": [rx, ry]})


# --- Gallery deck (x15-27, y27-30, +4 m), posts, rails, stairs --------------------------------------------------------
GAL = "BackAlleys/Gallery"
# The rail. User 2026-11-04: "The gallert rail is the wrong model too" (it was SM_Wooden_part_03, a solid tapered plank).
# AsiaSlum's steel bar rail, the deck and stairs' own kit: local X -2.5..299.5 along the run, Y +-5, Z -3.9..174. 3 m long
# like the deck's modules; 1.78 m is a tall balcony's, so scaled to 1.05 m. You can see and shoot through it.
RAIL = AS + "SM_Rail_A_001"
RAIL_SX, RAIL_SZ, RAIL_X0, RAIL_Z0 = 300 / 302.0, 105 / 177.9, 2.5, 3.9
dk = L["deck"]
Xs, _ = ue(0, dk["y1"])            # south edge
Xn, _ = ue(0, dk["y0"])            # north edge
for i in range(int((dk["x1"] - dk["x0"]) / 3)):
    _, Ye = ue(dk["x0"] + 3 * (i + 1), 0)
    put("Gallery_Deck_%d" % i, AS + "SM_Floor_A_001", Xs, Ye, 380.0, 0, (1, 1, 1), folder=GAL)
    put("Gallery_Rail_S%d" % i, RAIL, Xs + 6, Ye - 300 + RAIL_X0 * RAIL_SX, 400.0 + RAIL_Z0 * RAIL_SZ, 90,
        (RAIL_SX, 1, RAIL_SZ), folder=GAL)
for i, lx in enumerate((dk["x0"] + 0.2, 19.0, 23.0, dk["x1"] - 0.2)):
    put("Gallery_Post_%d" % i, ME + "Favela/SM_Pillar_01", Xs + 21, ue(lx, 0)[1], 0.0, 0, (1, 1, 380 / 797.0), folder=GAL)
_, Yw = ue(dk["x0"], 0)
_, Yeast = ue(dk["x1"], 0)
put("Gallery_Rail_W", RAIL, Xs + RAIL_X0 * RAIL_SX, Yw + 6, 400.0 + RAIL_Z0 * RAIL_SZ, 0, (RAIL_SX, 1, RAIL_SZ), folder=GAL)
put("Gallery_Rail_E", RAIL, Xs + RAIL_X0 * RAIL_SX, Yeast - 6, 400.0 + RAIL_Z0 * RAIL_SZ, 0, (RAIL_SX, 1, RAIL_SZ), folder=GAL)
# User 2026-11-04: "The stairs you are using is too steep and unnavigable, use another" "or find a way to make it less
# steep". One SM_Stair_A_001 (natively 4.5 m run, 2.15 m rise, 25 deg) stretched to 5 x 4 m was 39 deg with 31 cm risers.
# Now two flights in line, close to native scale: STAIR_RUN 7 m for the 4 m rise, about 30 deg, 15 cm risers on 27 cm
# treads. The lower flight's flat top is the landing between them, with two pillars under it. The stair runs STAIR_RUN
# north from the layout's top edge (the layout's own 5 m rect is left as it is); the layout's clear ahead allows it.
STAIR_RUN = 700.0
STAIR = (STAIR_RUN / 2 / 451.3, 300 / 306.0, 200 / 214.6)
for st in L["stairs"]:   # top step at the pivot, downhill along local +X = north (the feet face north)
    Xtop, _ = ue(0, st["y1"])
    _, Yx1 = ue(st["x1"], 0)
    put(st["id"], AS + "SM_Stair_A_001", Xtop, Yx1 - 3, 400.0, 0, STAIR, folder=GAL)
    put(st["id"] + "_Lower", AS + "SM_Stair_A_001", Xtop + STAIR_RUN / 2, Yx1 - 3, 200.0, 0, STAIR, folder=GAL)
    for k, inset in enumerate((30.0, 270.0)):
        put("%s_Post%d" % (st["id"], k), ME + "Favela/SM_Pillar_01", Xtop + STAIR_RUN / 2 + 25.0, Yx1 - inset, 0.0, 0,
            (1, 1, 190.0 / 797.0), folder=GAL)


_mark = len(items)
# --- Cover, stand-ins, kiosk -------------------------------------------------------------------------------------------
def box(label, c, h, folder):
    X1, Y0 = ue(c["x0"], c["y0"])
    X0, Y1 = ue(c["x1"], c["y1"])
    put(label, CUBE, X0, Y0, 0.0, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, h / 100.0), folder=folder)


COV = "BackAlleys/Cover"
for c in L["cover"]:
    cxm, cym = ue((c["x0"] + c["x1"]) / 2, (c["y0"] + c["y1"]) / 2)
    if c["id"] == "jeepney":
        box("STANDIN_Jeepney", c, 260, "BackAlleys/StandIns")
    elif c["id"] == "tricycle":
        box("STANDIN_Tricycle", c, 150, "BackAlleys/StandIns")
    elif c["id"].startswith("barrier"):
        long_x = (c["x1"] - c["x0"]) > (c["y1"] - c["y0"])   # SM_Concrete_Block_01's 2.44 m runs along local Y
        put("Cover_" + c["id"], ME + "MiddleEast/SM_Concrete_Block_01", cxm, cym, 2.0, 0 if long_x else 90, folder=COV)
    elif c["id"].startswith("drums"):
        for k, (ox, oy, mesh) in enumerate([(-30, -25, "SM_Barrel_01"), (30, -20, "SM_Barrel_02"), (0, 35, "SM_Barrel_01")]):
            put("Cover_%s_%d" % (c["id"], k), PM + "Barrels_Set_01/" + mesh, cxm + ox, cym + oy, 0.0, k * 47, folder=COV)
    elif c["id"] == "kiosk":   # one storey, shop front facing north (its south side backs onto B19)
        K = "BackAlleys/Kiosk"
        kxf, kyw = ue(c["x0"], c["y0"])
        kxb, kye = ue(c["x1"], c["y1"])
        put("Kiosk_Front", AS + "SM_Shop_A_001", kxf, kye, 0, -90, (320 / 300.0, 1, 1), folder=K)
        put("Kiosk_Back", AS + "SM_HouseWall_A_001", kxb, kyw, 0, 90, (320 / 300.0, 1, 1), folder=K)
        put("Kiosk_West", AS + "SM_HouseWall_A_001_HalfA", kxf, kyw, 0, 180, (240 / 150.0, 1, 1), folder=K)
        put("Kiosk_East", AS + "SM_HouseWall_A_001_HalfA", kxb, kye, 0, 0, (240 / 150.0, 1, 1), folder=K)
        put("Kiosk_Roof", AS + "SM_MetalPlate_C_001", kxb - 20, kyw - 20, 400, 0, (280 / 200.0, 360 / 300.0, 1), folder=K)
        put("Kiosk_Core", CUBE, kxb + 20, kyw + 20, 0, 0, (1.4, 2.8, 3.9), folder=K, mat="interior")
        put("Kiosk_Awning", AS + "SM_Roof_A_002", kxf, kye, 330, -90, folder=K, nocoll=True)

if not COVER:
    del items[_mark:]
# --- Ground: invisible collision slab (the template floor's collision is smaller than it looks) -----------------------
put("Floor_Collision", CUBE, -2700, -3000, -50.0, 0, (54.0, 60.0, 0.495), folder="BackAlleys/Lids", mat="hidden")

_mark = len(items)
# --- Dressing -------------------------------------------------------------------------------------------------------------
DR = "BackAlleys/Dressing"
doors = 0
for label, kind, x, y, side, w in ground_pieces:   # awnings over shop fronts and every other door; tin patches
    (rx, ry), (nx, ny) = RUN[side], NORMAL[side]
    if kind == "shop":
        put(label + "_Awning", AS + "SM_Roof_A_002", x, y, 330.0, YAW[side], folder=DR, nocoll=True)
    elif kind == "door":
        doors += 1
        if doors % 2:
            put(label + "_Awning", AS + "SM_Roof_A_002", x, y, 270.0, YAW[side], (w / 300.0, 1, 1), folder=DR,
                nocoll=True)
    elif kind == "plain" and w >= 150 and rnd.random() < 0.15:
        s = rnd.uniform(20, w - 130)
        put(label + "_Tin", AS + rnd.choice(("SM_MetalPlate_A_001", "SM_MetalPlate_A_002")), x + rx * s + nx * 4,
            y + ry * s + ny * 4, 120.0, YAW[side], roll=rnd.uniform(-3, 3), folder=DR, nocoll=True)

# Wall grime (Favela: grime around openings at 0.9-2 m, dirt splash at the foot, streaks running down from the
# slab). Fewer than Favela's 0.6 per tile: each decal costs on the Deck, so doors and ground floors come first.
# A DecalActor's DecalSize is an extent (128, 256, 256): scale y is the height and z the width (roll 90), as Favela.
DC = "BackAlleys/Decals"
decals = []


def wall_decal(t, mat, along, h, sy, sz, depth=0.02):
    (nx, ny) = NORMAL[t["side"]]
    x, y = at(t["x"], t["y"], t["side"], along, 2)
    yaw = math.degrees(math.atan2(-ny, -nx))
    decals.append((t["label"] + "_Dcl%d" % len(decals), mat, x, y, t["z"] + h, yaw, (depth, sy, sz)))


order = sorted(wall_tiles, key=lambda t: (t["kind"] != "door", t["s"], rnd.random()))
for t in order:
    w = t["w"]
    if t["kind"] == "door" and rnd.random() < 0.8:
        wall_decal(t, rnd.choice(DECALS["grime"]), w / 2, rnd.uniform(120, 190), rnd.uniform(0.45, 0.65),
                   rnd.uniform(0.55, 0.75))
    if t["s"] == 0 and rnd.random() < 0.15:
        wall_decal(t, DECALS["dirt"][0], w / 2, 30, 0.2, w / 512.0, 0.03)
    if rnd.random() < 0.25:   # streaks running down from the band
        wall_decal(t, DECALS["dirt"][0], w / 2, 255, rnd.uniform(0.25, 0.4), w / 512.0 * 0.9, 0.03)
    if t["kind"] == "window" and rnd.random() < 0.5:   # streaks running down from the window sill
        wall_decal(t, DECALS["dirt"][0], 111 * t["w"] / TILE_W, 50, 0.2, 0.25, 0.03)
    if t["kind"] == "plain" and rnd.random() < 0.2:
        wall_decal(t, rnd.choice(DECALS["grime"] + DECALS["dirt"][1:]), rnd.uniform(60, w - 60),
                   rnd.choice((90, 200)), rnd.uniform(0.4, 0.6), rnd.uniform(0.45, 0.7))
# (placed after the dressing switch below, so they can be on while the rest of the dressing is off)

# Window-type air conditioners, now and then (user: "add ocasional air conditioners"): the AsiaSlum set as the pack's
# demo map mounts it, a bracket frame 10 cm off the wall face, the unit 10 cm further out and 10 cm lower, the fan
# grille 15 cm to the side. On plain tiles only, above head height on street floors.
acs = 0
for t in sorted((t for t in wall_tiles if t["kind"] == "plain" and t["w"] >= 150), key=lambda t: rnd.random()):
    if acs >= 12:
        break
    if rnd.random() > 0.5:
        continue
    acs += 1
    z = t["z"] + (230 if t["s"] == 0 else 150)
    along = t["w"] * rnd.uniform(0.35, 0.65)
    yaw = YAW[t["side"]]
    for part, ds, dn, dz in (("Frame", 0, 10, 0), ("Unit", 0, 20, -10), ("Fan", -15, 35, 37)):
        x, y = at(t["x"], t["y"], t["side"], along + ds, dn)
        put("AC_%d_%s" % (acs, part), AS + "SM_AirConditioner%s_A_001" % ("" if part == "Unit" else part),
            x, y, z + dz, yaw, folder=DR)

# TV antennas on wall brackets at parapet height, leaning (Favela: 2-4 per house, scale 0.42, roll -30).
ant = 0
for t in sorted((t for t in wall_tiles if t["top"] and t["s"] == 1), key=lambda t: rnd.random()):
    if ant >= 14:
        break
    ant += 1
    top = t["z"] + 400
    x, y = at(t["x"], t["y"], t["side"], t["w"] * rnd.uniform(0.3, 0.7), 0)
    yaw = YAW[t["side"]]
    put("Antenna_%d_Bracket" % ant, FV + "SM_AntennaSupportPart_02", x, y, top - 40, yaw, (0.42, 0.42, 0.42),
        folder=DR, nocoll=True)
    x, y = at(x, y, t["side"], 0, 30)
    put("Antenna_%d" % ant, FV + rnd.choice(("SM_Antenna_01", "SM_Antenna_02", "SM_Antenna_03")), x, y, top - 2,
        yaw - 40 + rnd.uniform(-15, 15), (0.42, 0.42, 0.42), folder=DR, roll=-30, nocoll=True)
for sp in spawns:   # two cables across each dead-end alley, and garbage by its side wall
    (cx, cy), (nx, ny), (rx, ry) = sp["door"], sp["n"], sp["run"]
    for k, dist in enumerate((200, 400)):
        put("Cable_%s_%d" % (sp["label"][-2:], k), AS + "SM_Cable_A_005", cx + nx * dist, cy + ny * dist, 660 + 70 * k,
            90 if rx == 0 else 0, (450 / 380.0, 1, 1), folder=DR, nocoll=True)
    gx, gy = cx + nx * 250 - rx * 170, cy + ny * 250 - ry * 170
    put("Garbage_%s_a" % sp["label"][-2:], ME + "MiddleEast/SM_Garbage_bag_01", gx, gy, 0, rnd.uniform(0, 360), folder=DR)
    put("Garbage_%s_b" % sp["label"][-2:], ME + "MiddleEast/SM_Garbage_bag_green_03", gx + nx * 60, gy + ny * 60, 0,
        rnd.uniform(0, 360), folder=DR)
    put("Garbage_%s_c" % sp["label"][-2:], PM + "CardboardSet_01/SM_CardboardBox_01", gx + nx * 120, gy + ny * 120, 0,
        rnd.uniform(0, 360), folder=DR)
CLOTHES = ["SM_clothes_A_02", "SM_clothes_A_03", "SM_clothes_A_04", "SM_clothes_A_05", "SM_clothes_B_01",
           "SM_clothes_B_02", "SM_clothes_B_03"]
lines = 0
for bid, side, a, c in upper_runs:   # laundry across alleys 3-6 m wide, from upper-floor faces
    if lines >= 7:
        break
    mx, my = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2
    nlx, nly = LNORM[side]
    gap = next((g * 0.5 for g in range(1, 14) if solid(mx + nlx * g * 0.5, my + nly * g * 0.5, 1)), None)
    if not gap or not (3.0 <= gap <= 6.0) or rnd.random() < 0.35:
        continue
    lines += 1
    X, Y = ue(mx, my)
    nx, ny = NORMAL[side]
    yaw = 90 if side == "east" else 180
    put("Laundry_Line_%d" % lines, AS + "SM_Rope_A_001", X, Y, 520, yaw, (gap * 100 / 125.0, 1, 1), folder=DR, nocoll=True)
    for j in range(int((gap - 0.6) / 1.1) + 1):
        put("Laundry_%d_%d" % (lines, j), ME + "MiddleEast/" + rnd.choice(CLOTHES), X + nx * (70 + 110 * j),
            Y + ny * (70 + 110 * j), 515, yaw - 90, folder=DR, nocoll=True)
put("Wires_Web", ME + "MiddleEast/SM_Wires_01", -190, -1830, 50, 0, folder=DR, nocoll=True)
big = [b for b in BLOCKS.values() if b["storeys"] == 2 and (b["x1"] - b["x0"]) * (b["y1"] - b["y0"]) >= 30]
for k, b in enumerate(big[::2]):
    put("RoofTank_%d" % k, ME + "MiddleEast/SM_Water_Tank_0%d" % (k % 3 + 1),
        *ue((b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2), 800, rnd.uniform(0, 90), folder=DR)
for k, b in enumerate(big[1::3]):   # Favela's roof water drum on a stand
    X, Y = ue((b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2)
    put("RoofDrum_%d_Stand" % k, FV + "SM_Stand_01", X, Y, 800, rnd.uniform(0, 90), folder=DR)
    put("RoofDrum_%d" % k, FV + "SM_Barrel_01", X, Y, 860, rnd.uniform(0, 360), folder=DR)
    put("RoofDrum_%d_Cap" % k, FV + "SM_Barrel_Cap_2", X, Y, 946, rnd.uniform(0, 360), folder=DR)
sx, _ = ue(0, 6)   # the sari-sari front on B2's south face, west part (x16.5-21)
put("SariSari_Sign", AS + "SM_Sign_A_001", sx - 10, ue(18, 0)[1], 300, 90, folder=DR, nocoll=True)
for k, (lx, z) in enumerate([(16.9, 0), (17.45, 0), (17.17, 33)]):
    put("SariSari_Crate_%d" % k, PM + "Plastic_Crate_Set_01/SM_Plastic_Crate_01", sx - 110, ue(lx, 0)[1], z, 0, folder=DR)
put("SariSari_Rice_0", PM + "RiceBags_01/SM_Rice_Bag_Full_01", sx - 110, ue(20.4, 0)[1], 0, 90, folder=DR)
put("SariSari_Chair", PM + "MonoBloc_Chairs_01/SM_Monobloc_Chair_01", sx - 170, ue(19.6, 0)[1], 0, 200, folder=DR)

if not DRESSING:
    del items[_mark:]
# Stains (user: "I want stain decals next"; then "The decals you are currently using is meant to be stretched to the
# entire wall"). Favela's decal masks (Tools/LevelGen/analysis/inspect_decals_ue.py) are whole-wall layers:
#   T_decal_07 (MI_Decal_Dirt_06 / _08): drip streaks running down from a hard top edge at ~24% of the height.
#   T_decal_08 (MI_Decal_Dirt_07): rising damp, solid at the bottom, fading out by ~45% of the height.
#   T_decal_02 (MI_Decal_02/04-08): a rough-edged full-wall colour wash - left out, it would recolour the face.
# Each storey of each wall run gets drips whose top edge sits under the band (z +300); street floors also get rising
# damp to ~1.2 m. Decals are 23% wider than their stretch of wall so neighbours overlap and the ragged mask sides fall
# past the run ends. A DecalActor's DecalSize is an extent (128, 256, 256): scale = size / 512 (y height, z width,
# roll 90); 3 cm deep each way.
DRIPS = [(FM + "Decals/MI_Decal_Dirt_08", 1.0)]   # user: "use decal dirt 8" (the darker drips; was Dirt_06)
DAMP = FM + "Decals/MI_Decal_Dirt_07"
# Calibrated on the user's hand-placed decal (2026-11-03, "fix the alignment, first one is yours, second one is mine"):
# 497.5 cm tall, 1.23 x the wall's width, the mask's hard top edge at +292 - tucked behind the trim's lower half - and
# the streaks reaching the floor.
DRIP_H, DRIP_EDGE, DRIP_EDGE_Z = 380.0, 0.24, 292.0   # box height (was 500, user: "shorten the length more"); mask edge (fraction from the top); edge height
DRIP_H_SINGLE = 230.0                                  # box height when the drips cover one tile only (was 300)
DRIP_EDGE_BAND = 304.0                                 # edge height behind a protruding band, whose underside is at +300
STAIN_WIDEN = 1.12                                     # decal width / stretch: the mask's ragged sides (5% each) end at the face edge
DAMP_H = 220.0
P_DRIPS, P_DAMP = 0.35, 0.0  # P_DRIPS: chance per wall run (face + storey);  # user: "not all of them need the dirt decal"; rising damp off ("only use the dirt decal")
# Which wall tiles get drips: each tile with P_DRIPS; neighbouring picked tiles share one decal stretched across up to
# STAIN_SPAN of them (user 2026-11-03: "the using decal on adjacent walls, stretch the decal accross up to 3 walls
# instead", then "its actually up to 4 walls, the ammount of walls covered should determine the length"), so no two
# drip decals sit side by side on the same run. The box height grows with the tiles covered: DRIP_H_SINGLE for one,
# DRIP_H for STAIN_SPAN, evenly between.
STAIN_SPAN = 4   # user: "its actually up to 4 walls"


def drips_on(r):
    """Drips across one wall run, in groups of at most STAIN_SPAN tiles. Returns how many decals."""
    full = r["widths"]
    (nx, ny) = NORMAL[r["side"]]
    yaw = math.degrees(math.atan2(-ny, -nx))   # projects into the wall
    n = len(full)
    groups = math.ceil(n / STAIN_SPAN)
    bounds = [round(g * n / groups) for g in range(groups + 1)]
    edges = [0.0]
    for w in full:
        edges.append(edges[-1] + w)
    for g in range(groups):
        i, j = bounds[g], bounds[g + 1] - 1         # tiles i..j
        a, b = edges[i], edges[j + 1]
        x, y = at(r["start"][0], r["start"][1], r["side"], (a + b) / 2, 2)
        hgt = DRIP_H_SINGLE + (DRIP_H - DRIP_H_SINGLE) * (j - i) / (STAIN_SPAN - 1)
        top = r["z"] + DRIP_EDGE_Z + DRIP_EDGE * hgt     # puts the mask's edge behind the trim
        put("Drips_%s_%d" % (r["name"], g), pick(DRIPS), x, y, top - hgt / 2, yaw,
            (0.03, hgt / 512.0, (b - a) * STAIN_WIDEN / 512.0), folder=DC, roll=90, decal=True)
    return groups


if STAINS:
    n_st = 0
    for r in wall_runs:
        # Whole faces only (user: "keep the stains consistent with the face and material, no half wall decals" ... "half
        # block i mean" ... "you are leaving a section undecaled" - pointing at a bare half tile): a run (one face, one
        # storey, one material) gets drips across every tile, the half tile included, or none. Decal edges sit on tile
        # edges, so no block is half covered. Longer runs split into equal groups of at most STAIN_SPAN tiles.
        if rnd.random() < P_DRIPS:
            n_st += drips_on(r)
    print("stains:", n_st, "decals over", len(wall_runs), "wall runs")
# --- Gameplay -------------------------------------------------------------------------------------------------------
pickups = []
P = {"rifle": ("BP_WeaponPickup", 60, "/Game/ThirdPerson/Blueprints/BP_AssaultRifle"),
     "rifle ammo": ("BP_AmmoPickup_Rifle", 20, None), "shotgun": ("BP_PumpShotgun_Pickup", 60, None),
     "2x grenade": ("BP_AmmoPickup_Grenade", 20, None), ".45 ammo": ("BP_AmmoPickup_45", 20, None)}
counts = {}
for p in L["pickups"]:
    asset, z, weapon = P[p["what"]]
    base = p.get("z", 0) * 100.0
    n = 2 if p["what"] == "2x grenade" else 1
    for k in range(n):
        counts[p["what"]] = counts.get(p["what"], 0) + 1
        x, y = ue(p["x"] + 0.6 * k, p["y"])
        label = "Pickup_" + p["what"].replace(" ", "").replace(".", "").replace("2x", "") + "_%d" % counts[p["what"]]
        pickups.append({"label": label, "asset": PK + asset, "loc": [x, y, base + z], "weapon": weapon})
if not PICKUPS:
    pickups = []
wander = [{"label": "Wander_" + w["id"], "loc": list(ue(w["x"], w["y"])) + [100.0]} for w in L["wander"]]
# The level's opening music (user, 2026-11-04: "a bgm manager on the backalley too"): an AMusicTrigger that fires as the level
# starts, set like Lvl_Linear's. It stands in BackAlleys/Gameplay, which a rebuild keeps. Where it stands doesn't matter.
music = {"label": "Music_Start", "track": "/Game/Audio/BGM/DarkCrimes",
         "loc": list(ue(L["player_start"]["x"], L["player_start"]["y"])) + [100.0]}
gameplay = {"player_start": list(ue(L["player_start"]["x"], L["player_start"]["y"])) + [100.0], "spawns": spawns,
            "pickups": pickups, "wander": wander, "music": music,
            "floor": {"loc": [0, 0, 0], "scale": [5.6, 6.4, 1.0]},
            "nav": {"loc": [0, 0, 400], "scale": [1.272, 1.494, 1.0]},
            "lmv": {"loc": [0, 0, 400], "scale": [26.0, 29.0, 7.0]}}

for f in os.listdir(OUT):
    if f.startswith("plan3_"):
        os.remove(OUT + f)
# Building floors. User 2026-11-04: "can we put a floor on the buildings. currently the door go all the way to the road
# floor ... There is usually "riser" below the door that lifts it off the ground. The solution to this is to put the
# buildings on top of a "building floor"". Every house and door end wall stands on a concrete slab FLOOR_H tall, proud by
# FLOOR_OUT over open ground (not into a neighbour or past the arena edge). One height for all, applied last, so every
# relation between houses (covers, corners, trims) holds. The road, gallery deck, stairs and gameplay points stay put.
FLOOR_H, FLOOR_OUT = 18.0, 8.0
FLOORS = "BackAlleys/Floors"
LIFTED = (BLK, "BackAlleys/Lids", "BackAlleys/Terraces", RF, "BackAlleys/SpawnDoors", "BackAlleys/Decals")
for p in items:
    if p["folder"] in LIFTED and p["label"] != "Floor_Collision":
        p["loc"][2] = round(p["loc"][2] + FLOOR_H, 1)


def floor_box(label, a0, b0, a1, b1):
    """A slab over layout metres a0..a1 east, b0..b1 south; 5 cm into the road."""
    X0, Y0 = ue(a0, b1)
    X1, Y1 = ue(a1, b0)
    put(label, CUBE, X0, Y0, -5.0, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, (FLOOR_H + 5.0) / 100.0), folder=FLOORS,
        mats=[CONC])


_m = FLOOR_OUT / 100.0
for bid, b in BLOCKS.items():
    ivs = {side: side_intervals(b, side, lambda c: c) for side in ("north", "south", "west", "east")}
    out = {side: _m if all(c == 0 for _, _, c in iv) else 0.0 for side, iv in ivs.items()}
    floor_box("Floor_" + bid, b["x0"] - out["west"], b["y0"] - out["north"], b["x1"] + out["east"], b["y1"] + out["south"])
    for side, iv in ivs.items():                    # a side only partly open: strips along the open parts
        if out[side]:
            continue
        for n_, (t0, t1, c) in enumerate(iv):
            if c != 0 or t1 - t0 < 0.01:
                continue
            if side in ("north", "south"):
                a0 = b["x0"] + t0 - (out["west"] if t0 < 1e-6 else 0.0)
                a1 = b["x0"] + t1 + (out["east"] if abs(b["x0"] + t1 - b["x1"]) < 1e-6 else 0.0)
                b0, b1 = (b["y0"] - _m, b["y0"]) if side == "north" else (b["y1"], b["y1"] + _m)
            else:
                b0 = b["y0"] + t0 - (out["north"] if t0 < 1e-6 else 0.0)
                b1 = b["y0"] + t1 + (out["south"] if abs(b["y0"] + t1 - b["y1"]) < 1e-6 else 0.0)
                a0, a1 = (b["x0"] - _m, b["x0"]) if side == "west" else (b["x1"], b["x1"] + _m)
            floor_box("FloorStrip_%s_%s%d" % (bid, side[0].upper(), n_), a0, b0, a1, b1)
for d in L["doors"]:                                # the door end walls: across their 4.5 m alley, tucked into the sides
    n = FACE[d["face"]]
    nx_, ny_ = LNORM[n]
    if n in ("north", "south"):
        floor_box("Floor_" + d["id"], d["x"] - 2.32, min(d["y"], d["y"] + ny_ * _m) - (0.25 if ny_ > 0 else 0.0),
                  d["x"] + 2.32, max(d["y"], d["y"] + ny_ * _m) + (0.25 if ny_ < 0 else 0.0))
    else:
        floor_box("Floor_" + d["id"], min(d["x"], d["x"] + nx_ * _m) - (0.25 if nx_ > 0 else 0.0), d["y"] - 2.32,
                  max(d["x"], d["x"] + nx_ * _m) + (0.25 if nx_ < 0 else 0.0), d["y"] + 2.32)

# Hollow blocks on faces with no door or window (labels: <house>_<side letter><storey>_...).
if ONE_MATERIAL:
    _faces = {}
    for p in items:
        parts = p["label"].split("_")
        if p["folder"] != BLK or len(parts) < 3 or parts[1][:1] not in "NSEW" or not parts[1][1:].isdigit():
            continue
        house = parts[0][:-1] if parts[0].endswith("b") and parts[0][:-1] in BLOCKS else parts[0]
        _faces.setdefault((house, parts[1][0]), []).append(p)
    _clear = [f for f, ps in _faces.items() if all(p["asset"].split("/")[-1] in PLAIN_WALL for p in ps)]
    _hollow = [f for f in _clear if WALL_MIX_RNG.random() < P_HOLLOW]
    for f in _hollow:
        for p in _faces[f]:
            if p["mats"] and p["mats"][0] == WALL_MAT and p["asset"].split("/")[-1].startswith("SM_Wall_Tile"):
                p["mats"] = [HOLLOW] * len(p["mats"])
    print("hollow-block faces: %d of %d windowless (%d faces in all):" % (len(_hollow), len(_clear), len(_faces)),
          sorted(h + "_" + d for h, d in _hollow))
    # Paint, on what the hollow blocks left (see P_PAINTED). Colours go round a shuffled list, so they spread evenly and
    # houses next to each other in the list differ.
    _hset, _cset = set(_hollow), set(_clear)
    _chosen = [h for h in dict.fromkeys(f[0] for f in _faces) if PAINT_RNG.random() < P_PAINTED]
    _draw_colour = shuffle_bag(PAINT_RNG, PAINT_COLOURS)
    _paint = {}
    for h in _chosen:
        mi = BM + "MI_BackAlleys_PaintedWall_" + _draw_colour()
        sides_ = [f for f in _faces if f[0] == h and f not in _hset]
        picked = [f for f in sides_ if f not in _cset or PAINT_RNG.random() < P_PAINT_SIDE] or sides_[:1]
        for f in picked:
            _paint[f] = mi
    _contrast = {h for h in _chosen if BAND_MIX_RNG.random() < P_BAND_CONTRAST}
    for f, mi in _paint.items():
        for p in _faces[f]:
            a_ = p["asset"].split("/")[-1]
            if p["mats"] and (a_ in ("SM_Wall_Tile_01", "SM_Wall_Tile_Blue", "SM_Wall_Tile_03", "SM_WallDoor_01",
                                     "SM_Wall_Windows_01") or (a_ == "SM_Wall_14" and f[0] not in _contrast)):
                p["mats"] = [mi] * len(p["mats"])
    _colour = {f[0]: mi for f, mi in _paint.items()}
    for p in items:                                 # parapets follow their side, or the house where no wall shows there
        parts = p["label"].split("_")
        if parts[0] == "Parapet" and p["mats"]:
            house = parts[1][:-1] if parts[1].endswith("b") and parts[1][:-1] in BLOCKS else parts[1]
            f = (house, parts[2][0])
            if f in _paint or (f not in _faces and house in _colour):
                p["mats"] = [_paint.get(f, _colour.get(house))] * len(p["mats"])
    # Between the floors, a building has one of three treatments, on all its faces. User 2026-11-04: "so the building will
    # either has 1. No borders, 2. A border 3. A portruding band"; "if the paintjob for the whole face is the same, remove
    # the border"; "the band between the 1st and 2nd floor, not the top floor". So a painted house, whose band matches, gets
    # none or the protruding band, and an unpainted house any of the three.
    # Shuffle bags, so they spread evenly in no visible order. The border is each storey's Trim300 but the top one's.
    # Protruding band: BAND_OUT clears the trims' 7 cm (at 5 cm they hid it: "i cant see it"). It gets thicker, not moved:
    # the back stays 20 cm behind the face. Not on houses touching the gallery (they get no border): it would stand above
    # the deck floor and in the stairs' headroom. At an outside corner with another protruding band, it meets it as the trims
    # do: east/west runs past the corner to flush with that band's face, north/south stops at that band's back, 20 cm in
    # (t0/t1 say which: > 0 and -9; see corner_adjust). With a flush face there, it stops just short of the corner.
    _draw_three = shuffle_bag(BAND_RNG, ("none", "border", "proud"))
    _draw_two = shuffle_bag(BAND_RNG, ("none", "proud"))
    _style = {}
    for h in dict.fromkeys(f[0] for f in _faces):
        if BLOCKS[h]["storeys"] < 2:
            continue
        st = "border" if h in _contrast else (_draw_two() if h in _colour else _draw_three())
        if st == "proud" and (_near(BLOCKS[h], L["deck"], 0.05) or any(_near(BLOCKS[h], g, 0.05) for g in L["stairs"])):
            st = "none"
        _style[h] = st


    def _between_floors(p, house):
        return int(p["label"].split("_")[1][1:]) < BLOCKS[house]["storeys"] - 1


    _gone = {id(p) for f, ps in _faces.items() if _style.get(f[0], "border") != "border" for p in ps
             if p["label"].endswith("_Trim300") and _between_floors(p, f[0])}
    items[:] = [p for p in items if id(p) not in _gone]
    _proud = {f for f, ps in _faces.items() if _style.get(f[0]) == "proud"
              and any(p["label"].endswith("_Band") and _between_floors(p, f[0]) for p in ps)}
    _dir_letter = {(1, 0): "E", (-1, 0): "W", (0, 1): "S", (0, -1): "N"}


    def _band_end(t, house, along):
        if t > 0 or t == -9.0:                      # an outside corner (see corner_adjust)
            if (house, _dir_letter[along]) not in _proud:
                return 9.0
            return 10.0 + BAND_OUT if t > 0 else -10.0
        return 0.0


    for f in _proud:
        for p in _faces[f]:
            if p["label"].endswith("_Band") and _between_floors(p, f[0]):
                side_, px_, py_, w_, t0_, t1_, sh_ = p["band"]
                rx_, ry_ = RUN[side_]
                ahead = (int(ry_), int(-rx_))               # the run's direction, in layout axes
                b0_ = _band_end(t0_, f[0], (-ahead[0], -ahead[1]))
                b1_ = _band_end(t1_, f[0], ahead)
                x_, y_ = at(px_, py_, side_, -b0_, BAND_OUT)
                p["loc"][0], p["loc"][1] = round(x_, 1), round(y_, 1)
                p["scale"][0] = round((20.0 + BAND_OUT) / 20.0, 4)
                p["scale"][1] = round((w_ + b0_ + b1_ + TILE_LAP) / 200.0, 4)
    # Drips, after the treatments. User 2026-11-04: "you need to reevaluate the placements of Dirt decals, becuase of the new
    # border and band rules". Their hard top edge sat at +292, tucked behind the border, which is what's gone between floors:
    # - protruding band: the edge goes up behind the band (DRIP_EDGE_BAND), so the streaks come out from under the ledge;
    # - no border: nothing can hide it, and dirt doesn't start mid-wall, so the lower floors' drips go. A face that had them
    #   gets drips at the top floor instead, under the top border, if it has none there.
    # A border, and every top floor, stay as they were (the top storey's Trim300 is always there).
    _moved, _cut, _added = 0, 0, 0
    _had_low, _has_top = set(), set()
    _keep = []
    for p in items:
        parts = p["label"].split("_")
        if p["folder"] == DC and parts[0] == "Drips" and len(parts) > 3:
            h = parts[1][:-1] if parts[1].endswith("b") and parts[1][:-1] in BLOCKS else parts[1]
            st = _style.get(h)
            f = (h, parts[2][0])
            if st and int(parts[2][1:]) < BLOCKS[h]["storeys"] - 1:
                if st == "proud":
                    p["loc"][2] = round(p["loc"][2] + DRIP_EDGE_BAND - DRIP_EDGE_Z, 1)
                    _moved += 1
                elif st == "none":
                    _had_low.add(f)
                    _cut += 1
                    continue
            elif st:
                _has_top.add(f)
        _keep.append(p)
    items[:] = _keep
    for h, d in sorted(_had_low - _has_top):
        for r in wall_runs:
            q = r["name"].split("_")
            if q[0] == h and q[1] == d + str(BLOCKS[h]["storeys"] - 1):
                n0 = len(items)
                _added += drips_on(r)
                for p in items[n0:]:
                    p["loc"][2] = round(p["loc"][2] + FLOOR_H, 1)
    print("drips: %d moved up behind protruding bands, %d lower-floor ones cut, %d added at the top floor" % (
        _moved, _cut, _added))
    print("between the floors, of %d multi-storey houses: %s; %d border pieces removed; contrasting bands on %d of %d "
          "painted houses" % (len(_style), dict(sorted(__import__("collections").Counter(_style.values()).items())),
                              len(_gone), len(_contrast), len(_chosen)))
    _letter = {(1, 0): "E", (-1, 0): "W", (0, 1): "S", (0, -1): "N"}
    _ncol = 0
    for k, ((lx, ly, _dirs), col) in enumerate(sorted(COLUMNS.items())):
        s1, s2 = (_letter[d] for d in col["dirs"])
        for bid, b in BLOCKS.items():
            h = bid[:-1] if bid.endswith("b") and bid[:-1] in BLOCKS else bid
            if (h, s1) not in _paint or (h, s2) not in _paint or _paint[(h, s1)] != _paint[(h, s2)]:
                continue
            cx = b["x1"] if "E" in (s1, s2) else b["x0"]
            cy = b["y1"] if "S" in (s1, s2) else b["y0"]
            if abs(cx - lx) < 1e-3 and abs(cy - ly) < 1e-3:
                for p in items:
                    if p["label"].startswith("Column_%d_" % k):
                        p["mats"] = [_paint[(h, s1)]]
                        _ncol += 1
                break
    print("paint: %d of %d houses; faces %d painted, %d hollow, %d bare; %d columns" % (
        len(_chosen), len(set(f[0] for f in _faces)), len(_paint), len(_hollow), len(_faces) - len(_paint) - len(_hollow),
        _ncol))

# Awnings over windows and doors. User 2026-11-04 (a photo of a Manila street): "awnings is next, help me make these, see if
# you can use existing sets", "we place them in windows and doors". A sloped sheet held off the wall by diagonal brackets, as
# wide as the opening plus 19 cm a side, reaching out AWN_D, its top under the trim line. Three kinds from existing pieces, one
# per house: "panel", AsiaSlum's SM_Roof_A_002 (a sheet on a rusty frame with brackets), or MiddleEast's SM_awning_base_01
# frame under either a corrugated SM_MetalPlate_A_003/004 in a sheet finish ("corrugated") or a thin galvanised sheet
# ("plain"). Not SM_awning_01: 4.7k tris each. For now only "corrugated" (user: "you can use a base, then put a currogated
# roof on it", "as a try"); AWN_KINDS brings the others back. "make the awning house wide, If a house uses awnings in one
# window, then use it for all IN THAT FACE": a house has one kind or none, and each face has them on all its openings or on
# none. Kinds from a bag, and P_AWN_FACE keeps some faces bare. Not on doors above the street (balconies and the deck), under a balcony's roof, where a neighbour or the
# gallery stands within reach, or on the deck. No collision. See analysis/awning_shape_ue.py for the shapes.
AWN = "BackAlleys/Awnings"
AWN_D = 90.0
P_AWN_HOUSE, P_AWN_FACE = 0.75, 0.7
_awn_face = {}
AWN_RNG = random.Random(139)
AWN_PLATES = (AS + "SM_MetalPlate_A_003", AS + "SM_MetalPlate_A_004")
AWN_KINDS = ("corrugated",)
_draw_awning = shuffle_bag(AWN_RNG, AWN_KINDS)
_awn_finish = {}
_awn_kind = {}
_awn_count = {"panel": 0, "corrugated": 0, "plain": 0, "reach": 0}
_yaw_side = {0: "east", 180: "west", 270: "north", 90: "south"}


def awn_clear(lx, ly, z, house):
    """Nothing stands where the awning reaches: a neighbour up to this height, the deck, or the 7 m stairs."""
    if not (0 < lx < W and 0 < ly < H):
        return False
    me = BLOCKS.get(house)
    if cover_top(lx, ly, me) > z - 60:
        return False
    d = L["deck"]
    if d["x0"] - 0.3 < lx < d["x1"] + 0.3 and d["y0"] - 0.3 < ly < d["y1"] + 0.3:
        return False
    return not any(g["x0"] - 0.3 < lx < g["x1"] + 0.3 and g["y0"] - 2.3 < ly < g["y1"] + 0.3 for g in L["stairs"])


def awning(p, house, kind):
    side = _yaw_side[round(p["rot"][1]) % 360]
    px, py, z = p["loc"]
    sx = p["scale"][0]
    w = 150.0 * sx
    cs = 112.0 * sx
    (nx, ny), (rx, ry) = NORMAL[side], RUN[side]
    label = p["label"] + "_Awn"
    if kind == "panel":
        sa, sd, sz = w / 324.1, AWN_D / 220.9, 0.55
        x, y = at(px, py, side, cs - w / 2 + 6.1 * sa, 0.5 + 2.2 * sd)
        put(label, AS + "SM_Roof_A_002", x, y, z + 250.0, YAW[side], (sa, sd, sz), folder=AWN, nocoll=True)
        return
    sa, sd, sz = w / 419.2, AWN_D / 136.3, 0.4
    x, y = at(px, py, side, cs, 0.5 + 0.2 * sd)
    put(label, ME + "MiddleEast/SM_awning_base_01", x, y, z + 248.0, YAW[side] - 90, (sd, sa, sz), folder=AWN, nocoll=True)
    ztop, zfront = z + 248.0 + 59.9 * sz, z + 248.0 - 17.0 * sz    # the frame's top at the wall and at the front
    run_ = (float(rx), float(ry), 0.0)
    ang = math.atan2(ztop - zfront, AWN_D)
    c, s_ = math.cos(ang), math.sin(ang)
    up_slope = (-nx * c, -ny * c, s_)
    normal = (nx * s_, ny * s_, c)
    length = (AWN_D + 6.0) / c
    x0, y0 = at(px, py, side, cs, 0.5)
    if kind == "corrugated":
        top = v_add((x0, y0, ztop), normal, PLATE_T / 2 + 0.5)
        if house not in _awn_finish:               # one finish per house, so its awnings match
            _awn_finish[house] = AWN_RNG.choices([g for g, _ in SHEET_MIX], [q for _, q in SHEET_MIX])[0]
        f = _awn_finish[house]
        put_axes(label + "2", AWN_RNG.choice(AWN_PLATES), run_, normal, up_slope, (w / PLATE_W, 1.0, length / 164.9),
                 (0.0, 0.0, 0.0), top, mats=[SHEET_MATS[f]], nocoll=True)
    else:
        centre = v_add(v_add((x0, y0, ztop), up_slope, -length / 2), normal, 1.2)
        put_board(label + "2", CUBE, centre, up_slope, run_, normal, (length, w, 1.5), mats=[FLASH_MAT], nocoll=True)
    items[-1]["folder"] = AWN


for p in list(items):
    a_ = p["asset"].split("/")[-1]
    if a_ not in ("SM_WallDoor_01", "SM_Wall_Windows_01") or p["folder"] not in (BLK, "BackAlleys/SpawnDoors"):
        continue
    parts = p["label"].split("_")
    h = parts[0][:-1] if parts[0].endswith("b") and parts[0][:-1] in BLOCKS else parts[0]
    storey = int(parts[1][1:]) if parts[1][1:].isdigit() else 0
    door = a_ == "SM_WallDoor_01"
    if h not in _awn_kind:
        _awn_kind[h] = _draw_awning() if AWN_RNG.random() < P_AWN_HOUSE else None
    side = _yaw_side[round(p["rot"][1]) % 360]
    if (h, side) not in _awn_face:
        _awn_face[(h, side)] = AWN_RNG.random() < P_AWN_FACE
    if _awn_kind[h] is None or not _awn_face[(h, side)] or (door and storey > 0):
        continue
    if h in BLOCKS and storey > 0 and BLOCKS[h].get("balcony") == side:
        continue
    X, Y = at(p["loc"][0], p["loc"][1], side, 112.0 * p["scale"][0], AWN_D + 10.0)
    if not awn_clear(Y / 100.0 + 27.0, 24.0 - X / 100.0, p["loc"][2] - FLOOR_H + 270.0, h):
        _awn_count["reach"] += 1
        continue
    awning(p, h, _awn_kind[h])
    _awn_count[_awn_kind[h]] += 1
print("awnings:", _awn_count, "; houses:", dict(__import__("collections").Counter(_awn_kind.values())))
for p in items:
    p.pop("band", None)
chunks = [items[i:i + 140] for i in range(0, len(items), 140)]
for i, c in enumerate(chunks):
    json.dump(c, open(OUT + "plan3_%d.json" % i, "w"), separators=(",", ":"))
json.dump(gameplay, open(OUT + "plan3_gameplay.json", "w"), separators=(",", ":"))
from collections import Counter
print(len(items), "items in", len(chunks), "chunks;", dict(Counter(p["folder"] for p in items)))
print("max chunk", max(os.path.getsize(OUT + "plan3_%d.json" % i) for i in range(len(chunks))), "bytes; laundry", lines)
print("exposed:", {k: sorted(v) for k, v in exposed_sides.items()})

# Check: open cells along the arena edge must be inside a door's end wall (door point +-2.25 m).
open_edge = []
for k in range(int(W / 1.5)):
    for ly_in, ly_edge in ((0.75, 0), (H - 0.75, H)):
        lx = (k + 0.5) * 1.5
        if not solid(lx, ly_in, 0) and not any(abs(d["x"] - lx) <= 2.25 and d["y"] == ly_edge for d in L["doors"]):
            open_edge.append((lx, ly_edge))
for k in range(int(H / 1.5)):
    for lx_in, lx_edge in ((0.75, 0), (W - 0.75, W)):
        ly = (k + 0.5) * 1.5
        if not solid(lx_in, ly, 0) and not any(abs(d["y"] - ly) <= 2.25 and d["x"] == lx_edge for d in L["doors"]):
            open_edge.append((lx_edge, ly))
print("open edge cells without a door:", open_edge)
