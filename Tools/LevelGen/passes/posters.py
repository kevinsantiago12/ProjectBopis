# Pass `posters`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Posters and ads.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# Posters and ads. User 2026-11-05: "I can have gpt make product ads and movie posters, as well as election campaign posters", then "Added the Ads, btw, these
# ads are AI generated, they are currently placeholder labeled. I might decide to use them but we will see. Now see what you can do with it". So: 24 images
# in /Game/Project_Bopis_Posters, untouched, one switch, one folder, one material instance each (create_poster_materials_ue.py), easy to take out.
# The scale is from the user's photo ("look at this scale, use this for the poster"): a Manila wall with a man cycling past. Each sheet is about 61 x 91 cm, and they're
# pasted edge to edge in blocks, one candidate to a block, from just above the ground to over his head. So POSTER_AREA is that sheet's area, whatever an image's shape, and
# never smaller ("use your original size and make bigger variations"). Election posters fill walls, the same one over and over. Movie posters and ads go side by side, but
# never the same one twice: "only put together indentical posters for candidates type posters, you can put movie posters together side by side but not the same over and over,
# same goes for product ads".
# On the clear stretches of a whole wall, across tile joints, FACE_EDGE from its ends ("too close to the edge of the face"), never over a door or window. Hollow-block faces take
# them too, and nothing else ("Try to not have any first floor walls featureless, except hollow block, which yu can put posters on"). So do the shop row's plain stretches and
# the door end walls, which aren't wall tiles. A movie poster or ad only comes round again POSTER_GAP on, so two don't share a view; election posters may, as campaigns do.
STREET_POSTERS = True
DR_POSTERS = "BackAlleys/Posters"
POSTER_RNG = random.Random(227)
POSTER_GAP = 1000.0
POSTER_AREA = 61.0 * 91.0
# User 2026-11-06: "The posters are generally tiny", "Ads and campaign material needs to be seen from further away", "find a way to scale the posters more". So sheets are this much bigger than the
# photo's, as far as a stretch of wall and its band allow, and never under the photo's. Elections stack two rows where that still leaves them at least POSTER_TWO_ROWS, or one big row where it doesn't.
POSTER_SCALE, POSTER_TWO_ROWS = 1.8, 1.5
POSTER_TALL, POSTER_LOW, POSTER_MID = (18.0, 294.0), (18.0, 240.0), (76.0, 234.0)   # floor to the trim, floor to under the highest vent blocks, and eye level
# Vent blocks stand at several heights, and most came down since those bands were set: their bottoms are 173 to 240 cm off the floor. User 2026-11-06, of a wall with vents
# and nothing under them: "even this is bare, it has vents but needs something". So two more bands: under one row of vents, and under two.
POSTER_UNDER, POSTER_SHORT = (18.0, 209.0), (60.0, 168.0)
P_POSTER_TALL, P_POSTER_MID, P_POSTER_SHUTTER, P_POSTER_GONE = 0.92, 0.75, 0.55, 0.07
POSTER_MOVIES = {"Ang_Tagapaslang": (592, 887), "Dugo_sa_Lansangan": (591, 887), "Hatinggabing_Takas": (512, 1024), "Huli_Ka_Kuya": (512, 1024),
                 "Huling_Biyahe_sa_Maynila": (887, 887), "May_Bukas_Pa_Kuya": (591, 887), "Sa_Huling_Sakay": (512, 1024), "Suntok_sa_Pier": (887, 887)}
POSTER_ADS = {"Bayani_Baterya": (724, 724), "Gising_Kape": (542, 724), "Kanto_Cola": (1024, 1536), "Presko_Mint": (724, 724), "Sabaw_Sarap": (544, 724),
              "Sinag_VCD": (544, 724), "TextKanto": (1024, 1536), "Tibay_Selyas": (724, 724), "Tulay_Sanglaan": (1024, 1536)}     # Puting_Araw: imported as a normal map, so it can't be used yet
POSTER_ELECTION = {"Arturo_Villareal": {"Arturo_Villareal_01": (768, 1024), "Arturo_Villareal_02": (887, 887)},
                   "Benjamin_Mercado": {"Benjamin_Mercado_01": (768, 1024), "Benjamin_Mercado_02": (887, 887)},
                   "Teresa_de_Vera": {"Teresa_de_Vera_01": (887, 887), "Teresa_de_Vera_02": (887, 887)}}
# User 2026-11-07: "Project_Bopis_Local_Business_Signs Added, use this for new posters (add, dont replace the ones already there)". Five hand-painted local ads
# (a hardware, a vulcanizing shop, a rice seller, a VCD rental, an internet cafe), 2:3, in /Game/Project_Bopis_Local_Business_Signs/Posters. They join the
# product ads: side by side, never the same one twice.
POSTER_LOCAL = {"01_Hardware": (1024, 1536), "02_Vulcanizing": (1024, 1536), "03_Bigasan": (1024, 1536), "04_VCD_Rental": (1024, 1536),
                "05_Internet_Cafe": (1024, 1536)}
POSTER_ADS.update(POSTER_LOCAL)
_poster_px = dict(POSTER_MOVIES)
_poster_px.update(POSTER_ADS)
for _d in POSTER_ELECTION.values():
    _poster_px.update(_d)
_draw_movie = shuffle_bag(POSTER_RNG, tuple(POSTER_MOVIES))
_draw_ad = shuffle_bag(POSTER_RNG, tuple(POSTER_ADS))
_draw_candidate = shuffle_bag(POSTER_RNG, tuple(POSTER_ELECTION))
_draw_tall = shuffle_bag(POSTER_RNG, ("election", "election", "election", "election", "election", "movie", "movie", "ad"))
_draw_mid = shuffle_bag(POSTER_RNG, ("movie", "ad", "ad", "ad", "election"))
_draw_big = shuffle_bag(POSTER_RNG, (1.0, 1.0, 1.0, 1.0, 1.15, 1.3))      # movie posters and ads; a block of election posters is one print run
_poster_at = {}
_poster_n = {"movie": 0, "ad": 0, "election": 0}
_poster_lots = [0]


def _far_enough(name, X_, Y_):
    return all(math.hypot(X_ - o[0], Y_ - o[1]) >= POSTER_GAP for o in _poster_at.get(name, ()))


def _pick_design(draw, X_, Y_, pool=(), exclude=()):
    unseen = sorted(k for k in pool if k not in _poster_at and k not in exclude)    # every design has its turn before any comes round again
    if unseen:
        return POSTER_RNG.choice(unseen)
    for _ in range(12):
        name = draw()
        if name not in exclude and _far_enough(name, X_, Y_):
            return name
    return None


def _side_by_side(first, draw, pool, X_, Y_, n):
    """A row of different movie posters or ads, as many of n as can be found: never the same one twice."""
    names = [first]
    while len(names) < n:
        other = _pick_design(draw, X_, Y_, pool, names)
        if other is None:
            break
        names.append(other)
    return names


def _sheet_w(name, k=1.0):
    """A sheet's width: the photo's area at this image's shape. A movie one-sheet is a little bigger."""
    w_, h_ = _poster_px[name]
    return math.sqrt(POSTER_AREA * (1.3 if name in POSTER_MOVIES else 1.0) * w_ / float(h_)) * k


def _paste(label, u, name, s_c, z_c, wid, n_, swing):
    """One sheet, centred s_c along tile u and z_c up. As the plywood sheets: X along the wall, local Y down, so the image reads right way round."""
    hgt = wid * _poster_px[name][1] / float(_poster_px[name][0])
    side = u["side"]
    run3 = (float(RUN[side][0]), float(RUN[side][1]), 0.0)
    out3 = (float(NORMAL[side][0]), float(NORMAL[side][1]), 0.0)
    tilt = POSTER_RNG.uniform(-swing, swing)
    X3, up3 = v_rot(run3, out3, tilt), v_rot((0.0, 0.0, 1.0), out3, tilt)
    x_, y_ = at(u["x"], u["y"], side, s_c, n_)
    put_axes(label, PLANE, X3, (-up3[0], -up3[1], -up3[2]), out3, (wid / 100.0, hgt / 100.0, 1.0), (0.0, 0.0, 0.0), (x_, y_, z_c),
             mats=[BM + "MI_BackAlleys_Poster_" + name])
    items[-1]["folder"] = DR_POSTERS
    items[-1]["draw"] = CULL_FAR        # meant to be read from down the street
    items[-1]["noshadow"] = True
    items[-1]["coll"] = "PosterPaper"       # ignored by everything but the Paper trace: shots hit the wall behind, and throw paper


def _block(t0, s0, s1, base, columns, rows, band, n0, k=1.0, own_size=False):
    """Sheets edge to edge: columns is the image of each column, rows how many high, as many columns as fit in s0..s1. Laps and misses by a centimetre, as pasted by hand,
    and here and there one has been torn off. Returns (sheets, the columns that went up, where they start and end)."""
    # A block has every column one height, so the rows line up and nothing shows between them, as in the photo. Images of another shape come out wider or narrower.
    # own_size: a row of different movie posters or ads, each its own full size, centred on one line. Sharing a height there made a tall image's sheet too narrow.
    first_ = columns[0]
    band_h = band[1] - band[0]
    base_w = _sheet_w(first_, 1.0)
    base_h = max(_sheet_w(n_, 1.0) * _poster_px[n_][1] / float(_poster_px[n_][0]) for n_ in columns) if own_size else base_w * _poster_px[first_][1] / float(_poster_px[first_][0])
    if rows >= 2 and band_h / (rows * base_h) >= POSTER_TWO_ROWS:
        k = min(k, band_h / (rows * base_h))
    elif rows >= 2:
        rows = 1
    k = max(1.0, min(k, (s1 - s0) / base_w, band_h / base_h))
    row_h = _sheet_w(first_, k) * _poster_px[first_][1] / float(_poster_px[first_][0])
    widths, kept = [], []
    for name in columns:
        w_ = _sheet_w(name, k) if own_size else row_h * _poster_px[name][0] / float(_poster_px[name][1])
        if sum(widths) + w_ > s1 - s0:
            break
        widths.append(w_)
        kept.append(name)
    if not kept:
        return 0, [], 0.0, 0.0
    tall_ = max(w_ * _poster_px[n_][1] / float(_poster_px[n_][0]) for w_, n_ in zip(widths, kept)) if own_size else row_h
    if tall_ > band[1] - band[0]:                       # a long sheet in a short band would run into the vents above it
        return 0, [], 0.0, 0.0
    _poster_lots[0] += 1
    lot = "Poster_%s_L%d" % (t0["label"], _poster_lots[0])
    total = sum(widths)
    start = s0 + POSTER_RNG.uniform(0.0, min(30.0, s1 - s0 - total))
    rows = max(1, min(rows, int((band[1] - band[0]) / tall_)))
    if rows == 1:
        bottom = max(band[0], min(band[1] - tall_, POSTER_RNG.uniform(148.0, 172.0) - tall_ / 2))
    else:
        bottom = band[0] + POSTER_RNG.uniform(0.0, max(0.0, band[1] - band[0] - rows * tall_) * 0.5)
    placed = 0
    s_ = start
    for c_, (name, w_) in enumerate(zip(kept, widths)):
        h_ = w_ * _poster_px[name][1] / float(_poster_px[name][0]) if own_size else row_h
        for r_ in range(rows):
            if rows * len(kept) >= 4 and POSTER_RNG.random() < P_POSTER_GONE:
                continue
            z_c = base + bottom + tall_ * (r_ + 0.5) if own_size else base + bottom + tall_ * r_ + h_ / 2
            _paste("%s_%d_%d" % (lot, c_, r_), t0, name, s_ + w_ / 2 + POSTER_RNG.uniform(-1.2, 1.2), z_c + POSTER_RNG.uniform(-1.2, 1.2), w_,
                   n0 + 0.15 * ((c_ + r_) % 2), 0.7 if rows * len(kept) > 1 else 1.4)
            placed += 1
        s_ += w_
    return placed, kept, start, start + total


def _poster_clear(box):
    return not any(o not in _soft_boxes and box[0] - 1.0 < o[3] and o[0] < box[3] + 1.0 and box[1] - 1.0 < o[4] and o[1] < box[4] + 1.0 and box[2] - 1.0 < o[5] and o[2] < box[5] + 1.0
                   for o in _occ.near(box, 1.0))


def _poster_free(ts, a_, e_, band):
    """Nothing on a stretch of this wall between the band's heights, and somewhere to stand in front of it."""
    t0 = ts[0]
    mid = (a_ + e_) / 2
    u = next((q_ for q_ in ts if q_["off"] - t0["off"] <= mid < q_["off"] - t0["off"] + q_["w"]), None)
    if u is None:
        return False
    local = mid - (u["off"] - t0["off"])
    if u["kind"] in ("SM_Wall_Windows_01", "SM_WallDoor_01"):
        if 30.0 * u["sx"] - 5.0 < local < 195.0 * u["sx"] + 5.0:
            return False
    elif u["kind"] not in _plain_tile:
        return False
    if t0["s"] == 0:
        if not _ground_open(t0, mid, 60.0):
            return False
    else:
        lx, ly = _lay(*at(t0["x"], t0["y"], t0["side"], mid, 45.0))
        dk_ = L["deck"]
        if not (dk_["x0"] < lx < dk_["x1"] and dk_["y0"] < ly < dk_["y1"]):
            return False
    box = _wbox(t0, a_, e_, t0["z"] + band[0], t0["z"] + band[1], 10.0)
    return _pipe_free(t0, a_, e_) and _stair_clear(t0, a_, e_, t0["z"]) and _poster_clear(box)


def _stretches(ts, band):
    """The clear stretches of a whole wall, FACE_EDGE from its ends."""
    t0 = ts[0]
    total = ts[-1]["off"] - t0["off"] + ts[-1]["w"]
    out, cur, a_ = [], None, FACE_EDGE
    while a_ < total - FACE_EDGE:
        e_ = min(a_ + 8.0, total - FACE_EDGE)
        if _poster_free(ts, a_, e_, band):
            cur = a_ if cur is None else cur
        elif cur is not None:
            out.append((cur, a_))
            cur = None
        a_ = e_
    if cur is not None:
        out.append((cur, total - FACE_EDGE))
    return out


if STREET_POSTERS:
    _soft_boxes |= {_occ_of(p) for p in items if p["folder"] == DR_PATCH and p["asset"] == PLANE}
    # A room claims the whole height of its rectangle, to keep pipes and air conditioners off it, but the wall under it is still a wall that shows ("Try to not have any first
    # floor walls featureless"). So posters go under a room, and only the struts landing on the wall stop them.
    _soft_boxes |= {(o[0], o[1], 0.0, o[2], o[3], 3000.0) for o in _room_rects}
    _occ += [_wbox(t_, s_ - 8.0, s_ + 8.0, t_["z"] - 120.0, t_["z"], 30.0) for t_, s_ in _room_struts]
    _spots = []

    def _minus(a_, b_, taken):
        """a_..b_ with the stretches already taken cut out."""
        out, at_ = [], a_
        for c0, c1 in sorted(taken):
            if c1 <= at_ or c0 >= b_:
                continue
            if c0 > at_:
                out.append((at_, c0))
            at_ = max(at_, c1)
        if at_ < b_:
            out.append((at_, b_))
        return out

    for name in sorted(_run_tiles):
        ts = _run_tiles[name]
        t0 = ts[0]
        if not (t0["s"] == 0 or (t0["s"] == 1 and abs(t0["z"] - (400.0 + FLOOR_H)) < 1.0)):
            continue
        taken = []
        for how, band in (("tall", POSTER_TALL), ("low", POSTER_LOW), ("mid", POSTER_MID), ("under", POSTER_UNDER), ("short", POSTER_SHORT)):
            found = []
            for a_, b_ in _stretches(ts, band):
                for p_, q_ in _minus(a_, b_, taken):
                    if q_ - p_ >= 62.0:
                        _spots.append((how, ts, p_, q_))
                    found.append((p_, q_))
            taken += found

    def _extra_wall(label, x_, y_, z_, side, a_, b_):
        """A clear stretch of a wall that isn't made of wall tiles."""
        t = {"x": x_, "y": y_, "z": z_, "side": side, "label": label}
        if b_ - a_ >= 62.0 and _pipe_free(t, a_, b_) and _poster_clear(_wbox(t, a_, b_, z_ + POSTER_TALL[0], z_ + POSTER_TALL[1], 10.0)):
            _spots.append(("tall", [t], a_, b_))

    for p in items:
        if p["label"] == "B2_S0_2_1":       # the door frame module: its door is at 92-207, and the half wall carries on to 450, the wall's end
            _extra_wall(p["label"], p["loc"][0], p["loc"][1], p["loc"][2], "south", 4.0, 88.0)
            _extra_wall(p["label"], p["loc"][0], p["loc"][1], p["loc"][2], "south", 212.0, 450.0 - FACE_EDGE)
        elif p["label"] == "B2_S0_0_half":
            _extra_wall(p["label"], p["loc"][0], p["loc"][1], p["loc"][2], "south", 4.0, 110.0)
    for d in L["doors"]:                    # a door end wall: 450 across its alley, the door in the middle, 56 either side
        n_ = FACE[d["face"]]
        cx_, cy_ = ue(d["x"], d["y"])
        rx_, ry_ = RUN[n_]
        x0_, y0_ = cx_ - rx_ * 225.0, cy_ - ry_ * 225.0
        _extra_wall(d["id"] + "_S0_0", x0_, y0_, FLOOR_H, n_, FACE_EDGE, 165.0)
        _extra_wall(d["id"] + "_S0_2", x0_, y0_, FLOOR_H, n_, 285.0, 450.0 - FACE_EDGE)
    POSTER_RNG.shuffle(_spots)
    POSTER_BANDS = {"tall": POSTER_TALL, "low": POSTER_LOW, "mid": POSTER_MID, "under": POSTER_UNDER, "short": POSTER_SHORT}
    for how, ts, a_, b_ in _spots:
        # A long stretch takes several lots side by side, as in the photo, with a little wall between.
        while b_ - a_ >= 62.0:
            if POSTER_RNG.random() > (P_POSTER_TALL if how != "mid" else P_POSTER_MID):
                break
            t0 = ts[0]
            base = t0["z"]
            room_s = b_ - a_
            band = POSTER_BANDS[how]
            Xc, Yc = at(t0["x"], t0["y"], t0["side"], (a_ + b_) / 2, 2.0)
            if how != "mid" and room_s >= 190.0:
                kind = _draw_tall()                     # the long walls go mostly to the campaigns
            elif room_s >= 76.0 and any(k not in _poster_at for k in POSTER_MOVIES):
                kind = "movie"
            elif any(k not in _poster_at for k in POSTER_ADS):
                kind = "ad"
            else:
                kind = _draw_tall() if how != "mid" else _draw_mid()
            k_ = 1.0
            if kind == "movie":
                name = _pick_design(_draw_movie, Xc, Yc, POSTER_MOVIES)
                if name is None:
                    kind = "election"
                else:
                    k_ = POSTER_SCALE * _draw_big()
                    columns = _side_by_side(name, _draw_movie, POSTER_MOVIES, Xc, Yc, POSTER_RNG.choice((1, 2, 2, 3)))
                    rows = 1
            elif kind == "ad":
                name = _pick_design(_draw_ad, Xc, Yc, POSTER_ADS)
                if name is None:
                    kind = "election"
                else:
                    k_ = POSTER_SCALE * _draw_big()
                    columns = _side_by_side(name, _draw_ad, POSTER_ADS, Xc, Yc, POSTER_RNG.choice((1, 1, 2, 2, 3)))
                    rows = 1
            if kind == "election":
                cand = POSTER_ELECTION[_draw_candidate()]
                first, second = POSTER_RNG.sample(sorted(cand), 2)
                n_c = POSTER_RNG.choice((2, 3, 3, 4, 5, 6))
                # A block of one design, or two designs of one candidate in alternate columns, as in the photo.
                columns = [first] * n_c if POSTER_RNG.random() < 0.6 else [first if c_ % 2 == 0 else second for c_ in range(n_c)]
                rows = {"tall": 2, "low": 2, "mid": 1, "under": 2, "short": 1}[how]
                k_ = POSTER_SCALE
            n_s, kept, s_a, s_b = _block(t0, a_, b_, base, columns, rows, band, POSTER_RNG.uniform(2.0, 2.3), k_, kind != "election")
            if not n_s and kind != "election":         # no room for what it drew: one election poster, the smallest sheet
                kind = "election"
                n_s, kept, s_a, s_b = _block(t0, a_, b_, base, [POSTER_RNG.choice(sorted(POSTER_ELECTION[_draw_candidate()]))], 1, band, POSTER_RNG.uniform(2.0, 2.3), POSTER_SCALE)
            if not n_s:
                break
            _poster_n[kind] += n_s
            for k in set(kept):
                _poster_at.setdefault(k, []).append((Xc, Yc))
            _claim(_wbox(t0, s_a, s_b, base + band[0], base + band[1], 3.0))
            a_ = s_b + POSTER_RNG.uniform(8.0, 70.0)
    # On closed shutters, kept to the shutter.
    for u, s0, wid in _shops:
        if POSTER_RNG.random() > P_POSTER_SHUTTER:
            continue
        kind = POSTER_RNG.choice(("movie", "ad", "election", "election"))
        Xc, Yc = at(u["x"], u["y"], u["side"], s0 + wid / 2, 8.0)
        if kind == "election":
            columns = [POSTER_RNG.choice(sorted(POSTER_ELECTION[_draw_candidate()]))] * 3
            rows = 2
        else:
            draw_ = _draw_movie if kind == "movie" else _draw_ad
            name = _pick_design(draw_, Xc, Yc)
            if name is None:
                continue
            columns = _side_by_side(name, draw_, (), Xc, Yc, 2)
            rows = 1
        s_a_, s_b_ = _inside_face(u, s0 + 3.0, s0 + wid - 3.0)
        first_ = len(items)
        n_s, kept, _sa, _sb = _block(u, s_a_, s_b_, u["z"], columns, rows, (8.0, 262.0), 9.2, POSTER_SCALE, kind != "election")      # the shutter's face is 8.8 off the wall: at 8.5 they were hidden behind it, and still threw paper
        for p_ in items[first_:]:
            p_["vol"] = True        # no lightmap: the two in the level were baked while hidden, and their lightmaps came out in black patches
        if n_s:
            _poster_n[kind] += n_s
            for k in set(kept):
                _poster_at.setdefault(k, []).append((Xc, Yc))
    _count("posters", sum(_poster_n.values()))
    print("  posters", _poster_n, "in", _poster_lots[0], "lots, of", len(_spots), "stretches;", len(_poster_at), "designs used")

