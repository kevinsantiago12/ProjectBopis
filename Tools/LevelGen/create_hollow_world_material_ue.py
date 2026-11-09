"""Headless, new assets only (2026-11-08): M_BackAlleys_HollowBlocksWorld and MI_BackAlleys_HollowBlocks_World, the user's hollow
blocks (T_BackAlleys_HollowBlocksGPT_BC / _N, untouched) mapped from world position, for walls built as boxes (the story levels'
interiors, yard walls). User 2026-11-08: "you are also using the wrong hollowblock material" (the boxes had the procedural
MI_BackAlleys_CHB_Bare). MI_BackAlleys_HollowBlocks maps the texture through the Favela tile's UV0, which on a box would stretch;
this samples the same texture at the tile's own density (AssetGen manifest: 225 cm per U along the tile, 213.3 cm per V up it),
so a box wall reads exactly as a hollow-block tile does. x + y runs along any axis-aligned wall and z up it, as M_BackAlleys_CHB.
Concrete surface, as M_BackAlleys_HollowBlocks.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_hollow_world_material_ue.py"""
import unreal

MATS = "/Game/ThirdPerson/BackAlleys/Materials"
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
MAT, MI = "M_BackAlleys_HollowBlocksWorld", "MI_BackAlleys_HollowBlocks_World"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
phys = unreal.load_asset("/Game/ImpactsVFXVol1/Materials/Physical_Materials/Concrete")


def say(msg):
    unreal.log_warning("[HOLLOWW] " + msg)


def custom_input(name):
    ci = unreal.CustomInput()
    ci.set_editor_property("input_name", name)
    return ci


if eal.does_asset_exist(MATS + "/" + MAT):
    say("%s exists, kept" % MAT)
else:
    m = tools.create_asset(MAT, MATS, unreal.Material, unreal.MaterialFactoryNew())
    wp = mel.create_material_expression(m, unreal.MaterialExpressionWorldPosition, -1400, 0)
    params = {}
    for i, (name, val) in enumerate((("TileU", 225.0), ("TileV", 213.3), ("Roughness", 0.9))):
        s = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -1400, 150 + 100 * i)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("default_value", val)
        params[name] = s
    uv = mel.create_material_expression(m, unreal.MaterialExpressionCustom, -1000, 0)
    uv.set_editor_property("code", "return float2((WP.x + WP.y) / TileU, -WP.z / TileV);")
    uv.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT2)
    uv.set_editor_property("description", "HollowBlocks_WorldUV")
    uv.set_editor_property("inputs", [custom_input("WP"), custom_input("TileU"), custom_input("TileV")])
    ok = [mel.connect_material_expressions(wp, "", uv, "WP"),
          mel.connect_material_expressions(params["TileU"], "", uv, "TileU"),
          mel.connect_material_expressions(params["TileV"], "", uv, "TileV")]
    s_bc = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -500, 0)
    s_bc.set_editor_property("parameter_name", "BaseColor")
    s_bc.set_editor_property("texture", unreal.load_asset(TEX + "/T_BackAlleys_HollowBlocksGPT_BC"))
    s_bc.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    s_n = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -500, 300)
    s_n.set_editor_property("parameter_name", "Normal")
    s_n.set_editor_property("texture", unreal.load_asset(TEX + "/T_BackAlleys_HollowBlocksGPT_N"))
    s_n.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    ok += [mel.connect_material_expressions(uv, "", s_bc, "UVs"), mel.connect_material_expressions(uv, "", s_n, "UVs")]
    P = unreal.MaterialProperty
    ok += [mel.connect_material_property(s_bc, "RGB", P.MP_BASE_COLOR),
           mel.connect_material_property(s_n, "RGB", P.MP_NORMAL),
           mel.connect_material_property(params["Roughness"], "", P.MP_ROUGHNESS)]
    say("connections: %s" % ok)
    m.set_editor_property("phys_material", phys)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say("%s saved" % MAT)
if eal.does_asset_exist(MATS + "/" + MI):
    say("%s exists, kept" % MI)
else:
    mi = tools.create_asset(MI, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, unreal.load_asset(MATS + "/" + MAT))
    mi.set_editor_property("phys_material", phys)
    mi.set_editor_property("override_phys_material", True)     # without the flag the instance reports its parent's (LESSONS)
    eal.save_loaded_asset(mi)
    say("%s saved" % MI)
