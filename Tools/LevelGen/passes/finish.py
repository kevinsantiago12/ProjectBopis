# Pass `finish`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Hollow blocks on windowless faces, paint per house, bands and borders between floors.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# Hollow blocks on faces with no door or window (labels: <house>_<side letter><storey>_...).
if ONE_MATERIAL:
    _faces = {}
    for p in items:
        parts = p["label"].split("_")
        if p["folder"] != BLK or len(parts) < 3 or parts[1][:1] not in "NSEW" or not parts[1][1:].isdigit():
            continue
        house = parts[0][:-1] if parts[0].endswith("b") and parts[0][:-1] in BLOCKS else parts[0]
        _faces.setdefault((house, parts[1][0]), []).append(p)
    _clear = [f for f, ps in _faces.items() if all(p["asset"].split("/")[-1] in PLAIN_WALL for p in ps)]
    _hollow = [f for f in _clear if WALL_MIX_RNG.random() < P_HOLLOW or BLOCKS.get(f[0], {}).get("plain")]   # a plain house: every windowless face
    for f in _hollow:
        for p in _faces[f]:
            if p["mats"] and p["mats"][0] == WALL_MAT and p["asset"].split("/")[-1].startswith("SM_Wall_Tile"):
                p["mats"] = [HOLLOW] * len(p["mats"])
    print("hollow-block faces: %d of %d windowless (%d faces in all):" % (len(_hollow), len(_clear), len(_faces)),
          sorted(h + "_" + d for h, d in _hollow))
    # Paint, on what the hollow blocks left (see P_PAINTED). Colours go round a shuffled list, so they spread evenly and
    # houses next to each other in the list differ.
    _hset, _cset = set(_hollow), set(_clear)
    _chosen = [h for h in dict.fromkeys(f[0] for f in _faces) if PAINT_RNG.random() < P_PAINTED and not BLOCKS.get(h, {}).get("plain")]
    _draw_colour = shuffle_bag(PAINT_RNG, PAINT_COLOURS)
    _paint = {}
    for h in _chosen:
        mi = BM + "MI_BackAlleys_PaintedWall_" + _draw_colour()
        sides_ = [f for f in _faces if f[0] == h and f not in _hset]
        picked = [f for f in sides_ if f not in _cset or PAINT_RNG.random() < P_PAINT_SIDE] or sides_[:1]
        for f in picked:
            _paint[f] = mi
    _contrast = {h for h in _chosen if BAND_MIX_RNG.random() < P_BAND_CONTRAST}
    for f, mi in _paint.items():
        for p in _faces[f]:
            a_ = p["asset"].split("/")[-1]
            if p["mats"] and (a_ in ("SM_Wall_Tile_01", "SM_Wall_Tile_Blue", "SM_Wall_Tile_03", "SM_WallDoor_01",
                                     "SM_Wall_Windows_01") or (a_ == "SM_Wall_14" and f[0] not in _contrast)):
                p["mats"] = [mi] * len(p["mats"])
    _colour = {f[0]: mi for f, mi in _paint.items()}
    for p in items:                                 # parapets follow their side, or the house where no wall shows there
        parts = p["label"].split("_")
        if parts[0] == "Parapet" and p["mats"]:
            house = parts[1][:-1] if parts[1].endswith("b") and parts[1][:-1] in BLOCKS else parts[1]
            f = (house, parts[2][0])
            if f in _paint or (f not in _faces and house in _colour):
                p["mats"] = [_paint.get(f, _colour.get(house))] * len(p["mats"])
    # Between the floors, a building has one of three treatments, on all its faces. User 2026-11-04: "so the building will
    # either has 1. No borders, 2. A border 3. A portruding band"; "if the paintjob for the whole face is the same, remove
    # the border"; "the band between the 1st and 2nd floor, not the top floor". So a painted house, whose band matches, gets
    # none or the protruding band, and an unpainted house any of the three.
    # Shuffle bags, so they spread evenly in no visible order. The border is each storey's Trim300 but the top one's.
    # Protruding band: BAND_OUT clears the trims' 7 cm (at 5 cm they hid it: "i cant see it"). It gets thicker, not moved:
    # the back stays 20 cm behind the face. Not on houses touching the gallery (they get no border): it would stand above
    # the deck floor and in the stairs' headroom. At an outside corner with another protruding band, it meets it as the trims
    # do: east/west runs past the corner to flush with that band's face, north/south stops at that band's back, 20 cm in
    # (t0/t1 say which: > 0 and -9; see corner_adjust). With a flush face there, it stops just short of the corner.
    _draw_three = shuffle_bag(BAND_RNG, ("none", "border", "proud"))
    _draw_two = shuffle_bag(BAND_RNG, ("none", "proud"))
    _style = {}
    for h in dict.fromkeys(f[0] for f in _faces):
        if BLOCKS[h]["storeys"] < 2:
            continue
        st = "border" if h in _contrast else (_draw_two() if h in _colour else _draw_three())
        if st == "proud" and (_near(BLOCKS[h], L["deck"], 0.05) or any(_near(BLOCKS[h], g, 0.05) for g in L["stairs"])):
            st = "none"
        _style[h] = st


    def _between_floors(p, house):
        return int(p["label"].split("_")[1][1:]) < BLOCKS[house]["storeys"] - 1


    _gone = {id(p) for f, ps in _faces.items() if _style.get(f[0], "border") != "border" for p in ps
             if p["label"].endswith("_Trim300") and _between_floors(p, f[0])}
    items[:] = [p for p in items if id(p) not in _gone]
    _proud = {f for f, ps in _faces.items() if _style.get(f[0]) == "proud"
              and any(p["label"].endswith("_Band") and _between_floors(p, f[0]) for p in ps)}
    _dir_letter = {(1, 0): "E", (-1, 0): "W", (0, 1): "S", (0, -1): "N"}


    def _band_end(t, house, along):
        if t > 0 or t == -9.0:                      # an outside corner (see corner_adjust)
            if (house, _dir_letter[along]) not in _proud:
                return 9.0
            return 10.0 + BAND_OUT if t > 0 else -10.0
        return 0.0


    for f in _proud:
        for p in _faces[f]:
            if p["label"].endswith("_Band") and _between_floors(p, f[0]):
                side_, px_, py_, w_, t0_, t1_, sh_ = p["band"]
                rx_, ry_ = RUN[side_]
                ahead = (int(ry_), int(-rx_))               # the run's direction, in layout axes
                b0_ = _band_end(t0_, f[0], (-ahead[0], -ahead[1]))
                b1_ = _band_end(t1_, f[0], ahead)
                x_, y_ = at(px_, py_, side_, -b0_, BAND_OUT)
                p["loc"][0], p["loc"][1] = round(x_, 1), round(y_, 1)
                p["scale"][0] = round((20.0 + BAND_OUT) / 20.0, 4)
                p["scale"][1] = round((w_ + b0_ + b1_ + TILE_LAP) / 200.0, 4)
    # Drips, after the treatments. User 2026-11-04: "you need to reevaluate the placements of Dirt decals, becuase of the new
    # border and band rules". Their hard top edge sat at +292, tucked behind the border, which is what's gone between floors:
    # - protruding band: the edge goes up behind the band (DRIP_EDGE_BAND), so the streaks come out from under the ledge;
    # - no border: nothing can hide it, and dirt doesn't start mid-wall, so the lower floors' drips go. A face that had them
    #   gets drips at the top floor instead, under the top border, if it has none there.
    # A border, and every top floor, stay as they were (the top storey's Trim300 is always there).
    _moved, _cut, _added = 0, 0, 0
    _had_low, _has_top = set(), set()
    _keep = []
    for p in items:
        parts = p["label"].split("_")
        if p["folder"] == DC and parts[0] == "Drips" and len(parts) > 3:
            h = parts[1][:-1] if parts[1].endswith("b") and parts[1][:-1] in BLOCKS else parts[1]
            st = _style.get(h)
            f = (h, parts[2][0])
            if st and int(parts[2][1:]) < BLOCKS[h]["storeys"] - 1:
                if st == "proud":
                    p["loc"][2] = round(p["loc"][2] + DRIP_EDGE_BAND - DRIP_EDGE_Z, 1)
                    _moved += 1
                elif st == "none":
                    _had_low.add(f)
                    _cut += 1
                    continue
            elif st:
                _has_top.add(f)
        _keep.append(p)
    items[:] = _keep
    for h, d in sorted(_had_low - _has_top):
        for r in wall_runs:
            q = r["name"].split("_")
            if q[0] == h and q[1] == d + str(BLOCKS[h]["storeys"] - 1):
                n0 = len(items)
                _added += drips_on(r)
                for p in items[n0:]:
                    p["loc"][2] = round(p["loc"][2] + FLOOR_H, 1)
    print("drips: %d moved up behind protruding bands, %d lower-floor ones cut, %d added at the top floor" % (
        _moved, _cut, _added))
    print("between the floors, of %d multi-storey houses: %s; %d border pieces removed; contrasting bands on %d of %d "
          "painted houses" % (len(_style), dict(sorted(__import__("collections").Counter(_style.values()).items())),
                              len(_gone), len(_contrast), len(_chosen)))
    _letter = {(1, 0): "E", (-1, 0): "W", (0, 1): "S", (0, -1): "N"}
    _ncol = 0
    for k, ((lx, ly, _dirs), col) in enumerate(sorted(COLUMNS.items())):
        s1, s2 = (_letter[d] for d in col["dirs"])
        for bid, b in BLOCKS.items():
            h = bid[:-1] if bid.endswith("b") and bid[:-1] in BLOCKS else bid
            if (h, s1) not in _paint or (h, s2) not in _paint or _paint[(h, s1)] != _paint[(h, s2)]:
                continue
            cx = b["x1"] if "E" in (s1, s2) else b["x0"]
            cy = b["y1"] if "S" in (s1, s2) else b["y0"]
            if abs(cx - lx) < 1e-3 and abs(cy - ly) < 1e-3:
                for p in items:
                    if p["label"].startswith("Column_%d_" % k):
                        p["mats"] = [_paint[(h, s1)]]
                        _ncol += 1
                break
    print("paint: %d of %d houses; faces %d painted, %d hollow, %d bare; %d columns" % (
        len(_chosen), len(set(f[0] for f in _faces)), len(_paint), len(_hollow), len(_faces) - len(_paint) - len(_hollow),
        _ncol))

