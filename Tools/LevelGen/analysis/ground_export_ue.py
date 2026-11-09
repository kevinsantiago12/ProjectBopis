"""Headless and read-only: exports what the ground pass could use, as the stored previews are blank. For each candidate material: its parent, physical material, texture parameters and
scalars, to Saved/LevelGen/ground_tex/materials.json, and its colour textures as PNGs in the same folder. Also the bounds and slots of the drain and litter meshes.
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\ground_export_ue.py"""
import json
import os

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "ground_tex")
os.makedirs(OUT, exist_ok=True)
F = "/Game/Megapack/Material/Favela/"
M = "/Game/Megapack/Material/MiddleEast/"
Y = "/Game/Megapack/Material/Yakohama/"
MATS = [F + n for n in ("MI_Road_02", "MI_sidewalk_01", "MI_Concrete_bland_01")] + [M + n for n in ("MI_dirty_road_01", "MI_Dirt_01", "MI_gravel_01", "MI_paving_slab_01", "MI_road_02", "MI_road_03", "MI_road_05", "MI_sidewalk_01", "MI_sidewalk_02", "MI_channel_dirt_01")] + \
       [Y + n for n in ("MI_Asphalt", "MI_AsphaltContrast_01", "MI_Sidewalk_01", "MI_Sidewalk_02", "MI_Sidewalk_03")] + \
       [F + "Decals/" + n for n in ("MI_DecalRoadDirt_02", "MI_DecalRoadDirt_03", "MI_DecalRoadDirt_04", "MI_DecalRoadDirt_05", "MI_Decal_Dirt_06", "MI_Decal_Dirt_07", "MI_Decal_Dirt_08")] + \
       [Y + "Decals/" + n for n in ("MI_DecalDirt_03", "MI_DecalSidewalks_10", "M_Leakage_01", "M_Leakage_02", "M_RoadDirt_01", "M_RoadDirt_02")] + ["/Game/ThirdPerson/BackAlleys/Materials/MI_BackAlleys_Ground"]
MESH = ["/Game/Megapack/Meshes/Favela/SM_Sewer_01", "/Game/Megapack/Meshes/MiddleEast/SM_channel_01", "/Game/Megapack/Meshes/MiddleEast/SM_cigarette_butt_01", "/Game/Megapack/Meshes/MiddleEast/SM_cigarette_butt_02",
        "/Game/Megapack/Meshes/MiddleEast/SM_crumpled_cup", "/Game/Megapack/Meshes/MiddleEast/SM_cup", "/Game/Megapack/Meshes/MiddleEast/SM_Paper", "/Game/Megapack/Meshes/MiddleEast/SM_gravel_01",
        "/Game/Megapack/Meshes/MiddleEast/SM_Garbage_bag_01", "/Game/Megapack/Meshes/MiddleEast/SM_Garbage_bag_02", "/Game/Megapack/Meshes/MiddleEast/SM_Garbage_bag_green_03",
        "/Game/AsiaSlum/FBX/SM_Debris_A_001", "/Game/AsiaSlum/FBX/SM_Debris_A_002", "/Game/AsiaSlum/FBX/SM_Debris_A_003", "/Game/Philippines_Markets/Props/MarketStall_Metal/SM/OTHER/SM_PLASTIC_BAGS"] + \
       ["/Game/Philippines_Markets/Props/CardboardSet_01/SM_Cardboard_Flat_0%d" % i for i in range(1, 6)] + ["/Game/Philippines_Markets/Props/RiceBags_01/SM_Rice_Bag_" + n for n in ("Flat_01", "Flat_02", "Curled_01", "Straight_01", "HalfFull_01", "Full_01")]
L = unreal.MaterialEditingLibrary
out = {"materials": {}, "meshes": {}}
done = set()


def export(t):
    name = t.get_name()
    if name in done:
        return
    done.add(name)
    # Normal maps and masks aren't what's being judged.
    if str(t.get_editor_property("compression_settings")).split(".")[-1].split(":")[0] in ("TC_NORMALMAP",):
        return
    task = unreal.AssetExportTask()
    task.object = t
    task.filename = os.path.join(OUT, name + ".png")
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    unreal.Exporter.run_asset_export_task(task)


for path in MATS:
    m = unreal.load_asset(path)
    if m is None:
        out["materials"][path] = "missing"
        continue
    e = {"class": m.get_class().get_name(), "tex": {}, "scalars": {}}
    try:
        base = m.get_base_material()
        e["base"] = base.get_path_name()
        e["blend"] = str(base.get_editor_property("blend_mode")).split(".")[-1].split(":")[0]
        e["domain"] = str(base.get_editor_property("material_domain")).split(".")[-1].split(":")[0]
        e["decal_blend"] = str(base.get_editor_property("decal_blend_mode")).split(".")[-1].split(":")[0]
        pm = m.get_physical_material()
        e["phys"] = pm.get_path_name() if pm else None
    except Exception as ex:
        e["err"] = str(ex)[:120]
    if isinstance(m, unreal.MaterialInstance):
        for pn in L.get_texture_parameter_names(m.get_base_material()):
            t = L.get_material_instance_texture_parameter_value(m, pn)
            e["tex"][str(pn)] = t.get_path_name() if t else None
            if t:
                e["tex"][str(pn)] += " %dx%d" % (t.blueprint_get_size_x(), t.blueprint_get_size_y())
                export(t)
        for pn in L.get_scalar_parameter_names(m.get_base_material()):
            e["scalars"][str(pn)] = round(L.get_material_instance_scalar_parameter_value(m, pn), 3)
    else:
        for t in L.get_used_textures(m):
            e["tex"][t.get_name()] = t.get_path_name() + " %dx%d" % (t.blueprint_get_size_x(), t.blueprint_get_size_y())
            export(t)
    out["materials"][path] = e
for path in MESH:
    s = unreal.load_asset(path)
    if s is None:
        out["meshes"][path] = "missing"
        continue
    b = s.get_bounding_box()
    out["meshes"][path] = {"min": [round(b.min.x, 1), round(b.min.y, 1), round(b.min.z, 1)], "max": [round(b.max.x, 1), round(b.max.y, 1), round(b.max.z, 1)],
                           "slots": [m_.material_interface.get_path_name() if m_.material_interface else None for m_ in s.static_materials]}
json.dump(out, open(os.path.join(OUT, "materials.json"), "w"), indent=1)
unreal.log_warning("[GROUND] done, %d textures" % len(done))
