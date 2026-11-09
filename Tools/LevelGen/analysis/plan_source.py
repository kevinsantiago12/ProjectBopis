"""Which plan an offline check reads (2026-11-08, levels as data): the arena's by default, or a level's, named on the command
line (python Tools/LevelGen/analysis/check_overlaps.py linear_slums). A level's folders are mapped back to BackAlleys/<kind>, the
names the checks and the passes use, so every rule is tested the same way on any level."""
import importlib.util
import os
import sys

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))


def level_name(argv=None):
    argv = sys.argv[1:] if argv is None else argv
    names = [a for a in argv if not a.startswith("-")]
    return names[0] if names else "backalleys_arena"


def load_level(name=None):
    name = name or level_name()
    path = os.path.join(ROOT, "Tools", "LevelGen", "levels", name + ".py")
    spec = importlib.util.spec_from_file_location("level_" + name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def plan_glob(name=None):
    lv = load_level(name)
    return os.path.join(ROOT, *lv.OUT.split("/"), lv.PREFIX + "[0-9]*.json")


def layout_path(name=None):
    """The layout the passes worked from: a level with its own setup writes it beside its plan (<prefix>layout.json)."""
    lv = load_level(name)
    own = os.path.join(ROOT, *lv.OUT.split("/"), lv.PREFIX + "layout.json")
    return own if hasattr(lv, "setup") and os.path.exists(own) else os.path.join(ROOT, lv.LAYOUT)


def normalise(items, name=None):
    """A level's folder root back to BackAlleys, in place."""
    root = getattr(load_level(name), "FOLDER_ROOT", "BackAlleys")
    if root != "BackAlleys":
        for p in items:
            if p["folder"] == root or p["folder"].startswith(root + "/"):
                p["folder"] = "BackAlleys" + p["folder"][len(root):]
    return items
