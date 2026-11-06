"""Headless, new assets only: M_BackAlleys_Tyre and MI_BackAlleys_Tyre, for the tyres on the roofs. The pack's MI_wheel_01 is a dusty brown with no tint to turn (its parent M_wall_01 has
textures and nothing else), and in the sun it reads as pale as plaster. This samples the pack's own wheel textures, unchanged, with a Brightness parameter: 0.35 by default, 1 shows
them as supplied. Named "wheel" because a path with "\t" in it reaches Unreal as a tab.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_wheel_material_ue.py"""
import unreal

TEX = "/Game/Megapack/Textures/MiddleEast/T_wheel_01_"
MATS = "/Game/ThirdPerson/BackAlleys/Materials"
MASTER, INSTANCE = "M_BackAlleys_Tyre", "MI_BackAlleys_Tyre"
RUBBER = "/Game/ImpactsVFXVol1/Materials/Physical_Materials/Rubber"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
P = unreal.MaterialProperty


def say(msg):
    unreal.log_warning("[TYREMAT] " + msg)


def sampler(t):
    cs = t.get_editor_property("compression_settings")
    if cs == unreal.TextureCompressionSettings.TC_NORMALMAP:
        return unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    if cs == unreal.TextureCompressionSettings.TC_MASKS:
        return unreal.MaterialSamplerType.SAMPLERTYPE_MASKS
    return unreal.MaterialSamplerType.SAMPLERTYPE_COLOR if t.get_editor_property("srgb") else unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR


def build():
    path = MATS + "/" + MASTER
    if eal.does_asset_exist(path):
        say(MASTER + " exists, kept")
        return unreal.load_asset(path)
    m = tools.create_asset(MASTER, MATS, unreal.Material, unreal.MaterialFactoryNew())

    def sample(name, y):
        t = unreal.load_asset(TEX + name)
        n = mel.create_material_expression(m, unreal.MaterialExpressionTextureSample, -700, y)
        n.set_editor_property("texture", t)
        n.set_editor_property("sampler_type", sampler(t))
        return n

    bc, nm, orm = sample("BC", -300), sample("N", 0), sample("ORM", 300)
    bright = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -700, -500)
    bright.set_editor_property("parameter_name", "Brightness")
    bright.set_editor_property("default_value", 0.35)
    mul = mel.create_material_expression(m, unreal.MaterialExpressionMultiply, -350, -300)
    mel.connect_material_expressions(bc, "RGB", mul, "A")
    mel.connect_material_expressions(bright, "", mul, "B")
    ok = [mel.connect_material_property(mul, "", P.MP_BASE_COLOR), mel.connect_material_property(nm, "RGB", P.MP_NORMAL),
          mel.connect_material_property(orm, "R", P.MP_AMBIENT_OCCLUSION), mel.connect_material_property(orm, "G", P.MP_ROUGHNESS),
          mel.connect_material_property(orm, "B", P.MP_METALLIC)]
    say("connected %s" % ok)
    m.set_editor_property("phys_material", unreal.load_asset(RUBBER))
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say(MASTER + " made")
    return m


master = build()
if eal.does_asset_exist(MATS + "/" + INSTANCE):
    say(INSTANCE + " exists, kept")
else:
    mi = tools.create_asset(INSTANCE, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", master)
    eal.save_loaded_asset(mi)
    say(INSTANCE + " made")
