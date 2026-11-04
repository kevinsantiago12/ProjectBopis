"""Headless: imports the jalousie window textures (user 2026-11-03: "Heres a Jalouse window texture, can you put it on a
plane and use this instead of the mesh window?") and makes M_BackAlleys_Jalousie, a plain lit material for them.
New assets only, so the open editor can stay open.

Sources: Saved/LevelGen/import/T_BackAlleys_Jalousie_BC.png and _N.png (converted from the images the user pasted).
The images are 1254 x 1254; they're stretched to a power of two (mips, streaming) and capped at 1024 for the Deck.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_jalousie_ue.py"""
import os

import unreal

SRC = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "import")
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
MATS = "/Game/ThirdPerson/BackAlleys/Materials"
MAT = "M_BackAlleys_Jalousie"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary


def say(msg):
    unreal.log_warning("[JAL] " + msg)


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
    try:
        tex.set_editor_property("power_of_two_mode", unreal.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO)
    except Exception as e:
        say("no stretch mode (%s), padding instead" % e)
        tex.set_editor_property("power_of_two_mode", unreal.TexturePowerOfTwoSetting.PAD_TO_POWER_OF_TWO)
    tex.set_editor_property("max_texture_size", 1024)
    eal.save_loaded_asset(tex)
    say("%s imported (%s)" % (name, "normal map" if normal else "colour"))
    return tex


bc = import_tex("T_BackAlleys_Jalousie_BC", False)
nm = import_tex("T_BackAlleys_Jalousie_N", True)

if eal.does_asset_exist(MATS + "/" + MAT):
    say("%s exists, kept" % MAT)
else:
    m = tools.create_asset(MAT, MATS, unreal.Material, unreal.MaterialFactoryNew())
    s_bc = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -500, 0)
    s_bc.set_editor_property("parameter_name", "BaseColor")
    s_bc.set_editor_property("texture", bc)
    s_bc.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    s_n = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -500, 300)
    s_n.set_editor_property("parameter_name", "Normal")
    s_n.set_editor_property("texture", nm)
    s_n.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    rough = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -300, 200)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.35)   # glass louvres: a little gloss
    P = unreal.MaterialProperty
    ok = [mel.connect_material_property(s_bc, "RGB", P.MP_BASE_COLOR),
          mel.connect_material_property(s_n, "RGB", P.MP_NORMAL),
          mel.connect_material_property(rough, "", P.MP_ROUGHNESS)]
    if not all(ok):
        say("output connections: %s" % ok)
    phys = unreal.load_asset("/Game/ImpactsVFXVol1/Materials/Physical_Materials/Glass")
    if phys:
        m.set_editor_property("phys_material", phys)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say("%s saved (glass surface: %s)" % (MAT, bool(phys)))

# The double jalousie (user 2026-11-03: "Replace with this textures" - two panes side by side, 1024 x 1024): new
# textures and an instance of M_BackAlleys_Jalousie that uses them; the windows switch to it. New assets only, since
# the open editor has the first set loaded.
bc2 = import_tex("T_BackAlleys_JalousieDouble_BC", False)
nm2 = import_tex("T_BackAlleys_JalousieDouble_N", True)
MI2 = "MI_BackAlleys_JalousieDouble"
if eal.does_asset_exist(MATS + "/" + MI2):
    say("%s exists, kept" % MI2)
else:
    mi = tools.create_asset(MI2, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", unreal.load_asset(MATS + "/" + MAT))
    mel.set_material_instance_texture_parameter_value(mi, "BaseColor", bc2)
    mel.set_material_instance_texture_parameter_value(mi, "Normal", nm2)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say("%s saved" % MI2)
