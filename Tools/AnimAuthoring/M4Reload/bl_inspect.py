"""Inspect the original rifle reload against the AR4: hand paths in gun space, plus renders."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

import bl_common as c  # noqa: E402

rig, gun = c.setup()
scene = bpy.context.scene
print("RIG matrix_world", [list(r) for r in rig.matrix_world])
print("GUN bones", [b.name for b in gun.data.bones])
print("frames", scene.frame_start, scene.frame_end, "fps", scene.render.fps)
for name in ("b_gun_Root", "b_gun_chargehandle", "b_gun_mag", "b_gun_muzzleflash", "b_gun_shelleject"):
    m = c.gun_bone_rest(gun, name)
    print("GUNBONE", name, "pos", [round(v, 2) for v in m.translation], "x", [round(v, 2) for v in m.col[0].xyz],
          "y", [round(v, 2) for v in m.col[1].xyz], "z", [round(v, 2) for v in m.col[2].xyz])

for f in range(scene.frame_start, scene.frame_end + 1, 2):
    scene.frame_set(f)
    hl = rig.pose.bones["hand_l"].matrix.translation
    hr = rig.pose.bones["hand_r"].matrix.translation
    g = c.to_gun(rig, hl)
    print("F%02d t=%.2f hand_l(gun) %s  hand_l(rig) %s  hand_r(rig) %s" % (
        f, (f - scene.frame_start) / 30.0, [round(v, 1) for v in g], [round(v, 1) for v in hl], [round(v, 1) for v in hr]))

cam = c.setup_render()
for f0, label in ((0, "start"), (11, "magout"), (30, "magin"), (40, "pullstart"), (44, "chamber"), (52, "after"), (65, "end")):
    f = f0 + scene.frame_start
    scene.frame_set(f)
    c.place_gun(rig, gun)
    bpy.context.view_layer.update()
    head = rig.matrix_world @ rig.pose.bones["head"].matrix.translation
    to_world = rig.matrix_world @ c.gun_matrix(rig)
    muzzle = to_world @ c.gun_bone_rest(gun, "b_gun_muzzleflash").translation
    grip = to_world @ c.gun_bone_rest(gun, "b_gun_Root").translation
    fwd = (muzzle - grip)
    fwd.z = 0
    fwd.normalize()
    up = Vector((0, 0, 1))
    right = fwd.cross(up).normalized()
    target = grip + (muzzle - grip) * 0.3
    for view, eye in (("shoulder", head - fwd * 1.6 + right * 0.45 + up * 0.15),
                      ("left", target - right * 1.1 + up * 0.15),
                      ("top", target + up * 1.0 - fwd * 0.2)):
        c.look_at(cam, eye, target)
        scene.render.filepath = os.path.join(c.DIR, "renders", "orig_%02d_%s_%s.png" % (f, label, view))
        bpy.ops.render.render(write_still=True)
print("DONE")
