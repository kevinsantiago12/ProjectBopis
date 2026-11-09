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
    if p.get('nonav'):
        vals['bCanEverAffectNavigation'] = False
    if p.get('draw'):
        vals['LDMaxDrawDistance'] = p['draw']
    if p.get('seed') is not None:     # a monobloc piece's colour, picked once: 'Spawn Seed' in MF_PerInstanceColor reads custom primitive data 0
        vals['CustomPrimitiveData'] = {'data': [p['seed']]}
    if vals:
        call(O + 'set_properties', {'instance': comp, 'values': json.dumps(vals)})
    return a


def weld(out, todo, placed):
    # A welded piece (weld_to, a bucket's lid) is attached root to root to its parent and doesn't simulate. bAutoWeld, on by default, welds the two bodies into one when the game
    # starts (FBodyInstance::InitBody), so the lid rides the bucket. The parent sorts before its lid, so it was placed earlier in this call, or is already in the level.
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


def run():
    out = {'removed': 0, 'placed': 0, 'fail': []}
    ps = call(S + 'find_actors', {'name': 'PlayerStart', 'tag': '', 'collision_channels': []})
    if not ps or not ps[0]['refPath'].startswith('/Game/ThirdPerson/Lvl_BackAlleys_Arena') or call('EditorToolset.EditorAppToolset.IsPIERunning', {}):
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
    placed, todo = {}, []
    for n in PLACE_CHUNKS:
        for p in call(AS + 'read_file', {'file_path': DIR + 'plan_delta_place_%d.json' % n}):
            try:
                placed[p['label']] = place(p)
                out['placed'] += 1
                if p.get('weld_to'):
                    todo.append(p)
            except Exception as e:
                out['fail'].append([p['label'], str(e)[:160]])
    if todo:
        weld(out, todo, placed)
    out['save'] = call(AS + 'save_assets', {'asset_paths': []})
    return out
