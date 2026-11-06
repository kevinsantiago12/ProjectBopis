"""Headless and read-only: LOD counts, triangles per LOD and Nanite for the laundry meshes, to keep them cheap at a distance.
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\laundry_shape_ue.py"""
import unreal

AS = "/Game/AsiaSlum/FBX/"
ME = "/Game/Megapack/Meshes/MiddleEast/"
MESHES = [ME + "SM_clothes_A_0%d" % i for i in range(1, 6)] + [ME + "SM_clothes_B_0%d" % i for i in range(1, 4)] + [
    AS + "SM_Cloth_B_001", AS + "SM_Cloth_B_002", AS + "SM_DryingRack_A_001", AS + "SM_DryingRack_A_002", AS + "SM_DryingRack_A_003",
    AS + "SM_Rope_A_001", AS + "SM_Rope_A_002", ME + "SM_Dryer_01"]
for p in MESHES:
    m = unreal.load_asset(p)
    if not m:
        unreal.log_warning("[LAUNDRY] %s MISSING" % p)
        continue
    lods = m.get_num_lods()
    tris = [m.get_num_triangles(i) for i in range(lods)]
    b = m.get_bounding_box()
    unreal.log_warning("[LAUNDRY] %s lods %d tris %s min (%.0f, %.0f, %.0f) max (%.0f, %.0f, %.0f)" % (
        p.split("/")[-1], lods, tris, b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z))
