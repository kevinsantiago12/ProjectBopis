"""Headless Unreal export for checking the trigger finger offline (check_solve_bl.py): how each gun Blueprint sits
in the right hand (grip offsets, the weapon mesh component's own transform), into Saved/TriggerSockets/grips.json.
The gun FBXs and trigger sockets come from sockets_export_ue.py / place.json. Read-only; fine with the editor open.

    .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\AnimAuthoring\\TriggerFinger\\check_export_ue.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import uelib as U  # noqa: E402
import unreal  # noqa: E402

BP_DIR = "/Game/ThirdPerson/Blueprints/"
GUNS = ["BP_AssaultRifle", "BP_AssaultCarbine", "BP_Pistol45", "BP_Pistol9mm", "BP_MachinePistol", "BP_AutoShotgun",
        "BP_Revolver", "BP_PumpShotgun", "BP_DualPistol45", "BP_DualPistol9mm", "BP_DualMachinePistol"]
PLAYER = "/Game/ThirdPerson/Blueprints/BP_PlayerCharacter.BP_PlayerCharacter_C"
OUT = os.path.normpath(os.path.join(unreal.Paths.project_saved_dir(), "TriggerSockets"))


def component(comp):
    return {"loc": U.vec(comp.get_editor_property("relative_location")),
            "rot": U.rot(comp.get_editor_property("relative_rotation")),
            "scale": U.vec(comp.get_editor_property("relative_scale3d")),
            "is_root": comp.get_attach_parent() is None}


def body(info):
    guns = info.setdefault("guns", {})
    for bp in GUNS:
        cdo = unreal.get_default_object(unreal.load_object(None, "%s%s.%s_C" % (BP_DIR, bp, bp)))
        d = U.blueprint_defaults("%s%s.%s_C" % (BP_DIR, bp, bp),
                                 ["grip_location_offset", "grip_rotation_offset", "grip_style",
                                  "offhand_grip_location_offset", "offhand_grip_rotation_offset"])
        comp = cdo.get_editor_property("weapon_mesh")
        d["mesh"] = U.path_of(comp.get_editor_property("skeletal_mesh_asset"))
        d["mesh_component"] = component(comp)
        U.attempt(d, "root", lambda: U.path_of(cdo.get_editor_property("root_component")))
        guns[bp] = d
        U.log("TCHECK", "%s: %s" % (bp, d))
    player = unreal.get_default_object(unreal.load_object(None, PLAYER))
    U.attempt(info, "player_components", lambda: [c.get_name() for c in player.get_components_by_class(unreal.ActorComponent)])
    for c in player.get_components_by_class(unreal.ActorComponent):
        for p in ["weapon_attach_socket_name", "offhand_attach_socket_name"]:
            try:
                info.setdefault("attach", {})[p] = str(c.get_editor_property(p))
            except Exception:
                pass
    mesh = player.get_editor_property("mesh").get_editor_property("skeletal_mesh_asset")
    info["body_mesh"] = U.path_of(mesh)
    info["body_sockets"] = [s for s in U.sockets(mesh) if s["bone"] in ("hand_r", "hand_l")]


U.run("TCHECK", os.path.join(OUT, "grips.json"), body)
