"""Headless: the materials for the poured surfaces over the old asphalt. User 2026-11-06: "Next step is ground dirt, variations and dressings".
- M_BackAlleys_GroundPour: opaque, mapped from world position, so a bay of any size shows the texture at one scale, and no two pours line up: each instance has its own offset. A second, far larger sample of
  the colour texture breaks up the tile at a distance. Tile is in cm. Concrete surface; the asphalt patches say so per piece, with `phys` in the plan.
- MI_BackAlleys_Ground_<kind>: the tones. Megapack's T_Concrete_01 and T_Asphalt.
The master's samplers are set from the textures it's given, and the log line reads the tints back: the calls can return False even when they take.

Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\create_ground_materials_ue.py"""
import unreal

MATS = "/Game/ThirdPerson/BackAlleys/Materials"
MASTER = "M_BackAlleys_GroundPour"
PHYS = "/Game/ImpactsVFXVol1/Materials/Physical_Materials/"
CONC = "/Game/Megapack/Textures/Favela/T_Concrete_01_"
ASPH = "/Game/Megapack/Textures/Yakohama/T_Asphalt_"
KINDS = {
    # name: textures, tint, tile cm, offset, roughness multiplier
    "ConcreteA": (CONC, (0.72, 0.70, 0.65), 430.0, (0.13, 0.41), 1.0),
    "ConcreteB": (CONC, (0.84, 0.81, 0.73), 390.0, (0.57, 0.08), 1.0),
    "ConcreteOld": (CONC, (0.50, 0.48, 0.44), 470.0, (0.29, 0.73), 1.05),
    "ConcreteNew": (CONC, (1.08, 1.05, 0.97), 360.0, (0.81, 0.36), 0.95),
    "AsphaltPatch": (ASPH, (0.45, 0.45, 0.46), 170.0, (0.47, 0.62), 1.0),
}
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
P = unreal.MaterialProperty
E = unreal


def say(msg):
    unreal.log_warning("[GROUNDMAT] " + msg)


def sampler_for(t):
    c = str(t.get_editor_property("compression_settings")).split(".")[-1].split(":")[0]
    if c == "TC_NORMALMAP":
        return E.MaterialSamplerType.SAMPLERTYPE_NORMAL
    if c == "TC_MASKS":
        return E.MaterialSamplerType.SAMPLERTYPE_MASKS
    if t.get_editor_property("srgb"):
        return E.MaterialSamplerType.SAMPLERTYPE_COLOR
    return E.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR


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

    bc_t = unreal.load_asset(CONC + "BC")
    n_t = unreal.load_asset(CONC + "N")
    orm_t = unreal.load_asset(CONC + "ORM")
    pos = node(E.MaterialExpressionWorldPosition)
    xy = node(E.MaterialExpressionComponentMask, r=True, g=True, b=False, a=False)
    wire(pos, "", xy, "")
    off = node(E.MaterialExpressionAppendVector)
    wire(scalar("OffsetX", 0.0), "", off, "A")
    wire(scalar("OffsetY", 0.0), "", off, "B")
    uv = binary(E.MaterialExpressionAdd, binary(E.MaterialExpressionDivide, xy, scalar("Tile", 430.0)), off)
    uv_far = binary(E.MaterialExpressionDivide, xy, scalar("TileFar", 2300.0))
    bc = node(E.MaterialExpressionTextureSampleParameter2D, parameter_name="BC", texture=bc_t, sampler_type=sampler_for(bc_t))
    wire(uv, "", bc, "UVs")
    nm = node(E.MaterialExpressionTextureSampleParameter2D, parameter_name="Normal", texture=n_t, sampler_type=sampler_for(n_t))
    wire(uv, "", nm, "UVs")
    orm = node(E.MaterialExpressionTextureSampleParameter2D, parameter_name="ORM", texture=orm_t, sampler_type=sampler_for(orm_t))
    wire(uv, "", orm, "UVs")
    far = node(E.MaterialExpressionTextureSampleParameter2D, parameter_name="BCFar", texture=bc_t, sampler_type=sampler_for(bc_t))
    wire(uv_far, "", far, "UVs")
    # The far sample, about 0.2 in the middle: dark and light by up to a fifth.
    gain = binary(E.MaterialExpressionMultiply, far, scalar("FarGain", 1.6), "G", "")
    blot = node(E.MaterialExpressionLinearInterpolate)
    wire(scalar("FarDark", 0.8), "", blot, "A")
    wire(scalar("FarLight", 1.2), "", blot, "B")
    sat = node(E.MaterialExpressionSaturate)
    wire(gain, "", sat, "")
    wire(sat, "", blot, "Alpha")
    tint = node(E.MaterialExpressionVectorParameter, parameter_name="Tint", default_value=E.LinearColor(1.0, 1.0, 1.0, 1.0))
    base = binary(E.MaterialExpressionMultiply, binary(E.MaterialExpressionMultiply, bc, tint, "RGB", ""), blot)
    rough = binary(E.MaterialExpressionMultiply, orm, scalar("RoughMul", 1.0), "G", "")
    ok = [mel.connect_material_property(base, "", P.MP_BASE_COLOR), mel.connect_material_property(nm, "RGB", P.MP_NORMAL), mel.connect_material_property(rough, "", P.MP_ROUGHNESS),
          mel.connect_material_property(orm, "R", P.MP_AMBIENT_OCCLUSION)]
    say("outputs %s" % ok)
    m.set_editor_property("phys_material", unreal.load_asset(PHYS + "Concrete"))
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say(MASTER + " made")
    return m


master = build()
for name, (tx, tint, tile, offset, rough) in KINDS.items():
    mi_name = "MI_BackAlleys_Ground_" + name
    path = MATS + "/" + mi_name
    mi = unreal.load_asset(path) if eal.does_asset_exist(path) else tools.create_asset(mi_name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, master)
    bc_t = unreal.load_asset(tx + "BC")
    mel.set_material_instance_texture_parameter_value(mi, "BC", bc_t)
    mel.set_material_instance_texture_parameter_value(mi, "BCFar", bc_t)
    mel.set_material_instance_texture_parameter_value(mi, "Normal", unreal.load_asset(tx + "N"))
    mel.set_material_instance_texture_parameter_value(mi, "ORM", unreal.load_asset(tx + "ORM"))
    mel.set_material_instance_vector_parameter_value(mi, "Tint", E.LinearColor(tint[0], tint[1], tint[2], 1.0))
    mel.set_material_instance_scalar_parameter_value(mi, "Tile", tile)
    mel.set_material_instance_scalar_parameter_value(mi, "OffsetX", offset[0])
    mel.set_material_instance_scalar_parameter_value(mi, "OffsetY", offset[1])
    mel.set_material_instance_scalar_parameter_value(mi, "RoughMul", rough)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    t_ = mel.get_material_instance_vector_parameter_value(mi, "Tint")
    say("%s tint %.2f %.2f %.2f tile %.0f BC %s" % (mi_name, t_.r, t_.g, t_.b, mel.get_material_instance_scalar_parameter_value(mi, "Tile"), mel.get_material_instance_texture_parameter_value(mi, "BC").get_name()))
