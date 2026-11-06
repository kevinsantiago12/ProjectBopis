"""Headless and read-only: bounds, triangles, LODs, collision and materials of the last building dressing: power poles, tyres, water meters and the
graffiti cards, and exports the graffiti's base colour textures to Saved/LevelGen/graffiti/ so what they say can be read.
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\pole_shape_ue.py"""
import os

import unreal

ME = "/Game/Megapack/Meshes/MiddleEast/"
PM = "/Game/Philippines_Markets/Props/Water_Meters_Set_01/"
MESHES = [ME + "SM_Electric_Pole_0%d" % i for i in range(1, 6)] + [ME + "SM_electrical_contact_01", ME + "SM_wheel_01"] + [
    PM + k for k in ("SM_Water_Meter_Single_01", "SM_Water_Meter_Single_02", "SM_Water_Meter_Cage_01", "SM_Water_Meter_Cage_02")]
GRAFFITI = [ME + "Decals/SM_Graffiti_Decal_%02d" % i for i in range(0, 13)]
OUT = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "graffiti")
os.makedirs(OUT, exist_ok=True)


def mat_note(mi):
    if not mi:
        return "None"
    name = mi.get_path_name().split(".")[-1]
    base = mi
    while isinstance(base, unreal.MaterialInstance) and base.get_editor_property("parent"):
        base = base.get_editor_property("parent")
    if isinstance(base, unreal.Material):
        return "%s(%s,%s)" % (name, str(base.get_editor_property("blend_mode")).split(".")[-1].split(":")[0], "2side" if base.get_editor_property("two_sided") else "1side")
    return name


def report(p):
    m = unreal.load_asset(p)
    if not m:
        unreal.log_warning("[POLE] %s MISSING" % p)
        return None
    lods = m.get_num_lods()
    tris = [m.get_num_triangles(i) for i in range(lods)]
    b = m.get_bounding_box()
    body = m.get_editor_property("body_setup")
    coll = str(body.get_editor_property("collision_trace_flag")).split(".")[-1].split(":")[0] if body else "none"
    n_prims = 0
    if body:
        g = body.get_editor_property("agg_geom")
        n_prims = len(g.get_editor_property("box_elems")) + len(g.get_editor_property("sphere_elems")) + len(g.get_editor_property("sphyl_elems")) + len(g.get_editor_property("convex_elems"))
    unreal.log_warning("[POLE] %s lods %d tris %s min (%.1f, %.1f, %.1f) max (%.1f, %.1f, %.1f) coll %s prims %d mats %s" % (
        p.split("/")[-1], lods, tris, b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z, coll, n_prims, [mat_note(s.material_interface) for s in m.static_materials]))
    return m


for p in MESHES:
    report(p)
seen = set()
for p in GRAFFITI:
    m = report(p)
    if not m:
        continue
    for s in m.static_materials:
        mi = s.material_interface
        if not mi:
            continue
        for t in unreal.MaterialEditingLibrary.get_used_textures(mi):
            n = t.get_name()
            if n in seen or n.endswith(("_N", "_ORM", "_R", "_M", "_O")):
                continue
            seen.add(n)
            task = unreal.AssetExportTask()
            task.object = t
            task.filename = os.path.join(OUT, n + ".png")
            task.automated = True
            task.prompt = False
            task.replace_identical = True
            ok = unreal.Exporter.run_asset_export_task(task)
            unreal.log_warning("[POLE] texture %s -> %s of %s: %s" % (n, s.material_slot_name, p.split("/")[-1], ok))
