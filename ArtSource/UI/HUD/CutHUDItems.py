# Cuts the first-aid and grenade icons out of GPT's item-strip mockup (Src_GPT_HUDItems.webp:
# white pistol | "15 / 90" | divider | kit "3" | divider | grenade "2", on black).
#   blender --background --factory-startup --python CutHUDItems.py -- <source> <out dir>
# The strip is found by columns: every run of columns holding ink is one piece, printed with its
# box (the layout numbers in the spec come from this). The kit and the grenade are written as
# white on alpha, alpha = brightness / the piece's peak, so the black cross and grenade grooves
# come out as holes. The pistol is left out: the HUD shows the equipped weapon's own icon.
import bpy, sys, os
import numpy as np

src, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]
INK = 0.25      # brightness counted as ink when finding the pieces
MERGE = 4       # runs closer than this many columns are one piece (anti-aliasing gaps)
PAD = 4
# Piece order in the mockup -> output name (None: not written).
NAMES = ["pistol", "1", "5", "/", "9", "0", "divider", "T_HUD_Icon_FirstAid", "3", "divider",
         "T_HUD_Icon_Grenade", "2"]

img = bpy.data.images.load(src)
w, h = img.size
px = np.empty(w * h * 4, np.float32)
img.pixels.foreach_get(px)
lum = px.reshape(h, w, 4)[::-1][..., :3].mean(-1).astype(np.float64)

cols = (lum > INK).any(0)
runs, x = [], 0
while x < w:
    if cols[x]:
        x0 = x
        while x < w and cols[x]:
            x += 1
        if runs and x0 - runs[-1][1] - 1 < MERGE:
            runs[-1] = (runs[-1][0], x - 1)
        else:
            runs.append((x0, x - 1))
    else:
        x += 1

for i, (x0, x1) in enumerate(runs):
    rows = np.where((lum[:, x0:x1 + 1] > INK).any(1))[0]
    y0, y1 = rows.min(), rows.max()
    name = NAMES[i] if i < len(NAMES) else "?"
    print(f"[items] {name:22s} x {x0:4d}-{x1:4d} ({x1 - x0 + 1:3d})  y {y0:3d}-{y1:3d} ({y1 - y0 + 1:3d})")
    if not name.startswith("T_"):
        continue
    crop = lum[max(y0 - PAD, 0):y1 + PAD + 1, max(x0 - PAD, 0):x1 + PAD + 1]
    # Transparent padding up to a multiple of 4 on each side, split evenly.
    ph, pw = (-crop.shape[0]) % 4, (-crop.shape[1]) % 4
    crop = np.pad(crop, ((ph // 2, ph - ph // 2), (pw // 2, pw - pw // 2)))
    alpha = np.clip(crop / np.percentile(crop[crop > INK], 90), 0, 1)
    out = np.concatenate([np.ones(crop.shape + (3,)), alpha[..., None]], -1)
    hh, ww = out.shape[:2]
    o = bpy.data.images.new(name, ww, hh, alpha=True)
    o.pixels.foreach_set(np.ascontiguousarray(out[::-1]).astype(np.float32).ravel())
    o.filepath_raw = os.path.join(out_dir, name + ".png")
    o.file_format = "PNG"
    o.save()
    print(f"[items]   wrote {name}.png ({ww}x{hh})")
