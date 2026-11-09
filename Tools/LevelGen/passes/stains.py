# Pass `stains`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Drip decals on whole wall runs.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# Stains (user: "I want stain decals next"; then "The decals you are currently using is meant to be stretched to the
# entire wall"). Favela's decal masks (Tools/LevelGen/analysis/inspect_decals_ue.py) are whole-wall layers:
#   T_decal_07 (MI_Decal_Dirt_06 / _08): drip streaks running down from a hard top edge at ~24% of the height.
#   T_decal_08 (MI_Decal_Dirt_07): rising damp, solid at the bottom, fading out by ~45% of the height.
#   T_decal_02 (MI_Decal_02/04-08): a rough-edged full-wall colour wash - left out, it would recolour the face.
# Each storey of each wall run gets drips whose top edge sits under the band (z +300); street floors also get rising
# damp to ~1.2 m. Decals are 23% wider than their stretch of wall so neighbours overlap and the ragged mask sides fall
# past the run ends. A DecalActor's DecalSize is an extent (128, 256, 256): scale = size / 512 (y height, z width,
# roll 90); 3 cm deep each way.
DC = "BackAlleys/Decals"   # also set by dressing_old, which a level may not run
DRIPS = [(FM + "Decals/MI_Decal_Dirt_08", 1.0)]   # user: "use decal dirt 8" (the darker drips; was Dirt_06)
DAMP = FM + "Decals/MI_Decal_Dirt_07"
# Calibrated on the user's hand-placed decal (2026-11-03, "fix the alignment, first one is yours, second one is mine"):
# 497.5 cm tall, 1.23 x the wall's width, the mask's hard top edge at +292 - tucked behind the trim's lower half - and
# the streaks reaching the floor.
DRIP_H, DRIP_EDGE, DRIP_EDGE_Z = 380.0, 0.24, 292.0   # box height (was 500, user: "shorten the length more"); mask edge (fraction from the top); edge height
DRIP_H_SINGLE = 230.0                                  # box height when the drips cover one tile only (was 300)
DRIP_EDGE_BAND = 304.0                                 # edge height behind a protruding band, whose underside is at +300
STAIN_WIDEN = 1.12                                     # decal width / stretch: the mask's ragged sides (5% each) end at the face edge
DAMP_H = 220.0
P_DRIPS, P_DAMP = 0.35, 0.0  # P_DRIPS: chance per wall run (face + storey);  # user: "not all of them need the dirt decal"; rising damp off ("only use the dirt decal")
# Which wall tiles get drips: each tile with P_DRIPS; neighbouring picked tiles share one decal stretched across up to
# STAIN_SPAN of them (user 2026-11-03: "the using decal on adjacent walls, stretch the decal accross up to 3 walls
# instead", then "its actually up to 4 walls, the ammount of walls covered should determine the length"), so no two
# drip decals sit side by side on the same run. The box height grows with the tiles covered: DRIP_H_SINGLE for one,
# DRIP_H for STAIN_SPAN, evenly between.
STAIN_SPAN = 4   # user: "its actually up to 4 walls"


def drips_on(r):
    """Drips across one wall run, in groups of at most STAIN_SPAN tiles. Returns how many decals."""
    full = r["widths"]
    (nx, ny) = NORMAL[r["side"]]
    yaw = math.degrees(math.atan2(-ny, -nx))   # projects into the wall
    n = len(full)
    groups = math.ceil(n / STAIN_SPAN)
    bounds = [round(g * n / groups) for g in range(groups + 1)]
    edges = [0.0]
    for w in full:
        edges.append(edges[-1] + w)
    for g in range(groups):
        i, j = bounds[g], bounds[g + 1] - 1         # tiles i..j
        a, b = edges[i], edges[j + 1]
        x, y = at(r["start"][0], r["start"][1], r["side"], (a + b) / 2, 2)
        hgt = DRIP_H_SINGLE + (DRIP_H - DRIP_H_SINGLE) * (j - i) / (STAIN_SPAN - 1)
        top = r["z"] + DRIP_EDGE_Z + DRIP_EDGE * hgt     # puts the mask's edge behind the trim
        put("Drips_%s_%d" % (r["name"], g), pick(DRIPS), x, y, top - hgt / 2, yaw,
            (0.03, hgt / 512.0, (b - a) * STAIN_WIDEN / 512.0), folder=DC, roll=90, decal=True)
    return groups


if STAINS:
    n_st = 0
    for r in wall_runs:
        # Whole faces only (user: "keep the stains consistent with the face and material, no half wall decals" ... "half
        # block i mean" ... "you are leaving a section undecaled" - pointing at a bare half tile): a run (one face, one
        # storey, one material) gets drips across every tile, the half tile included, or none. Decal edges sit on tile
        # edges, so no block is half covered. Longer runs split into equal groups of at most STAIN_SPAN tiles.
        if rnd.random() < P_DRIPS:
            n_st += drips_on(r)
    print("stains:", n_st, "decals over", len(wall_runs), "wall runs")
