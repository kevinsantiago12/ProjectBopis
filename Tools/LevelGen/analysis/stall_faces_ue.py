"""Headless and read-only: the flat faces of the shop row's meshes, to find surfaces that share a plane. For each mesh and material section: triangles grouped by facing axis and plane, with the area and
extent of each, written to Saved/LevelGen/stall_faces.json. User 2026-11-06: "Shop A 001, overlapping surfaces with wall".
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\stall_faces_ue.py"""
import json
import os

import unreal

AS = "/Game/AsiaSlum/FBX/"
OUT = {}
for name in ("SM_Shop_A_001", "SM_HouseWall_A_001", "SM_HouseWall_A_001_HalfA", "SM_HouseWallDoorFrmae_A_002", "SM_RollupDoor_A_002"):
    m = unreal.load_asset(AS + name)
    if not m:
        unreal.log_warning("[FACES] %s missing" % name)
        continue
    faces = {}
    for sec in range(m.get_num_sections(0)):
        r = unreal.ProceduralMeshLibrary.get_section_from_static_mesh(m, 0, sec)
        verts, tris = r[0], r[1]
        for i in range(0, len(tris), 3):
            a, b, c = verts[tris[i]], verts[tris[i + 1]], verts[tris[i + 2]]
            ux, uy, uz = b.x - a.x, b.y - a.y, b.z - a.z
            vx, vy, vz = c.x - a.x, c.y - a.y, c.z - a.z
            nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
            area = (nx * nx + ny * ny + nz * nz) ** 0.5 / 2.0
            if area < 1.0:
                continue
            nx, ny, nz = nx / (2 * area), ny / (2 * area), nz / (2 * area)
            axis = max((abs(nx), "x", nx), (abs(ny), "y", ny), (abs(nz), "z", nz))
            if axis[0] < 0.995:
                continue
            at = {"x": a.x, "y": a.y, "z": a.z}[axis[1]]
            key = "%s%s %.1f s%d" % ("+" if axis[2] > 0 else "-", axis[1], at, sec)
            f = faces.setdefault(key, {"area": 0.0, "x": [a.x, a.x], "y": [a.y, a.y], "z": [a.z, a.z]})
            f["area"] += area
            for p in (a, b, c):
                for k, v in (("x", p.x), ("y", p.y), ("z", p.z)):
                    f[k] = [min(f[k][0], v), max(f[k][1], v)]
    OUT[name] = faces
    unreal.log_warning("[FACES] %s sections %d planes %d" % (name, m.get_num_sections(0), len(faces)))
path = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", "stall_faces.json")
json.dump(OUT, open(path, "w"), indent=0)
unreal.log_warning("[FACES] wrote %s" % path)
