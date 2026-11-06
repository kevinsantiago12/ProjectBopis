"""Headless and read-only: exports the user's graffiti from /Game/Project_Bopis_Graffiti_Decals to Saved/LevelGen/graffiti_user/, with their settings, so they can be looked at before any goes on a wall.
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\graffiti_export_ue.py"""
import os

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "graffiti_user")
os.makedirs(OUT, exist_ok=True)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
for ad in ar.get_assets_by_path("/Game/Project_Bopis_Graffiti_Decals", recursive=True):
    name = str(ad.asset_name)
    t = unreal.load_asset(str(ad.package_name))
    if not isinstance(t, unreal.Texture2D):
        unreal.log_warning("[GRAF] %s is a %s" % (ad.package_name, t.get_class().get_name()))
        continue
    task = unreal.AssetExportTask()
    task.object = t
    task.filename = os.path.join(OUT, name + ".png")
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    ok = unreal.Exporter.run_asset_export_task(task)
    unreal.log_warning("[GRAF] %s %dx%d comp %s srgb %s mips %s alpha %s lod %s export %s" % (ad.package_name, t.blueprint_get_size_x(), t.blueprint_get_size_y(),
                       str(t.get_editor_property("compression_settings")).split(".")[-1].split(":")[0], t.get_editor_property("srgb"),
                       str(t.get_editor_property("mip_gen_settings")).split(".")[-1].split(":")[0], t.has_alpha_channel() if hasattr(t, "has_alpha_channel") else "?",
                       str(t.get_editor_property("lod_group")).split(".")[-1].split(":")[0], ok))
