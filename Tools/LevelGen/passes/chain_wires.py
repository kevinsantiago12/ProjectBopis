# Pass `chain_wires`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Chained power lines.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
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
_block_grid = _index_blocks()       # (street.py) the blocks as they are now


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
        n_["block"] = _block_at(lx, ly)
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
                if not (W0 < lx < W and H0 < ly < H):
                    break
                o = _block_at(lx, ly)
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

