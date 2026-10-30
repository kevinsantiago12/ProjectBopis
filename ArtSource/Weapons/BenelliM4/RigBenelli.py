# Rigs the Benelli M4 (the "Shotgun 2" model: loose parts, no skeleton) as a skeletal mesh for
# Unreal.
#   blender --background --factory-startup --python RigBenelli.py -- <Shotgun+2.fbx> <out dir>
# The source model is kept next to this script, in Source/Shotgun+2.fbx.
# Writes SK_Benelli.fbx (import into Unreal as a skeletal mesh) and SK_Benelli.blend next to it,
# and prints where the sockets go.
#
# - Barrel turned from -Y to +X (Unreal forward), centimetres (unit scale 0.01, so the FBX is
#   1 unit = 1 cm with no scale on any node).
# - Every part is skinned 100% to one bone (rigid). The modeller gave every part the same pivot,
#   so each bone is placed from its part's shape instead (see place_bones). All are children of
#   `root`, pointing down the barrel with no roll.
# - The origin, and `root`, is in the pistol grip.
# - Three material slots, Body, Stock and Shell; the file's two stray Blinns are folded into
#   them. Only the first UV set is kept (the second is a lightmap set a skeletal mesh never uses).
import bpy, sys, os, math
from mathutils import Matrix, Vector

src, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]

SUFFIX = "XY1510"
# Part -> bone; every other part goes on `root`.
BONE_OF = {
    "Bolt": "bolt",              # bolt and charging handle; cycles on fire, locks back on empty
    "Trigger": "trigger",
    "Bullet_Pusher": "carrier",  # the shell lifter under the receiver
    "Bullet9": "shell",          # the round lying on the carrier
    # No forend bone: the M4 is gas-operated, so the forend never moves (user, 2026-10-30: no
    # pump). The model has no room for a stroke anyway: the forend meets the receiver, the barrel
    # ring is 2.5 cm ahead of it, and there's no magazine tube under it.
}
BONE_ORDER = ["root", "bolt", "trigger", "carrier", "shell"]
# File material -> slot.
SLOT_OF = {
    "Body_Base_Color": "Body", "blinn1": "Body",
    "Stock_Base_Color": "Stock",
    "Bullet_Base_Color": "Shell", "blinn8": "Shell",
}


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
bpy.ops.import_scene.fbx(filepath=src)
scene = bpy.context.scene

parts = {o.name[:-len(SUFFIX)]: o for o in scene.objects if o.type == 'MESH' and o.name.endswith(SUFFIX)}
missing = [n for n in BONE_OF if n not in parts]
if missing:
    raise SystemExit(f"parts missing from the FBX: {missing}")
unknown = {s.material.name for o in parts.values() for s in o.material_slots if s.material} - set(SLOT_OF)
if unknown:
    raise SystemExit(f"materials with no slot: {unknown}")

# Barrel -Y -> +X, metres -> cm.
fix = Matrix.Scale(100.0, 4) @ Matrix.Rotation(math.pi / 2, 4, 'Z')
world = {n: o.matrix_world.copy() for n, o in parts.items()}
before = normal_agreement(parts.values())

# Bake each part's world transform (and the fix) into its vertices; objects end at identity.
for o in parts.values():
    o.parent = None
for n, o in parts.items():
    o.data.transform(fix @ world[n])
    o.matrix_world = Matrix.Identity(4)
    while len(o.data.uv_layers) > 1:
        o.data.uv_layers.remove(o.data.uv_layers[-1])
    if o.data.uv_layers:
        o.data.uv_layers[0].name = "UVMap"
print(f"normals agreement before {before:.3f} after {normal_agreement(parts.values()):.3f}")

# The root sits in the pistol grip (user, 2026-10-30): the middle of the grip at hand height, on
# the centre line. In front of x -22 the stock is only the grip; the butt is further back.
stock = [v.co for v in parts["Rear_Stock"].data.vertices]
band = [v for v in stock if v.x > -22.0 and 1.0 < v.z < 6.0]
grip_lo, grip_hi = bounds(band)
grip = (grip_lo + grip_hi) / 2
grip.y = 0.0
print(f"grip band {len(band)} verts x {grip_lo.x:.2f}..{grip_hi.x:.2f} z {grip_lo.z:.2f}..{grip_hi.z:.2f};"
      f" origin moved to ({grip.x:.2f}, 0, {grip.z:.2f})")
for o in parts.values():
    o.data.transform(Matrix.Translation(-grip))
for o in [o for o in scene.objects if o.type != 'MESH']:
    bpy.data.objects.remove(o, do_unlink=True)

slots = {name: bpy.data.materials.new(name) for name in sorted(set(SLOT_OF.values()))}
for o in parts.values():
    for s in o.material_slots:
        s.material = slots[SLOT_OF[s.material.name]]

for n, o in parts.items():
    group = o.vertex_groups.new(name=BONE_OF.get(n, "root"))
    group.add(range(len(o.data.vertices)), 1.0, 'REPLACE')


def place_bones():
    verts = {n: [v.co.copy() for v in o.data.vertices] for n, o in parts.items()}
    pivots = {"root": Vector((0.0, 0.0, 0.0))}
    lo, hi = bounds(verts["Bolt"])
    pivots["bolt"] = (lo + hi) / 2
    # The trigger swings on a pin at the top of its blade.
    lo, hi = bounds(verts["Trigger"])
    pivots["trigger"] = mean([v for v in verts["Trigger"] if v.z > hi.z - 0.2])
    # The carrier hinges at its back end.
    lo, hi = bounds(verts["Bullet_Pusher"])
    pivots["carrier"] = mean([v for v in verts["Bullet_Pusher"] if v.x < lo.x + 0.3])
    lo, hi = bounds(verts["Bullet9"])
    pivots["shell"] = (lo + hi) / 2
    return pivots, verts


pivots, verts = place_bones()


# Socket suggestions, in Unreal space (Unreal's Y is Blender's -Y), relative to `root`.
def ue(v):
    return f"({v.x:.2f}, {-v.y:.2f}, {v.z:.2f})"


barrel = verts["Long_Barrel"]
front = max(v.x for v in barrel)
muzzle = mean([v for v in barrel if v.x > front - 0.3])
muzzle.x = front
# Ejection port: the bolt's middle, out on the receiver's right side (Blender's -Y).
port = pivots["bolt"].copy()
body = verts["Body"]
port.y = min(v.y for v in body if abs(v.z - port.z) < 1.0 and abs(v.x - port.x) < 3.0)
print("SOCKET MuzzleFlash on root at", ue(muzzle))
print("SOCKET AmmoEject on root at", ue(port), "(the ejection port, right side)")
for name in BONE_ORDER:
    print("BONE", name, "at", ue(pivots[name]))

for o in scene.objects:
    o.select_set(True)
bpy.context.view_layer.objects.active = parts["Body"]
bpy.ops.object.join()
mesh = bpy.context.view_layer.objects.active
mesh.name = mesh.data.name = "SK_Benelli"

scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.01

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
print("bounds", ue(lo), ue(hi), f"length {hi.x - lo.x:.1f} cm")
print("material slots", [s.material.name for s in mesh.material_slots if s.material])
print("uv layers", [uv.name for uv in mesh.data.uv_layers])
print("tris", sum(len(p.vertices) - 2 for p in mesh.data.polygons), "verts", len(mesh.data.vertices))

os.makedirs(out_dir, exist_ok=True)
for o in scene.objects:
    o.select_set(o in (arm, mesh))
bpy.ops.export_scene.fbx(
    filepath=os.path.join(out_dir, "SK_Benelli.fbx"),
    use_selection=True, object_types={'ARMATURE', 'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
    axis_forward='-Z', axis_up='Y',
    mesh_smooth_type='FACE', use_tspace=False,
    add_leaf_bones=False, primary_bone_axis='X', secondary_bone_axis='-Y',
    use_armature_deform_only=True, armature_nodetype='NULL',
    bake_anim=False, path_mode='STRIP')

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "SK_Benelli.blend"))
print("written", out_dir)
