"""Read-only, headless: exports the user's new plywood textures (2026-11-13: "I added a Plywood texture on the content folder") and
the old plywood material instances' base colours to PNG, with their sizes, sRGB, compression and the old instances' parameters, so
the new material can be set up to match. Writes Saved/LevelGen/tex/ply_*.png and ply_info.json. Nothing is saved.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\plywood_tex_ue.py"""
import json
import os
import traceback

import unreal

OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "tex")
os.makedirs(OUT, exist_ok=True)
TEX = ["/Game/T_Plywood_BaseColor", "/Game/T_Plywood_Normal_DX", "/Game/ThirdPerson/BackAlleys/Textures/T_BackAlleys_Plywood_Natural_BC",
       "/Game/ThirdPerson/BackAlleys/Textures/T_BackAlleys_Plywood_Weathered_BC", "/Game/ThirdPerson/BackAlleys/Textures/T_BackAlleys_Plywood_N"]
MIS = ["/Game/ThirdPerson/BackAlleys/Materials/MI_BackAlleys_Ply_" + k for k in ("Natural", "Weathered", "GreenPaint")]
mel = unreal.MaterialEditingLibrary
info = {"textures": {}, "instances": {}}


def say(msg):
    unreal.log_warning("[PLY] " + msg)


try:
    for p in TEX:
        t = unreal.load_asset(p)
        if not t:
            say("missing " + p)
            continue
        name = p.rsplit("/", 1)[1]
        info["textures"][name] = {"size": [t.blueprint_get_size_x(), t.blueprint_get_size_y()], "srgb": t.get_editor_property("srgb"),
                                  "compression": str(t.get_editor_property("compression_settings")),
                                  "flip_green": t.get_editor_property("flip_green_channel")}
        task = unreal.AssetExportTask()
        task.object = t
        task.filename = os.path.join(OUT, "ply_" + name + ".png")
        task.automated = True
        task.prompt = False
        task.replace_identical = True
        info["textures"][name]["exported"] = bool(unreal.Exporter.run_asset_export_task(task))
    for p in MIS:
        mi = unreal.load_asset(p)
        if not mi:
            say("missing " + p)
            continue
        d = {"parent": mi.get_editor_property("parent").get_path_name(), "textures": {}, "scalars": {}, "vectors": {}}
        for n in mel.get_texture_parameter_names(mi):
            v = mel.get_material_instance_texture_parameter_value(mi, n)
            d["textures"][str(n)] = v.get_path_name() if v else None
        for n in mel.get_scalar_parameter_names(mi):
            d["scalars"][str(n)] = mel.get_material_instance_scalar_parameter_value(mi, n)
        for n in mel.get_vector_parameter_names(mi):
            c = mel.get_material_instance_vector_parameter_value(mi, n)
            d["vectors"][str(n)] = [round(c.r, 3), round(c.g, 3), round(c.b, 3), round(c.a, 3)]
        pm = mi.get_editor_property("phys_material")
        d["phys"] = pm.get_path_name() if pm else None
        info["instances"][p.rsplit("/", 1)[1]] = d
    json.dump(info, open(os.path.join(OUT, "ply_info.json"), "w"), indent=1)
    say("done")
except Exception:
    say("ERROR " + traceback.format_exc())
