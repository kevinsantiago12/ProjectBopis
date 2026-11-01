# Makes a HUD icon from a white-on-transparent PNG: crops it to its ink plus PAD px, scales it to
# HEIGHT px tall and pads the sides to multiples of 4 (transparent), so it imports like the other
# T_HUD_Icon_* textures (with mipmaps).
#   blender --background --factory-startup --python CutHUDIcon.py -- <source> <out png> [height]
# Used for T_HUD_Icon_Melee from ArtSource/UI/Weapons/bopis-fist-reference-2048.png (the user's
# fist, 2048 square with wide margins).
import bpy, sys
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
src, out_path = args[:2]
HEIGHT = int(args[2]) if len(args) > 2 else 256
CROP_ALPHA = 0.02
PAD = 8

img = bpy.data.images.load(src)
w, h = img.size
px = np.empty(w * h * 4, np.float32)
img.pixels.foreach_get(px)
rgba = px.reshape(h, w, 4)   # bottom row first, as Blender stores it

ys, xs = np.where(rgba[..., 3] > CROP_ALPHA)
y0, y1 = max(ys.min() - PAD, 0), min(ys.max() + PAD + 1, h)
x0, x1 = max(xs.min() - PAD, 0), min(xs.max() + PAD + 1, w)
crop = np.ascontiguousarray(rgba[y0:y1, x0:x1])
ch, cw = crop.shape[:2]

# Scale on premultiplied colour so the edges keep no dark fringe; Blender's scale box-filters down.
pre = crop.copy()
pre[..., :3] *= pre[..., 3:4]
tmp = bpy.data.images.new("tmp", cw, ch, alpha=True, float_buffer=True)
tmp.pixels.foreach_set(pre.ravel())
nw, nh = max(1, round(cw * HEIGHT / ch)), HEIGHT
tmp.scale(nw, nh)
small = np.empty(nw * nh * 4, np.float32)
tmp.pixels.foreach_get(small)
small = small.reshape(nh, nw, 4)
a = np.clip(small[..., 3:4], 0, 1)
small = np.concatenate([np.clip(small[..., :3] / np.maximum(a, 1e-4), 0, 1) * (a > 1e-4), a], -1)

# Transparent padding up to a multiple of 4 on each side, split evenly.
ph, pw = (-nh) % 4, (-nw) % 4
small = np.pad(small, ((ph // 2, ph - ph // 2), (pw // 2, pw - pw // 2), (0, 0)))
oh, ow = small.shape[:2]
o = bpy.data.images.new("o", ow, oh, alpha=True)
o.pixels.foreach_set(np.ascontiguousarray(small).astype(np.float32).ravel())
o.filepath_raw = out_path
o.file_format = "PNG"
o.save()
print(f"[icon] ink {x1 - x0}x{y1 - y0} of {w}x{h} -> {out_path.split('/')[-1]} {ow}x{oh}")
