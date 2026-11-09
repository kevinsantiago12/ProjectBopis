"""Headless and read-only: the Megapack's remaining ground decals' textures, to Saved/LevelGen/ground_tex/. Paths on the command line's file, GROUND_PATHS below.
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\ground_export3_ue.py"""
import os

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "ground_tex")
GROUND_PATHS = [p.strip() for p in open(os.path.join(OUT, "paths.txt")) if p.strip()]
for path in GROUND_PATHS:
    t = unreal.load_asset(path)
    name = path.split("/")[-1]
    task = unreal.AssetExportTask()
    task.object = t
    task.filename = os.path.join(OUT, "x_" + name + ".png")
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    unreal.log_warning("[GROUND] %s %dx%d %s" % (path, t.blueprint_get_size_x(), t.blueprint_get_size_y(), unreal.Exporter.run_asset_export_task(task)))
