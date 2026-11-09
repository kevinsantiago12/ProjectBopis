"""Headless, read-only: how SM_Sign_A_001's board faces are UV-mapped, so lettering can go on them (user 2026-11-07, the business signs).
Per section: the vertices grouped by face direction, with their position and UV0 ranges.
Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\sign_uv_ue.py"""
import unreal

for path in ("/Game/AsiaSlum/FBX/SM_Sign_A_001",):
    m = unreal.load_asset(path)
    b = m.get_bounding_box()
    unreal.log_warning("[SIGNUV] %s bounds (%.1f %.1f %.1f)..(%.1f %.1f %.1f) sections %d" % (
        path.split("/")[-1], b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z, m.get_num_sections(0)))
    for sec in range(m.get_num_sections(0)):
        verts, tris, normals, uvs, tangents = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, sec)
        groups = {}
        for p, n, uv in zip(verts, normals, uvs):
            key = (round(n.x), round(n.y), round(n.z))
            groups.setdefault(key, []).append((p, uv))
        for key, pts in sorted(groups.items()):
            xs = [p.x for p, _ in pts]; ys = [p.y for p, _ in pts]; zs = [p.z for p, _ in pts]
            us = [uv.x for _, uv in pts]; vs = [uv.y for _, uv in pts]
            unreal.log_warning("[SIGNUV] sec %d normal %s n %d  x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f  u %.3f..%.3f v %.3f..%.3f" % (
                sec, key, len(pts), min(xs), max(xs), min(ys), max(ys), min(zs), max(zs), min(us), max(us), min(vs), max(vs)))
            if key[1] != 0 and len(pts) <= 40:
                for p, uv in pts:
                    unreal.log_warning("[SIGNUV]    (%.1f %.1f %.1f) uv (%.3f %.3f)" % (p.x, p.y, p.z, uv.x, uv.y))
