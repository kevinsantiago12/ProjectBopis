# Cuts the HUD pieces out of the GPT sheet (Src_GPT_HUDSheet.png) for the length-independent bar.
#   blender --background --factory-startup --python CutHUDSheet.py -- <sheet.png> <out dir> [preview.png]
#
# The sheet is flat art on a near-black background, laid out left to right as:
#   composite (reference only) | HEALTH | FOCUS | ACCENT | EMPTY
# Writes:
#   T_HUD_BarTile_Health/Focus/Empty.png  a seamless horizontal tile cut from each bar's straight
#       middle (the slanted ends are left out; M_HUDBar draws them, so a bar can be any length
#       without stretching). Full bar height, solid inside, so the grunge specks stay black print.
#   T_HUD_Accent.png  the white/gold slashes, keyed off the background, stray specks removed.
# All saved at UPSCALE x the sheet's resolution (Lanczos, wrapped horizontally for the tiles).
# Prints each bar's end slopes and outline colour (for M_HUDBar), and the composite's layout.
# With a preview path, also renders bars at several lengths and fills through the same maths
# the material uses, as a check.
import bpy, sys, os
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
src, out_dir = args[0], args[1]
preview = args[2] if len(args) > 2 else None
KEY_LO, KEY_HI = 0.03, 0.12      # distance from the background: fully clear .. fully solid
XFADE = 24                       # columns cross-faded to make the tile seamless
END_MARGIN = 3                   # columns kept clear of the slanted ends when cutting the tile
SLOPE = 1.0                      # one end slope for every bar (45 deg); M_HUDBar's default
UPSCALE = 4                      # saved textures are this many times the sheet's pixels (Lanczos),
                                 # so Unreal only ever shrinks them, up to 4K; aspects don't change
LAYOUT_HEALTH_H = 29             # the health bar's on-screen height at 1080p; layout is scaled to it
NAMES = ["Composite", "Health", "Focus", "Accent", "Empty"]

img = bpy.data.images.load(src)
W, H = img.size
px = np.empty(W * H * 4, np.float32)
img.pixels.foreach_get(px)
rgb = px.reshape(H, W, 4)[::-1, :, :3].astype(np.float64)
BG = np.median(rgb.reshape(-1, 3), 0)


def save(path, rgba):
    hh, ww = rgba.shape[:2]
    o = bpy.data.images.new("o", ww, hh, alpha=True)
    o.pixels.foreach_set(np.ascontiguousarray(rgba[::-1]).astype(np.float32).ravel())
    o.filepath_raw = path
    o.file_format = "PNG"
    o.save()
    bpy.data.images.remove(o)
    print(f"[cut] wrote {os.path.basename(path)} ({ww}x{hh})")


def resize_matrix(n, scale, wrap, a=3):
    """Lanczos weights mapping n source samples to n * scale; wrap keeps a tile seamless."""
    m = n * scale
    w = np.zeros((m, n))
    for i in range(m):
        x = (i + 0.5) / scale - 0.5
        for k in range(int(np.floor(x)) - a + 1, int(np.floor(x)) + a + 1):
            t = x - k
            lw = np.sinc(t) * np.sinc(t / a) if abs(t) < a else 0.0
            w[i, k % n if wrap else min(max(k, 0), n - 1)] += lw
    return w / w.sum(1, keepdims=True)


def upscale(rgba, wrap_x=False):
    """UPSCALE x Lanczos on premultiplied colour (no dark fringes at alpha edges)."""
    if UPSCALE == 1:
        return rgba
    pre = np.concatenate([rgba[..., :3] * rgba[..., 3:4], rgba[..., 3:4]], -1)
    my = resize_matrix(pre.shape[0], UPSCALE, False)
    mx = resize_matrix(pre.shape[1], UPSCALE, wrap_x)
    big = np.einsum("ij,jkc->ikc", my, pre)
    big = np.einsum("kj,ijc->ikc", mx, big)
    a = np.clip(big[..., 3:4], 0, 1)
    rgb = np.clip(big[..., :3] / np.maximum(a, 1e-4), 0, 1)
    return np.concatenate([rgb * (a > 1e-4), a], -1)


def key(crop):
    d = np.abs(crop - BG).max(-1)
    t = np.clip((d - KEY_LO) / (KEY_HI - KEY_LO), 0, 1)
    return t * t * (3 - 2 * t)


def unpremult(crop, alpha):
    return np.clip((crop - (1 - alpha[..., None]) * BG) / np.maximum(alpha[..., None], 1e-3), 0, 1)


def runs(mask):
    out, s = [], None
    for i, v in enumerate(mask):
        if v and s is None: s = i
        if not v and s is not None: out.append((s, i - 1)); s = None
    if s is not None: out.append((s, len(mask) - 1))
    return out


# Find the five pieces: column runs wider than a divider, then the biggest row run (not the label).
content = np.abs(rgb - BG).max(-1) > 0.08
pieces = {}
for name, (x0, x1) in zip(NAMES, [r for r in runs(content.any(0)) if r[1] - r[0] > 20]):
    rows = runs(content[:, x0:x1 + 1].any(1))
    y0, y1 = max(rows, key=lambda r: content[r[0]:r[1] + 1, x0:x1 + 1].sum())
    pieces[name] = (x0, x1, y0, y1)
print("[cut] pieces", pieces)


def cut_bar(name):
    x0, x1, y0, y1 = pieces[name]
    crop = rgb[y0 - 2:y1 + 3, x0 - 2:x1 + 3]
    alpha = key(crop)
    rows, lefts, rights = [], [], []
    for y in range(alpha.shape[0]):
        xs = np.where(alpha[y] > 0.5)[0]
        if len(xs) >= 2:
            rows.append(y); lefts.append(xs.min()); rights.append(xs.max())
    rows, lefts, rights = map(np.array, (rows, lefts, rights))
    k = slice(2, -2)
    kl = np.polyfit(rows[k], lefts[k], 1)[0]      # left end: x per row (positive = leans "\")
    kr = -np.polyfit(rows[k], rights[k], 1)[0]    # right end: x per row (positive = leans "/")
    top, bot = rows.min(), rows.max()
    # The straight middle: right of the left end's furthest point, left of the right end's.
    c0, c1 = lefts[k].max() + END_MARGIN, rights[k].min() - END_MARGIN
    strip_rgb = crop[top - 1:bot + 2, c0:c1 + 1]
    strip_a = key(strip_rgb)
    # Solid inside: every row between the outlines is opaque (specks stay black print, and the
    # Empty track's dark fill isn't keyed away); the anti-aliased rows outside keep their median.
    row_a = np.median(strip_a, 1)
    row_a[1:-1] = 1.0
    colour = np.where(row_a[:, None, None] > 0.98, strip_rgb,
                      unpremult(strip_rgb, np.repeat(row_a[:, None], strip_rgb.shape[1], 1)))
    a = np.repeat(row_a[:, None], strip_rgb.shape[1], 1)
    tile = np.dstack([colour, a])
    # Seamless: fold the last XFADE columns over the first ones.
    n = tile.shape[1]
    w = np.linspace(0, 1, XFADE)[None, :, None]
    tile[:, :XFADE] = tile[:, :XFADE] * w + tile[:, n - XFADE:] * (1 - w)
    tile = tile[:, :n - XFADE]
    keep = row_a > 0.02
    tile = tile[keep]
    # Outline colour: the brightest row in the top quarter (the border can sit a row or two in).
    solid = np.where(row_a > 0.9)[0]
    outline = max((colour[r].mean(0) for r in solid[:max(2, len(solid) // 4)]), key=lambda c: c.sum())
    save(os.path.join(out_dir, f"T_HUD_BarTile_{name}.png"), upscale(tile, wrap_x=True))
    print(f"[cut] {name}: bar {x1 - x0 + 1}x{bot - top + 1} px; tile {tile.shape[1]}x{tile.shape[0]}; "
          f"SlopeLeft {kl:.3f} SlopeRight {kr:.3f} (px across per px down); "
          f"OutlineColor ({outline[0]:.3f}, {outline[1]:.3f}, {outline[2]:.3f})")
    return tile, kl, kr, outline


def cut_accent():
    x0, x1, y0, y1 = pieces["Accent"]
    crop = rgb[y0 - 3:y1 + 4, x0 - 3:x1 + 4]
    alpha = key(crop)
    # Drop specks that aren't attached to the solid shape.
    core = alpha > 0.6
    grown = core.copy()
    for dy in range(-2, 3):
        for dx in range(-2, 3):
            grown |= np.roll(np.roll(core, dy, 0), dx, 1)
    alpha = alpha * grown
    rows = [y for y in range(alpha.shape[0]) if (alpha[y] > 0.5).any()]
    n = len(rows)
    for part, sel in (("white (top third)", rows[: n // 3]), ("gold (bottom third)", rows[-n // 3:])):
        lefts = [np.where(alpha[y] > 0.5)[0].min() for y in sel]
        print(f"[cut] Accent {part} left-edge slope {np.polyfit(sel, lefts, 1)[0]:.3f} px across per px down")
    accent = np.dstack([unpremult(crop, alpha), alpha])
    save(os.path.join(out_dir, "T_HUD_Accent.png"), upscale(accent))
    return accent


def layout():
    """Where things sit in the composite, relative to the accent's top-left."""
    x0, x1, y0, y1 = pieces["Composite"]
    sub = rgb[y0:y1 + 1, x0:x1 + 1]
    red = (sub[..., 0] > sub[..., 1] + 0.25) & (sub[..., 0] > sub[..., 2] + 0.25)
    blue = sub[..., 2] > sub[..., 0] + 0.2
    gold = (sub[..., 0] > 0.5) & (sub[..., 1] > 0.3) & (sub[..., 2] < sub[..., 1] - 0.15)
    grey = (sub.min(-1) > 0.35) & (np.ptp(sub, -1) < 0.08)
    light = sub.min(-1) > 0.3

    def bar_rows(m):
        r = m.sum(1)
        rows = np.where(r > r.max() * 0.5)[0]
        return rows.min(), rows.max()

    def longest(row):
        best, s = None, None
        for i, v in enumerate(np.append(row, False)):
            if v and s is None: s = i
            if not v and s is not None:
                if best is None or i - s > best[1] - best[0]: best = (s, i)
                s = None
        return best

    def top_edges(m, top, bot):
        """The bar's top-left and top-right x: lines fitted to each row's longest run, so the
        gold slash's orange and the grunge gaps don't count."""
        ys, ls, rs = [], [], []
        for y in range(top + 2, bot - 1):
            run = longest(m[y])
            if run and run[1] - run[0] > 40:
                ys.append(y); ls.append(run[0]); rs.append(run[1])
        return np.polyval(np.polyfit(ys, ls, 1), top), np.polyval(np.polyfit(ys, rs, 1), top)

    h_top, h_bot = bar_rows(red)
    f_top, f_bot = bar_rows(blue)
    h_l, h_r = top_edges(red, h_top, h_bot)
    f_l, _ = top_edges(blue, f_top, f_bot)
    # The focus track's right end: its light outline along the bar's top rows.
    f_r = max(np.where(light[y])[0].max() for y in range(f_top, f_top + 3))
    acc_cols = np.where((light | gold)[:, :int(h_l) + 60].any(0))[0]
    acc_rows = np.where((light | gold)[:, :int(h_l) + 60].any(1))[0]
    ax, ay = acc_cols.min(), acc_rows.min()
    # In 1080p px, with the health bar LAYOUT_HEALTH_H tall.
    s = LAYOUT_HEALTH_H / (h_bot - h_top + 1)
    for n, (x, y, w, hh) in (
            ("accent", (ax, ay, acc_cols.max() - ax + 1, acc_rows.max() - ay + 1)),
            ("health", (h_l, h_top, h_r - h_l + 1, h_bot - h_top + 1)),
            ("focus", (f_l, f_top, f_r - f_l + 1, f_bot - f_top + 1))):
        print(f"[layout] {n}: at ({(x - ax) * s:.0f}, {(y - ay) * s:.0f}), size {w * s:.0f} x {hh * s:.0f}")
    # Sheet px, relative to the composite's crop, for the assembly preview.
    return {"crop": sub, "accent": (ax, ay),
            "health": (round(h_l), h_top, round(h_r - h_l + 1)),
            "focus": (round(f_l), f_top, round(f_r - f_l + 1))}


def shade(tile, kl, kr, outline, length, fill, track):
    """M_HUDBar's maths in numpy: shape, outline on the slanted ends, fill front, tiled texture."""
    h, tw = tile.shape[:2]
    ys, xs = np.mgrid[0:h, 0:length] + 0.5
    xl = (ys - 0.5) * kl
    xr = length - (ys - 0.5) * kr
    cov = np.clip(xs - xl + 0.5, 0, 1) * np.clip(xr - xs + 0.5, 0, 1)
    edge = np.minimum((xs - xl) / np.hypot(1, kl), (xr - xs) / np.hypot(1, kr))
    front = fill * length - (ys - 0.5) * kr
    f = np.clip(front - xs + 0.5, 0, 1)[..., None]
    u = xs.astype(int) % tw
    v = ys / h
    fc = tile[(v * tile.shape[0]).astype(int), u]
    tc = track[0][(v * track[0].shape[0]).astype(int), xs.astype(int) % track[0].shape[1]]
    oc = np.clip(1.3 - edge, 0, 1)[..., None]               # ~1 px outline on the ends
    fcol = fc[..., :3] * (1 - oc) + np.array(outline) * oc
    tcol = tc[..., :3] * (1 - oc) + np.array(track[3]) * oc
    col = fcol * f + tcol * (1 - f)
    a = cov * (fc[..., 3] * f[..., 0] + tc[..., 3] * (1 - f[..., 0]) * 0.85)
    return col, a


tiles = {n: cut_bar(n) for n in ("Health", "Focus", "Empty")}
accent = cut_accent()
lay = layout()

if preview:
    rows = []
    for name in ("Health", "Focus"):
        tile, _, _, outline = tiles[name]
        for length, fill in ((180, 1.0), (300, 0.65), (480, 0.3)):
            col, a = shade(tile, SLOPE, SLOPE, outline, length, fill, tiles["Empty"])
            rows.append((col, a))
    Wp = max(c.shape[1] for c, _ in rows) + 20
    Hp = sum(c.shape[0] + 8 for c, _ in rows) + 12
    for bgc, tag in (((0.05, 0.05, 0.05), "dark"), ((0.55, 0.52, 0.48), "mid")):
        canvas = np.zeros((Hp, Wp, 3)) + bgc
        y = 6
        for c, a in rows:
            h, w = c.shape[:2]
            canvas[y:y + h, 10:10 + w] = canvas[y:y + h, 10:10 + w] * (1 - a[..., None]) + c * a[..., None]
            y += h + 8
        rows_img = canvas if tag == "dark" else np.concatenate([rows_img, canvas], 0)
    big = rows_img.repeat(2, 0).repeat(2, 1)
    save(preview, np.dstack([big, np.ones(big.shape[:2])]))

    # The cluster rebuilt from the cut pieces at the measured layout, under the sheet's composite.
    ref = lay["crop"]
    canvas = np.zeros_like(ref) + BG
    def put(col, a, x, y):
        h, w = a.shape
        x, y = int(x), int(y)
        h, w = min(h, canvas.shape[0] - y), min(w, canvas.shape[1] - x)
        region = canvas[y:y + h, x:x + w]
        canvas[y:y + h, x:x + w] = region * (1 - a[:h, :w, None]) + col[:h, :w] * a[:h, :w, None]
    for name, fill in (("Health", 1.0), ("Focus", 0.68)):
        tile, _, _, outline = tiles[name]
        x, y, length = lay[name.lower()]
        col, a = shade(tile, SLOPE, SLOPE, outline, length, fill, tiles["Empty"])
        put(col, a, x, y)
    put(accent[..., :3], accent[..., 3], *lay["accent"])
    both = np.concatenate([ref, np.ones((6,) + ref.shape[1:]), canvas], 0).repeat(2, 0).repeat(2, 1)
    save(preview.replace(".png", "_assembled.png"), np.dstack([both, np.ones(both.shape[:2])]))
