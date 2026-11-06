"""Headless and read-only: bounds, triangles, LODs, collision and material slots of the meshes the street dressing draws on: wires,
meters, tanks, aerials, lights, shutters, gates, tarps, signs. So the generator can fit them by measurement, not by their names.
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\street_shape_ue.py"""
import unreal

AS = "/Game/AsiaSlum/FBX/"
FV = "/Game/Megapack/Meshes/Favela/"
ME = "/Game/Megapack/Meshes/MiddleEast/"
MESHES = [AS + "SM_Cable_A_00%d" % i for i in range(1, 8)] + [AS + "SM_Cable_C_001", AS + "SM_Cable_D_001"] + [
    AS + "SM_ElectricBox_C_00%d" % i for i in (2, 3, 4)] + [AS + "SM_ElectricalBox_A_003"] + [
    AS + "SM_Antenna_A_00%d" % i for i in (1, 2, 3)] + [ME + "SM_Antenna_01", FV + "SM_AntennaSupportPart_01", FV + "SM_AntennaSupportPart_02"] + [
    AS + "SM_Light_A_00%d" % i for i in (1, 2, 3, 4)] + [
    FV + "SM_Barrel_01", FV + "SM_Barrel_Cap_01", FV + "SM_Barrel_Cap_2", FV + "SM_Stand_01", FV + "SM_Fencing_03"] + [
    FV + "SM_StreetLamp_0%d" % i for i in (2, 3, 5, 6, 7, 8)] + [
    AS + "SM_RollupDoor_A_001", AS + "SM_RollupDoor_A_002", AS + "SM_RollupDoorFrame_A_001", AS + "SM_RollupDoorFrame_A_002",
    FV + "SM_Metal_Gate_01", ME + "SM_metal_gate_01", AS + "SM_TarpCover_A_001", AS + "SM_TarpCover_A_002"] + [
    AS + "SM_Sign_A_001", AS + "SM_Sign_A_002"] + [AS + "SM_Sign_B_00%d" % i for i in range(1, 6)] + [
    AS + "SM_DamageWall_A_001", AS + "SM_DamageWall_A_002"]


def mat_note(mi):
    if not mi:
        return "None"
    name = mi.get_path_name().split(".")[-1]
    base = mi
    while isinstance(base, unreal.MaterialInstance) and base.get_editor_property("parent"):
        base = base.get_editor_property("parent")
    if isinstance(base, unreal.Material):
        return "%s(%s,%s,%s)" % (name, str(base.get_editor_property("blend_mode")).split(".")[-1].split(":")[0],
                                 "2side" if base.get_editor_property("two_sided") else "1side",
                                 str(base.get_editor_property("material_domain")).split(".")[-1].split(":")[0])
    return name


for p in MESHES:
    m = unreal.load_asset(p)
    if not m:
        unreal.log_warning("[STREET] %s MISSING" % p)
        continue
    lods = m.get_num_lods()
    tris = [m.get_num_triangles(i) for i in range(lods)]
    b = m.get_bounding_box()
    body = m.get_editor_property("body_setup")
    coll = str(body.get_editor_property("collision_trace_flag")).split(".")[-1].split(":")[0] if body else "none"
    mats = [mat_note(s.material_interface) for s in m.static_materials]
    unreal.log_warning("[STREET] %s lods %d tris %s min (%.1f, %.1f, %.1f) max (%.1f, %.1f, %.1f) coll %s mats %s" % (
        p.split("/")[-1], lods, tris, b.min.x, b.min.y, b.min.z, b.max.x, b.max.y, b.max.z, coll, mats))
