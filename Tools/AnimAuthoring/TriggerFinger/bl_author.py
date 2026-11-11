"""Blender: solves the right index finger onto the trigger (Rest) and pulling it (Press), renders both, and
writes each as a one-frame FBX of the whole pose (MM_Rifle_Idle_Hipfire's frame 0 with the finger changed).

The finger curls about each joint's local +Z (flexion; Unreal's yaw), and the knuckle also tilts about its
local Y to drop the finger into the trigger guard (toward the middle finger). The last joint follows the middle
one (DIP = 0.65 x PIP, as a real finger does). The pad is the centroid of the skin weighted to index_03_r,
taken as a fixed offset from that bone, and is placed half a finger's thickness in front of the blade's curve.

The clip's action is taken off the rig once frame 0 is posed, so renders and the bake see the bent finger
(an action on the rig re-poses it whenever the scene is evaluated)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project as P  # noqa: E402
import animlib as A  # noqa: E402
import bpy  # noqa: E402
from mathutils import Quaternion, Vector  # noqa: E402

RENDER = "render" in sys.argv
BONES = ["index_01_r", "index_02_r", "index_03_r"]
X, Y, Z = Vector((1.0, 0.0, 0.0)), Vector((0.0, 1.0, 0.0)), Vector((0.0, 0.0, 1.0))
DIP_SHARE = 0.15            # L, not C: the last segment stays nearly straight, the pad flat on the trigger
# Gun space (cm). The blade (|x| < 0.3) is curved; its front is deepest (y -6.31) at z ~4. The tip reaches
# into the trigger (user, 2026-11-11: "i need the tip further into the trigger"): the pad's centre sits 0.6 cm
# past the blade's line and just at its front, so the blade lies under the end of the finger. First version:
# (0, -7.0, 4.0) / (0, -6.55, 3.95), the pad 0.7 cm in front of the blade on its line.
TARGETS = {
    "TriggerRestPose": Vector((0.6, -6.5, 3.9)),
    "TriggerPressPose": Vector((0.6, -6.05, 3.85)),      # 0.45 cm further back: the trigger's travel
}

rig, gun = P.setup()
bpy.context.view_layer.update()
rig.animation_data.action = None          # frame 0 stays as posed; nothing re-poses it from here
comp_to_rig = gun.matrix(rig)
to_gun = comp_to_rig.inverted()
rig_inv = rig.matrix_world.inverted()
pbs = {b: rig.pose.bones[b] for b in BONES}
for pb in rig.pose.bones:
    if pb.rotation_mode != "QUATERNION":
        q = pb.rotation_euler.to_quaternion()
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = q
base = {b: pbs[b].rotation_quaternion.copy() for b in BONES}

# The pad: skin weighted to index_03_r, as an offset from the bone.
body = next(o for o in bpy.data.objects if o.type == "MESH" and o.parent == rig)
gi = body.vertex_groups["index_03_r"].index
ids = [v.index for v in body.data.vertices if any(g.group == gi and g.weight >= 0.6 for g in v.groups)]
dg = bpy.context.evaluated_depsgraph_get()
ev = body.evaluated_get(dg)
me = ev.to_mesh()
pad_rig = sum((rig_inv @ (ev.matrix_world @ me.vertices[i].co) for i in ids), Vector()) / len(ids)
ev.to_mesh_clear()
pad_local = pbs["index_03_r"].matrix.inverted() @ pad_rig


def pose(a1, t1, a2):
    """Bends the finger (degrees): the knuckle curls a1 and tilts t1, the middle joint curls a2, the last
    0.65 a2. Returns the pad's centre in gun space."""
    pbs["index_01_r"].rotation_quaternion = (base["index_01_r"] @ Quaternion(Z, math.radians(a1))
                                             @ Quaternion(Y, math.radians(t1)))
    pbs["index_02_r"].rotation_quaternion = base["index_02_r"] @ Quaternion(Z, math.radians(a2))
    pbs["index_03_r"].rotation_quaternion = base["index_03_r"] @ Quaternion(Z, math.radians(a2 * DIP_SHARE))
    bpy.context.view_layer.update()
    return to_gun @ (pbs["index_03_r"].matrix @ pad_local)


def solve(target):
    def search(r1, rt, r2):
        best = None
        for a1 in r1:
            for t1 in rt:
                for a2 in r2:
                    p = pose(a1, t1, a2)
                    # Miss, plus a small cost on bending, so the least bend that reaches it wins.
                    err = (p - target).length + 0.002 * (abs(a1) + abs(t1) + abs(a2))
                    if best is None or err < best[0]:
                        best = (err, a1, t1, a2, p)
        return best

    rng = lambda lo, hi, step: [lo + i * step for i in range(int(round((hi - lo) / step)) + 1)]  # noqa: E731
    best = search(rng(-10, 50, 4), rng(-24, 24, 4), rng(0, 90, 4))
    _, a1, t1, a2, _ = best
    best = search(rng(a1 - 4, a1 + 4, 0.5), rng(t1 - 4, t1 + 4, 0.5), rng(a2 - 4, a2 + 4, 0.5))
    return best


print("PAD in the clip (gun cm)", tuple(round(v, 2) for v in pose(0, 0, 0)))
results = {}
for name, target in TARGETS.items():
    err, a1, t1, a2, p = solve(target)
    results[name] = (a1, t1, a2)
    print("SOLVED %s: knuckle curl %.1f tilt %.1f, middle %.1f, last %.1f deg; pad %s, miss %.2f cm"
          % (name, a1, t1, a2, a2 * DIP_SHARE, tuple(round(v, 2) for v in p), (p - target).length))


def render(name):
    scene = bpy.context.scene
    cam = scene.camera or A.setup_render((900, 700))
    comp = rig.matrix_world @ comp_to_rig
    centre = comp @ Vector((-1.0, -5.5, 3.5))
    side = (comp.to_3x3() @ Vector((-1.0, 0.0, 0.0))).normalized()
    up = (comp.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
    gun.node.matrix_world = comp @ gun.node_offset
    cam.data.lens = 50
    for tag, d in [("side", side * 0.30), ("below", side * 0.10 - up * 0.28), ("front", side * 0.1 + (comp.to_3x3() @ Vector((0, -1, 0))).normalized() * 0.28)]:
        cam.location = centre + d
        cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
        A.render_tile(os.path.join(P.DIR, "renders", "%s_%s.png" % (name, tag)))


os.makedirs(os.path.join(P.DIR, "renders"), exist_ok=True)
if RENDER:
    pose(0, 0, 0)
    render("Clip")
    for name, (a1, t1, a2) in results.items():
        pose(a1, t1, a2)
        render(name)

# Bake each pose as a one-frame action and export it. The gun is left out (only the rig is selected).
for name, (a1, t1, a2) in results.items():
    pose(a1, t1, a2)
    act = bpy.data.actions.new(name)
    rig.animation_data.action = act
    # Keyed on frames 1 and 2: Unreal's importer needs a time range, and a "one-frame" clip spans 1/30 s.
    for pb in rig.pose.bones:
        for path in ("location", "rotation_quaternion", "scale"):
            pb.keyframe_insert(path, frame=1)
            pb.keyframe_insert(path, frame=2)
    A.export_armature(rig, "root", os.path.join(P.DIR, name + ".fbx"), frame_end=2)
    rig.animation_data.action = None
print("DONE")
