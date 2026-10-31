# Draws the HUD's left cap (the flag nod) and a mock of the full health/focus cluster.
#   blender --background --factory-startup --python MakeFlagCap.py -- <out dir>
# Writes, for each variant, a clean white/gold cap on transparent (T_HUD_FlagCap_<V>.png, the
# grunge goes on in the material) and a grunged mock of the whole cluster on a dark background
# (Mock_FlagCap_<V>.png) with health at 70% and focus at 55%.
#   A  "slashes": the mockup's white and gold slashes in front of slanted bars
#   B  "flag": the Philippine flag's hoist triangle (white, gold edge, sun and three stars);
#      the bars' left ends follow its two edges, so the cluster reads as the flag
# Geometry is in mock pixels at 2x the 1080p size (the cluster is ~52 px tall on screen).
import bpy, sys, os, math
import numpy as np

out_dir = sys.argv[sys.argv.index("--") + 1]
SS = 4                       # supersampling for anti-aliased edges

GOLD = (0.95, 0.72, 0.15)
WHITE = (0.94, 0.93, 0.90)
RED = (0.78, 0.06, 0.06)
BLUE = (0.07, 0.24, 0.85)
BG = (0.07, 0.06, 0.055)

RED_Y = (0, 56)              # bar rows, y down from the top of the cluster
BLUE_Y = (62, 92)
SLANT = 0.55                 # x per y of every slanted edge, "/" direction
RED_LEN, BLUE_LEN = 560, 460


class Canvas:
    def __init__(self, w, h):
        self.w, self.h = w, h
        yy, xx = np.mgrid[0:h * SS, 0:w * SS]
        self.x = (xx + 0.5) / SS
        self.y = (yy + 0.5) / SS

    def coverage(self, inside):
        """Supersampled boolean mask -> 0..1 coverage at output resolution."""
        m = inside.reshape(self.h, SS, self.w, SS).mean(axis=(1, 3))
        return m


def convex(cv, pts):
    """Inside test for a convex polygon given clockwise (y down) points."""
    inside = np.ones_like(cv.x, bool)
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        inside &= (x1 - x0) * (cv.y - y0) - (y1 - y0) * (cv.x - x0) >= 0
    return inside


def star(cv, cx, cy, r, points=5, inner=0.45, rot=-math.pi / 2):
    ang = np.arctan2(cv.y - cy, cv.x - cx) - rot
    d = np.hypot(cv.x - cx, cv.y - cy)
    seg = 2 * math.pi / points
    a = np.abs((ang % seg) - seg / 2) / (seg / 2)   # 0 at a valley, 1 at a point
    edge = r * (inner + (1 - inner) * a ** 2)
    return d <= edge


def sun(cv, cx, cy, r):
    disc = np.hypot(cv.x - cx, cv.y - cy) <= r * 0.5
    return disc | star(cv, cx, cy, r, points=8, inner=0.55, rot=0)


def grunge_sampler(path):
    img = bpy.data.images.load(path)
    n = img.size[0]
    px = np.empty(n * n * 4, np.float32)
    img.pixels.foreach_get(px)
    g = px.reshape(n, n, 4)[::-1]          # Blender rows run bottom-up
    # The material's default weights: streaks and scratches full, blotches at 35%.
    mix = g[..., 0] * (1 - 0.35 * (1 - g[..., 1])) * g[..., 2]
    def at(cv, scale=1.0, ox=0, oy=0):
        gy = ((np.arange(cv.h)[:, None] + oy) * scale).astype(int) % n
        gx = ((np.arange(cv.w)[None, :] + ox) * scale).astype(int) % n
        return mix[gy, gx]
    return at


def bar(cv, y0, y1, left_edge, length, fill):
    """Slanted bar; left_edge(y) gives its left x per row. Returns (fill mask, track mask)."""
    right = lambda y: length + (y1 - y) * SLANT
    rows = (cv.y >= y0) & (cv.y < y1)
    lx = left_edge(cv.y)
    full = rows & (cv.x >= lx) & (cv.x <= right(cv.y))
    fx = lx + (right(cv.y) - lx) * fill
    return full & (cv.x <= fx), full & (cv.x > fx)


def variant_a(cv):
    shapes = []
    h0, h1 = RED_Y[0] - 6, BLUE_Y[1] + 6
    sl = 0.75
    p = lambda x, w: [(x + (h1 - h0) * sl, h0), (x + (h1 - h0) * sl + w, h0), (x + w, h1), (x, h1)]
    shapes.append((convex(cv, p(0, 26)), WHITE))
    shapes.append((convex(cv, p(32, 7)), GOLD))
    left = lambda y: 52 + (BLUE_Y[1] - y) * SLANT
    return shapes, left, left


def variant_b(cv):
    top, bot = RED_Y[0], BLUE_Y[1]
    apex = (96, (RED_Y[1] + BLUE_Y[0]) / 2)
    tri = [(0, top), apex, (0, bot)]
    gold_w = 5
    shapes = [(convex(cv, [(0, top - 3), (apex[0] + gold_w, apex[1]), (0, bot + 3)]), GOLD),
              (convex(cv, tri), WHITE)]
    cx, cy = apex[0] * 0.36, apex[1]
    shapes.append((sun(cv, cx, cy, 13), GOLD))
    for sx, sy in [(9, top + 9), (9, bot - 9), (apex[0] - 20, apex[1])]:
        shapes.append((star(cv, sx, sy, 5), GOLD))
    gap = 7
    k = apex[0] / (apex[1] - top)          # the triangle edges' x per y
    red_left = lambda y: (y - top) * k + gap
    blue_left = lambda y: (bot - y) * apex[0] / (bot - apex[1]) + gap
    return shapes, red_left, blue_left


def save(path, rgb, a):
    h, w = a.shape
    img = bpy.data.images.new("o", w, h, alpha=True)
    px = np.zeros((h, w, 4), np.float32)
    px[..., :3] = rgb
    px[..., 3] = a
    img.pixels.foreach_set(px[::-1].ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    print(f"[cap] wrote {path}")


grunge = grunge_sampler(os.path.join(out_dir, "T_HUD_Grunge.png"))

for name, build in (("A", variant_a), ("B", variant_b)):
    pad = 12
    cv = Canvas(RED_LEN + 120, BLUE_Y[1] + 2 * pad)
    cv.y -= pad
    cv.x -= pad
    shapes, red_left, blue_left = build(cv)

    # The cap alone, clean, cropped to its shapes.
    rgb = np.zeros((cv.h, cv.w, 3), np.float32)
    a = np.zeros((cv.h, cv.w), np.float32)
    for inside, col in shapes:
        c = cv.coverage(inside)
        rgb = rgb * (1 - c[..., None]) + np.array(col) * c[..., None]
        a = a + c * (1 - a)
    cols = np.where(a.max(0) > 0)[0]
    x1 = cols.max() + pad
    save(os.path.join(out_dir, f"T_HUD_FlagCap_{name}.png"), rgb[:, :x1], a[:, :x1])

    # The mock: cap and bars over a dark background, all grunged.
    out = np.zeros((cv.h, cv.w, 3), np.float32) + BG
    g = grunge(cv, 2.0)
    def paint(cov, col, alpha):
        al = (cov * alpha)[..., None]
        out[:] = out * (1 - al) + np.array(col) * al
    rf, rt = bar(cv, *RED_Y, red_left, RED_LEN, 0.70)
    bf, bt = bar(cv, *BLUE_Y, blue_left, BLUE_LEN, 0.55)
    for m in (rt, bt):
        paint(cv.coverage(m), (0, 0, 0), 0.55)
    paint(cv.coverage(rf), RED, g)
    paint(cv.coverage(bf), BLUE, g)
    for inside, col in shapes:
        paint(cv.coverage(inside), col, 0.4 + 0.6 * g)
    save(os.path.join(out_dir, f"Mock_FlagCap_{name}.png"), out, np.ones((cv.h, cv.w)))
