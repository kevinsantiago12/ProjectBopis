# Pass `roofs`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Metal shed roofs with a kisame: sheets, fascia, barge and kisame boards, weatherboards, flashing.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# --- Metal roofs --------------------------------------------------------------------------------------------------------
# User 2026-11-03: "most philippine houses still use metal roofs even in stone houses" ... "also most metal roofs have at
# least a slight slope for water to slide on". Redone the same day from the user's reference photo (a shanty with
# lean-to roofs of mixed rusty and galvanised sheets, metal flashing, timber fascia) and "it shouldnt be just a metal
# slate on a sloped surface, theres usually a "kisame" there" -> "Both" (a flat ceiling with the roof on a frame above
# it, and boarded eaves).
# - Mostly single slopes (5-10 deg) falling toward open ground, never into a taller neighbour; a few wide free-standing
#   houses get two slopes (12-15 deg) and a ridge cap. Never flat (>= 3 deg).
# - Sheets: AsiaSlum's corrugated SM_MetalPlate_A (1.62 m wide, 3.25 m or 1.65 m long, four rust variants), in columns
#   down the slope with an 18 cm side lap (alternate columns 2 cm up) and 15 cm end laps (each upper sheet 1.5 cm over
#   the one below), long and short sheets mixed per column, a slight skew per sheet and a ragged eave.
# - The kisame: the walls stop at the flat ceiling (the concrete lid). The roof sits ROOF_CLEAR above the wall top on
#   a frame; the frame is closed by a timber fascia under every open eave (and an open high edge), level kisame boards
#   from the fascia back to the wall, barge boards under the open sloping edges, and horizontal weatherboards from the
#   wall top up to the kisame or the slope on every side that shows. One paint per house (natural, blue, green, brown:
#   MiddleEast's SM_wooden_beams). Each side is one board scaled to the full height (user, 2026-11-03: "the back of
#   the roof has 5 wood pieces, use one scaled board instead"). A sloping side is sealed up to the sheets ("close the
#   sides ... i mean seal it"): the board reaches the slope's lower end and an SM_Ramp wedge in the same paint fills
#   the triangle under each slope.
# - Galvanised flashing where a high edge meets a taller wall (a strip on the sheets and one up the wall).
# The flat concrete lid stays under the roof as the ceiling.
RF = "BackAlleys/Roofs"
PLATES = {"long": [AS + "SM_MetalPlate_A_001", AS + "SM_MetalPlate_A_002"],
          "short": [AS + "SM_MetalPlate_A_003", AS + "SM_MetalPlate_A_004"]}
PLATE_LEN = {"long": 324.9, "short": 164.9}   # pivot at the top end, centred in X and Y; hangs down local -Z
PLATE_W, PLATE_T = 162.4, 4.8                  # local X, local Y (corrugation depth)
SHEET_UP = 1                                   # which local Y faces up: +1 = +Y
SIDE_LAP, END_LAP = 18.0, 15.0
BEAMS = {"natural": ME + "MiddleEast/SM_wooden_beams_01", "blue": ME + "MiddleEast/SM_wooden_beams_02",
         "green": ME + "MiddleEast/SM_wooden_beams_03", "brown": ME + "MiddleEast/SM_wooden_beams_05"}
BEAM_SIZE = {p: (25.4, 737.6, 34.4 if p.endswith("_05") else 23.8) for p in BEAMS.values()}   # centred pivot, Y long
# The weatherboards and wedges use M_BackAlleys_Boards (create_board_material_ue.py), mapped from world position: the pack's
# wood textures are atlases, and a stretched beam or SM_Ramp's UVs land on the atlas's smeared padding (user: "roof
# textures are busted too", a wedge in grey streaks). The fascia, barge and kisame keep the beams' own UVs.
BOARD_MAT = {BEAMS["natural"]: BM + "MI_BackAlleys_Boards_Natural", BEAMS["blue"]: BM + "MI_BackAlleys_Boards_Blue",
             BEAMS["green"]: BM + "MI_BackAlleys_Boards_Green", BEAMS["brown"]: BM + "MI_BackAlleys_Boards_Brown"}
# Sheet finishes (AssetGen, 2026-11-03; user: "Yes, make them"): our own parent, a drop-in for the plates' slot 0.
# Each roof has a main finish; P_PATCH of its sheets are replacements in another finish, as in the user's photo.
SHEET_MATS = {f: BM + "MI_BackAlleys_MetalSheet_" + f for f in ("Galv", "RedOxide", "Rust")}
SHEET_MIX = (("Galv", 0.5), ("RedOxide", 0.3), ("Rust", 0.2))
P_PATCH = 0.25
FLASH_MAT = BM + "MI_BackAlleys_Flashing"       # world-mapped: the sheet atlas smeared on a cube
ROOF_RNG = random.Random(83)                   # its own sequence
MONO_PITCH, GABLE_PITCH, MIN_PITCH = (5.0, 10.0), (12.0, 15.0), 3.0
P_GABLE = 0.15
ROOF_CLEAR = 42.0                              # sheet underside over the wall top, at the low wall line
OVERHANG = {"low": 0.45, "lateral": 0.25, "high": 0.20}
FASCIA_H, FASCIA_T, SOFFIT_T = 20.0, 3.0, 2.0
BOARD_T = 2.5
FILL_IN = 2.0                                  # weatherboards' outer face, cm behind the wall face
DOWN = {"south": (0, 1), "north": (0, -1), "east": (1, 0), "west": (-1, 0)}   # layout direction a side faces


def roof_kind(c, T):
    if c >= 1e8:
        return "edge"
    if c >= T + 100:
        return "wall"
    if c > T - 60:
        return "flush"
    return "open"


def side_summary(b, side, T):
    iv = side_intervals(b, side, lambda c: (roof_kind(c, T), c))
    kinds = [k for _, _, (k, _) in iv]
    walls = [c for t0, t1, (k, c) in iv if k == "wall" and t1 - t0 >= 0.3]
    kind = "wall" if walls else ("flush" if "flush" in kinds else ("edge" if "edge" in kinds else "open"))
    return kind, (min(walls) if walls else None), iv


def side_line(b, side):
    """(fixed coordinate of the side's line, its axis 'x' or 'y' along it, inward unit (layout))"""
    return {"north": (b["y0"], "x", (0, 1)), "south": (b["y1"], "x", (0, -1)),
            "west": (b["x0"], "y", (1, 0)), "east": (b["x1"], "y", (-1, 0))}[side]




def put_axes(label, asset, X, Y, Z, scale, anchor_local, anchor_world, mats=None, nocoll=False):
    """Places asset with local axes X, Y, Z (right-handed: Z = X x Y) so that the local point anchor_local (unscaled)
    lands on anchor_world."""
    if v_dot(v_cross(X, Y), Z) < 0:
        # Turn X round to keep the axes right-handed. The anchor stays as it is: it names a point of the mesh (a cube's
        # centre is (50, 50, 50) whichever way X points). Negating it put SM_Cube strips one length off (2026-11-03).
        X = (-X[0], -X[1], -X[2])
    off = (0.0, 0.0, 0.0)
    for ax, a, s in ((X, anchor_local[0], scale[0]), (Y, anchor_local[1], scale[1]), (Z, anchor_local[2], scale[2])):
        off = v_add(off, ax, a * s)
    p = v_add(anchor_world, off, -1.0)
    put(label, asset, p[0], p[1], p[2], 0.0, scale, folder=RF, mats=mats, nocoll=nocoll)
    items[-1]["rot"] = axes_rot(X, Y, Z)


def put_board(label, asset, centre, X, Y, Z, dims, mats=None, nocoll=False):
    """A box-like piece by its centre and size (cm) along X, Y, Z: a beam (centred pivot) or SM_Cube (min corner)."""
    if asset == CUBE:
        size, anchor = (100.0, 100.0, 100.0), (50.0, 50.0, 50.0)
    else:
        size, anchor = BEAM_SIZE[asset], (0.0, 0.0, 0.0)
    put_axes(label, asset, X, Y, Z, tuple(dims[i] / size[i] for i in range(3)), anchor, centre, mats, nocoll)


def metal_roof(bid, b):
    T = b["storeys"] * b["sh"]
    sides = {s: side_summary(b, s, T) for s in ("north", "south", "west", "east")}
    dims = {"x": b["x1"] - b["x0"], "y": b["y1"] - b["y0"]}
    best = None
    for low in ("north", "south", "west", "east"):
        lk, hk = sides[low][0], sides[OPP[low]][0]
        if lk == "wall":
            continue
        span = dims["y"] if low in ("north", "south") else dims["x"]
        other = dims["x"] if low in ("north", "south") else dims["y"]
        score = {"open": 3, "edge": 2, "flush": 0}[lk] + {"wall": 2, "flush": 1, "edge": 1, "open": 0}[hk] + \
            (1 if span <= other else 0) + ROOF_RNG.random() * 0.5
        if best is None or score > best[0]:
            best = (score, low, span)
    if best is None:
        return False                                       # walled in on every side: the flat lid stays
    _, low, span = best
    high = OPP[low]
    lk, hk = sides[low][0], sides[high][0]
    gable = lk in ("open", "edge") and hk in ("open", "edge") and span >= 6.0 and ROOF_ROLL() < P_GABLE
    b["eaves"] = [low, high] if gable else [low]           # where it drains to, for the downpipes
    pitch = ROOF_RNG.uniform(*(GABLE_PITCH if gable else MONO_PITCH))
    run = span / 2 if gable else span                     # m from a low wall to the high edge / ridge
    max_rise = 160.0
    if not gable and hk == "wall":
        max_rise = min(max_rise, sides[high][1] - T - ROOF_CLEAR - 40)
    pitch = max(MIN_PITCH, min(pitch, math.degrees(math.atan2(max_rise, run * 100))))
    tanp, cosp, sinp = (f(math.radians(pitch)) for f in (math.tan, math.cos, math.sin))
    beam = BEAMS[ROOF_RNG.choice(sorted(BEAMS))]
    flash = [FLASH_MAT]
    finish = ROOF_RNG.choices([f for f, _ in SHEET_MIX], [w for _, w in SHEET_MIX])[0]

    def zu(d):                                             # sheet underside, d m upslope from a low wall line
        return T + ROOF_CLEAR + tanp * d * 100

    def ovh(side, role):
        k = sides[side][0]
        return {"open": OVERHANG[role], "edge": 0.05, "flush": -0.05, "wall": -0.10}[k]

    lats = [s for s in ("north", "south", "west", "east") if s not in (low, high)]
    lat0, lat1 = sorted(lats, key=lambda s: s in ("east", "south"))   # min side first
    halves = [(low, run)] + ([(high, run)] if gable else [])
    eave_top = {}                                          # side -> top of its weatherboards (cm), for the eaves
    k = 0
    for h, (hlow, hrun) in enumerate(halves):
        dx, dy = DOWN[hlow]                                # layout downslope
        line, axis, _ = side_line(b, hlow)                 # the low wall line
        U = ue_dir(-dx, -dy)                               # UE upslope, horizontal
        Lat = ue_dir(1, 0) if axis == "x" else ue_dir(0, 1)
        o_lo = ovh(hlow, "low")
        o_hi = 0.05 if gable else ovh(OPP[hlow], "high")
        d0, d1 = -o_lo, hrun + o_hi
        a0 = (b["x0"] if axis == "x" else b["y0"]) - ovh(lat0, "lateral")
        a1 = (b["x1"] if axis == "x" else b["y1"]) + ovh(lat1, "lateral")
        Wl = (a1 - a0) * 100

        def P(d, a, z):                                    # UE point at d m upslope, lateral coordinate a (layout)
            lx, ly = (a, line - dy * d) if axis == "x" else (line - dx * d, a)
            X, Y = ue(lx, ly)
            return (X, Y, z)

        # Sheets.
        up_slope = (U[0] * cosp, U[1] * cosp, sinp)        # along the slope, uphill
        normal = (-U[0] * sinp, -U[1] * sinp, cosp)        # the roof plane's up normal
        nc = max(1, math.ceil((Wl - SIDE_LAP) / (PLATE_W - SIDE_LAP)))
        w = (Wl + SIDE_LAP * (nc - 1)) / nc
        rows_max = 1
        for i in range(nc):
            ac = a0 + (w / 2 + i * (w - SIDE_LAP)) / 100 + ROOF_RNG.uniform(-0.012, 0.012)
            lo = d0 - ROOF_RNG.uniform(0.0, 0.05)          # ragged eave
            S = (d1 - lo) * 100 / cosp
            best_seq = None
            for _ in range(8):                             # long and short sheets; the mix closest to true length
                seq, rem = [], S
                while rem > 0:
                    pick = "long" if rem > 260 or (rem > 175 and ROOF_RNG.random() < 0.5) else "short"
                    seq.append(pick)
                    rem -= PLATE_LEN[pick] - END_LAP
                sz = S / (sum(PLATE_LEN[p] for p in seq) - END_LAP * (len(seq) - 1))
                if best_seq is None or abs(sz - 1) < abs(best_seq[1] - 1):
                    best_seq = (seq, sz)
            seq, sz = best_seq
            rows_max = max(rows_max, len(seq))
            s = 0.0                                        # cm down the slope from the high end
            for j, pick in enumerate(seq):
                d = d1 - s * cosp / 100
                lift = PLATE_T / 2 + 1.5 * (len(seq) - 1 - j) + 2.0 * (i % 2)
                top = v_add(P(d, ac, zu(d)), normal, lift)
                skew = ROOF_RNG.uniform(-1.0, 1.0)
                Zs = v_rot(up_slope, normal, skew)         # local +Z points uphill (the sheet hangs down -Z)
                Xs = v_rot(Lat, normal, skew)
                Ys = normal if SHEET_UP > 0 else (-normal[0], -normal[1], -normal[2])
                f = finish if ROOF_RNG.random() >= P_PATCH else \
                    ROOF_RNG.choice([g for g, _ in SHEET_MIX if g != finish])
                put_axes("Roof_%s_%d" % (bid, k), ROOF_RNG.choice(PLATES[pick]), Xs, Ys, Zs,
                         (w / PLATE_W, 1.0, sz), (0.0, 0.0, 0.0), top, mats=[SHEET_MATS[f]])
                k += 1
                s += (PLATE_LEN[pick] - END_LAP) * sz
        # Fascia and kisame under an open eave (this half's low edge), and under an open high edge (single slope).
        edges = [(hlow, d0, -1)] if sides[hlow][0] == "open" else []
        if not gable and sides[high][0] == "open":
            edges.append((high, d1, 1))
        for side, de, sgn in edges:
            ztop = zu(de) - 1
            n = max(1, math.ceil(Wl / 700))
            for m in range(n):
                am = a0 + (m + 0.5) * (a1 - a0) / n
                put_board("Fascia_%s_%s%d" % (bid, side[0].upper(), m), beam,
                          P(de - sgn * FASCIA_T / 200, am, ztop - FASCIA_H / 2), U, Lat, (0, 0, 1),
                          (FASCIA_T, Wl / n, FASCIA_H))
                width = abs(de) * 100 - FASCIA_T if sgn < 0 else (de - hrun) * 100 - FASCIA_T
                dm = (de - sgn * FASCIA_T / 100) / 2 if sgn < 0 else (hrun + de - FASCIA_T / 100) / 2
                put_board("Kisame_%s_%s%d" % (bid, side[0].upper(), m), beam,
                          P(dm, am, ztop - FASCIA_H + SOFFIT_T / 2), U, Lat, (0, 0, 1), (width, Wl / n, SOFFIT_T))
            eave_top[side] = ztop - FASCIA_H
        if hlow not in eave_top:
            eave_top[hlow] = zu(0) - 1
        if not gable and high not in eave_top:
            eave_top[high] = zu(hrun) - 1
        # Barge boards under the open sloping edges.
        for lat, a in ((lat0, a0 - 0.01 + FASCIA_T / 200), (lat1, a1 + 0.01 - FASCIA_T / 200)):
            if sides[lat][0] != "open":
                continue
            db = hrun if gable else d1                     # two slopes: the pair meet at the ridge, no overlap
            dm = (d0 + db) / 2
            c = v_add(P(dm, a, zu(dm)), normal, -(1 + FASCIA_H / 2))
            put_board("Barge_%s_%s%d" % (bid, lat[0].upper(), h), beam, c, Lat, up_slope, normal,
                      (FASCIA_T, (db - d0) * 100 / cosp, FASCIA_H))
        # Flashing where the high edge meets a taller wall: a strip on the sheets and one up the wall.
        if not gable and sides[high][0] == "wall":
            am = (a0 + a1) / 2
            sheet_top = PLATE_T + 1.5 * (rows_max - 1) + 2.0 + 0.6
            # The strip runs from 25 cm down the sheets to 2 cm off the wall, over the 10 cm the roof stops short, and
            # meets the upstand (the rebuild captures showed a 9 cm gap when it stopped at the sheet ends).
            dc = (d1 - 0.25 + hrun - 0.02) / 2
            put_board("Flash_%s_S" % bid, CUBE, v_add(P(dc, am, zu(dc)), normal, sheet_top + 0.5), up_slope, Lat,
                      normal, ((hrun - 0.02 - (d1 - 0.25)) * 100 / cosp, Wl, 1.0), mats=flash, nocoll=True)
            zb = zu(hrun - 0.02) + sheet_top - 1
            put_board("Flash_%s_W" % bid, CUBE, P(hrun - 0.015, am, zb + 12.5), U, Lat, (0, 0, 1), (1.0, Wl, 25.0),
                      mats=flash, nocoll=True)
        if gable and h == 0:                               # ridge cap over both halves' top rows
            put_board("Ridge_%s" % bid, CUBE, P(hrun, (a0 + a1) / 2, zu(hrun) + PLATE_T + 1.5 * 3 + 2 + 1.5),
                      U, Lat, (0, 0, 1), (36.0, Wl + 4, 1.5), mats=flash, nocoll=True)

    # Weatherboards between the wall tops and the kisame / the slope, on every side that shows.
    def lat_top(side, t):
        """Underside of the sheets over the lateral side's point t (m from its min corner), minus 1 cm."""
        line_l, axis_l, _ = side_line(b, side)
        c = (b["x0"] if axis_l == "x" else b["y0"]) + t
        ds = []
        for hlow, _ in halves:
            ln, ax, _ = side_line(b, hlow)
            dx, dy = DOWN[hlow]
            ds.append(-(c - ln) * (dx if ax == "y" else dy))
        return zu(min(ds)) - 1

    for side in ("north", "south", "west", "east"):
        line_s, axis_s, (ix, iy) = side_line(b, side)
        base = b["x0"] if axis_s == "x" else b["y0"]
        length = dims[axis_s]
        Run = ue_dir(1, 0) if axis_s == "x" else ue_dir(0, 1)
        In = ue_dir(ix, iy)
        inset = line_s + (ix + iy) * (FILL_IN + BOARD_T / 2) / 100

        def plank(row, r0, r1, z0, z1):                    # a level board over r0..r1 (m along the side), z0..z1 cm
            tm = (r0 + r1) / 2
            lx, ly = (base + tm, inset) if axis_s == "x" else (inset, base + tm)
            X, Y = ue(lx, ly)
            put_board("Board_%s_%s%d_%d" % (bid, side[0].upper(), n_, row), beam, (X, Y, (z0 + z1) / 2), In, Run,
                      (0, 0, 1), (BOARD_T, (r1 - r0) * 100, z1 - z0), mats=[BOARD_MAT[beam]])

        for n_, (t0, t1, (kind, _)) in enumerate(sides[side][2]):
            if kind in ("wall", "edge") or t1 - t0 < 0.05:
                continue
            ta = t0 + (0.03 if t0 < 1e-6 else 0.0)
            tb = t1 - (0.03 if abs(t1 - length) < 1e-6 else 0.0)
            zb = T - 8
            if side in eave_top:                           # an eave or a high edge: one board up to the level top
                if eave_top[side] - zb >= 3:
                    plank(0, ta, tb, zb, eave_top[side])
                continue
            # A sloping side: the board up to the slope's lower end, then a wedge under each slope, its top 1 cm under
            # the sheets. A run that starts partway up a slope gets a level filler under its wedge.
            ends = (lat_top(side, ta), lat_top(side, tb))
            tm = ta if ends[0] > ends[1] else tb           # the high end, or the ridge on two slopes
            if gable:
                tr = sum(side_line(b, hl)[0] for hl, _ in halves) / 2 - base
                tm = tr if ta + 0.05 < tr < tb - 0.05 else tm
            zlev = min(ends)
            plank(0, ta, tb, zb, zlev)
            row = 1
            for p0, p1 in ((ta, tm), (tm, tb)):
                if p1 - p0 < 0.05:
                    continue
                h0, h1 = lat_top(side, p0), lat_top(side, p1)
                zw = min(h0, h1)
                if zw - zlev > 1:
                    plank(row, p0, p1, zlev, zw)
                    row += 1
                if max(h0, h1) - zw < 1:
                    continue
                hi, lo = (p1, p0) if h1 > h0 else (p0, p1)
                lx, ly = (base + hi, inset) if axis_s == "x" else (inset, base + hi)
                X, Y = ue(lx, ly)
                # The ramp lies on its side: local +Y up (the tall edge), local +Z from the tall end down the slope. Its
                # triangle faces' grain runs along local Z; stood upright it read as vertical streaks in a capture.
                Zw = tuple(c * (1 if lo > hi else -1) for c in Run)
                put_axes("Wedge_%s_%s%d_%d" % (bid, side[0].upper(), n_, row), RAMP, In, (0.0, 0.0, 1.0), Zw,
                         (BOARD_T / 100, (max(h0, h1) - zw) / 100, p1 - p0), (50.0, 0.0, 0.0), (X, Y, zw),
                         mats=[BOARD_MAT[beam]])
                row += 1
    return True


def ROOF_ROLL():
    return ROOF_RNG.random()


_roofs = {"metal": 0, "flat": 0}
for bid, b in BLOCKS.items():
    ZB = b.get("z", 0.0)
    if b["roof"] == "metal" and metal_roof(bid, b):
        _roofs["metal"] += 1
    elif b["roof"] != "terrace":
        _roofs["flat"] += 1
ZB = 0.0
print("roofs:", _roofs)
