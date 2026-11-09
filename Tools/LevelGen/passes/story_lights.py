# Pass `story_lights` (story levels). Night on the street houses, 2026-11-08 (the layout: "Night, people still out"): cobra
# lamps on wall arms at the second storey over the streets and yards, bare bulbs over street doors. The fittings and Static
# lights as the arena's street pass makes them with its lights on (the arena keeps its off: daylight). The interior bulbs are
# story_interiors'. Brightness from the arena's (judged in daylight, unbaked), raised for night: look again after a bake.
# Needs: wall_tiles (walls pass), BLOCKS, cover_top, lay, put, _box.
SL = "BackAlleys/Lights"
SL_RNG = random.Random(419)
LAMP_GAP_N, BULB_GAP_N = 1100.0, 650.0
LAMPS_N, BULBS_N = 18, 30
COL_LAMP_N, COL_BULB_N = [1.0, 0.62, 0.3], [1.0, 0.72, 0.44]
LIGHT_ON_N = "/Game/AsiaSlum/Material/MI_Light_A_001"
_sl = {"lamps": 0, "bulbs": 0}


def _open_at(t, s_, n_, z_abs):
    """The point n_ cm out from tile t, s_ along it, is open ground below z_abs (nothing built there that tall)."""
    x_, y_ = at(t["x"], t["y"], t["side"], s_, n_)
    lx, ly = lay(x_, y_)
    return not outside(lx, ly) and cover_top(lx, ly) < z_abs - 30.0 and not any(
        e["x0"] < lx < e["x1"] and e["y0"] < ly < e["y1"] for e in EXTRA_SOLID)


def _sl_light(label, kind, x_, y_, z_, intensity, radius, colour, src=4.0, pitch=0.0, outer=60.0):
    put(label, "/Script/Engine.%s" % kind, x_, y_, z_, 0.0, (1, 1, 1), folder=SL)
    items[-1]["rot"][0] = pitch
    items[-1]["light"] = {"kind": kind, "intensity": intensity, "radius": radius, "colour": colour, "source": src, "outer": outer, "length": 0.0}
    if kind == "SpotLight":         # the fill under every spot light (street.py FILL_*, user 2026-11-09)
        put(label + "_Fill", "/Script/Engine.PointLight", x_, y_, z_ - 25.0, 0.0, (1, 1, 1), folder=SL)
        items[-1]["light"] = {"kind": "PointLight", "intensity": intensity * 0.12, "radius": radius * 0.5, "colour": colour, "source": 40.0,
                              "outer": 0.0, "length": 0.0, "fill": True}


# Hollow-block faces take nothing but posters and graffiti (user 2026-11-06), so no fittings there.
_hollow_tile = {p["label"] for p in items if p["folder"] == BLK and p.get("mats") and p["mats"][0] == HOLLOW}
_tiles = sorted((t for t in wall_tiles if t["label"] not in _hollow_tile), key=lambda t: t["label"])
SL_RNG.shuffle(_tiles)
_lamp_at, _bulb_at = [], []
for t in _tiles:                                   # lamps: second storey, plain tiles, a street or yard below
    if _sl["lamps"] >= LAMPS_N or t["s"] != 1 or t["kind"] != "plain" or t["w"] < 150.0 or BLOCKS[t["label"].split("_")[0]].get("balcony") or             BLOCKS[t["label"].split("_")[0]].get("plain"):             # street lamps are the slum's, not the compound's
        continue
    k = SL_RNG.uniform(0.62, 0.72)
    s_ = t["w"] / 2
    z_ = t["z"] + SL_RNG.uniform(175.0, 205.0)
    x_, y_ = at(t["x"], t["y"], t["side"], s_, 1.0)
    if any(math.hypot(x_ - o[0], y_ - o[1]) < LAMP_GAP_N for o in _lamp_at):
        continue
    if not all(_open_at(t, s_, n_, z_) for n_ in (60.0, 150.0, 220.0, 320.0)):
        continue
    put("Lamp_" + t["label"], FV + "SM_StreetLamp_02", x_, y_, z_, YAW[t["side"]] - 90.0, (k, k, k), folder=SL, nocoll=True)
    hx, hy = at(t["x"], t["y"], t["side"], s_, 280.0 * k)
    _sl_light("Light_Lamp_" + t["label"], "SpotLight", hx, hy, z_ + 20.0 * k, 60.0, 1400.0, COL_LAMP_N, src=8.0, pitch=-90.0, outer=66.0)
    _lamp_at.append((x_, y_))
    _sl["lamps"] += 1
for t in _tiles:                                   # bulbs over street doors
    if _sl["bulbs"] >= BULBS_N or t["s"] != 0 or t["kind"] != "door" or BLOCKS[t["label"].split("_")[0]].get("plain"):     # the slum's doors
        continue
    s_ = 111.0 * t["w"] / 225.0 + SL_RNG.choice((0.0, -72.0, 72.0))
    top = t["z"] + 338.0
    x_, y_ = at(t["x"], t["y"], t["side"], s_, 26.0)
    if any(math.hypot(x_ - o[0], y_ - o[1]) < BULB_GAP_N for o in _bulb_at) or not _open_at(t, s_, 80.0, top):
        continue
    k = 0.7
    put("Bulb_" + t["label"], AS + "SM_Light_A_002", x_, y_, top, SL_RNG.uniform(0.0, 360.0), (k, k, k), folder=SL, nocoll=True, mats=[LIGHT_ON_N])
    x0_, y0_ = at(t["x"], t["y"], t["side"], s_, -1.0)
    X0, X1 = sorted((x0_, x_))
    Y0, Y1 = sorted((y0_, y_))
    put("Bulb_%s_Arm" % t["label"], CUBE, X0 - 1.1, Y0 - 1.1, top - 1.1, 0, ((X1 - X0 + 2.2) / 100.0, (Y1 - Y0 + 2.2) / 100.0, 0.022),
        folder=SL, nocoll=True, mats=[BM + "MI_BackAlleys_MetalSheet_Rust"])
    _sl_light("Light_Bulb_" + t["label"], "PointLight", x_, y_, top - 124.0 * k, 8.0, 520.0, COL_BULB_N, src=3.0)
    _bulb_at.append((x_, y_))
    _sl["bulbs"] += 1
print("story lights:", _sl)
