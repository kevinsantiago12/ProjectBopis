# The Uzi's fire animation, on SK_Uzi.blend's skeleton (run RigUzi.py first).
#   blender --background --factory-startup --python AnimUzi.py -- <SK_Uzi.blend> <out dir>
# Writes A_Uzi_Fire.fbx (with the mesh, which the editor bridge's importer wants; delete the
# spare skeletal mesh it makes). 60 fps.
#
# The Uzi fires every 0.06 s (0.05 s for the duals, each gun every 0.1 s), and every shot
# restarts this, so the whole cycle fits in 3 frames: the bolt slams back in one and is home by
# the third. The cocking knob doesn't reciprocate on an Uzi, so only the bolt and trigger move.
# Fire notify at 0, Eject at 1.
import bpy, sys, os, math
from mathutils import Matrix, Vector

blend, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]
FPS = 60
# Bone -> keys (frame, back cm, turn degrees). The rig's barrel is +X here, so "back" is -X and
# the trigger turns about the gun's side-to-side axis (Y) through its pin.
TRACKS = {
    "bolt": [(0, 0.0, 0.0), (1, 4.5, 0.0), (3, 0.0, 0.0)],
    "trigger": [(0, 0.0, 12.0), (2, 0.0, 12.0), (3, 0.0, 0.0)],
}

bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
scene.render.fps = FPS
arm = bpy.data.objects["Armature"]
mesh = bpy.data.objects["SK_Uzi"]
action = bpy.data.actions.new("A_Uzi_Fire")
arm.animation_data_create()
arm.animation_data.action = action
end = max(k[0] for keys in TRACKS.values() for k in keys)


def key(name, frame, back, turn):
    pb = arm.pose.bones[name]
    world = arm.matrix_world @ arm.data.bones[name].matrix_local
    head = world.translation.copy()
    if turn:
        world = (Matrix.Translation(head) @ Matrix.Rotation(math.radians(turn), 4, 'Y')
                 @ Matrix.Translation(-head) @ world)
    if back:
        world = Matrix.Translation(Vector((-back, 0.0, 0.0))) @ world
    local = arm.convert_space(pose_bone=pb, matrix=arm.matrix_world.inverted() @ world,
                              from_space='POSE', to_space='LOCAL')
    loc, rot, _ = local.decompose()
    pb.rotation_mode = 'QUATERNION'
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
bpy.ops.export_scene.fbx(
    filepath=os.path.join(out_dir, "A_Uzi_Fire.fbx"),
    use_selection=True, object_types={'ARMATURE', 'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
    axis_forward='-Z', axis_up='Y', mesh_smooth_type='FACE', use_tspace=False,
    add_leaf_bones=False, primary_bone_axis='X', secondary_bone_axis='-Y',
    use_armature_deform_only=True, armature_nodetype='NULL',
    bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
    bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True,
    bake_anim_step=1.0, bake_anim_simplify_factor=0.0, path_mode='STRIP')
print(f"ANIM A_Uzi_Fire: frames 0-{end} ({end / FPS:.3f} s)")
