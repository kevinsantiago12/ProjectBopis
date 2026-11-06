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
| `make_dress_textures.py` | Offline, no libraries. Draws the vent-block and plywood textures to `Saved/LevelGen/import/dress/`. |
| `create_dress_materials_ue.py` | Headless, new assets only. Imports those textures and makes `MI_BackAlleys_VentBlock_*` and `MI_BackAlleys_Ply_*` (Wood surface). |
| `analysis/dress_profile_ue.py` | Headless and read-only. Vertex spread per axis of the dressing meshes: which way they face and where their pivots are. |
| `make_street_textures.py` | Offline, no libraries. Draws the blank sign boards and the peeling-paint decal to `Saved/LevelGen/import/street/`. |
| `create_street_materials_ue.py` | Headless, new assets only. Imports those and makes `MI_BackAlleys_Sign_*` (Metal surface) and `M_BackAlleys_PeelDecal` + `MI_BackAlleys_Peel_*`. |
| `create_poster_materials_ue.py` | Headless. `M_BackAlleys_PosterPaper`, its wear texture, and `MI_BackAlleys_Poster_<name>` for each image in `/Game/Project_Bopis_Posters`. Moves existing instances to the master, so close the editor first if there are any. Run `make_street_textures.py` first. The images aren't changed. |
| `plan_delta.py` | Offline. Compares the plan with the one last placed (`Saved/BackAlleys/plan_applied/`) and writes what changed, in chunks, for `apply_delta_ue.py`. |
| `apply_delta_ue.py` | Bridge-side. Removes and places only what `plan_delta.py` listed, so a small change doesn't clear whole folders. Copy the plan to `plan_applied` afterwards. |
| `analysis/street_shape_ue.py` | Headless and read-only. Bounds, triangles, LODs, collision and material slots of the street dressing's meshes. |
| `analysis/stall_shape_ue.py` | Headless and read-only. Bounds and material slots of the AsiaSlum wall pieces on the shop row. |
| `analysis/stall_faces_ue.py` | Headless and read-only. The flat faces of the shop row's meshes by plane, to `Saved/LevelGen/stall_faces.json`, to find surfaces that share a plane. |
| `analysis/pole_shape_ue.py`, `analysis/pole_profile_ue.py` | Headless and read-only. Bounds, triangles and collision of the power poles, tyre and water meters, then where their vertices sit by height: crossarms, insulators, transformers. |
| `analysis/wheel_material_ue.py`, `analysis/meter_material_ue.py` | Headless and read-only. Exports the tyre's and poles' textures; reports the water meter's material parameters. |
| `analysis/graffiti_export_ue.py` | Headless and read-only. Exports the user's graffiti to `Saved/LevelGen/graffiti_user/` with their texture settings. |
| `create_wheel_material_ue.py` | Headless, new assets only. `M_BackAlleys_Tyre` and `MI_BackAlleys_Tyre`: the pack's wheel textures with a `Brightness` parameter. |
| `create_meter_material_ue.py` | Headless. `MI_BackAlleys_WaterMeter`, a child of the pack's with an old brass tint. |
| `create_graffiti_materials_ue.py` | Headless. `M_BackAlleys_SprayDecal` and `MI_BackAlleys_Spray_<name>_<paint>`, for the user's graffiti. The images aren't touched. Rebuilds the master's graph, so close the editor first once the level uses it. |
| `analysis/laundry_shape_ue.py` | Headless and read-only. LOD counts, triangles per LOD and bounds of the laundry meshes. |
| `analysis/awning_shape_ue.py` | Headless and read-only. Prints the bounds and slope of the awning meshes: which way they run and which edge meets the wall. |
| `analysis/door_bounds_ue.py` | Headless and read-only. Prints the local bounds of the meshes the generator fits by size: the AsiaSlum doors (`steel_door()`), `SM_Slate_01` and `SM_Ramp` (roofs), plus `SM_Ramp`'s corner vertices. |
| `analysis/check_overlaps.py` | Offline check of the plan for z-fighting: trims crossing, same-facing pieces overlapping, end caps lying in another wall's face. Run it after every generator change. |
| `analysis/check_dressing.py` | Offline check of the plan's building dressing: nothing on the stair walls, pipes apart and one per house, nothing across a pipe, plywood never alone; street dressing off hollow faces, thin walls, stair walls and pipes, wires above the second floor and clear of houses, every light with its fitting. Run after every change to the dressing passes. |
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
