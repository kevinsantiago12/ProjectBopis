# AnimAuthoring

Animations made by script: an existing Unreal clip is exported, re-made in Blender with IK, and imported back
next to the original. Used for the reloads Lyra's library doesn't have.

## Done so far

The project folders are removed once their assets are in and tested. The spec section has the details: the
motion, the timings, the gun's rig and the assets made.

| Reload | Assets | Spec section | Scripts |
|---|---|---|---|
| M4, rear charging-handle pull | `MM_Rifle_Reload_M4`, `AM_Rifle_Reload_M4`, `A_AR4_Reload` | *Charging styles: the M4 reload* | in git history (`M4Reload/`) |
| Revolver, speedloader with a full flick | `MM_Pistol_Reload_Revolver`, `AM_Pistol_Reload_Revolver`, `A_Revolver_Reload` | *Revolver reload: speedloader, full flick* | removed |
| Mossberg pump rack after a reload from empty | `MM_Shotgun_Reload_Pump`, `AM_Shotgun_Reload_Pump`, `A_Mossberg_Rack` | *Shotgun rack after a reload from empty* | removed |
| Trigger finger, resting and pressing (one-frame poses, solved onto the AR4's trigger blade) | `TriggerRestPose`, `TriggerPressPose` (`/Game/ThirdPerson/Animations/TriggerFinger/`) | *Trigger finger* | `TriggerFinger/` (in progress: kept until tested in Play) |

## Layout

- `lib/animlib.py`: the Blender side.
  - Unreal-to-FBX conversions (`ue_xform`, `ue_rotator`).
  - Scene setup: `setup_character`, and `Gun`, which rides a gun on `hand_r` the way the game does.
  - Timing and curves: `frame_of`, `smooth`, `ramp`, `catmull`, `slerp_keys`.
  - Hands and arms: `basis`, `hand_l_basis`, `finger_basis`, `arm_lengths`, `solve_arm` (two-bone IK).
  - Renders: `setup_render`, `game_camera`, `render_tile`, `contact_sheet`.
  - The FBX export, `export_armature`.
- `lib/uelib.py`: the Unreal side.
  - Asset export (`export_asset`).
  - Reading: anim, montage, socket and Blueprint-default reports.
  - Import (`import_anim`, legacy FBX).
  - Pose comparison (`compare`, `worst`).
  - Montage and notify editing (`create_montage`, `copy_montage`, `set_montage_anim`, `set_weapon_sounds`).
  - Curves (`set_curve`) and holding bones still (`hold_bones`).
- `RunUnreal.ps1` / `RunBlender.ps1`: run one script headless with the right flags.
- One folder per job in progress, e.g. `MP5Reload/`. Working files (FBX, `.blend`, JSON reports, logs,
  renders) are written beside its scripts and ignored by git. Its `export_ue.py` recreates them.

## A project folder

Six scripts, each a few lines of setup around the libraries:

| Script | Runs in | Does |
|---|---|---|
| `project.py` | both | The folder's path, the clip and gun FBX names, the gun's grip offsets (from its weapon Blueprint, via `animlib.ue_xform`), the last frame, the `.blend` name, and `setup()` returning `(rig, gun)`. Puts `../lib` on the import path. |
| `export_ue.py` | Unreal | Exports the clip, `SKM_Manny_Simple` and the gun's mesh as FBX (`uelib.export_asset`), and writes `ue_info.json`: the clip's notifies and curves, the montage's sections and notifies, the gun's sockets, the weapon's settings. |
| `bl_inspect.py` | Blender | Prints the original's hands and the gun's parts in gun space; renders it. |
| `bl_author.py` | Blender | The motion. Keys the arms by IK (`solve_arm`) and the gun's own parts in a second action on the gun's armature, timed with the character's. Saves the `.blend`; `render` adds contact sheets. |
| `bl_export.py` | Blender | Opens the `.blend` and writes the FBX (`export_armature`: `root` for the character, the gun's root bone name and scale for the gun). |
| `import_ue.py` | Unreal | Imports (`import_anim`), compares with the original where nothing should change (`compare`, `worst`), and makes the montage and notifies. Writes `import_result.json`. |

Start each script with:

```python
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project as P   # Blender scripts; Unreal scripts put ../lib on the path themselves and import uelib
import animlib as A
```

The M4's folder (in git history) is the simplest complete example. Its gun has one moving part, the handle.

## Running

From the project root, e.g. for an `MP5Reload` folder:

```powershell
.\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\AnimAuthoring\MP5Reload\export_ue.py -Render
.\Tools\AnimAuthoring\RunBlender.ps1 .\Tools\AnimAuthoring\MP5Reload\bl_inspect.py
.\Tools\AnimAuthoring\RunBlender.ps1 .\Tools\AnimAuthoring\MP5Reload\bl_author.py render
.\Tools\AnimAuthoring\RunBlender.ps1 .\Tools\AnimAuthoring\MP5Reload\bl_export.py
.\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\AnimAuthoring\MP5Reload\import_ue.py
```

1. **Export** (`-Render`: skeletal meshes need rendering). The open editor can stay open.
2. **Inspect, then author:**
   - Check the contact sheets in `renders/`.
   - `animlib.game_camera` renders from the game's own camera.
   - A reload hidden behind the body from there (the revolver's first pass) needs restaging to the right
     side at shoulder height.
3. **Export the FBX.**
4. **Import.**
   - New assets are fine with the editor open.
   - Replacing assets the open editor has loaded isn't. It keeps its own copies and can save them back.
     Close it first (`..\RebuildEditor.ps1 -NoLaunch`, which also builds any code the import needs), import,
     then reopen it.
   - Read `import_result.json`: `worst` compares the new clip with the original where it shouldn't have
     changed (under 0.5).

Wiring the assets into Blueprints comes after, through the bridge or by hand. Set any child Blueprints too, and
compile them (spec: *Bridge-set Blueprint defaults*).

When the job's done and tested, delete its folder and add a row to *Done so far*.

## Conventions and gotchas

- **Spaces:**
  - Everything is in the FBX space Unreal exports: cm, Unreal's axes with Y negated.
  - An Unreal location (x, y, z) becomes (x, -y, z); a rotation R becomes S R S, with S = diag(1, -1, 1).
    `ue_xform` does both.
  - Guns ride the `HandGrip_R` socket on `hand_r` (`animlib.HANDGRIP_R`), then the weapon's
    `GripLocationOffset` / `GripRotationOffset`.
- **Root bones:**
  - Blender's FBX import turns each file's root bone into the armature object (`root`, `b_gun_Root`,
    `_357 Revolver Rig`).
  - It keys the root's track onto the object, with the cm-to-m scale included.
  - `export_armature` drops those keys and names the object back after the root bone.
  - It writes the root at the scale Unreal's skeleton has: 1, or 100 for the revolver pack's rig.
  - Unreal turns spaces in bone names into hyphens on import.
- **A gun's component space** is its FBX's top node. That's an empty when the exporter wrote one (the
  revolver, the Mossberg), otherwise the root-bone object (the AR4). `animlib.Gun` handles both.
- **Keys in moving spaces:**
  - Key a hand in the gun's space or the chest's (`spine_05`).
  - Re-evaluate every key in the current frame's space before interpolating, so a hand on the gun stays on
    it while the gun moves.
  - The left-hand key lists in the revolver's `bl_author.py` were built this way: each key is
    `(time, "gun" | "chest", wrist, rotation)`, all evaluated per frame, then Catmull-Rom.
- **Hands:** `finger_basis` gives a hand's orientation from its finger bones. Pose a hand by where its fingers
  point and which way its palm faces (`hand_l_basis`), times that fixed offset.
- **Headless editor:**
  - Python imports need the legacy FBX importer (`use_legacy_fbx_import`).
  - `-AllowCommandletRendering` asserts on startup if `-NoShaderCompile` is also given.
  - "HttpListener unable to bind to 127.0.0.1:8000" is the open editor's bridge port, and harmless.
- **Montages from Python:**
  - Sections (`composite_sections`) aren't reachable, so a sectioned montage starts as a copy of one that has
    the sections (`copy_montage`).
  - The nested struct arrays (tracks, segments) come back as copies. Edit them in place and the change is
    lost silently; `set_montage_anim` rebuilds each level instead.
- **Gun clips from another clip:** `hold_bones` holds every bone but the ones kept at frame 0, through the
  sequence's `AnimSequencerController`. That's how `A_Mossberg_Rack` came from `A_Mossberg_Fire`.
- **Physics instead of animation:** a part that leaves the gun (empties, a magazine) reads better as a physics
  actor spawned by a notify than as keys. The revolver's Eject notify drops `ReloadCasingMesh` from the round
  bones, and the animation only hides the bones.

## Checked

The libraries were checked on 2026-11-02, before the three project folders were removed:
- All three projects were regenerated from fresh exports through `lib/` and the runners.
- Every animation key matched the files behind the tested assets: revolver and shotgun exactly, M4 within 2e-6.
- The gun FBXs came out the same.

The import side (`import_anim`, `copy_montage`, `set_weapon_sounds`, `set_curve`, `hold_bones`) was refactored
from code that had run, but hasn't run in this form. Check `import_result.json` the first time.
