# Makes the HUD's tileable grunge mask (white = paint intact, dark = worn through).
#   blender --background --factory-startup --python MakeGrunge.py -- <out dir> [seed]
# Writes T_HUD_Grunge.png, three masks packed in one texture so the material can weight them:
#   R  brushed streaks: long horizontal drags, like the mockup's bars
#   G  blotchy wear: soft-edged chips and worn patches
#   B  scratches and speckle: thin hard lines and pits
# and T_HUD_Grunge_Preview.png, the default mix (R*G*B) as grey, for looking at.
# Every layer is built in frequency space (FFT) or with wrap-around, so it tiles seamlessly.
import bpy, sys, os
import numpy as np

args = sys.argv[sys.argv.index("--") + 1:]
out_dir = args[0]
seed = int(args[1]) if len(args) > 1 else 7
os.makedirs(out_dir, exist_ok=True)

N = 1024
rng = np.random.default_rng(seed)
ky = np.fft.fftfreq(N)[:, None]
kx = np.fft.fftfreq(N)[None, :]


def filtered_noise(spectrum):
    """White noise shaped by a filter in frequency space; periodic, normalised to 0..1."""
    f = np.fft.fft2(rng.standard_normal((N, N))) * spectrum
    n = np.real(np.fft.ifft2(f))
    return (n - n.min()) / (n.max() - n.min())


def smoothstep(e0, e1, x):
    t = np.clip((x - e0) / (e1 - e0), 0, 1)
    return t * t * (3 - 2 * t)


# R: streaks. Narrow in x frequency (long horizontally), wide in y (many thin rows).
streak = filtered_noise(np.exp(-(kx / 0.004) ** 2 - (ky / 0.08) ** 2))
fine = filtered_noise(np.exp(-(kx / 0.02) ** 2 - (ky / 0.3) ** 2))
r = 1 - smoothstep(0.62, 0.8, streak * 0.7 + fine * 0.3)

# G: blotches. 1/f fractal noise, thresholded into soft-edged worn patches.
k = np.sqrt(kx ** 2 + ky ** 2)
k[0, 0] = 1
fbm = filtered_noise(k ** -1.6 * (k > 0.002))
grain = filtered_noise(np.exp(-(k / 0.15) ** 2))
g = 1 - smoothstep(0.66, 0.74, fbm * 0.85 + grain * 0.15)

# B: scratches (wrapping line segments, mostly near-horizontal) and speckle.
b = np.ones((N, N))
for _ in range(140):
    x0, y0 = rng.uniform(0, N, 2)
    ang = rng.normal(0, 0.18) + (np.pi if rng.random() < 0.5 else 0)
    length = rng.uniform(30, 260)
    depth = rng.uniform(0.35, 0.9)
    steps = int(length * 2)
    t = np.linspace(0, length, steps)
    xs = (x0 + np.cos(ang) * t).astype(int) % N
    ys = (y0 + np.sin(ang) * t).astype(int) % N
    b[ys, xs] = np.minimum(b[ys, xs], 1 - depth * np.sin(np.linspace(0, np.pi, steps)))
speck = filtered_noise(np.exp(-(k / 0.35) ** 2))
b = np.minimum(b, 1 - smoothstep(0.78, 0.86, speck) * 0.8)


def save(name, rgb):
    img = bpy.data.images.new(name, N, N, alpha=True)
    img.colorspace_settings.name = "Non-Color"
    px = np.ones((N, N, 4), np.float32)
    px[..., :3] = rgb
    img.pixels.foreach_set(px.ravel())
    img.filepath_raw = os.path.join(out_dir, name + ".png")
    img.file_format = "PNG"
    img.save()
    print(f"[grunge] wrote {img.filepath_raw}")


save("T_HUD_Grunge", np.stack([r, g, b], -1))
mix = r * g * b
save("T_HUD_Grunge_Preview", np.stack([mix, mix, mix], -1))
print(f"[grunge] intact fraction (mix > 0.5): {(mix > 0.5).mean():.2f}")
