# Packs the Benelli's separate AO, roughness and metallic maps into ORM textures (R occlusion,
# G roughness, B metallic) for M_TacticalPistol, at 2048 (Unreal caps them at 1024 anyway).
#   blender --background --factory-startup --python PackORM.py -- <BenelliM4 download dir> <out dir>
# Writes T_Benelli_Body_ORM.png, T_Benelli_Stock_ORM.png and T_Benelli_Shell_ORM.png.
import bpy, sys, os
import numpy as np

src, out_dir = sys.argv[sys.argv.index("--") + 1:][:2]
SIZE = 2048
SETS = {"Body": "Shotgun 2 Body/Body", "Stock": "Shotgun 2 Stock/Stock", "Shell": "Shotgun 2 Bullets/Bullet"}


def channel(path):
    # The map's red channel (they're greyscale), as stored: no colour conversion.
    img = bpy.data.images.load(path)
    img.colorspace_settings.name = 'Non-Color'
    if tuple(img.size) != (SIZE, SIZE):
        img.scale(SIZE, SIZE)
    px = np.empty(SIZE * SIZE * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    bpy.data.images.remove(img)
    return px.reshape(-1, 4)[:, 0]


os.makedirs(out_dir, exist_ok=True)
for name, stem in SETS.items():
    base = os.path.join(src, stem)
    ao, rough, metal = (channel(f"{base}_{m}.png") for m in ("Mixed_AO", "Roughness", "Metallic"))
    out = bpy.data.images.new(f"T_Benelli_{name}_ORM", SIZE, SIZE, alpha=False)
    out.colorspace_settings.name = 'Non-Color'
    out.pixels.foreach_set(np.stack([ao, rough, metal, np.ones_like(ao)], axis=1).ravel())
    out.filepath_raw = os.path.join(out_dir, f"T_Benelli_{name}_ORM.png")
    out.file_format = 'PNG'
    out.save()
    print(f"ORM {name}: AO {ao.mean():.2f}, roughness {rough.mean():.2f}, metallic {metal.mean():.2f}")
