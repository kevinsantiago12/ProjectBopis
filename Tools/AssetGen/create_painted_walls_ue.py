"""Headless: the paint look of Favela's wall decals, as a wall material and as decals, in Philippine house colours.
User 2026-11-04: "The decals look good becuase they have imperfections, ie concrete base color coming through. What I
need a wall material based of the look of the decal paints, and variants of the decal of usual philippine house colors,
so I can use it if I want the color change outside of the tile face boundaries."

Favela's paint decal (M_Decal_01) is a flat colour shown through a mask, T_decal_02: fine specks, scratches and worn
patches inside a rough edge. The surface below keeps its normal and shows through the marks.

- M_BackAlleys_PaintDecal + MI_BackAlleys_PaintDecal_<Colour>: that decal, with our own copy of the mask. For colour
  that crosses tile faces. Overdraw cost per covered pixel: keep it to where it's needed.
- M_BackAlleys_PaintedWall + MI_BackAlleys_PaintedWall_<Colour>: T_Concrete_01 with the same paint on top, for whole
  tile faces, in one pass. World-aligned like M_BackAlleys_CHB (x + y along the wall, z up: axis-aligned walls only), so
  stretched tiles don't stretch it and its wear runs on across tiles. The same flat colour and roughness as the decal,
  so a decal continues a painted wall in the same colour.
  - The mask here is T_BackAlleys_PaintChips (make_paint_mask.ps1), the inside of T_decal_02 cut to tile. It's sampled at
    two scales, switched by a large blotch (the concrete's own colour at PatchTile), so its marks don't repeat at MaskTile.
    Not T_Wall_H: that's a brick wall's height map, so anything it drives wears away in brick shapes.
  - Wear: 0 is the decal's own coverage; higher thins the paint. PatchWear: bigger soft bare patches (0 = none).

Everything lives under /Game/ThirdPerson/BackAlleys (nothing depends on a pack). New assets only: anything that exists is
kept, because the open editor may have it loaded.

Run with rendering, so the shaders compile and get_statistics reports them:
.\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\AssetGen\\create_painted_walls_ue.py -Render"""
import os

import unreal

DEST = "/Game/ThirdPerson/BackAlleys/Materials"
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
PACK_MASK = "/Game/Megapack/Textures/Favela/Decals/T_decal_02"
SRC = os.path.join(unreal.Paths.project_saved_dir(), "AssetGen", "import", "paint_mask")
WALL, DECAL = "M_BackAlleys_PaintedWall", "M_BackAlleys_PaintDecal"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
phys = unreal.load_asset("/Game/ImpactsVFXVol1/Materials/Physical_Materials/Concrete")   # the project's Concrete surface

# Dusty, sun-faded house paint: sRGB, as a colour picker shows it. Close to the Favela paint decals, which peak near 0.34
# linear (these reach about 0.55): much brighter and the chips turn stark against the dark T_Concrete_01.
COLOURS = {"White": "C2BEB0", "Cream": "C4B993", "Yellow": "C2AA68", "Peach": "BF9478", "Salmon": "B5806E",
           "Pink": "B88E92", "Mint": "8FAF96", "AppleGreen": "98A76E", "SkyBlue": "84A3B5", "Teal": "6C9691",
           "Lavender": "9E93AE", "Terracotta": "A07059"}
PAINT_ROUGH = 0.55

NODES = {
    "Paint": ("""
float blotch = saturate((dot(Blotch, float3(0.3, 0.59, 0.11)) - 0.08) / 0.05);   // T_Concrete_01_BC spans about 0.08-0.13
float chips = lerp(M1, M2, smoothstep(0.32, 0.52, blotch));
float paint = saturate((chips - Wear) / max(1 - Wear, 0.001));
if (PatchWear > 0.001)
    paint *= smoothstep(PatchWear - 0.08, PatchWear + 0.08, blotch);
return paint;""", "CMOT_FLOAT1", ["M1", "M2", "Blotch", "Wear", "PatchWear"]),
    "Color": ("return lerp(BC * ConcreteTint, PaintColor, Paint);", "CMOT_FLOAT3",
              ["BC", "ConcreteTint", "PaintColor", "Paint"]),
    "Rough": ("return lerp(ORM.g, PaintRough, Paint);", "CMOT_FLOAT1", ["ORM", "PaintRough", "Paint"]),
}
# World-aligned UVs: x + y runs along any axis-aligned wall. The second mask sample is turned 90 degrees and rescaled.
UV_NORMAL = "return float2((WP.x + WP.y) / Tile, -WP.z / Tile);"
UV_TURNED = "return float2(-WP.z / (Tile * 0.73) + 0.37, (WP.x + WP.y) / (Tile * 0.73) + 0.61);"


def say(msg):
    unreal.log_warning("[PAINT] " + msg)


def linear(hexcode):
    def f(c):
        c /= 255.0
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4
    return tuple(f(int(hexcode[i:i + 2], 16)) for i in (0, 2, 4))


def custom_input(name):
    ci = unreal.CustomInput()
    ci.set_editor_property("input_name", name)
    return ci


def sampler_for(tex):
    cs = tex.get_editor_property("compression_settings")
    if cs == unreal.TextureCompressionSettings.TC_NORMALMAP:
        return unreal.MaterialSamplerType.SAMPLERTYPE_NORMAL
    if not tex.get_editor_property("srgb"):
        return unreal.MaterialSamplerType.SAMPLERTYPE_LINEAR_COLOR
    return unreal.MaterialSamplerType.SAMPLERTYPE_COLOR


def texture_copy(src, name):
    path = TEX + "/" + name
    if not eal.does_asset_exist(path):
        eal.duplicate_asset(src, path)
        eal.save_asset(path, only_if_is_dirty=False)
        say("copied %s -> %s" % (src, path))
    return unreal.load_asset(path)


def import_mask(name):
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
    eal.save_loaded_asset(tex)
    say("%s imported (%s, sRGB %s)" % (name, tex.get_editor_property("compression_settings"),
                                       tex.get_editor_property("srgb")))
    return tex


def build_decal(mask):
    m = tools.create_asset(DECAL, DEST, unreal.Material, unreal.MaterialFactoryNew())

    def node(cls, x, y):
        return mel.create_material_expression(m, cls, x, y)

    col = node(unreal.MaterialExpressionVectorParameter, -500, -200)
    col.set_editor_property("parameter_name", "PaintColor")
    col.set_editor_property("default_value", unreal.LinearColor(0.6, 0.6, 0.5, 1))
    rough = node(unreal.MaterialExpressionScalarParameter, -500, 0)
    rough.set_editor_property("parameter_name", "PaintRough")
    rough.set_editor_property("default_value", PAINT_ROUGH)
    spec = node(unreal.MaterialExpressionConstant, -500, 100)
    spec.set_editor_property("r", 0.5)
    metal = node(unreal.MaterialExpressionConstant, -500, 200)
    metal.set_editor_property("r", 0.0)
    s = node(unreal.MaterialExpressionTextureSampleParameter2D, -500, 300)
    s.set_editor_property("parameter_name", "Mask")
    s.set_editor_property("texture", mask)
    s.set_editor_property("sampler_type", sampler_for(mask))
    P = unreal.MaterialProperty
    ok = [mel.connect_material_property(col, "", P.MP_BASE_COLOR), mel.connect_material_property(rough, "", P.MP_ROUGHNESS),
          mel.connect_material_property(spec, "", P.MP_SPECULAR), mel.connect_material_property(metal, "", P.MP_METALLIC),
          mel.connect_material_property(s, "R", P.MP_OPACITY)]
    if not all(ok):
        say("decal output connections: %s" % ok)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("material_domain", unreal.MaterialDomain.MD_DEFERRED_DECAL)   # last: an opaque decal won't compile
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say("%s saved" % DECAL)
    return m


def build_wall(chips):
    m = tools.create_asset(WALL, DEST, unreal.Material, unreal.MaterialFactoryNew())

    def node(cls, x, y):
        return mel.create_material_expression(m, cls, x, y)

    def custom(desc, code, out, ins, x, y):
        c = node(unreal.MaterialExpressionCustom, x, y)
        c.set_editor_property("code", code)
        c.set_editor_property("output_type", getattr(unreal.CustomMaterialOutputType, out))
        c.set_editor_property("description", desc)
        c.set_editor_property("inputs", [custom_input(n) for n in ins])
        return c

    def link(src, out_name, dst, in_name):
        if not mel.connect_material_expressions(src, out_name, dst, in_name):
            say("connect failed: %s.%s -> %s.%s" % (src.get_name(), out_name, dst.get_name(), in_name))

    def scalar(name, val, y):
        s = node(unreal.MaterialExpressionScalarParameter, -2200, y)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("default_value", val)
        return s

    def vector(name, val, y):
        p = node(unreal.MaterialExpressionVectorParameter, -2200, y)
        p.set_editor_property("parameter_name", name)
        p.set_editor_property("default_value", unreal.LinearColor(val[0], val[1], val[2], 1))
        return p

    def sample(name, tex, uv, y):
        s = node(unreal.MaterialExpressionTextureSampleParameter2D, -1300, y)
        s.set_editor_property("parameter_name", name)
        s.set_editor_property("texture", tex)
        s.set_editor_property("sampler_type", sampler_for(tex))
        mel.connect_material_expressions(uv, "", s, "UVs")
        return s

    wp = node(unreal.MaterialExpressionWorldPosition, -2200, -800)
    tile = scalar("ConcreteTile", 200.0, -700)      # as M_BackAlleys_CHB's Tile, so it matches plain concrete walls
    mask_tile = scalar("MaskTile", 270.0, -600)     # the crop is about 2.7 m at the Favela decals' usual size
    patch_tile = scalar("PatchTile", 430.0, -500)
    wear = scalar("Wear", 0.0, -400)
    patch = scalar("PatchWear", 0.0, -300)
    rough_p = scalar("PaintRough", PAINT_ROUGH, -200)
    tint = vector("ConcreteTint", (0.9, 0.9, 0.88), -100)   # MI_BackAlleys_Concrete's RenderTint
    paint_c = vector("PaintColor", (0.6, 0.6, 0.5), 50)

    uvs = {}
    for i, (key, code, t) in enumerate((("Concrete", UV_NORMAL, tile), ("Mask1", UV_NORMAL, mask_tile),
                                        ("Mask2", UV_TURNED, mask_tile), ("Patch", UV_NORMAL, patch_tile))):
        c = custom("UV_" + key, code, "CMOT_FLOAT2", ["WP", "Tile"], -1700, -800 + 200 * i)
        link(wp, "", c, "WP")
        link(t, "", c, "Tile")
        uvs[key] = c

    bc = sample("ConcreteBC", unreal.load_asset(TEX + "/T_Concrete_01_BC"), uvs["Concrete"], -800)
    nm = sample("ConcreteN", unreal.load_asset(TEX + "/T_Concrete_01_N"), uvs["Concrete"], -500)
    orm = sample("ConcreteORM", unreal.load_asset(TEX + "/T_Concrete_01_ORM"), uvs["Concrete"], -200)
    m1 = sample("Chips", chips, uvs["Mask1"], 100)
    m2 = sample("Chips", chips, uvs["Mask2"], 400)
    blotch = sample("ConcreteBC", unreal.load_asset(TEX + "/T_Concrete_01_BC"), uvs["Patch"], 700)

    code, out, ins = NODES["Paint"]
    paint = custom("Paint", code, out, ins, -700, 300)
    link(m1, "R", paint, "M1")
    link(m2, "R", paint, "M2")
    link(blotch, "RGB", paint, "Blotch")
    link(wear, "", paint, "Wear")
    link(patch, "", paint, "PatchWear")
    code, out, ins = NODES["Color"]
    color = custom("Color", code, out, ins, -300, -400)
    link(bc, "RGB", color, "BC")
    link(tint, "", color, "ConcreteTint")
    link(paint_c, "", color, "PaintColor")
    link(paint, "", color, "Paint")
    code, out, ins = NODES["Rough"]
    rough = custom("Rough", code, out, ins, -300, 0)
    link(orm, "RGB", rough, "ORM")
    link(rough_p, "", rough, "PaintRough")
    link(paint, "", rough, "Paint")
    ao = node(unreal.MaterialExpressionComponentMask, -300, 300)
    ao.set_editor_property("r", True)
    mel.connect_material_expressions(orm, "RGB", ao, "")

    P = unreal.MaterialProperty
    ok = [mel.connect_material_property(color, "", P.MP_BASE_COLOR), mel.connect_material_property(rough, "", P.MP_ROUGHNESS),
          mel.connect_material_property(ao, "", P.MP_AMBIENT_OCCLUSION),
          mel.connect_material_property(nm, "RGB", P.MP_NORMAL)]
    if not all(ok):
        say("wall output connections: %s" % ok)
    if phys:
        m.set_editor_property("phys_material", phys)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say("%s saved, %d expressions" % (WALL, mel.get_num_material_expressions(m)))
    return m


def make_instance(name, parent, colour):
    path = DEST + "/" + name
    if eal.does_asset_exist(path):
        say("%s exists, kept" % name)
        return
    mi = tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", parent)
    mel.set_material_instance_vector_parameter_value(mi, "PaintColor", unreal.LinearColor(colour[0], colour[1], colour[2], 1))
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)


def stats(path):
    """Finishes compiling the material and reports it: zero pixel instructions means it failed."""
    st = mel.get_statistics(unreal.load_asset(path))
    say("%s: pixel %d, vertex %d, samplers %d" % (path.split("/")[-1], st.get_editor_property("num_pixel_shader_instructions"),
                                                  st.get_editor_property("num_vertex_shader_instructions"),
                                                  st.get_editor_property("num_samplers")))


# Replaces this script's materials. Only before anything uses them: never with the open editor having them loaded.
REBUILD = False
if REBUILD:
    for key in COLOURS:
        for name in ("MI_BackAlleys_PaintedWall_" + key, "MI_BackAlleys_PaintDecal_" + key):
            if eal.does_asset_exist(DEST + "/" + name):
                eal.delete_asset(DEST + "/" + name)
    for name in (WALL, DECAL):
        if eal.does_asset_exist(DEST + "/" + name):
            eal.delete_asset(DEST + "/" + name)
mask = texture_copy(PACK_MASK, "T_decal_02")
chips = import_mask("T_BackAlleys_PaintChips")
wall = unreal.load_asset(DEST + "/" + WALL) if eal.does_asset_exist(DEST + "/" + WALL) else build_wall(chips)
decal = unreal.load_asset(DEST + "/" + DECAL) if eal.does_asset_exist(DEST + "/" + DECAL) else build_decal(mask)
for key, hexcode in COLOURS.items():
    colour = linear(hexcode)
    make_instance("MI_BackAlleys_PaintedWall_" + key, wall, colour)
    make_instance("MI_BackAlleys_PaintDecal_" + key, decal, colour)
say("%d colours" % len(COLOURS))
for p in (DEST + "/" + WALL, DEST + "/" + DECAL, DEST + "/M_BackAlleys_CHB"):
    stats(p)
