"""Headless: MI_BackAlleys_WaterMeter, a child of the pack's MI_Water_Meter_Single_01. The pack tints the body bright blue (Tint 01 Color), and in the shade of an alley that reads as a
glowing toy at the foot of the wall. This turns it to old brass and leaves the rest of the pack's material as it is. The tint call returns False even when it takes: the log line reads the
value back, so trust that. If the instance is in the open level, close the editor first.

Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\create_meter_material_ue.py"""
import unreal

MATS = "/Game/ThirdPerson/BackAlleys/Materials"
NAME = "MI_BackAlleys_WaterMeter"
PACK = "/Game/Philippines_Markets/Materials/MI_Water_Meter_Single_01"
BRASS = unreal.LinearColor(0.20, 0.13, 0.05, 1.0)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary

path = MATS + "/" + NAME
mi = unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(NAME, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
mel.set_material_instance_parent(mi, unreal.load_asset(PACK))
ok = mel.set_material_instance_vector_parameter_value(mi, "Tint 01 Color", BRASS)
mel.update_material_instance(mi)
eal.save_loaded_asset(mi)
unreal.log_warning("[METERMAT] %s parent %s, tint set: %s, reads %s" % (NAME, mi.get_editor_property("parent").get_name(), ok, mel.get_material_instance_vector_parameter_value(mi, "Tint 01 Color")))
