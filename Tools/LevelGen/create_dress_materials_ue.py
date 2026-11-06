"""Headless, new assets only: imports the textures make_dress_textures.py drew and makes a material instance of each, for the
building dressing (user 2026-11-04: "ply patches", "door steps and vent blocks too").
- MI_BackAlleys_VentBlock_Diamond / _Slots: concrete, inherited from M_BackAlleys_HollowBlocks.
- MI_BackAlleys_Ply_Natural / _Weathered / _GreenPaint: Wood surface, so bullet impacts match.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_dress_materials_ue.py"""
import os

import unreal

SRC = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "import", "dress")
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
MATS = "/Game/ThirdPerson/BackAlleys/Materials"
WOOD = "/Game/ImpactsVFXVol1/Materials/Physical_Materials/Wood"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary


def say(msg):
    unreal.log_warning("[DRESSMAT] " + msg)


def import_tex(name, normal):
    path = TEX + "/" + name
    if eal.does_asset_exist(path):
        say("%s exists, kept" % name)
        return unreal.load_asset(path)
    task = unreal.AssetImportTask()
    task.filename = os.path.join(SRC, name + ".png")
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
    eal.save_loaded_asset(tex)
    say("%s imported" % name)
    return tex


def make(name, bc, nm, rough, phys=None):
    if eal.does_asset_exist(MATS + "/" + name):
        say("%s exists, kept" % name)
        return
    mi = tools.create_asset(name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    mel.set_material_instance_texture_parameter_value(mi, "BaseColor", bc)
    mel.set_material_instance_texture_parameter_value(mi, "Normal", nm)
    mel.set_material_instance_scalar_parameter_value(mi, "Roughness", rough)
    if phys:
        mi.set_editor_property("phys_material", unreal.load_asset(phys))
        mi.set_editor_property("override_phys_material", True)   # without it the engine uses the parent's
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say("%s saved" % name)


parent = unreal.load_asset(MATS + "/M_BackAlleys_HollowBlocks")
for kind in ("Diamond", "Slots"):
    make("MI_BackAlleys_VentBlock_" + kind, import_tex("T_BackAlleys_VentBlock_%s_BC" % kind, False),
         import_tex("T_BackAlleys_VentBlock_%s_N" % kind, True), 0.9)
ply_n = import_tex("T_BackAlleys_Plywood_N", True)
for kind in ("Natural", "Weathered", "GreenPaint"):
    make("MI_BackAlleys_Ply_" + kind, import_tex("T_BackAlleys_Ply_%s_BC" % kind, False), ply_n, 0.85, WOOD)
