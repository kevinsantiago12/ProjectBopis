# Reworks the guns' own fire animations in the Benelli's style: a hard, linear slam back in
# about 2 frames at 60 fps, a frame's hold, a quick return, the shot on frame 0 and no dead tail.
#   blender --background --factory-startup --python AnimPass.py -- <AnimPass dir>
# Reads the user's FBX exports in that folder (Unreal's Asset Actions > Export, with the preview
# mesh) for each gun's skeleton and mesh, and writes A_<Gun>_<Anim>.fbx next to them. Import
# each onto the gun's existing skeleton.
#
# - Unreal's exports of animations keyed in the editor come out static (the keys sit in a layer
#   the FBX export leaves out), so these are built from the rest pose rather than edited.
# - Scene unit scale is set to 0.01 before importing, so Blender units are centimetres and the
#   rig survives the round trip unchanged (checked to 4e-6).
# - Every gun here points down -Y with +Z up, so "back" is +Y in world space and hammers and
#   triggers turn about world X through their bone's head.
import bpy, sys, os, math
from mathutils import Matrix, Vector

folder = sys.argv[sys.argv.index("--") + 1]
FPS = 60

# Gun -> (the export that carries its skeleton and mesh, {animation: {bone: keys}}).
# A key is (frame, back cm, turn degrees, axis, scale); bones not listed stay at rest.
HAMMER_92 = -55.0     # Beretta hammer cocked (the hammer falls to 0 on the shot)
HAMMER_1911 = -68.2   # the 1911 kit's cocked angle
# The 1911's trigger slides 3.5 mm (the kit's 6.7 mm took it out of sight inside the frame).
GUNS = {
    "Beretta": ("SK_Beretta_92FS_Fire", {
        "A_Beretta_Fire": {
            "Slide": [(0, 0), (1, 2.2), (2, 4.5), (3, 4.5), (6, 0), (8, 0)],
            "Barrel": [(0, 0), (1, 0.5), (2, 0.6), (3, 0.6), (6, 0), (8, 0)],
            "Hammer": [(0, 0, 0), (1, 0, -30), (2, 0, -62), (3, 0, -62), (6, 0, HAMMER_92), (8, 0, HAMMER_92)],
            "Trigger": [(0, 0, 10), (3, 0, 10), (6, 0, 0), (8, 0, 0)],
        },
        "A_Beretta_FireEmpty": {
            "Slide": [(0, 0), (1, 2.2), (2, 4.5), (3, 4.5), (5, 4.2), (8, 4.2)],
            "Barrel": [(0, 0), (1, 0.5), (2, 0.6), (3, 0.6), (5, 0), (8, 0)],
            "Hammer": [(0, 0, 0), (1, 0, -30), (2, 0, -62), (3, 0, -62), (5, 0, HAMMER_92), (8, 0, HAMMER_92)],
            "Trigger": [(0, 0, 10), (3, 0, 10), (6, 0, 0), (8, 0, 0)],
            "Slide_Stop": [(0, 0, 0), (2, 0, 0), (3, 0, -5), (8, 0, -5)],
        },
        "A_Beretta_Ready": {
            "Hammer": [(0, 0, HAMMER_92), (1, 0, HAMMER_92)],
        },
    }),
    "P1911": ("Anim_P1911_M_Shot", {
        "A_P1911_Fire": {
            "slider": [(0, 0), (1, 3.4), (2, 5.63), (3, 5.63), (6, 0), (8, 0)],
            "hammer": [(0, 0, 0), (1, 0, -36), (2, 0, -72), (3, 0, -72), (6, 0, HAMMER_1911), (8, 0, HAMMER_1911)],
            "trigger": [(0, 0.35), (3, 0.35), (6, 0), (8, 0)],
        },
        "A_P1911_FireEmpty": {
            "slider": [(0, 0), (1, 3.4), (2, 5.63), (8, 5.63)],
            "hammer": [(0, 0, 0), (1, 0, -36), (2, 0, -72), (3, 0, -72), (5, 0, HAMMER_1911), (8, 0, HAMMER_1911)],
            "trigger": [(0, 0.35), (3, 0.35), (6, 0), (8, 0)],
            "slider_lock": [(0, 0, 0), (2, 0, 0), (3, 0, 4.64), (8, 0, 4.64)],
        },
    }),
    "AR4": ("SK_AR4_Fire", {
        # 600 rpm: the whole cycle fits the 0.1 s between shots. The dust cover is open from the
        # first frame, so a burst (which restarts this every shot) never flickers it shut.
        "A_AR4_Fire": {
            "b_gun_shelleject": [(0, 0), (2, 4.0), (3, 4.0), (5, 0), (6, 0)],
            "b_gun_shelleject_hatch": [(0, 0, -150, 'Y'), (6, 0, -150, 'Y')],
            "b_gun_trigger": [(0, 0, 8), (4, 0, 8), (6, 0, 0)],
        },
    }),
    "Mossberg": ("Mossberg-500_Pump", {
        # Shot, then a rack: the bolt rides the pump; the spent shell comes back with it and is
        # gone at the ejection (the casing itself is thrown from code on the Eject notify).
        "A_Mossberg_Fire": {
            "trigger": [(0, 0, 10), (4, 0, 0), (24, 0, 0)],
            "pump": [(0, 0), (5, 0), (11, 9.0), (13, 9.0), (19, 0), (24, 0)],
            "ejectionport": [(0, 0), (5, 0), (11, 9.0), (13, 9.0), (19, 0), (24, 0)],
            "shell": [(0, 0), (5, 0), (10, 3.0), (11, 3.0, 0, 'X', 0.001), (16, 0, 0, 'X', 0.001),
                      (17, 0), (24, 0)],
        },
    }),
}


def load(name):
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.scale_length = 0.01
    bpy.ops.import_scene.fbx(filepath=os.path.join(folder, name + ".FBX"))
    scene.render.fps = FPS
    arm = next(o for o in scene.objects if o.type == 'ARMATURE')
    mesh = next(o for o in scene.objects if o.type == 'MESH')
    return scene, arm, mesh


def key(arm, name, frame, back=0.0, turn=0.0, axis='X', scale=1.0):
    # The bone's rest pose in world space, turned about a world axis through its head, slid
    # back along +Y and scaled in place; then keyed as the bone's local loc/rot/scale.
    pb = arm.pose.bones[name]
    world = arm.matrix_world @ arm.data.bones[name].matrix_local
    head = world.translation.copy()
    if turn:
        world = (Matrix.Translation(head) @ Matrix.Rotation(math.radians(turn), 4, axis)
                 @ Matrix.Translation(-head) @ world)
    if back:
        world = Matrix.Translation(Vector((0.0, back, 0.0))) @ world
    if scale != 1.0:
        world = world @ Matrix.Scale(scale, 4)
    local = arm.convert_space(pose_bone=pb, matrix=arm.matrix_world.inverted() @ world,
                              from_space='POSE', to_space='LOCAL')
    loc, rot, sca = local.decompose()
    pb.rotation_mode = 'QUATERNION'
    pb.location, pb.rotation_quaternion, pb.scale = loc, rot, sca
    for path in ("location", "rotation_quaternion", "scale"):
        pb.keyframe_insert(path, frame=frame)


def make(arm, name, tracks):
    action = bpy.data.actions.new(name)
    arm.animation_data_create()
    arm.animation_data.action = action
    end = max(k[0] for keys in tracks.values() for k in keys)
    for pb in arm.pose.bones:
        pb.location, pb.rotation_quaternion, pb.scale = (0, 0, 0), (1, 0, 0, 0), (1, 1, 1)
    for pb in arm.pose.bones:
        if pb.name not in tracks:
            for frame in (0, end):
                for path in ("location", "rotation_quaternion", "scale"):
                    pb.keyframe_insert(path, frame=frame)
    for bone, keys in tracks.items():
        for k in keys:
            frame, back = k[0], k[1]
            turn = k[2] if len(k) > 2 else 0.0
            axis = k[3] if len(k) > 3 else 'X'
            scale = k[4] if len(k) > 4 else 1.0
            key(arm, bone, frame, back, turn, axis, scale)
    for curve in action.fcurves:
        for point in curve.keyframe_points:
            point.interpolation = 'LINEAR'
    return end


for gun, (source, anims) in GUNS.items():
    for name, tracks in anims.items():
        scene, arm, mesh = load(source)
        end = make(arm, name, tracks)
        scene.frame_start, scene.frame_end = 0, end
        for o in scene.objects:
            o.select_set(o in (arm, mesh))
        bpy.ops.export_scene.fbx(
            filepath=os.path.join(folder, name + ".fbx"), use_selection=True,
            object_types={'ARMATURE', 'MESH'},
            apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
            axis_forward='-Z', axis_up='Y', primary_bone_axis='Y', secondary_bone_axis='X',
            add_leaf_bones=False, armature_nodetype='NULL', use_armature_deform_only=False,
            mesh_smooth_type='FACE', bake_anim=True, bake_anim_use_all_bones=True,
            bake_anim_use_nla_strips=False, bake_anim_use_all_actions=False,
            bake_anim_force_startend_keying=True, bake_anim_step=1.0,
            bake_anim_simplify_factor=0.0, path_mode='STRIP')
        print(f"ANIM {name} ({gun}): frames 0-{end} ({end / FPS:.3f} s)")
