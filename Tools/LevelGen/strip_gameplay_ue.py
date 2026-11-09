# Headless. Strips the gameplay actors from a copy of Lvl_BackAlleys_Arena (Lvl_MainMenu, the main menu's scene).
# Run with Tools/AnimAuthoring/RunUnreal.ps1. DELETE False lists what would go; True deletes and saves.
# Gameplay = anything in the BackAlleys/Gameplay folder, plus any actor of a project class (/Script/ProjectBopis or
# a Blueprint under /Game/ThirdPerson/Blueprints) or of the gameplay engine classes below, wherever it stands.
import unreal

MAP = '/Game/ThirdPerson/Lvl_MenuScene_BackAlley'   # never the hub
DELETE = False
ENGINE_GAMEPLAY = ('PlayerStart', 'NavMeshBoundsVolume', 'RecastNavMesh', 'NavModifierVolume', 'KillZVolume',
                   'TriggerBox', 'TriggerVolume', 'BlockingVolume', 'AmbientSound', 'AbstractNavData')


def log(s):
    unreal.log('[STRIP] ' + s)


unreal.EditorLoadingAndSavingUtils.load_map(MAP)
world = unreal.EditorLevelLibrary.get_editor_world()
actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
log('actors %d' % len(actors))
gone = []
for a in actors:
    folder = str(a.get_folder_path())
    cls = a.get_class()
    cpath = cls.get_path_name()
    name = cls.get_name()
    hit = folder.startswith('BackAlleys/Gameplay') or cpath.startswith('/Script/ProjectBopis') or \
        cpath.startswith('/Game/ThirdPerson/Blueprints') or name in ENGINE_GAMEPLAY
    if hit:
        gone.append(a)
        log('GO %s | %s | %s' % (a.get_actor_label(), cpath, folder))
log('to remove %d' % len(gone))
# Every class in the level, so nothing gameplay-ish under an unexpected class slips past.
counts = {}
for a in actors:
    k = a.get_class().get_path_name()
    counts[k] = counts[k] + 1 if k in counts else 1
for k in sorted(counts):
    log('CLASS %5d %s' % (counts[k], k))
if DELETE:
    sub = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
    sub.destroy_actors(gone)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False)
    log('deleted and saved')
