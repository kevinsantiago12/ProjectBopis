# Level generation: lessons

What works and what doesn't for generated levels, so the generator keeps getting
better across sessions. **Read this before every build.**

- **Rules** that can be checked go into the code too, as a constant or an assert in
  `gen_level.py`. This file says why.
- **Taste** goes here only.
- The user's verdicts are quoted and dated. Patterns learned from reference maps
  say which map they came from.

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

**Fit with `Lvl_BackAlleys`:**
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
