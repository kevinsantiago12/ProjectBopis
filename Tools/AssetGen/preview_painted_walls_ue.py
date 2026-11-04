"""Headless, saves nothing: renders the paint materials under a real light, in a throwaway map, using the Favela wall tile.
Writes to Saved/AssetGen/preview/:
- paint_sheet.png: top two rows the wall material in every colour, bottom two rows the decal in every colour on plain
  concrete tiles, so the two can be compared colour for colour.
- paint_close.png: three plain concrete tiles, a decal crossing the seam between two of them, then two wall-material tiles
  in the same colour. This is what the decal is for, and whether it matches the wall material.
- paint_detail_decal.png, paint_detail_wall.png: closer, at about the player's distance: the decal's edge on concrete, and
  plain concrete next to the wall material.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\AssetGen\\preview_painted_walls_ue.py -Render"""
import os

import unreal

MATS = "/Game/ThirdPerson/BackAlleys/Materials/"
TILE = "/Game/Megapack/Meshes/Favela/SM_Wall_Tile_01"
OUT = os.path.join(unreal.Paths.project_saved_dir(), "AssetGen", "preview")
COLOURS = ("White", "Cream", "Yellow", "Peach", "Salmon", "Pink", "Mint", "AppleGreen", "SkyBlue", "Teal", "Lavender",
           "Terracotta")
EXPOSURE = 10.0
TW, TH = 225.0, 300.0   # tile: runs along +X from its pivot, outside face at local y = 0, facing +Y
mel = unreal.MaterialEditingLibrary


def say(msg):
    unreal.log_warning("[PREVIEW] " + msg)


os.makedirs(OUT, exist_ok=True)
unreal.EditorLoadingAndSavingUtils.new_blank_map(False)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
ell = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
# Nothing ticks a commandlet, so textures must build now (else: Unreal's grey checker placeholder) and load every mip up
# front. Changed in memory only, never saved.
unreal.SystemLibrary.execute_console_command(world, "Editor.AsyncTextureCompilation 0")
for t in ("T_Concrete_01_BC", "T_Concrete_01_N", "T_Concrete_01_ORM", "T_Wall_H", "T_BackAlleys_PaintChips", "T_decal_02"):
    unreal.load_asset("/Game/ThirdPerson/BackAlleys/Textures/" + t).set_editor_property("never_stream", True)
tile_mesh = unreal.load_asset(TILE)
wall_master = unreal.load_asset(MATS + "M_BackAlleys_PaintedWall")
for m in (wall_master, unreal.load_asset(MATS + "M_BackAlleys_PaintDecal")):
    mel.get_statistics(m)   # finishes compiling, else the shot shows the default material's checker
# Plain concrete: the wall material with no paint, the same T_Concrete_01 and tint as MI_BackAlleys_Concrete. Not that
# instance itself: it has no cached shader map for a headless run, and compiling one takes many minutes of full CPU.
concrete = unreal.MaterialLibrary.create_dynamic_material_instance(world, wall_master)
concrete.set_scalar_parameter_value("Wear", 1.0)


def tile(x, z, mat):
    a = ell.spawn_actor_from_class(unreal.StaticMeshActor, unreal.Vector(x, 0, z))
    c = a.static_mesh_component
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    c.set_static_mesh(tile_mesh)
    for i in range(tile_mesh.get_num_sections(0)):
        c.set_material(i, mat)
    return a


def decal(cx, cz, width, height, mat):
    """Projects into the wall. Decal axes: X depth, Y and Z the image; yaw -90 points X at the wall (-Y)."""
    a = ell.spawn_actor_from_class(unreal.DecalActor, unreal.Vector(cx, 0, cz), unreal.Rotator(0, 0, -90))
    c = a.get_editor_property("decal")
    c.set_editor_property("decal_size", unreal.Vector(6, width / 2.0, height / 2.0))
    c.set_decal_material(mat)
    c.set_editor_property("fade_screen_size", 0.0)
    return a


def light(pitch, yaw, intensity):
    a = ell.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 2000), unreal.Rotator(0, pitch, yaw))
    c = a.get_component_by_class(unreal.DirectionalLightComponent)
    c.set_mobility(unreal.ComponentMobility.MOVABLE)
    c.set_editor_property("intensity", intensity)
    return a


# A sun raking across the wall from upper left (the wall faces +Y), plus a weak fill so shade isn't black.
light(-40, -60, 6.0)
light(-10, -110, 1.2)

# Sheet: 6 columns, 4 rows, away from the close-up.
SX, SZ = 0.0, 0.0
for i, name in enumerate(COLOURS):
    col, row = i % 6, i // 6
    tile(SX + col * TW, SZ + (3 - row) * TH, unreal.load_asset(MATS + "MI_BackAlleys_PaintedWall_" + name))
    tile(SX + col * TW, SZ + (1 - row) * TH, concrete)
    decal(SX + (col + 0.5) * TW, SZ + (1 - row + 0.5) * TH, TW * 1.12, TH * 1.12,
          unreal.load_asset(MATS + "MI_BackAlleys_PaintDecal_" + name))

# Close-up: well away from the sheet.
CX, CZ, MAT = 5000.0, 0.0, "Mint"
for i in range(3):
    tile(CX + i * TW, CZ, concrete)
decal(CX + 1.1 * TW, CZ + 0.5 * TH, 1.5 * TW, TH * 1.12, unreal.load_asset(MATS + "MI_BackAlleys_PaintDecal_" + MAT))
for i in range(3, 5):
    tile(CX + i * TW, CZ, unreal.load_asset(MATS + "MI_BackAlleys_PaintedWall_" + MAT))


def capture(name, width, height, loc, rot, ortho=None, fov=None):
    rt = unreal.RenderingLibrary.create_render_target2d(world, width, height, unreal.TextureRenderTargetFormat.RTF_RGBA8)
    a = ell.spawn_actor_from_class(unreal.SceneCapture2D, loc, rot)
    c = a.capture_component2d
    c.set_editor_property("texture_target", rt)
    c.set_editor_property("capture_source", unreal.SceneCaptureSource.SCS_FINAL_COLOR_LDR)
    if ortho:
        c.set_editor_property("projection_type", unreal.CameraProjectionMode.ORTHOGRAPHIC)
        c.set_editor_property("ortho_width", ortho)
    if fov:
        c.set_editor_property("fov_angle", fov)
    pp = c.get_editor_property("post_process_settings")
    pp.set_editor_property("override_auto_exposure_method", True)
    pp.set_editor_property("auto_exposure_method", unreal.AutoExposureMethod.AEM_MANUAL)
    pp.set_editor_property("override_auto_exposure_bias", True)
    pp.set_editor_property("auto_exposure_bias", EXPOSURE)
    c.set_editor_property("post_process_settings", pp)
    c.set_editor_property("post_process_blend_weight", 1.0)
    for _ in range(4):   # first frames can miss streamed mips
        c.capture_scene()
    unreal.RenderingLibrary.export_render_target(world, rt, OUT, name)
    say("%s written: %s" % (name, os.path.exists(os.path.join(OUT, name))))


# The camera looks along -Y at the wall; yaw -90.
capture("paint_sheet.png", 1350, 1200, unreal.Vector(SX + 3 * TW, 1500, SZ + 2 * TH), unreal.Rotator(0, 0, -90), ortho=6 * TW)
capture("paint_close.png", 1500, 440, unreal.Vector(CX + 2.5 * TW, 680, CZ + 0.5 * TH), unreal.Rotator(0, 0, -90), fov=80)
capture("paint_detail_decal.png", 1000, 600, unreal.Vector(CX + 1.85 * TW, 280, CZ + 170), unreal.Rotator(0, 0, -90), fov=80)
capture("paint_detail_wall.png", 1000, 600, unreal.Vector(CX + 3.0 * TW, 280, CZ + 170), unreal.Rotator(0, 0, -90), fov=80)
