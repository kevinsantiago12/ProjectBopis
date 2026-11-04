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
LVL = '/Game/ThirdPerson/Lvl_BackAlleys.Lvl_BackAlleys:PersistentLevel.'
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


def place(p):
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
    if p['nocoll'] or p['mat'] or p['vol'] or p['mats']:
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
        if p['vol']:
            vals['LightmapType'] = 'ForceVolumetric'
        call(O + 'set_properties', {'instance': comp, 'values': json.dumps(vals)})


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
    for i in CHUNKS:
        for p in call(AS + 'read_file', {'file_path': DIR + 'plan3_%d.json' % i}):
            try:
                place(p)
                out['placed'] += 1
            except Exception as e:
                out['fail'].append([p['label'], str(e)[:120]])
    if GAMEPLAY:
        gameplay(out)
    return out
