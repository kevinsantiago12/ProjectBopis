"""Headless Unreal export for the trigger-finger poses: the idle clip, Manny, the M4's mesh, and the rifle's
grip offsets and mesh sockets (ue_info.json). Run with RunUnreal.ps1 -Render (skeletal meshes)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project as P  # noqa: E402  (puts ../lib on the path)
import uelib as U  # noqa: E402
import unreal  # noqa: E402


def body(info):
    U.export_asset(P.CLIP_PATH, os.path.join(P.DIR, P.CLIP_FBX), info)
    U.export_asset(U.MANNY, os.path.join(P.DIR, "SKM_Manny_Simple.fbx"), info)
    weapon = U.blueprint_defaults(P.WEAPON_BP, ["grip_location_offset", "grip_rotation_offset", "grip_style"])
    cdo = unreal.get_default_object(unreal.load_object(None, P.WEAPON_BP))
    comp = cdo.get_editor_property("weapon_mesh")
    mesh = comp.get_editor_property("skeletal_mesh_asset")
    weapon["mesh"] = U.path_of(mesh)
    weapon["scale"] = U.vec(comp.get_editor_property("relative_scale3d"))   # the mesh is drawn this much bigger
    info["weapon"] = weapon
    info["gun_sockets"] = U.sockets(mesh)
    U.export_asset(mesh, os.path.join(P.DIR, P.GUN_FBX), info)


U.run("TRIGGER", os.path.join(P.DIR, "export_result.json"), body)
