# Pass `base`, run first by gen_level.py in the level's shared namespace: put() and solid().
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.

# ZB: the base height (cm) of the house being built. The house passes set it per house and put() adds it, so a house
# is built as if it stood at 0 and its relations to its neighbours (cover_top, taller_at) are measured from its own
# base. 0 everywhere in the arena (one ground height), so nothing there changes. Levels with ground heights give a
# house its base as b["z"].
ZB = 0.0


def put(label, asset, x, y, z, yaw=0.0, scale=(1, 1, 1), folder="BackAlleys", roll=0.0, nocoll=False, mat=None,
        vol=False, mats=None, decal=False):
    """mat: "interior" or "hidden" (special cases); mats: material paths per slot, as overrides; decal: asset is the
    decal material and a DecalActor is placed."""
    if ZB:
        z = z + ZB
    items.append({"label": label, "asset": asset, "loc": [round(x, 1), round(y, 1), round(z, 1)],
                  "rot": [0.0, float(yaw), float(roll)], "scale": [round(s, 4) for s in scale], "folder": folder,
                  "nocoll": nocoll, "mat": mat, "vol": vol, "mats": mats, "decal": decal})


# The level's bounds. A level's setup() may define these first; otherwise they're the arena's: one W x H rectangle of
# layout ground, everything beyond it solid and taller than anything, and the ground at 0.
if "outside" not in globals():
    def outside(lx, ly):
        """(lx, ly) is beyond the level: solid, and taller than anything."""
        return lx <= 0 or lx >= W or ly <= 0 or ly >= H
if "touches_edge" not in globals():
    def touches_edge(b):
        """House b stands against the level's edge (its outer wall is the level's)."""
        return b["x0"] <= 0 or b["y0"] <= 0 or b["x1"] >= W or b["y1"] >= H
if "ground_z" not in globals():
    def ground_z(lx, ly):
        """Height (cm) of the open ground at (lx, ly)."""
        return 0.0
if "EDGE_RECTS" not in globals():
    EDGE_RECTS = [{"x0": 0.0, "x1": W, "y0": 0.0, "y1": H}]    # edges that split a house's side (side_intervals)
if "EXTRA_SOLID" not in globals():
    EXTRA_SOLID = []     # rects that stand like houses but aren't built by these passes: x0..y1, storeys, top (cm)


def solid(lx, ly, s):
    if outside(lx, ly):
        return True
    return any(b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] and b["storeys"] > s for b in BLOCKS.values()) or \
        any(e["x0"] < lx < e["x1"] and e["y0"] < ly < e["y1"] and e["storeys"] > s for e in EXTRA_SOLID)

