"""Blender: the trigger blade from the gun mesh, which way a +Z turn bends the index finger, and a clean side
view of the hand on the gun."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project as P  # noqa: E402
import animlib as A  # noqa: E402
import bpy  # noqa: E402
from mathutils import Quaternion, Vector  # noqa: E402

rig, gun = P.setup()
bpy.context.view_layer.update()
to_gun = gun.matrix(rig).inverted()
rig_inv = rig.matrix_world.inverted()


def group_points(obj, group, min_w=0.5, deformed=True):
    """The points of a vertex group (weight >= min_w) in gun space; deformed by the armature if asked."""
    gi = obj.vertex_groups[group].index
    ids = [v.index for v in obj.data.vertices if any(g.group == gi and g.weight >= min_w for g in v.groups)]
    if deformed:
        dg = bpy.context.evaluated_depsgraph_get()
        ev = obj.evaluated_get(dg)
        me = ev.to_mesh()
        pts = [to_gun @ (rig_inv @ (ev.matrix_world @ me.vertices[i].co)) for i in ids]
        ev.to_mesh_clear()
    else:
        pts = [to_gun @ (rig_inv @ (obj.matrix_world @ obj.data.vertices[i].co)) for i in ids]
    return pts


def bounds(pts):
    return tuple((round(min(p[i] for p in pts), 2), round(max(p[i] for p in pts), 2)) for i in range(3))


for o in gun.meshes:
    print("GUNMESH", o.name, "groups", [g.name for g in o.vertex_groups][:12])
    if "b_gun_trigger" in o.vertex_groups:
        blade = group_points(o, "b_gun_trigger", 0.5, deformed=False)
        print("BLADE", len(blade), "bounds xyz", bounds(blade))
        front = min(p.y for p in blade)
        for z0 in (2.0, 3.0, 4.0, 5.0, 6.0):
            row = [p for p in blade if abs(p.z - z0) < 0.5]
            if row:
                print("  z~%.0f: front y %.2f  back y %.2f  x %.2f..%.2f" % (z0, min(p.y for p in row),
                      max(p.y for p in row), min(p.x for p in row), max(p.x for p in row)))

body = next(o for o in bpy.data.objects if o.type == "MESH" and o.parent == rig)
pad = group_points(body, "index_03_r", 0.6)
print("PAD now: bounds", bounds(pad), "count", len(pad))

# Which way +10 degrees about each index bone's local Z moves the fingertip (gun space).
pb = rig.pose.bones["index_01_r"]
before = sum(pad, Vector()) / len(pad)
pb.rotation_mode = "QUATERNION"
pb.rotation_quaternion = pb.rotation_quaternion @ Quaternion(Vector((0, 0, 1)), 0.1745)
bpy.context.view_layer.update()
after_pts = group_points(body, "index_03_r", 0.6)
after = sum(after_pts, Vector()) / len(after_pts)
print("CURL +Z on index_01: tip moves", tuple(round(v, 2) for v in (after - before)))

# A side view from the finger's side, centred between the knuckle and the trigger.
cam = A.setup_render((900, 700))
comp = rig.matrix_world @ gun.matrix(rig)
centre = comp @ Vector((-1.0, -5.0, 4.0))
side = (comp.to_3x3() @ Vector((-1.0, 0.0, 0.0))).normalized()
up = (comp.to_3x3() @ Vector((0.0, 0.0, 1.0))).normalized()
cam.location = centre + side * 0.30
cam.rotation_euler = (-side).to_track_quat("-Z", "Y").to_euler()
cam.data.lens = 50
os.makedirs(os.path.join(P.DIR, "renders"), exist_ok=True)
A.render_tile(os.path.join(P.DIR, "renders", "probe_side.png"))
cam.location = centre + (side * 0.15 + up * 0.25)
cam.rotation_euler = (centre - cam.location).to_track_quat("-Z", "Y").to_euler()
A.render_tile(os.path.join(P.DIR, "renders", "probe_above.png"))
print("RENDERED")
