# Headless, one-off (2026-11-07). Builds the main menu as a hub plus scenes:
#   1. copies Lvl_BackAlleys_Arena to Lvl_MenuScene_BackAlley (scene 1) and checks its actor files came along;
#   2. strips the gameplay actors from the scene (same rule as strip_gameplay_ue.py) and saves;
#   3. makes an empty Lvl_MainMenu, not World Partition: the hub the scenes load into as level instances.
# Run with Tools/AnimAuthoring/RunUnreal.ps1, with neither map loaded in the open editor.
# Never rename these maps headless: a headless rename_asset moved the .umap but left its actor files behind
# (2026-11-07). Renames go through the editor, which moves the __ExternalActors__ folder with the map.
import os
import unreal

SRC = '/Game/ThirdPerson/Lvl_BackAlleys_Arena'
SCENE = '/Game/ThirdPerson/Lvl_MenuScene_BackAlley'
HUB = '/Game/ThirdPerson/Lvl_MainMenu'
ACTORS = os.path.join(unreal.Paths.project_content_dir(), '__ExternalActors__', 'ThirdPerson')
ENGINE_GAMEPLAY = ('PlayerStart', 'NavMeshBoundsVolume', 'RecastNavMesh', 'NavModifierVolume', 'KillZVolume',
                   'TriggerBox', 'TriggerVolume', 'BlockingVolume', 'AmbientSound', 'AbstractNavData')


def log(s):
    unreal.log('[HUB] ' + s)


def actor_files(name):
    n = 0
    for _, _, files in os.walk(os.path.join(ACTORS, name)):
        n += len([f for f in files if f.endswith('.uasset')])
    return n


eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def run():
    if eal.does_asset_exist(HUB):
        log('ABORT: the hub already exists; clear it first')
        return
    src_n = actor_files('Lvl_BackAlleys_Arena')
    if not eal.does_asset_exist(SCENE):
        # Headless duplicate_asset loses the actor files too (2026-11-07): make the copy in the editor (the
        # bridge's AssetTools.duplicate, then save) and this step is skipped.
        eal.duplicate_asset(SRC, SCENE)
        eal.save_asset(SCENE, False)
        unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False)
    scene_n = actor_files('Lvl_MenuScene_BackAlley')
    log('actor files: source %d, scene %d' % (src_n, scene_n))
    if scene_n < src_n - 5:
        log('ABORT: the copy lost its actor files; do the copy in the editor instead')
        return

    unreal.EditorLoadingAndSavingUtils.load_map(SCENE)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    actors = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    gone = []
    for a in actors:
        cpath = a.get_class().get_path_name()
        if str(a.get_folder_path()).startswith('BackAlleys/Gameplay') or cpath.startswith('/Script/ProjectBopis') or \
                cpath.startswith('/Game/ThirdPerson/Blueprints') or a.get_class().get_name() in ENGINE_GAMEPLAY:
            gone.append(a)
            log('GO %s | %s' % (a.get_actor_label(), cpath))
    log('scene actors %d, removing %d' % (len(actors), len(gone)))
    unreal.get_editor_subsystem(unreal.EditorActorSubsystem).destroy_actors(gone)
    unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, False)
    log('scene actor files after strip %d' % actor_files('Lvl_MenuScene_BackAlley'))

    try:
        ok = les.new_level(HUB, False)     # is_partitioned_world = False
    except TypeError:
        ok = les.new_level(HUB)
    log('hub made %s, saved %s, exists %s' % (ok, les.save_current_level(), eal.does_asset_exist(HUB)))


run()
