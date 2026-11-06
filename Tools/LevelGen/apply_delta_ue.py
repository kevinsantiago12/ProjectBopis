# Bridge-side: applies the plan_delta_*.json files plan_delta.py writes to the open level. The body of one ProgrammaticToolset.execute_tool_script call: the sandbox has no exec,
# so paste it whole. plan_delta.py prints how many chunks there are. Set REMOVE_CHUNKS on the first call only, then PLACE_CHUNKS a few at a time: a call shouldn't run too long.
# Saves at the end of each call. Stops if the level is wrong or in PIE. Only folders the delta removes from are asked about, as asking about one that doesn't exist stops the script.
import json
REMOVE_CHUNKS = [0, 1, 2]
PLACE_CHUNKS = [0, 1, 2]
S = 'editor_toolset.toolsets.scene.SceneTools.'
A = 'editor_toolset.toolsets.actor.ActorTools.'
O = 'editor_toolset.toolsets.object.ObjectTools.'
AS = 'editor_toolset.toolsets.asset.AssetTools.'
DIR = 'C:/Users/kevin/Documents/Unreal Projects/ProjectBopis/Saved/BackAlleys/'


def rv(r):
    r = r['returnValue'] if isinstance(r, dict) and 'returnValue' in r else r
    return json.loads(r) if isinstance(r, str) and r[:1] in '[{' else r


def call(n, args):
    return rv(execute_tool(n, json.dumps(args)))


def v(a):
    return {'x': a[0], 'y': a[1], 'z': a[2]}


def obj(p):
    return {'refPath': p + '.' + p.split('/')[-1]}


def xform(p):
    return {'location': v(p['loc']), 'rotation': {'pitch': p['rot'][0], 'yaw': p['rot'][1], 'roll': p['rot'][2]}, 'scale': v(p['scale'])}


def name_it(a, p):
    call(A + 'set_label', {'actor': a, 'label': p['label']})
    call(S + 'set_actor_folder', {'actor': a, 'folder_path': p['folder']})


def place(p):
    if p.get('light'):
        li = p['light']
        a = call(S + 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.' + li['kind']}, 'name': p['label'], 'xform': xform(p)})
        name_it(a, p)
        comp = [c for c in call(A + 'get_components', {'actor': a}) if 'LightComponent' in c['refPath']][0]
        vals = {'Mobility': 'Static', 'Intensity': li['intensity'], 'AttenuationRadius': li['radius'], 'SourceRadius': li['source'],
                'LightColor': {'r': li['colour'][0], 'g': li['colour'][1], 'b': li['colour'][2], 'a': 1.0}}    # lowercase, 0..1: capitals are ignored silently
        if li.get('length'):
            vals['SourceLength'] = li['length']
        if li['kind'] == 'SpotLight':
            vals['OuterConeAngle'] = li['outer']
            vals['InnerConeAngle'] = li['outer'] * 0.55
        call(O + 'set_properties', {'instance': comp, 'values': json.dumps(vals)})
        return
    if p['decal']:
        a = call(S + 'add_to_scene_from_class', {'actor_type': {'refPath': '/Script/Engine.DecalActor'}, 'name': p['label'], 'xform': xform(p)})
        name_it(a, p)
        comp = [c for c in call(A + 'get_components', {'actor': a}) if 'Decal' in c['refPath']][0]
        call(O + 'set_properties', {'instance': comp, 'values': json.dumps({'DecalMaterial': obj(p['asset'])})})
        return
    a = call(S + 'add_to_scene_from_asset', {'asset_path': p['asset'], 'name': p['label'], 'xform': xform(p)})
    name_it(a, p)
    comp = [c for c in call(A + 'get_components', {'actor': a}) if 'StaticMesh' in c['refPath']][0]
    vals = {}
    if p['mats']:
        vals['OverrideMaterials'] = [obj(m) for m in p['mats']]
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
    if p.get('noshadow'):
        vals['CastShadow'] = False
    if p.get('draw'):
        vals['LDMaxDrawDistance'] = p['draw']
    if vals:
        call(O + 'set_properties', {'instance': comp, 'values': json.dumps(vals)})


def run():
    out = {'removed': 0, 'placed': 0, 'fail': []}
    ps = call(S + 'find_actors', {'name': 'PlayerStart', 'tag': '', 'collision_channels': []})
    if not ps or not ps[0]['refPath'].startswith('/Game/ThirdPerson/Lvl_BackAlleys') or call('EditorToolset.EditorAppToolset.IsPIERunning', {}):
        out['abort'] = 'wrong level or PIE'
        return out
    wanted = {}
    for n in REMOVE_CHUNKS:
        for f, label in call(AS + 'read_file', {'file_path': DIR + 'plan_delta_remove_%d.json' % n}):
            wanted.setdefault(f, set()).add(label)
    for f, labels in wanted.items():
        for a in call(S + 'get_actors_in_folder', {'folder_path': f, 'recursive': True}):
            if call(A + 'get_label', {'actor': a}) in labels and call(S + 'remove_from_scene', {'actor': a}):
                out['removed'] += 1
    out['remove_wanted'] = sum(len(v) for v in wanted.values())
    for n in PLACE_CHUNKS:
        for p in call(AS + 'read_file', {'file_path': DIR + 'plan_delta_place_%d.json' % n}):
            try:
                place(p)
                out['placed'] += 1
            except Exception as e:
                out['fail'].append([p['label'], str(e)[:160]])
    out['save'] = call(AS + 'save_assets', {'asset_paths': []})
    return out
