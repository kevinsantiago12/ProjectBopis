"""Builds /Game/ThirdPerson/Cinematics/LS_InspectTest, a two-shot test cutscene for an Inspect Point.

Headless (Tools/AnimAuthoring/RunUnreal.ps1). Reads the inspect's placement from inspect_test.json beside
this script: focus (the inspect's centre), mark (where the player stands), yaw (his facing), floor (ground
Z under the mark). Recreates the asset, so edits made to it in the editor are lost.

- The player: a spawnable BP_Player_Cutscene, the cutscene double (user 2026-11-08: "replace the model
  with a BP_Player_Cutscene"), so authoring shows the real model, its binding tagged and named "Player"
  (no character names in the build). It stands on the mark; a transform track would move it.
- His animation sits on the actor binding (Sequencer uses the actor's first skeletal mesh, the body),
  Force Custom Mode on, so it plays without the AnimBP's slots.
- Two Cine Cameras: an over-the-shoulder medium (0-2 s), then a close shot on the focus (2-4 s). The first
  cut is hard; the last eases out over 0.5 s, back to the gameplay camera.
"""
import json
import os
import unreal

HERE = os.path.dirname(os.path.abspath(__file__))
P = json.load(open(os.path.join(HERE, 'inspect_test.json')))

PKG = '/Game/ThirdPerson/Cinematics'
NAME = 'LS_InspectTest'
FULL = PKG + '/' + NAME
# The cutscene double: BP_Player_CC's look (its construction script builds the CC parts) on a plain
# Character, with no movement, collision or AI. No gameplay code runs under the sequence.
PLAYER_BP = '/Game/ThirdPerson/Blueprints/CC/BP_Player_Cutscene'
TAG = 'Player'
ANIM = '/Game/Characters/Heroes/Mannequin/Animations/Locomotion/Unarmed/MM_Unarmed_Crouch_Idle'
FPS = 30
SHOT = 60          # frames per shot
END = SHOT * 2


def log(*parts):
    unreal.log('[SEQ] ' + ' '.join(str(p) for p in parts))


def vec(d):
    return unreal.Vector(d[0], d[1], d[2])


def place_template(binding, location, rotation):
    """Spawnables spawn where their template's root sits; no transform track needed."""
    template = binding.get_object_template()
    root = template.get_editor_property('root_component')
    root.set_editor_property('relative_location', location)
    root.set_editor_property('relative_rotation', rotation)
    return template


def look(from_loc, to_loc):
    return unreal.MathLibrary.find_look_at_rotation(from_loc, to_loc)


def run():
    if unreal.EditorAssetLibrary.does_asset_exist(FULL):
        log('replacing the old', FULL)
        unreal.EditorAssetLibrary.delete_asset(FULL)

    tools = unreal.AssetToolsHelpers.get_asset_tools()
    seq = tools.create_asset(NAME, PKG, unreal.LevelSequence, unreal.LevelSequenceFactoryNew())
    seq.set_display_rate(unreal.FrameRate(FPS, 1))
    seq.set_playback_start(0)
    seq.set_playback_end(END)

    focus = vec(P['focus'])
    mark = vec(P['mark'])
    yaw = float(P['yaw'])
    floor = float(P['floor'])

    # The player's stand-in: the player Blueprint itself, on the mark. A character's origin is its
    # capsule's centre, so it stands half a capsule above the floor.
    player = seq.add_spawnable_from_class(unreal.EditorAssetLibrary.load_blueprint_class(PLAYER_BP))
    player.set_display_name(TAG)
    template = player.get_object_template()
    half_height = template.get_editor_property('capsule_component').get_unscaled_capsule_half_height()
    place_template(player, unreal.Vector(mark.x, mark.y, floor + half_height), unreal.Rotator(0.0, 0.0, yaw))
    player.tag_binding(TAG)
    log('player stand-in', template.get_class().get_name(), 'half height', half_height,
        'tags', player.get_binding_tags())

    anim_track = player.add_track(unreal.MovieSceneSkeletalAnimationTrack)
    anim = anim_track.add_section()
    anim.set_range(0, END)
    params = anim.get_editor_property('params')
    params.set_editor_property('animation', unreal.load_asset(ANIM))
    params.set_editor_property('force_custom_mode', True)
    anim.set_editor_property('params', params)

    # Shot A: over his right shoulder, a medium on him and what he looks at.
    facing = unreal.Rotator(0.0, 0.0, yaw)
    forward = unreal.MathLibrary.get_forward_vector(facing)
    right = unreal.MathLibrary.get_right_vector(facing)
    head = unreal.Vector(mark.x, mark.y, floor + 120.0)
    a_loc = head - forward * 180.0 + right * 60.0 + unreal.Vector(0.0, 0.0, 30.0)
    a_aim = (head + focus) * 0.5

    # Shot B: low and close on the thing itself, from beside him.
    b_loc = focus - forward * 90.0 - right * 70.0 + unreal.Vector(0.0, 0.0, 25.0)

    cams = []
    for label, loc, aim, focal in (('Shot_A_OverShoulder', a_loc, a_aim, 35.0),
                                   ('Shot_B_Close', b_loc, focus, 50.0)):
        cam = seq.add_spawnable_from_class(unreal.CineCameraActor)
        cam.set_display_name(label)
        cam_template = place_template(cam, loc, look(loc, aim))
        # On a spawnable's template the getters come back empty; the property holds the component.
        cine = cam_template.get_editor_property('camera_component')
        log(label, 'camera component', cine.get_class().get_name() if cine else None)
        cine.set_editor_property('current_focal_length', focal)
        cine.set_editor_property('current_aperture', 2.8)
        fs = cine.get_editor_property('focus_settings')
        fs.set_editor_property('focus_method', unreal.CameraFocusMethod.MANUAL)
        fs.set_editor_property('manual_focus_distance', (aim - loc).length())
        cine.set_editor_property('focus_settings', fs)
        cams.append(cam)

    cut_track = seq.add_track(unreal.MovieSceneCameraCutTrack)
    # The track's Can Blend and the sections' easing aren't open to scripting (plain UPROPERTY()s). Without
    # them the first and last cuts are hard; a blend back to gameplay is set in the editor.
    for i, cam in enumerate(cams):
        cut = cut_track.add_section()
        cut.set_range(i * SHOT, (i + 1) * SHOT)
        cut.set_camera_binding_id(seq.get_binding_id(cam))

    unreal.EditorAssetLibrary.save_asset(FULL, only_if_is_dirty=False)
    log('saved', FULL, 'bindings', [b.get_display_name() for b in seq.get_bindings()],
        'tags', seq.get_all_binding_tags())


try:
    run()
except Exception as e:
    unreal.log_error('[SEQ] failed: ' + repr(e))
    raise
