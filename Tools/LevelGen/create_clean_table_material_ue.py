"""Headless, new assets only: a clean instance of the market pack's table. User 2026-11-06: "the table texture is a filthy texture, create a new instance of it where its not filthy".
The colour texture is clean: T_Table_01_BC is a grey top and light wood legs. Two things made it look filthy:
- MM_BasicProp lays near-black wear over it through T_Table_01_WTT (Wear Strength 0.74), and a dark brown tint. Turned down here.
- The top is metal: T_Table_01_ORM is high in blue and low in green there, so it mirrors whatever is around it, and with no sky in an alley that's dark marbling. Turning the wear down alone left that, so
  T_BackAlleys_Table_ORM, one flat matte value, replaces it: no occlusion, roughness 0.72, no metal.
MI_BackAlleys_Table_Clean is a child of MI_Table_01. The pack's own instance and textures aren't touched. An instance that already exists is left alone, as a headless run can't change what the open editor
has loaded: set the ORM through the bridge then. Values are read back in the log: the calls can return False even when they take.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_clean_table_material_ue.py"""
import os
import struct
import zlib

import unreal

MATS = "/Game/ThirdPerson/BackAlleys/Materials"
TEXS = "/Game/ThirdPerson/BackAlleys/Textures"
NAME = "MI_BackAlleys_Table_Clean"
TEX = "T_BackAlleys_Table_ORM"
ORM = (255, 220, 0)      # the pack samples its ORM as sRGB, so 220 reads as roughness 0.72
VALUES = {"Wear Strength": 0.06, "Tint 01 Strength": 0.22, "Tint 02 Strength": 0.12}
TINT = (0.42, 0.41, 0.39)      # the matte top comes out near white in sun without this
mel = unreal.MaterialEditingLibrary
eal = unreal.EditorAssetLibrary
tools = unreal.AssetToolsHelpers.get_asset_tools()


def flat_png(path, rgb, size=8):
    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xffffffff)
    row = b"\0" + bytes(rgb) * size
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n" + chunk(b"IHDR", struct.pack(">IIBBBBB", size, size, 8, 2, 0, 0, 0)) + chunk(b"IDAT", zlib.compress(row * size)) + chunk(b"IEND", b""))


tex_path = TEXS + "/" + TEX
if not eal.does_asset_exist(tex_path):
    png = os.path.join(unreal.Paths.project_saved_dir(), "LevelGen", TEX + ".png")
    flat_png(png, ORM)
    task = unreal.AssetImportTask()
    task.filename = png
    task.destination_path = TEXS
    task.destination_name = TEX
    task.automated = True
    task.save = True
    task.replace_existing = True
    tools.import_asset_tasks([task])
    t = unreal.load_asset(tex_path)
    old = unreal.load_asset("/Game/Philippines_Markets/Textures/T_Table_01_ORM")
    t.set_editor_property("compression_settings", old.get_editor_property("compression_settings"))
    t.set_editor_property("srgb", old.get_editor_property("srgb"))
    eal.save_loaded_asset(t)
    unreal.log_warning("[CLEANTABLE] %s made, compression %s srgb %s" % (TEX, t.get_editor_property("compression_settings"), t.get_editor_property("srgb")))
path = MATS + "/" + NAME
if eal.does_asset_exist(path):
    unreal.log_warning("[CLEANTABLE] %s exists: left alone" % NAME)
else:
    mi = tools.create_asset(NAME, MATS, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mel.set_material_instance_parent(mi, unreal.load_asset("/Game/Philippines_Markets/Materials/MI_Table_01"))
    for k, v in VALUES.items():
        mel.set_material_instance_scalar_parameter_value(mi, k, v)
    mel.set_material_instance_texture_parameter_value(mi, "ORM Texture", unreal.load_asset(tex_path))
    mel.set_material_instance_vector_parameter_value(mi, "Basecolor Tint", unreal.LinearColor(TINT[0], TINT[1], TINT[2], 1.0))
    mel.update_material_instance(mi)
    eal.save_loaded_asset(mi)
    unreal.log_warning("[CLEANTABLE] %s made, %s" % (NAME, {k: round(mel.get_material_instance_scalar_parameter_value(mi, k), 3) for k in VALUES}))
