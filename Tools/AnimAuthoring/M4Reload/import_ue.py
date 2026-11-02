"""Headless import of the M4 reload: the character sequence + montage and the AR4's handle animation.
Checks the new sequence against MM_Rifle_Reload on the frames that weren't changed."""
import json
import math
import os
import traceback

import unreal

DIR = os.path.dirname(os.path.abspath(__file__))
ACTIONS = "/Game/Characters/Heroes/Mannequin/Animations/Actions"
AR4 = "/Game/FPS_Weapon_Bundle/Weapons/Meshes/AR4"
CHAMBER_TIME = 1.40  # the pull starts (Blender: grab 1.37, fully back 1.47)
out = {"errors": []}


def log(msg):
    unreal.log_warning("[M4IMPORT] " + str(msg))


def run():
    cvar = "Interchange.FeatureFlags.Import.FBX"
    unreal.SystemLibrary.execute_console_command(None, cvar + " 0")
    out["interchange_fbx"] = unreal.SystemLibrary.get_console_variable_bool_value(cvar)
    if out["interchange_fbx"]:
        raise RuntimeError("Interchange FBX import still on; not importing")

    tools = unreal.AssetToolsHelpers.get_asset_tools()

    def import_anim(fbx, dest, name, skeleton_path):
        skeleton = unreal.load_asset(skeleton_path)
        ui = unreal.FbxImportUI()
        ui.set_editor_property("import_mesh", False)
        ui.set_editor_property("import_animations", True)
        ui.set_editor_property("import_materials", False)
        ui.set_editor_property("import_textures", False)
        ui.set_editor_property("skeleton", skeleton)
        ui.set_editor_property("automated_import_should_detect_type", False)
        ui.set_editor_property("mesh_type_to_import", unreal.FBXImportType.FBXIT_ANIMATION)
        data = ui.get_editor_property("anim_sequence_import_data")
        data.set_editor_property("animation_length", unreal.FBXAnimationLengthImportType.FBXALIT_EXPORTED_TIME)
        data.set_editor_property("remove_redundant_keys", False)
        data.set_editor_property("import_uniform_scale", 1.0)
        task = unreal.AssetImportTask()
        task.set_editor_property("filename", os.path.join(DIR, fbx))
        task.set_editor_property("destination_path", dest)
        task.set_editor_property("destination_name", name)
        task.set_editor_property("automated", True)
        task.set_editor_property("replace_existing", True)
        task.set_editor_property("save", True)
        task.set_editor_property("options", ui)
        tools.import_asset_tasks([task])
        out.setdefault("imported", {})[name] = [str(p) for p in task.get_editor_property("imported_object_paths")]
        return unreal.load_asset(dest + "/" + name)

    orig = unreal.load_asset(ACTIONS + "/MM_Rifle_Reload")
    skeleton = orig.get_editor_property("skeleton").get_path_name()
    out["skeleton"] = skeleton
    new = import_anim("MM_Rifle_Reload_M4.fbx", ACTIONS, "MM_Rifle_Reload_M4", skeleton)
    out["new_length"] = new.get_play_length()
    out["new_frames"] = unreal.AnimationLibrary.get_num_frames(new)

    # Same pose where nothing was changed; the M4 section differs only in the arms.
    lib = unreal.AnimationLibrary
    bones = ["root", "pelvis", "spine_03", "head", "clavicle_l", "upperarm_l", "hand_l", "hand_r", "index_02_l"]
    checks = {}
    for t in (0.0, 0.3, 0.6, 0.9, 1.4, 2.0, 2.17):
        row = {}
        for b in bones:
            a = lib.get_bone_pose_for_time(orig, b, t, False)
            n = lib.get_bone_pose_for_time(new, b, t, False)
            dl = (a.translation - n.translation).length()
            qa, qn = a.rotation, n.rotation
            dot = abs(qa.x * qn.x + qa.y * qn.y + qa.z * qn.z + qa.w * qn.w)
            ang = math.degrees(2.0 * math.acos(min(1.0, dot)))
            ds = (a.scale3d - n.scale3d).length()
            row[b] = [round(dl, 3), round(ang, 2), round(ds, 4)]
        checks["%.2f" % t] = row
    out["pose_diff_loc_deg_scale"] = checks
    worst = max(max(v[0], v[1] / 2.0, v[2] * 100) for t in ("0.00", "0.30", "0.60", "2.17") for v in checks[t].values())
    out["worst_unchanged"] = worst
    if worst > 0.5:
        raise RuntimeError("imported sequence doesn't match the original where unchanged (%.3f); no montage" % worst)

    gun_skel = AR4 + "/SK_AR4_Skeleton"
    gun_anim = import_anim("A_AR4_Reload.fbx", AR4, "A_AR4_Reload", gun_skel)
    out["gun_length"] = gun_anim.get_play_length()
    gun = {}
    for t in (0.0, 1.37, 1.47, 1.51, 1.6):
        for b in ("b_gun_Root", "b_gun_chargehandle"):
            p = lib.get_bone_pose_for_time(gun_anim, b, t, False)
            gun["%s@%.2f" % (b, t)] = [round(p.translation.x, 2), round(p.translation.y, 2), round(p.translation.z, 2),
                                       round(p.scale3d.x, 3)]
    out["gun_pose"] = gun

    # The montage: same slot and blends as AM_Rifle_Reload, with its sound notifies (Chamber at the pull).
    montage_path = ACTIONS + "/AM_Rifle_Reload_M4"
    if unreal.EditorAssetLibrary.does_asset_exist(montage_path):
        montage = unreal.load_asset(montage_path)
        out["montage"] = "exists, left as is"
    else:
        factory = unreal.AnimMontageFactory()
        factory.set_editor_property("source_animation", new)
        montage = tools.create_asset("AM_Rifle_Reload_M4", ACTIONS, unreal.AnimMontage, factory)
        lib.add_animation_notify_track(montage, "1")
        for time, sound in ((0.366, unreal.WeaponSound.MAG_OUT), (0.984, unreal.WeaponSound.MAG_IN),
                            (CHAMBER_TIME, unreal.WeaponSound.CHAMBER)):
            notify = lib.add_animation_notify_event(montage, "1", time, unreal.AnimNotify_WeaponSound)
            notify.set_editor_property("sound", sound)
        unreal.EditorAssetLibrary.save_loaded_asset(montage)
        out["montage"] = "created"
    out["montage_length"] = montage.get_play_length()
    out["montage_slots"] = [str(t.get_editor_property("slot_name")) for t in montage.get_editor_property("slot_anim_tracks")]
    out["montage_blend"] = [montage.get_editor_property("blend_in").get_editor_property("blend_time"),
                            montage.get_editor_property("blend_out").get_editor_property("blend_time")]
    out["montage_notifies"] = [[round(lib.get_anim_notify_event_trigger_time(ev), 3),
                                str(ev.get_editor_property("notify").get_editor_property("sound"))]
                               for ev in lib.get_animation_notify_events(montage)]

    cls = unreal.load_object(None, "/Game/ThirdPerson/Blueprints/BP_AssaultRifle.BP_AssaultRifle_C")
    cdo = unreal.get_default_object(cls)
    for prop in ("chamber_sound", "mag_out_sound", "mag_in_sound"):
        try:
            v = cdo.get_editor_property(prop)
            out[prop] = v.get_path_name() if v else None
        except Exception as e:
            out[prop] = "ERR %s" % e


try:
    run()
except Exception:
    out["errors"].append(traceback.format_exc())
with open(os.path.join(DIR, "import_result.json"), "w") as f:
    json.dump(out, f, indent=1, default=str)
log("done, errors %d" % len(out["errors"]))
