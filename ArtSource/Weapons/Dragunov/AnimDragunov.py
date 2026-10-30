# The Dragunov's gun-side animations, on SK_Dragunov.blend's skeleton (run RigDragunov.py first).
#   blender --background --factory-startup --python AnimDragunov.py -- <SK_Dragunov.blend> <out dir>
# Writes A_Dragunov_Fire.fbx, A_Dragunov_LastShot.fbx and A_Dragunov_Ready.fbx (import onto
# SK_Dragunov_Skeleton with animations on). 60 fps.
#
# - Fire: the gas piston throws the bolt carrier (and its charging handle) back and the spring
#   returns it; the trigger is pulled at frame 0 and lets go as the bolt closes. Fire notify at 0,
#   Eject when the carrier is back. A little slower than the Benelli's: a heavier action.
# - LastShot: the same, but the bolt stop holds the carrier open (a little forward of full
#   travel). Its last frame is the empty gun's rest pose.
# - Ready: the bind pose, bolt closed: what a loaded gun rests in.
import bpy, sys, os, math
from mathutils import Matrix, Vector

blend, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]
FPS = 60
BOLT_TRAVEL = 8.0      # cm back (mesh units): the carrier's stroke, the port fully open
BOLT_CAUGHT = 7.5      # cm back, held by the bolt stop
TRIGGER_PULL = 8.0     # degrees

bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
scene.render.fps = FPS
arm = bpy.data.objects["Armature"]
mesh = bpy.data.objects["SK_Dragunov"]
arm.animation_data_create()
for b in arm.pose.bones:
    b.rotation_mode = 'XYZ'


# Posed in the armature's space, which is the world here (the armature sits at the origin): the
# barrel runs to Blender -Y (Unreal +Y), so back is +Y, and the trigger turns about the gun's
# crosswise axis (X) through its pin — a positive turn swings the blade, below the pin, back.
def place(name, move):
    pb = arm.pose.bones[name]
    pb.matrix = move @ pb.bone.matrix_local


def key(frame, bolt=0.0, trigger=0.0):
    scene.frame_set(frame)
    place("bolt", Matrix.Translation((0.0, bolt, 0.0)))
    pin = arm.pose.bones["trigger"].bone.matrix_local.translation
    place("trigger", Matrix.Translation(pin) @ Matrix.Rotation(math.radians(trigger), 4, 'X') @ Matrix.Translation(-pin))
    bpy.context.view_layer.update()
    for b in arm.pose.bones:
        b.keyframe_insert("location", frame=frame)
        b.keyframe_insert("rotation_euler", frame=frame)


def make(name, keys):
    action = bpy.data.actions.new(name)
    arm.animation_data.action = action
    for frame, bolt, trigger in keys:
        key(frame, bolt, trigger)
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = 'LINEAR'
    return action, (keys[0][0], keys[-1][0])


ANIMS = {
    "A_Dragunov_Fire": [(0, 0.0, TRIGGER_PULL), (3, BOLT_TRAVEL, TRIGGER_PULL), (4, BOLT_TRAVEL, TRIGGER_PULL),
                        (8, 0.0, 0.0), (10, 0.0, 0.0)],
    "A_Dragunov_LastShot": [(0, 0.0, TRIGGER_PULL), (3, BOLT_TRAVEL, TRIGGER_PULL), (5, BOLT_CAUGHT, TRIGGER_PULL),
                            (8, BOLT_CAUGHT, 0.0), (10, BOLT_CAUGHT, 0.0)],
    "A_Dragunov_Ready": [(0, 0.0, 0.0), (1, 0.0, 0.0)],
}

os.makedirs(out_dir, exist_ok=True)
for name, keys in ANIMS.items():
    action, (start, end) = make(name, keys)
    scene.frame_start, scene.frame_end = start, end
    # The mesh rides along: the editor bridge's importer wants a mesh in the file. Delete the
    # extra skeletal mesh it makes; keep the animation.
    for o in scene.objects:
        o.select_set(o in (arm, mesh))
    bpy.context.view_layer.objects.active = arm
    bpy.ops.export_scene.fbx(
        filepath=os.path.join(out_dir, name + ".fbx"),
        use_selection=True, object_types={'ARMATURE', 'MESH'},
        mesh_smooth_type='FACE', use_tspace=False,
        apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
        axis_forward='-Z', axis_up='Y',
        add_leaf_bones=False, primary_bone_axis='X', secondary_bone_axis='-Y',
        use_armature_deform_only=True, armature_nodetype='NULL',
        bake_anim=True, bake_anim_use_all_bones=True, bake_anim_use_nla_strips=False,
        bake_anim_use_all_actions=False, bake_anim_force_startend_keying=True,
        bake_anim_step=1.0, bake_anim_simplify_factor=0.0, path_mode='STRIP')
    print(f"ANIM {name}: frames {start}-{end} ({(end - start) / FPS:.3f} s)")
