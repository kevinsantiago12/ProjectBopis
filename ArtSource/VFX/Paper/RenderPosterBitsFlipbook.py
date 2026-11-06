# Renders torn scraps of the posters tumbling, as one seamless loop, and packs them into a flipbook for NS_ImpactPosterBits.
# User, 2026-11-06: "I want bits of the poster, not actual paper. We can have 2 variations, one is for actualy stacks of paper and another for just bits".
#   blender --background --factory-startup --python RenderPosterBitsFlipbook.py -- <poster image dir> <out dir>
# The poster images come from ExportPosterImages_ue.py. They're only read, and each scrap is a crop of one. Writes T_ImpactPosterBits.png
# (GRID x GRID frames, read left to right, top to bottom) and contact.png (the same over grey, to look at).
#
# - 8 x 8 and the same frame rate as NS_ImpactPaper, so a copy of that effect only needs its size and counts changed.
# - The flipbook module plays one range for every particle, so it can't hold one scrap per particle. Instead each scrap has FRAMES_EACH frames, one
#   whole turn from edge-on to edge-on, and the next scrap takes over at that sliver. At this size nobody sees the swap, and a sheet of them in the air reads as many scraps.
# - The front is the print, torn to white at the edge. The back is plain paper. As with T_ImpactPaper the material is unlit, so the shading is baked.
# - Colour runs out past the scrap's edge into the transparent part, so mips don't pull a dark rim in, and each frame keeps an empty margin.
import bmesh
import bpy
import glob
import math
import numpy as np
import os
import random
import sys
from mathutils import Matrix, Vector

GRID = 8
CELL = 128              # pixels per frame in the final sheet
SUPER = 2               # rendered this much larger, then averaged down
FRAMES_EACH = 16        # frames per scrap: one turn. GRID * GRID must divide by it
FRAME_SIZE = 2.35       # across one frame, for a scrap whose longest reach from its middle is 1
CROP = (0.16, 0.30)     # a scrap's width as a fraction of the poster's width
RIM = 0.10              # how far in from the torn edge the white goes, as a fraction of the radius
BEND = 0.20             # how far a scrap curls, as a fraction of its radius
PAPER = (0.86, 0.85, 0.80)
BACK = (0.72, 0.71, 0.67)
RINGS = (0.45, 0.78, 0.90, 1.0)
SIDES = 40

args = sys.argv[sys.argv.index("--") + 1:]
image_dir, out_dir = args[:2]
os.makedirs(out_dir, exist_ok=True)
FRAMES = GRID * GRID
SCRAPS = FRAMES // FRAMES_EACH
RES = CELL * SUPER
rng = random.Random(1289)

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
paths = sorted(glob.glob(os.path.join(image_dir, "*.png")))
if not paths:
    raise RuntimeError("no poster images in " + image_dir)


def pick_crop(im, wid_frac):
    """A patch of the image with some colour in it, as (u0, v0, du, dv): a scrap of plain background reads as nothing."""
    w, h = im.size
    px = np.empty(w * h * im.channels, dtype=np.float32)
    im.pixels.foreach_get(px)
    px = px.reshape(h, w, im.channels)[:, :, :3]
    du = wid_frac
    dv = wid_frac * w / float(h)
    best, best_score = (0.5 - du / 2, 0.5 - dv / 2), -1.0
    for _ in range(30):
        u0, v0 = rng.uniform(0.02, 0.98 - du), rng.uniform(0.02, 0.98 - dv)
        x0, x1 = int(u0 * w), max(int((u0 + du) * w), int(u0 * w) + 2)
        y0, y1 = int(v0 * h), max(int((v0 + dv) * h), int(v0 * h) + 2)
        patch = px[y0:y1, x0:x1]
        sat = float((patch.max(axis=2) - patch.min(axis=2)).mean())
        contrast = float(patch.mean(axis=2).std())
        lum = float(patch.mean())
        score = sat + contrast - (0.3 if lum < 0.12 else 0.0)
        if score > best_score:
            best, best_score = (u0, v0), score
    return best[0], best[1], du, dv


def torn_outline():
    """Radius by angle: a lumpy shape, stretched, with small tears on top. Scaled so its longest reach is 1."""
    a1, a2, a3 = [rng.uniform(0, 2 * math.pi) for _ in range(3)]
    k1, k2 = rng.uniform(0.15, 0.3), rng.uniform(0.08, 0.2)
    stretch, lean = rng.uniform(1.0, 1.7), rng.uniform(0, math.pi)
    out = []
    for i in range(SIDES):
        t = 2 * math.pi * i / SIDES
        r = 1.0 + k1 * math.sin(2 * t + a1) + k2 * math.sin(3 * t + a2) + 0.06 * math.sin(7 * t + a3) + rng.uniform(-0.07, 0.07)
        x, y = r * math.cos(t) * stretch, r * math.sin(t)
        c, s = math.cos(lean), math.sin(lean)
        out.append((x * c - y * s, x * s + y * c))
    top = max(math.hypot(*p) for p in out)
    return [(x / top, y / top) for x, y in out]


POSTERS = rng.sample(paths, min(len(paths), SCRAPS))     # a different poster for each scrap


def make_scrap(index):
    im = bpy.data.images.load(POSTERS[index % len(POSTERS)])
    im.colorspace_settings.name = 'sRGB'
    u0, v0, du, dv = pick_crop(im, rng.uniform(*CROP))
    mat = bpy.data.materials.new("scrap%d" % index)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = nt.nodes["Principled BSDF"]
    bsdf.inputs["Roughness"].default_value = 0.85
    tex = nt.nodes.new("ShaderNodeTexImage")
    tex.image = im
    tex.extension = 'CLIP'
    rim = nt.nodes.new("ShaderNodeVertexColor")
    rim.layer_name = "rim"
    to_white = nt.nodes.new("ShaderNodeMixRGB")
    to_white.inputs[2].default_value = (*PAPER, 1)
    nt.links.new(rim.outputs["Color"], to_white.inputs[0])
    nt.links.new(tex.outputs["Color"], to_white.inputs[1])
    geo = nt.nodes.new("ShaderNodeNewGeometry")
    side = nt.nodes.new("ShaderNodeMixRGB")
    side.inputs[2].default_value = (*BACK, 1)
    nt.links.new(geo.outputs["Backfacing"], side.inputs[0])
    nt.links.new(to_white.outputs[0], side.inputs[1])
    nt.links.new(side.outputs[0], bsdf.inputs["Base Color"])

    outline = torn_outline()
    mesh = bpy.data.meshes.new("scrap%d" % index)
    bm = bmesh.new()
    uv = bm.loops.layers.uv.new("UVMap")
    rim_layer = bm.loops.layers.color.new("rim")
    middle = bm.verts.new((0.0, 0.0, 0.0))
    rings = [[bm.verts.new((x * k, y * k, 0.0)) for x, y in outline] for k in RINGS]

    def rim_of(v):
        # 0 well inside; 1 at the torn edge, by how far along the way out this vertex is, with its jag.
        k = next((RINGS[i] for i, ring in enumerate(rings) if v in ring), 0.0)
        return max(0.0, min(1.0, (k - (1.0 - RIM * 2.2)) / (RIM * 2.2)))

    def uv_of(v):
        return (u0 + du * (v.co.x + 1.0) / 2.0, v0 + dv * (v.co.y + 1.0) / 2.0)

    faces = []
    for i in range(SIDES):
        j = (i + 1) % SIDES
        faces.append(bm.faces.new((middle, rings[0][i], rings[0][j])))
        for a, b in zip(rings, rings[1:]):
            faces.append(bm.faces.new((a[i], b[i], b[j], a[j])))
    for f in faces:
        f.smooth = True
        for loop in f.loops:
            loop[uv].uv = uv_of(loop.vert)
            k = rim_of(loop.vert)
            loop[rim_layer] = (k, k, k, 1.0)
    bm.to_mesh(mesh)
    bm.free()
    mesh.materials.append(mat)
    ob = bpy.data.objects.new("scrap%d" % index, mesh)
    scene.collection.objects.link(ob)
    ob.hide_render = True
    rest = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
    mesh.vertices.foreach_get("co", rest)
    return {"ob": ob, "rest": rest.reshape(-1, 3), "roll": rng.uniform(0, 2 * math.pi), "axis": rng.uniform(-0.6, 0.6), "curl": rng.uniform(0.6, 1.0) * rng.choice((-1, 1)), "image": os.path.basename(im.filepath)}


scraps = [make_scrap(i) for i in range(SCRAPS)]
print("SCRAPS", [s["image"] for s in scraps])

# Looks along +Y, with Z up in the picture.
cam_data = bpy.data.cameras.new("cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = FRAME_SIZE
cam = bpy.data.objects.new("cam", cam_data)
cam.location = (0, -5, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

# The same soft daylight as T_ImpactPaper, so both sit together.
sun = bpy.data.objects.new("sun", bpy.data.lights.new("sun", 'SUN'))
sun.data.energy = 1.9
sun.data.angle = math.radians(25)
sun.rotation_euler = (math.radians(38), math.radians(-18), 0)
scene.collection.objects.link(sun)
world = bpy.data.worlds.new("w")
world.use_nodes = True
world.node_tree.nodes["Background"].inputs[0].default_value = (1, 1, 1, 1)
world.node_tree.nodes["Background"].inputs[1].default_value = 0.42
scene.world = world

r = scene.render
r.engine = 'CYCLES'
scene.cycles.device = 'CPU'
scene.cycles.samples = 32
scene.cycles.use_denoising = False
scene.cycles.max_bounces = 3
r.film_transparent = True
r.resolution_x = r.resolution_y = RES
r.image_settings.file_format = 'PNG'
r.image_settings.color_mode = 'RGBA'
r.image_settings.color_depth = '8'
scene.view_settings.view_transform = 'Standard'
scene.view_settings.look = 'None'
frame_dir = os.path.join(out_dir, "frames")
os.makedirs(frame_dir, exist_ok=True)

for i in range(FRAMES):
    s = scraps[i // FRAMES_EACH]
    t = (i % FRAMES_EACH) / FRAMES_EACH
    ob = s["ob"]
    for other in scraps:
        other["ob"].hide_render = other is not s
    # The flex: a curl that changes side twice a turn, so it's back where it began at the swap.
    co = s["rest"].copy()
    co[:, 2] = BEND * s["curl"] * math.sin(4 * math.pi * t + 0.7) * (co[:, 1] ** 2 - 0.33) + 0.06 * s["curl"] * co[:, 0] * co[:, 1]
    ob.data.vertices.foreach_set("co", co.ravel())
    ob.data.update()
    # One turn about an axis in the picture plane, so the scrap is exactly edge-on where one hands over to the next.
    axis = Vector((math.cos(s["axis"]), 0.0, math.sin(s["axis"])))
    ob.matrix_world = Matrix.Rotation(2 * math.pi * t, 4, axis) @ Matrix.Rotation(s["roll"], 4, Vector((0.0, 0.0, 1.0)))
    r.filepath = os.path.join(frame_dir, "f%02d.png" % i)
    bpy.ops.render.render(write_still=True)


def load(path):
    im = bpy.data.images.load(path)
    w, h = im.size
    a = np.empty(w * h * 4, dtype=np.float32)
    im.pixels.foreach_get(a)
    bpy.data.images.remove(im)
    return a.reshape(h, w, 4)[::-1]     # top row first


def save(arr, path):
    h, w = arr.shape[:2]
    im = bpy.data.images.new("o", w, h, alpha=True)
    im.pixels.foreach_set(arr[::-1].ravel())
    im.filepath_raw = path
    im.file_format = 'PNG'
    im.save()
    bpy.data.images.remove(im)


def down(x):
    return x.reshape(CELL, SUPER, CELL, SUPER, x.shape[2]).mean(axis=(1, 3))


size = GRID * CELL
sheet_px = np.zeros((size, size, 4), dtype=np.float32)
fill = np.array(PAPER, dtype=np.float32) * 0.8
smallest = CELL
for i in range(FRAMES):
    a = load(os.path.join(frame_dir, "f%02d.png" % i))
    al = a[:, :, 3:4]
    al2, col2 = down(al), down(a[:, :, :3] * al)
    rgb = np.where(al2 > 1e-4, col2 / np.maximum(al2, 1e-4), fill)
    known = al2[:, :, 0] > 1e-4
    for _ in range(6):
        grown = np.zeros_like(rgb)
        n = np.zeros(known.shape, dtype=np.float32)
        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
            k = np.roll(np.roll(known, dy, 0), dx, 1)
            grown += np.roll(np.roll(rgb, dy, 0), dx, 1) * k[:, :, None]
            n += k
        new = (~known) & (n > 0)
        rgb[new] = grown[new] / n[new][:, None]
        known = known | new
    ys, xs = np.nonzero(al2[:, :, 0] > 0.01)
    if len(xs):
        smallest = min(smallest, int(xs.min()), int(ys.min()), CELL - 1 - int(xs.max()), CELL - 1 - int(ys.max()))
    row, column = i // GRID, i % GRID
    sheet_px[row * CELL:(row + 1) * CELL, column * CELL:(column + 1) * CELL, :3] = rgb
    sheet_px[row * CELL:(row + 1) * CELL, column * CELL:(column + 1) * CELL, 3] = al2[:, :, 0]

save(sheet_px, os.path.join(out_dir, "T_ImpactPosterBits.png"))
bg = 0.25
contact = sheet_px.copy()
contact[:, :, :3] = sheet_px[:, :, :3] * sheet_px[:, :, 3:4] + bg * (1 - sheet_px[:, :, 3:4])
contact[:, :, 3] = 1
save(contact, os.path.join(out_dir, "contact.png"))
print("SMALLEST MARGIN %d px" % smallest)
print("DONE", size, "x", size)
