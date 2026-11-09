# Headless (Tools/AnimAuthoring/RunUnreal.ps1), 2026-11-09. Folds Lvl_01_Slum's section sublevels into the persistent map (user: "I would
# rather not have them as sublevels at this point if you have to add them headless everytime": the bridge only places into the persistent
# level; "only if we can still do Sections 1-7 split even without sublevles"). Each actor of Lvl_01_Slum_S<n>_Art / _Gameplay is made again
# in the persistent level from its own data, and tagged "S<n>": the section, for splitting the map by tag when streaming is built.
# EditorActorSubsystem.duplicate_actors crashes headless (null access in UnrealEd, 2026-11-09), so the copy is by data: class, transform,
# label, folder, tags; a mesh's mesh, material overrides, body instance (collision profile, responses, physical material) and render
# flags; a light's settings; a decal's material and size. Every copy is checked against its original; on any difference, or an actor
# of a kind it can't copy, it removes the copies and saves nothing. Then the originals go, the sublevels come out of the map, and only
# the persistent map is saved: the sublevel files stay on disk as they were, a copy from before the merge, until the user deletes them.
# REPLACE_DRY=1: copy, check, remove the copies, save nothing (fine with the editor open). A real run needs the editor closed.
#   .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\flatten_sections_ue.py
import json
import os
import unreal

MAP = '/Game/ThirdPerson/Lvl_01_Slum'
SUB_DIR = '/Game/ThirdPerson/01_Slum/'
SECTIONS = 7
REPORT = 'C:/Users/kevin/Documents/Unreal Projects/ProjectBopis/Saved/LinearSlums/flatten_report.json'
DRY = os.environ.get('REPLACE_DRY', '') == '1'
SKIP_CLASSES = ('WorldSettings', 'Brush', 'DefaultPhysicsVolume')
KINDS = ('StaticMeshActor', 'PointLight', 'SpotLight', 'DecalActor', 'PlayerStart')
# Component properties copied as they are (mobility first: setting it re-picks a default collision profile).
MESH_PROPS = ('mobility', 'use_default_collision', 'body_instance', 'override_materials', 'can_ever_affect_navigation', 'lightmap_type',
              'ld_max_draw_distance', 'cast_shadow', 'visible', 'hidden_in_game', 'generate_overlap_events', 'override_light_map_res',
              'overridden_light_map_res', 'receives_decals')
LIGHT_PROPS = ('mobility', 'intensity_units', 'intensity', 'light_color', 'attenuation_radius', 'source_radius', 'soft_source_radius',
               'source_length', 'cast_shadows', 'use_inverse_squared_falloff', 'light_falloff_exponent', 'inner_cone_angle',
               'outer_cone_angle', 'affects_world', 'visible', 'use_temperature', 'temperature', 'indirect_lighting_intensity',
               'volumetric_scattering_intensity')
DECAL_PROPS = ('decal_size', 'sort_order', 'fade_screen_size', 'fade_start_delay', 'fade_duration')

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)
_unset = []


def log(s):
    unreal.log('[FLATTEN] ' + s)


def copy_props(src, dst, names):
    for n in names:
        try:
            dst.set_editor_property(n, src.get_editor_property(n))
        except Exception as e:      # noqa: BLE001  (a light without cone angles, ...)
            if len(_unset) < 30 and 'cone' not in n:
                _unset.append('%s.%s: %s' % (src.get_class().get_name(), n, str(e)[:80]))


def make(a):
    """A copy of actor a in the current level (the persistent one)."""
    cls = a.get_class().get_name()
    loc, rot = a.get_actor_location(), a.get_actor_rotation()
    if cls == 'StaticMeshActor':
        d = eas.spawn_actor_from_class(unreal.StaticMeshActor, loc, rot)
        sc, dc = a.static_mesh_component, d.static_mesh_component
        dc.set_static_mesh(sc.static_mesh)
        copy_props(sc, dc, MESH_PROPS)
    elif cls in ('PointLight', 'SpotLight'):
        d = eas.spawn_actor_from_class(unreal.PointLight if cls == 'PointLight' else unreal.SpotLight, loc, rot)
        kind = unreal.PointLightComponent if cls == 'PointLight' else unreal.SpotLightComponent
        copy_props(a.get_component_by_class(kind), d.get_component_by_class(kind), LIGHT_PROPS)
    elif cls == 'DecalActor':
        d = eas.spawn_actor_from_class(unreal.DecalActor, loc, rot)
        d.decal.set_decal_material(a.decal.get_decal_material())
        copy_props(a.decal, d.decal, DECAL_PROPS)
    elif cls == 'PlayerStart':
        d = eas.spawn_actor_from_class(unreal.PlayerStart, loc, rot)
    else:
        return None
    d.set_actor_scale3d(a.get_actor_scale3d())
    d.set_actor_label(a.get_actor_label())
    d.set_folder_path(a.get_folder_path())
    return d


def differs(a, d):
    la, lb = a.get_actor_location(), d.get_actor_location()
    ra, rb = a.get_actor_rotation(), d.get_actor_rotation()
    sa, sb = a.get_actor_scale3d(), d.get_actor_scale3d()
    if max(abs(la.x - lb.x), abs(la.y - lb.y), abs(la.z - lb.z)) > 0.01 or max(abs(sa.x - sb.x), abs(sa.y - sb.y), abs(sa.z - sb.z)) > 1e-4:
        return 'transform'
    if any(abs(((x - y) + 180.0) % 360.0 - 180.0) > 0.01 for x, y in ((ra.pitch, rb.pitch), (ra.yaw, rb.yaw), (ra.roll, rb.roll))):
        return 'rotation'
    if a.get_actor_label() != d.get_actor_label() or str(a.get_folder_path()) != str(d.get_folder_path()):
        return 'label or folder'
    if isinstance(a, unreal.StaticMeshActor):
        sc, dc = a.static_mesh_component, d.static_mesh_component
        if sc.static_mesh != dc.static_mesh:
            return 'mesh'
        if [m.get_path_name() if m else None for m in sc.get_materials()] != [m.get_path_name() if m else None for m in dc.get_materials()]:
            return 'materials'
        if sc.get_collision_profile_name() != dc.get_collision_profile_name() or sc.get_collision_enabled() != dc.get_collision_enabled():
            return 'collision'
    if isinstance(a, unreal.DecalActor) and a.decal.get_decal_material() != d.decal.get_decal_material():
        return 'decal material'
    return None


def run():
    rep = {'dry': DRY}
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    les.set_current_level_by_name('Lvl_01_Slum')
    subs, odd = {}, []
    for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor):
        path = a.get_path_name()
        if not path.startswith(SUB_DIR) or a.get_class().get_name() in SKIP_CLASSES:
            continue
        name = path[len(SUB_DIR):].split('.')[0]          # Lvl_01_Slum_S3_Art
        if a.get_class().get_name() not in KINDS:
            odd.append('%s: %s (%s)' % (name, a.get_actor_label(), a.get_class().get_name()))
        if a.get_attach_parent_actor():
            odd.append('%s: %s is attached to %s' % (name, a.get_actor_label(), a.get_attach_parent_actor().get_actor_label()))
        subs.setdefault(name, []).append(a)
    rep['actors per sublevel'] = {k: len(v) for k, v in sorted(subs.items())}
    rep['kinds it cannot copy'] = odd
    log('actors per sublevel %s; %d it can\'t copy' % (rep['actors per sublevel'], len(odd)))
    pairs, bad = [], []
    if not odd:
        for name, acts in sorted(subs.items()):
            sec = int(name.split('_S')[-1].split('_')[0])
            for a in acts:
                d = make(a)
                if d is None:
                    bad.append('%s: not copied' % a.get_actor_label())
                    continue
                d.set_editor_property('tags', list(a.tags) + [unreal.Name('S%d' % sec)])
                pairs.append((a, d))
                if not d.get_path_name().startswith(MAP + '.'):
                    bad.append('%s landed in %s' % (a.get_actor_label(), d.get_path_name()))
                else:
                    why = differs(a, d)
                    if why:
                        bad.append('%s: %s' % (a.get_actor_label(), why))
            log('%s: %d copied' % (name, len(acts)))
    rep['copied'] = len(pairs)
    rep['problem count'] = len(bad)
    rep['problems'] = bad[:60]
    rep['properties not set'] = _unset
    if odd or bad or DRY:
        eas.destroy_actors([d for a, d in pairs])
        log('%s: %d kinds it can\'t copy, %d problems; copies removed, nothing saved' % ('dry run' if DRY else 'STOP', len(odd), len(bad)))
        json.dump(rep, open(REPORT, 'w'), indent=1)
        return
    eas.destroy_actors([a for a, d in pairs])
    removed = []
    for sec in range(1, SECTIONS + 1):
        for kind in ('Art', 'Gameplay'):
            name = 'Lvl_01_Slum_S%d_%s' % (sec, kind)
            st = unreal.GameplayStatics.get_streaming_level(world, name)
            lvl = st.get_loaded_level() if st else None
            if lvl and unreal.EditorLevelUtils.remove_level_from_world(lvl):
                removed.append(name)
    rep['sublevels taken out'] = removed
    all_ = unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    rep['actors left in sublevels'] = sum(1 for a in all_ if a.get_path_name().startswith(SUB_DIR))
    rep['actors in the map'] = len(all_)
    rep['tagged per section'] = {s: sum(1 for a in all_ if unreal.Name('S%d' % s) in a.tags) for s in range(1, SECTIONS + 1)}
    rep['dirty maps'] = [str(p.get_name()) for p in unreal.EditorLoadingAndSavingUtils.get_dirty_map_packages()]
    rep['saved'] = unreal.EditorLoadingAndSavingUtils.save_packages([unreal.load_package(MAP)], True)
    log('took out %d sublevels, %d actors left in them, tagged %s, saved %s; dirty maps %s' % (
        len(removed), rep['actors left in sublevels'], rep['tagged per section'], rep['saved'], rep['dirty maps']))
    json.dump(rep, open(REPORT, 'w'), indent=1)


run()
