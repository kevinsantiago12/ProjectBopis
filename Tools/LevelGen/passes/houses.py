# Pass `houses`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Houses: the layout's blocks split into houses, balconies and wide terraces cut off, storeys, heights, setbacks,
# roof kinds. Defines BLOCKS, cover_top, side_intervals.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
BLOCKS = {b["id"]: b for b in L["blocks"]}
# --- Houses: long blocks split into a row of separate houses ------------------------------------------------------------
# User 2026-11-03 (a photo of a Philippine back street): "most philippine houses still use metal roofs even in stone
# houses. They also vary in height, is not consistently aligned with each other on the street, and 1 storey houses with
# currogated roof exists as well" ... "All four at once". A block >= 9 m long becomes a row of houses 4.5-7.5 m wide
# along its long axis (on the 1.5 m grid, each the block's full depth). Each house then gets its own storeys, storey
# height, setbacks and roof (below, after the balconies). The layout JSON (design canon) is not changed.
HOUSE_RNG = random.Random(71)    # its own sequence
HOUSE_W = (4.5, 6.0, 7.5)
NO_SPLIT = getattr(LEVEL, "NO_SPLIT", ())   # arena: the shop row, the 1.5 m stub, the gallery-deck block
_houses = {}
for _bid, _b in BLOCKS.items():
    _along_x = _b["x1"] - _b["x0"] >= _b["y1"] - _b["y0"]
    _a0, _a1 = (_b["x0"], _b["x1"]) if _along_x else (_b["y0"], _b["y1"])
    if _bid in NO_SPLIT or _a1 - _a0 < 9.0:
        _houses[_bid] = _b
        continue
    _cuts = [_a0]
    while _a1 - _cuts[-1] > 7.5:
        _cuts.append(_cuts[-1] + HOUSE_RNG.choice([w for w in HOUSE_W if _a1 - _cuts[-1] - w >= 4.5] or [HOUSE_W[0]]))   # off the 1.5 m grid (a story level) none may fit
    _cuts.append(_a1)
    for _k, (_c0, _c1) in enumerate(zip(_cuts, _cuts[1:])):
        _h = dict(_b, id="%sh%d" % (_bid, _k + 1))
        _h.update({"x0": _c0, "x1": _c1} if _along_x else {"y0": _c0, "y1": _c1})
        _houses[_h["id"]] = _h
BLOCKS = _houses
# A level with ground heights gives each house its base (cm), b["z"], from the ground around it (levels/*.py
# house_base). The arena has one ground height and no base.
if hasattr(LEVEL, "house_base"):
    for _b in BLOCKS.values():
        _b["z"] = LEVEL.house_base(_b)
# A level may mark houses "plain" (a story level's compound: closed, unpainted, few openings, no balconies; levels/*.py
# house_plain). The arena has none.
if hasattr(LEVEL, "house_plain"):
    for _b in BLOCKS.values():
        _b["plain"] = LEVEL.house_plain(_b)
# --- Balconies: upper storeys stepped back ----------------------------------------------------------------------------
# User 2026-11-03: "replace some of the block's second story as balconies instead". As Favela's stepped-back top floors:
# on a few 2-storey blocks, a BALCONY_D strip along one face loses its upper storey and becomes a covered balcony on
# the ground floor's roof (the terrace builder below: parapet, corrugated sheets, plank frame). The upper wall behind it
# gets doors and windows onto it. Only the generator's blocks change; the layout JSON (design canon) does not.
# A face qualifies when it is open along its whole length at both storeys, is >= 6 m long, the block is >= 4.5 m deep
# behind it, and it is not B2 (the shop fronts) or B11 (the gallery deck). One face per block.
BALCONIES = getattr(LEVEL, "BALCONIES", 6)
NO_BALCONY = getattr(LEVEL, "NO_BALCONY", ())   # arena: B2 (shop fronts), B11 (the gallery deck)
BALCONY_D = 1.5
BALCONY_RNG = random.Random(23)   # its own sequence, so the choice doesn't shift the rest of the generator's randoms


def _face_open(b, side, s):
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    if side in ("north", "south"):
        ly = y0 - 0.75 if side == "north" else y1 + 0.75
        return all(not solid(x0 + (k + 0.5) * 1.5, ly, s) for k in range(int(round((x1 - x0) / 1.5))))
    lx = x0 - 0.75 if side == "west" else x1 + 0.75
    return all(not solid(lx, y0 + (k + 0.5) * 1.5, s) for k in range(int(round((y1 - y0) / 1.5))))


# Wide roof terraces (user 2026-11-03, with a reference picture: "the balcony you have is an extension on the
# building, we can use this, but what I really want is this", then "cut off the second story section completely and
# build on it"): on WIDE_TERRACES blocks >= 6 m deep, the upper storey's half along one face (on the 1.5 m grid, >= 3 m)
# is cut off and becomes an open roof terrace; the other half keeps its upper storey as the taller wall behind. The
# narrow 1.5 m balconies (the "extension", kept) go on other blocks.
WIDE_TERRACES = getattr(LEVEL, "WIDE_TERRACES", 4)


def _cands(min_dep):
    out = []
    for bid, b in BLOCKS.items():
        if b["storeys"] != 2 or bid in NO_BALCONY or b.get("plain"):
            continue
        for side in ("north", "south", "west", "east"):
            ln = (b["x1"] - b["x0"]) if side in ("north", "south") else (b["y1"] - b["y0"])
            dep = (b["y1"] - b["y0"]) if side in ("north", "south") else (b["x1"] - b["x0"])
            if ln >= 6.0 and dep >= min_dep and _face_open(b, side, 0) and _face_open(b, side, 1):
                out.append((bid, side, dep))
    BALCONY_RNG.shuffle(out)
    return out


BALCONY_FACES = []   # (block, side, strip depth)
for _bid, _side, _dep in _cands(6.0):
    if len(BALCONY_FACES) < WIDE_TERRACES and _bid not in [f[0] for f in BALCONY_FACES]:
        BALCONY_FACES.append((_bid, _side, max(3.0, math.floor(_dep / 2 / 1.5) * 1.5)))
_n_wide = len(BALCONY_FACES)
for _bid, _side, _dep in _cands(4.5):
    if len(BALCONY_FACES) < _n_wide + BALCONIES and _bid not in [f[0] for f in BALCONY_FACES]:
        BALCONY_FACES.append((_bid, _side, BALCONY_D))
for _bid, _side, _d in BALCONY_FACES:
    _b = BLOCKS[_bid]
    _strip = dict(_b, id=_bid + "b", storeys=1, balcony=_side)
    if _side == "north":
        _strip["y1"] = _b["y0"] + _d
        _b["y0"] += _d
    elif _side == "south":
        _strip["y0"] = _b["y1"] - _d
        _b["y1"] -= _d
    elif _side == "west":
        _strip["x1"] = _b["x0"] + _d
        _b["x0"] += _d
    else:
        _strip["x0"] = _b["x1"] - _d
        _b["x1"] -= _d
    BLOCKS[_strip["id"]] = _strip
print("balconies / terraces:", BALCONY_FACES)


def balcony_at(lx, ly):
    """True if (lx, ly) is on a balcony strip."""
    return any(b.get("balcony") and b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] for b in BLOCKS.values())


# --- Per house: storeys, storey height, setbacks, roof (see "Houses" above) ----------------------------------------------
# Fixed houses keep the layout's storeys, 4 m storey height and walls: those the gallery deck or a stair touches, those
# within reach of a spawn door's end wall (it is 2 storeys of 4 m and runs 1.1 m into the blocks either side), the shop
# row and the 1.5 m stub. Free houses: storey height 3.4-4.2 m; some 2-storey houses become 1-storey corrugated-roof
# houses (never at the arena edge - the arena's outer wall is its edge houses) and some get a third storey; street
# faces are set back 0, 0.3 or 0.6 m, inward only, so no alley gets narrower than the layout. Balcony parents and their
# strips keep their footprint and storeys (their terraces are built against them); the strip follows the parent's height.
STOREY_H = (340.0, 360.0, 380.0, 400.0, 420.0)   # cm
SHACK_H = (330.0, 350.0, 370.0)                   # 1-storey corrugated-roof houses
SHACKS, P_THIRD, P_FLAT = getattr(LEVEL, "SHACKS", 4), getattr(LEVEL, "P_THIRD", 0.4), 0.1          # P_FLAT: houses keeping a flat concrete roof ("most" have metal)
SETBACKS = (0.0, 0.0, 0.3, 0.6)                    # m, per open street face
FIX_RNG = random.Random(73)


def _near(b, r, pad):
    if r is None:        # a level with no gallery deck
        return False
    return b["x0"] < r["x1"] + pad and r["x0"] - pad < b["x1"] and b["y0"] < r["y1"] + pad and r["y0"] - pad < b["y1"]


FIXED = getattr(LEVEL, "FIXED", ())   # houses that keep the layout's storeys and 4 m storeys


def _fixed(b):
    if b["id"] in NO_SPLIT or b["id"] in FIXED or _near(b, L["deck"], 0.05) or any(_near(b, s, 0.05) for s in L["stairs"]):
        return True
    return any(_near(b, {"x0": d["x"], "x1": d["x"], "y0": d["y"], "y1": d["y"]}, 5.0) for d in L["doors"])


_parents = {f[0] for f in BALCONY_FACES}


def _inner(b):
    return not touches_edge(b)


# The 1-storey corrugated-roof houses: SHACKS of the free, inner (not on the arena edge), 2-storey, non-balcony houses.
_shacks = set(FIX_RNG.sample(sorted(b["id"] for b in BLOCKS.values() if not _fixed(b) and _inner(b) and
                                    b["storeys"] == 2 and b["id"] not in _parents and not b.get("balcony")), SHACKS))
for _b in BLOCKS.values():
    _b["sh"], _b["fixed"] = 400.0, _fixed(_b)
    _strip = _b["id"].endswith("b") and _b.get("balcony")
    if _b["fixed"] or _strip:
        continue
    if _b["id"] in _shacks:
        _b["storeys"], _b["shack"], _b["sh"] = 1, True, FIX_RNG.choice(SHACK_H)
        continue
    if _b["storeys"] == 2 and _b["id"] not in _parents and FIX_RNG.random() < P_THIRD and             not (hasattr(LEVEL, "no_third") and LEVEL.no_third(_b)):     # the draw comes first, so the sequence holds
        _b["storeys"] = 3
    _b["sh"] = FIX_RNG.choice(STOREY_H)
if hasattr(LEVEL, "stagger_heights"):        # a level's own rule for neighbours' storey heights (own draws)
    LEVEL.stagger_heights(BLOCKS)
for _b in BLOCKS.values():
    if _b["id"].endswith("b") and _b.get("balcony"):
        _b["sh"] = BLOCKS[_b["id"][:-1]]["sh"]
    # A 1-storey house of the layout (and every balcony strip) keeps its covered roof terrace; the rest get metal roofs.
    _b["roof"] = "terrace" if _b["storeys"] == 1 and not _b.get("shack") else \
        ("flat" if FIX_RNG.random() < P_FLAT else "metal")
for _bid, _sh in getattr(LEVEL, "FIXED_SH", {}).items():   # a level's own storey height for a fixed house, no draws
    if _bid in BLOCKS:
        BLOCKS[_bid]["sh"] = _sh
for _bid, _roof in getattr(LEVEL, "ROOFS", {}).items():   # a level's own roofs (e.g. a flat roof to land on), no draws
    if _bid in BLOCKS:
        BLOCKS[_bid]["roof"] = _roof
_cuts = []   # setbacks: decided on the unmoved footprints, then applied
for _b in BLOCKS.values():
    if _b["fixed"] or _b["roof"] == "terrace" or _b["id"] in _parents:
        continue
    for _side in ("north", "south", "west", "east"):
        _d = FIX_RNG.choice(SETBACKS)
        if _d and _face_open(_b, _side, 0):
            _cuts.append((_b, _side, _d))
if hasattr(LEVEL, "stagger"):                # a level's own setbacks for some houses (own draws)
    _cuts = LEVEL.stagger(BLOCKS, _cuts, _face_open)
_min_depth = getattr(LEVEL, "min_depth", lambda b: 3.0)   # how deep a house stays after its setback (a level may allow strips less)
for _b, _side, _d in _cuts:
    _key = {"north": "y0", "south": "y1", "west": "x0", "east": "x1"}[_side]
    _span = (_b["y1"] - _b["y0"]) if _side in ("north", "south") else (_b["x1"] - _b["x0"])
    if _span - _d >= _min_depth(_b):
        _b[_key] += _d if _side in ("north", "west") else -_d
        _b.setdefault("setback", {})[_side] = _d
print("houses:", len(BLOCKS), "| 3-storey", sum(b["storeys"] == 3 for b in BLOCKS.values()),
      "| 1-storey metal", sum(bool(b.get("shack")) for b in BLOCKS.values()),
      "| flat", sum(b["roof"] == "flat" for b in BLOCKS.values()), "| setbacks", len(_cuts))


_cover_grid = {}       # BLOCKS on a 1 m grid, made at cover_top's first call: no footprint changes after this pass (2026-11-09)


def _cover_cands(lx, ly):
    if not _cover_grid:
        for b_ in BLOCKS.values():
            for i in range(math.floor(b_["x0"]), math.floor(b_["x1"]) + 1):
                for j in range(math.floor(b_["y0"]), math.floor(b_["y1"]) + 1):
                    _cover_grid.setdefault((i, j), []).append(b_)
    return _cover_grid.get((math.floor(lx), math.floor(ly)), ())


def _blocks_near(lx, ly, pad):
    """The blocks whose footprint, grown by pad (m), might hold (lx, ly): from the cells round it (any order)."""
    _cover_cands(lx, ly)
    seen, out = set(), []
    for i in range(math.floor(lx - pad), math.floor(lx + pad) + 1):
        for j in range(math.floor(ly - pad), math.floor(ly + pad) + 1):
            for b_ in _cover_grid.get((i, j), ()):
                if id(b_) not in seen:
                    seen.add(id(b_))
                    out.append(b_)
    return out


def cover_top(lx, ly, me=None):
    """Height (cm) of the tallest house over (lx, ly) other than `me`: 0 for open ground, huge outside the arena."""
    if outside(lx, ly):
        return 1e9
    # Measured from me's base (or the house being built, ZB): houses and open ground stand at their own heights. In the
    # arena every base and the ground are 0, so this is each house's height, or 0.
    zb = me.get("z", 0.0) if me is not None else ZB
    return max([b.get("z", 0.0) + b["storeys"] * b["sh"] - zb for b in _cover_cands(lx, ly)
                if b is not me and b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"]] +
               [e["top"] - zb for e in EXTRA_SOLID if e is not me and e["x0"] < lx < e["x1"] and e["y0"] < ly < e["y1"] and
                e["id"] not in (me.get("ignore", ()) if me is not None else ())] or
               [ground_z(lx, ly) - zb])


def side_intervals(b, side, test):
    """Split one side of house b where other houses' edges (and the arena edge) cross it; for each piece, test(c) with
    c = cover_top 5 cm outside its middle. Returns [(t0, t1, result)] in metres from the side's min corner."""
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    p0 = {"north": (x0, y0), "south": (x0, y1), "west": (x0, y0), "east": (x1, y0)}[side]
    along_x = side in ("north", "south")
    length = (x1 - x0) if along_x else (y1 - y0)
    ts = {0.0, length}
    for o in list(BLOCKS.values()) + EDGE_RECTS + EXTRA_SOLID:
        for v in ((o["x0"], o["x1"]) if along_x else (o["y0"], o["y1"])):
            t = v - (p0[0] if along_x else p0[1])
            if 0 < t < length:
                ts.add(round(t, 4))
    ts = sorted(ts)
    nlx, nly = LNORM[side]
    out = []
    for ta, tb in zip(ts, ts[1:]):
        if tb - ta < 0.01:
            continue
        tm = (ta + tb) / 2
        lx, ly = (p0[0] + tm, p0[1]) if along_x else (p0[0], p0[1] + tm)
        res = test(cover_top(lx + nlx * 0.05, ly + nly * 0.05, b))
        if out and abs(out[-1][1] - ta) < 1e-6 and out[-1][2] == res:
            out[-1] = (out[-1][0], tb, res)
        else:
            out.append((ta, tb, res))
    return out

