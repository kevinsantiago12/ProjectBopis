# Headless (Tools/AnimAuthoring/RunUnreal.ps1), 2026-11-09. Replaces parts of the existing Lvl_01_Slum from the current plan
# and leaves the rest of the map as it is. The user handcrafts this map from 2026-11-09 (Claude-Rules.md §8, Story levels), so
# run it only when the user has said so for that change. What it swaps (map actors out, plan pieces in):
# - SECTIONS: every generated actor (folder Slums/...) in these sections' _Art sublevels. An actor outside the Slums/ folders
#   (the user's own) stays, and is listed.
# - The slum's houses, whole, in whichever section they are (a slum house that faces the compound's yard more than the street
#   went into section 3; one can change section between plans), and the compound houses touching one or a SECTIONS house:
#   their walls, roofs and wedges follow their neighbours'. A house's pieces are those with its id among the label's first
#   three parts (the plan's layout lists the houses: <prefix>layout.json "houses").
# - SWAP_IDS: other names, the same way (the garage roof).
# - Near the seam (within SEAM cm of a swapped piece), the loose pieces of the other sections, those with no house or building
#   id in their label (corner columns, numbered across the level; walls, ground, sidewalks): matched with the plan by shape
#   and place, not label. A map actor with no twin in the plan goes; a plan piece with no twin in the map comes in.
# A dry run (REPLACE_DRY=1 in the environment) only reports, saves nothing, and may run with the editor open: what each part
# would swap, and the house or building pieces near the seam that differ from the plan but aren't swapped. A real run saves
# only the sublevels it changed: close the editor first, a headless run mustn't save what the editor has loaded.
#   python Tools/LevelGen/gen_level.py linear_slums
#   $env:REPLACE_DRY='1'; .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\swap_sections_ue.py; $env:REPLACE_DRY=''
#   .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\swap_sections_ue.py
# SWAP_ONLY=<name>[,<name>...] in the environment swaps only the pieces with those names (no sections, houses or seam): for a
# new kind of piece added to an already swapped map, e.g. SWAP_ONLY=Curb (user 2026-11-09: "cap the curb edge").
# Since 2026-11-09 Lvl_01_Slum is one map (flatten_sections_ue.py): each actor's section is its tag S<n>, and ue_place tags what it
# places. The script finds which kind of map it has. In the one map, placing through the bridge works too.
# Named swap_, not replace_: the runner passes a backslash path, and UE read the "\r" of "\replace_" in it as a carriage return.
import glob
import json
import math
import os
import sys
import unreal

ROOT = 'C:/Users/kevin/Documents/Unreal Projects/ProjectBopis/'
PLAN = ROOT + 'Saved/LinearSlums/'
PREFIX = 'plan_'
MAP = '/Game/ThirdPerson/Lvl_01_Slum'
SUB_DIR = '/Game/ThirdPerson/01_Slum/'
ALL_SECTIONS = 7
GEN_ROOT = 'Slums'
SECTIONS = (1, 2)                   # user 2026-11-09: "first do passes on Sections 1 and 2"
SWAP_IDS = ('GarageRoof',)          # the garage roof, shortened off the drop ("your placement keeps blocking the drop")
SEAM = 300.0
CUBE = '/Game/LevelPrototyping/Meshes/SM_Cube'
PLANE = '/Engine/BasicShapes/Plane'
DRY = os.environ.get('REPLACE_DRY', '') == '1'
ONLY = tuple(x for x in os.environ.get('SWAP_ONLY', '').split(',') if x)
if ONLY:
    SECTIONS, SWAP_IDS = (), ONLY
REPORT = PLAN + 'swap_report.json'
sys.path.insert(0, ROOT + 'Tools/LevelGen')
import ue_place  # noqa: E402

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
SKIP_CLASSES = ('WorldSettings', 'Brush', 'DefaultPhysicsVolume')


def log(s):
    unreal.log('[SWAP] ' + s)


def sub(sec):
    return 'Lvl_01_Slum_S%d_Art' % sec


def generated(a):
    f = str(a.get_folder_path() or '')
    return f == GEN_ROOT or f.startswith(GEN_ROOT + '/')


def ids_of(label):
    return set(label.split('_')[:3])


def rect(asset, loc, rot, scale):
    """The piece's footprint on the ground plan (cm): a corner-pivot cube's box, a plane's square, else 1.5 m round it."""
    x, y = loc[0], loc[1]
    if asset == CUBE and abs(rot[1]) < 0.5 and abs(rot[0]) < 0.5 and abs(rot[2]) < 0.5:
        return (min(x, x + scale[0] * 100.0), min(y, y + scale[1] * 100.0), max(x, x + scale[0] * 100.0), max(y, y + scale[1] * 100.0))
    if asset == PLANE:
        r = max(abs(scale[0]), abs(scale[1])) * 50.0
        return (x - r, y - r, x + r, y + r)
    return (x - 150.0, y - 150.0, x + 150.0, y + 150.0)


def rect_gap(a, b):
    return max(a[0] - b[2], b[0] - a[2], a[1] - b[3], b[1] - a[3], 0.0)


class Near:
    """Which footprints lie within SEAM of the swapped pieces' footprints (a grid of SEAM cells)."""
    def __init__(self, rects):
        self.cells = {}
        for r in rects:
            for i in range(int(math.floor(r[0] / SEAM)), int(math.floor(r[2] / SEAM)) + 1):
                for j in range(int(math.floor(r[1] / SEAM)), int(math.floor(r[3] / SEAM)) + 1):
                    self.cells.setdefault((i, j), []).append(r)

    def __call__(self, r):
        seen = set()
        for i in range(int(math.floor(r[0] / SEAM)) - 1, int(math.floor(r[2] / SEAM)) + 2):
            for j in range(int(math.floor(r[1] / SEAM)) - 1, int(math.floor(r[3] / SEAM)) + 2):
                for q in self.cells.get((i, j), ()):
                    if id(q) not in seen:
                        seen.add(id(q))
                        if rect_gap(r, q) < SEAM:
                            return True
        return False


def actor_shape(a):
    """(asset, loc, rot, scale) of a map actor, as the plan writes them (a decal's asset: its material)."""
    loc, rot, sc = a.get_actor_location(), a.get_actor_rotation(), a.get_actor_scale3d()
    asset = None
    if isinstance(a, unreal.StaticMeshActor):
        m = a.static_mesh_component.static_mesh
        asset = m.get_path_name().split('.')[0] if m else None
    elif isinstance(a, unreal.DecalActor):
        m = a.decal.get_decal_material()
        asset = m.get_path_name().split('.')[0] if m else None
    else:
        asset = a.get_class().get_name()
    return asset, (loc.x, loc.y, loc.z), (rot.pitch, rot.yaw, rot.roll), (sc.x, sc.y, sc.z)


def plan_asset(p):
    return p['light']['kind'] if p.get('light') else p['asset']


def same_shape(s, p):
    asset, loc, rot, sc = s
    if asset != plan_asset(p):
        return False
    if max(abs(loc[k] - p['loc'][k]) for k in range(3)) > 1.0 or max(abs(sc[k] - p['scale'][k]) for k in range(3)) > 0.01:
        return False
    return all(abs(((rot[k] - p['rot'][k]) + 180.0) % 360.0 - 180.0) < 0.5 for k in range(3))


def run():
    rep = {'dry': DRY}
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    items = []
    for f in sorted(glob.glob(PLAN + PREFIX + '[0-9]*.json'), key=lambda s: int(os.path.basename(s)[len(PREFIX):-5])):
        items += json.load(open(f, encoding='utf-8'))
    lay_ = json.load(open(PLAN + PREFIX + 'layout.json', encoding='utf-8'))
    houses, buildings = lay_['houses'], set(lay_['buildings'])

    # Which houses go: the slum's, the ones in SECTIONS, and the compound houses touching either.
    core = set() if ONLY else {bid for bid, h in houses.items() if h['dressed'] or h['sec'] in SECTIONS}
    touching = {bid for bid, h in houses.items() if bid not in core and
                any(min(h['r'][2], houses[c]['r'][2]) - max(h['r'][0], houses[c]['r'][0]) > -0.05 and
                    min(h['r'][3], houses[c]['r'][3]) - max(h['r'][1], houses[c]['r'][1]) > -0.05 for c in core)}
    swap_ids = core | touching | set(SWAP_IDS)
    named = set(houses) | buildings | set(SWAP_IDS)          # labels with one of these belong to a house or a building
    rep['houses swapped outside the sections'] = sorted(b for b in core | touching if houses[b]['sec'] not in SECTIONS)
    log('houses swapped outside the sections: %s (+ %s)' % (rep['houses swapped outside the sections'], list(SWAP_IDS)))

    def plan_swapped(p):
        return p.get('sec') in SECTIONS or bool(ids_of(p['label']) & swap_ids)

    # Section -> its actors: the S<n>_Art sublevel's, or, in the one map (flatten_sections_ue.py, 2026-11-09), those tagged S<n>.
    all_ = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    single = not any(a.get_path_name().startswith(SUB_DIR) for a in all_)
    rep['one map'] = single
    actors = {}
    for a in all_:
        if single:
            secs = [int(str(t)[1:]) for t in a.tags if str(t)[:1] == 'S' and str(t)[1:].isdigit()]
            if secs:
                actors.setdefault(secs[0], []).append(a)
            continue
        path = a.get_path_name()
        for sec in range(1, ALL_SECTIONS + 1):
            if path.startswith(SUB_DIR + sub(sec) + '.'):
                actors.setdefault(sec, []).append(a)
    rep['actors per section'] = {sec: len(actors.get(sec, [])) for sec in range(1, ALL_SECTIONS + 1)}
    log('plan %d pieces; map actors per _Art sublevel %s' % (len(items), rep['actors per section']))
    if any(not actors.get(sec) for sec in range(1, ALL_SECTIONS + 1)):
        rep['abort'] = 'a sublevel is not loaded or empty'
        log('ABORT: ' + rep['abort'])
        json.dump(rep, open(REPORT, 'w'), indent=1)
        return
    rep['kept in the sections'] = {sec: ['%s (%s) %s' % (a.get_actor_label(), a.get_class().get_name(), str(a.get_folder_path() or ''))
                                         for a in actors[sec] if not generated(a) and a.get_class().get_name() not in SKIP_CLASSES]
                                   for sec in SECTIONS}

    # The swap: map actors out, plan pieces in.
    out_ = {sec: [] for sec in actors}
    for sec, acts in actors.items():
        for a in acts:
            if generated(a) and (sec in SECTIONS or ids_of(a.get_actor_label()) & swap_ids):
                out_[sec].append(a)
    in_ = [p for p in items if plan_swapped(p)]
    near = Near([rect(p['asset'], p['loc'], p['rot'], p['scale']) for p in in_])

    # Near the seam: loose pieces matched by shape; house and building pieces that differ, reported.
    loose_map, left = [], []
    by_label = {p['label']: p for p in items}
    for sec, acts in actors.items():
        if sec in SECTIONS:
            continue
        for a in acts:
            if not generated(a) or a in out_[sec]:
                continue
            s = actor_shape(a)
            if not near(rect(s[0], s[1], s[2], s[3])):
                continue
            lab = a.get_actor_label()
            if ids_of(lab) & named:
                p = by_label.get(lab)
                if p is None or p.get('sec') != sec or not same_shape(s, p):
                    left.append('S%d %s' % (sec, lab))
            else:
                loose_map.append((sec, a, s))
    loose_plan = [p for p in items if not plan_swapped(p) and not (ids_of(p['label']) & named) and
                  near(rect(p['asset'], p['loc'], p['rot'], p['scale']))]
    if ONLY:                                        # only the named pieces: no seam to match
        loose_map, loose_plan = [], []
    matched = set()
    for sec, a, s in loose_map:
        twin = next((k for k, p in enumerate(loose_plan) if k not in matched and p.get('sec') == sec and same_shape(s, p)), None)
        if twin is None:
            out_[sec].append(a)
        else:
            matched.add(twin)
    loose_in = [p for k, p in enumerate(loose_plan) if k not in matched]
    in_ += loose_in
    rep['seam'] = {'loose pieces in the map near it': len(loose_map), 'with a twin in the plan': len(matched),
                   'loose map pieces out': ['S%d %s' % (sec, a.get_actor_label()) for sec, a, s in loose_map if a in out_[sec]],
                   'loose plan pieces in': ['S%d %s' % (p.get('sec'), p['label']) for p in loose_in],
                   'house or building pieces near it that differ, left': left}
    rep['out per section'] = {sec: len(v) for sec, v in out_.items() if v}
    rep['in per section'] = {}
    for p in in_:
        rep['in per section'][p.get('sec')] = rep['in per section'].get(p.get('sec'), 0) + 1
    log('out %s; in %s' % (rep['out per section'], rep['in per section']))
    log('seam: %d loose map pieces out, %d loose plan pieces in, %d house/building pieces near it differ (left)' % (
        len(rep['seam']['loose map pieces out']), len(loose_in), len(left)))
    if DRY:
        log('dry run: nothing changed')
        json.dump(rep, open(REPORT, 'w'), indent=1)
        return

    touched = sorted(set(sec for sec, v in out_.items() if v) | set(p.get('sec') for p in in_))
    for sec in touched:
        eas.destroy_actors(out_.get(sec, []))
        les.set_current_level_by_name('Lvl_01_Slum' if single else sub(sec))
        mine = [p for p in in_ if p.get('sec') == sec]
        for p in mine:
            ue_place.try_place(p)
        log('S%d: removed %d, placed %d' % (sec, len(out_.get(sec, [])), len(mine)))
    les.set_current_level_by_name('Lvl_01_Slum')
    rep['placed'], rep['failed'], rep['props failed'], rep['failures'] = ue_place.n['placed'], ue_place.n['failed'], \
        ue_place.n['props failed'], list(ue_place.fail)
    log('placed %d, failed %d, property sets failed %d' % (ue_place.n['placed'], ue_place.n['failed'], ue_place.n['props failed']))
    for f in ue_place.fail:
        log('  ' + f)
    dirty = [str(p.get_name()) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()] + \
        [str(p.get_name()) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_content_packages()]
    rep['dirty before save'] = dirty
    pkgs = [unreal.load_package(MAP)] if single else [unreal.load_package(SUB_DIR + sub(sec)) for sec in touched]
    rep['saved'] = unreal.EditorLoadingAndSavingUtils.save_packages(pkgs, True)
    rep['saved packages'] = [str(p.get_name()) for p in pkgs]
    log('dirty before save %s; saved %s: %s' % (dirty, rep['saved'], rep['saved packages']))
    json.dump(rep, open(REPORT, 'w'), indent=1)


run()
