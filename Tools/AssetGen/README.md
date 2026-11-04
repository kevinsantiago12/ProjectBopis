# Asset generation

Measures, preps and makes the assets the levels use. Owned by the asset thread;
the level-generation thread (`Tools/LevelGen/`) reads its output and doesn't
edit it.

| File | What it does |
|---|---|
| `measure_ue.py` | Headless and read-only. Measures every mesh the generator places and writes `manifest/<pack>.json` plus `manifest/index.json`. Add a mesh to `MESHES` (and to `OPENINGS` / `PROFILE` if it has holes or a walk surface), then rerun. |
| `create_metal_sheet_ue.py` | Headless, new assets only. `M_BackAlleys_MetalSheet` (the AsiaSlum corrugated sheet look plus a worn paint layer: `PaintColor`, `Coverage`, `Wear`, `BaseTint`) and `MI_BackAlleys_MetalSheet_Galv` / `_RedOxide` / `_Rust`, with copies of `T_MetalPlate_A_001_D/M/N/R` in `BackAlleys/Textures`. For `SM_MetalPlate_A_00x` slot 0. |
| `preview_metal_sheet.ps1` | Offline, no editor: applies the sheet's colour formula to the pack PNG and writes `Saved/AssetGen/export/metal_sheet_preview.png`, one strip per instance. Tune colours here first; keep its `$Looks` and formula in step with the script. |
| `repair_chb_texture.ps1` | Offline. Repairs the GPT hollow-block texture (made from `T_Bricks_01_BC`). It finds the brick's running-bond joint grid (bed joints: rows mostly grey across the width; head joints: columns mostly grey over a course), puts the source mortar back wherever GPT painted concrete over a joint, fills faint joints and drops the clay grooves. It then rebuilds the DirectX normal map from the corrected grid and writes to `Saved/AssetGen/import/hollow_blocks_fixed/`. |
| `create_hollow_blocks_ue.py` | Headless, new assets only. Imports the repaired texture as `T_BackAlleys_HollowBlocks_BC/_N` and GPT's originals as `T_BackAlleys_HollowBlocksGPT_BC/_N` (2048). Makes `MI_BackAlleys_HollowBlocks`: `M_BackAlleys_HollowBlocks` parent (made by `Tools/LevelGen/create_hollow_master_ue.py`), UV0, roughness 0.9, Concrete; it maps on the Favela tiles' UV0 like their red brick. **The user chose GPT's originals:** the MI now points at the `GPT` textures (set through the bridge), and the repaired ones are unused. |
| `make_paint_mask.ps1` | Offline. Cuts the inside of Favela's `T_decal_02` into a seamless tiling mask, `T_BackAlleys_PaintChips`, so the wall material's paint chips like the decals without their rough edge repeating as a grid. |
| `create_painted_walls_ue.py` | Headless, new assets only; run with `-Render` so the shaders compile and it reports their cost. The Favela paint look as `M_BackAlleys_PaintedWall` + `MI_BackAlleys_PaintedWall_<Colour>` (whole tile faces, one pass) and `M_BackAlleys_PaintDecal` + `MI_BackAlleys_PaintDecal_<Colour>` (colour that crosses tile faces). 12 colours, same flat colour in both, so a decal can continue a painted wall. Colours are the `COLOURS` table at the top. |
| `preview_painted_walls_ue.py` | Headless with `-Render`, saves nothing. Builds a throwaway map with real wall tiles, decals and two lights, and writes shots to `Saved/AssetGen/preview/`. No bridge, and no level or open editor touched. Takes about a minute. |
| `manifest/index.json` | All packs in one file: `{"units", "source", "meshes": {object path: entry}}`. This is the file `gen_level.py` should read. |
| `manifest/<pack>.json` | The same entries split by pack: `AsiaSlum`, `Megapack_Favela`, `Megapack_MiddleEast`, `Philippines_Markets`, `LevelPrototyping`, `Engine`. |

**Run:** `.\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\AssetGen\measure_ue.py`
(about 3 minutes, editor can stay open, no bridge). Exit code 1 is the usual
"HttpListener unable to bind" from the open editor holding port 8000.

## Paint materials: how to use them

- **Decal, by hand:** drag `MI_BackAlleys_PaintDecal_<Colour>` onto a wall. **Decal Size** is half-sizes: X is the depth (keep it small, about 6), Y and Z half the width and height. The mask's paint fills about 86% of the box, so size the box about 1.15 × the area you want painted.
- **Wall material:** assign `MI_BackAlleys_PaintedWall_<Colour>` to every slot of the tile (`SM_Wall_Tile_03` has 2). It's world-aligned, so axis-aligned walls only, and insets stay shallow (≤ 2 cm) like `M_BackAlleys_CHB`.
- **Settings on the wall material:** `Wear` (0 = the decal's coverage, higher thins the paint), `PatchWear` (0 = off; try 0.05–0.1 for big bare patches, it gets heavy fast), `MaskTile` (270 cm), `PatchTile` (430 cm), `PaintRough`, `ConcreteTint`.
- **New colour:** duplicate an instance and set `PaintColor` to the same value on both, in linear. `T_Concrete_01` is dark, so keep paint under about 0.55 linear or the chips turn stark.

**Cost** (`get_statistics`, SM6): the wall material is 386 pixel instructions and 7 samplers, against `M_BackAlleys_CHB`'s 408 and 9, so it's no dearer than the walls now. The decal is 360 instructions on top of the wall under it, for every pixel it covers. Neither is measured on the Deck.

**Headless rendering, what it needs** (found building the preview):
- `Editor.AsyncTextureCompilation 0`, before loading textures: nothing ticks a commandlet, so textures otherwise stay placeholders.
- `never_stream` on each texture, in memory, or they stay at low mips.
- `MaterialEditingLibrary.get_statistics(material)` finishes compiling it. Without this the shot shows the default checker.
- Avoid materials with no cached shader map for this mode: `MI_BackAlleys_Concrete` took over 8 minutes of full CPU before I stopped it.

## Manifest entry

Everything is **local, unscaled, in cm**. Key = object path without the
`.Name` suffix (e.g. `/Game/Megapack/Meshes/Favela/SM_Slate_01`).

| Field | Meaning |
|---|---|
| `bounds_min`, `bounds_max`, `size` | Render bounds. |
| `pivot` | Where the pivot sits per axis: `x:min` (at the low end), `x:max`, `x:centre`, `x:offset` (somewhere else: use the bounds). |
| `extends` | Which way the mesh runs from its pivot: `+X` (pivot at min), `-X` (at max), `±X` (around it). |
| `long_axis`, `thin_axis` | Largest and smallest extent. |
| `slots` | `index`, `name`, default `material`, `blend` (`BLEND_OPAQUE`, `_MASKED`, `_TRANSLUCENT`, `_ADDITIVE`), `two_sided`, `area_share` (share of the surface area; assumes polygon group n = slot n). **Check `len(slots)` before overriding materials.** |
| `lods` | `[{tris, verts}]` per LOD from the render data. |
| `tris_lod0`, `area_m2`, `nanite`, `lightmap` | |
| `collision` | `type`: `complex` (complex-as-simple: the triangles collide, holes included), `simple` (`shapes` primitives: `boxes` listed with min/max/rot, convex hulls counted only), `none` (traces only; pawns, physics and nav ignore it). `trace_flag` is the raw setting. |
| `sockets` | `name`, `loc`, `rot`. |
| `sides` | Per local side `+X` … `-Z`: `tris_on_bound` (outward triangles lying on that bounds face), `cover` (share of the bounds face they cover), `facing_area_m2` (all triangles facing that way, anywhere). |
| `open_faces` | Sides with `cover` < 0.05: open backs and tops, or shapes that don't fill their box (wedges, frames, round things). |
| `normal_spread` | Area-weighted mean \|normal\| per axis. Corrugation and planks: the ridges run along the axis with the low value. |
| `corners` | Every distinct vertex, for meshes with ≤ 40 (wedges, cubes, planes, flat cards). |
| `openings` | Wall/frame pieces: holes through the face plane on a 4 cm grid (so ±4 cm). `regions[]` with `min`/`max` (spanning the full thickness), `area_m2`, `fill` (1.0 = clean rectangle; low = a seam outline, ignore), `touches` (bounds edges it reaches; a door touches `-Z`). |
| `uv0` | UV channel 0: `u_along` / `v_along` = area-weighted \|direction\| per local axis that U and V increase along (0.98 on one axis = clean; mixed = rotated or atlas islands), `cm_per_u` / `cm_per_v` = median cm per UV unit. Grain and corrugation in the texture usually follow U. |
| `slots[].params` | The slot material's `vector` / `scalar` / `texture` parameter names, an instance's `vector_values` and its `parent`: shows whether it can be tinted without a new parent. |
| `top_profile` | Stairs, floors, roofs: top of the up-facing surface in 12 bins along the long horizontal axis, `[from, to, z]`. |

Normals follow Unreal's winding (clockwise front faces).

## Readings the generator needs (first pass, 2026-11-03)

| Mesh | Reading |
|---|---|
| `SM_windows_06` | 172.3 × 12.3 × 80.2, pivot at x max / y max / bottom: runs **−X**, depth **−Y**. Collision is its own triangles (complex), so it blocks nav at full height (the top rail at 76–80 cm closes every pane). The four panes are holes about 40 × 72 cm (z 4–76): bullets and sight pass through. At z scale 1.24 it stands 99.5 cm. |
| `SM_Stair_A_001` | x 0–451, y −303–+3, **z −215–0**: the pivot is the **top** front edge. It descends along **+X** to z −215 at x 451, in about 17 cm steps. Complex collision, so it walks on the steps. |
| `SM_Floor_A_001` | x 0–300, **y −300–0**, z 0–20 (walk top at 20). Pivot at x min / y max / bottom. Complex collision. 2 slots. |
| `SM_Wooden_part_05` | 190.5 × 4.4 × 15.7, runs **−X**, thickness **−Y**, width **+Z**. At pitch −90 it rises from the pivot (local −X → world +Z). Mirrored on Y, a back-to-back pair is 8.8 cm, centred on the pivot plane. One box collider. |
| `SM_Wooden_part_03` | 374.4 × 10.4 × 76.6 (x −373–+1.3), runs **−X**, depth **−Y**. One box collider over the whole rail, so it blocks like a 76 cm wall. |
| `SM_Pillar_01` | 42 × 42 × 797, **centred** in X/Y (−21–+21.5), bottom pivot. 3 LODs, complex collision, material `MI_StreetLampA_03`. |
| `SM_Slate_01` | x −193–190, y −112–42, z 71.2–79.0. Ridges run along **X**, the 3.83 m length (`normal_spread` x 0.01). |
| `SM_Ramp` | Corners: 1 m tall along y = 0, 0 at y = 100: matches `door_bounds_ue.py`. |
| `SM_HouseDoor_B_003` | x −112.6–2.3, y −8.9–3.6, z 0–228: matches the hand values. |
| Favela tiles, `SM_Wall_14`, `SM_MainBorder_04` | Match `check_overlaps.py` `LOCAL` within 0.5 cm. Door opening x 56–168, z 0–220; window opening x 56–168, z 92–220 (±4 cm grid). |

## Open items: prep and budget

From the manifest plus the placement counts in `Saved/BackAlleys/plan3_*` (2026-11-03 build: 3,195 actors, **3.14M LOD0 triangles**):

1. **`SM_MainBorder_04` is 73% of the level's triangles.** It's placed 918 times at 2,510 triangles each (2.3M), with complex collision. Fix: our own low-poly trim (a 150 cm extrusion of the same profile, about 30 triangles, box collision), made headless with Geometry Script. Alternatively, a simple box collider plus forced LODs on the pack mesh.
2. **`SM_Slate_01`**: 233 × 2,872 = 670k triangles. A coarser corrugated sheet of our own (about 100–200 triangles) keeps the silhouette.
3. **Default `WorldGridMaterial` slots.** These need an override or a real material whenever they're placed:
   - `SM_MetalPlate_C_001` (its only slot), `SM_Sign_A_001` slot 0, `SM_Cable_A_005`, `SM_AirConditioner_A_001` (both slots), `SM_HouseDoor_A_002` slot 1 (0.2% of its area);
   - `/Engine/BasicShapes/Plane` and `Cube`.
4. **Non-opaque slots** (the generator already overrides the first two): `SM_windows_02` slot 1 and `SM_Door_01*` slot 1 are additive; `SM_Garbage_bag_green_03` is masked.
5. **Complex collision on dense props** (when dressing returns): `SM_Concrete_Block_01` (3.5k), `SM_Garbage_bag_*` (4.6k), `SM_clothes_B_02` (5.8k). Give them simple shapes.
6. **Merging:** per-house merged meshes or Packed Level Actors before the Deck measurement (LESSONS: "Merge per block before any Deck measurement").

## Missing assets

- **Jeepney and tricycle stand-ins:** no pack has them. They're out under the blockouts-only rule (`Claude-Rules.md` §8) until the user asks.
- **Court lines decal and hoop:** not needed. The court left the layout on 2026-11-02.
- **Hollow-block (CHB) texture:** covered by the procedural `M_BackAlleys_CHB`. Since 2026-11-03 there's also a
  texture-based one, `MI_BackAlleys_HollowBlocks` (GPT's original), used on walls with no doors or windows (`Claude-Rules.md` §8).
