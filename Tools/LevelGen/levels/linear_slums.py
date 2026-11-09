"""Level data: the linear slum level, working title "the missing patrolman" (user's scenario 2026-11-07; paper layout
Design Document/Linear_Slums_Layout.json from Tools/LevelGen/layout_linear_slums.mjs, the approved plan; never edit the
JSON, edit the .mjs). Story level: no _Arena suffix. Its map name is the user's call (MAP below).

The street houses come from the layout's built-up mass, through the same passes as the arena's houses (houses, walls,
terraces, roofs, stains, floors, finish). The buildings the player enters (the layout's rooms) are built by the story_*
passes: rooms per storey, openings at the layout's positions, slabs, stairs, rails, roofs. Ground heights per area.
Dressing passes are off for this first build (user 2026-11-08: buildings and interiors first)."""
import math

NAME = "linear_slums"
MAP = "/Game/ThirdPerson/Lvl_01_Slum"   # user 2026-11-08: "LevelName is 01_Slum", then the Lvl_ prefix (asked). Sublevels in /Game/ThirdPerson/01_Slum/
LAYOUT = "Design Document/Linear_Slums_Layout.json"
LAYOUT_ENCODING = "utf-8"
OUT = "Saved/LinearSlums"
PREFIX = "plan_"
ORIGIN = (80.0, 60.0)             # layout (80, 60) at the world origin: the level spans about X -46..45 m, Y -89..86 m
FOLDER_ROOT = "Slums"

SWITCHES = {"COVER": False, "PICKUPS": False, "DRESSING": False, "TERRACES": True, "STAINS": True}
PASSES = ["base", "houses", "walls", "terraces", "roofs", "stains", "floors", "finish",
          "story_ground", "story_interiors",
          # the slum's dressing (user 2026-11-09: "do passes on Sections 1 and 2. Dressings"): the arena's passes, scoped
          "story_dress_begin", "awnings", "building_dressing", "street", "low_wires", "posters", "chain_wires", "poles", "asia_cables", "story_road_clear", "graffiti",
          "story_light_fill",
          # the ground and its objects (user 2026-11-09: "For S1 and S2, Do a ground and object pass (garbage cans, buckets etc)"): the arena's, on the slum's ground
          "story_ground_dress", "dirt", "litter", "props",
          "story_dress_end",
          "story_gameplay", "story_resolve", "story_sections"]
STREET_LIGHTS_ON = True           # night: the street pass's bulbs, tubes and lamps are lit (it replaces story_lights' street lamps)
PARAPET_FULL = ("E3",)            # story_ground: E3's hollow-block yard wall along its whole north edge, capped (user 2026-11-09)
PROP_DRUMS = 6                    # props: garbage drums at the foot of walls (user 2026-11-09: "garbage cans, buckets etc")
FITTED = ("ROW",)                 # story_interiors' fitted baseline: one-leaf doors in jambs, framed windows, the user's steep stair (section 4)
LIGHT_FILL = True                 # story_light_fill: more lights where the slum's open ground is darkest (user 2026-11-09: "light are unevenly distributed")
AFTER_WRITE = []

BALCONIES, WIDE_TERRACES, SHACKS = 8, 4, 5
NO_SPLIT = ("NROOF",)
FIXED = ("NROOF",)
ROOFS = {"NROOF": "flat"}         # the neighbour's roof the last fight's survivors cross a plank to: flat, at +8
NO_BALCONY = ("NROOF",)
THIN_IDS = ()
SPECIAL = {}
DECK_FACE = None

# Ground (cm) per section, from the layout's sections table; areas may override.
SEC_Z = {1: 0.0, 2: 180.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: -180.0, 7: -180.0}
AREA_Z = {"PASS": 0.0}            # the bodega's back passage stays at the bodega's floor; it drops 1.8 m into the guard room
STEP_RISE = 180.0                 # the eskinita's steps (layout stairs[0]): y 84..87 rise 1.8 m going south
FLOOR_T = 18.0                    # every floor slab (the houses' FLOOR_H)

# Storeys of the buildings you enter. User 2026-11-08: "the interiors are too tall (ceilings a bit too high)": 3.5 m floor to floor,
# 3.32 m clear (was the layout's 4 m; AsiaSlum's demo map is 4 m too). The holding house stays taller: the bodega's passage drops
# 1.8 m into it through a 2.25 m opening. The neighbour's roof the plank crosses to follows the trap house's.
STOREY_IN = 350.0
FIXED_SH = {"NROOF": STOREY_IN}
# Third storeys. User 2026-11-08: "The buildings in Section 1 have 3 storey levels which is unusually high": none on houses facing the
# main street, and fewer elsewhere (the arena's 0.4).
P_THIRD = 0.2
# The buildings the player enters. rect in layout metres; ground: the ground (cm) they stand on; storeys: storey heights
# (cm, floor top to floor top). Their floors sit FLOOR_T over the ground, like the street houses'. sec: section.
ENTERED = [
    {"id": "ROW", "rect": (60.0, 58.5, 84.0, 70.5), "ground": 0.0, "storeys": (STOREY_IN, STOREY_IN), "sec": 4,
     "what": "four row houses H1-H4, knocked through"},
    {"id": "PLY", "rect": (84.0, 70.5, 99.0, 75.0), "ground": 0.0, "storeys": (300.0,), "sec": 5,
     "what": "three open-fronted plywood rooms on the covered alley"},
    {"id": "BOD", "rect": (94.5, 36.0, 112.5, 49.5), "ground": 0.0, "storeys": (600.0,), "sec": 5,
     "what": "the bodega, 6 m high, with a mezzanine at +3"},
    {"id": "PASS", "rect": (112.5, 39.0, 115.5, 42.0), "ground": 0.0, "storeys": (330.0,), "sec": 6,
     "what": "the bodega's back passage"},
    {"id": "HOLD", "rect": (115.5, 36.0, 130.5, 51.0), "ground": -180.0, "storeys": (430.0,), "sec": 6,
     "what": "the holding house: guard room, corridor, plywood cells"},
    {"id": "TRAP", "rect": (139.5, 30.0, 154.5, 48.0), "ground": -180.0, "storeys": (STOREY_IN, STOREY_IN), "sec": 7,
     "what": "the trap house: hollow-block ground storey, plastered +4, the +8 roof with its terraces"},
]
WOODEN = {"id": "TRAPW", "rect": (144.0, 30.0, 154.5, 42.75), "storeys": (320.0,), "sec": 7}   # the wooden storey on the trap house's roof
NROOF_RECT = (136.5, 22.5, 145.5, 28.5)    # the layout's "neighbour's roof" (f2, off): a 2-storey house at the trap house's ground

_AREAS, _FOOT, _OPEN = [], [], []


def _in(r, lx, ly, pad=0.0):
    return r[0] - pad < lx < r[2] + pad and r[1] - pad < ly < r[3] + pad


def area_z(a):
    return AREA_Z.get(a["id"], SEC_Z[a["sec"]])


_GRID = {}       # (2026-11-09) _FOOT and the ground areas on a 1 m grid, made at the first lookup (after setup): lists in their own order


def _grid_of(name, src, rect=lambda r: r):
    """The grid of src's rects (rect(item)), rebuilt whenever the list has grown since (they only grow, in setup)."""
    n, g = _GRID.get(name, (-1, None))
    if n != len(src):
        g = {}
        for k, r in enumerate(rect(q) for q in src):
            for i in range(math.floor(r[0]), math.floor(r[2]) + 1):
                for j in range(math.floor(r[1]), math.floor(r[3]) + 1):
                    g.setdefault((i, j), []).append(k)
        _GRID[name] = (len(src), g)
    return g


def _ground(lx, ly):
    """Ground (cm) of the f0 area at (lx, ly), or None."""
    for k in _grid_of("areas", _AREAS, lambda a: a["r"]).get((math.floor(lx), math.floor(ly)), ()):
        a = _AREAS[k]
        if a["kind"] != "room" and _in(a["r"], lx, ly):
            if a["id"] == "E1":                    # the steps up into the eskinita
                return min(STEP_RISE, max(0.0, (ly - 84.0) / 3.0 * STEP_RISE))
            return a["z"]
    return None


def outside(lx, ly):
    """Beyond the level: not walkable ground, not a house, not a building the player enters."""
    return not any(_in(_FOOT[k], lx, ly) for k in _grid_of("foot", _FOOT).get((math.floor(lx), math.floor(ly)), ()))


def ground_z(lx, ly):
    g = _ground(lx, ly)
    if g is not None:
        return g
    best = None                                    # a setback's gap or the like: the nearest walkable ground's
    for a in _OPEN:
        x0, y0, x1, y1 = a["r"]
        d = math.hypot(max(x0 - lx, 0.0, lx - x1), max(y0 - ly, 0.0, ly - y1))
        if best is None or d < best[0]:
            best = (d, a["z"])
    return best[1] if best and best[0] < 4.0 else 0.0


def _probes(b, out=0.3, step=0.75):
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    n = max(1, int(round((x1 - x0) / step)))
    for k in range(n):
        lx = x0 + (k + 0.5) * (x1 - x0) / n
        yield "north", lx, y0 - out
        yield "south", lx, y1 + out
    n = max(1, int(round((y1 - y0) / step)))
    for k in range(n):
        ly = y0 + (k + 0.5) * (y1 - y0) / n
        yield "west", x0 - out, ly
        yield "east", x1 + out, ly


def touches_edge(b):
    return any(outside(lx, ly) for _, lx, ly in _probes(b))


def no_third(b):
    """A house that faces the main street (section 1), or a plain one in the compound, stays at two storeys at most."""
    return b.get("plain") or any(a["sec"] == 1 and _in(a["r"], lx, ly) for _, lx, ly in _probes(b) for a in _AREAS)


# The compound. User 2026-11-08: "this entire area, aside from Section 1 and 2 are all a single compound", "the slum generator is
# useless here besides those 2 sections", "keep those as houses. the compound starts where you drop from there". So a house beside
# the main street or the eskinita stays a slum house; one that borders only the compound is plain: closed, unpainted, hollow blocks
# on every windowless face, few doors and windows (the ground floor's barred), no balconies or third storey, no street lamps.
PLAIN_OPEN = ({"door": 0.05, "window": 0.08}, {"window": 0.12})


def dress_house(b):
    """A house that takes the slum's dressing: one that isn't the compound's."""
    return not b.get("plain")


def dress_point(lx, ly):
    """A point in the slum: its nearest walkable ground is section 1 or 2."""
    best = None
    for a in _AREAS:
        d = _rect_dist(a["r"], lx, ly)
        if best is None or d < best[0]:
            best = (d, a["sec"])
    return best is not None and best[1] <= 2


# Unaligned (user 2026-11-09: "makes sure that each house is unaligned with the adjacent house"). Along a street, a slum house's
# front never lines up with its neighbour's: its setback differs by 30 cm or more (the arena's smallest return between two houses;
# shorter returns leave no room for the corner trims), from a random draw (no repeating rhythm); and
# its storey height differs from the houses beside it, so eaves and bands don't run on from one house to the next.
# AsiaSlum's cable bundles, ring brackets and drops where they fit better than the thin wires (passes/asia_cables.py; user 2026-11-09).
ASIA_CABLES = True
# Section 1 is the main road (user 2026-11-09: "it needs the power cables a bit higher. Trucks should be able to pass through"): no wire
# lower than this over its carriageway, cm over the road (passes/story_road_clear.py). A Philippine truck is up to about 4.3 m.
ROAD_CLEAR = 500.0

STAGGER_SETBACKS = (0.0, 0.3, 0.6, 0.9)
STAGGER_STEP = 0.3
STAGGER_RNG = __import__("random").Random(431)


def _neighbours(b, blocks, side, strips=False):
    """Houses beside b on the same face line (same side, touching end to end). strips: count the balcony and terrace strips and the
    compound's plain houses too."""
    out = []
    for o in blocks.values():
        if o is b or ((o.get("plain") or o.get("balcony")) and not strips):
            continue
        if side in ("north", "south"):
            line_b, line_o = (b["y0"], o["y0"]) if side == "north" else (b["y1"], o["y1"])
            touch = abs(o["x1"] - b["x0"]) < 0.01 or abs(o["x0"] - b["x1"]) < 0.01
        else:
            line_b, line_o = (b["x0"], o["x0"]) if side == "west" else (b["x1"], o["x1"])
            touch = abs(o["y1"] - b["y0"]) < 0.01 or abs(o["y0"] - b["y1"]) < 0.01
        if touch and abs(line_b - line_o) < 0.01:
            out.append(o)
    return out


def _strip(b):
    """A balcony or terrace strip cut off the front of a house (houses pass): b["balcony"] is its outward side."""
    return b["id"].endswith("b") and bool(b.get("balcony"))


def _staggers(b):
    if b.get("plain") or b["fixed"]:
        return False
    return _strip(b) or not (b.get("balcony") or b["roof"] == "terrace")


def _fronts_slum(b, side):
    """The ground in front of this face is the slum's (street, eskinita, wash yard), not the compound's: a face on the compound
    edge stays where it is, against the compound's own walls."""
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    if side in ("north", "south"):
        ly = y0 - 0.75 if side == "north" else y1 + 0.75
        pts = [(x0 + (k + 0.5) * (x1 - x0) / 4, ly) for k in range(4)]
    else:
        lx = x0 - 0.75 if side == "west" else x1 + 0.75
        pts = [(lx, y0 + (k + 0.5) * (y1 - y0) / 4) for k in range(4)]
    return all(dress_point(*q) for q in pts)


def min_depth(b):
    """How deep a house must stay after its setback (houses pass): a strip 1.2 m (the houses pass cuts them 1.5 m or 3 m deep, so
    even the narrow ones can step back once), a house 3 m."""
    return 1.2 if _strip(b) else 3.0


def stagger(blocks, cuts, face_open):
    """Every slum house and terrace strip gets a setback per open face on the slum's ground, STAGGER_STEP or more off every
    neighbour's on that line. Every other face (the compound's plain houses, 1-storey terrace houses, fixed houses, and a slum
    house's faces on the compound) keeps the houses pass's cut, and counts as a neighbour at it."""
    faces = []                                      # (house, side, the setbacks it has room for)
    for b in sorted(blocks.values(), key=lambda q: (q["x0"], q["y0"])):
        if not _staggers(b):
            continue
        for side in ("north", "south", "west", "east"):
            if not face_open(b, side, 0) or (_strip(b) and side != b["balcony"]) or not _fronts_slum(b, side):
                continue                            # a strip steps back only on its outward face; nothing on the compound edge
            depth = (b["y1"] - b["y0"]) if side in ("north", "south") else (b["x1"] - b["x0"])
            faces.append((b, side, [d for d in STAGGER_SETBACKS if depth - d >= min_depth(b)]))
    # The faces with the least room choose first (a shallow strip that can't step back at all), so the rest step round them.
    faces.sort(key=lambda f: len(f[2]))
    moving = {(b["id"], side) for b, side, _ in faces}     # the rest keep the setback they have (none, or the houses pass's cut)
    keep = [c for c in cuts if (c[0]["id"], c[1]) not in moving]
    done = {(c[0]["id"], c[1]): c[2] for c in keep}
    for b, side, room in faces:
        taken = [done.get((o["id"], side), 0.0) for o in _neighbours(b, blocks, side, strips=True)
                 if (o["id"], side) not in moving or (o["id"], side) in done]
        opts = [d for d in room if all(abs(d - t) >= STAGGER_STEP - 1e-6 for t in taken)] or room
        d = STAGGER_RNG.choice(opts)
        done[(b["id"], side)] = d
        if d:
            keep.append((b, side, d))
    def shows(o, side):                             # any 1.5 m piece of the face has open ground in front
        if side in ("north", "south"):
            n = max(1, int(round((o["x1"] - o["x0"]) / 1.5)))
            return any(face_open(dict(o, x0=o["x0"] + k * 1.5, x1=o["x0"] + (k + 1) * 1.5), side, 0) for k in range(n))
        n = max(1, int(round((o["y1"] - o["y0"]) / 1.5)))
        return any(face_open(dict(o, y0=o["y0"] + k * 1.5, y1=o["y0"] + (k + 1) * 1.5), side, 0) for k in range(n))
    in_line = sorted({tuple(sorted((b["id"], o["id"]))) + (side,) for b, side, _ in faces
                      for o in _neighbours(b, blocks, side, strips=True)
                      if abs(done[(b["id"], side)] - done.get((o["id"], side), 0.0)) < STAGGER_STEP - 1e-6 and shows(o, side)})
    print("stagger: %d street fronts; in line with a neighbour: %d %s" % (len(faces), len(in_line), in_line))
    return keep


def stagger_heights(blocks):
    sh = (340.0, 360.0, 380.0, 400.0, 420.0)
    for b in sorted(blocks.values(), key=lambda q: (q["x0"], q["y0"])):
        if b.get("plain") or b.get("balcony") or b["fixed"] or b.get("shack"):
            continue
        near = {o["sh"] for side in ("north", "south", "west", "east") for o in _neighbours(b, blocks, side)}
        near |= {o["sh"] for o in blocks.values() if o is not b and not o.get("plain") and
                 (abs(o["x1"] - b["x0"]) < 0.01 or abs(o["x0"] - b["x1"]) < 0.01 or abs(o["y1"] - b["y0"]) < 0.01 or abs(o["y0"] - b["y1"]) < 0.01) and
                 min(o["x1"], b["x1"]) - max(o["x0"], b["x0"]) > -0.01 and min(o["y1"], b["y1"]) - max(o["y0"], b["y0"]) > -0.01}
        if b["sh"] in near:
            opts = [v for v in sh if all(abs(v - n) >= 20.0 for n in near)] or [v for v in sh if v not in near] or list(sh)
            b["sh"] = STAGGER_RNG.choice(opts)


def house_plain(b):
    secs = {a["sec"] for _, lx, ly in _probes(b) for a in _AREAS if _in(a["r"], lx, ly)}
    if secs & {1, 2}:
        return False
    b["p_open"] = PLAIN_OPEN
    return True


def house_base(b):
    """A street house stands on the lowest walkable ground beside it, so no face hangs over a drop; faces toward
    higher ground show above it only (the walls pass's "buried")."""
    if b["id"] == "NROOF":
        return -180.0
    if "zblock" in b:
        return b["zblock"]                             # every house of a block on one ground: no steps between them
    zs = [g for _, lx, ly in _probes(b) for g in [_ground(lx, ly)] if g is not None]
    if zs:
        return min(zs)
    cx, cy = (b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2
    return ground_z(cx, cy)


def _subtract(r, cut):
    """Rect r minus rect cut, as up to four rects."""
    x0, y0, x1, y1 = r
    c0, d0, c1, d1 = cut
    if c0 >= x1 or c1 <= x0 or d0 >= y1 or d1 <= y0:
        return [r]
    out = []
    if d0 > y0:
        out.append((x0, y0, x1, d0))
    if d1 < y1:
        out.append((x0, d1, x1, y1))
    a0, a1 = max(y0, d0), min(y1, d1)
    if c0 > x0:
        out.append((x0, a0, c0, a1))
    if c1 < x1:
        out.append((c1, a0, x1, a1))
    return [o for o in out if o[2] - o[0] > 1e-6 and o[3] - o[1] > 1e-6]


def _absorb_thin(rects, thin=3.0, max_depth=12.0, least=3.0):
    """A strip under `thin` m deep joins the block it lies along: that block is cut where the strip ends, and its middle
    takes the strip, if it stays under max_depth and what's cut off is at least `least` wide. The layout's mass is a
    raster's row runs, and the strips it leaves would be 1.5 m houses against full ones."""
    rects = list(rects)
    e = 1e-6
    changed = True
    while changed:
        changed = False
        for t in rects:
            w, d = t[2] - t[0], t[3] - t[1]
            if min(w, d) >= thin:
                continue
            for n in rects:
                if n is t:
                    continue
                if w >= d:                                  # an east-west strip: a block north or south of it
                    north, south = abs(n[3] - t[1]) < e, abs(n[1] - t[3]) < e
                    if not (north or south) or n[0] > t[0] + e or n[2] < t[2] - e:
                        continue
                    if (n[3] - n[1]) + d > max_depth or 0 < t[0] - n[0] < least or 0 < n[2] - t[2] < least:
                        continue
                    pieces = [q for q in ((n[0], n[1], t[0], n[3]), (t[2], n[1], n[2], n[3])) if q[2] - q[0] > e]
                    mid = (t[0], n[1], t[2], t[3]) if north else (t[0], t[1], t[2], n[3])
                else:                                       # a north-south strip: a block west or east of it
                    west, east = abs(n[2] - t[0]) < e, abs(n[0] - t[2]) < e
                    if not (west or east) or n[1] > t[1] + e or n[3] < t[3] - e:
                        continue
                    if (n[2] - n[0]) + w > max_depth or 0 < t[1] - n[1] < least or 0 < n[3] - t[3] < least:
                        continue
                    pieces = [q for q in ((n[0], n[1], n[2], t[1]), (n[0], t[3], n[2], n[3])) if q[3] - q[1] > e]
                    mid = (n[0], t[1], t[2], t[3]) if west else (t[0], t[1], n[2], t[3])
                rects = [q for q in rects if q is not t and q is not n] + pieces + [mid]
                changed = True
                break
            if changed:
                break
    return rects


def _grid_rects(g, nx, ny, xs0, ys0, cell):
    """Greedy largest rectangles of the True cells of grid g (rows of nx), consumed as found."""
    out = []
    # (2026-11-09) Only the box that still has cells is scanned, kept by per-row and per-column counts. The empty rows and columns
    # round it hold no candidate (their heights are 0), so the same rectangles come out in the same order as the full scan.
    rows_ = [sum(1 for v in r[:nx] if v) for r in g[:ny]]
    cols_ = [sum(1 for j in range(ny) if g[j][i]) for i in range(nx)]
    while True:
        best, hts = None, [0] * nx
        js_ = [j for j in range(ny) if rows_[j]]
        is_ = [i for i in range(nx) if cols_[i]]
        if not js_:
            break
        i_lo, i_hi = is_[0], is_[-1]
        for j in range(js_[0], js_[-1] + 1):
            for i in range(i_lo, i_hi + 1):
                hts[i] = hts[i] + 1 if g[j][i] else 0
            stack = []
            for i in range(i_lo, i_hi + 2):
                h = hts[i] if i <= i_hi else 0
                start = i
                while stack and stack[-1][1] >= h:
                    s0, sh = stack.pop()
                    area = sh * (i - s0)
                    if sh and (best is None or area > best[0]):
                        best = (area, s0, j - sh + 1, i, j + 1)
                    start = s0
                stack.append((start, h))
        if best is None:
            break
        _, i0, j0, i1, j1 = best
        for j in range(j0, j1):
            for i in range(i0, i1):
                if g[j][i]:
                    g[j][i] = False
                    rows_[j] -= 1
                    cols_[i] -= 1
        out.append((xs0 + i0 * cell, ys0 + j0 * cell, xs0 + i1 * cell, ys0 + j1 * cell))
    return out


# The compound's open ground (user 2026-11-08, of the yard: "The yard should just be 1 storey walls around it, push these buildings
# back so they look like distant buildings"; of the alleys: "we are inside the compound, It does not make sense to have residential
# houses leading into it"). Round each open area of sections 3-7 (not the gated car lane), a wall one storey high, and behind it
# COMPOUND_BACK m of empty ground ("nml": nobody's land, walled off), the buildings beyond it. Houses lining the slum's streets keep
# SLUM_KEEP m of depth where the compound backs onto them, so the eskinita stays lined with houses.
COMPOUND_BACK, SLUM_KEEP = 6.0, 4.5
COMPOUND_WALL_H = 350.0
COMPOUND_WALL_HI = {"CA1": 400.0}      # the covered alley's lean-to rests on its wall
COMPOUND_SKIP = ("LANE",)


def _rect_dist(r, x, y):
    """Square-cornered distance (the larger of the two axes), so the rings round an area stay rectangles."""
    return max(r[0] - x, 0.0, x - r[2], r[1] - y, y - r[3])


def _mass_blocks(lay, areas, cuts, cell=0.75, max_depth=10.5):
    """The built-up mass as house blocks, and the compound's walled-off ground, on the layout's 0.75 m cells. Mass: the layout's
    (its rects are a raster's row runs) and, round the compound's open ground, the ring beyond the walled-off strip. Greedy largest
    rectangles, those deeper than max_depth halved, thin strips merged into the block beside them."""
    comp = [a for a in areas if a["sec"] >= 3 and a["kind"] in ("open", "cov") and a["id"] not in COMPOUND_SKIP]
    slum = [a for a in areas if a["sec"] <= 2]
    mass = [tuple(r) for r in lay["mass_auto"]]
    xs0 = min([r[0] for r in mass] + [a["r"][0] - COMPOUND_BACK - 8.0 for a in comp])
    ys0 = min([r[1] for r in mass] + [a["r"][1] - COMPOUND_BACK - 8.0 for a in comp])
    xs1 = max([r[2] for r in mass] + [a["r"][2] + COMPOUND_BACK + 8.0 for a in comp])
    ys1 = max([r[3] for r in mass] + [a["r"][3] + COMPOUND_BACK + 8.0 for a in comp])
    xs0, ys0 = math.floor(xs0 / cell) * cell, math.floor(ys0 / cell) * cell
    nx, ny = int(round((xs1 - xs0) / cell)) + 1, int(round((ys1 - ys0) / cell)) + 1
    g_mass = [[False] * nx for _ in range(ny)]
    g_nml = {}                                    # compound area id -> grid of its walled-off ground
    for j in range(ny):
        for i in range(nx):
            x, y = xs0 + (i + 0.5) * cell, ys0 + (j + 0.5) * cell
            if any(_in(a["r"], x, y) for a in areas) or any(_in(c, x, y) for c in cuts):
                continue
            d_slum = min([_rect_dist(a["r"], x, y) for a in slum] or [1e9])
            dc = sorted((_rect_dist(a["r"], x, y), a["id"]) for a in comp) if comp else [(1e9, None)]
            if dc[0][0] <= COMPOUND_BACK and d_slum >= SLUM_KEEP:
                g_nml.setdefault(dc[0][1], [[False] * nx for _ in range(ny)])[j][i] = True
            elif any(_in(r, x, y) for r in mass) or (dc[0][0] <= COMPOUND_BACK + 7.5 and d_slum >= SLUM_KEEP):
                g_mass[j][i] = True
    nml = [(aid, r) for aid, g in sorted(g_nml.items()) for r in _grid_rects(g, nx, ny, xs0, ys0, cell)]
    out = _absorb_thin(_grid_rects(g_mass, nx, ny, xs0, ys0, cell))
    blocks = []
    for x0, y0, x1, y1 in out:
        w, d = x1 - x0, y1 - y0
        pieces = [(x0, y0, x1, y1)]
        if min(w, d) > max_depth:                  # back to back: two blocks, each facing its own street
            if w < d:
                m = x0 + round(w / 2 / 1.5) * 1.5
                pieces = [(x0, y0, m, y1), (m, y0, x1, y1)]
            else:
                m = y0 + round(d / 2 / 1.5) * 1.5
                pieces = [(x0, y0, x1, m), (x0, m, x1, y1)]
        blocks.extend(pieces)
    return blocks, nml


def setup(NS):
    """Called by gen_level.py before the passes: the level's bounds, ground and blocks."""
    lay = NS["L"]
    for a in lay["areas"]:
        if a["f"] != 0:
            continue
        a2 = dict(a, r=(a["x0"], a["y0"], a["x1"], a["y1"]), z=area_z(a))
        _AREAS.append(a2)
        if a2["kind"] != "room":
            _OPEN.append(a2)
    cuts = [e["rect"] for e in ENTERED] + [NROOF_RECT]
    mass_rects, nml = _mass_blocks(lay, list(_AREAS), cuts)
    by_id = {a["id"]: a for a in _AREAS}
    for k, (aid, r) in enumerate(nml):            # the walled-off ground: open, at its compound area's height, out of reach
        src = by_id[aid]
        a2 = {"id": "NML%d" % k, "sec": src["sec"], "f": 0, "kind": "nml", "r": r, "z": src["z"], "of": aid,
              "x0": r[0], "y0": r[1], "x1": r[2], "y1": r[3], "label": "behind the compound wall"}
        _AREAS.append(a2)
        _OPEN.append(a2)
    blocks = []
    for k, (x0, y0, x1, y1) in enumerate(sorted(mass_rects, key=lambda r: (r[1], r[0]))):
        thin_ = min(x1 - x0, y1 - y0) < 3.0
        blocks.append({"id": "M%02d" % (k + 1), "x0": x0, "y0": y0, "x1": x1, "y1": y1, "storeys": 1 if thin_ else 2})
    for b in blocks:
        b["zblock"] = house_base(b)
    x0, y0, x1, y1 = NROOF_RECT
    blocks.append({"id": "NROOF", "x0": x0, "y0": y0, "x1": x1, "y1": y1, "storeys": 2})
    _FOOT.extend(a["r"] for a in _AREAS)
    _FOOT.extend((b["x0"], b["y0"], b["x1"], b["y1"]) for b in blocks)
    _FOOT.extend(e["rect"] for e in ENTERED)
    extra = []
    for e in ENTERED:
        x0, y0, x1, y1 = e["rect"]
        # Heights as the street houses' (before the floors pass lifts them FLOOR_T): ground + storeys, the parapet on top.
        top = e["ground"] + sum(e["storeys"]) + (106.0 if e["id"] == "TRAP" else 0.0)
        extra.append({"id": e["id"], "x0": x0, "y0": y0, "x1": x1, "y1": y1, "storeys": len(e["storeys"]), "top": top})
    x0, y0, x1, y1 = WOODEN["rect"]
    extra.append({"id": WOODEN["id"], "x0": x0, "y0": y0, "x1": x1, "y1": y1, "storeys": 3,
                  "top": -180.0 + 2 * STOREY_IN + WOODEN["storeys"][0]})
    NS["LAYOUT_RAW"] = lay
    # The arena passes keep their pieces inside (W0, W) x (H0, H): here, the level's whole footprint, a metre out.
    NS["W0"], NS["W"] = min(r[0] for r in _FOOT) - 1.0, max(r[2] for r in _FOOT) + 1.0
    NS["H0"], NS["H"] = min(r[1] for r in _FOOT) - 1.0, max(r[3] for r in _FOOT) + 1.0
    NS.update(ENTERED=ENTERED, WOODEN=WOODEN, FLOOR_T=FLOOR_T, STEP_RISE=STEP_RISE, SEC_Z=SEC_Z)
    NS["AREAS"] = _AREAS
    NS["EXTRA_SOLID"] = extra
    NS["EDGE_RECTS"] = [{"x0": a["r"][0], "y0": a["r"][1], "x1": a["r"][2], "y1": a["r"][3]} for a in _AREAS]
    NS["outside"], NS["touches_edge"], NS["ground_z"] = outside, touches_edge, ground_z
    # No gallery deck here: one far away, so the arena passes' tests against it all fail.
    NS["L"] = {"blocks": blocks, "deck": {"x0": -1e6, "y0": -1e6, "x1": -1e6 + 1, "y1": -1e6 + 1},
               "stairs": [], "doors": [], "cover": [], "pickups": [], "wander": [],
               "player_start": {"x": lay["start"][0], "y": lay["start"][1]},
               "bounds": [NS["W0"], NS["H0"], NS["W"], NS["H"]]}      # for the checks (check_dressing BOUNDS)
    NS.update(COMPOUND_WALL_H=COMPOUND_WALL_H, COMPOUND_WALL_HI=COMPOUND_WALL_HI, COMPOUND_SKIP=COMPOUND_SKIP)
    print("linear slums: %d areas on the ground (%d walled off behind the compound), %d street blocks, %d entered buildings" % (
        len(_AREAS), len(nml), len(blocks), len(ENTERED)))
