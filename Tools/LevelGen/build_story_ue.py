# Headless (Tools/AnimAuthoring/RunUnreal.ps1), 2026-11-08. Builds a story level from gen_level.py's plan as the spec's
# streaming plan has it: one small persistent map (not World Partition) and, per section, an _Art and a _Gameplay
# sublevel. Each piece goes into its section's _Art sublevel (the plan's "sec"); the player start into section 1's
# _Gameplay; the nav mesh bounds and the Lightmass importance volume into the persistent map.
#   python Tools/LevelGen/gen_level.py linear_slums      first, for Saved/LinearSlums/plan_*.json
#   .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\build_story_ue.py
# Only makes NEW maps: it stops if the persistent map exists (so it never touches a map the open editor may have). To
# rebuild, delete the maps in the editor first. The sublevels stream as LevelStreamingDynamic, loaded and visible from the
# start until the streaming code exists (spec, Linear levels).
import json
import os
import glob
import sys
import unreal

PLAN = 'C:/Users/kevin/Documents/Unreal Projects/ProjectBopis/Saved/LinearSlums/'
PREFIX = 'plan_'
MAP = '/Game/ThirdPerson/Lvl_01_Slum'
SUB_DIR = '/Game/ThirdPerson/01_Slum/'
SECTIONS = 7
REBUILD = False      # True: try to delete this level's maps first (only while the open editor hasn't loaded them). Headless
#                      delete_asset returned True and left the files (2026-11-08): delete the .umap files by hand if it aborts.
sys.path.insert(0, 'C:/Users/kevin/Documents/Unreal Projects/ProjectBopis/Tools/LevelGen')
import ue_place  # noqa: E402   one plan piece -> one actor (shared with replace_sections_ue.py)

eal = unreal.EditorAssetLibrary
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
setp = ue_place.setp
_n, _fail = ue_place.n, ue_place.fail


def log(s):
    unreal.log('[STORY] ' + s)


def sub_name(sec, kind):
    return 'Lvl_01_Slum_S%d_%s' % (sec, kind)


def run():
    if eal.does_asset_exist(MAP) and REBUILD:
        gone = [MAP + '_BuiltData'] + [SUB_DIR + sub_name(s_, k_) + suf for s_ in range(1, SECTIONS + 1) for k_ in ('Art', 'Gameplay')
                                         for suf in ('', '_BuiltData')]
        for a_ in [MAP] + gone:
            if eal.does_asset_exist(a_):
                log('delete %s: %s' % (a_, eal.delete_asset(a_)))
    if eal.does_asset_exist(MAP):
        log('ABORT: %s exists; delete it (and %s*) in the editor to rebuild' % (MAP, SUB_DIR))
        return
    items = []
    for f in sorted(glob.glob(PLAN + PREFIX + '[0-9]*.json'), key=lambda s: int(os.path.basename(s)[len(PREFIX):-5])):
        items += json.load(open(f, encoding='utf-8'))
    gp = json.load(open(PLAN + PREFIX + 'gameplay.json', encoding='utf-8'))
    log('plan: %d pieces' % len(items))
    try:
        ok = les.new_level(MAP, False)
    except TypeError:
        ok = les.new_level(MAP)
    log('persistent map made: %s' % ok)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    streams = {}
    for sec in range(1, SECTIONS + 1):
        for kind in ('Art', 'Gameplay'):
            st = unreal.EditorLevelUtils.create_new_streaming_level(unreal.LevelStreamingDynamic, SUB_DIR + sub_name(sec, kind), False)
            if st is None:
                log('ABORT: no sublevel %s' % sub_name(sec, kind))
                return
            setp(st, 'initially_loaded', True)
            setp(st, 'initially_visible', True)
            streams[(sec, kind)] = st
    log('sublevels made: %d' % len(streams))
    by_sec = {}
    for p in items:
        by_sec.setdefault(p.get('sec', 1), []).append(p)
    for sec in sorted(by_sec):
        unreal.EditorLevelUtils.make_level_current(streams[(sec, 'Art')])
        for p in by_sec[sec]:
            ue_place.try_place(p)
        log('section %d: %d pieces' % (sec, len(by_sec[sec])))
    # Gameplay: the start in section 1's _Gameplay; the volumes in the persistent map
    unreal.EditorLevelUtils.make_level_current(streams[(1, 'Gameplay')])
    ps = eas.spawn_actor_from_class(unreal.PlayerStart, unreal.Vector(*gp['player_start']), unreal.Rotator(roll=0.0, pitch=0.0, yaw=gp['player_yaw']))
    ps.set_actor_label('PlayerStart')
    ps.set_folder_path('Slums/Gameplay')
    les.set_current_level_by_name('Lvl_01_Slum')
    for key, cls in (('nav', unreal.NavMeshBoundsVolume), ('lmv', unreal.LightmassImportanceVolume)):
        v = eas.spawn_actor_from_class(cls, unreal.Vector(*gp[key]['centre']), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
        v.set_actor_scale3d(unreal.Vector(*[s / 200.0 for s in gp[key]['size']]))     # the default brush is 200 cm a side
        v.set_actor_label('NavMeshBounds' if key == 'nav' else 'LightmassImportance')
        v.set_folder_path('Slums/Gameplay')
    log('placed %d, failed %d, property sets failed %d' % (_n['placed'], _n['failed'], _n['props failed']))
    for f in _fail:
        log('  ' + f)
    saved = unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True)
    log('saved: %s; map %s, sublevels %d' % (saved, eal.does_asset_exist(MAP),
                                             sum(1 for k in streams if eal.does_asset_exist(SUB_DIR + sub_name(*k)))))


run()
