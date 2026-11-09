# Pass `low_wires`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Low wires across the alleys at the top of the ground floor.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# Low wires. User 2026-11-05: "add more power lines, power lines are a big identity show for the philippines", with a photo of a Manila alley: bundles
# hanging low across it, slanting down over the walls. The spans above sit at the second floor, and from the ground, in three shots at the busiest
# spots, looking 22 degrees up, none was in frame. So a second layer: across the alley at the top of the ground floor, some climbing to the second
# floor opposite, and bundles slanting down a wall from a box up high to a box low down. Never under LOW_FLOOR, clear of awnings, signs and doors
# below it, and only over the gallery or its stairs if high enough to walk under. Its own random sequence, so nothing above moves.
STREET_LOW_WIRES = True
LOW_RNG = random.Random(223)
LOW_SPANS, LOW_DRAPES = 28, 16
LOW_FLOOR, DECK_CLEAR, P_LOW_CLIMB = 300.0, 620.0, 0.35
_block_grid = _index_blocks()       # (street.py) the blocks as they are now
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
        if not (W0 < lx < W and H0 < ly < H) or _in_room(X_, Y_) or not _clear_of_end_walls(lx, ly, 0.3) or (Z_ < DECK_CLEAR and _over_deck(lx, ly)):
            return False
        for o in BLOCKS.values():
            if o["x0"] < lx < o["x1"] and o["y0"] < ly < o["y1"]:
                if o is me or o is other or o["storeys"] * o["sh"] + FLOOR_H + {"terrace": 330.0, "metal": 260.0}.get(o["roof"], 70.0) > Z_:
                    return False
    return True


def _ground_band_z(b):
    return FLOOR_H + b.get("z", 0.0) + 300.0 + LOW_RNG.uniform(0.25, 0.75) * (b["sh"] - 300.0)     # from the house's own ground


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
            if not (W0 < lx < W and H0 < ly < H):
                break
            o = _block_at(lx, ly)
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


