"""Headless and read-only: the Yakohama road-dirt and leak decals' textures, to Saved/LevelGen/ground_tex/ (ground_export_ue.py can't reach them: they're plain materials).
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\ground_export2_ue.py"""
import os

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "ground_tex")
D = "/Game/Megapack/Textures/Yakohama/Decal/"
for name in ("T_RoadDirt_01_BC", "T_RoadDirt_01_O", "T_RoadDirt_02_BC", "T_RoadDirt_02_O", "T_Leakage_01_BC", "T_Leakage_01_O", "T_Leakage_02_BC", "T_Leakage_02_O"):
    t = unreal.load_asset(D + name)
    task = unreal.AssetExportTask()
    task.object = t
    task.filename = os.path.join(OUT, name + ".png")
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    unreal.log_warning("[GROUND] %s %dx%d %s" % (name, t.blueprint_get_size_x(), t.blueprint_get_size_y(), unreal.Exporter.run_asset_export_task(task)))
