"""Blender: checks the Trigger Finger node offline on every gun (spec *Trigger finger* -> *Tracking the trigger*).
The right hand in the Rest pose (MM_Rifle_Idle_Hipfire frame 0 with TriggerRestPose's index finger, what the node
receives), each gun Blueprint placed on HandGrip_R by its grip offsets and mesh scale (grips.json from
check_export_ue.py), its TriggerFinger socket (place.json), then the node's maths, copied from
AnimNode_TriggerFinger.cpp. Writes Saved/TriggerSockets/check/results.json and sheet.png: per gun, the finger as it
comes in, solved from the side, and solved from behind. Red: the socket. Blue: the node's pad point.

    blender -b -P Tools/AnimAuthoring/TriggerFinger/check_solve_bl.py [-- BoneAxis=1 WrapCurl=50 norender BP_Pistol45 ...]

Options after "--": BoneAxis=1 curls about the middle joint's own -Z (Manny's flexion axis, both hands) instead of
the node's original axis (the incoming bend, else the plane through the target); WrapCurl=<deg> caps the curl and
lets a closer trigger rest further back along the finger (sheet_bone_wrap50.png); any node parameter by name
(PadLength=...); norender for numbers only; Blueprint names to check only those. Prints TFRAME (the trigger in the
incoming finger's frame) and TCHECK (reach, curl, swing, miss) per gun.
"""
import json
import math
import os
import sys

DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(DIR, "..", "lib"))
import animlib as A  # noqa: E402
import bpy  # noqa: E402
from mathutils import Matrix, Quaternion, Vector  # noqa: E402

PROJECT = os.path.normpath(os.path.join(DIR, "..", "..", ".."))
SOCK = os.path.join(PROJECT, "Saved", "TriggerSockets")
OUT = os.path.join(SOCK, "check")
S3 = A.S.to_3x3()
CHAIN = ["index_01_r", "index_02_r", "index_03_r"]
ONLY = [a for a in sys.argv[sys.argv.index("--") + 1:]] if "--" in sys.argv else []

# The node's defaults (AnimNode_TriggerFinger.h); override with KEY=value after "--".
# Defaults = the node as built 2026-11-12 20:18 (the trigger on the 2nd bone), with ABP_Player's Contact Along 0.75. The first version's maths:
# BoneAxis=0 Second=0 MaxCurl=110 (pad reach, curl axis from the incoming bend); WrapCurl was the 50-degree wrap
# tried before it. LastJointShare only applies to those older modes.
PARAMS = {"PadLength": 2.0, "LastJointShare": 0.15, "MaxCurl": 120.0, "MaxSwing": 40.0,
          "BoneAxis": 1.0, "WrapCurl": 0.0, "Second": 0.75, "TipWrap": 40.0}
RENDER = True
for a in ONLY[:]:
    if a == "norender":
        RENDER = False
        ONLY.remove(a)
        continue
    if "=" in a:
        k, v = a.split("=")
        PARAMS[k] = float(v)
        ONLY.remove(a)


def ue(v):
    return Vector((v[0], -v[1], v[2]))


def angle_about(a, b, axis):
    return math.atan2(a.cross(b).dot(axis), a.dot(b))


def solve(p1, p2, p3, last_x, goal, flex=None):
    """AnimNode_TriggerFinger::EvaluateSkeletalControl_AnyThread, in Unreal space. Returns the turns and a report."""
    pad_len, share = PARAMS["PadLength"], PARAMS["LastJointShare"]
    last_axis = last_x if last_x.dot(p3 - p2) >= 0.0 else -last_x
    d1, d2, d3 = p2 - p1, p3 - p2, last_axis * pad_len
    l1, l2 = d1.length, d2.length
    axis = d1.cross(d2)
    if axis.length_squared < (0.05 * l1 * l2) ** 2:
        axis = d1.cross(goal - p1)
    if flex is not None:
        axis = flex.copy()
    axis.normalize()

    def reach(t):
        lt = t * (1.0 + share)
        return math.hypot(l1 + l2 * math.cos(t) + pad_len * math.cos(lt), l2 * math.sin(t) + pad_len * math.sin(lt))

    wanted = (goal - p1).length
    lo, hi = 0.0, math.radians(PARAMS["MaxCurl"])
    state = "ok"
    if wanted >= reach(lo):
        hi, state = lo, "straight (target out of reach)"
    elif wanted <= reach(hi):
        lo, state = hi, "FULL CURL (target too close)"
    for _ in range(24):
        if hi - lo <= 1.0e-4:
            break
        mid = 0.5 * (lo + hi)
        if reach(mid) > wanted:
            lo = mid
        else:
            hi = mid
    theta = 0.5 * (lo + hi)
    # Wrap: past WrapCurl the pad would hook; instead the finger keeps that curl and the trigger rests further
    # back along it (the point on the finger as far from the knuckle as the trigger), the rest wrapping round.
    wrap = PARAMS["WrapCurl"] > 0.0 and theta > math.radians(PARAMS["WrapCurl"])
    if wrap:
        theta = math.radians(PARAMS["WrapCurl"])
        state = "wrap"
    last_angle = share * theta
    fixed = None
    # Second: the trigger on the middle segment (index_02), Second of the way along it, the tip wrapping round
    # it by TipWrap at the last joint. The middle joint curls until that point is as far from the knuckle as the
    # trigger. A trigger further than it reaches straight slides the contact out along the finger.
    if PARAMS.get("Second", 0.0) > 0.0:
        u, tip = PARAMS["Second"], math.radians(PARAMS.get("TipWrap", 40.0))

        def contact_at(t):
            return p2 + Quaternion(axis, t - angle_about(d1, d2, axis)) @ (d2 * u)

        if wanted < (contact_at(0.0) - p1).length:
            lo, hi = 0.0, math.radians(150.0)
            for _ in range(30):
                mid = 0.5 * (lo + hi)
                if (contact_at(mid) - p1).length > wanted:
                    lo = mid
                else:
                    hi = mid
            theta, last_angle, state = 0.5 * (lo + hi), tip, "second"
            fixed = "middle %.0f%%" % (u * 100)
        else:
            theta, wrap, state = 0.0, True, "second, slid out"
            last_angle = tip if wanted <= (p2 + Quaternion(axis, -angle_about(d1, d2, axis)) @ d2 - p1).length else 0.0
    mid_turn = Quaternion(axis, theta - angle_about(d1, d2, axis))
    last_turn = Quaternion(axis, last_angle - angle_about(d2, d3, axis))
    new_d2 = mid_turn @ d2
    new_p3 = p2 + new_d2
    new_pad = new_p3 + (last_turn @ mid_turn) @ d3
    contact, where = new_pad, "pad"
    if fixed:
        contact, where = p2 + new_d2 * PARAMS["Second"], fixed
    elif wrap:
        chain = [(p1, p2, "proximal"), (p2, new_p3, "middle"), (new_p3, new_pad, "last")]
        for qa, qb, name in chain:
            a, d = qa - p1, qb - qa
            if a.length <= wanted <= (qb - p1).length:
                ad, dd = a.dot(d), d.dot(d)
                t = (-ad + math.sqrt(max(ad * ad - dd * (a.dot(a) - wanted * wanted), 0.0))) / dd
                contact, where = qa + d * t, "%s %.0f%%" % (name, t * 100)
                break
    swing = (contact - p1).rotation_difference(goal - p1)
    s_axis, s_angle = swing.to_axis_angle()
    capped = s_angle > math.radians(PARAMS["MaxSwing"])
    if capped:
        swing = Quaternion(s_axis, math.radians(PARAMS["MaxSwing"]))
    pad = p1 + swing @ (contact - p1)
    report = {"wanted": wanted, "reach_straight": reach(0.0), "reach_full_curl": reach(math.radians(PARAMS["MaxCurl"])),
              "state": state, "curl_in": math.degrees(angle_about(d1, d2, axis)), "curl_out": math.degrees(theta),
              "swing": math.degrees(s_angle), "swing_capped": capped, "pad_miss": (pad - goal).length,
              "l1": l1, "l2": l2, "contact": where}
    rots = {"index_01_r": swing, "index_02_r": swing @ mid_turn, "index_03_r": swing @ last_turn @ mid_turn}
    locs = {"index_01_r": p1, "index_02_r": p1 + swing @ d1, "index_03_r": p1 + swing @ (new_p3 - p1)}
    return rots, locs, pad, report


def set_world(pb, rot_ue, loc_ue):
    """Turns a pose bone by an Unreal-space rotation (about the rig's origin) and moves it to an Unreal-space
    location, in the rig's armature space (FBX space: Unreal with Y negated)."""
    r = (S3 @ rot_ue.to_matrix() @ S3) @ pb.matrix.to_3x3()
    pb.matrix = Matrix.Translation(ue(loc_ue)) @ r.to_4x4()
    bpy.context.view_layer.update()


def rest_finger():
    """TriggerRestPose's index chain, each bone's rotation relative to its parent."""
    rig = A.setup_character(DIR, "TriggerRestPose.fbx")
    bpy.context.scene.frame_set(bpy.context.scene.frame_start)
    bpy.context.view_layer.update()
    out = {}
    for b in CHAIN:
        pb = rig.pose.bones[b]
        out[b] = (pb.parent.matrix.inverted() @ pb.matrix).to_quaternion()
    return out


def marker(at, colour, radius=0.0025):
    bpy.ops.mesh.primitive_uv_sphere_add(radius=radius, location=at)
    m = bpy.context.active_object
    m.color = colour
    return m


def label(cam, text):
    curve = bpy.data.curves.new("Label", type="FONT")
    curve.body = text
    curve.size = 0.0032
    obj = bpy.data.objects.new("Label", curve)
    bpy.context.scene.collection.objects.link(obj)
    obj.parent = cam
    obj.location = (-0.0345, 0.0255, -0.1)
    obj.color = (0.0, 0.0, 0.0, 1.0)
    return obj


def main():
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(SOCK, "grips.json")) as f:
        grips = json.load(f)["guns"]
    with open(os.path.join(SOCK, "info.json")) as f:
        info = json.load(f)["meshes"]
    with open(os.path.join(SOCK, "place.json")) as f:
        place = {p: (bone, rel) for p, bone, rel in json.load(f)}
    rest = rest_finger()

    results, tiles = {}, []
    for bp, g in grips.items():
        if ONLY and bp not in ONLY:
            continue
        mesh = g["mesh"]
        entry = info[mesh]
        bone, rel = place[mesh.split(".")[0]]
        rig = A.setup_character(DIR, "MM_Rifle_Idle_Hipfire.fbx")
        r = g["grip_rotation_offset"]
        scale = Matrix.Diagonal(tuple(g["mesh_component"]["scale"]) + (1.0,))
        gun = A.Gun(rig, entry["fbx"], A.ue_xform(g["grip_location_offset"], pitch=r["pitch"], yaw=r["yaw"],
                                                  roll=r["roll"]) @ scale)
        scene = bpy.context.scene
        scene.frame_set(scene.frame_start)
        bpy.context.view_layer.update()
        rig.animation_data.action = None
        # The Rest pose's finger, as LayeredBoneBlend_18 lays it on.
        for b in CHAIN:
            pb = rig.pose.bones[b]
            local = pb.parent.matrix.inverted() @ pb.matrix
            pb.matrix = pb.parent.matrix @ Matrix.Translation(local.translation) @ rest[b].to_matrix().to_4x4()
            bpy.context.view_layer.update()
        gun.place(rig)
        bpy.context.view_layer.update()

        rig_inv = rig.matrix_world.inverted()
        arm = gun.arm
        goal_fbx = rig_inv @ (arm.matrix_world @ arm.data.bones[bone].matrix_local @ ue(rel))
        goal = ue(goal_fbx)
        pbs = {b: rig.pose.bones[b] for b in CHAIN}
        p1, p2, p3 = (ue(pbs[b].matrix.translation) for b in CHAIN)
        last_x = ue(pbs["index_03_r"].matrix.col[0].to_3d())
        flex = -ue(pbs["index_02_r"].matrix.col[2].to_3d()) if PARAMS["BoneAxis"] else None

        # Views: from the knuckle's side of the gun, square to the barrel, and from behind the hand.
        mq = entry["muzzle"]["quat"]
        node_w = gun.node.matrix_world
        fwd = (node_w.to_3x3() @ ue(Quaternion((mq[3], mq[0], mq[1], mq[2])) @ Vector((1, 0, 0)))).normalized()
        goal_w = rig.matrix_world @ goal_fbx
        p1_w = rig.matrix_world @ ue(p1)
        centre = (goal_w + p1_w) * 0.5
        side = (p1_w - goal_w)
        side = (side - fwd * side.dot(fwd))
        up = fwd.cross(side).normalized()
        side = up.cross(fwd).normalized()
        if side.dot(p1_w - (node_w @ Vector())) < 0:
            side = -side
        cam = A.setup_render((380, 300))
        cam.data.lens = 50
        for o in bpy.data.objects:
            if o.type == "MESH":
                o.color = (0.86, 0.68, 0.55, 1.0) if o.parent == rig else (0.45, 0.45, 0.5, 1.0)
        red = marker(goal_w, (0.95, 0.05, 0.05, 1.0))

        def shot(text, eye):
            A.look_at(cam, eye, centre)
            lab = label(cam, text)
            if RENDER:
                tiles.append(A.render_tile(os.path.join(OUT, "tile.png")))
            bpy.data.objects.remove(lab, do_unlink=True)

        short = bp.replace("BP_", "")
        shot(short + ": coming in", centre + side * 0.22 + up * 0.03)
        rots, locs, pad, rep = solve(p1, p2, p3, last_x, goal, flex)
        for b in CHAIN:
            set_world(pbs[b], rots[b], locs[b])
        blue = marker(rig.matrix_world @ ue(pad), (0.1, 0.3, 0.95, 1.0), 0.002)
        shot("%s: solved, %s" % (short, rep["state"].split(" ")[0].lower()), centre + side * 0.22 + up * 0.03)
        shot(short + ": solved, from above", centre + up * 0.22 + side * 0.04 - fwd * 0.02)

        # How far the finger's actual skin (index_03_r's) is from the socket, for comparison with the node's pad.
        body = next(o for o in bpy.data.objects if o.type == "MESH" and o.parent == rig)
        gi = body.vertex_groups["index_03_r"].index
        dg = bpy.context.evaluated_depsgraph_get()
        ev = body.evaluated_get(dg)
        me = ev.to_mesh()
        ids = [v.index for v in body.data.vertices if any(gg.group == gi and gg.weight >= 0.6 for gg in v.groups)]
        skin = sum((rig_inv @ (ev.matrix_world @ me.vertices[i].co) for i in ids), Vector()) / max(len(ids), 1)
        ev.to_mesh_clear()
        rep["skin_pad_miss"] = (ue(skin) - goal).length
        # The target in the incoming finger's frame: along the first segment, toward where it curls (about the
        # knuckle's -Z), and along that axis (toward the gun's centre line when negative/positive, see the print).
        f = (p2 - p1).normalized()
        ax = -ue(rig.pose.bones["index_01_r"].matrix.col[2].to_3d()).normalized()
        cdir = ax.cross(f).normalized()
        t = goal - p1
        rep["target_in_finger"] = [t.dot(f), t.dot(cdir), t.dot(ax)]
        rep["goal_from_hand"] = list(ue(goal_fbx) - ue(rig.pose.bones["hand_r"].matrix.translation))
        results[bp] = rep
        print("TFRAME %-20s along %.2f  curl-side %.2f  across %.2f" % (bp, *rep["target_in_finger"]))
        print("TCHECK %-20s %-32s want %.2f (straight %.2f, full %.2f) curl %5.1f->%5.1f swing %5.1f%s miss %.2f skin %.2f"
              % (bp, rep["state"] + " " + rep["contact"], rep["wanted"], rep["reach_straight"], rep["reach_full_curl"], rep["curl_in"],
                 rep["curl_out"], rep["swing"], " CAPPED" if rep["swing_capped"] else "", rep["pad_miss"],
                 rep["skin_pad_miss"]))
    tag = (("_bone" if PARAMS["BoneAxis"] else "") + ("_wrap%d" % PARAMS["WrapCurl"] if PARAMS["WrapCurl"] else "")
           + ("_second%d_tip%d" % (PARAMS["Second"] * 100, PARAMS.get("TipWrap", 40)) if PARAMS.get("Second") else ""))
    with open(os.path.join(OUT, "results%s.json" % tag), "w") as f:
        json.dump({"params": PARAMS, "guns": results}, f, indent=1)
    if tiles:
        A.contact_sheet(tiles, os.path.join(OUT, "sheet%s.png" % tag), per_row=6)
    print("TCHECK done, %d guns" % len(results))


main()
