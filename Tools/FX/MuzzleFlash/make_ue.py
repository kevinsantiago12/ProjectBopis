"""Makes the muzzle flash's Unreal assets, headless: builds M_MuzzleFlash from design.py, its instances
MI_MuzzleFlash (the round base, for pistols) and MI_MuzzleFlash_Star (Spikes 1, for rifles), and imports
SM_MuzzleFlash.fbx (from bl_mesh.py) twice, as SM_MuzzleFlash and SM_MuzzleFlash_Star with those instances,
in /Game/ThirdPerson/FX/MuzzleFlash.

    .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\FX\\MuzzleFlash\\make_ue.py -Render

-Render lets the material compile here, so HLSL errors show in make_ue_log.txt ("[FLASH]" lines, and any
"error" from the shader compiler). The first run makes new assets and is safe with the editor open. Re-running
rebuilds them in place: close the editor first if it has loaded them (it would keep its own copies).

The material is additive and unlit. Per shot, UMuzzleFlashComponent sets its custom primitive data:
0 Age (0..1 over the flash's life), 1 Seed, 2 Petals (front spikes, used only when Spikes > 0), 3 Brightness."""
import os
import sys

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "..", "..", "AnimAuthoring", "lib"))
import design as D  # noqa: E402
import uelib as U  # noqa: E402

DEST = "/Game/ThirdPerson/FX/MuzzleFlash"
MESH = "SM_MuzzleFlash"
MAT = "M_MuzzleFlash"
INST = "MI_MuzzleFlash"
# The same cards with the star look (Spikes 1): a gun picks its look by its FlashMesh. Pistols round, rifles star.
MESH_STAR = "SM_MuzzleFlash_Star"
INST_STAR = "MI_MuzzleFlash_Star"
NOISE = "/Game/MilitaryWeapSilver/FX/Textures/T_Explosion_Macro_01"

MEL = unreal.MaterialEditingLibrary
EAL = unreal.EditorAssetLibrary
TOOLS = unreal.AssetToolsHelpers.get_asset_tools()


def log(msg):
    U.log("FLASH", msg)


# --- HLSL --------------------------------------------------------------------------------------------------
NOISE_SAMPLE = """
    float a1 = Texture2DSampleLevel(NoiseTex, NoiseTexSampler, nuv, {NOISE_MIP}).r;
    float a2 = Texture2DSampleLevel(NoiseTex, NoiseTexSampler, nuv * {NOISE_SCALE_2} + 0.5, {NOISE_MIP}).r;
    n = saturate((pow(max(lerp(a1, a2, {NOISE_MIX}), 1e-4), 1.0 / 2.2) - {NOISE_LOW}) / ({NOISE_HIGH} - {NOISE_LOW}));"""

HLSL = """// Made by Tools/FX/MuzzleFlash/make_ue.py from design.py: change it there and re-run, or tune MI_MuzzleFlash.
// Vertex colour R < 0.5: a side card (U from the muzzle to the tip, V across); else the front card.
float age = saturate(Age);
float n, shape, nearness;
if (VC.r < 0.5)
{{
    float2 nuv = float2(UV.x * 0.9 - age * Flow + Seed + VC.g * 0.37, UV.y * 0.6 + Seed * 1.7 + VC.g * 0.61);
    {noise}
    // Two petals per card, each its own length.
    float petal = VC.g * 2.0 + (UV.y > 0.5 ? 1.0 : 0.0);
    float reach = {PETAL_SHORTEST} + (1.0 - {PETAL_SHORTEST}) * frac(sin((petal + Seed * 7.13) * 12.9898) * 43758.5453);
    float pu = UV.x / reach;
    float side = abs(UV.y - 0.5) * 2.0 + (n - 0.5) * {WARP};
    float width = {PETAL_WIDTH} * pow(clamp(pu, 1e-4, 1.0), {PETAL_RISE}) * pow(max(1.0 - pu, 1e-4), {PETAL_FALL});
    width = pu < 1.0 ? width : 0.0;
    // The round base: a ball on the muzzle (Spikes 1: the plain pointed petals).
    float bu = UV.x - {BALL_U};
    float ball = 2.0 * {LENGTH_PER_WIDTH} * sqrt(max({BALL_U} * {BALL_U} - bu * bu, 0.0));
    width = lerp(max(width, ball), width, Spikes);
    shape = saturate((width - max(side, 0.0)) / max(width, 1e-3));
    nearness = 1.0 - UV.x;
}}
else
{{
    float2 d = (UV - 0.5) * 2.0;
    float r = length(d);
    float ang = atan2(d.y, d.x);
    float2 nuv = float2(r * 0.8 - age * Flow + Seed, ang * (3.0 / 6.2832) + Seed * 1.7);
    {noise}
    // A ragged disc (Spikes 1: Petals spikes round the barrel, each leaning off its even spacing and
    // reaching its own length).
    float turn = frac(ang / 6.2832 + 0.5 + Seed) * Petals;
    float spike = floor(turn);
    float across = frac(turn) - 0.5 + (frac(sin((spike * 3.7 + Seed * 5.1) * 12.9898) * 43758.5453) - 0.5) * {SPIKE_JITTER};
    float lobe = pow(saturate(cos(across * 3.14159)), {STAR_SHARP});
    float len = {SPIKE_SHORTEST} + (1.0 - {SPIKE_SHORTEST}) * frac(sin((spike + Seed * 7.13) * 12.9898) * 43758.5453);
    float star = {STAR_REACH} * ({STAR_CORE} + (1.0 - {STAR_CORE}) * lobe * len);
    float reach = lerp({DISC_REACH}, star, Spikes);
    shape = saturate(1.0 - (r + (n - 0.5) * {WARP} * r) / reach);
    nearness = 1.0 - r;
}}
// The body burns away from its thin edges as the threshold rises with age; the last of it fades out.
float body = shape * ({DENSITY_BASE} + {DENSITY_NOISE} * n);
float burn = pow(saturate((age - {BURN_START}) / (1.0 - {BURN_START})), {BURN_CURVE});
float threshold = {BURN_FROM} + ({BURN_TO} - {BURN_FROM}) * burn;
float mask = saturate((body - threshold) / max(Softness, 1e-3)) * saturate((1.0 - age) / {FADE_LAST});
// Hot where it's dense and near the muzzle, cooling with age; brighter for the bang on the first frames.
float pop = {POP} * (1.0 - saturate(age / {POP_TIME}));
float heat = saturate(body * {HEAT_DENSITY} + nearness * {HEAT_BIAS} - age * {HEAT_AGE} + pop * 0.3);
float3 col = lerp(Cool, Mid, saturate(heat * 2.0));
col = lerp(col, Hot, saturate(heat * 2.0 - 1.0));
// A card fades as it turns edge-on to the camera.
float facing = abs(dot(normalize(CamVec), normalize(Nrm)));
float view = smoothstep(FacingMin, FacingMax, facing);
return col * (mask * view * Intensity * Brightness * (1.0 + pop));
"""


def hlsl():
    consts = {k: v for k, v in vars(D).items() if k.isupper() and isinstance(v, (int, float))}
    noise = NOISE_SAMPLE.format(**consts).strip()
    return HLSL.format(noise=noise, **consts)


# --- Material ----------------------------------------------------------------------------------------------
def node(mat, cls, x, y):
    return MEL.create_material_expression(mat, cls, x, y)


def scalar(mat, name, value, x, y, cpd=None):
    e = node(mat, unreal.MaterialExpressionScalarParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("default_value", value)
    if cpd is not None:
        e.set_editor_property("use_custom_primitive_data", True)
        e.set_editor_property("primitive_data_index", cpd)
    return e


def vector(mat, name, rgb, x, y):
    e = node(mat, unreal.MaterialExpressionVectorParameter, x, y)
    e.set_editor_property("parameter_name", name)
    e.set_editor_property("default_value", unreal.LinearColor(rgb[0], rgb[1], rgb[2], 1.0))
    return e


def build_material():
    path = DEST + "/" + MAT
    if EAL.does_asset_exist(path):
        mat = unreal.load_asset(path)
        MEL.delete_all_material_expressions(mat)
        log("rebuilding %s" % path)
    else:
        mat = TOOLS.create_asset(MAT, DEST, unreal.Material, unreal.MaterialFactoryNew())
        log("made %s" % path)
    mat.set_editor_property("blend_mode", unreal.BlendMode.BLEND_ADDITIVE)
    mat.set_editor_property("shading_model", unreal.MaterialShadingModel.MSM_UNLIT)
    mat.set_editor_property("two_sided", True)

    custom = node(mat, unreal.MaterialExpressionCustom, -400, 0)
    custom.set_editor_property("description", "Muzzle flash")
    custom.set_editor_property("output_type", unreal.CustomMaterialOutputType.CMOT_FLOAT3)
    custom.set_editor_property("code", hlsl())

    inputs = []
    wired = []          # (expression, output name, custom input name)

    def feed(name, expr, output=""):
        ci = unreal.CustomInput()
        ci.set_editor_property("input_name", name)
        inputs.append(ci)
        wired.append((expr, output, name))

    y = -900
    def row():
        nonlocal y
        y += 70
        return y

    feed("UV", node(mat, unreal.MaterialExpressionTextureCoordinate, -900, row()))
    feed("VC", node(mat, unreal.MaterialExpressionVertexColor, -900, row()))
    feed("CamVec", node(mat, unreal.MaterialExpressionCameraVectorWS, -900, row()))
    feed("Nrm", node(mat, unreal.MaterialExpressionVertexNormalWS, -900, row()))
    for i, (name, default) in enumerate([("Age", 0.25), ("Seed", 0.37), ("Petals", 5.0), ("Brightness", 1.0)]):
        feed(name, scalar(mat, name, default, -900, row(), cpd=i))
    for name in ("Intensity", "Softness", "Flow", "FacingMin", "FacingMax", "Spikes"):
        feed(name, scalar(mat, name, D.PARAMS[name], -900, row()))
    for name, key in (("Hot", "HotColour"), ("Mid", "MidColour"), ("Cool", "CoolColour")):
        feed(name, vector(mat, key, D.COLOURS[key], -900, row()))
    tex = node(mat, unreal.MaterialExpressionTextureObjectParameter, -900, row())
    tex.set_editor_property("parameter_name", "NoiseTexture")
    tex.set_editor_property("texture", unreal.load_asset(NOISE))
    feed("NoiseTex", tex)
    custom.set_editor_property("inputs", inputs)
    for expr, output, name in wired:
        if not MEL.connect_material_expressions(expr, output, custom, name):
            log("ERROR could not connect %s" % name)

    # Softened where it meets a wall, so a shot point-blank into one shows no hard line.
    fade = node(mat, unreal.MaterialExpressionDepthFade, -150, 200)
    MEL.connect_material_expressions(scalar(mat, "DepthFade", D.PARAMS["DepthFade"], -400, 250), "", fade, "FadeDistance")
    mul = node(mat, unreal.MaterialExpressionMultiply, 50, 0)
    MEL.connect_material_expressions(custom, "", mul, "A")
    MEL.connect_material_expressions(fade, "", mul, "B")
    MEL.connect_material_property(mul, "", unreal.MaterialProperty.MP_EMISSIVE_COLOR)

    MEL.recompile_material(mat)
    EAL.save_asset(path, only_if_is_dirty=False)
    return mat


def build_instance(mat, name, spikes=None):
    path = DEST + "/" + name
    if EAL.does_asset_exist(path):
        inst = unreal.load_asset(path)
    else:
        inst = TOOLS.create_asset(name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    MEL.set_material_instance_parent(inst, mat)
    if spikes is not None:
        MEL.set_material_instance_scalar_parameter_value(inst, "Spikes", spikes)
    EAL.save_asset(path, only_if_is_dirty=False)
    log("instance %s" % path)
    return inst


# --- Mesh --------------------------------------------------------------------------------------------------
def import_mesh(inst, name):
    U.use_legacy_fbx_import()
    ui = unreal.FbxImportUI()
    ui.set_editor_property("import_mesh", True)
    ui.set_editor_property("import_as_skeletal", False)
    ui.set_editor_property("import_animations", False)
    ui.set_editor_property("import_materials", False)
    ui.set_editor_property("import_textures", False)
    ui.set_editor_property("automated_import_should_detect_type", False)
    ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_STATIC_MESH)
    data = ui.get_editor_property("static_mesh_import_data")
    data.set_editor_property("combine_meshes", True)
    data.set_editor_property("auto_generate_collision", False)
    data.set_editor_property("generate_lightmap_u_vs", False)
    data.set_editor_property("remove_degenerates", False)
    data.set_editor_property("build_nanite", False)
    data.set_editor_property("vertex_color_import_option", unreal.VertexColorImportOption.REPLACE)
    data.set_editor_property("normal_import_method", unreal.FBXNormalImportMethod.FBXNIM_IMPORT_NORMALS)
    task = unreal.AssetImportTask()
    task.set_editor_property("filename", os.path.join(HERE, MESH + ".fbx"))
    task.set_editor_property("destination_path", DEST)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", False)
    task.set_editor_property("options", ui)
    TOOLS.import_asset_tasks([task])
    mesh = unreal.load_asset(DEST + "/" + name)
    mesh.set_material(0, inst)
    box = mesh.get_bounding_box()
    log("mesh %s: bounds %s .. %s, %d triangles, %d sections" % (
        mesh.get_path_name(), box.min, box.max,
        unreal.EditorStaticMeshLibrary.get_number_verts(mesh, 0), mesh.get_num_sections(0)))
    EAL.save_asset(DEST + "/" + name, only_if_is_dirty=False)
    return mesh


def export_noise():
    out = os.path.join(HERE, "noise.tga")
    if os.path.exists(out):
        return
    task = unreal.AssetExportTask()
    task.object = unreal.load_asset(NOISE)
    task.filename = out
    task.exporter = unreal.TextureExporterTGA()
    task.automated = True
    task.prompt = False
    unreal.Exporter.run_asset_export_task(task)
    log("exported noise.tga for preview.py")


def main():
    export_noise()
    mat = build_material()
    import_mesh(build_instance(mat, INST), MESH)
    import_mesh(build_instance(mat, INST_STAR, spikes=1.0), MESH_STAR)
    log("done")


try:
    main()
except Exception:
    import traceback
    log("ERROR " + traceback.format_exc())
