"""Headless, new assets only: creates M_BackAlleys_Boards, a timber material mapped from world position, and its instances,
for the weatherboards and gable wedges on the metal roofs and for the flashing.
User 2026-11-03: "roof textures are busted too" (a screenshot of a gable wedge in grey streaks).

Why: MiddleEast's T_wood_* textures are atlases. Only part of each is real wood or paint; the rest is smeared padding. The
beams' own UVs stay on the good part, but a beam stretched into a tall board magnifies a thin strip, and SM_Ramp's UVs land
on the padding. So the plank look is drawn here, as M_BackAlleys_CHB draws its blocks: mapped from world position (no mesh
UVs, so scale and mesh don't matter and a board and its wedge line up), and sampling only the usable band of the atlas.
- Planks: PlankH cm tall, each with its own place in the texture and its own tone, a dark gap between them. Gap < 0: none.
- The band: VMin..VMax of the texture. Period > 0 picks painted stripes (blue, green), BandH tall, centred on
  VMin + i * Period, so a plank is paint with worn patches, as on the beams. Measured from the exported textures.
- Upward faces map from above, so a nearly level strip (the flashing) doesn't smear.
Our own copies of the pack textures (user 2026-11-03: "isolate any new materials we created outside the external assets").
The material compiles when the open editor first loads it; errors show in Saved/Logs/ProjectBopis.log.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_board_material_ue.py"""
import unreal

DEST = "/Game/ThirdPerson/BackAlleys/Materials"
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
PACK_TEX = "/Game/Megapack/Textures/MiddleEast/"
PHYS = "/Game/ImpactsVFXVol1/Materials/Physical_Materials/"
MAT = "M_BackAlleys_Boards"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary


def say(msg):
    unreal.log_warning("[BOARDS] " + msg)


PLANK = """
float3 Q = abs(Nrm.z) > 0.7 ? float3(WP.x, 0, WP.y) : float3(WP.x + WP.y, 0, WP.z);
float row = floor(Q.z / PlankH);
float fv = frac(Q.z / PlankH);
float r1 = frac(sin(row * 12.9898) * 43758.5453);
float r2 = frac(sin(row * 78.233) * 12543.123);
"""
NODES = {
    "UV": (PLANK + """
float v = Period > 0 ? VMin + floor(r1 * floor((VMax - VMin) / Period + 1)) * Period + (fv - 0.5) * BandH
                     : VMin + r1 * (VMax - VMin - BandH) + fv * BandH;
return float2(Q.x / TileCm + r2, v);""", "CMOT_FLOAT2",
           ["WP", "Nrm", "PlankH", "TileCm", "VMin", "VMax", "Period", "BandH"]),
    "Color": (PLANK + """
float d = min(fv, 1 - fv) * PlankH;
float line_ = Gap >= 0 ? lerp(0.25, 1.0, saturate((d - Gap * 0.5) / 0.4)) : 1.0;
float tone = Gap >= 0 ? 0.88 + 0.24 * r2 : 1.0;
return BC * Tint * line_ * tone;""", "CMOT_FLOAT3", ["WP", "Nrm", "BC", "Tint", "PlankH", "Gap"]),
}


def custom_input(name):
    ci = unreal.CustomInput()
    ci.set_editor_property("input_name", name)
    return ci


def local_texture(name):
    path = TEX + "/" + name
    if not eal.does_asset_exist(path):
        eal.duplicate_asset(PACK_TEX + name, path)
        if not eal.save_asset(path, only_if_is_dirty=False):
            say("FAILED to save %s" % path)
        say("copied %s" % name)
    return unreal.load_asset(path)


def sampler_for(tex):
    cs = tex.get_editor_property("compression_settings")
    if cs == unreal.TextureCompressionSettings.TC_NORMALMAP:
        return unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    if cs == unreal.TextureCompressionSettings.TC_MASKS or not tex.get_editor_property("srgb"):
        return unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    return unreal.MaterialSamplerType.SAMPLERTYPE_COLOR


def build_material():
    m = tools.create_asset(MAT, DEST, unreal.Material, unreal.MaterialFactoryNew())

    def node(cls, x, y):
        return mel.create_material_expression(m, cls, x, y)

    wp = node(unreal.MaterialExpressionWorldPosition, -2200, 0)
    nrm = node(unreal.MaterialExpressionVertexNormalWS, -2200, 120)
    scal = {}
    for i, (name, val) in enumerate((("PlankH", 20.0), ("Gap", 1.0), ("TileCm", 738.0), ("VMin", 0.29), ("VMax", 0.99),
                                     ("Period", 0.0), ("BandH", 0.027), ("Metal", 0.0))):
        s = node(unreal.MaterialExpressionScalarParameter, -2200, 240 + 90 * i)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("default_value", val)
        scal[name] = s
    tint = node(unreal.MaterialExpressionVectorParameter, -2200, 1000)
    tint.set_editor_property("parameter_name", "Tint")
    tint.set_editor_property("default_value", unreal.LinearColor(1, 1, 1, 1))

    customs = {}
    for i, (key, (code, out, ins)) in enumerate(NODES.items()):
        c = node(unreal.MaterialExpressionCustom, -1000 + 700 * i, -600 + 500 * i)
        c.set_editor_property("code", code)
        c.set_editor_property("output_type", getattr(unreal.CustomMaterialOutputType, out))
        c.set_editor_property("description", "Boards_" + key)
        c.set_editor_property("inputs", [custom_input(n) for n in ins])
        customs[key] = c

    tex = {}
    for i, (name, asset) in enumerate((("BC", "T_wood_01_BC"), ("N", "T_wood_01_N"), ("ORM", "T_wood_01_ORM"))):
        t = local_texture(asset)
        s = node(unreal.MaterialExpressionTextureSampleParameter2D, -600, -200 + 300 * i)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("texture", t)
        s.set_editor_property("sampler_type", sampler_for(t))
        mel.connect_material_expressions(customs["UV"], "", s, "UVs")
        tex[name] = s

    def link(src, out_name, key, in_name):
        if not mel.connect_material_expressions(src, out_name, customs[key], in_name):
            say("connect failed: %s.%s -> %s.%s" % (src.get_name(), out_name, key, in_name))

    for key in NODES:
        link(wp, "", key, "WP")
        link(nrm, "", key, "Nrm")
        link(scal["PlankH"], "", key, "PlankH")
    for name in ("TileCm", "VMin", "VMax", "Period", "BandH"):
        link(scal[name], "", "UV", name)
    link(scal["Gap"], "", "Color", "Gap")
    link(tint, "", "Color", "Tint")
    link(tex["BC"], "RGB", "Color", "BC")

    P = unreal.MaterialProperty
    ok = [mel.connect_material_property(customs["Color"], "", P.MP_BASE_COLOR),
          mel.connect_material_property(tex["ORM"], "G", P.MP_ROUGHNESS),
          mel.connect_material_property(tex["ORM"], "R", P.MP_AMBIENT_OCCLUSION),
          mel.connect_material_property(tex["N"], "RGB", P.MP_NORMAL),
          mel.connect_material_property(scal["Metal"], "", P.MP_METALLIC)]
    if not all(ok):
        say("material output connections: %s" % ok)
    m.set_editor_property("phys_material", unreal.load_asset(PHYS + "Wood"))
    mel.layout_material_expressions(m)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say("%s saved" % MAT)
    return m


def make_instance(name, parent, scalars, tint, first, phys):
    path = DEST + "/" + name
    if eal.does_asset_exist(path):
        say("%s exists, kept" % name)
        return
    mi = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    for k, v in scalars.items():
        mel.set_material_instance_scalar_parameter_value(mi, k, v)
    if tint:
        mel.set_material_instance_vector_parameter_value(mi, "Tint", unreal.LinearColor(tint[0], tint[1], tint[2], 1))
    for k, suffix in (("BC", "_BC"), ("N", "_N"), ("ORM", "_ORM")):
        mel.set_material_instance_texture_parameter_value(mi, k, unreal.load_asset(TEX + "/" + first[k]))
    mi.set_editor_property("phys_material", unreal.load_asset(PHYS + phys))
    mi.set_editor_property("override_phys_material", True)   # without it the engine uses the parent's (GetPhysicalMaterial)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say("%s saved" % name)


def wood(bc, n, orm):
    for t in (bc, n, orm):
        local_texture(t)
    return {"BC": bc, "N": n, "ORM": orm}


path = DEST + "/" + MAT
m = unreal.load_asset(path) if eal.does_asset_exist(path) else build_material()
# 20 cm planks at the texture's own scale (the beams': 738 cm across the whole texture), so 20 / 738 = 0.027 tall.
make_instance("MI_BackAlleys_Boards_Natural", m, {"VMin": 0.29, "VMax": 0.99}, None,
              wood("T_wood_01_BC", "T_wood_01_N", "T_wood_01_ORM"), "Wood")
make_instance("MI_BackAlleys_Boards_Brown", m, {"VMin": 0.01, "VMax": 0.44}, None,
              wood("T_wooden_beam_01_BC", "T_wooden_beam_01_N", "T_Wooden_beam_01_ORM"), "Wood")
# Painted: the dark stripes, centred at 0.281 + 0.0441 * i and about 0.02 tall (measured).
STRIPES = {"VMin": 0.281, "VMax": 0.986, "Period": 0.0441, "BandH": 0.02}
make_instance("MI_BackAlleys_Boards_Blue", m, STRIPES, None,
              wood("T_wood_blue_BC", "T_wood_blue_N", "T_wood_blue_ORM"), "Wood")
make_instance("MI_BackAlleys_Boards_Green", m, STRIPES, None,
              wood("T_wood_green_BC", "T_wood_green_N", "T_wood_green_ORM"), "Wood")
# Flashing and ridge caps: plain galvanised, no planks. One huge "plank" and a band scaled to match, so the concrete detail
# maps continuously at 2 m a tile; our copy of T_Concrete_01 already exists.
make_instance("MI_BackAlleys_Flashing", m, {"PlankH": 100000.0, "Gap": -1.0, "TileCm": 200.0, "VMin": 0.0, "VMax": 500.0,
                                            "BandH": 500.0, "Metal": 0.9}, (0.62, 0.64, 0.66),
              {"BC": "T_Concrete_01_BC", "N": "T_Concrete_01_N", "ORM": "T_Concrete_01_ORM"}, "Metal")
