"""Level generator: a level's data (Tools/LevelGen/levels/<name>.py) and its layout file in, a placement plan out.

Usage (from the project root):
    python Tools/LevelGen/gen_level.py [level]          level: a file in Tools/LevelGen/levels, default backalleys_arena
    python Tools/LevelGen/gen_level.py layout.json      the arena's passes on another layout file (as before the split)
See README.md.

Split on 2026-11-08 out of the one-file arena generator (6,150 lines):
- kit/core.py: the stateless kit (asset roots, side tables, vector maths, shuffle bag, frame, plan writer);
- passes/*.py: the generator's passes, unchanged, each run in one shared namespace in the order the level lists, so a
  pass sees the names the passes before it defined (as when they were one file);
- levels/*.py: per-level data: layout, output, origin, switches, which passes run.
Rule: Lvl_BackAlleys_Arena's plan must come out identical after any change here (analysis/plan_identical.py)."""
import importlib.util
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", ".."))
sys.path.insert(0, HERE)
from kit import core  # noqa: E402


def load_level(name):
    path = os.path.join(HERE, "levels", name + ".py")
    spec = importlib.util.spec_from_file_location("level_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_arg = sys.argv[1] if len(sys.argv) > 1 else "backalleys_arena"
if _arg.endswith(".json"):                      # a layout file: the arena's passes on it
    LEVEL = load_level("backalleys_arena")
    SRC = _arg
else:
    LEVEL = load_level(_arg)
    SRC = os.path.join(ROOT, LEVEL.LAYOUT)
OUT = os.path.join(ROOT, *LEVEL.OUT.split("/")) + os.sep
os.makedirs(OUT, exist_ok=True)

NS = {"__name__": "gen_level_passes", "__builtins__": __builtins__,
      "json": json, "math": math, "os": os, "random": random, "sys": sys,
      "ROOT": ROOT, "SRC": SRC, "OUT": OUT, "LEVEL": LEVEL}
NS.update({k: v for k, v in vars(core).items() if not k.startswith("__") and k not in ("json", "math", "os")})
NS["ue"], NS["lay"] = core.frame(*LEVEL.ORIGIN)
L = json.load(open(SRC, encoding=getattr(LEVEL, "LAYOUT_ENCODING", None)))   # the arena's reads as before (locale)
NS["L"] = L
if "arena" in L:
    NS["W"], NS["H"] = L["arena"]
NS["W0"] = NS["H0"] = 0.0                       # the low edges of the bounds the passes keep pieces inside
NS["rnd"] = random.Random(11)
NS["items"] = []
NS.update(LEVEL.SWITCHES)
if hasattr(LEVEL, "setup"):
    LEVEL.setup(NS)                              # a level's own names (bounds, ground heights, entered buildings, ...)


def run(name):
    path = os.path.join(HERE, "passes", name + ".py")
    exec(compile(open(path, encoding="utf-8").read(), path, "exec"), NS)


for _name in LEVEL.PASSES:
    run(_name)

items = NS["items"]
for p in items:
    p.pop("band", None)
_root = getattr(LEVEL, "FOLDER_ROOT", "BackAlleys")
if _root != "BackAlleys":                       # the passes name their folders BackAlleys/<kind>
    for p in items:
        if p["folder"] == "BackAlleys" or p["folder"].startswith("BackAlleys/"):
            p["folder"] = _root + p["folder"][len("BackAlleys"):]
_n = core.write_plan(OUT, LEVEL.PREFIX, items, NS.get("gameplay", {}))
if hasattr(LEVEL, "setup"):                      # what the passes took as the layout (the checks read it): blocks, deck, ...
    json.dump(NS["L"], open(OUT + LEVEL.PREFIX + "layout.json", "w"), separators=(",", ":"))
from collections import Counter  # noqa: E402
print(len(items), "items in", _n, "chunks;", dict(Counter(p["folder"] for p in items)))
print("max chunk", max(os.path.getsize(OUT + LEVEL.PREFIX + "%d.json" % i) for i in range(_n)), "bytes; laundry",
      NS.get("lines"))
print("exposed:", {k: sorted(v) for k, v in NS.get("exposed_sides", {}).items()})
for _name in getattr(LEVEL, "AFTER_WRITE", ()):
    run(_name)
