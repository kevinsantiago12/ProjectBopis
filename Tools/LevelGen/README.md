# Level generation

Turns a layout file into an Unreal level. Owned by the level-generation thread.
**Read `LESSONS.md` before every build.**

**The generator is split (2026-11-08): levels as data.** `python Tools/LevelGen/gen_level.py [level]`, default `backalleys_arena`.

| Part | What it is |
|---|---|
| `gen_level.py` | The driver. Loads `levels/<level>.py`, runs its `PASSES` in order in one shared namespace (a pass sees what the passes before it defined, as when they were one file), writes the plan. A `.json` argument runs the arena's passes on that layout, as before. |
| `levels/backalleys_arena.py` | The arena's data: layout, `Saved/BackAlleys/plan3_*`, origin (27, 24), switches, the blocks treated specially (`NO_SPLIT`, `SPECIAL`, `DECK_FACE`...), its passes. |
| `levels/linear_slums.py` | The first story level, `Lvl_01_Slum`: layout `Linear_Slums_Layout.json`, `Saved/LinearSlums/plan_*`, origin (80, 60), folder `Slums/`. Its `setup()` gives the passes the level's bounds, ground heights per area, the buildings the player enters, and street blocks cut from the layout's mass. |
| `kit/core.py` | Stateless and importable: asset roots, side tables, vector maths, `shuffle_bag`, `frame()` (layout to Unreal and back), `write_plan()`. |
| `passes/*.py` | The arena generator's passes, cut out unchanged (2026-11-08) plus hooks: `base`, `houses`, `walls`, `terraces`, `roofs`, `stains`, `floors`, `finish`, `awnings`, `building_dressing`, `street`, `low_wires`, `stalls`, `posters`, `chain_wires`, `poles`, `graffiti`, `ground`, `dirt`, `litter`, `props`; the arena's own `arena_*`; the story levels' `story_ground` (slabs at heights, steps, parapets at drops, gates, the garage roof), `story_interiors` (rooms, walls with the layout's openings, windows, slabs, stairs, rails, roofs, bulbs), `story_lights` (street lamps and door bulbs, on; not in the slum's passes since 2026-11-09), `story_dress_begin` / `story_dress_end` (the arena's dressing passes, scoped to the houses a level dresses), `asia_cables` (AsiaSlum cable bundles on ring brackets, across the street and pole to pole, beside the thin wires), `story_road_clear` (nothing under `ROAD_CLEAR` over a main road: low wires lifted or taken out, writes `road_clear.json`), `story_light_fill` (more wall lamps and tubes where the slum's open ground is darkest, `LIGHT_FILL`; writes `light_fill.json`), `story_ground_dress` (hands the arena's `dirt`, `litter` and `props` the story level's open ground and its surface heights, `STORY_GROUND_TOP` / `STORY_GROUND_BASE`), `story_gameplay`, `story_resolve` (fixes the few trim and band corners the street rules leave on new ground), `story_sections` (each piece's section). |

**Rule: `Lvl_BackAlleys_Arena`'s plan must come out identical after any change to the driver, kit or passes.** Run the
arena from a scratch copy of `Tools/LevelGen` (so `Saved/BackAlleys` isn't touched) and compare with
`analysis/plan_identical.py <old dir> <new dir>`: every file byte for byte.

| File | What it does |
|---|---|
| `gen_level.py backalleys_arena` | Writes placement lists to `Saved/BackAlleys/plan3_*.json` (140 actors per file; the bridge's `read_file` caps at 80 KB) and `plan3_gameplay.json`. It prints a check that every open cell on the arena edge sits behind a door. |
| `gen_level.py linear_slums` | Writes `Saved/LinearSlums/plan_*.json`, `plan_gameplay.json` and `plan_layout.json` (the blocks the passes used, for the checks). Every piece has a `sec`, its section. |
| `build_story_ue.py` | Headless. Makes `Lvl_01_Slum` (not World Partition) with an `_Art` and a `_Gameplay` sublevel per section in `/Game/ThirdPerson/01_Slum/`, places each piece in its section's `_Art`, the player start in section 1's `_Gameplay`, the nav bounds and Lightmass volume in the persistent map, and saves. New maps only: it stops if the map exists. **Since 2026-11-09 the user handcrafts `Lvl_01_Slum`: don't rebuild it without their say.** |
| `create_hollow_world_material_ue.py` | Headless, new assets only. `M_BackAlleys_HollowBlocksWorld` / `MI_BackAlleys_HollowBlocks_World`: the user's hollow-block textures, untouched, mapped from world position at the Favela tile's density, for walls built as boxes. |
| `swap_sections_ue.py` | Headless, editor closed. Swaps parts of the existing `Lvl_01_Slum` for the current plan and leaves the rest alone: whole sections' `_Art` (generated actors only), the slum's houses wherever they are and the compound houses touching them, named pieces (`SWAP_IDS`), and loose pieces near the seam by shape. `REPLACE_DRY=1` reports without saving (fine with the editor open); `SWAP_ONLY=<names>` swaps only those pieces. Saves only the sublevels it changed. Only on the user's say for that change. |
| `flatten_sections_ue.py` | Headless, editor closed (done 2026-11-09). Folded `Lvl_01_Slum`'s 14 sublevels into the persistent map: each actor made again there from its data and tagged `S1`-`S7`, checked against its original, the sublevels taken out of the map (their files kept as a pre-merge copy). `REPLACE_DRY=1` checks without saving. |
| `ue_place.py` | Unreal side: one plan piece to one actor in the current level (lights, decals, meshes and their flags). Shared by `build_story_ue.py` and `swap_sections_ue.py`. |
| `story_night_ue.py` | Headless. The base night in `Lvl_01_Slum`'s persistent map: a Stationary moon, sky light, sky atmosphere, height fog (`Slums/Lighting`, replaced on a re-run). Only while the editor hasn't loaded the map. |
| `analysis/plan_identical.py` | Offline. Two plan folders, byte for byte; lists the first piece that differs. |
| `analysis/plan_source.py` | Lets the offline checks read any level: `check_overlaps.py linear_slums`, `check_dressing.py linear_slums`, `check_nav_roofs.py linear_slums`. Folders are mapped back to `BackAlleys/` for them. |
| `analysis/draw_plan.py` | Offline. A top-down PNG of a level's plan, with a height band (`--z lo hi`) and a crop (`--box x0 y0 x1 y1`, layout m): slabs pale, walls dark, stairs orange, rails blue, lights yellow. No libraries. |
| `strip_gameplay_ue.py` | Headless. Lists or removes the gameplay actors (the `BackAlleys/Gameplay` folder, project-class actors, player start, navmesh) from the map in `MAP`; `DELETE` False lists, True deletes and saves. For the menu it was superseded by `menu_hub_ue.py`. |
| `menu_hub_ue.py` | Headless, one-off. Strips the editor-made copy `Lvl_MenuScene_BackAlley` and makes the empty hub `Lvl_MainMenu`. Don't copy or rename these maps headless: the actor files stay behind. |
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
| `create_sign_boards_ue.py` | Headless, new assets only. `M_BackAlleys_SignBoard` and `MI_BackAlleys_SignBoard_<name>` for the user's lettered boards in `/Game/Project_Bopis_Local_Business_Signs/Wall_Boards`: each image cropped to its board and laid on the sign's street-side panel. The images aren't changed. |
| `analysis/sign_uv_ue.py` | Headless and read-only. `SM_Sign_A_001`'s UVs per face, to find where lettering goes. |
| `analysis/export_business_signs_ue.py` | Headless and read-only. Exports the business sign textures to PNG in `Saved/LevelGen/import/business_signs`, to see them as imported. |
| `create_poster_materials_ue.py` | Headless. `M_BackAlleys_PosterPaper`, its wear texture, and `MI_BackAlleys_Poster_<name>` for each image in `/Game/Project_Bopis_Posters` and `/Game/Project_Bopis_Local_Business_Signs/Posters` (`Dirt` 0.3 on those). Moves existing instances to the master, so close the editor first if there are any. Run `make_street_textures.py` first. The images aren't changed. |
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
| `analysis/ground_export_ue.py`, `ground_export2_ue.py`, `ground_export3_ue.py` | Headless and read-only. Export the candidate road and decal textures to `Saved/LevelGen/ground_tex/`, with each material's settings, as stored previews are blank. |
| `create_grime_materials_ue.py` | Headless. `M_BackAlleys_GroundGrime`, a decal that fades both ends, and `MI_BackAlleys_Grime_Soft`, `_Grit01`, `_Grit02`: dirt along the feet of walls. |
| `create_clean_table_material_ue.py` | Headless. `MI_BackAlleys_Table_Clean`, the market pack's table with its wear turned down. |
| `analysis/wood_table_material_ue.py` | Headless and read-only. The table's master, parameters and textures, to `Saved/LevelGen/table_tex/`. |
| `create_ground_materials_ue.py` | Headless. `M_BackAlleys_GroundPour` (mapped from world position) and `MI_BackAlleys_Ground_*`, the concrete and asphalt tones. |
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
  *`Lvl_BackAlleys_Arena`: first build*.
