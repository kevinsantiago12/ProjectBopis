"""Draws the textures for the street dressing, with no libraries. User 2026-11-05: "do all that and add it to the tool" (wires, rooftops,
lights, shop fronts, wall details). Everything here is original, drawn from noise, so nothing depends on the packs.

Writes PNGs to Saved/LevelGen/import/street/; create_street_materials_ue.py imports them.
- Sign boards: 512 x 256, sun-faded paint on sheet metal, rust from the fixings and the top edge. No lettering: what a sign says is
  design's call, so they are blank until the user gives wording. No normal map: the first one made them look hammered.
- Peeling paint: 512 x 512 with alpha, flakes of bare grey render with dark broken edges, for the decal on painted faces.
- Poster wear: 512 x 512, three masks for M_BackAlleys_Poster. R tears the edges, G is grime and fold lines, B says where the sun faded it. It wraps,
  and each copy of a poster reads its own patch of it.

Usage (from the project root): python Tools/LevelGen/make_street_textures.py"""
import math
import os
import random
import struct
import zlib

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
OUT = os.path.join(ROOT, "Saved", "LevelGen", "import", "street")
os.makedirs(OUT, exist_ok=True)


def write_png(name, w, h, px):
    """px: a flat list of (r, g, b) or (r, g, b, a) floats 0..1, row by row from the top."""
    n = len(px[0])
    raw = bytearray()
    for y in range(h):
        raw.append(0)
        for x in range(w):
            raw += bytes(max(0, min(255, int(c * 255 + 0.5))) for c in px[y * w + x])

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xffffffff)
    with open(os.path.join(OUT, name), "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6 if n == 4 else 2, 0, 0, 0)) +
                chunk(b"IDAT", zlib.compress(bytes(raw), 6)) + chunk(b"IEND", b""))
    print("wrote", name)


class Noise:
    """Value noise on a wrapping lattice."""

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


def lerp3(a, b, t):
    return (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, a[2] + (b[2] - a[2]) * t)


def smooth(e0, e1, x):
    t = max(0.0, min(1.0, (x - e0) / (e1 - e0)))
    return t * t * (3 - 2 * t)


def make_signs(seed):
    w, h = 512, 256
    blot = [(Noise(seed, 5, 3), 1.0), (Noise(seed + 1, 20, 10), 0.5), (Noise(seed + 2, 80, 40), 0.25)]
    fine = [(Noise(seed + 3, 128, 64), 1.0), (Noise(seed + 4, 256, 128), 0.6)]
    chip = [(Noise(seed + 5, 24, 12), 1.0), (Noise(seed + 6, 90, 45), 0.8), (Noise(seed + 7, 200, 100), 0.4)]
    streak = [(Noise(seed + 8, 64, 3), 1.0), (Noise(seed + 9, 160, 5), 0.6)]
    rnd = random.Random(seed)
    screws = [(x + rnd.uniform(-0.006, 0.006), y + rnd.uniform(-0.01, 0.01)) for x in (0.03, 0.5, 0.97) for y in (0.06, 0.94)]
    # Sun-faded: dusty, never pure. sRGB, as a colour picker shows it.
    colours = {"Red": (0.56, 0.20, 0.15), "Yellow": (0.74, 0.60, 0.25), "White": (0.70, 0.68, 0.61), "Blue": (0.21, 0.33, 0.46)}
    out = {k: [] for k in colours}
    for py in range(h):
        v = (py + 0.5) / h
        for px in range(w):
            u = (px + 0.5) / w
            b, f = fbm(blot, u, v), fbm(fine, u, v)
            run = fbm(streak, u, v)
            # Rust runs down from the top edge and from each fixing.
            rust = smooth(0.62, 0.8, run) * smooth(0.75, 0.0, v) * 0.55
            for sx_, sy_ in screws:
                dx, dy = (u - sx_) * 2.0, v - sy_
                if abs(dx) < 0.03 and dy > -0.02:
                    rust = max(rust, smooth(0.03, 0.004, abs(dx)) * smooth(0.45, 0.0, dy) * 0.8)
            bare = smooth(0.66, 0.70, fbm(chip, u, v) + 0.12 * (b - 0.5))
            metal = lerp3((0.47, 0.46, 0.44), (0.32, 0.20, 0.13), 0.5 + 0.5 * (f - 0.5))
            for k, c in colours.items():
                t = 0.80 + 0.42 * (b - 0.5) + 0.25 * (f - 0.5)
                paint = (c[0] * t, c[1] * t, c[2] * t)
                paint = lerp3(paint, (0.62, 0.61, 0.57), smooth(0.5, 0.75, b) * 0.22)      # chalky from the sun
                col = lerp3(lerp3(paint, metal, bare), (0.24, 0.12, 0.07), rust)
                out[k].append(col)
    for k, c in out.items():
        write_png("T_BackAlleys_Sign_%s_BC.png" % k, w, h, c)


def make_peel(letter, seed):
    """Alpha is where the paint has gone. A soft blob of it that breaks up into flakes towards its edge, and never reaches the texture's."""
    w = h = 512
    warp = [(Noise(seed, 4, 4), 1.0), (Noise(seed + 1, 11, 11), 0.5)]
    flake = [(Noise(seed + 2, 14, 14), 1.0), (Noise(seed + 3, 40, 40), 0.75), (Noise(seed + 4, 110, 110), 0.4)]
    grain = [(Noise(seed + 5, 64, 64), 1.0), (Noise(seed + 6, 200, 200), 0.6)]
    px_ = []
    for py in range(h):
        v = (py + 0.5) / h
        for px in range(w):
            u = (px + 0.5) / w
            du, dv = u - 0.5, v - 0.5
            r = math.sqrt(du * du + dv * dv) * 2.0 + 0.62 * (fbm(warp, u, v) - 0.5)
            keep = smooth(0.98, 0.42, r)                        # 1 in the middle of the blob, 0 past its edge
            f = fbm(flake, u, v) + 0.34 * (keep - 0.5)
            a = smooth(0.545, 0.556, f) * smooth(0.0, 0.08, min(u, 1 - u, v, 1 - v))
            g = fbm(grain, u, v)
            render = lerp3((0.33, 0.32, 0.29), (0.52, 0.50, 0.46), g)      # bare render under the paint
            edge = smooth(0.60, 0.553, f)                       # where the paint broke: a dark line round each flake
            col = lerp3(render, (0.13, 0.12, 0.10), edge * 0.75)
            px_.append((col[0], col[1], col[2], a))
    write_png("T_BackAlleys_Peel_%s_BC.png" % letter, w, h, px_)


def make_poster_wear(seed):
    w = h = 512
    tear = [(Noise(seed, 9, 9), 1.0), (Noise(seed + 1, 30, 30), 0.8), (Noise(seed + 2, 90, 90), 0.45)]
    soft = [(Noise(seed + 3, 5, 5), 1.0), (Noise(seed + 4, 16, 16), 0.5)]
    fine = [(Noise(seed + 5, 128, 128), 1.0), (Noise(seed + 6, 256, 256), 0.5)]
    sun = [(Noise(seed + 7, 3, 3), 1.0), (Noise(seed + 8, 7, 7), 0.5)]
    px_ = []
    for py in range(h):
        v = (py + 0.5) / h
        for px in range(w):
            u = (px + 0.5) / w
            r_ = smooth(0.32, 0.68, fbm(tear, u, v))
            # Grime in soft patches with fine speckle, and the two folds a poster gets from being carried, in wrapping bands.
            g_ = smooth(0.46, 0.72, fbm(soft, u, v)) * 0.55 + smooth(0.62, 0.8, fbm(fine, u, v)) * 0.25
            for f_ in (0.27, 0.71):
                g_ = max(g_, smooth(0.006, 0.0, abs(((v - f_ + 0.5) % 1.0) - 0.5)) * 0.32)
                g_ = max(g_, smooth(0.005, 0.0, abs(((u - f_ * 0.8 + 0.5) % 1.0) - 0.5)) * 0.26)
            b_ = smooth(0.3, 0.72, fbm(sun, u, v))
            px_.append((r_, g_, b_))
    write_png("T_BackAlleys_PosterWear.png", w, h, px_)


make_poster_wear(503)
make_signs(401)
make_peel("A", 431)
make_peel("B", 457)
print("done:", OUT)
