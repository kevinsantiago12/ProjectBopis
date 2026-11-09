# Pass `street`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Street dressing: wires, meters, tanks, aerials, lights, fronts, details.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
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


def _index_blocks():
    """BLOCKS on a 1 m grid (layout metres): each cell lists the blocks over it in BLOCKS' own order (2026-11-09: the rays across
    the street scanned every block at every 5 cm step)."""
    g = {}
    for b_ in BLOCKS.values():
        for i in range(math.floor(b_["x0"]), math.floor(b_["x1"]) + 1):
            for j in range(math.floor(b_["y0"]), math.floor(b_["y1"]) + 1):
                g.setdefault((i, j), []).append(b_)
    return g


_block_grid = _index_blocks()


def _block_at(lx, ly, pred=None):
    """The first block, in BLOCKS' order, with (lx, ly) strictly inside it (and pred(block) if given): what
    next(b for b in BLOCKS.values() if ...) gives, without the scan."""
    for b_ in _block_grid.get((math.floor(lx), math.floor(ly)), ()):
        if b_["x0"] < lx < b_["x1"] and b_["y0"] < ly < b_["y1"] and (pred is None or pred(b_)):
            return b_
    return None


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


class _OccList(list):
    """The claimed boxes (cm: x0, y0, z0, x1, y1, z1): a list, as before, that also keeps them on a CELL cm grid as they're added, so a
    test looks only at the boxes near it (2026-11-09: _free and the posters' test scanned every box, 10 million times an arena run).
    Every way the passes add to it (append, +=, extend) goes through append."""
    CELL = 250.0

    def __init__(self, it=()):
        super().__init__()
        self.grid = {}
        self.extend(it)

    def append(self, o):
        super().append(o)
        k = len(self) - 1
        for c_ in self._cells(o[0], o[1], o[3], o[4]):
            self.grid.setdefault(c_, []).append(k)

    def extend(self, it):
        for o in it:
            self.append(o)

    def __iadd__(self, it):
        self.extend(it)
        return self

    def _cells(self, x0, y0, x1, y1):
        c = self.CELL
        return [(i, j) for i in range(math.floor(x0 / c), math.floor(x1 / c) + 1) for j in range(math.floor(y0 / c), math.floor(y1 / c) + 1)]

    def near(self, box, pad):
        """The boxes whose cells meet box, grown by pad: every box that could touch it (and some that don't)."""
        ks = set()
        for c_ in self._cells(box[0] - pad, box[1] - pad, box[3] + pad, box[4] + pad):
            ks.update(self.grid.get(c_, ()))
        return [self[k] for k in sorted(ks)]


_occ = _OccList(b_ for b_ in (_occ_of(p) for p in items if p["folder"] in (DR_PATCH, DR_VENT, DR_ACS, DR_PIPES, DR_LAUNDRY)) if b_)
_occ += [(o[0], o[1], 0.0, o[2], o[3], 3000.0) for o in _room_rects]


def _wbox(t, s0, s1, z0, z1, n1=30.0):
    a_, b_ = at(t["x"], t["y"], t["side"], s0, -2.0), at(t["x"], t["y"], t["side"], s1, n1)
    return (min(a_[0], b_[0]), min(a_[1], b_[1]), z0, max(a_[0], b_[0]), max(a_[1], b_[1]), z1)


def _free(box, pad=6.0):
    return not any(box[0] - pad < o[3] and o[0] < box[3] + pad and box[1] - pad < o[4] and o[1] < box[4] + pad and
                   box[2] - pad < o[5] and o[2] < box[5] + pad for o in _occ.near(box, pad))


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


GATE_TOUCH = 0.3      # cm the gate's frame goes into the wall: touching, with no coincident faces


def _gate(label, u, s0, sa, sz):
    """SM_Metal_Gate_01, s0..s0 + 165.8*sa along the wall. X -1.7..164.1 along, Y -7.6..4.2, Z 0..241. Its plain sheet is on local -Y and its frame and
    rail on +Y (renders a and b). A sheet-steel gate shows the sheet to the street and keeps the frame inside, against the wall. User 2026-11-07, of a
    gate hung frame-out and 8 cm off the wall on its sheet: "this door is backwards and not in contact with the wall". So: turned 180, the pivot at
    the far end, the frame's edge GATE_TOUCH into the wall face."""
    x_, y_ = at(u["x"], u["y"], u["side"], s0 + 164.1 * sa, 4.2 - GATE_TOUCH)
    put(label, FV + "SM_Metal_Gate_01", x_, y_, u["z"] + 2.0, YAW[u["side"]] + 180.0, (sa, 1.0, sz), folder=DR_GATES)
    _cheap(CULL_FAR)


# Lettered boards. User 2026-11-07: "Project_Bopis_Local_Business_Signs Added ... then add the signage to the apprpriate signboards". Five painted boards, each
# once: the shops (sari-sari, xerox, carinderia) over a shutter, and the barber and the tailor, who work from home, over a house door. The other signs stay
# blank. Each image is 1850 x 500, the board in the middle: its columns here and in create_sign_boards_ue.py (the material crops to them). The sign is sized
# to its board, never stretched: the front panel is 291.4 x 78.6 of the mesh's 300 x 84 (SIGN_PANEL_K), and the sign only ever gets smaller, inside what
# it claimed.
SIGN_BOARDS = {"06_Sari_Sari": ("shop", 232, 1617), "07_Barberya": ("home", 174, 1674), "08_Patahian": ("home", 230, 1620),
               "09_Xerox": ("shop", 254, 1594), "10_Carinderia": ("shop", 252, 1597)}
SIGN_PANEL_K = (291.4 / 300.0) / (78.6 / 84.0)
SIGN_RNG = random.Random(337)                      # its own: drawing from FRONT_RNG would move everything placed after the signs
_boards_left = {k: sorted(n for n, v in SIGN_BOARDS.items() if v[0] == k) for k in ("shop", "home")}
for _k in sorted(_boards_left):
    SIGN_RNG.shuffle(_boards_left[_k])


def _board_aspect(name):
    _, x0, x1 = SIGN_BOARDS[name]
    return (x1 - x0 + 1 - 4.0) / 498.0             # the material's crop: 2 px in from each cut, 1 from top and bottom


def _next_board(kind):
    return _boards_left[kind].pop() if _boards_left[kind] else None


SIGN_BLOCKERS = ("BackAlleys/Awnings", "BackAlleys/Rooms", "BackAlleys/Tarps", "BackAlleys/WallACs")


def _sign_seen(t, s_mid, width, z_low, kind_h):
    """Nothing standing out in front of a sign. The first barber's board went over a door whose neighbour's awning stood 1.1 m out, across half of it
    (2026-11-07 capture): a lettered board only goes where it can be read."""
    cx_, cy_ = at(t["x"], t["y"], t["side"], s_mid, 0.0)
    (rx_, ry_), (nx_, ny_) = RUN[t["side"]], NORMAL[t["side"]]
    for p in items:
        if p["folder"] not in SIGN_BLOCKERS:
            continue
        dx_, dy_ = p["loc"][0] - cx_, p["loc"][1] - cy_
        if abs(dx_ * rx_ + dy_ * ry_) < width / 2 + 100.0 and 40.0 < dx_ * nx_ + dy_ * ny_ < 320.0 and z_low - 160.0 < p["loc"][2] < z_low + kind_h + 40.0:
            return False
    return True


def _sign_board(label, t, s_mid, width, z_low, kind_h, board=None):
    """SM_Sign_A_001: centred pivot, 300 x 84, 13 thick. Over the trim, and over a protruding band if there is one. Always long: user, "square
    signage may fit chinese characters but not alphanumerics". A lettered board (SIGN_BOARDS) takes its image's shape, and is seen from further off."""
    nat_w, nat_h = 300.0, 84.0
    kind_h = min(kind_h, width / SIGN_LONG)
    paint = _draw_sign()                           # drawn for every sign, so the draws after it stay put
    if board:
        a_ = _board_aspect(board)
        if width * SIGN_PANEL_K / kind_h > a_:
            width = kind_h * a_ / SIGN_PANEL_K
        else:
            kind_h = width * SIGN_PANEL_K / a_
        paint = BM + "MI_BackAlleys_SignBoard_" + board
    x_, y_ = at(t["x"], t["y"], t["side"], s_mid, 14.0 + _band_out(t))
    put(label, AS + "SM_Sign_A_001", x_, y_, z_low + kind_h / 2, YAW[t["side"]], (width / nat_w, 1.0, kind_h / nat_h), folder=DR_SIGNS, nocoll=True,
        mats=[paint, AM + "MI_MetalFrame_A_001_Black"])
    _cheap(CULL_FAR if board else CULL_MID)


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
            sign_w = wid + FRONT_RNG.uniform(-8.0, 12.0)
            _sign_board("Sign_" + u["label"], u, s0 + wid / 2, sign_w, u["z"] + 290.0, sign_h,
                        _next_board("shop") if _sign_seen(u, s0 + wid / 2, sign_w, u["z"] + 290.0, sign_h) else None)
            _shops.append((u, s0, wid))
            _n_sh += 1
            _count("shutters")
        elif kind == "gate":
            sa = min(1.0, (room_ - 4.0) / 165.8, (w_ - 30.0) / 165.8)
            s0 = (in0 + in1 - 165.8 * sa) / 2
            _gate("Gate_" + u["label"], u, s0, sa, 1.0)
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
        _gate("Gate_" + u["label"], u, 111.0 * u["sx"] - 82.9 * sa, sa, 232.0 / 240.7)
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
        _sign_board("WallSign_" + u["label"], u, s_mid, wid, z_, h_,
                    _next_board("home") if u["kind"] == "SM_WallDoor_01" and _sign_seen(u, s_mid, wid, z_, h_) else None)
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
        if not (W0 < lx < W and H0 < ly < H) or _in_room(X_, Y_) or not _clear_of_end_walls(lx, ly, 0.3):
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
    return FLOOR_H + b.get("z", 0.0) + st * b["sh"] + 300.0 + WIRE_RNG.uniform(0.3, 0.7) * (b["sh"] - 300.0)     # from the house's own ground


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
            if not (W0 < lx < W and H0 < ly < H):
                break
            o = _block_at(lx, ly, lambda b_: b_["storeys"] > 1)
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


STREET_LIGHTS_ON = getattr(LEVEL, "STREET_LIGHTS_ON", False)    # (a level may light them: a night level) user: "I will keep this level on daylight so the lights should be off". The fittings stay, unlit, with no light actors. True for a night version.


# Fill (user 2026-11-09): "rule on directional lights, always put a point light that is shadowless, like ambient light around the source, light
# never just travels in one direction", "bonus if you can have it cast shadow but very very mild". Every spot light gets a point light under its
# head: FILL_SHARE of its intensity, FILL_REACH of its radius, and a FILL_SOURCE cm source, so the shadows it casts are very soft, and faint
# at that brightness. FILL_BELOW cm under the fitting, so the lamp's own housing doesn't block it.
FILL_SHARE, FILL_REACH, FILL_SOURCE, FILL_BELOW = 0.12, 0.5, 40.0, 25.0


def _light(label, kind, x_, y_, z_, intensity, radius, colour, src=4.0, pitch=0.0, outer=60.0, length=0.0):
    if not STREET_LIGHTS_ON:
        return
    put(label, "/Script/Engine.%s" % kind, x_, y_, z_, 0.0, (1, 1, 1), folder=DR_LIGHTS)
    items[-1]["rot"][0] = pitch
    items[-1]["light"] = {"kind": kind, "intensity": intensity, "radius": radius, "colour": colour, "source": src, "outer": outer, "length": length}
    if kind == "SpotLight":
        put(label + "_Fill", "/Script/Engine.PointLight", x_, y_, z_ - FILL_BELOW, 0.0, (1, 1, 1), folder=DR_LIGHTS)
        items[-1]["light"] = {"kind": "PointLight", "intensity": intensity * FILL_SHARE, "radius": radius * FILL_REACH, "colour": colour,
                              "source": FILL_SOURCE, "outer": 0.0, "length": 0.0, "fill": True}


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

