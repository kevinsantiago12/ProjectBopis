"""Headless, new assets only: imports what make_street_textures.py drew and makes the street dressing's materials (user 2026-11-05: "do
all that and add it to the tool").
- MI_BackAlleys_Sign_Red / _Yellow / _White / _Blue: blank painted boards on Metal, inherited from M_BackAlleys_HollowBlocks.
- M_BackAlleys_PeelDecal + MI_BackAlleys_Peel_A / _B: flakes of bare render, a deferred decal. Colour and opacity from one texture, so
  it costs far less than the paint decals.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_street_materials_ue.py"""
import os

import unreal

SRC = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "import", "street")
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
MATS = "/Game/ThirdPerson/BackAlleys/Materials"
METAL = "/Game/ImpactsVFXVol1/Materials/Physical_Materials/Metal"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary


def say(msg):
    unreal.log_warning("[STREETMAT] " + msg)


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
    say("%s imported, format %s" % (name, tex.get_editor_property("compression_settings")))
    return tex


def sign(name, bc, nm):
    if eal.does_asset_exist(MATS + "/" + name):
        say("%s exists, kept" % name)
        return
    mi = tools.create_asset(name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", unreal.load_asset(MATS + "/M_BackAlleys_HollowBlocks"))
    mel.set_material_instance_texture_parameter_value(mi, "BaseColor", bc)
    mel.set_material_instance_texture_parameter_value(mi, "Normal", nm)
    mel.set_material_instance_scalar_parameter_value(mi, "Roughness", 0.7)
    mi.set_editor_property("phys_material", unreal.load_asset(METAL))
    mi.set_editor_property("override_phys_material", True)      # without it the engine uses the parent's
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say("%s saved" % name)


def peel_master(tex):
    path = MATS + "/M_BackAlleys_PeelDecal"
    if eal.does_asset_exist(path):
        say("M_BackAlleys_PeelDecal exists, kept")
        return unreal.load_asset(path)
    m = tools.create_asset("M_BackAlleys_PeelDecal", MATS, unreal.Material, unreal.MaterialFactoryNew())
    s = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -500, 0)
    s.set_editor_property("parameter_name", "Peel")
    s.set_editor_property("texture", tex)
    s.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    rough = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -500, 250)
    rough.set_editor_property("r", 0.95)
    spec = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -500, 350)
    spec.set_editor_property("r", 0.3)
    metal = mel.create_material_expression(m, unreal.MaterialExpressionConstant, -500, 450)
    metal.set_editor_property("r", 0.0)
    P = unreal.MaterialProperty
    ok = [mel.connect_material_property(s, "RGB", P.MP_BASE_COLOR), mel.connect_material_property(s, "A", P.MP_OPACITY),
          mel.connect_material_property(rough, "", P.MP_ROUGHNESS), mel.connect_material_property(spec, "", P.MP_SPECULAR),
          mel.connect_material_property(metal, "", P.MP_METALLIC)]
    if not all(ok):
        say("decal output connections: %s" % ok)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)   # last: an opaque decal won't compile
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say("M_BackAlleys_PeelDecal saved")
    return m


sign_n = unreal.load_asset("/Engine/EngineMaterials/DefaultNormal")     # flat: a drawn normal made the boards look hammered
for kind in ("Red", "Yellow", "White", "Blue"):
    sign("MI_BackAlleys_Sign_" + kind, import_tex("T_BackAlleys_Sign_%s_BC" % kind, False), sign_n)
peel_a = import_tex("T_BackAlleys_Peel_A_BC", False)
peel_b = import_tex("T_BackAlleys_Peel_B_BC", False)
master = peel_master(peel_a)
for letter, tex in (("A", peel_a), ("B", peel_b)):
    name = "MI_BackAlleys_Peel_" + letter
    if eal.does_asset_exist(MATS + "/" + name):
        say("%s exists, kept" % name)
        continue
    mi = tools.create_asset(name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", master)
    mel.set_material_instance_texture_parameter_value(mi, "Peel", tex)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say("%s saved" % name)
