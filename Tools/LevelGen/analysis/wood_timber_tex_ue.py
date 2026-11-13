"""Read-only, headless: exports the packs' timber textures to PNG with their sizes and their normal-map partners, to pick one for the
plywood walls' studs (user 2026-11-13: of the studs, "Give them timber"). Writes Saved/LevelGen/tex/timber_*.png and timber_info.json.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\timber_tex_ue.py"""
import json
import os
import traceback

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "tex")
os.makedirs(OUT, exist_ok=True)
CANDIDATES = ["/Game/Megapack/Textures/MiddleEast/T_wooden_beam_01_BC", "/Game/Megapack/Textures/MiddleEast/T_wood_01_BC",
              "/Game/AsiaSlum/Textures/T_WoodFrame_A_001_D", "/Game/AsiaSlum/Textures/T_Wood_A_001_D",
              "/Game/Megapack/Textures/Favela/T_wooden_part_BC"]
NORMAL_SUFFIX = {"_BC": ["_N", "_NM", "_Normal"], "_D": ["_N", "_NM", "_Normal"]}
eal = unreal.EditorAssetLibrary
info = {}


def say(msg):
    unreal.log_warning("[TIMBER] " + msg)


try:
    for p in CANDIDATES:
        t = unreal.load_asset(p)
        if not t:
            say("missing " + p)
            continue
        name = p.rsplit("/", 1)[1]
        d = {"size": [t.blueprint_get_size_x(), t.blueprint_get_size_y()], "normal": None}
        for suf, alts in NORMAL_SUFFIX.items():
            if p.endswith(suf):
                for a in alts:
                    q = p[: -len(suf)] + a
                    if eal.does_asset_exist(q):
                        d["normal"] = q
                        break
        task = unreal.AssetExportTask()
        task.object = t
        task.filename = os.path.join(OUT, "timber_" + name + ".png")
        task.automated = True
        task.prompt = False
        task.replace_identical = True
        d["exported"] = bool(unreal.Exporter.run_asset_export_task(task))
        info[name] = d
    json.dump(info, open(os.path.join(OUT, "timber_info.json"), "w"), indent=1)
    say("done")
except Exception:
    say("ERROR " + traceback.format_exc())
