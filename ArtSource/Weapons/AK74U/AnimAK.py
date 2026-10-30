# The AK-74u's fire animation, on the stockless mesh's skeleton (SK_KA74U_Y_Skeleton).
#   blender --background --factory-startup --python AnimAK.py -- <SK_KA74U_Stockless.fbx> <out dir>
# Writes A_AK74U_Fire.fbx (with the mesh, which the editor bridge's importer wants; delete the
# spare skeletal mesh it makes). 60 fps.
#
# The AK fires every 0.075 s (4.5 frames) and every shot restarts this, so the carrier's cycle
# fits in 4 frames: slammed back in one, held one, home by the fourth. b_gun_shelleject is the
# bolt carrier with its charging handle, so the handle reciprocates on the right side. The
# trigger stays pulled past the next shot (frame 4.5), so it never flickers in a burst, and lets
# go after the last one. Fire notify at 0, Eject at 1 (the carrier back).
#
# Round trip as in AnimPass.py (same bundle as the M4): scene unit scale 0.01 before the import,
# posed in world space, where the barrel runs to -Y, so back is +Y and the trigger turns about X
# through its pin (positive swings the blade, below the pin, back). The armature object is
# rotated, so the pose bones' own space is not the world's.
import bpy, sys, os, math
from mathutils import Matrix, Vector

src, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]
FPS = 60
CARRIER_TRAVEL = 8.0   # cm back: the handle at the rear of the port, the port open
TRIGGER_PULL = 8.0     # degrees, as the M4's
# Bone -> keys (frame, back cm, turn degrees). Bones not listed stay at rest.
TRACKS = {
    "b_gun_shelleject": [(0, 0.0, 0.0), (1, CARRIER_TRAVEL, 0.0), (2, CARRIER_TRAVEL, 0.0),
                         (4, 0.0, 0.0), (7, 0.0, 0.0)],
    "b_gun_trigger": [(0, 0.0, TRIGGER_PULL), (5, 0.0, TRIGGER_PULL), (7, 0.0, 0.0)],
}

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.scale_length = 0.01
bpy.ops.import_scene.fbx(filepath=src)
scene.render.fps = FPS
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
mesh = next(o for o in scene.objects if o.type == 'MESH')
action = bpy.data.actions.new("A_AK74U_Fire")
arm.animation_data_create()
arm.animation_data.action = action
end = max(k[0] for keys in TRACKS.values() for k in keys)


def key(name, frame, back, turn):
    pb = arm.pose.bones[name]
    world = arm.matrix_world @ arm.data.bones[name].matrix_local
    head = world.translation.copy()
    if turn:
        world = (Matrix.Translation(head) @ Matrix.Rotation(math.radians(turn), 4, 'X')
                 @ Matrix.Translation(-head) @ world)
    if back:
        world = Matrix.Translation(Vector((0.0, back, 0.0))) @ world
    local = arm.convert_space(pose_bone=pb, matrix=arm.matrix_world.inverted() @ world,
                              from_space='POSE', to_space='LOCAL')
    loc, rot, _ = local.decompose()
    pb.location, pb.rotation_quaternion = loc, rot
    for path in ("location", "rotation_quaternion"):
        pb.keyframe_insert(path, frame=frame)


for pb in arm.pose.bones:
    pb.rotation_mode = 'QUATERNION'
    if pb.name not in TRACKS:
        for frame in (0, end):
            for path in ("location", "rotation_quaternion"):
                pb.keyframe_insert(path, frame=frame)
for bone, keys in TRACKS.items():
    for frame, back, turn in keys:
        key(bone, frame, back, turn)
for curve in action.fcurves:
    for point in curve.keyframe_points:
        point.interpolation = 'LINEAR'

scene.frame_start, scene.frame_end = 0, end
for o in scene.objects:
    o.select_set(o in (arm, mesh))
bpy.context.view_layer.objects.active = arm
os.makedirs(out_dir, exist_ok=True)
bpy.ops.export_scene.fbx(
    filepath=os.path.join(out_dir, "A_AK74U_Fire.fbx"), use_selection=True,
    object_types={'ARMATURE', 'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
    axis_forward='-Z', axis_up='Y', primary_bone_axis='Y', secondary_bone_axis='X',
    add_leaf_bones=False, armature_nodetype='NULL', use_armature_deform_only=False,
    mesh_smooth_type='FACE', use_tspace=False,
    bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True,
    bake_anim_step=1.0, bake_anim_simplify_factor=0.0, path_mode='STRIP')
print(f"ANIM A_AK74U_Fire: frames 0-{end} ({end / FPS:.3f} s)")
