# Pass `dirt`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Ground dirt decals.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# Dirt, as decals over the pours and the road. Grit along the feet of walls, where the sweeping stops and rain leaves it; run-off from downpipes and air conditioners; dark grime in front of doors; heaps and specks; a few
# manholes, drain plates and steel plates. A decal lying on the ground looks straight down: pitch -90, with its U along local Z, which is the yaw's direction, and V along local Y. Shallow, so it can't paint up a wall.
GROUND_DIRT = True
DR_GROUND_DIRT = "BackAlleys/GroundDirt"
DIRT_RNG = random.Random(283)
GD_Y = "/Game/Megapack/Material/Yakohama/Decals/"
GD_F = "/Game/Megapack/Material/Favela/Decals/"
# Dirt along the feet of walls. User 2026-11-06: "Your decal alignment for the Dirt decals to the edge of the houses are bad at the moment. They either go above to the floor lining OR they
# do not hit the edge at all". So a strip's dense edge lies just under the lining's edge, from the slabs themselves: GD_EDGE is how far down its image that edge is, measured from the masks row by row
# (my first guesses were out by 5 cm and more). A strip only runs where there's lining behind it, never past the end of a wall. Their material fades both ends: the masks run the image's full width.
GD_SOFT, GD_GRIT1, GD_GRIT2 = BM + "MI_BackAlleys_Grime_Soft", BM + "MI_BackAlleys_Grime_Grit01", BM + "MI_BackAlleys_Grime_Grit02"
GD_STRIPS = (GD_GRIT1, GD_GRIT2)
GD_EDGE = {GD_SOFT: 0.985, GD_GRIT1: 0.775, GD_GRIT2: 0.69}
GD_TUCK = 1.5       # cm under the lining
GD_LEAKS = (BM + "MI_BackAlleys_Grime_Leak01", BM + "MI_BackAlleys_Grime_Leak02")
GD_HEAPS = (GD_F + "MI_DecalRoadDirt_04", GD_F + "MI_DecalRoadDirt_05")
GD_SPECKS = (GD_F + "MI_DecalRoadDirt_02", GD_Y + "MI_DecalDirt_03")
GD_MANHOLE, GD_DRAIN, GD_PLATE = GD_Y + "MI_Decal_02", GD_Y + "MI_Decal_01", GD_Y + "MI_Decal_05"
# User 2026-11-06: "you can see where the decal goes into the house floor, the decal shoud be super thin and hit just about the surface of the road". Of the decal's 128 cm each way: from 0.6 under the road
# to 1.1 over it, which takes in the road and the pours (at most 0.8) and next to nothing of a lining.
GD_DEPTH, GD_Z = 0.85 / 128.0, 0.25
_dirt_n = {}


# A story level's ground has heights (story_ground_dress sets STORY_GROUND_TOP, 2026-11-09); the arena's is flat and has none, so its plan
# doesn't move.
_gt_hook = globals().get("STORY_GROUND_TOP")
_gb_hook = globals().get("STORY_GROUND_BASE")


def _ground_decal(label, asset, x_, y_, yaw_, u_cm, v_cm, kind):
    """u_cm along the yaw's direction, v_cm across it."""
    if asset in (GD_DRAIN, GD_PLATE):       # user 2026-11-06: "metal square grates are not common in the ph". They still draw their randoms, so nothing else moves.
        return
    put(label, asset, x_, y_, GD_Z + (_gb_hook(x_, y_) if _gb_hook else 0.0), yaw_, (GD_DEPTH, v_cm / 512.0, u_cm / 512.0), folder=DR_GROUND_DIRT, decal=True)
    items[-1]["rot"][0] = -90.0
    _dirt_n[kind] = _dirt_n.get(kind, 0) + 1


_floor_boxes = [(p["loc"][0], p["loc"][1], p["loc"][0] + p["scale"][0] * 100.0, p["loc"][1] + p["scale"][1] * 100.0) for p in items if p["folder"] == FLOORS]


def _on_floor(x_, y_):
    return any(b_[0] <= x_ <= b_[2] and b_[1] <= y_ <= b_[3] for b_ in _floor_boxes)


def _lining_span(t, s0, s1):
    """The longest stretch of s0..s1 along a wall with the lining's edge where it should be: slab just inside, open ground just outside."""
    best, cur, s_ = (s0, s0), None, s0
    while True:
        a_, b_ = at(t["x"], t["y"], t["side"], s_, FLOOR_OUT - 2.0), at(t["x"], t["y"], t["side"], s_, FLOOR_OUT + 2.0)
        if _on_floor(a_[0], a_[1]) and not _on_floor(b_[0], b_[1]):
            cur = s_ if cur is None else cur
            if s_ - cur > best[1] - best[0]:
                best = (cur, s_)
        else:
            cur = None
        if s_ >= s1:
            return best
        s_ = min(s_ + 8.0, s1)


def _lining_foot(x_, y_, side, reach=60):
    """Straight back from a point near a wall to the lining's edge: a point on the wall's plane to measure along, or None."""
    nx, ny = NORMAL[side]
    for k_ in range(reach, -reach - 1, -1):
        ax_, ay_ = x_ + nx * k_, y_ + ny * k_
        if _on_floor(ax_, ay_) and not _on_floor(ax_ + nx * 1.0, ay_ + ny * 1.0):
            return {"x": ax_ - nx * FLOOR_OUT, "y": ay_ - ny * FLOOR_OUT, "side": side}
    return None


def _ground_stain(label, asset, x_, y_, side, u_, v_, kind):
    """A stain spreading out from the foot of a wall. User 2026-11-06, of one by a downpipe near a corner: "1rst one overshoots the house". Its hard top edge lies under the lining, only where there is lining."""
    t_ = _lining_foot(x_, y_, side)
    if t_ is None:
        return False
    a_, e_ = _lining_span(t_, -u_ / 2, u_ / 2)
    if e_ - a_ < 60.0:
        return False
    cx_, cy_ = at(t_["x"], t_["y"], side, (a_ + e_) / 2, FLOOR_OUT - GD_TUCK + v_ / 2)
    _ground_decal(label, asset, cx_, cy_, YAW[side], e_ - a_, v_, kind)
    return True


def _ground_top(x_, y_):
    """How high the surface is under a point, to set something down on it."""
    if _gt_hook:
        return _gt_hook(x_, y_)
    lx, ly = _lay(x_, y_)
    for o_ in _ground_bays:
        if o_[0] < lx < o_[2] and o_[1] < ly < o_[3]:
            return o_[4]
    return 0.0


if GROUND_DIRT:
    _gd_runs = [k_ for k_ in sorted(_run_tiles) if _run_tiles[k_][0]["s"] == 0]
    DIRT_RNG.shuffle(_gd_runs)
    for name_ in _gd_runs:
        ts = _run_tiles[name_]
        t0 = ts[0]
        total = ts[-1]["off"] - t0["off"] + ts[-1]["w"]
        if total < 150.0 or DIRT_RNG.random() > 0.62:
            continue
        s_ = DIRT_RNG.uniform(0.0, min(160.0, total * 0.3))
        k_ = 0
        while s_ < total - 80.0:
            a_, e_ = _lining_span(t0, s_, min(s_ + DIRT_RNG.uniform(260.0, 480.0), total))
            u_ = e_ - a_
            if u_ < 120.0:
                s_ += 120.0
                continue
            s_ = a_
            mid = s_ + u_ / 2
            # V runs out from the wall at the run's yaw, so turned round it runs in to it: the dense edge lies against the wall.
            rx, ry = RUN[t0["side"]]
            yaw_ = math.degrees(math.atan2(ry, rx)) + 180.0
            if DIRT_RNG.random() < 0.62:
                asset, kind = GD_SOFT, "foot"
                v_ = DIRT_RNG.uniform(120.0, 210.0)
            else:
                asset, kind = DIRT_RNG.choice(GD_STRIPS), "grit"
                v_ = max(60.0, u_ / 4.0 * DIRT_RNG.uniform(0.9, 1.25))
            n_ = FLOOR_OUT - GD_TUCK + v_ * (GD_EDGE[asset] - 0.5)
            if _ground_open(t0, mid, FLOOR_OUT + 40.0) and _stair_clear(t0, s_, s_ + u_, 0.0):
                x_, y_ = at(t0["x"], t0["y"], t0["side"], mid, n_)
                _ground_decal("GD_Foot_%s_%d" % (name_, k_), asset, x_, y_, yaw_, u_, v_, kind)
                k_ += 1
            s_ += u_ + DIRT_RNG.uniform(60.0, 420.0)
    # Run-off where a downpipe comes down, and a drain plate beside some of them. A stain spreads out from the wall.
    _gd_pipes = {}
    for p in items:
        if p["folder"] == DR_PIPES and p["label"].startswith("Pipe_"):
            _gd_pipes.setdefault(p["label"].rsplit("_", 1)[0], p)
    _gd_drains = 0
    for key_ in sorted(_gd_pipes):
        p = _gd_pipes[key_]
        yaw_ = p["rot"][1]
        side_ = next(k_ for k_, v_ in YAW.items() if abs((v_ - yaw_) % 360.0) < 1.0)
        # A pipe's yaw is its wall's: at(), YAW. Its wall's run lies along the yaw, the street out to +Y of it.
        ca_, sa_ = math.cos(math.radians(yaw_)), math.sin(math.radians(yaw_))
        ox_, oy_ = -sa_, ca_
        lx, ly = _lay(p["loc"][0] + ox_ * 60.0, p["loc"][1] + oy_ * 60.0)
        if solid(lx, ly, 0):
            continue
        if DIRT_RNG.random() < 0.8:
            u_ = DIRT_RNG.uniform(110.0, 170.0)
            v_ = DIRT_RNG.uniform(150.0, 240.0)
            _ground_stain("GD_RunOff_%s" % key_, DIRT_RNG.choice(GD_LEAKS), p["loc"][0], p["loc"][1], side_, u_, v_, "runoff")
        if _gd_drains < 7 and DIRT_RNG.random() < 0.34:
            w_ = DIRT_RNG.uniform(48.0, 58.0)
            _ground_decal("GD_Drain_%s" % key_, GD_DRAIN, p["loc"][0] + ox_ * (w_ / 2 + 16.0) + ca_ * 8.0, p["loc"][1] + oy_ * (w_ / 2 + 16.0) + sa_ * 8.0, yaw_, w_, w_, "drain")
            _gd_drains += 1
    # Drips from the air conditioners, smaller.
    _gd_acs = sorted({(p["label"].split("_Unit")[0], p["loc"][0], p["loc"][1], p["rot"][1]) for p in items if p["folder"] == DR_ACS and p["label"].startswith("AC_") and p["asset"].split("/")[-1].startswith("SM_Air_Conditioning")})
    DIRT_RNG.shuffle(_gd_acs)
    for label_, ax_, ay_, yaw_ in _gd_acs[:12]:
        lx, ly = _lay(ax_, ay_)
        if solid(lx, ly, 0):
            continue
        w_ = DIRT_RNG.uniform(70.0, 120.0)
        v_ = DIRT_RNG.uniform(70.0, 120.0)
        _ground_stain("GD_Drip_%s" % label_, GD_LEAKS[1], ax_, ay_, {"N": "north", "S": "south", "E": "east", "W": "west"}[label_.split("_")[2][0]], w_, v_, "drip")
    # Grime where people walk out of a door: dark, with its edge at the step.
    _gd_doors = [u for u in _wall_tiles if u["s"] == 0 and u["kind"] == "SM_WallDoor_01"]
    DIRT_RNG.shuffle(_gd_doors)
    for u in _gd_doors[:18]:
        mid = 112.5 * u["sx"] + DIRT_RNG.uniform(-12.0, 12.0)
        if not _ground_open(u, mid, 120.0):
            continue
        w_ = DIRT_RNG.uniform(240.0, 320.0)
        v_ = DIRT_RNG.uniform(190.0, 280.0)
        a_, e_ = _lining_span(u, mid - w_ / 2, mid + w_ / 2)
        if e_ - a_ < 140.0:
            continue
        x_, y_ = at(u["x"], u["y"], u["side"], (a_ + e_) / 2, FLOOR_OUT - GD_TUCK + v_ * (GD_EDGE[GD_SOFT] - 0.5))
        rx, ry = RUN[u["side"]]
        _ground_decal("GD_Door_%s" % u["label"], GD_SOFT, x_, y_, math.degrees(math.atan2(ry, rx)) + 180.0, e_ - a_, v_, "door")
    # Heaps by the walls, specks anywhere, a few covers out in the lanes.
    _gd_rects = [r_ for r_ in _ground_rects if min(r_[2] - r_[0], r_[3] - r_[1]) >= 1.5]
    _gd_weights = [(r_[2] - r_[0]) * (r_[3] - r_[1]) for r_ in _gd_rects]
    _gd_done = []

    def _gd_spot(margin, gap, tries=60):
        for _t in range(tries):
            r_ = DIRT_RNG.choices(_gd_rects, _gd_weights)[0]
            if min(r_[2] - r_[0], r_[3] - r_[1]) < 2.0 * margin + 0.1:
                continue
            lx, ly = DIRT_RNG.uniform(r_[0] + margin, r_[2] - margin), DIRT_RNG.uniform(r_[1] + margin, r_[3] - margin)
            x_, y_ = ue(lx, ly)
            if solid(lx, ly, 0) or any(math.hypot(x_ - o_[0], y_ - o_[1]) < gap for o_ in _gd_done):
                continue
            _gd_done.append((x_, y_))
            return x_, y_
        return None

    for k_ in range(5):
        at_ = _gd_spot(1.2, 800.0)
        if at_:
            w_ = DIRT_RNG.uniform(135.0, 165.0)
            _ground_decal("GD_Manhole_%d" % k_, GD_MANHOLE, at_[0], at_[1], DIRT_RNG.uniform(0.0, 360.0), w_, w_, "manhole")
    for k_ in range(3):
        at_ = _gd_spot(1.0, 600.0)
        if at_:
            w_ = DIRT_RNG.uniform(150.0, 190.0)
            _ground_decal("GD_Plate_%d" % k_, GD_PLATE, at_[0], at_[1], DIRT_RNG.choice((0.0, 90.0)) + DIRT_RNG.uniform(-5.0, 5.0), w_, w_, "plate")
    for k_ in range(26):
        at_ = _gd_spot(0.3, 300.0)
        if at_:
            w_ = DIRT_RNG.uniform(120.0, 240.0)
            asset = DIRT_RNG.choice(GD_HEAPS)
            if asset == GD_HEAPS[1]:        # the rubble one: at full size it reads as a flat golden sticker in the sun
                w_ *= 0.6
            _ground_decal("GD_Heap_%d" % k_, asset, at_[0], at_[1], DIRT_RNG.uniform(0.0, 360.0), w_, w_, "heap")
    for k_ in range(30):
        at_ = _gd_spot(0.5, 240.0)
        if at_:
            w_ = DIRT_RNG.uniform(170.0, 320.0)
            _ground_decal("GD_Speck_%d" % k_, DIRT_RNG.choice(GD_SPECKS), at_[0], at_[1], DIRT_RNG.uniform(0.0, 360.0), w_, w_, "speck")
    print("ground dirt:", dict(sorted(_dirt_n.items())), sum(_dirt_n.values()))

