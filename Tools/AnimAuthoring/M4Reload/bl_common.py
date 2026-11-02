"""Shared Blender setup for the M4 reload: imports the reload, Manny and the AR4, and rides the gun on
hand_r the way the game does (WeaponHolderComponent: snap to hand_r, then GripLocationOffset).

Spaces: everything is worked in the character armature's own space, which is the FBX space Unreal
exported (centimetres, Unreal's axes with Y negated)."""
import math
import os

import bpy
from mathutils import Matrix, Vector

DIR = os.path.dirname(os.path.abspath(__file__))
GRIP_OFFSET = Vector((1.0, 0.0, -2.0))  # BP_AssaultRifle GripLocationOffset (1,0,-2), Y negated -> (1,-0,-2)


GUN_ROOT = Matrix.Identity(4)  # b_gun_Root in the gun's component space; Blender makes it the object


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = 30


def import_fbx(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(DIR, name), use_anim=True, automatic_bone_orientation=False,
                             ignore_leaf_bones=False)
    return [o for o in bpy.data.objects if o not in before]


def setup():
    clear_scene()
    anim_objs = import_fbx("MM_Rifle_Reload.fbx")
    rig = next(o for o in anim_objs if o.type == "ARMATURE")
    rig.name = "Rig"
    manny_objs = import_fbx("SKM_Manny_Simple.fbx")
    manny_rig = next(o for o in manny_objs if o.type == "ARMATURE")
    for o in manny_objs:
        if o.type == "MESH":
            o.parent = rig
            o.matrix_parent_inverse = Matrix.Identity(4)
            for mod in o.modifiers:
                if mod.type == "ARMATURE":
                    mod.object = rig
    bpy.data.objects.remove(manny_rig, do_unlink=True)

    gun_objs = import_fbx("SK_AR4.fbx")
    gun = next(o for o in gun_objs if o.type == "ARMATURE")
    gun.name = "Gun"
    global GUN_ROOT
    GUN_ROOT = rig.matrix_world.inverted() @ gun.matrix_world
    print("RIGBONES", [b.name for b in rig.data.bones][:6], "count", len(rig.data.bones))
    print("GUNROOT", [[round(v, 3) for v in row] for row in GUN_ROOT])
    scene = bpy.context.scene
    act = rig.animation_data.action
    scene.frame_start = int(act.frame_range[0])
    scene.frame_end = int(act.frame_range[1])
    return rig, gun


def hand_r_matrix(rig):
    """hand_r in the rig's space (cm)."""
    return rig.pose.bones["hand_r"].matrix.copy()


# BP_PlayerCharacter attaches to the HandGrip_R socket on hand_r: (-7.012, 2.049, 0), yaw 90 in Unreal;
# with Y negated that's (-7.012, -2.049, 0) and -90 about Z.
HANDGRIP_R = Matrix.Translation(Vector((-7.012, -2.049, 0.0))) @ Matrix.Rotation(math.radians(-90.0), 4, "Z")


def gun_matrix(rig):
    """The gun's component space in the rig's space, as WeaponHolderComponent places it."""
    return hand_r_matrix(rig) @ HANDGRIP_R @ Matrix.Translation(GRIP_OFFSET)


def place_gun(rig, gun):
    gun.matrix_world = rig.matrix_world @ gun_matrix(rig) @ GUN_ROOT


def gun_bone_rest(gun, name):
    """A gun bone's rest matrix in the gun's component space (cm)."""
    if name == "b_gun_Root":
        return GUN_ROOT.copy()
    return GUN_ROOT @ gun.data.bones[name].matrix_local


def to_gun(rig, point_rig):
    return gun_matrix(rig).inverted() @ point_rig


def setup_render(res=(960, 600)):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "OBJECT"
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.image_settings.file_format = "PNG"
    world = bpy.data.worlds.new("W")
    scene.world = world
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 35
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    return cam


def look_at(cam, eye, target):
    direction = (target - eye).normalized()
    cam.location = eye
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()
