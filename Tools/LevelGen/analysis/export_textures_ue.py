"""Read-only, headless: exports wall-like base colour textures from the art packs to PNG, so candidates for a material
can be looked at side by side (make_contact_sheet.ps1). Writes Saved/LevelGen/tex/<name>.png.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\export_textures_ue.py"""
import os
import re

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "tex")
os.makedirs(OUT, exist_ok=True)
WANT = re.compile(r"(wall|brick|block|concrete|plaster|stucco|cement)", re.I)
SKIP = re.compile(r"(Decal|Cornet|Inner|Chopping|Fence|Grime)", re.I)
ar = unreal.AssetRegistryHelpers.get_asset_registry()
n = 0
for pack in ("/Game/Megapack/Textures", "/Game/AsiaSlum/Textures"):
    for ad in ar.get_assets_by_path(pack, recursive=True):
        name = str(ad.asset_name)
        if str(ad.asset_class_path.asset_name) != "Texture2D" or not WANT.search(name) or SKIP.search(name):
            continue
        if not (name.endswith("_BC") or name.endswith("_D")):
            continue
        task = unreal.AssetExportTask()
        task.object = unreal.load_asset(str(ad.package_name))
        task.filename = os.path.join(OUT, name + ".png")
        task.automated = True
        task.prompt = False
        task.replace_identical = True
        ok = unreal.Exporter.run_asset_export_task(task)
        n += 1
        unreal.log_warning("[TEX] %s %s" % (name, "ok" if ok else "FAILED"))
unreal.log_warning("[TEX] exported %d" % n)
