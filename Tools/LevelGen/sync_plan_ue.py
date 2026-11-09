# Bridge-side: makes the open level match the current plan without a rebuild. The body of one
# ProgrammaticToolset.execute_tool_script call (the sandbox has no exec, so paste it whole; see LESSONS).
# For each FOLDER: sets every actor's transform and material overrides from the plan, by label, and places any planned
# piece the level doesn't have yet; with REMOVE, also deletes pieces the plan no longer has. Takes a few minutes for a big folder, so split the big ones
# over calls: ('BackAlleys/Blocks', 'BackAlleys/SpawnDoors'), then the rest. Stops if the level is wrong or in PIE.
# Placed actors aren't named by label (StaticMeshActor_UAID_...), so labels come from get_label, not find_actors.
# It can't change a placed actor's mesh: if a label keeps its name but gets a new mesh, remove it first.
import json
FOLDERS = ('BackAlleys/Blocks', 'BackAlleys/SpawnDoors')
REMOVE = False              # delete actors in FOLDERS that the plan no longer has: check the plan first
NEW_FOLDERS = ()            # folders not in the level yet: their pieces are just placed. Asking the bridge about a
#                            missing folder stops the whole script, and try/except can't catch it.
CHUNKS = 40                # the generator prints this: "N items in M chunks"
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
    return {'location': v(p['loc']), 'rotation': {'pitch': p['rot'][0], 'yaw': p['rot'][1], 'roll': p['rot'][2]},
            'scale': v(p['scale'])}


def place_light(p):
    """A static light: the plan's "light" holds its settings."""
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


def set_mats(a, p):
    if p['mats'] and not p['decal']:
        comp = [c for c in call(A + 'get_components', {'actor': a}) if 'StaticMesh' in c['refPath']][0]
        call(O + 'set_properties', {'instance': comp, 'values': json.dumps({'OverrideMaterials': [obj(m) for m in p['mats']]})})


def run():
    out = {'synced': 0, 'placed': 0, 'fail': [], 'not_in_plan': []}
    gp = call(S + 'get_actors_in_folder', {'folder_path': 'BackAlleys/Gameplay', 'recursive': True})
    if not gp or not gp[0]['refPath'].startswith('/Game/ThirdPerson/Lvl_BackAlleys_Arena'):
        out['abort'] = 'wrong level or in PIE'
        return out
    if call('EditorToolset.EditorAppToolset.IsPIERunning', {}):
        out['abort'] = 'PIE running'
        return out
    plan = {}
    for i in range(CHUNKS):
        for p in call(AS + 'read_file', {'file_path': DIR + 'plan3_%d.json' % i}):
            if p['folder'] in FOLDERS + NEW_FOLDERS:
                plan[(p['folder'], p['label'])] = p
    out['planned'] = len(plan)
    seen = set()
    have = {}
    for folder in FOLDERS:
        for a in call(S + 'get_actors_in_folder', {'folder_path': folder, 'recursive': True}):
            label = call(A + 'get_label', {'actor': a})
            p = plan.get((folder, label))
            if p is None:
                out['not_in_plan'].append(label)
                if REMOVE:
                    call(S + 'remove_from_scene', {'actor': a})
                continue
            seen.add((folder, label))
            have[label] = a
            try:
                call(A + 'set_actor_transform', {'actor': a, 'xform': xform(p)})
                set_mats(a, p)
                out['synced'] += 1
            except Exception as e:
                out['fail'].append([label, str(e)[:120]])
    for key, p in plan.items():
        if key in seen:
            continue
        try:
            if p.get('light'):
                place_light(p)
                out['placed'] += 1
                continue
            a = call(S + 'add_to_scene_from_asset', {'asset_path': p['asset'], 'name': p['label'], 'xform': xform(p)})
            call(A + 'set_label', {'actor': a, 'label': p['label']})
            call(S + 'set_actor_folder', {'actor': a, 'folder_path': p['folder']})
            have[p['label']] = a
            set_mats(a, p)
            if p['nocoll'] or p.get('coll') or p.get('phys') or p.get('draw') or p['vol'] or p.get('noshadow') or p.get('physics') or p.get('weld_to'):
                vals = {'BodyInstance': {'collisionProfileName': 'NoCollision'}, 'bUseDefaultCollision': False} if p['nocoll'] else {}     # left on, the component ignores the preset
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
                    # Mobility goes first: the keys are set in order, and setting Mobility re-picks a default profile from mobility and simulate (FBodyInstanceEditorHelpers),
                    # which turned a lid's PhysicsActor into BlockAllDynamic when it came after BodyInstance.
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
                comp = [c for c in call(A + 'get_components', {'actor': a}) if 'StaticMesh' in c['refPath']][0]
                call(O + 'set_properties', {'instance': comp, 'values': json.dumps(vals)})
            out['placed'] += 1
        except Exception as e:
            out['fail'].append([p['label'], str(e)[:120]])
    # A welded piece (weld_to, a bucket's lid) is attached root to root to its parent and doesn't simulate. bAutoWeld, on by default, welds the two bodies into one when the game
    # starts (FBodyInstance::InitBody), so the lid rides the bucket. Removing or re-placing a parent leaves its lid detached, so every pair is checked, not only new ones.
    out['welded'] = 0
    for key, p in plan.items():
        if not p.get('weld_to'):
            continue
        child, par = have.get(p['label']), have.get(p['weld_to'])
        if not (child and par):
            out['fail'].append([p['label'], 'not welded to ' + p['weld_to']])
            continue
        cc = call(A + 'get_root_component', {'actor': child})
        pc = call(A + 'get_root_component', {'actor': par})
        now = call(A + 'get_parent_component', {'component': cc})
        if (isinstance(now, dict) and now.get('refPath') == pc['refPath']) or call(A + 'set_parent_component', {'component': cc, 'parent': pc}):
            out['welded'] += 1
        else:
            out['fail'].append([p['label'], 'not welded to ' + p['weld_to']])
    out['not_in_plan'] = out['not_in_plan'][:10]
    out['save'] = call(AS + 'save_assets', {'asset_paths': []})
    return out
