# Pass `stalls`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Closed shop stalls (walls and shutters inside SM_Shop_A_001).
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# The shop stalls. User 2026-11-06: "the wall if open". SM_Shop_A_001 is only a counter and an open bar frame, with the block's core 1.5 m behind it, so it read as a hole in the
# wall. Closed for the night: the kit's solid wall in the same module, just behind the frame, and a roll-up shutter down inside the frame to the counter. Frame X 0..300, Z 0..400;
# SM_RollupDoor_A_002 X -283.6..270.6, Z -333..0. A stall buried behind a house comes out of the plan at the end, so nothing else moves: B2_S0_1_1 stood 60 cm past B6h2's end wall, right on
# the next stall's frame. User 2026-11-06: "Shop A 001, overlapping surfaces with wall".
STALL_RNG = random.Random(229)
_stalls = [p for p in items if p["asset"].endswith("/SM_Shop_A_001")]
_buried_stalls = set()
for k_, p in enumerate(sorted(_stalls, key=lambda q_: q_["label"])):
    side = _yaw_side[round(p["rot"][1]) % 360]
    x0_, y0_, z_ = p["loc"]
    roll_ = STALL_RNG.choice(ROLL_MATS)
    lx_, ly_ = _lay(*at(x0_, y0_, side, 150.0, 60.0))
    if any(b_["x0"] < lx_ < b_["x1"] and b_["y0"] < ly_ < b_["y1"] for b_ in L["blocks"]):      # B2_S0_1_1, mostly behind B6h2
        _buried_stalls.add(p["label"])
        continue
    # Always behind the frame: the stall's frame and this wall share the planes local Y 0 and -20, and the first stall's wall sat exactly on them. User 2026-11-06: "Shop A 001, overlapping surfaces with wall".
    x_, y_ = at(x0_, y0_, side, 0.0, -1.3 * (k_ + 1))
    put(p["label"] + "_Back", AS + "SM_HouseWall_A_001", x_, y_, z_, YAW[side], (1, 1, 1), folder=DR_SHUTTERS)
    sa_ = 272.0 / 554.2
    x_, y_ = at(x0_, y0_, side, 150.0 + 6.5 * sa_, 3.0 + 1.3 * k_)
    put("Shutter_" + p["label"], AS + "SM_RollupDoor_A_002", x_, y_, z_ + 378.0, YAW[side], (sa_, 1.0, 290.0 / 333.1), folder=DR_SHUTTERS,
        mats=[roll_])
    _cheap(CULL_FAR)
    _count("closed stalls")


