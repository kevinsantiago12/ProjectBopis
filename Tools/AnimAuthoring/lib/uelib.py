"""Shared helpers for the headless Unreal side of the animation projects. The scripts run inside the editor's
Python (UnrealEditor-Cmd -run=pythonscript; see RunUnreal.ps1); each project's export_ue.py writes the FBX and
JSON its Blender scripts read, and its import_ue.py brings the results back."""
import json
import math
import os
import traceback

import unreal

lib = unreal.AnimationLibrary
eal = unreal.EditorAssetLibrary
ACTIONS = "/Game/Characters/Heroes/Mannequin/Animations/Actions"
MANNY = "/Game/Characters/Mannequins/Meshes/SKM_Manny_Simple"


def log(tag, msg):
    unreal.log_warning("[%s] %s" % (tag, msg))


def write_json(path, data):
    with open(path, "w") as f:
        json.dump(data, f, indent=1, default=str)


def attempt(d, key, fn):
    """d[key] = fn(), or the error as text: one failed field doesn't lose the rest."""
    try:
        d[key] = fn()
    except Exception as e:
        d[key] = "ERR %s" % e


def vec(v):
    return [v.x, v.y, v.z]


def rot(r):
    return {"roll": r.roll, "pitch": r.pitch, "yaw": r.yaw}


def quat(q):
    return [q.x, q.y, q.z, q.w]


def xform(t):
    return {"loc": vec(t.translation), "rot": quat(t.rotation), "scale": vec(t.scale3d)}


def path_of(v):
    return v.get_path_name() if v is not None and hasattr(v, "get_path_name") else str(v)


# --- Export ------------------------------------------------------------------------------------------------
def fbx_export_options():
    o = unreal.FbxExportOption()
    o.ascii = False
    o.collision = False
    o.level_of_detail = False
    o.vertex_color = False
    o.map_skeletal_motion_to_root = False
    o.export_morph_targets = False
    try:
        o.export_preview_mesh = False      # an anim with its preview mesh needs rendering
    except Exception:
        pass
    return o


def export_asset(asset, path, info):
    """Exports an anim sequence, skeletal or static mesh as FBX, unless the file exists already. Skeletal meshes
    need rendering (RunUnreal.ps1 -Render). Results go in info["exports"], failures in info["errors"]."""
    if os.path.exists(path):
        return
    try:
        if isinstance(asset, str):
            asset = unreal.load_asset(asset)
        if isinstance(asset, unreal.AnimSequence):
            exporter = unreal.AnimSequenceExporterFBX()
        elif isinstance(asset, unreal.SkeletalMesh):
            exporter = unreal.SkeletalMeshExporterFBX()
        else:
            exporter = unreal.StaticMeshExporterFBX()
        task = unreal.AssetExportTask()
        task.object = asset
        task.filename = path
        task.automated = True
        task.prompt = False
        task.replace_identical = True
        task.exporter = exporter
        task.options = fbx_export_options()
        info.setdefault("exports", {})[os.path.basename(path)] = bool(unreal.Exporter.run_asset_export_task(task))
    except Exception:
        info.setdefault("errors", []).append(traceback.format_exc())


# --- Reading -----------------------------------------------------------------------------------------------
def notify_list(asset):
    """[time, notify class, Weapon Sound value] for every notify."""
    out = []
    for ev in lib.get_animation_notify_events(asset):
        n = ev.get_editor_property("notify")
        name = n.get_class().get_name() if n else None
        e = [round(lib.get_anim_notify_event_trigger_time(ev), 4), name, ""]
        if name == "AnimNotify_WeaponSound":
            e[2] = str(n.get_editor_property("sound"))
        out.append(e)
    return out


def curves(asset):
    c = {}
    for name in lib.get_animation_curve_names(asset, unreal.RawCurveTrackTypes.RCT_FLOAT):
        times, values = lib.get_float_keys(asset, name)
        c[str(name)] = [[round(t, 4), round(v, 4)] for t, v in zip(times, values)]
    return c


def anim_info(asset):
    if isinstance(asset, str):
        asset = unreal.load_asset(asset)
    a = {}
    attempt(a, "length", asset.get_play_length)
    attempt(a, "frames", lambda: lib.get_num_frames(asset))
    attempt(a, "skeleton", lambda: asset.get_editor_property("skeleton").get_path_name())
    attempt(a, "additive", lambda: str(asset.get_editor_property("additive_anim_type")))
    attempt(a, "curves", lambda: curves(asset))
    attempt(a, "notifies", lambda: notify_list(asset))
    attempt(a, "tracks", lambda: [str(n) for n in lib.get_animation_track_names(asset)])
    return a


def montage_segments(montage):
    return [{"slot": str(t.get_editor_property("slot_name")),
             "anim": path_of(s.get_editor_property("anim_reference")),
             "start_pos": s.get_editor_property("start_pos"),
             "anim_start": s.get_editor_property("anim_start_time"),
             "anim_end": s.get_editor_property("anim_end_time"),
             "rate": s.get_editor_property("anim_play_rate")}
            for t in montage.get_editor_property("slot_anim_tracks")
            for s in t.get_editor_property("anim_track").get_editor_property("anim_segments")]


def montage_info(montage):
    if isinstance(montage, str):
        montage = unreal.load_asset(montage)
    m = {}
    attempt(m, "length", montage.get_play_length)
    attempt(m, "blend", lambda: [montage.get_editor_property("blend_in").get_editor_property("blend_time"),
                                 montage.get_editor_property("blend_out").get_editor_property("blend_time")])
    attempt(m, "blend_out_trigger", lambda: montage.get_editor_property("blend_out_trigger_time"))
    attempt(m, "sections", lambda: [str(montage.get_section_name(i)) for i in range(montage.get_num_sections())])
    attempt(m, "segments", lambda: montage_segments(montage))
    attempt(m, "notifies", lambda: notify_list(montage))
    return m


def sockets(mesh):
    if isinstance(mesh, str):
        mesh = unreal.load_asset(mesh)
    out = []
    for i in range(mesh.num_sockets()):
        s = mesh.get_socket_by_index(i)
        out.append({"name": str(s.get_editor_property("socket_name")), "bone": str(s.get_editor_property("bone_name")),
                    "loc": vec(s.get_editor_property("relative_location")),
                    "rot": rot(s.get_editor_property("relative_rotation")),
                    "scale": vec(s.get_editor_property("relative_scale"))})
    return out


def blueprint_defaults(bp_class_path, props):
    """Class defaults of a Blueprint ('/Game/.../BP_X.BP_X_C'), by snake_case property name."""
    cdo = unreal.get_default_object(unreal.load_object(None, bp_class_path))
    out = {}
    for p in props:
        def get(p=p):
            v = cdo.get_editor_property(p)
            if isinstance(v, unreal.Vector):
                return vec(v)
            if isinstance(v, unreal.Rotator):
                return rot(v)
            if isinstance(v, unreal.Map):
                return {str(k): path_of(val) for k, val in v.items()}
            return path_of(v) if hasattr(v, "get_path_name") else str(v)
        attempt(out, p, get)
    return out


def pose_diff(a, b):
    """[location cm, rotation degrees, scale] between two bone transforms."""
    qa, qb = a.rotation, b.rotation
    dot = abs(qa.x * qb.x + qa.y * qb.y + qa.z * qb.z + qa.w * qb.w)
    return [round((a.translation - b.translation).length(), 4),
            round(math.degrees(2.0 * math.acos(min(1.0, dot))), 2),
            round((a.scale3d - b.scale3d).length(), 4)]


def compare(orig, new, bones, times):
    """{time: {bone: pose_diff}} of two sequences' local bone poses."""
    return {"%.2f" % t: {b: pose_diff(lib.get_bone_pose_for_time(orig, b, t, False),
                                      lib.get_bone_pose_for_time(new, b, t, False)) for b in bones}
            for t in times}


def worst(diffs):
    """The worst of compare()'s results, rotation counted at 2 degrees per cm and scale x100."""
    return max(max(v[0], v[1] / 2.0, v[2] * 100) for row in diffs.values() for v in row.values())


# --- Import and editing ------------------------------------------------------------------------------------
def use_legacy_fbx_import():
    """Python imports through FbxImportUI need the legacy importer, not Interchange."""
    cvar = "Interchange.FeatureFlags.Import.FBX"
    unreal.SystemLibrary.execute_console_command(None, cvar + " 0")
    if unreal.SystemLibrary.get_console_variable_bool_value(cvar):
        raise RuntimeError("Interchange FBX import still on; not importing")


def import_anim(fbx_path, dest, name, skeleton):
    """Imports an animation FBX onto a skeleton (asset or path), replacing an existing asset, and saves it.
    Re-importing over an asset the open editor has loaded isn't safe: close the editor first."""
    if isinstance(skeleton, str):
        skeleton = unreal.load_asset(skeleton)
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
    task.set_editor_property("filename", fbx_path)
    task.set_editor_property("destination_path", dest)
    task.set_editor_property("destination_name", name)
    task.set_editor_property("automated", True)
    task.set_editor_property("replace_existing", True)
    task.set_editor_property("save", True)
    task.set_editor_property("options", ui)
    unreal.AssetToolsHelpers.get_asset_tools().import_asset_tasks([task])
    return unreal.load_asset(dest + "/" + name)


def create_montage(seq, dest, name):
    """A montage made from a sequence (one Default section, DefaultSlot, 0.25 s blends), unless it exists.
    Montage sections can't be added from Python: copy a montage that has them instead (copy_montage)."""
    path = dest + "/" + name
    if eal.does_asset_exist(path):
        return unreal.load_asset(path), False
    factory = unreal.AnimMontageFactory()
    factory.set_editor_property("source_animation", seq)
    montage = unreal.AssetToolsHelpers.get_asset_tools().create_asset(name, dest, unreal.AnimMontage, factory)
    return montage, True


def copy_montage(source_path, path, seq):
    """A copy of a montage (sections, links, slots, blends) playing `seq` instead, unless it exists."""
    if not eal.does_asset_exist(path):
        eal.duplicate_asset(source_path, path)
    montage = unreal.load_asset(path)
    set_montage_anim(montage, seq)
    return montage


def set_montage_anim(montage, seq):
    """Points every segment of a montage at `seq`. The nested struct arrays come back as copies, so each
    level (segments, track, tracks) is rebuilt and set back; editing them in place is lost silently."""
    new_tracks = []
    for track in montage.get_editor_property("slot_anim_tracks"):
        at = track.get_editor_property("anim_track")
        new_segs = []
        for seg in at.get_editor_property("anim_segments"):
            seg.set_editor_property("anim_reference", seq)
            new_segs.append(seg)
        at.set_editor_property("anim_segments", new_segs)
        track.set_editor_property("anim_track", at)
        new_tracks.append(track)
    montage.set_editor_property("slot_anim_tracks", new_tracks)


def set_weapon_sounds(asset, events, track="1"):
    """Replaces every notify on an anim or montage with Weapon Sound notifies: [(time, unreal.WeaponSound.X)]."""
    lib.remove_all_animation_notify_tracks(asset)
    lib.add_animation_notify_track(asset, track)
    for time, sound in events:
        n = lib.add_animation_notify_event(asset, track, time, unreal.AnimNotify_WeaponSound)
        n.set_editor_property("sound", sound)


def set_curve(seq, name, keys):
    """A float curve with [(time, value)] keys (added if missing)."""
    if name not in [str(n) for n in lib.get_animation_curve_names(seq, unreal.RawCurveTrackTypes.RCT_FLOAT)]:
        lib.add_curve(seq, name, unreal.RawCurveTrackTypes.RCT_FLOAT, False)
    lib.add_float_curve_keys(seq, name, [k[0] for k in keys], [k[1] for k in keys])


def hold_bones(seq, keep):
    """Holds every bone track of a sequence at its first frame except those in `keep` (through the
    sequence's AnimSequencerController). Returns the bones held."""
    ctrl = None
    for get in (lambda: seq.get_editor_property("controller"), lambda: seq.controller, lambda: seq.get_controller()):
        try:
            ctrl = get()
            if ctrl:
                break
        except Exception:
            pass
    nkeys = lib.get_num_keys(seq)
    held = []
    for bone in [str(b) for b in lib.get_animation_track_names(seq)]:
        if bone in keep:
            continue
        p = lib.get_bone_pose_for_time(seq, bone, 0.0, False)
        ctrl.set_bone_track_keys(bone, [p.translation] * nkeys, [p.rotation] * nkeys, [p.scale3d] * nkeys)
        held.append(bone)
    return held


def save(asset):
    eal.save_loaded_asset(asset)


def run(tag, out_path, body):
    """Runs body(info), catching errors into info["errors"], then writes info as JSON and logs a summary line."""
    info = {"errors": []}
    try:
        body(info)
    except Exception:
        info["errors"].append(traceback.format_exc())
    write_json(out_path, info)
    log(tag, "done, errors %d" % len(info["errors"]))
    return info
