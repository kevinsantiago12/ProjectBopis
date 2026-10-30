# The Benelli's gun-side animations, on SK_Benelli.blend's skeleton (run RigBenelli.py first).
#   blender --background --factory-startup --python AnimBenelli.py -- <SK_Benelli.blend> <out dir>
# Writes A_Benelli_Fire.fbx, A_Benelli_LastShot.fbx and A_Benelli_Ready.fbx (import onto
# SK_Benelli_Skeleton with animations on). 60 fps.
#
# - Fire: the gas system throws the bolt back and the spring returns it; the trigger is pulled
#   at frame 0 and lets go as the bolt closes. Fire notify at 0, Eject when the bolt is back.
# - LastShot: the same, but the bolt catch holds it open (it settles a little forward of full
#   travel). Its last frame is the empty gun's rest pose.
# - Ready: the bind pose, bolt closed: what a loaded gun rests in.
import bpy, sys, os, math

blend, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]
FPS = 60
BOLT_TRAVEL = 6.0      # cm back: the charging handle reaches the back of its slot
BOLT_CAUGHT = 5.5      # cm back, held by the bolt catch
TRIGGER_PULL = 6.0     # degrees

bpy.ops.wm.open_mainfile(filepath=blend)
scene = bpy.context.scene
scene.render.fps = FPS
arm = bpy.data.objects["Armature"]
mesh = bpy.data.objects["SK_Benelli"]
arm.animation_data_create()
for b in arm.pose.bones:
    b.rotation_mode = 'XYZ'


# Pose-bone axes here: local Y runs down the barrel (+X in Unreal), local X is to the gun's
# left. So the bolt goes back along -Y, and a negative X rotation swings the trigger's blade
# back about its pin.
def key(frame, bolt=0.0, trigger=0.0):
    scene.frame_set(frame)
    pb = arm.pose.bones
    pb["bolt"].location = (0.0, -bolt, 0.0)
    pb["trigger"].rotation_euler = (math.radians(-trigger), 0.0, 0.0)
    for b in pb:
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
    "A_Benelli_Fire": [(0, 0.0, TRIGGER_PULL), (2, BOLT_TRAVEL, TRIGGER_PULL), (3, BOLT_TRAVEL, TRIGGER_PULL),
                       (6, 0.0, 0.0), (8, 0.0, 0.0)],
    "A_Benelli_LastShot": [(0, 0.0, TRIGGER_PULL), (2, BOLT_TRAVEL, TRIGGER_PULL), (4, BOLT_CAUGHT, TRIGGER_PULL),
                           (6, BOLT_CAUGHT, 0.0), (8, BOLT_CAUGHT, 0.0)],
    "A_Benelli_Ready": [(0, 0.0, 0.0), (1, 0.0, 0.0)],
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
