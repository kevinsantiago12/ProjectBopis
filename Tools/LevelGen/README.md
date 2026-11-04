# Level generation

Turns a layout file into an Unreal level. Owned by the level-generation thread.
**Read `LESSONS.md` before every build.**

| File | What it does |
|---|---|
| `gen_level.py` | Reads `Design Document/Arena_Slums_Layout.json` (or a path given as the first argument). It writes placement lists to `Saved/BackAlleys/plan3_*.json` (140 actors per file; the bridge's `read_file` caps at 80 KB) and `plan3_gameplay.json`. It prints a check that every open cell on the arena edge sits behind a door. |
| `place_plan_ue.py` | Bridge-side placer: two `ProgrammaticToolset.execute_tool_script` bodies, recovered from the 2026-11-02 build. Call 1 clears `BackAlleys/*` (except `BackAlleys/Gameplay`) and places `plan3_0..3`. Call 2 places `plan3_4..6`, applies the gameplay file, traces checks and saves. **Re-running call 2 adds the wander points again;** delete `Wander_*` first. |
| `sync_plan_ue.py` | Bridge-side: makes the open level match the plan without a rebuild. Sets transforms and material overrides by label for the chosen folders, and places any planned piece that's missing. Nothing is removed. |
| `analysis/dump_map_ue.py` | Headless and read-only. Dumps every mesh and decal in the packs' demo maps (Favela, AsiaSlum), with materials, to `Saved/LevelGen/`. |
| `analysis/analyse_buildings.py` | Groups a dump's wall pieces into buildings and reports how they're made. |
| `create_materials_ue.py` | Headless. The first block materials (pack parents, `T_Brick_wall`). Superseded by the CHB material; its five `MI_BackAlleys_*OverBlock` / `_HollowBlock` instances are unused. |
| `create_chb_material_ue.py` | Headless. `M_BackAlleys_CHB` (procedural hollow blocks with an optional chipped render) and its instances. It copies the pack textures it uses into `BackAlleys/Textures` so our materials don't depend on the packs. |
| `create_jalousie_ue.py` | Headless. Imports the user's jalousie textures and makes `M_BackAlleys_Jalousie` (a plain BaseColor / Normal / Roughness material for textured planes) and `MI_BackAlleys_JalousieDouble`. |
| `create_hollow_master_ue.py` | Headless, new assets only. `M_BackAlleys_HollowBlocks`, the plain textured master with a Concrete surface: the parent of the hollow blocks, the jalousie instance and the doors. It replaced `M_BackAlleys_Jalousie` as their parent. |
| `create_doors_ue.py` | Headless. Imports the user's five plane-door textures from `Saved/LevelGen/import/doors_zip/` and makes `MI_BackAlleys_Door_<Name>` (parent `M_BackAlleys_HollowBlocks`, Wood or Metal surface). New assets only. |
| `create_board_material_ue.py` | Headless, new assets only. `M_BackAlleys_Boards`, a world-mapped plank material sampling only the usable bands of the pack's wood atlases, with `MI_BackAlleys_Boards_Natural/Blue/Green/Brown` (weatherboards, gable wedges) and `MI_BackAlleys_Flashing`. |
| `analysis/awning_shape_ue.py` | Headless and read-only. Prints the bounds and slope of the awning meshes: which way they run and which edge meets the wall. |
| `analysis/door_bounds_ue.py` | Headless and read-only. Prints the local bounds of the meshes the generator fits by size: the AsiaSlum doors (`steel_door()`), `SM_Slate_01` and `SM_Ramp` (roofs), plus `SM_Ramp`'s corner vertices. |
| `analysis/check_overlaps.py` | Offline check of the plan for z-fighting: trims crossing, same-facing pieces overlapping, end caps lying in another wall's face. Run it after every generator change. |
| `analysis/check_nav_roofs.py` | Offline nav check of the plan: lists roof, lid and terrace tops within step reach of the deck or stairs, and the lowest roof piece against the agent height. Run it after roof, terrace or deck changes. |
| `analysis/export_textures_ue.py`, `analysis/make_contact_sheet.ps1` | Headless texture export, then a labelled contact sheet, for picking textures. |
| `analysis/export_meshes_ue.py`, `analysis/render_meshes_blender.py`, `analysis/extract_thumbs.py`, `analysis/make_mesh_sheets.ps1` | The visual pass, run in that order: export every pack mesh to FBX with its base colour textures (headless), render three views each in Blender 4.0, pull the editor thumbnails out of the `.uasset` files, then tile everything into labelled sheets in `Saved/LevelGen/visual/sheets/`. Delete `visual/fbx` and `visual/tex` afterwards (2.2 GB). |
| `VISUAL_CATALOGUE.md` | What each pack mesh looks like, and whether it fits a 2002 PH back alley. Written from the visual pass. |
| `LESSONS.md` | What works and what doesn't: the user's verdicts, and patterns learned from reference maps. |

**Running things:**
- **Python:** there's no `python` on PATH. Use
  `C:\Users\kevin\AppData\Local\Programs\Python\Python311\python.exe`, or UE's
  `Engine\Binaries\ThirdParty\Python3\Win64\python.exe`.
- **Headless:**
  `.\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\dump_map_ue.py`.
  It takes about 3 minutes, and the editor can stay open.
- **The bridge:** ask the user first (`Claude-Rules.md` §3).

**Conventions:**
- **Coordinates:** layout metres (lx east, ly south, from the NW corner) map to
  Unreal as X = (24 − ly) × 100 and Y = (lx − 27) × 100.
- **Wall pieces:** the pivot and yaw rules are in `TechnicalDesignSpec.md`,
  *`Lvl_BackAlleys`: first build*.
