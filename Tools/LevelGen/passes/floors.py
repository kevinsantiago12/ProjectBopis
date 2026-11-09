# Pass `floors`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Building floors: everything built so far is lifted FLOOR_H onto an 18 cm slab under each house.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# Building floors. User 2026-11-04: "can we put a floor on the buildings. currently the door go all the way to the road
# floor ... There is usually "riser" below the door that lifts it off the ground. The solution to this is to put the
# buildings on top of a "building floor"". Every house and door end wall stands on a concrete slab FLOOR_H tall, proud by
# FLOOR_OUT over open ground (not into a neighbour or past the arena edge). One height for all, applied last, so every
# relation between houses (covers, corners, trims) holds. The road, gallery deck, stairs and gameplay points stay put.
FLOOR_H, FLOOR_OUT = 18.0, 8.0
FLOORS = "BackAlleys/Floors"
LIFTED = (BLK, "BackAlleys/Lids", "BackAlleys/Terraces", RF, "BackAlleys/SpawnDoors", "BackAlleys/Decals")
for p in items:
    if p["folder"] in LIFTED and p["label"] != "Floor_Collision":
        p["loc"][2] = round(p["loc"][2] + FLOOR_H, 1)


def floor_box(label, a0, b0, a1, b1):
    """A slab over layout metres a0..a1 east, b0..b1 south; 5 cm into the road."""
    X0, Y0 = ue(a0, b1)
    X1, Y1 = ue(a1, b0)
    put(label, CUBE, X0, Y0, -5.0, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, (FLOOR_H + 5.0) / 100.0), folder=FLOORS,
        mats=[CONC])


_m = FLOOR_OUT / 100.0
for bid, b in BLOCKS.items():
    ZB = b.get("z", 0.0)
    ivs = {side: side_intervals(b, side, lambda c: c) for side in ("north", "south", "west", "east")}
    out = {side: _m if all(c == 0 for _, _, c in iv) else 0.0 for side, iv in ivs.items()}
    floor_box("Floor_" + bid, b["x0"] - out["west"], b["y0"] - out["north"], b["x1"] + out["east"], b["y1"] + out["south"])
    for side, iv in ivs.items():                    # a side only partly open: strips along the open parts
        if out[side]:
            continue
        for n_, (t0, t1, c) in enumerate(iv):
            if c != 0 or t1 - t0 < 0.01:
                continue
            if side in ("north", "south"):
                a0 = b["x0"] + t0 - (out["west"] if t0 < 1e-6 else 0.0)
                a1 = b["x0"] + t1 + (out["east"] if abs(b["x0"] + t1 - b["x1"]) < 1e-6 else 0.0)
                b0, b1 = (b["y0"] - _m, b["y0"]) if side == "north" else (b["y1"], b["y1"] + _m)
            else:
                b0 = b["y0"] + t0 - (out["north"] if t0 < 1e-6 else 0.0)
                b1 = b["y0"] + t1 + (out["south"] if abs(b["y0"] + t1 - b["y1"]) < 1e-6 else 0.0)
                a0, a1 = (b["x0"] - _m, b["x0"]) if side == "west" else (b["x1"], b["x1"] + _m)
            floor_box("FloorStrip_%s_%s%d" % (bid, side[0].upper(), n_), a0, b0, a1, b1)
ZB = 0.0
for d in L["doors"]:                                # the door end walls: across their 4.5 m alley, tucked into the sides
    n = FACE[d["face"]]
    nx_, ny_ = LNORM[n]
    if n in ("north", "south"):
        floor_box("Floor_" + d["id"], d["x"] - 2.32, min(d["y"], d["y"] + ny_ * _m) - (0.25 if ny_ > 0 else 0.0),
                  d["x"] + 2.32, max(d["y"], d["y"] + ny_ * _m) + (0.25 if ny_ < 0 else 0.0))
    else:
        floor_box("Floor_" + d["id"], min(d["x"], d["x"] + nx_ * _m) - (0.25 if nx_ > 0 else 0.0), d["y"] - 2.32,
                  max(d["x"], d["x"] + nx_ * _m) + (0.25 if nx_ < 0 else 0.0), d["y"] + 2.32)

