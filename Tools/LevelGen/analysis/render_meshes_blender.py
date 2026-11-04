"""Blender (4.0), background: renders every mesh export_meshes_ue.py wrote from three angles, textured with its slots'
base colour, so the packs' models can be looked at, not just measured. Workbench engine (fast, no lights to set up).
Views, in Unreal axes (the FBX import maps UE (x, y, z) to Blender (x, -y, z)):
  a  isometric from the -X -Y corner (UE: from behind-left)   b  isometric from the +X +Y corner
  t  straight down (UE +X up the image, +Y to the right)
Writes Saved/LevelGen/visual/renders/<group>/<name>_<a|b|t>.png. Skips meshes already rendered.

Run: blender -b --factory-startup -P Tools/LevelGen/analysis/render_meshes_blender.py -- [first] [count] [force]"""
import json
import math
import os
import sys

import bpy
from mathutils import Vector

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
VIS = os.path.join(ROOT, "Saved", "LevelGen", "visual")
RES = 320
args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
first = int(args[0]) if args else 0
count = int(args[1]) if len(args) > 1 else 100000
FORCE = "force" in args                        # re-render meshes already rendered
index = json.load(open(os.path.join(VIS, "meshes.json")))[first:first + count]

scene = bpy.context.scene
scene.render.engine = "BLENDER_WORKBENCH"
scene.render.resolution_x = scene.render.resolution_y = RES
scene.render.film_transparent = False
scene.display.shading.light = "FLAT"          # true texture colour (studio light left the sides near black)
scene.display.shading.color_type = "TEXTURE"
scene.display.shading.show_shadows = True      # shape comes from the shadow and the cavity shading
scene.display.shading.shadow_intensity = 0.6
scene.display.light_direction = (0.4, 0.3, 0.87)
scene.display.shading.show_cavity = True
scene.display.shading.cavity_type = "BOTH"
scene.display.shading.cavity_ridge_factor = 1.5
scene.display.shading.cavity_valley_factor = 1.5
scene.display.shading.show_object_outline = True
scene.display.shading.background_type = "VIEWPORT"
scene.display.shading.background_color = (0.32, 0.34, 0.37)
scene.view_settings.view_transform = "Standard"
scene.render.image_settings.file_format = "PNG"
cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
cam = bpy.data.objects.new("Cam", cam_data)
scene.collection.objects.link(cam)
scene.camera = cam
VIEWS = {"a": Vector((-1, 1, 0.8)), "b": Vector((1, -1, 0.8)), "t": Vector((0, 0, 1))}   # Blender dirs, see above
images = {}


def image(name):
    if name not in images:
        p = os.path.join(VIS, "tex", name)
        img = bpy.data.images.load(p) if os.path.exists(p) else None
        if img is not None and max(img.size) > 512:
            img.scale(512, max(1, int(512 * img.size[1] / img.size[0])))
        images[name] = img
    return images[name]


def texture(mat, img):
    mat.use_nodes = True
    nt = mat.node_tree
    for n in list(nt.nodes):
        if n.type == "TEX_IMAGE":
            nt.nodes.remove(n)
    if img is None:
        return
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = img
    nt.nodes.active = tex


done = 0
for e in index:
    out = os.path.join(VIS, "renders", e["group"])
    os.makedirs(out, exist_ok=True)
    if not e["ok"] or (not FORCE and os.path.exists(os.path.join(out, e["name"] + "_t.png"))):
        continue
    for o in [o for o in scene.objects if o.type != "CAMERA"]:
        bpy.data.objects.remove(o, do_unlink=True)
    for m in list(bpy.data.meshes) + list(bpy.data.materials):
        if m.users == 0:
            (bpy.data.meshes if isinstance(m, bpy.types.Mesh) else bpy.data.materials).remove(m)
    try:
        bpy.ops.import_scene.fbx(filepath=os.path.join(VIS, e["fbx"]))
    except Exception as ex:
        print("[RENDER] %s import failed: %s" % (e["name"], ex))
        continue
    objs = [o for o in scene.objects if o.type == "MESH"]
    if not objs:
        continue
    # Slots in order: the FBX keeps UE's slot order, and each object's material list follows it.
    for o in objs:
        for i, ms in enumerate(o.material_slots):
            if ms.material is not None and i < len(e["slots"]):
                texture(ms.material, image(e["slots"][i]["tex"]) if e["slots"][i]["tex"] else None)
    pts = [o.matrix_world @ Vector(c) for o in objs for c in o.bound_box]
    lo = Vector((min(p.x for p in pts), min(p.y for p in pts), min(p.z for p in pts)))
    hi = Vector((max(p.x for p in pts), max(p.y for p in pts), max(p.z for p in pts)))
    centre, radius = (lo + hi) / 2, max((hi - lo).length / 2, 0.01)
    for v, d in VIEWS.items():
        d = d.normalized()
        cam.location = centre + d * radius * 4
        # Straight down, image up = Blender +X (UE +X), right = Blender -Y (UE +Y).
        cam.rotation_euler = (0, 0, math.radians(-90)) if v == "t" else (-d).to_track_quat("-Z", "Y").to_euler()
        cam_data.ortho_scale = radius * 2.1
        cam_data.clip_end = radius * 10
        scene.render.filepath = os.path.join(out, "%s_%s.png" % (e["name"], v))
        bpy.ops.render.render(write_still=True)
    done += 1
    print("[RENDER] %s" % e["name"])
print("[RENDER] rendered %d" % done)
