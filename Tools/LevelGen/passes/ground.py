# Pass `ground`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Ground surfaces: poured bays and repairs.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# --- The ground. User 2026-11-06: "Next step is ground dirt, variations and dressings". Surfaces first, then dirt, then litter, each with its own random sequence. ----------------------------------
# The ground actor's cracked asphalt stays as the old road. Over it, poured concrete: the open ground is cut into stretches, the narrow ones nearly always poured, the wide ones about half; a poured stretch
# is cut into bays, each its own pour, with a joint between them where the dark road shows. Wide stretches get two or three strips whose joints don't line up. On the bare stretches, utility cuts and
# repairs. Planes, from world-mapped materials: no thickness, and a lightmap of their own, so a sun shadow crosses them properly after a bake. They stop shots and report their surface, and a pawn walks
# through them on the slab below (IgnoreOnlyPawn), so the nav mesh doesn't change.
GROUND_SURFACES = True
DR_GROUND = "BackAlleys/Ground"
GROUND_RNG = random.Random(281)
GROUND_JOINT = 2.5
GM = BM + "MI_BackAlleys_Ground_"
_ground_n = {"stretches": 0, "poured": 0, "bays": 0, "patches": 0}
_ground_rects, _ground_bare, _ground_bays = [], [], []


def _ground_plane(label, x0, y0, x1, y1, kind, z):
    """A flat rectangle in layout metres. Plane's 100 cm across and centred."""
    a_, b_ = ue(x0, y0), ue(x1, y1)
    cx_, cy_ = (a_[0] + b_[0]) / 2, (a_[1] + b_[1]) / 2
    put(label, PLANE, cx_, cy_, z, 0.0, (abs(a_[0] - b_[0]) / 100.0, abs(a_[1] - b_[1]) / 100.0, 1.0), folder=DR_GROUND, mats=[GM + kind])
    items[-1]["coll"] = "IgnoreOnlyPawn"
    items[-1]["phys"] = PHYS + ("Asphalt" if kind == "AsphaltPatch" else "Concrete")
    items[-1]["nonav"] = True
    items[-1]["noshadow"] = True        # flat on the road, it has nothing to shadow but a hard black line along one edge


if GROUND_SURFACES:
    _gx = sorted({0.0, float(W)} | {b_["x0"] for b_ in BLOCKS.values()} | {b_["x1"] for b_ in BLOCKS.values()})
    _gy = sorted({0.0, float(H)} | {b_["y0"] for b_ in BLOCKS.values()} | {b_["y1"] for b_ in BLOCKS.values()})
    _gx = [v_ for v_ in _gx if 0.0 <= v_ <= W]
    _gy = [v_ for v_ in _gy if 0.0 <= v_ <= H]
    _gopen = [[not solid((_gx[i_] + _gx[i_ + 1]) / 2, (_gy[j_] + _gy[j_ + 1]) / 2, 0) for j_ in range(len(_gy) - 1)] for i_ in range(len(_gx) - 1)]
    while True:     # the largest open rectangle left, again and again
        best_, best_a = None, 0.0
        for i0 in range(len(_gx) - 1):
            for j0 in range(len(_gy) - 1):
                if not _gopen[i0][j0]:
                    continue
                j_end = len(_gy) - 1
                for i1 in range(i0, len(_gx) - 1):
                    j1 = j0
                    while j1 < j_end and _gopen[i1][j1]:
                        j1 += 1
                    j_end = j1
                    if j_end == j0:
                        break
                    w_, h_ = _gx[i1 + 1] - _gx[i0], _gy[j_end] - _gy[j0]
                    # Long lanes rather than big squares.
                    a_ = w_ * h_ * (1.0 + 0.04 * max(w_, h_) / max(min(w_, h_), 0.5))
                    if a_ > best_a:
                        best_, best_a = (i0, j0, i1, j_end), a_
        if best_ is None:
            break
        i0, j0, i1, j_end = best_
        for i_ in range(i0, i1 + 1):
            for j_ in range(j0, j_end):
                _gopen[i_][j_] = False
        _ground_rects.append((_gx[i0], _gy[j0], _gx[i1 + 1], _gy[j_end]))
    _ground_rects.sort()
    _draw_tone = shuffle_bag(GROUND_RNG, ("ConcreteA", "ConcreteA", "ConcreteB", "ConcreteOld", "ConcreteA", "ConcreteB"))
    for r_i, (x0, y0, x1, y1) in enumerate(_ground_rects):
        # A long stretch doesn't stay one thing all the way down.
        along_x = x1 - x0 >= y1 - y0
        length, width = (x1 - x0, y1 - y0) if along_x else (y1 - y0, x1 - x0)
        pieces, at_ = [], 0.0
        while length - at_ > 15.0:
            step_ = GROUND_RNG.uniform(9.0, 14.0)
            pieces.append((at_, at_ + step_))
            at_ += step_
        pieces.append((at_, length))
        for p_i, (a_, e_) in enumerate(pieces):
            rx0, ry0, rx1, ry1 = (x0 + a_, y0, x0 + e_, y1) if along_x else (x0, y0 + a_, x1, y0 + e_)
            _ground_n["stretches"] += 1
            p_poured = 0.92 if width < 3.2 else 0.72 if width < 5.0 else 0.5
            if GROUND_RNG.random() >= p_poured or width < 0.6 or e_ - a_ < 0.6:
                _ground_bare.append((rx0, ry0, rx1, ry1, along_x))
                continue
            _ground_n["poured"] += 1
            main = _draw_tone()
            n_strips = max(1, int(math.ceil(width / 4.3)))
            # A little off the even split. It was k + 0.82..1.18, a slip for k * that, so a cut could fall past the edge of the lane and a bay ran over the next: user 2026-11-06, "theres a shimering overlap".
            cuts_w = [0.0] + sorted(width * (k_ + GROUND_RNG.uniform(-0.18, 0.18)) / n_strips for k_ in range(1, n_strips)) + [width]
            for k_ in range(n_strips):
                at_l, bay = 0.0, []
                run_l = e_ - a_
                while run_l - at_l > 4.3:
                    step_ = GROUND_RNG.uniform(2.1, 4.2)
                    bay.append((at_l, at_l + step_))
                    at_l += step_
                bay.append((at_l, run_l))
                for b_i, (l0, l1) in enumerate(bay):
                    w0, w1 = cuts_w[k_], cuts_w[k_ + 1]
                    j_ = GROUND_JOINT / 200.0
                    if along_x:
                        bx0, by0, bx1, by1 = rx0 + l0 + j_, ry0 + w0 + j_, rx0 + l1 - j_, ry0 + w1 - j_
                    else:
                        bx0, by0, bx1, by1 = rx0 + w0 + j_, ry0 + l0 + j_, rx0 + w1 - j_, ry0 + l1 - j_
                    roll_ = GROUND_RNG.random()
                    z_ = GROUND_RNG.uniform(0.45, 0.8)
                    if min(l1 - l0, w1 - w0) < 0.5 or (roll_ < 0.05 and (l1 - l0) * (w1 - w0) < 13.0):
                        _ground_bare.append((bx0, by0, bx1, by1, along_x))      # this bay never got poured, or broke up
                        continue
                    kind = "ConcreteNew" if roll_ < 0.13 else GROUND_RNG.choice(("ConcreteA", "ConcreteB", "ConcreteOld")) if roll_ < 0.27 else main
                    _ground_plane("Ground_%d_%d_%d_%d" % (r_i, p_i, k_, b_i), bx0, by0, bx1, by1, kind, z_)
                    _ground_bays.append((bx0, by0, bx1, by1, z_))
                    _ground_n["bays"] += 1
    # Repairs on what stayed road: long utility cuts, and a few squares.
    for b_i, (x0, y0, x1, y1, along_x) in enumerate(_ground_bare):
        w_, h_ = x1 - x0, y1 - y0
        length, width = (w_, h_) if along_x else (h_, w_)
        if length < 2.5 or width < 1.5:
            continue
        for c_i in range(GROUND_RNG.choice((0, 1, 1, 2))):
            shape = GROUND_RNG.random()
            kind = GROUND_RNG.choice(("AsphaltPatch", "AsphaltPatch", "AsphaltPatch", "AsphaltPatch"))      # user 2026-11-06: "these strips are too bright", "keep them darker", so nothing lighter than the road. Still a draw, so nothing else moves
            if shape < 0.5:     # along the stretch
                l_ = GROUND_RNG.uniform(2.2, max(2.3, min(length - 0.2, 8.0)))
                t_ = GROUND_RNG.uniform(0.35, 0.7)
                l0 = GROUND_RNG.uniform(0.1, max(0.11, length - l_ - 0.1))
                w0 = GROUND_RNG.uniform(0.3, max(0.31, width - t_ - 0.3))
                rect = (x0 + l0, y0 + w0, x0 + l0 + l_, y0 + w0 + t_) if along_x else (x0 + w0, y0 + l0, x0 + w0 + t_, y0 + l0 + l_)
            elif shape < 0.75:  # across it, from one side
                l_ = GROUND_RNG.uniform(min(1.4, width - 0.2), width - 0.1)
                t_ = GROUND_RNG.uniform(0.35, 0.6)
                l0 = GROUND_RNG.uniform(0.2, length - t_ - 0.2)
                rect = (x0 + l0, y0, x0 + l0 + t_, y0 + l_) if along_x else (x0, y0 + l0, x0 + l_, y0 + l0 + t_)
            else:               # a square-ish repair
                s0_, s1_ = GROUND_RNG.uniform(0.9, 2.2), GROUND_RNG.uniform(0.9, max(1.0, min(width - 0.2, 2.2)))
                l0 = GROUND_RNG.uniform(0.1, max(0.11, length - s0_ - 0.1))
                w0 = GROUND_RNG.uniform(0.1, max(0.11, width - s1_ - 0.1))
                rect = (x0 + l0, y0 + w0, x0 + l0 + s0_, y0 + w0 + s1_) if along_x else (x0 + w0, y0 + l0, x0 + w0 + s1_, y0 + l0 + s0_)
            if rect[2] > x1 or rect[3] > y1 or min(rect[2] - rect[0], rect[3] - rect[1]) < 0.3 or max(rect[2] - rect[0], rect[3] - rect[1]) < 0.9 or any(rect[0] < o_[2] and o_[0] < rect[2] and rect[1] < o_[3] and o_[1] < rect[3] for o_ in _ground_bays):
                continue
            z_ = GROUND_RNG.uniform(0.25, 0.35)
            _ground_plane("GroundPatch_%d_%d" % (b_i, c_i), rect[0], rect[1], rect[2], rect[3], kind, z_)
            _ground_bays.append(rect + (z_,))
            _ground_n["patches"] += 1
    print("ground:", _ground_n, "rects", len(_ground_rects))

