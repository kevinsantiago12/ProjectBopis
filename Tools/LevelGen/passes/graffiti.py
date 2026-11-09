# Pass `graffiti`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Graffiti decals.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# Graffiti. User 2026-11-06: "added 10 graffitits": five crew tags and five painted warnings, white-on-black masks in /Game/Project_Bopis_Graffiti_Decals, which stay as supplied. Decals, with the
# paint in the material (create_graffiti_materials_ue.py). On the clear stretches of ground-floor walls, at hand height, and on closed shutters with no poster on them, where "Bawal Pumarada" and
# "Huwag Harangan ang Daan" belong. Thin walls stay off under their rule; hollow-block walls get big tags of their own, further down. One to a house, the same image not twice in a view. Tags lean a little; warnings less.
STREET_GRAFFITI = True
DR_GRAFFITI = "BackAlleys/Graffiti"
GRAF_RNG = random.Random(271)
GRAF_WALLS, GRAF_SHUTTERS = 13, 3
GRAF_GAP, GRAF_SAME_GAP = 350.0, 1100.0
GRAF_ROLL = 90.0
GRAF_TAGS = {"Bakod_7": ("Black", "Red"), "Eskinita_13": ("White", "Blue"), "Kanto_Boys": ("Black", "Blue"), "Loob_Crew": ("Black", "White"), "Siksik": ("Red", "Black")}
GRAF_SIGNS = {"Bawal_Magtapon_ng_Basura": ("Black", "Red"), "Bawal_Pumarada": ("White", "Red"), "Bawal_Pumasok": ("Red", "White"), "Bawal_Umihi_Dito": ("Black", "Red"),
              "Huwag_Harangan_ang_Daan": ("Black", "White")}
GRAF_ON_SHUTTERS = ("Bawal_Pumarada", "Huwag_Harangan_ang_Daan", "Kanto_Boys", "Siksik", "Bakod_7")
GRAF_BANDS = ((70.0, 200.0), (85.0, 215.0), (60.0, 180.0), (70.0, 170.0))      # what shows of the image, up the wall. The masks' ink fills about 80% of the square
GRAF_INK = 0.8
GRAF_LIGHT = ("White", "Cream", "Yellow", "Mint", "Peach")
_graf_n = {"walls": 0, "shutters": 0}
_graf_done = []


def _graffiti(label, x_, y_, z_, side, name, w_, light=False, avoid=()):
    table = GRAF_TAGS if name in GRAF_TAGS else GRAF_SIGNS
    paints = [c_ for c_ in table[name] if not (light and c_ == "White") and c_ not in avoid] or list(table[name])
    tilt = GRAF_RNG.uniform(-4.0, 4.0) if name in GRAF_TAGS else GRAF_RNG.uniform(-1.2, 1.2)
    nx, ny = NORMAL[side]
    put(label, BM + "MI_BackAlleys_Spray_%s_%s" % (name, GRAF_RNG.choice(paints)), x_, y_, z_, math.degrees(math.atan2(-ny, -nx)), (0.03, w_ / 512.0, w_ / 512.0), folder=DR_GRAFFITI,
        roll=GRAF_ROLL + tilt, decal=True)
    _graf_done.append((x_, y_, name))


# User 2026-11-06, of a block of posters behind a power pole: "there is no way he was able to stick that behind the post". A wall with a post standing this close to it can't be reached.
POST_REACH, POST_CLEAR = 90.0, 30.0
_posts = [(p["loc"][0], p["loc"][1]) for p in items if (p["folder"] == DR_POLES and "Electric_Pole" in p["asset"]) or p["asset"].endswith("SM_Pillar_01")]


def _post_in_front(x_, y_, nx, ny, half):
    """A post stands between this spot on a wall and whoever would paste or paint it. half: half the width along the wall."""
    return any(0.0 < (px_ - x_) * nx + (py_ - y_) * ny < POST_REACH and abs((px_ - x_) * -ny + (py_ - y_) * nx) < half + POST_CLEAR for px_, py_ in _posts)


def _graf_room(x_, y_, name):
    return all(math.hypot(x_ - o[0], y_ - o[1]) >= (GRAF_SAME_GAP if o[2] == name else GRAF_GAP) for o in _graf_done)


if STREET_GRAFFITI and STREET_POSTERS:
    _posters_now = [p for p in items if p["folder"] == DR_POSTERS]
    _bare_shops = []
    for u, s0, wid in _shops:
        Xc, Yc = at(u["x"], u["y"], u["side"], s0 + wid / 2, 8.8)
        rx, ry = RUN[u["side"]]
        nx, ny = NORMAL[u["side"]]
        if not any(abs((p["loc"][0] - Xc) * nx + (p["loc"][1] - Yc) * ny) < 16.0 and abs((p["loc"][0] - Xc) * rx + (p["loc"][1] - Yc) * ry) < wid / 2 + 40.0 for p in _posters_now):
            _bare_shops.append((u, s0, wid))
    GRAF_RNG.shuffle(_bare_shops)
    _graf_houses = set()
    _draw_shutter_graf = shuffle_bag(GRAF_RNG, GRAF_ON_SHUTTERS)
    for u, s0, wid in _bare_shops[:GRAF_SHUTTERS]:
        name = _draw_shutter_graf()
        w_ = min(GRAF_RNG.uniform(135.0, 165.0), wid * 0.98)
        x_, y_ = at(u["x"], u["y"], u["side"], s0 + wid / 2 + GRAF_RNG.uniform(-8.0, 8.0), 8.8)
        _graffiti("Graffiti_%s_Shutter" % u["label"], x_, y_, u["z"] + GRAF_RNG.uniform(120.0, 170.0), u["side"], name, w_)
        _graf_houses.add(u["house"])
        _graf_n["shutters"] += 1
    # Where there's room: the longest clear wall goes first, as it's the one that reads as bare.
    _graf_spots = []
    for name_, ts in _run_tiles.items():
        t0 = ts[0]
        if t0["s"] != 0 or _hollow_face(t0) or ts[-1]["off"] + ts[-1]["w"] - t0["off"] < 200.0:
            continue
        for band in GRAF_BANDS:
            for a_, e_ in _stretches(ts, band):
                _graf_spots.append((e_ - a_, GRAF_RNG.random(), name_, band, a_, e_))
    _graf_spots.sort(key=lambda g_: -g_[0] * GRAF_RNG.uniform(0.75, 1.25))
    _draw_graf = shuffle_bag(GRAF_RNG, tuple(sorted(GRAF_TAGS)) + tuple(sorted(GRAF_SIGNS)))
    for _len, _r, name_, band, a_, e_ in _graf_spots:
        if _graf_n["walls"] >= GRAF_WALLS:
            break
        ts = _run_tiles[name_]
        t0 = ts[0]
        if t0["house"] in _graf_houses:
            continue
        w_ = min(GRAF_RNG.uniform(125.0, 185.0), (e_ - a_) / 0.92, (band[1] - band[0]) / GRAF_INK)
        if w_ < 95.0:
            continue
        s_ = GRAF_RNG.uniform(a_ + 0.46 * w_, e_ - 0.46 * w_)
        x_, y_ = at(t0["x"], t0["y"], t0["side"], s_, 2.0)
        z_ = t0["z"] + (band[0] + band[1]) / 2
        if _post_in_front(x_, y_, NORMAL[t0["side"]][0], NORMAL[t0["side"]][1], 0.46 * w_):
            continue
        for _try in range(10):
            name = _draw_graf()
            if _graf_room(x_, y_, name):
                break
        else:
            continue
        light_ = any(k_ in str(_paint.get((t0["house"], t0["letter"]), "")) for k_ in GRAF_LIGHT)
        _graffiti("Graffiti_%s_%d" % (t0["label"], _graf_n["walls"]), x_, y_, z_, t0["side"], name, w_, light_)
        _claim(_wbox(t0, s_ - 0.46 * w_, s_ + 0.46 * w_, z_ - w_ * GRAF_INK / 2, z_ + w_ * GRAF_INK / 2, 3.0))
        _graf_houses.add(t0["house"])
        _graf_n["walls"] += 1
    # Big paint on the hollow-block walls. User 2026-11-06: "yes do grafitti on hollow blocks, actually allowed to paint them big". The ground floors of those walls are full of posters, and the
    # upper storeys are bare, so one crew tag to each upper wall, sized from the wall: a warning has no business 5 m up. Own random sequence, last, so nothing above moves.
    GRAF_BIG_RNG = random.Random(277)
    _draw_big_tag = shuffle_bag(GRAF_BIG_RNG, tuple(sorted(GRAF_TAGS)))
    _graf_n["big"] = 0
    _big_paints = []
    for name_ in sorted(_run_tiles):
        ts = _run_tiles[name_]
        t0 = ts[0]
        if t0["s"] != 1 or not _hollow_face(t0):
            continue
        total = ts[-1]["off"] - t0["off"] + ts[-1]["w"]
        sh_ = BLOCKS[t0["bid"]]["sh"]
        z0_, z1_ = t0["z"] + 30.0, t0["z"] + sh_ - 25.0
        w_max = min((z1_ - z0_) / GRAF_INK, (total - 2.0 * FACE_EDGE) / 0.92)
        if w_max < 200.0:
            continue
        w_ = w_max * GRAF_BIG_RNG.uniform(0.74, 1.0)
        s_ = GRAF_BIG_RNG.uniform(FACE_EDGE + 0.46 * w_, total - FACE_EDGE - 0.46 * w_)
        z_ = (z0_ + z1_) / 2 + GRAF_BIG_RNG.uniform(-1.0, 1.0) * ((z1_ - z0_) - w_ * GRAF_INK) / 2
        box_ = _wbox(t0, s_ - 0.46 * w_, s_ + 0.46 * w_, z_ - w_ * GRAF_INK / 2, z_ + w_ * GRAF_INK / 2, 10.0)
        if not _poster_clear(box_) or not _pipe_free(t0, s_ - 0.46 * w_, s_ + 0.46 * w_) or not _stair_clear(t0, s_ - 0.46 * w_, s_ + 0.46 * w_, t0["z"]):
            print("  big graffiti: no room on", t0["label"])
            continue
        x_, y_ = at(t0["x"], t0["y"], t0["side"], s_, 2.0)
        # Up here it can stand over another wall's low tag, so only the same image has to keep away.
        for _try in range(10):
            name = _draw_big_tag()
            if all(math.hypot(x_ - o[0], y_ - o[1]) >= GRAF_SAME_GAP for o in _graf_done if o[2] == name):
                break
        else:
            print("  big graffiti: no image for", t0["label"])
            continue
        # A crew paints twice, but in another colour, or it reads as a copy.
        _graffiti("Graffiti_%s_Big" % t0["label"], x_, y_, z_, t0["side"], name, w_, avoid=[a_.rsplit("_", 1)[1] for a_ in _big_paints if ("_" + name + "_") in a_])
        _big_paints.append(items[-1]["asset"])
        _claim(box_)
        _graf_n["big"] += 1
        print("  big graffiti:", t0["label"], name, "%.0f cm" % w_)
    print("graffiti:", _graf_n, sorted(o[2] for o in _graf_done))

