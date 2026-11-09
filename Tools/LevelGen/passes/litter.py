# Pass `litter`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Litter.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# Litter. Loose props, no collision: nothing here should stop a pawn or change the fights, and the nav mesh stays as it is. Rubbish lies where it's kept off the path: bags and rubble against walls,
# away from doors; paper and cups wherever; butts by the doors, where people stand. Culled near, as there's a lot of it and it's small.
GROUND_LITTER = True
DR_LITTER = "BackAlleys/Litter"
LITTER_RNG = random.Random(293)
LT_ME = ME + "MiddleEast/"
LT_BAGS = (LT_ME + "SM_Garbage_bag_02", LT_ME + "SM_Garbage_bag_02", LT_ME + "SM_Garbage_bag_02", LT_ME + "SM_Garbage_bag_01", LT_ME + "SM_Garbage_bag_green_03")
# The bags are physical (user 2026-11-07: "do the trash back with physcics as well"), set like the light props: Movable, asleep until hit, out of the nav mesh, no overlap events. The pack's bags
# are complex-as-simple, which can't simulate, so the level uses project copies set to their own convex hull (CTF_UseDefault). The pack's meshes are left as they are.
BA_DIR = "/Game/ThirdPerson/BackAlleys/"
# Caps on every physical piece, the bags here and the props below (user 2026-11-07: "the chairs go flying when you walk to them. cap their velocity"): how fast a piece is pushed out of
# something it overlaps, in cm/s, and how fast it may spin, in deg/s. A body has no setting for its straight-line speed: walking pushes come from the player's movement settings, in C++.
PHYS_CAP = (150.0, 720.0)
LT_BAG_PHYS = {LT_ME + "SM_Garbage_bag_01": BA_DIR + "SM_BackAlleys_GarbageBag_01", LT_ME + "SM_Garbage_bag_02": BA_DIR + "SM_BackAlleys_GarbageBag_02",
               LT_ME + "SM_Garbage_bag_green_03": BA_DIR + "SM_BackAlleys_GarbageBag_Green_03"}
LT_BAG_KG = {LT_ME + "SM_Garbage_bag_01": 4.0, LT_ME + "SM_Garbage_bag_02": 3.0, LT_ME + "SM_Garbage_bag_green_03": 4.0}      # a full bag of household rubbish at scale 1, times the cube of the scale
LT_BAG_HALF = {LT_ME + "SM_Garbage_bag_01": (40.5, 30.2), LT_ME + "SM_Garbage_bag_02": (47.3, 37.5), LT_ME + "SM_Garbage_bag_green_03": (40.5, 30.2)}    # half length and width, measured bounds
LT_RUBBLE = tuple(AS + "SM_Debris_A_00%d" % k_ for k_ in (1, 2, 3))
LT_SACKS = tuple(PM + "RiceBags_01/SM_Rice_Bag_" + k_ for k_ in ("Flat_01", "Flat_02", "Flat_03", "Flat_04", "HalfFull_01"))
LT_CARD = tuple(PM + "CardboardSet_01/SM_Cardboard_Flat_0%d" % k_ for k_ in (1, 2, 3, 4, 5))
_litter_n = {}


def _litter(label, asset, x_, y_, yaw_, kind, k_=1.0, flat=False, dz=0.0, z=None, kg=None):
    """z: the ground under the piece, when it's been measured under its whole footprint. kg: a physical piece of that mass (the bags)."""
    if kind == "sack":      # user 2026-11-06: "move the ricebags to the secured balconies", in the props pass. These still draw their randoms, so no other litter moves
        return
    z_ = (_ground_top(x_, y_) if z is None else z) + 0.1 + dz
    if kg:
        # The light props' settings (see _prop). Cloth, not Plastic: a bag of rubbish takes a shot like something soft, not like a monobloc chair.
        put(label, asset, x_, y_, z_, yaw_, (k_, k_, k_), folder=DR_LITTER)
        items[-1].update({"coll": "PhysicsActor", "phys": PHYS + "Cloth", "nonav": True, "physics": kg, "cap": list(PHYS_CAP)})
    else:
        put(label, asset, x_, y_, z_, yaw_, (k_, k_, k_), folder=DR_LITTER, nocoll=True)
    _cheap(CULL_NEAR, noshadow=flat)
    _litter_n[kind] = _litter_n.get(kind, 0) + 1


if GROUND_LITTER:
    _lt_spots = []
    for u in sorted(_wall_tiles, key=lambda t_: t_["label"]):
        if u["s"] != 0 or u["kind"] not in _plain_tile + ("SM_Wall_Windows_01", "SM_WallDoor_01"):
            continue
        in0, in1 = _inside_face(u, 0.0, u["w"])
        spans_ = [(in0, min(in1, 10.0 * u["sx"])), (max(in0, 215.0 * u["sx"]), in1)] if u["kind"] == "SM_WallDoor_01" else [(in0, in1)]
        for lo_, hi_ in spans_:
            if hi_ - lo_ >= 90.0:
                _lt_spots.append({"u": u, "lo": lo_, "hi": hi_, "x": at(u["x"], u["y"], u["side"], (lo_ + hi_) / 2, 50.0)[0], "y": at(u["x"], u["y"], u["side"], (lo_ + hi_) / 2, 50.0)[1]})
    LITTER_RNG.shuffle(_lt_spots)
    _lt_done = []

    def _lt_take(gap):
        """A clear stretch at the foot of a wall, well away from the other lots."""
        for c_ in _lt_spots:
            if any(math.hypot(c_["x"] - o_[0], c_["y"] - o_[1]) < gap for o_ in _lt_done):
                continue
            u = c_["u"]
            a_, b_ = at(u["x"], u["y"], u["side"], c_["lo"], 8.0), at(u["x"], u["y"], u["side"], c_["hi"], 90.0)
            box_ = (min(a_[0], b_[0]), min(a_[1], b_[1]), 0.0, max(a_[0], b_[0]), max(a_[1], b_[1]), 80.0)
            if not _ground_open(u, (c_["lo"] + c_["hi"]) / 2, 110.0) or not _free(box_, 1.0) or not _pipe_free(u, c_["lo"], c_["hi"]) or not _stair_clear(u, c_["lo"], c_["hi"], 0.0):
                continue
            _lt_done.append((c_["x"], c_["y"]))
            return c_
        return None

    for k_ in range(11):
        c_ = _lt_take(620.0)
        if c_ is None:
            break
        u = c_["u"]
        n_bags = LITTER_RNG.choice((1, 2, 2, 3, 3, 4))
        s_ = LITTER_RNG.uniform(c_["lo"] + 42.0, max(c_["lo"] + 43.0, c_["hi"] - 42.0))
        rx_, ry_ = RUN[u["side"]]
        bags_ = []
        for j_ in range(n_bags):
            # The same draws in the same order as before the bags were physical, so the rest of the litter stays where it was.
            d_, n_ = LITTER_RNG.uniform(52.0, 74.0), LITTER_RNG.uniform(46.0, 74.0)
            asset_, yaw_, k_bag = LITTER_RNG.choice(LT_BAGS), LITTER_RNG.uniform(0.0, 360.0), LITTER_RNG.uniform(0.8, 1.05)
            # Physical, so nothing may start inside anything ("make sure whatevr is a physical object does not overlap initially to any other object"). They used to lie 39-55 cm
            # apart, and a bag is 60-95 wide. Now each takes what it needs along the wall and out from it, turned as it lies, 1-4 cm from the next, clear of the lining.
            hx_, hy_ = LT_BAG_HALF[asset_]
            cy_, sy_ = math.cos(math.radians(yaw_)), math.sin(math.radians(yaw_))
            ct_, st_ = abs(cy_ * rx_ + sy_ * ry_), abs(cy_ * ry_ - sy_ * rx_)
            bags_.append((j_, asset_, yaw_, k_bag, (ct_ * hx_ + st_ * hy_) * k_bag, (st_ * hx_ + ct_ * hy_) * k_bag, 1.0 + (d_ - 52.0) * 0.14, n_))
        # One row across the clear stretch, around where the pile used to start; a bag that won't fit isn't put down. The props pass then tests them against everything else.
        row_, used_ = [], 0.0
        for b_ in bags_:
            need_ = 2.0 * b_[4] + (b_[6] if row_ else 0.0)
            if used_ + need_ > c_["hi"] - c_["lo"]:
                _litter_n["bag off its stretch"] = _litter_n.get("bag off its stretch", 0) + 1
                continue
            row_.append(b_)
            used_ += need_
        pos_ = min(max(s_ - used_ / 2.0, c_["lo"]), c_["hi"] - used_)
        for i_, (j_, asset_, yaw_, k_bag, along_, out_, gap_, n_) in enumerate(row_):
            mid_ = pos_ + (gap_ if i_ else 0.0) + along_
            pos_ = mid_ + along_
            off_ = FLOOR_OUT + 1.5 + out_ + (n_ - 46.0) * 0.25
            x_, y_ = at(u["x"], u["y"], u["side"], mid_, off_)
            z_ = max(_ground_top(*at(u["x"], u["y"], u["side"], mid_ + a_ * along_, off_ + b_ * out_)) for a_ in (-1, 0, 1) for b_ in (-1, 0, 1))
            _litter("Lt_Bag_%d_%d" % (k_, j_), LT_BAG_PHYS[asset_], x_, y_, yaw_, "bag", k_bag, z=z_, kg=round(LT_BAG_KG[asset_] * k_bag ** 3, 1))
        if LITTER_RNG.random() < 0.6:
            x_, y_ = at(u["x"], u["y"], u["side"], s_ + LITTER_RNG.uniform(-100.0, 100.0), LITTER_RNG.uniform(60.0, 120.0))
            _litter("Lt_BagCard_%d" % k_, LITTER_RNG.choice(LT_CARD), x_, y_, LITTER_RNG.uniform(0.0, 360.0), "card", 1.0, True)
    for k_ in range(7):
        c_ = _lt_take(700.0)
        if c_ is None:
            break
        u = c_["u"]
        x_, y_ = at(u["x"], u["y"], u["side"], (c_["lo"] + c_["hi"]) / 2 + LITTER_RNG.uniform(-14.0, 14.0), 78.0)
        _litter("Lt_Rubble_%d" % k_, LITTER_RNG.choice(LT_RUBBLE), x_, y_, LITTER_RNG.uniform(0.0, 360.0), "rubble", LITTER_RNG.uniform(0.62, 0.86))
    for k_ in range(7):
        c_ = _lt_take(620.0)
        if c_ is None:
            break
        u = c_["u"]
        s_ = LITTER_RNG.uniform(c_["lo"] + 30.0, max(c_["lo"] + 31.0, c_["hi"] - 30.0))
        stack = LITTER_RNG.choice((1, 2, 2, 3))
        for j_ in range(stack):
            x_, y_ = at(u["x"], u["y"], u["side"], s_ + LITTER_RNG.uniform(-7.0, 7.0), 52.0 + LITTER_RNG.uniform(-7.0, 7.0))
            _litter("Lt_Sack_%d_%d" % (k_, j_), LITTER_RNG.choice(LT_SACKS[:4]), x_, y_, YAW[u["side"]] + LITTER_RNG.uniform(-16.0, 16.0), "sack", 1.0, False, j_ * 15.0)

    def _lt_open(margin):
        for _t in range(40):
            r_ = LITTER_RNG.choices(_gd_rects, _gd_weights)[0]
            if min(r_[2] - r_[0], r_[3] - r_[1]) < 2.0 * margin + 0.1:
                continue
            # Mostly toward the edges of a lane, where the walking doesn't sweep it.
            def side_(a_, b_):
                t_ = LITTER_RNG.random() ** 2.0 * 0.5
                return a_ + margin + (b_ - a_ - 2.0 * margin) * (t_ if LITTER_RNG.random() < 0.5 else 1.0 - t_)
            lx, ly = side_(r_[0], r_[2]), side_(r_[1], r_[3])
            x_, y_ = ue(lx, ly)
            if not solid(lx, ly, 0) and _free((x_ - 12.0, y_ - 12.0, 0.0, x_ + 12.0, y_ + 12.0, 20.0), 1.0):
                return x_, y_
        return None

    for kind, count, assets, lo_, hi_ in (("card", 12, LT_CARD, 0.85, 1.1), ("paper", 14, (LT_ME + "SM_Paper",), 0.7, 1.0), ("cup", 16, (LT_ME + "SM_crumpled_cup", LT_ME + "SM_crumpled_cup", LT_ME + "SM_cup"), 1.0, 1.15)):
        for k_ in range(count):
            at_ = _lt_open(0.2)
            if at_:
                _litter("Lt_%s_%d" % (kind, k_), LITTER_RNG.choice(assets), at_[0], at_[1], LITTER_RNG.uniform(0.0, 360.0), kind, LITTER_RNG.uniform(lo_, hi_), True)
    _lt_doors = [u for u in _wall_tiles if u["s"] == 0 and u["kind"] == "SM_WallDoor_01"]
    LITTER_RNG.shuffle(_lt_doors)
    for k_, u in enumerate(_lt_doors[:12]):
        mid = 112.5 * u["sx"]
        if not _ground_open(u, mid, 120.0):
            continue
        for j_ in range(LITTER_RNG.choice((2, 3, 3, 4, 6))):
            x_, y_ = at(u["x"], u["y"], u["side"], mid + LITTER_RNG.uniform(-140.0, 140.0), LITTER_RNG.uniform(34.0, 150.0))
            _litter("Lt_Butt_%d_%d" % (k_, j_), LT_ME + LITTER_RNG.choice(("SM_cigarette_butt_01", "SM_cigarette_butt_02")), x_, y_, LITTER_RNG.uniform(0.0, 360.0), "butt", 1.15, True)
    print("litter:", dict(sorted(_litter_n.items())), sum(_litter_n.values()))

