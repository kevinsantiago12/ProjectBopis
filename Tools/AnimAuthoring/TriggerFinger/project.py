"""The trigger finger's two one-frame poses (spec *Trigger finger*): the right index finger resting on the
trigger, and pressing it, made from MM_Rifle_Idle_Hipfire's frame 0 (the clip the aiming pose is built on)
with the M4 ridden on hand_r the way the game holds it. Only index_01_r down is used by the AnimGraph."""
import json
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "..", "lib"))

CLIP = "MM_Rifle_Idle_Hipfire"
CLIP_PATH = "/Game/Characters/Heroes/Mannequin/Animations/Locomotion/Rifle/" + CLIP
WEAPON_BP = "/Game/ThirdPerson/Blueprints/BP_AssaultRifle.BP_AssaultRifle_C"
SKELETON = "/Game/Characters/Mannequins/Meshes/SK_Mannequin"
DEST = "/Game/ThirdPerson/Animations/TriggerFinger"
CLIP_FBX = CLIP + ".fbx"
GUN_FBX = "Gun.fbx"
INFO = os.path.join(DIR, "export_result.json")


def info():
    with open(INFO) as f:
        return json.load(f)


def setup():
    """(rig, gun) at the clip's first frame, the gun in the right hand as the game places it."""
    import bpy
    import animlib as A
    rig = A.setup_character(DIR, CLIP_FBX)
    from mathutils import Matrix
    d = info()["weapon"]
    loc, rot = d["grip_location_offset"], d["grip_rotation_offset"]
    # The weapon mesh component's scale (BP_AssaultRifle 1.33) after the grip offset, as the game draws it.
    # Gun space below is then the mesh's own (raw) space. (First versions left it out: 10% off at 1.1.)
    scale = Matrix.Diagonal(tuple(d.get("scale", [1.0, 1.0, 1.0])) + (1.0,))
    gun = A.Gun(rig, os.path.join(DIR, GUN_FBX),
                A.ue_xform(loc, pitch=rot["pitch"], yaw=rot["yaw"], roll=rot["roll"]) @ scale)
    bpy.context.scene.frame_set(int(bpy.context.scene.frame_start))
    gun.place(rig)
    return rig, gun
