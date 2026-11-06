# Headless and read-only: writes the poster images as PNGs, for RenderPosterBitsFlipbook.py to cut scraps from. Saves nothing in the project.
#   .\Tools\AnimAuthoring\RunUnreal.ps1 .\ArtSource\VFX\Paper\ExportPosterImages_ue.py
# Writes to Saved/BackAlleys/poster_images. Run it again, and the Blender script, if the images in /Game/Project_Bopis_Posters change.
import json
import os
import unreal

ROOT = unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_dir())
OUT = os.path.join(ROOT, 'Saved', 'BackAlleys', 'poster_images')
SKIP = ('Puting_Araw',)     # came in as a normal map, so the posters don't use it (Tools/LevelGen/LESSONS.md)
os.makedirs(OUT, exist_ok=True)
done = {}
for path in unreal.EditorAssetLibrary.list_assets('/Game/Project_Bopis_Posters', recursive=True, include_folder=False):
    name = path.split('.')[-1]
    if name in SKIP:
        continue
    tex = unreal.load_asset(path)
    if not isinstance(tex, unreal.Texture2D):
        continue
    t = unreal.AssetExportTask()
    t.object = tex
    t.filename = os.path.join(OUT, name + '.png')
    t.exporter = unreal.TextureExporterPNG()
    t.automated = True
    t.prompt = False
    t.replace_identical = True
    done[name] = bool(unreal.Exporter.run_asset_export_task(t))
with open(os.path.join(OUT, 'exported.json'), 'w', encoding='utf-8') as f:
    json.dump(done, f, indent=1)
