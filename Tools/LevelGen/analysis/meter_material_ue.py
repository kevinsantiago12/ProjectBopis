"""Headless and read-only: the water meter's material: parent, parameters, textures and whether its surface is metal.
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\meter_material_ue.py"""
import os

import unreal

L = unreal.MaterialEditingLibrary
m = unreal.load_asset(unreal.StaticMesh.cast(unreal.load_asset("/Game/Philippines_Markets/Props/Water_Meters_Set_01/SM_Water_Meter_Single_01")).static_materials[0].material_interface.get_path_name().split(".")[0])
unreal.log_warning("[METER] %s" % m.get_path_name())
base = m
while isinstance(base, unreal.MaterialInstance):
    unreal.log_warning("[METER] parent %s" % base.get_editor_property("parent").get_path_name())
    base = base.get_editor_property("parent")
unreal.log_warning("[METER] scalars %s" % [(str(n), round(L.get_material_instance_scalar_parameter_value(m, n), 3)) for n in L.get_scalar_parameter_names(m)])
unreal.log_warning("[METER] vectors %s" % [(str(n), str(L.get_material_instance_vector_parameter_value(m, n))) for n in L.get_vector_parameter_names(m)])
tex = [(str(n), L.get_material_instance_texture_parameter_value(m, n)) for n in L.get_texture_parameter_names(m)]
unreal.log_warning("[METER] textures %s" % [(n, t.get_path_name() if t else None) for n, t in tex])
OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "poles")
for n, t in tex:
    if t:
        task = unreal.AssetExportTask()
        task.object = t
        task.filename = os.path.join(OUT, "meter_" + t.get_name() + ".png")
        task.automated = True
        task.prompt = False
        task.replace_identical = True
        unreal.Exporter.run_asset_export_task(task)
