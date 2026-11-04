"""Headless and read-only: prints the shape of the meshes the window and door awnings are built from: bounds, material
slots, and for each depth bin along the projecting axis the lowest and highest vertex, which shows which way the mesh
slopes and which edge goes against the wall.
Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\awning_shape_ue.py"""
import unreal

MESHES = {"/Game/AsiaSlum/FBX/SM_Roof_A_002": "y", "/Game/Megapack/Meshes/MiddleEast/SM_awning_base_01": "x",
          "/Game/AsiaSlum/FBX/SM_Roof_B_001": "x"}
for path, axis in MESHES.items():
    m = unreal.load_asset(path)
    b = m.get_bounding_box()
    unreal.log_warning("[AWN] %s min (%.1f, %.1f, %.1f) max (%.1f, %.1f, %.1f) slots %d" % (
        path.split("/")[-1], b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z, len(m.static_materials)))
    desc = m.get_static_mesh_description(0)
    pts = []
    for i in range(desc.get_vertex_count()):
        v = desc.get_vertex_position(unreal.VertexID(i))
        pts.append((v.x, v.y, v.z))
    for ax, name in ((0, "x"), (1, "y")):
        lo, hi = min(p[ax] for p in pts), max(p[ax] for p in pts)
        n = 8
        rows = []
        for k in range(n):
            a, c = lo + (hi - lo) * k / n, lo + (hi - lo) * (k + 1) / n + 0.01
            zs = [p[2] for p in pts if a <= p[ax] < c]
            rows.append("%.0f..%.0f: z %s" % (a, c, ("%.0f..%.0f (%d)" % (min(zs), max(zs), len(zs))) if zs else "-"))
        unreal.log_warning("[AWN]   along %s: %s" % (name, " | ".join(rows)))
