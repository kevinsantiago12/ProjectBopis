# Pass `story_ground_dress` (story levels; 2026-11-09). User: "For S1 and S2, Do a ground and object pass (garbage cans, buckets etc)".
# The arena's dirt, litter and props passes read what the arena's own ground pass left (its open rectangles, its raised bays, its
# folder) and stand everything on flat ground. A story level builds its ground in story_ground instead: road panels, sidewalks 15 cm up,
# steps, section 2 at 180 cm. This hands those passes the story level's:
#   - _ground_rects: the open ground of the dressed sections (levels/*.py dress_point), less the step flights;
#   - STORY_GROUND_TOP(X, Y): the height of the surface at a world point, the top of whatever ground piece is highest there (the poured
#     planes, the bodies under them, the steps, the houses' floors and linings, the curb stones), to set things down on (dirt.py's
#     _ground_top): a trash bag across a curb lies on it, not 1 cm into it;
#   - STORY_GROUND_BASE(X, Y): the slab under that surface (a poured plane sits G_SKIN over its body), which a ground decal is set
#     against, as the arena's are against its road (dirt.py's _ground_decal).
#   dirt.py uses them when they're set; the arena doesn't set them, so its plan doesn't move.
DR_GROUND = "BackAlleys/Ground"
_ground_bare, _ground_bays = [], []


def _sgd_minus(r, holes):
    """Rectangle r (layout m) less the holes, as rectangles."""
    out = [r]
    for h in holes:
        nxt = []
        for a in out:
            if h[0] >= a[2] or h[2] <= a[0] or h[1] >= a[3] or h[3] <= a[1]:
                nxt.append(a)
                continue
            if h[1] > a[1]:
                nxt.append((a[0], a[1], a[2], h[1]))
            if h[3] < a[3]:
                nxt.append((a[0], h[3], a[2], a[3]))
            y0_, y1_ = max(a[1], h[1]), min(a[3], h[3])
            if h[0] > a[0]:
                nxt.append((a[0], y0_, h[0], y1_))
            if h[2] < a[2]:
                nxt.append((h[2], y0_, a[2], y1_))
        out = [q for q in nxt if q[2] - q[0] > 0.05 and q[3] - q[1] > 0.05]
    return out


_sgd_steps = [tuple(s_["r"]) for s_ in LAYOUT_RAW["stairs"] if s_["f"] == 0 and "steps" in s_.get("label", "")]
_ground_rects = []
for a in AREAS:
    if a["kind"] == "open" and LEVEL.dress_point((a["r"][0] + a["r"][2]) / 2, (a["r"][1] + a["r"][3]) / 2):
        _ground_rects += _sgd_minus(tuple(a["r"]), _sgd_steps)

# The ground's surfaces, on a 1 m grid (UE cm): (x0, y0, x1, y1, top)
_sgd_grid = {}
for p in items:
    kind_ = p["folder"].split("/")[-1]
    if kind_ not in ("Ground", "GroundBody", "Floors", "Curbs") or p.get("decal"):
        continue
    x_, y_, z_ = p["loc"]
    sx, sy, sz = (abs(v) for v in p["scale"])
    if p["asset"] == PLANE:
        box = (x_ - sx * 50.0, y_ - sy * 50.0, x_ + sx * 50.0, y_ + sy * 50.0, z_, z_ - G_SKIN)
    elif p["asset"] == CURB_STONE:
        # SM_MainBorder_04: X -0.2..150 along, Y -13.2..13.2 across, Z -7.9..7.9; turned in quarter turns
        c_, s_ = round(math.cos(math.radians(p["rot"][1]))), round(math.sin(math.radians(p["rot"][1])))
        xs_ = (x_ + c_ * -0.2 * sx - s_ * 13.2, x_ + c_ * 150.0 * sx + s_ * 13.2, x_ + c_ * -0.2 * sx + s_ * 13.2, x_ + c_ * 150.0 * sx - s_ * 13.2)
        ys_ = (y_ + s_ * -0.2 * sx + c_ * 13.2, y_ + s_ * 150.0 * sx - c_ * 13.2, y_ + s_ * -0.2 * sx - c_ * 13.2, y_ + s_ * 150.0 * sx + c_ * 13.2)
        box = (min(xs_), min(ys_), max(xs_), max(ys_), z_ + 7.9 * sz, -1e9)       # a surface to set things on, not a slab for decals
    elif p["asset"] == CUBE and abs(p["rot"][1]) < 0.01:
        box = (x_, y_, x_ + sx * 100.0, y_ + sy * 100.0, z_ + sz * 100.0, z_ + sz * 100.0)
    else:
        continue
    for i in range(math.floor(box[0] / 100.0), math.floor(box[2] / 100.0) + 1):
        for j in range(math.floor(box[1] / 100.0), math.floor(box[3] / 100.0) + 1):
            _sgd_grid.setdefault((i, j), []).append(box)


def _sgd_at(X, Y, k):
    tops = [b[k] for b in _sgd_grid.get((math.floor(X / 100.0), math.floor(Y / 100.0)), ()) if b[0] <= X <= b[2] and b[1] <= Y <= b[3]]
    return max(tops) if tops else ground_z(*_lay(X, Y))


def STORY_GROUND_TOP(X, Y):
    return _sgd_at(X, Y, 4)


def STORY_GROUND_BASE(X, Y):
    return _sgd_at(X, Y, 5)


print("ground for the dressing: %d open rectangles, %d surface pieces" % (len(_ground_rects), len({id(b) for v in _sgd_grid.values() for b in v})))
