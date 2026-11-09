# Pass `story_ground` (story levels; levels/linear_slums.py). The ground at its heights, 2026-11-08:
# - every walkable area on the ground floor (open, covered, out of bounds) is a slab: a concrete body (its sides are the
#   retaining walls where the ground steps) and a poured top as a plane, as the arena's pours (IgnoreOnlyPawn, nonav);
# - ground under each street house's footprint before its setback, so a setback leaves no hole;
# - the eskinita's steps (the layout's 1.8 m stair), parapets wherever open ground drops 1 m or more except at the
#   layout's drops (the broken yard wall), the lane's two gates (the layout's barriers), the garage roof over the car.
# Needs: AREAS, LAYOUT_RAW, BLOCKS, ground_z (levels/linear_slums.py setup), put, put_axes (roofs pass).
PLANE = "/Engine/BasicShapes/Plane"
GR = "BackAlleys/Ground"
GR_BODY = "BackAlleys/GroundBody"
GM = BM + "MI_BackAlleys_Ground_"
GROUND_RNG2 = random.Random(401)
G_MAT = {1: "AsphaltPatch", 2: "ConcreteOld", 3: "ConcreteB", 4: "ConcreteA", 5: "ConcreteOld", 6: "ConcreteA", 7: "ConcreteB"}
G_AREA = {"LANE": "AsphaltPatch", "WASH": "ConcreteA", "CYARD": "ConcreteOld"}
G_SKIN = 0.6        # cm the poured plane sits over the body's top (check_dressing: a pour at most 0.85 over its road)
STEP_H, STEP_G = 18.0, 30.0
PARAPET_DROP = 100.0
YARD_WALL_H, YARD_WALL_T = 110.0, 15.0
# Areas whose yard wall runs their whole edge, not only the stretch over the lower area, and is capped (user 2026-11-09, of eskinita E3: "in
# the eskenita, extend the hollow block wall all the way", "put a cap on it too"): E3's north edge drops to the yard for 3 m, and along the
# rest of it a 60 cm slot drops past the yard's houses. A drop opening still cuts it.
PARAPET_FULL = getattr(LEVEL, "PARAPET_FULL", ())
YARD_CAP_T, YARD_CAP_OUT = 6.0, 0.03
_RAW = LAYOUT_RAW


def _box(label, x0, y0, x1, y1, z0, z1, folder, mats, **kw):
    """A cube over layout metres x0..x1 east, y0..y1 south, z0..z1 cm."""
    X1, Y0 = ue(x0, y0)
    X0, Y1 = ue(x1, y1)
    put(label, CUBE, X0, Y0, z0, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, (z1 - z0) / 100.0), folder=folder, mats=mats, **kw)
    return items[-1]


def _pour(label, x0, y0, x1, y1, z, kind, phys="Concrete"):
    X, Y = ue((x0 + x1) / 2, (y0 + y1) / 2)
    put(label, PLANE, X, Y, z, 0, ((y1 - y0), (x1 - x0), 1.0), folder=GR, mats=[GM + kind])
    p = items[-1]
    p["coll"], p["phys"], p["nonav"] = "IgnoreOnlyPawn", PHYS + phys, True
    return p


def _touch(r, q, pad=0.05):
    return r[0] - pad <= q[2] and q[0] - pad <= r[2] and r[1] - pad <= q[3] and q[1] - pad <= r[3]


_g_n = {"slabs": 0, "steps": 0, "parapets": 0, "gates": 0, "house ground": 0}
# The slum's street (user 2026-11-09: "we need a curb and actual street. Look at the net for references of PH streets"): a concrete
# road in panels with dark joints, and a raised sidewalk along the house fronts, its edge the curb. The eskinita: concrete with a
# drain channel along one side.
SIDEWALK_W, CURB_H = 1.1, 15.0
# The curb: Favela's main border stone (user 2026-11-09, of a sharp box cap: "its too sharp edged, you should be using the main border
# stone"). SM_MainBorder_04 is 150 cm long from its pivot along local X, 26.4 wide (Y +-13.2) and 15.8 tall (Z +-7.9), worn, with
# rounded edges: the curb's own height, so it is the curb face, not a cap on it.
CURB_STONE = "/Game/Megapack/Meshes/Favela/SM_MainBorder_04"
CURB_STONE_L, CURB_W = 150.0, 0.264               # cm, m
CURB_UP, CURB_PROUD, CURB_DOWN = 1.0, 0.03, 1.0     # cm over the sidewalk, m out past its face, cm into the road
CURB_JOINT = 1.0                                    # cm between stones: a joint, not a butt
CURB = "BackAlleys/Curbs"
PANEL_L, JOINT_W = (3.6, 4.6), 0.04
# Panel ends on a 2 cm grid: each piece's centre then falls on a whole centimetre and the plan's 1 mm rounding leaves them edge to
# edge. Off the grid they lap by a fraction of a millimetre and shimmer (check_overlaps, ground planes).
_snap2 = lambda v: round(v * 50.0) / 50.0
GUTTER = {"E2": "south", "E3": "south", "E4": "east"}
GUTTER_W = 0.3
_street_rects = []
# --- Area slabs ----------------------------------------------------------------------------------------------------------
_low = {}       # area id -> the lowest ground beside it, for the body's foot
for a in AREAS:
    zs = [a["z"]] + [o["z"] for o in AREAS if o is not a and _touch(a["r"], o["r"])] + \
        [b.get("z", 0.0) for b in BLOCKS.values() if _touch(a["r"], (b["x0"], b["y0"], b["x1"], b["y1"]))]
    _low[a["id"]] = min(zs)
for a in AREAS:
    if a["kind"] == "room":
        continue                                    # the buildings make their own floors
    x0, y0, x1, y1 = a["r"]
    kind = "ConcreteOld" if a["kind"] == "nml" else G_AREA.get(a["id"], G_MAT[a["sec"]])
    foot = _low[a["id"]] - 20.0
    if a["id"] == "E1":                             # the steps up into the eskinita: y 84..87, 1.8 m, going south
        _box("Ground_E1_Foot", x0, y0, x1, 84.0, foot, -G_SKIN, GR_BODY, [CONC])
        _pour("Ground_E1_Foot_Top", x0, y0, x1, 84.0, 0.0, kind)
        n = int(round(STEP_RISE / STEP_H))
        for k in range(n):
            ya, yb = 84.0 + k * 3.0 / n, 84.0 + (k + 1) * 3.0 / n
            _box("Step_E1_%d" % k, x0, ya, x1, y1 if k == n - 1 else yb + 0.02, foot, (k + 1) * STEP_RISE / n, GR_BODY, [CONC])
            _g_n["steps"] += 1
        _pour("Ground_E1_Top", x0, 87.0, x1, y1, STEP_RISE + G_SKIN * 0.5, kind)
        continue
    _box("Ground_%s" % a["id"], x0, y0, x1, y1, foot, a["z"] - G_SKIN, GR_BODY, [CONC])
    _g_n["slabs"] += 1
    if a["sec"] == 1 and a["kind"] == "open":
        continue                                    # the main street: sidewalk, curb and road panels, below
    if a["id"] in GUTTER:                           # a drain channel along one side, as the eskinitas have
        side_ = GUTTER[a["id"]]
        g0 = {"south": (x0, y1 - GUTTER_W, x1, y1), "north": (x0, y0, x1, y0 + GUTTER_W),
              "east": (x1 - GUTTER_W, y0, x1, y1), "west": (x0, y0, x0 + GUTTER_W, y1)}[side_]
        rest = {"south": (x0, y0, x1, y1 - GUTTER_W), "north": (x0, y0 + GUTTER_W, x1, y1),
                "east": (x0, y0, x1 - GUTTER_W, y1), "west": (x0 + GUTTER_W, y0, x1, y1)}[side_]
        _pour("Ground_%s_Top" % a["id"], *rest, a["z"], kind)
        _pour("Ground_%s_Gutter" % a["id"], *g0, a["z"], "AsphaltPatch", "Asphalt")
        continue
    _pour("Ground_%s_Top" % a["id"], x0, y0, x1, y1, a["z"], kind, "Asphalt" if kind == "AsphaltPatch" else "Concrete")

# --- The main street: sidewalk and curb along the house fronts (and into a setback's gap), road panels between ---------------
def _grid_rects2(cells, x0, y0, nx, ny, cell):
    g = [[(i, j) in cells for i in range(nx)] for j in range(ny)]
    out = []
    while True:
        best, hts = None, [0] * nx
        for j in range(ny):
            for i in range(nx):
                hts[i] = hts[i] + 1 if g[j][i] else 0
            stack = []
            for i in range(nx + 1):
                h = hts[i] if i < nx else 0
                start = i
                while stack and stack[-1][1] >= h:
                    s0, sh = stack.pop()
                    if sh and (best is None or sh * (i - s0) > best[0]):
                        best = (sh * (i - s0), s0, j - sh + 1, i, j + 1)
                    start = s0
                stack.append((start, h))
        if best is None:
            return out
        _, i0, j0, i1, j1 = best
        for j in range(j0, j1):
            for i in range(i0, i1):
                g[j][i] = False
        out.append((x0 + i0 * cell, y0 + j0 * cell, x0 + i1 * cell, y0 + j1 * cell))


_streets = [a for a in AREAS if a["sec"] == 1 and a["kind"] == "open"]
if _streets:
    _slum = [b for b in BLOCKS.values() if not b.get("plain")]

    def _orig(b):
        sb_ = b.get("setback", {})
        return (b["x0"] - sb_.get("west", 0.0), b["y0"] - sb_.get("north", 0.0), b["x1"] + sb_.get("east", 0.0), b["y1"] + sb_.get("south", 0.0))
    _fronts = []                                    # (x0, y0, x1, y1) segments of street edge with a house behind
    for a in _streets:
        x0, y0, x1, y1 = a["r"]
        for axis, c, t0, t1, sgn in (("x", y0, x0, x1, -1.0), ("x", y1, x0, x1, 1.0), ("y", x0, y0, y1, -1.0), ("y", x1, y0, y1, 1.0)):
            n = max(1, int(math.ceil((t1 - t0) / 0.25)))
            for i in range(n):
                ta, tb = t0 + (t1 - t0) * i / n, t0 + (t1 - t0) * (i + 1) / n
                tm = (ta + tb) / 2
                p = (tm, c + sgn * 0.3) if axis == "x" else (c + sgn * 0.3, tm)
                if any(_orig(b)[0] < p[0] < _orig(b)[2] and _orig(b)[1] < p[1] < _orig(b)[3] for b in _slum):
                    _fronts.append((ta, c, tb, c) if axis == "x" else (c, ta, c, tb))
    cell = 0.25
    gx0 = min(a["r"][0] for a in _streets) - 1.5
    gy0 = min(a["r"][1] for a in _streets) - 1.5
    nx = int(round((max(a["r"][2] for a in _streets) + 1.5 - gx0) / cell))
    ny = int(round((max(a["r"][3] for a in _streets) + 1.5 - gy0) / cell))
    # Where an eskinita or another open area opens off the street, the sidewalk stops at the house corners: nothing across a
    # mouth (user 2026-11-09, of the E1 parapet: "you also added a wall at the entrance of the eskinita and I can't go through").
    _mouths = []
    for a in _streets:
        for o in AREAS:
            if o in _streets or o["kind"] == "room":
                continue
            ax0, ay0, ax1, ay1 = a["r"]
            ox0, oy0, ox1, oy1 = o["r"]
            for c, hit in ((ay0, abs(oy1 - ay0) < 0.01), (ay1, abs(oy0 - ay1) < 0.01)):
                t0, t1 = max(ax0, ox0), min(ax1, ox1)
                if hit and t1 - t0 > 0.5:
                    _mouths.append((t0, c - SIDEWALK_W - 0.5, t1, c + SIDEWALK_W + 0.5))
            for c, hit in ((ax0, abs(ox1 - ax0) < 0.01), (ax1, abs(ox0 - ax1) < 0.01)):
                t0, t1 = max(ay0, oy0), min(ay1, oy1)
                if hit and t1 - t0 > 0.5:
                    _mouths.append((c - SIDEWALK_W - 0.5, t0, c + SIDEWALK_W + 0.5, t1))
    side_c, road_c = set(), set()
    gaps_ = [(_orig(b), (b["x0"], b["y0"], b["x1"], b["y1"])) for b in _slum if b.get("setback")]
    _front_grid = {}                                # (2026-11-09) the fronts by 1 m cell: a cell only asks about fronts within 1.1 m
    for f in _fronts:
        for gi in range(math.floor(f[0]) - 2, math.floor(f[2]) + 3):
            for gj in range(math.floor(f[1]) - 2, math.floor(f[3]) + 3):
                _front_grid.setdefault((gi, gj), []).append(f)
    for j in range(ny):
        for i in range(nx):
            x, y = gx0 + (i + 0.5) * cell, gy0 + (j + 0.5) * cell
            _fronts_here = _front_grid.get((math.floor(x), math.floor(y)), ())
            in_st = any(a["r"][0] < x < a["r"][2] and a["r"][1] < y < a["r"][3] for a in _streets)
            in_gap = any(o[0] < x < o[2] and o[1] < y < o[3] and not (r[0] < x < r[2] and r[1] < y < r[3]) for o, r in gaps_) and \
                any(max(f[0] - x, 0.0, x - f[2], f[1] - y, 0.0, y - f[3]) < 1.0 for f in _fronts_here)
            in_mouth = any(m[0] < x < m[2] and m[1] < y < m[3] for m in _mouths)
            if not in_mouth and (in_gap or (in_st and any(max(f[0] - x, 0.0, x - f[2], f[1] - y, 0.0, y - f[3]) <= SIDEWALK_W for f in _fronts_here))):
                side_c.add((i, j))
            elif in_st:
                road_c.add((i, j))
    zst = _streets[0]["z"]
    for k, r in enumerate(_grid_rects2(side_c, gx0, gy0, nx, ny, cell)):
        _box("Sidewalk_%d" % k, *r, zst - 10.0, zst + CURB_H - G_SKIN, GR_BODY, [CONC])
        _pour("Sidewalk_%d_Top" % k, *r, zst + CURB_H, "ConcreteOld")
        _street_rects.append(r)
    pk = 0
    for k, r in enumerate(_grid_rects2(road_c, gx0, gy0, nx, ny, cell)):
        x0, y0, x1, y1 = r
        along_x = (x1 - x0) >= (y1 - y0)
        a0, a1 = (x0, x1) if along_x else (y0, y1)
        s = a0
        while s < a1 - 1e-6:
            e = min(a1, _snap2(s + GROUND_RNG2.uniform(*PANEL_L)))
            if a1 - e < 1.5:
                e = a1
            bay = (s, y0, e, y1) if along_x else (x0, s, x1, e)
            _pour("Road_%d" % pk, *bay, zst, GROUND_RNG2.choice(("ConcreteA", "ConcreteB", "ConcreteA", "ConcreteOld")))
            pk += 1
            if e < a1 - 1e-6:
                je = min(a1, _snap2(e + JOINT_W))
                _pour("Road_%d_Joint" % pk, *((e, y0, je, y1) if along_x else (x0, e, x1, je)), zst, "AsphaltPatch", "Asphalt")
                e = je
            s = e
        _street_rects.append(r)
    _g_n["sidewalk pieces"], _g_n["road panels"] = len(side_c) and len([p for p in items if p["label"].startswith("Sidewalk_") and p["label"].endswith("_Top")]), pk
    # Curb stones (user 2026-11-09: "cap the curb edge", then the main border stone): along every sidewalk edge on the road, a row of
    # stones CURB_W wide, from CURB_DOWN under the road to CURB_UP over the sidewalk, CURB_PROUD out past the sidewalk's face (so no
    # face of theirs lies in the sidewalk's), CURB_JOINT apart. Along-x rows run through the corners; along-y ones stop at them.
    edges = {}                                      # (axis, line, outward sign) -> cell spans along the line
    for (i, j) in side_c:
        for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            if (i + di, j + dj) not in road_c:
                continue
            if dj:
                edges.setdefault(("x", round(gy0 + (j + (dj > 0)) * cell, 3), dj), []).append(i)
            else:
                edges.setdefault(("y", round(gx0 + (i + (di > 0)) * cell, 3), di), []).append(j)
    runs_x, runs_y = [], []
    for (axis, c, sg), ks in sorted(edges.items()):
        ks = sorted(ks)
        k0 = prev = ks[0]
        for k in ks[1:] + [None]:
            if k is not None and k == prev + 1:
                prev = k
                continue
            g0 = (gx0 if axis == "x" else gy0) + k0 * cell
            g1 = (gx0 if axis == "x" else gy0) + (prev + 1) * cell
            n0, n1 = sorted((c - sg * (CURB_W - CURB_PROUD), c + sg * CURB_PROUD))
            if axis == "x":
                runs_x.append([g0 - CURB_PROUD, n0, g1 + CURB_PROUD, n1])
            else:
                runs_y.append([n0, g0, n1, g1])
            if k is not None:
                k0 = prev = k
    for r in runs_y:                                # an along-y stone stops where an along-x one crosses its end
        for q in runs_x:
            if min(r[2], q[2]) - max(r[0], q[0]) > 1e-6 and min(r[3], q[3]) - max(r[1], q[1]) > 1e-6:
                if q[1] <= r[1] + 1e-6:
                    r[1] = max(r[1], q[3])
                if q[3] >= r[3] - 1e-6:
                    r[3] = min(r[3], q[1])
    n_curb = 0
    _c_sz = (CURB_H + CURB_UP + CURB_DOWN) / 15.8
    _c_zc = zst + (CURB_H + CURB_UP - CURB_DOWN) / 2.0      # the stone's pivot is its middle
    for _c_k, _c_r in enumerate(runs_x + [q for q in runs_y if q[3] - q[1] > 0.02]):   # (the passes share one namespace: no L, X, Y here)
        _c_ax = _c_k < len(runs_x)
        _c_a0, _c_a1 = (_c_r[0], _c_r[2]) if _c_ax else (_c_r[1], _c_r[3])
        _c_mid = (_c_r[1] + _c_r[3]) / 2.0 if _c_ax else (_c_r[0] + _c_r[2]) / 2.0
        _c_len = (_c_a1 - _c_a0) * 100.0
        _c_n = max(1, int(math.ceil(_c_len / CURB_STONE_L)))
        _c_seg = _c_len / _c_n
        for _c_i in range(_c_n):
            _c_s0 = _c_a0 * 100.0 + _c_seg * _c_i + (CURB_JOINT / 2.0 if _c_i else 0.0)
            _c_s1 = _c_a0 * 100.0 + _c_seg * (_c_i + 1) - (CURB_JOINT / 2.0 if _c_i < _c_n - 1 else 0.0)
            # local X along the row: layout +x is UE +Y (yaw 90), layout +y is UE -X (yaw 180)
            _cX, _cY = ue(_c_s0 / 100.0, _c_mid) if _c_ax else ue(_c_mid, _c_s0 / 100.0)
            put("Curb_%d_%d" % (_c_k, _c_i), CURB_STONE, _cX, _cY, _c_zc, 90.0 if _c_ax else 180.0,
                ((_c_s1 - _c_s0) / CURB_STONE_L, CURB_W * 100.0 / 26.4, _c_sz), folder=CURB)
            n_curb += 1
    _g_n["curb stones"] = n_curb

# --- Under the street houses: their footprint before the setback, at their base -------------------------------------------
for bid, b in BLOCKS.items():
    sb = b.get("setback", {})
    x0, y0 = b["x0"] - sb.get("west", 0.0), b["y0"] - sb.get("north", 0.0)
    x1, y1 = b["x1"] + sb.get("east", 0.0), b["y1"] + sb.get("south", 0.0)
    z = b.get("z", 0.0)
    _box("HouseGround_%s" % bid, x0, y0, x1, y1, z - 40.0, z - G_SKIN, GR_BODY, [CONC])
    if sb:                                          # what a setback leaves in front of the house is street
        for side, d in sb.items():
            q = {"west": (x0, b["y0"], b["x0"], b["y1"]), "east": (b["x1"], b["y0"], x1, b["y1"]),
                 "north": (b["x0"], y0, b["x1"], b["y0"]), "south": (b["x0"], b["y1"], b["x1"], y1)}[side]
            if any(min(q[2], r[2]) - max(q[0], r[0]) > 0.01 and min(q[3], r[3]) - max(q[1], r[1]) > 0.01 for r in _street_rects):
                continue                            # the sidewalk covers it
            _pour("HouseGround_%s_%s" % (bid, side[0].upper()), *q, z, "ConcreteOld")
    _g_n["house ground"] += 1

# --- Parapets where open ground drops a metre or more, but not at the layout's drops ---------------------------------------
_drops = [o for o in _RAW["openings"] if o["f"] == 0 and o["k"] == "drop"]


def _gaps(line_axis, c, t0, t1):
    """Pieces of the edge t0..t1 on the line (axis 'x' = a line of constant y) that aren't a drop."""
    cut = []
    for o in _drops:
        (ax, ay), (bx, by) = o["a"], o["b"]
        if line_axis == "x" and abs(ay - c) < 0.01 and abs(by - c) < 0.01:
            cut.append((min(ax, bx), max(ax, bx)))
        if line_axis == "y" and abs(ax - c) < 0.01 and abs(bx - c) < 0.01:
            cut.append((min(ay, by), max(ay, by)))
    out, t = [], t0
    for a_, b_ in sorted(cut):
        if b_ <= t or a_ >= t1:
            continue
        if a_ > t:
            out.append((t, a_))
        t = max(t, b_)
    if t < t1:
        out.append((t, t1))
    return out


_open = [a for a in AREAS if a["kind"] != "room"]
for a in _open:
    for o in _open:
        if a is o or a["z"] - o["z"] < PARAPET_DROP:
            continue
        ax0, ay0, ax1, ay1 = a["r"]
        ox0, oy0, ox1, oy1 = o["r"]
        edges = []
        if abs(ay1 - oy0) < 0.01 or abs(ay0 - oy1) < 0.01:     # o south / north of a
            c = ay1 if abs(ay1 - oy0) < 0.01 else ay0
            t0, t1 = max(ax0, ox0), min(ax1, ox1)
            if t1 - t0 > 0.05:
                edges = [("x", c, t0, t1, 1.0 if c == ay1 else -1.0)]
        if abs(ax1 - ox0) < 0.01 or abs(ax0 - ox1) < 0.01:
            c = ax1 if abs(ax1 - ox0) < 0.01 else ax0
            t0, t1 = max(ay0, oy0), min(ay1, oy1)
            if t1 - t0 > 0.05:
                edges.append(("y", c, t0, t1, 1.0 if c == ax1 else -1.0))
        for axis, c, t0, t1, sgn in edges:
            tm_ = (t0 + t1) / 2
            pin = (tm_, c - sgn * 0.3) if axis == "x" else (c - sgn * 0.3, tm_)
            pout = (tm_, c + sgn * 0.3) if axis == "x" else (c + sgn * 0.3, tm_)
            if ground_z(*pin) - ground_z(*pout) < PARAPET_DROP:
                continue                            # the ground there doesn't drop (2026-11-09: a wall across the eskinita's mouth)
            if a["id"] in PARAPET_FULL:
                t0, t1 = (ax0, ax1) if axis == "x" else (ay0, ay1)
            whole = _gaps(axis, c, t0, t1)
            t_in = YARD_WALL_T / 100.0
            for k, (g0, g1) in enumerate(whole):
                # Hollow blocks on the higher side, on its slab; the stub ends of a broken stretch are left low and ragged.
                broken = (g0 > t0 + 0.01, g1 < t1 - 0.01)
                if axis == "x":
                    r = (g0, c - t_in, g1, c) if sgn > 0 else (g0, c, g1, c + t_in)
                else:
                    r = (c - t_in, g0, c, g1) if sgn > 0 else (c, g0, c + t_in, g1)
                _box("YardWall_%s_%s_%d" % (a["id"], o["id"], k), *r, a["z"] - 2.0, a["z"] + YARD_WALL_H, GR_BODY,
                     [BM + "MI_BackAlleys_HollowBlocks_World"])
                if a["id"] in PARAPET_FULL:         # the compound walls' cap: concrete, 6 cm, 3 cm proud of both faces
                    rc = (r[0], r[1] - YARD_CAP_OUT, r[2], r[3] + YARD_CAP_OUT) if axis == "x" else (r[0] - YARD_CAP_OUT, r[1], r[2] + YARD_CAP_OUT, r[3])
                    # Two layers: the pours' concrete is mapped from above and streaks on an upright face (the user's "messed up UVs on one side"),
                    # the wall render streaks on a flat one. So the body in the render, and the top 1 cm in the pours' concrete.
                    _box("YardWall_%s_%s_%d_CapBody" % (a["id"], o["id"], k), *rc, a["z"] + YARD_WALL_H, a["z"] + YARD_WALL_H + YARD_CAP_T - 1.0, GR_BODY,
                         [CONC])
                    _box("YardWall_%s_%s_%d_Cap" % (a["id"], o["id"], k), *rc, a["z"] + YARD_WALL_H + YARD_CAP_T - 1.0, a["z"] + YARD_WALL_H + YARD_CAP_T,
                         GR_BODY, [GM + "ConcreteOld"])
                for e, end in enumerate(broken):
                    if not end:
                        continue
                    t_e = g0 if e == 0 else g1
                    w_ = 0.3
                    s0, s1 = (t_e, t_e + w_) if e == 1 else (t_e - w_, t_e)
                    if axis == "x":
                        r = (s0, c - t_in, s1, c) if sgn > 0 else (s0, c, s1, c + t_in)
                    else:
                        r = (c - t_in, s0, c, s1) if sgn > 0 else (c, s0, c + t_in, s1)
                    _box("YardWall_%s_%s_%d_Stub%d" % (a["id"], o["id"], k, e), *r, a["z"] - 2.0,
                         a["z"] + GROUND_RNG2.uniform(25.0, 60.0), GR_BODY, [BM + "MI_BackAlleys_HollowBlocks_World"])
                _g_n["parapets"] += 1

# --- The compound's walls (levels/linear_slums.py, COMPOUND_BACK): one storey of the user's hollow blocks round each open area of the
# compound, 20 cm inside its edge, wherever the walled-off ground or a house is behind it, with a concrete cap. North/south walls stop
# at an east/west wall's face where one meets them, so no two share a top face.
CW_MAT = BM + "MI_BackAlleys_HollowBlocks_World"
CW_T = 0.20
_nml = [a for a in AREAS if a["kind"] == "nml"]


def _walled_behind(lx, ly):
    return any(a["r"][0] < lx < a["r"][2] and a["r"][1] < ly < a["r"][3] for a in _nml) or         any(b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] for b in BLOCKS.values())


_cw_n = 0
for a in AREAS:
    if a["sec"] < 3 or a["kind"] not in ("open", "cov") or a["id"] in COMPOUND_SKIP:
        continue
    x0, y0, x1, y1 = a["r"]
    H, z = COMPOUND_WALL_HI.get(a["id"], COMPOUND_WALL_H), a["z"]
    sides = {"north": ("x", y0, x0, x1, -1.0), "south": ("x", y1, x0, x1, 1.0), "west": ("y", x0, y0, y1, -1.0), "east": ("y", x1, y0, y1, 1.0)}
    runs = {}
    for side, (axis, c, t0, t1, sgn) in sides.items():
        n = max(1, int(math.ceil((t1 - t0) / 0.25)))
        rs = []
        for i in range(n):
            ta, tb = t0 + (t1 - t0) * i / n, t0 + (t1 - t0) * (i + 1) / n
            tm = (ta + tb) / 2
            p = (tm, c + sgn * 0.3) if axis == "x" else (c + sgn * 0.3, tm)
            if _walled_behind(*p):
                if rs and abs(rs[-1][1] - ta) < 1e-9:
                    rs[-1][1] = tb
                else:
                    rs.append([ta, tb])
        runs[side] = [r for r in rs if r[1] - r[0] > 0.2]
    for side, (axis, c, t0, t1, sgn) in sides.items():
        for k, (ra, rb) in enumerate(runs[side]):
            if axis == "x":                            # stop at an east/west wall that holds this corner
                if abs(ra - t0) < 1e-6 and any(abs(r[0] - (y0 if side == "north" else y1)) < 0.3 or abs(r[1] - (y0 if side == "north" else y1)) < 0.3 for r in runs["west"]):
                    ra += CW_T
                if abs(rb - t1) < 1e-6 and any(abs(r[0] - (y0 if side == "north" else y1)) < 0.3 or abs(r[1] - (y0 if side == "north" else y1)) < 0.3 for r in runs["east"]):
                    rb -= CW_T
            n0, n1 = sorted((c, c - sgn * CW_T))
            # The cap in two layers (2026-11-09, user: "Yes, fix them", after E3's yard wall cap): a 5 cm body in the wall render, whose
            # sides don't streak, and the top 1 cm in the pours' concrete, which is mapped from above and streaked on the sides.
            for part, (za, zb, mat, widen) in (("", (z - 20.0, z + H, CW_MAT, 0.0)), ("_CapBody", (z + H, z + H + 5.0, CONC, 0.03)),
                                               ("_Cap", (z + H + 5.0, z + H + 6.0, GM + "ConcreteOld", 0.03))):
                if axis == "x":
                    _box("CompoundWall_%s_%s%d%s" % (a["id"], side[0].upper(), k, part), ra, n0 - widen, rb, n1 + widen, za, zb, GR_BODY, [mat])
                else:
                    _box("CompoundWall_%s_%s%d%s" % (a["id"], side[0].upper(), k, part), n0 - widen, ra, n1 + widen, rb, za, zb, GR_BODY, [mat])
            _cw_n += 1
_g_n["compound walls"] = _cw_n

# --- The lane's gates (the layout's barriers): two steel leaves on posts, the plain sheet toward the street ----------------
GATE_LEAF = 165.8          # SM_Metal_Gate_01: X -1.7..164.1 along, Y -7.6..4.2, Z 0..241; sheet on local -Y
for k, g in enumerate(_RAW["barriers"]):
    (ax, ay), (bx, by) = g["a"], g["b"]
    z = ground_z(ax - 0.3, (ay + by) / 2) if abs(ax - bx) < 0.01 else ground_z((ax + bx) / 2, ay - 0.3)
    side = "west" if abs(ax - bx) < 0.01 else "north"          # the street is west of both
    y_n, y_s = min(ay, by), max(ay, by)
    sx, sy = ue(ax, y_n)                                       # the run starts at the north end, going south
    span = (y_s - y_n) * 100.0
    sa = (span / 2 - 6.0) / GATE_LEAF
    for j in range(2):
        s0 = 3.0 + j * span / 2
        x_, y_ = at(sx, sy, side, s0 + 164.1 * sa, 0.0)
        put("Gate_%d_%d" % (k, j), FV + "SM_Metal_Gate_01", x_, y_, z + 2.0, YAW[side] + 180.0, (sa, 1.0, 1.05),
            folder="BackAlleys/Gates")
        items[-1]["phys"] = PHYS + "Metal"
    for j, s_ in enumerate((0.0, span)):
        x_, y_ = at(sx, sy, side, s_, 0.0)
        put("Gate_%d_Post%d" % (k, j), CUBE, x_ - 7.5, y_ - 7.5, z, 0, (0.15, 0.15, 2.7), folder="BackAlleys/Gates",
            mats=[BM + "MI_BackAlleys_MetalSheet_Rust"])
    _g_n["gates"] += 1


# --- Lean-to sheet roofs on posts (the garage over the car; the covered alley uses it too) ---------------------------------
PLATE_A = (AS + "SM_MetalPlate_A_001", AS + "SM_MetalPlate_A_002")     # 162.4 wide, 324.9 long, pivot at the top end


def sheet_roof(label, rect, high, z_hi, z_lo, folder, finish="Rust", rng=GROUND_RNG2, posts=None, post_mat=None):
    """Corrugated sheets over rect (layout m), falling from its `high` side (north/south/east/west) at z_hi to the
    opposite side at z_lo (cm, sheet underside), 15 cm end laps and 18 cm side laps, alternate columns 2 cm up.
    posts: layout points for 8 cm steel posts up to the low edge's beam."""
    x0, y0, x1, y1 = rect
    dx, dy = {"north": (0, 1), "south": (0, -1), "west": (1, 0), "east": (-1, 0)}[high]      # layout downslope
    along = "x" if high in ("north", "south") else "y"
    run = (y1 - y0) if along == "x" else (x1 - x0)
    a0, a1 = (x0, x1) if along == "x" else (y0, y1)
    line = {"north": y0, "south": y1, "west": x0, "east": x1}[high]
    pitch = math.atan2(z_hi - z_lo, run * 100.0)
    cosp, sinp = math.cos(pitch), math.sin(pitch)
    D = ue_dir(dx, dy)
    up_slope = (-D[0] * cosp, -D[1] * cosp, sinp)
    normal = (D[0] * sinp, D[1] * sinp, cosp)
    Lat = ue_dir(1, 0) if along == "x" else ue_dir(0, 1)
    Wl = (a1 - a0) * 100.0
    nc = max(1, math.ceil((Wl - 18.0) / (162.4 - 18.0)))
    w = (Wl + 18.0 * (nc - 1)) / nc
    S = run * 100.0 / cosp + 10.0
    nseq = max(1, math.ceil((S - 15.0) / (324.9 - 15.0)))
    sz = (S + 15.0 * (nseq - 1)) / (324.9 * nseq)
    k = 0
    for i in range(nc):
        ac = a0 + (w / 2 + i * (w - 18.0)) / 100.0
        for j in range(nseq):
            s = j * (324.9 - 15.0) * sz + 2.0                       # cm down the slope from the high edge (2 cm off its wall)
            d = s * cosp / 100.0
            lx, ly = (ac, line + dy * d) if along == "x" else (line + dx * d, ac)
            X, Y = ue(lx, ly)
            z = z_hi - s * sinp
            top = v_add((X, Y, z), normal, 2.4 + 1.5 * (nseq - 1 - j) + 2.0 * (i % 2))
            put_axes("%s_Sheet_%d" % (label, k), rng.choice(PLATE_A), Lat, normal, up_slope, (w / 162.4, 1.0, sz),
                     (0.0, 0.0, 0.0), top, mats=[BM + "MI_BackAlleys_MetalSheet_" + finish])
            items[-1]["folder"] = folder
            k += 1
    for j, (px, py) in enumerate(posts or ()):
        X, Y = ue(px, py)
        dd = (px - line) * dx if dx else (py - line) * dy
        zt = z_hi - (z_hi - z_lo) * max(0.0, min(1.0, abs(dd) / run))
        put("%s_Post%d" % (label, j), CUBE, X - 4.0, Y - 4.0, ground_z(px, py), 0, (0.08, 0.08, (zt - ground_z(px, py)) / 100.0),
            folder=folder, mats=[post_mat or BM + "MI_BackAlleys_MetalSheet_Rust"])
        items[-1]["phys"] = PHYS + "Metal"
    return k


for k, rf in enumerate(_RAW["roofs"]):
    x0, y0, x1, y1 = rf["r"]
    if rf["label"] == "garage roof":                # against the houses on the yard's west side, falling east to posts
        x0 += CW_T + 0.02                             # off the compound wall it rests against
        y1 = min(y1, 83.0)                            # 2.5 m short of the broken wall's drop (63-66, 85.5): you dropped onto its sheets
        posts = [(x1 - 0.15, y0 + 0.4 + i * (y1 - y0 - 0.8) / 4) for i in range(5)] + [(x0 + 0.15, 76.35), (x0 + 0.15, 81.15)]   # and either side of the yard gate, which it spans
        sheet_roof("GarageRoof", (x0, y0, x1, y1), "west", ground_z(x0 + 0.5, y0 + 1) + 330.0, ground_z(x1 - 0.5, y0 + 1) + 255.0,
                   "BackAlleys/Roofs", "Rust", posts=posts)
print("story ground:", _g_n)
