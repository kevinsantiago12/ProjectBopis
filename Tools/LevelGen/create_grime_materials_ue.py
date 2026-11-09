"""Headless, new assets only: the decals for dirt along the feet of walls. User 2026-11-06: "Your decal alignment for the Dirt decals to the edge of the houses are bad".
The pack's masks run the full width of the image, so a strip stopped in a hard line wherever it ended. M_BackAlleys_GroundGrime is a deferred decal that fades both ends along U.
- MI_BackAlleys_Grime_Soft: T_decal_08 in a plain earth colour. Its dense edge is at V 0.985.
- MI_BackAlleys_Grime_Grit01, _Grit02: the pack's road dirt, with its own colour. Their dense edges are at V 0.775 and 0.69 (measured: analysis of the exported masks, row by row).
- MI_BackAlleys_Grime_Leak01, _Leak02: the pack's leak stains, for run-off from pipes and air conditioners, with their hard edge at V 0.
A master that already exists is left alone, as a headless run can't change what the open editor has loaded; only missing instances are made then.
The images aren't changed. The tint and texture calls can return False even when they take: the log lines read them back.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_grime_materials_ue.py"""
import unreal

MATS = "/Game/ThirdPerson/BackAlleys/Materials"
MASTER = "M_BackAlleys_GroundGrime"
WHITE = "/Engine/EngineResources/WhiteSquareTexture"
Y = "/Game/Megapack/Textures/Yakohama/Decal/"
SOFT = "/Game/Megapack/Textures/Favela/Decals/T_decal_08"
KINDS = {
    # name: colour texture, mask, tint, strength
    "Soft": (WHITE, SOFT, (0.060, 0.048, 0.032), 0.85),
    "Grit01": (Y + "T_RoadDirt_01_BC", Y + "T_RoadDirt_01_O", (1.0, 1.0, 1.0), 1.0),
    "Grit02": (Y + "T_RoadDirt_02_BC", Y + "T_RoadDirt_02_O", (1.0, 1.0, 1.0), 1.0),
    "Leak01": (Y + "T_Leakage_01_BC", Y + "T_Leakage_01_O", (1.0, 1.0, 1.0), 1.0),
    "Leak02": (Y + "T_Leakage_02_BC", Y + "T_Leakage_02_O", (1.0, 1.0, 1.0), 1.0),
}
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
P = unreal.MaterialProperty
E = unreal


def say(msg):
    unreal.log_warning("[GRIME] " + msg)


def build():
    path = MATS + "/" + MASTER
    if eal.does_asset_exist(path):
        m = unreal.load_asset(path)
        mel.delete_all_material_expressions(m)
    else:
        m = tools.create_asset(MASTER, MATS, unreal.Material, unreal.MaterialFactoryNew())
    x = [0]

    def node(cls, **props):
        x[0] += 1
        n = mel.create_material_expression(m, cls, -1300 + (x[0] % 5) * 240, -400 + (x[0] // 5) * 170)
        for k, v in props.items():
            n.set_editor_property(k, v)
        return n

    def wire(a, a_out, b, b_in):
        if not mel.connect_material_expressions(a, a_out, b, b_in):
            say("couldn't connect %s.%s to %s.%s" % (a.get_name(), a_out, b.get_name(), b_in))

    def binary(cls, a, b, a_out="", b_out=""):
        n = node(cls)
        wire(a, a_out, n, "A")
        wire(b, b_out, n, "B")
        return n

    def scalar(name, value):
        return node(E.MaterialExpressionScalarParameter, parameter_name=name, default_value=value)

    def sampler(t):
        c = str(t.get_editor_property("compression_settings")).split(".")[-1].split(":")[0]
        if c == "TC_MASKS":
            return E.MaterialSamplerType.SAMPLERTYPE_MASKS
        if c == "TC_GRAYSCALE":
            return E.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE if not t.get_editor_property("srgb") else E.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE
        if c == "TC_ALPHA":
            return E.MaterialSamplerType.SAMPLERTYPE_ALPHA
        return E.MaterialSamplerType.SAMPLERTYPE_COLOR if t.get_editor_property("srgb") else E.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR

    soft_mask = unreal.load_asset(SOFT)
    white = unreal.load_asset(WHITE)
    say("mask %s compression %s srgb %s" % (soft_mask.get_name(), soft_mask.get_editor_property("compression_settings"), soft_mask.get_editor_property("srgb")))
    mask = node(E.MaterialExpressionTextureSampleParameter2D, parameter_name="Mask", texture=soft_mask, sampler_type=sampler(soft_mask))
    colour = node(E.MaterialExpressionTextureSampleParameter2D, parameter_name="Colour", texture=white, sampler_type=sampler(white))
    tint = node(E.MaterialExpressionVectorParameter, parameter_name="Tint", default_value=E.LinearColor(1.0, 1.0, 1.0, 1.0))
    uv = node(E.MaterialExpressionTextureCoordinate)
    u = node(E.MaterialExpressionComponentMask, r=True, g=False, b=False, a=False)
    wire(uv, "", u, "")
    u_back = node(E.MaterialExpressionOneMinus)
    wire(u, "", u_back, "")
    nearer = binary(E.MaterialExpressionMin, u, u_back)
    ends = node(E.MaterialExpressionSaturate)
    wire(binary(E.MaterialExpressionDivide, nearer, scalar("EndFade", 0.14)), "", ends, "")
    opacity = binary(E.MaterialExpressionMultiply, binary(E.MaterialExpressionMultiply, mask, scalar("Strength", 1.0), "R", ""), ends)
    base = binary(E.MaterialExpressionMultiply, colour, tint, "RGB", "")
    rough = node(E.MaterialExpressionConstant, r=0.9)
    spec = node(E.MaterialExpressionConstant, r=0.2)
    metal = node(E.MaterialExpressionConstant, r=0.0)
    ok = [mel.connect_material_property(base, "", P.MP_BASE_COLOR), mel.connect_material_property(opacity, "", P.MP_OPACITY), mel.connect_material_property(rough, "", P.MP_ROUGHNESS),
          mel.connect_material_property(spec, "", P.MP_SPECULAR), mel.connect_material_property(metal, "", P.MP_METALLIC)]
    say("outputs %s" % ok)
    m.set_editor_property("blend_mode", E.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("material_domain", E.MaterialDomain.MD_DEFERRED_DECAL)     # last: an opaque decal won't compile
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say(MASTER + " made")
    return m


master = unreal.load_asset(MATS + "/" + MASTER) if eal.does_asset_exist(MATS + "/" + MASTER) else build()
for name, (col, msk, tint, strength) in KINDS.items():
    mi_name = "MI_BackAlleys_Grime_" + name
    path = MATS + "/" + mi_name
    if eal.does_asset_exist(path):
        continue
    mi = tools.create_asset(mi_name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, master)
    m_t = unreal.load_asset(msk)
    mel.set_material_instance_texture_parameter_value(mi, "Mask", m_t)
    mel.set_material_instance_texture_parameter_value(mi, "Colour", unreal.load_asset(col))
    mel.set_material_instance_vector_parameter_value(mi, "Tint", E.LinearColor(tint[0], tint[1], tint[2], 1.0))
    mel.set_material_instance_scalar_parameter_value(mi, "Strength", strength)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say("%s mask %s (%s) tint %.3f strength %.2f" % (mi_name, mel.get_material_instance_texture_parameter_value(mi, "Mask").get_name(), str(m_t.get_editor_property("compression_settings")).split(".")[-1].split(":")[0],
                                                    mel.get_material_instance_vector_parameter_value(mi, "Tint").r, mel.get_material_instance_scalar_parameter_value(mi, "Strength")))
