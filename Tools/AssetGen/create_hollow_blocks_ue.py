"""Headless: imports the hollow-block (CHB) wall texture and makes MI_BackAlleys_HollowBlocks. New assets only.

User 2026-11-03: the Favela red brick (T_Bricks_01_BC) was exported, turned into hollow blocks by GPT ("Here is the zip
for the hollow blocks"), and repaired by repair_chb_texture.ps1 (GPT's mask had lost about a third of the joints). The
layout and UVs are the brick's, so it maps onto the Favela wall tiles' UV0 exactly as T_Bricks_01_BC did.

Sources: Saved/AssetGen/import/hollow_blocks_fixed/T_HollowBlocks_01_BC.png and _N.png (DirectX), 2048 x 2048.
- T_BackAlleys_HollowBlocks_BC (sRGB colour) and _N (normal map), kept at 2048: walls are the biggest surface on screen.
- MI_BackAlleys_HollowBlocks: an instance of M_BackAlleys_HollowBlocks (plain BaseColor / Normal / Roughness on UV0, made
  by Tools/LevelGen/create_hollow_master_ue.py), roughness 0.9, the project's Concrete surface type.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\AssetGen\\create_hollow_blocks_ue.py"""
import os

import unreal

SRC = os.path.join(unreal.Paths.project_saved_dir(), "AssetGen", "import", "hollow_blocks_fixed")
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
MATS = "/Game/ThirdPerson/BackAlleys/Materials"
PARENT = MATS + "/M_BackAlleys_HollowBlocks"
MI = "MI_BackAlleys_HollowBlocks"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary


def say(msg):
    unreal.log_warning("[CHBTEX] " + msg)


def import_tex(src_name, name, normal):
    path = TEX + "/" + name
    if eal.does_asset_exist(path):
        say("%s exists, kept" % name)
        return unreal.load_asset(path)
    task = unreal.AssetImportTask()
    task.filename = os.path.join(SRC, src_name)
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
    tex.set_editor_property("max_texture_size", 2048)
    eal.save_loaded_asset(tex)
    say("%s imported (%s, %s)" % (name, "normal map" if normal else "colour",
                                  tex.get_editor_property("compression_settings")))
    return tex


bc = import_tex("T_HollowBlocks_01_BC.png", "T_BackAlleys_HollowBlocks_BC", False)
nm = import_tex("T_HollowBlocks_01_N.png", "T_BackAlleys_HollowBlocks_N", True)

# GPT's originals, unrepaired (user 2026-11-03, asked whether the repair was wanted: "I dont want that" -> "Use GPT's
# original"). MI_BackAlleys_HollowBlocks is re-pointed at these through the bridge, since the open editor has it loaded.
SRC = os.path.join(unreal.Paths.project_saved_dir(), "AssetGen", "import", "hollow_blocks_zip", "philippine-hollow-blocks")
import_tex("T_HollowBlocks_01_BC.png", "T_BackAlleys_HollowBlocksGPT_BC", False)
import_tex("T_HollowBlocks_01_N_DirectX.png", "T_BackAlleys_HollowBlocksGPT_N", True)
if eal.does_asset_exist(MATS + "/" + MI):
    say("%s exists, kept" % MI)
else:
    mi = tools.create_asset(MI, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", unreal.load_asset(PARENT))
    mel.set_material_instance_texture_parameter_value(mi, "BaseColor", bc)
    mel.set_material_instance_texture_parameter_value(mi, "Normal", nm)
    mel.set_material_instance_scalar_parameter_value(mi, "Roughness", 0.9)
    phys = unreal.load_asset("/Game/ImpactsVFXVol1/Materials/Physical_Materials/Concrete")
    if phys:   # an instance's phys_material only counts with the override flag on
        mi.set_editor_property("override_phys_material", True)
        mi.set_editor_property("phys_material", phys)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say("%s saved (concrete surface: %s)" % (MI, bool(phys)))
