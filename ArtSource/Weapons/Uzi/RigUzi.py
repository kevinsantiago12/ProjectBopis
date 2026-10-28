# Rigs the CGTrader Micro Uzi (loose parts, no skeleton) as a skeletal mesh for Unreal.
#   blender --background --factory-startup --python RigUzi.py -- <UziRigged.fbx> <out dir>
# Writes SK_Uzi.fbx (import into Unreal as a skeletal mesh), SM_Uzi_Mag.fbx (static, the
# dropped magazine) and SK_Uzi.blend next to it, and prints where the sockets go.
#
# - Barrel turned from -X to +X (Unreal forward), centimetres (unit scale 0.01, so the FBX
#   is 1 unit = 1 cm with no scale on any node).
# - Every part is skinned 100% to one bone (rigid). Bones sit on the pivots the modeller gave
#   each part, all children of `root` at the origin, pointing down the barrel with no roll.
# - Dropped: the loose display round (`bullet`, 5 cm beside the gun) and the folding stock.
import bpy, sys, os, math
from mathutils import Matrix, Vector

src, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]

# Part -> bone. Parts not listed here are dropped.
PARTS = {
    "Body": "root", "sight": "root",
    "Bolt": "bolt",                 # seen through the ejection port; kicks back on fire
    "slide": "charging_handle",     # the knob on the top cover
    "Mag": "mag",
    "Trigger": "trigger",
    "button": "grip_safety",
    "switch1": "selector",
    # The folding stock (`stock` and its hinge `stock2`) is dropped (user, 2026-10-28).
}
# Bone -> the part whose pivot it sits on.
PIVOTS = {
    "bolt": "Bolt", "charging_handle": "slide", "mag": "Mag", "trigger": "Trigger",
    "grip_safety": "button", "selector": "switch1",
}
BONE_ORDER = ["root", "bolt", "charging_handle", "mag", "trigger", "grip_safety", "selector"]


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


bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.context.preferences.filepaths.save_version = 0   # no .blend1 backups
bpy.ops.import_scene.fbx(filepath=src)
scene = bpy.context.scene

objs = {o.name: o for o in scene.objects}
missing = [n for n in PARTS if n not in objs]
if missing:
    raise SystemExit(f"parts missing from the FBX: {missing}")

fix = Matrix.Scale(100.0, 4) @ Matrix.Rotation(math.pi, 4, 'Z')
world = {n: o.matrix_world.copy() for n, o in objs.items()}
pivots = {bone: fix @ world[part].translation for bone, part in PIVOTS.items()}

for n, o in list(objs.items()):
    if n not in PARTS:
        print("dropped", n)
        bpy.data.objects.remove(o, do_unlink=True)
parts = [objs[n] for n in PARTS]
before = normal_agreement(parts)

# Bake each part's world transform (and the fix) into its vertices; objects end at identity.
for o in parts:
    if o.data.users > 1:
        o.data = o.data.copy()
for o in parts:
    o.parent = None
for o in parts:
    o.data.transform(fix @ world[o.name])
    o.matrix_world = Matrix.Identity(4)
    if o.data.uv_layers:
        o.data.uv_layers[0].name = "UVMap"
print(f"normals agreement before {before:.3f} after {normal_agreement(parts):.3f}")

for o in parts:
    group = o.vertex_groups.new(name=PARTS[o.name])
    group.add(range(len(o.data.vertices)), 1.0, 'REPLACE')

# The dropped magazine: the Mag part on its own, pivot on the `mag` bone, so a `Magazine`
# socket on that bone with no offset lines it up exactly.
mag_mesh = objs["Mag"].data.copy()
mag_mesh.name = "SM_Uzi_Mag"
mag_mesh.transform(Matrix.Translation(-pivots["mag"]))

# Socket suggestions, in Unreal space (Unreal's Y is Blender's -Y), relative to their bone.
def ue(v):
    return f"({v.x:.2f}, {-v.y:.2f}, {v.z:.2f})"
body_verts = [v.co for v in objs["Body"].data.vertices]
front = max(v.x for v in body_verts)
tip = [v for v in body_verts if v.x > front - 0.3]
muzzle = sum(tip, Vector()) / len(tip)
muzzle.x = front
# Ejection port: the bolt's middle, out on the receiver's right side (Blender's -Y).
bolt_verts = [v.co for v in objs["Bolt"].data.vertices]
port = sum(bolt_verts, Vector()) / len(bolt_verts)
port.y = min(v.y for v in body_verts if abs(v.z - port.z) < 1.0 and abs(v.x - port.x) < 3.0)
print("SOCKET MuzzleFlash on root at", ue(muzzle))
print("SOCKET AmmoEject on root at", ue(port), "(the ejection port, right side)")
print("SOCKET Magazine on mag at (0.00, 0.00, 0.00)")

body = objs["Body"]
for o in scene.objects:
    o.select_set(o in parts)
bpy.context.view_layer.objects.active = body
bpy.ops.object.join()
mesh = bpy.context.view_layer.objects.active
mesh.name = mesh.data.name = "SK_Uzi"

scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 0.01

arm = bpy.data.objects.new("Armature", bpy.data.armatures.new("Armature"))
scene.collection.objects.link(arm)
bpy.context.view_layer.objects.active = arm
bpy.ops.object.mode_set(mode='EDIT')
edit = arm.data.edit_bones
for name in BONE_ORDER:
    b = edit.new(name)
    b.head = pivots.get(name, Vector((0.0, 0.0, 0.0)))
    b.tail = b.head + Vector((3.0, 0.0, 0.0))
    b.roll = 0.0
    if name != "root":
        b.parent = edit["root"]
bpy.ops.object.mode_set(mode='OBJECT')

mesh.parent = arm
mesh.modifiers.new("Armature", 'ARMATURE').object = arm

print("material slots", [s.material.name for s in mesh.material_slots if s.material])
print("uv layers", [uv.name for uv in mesh.data.uv_layers])
print("tris", sum(len(p.vertices) - 2 for p in mesh.data.polygons), "verts", len(mesh.data.vertices))

os.makedirs(out_dir, exist_ok=True)
for o in scene.objects:
    o.select_set(o in (arm, mesh))
bpy.ops.export_scene.fbx(
    filepath=os.path.join(out_dir, "SK_Uzi.fbx"),
    use_selection=True, object_types={'ARMATURE', 'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
    axis_forward='-Z', axis_up='Y',
    mesh_smooth_type='FACE', use_tspace=False,
    add_leaf_bones=False, primary_bone_axis='X', secondary_bone_axis='-Y',
    use_armature_deform_only=True, armature_nodetype='NULL',
    bake_anim=False, path_mode='STRIP')

mag = bpy.data.objects.new("SM_Uzi_Mag", mag_mesh)
scene.collection.objects.link(mag)
for o in scene.objects:
    o.select_set(o == mag)
bpy.ops.export_scene.fbx(
    filepath=os.path.join(out_dir, "SM_Uzi_Mag.fbx"),
    use_selection=True, object_types={'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
    axis_forward='-Z', axis_up='Y',
    mesh_smooth_type='FACE', use_tspace=False, bake_anim=False, path_mode='STRIP')
bpy.data.objects.remove(mag, do_unlink=True)

bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out_dir, "SK_Uzi.blend"))
print("written", out_dir)
