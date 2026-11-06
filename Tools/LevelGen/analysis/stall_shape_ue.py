"""Headless and read-only: the AsiaSlum wall pieces of the shop row, to fit shutters and closed walls into them. User 2026-11-06: "the wall if open".
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\stall_shape_ue.py"""
import unreal

AS = "/Game/AsiaSlum/FBX/"
for name in ("SM_Shop_A_001", "SM_HouseWall_A_001", "SM_HouseWall_A_001_HalfA", "SM_HouseWindow_A_001", "SM_RollupDoor_A_001", "SM_RollupDoor_A_002"):
    m = unreal.load_asset(AS + name)
    if not m:
        unreal.log_warning("[STALL] %s MISSING" % name)
        continue
    b = m.get_bounding_box()
    slots = [str(s.material_interface.get_name()) if s.material_interface else "None" for s in m.static_materials]
    sm = unreal.get_editor_subsystem(unreal.StaticMeshEditorSubsystem)
    unreal.log_warning("[STALL] %s tris %d min (%.1f, %.1f, %.1f) max (%.1f, %.1f, %.1f) slots %s" % (
        name, m.get_num_triangles(0), b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z, slots))
