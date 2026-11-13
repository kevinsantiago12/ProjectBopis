"""Read-only check of make_ue.py's assets: the material compiles (its shader statistics; errors land in the log),
the mesh's triangles, bounds and material, and the instance's parent.

    .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\FX\\MuzzleFlash\\verify_ue.py -Render"""
import unreal

DEST = "/Game/ThirdPerson/FX/MuzzleFlash"


def log(msg):
    unreal.log_warning("[VERIFY] " + msg)


mat = unreal.load_asset(DEST + "/M_MuzzleFlash")
stats = unreal.MaterialEditingLibrary.get_statistics(mat)
log("M_MuzzleFlash: blend %s, shading %s, two-sided %s" % (
    mat.get_editor_property("blend_mode"), mat.get_editor_property("shading_model"), mat.get_editor_property("two_sided")))
for field in ("num_vertex_shader_instructions", "num_pixel_shader_instructions", "num_samplers",
              "num_vertex_texture_samples", "num_pixel_texture_samples", "num_virtual_texture_samples",
              "num_uv_scalars", "num_interpolator_scalars"):
    try:
        log("  %s = %s" % (field, stats.get_editor_property(field)))
    except Exception as e:
        log("  %s: %s" % (field, e))

mesh = unreal.load_asset(DEST + "/SM_MuzzleFlash")
box = mesh.get_bounding_box()
log("SM_MuzzleFlash: %d verts, %d triangles, bounds (%.1f %.1f %.1f)..(%.1f %.1f %.1f), material %s, nanite %s" % (
    mesh.get_num_vertices(0), mesh.get_num_triangles(0), box.min.x, box.min.y, box.min.z, box.max.x, box.max.y,
    box.max.z, mesh.get_material(0).get_path_name() if mesh.get_material(0) else None,
    mesh.get_editor_property("nanite_settings").enabled))
inst = unreal.load_asset(DEST + "/MI_MuzzleFlash")
log("MI_MuzzleFlash parent: %s" % inst.get_editor_property("parent").get_path_name())
names = unreal.MaterialEditingLibrary.get_scalar_parameter_names(mat)
log("scalar parameters: %s" % [str(n) for n in names])

# The star look, for rifles: its instance's Spikes, its mesh's material, and which guns use it.
star = unreal.load_asset(DEST + "/MI_MuzzleFlash_Star")
for i in (inst, star):
    log("%s: Spikes %s" % (i.get_name(), unreal.MaterialEditingLibrary.get_material_instance_scalar_parameter_value(i, "Spikes")))
star_mesh = unreal.load_asset(DEST + "/SM_MuzzleFlash_Star")
log("SM_MuzzleFlash_Star: %d triangles, material %s" % (star_mesh.get_num_triangles(0), star_mesh.get_material(0).get_path_name()))
for name in ("BP_Pistol45", "BP_AssaultRifle"):
    cdo = unreal.get_default_object(unreal.load_object(None, "/Game/ThirdPerson/Blueprints/%s.%s_C" % (name, name)))
    fm, fs = cdo.get_editor_property("flash_mesh"), cdo.get_editor_property("flash_settings")
    log("%s: FlashMesh %s, length %s..%s, width %s..%s" % (name, fm.get_name() if fm else None,
        fs.length.min, fs.length.max, fs.width.min, fs.width.max))
