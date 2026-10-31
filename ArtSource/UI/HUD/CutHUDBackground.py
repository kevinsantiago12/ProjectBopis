# Crops GPT's HUD background layer (Src_GPT_HUDBackground.webp, black ink on real transparency)
# to its ink and upscales it, for the bottom-left HUD section.
#   blender --background --factory-startup --python CutHUDBackground.py -- <source> <out dir>
# Writes T_HUD_Background.png: the source cropped to everything with alpha > CROP_ALPHA plus PAD px,
# then (if UPSCALE > 1) Lanczos on premultiplied colour (as CutHUDSheet.py), so soft edges keep no
# fringe. Import with BC7 compression: unlike the bar tiles it's big, and soft ink compresses well.
import bpy, sys, os
import numpy as np

src, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]
CROP_ALPHA = 0.02
PAD = 6
# 1 for now: the source (~1940 px of ink) is already wider than the layer ever shows (~570 px at
# 1080p, ~1140 at 4K), and a 4x copy would be ~55 MB uncompressed. Sides are padded to a multiple
# of 4 so the texture can take block compression (BC7).
UPSCALE = 1

img = bpy.data.images.load(src)
w, h = img.size
px = np.empty(w * h * 4, np.float32)
img.pixels.foreach_get(px)
rgba = px.reshape(h, w, 4)[::-1].astype(np.float64)

ys, xs = np.where(rgba[..., 3] > CROP_ALPHA)
y0, y1 = max(ys.min() - PAD, 0), min(ys.max() + PAD + 1, h)
x0, x1 = max(xs.min() - PAD, 0), min(xs.max() + PAD + 1, w)
crop = rgba[y0:y1, x0:x1]
# Transparent padding up to a multiple of 4 on each side, split evenly.
ph, pw = (-crop.shape[0]) % 4, (-crop.shape[1]) % 4
crop = np.pad(crop, ((ph // 2, ph - ph // 2), (pw // 2, pw - pw // 2), (0, 0)))
print(f"[bg] crop x {x0}..{x1 - 1}, y {y0}..{y1 - 1} of {w}x{h} -> {x1 - x0}x{y1 - y0}")


def resize_matrix(n, scale, a=3):
    m = n * scale
    wts = np.zeros((m, n))
    for i in range(m):
        x = (i + 0.5) / scale - 0.5
        for k in range(int(np.floor(x)) - a + 1, int(np.floor(x)) + a + 1):
            t = x - k
            wts[i, min(max(k, 0), n - 1)] += np.sinc(t) * np.sinc(t / a) if abs(t) < a else 0.0
    return wts / wts.sum(1, keepdims=True)


pre = np.concatenate([crop[..., :3] * crop[..., 3:4], crop[..., 3:4]], -1)
big = np.einsum("ij,jkc->ikc", resize_matrix(pre.shape[0], UPSCALE), pre)
big = np.einsum("kj,ijc->ikc", resize_matrix(pre.shape[1], UPSCALE), big)
a = np.clip(big[..., 3:4], 0, 1)
rgb = np.clip(big[..., :3] / np.maximum(a, 1e-4), 0, 1) * (a > 1e-4)
out = np.concatenate([rgb, a], -1)

hh, ww = out.shape[:2]
o = bpy.data.images.new("o", ww, hh, alpha=True)
o.pixels.foreach_set(np.ascontiguousarray(out[::-1]).astype(np.float32).ravel())
path = os.path.join(out_dir, "T_HUD_Background.png")
o.filepath_raw = path
o.file_format = "PNG"
o.save()
print(f"[bg] wrote {os.path.basename(path)} ({ww}x{hh}, aspect {ww / hh:.3f})")
