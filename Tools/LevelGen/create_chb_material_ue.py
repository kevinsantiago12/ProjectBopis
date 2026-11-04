"""Headless: creates M_BackAlleys_CHB, a procedural concrete-hollow-block (CHB) wall material, and its instances.
User 2026-11-03: "Make a CHB material" (no pack has CHB; MiddleEast's T_Brick_wall read as rough stone).

The blocks are drawn in the shader, in world space, so stretched Favela tiles don't stretch them and they line up across
tile seams. All back-alley walls are axis-aligned, so x + y runs along any wall and z runs up it.
- Blocks: 40 x 20 cm, running bond (every other course offset half a block), 1 cm mortar drawn darker and rougher,
  each block toned slightly differently. Surface detail comes from a concrete texture, desaturated.
- Render (optional): a concrete or paint layer over the blocks, chipped away where the height mask (Favela's T_Wall_H,
  as M_Bricks_Bland_01 uses it) falls below 1 - RenderCoverage, with a dark rim at the chip edge.
Instances: MI_BackAlleys_CHB_Bare (coverage 0), _Concrete (0.8), _PaintWhite / _PaintYellow / _PaintBlue (0.75), and
MI_BackAlleys_Concrete (1.0: plain render, for the floor bands).
Everything lives under /Game/ThirdPerson/BackAlleys/, with our own copies of the pack textures it uses (Textures/), so
nothing we make depends on a pack's materials or textures (user 2026-11-03: "isolate any new materials we created
outside the external assets").
The material is compiled by the open editor when the level uses it; errors show in Saved/Logs/ProjectBopis.log.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_chb_material_ue.py"""
import unreal

DEST = "/Game/ThirdPerson/BackAlleys/Materials"
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
PACK_TEX = ("/Game/Megapack/Textures/Favela/",)
MAT = "M_BackAlleys_CHB"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
phys = unreal.load_asset("/Game/ImpactsVFXVol1/Materials/Physical_Materials/Concrete")   # the project's Concrete surface


def say(msg):
    unreal.log_warning("[CHB] " + msg)


# Shared HLSL: block mask (1 = block face, 0 = mortar), per-block random, render mask (1 = render), chip-edge rim.
MASKS = """
float u = (WP.x + WP.y) / BlockW;
float v = WP.z / BlockH;
float row = floor(v);
u += frac(row * 0.5);
float2 id = float2(floor(u), row);
float fu = frac(u), fv = frac(v);
float d = min(min(fu, 1 - fu) * BlockW, min(fv, 1 - fv) * BlockH);
float block = saturate((d - Mortar * 0.5) / 0.4);
float rnd = frac(sin(dot(id, float2(12.9898, 78.233))) * 43758.5453);
float t = 1.0 - Coverage;
float r = Coverage > 0.001 ? smoothstep(t - 0.03, t + 0.03, ChipH) : 0.0;
float rim = Coverage > 0.001 ? (1 - saturate(abs(ChipH - t) / 0.05)) * (1 - r) : 0.0;
"""
NODES = {
    "UV": ("return float2((WP.x + WP.y) / Tile, -WP.z / Tile);", "CMOT_FLOAT2", ["WP", "Tile"]),
    "Color": (MASKS + """
float3 grey = dot(BlockBC, float3(0.3, 0.59, 0.11)) * BlockTint;
float3 chb = lerp(grey * 0.5, grey * (0.82 + 0.36 * rnd), block);
chb *= 1 - 0.45 * rim;
return lerp(chb, RenderBC * RenderTint, r);""", "CMOT_FLOAT3",
              ["WP", "BlockBC", "RenderBC", "ChipH", "Coverage", "BlockTint", "RenderTint", "BlockW", "BlockH", "Mortar"]),
    "RoughAO": (MASKS + """
float rough = lerp(lerp(0.95, 0.85, block), RenderORM.g, r);
float ao = lerp(lerp(0.45, 1.0, block) * (1 - 0.4 * rim), RenderORM.r, r);
return float2(rough, ao);""", "CMOT_FLOAT2",
                ["WP", "RenderORM", "ChipH", "Coverage", "BlockW", "BlockH", "Mortar"]),
    "Normal": (MASKS + """
float3 bn = normalize(lerp(float3(0, 0, 1), BlockN, 0.6));
return normalize(lerp(bn, RenderN, r));""", "CMOT_FLOAT3",
               ["WP", "BlockN", "RenderN", "ChipH", "Coverage", "BlockW", "BlockH", "Mortar"]),
}


def custom_input(name):
    ci = unreal.CustomInput()
    ci.set_editor_property("input_name", name)
    return ci


def local_texture(name):
    """Our own copy of a pack texture, so nothing we make depends on the packs (user 2026-11-03: "isolate any new
    materials we created outside the external assets")."""
    path = TEX + "/" + name
    if not eal.does_asset_exist(path):
        src = next(p + name for p in PACK_TEX if eal.does_asset_exist(p + name))
        eal.duplicate_asset(src, path)
        if not eal.save_asset(path, only_if_is_dirty=False):
            say("FAILED to save %s" % path)
        say("copied %s -> %s" % (src, path))
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
    path = DEST + "/" + MAT
    if eal.does_asset_exist(path):
        eal.delete_asset(path)
    m = tools.create_asset(MAT, DEST, unreal.Material, unreal.MaterialFactoryNew())
    x = -1600

    def node(cls, y, xx=None):
        return mel.create_material_expression(m, cls, xx if xx is not None else x, y)

    wp = node(unreal.MaterialExpressionWorldPosition, 0, -2200)
    scal = {}
    for i, (name, val) in enumerate((("Coverage", 0.0), ("Tile", 200.0), ("BlockW", 40.0), ("BlockH", 20.0),
                                     ("Mortar", 1.0))):
        s = node(unreal.MaterialExpressionScalarParameter, 200 + 90 * i, -2200)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("default_value", val)
        scal[name] = s
    vec = {}
    for i, (name, val) in enumerate((("BlockTint", (0.62, 0.62, 0.6)), ("RenderTint", (1.0, 1.0, 1.0)))):
        p = node(unreal.MaterialExpressionVectorParameter, 700 + 120 * i, -2200)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", unreal.LinearColor(val[0], val[1], val[2], 1))
        vec[name] = p

    customs = {}
    for i, (key, (code, out, ins)) in enumerate(NODES.items()):
        c = node(unreal.MaterialExpressionCustom, -200 + 400 * i, -1800 if key == "UV" else -400)
        c.set_editor_property("code", code)
        c.set_editor_property("output_type", getattr(unreal.CustomMaterialOutputType, out))
        c.set_editor_property("description", "CHB_" + key)
        c.set_editor_property("inputs", [custom_input(n) for n in ins])
        customs[key] = c

    tex = {}
    for i, (name, asset) in enumerate((("BlockBC", "T_Concrete_01_BC"), ("BlockN", "T_Concrete_01_N"),
                                        ("RenderBC", "T_Concrete_01_BC"), ("RenderN", "T_Concrete_01_N"),
                                        ("RenderORM", "T_Concrete_01_ORM"), ("ChipH", "T_Wall_H"))):
        t = local_texture(asset)
        s = node(unreal.MaterialExpressionTextureSampleParameter2D, -1500 + 260 * i, -1200)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("texture", t)
        s.set_editor_property("sampler_type", sampler_for(t))
        mel.connect_material_expressions(customs["UV"], "", s, "UVs")
        tex[name] = s

    def link(src, out_name, key, in_name):
        if not mel.connect_material_expressions(src, out_name, customs[key], in_name):
            say("connect failed: %s.%s -> %s.%s" % (src.get_name(), out_name, key, in_name))

    link(wp, "", "UV", "WP")
    link(scal["Tile"], "", "UV", "Tile")
    for key in ("Color", "RoughAO", "Normal"):
        link(wp, "", key, "WP")
        for name in ("Coverage", "BlockW", "BlockH", "Mortar"):
            link(scal[name], "", key, name)
        link(tex["ChipH"], "R", key, "ChipH")
    link(tex["BlockBC"], "RGB", "Color", "BlockBC")
    link(tex["RenderBC"], "RGB", "Color", "RenderBC")
    link(vec["BlockTint"], "", "Color", "BlockTint")
    link(vec["RenderTint"], "", "Color", "RenderTint")
    link(tex["RenderORM"], "RGB", "RoughAO", "RenderORM")
    link(tex["BlockN"], "RGB", "Normal", "BlockN")
    link(tex["RenderN"], "RGB", "Normal", "RenderN")

    rough = node(unreal.MaterialExpressionComponentMask, -100, 600)
    rough.set_editor_property("r", False)
    rough.set_editor_property("g", True)
    ao = node(unreal.MaterialExpressionComponentMask, -100, 760)
    ao.set_editor_property("r", True)
    mel.connect_material_expressions(customs["RoughAO"], "", rough, "")
    mel.connect_material_expressions(customs["RoughAO"], "", ao, "")

    P = unreal.MaterialProperty
    ok = [mel.connect_material_property(customs["Color"], "", P.MP_BASE_COLOR),
          mel.connect_material_property(rough, "", P.MP_ROUGHNESS),
          mel.connect_material_property(ao, "", P.MP_AMBIENT_OCCLUSION),
          mel.connect_material_property(customs["Normal"], "", P.MP_NORMAL)]
    if not all(ok):
        say("material output connections: %s" % ok)
    if phys:
        m.set_editor_property("phys_material", phys)
    mel.layout_material_expressions(m)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say("%s saved, %d expressions" % (MAT, mel.get_num_material_expressions(m)))
    return m


def make_instance(name, parent, scalars, vectors, textures):
    path = DEST + "/" + name
    if eal.does_asset_exist(path) and not REBUILD:
        say("%s exists, kept" % name)
        return
    mi =unreal.load_asset(path) if eal.does_asset_exist(path) else \
        tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    for k, v in scalars.items():
        mel.set_material_instance_scalar_parameter_value(mi, k, v)
    for k, v in vectors.items():
        mel.set_material_instance_vector_parameter_value(mi, k, unreal.LinearColor(v[0], v[1], v[2], 1))
    for k, v in textures.items():
        mel.set_material_instance_texture_parameter_value(mi, k, local_texture(v))
    if phys:
        mi.set_editor_property("phys_material", phys)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say("%s saved" % name)


# Existing assets are kept unless REBUILD: the open editor has the level's materials loaded and locked, and rebuilding
# them headless isn't safe (2026-11-03: a run tried to force-delete the master; the editor's file lock stopped it).
# New instances are always fine. Set REBUILD only with the editor closed.
REBUILD = False
MAT_PATH = DEST + "/" + MAT
m = build_material() if REBUILD or not eal.does_asset_exist(MAT_PATH) else unreal.load_asset(MAT_PATH)
make_instance("MI_BackAlleys_CHB_Bare", m, {"Coverage": 0.0}, {}, {})
make_instance("MI_BackAlleys_CHB_Concrete", m, {"Coverage": 0.8}, {"RenderTint": (0.95, 0.95, 0.93)}, {})
make_instance("MI_BackAlleys_Concrete", m, {"Coverage": 1.0}, {"RenderTint": (0.9, 0.9, 0.88)}, {})   # bands: full render
for key, first in (("PaintWhite", "T_plaster_01"), ("PaintYellow", "T_Wall_yellow_01"), ("PaintBlue", "T_Wall_Blue_01")):
    make_instance("MI_BackAlleys_CHB_" + key, m, {"Coverage": 0.75}, {},
                  {"RenderBC": first + "_BC", "RenderN": first + "_N", "RenderORM": first + "_ORM"})

# Colour variants (user 2026-11-03: "make more variant colors of MI_BackAlleys_CHB"). House paints are a tinted white
# plaster render (2002 Manila: pastel paint over CHB); concretes and bare blocks vary in tone.
PLASTER = {"RenderBC": "T_plaster_01_BC", "RenderN": "T_plaster_01_N", "RenderORM": "T_plaster_01_ORM"}
for key, tint in (("Mint", (0.55, 0.80, 0.62)), ("Pink", (0.92, 0.62, 0.64)), ("SkyBlue", (0.55, 0.72, 0.92)),
                  ("Cream", (0.96, 0.88, 0.70)), ("Peach", (0.96, 0.70, 0.50)), ("Lime", (0.72, 0.86, 0.45)),
                  ("Lavender", (0.74, 0.66, 0.86)), ("Teal", (0.40, 0.70, 0.70)), ("Salmon", (0.90, 0.52, 0.42)),
                  ("PaleYellow", (0.95, 0.92, 0.55))):
    make_instance("MI_BackAlleys_CHB_Paint" + key, m, {"Coverage": 0.72}, {"RenderTint": tint}, PLASTER)
make_instance("MI_BackAlleys_CHB_ConcreteWarm", m, {"Coverage": 0.8}, {"RenderTint": (0.98, 0.9, 0.78)}, {})
make_instance("MI_BackAlleys_CHB_ConcreteDark", m, {"Coverage": 0.8}, {"RenderTint": (0.62, 0.62, 0.62)}, {})
make_instance("MI_BackAlleys_CHB_BareLight", m, {"Coverage": 0.0}, {"BlockTint": (0.78, 0.77, 0.74)}, {})
make_instance("MI_BackAlleys_CHB_BareDark", m, {"Coverage": 0.0}, {"BlockTint": (0.46, 0.46, 0.45)}, {})
