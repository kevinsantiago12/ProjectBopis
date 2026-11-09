# Pass `arena_check`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Arena only: every open cell on the arena edge must sit behind a spawn door.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# Check: open cells along the arena edge must be inside a door's end wall (door point +-2.25 m).
open_edge = []
for k in range(int(W / 1.5)):
    for ly_in, ly_edge in ((0.75, 0), (H - 0.75, H)):
        lx = (k + 0.5) * 1.5
        if not solid(lx, ly_in, 0) and not any(abs(d["x"] - lx) <= 2.25 and d["y"] == ly_edge for d in L["doors"]):
            open_edge.append((lx, ly_edge))
for k in range(int(H / 1.5)):
    for lx_in, lx_edge in ((0.75, 0), (W - 0.75, W)):
        ly = (k + 0.5) * 1.5
        if not solid(lx_in, ly, 0) and not any(abs(d["y"] - ly) <= 2.25 and d["x"] == lx_edge for d in L["doors"]):
            open_edge.append((lx_edge, ly))
print("open edge cells without a door:", open_edge)
