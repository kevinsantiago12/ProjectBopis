"""Blender: where the trigger finger's pad rests on each gun's trigger (spec *Trigger finger* -> *Tracking the
trigger*, step 3). Reads Saved/TriggerSockets/info.json and the FBX from sockets_export_ue.py, finds the blade
(the vertices skinned to the trigger bone), picks the point on its front face where a pad sits, and writes the
TriggerFinger socket offsets (in the trigger bone's space) to results.json, with a contact sheet of renders
(sheet.png: each gun from the side and from below-front, the point in red).

    .\\Tools\\AnimAuthoring\\RunBlender.ps1 .\\Tools\\AnimAuthoring\\TriggerFinger\\sockets_find_bl.py

Everything below is worked in Unreal's mesh space (cm); the FBX space is that with Y negated (animlib's S).
"""
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "lib"))
import animlib as A  # noqa: E402
import bpy  # noqa: E402
from mathutils import Quaternion, Vector  # noqa: E402

PROJECT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
DIR = os.path.join(PROJECT, "Saved", "TriggerSockets")
CLEARANCE = 0.6      # cm: the pad's centre this far in front of the blade's face (half a finger's thickness)
PREFER = 0.62        # how far down the trigger (0 top, 1 bottom) the pad likes to sit
BAND = 0.25          # cm: half-height of a slice through the blade
S3 = A.S.to_3x3()


def ue(v):
    return Vector((v[0], -v[1], v[2]))      # FBX <-> Unreal (Y negated); its own inverse


def find_contact(blade, pivot, forward, muzzle):
    """The pad's spot on a blade (Unreal mesh space). Below the barrel is 'down'; through the blade, the slice
    whose front (toward the muzzle) is furthest back in the lower half (45-85% down: a C-shaped trigger, the
    revolver's, curves back hardest near its top), i.e. the bottom of the curve, nearest
    PREFER of the way down; on the blade's centre line; CLEARANCE in front of its face."""
    to_pivot = pivot - muzzle
    down = (to_pivot - forward * to_pivot.dot(forward)).normalized()
    side = forward.cross(down).normalized()
    pts = [(p - pivot) for p in blade]
    hs = [p.dot(down) for p in pts]
    top, bottom = min(hs), max(hs)
    best = None
    for i in range(41):
        hc = top + (0.45 + 0.4 * i / 40.0) * (bottom - top)
        band = [p for p, h in zip(pts, hs) if abs(h - hc) < BAND]
        if len(band) < 3:
            continue
        front = max(p.dot(forward) for p in band)
        score = front + 0.3 * abs(hc - (top + PREFER * (bottom - top)))
        if best is None or score < best[0]:
            sides = sorted(p.dot(side) for p in band)
            best = (score, hc, front, sides[len(sides) // 2])
    if best is None:
        return None, None
    _, hc, front, sc = best
    contact = pivot + forward * (front + CLEARANCE) + down * hc + side * sc
    return contact, {"down": list(down), "side": list(side), "height": hc, "top": top, "bottom": bottom,
                     "front": front}


def gun_scene(entry):
    """Imports a gun; returns (node, objects, blade vertices in Unreal mesh space, the trigger bone's full
    matrix in FBX component space). The bone is the mesh's own reference pose, which the socket rides on; it
    can differ from the skeleton asset's (the Benelli's by 15 cm)."""
    A.clear_scene()
    objs = A.import_fbx(entry["fbx"])
    arm = next(o for o in objs if o.type == "ARMATURE")
    node = next((o for o in objs if o.type == "EMPTY"), None) or arm
    to_comp = node.matrix_world.inverted()
    bone = entry["trigger_bone"]
    blade = []
    for o in objs:
        if o.type != "MESH" or bone not in o.vertex_groups:
            continue
        group = o.vertex_groups[bone].index
        mw = to_comp @ o.matrix_world
        for v in o.data.vertices:
            if any(g.group == group and g.weight > 0.5 for g in v.groups):
                blade.append(ue(mw @ v.co))
    bone_matrix = None
    if bone in arm.data.bones:
        bone_matrix = to_comp @ arm.matrix_world @ arm.data.bones[bone].matrix_local
    return node, objs, blade, bone_matrix


def render_views(node, objs, contact, side, down, forward, size):
    cam = A.setup_render((480, 380))
    for o in objs:
        if o.type == "MESH":
            o.color = (0.62, 0.62, 0.66, 1.0)
    world = node.matrix_world
    mark_at = world @ ue(contact)
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.0035, location=mark_at)
    marker = bpy.context.active_object
    marker.color = (0.95, 0.1, 0.1, 1.0)
    to_world = lambda v: (world.to_3x3() @ (S3 @ v)).normalized()   # noqa: E731
    tiles = []
    for d in [to_world(side), (to_world(side) * 0.5 + to_world(down) * 0.6 + to_world(forward) * 0.6).normalized()]:
        A.look_at(cam, mark_at + d * size, mark_at)
        cam.data.lens = 50
        tiles.append(A.render_tile(os.path.join(DIR, "tile.png")))
    return tiles


def main():
    with open(os.path.join(DIR, "info.json")) as f:
        info = json.load(f)
    results, tiles = {}, []
    for path, entry in info["meshes"].items():
        if not entry.get("trigger_bone") or "muzzle" not in entry:
            print("TSOCK skip %s" % entry["name"])
            continue
        node, objs, blade, bone_matrix = gun_scene(entry)
        if bone_matrix is None:
            print("TSOCK %s: trigger bone not in the FBX" % entry["name"])
            continue
        pivot = ue(bone_matrix.translation)
        mq = entry["muzzle"]["quat"]
        forward = Quaternion((mq[3], mq[0], mq[1], mq[2])) @ Vector((1.0, 0.0, 0.0))
        muzzle = Vector(entry["muzzle"]["loc"])
        contact, frame = find_contact(blade, pivot, forward.normalized(), muzzle)
        if contact is None:
            print("TSOCK %s: no blade (%d verts)" % (entry["name"], len(blade)))
            continue
        # The socket's offset in the trigger bone's space, from the mesh's own bone (rotation and any scale,
        # the revolver's 100x included): into the bone's FBX frame, then Y negated back to Unreal's.
        rel = ue(bone_matrix.inverted() @ ue(contact))
        # For comparison: the same from the skeleton asset's reference pose.
        t = entry["trigger"]
        q = Quaternion((t["quat"][3], t["quat"][0], t["quat"][1], t["quat"][2]))
        rel_skel = q.conjugated() @ (contact - Vector(t["loc"]))
        rel_skel = Vector((rel_skel.x / t["scale"][0], rel_skel.y / t["scale"][1], rel_skel.z / t["scale"][2]))
        results[path] = {"name": entry["name"], "bone": entry["trigger_bone"], "contact": list(contact),
                         "relative": list(rel), "relative_from_skeleton": list(rel_skel), "frame": frame,
                         "blade_verts": len(blade), "pivot_mesh": list(pivot), "pivot_skeleton": t["loc"]}
        print("TSOCK %-20s blade %4d verts, trigger %.1f cm tall, pad %.1f down, contact (%.2f, %.2f, %.2f), "
              "rel (%.3f, %.3f, %.3f) [skeleton's (%.3f, %.3f, %.3f)], bone scale %.1f" % (
                  entry["name"], len(blade), frame["bottom"] - frame["top"], frame["height"] - frame["top"],
                  *contact, *rel, *rel_skel, bone_matrix.to_scale()[0]))
        size = 0.16 if (frame["bottom"] - frame["top"]) < 4.0 else 0.22
        tiles += render_views(node, objs, contact, Vector(frame["side"]), Vector(frame["down"]),
                              forward.normalized(), size)
    with open(os.path.join(DIR, "results.json"), "w") as f:
        json.dump(results, f, indent=1)
    if tiles:
        A.contact_sheet(tiles, os.path.join(DIR, "sheet.png"), per_row=4)
    print("TSOCK done, %d guns" % len(results))


main()
