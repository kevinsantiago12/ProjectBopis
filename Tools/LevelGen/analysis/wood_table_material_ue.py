"""Headless and read-only: the market pack's table material, what its parent offers, and its textures, to Saved/LevelGen/table_tex/. User 2026-11-06: "the table texture is a filthy texture".
Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\table_material_ue.py"""
import json
import os

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "table_tex")
os.makedirs(OUT, exist_ok=True)
L = unreal.MaterialEditingLibrary
mi = unreal.load_asset("/Game/Philippines_Markets/Materials/MI_Table_01")
base = mi.get_base_material()
out = {"parent": mi.get_editor_property("parent").get_path_name(), "base": base.get_path_name(), "phys": mi.get_physical_material().get_path_name() if mi.get_physical_material() else None, "tex": {}, "scalars": {}, "vectors": {}, "switches": []}
for n in L.get_texture_parameter_names(base):
    t = L.get_material_instance_texture_parameter_value(mi, n)
    out["tex"][str(n)] = t.get_path_name() + " %dx%d %s" % (t.blueprint_get_size_x(), t.blueprint_get_size_y(), str(t.get_editor_property("compression_settings")).split(".")[-1].split(":")[0]) if t else None
    if t:
        task = unreal.AssetExportTask()
        task.object = t
        task.filename = os.path.join(OUT, t.get_name() + ".png")
        task.automated = True
        task.prompt = False
        task.replace_identical = True
        unreal.Exporter.run_asset_export_task(task)
for n in L.get_scalar_parameter_names(base):
    out["scalars"][str(n)] = round(L.get_material_instance_scalar_parameter_value(mi, n), 3)
for n in L.get_vector_parameter_names(base):
    c = L.get_material_instance_vector_parameter_value(mi, n)
    out["vectors"][str(n)] = [round(c.r, 3), round(c.g, 3), round(c.b, 3)]
for n in L.get_static_switch_parameter_names(base):
    out["switches"].append(str(n))
json.dump(out, open(os.path.join(OUT, "material.json"), "w"), indent=1)
unreal.log_warning("[TABLE] " + json.dumps(out))
