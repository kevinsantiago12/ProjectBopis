"""Export the authored M4 reload (character) and the AR4's handle animation as FBX for Unreal.

Opens m4_reload.blend (saved by bl_author.py). The armature objects take their root bones' names, since
Blender made each FBX's root bone the object: 'root' for the character, 'b_gun_Root' for the gun."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

DIR = os.path.dirname(os.path.abspath(__file__))
bpy.ops.wm.open_mainfile(filepath=os.path.join(DIR, "m4_reload.blend"))
scene = bpy.context.scene
scene.render.fps = 30
scene.frame_start = 1
scene.frame_end = 67  # 66 frames: 2.2 s
# 1 Blender unit = 1 cm, as Unreal expects, so the exporter writes the cm data unscaled.
scene.unit_settings.system = "METRIC"
scene.unit_settings.scale_length = 0.01

# bl_author.py saves before rendering, so the gun is still where it was imported (its root bone's rest).
rig = bpy.data.objects["Rig"]
gun = bpy.data.objects["Gun"]


def export(obj, name, path):
    # The import left the armature objects at 1/100 scale (cm data in a metre scene); exported as is,
    # that lands on the root bone in Unreal. The bone data is already in cm, so drop it.
    # The FBX import also keyed the root bone's track onto the object itself, 1/100 scale included, and
    # those keys win over the object's transform. The reload's root never moves, so drop them.
    if obj.animation_data and obj.animation_data.action:
        act = obj.animation_data.action
        for fc in [fc for fc in act.fcurves if not fc.data_path.startswith("pose.bones")]:
            act.fcurves.remove(fc)
    loc, rot, _ = obj.matrix_world.decompose()
    obj.matrix_world = Matrix.LocRotScale(loc, rot, Vector((1.0, 1.0, 1.0)))
    obj.name = name
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"ARMATURE"}, add_leaf_bones=False,
        primary_bone_axis="Y", secondary_bone_axis="X", armature_nodetype="NULL",
        axis_forward="-Y", axis_up="Z", global_scale=1.0, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE", bake_space_transform=False,
        bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0,
        use_armature_deform_only=False)
    print("EXPORTED", path)


export(rig, "root", os.path.join(DIR, "MM_Rifle_Reload_M4.fbx"))
print("GUN matrix_world", [[round(v, 4) for v in row] for row in gun.matrix_world])
export(gun, "b_gun_Root", os.path.join(DIR, "A_AR4_Reload.fbx"))
