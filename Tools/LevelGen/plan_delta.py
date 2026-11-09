"""Offline: what has to change in the open level to match the plan, given the plan it was last placed from. A generator change can move a few pieces anywhere in the level,
and clearing whole folders loses what was fine. Writes Saved/BackAlleys/plan_delta_remove_<n>.json and plan_delta_place_<n>.json for apply_delta_ue.py.

Usage (from the project root): python Tools/LevelGen/plan_delta.py <folder holding the plan the level was placed from>
Keep a copy of Saved/BackAlleys/plan3_*.json from before you regenerate. There is no way to get it back afterwards."""
import glob
import json
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
NEW = os.path.join(ROOT, "Saved", "BackAlleys")
KEYS = ("asset", "loc", "rot", "scale", "mats", "mat", "nocoll", "coll", "phys", "vol", "noshadow", "nonav", "physics", "cap", "seed", "weld_to", "draw", "decal", "light")


def load(d):
    out = {}
    for f in sorted(glob.glob(os.path.join(d, "plan3_[0-9]*.json"))):
        for p in json.load(open(f, encoding="utf-8")):
            out[(p["folder"], p["label"])] = p
    return out


old, new = load(sys.argv[1]), load(NEW)
changed = [k for k in old if k in new and any(old[k].get(a) != new[k].get(a) for a in KEYS)]
gone = [k for k in old if k not in new]
added = [k for k in new if k not in old]
# A welded piece (weld_to, a bucket's lid) goes with its parent: removing the parent leaves it detached in the level, so it's re-placed and re-welded too.
moved = set(changed) | set(gone) | set(added)
changed += [k for k in new if k in old and k not in moved and new[k].get("weld_to") and (k[0], new[k]["weld_to"]) in moved]
remove = sorted(set(changed) | set(gone))
place = [new[k] for k in sorted(set(changed) | set(added))]
# In chunks, as the plan is: the bridge's read_file stops at 80 KB.
for f in glob.glob(os.path.join(NEW, "plan_delta_*.json")):
    os.remove(f)
chunks_r = [remove[i:i + 400] for i in range(0, len(remove), 400)]
chunks_p = [place[i:i + 120] for i in range(0, len(place), 120)]
for i, c in enumerate(chunks_r):
    json.dump([list(k) for k in c], open(os.path.join(NEW, "plan_delta_remove_%d.json" % i), "w"), separators=(",", ":"))
for i, c in enumerate(chunks_p):
    json.dump(c, open(os.path.join(NEW, "plan_delta_place_%d.json" % i), "w"), separators=(",", ":"))
print("chunks: remove %d, place %d" % (len(chunks_r), len(chunks_p)))
tally = {}
for k in remove:
    tally.setdefault(k[0].split("/")[-1], [0, 0])[0] += 1
for p in place:
    tally.setdefault(p["folder"].split("/")[-1], [0, 0])[1] += 1
print("old %d, new %d, unchanged %d" % (len(old), len(new), len(old) - len(remove)))
print("folder: remove, place")
for k in sorted(tally):
    print("  %s: %d, %d" % (k, tally[k][0], tally[k][1]))
print("new folders:", sorted({p["folder"] for p in place} - {k[0] for k in old}))
