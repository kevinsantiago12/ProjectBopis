"""Headless, read-only: prints the local bounds of meshes the generator fits by size (the AsiaSlum door meshes for
the door slot, SM_Ramp for the roof gables), and the corner vertices of SM_Ramp so its slope direction is known.
Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\door_bounds_ue.py"""
import unreal

for p in ("/Game/AsiaSlum/FBX/SM_HouseDoor_A_002", "/Game/AsiaSlum/FBX/SM_HouseDoor_A_004",
          "/Game/AsiaSlum/FBX/SM_HouseDoor_A_005", "/Game/AsiaSlum/FBX/SM_HouseDoor_B_003",
          "/Game/LevelPrototyping/Meshes/SM_Ramp", "/Game/Megapack/Meshes/Favela/SM_Slate_01"):
    m = unreal.load_asset(p)
    b = m.get_bounding_box()
    unreal.log_warning("[BOUNDS] %s min (%.1f, %.1f, %.1f) max (%.1f, %.1f, %.1f) slots %d" % (
        p.split("/")[-1], b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z, len(m.static_materials)))
ramp = unreal.load_asset("/Game/LevelPrototyping/Meshes/SM_Ramp")
desc = ramp.get_static_mesh_description(0)
pts = set()
for i in range(desc.get_vertex_count()):
    v = desc.get_vertex_position(unreal.VertexID(i))
    pts.add((round(v.x), round(v.y), round(v.z)))
unreal.log_warning("[RAMP] %s" % sorted(pts))
