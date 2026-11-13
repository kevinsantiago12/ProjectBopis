"""Gives the rifles the star flash (SM_MuzzleFlash_Star, from make_ue.py); every other gun keeps SM_MuzzleFlash,
the round base. Headless, with the editor closed (it has the Blueprints loaded):

    .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\FX\\MuzzleFlash\\set_guns_ue.py

Sets the class default FlashMesh, compiles and saves, then reads it back ("[FLASH]" lines in the log)."""
import os
import sys

import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "..", "AnimAuthoring", "lib"))
import uelib as U  # noqa: E402

BPS = "/Game/ThirdPerson/Blueprints/"
STAR = "/Game/ThirdPerson/FX/MuzzleFlash/SM_MuzzleFlash_Star"
RIFLES = ["BP_AssaultRifle", "BP_AssaultCarbine"]     # the M4 and the AK


def log(msg):
    U.log("FLASH", msg)


def cdo_of(name):
    return unreal.get_default_object(unreal.load_object(None, "%s%s.%s_C" % (BPS, name, name)))


def main():
    star = unreal.load_asset(STAR)
    if not star:
        log("ERROR no %s: run make_ue.py first" % STAR)
        return
    for name in RIFLES:
        bp = unreal.load_asset(BPS + name)
        cdo_of(name).set_editor_property("flash_mesh", star)
        unreal.BlueprintEditorLibrary.compile_blueprint(bp)
        unreal.EditorAssetLibrary.save_asset(BPS + name, only_if_is_dirty=False)
        mesh = cdo_of(name).get_editor_property("flash_mesh")
        log("%s: FlashMesh %s" % (name, mesh.get_path_name() if mesh else None))


try:
    main()
except Exception:
    import traceback
    log("ERROR " + traceback.format_exc())
