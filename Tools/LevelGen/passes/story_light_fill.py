# Pass `story_light_fill` (story levels; 2026-11-09). User: "need to add more lights to Section 1 and 2, light are unevenly distributed". The street
# pass picks its tubes, door bulbs and wall lamps at random, one to a house, so the slum's open ground was lit in patches (80% of it within
# reach of a light, the rest in dark stretches down the main street, the wash yard and the eskinitas). This adds lights where it's darkest:
# each round it measures the slum's open ground on a 1 m grid (lit within LF_REACH of a light, by its kind), tries every fitting it could
# place (a cobra lamp on a second storey, a tube on a ground-floor wall, a bulb over a door with none), and places the one that lights the
# most dark ground, until none would light LF_MIN_GAIN cells more. The street pass's own fittings and rules (no fittings on hollow-block or
# thin walls, clear of pipes, nothing in front of the wall, lamps LF_LAMP_GAP apart); against everything already placed (boxes and the
# wires as segments). After the other dressing passes, so nothing they placed moves. Every spot light gets its fill (street.py `_light`).
LIGHT_FILL = getattr(LEVEL, "LIGHT_FILL", False)
LF_REACH = {"Lamp": 500.0, "Tube": 300.0, "Bulb": 260.0}       # cm on the ground plan that a light of each kind visibly lights (its pool)
LF_MIN_GAIN, LF_MAX = 6, 40
LF_LAMP_GAP = 400.0                                             # between lamp heads in sight of each other (the street pass keeps 10 m); each must light LF_MIN_GAIN dark cells anyway
LF_TUBE_W = 140.0                                               # the narrowest plain tile that takes a 120 cm tube
_lf_n = {"lamps": 0, "pole lamps": 0, "tubes": 0, "bulbs": 0}
# Street lamps (2026-11-09, user: "Street lights are in someones balcony, that cannot happen ... remove them all and reevaluate
# placement"). A wall lamp needs open ground from its wall out (the street pass's rule): the arm crossing a lower roof put lamps
# inside covered balconies and terraces. Lamps also go on the power poles, as Philippine street lights do, arm over the street,
# under the cross-arms; they rank LF_POLE_BONUS ahead of a wall lamp lighting as much.
LF_POLE_Z, LF_POLE_R, LF_POLE_BONUS = 620.0, 15.0, 1.5      # cm up the pole, the pole's radius, the rank bonus

if LIGHT_FILL and STREET_LIGHTS_ON:
    _lf_rng = random.Random(311)
    def _lf_under(lx, ly, me=None):
        """A house or a solid (stairs, decks) stands over (lx, ly). Not cover_top: it measures from one base, and section 2's ground
        stands 180 cm up, so the whole section read as covered."""
        return any(o is not me and o["x0"] < lx < o["x1"] and o["y0"] < ly < o["y1"] for o in _cover_cands(lx, ly)) or \
            any(e["x0"] < lx < e["x1"] and e["y0"] < ly < e["y1"] for e in EXTRA_SOLID)

    def _lf_open(u, s_, n_):
        """Open ground in front of tile u, s_ cm along it and n_ cm out, no more than a curb or a ramp above the house's base. A
        staggered front stands up to 60 cm back from the street's edge; that strip (story_ground paves it) is beyond the layout's
        ground, so building_dressing's `_ground_open` calls it covered. Here it counts, when it's that close to the street."""
        b = BLOCKS[u["bid"]]
        lx, ly = _lay(*at(u["x"], u["y"], u["side"], s_, n_))
        if _lf_under(lx, ly, b):
            return False
        if outside(lx, ly) and min(LEVEL._rect_dist(a["r"], lx, ly) for a in AREAS if a["kind"] != "room") > 0.7:
            return False
        return ground_z(lx, ly) - b.get("z", 0.0) <= 40.0

    def _lf_open_at(X, Y):
        """Open ground at a world point: no house over it, and on the level's ground (or within 0.7 m of it)."""
        lx, ly = _lay(X, Y)
        return not _lf_under(lx, ly) and (not outside(lx, ly) or min(LEVEL._rect_dist(a["r"], lx, ly) for a in AREAS if a["kind"] != "room") <= 0.7)

    # The slum's open ground, 1 m cells (layout), not under a house.
    _lf_cells = []
    for a in AREAS:
        if a["kind"] == "room" or not LEVEL.dress_point((a["r"][0] + a["r"][2]) / 2, (a["r"][1] + a["r"][3]) / 2):
            continue
        x = math.floor(a["r"][0]) + 0.5
        while x < a["r"][2]:
            y = math.floor(a["r"][1]) + 0.5
            while y < a["r"][3]:
                if a["r"][0] < x < a["r"][2] and a["r"][1] < y < a["r"][3] and not _lf_under(x, y):
                    _lf_cells.append(ue(x, y))
                y += 1.0
            x += 1.0
    _lf_lights = []
    for p in items:
        if p.get("light") and not p["light"].get("fill") and p["label"].startswith("Light_"):
            kind_ = p["label"].split("_")[1]
            if kind_ in LF_REACH:
                _lf_lights.append((p["loc"][0], p["loc"][1], LF_REACH[kind_]))

    def _lf_sees(a, b):
        """No house stands between world points a and b (on the ground plan, every 40 cm): a light doesn't light the far side of a wall."""
        n_ = max(1, int(math.dist(a[:2], b[:2]) / 40.0))
        return not any(_lf_under(*_lay(a[0] + (b[0] - a[0]) * i / n_, a[1] + (b[1] - a[1]) * i / n_)) for i in range(1, n_))

    def _lf_pool(cx, cy, reach):
        """The cells a light at (cx, cy) lights: within its reach, and in its sight."""
        return {i for i, c in enumerate(_lf_cells) if math.hypot(c[0] - cx, c[1] - cy) <= reach and _lf_sees((cx, cy), c)}

    _lf_lit = set()
    for l in _lf_lights:
        _lf_lit |= _lf_pool(*l)

    def _lf_dark():
        return [c for i, c in enumerate(_lf_cells) if i not in _lf_lit]

    # Everything already placed, as boxes; wires and laundry as segments (a slanting wire's box covers a whole wall).
    _lf_skip = {"Blocks", "Lids", "Floors", "Ground", "GroundBody", "Decals", "Roofs", "Curbs", "Interiors", "GroundDirt", "Graffiti", "Peel", "Litter"}
    _lf_boxes, _lf_segs = [], []
    for p in items:
        kind_ = p["folder"].split("/")[-1]
        if not p["folder"].startswith("BackAlleys/") or kind_ in _lf_skip or p.get("decal") or p.get("light"):
            continue
        if p["asset"] == CUBE and kind_ in ("Wires", "Laundry"):
            _lf_segs.append(_rod_line(p))
            continue
        x_, y_, z_ = p["loc"]
        if kind_ == "Poles":
            _lf_boxes += [(x_ - 25, y_ - 25, z_, x_ + 25, y_ + 25, z_ + 1000), (x_ - 170, y_ - 170, z_ + 720, x_ + 170, y_ + 170, z_ + 980)]
        elif kind_ == "Lights":
            _lf_boxes.append((x_ - 40, y_ - 40, z_ - 40, x_ + 40, y_ + 40, z_ + 40))
        else:
            o_ = _occ_of(p)
            _lf_boxes.append(o_ if o_ else (x_ - 30, y_ - 30, z_ - 30, x_ + 30, y_ + 30, z_ + 30))
    _lf_boxes += [o_ for o_ in _occ if not (o_[2] == 0.0 and o_[5] == 3000.0)]

    def _lf_clear(box, pad=3.0):
        for o in _lf_boxes:
            if box[0] - pad < o[3] and o[0] < box[3] + pad and box[1] - pad < o[4] and o[1] < box[4] + pad and box[2] - pad < o[5] and o[2] < box[5] + pad:
                return False
        for a3, b3 in _lf_segs:
            if max(a3[0], b3[0]) < box[0] - pad or min(a3[0], b3[0]) > box[3] + pad or max(a3[1], b3[1]) < box[1] - pad or \
                    min(a3[1], b3[1]) > box[4] + pad:
                continue
            n_ = max(2, int(math.dist(a3, b3) / 8.0))
            for k in range(n_ + 1):
                u_ = k / n_
                q = (a3[0] + (b3[0] - a3[0]) * u_, a3[1] + (b3[1] - a3[1]) * u_, a3[2] + (b3[2] - a3[2]) * u_)
                if box[0] - pad < q[0] < box[3] + pad and box[1] - pad < q[1] < box[4] + pad and box[2] - pad < q[2] < box[5] + pad:
                    return False
        return True

    def _lf_wall_ok(u):
        b = BLOCKS[u["bid"]]
        return not _hollow_face(u) and u["bid"] not in _thin_blocks and LEVEL.dress_house(b) and \
            LEVEL.dress_point(*_lay(*at(u["x"], u["y"], u["side"], u["w"] / 2, 150.0)))

    # The fittings it could place: (kind, light point x, y, reach, place()).
    _lf_why, _lf_why_at = {}, []

    def _lf_no(kind_, why, u, s_, n_):
        """Counts why a fitting that would have lit dark ground was turned down (the report, and for tuning)."""
        x_, y_ = at(u["x"], u["y"], u["side"], s_, n_)
        if sum(1 for c in _lf_dark0 if math.hypot(c[0] - x_, c[1] - y_) <= LF_REACH[kind_]) >= LF_MIN_GAIN:
            _lf_why[kind_ + " " + why] = _lf_why.get(kind_ + " " + why, 0) + 1
            _lf_why_at.append((kind_, why, u["label"]) + tuple(round(v, 2) for v in _lay(x_, y_)))

    def _lf_candidates():
        out = []
        lamps_xy = [(l[0], l[1]) for l in _lf_lights if l[2] == LF_REACH["Lamp"]]
        for u in _wall_tiles:
            b = BLOCKS[u["bid"]]
            if not _lf_wall_ok(u):
                if u["s"] <= 1:
                    _lf_no("Tube", "hollow" if _hollow_face(u) else "thin" if u["bid"] in _thin_blocks else
                           "not dressed" if not LEVEL.dress_house(b) else "out of scope", u, u["w"] / 2, 150.0)
                continue
            if u["s"] == 1 and b["storeys"] >= 2 and not b.get("balcony"):          # a cobra lamp, as the street pass hangs them
                # Plain walls along the tile; beside an opening, just clear of it and its awning (street.py _edge_ok).
                sp_ = (u["w"] * 0.3, u["w"] * 0.5, u["w"] * 0.7) if u["kind"] in _plain_tile else (30.0 * u["sx"] - 14.0, 195.0 * u["sx"] + 14.0)
                for s_ in [v for v in sp_ if 12.0 <= v <= u["w"] - 12.0]:
                    k = 0.67
                    z_ = u["z"] + 190.0
                    reach = 299.0 * k
                    x_, y_ = at(u["x"], u["y"], u["side"], s_, 1.0)
                    hx, hy = at(u["x"], u["y"], u["side"], s_, 280.0 * k)
                    if any(math.hypot(hx - o[0], hy - o[1]) < LF_LAMP_GAP and _lf_sees((hx, hy), o) for o in lamps_xy):
                        _lf_no("Lamp", "near a lamp", u, s_, 280.0 * k)
                        continue
                    if not _edge_ok(u, s_, 12.0) or not _pipe_free(u, s_ - 16.0, s_ + 16.0):
                        _lf_no("Lamp", "edge or pipe", u, s_, 280.0 * k)
                        continue
                    # Open ground from the wall out: nothing under the arm (not a balcony, a terrace or a lower roof)
                    if not all(_lf_open(u, s_, n_) for n_ in (30.0, 60.0, reach * 0.5, reach, reach + 100.0)):
                        _lf_no("Lamp", "ground", u, s_, 280.0 * k)
                        continue
                    if not all(_reach_clear(u, s_, n_, z_ + 60.0) and not _in_room(*at(u["x"], u["y"], u["side"], s_, n_))
                               for n_ in (60.0, reach * 0.5, reach, reach + 100.0)):
                        _lf_no("Lamp", "reach", u, s_, 280.0 * k)
                        continue
                    arm = _wbox(u, s_ - 18.0, s_ + 18.0, z_ - 45.0, z_ + 85.0, reach + 20.0)
                    if not _lf_clear(arm):
                        _lf_no("Lamp", "blocked", u, s_, 280.0 * k)
                        continue
                    out.append(("Lamp", hx, hy, LF_REACH["Lamp"], (u, s_, k, z_), arm))
            elif u["s"] == 1:
                _lf_no("Lamp", "one storey" if b["storeys"] < 2 else "balcony", u, u["w"] / 2, 190.0)
            _tube_ok = u["s"] == 0 and u["w"] >= LF_TUBE_W and (u["kind"] in _plain_tile or (u["kind"] == "SM_Wall_Windows_01" and u["label"] not in _has_awn))
            if u["s"] == 0 and u["kind"] not in _plain_tile and u["kind"] != "SM_WallDoor_01" and not _tube_ok:
                _lf_no("Tube", "tile " + u["kind"], u, u["w"] / 2, 20.0)
            if u["s"] == 0 and u["kind"] in _plain_tile and u["w"] < LF_TUBE_W:
                _lf_no("Tube", "narrow", u, u["w"] / 2, 20.0)
            if u["s"] == 0 and u["kind"] == "SM_WallDoor_01" and (u["label"] in _has_awn or {"Bulb_" + u["label"], "Tube_" + u["label"]} & _lf_labels):
                _lf_no("Bulb", "awning or lit", u, 111.0 * u["sx"], 30.0)
            # A tube on a plain ground-floor wall, or over a window with no awning (the awnings sit at +248, the window's head under
            # them), over head height.
            if _tube_ok:
                s_ = (u["w"] - 120.0) / 2
                z_ = u["z"] + 262.0
                why = "ground" if not _lf_open(u, s_ + 60.0, 120.0) else "pipe" if not _pipe_free(u, s_ - 10.0, s_ + 130.0) else \
                    "blocked" if not _lf_clear(_wbox(u, s_ - 10.0, s_ + 130.0, z_ - 20.0, z_ + 25.0, 35.0)) else None
                if why:
                    _lf_no("Tube", why, u, s_ + 60.0, 20.0)
                    continue
                x2, y2 = at(u["x"], u["y"], u["side"], s_ + 60.0, 20.0)
                out.append(("Tube", x2, y2, LF_REACH["Tube"], (u, s_, z_), _wbox(u, s_ - 10.0, s_ + 130.0, z_ - 20.0, z_ + 25.0, 35.0)))
            if u["s"] == 0 and u["kind"] == "SM_WallDoor_01" and u["label"] not in _has_awn and \
                    not ({"Bulb_" + u["label"], "Tube_" + u["label"]} & _lf_labels):          # a bulb over a door with no light yet
                s_ = 111.0 * u["sx"]
                top = u["z"] + 338.0
                why = "ground" if not _lf_open(u, s_, 45.0) else "pipe" if not _pipe_free(u, s_ - 10.0, s_ + 10.0) else \
                    "blocked" if not _lf_clear(_wbox(u, s_ - 12.0, s_ + 12.0, top - 115.0, top + 5.0, 30.0)) else None
                if why:
                    _lf_no("Bulb", why, u, s_, 30.0)
                    continue
                x_, y_ = at(u["x"], u["y"], u["side"], s_, 26.0 + _band_out(u))
                out.append(("Bulb", x_, y_, LF_REACH["Bulb"], (u, s_, top), _wbox(u, s_ - 12.0, s_ + 12.0, top - 115.0, top + 5.0, 30.0)))
        # A lamp on each power pole in the slum, its arm toward the side with the longest open run (the road), LF_POLE_Z up
        for p in items:
            if not (p["folder"] == DR_POLES and p["label"].startswith("Pole_") and "SM_Electric_Pole" in p["asset"]):
                continue
            X0, Y0, zg = p["loc"][0], p["loc"][1], p["loc"][2] + 2.0
            if not LEVEL.dress_point(*_lay(X0, Y0)):
                continue
            best_d = None
            for d in ((1.0, 0.0), (-1.0, 0.0), (0.0, 1.0), (0.0, -1.0)):
                run = 0.0
                while run < 600.0 and _lf_open_at(X0 + d[0] * (run + 40.0), Y0 + d[1] * (run + 40.0)):
                    run += 25.0
                if best_d is None or run > best_d[1]:
                    best_d = (d, run)
            d, run = best_d
            k = 0.67
            reach = 299.0 * k
            if run < reach + 80.0:
                continue
            z_ = zg + LF_POLE_Z
            hx, hy = X0 + d[0] * (LF_POLE_R + 280.0 * k), Y0 + d[1] * (LF_POLE_R + 280.0 * k)
            if any(math.hypot(hx - o[0], hy - o[1]) < LF_LAMP_GAP and _lf_sees((hx, hy), o) for o in lamps_xy):
                continue
            a0, a1 = 30.0, LF_POLE_R + reach + 20.0                 # the arm, past the pole's own box
            xs_ = (X0 + d[0] * a0 - abs(d[1]) * 18.0, X0 + d[0] * a1 + abs(d[1]) * 18.0)
            ys_ = (Y0 + d[1] * a0 - abs(d[0]) * 18.0, Y0 + d[1] * a1 + abs(d[0]) * 18.0)
            arm = (min(xs_), min(ys_), z_ - 45.0, max(xs_), max(ys_), z_ + 85.0)
            if not _lf_clear(arm):
                continue
            out.append(("PoleLamp", hx, hy, LF_REACH["Lamp"], ({"label": p["label"]}, X0 + d[0] * LF_POLE_R, Y0 + d[1] * LF_POLE_R, d, k, z_), arm))
        return out

    # The candidates once; after each placement those its fitting now blocks drop out (and lamps too near the new one).
    _lf_labels = {p["label"] for p in items}
    _lf_dark0 = _lf_dark()
    _lf_cands = _lf_candidates()
    _lf_n["candidates"] = len(_lf_cands)

    def _lf_meet(a, b, pad=3.0):
        return a[0] - pad < b[3] and b[0] < a[3] + pad and a[1] - pad < b[4] and b[1] < a[4] + pad and a[2] - pad < b[5] and b[2] < a[5] + pad

    _lf_pools = [_lf_pool(c_[1], c_[2], c_[3]) for c_ in _lf_cands]
    _lf_new = []
    for _round in range(LF_MAX):
        best = None
        for cand, pool in zip(_lf_cands, _lf_pools):
            gain = len(pool - _lf_lit)
            rank = gain * (LF_POLE_BONUS if cand[0] == "PoleLamp" else 1.0)
            if gain >= LF_MIN_GAIN and (best is None or rank > best[0]):
                best = (rank, cand, pool)
        if best is None:
            break
        kind_, cx, cy, reach, args, cbox = best[1]
        _lf_lit |= best[2]
        u = args[0]
        n_k = _lf_n["lamps"] + _lf_n["pole lamps"] + _lf_n["tubes"] + _lf_n["bulbs"]
        tag = "%s_F%d" % (u["label"], n_k)
        _lf_n0 = len(items)
        if kind_ == "Lamp":
            u_, s_, k, z_ = args
            x_, y_ = at(u["x"], u["y"], u["side"], s_, 1.0)
            put("Lamp_" + tag, FV + "SM_StreetLamp_02", x_, y_, z_, YAW[u["side"]] - 90.0, (k, k, k), folder=DR_LIGHTS, nocoll=True)
            _cheap(CULL_FAR)
            _light("Light_Lamp_" + tag, "SpotLight", cx, cy, z_ + 20.0 * k, 40.0, 1200.0, COL_LAMP, src=8.0, pitch=-90.0, outer=66.0)
            box = _wbox(u, s_ - 18.0, s_ + 18.0, z_ - 45.0, z_ + 85.0, 299.0 * k + 20.0)
        elif kind_ == "PoleLamp":
            u_, bx, by, d, k, z_ = args
            put("Lamp_" + tag, FV + "SM_StreetLamp_02", bx, by, z_, math.degrees(math.atan2(-d[1], -d[0])), (k, k, k), folder=DR_LIGHTS, nocoll=True)
            _cheap(CULL_FAR)
            _light("Light_Lamp_" + tag, "SpotLight", cx, cy, z_ + 20.0 * k, 40.0, 1200.0, COL_LAMP, src=8.0, pitch=-90.0, outer=66.0)
            box = cbox
        elif kind_ == "Tube":
            u_, s_, z_ = args
            _tube(dict(u, label=tag), s_, z_)
            box = _wbox(u, s_ - 10.0, s_ + 130.0, z_ - 20.0, z_ + 25.0, 35.0)
        else:
            u_, s_, top = args
            k = 0.7
            x_, y_ = cx, cy
            put("Bulb_" + tag, AS + "SM_Light_A_002", x_, y_, top, _lf_rng.uniform(0.0, 360.0), (k, k, k), folder=DR_LIGHTS, nocoll=True, mats=[LIGHT_ON])
            _cheap(CULL_MID, 1, True)
            n_ = 26.0 + _band_out(u)
            x0, y0 = at(u["x"], u["y"], u["side"], s_, -1.0)
            x1, y1 = at(u["x"], u["y"], u["side"], s_, n_ + 1.0)
            _rod("Bulb_%s_Arm" % tag, (x0, y0, top + 1.0), (x1, y1, top + 1.0), 2.2, RUST_MAT, DR_LIGHTS, CULL_MID)
            _light("Light_Bulb_" + tag, "PointLight", x_, y_, top - 124.0 * k, 4.5, 460.0, COL_BULB, src=3.0)
            box = _wbox(u, s_ - 12.0, s_ + 12.0, top - 115.0, top + 5.0, 30.0)
        _lf_new += [p["label"] for p in items[_lf_n0:]]
        _lf_boxes.append(box)
        _claim(box)
        _lf_lights.append((cx, cy, reach))
        _keep = [i for i, c_ in enumerate(_lf_cands) if c_[4][0]["label"] != u["label"] and not _lf_meet(c_[5], box) and
                 not (kind_ in ("Lamp", "PoleLamp") and c_[0] in ("Lamp", "PoleLamp") and math.hypot(c_[1] - cx, c_[2] - cy) < LF_LAMP_GAP and
                      _lf_sees((cx, cy), c_[1:3]))]
        _lf_cands, _lf_pools = [_lf_cands[i] for i in _keep], [_lf_pools[i] for i in _keep]
        _lf_n[{"Lamp": "lamps", "PoleLamp": "pole lamps", "Tube": "tubes", "Bulb": "bulbs"}[kind_]] += 1
    _lf_n["open ground lit"] = "%.0f%%" % (100.0 * (1.0 - len(_lf_dark()) / max(1, len(_lf_cells))))
    _lf_n["cells"] = len(_lf_cells)
    # The report (Saved/<level>/light_fill.json, not <prefix>*: write_plan clears those): what it placed, and where a fitting was turned down.
    json.dump({"placed": _lf_new,
               "turned down": _lf_why_at}, open(OUT + "light_fill.json", "w"), indent=0)
    print("light fill:", _lf_n, "; turned down (would light dark ground):", sorted(_lf_why.items(), key=lambda kv: -kv[1]))
