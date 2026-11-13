# Pass `building_dressing`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Building dressing on blank tiles: rooms, downpipes, air conditioners, patches, vents, steps, laundry.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
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
    return lay(X, Y)


def _ground_open(t, s_, n_):
    """Open ground (no house at any height) in front of tile t, s_ cm along it and n_ cm out."""
    lx, ly = _lay(*at(t["x"], t["y"], t["side"], s_, n_))
    return W0 < lx < W and H0 < ly < H and cover_top(lx, ly, BLOCKS[t["bid"]]) <= 0


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
            if not ok or not (W0 < lx < W and H0 < ly < H) or cover_top(lx, ly, b) > 0 or not awn_clear(lx, ly, 100.0, bid):
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
# The patches keep their own plywood: the user's plywood texture is for plywood walls only (2026-11-13: "keep the patches as they are.
# The one I added is for actually plywood walls").
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
                             (x_, y_, t0["z"] + bot + h_p / 2), mats=[mi])
                    _n_patch["ply"] += 1
                else:
                    tilt = PATCH_RNG.uniform(-1.0, 1.0)
                    X3, up3 = v_rot(run3, out3, tilt), v_rot((0.0, 0.0, 1.0), out3, tilt)
                    h_p = PATCH_RNG.uniform(min(180.0, PATCH_TOP - bot - 12.0), PATCH_TOP - bot)
                    x_, y_ = at(t0["x"], t0["y"], side, s_ + w_s / 2, 1.0 + PLATE_T / 2 + 1.5 * k_)
                    top3 = v_add((x_, y_, t0["z"] + bot + h_p / 2), up3, h_p / 2)
                    put_axes(label, PATCH_RNG.choice(AWN_PLATES), X3, out3, up3, (w_s / PLATE_W, 1.0, h_p / 164.9), (0.0, 0.0, 0.0), top3,
                             mats=[mi])
                    _n_patch["tin"] += 1
                items[-1]["folder"] = DR_PATCH
                # Shots stop on the sheet and play its own surface, not the wall's behind it (user 2026-11-07: "the sheet metals and wood on the walls are not playing the
                # correct impact"). Pawns pass, as with furniture: the sheets stand 1-2 cm off the wall, and their edges shouldn't snag anyone.
                items[-1].update({"coll": "IgnoreOnlyPawn", "phys": PHYS + ("Wood" if mi in PLY else "Metal"), "nonav": True})
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
for _ in range(60 if "arena_gallery" in LEVEL.PASSES else 0):    # only a level with the gallery deck has its rail
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
        if not (W0 < lx < W and H0 < ly < H) or cover_top(lx, ly, me) > 0 or \
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

