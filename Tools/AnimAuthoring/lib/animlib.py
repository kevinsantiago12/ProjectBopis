"""Shared Blender helpers for authoring Unreal animations by script (the project folders beside lib/; see README.md).

Spaces. Everything is worked in the FBX space Unreal exports: centimetres, Unreal's axes with Y negated.
- The character's armature space is that space. Blender turns the FBX's root bone ('root') into the armature
  object and puts the cm -> m scale (0.01) on it, so pose-bone matrices come out in cm.
- A gun's component space is its FBX's top node: an empty when the exporter wrote one (the revolver, the
  Mossberg), otherwise the armature object Blender made of the root bone (the AR4).
- Unreal values convert with S = diag(1, -1, 1): a location (x, y, z) becomes (x, -y, z), a rotation R
  becomes S R S (ue_rotator, ue_xform).
"""
import math
import os

import bpy
from mathutils import Matrix, Quaternion, Vector

FPS = 30.0
S = Matrix.Diagonal((1.0, -1.0, 1.0, 1.0))


# --- Unreal <-> FBX space ----------------------------------------------------------------------------------
def ue_rotator(pitch, yaw, roll):
    """An Unreal FRotator as a 4x4 rotation in FBX space."""
    p, y, r = (math.radians(a) for a in (pitch, yaw, roll))
    cp, sp, cy, sy, cr, sr = math.cos(p), math.sin(p), math.cos(y), math.sin(y), math.cos(r), math.sin(r)
    x_axis = Vector((cp * cy, cp * sy, sp))
    y_axis = Vector((sr * sp * cy - cr * sy, sr * sp * sy + cr * cy, -sr * cp))
    z_axis = Vector((-(cr * sp * cy + sr * sy), cy * sr - cr * sp * sy, cr * cp))
    m = Matrix.Identity(4)
    for i, axis in enumerate((x_axis, y_axis, z_axis)):
        m.col[i] = (axis.x, axis.y, axis.z, 0.0)
    return S @ m @ S


def ue_xform(location=(0.0, 0.0, 0.0), pitch=0.0, yaw=0.0, roll=0.0):
    """An Unreal relative transform (a socket, a grip offset: location, then rotation) in FBX space."""
    return Matrix.Translation(Vector((location[0], -location[1], location[2]))) @ ue_rotator(pitch, yaw, roll)


def normalised(m):
    """A matrix's rotation and location, scale dropped."""
    loc, rot, _ = m.decompose()
    return Matrix.Translation(loc) @ rot.to_matrix().to_4x4()


# BP_PlayerCharacter / BP_EnemyBase attach guns to this socket on hand_r (WeaponAttachSocketName), then apply
# the weapon's GripLocationOffset and GripRotationOffset.
HANDGRIP_R = ue_xform((-7.012, 2.049, 0.0), yaw=90.0)


# --- Scene -------------------------------------------------------------------------------------------------
def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.render.fps = int(FPS)


def import_fbx(path):
    """Imports an FBX with its bone frames as written (no bone correction); returns the new objects."""
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=path, use_anim=True, automatic_bone_orientation=False, ignore_leaf_bones=False)
    return [o for o in bpy.data.objects if o not in before]


def setup_character(directory, anim_fbx, mesh_fbx="SKM_Manny_Simple.fbx"):
    """The character animation as the armature 'Rig', with the mesh skinned to it and the scene's frame range
    set to the animation's. Import the character before any gun: guns are placed relative to it."""
    clear_scene()
    rig = next(o for o in import_fbx(os.path.join(directory, anim_fbx)) if o.type == "ARMATURE")
    rig.name = "Rig"
    mesh_objs = import_fbx(os.path.join(directory, mesh_fbx))
    mesh_rig = next(o for o in mesh_objs if o.type == "ARMATURE")
    for o in mesh_objs:
        if o.type == "MESH":
            o.parent = rig
            o.matrix_parent_inverse = Matrix.Identity(4)
            for mod in o.modifiers:
                if mod.type == "ARMATURE":
                    mod.object = rig
    bpy.data.objects.remove(mesh_rig, do_unlink=True)
    scene = bpy.context.scene
    act = rig.animation_data.action
    scene.frame_start = int(act.frame_range[0])
    scene.frame_end = int(act.frame_range[1])
    return rig


class Gun:
    """A gun FBX ridden on hand_r the way WeaponHolderComponent places it."""

    def __init__(self, rig, path, grip):
        """path: the gun's skeletal mesh FBX; grip: the weapon's GripLocationOffset / GripRotationOffset
        (ue_xform). Import right after setup_character, while the rig is still at its import transform."""
        objs = import_fbx(path)
        self.arm = next(o for o in objs if o.type == "ARMATURE")
        self.top = next((o for o in objs if o.type == "EMPTY"), None)
        self.meshes = [o for o in objs if o.type == "MESH"]
        self.grip = grip
        self.node = self.top or self.arm
        rig_inv = rig.matrix_world.inverted()
        self.node_offset = rig_inv @ self.node.matrix_world     # the top node in component space (cm)
        self.arm_to_comp = rig_inv @ self.arm.matrix_world      # armature space -> component space (cm)

    def matrix(self, rig):
        """The gun's component space in the rig's space for the rig's current pose."""
        return rig.pose.bones["hand_r"].matrix @ HANDGRIP_R @ self.grip

    def place(self, rig):
        """Moves the gun into the right hand (for renders)."""
        self.node.matrix_world = rig.matrix_world @ self.matrix(rig) @ self.node_offset

    def rest(self, bone):
        """A bone's rest matrix in component space (cm), unit scale. The root bone Blender made the armature
        object is asked for by the object's name."""
        if bone not in self.arm.data.bones:
            return normalised(self.arm_to_comp)
        return normalised(self.arm_to_comp @ self.arm.data.bones[bone].matrix_local)

    def pose(self, bone):
        return normalised(self.arm_to_comp @ self.arm.pose.bones[bone].matrix)

    def set_pose(self, bone, comp_matrix, scale=1.0):
        """Poses a bone by its component-space matrix (rotation + location), with a uniform scale on top of
        the bone's own (the revolver's bones carry 100x)."""
        rest_scale = (self.arm_to_comp @ self.arm.data.bones[bone].matrix_local).to_scale()[0]
        m = comp_matrix.normalized() @ Matrix.Diagonal((rest_scale * scale,) * 3 + (1.0,))
        self.arm.pose.bones[bone].matrix = self.arm_to_comp.inverted() @ m


# --- Timing and curves -------------------------------------------------------------------------------------
def frame_of(t):
    """The scene frame at t seconds into the animation."""
    return int(round(t * FPS)) + bpy.context.scene.frame_start


def smooth(x):
    x = max(0.0, min(1.0, x))
    return x * x * (3.0 - 2.0 * x)


def ramp(t, a, b):
    """0 before a, 1 after b, smoothstep between."""
    return smooth((t - a) / (b - a))


def catmull(points, t):
    """Catmull-Rom through (time, Vector) points, clamped at the ends."""
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


def slerp_keys(keys, t):
    """(time, Quaternion) keys; eased slerp between neighbours."""
    if t <= keys[0][0]:
        return keys[0][1].copy()
    if t >= keys[-1][0]:
        return keys[-1][1].copy()
    i = max(k for k in range(len(keys) - 1) if keys[k][0] <= t)
    (ta, qa), (tb, qb) = keys[i], keys[i + 1]
    if qa.dot(qb) < 0.0:
        qb = -qb
    return qa.slerp(qb, smooth((t - ta) / (tb - ta)))


# --- Hands and arms ----------------------------------------------------------------------------------------
def basis(fingers, knuckles):
    """A rotation whose X runs along `fingers` and Y along `knuckles` (made perpendicular)."""
    x = fingers.normalized()
    y = (knuckles - x * knuckles.dot(x)).normalized()
    return Matrix((x, y, x.cross(y))).transposed().to_quaternion()


def hand_l_basis(fingers, palm):
    """A left hand's basis from where its fingers point and which way its palm faces (index -> pinky is
    fingers x palm for a left hand)."""
    return basis(fingers, fingers.normalized().cross(palm.normalized()))


def finger_basis(rig, side="l"):
    """A hand's orientation (rig space) from its finger bases: wrist -> middle_01, index_01 -> pinky_01. With
    the bone's own rotation it gives a fixed offset (from_basis) for posing hands by basis()."""
    p = rig.pose.bones
    wrist = p["hand_" + side].matrix.translation
    return basis(p["middle_01_" + side].matrix.translation - wrist,
                 p["pinky_01_" + side].matrix.translation - p["index_01_" + side].matrix.translation)


def rotate_about(matrix, pivot, rot):
    """Rotates an armature-space bone matrix by a Quaternion about a pivot point."""
    return Matrix.Translation(pivot) @ rot.to_matrix().to_4x4() @ Matrix.Translation(-pivot) @ matrix


def arm_lengths(rig):
    """Upper arm and forearm lengths for each side, from the current pose."""
    p = rig.pose.bones
    return {s: ((p["lowerarm_" + s].matrix.translation - p["upperarm_" + s].matrix.translation).length,
                (p["hand_" + s].matrix.translation - p["lowerarm_" + s].matrix.translation).length)
            for s in ("l", "r")}


def solve_arm(pb, side, wrist, hand_q, pole_point, lengths):
    """Two-bone IK: swings upperarm/lowerarm so the wrist lands on `wrist` with the elbow toward
    `pole_point`, rolls the forearm half the hand's twist, then sets the hand's orientation. Returns how far
    the wrist ended from where it was asked to go (out of reach: clamped short)."""
    upper, lower, hand = ("upperarm_" + side, "lowerarm_" + side, "hand_" + side)
    l1, l2 = lengths
    target = wrist
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
    pb[upper].matrix = rotate_about(pb[upper].matrix.copy(), shoulder,
                                    (old_elbow - shoulder).rotation_difference(elbow - shoulder))
    bpy.context.view_layer.update()

    old_wrist = pb[hand].matrix.translation.copy()
    pb[lower].matrix = rotate_about(pb[lower].matrix.copy(), elbow,
                                    (old_wrist - elbow).rotation_difference(wrist - elbow))
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
    return (pb[hand].matrix.translation - target).length


# --- Renders -----------------------------------------------------------------------------------------------
def setup_render(res=(640, 480), material_colours=None):
    """Workbench renders through a new camera. material_colours: {material name prefix: RGBA} to colour by
    material (others grey); None colours by object."""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL" if material_colours else "OBJECT"
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.image_settings.file_format = "PNG"
    scene.world = bpy.data.worlds.new("W")
    cam_data = bpy.data.cameras.new("Cam")
    cam_data.lens = 35
    cam = bpy.data.objects.new("Cam", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    if material_colours:
        for mat in bpy.data.materials:
            mat.diffuse_color = material_colours.get(mat.name.split(".")[0], (0.55, 0.55, 0.58, 1))
    return cam


def look_at(cam, eye, target):
    direction = (target - eye).normalized()
    cam.location = eye
    cam.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def game_camera(cam, rig, aimed=True):
    """The game's camera boom as the rig sees it: 70 cm above the capsule's centre (~162 cm off the floor),
    140 back, 65 right and 15 up aimed (75 degrees), or 300 back and 50 right at the hip (90); looking level."""
    eye = Vector((-65.0, 140.0, 177.0)) if aimed else Vector((-50.0, 300.0, 162.0))
    look_at(cam, rig.matrix_world @ eye, rig.matrix_world @ (eye + Vector((0.0, -100.0, 0.0))))
    cam.data.sensor_fit = "HORIZONTAL"
    cam.data.angle = math.radians(75.0 if aimed else 90.0)


def render_tile(path):
    """Renders the scene to `path` and returns its pixels (rows bottom-up)."""
    import numpy as np
    scene = bpy.context.scene
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    img = bpy.data.images.load(path, check_existing=False)
    px = np.array(img.pixels[:], dtype=np.float32).reshape(img.size[1], img.size[0], 4)
    bpy.data.images.remove(img)
    return px


def contact_sheet(tiles, path, per_row=5):
    """Lays render_tile pixels out in rows, left to right and top to bottom, and saves them as a PNG."""
    import numpy as np
    tiles = list(tiles)
    while len(tiles) % per_row:
        tiles.append(np.zeros_like(tiles[0]))
    rows = [np.concatenate(tiles[i:i + per_row], axis=1) for i in range(0, len(tiles), per_row)]
    sheet = np.concatenate(rows[::-1], axis=0)
    h, w = sheet.shape[:2]
    out = bpy.data.images.new(os.path.basename(path), w, h, alpha=True)
    out.pixels[:] = sheet.ravel()
    out.filepath_raw = path
    out.file_format = "PNG"
    out.save()


# --- Export ------------------------------------------------------------------------------------------------
def export_armature(obj, name, path, frame_end, scale=1.0):
    """Writes an armature's action as an FBX for Unreal's legacy importer.

    obj: the armature. name: its root bone's name in Unreal (Blender made the root bone the object).
    frame_end: the last frame (the scene starts at 1, 30 fps). scale: the root bone's scale in Unreal (1;
    the revolver's root carries 100).
    The import keyed the root's track onto the object (the cm -> m scale included) and those keys win over
    the object's transform, so they're dropped; the root never moves in these clips. One Blender unit is
    written as one centimetre."""
    scene = bpy.context.scene
    scene.render.fps = int(FPS)
    scene.frame_start = 1
    scene.frame_end = frame_end
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 0.01
    if obj.animation_data and obj.animation_data.action:
        act = obj.animation_data.action
        for fc in [fc for fc in act.fcurves if not fc.data_path.startswith("pose.bones")]:
            act.fcurves.remove(fc)
    loc, rot, _ = obj.matrix_world.decompose()
    obj.parent = None
    obj.matrix_world = Matrix.LocRotScale(loc, rot, Vector((scale, scale, scale)))
    obj.name = name
    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj
    bpy.ops.export_scene.fbx(
        filepath=path, use_selection=True, object_types={"ARMATURE"}, add_leaf_bones=False,
        primary_bone_axis="Y", secondary_bone_axis="X", armature_nodetype="NULL",
        axis_forward="-Y", axis_up="Z", global_scale=1.0, apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_NONE", bake_space_transform=False,
        bake_anim=True, bake_anim_use_all_actions=False, bake_anim_use_nla_strips=False,
        bake_anim_force_startend_keying=True, bake_anim_step=1.0, bake_anim_simplify_factor=0.0,
        use_armature_deform_only=False)
    print("EXPORTED", path)
