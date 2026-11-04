"""Headless: creates M_BackAlleys_MetalSheet, a corrugated-roof material with a worn paint layer, and its instances.
User 2026-11-03: "Yes, make them" (level-gen asked for painted variants of AsiaSlum's MI_MetalPlate_A_001 to match a
reference of mixed red, rust and galvanised roofs).

The look is the pack sheet's own (T_MetalPlate_A_001_D/M/N/R, copied into BackAlleys/Textures so nothing we make
depends on a pack material: user 2026-11-03, "isolate any new materials we created outside the external assets").
- Paint: PaintColor over the sheet where it's grey, worn through where the texture is rusty (red minus blue above
  Wear). Paint keeps the texture's shading (0.55 + 0.9 x luminance), is non-metallic and PaintRough rough.
- BaseTint multiplies the unpainted sheet (the rust look darkens and warms it).
- U_Tile / V_Tile scale UV0, copied from the pack instance.
Instances: MI_BackAlleys_MetalSheet_Galv (no paint: the pack look), _RedOxide (faded red-oxide primer), _Rust (dark
old rust). Tune colours offline first with preview_metal_sheet.ps1, which uses the same Color formula.
New assets only: anything that exists is kept (the open editor may have it loaded; never re-save those headless).

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\AssetGen\\create_metal_sheet_ue.py"""
import unreal

DEST = "/Game/ThirdPerson/BackAlleys/Materials"
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
SRC_TEX = "/Game/AsiaSlum/Textures/"
SRC_MI = "/Game/AsiaSlum/Material/MI_MetalPlate_A_001"
MAT = "M_BackAlleys_MetalSheet"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
phys = unreal.load_asset("/Game/ImpactsVFXVol1/Materials/Physical_Materials/Metal")   # the project's Metal surface


def say(msg):
    unreal.log_warning("[SHEET] " + msg)


NODES = {
    "UV": ("return UV * float2(U_Tile, V_Tile);", "CMOT_FLOAT2", ["UV", "U_Tile", "V_Tile"]),
    # Keep in step with preview_metal_sheet.ps1 (FORMULA).
    "Color": ("""
float lum = dot(D, float3(0.3, 0.59, 0.11));
float rust = saturate((D.r - D.b) * 6);
float m = Coverage * (1 - smoothstep(Wear - 0.15, Wear + 0.15, rust));
return lerp(D * BaseTint, PaintColor * (0.55 + 0.9 * lum), m);""", "CMOT_FLOAT3",
              ["D", "PaintColor", "Coverage", "Wear", "BaseTint"]),
    "RoughMetal": ("""
float rust = saturate((D.r - D.b) * 6);
float m = Coverage * (1 - smoothstep(Wear - 0.15, Wear + 0.15, rust));
return float2(lerp(saturate(R * RoughScale), PaintRough, m), lerp(saturate(M * MetalScale), 0, m));""", "CMOT_FLOAT2",
                   ["D", "M", "R", "Coverage", "Wear", "RoughScale", "MetalScale", "PaintRough"]),
}


def custom_input(name):
    ci = unreal.CustomInput()
    ci.set_editor_property("input_name", name)
    return ci


def local_texture(name):
    path = TEX + "/" + name
    if not eal.does_asset_exist(path):
        eal.duplicate_asset(SRC_TEX + name, path)
        if not eal.save_asset(path, only_if_is_dirty=False):
            say("FAILED to save %s" % path)
        say("copied %s -> %s" % (SRC_TEX + name, path))
    return unreal.load_asset(path)


def sampler_for(tex):
    cs = tex.get_editor_property("compression_settings")
    srgb = tex.get_editor_property("srgb")
    if cs == unreal.TextureCompressionSettings.TC_NORMALMAP:
        return unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    if cs in (unreal.TextureCompressionSettings.TC_GRAYSCALE, unreal.TextureCompressionSettings.TC_ALPHA):
        return unreal.MaterialSamplerType.SAMPLERTYPE_GRAYSCALE if srgb else \
            unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_GRAYSCALE
    if cs == unreal.TextureCompressionSettings.TC_MASKS or not srgb:
        return unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    return unreal.MaterialSamplerType.SAMPLERTYPE_COLOR


def build_material():
    m = tools.create_asset(MAT, DEST, unreal.Material, unreal.MaterialFactoryNew())

    def node(cls, x, y):
        return mel.create_material_expression(m, cls, x, y)

    uv = node(unreal.MaterialExpressionTextureCoordinate, -2200, -1800)
    scal = {}
    for i, (name, val) in enumerate((("U_Tile", 1.0), ("V_Tile", 1.0), ("Coverage", 0.0), ("Wear", 0.3),
                                     ("RoughScale", 1.0), ("MetalScale", 1.0), ("PaintRough", 0.75))):
        s = node(unreal.MaterialExpressionScalarParameter, -2200, -1600 + 90 * i)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("default_value", val)
        scal[name] = s
    vec = {}
    for i, (name, val) in enumerate((("PaintColor", (0.3, 0.075, 0.035)), ("BaseTint", (1.0, 1.0, 1.0)))):
        p = node(unreal.MaterialExpressionVectorParameter, -2200, -800 + 120 * i)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", unreal.LinearColor(val[0], val[1], val[2], 1))
        vec[name] = p

    customs = {}
    for i, (key, (code, out, ins)) in enumerate(NODES.items()):
        c = node(unreal.MaterialExpressionCustom, -400, -1800 + 500 * i)
        c.set_editor_property("code", code)
        c.set_editor_property("output_type", getattr(unreal.CustomMaterialOutputType, out))
        c.set_editor_property("description", "Sheet_" + key)
        c.set_editor_property("inputs", [custom_input(n) for n in ins])
        customs[key] = c

    def link(src, out_name, key, in_name):
        if not mel.connect_material_expressions(src, out_name, customs[key], in_name):
            say("connect failed: %s.%s -> %s.%s" % (src.get_name(), out_name, key, in_name))

    link(uv, "", "UV", "UV")
    link(scal["U_Tile"], "", "UV", "U_Tile")
    link(scal["V_Tile"], "", "UV", "V_Tile")
    tex = {}
    for i, (name, asset) in enumerate((("D", "T_MetalPlate_A_001_D"), ("M", "T_MetalPlate_A_001_M"),
                                        ("N", "T_MetalPlate_A_001_N"), ("R", "T_MetalPlate_A_001_R"))):
        t = local_texture(asset)
        s = node(unreal.MaterialExpressionTextureSampleParameter2D, -1500, -1400 + 300 * i)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("texture", t)
        s.set_editor_property("sampler_type", sampler_for(t))
        mel.connect_material_expressions(customs["UV"], "", s, "UVs")
        tex[name] = s
    for key in ("Color", "RoughMetal"):
        link(tex["D"], "RGB", key, "D")
        link(scal["Coverage"], "", key, "Coverage")
        link(scal["Wear"], "", key, "Wear")
    link(vec["PaintColor"], "", "Color", "PaintColor")
    link(vec["BaseTint"], "", "Color", "BaseTint")
    link(tex["M"], "R", "RoughMetal", "M")
    link(tex["R"], "R", "RoughMetal", "R")
    for name in ("RoughScale", "MetalScale", "PaintRough"):
        link(scal[name], "", "RoughMetal", name)

    rough = node(unreal.MaterialExpressionComponentMask, 0, -800)
    rough.set_editor_property("r", True)
    metal = node(unreal.MaterialExpressionComponentMask, 0, -650)
    metal.set_editor_property("g", True)
    mel.connect_material_expressions(customs["RoughMetal"], "", rough, "")
    mel.connect_material_expressions(customs["RoughMetal"], "", metal, "")
    P = unreal.MaterialProperty
    ok = [mel.connect_material_property(customs["Color"], "", P.MP_BASE_COLOR),
          mel.connect_material_property(rough, "", P.MP_ROUGHNESS),
          mel.connect_material_property(metal, "", P.MP_METALLIC),
          mel.connect_material_property(tex["N"], "RGB", P.MP_NORMAL)]
    if not all(ok):
        say("material output connections: %s" % ok)
    if phys:
        m.set_editor_property("phys_material", phys)
    mel.layout_material_expressions(m)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say("%s saved, %d expressions" % (MAT, mel.get_num_material_expressions(m)))
    return m


def make_instance(name, parent, scalars, vectors):
    path = DEST + "/" + name
    if eal.does_asset_exist(path):
        say("%s exists, kept" % name)
        return
    mi = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    for k, v in scalars.items():
        mel.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in vectors.items():
        mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(v[0], v[1], v[2], 1))
    if phys:
        mi.set_editor_property("phys_material", phys)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say("%s saved" % name)


# The pack instance's values, so _Galv matches it. Logged: M_BaseMaterial's use of UVDivide is unknown, so check that it
# reads 1 (if not, the tiling here differs from the pack's).
src = unreal.load_asset(SRC_MI)
pack = {}
for k in ("U_Tile", "V_Tile", "UVDivide", "RoughScale", "MetalScale"):
    try:
        pack[k] = mel.get_material_instance_scalar_parameter_value(src, k)
    except Exception as ex:
        say("can't read %s: %s" % (k, ex))
say("pack values %s" % pack)
base = {k: pack[k] for k in ("U_Tile", "V_Tile", "RoughScale", "MetalScale") if k in pack}
if pack.get("UVDivide", 1.0) not in (0.0, 1.0):
    base["U_Tile"] = base.get("U_Tile", 1.0) / pack["UVDivide"]
    base["V_Tile"] = base.get("V_Tile", 1.0) / pack["UVDivide"]

MAT_PATH = DEST + "/" + MAT
m = unreal.load_asset(MAT_PATH) if eal.does_asset_exist(MAT_PATH) else build_material()
# Keep the colours in step with preview_metal_sheet.ps1 ($Looks).
make_instance("MI_BackAlleys_MetalSheet_Galv", m, dict(base, Coverage=0.0), {})
make_instance("MI_BackAlleys_MetalSheet_RedOxide", m, dict(base, Coverage=0.9, Wear=0.3),
              {"PaintColor": (0.30, 0.075, 0.035)})
make_instance("MI_BackAlleys_MetalSheet_Rust", m, dict(base, Coverage=0.75, Wear=0.3, PaintRough=0.85),
              {"PaintColor": (0.16, 0.06, 0.025), "BaseTint": (0.6, 0.42, 0.3)})
