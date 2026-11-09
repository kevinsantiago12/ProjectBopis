# Bridge-side placer for gen_level.py output: the body of one ProgrammaticToolset.execute_tool_script call.
# read_file caps at 80 KB and a call shouldn't run too long, so the plan is placed over several calls. Set the three
# constants for each call:
#   CLEAR  True on the first call only: removes everything under BackAlleys/ except BackAlleys/Gameplay.
#   CHUNKS the plan3_<n>.json files this call places.
#   GAMEPLAY True on the last call: applies plan3_gameplay.json (spawns, start, pickups, wander points, music, floor and
#          volume sizes), traces the checks and saves.
# History: recovered from the 2026-11-02 build (session "Current Coding Work"); 2026-11-03 adds per-slot material
# overrides ("mats"), decals ("decal") and no duplicate wander points on a re-run.
import json
CLEAR = True
CHUNKS = [0, 1, 2, 3]
GAMEPLAY = False
S = 'editor_toolset.toolsets.scene.SceneTools.'
A = 'editor_toolset.toolsets.actor.ActorTools.'
O = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
DIR = 'C:/Users/kevin/Documents/Unreal Projects/ProjectBopis/Saved/BackAlleys/'
LVL = '/Game/ThirdPerson/Lvl_BackAlleys_Arena.Lvl_BackAlleys_Arena:PersistentLevel.'
INTERIOR = '/Game/ThirdPerson/BackAlleys/MI_BackAlleys_Interior'


def rv(r):
    r = r['returnValue'] if isinstance(r, dict) and 'returnValue' in r else r
    return json.loads(r) if isinstance(r, str) and r[:1] in '[{' else r


def call(n, args):
    return rv(execute_tool(n, json.dumps(args)))


def v(a):
    return {'x': a[0], 'y': a[1], 'z': a[2]}


def obj(p):
    return {'refPath': p + '.' + p.split('/')[-1]}


def down(x, y, z0=1200):
    d = call(S + 'trace_world', {'start': v([x, y, z0]), 'end': v([x, y, -100])})
    return None if d is None else round(z0 - d)


def xform(p):
    return {'location': v(p['loc']), 'rotation': {'pitch': p['rot'][0], 'yaw': p['rot'][1], 'roll': p['rot'][2]},
            'scale': v(p['scale'])}


def place_light(p):
    """A static light: the plan's "light" holds its settings. Static so the bake carries it and it costs nothing at run time."""
    li = p['light']
    a = call(S + 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.' + li['kind']}, 'name': p['label'], 'xform': xform(p)})
    call(A + 'set_label', {'actor': a, 'label': p['label']})
    call(S + 'set_actor_folder', {'actor': a, 'folder_path': p['folder']})
    comp = [c for c in call(A + 'get_components', {'actor': a}) if 'LightComponent' in c['refPath']][0]
    vals = {'Mobility': 'Static', 'Intensity': li['intensity'], 'AttenuationRadius': li['radius'], 'SourceRadius': li['source'],
            'LightColor': {'r': li['colour'][0], 'g': li['colour'][1], 'b': li['colour'][2], 'a': 1.0}}    # lowercase, 0..1: capitals are ignored silently
    if li.get('length'):
        vals['SourceLength'] = li['length']
    if li['kind'] == 'SpotLight':
        vals['OuterConeAngle'] = li['outer']
        vals['InnerConeAngle'] = li['outer'] * 0.55
    call(O + 'set_properties', {'instance': comp, 'values': json.dumps(vals)})


def place(p):
    if p.get('light'):
        place_light(p)
        return
    if p['decal']:
        a = call(S + 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.DecalActor'},
                                                  'name': p['label'], 'xform': xform(p)})
    else:
        a = call(S + 'add_to_scene_from_asset', {'asset_path': p['asset'], 'name': p['label'], 'xform': xform(p)})
    call(A + 'set_label', {'actor': a, 'label': p['label']})
    call(S + 'set_actor_folder', {'actor': a, 'folder_path': p['folder']})
    if p['decal']:
        comp = [c for c in call(A + 'get_components', {'actor': a}) if 'Decal' in c['refPath']][0]
        call(O + 'set_properties', {'instance': comp, 'values': json.dumps({'DecalMaterial': obj(p['asset'])})})
        return
    if p['nocoll'] or p.get('coll') or p.get('phys') or p['mat'] or p['vol'] or p['mats'] or p.get('draw') or p.get('noshadow') or p.get('physics') or p.get('weld_to'):
        comp = [c for c in call(A + 'get_components', {'actor': a}) if 'StaticMesh' in c['refPath']][0]
        vals = {}
        if p['mats']:
            vals['OverrideMaterials'] = [obj(m) for m in p['mats']]
        if p['mat'] == 'interior':
            vals['OverrideMaterials'] = [obj(INTERIOR)]
        if p['mat'] == 'hidden':
            vals.update({'bVisible': False, 'bHiddenInGame': True, 'CastShadow': False})
        if p['nocoll']:
            vals['BodyInstance'] = {'collisionProfileName': 'NoCollision'}
            vals['bUseDefaultCollision'] = False     # left on, the component keeps the mesh's own collision and ignores the preset
        if p.get('coll'):
            vals['BodyInstance'] = {'collisionProfileName': p['coll']}
            vals['bUseDefaultCollision'] = False
        if p.get('phys'):
            vals.setdefault('BodyInstance', {})['physMaterialOverride'] = obj(p['phys'])     # a surface for this piece alone, when its material is shared
        if p['vol']:
            vals['LightmapType'] = 'ForceVolumetric'
        if p.get('nonav'):
            vals['bCanEverAffectNavigation'] = False
        if p.get('physics') or p.get('weld_to'):
            # A loose prop a shot or a blast moves (user 2026-11-07: "I want bullets to affect them", "only light things"). Movable, asleep until hit, out of the nav mesh and with no overlap
            # events, which is what made the shell casings expensive in trace 24. A welded piece (weld_to) doesn't simulate: it rides its parent, attached after placing.
            # Mobility goes first: the keys are set in order, and setting Mobility re-picks a default profile from mobility and simulate (FBodyInstanceEditorHelpers), which turned
            # a lid's PhysicsActor into BlockAllDynamic when it came after BodyInstance.
            m = {'Mobility': 'Movable'}
            m.update(vals)
            vals = m
            vals['bGenerateOverlapEvents'] = False
            vals['bCanEverAffectNavigation'] = False
            vals['bUseDefaultCollision'] = False
            bi = vals.setdefault('BodyInstance', {})
            if not p['nocoll']:     # a pot's plant has no collision: it's only attached, and rides the pot
                bi['collisionProfileName'] = 'PhysicsActor'
            if p.get('physics'):
                bi['bSimulatePhysics'] = True
                bi['bStartAwake'] = False
                bi['bOverrideMass'] = True
                bi['massInKgOverride'] = p['physics']
                if p.get('cap'):
                    # Caps (user 2026-11-07: "cap their velocity"): how fast it's pushed out of an overlap (cm/s), and how fast it may spin (deg/s)
                    bi['bOverrideMaxDepenetrationVelocity'] = True
                    bi['maxDepenetrationVelocity'] = p['cap'][0]
                    bi['bOverrideMaxAngularVelocity'] = True
                    bi['maxAngularVelocity'] = p['cap'][1]
        if p.get('noshadow'):
            vals['CastShadow'] = False
        if p.get('draw'):
            vals['LDMaxDrawDistance'] = p['draw']      # cull distance: laundry, street dressing
        if p.get('seed') is not None:     # a monobloc piece's colour, picked once: 'Spawn Seed' in MF_PerInstanceColor reads custom primitive data 0
            vals['CustomPrimitiveData'] = {'data': [p['seed']]}
        call(O + 'set_properties', {'instance': comp, 'values': json.dumps(vals)})
    return a


def weld(out, todo, placed):
    # A welded piece (weld_to, a bucket's lid) is attached root to root to its parent and doesn't simulate. bAutoWeld, on by default, welds the two bodies into one when the game
    # starts (FBodyInstance::InitBody), so the lid rides the bucket. The parent comes before its lid in the plan, so it was placed earlier in this call, or in an earlier one.
    need = [p['weld_to'] for p in todo if p['weld_to'] not in placed]
    folders = []
    for p in todo:
        if need and p['folder'] not in folders:
            folders.append(p['folder'])
    for f in folders:
        for a in call(S + 'get_actors_in_folder', {'folder_path': f, 'recursive': True}):
            lab = call(A + 'get_label', {'actor': a})
            if lab in need:
                placed[lab] = a
    out['welded'] = 0
    for p in todo:
        par = placed.get(p['weld_to'])
        child = placed.get(p['label'])
        if par and child and call(A + 'set_parent_component', {'component': call(A + 'get_root_component', {'actor': child}),
                                                                 'parent': call(A + 'get_root_component', {'actor': par})}):
            out['welded'] += 1
        else:
            out['fail'].append([p['label'], 'not welded to ' + p['weld_to']])


def gameplay(out):
    g = call(AS + 'read_file', {'file_path': DIR + 'plan3_gameplay.json'})
    sp = {}
    for s in g['spawns']:
        a = call(S + 'find_actors', {'name': s['label'], 'tag': '', 'collision_channels': []})[0]
        call(A + 'set_actor_transform', {'actor': a, 'xform': {'location': v(s['loc']),
                                                                'rotation': {'pitch': 0, 'yaw': s['yaw'], 'roll': 0}}})
        sp[s['label'][-2:]] = [down(s['loc'][0], s['loc'][1], 300),
                               call(S + 'trace_world', {'start': v([s['loc'][0], s['loc'][1], 100]),
                                                        'end': v([s['loc'][0], s['loc'][1], 350])})]
    out['spawns'] = sp
    call(A + 'set_actor_transform', {'actor': {'refPath': LVL + 'PlayerStart_0'},
                                     'xform': {'location': v(g['player_start']), 'rotation': {'pitch': 0, 'yaw': 0, 'roll': 0}}})
    out['start_ground'] = down(g['player_start'][0], g['player_start'][1], 300)
    pk = {}
    for p in g['pickups']:
        a = call(S + 'add_to_scene_from_asset', {'asset_path': p['asset'], 'name': p['label'], 'xform': {'location': v(p['loc'])}})
        call(A + 'set_label', {'actor': a, 'label': p['label']})
        call(S + 'set_actor_folder', {'actor': a, 'folder_path': 'BackAlleys/Pickups'})
        if p['weapon']:
            cls = p['weapon'] + '.' + p['weapon'].split('/')[-1] + '_C'
            call(O + 'set_properties', {'instance': a, 'values': json.dumps({'WeaponClass': {'refPath': cls}})})
        pk[p['label'][7:]] = down(p['loc'][0], p['loc'][1], p['loc'][2] + 50)
    out['pickups'] = pk
    for w in g['wander']:
        if call(S + 'find_actors', {'name': w['label'], 'tag': '', 'collision_channels': []}):
            continue
        a = call(S + 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.TargetPoint'}, 'name': w['label'],
                                                  'xform': {'location': v(w['loc'])}})
        call(A + 'set_label', {'actor': a, 'label': w['label']})
        call(S + 'set_actor_folder', {'actor': a, 'folder_path': 'BackAlleys/Gameplay'})
    m = g['music']
    if m['label'] not in [call(A + 'get_label', {'actor': a}) for a in
                          call(S + 'get_actors_in_folder', {'folder_path': 'BackAlleys/Gameplay', 'recursive': True})]:
        a = call(S + 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/ProjectBopis.MusicTrigger'},
                                                  'name': m['label'], 'xform': {'location': v(m['loc'])}})
        call(A + 'set_label', {'actor': a, 'label': m['label']})
        call(S + 'set_actor_folder', {'actor': a, 'folder_path': 'BackAlleys/Gameplay'})
        call(O + 'set_properties', {'instance': a, 'values': json.dumps({'Track': obj(m['track']), 'bPlayAtStart': True})})
    call(A + 'set_actor_transform', {'actor': {'refPath': LVL + 'Floor_0'},
                                     'xform': {'location': v(g['floor']['loc']), 'scale': v(g['floor']['scale'])}})
    for a in call(S + 'find_actors', {'name': '', 'tag': '', 'collision_channels': []}):
        p = a['refPath']
        if 'NavMeshBoundsVolume' in p:
            call(A + 'set_actor_transform', {'actor': a, 'xform': {'location': v(g['nav']['loc']), 'scale': v(g['nav']['scale'])}})
        elif 'LightmassImportanceVolume' in p:
            call(A + 'set_actor_transform', {'actor': a, 'xform': {'location': v(g['lmv']['loc']), 'scale': v(g['lmv']['scale'])}})
    out['stairs'] = [down(-350, -1050), down(-50, -1050), down(150, -1050), down(-350, -150), down(150, -150)]
    out['deck'] = down(-450, -600)
    out['save'] = call(AS + 'save_assets', {'asset_paths': []})


def run():
    out = {'removed': 0, 'placed': 0, 'fail': []}
    if CLEAR:
        keep = set(a['refPath'] for a in call(S + 'get_actors_in_folder', {'folder_path': 'BackAlleys/Gameplay', 'recursive': True}))
        for a in call(S + 'get_actors_in_folder', {'folder_path': 'BackAlleys', 'recursive': True}):
            if a['refPath'] not in keep and call(S + 'remove_from_scene', {'actor': a}):
                out['removed'] += 1
    placed, todo = {}, []
    for i in CHUNKS:
        for p in call(AS + 'read_file', {'file_path': DIR + 'plan3_%d.json' % i}):
            try:
                placed[p['label']] = place(p)
                out['placed'] += 1
                if p.get('weld_to'):
                    todo.append(p)
            except Exception as e:
                out['fail'].append([p['label'], str(e)[:120]])
    if todo:
        weld(out, todo, placed)
    if GAMEPLAY:
        gameplay(out)
    return out
