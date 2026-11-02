"""M4 reload: the rifle reload with its AK-style side pull replaced by a rear charging-handle pull.

Keeps MM_Rifle_Reload up to just after the new magazine seats, then drives the left arm (two-bone IK
on upperarm_l/lowerarm_l, hand_l set directly) along a path authored in the gun's space: up and over
the receiver, hook the T-handle, pull it back, let go, back to the handguard, where it rejoins the
original. The gun's b_gun_chargehandle travels with the hand.

Run: blender -b --factory-startup --python bl_author.py -- [render] [export]
"""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402

import bl_common as c  # noqa: E402

ARGS = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
FPS = 30.0

# --- Timing (seconds into the reload) ------------------------------------------------------------
T_LEAVE = 1.067   # leaves the original: just after the magazine seats (MagIn notify 0.98)
T_RETURN = 1.867  # rejoins the original on the handguard
T_GRAB = 1.37     # fingers on the T-handle
T_PULLED = 1.47   # handle fully back (Chamber notify here)
T_RELEASE = 1.51  # let go; the handle snaps forward
HANDLE_TRAVEL = 7.5  # cm the T-handle and hand travel back

# Gun space (cm, the AR4's component space as Blender sees it): +X the gun's left, -Y forward, +Z up.
# b_gun_chargehandle sits at (0, 1.37, 12.99).
HANDLE = Vector((0.0, 1.37, 12.99))

# Left hand (hand_l, the wrist) keyframes between the two ends taken from the original:
# (time, wrist position in gun space, orientation key: "grab" or a blend weight toward "grab")
PATH = [
    (1.20, Vector((13.0, 1.0, 7.0)), 0.45),
    (1.30, HANDLE + Vector((8.5, -4.0, 7.5)), 1.0),                    # over the top, in front of the handle
    (T_GRAB, HANDLE + Vector((7.0, -2.5, 5.0)), 1.0),                  # fingers hooked in front of the wings
    (T_PULLED, HANDLE + Vector((7.0, -2.5 + HANDLE_TRAVEL, 5.5)), 1.0),  # pulled straight back
    (T_RELEASE, HANDLE + Vector((8.0, -1.0 + HANDLE_TRAVEL, 8.0)), 1.0),  # off the handle, up a touch
    (1.68, Vector((16.0, -11.0, 7.0)), 0.35),
]

# Grab orientation in gun space: fingers across the top toward the gun's right and a little down,
# knuckle line (index -> pinky) running forward and down, so the palm faces back toward the shooter.
GRAB_FINGERS = Vector((-1.0, 0.1, -0.35)).normalized()
GRAB_KNUCKLES = Vector((0.0, -0.87, -0.5)).normalized()

ARM = ("upperarm_l", "lowerarm_l", "hand_l")


def frame_of(t):
    return int(round(t * FPS)) + bpy.context.scene.frame_start


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def basis(fingers, knuckles):
    x = fingers.normalized()
    y = (knuckles - x * knuckles.dot(x)).normalized()
    z = x.cross(y)
    m = Matrix((x, y, z)).transposed()
    return m.to_quaternion()


def hand_basis(rig):
    """Orientation (rig space) of the hand from its finger bases: wrist->middle, index->pinky."""
    p = rig.pose.bones
    wrist = p["hand_l"].matrix.translation
    return basis(p["middle_01_l"].matrix.translation - wrist,
                 p["pinky_01_l"].matrix.translation - p["index_01_l"].matrix.translation)


def catmull(points, t):
    """Catmull-Rom through (time, Vector) points, clamped ends."""
    times = [pt[0] for pt in points]
    if t <= times[0]:
        return points[0][1].copy()
    if t >= times[-1]:
        return points[-1][1].copy()
    i = max(k for k in range(len(times) - 1) if times[k] <= t)
    p0 = points[max(i - 1, 0)][1]
    p1 = points[i][1]
    p2 = points[i + 1][1]
    p3 = points[min(i + 2, len(points) - 1)][1]
    u = (t - times[i]) / (times[i + 1] - times[i])
    u2, u3 = u * u, u * u * u
    return 0.5 * ((2 * p1) + (-p0 + p2) * u + (2 * p0 - 5 * p1 + 4 * p2 - p3) * u2 + (-p0 + 3 * p1 - 3 * p2 + p3) * u3)


def rotate_about(matrix, pivot, rot):
    """Rotate an armature-space bone matrix by a rotation (Quaternion) about a pivot point."""
    return Matrix.Translation(pivot) @ rot.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ matrix


# The gun comes off the cheek for the pull: pushed forward and a little down, muzzle dipped and the top
# canted toward the left hand, pivoting on the right hand (gun space: forward is -Y, up +Z).
GUN_PUSH = Vector((0.0, -12.0, -4.0))
GUN_CANT = 25.0   # degrees, top toward the gun's left
GUN_DIP = 8.0     # degrees, muzzle down
GUN_OUT = (T_LEAVE + 0.03, 1.28)   # eases off the cheek
GUN_BACK = (1.55, T_RETURN)        # and back on

ARMS = ("upperarm_r", "lowerarm_r", "hand_r") + ARM


def gun_weight(t):
    if t < GUN_BACK[0]:
        return smooth((t - GUN_OUT[0]) / (GUN_OUT[1] - GUN_OUT[0]))
    return 1.0 - smooth((t - GUN_BACK[0]) / (GUN_BACK[1] - GUN_BACK[0]))


def gun_delta(g, w):
    """Rig-space move of the gun off the cheek, weighted, pivoting on the gun's origin (the grip)."""
    rot_gun = (Matrix.Rotation(math.radians(GUN_CANT * w), 3, "Y") @
               Matrix.Rotation(math.radians(GUN_DIP * w), 3, "X"))
    g3 = g.to_3x3()
    rot = (g3 @ rot_gun @ g3.inverted()).to_4x4()
    pivot = g.translation
    push = g3 @ (GUN_PUSH * w)
    return Matrix.Translation(pivot + push) @ rot @ Matrix.Translation(-pivot)


def solve_arm(pb, side, wrist, hand_q, pole_point, lengths):
    """Two-bone IK: swing upperarm/lowerarm so the wrist lands on `wrist` with the elbow toward
    `pole_point`, roll the forearm half the hand's twist, then set the hand's orientation."""
    upper, lower, hand = ("upperarm_" + side, "lowerarm_" + side, "hand_" + side)
    l1, l2 = lengths
    shoulder = pb[upper].matrix.translation.copy()
    to_wrist = wrist - shoulder
    d = min(to_wrist.length, l1 + l2 - 0.5)
    u = to_wrist.normalized()
    pole = pole_point - shoulder
    pole = (pole - u * pole.dot(u)).normalized()
    a = (l1 * l1 - l2 * l2 + d * d) / (2.0 * d)
    h = math.sqrt(max(l1 * l1 - a * a, 0.0))
    elbow = shoulder + u * a + pole * h
    wrist = shoulder + u * d

    old_elbow = pb[lower].matrix.translation.copy()
    swing = (old_elbow - shoulder).rotation_difference(elbow - shoulder)
    pb[upper].matrix = rotate_about(pb[upper].matrix.copy(), shoulder, swing)
    bpy.context.view_layer.update()

    old_wrist = pb[hand].matrix.translation.copy()
    swing = (old_wrist - elbow).rotation_difference(wrist - elbow)
    pb[lower].matrix = rotate_about(pb[lower].matrix.copy(), elbow, swing)
    bpy.context.view_layer.update()

    axis = (wrist - elbow).normalized()
    delta = hand_q @ pb[hand].matrix.to_quaternion().inverted()
    v = Vector((delta.x, delta.y, delta.z))
    proj = axis * v.dot(axis)
    twist = Quaternion((delta.w, proj.x, proj.y, proj.z))
    if twist.magnitude > 1e-6:
        twist.normalize()
        pb[lower].matrix = rotate_about(pb[lower].matrix.copy(), elbow, Quaternion().slerp(twist, 0.5))
        bpy.context.view_layer.update()

    m = hand_q.to_matrix().to_4x4()
    m.translation = pb[hand].matrix.translation
    pb[hand].matrix = m
    bpy.context.view_layer.update()
    return (pb[hand].matrix.translation - wrist).length


def main():
    rig, gun = c.setup()
    scene = bpy.context.scene
    pb = rig.pose.bones
    for name in ARMS:
        pb[name].rotation_mode = "QUATERNION"

    f_leave, f_return = frame_of(T_LEAVE), frame_of(T_RETURN)

    orig = {}
    for f in range(f_leave, f_return + 1):
        scene.frame_set(f)
        g = c.gun_matrix(rig)
        orig[f] = {
            "wrist_gun": g.inverted() @ pb["hand_l"].matrix.translation,
            "hand_rot_gun": g.to_quaternion().inverted() @ pb["hand_l"].matrix.to_quaternion(),
            "elbow_l": pb["lowerarm_l"].matrix.translation.copy(),
            "elbow_r": pb["lowerarm_r"].matrix.translation.copy(),
            "hand_from_basis": hand_basis(rig).inverted() @ pb["hand_l"].matrix.to_quaternion(),
        }
    lengths = {}
    for side in ("l", "r"):
        lengths[side] = ((pb["lowerarm_" + side].matrix.translation - pb["upperarm_" + side].matrix.translation).length,
                         (pb["hand_" + side].matrix.translation - pb["lowerarm_" + side].matrix.translation).length)
    print("ARM lengths", lengths)
    grab_rot_gun = basis(GRAB_FINGERS, GRAB_KNUCKLES) @ orig[f_leave]["hand_from_basis"]

    start_rot = orig[f_leave]["hand_rot_gun"]
    end_rot = orig[f_return]["hand_rot_gun"]
    points = [(T_LEAVE, orig[f_leave]["wrist_gun"])] + [(t, p) for t, p, _ in PATH] + \
             [(T_RETURN, orig[f_return]["wrist_gun"])]
    weights = [(T_LEAVE, 0.0)] + [(t, w) for t, _, w in PATH] + [(T_RETURN, 0.0)]

    def grab_weight(t):
        for (ta, wa), (tb, wb) in zip(weights, weights[1:]):
            if ta <= t <= tb:
                return wa + (wb - wa) * smooth((t - ta) / (tb - ta))
        return 0.0

    def hand_rot(t):
        u = smooth((t - T_LEAVE) / (T_RETURN - T_LEAVE))
        return start_rot.slerp(end_rot, u).slerp(grab_rot_gun, grab_weight(t))

    report = []
    for f in range(f_leave + 1, f_return):
        t = (f - scene.frame_start) / FPS
        scene.frame_set(f)

        # Right arm carries the gun off the cheek.
        g0 = c.gun_matrix(rig)
        delta = gun_delta(g0, gun_weight(t))
        target_r = delta @ pb["hand_r"].matrix
        miss_r = solve_arm(pb, "r", target_r.translation, target_r.to_quaternion(), delta @ orig[f]["elbow_r"],
                           lengths["r"])

        # Left hand follows its path on the moved gun; its elbow flares out to the left while reaching over.
        g = c.gun_matrix(rig)
        wrist = g @ catmull(points, t)
        hand_q = g.to_quaternion() @ hand_rot(t)
        reach = smooth(min((t - T_LEAVE) / 0.15, (T_RETURN - t) / 0.2, 1.0))
        pole_l = orig[f]["elbow_l"].lerp(wrist + Vector((34.0, 6.0, -12.0)), reach)
        miss_l = solve_arm(pb, "l", wrist, hand_q, pole_l, lengths["l"])

        for name in ARMS:
            pb[name].keyframe_insert("rotation_quaternion", frame=f, group=name)
        report.append((f, t, [round(x, 1) for x in (g.inverted() @ pb["hand_l"].matrix.translation)], miss_l, miss_r))

    for row in report:
        print("NEW F%02d t=%.3f wrist(gun) %s miss_l %.2f miss_r %.2f" % row)

    # The gun: the T-handle rides back with the hand, then snaps home on release.
    gun.animation_data_create()
    gun_act = bpy.data.actions.new("A_AR4_Reload")
    gun.animation_data.action = gun_act
    handle = gun.pose.bones["b_gun_chargehandle"]
    # Local -Z of the handle bone is the gun's rear.
    for t, back in ((0.0, 0.0), (T_GRAB, 0.0), (T_PULLED, HANDLE_TRAVEL), (T_RELEASE, HANDLE_TRAVEL),
                    (T_RELEASE + 0.05, 0.0), (2.2, 0.0)):
        handle.location = Vector((0.0, 0.0, -back))
        handle.keyframe_insert("location", frame=frame_of(t), group=handle.name)
    for fc in gun_act.fcurves:
        for kp in fc.keyframe_points:
            kp.interpolation = "LINEAR"

    blend_path = os.path.join(c.DIR, "m4_reload.blend")
    bpy.ops.wm.save_as_mainfile(filepath=blend_path)
    print("SAVED", blend_path)

    if "render" in ARGS:
        render(rig, gun)




def render(rig, gun):
    import numpy as np

    scene = bpy.context.scene
    cam = c.setup_render((640, 400))
    fwd, right, upv = Vector((0, -1, 0)), Vector((-1, 0, 0)), Vector((0, 0, 1))
    times = [1.067, 1.20, 1.30, 1.37, 1.47, 1.51, 1.68, 1.867]
    os.makedirs(os.path.join(c.DIR, "renders"), exist_ok=True)
    sheets = {}
    for view in ("game", "left", "close"):
        tiles = []
        for t in times:
            scene.frame_set(frame_of(t))
            c.place_gun(rig, gun)
            bpy.context.view_layer.update()
            to_world = rig.matrix_world @ c.gun_matrix(rig)
            handle = to_world @ HANDLE
            head = rig.matrix_world @ rig.pose.bones["head"].matrix.translation
            if view == "game":
                eye = head - fwd * 1.5 + right * 0.55 + upv * 0.2
                target = head + fwd * 0.8 + right * 0.15 - upv * 0.25
            elif view == "left":
                eye = handle - right * 0.9 + fwd * 0.35 + upv * 0.15
                target = handle + fwd * 0.12 - upv * 0.1
            else:
                eye = handle - right * 0.4 + fwd * 0.4 + upv * 0.22
                target = handle - upv * 0.03
            c.look_at(cam, eye, target)
            path = os.path.join(c.DIR, "renders", "tile.png")
            scene.render.filepath = path
            bpy.ops.render.render(write_still=True)
            img = bpy.data.images.load(path, check_existing=False)
            px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
            tiles.append(px)
            bpy.data.images.remove(img)
        rows = [np.concatenate(tiles[i:i + 4], axis=1) for i in range(0, len(tiles), 4)]
        sheet = np.concatenate(rows[::-1], axis=0)  # pixel rows run bottom-up
        h, w = sheet.shape[:2]
        out = bpy.data.images.new("sheet_" + view, w, h, alpha=True)
        out.pixels[:] = sheet.ravel()
        out.filepath_raw = os.path.join(c.DIR, "renders", "m4_%s.png" % view)
        out.file_format = "PNG"
        out.save()
        sheets[view] = out.filepath_raw
    print("SHEETS", sheets)


main()
