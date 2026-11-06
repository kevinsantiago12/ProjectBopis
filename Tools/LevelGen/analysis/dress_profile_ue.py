"""Headless and read-only: which way the building dressing's meshes face. For each mesh, how its vertices spread along local X,
Y and Z in 10 bins, so the wall side and the outer side show up. See dress_shape_ue.py for bounds and collision.
Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\dress_profile_ue.py"""
import unreal

AS = "/Game/AsiaSlum/FBX/"
FV = "/Game/Megapack/Meshes/Favela/"
ME = "/Game/Megapack/Meshes/MiddleEast/"
for p in (AS + "SM_Balcony_A_003", AS + "SM_Balcony_B_004", ME + "SM_Windows_04", ME + "SM_Air_Conditioning_White_03",
          ME + "SM_Support_01", FV + "SM_Rain_Pipe_01", FV + "SM_Metal_Bracket_01"):
    m = unreal.load_asset(p)
    d = m.get_static_mesh_description(0)
    pts = [d.get_vertex_position(unreal.VertexID(i)) for i in range(d.get_vertex_count())]
    b = m.get_bounding_box()
    out = []
    for name, lo, hi, get in (("x", b.min.x, b.max.x, lambda v: v.x), ("y", b.min.y, b.max.y, lambda v: v.y),
                              ("z", b.min.z, b.max.z, lambda v: v.z)):
        bins = [0] * 10
        for v in pts:
            bins[min(9, int((get(v) - lo) / max(hi - lo, 0.01) * 10))] += 1
        out.append("%s %.1f..%.1f %s" % (name, lo, hi, bins))
    unreal.log_warning("[PROFILE] %s verts %d | %s" % (p.split("/")[-1], len(pts), " | ".join(out)))
