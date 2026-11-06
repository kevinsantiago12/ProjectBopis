# Visual catalogue: the art packs' meshes

From the visual pass of 2026-11-03. The user asked for "the models themselves via editor or
blender, not just metadata". All 1,098 static meshes in Megapack (Favela, MiddleEast, Yakohama),
AsiaSlum and Philippines_Markets were rendered in Blender from three angles. Each mesh was
reviewed on a contact sheet next to its editor thumbnail.

- **Sheets:** `Saved/LevelGen/visual/sheets/<group>_NN.png`. Each mesh is a 2×2 block:
  thumbnail, isometric from UE −X−Y, isometric from UE +X+Y, top view (UE +X up). Under it are
  the size in metres (UE X × Y × Z) and the triangle count.
- **Regenerate:**
  1. `analysis/export_meshes_ue.py` (headless).
  2. `analysis/render_meshes_blender.py`.
  3. `analysis/extract_thumbs.py`.
  4. `analysis/make_mesh_sheets.ps1`.

  The FBX and texture exports (2.2 GB) were deleted afterwards, because the disk is nearly full.
- **Exact numbers** (pivot, collision, openings) come from `Tools/AssetGen/manifest/`, not from
  here.
- **Fit:**
  - **use** means it suits a 2002 Philippine back alley;
  - **maybe** means it needs a material swap or care;
  - **no** means it's wrong for the setting, or impractical (very high tris).
- **Rule reminder:** the level is building blockouts only (Claude-Rules §8). Props here are for
  later, when the user asks for dressing.
- **Rendering note:** one-sided cards (posters, cables, decals) render blank from behind. That's
  expected.

## AsiaSlum (274)

**Prefab merges: no.**
- `Prefab_Merge_DecoHouseA/B`: 6.5 × 6.8 × 6.2 m gabled huts, 16–19k tris.
- `Prefab_Merge_TypeA/B/C`: Chinese-style 6–12-storey tenement blocks, 0.33–0.84M tris.
- `*_Satir_*`: their fire-escape stair stacks, 0.2–0.3M tris.

They're far too heavy, and the wrong building type for the alleys. At most they could be a
distant skyline backdrop, at LOD.

**Air conditioners: maybe, later dressing.**
- `SM_AirConditioner_A_001`: an outdoor unit, 1.25 × 0.45 × 0.82 m, 13k tris. That's heavy for
  a prop.
- `SM_AirConditionerFan_A_001`: its fan.
- `SM_AirConditionerFrame_A_001`: a wall bracket cage, 608 tris.

Window-type units are what you'd see in 2002 PH. This split unit is plausible on newer houses.

**Antennas: use, later dressing.** `SM_Antenna_A_001/002/003` are rooftop TV antennas on masts,
2–3 m, 5–11k tris. They're very PH 2002, but the triangle counts are heavy.

**Balconies: use for the building, maybe.**
- **`SM_Balcony_A_001/002/003`:** 3.3 × 2.4 m wooden balcony boxes, 1.2–1.9k tris.
  - `A_001` is a caged box with a roof.
  - `A_002` is an open railing (1.75 m).
  - `A_003` is a half-enclosed box with windows.
- **`SM_Balcony_B_001..009`:** 6.4 × 2.4 × 4.0 m enclosed balconies with a roof. Some have
  grille fronts and some window fronts. `B_002` and `B_009` are open rails, about 1.9 m tall.
  - **Triangle counts vary a lot:** `B_003` and `B_008` are 177k (too heavy), `B_007` is 24k,
    `B_005` is 8.8k, and `B_001/002/004/006/009` are 1.5–2.5k.
  - **Fit:** these are AsiaSlum's add-on "cages" on upper storeys. They could fit the
    stepped-back balconies, with the light versions only.

**Balcony windows: maybe.** `SM_BalconyWindow_A_001` is a tall 0.7 × 1.6 m glazed window, 168
tris. `A_002` is an empty 1.5 × 1.6 m frame, 50 tris.

**Base floors: use for the building.** `SM_BaseFloor_A_001/002` and `SM_BaseFloorCorner_A_001`
are concrete plinth or kerb strips 0.5 m tall (3 × 1, 6 × 1, and an L-shaped 2.5 × 2.5), 12–20
tris. They suit a raised house base or a step at doorways.

**Beds: no (interior).** `SM_Bed_A_001..005` and `SM_Bed_B_001` are iron beds, mattresses,
pillows and a bunk.

**Cables: use, later dressing.**
- `SM_Cable_A_001..007`: flat cards of hanging wire, 2–8 tris.
- `SM_Cable_B_001..004`: wire bundles, 3–4 m, about 5k tris each.
- `SM_Cable_C_001`: a ring hanger.
- `SM_Cable_D_001`: a single 2 m wire, 108 tris.

Overhead wire tangles are essential to the Manila look. The `B` bundles are heavy.

**Chairs: maybe, later.** `SM_Chair_A_001/002` are school and kitchen chairs, about 16k tris
each. Too heavy.

**Clothes: use, later dressing.** `SM_Cloth_A_001..005` are hanging shorts, shirts and towels on
hangers, 7–21k tris. They're heavy. `SM_Cloth_B_001/002` are hanging sheets, 1–4k. Laundry is
very PH.

**Curtains: maybe.** `SM_Curtain_A_001` is a 3.25 m drape, 10.7k tris. `A_002` is its rod.

**Damage and debris: maybe.**
- `SM_DamageWall_A_001/002`: small peeled-paint patches, 0.3 m.
- `SM_Debris_A_001..003`: rubble piles, 1.5 m, 3–6k tris.

**Deco: no.**
- `SM_DecoCage_A_001`: a 3 m rail box.
- `SM_DecoStreet_A_001..009`: posters and signs as flat cards with Chinese and Japanese text, pink
  ad walls.

The text is wrong for PH, so use these only with new textures. `A_009` is a louvred vent panel
(0.8 × 1.0 m), which is usable.

**Drying racks: use, later dressing.** `SM_DryingRack_A_001..003` are wall-mounted laundry bars
and racks, 60–384 tris.

**Electrical: use, later dressing.** Electrical boxes are a strong PH look.
- `SM_ElectricalBox_A_001..003`: a small wall box (10.8k tris), a meter on a post with conduits
  (19k), and a 0.76 m conduit stub.
- `SM_ElectricBox_B_001/002`: rows of 6 meters on a board, 3–4 m long, 23–24k tris. This is the
  classic Meralco meter bank on a wall. It's heavy.
- `SM_ElectricBox_C_001..005`:
  - `C_001`: transformer cans hung on a bar, 45k tris.
  - `C_002`: a plain box, 12 tris.
  - `C_003`: a meter box with a window, 132 tris.
  - `C_004`: a grey panel, 228 tris.
  - `C_005`: a junction with cables, 17k tris.

**Fabric: maybe.** `SM_Fabric_A_001/002` are tarps over a table or stall, 7 × 3 m.

**Fans: maybe.** `SM_Fan_A_001/002` are a ceiling fan and its blades.

**Floor: in use, the gallery deck.** `SM_Floor_A_001` is a 3 × 3 × 0.2 m slab, 768 tris.

**Front: maybe.** `SM_Front_A_001` is a 1.5 × 0.8 m tiled step or threshold slab.

**Furniture, gas and kitchen: no (interior).** `SM_Furniture_A_001/002`, `SM_Gas_A_001` (stove
top) and `SM_KitchenProp_*`. One exception: `SM_Gas_B_001`, the LPG tank (0.5 × 0.9 m, 2k tris),
is very PH outside eateries.

**Hanger: maybe.** `SM_Hanger_A_001` is a hook rail, 5.5k tris.

**House doors: in use.**
- `SM_HouseDoor_A_001/003`: 1.5 m door slabs, glazed and plain.
- `A_002/004/005`: lattice and bar grilles. These are in use.
- `B_001`: a 4-pane glazed door.
- `B_002`: a half-glazed door.
- `B_003`: the louvred door, in use.

**AsiaSlum house wall kit: important, use.** This is a complete, light modular wall system. It's
a cheaper alternative to the Favela tiles at 12–270 tris against the Favela tile pieces, and it
already has openings.
- **Wall finish:** render on top, with a teal or grey painted dado band about 1 m tall along the
  bottom.
- **Plain walls:**
  - `SM_HouseWall_A_001`: 3 × 0.2 × 4 m, 96 tris.
  - `A_001_HalfA`: 1.5 × 4 m.
  - `HalfB`: 3 × 2 m.
  - `HalfC`: 1.5 × 2 m.
  - `A_002`: 6 × 4 m, 12 tris.
- **Corners:** `SM_HouseWallCorner_A_001` (1.5 × 1.5 × 4 m, an L) and `A_002` (2 m tall).
- **Door frames:**
  - `SM_HouseWallDoorFrmae_A_001/002`: a 3 × 4 m wall with a door opening (`002` has no dado).
  - `A_003`: an open 3 × 4 m frame.
  - `A_004`: a white roller-shutter frame with a grille, 3 × 3.8 m. This is the sari-sari or
    shop front.
  - `B_001`: 6 × 4 m with a wide opening and shutters.
  - `B_002`: 6 × 1 m deep, a shop counter front with a window.
  - `B_003`: an open frame.
- **Window walls:**
  - `SM_HouseWindow_A_001/002`: 3 × 4 m walls with one window, at sill heights about 1 m and
    1.5 m.
  - `B_001`: 6 × 4 m with 4 windows.
  - `B_002`: 6 × 4 m with 2 wide windows.

**Lights: use, later dressing.** `SM_Light_A_001..003`: an enamel pendant (17k tris), a bare bulb
on a cord (3.5k) and a fluorescent tube fitting (6.9k). The bare bulb and the tube are very PH.

**Lock and mailboxes: maybe.** `SM_Lock_A_001` (a padlock, 2k tris) and `SM_MailBox_A_001..004`
(rusty wall mailboxes, 240–2k tris).

**Corrugated metal: key for roofs. These are the best roof pieces in the packs.**
- **`SM_MetalPlate_A_001/002`:** single corrugated sheets, 1.62 × 0.05 × 3.25 m, 364 tris. They
  stand upright and hang down from the pivot.
  - `A_001` is rusty and `A_002` is galvanised grey with spots of rust.
  - That's real sheet proportion, and about 1/8 of `SM_Slate_01`'s 2,872 tris.
- **`A_003/004`:** the same sheets at 1.65 m long.
- **`SM_MetalPlate_B_001/002`:** pre-made patchwork piles of overlapping rusty and galvanised
  sheets, laid flat: 3.4 × 2.6 × 0.8 m (1.5k tris) and 6.2 × 2.6 × 0.8 m (2.5k). They're
  ready-made "messy roof" panels, but 0.8 m thick (sheets heaped up). Check them in context
  before using them.
- **`SM_MetalPlate_C_001`:** a 2 × 3 m checker-plate deck with a channel underside. It has a
  WorldGridMaterial slot, so override it.

**Mirror, washing machines and plants: no (dressing).** `SM_Mirror_A_001`,
`SM_OldWashing_A_001/002` and `SM_Palnt_A_001..003` (potted plants, 2–12k tris). The plants are
good PH dressing later.

**Pipes: maybe, later.** `SM_Pipe_A/B/C_*`, `SM_PipeDeco_*`, `SM_PipeHanger_A_001` and
`SM_PipeValve_*` are short pipe elbows, tees and valves, 0.3–1 m, 0.5–4k tris. Downpipes could be
built from these.

**Plastic: use later.** `SM_PlasticBowl_A_001..004`: red planggana basins, buckets, a bin and a
lid. Very PH dressing.

**Rails: in use.** `SM_Rail_A_001` is a 3 m steel balcony rail section, 1.78 m tall, 460 tris. The gallery rail, scaled to 1.05 m.
`A_002` is a post.

**Fridges: no.** `SM_Refrig_A_001..003`.

**Roll-up shutters: use.** `SM_RollupDoor_A_001/002` are steel roll-up shutters, 1.9 × 2.8 m and
5.5 × 3.3 m, 36–56 tris. `SM_RollupDoorFrame_A_001/002` are their 6 m frames, 44–176 tris. They
suit a sari-sari store or garage front.

**Roof pieces: key for roofs.**
- **`SM_Roof_A_001/002`:** a corrugated lean-to awning on a timber frame with diagonal brackets
  underneath, 6.2 × 2.2 × 1.1 m and 3.2 × 2.2 × 1.1 m, 604 tris. A ready-made door or window
  canopy, like the awning over the window in the user's reference.
- **`SM_Roof_B_001`:** a flat plank board, 1.5 × 4 × 2.1 m bounds (it stands tilted), 20 tris.
- **`SM_Roof_B_002`:** a thin 4 m board, 0.08 × 4 × 2.28 m bounds, 20 tris. Usable as a
  fascia or barge board.
- **`SM_Roof_B_003`:** a triangular gable infill board, 0.2 × 4 × 1.9 m, 12 tris. The gable-end
  triangle.

**Rope: maybe.** `SM_Rope_A_001/002`.

**Security window grilles: use.**
- `SM_SecurityWinodw_A_001`: a rusty window grille, 2.1 × 1.9 m, 896 tris. Very PH.
- `B_001`: a 3 × 2.6 m lattice grille, but 82k tris. Too heavy.

**Heavy grilles: no.** `SM_SecurityWinodw_B_001_Half`, `B_002` and `B_002_Half` are 82–85k tris
each. `SM_SecurityWinodwLock_A_001` is 5.6k tris for a tiny lock.

**Shelf: no.** `SM_Shelf_A_001`, a wall shelf.

**Shop pieces: in use.**
- `SM_Shop_A_001`: a 3 × 1 × 4 m stall front with a counter and an open bar frame, 196 tris.
  In use for the shop row.
- `SM_ShopFrige_*`: drinks fridges. Maybe, interior.
- `SM_ShopProps_*`: steel kitchen counters, sinks, a fryer, trays. These are carinderia
  (canteen) props. Maybe, later.
- `SM_ShopScreen_A_001/002`: a light awning frame of steel poles, 3 m and 6 m × 2.7 m tall,
  740 tris. It could hold tarps.

**Interior: no.** `SM_SideTable_*`, `SM_Sink_A_001`, `SM_Sofa_*`, `SM_Table_*`, `SM_Tissue`,
`SM_Toilet_*`, `SM_TV_A_001` (CRT TV, period-correct indoors).

**Signs: maybe, retexture.**
- `SM_Sign_A_001/002`: 3 m and 2.5 m wall sign boards, 156 tris. They need our own textures.
- `SM_Sign_B_001..005`: projecting signs and a lightbox. Their slots are WorldGrid or blank,
  so override them.

**Stairs: in use.**
- `SM_Stair_A_001` is the gallery stairs (its top edge is the pivot).
- `SM_Stair_A_002` is a 3 m concrete stair, 1.15 m rise, 236 tris. A doorstep or low stair.
- `SM_StairRail_A/B/C_*` are pipe handrails, 48–2k tris.

**Switch: no.** `SM_Switch_A_001`, a wall switch.

**Tarps: use.** `SM_TarpCover_A_001/002` are tarps hung from a rod, about 2 × 2.8 m, 300 tris.
Good as door curtains or a shade.

**Text: no.** `SM_Text_A_001..005` are flat cards of Asian text.

**Trims: use for the building.**
- `SM_Trim_A_001/002`: 6 m and 3 m concrete beam or band strips, 0.4 × 1.0 m, 12 tris.
- `SM_Trim_A_003`: an L corner.
- `SM_TrimWall_A_001`: a 3 × 0.2 × 1.5 m low wall or parapet, 20 tris.

These are a very cheap band and parapet. They could replace `SM_Wall_14` and, partly,
`MainBorder_04` (2.5k tris each).

**Water taps: maybe.** `SM_WaterTap_A_001/002` are standpipe taps with a hose, but 14–16k tris.
The communal gripo is very PH.

**Windows: use.**
- `SM_Window_A_001/002`, `SM_Window_B_001/002`: tall casements 0.65–0.74 × 1.7–1.9 m, plain,
  6-pane and 3-pane.
- `SM_Window_A_003`: a wide 1.3 × 1.0 m.
- `SM_Window_B_003..006`: tall 1.4 × 2.3 m (and `B_005` 3.4 m), plain and 6-pane.

All are 52–184 tris with white weathered timber frames.

**Wood: maybe.** `SM_Wood_A_001..003` are 0.5 m loose planks, 1–2k tris. Heavy for what they
are.

**AsiaSlum summary:**
- **Fit:** strongest for building parts. A cheap modular wall kit with a dado band, shutters,
  grilles, casement windows, and the corrugated sheets and awnings for roofs.
- **Props:** utility props are PH-plausible (meters, cables, basins, laundry, bulbs), but many
  are 10–25k tris.
- **Avoid:** anything with Chinese or Japanese text, and the tenement prefabs.

## Megapack Favela (202)

**Weapons: no.** `SM_AK47A_01..04`, 9.8k tris; one has a pink camo skin. These are props, and
the game has its own weapons.

**Dish antennas: maybe.** `SM_Antenna_01..03` are satellite dishes, 1.9 × 2 m, 2.9k tris, with
"SKY HDTV" branding on one. Cable dishes are rare in PH in 2002, and the branding is wrong. TV
aerials (AsiaSlum) fit better. `SM_AntennaSupport*` are their wall brackets.

**Beds: no.** `SM_Bad_01` (an iron bed) and `SM_BadPart_*`.

**Water tanks: use, later.** `SM_Barrel_01` is a big round water tank (1.5 m across, 0.8 m tall,
1.2k tris), orange or blue. `SM_Barrel_Cap_01/2` are its lids. Rooftop water drums are very PH,
but they're dressing.

**Corner and building shells: maybe.**
- `SM_BrickWallCorner_01`: an L corner, 1.6 × 2 × 4.9 m, 410 tris.
- `SM_building_01..10`: one-storey, open-topped room shells, 7 × 3.75–6.6 × 3 m, 560–1,120 tris,
  with window and door holes. The wall kit already does this better.

**Carpet, statues and clothes: no.**
- `SM_Carpet_01`: a Persian rug.
- `SM_ChristStatue_01/02`: Christ the Redeemer and its plinth, 30 m. That's Rio, so no.
- `SM_Clothes_01..03`: clothing on mannequin poses, 9–15k tris.

**Concrete pieces: use.**
- `SM_Concrete_Beam_01`: a 7.8 m thin beam.
- `SM_Concrete_Parapet_01`: a 2.25 × 0.94 m parapet slab, 76 tris.
- `SM_ConcreteFencing_01/02`: 2.5 m straight and curved low walls with an orange cap, 1.2–2.5k
  tris.

**Stoves: no.** `SM_CookingStove_*`.

**Decal: maybe.** `SM_Decal_Corner_01` is a set of mesh strips for corner grime.

**Doors: in use earlier.**
- `SM_Door_01`, `_Blue` and `_Green`: 1.07 × 2.18 m doors with a small window, 1.2k tris.
- `SM_Door_Jamb_01`: a timber jamb, 132 tris.

**Electric pole parts: use, later.**
- `SM_ElectricPole_Part_01..10`, `PartA_03`: crossarms, insulators and a transformer can, 2–19k
  tris.
- `SM_ElectroSupport_01`: an 8 m light pole with a platform, 1.6k tris.

Poles with crossarms and wire tangles are the signature Manila streetscape, but many parts are
6–16k tris.

**Fencing: maybe.** `SM_Fencing_01..03` are rough stone or plastered wall slabs (1.4–2.1 m) and a
post, 0.7–1.8k tris.

**Football goal: no.** `SM_FootbalGoal_01`. Basketball is the PH sport.

**Gas pipes and lamp: maybe.**
- `SM_Gas_Pipe_01/02`: wall gas risers.
- `SM_LampA_01`: a floodlight bar, 8.3k tris.

**Lamp: maybe.** `SM_LampB_01` is a floodlight bar.

**Main borders: in use, and the budget problem.** `SM_MainBorder_01..04` are 1.5 m rough concrete
trim bars, about 2.5k tris each. They read as cast concrete ledges. The asset thread proposes
a low-poly replacement; AsiaSlum `SM_Trim_A_*` is a 12-tri alternative.

**Road and mannequins: no.** `SM_MainRoad_01` is a 5 × 3.3 m road card. `SM_Mannequin_01/02` are
41k tris each.

**Mattresses: no.** `SM_Mattress_01/02`.

**Metal pieces: maybe.**
- `SM_Metal_Bracket_01`: a U bracket.
- `SM_Metal_Door_01`: a 1.06 × 2.33 m door with a barred top half, 200 tris. A good back door.
- `SM_Metal_Fence_01/02`: chain-link panels, 2.1 m.
- `SM_Metal_Gate_01`: a green painted steel gate leaf, 1.66 × 2.41 m, 764 tris. Very PH.
- `SM_Metal_Window_Frame_03`: a thin steel frame.
- `SM_MetalBucket_01/02`: rusty buckets.
- `SM_MetalRail_01/02`: pipe posts and rails, 180 tris.

**Monorail: no.** `SM_MonorailA_01` and `SM_MonorailColumnA_01`, 20 m. Rio.

**Old stairs: maybe.** `SM_Old_Stair_01/02` are 1.5 × 3.5 × 1.5 m concrete stair flights with a
landing, 2.2k tris. Good for an outside stair to an upper door.

**Pillar: in use.** `SM_Pillar_01` is the 8 m round concrete pillar, 976 tris, centred pivot.
Used for the gallery posts.

**SM_Plane: no.** It's actually a 100 × 100 × 50 m rounded basin, a terrain or water piece.

**Plants: maybe, later.** `SM_Plant_01..27` are grass tufts, weeds, small bushes and palm shrubs,
40–21k tris. Weeds at wall bases would suit the setting.

**Plates: use.**
- `SM_Plate_01`: a 7.7 × 4.5 m floor with timber and plank strips.
- `SM_Plate_02`, `_6`, `_7`, `_9`: 6–7 m concrete floor or roof slabs, 0.2 m, 44–192 tris.
- `SM_Plate_8`: a dark tiled slab.
- `SM_Plate_03`: a 2 × 2 m rounded block.

The slabs could serve as roof decks and floor plates.

**Podiums and plate tile: maybe.**
- `SM_Plate_Tile_03`: a 2.25 m concrete slab.
- `SM_Podium_01..03`: 5 × 5 × 0.8 m raised plinths with red tile tops and blue sides, 12–68
  tris.
- `SM_Rad_01`: the same door as `SM_Door_01`, red.

**Rain pipe: use.** `SM_Rain_Pipe_01` is a 2.08 m red downpipe with brackets, 564 tris. Stack
them for downpipes from the metal roofs.

**Fridge: no.** `SM_Refrigerator_01`.

**Tarpaulins: maybe.** `SM_ScaneTarpaulinClear_01..03` are hanging blue tarps, 6 m tall, and a
tarp over a sloped frame, 7–17k tris. Heavy. Blue tarp roofs are very PH, but these are dense.

**Sewer stack: maybe.** `SM_Sewer_01` is a vent pipe on a block, 2.8 m.

**Shelves: no.** `SM_Shelf_01..04`.

**Sidewalk: maybe.** `SM_sidewalk_01` is a 10 × 5 m road strip with kerbs, 132 tris.

**Roof sheets: in use.** `SM_Slate_01` and `SM_SlateA_02` are 3.83 × 1.54 m corrugated sheets,
about 2.8k tris each. That's heavy, and dark grey with no rust. The AsiaSlum `MetalPlate_A`
sheets are lighter and look better.

**Soccer net and speakers: no.** `SM_SoccerNet_01` and `SM_Speakers_01..03`.

**Stairs: maybe.**
- `SM_Stair_01`: a timber open-riser stair, 3.4 × 2.6 m rise, 6.3k tris.
- `SM_Stairs_Base_01`: a concrete stair base block, 1.45 × 3.5 × 5.3 m, 64 tris.

**Stand: maybe.** `SM_Stand_01` is a plank table on blocks, a market stand.

**Street lamps: use, later.** `SM_StreetLamp_02/03` are wall-arm and pole cobra lamps, 1.4–1.7k
tris. `_05..08` are fluorescent tube bars. Cobra-head street lights are right for 2002 Manila.

**Table: no.** `SM_Table_01`.

**Tile plate: maybe.** `SM_TilePlate_01` is a 4 × 4 m slab.

**Favela wall kit: in use.** These are 3 m storeys.
- **Plain walls:**
  - `SM_Wall_03` (2 × 3 m, 14 tris), `_06` (2 m) and `_15` (2 × 1.06 m low wall).
  - `SM_Wall_04` (5 × 3 m with 2 windows) and `_11` (2.25 × 3 m with a window).
  - `SM_Wall_02`/`_Rad` (5 × 3 m with a door and 2 windows, 316 tris).
  - `SM_Wall_09` (4.25 m, a U with a window).
- **Shells and corners:**
  - `SM_Wall_06_test`: a 3-post portico frame.
  - `SM_Wall_07`: a blue U shell.
  - `SM_Wall_08`: an L with a cornice.
  - `SM_Wall_12`: a blue L.
  - `SM_Wall_13`: a U with a door.
  - `SM_Wall_Corner_01`: an L post.
- **Columns:** `SM_Wall_Column_02/03/05` are 3 m posts.
- **Parts:**
  - `SM_Wall_10`: a 3 m pilaster.
  - `SM_Wall_14`: the band, in use.
  - `SM_Wall_017`: a stepped plinth block.
  - `SM_Wall_darail_03`: a 5 m rail strip.
- **Tiles:** `SM_Wall_Tile_01/02/03/Blue/Rad/White` are 2.25 × 0.2 × 3 m tiles (`_03` is 1.13 m),
  96–116 tris. These are what the generator uses. Their default materials are yellow, brick and
  blue render; the generator overrides them with the CHB material.
- **More wall pieces:**
  - `SM_Wall_Tile_Yellow`: another 2.25 × 3 m tile.
  - `SM_Wall_Windows_01`: a 2.25 × 3 m tile with a window hole.
  - `SM_WallDoor_01/02`: 2.25 × 3 m tiles with a door hole, 84 tris.

**Water dispenser: no.** `SM_WaterDispenser_01` and `SM_WaterDispenserRag_01`, a sink stand and a
rag.

**Window frames: maybe.**
- `SM_Window_Frame_01/02`: thin steel window grilles, 0.4 m and 1.1 × 1.6 m, 100–180 tris.
- `SM_Window_Part_01`: a 3.3 m strip of window frames.

**Windows: in use.**
- `SM_windows_01/02`: 1.1 × 1.33 m timber double casements, natural and orange, 856 tris.
- `SM_windows_03`: a single, 0.6 m.
- `SM_windows_04`: a 0.6 × 0.6 m sash.
- `SM_windows_05`: a 1.75 × 1.3 m 4-leaf window with diamond lattice glazing, 1.2k tris. It reads
  as capiz-style, which fits PH.
- `SM_windows_06`: a blue 1.72 × 0.8 m 4-pane frame. In use as the terrace banister.
- `SM_windows_07`: a boarded panel.

**Wooden parts: in use.**
- `SM_Wooden_part_01/02/04`: plank fence panels, 1.2–1.9 × 0.76 m.
- `SM_Wooden_part_03`: a tapered 3.74 m solid plank. Was the gallery rail; the user: "the wrong model".
- `SM_Wooden_part_05`: a single 1.9 m plank, 52 tris. In use for posts and beams; a good fascia
  board.

**Yellow door: maybe.** `SM_Yellow_01`, the door again.

**Favela summary:**
- **What we use:** the wall kit is the generator's backbone.
- **Good fits:** plates and slabs, the rain pipe, the cobra street lamps, the steel gate and barred
  door, and the capiz-like window.
- **Avoid:** the Rio identifiers (the Christ statue, the monorail, the football goal), satellite
  dishes and AKs.
- **Budget:** the `Slate` sheets and `MainBorder` trims are heavy.

## Philippines_Markets (206)

**LED lights: no.** `SM_3_WINGS_LIGHT_01..05` and `SM_4_WINGS_LIGHT_01..06` are folding
"wing" LED bulbs, 0.6–1.1k tris. **Anachronism:** these are a 2015+ product. Use AsiaSlum's bare
bulb or fluorescent tube for 2002.

**Market props: use, later.**
- `SM_Barrel_01/02`: plastic and steel drums, 1 m, about 2.1k tris.
- `SM_BILL`: a receipt.
- `SM_Bollard_01a/b`: striped and plain bollards, 0.94 m, 160 tris.
- `SM_Bottle_Tall`: a bottle.
- `SM_BottleCrate_01..03`: beer and soft-drink crates, 2.8–5.3k tris. These are very PH (the
  sari-sari crate stack), though heavy.

**Crates and buckets: use, later dressing.**
- `SM_BottleCrate_04`: another crate.
- `SM_Box_Wood_01..12`: open slatted produce crates, 0.4–0.6 m, 380–620 tris. Good market
  clutter.
- `SM_Box_Wood_Side_01..05`: crate sides or small pallets.
- `SM_Bucket_01..03`, `SM_Bucket_Lid_01/03`, `SM_Bucket_Plastic_Tall_01`: paint and water
  buckets.

**Cardboard: use, later.** `SM_Cardboard_Banana_Box_01/02`, `SM_Cardboard_Flat_01..05` (flattened
boxes, the karton people sleep on) and `SM_CardboardBox_01..03`, 44–900 tris. Cheap clutter.

**Chains: no.** `SM_Chain_01..06` and their `_Rusty` versions, 1–19k tris. They're heavy for what
they are.

**Market small props: maybe.**
- `SM_Chopping_Block_01/02`: a tree-slice chopping board and a steel stand. Good for a wet
  market.
- `SM_DigitalScale_01`: a digital scale. Plausible in 2002, but modern-looking.
- `SM_DUCT_TAPE`: duct tape.
- `SM_ElectricalCabinet_02`: a 1 × 1.4 m metal cabinet on a hazard-striped plinth, 5.3k tris.
- `SM_Extension_01..07`: power strips and cords.

**Food: use, later.** Street-food props are very PH, though heavy for tiny props.
- `SM_Extension_PIPE_01..05`: extension cords tied to poles.
- `SM_FishBalls_01/02`, `SM_FriedSausage_01/02`, `SM_FriedWonTons_01/02`: fishballs, hotdogs and
  wontons on skewers, 0.6–1.1k tris.

**Market small props, continued.**
- `SM_Hanging_Scale_01`: a hanging spring scale, 3.4k tris.
- `SM_LargeBowl_01`: a basin.
- `SM_LOCK_01..03`: padlocks.
- `SM_InifinityWall_01`: an 80 m photo-studio backdrop cyclorama. **No.**

**Market stall kit: use for stalls.** This is a coherent kit for wet-market and stall rows.
- **`SM_Market_Stall_Metal_Top_BASE_01..07`:** 1.9 × 1.1 × 0.73 m concrete stall counters (a
  U shape with a cupboard door), painted in blue, yellow, cyan, pink and peach. 290–10k tris; vary
  which variant you pick.
- **`COUNTERTOP_01/02`:** concrete tops, 2 × 1.1 m, 44–140 tris.
- **`POLE_01..04`:** steel pipe frames above the counter with timber battens, 1.7 × 1.5–1.8 ×
  1.0 m, 3.4–5.4k tris.
- **`ROOF_01..04`:** stall roofs of rusty corrugated patchwork with planks and debris on top, about
  2 × 1.2 × 0.4 m, 13–17k tris. The look matches the user's reference roof, but they're too heavy
  to tile over houses. The rust patchwork texture could be reused on our own sheets.
- **`SM_MarketStall_Tiled_*`:** a second, tiled stall type:
  - `Bottom_01/02`: tiled bases, about 100–160 tris.
  - `Table_01/02`: tiled tables, 2 × 1.2 m.
  - `Pole_01/02`: pipe frames.
  - `Top_01/02`: a wire cage and a timber box top, 4.6–5.1k tris.
  - Bulb, socket, poster, tri-hooks, zip ties and hanging hook.

**Hooks and trays: maybe.** `SM_METAL_HOOK` (a meat hook) and `SM_Metal_Tray_01..04` (steel
trays).

**Monobloc: use, later. Iconic PH.**
- `SM_Monobloc_Chair_01`: the monobloc plastic chair, 1.8k tris.
- `SM_Monobloc_Chair_03`: a monobloc bench, 4k.
- `SM_Monobloc_Stool_01/02`: plastic stools, 1.3–1.5k.

**Paper and plastic: maybe, later.**
- `SM_NOTE_01/02`, `SM_Paper_Towel_*` and `SM_PIN_01..03` (receipt spikes): paper props.
- `SM_PLASTIC_BAGS`: a plastic bag.
- `SM_Plastic_Crate_01..04`: produce crates, 0.45–7.3k tris.
- `SM_PlasticBox_*` and `SM_PlasticTray_*`: plastic boxes and trays.

**Ramps: use for ground details.** `SM_Ramp_01/02` are small concrete wedge ramps, 0.5–0.8 m. That
means kerb ramps at doorways.

**Bins and bags: later.**
- `SM_Recycle_Box_01` and `SM_Recycle_Boxes_01`: swing-lid bins.
- `SM_Rice_Bag_*` (12 types): rice sacks, curled, flat, full and half-full, 0.7–2.1k tris. Very
  PH sari-sari or market.

**Market tables: maybe.**
- `SM_Round_Chopping_Block_03` and `SM_Scale_01`: a board and a dial scale.
- `SM_SmallBowl_01`: a bowl.
- `SM_Speed_Barrier_01_2m`: a 2 m speed hump, 292 tris.
- `SM_Styrofoam_Box_*`: fish-market styro boxes.
- `SM_Table_01`: a folding market table, 648 tris.
- `SM_Toilet_Paper_*` and `SM_TOWEL`: paper and a towel.
- `SM_Umbrella_01a/01b/02` and `SM_Umbrella_Base_01`: market umbrellas, 4.7–7.3k tris.
- `SM_WALL_PIN_01/02`: pinned papers.

**Water meters: use, later.** `SM_Water_Meter_Cage_01/02` are banks of water meters in steel
cages, 9.8–22k tris (heavy). `SM_Water_Meter_Single_01/02` are 2.3k tris. Maynilad meter cages
are a strong PH alley detail.

**Water and wires: maybe.**
- `SM_WaterCooler_Bottle_01`: a 5-gallon water jug.
- `SM_WINGS_LIGHT_CORD`: the cord for the LED lights.
- `SM_WIRE_01/02`: loose wires, 1.6–2k tris.

**Philippines_Markets summary:**
- **What it is:** a stall-and-market prop pack, not buildings. The stall kit (counters, poles, rusty
  patchwork roofs) and the props are authentic, but almost everything is dressing, out under the
  blockouts rule.
- **Anachronism:** the wing LED lights.
- **Rendering note:** most of this pack's textures didn't resolve in Blender (the materials use
  tint parameters), so the grey renders show shape only. Check colour in the editor thumbnails.

## Megapack MiddleEast (143)

The user's earlier rule: not MiddleEast's buildings. Its generic street props are fine.

**AC units: maybe.** `SM_Air_Conditioning_01`, `_Blue_02` and `_White_03` are 1.2 × 0.9 m wall-hung
evaporative coolers, 2k tris. They read close to window-type ACs.

**Small props: maybe.**
- `SM_Antenna_01`: a 5 m mast, 244 tris.
- `SM_apple_set_01/02`: apples.

**Awnings: maybe, close to PH.**
- `SM_awning_01`: a slatted blue corrugated awning on a frame, 1.5 × 4.4 m, 4.7k tris.
- `SM_awning_base_01`: its bare frame, 184 tris.
- `SM_awning_cloth_01`: a timber-slat version.

**Not useful: no.**
- `SM_balcony_01/02`: a flat balcony rim, 112–128 tris.
- `SM_Barbed_wire_01/02`: razor wire coils.
- `SM_bridge_01`: a 10 m plank bridge, 2.4k tris.
- `SM_Building_01`: a 6 × 7 × 4 m plain box.

**Cardboard: use, later.** `SM_Cardboard_box_01..04` are 12-tri boxes, extremely cheap. Better
than the Markets boxes for distant clutter.

**Cart: maybe.** `SM_Cart_01` is a 5.4 m flatbed cart, 1.5k tris. Close to a PH kariton.

**Channel, litter and clothes: maybe or no.**
- `SM_channel_01`: a 22 m drainage channel.
- `SM_cigarette_butt_*`, `SM_crumpled_cup`, `SM_cup`: litter.
- `SM_clothes_A/B_*`: draped laundry, 0.4–5.8k tris. Lighter than the AsiaSlum laundry.

**Concrete: maybe.**
- `SM_Concrete_Block_01/02`: Jersey barriers, 3.5k tris.
- `SM_Concrete_Fence_01..03`: 3.5 m T-wall slabs. Military-looking, so **no**.

**Doors: maybe.**
- `SM_Door_02`: a blue plank door, 2.2k tris.
- `SM_Door_color_03`: white.
- `SM_Door_hingles_01`, `SM_Door_part_02`: hinges and a door part.
- `SM_Doorway_01`: a teal steel doorway frame, 48 tris.

**Clothesline: use, later.** `SM_Dryer_01` is a 4.2 m clothesline frame, 2.5k tris.

**Electric poles: use, later.**
- `SM_Electric_Pole_01..05`: 9–10 m concrete and timber poles with crossarms and transformers,
  1.3–5.1k tris. Lighter than the Favela pole parts, and close to PH Meralco poles.
- `SM_electrical_contact_01`: a crossarm.

**Ground litter: maybe.**
- `SM_FieldGrass_01/02`: grass.
- `SM_flagpole_01`: a flagpole.
- `SM_Garbage_bag_01/02` and `_green_03`: trash bags, 4.6–5.1k tris.
- `SM_glass_01`: a glass card.
- `SM_Graffiti_Decal_00..12`: graffiti cards, 2 tris. They need checking for script content.
- `SM_gravel_01`: a gravel strip.

**Houses: no.** `SM_House_01/02/03/06/08/09/10` and `SM_House_a_part_*` are flat-roofed
Middle-Eastern houses (crenellated, mud-brick colours), 1.5–48k tris. `SM_House_a_part_03/04`
are a 7 × 7 m wall ring and slab.
- `SM_House_a_part_05..07`: 0.7 m wall rings (parapets).
- `SM_House_a_part_2..9`: 7 × 7 × 3 m wall rings with windows, 480–520 tris, in sand, ochre or
  green.

The MiddleEast building ban stands.

**Market table: maybe.** `SM_market_table_01/02` are slatted stall tables with a roof, 324 tris.

**Cheap pieces: use.**
- `SM_Metal_Carcass_01`: a gabled steel-pipe shed frame, 2.6 × 3.2 × 2.5 m, 416 tris. A tarp
  shelter frame.
- `SM_metal_fence_01`: a 1.3 m green fence panel.
- `SM_metal_gate_01`: a 3.4 × 3.1 m roller-gate panel, 640 tris.
- `SM_Paper`: a paper card.
- `SM_Pipe_01`: a 1.1 m clay pipe.
- `SM_Platform_Water_Tank_01`: a steel stand for a rooftop tank, 1.6 × 2.4 × 0.9 m, 272 tris.

**Ground: maybe.**
- `SM_road_02..06`: 10 × 10 m dirt and road tiles with kerbs, 270–306 tris.
- `SM_sidewalk_01/02`: 4 × 4 m paving, 1.5k tris.

**Stairs and tents: no.**
- `SM_stairs_01`: a stairwell box, 4 × 4 × 3.6 m, 134 tris.
- `SM_Support_01`: a bracket.
- `SM_Tent_01` and `SM_tent_02`: canvas tents and a shade sail, 1.8–9k tris.

**Tile and paint: maybe.** `SM_Tile_01` (a 2 m paving slab) and `SM_tin_of_paint_01` (a paint can
with Cyrillic text, so no).

**Walls: maybe.**
- `SM_wall_01/02`: 4 × 3.45 m concrete walls, with and without a door opening. Grey render over
  a brown dado, 28–60 tris.
- `SM_wall_part_04`: a 7 m window wall.

**Water tanks: use, best fit.**
- `SM_Water_Pipe_01`: a 22 m industrial pipe rack. No.
- `SM_Water_Tank_01..03` and `SM_Water_Tank_BG_04`: 1.64 m cylindrical tanks in rusty orange,
  rusty blue, black and blue-and-grey poly, 704 tris.

These are the rooftop water tanks that mark a PH house. Use them with the tank platform when the
user allows rooftop items (they count as dressing now).

**Wheel: maybe.** `SM_wheel_01` is a tyre, 1.4k tris. Tyres weigh down PH roofs (in the user's
reference). That's dressing.

**Windows: use.**
- `SM_window_01`: a 3.3 m triple window, 228 tris.
- `SM_Window_02`: a timber frame.
- `SM_window_door_01`: a plank shutter, 12 tris.
- `SM_Windows_02/03`: triple and double casements, 180–412 tris.
- `SM_Windows_04`: **a window-type air conditioner in a timber frame**, 1.4 × 1.5 m, 2.2k tris.
  The classic 2002 PH window AC.
- `SM_Windows_grill_01/02`: 3.1 × 2.4 m bar window grilles, 248–688 tris.

**Wires and wood: use.**
- `SM_wire_part_01`, `SM_Wires_01`: a 27 × 37 m overhead wire web, 916 tris. A whole-street wire
  tangle for very little.
- `SM_wooden_beams_01..05`: 7.38 m timber beams, 0.25 × 0.24–0.34 m, **12 tris**. The cheapest
  rafters, purlins, fascia and eave beams in the packs.
- `SM_Wooden_Box_01/02`: crates.
- `SM_wooden_gates_01`: a 2.9 × 3.5 m slatted gate, 524 tris.
- `SM_wooden_pallet_01`: a pallet.
- `SM_Wooden_Shield_01/02`: a 4.5 m red plank fence, 350–380 tris.

**MiddleEast summary:**
- **Buildings:** off-limits, as the user said.
- **Useful finds:**
  - water tanks and their stand;
  - the window AC;
  - window grilles;
  - 12-tri timber beams (for the roof frame and kisame);
  - the overhead wire web;
  - electric poles;
  - 12-tri cardboard.
- **Avoid:** barbed wire, T-walls, Cyrillic paint cans and script graffiti.

## Megapack Yakohama (273)

The user's rule: not the Japanese-signage pieces.

**Rendering:** its textures didn't resolve in Blender, so the renders are white (shape only), and
most editor thumbnails are untextured too.

**Japanese city kit: mostly no.**
- `SM_AdvertisingFrame/Light`, `SM_Awning_05..08` (fabric shop awnings, 8k tris).
- `SM_BGBuilding*`, `SM_BGBuildingPlane_*`: background skyscraper cards.
- `SM_Billboard*`, `SM_BlindTile_*` (tactile paving), `SM_Bridge*`, `SM_Building*`, `SM_Canopy_01`.
- `SM_Citylight_02`, `SM_CycRoom_01`, `SM_Escalator*`, `SM_Entrance_*` (glass shop fronts).
- `SM_SignText_*`: katakana signs.
- `SM_Railways_01`, `SM_Support*`/overpass, `SM_TicketMachine_01`, `SM_TrainStation*`,
  `SM_VendingMachine_*`.
- `SM_StreetLamp_06/07`: lantern and globe lamps.
- `SM_Stairs_01/02`: station stairs.

**Usable shapes, low tris, need our own materials: maybe.**
- `SM_Border_01..10`: kerb strips.
- `SM_Floor_01`: a 3 m slab.
- `SM_Balcony_01..04`: 28-tri balcony slabs and parapets.
- `SM_Wall_03..32`, `SM_Wall_2x2_01`, `SM_Wall_up_18`: a plain 3.25 m wall kit with door
  frames, corners and ramps, 12–400 tris. `SM_Wall_32` is a 15.5 m gable-end wall.
- `SM_Window_01`, `SM_WindowFrame_01..07`, `SM_WindowSill_01`: windows and frames.
- `SM_Jalousie_01..04`: louvre panels, 12–168 tris. Jalousie windows are very PH. Our own plane
  jalousies already cover this.
- `SM_Pipe_01..16`: downpipes and duct pieces, 60–780 tris.
- `SM_ElectricBox_01/02`: 120-tri boxes.
- `SM_ElectricPole_1/03/4`: 58–104k tris. **No.** `SM_ElectricPole_Part_*` are the Favela pole
  parts again.
- `SM_Steps_01..03`: stair steps.
- `SM_Props_01..03`: a low wall and rails.
- `SM_Pylon_01`, `SM_RoadCone_*`, `SM_Road_*`, `SM_Sidewalk_01..08`: road pieces.
- `SM_PlasticBox_*`, `SM_Polyethylene_*`, `SM_MetalCan_*`, `SM_Bottle_*`, `SM_TrashBox_02`
  (7k tris): small props.
- `SM_GlassDoor_02`, `SM_Handrail_01`, `SM_MetalFance_03..05`, `SM_MetalShelves_02`: doors,
  rails and fences.
- `SM_VentilationTube_*`, `SM_TessPlane_01` (20k-tri plane, no), `SM_Wire_01`,
  `T_StreetSign_02`.

**Yakohama summary:** nothing here beats AsiaSlum or Favela for a PH alley. At most the plain
walls, pipes and borders could serve as untextured geometry with our own materials.

---

## What this means for the generator

### Roofs: the user's reference (2026-11-03) and the kisame

**Sheets.** Switch from `SM_Slate_01` (2,872 tris, dark grey) to AsiaSlum `SM_MetalPlate_A_001`
(rusty) and `A_002` (galvanised):
- 1.62 × 3.25 m, 364 tris, real single-sheet proportions.
- Mixing the two per sheet gives the reference's patchwork.
- `A_003/004` are the half-length versions, for short runs.

**Frame and kisame.**
- MiddleEast `SM_wooden_beams_01..05`: 7.38 m timber beams at 12 tris, for rafters, purlins
  and eave beams.
- Favela `SM_Wooden_part_05`: a 1.9 m plank at 52 tris, for the fascia board.
- AsiaSlum `SM_Roof_B_002`: a 4 m board, for the fascia.
- AsiaSlum `SM_Roof_B_003`: a 12-tri triangle, for the gable-end infill.
- The kisame boards themselves are flat panels, so thin boxes with a board or plywood material
  work.

**Ready-made awnings.**
- AsiaSlum `SM_Roof_A_001/002`: corrugated lean-tos with brackets, 604 tris. Use over doors
  and windows, like the window awning in the reference.
- MiddleEast `SM_awning_base_01`: a bare frame, 184 tris.

**Patchwork reference.** AsiaSlum `SM_MetalPlate_B_001/002` and the Markets stall roofs show the
rust-patch look. They're too thick or heavy to tile, but their materials can be reused.

**Downpipes.** Favela `SM_Rain_Pipe_01`, stacked; in use.

**Wall dressing in use (2026-11-04).** AsiaSlum `SM_Balcony_A_003` as overhanging rooms.
MiddleEast `SM_Windows_04` (a cooler in a window frame) and `SM_Air_Conditioning_*` (desert
coolers, squashed to about 60 cm wide; a thin rod below reads as a bracket). AsiaSlum
`SM_MetalPlate_A_003/004` as tin patches, `Interior/SM_Front_A_001` as a tiled step top.

**Street dressing in use (2026-11-05).** `SM_ElectricBox_C_002/003`, `SM_Antenna_A_001..003` (with
`MI_Antenna_A_001`), MiddleEast `SM_Antenna_01`, `SM_Light_A_002` (with `MI_Light_A_001`), Favela
`SM_StreetLamp_02/05/06`, `SM_Barrel_01` and caps, `SM_Stand_01`, `SM_Fencing_03`, `SM_Metal_Gate_01`,
`SM_RollupDoor_A_001`, `SM_TarpCover_A_002`, `SM_Sign_A_001/002`, `SM_Sign_B_005`. Favela's
`SM_Antenna_01` is the satellite dish; MiddleEast's is a bare 5 m mast. `SM_DamageWall_A_*` is under
`FBX/Interior/`.

**Laundry in use (2026-11-04).** MiddleEast `SM_clothes_A_02..05`, `B_01`, `B_03` have four
LODs, down to 200-350 tris; `A_01` is 395 with none. `SM_clothes_B_02` is 5.8k: left out.
AsiaSlum `SM_DryingRack_A_002` (108 tris) as wall racks. `SM_Rope_A_001` is 1,208 tris with
no LODs, so lines are engine cubes.

### Budget

The cheap pieces that could replace current heavy ones:
- AsiaSlum `SM_Trim_A_001/002` (12 tris) for `MainBorder_04` (2.5k tris, 73% of the level's
  triangles).
- The AsiaSlum house wall kit (12–270 tris, with openings and a dado band) as an alternative to
  the Favela tiles.

### Later dressing, when the user asks

Water tanks and their stand (MiddleEast), the window AC (MiddleEast `SM_Windows_04`), window
grilles, meter banks and water-meter cages, overhead wires (`SM_Wires_01`), poles (MiddleEast),
cobra lamps (Favela), monobloc chairs, rice sacks, crates, cardboard, basins and laundry.

### Anachronisms and wrong-place pieces

- **Anachronism:** the wing LED bulbs (Markets).
- **Branding:** the "SKY HDTV" dishes (Favela).
- **Rio:** the Christ statue and the monorail.
- **Script:** anything with Chinese, Japanese or Cyrillic text.
- **Military:** T-walls and barbed wire.
