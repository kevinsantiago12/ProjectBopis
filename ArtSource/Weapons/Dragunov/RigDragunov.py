# Normalizes the Sniper Rifle Pack's Dragunov (SVD) to our weapon standard: one skeletal mesh for
# Unreal, built from the pack's three pieces (rifle, magazine, scope).
#   blender --background --factory-startup --python RigDragunov.py -- <source dir> <out dir>
# The sources are kept next to this script, in Source/: SKM_Dragunov.FBX, SKM_Dragunov_Mag.FBX and
# SM_Dragunov_Scope.FBX, exported from Unreal by the user (2026-10-30).
# Writes SK_Dragunov.fbx (import into Unreal as a skeletal mesh) and SK_Dragunov.blend next to it,
# and prints where the sockets go.
#
# - Barrel along +Y (our standard; the pack's already is), centimetres (unit scale 0.01, so the FBX
#   is 1 unit = 1 cm with no scale on any node). Unreal-exported FBXs come in at that scale once the
#   scene's unit scale is set before the import.
# - The magazine and scope go where the pack's own Blueprint (BP_Sniper) holds them.
# - Every part is skinned 100% to one bone (rigid), as the pack's rifle already was. The bones are
#   children of `root` and unrotated (as the Benelli's), so a socket that needs X down the barrel
#   takes yaw 90.
# - The origin, and `root`, is in the pistol grip.
# - Three material slots: Body (rifle and magazine share a texture set), Scope, and Lens (the
#   scope's glass, its own small set). Only the first UV set is kept (the scope's second is a
#   lightmap set a skeletal mesh never uses), and the scope's collision hull is dropped.
import bpy, sys, os, re
from mathutils import Matrix, Vector

src_dir, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]

# Where the pack's BP_Sniper holds the magazine and scope, in Unreal space (relative to the rifle).
MAG_OFFSET = Vector((-0.11, 24.30, 0.0))
SCOPE_OFFSET = Vector((-0.38, 16.91, 15.74))
# The rifle's own skin groups -> ours.
GROUP_OF = {"Body": "root", "Trigger": "trigger", "Charging_Handle": "bolt"}
BONE_ORDER = ["root", "bolt", "trigger", "magazine"]
# File material -> slot.
SLOT_OF = {"MI_Dragunov_1": "Body", "MI_Scopes": "Scope", "MI_Scopes_Glass": "Lens"}


def base(name):
    # Blender suffixes a repeated name (the magazine's copy of the body material is ".001").
    return re.sub(r"\.\d{3}$", "", name)


def bl(v):
    # Unreal -> Blender (Unreal's Y is Blender's -Y).
    return Vector((v.x, -v.y, v.z))


def ue(v):
    return f"({v.x:.2f}, {-v.y:.2f}, {v.z:.2f})"


def normal_agreement(objects):
    # Mean dot of each corner normal with its face normal: drops sharply if custom normals
    # didn't follow the geometry.
    total, count = 0.0, 0
    for o in objects:
        me = o.data
        me.calc_normals_split()
        for p in me.polygons:
            for li in p.loop_indices:
                total += me.loops[li].normal.dot(p.normal)
                count += 1
    return total / max(count, 1)


def bounds(verts):
    return (Vector((min(v.x for v in verts), min(v.y for v in verts), min(v.z for v in verts))),
            Vector((max(v.x for v in verts), max(v.y for v in verts), max(v.z for v in verts))))


def mean(verts):
    return sum(verts, Vector()) / len(verts)


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0   # no .blend1 backups
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.01


def load(name):
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(src_dir, name + ".FBX"))
    return [o for o in bpy.data.objects if o not in before]


rifle_objs, mag_objs, scope_objs = load("SKM_Dragunov"), load("SKM_Dragunov_Mag"), load("SM_Dragunov_Scope")
rifle = next(o for o in rifle_objs if o.type == 'MESH')
mag = next(o for o in mag_objs if o.type == 'MESH')
scope = next(o for o in scope_objs if o.type == 'MESH' and not o.name.startswith("UCX_"))
parts = [rifle, mag, scope]

missing = set(GROUP_OF) - {g.name for g in rifle.vertex_groups}
if missing:
    raise SystemExit(f"rifle skin groups missing: {missing}")
unknown = {base(s.material.name) for o in parts for s in o.material_slots if s.material} - set(SLOT_OF)
if unknown:
    raise SystemExit(f"materials with no slot: {unknown}")

# The pack placed the trigger's bone on its pin and the charging handle's on the handle; keep them.
rifle_arm = next(o for o in rifle_objs if o.type == 'ARMATURE')
pivots = {GROUP_OF[b.name]: rifle_arm.matrix_world @ b.head_local
          for b in rifle_arm.data.bones if b.name in ("Trigger", "Charging_Handle")}
# The magazine's own origin (its Mag bone), where the pack's SM_Dragunov_Mag lines up too.
pivots["magazine"] = bl(MAG_OFFSET)

before = normal_agreement(parts)
# Bake each piece's world transform (and its place on the rifle) into its vertices; objects end at
# identity with no parent, modifiers or extra UV sets.
for o, offset in ((rifle, None), (mag, MAG_OFFSET), (scope, SCOPE_OFFSET)):
    o.data = o.data.copy()
    world = o.matrix_world.copy()
    o.parent = None
    o.modifiers.clear()
    o.data.transform(world)
    if offset is not None:
        o.data.transform(Matrix.Translation(bl(offset)))
    o.matrix_world = Matrix.Identity(4)
    while len(o.data.uv_layers) > 1:
        o.data.uv_layers.remove(o.data.uv_layers[-1])
    o.data.uv_layers[0].name = "UVMap"
for o in rifle_objs + mag_objs + scope_objs:
    if o not in parts:
        bpy.data.objects.remove(o, do_unlink=True)
print(f"normals agreement before {before:.3f} after {normal_agreement(parts):.3f}")

# Skin groups: the rifle's renamed to ours; the magazine and scope each wholly on one bone.
for g in rifle.vertex_groups:
    g.name = GROUP_OF[g.name]
for o, bone in ((mag, "magazine"), (scope, "root")):
    o.vertex_groups.clear()
    o.vertex_groups.new(name=bone).add(range(len(o.data.vertices)), 1.0, 'REPLACE')

slots = {name: bpy.data.materials.new(name) for name in sorted(set(SLOT_OF.values()))}
for o in parts:
    for s in o.material_slots:
        s.material = slots[SLOT_OF[base(s.material.name)]]

# The root sits in the pistol grip: the middle of the grip between its bottom and the receiver
# (Unreal y -5..4.5, z -3.5..1: the stock's lower bar meets it further back, the trigger guard
# further forward), on the bore's centre line.
rifle_verts = [v.co.copy() for v in rifle.data.vertices]
front = min(v.y for v in rifle_verts)                       # Blender -Y is the muzzle
tip = [v for v in rifle_verts if v.y < front + 0.3]
muzzle = mean(tip)
muzzle.y = front
band = [v for v in rifle_verts if -4.5 < v.y < 5.0 and -3.5 < v.z < 1.0]
grip_lo, grip_hi = bounds(band)
grip = (grip_lo + grip_hi) / 2
grip.x = muzzle.x
print(f"grip band {len(band)} verts, origin moved to {ue(grip)} (Unreal, the pack's frame)")
for o in parts:
    o.data.transform(Matrix.Translation(-grip))
for k in pivots:
    pivots[k] = pivots[k] - grip
pivots["root"] = Vector()
muzzle -= grip
rifle_verts = [v - grip for v in rifle_verts]

# Socket suggestions, in Unreal space, relative to their bone (all on root but Magazine).
bolt_verts = [v.co for v in rifle.data.vertices
              if any(rifle.vertex_groups[g.group].name == "bolt" for g in v.groups)]
handle = mean(bolt_verts)
# The ejection port: the receiver's right wall (Unreal -X, Blender -X) beside the bolt.
port = handle.copy()
port.x = min(v.x for v in rifle_verts if abs(v.z - port.z) < 1.0 and abs(v.y - port.y) < 3.0)
# The left hand: under the handguard, a third of the way along it from the receiver.
guard = [v for v in rifle_verts if -48.0 < v.y < -42.0]
hand = Vector((muzzle.x, -45.0, min(v.z for v in guard) + 1.0))
print("SOCKET MuzzleFlash on root at", ue(muzzle), "rotation yaw 90 (X out of the barrel)")
print("SOCKET AmmoEject on root at", ue(port), "(the receiver's right side beside the bolt)")
print("SOCKET LeftHandGrip on root at", ue(hand), "(under the handguard; tune in play)")
print("SOCKET Magazine on magazine at (0.00, 0.00, 0.00): SM_Dragunov_Mag lines up with no offset")
for name in BONE_ORDER:
    print("BONE", name, "at", ue(pivots[name]))

for o in scene.objects:
    o.select_set(o in parts)
bpy.context.view_layer.objects.active = rifle
bpy.ops.object.join()
mesh = bpy.context.view_layer.objects.active
mesh.name = mesh.data.name = "SK_Dragunov"

arm = bpy.data.objects.new("Armature", bpy.data.armatures.new("Armature"))
scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
edit = arm.data.edit_bones
for name in BONE_ORDER:
    b = edit.new(name)
    b.head = pivots[name]
    b.tail = b.head + Vector((3.0, 0.0, 0.0))
    b.roll = 0.0
    if name != "root":
        b.parent = edit["root"]
bpy.ops.object.mode_set(mode='OBJECT')

mesh.parent = arm
mesh.modifiers.new("Armature", 'ARMATURE').object = arm

lo, hi = bounds([v.co for v in mesh.data.vertices])
print("bounds", ue(Vector((lo.x, hi.y, lo.z))), ue(Vector((hi.x, lo.y, hi.z))), f"length {hi.y - lo.y:.1f} cm")
print("material slots", [s.material.name for s in mesh.material_slots if s.material])
print("uv layers", [uv.name for uv in mesh.data.uv_layers])
print("groups", [g.name for g in mesh.vertex_groups])
print("tris", sum(len(p.vertices) - 2 for p in mesh.data.polygons), "verts", len(mesh.data.vertices))

os.makedirs(out_dir, exist_ok=True)
for o in scene.objects:
    o.select_set(o in (arm, mesh))
bpy.ops.export_scene.fbx(
    filepath=os.path.join(out_dir, "SK_Dragunov.fbx"),
    use_selection=True, object_types={'ARMATURE', 'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
    axis_forward='-Z', axis_up='Y',
    mesh_smooth_type='FACE', use_tspace=False,
    add_leaf_bones=False, primary_bone_axis='X', secondary_bone_axis='-Y',
    use_armature_deform_only=True, armature_nodetype='NULL',
    bake_anim=False, path_mode='STRIP')

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "SK_Dragunov.blend"))
print("written", out_dir)
