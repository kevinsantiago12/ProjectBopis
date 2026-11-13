"""Read-only, headless: every piece in Lvl_01_Slum that wears a plywood or board material, by section tag and label stem,
so a wood pass can see where the sheets and boards are (user 2026-11-13: "I added a Plywood texture on the content folder. Use
that instead of whatever you are using", "and use less boards on the Alley section"). Nothing is saved.

Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\wood_pieces_ue.py
Writes Saved/LinearSlums/wood_pieces.json."""
import json
import os
import re
import traceback

import unreal

MAP = "/Game/ThirdPerson/Lvl_01_Slum"
OUT = os.path.join(unreal.Paths.project_saved_dir(), "LinearSlums", "wood_pieces.json")
WOOD = re.compile(r"(Ply|Plywood|Boards|Timber|Wood)", re.I)


def say(msg):
    unreal.log_warning("[WOOD] " + msg)


try:
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    pieces = []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.StaticMeshActor):
        smc = a.static_mesh_component
        mesh = smc.static_mesh
        mats = []
        for i in range(smc.get_num_materials()):
            m = smc.get_material(i)
            mats.append(m.get_name() if m else None)
        if not any(m and WOOD.search(m) for m in mats):
            continue
        tags = [str(t) for t in a.tags]
        sec = next((t for t in tags if re.fullmatch(r"S\d", t)), "")
        b = a.get_actor_bounds(False)
        loc, ext = b[0], b[1]
        t = a.get_actor_transform()
        r = t.rotation.rotator()
        ov = smc.get_editor_property("override_materials")
        pieces.append({"label": a.get_actor_label(), "name": a.get_name(), "sec": sec, "folder": str(a.get_folder_path()),
                       "mesh": mesh.get_path_name() if mesh else None, "mats": mats,
                       "override": [m.get_path_name() if m else None for m in ov],
                       "loc": [round(loc.x, 2), round(loc.y, 2), round(loc.z, 2)], "ext": [round(ext.x, 2), round(ext.y, 2), round(ext.z, 2)],
                       "pos": [round(t.translation.x, 3), round(t.translation.y, 3), round(t.translation.z, 3)],
                       "rot": [round(r.pitch, 3), round(r.yaw, 3), round(r.roll, 3)],
                       "scale": [round(t.scale3d.x, 5), round(t.scale3d.y, 5), round(t.scale3d.z, 5)]})
    json.dump(pieces, open(OUT, "w"), indent=0)
    say("%d wood pieces -> %s" % (len(pieces), OUT))
except Exception:
    say("ERROR " + traceback.format_exc())
