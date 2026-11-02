"""Headless export for the M4 reload: FBX of the rifle reload, Manny, the CC body and the AR4,
plus a JSON dump of the montage, curves, sockets and the rifle's grip offsets."""
import json
import os
import traceback

import unreal

OUT = os.path.dirname(os.path.abspath(__file__))
info = {"errors": []}


def log(msg):
    unreal.log_warning("[M4EXPORT] " + str(msg))


def vec(v):
    return [v.x, v.y, v.z]


def rot(r):
    return {"roll": r.roll, "pitch": r.pitch, "yaw": r.yaw}


def fbx_options():
    o = unreal.FbxExportOption()
    o.ascii = False
    o.collision = False
    o.level_of_detail = False
    o.vertex_color = False
    o.map_skeletal_motion_to_root = False
    o.export_morph_targets = False
    try:
        o.export_preview_mesh = False
    except Exception as e:  # property name differs between versions
        info["errors"].append("export_preview_mesh: %s" % e)
    return o


def export(asset_path, filename, exporter):
    if os.path.exists(os.path.join(OUT, filename)):
        return
    try:
        obj = unreal.load_asset(asset_path)
        if not obj:
            info["errors"].append("missing " + asset_path)
            return
        task = unreal.AssetExportTask()
        task.object = obj
        task.filename = os.path.join(OUT, filename)
        task.automated = True
        task.prompt = False
        task.replace_identical = True
        task.exporter = exporter
        task.options = fbx_options()
        ok = unreal.Exporter.run_asset_export_task(task)
        info.setdefault("exports", {})[filename] = bool(ok)
        log("export %s -> %s" % (asset_path, ok))
    except Exception:
        info["errors"].append(traceback.format_exc())


def sockets(mesh_path):
    out = []
    try:
        mesh = unreal.load_asset(mesh_path)
        for i in range(mesh.num_sockets()):
            s = mesh.get_socket_by_index(i)
            out.append({
                "name": str(s.get_editor_property("socket_name")),
                "bone": str(s.get_editor_property("bone_name")),
                "loc": vec(s.get_editor_property("relative_location")),
                "rot": rot(s.get_editor_property("relative_rotation")),
                "scale": vec(s.get_editor_property("relative_scale")),
            })
    except Exception:
        info["errors"].append(traceback.format_exc())
    return out


def attempt(d, key, fn):
    try:
        d[key] = fn()
    except Exception as e:
        d[key] = "ERR %s" % e


def notify_list(asset):
    out = []
    for ev in unreal.AnimationLibrary.get_animation_notify_events(asset):
        n = ev.get_editor_property("notify")
        entry = {"class": n.get_class().get_name() if n else None}
        attempt(entry, "time", lambda: unreal.AnimationLibrary.get_anim_notify_event_trigger_time(ev))
        attempt(entry, "name", lambda: str(ev.get_editor_property("notify_name")))
        if n:
            attempt(entry, "sound", lambda: str(n.get_editor_property("sound")))
        out.append(entry)
    return out


actions = "/Game/Characters/Heroes/Mannequin/Animations/Actions/"
anim = unreal.load_asset(actions + "MM_Rifle_Reload")
a = {}
attempt(a, "play_length", anim.get_play_length)
attempt(a, "frames", lambda: unreal.AnimationLibrary.get_num_frames(anim))


def read_curves():
    curves = {}
    for name in unreal.AnimationLibrary.get_animation_curve_names(anim, unreal.RawCurveTrackTypes.RCT_FLOAT):
        times, values = unreal.AnimationLibrary.get_float_keys(anim, name)
        curves[str(name)] = [[round(t, 4), round(v, 4)] for t, v in zip(times, values)]
    return curves


attempt(a, "curves", read_curves)
attempt(a, "notifies", lambda: notify_list(anim))
info["MM_Rifle_Reload"] = a

montage = unreal.load_asset(actions + "AM_Rifle_Reload")
m = {}
attempt(m, "play_length", montage.get_play_length)
attempt(m, "blend_in", lambda: montage.get_editor_property("blend_in").get_editor_property("blend_time"))
attempt(m, "blend_out", lambda: montage.get_editor_property("blend_out").get_editor_property("blend_time"))
attempt(m, "blend_out_trigger", lambda: montage.get_editor_property("blend_out_trigger_time"))
attempt(m, "rate_scale", lambda: montage.get_editor_property("rate_scale"))
attempt(m, "sections", lambda: [str(montage.get_section_name(i)) for i in range(montage.get_num_sections())])


def read_slots():
    slots = []
    for track in montage.get_editor_property("slot_anim_tracks"):
        segs = []
        for seg in track.get_editor_property("anim_track").get_editor_property("anim_segments"):
            ref = seg.get_editor_property("anim_reference")
            segs.append({"anim": ref.get_path_name() if ref else None,
                         "start_pos": seg.get_editor_property("start_pos"),
                         "anim_start": seg.get_editor_property("anim_start_time"),
                         "anim_end": seg.get_editor_property("anim_end_time"),
                         "rate": seg.get_editor_property("anim_play_rate")})
        slots.append({"slot": str(track.get_editor_property("slot_name")), "segments": segs})
    return slots


attempt(m, "slots", read_slots)
attempt(m, "notifies", lambda: notify_list(montage))
info["AM_Rifle_Reload"] = m

with open(os.path.join(OUT, "ue_info2.json"), "w") as f:
    json.dump(info, f, indent=1, default=str)
log("done")
