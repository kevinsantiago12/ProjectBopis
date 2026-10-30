# Makes the AK-74u stockless: deletes the stock and its sling ring from the FPS bundle's SK_KA74U_Y and
# keeps every other vertex, bone and axis as it was, so the result imports onto the same skeleton
# (SK_KA74U_Y_Skeleton) and the gun's sockets, grip offsets and magazine still line up.
#   blender --background --factory-startup --python StripStockAK.py -- <SK_KA74U_Y FBX> <out dir>
# The source is the user's Unreal export (2026-10-30), kept in Source/ (named SM_KA74U_Y.FBX by the
# export dialog, but it's the skeletal mesh). Writes SK_KA74U_Stockless.fbx.
#
# - Round trip as in AnimPass.py: the scene's unit scale is 0.01 before the import, so the armature
#   comes in at scale 1 in cm, and the export settings below give Unreal back its own bone frames.
# - Blender makes the root bone (b_gun_Root) the armature object, so the body's vertices, skinned to
#   the root, come in with no group. They export unweighted, and Unreal's importer binds unweighted
#   vertices to the root bone, which is where they were.
import bpy, bmesh, sys, os

src, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]
STOCK_BONES = {"b_gun_stock", "b_gun_stock_ring"}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.scale_length = 0.01
bpy.ops.import_scene.fbx(filepath=src)
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
mesh = next(o for o in scene.objects if o.type == 'MESH')

stock_groups = {g.index for g in mesh.vertex_groups if g.name in STOCK_BONES}
if len(stock_groups) != len(STOCK_BONES):
    raise SystemExit(f"stock groups missing: {STOCK_BONES - {g.name for g in mesh.vertex_groups}}")

before = (len(mesh.data.vertices), sum(len(p.vertices) - 2 for p in mesh.data.polygons))
bm = bmesh.new()
bm.from_mesh(mesh.data)
deform = bm.verts.layers.deform.verify()
doomed = [v for v in bm.verts if any(g in stock_groups and w > 0.0 for g, w in v[deform].items())]
bmesh.ops.delete(bm, geom=doomed, context='VERTS')
bm.to_mesh(mesh.data)
bm.free()
for g in [g for g in mesh.vertex_groups if g.name in STOCK_BONES]:
    mesh.vertex_groups.remove(g)
mesh.name = mesh.data.name = "SK_KA74U_Stockless"

ys = [-(mesh.matrix_world @ v.co).y for v in mesh.data.vertices]
after = (len(mesh.data.vertices), sum(len(p.vertices) - 2 for p in mesh.data.polygons))
print(f"removed {len(doomed)} stock vertices: verts {before[0]} -> {after[0]}, tris {before[1]} -> {after[1]}")
print(f"length now {max(ys) - min(ys):.1f} cm (Unreal y {min(ys):.1f}..{max(ys):.1f})")
print("groups", [g.name for g in mesh.vertex_groups], "slots", [s.material.name for s in mesh.material_slots if s.material])

os.makedirs(out_dir, exist_ok=True)
for o in scene.objects:
    o.select_set(o in (arm, mesh))
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(
    filepath=os.path.join(out_dir, "SK_KA74U_Stockless.fbx"), use_selection=True,
    object_types={'ARMATURE', 'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
    axis_forward='-Z', axis_up='Y', primary_bone_axis='Y', secondary_bone_axis='X',
    add_leaf_bones=False, armature_nodetype='NULL', use_armature_deform_only=False,
    mesh_smooth_type='FACE', use_tspace=False, bake_anim=False, path_mode='STRIP')
print("written", out_dir)
