# Renders a sheet of paper tumbling as it falls, as one seamless loop, and packs it into a flipbook for NS_ImpactPaper.
# User, 2026-11-06: "I want slowly dropping paper like in John Woo films."
#   blender --background --factory-startup --python RenderPaperFlipbook.py -- <out dir>
# Writes T_ImpactPaper.png (GRID x GRID frames, read left to right, top to bottom) and contact.png (the same over grey, to look at).
#
# - The sprite always faces the camera, so the tumble has to be in the picture. The sheet never goes fully edge-on (TILT), because a sprite
#   that thins to nothing reads as a flicker rather than a turn.
# - The rates are whole numbers of cycles, so the last frame runs back into the first. Three turns and a slower wander keep one turn from
#   looking like the last.
# - 64 frames, not 16: Focus runs at 0.3x, and at 16 frames a sheet would visibly step from pose to pose.
# - The game's material is unlit, so the shading is baked: the sheet brightens and greys as it turns. The back is a little greyer than the front.
# - Colour runs out past the sheet's edge into the transparent part, so mips don't pull a dark rim in, and each frame keeps an empty margin so
#   mips don't bleed between frames.
import bmesh
import bpy
import math
import numpy as np
import os
import random
import sys
from mathutils import Matrix, Vector

GRID = 8
CELL = 128              # pixels per frame in the final sheet
SUPER = 2               # rendered this much larger, then averaged down
TURNS = 3               # whole turns over the loop
WANDER_CYCLES = 2       # whole cycles of the axis wandering
BEND_CYCLES = 5         # whole cycles of the sheet flexing
TILT = math.radians(24) # the turning axis leans this far out of the picture plane, so the sheet never goes edge-on
BEND = 0.34             # how far the sheet curls, as a fraction of its height
SHEET_W, SHEET_H = 0.21, 0.297  # A4, metres
FRAME_SIZE = 0.46       # metres across one frame: the sheet's diagonal is 0.364 and the curl reaches further, and this leaves an empty margin
PAPER = (0.86, 0.85, 0.80)
BACK = (0.70, 0.69, 0.65)
INK = (0.13, 0.13, 0.14)

out_dir = sys.argv[sys.argv.index("--") + 1]
os.makedirs(out_dir, exist_ok=True)
FRAMES = GRID * GRID
RES = CELL * SUPER

bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene

# The page: typed lines under a heading, drawn into an image.
PAGE_W, PAGE_H = 420, 594
rng = random.Random(1289)
page = np.ones((PAGE_H, PAGE_W, 4), dtype=np.float32)
page[:, :, :3] = PAPER


def ink_line(y, x0, x1, h, weight):
    for x in range(x0, x1):
        if rng.random() < 0.92:
            page[y:y + h, x, :3] = np.array(PAPER) * (1 - weight) + np.array(INK) * weight


ink_line(50, 42, 210, 7, 0.9)
y = 92
while y < PAGE_H - 50:
    if rng.random() < 0.12:
        y += 16
        continue
    # Word by word, so a line reads as type and not as a ruled bar.
    x = 42
    end = PAGE_W - 42 - (rng.randint(0, 120) if rng.random() < 0.2 else 0)
    while x < end:
        w = rng.randint(10, 38)
        ink_line(y, x, min(x + w, end), 4, 0.72)
        x += w + 7
    y += 16
img = bpy.data.images.new("page", PAGE_W, PAGE_H, alpha=True)
img.pixels.foreach_set(page[::-1].ravel())   # Blender's rows run bottom-up
img.update()

mat = bpy.data.materials.new("paper")
mat.use_nodes = True
nt = mat.node_tree
bsdf = nt.nodes["Principled BSDF"]
bsdf.inputs["Roughness"].default_value = 0.85
tex = nt.nodes.new("ShaderNodeTexImage")
tex.image = img
tex.interpolation = 'Cubic'
geo = nt.nodes.new("ShaderNodeNewGeometry")
mix = nt.nodes.new("ShaderNodeMixRGB")
mix.inputs[2].default_value = (*BACK, 1)
nt.links.new(geo.outputs["Backfacing"], mix.inputs[0])
nt.links.new(tex.outputs["Color"], mix.inputs[1])
nt.links.new(mix.outputs[0], bsdf.inputs["Base Color"])

# A grid the size of the sheet, flexed in the frame loop below.
COLS, ROWS = 14, 20
mesh = bpy.data.meshes.new("sheet")
bm = bmesh.new()
uv_layer = bm.loops.layers.uv.new("UVMap")
verts = [[bm.verts.new(((c / COLS - 0.5) * SHEET_W, (r / ROWS - 0.5) * SHEET_H, 0)) for c in range(COLS + 1)] for r in range(ROWS + 1)]
for r_i in range(ROWS):
    for c in range(COLS):
        f = bm.faces.new((verts[r_i][c], verts[r_i][c + 1], verts[r_i + 1][c + 1], verts[r_i + 1][c]))
        f.smooth = True
        for loop, (u, v) in zip(f.loops, ((c, r_i), (c + 1, r_i), (c + 1, r_i + 1), (c, r_i + 1))):
            loop[uv_layer].uv = (u / COLS, v / ROWS)
bm.to_mesh(mesh)
bm.free()
mesh.materials.append(mat)
sheet = bpy.data.objects.new("sheet", mesh)
scene.collection.objects.link(sheet)
rest = np.empty(len(mesh.vertices) * 3, dtype=np.float32)
mesh.vertices.foreach_get("co", rest)
rest = rest.reshape(-1, 3)

# Looks along +Y, with Z up in the picture and the sheet turning in the middle.
cam_data = bpy.data.cameras.new("cam")
cam_data.type = 'ORTHO'
cam_data.ortho_scale = FRAME_SIZE
cam = bpy.data.objects.new("cam", cam_data)
cam.location = (0, -1, 0)
cam.rotation_euler = (math.radians(90), 0, 0)
scene.collection.objects.link(cam)
scene.camera = cam

# Soft daylight from above, so a sheet is brightest tilted up and greys as it turns away. Baked, because the material can't do it.
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
    t = i / FRAMES
    # The flex: a curl along the height whose bow changes side, with a gentler twist across the width.
    co = rest.copy()
    curl = BEND * SHEET_H * math.sin(2 * math.pi * BEND_CYCLES * t)
    twist = 0.35 * BEND * SHEET_H * math.sin(2 * math.pi * (BEND_CYCLES - 2) * t + 1.1)
    ny, nx = co[:, 1] / (SHEET_H / 2), co[:, 0] / (SHEET_W / 2)
    co[:, 2] = curl * (ny * ny - 0.33) + twist * nx * ny
    mesh.vertices.foreach_set("co", co.ravel())
    mesh.update()
    # The turn: about an axis in the picture plane that wanders, then leaned towards the camera. A sheet turning about an axis that leans
    # by TILT shows at least sin(TILT) of its face.
    wander = math.radians(32) * math.sin(2 * math.pi * WANDER_CYCLES * t)
    axis = Vector((math.cos(wander), 0.0, math.sin(wander))).normalized()
    lean = Matrix.Rotation(TILT, 4, Vector((0.0, 0.0, 1.0)))
    turn = Matrix.Rotation(2 * math.pi * TURNS * t, 4, axis)
    sheet.matrix_world = lean @ turn
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
fill = np.array(PAPER, dtype=np.float32) * 0.8      # the colour under the transparent parts
min_cov, max_cov, edge = 1.0, 0.0, 0.0
for i in range(FRAMES):
    a = load(os.path.join(frame_dir, "f%02d.png" % i))
    # Down to size, averaging colour by coverage so the edge stays clean.
    al = a[:, :, 3:4]
    al2, col2 = down(al), down(a[:, :, :3] * al)
    rgb = np.where(al2 > 1e-4, col2 / np.maximum(al2, 1e-4), fill)
    # The sheet's colour bleeds outward a few steps, then the flat fill beyond.
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
    cov = float((al2 > 0.5).mean())
    min_cov, max_cov = min(min_cov, cov), max(max_cov, cov)
    border = np.concatenate([al2[0:4].ravel(), al2[-4:].ravel(), al2[:, 0:4].ravel(), al2[:, -4:].ravel()])
    edge = max(edge, float(border.max()))
    row, column = i // GRID, i % GRID
    sheet_px[row * CELL:(row + 1) * CELL, column * CELL:(column + 1) * CELL, :3] = rgb
    sheet_px[row * CELL:(row + 1) * CELL, column * CELL:(column + 1) * CELL, 3] = al2[:, :, 0]

save(sheet_px, os.path.join(out_dir, "T_ImpactPaper.png"))
bg = 0.25
contact = sheet_px.copy()
contact[:, :, :3] = sheet_px[:, :, :3] * sheet_px[:, :, 3:4] + bg * (1 - sheet_px[:, :, 3:4])
contact[:, :, 3] = 1
save(contact, os.path.join(out_dir, "contact.png"))
print("COVERAGE min %.3f max %.3f; alpha in the 4px margin %.3f" % (min_cov, max_cov, edge))
print("DONE", size, "x", size)
