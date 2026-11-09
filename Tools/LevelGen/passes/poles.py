# Pass `poles`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Power poles and their lines, roof tyres, water meters.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
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
    _pole_rod_grid = {}                     # by the 4 m cell of each end: a rod only matters to a pole within 4 m of an end (2026-11-09)
    for k_, (r0, r1) in enumerate(_pole_rods):
        for e_ in (r0, r1):
            _pole_rod_grid.setdefault((math.floor(e_[0] / 400.0), math.floor(e_[1] / 400.0)), set()).add(k_)

    def _rods_near(x_, y_):
        i0, j0 = math.floor(x_ / 400.0), math.floor(y_ / 400.0)
        ks = set()
        for i in (i0 - 1, i0, i0 + 1):
            for j in (j0 - 1, j0, j0 + 1):
                ks |= _pole_rod_grid.get((i, j), set())
        return [_pole_rods[k_] for k_ in sorted(ks)]
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
            if not (W0 < lx < W and H0 < ly < H):
                return False
            for o in _blocks_near(lx, ly, 0.1):
                if o["x0"] - 0.1 < lx < o["x1"] + 0.1 and o["y0"] - 0.1 < ly < o["y1"] + 0.1 and \
                        o["storeys"] * o["sh"] + FLOOR_H + {"terrace": 330.0, "metal": 120.0}.get(o["roof"], 70.0) > z_:
                    return False
        return True

    def _pole_fit(u, s_, kind, turned):
        k_ = POLE_KINDS[kind]
        side, n_ = u["side"], k_["n"]
        x_, y_ = at(u["x"], u["y"], side, s_, n_)
        lx, ly = _lay(x_, y_)
        if not (W0 < lx < W and H0 < ly < H) or cover_top(lx, ly) > 0 or not _clear_of_end_walls(lx, ly, 1.5) or _over_deck(lx, ly):
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
            if not (W0 < lx2 < W and H0 < ly2 < H) or cover_top(lx2, ly2) > 0 or not _clear_of_end_walls(lx2, ly2, 0.1):
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
        for r0, r1 in _rods_near(x_, y_):
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
                if not (W0 < lx < W and H0 < ly < H) or cover_top(lx, ly) > 0:
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

