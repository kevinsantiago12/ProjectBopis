"""Read-only: can the AI get through every swing door? On a level's saved navmesh, a path from 1.2 m in front of
each ASwingDoor to 1.2 m behind it. A full path is about 240 cm; "partial" means the navmesh stops at the door
(its nav link missing from the saved navmesh: Build Paths and save the level).

    .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\LevelGen\\analysis\\check_door_nav_ue.py

Fine with the editor open (it saves nothing). Results: "[NAV]" lines in check_door_nav_ue_log.txt."""
import unreal

MAP = "/Game/ThirdPerson/Lvl_01_Slum"


def log(m):
    unreal.log_warning("[NAV] " + str(m))


unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()

door_cls = unreal.load_class(None, "/Script/ProjectBopis.SwingDoor")
doors = unreal.GameplayStatics.get_all_actors_of_class(world, door_cls)
bad = 0
for d in doors:
    c = d.get_actor_location()
    y = d.get_actor_transform().rotation.rotate_vector(unreal.Vector(0, 1, 0))     # through the doorway
    a, b = c + y * 120.0 + unreal.Vector(0, 0, 20), c - y * 120.0 + unreal.Vector(0, 0, 20)
    path = unreal.NavigationSystemV1.find_path_to_location_synchronously(world, a, b)
    partial = path.is_partial() if path else True
    length = path.get_path_length() if path else -1.0
    ok = path is not None and not partial and length < 400.0
    bad += 0 if ok else 1
    log("%s %s: partial=%s, length %.0f cm (straight 240)" % ("OK  " if ok else "FAIL", d.get_actor_label(), partial, length))
log("%d doors, %d blocked" % (len(doors), bad))
