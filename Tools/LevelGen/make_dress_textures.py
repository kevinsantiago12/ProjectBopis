"""Draws the textures for the building dressing, with no libraries: concrete vent blocks and nailed-on plywood sheets. User
2026-11-04: "do downpipes and window air conditioning. and the overhang rooms, ply patches" ... "door steps and vent blocks
too". No pack has either. All original, drawn from noise here, so nothing depends on the packs.

Writes colour and DirectX normal PNGs to Saved/LevelGen/import/dress/; create_dress_materials_ue.py imports them.
- Vent blocks: 1024 x 512, 4 x 2 blocks of 20 x 20 cm, so a plane 80 x 40 cm shows them at their real size. The holes are painted
  dark: the walls behind are solid, and at alley distance it reads as depth.
- Plywood: 512 x 1024, one sheet with the grain along its height, nails around the edge. Natural, weathered, flaking green paint.

Usage (from the project root): python Tools/LevelGen/make_dress_textures.py"""
import math
import os
import random
import struct
import zlib

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "Saved", "LevelGen", "import", "dress")
os.makedirs(OUT, exist_ok=True)


def write_png(name, w, h, rgb):
    """rgb: a flat list of (r, g, b) floats 0..1, row by row from the top."""
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            r, g, b = rgb[y * w + x]
            raw += bytes((max(0, min(255, int(r * 255 + 0.5))), max(0, min(255, int(g * 255 + 0.5))),
                          max(0, min(255, int(b * 255 + 0.5)))))

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0)) +
                chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))
    print("wrote", name)


class Noise:
    """Value noise on a wrapping lattice, so the pattern has no seams at the texture's edge."""

    def __init__(self, seed, nx, ny):
        r = random.Random(seed)
        self.nx, self.ny = nx, ny
        self.v = [r.random() for _ in range(nx * ny)]

    def at(self, u, v):
        x, y = u * self.nx, v * self.ny
        ix, iy = int(math.floor(x)), int(math.floor(y))
        fx, fy = x - ix, y - iy
        fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
        a = self.v[(iy % self.ny) * self.nx + ix % self.nx]
        b = self.v[(iy % self.ny) * self.nx + (ix + 1) % self.nx]
        c = self.v[((iy + 1) % self.ny) * self.nx + ix % self.nx]
        d = self.v[((iy + 1) % self.ny) * self.nx + (ix + 1) % self.nx]
        return a + (b - a) * fx + (c - a) * fy + (a - b - c + d) * fx * fy


def fbm(layers, u, v):
    return sum(n.at(u, v) * k for n, k in layers) / sum(k for _, k in layers)


def normal_from(h, w, ht, strength, wrap=True):
    """DirectX normal map from a height field (a flat list, 0..1): green is the image's downward slope."""
    out = []
    for y in range(ht):
        for x in range(w):
            l, r = h[y * w + (x - 1) % w], h[y * w + (x + 1) % w]
            u, d = h[((y - 1) % ht) * w + x], h[((y + 1) % ht) * w + x]
            nx, ny = (l - r) * strength, (u - d) * strength
            k = math.sqrt(nx * nx + ny * ny + 1.0)
            out.append((nx / k * 0.5 + 0.5, ny / k * 0.5 + 0.5, 1.0 / k * 0.5 + 0.5))
    return out


def lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def vent_holes(kind, u, v):
    """Signed distance-ish value in a unit cell (0..1): > 0 inside a hole. Cell coordinates, block frame included."""
    x, y = u - 0.5, v - 0.5
    if kind == "Diamond":                   # four triangles round a central diamond, the commonest pattern
        frame = 0.42 - max(abs(x), abs(y))
        bar = abs(abs(x) + abs(y) - 0.26) - 0.045      # the diamond's outline
        cross = min(abs(x - y), abs(x + y)) - 0.028     # ties from the diamond to the block's corners
        return min(frame, min(bar, cross) if abs(x) + abs(y) > 0.26 else bar)
    if kind == "Slots":                     # three upright slots
        frame = 0.42 - max(abs(x), abs(y))
        cx = (x + 0.42) / 0.84 * 3
        slot = 0.5 - abs((cx % 1.0) - 0.5)
        return min(frame, (slot - 0.13) * 0.84 / 3)
    raise ValueError(kind)


def make_vents(kind, seed):
    w, h = 1024, 512
    n = [(Noise(seed, 8, 4), 1.0), (Noise(seed + 1, 32, 16), 0.6), (Noise(seed + 2, 128, 64), 0.35),
         (Noise(seed + 3, 256, 128), 0.25)]
    stain = [(Noise(seed + 4, 6, 3), 1.0), (Noise(seed + 5, 24, 12), 0.4)]
    rnd = random.Random(seed)
    tones = [rnd.uniform(0.9, 1.08) for _ in range(8)]
    col, hgt = [], []
    for py in range(h):
        v = (py + 0.5) / h
        for px in range(w):
            u = (px + 0.5) / w
            cu, cv = u * 4, v * 2
            cell = int(cu) + int(cv) * 4
            fu, fv = cu - int(cu), cv - int(cv)
            d = vent_holes(kind, fu, fv)
            mortar = min(fu, 1 - fu, fv, 1 - fv)
            grain = fbm(n, u, v)
            base = (0.56, 0.55, 0.52)
            t = tones[cell] * (0.74 + 0.5 * grain)
            c = (base[0] * t, base[1] * t, base[2] * t)
            c = lerp3(c, (0.26, 0.25, 0.23), smooth(0.022, 0.008, mortar))     # mortar joints
            c = lerp3(c, (0.21, 0.2, 0.17), 0.55 * smooth(0.5, 0.72, fbm(stain, u, v)))   # grime
            # Inside a hole: near black, a little lighter at the top lip (light falls in from above).
            if d > 0:
                depth = smooth(0.0, 0.05, d)
                c = lerp3(lerp3(c, (0.05, 0.05, 0.05), 0.75), (0.018, 0.018, 0.02), depth)
                hh = 0.0
            else:
                c = lerp3(c, (c[0] * 0.55, c[1] * 0.55, c[2] * 0.55), smooth(-0.03, 0.0, d))
                hh = 0.55 + 0.12 * grain + 0.45 * smooth(0.0, 0.03, -d)
            hh -= 0.12 * smooth(0.022, 0.008, mortar)
            col.append(c)
            hgt.append(hh)
    write_png("T_BackAlleys_VentBlock_%s_BC.png" % kind, w, h, col)
    write_png("T_BackAlleys_VentBlock_%s_N.png" % kind, w, h, normal_from(hgt, w, h, 5.0))


def make_plywood(seed):
    """One sheet: returns the height field; writes the three finishes."""
    w, h = 512, 1024
    warp = [(Noise(seed, 5, 3), 1.0), (Noise(seed + 1, 13, 7), 0.4)]
    fine = [(Noise(seed + 2, 150, 7), 1.0), (Noise(seed + 3, 256, 18), 0.55)]
    blot = [(Noise(seed + 4, 7, 12), 1.0), (Noise(seed + 5, 22, 40), 0.5), (Noise(seed + 6, 64, 128), 0.25)]
    flake = [(Noise(seed + 7, 18, 30), 1.0), (Noise(seed + 8, 60, 110), 0.7), (Noise(seed + 9, 150, 280), 0.3)]
    rnd = random.Random(seed)
    nails = []
    for ny_ in range(9):                        # along both long sides, and the two ends
        yy = (ny_ + 0.5) / 9
        for xx in (0.035, 0.965):
            nails.append((xx + rnd.uniform(-0.006, 0.006), yy + rnd.uniform(-0.01, 0.01)))
    for nx_ in range(5):
        xx = (nx_ + 0.5) / 5
        for yy in (0.018, 0.982):
            nails.append((xx + rnd.uniform(-0.01, 0.01), yy + rnd.uniform(-0.004, 0.004)))
    finishes = {"Natural": [], "Weathered": [], "GreenPaint": []}
    hgt = []
    for py in range(h):
        v = (py + 0.5) / h
        for px in range(w):
            u = (px + 0.5) / w
            wx = fbm(warp, u, v)
            # Cathedral grain: bands of a warped coordinate, as a rotary-cut veneer shows.
            band = 0.5 + 0.5 * math.sin((u * 7.0 + wx * 5.5) * 2 * math.pi)
            band = band * band
            f = fbm(fine, u, v)
            b = fbm(blot, u, v)
            edge = min(u, 1 - u, (v * 2), (1 - v) * 2)
            wet = smooth(0.09, 0.0, edge) * 0.55 + smooth(0.48, 0.9, b) * 0.42
            nail = 0.0
            for nx0, ny0 in nails:
                dx, dy = (u - nx0) * 512, (v - ny0) * 1024
                if abs(dx) < 9 and abs(dy) < 40:
                    d2 = dx * dx + dy * dy
                    nail = max(nail, smooth(30.0, 3.0, d2) * 0.9)         # the head
                    nail = max(nail, smooth(1.0, 0.0, abs(dx) / 3.5) * smooth(36.0, 0.0, max(0.0, dy)) * 0.3
                               if dy > 0 else 0.0)                         # a rust streak under it
            # Bright enough to stay a board in an alley's shade: first go was near black there. Real ply is pale.
            tan = lerp3((0.76, 0.64, 0.47), (0.63, 0.50, 0.34), band * 0.5 + (f - 0.5) * 0.7)
            nat = lerp3(tan, (0.36, 0.27, 0.18), wet * 0.8)
            grey = (0.60, 0.57, 0.52)
            wea = lerp3(lerp3(tan, grey, 0.75), (0.27, 0.24, 0.21), wet * 0.85)
            paint = lerp3((0.40, 0.60, 0.48), (0.32, 0.50, 0.40), smooth(0.35, 0.7, b))
            # Mostly painted, flaking only in patches and along the wet edges: half and half read as camouflage.
            kept = smooth(0.30, 0.34, fbm(flake, u, v) + 0.03 * band - wet * 0.14)
            grn = lerp3(lerp3(lerp3(tan, grey, 0.5), (0.3, 0.26, 0.21), wet * 0.8), paint, kept)
            rust = (0.17, 0.09, 0.05)
            finishes["Natural"].append(lerp3(nat, rust, nail))
            finishes["Weathered"].append(lerp3(wea, rust, nail))
            finishes["GreenPaint"].append(lerp3(grn, rust, nail))
            hgt.append(0.5 + 0.35 * (band - 0.5) * 0.45 + 0.32 * (f - 0.5) - 0.7 * smooth(30.0, 3.0, 1e9 if nail == 0 else 10.0) * 0)
    for k, c in finishes.items():
        write_png("T_BackAlleys_Ply_%s_BC.png" % k, w, h, c)
    write_png("T_BackAlleys_Plywood_N.png", w, h, normal_from(hgt, w, h, 2.2))


make_vents("Diamond", 211)
make_vents("Slots", 223)
make_plywood(307)
print("done:", OUT)
