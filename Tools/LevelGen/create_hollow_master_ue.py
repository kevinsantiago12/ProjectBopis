"""Headless, new assets only: creates M_BackAlleys_HollowBlocks, the plain textured master (BaseColor / Normal / Roughness on
UV0) with a Concrete surface. It replaces M_BackAlleys_Jalousie as the parent of our textured instances.
User 2026-11-04: "you made a jalouise material and decided to parent the hollowblocks from that, it should have been the
other way around" (hollow-block walls sounded like glass). So concrete is the base, and the jalousie window instance is a
child that overrides to Glass. Same parameter names as the old parent, so an instance keeps its values when re-parented.

A material instance's phys_material only counts with bOverridePhysMaterial on (UMaterialInstance::GetPhysicalMaterial);
without the flag the parent's is used. The re-parenting and flags go through the bridge, since the editor has them loaded.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_hollow_master_ue.py"""
import unreal

MATS = "/Game/ThirdPerson/BackAlleys/Materials"
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
MAT = "M_BackAlleys_HollowBlocks"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary

if eal.does_asset_exist(MATS + "/" + MAT):
    unreal.log_warning("[MASTER] %s exists, kept" % MAT)
else:
    m = tools.create_asset(MAT, MATS, unreal.Material, unreal.MaterialFactoryNew())
    s_bc = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -500, 0)
    s_bc.set_editor_property("parameter_name", "BaseColor")
    s_bc.set_editor_property("texture", unreal.load_asset(TEX + "/T_BackAlleys_HollowBlocksGPT_BC"))
    s_bc.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    s_n = mel.create_material_expression(m, unreal.MaterialExpressionTextureSampleParameter2D, -500, 300)
    s_n.set_editor_property("parameter_name", "Normal")
    s_n.set_editor_property("texture", unreal.load_asset(TEX + "/T_BackAlleys_HollowBlocksGPT_N"))
    s_n.set_editor_property("sampler_type", unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL)
    rough = mel.create_material_expression(m, unreal.MaterialExpressionScalarParameter, -300, 200)
    rough.set_editor_property("parameter_name", "Roughness")
    rough.set_editor_property("default_value", 0.9)
    P = unreal.MaterialProperty
    ok = [mel.connect_material_property(s_bc, "RGB", P.MP_BASE_COLOR),
          mel.connect_material_property(s_n, "RGB", P.MP_NORMAL),
          mel.connect_material_property(rough, "", P.MP_ROUGHNESS)]
    if not all(ok):
        unreal.log_warning("[MASTER] output connections: %s" % ok)
    m.set_editor_property("phys_material", unreal.load_asset("/Game/ImpactsVFXVol1/Materials/Physical_Materials/Concrete"))
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    unreal.log_warning("[MASTER] %s saved" % MAT)
