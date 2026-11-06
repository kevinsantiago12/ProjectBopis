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
PHYS = "/Game/ImpactsVFXVol1/Materials/Physical_Materials/"
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
    b["eaves"] = [low, high] if gable else [low]           # where it drains to, for the downpipes
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
    items[-1]["phys"] = PHYS + "Concrete"          # its material is shared with the street lamps, which are Metal
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
        items[-1]["phys"] = PHYS + "Concrete"      # its material is shared with the street lamps, which are Metal


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
        put(label, AS + "SM_Roof_A_002", x, y, z + 250.0, YAW[side], (sa, sd, sz), folder=AWN)
        return
    sa, sd, sz = w / 419.2, AWN_D / 136.3, 0.4
    x, y = at(px, py, side, cs, 0.5 + 0.2 * sd)
    put(label, ME + "MiddleEast/SM_awning_base_01", x, y, z + 248.0, YAW[side] - 90, (sd, sa, sz), folder=AWN)
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
                 (0.0, 0.0, 0.0), top, mats=[SHEET_MATS[f]])
    else:
        centre = v_add(v_add((x0, y0, ztop), up_slope, -length / 2), normal, 1.2)
        put_board(label + "2", CUBE, centre, up_slope, run_, normal, (length, w, 1.5), mats=[FLASH_MAT])
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
# --- Building dressing: something to see on the blank tiles ----------------------------------------------------------------
# User 2026-11-04: "do downpipes and window air conditioning. and the overhang rooms, ply patches. See what you can do about
# this yourself. There are alot of blank face tiles so I want them to see more (The hollow block faces can remain empty." ...
# "door steps and vent blocks too". All of it goes on plain tiles of runs that show (not buried), hollow-block faces stay empty.
# Each kind has its own random sequence, so nothing else moves, and picks from bags with exceptions: some houses have none
# ("have patterns in building but have the player not see patterns when playing"). Claimed in this order, as each needs more
# room than the next: rooms, downpipes, air conditioners, patches, vent blocks. Patches and vent blocks can share a tile, low and
# high. Own folders, so a kind can be taken back out. Shapes: analysis/dress_shape_ue.py and dress_profile_ue.py.
DR_ROOMS, DR_PIPES, DR_ACS, DR_PATCH, DR_VENT, DR_STEP = ("BackAlleys/" + k for k in (
    "Rooms", "Downpipes", "WallACs", "Patches", "Vents", "DoorSteps"))
PLANE = "/Engine/BasicShapes/Plane"
_plain_tile = ("SM_Wall_Tile_01", "SM_Wall_Tile_Blue", "SM_Wall_Tile_03")
_by_label = {p["label"]: p for p in items if p["folder"] == BLK}
_dress_tiles, _bare_runs = [], {}
# User: "this wall section needs no vents, its just a wall divider"; "That bit is a thin wall, not a house". Thin walls get no dressing:
# the 1.5 m blocks with no door or window, and any run too short to be a house's side (a balcony strip's end).
THIN_RUN = 200.0
_thin_blocks = {k for k, b in BLOCKS.items() if min(b["x1"] - b["x0"], b["y1"] - b["y0"]) <= 1.5 and not b.get("balcony")}
for r in wall_runs:
    q = r["name"].split("_")
    h = q[0][:-1] if q[0].endswith("b") and q[0][:-1] in BLOCKS else q[0]
    if q[0] in _thin_blocks or sum(r["widths"]) < THIN_RUN:
        continue
    for i, w_ in enumerate(r["widths"]):
        p = _by_label.get("%s_%d" % (r["name"], i))
        if p is None or p["asset"].split("/")[-1] not in _plain_tile or p["mats"][0] == HOLLOW:
            continue
        t = {"label": p["label"], "house": h, "bid": q[0], "side": r["side"], "letter": q[1][0], "s": int(q[1][1:]),
             "x": p["loc"][0], "y": p["loc"][1], "z": p["loc"][2], "w": w_, "run": r["name"], "i": i, "z0": r["z"],
             "bare_face": (h, q[1][0]) in _cset, "has": []}
        _dress_tiles.append(t)
_dress_labels = {t["label"]: t for t in _dress_tiles}


def _lay(X, Y):
    return Y / 100.0 + 27.0, 24.0 - X / 100.0


def _ground_open(t, s_, n_):
    """Open ground (no house at any height) in front of tile t, s_ cm along it and n_ cm out."""
    lx, ly = _lay(*at(t["x"], t["y"], t["side"], s_, n_))
    return 0 < lx < W and 0 < ly < H and cover_top(lx, ly, BLOCKS[t["bid"]]) <= 0


def _reach_clear(t, s_, n_, z):
    lx, ly = _lay(*at(t["x"], t["y"], t["side"], s_, n_))
    return awn_clear(lx, ly, z, t["bid"])


def _stair_clear(t, s0, s1, z_low):
    """User: "some of your patch placements and vent placements go into the stairs". The gallery stairs run against walls (B11's sides):
    nothing on that stretch of wall lower than the stairs' top. Upstairs, high enough, is clear of them."""
    if z_low >= 520.0:
        return True
    for s_ in (s0 - 10.0, (s0 + s1) / 2, s1 + 10.0):
        lx, ly = _lay(*at(t["x"], t["y"], t["side"], s_, 30.0))
        if any(g["x0"] - 0.3 < lx < g["x1"] + 0.3 and g["y0"] - 2.3 < ly < g["y1"] + 0.3 for g in L["stairs"]):
            return False
    return True


def _clear_of_end_walls(lx, ly, pad):
    for d in L["doors"]:
        ax, ay = (2.5, 0.4) if d["face"] in "NS" else (0.4, 2.5)
        if abs(lx - d["x"]) < ax + pad and abs(ly - d["y"]) < ay + pad:
            return False
    return True


# Rooms overhanging the alley. User: "the overhang rooms". AsiaSlum's add-on boxes: local X along the wall from -11.1, local +Y
# outward from the open back at -5, floor at -1.1. On upper storeys, over open ground only, on 1-3 blank tiles side by side,
# scaled to the run, ROOM_D deep instead of 2.4 m so the alley keeps its sky, and under the storey's top trim. Timber joists
# and struts under the floor, or it looks hung from nothing. Not within a metre of the wall opposite, another room, the deck, the
# stairs or a door end wall. One a house at most. Collision stays: they stop bullets.
ROOM_NATIVE = {AS + "SM_Balcony_A_003": 328.5, AS + "SM_Balcony_B_004": 635.5, AS + "SM_Balcony_B_006": 635.5}
ROOM_COLOURS = (("White", 0.5), ("BLUE", 0.3), ("RED", 0.2))
ROOM_D = (120.0, 135.0, 150.0)
ROOMS_WANTED = 12
ROOM_RNG = random.Random(149)
_draw_room_b = shuffle_bag(ROOM_RNG, (AS + "SM_Balcony_B_004", AS + "SM_Balcony_B_006"))
_draw_room_door = shuffle_bag(DOOR_RNG, tuple(PLANE_DOORS))
_room_rects, _room_spans, _rooms_made = [], {}, []
_room_struts = []                                       # (tile, how far along it): where a room's strut lands on the wall
_by_run = {}
for t in _dress_tiles:
    _by_run.setdefault(t["run"], []).append(t)
_room_cands = {}
for run_, ts in _by_run.items():
    if ts[0]["s"] < 1 or BLOCKS[ts[0]["bid"]].get("balcony"):
        continue
    for a_ in range(len(ts)):
        for c_ in (1, 2, 3):
            seq = ts[a_:a_ + c_]
            if len(seq) == c_ and all(seq[k + 1]["i"] == seq[k]["i"] + 1 for k in range(c_ - 1)) and \
                    250.0 <= sum(q_["w"] for q_ in seq) <= 720.0:
                _room_cands.setdefault(seq[0]["house"], []).append(seq)
_room_order = sorted(_room_cands)
ROOM_RNG.shuffle(_room_order)
_n_rooms = 0
for h in _room_order:
    if _n_rooms >= ROOMS_WANTED:
        break
    cands = list(_room_cands[h])
    ROOM_RNG.shuffle(cands)
    for seq in cands:
        t = seq[0]
        total = sum(q_["w"] for q_ in seq)
        w_r, d_r = total - 16.0, ROOM_RNG.choice(ROOM_D)
        if not all(_ground_open(t, s_, n_) for s_ in (-14.0, total / 2, total + 14.0) for n_ in (5.0, d_r / 2, d_r + 100.0)):
            continue
        if not all(_reach_clear(t, s_, d_r + 40.0, t["z0"] + 60.0) for s_ in (-14.0, total / 2, total + 14.0)):
            continue
        c0 = at(t["x"], t["y"], t["side"], -100.0, 0.0)
        c1 = at(t["x"], t["y"], t["side"], total + 100.0, d_r + 100.0)
        rect = (min(c0[0], c1[0]), min(c0[1], c1[1]), max(c0[0], c1[0]), max(c0[1], c1[1]))
        if any(rect[0] < o[2] and o[0] < rect[2] and rect[1] < o[3] and o[1] < rect[3] for o in _room_rects):
            continue
        if not all(_clear_of_end_walls(*_lay(*at(t["x"], t["y"], t["side"], s_, d_r)), 1.0) for s_ in (0.0, total)):
            continue
        _room_rects.append(rect)
        _n_rooms += 1
        mesh = AS + "SM_Balcony_A_003" if w_r < 430.0 else _draw_room_b()
        sx_ = w_r / ROOM_NATIVE[mesh]
        sy_, h_r = d_r / 242.5, BLOCKS[t["bid"]]["sh"] - 30.0
        sz_ = h_r / 400.5
        x_, y_ = at(t["x"], t["y"], t["side"], 8.0 + 11.1 * sx_, -1.0 + 5.0 * sy_)
        colour = ROOM_RNG.choices([c for c, _ in ROOM_COLOURS], [k for _, k in ROOM_COLOURS])[0]
        label = "Room_" + t["label"]
        put(label, mesh, x_, y_, t["z"] + 1.1 * sz_, YAW[t["side"]], (sx_, sy_, sz_), folder=DR_ROOMS,
            mats=["/Game/AsiaSlum/Material/MI_Balcony_A_001_" + colour])
        # User: "put a doorr texture on the overhang balcony wall, looks like nothing leads to their right now". One of the user's
        # plane doors on the wall behind, at the same 110 x 218 cm as the wall doors, standing on the room's floor (traced: 33 cm up,
        # before the room's Z scale). Seen through the room's open windows. DOOR_RNG: nothing after this draws from it.
        door_s = total / 2 + ROOM_RNG.uniform(-1.0, 1.0) * max(0.0, total / 2 - 75.0) * 0.6
        door_x, door_y = at(t["x"], t["y"], t["side"], door_s, 0.8)
        put(label + "_Door", PLANE, door_x, door_y, t["z"] + 33.0 * sz_ + 109.0, YAW[t["side"]],
            (-1.10 if PLANE_HINGE_RIGHT else 1.10, 2.18, 1), folder=DR_ROOMS, roll=90.0, nocoll=True, mats=[BM + _draw_room_door()])
        _room_spans.setdefault((t["bid"], t["side"]), []).append((t["x"], t["y"], total))
        _rooms_made.append((t, total, d_r, sz_))
        for q_ in seq:
            q_["has"].append("room")
        # Joists: level under the floor. Struts: from the wall up to 70% of the joist.
        side = t["side"]
        (nx, ny), (rx, ry) = NORMAL[side], RUN[side]
        run3, out3, up3 = (float(rx), float(ry), 0.0), (float(nx), float(ny), 0.0), (0.0, 0.0, 1.0)
        joists = 2 if w_r < 430.0 else 3
        beam = BEAMS["brown"]
        for k in range(joists):
            s_ = 30.0 + (total - 60.0) * k / (joists - 1)
            x_, y_ = at(t["x"], t["y"], side, s_, (d_r - 6.0) / 2)
            put_board("%s_Joist%d" % (label, k), beam, (x_, y_, t["z"] - 6.0), run3, out3, up3, (9.0, d_r - 6.0, 12.0),
                      nocoll=True)
            items[-1]["folder"] = DR_ROOMS
            reach, drop = d_r * 0.7, 95.0
            leng = math.hypot(reach, drop)
            dir3 = (out3[0] * reach / leng, out3[1] * reach / leng, drop / leng)
            x_, y_ = at(t["x"], t["y"], side, s_, reach / 2)
            put_board("%s_Strut%d" % (label, k), beam, (x_, y_, t["z"] - 12.0 - drop / 2), run3, dir3, v_cross(run3, dir3),
                      (7.0, leng, 9.0), nocoll=True)
            items[-1]["folder"] = DR_ROOMS
            _room_struts.append((t, s_))
        break

# Downpipes. User: "do downpipes". Favela's SM_Rain_Pipe_01 (2.08 m, 564 tris, its own clips): local +Y outward, pipe centred 22.8
# cm off the wall, which clears the trims and the protruding bands. Stacked from under the eave to just above the road. Only on the
# side a metal roof drains to, near an end of the face (clear of openings and awnings, which keep 37 cm from a tile's edge), where
# the wall shows at every storey. One on P_PIPE of those faces, and never two on a house (user: "for pipes, never 2 on the same house"),
# in the pack's dark red or galvanised.
PIPE = FV + "SM_Rain_Pipe_01"
PIPE_H = 208.4
P_PIPE = 0.8
_pipe_houses = set()
PIPE_GAP = 70.0                                         # user: "theres also a pipe that overlaps with another pipe", on two blocks at a corner
_pipe_xy = []
PIPE_RNG = random.Random(151)
_pipe_style = {}
_pipes = {}
_draw_pipe_style = shuffle_bag(PIPE_RNG, (None, None, "galv"))
_n_pipes = 0
for bid, b in BLOCKS.items():
    h = bid[:-1] if bid.endswith("b") and bid[:-1] in BLOCKS else bid
    for side in b.get("eaves", ()):
        letter = side[0].upper()
        if h in _pipe_houses or (h, letter) in _hset or PIPE_RNG.random() > P_PIPE:
            continue
        rs = [r for r in wall_runs if r["name"].startswith("%s_%s0_" % (bid, letter))]
        if not rs:
            continue
        r0 = max(rs, key=lambda r: r["len"])
        ends = [PIPE_RNG.uniform(26.0, 34.0), r0["len"] - PIPE_RNG.uniform(26.0, 34.0)]
        PIPE_RNG.shuffle(ends)
        rx, ry = RUN[side]
        for e_, s_ in enumerate(ends):
            if h in _pipe_houses:
                break
            X_, Y_ = at(r0["start"][0], r0["start"][1], side, s_, 0.0)
            px3, py3 = at(X_, Y_, side, 0.0, 23.0)              # the pipe's centre: its pivot is 15 cm nearer the wall
            ok = not any(math.hypot(px3 - o[0], py3 - o[1]) < PIPE_GAP for o in _pipe_xy)
            if any(o[0] < px3 < o[2] and o[1] < py3 < o[3] for o in _room_rects):   # the rooms' rectangles have a metre to spare
                ok = False
            for st in range(1, b["storeys"]):
                rup = [r for r in wall_runs if r["name"].startswith("%s_%s%d_" % (bid, letter, st))]
                if not any(-1.0 <= (X_ - r["start"][0]) * rx + (Y_ - r["start"][1]) * ry <= r["len"] + 1.0 for r in rup):
                    ok = False
            for (px_, py_, tot) in _room_spans.get((bid, side), ()):
                if -20.0 < (X_ - px_) * rx + (Y_ - py_) * ry < tot + 20.0:
                    ok = False
            lx, ly = _lay(*at(X_, Y_, side, 0.0, 45.0))
            if not ok or not (0 < lx < W and 0 < ly < H) or cover_top(lx, ly, b) > 0 or not awn_clear(lx, ly, 100.0, bid):
                continue
            top_, bot_ = b["storeys"] * b["sh"] + FLOOR_H + 6.0, 12.0
            n_ = int(math.ceil((top_ - bot_) / PIPE_H))
            step_ = (top_ - bot_) / n_
            if h not in _pipe_style:
                _pipe_style[h] = _draw_pipe_style()
            x_, y_ = at(X_, Y_, side, 0.0, 7.6)
            for j in range(n_):
                put("Pipe_%s_%s%d_%d" % (bid, letter, e_, j), PIPE, x_, y_, bot_ + step_ * (j + 0.5), YAW[side],
                    (1, 1, step_ / PIPE_H), folder=DR_PIPES, nocoll=True, mats=[FLASH_MAT] if _pipe_style[h] else None)
            _pipes.setdefault((bid, side), []).append((X_, Y_))
            _pipe_xy.append((px3, py3))
            _pipe_houses.add(h)
            _n_pipes += 1


def _pipe_free(t, s0, s1):
    """No downpipe across this stretch of wall, or standing in front of it on a neighbour's wall at a corner (s0..s1, up to 90 cm out)."""
    rx, ry = RUN[t["side"]]
    nx, ny = NORMAL[t["side"]]
    return not any(s0 - 16.0 < (X_ - t["x"]) * rx + (Y_ - t["y"]) * ry < s1 + 16.0 and -30.0 < (X_ - t["x"]) * nx + (Y_ - t["y"]) * ny < 90.0
                   for X_, Y_ in _pipe_xy)


# Air conditioners. User: "window air conditioning"; "a lot of blank face tiles". MiddleEast's window unit in its timber frame
# (SM_Windows_04), or the box alone through the wall (SM_Air_Conditioning_*), both natively a big desert cooler: squashed to a
# 2002 window type about 60 cm wide and 45 cm out. Local -X outward, frame or flanges at X 0, so yaw 90 less than the wall. On blank tiles, so they
# need no window hole. The frame's panes would show the wall through them, so a dark glass plane goes behind. Half the houses, one
# kind per house, 1-2 units, upstairs first, and high enough on the ground floor to walk under.
AC_FRAME = ME + "MiddleEast/SM_Windows_04"
AC_BOXES = (ME + "MiddleEast/SM_Air_Conditioning_White_03", ME + "MiddleEast/SM_Air_Conditioning_01",
            ME + "MiddleEast/SM_Air_Conditioning_Blue_02")
P_AC_HOUSE = 0.5
AC_RNG = random.Random(157)
_draw_ac = shuffle_bag(AC_RNG, (AC_FRAME, AC_FRAME, AC_BOXES[0], AC_BOXES[0], AC_BOXES[1], AC_BOXES[2]))
_ac_by_house = {}
for t in _dress_tiles:
    if not t["has"] and t["w"] >= 170.0:
        _ac_by_house.setdefault(t["house"], []).append(t)
_n_acs = 0
for h in sorted(_ac_by_house):
    if AC_RNG.random() > P_AC_HOUSE:
        continue
    mesh = _draw_ac()
    ts = _ac_by_house[h]
    AC_RNG.shuffle(ts)
    ts.sort(key=lambda t: t["s"] == 0)                  # upstairs first
    want = AC_RNG.choice((1, 1, 1, 2))
    for t in ts:
        if want == 0:
            break
        frame = mesh == AC_FRAME
        sa, sd, sz = (0.66, 0.55, 0.62) if frame else (0.62, 0.55, 0.5)
        wid, hei = (106.4 * sa, 151.1 * sz) if frame else (93.0 * sa, 93.6 * sz)
        bottom = t["z"] + (AC_RNG.uniform(186.0, 192.0) if t["s"] == 0 else AC_RNG.uniform(120.0, 175.0))
        sc = t["w"] / 2 + AC_RNG.uniform(-1.0, 1.0) * max(0.0, (t["w"] - wid) / 2 - 25.0)
        if not _pipe_free(t, sc - wid / 2, sc + wid / 2) or not _reach_clear(t, sc, 90.0, t["z0"] + 190.0) or \
                not _stair_clear(t, sc - wid / 2, sc + wid / 2, bottom):
            continue
        side = t["side"]
        label = "AC_" + t["label"]
        x_, y_ = at(t["x"], t["y"], side, sc - wid / 2 if frame else sc, 1.0)
        put(label, mesh, x_, y_, bottom + 11.4 * sz if frame else bottom + hei / 2, YAW[side] - 90, (sd, sa, sz), folder=DR_ACS)
        if frame:
            x_, y_ = at(t["x"], t["y"], side, sc, 0.6)
            put(label + "_Glass", PLANE, x_, y_, bottom + hei / 2, YAW[side], ((wid - 4.0) / 100.0, (hei - 4.0) / 100.0, 1),
                folder=DR_ACS, roll=90.0, nocoll=True, mats=[GLASS])
        t["has"].append("ac")
        want -= 1
        _n_acs += 1

# Laundry beside ground doors (see Laundry below) takes its tiles now: by the time patches and vents have run, nearly every tile next to
# a door is full. On the bare tile beside the door, at the door's end of it, high enough that what hangs stays above a head.
LAUNDRY_RNG = random.Random(179)
DOOR_RACKS = 5
_door_at = set()
for r in wall_runs:
    q = r["name"].split("_")
    if q[1][1:] != "0":
        continue
    for i, w_ in enumerate(r["widths"]):
        p = _by_label.get("%s_%d" % (r["name"], i))
        if p is not None and p["asset"].split("/")[-1] == "SM_WallDoor_01":
            _door_at.add((r["name"], i))
_door_ts = [t for t in _dress_tiles if t["s"] == 0 and not t["has"] and t["w"] >= 140.0 and
            ((t["run"], t["i"] - 1) in _door_at or (t["run"], t["i"] + 1) in _door_at)]
LAUNDRY_RNG.shuffle(_door_ts)
_door_racks = []
_door_rack_houses = set()
for t in _door_ts:
    if len(_door_racks) >= DOOR_RACKS or t["house"] in _door_rack_houses:
        continue
    w_r = min(t["w"] - 24.0, LAUNDRY_RNG.uniform(120.0, 170.0))
    s0 = 12.0 if (t["run"], t["i"] - 1) in _door_at else t["w"] - w_r - 12.0
    z_ = t["z"] + LAUNDRY_RNG.uniform(255.0, 272.0)
    if not _pipe_free(t, s0, s0 + w_r) or not all(_ground_open(t, s_, 90.0) and _reach_clear(t, s_, 90.0, z_ + 60.0) for s_ in (s0, s0 + w_r)):
        continue
    t["has"].append("rack")
    _door_racks.append((t, s0, w_r, z_))
    _door_rack_houses.add(t["house"])

# Plywood and tin patches. User: "ply patches". A sheet nailed over a bad bit of wall, a little off true. Plywood is an engine plane
# (make_dress_textures.py, Wood surface), the tin AsiaSlum's real corrugated sheet in a roof finish. About two houses in three are
# patchy, the rest have few. User: "the patches look out of place, maybe if you scale them bigger". Small boards floating mid-wall
# read as stickers, so they're now real sheets: plywood about 1.2 x 2.4 m, one or two side by side, tin a whole plate. On the ground
# they start just above the plinth. Upstairs, they stay above whatever a neighbour's roof hides. They stop under the trim line, and a
# vent block only goes on the same tile if it fits above one. No collision: flat on the wall.
# User: "if you are gonna place patches, place atleast 2 beside each other", "except the roof type, the wood one, yes do 2". Plywood is
# always a group of two or three sheets, lapping, the same finish, over as many blank tiles in a row as it takes; a stretch too short for
# two at their narrowest gets none. Tin stays one plate.
PLY = [BM + "MI_BackAlleys_Ply_" + k for k in ("Natural", "Weathered", "GreenPaint")]
PATCH_RNG = random.Random(163)
P_PATCHY, P_PATCH_T, P_PATCH_RARE = 0.65, 0.6, 0.2
PLY_MIN, TIN_MIN, PLY_LAP, TIN_LAP = 78.0, 110.0, 2.0, 8.0     # the narrowest sheet that still reads as one, and how far they lap
PATCH_TOP = 262.0                                       # above the tile's base, under the trim line
_draw_patch = shuffle_bag(PATCH_RNG, tuple(PLY) * 2 + tuple(SHEET_MATS[f] for f in ("Galv", "Rust", "RedOxide")))
_draw_sheets = shuffle_bag(PATCH_RNG, (2, 2, 2, 3))
_patchy = {}
_n_patch = {"groups": 0, "ply": 0, "tin": 0}


def _fit_sheets(n, ideal, least, lap, avail):
    """n sheet widths for avail cm, shrunk if they must be; two if three won't go; None if two won't."""
    for k_ in (n, 2):
        widths = [PATCH_RNG.uniform(*ideal) for _ in range(k_)]
        total_ = sum(widths) - lap * (k_ - 1)
        if total_ > avail:
            shrink = (avail + lap * (k_ - 1)) / sum(widths)
            widths = [w_ * shrink for w_ in widths]
        if min(widths) >= least:
            return widths
    return None


for run_, ts in _by_run.items():
    spans, cur = [], []
    for t in ts:                                        # the blank tiles side by side in this run
        if t["has"] or (cur and t["i"] != cur[-1]["i"] + 1):
            if cur:
                spans.append(cur)
            cur = []
        if not t["has"]:
            cur.append(t)
    if cur:
        spans.append(cur)
    for sp in spans:
        t0 = sp[0]
        h, side = t0["house"], t0["side"]
        if h not in _patchy:
            _patchy[h] = PATCH_RNG.random() < P_PATCHY
        total = sum(t["w"] for t in sp)
        start = 0.0
        while total - start >= TIN_MIN + 24.0:
            if PATCH_RNG.random() > (P_PATCH_T if _patchy[h] else P_PATCH_RARE):
                start += PATCH_RNG.uniform(150.0, 260.0)
                continue
            avail = total - start - 24.0
            mi = _draw_patch()
            n_ = _draw_sheets()
            widths = None
            if mi not in PLY:                           # native 162 cm: the corrugations stay near true size
                widths = _fit_sheets(1, (135.0, 190.0), TIN_MIN, TIN_LAP, avail)
                if widths is None:
                    mi = PATCH_RNG.choice(PLY)
            if mi in PLY:
                widths = _fit_sheets(n_, (108.0, 124.0), PLY_MIN, PLY_LAP, avail)
            if widths is None:
                break
            lap = PLY_LAP if mi in PLY else TIN_LAP
            g_ = sum(widths) - lap * (len(widths) - 1)
            s0 = start + 12.0 + PATCH_RNG.uniform(0.0, max(0.0, avail - g_))
            bot = PATCH_RNG.uniform(8.0, 26.0) if t0["s"] == 0 else PATCH_RNG.uniform(58.0, 78.0)
            if not _pipe_free(t0, s0, s0 + g_) or not _stair_clear(t0, s0, s0 + g_, t0["z"] + bot):
                start += 90.0
                continue
            # The tiles it lies on, and which one it starts on, for its name.
            under, first, off = [], None, 0.0
            for t in sp:
                if off < s0 + g_ and s0 < off + t["w"]:
                    under.append(t)
                    first = first or t
                off += t["w"]
            run3 = (float(RUN[side][0]), float(RUN[side][1]), 0.0)
            out3 = (float(NORMAL[side][0]), float(NORMAL[side][1]), 0.0)
            patch_top = 0.0
            s_ = s0
            for k_, w_s in enumerate(widths):
                label = "Patch_%s_%d" % (first["label"], k_)
                if mi in PLY:
                    tilt = PATCH_RNG.uniform(-0.8, 0.8)
                    X3, up3 = v_rot(run3, out3, tilt), v_rot((0.0, 0.0, 1.0), out3, tilt)
                    h_p = PATCH_RNG.uniform(min(190.0, PATCH_TOP - bot - 12.0), PATCH_TOP - bot)
                    x_, y_ = at(t0["x"], t0["y"], side, s_ + w_s / 2, 1.0 + 0.4 * k_)
                    put_axes(label, PLANE, X3, (-up3[0], -up3[1], -up3[2]), out3, (w_s / 100.0, h_p / 100.0, 1.0), (0.0, 0.0, 0.0),
                             (x_, y_, t0["z"] + bot + h_p / 2), mats=[mi], nocoll=True)
                    _n_patch["ply"] += 1
                else:
                    tilt = PATCH_RNG.uniform(-1.0, 1.0)
                    X3, up3 = v_rot(run3, out3, tilt), v_rot((0.0, 0.0, 1.0), out3, tilt)
                    h_p = PATCH_RNG.uniform(min(180.0, PATCH_TOP - bot - 12.0), PATCH_TOP - bot)
                    x_, y_ = at(t0["x"], t0["y"], side, s_ + w_s / 2, 1.0 + PLATE_T / 2 + 1.5 * k_)
                    top3 = v_add((x_, y_, t0["z"] + bot + h_p / 2), up3, h_p / 2)
                    put_axes(label, PATCH_RNG.choice(AWN_PLATES), X3, out3, up3, (w_s / PLATE_W, 1.0, h_p / 164.9), (0.0, 0.0, 0.0), top3,
                             mats=[mi], nocoll=True)
                    _n_patch["tin"] += 1
                items[-1]["folder"] = DR_PATCH
                patch_top = max(patch_top, bot + h_p)
                s_ += w_s - lap
            for t in under:
                t["has"].append("patch")
                t["patch_top"] = patch_top
            _n_patch["groups"] += 1
            start = s0 + g_ + PATCH_RNG.uniform(90.0, 220.0)

# Vent blocks. User: "vent blocks". Concrete blocks 20 x 20 cm, set high in the wall under the band, where a house lets its rooms
# breathe (make_dress_textures.py: 4 x 2 blocks on an 80 x 40 cm plane). More on faces with no window at all, one pattern per house.
# User: "The vents, align them if they are on the same face", "atleast the same height". A face (one side of a house, every storey)
# has one height and one row count, so tops and bottoms line up. Faces differ from each other, and how wide a run is stays free.
VENT = [BM + "MI_BackAlleys_VentBlock_" + k for k in ("Diamond", "Slots")]
VENT_RNG = random.Random(167)
P_VENT_BLANK, P_VENT_OPEN = 0.72, 0.5
_draw_vent = shuffle_bag(VENT_RNG, tuple(VENT))
_vent_house = {}
_vent_face = {}
_n_vents = 0
for t in _dress_tiles:
    if "room" in t["has"] or "ac" in t["has"] or t["w"] < 110.0:
        continue
    if t["s"] > 0 and not _ground_open(t, t["w"] / 2, 30.0):   # a terrace's lean-to may be there
        continue
    if VENT_RNG.random() > (P_VENT_BLANK if t["bare_face"] else P_VENT_OPEN):
        continue
    if t["house"] not in _vent_house:
        _vent_house[t["house"]] = _draw_vent()
    face_key = (t["house"], t["letter"])
    if face_key not in _vent_face:
        _vent_face[face_key] = (282.0 - VENT_RNG.uniform(0.0, 30.0), VENT_RNG.choice((1, 1, 1, 2)))
    top, rows = _vent_face[face_key]
    if t["w"] >= 270.0:
        cols = VENT_RNG.choice((1, 2, 2, 3))
    elif t["w"] >= 195.0:
        cols = VENT_RNG.choice((1, 2, 2))
    else:
        cols = 1
    w_v, h_v = cols * 80.0, rows * 40.0
    if t.get("patch_top") and top - h_v < t["patch_top"] + 4.0:     # no room above the sheet: leave this tile out of the line
        continue
    pad = min(14.0, (t["w"] - w_v) / 2 - 1.0)        # a narrow tile takes one panel with less to spare
    sc = VENT_RNG.uniform(w_v / 2 + pad, t["w"] - w_v / 2 - pad)
    if not _pipe_free(t, sc - w_v / 2, sc + w_v / 2) or not _stair_clear(t, sc - w_v / 2, sc + w_v / 2, t["z"] + top - h_v):
        continue
    for c_ in range(cols):
        for r_ in range(rows):
            x_, y_ = at(t["x"], t["y"], t["side"], sc - w_v / 2 + 80.0 * (c_ + 0.5), 0.7)
            put("Vent_%s_%d%d" % (t["label"], c_, r_), PLANE, x_, y_, t["z"] + top - 40.0 * (r_ + 0.5), YAW[t["side"]],
                (0.8, 0.4, 1), folder=DR_VENT, roll=90.0, nocoll=True, mats=[_vent_house[t["house"]]])
    t["has"].append("vent")
    _n_vents += 1

# Laundry. User: "start adding laundry hang, but keep it cheap if its far away". Then: "keep the laundry stuff on balconies , or near
# reach of a window on the second floor. or near the doors. never out across the street, if it crosses the street, then make sure its
# on the second floor". So somebody can always reach it: lines on the balcony strips and in the overhanging rooms, clothes over the
# gallery rail, racks under second-floor windows and beside ground doors, and the only lines over a street start at a second-floor
# window and tie off at the second floor opposite. One lot to a house, so no street of the same thing.
# Cheap: the clothes are MiddleEast's lighter ones, which already have four LODs down to 200-350 tris (SM_clothes_B_02 at 5.8k stays
# out). Everything culls at LAUNDRY_CULL by "draw" in the plan, and a line is two engine cubes, not SM_Rope_A_001 at 1,208 tris with no
# LODs. Racks are AsiaSlum's, 108 tris. No collision: shots and players go through.
DR_LAUNDRY = "BackAlleys/Laundry"
LAUNDRY_CULL = 3500.0
BALCONY_LINES, ROOM_LINES, STREET_LINES, WINDOW_RACKS, RAIL_CLOTHES = 5, 5, 6, 6, 5
ROPE_MAT = "/Game/AsiaSlum/Material/MI_Rope_A_001"
_clothes_path = ME + "MiddleEast/SM_clothes_"
_draw_clothes = shuffle_bag(LAUNDRY_RNG, tuple(_clothes_path + k for k in ("A_01", "A_01", "A_02", "A_03", "A_04", "A_05", "B_01", "B_01", "B_03")))
# Beside a door or over a rail: nothing long, so it stays above a head and doesn't fill the rail.
_draw_short = shuffle_bag(LAUNDRY_RNG, tuple(_clothes_path + k for k in ("A_02", "A_03", "A_04", "A_05", "B_03")))
_laundry_houses = set(_door_rack_houses)
_n_laundry = {"balcony": 0, "room": 0, "street": 0, "window": 0, "door": 0, "rail": 0}


def _cloth(label, x_, y_, z_, yaw_, short=False):
    k = LAUNDRY_RNG.uniform(0.92, 1.06)
    put(label, _draw_short() if short else _draw_clothes(), x_, y_, z_, yaw_ + LAUNDRY_RNG.uniform(-7.0, 7.0), (k, k, k),
        folder=DR_LAUNDRY, nocoll=True)
    items[-1]["draw"] = LAUNDRY_CULL


def _laundry_line(label, a3, b3, yaw_, step=(75.0, 90.0, 90.0, 110.0, 170.0), end=45.0):
    """A sagging line from a3 to b3 (x, y, z), two thin cubes, with clothes along it: a gap here and there, none right at an end."""
    sag = LAUNDRY_RNG.uniform(5.0, 13.0) * math.hypot(b3[0] - a3[0], b3[1] - a3[1]) / 400.0
    mid = ((a3[0] + b3[0]) / 2, (a3[1] + b3[1]) / 2, (a3[2] + b3[2]) / 2 - sag)
    for k_, (p0, p1) in enumerate(((a3, mid), (mid, b3))):
        d3 = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        len_ = math.sqrt(sum(c * c for c in d3))
        X3 = (d3[0] / len_, d3[1] / len_, d3[2] / len_)
        h_ = math.hypot(X3[0], X3[1])
        Y3 = (-X3[1] / h_, X3[0] / h_, 0.0)
        put_board("%s_Line%d" % (label, k_), CUBE, ((p0[0] + p1[0]) / 2, (p0[1] + p1[1]) / 2, (p0[2] + p1[2]) / 2), X3, Y3,
                  v_cross(X3, Y3), (len_, 1.2, 1.2), mats=[ROPE_MAT], nocoll=True)
        items[-1]["folder"] = DR_LAUNDRY
        items[-1]["draw"] = LAUNDRY_CULL
    length = math.hypot(b3[0] - a3[0], b3[1] - a3[1])
    d_ = end + LAUNDRY_RNG.uniform(0.0, 35.0)
    j_ = 0
    while d_ < length - end:
        u = d_ / length
        _cloth("%s_%d" % (label, j_), a3[0] + (b3[0] - a3[0]) * u, a3[1] + (b3[1] - a3[1]) * u,
               a3[2] + (b3[2] - a3[2]) * u - sag * (1.0 - abs(2.0 * u - 1.0)), yaw_)
        j_ += 1
        d_ += LAUNDRY_RNG.choice(step)


def _laundry_rack(label, t, s0, w_r, z_, short):
    """SM_DryingRack_A_002: 271 long on local X from its pivot, 7 cm behind to 63 out on local -Y. Turned 180, X runs back along the wall."""
    side = t["side"]
    x_, y_ = at(t["x"], t["y"], side, s0 + w_r, 7.0)
    put(label, AS + "SM_DryingRack_A_002", x_, y_, z_, YAW[side] + 180.0, (w_r / 271.0, 1.0, 1.0), folder=DR_LAUNDRY, nocoll=True)
    items[-1]["draw"] = LAUNDRY_CULL
    s_ = s0 + LAUNDRY_RNG.uniform(30.0, 50.0)
    j_ = 0
    while s_ < s0 + w_r - 25.0:
        x_, y_ = at(t["x"], t["y"], side, s_, 62.0)
        _cloth("%s_%d" % (label, j_), x_, y_, z_ - 2.0, YAW[side] - 90.0, short)
        j_ += 1
        s_ += LAUNDRY_RNG.choice((60.0, 75.0, 90.0))


def _in_room(X, Y):
    return any(o[0] < X < o[2] and o[1] < Y < o[3] for o in _room_rects)


# On the balcony strips: tied between two of the frame's posts, 18 cm in from them, above the parapet and under the roof.
_side_of = {"N": "north", "S": "south", "E": "east", "W": "west"}
_strip_posts = {}
for p in items:
    if p["folder"] == TER and p["label"].startswith(("Post_", "AwnPost_")) and p["label"].endswith("_0"):
        q = p["label"].split("_")
        if BLOCKS.get(q[1], {}).get("balcony"):
            _strip_posts.setdefault((q[1], q[2][0]), []).append(p)
_strips = sorted(_strip_posts)
LAUNDRY_RNG.shuffle(_strips)
for bid, letter in _strips:
    b = BLOCKS[bid]
    house = bid[:-1] if bid.endswith("b") and bid[:-1] in BLOCKS else bid
    ps = _strip_posts[(bid, letter)]
    if _n_laundry["balcony"] >= BALCONY_LINES or house in _laundry_houses or len(ps) < 3:
        continue
    side = _side_of[letter]
    rx, ry = RUN[side]
    ps = sorted(ps, key=lambda p: p["loc"][0] * rx + p["loc"][1] * ry)
    i0 = LAUNDRY_RNG.randrange(0, len(ps) - 2)
    p0, p1 = ps[i0], ps[min(i0 + LAUNDRY_RNG.choice((2, 2, 3)), len(ps) - 1)]
    nx, ny = NORMAL[side]
    z_ = b["sh"] - 5.0 + FLOOR_H + LAUNDRY_RNG.uniform(180.0, 200.0)
    a3 = (p0["loc"][0] - nx * 18.0, p0["loc"][1] - ny * 18.0, z_)
    b3 = (p1["loc"][0] - nx * 18.0, p1["loc"][1] - ny * 18.0, z_)
    _laundry_line("BalconyLine_%s_%s" % (bid, letter), a3, b3, YAW[side] - 90.0, step=(60.0, 75.0, 75.0, 95.0))
    _laundry_houses.add(house)
    _n_laundry["balcony"] += 1

# In the overhanging rooms: side to side, a little nearer the front, at head height over the room's floor. Seen through its windows.
_room_order2 = list(_rooms_made)
LAUNDRY_RNG.shuffle(_room_order2)
for t, total, d_r, sz_ in _room_order2:
    if _n_laundry["room"] >= ROOM_LINES or t["house"] in _laundry_houses:
        continue
    side = t["side"]
    inside = 0.826 * (BLOCKS[t["bid"]]["sh"] - 30.0)
    z_ = t["z"] + 33.0 * sz_ + min(LAUNDRY_RNG.uniform(180.0, 200.0), inside - 15.0)
    n_ = d_r * LAUNDRY_RNG.uniform(0.5, 0.7)
    x0_, y0_ = at(t["x"], t["y"], side, 30.0, n_)
    x1_, y1_ = at(t["x"], t["y"], side, total - 30.0, n_)
    _laundry_line("RoomLine_%s" % t["label"], (x0_, y0_, z_), (x1_, y1_, z_), YAW[side] - 90.0, step=(60.0, 75.0, 75.0, 95.0), end=30.0)
    _laundry_houses.add(t["house"])
    _n_laundry["room"] += 1

# Second-floor windows.
_win_tiles = []
for r in wall_runs:
    q = r["name"].split("_")
    if q[0] in _thin_blocks:
        continue
    h = q[0][:-1] if q[0].endswith("b") and q[0][:-1] in BLOCKS else q[0]
    for i, w_ in enumerate(r["widths"]):
        p = _by_label.get("%s_%d" % (r["name"], i))
        if p is None:
            continue
        a_ = p["asset"].split("/")[-1]
        if a_ == "SM_Wall_Windows_01" and q[1][1:] == "1":
            _win_tiles.append({"label": p["label"], "house": h, "bid": q[0], "side": r["side"], "s": 1, "x": p["loc"][0], "y": p["loc"][1],
                               "z": p["loc"][2], "w": w_, "sx": p["scale"][0]})
LAUNDRY_RNG.shuffle(_win_tiles)

# Over the street: only from beside a second-floor window, at a height you can reach from it, to a second-floor wall opposite.
_line_mids = []
for t in _win_tiles:
    if _n_laundry["street"] >= STREET_LINES:
        break
    if t["house"] in _laundry_houses:
        continue
    side = t["side"]
    s_ = 111.0 * t["sx"] + LAUNDRY_RNG.choice((-1.0, 1.0)) * (55.0 * t["sx"] + LAUNDRY_RNG.uniform(10.0, 30.0))
    gap = None
    for n_ in range(100, 700, 5):
        lx, ly = _lay(*at(t["x"], t["y"], side, s_, float(n_)))
        if solid(lx, ly, 1):
            gap = float(n_)
            break
    if gap is None or not 250.0 <= gap <= 650.0:
        continue
    z_ = t["z"] + LAUNDRY_RNG.uniform(165.0, 205.0)
    if not all(_ground_open(t, s_, k * gap / 6.0) and _reach_clear(t, s_, k * gap / 6.0, z_ + 60.0) for k in range(1, 6)):
        continue
    ax, ay = at(t["x"], t["y"], side, s_, 0.0)
    bx, by = at(t["x"], t["y"], side, s_, gap)
    mx, my = (ax + bx) / 2, (ay + by) / 2
    if any(math.hypot(mx - o[0], my - o[1]) < 450.0 for o in _line_mids) or _in_room(mx, my):
        continue
    _line_mids.append((mx, my))
    _laundry_line("StreetLine_%s" % t["label"], (ax, ay, z_), (bx, by, z_), YAW[side], end=70.0)
    _laundry_houses.add(t["house"])
    t["used"] = True
    _n_laundry["street"] += 1

# Under a second-floor window's sill, as wide as the window and a bit, over the wall below.
for t in _win_tiles:
    if _n_laundry["window"] >= WINDOW_RACKS:
        break
    if t["house"] in _laundry_houses or t.get("used"):
        continue
    side = t["side"]
    w_r = min(t["w"] - 16.0, LAUNDRY_RNG.uniform(140.0, 190.0))
    s0 = max(8.0, min(t["w"] - w_r - 8.0, 111.0 * t["sx"] - w_r / 2))
    z_ = t["z"] + 78.0
    if not _pipe_free(t, s0, s0 + w_r) or not all(_ground_open(t, s_, 90.0) and _reach_clear(t, s_, 90.0, z_ + 60.0) for s_ in (s0, s0 + w_r)):
        continue
    if any(_in_room(*at(t["x"], t["y"], side, s_, 40.0)) for s_ in (s0, s0 + w_r)):
        continue
    _laundry_rack("Rack_" + t["label"], t, s0, w_r, z_, False)
    _laundry_houses.add(t["house"])
    _n_laundry["window"] += 1

# Beside a ground door: the tiles chosen before the patches.
for t, s0, w_r, z_ in _door_racks:
    _laundry_rack("Rack_" + t["label"], t, s0, w_r, z_, True)
    _n_laundry["door"] += 1

# Over the gallery rail: its top bar, on the south side, 1.2 m apart at least. These meshes are draped, so they straddle the bar.
_rail_ys = []
for _ in range(60):
    y_ = LAUNDRY_RNG.uniform(Yw + 70.0, Yeast - 70.0)
    if len(_rail_ys) < RAIL_CLOTHES and all(abs(y_ - o) > 120.0 for o in _rail_ys):
        _rail_ys.append(y_)
for j_, y_ in enumerate(_rail_ys):
    _cloth("Rail_Cloth_%d" % j_, Xs + 6.0, y_, 503.0, 0.0, True)
    _n_laundry["rail"] += 1

# Door steps. User: "door steps". The building floor lifts a door 18 cm; a step halves that riser. A concrete block, wider than the
# door and proud of the floor, in three forms and sometimes none: plain, topped with AsiaSlum's tiled threshold (SM_Front_A_001: X
# -31.2..115.9, Y -59.5..16.2, 2.6 thick), or two risers. Ground doors and door end walls, and the doors onto the deck. Pack concrete
# (MI_Concrete_01): the world-mapped wall material streaks on a level top. They keep collision, so people and bullets meet them.
STEP_MAT = FM + "MI_Concrete_01"
STEP_TILE = "/Game/AsiaSlum/Material/MI_OuterWallTile_A_002"
STEP_RNG = random.Random(173)
_draw_step = shuffle_bag(STEP_RNG, ("plain", "plain", "plain", "tile", "tile", "tile", "double", "double", "none"))
_n_steps = {"plain": 0, "tile": 0, "double": 0, "none": 0, "blocked": 0}


def _step_box(label, side, x0, y0, s0, n0, wid, dep, z0, z1):
    c0, c1 = at(x0, y0, side, s0, n0), at(x0, y0, side, s0 + wid, n0 + dep)
    put(label, CUBE, min(c0[0], c1[0]), min(c0[1], c1[1]), z0, 0, (abs(c1[0] - c0[0]) / 100.0, abs(c1[1] - c0[1]) / 100.0,
                                                                   (z1 - z0) / 100.0), folder=DR_STEP, mats=[STEP_MAT])


for p in list(items):
    if p["asset"].split("/")[-1] != "SM_WallDoor_01" or p["folder"] not in (BLK, "BackAlleys/SpawnDoors"):
        continue
    side = _yaw_side[round(p["rot"][1]) % 360]
    x0_, y0_, z_ = p["loc"]
    sx_ = p["scale"][0]
    lx, ly = _lay(*at(x0_, y0_, side, 111.0 * sx_, FLOOR_OUT + 30.0))
    dk_ = L["deck"]
    on_deck = dk_["x0"] < lx < dk_["x1"] and dk_["y0"] < ly < dk_["y1"]
    if on_deck and abs(z_ - (400.0 + FLOOR_H)) < 1.0:
        base, n0 = 400.0, -2.0
    elif abs(z_ - FLOOR_H) < 1.0:
        base, n0 = 0.0, FLOOR_OUT - 4.0
        parts = p["label"].split("_")
        me = BLOCKS.get(parts[0])
        if not (0 < lx < W and 0 < ly < H) or cover_top(lx, ly, me) > 0 or \
                any(g["x0"] - 0.2 < lx < g["x1"] + 0.2 and g["y0"] - 2.2 < ly < g["y1"] + 0.2 for g in L["stairs"]):
            _n_steps["blocked"] += 1
            continue
    else:
        continue
    kind = _draw_step()
    _n_steps[kind] += 1
    if kind == "none":
        continue
    wid, dep = 110.0 * sx_ + STEP_RNG.uniform(22.0, 44.0), STEP_RNG.uniform(32.0, 50.0)
    s0 = 111.0 * sx_ - wid / 2
    label = "Step_" + p["label"]
    if kind == "double":
        _step_box(label + "_Low", side, x0_, y0_, s0 - 9.0, n0, wid + 18.0, dep + 24.0, base - 5.0, base + 6.0)
        _step_box(label, side, x0_, y0_, s0, n0, wid, dep, base - 5.0, base + 12.0)
    else:
        _step_box(label, side, x0_, y0_, s0, n0, wid, dep, base - 5.0, base + 9.0)
    if kind == "tile":
        sa, sd = wid / 147.1, (dep - 2.0) / 75.7
        x_, y_ = at(x0_, y0_, side, s0 + 31.2 * sa, n0 + 59.5 * sd)
        put(label + "_Tile", AS + "Interior/SM_Front_A_001", x_, y_, base + 8.8, YAW[side], (sa, sd, 1), folder=DR_STEP,
            nocoll=True, mats=[STEP_MAT, STEP_TILE])

# --- Street dressing: overhead, rooftops, lights, fronts, small details ------------------------------------------------------------
# User 2026-11-05: "whats else can we add?", then "do all that and add it to the tool". Wires and meter boxes, rooftop tanks and aerials,
# bulbs and lamps with real lights, shutters, gates, tarps, blank signs, window sills, rebar, peeling paint. Every kind has its own switch,
# folder and random sequence, and this pass runs last, so nothing placed above moves and a kind can be taken back out. They keep the
# building dressing's rules: hollow-block faces and thin walls stay empty, nothing on the stair walls, nothing across a pipe, and picks from
# bags with exceptions, one lot to a house, so no street repeats. Shapes: analysis/street_shape_ue.py.
STREET_WIRES, STREET_ROOFTOPS, STREET_LIGHTS, STREET_FRONTS, STREET_DETAILS = True, True, True, True, True
DR_WIRES, DR_METERS, DR_TANKS, DR_AERIALS, DR_LIGHTS, DR_SHUTTERS, DR_GATES, DR_TARPS, DR_SIGNS, DR_SILLS, DR_REBAR, DR_PEEL = (
    "BackAlleys/" + k for k in ("Wires", "Meters", "Tanks", "Aerials", "Lights", "Shutters", "Gates", "Tarps", "Signs", "Sills", "Rebar", "Peel"))
CULL_NEAR, CULL_MID, CULL_FAR = 3500.0, 5000.0, 8000.0
AM = "/Game/AsiaSlum/Material/"
WIRE_MAT, LIGHT_ON, ANT_MAT = AM + "MI_Rubber_A_001", AM + "MI_Light_A_001", AM + "MI_Antenna_A_001"
RUST_MAT = BM + "MI_BackAlleys_MetalSheet_Rust"
_street_n = {}


def _cheap(draw, n=1, noshadow=False):
    """The last n items: culled at draw, no lightmap of their own (the last bake ran out of video memory), and no shadow if thin."""
    for p in items[-n:]:
        p["draw"] = draw
        p["vol"] = True
        if noshadow:
            p["noshadow"] = True


def _count(kind, k=1):
    _street_n[kind] = _street_n.get(kind, 0) + k


def _house_of(bid):
    return bid[:-1] if bid.endswith("b") and bid[:-1] in BLOCKS else bid


# Every wall tile that shows, of any kind, so the openings can be seen too.
_wall_tiles, _run_tiles, _face_runs = [], {}, {}
for r in wall_runs:
    q = r["name"].split("_")
    if q[0] not in BLOCKS or q[0] in _thin_blocks or len(q) < 2 or not q[1][1:].isdigit():
        continue
    off_ = 0.0
    for i, w_ in enumerate(r["widths"]):
        p = _by_label.get("%s_%d" % (r["name"], i))
        if p is not None:
            t = {"label": p["label"], "house": _house_of(q[0]), "bid": q[0], "side": r["side"], "letter": q[1][0], "s": int(q[1][1:]),
                 "x": p["loc"][0], "y": p["loc"][1], "z": p["loc"][2], "w": w_, "sx": abs(p["scale"][0]), "kind": p["asset"].split("/")[-1],
                 "run": r["name"], "off": off_, "dress": _dress_labels.get(p["label"])}
            _wall_tiles.append(t)
            _run_tiles.setdefault(r["name"], []).append(t)
        off_ += w_
    _face_runs.setdefault((q[0], q[1]), []).append(r["name"])
_has_awn = {p["label"][:-4] for p in items if p["label"].endswith("_Awn")}
_hollow_face = lambda t: (t["house"], t["letter"]) in _hset


def _occ_of(p):
    """A world box round a piece already on a wall, by the shapes measured for the building dressing. None if it isn't one of those."""
    a_ = p["asset"].split("/")[-1]
    x, y, z = p["loc"]
    yaw = math.radians(p["rot"][1])
    c, s_ = math.cos(yaw), math.sin(yaw)
    sc = p["scale"]
    if a_ == "Plane":
        pts, lo, hi = [(x - c * abs(sc[0]) * 50, y - s_ * abs(sc[0]) * 50), (x + c * abs(sc[0]) * 50, y + s_ * abs(sc[0]) * 50)], z - abs(sc[1]) * 50, z + abs(sc[1]) * 50
    elif a_.startswith("SM_MetalPlate"):
        pts, lo, hi = [(x - c * abs(sc[0]) * 81, y - s_ * abs(sc[0]) * 81), (x + c * abs(sc[0]) * 81, y + s_ * abs(sc[0]) * 81)], z - abs(sc[2]) * 165, z
    elif a_ == "SM_Rain_Pipe_01":
        cx, cy = x - s_ * 15.4, y + c * 15.4
        pts, lo, hi = [(cx - 14, cy - 14), (cx + 14, cy + 14)], z - abs(sc[2]) * 105, z + abs(sc[2]) * 105
    elif a_ == "SM_DryingRack_A_002":
        ex, ey = x + c * 271 * sc[0], y + s_ * 271 * sc[0]
        pts, lo, hi = [(x, y), (ex, ey), (x + s_ * 63, y - c * 63), (ex + s_ * 63, ey - c * 63)], z - 110, z + 8
    elif a_ == "SM_Windows_04":
        ex, ey = x - s_ * 106.4 * sc[1], y + c * 106.4 * sc[1]
        pts, lo, hi = [(x, y), (ex, ey), (x - c * 60, y - s_ * 60), (ex - c * 60, ey - s_ * 60)], z - 12, z + 151 * sc[2]
    elif a_.startswith("SM_Air_Conditioning"):
        hw_ = 46.5 * sc[1]
        pts, lo, hi = [(x + s_ * hw_, y - c * hw_), (x - s_ * hw_, y + c * hw_), (x + s_ * hw_ - c * 60, y - c * hw_ - s_ * 60)], z - 47 * sc[2], z + 47 * sc[2]
    else:
        return None
    return (min(q_[0] for q_ in pts), min(q_[1] for q_ in pts), lo, max(q_[0] for q_ in pts), max(q_[1] for q_ in pts), hi)


_occ = [b_ for b_ in (_occ_of(p) for p in items if p["folder"] in (DR_PATCH, DR_VENT, DR_ACS, DR_PIPES, DR_LAUNDRY)) if b_]
_occ += [(o[0], o[1], 0.0, o[2], o[3], 3000.0) for o in _room_rects]


def _wbox(t, s0, s1, z0, z1, n1=30.0):
    a_, b_ = at(t["x"], t["y"], t["side"], s0, -2.0), at(t["x"], t["y"], t["side"], s1, n1)
    return (min(a_[0], b_[0]), min(a_[1], b_[1]), z0, max(a_[0], b_[0]), max(a_[1], b_[1]), z1)


def _free(box, pad=6.0):
    return not any(box[0] - pad < o[3] and o[0] < box[3] + pad and box[1] - pad < o[4] and o[1] < box[4] + pad and
                   box[2] - pad < o[5] and o[2] < box[5] + pad for o in _occ)


def _claim(box):
    _occ.append(box)


def _tile_above(t, s_local, st):
    """The tile of storey st over a point s_local along tile t, and how far along it that point is. None if no wall shows there."""
    X_, Y_ = at(t["x"], t["y"], t["side"], s_local, 0.0)
    rx, ry = RUN[t["side"]]
    nx, ny = NORMAL[t["side"]]
    for name in _face_runs.get((t["bid"], "%s%d" % (t["letter"], st)), ()):
        for u in _run_tiles.get(name, ()):
            a_ = (X_ - u["x"]) * rx + (Y_ - u["y"]) * ry
            if 0.0 <= a_ < u["w"] and abs((X_ - u["x"]) * nx + (Y_ - u["y"]) * ny) < 3.0:
                return u, a_
    return None


def _edge_ok(u, s_local, half=0.0):
    """Clear of an opening and of its awning, which keeps 37 cm from a tile's edge; plain walls are clear everywhere."""
    if u["kind"] in ("SM_Wall_Windows_01", "SM_WallDoor_01"):
        return s_local + half < 30.0 * u["sx"] or s_local - half > 195.0 * u["sx"]
    return u["kind"] in _plain_tile


def _band_out(t):
    """How far the band between the floors stands off this wall."""
    return BAND_OUT if (t["house"], t["letter"]) in _proud and t["s"] < BLOCKS[t["house"]]["storeys"] - 1 else 0.0


FACE_EDGE = 40.0        # user: "some of your placements are too close to the edge of the face". A corner column alone takes 20


def _inside_face(u, s0, s1):
    """s0..s1 along tile u, cut back to FACE_EDGE from the ends of its wall."""
    ts_ = _run_tiles[u["run"]]
    return max(s0, ts_[0]["off"] + FACE_EDGE - u["off"]), min(s1, ts_[-1]["off"] + ts_[-1]["w"] - FACE_EDGE - u["off"])


def _wall_cube(label, t, s0, s1, n0, n1, z0, z1, folder, mat, nocoll=True):
    c0, c1 = at(t["x"], t["y"], t["side"], s0, n0), at(t["x"], t["y"], t["side"], s1, n1)
    put(label, CUBE, min(c0[0], c1[0]), min(c0[1], c1[1]), z0, 0, (abs(c1[0] - c0[0]) / 100.0, abs(c1[1] - c0[1]) / 100.0, (z1 - z0) / 100.0),
        folder=folder, mats=[mat], nocoll=nocoll)


def _rod(label, a3, b3, thick, mat, folder, draw):
    """A thin box from a3 to b3: a span of wire, a conduit, a bar of rebar. Twelve triangles."""
    d3 = (b3[0] - a3[0], b3[1] - a3[1], b3[2] - a3[2])
    len_ = math.sqrt(sum(c * c for c in d3))
    X3 = (d3[0] / len_, d3[1] / len_, d3[2] / len_)
    h_ = math.hypot(X3[0], X3[1])
    Y3 = (-X3[1] / h_, X3[0] / h_, 0.0) if h_ > 1e-4 else (1.0, 0.0, 0.0)
    put_board(label, CUBE, ((a3[0] + b3[0]) / 2, (a3[1] + b3[1]) / 2, (a3[2] + b3[2]) / 2), X3, Y3, v_cross(X3, Y3), (len_ + 0.3, thick, thick),
              mats=[mat], nocoll=True)
    items[-1]["folder"] = folder
    _cheap(draw, 1, True)


# Shop fronts: closed roll-up shutters, each with a blank sign over it; steel gates; tarps over a wall or half across a door. On ground-floor
# tiles nothing else has taken. A good share stays bare, and one to a house, so a street doesn't read as a row of shops.
FRONT_RNG = random.Random(181)
SHUTTERS, GATES, WALL_TARPS, EXTRA_SIGNS = 8, 4, 4, 5
SIGN_LONG = 2.6       # a sign's width to its height, at least
ROLL_MATS = (AM + "MI_RollUp_A_001", AM + "MI_RollUp_A_002")
TARP_MATS = (AM + "MI_TarpCover_A_001_Blue", AM + "MI_TarpCover_A_001_Blue", AM + "MI_TarpCover_A_001_White")
SIGN_MATS = tuple(BM + "MI_BackAlleys_Sign_" + k for k in ("Red", "Yellow", "White", "Blue"))
_draw_sign = shuffle_bag(FRONT_RNG, SIGN_MATS)
_draw_roll = shuffle_bag(FRONT_RNG, ROLL_MATS)
_draw_tarp = shuffle_bag(FRONT_RNG, TARP_MATS)
_shops = []
_front_houses = set()


def _sign_board(label, t, s_mid, width, z_low, kind_h):
    """SM_Sign_A_001: centred pivot, 300 x 84, 13 thick. Over the trim, and over a protruding band if there is one. Always long: user, "square
    signage may fit chinese characters but not alphanumerics"."""
    nat_w, nat_h = 300.0, 84.0
    kind_h = min(kind_h, width / SIGN_LONG)
    x_, y_ = at(t["x"], t["y"], t["side"], s_mid, 14.0 + _band_out(t))
    put(label, AS + "SM_Sign_A_001", x_, y_, z_low + kind_h / 2, YAW[t["side"]], (width / nat_w, 1.0, kind_h / nat_h), folder=DR_SIGNS, nocoll=True,
        mats=[_draw_sign(), AM + "MI_MetalFrame_A_001_Black"])
    _cheap(CULL_MID)


if STREET_FRONTS:
    _front_ts = [u for u in _wall_tiles if u["s"] == 0 and u["dress"] is not None and u["w"] >= 125.0 and not [k for k in u["dress"]["has"] if k != "vent"]]
    FRONT_RNG.shuffle(_front_ts)
    _n_sh, _n_ga, _n_ta = 0, 0, 0
    _draw_front = shuffle_bag(FRONT_RNG, ("shutter", "shutter", "shutter", "gate", "tarp"))
    FRONT_TOP = {"shutter": 375.0, "gate": 246.0, "tarp": 232.0}     # how much wall each takes, a shutter's sign included
    for u in _front_ts:
        if (u["house"], u["letter"]) in _front_houses:
            continue
        if not all(_ground_open(u, s_, 110.0) for s_ in (10.0, u["w"] / 2, u["w"] - 10.0)) or not _stair_clear(u, 0.0, u["w"], u["z"]) or \
                not _pipe_free(u, 0.0, u["w"]):
            continue
        kind = _draw_front()
        in0, in1 = _inside_face(u, 0.0, u["w"])
        room_ = in1 - in0
        FRONT_MIN = {"shutter": 122.0, "gate": 110.0, "tarp": 98.0}
        for _try in range(3):
            if room_ < FRONT_MIN[kind] or not _free(_wbox(u, 0.0, u["w"], u["z"], u["z"] + FRONT_TOP[kind])) or \
                    (kind == "shutter" and _n_sh >= SHUTTERS) or (kind == "gate" and _n_ga >= GATES) or (kind == "tarp" and _n_ta >= WALL_TARPS):
                kind = {"shutter": "gate", "gate": "tarp", "tarp": "shutter"}[kind]
            else:
                break
        else:
            continue
        side, w_ = u["side"], u["w"]
        if kind == "shutter":
            # SM_RollupDoor_A_001: X 0..191 along the wall, Z -277..0 from its top, a lip 11 cm either side of Y 0. Local Y is out.
            wid = min(room_ - 14.0, w_ - 24.0, FRONT_RNG.uniform(180.0, 205.0))        # 7 a side: its rails, its box and the sign over it
            s0 = in0 + 7.0 + FRONT_RNG.uniform(0.0, room_ - 14.0 - wid)
            top = u["z"] + 268.0
            x_, y_ = at(u["x"], u["y"], side, s0, 6.0)
            put("Shutter_" + u["label"], AS + "SM_RollupDoor_A_001", x_, y_, top, YAW[side], (wid / 190.9, 1.0, (268.0 - 5.0) / 277.0), folder=DR_SHUTTERS,
                mats=[_draw_roll()])
            _cheap(CULL_FAR)
            _wall_cube("Shutter_%s_Box" % u["label"], u, s0 - 6.0, s0 + wid + 6.0, -2.0, 15.0, top - 4.0, top + 20.0, DR_SHUTTERS, FLASH_MAT)
            _cheap(CULL_FAR)
            for e_, s_ in enumerate((s0 - 5.0, s0 + wid)):
                _wall_cube("Shutter_%s_Rail%d" % (u["label"], e_), u, s_, s_ + 5.0, -2.0, 9.0, u["z"] + 3.0, top, DR_SHUTTERS, FLASH_MAT)
                _cheap(CULL_MID, 1, True)
            sign_h = FRONT_RNG.choice((58.0, 66.0, 72.0))
            _sign_board("Sign_" + u["label"], u, s0 + wid / 2, wid + FRONT_RNG.uniform(-8.0, 12.0), u["z"] + 290.0, sign_h)
            _shops.append((u, s0, wid))
            _n_sh += 1
            _count("shutters")
        elif kind == "gate":
            # SM_Metal_Gate_01: X -1.7..164 along the wall, Y -7.6..4.2, Z 0..241.
            sa = min(1.0, (room_ - 4.0) / 165.8, (w_ - 30.0) / 165.8)
            s0 = (in0 + in1 - 165.8 * sa) / 2
            x_, y_ = at(u["x"], u["y"], side, s0 + 1.7 * sa, 8.0)
            put("Gate_" + u["label"], FV + "SM_Metal_Gate_01", x_, y_, u["z"] + 2.0, YAW[side], (sa, 1.0, 1.0), folder=DR_GATES)
            _cheap(CULL_FAR)
            _n_ga += 1
            _count("gates")
        else:
            # SM_TarpCover_A_002: 223 wide, hanging 183 from its rod. Blue plastic mostly, the way Manila uses it.
            sa = min(w_ - 40.0, room_ - 4.0) / 223.0
            x_, y_ = at(u["x"], u["y"], side, (in0 + in1) / 2, 12.0)
            put("Tarp_" + u["label"], AS + "SM_TarpCover_A_002", x_, y_, u["z"] + FRONT_RNG.uniform(218.0, 228.0), YAW[side], (sa, 1.0, FRONT_RNG.uniform(0.9, 1.15)),
                folder=DR_TARPS, nocoll=True, mats=[_draw_tarp(), AM + "MI_RollUp_A_001"])
            _cheap(CULL_MID)
            _n_ta += 1
            _count("wall tarps")
        u["dress"]["has"].append(kind)
        _front_houses.add((u["house"], u["letter"]))
        _claim(_wbox(u, 0.0, w_, u["z"], u["z"] + FRONT_TOP[kind]))
    # A steel gate in front of a door, covering it and a little of the wall either side. Ground doors with no awning.
    _door_ts2 = [u for u in _wall_tiles if u["s"] == 0 and u["kind"] == "SM_WallDoor_01" and u["label"] not in _has_awn]
    FRONT_RNG.shuffle(_door_ts2)
    def _door_inside(u, half):
        in0_, in1_ = _inside_face(u, 0.0, u["w"])
        return in0_ <= 111.0 * u["sx"] - half and 111.0 * u["sx"] + half <= in1_

    for u in _door_ts2:
        if _n_ga >= GATES or (u["house"], u["letter"]) in _front_houses or not _ground_open(u, 111.0 * u["sx"], 60.0) or not _door_inside(u, 55.0 * u["sx"] + 11.0):
            continue
        sa = (110.0 * u["sx"] + 22.0) / 165.8
        x_, y_ = at(u["x"], u["y"], u["side"], 111.0 * u["sx"] - 82.9 * sa + 1.7 * sa, 8.0)
        put("Gate_" + u["label"], FV + "SM_Metal_Gate_01", x_, y_, u["z"] + 2.0, YAW[u["side"]], (sa, 1.0, 232.0 / 240.7), folder=DR_GATES)
        _cheap(CULL_FAR)
        _front_houses.add((u["house"], u["letter"]))
        _n_ga += 1
        _count("gates")
    # No tarps on doors. User 2026-11-06: "dont put a tarp on the doors". Tarps go on plain wall only, above. The four doors that had one keep their draws and their place in
    # _front_houses, so that nothing else in the level moves: taking them out reshuffled every wire, poster and lamp after this point.
    _door_slots = 4
    for u in _door_ts2:
        if _door_slots <= 0 or (u["house"], u["letter"]) in _front_houses or not _ground_open(u, 111.0 * u["sx"], 60.0) or not _door_inside(u, 55.0 * u["sx"] + 12.0):
            continue
        FRONT_RNG.uniform(0.85, 1.0)
        _draw_tarp()
        _front_houses.add((u["house"], u["letter"]))
        _door_slots -= 1
    # A few signs with no shop under them: long boards over a door or a window, where a shop's would go. Blank walls stay free for the meters.
    _sign_ts = [u for u in _wall_tiles if u["s"] == 0 and u["w"] >= 190.0 and not _hollow_face(u) and (u["house"], u["letter"]) not in _front_houses and
                u["kind"] in ("SM_WallDoor_01", "SM_Wall_Windows_01")]
    FRONT_RNG.shuffle(_sign_ts)
    _sign_xy = []
    for u in _sign_ts:
        if _street_n.get("wall signs", 0) >= EXTRA_SIGNS:
            break
        in0, in1 = _inside_face(u, 0.0, u["w"])
        wid = min(u["w"] - 16.0, in1 - in0, FRONT_RNG.uniform(185.0, 280.0))
        h_ = FRONT_RNG.choice((58.0, 66.0, 72.0))
        if wid < 150.0:
            continue
        s_mid = (in0 + in1) / 2
        s0, s1 = s_mid - wid / 2, s_mid + wid / 2
        z_ = u["z"] + 290.0
        x_, y_ = at(u["x"], u["y"], u["side"], u["w"] / 2, 0.0)
        box = _wbox(u, s0, s1, z_, z_ + h_)
        if not all(_ground_open(u, s_, 90.0) and _reach_clear(u, s_, 30.0, z_) for s_ in (s0, u["w"] / 2, s1)) or not _pipe_free(u, s0, s1) or                 not _stair_clear(u, s0, s1, z_) or any(math.hypot(x_ - o[0], y_ - o[1]) < 900.0 for o in _sign_xy) or not _free(box):
            continue
        _sign_board("WallSign_" + u["label"], u, s_mid, wid, z_, h_)
        _sign_xy.append((x_, y_))
        _claim(box)
        _front_houses.add((u["house"], u["letter"]))
        _count("wall signs")


# Wires. A span leaves a junction box on the band at the top of a second storey, crosses the alley on a slant and ends in a box on the wall
# opposite, a storey up, so everything overhead sits above the laundry and over the gallery's headroom. Bundles of one to three, each with its
# own sag. Never through a house, a room or over a roof too low to clear. Meter boxes low on a ground-floor wall feed their conduit up to one of
# these boxes, so a wire always arrives at a house for a reason. Others run along a wall from box to box. Thin boxes, three or four to a span,
# culled at CULL_FAR: they're the outline against the sky, so they stay on longer than the laundry.
WIRE_RNG = random.Random(191)
METERS_WANTED, SPANS_WANTED, ALONG_WANTED = 13, 30, 16
WIRE_GAP_MIN, WIRE_GAP_MAX, WIRE_LOW = 250.0, 900.0, 560.0
SPAN_SPACING = 140.0      # between the middles of two spans. User: "power lines are a big identity show for the philippines"
_draw_wires = shuffle_bag(WIRE_RNG, (2, 2, 3, 3, 3, 4, 4, 5, 6))
_span_mids = []
_wire_lows = []
_wire_runs, _wire_nodes = [], []        # every wire and junction box, for the chains below


def _wire(label, a3, b3, sag, segs, thick, draw=None):
    """One wire from a3 to b3, a parabola of thin boxes."""
    pts = []
    for k in range(segs + 1):
        u_ = k / float(segs)
        pts.append((a3[0] + (b3[0] - a3[0]) * u_, a3[1] + (b3[1] - a3[1]) * u_, a3[2] + (b3[2] - a3[2]) * u_ - 4.0 * sag * u_ * (1.0 - u_)))
    for k in range(segs):
        _rod("%s_%d" % (label, k), pts[k], pts[k + 1], thick, WIRE_MAT, DR_WIRES, draw or CULL_FAR)
    _wire_lows.append(min(p_[2] for p_ in pts))
    _wire_runs.append((label, a3, b3))


def _box_on_wall(label, X_, Y_, z_, yaw_):
    """SM_ElectricBox_C_002: 28 x 12 x 10, back on the wall, twelve triangles."""
    k = WIRE_RNG.uniform(0.7, 1.0)
    put(label, AS + "SM_ElectricBox_C_002", X_, Y_, z_ - 4.8 * k, yaw_, (k, k, k), folder=DR_WIRES, nocoll=True)
    _cheap(CULL_MID, 1, True)
    _wire_nodes.append({"label": label, "x": X_, "y": Y_, "z": z_, "side": next(s_ for s_, y_ in YAW.items() if y_ == yaw_)})


def _path_clear(a3, b3, me, other):
    """Nothing in a wire's way: no house it would pass through, a roof it would touch, a room or a door's end wall."""
    for k in range(1, 12):
        u_ = k / 12.0
        X_, Y_, Z_ = a3[0] + (b3[0] - a3[0]) * u_, a3[1] + (b3[1] - a3[1]) * u_, a3[2] + (b3[2] - a3[2]) * u_
        lx, ly = _lay(X_, Y_)
        if not (0 < lx < W and 0 < ly < H) or _in_room(X_, Y_) or not _clear_of_end_walls(lx, ly, 0.3):
            return False
        for o in BLOCKS.values():
            if o["x0"] < lx < o["x1"] and o["y0"] < ly < o["y1"]:
                if o is me or o is other:
                    return False
                top_ = o["storeys"] * o["sh"] + FLOOR_H
                if top_ + {"terrace": 330.0, "metal": 260.0}.get(o["roof"], 70.0) > Z_:
                    return False
    return True


def _band_z(b, st):
    return FLOOR_H + st * b["sh"] + 300.0 + WIRE_RNG.uniform(0.3, 0.7) * (b["sh"] - 300.0)


def _try_span(t, s_local, z_a, n_a, label):
    """A bundle from a point on tile t to the wall across the alley. False if no way across is clear."""
    side = t["side"]
    me = BLOCKS[t["bid"]]
    slopes = [-0.55, -0.35, -0.18, 0.0, 0.18, 0.35, 0.55]
    WIRE_RNG.shuffle(slopes)
    letter_o = OPP[side][0].upper()
    for slope in slopes:
        hit, o = None, None
        for n_ in range(120, int(WIRE_GAP_MAX) + 10, 5):
            lx, ly = _lay(*at(t["x"], t["y"], side, s_local + slope * n_, float(n_)))
            if not (0 < lx < W and 0 < ly < H):
                break
            o = next((b_ for b_ in BLOCKS.values() if b_["x0"] < lx < b_["x1"] and b_["y0"] < ly < b_["y1"] and b_["storeys"] > 1), None)
            if o is not None:
                hit = float(n_)
                break
        if hit is None or o is me or not WIRE_GAP_MIN <= hit <= WIRE_GAP_MAX:
            continue
        ho = _house_of(o["id"])
        if o["id"] in _thin_blocks or o.get("balcony") or (ho, letter_o) in _hset:
            continue
        # It has to meet the face opposite, not come in along a side wall.
        lx0, ly0 = _lay(*at(t["x"], t["y"], side, s_local + slope * (hit - 6.0), hit - 6.0))
        if side in ("east", "west"):
            if not o["y0"] + 0.25 < ly0 < o["y1"] - 0.25:
                continue
        elif not o["x0"] + 0.25 < lx0 < o["x1"] - 0.25:
            continue
        n_b = hit - 10.0 - (BAND_OUT if (ho, letter_o) in _proud and o["storeys"] > 2 else 0.0)
        X0, Y0 = at(t["x"], t["y"], side, s_local, n_a)
        X1, Y1 = at(t["x"], t["y"], side, s_local + slope * n_b, n_b)
        z_b = _band_z(o, 1)
        if abs(z_b - z_a) > 170.0:
            continue
        a3, b3 = (X0, Y0, z_a), (X1, Y1, z_b)
        mid = ((X0 + X1) / 2, (Y0 + Y1) / 2)
        if not _path_clear(a3, b3, me, o) or any(math.hypot(mid[0] - m[0], mid[1] - m[1]) < SPAN_SPACING for m in _span_mids):
            continue
        box_b = (X1 - 34.0, Y1 - 34.0, z_b - 12.0, X1 + 34.0, Y1 + 34.0, z_b + 12.0)
        if not _free(box_b, 2.0):
            continue
        gap = math.hypot(X1 - X0, Y1 - Y0)
        segs = 3 if gap < 420.0 else 4
        rx, ry = RUN[side]
        for j in range(_draw_wires()):
            wob = WIRE_RNG.uniform(-20.0, 20.0) if j else 0.0
            wz = WIRE_RNG.uniform(-5.0, 5.0) if j else 0.0
            a_ = (X0 + rx * wob, Y0 + ry * wob, z_a + wz)
            b_ = (X1 + rx * wob * WIRE_RNG.uniform(0.4, 1.6), Y1 + ry * wob * WIRE_RNG.uniform(0.4, 1.6), z_b + wz)
            _wire("%s_W%d" % (label, j), a_, b_, WIRE_RNG.uniform(10.0, 24.0) * gap / 400.0, segs, WIRE_RNG.uniform(1.5, 2.2))
            _count("wires")
        nx, ny = NORMAL[side]
        _box_on_wall(label + "_BoxB", X1 - nx * (-10.0), Y1 - ny * (-10.0), z_b, YAW[OPP[side]])
        _claim(box_b)
        _span_mids.append(mid)
        return True
    return False


if STREET_WIRES:
    # Meter boxes first: they need the most room.
    _meter_ts = [u for u in _wall_tiles if u["s"] == 0 and u["dress"] is not None and u["w"] >= 100.0 and not [k for k in u["dress"]["has"] if k != "vent"]]
    WIRE_RNG.shuffle(_meter_ts)
    _meter_houses = set()
    for u in _meter_ts * 2:     # twice: a tile can fail on its random end, and each house should get a fair go
        if _street_n.get("meters", 0) >= METERS_WANTED:
            break
        if u["house"] in _meter_houses or u["house"] in _laundry_houses and WIRE_RNG.random() < 0.3:
            continue
        side = u["side"]
        s_ = WIRE_RNG.choice((WIRE_RNG.uniform(15.0, 26.0), u["w"] - WIRE_RNG.uniform(15.0, 26.0)))
        in0, in1 = _inside_face(u, 0.0, u["w"])
        if s_ - 13.0 < in0 or s_ + 13.0 > in1:
            continue
        b_ = BLOCKS[u["bid"]]
        two = b_["storeys"] >= 2 and not b_.get("balcony")
        up = _tile_above(u, s_, 1) if two else None
        if two and (up is None or not _edge_ok(up[0], up[1], 4.0) or _hollow_face(up[0])):
            continue
        z_m = u["z"] + WIRE_RNG.uniform(165.0, 195.0)
        z_b = _band_z(b_, 1) if two else FLOOR_H + b_["sh"] + 2.0
        st_ = _style.get(u["house"], "border")
        n_c = ({"proud": 17.0, "border": 9.0}.get(st_, 4.0)) if two else 9.0
        if not _ground_open(u, s_, 70.0) or not _pipe_free(u, s_ - 20.0, s_ + 20.0) or not _stair_clear(u, s_ - 20.0, s_ + 20.0, u["z"]) or \
                not _free(_wbox(u, s_ - 18.0, s_ + 18.0, z_m, z_b + 12.0)):
            continue
        X_, Y_ = at(u["x"], u["y"], side, s_, 0.0)
        label = "Meter_" + u["label"]
        fed = two and _try_span(u, s_, z_b, n_c + 8.0, "Span_" + u["label"])
        if two and not fed:
            # Along the wall from its box, to a box further down the same run, on a stretch that's clear.
            ts_ = _run_tiles.get(up[0]["run"], ())
            a_at = up[0]["off"] + up[1]
            total = ts_[-1]["off"] + ts_[-1]["w"] - ts_[0]["off"] if ts_ else 0.0
            for dir_ in WIRE_RNG.sample((-1.0, 1.0), 2):
                len_ = WIRE_RNG.uniform(240.0, 520.0)
                end_ = a_at + dir_ * len_
                if end_ < 20.0 or end_ > total - 20.0:
                    continue
                t0 = ts_[0]
                lo_, hi_ = min(a_at, end_), max(a_at, end_)
                if not _pipe_free(t0, lo_ - 8.0, hi_ + 8.0) or not _free(_wbox(t0, lo_ + 18.0, hi_ + 18.0 if dir_ > 0 else hi_ - 18.0, z_b - 12.0, z_b + 12.0), 2.0) or \
                        not all(_ground_open(t0, lo_ + (hi_ - lo_) * k_ / 4.0, 40.0) for k_ in range(5)):
                    continue
                a3 = tuple(at(t0["x"], t0["y"], side, a_at, n_c + 8.0)) + (z_b,)
                b3 = tuple(at(t0["x"], t0["y"], side, end_, n_c + 8.0)) + (z_b + WIRE_RNG.uniform(-5.0, 5.0),)
                _wire("Along_%s_W0" % u["label"], a3, b3, WIRE_RNG.uniform(2.0, 5.0) * len_ / 300.0, 3, 1.7)
                Xb, Yb = at(t0["x"], t0["y"], side, end_, _band_out(up[0]))
                _box_on_wall("Along_%s_Box" % u["label"], Xb, Yb, z_b, YAW[side])
                _claim(_wbox(t0, lo_ - 14.0, hi_ + 14.0, z_b - 12.0, z_b + 12.0))
                _count("along walls")
                fed = True
                break
        put(label, AS + "SM_ElectricBox_C_003", X_, Y_, z_m, YAW[side], (1, 1, 1), folder=DR_METERS)
        _cheap(CULL_MID)
        d_ = 34.0 if s_ < u["w"] / 2 else -34.0
        if WIRE_RNG.random() < 0.3 and u["w"] >= 130.0 and _free(_wbox(u, s_ + d_ - 16.0, s_ + d_ + 16.0, z_m, z_m + 38.0)):    # now and then two side by side
            X2, Y2 = at(u["x"], u["y"], side, s_ + d_, 0.0)
            put(label + "_2", AS + "SM_ElectricBox_C_003", X2, Y2, z_m, YAW[side], (1, 1, 1), folder=DR_METERS)
            _cheap(CULL_MID)
        Xc, Yc = at(u["x"], u["y"], side, s_, n_c)
        _rod(label + "_Conduit", (Xc, Yc, z_m + 34.0), (Xc, Yc, z_b), 3.2, FLASH_MAT, DR_METERS, CULL_MID)
        if two:
            Xb, Yb = at(u["x"], u["y"], side, s_, max(n_c - 7.0, 0.0))
            _box_on_wall(label + "_Box", Xb, Yb, z_b, YAW[side])
        _claim(_wbox(u, s_ - 18.0, s_ + 18.0, z_m, z_b + 12.0))
        u["dress"]["has"].append("meter")
        _meter_houses.add(u["house"])
        _count("meters")
    # Spans with no meter of their own, for the tangle overhead.
    _span_ts = [u for u in _wall_tiles if u["s"] == 1 and BLOCKS[u["bid"]]["storeys"] >= 2 and not BLOCKS[u["bid"]].get("balcony") and not _hollow_face(u)
                and u["w"] >= 100.0]
    WIRE_RNG.shuffle(_span_ts)
    _n_extra = 0
    for u in _span_ts:
        if _n_extra >= SPANS_WANTED:
            break
        s_ = WIRE_RNG.uniform(24.0, u["w"] - 24.0)
        z_a = _band_z(BLOCKS[u["bid"]], 1)
        n_a = _band_out(u) + 10.0
        if not _ground_open(u, s_, 70.0) or not _pipe_free(u, s_ - 16.0, s_ + 16.0) or not _free(_wbox(u, s_ - 16.0, s_ + 16.0, z_a - 12.0, z_a + 12.0), 2.0):
            continue
        if not _try_span(u, s_, z_a, n_a, "Span_" + u["label"]):
            continue
        Xb, Yb = at(u["x"], u["y"], u["side"], s_, _band_out(u))
        _box_on_wall("Span_%s_Box" % u["label"], Xb, Yb, z_a, YAW[u["side"]])
        _claim(_wbox(u, s_ - 16.0, s_ + 16.0, z_a - 12.0, z_a + 12.0))
        _n_extra += 1
        _count("spans")
    # Along a wall, box to box, on one straight run.
    _along_runs = [k for k in _run_tiles if _run_tiles[k][0]["s"] == 1 and BLOCKS[_run_tiles[k][0]["bid"]]["storeys"] >= 2 and
                   not BLOCKS[_run_tiles[k][0]["bid"]].get("balcony") and not _hollow_face(_run_tiles[k][0])]
    WIRE_RNG.shuffle(_along_runs)
    for name in _along_runs:
        if _street_n.get("along walls", 0) >= ALONG_WANTED:
            break
        ts = _run_tiles[name]
        t0 = ts[0]
        total = ts[-1]["off"] - t0["off"] + ts[-1]["w"]
        if total < 330.0:
            continue
        len_ = WIRE_RNG.uniform(260.0, min(total - 50.0, 620.0))
        s0 = WIRE_RNG.uniform(25.0, total - len_ - 25.0)
        z_a = _band_z(BLOCKS[t0["bid"]], 1)
        n_a = _band_out(t0) + 10.0
        if not _pipe_free(t0, s0 - 10.0, s0 + len_ + 10.0) or not _free(_wbox(t0, s0 - 16.0, s0 + len_ + 16.0, z_a - 12.0, z_a + 12.0), 2.0) or \
                not all(_ground_open(t0, s0 + len_ * k_ / 4.0, 40.0) for k_ in range(5)):
            continue
        a3 = tuple(at(t0["x"], t0["y"], t0["side"], s0, n_a)) + (z_a,)
        b3 = tuple(at(t0["x"], t0["y"], t0["side"], s0 + len_, n_a)) + (z_a + WIRE_RNG.uniform(-6.0, 6.0),)
        label = "Along_%s" % name
        for j in range(WIRE_RNG.choice((1, 2, 2, 3, 3, 4))):
            _wire("%s_W%d" % (label, j), (a3[0], a3[1], a3[2] - 3.5 * j), (b3[0], b3[1], b3[2] - 3.5 * j), WIRE_RNG.uniform(2.0, 5.0) * len_ / 300.0, 3, 1.6)
        for e_, s_ in enumerate((s0, s0 + len_)):
            Xb, Yb = at(t0["x"], t0["y"], t0["side"], s_, _band_out(t0))
            _box_on_wall("%s_Box%d" % (label, e_), Xb, Yb, z_a, YAW[t0["side"]])
        _claim(_wbox(t0, s0 - 16.0, s0 + len_ + 16.0, z_a - 12.0, z_a + 12.0))
        _count("along walls")
    assert not _wire_lows or min(_wire_lows) >= WIRE_LOW, "a wire hangs at %.0f" % min(_wire_lows)      # second floor, above the laundry


# Rooftops. Favela's water tank: the tub on its plank stand, on four legs where it stands clear of a roof. Low under the terraces' roofs, tall on
# the flat roofs and over the metal ones, whose legs go through the sheets, as they do. The tub keeps its collision. TV aerials stand near a
# corner of the roof, leaning a little, all pointing about the same way, as they would at one transmitter, and a plain mast here and there.
TANK_RNG = random.Random(193)
TANK_METAL, AERIALS_WANTED = 6, 12
TANK_COLOURS = (FM + "MI_Barrel_01", FM + "MI_Barrel_01", FM + "MI_Barrel_Color_01", FM + "MI_Barrel_Color_02")
_draw_tank_colour = shuffle_bag(TANK_RNG, TANK_COLOURS)
_roof_z = {}
for p in items:
    if p["folder"] == RF and p["label"].startswith("Roof_"):
        k_ = p["label"].split("_")[1]
        _roof_z[k_] = max(_roof_z.get(k_, 0.0), p["loc"][2])
_roof_things = []


def _tank(label, x_, y_, z_floor, tall, k, over=None):
    yaw_ = TANK_RNG.uniform(0.0, 360.0)
    c, s_ = math.cos(math.radians(yaw_)), math.sin(math.radians(yaw_))
    stand_z = z_floor
    n_ = 0
    if tall:
        stand_z = max(z_floor + TANK_RNG.uniform(112.0, 130.0), (over or 0.0) + 22.0)
        for j, (dx, dy) in enumerate(((-57.0, -30.0), (57.0, -30.0), (-57.0, 30.0), (57.0, 30.0))):
            put("%s_Leg%d" % (label, j), FV + "SM_Fencing_03", x_ + (c * dx - s_ * dy) * k, y_ + (s_ * dx + c * dy) * k, z_floor, yaw_,
                (0.55, 0.55, (stand_z - z_floor) / 117.6), folder=DR_TANKS, nocoll=True)
            n_ += 1
    put(label + "_Stand", FV + "SM_Stand_01", x_, y_, stand_z, yaw_, (k, k, k), folder=DR_TANKS, nocoll=True)
    put(label, FV + "SM_Barrel_01", x_, y_, stand_z + 59.5 * k, TANK_RNG.uniform(0.0, 360.0), (k, k, k), folder=DR_TANKS, mats=[_draw_tank_colour()])
    put(label + "_Cap", FV + TANK_RNG.choice(("SM_Barrel_Cap_01", "SM_Barrel_Cap_2")), x_, y_, stand_z + (59.5 + 85.2) * k, TANK_RNG.uniform(0.0, 360.0), (k, k, k),
        folder=DR_TANKS, nocoll=True)
    _cheap(CULL_FAR, n_ + 3)
    _roof_things.append((x_, y_))
    _count("tanks")


def _roof_spot(rng, b, inset, tries=40, avoid=()):
    """A point on house b at least inset (m) in from its edges and away from avoid, in UE."""
    x0, y0, x1, y1 = b["x0"] + inset, b["y0"] + inset, b["x1"] - inset, b["y1"] - inset
    if x0 >= x1 or y0 >= y1:
        return None
    for _ in range(tries):
        X_, Y_ = ue(rng.uniform(x0, x1), rng.uniform(y0, y1))
        if all(math.hypot(X_ - o[0], Y_ - o[1]) > 190.0 for o in _roof_things) and all(math.hypot(X_ - o[0], Y_ - o[1]) > 95.0 for o in avoid):
            return X_, Y_
    return None


if STREET_ROOFTOPS:
    _posts = [(p["loc"][0], p["loc"][1]) for p in items if p["folder"] == TER and p["label"].startswith(("Post_", "AwnPost_"))]
    _up_doors = [at(u["x"], u["y"], u["side"], 111.0 * u["sx"], 60.0) for u in _wall_tiles if u["kind"] == "SM_WallDoor_01" and u["s"] >= 1]
    # Terraces: the wide ones have room to walk round a tank, and a roof over them, so it stands low.
    for bid, b in sorted(BLOCKS.items()):
        if b["roof"] == "terrace" and min(b["x1"] - b["x0"], b["y1"] - b["y0"]) >= 2.4:
            spot = _roof_spot(TANK_RNG, b, 0.72, avoid=_posts + _up_doors)
            if spot:
                _tank("Tank_" + bid, spot[0], spot[1], b["sh"] - 5.0 + FLOOR_H, False, 0.85)
    for bid, b in sorted(BLOCKS.items()):
        if b["roof"] == "flat":
            spot = _roof_spot(TANK_RNG, b, 1.0)
            if spot:
                _tank("Tank_" + bid, spot[0], spot[1], b["storeys"] * b["sh"] + FLOOR_H - 5.0, True, TANK_RNG.uniform(0.85, 1.0))
    _metal_ids = [k for k, b in sorted(BLOCKS.items()) if k in _roof_z and min(b["x1"] - b["x0"], b["y1"] - b["y0"]) >= 3.0]
    TANK_RNG.shuffle(_metal_ids)
    _n_mt = 0
    for bid in _metal_ids:
        if _n_mt >= TANK_METAL:
            break
        b = BLOCKS[bid]
        spot = _roof_spot(TANK_RNG, b, 1.1)
        if spot:
            _tank("Tank_" + bid, spot[0], spot[1], b["storeys"] * b["sh"] + FLOOR_H - 5.0, True, TANK_RNG.uniform(0.8, 0.95), over=_roof_z[bid])
            _n_mt += 1
    # Aerials: AsiaSlum's, with their four LODs; A_001 at 11k stays rare. SM_Antenna_01 is a plain mast, 244 triangles.
    AER_DIR = TANK_RNG.uniform(0.0, 360.0)
    _draw_aerial = shuffle_bag(TANK_RNG, (AS + "SM_Antenna_A_002", AS + "SM_Antenna_A_002", AS + "SM_Antenna_A_002", AS + "SM_Antenna_A_003",
                                          AS + "SM_Antenna_A_003", AS + "SM_Antenna_A_003", AS + "SM_Antenna_A_001", ME + "MiddleEast/SM_Antenna_01"))
    _aer_ids = [k for k, b in sorted(BLOCKS.items()) if b["roof"] in ("metal", "flat") and k not in _thin_blocks and not b.get("balcony")]
    TANK_RNG.shuffle(_aer_ids)
    _aer_xy = []
    for bid in _aer_ids:
        if _street_n.get("aerials", 0) >= AERIALS_WANTED:
            break
        b = BLOCKS[bid]
        T_ = b["storeys"] * b["sh"] + FLOOR_H
        cx, cy = TANK_RNG.choice((b["x0"] + 0.55, b["x1"] - 0.55)), TANK_RNG.choice((b["y0"] + 0.55, b["y1"] - 0.55))
        X_, Y_ = ue(cx, cy)
        if any(cover_top(cx + dx, cy + dy, b) + FLOOR_H > T_ - 20.0 for dx in (-1.6, 1.6) for dy in (-1.6, 1.6)):
            continue                                    # a taller neighbour would stand in its arms
        if any(math.hypot(X_ - o[0], Y_ - o[1]) < 260.0 for o in _roof_things) or any(math.hypot(X_ - o[0], Y_ - o[1]) < 700.0 for o in _aer_xy):
            continue
        mesh = _draw_aerial()
        whip = mesh.endswith("SM_Antenna_01")
        k = TANK_RNG.uniform(0.6, 0.72) if whip else TANK_RNG.uniform(1.05, 1.3)
        put("Aerial_" + bid, mesh, X_, Y_, T_ - 8.0, AER_DIR + TANK_RNG.uniform(-22.0, 22.0), (k, k, k), folder=DR_AERIALS, roll=TANK_RNG.uniform(-3.0, 3.0), nocoll=True,
            mats=None if whip else [ANT_MAT])
        _cheap(CULL_FAR, 1, True)
        _aer_xy.append((X_, Y_))
        _count("aerials")


# Lights. Real ones, with their fittings: bare bulbs over doors, fluorescent tubes over shop fronts and under door awnings, cobra lamps on wall arms
# over the alleys. Static, so the bake carries them and they cost nothing at run time (the spec: baked world, dynamic per case). Warm tungsten, a
# greener tube, orange sodium: three colours to read in the dark. One to a house, lamps at least LAMP_GAP apart. The pack's bulb is hung by its
# whole cord: scaled 0.7, the cord's top meets a bracket on the band and the bulb sits above the door's head.
LIGHT_RNG = random.Random(197)
BULBS_WANTED, TUBES_WANTED, LAMPS_WANTED, LAMP_GAP = 9, 10, 8, 1000.0
COL_BULB, COL_TUBE, COL_LAMP = [1.0, 0.72, 0.44], [0.86, 1.0, 0.9], [1.0, 0.62, 0.3]


STREET_LIGHTS_ON = False    # user: "I will keep this level on daylight so the lights should be off". The fittings stay, unlit, with no light actors. True for a night version.


def _light(label, kind, x_, y_, z_, intensity, radius, colour, src=4.0, pitch=0.0, outer=60.0, length=0.0):
    if not STREET_LIGHTS_ON:
        return
    put(label, "/Script/Engine.%s" % kind, x_, y_, z_, 0.0, (1, 1, 1), folder=DR_LIGHTS)
    items[-1]["rot"][0] = pitch
    items[-1]["light"] = {"kind": kind, "intensity": intensity, "radius": radius, "colour": colour, "source": src, "outer": outer, "length": length}


_light_houses = set()


def _tube(u, s0, z_, n0=1.0):
    """Favela's fitting and tube, as the map pairs them, 120 cm long. Base on the wall."""
    side = u["side"]
    run3, out3 = (float(RUN[side][0]), float(RUN[side][1]), 0.0), (float(NORMAL[side][0]), float(NORMAL[side][1]), 0.0)
    Y3 = v_cross(out3, run3)
    k = 0.504
    x_, y_ = at(u["x"], u["y"], side, s0, n0)
    label = "Tube_" + u["label"]
    put_axes(label, FV + "SM_StreetLamp_05", run3, Y3, out3, (k, k, k), (0.0, 0.0, 0.0), (x_, y_, z_), nocoll=True, mats=None if STREET_LIGHTS_ON else [FLASH_MAT])
    items[-1]["folder"] = DR_LIGHTS
    _cheap(CULL_MID, 1, True)
    centre = (x_ + run3[0] * 6.7 * k + Y3[0] * 11.9 * k + out3[0] * 7.9 * k, y_ + run3[1] * 6.7 * k + Y3[1] * 11.9 * k + out3[1] * 7.9 * k,
              z_ + Y3[2] * 11.9 * k)
    put_axes(label + "_Glow", FV + "SM_StreetLamp_06", run3, Y3, out3, (k, k, k), (0.0, 0.0, 0.0), centre, nocoll=True,
             mats=[FM + "MI_StopSupport_03" if STREET_LIGHTS_ON else FLASH_MAT])    # the pack's tube glows whatever the hour: off, a plain grey one
    items[-1]["folder"] = DR_LIGHTS
    _cheap(CULL_MID, 1, True)
    x2, y2 = at(u["x"], u["y"], side, s0 + 60.0, n0 + 20.0)
    _light("Light_" + label, "PointLight", x2, y2, z_ - 8.0, 6.0, 520.0, COL_TUBE, src=3.0, length=110.0)
    _count("tubes")


if STREET_LIGHTS:
    # Tubes over the shop fronts, under the sign, on the shutter's box.
    LIGHT_RNG.shuffle(_shops)
    for u, s0, wid in _shops:
        if _street_n.get("tubes", 0) >= TUBES_WANTED - 3 or LIGHT_RNG.random() < 0.3:
            continue
        _tube(u, s0 + (wid - 120.0) * LIGHT_RNG.uniform(0.3, 0.7), u["z"] + 286.0, 15.5)
        _light_houses.add(u["house"])
    # Bulbs and tubes at doors.
    _door_ts3 = [u for u in _wall_tiles if u["kind"] == "SM_WallDoor_01"]
    LIGHT_RNG.shuffle(_door_ts3)
    for u in _door_ts3:
        if u["house"] in _light_houses:
            continue
        lx, ly = _lay(*at(u["x"], u["y"], u["side"], 111.0 * u["sx"], 45.0))
        dk_ = L["deck"]
        on_deck = dk_["x0"] < lx < dk_["x1"] and dk_["y0"] < ly < dk_["y1"]
        if u["s"] == 0 and not _ground_open(u, 111.0 * u["sx"], 45.0):
            continue
        if u["label"] in _has_awn or (u["s"] != 0 and not on_deck):
            if _street_n.get("tubes", 0) >= TUBES_WANTED:
                continue
            # Under the awning, on the bit of wall between the door's head and the awning's front.
            _tube(u, 111.0 * u["sx"] - 60.0, u["z"] + 234.0)
            _light_houses.add(u["house"])
            continue
        if _street_n.get("bulbs", 0) >= BULBS_WANTED:
            continue
        s_ = 111.0 * u["sx"] + LIGHT_RNG.choice((0.0, -72.0, 72.0)) * u["sx"]
        top = u["z"] + 338.0
        if not _free(_wbox(u, s_ - 10.0, s_ + 10.0, top - 110.0, top + 5.0)) or not _pipe_free(u, s_ - 10.0, s_ + 10.0):
            continue
        k = 0.7
        n_ = 26.0 + _band_out(u)
        x_, y_ = at(u["x"], u["y"], u["side"], s_, n_)
        put("Bulb_" + u["label"], AS + "SM_Light_A_002", x_, y_, top, LIGHT_RNG.uniform(0.0, 360.0), (k, k, k), folder=DR_LIGHTS, nocoll=True, mats=[LIGHT_ON] if STREET_LIGHTS_ON else None)
        _cheap(CULL_MID, 1, True)
        x0, y0 = at(u["x"], u["y"], u["side"], s_, -1.0)
        x1, y1 = at(u["x"], u["y"], u["side"], s_, n_ + 1.0)
        _rod("Bulb_%s_Arm" % u["label"], (x0, y0, top + 1.0), (x1, y1, top + 1.0), 2.2, RUST_MAT, DR_LIGHTS, CULL_MID)
        _light("Light_Bulb_" + u["label"], "PointLight", x_, y_, top - 124.0 * k, 4.5, 460.0, COL_BULB, src=3.0)
        _claim(_wbox(u, s_ - 10.0, s_ + 10.0, top - 110.0, top + 5.0))
        _light_houses.add(u["house"])
        _count("bulbs")
    # Cobra lamps on wall arms, second storey. SM_StreetLamp_02: wall at local X 0, the arm out along -X for 299 cm, Z -61..114. Scaled to reach about 2 m.
    _lamp_ts = [u for u in _wall_tiles if u["s"] == 1 and BLOCKS[u["bid"]]["storeys"] >= 2 and not BLOCKS[u["bid"]].get("balcony") and not _hollow_face(u)]
    LIGHT_RNG.shuffle(_lamp_ts)
    _lamp_xy = []
    for u in _lamp_ts:
        if _street_n.get("lamps", 0) >= LAMPS_WANTED:
            break
        k = LIGHT_RNG.uniform(0.62, 0.72)
        if u["kind"] in _plain_tile:
            s_ = LIGHT_RNG.uniform(30.0, max(30.0, u["w"] - 30.0))
        else:
            s_ = LIGHT_RNG.choice((LIGHT_RNG.uniform(14.0, 17.0) * u["sx"], u["w"] - LIGHT_RNG.uniform(14.0, 17.0) * u["sx"]))
        z_ = u["z"] + LIGHT_RNG.uniform(175.0, 205.0)
        reach = 299.0 * k
        x_, y_ = at(u["x"], u["y"], u["side"], s_, 1.0)
        if not _edge_ok(u, s_, 12.0) or any(math.hypot(x_ - o[0], y_ - o[1]) < LAMP_GAP for o in _lamp_xy) or not _pipe_free(u, s_ - 16.0, s_ + 16.0) or \
                not all(_ground_open(u, s_, n_) and _reach_clear(u, s_, n_, z_ + 60.0) and not _in_room(*at(u["x"], u["y"], u["side"], s_, n_))
                        for n_ in (60.0, reach * 0.5, reach, reach + 100.0)) or \
                not _free(_wbox(u, s_ - 18.0, s_ + 18.0, z_ - 45.0, z_ + 85.0, 60.0)):
            continue
        # The pack's lamp material glows whatever the hour (EmissiveMultiply 3). Off, our plain galvanised metal: a child of the pack's would break "nothing we make has a pack parent".
        put("Lamp_" + u["label"], FV + "SM_StreetLamp_02", x_, y_, z_, YAW[u["side"]] - 90.0, (k, k, k), folder=DR_LIGHTS, nocoll=True, mats=None if STREET_LIGHTS_ON else [FLASH_MAT])
        _cheap(CULL_FAR)
        hx, hy = at(u["x"], u["y"], u["side"], s_, 280.0 * k)
        _light("Light_Lamp_" + u["label"], "SpotLight", hx, hy, z_ + 20.0 * k, 40.0, 1200.0, COL_LAMP, src=8.0, pitch=-90.0, outer=66.0)
        _claim(_wbox(u, s_ - 18.0, s_ + 18.0, z_ - 45.0, z_ + 85.0, 60.0))
        _lamp_xy.append((x_, y_))
        _count("lamps")


# Small details. Concrete sills under windows, in the band's material so a painted face stays one colour; a face has them or doesn't, one in ten
# missing. Rebar: a stub of column at a roof's corner with bars left for the next floor, as houses built a storey at a time have. Peeling paint:
# our decal, bare render through painted faces only, low on the wall and beside corners, never on a tile with something on it.
DETAIL_RNG = random.Random(199)
P_SILL_FACE, P_SILL_MISS, P_REBAR = 0.55, 0.1, 0.65
PEEL_MATS = (BM + "MI_BackAlleys_Peel_A", BM + "MI_BackAlleys_Peel_B")
_draw_peel = shuffle_bag(DETAIL_RNG, PEEL_MATS)
_draw_peels = shuffle_bag(DETAIL_RNG, (0, 1, 1, 2, 2, 3))

if STREET_DETAILS:
    _rack_tiles = {p["label"][5:] for p in items if p["label"].startswith("Rack_")}
    _sill_faces = {}
    for u in _wall_tiles:
        if u["kind"] != "SM_Wall_Windows_01" or u["label"] in _rack_tiles:
            continue
        f = (u["house"], u["letter"])
        if f not in _sill_faces:
            _sill_faces[f] = DETAIL_RNG.choice(("slab", "slab", "deep")) if DETAIL_RNG.random() < P_SILL_FACE else None
        kind = _sill_faces[f]
        if kind is None or DETAIL_RNG.random() < P_SILL_MISS:
            continue
        band = _by_label.get(u["label"] + "_Band")
        mat = band["mats"][0] if band and band.get("mats") else BM + "MI_BackAlleys_Concrete"
        hi = 86.0 if u["s"] == 0 else 91.0                  # a ground window's grille comes 5 cm lower
        out_, thick = (6.0, 5.0) if kind == "slab" else (10.0, 9.0)
        w_s = 112.0 * u["sx"] + 12.0
        _wall_cube("Sill_" + u["label"], u, 112.0 * u["sx"] - w_s / 2, 112.0 * u["sx"] + w_s / 2, -3.0, out_, u["z"] + hi - thick, u["z"] + hi, DR_SILLS, mat)
        _cheap(CULL_MID)
        _count("sills")
    # Rebar.
    _rebar_ids = [k for k, b in sorted(BLOCKS.items()) if b["roof"] == "flat" or (b["roof"] == "terrace" and min(b["x1"] - b["x0"], b["y1"] - b["y0"]) >= 2.4)]
    for bid in _rebar_ids:
        b = BLOCKS[bid]
        corners = [(x_, y_) for x_ in (b["x0"] + 0.32, b["x1"] - 0.32) for y_ in (b["y0"] + 0.32, b["y1"] - 0.32)]
        DETAIL_RNG.shuffle(corners)
        floor_ = (b["storeys"] * b["sh"] if b["roof"] == "flat" else b["sh"]) + FLOOR_H - 5.0
        for j, (cx, cy) in enumerate(corners[:2]):
            out_x, out_y = -0.6 if cx < (b["x0"] + b["x1"]) / 2 else 0.6, -0.6 if cy < (b["y0"] + b["y1"]) / 2 else 0.6
            if DETAIL_RNG.random() > P_REBAR or cover_top(cx + out_x, cy, b) > floor_ or cover_top(cx, cy + out_y, b) > floor_:
                continue
            X_, Y_ = ue(cx, cy)
            if any(math.hypot(X_ - o[0], Y_ - o[1]) < 120.0 for o in _roof_things):
                continue
            label = "Rebar_%s_%d" % (bid, j)
            stub = DETAIL_RNG.uniform(115.0, 150.0) if b["roof"] == "terrace" else DETAIL_RNG.uniform(25.0, 70.0)
            put(label, CUBE, X_ - 11.0, Y_ - 11.0, floor_ - 4.0, 0, (0.22, 0.22, (stub + 4.0) / 100.0), folder=DR_REBAR, nocoll=True, mats=[BM + "MI_BackAlleys_Concrete"])
            _cheap(CULL_MID)
            for r_, (dx, dy) in enumerate(((-7.0, -7.0), (7.0, -7.0), (-7.0, 7.0), (7.0, 7.0))):
                if DETAIL_RNG.random() < 0.15:
                    continue                                # one's been cut
                hgt_ = DETAIL_RNG.uniform(25.0, 70.0) if b["roof"] == "terrace" else DETAIL_RNG.uniform(40.0, 105.0)
                base = (X_ + dx, Y_ + dy, floor_ + stub - 2.0)
                lean = (DETAIL_RNG.uniform(-5.0, 5.0), DETAIL_RNG.uniform(-5.0, 5.0))
                tip = (base[0] + lean[0], base[1] + lean[1], base[2] + hgt_)
                _rod("%s_Bar%d" % (label, r_), base, tip, 1.3, RUST_MAT, DR_REBAR, CULL_NEAR)
                if DETAIL_RNG.random() < 0.3:              # the top bent over
                    _rod("%s_Bar%d_Hook" % (label, r_), tip, (tip[0] + DETAIL_RNG.uniform(-13.0, 13.0), tip[1] + DETAIL_RNG.uniform(-13.0, 13.0), tip[2] + DETAIL_RNG.uniform(-5.0, 3.0)),
                         1.3, RUST_MAT, DR_REBAR, CULL_NEAR)
            _count("rebar stubs")
    # Peeling paint.
    _peel_by_face = {}
    for u in _wall_tiles:
        if (u["house"], u["letter"]) in _paint and u["kind"] != "SM_WallDoor_01" and (u["dress"] is None or "room" not in u["dress"]["has"]):
            _peel_by_face.setdefault((u["house"], u["letter"]), []).append(u)
    for f in sorted(_peel_by_face):
        ts = _peel_by_face[f]
        DETAIL_RNG.shuffle(ts)
        for u in ts[:_draw_peels()]:
            low = u["kind"] == "SM_Wall_Windows_01" or DETAIL_RNG.random() < 0.6
            w_p, h_p = DETAIL_RNG.uniform(70.0, 170.0), DETAIL_RNG.uniform(45.0, 62.0) if u["kind"] == "SM_Wall_Windows_01" else DETAIL_RNG.uniform(60.0, 150.0)
            s_ = DETAIL_RNG.uniform(w_p / 2 + 6.0, max(w_p / 2 + 6.0, u["w"] - w_p / 2 - 6.0))
            z_ = u["z"] + (DETAIL_RNG.uniform(14.0, 20.0) + h_p / 2 if low else DETAIL_RNG.uniform(120.0, 200.0))
            if w_p > u["w"] - 12.0 or not _free(_wbox(u, s_ - w_p / 2, s_ + w_p / 2, z_ - h_p / 2, z_ + h_p / 2), 2.0) or \
                    not _stair_clear(u, s_ - w_p / 2, s_ + w_p / 2, z_ - h_p / 2):
                continue
            nx, ny = NORMAL[u["side"]]
            x_, y_ = at(u["x"], u["y"], u["side"], s_, 2.0)
            put("Peel_" + u["label"], _draw_peel(), x_, y_, z_, math.degrees(math.atan2(-ny, -nx)), (0.03, h_p / 512.0, w_p / 512.0), folder=DR_PEEL,
                roll=DETAIL_RNG.choice((90.0, -90.0)), decal=True)
            _claim(_wbox(u, s_ - w_p / 2, s_ + w_p / 2, z_ - h_p / 2, z_ + h_p / 2, 3.0))
            _count("peels")

# Low wires. User 2026-11-05: "add more power lines, power lines are a big identity show for the philippines", with a photo of a Manila alley: bundles
# hanging low across it, slanting down over the walls. The spans above sit at the second floor, and from the ground, in three shots at the busiest
# spots, looking 22 degrees up, none was in frame. So a second layer: across the alley at the top of the ground floor, some climbing to the second
# floor opposite, and bundles slanting down a wall from a box up high to a box low down. Never under LOW_FLOOR, clear of awnings, signs and doors
# below it, and only over the gallery or its stairs if high enough to walk under. Its own random sequence, so nothing above moves.
STREET_LOW_WIRES = True
LOW_RNG = random.Random(223)
LOW_SPANS, LOW_DRAPES = 28, 16
LOW_FLOOR, DECK_CLEAR, P_LOW_CLIMB = 300.0, 620.0, 0.35
LOW_CULL = 5000.0                                      # thin and low: walls hide them long before this anyway
_draw_low = shuffle_bag(LOW_RNG, (2, 2, 3, 3, 3, 4, 5))
_low_mids = []
_n_low_house = {}
_soft_boxes = set()                                    # claimed, but a poster may go under them


def _over_deck(lx, ly):
    d = L["deck"]
    if d["x0"] - 0.3 < lx < d["x1"] + 0.3 and d["y0"] - 0.3 < ly < d["y1"] + 0.3:
        return True
    return any(g["x0"] - 0.3 < lx < g["x1"] + 0.3 and g["y0"] - 2.3 < ly < g["y1"] + 0.3 for g in L["stairs"])


def _low_path_clear(a3, b3, me, other):
    for k in range(1, 12):
        u_ = k / 12.0
        X_, Y_, Z_ = a3[0] + (b3[0] - a3[0]) * u_, a3[1] + (b3[1] - a3[1]) * u_, a3[2] + (b3[2] - a3[2]) * u_
        lx, ly = _lay(X_, Y_)
        if not (0 < lx < W and 0 < ly < H) or _in_room(X_, Y_) or not _clear_of_end_walls(lx, ly, 0.3) or (Z_ < DECK_CLEAR and _over_deck(lx, ly)):
            return False
        for o in BLOCKS.values():
            if o["x0"] < lx < o["x1"] and o["y0"] < ly < o["y1"]:
                if o is me or o is other or o["storeys"] * o["sh"] + FLOOR_H + {"terrace": 330.0, "metal": 260.0}.get(o["roof"], 70.0) > Z_:
                    return False
    return True


def _ground_band_z(b):
    return FLOOR_H + 300.0 + LOW_RNG.uniform(0.25, 0.75) * (b["sh"] - 300.0)


def _low_span(u, s_, z_a, n_a, label):
    side = u["side"]
    me = BLOCKS[u["bid"]]
    letter_o = OPP[side][0].upper()
    slopes = [-0.7, -0.45, -0.2, 0.0, 0.2, 0.45, 0.7]
    LOW_RNG.shuffle(slopes)
    for slope in slopes:
        hit, o = None, None
        for n_ in range(120, int(WIRE_GAP_MAX) + 10, 5):
            lx, ly = _lay(*at(u["x"], u["y"], side, s_ + slope * n_, float(n_)))
            if not (0 < lx < W and 0 < ly < H):
                break
            o = next((b_ for b_ in BLOCKS.values() if b_["x0"] < lx < b_["x1"] and b_["y0"] < ly < b_["y1"]), None)
            if o is not None:
                hit = float(n_)
                break
        if hit is None or o is me or not 200.0 <= hit <= WIRE_GAP_MAX:
            continue
        ho = _house_of(o["id"])
        if o["id"] in _thin_blocks or (ho, letter_o) in _hset:
            continue
        lx0, ly0 = _lay(*at(u["x"], u["y"], side, s_ + slope * (hit - 6.0), hit - 6.0))
        if side in ("east", "west"):
            if not o["y0"] + 0.25 < ly0 < o["y1"] - 0.25:
                continue
        elif not o["x0"] + 0.25 < lx0 < o["x1"] - 0.25:
            continue
        climb = o["storeys"] >= 2 and not o.get("balcony") and LOW_RNG.random() < P_LOW_CLIMB
        z_b = _band_z(o, 1) if climb else _ground_band_z(o)
        proud = (ho, letter_o) in _proud and o["storeys"] > (2 if climb else 1)
        n_b = hit - 10.0 - (BAND_OUT if proud else 0.0)
        X0, Y0 = at(u["x"], u["y"], side, s_, n_a)
        X1, Y1 = at(u["x"], u["y"], side, s_ + slope * n_b, n_b)
        a3, b3 = (X0, Y0, z_a), (X1, Y1, z_b)
        mid = ((X0 + X1) / 2, (Y0 + Y1) / 2)
        if not _low_path_clear(a3, b3, me, o) or any(math.hypot(mid[0] - m[0], mid[1] - m[1]) < 170.0 for m in _low_mids):
            continue
        box_b = (X1 - 34.0, Y1 - 34.0, z_b - 12.0, X1 + 34.0, Y1 + 34.0, z_b + 12.0)
        if not _free(box_b, 2.0):
            continue
        gap = math.hypot(X1 - X0, Y1 - Y0)
        segs = 3 if gap < 420.0 else 4
        rx, ry = RUN[side]
        lowest = min(z_a, z_b)
        for j in range(_draw_low()):
            wob = LOW_RNG.uniform(-26.0, 26.0) if j else 0.0
            wz = LOW_RNG.uniform(-6.0, 6.0) if j else 0.0
            a_ = (X0 + rx * wob, Y0 + ry * wob, z_a + wz)
            b_ = (X1 + rx * wob * LOW_RNG.uniform(0.4, 1.8), Y1 + ry * wob * LOW_RNG.uniform(0.4, 1.8), z_b + wz)
            sag = min(LOW_RNG.uniform(14.0, 34.0) * gap / 400.0, lowest - LOW_FLOOR - 8.0)
            _wire("%s_W%d" % (label, j), a_, b_, max(2.0, sag), segs, LOW_RNG.uniform(1.5, 2.3), LOW_CULL)
            _count("low wires")
        nx, ny = NORMAL[side]
        _box_on_wall(label + "_BoxB", X1 + nx * 10.0, Y1 + ny * 10.0, z_b, YAW[OPP[side]])
        _claim(box_b)
        _low_mids.append(mid)
        return True
    return False


if STREET_LOW_WIRES:
    _low_ts = [u for u in _wall_tiles if u["s"] == 0 and not _hollow_face(u) and u["w"] >= 90.0]
    LOW_RNG.shuffle(_low_ts)
    for u in _low_ts:
        if _street_n.get("low spans", 0) >= LOW_SPANS:
            break
        if _n_low_house.get(u["house"], 0) >= 2:
            continue
        s_ = LOW_RNG.uniform(22.0, u["w"] - 22.0)
        z_a = _ground_band_z(BLOCKS[u["bid"]])
        n_b0 = _band_out(u)
        if not _ground_open(u, s_, 70.0) or not _pipe_free(u, s_ - 14.0, s_ + 14.0) or not _free(_wbox(u, s_ - 16.0, s_ + 16.0, z_a - 12.0, z_a + 12.0), 2.0):
            continue
        if not _low_span(u, s_, z_a, n_b0 + 10.0, "LowSpan_" + u["label"]):
            continue
        Xb, Yb = at(u["x"], u["y"], u["side"], s_, n_b0)
        _box_on_wall("LowSpan_%s_Box" % u["label"], Xb, Yb, z_a, YAW[u["side"]])
        _claim(_wbox(u, s_ - 16.0, s_ + 16.0, z_a - 12.0, z_a + 12.0))
        _n_low_house[u["house"]] = _n_low_house.get(u["house"], 0) + 1
        _count("low spans")
    # Slanting down a wall, box to box: a bundle that came in high and goes to somebody's ground floor. Over a plain stretch, never across an opening.
    _drape_runs = [k for k in _run_tiles if _run_tiles[k][0]["s"] == 1 and BLOCKS[_run_tiles[k][0]["bid"]]["storeys"] >= 2 and
                   not BLOCKS[_run_tiles[k][0]["bid"]].get("balcony") and not _hollow_face(_run_tiles[k][0])]
    LOW_RNG.shuffle(_drape_runs)
    _drape_houses = set()

    def _drape_clear(t0, s_, z_, n_):
        b_ = BLOCKS[t0["bid"]]
        st = int((z_ - FLOOR_H) // b_["sh"])
        hit_ = _tile_above(t0, s_, st)
        if hit_ is None:
            return False
        u_, a_ = hit_
        if (u_["kind"] == "SM_WallDoor_01" or u_["label"] in _has_awn) and z_ < u_["z"] + 280.0 and 30.0 * u_["sx"] < a_ < 195.0 * u_["sx"]:
            return False                                # past a window is fine, as in the photo; not over a door or through an awning
        x_, y_ = at(t0["x"], t0["y"], t0["side"], s_, n_)
        if z_ < DECK_CLEAR and _over_deck(*_lay(x_, y_)):
            return False
        return _free((x_ - 8.0, y_ - 8.0, z_ - 8.0, x_ + 8.0, y_ + 8.0, z_ + 8.0), 2.0)

    for name in _drape_runs:
        if _street_n.get("drapes", 0) >= LOW_DRAPES:
            break
        ts = _run_tiles[name]
        t0 = ts[0]
        if t0["house"] in _drape_houses:
            continue
        total = ts[-1]["off"] - t0["off"] + ts[-1]["w"]
        if total < 260.0:
            continue
        b_ = BLOCKS[t0["bid"]]
        n_ = 17.0 if (t0["house"], t0["letter"]) in _proud else 9.5
        found = None
        for _try in range(8):
            len_ = LOW_RNG.uniform(200.0, min(total - 40.0, 520.0))
            s0 = LOW_RNG.uniform(20.0, total - len_ - 20.0)
            s_hi, s_lo = (s0, s0 + len_) if LOW_RNG.random() < 0.5 else (s0 + len_, s0)
            z_hi, z_lo = _band_z(b_, 1), _ground_band_z(b_)
            if _pipe_free(t0, s0 - 8.0, s0 + len_ + 8.0) and _stair_clear(t0, s0, s0 + len_, z_lo) and \
                    all(_ground_open(t0, s0 + len_ * k_ / 4.0, 40.0) for k_ in range(5)) and \
                    all(_drape_clear(t0, s_hi + (s_lo - s_hi) * k_ / 8.0, z_hi + (z_lo - z_hi) * k_ / 8.0, n_) for k_ in range(9)):
                found = (s_hi, s_lo, z_hi, z_lo)
                break
        if found is None:
            continue
        s_hi, s_lo, z_hi, z_lo = found
        label = "Drape_" + name
        for j in range(LOW_RNG.choice((2, 2, 3, 3, 4))):
            dz, dn = LOW_RNG.uniform(-7.0, 7.0) if j else 0.0, LOW_RNG.uniform(-1.5, 3.0) if j else 0.0
            a3 = tuple(at(t0["x"], t0["y"], t0["side"], s_hi + LOW_RNG.uniform(-5.0, 5.0), n_ + dn)) + (z_hi + dz,)
            b3 = tuple(at(t0["x"], t0["y"], t0["side"], s_lo + LOW_RNG.uniform(-5.0, 5.0), n_ + dn)) + (z_lo + dz,)
            _wire("%s_W%d" % (label, j), a3, b3, LOW_RNG.uniform(5.0, 16.0), 3, LOW_RNG.uniform(1.4, 2.0), LOW_CULL)
            _count("low wires")
        for e_, (s_, z_) in enumerate(((s_hi, z_hi), (s_lo, z_lo))):
            Xb, Yb = at(t0["x"], t0["y"], t0["side"], s_, max(n_ - 9.5, 0.0))
            _box_on_wall("%s_Box%d" % (label, e_), Xb, Yb, z_, YAW[t0["side"]])
        for k_ in range(9):
            x_, y_ = at(t0["x"], t0["y"], t0["side"], s_hi + (s_lo - s_hi) * k_ / 8.0, n_)
            z_ = z_hi + (z_lo - z_hi) * k_ / 8.0
            _claim((x_ - 10.0, y_ - 10.0, z_ - 10.0, x_ + 10.0, y_ + 10.0, z_ + 10.0))
            _soft_boxes.add(_occ[-1])
        _drape_houses.add(t0["house"])
        _count("drapes")
    assert not _wire_lows or min(_wire_lows) >= LOW_FLOOR, "a wire hangs at %.0f" % min(_wire_lows)     # above a head, whatever is on the wall


# The shop stalls. User 2026-11-06: "the wall if open". SM_Shop_A_001 is only a counter and an open bar frame, with the block's core 1.5 m behind it, so it read as a hole in the
# wall. Closed for the night: the kit's solid wall in the same module, just behind the frame, and a roll-up shutter down inside the frame to the counter. Frame X 0..300, Z 0..400;
# SM_RollupDoor_A_002 X -283.6..270.6, Z -333..0. A stall buried behind a house comes out of the plan at the end, so nothing else moves: B2_S0_1_1 stood 60 cm past B6h2's end wall, right on
# the next stall's frame. User 2026-11-06: "Shop A 001, overlapping surfaces with wall".
STALL_RNG = random.Random(229)
_stalls = [p for p in items if p["asset"].endswith("/SM_Shop_A_001")]
_buried_stalls = set()
for k_, p in enumerate(sorted(_stalls, key=lambda q_: q_["label"])):
    side = _yaw_side[round(p["rot"][1]) % 360]
    x0_, y0_, z_ = p["loc"]
    roll_ = STALL_RNG.choice(ROLL_MATS)
    lx_, ly_ = _lay(*at(x0_, y0_, side, 150.0, 60.0))
    if any(b_["x0"] < lx_ < b_["x1"] and b_["y0"] < ly_ < b_["y1"] for b_ in L["blocks"]):      # B2_S0_1_1, mostly behind B6h2
        _buried_stalls.add(p["label"])
        continue
    # Always behind the frame: the stall's frame and this wall share the planes local Y 0 and -20, and the first stall's wall sat exactly on them. User 2026-11-06: "Shop A 001, overlapping surfaces with wall".
    x_, y_ = at(x0_, y0_, side, 0.0, -1.3 * (k_ + 1))
    put(p["label"] + "_Back", AS + "SM_HouseWall_A_001", x_, y_, z_, YAW[side], (1, 1, 1), folder=DR_SHUTTERS)
    sa_ = 272.0 / 554.2
    x_, y_ = at(x0_, y0_, side, 150.0 + 6.5 * sa_, 3.0 + 1.3 * k_)
    put("Shutter_" + p["label"], AS + "SM_RollupDoor_A_002", x_, y_, z_ + 378.0, YAW[side], (sa_, 1.0, 290.0 / 333.1), folder=DR_SHUTTERS,
        mats=[roll_])
    _cheap(CULL_FAR)
    _count("closed stalls")


# Posters and ads. User 2026-11-05: "I can have gpt make product ads and movie posters, as well as election campaign posters", then "Added the Ads, btw, these
# ads are AI generated, they are currently placeholder labeled. I might decide to use them but we will see. Now see what you can do with it". So: 24 images
# in /Game/Project_Bopis_Posters, untouched, one switch, one folder, one material instance each (create_poster_materials_ue.py), easy to take out.
# The scale is from the user's photo ("look at this scale, use this for the poster"): a Manila wall with a man cycling past. Each sheet is about 61 x 91 cm, and they're
# pasted edge to edge in blocks, one candidate to a block, from just above the ground to over his head. So POSTER_AREA is that sheet's area, whatever an image's shape, and
# never smaller ("use your original size and make bigger variations"). Election posters fill walls, the same one over and over. Movie posters and ads go side by side, but
# never the same one twice: "only put together indentical posters for candidates type posters, you can put movie posters together side by side but not the same over and over,
# same goes for product ads".
# On the clear stretches of a whole wall, across tile joints, FACE_EDGE from its ends ("too close to the edge of the face"), never over a door or window. Hollow-block faces take
# them too, and nothing else ("Try to not have any first floor walls featureless, except hollow block, which yu can put posters on"). So do the shop row's plain stretches and
# the door end walls, which aren't wall tiles. A movie poster or ad only comes round again POSTER_GAP on, so two don't share a view; election posters may, as campaigns do.
STREET_POSTERS = True
DR_POSTERS = "BackAlleys/Posters"
POSTER_RNG = random.Random(227)
POSTER_GAP = 1000.0
POSTER_AREA = 61.0 * 91.0
POSTER_TALL, POSTER_LOW, POSTER_MID = (18.0, 294.0), (18.0, 240.0), (76.0, 234.0)   # floor to the trim, floor to under the highest vent blocks, and eye level
# Vent blocks stand at several heights, and most came down since those bands were set: their bottoms are 173 to 240 cm off the floor. User 2026-11-06, of a wall with vents
# and nothing under them: "even this is bare, it has vents but needs something". So two more bands: under one row of vents, and under two.
POSTER_UNDER, POSTER_SHORT = (18.0, 209.0), (60.0, 168.0)
P_POSTER_TALL, P_POSTER_MID, P_POSTER_SHUTTER, P_POSTER_GONE = 0.92, 0.75, 0.8, 0.07
POSTER_MOVIES = {"Ang_Tagapaslang": (592, 887), "Dugo_sa_Lansangan": (591, 887), "Hatinggabing_Takas": (512, 1024), "Huli_Ka_Kuya": (512, 1024),
                 "Huling_Biyahe_sa_Maynila": (887, 887), "May_Bukas_Pa_Kuya": (591, 887), "Sa_Huling_Sakay": (512, 1024), "Suntok_sa_Pier": (887, 887)}
POSTER_ADS = {"Bayani_Baterya": (724, 724), "Gising_Kape": (542, 724), "Kanto_Cola": (1024, 1536), "Presko_Mint": (724, 724), "Sabaw_Sarap": (544, 724),
              "Sinag_VCD": (544, 724), "TextKanto": (1024, 1536), "Tibay_Selyas": (724, 724), "Tulay_Sanglaan": (1024, 1536)}     # Puting_Araw: imported as a normal map, so it can't be used yet
POSTER_ELECTION = {"Arturo_Villareal": {"Arturo_Villareal_01": (768, 1024), "Arturo_Villareal_02": (887, 887)},
                   "Benjamin_Mercado": {"Benjamin_Mercado_01": (768, 1024), "Benjamin_Mercado_02": (887, 887)},
                   "Teresa_de_Vera": {"Teresa_de_Vera_01": (887, 887), "Teresa_de_Vera_02": (887, 887)}}
_poster_px = dict(POSTER_MOVIES)
_poster_px.update(POSTER_ADS)
for _d in POSTER_ELECTION.values():
    _poster_px.update(_d)
_draw_movie = shuffle_bag(POSTER_RNG, tuple(POSTER_MOVIES))
_draw_ad = shuffle_bag(POSTER_RNG, tuple(POSTER_ADS))
_draw_candidate = shuffle_bag(POSTER_RNG, tuple(POSTER_ELECTION))
_draw_tall = shuffle_bag(POSTER_RNG, ("election", "election", "election", "election", "election", "movie", "movie", "ad"))
_draw_mid = shuffle_bag(POSTER_RNG, ("movie", "ad", "ad", "ad", "election"))
_draw_big = shuffle_bag(POSTER_RNG, (1.0, 1.0, 1.0, 1.0, 1.15, 1.3))      # movie posters and ads; a block of election posters is one print run
_poster_at = {}
_poster_n = {"movie": 0, "ad": 0, "election": 0}
_poster_lots = [0]


def _far_enough(name, X_, Y_):
    return all(math.hypot(X_ - o[0], Y_ - o[1]) >= POSTER_GAP for o in _poster_at.get(name, ()))


def _pick_design(draw, X_, Y_, pool=(), exclude=()):
    unseen = sorted(k for k in pool if k not in _poster_at and k not in exclude)    # every design has its turn before any comes round again
    if unseen:
        return POSTER_RNG.choice(unseen)
    for _ in range(12):
        name = draw()
        if name not in exclude and _far_enough(name, X_, Y_):
            return name
    return None


def _side_by_side(first, draw, pool, X_, Y_, n):
    """A row of different movie posters or ads, as many of n as can be found: never the same one twice."""
    names = [first]
    while len(names) < n:
        other = _pick_design(draw, X_, Y_, pool, names)
        if other is None:
            break
        names.append(other)
    return names


def _sheet_w(name, k=1.0):
    """A sheet's width: the photo's area at this image's shape. A movie one-sheet is a little bigger."""
    w_, h_ = _poster_px[name]
    return math.sqrt(POSTER_AREA * (1.3 if name in POSTER_MOVIES else 1.0) * w_ / float(h_)) * k


def _paste(label, u, name, s_c, z_c, wid, n_, swing):
    """One sheet, centred s_c along tile u and z_c up. As the plywood sheets: X along the wall, local Y down, so the image reads right way round."""
    hgt = wid * _poster_px[name][1] / float(_poster_px[name][0])
    side = u["side"]
    run3 = (float(RUN[side][0]), float(RUN[side][1]), 0.0)
    out3 = (float(NORMAL[side][0]), float(NORMAL[side][1]), 0.0)
    tilt = POSTER_RNG.uniform(-swing, swing)
    X3, up3 = v_rot(run3, out3, tilt), v_rot((0.0, 0.0, 1.0), out3, tilt)
    x_, y_ = at(u["x"], u["y"], side, s_c, n_)
    put_axes(label, PLANE, X3, (-up3[0], -up3[1], -up3[2]), out3, (wid / 100.0, hgt / 100.0, 1.0), (0.0, 0.0, 0.0), (x_, y_, z_c),
             mats=[BM + "MI_BackAlleys_Poster_" + name])
    items[-1]["folder"] = DR_POSTERS
    items[-1]["draw"] = CULL_MID
    items[-1]["noshadow"] = True
    items[-1]["coll"] = "PosterPaper"       # ignored by everything but the Paper trace: shots hit the wall behind, and throw paper


def _block(t0, s0, s1, base, columns, rows, band, n0, k=1.0, own_size=False):
    """Sheets edge to edge: columns is the image of each column, rows how many high, as many columns as fit in s0..s1. Laps and misses by a centimetre, as pasted by hand,
    and here and there one has been torn off. Returns (sheets, the columns that went up, where they start and end)."""
    # A block has every column one height, so the rows line up and nothing shows between them, as in the photo. Images of another shape come out wider or narrower.
    # own_size: a row of different movie posters or ads, each its own full size, centred on one line. Sharing a height there made a tall image's sheet too narrow.
    first_ = columns[0]
    row_h = _sheet_w(first_, k) * _poster_px[first_][1] / float(_poster_px[first_][0])
    widths, kept = [], []
    for name in columns:
        w_ = _sheet_w(name, k) if own_size else row_h * _poster_px[name][0] / float(_poster_px[name][1])
        if sum(widths) + w_ > s1 - s0:
            break
        widths.append(w_)
        kept.append(name)
    if not kept:
        return 0, [], 0.0, 0.0
    tall_ = max(w_ * _poster_px[n_][1] / float(_poster_px[n_][0]) for w_, n_ in zip(widths, kept)) if own_size else row_h
    if tall_ > band[1] - band[0]:                       # a long sheet in a short band would run into the vents above it
        return 0, [], 0.0, 0.0
    _poster_lots[0] += 1
    lot = "Poster_%s_L%d" % (t0["label"], _poster_lots[0])
    total = sum(widths)
    start = s0 + POSTER_RNG.uniform(0.0, min(30.0, s1 - s0 - total))
    rows = max(1, min(rows, int((band[1] - band[0]) / tall_)))
    if rows == 1:
        bottom = max(band[0], min(band[1] - tall_, POSTER_RNG.uniform(148.0, 172.0) - tall_ / 2))
    else:
        bottom = band[0] + POSTER_RNG.uniform(0.0, max(0.0, band[1] - band[0] - rows * tall_) * 0.5)
    placed = 0
    s_ = start
    for c_, (name, w_) in enumerate(zip(kept, widths)):
        h_ = w_ * _poster_px[name][1] / float(_poster_px[name][0]) if own_size else row_h
        for r_ in range(rows):
            if rows * len(kept) >= 4 and POSTER_RNG.random() < P_POSTER_GONE:
                continue
            z_c = base + bottom + tall_ * (r_ + 0.5) if own_size else base + bottom + tall_ * r_ + h_ / 2
            _paste("%s_%d_%d" % (lot, c_, r_), t0, name, s_ + w_ / 2 + POSTER_RNG.uniform(-1.2, 1.2), z_c + POSTER_RNG.uniform(-1.2, 1.2), w_,
                   n0 + 0.15 * ((c_ + r_) % 2), 0.7 if rows * len(kept) > 1 else 1.4)
            placed += 1
        s_ += w_
    return placed, kept, start, start + total


def _poster_clear(box):
    return not any(o not in _soft_boxes and box[0] - 1.0 < o[3] and o[0] < box[3] + 1.0 and box[1] - 1.0 < o[4] and o[1] < box[4] + 1.0 and box[2] - 1.0 < o[5] and o[2] < box[5] + 1.0
                   for o in _occ)


def _poster_free(ts, a_, e_, band):
    """Nothing on a stretch of this wall between the band's heights, and somewhere to stand in front of it."""
    t0 = ts[0]
    mid = (a_ + e_) / 2
    u = next((q_ for q_ in ts if q_["off"] - t0["off"] <= mid < q_["off"] - t0["off"] + q_["w"]), None)
    if u is None:
        return False
    local = mid - (u["off"] - t0["off"])
    if u["kind"] in ("SM_Wall_Windows_01", "SM_WallDoor_01"):
        if 30.0 * u["sx"] - 5.0 < local < 195.0 * u["sx"] + 5.0:
            return False
    elif u["kind"] not in _plain_tile:
        return False
    if t0["s"] == 0:
        if not _ground_open(t0, mid, 60.0):
            return False
    else:
        lx, ly = _lay(*at(t0["x"], t0["y"], t0["side"], mid, 45.0))
        dk_ = L["deck"]
        if not (dk_["x0"] < lx < dk_["x1"] and dk_["y0"] < ly < dk_["y1"]):
            return False
    box = _wbox(t0, a_, e_, t0["z"] + band[0], t0["z"] + band[1], 10.0)
    return _pipe_free(t0, a_, e_) and _stair_clear(t0, a_, e_, t0["z"]) and _poster_clear(box)


def _stretches(ts, band):
    """The clear stretches of a whole wall, FACE_EDGE from its ends."""
    t0 = ts[0]
    total = ts[-1]["off"] - t0["off"] + ts[-1]["w"]
    out, cur, a_ = [], None, FACE_EDGE
    while a_ < total - FACE_EDGE:
        e_ = min(a_ + 8.0, total - FACE_EDGE)
        if _poster_free(ts, a_, e_, band):
            cur = a_ if cur is None else cur
        elif cur is not None:
            out.append((cur, a_))
            cur = None
        a_ = e_
    if cur is not None:
        out.append((cur, total - FACE_EDGE))
    return out


if STREET_POSTERS:
    _soft_boxes |= {_occ_of(p) for p in items if p["folder"] == DR_PATCH and p["asset"] == PLANE}
    # A room claims the whole height of its rectangle, to keep pipes and air conditioners off it, but the wall under it is still a wall that shows ("Try to not have any first
    # floor walls featureless"). So posters go under a room, and only the struts landing on the wall stop them.
    _soft_boxes |= {(o[0], o[1], 0.0, o[2], o[3], 3000.0) for o in _room_rects}
    _occ += [_wbox(t_, s_ - 8.0, s_ + 8.0, t_["z"] - 120.0, t_["z"], 30.0) for t_, s_ in _room_struts]
    _spots = []

    def _minus(a_, b_, taken):
        """a_..b_ with the stretches already taken cut out."""
        out, at_ = [], a_
        for c0, c1 in sorted(taken):
            if c1 <= at_ or c0 >= b_:
                continue
            if c0 > at_:
                out.append((at_, c0))
            at_ = max(at_, c1)
        if at_ < b_:
            out.append((at_, b_))
        return out

    for name in sorted(_run_tiles):
        ts = _run_tiles[name]
        t0 = ts[0]
        if not (t0["s"] == 0 or (t0["s"] == 1 and abs(t0["z"] - (400.0 + FLOOR_H)) < 1.0)):
            continue
        taken = []
        for how, band in (("tall", POSTER_TALL), ("low", POSTER_LOW), ("mid", POSTER_MID), ("under", POSTER_UNDER), ("short", POSTER_SHORT)):
            found = []
            for a_, b_ in _stretches(ts, band):
                for p_, q_ in _minus(a_, b_, taken):
                    if q_ - p_ >= 62.0:
                        _spots.append((how, ts, p_, q_))
                    found.append((p_, q_))
            taken += found

    def _extra_wall(label, x_, y_, z_, side, a_, b_):
        """A clear stretch of a wall that isn't made of wall tiles."""
        t = {"x": x_, "y": y_, "z": z_, "side": side, "label": label}
        if b_ - a_ >= 62.0 and _pipe_free(t, a_, b_) and _poster_clear(_wbox(t, a_, b_, z_ + POSTER_TALL[0], z_ + POSTER_TALL[1], 10.0)):
            _spots.append(("tall", [t], a_, b_))

    for p in items:
        if p["label"] == "B2_S0_2_1":       # the door frame module: its door is at 92-207, and the half wall carries on to 450, the wall's end
            _extra_wall(p["label"], p["loc"][0], p["loc"][1], p["loc"][2], "south", 4.0, 88.0)
            _extra_wall(p["label"], p["loc"][0], p["loc"][1], p["loc"][2], "south", 212.0, 450.0 - FACE_EDGE)
        elif p["label"] == "B2_S0_0_half":
            _extra_wall(p["label"], p["loc"][0], p["loc"][1], p["loc"][2], "south", 4.0, 110.0)
    for d in L["doors"]:                    # a door end wall: 450 across its alley, the door in the middle, 56 either side
        n_ = FACE[d["face"]]
        cx_, cy_ = ue(d["x"], d["y"])
        rx_, ry_ = RUN[n_]
        x0_, y0_ = cx_ - rx_ * 225.0, cy_ - ry_ * 225.0
        _extra_wall(d["id"] + "_S0_0", x0_, y0_, FLOOR_H, n_, FACE_EDGE, 165.0)
        _extra_wall(d["id"] + "_S0_2", x0_, y0_, FLOOR_H, n_, 285.0, 450.0 - FACE_EDGE)
    POSTER_RNG.shuffle(_spots)
    POSTER_BANDS = {"tall": POSTER_TALL, "low": POSTER_LOW, "mid": POSTER_MID, "under": POSTER_UNDER, "short": POSTER_SHORT}
    for how, ts, a_, b_ in _spots:
        # A long stretch takes several lots side by side, as in the photo, with a little wall between.
        while b_ - a_ >= 62.0:
            if POSTER_RNG.random() > (P_POSTER_TALL if how != "mid" else P_POSTER_MID):
                break
            t0 = ts[0]
            base = t0["z"]
            room_s = b_ - a_
            band = POSTER_BANDS[how]
            Xc, Yc = at(t0["x"], t0["y"], t0["side"], (a_ + b_) / 2, 2.0)
            if how != "mid" and room_s >= 190.0:
                kind = _draw_tall()                     # the long walls go mostly to the campaigns
            elif room_s >= 76.0 and any(k not in _poster_at for k in POSTER_MOVIES):
                kind = "movie"
            elif any(k not in _poster_at for k in POSTER_ADS):
                kind = "ad"
            else:
                kind = _draw_tall() if how != "mid" else _draw_mid()
            k_ = 1.0
            if kind == "movie":
                name = _pick_design(_draw_movie, Xc, Yc, POSTER_MOVIES)
                if name is None:
                    kind = "election"
                else:
                    k_ = _draw_big() if how != "short" else 1.0
                    columns = _side_by_side(name, _draw_movie, POSTER_MOVIES, Xc, Yc, POSTER_RNG.choice((1, 2, 2, 3)))
                    rows = 1
            elif kind == "ad":
                name = _pick_design(_draw_ad, Xc, Yc, POSTER_ADS)
                if name is None:
                    kind = "election"
                else:
                    k_ = _draw_big() if how != "short" else 1.0
                    columns = _side_by_side(name, _draw_ad, POSTER_ADS, Xc, Yc, POSTER_RNG.choice((1, 1, 2, 2, 3)))
                    rows = 1
            if kind == "election":
                cand = POSTER_ELECTION[_draw_candidate()]
                first, second = POSTER_RNG.sample(sorted(cand), 2)
                n_c = POSTER_RNG.choice((2, 3, 3, 4, 5, 6))
                # A block of one design, or two designs of one candidate in alternate columns, as in the photo.
                columns = [first] * n_c if POSTER_RNG.random() < 0.6 else [first if c_ % 2 == 0 else second for c_ in range(n_c)]
                rows = {"tall": 3, "low": 2, "mid": 1, "under": 2, "short": 1}[how]
            n_s, kept, s_a, s_b = _block(t0, a_, b_, base, columns, rows, band, POSTER_RNG.uniform(2.0, 2.3), k_, kind != "election")
            if not n_s and kind != "election":         # no room for what it drew: one election poster, the smallest sheet
                kind = "election"
                n_s, kept, s_a, s_b = _block(t0, a_, b_, base, [POSTER_RNG.choice(sorted(POSTER_ELECTION[_draw_candidate()]))], 1, band, POSTER_RNG.uniform(2.0, 2.3))
            if not n_s:
                break
            _poster_n[kind] += n_s
            for k in set(kept):
                _poster_at.setdefault(k, []).append((Xc, Yc))
            _claim(_wbox(t0, s_a, s_b, base + band[0], base + band[1], 3.0))
            a_ = s_b + POSTER_RNG.uniform(8.0, 70.0)
    # On closed shutters, kept to the shutter.
    for u, s0, wid in _shops:
        if POSTER_RNG.random() > P_POSTER_SHUTTER:
            continue
        kind = POSTER_RNG.choice(("movie", "ad", "election", "election"))
        Xc, Yc = at(u["x"], u["y"], u["side"], s0 + wid / 2, 8.0)
        if kind == "election":
            columns = [POSTER_RNG.choice(sorted(POSTER_ELECTION[_draw_candidate()]))] * 3
            rows = 3
        else:
            draw_ = _draw_movie if kind == "movie" else _draw_ad
            name = _pick_design(draw_, Xc, Yc)
            if name is None:
                continue
            columns = _side_by_side(name, draw_, (), Xc, Yc, 2)
            rows = 1
        s_a_, s_b_ = _inside_face(u, s0 + 3.0, s0 + wid - 3.0)
        first_ = len(items)
        n_s, kept, _sa, _sb = _block(u, s_a_, s_b_, u["z"], columns, rows, (8.0, 262.0), 9.2, 1.0, kind != "election")      # the shutter's face is 8.8 off the wall: at 8.5 they were hidden behind it, and still threw paper
        for p_ in items[first_:]:
            p_["vol"] = True        # no lightmap: the two in the level were baked while hidden, and their lightmaps came out in black patches
        if n_s:
            _poster_n[kind] += n_s
            for k in set(kept):
                _poster_at.setdefault(k, []).append((Xc, Yc))
    _count("posters", sum(_poster_n.values()))
    print("  posters", _poster_n, "in", _poster_lots[0], "lots, of", len(_spots), "stretches;", len(_poster_at), "designs used")

# Chained power lines. User 2026-11-06: "try to chain connect powerlines". Every span and run ended at a box of its own, so the lines read as separate hops. Now a line carries on from house
# to house: back across the alley further along, round an inside corner, along a wall, or down a wall to join the upper wires to the low ones. First it links the boxes already there. Then a chain's
# end grows towards the nearest other chain, with a new box on the wall it can reach, and links up when it can. A box takes two lines at most, three where a branch ties in, and nothing closes a loop, so these are chains, not stars.
# Whatever is still on its own then ties into a box part way along another chain, as a service line does. Last of the passes, so no other piece moves. Off with the switch; the pieces are Chain*_ in BackAlleys/Wires.
STREET_CHAIN_WIRES = True
CHAIN_RNG = random.Random(229)
CHAIN_LINKS, CHAIN_PASSES = 90, 6
CHAIN_MIN, CHAIN_ACROSS, CHAIN_ALONG = 180.0, 1000.0, 800.0     # cm: a link's length, across an alley or along a wall
CHAIN_DZ, CHAIN_ALONG_DZ = 220.0, 60.0                          # how much a link may climb, across and along
CHAIN_DROP_MIN, CHAIN_DROP_DZ = 40.0, 480.0                     # a drop down one wall, joining the upper wires to the low ones
CHAIN_FACING = 0.30                                             # a wall has to face the link: up to about 70 degrees off square
CHAIN_TURN = 15.0                                               # degrees between two lines leaving one box, or they read as one
CHAIN_MID_GAP = 40.0                                            # between the middles of any two links or spans
CHAIN_REACH = 2200.0                                            # how far a chain's end looks for another chain to grow towards
CHAIN_TARGETS, CHAIN_CLOSER = 5, 80.0                           # how many chains it looks at, and how much nearer a new box has to bring it
CHAIN_SLOPES = (0.2, -0.2, 0.4, -0.4, 0.6, -0.6, 0.85, -0.85, 1.1, -1.1, 1.4, -1.4)
_chain_n = {"links": 0, "wires": 0, "new boxes": 0}


def _chain_links():
    nodes = _wire_nodes
    n0 = len(nodes)
    root, deg, bundle, dirs = list(range(n0)), [0] * n0, [1] * n0, [[] for _ in nodes]
    cos_turn = math.cos(math.radians(CHAIN_TURN))
    mids = list(_span_mids) + list(_low_mids)

    def find(i):
        while root[i] != i:
            root[i] = root[root[i]]
            i = root[i]
        return i

    def prep(n_):
        """Where a wire leaves this box, as the spans do; its block; its wall tile."""
        nx, ny = NORMAL[n_["side"]]
        rx, ry = RUN[n_["side"]]
        n_["p"] = (n_["x"] + nx * 10.0, n_["y"] + ny * 10.0, n_["z"])
        lx, ly = _lay(n_["x"] - nx * 25.0, n_["y"] - ny * 25.0)
        n_["block"] = next((b_ for b_ in BLOCKS.values() if b_["x0"] < lx < b_["x1"] and b_["y0"] < ly < b_["y1"]), None)
        n_["tile"], n_["s"] = None, 0.0
        for u in _wall_tiles:
            a0 = (n_["x"] - u["x"]) * rx + (n_["y"] - u["y"]) * ry
            if u["side"] == n_["side"] and -1.0 <= a0 < u["w"] + 1.0 and abs((n_["x"] - u["x"]) * nx + (n_["y"] - u["y"]) * ny) < 40.0 and \
                    u["z"] <= n_["z"] < u["z"] + BLOCKS[u["bid"]]["sh"]:
                n_["tile"], n_["s"] = u, a0
                break

    for n_ in nodes:
        prep(n_)

    def gap(a_, b_):
        return math.hypot(a_["x"] - b_["x"], a_["y"] - b_["y"])

    def nearest(p3):
        best = min(range(n0), key=lambda i: math.dist(nodes[i]["p"], p3))
        return best if math.dist(nodes[best]["p"], p3) < 70.0 else None

    # The lines already there.
    groups = {}
    for label, a3, b3 in _wire_runs:
        groups.setdefault(label.rsplit("_W", 1)[0], []).append((a3, b3))
    for wires in groups.values():
        a_, b_ = nearest(wires[0][0]), nearest(wires[0][1])
        if a_ is None or b_ is None or a_ == b_:
            continue
        root[find(a_)] = find(b_)
        for i, j in ((a_, b_), (b_, a_)):
            deg[i] += 1
            bundle[i] = max(bundle[i], len(wires))
            d_ = gap(nodes[i], nodes[j])
            dirs[i].append(((nodes[j]["x"] - nodes[i]["x"]) / d_, (nodes[j]["y"] - nodes[i]["y"]) / d_))
    _chain_n["hops before"] = len(set(find(i) for i in range(n0)))

    def kind_of(a_, b_):
        """How these two boxes could join, and what it costs, or None."""
        na, nb = NORMAL[a_["side"]], NORMAL[b_["side"]]
        dx, dy = b_["p"][0] - a_["p"][0], b_["p"][1] - a_["p"][1]
        len_, dz = math.hypot(dx, dy), abs(b_["z"] - a_["z"])
        if a_["side"] == b_["side"] and abs(dx * na[0] + dy * na[1]) <= 40.0:
            if dz <= CHAIN_ALONG_DZ and CHAIN_MIN <= len_ <= CHAIN_ALONG:
                return "along", len_ * 1.15
            if CHAIN_ALONG_DZ < dz <= CHAIN_DROP_DZ and CHAIN_DROP_MIN <= len_ <= CHAIN_ALONG:
                return "drop", (len_ + dz) * 1.1
            return None
        if CHAIN_MIN <= len_ <= CHAIN_ACROSS and dz <= CHAIN_DZ and dx * na[0] + dy * na[1] >= CHAIN_FACING * len_ and -(dx * nb[0] + dy * nb[1]) >= CHAIN_FACING * len_:
            return "across", len_
        return None

    def stretch_ok(a_, b_):
        """Along a wall: nothing in the way, no pipe, not over a hollow-block face or the stairs' wall."""
        side = a_["side"]
        rx, ry = RUN[side]
        nx, ny = NORMAL[side]
        s_ = (b_["x"] - a_["x"]) * rx + (b_["y"] - a_["y"]) * ry
        lo, hi = min(0.0, s_), max(0.0, s_)
        t_ = {"x": a_["x"], "y": a_["y"], "side": side}
        if not _pipe_free(t_, lo - 6.0, hi + 6.0) or not _stair_clear(t_, lo, hi, min(a_["z"], b_["z"]) - 20.0):
            return False
        c0, c1 = at(a_["x"], a_["y"], side, lo + 30.0, -2.0), at(a_["x"], a_["y"], side, hi - 30.0, 25.0)
        if not _free((min(c0[0], c1[0]), min(c0[1], c1[1]), min(a_["z"], b_["z"]) - 8.0, max(c0[0], c1[0]), max(c0[1], c1[1]), max(a_["z"], b_["z"]) + 8.0), 0.0):
            return False
        for u in _wall_tiles:
            if u["side"] == side and abs((a_["x"] - u["x"]) * nx + (a_["y"] - u["y"]) * ny) < 40.0 and u["z"] <= a_["z"] < u["z"] + BLOCKS[u["bid"]]["sh"]:
                a0 = (a_["x"] - u["x"]) * rx + (a_["y"] - u["y"]) * ry
                if a0 + lo < u["w"] and a0 + hi > 0.0 and _hollow_face(u):
                    return False
        return True

    def drop_ends(a_, b_):
        """A drop down one wall, past windows but not doors or awnings, as the drapes do. Its two ends off the wall, or None if it won't go."""
        t_, t2 = a_["tile"], b_["tile"]
        if t_ is None or t2 is None or _hollow_face(t_) or _hollow_face(t2):
            return None
        s0, s1 = a_["s"], a_["s"] + (b_["x"] - a_["x"]) * RUN[t_["side"]][0] + (b_["y"] - a_["y"]) * RUN[t_["side"]][1]
        n_ = 17.0 if (t_["house"], t_["letter"]) in _proud or (t2["house"], t2["letter"]) in _proud else 10.0
        if not _pipe_free(t_, min(s0, s1) - 6.0, max(s0, s1) + 6.0) or not _stair_clear(t_, min(s0, s1), max(s0, s1), min(a_["z"], b_["z"])):
            return None
        for k in range(1, 8):
            s_, z_ = s0 + (s1 - s0) * k / 8.0, a_["z"] + (b_["z"] - a_["z"]) * k / 8.0
            if math.hypot(s_ - s0, z_ - a_["z"]) >= 34.0 and math.hypot(s_ - s1, z_ - b_["z"]) >= 34.0 and not _drape_clear(t_, s_, z_, n_):
                return None
        return tuple(at(t_["x"], t_["y"], t_["side"], s0, n_)) + (a_["z"],), tuple(at(t_["x"], t_["y"], t_["side"], s1, n_)) + (b_["z"],)

    def plan_link(a_, b_, kind, dirs_a, dirs_b):
        """The shape of a link, or None if something's in its way."""
        pa, pb = a_["p"], b_["p"]
        len_ = math.hypot(pb[0] - pa[0], pb[1] - pa[1])
        ux, uy = (pb[0] - pa[0]) / len_, (pb[1] - pa[1]) / len_
        if any(ux * d_[0] + uy * d_[1] > cos_turn for d_ in dirs_a) or any(-ux * d_[0] - uy * d_[1] > cos_turn for d_ in dirs_b):
            return None
        mid = ((pa[0] + pb[0]) / 2, (pa[1] + pb[1]) / 2)
        if kind != "drop" and any(math.hypot(mid[0] - m[0], mid[1] - m[1]) < CHAIN_MID_GAP for m in mids):
            return None
        if kind == "along" and not stretch_ok(a_, b_):
            return None
        if kind == "drop":
            ends = drop_ends(a_, b_)
            if ends is None:
                return None
            pa, pb = ends
        lowest = min(pa[2], pb[2])
        high = lowest >= WIRE_LOW + 20.0
        rate = {"along": CHAIN_RNG.uniform(2.0, 5.0) * len_ / 300.0, "drop": CHAIN_RNG.uniform(3.0, 10.0)}.get(kind, CHAIN_RNG.uniform(10.0, 24.0 if high else 34.0) * len_ / 400.0)
        sag = max(1.5, min(rate, lowest - (WIRE_LOW if high else LOW_FLOOR) - 14.0))
        segs = 3 if len_ < 420.0 else 4
        pts = [(pa[0] + (pb[0] - pa[0]) * k / segs, pa[1] + (pb[1] - pa[1]) * k / segs, pa[2] + (pb[2] - pa[2]) * k / segs - 4.0 * sag * (k / segs) * (1.0 - k / segs))
               for k in range(segs + 1)]
        me, other = (a_["block"], b_["block"]) if kind == "across" else (None, None)
        if not all(_low_path_clear(pts[k], pts[k + 1], me, other) for k in range(segs)):
            return None
        return pa, pb, sag, segs, high, mid, (ux, uy)

    def lay_link(i, j, kind, shape, most):
        pa, pb, sag, segs, high, mid, (ux, uy) = shape
        a_, b_ = nodes[i], nodes[j]
        label = "%s_%d" % ("Chain" if high else "ChainLow", _chain_n["links"])
        rax, ray = RUN[a_["side"]]
        rbx, rby = RUN[b_["side"]]
        for w_ in range(max(1, min(bundle[i], bundle[j], most))):
            wob = CHAIN_RNG.uniform(-9.0, 9.0) if w_ else 0.0
            wz = CHAIN_RNG.uniform(-4.0, 4.0) if w_ else 0.0
            a3 = (pa[0] + rax * wob, pa[1] + ray * wob, pa[2] + wz)
            b3 = (pb[0] + rbx * wob * CHAIN_RNG.uniform(0.5, 1.5), pb[1] + rby * wob * CHAIN_RNG.uniform(0.5, 1.5), pb[2] + wz)
            _wire("%s_W%d" % (label, w_), a3, b3, sag * CHAIN_RNG.uniform(0.85, 1.0), segs, CHAIN_RNG.uniform(1.5, 2.2), CULL_FAR if high else LOW_CULL)
            _chain_n["wires"] += 1
        root[find(i)] = find(j)
        deg[i] += 1
        deg[j] += 1
        dirs[i].append((ux, uy))
        dirs[j].append((-ux, -uy))
        if kind != "drop":
            mids.append(mid)
        _chain_n["links"] += 1
        _chain_n[kind] = _chain_n.get(kind, 0) + 1

    def link_up(only=None, branch=False):
        """Join chain ends that can reach each other, the shortest first, with some give so it isn't always the nearest. With branch, an end may tie into a box part way along another chain."""
        cands = []
        j_max = 3 if branch else 2
        for i in (range(len(nodes)) if only is None else (only,)):
            for j in range(len(nodes)):
                if (only is None and not branch and j <= i) or j == i or deg[i] >= 2 or deg[j] >= j_max or find(i) == find(j):
                    continue
                k_ = kind_of(nodes[i], nodes[j])
                if k_:
                    cands.append((k_[1] * CHAIN_RNG.uniform(0.8, 1.2), i, j, k_[0]))
        for _c, i, j, kind in sorted(cands):
            if _chain_n["links"] >= CHAIN_LINKS:
                return
            if deg[i] < 2 and deg[j] < j_max and find(i) != find(j):
                shape = plan_link(nodes[i], nodes[j], kind, dirs[i], dirs[j])
                if shape:
                    lay_link(i, j, kind, shape, 2 if kind == "drop" else 3)

    def clear_spot(X_, Y_, z_):
        return _free((X_ - 34.0, Y_ - 34.0, z_ - 12.0, X_ + 34.0, Y_ + 34.0, z_ + 12.0), 2.0) and all(math.hypot(X_ - o["x"], Y_ - o["y"]) >= 60.0 or abs(z_ - o["z"]) > 40.0 for o in nodes)

    why = {}

    def no(reason):
        why[reason] = why.get(reason, 0) + 1

    def grow(i):
        """Carry a chain's end on towards the nearest other chain, with a new box where it can reach: across the alley, or along its wall if it can't cross. The new box's index, or None."""
        a_ = nodes[i]
        ends = [j for j in range(len(nodes)) if j != i and deg[j] < 2 and find(j) != find(i)]
        if not ends:
            return None
        # The nearest few other chains: the very nearest is often just round a corner, with no way to it.
        targets = [nodes[j] for j in sorted(ends, key=lambda j: gap(a_, nodes[j]) + abs(nodes[j]["z"] - a_["z"]))[:CHAIN_TARGETS] if gap(a_, nodes[j]) <= CHAIN_REACH]
        if not targets:
            no("too far")
            return None

        def closer(c_):
            return max(gap(a_, t_) - gap(c_, t_) for t_ in targets)

        side = a_["side"]
        letter_o = OPP[side][0].upper()
        high = a_["z"] >= WIRE_LOW + 20.0
        best = None
        for slope in CHAIN_SLOPES:
            hit, o = None, None
            for n_ in range(150, int(CHAIN_ACROSS) + 5, 5):
                lx, ly = _lay(*at(a_["x"], a_["y"], side, slope * n_, float(n_)))
                if not (0 < lx < W and 0 < ly < H):
                    break
                o = next((b_ for b_ in BLOCKS.values() if b_["x0"] < lx < b_["x1"] and b_["y0"] < ly < b_["y1"]), None)
                if o is not None:
                    hit = float(n_)
                    break
            if hit is None or o is a_["block"]:
                no("no wall")
                continue
            ho = _house_of(o["id"])
            if o["id"] in _thin_blocks or (ho, letter_o) in _hset or (high and (o["storeys"] < 2 or o.get("balcony"))):
                no("wrong wall")
                continue
            lx0, ly0 = _lay(*at(a_["x"], a_["y"], side, slope * (hit - 6.0), hit - 6.0))
            if side in ("east", "west"):
                if not o["y0"] + 0.4 < ly0 < o["y1"] - 0.4:
                    no("wall edge")
                    continue
            elif not o["x0"] + 0.4 < lx0 < o["x1"] - 0.4:
                no("wall edge")
                continue
            z_b = _band_z(o, 1) if high else _ground_band_z(o)
            n_b = hit - (BAND_OUT if (ho, letter_o) in _proud and o["storeys"] > (2 if high else 1) else 0.0)
            X1, Y1 = at(a_["x"], a_["y"], side, slope * n_b, n_b)
            c = {"x": X1, "y": Y1, "z": z_b, "side": OPP[side]}
            prep(c)
            if closer(c) < CHAIN_CLOSER:
                no("no closer")
                continue
            if c["tile"] is None or c["block"] is not o:
                no("no tile")
                continue
            if not clear_spot(X1, Y1, z_b):
                no("spot taken")
                continue
            shape = plan_link(a_, c, "across", dirs[i], [])
            if not shape:
                no("link blocked")
            if shape and (best is None or closer(c) > best[0]):
                best = (closer(c), c, shape, "across")
        if best is None and a_["tile"] is not None:
            t0 = a_["tile"]
            ts = _run_tiles[t0["run"]]
            base = ts[0]
            total = ts[-1]["off"] + ts[-1]["w"] - base["off"]
            here = t0["off"] - base["off"] + a_["s"]
            rx, ry = RUN[side]
            for len_ in (620.0, -620.0, 500.0, -500.0, 380.0, -380.0, 260.0, -260.0):
                end_ = here + len_
                if end_ < 40.0 or end_ > total - 40.0:
                    continue
                X1, Y1 = at(base["x"], base["y"], side, end_, _band_out(t0))
                c = {"x": X1, "y": Y1, "z": a_["z"] + CHAIN_RNG.uniform(-8.0, 8.0), "side": side}
                prep(c)
                if closer(c) < CHAIN_CLOSER or c["tile"] is None or not clear_spot(X1, Y1, c["z"]):
                    continue
                shape = plan_link(a_, c, "along", dirs[i], [])
                if shape:
                    best = (closer(c), c, shape, "along")
                    break
        if best is None:
            return None
        _d, c, shape, kind = best
        _box_on_wall("ChainBox_%s_%d" % (c["tile"]["label"], _chain_n["new boxes"]), c["x"], c["y"], c["z"], YAW[c["side"]])
        new = len(nodes) - 1
        nodes[new].update(p=c["p"], block=c["block"], tile=c["tile"], s=c["s"])
        root.append(new)
        deg.append(0)
        bundle.append(bundle[i])
        dirs.append([])
        lay_link(i, new, kind, shape, 2)
        _chain_n["new boxes"] += 1
        return new

    link_up()
    for _pass in range(CHAIN_PASSES):
        ends = [i for i in range(len(nodes)) if deg[i] < 2]
        CHAIN_RNG.shuffle(ends)
        for i in ends:
            if _chain_n["links"] >= CHAIN_LINKS or deg[i] >= 2:
                continue
            new = grow(i)
            if new is not None:
                link_up(new)
    # What's still on its own ties into the nearest chain, as a service line does.
    link_up(branch=True)
    sizes = {}
    for i in range(len(nodes)):
        sizes[find(i)] = sizes.get(find(i), 0) + 1
    _chain_n["chains"] = len(sizes)
    _chain_n["boxes in chains"] = sorted(sizes.values(), reverse=True)[:12]
    _chain_n["ends left"] = sum(1 for k in deg if k < 2)
    _chain_n["boxes"] = len(nodes)
    _chain_n["grow"] = why


if STREET_WIRES and STREET_LOW_WIRES and STREET_CHAIN_WIRES:
    _chain_links()
    assert min(_wire_lows) >= LOW_FLOOR, "a chain wire hangs at %.0f" % min(_wire_lows)
    print("chains:", _chain_n)

# Power poles, roof tyres and water meters. User 2026-11-06: "do the building centric ones first". The last pass, each kind with its own random sequence, so that nothing
# above moves. Shapes: analysis/pole_shape_ue.py and pole_profile_ue.py.
STREET_POLES, STREET_TYRES, STREET_WATER_METERS = True, True, True
DR_POLES, DR_TYRES, DR_WATER = "BackAlleys/Poles", "BackAlleys/Tyres", "BackAlleys/WaterMeters"
MEAST = ME + "MiddleEast/"
WATER_MESH = "/Game/Philippines_Markets/Props/Water_Meters_Set_01/SM_Water_Meter_Single_0%d"


def _rot_axes(rot):
    """FRotationMatrix's local axes, from [pitch, yaw, roll]."""
    pi, ya, ro = (math.radians(a) for a in rot)
    cp, sp, cy, sy, cr, sr = math.cos(pi), math.sin(pi), math.cos(ya), math.sin(ya), math.cos(ro), math.sin(ro)
    return ((cp * cy, cp * sy, sp), (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp), (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp))


def _rod_line(p):
    """A thin SM_Cube's two ends: its pivot is a corner, and its length is along local X."""
    X, Y, Z = _rot_axes(p["rot"])
    sx, sy, sz = (s_ * 100.0 for s_ in p["scale"])
    c_ = tuple(p["loc"][i] + X[i] * sx / 2 + Y[i] * sy / 2 + Z[i] * sz / 2 for i in range(3))
    return tuple(c_[i] - X[i] * sx / 2 for i in range(3)), tuple(c_[i] + X[i] * sx / 2 for i in range(3))


def _seg2(a, b, c, d):
    """How close two segments come, on the ground plan."""
    def pt(p_, q0, q1):
        vx, vy = q1[0] - q0[0], q1[1] - q0[1]
        k_ = max(0.0, min(1.0, ((p_[0] - q0[0]) * vx + (p_[1] - q0[1]) * vy) / max(vx * vx + vy * vy, 1e-6)))
        return math.hypot(p_[0] - q0[0] - vx * k_, p_[1] - q0[1] - vy * k_)

    def side_(p_, q0, q1):
        return (q1[0] - q0[0]) * (p_[1] - q0[1]) - (q1[1] - q0[1]) * (p_[0] - q0[0])
    if side_(a, c, d) * side_(b, c, d) < 0.0 and side_(c, a, b) * side_(d, a, b) < 0.0:
        return 0.0
    return min(pt(a, c, d), pt(b, c, d), pt(c, a, b), pt(d, a, b))


# Power poles. "Power lines are a big identity show for the philippines", and until now there wasn't one pole: every wire ran wall to wall. They stand clear of the wall, at the
# side of a lane wide enough to keep walking room. Own measures, from their vertices: n: how far off the wall; low: x0, x1, y0, y1, z0, z1 of the lower arms or transformers;
# head: the same of the top crossarm; tops: where the insulators are. With local X along the wall, +Y points out into the lane, or in if the pole is turned round. Pole 02's
# transformers hang off its -Y, so it's always turned round, to hang them over the lane.
POLE_RNG = random.Random(251)
POLE_ORDER = ("02", "04", "01", "03", "04", "02", "01")
POLE_GAP, POLE_LINK_MIN, POLE_LINK_MAX = 1100.0, 700.0, 2800.0
POLE_LANE, POLE_DOOR, POLE_KEEP, POLE_SERVICE = 380.0, 135.0, 220.0, 4
POLE_KINDS = {
    "01": {"n": 66.0, "low": (-48.0, 48.0, -48.0, 48.0, 440.0, 740.0), "head": (-40.0, 292.0, -24.0, 14.0, 840.0, 975.0),
           "tops": ((199.0, -9.5, 968.0), (270.0, -9.0, 912.0), (-30.0, -9.0, 880.0))},
    "02": {"n": 42.0, "low": (-122.0, 124.0, -72.0, 13.0, 600.0, 760.0), "head": (-162.0, 165.0, -25.0, 13.0, 760.0, 925.0), "turned": True,
           "tops": ((-130.0, -12.0, 915.0), (70.0, -12.0, 915.0), (125.0, -12.0, 915.0))},
    "03": {"n": 34.0, "low": (-13.0, 35.0, -13.0, 13.0, 0.0, 245.0), "head": (-13.0, 13.0, -13.0, 13.0, 880.0, 955.0),
           "tops": ((0.0, 0.0, 890.0), (0.0, 0.0, 865.0))},
    "04": {"n": 66.0, "low": (-48.0, 48.0, -48.0, 48.0, 600.0, 780.0), "head": (-110.0, 108.0, -23.0, 11.0, 800.0, 900.0),
           "tops": ((-95.0, -13.0, 903.0), (70.0, -13.0, 903.0), (-95.0, -13.0, 848.0))},
}
_pole_n = {"poles": 0, "lines": 0, "line wires": 0, "drops": 0, "drop wires": 0, "boxes": 0}
_poles = []

if STREET_POLES and STREET_WIRES and STREET_LOW_WIRES and STREET_CHAIN_WIRES:
    # Awnings reach out from the wall, and nothing else lists them.
    for p in items:
        if p["folder"] == "BackAlleys/Awnings" and "SM_MetalPlate" in p["asset"]:
            X_a, _y, Z_a = _rot_axes(p["rot"])
            hw_, len_ = 81.0 * abs(p["scale"][0]), 164.9 * abs(p["scale"][2])
            pts_ = [(p["loc"][0] + X_a[0] * k_ - Z_a[0] * m_, p["loc"][1] + X_a[1] * k_ - Z_a[1] * m_, p["loc"][2] - Z_a[2] * m_) for k_ in (-hw_, hw_) for m_ in (0.0, len_)]
            _claim((min(q_[0] for q_ in pts_), min(q_[1] for q_ in pts_), min(q_[2] for q_ in pts_), max(q_[0] for q_ in pts_), max(q_[1] for q_ in pts_), max(q_[2] for q_ in pts_)))
    _pole_rods = [_rod_line(p) for p in items if p["folder"] in (DR_WIRES, DR_LAUNDRY) and p["asset"] == CUBE]
    _pole_keep = [(s_["loc"][0], s_["loc"][1]) for s_ in gameplay["spawns"]] + [(w_["loc"][0], w_["loc"][1]) for w_ in gameplay["wander"]] + [tuple(gameplay["player_start"][:2])] + \
        [tuple(ue(k_["x"], k_["y"])) for k_ in L["pickups"] if not k_.get("z")]
    _start_xy = tuple(gameplay["player_start"][:2])

    def _pole_rect(x_, y_, side, turned, r_):
        """The four corners and the middles of a pole's rectangle (x0, x1, y0, y1), on the ground plan."""
        sgn = -1.0 if turned else 1.0
        rx, ry = RUN[side]
        nx, ny = NORMAL[side]
        return [(x_ + sgn * (rx * a_ + nx * b_), y_ + sgn * (ry * a_ + ny * b_)) for a_ in (r_[0], (r_[0] + r_[1]) / 2, r_[1]) for b_ in (r_[2], r_[3])]

    def _in_lane(pts, z_):
        for X_, Y_ in pts:
            lx, ly = _lay(X_, Y_)
            if not (0 < lx < W and 0 < ly < H):
                return False
            for o in BLOCKS.values():
                if o["x0"] - 0.1 < lx < o["x1"] + 0.1 and o["y0"] - 0.1 < ly < o["y1"] + 0.1 and \
                        o["storeys"] * o["sh"] + FLOOR_H + {"terrace": 330.0, "metal": 120.0}.get(o["roof"], 70.0) > z_:
                    return False
        return True

    def _pole_fit(u, s_, kind, turned):
        k_ = POLE_KINDS[kind]
        side, n_ = u["side"], k_["n"]
        x_, y_ = at(u["x"], u["y"], side, s_, n_)
        lx, ly = _lay(x_, y_)
        if not (0 < lx < W and 0 < ly < H) or cover_top(lx, ly) > 0 or not _clear_of_end_walls(lx, ly, 1.5) or _over_deck(lx, ly):
            return False
        if any(g["x0"] - 0.6 < lx < g["x1"] + 0.6 and g["y0"] - g.get("clear_ahead_m", 2.3) < ly < g["y1"] + 0.6 for g in L["stairs"]):
            return False
        if any(c_["x0"] - 0.6 < lx < c_["x1"] + 0.6 and c_["y0"] - 0.6 < ly < c_["y1"] + 0.6 for c_ in L["cover"]):
            return False
        if any(math.hypot(x_ - o[0], y_ - o[1]) < POLE_KEEP for o in _pole_keep):
            return False
        a_ = u["off"] + s_
        if any(t_["kind"] == "SM_WallDoor_01" and abs(t_["off"] + 111.0 * t_["sx"] - a_) < POLE_DOOR for t_ in _run_tiles[u["run"]]):
            return False
        # Walking room: the width of the lane across from here.
        for m_ in range(40, 1200, 10):
            lx2, ly2 = _lay(*at(u["x"], u["y"], side, s_, float(m_)))
            if not (0 < lx2 < W and 0 < ly2 < H) or cover_top(lx2, ly2) > 0 or not _clear_of_end_walls(lx2, ly2, 0.1):
                if m_ < POLE_LANE:
                    return False
                break
        low, head = k_["low"], k_["head"]
        pts_l, pts_h = _pole_rect(x_, y_, side, turned, low), _pole_rect(x_, y_, side, turned, head)
        if not _in_lane(pts_l, max(low[4], 300.0)) or not _in_lane(pts_h, head[4]) or any(_over_deck(*_lay(*q_)) for q_ in pts_l) and low[4] < 520.0:
            return False
        shaft = (x_ - 14.0, y_ - 14.0, 0.0, x_ + 14.0, y_ + 14.0, 980.0)
        low_box = (min(q_[0] for q_ in pts_l), min(q_[1] for q_ in pts_l), low[4], max(q_[0] for q_ in pts_l), max(q_[1] for q_ in pts_l), low[5])
        head_box = (min(q_[0] for q_ in pts_h), min(q_[1] for q_ in pts_h), head[4], max(q_[0] for q_ in pts_h), max(q_[1] for q_ in pts_h), head[5])
        if not _free(shaft, 3.0) or not _free(low_box, 3.0) or not _free(head_box, 3.0):
            return False
        arm0, arm1 = (min(q_[0] for q_ in pts_h), min(q_[1] for q_ in pts_h)), (max(q_[0] for q_ in pts_h), max(q_[1] for q_ in pts_h))
        for r0, r1 in _pole_rods:
            near = abs(r0[0] - x_) < 400.0 and abs(r0[1] - y_) < 400.0 or abs(r1[0] - x_) < 400.0 and abs(r1[1] - y_) < 400.0
            if near and _seg2((x_, y_), (x_, y_), r0, r1) < 18.0:
                return False
            if near and max(r0[2], r1[2]) > head[4] - 10.0 and _seg2(arm0, arm1, r0, r1) < 14.0:
                return False
        return True

    def _lane_view(u, s_, n_):
        """How far you can see along the lane from here: a pole at the end of a long view is worth more than one in a corner."""
        seen = 0.0
        for sgn in (-1.0, 1.0):
            for d_ in range(50, 2550, 50):
                lx, ly = _lay(*at(u["x"], u["y"], u["side"], s_ + sgn * d_, n_))
                if not (0 < lx < W and 0 < ly < H) or cover_top(lx, ly) > 0:
                    break
                seen += 50.0
        return seen

    def _pole_points(c_):
        return tuple(tuple(c_["base"][i] + c_["X"][i] * l_[0] + c_["Y"][i] * l_[1] + c_["Z"][i] * l_[2] for i in range(3)) for l_ in POLE_KINDS[c_["kind"]]["tops"])

    def _pole_can_link(a_, b_):
        d_ = math.hypot(a_["x"] - b_["x"], a_["y"] - b_["y"])
        return POLE_LINK_MIN <= d_ <= POLE_LINK_MAX and _path_clear((a_["x"], a_["y"], 880.0), (b_["x"], b_["y"], 880.0), None, None)

    _ground_ts = [u for u in _wall_tiles if u["s"] == 0]
    _pole_cands = {}
    for kind_ in POLE_KINDS:
        out_ = []
        for u in _ground_ts:
            s_ = 30.0
            while s_ < u["w"] - 20.0:
                for turned_ in ((True,) if POLE_KINDS[kind_].get("turned") else (False, True)):
                    if _pole_fit(u, s_, kind_, turned_):
                        x_, y_ = at(u["x"], u["y"], u["side"], s_, POLE_KINDS[kind_]["n"])
                        out_.append({"u": u, "s": s_, "kind": kind_, "turned": turned_, "x": x_, "y": y_, "view": _lane_view(u, s_, POLE_KINDS[kind_]["n"])})
                s_ += 55.0
        _pole_cands[kind_] = out_
    print("pole spots:", {k_: len(v_) for k_, v_ in sorted(_pole_cands.items())})

    for kind_ in POLE_ORDER:
        cands = [c_ for c_ in _pole_cands[kind_] if all(math.hypot(c_["x"] - o["x"], c_["y"] - o["y"]) >= POLE_GAP for o in _poles)]
        if not cands:
            continue
        if not _poles:
            # The first stands where the player sees it from the start.
            def _seen_from_start(c_):
                d_ = math.hypot(c_["x"] - _start_xy[0], c_["y"] - _start_xy[1])
                return 450.0 <= d_ <= 1800.0 and all(cover_top(*_lay(_start_xy[0] + (c_["x"] - _start_xy[0]) * k_ / 24.0, _start_xy[1] + (c_["y"] - _start_xy[1]) * k_ / 24.0)) <= 0 for k_ in range(1, 24))
            near_ = [c_ for c_ in cands if _seen_from_start(c_)]
            cands = near_ or cands
        best = max(cands, key=lambda c_: c_["view"] * POLE_RNG.uniform(0.6, 1.4) + (1500.0 if any(_pole_can_link(c_, o) for o in _poles) else 0.0))
        _poles.append(best)

    for i, c_ in enumerate(_poles):
        u, k_ = c_["u"], POLE_KINDS[c_["kind"]]
        side = u["side"]
        rx, ry = RUN[side]
        sgn = -1.0 if c_["turned"] else 1.0
        lean, dir_ = math.radians(POLE_RNG.uniform(0.0, 1.3)), math.radians(POLE_RNG.uniform(0.0, 360.0))
        Z_p = (math.sin(lean) * math.cos(dir_), math.sin(lean) * math.sin(dir_), math.cos(lean))
        X_p = (sgn * rx, sgn * ry, 0.0)
        dot_ = v_dot(X_p, Z_p)
        X_p = (X_p[0] - Z_p[0] * dot_, X_p[1] - Z_p[1] * dot_, X_p[2] - Z_p[2] * dot_)
        len_ = math.sqrt(v_dot(X_p, X_p))
        X_p = (X_p[0] / len_, X_p[1] / len_, X_p[2] / len_)
        Y_p = v_cross(Z_p, X_p)
        c_.update(base=(c_["x"], c_["y"], -2.0), X=X_p, Y=Y_p, Z=Z_p)
        put("Pole_%d" % i, MEAST + "SM_Electric_Pole_" + c_["kind"], c_["x"], c_["y"], -2.0, 0.0, (1, 1, 1), folder=DR_POLES)
        items[-1]["rot"] = axes_rot(X_p, Y_p, Z_p)
        items[-1]["phys"] = PHYS + "Concrete"
        _cheap(CULL_FAR)
        _claim((c_["x"] - 14.0, c_["y"] - 14.0, 0.0, c_["x"] + 14.0, c_["y"] + 14.0, 980.0))
        _pole_n["poles"] += 1

    # Pole to pole, crossarm to crossarm: the primary line, a shortest tree of it. The lines keep to their sides, so they don't cross on the way.
    _root = list(range(len(_poles)))

    def _pole_find(i):
        while _root[i] != i:
            _root[i] = _root[_root[i]]
            i = _root[i]
        return i

    _pairs = sorted((math.hypot(a_["x"] - b_["x"], a_["y"] - b_["y"]), i, j) for i, a_ in enumerate(_poles) for j, b_ in enumerate(_poles) if i < j)
    for d_, i, j in _pairs:
        if _pole_find(i) == _pole_find(j) or not _pole_can_link(_poles[i], _poles[j]):
            continue
        a_, b_ = _poles[i], _poles[j]
        ux, uy = (b_["x"] - a_["x"]) / d_, (b_["y"] - a_["y"]) / d_
        pa_, pb_ = sorted(_pole_points(a_), key=lambda q_: -uy * q_[0] + ux * q_[1]), sorted(_pole_points(b_), key=lambda q_: -uy * q_[0] + ux * q_[1])
        n_w = min(len(pa_), len(pb_))
        if not all(_path_clear(pa_[w_], pb_[w_], None, None) for w_ in range(n_w)):
            continue
        segs = max(4, int(d_ / 340.0))
        sag = POLE_RNG.uniform(22.0, 42.0) * d_ / 1000.0
        for w_ in range(n_w):
            _wire("PoleLine_%d_%d_W%d" % (i, j, w_), pa_[w_], pb_[w_], sag * POLE_RNG.uniform(0.92, 1.0), segs, 2.2)
            _pole_n["line wires"] += 1
        _root[_pole_find(i)] = _pole_find(j)
        _pole_n["lines"] += 1

    # From the pole down to the boxes on the houses round it: the bundles that make the tangle. A box takes one, and has to face the pole.
    _taken = set()
    for i, c_ in enumerate(_poles):
        cands = []
        for n_i, n_ in enumerate(_wire_nodes):
            if n_i in _taken or "p" not in n_:
                continue
            dx, dy = c_["x"] - n_["p"][0], c_["y"] - n_["p"][1]
            len_ = math.hypot(dx, dy)
            nx, ny = NORMAL[n_["side"]]
            if 250.0 <= len_ <= 1150.0 and dx * nx + dy * ny >= 0.3 * len_:
                cands.append((len_ * POLE_RNG.uniform(0.75, 1.25), n_i))
        cands.sort()
        made, low_made = 0, 0
        for _c, n_i in cands:
            if made >= POLE_SERVICE:
                break
            n_ = _wire_nodes[n_i]
            low_ = n_["z"] < WIRE_LOW
            if low_ and low_made >= 2:
                continue
            z_s = min(POLE_RNG.uniform(n_["z"] + 50.0, n_["z"] + 240.0), 800.0)
            z_s = max(z_s, 440.0)
            if abs(z_s - n_["z"]) > 330.0:
                continue
            a3 = tuple(c_["base"][m_] + c_["Z"][m_] * z_s for m_ in range(3))
            b3 = n_["p"]
            len_ = math.hypot(a3[0] - b3[0], a3[1] - b3[1])
            lowest = min(a3[2], b3[2])
            floor_ = WIRE_LOW if lowest >= WIRE_LOW + 20.0 else LOW_FLOOR
            sag = max(1.5, min(POLE_RNG.uniform(8.0, 22.0) * len_ / 400.0, lowest - floor_ - 14.0))
            segs = 3 if len_ < 500.0 else 4
            pts_ = [(a3[0] + (b3[0] - a3[0]) * k_ / segs, a3[1] + (b3[1] - a3[1]) * k_ / segs, a3[2] + (b3[2] - a3[2]) * k_ / segs - 4.0 * sag * (k_ / segs) * (1.0 - k_ / segs)) for k_ in range(segs + 1)]
            if not all(_low_path_clear(pts_[k_], pts_[k_ + 1], None, None) for k_ in range(segs)):
                continue
            label = "%s_%d_%d" % ("PoleDrop" if floor_ == WIRE_LOW else "PoleDropLow", i, made)
            rx, ry = RUN[n_["side"]]
            for w_ in range(POLE_RNG.choice((2, 2, 3))):
                wob = POLE_RNG.uniform(-7.0, 7.0) if w_ else 0.0
                wz = POLE_RNG.uniform(-4.0, 4.0) if w_ else 0.0
                _wire("%s_W%d" % (label, w_), (a3[0], a3[1], a3[2] + wz), (b3[0] + rx * wob, b3[1] + ry * wob, b3[2] + wz), sag * POLE_RNG.uniform(0.85, 1.0), segs, POLE_RNG.uniform(1.5, 2.2),
                      CULL_FAR if floor_ == WIRE_LOW else LOW_CULL)
                _pole_n["drop wires"] += 1
            _taken.add(n_i)
            made += 1
            low_made += 1 if low_ else 0
            _pole_n["drops"] += 1
            if made <= 2:
                # A junction box strapped to the pole, where the bundle leaves it.
                k_ = POLE_RNG.uniform(0.8, 1.0)
                nx, ny = NORMAL[c_["u"]["side"]]
                put("PoleBox_%d_%d" % (i, made), AS + "SM_ElectricBox_C_002", a3[0] + nx * 11.0, a3[1] + ny * 11.0, a3[2] - 4.8 * k_, YAW[c_["u"]["side"]], (k_, k_, k_), folder=DR_POLES, nocoll=True)
                _cheap(CULL_MID, 1, True)
                _pole_n["boxes"] += 1
    assert min(_wire_lows) >= LOW_FLOOR, "a pole's wire hangs at %.0f" % min(_wire_lows)
    print("poles:", _pole_n, [(c_["kind"], c_["u"]["label"], round(c_["view"])) for c_ in _poles])

# Tyres on the roofs: what holds a corrugated sheet down in the user's shanty photo. A truck tyre at 95 cm in the pack, so scaled to a car's. Lying flat on a sheet, away from its
# laps and from what stands on the roof. All the one-storey roofs, which the gallery looks down on, and a third of the rest. Now and then one on another. No collision.
TYRE_RNG = random.Random(257)
TYRES_WANTED, P_TYRE_ROOF, P_TYRE_STACK = 30, 0.35, 0.18
TYRE_R, TYRE_HALF = 47.8, 15.4
_tyre_n = {"tyres": 0, "roofs": 0, "stacks": 0}
if STREET_TYRES:
    _sheets = {}
    for p in items:
        if p["folder"] == RF and p["label"].startswith("Roof_") and "SM_MetalPlate_A" in p["asset"]:
            bid = p["label"].split("_")[1]
            if bid in BLOCKS:
                _sheets.setdefault(bid, []).append(p)
    _on_roofs = [(p["loc"][0], p["loc"][1]) for p in items if p["folder"] in (DR_TANKS, DR_AERIALS, DR_REBAR)]
    _roof_ids = sorted(_sheets, key=lambda k_: (BLOCKS[k_]["storeys"] > 1, TYRE_RNG.random()))
    _draw_tyres = shuffle_bag(TYRE_RNG, (1, 1, 2, 2, 2, 3, 3, 4))
    for bid in _roof_ids:
        if _tyre_n["tyres"] >= TYRES_WANTED:
            break
        if BLOCKS[bid]["storeys"] > 1 and TYRE_RNG.random() > P_TYRE_ROOF:
            continue
        want_, here_ = _draw_tyres(), []
        for _try in range(want_ * 14):
            if len(here_) >= want_:
                break
            p = TYRE_RNG.choice(_sheets[bid])
            X_s, Y_s, Z_s = _rot_axes(p["rot"])
            if Y_s[2] <= 0.0:
                X_s, Y_s = (-X_s[0], -X_s[1], -X_s[2]), (-Y_s[0], -Y_s[1], -Y_s[2])
            k_ = TYRE_RNG.uniform(0.58, 0.72)
            r_ = TYRE_R * k_
            hw_ = 81.2 * abs(p["scale"][0]) - r_ - 3.0
            len_ = (164.9 if p["asset"].endswith(("_003", "_004")) else 324.9) * abs(p["scale"][2])
            if hw_ <= 0.0 or len_ - 2.0 * (r_ + 18.0) <= 0.0:
                continue
            a_, m_ = TYRE_RNG.uniform(-hw_, hw_), TYRE_RNG.uniform(r_ + 18.0, len_ - r_ - 18.0)
            spot = tuple(p["loc"][i] + X_s[i] * a_ - Z_s[i] * m_ for i in range(3))
            if any(math.hypot(spot[0] - o[0], spot[1] - o[1]) < 130.0 for o in _on_roofs) or any(math.hypot(spot[0] - o[0], spot[1] - o[1]) < 2.0 * TYRE_R * 0.72 + 10.0 for o in here_):
                continue
            ang = TYRE_RNG.uniform(0.0, 360.0)
            A_t = v_rot(X_s, Y_s, ang)
            C_t = v_cross(Y_s, A_t)
            lift_ = 2.4 + 1.5 + TYRE_HALF * k_
            centre = tuple(spot[i] + Y_s[i] * lift_ for i in range(3))
            label = "Tyre_%s_%d" % (bid, len(here_))
            put(label, MEAST + "SM_wheel_01", centre[0], centre[1], centre[2], 0.0, (k_, k_, k_), folder=DR_TYRES, nocoll=True, mats=[BM + "MI_BackAlleys_Tyre"])
            items[-1]["rot"] = axes_rot(Y_s, A_t, C_t)
            _cheap(CULL_MID)
            _tyre_n["tyres"] += 1
            if TYRE_RNG.random() < P_TYRE_STACK:
                c2 = tuple(centre[i] + Y_s[i] * (2.0 * TYRE_HALF * k_ + 0.4) for i in range(3))
                put(label + "_Top", MEAST + "SM_wheel_01", c2[0] + TYRE_RNG.uniform(-5.0, 5.0), c2[1] + TYRE_RNG.uniform(-5.0, 5.0), c2[2], 0.0, (k_, k_, k_), folder=DR_TYRES, nocoll=True, mats=[BM + "MI_BackAlleys_Tyre"])
                items[-1]["rot"] = axes_rot(Y_s, A_t, C_t)
                _cheap(CULL_MID)
                _tyre_n["tyres"] += 1
                _tyre_n["stacks"] += 1
            here_.append(spot)
        if here_:
            _tyre_n["roofs"] += 1
    print("tyres:", _tyre_n)

# Water meters at the foot of a wall, as a house's feed comes up out of the ground. One to four in a row, on their own legs, with a pipe along the ground under a row. Faces that take dressing
# only; not on the stairs' walls, nor across a pipe or a door. One lot to a house. No collision: nobody should trip on a 30 cm pipe. User 2026-11-06: "the water meter needs to be distributed more":
# they had bunched in the east, with one lot in the whole west half. So each lot now goes where it's furthest from the others, with enough give that the spacing doesn't read as a grid, and
# never nearer than WATER_GAP. A door nearby counts for a little. The claim stops at 45 cm, under the graffiti's lowest band, so moving a meter can't move a tag.
WATER_RNG = random.Random(263)
WATER_LOTS, WATER_GAP = 20, 550.0
_water_n = {"lots": 0, "meters": 0}
if STREET_WATER_METERS:
    _draw_water_n = shuffle_bag(WATER_RNG, (1, 1, 1, 2, 2, 3, 3, 4))
    N_WATER = FLOOR_OUT + 8.0
    _water_spots = []
    for u in sorted(_wall_tiles, key=lambda t_: t_["label"]):
        if u["s"] != 0 or _hollow_face(u) or u["kind"] not in _plain_tile + ("SM_Wall_Windows_01", "SM_WallDoor_01"):
            continue
        in0, in1 = _inside_face(u, 0.0, u["w"])
        # On a door's tile, only what's left beside the door.
        spans_ = [(in0, min(in1, 30.0 * u["sx"])), (max(in0, 195.0 * u["sx"]), in1)] if u["kind"] == "SM_WallDoor_01" else [(in0, in1)]
        for lo_, hi_ in spans_:
            s_ = lo_
            while s_ + 40.0 <= hi_:
                x_, y_ = at(u["x"], u["y"], u["side"], s_ + 20.0, N_WATER)
                _water_spots.append({"u": u, "lo": s_, "hi": hi_, "x": x_, "y": y_, "door": u["kind"] == "SM_WallDoor_01"})
                s_ += 45.0
    _water_lots, _water_houses = [], set()
    while _water_n["lots"] < WATER_LOTS:
        best, best_score = None, -1.0
        for c_ in _water_spots:
            if c_["u"]["house"] in _water_houses:
                continue
            near = min((math.hypot(c_["x"] - o[0], c_["y"] - o[1]) for o in _water_lots), default=5000.0)
            if near < WATER_GAP:
                continue
            score = near * WATER_RNG.uniform(0.55, 1.45) * (1.15 if c_["door"] else 1.0)
            if score > best_score:
                best, best_score = c_, score
        if best is None:
            break
        _water_spots.remove(best)
        u = best["u"]
        n_m = _draw_water_n()
        gap_ = WATER_RNG.uniform(38.0, 46.0)
        while (n_m - 1) * gap_ + 40.0 > best["hi"] - best["lo"]:
            n_m -= 1
        w_ = (n_m - 1) * gap_ + 40.0
        s0 = best["lo"]
        s1 = s0 + w_
        a_, b_ = at(u["x"], u["y"], u["side"], s0, 5.0), at(u["x"], u["y"], u["side"], s1, 28.0)
        box_ = (min(a_[0], b_[0]), min(a_[1], b_[1]), 0.0, max(a_[0], b_[0]), max(a_[1], b_[1]), 45.0)
        if not _free(box_, 1.0) or not _pipe_free(u, s0 - 6.0, s1 + 6.0) or not _stair_clear(u, s0, s1, 0.0) or not all(_ground_open(u, s_, 40.0) for s_ in (s0, s1)):
            continue
        rx, ry = RUN[u["side"]]
        yaw_ = YAW[u["side"]] + 90.0
        h_base = WATER_RNG.uniform(5.0, 11.0)
        for j in range(n_m):
            s_ = s0 + 20.0 + j * gap_
            h_ = h_base + WATER_RNG.uniform(-1.5, 1.5)
            x_, y_ = at(u["x"], u["y"], u["side"], s_, N_WATER)
            label = "WaterMeter_%s_%d" % (u["label"], j)
            put(label, WATER_MESH % WATER_RNG.choice((1, 2)), x_, y_, h_ + 2.4, yaw_ + WATER_RNG.uniform(-3.0, 3.0), (1, 1, 1), folder=DR_WATER, nocoll=True, mats=[BM + "MI_BackAlleys_WaterMeter"])
            _cheap(CULL_NEAR)
            for e_, off_ in enumerate((-16.0, 15.2)):       # local +Y points back along the run
                _rod("%s_Leg%d" % (label, e_), (x_ + rx * off_, y_ + ry * off_, 0.0), (x_ + rx * off_, y_ + ry * off_, h_ + 1.0), 2.6, FLASH_MAT, DR_WATER, CULL_NEAR)
            _water_n["meters"] += 1
        if n_m > 1:
            p0, p1 = at(u["x"], u["y"], u["side"], s0 + 2.0, N_WATER), at(u["x"], u["y"], u["side"], s1 - 2.0, N_WATER)
            _rod("WaterMeter_%s_Feed" % u["label"], (p0[0], p0[1], 2.5), (p1[0], p1[1], 2.5), 2.6, FLASH_MAT, DR_WATER, CULL_NEAR)
        _claim(box_)
        _water_lots.append((best["x"], best["y"]))
        _water_houses.add(u["house"])
        _water_n["lots"] += 1
    print("water meters:", _water_n)

# Graffiti. User 2026-11-06: "added 10 graffitits": five crew tags and five painted warnings, white-on-black masks in /Game/Project_Bopis_Graffiti_Decals, which stay as supplied. Decals, with the
# paint in the material (create_graffiti_materials_ue.py). On the clear stretches of ground-floor walls, at hand height, and on closed shutters with no poster on them, where "Bawal Pumarada" and
# "Huwag Harangan ang Daan" belong. Never on a hollow-block face or a thin wall, which keep their own rules. One to a house, the same image not twice in a view. Tags lean a little; warnings less.
STREET_GRAFFITI = True
DR_GRAFFITI = "BackAlleys/Graffiti"
GRAF_RNG = random.Random(271)
GRAF_WALLS, GRAF_SHUTTERS = 13, 3
GRAF_GAP, GRAF_SAME_GAP = 350.0, 1100.0
GRAF_ROLL = 90.0
GRAF_TAGS = {"Bakod_7": ("Black", "Red"), "Eskinita_13": ("White", "Blue"), "Kanto_Boys": ("Black", "Blue"), "Loob_Crew": ("Black", "White"), "Siksik": ("Red", "Black")}
GRAF_SIGNS = {"Bawal_Magtapon_ng_Basura": ("Black", "Red"), "Bawal_Pumarada": ("White", "Red"), "Bawal_Pumasok": ("Red", "White"), "Bawal_Umihi_Dito": ("Black", "Red"),
              "Huwag_Harangan_ang_Daan": ("Black", "White")}
GRAF_ON_SHUTTERS = ("Bawal_Pumarada", "Huwag_Harangan_ang_Daan", "Kanto_Boys", "Siksik", "Bakod_7")
GRAF_BANDS = ((70.0, 200.0), (85.0, 215.0), (60.0, 180.0), (70.0, 170.0))      # what shows of the image, up the wall. The masks' ink fills about 80% of the square
GRAF_INK = 0.8
GRAF_LIGHT = ("White", "Cream", "Yellow", "Mint", "Peach")
_graf_n = {"walls": 0, "shutters": 0}
_graf_done = []


def _graffiti(label, x_, y_, z_, side, name, w_, light=False):
    table = GRAF_TAGS if name in GRAF_TAGS else GRAF_SIGNS
    paints = [c_ for c_ in table[name] if not (light and c_ == "White")] or list(table[name])
    tilt = GRAF_RNG.uniform(-4.0, 4.0) if name in GRAF_TAGS else GRAF_RNG.uniform(-1.2, 1.2)
    nx, ny = NORMAL[side]
    put(label, BM + "MI_BackAlleys_Spray_%s_%s" % (name, GRAF_RNG.choice(paints)), x_, y_, z_, math.degrees(math.atan2(-ny, -nx)), (0.03, w_ / 512.0, w_ / 512.0), folder=DR_GRAFFITI,
        roll=GRAF_ROLL + tilt, decal=True)
    _graf_done.append((x_, y_, name))


def _graf_room(x_, y_, name):
    return all(math.hypot(x_ - o[0], y_ - o[1]) >= (GRAF_SAME_GAP if o[2] == name else GRAF_GAP) for o in _graf_done)


if STREET_GRAFFITI and STREET_POSTERS:
    _posters_now = [p for p in items if p["folder"] == DR_POSTERS]
    _bare_shops = []
    for u, s0, wid in _shops:
        Xc, Yc = at(u["x"], u["y"], u["side"], s0 + wid / 2, 8.8)
        rx, ry = RUN[u["side"]]
        nx, ny = NORMAL[u["side"]]
        if not any(abs((p["loc"][0] - Xc) * nx + (p["loc"][1] - Yc) * ny) < 16.0 and abs((p["loc"][0] - Xc) * rx + (p["loc"][1] - Yc) * ry) < wid / 2 + 40.0 for p in _posters_now):
            _bare_shops.append((u, s0, wid))
    GRAF_RNG.shuffle(_bare_shops)
    _graf_houses = set()
    _draw_shutter_graf = shuffle_bag(GRAF_RNG, GRAF_ON_SHUTTERS)
    for u, s0, wid in _bare_shops[:GRAF_SHUTTERS]:
        name = _draw_shutter_graf()
        w_ = min(GRAF_RNG.uniform(135.0, 165.0), wid * 0.98)
        x_, y_ = at(u["x"], u["y"], u["side"], s0 + wid / 2 + GRAF_RNG.uniform(-8.0, 8.0), 8.8)
        _graffiti("Graffiti_%s_Shutter" % u["label"], x_, y_, u["z"] + GRAF_RNG.uniform(120.0, 170.0), u["side"], name, w_)
        _graf_houses.add(u["house"])
        _graf_n["shutters"] += 1
    # Where there's room: the longest clear wall goes first, as it's the one that reads as bare.
    _graf_spots = []
    for name_, ts in _run_tiles.items():
        t0 = ts[0]
        if t0["s"] != 0 or _hollow_face(t0) or ts[-1]["off"] + ts[-1]["w"] - t0["off"] < 200.0:
            continue
        for band in GRAF_BANDS:
            for a_, e_ in _stretches(ts, band):
                _graf_spots.append((e_ - a_, GRAF_RNG.random(), name_, band, a_, e_))
    _graf_spots.sort(key=lambda g_: -g_[0] * GRAF_RNG.uniform(0.75, 1.25))
    _draw_graf = shuffle_bag(GRAF_RNG, tuple(sorted(GRAF_TAGS)) + tuple(sorted(GRAF_SIGNS)))
    for _len, _r, name_, band, a_, e_ in _graf_spots:
        if _graf_n["walls"] >= GRAF_WALLS:
            break
        ts = _run_tiles[name_]
        t0 = ts[0]
        if t0["house"] in _graf_houses:
            continue
        w_ = min(GRAF_RNG.uniform(125.0, 185.0), (e_ - a_) / 0.92, (band[1] - band[0]) / GRAF_INK)
        if w_ < 95.0:
            continue
        s_ = GRAF_RNG.uniform(a_ + 0.46 * w_, e_ - 0.46 * w_)
        x_, y_ = at(t0["x"], t0["y"], t0["side"], s_, 2.0)
        z_ = t0["z"] + (band[0] + band[1]) / 2
        for _try in range(10):
            name = _draw_graf()
            if _graf_room(x_, y_, name):
                break
        else:
            continue
        light_ = any(k_ in str(_paint.get((t0["house"], t0["letter"]), "")) for k_ in GRAF_LIGHT)
        _graffiti("Graffiti_%s_%d" % (t0["label"], _graf_n["walls"]), x_, y_, z_, t0["side"], name, w_, light_)
        _claim(_wbox(t0, s_ - 0.46 * w_, s_ + 0.46 * w_, z_ - w_ * GRAF_INK / 2, z_ + w_ * GRAF_INK / 2, 3.0))
        _graf_houses.add(t0["house"])
        _graf_n["walls"] += 1
    print("graffiti:", _graf_n, sorted(o[2] for o in _graf_done))

print("street:", dict(sorted(_street_n.items())))
print("  bare ground tiles left:", sum(1 for t in _dress_tiles if t["s"] == 0 and not t["has"]))

_bare = [t for t in _dress_tiles if not t["has"]]
print("dressing: %d blank tiles (no hollow blocks), %d now have something, %d stay bare" % (
    len(_dress_tiles), len(_dress_tiles) - len(_bare), len(_bare)))
print("  rooms %d, downpipes %d, air conditioners %d, patches %s, vents on %d tiles, steps %s, laundry %s" % (
    _n_rooms, _n_pipes, _n_acs, _n_patch, _n_vents, _n_steps, _n_laundry))
items[:] = [p for p in items if p["label"] not in _buried_stalls]
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
