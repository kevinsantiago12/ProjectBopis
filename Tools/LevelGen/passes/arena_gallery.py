# Pass `arena_gallery`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Arena only: the gallery deck, its posts, rails and stairs.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# --- Gallery deck (x15-27, y27-30, +4 m), posts, rails, stairs --------------------------------------------------------
GAL = "BackAlleys/Gallery"
# The rail. User 2026-11-04: "The gallert rail is the wrong model too" (it was SM_Wooden_part_03, a solid tapered plank).
# AsiaSlum's steel bar rail, the deck and stairs' own kit: local X -2.5..299.5 along the run, Y +-5, Z -3.9..174. 3 m long
# like the deck's modules; 1.78 m is a tall balcony's, so scaled to 1.05 m. You can see and shoot through it.
RAIL = AS + "SM_Rail_A_001"
RAIL_SX, RAIL_SZ, RAIL_X0, RAIL_Z0 = 300 / 302.0, 105 / 177.9, 2.5, 3.9
dk = L["deck"]
Xs, _ = ue(0, dk["y1"])            # south edge
Xn, _ = ue(0, dk["y0"])            # north edge
for i in range(int((dk["x1"] - dk["x0"]) / 3)):
    _, Ye = ue(dk["x0"] + 3 * (i + 1), 0)
    put("Gallery_Deck_%d" % i, AS + "SM_Floor_A_001", Xs, Ye, 380.0, 0, (1, 1, 1), folder=GAL)
    put("Gallery_Rail_S%d" % i, RAIL, Xs + 6, Ye - 300 + RAIL_X0 * RAIL_SX, 400.0 + RAIL_Z0 * RAIL_SZ, 90,
        (RAIL_SX, 1, RAIL_SZ), folder=GAL)
for i, lx in enumerate((dk["x0"] + 0.2, 19.0, 23.0, dk["x1"] - 0.2)):
    put("Gallery_Post_%d" % i, ME + "Favela/SM_Pillar_01", Xs + 21, ue(lx, 0)[1], 0.0, 0, (1, 1, 380 / 797.0), folder=GAL)
    items[-1]["phys"] = PHYS + "Concrete"          # its material is shared with the street lamps, which are Metal
_, Yw = ue(dk["x0"], 0)
_, Yeast = ue(dk["x1"], 0)
put("Gallery_Rail_W", RAIL, Xs + RAIL_X0 * RAIL_SX, Yw + 6, 400.0 + RAIL_Z0 * RAIL_SZ, 0, (RAIL_SX, 1, RAIL_SZ), folder=GAL)
put("Gallery_Rail_E", RAIL, Xs + RAIL_X0 * RAIL_SX, Yeast - 6, 400.0 + RAIL_Z0 * RAIL_SZ, 0, (RAIL_SX, 1, RAIL_SZ), folder=GAL)
# User 2026-11-04: "The stairs you are using is too steep and unnavigable, use another" "or find a way to make it less
# steep". One SM_Stair_A_001 (natively 4.5 m run, 2.15 m rise, 25 deg) stretched to 5 x 4 m was 39 deg with 31 cm risers.
# Now two flights in line, close to native scale: STAIR_RUN 7 m for the 4 m rise, about 30 deg, 15 cm risers on 27 cm
# treads. The lower flight's flat top is the landing between them, with two pillars under it. The stair runs STAIR_RUN
# north from the layout's top edge (the layout's own 5 m rect is left as it is); the layout's clear ahead allows it.
STAIR_RUN = 700.0
STAIR = (STAIR_RUN / 2 / 451.3, 300 / 306.0, 200 / 214.6)
for st in L["stairs"]:   # top step at the pivot, downhill along local +X = north (the feet face north)
    Xtop, _ = ue(0, st["y1"])
    _, Yx1 = ue(st["x1"], 0)
    put(st["id"], AS + "SM_Stair_A_001", Xtop, Yx1 - 3, 400.0, 0, STAIR, folder=GAL)
    put(st["id"] + "_Lower", AS + "SM_Stair_A_001", Xtop + STAIR_RUN / 2, Yx1 - 3, 200.0, 0, STAIR, folder=GAL)
    for k, inset in enumerate((30.0, 270.0)):
        put("%s_Post%d" % (st["id"], k), ME + "Favela/SM_Pillar_01", Xtop + STAIR_RUN / 2 + 25.0, Yx1 - inset, 0.0, 0,
            (1, 1, 190.0 / 797.0), folder=GAL)
        items[-1]["phys"] = PHYS + "Concrete"      # its material is shared with the street lamps, which are Metal


