"""Draws the muzzle flash offline, from design.py, so its look can be tuned without the editor: the same cards as
bl_mesh.py, the same growth as the component, the same shading as make_ue.py's HLSL, traced from a few camera
angles at several ages. The cards add up (the material is additive), so their order doesn't matter.

Run with Blender's bundled Python (it has numpy):
    "C:/Program Files/Blender Foundation/Blender 4.0/4.0/python/bin/python.exe" Tools/FX/MuzzleFlash/preview.py
Needs noise.tga beside it (make_ue.py exports it). Writes preview.png: rows are ages, columns are views, and
the last row is six different shots from behind the shooter."""
import math
import os
import struct
import sys
import zlib

import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import design as D  # noqa: E402

TILE = 200
LENGTH, WIDTH = 1.0, 0.45            # a pistol-ish flash, in lengths
AGES = [0.0, 0.08, 0.16, 0.25, 0.4, 0.55, 0.7, 0.85, 0.95]
# (name, angle from the barrel's line out of the muzzle, degrees). 160: behind the shooter, as the player sees it.
VIEWS = [("front 25", 25.0), ("side 90", 90.0), ("behind 140", 140.0), ("behind 160", 160.0)]


# --- Noise --------------------------------------------------------------------------------------------------
def read_tga(path):
    data = open(path, "rb").read()
    id_len, kind = data[0], data[2]
    w, h = struct.unpack("<HH", data[12:16])
    bpp, desc = data[16], data[17]
    if kind != 2:
        raise RuntimeError("only uncompressed true-colour TGA")
    px = np.frombuffer(data, np.uint8, offset=18 + id_len, count=w * h * bpp // 8).reshape(h, w, bpp // 8)
    if not desc & 0x20:
        px = px[::-1]
    return px[..., 2].astype(np.float32) / 255.0      # red; BGR order


def load_noise():
    srgb = read_tga(os.path.join(HERE, "noise.tga"))
    lin = np.power(srgb, 2.2)                          # the texture is sRGB: the material reads it linear
    mip = int(D.NOISE_MIP)
    for _ in range(mip):
        lin = 0.25 * (lin[0::2, 0::2] + lin[1::2, 0::2] + lin[0::2, 1::2] + lin[1::2, 1::2])
    return lin


def sample(tex, u, v):
    h, w = tex.shape
    x = np.mod(u, 1.0) * w - 0.5
    y = np.mod(v, 1.0) * h - 0.5
    x0 = np.floor(x).astype(np.int64)
    y0 = np.floor(y).astype(np.int64)
    fx, fy = x - x0, y - y0
    x1, y1 = (x0 + 1) % w, (y0 + 1) % h
    x0, y0 = x0 % w, y0 % h
    return (tex[y0, x0] * (1 - fx) * (1 - fy) + tex[y0, x1] * fx * (1 - fy)
            + tex[y1, x0] * (1 - fx) * fy + tex[y1, x1] * fx * fy)


# --- The material, as make_ue.py writes it ----------------------------------------------------------------------
def sat(x):
    return np.clip(x, 0.0, 1.0)


def smoothstep(a, b, x):
    t = sat((x - a) / (b - a))
    return t * t * (3 - 2 * t)


def hash1(x):
    return np.mod(np.sin(x * 12.9898) * 43758.5453, 1.0)


def noise_at(noise, nu, nv):
    n1 = sample(noise, nu, nv)
    n2 = sample(noise, nu * D.NOISE_SCALE_2 + 0.5, nv * D.NOISE_SCALE_2 + 0.5)
    n = n1 * (1.0 - D.NOISE_MIX) + n2 * D.NOISE_MIX
    n = np.power(n, 1 / 2.2)                           # back to the texture's own (sRGB) values
    return sat((n - D.NOISE_LOW) / (D.NOISE_HIGH - D.NOISE_LOW))


def shade(noise, star, u, v, fin_id, facing, age, seed, petals, p=D.PARAMS, c=D.COLOURS):
    if not star:
        nu = u * 0.9 - age * p["Flow"] + seed + fin_id * 0.37
        nv = v * 0.6 + seed * 1.7 + fin_id * 0.61
        n = noise_at(noise, nu, nv)
        petal = fin_id * 2.0 + (v > 0.5)               # six petals, two per card
        reach = D.PETAL_SHORTEST + (1.0 - D.PETAL_SHORTEST) * hash1(petal + seed * 7.13)
        pu = u / reach
        side = np.abs(v - 0.5) * 2.0 + (n - 0.5) * D.WARP
        uu = np.clip(pu, 1e-4, 1.0)
        width = D.PETAL_WIDTH * np.power(uu, D.PETAL_RISE) * np.power(np.clip(1.0 - pu, 0.0, 1.0), D.PETAL_FALL)
        width = np.where(pu < 1.0, width, 0.0)
        bu = u - D.BALL_U
        ball = 2.0 * D.LENGTH_PER_WIDTH * np.sqrt(np.maximum(D.BALL_U * D.BALL_U - bu * bu, 0.0))
        width = np.maximum(width, ball) * (1.0 - p["Spikes"]) + width * p["Spikes"]
        shape = sat((width - np.maximum(side, 0.0)) / np.maximum(width, 1e-3))
        near = 1.0 - u
    else:
        dx, dy = (u - 0.5) * 2.0, (v - 0.5) * 2.0
        r = np.hypot(dx, dy)
        a = np.arctan2(dy, dx)
        nu = r * 0.8 - age * p["Flow"] + seed
        nv = a * (3.0 / 6.2832) + seed * 1.7
        n = noise_at(noise, nu, nv)
        turn = np.mod(a / 6.2832 + 0.5 + seed, 1.0) * petals
        spike = np.floor(turn)
        across = np.mod(turn, 1.0) - 0.5 + (hash1(spike * 3.7 + seed * 5.1) - 0.5) * D.SPIKE_JITTER
        lobe = np.power(sat(np.cos(across * 3.14159)), D.STAR_SHARP)
        length = D.SPIKE_SHORTEST + (1.0 - D.SPIKE_SHORTEST) * hash1(spike + seed * 7.13)
        star = D.STAR_REACH * (D.STAR_CORE + (1.0 - D.STAR_CORE) * lobe * length)
        reach = D.DISC_REACH * (1.0 - p["Spikes"]) + star * p["Spikes"]
        shape = sat(1.0 - (r + (n - 0.5) * D.WARP * r) / reach)
        near = 1.0 - r
    body = shape * (D.DENSITY_BASE + D.DENSITY_NOISE * n)
    burn = np.power(sat((age - D.BURN_START) / (1.0 - D.BURN_START)), D.BURN_CURVE)
    threshold = D.BURN_FROM + (D.BURN_TO - D.BURN_FROM) * burn
    mask = sat((body - threshold) / p["Softness"]) * sat((1.0 - age) / D.FADE_LAST)
    pop = D.POP * (1.0 - sat(age / D.POP_TIME))
    heat = sat(body * D.HEAT_DENSITY + near * D.HEAT_BIAS - age * D.HEAT_AGE + pop * 0.3)
    hot, mid, cool = (np.array(c[k]) for k in ("HotColour", "MidColour", "CoolColour"))
    t1 = sat(heat * 2.0)[..., None]
    t2 = sat(heat * 2.0 - 1.0)[..., None]
    col = cool * (1 - t1) + mid * t1
    col = col * (1 - t2) + hot * t2
    view = smoothstep(p["FacingMin"], p["FacingMax"], facing)
    return col * (mask * view * p["Intensity"] * (1.0 + pop))[..., None]


# --- Tracing the cards ------------------------------------------------------------------------------------------
def ease_out(t):
    t = min(max(t, 0.0), 1.0)
    return 1.0 - (1.0 - t) ** 2


def render(noise, view_deg, age, seed, petals, roll_deg, p=D.PARAMS):
    grow = ease_out(age / D.GROW_TIME)
    lx = LENGTH * (D.START_LENGTH + (1 - D.START_LENGTH) * grow)
    wy = WIDTH * (D.START_WIDTH + (1 - D.START_WIDTH) * grow)
    target = np.array([0.4 * LENGTH, 0.0, 0.0])
    a = math.radians(view_deg)
    eye = target + 1.6 * np.array([math.cos(a), math.sin(a) * 0.8, math.sin(a) * 0.6])
    fwd = target - eye
    fwd /= np.linalg.norm(fwd)
    right = np.cross(fwd, [0.0, 0.0, 1.0])
    right /= np.linalg.norm(right)
    up = np.cross(right, fwd)
    s = (np.arange(TILE) + 0.5) / TILE * 2.0 - 1.0
    sx, sy = np.meshgrid(s, -s)
    half = math.tan(math.radians(20.0))
    dirs = fwd + (sx[..., None] * right + sy[..., None] * up) * half
    dirs /= np.linalg.norm(dirs, axis=-1, keepdims=True)
    out = np.zeros((TILE, TILE, 3))

    def plane(normal, point):
        denom = dirs @ normal
        with np.errstate(divide="ignore", invalid="ignore"):
            t = ((point - eye) @ normal) / denom
        hit = eye + dirs * t[..., None]
        facing = np.abs(denom)
        return hit, (t > 0) & np.isfinite(t), facing

    for k in range(D.FIN_PLANES):
        th = math.radians(k * 180.0 / D.FIN_PLANES + roll_deg)
        d = np.array([0.0, math.cos(th), math.sin(th)])
        n = np.array([0.0, -math.sin(th), math.cos(th)])
        hit, ok, facing = plane(n, np.zeros(3))
        u = hit[..., 0] / lx
        v = (hit @ d) / wy + 0.5
        ok &= (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
        col = shade(noise, False, u, v, k / D.FIN_PLANES, facing, age, seed, petals, p)
        out += np.where(ok[..., None], col, 0.0)

    sh = D.STAR_HALF * wy
    hit, ok, facing = plane(np.array([1.0, 0.0, 0.0]), np.array([D.STAR_X * lx, 0.0, 0.0]))
    rr = math.radians(roll_deg)
    y = hit[..., 1] * math.cos(rr) + hit[..., 2] * math.sin(rr)
    z = -hit[..., 1] * math.sin(rr) + hit[..., 2] * math.cos(rr)
    u, v = (y / sh + 1) * 0.5, (z / sh + 1) * 0.5
    ok &= (u >= 0) & (u <= 1) & (v >= 0) & (v <= 1)
    col = shade(noise, True, u, v, 0.0, facing, age, seed, petals, p)
    out += np.where(ok[..., None], col, 0.0)
    return out


def tonemap(hdr, background=0.04, exposure=0.025):
    """A dim wall behind, then a filmic curve (Narkowicz's ACES fit), close enough to Unreal's to judge colour."""
    x = (hdr * exposure + background) * 0.6
    x = np.clip((x * (2.51 * x + 0.03)) / (x * (2.43 * x + 0.59) + 0.14), 0.0, 1.0)
    return np.power(x, 1 / 2.2)


def write_png(path, img):
    h, w, _ = img.shape
    rows = np.clip(img * 255 + 0.5, 0, 255).astype(np.uint8)
    raw = b"".join(b"\x00" + rows[y].tobytes() for y in range(h))

    def chunk(tag, data):
        return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 2, 0, 0, 0))
                + chunk(b"IDAT", zlib.compress(raw, 6)) + chunk(b"IEND", b""))


def compare(noise, path):
    """Spikes 1 (the first version) above Spikes 0 (the round base), for each view at a young age, then one
    shot from behind the shooter growing and burning away."""
    rows = []
    for spikes in (1.0, 0.0):
        p = dict(D.PARAMS, Spikes=spikes)
        row = [tonemap(render(noise, deg, 0.1, 0.37, 5, 10.0, p)) for _, deg in VIEWS]
        row += [tonemap(render(noise, 160.0, age, 0.37, 5, 10.0, p)) for age in (0.0, 0.3, 0.55)]
        rows.append(np.concatenate(row, axis=1))
    sheet = np.concatenate(rows, axis=0)
    sheet[:, TILE - 1::TILE] = 0.3
    sheet[TILE - 1::TILE, :] = 0.3
    write_png(path, sheet)
    print("wrote", path)


def main():
    noise = load_noise()
    if len(sys.argv) > 1 and sys.argv[1] == "compare":
        compare(noise, os.path.join(HERE, "preview_compare.png"))
        return
    rows = []
    for age in AGES:
        rows.append(np.concatenate([tonemap(render(noise, deg, age, 0.37, 5, 10.0)) for _, deg in VIEWS], axis=1))
    rng = np.random.default_rng(7)
    shots = [tonemap(render(noise, 160.0, 0.2, rng.random(), int(rng.integers(3, 7)), rng.uniform(0, 360)))
             for _ in range(len(VIEWS))]
    rows.append(np.concatenate(shots, axis=1))
    sheet = np.concatenate(rows, axis=0)
    sheet[:, TILE - 1::TILE] = 0.3                     # grid lines
    sheet[TILE - 1::TILE, :] = 0.3
    path = os.path.join(HERE, sys.argv[1] if len(sys.argv) > 1 else "preview.png")
    write_png(path, sheet)
    print("wrote", path, "views:", [v for v, _ in VIEWS], "ages:", AGES)


if __name__ == "__main__":
    main()
