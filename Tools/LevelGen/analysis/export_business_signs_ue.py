"""Headless, read-only: exports the user's business sign textures (/Game/Project_Bopis_Local_Business_Signs) to PNG in
Saved/LevelGen/import/business_signs, and logs each one's size and settings, so they can be looked at as imported. The assets are not changed.
Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\export_business_signs_ue.py"""
import os

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "import", "business_signs")
os.makedirs(OUT, exist_ok=True)
eal = unreal.EditorAssetLibrary
for path in sorted(eal.list_assets("/Game/Project_Bopis_Local_Business_Signs", recursive=True, include_folder=False)):
    t = unreal.load_asset(path)
    if not isinstance(t, unreal.Texture2D):
        continue
    task = unreal.AssetExportTask()
    task.object = t
    task.filename = os.path.join(OUT, t.get_name() + ".png")
    task.automated = True
    task.replace_identical = True
    task.prompt = False
    task.exporter = unreal.TextureExporterPNG()
    ok = unreal.Exporter.run_asset_export_task(task)
    unreal.log_warning("[BIZSIGN] %s %dx%d srgb %s comp %s addr %s/%s lod %s export %s" % (
        path, t.blueprint_get_size_x(), t.blueprint_get_size_y(), t.get_editor_property("srgb"), t.get_editor_property("compression_settings"),
        t.get_editor_property("address_x"), t.get_editor_property("address_y"), t.get_editor_property("lod_group"), ok))
