# Pass `arena_doors`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Arena only: the spawn doors' end walls across the dead-end alleys.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# --- Spawn doors ------------------------------------------------------------------------------------------------------
# A Favela end wall across each dead end: a door tile centred on the door, a plain tile each side (4.5 m alley + 1.1 m
# into the blocks either side), a plain upper storey, bands and trims. A dark backer sits behind the door.
SP = "BackAlleys/SpawnDoors"
spawns = []
for d in L["doors"]:
    n = FACE[d["face"]]
    yaw, (rx, ry), (nx, ny) = YAW[n], RUN[n], NORMAL[n]
    cx, cy = ue(d["x"], d["y"])
    # The alley's side walls meet this wall 2.25 m either side of the door; its trims follow the same inside-corner
    # rule as the blocks: a north/south-facing end wall's trims stop 7 cm short of the side walls, an east/west one's
    # run 10 cm into them.
    reach = 218.0 if n in ("north", "south") else 235.0
    trim_cut = 337.5 - reach
    mats = [pick(FACE_MATS)]                                # one material per storey of the end wall
    mats.append(mats[0] if rnd.random() < SAME_AS_GROUND else pick(FACE_MATS))
    for s in (0, 1):
        mat = mats[s]
        for k, off in enumerate((-337.5, -112.5, 112.5)):
            kind = "door" if s == 0 and k == 1 else "plain"
            favela_tile("%s_S%d_%d" % (d["id"], s, k), kind, mat, cx + rx * off, cy + ry * off, s * 400.0, n, 1.0,
                        TILE_W, s == 1, SP, -trim_cut if k == 0 else 0.0, -trim_cut if k == 2 else 0.0)
    for s in (0, 1):   # the part of the end wall that shows: the 4.5 m alley between its side walls
        wall_runs.append({"start": (cx - rx * 225, cy - ry * 225), "len": 450.0, "side": n, "z": s * 400.0,
                          "name": "%s_S%d" % (d["id"], s), "widths": [225.0, 225.0]})
    bx, by = cx - rx * 112.5 - nx * 40, cy - ry * 112.5 - ny * 40
    X0, X1 = sorted((bx, bx + rx * 225 - nx * 20))
    Y0, Y1 = sorted((by, by + ry * 225 - ny * 20))
    put(d["id"] + "_Backer", CUBE, X0, Y0, 0.0, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, 3.0), folder=SP,
        mat="interior")
    spawns.append({"label": "Spawn_" + d["id"], "loc": [round(cx + nx * 160, 1), round(cy + ny * 160, 1), 100.0],
                   "yaw": FACING[n], "door": [cx, cy], "n": [nx, ny], "run": [rx, ry]})

