"""Headless and read-only: exports every static mesh in the art packs to FBX (LOD0, no collision), with each material
slot's base colour texture as PNG, so Blender can render the meshes from several angles (render_meshes_blender.py).
User 2026-11-03: analyse the packs' models themselves, not just metadata.
Writes Saved/LevelGen/visual/fbx/<pack>/<name>.fbx, visual/tex/<texture>.png and visual/meshes.json.
Skips files already exported, so a re-run only adds new meshes.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\export_meshes_ue.py"""
import json
import os
import re

import unreal

PACKS = ("/Game/Megapack", "/Game/AsiaSlum", "/Game/Philippines_Markets")
OUT = os.path.join(unreal.Paths.convert_relative_path_to_full(unreal.Paths.project_saved_dir()), "LevelGen", "visual")
BASE = re.compile(r"(base ?colou?r|albedo|diffuse|^color|^colour|^tex(ture)?$|_bc$|_d$|_albedo$)", re.I)
NOT_BASE = re.compile(r"(normal|rough|metal|mask|ao$|_n$|_orm$|_rma$|height|emiss|opacity|detail)", re.I)
os.makedirs(os.path.join(OUT, "tex"), exist_ok=True)


def export(obj, filename, options=None):
    if os.path.exists(filename):
        return True
    task = unreal.AssetExportTask()
    task.object = obj
    task.filename = filename
    task.automated = True
    task.prompt = False
    task.replace_identical = True
    if options is not None:
        task.options = options
    return unreal.Exporter.run_asset_export_task(task)


def base_texture(mat):
    """The base colour texture of a material or instance: a named parameter first, then any used texture that
    doesn't look like a normal/mask map."""
    if mat is None:
        return None
    m = mat
    while isinstance(m, unreal.MaterialInstance):
        for tp in m.get_editor_property("texture_parameter_values") or []:
            name = str(tp.parameter_info.name)
            tex = tp.parameter_value
            if tex and BASE.search(name) and not NOT_BASE.search(name):
                return tex
        m = m.get_editor_property("parent")
    try:
        used = unreal.MaterialEditingLibrary.get_used_textures(mat)
    except Exception:
        used = []
    for tex in used:
        if tex and BASE.search(tex.get_name()) and not NOT_BASE.search(tex.get_name()):
            return tex
    for tex in used:
        if tex and not NOT_BASE.search(tex.get_name()):
            return tex
    return None


opts = unreal.FbxExportOption()
opts.collision = False
opts.level_of_detail = False
opts.export_morph_targets = False
ar = unreal.AssetRegistryHelpers.get_asset_registry()
index, n_ok, n_fail = [], 0, 0
for pack in PACKS:
    for ad in ar.get_assets_by_path(pack, recursive=True):
        if str(ad.asset_class_path.asset_name) != "StaticMesh":
            continue
        path = str(ad.package_name)
        name = str(ad.asset_name)
        sub = path.split("/")[2] + ("_" + path.split("/")[4] if path.startswith("/Game/Megapack/Meshes/") else "")
        os.makedirs(os.path.join(OUT, "fbx", sub), exist_ok=True)
        mesh = unreal.load_asset(path)
        fbx = os.path.join(OUT, "fbx", sub, name + ".fbx")
        ok = export(mesh, fbx, opts)
        n_ok += ok
        n_fail += not ok
        slots = []
        for i, sm in enumerate(mesh.static_materials):
            mat = sm.material_interface
            tex = base_texture(mat)
            png = None
            if tex is not None:
                png = os.path.join(OUT, "tex", tex.get_name() + ".png")
                if not export(tex, png):
                    png = None
            blend = str(mat.get_blend_mode()) if mat is not None and hasattr(mat, "get_blend_mode") else ""
            slots.append({"index": i, "slot": str(sm.material_slot_name), "material": mat.get_name() if mat else None,
                          "tex": os.path.basename(png) if png else None, "blend": blend})
        try:
            tris = mesh.get_num_triangles(0)
        except Exception:
            tris = None
        b = mesh.get_bounding_box()
        index.append({"path": path, "name": name, "group": sub, "fbx": os.path.relpath(fbx, OUT).replace("\\", "/"),
                      "ok": bool(ok), "slots": slots, "tris": tris,
                      "bounds_min": [round(b.min.x, 1), round(b.min.y, 1), round(b.min.z, 1)],
                      "bounds_max": [round(b.max.x, 1), round(b.max.y, 1), round(b.max.z, 1)]})
        unreal.log_warning("[MESH] %s %s" % (path, "ok" if ok else "FAILED"))
json.dump(index, open(os.path.join(OUT, "meshes.json"), "w"), indent=1)
unreal.log_warning("[MESH] exported %d, failed %d" % (n_ok, n_fail))
