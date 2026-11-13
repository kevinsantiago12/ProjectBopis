"""Headless Unreal export for the TriggerFinger sockets (spec *Trigger finger* -> *Tracking the trigger*, step 3):
every gun Blueprint's mesh as FBX, with its trigger bone and muzzle socket in the mesh's own space, into
Saved/TriggerSockets/ (info.json + <mesh>.fbx). sockets_find_bl.py reads them. Read-only; fine with the editor
open. Skeletal meshes need rendering:

    .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\AnimAuthoring\\TriggerFinger\\sockets_export_ue.py -Render
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import uelib as U  # noqa: E402
import unreal  # noqa: E402

BP_DIR = "/Game/ThirdPerson/Blueprints/"
GUNS = ["BP_AssaultRifle", "BP_AssaultCarbine", "BP_Pistol45", "BP_Pistol9mm", "BP_MachinePistol", "BP_AutoShotgun",
        "BP_Revolver", "BP_PumpShotgun", "BP_DualPistol45", "BP_DualPistol9mm", "BP_DualMachinePistol"]
TRIGGER_BONES = ["b_gun_trigger", "trigger", "Trigger"]
OUT = os.path.normpath(os.path.join(unreal.Paths.project_saved_dir(), "TriggerSockets"))
APE = unreal.AnimPoseExtensions


def transform(t):
    q = t.rotation
    return {"loc": U.vec(t.translation), "quat": [q.x, q.y, q.z, q.w], "scale": U.vec(t.scale3d)}


def body(info):
    os.makedirs(OUT, exist_ok=True)
    meshes = info.setdefault("meshes", {})
    for bp in GUNS:
        cls = unreal.load_object(None, "%s%s.%s_C" % (BP_DIR, bp, bp))
        cdo = unreal.get_default_object(cls)
        comp = cdo.get_editor_property("weapon_mesh")
        mesh = comp.get_editor_property("skeletal_mesh_asset")
        if not mesh:
            info["errors"].append("%s: no mesh" % bp)
            continue
        path = U.path_of(mesh)
        entry = meshes.setdefault(path, {"guns": [], "name": mesh.get_name()})
        entry["guns"].append({"bp": bp, "scale": U.vec(comp.get_editor_property("relative_scale3d")),
                              "muzzle_socket": str(cdo.get_editor_property("muzzle_socket_name"))})
        if "trigger_bone" in entry:
            continue

        pose = APE.get_reference_pose(mesh.get_editor_property("skeleton"))
        bones = [str(n) for n in APE.get_bone_names(pose)]
        trigger = next((b for b in TRIGGER_BONES if b in bones), None)
        entry["bones"] = bones
        entry["trigger_bone"] = trigger
        if trigger:
            entry["trigger"] = transform(APE.get_bone_pose(pose, trigger, unreal.AnimPoseSpaces.WORLD))
        entry["sockets"] = U.sockets(mesh)
        # The muzzle socket in mesh space (its X runs down the barrel): its bone's pose x its own offset.
        name = entry["guns"][0]["muzzle_socket"]
        sock = next((s for s in entry["sockets"] if s["name"] == name), None)
        if sock:
            socket = mesh.find_socket(name)
            rel = unreal.Transform(socket.get_editor_property("relative_location"),
                                   socket.get_editor_property("relative_rotation"),
                                   socket.get_editor_property("relative_scale"))
            bone = APE.get_bone_pose(pose, sock["bone"], unreal.AnimPoseSpaces.WORLD)
            entry["muzzle"] = transform(unreal.MathLibrary.compose_transforms(rel, bone))
        entry["fbx"] = os.path.join(OUT, mesh.get_name() + ".fbx")
        U.export_asset(mesh, entry["fbx"], info)
        U.log("TSOCK", "%s: trigger %s, muzzle %s" % (path, trigger, "yes" if sock else "MISSING"))


U.run("TSOCK", os.path.join(OUT, "info.json"), body)
