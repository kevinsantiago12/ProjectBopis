"""Headless, new assets only: the lettered sign boards. User 2026-11-07: "Project_Bopis_Local_Business_Signs Added, use this for new posters (add, dont
replace the ones already there), then add the signage to the apprpriate signboards".

The five images in /Game/Project_Bopis_Local_Business_Signs/Wall_Boards are not touched. Each is 1850 x 500 with the painted board in the middle and a
plain backdrop either side, so the material crops to the board (BoardMin/BoardSize, in the image's UV) and lays it on SM_Sign_A_001's front panel.
- SM_Sign_A_001's slot 0 (section 0, the board) is one atlas: the front panel, local +Y, the street side, is the rectangle u 0.041-0.462, v 0.788-0.963,
  left to right and top down as seen from the street (analysis/sign_uv_ue.py). PanelMin/PanelSize. Everything outside it (the board's edges, its back)
  keeps a blank sign's paint, in the board's own colour.
- Brightness 0.55, as the posters: the images reach full white, the wall paints stop at about 0.55 ("the material is bright even in shade").
- Wood: they're painted planks, nail holes and grain.
gen_level.py's SIGN_BOARDS holds the same crop, to size each sign to its board so nothing is stretched.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_sign_boards_ue.py"""
import unreal

ART = "/Game/Project_Bopis_Local_Business_Signs/Wall_Boards"
TEX = "/Game/ThirdPerson/BackAlleys/Textures"
MATS = "/Game/ThirdPerson/BackAlleys/Materials"
WOOD = "/Game/ImpactsVFXVol1/Materials/Physical_Materials/Wood"
MASTER = "M_BackAlleys_SignBoard"
IMG_W, IMG_H = 1850.0, 500.0
# The board's columns in the image (measured: where the backdrop ends, three rows), and the blank paint for its edges.
BOARDS = {"06_Sari_Sari": (232, 1617, "White"), "07_Barberya": (174, 1674, "Blue"), "08_Patahian": (230, 1620, "White"),
          "09_Xerox": (254, 1594, "Yellow"), "10_Carinderia": (252, 1597, "White")}
INSET = 2.0           # px off each cut, so filtering never pulls in the backdrop
PANEL = (0.041, 0.788, 0.421, 0.175)
tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary


def say(msg):
    unreal.log_warning("[SIGNBOARD] " + msg)


def build_master(first, paint):
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

    def vec2(name, a, b):
        p = node(unreal.MaterialExpressionVectorParameter, parameter_name=name, default_value=unreal.LinearColor(a, b, 0, 0))
        n = node(unreal.MaterialExpressionComponentMask, r=True, g=True)
        wire(p, "", n, "")
        return n

    def mask(a, **chans):
        n = node(unreal.MaterialExpressionComponentMask, **chans)
        wire(a, "", n, "")
        return n

    def one(cls, a):
        n = node(cls)
        wire(a, "", n, "")
        return n

    Mul, Add, Sub, Div, Min = (unreal.MaterialExpressionMultiply, unreal.MaterialExpressionAdd, unreal.MaterialExpressionSubtract,
                               unreal.MaterialExpressionDivide, unreal.MaterialExpressionMin)
    Sat, OneMinus = unreal.MaterialExpressionSaturate, unreal.MaterialExpressionOneMinus

    uv = node(unreal.MaterialExpressionTextureCoordinate)
    # Where on the front panel, 0-1 each way; 1 inside it, 0 outside.
    d = binary(Div, binary(Sub, uv, vec2("PanelMin", PANEL[0], PANEL[1])), vec2("PanelSize", PANEL[2], PANEL[3]))
    du, dv = mask(d, r=True), mask(d, g=True)
    edge = binary(Min, binary(Min, du, one(OneMinus, du)), binary(Min, dv, one(OneMinus, dv)))
    inside = one(Sat, binary(Mul, edge, const(2000.0)))
    # The board's own rectangle in the image.
    buv = binary(Add, vec2("BoardMin", 0.0, 0.0), binary(Mul, one(Sat, d), vec2("BoardSize", 1.0, 1.0)))
    board = node(unreal.MaterialExpressionTextureSampleParameter2D, parameter_name="Board", texture=first,
                 sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    wire(buv, "", board, "UVs")
    blank = node(unreal.MaterialExpressionTextureSampleParameter2D, parameter_name="Paint", texture=paint,
                 sampler_type=unreal.MaterialSamplerType.SAMPLERTYPE_COLOR)
    wire(uv, "", blank, "UVs")
    lettered = binary(Mul, board, scalar("Brightness", 0.55), "RGB")
    colour = node(unreal.MaterialExpressionLinearInterpolate)
    wire(blank, "RGB", colour, "A")
    wire(lettered, "", colour, "B")
    wire(inside, "", colour, "Alpha")

    P = unreal.MaterialProperty
    ok = [mel.connect_material_property(colour, "", P.MP_BASE_COLOR), mel.connect_material_property(scalar("Roughness", 0.75), "", P.MP_ROUGHNESS),
          mel.connect_material_property(const(0.35), "", P.MP_SPECULAR)]
    if not all(ok):
        say("output connections: %s" % ok)
    mel.recompile_material(m)
    eal.save_loaded_asset(m)
    say(MASTER + " saved")
    return m


def vec(mi, name, a, b):
    mel.set_material_instance_vector_parameter_value(mi, name, unreal.LinearColor(a, b, 0, 0))


images = {}
for path in eal.list_assets(ART, recursive=True, include_folder=False):
    a = unreal.load_asset(path)
    if isinstance(a, unreal.Texture2D):
        images[a.get_name()] = a
say("%d boards: %s" % (len(images), sorted(images)))
missing = [k for k in BOARDS if k not in images]
if missing:
    say("MISSING " + ", ".join(missing))
paints = {c: unreal.load_asset(TEX + "/T_BackAlleys_Sign_%s_BC" % c) for c in ("White", "Blue", "Yellow")}
master = build_master(images[sorted(images)[0]], paints["White"])
for name, (x0, x1, colour) in sorted(BOARDS.items()):
    if name not in images:
        continue
    mi_name = "MI_BackAlleys_SignBoard_" + name
    if eal.does_asset_exist(MATS + "/" + mi_name):
        say(mi_name + " exists, kept")
        continue
    mi = tools.create_asset(mi_name, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", master)
    mel.set_material_instance_texture_parameter_value(mi, "Board", images[name])
    mel.set_material_instance_texture_parameter_value(mi, "Paint", paints[colour])
    vec(mi, "BoardMin", (x0 + INSET) / IMG_W, 1.0 / IMG_H)
    vec(mi, "BoardSize", (x1 - x0 + 1 - 2 * INSET) / IMG_W, (IMG_H - 2.0) / IMG_H)
    mi.set_editor_property("phys_material", unreal.load_asset(WOOD))
    mi.set_editor_property("override_phys_material", True)      # without it the engine uses the parent's
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    t = images[name]
    say("%s saved: %dx%d, board %.4f..%.4f, %s edges" % (mi_name, t.blueprint_get_size_x(), t.blueprint_get_size_y(), (x0 + INSET) / IMG_W,
                                                         (x1 + 1 - INSET) / IMG_W, colour))
