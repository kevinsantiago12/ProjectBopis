"""Headless: imports the five back-alley door textures (user 2026-11-03: "Heres a zip of 5 backalley "plane" doors",
"get them in the game") and makes one material instance per door. New assets only, so the open editor can stay open.

Source: Saved/LevelGen/import/doors_zip/filipino-backalley-doors-1x2/ (the user's zip, extracted as is): per door a
colour map and a tangent-space normal map in DirectX convention (Unreal's), 1024 x 2048 (the door slot's 1:2).
The instances parent M_BackAlleys_HollowBlocks (our plain BaseColor / Normal / Roughness material) and set the surface type
per door (wood or metal), so bullet impacts match.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_doors_ue.py"""
import os

import unreal

SRC = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "import", "doors_zip", "filipino-backalley-doors-1x2")
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
MATS = "/Game/ThirdPerson/BackAlleys/Materials"
PHYS = "/Game/ImpactsVFXVol1/Materials/Physical_Materials/"
DOORS = [("01-rough-timber", "RoughTimber", "Wood", 0.85), ("02-green-plywood", "GreenPlywood", "Wood", 0.8),
         ("03-blue-plywood", "BluePlywood", "Wood", 0.8), ("04-corrugated-metal", "CorrugatedMetal", "Metal", 0.55),
         ("05-painted-steel", "PaintedSteel", "Metal", 0.6)]
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary


def say(msg):
    unreal.log_warning("[DOOR] " + msg)


def import_tex(src_file, name, normal):
    path = TEX + "/" + name
    if eal.does_asset_exist(path):
        say("%s exists, kept" % name)
        return unreal.load_asset(path)
    task = unreal.AssetImportTask()
    task.filename = os.path.join(SRC, src_file)
    task.destination_path = TEX
    task.destination_name = name
    task.automated = True
    task.save = False
    task.replace_existing = False
    tools.import_asset_tasks([task])
    tex = unreal.load_asset(path)
    if normal:
        tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_NORMALMAP)
        tex.set_editor_property("srgb", False)
    tex.set_editor_property("max_texture_size", 1024)   # 512 x 1024 on screen: plenty for a door, kinder to the Deck
    eal.save_loaded_asset(tex)
    say("%s imported" % name)
    return tex


parent = unreal.load_asset(MATS + "/M_BackAlleys_HollowBlocks")
for src, key, phys, rough in DOORS:
    bc = import_tex(src + "-color.png", "T_BackAlleys_Door_%s_BC" % key, False)
    nm = import_tex(src + "-normal-directx.png", "T_BackAlleys_Door_%s_N" % key, True)
    name = "MI_BackAlleys_Door_" + key
    if eal.does_asset_exist(MATS + "/" + name):
        say("%s exists, kept" % name)
        continue
    mi = tools.create_asset(name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    mel.set_material_instance_texture_parameter_value(mi, "BaseColor", bc)
    mel.set_material_instance_texture_parameter_value(mi, "Normal", nm)
    mel.set_material_instance_scalar_parameter_value(mi, "Roughness", rough)
    mi.set_editor_property("phys_material", unreal.load_asset(PHYS + phys))
    mi.set_editor_property("override_phys_material", True)   # without it the engine uses the parent's (GetPhysicalMaterial)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say("%s saved (%s, roughness %.2f)" % (name, phys, rough))
