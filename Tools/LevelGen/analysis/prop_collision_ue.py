"""Headless and read-only: whether the props meant to be physical have simple collision, which a simulated body needs (complex-as-simple can't simulate), and their mass at scale 1.
User 2026-11-07: "I want bullets to affect them ... only light things".
Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\prop_collision_ue.py"""
import json

import unreal

PM = "/Game/Philippines_Markets/Props/"
ME = "/Game/Megapack/Meshes/"
ASSETS = [PM + "MonoBloc_Chairs_01/SM_Monobloc_Chair_01", PM + "MonoBloc_Chairs_01/SM_Monobloc_Chair_03", PM + "MonoBloc_Chairs_01/SM_Monobloc_Stool_01", PM + "MonoBloc_Chairs_01/SM_Monobloc_Stool_02",
          PM + "Buckets_Set_01/SM_Bucket_01", PM + "Buckets_Set_01/SM_Bucket_02", PM + "Buckets_Set_01/SM_Bucket_03", PM + "Buckets_Set_01/SM_Bucket_Lid_01", ME + "Favela/SM_MetalBucket_01", ME + "Favela/SM_MetalBucket_02"]
out = {}
for path in ASSETS:
    m = unreal.load_asset(path)
    if m is None:
        out[path] = "missing"
        continue
    bs = m.get_editor_property("body_setup")
    e = {"trace": str(bs.get_editor_property("collision_trace_flag")).split(".")[-1].split(":")[0] if bs else None}
    if bs:
        g = bs.get_editor_property("agg_geom")
        e.update({k: len(g.get_editor_property(k)) for k in ("box_elems", "sphere_elems", "sphyl_elems", "convex_elems")})
        e["phys"] = bs.get_editor_property("phys_material").get_path_name() if bs.get_editor_property("phys_material") else None
    b = m.get_bounding_box()
    e["size"] = [round(b.max.x - b.min.x), round(b.max.y - b.min.y), round(b.max.z - b.min.z)]
    out[path.split("/")[-1]] = e
unreal.log_warning("[PROPCOLL] " + json.dumps(out))
