"""Builds the muzzle-flash mesh and writes SM_MuzzleFlash.fbx beside this script.

    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe" --background --factory-startup
        --python Tools/FX/MuzzleFlash/bl_mesh.py

The mesh is 1 m (100 cm in Unreal) long along +X out of the muzzle and 1 m wide; UMuzzleFlashComponent scales
it to the gun's flash size every frame (length on X, width on Y and Z), so these are proportions only.
- FIN_PLANES side cards through the X axis, 180/FIN_PLANES degrees apart: the flame seen from the side. UV U runs
  0 at the muzzle to 1 at the tip, V across (0.5 on the axis). Vertex colour R 0, G the card's number / FIN_PLANES.
- One front card across the barrel, STAR_X out: the flame seen down the barrel. Vertex colour R 1.
The material fades each card as it turns edge-on, so every angle shows the card that suits it. 8 triangles."""
import math
import os
import sys

import bpy

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D  # noqa: E402

OUT = os.path.join(HERE, "SM_MuzzleFlash.fbx")

for o in list(bpy.data.objects):                  # the startup scene's cube, camera and light
    bpy.data.objects.remove(o, do_unlink=True)

verts, faces, face_uvs, face_colours = [], [], [], []


def quad(corners, colour):
    base = len(verts)
    verts.extend(corners)
    faces.append((base, base + 1, base + 2, base + 3))
    face_uvs.append([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)])
    face_colours.append(colour)


for k in range(D.FIN_PLANES):
    th = math.radians(k * 180.0 / D.FIN_PLANES)
    y, z = 0.5 * math.cos(th), 0.5 * math.sin(th)
    quad([(0.0, -y, -z), (1.0, -y, -z), (1.0, y, z), (0.0, y, z)], (0.0, k / D.FIN_PLANES, 0.0, 1.0))

h, x = D.STAR_HALF, D.STAR_X
quad([(x, -h, -h), (x, h, -h), (x, h, h), (x, -h, h)], (1.0, 0.0, 0.0, 1.0))

mesh = bpy.data.meshes.new("SM_MuzzleFlash")
mesh.from_pydata(verts, [], faces)
uv = mesh.uv_layers.new(name="UVMap")
col = mesh.color_attributes.new(name="Col", type="BYTE_COLOR", domain="CORNER")
for poly in mesh.polygons:
    for i, loop in enumerate(poly.loop_indices):
        uv.data[loop].uv = face_uvs[poly.index][i]
        col.data[loop].color = face_colours[poly.index]
mesh.update()

obj = bpy.data.objects.new("SM_MuzzleFlash", mesh)
bpy.context.scene.collection.objects.link(obj)

bpy.ops.export_scene.fbx(filepath=OUT, use_selection=False, object_types={"MESH"}, mesh_smooth_type="FACE",
                         add_leaf_bones=False, apply_unit_scale=True, global_scale=1.0, colors_type="SRGB",
                         use_mesh_modifiers=False, bake_anim=False)
print("[FLASH] wrote %s: %d cards, %d verts" % (OUT, len(faces), len(verts)))
