"""Headless: exports the AK's stockless mesh (for converting the M4's left-hand angle into its root frame)."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project as P  # noqa: E402
import uelib as U  # noqa: E402


def body(info):
    U.export_asset("/Game/AK74U/SK_KA74U_Stockless", os.path.join(P.DIR, "AK.fbx"), info)


U.run("AKEXPORT", os.path.join(P.DIR, "export_ak.json"), body)
