# Pass `awnings`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Window and door awnings.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
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
    if not (W0 < lx < W and H0 < ly < H):
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
    if not awn_clear(*lay(X, Y), p["loc"][2] - FLOOR_H + 270.0, h):
        _awn_count["reach"] += 1
        continue
    awning(p, h, _awn_kind[h])
    _awn_count[_awn_kind[h]] += 1
print("awnings:", _awn_count, "; houses:", dict(__import__("collections").Counter(_awn_kind.values())))
