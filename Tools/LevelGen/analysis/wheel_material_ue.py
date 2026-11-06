"""Headless and read-only: the tyre's and the poles' textures: sizes, and exports their base colours to Saved/LevelGen/poles/. Their materials (M_wall_01) have no tint to turn.
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\wheel_material_ue.py"""
import os

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "poles")
os.makedirs(OUT, exist_ok=True)
for n in ("T_wheel_01_BC", "T_wheel_01_ORM", "T_Electric_Pole_01_BC", "T_Electric_Pole_02_BC"):
    t = unreal.load_asset("/Game/Megapack/Textures/MiddleEast/" + n)
    unreal.log_warning("[TYRE] %s %dx%d %s" % (n, t.blueprint_get_size_x(), t.blueprint_get_size_y(), t.get_editor_property("compression_settings")))
    task = unreal.AssetExportTask()
    task.object = t
    task.filename = os.path.join(OUT, n + ".png")
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    unreal.log_warning("[TYRE]   export %s" % unreal.Exporter.run_asset_export_task(task))
