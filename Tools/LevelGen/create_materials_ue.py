"""Headless: creates the back-alley wall materials. User 2026-11-03: "we need to use mostly the concrete material. There
are red brick walls that are used, those need to be non-red hollow blocks."

No pack has concrete hollow blocks (CHB). The nearest is MiddleEast's T_Brick_wall (large grey blocks, BC/N/ORM/H),
so it stands in for the blocks:
- MI_BackAlleys_HollowBlock: bare blocks (M_Bricks_01, the Favela simple parent).
- MI_BackAlleys_ConcreteOverBlock / _Paint*OverBlock: Favela's chipped-render parent (M_Bricks_Bland_01) with its red
  brick layer (Second_*) swapped for the blocks. The main wall material is ConcreteOverBlock.
Each copies the surface type (phys material) of MI_Concrete_01. Existing assets are updated, not duplicated.

Run (the editor can stay open: these are new assets): .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\create_materials_ue.py"""
import unreal

DEST = "/Game/ThirdPerson/BackAlleys/Materials"
FT, MT = "/Game/Megapack/Textures/Favela/", "/Game/Megapack/Textures/MiddleEast/"
FM = "/Game/Megapack/Material/Favela/"
BLOCK = {"BC": MT + "T_Brick_wall_BC", "N": MT + "T_Brick_wall_N", "ORM": MT + "T_Brick_wall_ORM"}
FIRST = {"Concrete": "T_Concrete_01", "PaintWhite": "T_plaster_01", "PaintYellow": "T_Wall_yellow_01",
         "PaintBlue": "T_Wall_Blue_01"}

tools = unreal.AssetToolsHelpers.get_asset_tools()
mel = unreal.MaterialEditingLibrary
phys = unreal.load_asset(FM + "MI_Concrete_01").get_editor_property("phys_material")


def say(msg):
    unreal.log_warning("[MAT] " + msg)


def make(name, parent, textures):
    path = DEST + "/" + name
    mi = unreal.load_asset(path) if unreal.EditorAssetLibrary.does_asset_exist(path) else \
        tools.create_asset(name, DEST, unreal.MaterialInstanceConstant, unreal.MaterialInstanceConstantFactoryNew())
    mi.set_editor_property("parent", unreal.load_asset(parent))
    for param, tex in textures.items():
        # Returns False headless (-NoShaderCompile: the parent's parameter info isn't built), but the value is stored:
        # the saved asset references every texture. Check the result in a viewport capture.
        mel.set_material_instance_texture_parameter_value(mi, param, unreal.load_asset(tex))
    if phys:
        mi.set_editor_property("phys_material", phys)
    mel.update_material_instance(mi)
    unreal.EditorAssetLibrary.save_loaded_asset(mi)
    say("%s saved (parent %s)" % (name, parent.split("/")[-1]))


make("MI_BackAlleys_HollowBlock", FM + "M_Bricks_01",
     {"Base Color": BLOCK["BC"], "Normal Map": BLOCK["N"], "AO Roughness Metallic": BLOCK["ORM"]})
for key, first in FIRST.items():
    make("MI_BackAlleys_%sOverBlock" % key, FM + "M_Bricks_Bland_01",
         {"First_BC": FT + first + "_BC", "First_ORM": FT + first + "_ORM", "First_Normal": FT + first + "_N",
          "Second_BC": BLOCK["BC"], "Second_ORM": BLOCK["ORM"], "Second_Normal": BLOCK["N"],
          "Hight_map": FT + "T_Wall_H"})
say("phys material: %s" % (phys.get_path_name() if phys else None))
