# Pass `asia_cables` (story levels; 2026-11-09). AsiaSlum's cable meshes where they fit better than the generated thin wires, which all
# stay (user: "see if the asian slum cables is usable instead of mass dropping the current small wires", "dont eliminate using the current
# ones, I just think those fit better in some instances", "go and build it"). As Demomap_AsiaSlum uses them:
# - facade runs: SM_Cable_B_001 / B_003 bundles (4 m of about 8 cables, 45 / 18 cm of sag) hung along a slum house's top storey from
#   SM_Cable_C_001 ring brackets, about every 4 m, under the lid and over the windows, chained to the next house where the line is clear;
# - across the street: a bundle stretched from a ring on one house to a ring on the house opposite;
# - drops: SM_Cable_D_001 (a straight round cable) from a run down or up to a junction box on the same wall;
# - trunks: one bundle from pole to pole under the pole line's wires.
# Shapes measured from the pack's FBX (ASCII; GeometricTranslation 200 along X): a bundle runs local X 0..401 from its pivot, ends level,
# centre line 10 cm off the pivot along local -Y; the ring's centre hangs 47 cm under its plate (local -Z), its axis along local X; the drop
# cable runs local X 0..200, 2 cm round. Corner pieces (B_002 / B_004) bend about 60 degrees over a metre: no fit for a 90-degree house
# corner at a 43 cm stand-off, so not used. Needs: the street pass (_run_tiles, _occ_of, _wire_nodes, _hollow_face, _thin_blocks), poles.
ASIA_CABLES = getattr(LEVEL, "ASIA_CABLES", False)
DR_CABLES = "BackAlleys/Cables"
CAB_RNG = random.Random(277)
CAB_BUNDLES = ((AS + "SM_Cable_B_001", 45.0), (AS + "SM_Cable_B_003", 18.0))      # mesh, its sag (cm) at scale 1
CAB_B_LEN, CAB_B_Y = 401.0, -10.0
CAB_RING, CAB_RING_K, CAB_RING_DROP = AS + "SM_Cable_C_001", 1.0, 47.0
CAB_RING_OUT = 1.0 + CAB_RING_DROP * CAB_RING_K          # the ring's centre off the wall: the bundle's line
CAB_DROP, CAB_DROP_LEN, CAB_DROP_K = AS + "SM_Cable_D_001", 200.0, 1.2
CAB_SPAN = (250.0, 420.0)            # cm between rings
CAB_RUNS = 8                         # facade chains with a run in the dressed sections ("in some instances")
CAB_TOP, CAB_WIN = 34.0, 12.0        # the ring at least this far under the wall's top (the lid), the bundle this far over an opening
CAB_HALF = 14.0                      # the bundle's half thickness (it is about 25 cm across), for clearances
CAB_GAP = 500.0                      # cm of other wall a chain may pass with no ring on it
CAB_CLIMB = 90.0                     # cm a bundle may climb from one house's ring to the next one's
CAB_CROSS, CAB_CROSS_D, CAB_CROSS_SAG = 4, (300.0, 950.0), 0.09     # bundles across the street: how many, how long (cm), sag per length
CAB_CROSS_SIDE = 450.0               # cm a crossing may run on along the street: up to a 30-degree diagonal over the main street
CAB_TRUNK_DOWN = 60.0                # a trunk hangs this far under the pole line's lowest wire end
_CAB_ROOM_BOUNDS = {                 # the overhanging rooms' meshes (Saved/LevelGen/visual/meshes.json): min, max, cm
    "SM_Balcony_A_003": ((-11.1, -5.0, -1.1), (317.4, 237.5, 399.4)),
    "SM_Balcony_B_004": ((-11.1, -5.0, -1.1), (624.4, 237.5, 399.4)),
    "SM_Balcony_B_006": ((-11.1, -5.0, -1.1), (624.4, 237.5, 399.4))}
_cab_n = {"runs": 0, "across": 0, "rings": 0, "bundles": 0, "drops": 0, "trunks": 0, "faces looked at": 0, "no room": 0}

if ASIA_CABLES:
    # What a cable must keep clear of: the wall dressing already placed, as boxes (cm), and the wires, as segments (a slanting wire's box
    # would cover the whole front of the wall it leaves). Each with its label, for the report.
    _cab_skip = {"Blocks", "Lids", "Floors", "Ground", "GroundBody", "Decals", "Roofs", "Curbs", "Interiors", "GroundDirt", "Graffiti",
                 "Peel", "Posters", "Litter"}
    _cab_obst, _cab_segs = [], []
    for p in items:
        kind_ = p["folder"].split("/")[-1]
        if not p["folder"].startswith("BackAlleys/") or kind_ in _cab_skip or p.get("decal") or p.get("light"):
            continue
        if p["asset"] == CUBE and kind_ in ("Wires", "Laundry"):
            a3, b3 = _rod_line(p)
            _cab_segs.append((a3, b3, 3.0, p["label"]))
            continue
        x_, y_, z_ = p["loc"]
        if kind_ == "Poles":                        # the shaft to the top, and the head's arms
            _cab_obst.append(((x_ - 25, y_ - 25, z_, x_ + 25, y_ + 25, z_ + 1000), p["label"]))
            _cab_obst.append(((x_ - 170, y_ - 170, z_ + 720, x_ + 170, y_ + 170, z_ + 980), p["label"]))
            continue
        if kind_ == "Lights":                       # a lamp's arm reaches out from the wall
            _cab_obst.append(((x_ - 160, y_ - 160, z_ - 35, x_ + 160, y_ + 160, z_ + 35), p["label"]))
            continue
        nm_ = p["asset"].split("/")[-1]
        if nm_ in _CAB_ROOM_BOUNDS:                 # an overhanging room: its own box, turned
            bmin, bmax = _CAB_ROOM_BOUNDS[nm_]
            Xa, Ya, Za = _rot_axes(p["rot"])
            cs = [tuple(p["loc"][k] + Xa[k] * cx * p["scale"][0] + Ya[k] * cy * p["scale"][1] + Za[k] * cz * p["scale"][2] for k in range(3))
                  for cx in (bmin[0], bmax[0]) for cy in (bmin[1], bmax[1]) for cz in (bmin[2], bmax[2])]
            _cab_obst.append(((min(c[0] for c in cs), min(c[1] for c in cs), min(c[2] for c in cs),
                               max(c[0] for c in cs), max(c[1] for c in cs), max(c[2] for c in cs)), p["label"]))
            continue
        o_ = _occ_of(p)
        _cab_obst.append((o_ if o_ else (x_ - 30, y_ - 30, z_ - 30, x_ + 30, y_ + 30, z_ + 30), p["label"]))
    # The street pass's own: patches, vents, air conditioners, pipes, laundry. Not the rooms' planning rectangles (a metre to spare, ground to
    # 30 m): the rooms are in above, as their own boxes.
    _cab_obst += [(o_, "street occupancy") for o_ in _occ if not (o_[2] == 0.0 and o_[5] == 3000.0)]
    _cab_grid = {}

    def _cab_cells(r):
        return [(i_, j_) for i_ in range(int(r[0] // 500), int(r[3] // 500) + 1) for j_ in range(int(r[1] // 500), int(r[4] // 500) + 1)]
    for o_ in _cab_obst:
        for c_ in _cab_cells(o_[0]):
            _cab_grid.setdefault(c_, []).append(("box", o_))
    for sg_ in _cab_segs:
        a3, b3 = sg_[0], sg_[1]
        for c_ in _cab_cells((min(a3[0], b3[0]), min(a3[1], b3[1]), 0, max(a3[0], b3[0]), max(a3[1], b3[1]), 0)):
            _cab_grid.setdefault(c_, []).append(("seg", sg_))
    _cab_why = []

    def _cab_tied(a3, b3, wall):
        """A wire with an end on this wall (within 25 cm of its face, along the run): a service wire that leaves the bundle there."""
        t0, run_len = wall
        rx, ry = RUN[t0["side"]]
        nx, ny = NORMAL[t0["side"]]
        for e in (a3, b3):
            n_ = (e[0] - t0["x"]) * nx + (e[1] - t0["y"]) * ny
            s_ = (e[0] - t0["x"]) * rx + (e[1] - t0["y"]) * ry
            if abs(n_) < 25.0 and -50.0 < s_ < run_len + 50.0:
                return True
        return False

    def _cab_clear(box, pad=4.0, walls=None):
        """Nothing in the box. walls [(tile, run length)]: wires tied to those walls don't count (they branch off the bundle there)."""
        seen = set()
        for c_ in _cab_cells(box):
            for kind_, o_ in _cab_grid.get(c_, ()):
                if id(o_) in seen:
                    continue
                seen.add(id(o_))
                if kind_ == "box":
                    r = o_[0]
                    if box[0] - pad < r[3] and r[0] < box[3] + pad and box[1] - pad < r[4] and r[1] < box[4] + pad and \
                            box[2] - pad < r[5] and r[2] < box[5] + pad:
                        _cab_why.append(o_[1])
                        return False
                else:
                    a3, b3, th, lab_ = o_
                    if walls and any(_cab_tied(a3, b3, w_) for w_ in walls):
                        continue
                    n_ = max(2, int(math.dist(a3, b3) / 8.0))
                    e_ = pad + th
                    for k in range(n_ + 1):
                        u_ = k / n_
                        q = (a3[0] + (b3[0] - a3[0]) * u_, a3[1] + (b3[1] - a3[1]) * u_, a3[2] + (b3[2] - a3[2]) * u_)
                        if box[0] - e_ < q[0] < box[3] + e_ and box[1] - e_ < q[1] < box[4] + e_ and box[2] - e_ < q[2] < box[5] + e_:
                            _cab_why.append(lab_)
                            return False
        return True

    def _cab_claim(box):
        o_ = (box, "cable")
        _cab_obst.append(o_)
        for c_ in _cab_cells(box):
            _cab_grid.setdefault(c_, []).append(("box", o_))

    def _cab_box(t0, s0, s1, n0, n1, z0, z1):
        a_, b_ = at(t0["x"], t0["y"], t0["side"], s0, n0), at(t0["x"], t0["y"], t0["side"], s1, n1)
        return (min(a_[0], b_[0]), min(a_[1], b_[1]), z0, max(a_[0], b_[0]), max(a_[1], b_[1]), z1)

    def _cab_bundle(label, p0, p1, sag_mesh, zsc):
        """A bundle from ring centre p0 to ring centre p1 (cm, the same height): its centre line through both."""
        d = (p1[0] - p0[0], p1[1] - p0[1], p1[2] - p0[2])
        L_ = math.sqrt(sum(c * c for c in d))
        X3 = (d[0] / L_, d[1] / L_, d[2] / L_)
        h_ = math.hypot(X3[0], X3[1])
        Y3 = (-X3[1] / h_, X3[0] / h_, 0.0)
        Z3 = v_cross(X3, Y3)
        put_axes(label, sag_mesh, X3, Y3, Z3, (L_ / CAB_B_LEN, 1.0, zsc), (0.0, CAB_B_Y, 0.0), p0, mats=None, nocoll=True)
        items[-1]["folder"] = DR_CABLES
        _cheap(CULL_FAR, 1, False)

    def _cab_drop(label, a3, b3):
        d = (b3[0] - a3[0], b3[1] - a3[1], b3[2] - a3[2])
        L_ = math.sqrt(sum(c * c for c in d))
        X3 = (d[0] / L_, d[1] / L_, d[2] / L_)
        ref = (0.0, 0.0, 1.0) if abs(X3[2]) < 0.9 else (1.0, 0.0, 0.0)
        Y3 = v_cross(ref, X3)
        n_ = math.sqrt(sum(c * c for c in Y3))
        Y3 = (Y3[0] / n_, Y3[1] / n_, Y3[2] / n_)
        put_axes(label, CAB_DROP, X3, Y3, v_cross(X3, Y3), (L_ / CAB_DROP_LEN, CAB_DROP_K, CAB_DROP_K), (0.0, 0.0, 0.0), a3, nocoll=True)
        items[-1]["folder"] = DR_CABLES
        _cheap(CULL_MID, 1, True)

    def _cab_ring(label, t0, s_, z_):
        """A ring bracket: its plate on the wall at s_ along the run, height z_ (the ring's centre), the ring out from the wall."""
        rx, ry = RUN[t0["side"]]
        nx, ny = NORMAL[t0["side"]]
        X3, Z3 = (rx, ry, 0.0), (-nx, -ny, 0.0)
        wx, wy = at(t0["x"], t0["y"], t0["side"], s_, 1.0)
        put_axes(label, CAB_RING, X3, v_cross(Z3, X3), Z3, (CAB_RING_K,) * 3, (0.0, 0.0, 0.0), (wx, wy, z_), nocoll=True)
        items[-1]["folder"] = DR_CABLES
        _cheap(CULL_MID, 1, True)

    # --- Facade runs -------------------------------------------------------------------------------------------------------
    # Every slum house's top storey on the slum's own ground gets a height for a run (under the lid, over its openings, clear of its trims)
    # and its free stretches. Neighbouring faces along one side of a street make a chain, as the demo map chains its bundles: rings about
    # every CAB_SPAN[1] cm on whichever face is free there, a bundle stepping across to the next house's front where the line is clear.
    _cab_faces = []
    for name_, ts in sorted(_run_tiles.items()):
        t0 = ts[0]
        b = BLOCKS[t0["bid"]]
        if b["storeys"] < 2 or t0["s"] != b["storeys"] - 1 or b.get("balcony") or b.get("plain") or t0["bid"] in _thin_blocks or \
                _hollow_face(t0) or not LEVEL.dress_house(b):
            continue
        run_len = ts[-1]["off"] + ts[-1]["w"] - t0["off"]
        if run_len < 2 * FACE_EDGE + 60.0:
            continue
        if not all(_ground_open(t, t["w"] / 2, 150.0) and LEVEL.dress_point(*_lay(*at(t["x"], t["y"], t["side"], t["w"] / 2, 150.0)))
                   for t in ts):
            continue
        z_t, top = t0["z"], t0["z"] + b["sh"]
        tops = []
        for t in ts:
            p_ = _by_label.get(t["label"])
            sz = abs(p_["scale"][2]) if p_ else 1.0
            if t["kind"] == "SM_Wall_Windows_01":
                tops.append(z_t + 220.0 * sz)
            elif t["kind"] == "SM_WallDoor_01":
                tops.append(z_t + 245.0 * sz)
        low = max(tops) + CAB_WIN if tops else z_t + 150.0
        trims = [q_["loc"][2] for t in ts for q_ in (_by_label.get(t["label"] + "_Trim300"), _by_label.get(t["label"] + "_Trim400")) if q_]
        z_ring = None
        z_ = top - CAB_TOP
        while z_ - CAB_BUNDLES[1][1] - CAB_HALF >= low:      # room at least for the flatter bundle
            if all(abs(z_ - tz_) > 7.9 + 6.5 * CAB_RING_K + 3.0 for tz_ in trims):
                z_ring = z_
                break
            z_ -= 5.0
        if z_ring is None:
            _cab_n["no room"] += 1
            continue
        room = z_ring - CAB_HALF - low                         # how much sag this face allows
        lo_z = z_ring - min(room, CAB_BUNDLES[0][1]) - CAB_HALF
        free, cur = [], None
        s_ = FACE_EDGE + 10.0
        while s_ <= run_len - FACE_EDGE - 10.0 + 1e-6:
            ok = _cab_clear(_cab_box(t0, s_ - 10.0, s_ + 10.0, CAB_RING_OUT - CAB_HALF, CAB_RING_OUT + CAB_HALF, lo_z, z_ring + CAB_HALF),
                            walls=[(t0, run_len)]) and _pipe_free(t0, s_ - 10.0, s_ + 10.0) and _stair_clear(t0, s_ - 10.0, s_ + 10.0, lo_z) and \
                _cab_clear(_cab_box(t0, s_ - 14.0, s_ + 14.0, 0.0, CAB_RING_OUT + 4.0, z_ring - 22.0, z_ring + 22.0), walls=[(t0, run_len)])
            if ok:
                cur = [s_, s_] if cur is None else [cur[0], s_]
            elif cur is not None:
                free.append(cur)
                cur = None
            s_ += 20.0
        if cur is not None:
            free.append(cur)
        if not free:
            _cab_n["no room"] += 1
            continue
        rx, ry = RUN[t0["side"]]
        nx, ny = NORMAL[t0["side"]]
        p_s, p_e = at(t0["x"], t0["y"], t0["side"], 0.0, 0.0), at(t0["x"], t0["y"], t0["side"], run_len, 0.0)
        _cab_faces.append({"name": name_, "t0": t0, "len": run_len, "z": z_ring, "room": room, "free": free, "side": t0["side"],
                           "u0": p_s[0] * rx + p_s[1] * ry, "u1": p_e[0] * rx + p_e[1] * ry, "v": p_s[0] * nx + p_s[1] * ny})
    # Chains: faces on one side, one after the other along the street, a setback's jog of up to a metre between them and at most CAB_GAP
    # cm of other wall (a hollow-block face, one with a lamp) between them: the bundle may pass in front of that, with no ring on it.
    _cab_faces.sort(key=lambda f_: (f_["side"], f_["u0"]))
    _cab_chains = []
    for f_ in _cab_faces:
        host = next((c_ for c_ in _cab_chains if c_[-1]["side"] == f_["side"] and -60.0 < f_["u0"] - c_[-1]["u1"] < CAB_GAP and
                     abs(f_["v"] - c_[-1]["v"]) <= 100.0), None)
        if host is not None:
            host.append(f_)
        else:
            _cab_chains.append([f_])

    def _cab_ring_pt(f_, s_):
        wx, wy = at(f_["t0"]["x"], f_["t0"]["y"], f_["side"], s_, CAB_RING_OUT)
        return (wx, wy, f_["z"])

    def _cab_link_ok(a, b, sag_):
        """The bundle from ring a to ring b (dicts: face, s) clear: on one face inside one free stretch; across two faces, a line
        through no house and nothing else (wires tied to either wall aside), and climbing no more than CAB_CLIMB a span."""
        fa, fb = a["face"], b["face"]
        if fa is fb:
            return any(fr[0] - 1e-6 <= a["s"] and b["s"] <= fr[1] + 1e-6 for fr in fa["free"])
        p0, p1 = _cab_ring_pt(fa, a["s"]), _cab_ring_pt(fb, b["s"])
        if abs(p0[2] - p1[2]) > CAB_CLIMB:
            return False
        walls = [(fa["t0"], fa["len"]), (fb["t0"], fb["len"])]
        for k in range(1, 12):
            u_ = k / 12.0
            q3 = (p0[0] + (p1[0] - p0[0]) * u_, p0[1] + (p1[1] - p0[1]) * u_, p0[2] + (p1[2] - p0[2]) * u_ - 4.0 * sag_ * u_ * (1.0 - u_))
            lx, ly = _lay(q3[0], q3[1])
            if cover_top(lx, ly) > q3[2] - FLOOR_H - CAB_HALF - 40.0:
                return False
            if not _cab_clear((q3[0] - CAB_HALF, q3[1] - CAB_HALF, q3[2] - CAB_HALF, q3[0] + CAB_HALF, q3[1] + CAB_HALF, q3[2] + CAB_HALF), 2.0, walls):
                return False
        return True

    _cab_runs = []
    CAB_RNG.shuffle(_cab_chains)
    _cab_chains.sort(key=lambda c_: -sum(f_["len"] for f_ in c_) * CAB_RNG.uniform(0.7, 1.0))     # longer chains first, loosely
    for chain in _cab_chains:
        if _cab_n["runs"] >= CAB_RUNS:
            break
        _cab_n["faces looked at"] += len(chain)
        cands = []                                                   # ring spots along the chain, by u
        for f_ in chain:
            for fr in f_["free"]:
                s_ = fr[0]
                while s_ <= fr[1] + 1e-6:
                    cands.append({"face": f_, "s": s_, "u": f_["u0"] + s_})
                    s_ += 20.0
        cands.sort(key=lambda c_: c_["u"])
        # one bundle and one sag for the whole run: the flatter one where a face is tight
        mesh, sag = CAB_BUNDLES[0] if CAB_RNG.random() < 0.6 else CAB_BUNDLES[1]
        if any(f_["room"] < sag for f_ in chain):
            mesh, sag = CAB_BUNDLES[1]
        zsc = CAB_RNG.uniform(0.85, 1.05)
        i = 0
        placed = 0
        while i < len(cands):
            run = [cands[i]]
            while True:
                last = run[-1]
                span_ = CAB_RNG.uniform(CAB_SPAN[1] - 70.0, CAB_SPAN[1])
                opts = [c_ for c_ in cands if last["u"] + CAB_SPAN[0] <= c_["u"] <= last["u"] + span_]
                nxt = next((c_ for c_ in reversed(opts) if _cab_link_ok(last, c_, sag * zsc)), None)
                if nxt is None:
                    break
                run.append(nxt)
            if len(run) >= 2:
                lab = "Cab_%s_%d" % (run[0]["face"]["name"], placed)
                pts = []
                for k, r_ in enumerate(run):
                    # each ring is named after the wall it's on, so it goes with that house
                    _cab_ring("Cab_%s_%d_Ring%d" % (r_["face"]["name"], placed, k), r_["face"]["t0"], r_["s"], r_["face"]["z"])
                    pts.append(_cab_ring_pt(r_["face"], r_["s"]))
                    _cab_n["rings"] += 1
                for k in range(len(pts) - 1):
                    a3, b3 = (pts[k], pts[k + 1]) if CAB_RNG.random() < 0.5 else (pts[k + 1], pts[k])
                    _cab_bundle("%s_B%d" % (lab, k), a3, b3, mesh, zsc * CAB_RNG.uniform(0.92, 1.04))
                    _cab_n["bundles"] += 1
                    lo3 = min(pts[k][2], pts[k + 1][2]) - sag * zsc - CAB_HALF
                    _cab_claim((min(pts[k][0], pts[k + 1][0]) - CAB_HALF, min(pts[k][1], pts[k + 1][1]) - CAB_HALF, lo3,
                                max(pts[k][0], pts[k + 1][0]) + CAB_HALF, max(pts[k][1], pts[k + 1][1]) + CAB_HALF, max(pts[k][2], pts[k + 1][2]) + 25.0))
                _cab_runs.append((run, sag * zsc, lab))
                placed += 1
                i = next((k for k, c_ in enumerate(cands) if c_["u"] > run[-1]["u"] + 60.0), len(cands))
            else:
                i += 1
        if placed:
            _cab_n["runs"] += 1

    # --- Across the street: a bundle from a ring on one house to a ring on the house opposite ------------------------------
    # The heavy bundles the user asked for over the street (2026-11-05: "power lines are a big identity show"): from a free spot on one face
    # to the spot square across on the face opposite, CAB_CROSS_D apart, sagging CAB_CROSS_SAG of its length. Near the walls the wires tied
    # there may meet it (they branch off it); over the street nothing may.
    _cab_rings_at = {}
    for run, sag_, lab in _cab_runs:
        for r_ in run:
            _cab_rings_at.setdefault(r_["face"]["name"], []).append(r_["s"])

    def _cab_spots(f_):
        """Where a crossing's ring can go on face f_: its plate clear on the wall, no pipe there, 60 cm from the other rings. A crossing
        leaves the wall straight out, so the run's corridor along the wall doesn't matter here."""
        t0, out = f_["t0"], []
        s_ = FACE_EDGE + 10.0
        while s_ <= f_["len"] - FACE_EDGE - 10.0 + 1e-6:
            if all(abs(s_ - q_) >= 60.0 for q_ in _cab_rings_at.get(f_["name"], ())) and _pipe_free(t0, s_ - 14.0, s_ + 14.0) and                     _cab_clear(_cab_box(t0, s_ - 14.0, s_ + 14.0, 0.0, CAB_RING_OUT + 4.0, f_["z"] - 22.0, f_["z"] + 22.0), walls=[(t0, f_["len"])]):
                out.append(s_)
            s_ += 20.0
        return out

    def _cab_cross_ok(fa, sa, fb, sb, sag_):
        p0, p1 = _cab_ring_pt(fa, sa), _cab_ring_pt(fb, sb)
        if abs(p0[2] - p1[2]) > CAB_CLIMB:
            return False
        walls = [(fa["t0"], fa["len"]), (fb["t0"], fb["len"])]
        for k in range(1, 16):
            u_ = k / 16.0
            q3 = (p0[0] + (p1[0] - p0[0]) * u_, p0[1] + (p1[1] - p0[1]) * u_, p0[2] + (p1[2] - p0[2]) * u_ - 4.0 * sag_ * u_ * (1.0 - u_))
            if q3[2] - CAB_HALF < 480.0:
                return False
            lx, ly = _lay(q3[0], q3[1])
            if cover_top(lx, ly) > q3[2] - FLOOR_H - CAB_HALF - 40.0:
                return False
            near_wall = u_ < 0.15 or u_ > 0.85
            if not _cab_clear((q3[0] - CAB_HALF, q3[1] - CAB_HALF, q3[2] - CAB_HALF, q3[0] + CAB_HALF, q3[1] + CAB_HALF, q3[2] + CAB_HALF), 3.0,
                              walls if near_wall else None):
                return False
        return True

    _cab_pairs = []
    for i, fa in enumerate(_cab_faces):
        for fb in _cab_faces[i + 1:]:
            if fb["side"] != OPP[fa["side"]]:
                continue
            na, nb = NORMAL[fa["side"]], NORMAL[fb["side"]]
            pa = at(fa["t0"]["x"], fa["t0"]["y"], fa["side"], fa["len"] / 2, 0.0)
            pb = at(fb["t0"]["x"], fb["t0"]["y"], fb["side"], fb["len"] / 2, 0.0)
            d_ = (pb[0] - pa[0]) * na[0] + (pb[1] - pa[1]) * na[1]
            if CAB_CROSS_D[0] - 2 * CAB_RING_OUT <= d_ <= CAB_CROSS_D[1] + 2 * CAB_RING_OUT:
                _cab_pairs.append((fa, fb))
    CAB_RNG.shuffle(_cab_pairs)
    for fa, fb in _cab_pairs:
        if _cab_n["across"] >= CAB_CROSS:
            break
        ra, rb_ = RUN[fa["side"]], RUN[fb["side"]]
        spots_b = _cab_spots(fb)
        done = False
        sa_list = _cab_spots(fa)
        CAB_RNG.shuffle(sa_list)
        for sa in sa_list:
            p0 = _cab_ring_pt(fa, sa)
            # the spots on b, squarest first
            opts = []
            for sb in spots_b:
                p1 = _cab_ring_pt(fb, sb)
                side_off = abs((p1[0] - p0[0]) * ra[0] + (p1[1] - p0[1]) * ra[1])
                if side_off <= CAB_CROSS_SIDE and CAB_CROSS_D[0] <= math.dist(p0, p1) <= CAB_CROSS_D[1]:
                    opts.append((side_off, sb, p1))
            pick = next(((sb, p1) for so_, sb, p1 in sorted(opts) if _cab_cross_ok(fa, sa, fb, sb, CAB_CROSS_SAG * math.dist(p0, p1))), None)
            if pick is None:
                continue
            sb, p1 = pick
            d_ = math.dist(p0, p1)
            sag_ = CAB_CROSS_SAG * d_
            lab = "CabX_%s_%d" % (fa["name"], _cab_n["across"])
            _cab_ring("CabX_%s_%d_RingA" % (fa["name"], _cab_n["across"]), fa["t0"], sa, fa["z"])
            _cab_ring("CabX_%s_%d_RingB" % (fb["name"], _cab_n["across"]), fb["t0"], sb, fb["z"])
            mesh, sag0 = CAB_BUNDLES[0]
            a3, b3 = (p0, p1) if CAB_RNG.random() < 0.5 else (p1, p0)
            _cab_bundle(lab + "_B", a3, b3, mesh, sag_ / sag0)
            _cab_claim((min(p0[0], p1[0]) - CAB_HALF, min(p0[1], p1[1]) - CAB_HALF, min(p0[2], p1[2]) - sag_ - CAB_HALF,
                        max(p0[0], p1[0]) + CAB_HALF, max(p0[1], p1[1]) + CAB_HALF, max(p0[2], p1[2]) + 25.0))
            _cab_rings_at.setdefault(fa["name"], []).append(sa)
            _cab_rings_at.setdefault(fb["name"], []).append(sb)
            _cab_n["across"] += 1
            _cab_n["rings"] += 2
            done = True
            break

    # --- Drops: from a run down (or up) to a junction box on the same wall, between two of its rings ------------------------
    _opening = ("SM_Wall_Windows_01", "SM_WallDoor_01")
    for run, sag_, lab in _cab_runs:
        for k in range(len(run) - 1):
            a, b = run[k], run[k + 1]
            if a["face"] is not b["face"]:
                continue
            f_ = a["face"]
            t0 = f_["t0"]
            rx, ry = RUN[t0["side"]]
            nx, ny = NORMAL[t0["side"]]
            for nd in _wire_nodes:
                if nd["side"] != t0["side"]:
                    continue
                s_ = (nd["x"] - t0["x"]) * rx + (nd["y"] - t0["y"]) * ry
                if abs((nd["x"] - t0["x"]) * nx + (nd["y"] - t0["y"]) * ny) > 15.0 or not a["s"] + 30.0 < s_ < b["s"] - 30.0:
                    continue
                u_ = (s_ - a["s"]) / (b["s"] - a["s"])
                z_b = f_["z"] - 4.0 * sag_ * u_ * (1.0 - u_) - 6.0
                z_n = nd["z"] + (6.0 if nd["z"] < z_b else -6.0)
                if abs(z_b - z_n) < 40.0:
                    continue
                zl, zh = min(z_b, z_n), max(z_b, z_n)
                if not _cab_clear(_cab_box(t0, s_ - 4.0, s_ + 4.0, 2.0, 12.0, zl + 8.0, zh - 8.0), 2.0, [(t0, f_["len"])]):
                    continue
                # no window or door crossed, on any storey of this face
                crossed = False
                for st in range(BLOCKS[t0["bid"]]["storeys"]):
                    hit = _tile_above(t0, s_, st)
                    if hit is None:
                        continue
                    u2, a2 = hit
                    if u2["kind"] in _opening and not _edge_ok(u2, a2, 6.0):
                        z_o0, z_o1 = (u2["z"], u2["z"] + 250.0) if u2["kind"] == "SM_WallDoor_01" else (u2["z"] + 85.0, u2["z"] + 230.0)
                        if zl < z_o1 and z_o0 < zh:
                            crossed = True
                if crossed:
                    continue
                w0 = at(t0["x"], t0["y"], t0["side"], s_, CAB_RING_OUT - 6.0)
                w1 = at(t0["x"], t0["y"], t0["side"], s_, 7.0)
                _cab_drop("%s_Drop%d_A" % (lab, _cab_n["drops"]), (w0[0], w0[1], z_b), (w1[0], w1[1], z_b))
                _cab_drop("%s_Drop%d_B" % (lab, _cab_n["drops"]), (w1[0], w1[1], z_b), (w1[0], w1[1], z_n))
                _cab_claim(_cab_box(t0, s_ - 4.0, s_ + 4.0, 2.0, CAB_RING_OUT, zl, zh))
                _cab_n["drops"] += 1

    # --- Trunks: one bundle pole to pole, under the line's wires -----------------------------------------------------------
    _poles_at = {p["label"]: p for p in items if p["folder"] == DR_POLES and "Electric_Pole" in p["asset"]}
    _lines = {}
    for p in items:
        if p["label"].startswith("PoleLine_") and p["asset"] == CUBE:
            q = p["label"].split("_")
            _lines.setdefault((q[1], q[2]), []).append(_rod_line(p))
    for (i_, j_), rods in sorted(_lines.items()):
        pa, pb = _poles_at.get("Pole_" + i_), _poles_at.get("Pole_" + j_)
        if pa is None or pb is None:
            continue
        ends = [r_[0] for r_ in rods] + [r_[1] for r_ in rods]
        za = min(e[2] for e in ends if math.hypot(e[0] - pa["loc"][0], e[1] - pa["loc"][1]) < 300.0) - CAB_TRUNK_DOWN
        zb = min(e[2] for e in ends if math.hypot(e[0] - pb["loc"][0], e[1] - pb["loc"][1]) < 300.0) - CAB_TRUNK_DOWN
        dx, dy = pb["loc"][0] - pa["loc"][0], pb["loc"][1] - pa["loc"][1]
        L_ = math.hypot(dx, dy)
        ux, uy = dx / L_, dy / L_
        a3 = (pa["loc"][0] + ux * 16.0, pa["loc"][1] + uy * 16.0, za)
        b3 = (pb["loc"][0] - ux * 16.0, pb["loc"][1] - uy * 16.0, zb)
        span = math.dist(a3, b3)
        sag_t = min(0.03 * span, 60.0)
        lowest = min(min(r_[0][2], r_[1][2]) for r_ in rods)
        if (za + zb) / 2 - sag_t > lowest - 25.0:        # it would meet the line's lowest wire: hang it lower
            sag_t = max(10.0, (za + zb) / 2 - (lowest - 25.0))
        if min(za, zb) - sag_t < 480.0:
            continue
        # The curve clear of everything but the poles' own heads: samples a metre and more from either pole.
        blocked = False
        for k in range(1, 20):
            u_ = k / 20.0
            q3 = (a3[0] + (b3[0] - a3[0]) * u_, a3[1] + (b3[1] - a3[1]) * u_, a3[2] + (b3[2] - a3[2]) * u_ - 4.0 * sag_t * u_ * (1.0 - u_))
            if min(math.dist(q3[:2], pa["loc"][:2]), math.dist(q3[:2], pb["loc"][:2])) < 200.0:
                continue
            if not _cab_clear((q3[0] - CAB_HALF, q3[1] - CAB_HALF, q3[2] - CAB_HALF, q3[0] + CAB_HALF, q3[1] + CAB_HALF, q3[2] + CAB_HALF), 2.0):
                blocked = True
                break
        if blocked:
            _cab_n["trunks blocked"] = _cab_n.get("trunks blocked", 0) + 1
            continue
        mesh, sag0 = CAB_BUNDLES[0]
        _cab_bundle("CabTrunk_%s_%s" % (i_, j_), a3, b3, mesh, sag_t / sag0)
        _cab_n["trunks"] += 1
    print("asia cables:", _cab_n)
