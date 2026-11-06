"""Headless, new assets only: the material for the user's posters and ads, and one instance per image. User 2026-11-05: "Added the Ads ... these
ads are AI generated, they are currently placeholder labeled. I might decide to use them but we will see. Now see what you can do with it".

The images in /Game/Project_Bopis_Posters are not touched: all the wear is in the material, so one image looks different on each wall.
- M_BackAlleys_PosterPaper: paper on a plane, masked. Each placed copy reads its own patch of T_BackAlleys_PosterWear, from where it stands: R tears
  the edges, G is grime, B says where the sun faded it. Tear, Fade, Dirt and WearScale are parameters; at 0 the image shows as supplied.
- Brightness 0.55 (user: "the material is bright even in shade"): the images reach full white, and the wall paints stop at about 0.55 (spec, Paint materials). This caps
  the posters at the same, without touching an image. At 1 they show as supplied.
- MI_BackAlleys_Poster_<name>: one per image. A texture set up as a normal map can't feed this material, so it's skipped and logged.

Close the editor first if the instances already exist. Run after make_street_textures.py: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_poster_materials_ue.py"""
import os

import unreal

SRC = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "import", "street")
ART = "/Game/Project_Bopis_Posters"
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
MATS = "/Game/ThirdPerson/BackAlleys/Materials"
WEAR = "T_BackAlleys_PosterWear"
MASTER = "M_BackAlleys_PosterPaper"
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary


def say(msg):
    unreal.log_warning("[POSTERMAT] " + msg)


def wear_texture():
    path = TEX + "/" + WEAR
    if eal.does_asset_exist(path):
        say(WEAR + " exists, kept")
        return unreal.load_asset(path)
    task = unreal.AssetImportTask()
    task.filename = os.path.join(SRC, WEAR + ".png")
    task.destination_path = TEX
    task.destination_name = WEAR
    task.automated = True
    task.save = False
    task.replace_existing = False
    tools.import_asset_tasks([task])
    tex = unreal.load_asset(path)
    tex.set_editor_property("compression_settings", unreal.TextureCompressionSettings.TC_MASKS)
    tex.set_editor_property("srgb", False)
    eal.save_loaded_asset(tex)
    say(WEAR + " imported")
    return tex


def build_master(first, wear):
    path = MATS + "/" + MASTER
    if eal.does_asset_exist(path):
        say(MASTER + " exists, kept")
        return unreal.load_asset(path)
    m = tools.create_asset(MASTER, MATS, unreal.Material, unreal.MaterialFactoryNew())
    x = [0]

    def node(cls, **props):
        x[0] += 1
        n = mel.create_material_expression(m, cls, -1400 + (x[0] % 6) * 220, -500 + (x[0] // 6) * 150)
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

    def const(v):
        return node(unreal.MaterialExpressionConstant, r=v)

    def scalar(name, v):
        return node(unreal.MaterialExpressionScalarParameter, parameter_name=name, default_value=v)

    def vec3(r, g, b):
        return node(unreal.MaterialExpressionConstant3Vector, constant=unreal.LinearColor(r, g, b, 1))

    def mask(a, **chans):
        n = node(unreal.MaterialExpressionComponentMask, **chans)
        wire(a, "", n, "")
        return n

    def one(cls, a):
        n = node(cls)
        wire(a, "", n, "")
        return n

    Mul, Add, Sub, Min, Dot = (unreal.MaterialExpressionMultiply, unreal.MaterialExpressionAdd, unreal.MaterialExpressionSubtract,
                               unreal.MaterialExpressionMin, unreal.MaterialExpressionDotProduct)
    Frac, Sat, OneMinus = unreal.MaterialExpressionFrac, unreal.MaterialExpressionSaturate, unreal.MaterialExpressionOneMinus

    uv = node(unreal.MaterialExpressionTextureCoordinate)
    u, v = mask(uv, r=True), mask(uv, g=True)
    edge = binary(Min, binary(Min, u, one(OneMinus, u)), binary(Min, v, one(OneMinus, v)))     # 0 at the paper's edge, 0.5 in the middle

    # Each copy's own numbers, from where it stands.
    where = mask(node(unreal.MaterialExpressionObjectPositionWS), r=True, g=True)
    offset = one(Frac, binary(Mul, where, const(0.0173)))
    k1 = one(Frac, binary(Dot, where, node(unreal.MaterialExpressionConstant2Vector, r=0.0371, g=0.0533)))
    k2 = one(Frac, binary(Mul, k1, const(7.13)))

    wear_uv = binary(Add, binary(Mul, uv, scalar("WearScale", 0.8)), offset)
    w = node(unreal.MaterialExpressionTextureSampleParameter2D, parameter_name="Wear", texture=wear,
             sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_MASKS)
    wire(wear_uv, "", w, "UVs")
    art = node(unreal.MaterialExpressionTextureSampleParameter2D, parameter_name="Poster", texture=first,
               sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    wire(uv, "", art, "UVs")

    # Tears start at the edges and reach about a tenth of the way in; some copies have hardly any.
    keep = binary(Add, mask(w, r=True), binary(Mul, edge, scalar("EdgeGain", 4.0)))
    tear = binary(Mul, scalar("Tear", 0.45), k1)
    opacity = one(Sat, binary(Mul, binary(Sub, keep, tear), const(12.0)))

    # Sun: colour goes first, and the darks lift towards the paper.
    grey = binary(Dot, art, vec3(0.3, 0.59, 0.11), "RGB")
    pale = binary(Add, binary(Mul, grey, vec3(0.86, 0.83, 0.75)), const(0.1))
    fade = one(Sat, binary(Mul, binary(Mul, scalar("Fade", 0.3), binary(Add, k2, const(0.25))), binary(Add, mask(w, b=True), const(0.6))))
    faded = node(unreal.MaterialExpressionLinearInterpolate)
    wire(art, "RGB", faded, "A")
    wire(pale, "", faded, "B")
    wire(fade, "", faded, "Alpha")

    # Grime.
    grime = node(unreal.MaterialExpressionLinearInterpolate)
    wire(vec3(1.0, 1.0, 1.0), "", grime, "A")
    wire(vec3(0.5, 0.45, 0.38), "", grime, "B")
    wire(one(Sat, binary(Mul, mask(w, g=True), scalar("Dirt", 1.0))), "", grime, "Alpha")
    colour = binary(Mul, binary(Mul, faded, grime), scalar("Brightness", 0.55))

    P = unreal.MaterialProperty
    ok = [mel.connect_material_property(colour, "", P.MP_BASE_COLOR), mel.connect_material_property(opacity, "", P.MP_OPACITY_MASK),
          mel.connect_material_property(const(0.82), "", P.MP_ROUGHNESS), mel.connect_material_property(const(0.3), "", P.MP_SPECULAR)]
    if not all(ok):
        say("output connections: %s" % ok)
    m.set_editor_property("blend_mode", unreal.BlendMode.BLEND_MASKED)
    m.set_editor_property("opacity_mask_clip_value", 0.5)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say(MASTER + " saved")
    return m


images = []
for path in eal.list_assets(ART, recursive=True, include_folder=False):
    a = unreal.load_asset(path)
    if isinstance(a, unreal.Texture2D):
        images.append(a)
say("%d images" % len(images))
usable = [t for t in images if t.get_editor_property("compression_settings") != unreal.TextureCompressionSettings.TC_NORMALMAP]
for t in images:
    if t not in usable:
        say("SKIPPED %s: set up as a normal map" % t.get_name())
wear = wear_texture()
master = build_master(usable[0], wear)
for t in usable:
    name = "MI_BackAlleys_Poster_" + t.get_name()
    if eal.does_asset_exist(MATS + "/" + name):
        # Moved to the current master here, with the editor closed. Doing it through the bridge, live, crashed the editor (LESSONS).
        mi = unreal.load_asset(MATS + "/" + name)
        if mi.get_editor_property("parent") != master:
            mi.set_editor_property("parent", master)
            mel.update_material_instance(mi)
            eal.save_loaded_asset(mi)
            say(name + " moved to " + MASTER)
        else:
            say(name + " exists, kept")
        continue
    mi = tools.create_asset(name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", master)
    mel.set_material_instance_texture_parameter_value(mi, "Poster", t)
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    say(name + " saved")
