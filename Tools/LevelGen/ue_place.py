# Unreal side, shared by the headless placers (build_story_ue.py, swap_sections_ue.py): one plan piece -> one actor in the
# current level. Moved out of build_story_ue.py on 2026-11-09, unchanged. Import it after putting this folder on sys.path
# (a -run=pythonscript run doesn't add the script's own folder).
import unreal

INTERIOR = '/Game/ThirdPerson/BackAlleys/MI_BackAlleys_Interior'

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
_assets = {}
n = {'placed': 0, 'failed': 0, 'props failed': 0}
fail = []


def asset(path):
    if path not in _assets:
        _assets[path] = unreal.load_asset(path)
    return _assets[path]


def xform(p):
    loc = unreal.Vector(*p['loc'])
    rot = unreal.Rotator(roll=p['rot'][2], pitch=p['rot'][0], yaw=p['rot'][1])
    return loc, rot


def setp(obj, name, value):
    try:
        obj.set_editor_property(name, value)
        return True
    except Exception as e:      # noqa: BLE001
        n['props failed'] += 1
        if len(fail) < 40:
            fail.append('%s.%s: %s' % (obj.get_name(), name, e))
        return False


def place_light(p):
    li = p['light']
    loc, rot = xform(p)
    cls = unreal.PointLight if li['kind'] == 'PointLight' else unreal.SpotLight
    a = eas.spawn_actor_from_class(cls, loc, rot)
    comp = a.get_component_by_class(unreal.PointLightComponent if li['kind'] == 'PointLight' else unreal.SpotLightComponent)
    setp(comp, 'mobility', unreal.ComponentMobility.STATIC)
    setp(comp, 'intensity', li['intensity'])
    setp(comp, 'attenuation_radius', li['radius'])
    setp(comp, 'source_radius', li['source'])
    if li.get('length'):
        setp(comp, 'source_length', li['length'])
    if li['kind'] == 'SpotLight':
        setp(comp, 'outer_cone_angle', li['outer'])
        setp(comp, 'inner_cone_angle', li['outer'] * 0.55)
    # The colour as the property itself (an FColor, 0-255, as the bridge's set_properties stores it): set_light_color is a run-time
    # call, and a Static light ignores it, so every light placed headless before 2026-11-09 came out white.
    c = li['colour']
    setp(comp, 'light_color', unreal.Color(r=int(c[0] * 255.0 + 0.5), g=int(c[1] * 255.0 + 0.5), b=int(c[2] * 255.0 + 0.5), a=255))
    return a


def place(p):
    if p.get('light'):
        a = place_light(p)
    elif p['decal']:
        loc, rot = xform(p)
        a = eas.spawn_actor_from_class(unreal.DecalActor, loc, rot)
        a.decal.set_decal_material(asset(p['asset']))
        a.set_actor_scale3d(unreal.Vector(*p['scale']))
    else:
        loc, rot = xform(p)
        # spawn_actor_from_object returns None in a headless run (2026-11-08: 8,324 of 8,495 failed), so: the class, then its mesh
        mesh = asset(p['asset'])
        if mesh is None:
            raise RuntimeError('no asset ' + p['asset'])
        a = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        comp = a.static_mesh_component
        comp.set_static_mesh(mesh)
        a.set_actor_scale3d(unreal.Vector(*p['scale']))
        if p.get('mats'):
            for i, m in enumerate(p['mats']):
                comp.set_material(i, asset(m))
        if p.get('mat') == 'interior':
            comp.set_material(0, asset(INTERIOR))
        if p.get('mat') == 'hidden':
            setp(comp, 'visible', False)
            setp(comp, 'hidden_in_game', True)
            setp(comp, 'cast_shadow', False)
        prof = 'NoCollision' if p.get('nocoll') else p.get('coll')
        if prof:
            setp(comp, 'use_default_collision', False)   # left on, the component keeps the mesh's own collision (LESSONS)
            comp.set_collision_profile_name(prof)
        if p.get('phys'):
            bi = comp.get_editor_property('body_instance')
            bi.set_editor_property('phys_material_override', asset(p['phys']))
            setp(comp, 'body_instance', bi)
        if p.get('vol'):
            setp(comp, 'lightmap_type', unreal.LightmapType.FORCE_VOLUMETRIC)
        if p.get('nonav'):
            setp(comp, 'can_ever_affect_navigation', False)
        if p.get('draw'):
            setp(comp, 'ld_max_draw_distance', p['draw'])
        if p.get('noshadow'):
            setp(comp, 'cast_shadow', False)
    a.set_actor_label(p['label'])
    a.set_folder_path(p['folder'])
    if p.get('sec'):                # the section, as a tag: Lvl_01_Slum is one map since 2026-11-09 (flatten_sections_ue.py)
        a.set_editor_property('tags', [unreal.Name('S%d' % p['sec'])])
    return a


def try_place(p):
    """place(p), counting and logging a failure instead of stopping the run."""
    try:
        place(p)
        n['placed'] += 1
    except Exception as e:      # noqa: BLE001
        n['failed'] += 1
        if len(fail) < 40:
            fail.append('%s: %s' % (p['label'], e))
