# Level generation: lessons

What works and what doesn't for generated levels, so the generator keeps getting
better across sessions. **Read this before every build.**

- **Rules** that can be checked go into the code too, as a constant or an assert in
  `gen_level.py`. This file says why.
- **Taste** goes here only.
- The user's verdicts are quoted and dated. Patterns learned from reference maps
  say which map they came from.
- **The level is `/Game/ThirdPerson/Lvl_BackAlleys_Arena`** (renamed from `Lvl_BackAlleys` 2026-11-07; arena levels end
  in `_Arena`). The bridge scripts check for it; older notes below may still say the old name.
- **Copying or renaming a map (2026-11-07, the main menu's scene):** these maps keep one file per actor. A headless
  `rename_asset` or `duplicate_asset` moves or copies only the `.umap` and leaves the `__ExternalActors__` folder
  behind: the result opens with 8 actors. Copy and rename in the editor (the bridge's `AssetTools.duplicate` /
  `move`, then save). A map the editor just copied is loaded there, so the rule further down applies: no headless
  re-save of it. Strip or edit it through the editor, or restart the editor before a headless run touches it.

---

## Standing rule: building blockouts only (user, 2026-11-03)

"forget all the dressings and, just make the building block outs. No other
objects in the level besides building blockouts as a rule."
- **What stays**, asked and answered:
  - the buildings: walls, doors, windows, bands, trims, roof lids and cores,
    the door end walls;
  - the gameplay actors: start, spawns, director, wander points, volumes,
    floor;
  - the gallery deck and stairs.
- **What's off:**
  - cover (stand-ins, kiosk, barriers, drums);
  - pickups;
  - all dressing (awnings, tin, cables, garbage, laundry, wires, roof drums,
    antennas, AC units, shop props);
  - decals.
- **In code:** the `COVER`, `PICKUPS` and `DRESSING` switches in
  `gen_level.py` are False. Their code stays. Turn one on only when the user
  asks.
- **Exception, 2026-11-03** (user: "I want stain decals next"): `STAINS =
  True` placed wall stain decals while the rest of the dressing stayed off.
  - **Withdrawn, then restored the same day:** "forget the decals
    completely", then "actually, bring it back but use decal dirt 8".
    `STAINS = True` with **`MI_Decal_Dirt_08`**, the darker drips on the same
    `T_decal_07` mask.
  - All the stain rules below still apply: whole faces, up to 4 tiles,
    length by span, 230–380 cm.
- **How stains work now** (user, same day):
  - **The ask:** "The decals you are currently using is meant to be stretched
    to the entire wall". Then "fix the alignment, first one is yours, second
    one is mine" (a hand-placed decal). Then "only use the dirt decal for
    now", and "not all of them need the dirt decal".
  - **The decals are whole-wall layers.** `analysis/inspect_decals_ue.py`
    exports the masks. Never place them as small spots.

    | Mask | Decals | What it is |
    |---|---|---|
    | `T_decal_07` | `Dirt_06`, `Dirt_08` | drips under a hard top edge at 24% of the height |
    | `T_decal_08` | `Dirt_07` | rising damp from the bottom |
    | `T_decal_02` | `Decal_02/04-08` | a rough-edged full-wall colour wash, tinted by `Decal Color` (the "green rectangle") |

  - **Rule now:** only `MI_Decal_Dirt_06`. Each wall tile gets drips with
    `P_DRIPS` 0.35.
    - Neighbouring picked tiles share **one decal stretched across up to 3
      tiles** (`STAIN_SPAN`). User: "the using decal on adjacent walls,
      stretch the decal accross up to 3 walls instead".
    - The tile after a group stays clean, so two drip decals never sit side
      by side.
    - **Single tile → shorter** (user: "if you are only using it on 1 wall,
      shorten it vertically. That particular decal looks bad on 1 wall full
      length").
      - A one-tile drip uses a 300 cm box (`DRIP_H_SINGLE`) with the same
        edge height, so its streaks stop about 1.1 m above the floor.
    - **Up to 4 tiles, length by span** (user: "its actually up to 4 walls,
      the ammount of walls covered should determine the length"):
      - `STAIN_SPAN` 4.
      - Box height was 300 / 367 / 433 / 500 cm for 1 / 2 / 3 / 4 tiles.
      - **Now 230 / 280 / 330 / 380** (user: "shorten the length more").
        The streaks end about 1.4 m above the floor on 1 tile, 0.6 m on 4.
      - Same edge height (+292); only how far down the streaks run changes.
    - **Whole faces, no half blocks** (user: "keep the stains consistent with
      the face and material, no half wall decals" … "half block i mean"):
      - Drips are decided **per wall run** (one face, one storey, one
        material), at `P_DRIPS` 0.35.
      - A picked run is covered across **every** tile, the half tile
        (`SM_Wall_Tile_03`) at its end included. Decal edges sit on tile
        edges, so no block is left bare or half covered.
      - *Misread first:* I took "half block" to mean "never on half tiles"
        and left them bare. User: "you are leaving a section undecaled",
        "you are also ignoring the half block at the end of the face".
      - Runs of more than 4 tiles split into equal groups of ≤ 4, side by
        side.
      - `STAIN_WIDEN` is now 1.12, so the mask's ragged sides end at the face
        edge instead of spilling onto neighbouring faces.
      - This replaces the per-tile pick.
    - Calibrated on the user's decal: 500 cm tall, 1.23 × the stretch wide,
      the mask's hard edge at storey +292 (behind the trim), so the streaks
      reach the floor.
    - Rising damp and the colour washes are off.
- The dressing lessons below stay as reference for when that happens.

## User verdicts

*(add them as "YYYY-MM-DD, user: "…" → what changed")*

- **2026-11-03, user: "Favela walls, 4 m storeys"** → the walls are the Favela
  kit. A storey is a 3 m tile, a 1 m concrete band (`SM_Wall_14`, the floor
  beam, or the parapet on the top storey) and an `SM_MainBorder_04` trim over
  the seam, with a cap trim on the top storey. The B2 shop fronts stay
  AsiaSlum.
  - **First look (two viewport captures, 2026-11-03):** it reads as intended:
    brick through plaster, the bands, parapets, drums, antennas.
  - **Not yet judged by the user in PIE.**
- **2026-11-03, user: "you have issues on overlapping faces, evident is corners
  of the buildings"** → wall pieces are 20 cm thick behind their face, so two
  walls meeting at a corner put an end cap in the other wall's face (z-fight).
  `corner_adjust()` now handles every run end:
  - **Inside corners:** run on 10 cm into the wall ahead.
  - **Outside corners:** north/south runs stop 20 cm short; east/west trims run
    on 7 cm.
  - **Rule:** never let two wall pieces' faces share a plane. Any new wall kit
    needs its thickness in this check.
- **2026-11-03, user: "we need to use mostly the concrete material… red brick
  walls… need to be non-red hollow blocks"** → no Favela red brick at all
  now.
  - **The mix:** concrete over blocks (`MI_BackAlleys_ConcreteOverBlock`)
    and plain `MI_Concrete_01` make up about 80% of tiles. Bare hollow blocks
    (`MI_BackAlleys_HollowBlock`) are about 18%: some street floors, patches,
    half the openings. Painted variants are accents only, at 20% weight per
    block.
  - **The materials** are made by `create_materials_ue.py`.
  - **The texture:** no pack has real CHB. MiddleEast's `T_Brick_wall`
    stands in. It's grey, but reads as rough stone blocks rather than smooth
    40 × 20 cm CHB. A proper CHB texture would fix that. *(Superseded by the
    CHB material, below.)*
- **2026-11-03, user: "Keep the texturing consistent per block face, ie 4 walls
  on the same block face should have the same texture"** → one material per
  block face (`face_mats` in the block loop): every storey, tile, door and
  window tile on that face. Each door end wall gets one material too.
  - **Favela's patchwork is off:** no ground-floor change, no 1–2 tile
    patches, no patched-in openings. This overrides the Favela patterns
    under "Materials" below.
  - **Faces of one block may differ.** The pick is weighted (`FACE_MATS`):
    concrete over blocks 0.45, plain concrete 0.2, bare blocks 0.15, paint
    0.2.
  - **Check:** 90 faces, 0 mixed.
- **2026-11-03, user: "second floor material can differ from ground floor. Also
  make more variant colors of MI_BackAlleys_CHB"** →
  - **Per storey:** the material is now per block face *and storey*
    (`face_mats[(side, s)]`). An upper storey keeps the one below 40% of the
    time (`SAME_AS_GROUND`). Door end walls work the same way.
  - **New instances:** 14, made by `create_chb_material_ue.py`:
    - Paint: Mint, Pink, SkyBlue, Cream, Peach, Lime, Lavender, Teal, Salmon,
      PaleYellow. Tinted `T_plaster_01` render, coverage 0.72.
    - Concrete: ConcreteWarm, ConcreteDark.
    - Bare blocks: BareLight, BareDark.
  - **Mix** (`FACE_MATS`): concrete family 0.5, bare blocks 0.15, 13 paints
    share 0.35.
  - **Check:** 165 face-storeys, 0 mixed, 20 materials used.
  - **Side effect seen in the capture:** where two faces of one block differ,
    the 2 cm corner overlap shows the other face's material as a 20 cm
    strip. Fine as a "corner column" with concrete; with a strong paint it
    reads as a coloured edge.
- **2026-11-03, user (screenshot): "This corner pattern is bad, fix it"** →
  two causes.
  - **The 2 cm outside-corner overlap** put one face's material on the other
    face as a 20 cm strip. Now every outside corner gets a **corner
    column**: a 20 × 20 cm cube in `MI_BackAlleys_Concrete`, 2 cm proud of
    both faces, 5 cm over the band's top (`COLUMNS`, placed after the walls).
    - Both runs stop 10 cm inside it.
    - The east/west trim crosses it to 7 cm past the corner; the north/south
      trim stops behind.
    - 55 columns. This reads like a CHB house's concrete corner column.
  - **`SM_Wall_Tile_03`** (the half tile, often at run ends) has **two
    material slots**. Only the first was overridden, so the pack's brick
    showed. Every slot is overridden now.
    - **Rule:** check a mesh's slot count before overriding materials.
- **2026-11-03, user: "keep the band color consistent with the walls"**, then
  "actually roll the bands back" → bands stay plain concrete
  (`MI_BackAlleys_Concrete`).
- **2026-11-03, user: "remove the material variation I asked you to do
  earlier"** → asked which: "All of it: one material".
  - `ONE_MATERIAL = True`: every wall face and storey uses
    `MI_BackAlleys_CHB_Concrete`; bands stay `MI_BackAlleys_Concrete`.
  - The per-face, per-storey and paint picks still run, so the random
    sequence and the window layout don't change, but their result is
    replaced.
  - **This overrides** the per-face, per-storey and colour-variant entries
    above. Those stay as reference only.
- **Safety, 2026-11-03:** `create_chb_material_ue.py` now only creates
  missing assets (`REBUILD = False`). A headless rebuild of
  `M_BackAlleys_CHB` while the editor had it loaded tried to force-delete
  it; the editor's file lock stopped it.
  - Never re-save assets the open editor uses from a headless run.
  - Confirm an edit applied before running the script it changes.
- **2026-11-03, user: "increase the number of windows" … "increase it by
  default"** → the new window rates are the generator's **defaults**
  (`P_GROUND`, `P_UPPER`).
  - Street floors: 25% windows (Favela 9%), doors still 12%.
  - Upper floors: 40% windows (Favela 13%).
  - In the 2026-11-03 build that's 106 window tiles, up from 50. Don't drop
    back to Favela's numbers.
- **2026-11-03, user: "Make a CHB material"** → `M_BackAlleys_CHB`
  (`create_chb_material_ue.py`).
  - **The blocks:** procedural 40 × 20 cm blocks, running bond, 1 cm mortar,
    a tone change per block.
  - **World-aligned:** x + y along the wall, z up, so stretched tiles don't
    stretch the blocks and blocks line up across tiles.
  - **Render:** an optional render over the blocks, chipped by `T_Wall_H`
    (`RenderCoverage`).
  - **Instances:** `_CHB_Bare` (0), `_CHB_Concrete` (0.8), `_CHB_Paint*`
    (0.75), `MI_BackAlleys_Concrete` (1.0, for the bands).
  - **Checked in a capture:** the bare walls read as hollow blocks.
  - **Limit:** world-aligned mapping assumes axis-aligned walls, which every
    generated wall is.
- **2026-11-03, user: "overlaps happens in the trims as well"** → trims stand
  7 cm proud, so at inside corners both crossed (coplanar tops). Now the
  east/west trim runs into the wall ahead and the north/south one stops at its
  front; the door end walls follow the same rule. Also found: the roof lid's
  sides lay in the parapet band's face, so lids are inset 5 cm and sit 5 cm
  lower.
- **2026-11-03, user: "you can overlap the wall model, just make sure the faces
  dont overlap, currently you detached the intersecting walls which is
  unnecessary"** → outside corners no longer stop one wall 20 cm short.
  - **Now:** both walls run 2 cm past the corner and intersect.
  - **What shows:** a 20 cm strip at the corner, which reads like the
    concrete corner column of a real CHB house.
  - **Rule:** overlap freely; only coincident faces matter.
    `analysis/check_overlaps.py` checks this (trim crossings, same-facing
    overlaps, end caps lying in another wall's face) and catches the old
    flush corners. **Run it after every generator change.**
- **2026-11-03, user: "isolate any new materials we created outside the
  external assets"** → all our materials live in
  `/Game/ThirdPerson/BackAlleys/Materials`, with our own texture copies in
  `.../Textures`. Nothing we make has a pack parent or texture.
  - The one outside reference is the project-wide Concrete surface type
    (`ImpactsVFXVol1/.../Concrete`), which the impact effects need.
- **2026-11-03, user: "add ocasional air conditioners"** → 12 window-type AC
  units on plain tiles.
  - AsiaSlum frame + unit + fan, mounted as the pack's demo map does: frame
    10 cm out, unit +10 out / −10 down, fan 15 cm aside.
  - At 2.3 m on street floors and 1.5 m above the floor upstairs.
  - The street-floor ones cross the 3 m trim line (not coplanar, so no
    flicker). Lower them to about 1.9 m if it looks wrong.

## Build notes (checked in the editor)

- **Glass:** `SM_windows_02` slot 1 and `SM_Door_01*` slot 1 are additive
  glass. Override them with `/Game/AsiaSlum/Material/MI_Glass_A_001` (opaque).
- **Nav on the roofs:** the block lids get nav mesh islands. They're
  unreachable and harmless, but the build pays for them. Turning off "can
  ever affect navigation" on the lids is a cheap fix.
  - **Checked 2026-11-03 (street-look build)** with
    `analysis/check_nav_roofs.py`. The bridge can't switch on the
    Navigation show flag, so this check is offline.
    - No roof, lid or terrace joins the ground, deck or stairs.
    - The near misses are the B17 and B19 terraces (395 cm). They touch the
      deck only diagonally at a corner, and banisters close every side.
      `SM_windows_06` collides on its own triangles, and its top rail at
      z 76–80 closes every pane. So it blocks nav at full height, though
      bullets pass through the panes. Confirmed by the AssetGen manifest.
    - The lowest roof piece is 322 cm, so no alley loses nav under an
      eave.
    - `EnemyBase` only asks for reachable points
      (`GetRandomReachablePointInRadius`), so islands are never picked.
    - Run the script after any change to roofs, terraces or the deck.
- **Cost:** about 3.5 actors per tile (tile, band, 1–2 trims, opening parts).
  Merge per block before any Deck measurement.

---

## Learned from the Favela map (2026-11-03, buildings only)

**Source:** `/Game/Megapack/Maps/Favela/Favela`, dumped headless by
`analysis/dump_map_ue.py` and grouped by `analysis/analyse_buildings.py`.
- It has 1,382 wall pieces and 1,048 decals.
- Most of it is one continuous terraced mass on a hillside.
- The cleanest unit is a 6 × 11.5 m, 3-storey house the map uses three times.
  It's the recipe below.

### Structure
- **Wall module:** `SM_Wall_Tile_*` / `SM_Wall_Windows_01` / `SM_WallDoor_01`.
  - Each is 2.25 m wide, 3 m tall and 20 cm thick. The pivot is at the bottom
    corner, and the wall runs along local +X.
  - `SM_Wall_Tile_03` is the 1.13 m half.
- **Odd lengths: stretch the tiles.** Runs are filled by scaling X to
  0.82–1.29, not by mixing in odd pieces. About 20% of tiles are stretched,
  most often to 1.11, 1.23 or 1.29.
- **Storeys are 3 m:**
  - a floor slab of `SM_Plate_Tile_03` (2.24 m square, 20 cm) with its top
    at the storey line;
  - an `SM_MainBorder_04` trim band (1.5 m, scaled 0.69 or 0.83) along the
    slab edge;
  - the same trim again capping the parapets.
- **Upper floors step back.** The top storey covers less floor than the one
  under it, which leaves a roof terrace.
  - The terrace has a parapet of `SM_Wall_14` (2 m long, 1.06 m tall,
    capped with trim).
  - It has railing posts (`SM_Fencing_03`) and a grille panel
    (`SM_Metal_Fence_02`).
- **Roofs:**
  - sheets of `SM_Slate_01` / `SM_SlateA_02`, scaled 0.77, over part of the
    top floor;
  - a water drum (`SM_Barrel_01` + cap) on a stand (`SM_Stand_01`).

### Openings
**Where they go:**

| Row | Plain | Door | Window |
|---|---|---|---|
| Bottom (street) | 79% | 12% | 9% |
| Top | 80% | 7% | 13% |

Middle rows are almost solid wall (94% plain).

**Doors:** an `SM_WallDoor_01` tile, plus `SM_Door_Jamb_01` and `SM_Door_01`
5 cm up.
- Upper-floor doors that open onto a terrace become a metal door
  (`SM_Metal_Door_01` + `SM_Metal_Window_Frame_03`).

**Windows:** an `SM_Wall_Windows_01` tile, plus the `SM_windows_02` insert at
+0.9 m.
- Most windows also get a **green metal grille**: `SM_Window_Frame_01`
  (scale 1.41 to 1.64, some rolled −90 to lie flat) or `SM_Window_Frame_02`
  (0.74).
- Wide openings use `SM_windows_06` (scale 1.66/1.66/1.24) or
  `SM_Window_Part_01`.
- **Small concrete canopies** go over openings: 3 × `SM_Plate_03` at 0.51
  scale in a row, plus vertical ones (pitch 90) as cheeks.

### Materials (the look)
- **One wall mesh, many materials.** The tile mesh is the same; the wall
  material is an override.

| Material | Plain tiles | Look |
|---|---|---|
| `MI_Wall_Brick_yellow_01` | 49% | painted plaster |
| `M_Bricks_Bland_01` | 31% | |
| `MI_OldWall_01` | 14% | old brick |
| `MI_Concrete_01` | 8% | bare concrete |
| `MI_Wall_Brick_White_01`, `_Blue_01` | rest | painted plaster |

- **Brick under the plaster:** the yellow, white and blue materials are
  children of `M_Bricks_Bland_01`.
  - They blend a paint/plaster texture (`First_BC`: `T_Wall_yellow_01`,
    `T_plaster_01`, `T_Wall_Blue_01`) with brick (`T_Bricks_01`) through a
    height map (`T_Wall_H`).
  - So bare brick shows where the plaster is chipped.
- **Materials come in patches, not per tile.** A tile shares its material
  with the next tile along the row 84% of the time, and with the tile above
  80% of the time.
- **Openings break the patch.** Door and window tiles are almost always
  `M_Bricks_Bland_01` or `MI_OldWall_01`, even inside a yellow wall. They
  read as patched-in brickwork.
- **The ground floor at the street is often old brick**
  (`MI_OldWall_01`), with painted plaster above it.
- **Trims:** `MI_MainBorderBright_01` everywhere; `MI_MainBorderBlack_01` on
  a few.
- **Door jambs:** `MI_Bricks_02`.
- **Window grilles:** `MI_Metal_Window_Frame_Green`, which has a colour mask
  (`M_Door_Color_Var_01`), so the colour can vary.

### Decals (wall grime)
- **Density:** about 0.6 per wall tile across the map, and 0.84 per tile on
  the template house.
- **Base size:** every one is 128 × 256 × 256, scaled. Depth scale is
  0.01–0.03 (1–4 cm projection), and roll is 90.
  - That size is the DecalActor default `DecalSize`, an **extent** (half
    size). With roll 90, scale Y is the height and Z the width.
  - The sizes in metres in the table below are scale × 2.56, so they're
    half sizes. The generator copies Favela's scale ranges directly.

| Decal | Mask | Height in the storey | Size |
|---|---|---|---|
| `MI_Decal_02` | `T_decal_02` | 0.5–2 m, around doors and windows; often two stacked at the same x (+0.9 and +2.0 m) | 0.8–1.7 m |
| `MI_Decal_05`, `_08` | `T_decal_02` | 0.5–2 m, around doors and windows | 0.8–3.1 m |
| `MI_Decal_Dirt_06` | `T_decal_07` | either 0–0.5 m (splash at the foot) or 2–2.5 m (streaks running down from the slab above) | 1.2–3.4 m wide |
| `MI_Decal_Dirt_08` | | 0.5 and 1.5 m | up to 4 m |

- **Leave out:**
  - `MI_BFlag_01` (the Brazilian flag);
  - `MI_RobotsD*` / `MI_FGRobots_*` / `MI_Decal_Robotics_01` (graffiti
    text);
  - `MI_WCup2028`, `MI_DBruno`.
  - The `MI_Graffiti_*` set needs a look first, for readable text that
    isn't Filipino.
- **Corners:** `SM_BrickWallCorner_01` at 0.35 scale with
  `M_Corner_decal_01`. It's a **translucent** mesh that shows brick at
  outside corners. Translucent, so use it sparingly on the Deck.

### Attached dressing (per house)
- **Antennas:** 2–4 TV antennas, `SM_Antenna_01/02/03`.
  - Scale 0.42, rolled −30 (they lean), on wall brackets
    (`SM_AntennaSupportPart_01/02`) at parapet height.
- **Pipes:** `SM_Rain_Pipe_01` is rare (4 in the whole map).

### For the Deck
- DBuffer is on, with its fixed cost already accepted (spec, *Bullet holes*).
  Each wall decal still adds overdraw, so grime goes where the player looks:
  - around doors and at alley mouths;
  - not on every tile of every face.
- `SM_BrickWallCorner_01` is translucent, and so are the `ScaneTarpaulinClear`
  tarps. Keep them rare, or leave them out.

### Covered roof terraces: the "balcony with a corrugated roof" (2026-11-03)

User: "study the balcony with currogated roof pattern in favela map".

**Source:** the 87 corrugated sheets in the Favela dump, grouped into 53
roofs, plus what sits under each.

**What it is:** almost always a **roof terrace**, not a hanging balcony.
- The flat roof of a lower part of the house (`SM_Plate_9` /
  `SM_Plate_Tile_03`, 20 cm), on the open sides a low parapet (`SM_Wall_15` /
  `SM_Wall_14`, 1.06 m, `MI_OldWall` or brick, trim on top).
- The taller wall of the next storey forms the back.
- It's roofed with corrugated sheets.

**The sheets:**
- `SM_Slate_01` (3.82 × 1.54 m, 7 cm; its underside sits 72 cm above its
  pivot). `SM_SlateA_02` (same size, centred pivot) mixes in.
- `MI_Slate_01` (rusty corrugated metal). All are **flat** (pitch 0).
- Yaw 0 / 90 / 180 / 270, often scaled 0.77 along their length (≈ 2.9 m).
- **Height:** underside about **2.75 m above the terrace slab** (median 276
  cm, range 153–309), so the edge against the taller wall sits just under
  that wall's next floor line.
- **Rows:** side by side, 145 cm apart (a 9 cm side lap) or 155 (butted).
  End to end, about 200 cm apart with the 0.77 scale (heavy overlap).
- Touching sheets differ in height by 0–3 cm, which avoids z-fighting on
  the overlaps.
- Typically 1–5 sheets per terrace.

**Support:**
- **Usually none:** 41 of 53 roofs rest on the walls around the terrace.
- **Where there's no wall to carry them** (6 roofs): a plank frame of
  `SM_Wooden_part_05` (1.9 m × 16 × 4 cm, `MI_wooden_part_01`).
  - Each piece is **two planks back to back**: the same transform, scale
    y +1 and −1.
  - Posts: pitch −90, scale 0.75, stacked twice ≈ 2.85 m, about 1.5–1.9 m
    apart.
  - Beams: pitch 0, in a grid in both directions, top about level with the
    sheets' underside.

**Under the roof:** a water drum on a stand (31 of 53).
- Four `SM_Fencing_03` posts (20 × 20 × 118 cm) in a 115 × 61 cm rectangle,
  `SM_Stand_01` on top at +1.18 m, `SM_Barrel_01` at +1.78 m, the cap at
  +2.6 m.
- (Those `Fencing_03` posts are stand legs, not railings.)

**Fit with `Lvl_BackAlleys_Arena`:**
- The five 1-storey blocks (B10, B17, B19, B21, B22) have flat roofs at 4 m
  against 2-storey neighbours: exactly this situation. A parapet on their
  open sides plus sheets at about 6.75 m would make covered terraces.
- They're also visible from the gallery deck.
- Not built: the blockouts-only rule needs the user's OK.

**Built 2026-11-03** (user: "Yes, build them"): `TERRACES = True`, folder
`BackAlleys/Terraces`, 142 pieces on B10, B17, B19, B21, B22.
- **Floor:** the 1-storey lid, in Favela's `MI_Concrete_01`. Our CHB
  material is world-aligned for walls and would streak on a floor. The tin
  roof sheets are gone.
- **Parapet:** `SM_Wall_14`, 1.06 m, `MI_BackAlleys_Concrete`, on every side
  open at storey 1, 1 cm in from the face line.
  - **Ends:** against a taller neighbour (ahead, or in line behind the
    face), run 10 cm into its wall. Where two parapets meet at an outside
    corner, the north/south one stops 20 cm short.
- **Roof:** one row of `SM_Slate_01` lengthwise (the blocks are 1.5 m deep,
  the sheet 1.54 m wide).
  - The underside sits 2.75 m above the floor, with 10 cm end overhangs
    and 30 cm laps. Alternate sheets are 2 cm higher.
- **Frame:** on open long sides, posts of two `SM_Wooden_part_05` back to
  back (pitch −90), 12 cm in from the face on the parapet, ≤ 1.9 m apart,
  up to the sheets. A plank-pair beam under the sheet edge.
- **Left out:** water drums (dressing).
- **Code trap:** the terrace code first reused the name `L`, which
  shadowed the layout. Never reuse `L`, `W`, `H` in gen_level.py.
- **Seen in a capture:** it reads right. The sheets carry nav (collision).
  Harmless, but `nocoll` on the sheets would remove it if the nav build
  cost matters.

**Balconies from stepped-back upper storeys** (user, 2026-11-03: "replace
some of the block's second story as balconies instead"):
- **How:** `BALCONIES` = 6 faces, `BALCONY_D` 1.5 m. A 1.5 m strip along the
  face is split off as a 1-storey block (`<id>b`, `balcony=<side>`), so the
  terrace builder roofs it: parapet, `SM_Slate_01` row, plank frame.
- **Which faces qualify:** 2-storey blocks only, one face each, picked by
  their own random sequence (`BALCONY_RNG`, seed 23). The face must be open
  along its whole length at both storeys, ≥ 6 m long, on a block ≥ 4.5 m
  deep. Not B2 (shop fronts) or B11 (the gallery deck).
- **The upper wall behind** a balcony alternates doors and windows
  (`onto_balcony`, like the deck face). The strip's street wall keeps normal
  doors and windows (`thin()` exempts balcony strips).
- **Built:** B28 west, B3 west, B7 north, B26 north, B25 north, B8 north.
- **Only the generator's blocks change.** The layout JSON (design canon) is
  untouched.
- **Seen in a capture (B7):** reads like Favela's stepped-back floors.

**Wide roof terraces with lean-to awnings** (user, 2026-11-03, with a
reference picture: "the balcony you have is an extension on the building, we
can use this, but what I really want is this", then "cut off the second
story section completely and build on it"):
- **The picture:**
  - a lower roof as an open terrace, walled by low parapets;
  - corrugated lean-to roofs hung off the taller wall over part of the
    terrace, sloping down and out, held by thin posts standing on the
    terrace floor;
  - water tanks on stands (left out: dressing).
- **How:** `WIDE_TERRACES` = 4 blocks ≥ 6 m deep (picked before the narrow
  balconies) lose the upper storey over half their depth along one face
  (on the 1.5 m grid, ≥ 3 m). The other half keeps it, as the taller wall.
- **`lean_to()`:**
  - **Sheets:** `SM_Slate_01` running down the slope (length outward), side
    by side along the wall 145 cm apart (9 cm laps), alternating 2 cm in
    height.
  - **Reach:** `AWN_D` 2.4 m out, falling `AWN_PITCH` 9°. The underside is
    `AWN_HIGH` 2.9 m above the floor at the wall, under the upper storey's
    band.
  - **Supports:** plank-pair posts on the floor 2.25 m out, ≤ 2 m apart and
    35 cm in from the ends (clear of side parapets), with a beam on top.
- **Parapets:** on every open side, and the arena edge counts as open
  (`taller_at`), so edge blocks (B24, B4) get their outer parapet.
- **Built:** B20 W (3 m), B24 N (6 m), B18 N (3 m), B4 S (6 m). The narrow
  balconies were re-picked: B26 N, B8 N, B7 W, B23 S, B6 S, B9 N.
- **Seen in a capture:** matches the reference: terrace, parapet, lean-to
  on posts, a door onto it.

**Terrace edges: capped parapets and frame banisters** (user, 2026-11-03:
"use main border on top of a stone bannister. also the favela level used a
wooden window frame as banisters as well. Use that as variation"):
- **Favela, from the dump:**
  - Parapets (`SM_Wall_14`) are capped with `SM_MainBorder_04` at 0.69
    scale, set 4 cm in from the outer face, so they overhang about 9 cm.
  - 108 of the 118 `SM_Window_Frame_01` and 68 of the 79 `SM_Window_Frame_02`
    stand on slab or parapet edges: they're the banisters.
    - `Frame_02` at 0.74 is a panel about 81 × 118 cm. Panels stand side by
      side on the edge, sometimes with a `SM_Metal_Fence_02` grille.
    - Tall `Frame_01` (1.41/1.64) act as uprights.
  - The material is `MI_Metal_Window_Frame_Green` (colour-mask, painted).
- **Built:** per terrace, `EDGE_RNG` (seed 41) picks the style.
  - **Stone parapet** with a `ParapetCap`: `MainBorder_04` along the top at
    +1.06 m, 5 cm in. At outside corners the east/west cap runs 8 cm past
    and the north/south one 2 cm back.
  - **Frame banister** (`BANISTER_SHARE` 0.4): `SM_Window_Frame_02` panels
    at about 81 cm, 0.74 deep and tall, on the edge 7 cm in.
    - The mesh runs along its local −X, so yaw = run + 180.
    - Posts on narrow terraces then stand on the floor behind it.
- **Fix found by the overlap check:** parapet ends treated the arena edge
  as a wall and ran 10 cm into it, so two parapets crossed at edge corners.
  End checks now use `taller_at` (only a 2-storey block counts).
- **This build:** banisters on B10, B17, B18b, B19, B9b (one more terrace
  too); capped parapets on the rest.
- **Corrected the same day** (user: "the banister window frame I was talking
  about was a wooden one"): Favela's wooden banister is **`SM_windows_06`**,
  not `SM_Window_Frame_02`.
  - It's 172 × 12 × 80 cm, wood (`MI_Windows_02`). 36 of its 40 stand on
    the top of a wall at a roof edge, never in a wall tile, at 1.66 / 1.66 /
    1.24 scale (about 2.85 m × 1 m).
  - Now: panels ≤ 2.85 m filling the run, 1 m tall, 12 cm deep, 13 to 1 cm
    in. On banister terraces the posts stand 20 cm in, behind it.
  - `SM_Window_Part_01`, the other wooden candidate, sits on the window
    canopies (`SM_Plate_03`), so it isn't a banister.

**Jalousie windows** (user, 2026-11-03: "Heres a Jalouse window texture, can
you put it on a plane and use this instead of the mesh window?"):
- **Textures:** the pasted WebP images were converted to PNG (PowerShell
  WPF `BitmapDecoder` reads WebP; System.Drawing doesn't) and imported
  headless by `create_jalousie_ue.py` as `T_BackAlleys_Jalousie_BC/_N` in
  `BackAlleys/Textures`. The normal map uses `TC_NORMALMAP` with sRGB off.
- **Material:** `M_BackAlleys_Jalousie` (ours, now unused; see *Parent and
  physics*): base colour, normal,
  roughness 0.35, and the project's Glass surface type.
- **Window:** `/Engine/BasicShapes/Plane` replaces `SM_windows_02`.
  - Scale 1.10 × 1.33 × the tile stretch, centre 111 cm along and 9 cm into
    the opening, 0.9–2.2 m up. Yaw = the wall's, **roll +90**.
  - Roll −90 faced it into the wall, which was invisible from the alley.
    User: "its facing the wrong way", "flip it vertically 180 degrees".
- **Texture size:** the images are 1254 px, not a multiple of 4, so the
  colour map first built uncompressed (BGRA8).
  - Set `PowerOfTwoMode` = `StretchToPowerOfTwo` and `MaxTextureSize` 1024
    (through the bridge, since the texture is loaded in the editor). Saved;
    it recompresses when next loaded.
  - **Rule:** in a headless import, check the import log for the built
    format.
- **Replaced by the double jalousie** (user: "Replace with this textures":
  two panes side by side, 1024 × 1024, so it compresses properly).
  - New: `T_BackAlleys_JalousieDouble_BC/_N` and
    `MI_BackAlleys_JalousieDouble`, an instance of `M_BackAlleys_Jalousie`.
  - The 98 windows were switched through the bridge; the generator uses it
    too.
  - The single-pane textures stay, unused.
- **Per-house window style** (user: "you can also use the old window as
  well, but make sure they are consistent house wise. IE all jalouse or all
  pull windows"):
  - `window_style()`: each block, its `<id>b` strip included, gets all
    jalousie planes or all Favela `SM_windows_02` inserts.
  - The inserts go where Favela puts them: 111 along, 11 in, +0.9 m,
    yaw + 180, with `MI_Window_02` and opaque glass.
  - `WINDOW_JALOUSIE_SHARE` 0.5, its own random sequence (seed 53).
  - This build: 10 jalousie houses, 13 insert houses, none mixed.
- **2 cm deep, not 9** (user: "push the windows more out, i can see some
  texture anomalies"). The opening's sill showed, and the world-aligned CHB
  wall material smears on horizontal faces.
  - **Rule:** keep insets in wall openings shallow (≤ 2 cm) so their
    horizontal reveals barely show.
  - The 98 planes were moved in place (7 cm out) and the generator updated.
**Doors: `SM_HouseDoor_B_003`** (user, 2026-11-03: "use this door
SM_HouseDoor_B_003, replace the current ones" … "make sure it fits"):
- **Mesh:** 115 × 13 × 228 cm (bounds x −113..2, y −9..4, z 0..228). Pivot
  at a bottom corner, running along local −X, outer face on local +Y: the
  same yaw as the wall, which is how the AsiaSlum frames seat it.
  `MI_MetalDoor_A_002`, one opaque slot.
- **Fit to the Favela door tile's opening:** the opening is what
  `SM_Door_Jamb_01` filled, 110 × 218 cm × the tile's stretch, centred
  111 cm along.
  - Scale (110·sx/115, 0.956, 218/228). The pivot sits 111·sx + 55.5·scale
    along and 10 − 2.5·scale in, 2 cm up.
  - The door has its own frame, so the jamb is gone.
  - **Checked in numbers** (the door spans exactly the opening's 59.7–177
    cm on B1) **and in a capture.**
- **AsiaSlum frames** (B2's shop row) use it too, at the pack's frame-local
  (205, 5, 0).
- `rnd.choice(DOORS)` is still called so the random sequence, and with it
  the layout, doesn't shift.

**Doors → the user's five plane doors** (user, 2026-11-03: "Heres a zip of
5 backalley "plane" doors" … "get them in the game"). This replaces
`SM_HouseDoor_B_003` in the wall door slots; the AsiaSlum frames on B2 keep it.
- **Textures:** rough timber, green plywood, blue plywood, corrugated
  metal, painted steel. Each is 1024 × 2048 (the slot's 1:2) with its own
  frame and hinges.
  - Imported headless by `create_doors_ue.py` as
    `T_BackAlleys_Door_<Name>_BC/_N`, using the **DirectX** normal (Unreal's
    convention), capped at 1024.
  - Material instances `MI_BackAlleys_Door_<Name>` of `M_BackAlleys_Jalousie`.
    Surface type is Wood for the first three and Metal for the last two, so
    impacts match.
- **Placement:** the jalousie recipe. An engine plane at 111·sx along, 2 cm
  in, z + 109, scale (1.10·sx, 2.18, 1), roll +90, wall yaw. It fills the
  110 × 218 opening exactly.
  - One texture per door from `DOOR_RNG` (seed 61). The current spread is
    14 / 10 / 6 / 9 / 4.
  - Checked in a capture: upright, edge to edge in the slot.

**Steel grilles and the louvred door** (user, 2026-11-03, with a screenshot
of `SM_HouseDoor_A_002` in a slot):
> "use that along with the metal doors in asian slums like so" … "for doors 2
> 4 and 5" … "you can still use the original door by itself" … "just make
> sure the hinges are on the inside" … "and right hand open, if not them
> roatate as appropriate"
- **"2, 4 and 5" means the AsiaSlum meshes `SM_HouseDoor_A_002/_004/_005`,**
  not plane textures 2/4/5. I first read it the wrong way. A_002 is the
  lattice grille, A_004 has bars, A_005 has bars plus a diagonal. **B_003 is
  the louvred solid door**, not a grille.
  - To identify a pack mesh without the bridge, pull the JPEG thumbnail
    embedded in its `.uasset` (look for `FF D8 FF` … `FF D9`).
- **The mix per wall door slot:** one draw from the five textures plus
  "steel", using `DOOR_RNG`.
  - "Steel" is B_003 alone, 3 cm in.
  - A plane gets a random grille in front half the time (`P_GRILLE`). The
    grille's front face sits 2 cm in, and the plane goes 1 cm behind its
    back face.
- **Fitting (`steel_door()`):** scaled by local bounds
  (`analysis/door_bounds_ue.py`) to 110·sx × 218.
  - A_005 is a bigger mesh (162 × 330) but the same 1:2 shape.
  - A per-mesh `turn` flag spins a door 180° about its bounds centre if its
    hinges come out wrong.
- **Hinges:**
  - Right-hand means hinges on the right seen from the alley.
  - B_003 and A_002 already show the handle on the left and hinges on the
    right, from captures. A_004 and A_005 are assumed the same (same family).
  - The plane textures paint their hinges on the left, so the planes are
    mirrored (negative X scale, `PLANE_HINGE_RIGHT`).
  - Painted hinges can't be moved to the inside face.
  - **The grilles' hinges were on the alley side.** User, after looking in
    the editor: "Turn the grilles".
    - A_002/A_004/A_005 now have `turn = True`: yaw + 180 **and** a negative
      X scale (mirrored along the run). The hinges go to the inside face and
      stay on the right.
    - A plain 180° turn would have made them left-handed.
    - Same box, so the plane behind is unchanged. Swapped in place (25) and
      saved; checked in a capture.

- **Capture gotcha:** `CaptureViewport` sometimes returns an empty world
  (no buildings), apparently from stale occlusion when the camera jumps far.
  Capture again and the second frame renders.

**Philippine street look: houses, heights, setbacks, metal roofs** (user,
2026-11-03, with a photo of a back street; then "All four at once"):
> "most philippine houses still use metal roofs even in stone houses. They
> also vary in height, is not consistently aligned with each other on the
> street, and 1 storey houses with currogated roof exists as well"
>
> "also most metal roofs have at least a slight slope for water to slide on"
- **Rule:** a metal roof is never flat. Every corrugated roof slopes at
  least 3 degrees.
- **Fixed houses** keep the layout's storeys, 4 m storey height and walls:
  - those touching the gallery deck or a stair;
  - those within 5 m of a spawn door (its end wall is 2 storeys of 4 m and
    runs 1.1 m into the blocks either side);
  - the B2 shop row, the B10 stub and B11.
  The layout JSON is not changed.
- **Houses:** blocks 9 m or longer split into houses 4.5-7.5 m wide along
  their long axis (`HOUSE_W`, `HOUSE_RNG` 71). Ids look like `B28h3`.
  Balcony strips are picked after the split.
- **Heights:**
  - Free houses get 3.4-4.2 m storeys (`STOREY_H`). The 3 m tile stays and
    the band above it takes the rest.
  - `P_THIRD` (0.4) of the free 2-storey non-balcony houses get a third
    storey.
  - `SHACKS` (4) inner free houses become 1-storey corrugated-roof houses
    (3.3-3.7 m). Never on the arena edge, since the edge houses are the
    arena's outer wall.
  - Balcony strips follow their parent's height.
- **Setbacks:** street faces open along their whole length are set back 0,
  0.3 or 0.6 m (`SETBACKS`), inward only, so no alley gets narrower than
  the layout. Terrace houses and balcony parents keep their footprint.
- **Walls are now geometric and height-aware (`side_intervals`,
  `cover_top`).**
  - A side splits wherever another house's edge crosses it.
  - A storey's wall shows wherever what stands outside is lower than the
    storey's top.
  - Where a lower neighbour still hides its bottom 50 cm or more, the run is
    "buried": plain, no openings, no stains, and no trims under that roof.
  - Probes sit 5 cm off corners, not 0.75 m, because setbacks put houses
    off the 1.5 m grid.
- **Corner rules the new shapes needed:**
  - **Diagonal** (two houses touching at a point): an outside corner with a
    column, not an inside one.
  - **Lower house in line:** a column, and both trims stop behind it.
  - **Junction** (a face that shows fully, then only above a lower roof):
    the runs meet flush with no corner. Trims at the lower house's height
    stop 17 cm short.
  - Columns are keyed per corner and direction pair, and tops alternate
    +5 / +7 cm.
  - Only one parapet stands between two terraces of about the same height
    (the lower id's).
  - Spawn end walls count as tall walls for parapets.
- **Metal roofs (`metal_roof`):**
  - **Slope direction:** it falls toward open ground (or the arena edge
    behind), never into a taller wall. A taller wall takes the high edge,
    with the rise kept 30 cm under that wall's top.
  - **Slope:** 5-10 deg single slope; or two-sided 12-15 deg on free-standing
    houses 6 m or deeper (`P_GABLE` 0.4).
  - **Sheets:** `SM_Slate_01` in rows of 4.5 m or less down the slope (20 cm
    laps, each lower row 3 cm under) and columns of 2.2 m or less (9 cm laps,
    alternate ones 2 cm up), so no two sheets share a plane. The underside
    clears the low wall top by 22 cm, over the trims.
  - **Overhangs:** eaves 40 cm, verges 25 cm, open high side 15 cm. Against a
    neighbour the roof stops 5 cm short (same height) or 10 cm short (taller
    wall).
  - **Gap fill:** the gap between the wall tops and the roof is filled in
    the wall material, 2-18 cm in from the face: a 26 cm strip on every side
    that shows, an `SM_Ramp` wedge on the sloping sides, and a tall strip
    along an open high side.
  - **`SM_Ramp`:** extruded along local X; 1 m tall at y = 0, falling to 0 at
    y = 1 m. Measured with `analysis/door_bounds_ue.py`.
  - The concrete lid stays under the roof as the ceiling.
  - `P_FLAT` (0.1) of the houses keep a flat concrete roof ("most" have
    metal).
- **Result:** 53 houses (3 with 3 storeys, 4 one-storey metal), 17 setbacks,
  32 metal roofs (192 sheets, 5-13 deg), 5 flat. 3,195 actors (was 2,594).
  `check_overlaps` is clean. Traces are unchanged.
- **`check_overlaps` now skips two cases:** coincidences inside a corner
  column, and caps sealed against another cap at a junction.
- **Bridge:** `read_file` only reads under `Content/` and `Saved/`, and the
  script sandbox has no `exec`. So each placer call carries the placer
  source itself; it can't load it from `Tools/`.

**Metal roofs redone: shed roofs with a kisame** (user, 2026-11-03, with a
photo of a model shanty: lean-to roofs of mixed rusty and galvanised sheets,
metal flashing, timber fascia). Then: "it shouldnt be just a metal slate on a
sloped surface, theres usually a "kisame" there". Asked where; answer: "Both"
(a flat ceiling with the roof on a frame above it, and boarded eaves). This
replaces the sheets, gap fill and gables above; the slope rules stay.
- **Kisame** is the ceiling. Here it means the walls stop at the flat
  ceiling (the concrete lid). The roof sits on a frame above it, and the
  frame is closed in timber, not in wall material.
- **Slope:** mostly single slopes (`P_GABLE` 0.15, was 0.4); two-sided roofs
  get a galvanised ridge cap.
- **Sheets:** AsiaSlum `SM_MetalPlate_A_001`–`004` (real corrugated sheets,
  1.62 m wide, 3.25 m or 1.65 m long, four rust variants, 364 tris).
  `SM_Slate_01` is 2,872 tris and reads as dark ribs. Pivot at the top end,
  centred; the sheet hangs down local −Z.
  - Placed in columns down the slope: 18 cm side lap (alternate columns
    2 cm up), 15 cm end laps (each upper sheet 1.5 cm over the one below).
  - Long and short sheets mixed per column, scaled to the true slope length.
  - ±1° skew per sheet; the eave is ragged by 0–5 cm.
  - `SHEET_UP` says which local Y faces up (+1). The AssetGen manifest says
    the sheet is modelled with both faces, so either way up renders. +Y has
    the wider pans (crests cover 49% of +Y and 19% of −Y), so +Y up it is.
    The ridges run along local Z, down the slope. Collision is one convex
    hull.
  - **Finishes:** AssetGen's `MI_BackAlleys_MetalSheet_Galv` / `_RedOxide`
    / `_Rust` override slot 0. They have our own parent and copied
    textures; the user said "Yes, make them". Each roof has a main finish
    (galvanised 50%, red-oxide 30%, rust 20%), and 25% of its sheets are
    replacements in another finish. The flashing uses `_Galv`. They aren't
    seen lit yet: a default checker in captures means the shader failed to
    compile (see the editor log).
  - `SM_wooden_beams` UVs run once along the full 7.38 m length. A short
    board compresses the grain; that's fine at fascia and board sizes.
- **Frame (one paint per house: MiddleEast `SM_wooden_beams_01/02/03/05`,
  natural, blue, green, brown; 12 tris, centred pivot, length along Y):**
  - **Clearance:** the sheet underside clears the low wall top by 42 cm
    (`ROOF_CLEAR`).
  - **Fascia** (3 × 20 cm) under every open eave, and under an open high
    edge on single slopes.
  - **Kisame boards:** level boards (2 cm) from the fascia's foot back to
    the wall face. Their underside clears the top trim (wall top + 8) at up
    to 15°.
  - **Barge boards** under the open sloping edges, 1 cm outside the verge so
    the fascia and kisame ends sit inside them. On two slopes the pair meet
    at the ridge.
  - **Weatherboards:** 2.5 cm thick, 2 cm behind the wall face, from wall
    top − 8. They go on every side the old fill went on: open and flush, not
    walls or the arena edge.
    - **One board per side** (user, 2026-11-03: "the back of the roof has 5
      wood pieces, use one scaled board instead"). It replaced the stacked
      20 cm rows and runs up to the kisame on eaves and high edges.
    - **Sloping sides are sealed** (user: "close the sides … i mean seal
      it"). The stepped rows left dark notches under the barge.
      - The board runs up to the slope's lower end.
      - An `SM_Ramp` wedge in the house paint fills the triangle under
        each slope, its top 1 cm under the sheets.
      - On two slopes there are two wedges, meeting at the ridge.
      - A run that starts partway up a slope gets a level filler under
        its wedge.
      - `BOARD_MAT` maps each beam to its `MI_BackAlleys_Boards_*` paint.
    - **Wedge orientation:** the wedge lies on its side (local +Y up, +Z
      down the slope). Its UVs no longer matter (below).
    - **Timber is mapped from world position** (user, 2026-11-03: "roof
      textures are busted too", a wedge in grey streaks).
      - **Cause:** MiddleEast's `T_wood_*` are atlases. Only part is real
        wood or paint, the rest is smeared padding. The beam's own UVs stay
        on the good part, sampling about 3% of the texture's height; a beam
        stretched into a tall board magnifies that, and `SM_Ramp`'s UVs
        land on the padding.
      - **Fix:** `M_BackAlleys_Boards` (`create_board_material_ue.py`), as
        `M_BackAlleys_CHB` does for blocks: no mesh UVs, so a board and its
        wedge line up. 20 cm planks with a dark gap and their own tone, each
        sampling only the usable band. Measured bands: wood_01 V 0.29–0.99,
        wooden_beam_01 V 0.01–0.44, blue and green dark stripes at
        0.281 + 0.0441i, about 0.02 tall.
      - **Seen in captures:** continuous planks across a board and wedge,
        no streaks (`16_boards_wedge_B7`).
      - **Rule:** never put a pack atlas material on a mesh it wasn't made
        for. The fascia, barge and kisame are real beams and keep their UVs.
    - **Count:** 441 boards became 114 boards and 53 wedges. The level is
      3,602 items. `check_overlaps` is clean; nav is unchanged (lowest roof
      piece 3.22 m, no roof joins the deck or stairs).
  - **Flashing** where a high edge meets a taller wall: a strip on the
    sheets and one up the wall (`SM_Cube`, `MI_BackAlleys_Flashing`,
    no collision). The rise keeps 40 cm under that wall's top.
- **Pieces that tilt in pitch and roll** go through `put_axes`. It takes the
  local axes in world space and returns the rotator with `axes_rot`, which
  is `FMatrix::Rotator`; it round-trips to 1e-5. `check_nav_roofs.py` now
  uses the full `FRotationMatrix`. Its old roll sign was wrong; that only
  mattered for the plane doors.
- **Result:** 32 metal roofs, 1,023 roof pieces: 430 sheets, 439 boards, 45
  fascia, 45 kisame, 38 barge, 26 flashing and ridge. The level is 3,863
  items, up from 3,195. `check_overlaps` is clean. Nav is unchanged: no
  roof joins the deck or stairs, and the lowest roof piece is at 3.22 m.
- **Rebuilt (2026-11-03, side session `backalleys-rebuild`):**
  - **Placement:** 3,876 placed, 0 failures, saved.
  - **Traces (before the stairs were rebuilt):** spawns ground 0 and clear; stairs [400, 238, 74, 400, 74];
    deck 400.
  - **Captures:** in `Saved/BackAlleys/captures/2026-11-03_kisame/`. All
    three sheet finishes render. The patchwork, fascia, barge and
    weatherboards read right. The kisame is level but near-black in
    shadow.
  - **Notches:** small dark notches between the stepped weatherboard ends
    and the barge board. Fixed by the sealed sides (*Weatherboards* above),
    and swapped in the level.
  - **Red-oxide** looks bright orange next to the photo's dull brick-brown.
    It's the user's call (AssetGen's material).
- **Bug, fixed in the generator, not yet in the level:** the flashing
  strips sat off the wall.
  - **Cause 1:** when `put_axes` turned X round for right-handedness, it
    also negated the anchor. That's harmless for centred meshes, but it put
    `SM_Cube` strips one length off (25 cm on B14, B15, B25h1, B25h2, B9h1,
    and the ridge caps).
  - **Cause 2:** the strip stopped at the sheet ends, 9–10 cm short of the
    wall. It now runs to 2 cm off the wall and meets the upstand. All 12 are
    within 2 cm.
- **Placer gotchas** (from the rebuild):
  - Placed actors are named `StaticMeshActor_UAID_…`, not by label, so
    `LVL + label` doesn't resolve. Map them with `ActorTools.get_label`.
  - `find_actors(name=…)` is a substring match: `B18_S0_0_0` also returns
    its `_Band` and `_Trim300`.
- **Capture gotcha:** stale culling repeats at a transform, and moving
  30 cm doesn't help. Change the view direction instead (bad frames were at
  yaw 45–80).

**Wall seams** (user, 2026-11-04: "I can see seams on the walls, right after
the height and alignment parameter changes"). Thin dark vertical lines.
- **Cause:** off the 1.5 m grid, tiles have fractional widths, and rounding the
  plan (position to 0.1 cm, scale to 4 places) left gaps of up to 0.08 cm at
  some joints. That's under a pixel, so it shows as a thin, broken line.
  Close-ups: a 0.075 cm gap shows it (`19_joint_gap_B23`); a 0.075 cm overlap
  doesn't (`20_joint_overlap_B8b`).
- **Fix:** `TILE_LAP` (0.4 cm): each tile runs past its slot, under the next.
  All 306 joints now overlap by 0.33-0.48 cm. After: `21_joint_fixed_B23`.
- **Rule:** never butt modular pieces at fractional scales; overlap them by
  more than the plan's rounding and under `check_overlaps`' 1 cm.
- **Also fixed:** the half tile's scale divided by 113; its mesh is 112.5.
- **A different line, left as is:** the corner columns stand 2 cm proud
  (`COLUMN_PROUD`), so their edges show about 20 cm in from a corner, bright in
  sun and dark in shade.

**Building floors** (user, 2026-11-04: "can we put a floor on the buildings.
currently the door go all the way to the road floor, which is never the case in
real life. There is usually "riser" below the door that lifts it off the
ground. The solution to this is to put the buildings on top of a "building
floor"").
- **What:** every house and door end wall stands on a concrete slab
  (`SM_Cube`, `MI_BackAlleys_Concrete`, folder `BackAlleys/Floors`), `FLOOR_H`
  18 cm tall and proud by `FLOOR_OUT` 8 cm over open ground. It doesn't reach
  into a neighbour or past the arena edge; a side only partly open gets strips
  along the open parts. 82 pieces.
- **How:** one height for all, applied as a last pass that adds `FLOOR_H` to
  Blocks, Lids, Terraces, Roofs, SpawnDoors and Decals. All the corner, cover
  and trim logic still works in unlifted heights, so none of it changed.
- **Bridge gotchas found applying this:**
  - The editor reopens on `Lvl_Sandbox`. Check the level first. `load_level`
    silently drops unsaved changes, so ask the user to open it.
  - Asking about a folder that doesn't exist stops the whole script, and
    `try`/`except` can't catch it. `sync_plan_ue.py` has `NEW_FOLDERS` for this.
- **Stays at road level:** the road, `Floor_Collision`, the gallery deck, posts
  and stairs, and the gameplay points. Doors onto the deck now have an 18 cm
  step up too.

**Painted houses** (user, 2026-11-04: "One color per house, but some side can
remain unpainted"; "keep the dirt decal placement there").
- **Materials:** AssetGen's `MI_BackAlleys_PaintedWall_<Colour>`, 12 colours,
  world-mapped, Concrete surface (from the parent).
- **Rule:** `P_PAINTED` (0.5) of the houses take one colour. A face with a door
  or window always takes it; a windowless face takes it `P_PAINT_SIDE` (0.5) of
  the time; hollow-block faces stay as they are. Faces never mix.
- **Follow the colour:** bands (see *Bands and borders*), parapets, and a corner
  column when both its faces have it. Trims, timber and door end walls don't
  change. The drip decals stay.
- **My calls, not the user's:** half the houses, half the windowless sides, and
  hollow-block faces staying unpainted. The user didn't choose these; each is
  one setting.
- **Result:** seed 103: 21 of 41 houses; faces 40 painted, 16 hollow, 56 bare;
  23 columns. No mixed face, no house with two colours.
- **Paint decals** (`MI_BackAlleys_PaintDecal_*`) aren't placed; they're for the
  user, and cost about 360 extra instructions per pixel.

**Window grilles** (user, 2026-11-04: "find an appropriate window grill and put it
in the first floor windows", "more variation is appreciated").
- **Where:** every ground-floor `SM_Wall_Windows_01` window, 37 in all (`z == 0`
  in `favela_tile`). "First floor" was taken as the ground floor. B2's one
  AsiaSlum shop window (`SM_HouseWindow_A_001`) doesn't get one.
- **Which:** five kinds, drawn from a shuffle bag per house, so they're balanced
  in no fixed order and a house matches itself: `SM_Window_Frame_02` (green steel, what Favela uses),
  `SM_Windows_grill_01` (olive bars), `SM_Windows_grill_02` (dark grid),
  `SM_metal_fence_01` (sparse bars), `SM_SecurityWinodw_A_001` (rusty lattice on
  brackets). 96-896 tris each, against the 82k AsiaSlum lattice grilles.
- **Fit:** the opening is 112 x 128 cm x the tile's stretch, centred 112 along
  and 156 up. Each grille is scaled to 122 x 138 cm, 5 cm over the wall around
  it, starting 0.5 cm off the face. `WIN_GRILLES` holds each mesh's bounds, run
  axis and depth; `SM_metal_fence_01` runs along local Y, so it turns 90 less.
- **No collision** (`nocoll`): thin and cheap; shots go through to the window.
- **Not recoloured:** AsiaSlum's coloured `MI_MetalFrame_A_001_*` are atlases
  made for other meshes (see *Timber is mapped from world position*).
  `MI_Metal_Window_Frame_Green` has a colour mask, so painted variants are
  possible as new instances.

**Gallery stairs made walkable** (user, 2026-11-04: "The stairs you are using is
too steep and unnavigable, use another", "or find a way to make it less steep").
- **Cause:** one `SM_Stair_A_001` (natively 4.5 m run, 2.15 m rise, 25 deg, 16.5 cm
  risers) was stretched to 5 x 4 m: 39 deg, about 31 cm risers, close to the
  nav's 35 cm step limit. Don't stretch a stair's rise; add flights.
- **Now:** two flights in line (`STAIR_RUN` 7 m, about 30 deg). The lower flight's
  flat top is a landing at 200 cm, with two `SM_Pillar_01` under it.
- **Measured by trace:** risers 13-17 cm; biggest step 23.7 cm, at the bottom of
  each flight.
- **Layout:** the stairs run 2 m past the layout's 5 m rect, which stays as it is.
  Clear ahead is now 3.4 m (west) and 9.4 m (east), not 5.5 and 11.5.
  `check_nav_roofs.py` uses the 7 m.

**Hidden patterns** (user, 2026-11-04: "we are trying to have patterns in building
but have the player not see patterns when playing"). This is the goal behind all
the variation rules.
- **Do:** build from rules with exceptions. Use `shuffle_bag` to spread a set of
  options evenly: a fixed cycle repeats along a street, and plain random clumps
  (a grille pick came out 15 / 10 / 7 / 3 / 2).
- **Do:** make sure a visible difference doesn't always mean the same thing. A
  missing border also happens on bare concrete, not only on painted houses.

**Bands and borders** (user, 2026-11-04: "the mainborder in between the first and
second story needs more variations: keep some as they are, if the paintjob for
the whole face is the same, remove the border. If there is a band on the second
story, portrude the band out a bit in some houses"; "the bands have different
paint jobs in some houses, try to avoid these, you can leave some for variation
purposes").
- **Band colour:** on a painted face the band always matches (user: "when the face
  is painted, the band looks off if left unpainted. It works for hollow blocks but
  not for painted"). I'd left 20% contrasting for variety, as the user first
  allowed; that's off (`P_BAND_CONTRAST` 0). Hollow blocks and bare concrete keep
  concrete bands. This replaces 2026-11-03's "actually roll the bands back".
- **Between the floors, each building has one of three** (user: "so the building
  will either has 1. No borders, 2. A border 3. A portruding band"), on all its
  faces. Picked from shuffle bags in the pass before the chunks (`_style`):
  - a painted house: **none or protruding** ("if the paintjob for the whole face
    is the same, remove the border");
  - an unpainted house: **any of the three**;
  - houses touching the gallery can't protrude: they get none. The band would stand
    above the deck floor and in the stairs' headroom.
- **Border** is each storey's `Trim300` but the top one's. A balcony strip counts
  with its house, or the line would stop short. Top trims don't change.
- **Protruding band:** the band between floors ("the band between the 1st and 2nd
  floor, not the top floor"; I first did the top one). `BAND_OUT` 15 cm proud.
  **It has to clear the trims' 7 cm:** at 5 cm they hid it (user: "the protutuding
  band, i cant see it"). The band gets thicker, not moved; its back stays 20 cm
  behind the face. At an outside corner the east/west band runs past the corner to
  flush with the other band's face, and the north/south band stops at that band's
  back, as the trims do. Beside a flush face it stops 1 cm short of the corner.
  Inside corners are buried in the wall ahead.
- **Drips follow the treatment** (user: "you need to reevaluate the placements of
  Dirt decals, becuase of the new border and band rules. The treatment themsleves
  looks good"). `MI_Decal_Dirt_08` has a hard top edge, which must hide behind a
  ledge. It sat at +292, behind the border:
  - **Border, and every top floor:** as before.
  - **Protruding band:** the lower floor's edge moves up to +304, behind the band
    (`DRIP_EDGE_BAND`), so the streaks come out from under the ledge.
  - **No border:** the lower floor's drips go; nothing could hide the edge, and
    dirt doesn't start mid-wall. A face that had them gets drips at the top floor
    if it has none there. Lengths don't change (the user asked for them shorter).
- **Bands overlap too:** `TILE_LAP`, as the tiles.
- **Applying:** `sync_plan_ue.py` can't change a placed actor's mesh. If a piece
  keeps its label but gets a new mesh (the grilles here), remove and re-place it.

**Window and door awnings** (user, 2026-11-04, a Manila street photo: "awnings is
next, help me make these, see if you can use existing sets", "we place them in
windows and doors", "you can use a base, then put a currogated roof on it", "as a
try"). `AWN_KINDS` is `corrugated` only for this try.
- **Corrugated:** MiddleEast `SM_awning_base_01` (184 tris; wall post at local
  X 0, projecting along -X, 30 deg native, squashed to about 19) with an AsiaSlum
  `SM_MetalPlate_A_003/004` on it (364 tris), ribs down the slope, in a sheet finish,
  one per house.
- **Parked:** `panel` (AsiaSlum `SM_Roof_A_002`, 604 tris: sheet on a rusty bracket
  frame; tall edge at local Y 0, sloping down along +Y) and `plain` (the frame with
  a thin galvanised sheet).
- **Rejected:** `SM_awning_01` and `SM_awning_cloth_01`, 4.7k tris each.
- **Fit:** as wide as the opening plus 19 cm a side, reaching out `AWN_D` 90 cm, top
  at 272 cm above the tile's base (under the trim line), front edge at about 241.
  No collision. Shapes: `analysis/awning_shape_ue.py`.
- **Where:** "make the awning house wide, If a house uses awnings in one window,
  then use it for all IN THAT FACE". Three-quarters of houses have one kind
  (`P_AWN_HOUSE`); each face of those has them on all its openings or none
  (`P_AWN_FACE` 0.7). Not on doors above the street, under a balcony's roof, or
  where a neighbour, the deck or the stairs stand within reach.

**Gallery rail** (user, 2026-11-04: "The gallert rail is the wrong model too"). It
was `SM_Wooden_part_03`, a solid tapered plank. Now AsiaSlum `SM_Rail_A_001`, the
steel bar rail from the deck and stairs' own kit, 1.05 m tall (native 1.78 m is a
tall balcony's), inset 6 cm from the deck edge on the south, west and east sides.
- **Collision:** each bar and the top rail block (traced at 450 and 503, clear at
  515). Rays pass between the bars, so bullets do too. The gaps are about 16 cm,
  far under the 34 cm agent radius, so nobody walks through.
- **Fitting a mesh to a run:** when local bounds start at -2.5, shift the pivot by
  that times the scale (`RAIL_X0`, `RAIL_Z0`). `set_properties` can't change a mesh:
  remove and re-place.

**Building dressing** (user, 2026-11-04: "do downpipes and window air conditioning. and
the overhang rooms, ply patches", "door steps and vent blocks too", "There are alot of
blank face tiles so I want them to see more", "The hollow block faces can remain empty").
A pass in `gen_level.py` just before the chunks. Each kind has its own RNG, so tuning one
moves nothing placed before it. 149 of 235 blank tiles carry something; 86 stay bare on
purpose (hidden patterns). `analysis/check_dressing.py` tests the rules below that can be
measured: run it after every change to this pass.
- **Thin walls get nothing** (user: "this wall section needs no vents, its just a wall
  divider", "That bit is a thin wall, not a house"). `_thin_blocks`: 1.5 m blocks with no
  door or window (B10, B17, B19, B21h1, B21h2, B22). `THIN_RUN`: any run under 2 m, such
  as a balcony strip's end. They aren't dressing tiles at all.
- **Rooms** (11, `BackAlleys/Rooms`): `SM_Balcony_A_003` squashed to 1.2-1.5 m deep, on
  upper storeys over open ground, 1 m clear of the opposite wall, deck, stairs and end
  walls, one per house. Brown beam joists and knee struts, lowest at 268 cm. White or
  blue `MI_Balcony_A_001_*`. Open windows, no glass.
- **Room doors** (user: "put a doorr texture on the overhang balcony wall, looks like
  nothing leads to their right now"): one of the user's five plane doors on the wall
  behind, 110 x 218 cm, standing on the room's floor, which traced 33 cm up before the
  room's Z scale. Seen through the windows.
- **Downpipes** (11): stacked `SM_Rain_Pipe_01` near a face's end, only on faces with a
  metal roof's eave (`b["eaves"]`), pack dark red or galvanised. Never two on a house (user:
  "for pipes, never 2 on the same house"), and never within 70 cm of another pipe on any block
  (user: "theres also a pipe that overlaps with another pipe": two blocks' pipes at a corner).
  If one end of a face won't do, the other gets a try.
- **Pipe clearance:** `_pipe_free` looks at every block's pipes, not just this face's. A
  neighbour's pipe at a corner stands in front of this wall: an air conditioner sat across one.
  A pipe's centre is 23 cm off its wall and its pivot 7.6, so measure from the centre. The
  first version of the check measured from the pivot and passed that air conditioner.
- **Nothing on the walls the stairs run against** (user: "some of your patch placements and vent
  placements go into the stairs"). The gallery stairs stand against B11's sides. `_stair_clear`
  turns away patches, vents and air conditioners on that stretch below 520 cm, the top of the
  stairs' rails. Higher up, on the second storey, is fine.
- **Wall air conditioners** (20): MiddleEast `SM_Windows_04` (cooler in a window frame,
  with a glass plane) or the `SM_Air_Conditioning_*` box. They need no window hole. Ground
  ones have their bottom at 186-192 cm above the tile, so a 192 cm capsule walks under.
  The thin rod below the box is in the pack mesh and reads as a bracket.
- **Patches** (52 plywood sheets in 25 groups, 15 tin). User: "the patches look out of place,
  maybe if you scale them bigger". Small boards floating mid-wall read as stickers, so they're
  real sheets now: plywood up to 1.24 x 2.5 m, tin a whole `SM_MetalPlate_A_003/004` at about
  true width. On the ground they start just above the plinth (8-26 cm), upstairs at 58-78 cm,
  and all stop by 262 cm (`PATCH_TOP`).
- **Patches stop shots and play their own surface** (user, 2026-11-07: "the sheet metals and wood on the walls are not
  playing the correct impact").
  - They had no collision, so shots went through to the wall behind and played concrete or hollow block.
  - Now each has `coll` `IgnoreOnlyPawn`, `phys` Wood (plywood) or Metal (tin), and `nonav`. The engine `Plane` has a simple
    box and the plates a convex hull, and hitscan traces `ECC_Visibility` against simple collision.
  - Pawns pass, so the 1-2 cm lip of a sheet off the wall snags nobody.
  - A trace from 60 cm out stops at 60.0 on plywood (the wall is 1-1.4 further) and at the front face on tin.
  - `check_dressing` fails a patch without this. Posters pasted over plywood still burst; the shot behind them now plays wood.
- **Plywood comes in twos or more; tin stays single** (user: "if you are gonna place patches,
  place atleast 2 beside each other", "except the roof type, the wood one, yes do 2"). Two
  sheets, now and then three, same finish, lapping 2 cm, each its own height and tilt, across
  as many blank tiles in a row as it takes. Sheets shrink to fit but never under 78 cm wide; a
  stretch too short for that gets none.
- **Vent blocks** (48 tiles): 80 x 40 cm planes, 4 x 2 blocks, set high in the wall, one
  pattern per house, more on faces with no window (`P_VENT_BLANK`, `P_VENT_OPEN`). User:
  "align them if they are on the same face", "atleast the same height". A face (house and
  side, every storey) has one height and one row count, so tops and bottoms line up. A tile
  whose sheet reaches that height skips its vent rather than break the line. Under 110 cm
  takes none.
- **Door steps** (plain 7, tiled 8, double 4, none 3): concrete boxes 6-12 cm high, on
  ground and deck doors. Tiled ones add `SM_Front_A_001`.
- **Collision, by trace:** rooms' floor and solid panel stop shots; shots pass through
  their window openings. ACs stop shots 41 cm off the wall. Patches, vents, pipes and
  laundry have none: shots reach the wall behind.
- **Textures are ours:** `make_dress_textures.py` draws them with no libraries. First
  plywood was too dark and the green read as camouflage, so natural ply is now pale and the
  paint flakes only in patches.

**Laundry** (user, 2026-11-04: "start adding laundry hang, but keep it cheap if its far
away", then "keep the laundry stuff on balconies , or near reach of a window on the second
floor. or near the doors. never out across the street, if it crosses the street, then make
sure its on the second floor"). `BackAlleys/Laundry`, 104 pieces, 69 of them clothes. The
test: could somebody reach it? `DRESSING`'s old laundry stays off.
- **Balcony strips (4):** a line between two of the frame's posts, 18 cm in from them, 180-200
  cm over the floor, above the parapet and under the roof.
- **Overhanging rooms (5):** a line side to side, past mid-depth, about 190 cm over the room's
  floor, in front of the door. Seen through the windows.
- **Gallery rail (5):** draped clothes on the south rail's top bar, irregularly spaced.
- **Second-floor windows (6):** a rack under the sill (78 cm above the tile), centred on the
  window. Storey index 1 only: the user's "second floor".
- **Ground doors (5):** a rack on the bare tile next to a door, at the door's end, 255-272 cm
  up, short clothes only, so they stay above a head. These tiles are claimed before patches
  and vents run: afterwards nearly every tile beside a door was full.
- **Over the street (3 of 6 asked):** only from beside a second-floor window, at a height
  reachable from it (165-205 cm above the tile), tied to a second-floor wall opposite. Alleys
  2.5-6.5 m wide, open ground the whole way, 4.5 m between lines. Nothing crosses lower.
- **One lot to a house,** so no street of the same thing.
- **Cheap:** every piece culls at 35 m (`LAUNDRY_CULL`, the plan's `draw`, set as
  `LDMaxDrawDistance`). Clothes are `SM_clothes_A_02..05`, `B_01`, `B_03`, which have four
  LODs (2,026 tris down to 202), plus `A_01` at 395 with none. `SM_clothes_B_02` (5.8k)
  stays out, and so does `SM_Rope_A_001` (1,208 tris, no LODs): a line is two engine cubes
  meeting in a slight sag. Racks are 108 tris. All drawn at LOD 0 would be 156k tris, which
  can't happen in these alleys. The LOD switch sizes couldn't be read: the headless call
  returned an empty list.
- **Rack fit:** `SM_DryingRack_A_002` runs 271 cm along local X and 7 behind to 63 out on
  -Y: turned 180, pivot at the run's far end, 7 cm out. Clothes hang at 62 cm out.
- **No collision** on any of it.

**Street dressing** (user, 2026-11-05: "whats else can we add?", then "do all that and add it to
the tool"). A last pass in `gen_level.py`, with a switch per group (`STREET_WIRES`, `_ROOFTOPS`,
`_LIGHTS`, `_FRONTS`, `_DETAILS`), its own folder and RNG per kind. Being last, it moved none of the
4,109 pieces before it (compared piece by piece). 475 new actors. It keeps the building dressing's
rules: hollow faces and thin walls stay empty, nothing on stair walls, nothing across a pipe. Shapes:
`analysis/street_shape_ue.py`. `analysis/check_dressing.py` tests it; faults planted in the plan are
all caught.
- **Wires** (`BackAlleys/Wires`; since 2026-11-05 22 spans and 13 runs along walls, 84 wires across the
  alleys, in bundles of two to six: "power lines are a big identity show for the philippines"; up from
  11 spans, 7 runs and 23 wires. 493 pieces, each its own actor, so they are the thing to watch on the
  Deck; not traced yet): a span goes box to box
  on the bands at second-floor height, slanting across the alley. Never under 5.6 m (`WIRE_LOW`, an
  assert), so above the laundry and the gallery's headroom. Never through a house, room or end wall,
  or over a roof too low to clear. Thin `SM_Cube`s, 3-4 per span, as a parabola. Junctions are
  `SM_ElectricBox_C_002` (12 tris). `SM_Cable_B` at 5k each stays out, and so do the flat
  `SM_Cable_A` cards: untested, one-sided, and the pack's own map leaves them without a material.
- **Meters** (10, `BackAlleys/Meters`): `SM_ElectricBox_C_003` (132 tris) low on a ground tile, with a
  conduit climbing to a box on the band. It feeds a span if one can cross, else a wire along the wall,
  else it just rises to the roofline. Near a tile's end, so upstairs openings and awnings stay clear.
  The conduit clears the trim or protruding band by `_style`.
- **Tanks** (15, `BackAlleys/Tanks`): Favela's stack from its dump: stand, tub at +59.5, cap at +85.2.
  Low on the wide terraces, whose roofs are above; on four 12 cm legs on flat roofs and over metal
  ones, where the legs go through the sheets. The tub alone keeps collision. 6.5k tris at most, all
  LODded.
- **Aerials** (10, `BackAlleys/Aerials`): AsiaSlum's `SM_Antenna_A_*` need `MI_Antenna_A_001` (their
  own slot is WorldGrid), near a roof corner, leaning up to 3 degrees, all facing about one way, as at
  one transmitter. `SM_Antenna_01` in MiddleEast is a bare mast; in Favela it's a satellite dish with
  branding, left out. A taller neighbour within 1.6 m turns one away.
- **Lights are off** (user, later the same day: "I will keep this level on daylight so the lights should be off"). `STREET_LIGHTS_ON` False: the
  fittings stay, unlit, with no light actors: bulbs in the mesh's own `MI_Light_A_001_Off`; lamps and tubes in plain galvanised metal, as the pack's lamp
  material glows whatever the hour (`EmissiveMultiply` 3), and a child of it would give us a pack parent. The rest of this entry is how they work with it
  True, for a night version.
- **Lights** (`BackAlleys/Lights`): real Static lights plus their fittings, so the bake carries them
  and they cost nothing at run time. 5 bare bulbs (`SM_Light_A_002` in `MI_Light_A_001`, the "on" one;
  `_Off` is the default), 10 fluorescent tubes (Favela's pair: `SM_StreetLamp_05` + `_06` at 0.504 is
  a 120 cm tube, with `_06` at local (6.7, 11.9, 7.9)), 8 cobra lamps on wall arms (`SM_StreetLamp_02`
  at about 0.67, reaching 2 m). Warm bulb, greener tube, orange sodium. A plan item's `light` holds
  the settings; both placers read it.
- **Fronts:** 4 shutters with a blank sign, 4 gates (on a wall or in front of a door), 8 tarps (blue
  mostly, on a wall or half across a door), 5 long signs over a door or window with no shop under them
  (`WallSign_*`; were square `SM_Sign_B_005` blade signs until 2026-11-05: "square signage may fit
  chinese charachers but not alpha numberics"). Every sign is `SM_Sign_A_001`, at least 2.6 times as wide
  as it is tall (`SIGN_LONG`, checked by `check_dressing.py`). Few because few tiles were left:
  the earlier dressing has most of the ground floor. One to a face.
- **Signs are blank on purpose:** `MI_BackAlleys_Sign_*` are faded paint and rust with no lettering.
  What a sign says is design's call, so they wait for wording.
- **Sills** (57): a slab or a deeper one, in the band's material so a painted face stays one colour. A
  face has them or doesn't, one window in ten missing. Not above a drying rack.
- **Rebar** (5 stubs): a concrete stub at a roof corner with bars left for the next floor, on flat
  roofs and wide terraces, never against a taller wall.
- **Peeling paint** (20, `BackAlleys/Peel`): our decal, painted faces only. Colour and opacity come
  from one texture, drawn by `make_street_textures.py`. On a window tile, only under the sill.
- **Bake cost:** wires, rods, fittings, tanks, sills and the rest carry `vol` (`ForceVolumetric`, no
  lightmap), and thin ones `noshadow`. The last bake ran out of video memory; this adds no lightmaps
  to that.
- **Not used:** `SM_DamageWall_A` (red interior flakes), the meter banks (23k). Poles and transformers went in on 2026-11-06, below.
- **Placed and saved (2026-11-05):** 475 of 475, no failures; folder counts match the plan. Seen in
  captures: shutters, signs, gates on walls and doors, tarps, meters and conduits, wires, tanks, aerials,
  a lamp, bulbs, tubes, rebar, a peel. Not walked in PIE, not baked.

**Low wires** (user, 2026-11-05: "power lines are a big identity show for the philippines", with a photo of a
Manila alley; `STREET_LOW_WIRES`). At the three spots with the most wires overhead, shots from the ground looking
22 degrees up showed none: the spans sit at 7-8 m. So a second layer: 28 spans across the alley at the top of the
ground floor, a third of them climbing to the second floor opposite, and 10 bundles slanting down a wall, past
windows but not doors or awnings. 116 wires. Never under 3 m (`LOW_FLOOR`, an assert), and over the
gallery or its stairs only above 6.2 m (`DECK_CLEAR`; the check caught a drape on B11's gallery wall). Culled at
50 m. The Wires folder is now 969 actors: not traced on the Deck. They could be merged or instanced.

**Chained power lines** (user, 2026-11-06: "try to chain connect powerlines"; `STREET_CHAIN_WIRES`, `Chain_*`, `ChainLow_*`, `ChainBox_*`). Every span and run had ended at a box of its own: 73 separate hops. The last pass of the generator, so no other piece moved (`plan_delta.py`: 0 removed, 561 added).
- **Three stages:** link boxes that can already reach each other, shortest first; grow a chain's end towards one of the 5 nearest other chains with a new box; tie what's left into a box part way along another chain. A box takes two lines, three at a branch, and nothing closes a loop.
- **Result:** 64 links (51 across, 11 along a wall, 2 drops down a wall), 142 wires, 21 new boxes. 73 hops became 30 groups, the biggest with 18 boxes. Seen from the ground in one capture (`Saved/BackAlleys/captures/2026-11-06_chains/`), where it reads as one tangle. Not walked in PIE. The Wires folder is now 1,530 actors, so the Deck trace matters more: merging them is the next step if they cost too much.
- **What limited it:** the links stay in their layer unless a drop joins them, and few drops pass the door and awning rule. Growth rarely merges chains by itself. Most of its tries fail on open ground, on hollow-block or thin walls, or on a spot already taken. The branch stage did the most for the group count (38 to 30).
- **Check with a picture:** I drew the wires from above to judge this (bright lines for chains). My first drawing was wrong: an `SM_Cube` rod's pivot is its corner, so its line starts at the location rather than centring on it. Use `rod_ends` in `check_dressing.py`.

**Posters and ads** (user, 2026-11-05: "Added the Ads, btw, these ads are AI generated, they are currently
placeholder labeled. I might decide to use them but we will see. Now see what you can do with it"; `STREET_POSTERS`,
`BackAlleys/Posters`). 101 sheets in 32 lots, all 23 usable images; the biggest block is 15. Take them out with the switch and the folder.
- **The images aren't touched.** `/Game/Project_Bopis_Posters` stays as supplied. `M_BackAlleys_PosterPaper`
  (`create_poster_materials_ue.py`) does the wear: each copy reads its own patch of `T_BackAlleys_PosterWear`,
  from where it stands, so one image tears and fades differently on each wall. Fade 0.3: at 0.55 a poster could
  lose most of its colour. All four wear settings at 0 show the image as supplied.
- **Scale, from the user's photo** ("look at this scale, use this for the poster", "the posters are tiny atm"): a Manila wall of
  campaign posters with a man cycling past. By him, each sheet is about 61 x 91 cm, pasted edge to edge in blocks of one candidate, from
  just above the ground to over his head, with a concrete column between two blocks. `POSTER_AREA` is that sheet's area at each image's
  own shape, 1.3 times for a movie one-sheet, so 60-97 cm wide and 75-156 tall.
  - **How I got this wrong first:** 44-50 cm sheets at eye level, then "use varying sizes" read as smaller too ("I meant bigger, not
    smaller"). Check a size against a person before placing it. Bigger variations stay for movie posters and ads (1.15, 1.3); a block of
    election posters is one print run.
- **Only candidates repeat** (user: "only put together indentical posters for candidates type posters, you can put movie posters together side by
  side but not the same over and over, same goes for product ads"). Election posters: three rows up to the trim where the wall is clear (`POSTER_TALL`
  18-294), two under the vent blocks (`POSTER_LOW` 18-240), one at eye level (`POSTER_MID` 76-234), in 2-6 columns of one design, or two designs of one
  candidate in alternate columns; a centimetre of lap or miss, 7% torn off. Movie posters and ads: a single row of one to three different ones.
  They run across tile joints, on the clear stretches of a whole wall, and a long stretch takes several lots with a little wall between, as in the photo.
  Every column of a candidate's block is one height, so rows line up: at first a square image's column left gaps beside a 3:4 one. A row of different
  movie posters or ads keeps each at its own size, centred on one line: sharing a height made a tall image's sheet too narrow.
- **On closed shutters:** 9.2 cm off the wall. The shutter's face is at 8.8. They went in at 8.5, buried 0.1-0.3 cm behind the metal, so two shutters carried 8 sheets nobody could see, and
  those still threw paper (user, 2026-11-06: "one of the rollups are throwing paper even without a poster"). A poster's check can't tell a hidden sheet from a visible one, so any sheet
  placed on something else needs that thing's real face. Traced at 648 points after the move: all of them 0.4-0.5 cm in front.
  - **Moving a baked piece keeps its lightmap.** They came out in black patches, the bake from when they were buried. Switching one column to `ForceVolumetric` cleared it at once in a
    capture, which proved the cause. All 8 stay volumetric (`vol`), so they don't wait on a bake. `set_actor_transform` doesn't invalidate the old lighting here.
  - **A capture right after the editor opens shows nothing useful:** "Sky Light waiting on Meshes, Textures". Wait, or take it again.
- **Over plywood and under wires:** plywood is what posters get pasted on, so plywood patches don't stop them (`_soft_boxes`), nor do the
  wire drapes in front. 2 cm off the wall, clear of the sheets at 1-1.8. Tin stops them: its ribs stand out.
- **Brightness** (user: "the material is bright even in shade"). The images reach full white and the wall paints stop at about 0.55, so
  `M_BackAlleys_PosterPaper` has `Brightness` 0.55. In shade they now sit with the walls in captures. Part of it was likely the
  missing bake as well: look again after one.
- **On hollow-block faces too** (user, 2026-11-06: "except hollow block, which yu can put posters on"). Nothing else goes on them.
- **Too near the ends of a wall** (user: "some of your placements are too close to the edge of the face", then "Yes, apply it"). `FACE_EDGE` 40 cm
  from the ends of a run, for posters, shutters, signs, meters, tarps and gates; a corner column alone takes 20. `check_dressing.py` tests all of
  them: it caught 31 sheets before the fix, and I'd counted 22 of the others. A front that can't fit becomes the next kind or nothing; a door too
  near the end goes without a gate or tarp.
- **Planes with lightmaps,** like the patches, so a sun shadow crosses the wall and the poster together. No shadow.
- **Collision: the `PosterPaper` preset** (user, 2026-11-06: "do an overlap on the poster to throw the paper impact but retain the material and
  decal on the surface underneath"). `coll` in the plan. Everything ignores it except the `Paper` trace, which `UImpactEffectsData::SpawnImpact` runs
  at a hit. Traced at 900 points on the 300 sheets: shots reach the wall 2-2.4 cm behind, or a plywood patch at 0.4-1.4, all inside the probe (2 in, 10 out).
  At two points something else sits 16 and 43 cm in front, so a shot there hits that and throws no paper.
- **Flaws in the supplied art, left as they are; the user decides:**
  - `Puting_Araw` imported as a normal map (blue image, so the importer guessed). It can't feed the material: skipped.
  - Most have no mipmaps, and 10 of the 24 are uncompressed (`TC_EditorIcon`): they can shimmer at a distance and take
    about twice the memory. Settings only; the images wouldn't change.
  - The election posters say 2004 and Tibay Selyas says "Manila 2003". The game is set in 2002.
  - Hatinggabing Takas, Huli Ka Kuya and Sa Huling Sakay are 512 x 1024 in the PNGs themselves, and look a little tall.
    They're shown at that shape.

Learned on the way:
- **`nocoll` didn't work until 2026-11-06.** A placed `StaticMeshActor` has `bUseDefaultCollision` on, which makes the component use the mesh's own collision and
  ignore the preset set on it. The placers only set `BodyInstance.collisionProfileName`, so a `nocoll` piece read `NoCollision` but stayed `QueryAndPhysics`, and
  traces stopped on the patches. A preset takes only with `bUseDefaultCollision` off too, then a save and a level reload: the name alone changes nothing in the open
  level, and `collisionEnabled` is what tells the truth. The placers now set both. Fixed on 2,209 pieces, wires included. User: "fix them all, but keep the awnings
  solid, wires stay no collision", so the 112 awning pieces are no longer `nocoll`.
- **The surface pass of 2026-11-03 mostly did nothing.** It set `phys_material` on instances without `bOverridePhysMaterial` (see the rule above), so a piece reported its
  parent's surface: Favela's `M_Bricks_01` made terrace planks and window frames Brick, AsiaSlum's masters made metal doors and glass Concrete. Fixed for what this level
  uses (45 instances). `get_physical_material()` is the only honest check.
  - **Look at the texture before trusting a name, and use the exact path.** The pass named `MI_Window_02` and `MI_Windows_02` Glass, and they're painted steel; balconies and the stall
    front were Concrete, and they're metal. I then read the wrong pack's `T_Windows_02_BC`, a wood one with the same name, and nearly set gates to Wood.
  - **A surface for one piece:** `phys` in the plan sets `BodyInstance.physMaterialOverride`, honoured on complex-as-simple meshes too. The gallery pillars use it: they're concrete,
    and their material is shared with the street lamps.
  - **Audits must resolve the plan's `mat` keyword.** `mat: "interior"` means `MI_BackAlleys_Interior` on 61 pieces, and my first audit read the mesh's default instead. `get_referencers` caught
    that, and the ground, which is one actor outside the plan.
- **`SceneTools.save_actor` fails on World Partition actors** ("Asset does not exist"). Use `save_assets` with an empty list.
- **Don't change a material instance's parent through the bridge.** `set_properties` with `Parent`, on 23 instances in use in the open level, and the editor
  crashed within seconds: an access violation in `UnrealEditor-D3D12RHI`, in the render thread. The level had been saved just before. With the editor closed, a
  headless script does it safely (`create_poster_materials_ue.py` moves existing instances to its master).
- **A generator change ripples.** Moving one meter moved every wire after it: 1,043 pieces out and 1,035 in, for an edge rule. `plan_delta.py` compares against
  the plan last placed (`Saved/BackAlleys/plan_applied/`) and `apply_delta_ue.py` touches only what changed. Copy the plan there after each apply.
- **Look from where the player stands.** The power lines passed every count and check, and from the ground none was in
  frame. A capture from eye level at the busiest spot takes a minute.
- **Bridge texture settings:** `get_properties` reads `CompressionSettings`, `MipGenSettings`, `SRGB`; `ImportedSize` can't be
  read. The source PNG's path is in the `.uasset`, and its header gives the true size.
- **Read a light back.** `LightColor` takes lowercase `r g b a`, 0 to 1. With capitals `set_properties`
  returned True and the light stayed white; only reading it back showed that. Now fixed in both placers.
- **Brightness (Candelas, Static):** bulb 4.5, tube 6, lamp 40. The first numbers (16, 26, 70) blew a wall
  in shade out to white. These are judged in the daytime exposure and unbaked, so they'll need another
  look after a bake, and more so in any night version.
- **Signs have a flat normal** (`/Engine/EngineMaterials/DefaultNormal`). The drawn one made a board look
  hammered at this stretch. `T_BackAlleys_Sign_N` is unused now.
- **Check which level is open before placing:** `find_actors` for `PlayerStart` and read its path. It costs
  nothing, while asking about a folder the open level hasn't got stops the whole script.
- **Gate colour:** `SM_Metal_Gate_01` is the same green with tan edges every time. Two can show in one
  view; a colour mask would need a new material.
- **`MI_Light_A_001_Off` is the lights' default;** the pack's map overrides it to get them lit. Read
  `dump_Demomap_AsiaSlum.json` for a mesh's overrides before guessing: WorldGrid in a slot usually
  means the map sets it.
- **Judge new pieces after a bake.** In shade, an unbaked plane has no bounced light and
  reads far darker than the baked wall beside it.
- **AsiaSlum's materials are in `/Game/AsiaSlum/Material/`, not under `FBX/`.** A wrong
  material path doesn't stop the placer: the piece lands with its default look. Before
  placing, check every plan path against `Content/`.
- **A headless run can't replace an asset the open editor has loaded,** and the file is
  locked against deleting until the editor closes. Import under a new name and swap
  (`T_BackAlleys_Ply_*`, not `_Plywood_*`).
- **The white curled sheet in captures is the decal actor's editor icon,** not a mesh.
- **Captures at yaw 45-90 can lose whole buildings** to stale culling, again here. Change
  the view direction before believing an empty alley.

### Closed stalls and bare ground walls (2026-11-06)
User, with a screenshot from PIE: "look at the place behind the player, that need fixing, the wall if open. Try to not have any first floor
walls featureless, except hollow block, which yu can put posters on."
- **`SM_Shop_A_001` is only a counter and an open bar frame.** The block's core stands 1.5 m behind it, so it read as a hole in the wall. Each
  stall now has `SM_HouseWall_A_001` on the module's line (`<label>_Back`) and `SM_RollupDoor_A_002` down inside the frame to the counter
  (`Shutter_<label>`), in `BackAlleys/Shutters`. Frame X 0..300, Z 0..400; shutter X -283.6..270.6, Z -333..0 (`analysis/stall_shape_ue.py`).
- **Overlapping surfaces, fixed later the same day** (user: "Shop A 001, overlapping surfaces with wall"). I had written that no faces shared a plane and that `B2_S0_1_1` couldn't be seen. Both were wrong:
  - **The wall sat on the frame.** `SM_Shop_A_001`'s frame and `SM_HouseWall_A_001` both have faces at local Y 0 and -20. Each stall's `_Back` wall stood 1.3 cm further back per stall, and for the first
    stall that was 0. Now `-1.3 * (k + 1)`, always behind.
  - **Two stalls lapped.** `B2_S0_1_1` runs Y 150-450 and the next stall starts at 390, on the same plane. B6's footprint in the layout ends at 450, but the house `B6h2` ends at 390, so those 60 cm were in the
    open, with a second counter end showing. A test against layout blocks says nothing about the houses. That stall comes out of the plan at the end (`_buried_stalls`), so nothing else moved.
  - **The check couldn't see it:** `check_overlaps.py` only knew the wall tiles, bands and trims. It now also fails a stall's wall on its frame, and two stalls lapping on one plane; it caught both before the fixes.
    `analysis/stall_faces_ue.py` lists a mesh's flat faces by plane, which is how to settle what shares a plane.
- **Posters on walls that aren't wall tiles** (`_extra_wall`): B2's plain stretches and the door end walls. `_run_tiles` doesn't hold these.
- **A room claims its rectangle from the ground to 30 m,** to keep pipes and air conditioners off it. That left the wall below bare, and it hid from
  my blank-wall measure too. Posters may go under a room (`_soft_boxes`); only the struts stop them (`_room_struts`, 1.2 m down the wall from the
  floor). Other dressing still treats the rectangle as taken.
- **Stair walls stay empty:** B11's two, about 7 m each, under the stairs rule.
- **258 sheets stay** (101 before this). Asked whether to thin them, the user said "Keep them". The Deck cost is still to be traced. Then 300, below.
- **No tarps on doors** (user: "dont put a tarp on the doors"). The four door tarps are gone; the three on plain wall stay. `check_dressing.py` tests it, and it caught all four
  in the plan before the fix. Just deleting the loop reshuffled 1,800 pieces, every wire, poster and lamp after it, because the street pass shares `FRONT_RNG` and
  `_front_houses`. So the loop still makes its draws and places nothing. To take something out of a pass, keep its draws, and read the delta before placing.
- **A wall with vents still reads as bare** (user: "even this is bare, it has vents but needs something", of `B18_S0`). Vent blocks stand with their bottoms 173 to
  240 cm off the floor, but `POSTER_LOW` and `POSTER_MID` top out at 240 and 234, so posters only fitted under the highest. Two more bands, `POSTER_UNDER`
  (18-209, under one row) and `POSTER_SHORT` (60-168, under two). A sheet too tall for its band now gives way to a smaller one: a 120 cm movie poster ran 8 cm into
  a vent. `check_dressing.py` tests posters against vents; it caught that one. 300 sheets in 95 lots (240 election, 35 movie, 25 ad).
- **My measure missed this.** It tested 40-280 cm up the wall, so one vent made the whole height count as dressed, and it reported 1.6 and 2.2 m as the longest bare
  stretches when two walls of over 4 m were empty. Test 40-190 cm, eye level, where the player looks. On that: 20 stretches of 1.2 m or more, 29 m of 351 m, the
  longest 2.3 m. Most are the thin returns of 1.4 m.
- **`check_dressing.py` assumed 225 cm tiles,** so B2's AsiaSlum wall read as too short and failed three good posters. It now knows 300 and 150.
- **A black capture can mean the camera is inside a block.** I took three inside B6 and blamed exposure. `SceneTools.trace_world` up and sideways
  from the camera settles it: a hit 2 m overhead and on all sides is a room.

### Power poles, roof tyres, water meters, graffiti (2026-11-06)
User: "any other dressing?", then "do the building centric ones first" and "added 10 graffitits". Last passes of the generator, each with its own random sequence: the delta removed nothing and
added 420 pieces, then 49 more when the water meters spread out, so the level is 6,707 actors. Placed and saved, no failures, seen in captures (`Saved/BackAlleys/captures/2026-11-06_poles/`). Not walked in PIE, not baked. Check with
`check_dressing.py`, which now tests all four; shapes in `analysis/pole_shape_ue.py` and `pole_profile_ue.py`.
- **Poles** (`STREET_POLES`, `BackAlleys/Poles`): 7, from `SM_Electric_Pole_01`, `02` (transformers), `03` (plain) and `04`. The first stands in view of the player's start. They keep to a lane
  at least 3.8 m wide, 135 cm from a door, 220 cm from a gameplay point, clear of awnings, rooms, the gallery and the clear run ahead of its stairs. Up to 1.3 degrees of lean.
  - **How they stand:** with local X along the wall, +Y is out, or in if turned round. 02's transformers hang off -Y, so it's always turned, to hang them over the lane. 01 and 04 have lower arms
    reaching 48 cm both ways, so they stand 66 cm off the wall; 02 stands 42 and 03 34.
  - **Lines:** 5 pole-to-pole lines of 2 or 3 wires, crossarm to crossarm, a shortest tree. They can't cross over a roof, so 7 poles make 2 groups. 24 bundles of 2-3 wires drop from the pole to
    existing boxes on the houses, one to a box, the box facing the pole; a junction box is strapped to the pole at the first two of them. 298 more wire rods: the Wires folder is 1,828 actors.
  - **Surface:** the pack's pole material is Metal, so each pole has `phys` Concrete.
- **Tyres** (`STREET_TYRES`, `BackAlleys/Tyres`): 30 on 10 roofs, 8 of them on another tyre. All the one-storey metal roofs and a third of the rest, away from laps, tanks and aerials. No collision.
  - **Pale in the sun.** The pack's dusty brown read as plaster and its parent has no tint. `M_BackAlleys_Tyre` samples the same textures with `Brightness` 0.35, so the pack is untouched.
- **Water meters** (`STREET_WATER_METERS`, `BackAlleys/WaterMeters`): 32 in 20 lots of 1-4, on short legs, off door openings, one lot to a house. No collision.
  - **Spread** (user: "the water meter needs to be distributed more"). The first pass took tiles in a random order and stopped at 9 lots: they bunched in the east, 2.8 m apart in places, with one
    lot in the whole west half. A random order doesn't spread anything. Now each lot goes where it's furthest from the others, times a random 0.55-1.45 so it doesn't read as a grid, and never within
    `WATER_GAP` 5.5 m. Nearest neighbours are 7.6-11.3 m, and `check_dressing.py` wants all four quarters of the arena covered. To judge a spread, draw it: a text grid of blocks and lots took a few lines.
  - **Keeping the tags still:** the meters' claim stops at 45 cm, under the graffiti's lowest band. The first time, a claim up to 70 cm could reach the graffiti's stretches, and any change there would
    have reshuffled every tag. Only `WaterMeters` changed in the delta.
  - **Bright blue.** The body is `Tint 01 Color`, and the stored thumbnail (beige) is out of date, so look at the material's parameters. `MI_BackAlleys_WaterMeter` turns it to old brass.
- **Graffiti** (`STREET_GRAFFITI`, `BackAlleys/Graffiti`): 16 decals, 13 on clear walls (longest first, as they read as bare) and 3 on closed shutters with no poster. 102-185 cm square. One to a house, the
  same image not twice within 11 m. Hollow-block faces and thin walls stay off under their rules.
  - **The images aren't touched.** They're white-on-black masks, 512 square. `M_BackAlleys_SprayDecal` holds the paint and fades each copy a little from `T_BackAlleys_PosterWear`'s sun channel by where it
    stands. `MI_BackAlleys_Spray_<name>_<paint>`: 20 pairs, two paints each. Solid 1, Strength 1 and Wear 0 show the mask as supplied.
  - **Too faded at first** (user: "the warning and tag decals are to faded"). Three things stacked: the masks' ink reads only 0.75-0.95 once sampled (they're sRGB, medians 224-249), Strength was 0.92, and
    Wear 0.55 took up to half of what was left, so a word could drop to about 0.35. Now `Solid` 1.35 holds the ink at full, with its soft edges kept, Strength is 1 and Wear 0.12. Paint is stronger too:
    white 0.75 (it was capped at 0.5 like the wall paints), red 0.42, blue 0.34, black 0.008. Measure a mask before judging its wear: decode the PNG and read its values.
  - **New names, not edits.** The open editor had the first material loaded, and a headless run can't change that. `M_BackAlleys_GraffitiDecal` and its 20 `MI_BackAlleys_Graffiti_*` are unused now: delete them once the editor has closed.
  - **Orientation:** roll 90 with the decal's X into the wall reads upright and unmirrored, tested in captures, and it has to: these have words. Tags lean up to 4 degrees, warnings 1.2.
  - **The pack's own were no use:** `T_graffiti_01` is Arabic with "IRAQ", `T_Graffiti_09/10` name a Ukrainian district, and the rest are a skull, a bolt and unreadable tags.
  - **First capture looks blurred:** the texture is still streaming in. A second capture a little later is sharp.

Learned on the way:
- **`\t` in a script's path reaches Unreal as a tab.** `analysis\tyre_material_ue.py` failed to load as `analysis<tab>yre_material_ue.py`, so name a script so that nothing after a backslash makes an escape.
- **`set_material_instance_vector_parameter_value` returned False and still took.** Read the value back with `get_material_instance_vector_parameter_value` and trust that.
- **`MaterialExpressionWorldPosition` has no X or Y outputs.** Connecting by those names fails and leaves the node's input at its default: read the "couldn't connect" lines. Use `ComponentMask`s.
- **A capture can land inside a terrace** when a camera is set from the plan alone. The terrace's roof also hid where one line meets its box, which looked like a wire ending in mid-air: all 24
  bundles end within 11 cm of a box, by numbers.

### Big graffiti, the ground, bigger posters (2026-11-06)
User: "yes do grafitti on hollow blocks, actually allowed to paint them big. Do the ground pass after". Last passes of the generator, each with its own random sequence.
- **Big tags** (`Graffiti_<tile>_Big`): one crew tag on each of the 6 upper-storey hollow-block walls, 207-420 cm square, sized from the wall. The ground floors of those walls are full of posters, so a street-level one
  would need posters cleared. Tags only: a warning has no business 5 m up. A tag painted twice comes in its other colour. The masks are 512 px, so at 4 m they're soft up close, which suits spray. Block joints show through, as the decal only changes colour.
- **Surfaces** (`GROUND_SURFACES`, `BackAlleys/Ground`): the cracked asphalt stays as the old road, and looks right in sun. Over it, 132 poured bays and 6 repairs, as planes. The open ground is cut into the largest rectangles left, long ones cut again, narrow lanes nearly always poured and wide ones about half. A poured stretch has bays of 2.1-4.2 m, wide ones several strips whose joints don't line up, and a 2.5 cm joint where the road shows.
  - **Shimmer** (user: "theres a shimering overlap here when moving the camera, plane clipping I think", "theres a couple of them actually"). 19 pairs of planes overlapped. A slip in the cut across a wide stretch, `k + uniform(0.82, 1.18)` for a jitter round `k`, put cuts about a whole strip too far, so a bay ran past its stretch into the next, and wide stretches weren't really split at all. Lowering the pours made it worse: the plan rounds heights to 1 mm and they now span 3-8 mm, so many came out equal. Fixed, which also gives the strips as intended: biggest bay 16 m², was 28. `check_overlaps.py` now fails planes that overlap. I'd checked the bays' map and never tested them against each other, though "no coincident faces" is the rule.
  - **Repairs darker than the road** (user: "avoid these strips are too bright, if you are going to put something like this, then keep them darker", with a shot of two in shade). Pale strips on the road read as tape. All 6 are `AsphaltPatch` now, at tint 0.45. Its 0.72 looked dark in shade and matched the road in sun, so check a tone in both. `ConcreteOld` read lighter than the road in sun.
  - **Why planes:** no thickness, so no lip to walk over, and a lightmap of their own. `coll` `IgnoreOnlyPawn`, `phys` per piece and `nonav`: a trace stops on the plane at its height (checked: 1.5 and 0.8 cm) and reports its surface, a pawn walks on the slab below, and the nav mesh doesn't change. `objectType` still reads WorldStatic until the level reloads, as with other presets.
  - **`M_BackAlleys_GroundPour`** is mapped from world position, so a bay of any size shows one scale, with an offset per instance so pours don't line up. Five tones, `MI_BackAlleys_Ground_*`.
  - **Most road textures can't tile.** `T_road_02..06`, `T_Road_04`, `T_dirty_road_01`, `T_Dirt_01`, `T_channel_dirt_01` and the sidewalk ones are strip atlases for road meshes, with gutters and stretched bands. `T_Concrete_01`, `T_Asphalt` and `T_gravel_01` tile. There's no usable packed-dirt texture, so dirt comes from decals. The stored previews are blank: `analysis/ground_export_ue.py` and its two siblings export the textures to `Saved/LevelGen/ground_tex/` (506 MB, safe to delete).
  - **Tints can be changed live.** `ObjectTools.set_properties` with `VectorParameterValues` on an instance the level uses worked and saved, with no crash. Only `Parent` is dangerous.
  - **Unbaked planes read brighter and bluer in shade than the baked road.** Judge the tones after a bake, not before.
- **Dirt** (`GROUND_DIRT`, `BackAlleys/GroundDirt`): 141 decals. Soft grime at wall feet and doors (`MI_BackAlleys_Grime_Soft`), grit lines (`_Grit01`, `_Grit02`), run-off from downpipes and drips under air conditioners (`M_Leakage_01/02`), heaps, specks, 5 manholes.
  - **Lying on the ground:** pitch -90, scale `(depth, v/512, u/512)`, U along the yaw's direction. At a wall's run yaw, V runs out from the wall, so turn it 180 to put an image's lower edge against the wall.
  - **Alignment to the houses** (user: "They either go above to the floor lining OR they do not hit the edge at all"). Three faults, measured with a script before touching anything:
    - **Up the lining:** the box was 6.4 cm each way from z 2, so it smeared up the lining's and the steps' vertical faces. A first cut to 3 cm above the road still showed (user: "you can see where the decal goes into the house floor, the decal shoud be super thin and hit just about the surface of the road"), as the pours stood up to 2.2 cm over the road and set the height. So the pours came down, to 0.45-0.8 cm and repairs to 0.25-0.35, and the box runs from 0.6 under the road to 1.1 over it (`GD_Z` 0.25, `GD_DEPTH` 0.85/128). `check_dressing.py` fails a box over 1.2 or a pour over 0.85.
    - **Past the corner** (user: "1rst one overshoots the house"): the run-off stains were centred on their pipes and got no lining check, and a leak mask's top edge is a hard line, so one near a corner ran on past the house. `_ground_stain` fits them to the lining as the strips are, drips too, and the check covers them. Drips had a random yaw: now their hard edge lies along the wall.
    - **Short of the edge:** all 13 door decals stopped 12 cm short, as I'd offset them 8 cm for the step. Strips ran up to 40 cm past the end of their wall, with no lining behind them.
    - **Guessed masks:** I'd judged the dense edge's position from a contact sheet, and some were buried 9-12 cm under the slab, which wastes the densest part. `GD_EDGE` is measured, by averaging each mask down to 40 rows: `T_decal_08` 0.985, `T_RoadDirt_01_O` 0.775, `T_RoadDirt_02_O` 0.69. Measure a mask, don't read it off a thumbnail.
    - **A search off by 2 cm:** `_lining_foot` first tested 2 cm either side of its walker, so walking in it stopped 2 cm out, and 7 drips sat just off the lining. `check_dressing.py` caught them.
    - **Now:** `_lining_span` walks the wall and keeps the stretch with slab just inside the lining's edge and open ground just outside, from the `Floor_*` boxes themselves (`SM_Cube`, pivot at a corner), and the edge sits `GD_TUCK` 1.5 cm under it. Every sample of all 62 strips and door decals came out at 1 cm under, and the 17 stains pass the check. `check_dressing.py` fails any that isn't.
  - **`M_BackAlleys_GroundGrime`** (`create_grime_materials_ue.py`): the pack's masks run the image's full width, so a strip stopped in a hard line. This decal fades both ends along U (`EndFade` 0.14). Five instances: `Soft`, `Grit01`, `Grit02`, `Leak01`, `Leak02`.
  - **The pours cast no shadow** (`noshadow`): flat on the road, their only shadow was a hard black line along one edge. Joints still read, dark in shade, and go a little dashed at a distance. `AsphaltPatch`'s `Tile` went from 340 to 170, as its grain looked coarse beside the road's.
  - **`MI_DecalRoadDirt_05`** reads as a flat golden sticker in sun at full size, so it's 0.6 of the other heaps.
  - **Tried and dropped:** `MI_DecalRoadDirt_03` makes a hard rust line, not grime. `M_RoadDecal_01` reads as a bright pale patch on asphalt, even in shade. Square drains and mesh plates: user, "metal square grates are not common in the ph". They still draw their randoms in `_ground_decal`, so nothing moved when they came out.
- **Litter** (`GROUND_LITTER`, `BackAlleys/Litter`): 129 pieces, no collision, so nothing stops a pawn or changes a fight. Bags, rubble and sacks at wall feet away from doors, in lots at least 6 m apart; cardboard, paper and cups toward the edges of lanes; butts by doors. `SM_Garbage_bag_01` and `_green_03` look stood on end, so mostly `_02`, which lies down. `SM_Paper` is a clean white sheet, so few and small. `SM_PLASTIC_BAGS` is a hanging bag, not used. `SM_Sewer_01` is a 2.8 m pipe, not a sewer.
- **Bigger posters** (user: "The posters are generally tiny", "Ads and campaign material needs to be seen from further away", "find a way to scale the posters more"). `POSTER_SCALE` 1.8 over the photo's sheet, or as far as the stretch and band allow, and never under it. Elections stack two rows only if each is still `POSTER_TWO_ROWS` 1.5, or else one big row. 300 sheets became 143: median 134 cm tall, up to 249. Culled at 80 m, not 50. Tiny wasn't only the sheet size: at a distance a block of many small sheets reads as texture. Only the `short` band under two rows of vents stays near the old size.
- **Nothing behind a post** (user: "there is no way he was able to stick that behind the post"). `Pole_3` stood 0-90 cm off a wall with a block on it. Poles go in after posters, so the sheets come out at the very end, by `_post_in_front`: within `POST_REACH` 90 cm of the wall and across the sheet. 4 sheets. Low graffiti checks too. `check_dressing.py` tests both, working the plane's normal out from its rotation.
- **`P_POSTER_SHUTTER` down to 0.55.** With bigger sheets every shutter took posters, and the warnings that belong on shutters had nowhere to go. 2 shutters are clear now.
- **A view with open sky where houses should be is stale culling,** as noted earlier: from one spot at pitch 25 the houses are there, and at pitch 8 they're gone. No actor had moved. Check the delta before believing a capture.
- **Bash heredocs can fail on apostrophes here.** Write patch scripts with the Write tool.
- **Clear `plan_applied` before copying.** When the plan shrinks by a chunk, a stale `plan3_50.json` stays there and its old pieces override the new ones, so the delta shows changes that aren't real. `rm` the numbered chunks, then `cp`.

### Things people use (2026-11-06)
User: "we are near to getting the feel, I think its objects now. wooden bench-stools, plastic seats and tables in some areas. Buckets, potted plants on the balconies". `GROUND_PROPS`, `BackAlleys/Props`, own random sequence, last pass.
- **What's in the packs:** `Philippines_Markets/Props/MonoBloc_Chairs_01` has real monobloc chairs, stools and a two-seat bench, with colour instances (`MI_Monobloc_Chair_01` and `a`-`d`, green and blue among them). `Buckets_Set_01`, `Favela/SM_MetalBucket_01/02` (rusty, one with water). `Yakohama/SM_FlowerPots_01-10`, five shapes in two colours (`06-10` are `01-05`'s twins). `Saved/LevelGen/visual/renders` and `meshes.json` from the pack analysis gave the shapes and sizes; the stored thumbs are grey, so check colours in the level.
- **What isn't, and what stands in:** no wooden stool, and no plastic table in any pack.
  - **Bangko:** `AsiaSlum/.../SM_Table_B_001` at `(length/214, 0.28, 0.47)` is a good bench, and at `(0.25, 0.3, 0.46)` a stool. Its grain survives the squeeze.
  - **Tables:** `Philippines_Markets/Props/Table_01/SM_Table_01` at `(0.72, 0.95, 0.82)`, 123 x 74 x 74, a wooden table, not plastic. I first scaled `SM_Monobloc_Stool_02` up to `(2, 2, 1.6)` as a plastic table and thought it read well. User: "monobloc stool 02 is a chair, not a table". A stool scaled up is still a stool to anyone who knows them, so `check_dressing.py` now fails any monobloc piece scaled up. No plastic table, then: user, "Keep wooden tables".
- **A monobloc faces its local -Y:** the render's top view shows the back at +Y. `_facing(dx, dy)` gives the yaw. Back to a wall is `YAW[side] + 180`.
- **Into a wall** (user: "one of the chairs is into the wall too"). I placed furniture by its middle, and a chair turned 42 degrees swings a corner 44 cm out. A new test found 5 pieces in walls: 3 seats and 2 benches. `_prop_fits` now tests a piece's corners and edge middles against the `Floor_*` slabs and the blocks, turned as it stands, and drops what doesn't fit; `check_dressing.py` tests the same, and failed on the plan before the fix. Door chairs stand 46-60 from the lining, stools 30-46, benches 23.
- **Footprints against each other:** pots landed under tables, with plants through the top, and one table's chair stood half across a door. I'd kept lots apart by their middles. `_prop_tables` and the door centres now keep them off, and table seats within 150 of a door are dropped, so a table can be left with none; one is, with just a crate. `check_dressing.py` tests both.
- **A capture with a shadow but no object, or sky where houses should be:** stale occlusion after the camera jumps. Take the same capture twice and read the second.
- **Physical props** (user, 2026-11-07: "I want bullets to affect them, some props like the filled bucket need to be static. weld them if they are separate pieces, dont affect navigation. as you suggested, only light things").
  - **Which:** monobloc chairs, stools and the two-seat bench, and the empty buckets: 30 pieces. `PROP_KG` holds their masses. Lids are welded to their bucket (`weld_to`). Static: the filled
    `SM_MetalBucket_01`, tables, benches, wooden stools, crates, cups. Pots and trash bags were added later the same day (below).
  - **Settings, in all three placers:** Movable, `PhysicsActor`, simulate, start asleep, mass overridden, `bCanEverAffectNavigation` and `bGenerateOverlapEvents` off. Trace 24's casings cost 20-29 ms
    of nav tick by dirtying tiles as they moved, and their overlap updates too. Asleep, 30 bodies should cost close to nothing until hit; measure it on the Deck.
  - **Property names that work (read back 2026-11-07):** these go in one `ObjectTools.set_properties` on the StaticMeshComponent, and they took as written.
    - Top level: `Mobility: "Movable"`, `bGenerateOverlapEvents`, `bCanEverAffectNavigation`, `bUseDefaultCollision: false`.
    - In `BodyInstance`, lower camel case: `collisionProfileName`, `bSimulatePhysics`, `bStartAwake`, `bOverrideMass`, `massInKgOverride`, `physMaterialOverride`.
    - Read back with `ObjectTools.get_properties` and `properties: [...]`.
  - **`Mobility` goes first.** The keys are set in order. Setting `Mobility` re-picks a default profile from mobility and simulate (`FBodyInstanceEditorHelpers::EnsureConsistentMobilitySimulationSettingsOnPostEditChange`). So a lid, Movable but not simulating, went from `PhysicsActor` to `BlockAllDynamic` when `Mobility` came after `BodyInstance`. `objectType` reads WorldStatic or WorldDynamic until the level reloads, as with other presets.
  - **Welding:** call `ActorTools.set_parent_component` with `component` set to the lid's root and `parent` set to the bucket's root. It keeps the world position.
    - Nothing in the bridge welds directly. A Movable, non-simulating child with `bAutoWeld` on (the default for static meshes) is welded to a simulating parent when its body is made in a game world (`FBodyInstance::InitBody`).
    - The placers' `weld()` does this after placing. In `plan_delta.py`, a lid whose bucket changes is re-placed too, as removing a parent leaves its child detached.
    - Not yet seen in PIE.
  - **Trash bags** (user, 2026-11-07: "do the trash back with physcics as well if you are not already"): the `Lt_Bag_*` litter is physical, Cloth, 3-4 kg at scale 1, times the cube of the scale (`LT_BAG_KG`).
    - The pack's bags are `CTF_UseComplexAsSimple`, so they're placed as project copies (`SM_BackAlleys_GarbageBag_01`, `_02`, `_Green_03`) set to `CTF_UseDefault`. Each copy has one 30-34 point hull matching its bounds. The pack itself is untouched.
    - They used to lie 39-55 cm apart, and a bag is 60-95 cm wide. Now each lot's bags form one row across its clear stretch, spaced by each bag's turned width plus 1-4 cm and set clear of the lining. The random draws are unchanged, so no other litter moved.
    - 18 of 25 fit. Loose no-collision litter under a bag (4 flattened boxes) is taken out, and the bag stays.
    - **First try didn't collide** (user: "the bags dont trigger physics", "the pots and bags dont even collide").
      - Unreal never cooks a complex-as-simple mesh's hull (`UBodySetup::GetCookInfo`). Setting `CollisionTraceFlag` by property afterwards doesn't re-cook it: `PostEditChangeProperty` only reacts to `AggGeom`. So the bodies had no shapes.
      - Fixed with `StaticMeshTools.generate_convex_collisions` (1 hull, 32 points), which cooks.
      - **Check:** `SceneTools.find_actors` with `bounds` and `collision_channels` runs a physics overlap query and sees only cooked simple shapes. A chair showed up there, the bags didn't until the rebuild.
  - **Pots are physical** (user, 2026-11-07: "The pots dont get physics", "the pots and bags dont even collide").
    - Masses are in `POT_KG` by shape, times the cube of the scale; tins 4 kg.
    - Surface: `FlowerPots_01-05` are terracotta (`T_FlowerPots_02_BC`), so Clay. `06-10` are coloured plastic with a recycling mark (`T_FlowerPots_01_BC`), so Plastic. Tins are Metal. The pack's instances report Leaves, which is wrong.
    - A plant has `weld_to` its pot but no collision. It's attached, Movable, and rides the pot; it can't weld without collision.
  - **Raised physical pieces are tested too:** balcony pots against everything within 3 m.
    - Neighbours' plants don't count: no collision, and a plant's box is far wider than its leaves.
    - 10 pots touched a floor band, a pole, an awning post or another pot, and are out.
  - **Caps** (user: "the chairs go flying when you walk to them. cap their velocity"): `PHYS_CAP` (150, 720) goes into the plan as `cap`.
    - The placers set it as `bOverrideMaxDepenetrationVelocity` and `maxDepenetrationVelocity` (cm/s), and `bOverrideMaxAngularVelocity` and `maxAngularVelocity` (deg/s).
    - A body has no setting for its straight-line speed. Chaos has one, but only from C++ (`FPhysicsInterface::SetMaxLinearVelocity_AssumesLocked`).
    - **The flying is the player's push:** `UCharacterMovementComponent::ApplyImpactPhysicsForces` pushes with `PushForceFactor` 750,000 whatever the mass, about 50 m/s a frame on a 2.5 kg chair. Its velocity scaling compares an unnormalised dot product with 1, so it almost never applies.
    - The fix is `bPushForceScaledToMass` with small factors, in the player's C++ constructor. Enemies already have `bEnablePhysicsInteraction` off.
  - **Monobloc colour, picked once** (user: "the monobloc MI for chair 1 (not 1b) has code that changes his color in realtime", "there are still issus with the monobloc MI, for the other stool 02",
    then "code the material so it does not regenerate the color if moved? only generate on spawn time").
    - **The cause** is in `MM_BasicProp`: `Activate Random Color?` sends the base colour through `MF_PerInstanceColor`.
      - It computes uv = mask((`ObjectPositionWS` × 0.01 + (100, 10, 1) × `PerInstanceRandom`) ÷ `Scale Multiplier` 0.001), which is world position × 10 per cm.
      - It samples `TX_ColorVariation_BC_01`, a 4 × 4 sRGB palette. The colour is lerp(base, base × swatch, `Color Overlay Strength` 0.9), then × `Basecolor Tint`.
      - A static piece keeps one colour; a moving one flips every millimetre. 8 of the 11 monobloc instances had it on: `Chair_01`, `01d`, `03`, `03a`, and all the stools. Only `Chair_01a`–`c` are fixed.
    - **The fix** is a switch inside `MF_PerInstanceColor` (pack asset), `Colour From Spawn Seed?`, off by default, so the rest of the pack is unchanged.
      - When it's on, a scalar parameter `Spawn Seed` (Use Custom Primitive Data, index 0) picks the cell centre: u = frac(floor(16s)/4) + 0.125, v = floor(4s)/4 + 0.125.
      - The `*_SpawnColour` instances (`BackAlleys/Materials/Monobloc`, children of each mesh's base) turn it on.
      - `_mono_look` gives each piece (material, seed). Chairs use `Chair_01a`–`c` 3 times in 19. The plan's `seed` goes to `CustomPrimitiveData` `{data: [seed]}` on the component.
      - `check_dressing` fails any monobloc piece on a moving-colour instance, or on a `_SpawnColour` one with no seed.
      - A runtime-spawned piece would need its seed set in code; none are spawned yet.
    - **The bridge has no custom-primitive-data node:** it's a ScalarParameter with `bUseCustomPrimitiveData` and `PrimitiveDataIndex`. Built with `MaterialTools.add_expression`, `connect_expressions` and `recompile`.
    - **First approach, superseded the same hour:** 64 instances with each swatch baked into `Basecolor Tint` (base tint × (0.1 + 0.9 × swatch), linear) and the switch off: `Chair_01e`–`t`, `Chair_03b`–`q`, `Stool_01c`–`r`, `Stool_02a`–`p`. Deleted (user: "Delete them"); the tints can be recomputed from the swatches if they're ever wanted.
  - **`ActorTools.set_actor_transform` with only a location resets the rotation to 0**, whatever its docs say. Always pass the full transform.
  - **Captures:** the floating white "sheets" in `CaptureViewport` are DecalActor editor sprites. They show even with `bShowUI` off.
  - **Collision:** all of them already have simple collision (convex hulls, a box for `SM_Monobloc_Stool_01` and the filled bucket): `analysis/prop_collision_ue.py`. Complex-as-simple couldn't simulate.
  - **Bullets** need C++ (`AWeaponBase::FireHitscan`, `AProjectileBase::OnHit`): only blasts pushed simulating bodies (`Explosion.cpp`), and gunshots only bodies. A push of `PropPushSpeed` per shot,
    split across pellets, times the prop's mass, at the impact point so chairs spin and tip.
  - **Nothing starts touching anything** (user: "make sure whatevr is a physical object does not overlap initially to any other object, i saw a bucket overlapping pipes earilier"). A body that
    starts inside another is thrown out on the first frame. `_piece_box` takes every piece's box from the measured bounds in `Saved/LevelGen/visual/meshes.json`, turned as placed (a separating-axis
    test for flat ones), and the props pass drops any ground-level prop touching something that isn't its own pot, lid, table or stack. It found 5 physical pieces and 10 static ones: buckets into
    wall ends and floors, pots against a pole, a plant in a column, a crate against a pot. Buckets by a downpipe now stand in front of it, clear of it. `check_dressing.py` runs the same test.
- **Spacing:** a chair is 58 x 65, so four round a table went through each other. Three at most, and `check_dressing.py` fails seats nearer than 62 cm.
- **Seats near doors** (user: "use the chairs near doors"). Taking them from the walls' clear stretches left two doors with a seat: the other lots took the stretches first, and a door's own tile has no stretch beside the frame. Now they work from the doors themselves, ahead of the benches and buckets, just past the frame and clear of the step. 7 seats, from a bag so the square stool is about half. Checks use `_poster_clear`, not `_free`: an overhanging room's claim runs the whole height of its rectangle, and a seat stands fine under one. Whatever goes first eats the wall spots: raising door seats cut benches to 3, and more benches cut buckets to 1. Print the counts after any change here.
- **Furniture stops shots, not pawns:** `IgnoreOnlyPawn`, `phys` Plastic or Wood, `nonav`. Same as the pours. No fight or path changes, but you can walk through a table. Solid is the user's call: a table in a lane would be cover. Plants have no collision. Buckets and pots used to have none; since 2026-11-07 they're physical (see Physical props).
- **A clean table** (user: "the table texture is a filthy texture, create a new instance of it where its not filthy"). The colour texture is clean: a grey top and light wood legs. Two other things made it filthy:
  - `MM_BasicProp` lays near-black wear through `T_Table_01_WTT` (`Wear Strength` 0.74) and a dark brown tint. `MI_BackAlleys_Table_Clean`, a child of `MI_Table_01`, has Wear 0.06, Tint 01 0.22, Tint 02 0.12. That alone left the top marbled and dark.
  - **The top is metal.** In `T_Table_01_ORM` it's high in blue and low in green, so it mirrored the dark alley. `T_BackAlleys_Table_ORM`, one flat value, makes it matte. The pack samples its ORM as sRGB, so 220 reads as roughness 0.72. Matte, it came out near white in sun, so `Basecolor Tint` 0.42. Read an ORM's blue channel when something looks dirty and blotchy. The whole Philippine Markets pack uses this master, so any of its props can be cleaned the same way.
  - Set live through the bridge, as `TextureParameterValues` and `VectorParameterValues` lists, since the open editor had the instance loaded. Worked, saved, no crash.
- **Rice sacks** moved off the street (user: "move the ricebags to the secured balconies"): the old ones still draw their randoms in `_litter`, so no other litter moved. On terrace floors, banister terraces first as they show from the street, away from pots and posts.
- **Pots by doors** (user: "put some potted plants along the wall near doors where you can"): `Prop_DoorPot_`, walking along the wall from the door up to about 3 m, as the first spot past a frame is often a seat or a pipe. Plants stand off the wall by their reach.
- **Balconies are seen from below.** A parapet is 106 cm, so a pot on the floor behind it can't be seen from the street. So: pots on the cap's ledge (`ParapetCap` top is its z + 8, 26 cm wide, so pots at 0.66-0.76), and tall plants on the floor behind it. A wooden banister shows the floor, so pots go there. Posts stand on the ledge: keep off them. Tanks too.
- **Plants reach as far as they're wide.** From outside, below the cap, fern leaves came through the parapet, from plants on the floor 35 cm behind it. A floor plant now stands its reach back from the wall's inner face and goes without if it would still reach a wall of the terrace. `SM_Plants_01` went: too wide for a 1.5 m balcony.
- **Tris add up:** 64 pots and 45 plants at 1-2.7k each, culled at 35 m. Plants are masked. On the Deck trace list.
- **Under a downpipe, a bucket** catches the rain: half the pipes. The pipe ends in the bucket, which reads right.

### Gates, business posters, lettered boards (2026-11-07)
- **The "backwards door" was a gate.** User: "this door is backwards and not in contact with the wall", of a green steel door with a tan frame. No door mesh or
  texture is green with a frame and a middle rail: it was `SM_Metal_Gate_01` from the street pass (`Gate_*`). To find what a screenshot shows: the plan's door
  pieces first, then every actor near the spot (`find_actors` with an empty name lists them all; `RelativeLocation` from the root component), and a row of
  `trace_world` lines across it to see where its face really is.
  - Its frame and rail are on local +Y and the plain sheet on -Y (renders a and b in `Saved/LevelGen/visual/renders`). It hung frame-out, 8 cm off the wall on
    its sheet. A sheet-steel gate shows the sheet and keeps its frame inside. `_gate()` turns it 180°, puts the pivot at the far end, and sets the frame's
    edge 0.3 cm into the wall (`GATE_TOUCH`). All 4 gates. Traced after: the sheet is 3.9 cm off the wall, and the handle is on the left.
  - `check_dressing`'s face-edge test knows a turned gate runs back from its pivot.
- **Business posters:** `/Game/Project_Bopis_Local_Business_Signs/Posters`, five hand-painted 2:3 local ads, joined `POSTER_ADS` (`POSTER_LOCAL`).
  `create_poster_materials_ue.py` reads that folder too. All 28 designs are used. Adding them re-drew every poster lot (141 to 139) and moved 2 graffiti,
  which keep off posters.
  - White paper showed the wear texture's grime as blue-grey camouflage. `Dirt` is 0.3 on these five (1 on the rest), set live and in the script.
- **Lettered boards** (`SIGN_BOARDS`, `M_BackAlleys_SignBoard`, `MI_BackAlleys_SignBoard_<name>`, `create_sign_boards_ue.py`):
  - The five images are 1850 × 500, with the painted board in the middle and a plain backdrop either side. The board's columns were measured where the
    backdrop ends; it's full height. The material crops to them, 2 px in.
  - `SM_Sign_A_001`'s slot 0 is an atlas. The street-side panel (local +Y) is u 0.041-0.462, v 0.788-0.963, left to right and top down as seen from the
    street (`analysis/sign_uv_ue.py`, using `ProceduralMeshLibrary.get_section_from_static_mesh`). Outside it, the board keeps a blank sign's paint in the
    board's colour.
  - The panel is 291.4 × 78.6 of the mesh's 300 × 84, so a sign takes its board's shape. It only ever shrinks, in width or height, inside what it claimed.
    `check_dressing` fails a board stretched by over 2%, or used twice.
  - Each board once: sari-sari, xerox and carinderia over shop shutters, barber and tailor over house doors. `SIGN_RNG` (337) is their own, so nothing else
    moves. A board goes only where nothing stands 40-320 cm in front of it (awnings, rooms, tarps, ACs): the first barber's board went behind a neighbour's
    awning. 5 signs stay blank.
  - Lettered boards draw to 80 m (`CULL_FAR`), blank ones to 50 m.
  - **Flagged to the user, left as supplied:** the wall boards came in with UserInterface2D compression at 1850 × 500, so they have no mipmaps and will shimmer
    at a distance.
  - The thumbnails embedded in texture `.uasset`s show red and blue swapped. Export to PNG (`analysis/export_business_signs_ue.py`) to see real colours.

### Levels as data, and the first story level (2026-11-08)
User: "generator splits first, start a new session and try to build the map already, with what assets we currently have"; then "LevelName is 01_Slum"
(asked: `Lvl_01_Slum`, the project's prefix).
- **The split.** `gen_level.py` is now a driver; the 6,150 lines became `kit/core.py` (stateless) and `passes/*.py` (unchanged code), run in order in one
  namespace, with each level's names and switches in `levels/*.py`. Cutting a global-state script into passes that share a namespace was the safe way:
  nothing about the random sequences or the order of draws can change. A slicer asserted that every source line landed in exactly one place.
- **Proving it.** Generate from a scratch copy of `Tools/LevelGen` (its `ROOT` is two folders up from the script, so the copy writes to scratch, not to
  `Saved/BackAlleys`) and compare with `analysis/plan_identical.py`. The arena came out identical, plan and printout, after every change below.
- **Hooks with no effect on the arena:** `ZB` (a house's base, added in `put()` only when non-zero, so no `-0.0` can appear), `outside()`,
  `ground_z()`, `EDGE_RECTS`, `EXTRA_SOLID` (buildings the house passes don't build but must see), `house_base`, `ROOFS`. `cover_top` measures from the
  house's own base; `0.0 + h - 0.0` is `h` exactly, so the arena's numbers don't move.
- **The street rules on new ground found new corners.** check_overlaps failed 22 pairs on the first build, all from the arena's corner rules meeting
  shapes the arena never had:
  - **An inside corner whose "wall ahead" is a lower house in front of the next house's face on the same line.** The run went 10 cm on into that face.
    `_coplanar_ahead` meets it flush instead. Thresholds differed: one house tested "solid up to my storey top" while its neighbour, a storey taller, still
    built its face there.
  - **1.5 m strips.** The layout's mass is a raster's row runs, so blocks came with thin strips beside them, which became 1-storey "thin walls" against full
    houses. `_absorb_thin` cuts the block a strip lies along and merges its middle with the strip.
  - **Neighbours on different ground.** One base per block (`zblock`), not per house, so a row doesn't step between its houses.
  - What was left (a setback beside a neighbour's wall at the same trim height; back-to-back faces) is fixed by `story_resolve`, which shortens a trim or
    moves a band's end by what check_overlaps would fail. It honours the check's exceptions (junctions sealed by another cap, ends inside a column): the
    first version moved 20 band ends and made three new overlaps.
- **Heights: the houses' are before the floors pass lifts them 18 cm.** `cover_top` gives a house's top unlifted. My first trims compared it with the
  final heights and ran 7 cm on into a house in line. Compare with `z - FLOOR_T`.
- **Interiors are boxes in world-mapped materials** (the CHB, paint and board families), so a box wall looks like the street houses' tiles and an
  opening is cut at the layout's exact size: 2.25 m doors, 1 m doors, 3 m knock-throughs, the garage, 4 m open fronts. Every edge between two cells of a
  storey is classified (exterior, party, partition, plywood, inside wall, rail, parapet, nothing). Party walls between two buildings are built once.
  A stair's arrival edge stays open. Plywood is sheet-sized cubes (one texture per face) on studs.
- **Windows read from inside:** Favela's tiles and AsiaSlum's wall pieces are closed boxes with full inside faces (AssetGen manifest: cover 1.0 on both
  big sides), but the jalousie plane is one-sided. So entered rooms get a second plane facing in. Their openings use the Favela window's 112 x 128 hole
  at 92 cm, so `window_grille` fits the ground-floor ones unchanged.
- **The checks took a level argument** (`analysis/plan_source.py`), and two tests needed the arena taken out of them: a pour is measured from the slab
  under it, not from 0 (the story level's ground has heights), and the water meters' "all four quarters" only applies when there are meters.
- **Placing:** headless (`build_story_ue.py`), not through the bridge: a new map isn't loaded in the open editor, so a headless run may make and save it,
  and 8,500 pieces cost no bridge context. `LevelEditorSubsystem.new_level(path, False)` makes a map that isn't World Partition (as `menu_hub_ue.py` did);
  `EditorLevelUtils.create_new_streaming_level` and `make_level_current` put each section's pieces in its sublevel.
- **Headless gotchas found building it:** `EditorActorSubsystem.spawn_actor_from_object` returns None in a `-run=pythonscript` run (8,324 of 8,495
  failed the first time; lights and decals, spawned by class, were fine). Spawn `StaticMeshActor` by class and `set_static_mesh`. `delete_asset` on the
  maps returned True and left the files: the failed maps had to be removed from disk (no `__ExternalActors__`: not World Partition).
- **Seen in captures** (`Saved/LinearSlums/captures/`): the night street, the yard and garage roof, the trap house from the courtyard, the hall and
  gallery. Two faults, fixed in the generator and patched into the open map through the bridge (by label, `Saved/LinearSlums/patch_1.json`):
  - slabs and ceilings in the wall render streaked (the world-aligned CHB on a flat face, as warned above): they're the pours' `Ground_ConcreteNew`, mapped
    from above;
  - bulbs under the double-height hall hung from a ceiling that isn't there: a bulb now hangs from the first slab above it.
- **Gotcha:** a `cd` into a subfolder in a Bash call moved the session's working directory (the bridge rule says never leave the root). Use paths.

**The user's first walk-through (2026-11-08)** ("some bits are blocked. Stairs are awful and the interiors are too tall (ceilings a bit too
high). The buildings in Section 1 have 3 storey levels which is unusually high", "look at Demomap_AsiaSlum for interiors, it has a stair and
rail setup. The way you use the blocks for stair rails is absurd, remove immediately"):
- **The block balustrades came out at once** (82 pieces, through the bridge, saved) and out of the generator.
- **Stairs as `Demomap_AsiaSlum` builds them** (`dump_Demomap_AsiaSlum.json`): the kit's concrete flights, `SM_Stair_A_002` (300 run, 114.9 rise,
  307 wide, pivot at the top edge, falling along local +X, the width toward local -Y), three in line per storey: about 16.7 cm risers on 29 cm
  treads. On the open side the kit's balusters, `SM_StairRail_C_002`, at most 68 cm apart as in the demo, each scaled up to the pipe handrail,
  `SM_StairRail_A_001`. That pipe rises toward its local -X at 27.2 degrees from a low end at local (43.6, 0, 17): found by laying the demo's
  handrails against the tops of the balusters beside them. Two pipe lengths per stair, turned to the stair's slope by a small pitch, so the
  pipe stays thin (one scaled length would have been 12 cm thick). Landings and stairwell edges keep the bar rail (`SM_Rail_A_001`), as the demo.
  The wooden stair is the same kit stair for now; Favela's `SM_Stair_01` (12 steps of about 22 cm) is the other candidate.
- **The demo's floors are 4 m apart too** (floor meshes at about 85, 480, 880, 1280 cm). "A bit too high" is below the kit's own height:
  entered buildings are now 3.5 m floor to floor (3.32 m clear), the wooden storey 3.2 m, the holding house 4.3 m so the passage's 2.25 m drop
  opening still fits under its ceiling. The neighbour's roof follows the trap house's terrace (`FIXED_SH`). At 7 m the row houses are lower
  than every neighbour, so the roof builder leaves them a flat concrete roof.
- **Third storeys:** none on a house facing the main street (`no_third`), `P_THIRD` 0.2 for this level (the arena's 0.4): 29 became 12, then 1
  once the compound came in.
- **Hollow blocks on boxes** (user: "you are also using the wrong hollowblock material"): I'd put the procedural `MI_BackAlleys_CHB_Bare` on the
  box walls. The user's is `MI_BackAlleys_HollowBlocks`, mapped through the Favela tile's UV0, which stretches on a box. So
  `M_BackAlleys_HollowBlocksWorld` / `MI_BackAlleys_HollowBlocks_World` (`create_hollow_world_material_ue.py`, new assets): the same two textures,
  untouched, sampled from world position at the tile's own density (manifest: 225 cm per U, 213.3 cm per V). A box wall reads as a hollow-block tile.
- **One compound** (user: "this entire area, aside from Section 1 and 2 are all a single compound", "the slum generator is useless here besides
  those 2 sections", "keep those as houses. the compound starts where you drop from there"). A street house beside the main street or the eskinita
  stays a slum house; one bordering only sections 3-7 is `plain` (`house_plain`): no paint, every windowless face hollow blocks, doors 5% and
  windows 8% / 12% (the ground floor's barred), no balconies or third storey, no street lamps. 15 of 97 houses painted now (was 51).
  What a plain house should be beyond that wasn't answered; it's one hook to change.
- **The resolver can loop:** an 8 cm trim shortened past its overlap clamps at 1 cm and never clears, so it ran its 400 rounds on one pair. A
  trim that would end under 5 cm is now removed. And a tile's end moved out of another tile's face takes its own band and trims along (moved alone
  they were left behind, and 9 new caps came of 1).
- **Walls behind a taller neighbour:** my first test of whether an outside wall shows looked at its middle only, so a long wall half behind a house
  got trims (and windows) the whole way. `_shown` samples it every 25 cm.
- **Rebuilt** (the user closed the map): 7,729 pieces, 0 failed, night re-added. Then the user, in the rebuilt map: "I moved the stairs, fix it again
  yourself". The flights were placed from the stair's top end going uphill, not down, so the lower two sat past the top end, in every stair. The user
  had pulled the row house's two back by eye (7.7 and 3.8 m). Fixed in the generator (`+ D2`, downhill) and all 12 flights set from the plan through
  the bridge, saved; a capture shows the row house stair right. **Check a new piece's placement in a capture before the user walks it.**
- **Compound walls** (user, with two screenshots from the walk: "The yard should just be 1 storey walls around it, push these buildings back so they look like
  distant buildings", "we are inside the compound, It does not make sense to have residential houses leading into it"). Round each open area of sections 3-7
  (not the gated car lane): a wall of the user's hollow blocks, one storey (3.5 m; 4 m under the covered alley's lean-to), 20 cm inside the area's edge, with a
  concrete cap; behind it `COMPOUND_BACK` 6 m of walled-off ground (`nml` areas, at the area's height, out of reach), and the street blocks beyond that,
  the ring extended outward to keep them deep. Houses lining the eskinita keep `SLUM_KEEP` 4.5 m where the yard backs onto them, and the wall stands
  in front of their backs. Distances are square-cornered (the larger axis): round ones broke the rings into 62 strips and 129 blocks. The garage
  roof and the lean-to moved 22 cm off the walls. Off the 1.5 m grid a block can be 7.5-9 m long, where no house width fits; the split falls back
  to 4.5. The resolver's two steps now repeat until neither changes anything (moving a tile's end had made a band overlap after the overlap step).
  Rebuilt; seen in captures (`Saved/LinearSlums/captures/09_yard_walls_open.png`, `10_alley_to_bodega.png`): the wall, and a plain building's upper storey
  and roof over it, set back.
- **The user's verdict, end of 2026-11-08:** "I think this is something beyond automated generation. I have to handcraft some of these." The generated
  map is the blockout from here. **Never rebuild `Lvl_01_Slum` from the generator again unless the user says so:** `build_story_ue.py` recreates the maps
  and would wipe the handwork. Put generated additions in new sublevels.
- **Bridge gotcha:** a headless run started while the editor is closed binds port 8000 itself; an editor opened during that run starts without the
  bridge ("not reachable ... ECONNREFUSED"). `ModelContextProtocol.StartServer` in the editor console starts it.

### Sections 1-2 dressed, unaligned fronts, a real street (2026-11-09)
User: "first do passes on Sections 1 and 2. Dressings, also makes sure that each house is unaligned with the adjacent house. Also we need a curb and
actual street. Look at the net for references of PH streets"; and, of the map: "the only edit was the wall drop, your placement keeps blocking the drop so I
cant proceed and you also added a wall at the entrance of the eskinita and I can't go through".
- **References** (Pinterest thumbnails; Google Images asked for a CAPTCHA, left alone): Manila streets are concrete in poured panels with dark joints, a
  raised concrete sidewalk along the house fronts with its edge as the curb, power poles at the curb; eskinitas are concrete with a drain along one side.
- **The street** (`story_ground`): a 1.1 m sidewalk, 15 cm up, along every slum house front of the main street (into the setback gaps too); the rest
  of the street is road panels 3.6-4.6 m long with 4 cm dark joints. The eskinitas E2-E4 get a 30 cm drain channel along one side. Panel ends sit on a
  2 cm grid: off it, the plan's 1 mm rounding lapped neighbouring planes by a fraction of a millimetre (check_overlaps, *ground planes*: 17 at first).
  The sidewalk stops at the house corners where an eskinita opens off the street: nothing across a mouth.
- **The blockers:** the parapet across E1's mouth came from comparing the area's height (E1 is at 1.8 m) with the street, where E1's foot is at
  street level: parapets compare `ground_z` at the edge now. The garage roof reached over the drop: it ends at y 83.
- **Unaligned fronts** (`levels/linear_slums.py` `stagger`): every slum house face on the slum's own ground (street, eskinita, wash yard) gets a
  setback of 0, 30, 60 or 90 cm, at least `STAGGER_STEP` 30 cm off each neighbour's on that line. Found on the way:
  - 25 cm steps broke the walls pass (a 5 cm return between a slum house and a compound house's 60 cm setback came out as a run of -15 cm). 30 cm is the
    arena's smallest return and works. The compound's houses count as neighbours at their own setbacks.
  - A neighbour that doesn't move (a terrace strip, a 1-storey terrace house, a compound house, a face the stagger leaves alone) counts at its setback.
    Skipping those had left 4 of 19 pairs in line.
  - Terrace strips step back too, on their outward face only, down to 1.2 m deep (`min_depth`, a hook in the houses pass; the arena keeps 3 m). The
    faces with the fewest choices choose first, so a strip that can't move is settled before its neighbours.
  - A strip that stepped back has a side off the 1.5 m grid, and its parapet ran a cell past the corner into the next one. Terrace parapets now end where
    the face does (unchanged on the grid, so the arena is identical).
  - A face on the compound's ground keeps the houses pass's own cut, so the compound side stays as it is in the map.
  - Storey heights: a slum house's differs from its neighbours' by 20 cm or more (`stagger_heights`).
  - The generator prints `stagger: N street fronts; in line with a neighbour: 0`.
- **Dressing on a story level** (the arena's dressing passes, scoped by `story_dress_begin` / `story_dress_end` to houses `dress_house` accepts):
  arena-only assumptions that broke, now level settings: the bounds are `W0..W`, `H0..H` (the arena's are 0 to its size; the slum's footprint starts at
  x -8.5), the gallery-rail laundry needs `arena_gallery`, the poles keep clear of a provisional start, posters behind a pole come out as in
  `arena_report`. `check_dressing` takes the level's frame and bounds (it had the arena's 27/24 built in, so it called every slum pole "on a house").
  Street lights are on for this level, at the arena's values (bulb 4.5, tube 6, lamp 40): unjudged at night.
- **Putting it in the map** (`swap_sections_ue.py`, headless, editor closed; `ue_place.py` is `build_story_ue.py`'s placer, shared). A street house
  goes whole into the section it faces most, so a section swap alone would have broken the seam: 4 slum houses face the yard more than the street (section 3),
  one moved from 3 to 2 between plans (its old copy would have stayed), corner columns are numbered across the level (labels shift), and compound houses'
  roofs follow their neighbours. So it swaps sections 1-2, every slum house wherever it is, the compound houses touching one, and the garage roof; near the
  seam it matches loose pieces (columns, walls, ground) by shape and place. A dry run lists what differs at the seam but isn't swapped (here: only the
  random-draw drift of unchanged houses, roof sheets and grilles). Anything outside the `Slums/` folders in a swapped section stays.
- **Gotcha:** `RunUnreal.ps1` passes the script as a backslash path, and UE read `\r` in `...\LevelGen\replace_...` as a carriage return ("Could not
  load Python file"). Hence `swap_`.
- **Curb stones** (user, after the swap: "cap the curb edge"). First a box cap; the user: "its too sharp edged, you should be using the main border
  stone". Now Favela's `SM_MainBorder_04` (150 x 26.4 x 15.8 cm, pivot at one end of its middle line, worn, rounded edges): the curb's own height, so
  it is the curb face, not a cap. Rows of stones along every sidewalk edge on the road, 1 cm under the road to 1 cm over the sidewalk (scaled 1.076
  high), 3 cm proud of the sidewalk's face, 1 cm joints (a joint, not a butt). Along-x rows run through the corners, along-y ones stop at them. 84 stones,
  folder `Curbs`; `check_overlaps` covers them. Seen in a capture (`12_street_curb_border_stones.png`): rounded nose, chipped edges, joints showing.
- **One map** (user: "I would rather not have them as sublevels at this point if you have to add them headless everytime", "only if we can still do
  Sections 1-7 split even without sublevles"). `flatten_sections_ue.py` made every sublevel actor again in the persistent map from its data and tagged
  it `S<n>`. `EditorActorSubsystem.duplicate_actors` crashed headless (null access in UnrealEd), so the copy is by data: class, transform, label,
  folder, tags, the mesh, material overrides, body instance and render flags, light settings, decal material and size. Each copy was checked against
  its original: 9,897, 0 differences. The 14 sublevels came out of the map; their files stay as a pre-merge copy. `ue_place` tags what it places, and
  `swap_sections_ue.py` reads sections from the tags in a one-map level. The stones then went in through the bridge (84 placed, 28 box pieces out).
- **Bridge gotcha (confirmed 2026-11-09, twice):** `SceneTools.add_to_scene_from_asset` spawns into the persistent level even with a sublevel
  current (the user made `S1_Art` current both times). `SceneTools.get_current_level` names the loaded map, not the current sublevel. No toolset
  sets the current level or moves actors between levels (`list_toolsets`, `SceneTools` and `EditorAppToolset` checked). The placer's first piece
  is checked and removed if it lands wrong. Editing, deleting and capturing actors in a sublevel through the bridge work (the stair flights,
  2026-11-08). **New sublevel pieces go in headless** (`swap_sections_ue.py`, editor closed), or the user moves them from the persistent level.
  The curb stones went in with `SWAP_ONLY=Curb`: 28 placed, only S1_Art saved.
- **AsiaSlum cables, alongside the thin wires** (user: "see if the asian slum cables is usable instead of mass dropping the current small wires",
  "dont eliminate using the current ones, I just think those fit better in some instances", "go and build it"). `passes/asia_cables.py`, level
  switch `ASIA_CABLES`. Measured from the pack's FBX (ASCII, so not through Blender; `GeometricTranslation` moves the vertices 200 along X):
  `SM_Cable_B_001` / `B_003` run local X 0..401 from the pivot with level ends, the bundle's centre line 10 cm along local -Y, 45 / 18 cm of
  sag, 4 LODs (5.4k to 540 triangles); `SM_Cable_C_001` is a plate with a ring hanging 47 cm under it, the ring's axis along local X;
  `SM_Cable_D_001` is a 2 cm round cable along local X 0..200. The demo map chains bundles end to end along facades on ring brackets (106 joins).
  - **Facade runs:** rings with the plate on the wall (rolled 90), the bundle 48 cm out, under the lid and over the windows, clear of the trims.
    Neighbouring faces chain, passing up to 5 m of a face that can't take a bracket, climbing up to 90 cm. **Across the street:** a bundle from a ring
    on one house to one opposite, 3 to 9.5 m, up to 4.5 m on along the street, 9% sag. **Trunks:** a bundle pole to pole, 60 cm under the pole
    line's lowest wire end. **Drops** to a junction box on the same wall, past no window or door: none found room in sections 1-2. **Corner pieces**
    (`B_002` / `B_004`) bend about 60 degrees over a metre: no fit for a 90-degree corner at a 48 cm stand-off; not used.
  - **What limits them here:** brackets are dressing, so none on hollow-block faces (most top storeys); the top storeys are busy (lamps, rooms,
    air conditioners); facing houses are staggered. Result: 3 facade runs, 1 crossing, 3 trunks (2 kept in sections 1-2), 8 rings. Placed in the
    one map through the bridge (14 pieces, tagged S1/S2, saved); captures `13_asia_cables_crossing.png`, `14_asia_cables_facade_run.png`.
    Two editors had been open after another session's rebuild; the one left had started without the bridge (port taken) until the user ran
    `ModelContextProtocol.StartServer`. Asking the bridge for a folder that doesn't exist stops the whole script: check `get_folders` first.
  - **Found on the way:** a slanting wire's bounding box covers the whole front of the wall it leaves, so wires are tested as segments; a wire tied to
    the same wall may meet the bundle (it branches off there); the rooms' planning rectangles (a metre spare, ground to 30 m) blanked whole faces,
    so rooms are tested by their own turned boxes. Passes share one namespace: a module-level `L` in story_ground had overwritten the layout.
  - `check_dressing`: every bundle's ends on a ring's centre or at a pole, its lowest point 4.8 m up or more, none through a house (the layout's
    houses now carry their final footprint `rf` and wall `top`).
- **Fill under spot lights** (user: "rule on directional lights, always put a point light that is shadowless, like ambient light around the source,
  light never just travels in one direction", "bonus if you can have it cast shadow but very very mild"). Every spot light gets a point light 25 cm
  under its head (`street.py` `FILL_*`; the old `story_lights` pass too): 12% of its intensity, half its reach, a 40 cm source, shadows on. A
  big source makes the shadow very soft, and at that brightness it's faint. The 7 lamps in the map got theirs through the bridge.
  `check_dressing`: no spot light without a fill, and a fill counts its lamp as its fitting.
- **Main road clearance** (user: "section 1 is a main road, it needs the power cables a bit higher. Trucks should be able to pass through").
  `passes/story_road_clear.py`, level setting `ROAD_CLEAR` 500 cm over the road panels (a Philippine truck is up to about 4.3 m); the
  sidewalks and the eskinitas keep the 3 m low layer. 73 wires (27 bundles: low spans, low chain links, low pole drops) dipped to 3.0-3.5 m.
  - **Lift first:** a bundle's wall ends move up their wall (with the box) until it clears: plain wall there, below the roof, past openings,
    clear of the wall's dressing, the wire through no house. Only 1 could: most low crossings end on the 1-storey terrace strips and shacks
    along the main road, with no wall at 5 m+, and reaching past to the house behind would cross the terrace's roof frame. The other 26 came
    out with the 12 boxes only they used. Replacement spans one storey up (the street pass's own `_try_span`, several spots per wall): 1 more
    fitted; the upper walls on the road are already full of spans and dressing. Every wire over the road now clears 5 m (`check_dressing`).
  - **Found:** `story_dress_end` cut wires rod by rod by where each rod stands, so a wire leaving a pole at a section's edge lost its first rod
    (also in the map before). A wire's rods now stay or go together. `write_plan` clears every `<prefix>*` file in the plan folder: the
    report the pass writes for patching a map is `road_clear.json`. A probe that broke out of `gen_level.py`'s pass loop still wrote a
    partial plan: stop it with an exception.
  - **Into the map:** the wires folder synced by label through the bridge (288 out, 552 moved to the plan, 53 in), saved; capture
    `15_main_road_clearance.png`.
- **White lights (2026-11-09; user: "your point lights are the wrong color").** Every light placed headless (`ue_place.place_light`, so
  `build_story_ue.py` and `swap_sections_ue.py`) came out white: it set the light Static and then called `set_light_color`, a run-time call
  that a Static light ignores. Only the 7 fills, placed through the bridge, had their colour, so they glowed orange under white lamps. The
  placer now sets the `light_color` property itself (an FColor, 0-255, rounded as the bridge stores it); a headless test read back 255/158/77.
  All 90 lights in `Lvl_01_Slum` were set to their plan colours through the bridge (warm bulbs, green-white tubes, sodium lamps and fills),
  read back, saved. **Rule:** set a Static light's colour as the property, never with `set_light_color`, and read it back.
- **Faster generator (2026-11-09; user: "optimize our generator tools if we can").** The slum 25.0 s to 4.9 s, the arena 9.5 s to 2.8 s, both
  plans byte-identical (72 and 52 files, and the printouts). Found by profiling each pass (cProfile); every change is an index that hands back
  the same candidates, in the same order wherever the first match decides:
  - `story_resolve`: the band end-cap and `_sealed` tests scanned every face and cap per end (38 million comparisons): faces and caps by
    axis and 1 cm plane bins (25 s to 9 s on its own);
  - rays across the street (`street`, `low_wires`, `chain_wires`) scanned every block at each 5 cm step: `_block_at`, a 1 m grid of BLOCKS
    in their own order;
  - `cover_top`: a 1 m grid of BLOCKS made at its first call (no footprint changes after the houses pass); `_blocks_near` for the poles'
    padded lane test;
  - `_occ` (the claimed boxes) is an `_OccList`: still a list, but it grids each box as it's added, so `_free` and the posters' test look
    only nearby (10 million comparisons an arena run);
  - the poles' wire rods on a 4 m grid; the road-clearance pass works out each wire's shape once;
  - the slum's `outside` / `_ground` on a grid (rebuilt if `_FOOT` or the areas grow), the street builder's fronts on a grid, and
    `_grid_rects` scans only the box that still has cells (the empty rows and columns hold no candidate).
  - Left: `story_resolve`'s overlap step rebuilds its grid each round (about 2 s); an incremental version would have to keep the
    order it finds fixes in, so it stays as it is.
- **Even light in sections 1-2 (2026-11-09; user: "need to add more lights to Section 1 and 2, light are unevenly distributed").** The street
  pass picks its fittings at random, one to a house, so the main street had pools and gaps and section 2 had 1 lamp. `passes/story_light_fill.py`
  (`LIGHT_FILL`, after `graffiti`): open ground as 1 m cells, lit within a pool of its light's kind (`LF_REACH`: lamp 500, tube 300, bulb 260 cm,
  what the light visibly lights rather than its radius), placed greedily by dark cells gained until none gains `LF_MIN_GAIN` (6). 51% to 89%,
  8 lamps and 3 tubes; it reports what it placed and every fitting it turned down that would have lit dark ground (`light_fill.json`).
  - **Passes share one namespace:** the pass first named its reach table `FILL_REACH`, and `street.py`'s `_light` (called later for the new
    lamps) multiplied by it. Prefix a pass's settings (`LF_*`).
  - **`cover_top` measures from one base.** Asked with no house, it measured from 0, so section 2's ground (180 cm up) counted as covered and
    the pass saw only section 1. For "is a house over this point" test the footprints (`_lf_under`).
  - **Staggered fronts:** a house set back from the street stands up to 60 cm behind the area's edge, and that strip isn't layout ground, so
    `_ground_open` (60 cm out) calls it covered, and a 27 cm ramp fails a strict `<= 0`. The fill's own test (`_lf_open`) takes the strip and
    40 cm of ground step. Other dressing on those fronts still uses `_ground_open`.
  - **A lamp arm crosses a lower roof:** second storeys over a one-storey front room failed "open ground" at 60 cm. The arm needs nothing within a
    metre of its height (`_lf_below`); only the head and the ground past it must be open.
  - **Light through walls:** pools and the lamp spacing both count only what's in sight (a 40 cm line test against the footprints), or a lamp
    on a house's far face reads as lighting the yard behind it.
  - **The arena identity check runs from the project root:** `python <scratch>/Tools/LevelGen/gen_level.py`, not from inside the scratch
    folder. `props` (`_piece_box`) reads `Saved/LevelGen/visual/meshes.json` relative to the working folder and quietly does without it;
    then 32 more props and litter pieces fit and the plans differ for no reason in the code.
- **Section 4's fitted baseline (2026-11-09; user: "the doorways are two doors wide, I need it only 1 door wide except for the broken down
  wall", "I also need sils or door frames ... we should be using what assets we have instead", "conform to that when making stairs").**
  `story_interiors`, for the buildings in the level's `FITTED` (`("ROW",)`); every other building's plan is unchanged.
  - **Doors:** the layout's 2.25 m `door`/`door1` openings become a 1.10 x 2.18 m hole, the size of Favela's `SM_Door_Jamb_01` (110 x 218,
    18 deep, centred pivot, local X along the wall), placed near one end, the middle or the other end by its coordinates (`_door_span`).
    The jamb is scaled to the wall's depth plus 1 cm a side. `knock` openings stay wide. Each door's slot (centre on the floor, yaw with
    local X along the wall, width, wall depth) goes to `Saved/LinearSlums/doors.json` for the swinging doors.
  - **Windows:** Favela's `SM_windows_01` (110 x 133: frame, mullions, a dark sill on local -Y, a wooden board on +Y; renders `_a` from
    -X -Y, `_t` top with +X up) fits the window hole (112 x 128) at 1.018 x 0.992, centred in the wall, turned `YAW[side] + 180` so -Y faces
    out, set 13 cm in from the outer face so its sill stands 1 cm proud (the board 9 cm into the room); the ground floor's grille moves
    out 1.5 cm. Windows keep their places from the layout's original openings (`ops_layout`): the first try placed them from the
    narrowed doors, and one moved 28 cm off the security cage the user had hung on it. The jalousie planes stay, one facing out and one in
    (the inside twin was already there and is in the map: 9 windows, 9 inside planes, read back through the bridge).
  - **Not used:** Yakohama's `SM_Jalousie_*` (a vertical slat curtain, 2.77 m tall, not louvres); `SM_WindowSill_01` (a 4 mm strip).
  - **Stairs:** the user rebuilt `TRAP_Stair3` in the map: the top flight where the generator put it, then the kit's flights at
    0.538 x 1.015 (27 cm treads, 19.4 cm risers, 36 degrees instead of 30), four instead of three, each about one step (of six) down the
    one above, the lowest sunk into the floor, the posts re-spaced down the steeper line. Fitted stairs do exactly that
    (`FLIGHT_RUN/RISE/STEP`): flights from the top end, 5/6 of a flight apart, as many as reach the floor; the posts and pipe run from
    where the steps meet the floor. The row house's stair now lands 1.4 m short of the stairwell's foot (floor there).
  - **Into the map (2026-11-09, user: "Swap them in"):** through the bridge, by label, against the old plan: each row-house piece
    the generator moves is checked first, and one that no longer matches the old plan is the user's and is skipped (4: the ground
    floor's grilles, which the user had swapped for AsiaSlum's `SM_SecurityWinodw_A_001`, 1.1 to 15 cm off the wall). 2 removed,
    16 added, 65 moved; then 19 more moved for the window fix above. Saved; the plan's pieces read back.
  - **Knocked-through walls (user: "do we have rubble we can use on the broken through wall?", "around the door frame i mean", "Yes, dress
    them"):** no pack has a broken-edge wall mesh. Favela's `SM_BrickWallCorner_01` is a translucent mesh decal (`M_Corner_decal_01`) for a
    building's outside corner, plaster broken back to the brick: apex at its origin, the wall it wraps in its -X -Y quarter, legs 161 cm
    along -X and 194 along -Y, 491 up. `_knocks` puts one down each side of the hole and one along its top, on both faces (`put_axes`
    with +X/+Y as the two faces' normals, swapped so +Z is up), 70 cm along the wall (45 over the top), half the wall's depth into the
    hole, 1 cm off both faces. AsiaSlum's `SM_Debris_A_001-003` heaps (about 1.5 m, pivot near the middle, 10 cm of each below its
    pivot) at 0.5-0.7 scale, one each side, 3 cm clear of the wall, the Concrete surface. Checked by working out each decal's legs in
    layout metres from its rotation (UE's rotation-matrix rows) before placing. AsiaSlum's `SM_DamageWall_A_*` are peeling paint flaps,
    not rubble.
  - **White, not red (user: "make it white not red"):** `M_Corner_decal_01` is a DBuffer decal material with four texture parameters
    (`BC`, `N`, `ORM`, `MSK`; read with `MaterialInstanceTools.list_parameters`). `MI_BackAlleys_CornerDecal_White` swaps `BC` for
    Favela's `T_Wall_white_01_BC`; the brick relief and the broken-edge mask stay. Made and applied through the bridge.
  - **The top corners (user: "there a way to fix the top corners?"):** the side strips stopped at the hole's top and the top strip
    spanned only the hole, so the squares over the side strips were bare plaster, three loose strips. The top strip now runs on past
    each side as far as the side strips' plaster shows (`KNOCK_SHOWN`, 0.6 of their 70 cm: the decal's mask fades out before its leg
    ends; the full 70 cm stood out like a lintel), its soffit leg there inside the wall. Both clamp to the wall's ends (`ta`, `tb`).
  - **Inside walls showed outside (user: "the inside walls in the 3rd screen penetrates to the outside yard"):** an inside wall ran to the
    building's edge line, through the outside wall to its outer face, so its end and paint skins showed there as coloured strips (26
    pieces on the row houses alone). `_inner_ends` stops it at the outside wall's inner face (`WALL_T`; a ground-floor party wall's,
    `WALL_T / 2`). Every building had it; fixed in the map for all of them (user: "Yes, apply them"): the row houses, then the plywood
    rooms, the holding house and the trap house (26 out, 180 moved, 1 in; a shorter plywood wall takes fewer sheets, so its sheets and
    studs renumber). None differed from the old plan. The plan's one known duplicate pair (`TRAP_F2_X30p00_139p50_Parapet_0`/`_Cap`)
    shows as duplicates in every sync by label: leave it.
  - **"The walls below are pushing through the cieling":** not the walls below. Upstairs an inside wall starts 1 cm under the floor
    (`lv0 - 1`), and a hole at floor level (a door or a knocked-through wall) cut it only from `lv0`, leaving a 1 cm sliver whose top
    shared the floor finish's plane (`lv0`), flickering through it as a striped band. Floor-level holes in inside walls now cut down to
    the wall's foot. (18 in the level: the row houses 8, the trap house 10.)
  - **The recess in the stairwell (user: "theres a gap on the 2nd floor flooring", "not the sairwell", "the issue is that caved in bit on
    the wall", "the cubes you are using has messed up UVs on one side"):** an upper slab is cut round a void (a stairwell, the floor hole)
    at the line of the wall under it, the wall below stops at the slab's underside and the one above starts at its top, so along a void
    the void-side half of the wall was missing for the slab's 17 cm: a recess, and in it the slab's edge, whose material is mapped from
    above and streaked on a vertical face (the cube's UVs were fine). An inside wall under a void edge now rises to the wall above's
    foot (`_void_edges`), and every void's slab edge gets a 1 cm facing in the wall render (`CONC`, world-aligned for walls) up to the
    floor's plane (`_SlabEdge*`; hidden inside the wall where one stands). Row houses and trap house: 11 walls raised, 20 facings.
    Not the stairwell's length: a first guess cut the well to the steep stair's headroom; the user meant the wall, and it wasn't applied.
  - **The jamb blocked the doorway (user: "I cant get thru the single doorway", "it blocks bullets too"):** `SM_Door_Jamb_01`'s simple
    collision was one box over its whole 110 x 18 x 218 cm, opening and all. The mesh now collides with its own triangles
    (`CollisionTraceFlag` `CTF_UseComplexAsSimple` on its BodySetup, saved): only the posts and the head block. Check a frame-like
    pack mesh's collision (`BodySetup` > `AggGeom`) before using it around an opening.
  - **Swinging doors (user: "Apply and build"):** `BP_SwingDoor` (`ASwingDoor`, leaf Favela `SM_Door_01`) in each of the 6 jambs,
    placed through the bridge from `Saved/LinearSlums/doors_place.json` (label `..._SwingDoor0`, `Slums/Interiors`, tag S4). The
    jambs were measured in the map with `trace_world` from each door's centre: 105.8 cm clear across, 215.7 cm to the head, all six
    alike (the 110 x 218 hole less the jamb's posts and head). Leaf 103.8 x 213.7, 1 cm off the floor. `SM_Door_01`'s handle is on
    its +X edge (the `_t` render: +X up); a door hinged on the -X side keeps it on the free edge, so a door meant to hinge on the right
    is placed turned 180 degrees and hinged left. Its Y bounds (19.4 cm) are the handle; the slab is about 5 cm (traced). The sizes
    went in with `ObjectTools.set_properties`, then the actor was set to its own transform (`set_actor_transform`) so the
    construction script ran again; the leaf's scale read back right (0.974 x 0.982).
  - **Door meshes for the variants (user: "make one for every door type we have"):** 14 children of `BP_SwingDoor` in
    `Blueprints/SwingDoors/`, only the leaf mesh changed. The `_t` renders show the handle's edge: on +X for Favela `SM_Door_01`
    (all three colours) and Yakohama `SM_Door_02`; none on Favela `SM_Metal_Door_01` and Yakohama `SM_Door_01`; on -X (the hinge
    side as things stand) for Yakohama `SM_GlassDoor_02` and all eight AsiaSlum `SM_HouseDoor_*`. MiddleEast `SM_Door_02` and
    `SM_Door_color_03` are modelled along Y (10.4 x 119.3). AsiaSlum is built bigger than the Megapack (its door-wall pieces are 3 x 4
    m): `A_001`/`A_003` are 151 cm wide and `B_001` 168, so in a 104 cm leaf they squash to about 0.65 across (against about 0.9 up);
    `A_005` (a barred gate, 163 x 330) shrinks evenly. Not doors to swing: Yakohama `SM_Door_03` (41 cm, a cupboard panel), the
    `WallDoor`/`DoorFrame`/`Doorway` wall pieces, MiddleEast's hinges, door parts and window shutter, AsiaSlum's roll-up doors.
    `LeafQuarterTurns` 2 on the nine with the handle on -X. Checked with test doors spawned 50 m up over the arena (sky behind, no
    geometry in the way), captured, then removed: handles on the free edge (`26_swingdoor_variants.png`; a camera looking +Y has -X
    on the image's right). The `_b` render (from +X +Y) shows MiddleEast `SM_Door_02`'s hinge plates on +Y, handle on -Y (1 turn
    would fit it); the user dropped the MiddleEast variants.
  - **Door sounds (stand-ins):** cues in `/Game/Audio/Doors/` (copies, `AssetTools.duplicate`), each given `ATT_Footstep`: a pack
    cue with no attenuation (`Bump_Cue`) plays at full volume everywhere through `PlaySoundAtLocation`. Set on `BP_SwingDoor`'s
    defaults, they reached only the children whose defaults hadn't been edited: the nine with `LeafQuarterTurns` set through the
    bridge kept None until set directly. After changing a parent Blueprint's defaults, read every child back.
  - **Placed doors kept no sound (user: "no sounds on the door"):** the 6 doors in `Lvl_01_Slum`, placed before the sounds
    existed, still read None after the map was reloaded, though `BP_SwingDoor`'s defaults (and a door spawned fresh) had them.
    Placed instances don't reliably take a default added later: set the same values on them (equal to the default, so they
    follow it again) and read the placed actors back, not just the Blueprint.
  - **Shots from inside a row-house window played wood (2026-11-09; user: "when i shoot the window, i hear wood, the seal colider is
    infront of the jaoloise window", "its when im shooting from inside the building").** Three things together: `SM_windows_01` has a
    second slot, `MI_T_WindowGlass_01` (additive glass panes across the opening, 4 of them, lower ones 1-2 cm inside its origin), and it
    collided as its own triangles (`CTF_UseComplexAsSimple`), so the panes stopped shots, with the frame's Wood surface. The inside
    jalousie plane had no collision. And the engine `Plane` collides as one 100 x 100 x 0 box: `trace_world` never hits a plane from
    behind (the outside plane, seen from inside), and a zero-thickness box isn't something to trust a weapon trace to.
    - The frame now collides as 8 boxes round its wood (outside sill, inside board, posts, bottom rail, head, mullion, transom; from its
      loose parts measured in Blender), `CTF_UseSimpleAsComplex`, saved. Its glass panes don't collide. `ObjectTools.set_properties`
      won't resize `AggGeom.boxElems` and change elements in one call: change the existing ones, then append.
    - Each fitted window gets `_WinGlass`: a hidden `SM_Cube` (pivot at a corner, convex collision) filling the gap between the two
      jalousie planes, 0.5 cm in from each, BlockAll, Glass. Traced in the map on all 9: from inside, lower pane, upper pane and mullion
      all stop 0.5 cm behind the inside plane; from outside, at the outside plane. In `story_interiors` `_window` too (compiles; not run:
      the layout JSON changed 2026-11-08 and the story passes don't read it yet). The map's 9 are turned to the wall (yaw 0/90/180,
      scale 1.10 x gap x 1.33); the plan's are axis-aligned boxes: the same space, a different transform.
    - Other buildings' windows (no frame) still have the inside plane without collision and only the outside plane's zero box.
  - **Baking `Lvl_01_Slum` (2026-11-09, GPU Lightmass):** a bake whose log shows "Cached ray tracing scene is invalidated due to
    material changes" before "Volumetric lightmap NumTotalBricks" gets 0 bricks: nothing lights a moving character from the static
    lamps. A material that only gains a usage flag at bake time causes it; save the flag (`M_BackAlleys_HollowBlocksWorld`,
    static lighting). A sky light with Real Time Capture is skipped by the bake ("empty cubemap"). The bake has crashed the editor on
    memory (RAM full, then video memory over budget): one editor only, Lightmap Tile Pool Size 30, and the lightmaps are 2 GB.
  - **Reading what the user changed:** `find_actors` by name (`Stair`, `Step`) and the meshes' transforms through one bridge script,
    against the plan. A flight the plan doesn't have (`TRAP_Stair3_3`) and scales that differ show the edit.
- **Street lamps in balconies (2026-11-09; user: "Street lights are in someones balcony, that cannot happen ... remove them all and
  reevaluate placement").** The light fill had let a wall lamp's arm cross a lower roof (`_lf_below`), and on this street the lower roofs
  in front of second storeys are the balcony and terrace blocks (`M28h5b`, `M40h3b`...): five lamps hung inside covered balconies. The
  user had moved four by hand. Now a wall lamp needs open ground from 30 cm out to past its head (the street pass's rule; its own lamps
  were all fine), and lamps also go on the power poles (`PoleLamp`: 6.2 m up, under the cross-arms, the arm toward the side with the
  longest open run, `LF_POLE_BONUS` 1.5 in the ranking). `check_dressing`: no street lamp with a house, balcony or terrace footprint
  under it, from its fitting to its light (it flags exactly the five old ones). In the map every lamp and fill piece was taken out and
  the new set placed (51 pieces: 3 wall lamps, 2 pole lamps, 5 tubes from the fill, the street pass's 7). Lit share 83% (the 89% counted
  the balcony lamps). Capture `21_pole_lamp.png`.
- **Ground and objects in sections 1-2 (2026-11-09; user: "For S1 and S2, Do a ground and object pass (garbage cans, buckets etc)").** The arena's
  `dirt`, `litter` and `props` passes, run on the slum after `story_light_fill` (so the lights don't move). They had read the arena's `ground` pass
  (`_ground_rects`, `_ground_bays`, `DR_GROUND`) and stood everything on ground at 0. `passes/story_ground_dress.py` gives them the slum's: the open
  areas of the dressed sections less the step flight, and two hooks read from the slum's ground pieces on a 1 m grid. `STORY_GROUND_TOP` is the
  surface to set things on (pours, bodies, steps, house floors, curb stones), used by `_ground_top`. `STORY_GROUND_BASE` is the slab a decal sits
  against (a pour 0.6 cm under its plane, no curbs), used by `_ground_decal`. `dirt.py` and `props.py` use them only when they're set, and props
  measures "near the ground" and "up off the street" from the ground under a piece when they are. The arena: identical, plan and printout.
  - **Garbage drums:** the market pack's `SM_Barrel_01/02` (plastic drums, the barangay street bin; Yakohama's `SM_TrashBox_02` is a hooded
    public bin and doesn't fit). `PROP_DRUMS` (the slum 6, the arena none), their own random stream: at the foot of a wall, nearest the trash-bag
    lots first but 50 cm clear of every bag, clear of doors, pipes, posters and stairs; static, with the furniture's collision.
  - **Found on the slum's street:** a door pot walking along its wall from one door stopped in front of the next (props keep 105 cm from a
    door's centre; the check tests the opening's whole width): `_in_doorway` is the check's own test. Bags across a curb went 1 cm into it (the
    curb stands over the sidewalk): curbs count as a surface. `check_dressing` measures ground decals from the slab under them (story levels).
  - **Drums were dropped:** 6 of the first 8 touched something in the props pass's overlap test, which boxes a piece by its square bounds:
    turned at random, a drum's corners swung into the house's lining; others stood at a curb's end or under a grille. Drums now turn square to
    the wall, need flat ground (the same height at centre and corners) and a plain wall: 6 of 9 kept.
  - **Bridge saves fail while PIE starts** ("Asset does not exist: /Game/ThirdPerson/Lvl_01_Slum"), and a script that dies on its save loses
    its report: check what landed before retrying. `get_actors_in_folder` refused a folder `get_folders` had just listed; find by label prefix.
  - **Drums solid (user: "drums have no collisions"):** they had the furniture's `IgnoreOnlyPawn` (a pawn walks through, a shot stops); the
    mesh has its convex hull. Now `BlockAll` and on the nav mesh, in the plan and the map.
  - **"The plastic chairs have glass physics materials":** not found in the data. Every monobloc piece in the map carries the Plastic override
    (SurfaceType18), the pack's materials are Plastic, the meshes have none of their own, the weapon trace is simple (so the override is what
    a shot reads), and `DA_ImpactEffects` maps Plastic to NS_ImpactPlastic, plastic hole decals and the Metal_light clinks (no plastic sounds
    in the pack). Asked the user what they saw.
  - **E3's yard wall (user: "in the eskenita, extend the hollow block wall all the way", "put a cap on it too"):** story_ground's yard wall
    (hollow blocks where an area's ground drops 1 m or more to the next) covered only the 3 m of E3's north edge over the yard; along the rest
    a 60 cm slot drops past the yard's houses. `PARAPET_FULL` (level setting, ("E3",)): the wall runs the area's whole edge (drops still cut it;
    E4's drop into the yard stays open) and gets a cap like the compound walls' (6 cm, 3 cm proud), in two layers: a 5 cm body in the wall
    render and a 1 cm top in the pours' concrete. In one piece of the pours' concrete (the compound walls' caps), its sides streak like the
    slab edges did. In the map, saved; capture `24_e3_wall.png`. The compound walls' caps then got the same two layers (user: "Yes, fix them";
    `_CapBody` under each `_Cap`, 10 walls in sections 3-7).
  - **Plastic's impact sound (user: "make the soud for plastic woodlight"):** `DA_ImpactEffects` SurfaceType18 (Plastic) played the
    Metal_light clinks, as the pack has no plastic set; now the Wood_Light_Impact cues (`Wood_hit_Light_1..8_Cue`). The user had heard the
    monobloc chairs as glass.
  - 268 pieces: 109 dirt decals, 75 litter (12 physical bags), 84 props (8 drums, buckets, chairs, tables, pots on balconies and by doors,
    rice sacks on balconies). Props that would start touching something are still dropped (49 here, 28 in the arena).
- **Report gotcha:** `swap_sections_ue.py` compares rotations as pitch/yaw/roll, and Unreal re-expresses a piece stood on end (pitch 90: water
  meter legs, meter conduits), so those show as "differ" right after being placed. Compare quaternions if the seam report starts to matter for them.

### Not decided (the user's call)
- **Wall material: hollow blocks only on faces with no door or window
  (2026-11-03).** The user's rules, latest first:
  > "only use them on walls with no windows or doors. They are not to be used
  > for whole houses, so rescind rules regarding not mixing"
  > "the only mixing rule is not to mix on the same face"

  Earlier: "half and half", "use the hollow blocks 25% of the time only", "it
  should never be beside concrete", and "Yes, neighbours can differ".
  - **Rule:** a face is one side of a house, all its storeys, with its balcony
    strip's same side. If nothing on it is a door or window, it's hollow blocks
    `P_HOLLOW` (0.30) of the time. Everything else is
    `MI_BackAlleys_CHB_Concrete`. A face never mixes; neighbours may differ.
    Door end walls have doors, so they're concrete.
  - **Concrete stays:** bands, parapets and corner columns.
  - **Share:** user: "make it 30% of windowless faces, following the rules
    still". Seed 107 gives 16 of the 52 windowless faces (112 faces in all),
    46 of 481 house wall tiles. All 52 would be 153 tiles.
    `P_HOLLOW` applies to the windowless faces only; raise it for more.
  - **Superseded:** the per-face-and-storey mixes (50/50, then 25%) and the
    per-house rule of the same day.
  - **The material:** `MI_BackAlleys_HollowBlocks` is the user's GPT
    hollow-block texture and normal map on the Favela tiles' UV0, like their
    red brick. It is GPT's original, unedited. AssetGen first repaired joints
    it thought were missing; the user said "I dont want that" and "Use GPT's
    original". Don't touch up the user's textures. It
    is not world-aligned, so it stretches with tile X scale (0.89–1.33). It
    isn't the old unused `MI_BackAlleys_HollowBlock` (singular).
  - **Code:** a pass just before the chunks groups the Blocks items by house
    and side from their labels, finds the faces made only of `PLAIN_WALL`
    pieces, and sets the chosen ones' tiles. It has its own `WALL_MIX_RNG`,
    and the old picks still run, so `rnd` stays in step and windows and doors
    don't move. Every slot is overridden.
  - **Parent and physics (2026-11-04):** user: "i hear the sound of glass
    when shooting the wall"; "you made a jalouise material and decided to
    parent the hollowblocks from that, it should have been the other way
    around". `M_BackAlleys_HollowBlocks` (Concrete) is now the master, and
    `MI_BackAlleys_HollowBlocks`, `MI_BackAlleys_JalousieDouble` (overrides
    to Glass, roughness 0.35) and the five door MIs are its children.
    `M_BackAlleys_Jalousie` is unused.
  - **Rule: `phys_material` on a material instance does nothing without
    `bOverridePhysMaterial`.** `UMaterialInstance::GetPhysicalMaterial` uses
    the parent's otherwise, and the MI's file still lists the material, so
    grepping for it proves nothing; grep for the flag too. In Python:
    `override_phys_material`. Glass should never be a base others inherit.
- **Storey height:** Favela is 3 m; our layout is 4 m (the deck at +4 m,
  3.6 m clear under).
- **Kit:** Favela walls or AsiaSlum walls. Options are in the 2026-11-03
  ProgressLog entry.
