"""Blender: the M4's and the AK's root frames and barrel axes, as imported (for converting the hand angle)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project as P  # noqa: E402
import animlib as A  # noqa: E402
import bpy  # noqa: E402

A.clear_scene()
for name in ("Gun.fbx", "AK.fbx"):
    objs = A.import_fbx(os.path.join(P.DIR, name))
    arm = next(o for o in objs if o.type == "ARMATURE")
    top = next((o for o in objs if o.type == "EMPTY"), None)
    mesh = next(o for o in objs if o.type == "MESH")
    bpy.context.view_layer.update()
    print("FILE", name, "top", top.name if top else None, "arm", arm.name, "bones", [b.name for b in arm.data.bones][:4])
    print("  arm world rot", [[round(v, 3) for v in r] for r in arm.matrix_world.to_3x3().normalized()])
    if top:
        print("  top world rot", [[round(v, 3) for v in r] for r in top.matrix_world.to_3x3().normalized()])
    if "b_gun_Root" in arm.data.bones:
        m = arm.matrix_world @ arm.data.bones["b_gun_Root"].matrix_local
        print("  root bone world rot", [[round(v, 3) for v in r] for r in m.to_3x3().normalized()])
    vs = [mesh.matrix_world @ v.co for v in mesh.data.vertices]
    for i, ax in enumerate("xyz"):
        print("  mesh world %s %.3f..%.3f" % (ax, min(v[i] for v in vs), max(v[i] for v in vs)))
    for o in objs:
        bpy.data.objects.remove(o, do_unlink=True)
