# Pass `story_interiors` (story levels; levels/linear_slums.py). The buildings the player enters, 2026-11-08: rooms per storey
# from the layout's areas, walls between them with the layout's openings, windows on the outside walls that can be seen,
# slabs with stairwells and the one-way floor hole, stairs, rails, the bodega's mezzanine, the trap house's terrace and plank,
# lights, and roofs from the street houses' roof builder (metal_roof), so they match the street.
# Walls are boxes in world-mapped materials (the CHB, paint, board families), so a box reads as the street houses' tiles,
# and an opening is cut at the layout's exact place and size. Every edge between two cells of one storey is one of:
#   exterior (on the building's edge, 20 cm in from it), party (between two buildings: built once), interior wall (a room
#   against a gallery, void or room of another kind, 15 cm), partition (room | room: CHB 15 cm, or plywood where a cell or
#   a plywood building is on either side), rail (a gallery against a void), parapet (a roof terrace's edge), or nothing.
# Needs: ENTERED, WOODEN, FLOOR_T, LAYOUT_RAW, AREAS (levels/linear_slums.py), _box, sheet_roof, ground_z (story_ground),
# metal_roof (roofs), window_grille, shuffle_bag (walls), put, put_axes.
IR = "BackAlleys/Interiors"
INT_RNG = random.Random(409)
WALL_T, PART_T, INNER_T, PLY_T, BOARD_W_T = 0.20, 0.15, 0.15, 0.012, 0.12
SKIN = 0.01                                     # m: a room's paint over a wall of another material
OPEN_H = {"door": 240.0, "door1": 220.0, "knock": 260.0, "garage": 280.0, "front": 255.0, "drop": 225.0}
WIN_W, WIN_SILL, WIN_TOP = 1.12, 92.0, 220.0    # the Favela window tile's opening, so window_grille fits it
PAINTS_IN = ("Cream", "White", "Mint", "SkyBlue", "Peach", "Pink", "Yellow", "AppleGreen", "Lavender")
# Hollow blocks on boxes: the user's texture, world-mapped (create_hollow_world_material_ue.py). User 2026-11-08: "you are also using
# the wrong hollowblock material" (it was the procedural MI_BackAlleys_CHB_Bare).
CHB_BARE, CHB_CONC = BM + "MI_BackAlleys_HollowBlocks_World", BM + "MI_BackAlleys_CHB_Concrete"
# Bare plywood is the user's texture, world-mapped (user 2026-11-13: "I added a Plywood texture on the content folder. Use that instead
# of whatever you are using"): T_Plywood_BaseColor / _Normal_DX on the hollow blocks' world material, 122 cm a repeat. It stands for
# both the old Natural and Weathered; the green-painted sheets stay.
PLYWOOD = BM + "MI_BackAlleys_Plywood_World"
PLY_MATS = [PLYWOOD, PLYWOOD, BM + "MI_BackAlleys_Ply_GreenPaint"]
# The studs behind plywood: AsiaSlum's frame timber (T_WoodFrame_A_001, grain along its length), world-mapped 60 x 250 cm so a 10 cm stud
# reads as one length of wood (user 2026-11-13: "Give them timber"; the plank texture squeezed onto a stud showed as blocks).
TIMBER = BM + "MI_BackAlleys_Timber_World"
BOARDS = [BM + "MI_BackAlleys_Boards_" + k for k in ("Natural", "Blue", "Green", "Brown")]
FLOOR_FIN = {"concrete": GM + "ConcreteA", "old": GM + "ConcreteOld", "new": GM + "ConcreteNew"}
RAIL = AS + "SM_Rail_A_001"
RAIL_SX, RAIL_SZ, RAIL_X0, RAIL_Z0 = 300 / 302.0, 105 / 177.9, 2.5, 3.9
CELLS = ("N1", "N2", "S1C", "S2C", "S3C", "S4C")
_draw_paint_in = shuffle_bag(INT_RNG, PAINTS_IN)
_draw_paint_out = shuffle_bag(INT_RNG, PAINT_COLOURS)

_raw = LAYOUT_RAW
_bld = {e["id"]: dict(e) for e in ENTERED}
_bld["TRAP"]["storeys"] = tuple(_bld["TRAP"]["storeys"]) + (WOODEN["storeys"][0],)     # the wooden storey is the trap house's third, on part of it
for _b in _bld.values():
    _b["lv"] = [_b["ground"] + FLOOR_T]
    for h_ in _b["storeys"]:
        _b["lv"].append(_b["lv"][-1] + h_)
_n = {"walls": 0, "openings": 0, "windows": 0, "slabs": 0, "stairs": 0, "rails": 0, "lights": 0, "roofs": 0}

# The fitted baseline (user 2026-11-09, of section 4's row houses: "the doorways are two doors wide, I need it only 1 door wide except
# for the broken down wall"; "I also need sils or door frames, see if we have any assets that would work. You have been adding Cubes to
# fill the space, we should be using what assets we have instead"; "I changed the stairs at the bottom of the last section, conform to
# that when making stairs for section 4"). In the buildings a level lists in FITTED:
#   - a door is one leaf wide: a hole the size of Favela's wooden jamb (SM_Door_Jamb_01, 110 x 218 cm outside, 18 deep), the jamb in
#     it as deep as the wall, at one of three places along the layout's 2.25 m opening. Knocked-through walls stay wide. Each door's
#     slot goes to Saved/<level>/doors.json for the swinging doors.
#   - a window sits in Favela's wooden window (SM_windows_01, 110 x 133 cm: frame, mullions, a dark sill outside on its local -Y and a
#     wooden board inside), the two jalousie planes in it, the ground floor's grille moved out past the sill;
#   - a stair is the user's (TRAP_Stair3 as they rebuilt it in the map): the kit's flights at 0.538 x 1.015 (27 cm treads, 19.4 cm
#     risers, 36 degrees), each one step (of six) down the one above, anchored at the top, as many as reach the floor (the lowest
#     sinks into it).
FITTED = getattr(LEVEL, "FITTED", ())
DOOR_KINDS = ("door", "door1")
DOOR_W, DOOR_H = 1.10, 218.0
JAMB = FV + "SM_Door_Jamb_01"
WIN_FRAME = FV + "SM_windows_01"
FLIGHT_RUN, FLIGHT_RISE, FLIGHT_STEP = 300.0 * 0.538, 114.9 * 1.015, 5.0 / 6.0
_doors = []
_n.update({"jambs": 0, "frames": 0, "rubble": 0})


def _door_span(f, axis, c, a, b):
    """Where a one-leaf door goes in the layout's opening [a, b] (m): near one end, the middle, or the other end, picked from its place."""
    if b - a <= DOOR_W + 0.3:
        return ((a + b) / 2 - DOOR_W / 2, (a + b) / 2 + DOOR_W / 2)
    s_ = (a + 0.1, (a + b) / 2 - DOOR_W / 2, b - 0.1 - DOOR_W)[int(round(a * 4.0 + c * 7.0 + f * 3.0 + (axis == "y"))) % 3]
    return (s_, s_ + DOOR_W)


def _jambs(label, bid, f, axis, c, ops, n0, n1, sill_z):
    """Favela's jamb in each one-leaf door of a fitted building, as deep as the wall and 1 cm proud of each face; its slot, for the doors."""
    if bid not in FITTED:
        return
    for i, (a, b, k_) in enumerate(ops):
        if k_ not in DOOR_KINDS:
            continue
        X, Y = _face_point(axis, c, (a + b) / 2, (n0 + n1) / 2)
        yaw = 90.0 if axis == "x" else 180.0                 # local X along +t: east (UE +Y) or south (UE -X)
        put("%s_Jamb%d" % (label, i), JAMB, X, Y, sill_z, yaw, ((b - a) * 100.0 / 110.0, ((n1 - n0) * 100.0 + 2.0) / 18.0, 1.0), folder=IR)
        items[-1]["phys"] = PHYS + "Wood"
        _doors.append({"label": "%s_Door%d" % (label, i), "loc": [round(X, 1), round(Y, 1), round(sill_z, 1)], "yaw": yaw,
                       "width": round((b - a) * 100.0, 1), "height": DOOR_H, "wall": round((n1 - n0) * 100.0, 1), "bid": bid, "f": f})
        _n["jambs"] += 1


# Knocked-through walls in a fitted building (user 2026-11-09: "do we have rubble we can use on the broken through wall?", "around the door
# frame i mean", "Yes, dress them"). No pack has a broken-edge wall mesh. Favela's SM_BrickWallCorner_01 is a mesh decal (translucent) made
# for a building's outside corner: plaster broken back to the brick. Its apex is its origin, the wall it wraps lies in its -X -Y quarter,
# one leg 161 cm along -X (on the face whose normal is +Y), one 194 cm along -Y (on the face whose normal is +X), 491 cm up +Z. It goes
# down both sides and along the top of each knocked-through hole, on both faces: KNOCK_LEG along the wall, half the wall's depth round
# into the hole, 1 cm off both faces (translucent: never on a face). At the foot, one of AsiaSlum's debris heaps on each side.
RB = "BackAlleys/Rubble"
CORNER = FV + "Decals/SM_BrickWallCorner_01"
# White, not the pack's red brick (user 2026-11-09: "make it white not red"): an instance of its M_Corner_decal_01 with Favela's
# T_Wall_white_01_BC as its colour (parameter BC); the brick's normal map and the broken-edge mask stay.
CORNER_MAT = BM + "MI_BackAlleys_CornerDecal_White"
RUBBLE = [AS + "SM_Debris_A_00%d" % i for i in (1, 2, 3)]
RUBBLE_R = 88.0                                   # cm: the heaps' furthest reach from their pivot (bounds)
KNOCK_LEG, KNOCK_UP = 70.0, 45.0                  # cm of broken plaster along the wall beside the hole, and over it
KNOCK_SHOWN = 0.6                                 # of a leg, the part where the decal's mask shows (its ragged edge), seen in the map


def _corner_decal(label, P, A_, B_, lx, ly, lz):
    """The corner decal with its +X along A_ and +Y along B_ (the two faces' normals), +Z = A_ x B_, its apex 1 cm off both faces at P:
    lx cm along -X (on face B_), ly along -Y (on face A_), lz along +Z."""
    put_axes(label, CORNER, A_, B_, v_cross(A_, B_), (lx / 161.2, ly / 193.5, lz / 491.2), (0.0, 0.0, 0.0),
             (P[0] + A_[0] + B_[0], P[1] + A_[1] + B_[1], P[2] + A_[2] + B_[2]), mats=[CORNER_MAT], nocoll=True)
    items[-1]["folder"] = RB
    items[-1]["noshadow"] = True


def _knocks(label, bid, f, axis, c, ops, n0, n1, sill_z, ta, tb):
    """ta, tb: the wall's ends (m), so nothing runs past them."""
    if bid not in FITTED:
        return
    tv = (0.0, 1.0, 0.0) if axis == "x" else (-1.0, 0.0, 0.0)       # UE: along the wall (+t)
    nv = (-1.0, 0.0, 0.0) if axis == "x" else (0.0, 1.0, 0.0)       # UE: across it (+n)
    half = (n1 - n0) * 50.0
    for i, (a, b, k_) in enumerate(ops):
        if k_ != "knock":
            continue
        top = sill_z + OPEN_H[k_]
        rng = random.Random(int(round(a * 1000.0 + c * 100.0 + f * 7.0)))
        leg_a = max(0.0, min(KNOCK_LEG, (a - ta) * 100.0 - 10.0))   # cm of wall beside each side of the hole, 10 short of its end
        leg_b = max(0.0, min(KNOCK_LEG, (tb - b) * 100.0 - 10.0))
        for s_n, n_f in ((-1.0, n0), (1.0, n1)):
            no = tuple(s_n * v for v in nv)                          # this face's normal
            for s_t, t_e in ((1.0, a), (-1.0, b)):                  # each side of the hole; its reveal faces s_t * tv
                rv_ = tuple(s_t * v for v in tv)
                X_, Y_ = (no, rv_) if v_cross(no, rv_)[2] > 0 else (rv_, no)
                leg = leg_a if s_t > 0 else leg_b
                lx, ly = (half, leg) if X_ is no else (leg, half)
                P = _face_point(axis, c, t_e, n_f) + (sill_z,)
                _corner_decal("%s_Knock%d_%s%s" % (label, i, "N" if s_n > 0 else "S", "A" if s_t > 0 else "B"), P, X_, Y_, lx, ly, top - sill_z)
            # over the hole: the face and the soffit (normal down); +Z runs along the top from whichever end it points away from.
            # (2026-11-09, user: "there a way to fix the top corners?") It runs on past both sides as far as the side strips reach,
            # so the squares over them aren't bare: one piece round the top corners. Past the hole its soffit leg is inside the wall.
            # As far as their plaster shows (KNOCK_SHOWN of the leg), not their whole leg: the full 70 cm stood out like a lintel.
            down = (0.0, 0.0, -1.0)
            Z_ = v_cross(no, down)
            run_a, run_b = leg_a * KNOCK_SHOWN, leg_b * KNOCK_SHOWN
            t_e = (a - run_a / 100.0) if (Z_[0] * tv[0] + Z_[1] * tv[1]) > 0 else (b + run_b / 100.0)
            P = _face_point(axis, c, t_e, n_f) + (top,)
            _corner_decal("%s_Knock%d_%sTop" % (label, i, "N" if s_n > 0 else "S"), P, no, down, half, KNOCK_UP,
                          (b - a) * 100.0 + run_a + run_b)
            # a heap at its foot, clear of the wall
            k = rng.uniform(0.5, 0.7)
            t_m = rng.uniform(a + 0.45, b - 0.45)
            X, Y = _face_point(axis, c, t_m, n_f + s_n * (RUBBLE_R * k + 3.0) / 100.0)
            put("%s_Knock%d_%sRubble" % (label, i, "N" if s_n > 0 else "S"), rng.choice(RUBBLE), X, Y, sill_z, rng.uniform(0.0, 360.0),
                (k, k, k), folder=RB)
            items[-1]["phys"] = PHYS + "Concrete"
            _n["rubble"] += 1


def _void_edges(bid, f):
    """The edges of storey f's voids (stairwells, the floor hole), as wall lines: (axis, c, t0, t1)."""
    out = []
    for cl in _cells(bid, f):
        if cl["kind"] == "void":
            x0, y0, x1, y1 = cl["r"]
            out += [("y", x0, y0, y1), ("y", x1, y0, y1), ("x", y0, x0, x1), ("x", y1, x0, x1)]
    return out


def _inner_ends(bid, f, axis, c, ta, tb):
    """An inside wall's ends, pulled back where one lies on the building's edge: to the outside wall's inner face (WALL_T in), or a
    party wall's (WALL_T / 2: the ground floor's party walls are centred on the edge)."""
    R = _bld[bid]["rect"]
    lo, hi = (R[0], R[2]) if axis == "x" else (R[1], R[3])

    def cut(t_end, d):
        if abs(t_end - (lo if d < 0 else hi)) > 0.005:
            return 0.0
        pt = (t_end + d * 0.3, c) if axis == "x" else (c, t_end + d * 0.3)
        return WALL_T / 2 if f == 0 and _other_building(bid, *pt) else WALL_T
    return ta + cut(ta, -1.0), tb - cut(tb, 1.0)


def _in(r, lx, ly, pad=0.0):
    return r[0] - pad < lx < r[2] + pad and r[1] - pad < ly < r[3] + pad


def _inside(r, R, pad=0.01):
    return r[0] >= R[0] - pad and r[1] >= R[1] - pad and r[2] <= R[2] + pad and r[3] <= R[3] + pad


def _cells(bid, f):
    """The layout's areas on storey f inside building bid, plus closed cells for what no area covers."""
    R = _bld[bid]["rect"]
    out = []
    for a in _raw["areas"]:
        r = (a["x0"], a["y0"], a["x1"], a["y1"])
        if a["f"] == f and _inside(r, R) and not (bid == "BOD" and a["id"] == "MEZZ"):
            out.append({"id": a["id"], "kind": a["kind"], "r": r, "label": a["label"]})
    if f >= len(_bld[bid]["storeys"]):
        return []
    if f == 2 and bid == "TRAP":
        return out                                  # the +8 roof: the wooden rooms and the terraces cover it
    xs = sorted({R[0], R[2]} | {c["r"][0] for c in out} | {c["r"][2] for c in out})
    ys = sorted({R[1], R[3]} | {c["r"][1] for c in out} | {c["r"][3] for c in out})
    free = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            mx, my = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if R[0] < mx < R[2] and R[1] < my < R[3] and not any(c["r"][0] < mx < c["r"][2] and c["r"][1] < my < c["r"][3] for c in out):
                free.append((xs[i], ys[j], xs[i + 1], ys[j + 1]))
    for k, r in enumerate(_merge(free)):
        out.append({"id": "%s_X%d_%d" % (bid, f, k), "kind": "closed", "r": r, "label": "closed"})
    return out


def _merge(rects):
    """Merge rectangles that share a whole edge, until none do."""
    rects = list(rects)
    changed = True
    while changed:
        changed = False
        for i in range(len(rects)):
            for j in range(i + 1, len(rects)):
                a, b = rects[i], rects[j]
                m = None
                if abs(a[1] - b[1]) < 1e-6 and abs(a[3] - b[3]) < 1e-6 and (abs(a[2] - b[0]) < 1e-6 or abs(b[2] - a[0]) < 1e-6):
                    m = (min(a[0], b[0]), a[1], max(a[2], b[2]), a[3])
                elif abs(a[0] - b[0]) < 1e-6 and abs(a[2] - b[2]) < 1e-6 and (abs(a[3] - b[1]) < 1e-6 or abs(b[3] - a[1]) < 1e-6):
                    m = (a[0], min(a[1], b[1]), a[2], max(a[3], b[3]))
                if m:
                    rects[i] = m
                    del rects[j]
                    changed = True
                    break
            if changed:
                break
    return rects


def _at_cell(cells, lx, ly):
    """The cell at (lx, ly) for walls: a room, gallery or closed cell before a void inside it."""
    hit = [c for c in cells if c["r"][0] < lx < c["r"][2] and c["r"][1] < ly < c["r"][3]]
    for kind in ("room", "closed", "open", "off", "void"):
        for c in hit:
            if c["kind"] == kind:
                return c
    return None


def _other_building(bid, lx, ly):
    for o, e in _bld.items():
        if o != bid and _in(e["rect"], lx, ly):
            return o
    return None


def _is_terrace(bid, f, c):
    return c is not None and c["kind"] == "open" and bid == "TRAP" and f == 2


def _ply_side(bid, f, c):
    return c is not None and (bid == "PLY" or c["id"] in CELLS or (bid == "TRAP" and f == 2))


# --- Materials ------------------------------------------------------------------------------------------------------------
_ext_house = {}
_room_fin = {}


def _ext_mat(bid, f, side, t_mid, has_open):
    """The outside of a building's wall at storey f."""
    if bid == "ROW":                                 # four houses, 6 m each: one colour per house or bare concrete
        h = int((t_mid - 60.0) // 6.0) if side in ("north", "south") else 3
        if h not in _ext_house:
            _ext_house[h] = BM + "MI_BackAlleys_PaintedWall_" + _draw_paint_out() if INT_RNG.random() < 0.6 else CHB_CONC
        return _ext_house[h]
    if bid == "TRAP":
        if f == 0:
            return CHB_CONC if has_open else CHB_BARE     # hollow blocks only on faces with no door or window
        if f == 1:
            if "f1" not in _ext_house:
                _ext_house["f1"] = BM + "MI_BackAlleys_PaintedWall_" + _draw_paint_out()
            return _ext_house["f1"]
        return _wood_mat()
    return CHB_BARE if bid == "PASS" else CHB_CONC


def _wood_mat():
    if "wood" not in _ext_house:
        _ext_house["wood"] = INT_RNG.choice(BOARDS)
    return _ext_house["wood"]


def _fin(bid, f, c):
    """A room's inside walls."""
    if c is None or c["kind"] in ("void", "off"):
        return None
    key = c["id"]
    if key not in _room_fin:
        if c["kind"] == "closed":
            _room_fin[key] = CONC
        elif bid == "ROW" or (bid == "TRAP" and f == 1) or c["id"] == "GUARD":
            _room_fin[key] = BM + "MI_BackAlleys_PaintedWall_" + _draw_paint_in()
        elif bid == "TRAP" and f == 2 or bid == "PLY" or c["id"] in CELLS:
            _room_fin[key] = PLY_MATS[0] if bid == "PLY" else PLY_MATS[1]
        else:
            _room_fin[key] = CHB_BARE
    return _room_fin[key]


# --- Geometry -------------------------------------------------------------------------------------------------------------
def _wbox(label, axis, c, t0, t1, n0, n1, z0, z1, mats, folder=IR, **kw):
    """A box on a wall line: axis 'x' is the line y = c (t along x, n along +y), 'y' the line x = c (t along y, n along +x)."""
    if t1 - t0 < 0.005 or n1 - n0 < 0.0005 or z1 - z0 < 0.5:
        return None
    if axis == "x":
        return _box(label, t0, c + n0, t1, c + n1, z0, z1, folder, mats, **kw)
    return _box(label, c + n0, t0, c + n1, t1, z0, z1, folder, mats, **kw)


def _solid_parts(t0, t1, z0, z1, holes):
    """[t0, t1] x [z0, z1] less the holes (a, b, za, zb): rectangles (ta, tb, za, zb)."""
    cuts = sorted({t0, t1} | {max(t0, min(t1, h[0])) for h in holes} | {max(t0, min(t1, h[1])) for h in holes})
    out = []
    for ta, tb in zip(cuts, cuts[1:]):
        if tb - ta < 1e-4:
            continue
        zs = [(z0, z1)]
        for a, b, za, zb in holes:
            if a < tb - 1e-4 and b > ta + 1e-4:
                nz = []
                for p, q in zs:
                    if zb <= p or za >= q:
                        nz.append((p, q))
                        continue
                    if za > p:
                        nz.append((p, za))
                    if zb < q:
                        nz.append((zb, q))
                zs = nz
        for p, q in zs:
            if q - p > 0.5:
                if out and abs(out[-1][1] - ta) < 1e-6 and abs(out[-1][2] - p) < 1e-6 and abs(out[-1][3] - q) < 1e-6:
                    out[-1] = (out[-1][0], tb, p, q)
                else:
                    out.append((ta, tb, p, q))
    return out


def _openings(f, axis, c, t0, t1):
    out = []
    for o in _raw["openings"]:
        (ax, ay), (bx, by) = o["a"], o["b"]
        if o["f"] != f:
            continue
        if axis == "x" and abs(ay - c) < 0.02 and abs(by - c) < 0.02:
            a, b = min(ax, bx), max(ax, bx)
        elif axis == "y" and abs(ax - c) < 0.02 and abs(bx - c) < 0.02:
            a, b = min(ay, by), max(ay, by)
        else:
            continue
        if a < t1 - 0.01 and b > t0 + 0.01:
            out.append((a, b, o["k"]))
    return out


def _ply_wall(label, axis, c, t0, t1, n_c, z0, z1, holes, mat, studs_n, whole=False):
    """Plywood: sheets (1.22 x 2.44 m) on 5 x 10 cm studs on the studs_n side, holes cut. whole: one box per solid stretch between the
    holes and studs at the two ends only (user 2026-11-13, of the covered alley's plywood rooms: "use less boards on the Alley section";
    the world-mapped plywood doesn't need a box per sheet)."""
    k = 0
    for ta, tb, za, zb in _solid_parts(t0, t1, z0, z1, holes):
        nw = 1 if whole else max(1, math.ceil((tb - ta) / 1.22 - 1e-6))
        nh = 1 if whole else max(1, math.ceil((zb - za) / 244.0 - 1e-6))
        for i in range(nw):
            for j in range(nh):
                s0, s1 = ta + (tb - ta) * i / nw, ta + (tb - ta) * (i + 1) / nw
                h0, h1 = za + (zb - za) * j / nh, za + (zb - za) * (j + 1) / nh
                lap = 0.004 if i < nw - 1 else 0.0     # sheets lap 4 mm (the tiles' rule: never butt at fractional sizes)
                _wbox("%s_Ply%d" % (label, k), axis, c, s0, s1 + lap, n_c - PLY_T / 2 + (0.0006 if i % 2 else 0.0),
                      n_c + PLY_T / 2 + (0.0006 if i % 2 else 0.0), h0, h1 + (0.4 if j < nh - 1 else 0.0), [mat])
                items[-1]["phys"] = PHYS + "Wood"
                k += 1
    # studs at the sheet joints and ends, behind the sheets, not across the holes
    n0 = n_c + studs_n * PLY_T / 2
    n1 = n0 + studs_n * 0.05
    m = 1 if whole else max(1, math.ceil((t1 - t0) / 1.22 - 1e-6))
    for i in range(m + 1):
        t = min(max(t0 + (t1 - t0) * i / m, t0 + 0.05), t1 - 0.05)
        if any(h[0] - 0.06 < t < h[1] + 0.06 for h in holes):
            continue
        _wbox("%s_Stud%d" % (label, i), axis, c, t - 0.05, t + 0.05, min(n0, n1), max(n0, n1), z0, z1, [TIMBER])
        items[-1]["phys"] = PHYS + "Wood"


def _wall(label, axis, c, t0, t1, n0, n1, z0, z1, holes, core, skins=()):
    """A box wall with holes, in `core`, and paint skins (n_face, outward sign, material) over it."""
    k = 0
    for ta, tb, za, zb in _solid_parts(t0, t1, z0, z1, holes):
        _wbox("%s_%d" % (label, k), axis, c, ta, tb, n0, n1, za, zb, [core])
        for s, (nf, sgn, mat) in enumerate(skins):
            if mat and mat != core:
                a_, b_ = (nf, nf + sgn * SKIN) if sgn > 0 else (nf - SKIN, nf)
                _wbox("%s_%d_Skin%d" % (label, k, s), axis, c, ta, tb, a_, b_, max(za, z0 + 0.0), zb, [mat])
        k += 1
    _n["walls"] += 1


def _side_of(axis, sgn):
    """The side a face looks toward: on line axis 'x' (y = c), +n is south."""
    return ("south" if sgn > 0 else "north") if axis == "x" else ("east" if sgn > 0 else "west")


def _face_point(axis, c, t, n):
    """UE point of layout (t, n) on a wall line."""
    return ue(t, c + n) if axis == "x" else ue(c + n, t)


def _window(label, axis, c, t_mid, n_face, sgn, floor_z, thick, ground_floor, fitted=False):
    """A jalousie window in a hole already cut: the plane outside (2 cm in), a twin facing in, a grille on the ground floor. Fitted:
    in Favela's wooden window, its outside sill on local -Y, 1 cm proud (2026-11-09: AsiaSlum's security cages, which the user put on
    the row houses, stand 1.1 cm off the wall), the wooden board 9 cm into the room."""
    side = _side_of(axis, sgn)
    # t grows east on a line of constant y (UE +Y), south on a line of constant x (UE -X)
    t_dir = (0.0, 1.0) if axis == "x" else (-1.0, 0.0)
    along = 1.0 if (RUN[side][0] * t_dir[0] + RUN[side][1] * t_dir[1]) > 0 else -1.0
    t_start = t_mid - along * 1.12                 # the Favela tile's start: its opening is centred 112 cm along
    px, py = _face_point(axis, c, t_start, n_face)
    x, y = at(px, py, side, 111.0, -2.0)
    put(label + "_Win", PLANE, x, y, floor_z + 90 + 66.5, YAW[side], (1.10, 1.33, 1), folder=IR, roll=90.0,
        mats=[BM + "MI_BackAlleys_JalousieDouble"])
    items[-1]["phys"] = PHYS + "Glass"
    x, y = at(px, py, side, 111.0, -(thick * 100.0 - 2.0))
    put(label + "_WinIn", PLANE, x, y, floor_z + 90 + 66.5, YAW[side] + 180.0, (1.10, 1.33, 1), folder=IR, roll=90.0,
        mats=[BM + "MI_BackAlleys_JalousieDouble"])
    items[-1]["nocoll"] = True
    if fitted:
        X, Y = _face_point(axis, c, t_mid, n_face - sgn * 0.13)          # its outside sill (14 cm out from the origin) 1 cm proud
        put(label + "_Frame", WIN_FRAME, X, Y, floor_z + WIN_SILL, YAW[side] + 180.0,
            (WIN_W * 100.0 / 110.0, 1.0, (WIN_TOP - WIN_SILL) / 129.0), folder=IR)
        items[-1]["phys"] = PHYS + "Wood"
        _n["frames"] += 1
        # A hidden glass block filling the gap between the two jalousie planes, 0.5 cm in from each (2026-11-09, user, shooting a
        # row-house window from inside: "i hear wood", "its when im shooting from inside the building"). A plane collides as a
        # zero-thickness box, and a trace only meets it from its front, so a shot from inside passed the inside plane and hit the
        # frame (its glass panes collided as Wood). The frame now collides as boxes round its wood only; this takes the shots.
        ga = at(px, py, side, 111.0 - 55.0, -2.5)
        gb = at(px, py, side, 111.0 + 55.0, -(thick * 100.0 - 2.5))
        put(label + "_WinGlass", CUBE, min(ga[0], gb[0]), min(ga[1], gb[1]), floor_z + 90, 0.0,
            (abs(gb[0] - ga[0]) / 100.0, abs(gb[1] - ga[1]) / 100.0, 1.33), folder=IR, mat="hidden")
        items[-1].update({"coll": "BlockAll", "phys": PHYS + "Glass", "nonav": True})
        px, py = _face_point(axis, c, t_start, n_face + sgn * 0.015)     # the grille clear of the sill
    if ground_floor:
        window_grille(label, px, py, floor_z, side, 1.0, IR)
    _n["windows"] += 1


def _trim(label, axis, c, t0, t1, n_face, sgn, z, ext0, ext1):
    """SM_MainBorder_04 along an outside face at z (its centre), 7 cm proud; ext0/ext1 lengthen it past its ends (cm)."""
    side = _side_of(axis, sgn)
    t_dir = (0.0, 1.0) if axis == "x" else (-1.0, 0.0)
    along = 1.0 if (RUN[side][0] * t_dir[0] + RUN[side][1] * t_dir[1]) > 0 else -1.0
    a, b = (t0, t1) if along > 0 else (t1, t0)
    e_a, e_b = (ext0, ext1) if along > 0 else (ext1, ext0)
    px, py = _face_point(axis, c, a, n_face)
    x, y = at(px, py, side, -e_a, -6.0)
    put(label, FV + "SM_MainBorder_04", x, y, z, YAW[side], ((abs(b - a) * 100.0 + e_a + e_b) / 150.0, 1, 1), folder=IR)


def _shown(axis, c, t0, t1, sgn, z):
    """The stretches of an outside face (outside toward sgn) where what stands in front is lower than z (cm, the houses'
    unlifted heights), sampled every 25 cm."""
    n = max(1, int(math.ceil((t1 - t0) / 0.25)))
    out = []
    for i in range(n):
        a, b = t0 + (t1 - t0) * i / n, t0 + (t1 - t0) * (i + 1) / n
        tm = (a + b) / 2
        p = (c + sgn * 0.3, tm) if axis == "y" else (tm, c + sgn * 0.3)
        if not outside(*p) and cover_top(*p) < z:
            if out and abs(out[-1][1] - a) < 1e-9:
                out[-1] = (out[-1][0], b)
            else:
                out.append((a, b))
    return [(a, b) for a, b in out if b - a > 0.2]


def _end_ext(axis, c, t_end, d, sgn, z):
    """How far (cm) a trim at height z on an outside face (outside toward sgn along n) runs past its end t_end (d: the
    direction the end points, along t), as the street houses' corner rules: an outside corner, east/west faces 7 past it
    and north/south ones 19 short (behind the other trim); an inside corner (a wall ahead), east/west 10 into it and
    north/south 7 short; something continuing the face in line, or a lower roof's edge, 1 short."""
    def pt(dt, dn):
        return (c + dn, t_end + dt) if axis == "y" else (t_end + dt, c + dn)
    ew = axis == "y"                                       # a line of constant x carries east/west faces
    z = z - FLOOR_T                                        # the houses' heights are before the floors pass lifts them
    ahead_out, ahead_in = pt(d * 0.1, sgn * 0.1), pt(d * 0.1, -sgn * 0.1)
    if outside(*ahead_out) or cover_top(*ahead_out) >= z + 10.0:
        return 10.0 if ew else -7.0
    if outside(*ahead_in) or cover_top(*ahead_in) >= z - 10.0 or any(_in(e["rect"], *ahead_in) for e in _bld.values()):
        return -1.0
    return 7.0 if ew else -19.0


def _rail(label, axis, c, t0, t1, n, z):
    """AsiaSlum's bar rail, 1.05 m, in modules of at most 3 m, along a line at offset n (m)."""
    L_ = (t1 - t0) * 100.0
    m = max(1, math.ceil(L_ / 300.0 - 1e-6))
    for i in range(m):
        ta = t0 + (t1 - t0) * i / m
        sx = (L_ / m) / 302.0
        X, Y = _face_point(axis, c, ta, n)
        yaw = 90.0 if axis == "x" else 180.0        # local X along +t: east (UE +Y) or south (UE -X)
        dX, dY = (0.0, 1.0) if axis == "x" else (-1.0, 0.0)
        put("%s_%d" % (label, i), RAIL, X + dX * RAIL_X0 * sx, Y + dY * RAIL_X0 * sx, z + RAIL_Z0 * RAIL_SZ, yaw, (sx, 1, RAIL_SZ), folder=IR)
        items[-1]["phys"] = PHYS + "Metal"
    _n["rails"] += 1


def _stair_top_on(s_, axis, cc, ta, tb):
    """The stair s_ arrives across this edge (its top end lies on the line, within the edge)."""
    x0, y0, x1, y1 = s_["r"]
    up = s_["up"]
    if up in ("N", "S") and axis == "x":
        yt = y0 if up == "N" else y1
        return abs(yt - cc) < 0.02 and ta < (x0 + x1) / 2 < tb
    if up in ("E", "W") and axis == "y":
        xt = x1 if up == "E" else x0
        return abs(xt - cc) < 0.02 and ta < (y0 + y1) / 2 < tb
    return False



def _parapet_gaps(axis, cc, ta, tb):
    """The terrace parapet, less the plank's landing (the layout's PLANK area, where the last survivors cross)."""
    out, t = [], ta
    for a in _raw["areas"]:
        if a["id"] != "PLANK":
            continue
        if axis == "x" and (abs(a["y1"] - cc) < 0.02 or abs(a["y0"] - cc) < 0.02):
            g0, g1 = a["x0"], a["x1"]
            if g0 < tb and g1 > ta:
                if g0 > t:
                    out.append((t, g0))
                t = g1
    if t < tb:
        out.append((t, tb))
    return out


# --- Edges per building and storey ----------------------------------------------------------------------------------------
_built_party = set()
_light_cells = []
for bid in sorted(_bld):
    B = _bld[bid]
    R = B["rect"]
    nst = len(B["storeys"])
    for f in range(nst):
        cells = _cells(bid, f)
        if not cells:
            continue
        lv0, lv1 = B["lv"][f], B["lv"][f + 1]
        top_f = f == nst - 1
        _o = [e["rect"] for o_, e in _bld.items() if o_ != bid]
        xs = sorted({R[0], R[2]} | {c["r"][0] for c in cells} | {c["r"][2] for c in cells} | {v for r_ in _o for v in (r_[0], r_[2]) if R[0] < v < R[2]})
        ys = sorted({R[1], R[3]} | {c["r"][1] for c in cells} | {c["r"][3] for c in cells} | {v for r_ in _o for v in (r_[1], r_[3]) if R[1] < v < R[3]})
        _lines = [("y", x_, ys) for x_ in xs] + [("x", y_, xs) for y_ in ys]
        for axis, cc, ts in _lines:
            segs = []
            for ta, tb in zip(ts, ts[1:]):
                tm = (ta + tb) / 2
                pa = (cc - 0.02, tm) if axis == "y" else (tm, cc - 0.02)      # the -n side
                pb = (cc + 0.02, tm) if axis == "y" else (tm, cc + 0.02)
                ina, inb = _in(R, *pa), _in(R, *pb)
                if not ina and not inb:
                    continue
                ca = _at_cell(cells, *pa) if ina else None
                cb = _at_cell(cells, *pb) if inb else None
                if ca is not None and cb is not None and ca is cb:
                    continue
                if ca is None and cb is None:
                    continue
                ka = "out" if not ina else (ca["kind"] if ca else "none")
                kb = "out" if not inb else (cb["kind"] if cb else "none")
                key = (ka, kb, ca["id"] if ca else None, cb["id"] if cb else None)
                if segs and abs(segs[-1][1] - ta) < 1e-6 and segs[-1][2] == key:
                    segs[-1][1] = tb
                else:
                    segs.append([ta, tb, key, ca, cb])
            for ta, tb, key, ca, cb in segs:
                ka, kb = key[0], key[1]
                name = "%s_F%d_%s%s_%s" % (bid, f, axis.upper(), ("%.2f" % cc).replace(".", "p"), ("%.2f" % ta).replace(".", "p"))
                ops = _openings(f, axis, cc, ta, tb)
                ops_layout = ops                # windows keep their places from the layout's openings, so a narrower door moves none
                if bid in FITTED:
                    ops = [_door_span(f, axis, cc, a, b) + (k_,) if k_ in DOOR_KINDS else (a, b, k_) for a, b, k_ in ops]
                walled = ("room", "closed")
                # Which kind of edge
                if "out" in (ka, kb):
                    sgn = 1.0 if kb == "out" else -1.0                      # where the outside is, along n
                    inner = ca if sgn > 0 else cb
                    ik = inner["kind"] if inner else "none"
                    pt_out = (cc + sgn * 0.3, (ta + tb) / 2) if axis == "y" else ((ta + tb) / 2, cc + sgn * 0.3)
                    other = _other_building(bid, *pt_out)
                    if _is_terrace(bid, f, inner):
                        kind = "parapet"
                    elif other and f == 0:
                        if (min(bid, other), max(bid, other), axis, round(cc, 3), round(ta, 3)) in _built_party:
                            continue
                        _built_party.add((min(bid, other), max(bid, other), axis, round(cc, 3), round(ta, 3)))
                        kind = "party"
                    else:
                        kind = "ext"
                elif ka in walled and kb in walled:
                    kind = "ply" if (_ply_side(bid, f, ca) or _ply_side(bid, f, cb)) else ("none" if ka == kb == "closed" else "part")
                elif ka in walled or kb in walled:
                    kind = "ply" if _ply_side(bid, f, ca if ka in walled else cb) and bid != "TRAP" else "inner"
                    if bid == "TRAP" and f == 2:
                        kind = "boards"                                     # the wooden storey's outside walls
                    if "void" in (ka, kb) and any(s_["f"] + 1 == f and _stair_top_on(s_, axis, cc, ta, tb) for s_ in _raw["stairs"]):
                        kind = "none"                                       # where a stair arrives: open
                elif "void" in (ka, kb) and ("open" in (ka, kb)):
                    kind = "rail"
                else:
                    kind = "none"
                if kind == "none":
                    continue
                z_lo = lv0 - (FLOOR_T + 5.0 if f == 0 else FLOOR_T)
                z_hi = lv1 if top_f else lv1 - FLOOR_T
                holes = []
                for a, b, k_ in ops:
                    sill = lv0
                    if k_ == "drop" and kind == "party":
                        sill = max(_bld[o]["lv"][0] for o in (bid, _other_building(bid, *pt_out)))
                    holes.append((a, b, sill, sill + (DOOR_H if bid in FITTED and k_ in DOOR_KINDS else OPEN_H[k_])))
                    _n["openings"] += 1
                if kind == "rail":
                    o_side = 1.0 if ka == "void" else -1.0                 # the gallery is on the +n side if a is the void
                    _rail(name + "_Rail", axis, cc, ta + 0.06, tb - 0.06, o_side * 0.08, lv0)
                    continue
                if kind == "parapet":
                    sgn_out = 1.0 if kb == "out" else -1.0
                    n0, n1 = (-0.15, 0.0) if sgn_out > 0 else (0.0, 0.15)
                    for ga, gb in _parapet_gaps(axis, cc, ta, tb):
                        # At the terrace's corners the east/west-facing parapet runs through; the north/south one stops at
                        # its inner face, so no two share the corner. Caps: as the trims (_end_ext). Not where a house
                        # stands against it outside, taller than the cap: the cap would run into its wall.
                        e_a, e_b = _end_ext(axis, cc, ga, -1.0, sgn_out, lv0 + PARAPET_H), _end_ext(axis, cc, gb, 1.0, sgn_out, lv0 + PARAPET_H)
                        cut_a = 0.15 if axis == "x" and e_a == -19.0 else 0.0
                        cut_b = 0.15 if axis == "x" and e_b == -19.0 else 0.0
                        _wall(name + "_Parapet", axis, cc, ga + cut_a, gb - cut_b, n0, n1, lv0 - FLOOR_T, lv0 + PARAPET_H, [],
                              _ext_mat(bid, 1, _side_of(axis, sgn_out), (ga + gb) / 2, True))
                        pm = (cc + sgn_out * 0.3, (ga + gb) / 2) if axis == "y" else ((ga + gb) / 2, cc + sgn_out * 0.3)
                        if cover_top(*pm) < lv0 + PARAPET_H - FLOOR_T - 20.0:
                            _trim(name + "_Cap", axis, cc, ga, gb, n1 if sgn_out > 0 else n0, sgn_out, lv0 + PARAPET_H + 6.0, e_a, e_b)
                    continue
                if kind in ("ext", "party"):
                    sgn = 1.0 if kb == "out" else -1.0
                    inner = ca if sgn > 0 else cb
                    if kind == "party":
                        o_ = _other_building(bid, *pt_out)
                        z_lo = min(z_lo, _bld[o_]["lv"][0] - FLOOR_T - 5.0)
                        z_hi = max(z_hi, _bld[o_]["lv"][1])
                        n0, n1 = -WALL_T / 2, WALL_T / 2
                    else:
                        n0, n1 = (-WALL_T, 0.0) if sgn > 0 else (0.0, WALL_T)
                    side = _side_of(axis, sgn)
                    face_n = n1 if sgn > 0 else n0
                    in_n = n0 if sgn > 0 else n1
                    # Windows where the wall shows from the outside (nothing in front up to the sill) and has room
                    wins = []
                    show = bool(_shown(axis, cc, ta, tb, sgn, lv0 - FLOOR_T + WIN_SILL)) if kind == "ext" else False
                    if kind == "ext" and show and bid in ("ROW", "TRAP") and f < 2 and inner is not None and inner["kind"] == "room":
                        free = [(a_ + 0.45, b_ - 0.45) for a_, b_ in _shown(axis, cc, ta, tb, sgn, lv0 - FLOOR_T + WIN_TOP + 20.0)]
                        for a, b, _ in ops_layout:
                            free = [p for s_ in free for p in ((s_[0], min(s_[1], a - 0.4)), (max(s_[0], b + 0.4), s_[1])) if p[1] - p[0] > 0.01]
                        for fa, fb in free:
                            if fb - fa < 1.6:
                                continue
                            m = max(1, int((fb - fa + 0.6) // 3.2))
                            for i in range(m):
                                tmid = fa + (fb - fa) * (i + 0.5) / m
                                wins.append(tmid)
                    for tmid in wins:
                        holes.append((tmid - WIN_W / 2, tmid + WIN_W / 2, lv0 + WIN_SILL, lv0 + WIN_TOP))
                    core = _ext_mat(bid, f, side, (ta + tb) / 2, bool(ops or wins))
                    fin = _fin(bid, f, inner) if inner is not None else None
                    if bid == "TRAP" and f == 2:
                        core = _wood_mat()
                    if kind == "ext" and bid == "PLY":
                        _ply_wall(name + "_PlyX", axis, cc, ta, tb, (-PLY_T / 2 if sgn > 0 else PLY_T / 2), lv0, z_hi, holes, PLY_MATS[0], -sgn,
                                  whole=True)
                        _n["walls"] += 1
                        continue
                    if kind == "party":
                        _wall(name + "_Party", axis, cc, ta, tb, n0, n1, z_lo, z_hi, holes, CHB_BARE)
                    else:
                        _wall(name + "_Ext", axis, cc, ta, tb, n0, n1, z_lo, z_hi, holes, core,
                              [(in_n, -sgn, fin if fin and fin not in (CONC,) else None)])
                    _jambs(name, bid, f, axis, cc, ops, n0, n1, lv0)
                    _knocks(name, bid, f, axis, cc, ops, n0, n1, lv0, ta, tb)
                    for i, tmid in enumerate(wins):
                        _window("%s_W%d" % (name, i), axis, cc, tmid, face_n, sgn, lv0, WALL_T, f == 0, bid in FITTED)
                    # Trims at the floor lines and the top, on concrete and paint, where they show
                    if kind == "ext" and show and core in (CHB_CONC, CHB_BARE) or (kind == "ext" and show and "PaintedWall" in core):
                        for zt in ([lv0 - FLOOR_T / 2] if f > 0 else []) + ([lv1 + 8.0] if top_f else []):
                            for q, (ga, gb) in enumerate(_shown(axis, cc, ta, tb, sgn, zt - FLOOR_T - 10.0)):   # only where it shows
                                _trim(name + "_Trim%d_%d" % (int(zt), q), axis, cc, ga, gb, face_n, sgn, zt,
                                      _end_ext(axis, cc, ga, -1.0, sgn, zt), _end_ext(axis, cc, gb, 1.0, sgn, zt))
                    continue
                # Inside walls. (2026-11-09, user: "the inside walls ... penetrates to the outside yard", "the walls below are pushing
                # through the cieling into the 2nd floor".) An inside wall whose end is on the building's edge stops at the outside wall's
                # inner face (a party wall's on the ground floor), not at the outer face, where its end and paint showed outside. Upstairs
                # an inside wall starts 1 cm under the floor; a hole at floor level cuts that centimetre too, or it is left as a 1 cm sliver
                # whose top shares the floor's plane and flickers through it.
                ta_w, tb_w = _inner_ends(bid, f, axis, cc, ta, tb)
                # (2026-11-09, user: "the issue is that caved in bit on the wall".) Over a void (a stairwell) the slab above is cut at this
                # wall's line, so the half of the wall facing the void was missing for the slab's depth: a recess, and in it the slab's
                # edge. Where a void at the next storey has an edge on this line, the wall rises through the slab to the wall above's foot.
                z_top = z_hi
                if not top_f and any(ax_ == axis and abs(c_ - cc) < 0.01 and a_ < tb - 0.01 and b_ > ta + 0.01
                                     for ax_, c_, a_, b_ in _void_edges(bid, f + 1)):
                    z_top = B["lv"][f + 1] - 1.0
                z_w = lv0 if f == 0 else lv0 - (2.0 if kind == "ply" or (kind == "inner" and bid == "PLY") else 1.0)
                holes = [(a, b, z_w if abs(za - lv0) < 0.01 else za, zb) for a, b, za, zb in holes]
                ca_f, cb_f = _fin(bid, f, ca), _fin(bid, f, cb)
                if kind == "ply" or (kind == "inner" and bid == "PLY"):
                    studs = -1.0 if ka in walled and _ply_side(bid, f, ca) else 1.0
                    mat = _fin(bid, f, ca if ka in walled else cb) or PLY_MATS[1]
                    if mat not in PLY_MATS:
                        mat = PLY_MATS[1]
                    _ply_wall(name + "_PlyW", axis, cc, ta_w, tb_w, 0.0, lv0 - 2.0 if f else lv0, z_top, holes, mat, studs,
                              whole=(bid == "PLY"))
                    _n["walls"] += 1
                    continue
                if kind == "boards":
                    sgn = 1.0 if ka in walled else -1.0                     # the room is on the -n side when a is the room
                    n0, n1 = (-BOARD_W_T, 0.0) if sgn > 0 else (0.0, BOARD_W_T)
                    inner = ca if ka in walled else cb
                    _wall(name + "_Boards", axis, cc, ta_w, tb_w, n0, n1, lv0, z_top, holes, _wood_mat(),
                          [((n0 if sgn > 0 else n1), -sgn, _fin(bid, f, inner))])
                    continue
                t_ = PART_T if kind == "part" else INNER_T
                core = ca_f or cb_f or CHB_BARE
                skins = [(-t_ / 2, -1.0, ca_f), (t_ / 2, 1.0, cb_f)]
                _wall(name + ("_Part" if kind == "part" else "_Inner"), axis, cc, ta_w, tb_w, -t_ / 2, t_ / 2,
                      lv0 if f == 0 else lv0 - 1.0, z_top, holes, core, skins)
                _jambs(name, bid, f, axis, cc, ops, -t_ / 2, t_ / 2, lv0)
                _knocks(name, bid, f, axis, cc, ops, -t_ / 2, t_ / 2, lv0, ta, tb)
        for c in cells:
            if c["kind"] in ("room", "open") and not _is_terrace(bid, f, c):
                _light_cells.append((bid, f, c))



# --- Floors and slabs -----------------------------------------------------------------------------------------------------
def _minus(R, holes):
    """Rect R less the hole rects, as rectangles (compressed grid, merged)."""
    xs = sorted({R[0], R[2]} | {min(max(h[0], R[0]), R[2]) for h in holes} | {min(max(h[2], R[0]), R[2]) for h in holes})
    ys = sorted({R[1], R[3]} | {min(max(h[1], R[1]), R[3]) for h in holes} | {min(max(h[3], R[1]), R[3]) for h in holes})
    out = []
    for j in range(len(ys) - 1):
        for i in range(len(xs) - 1):
            if xs[i + 1] - xs[i] < 1e-6 or ys[j + 1] - ys[j] < 1e-6:
                continue
            mx, my = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            if not any(h[0] < mx < h[2] and h[1] < my < h[3] for h in holes):
                out.append((xs[i], ys[j], xs[i + 1], ys[j + 1]))
    return _merge(out)


def _finish(bid, f, c):
    if c["kind"] == "open":
        return FLOOR_FIN["old"]
    if bid == "BOD" or c["id"] in CELLS or c["id"] in ("CORR", "PASS"):
        return FLOOR_FIN["old"]
    return FLOOR_FIN["concrete"] if f == 0 else FLOOR_FIN["new"]


FLOOR_PLANE = 1.0       # cm the finish plane sits over its slab
# Slabs, ceilings and steps: the pours' material, mapped from above. The wall render (CONC, world-aligned for walls) streaks
# on a flat face (LESSONS; seen 2026-11-08 on the hall's ceiling).
SLAB_MAT = GM + "ConcreteNew"
for bid in sorted(_bld):
    B = _bld[bid]
    R = B["rect"]
    for f in range(len(B["storeys"])):
        cells = _cells(bid, f)
        voids = [c["r"] for c in cells if c["kind"] == "void"]
        lv = B["lv"][f]
        if f == 0:
            _box("%s_Floor0" % bid, *R, B["ground"] - 20.0, lv - FLOOR_PLANE, IR, [SLAB_MAT])
        else:
            for k, r in enumerate(_minus(R, voids)):
                _box("%s_Slab%d_%d" % (bid, f, k), *r, lv - FLOOR_T, lv - FLOOR_PLANE, IR, [SLAB_MAT])
            # (2026-11-09, user: "the cubes you are using has messed up UVs on one side".) The slab's material is mapped from above, so
            # its cut edge round a void streaked. Each edge gets a 1 cm facing in the wall render (world-aligned for walls), up to the
            # floor's plane; where a wall stands on the edge the facing is inside it.
            for v_, (x0, y0, x1, y1) in enumerate(voids):
                for e_, r_ in enumerate(((x0, y0, x0 + 0.01, y1), (x1 - 0.01, y0, x1, y1), (x0 + 0.01, y0, x1 - 0.01, y0 + 0.01),
                                         (x0 + 0.01, y1 - 0.01, x1 - 0.01, y1))):
                    _box("%s_SlabEdge%d_%d_%d" % (bid, f, v_, e_), *r_, lv - FLOOR_T, lv, IR, [CONC])
        _n["slabs"] += 1
        for c in cells:
            if c["kind"] not in ("room", "open"):
                continue
            for k, r in enumerate(_minus(c["r"], [v for v in voids if v != c["r"]])):
                x0, y0, x1, y1 = r
                X, Y = ue((x0 + x1) / 2, (y0 + y1) / 2)
                put("%s_%s_Floor%d" % (bid, c["id"], k), PLANE, X, Y, lv, 0, (y1 - y0, x1 - x0, 1.0), folder=IR, mats=[_finish(bid, f, c)])
                p_ = items[-1]
                p_["coll"], p_["phys"], p_["nonav"] = "IgnoreOnlyPawn", PHYS + "Concrete", True
    top = B["lv"][-1]
    if bid in ("ROW", "BOD", "PASS", "HOLD"):       # the ceiling under the roof (the street houses' lid)
        _box("%s_Ceiling" % bid, R[0] + 0.05, R[1] + 0.05, R[2] - 0.05, R[3] - 0.05, top - FLOOR_T, top - 2.0, IR, [SLAB_MAT])
x0, y0, x1, y1 = WOODEN["rect"]                  # the wooden storey: a board ceiling under its roof
_box("TRAPW_Ceiling", x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05, _bld["TRAP"]["lv"][3] - 4.0, _bld["TRAP"]["lv"][3] - 1.0, IR, [_wood_mat()])
items[-1]["phys"] = PHYS + "Wood"


# --- Stairs -------------------------------------------------------------------------------------------------------------
def _building_at(lx, ly):
    for o, e in _bld.items():
        if _in(e["rect"], lx, ly):
            return o
    return None


def _wall_near(bid, f, axis_line, c):
    """A wall line within 0.35 m of c: the building's edge (its inner face) or a partition (its line): where the stair
    stops, or None."""
    R = _bld[bid]["rect"]
    lo, hi = (R[0], R[2]) if axis_line == "y" else (R[1], R[3])
    for e, sgn in ((lo, 1.0), (hi, -1.0)):
        if abs(c - e) < 0.35:
            return e + sgn * (WALL_T - 0.01)
    for cl in _cells(bid, f):
        if cl["kind"] not in ("room", "closed"):
            continue
        for e in ((cl["r"][0], cl["r"][2]) if axis_line == "y" else (cl["r"][1], cl["r"][3])):
            if abs(c - e) < 0.02 and lo + 0.1 < e < hi - 0.1:
                return e
    return None


STAIR_RISE = 18.5
for si, st in enumerate(_raw["stairs"]):
    if si == 0:
        continue                                    # the eskinita steps: story_ground
    x0, y0, x1, y1 = st["r"]
    bid = _building_at((x0 + x1) / 2, (y0 + y1) / 2)
    B = _bld[bid]
    zb = B["lv"][st["f"]]
    zt = B["lv"][st["f"] + 1] if st["rise"] >= 3.5 else zb + st["rise"] * 100.0     # a storey (the layout drew 4 m ones), or the mezzanine's 3 m
    up = st["up"]
    along_y = up in ("N", "S")
    # widened to the wall it runs against, 1 cm into it
    if along_y:
        w0, w1 = _wall_near(bid, st["f"], "y", x0), _wall_near(bid, st["f"], "y", x1)
        if w0 is not None and abs(w0 - x0) < 0.35:
            x0 = min(x0, w0 - 0.01)
        if w1 is not None and abs(w1 - x1) < 0.35:
            x1 = max(x1, w1 + 0.01)
        open_sides = [s_ for s_, w_ in (("west", w0), ("east", w1)) if w_ is None]
        L0, L1 = (y1, y0) if up == "N" else (y0, y1)        # bottom end, top end
    else:
        w0, w1 = _wall_near(bid, st["f"], "x", y0), _wall_near(bid, st["f"], "x", y1)
        open_sides = [s_ for s_, w_ in (("north", w0), ("south", w1)) if w_ is None]
        L0, L1 = (x0, x1) if up == "E" else (x1, x0)
    # User 2026-11-08: "Stairs are awful" ... "look at Demomap_AsiaSlum for interiors, it has a stair and rail setup. The way you use the
    # blocks for stair rails is absurd". As that map builds them: the kit's concrete flights, SM_Stair_A_002 (300 run, 114.9 rise, 307
    # wide; pivot at its top edge, falling along local +X, the width toward local -Y), three in line per storey; on the open side the
    # kit's balusters, SM_StairRail_C_002, at most 68 cm apart (the demo's spacing), each scaled up to the pipe handrail over them,
    # SM_StairRail_A_001 (a straight pipe rising toward its local -X at 27.2 deg, its low end at local (43.6, 0, 17); found from the
    # demo, where its ends meet the balusters' tops). Two pipe lengths per stair, turned to the stair's slope, so the pipe stays thin.
    run_cm, rise_cm = abs(L1 - L0) * 100.0, zt - zb
    nfl = 3
    dl = (1.0 if L0 > L1 else -1.0)                         # layout direction of "downhill" along the run axis
    D2 = ue_dir(0, dl) if along_y else ue_dir(dl, 0)        # UE, horizontal, from the top end toward the bottom end
    Ly = (-D2[1], D2[0])                                    # the flights' local +Y
    lat0, lat1 = (x0, x1) if along_y else (y0, y1)          # the stair's width, layout
    width_cm = (lat1 - lat0) * 100.0
    sy_ = width_cm / 306.7
    e_a = ue(lat0, L1) if along_y else ue(L1, lat0)          # the two lateral edges at the top end, UE
    e_b = ue(lat1, L1) if along_y else ue(L1, lat1)
    piv = e_a if ((e_b[0] - e_a[0]) * Ly[0] + (e_b[1] - e_a[1]) * Ly[1]) < 0 else e_b      # local -Y must cross the width
    yaw_ = math.degrees(math.atan2(D2[1], D2[0]))
    if bid in FITTED:
        # The user's stair (FITTED, above): fixed flights from the top end down, each one step down the last, until the steps reach
        # the floor; the run they light is shorter than the stairwell, the rest of it floor at the foot.
        nfl_f = max(1, math.ceil((rise_cm - FLIGHT_RISE) / (FLIGHT_RISE * FLIGHT_STEP) - 1e-6) + 1)
        for k in range(nfl_f):
            d_ = FLIGHT_RUN * FLIGHT_STEP * k                   # cm downhill from the top end to this flight's top
            put("%s_Stair%d_%d" % (bid, si, nfl_f - 1 - k), AS + "SM_Stair_A_002", piv[0] + D2[0] * d_ - Ly[0] * 3.5 * sy_,
                piv[1] + D2[1] * d_ - Ly[1] * 3.5 * sy_, zt - FLIGHT_RISE * FLIGHT_STEP * k, yaw_, (FLIGHT_RUN / 300.0, sy_, FLIGHT_RISE / 114.9),
                folder=IR)
        run_cm = rise_cm * FLIGHT_RUN / FLIGHT_RISE             # where the steps meet the floor, for the rails
        L0 = L1 - (L1 - L0) / abs(L1 - L0) * run_cm / 100.0
    for k in range(nfl if bid not in FITTED else 0):
        frac = (k + 1) / nfl
        # from the stair's top end, downhill (D2) to this flight's top. (2026-11-08: this went uphill, past the top end; the user
        # moved the row house's two lower flights back by hand: "I moved the stairs, fix it again yourself".)
        top_x = piv[0] + D2[0] * run_cm * (1 - frac) - Ly[0] * 3.5 * sy_
        top_y = piv[1] + D2[1] * run_cm * (1 - frac) - Ly[1] * 3.5 * sy_
        put("%s_Stair%d_%d" % (bid, si, k), AS + "SM_Stair_A_002", top_x, top_y, zb + rise_cm * frac, yaw_,
            (run_cm / nfl / 300.0, sy_, rise_cm / nfl / 114.9), folder=IR)
    # Balusters and the handrail along each open side, 8 cm in from its edge
    alpha = math.atan2(206.9, 403.2)
    theta = math.atan2(rise_cm, run_cm)
    dlt = theta - alpha
    up3 = (0.0, 0.0, 1.0)
    D3 = (D2[0], D2[1], 0.0)
    Xw = (D3[0] * math.cos(dlt) - up3[0] * math.sin(dlt), D3[1] * math.cos(dlt) - up3[1] * math.sin(dlt), -math.sin(dlt))
    Zw = (D3[0] * math.sin(dlt), D3[1] * math.sin(dlt), math.cos(dlt))
    Yw = v_cross(Zw, Xw)
    for s_ in open_sides:
        lat = (lat0 + 0.08) if s_ in ("west", "north") else (lat1 - 0.08)

        def pt(s_m, lat=lat):                                # UE point s_m metres up the run from the bottom end, on this side
            along = L0 + (L1 - L0) * s_m / abs(L1 - L0)
            return ue(lat, along) if along_y else ue(along, lat)

        def surf(s_m):
            return zb + rise_cm * s_m / abs(L1 - L0)
        s_lo, s_hi = 0.25, abs(L1 - L0) - 0.15
        n_posts = max(2, math.ceil((s_hi - s_lo) / 0.68) + 1)
        for i in range(n_posts):
            s_m = s_lo + (s_hi - s_lo) * i / (n_posts - 1)
            X_, Y_ = pt(s_m)
            bot, top = surf(s_m) - 9.0, surf(s_m) + 92.0
            put("%s_Stair%d_Post%s%d" % (bid, si, s_[0].upper(), i), AS + "SM_StairRail_C_002", X_, Y_, bot, yaw_,
                (1.0, 1.0, (top - bot) / 109.9), folder=IR)
            items[-1]["phys"] = PHYS + "Metal"
        for j in range(2):                                    # the pipe, in two lengths
            sa = s_lo + (s_hi - s_lo) * j / 2
            sb = s_lo + (s_hi - s_lo) * (j + 1) / 2
            Pa = pt(sa) + (surf(sa) + 90.0,)
            Pb = pt(sb) + (surf(sb) + 90.0,)
            k_ = math.dist(Pa, Pb) / 453.2
            put_axes("%s_Stair%d_Rail%s%d" % (bid, si, s_[0].upper(), j), AS + "SM_StairRail_A_001", Xw, Yw, Zw, (k_, k_, k_),
                     (43.6, 0.0, 17.0), Pa)
            items[-1]["folder"] = IR
            items[-1]["phys"] = PHYS + "Metal"
    _n["stairs"] += 1
    # Rails round a stairwell that is a hole in a room's floor (H2's, the wooden one): its open edges, not where the
    # stair arrives, not along a wall
    for c in _cells(bid, st["f"] + 1):
        if c["kind"] != "void":
            continue
        vx0, vy0, vx1, vy1 = c["r"]
        if not (vx0 - 0.05 <= (x0 + x1) / 2 <= vx1 + 0.05 and vy0 - 0.05 <= (y0 + y1) / 2 <= vy1 + 0.05):
            continue
        host = [h for h in _cells(bid, st["f"] + 1) if h["kind"] == "room" and _inside(c["r"], h["r"])]
        if not host:
            continue                                # a void beside rooms (the trap house's): the edges did its rails
        zr = B["lv"][st["f"] + 1]
        for axis, cc, ta, tb, sgn in (("x", vy0, vx0, vx1, -1.0), ("x", vy1, vx0, vx1, 1.0), ("y", vx0, vy0, vy1, -1.0), ("y", vx1, vy0, vy1, 1.0)):
            if _stair_top_on(st, axis, cc, ta, tb) or _wall_near(bid, st["f"] + 1, axis, cc) is not None:
                continue
            _rail("%s_Well%d_%s%d" % (bid, si, axis.upper(), int(cc * 10)), axis, cc, ta + 0.06, tb - 0.06, sgn * 0.06, zr)

# --- The bodega mezzanine (+3): a slab along the north wall, steel posts under its edge, a rail but at its stair --------------
_m = next(a for a in _raw["areas"] if a["id"] == "MEZZ")
_zb = _bld["BOD"]["lv"][0] + 300.0
_box("BOD_Mezz", _m["x0"] + 0.18, _m["y0"] + 0.18, _m["x1"] - 0.18, _m["y1"], _zb - FLOOR_T, _zb - FLOOR_PLANE, IR, [SLAB_MAT])
X, Y = ue((_m["x0"] + _m["x1"]) / 2, (_m["y0"] + 0.18 + _m["y1"]) / 2)
put("BOD_Mezz_Floor", PLANE, X, Y, _zb, 0, (_m["y1"] - _m["y0"] - 0.18, _m["x1"] - _m["x0"] - 0.36, 1.0), folder=IR, mats=[FLOOR_FIN["old"]])
items[-1].update({"coll": "IgnoreOnlyPawn", "phys": PHYS + "Concrete", "nonav": True})
_mst = _raw["stairs"][2]
for k in range(5):
    px = _mst["r"][2] + 0.3 + k * (_m["x1"] - 0.5 - _mst["r"][2] - 0.3) / 4
    _box("BOD_Mezz_Post%d" % k, px - 0.06, _m["y1"] - 0.14, px + 0.06, _m["y1"] - 0.02, _bld["BOD"]["lv"][0], _zb - FLOOR_T, IR,
         [BM + "MI_BackAlleys_MetalSheet_Rust"])
    items[-1]["phys"] = PHYS + "Metal"
_rail("BOD_Mezz_Rail", "x", _m["y1"], _mst["r"][2] + 0.05, _m["x1"] - 0.25, -0.06, _zb)

# --- The plank to the neighbour roof (the layout's PLANK: where F12's survivors run) ---------------------------------------
_pk = next(a for a in _raw["areas"] if a["id"] == "PLANK")
_zt = _bld["TRAP"]["lv"][2]
for k, (a_, b_) in enumerate(((0.25, 0.6), (0.85, 1.2))):
    _box("TRAP_Plank%d" % k, _pk["x0"] + a_, _pk["y0"] - 0.25, _pk["x0"] + b_, _pk["y1"] + 0.3, _zt, _zt + 4.0, IR, [BOARDS[0]])
    items[-1]["phys"] = PHYS + "Wood"

# --- Lights: a bare bulb hung from each room's ceiling, more in the big ones (night: on) ------------------------------------
LIGHTS_ON = getattr(LEVEL, "LIGHTS_ON", True)
IL = "BackAlleys/Lights"
COL_BULB_IN = [1.0, 0.7, 0.42]
for bid, f, c in _light_cells:
    B = _bld[bid]
    x0, y0, x1, y1 = c["r"]
    if bid == "PLY":
        ceil_ = B["lv"][0] + 300.0
    elif bid == "BOD":
        ceil_ = B["lv"][1] - FLOOR_T
    elif bid == "TRAP" and f == 2:
        ceil_ = B["lv"][3] - 4.0
    else:
        ceil_ = B["lv"][f + 1] - FLOOR_T
    area = (x1 - x0) * (y1 - y0)
    nx_ = 2 if (x1 - x0) > 7.0 else 1
    ny_ = 2 if (y1 - y0) > 7.0 else 1
    if c["kind"] == "open" and area < 12.0:
        continue
    for i in range(nx_):
        for j in range(ny_):
            lx, ly = x0 + (x1 - x0) * (i + 0.5) / nx_, y0 + (y1 - y0) * (j + 0.5) / ny_
            ceil_b = B["lv"][0] + 300.0 - FLOOR_T if bid == "BOD" and ly < 39.9 else ceil_     # under the mezzanine
            if bid in ("ROW", "TRAP", "HOLD", "PASS"):      # a void above (the hall, a stairwell): the first slab that is there
                for k2 in range(f + 1, len(B["storeys"])):
                    if any(v["kind"] == "void" and _in(v["r"], lx, ly) for v in _cells(bid, k2)):
                        ceil_b = (B["lv"][k2 + 1] - FLOOR_T) if k2 + 1 < len(B["storeys"]) else B["lv"][-1] - 4.0
                    else:
                        break
            X, Y = ue(lx, ly)
            k_ = 0.7 if ceil_b - B["lv"][f] > 330.0 else 0.45
            put("Bulb_%s_%s_%d%d" % (bid, c["id"], i, j), AS + "SM_Light_A_002", X, Y, ceil_b, INT_RNG.uniform(0.0, 360.0), (k_, k_, k_),
                folder=IL, nocoll=True, mats=["/Game/AsiaSlum/Material/MI_Light_A_001"] if LIGHTS_ON else None)
            if LIGHTS_ON:
                # Shadowless and volumetric, as the street's bulbs are (_cheap): the light sits inside the bulb's opaque glass, which
                # otherwise shadows it whole, and the bake gave sections 4-7 no light at all (user 2026-11-09: "no lights past the first 2 sections").
                items[-1].update({"noshadow": True, "vol": True})
                put("Light_Bulb_%s_%s_%d%d" % (bid, c["id"], i, j), "/Script/Engine.PointLight", X, Y, ceil_b - 124.0 * k_ - 4.0, 0.0, (1, 1, 1), folder=IL)
                items[-1]["light"] = {"kind": "PointLight", "intensity": 6.0, "radius": 650.0 if area < 40 else 900.0, "colour": COL_BULB_IN,
                                      "source": 3.0, "outer": 60.0, "length": 0.0}
            _n["lights"] += 1

# --- Roofs: the street houses' metal roof builder on each building (on the wooden storey for the trap house) ----------------
_save_zb = ZB
for bid, rect, z_, sh_, ign in [("ROW", _bld["ROW"]["rect"], 0.0, sum(_bld["ROW"]["storeys"]), ("ROW",)),
                                ("BOD", _bld["BOD"]["rect"], 0.0, sum(_bld["BOD"]["storeys"]), ("BOD",)),
                                ("PASS", _bld["PASS"]["rect"], 0.0, sum(_bld["PASS"]["storeys"]), ("PASS",)),
                                ("HOLD", _bld["HOLD"]["rect"], -180.0, sum(_bld["HOLD"]["storeys"]), ("HOLD",)),
                                ("TRAPW", WOODEN["rect"], -180.0 + sum(_bld["TRAP"]["storeys"][:2]), WOODEN["storeys"][0], ("TRAPW", "TRAP"))]:
    pseudo = {"id": bid, "x0": rect[0], "y0": rect[1], "x1": rect[2], "y1": rect[3], "storeys": 1, "sh": sh_, "z": z_,
              "roof": "metal", "ignore": ign}
    ZB = z_ + FLOOR_T
    _k0 = len(items)
    if metal_roof(bid, pseudo):
        _n["roofs"] += 1
    for p_ in items[_k0:]:
        p_["folder"] = "BackAlleys/Roofs"
ZB = _save_zb
# the covered alley and the plywood rooms: one lean-to off the houses north of the alley, falling south over both
sheet_roof("CoveredAlley", (84.0, 66.0 + CW_T + 0.02, 99.0, 75.0), "north", 395.0, 335.0, "BackAlleys/Roofs", "Galv")   # off the compound wall
# The fitted doors' slots, for placing the swinging doors (not <prefix>*: write_plan clears those)
json.dump(_doors, open(OUT + "doors.json", "w"), indent=0)
print("story interiors:", _n)
