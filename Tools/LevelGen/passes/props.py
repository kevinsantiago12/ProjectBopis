# Pass `props`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Things people use: seats, tables, buckets, pots; physical props kept clear of everything.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# Things people use. User 2026-11-06: "wooden bench-stools, plastic seats and tables in some areas. Buckets, potted plants on the balconies". Monobloc chairs and stools from the Philippine Markets pack. It has no
# wooden stool, so AsiaSlum's heavy table (SM_Table_B_001) squeezed narrow and low is a bangko, or a stool when short. No pack has a plastic table: the tables are the market pack's SM_Table_01, cut down. A scaled-up
# SM_Monobloc_Stool_02 stood in at first, and the user wouldn't have it: "monobloc stool 02 is a chair, not a table". In some areas,
# not everywhere: a table with seats where a lane has room, a bench against a wall, a chair by a door, a bucket under a downpipe. Furniture stops a shot and reports its surface, and a pawn walks through it
# (IgnoreOnlyPawn), so no fight or nav path changes. A chair faces its local -Y. On the balconies: pots on a parapet's ledge, where they can be seen from the street, and bigger plants on the floor behind it,
# tall enough to show over it; behind a wooden banister, on the floor. Old tins as pots now and then.
GROUND_PROPS = True
DR_PROPS = "BackAlleys/Props"
PROP_RNG = random.Random(307)
PMAT = "/Game/Philippines_Markets/Materials/"
MB_DIR = PM + "MonoBloc_Chairs_01/"
MB_CHAIR, MB_BENCH, MB_STOOL1, MB_STOOL2 = MB_DIR + "SM_Monobloc_Chair_01", MB_DIR + "SM_Monobloc_Chair_03", MB_DIR + "SM_Monobloc_Stool_01", MB_DIR + "SM_Monobloc_Stool_02"
MB_CHAIR_MATS = tuple(PMAT + "MI_Monobloc_Chair_01" + k_ for k_ in ("", "a", "b", "c", "d"))
MB_BENCH_MATS = (PMAT + "MI_Monobloc_Chair_03", PMAT + "MI_Monobloc_Chair_03a")
MB_STOOL_MATS = tuple(PMAT + "MI_Monobloc_Stool_01" + k_ for k_ in ("", "a", "b"))
# A monobloc piece's colour is picked once, when it's placed, and never changes. Most of the pack's monobloc instances have "Activate Random Color?" on: MF_PerInstanceColor looks the
# colour up in TX_ColorVariation_BC_01 (a 4 x 4 palette) at the piece's world position x 10 per cm, so a physical piece changed colour as it moved (user 2026-11-07: "the monobloc MI for
# chair 1 (not 1b) has code that changes his color in realtime", "there are still issus with the monobloc MI, for the other stool 02"). User: "code the material so it does not regenerate
# the color if moved? only generate on spawn time". MF_PerInstanceColor now has a switch, "Colour From Spawn Seed?" (off by default, so the rest of the pack is as it was): on, the
# palette cell comes from "Spawn Seed", custom primitive data 0, which the placers write on each piece from its "seed". The *_SpawnColour instances in Materials/Monobloc have it on.
# Chairs also use the pack's Chair_01a-c, which have random colour off. The old draws from the lists above still happen, so nothing moves; looks come from MB_MAT_RNG.
MB_MONO_DIR = BA_DIR + "Materials/Monobloc/"
MB_SEEDED = {MB_CHAIR: MB_MONO_DIR + "MI_Monobloc_Chair_01_SpawnColour", MB_BENCH: MB_MONO_DIR + "MI_Monobloc_Chair_03_SpawnColour",
             MB_STOOL1: MB_MONO_DIR + "MI_Monobloc_Stool_01_SpawnColour", MB_STOOL2: MB_MONO_DIR + "MI_Monobloc_Stool_02_SpawnColour"}
MB_CHAIR_FIXED = (PMAT + "MI_Monobloc_Chair_01a", PMAT + "MI_Monobloc_Chair_01b", PMAT + "MI_Monobloc_Chair_01c")
MB_MAT_RNG = random.Random(331)


def _mono_look(mesh, _drawn=None):
    """A monobloc piece's look, (material, seed): one of the palette's 16 colours by its seed, or for a chair now and then one of the pack's fixed ones (seed None).
    _drawn is the old draw from PROP_RNG, kept only so nothing else moves."""
    if mesh == MB_CHAIR and MB_MAT_RNG.random() < 3.0 / 19.0:
        return (MB_MAT_RNG.choice(MB_CHAIR_FIXED), None)
    return (MB_SEEDED[mesh], round(MB_MAT_RNG.random(), 4))


WOOD_BENCH = AS + "Interior/SM_Table_B_001"     # 214 x 116 x 96
PROP_TABLE = PM + "Table_01/SM_Table_01"        # 171 x 78 x 90
PROP_TABLE_K, PROP_TABLE_TOP, PROP_TABLE_N = (0.72, 0.95, 0.82), 90.0 * 0.82, 62.0   # scale, height of its top, how far its middle stands off the lining
BK_DIR = PM + "Buckets_Set_01/"
PROP_BUCKETS = (BK_DIR + "SM_Bucket_01", BK_DIR + "SM_Bucket_02", BK_DIR + "SM_Bucket_03", ME + "Favela/SM_MetalBucket_01", ME + "Favela/SM_MetalBucket_02")
# Mass of the light pieces, which are physical. SM_MetalBucket_01 has water in it, so it stays put: "some props like the filled bucket need to be static".
PROP_KG = {MB_CHAIR: 2.5, MB_BENCH: 4.5, MB_STOOL1: 1.2, MB_STOOL2: 1.3, BK_DIR + "SM_Bucket_01": 0.8, BK_DIR + "SM_Bucket_02": 0.5, BK_DIR + "SM_Bucket_03": 0.9, ME + "Favela/SM_MetalBucket_02": 1.6}
PROP_REACH = {BK_DIR + "SM_Bucket_01": 17.0, BK_DIR + "SM_Bucket_02": 12.0, BK_DIR + "SM_Bucket_03": 19.0, ME + "Favela/SM_MetalBucket_01": 18.0, ME + "Favela/SM_MetalBucket_02": 18.0}
POT_DIR = ME + "Yakohama/SM_FlowerPots_"
POT_SIZE = {"01": (32.0, 34.0, 1.0), "02": (47.0, 30.0, 0.0), "03": (26.0, 32.0, 0.0), "04": (30.0, 32.0, 0.0), "05": (35.0, 36.0, 3.0)}      # height, across, how far under its pivot
POT_TWIN = {"01": "06", "02": "07", "03": "08", "04": "09", "05": "10"}     # the same pot in its other colour
# Pots are physical (user 2026-11-07: "The pots dont get physics", "the pots and bags dont even collide"): a pot with its soil at scale 1, times the cube of the scale. Its plant has no
# collision and rides it, attached. 01-05 are terracotta (T_FlowerPots_02_BC, brown) and take Clay; 06-10 are coloured plastic (T_FlowerPots_01_BC, with a recycling mark); a tin is Metal.
POT_KG = {"01": 8.0, "02": 9.0, "03": 5.0, "04": 6.0, "05": 9.0}
POT_TIN_KG = 4.0
PLANT_SMALL = ((ME + "Favela/Plants/SM_Plant_23", 0.6, 0.85), (ME + "Favela/Plants/SM_Plant_25", 0.6, 0.85), (ME + "Favela/Plants/SM_Plant_26", 0.8, 1.05), (ME + "Yakohama/SM_Plants_05", 0.7, 0.95), (ME + "Yakohama/SM_Plants_04", 0.55, 0.75))
PLANT_TALL = ((ME + "Yakohama/SM_Plants_02", 0.7, 0.85, 79.0), (ME + "Yakohama/SM_Plants_03", 0.9, 1.1, 54.0), (ME + "Favela/Plants/SM_Plant_27", 1.3, 1.7, 25.0), (ME + "Favela/Plants/SM_Plant_24", 1.2, 1.6, 32.0))      # lowest scale, highest, reach at scale 1
_prop_n = {}


def _prop_fits(x_, y_, yaw_, hx, hy):
    """A piece's footprint, half hx by hy, clear of every house and its lining. User 2026-11-06: "one of the chairs is into the wall too": a chair turned 42 degrees swings a corner 44 cm out from its middle."""
    c_, s_ = math.cos(math.radians(yaw_)), math.sin(math.radians(yaw_))
    for ax, ay in ((1, 1), (1, -1), (-1, 1), (-1, -1), (1, 0), (-1, 0), (0, 1), (0, -1)):
        px_, py_ = x_ + c_ * ax * hx - s_ * ay * hy, y_ + s_ * ax * hx + c_ * ay * hy
        lx_, ly_ = _lay(px_, py_)
        if _on_floor(px_, py_) or solid(lx_, ly_, 0):
            return False
    return True


def _rot_axes3(rot):
    """A plan rotation [pitch, yaw, roll] as its X, Y and Z axes."""
    p_, y_, r_ = (math.radians(a_) for a_ in rot)
    cp, sp, cy, sy, cr, sr = math.cos(p_), math.sin(p_), math.cos(y_), math.sin(y_), math.cos(r_), math.sin(r_)
    return ((cp * cy, cp * sy, sp), (sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp), (-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp))


_MESH_BOUNDS = None


def _piece_box(p):
    """A placed piece as a box on the ground, (x, y, half x, half y, yaw, z0, z1), from the packs' measured bounds; None if it isn't known. Turned pieces that aren't flat go by their whole extent."""
    global _MESH_BOUNDS
    if _MESH_BOUNDS is None:
        _MESH_BOUNDS = {}
        try:
            m_ = json.load(open("Saved/LevelGen/visual/meshes.json", encoding="utf-8"))
            for e_ in (m_ if isinstance(m_, list) else list(m_.values())):
                _MESH_BOUNDS[e_["path"]] = (e_["bounds_min"], e_["bounds_max"])
        except (OSError, ValueError, KeyError):
            pass
        _MESH_BOUNDS[CUBE] = ((0.0, 0.0, 0.0), (100.0, 100.0, 100.0))
        _MESH_BOUNDS[PLANE] = ((-50.0, -50.0, 0.0), (50.0, 50.0, 0.0))
        for k_, v_ in LT_BAG_PHYS.items():      # the bags' project copies measure as the pack's
            if k_ in _MESH_BOUNDS:
                _MESH_BOUNDS[v_] = _MESH_BOUNDS[k_]
    if p.get("decal") or p.get("light"):
        return None
    b_ = _MESH_BOUNDS.get(p["asset"])
    if b_ is None:
        return None
    lo_, hi_ = b_
    sx_, sy_, sz_ = p["scale"]
    X_, Y_, Z_ = _rot_axes3(p["rot"])
    pts = []
    for cx_ in (lo_[0], hi_[0]):
        for cy_ in (lo_[1], hi_[1]):
            for cz_ in (lo_[2], hi_[2]):
                pts.append(tuple(p["loc"][k_] + X_[k_] * cx_ * sx_ + Y_[k_] * cy_ * sy_ + Z_[k_] * cz_ * sz_ for k_ in range(3)))
    z0_, z1_ = min(q_[2] for q_ in pts), max(q_[2] for q_ in pts)
    if abs(p["rot"][0]) < 0.5 and abs(p["rot"][2]) < 0.5:
        # Flat: a turned rectangle, exactly.
        c_, s_ = math.cos(math.radians(p["rot"][1])), math.sin(math.radians(p["rot"][1]))
        mx_, my_ = (lo_[0] + hi_[0]) / 2 * sx_, (lo_[1] + hi_[1]) / 2 * sy_
        return (p["loc"][0] + c_ * mx_ - s_ * my_, p["loc"][1] + s_ * mx_ + c_ * my_, abs(hi_[0] - lo_[0]) * abs(sx_) / 2, abs(hi_[1] - lo_[1]) * abs(sy_) / 2, p["rot"][1], z0_, z1_)
    x0_, x1_, y0_, y1_ = min(q_[0] for q_ in pts), max(q_[0] for q_ in pts), min(q_[1] for q_ in pts), max(q_[1] for q_ in pts)
    return ((x0_ + x1_) / 2, (y0_ + y1_) / 2, (x1_ - x0_) / 2, (y1_ - y0_) / 2, 0.0, z0_, z1_)


def _boxes_meet(a_, b_, gap=0.5):
    """Two pieces' boxes overlap, by more than gap, in height and on the ground (separating axes)."""
    if a_[5] + gap >= b_[6] or b_[5] + gap >= a_[6]:
        return False
    for box_ in (a_, b_):
        c_, s_ = math.cos(math.radians(box_[4])), math.sin(math.radians(box_[4]))
        for ax_, ay_ in ((c_, s_), (-s_, c_)):
            def reach(q_):
                cq, sq = math.cos(math.radians(q_[4])), math.sin(math.radians(q_[4]))
                return abs((cq * ax_ + sq * ay_) * q_[2]) + abs((-sq * ax_ + cq * ay_) * q_[3])
            d_ = abs((b_[0] - a_[0]) * ax_ + (b_[1] - a_[1]) * ay_)
            if d_ + gap >= reach(a_) + reach(b_):
                return False
    return True


def _prop(label, asset, x_, y_, yaw_, kind, scale=(1.0, 1.0, 1.0), mats=None, surface=None, z=None, draw=None, noshadow=False, fit=None, kg=None, weld_to=None, look=None):
    """kg: a physical piece of that mass, which a shot or a blast moves (user 2026-11-07: "I want bullets to affect them", "only light things"). weld_to: the physical piece this one is welded to."""
    if fit and not _prop_fits(x_, y_, yaw_, fit[0], fit[1]):
        return False
    z_ = _ground_top(x_, y_) + 0.1 if z is None else z
    if look:
        mats = [look[0]]     # a monobloc piece: its material, and the seed that picks its colour once (_mono_look)
    put(label, asset, x_, y_, z_, yaw_, scale, folder=DR_PROPS, nocoll=surface is None, mats=mats)
    if look and look[1] is not None:
        items[-1]["seed"] = look[1]
    if surface:
        items[-1]["coll"] = "IgnoreOnlyPawn"
        items[-1]["phys"] = PHYS + surface
        items[-1]["nonav"] = True
    if kg or weld_to:
        # Starts asleep, doesn't touch the nav mesh or run overlap events: the casings' cost in trace 24 was exactly that. A piece with no collision of its own (a pot's plant) stays
        # without: it's only attached, and rides its parent.
        if not items[-1]["nocoll"]:
            items[-1]["coll"] = "PhysicsActor"
        items[-1]["nonav"] = True
        if kg:
            items[-1]["physics"] = kg
            items[-1]["cap"] = list(PHYS_CAP)
        if weld_to:
            items[-1]["weld_to"] = weld_to
    _cheap(CULL_NEAR if draw is None else draw, noshadow=noshadow)
    _prop_n[kind] = _prop_n.get(kind, 0) + 1
    return True


def _facing(dx_, dy_):
    """The yaw that turns a chair, which faces its local -Y, toward (dx_, dy_)."""
    return math.degrees(math.atan2(dx_, -dy_))


if GROUND_PROPS and GROUND_DIRT and GROUND_LITTER:
    _prop_done, _prop_tables = [], []
    _prop_keep = [tuple(ue(k_["x"], k_["y"])) for k_ in L["pickups"]] + [tuple(ue(L["player_start"]["x"], L["player_start"]["y"]))] + [tuple(ue(d_["x"], d_["y"])) for d_ in L["doors"]]
    _prop_doors = [at(u["x"], u["y"], u["side"], 112.5 * u["sx"], 0.0) for u in _wall_tiles if u["s"] == 0 and u["kind"] == "SM_WallDoor_01"]
    # Each ground-floor door's way, as check_dressing tests it: within 82.5 cm (times the tile's width) of the opening's middle along the wall
    # and 0-110 cm out. 2026-11-09: on the slum's tighter fronts a door pot walking along its wall from one door stopped in front of the next.
    _prop_door_ax = [(at(u["x"], u["y"], u["side"], 112.5 * u["sx"], 0.0), RUN[u["side"]], NORMAL[u["side"]], u["sx"]) for u in _wall_tiles
                     if u["s"] == 0 and u["kind"] == "SM_WallDoor_01"]

    def _in_doorway(x_, y_):
        for (cx_, cy_), (rx_, ry_), (nx_, ny_), sx_ in _prop_door_ax:
            dx_, dy_ = x_ - cx_, y_ - cy_
            if abs(dx_ * rx_ + dy_ * ry_) < 82.5 * sx_ and 0.0 < dx_ * nx_ + dy_ * ny_ < 110.0:
                return True
        return False

    def _prop_take(gap, need_n, width, near_door=False):
        """A clear stretch at the foot of a wall with need_n cm of open ground in front of it, well away from other lots, pickups and doors in the end walls."""
        spots_ = list(_lt_spots)
        PROP_RNG.shuffle(spots_)
        for c_ in spots_:
            u = c_["u"]
            if c_["hi"] - c_["lo"] < width:
                continue
            xy_ = (c_["x"], c_["y"])
            if any(math.hypot(xy_[0] - o_[0], xy_[1] - o_[1]) < gap for o_ in _prop_done) or any(math.hypot(xy_[0] - o_[0], xy_[1] - o_[1]) < 200.0 for o_ in _lt_done):
                continue
            if any(math.hypot(xy_[0] - o_[0], xy_[1] - o_[1]) < 260.0 for o_ in _prop_keep) or any(math.hypot(xy_[0] - o_[0], xy_[1] - o_[1]) < 130.0 for o_ in _posts):
                continue
            if near_door and not any(math.hypot(xy_[0] - o_[0], xy_[1] - o_[1]) < 380.0 for o_ in _prop_doors):
                continue
            mid = (c_["lo"] + c_["hi"]) / 2
            a_, b_ = at(u["x"], u["y"], u["side"], c_["lo"], 8.0), at(u["x"], u["y"], u["side"], c_["hi"], min(need_n, 130.0))
            box_ = (min(a_[0], b_[0]), min(a_[1], b_[1]), 0.0, max(a_[0], b_[0]), max(a_[1], b_[1]), 110.0)
            if not _ground_open(u, mid, need_n) or not _free(box_, 1.0) or not _pipe_free(u, c_["lo"], c_["hi"]) or not _stair_clear(u, c_["lo"], c_["hi"], 0.0):
                continue
            _prop_done.append(xy_)
            return c_
        return None

    def _prop_on(u, s_, n_):
        return at(u["x"], u["y"], u["side"], s_, FLOOR_OUT + n_)

    def _prop_bucket(label, x_, y_, kind="bucket", z=None, asset=None):
        asset = asset or PROP_RNG.choice(PROP_BUCKETS)
        _prop(label, asset, x_, y_, PROP_RNG.uniform(0.0, 360.0), kind, z=z, surface="Plastic" if "Philippines" in asset else "Metal", kg=PROP_KG.get(asset))
        return asset

    # A table where a lane has room, with seats pulled up to it, some crates, a cup or two. Seats of one colour more often than not.
    for k_ in range(4):
        c_ = _prop_take(800.0, 340.0, 170.0)
        if c_ is None:
            break
        u = c_["u"]
        mid = (c_["lo"] + c_["hi"]) / 2 + PROP_RNG.uniform(-10.0, 10.0)
        tx_, ty_ = _prop_on(u, mid, PROP_TABLE_N)
        _prop_tables.append((tx_, ty_))
        top_ = _ground_top(tx_, ty_) + PROP_TABLE_TOP
        _prop("Prop_Table_%d" % k_, PROP_TABLE, tx_, ty_, YAW[u["side"]] + PROP_RNG.uniform(-5.0, 5.0), "table", PROP_TABLE_K, mats=[BM + "MI_BackAlleys_Table_Clean"], surface="Wood", draw=CULL_MID, fit=(62.0, 37.0))      # user 2026-11-06: "the table texture is a filthy texture", create_clean_table_material_ue.py
        # A chair is 58 x 65, and the table 123 x 74: three seats at most, either end and the street side.
        places = [(-104.0, PROP_RNG.uniform(-8.0, 8.0)), (104.0, PROP_RNG.uniform(-8.0, 8.0)), (PROP_RNG.uniform(-14.0, 14.0), 84.0)]
        PROP_RNG.shuffle(places)
        colour = _mono_look(MB_CHAIR, PROP_RNG.choice(MB_CHAIR_MATS))
        for j_, (ds_, dn_) in enumerate(places[:PROP_RNG.choice((2, 2, 3))]):
            sx_, sy_ = _prop_on(u, mid + ds_, PROP_TABLE_N + dn_)
            if any(math.hypot(sx_ - o_[0], sy_ - o_[1]) < 150.0 for o_ in _prop_doors):        # half a door, and a chair's reach
                continue
            if PROP_RNG.random() < 0.72:
                yaw_ = _facing(tx_ - sx_, ty_ - sy_) + PROP_RNG.uniform(-24.0, 24.0)
                _prop("Prop_Table_%d_Seat%d" % (k_, j_), MB_CHAIR, sx_, sy_, yaw_, "chair", look=colour if PROP_RNG.random() < 0.7 else _mono_look(MB_CHAIR, PROP_RNG.choice(MB_CHAIR_MATS)), surface="Plastic", draw=CULL_MID, fit=(29.0, 33.0), kg=PROP_KG[MB_CHAIR])
            else:
                _prop("Prop_Table_%d_Seat%d" % (k_, j_), MB_STOOL1, sx_, sy_, PROP_RNG.uniform(0.0, 360.0), "stool", look=_mono_look(MB_STOOL1, PROP_RNG.choice(MB_STOOL_MATS)), surface="Plastic", fit=(20.0, 20.0), kg=PROP_KG[MB_STOOL1])
        if PROP_RNG.random() < 0.75:
            bx_, by_ = _prop_on(u, mid + PROP_RNG.uniform(-70.0, 70.0), 26.0)
            for j_ in range(PROP_RNG.choice((1, 1, 2))):
                _prop("Prop_Table_%d_Crate%d" % (k_, j_), PM + "BottleCrateSet_01/SM_BottleCrate_0%d" % PROP_RNG.choice((1, 2)), bx_, by_, YAW[u["side"]] + PROP_RNG.uniform(-12.0, 12.0), "crate", z=_ground_top(bx_, by_) + 0.1 + j_ * 12.0)
        for j_ in range(PROP_RNG.choice((0, 1, 2))):
            cx_, cy_ = tx_ + PROP_RNG.uniform(-24.0, 24.0), ty_ + PROP_RNG.uniform(-24.0, 24.0)
            _prop("Prop_Table_%d_Cup%d" % (k_, j_), LT_ME + "SM_cup", cx_, cy_, PROP_RNG.uniform(0.0, 360.0), "cup", z=top_)
    # A seat by a door, left where somebody got up. User 2026-11-06: "monobloc stool 02 is a chair, not a table", "use the chairs near doors". Going by the wall's clear stretches, the lots above took nearly all of them
    # and two doors got a seat, so these work from the doors themselves: most doors have one seat just past the frame and clear of its step, a few have one each side.
    # Ahead of the benches and buckets, so the doors get first pick.
    _door_tiles = [u for u in _wall_tiles if u["s"] == 0 and u["kind"] == "SM_WallDoor_01"]
    PROP_RNG.shuffle(_door_tiles)
    _draw_seat = shuffle_bag(PROP_RNG, ("square", "chair", "square", "chair", "round"))
    for k_, u in enumerate(_door_tiles):
        if PROP_RNG.random() > 0.88:
            continue
        centre_ = 112.5 * u["sx"]
        sides_ = [-1.0, 1.0]
        PROP_RNG.shuffle(sides_)
        for j_, d_ in enumerate(sides_):
            s_ = centre_ + d_ * PROP_RNG.uniform(112.0, 138.0)
            pick_ = _draw_seat()
            # From the lining: a chair turned as much as these are reaches 44 cm, a stool 27.
            x_, y_ = _prop_on(u, s_, PROP_RNG.uniform(46.0, 60.0) if pick_ == "chair" else PROP_RNG.uniform(30.0, 46.0))
            a_, b_ = at(u["x"], u["y"], u["side"], s_ - 30.0, 8.0), at(u["x"], u["y"], u["side"], s_ + 30.0, 80.0)
            box_ = (min(a_[0], b_[0]), min(a_[1], b_[1]), 0.0, max(a_[0], b_[0]), max(a_[1], b_[1]), 110.0)
            lining_ = all(_on_floor(*at(u["x"], u["y"], u["side"], s_ + e_, FLOOR_OUT - 2.0)) and not _on_floor(*at(u["x"], u["y"], u["side"], s_ + e_, FLOOR_OUT + 2.0)) for e_ in (-30.0, 30.0))
            # _poster_clear, not _free: an overhanging room's claim runs the whole height of its rectangle, and a seat stands fine under one.
            if not lining_ or not _ground_open(u, s_, 130.0) or not _poster_clear(box_) or not _pipe_free(u, s_ - 30.0, s_ + 30.0) or not _stair_clear(u, s_ - 30.0, s_ + 30.0, 0.0):
                continue
            if any(math.hypot(x_ - o_[0], y_ - o_[1]) < 80.0 for o_ in _prop_done + _lt_done) or any(math.hypot(x_ - o_[0], y_ - o_[1]) < 130.0 for o_ in _prop_tables) or any(math.hypot(x_ - o_[0], y_ - o_[1]) < 100.0 for o_ in _posts) or any(math.hypot(x_ - o_[0], y_ - o_[1]) < 200.0 for o_ in _prop_keep):
                continue
            if pick_ == "square":
                placed_ = _prop("Prop_DoorSeat_%d_%d" % (k_, j_), MB_STOOL2, x_, y_, YAW[u["side"]] + PROP_RNG.uniform(-30.0, 30.0), "stool", look=_mono_look(MB_STOOL2), surface="Plastic", fit=(19.0, 19.0), kg=PROP_KG[MB_STOOL2])
            elif pick_ == "chair":
                placed_ = _prop("Prop_DoorSeat_%d_%d" % (k_, j_), MB_CHAIR, x_, y_, YAW[u["side"]] + 180.0 + PROP_RNG.uniform(-42.0, 42.0), "chair", look=_mono_look(MB_CHAIR, PROP_RNG.choice(MB_CHAIR_MATS)), surface="Plastic", draw=CULL_MID, fit=(29.0, 33.0), kg=PROP_KG[MB_CHAIR])
            else:
                placed_ = _prop("Prop_DoorSeat_%d_%d" % (k_, j_), MB_STOOL1, x_, y_, PROP_RNG.uniform(0.0, 360.0), "stool", look=_mono_look(MB_STOOL1, PROP_RNG.choice(MB_STOOL_MATS)), surface="Plastic", fit=(20.0, 20.0), kg=PROP_KG[MB_STOOL1])
            if not placed_:
                continue
            _prop_done.append((x_, y_))
            if PROP_RNG.random() > 0.22:
                break
    # Wooden benches along walls. A stool now and then.
    for k_ in range(7):
        c_ = _prop_take(480.0, 150.0, 140.0, near_door=PROP_RNG.random() < 0.3)
        if c_ is None:
            continue
        u = c_["u"]
        length = min(PROP_RNG.uniform(120.0, 172.0), c_["hi"] - c_["lo"] - 6.0)
        s_ = PROP_RNG.uniform(c_["lo"] + length / 2 + 3.0, max(c_["lo"] + length / 2 + 3.5, c_["hi"] - length / 2 - 3.0))
        x_, y_ = _prop_on(u, s_, 23.0)
        _prop("Prop_Bench_%d" % k_, WOOD_BENCH, x_, y_, YAW[u["side"]] + PROP_RNG.uniform(-2.0, 2.0), "bench", (length / 214.0, 0.28, 0.47), surface="Wood", draw=CULL_MID, fit=(length / 2.0, 16.5))
    for k_ in range(6):
        c_ = _prop_take(560.0, 130.0, 70.0)
        if c_ is None:
            continue
        u = c_["u"]
        x_, y_ = _prop_on(u, (c_["lo"] + c_["hi"]) / 2 + PROP_RNG.uniform(-12.0, 12.0), PROP_RNG.uniform(22.0, 40.0))
        _prop("Prop_WoodStool_%d" % k_, WOOD_BENCH, x_, y_, YAW[u["side"]] + PROP_RNG.uniform(-14.0, 14.0), "wood stool", (0.25, 0.3, 0.46), surface="Wood", fit=(27.0, 17.5))
    # Two-seat monobloc benches, their backs to a wall.
    for k_ in range(3):
        c_ = _prop_take(500.0, 170.0, 136.0)
        if c_ is None:
            continue
        u = c_["u"]
        x_, y_ = _prop_on(u, (c_["lo"] + c_["hi"]) / 2, 42.0)
        _prop("Prop_MonoBench_%d" % k_, MB_BENCH, x_, y_, YAW[u["side"]] + 180.0 + PROP_RNG.uniform(-5.0, 5.0), "monobloc bench", look=_mono_look(MB_BENCH, PROP_RNG.choice(MB_BENCH_MATS)), surface="Plastic", draw=CULL_MID, fit=(65.0, 34.0), kg=PROP_KG[MB_BENCH])
    # Buckets: under a downpipe to catch the rain, and in ones and twos along walls, some with lids.
    for key_ in sorted(_gd_pipes):
        p = _gd_pipes[key_]
        side_ = next(k_ for k_, v_ in YAW.items() if abs((v_ - p["rot"][1]) % 360.0) < 1.0)
        nx, ny = NORMAL[side_]
        rx, ry = RUN[side_]
        # Clear of the pipe, in front of it: the pipe is 7.6 off the wall and about 6 across its half. It went into the rim before (user: "i saw a bucket overlapping pipes").
        asset_ = PROP_RNG.choice(PROP_BUCKETS)
        off_ = 6.0 + PROP_REACH[asset_] + 3.0
        along_ = PROP_RNG.uniform(-5.0, 5.0)
        x_, y_ = p["loc"][0] + nx * off_ + rx * along_, p["loc"][1] + ny * off_ + ry * along_
        if PROP_RNG.random() < 0.65 and not solid(_lay(x_, y_)[0], _lay(x_, y_)[1], 0) and not any(math.hypot(x_ - o_[0], y_ - o_[1]) < 130.0 for o_ in _prop_doors):
            _prop_bucket("Prop_PipeBucket_%s" % key_, x_, y_, asset=asset_)
    for k_ in range(14):
        c_ = _prop_take(240.0, 120.0, 60.0)
        if c_ is None:
            continue
        u = c_["u"]
        s_ = (c_["lo"] + c_["hi"]) / 2 + PROP_RNG.uniform(-14.0, 14.0)
        n_b = PROP_RNG.choice((1, 1, 2, 2, 3))
        for j_ in range(n_b):
            x_, y_ = _prop_on(u, s_ + (j_ - (n_b - 1) / 2) * PROP_RNG.uniform(38.0, 46.0), PROP_RNG.uniform(22.0, 30.0))
            asset = _prop_bucket("Prop_Bucket_%d_%d" % (k_, j_), x_, y_)
            if asset.endswith("SM_Bucket_01") and PROP_RNG.random() < 0.4:
                # Welded to its bucket, so they move as one: "weld them if they are separate pieces".
                _prop("Prop_Bucket_%d_%d_Lid" % (k_, j_), BK_DIR + "SM_Bucket_Lid_01", x_, y_, PROP_RNG.uniform(0.0, 360.0), "lid", z=_ground_top(x_, y_) + 39.2, surface="Plastic", weld_to="Prop_Bucket_%d_%d" % (k_, j_))

    # Potted plants on the balconies.
    _ter_pieces, _ter_posts = {}, {}
    _ter_side = {"N": "north", "S": "south", "E": "east", "W": "west"}
    for p in items:
        if p["folder"] != TER:
            continue
        lab_ = p["label"].split("_")
        if lab_[0] in ("ParapetCap", "Banister"):
            _ter_pieces.setdefault(lab_[1], []).append((p, _ter_side[lab_[2][0]]))
        elif lab_[0] == "Post":
            _ter_posts.setdefault(lab_[1], []).append((p["loc"][0], p["loc"][1]))
    _ter_clutter = [(p["loc"][0], p["loc"][1]) for p in items if p["folder"] in (DR_TANKS, DR_AERIALS)]
    _ter_used = []

    def _pot(label, x_, y_, z_, pot_key, k_pot, tall=None, tin=False, on_ledge=False):
        """A pot standing at z_, and a plant in it: tall is (plant, its scale) for a floor pot; a ledge pot most of the time gets a small one."""
        if tin:
            asset = ME + "Favela/SM_MetalBucket_02"
            h_, under_ = 35.0, 0.0
            surface_, kg_ = "Metal", POT_TIN_KG
        else:
            name = pot_key if PROP_RNG.random() < 0.5 else POT_TWIN[pot_key]
            asset = POT_DIR + name
            h_, _across, under_ = POT_SIZE[pot_key]
            surface_, kg_ = ("Clay" if name <= "05" else "Plastic"), POT_KG[pot_key]
        _prop(label, asset, x_, y_, PROP_RNG.uniform(0.0, 360.0), "pot", (k_pot, k_pot, k_pot), z=z_ + under_ * k_pot + 0.1, surface=surface_, kg=round(kg_ * k_pot ** 3, 1))
        if tall:
            plant, k_ = tall
        elif PROP_RNG.random() < 0.72 and on_ledge:
            plant, lo_, hi_ = PROP_RNG.choice(PLANT_SMALL)
            k_ = PROP_RNG.uniform(lo_, hi_)
        else:
            return
        _prop(label + "_Plant", plant, x_, y_, PROP_RNG.uniform(0.0, 360.0), "plant", (k_, k_, k_), z=z_ + (h_ - 4.0) * k_pot, weld_to=label)

    for bid in sorted(_ter_pieces):
        pieces_ = list(_ter_pieces[bid])
        PROP_RNG.shuffle(pieces_)
        for c_i in range(min(len(pieces_), PROP_RNG.choice((0, 1, 1, 2, 2, 3)))):
            p, side_ = pieces_[c_i]
            cap_ = p["label"].startswith("ParapetCap")
            rx, ry = RUN[side_]
            nx, ny = NORMAL[side_]
            run_len = abs(p["scale"][0]) * (150.0 if cap_ else 172.0)
            ledge = cap_ and PROP_RNG.random() < 0.68
            floor_z = BLOCKS[bid]["sh"] - 5.0 + FLOOR_H
            n_p = PROP_RNG.choice((1, 2, 2, 3))
            s_ = PROP_RNG.uniform(16.0, max(17.0, run_len * 0.6))
            for j_ in range(n_p):
                pot_key = PROP_RNG.choice(("04", "04", "02", "01", "03", "05"))
                k_pot = PROP_RNG.uniform(0.66, 0.76) if ledge else PROP_RNG.uniform(0.95, 1.15)
                across_ = POT_SIZE[pot_key][1] * k_pot
                if s_ + across_ / 2 > run_len - 6.0:
                    break
                # A plant on the floor reaches out as far as it's wide, and its low leaves went through the parapet (seen from outside, below the cap). So it stands its reach back from the wall's inner
                # face, 13 cm in from the cap's line, and goes without if it would still reach a wall of the terrace.
                tall_ = None
                reach_ = 0.0
                if not ledge and PROP_RNG.random() < 0.9:
                    plant_, lo_, hi_, r1_ = PROP_RNG.choice(PLANT_TALL)
                    k_pl = PROP_RNG.uniform(lo_, hi_)
                    tall_ = (plant_, k_pl)
                    reach_ = r1_ * k_pl
                back_ = 0.0 if ledge else max(35.0 if cap_ else 22.0, (13.0 if cap_ else 0.0) + reach_ + 4.0)
                x_, y_ = p["loc"][0] + rx * s_ - nx * back_, p["loc"][1] + ry * s_ - ny * back_
                if tall_:
                    b_ = BLOCKS[bid]
                    if not all(b_["x0"] + 0.12 < _lay(x_ + a2_ * reach_, y_ + b2_ * reach_)[0] < b_["x1"] - 0.12 and b_["y0"] + 0.12 < _lay(x_ + a2_ * reach_, y_ + b2_ * reach_)[1] < b_["y1"] - 0.12 for a2_, b2_ in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                        tall_ = None
                near_post = any(math.hypot(x_ - o_[0], y_ - o_[1]) < across_ / 2 + 12.0 for o_ in _ter_posts.get(bid, ()))
                near_tank = any(math.hypot(x_ - o_[0], y_ - o_[1]) < 80.0 for o_ in _ter_clutter)
                if not near_post and not near_tank:
                    _ter_used.append((x_, y_))
                    _pot("Prop_Pot_%s_%d_%d" % (bid, c_i, j_), x_, y_, p["loc"][2] + 8.0 if ledge else floor_z, pot_key, k_pot, tall_, tin=(not ledge) and PROP_RNG.random() < 0.18, on_ledge=ledge)
                s_ += across_ + PROP_RNG.uniform(5.0, 16.0)
    # Rice sacks, off the street and up on the balconies. User 2026-11-06: "move the ricebags to the secured balconies". On the floor by the rail or parapet, away from pots and posts: filled sacks standing, empty ones in a pile.
    SACK_DIR = PM + "RiceBags_01/SM_Rice_Bag_"
    _sack_lots = 0
    _ter_order = sorted(_ter_pieces)
    PROP_RNG.shuffle(_ter_order)
    for bid in _ter_order:
        if _sack_lots >= 9:
            break
        pieces_ = list(_ter_pieces[bid])
        PROP_RNG.shuffle(pieces_)
        # A banister shows the floor to the street, so those first.
        pieces_.sort(key=lambda q_: q_[0]["label"].startswith("ParapetCap"))
        p, side_ = pieces_[0]
        cap_ = p["label"].startswith("ParapetCap")
        rx, ry = RUN[side_]
        nx, ny = NORMAL[side_]
        run_len = abs(p["scale"][0]) * (150.0 if cap_ else 172.0)
        floor_z = BLOCKS[bid]["sh"] - 5.0 + FLOOR_H
        b_ = BLOCKS[bid]
        for _t in range(10):
            s_ = PROP_RNG.uniform(30.0, max(31.0, run_len - 30.0))
            back_ = (13.0 if cap_ else 0.0) + PROP_RNG.uniform(40.0, 52.0)
            x_, y_ = p["loc"][0] + rx * s_ - nx * back_, p["loc"][1] + ry * s_ - ny * back_
            inside_ = all(b_["x0"] + 0.42 < _lay(x_ + a2_ * 40.0, y_ + b2_ * 40.0)[0] < b_["x1"] - 0.42 + 0.42 and b_["y0"] + 0.0 < _lay(x_ + a2_ * 40.0, y_ + b2_ * 40.0)[1] < b_["y1"] for a2_, b2_ in ((1, 0), (-1, 0), (0, 1), (0, -1)))
            if inside_ and not any(math.hypot(x_ - o_[0], y_ - o_[1]) < 75.0 for o_ in _ter_used) and not any(math.hypot(x_ - o_[0], y_ - o_[1]) < 55.0 for o_ in _ter_posts.get(bid, ())) and not any(math.hypot(x_ - o_[0], y_ - o_[1]) < 95.0 for o_ in _ter_clutter):
                yaw_ = YAW[side_] + PROP_RNG.uniform(-14.0, 14.0)
                if PROP_RNG.random() < 0.5:
                    for j_ in range(PROP_RNG.choice((2, 3, 3, 4))):
                        _prop("Prop_Sack_%s_%d" % (bid, j_), SACK_DIR + "Flat_0%d" % PROP_RNG.choice((1, 2, 3, 4)), x_ + PROP_RNG.uniform(-5.0, 5.0), y_ + PROP_RNG.uniform(-5.0, 5.0), yaw_ + PROP_RNG.uniform(-9.0, 9.0), "sack", z=floor_z + 0.1 + j_ * 15.0)
                else:
                    for j_ in range(PROP_RNG.choice((1, 2, 2, 3))):
                        sx_, sy_ = x_ + rx * (j_ - 1) * 42.0, y_ + ry * (j_ - 1) * 42.0
                        _prop("Prop_Sack_%s_%d" % (bid, j_), SACK_DIR + PROP_RNG.choice(("Full_01", "Full_02", "HalfFull_01", "Straight_02", "Straight_03")), sx_, sy_, yaw_ + PROP_RNG.uniform(-20.0, 20.0), "sack", z=floor_z + 0.1)
                _ter_used.append((x_, y_))
                _sack_lots += 1
                break
    # Potted plants along the wall by doors, where there's room. User 2026-11-06: "put some potted plants along the wall near doors where you can". Past the door's frame and step, and past any seat, a plant standing off the wall by its reach.
    PLANT_DOOR = ((ME + "Favela/Plants/SM_Plant_23", 0.7, 0.95, 38.0), (ME + "Favela/Plants/SM_Plant_25", 0.7, 0.95, 40.0), (ME + "Favela/Plants/SM_Plant_26", 0.9, 1.2, 26.0), (ME + "Yakohama/SM_Plants_05", 0.8, 1.05, 38.0), (ME + "Favela/Plants/SM_Plant_27", 0.9, 1.2, 25.0), (ME + "Favela/Plants/SM_Plant_24", 0.8, 1.1, 32.0))
    _door_pot_tiles = list(_door_tiles)
    PROP_RNG.shuffle(_door_pot_tiles)
    for k_, u in enumerate(_door_pot_tiles):
        if PROP_RNG.random() > 0.72:
            continue
        centre_ = 112.5 * u["sx"]
        sides_ = [-1.0, 1.0]
        PROP_RNG.shuffle(sides_)
        for c_i, d_ in enumerate(sides_):
            s_ = centre_ + d_ * PROP_RNG.uniform(118.0, 150.0)
            placed_, want_, j_ = 0, PROP_RNG.choice((1, 1, 2, 2, 3)), 0
            # Walk along the wall from the door until they're down, up to about 3 m: the first spot past a frame is often a seat or a pipe.
            while placed_ < want_ and abs(s_ - centre_) < 320.0:
                j_ += 1
                pot_key = PROP_RNG.choice(("04", "01", "03", "02", "05"))
                k_pot = PROP_RNG.uniform(0.85, 1.05)
                across_ = POT_SIZE[pot_key][1] * k_pot
                plant_, lo_, hi_, r1_ = PROP_RNG.choice(PLANT_DOOR)
                k_pl = PROP_RNG.uniform(lo_, hi_)
                n_ = max(FLOOR_OUT + across_ / 2.0 + 3.0, r1_ * k_pl + 3.0) - FLOOR_OUT
                x_, y_ = _prop_on(u, s_, n_)
                a_, b_ = at(u["x"], u["y"], u["side"], s_ - across_ / 2, 8.0), at(u["x"], u["y"], u["side"], s_ + across_ / 2, FLOOR_OUT + n_ + across_ / 2)
                box_ = (min(a_[0], b_[0]), min(a_[1], b_[1]), 0.0, max(a_[0], b_[0]), max(a_[1], b_[1]), 90.0)
                lining_ = all(_on_floor(*at(u["x"], u["y"], u["side"], s_ + e_, FLOOR_OUT - 2.0)) and not _on_floor(*at(u["x"], u["y"], u["side"], s_ + e_, FLOOR_OUT + 2.0)) for e_ in (-across_ / 2, across_ / 2))
                clear_ = lining_ and _ground_open(u, s_, 110.0) and _poster_clear(box_) and _pipe_free(u, s_ - across_ / 2 - 5.0, s_ + across_ / 2 + 5.0) and _stair_clear(u, s_ - 20.0, s_ + 20.0, 0.0) and not \
                    any(math.hypot(x_ - o_[0], y_ - o_[1]) < across_ / 2 + 34.0 for o_ in _prop_done) and not any(math.hypot(x_ - o_[0], y_ - o_[1]) < 75.0 for o_ in _lt_done) and not \
                    any(math.hypot(x_ - o_[0], y_ - o_[1]) < 85.0 for o_ in _posts) and not any(math.hypot(x_ - o_[0], y_ - o_[1]) < 150.0 for o_ in _prop_keep) and not any(math.hypot(x_ - o_[0], y_ - o_[1]) < 105.0 for o_ in _prop_doors) and not \
                    any(math.hypot(x_ - o_[0], y_ - o_[1]) < 62.0 + r1_ * k_pl + 12.0 for o_ in _prop_tables) and not _in_doorway(x_, y_)
                if clear_:
                    _pot("Prop_DoorPot_%d_%d_%d" % (k_, c_i, j_), x_, y_, _ground_top(x_, y_), pot_key, k_pot, (plant_, k_pl), tin=PROP_RNG.random() < 0.14)
                    _prop_done.append((x_, y_))
                    placed_ += 1
                    s_ += d_ * (across_ + PROP_RNG.uniform(6.0, 18.0))
                else:
                    s_ += d_ * 24.0
            if placed_ and PROP_RNG.random() > 0.25:
                break
    # Garbage drums (user 2026-11-09: "For S1 and S2, Do a ground and object pass (garbage cans, buckets etc)"): the market pack's plastic drums, the street bins of a
    # Philippine barangay, at the foot of a wall in ones and twos, the stretches nearest the trash bags first, clear of doors, pipes, stairs and the rest. Static and solid:
    # unlike the furniture a pawn doesn't walk through one, and the nav mesh goes round it. A level asks for them (PROP_DRUMS); their own randoms, so nothing else moves.
    # Against plain walls only (under a window a drum's top went into the grille), on flat ground (by a curb's end one went into the curb), turned square to the wall: the
    # overlap test boxes a drum by its square bounds, and turned at random their corners swung into the house's lining. A drum is round, so it looks the same.
    PROP_DRUMS = getattr(LEVEL, "PROP_DRUMS", 0)
    DRUM_RNG = random.Random(337)
    DRUMS = (PM + "Barrels_Set_01/SM_Barrel_01", PM + "Barrels_Set_01/SM_Barrel_02")
    DRUM_R, DRUM_H = 32.0, 100.0
    if PROP_DRUMS:
        _bag_xy = [(p["loc"][0], p["loc"][1]) for p in items if p["folder"] == DR_LITTER and p["label"].startswith("Lt_Bag_")]
        _drum_spots = list(_lt_spots)
        DRUM_RNG.shuffle(_drum_spots)
        _drum_spots.sort(key=lambda c_: min([math.hypot(c_["x"] - b_[0], c_["y"] - b_[1]) for b_ in _bag_xy] or [0.0]) > 450.0)
        _drum_lots = []
        for c_ in _drum_spots:
            if len(_drum_lots) >= PROP_DRUMS:
                break
            u = c_["u"]
            if u["kind"] not in _plain_tile or any(math.hypot(c_["x"] - o_[0], c_["y"] - o_[1]) < 700.0 for o_ in _drum_lots):
                continue
            n_d = DRUM_RNG.choice((1, 1, 2))
            step_ = 2.0 * DRUM_R + 4.0
            width_ = n_d * step_
            if c_["hi"] - c_["lo"] < width_ + 10.0:
                continue
            s0_ = DRUM_RNG.uniform(c_["lo"] + 5.0, c_["hi"] - width_ - 5.0)
            pts_ = [_prop_on(u, s0_ + DRUM_R + 2.0 + i_ * step_, DRUM_R + 3.0) for i_ in range(n_d)]
            z0_ = max(_ground_top(*q_) for q_ in pts_)
            yaw_d = YAW[u["side"]] + 90.0 * DRUM_RNG.randint(0, 3)
            flat_ = all(abs(_ground_top(q_[0] + ex_, q_[1] + ey_) - z0_) < 0.5 for q_ in pts_
                        for ex_, ey_ in ((0.0, 0.0), (DRUM_R, DRUM_R), (DRUM_R, -DRUM_R), (-DRUM_R, DRUM_R), (-DRUM_R, -DRUM_R)))
            a_, b_ = at(u["x"], u["y"], u["side"], s0_, 8.0), at(u["x"], u["y"], u["side"], s0_ + width_, FLOOR_OUT + 2.0 * DRUM_R + 6.0)
            box_ = (min(a_[0], b_[0]), min(a_[1], b_[1]), z0_, max(a_[0], b_[0]), max(a_[1], b_[1]), z0_ + DRUM_H + 10.0)
            if not (flat_ and _ground_open(u, s0_ + width_ / 2.0, 110.0) and _free(box_, 1.0) and _pipe_free(u, s0_ - 5.0, s0_ + width_ + 5.0) and
                    _stair_clear(u, s0_, s0_ + width_, 0.0) and _poster_clear(box_) and
                    not any(_in_doorway(*q_) or any(math.hypot(q_[0] - d_[0], q_[1] - d_[1]) < 130.0 for d_ in _prop_doors) or
                            any(math.hypot(q_[0] - b_[0], q_[1] - b_[1]) < DRUM_R + 60.0 for b_ in _bag_xy) or
                            any(math.hypot(q_[0] - o_[0], q_[1] - o_[1]) < DRUM_R + 34.0 for o_ in _prop_done) or
                            not _prop_fits(q_[0], q_[1], yaw_d, DRUM_R, DRUM_R) for q_ in pts_)):
                continue
            for i_, (x_, y_) in enumerate(pts_):
                _prop("Prop_Drum_%d_%d" % (len(_drum_lots), i_), DRUM_RNG.choice(DRUMS), x_, y_, yaw_d, "drum", z=z0_ + 0.1,
                      surface="Plastic", draw=CULL_MID)
                # Solid (user 2026-11-09: "drums have no collisions"): a drum blocks a pawn as well as a shot, and the nav mesh goes round it.
                items[-1]["coll"] = "BlockAll"
                items[-1].pop("nonav", None)
                _prop_done.append((x_, y_))
            _claim(box_)
            _drum_lots.append((c_["x"], c_["y"]))
    # Physical pieces start clear of everything. User 2026-11-07: "make sure whatevr is a physical object does not overlap initially to any other object, i saw a bucket overlapping pipes earilier".
    # A body that starts inside another is thrown out of it on the first frame, and looks wrong before that. Every piece near the ground, its box from the measured mesh; what a physical piece touches, it loses.
    # Heights from the ground under a piece where a story level's ground has heights (story_ground_dress); from 0 in the arena, as before.
    _gz_ = _gt_hook if _gt_hook else (lambda x_, y_: 0.0)
    _near = [(p["label"], _piece_box(p)) for p in items if p["loc"][2] - _gz_(p["loc"][0], p["loc"][1]) < 300.0 and p["folder"] not in (DR_GROUND, DR_GROUND_DIRT)]
    _near = [(l_, b_) for l_, b_ in _near if b_ and b_[5] - _gz_(b_[0], b_[1]) < 160.0]
    # Static props too, at ground level: a filled bucket into a wall's end, a pot against a pole, look as wrong. A plant in its pot, a lid on its bucket, a cup on its table and a crate on a crate are meant.
    _phys_drop = set()
    # The physical trash bags are tested too. Loose litter with no collision lying under one (a flattened box, paper, a butt) is taken out, and the bag stays.
    _loose = {p["label"] for p in items if p["folder"] == DR_LITTER and p.get("nocoll")}
    _loose_off = set()
    # Physical pieces up off the street (pots on balcony ledges and floors) are tested too, against everything within 3 m of them.
    _all = [(p["label"], _piece_box(p)) for p in items if p["folder"] not in (DR_GROUND, DR_GROUND_DIRT)]
    _all = [(l_, b_) for l_, b_ in _all if b_]
    _high_drop = []
    for p in items:
        if p["folder"] != DR_PROPS and not (p["folder"] == DR_LITTER and p.get("physics")):
            continue
        box_ = _piece_box(p)
        if box_ is None:
            continue
        high_ = box_[5] - _gz_(box_[0], box_[1]) > 30.0
        if high_ and not (p.get("physics") or (p.get("weld_to") and not p["nocoll"])):
            continue
        pool_ = [(l_, b_) for l_, b_ in _all if abs(b_[0] - box_[0]) < 300.0 and abs(b_[1] - box_[1]) < 300.0] if high_ else _near
        mates = {p["label"], p.get("weld_to")} | {q_["label"] for q_ in items if q_.get("weld_to") == p["label"]}
        stem_ = p["label"].replace("_Plant", "").replace("_Lid", "")
        pot_ = "Pot_" in p["label"] and not p["label"].endswith("_Plant")
        for l_, b_ in pool_:
            if l_ in mates or l_ in _phys_drop or l_ in _loose_off or l_.startswith(stem_) or stem_.startswith(l_.replace("_Plant", "")):
                continue
            if pot_ and l_.endswith("_Plant"):
                continue        # a neighbour's leaves: no collision, and its box is far wider than the leaves. Pots stand in clusters.
            if _boxes_meet(box_, b_):
                if p["folder"] == DR_LITTER and l_ in _loose:
                    _loose_off.add(l_)
                    continue
                _phys_drop.add(p["label"])
                if high_:
                    _high_drop.append((p["label"], l_))
                break
    # What stood on or in a dropped piece goes with it.
    _phys_drop |= {p["label"] for p in items if p.get("weld_to") in _phys_drop or p["label"].replace("_Plant", "") in _phys_drop or p["label"].replace("_Lid", "") in _phys_drop}
    _bags_n = sum(1 for p in items if p["folder"] == DR_LITTER and p.get("physics"))
    _bags_drop = sum(1 for p in items if p["folder"] == DR_LITTER and p["label"] in _phys_drop)
    items[:] = [p for p in items if p["label"] not in _phys_drop and p["label"] not in _loose_off]
    _prop_n["dropped, touching something"] = len(_phys_drop) - _bags_drop
    print("physical bags: %d placed, %d dropped touching something, %d off their stretch; loose litter taken from under them: %d %s" % (
        _bags_n - _bags_drop, _bags_drop, _litter_n.get("bag off its stretch", 0), len(_loose_off), sorted(_loose_off)))
    print("physical pieces up off the street dropped, touching something: %d %s" % (len(_high_drop), _high_drop))
    print("props:", dict(sorted(_prop_n.items())), sum(v_ for k_, v_ in _prop_n.items() if not k_.startswith("dropped")))

