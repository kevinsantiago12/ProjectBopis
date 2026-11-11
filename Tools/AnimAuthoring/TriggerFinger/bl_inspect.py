"""Blender: prints the gun's bones and the right index finger in gun space at frame 0, and renders the hand."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project as P  # noqa: E402
import animlib as A  # noqa: E402
import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402

rig, gun = P.setup()
comp = gun.matrix(rig)            # gun component space -> rig space
to_gun = comp.inverted()

print("GUNBONES")
for b in gun.arm.data.bones:
    m = gun.rest(b.name)
    print("  %-22s head(gun) %s" % (b.name, tuple(round(v, 2) for v in m.translation)))

print("FINGER (gun space, cm)")
for name in ["hand_r", "index_metacarpal_r", "index_01_r", "index_02_r", "index_03_r", "middle_01_r", "thumb_03_r"]:
    pb = rig.pose.bones[name]
    head = to_gun @ pb.matrix.translation
    axes = [to_gun.to_3x3() @ pb.matrix.to_3x3().col[i] for i in range(3)]
    print("  %-20s head %s  x %s  y %s  z %s" % (name, tuple(round(v, 2) for v in head),
          tuple(round(v, 2) for v in axes[0].normalized()), tuple(round(v, 2) for v in axes[1].normalized()),
          tuple(round(v, 2) for v in axes[2].normalized())))

# The gun's mesh in gun space: bounds, and the lowest points behind the magazine (where a trigger hangs).
verts = []
for o in gun.meshes:
    mw = rig.matrix_world.inverted() @ o.matrix_world
    verts += [to_gun @ (mw @ v.co) for v in o.data.vertices]
xs, ys, zs = [v.x for v in verts], [v.y for v in verts], [v.z for v in verts]
print("GUNMESH bounds x %.1f..%.1f y %.1f..%.1f z %.1f..%.1f (%d verts)" % (min(xs), max(xs), min(ys), max(ys),
      min(zs), max(zs), len(verts)))

# Renders: the hand from the side and from below, the gun in place.
cam = A.setup_render((900, 700))
target = rig.matrix_world @ rig.pose.bones["index_02_r"].matrix.translation
os.makedirs(os.path.join(P.DIR, "renders"), exist_ok=True)
for tag, off in [("side_left", Vector((0.0, 0.0, 0.0))), ]:
    pass
side = rig.matrix_world.to_3x3() @ (comp.to_3x3() @ Vector((0.0, 1.0, 0.0)))   # gun's -Y in rig: one side
up = rig.matrix_world.to_3x3() @ (comp.to_3x3() @ Vector((0.0, 0.0, 1.0)))
fwd = rig.matrix_world.to_3x3() @ (comp.to_3x3() @ Vector((1.0, 0.0, 0.0)))
for tag, d in [("side_a", side), ("side_b", -side), ("below", -up), ("front", fwd)]:
    A.look_at(cam, target + d.normalized() * 0.35, target)
    cam.data.lens = 50
    A.render_tile(os.path.join(P.DIR, "renders", "inspect_%s.png" % tag))
print("RENDERED")
