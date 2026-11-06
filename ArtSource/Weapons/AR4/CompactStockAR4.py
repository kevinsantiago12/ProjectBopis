# Collapses the M4's stock: slides the buttstock forward along its buffer tube, as the real gun's does, and keeps every other vertex,
# bone and axis as it was, so the result imports onto the same skeleton (SK_AR4_Skeleton) and the gun's sockets, grips and magazine still
# line up. User, 2026-11-06: "could you make the M4 compact the stock, its super extended at the moment and its cutting into the shoulder on aiming".
#   blender --background --factory-startup --python CompactStockAR4.py -- <SK_AR4 FBX> <out dir> [render dir]
# The source is SK_AR4 exported from Unreal, kept in Source/. Writes SK_AR4_CompactStock.fbx.
#
# - The stock has no bone, but it's separate parts from the tube: everything that ends behind STOCK_FRONT (Unreal y) is stock. The tube and
#   its rail run on to y -2.0 and -6.7, so they stay, and their rear ends disappear inside the stock's shell.
# - SLIDE: the collar reaches y -4.59, leaving a little tube showing behind the castle nut (y -3.23), which is about where a real one stops.
# - Round trip as in ../AK74U/StripStockAK.py: unit scale 0.01 before the import, and these export settings give Unreal back its own bone
#   frames. Vertices skinned to the root come in with no group, export unweighted, and Unreal binds those to the root bone.
import bmesh
import bpy
import math
import os
import sys
from mathutils import Vector

STOCK_FRONT = -13.5     # Unreal y; every part ending behind this is the stock
SLIDE = 9.0             # cm towards the muzzle, in the mesh's own units; the gun's Blueprint scales it

args = sys.argv[sys.argv.index("--") + 1:]
src, out_dir = args[:2]
render_dir = args[2] if len(args) > 2 else None

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.scale_length = 0.01
bpy.ops.import_scene.fbx(filepath=src)
arm = next(o for o in scene.objects if o.type == 'ARMATURE')
mesh = next(o for o in scene.objects if o.type == 'MESH')
M = mesh.matrix_world
to_local = M.inverted().to_3x3()
slide_local = to_local @ Vector((0.0, -SLIDE, 0.0))     # Unreal y is Blender -y


def unreal_y(v):
    return -(M @ v.co).y


bm = bmesh.new()
bm.from_mesh(mesh.data)
bm.verts.ensure_lookup_table()
before = (min(unreal_y(v) for v in bm.verts), max(unreal_y(v) for v in bm.verts))
seen, moved, parts = set(), 0, 0
for v in bm.verts:
    if v.index in seen:
        continue
    stack, part = [v], []
    seen.add(v.index)
    while stack:
        q = stack.pop()
        part.append(q)
        for e in q.link_edges:
            o = e.other_vert(q)
            if o.index not in seen:
                seen.add(o.index)
                stack.append(o)
    if max(unreal_y(p) for p in part) <= STOCK_FRONT:
        parts += 1
        for p in part:
            p.co += slide_local
            moved += 1
after = (min(unreal_y(v) for v in bm.verts), max(unreal_y(v) for v in bm.verts))
bm.to_mesh(mesh.data)
bm.free()
mesh.data.update()
mesh.name = mesh.data.name = "SK_AR4_CompactStock"
print(f"SLID {parts} parts, {moved} of {len(mesh.data.vertices)} vertices by {SLIDE} cm")
print(f"LENGTH {before[1] - before[0]:.1f} -> {after[1] - after[0]:.1f} cm (Unreal y {after[0]:.2f}..{after[1]:.2f})")
print("SLOTS", [s.material.name for s in mesh.material_slots if s.material], "GROUPS", [g.name for g in mesh.vertex_groups])

os.makedirs(out_dir, exist_ok=True)
for o in scene.objects:
    o.select_set(o in (arm, mesh))
bpy.context.view_layer.objects.active = arm
bpy.ops.export_scene.fbx(
    filepath=os.path.join(out_dir, "SK_AR4_CompactStock.fbx"), use_selection=True,
    object_types={'ARMATURE', 'MESH'},
    apply_unit_scale=True, apply_scale_options='FBX_SCALE_NONE', global_scale=1.0,
    axis_forward='-Z', axis_up='Y', primary_bone_axis='Y', secondary_bone_axis='X',
    add_leaf_bones=False, armature_nodetype='NULL', use_armature_deform_only=False,
    mesh_smooth_type='FACE', use_tspace=False, bake_anim=False, path_mode='STRIP')
print("WRITTEN", out_dir)

if render_dir:
    os.makedirs(render_dir, exist_ok=True)
    cam_data = bpy.data.cameras.new("c")
    cam_data.type = 'ORTHO'
    cam = bpy.data.objects.new("c", cam_data)
    scene.collection.objects.link(cam)
    scene.camera = cam
    sun = bpy.data.objects.new("s", bpy.data.lights.new("s", 'SUN'))
    sun.rotation_euler = (math.radians(60), 0, math.radians(40))
    scene.collection.objects.link(sun)
    scene.world = bpy.data.worlds.new("w")
    scene.world.color = (0.8, 0.8, 0.8)
    scene.render.engine = 'BLENDER_WORKBENCH'
    scene.display.shading.show_cavity = True
    scene.render.resolution_x, scene.render.resolution_y = 1400, 800
    pts = [M @ v.co for v in mesh.data.vertices]
    lo, hi = [min(p[i] for p in pts) for i in range(3)], [max(p[i] for p in pts) for i in range(3)]
    for name, y_, scale, rz in (("rear_side", hi[1] - 18.0, 45.0, 90), ("whole_side", (lo[1] + hi[1]) / 2, (hi[1] - lo[1]) * 1.1, 90)):
        cam.location = (hi[0] + 60.0, y_, (lo[2] + hi[2]) / 2)
        cam.rotation_euler = (math.radians(90), 0, math.radians(rz))
        cam_data.ortho_scale = scale
        scene.render.filepath = os.path.join(render_dir, name + ".png")
        bpy.ops.render.render(write_still=True)
    # From behind and below, to see inside the stock's front.
    cam.location = (hi[0] + 40.0, hi[1] - 30.0, lo[2] - 5.0)
    cam.rotation_euler = (math.radians(100), 0, math.radians(110))
    cam_data.ortho_scale = 40.0
    scene.render.filepath = os.path.join(render_dir, "rear_low.png")
    bpy.ops.render.render(write_still=True)
print("DONE")
