# Pass `story_road_clear` (story levels; 2026-11-09). User: "section 1 is a main road, it needs the power cables a bit higher. Trucks should be
# able to pass through". Over the main road's carriageway (the story_ground road panels; not the sidewalks, not the eskinitas) no wire hangs
# lower than ROAD_CLEAR over the road (a Philippine truck is up to about 4.3 m). The low layer (user 2026-11-05: across at the top of the ground
# floor, never under 3 m) dips to about 3 m there, so each wire bundle that does is lifted: its ends on a wall move up that wall (the box with
# them) until every wire of the bundle clears, a pole's end stays. The new spot has to be plain wall below the roof, past any window or door,
# clear of the wall's dressing and other boxes, and the wire must pass through no house. A bundle that can't be lifted comes out, with the boxes
# only it used. Run after every wire pass (street, low_wires, chain_wires, poles, asia_cables).
ROAD_CLEAR = getattr(LEVEL, "ROAD_CLEAR", None)
_rc_n = {"bundles too low": 0, "lifted": 0, "removed": 0, "boxes moved": 0, "boxes added": 0, "boxes removed": 0}

if ROAD_CLEAR:
    _rc_roads = []
    for p in items:
        if p["folder"] == GR and p["label"].startswith("Road_"):
            hx, hy = abs(p["scale"][0]) * 50.0, abs(p["scale"][1]) * 50.0
            _rc_roads.append((p["loc"][0] - hx, p["loc"][1] - hy, p["loc"][0] + hx, p["loc"][1] + hy, p["loc"][2]))

    def _rc_road_z(X, Y):
        r = next((r for r in _rc_roads if r[0] < X < r[2] and r[1] < Y < r[3]), None)
        return r[4] if r else None

    def _rc_curve(a3, b3, sag, n=40):
        return [(a3[0] + (b3[0] - a3[0]) * k / n, a3[1] + (b3[1] - a3[1]) * k / n,
                 a3[2] + (b3[2] - a3[2]) * k / n - 4.0 * sag * (k / n) * (1.0 - k / n)) for k in range(n + 1)]

    def _rc_short(a3, b3, sag):
        """How far under ROAD_CLEAR the wire hangs over the road at its worst (0: it clears)."""
        worst = 0.0
        for q in _rc_curve(a3, b3, sag):
            rz = _rc_road_z(q[0], q[1])
            if rz is not None:
                worst = max(worst, rz + ROAD_CLEAR - q[2])
        return worst

    # The wires, as rods: wire label -> its rods in order; a bundle is the wires of one label but the _W<j>.
    _rc_wires = {}
    for i_, p in enumerate(items):
        if p["folder"] == DR_WIRES and p["asset"] == CUBE:
            q = p["label"].rsplit("_", 1)
            if len(q) == 2 and q[1].isdigit():
                _rc_wires.setdefault(q[0], []).append((int(q[1]), i_))
    _rc_bundles = {}
    for w_ in _rc_wires:
        q = w_.rsplit("_", 1)
        key = q[0] if len(q) == 2 and q[1][:1] == "W" and q[1][1:].isdigit() else w_
        _rc_bundles.setdefault(key, []).append(w_)
    _rc_boxes = [i_ for i_, p in enumerate(items) if p["folder"] == DR_WIRES and p["asset"].endswith("SM_ElectricBox_C_002")]
    _rc_shape_memo = {}
    _rc_poles = [p["loc"] for p in items if p["folder"] == DR_POLES and "Electric_Pole" in p["asset"]]

    def _rc_shape(w_):
        """A wire's two ends and its sag, from its rods (street.py _wire: a parabola of thin boxes). The rods don't change in this pass
        (a lifted wire gets new ones; the old stay until the end), so each is worked out once."""
        if w_ in _rc_shape_memo:
            return _rc_shape_memo[w_]
        _rc_shape_memo[w_] = _rc_shape_raw(w_)
        return _rc_shape_memo[w_]

    def _rc_shape_raw(w_):
        rods = [items[i_] for k, i_ in sorted(_rc_wires[w_])]
        ends = [_rod_line(p) for p in rods]
        a3, b3 = ends[0][0], ends[-1][1]
        n = len(rods)
        j = ends[0][1]                                       # the first joint, at u = 1/n
        u_ = 1.0 / n
        lerp = a3[2] + (b3[2] - a3[2]) * u_
        sag = max(0.0, (lerp - j[2]) / (4.0 * u_ * (1.0 - u_))) if n > 1 else 0.0
        return a3, b3, sag, n, abs(rods[0]["scale"][1]) * 100.0, rods[0]["mats"][0], rods[0].get("draw")

    def _rc_box_at(e):
        return [i_ for i_ in _rc_boxes if math.hypot(items[i_]["loc"][0] - e[0], items[i_]["loc"][1] - e[1]) < 30.0 and
                abs(items[i_]["loc"][2] - e[2]) < 30.0]

    def _rc_on_pole(e):
        return any(math.hypot(e[0] - q[0], e[1] - q[1]) < 220.0 for q in _rc_poles)

    _rc_open = ("SM_Wall_Windows_01", "SM_WallDoor_01")

    def _rc_wall_ok(e, z_new):
        """A box's new spot on its wall at z_new: plain wall there (no opening), below the roof, clear of the wall's dressing."""
        for t in _wall_tiles:
            rx, ry = RUN[t["side"]]
            nx, ny = NORMAL[t["side"]]
            s_ = (e[0] - t["x"]) * rx + (e[1] - t["y"]) * ry
            n_ = (e[0] - t["x"]) * nx + (e[1] - t["y"]) * ny
            if not (-2.0 <= s_ <= t["w"] + 2.0 and -5.0 < n_ < 40.0):
                continue
            b = BLOCKS[t["bid"]]
            if not t["z"] <= z_new < t["z"] + b["sh"]:
                continue
            if FLOOR_H + b.get("z", 0.0) + b["storeys"] * b["sh"] - 40.0 < z_new:
                return False
            if t["kind"] in _rc_open and not _edge_ok(t, s_, 18.0):
                z0, z1 = (t["z"] - 5.0, t["z"] + 255.0) if t["kind"] == "SM_WallDoor_01" else (t["z"] + 80.0, t["z"] + 235.0)
                if z_new - 14.0 < z1 and z0 < z_new + 14.0:
                    return False
            box = (e[0] - 30.0, e[1] - 30.0, z_new - 14.0, e[0] + 30.0, e[1] + 30.0, z_new + 14.0)
            if not _free(box, 2.0):
                return False
            for p in items:
                if p["folder"] in (DR_LIGHTS, DR_SIGNS, "BackAlleys/Awnings", "BackAlleys/Cables", DR_METERS) and \
                        math.hypot(p["loc"][0] - e[0], p["loc"][1] - e[1]) < 60.0 and abs(p["loc"][2] - z_new) < 50.0:
                    return False
            return True
        return False                                         # not on a wall we know

    def _rc_path_ok(a3, b3, sag):
        for q in _rc_curve(a3, b3, sag, 24)[2:-2]:
            lx, ly = _lay(q[0], q[1])
            if cover_top(lx, ly) > q[2] - FLOOR_H - 10.0:
                return False
        return True

    _rc_drop = set()
    _rc_before = {id(p) for p in items}                  # what was there before this pass: the rest is new
    for key, ws in sorted(_rc_bundles.items()):
        shapes = {w_: _rc_shape(w_) for w_ in ws}
        if all(_rc_short(s_[0], s_[1], s_[2]) <= 0.0 for s_ in shapes.values()):
            continue
        _rc_n["bundles too low"] += 1
        # which ends may move: those on a wall (a box there), not at a pole
        movable = {w_: [not _rc_on_pole(e) and bool(_rc_box_at(e)) for e in (s_[0], s_[1])] for w_, s_ in shapes.items()}
        lifted = None
        for d_ in range(10, 310, 10):
            new = {}
            ok = True
            for w_, (a3, b3, sag, n, th, mat, draw) in shapes.items():
                ma, mb = movable[w_]
                a2 = (a3[0], a3[1], a3[2] + d_) if ma else a3
                b2 = (b3[0], b3[1], b3[2] + d_) if mb else b3
                if not (ma or mb) or _rc_short(a2, b2, sag) > 0.0 or not _rc_path_ok(a2, b2, sag):
                    ok = False
                    break
                new[w_] = (a2, b2)
            if not ok:
                continue
            spots = {}
            for w_, (a3, b3, sag, n, th, mat, draw) in shapes.items():
                for e, m in ((a3, movable[w_][0]), (b3, movable[w_][1])):
                    if m:
                        spots[(round(e[0]), round(e[1]), round(e[2]))] = e
            if all(_rc_wall_ok(e, e[2] + d_) for e in spots.values()):
                lifted = (d_, new)
                break
        old_rods = [i_ for w_ in ws for k, i_ in _rc_wires[w_]]
        ends = [e for s_ in shapes.values() for e in (s_[0], s_[1])]
        if lifted is None:
            _rc_drop.update(old_rods)
            for e in ends:
                for bi in _rc_box_at(e):
                    others = [w2 for w2 in _rc_wires if w2 not in ws and any(math.dist(items[bi]["loc"], q) < 40.0 for q in _rc_shape(w2)[:2])]
                    if not others:
                        _rc_drop.add(bi)
            _rc_n["removed"] += 1
            continue
        d_, new = lifted
        _rc_drop.update(old_rods)
        for w_, (a2, b2) in new.items():
            a3, b3, sag, n, th, mat, draw = shapes[w_]
            pts = _rc_curve(a2, b2, sag, n)
            for k in range(n):
                _rod("%s_%d" % (w_, k), pts[k], pts[k + 1], th, mat, DR_WIRES, draw or CULL_FAR)
        # the boxes at the lifted ends: moved up with them, or, where another wire still uses one, a new box above it
        moved = set()
        for w_ in ws:
            a3, b3 = shapes[w_][0], shapes[w_][1]
            for e, m in ((a3, movable[w_][0]), (b3, movable[w_][1])):
                if not m:
                    continue
                for bi in _rc_box_at(e):
                    if bi in moved:
                        continue
                    moved.add(bi)
                    others = [w2 for w2 in _rc_wires if w2 not in ws and any(math.dist(items[bi]["loc"], q) < 40.0 for q in _rc_shape(w2)[:2])]
                    if others:
                        p2 = dict(items[bi], label=items[bi]["label"] + "_Up", loc=[items[bi]["loc"][0], items[bi]["loc"][1], items[bi]["loc"][2] + d_],
                                  rot=list(items[bi]["rot"]), scale=list(items[bi]["scale"]))
                        items.append(p2)
                        _rc_n["boxes added"] += 1
                    else:
                        items[bi]["loc"][2] = round(items[bi]["loc"][2] + d_, 1)
                        items[bi]["_rc_moved"] = True
                        _rc_n["boxes moved"] += 1
        _rc_n["lifted"] += 1
    _rc_n["boxes removed"] = sum(1 for i_ in _rc_drop if items[i_]["asset"].endswith("SM_ElectricBox_C_002"))
    _rc_gone = {items[i_]["label"] for i_ in _rc_drop}
    items[:] = [p for i_, p in enumerate(items) if i_ not in _rc_drop]

    # As many spans again one storey up, so the main road keeps its wires: the street pass's own span (_try_span) from a second-floor wall
    # that faces the road, to the second floor across (it spans only between two-storey houses, at their upper band, about 6.7-7.6 m).
    _rc_n["spans added"] = 0
    _rc_ts = [u for u in _wall_tiles if u["s"] == 1 and BLOCKS[u["bid"]]["storeys"] >= 2 and not BLOCKS[u["bid"]].get("balcony") and
              not _hollow_face(u) and u["w"] >= 100.0 and _rc_road_z(*at(u["x"], u["y"], u["side"], u["w"] / 2, 260.0)) is not None]
    WIRE_RNG.shuffle(_rc_ts)
    _rc_n["upper walls on the road"] = len(_rc_ts)
    _rc_n["span misses"] = {}
    for u in _rc_ts:
        if _rc_n["spans added"] >= _rc_n["removed"]:
            break
        spots = [24.0 + k * 30.0 for k in range(int((u["w"] - 48.0) // 30.0) + 1)]
        WIRE_RNG.shuffle(spots)
        z_a = _band_z(BLOCKS[u["bid"]], 1)
        n_a = _band_out(u) + 10.0
        for s_ in spots:                                    # a few spots along the wall; the first that spans the road
            if not _ground_open(u, s_, 70.0) or not _pipe_free(u, s_ - 16.0, s_ + 16.0) or                     not _free(_wbox(u, s_ - 16.0, s_ + 16.0, z_a - 12.0, z_a + 12.0), 2.0):
                _rc_n["span misses"]["wall"] = _rc_n["span misses"].get("wall", 0) + 1
                continue
            n0 = len(items)
            if not _try_span(u, s_, z_a, n_a, "SpanR_" + u["label"]):
                _rc_n["span misses"]["no way across"] = _rc_n["span misses"].get("no way across", 0) + 1
                continue
            if any(_rc_short(*_rod_line(p), 0.0) > 0.0 for p in items[n0:] if p["asset"] == CUBE):    # each rod as it hangs
                del items[n0:]
                _span_mids.pop()
                _rc_n["span misses"]["low"] = _rc_n["span misses"].get("low", 0) + 1
                continue
            Xb, Yb = at(u["x"], u["y"], u["side"], s_, _band_out(u))
            _box_on_wall("SpanR_%s_Box" % u["label"], Xb, Yb, z_a, YAW[u["side"]])
            _claim(_wbox(u, s_ - 16.0, s_ + 16.0, z_a - 12.0, z_a + 12.0))
            _rc_n["spans added"] += 1
            break
    # What changed, by label, for patching a map that already has the wires (Saved/<level>/road_clear.json): the pieces gone, and
    # the pieces to place or move (a lifted wire keeps its rods' labels, so those are in both lists).
    _rc_new = [p["label"] for p in items if id(p) not in _rc_before] + [p["label"] for p in items if p["folder"] == DR_WIRES and
                                                                         p["asset"].endswith("SM_ElectricBox_C_002") and p.get("_rc_moved")]
    for p in items:
        p.pop("_rc_moved", None)
    json.dump({"gone": sorted(_rc_gone), "place": sorted(set(_rc_new))}, open(OUT + "road_clear.json", "w"), indent=1)     # not <prefix>*: write_plan clears those
    print("road clearance (%.0f cm over the main road):" % ROAD_CLEAR, _rc_n)
