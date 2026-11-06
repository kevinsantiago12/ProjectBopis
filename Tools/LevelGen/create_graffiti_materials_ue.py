"""Headless: the decal material for the user's graffiti, and an instance per image and paint. User 2026-11-06: "added 10 graffitits", then "the warning and tag decals are to faded". The images in
/Game/Project_Bopis_Graffiti_Decals aren't touched: they are white-on-black masks, and the paint and the wear are all in the material.
- M_BackAlleys_SprayDecal: a deferred decal. Opacity is the mask times Solid, held at 1: the masks' ink reads 0.75-0.95 once sampled (they're sRGB, medians 224-249), so without this nothing is ever
  fully painted. Then a little of T_BackAlleys_PosterWear's sun fade, from where it stands, so one image differs from wall to wall. Solid 1, Strength 1 and Wear 0 show the mask as supplied.
- MI_BackAlleys_Spray_<name>_<paint>: Paint is its colour.
Replaces M_BackAlleys_GraffitiDecal and MI_BackAlleys_Graffiti_*, at new names, because a headless run can't change what the open editor has loaded. Delete those once the editor has closed.
The tint and texture calls can return False even when they take: the log line reads the paint back.

Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\create_graffiti_materials_ue.py"""
import unreal

ART = "/Game/Project_Bopis_Graffiti_Decals/"
MATS = "/Game/ThirdPerson/BackAlleys/Materials"
WEAR = "/Game/ThirdPerson/BackAlleys/Textures/T_BackAlleys_PosterWear"
MASTER = "M_BackAlleys_SprayDecal"
PAINT = {"Black": (0.008, 0.008, 0.01), "Red": (0.42, 0.03, 0.02), "White": (0.75, 0.74, 0.69), "Blue": (0.03, 0.09, 0.34)}
# gen_level.py GRAF_TAGS and GRAF_SIGNS: which paints each image comes in.
IMAGES = {"Crew_Tags/Bakod_7": ("Black", "Red"), "Crew_Tags/Eskinita_13": ("White", "Blue"), "Crew_Tags/Kanto_Boys": ("Black", "Blue"), "Crew_Tags/Loob_Crew": ("Black", "White"),
          "Crew_Tags/Siksik": ("Red", "Black"), "Warnings/Bawal_Magtapon_ng_Basura": ("Black", "Red"), "Warnings/Bawal_Pumarada": ("White", "Red"), "Warnings/Bawal_Pumasok": ("Red", "White"),
          "Warnings/Bawal_Umihi_Dito": ("Black", "Red"), "Warnings/Huwag_Harangan_ang_Daan": ("Black", "White")}
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
P = unreal.MaterialProperty
E = unreal


def say(msg):
    unreal.log_warning("[GRAFMAT] " + msg)


def build(first):
    path = MATS + "/" + MASTER
    if eal.does_asset_exist(path):      # its graph is rebuilt, and the instances keep their settings. Close the editor first if the level uses them
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

    mask = node(E.MaterialExpressionTextureSampleParameter2D, parameter_name="Mask", texture=first, sampler_type=E.MaterialSamplerType.SAMPLERTYPE_COLOR)
    paint = node(E.MaterialExpressionVectorParameter, parameter_name="Paint", default_value=E.LinearColor(0.008, 0.008, 0.01, 1.0))
    solid = node(E.MaterialExpressionScalarParameter, parameter_name="Solid", default_value=1.35)
    strength = node(E.MaterialExpressionScalarParameter, parameter_name="Strength", default_value=1.0)
    wear_amt = node(E.MaterialExpressionScalarParameter, parameter_name="Wear", default_value=0.12)
    wear_scale = node(E.MaterialExpressionScalarParameter, parameter_name="WearScale", default_value=0.0035)
    pos = node(E.MaterialExpressionWorldPosition)


    def axis(**which):
        n = node(E.MaterialExpressionComponentMask, r=False, g=False, b=False, a=False, **{})
        for k, v in which.items():
            n.set_editor_property(k, v)
        wire(pos, "", n, "")
        return n

    along = binary(E.MaterialExpressionAdd, axis(r=True), axis(g=True))
    uv = binary(E.MaterialExpressionAppendVector, along, axis(b=True))
    uv_s = binary(E.MaterialExpressionMultiply, uv, wear_scale)
    wear = node(E.MaterialExpressionTextureSample, texture=unreal.load_asset(WEAR), sampler_type=E.MaterialSamplerType.SAMPLERTYPE_MASKS)
    wire(uv_s, "", wear, "UVs")
    fade = binary(E.MaterialExpressionMultiply, wear, wear_amt, "B", "")
    keep = node(E.MaterialExpressionOneMinus)
    wire(fade, "", keep, "")
    ink = node(E.MaterialExpressionSaturate)
    wire(binary(E.MaterialExpressionMultiply, mask, solid, "R", ""), "", ink, "")
    opacity = binary(E.MaterialExpressionMultiply, binary(E.MaterialExpressionMultiply, ink, strength), keep)
    rough = node(E.MaterialExpressionConstant, r=0.72)
    spec = node(E.MaterialExpressionConstant, r=0.3)
    metal = node(E.MaterialExpressionConstant, r=0.0)
    ok = [mel.connect_material_property(paint, "", P.MP_BASE_COLOR), mel.connect_material_property(opacity, "", P.MP_OPACITY), mel.connect_material_property(rough, "", P.MP_ROUGHNESS),
          mel.connect_material_property(spec, "", P.MP_SPECULAR), mel.connect_material_property(metal, "", P.MP_METALLIC)]
    say("outputs %s" % ok)
    m.set_editor_property("blend_mode", E.BlendMode.BLEND_TRANSLUCENT)
    m.set_editor_property("material_domain", E.MaterialDomain.MD_DEFERRED_DECAL)     # last: an opaque decal won't compile
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say(MASTER + " made")
    return m


def tex(key):
    folder, name = key.split("/")
    return unreal.load_asset(ART + folder + "/T_Graffiti_" + name + "_MSK")


master = build(tex("Crew_Tags/Bakod_7"))
for key, paints in IMAGES.items():
    name = key.split("/")[1]
    for colour in paints:
        mi_name = "MI_BackAlleys_Spray_%s_%s" % (name, colour)
        path = MATS + "/" + mi_name
        if eal.does_asset_exist(path):
            say(mi_name + " exists, kept")
            continue
        mi = tools.create_asset(mi_name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
        mel.set_material_instance_parent(mi, master)
        mel.set_material_instance_texture_parameter_value(mi, "Mask", tex(key))
        r, g, b = PAINT[colour]
        mel.set_material_instance_vector_parameter_value(mi, "Paint", E.LinearColor(r, g, b, 1.0))
        mel.update_material_instance(mi)
        eal.save_loaded_asset(mi)
        say("%s: mask %s, paint %s" % (mi_name, mel.get_material_instance_texture_parameter_value(mi, "Mask").get_name(), mel.get_material_instance_vector_parameter_value(mi, "Paint")))
