# Headless, 2026-11-08: the base night for Lvl_01_Slum's persistent map ("Night, people still out"): a Stationary moon
# (the spec's Stationary lighting setup: dynamic shadows to 30 m for moving things), a Stationary sky light capturing a
# dark sky atmosphere, and thin blue height fog. Starting values, to be judged in the editor and after a bake: auto
# exposure is off project-wide, so night comes from the light values. Run only while the open editor hasn't loaded the map.
# Replaces actors with the same labels in Slums/Lighting, so it can run again.
import unreal

MAP = '/Game/ThirdPerson/Lvl_01_Slum'
FOLDER = 'Slums/Lighting'
MOON_LUX, MOON_COLOUR = 0.35, (0.62, 0.72, 1.0)
SKY_INTENSITY = 0.6
FOG_DENSITY, FOG_COLOUR = 0.012, (0.012, 0.016, 0.03)

eas = unreal.get_editor_subsystem(unreal.EditorActorSubsystem)
les = unreal.get_editor_subsystem(unreal.LevelEditorSubsystem)


def log(s):
    unreal.log('[NIGHT] ' + s)


def run():
    unreal.EditorLoadingAndSavingUtils.load_map(MAP)
    les.set_current_level_by_name('Lvl_01_Slum')
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    old = [a for a in unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor) if str(a.get_folder_path()) == FOLDER]
    eas.destroy_actors(old)
    moon = eas.spawn_actor_from_class(unreal.DirectionalLight, unreal.Vector(0, 0, 3000), unreal.Rotator(roll=0.0, pitch=-38.0, yaw=35.0))
    lc = moon.light_component
    lc.set_editor_property('mobility', unreal.ComponentMobility.STATIONARY)
    lc.set_editor_property('intensity', MOON_LUX)
    lc.set_light_color(unreal.LinearColor(MOON_COLOUR[0], MOON_COLOUR[1], MOON_COLOUR[2], 1.0))
    lc.set_editor_property('dynamic_shadow_distance_stationary_light', 3000.0)
    lc.set_editor_property('atmosphere_sun_light', True)
    moon.set_actor_label('Moon')
    sky = eas.spawn_actor_from_class(unreal.SkyLight, unreal.Vector(0, 0, 2800), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    sc = sky.light_component
    sc.set_editor_property('mobility', unreal.ComponentMobility.STATIONARY)
    sc.set_editor_property('intensity', SKY_INTENSITY)
    sc.set_editor_property('real_time_capture', True)
    sky.set_actor_label('SkyLight_Night')
    atm = eas.spawn_actor_from_class(unreal.SkyAtmosphere, unreal.Vector(0, 0, 0), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    atm.set_actor_label('SkyAtmosphere')
    fog = eas.spawn_actor_from_class(unreal.ExponentialHeightFog, unreal.Vector(0, 0, -200), unreal.Rotator(roll=0.0, pitch=0.0, yaw=0.0))
    fc = fog.component
    fc.set_editor_property('fog_density', FOG_DENSITY)
    fc.set_editor_property('fog_inscattering_luminance', unreal.LinearColor(FOG_COLOUR[0], FOG_COLOUR[1], FOG_COLOUR[2], 1.0))
    fog.set_actor_label('HeightFog_Night')
    for a in (moon, sky, atm, fog):
        a.set_folder_path(FOLDER)
    log('moon %.2f lux, sky %.2f, fog %.3f' % (MOON_LUX, SKY_INTENSITY, FOG_DENSITY))
    log('saved: %s' % unreal.EditorLoadingAndSavingUtils.save_dirty_packages(True, True))


run()
