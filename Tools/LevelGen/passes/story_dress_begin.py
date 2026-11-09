# Pass `story_dress_begin` (story levels; 2026-11-09). Before the arena's dressing passes run on a story level, they're shown only
# the walls of the houses that take dressing (levels/*.py dress_house: the slum's, user 2026-11-09: "do passes on Sections 1 and
# 2. Dressings"). The compound's walls are the user's to handcraft. story_dress_end takes out anything the passes still put there.
_dress_start = len(items)


def _dress_ok(label):
    h = label.split("_")[0]
    h = h[:-1] if h.endswith("b") and h[:-1] in BLOCKS else h
    return h in BLOCKS and LEVEL.dress_house(BLOCKS[h])


wall_tiles[:] = [t for t in wall_tiles if _dress_ok(t["label"])]
wall_runs[:] = [r for r in wall_runs if _dress_ok(r["name"])]
ground_pieces[:] = [g for g in ground_pieces if _dress_ok(g[0])]
print("dressing scope: %d tiles, %d runs" % (len(wall_tiles), len(wall_runs)))

# The poles keep clear of the arena's spawns, wanderers and start. A story level has only its start so far (no fights placed):
# story_gameplay writes the real gameplay later.
gameplay = {"spawns": [], "wander": [], "player_start": list(ue(*LAYOUT_RAW["start"])) + [0.0]}
