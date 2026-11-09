"""Level data: Lvl_BackAlleys_Arena, the all-alley arena (Design Document/Arena_Slums_Layout.json, from the "Arena Level
Design: Slums" session; user: "remove the court, make it exclusively alleys"; "remove the grenade launcher").

gen_level.py reads this file, then runs PASSES (Tools/LevelGen/passes/<name>.py) in order in one shared namespace, so a
pass sees everything the passes before it defined. Everything the arena needs that another level wouldn't is named here
or in the arena_* passes. The arena's plan must come out identical whenever the passes change (2026-11-08 rule):
compare with analysis/plan_identical.py before placing anything."""

NAME = "backalleys_arena"
MAP = "/Game/ThirdPerson/Lvl_BackAlleys_Arena"
LAYOUT = "Design Document/Arena_Slums_Layout.json"
OUT = "Saved/BackAlleys"
PREFIX = "plan3_"                 # plan3_<n>.json chunks and plan3_gameplay.json
ORIGIN = (27.0, 24.0)             # the layout point at the world origin: X = (24 - ly) * 100, Y = (lx - 27) * 100
FOLDER_ROOT = "BackAlleys"        # World Outliner folder every piece goes under

# Standing rule (user 2026-11-03): "forget all the dressings and, just make the building block outs. No other objects in
# the level besides building blockouts as a rule." Asked what else stays: the gameplay actors and the gallery deck +
# stairs. So cover (stand-ins, kiosk, barriers, drums), pickups, dressing and decals are off. The code for them stays
# behind these switches; turn one on only when the user asks for it.
SWITCHES = {
    "COVER": False,
    "PICKUPS": False,
    "DRESSING": False,
    "TERRACES": True,    # user 2026-11-03: "Yes, build them" - covered roof terraces on the 1-storey blocks
    "STAINS": True,      # user 2026-11-03: "I want stain decals next"; "forget the decals completely"; then "actually,
                         # bring it back but use decal dirt 8" - on, with MI_Decal_Dirt_08
}

# Blocks the passes treat specially (names from the layout).
NO_SPLIT = ("B2", "B10", "B11")   # not split into houses: the shop row, the 1.5 m stub, the gallery-deck block
NO_BALCONY = ("B2", "B11")        # no balcony or wide terrace: the shop fronts, the gallery deck
THIN_IDS = ("B10",)               # thin walls whatever their size: the stub
FIXED = ()                        # besides NO_SPLIT, the deck, stairs and spawn doors (houses.py _fixed)
SPECIAL = {("B2", "south", 0): ["SM_Shop_A_001", "SM_HouseWindow_A_001", "SM_Shop_A_001", "SM_HouseWallDoorFrmae_A_002"]}
DECK_FACE = ("B11", "south", 1)   # doors and windows onto the gallery deck, alternating
BALCONIES, WIDE_TERRACES, SHACKS = 6, 4, 4

PASSES = ["base", "houses", "walls", "terraces", "roofs", "arena_doors", "arena_gallery", "arena_cover", "dressing_old",
          "stains", "arena_gameplay", "floors", "finish", "awnings", "building_dressing", "street", "low_wires", "stalls",
          "posters", "chain_wires", "poles", "graffiti", "ground", "dirt", "litter", "props", "arena_report"]
AFTER_WRITE = ["arena_check"]     # run once the plan is written
