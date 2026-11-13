# ProjectBopis — Progress Log

> Running record of project state and session-by-session progress, kept so
> context carries over between Claude Code sessions. Newest entry on top.
> Update this at the end of any session with meaningful progress or decisions.

## How to use this file
- Add a new dated entry for each session with notable work.
- Keep entries short: what changed, what was decided, what's next.
- Link to relevant files with `path:line` where useful.
- Move stale "Next Steps" into "Decided/Done" once complete.
- Keep one live **▶ RESUME HERE** (the newest entry's); older ones are marked *(old)*.
- Entries before 2026-10-21 (3) are in [ProgressLog_Archive.md](ProgressLog_Archive.md) (moved 2026-10-24, unchanged).

---

## 2026-11-13 — Mission 2 paper layout: the restaurant block
- **User:** the Mission 2 scenario (restaurant / smuggler compound), "Linear Level Design: Mission 2", "ignore the Navarro name, To be decided"; mid-work, "for this level, we can start using wave stlye encounters, in the restaurant is a good spot to put it, where you have to kill x amount of enemies for the next event that would open the door start".
- **Lore:** imported as *LEVEL SCENARIO — MISSION 2* (end of PART 2); the patrolman scenario is now marked Mission 1; the lead's name marked not final; *Wave encounters* added to PART 4. Claude-Rules §8 has the wave rule.
- **Layout:** `Design Document/Linear_Restaurant_Layout.html` + `.json` from the new `Tools/LevelGen/layout_linear_restaurant.mjs`. 7 sections (street, restaurant, back lanes, storage, upstairs + roof + plank + flats, workshop + burn yard, print shop), 12 fights, 64 gunmen, 9 inspects (4 needed), 12 checkpoints, 316 m, about 17-31 min. The courtyard is the loop (F3 from the west, F8 from the north after the flats). F1 is a wave encounter: kill 11 (4 + 4 at the front + 3 down a stair), at most 5 up, then the barred kitchen door opens. Longest fight sightline 23.5 m, the street 25.0 m.
- **Spec:** *Linear levels → Second one*. Plan item 52. GDD (+ html): *The second case: the restaurant*, and a changelog line.
- **Lengthened, same day** (user: "lengthen it, also remove the civilians in real time,we will evacuate them via cutscene"; "add more backalleys, somilar to what we have in the arena", "except linear", "linear or looping"): two new sections, the back alleys (the arena's 4.5 m, a ring round a block back to its first corner from the north, F11-F14, loop 2) and a two-storey safe house (F15-F16) knocked through into the print shop (now section 9, F17-F18). No civilians in play; the recognition cutscene gets the customers out. Now 9 sections, 18 fights, 100 gunmen, 10 inspects, 15 checkpoints, 499 m, about 25-45 min. Longest fight sightline 24.5 m. Lore, Claude-Rules §8, spec, plan 52 and the GDD updated.
- Not in UE5. Nothing committed.

## 2026-11-13 — Plywood: the user's texture, fewer sheets in the alley
- **User:** "I added a Plywood texture on the content folder. Use that instead of whatever you are using", "and use less boards on the Alley section"; asked, "Plywood room walls" and "All bare plywood"; of the texture, "can you fix it by resizing yourself?"; the bridge, "Yes, go ahead".
- **Texture** (`/Game/T_Plywood_BaseColor`, `_Normal_DX`, 1254 px, seamless): had `TC_EditorIcon` and no mipmaps. Now `TC_Default` on the colour, both resized to 1024 at build (`ResizeToSpecificResolution`), mips from the World / WorldNormalMap groups. The image is untouched. Saved.
- **New `MI_BackAlleys_Plywood_World`:** the user's texture on the hollow blocks' world-mapped material, 122 cm a repeat, Wood surface. Saved. **For plywood walls only** (`story_interiors` `PLY_MATS`). The wall patches keep their own plywood (user: "keep the patches as they are. The one I added is for actually plywood walls"), and so do the plywood doors.
- **`Lvl_01_Slum`** (bridge, backup `Saved/Backups/Lvl_01_Slum_before_plywood_20261113_0030.umap`): the covered alley's plywood rooms went from 86 sheets to 16 wall pieces and from 44 studs to 20 (ends only). 164 wall pieces are on the new plywood (S5 16, S6 cells 111, S7 wooden storey 37). The 17 patches in S1-S3 had been swapped too and were put back on their old plywood. Saved twice (00:32, then after the patches), each time with whatever else was unsaved in the open editor. Read back headless. Not looked at in the viewport. **The bake is stale** for the changed walls.
- **Generator:** `_ply_wall(whole=True)` for the alley's plywood building; `building_dressing` unchanged apart from a comment. Arena regenerated: overlaps and dressing clean. `gen_level.py linear_slums` stops on `KeyError: 'open'`: the 2026-11-08 layout data the generator doesn't read yet, so it's not from this change.
- **Studs given timber** (user, of a screenshot: "what are these?", then "Give them timber"): the dark strips were the plywood walls' studs, in the plank texture squeezed onto 10 cm. New `MI_BackAlleys_Timber_World` (AsiaSlum's `T_WoodFrame_A_001`, world-mapped 60 x 250 cm, Wood surface), on all 87 studs (S5 20, S6 53, S7 14). Map saved 01:04 (with whatever else was unsaved); `story_interiors` `TIMBER`. Not looked at in the viewport (a capture needs a camera pose).

---

## 2026-11-13 — Post-death soak threshold
- **User:** "Do an accumulated damage threshold, where if the riddled body does a certain % of the enemy Max Health … then do straight to ragdoll"; "thats on top of what we have, you can still do overkill"; "actually initially 100%".
  - Then: "keep it simple, count the accumulated damage since the dying bullet, if the body keeps taking hits and reaches 100% damage, then straight into ragdoll regardless of what state he is currently in."
- **First build** (riddled hits only, `RiddledRagdollFraction`): compiled, then replaced by the version below.
- **Built** ("apply and build"):
  - `TakeDamage` now adds every hit on a dead, not-yet-ragdoll body to `PostDeathDamage` before the state routing. The killing bullet doesn't count.
  - At `PostDeathDamage` ≥ `PostDeathRagdollFraction` (Health|Death, 1.0) × `MaxHealth`, it calls `StartRagdoll` with all of it, from the death animation or riddled alike.
  - The riddled branch is back as it was. The dying branch no longer adds to the counter itself.
  - Compiled clean in 30 s. The DLL (01:23) is newer than the source. Not yet tested in play.
  - Spec: *Death sequence* → **Post-death soak**.

## 2026-11-12 (3) — Showcase build, back alley
- **User:** "make me showcase deck build, backalley".
  - Ran `Tools/BuildDeck.ps1 -Configuration Shipping`. The only peer session was offline. The back alley was unchanged since its bake (last actor edit 2026-11-07 22:08, `_BuiltData` 2026-11-10 00:18), so no re-bake was needed.
  - **Result:** BUILD SUCCESSFUL in 4 m 32 s, exit 0. 4,801 packages, 0 errors, 20 warnings: the same old resave notices, missing NodeGuids on the knife cue, the smartphone anim and the MCP notice, none new.
  - **Output:** `ProjectBopis_Builds/Showcase/Windows` (3.3 GB; the 237 MB `.pdb` isn't needed to play), game exe 22:16. It overwrites the 2026-11-10 Showcase.
  - It starts on `Lvl_MainMenu`. The cooked maps are unchanged: Sandbox, Linear, `Lvl_BackAlleys_Arena`, the main menu and the menu scene. `Lvl_01_Slum` isn't cooked.
  - **New since the last Showcase:**
    - shoulder swap
    - the trigger finger
    - shots past the character
    - bodies by posts and walls
    - the blood at 0.35 and lit impacts
    - no draw sound from enemy reserves
    - the muzzle flash mesh
    - the doorway aim
  - The editor reopened and holds the bridge port. The user deploys it to the Deck; I didn't run it.

## 2026-11-12 (2) — Impacts lit again, per vertex
- **The cost (user: "I think impact needs to be lit, how much ms are we losing?"):** about 0.3 ms a frame on the Deck for lit as it was before 2026-11-01, 0.5 ms in the heaviest fights: the lighting volume 0.15 ms plus the lit shading, scaled from the 2026-11-01 lit/unlit traces to trace 26. Per-vertex lighting keeps the pixel cost near unlit: about 0.2 ms, estimated.
- **Done (user: "Per-vertex lit"; bridge, saved):** the 16 impact materials in `ImpactsVFXVol1/Materials` are `MSM_DefaultLit` with `TLM_VolumetricPerVertexNonDirectional`, and `Unlit Brightness` 0 so their colour goes through the lighting. `r.TranslucencyLightingVolume=0` is out of `[EffectsQuality@2]` (`DefaultScalability.ini`). `M_ImpactPaper` and `M_ImpactPosterBits` stay unlit. No compile errors in the log. Spec: *Unlit impact effects* → *Lit again, per vertex*.
- **Not yet seen in game or traced on the Deck.** The flecks were dimmed to 0.25 for being bright unlit; lit, they're back to the pack's look.
- **Seen in Play (user):** "keep the impact lit for now"; "smoke is ok actually, blood is bright even on shade" (screenshot: an orange glowing splash on an enemy in a dark room).
- **Blood splash glow off** (user: "go ahead with option 1"; bridge, saved 14:08): the splash material `M_ImpactSplashSubUV` was never in the 16. It's lit and masked, but its Emissive was the particle colour straight, so it glowed in any light. Its texture is a white mask, so all its colour is particle colour. Now Emissive = Base Color input × `Unlit Brightness` (default 0), the same knob as the other 16. Only `NS_ImpactBlood` uses it. No compile errors. Spec: *Lit again, per vertex*.
  - **Then 0.15** (user: "the look black", then "go ahead"; bridge, saved 14:27): with no glow the splash read black in a dim room, so `Unlit Brightness` is now 0.15 of the old glow, under the lighting.
  - **Then 0.35** (user: "still too dark", then "go set it"; bridge). Not yet seen in Play.
- **Bodies through posts and walls** (user, with a screenshot of a body folded round a post: "happens to walls too, I think is the pint where hes in riddle then goes to ragdoll"):
  - **Why:** the dying body's wall check (lines between joints) only fires once a limb is already past the wall, so the ragdoll started astride it. The riddled collapse also launches at up to 900 cm/s, about 15 cm a frame, with no CCD.
  - **Fix:** `IsWallNear`, a 12 cm sphere sweep (`DyingWallMargin`) along the same lines, floors excluded. `SetAllUseCCD(true)` in `UseRagdollCollision`, so only dying bodies get CCD.
  - `BopisCharacterBase.h/.cpp`, applied by Claude ("apply and build"). The first rebuild timed out because the user opened the editor mid-build, and the script never force-closes. The second, after "closed it, run the script", built clean at 15:25. DLL 15:25:40 newer than the source; read back; bridge answers. Not tested yet. Spec: *Dying bodies adrift* → *Caught earlier, and CCD*.
- **Trigger finger tracks the trigger** (user: "can we do something to make the trigger finger track the trigger?", "go ahead with the trigger finger"). Every gun mesh has a trigger bone (the Mossberg's not checked yet). There are four steps: the node, feeding it, sockets on the guns, the AnimGraph.
  - **Step 1 built 15:50:** `FAnimNode_TriggerFinger` and its editor node "Trigger Finger", new files, applied by Claude ("apply and build"). It keeps the incoming L, bisects the middle joint's curl until the pad reaches the target's distance (last joint at 0.15), then swings the finger at the knuckle onto it (cap 40°). Both DLLs 15:50:28, newer than the sources; bridge answers. Nothing uses it yet. Spec: *Trigger finger* → *Tracking the trigger*.
  - **No press** (user, stopping the step 2 build with "hold on": "I dont really need a press anim, I just want the finger on the trigger, the kick will sell the trigger pull already"). Step 2 was revised before building. The press timing is gone, and the press alphas are held at 0 until the AnimGraph's press blend comes out in step 4.
  - **Step 2 built 16:02** (applied by Claude, "apply and build"; the other session offline): `AWeaponBase::TriggerFingerSocketName` / `GetTriggerFingerLocation`. The anim instance gives `TriggerTarget(Left)` in the hand's space and `TriggerTrackAlpha(Left)`. DLL 16:02:25 newer than the sources; read back; bridge answers. In play, the shot press is already gone (the press alpha is 0); the finger rests on the old fixed pose until steps 3-4.
  - **Step 3 placed 16:20** (user: "go ahead, place them after the renders"): `TriggerFinger` sockets on the 8 gun meshes, each on its trigger bone, 0.6 cm in front of the blade's face at the bottom of its curve. Found headless (`sockets_export_ue.py` → `sockets_find_bl.py`, contact sheet sent). Placed through the bridge, read back and saved. The Benelli's and 1911's mesh bones differ from their skeletons' (15 / 0.4 cm), so offsets come from the mesh. The revolver's search was narrowed to 45–85% down its C-shaped trigger. Spec: *Tracking the trigger* step 3 (table).
  - **Step 4 done 16:47** (user: "go ahead"; bridge, compiled, saved; asset backed up first). In `ABP_Player`, the press blend is out (the Rest evaluators feed the finger layers directly), and Local→Component → Trigger Finger → Component→Local sits after `LayeredBoneBlend_18` (right: `hand_r`, `index_0x_r`, `TriggerTarget`/`TriggerTrackAlpha`) and after `_19` (left, the duals). StraightStock is mapped to the Rest pose (the Mossberg). No errors in the log. **Not yet seen in Play.**
  - **Step 5 built 16:53** (applied by Claude, "apply and build"; the other session offline): the press leftovers are out of the C++ (`TriggerPressAlpha`/`Left`, `TriggerPressPose`, `FTriggerFingerPoses::Press`). DLL 16:53:30 newer than the header; read back; bridge answers.
  - **Curled fingers (the user: "fingers look curled", a pistol in Play).**
    - Checked offline: `check_export_ue.py` (grip offsets for every gun) and `check_solve_bl.py` (the node's maths in Blender, every gun, rendered sheets in `Saved/TriggerSockets/check/`).
    - Two faults. The curl axis came from the incoming bend, and the Rest finger is straight, so the finger curled any which way, up over the slide. And the pistols' triggers sit 4.2–5.9 cm from the knuckle, too close for the pad, so it hooked up and over.
    - The fix: curl about the finger's own flexion axis (bone −Z, both hands), and cap the curl at 50°. A closer trigger rests further back along the finger, with the rest wrapping round it. Checked on all 11 Blueprints.
    - Then the user: "try using the 2nd bone on the trigger". The trigger rests halfway along `index_02`, and the tip wraps 40°. A far trigger (M4, pump, Beretta, AK) slides the contact out along the straight finger. Checked offline on all 11; halfway curls less than 80%.
    - **Built 20:18** (applied by Claude, "apply and build"; the peer session offline). DLL newer than the sources, files read back, bridge answers. The nodes picked up the new defaults on load.
    - User: "too far in, something in between maybe". Contact Along set to 0.75 on both nodes through the bridge ("go set it in the bridge"), then compiled and saved at 21:35. 1.0 was tried offline and curls too much.
    - **Accepted** (user: "keep this fir now, make all tests ok. I'll bring it up again if its broken"). Spec: *Trigger finger* step 7.
  - **Step 6 done 18:44** (the user: "ok go"): `ABP_Player` re-saved, and its file no longer names `TriggerPressPose`. Both grips keep the Rest clip. The `TriggerPressPose` clip is deleted (git shows it as `D`). It took a real change, reverted, to dirty the package: `save_assets` skips clean packages, and re-setting the same value doesn't dirty them.
- **All of today's Play tests accepted** (user: "keep this fir now, make all tests ok. I'll bring it up again if its broken"): door nav links, the enemy draw sound, shots past the character, the blood splash at 0.35, bodies by posts and walls, and the trigger finger. They were accepted together, not tested one by one; the user will raise any that break. Each resume item keeps what to look for.

- **Too quick (user: "I'm concerned that the level can be completed pretty quickly"; the eskinita "takes 10 secons to cross").** Measured on the paper layout: the whole route was ~280 m, under a minute at run speed (5 m/s). The layout's 34-48 minutes were my hand guesses at what each section would hold, and ran about three times long. The user's target was 30-45 minutes (spec *Linear levels*).
- **The way back (user: "how about we just do the whole map in reverse? it ends back at the yard gate where you need to meet up with arriving cops, also work narratively becuase the cop's body is there"; "Yes add it"):** in `Tools/LevelGen/layout_linear_slums.mjs`, regenerated. After the documents (I8), sections 7 to 3 in reverse with F13-F17 (22 gunmen), each taking a room from the side you left it by: the hall from the gallery, the guard room from the cells, the bodega from its back door, up H4's back stair into a held floor, the yard from H1's back door. They're armed by I8; CP9-CP13; the end is I9 at the yard gate, where the cops arrive down the lane. No geometry changed: areas, openings, stairs, cover, mass and sightlines are identical to the 2026-11-08 JSON.
- **Minutes now from a model:** the route as waypoints through the doors (`ROUTE_IN`/`ROUTE_BACK`: 340 m in, 224 m back), walked at 2.5 m/s, plus 12-20 s a gunman and 15-45 s an inspect. That gives about 20-35 min (in 14-25, back 6-10), 17 fights, 71 gunmen, 9 inspects (3 needed), 13 checkpoints.
- **Canon:** lore scenario beat 9 (the way back, the cops at the yard gate, the patrolman's body in the yard); open: where the body is and when it's found, who comes on the way back, what happens with the cops. The GDD's first case gets one line.
- **New rules (`Claude-Rules.md` §8):** *Loops*. Look for a mid room revisited from another entrance; reverse runs only where every fight gets a new angle. *Paper layouts*: gunmen and pickups are rough guides, and the geometry is followed.
- **Enemy draw sound** (encounter reserves heard drawing their guns on waking): the one-line `ShouldSkipEquipAnimation` override went into `EnemyBase.h` here; the rest (compile, read-back, docs) was handed to the "Current Coding Work" session.
  - **Built 01:00** (user: "run the script"; the other sessions idle or offline). DLL 01:00:51 newer than the header; read back unchanged. Side effect: a woken enemy can shoot once its reaction time is up, with no draw first. Not tested yet. Spec: *Encounter reserves* → *No draw on waking*.
- **Door nav checked:** the user ran Build Paths and saved `Lvl_01_Slum` (00:57). `check_door_nav_ue.py` found all 6 doors OK, with full paths of 240–246 cm and none partial (before the fix, all 6 stopped in the doorway). Not yet seen in Play.
- **Bridge down after that rebuild:** I ran the headless door check while the editor was still loading. The headless instance started its own MCP server on port 8000 first (01:01:23), so the editor's failed at 01:01:31 ("unable to bind") and stayed down. Fix: `ModelContextProtocol.StartServer` in the editor console. From now on, no headless run until the editor's bridge answers after a rebuild.
- **Shots into the leaf behind** (user, aiming in a doorway with the camera past the open leaf: "from this position, the bullet goes to the wood behind me"). The shots' crosshair trace started at the camera, so it hit the leaf by the lens. The leaf ignores the camera channel, so the boom swings through it. Now it starts level with the character, as the pose's aim point has since 2026-11-11, and `MinConvergenceDistance` is 50 cm past the muzzle (was 200 cm from the camera, which never came into play at hip). `WeaponHolderComponent.h/.cpp`, applied by Claude ("apply and build"). Built 02:21 (the other session idle); DLL 02:21:39 newer than the source; read back; bridge answers. Not tested yet. Spec: *Trace source — two-stage*.

---

## 2026-11-11 — Gun scales, trigger finger parked, arm twist, Gun Upright
- **Trigger finger:** reshaped to an L and pushed deeper on the user's notes, then **parked** ("leave the trigger finger for now"): with the M4 at 1.33 the L finger can't reach its trigger. The Blender setup now includes the gun's component scale. The duals' left finger layer moved after the left-arm layers (it did nothing before them); built 01:48, wired, saved.
- **Gun scales:** M4 1.33 (grip offset (1.64, 1.47, −2.42)), the .45 1.1 and the dual machine pistol matched by the user ("it looks ok without any adjustments"). Pickups and drops now copy the weapon mesh's scale (built 01:41). AK left hand: user says it's OK; my proposal not applied.
- **One-handed pistol aimed high** (user: "the right hand twists the higher you point, also, the twist messes up the shoulder here"): `FAnimNode_UpperArmTwist`, built 13:45; Upper Arm Twist on both arms and Forearm Twist on the right placed (bridge, saved). User: "still an issue". Measured: the aim poses roll the gun itself up to +14.6° aimed up. `FAnimNode_GunUpright` rolls the hand back about the barrel; applied by Claude ("apply and build"), built 14:07, placed before `hand_r` → `ik_hand_gun` (bridge, compiled, saved). Its angle took the half-turn for an upright gun; caught on review before any test, fixed ("apply and build"), rebuilt 15:13 (no busy peers); DLL 15:13:07 newer than the source; bridge answers. Tested (user): "looks good". Spec: *Gun Upright*.
- **Muzzle flash looks flat** (user: "the muzzle flash looks flat, like a billboard ... They looks worse especially in Focus slo mo"). Read headless (T3D export, no bridge): each pack flash is one barrel-aligned card (`Flash Core`, `PSA_Velocity`, a random frame of a 4×1 or 2×1 soft fireball texture, held for 0.05–0.08 s), plus a camera-facing smoke-tinted card (`FlashCore Smoke`, `PSA_Rectangle`) and smoke; the shotgun adds streaks, sparks and a core. Nothing animates over the flash's life, so at Focus's 0.3 it hangs as a still card for ~0.2-0.27 s (12-16 frames at 60 fps). Options given to the user (build a mesh flash, or buy a Niagara pack). **Requirement (user): "I need it so that It doesnt look awful in slo mo".** Recommended: build, animated across its whole life (see the RESUME item).
  - **Built (user: "build it"):** `Tools/FX/MuzzleFlash/` (`design.py` the look; `bl_mesh.py` Blender mesh; `make_ue.py` headless material + import; `verify_ue.py`; `preview.py` numpy preview, sent). Assets `/Game/ThirdPerson/FX/MuzzleFlash/{SM_,M_,MI_}MuzzleFlash`: 3 crossed side cards + a front card (8 tris) that each fade edge-on; additive unlit, 277 PS instructions; Age/Seed/Petals/Brightness as custom primitive data.
  - **Code** ("apply and build", applied by Claude): new `UMuzzleFlashComponent` (+ `FMuzzleFlashSettings`), two per gun (main and off-hand), on the muzzle socket at BeginPlay; `AWeaponBase` gains `FlashMesh`, `FlashSettings`, `FlashEmitterNames` (the pack's flame emitters, off while `FlashMesh` is set; includes `Pop`), and the muzzle light now fades with the square of its time left. **Built clean 18:08** (peers idle/offline); DLL 18:08:40 newer than the source; bridge answers. Nothing changes until a Blueprint sets `FlashMesh`.
  - **Blueprints** (user: "go ahead", one batched bridge script): `FlashMesh` = `SM_MuzzleFlash` on `BP_Pistol45`, `BP_Pistol45_EnemyOnly`, `BP_Pistol9mm`, `BP_DualPistol45`, `BP_DualPistol9mm`, `BP_MachinePistol`, `BP_DualMachinePistol`, `BP_AssaultRifle`; the M4's `FlashSettings` Length 34–46, Width 20–26 (the rest keep 18–26 / 11–15). Compiled, saved, read back; no log errors. Muzzle sockets: `muzzle_socket` (.45s), `MuzzleFlash` (the rest). Next: the user's PIE test incl. Focus; AK, revolver, shotgun after.
  - **Round base for pistols, star for rifles** (user: "I would prefer a circular looking base than the spiky leaf", then "the rifles can retain the spiky star actually"). New material scalar `Spikes` (0 round, 1 the first version's star and plain petals): front card a ragged disc of radius `BALL` (0.42 of the width), side cards get a ball on the muzzle (round at `LENGTH_PER_WIDTH` 1.7). `MI_MuzzleFlash` Spikes 0 on `SM_MuzzleFlash` (pistols); new `MI_MuzzleFlash_Star` Spikes 1 on new `SM_MuzzleFlash_Star` (same cards); `BP_AssaultRifle` now uses the star mesh (`set_guns_ue.py`). Preview `preview.py compare` (sent). Built headless with the editor closed (user: "go ahead"; peers offline): 283 PS instructions, no shader errors; `verify_ue.py` read back the Spikes values, the meshes' instances and both guns' meshes and sizes. No C++.
  - **The rest of the guns** (user: "go all the way to 7"; one batched bridge script, saved and read back, no log errors): `BP_AssaultCarbine` star 38–50 × 24–30; `BP_Revolver` round 26–34 × 16–21; `BP_PumpShotgun` and `BP_AutoShotgun` round 45–60 × 32–40, 0.07 s (the pack's `Core` and `Pop` off by the default list; streaks, sparks, embers and smoke stay). Left out: the sniper (its pack flash has `Flash Left`/`Flash Right` brake blasts and `FlashCoreSmoke` without a space, so it needs its own list) and the grenade launcher. Spec: new *Muzzle flash mesh* section (the old *Muzzle flash* section points to it); *One-handed pistol* gained *The aim point*.
- **Gun swings up in doorways** (user's screenshot, "happens on doors when aiming", "happens even when the door is open"): the pose aim (blade arm/hand, dive correction) pointed at the crosshair's raw hit, and in a doorway that's the jamb right beside the shoulder (the camera sits 65 cm right), so the arm swung to its 60° + 45° limits. The shot was fine (its own `MinConvergenceDistance`). New `GetCrosshairAimPoint` in the anim instance, shared by `UpdateBlade` and `UpdateShootdodgeAimCorrection`: the trace starts level with the character, and the point is held at least `AimMinReach` (150 cm) past it. Applied by Claude ("apply and build"); the first build failed on C4458 (a local `Direction` shadowed the anim instance's member), renamed `ViewDirection`, then **built clean 19:30**; DLL 19:30:19 newer than the source; bridge answers. Tested (user, with the flashes): "tested, all good".
- **Test starts** (user: "I need a way to place multiple player starts so I can test each section", "and switch where I want to spawn"): `AProjectBopisGameMode::ChoosePlayerStart_Implementation` picks Play From Here, else the start whose Player Start Tag matches `Bopis.StartAt`, else the untagged start (several starts would otherwise be a random pick); console `StartAt S3` / `StartAt off` sets it and reloads through `ULevelTravelSubsystem`. Applied by Claude ("apply and build"); before building, a local `Tags` was renamed `StartTags` (it would have shadowed `AActor::Tags`, the same C4458 as above). **Built clean 20:22** (peer offline); DLL 20:22:22 newer than the source; bridge answers. The starts themselves are the user's to place (handcrafted map). Spec: *Test starts*. User: "thats good now".
- **Enemies can't get through doors** (user: "The nav does not go thru doors it seems. So When I spawn from enemies in the room to rush me outside, they cant get out"). Headless, read-only on `Lvl_01_Slum`: the level's navmesh has `AgentRadius` 35 (19 cm cells, so 38 cm off each jamb), and all 6 swing doors (S4, leaf 103.8) had navmesh on both sides but paths stopping in the doorway (partial, 53–90 cm). Fix: `ASwingDoor` gets a `NavLink` (`UNavLinkComponent`, both ways, ±75 cm on the floor). Applied by Claude ("apply and build"); **built clean 21:24** (peer offline); DLL 21:24:36 newer than the source; bridge answers. Next: the user runs Build Paths in `Lvl_01_Slum` and saves; then I re-run `Tools/LevelGen/analysis/check_door_nav_ue.py` (expect full ~240 cm paths). Spec: *Swinging doors* → *Nav link*.

---

## 2026-11-10 — Showcase build (Shipping)
- **User:** "I want to show the game to someone, I want a build with no debug messages. Starting from the main menu". `Tools/BuildDeck.ps1` takes `-Configuration Shipping` now (to `ProjectBopis_Builds/Showcase`, log `BuildShowcase.log`; plain runs still Development to `DeckTest`, log `BuildDeckTest.log`). Shipping strips on-screen debug messages, map warnings, Print String, debug draws and the console. Spec: *Deck test builds*.
- **Lighting:** the user asked whether the bake applied to the back alley. Yes: `Lvl_BackAlleys_Arena` baked (14:20 min, done 00:13) and its `_BuiltData` saved 00:18 on 2026-11-10, after its last actor edit (2026-11-07 22:08); `Lvl_MenuScene_BackAlley` baked 23:48 on 2026-11-09.
- **First Shipping cook failed** (exit 25): the CC AnimBP couldn't load at startup because `AInspectPoint`'s constructor loaded `BP_Player_Cutscene` before the IK Rig plugin. Fix presented and applied ("apply and build"): `DoubleClass` a `TSoftClassPtr`, loaded at `BeginPlay`. Rerun: **BUILD SUCCESSFUL**, cook 0 errors (20 warnings, none IK Rig), 00:30; `ProjectBopis_Builds/Showcase/Windows`, 3.3 GB (the 237 MB `.pdb` is debug symbols, not needed to play). Editor reopened. The user deploys it to the Deck; not run by me. Spec: *Deck test builds* (gotcha).
- **The Options page** is in both menus (the user pasted and edited them 2026-11-09 14:08-14:21).
- **Shoulder swap** (user: "We are adding shoulder switch", then "apply and build"): `ShoulderSwapAction` toggles `bLeftShoulder`, which mirrors the camera's sideways offset in every framing; camera only, the gun stays in the right hand. Applied by Claude; built clean 21:20 (no busy peers); DLL 21:20:27 newer than the source; one editor; bridge answers. `IA_ShoulderSwap` (copy of `IA_Interact`) made and set on `BP_PlayerCharacter` and `BP_Player_CC`, read back, saved. The user maps it in `IMC_Default` and tests. Not in the Showcase build. Spec: *Camera*.
  - **Debugging:** first mapped to `H`, which `IA_Heal` already had (and consumed). Moved to V and D-pad Down: the action triggered (`showdebug enhancedinput`) but the camera didn't move. Three diagnostic `UE_LOG`s added (applied by Claude, "apply and build", built 22:02); after that restart it bound and toggled once per press. User: "it works now". Likely cause: the Blueprint defaults set through the bridge didn't reach Play until the editor reloaded them. The logs came out with the next build (22:33).
- **Left-wrist pinch** (user, from the left shoulder: "the left wrist does a overtwist"; "this only happens when aiming with 2 hand weapons"): the locked hand angle (calibrated on the lowered idle/jog) against the aiming pose's forearm roll, with the twist bones left at the clip's roll. New `FAnimNode_ForearmTwist` (runtime) and `UAnimGraphNode_ForearmTwist` (editor module) spread the roll along `lowerarm_twist_01_l`/`_02_l`. Applied by Claude, "apply and build"; built clean 22:33 (no busy peers); both DLLs newer than the source; one editor; bridge answers. The user adds the node in `ABP_Player`. Spec: *Per-gun hand angle* → *Forearm Twist*.

---

## 2026-11-09 — Sensitivity settings, step 1; metal smoke; inspects parked
- **Inspects parked** (user: "park the cutscene bit for now. I actually want to test the level for playability first and foremost"). 2a and the pre-built double tested: "looks good so far", "he HAS hair". The glance isn't confirmed.
- **Impact size** (user: "did we at any point decide we wanted to make the impacts bigger", "the smoke is absurdly large when hitting metal", "check in code if we are doing something as well"): yes, 2026-10-09's exaggeration pass (1.5×), back to 1.0 on 2026-11-01 for the Deck. Code and data (read headless) scale a burst only by surface `Scale` × `EffectScale`, both 1.0 for Metal, no extra layers. The size is the pack's `MetalSmoke` (125 cm); the fix is the concrete one (Uniform Curve Scale 0.25, or 0.15 to match), and `WoodSmoke` / `GlassSmoke` are 125 too. The user's to do in the editor. Blood's Scale reads 0.25 (spec said 0.5; fixed).
- **`Lvl_01_Slum` for a play test:** it has a player start, a navmesh, the 6 swing doors and the inspect point; no enemies, director or checkpoints yet.
- **Sensitivity** (user: "Lets put Mouse and Controller Sensitivity Settings on the Pause and Main Menu"): step 1, `UBopisGameUserSettings` (saved in GameUserSettings.ini), mouse look and stick turning scaled by it. Applied by Claude, "apply and build"; built clean 13:27 (all peers idle); DLL 13:27:47 newer than the source; one editor; bridge answers; no class-load errors in the log. Step 2 (user: "shared options page", then "apply and build"): `UMenuItemWidget` (new base, the button's shared parts moved into it), `USettingSliderWidget`, and `UMenuWidget` walking into a page that is its own widget. Applied by Claude; built clean 13:58 (all peers idle); DLL 13:58:52 newer than the source; one editor; bridge answers. Not tested in Play: the button code moved, so the user re-checks both menus. Step 3 (user: "go ahead"): `WBP_SettingSlider` and `WBP_OptionsPage` made and saved through the bridge (two creates, one save; parents checked on disk); their trees added to `Tools/MakeMenuTrees.ps1`, the slider's on the clipboard. The user pastes them and adds the page to both menus by hand. Spec: *Player settings*.

---

## 2026-11-08 — Linear slum layout: doors and steps for the drops
- **User:** "can we revise the map paper layout? We have doors now. The use of one way drops in the current level, I do not like."; "only those bits"; "try not to resize the buildings when looking for a solution". Plan item 50.
- **Changed in `layout_linear_slums.mjs`** (nothing else moved, no building resized):
  - **2→3:** a 1.1 m door in the yard wall at the eskinita's +1.8, a railed landing, and steps down into the yard. The car is in view from the landing.
  - **H4:** the floor hole is now a stair with a half landing in the back room, with its foot at the back door (4→5). F4's third gunman holds the stair head; CP4 is just outside the door.
  - **5→6:** the bodega's back door, then steps down through the passage into the guard room. CP6 is at their foot.
- **Streaming both ways:** a border door holds until the section behind it is loaded, unloading waits a few metres past the door, and a section keeps what's done. Spec *Linear levels*.
- **Measured:** the longest fight sightline is 24.8 m (it was 25.3); the street's is 25.8.
- **Not in the map:** `Lvl_01_Slum` is handcrafted and was not touched.
- **Not in the generator:** it doesn't read the new layout data yet (`open`, `z0`, landings, wall barriers).

---

## 2026-11-09 — `Lvl_01_Slum` sections 1-2: dressing, unaligned houses, a real street
- **User:** "first do passes on Sections 1 and 2. Dressings, also makes sure that each house is unaligned with the adjacent house. Also we need a curb and actual street. Look at the net for references of PH streets"; of the map: "the only edit was the wall drop, your placement keeps blocking the drop so I cant proceed and you also added a wall at the entrance of the eskinita and I can't go through". Later: "cap the curb edge".
- **References:** Pinterest thumbnails of Manila streets (Google Images asked for a CAPTCHA, left alone): concrete roads in poured panels, raised sidewalks with curbs, poles at the curb, eskinitas with a side drain.
- **Generator** (LESSONS, *Sections 1-2 dressed*): the arena's building and street dressing, posters, wires, poles and graffiti on the slum's houses; every slum front stepped 30 cm or more off its neighbours' (0 of 30 fronts in line), storey heights 20 cm apart; a concrete road in panels, a 1.1 m sidewalk 15 cm up with capped curb stones, eskinita drains. The blockers: no parapet across the E1 mouth, the garage roof ends short of the drop, the sidewalk stops at an alley mouth's corners. The dressing passes' arena-only assumptions became level settings; `check_dressing` takes the level's frame. Both checks clean on both levels; the arena's plan still identical (52 of 52, and its printout).
- **Into the map:** headless with the editor closed, `swap_sections_ue.py` (new; `ue_place.py` is the shared placer): sections 1-2, every slum house wherever it went (4 face the yard and sit in section 3), the compound houses touching them, the garage roof, and loose pieces near the seam matched by shape. 4,966 pieces placed, 0 failed; only S1/S2/S3 `_Art` saved. A dry run first showed nothing of the user's in S1/S2. A box curb cap went in afterwards (`SWAP_ONLY=Curb`); the user: "its too sharp edged, you should be using the main border stone", so the curb is now 84 Favela `SM_MainBorder_04` stones (1 cm joints, 3 cm proud), seen in a capture.
- **One map** (user: "I would rather not have them as sublevels at this point if you have to add them headless everytime", "only if we can still do Sections 1-7 split even without sublevles"). Tested twice: the bridge places only into the persistent level, even with a sublevel current. `flatten_sections_ue.py` (headless) made all 9,897 sublevel actors again in the persistent map, checked each against its original (0 differences), tagged each with its section `S1`-`S7`, and took the 14 sublevels out of the map; their files in `Content/ThirdPerson/01_Slum/` stay as a pre-merge copy. The stones then went in through the bridge.
- **Fill lights** (user: "rule on directional lights, always put a point light that is shadowless, like ambient light around the source", "bonus if you can have it cast shadow but very very mild"): every spot light gets a point light under its head (12% intensity, half the reach, a 40 cm source: very soft, faint shadows). In the generator (`street.py` `FILL_*`), and the 7 lamps in the map got theirs through the bridge. Standing rule in `Claude-Rules.md` §8.
- **AsiaSlum cables** (user: "dont eliminate using the current ones, I just think those fit better in some instances", "go and build it"): `passes/asia_cables.py` hangs the pack's cable bundles on ring brackets along a few top storeys, one across the main street, and trunks pole to pole, with the thin wires all kept. Few fit: brackets can't go on hollow-block faces and the top storeys are busy. Corner pieces don't fit a 90-degree corner; drops found no clear path. `check_dressing` tests them. Arena plan still identical. Placed in the map through the bridge (14 pieces, saved); captures 13 and 14 in `Saved/LinearSlums/captures/`.
- **Main road clearance** (user: "section 1 is a main road, it needs the power cables a bit higher. Trucks should be able to pass through"): nothing under 5 m over the main road now (`passes/story_road_clear.py`, `ROAD_CLEAR`). Of 27 low bundles, 1 lifted up its walls; 26 removed (they end on 1-storey fronts with no wall to climb); 1 extra span added one storey up, where the walls had room. The eskinitas keep the low layer. A wire is no longer cut rod by rod at a section's edge. Synced into the map through the bridge; checks clean, arena identical. Standing rule in `Claude-Rules.md` §8.
- **Light colours fixed** (user: "your point lights are the wrong color"): every light the headless placer made was white (it used a run-time colour call that Static lights ignore); only the bridge-placed fills had their colour. All 90 lights in `Lvl_01_Slum` set to their planned colours and saved; `ue_place.py` now sets the colour property, tested headless.
- **Generator sped up** (user: "optimize our generator tools if we can"): the slum generates in 4.9 s (was 25.0), the arena in 2.8 s (was 9.5), both plans byte-identical and every check clean. Spatial indexes in place of full scans, found by profiling (LESSONS, *Faster generator*).
- **Even light** (user: "need to add more lights to Section 1 and 2, light are unevenly distributed"): new pass `passes/story_light_fill.py` (`LIGHT_FILL`) measures the open ground on a 1 m grid and adds, one at a time, the fitting that lights the most dark ground, under the street pass's rules. 8 wall lamps (with fills) and 3 tubes, 33 pieces: lit share 51% to 89% (maps: `Saved/LinearSlums/captures/16_light_cover_before.png`, `17_light_cover_after.png`). Still dim: the wash yard's north-west corner and an eskinita corner (hollow-block and stair walls take no fittings). The pass only adds; checks clean, arena identical. **In the map:** all 33 placed through the bridge (by label, from `Saved/LinearSlums/light_fill_place.json`), tagged S1/S2, colours, intensity and Static read back, saved. Not yet looked at in the editor or baked.
- **Section 4 baseline** (user: "the doorways are two doors wide, I need it only 1 door wide except for the broken down wall", "sils or door frames ... we should be using what assets we have instead", the jalousies on both sides, stairs to "conform" to theirs, doors that swing "both ways, whichever side anyone is pushing through"): `story_interiors` for `FITTED` buildings (the row houses). 6 doors one leaf wide (110 x 218) in Favela's wooden jamb; 9 windows in Favela's wooden window (outside sill, inside board) around the two jalousie planes; the stair rebuilt the user's way (read from their `TRAP_Stair3` edit in the map: steep flights, each a step down the last, from the top). Only row-house pieces change (16 new, 2 gone, 69 moved); overlaps and dressing checks clean. The jalousies already had an inside twin in the map (all 9). **Swapped into the map** (user: "Swap them in"), through the bridge by label: pieces the user had changed were skipped (the 4 ground-floor grilles, now their AsiaSlum security cages), windows kept where they were (the first try moved one off its cage; fixed), the frames' sills 1 cm proud so they clear the cages. Saved. `ASwingDoor` C++ presented for the user to type. **Knocked-through walls** (user: rubble "around the door frame", "Yes, dress them"): broken plaster down both sides and over the top of the 3 holes, both faces (Favela's broken-corner mesh decal), a debris heap each side (AsiaSlum); 24 pieces, checks clean; placed through the bridge and saved (surfaces and sizes read back). Capture `Saved/LinearSlums/captures/18_knock_ground_floor.png`. Then (user: "make it white not red"): `MI_BackAlleys_CornerDecal_White` (Favela's white wall texture as the decal's colour) on all 18, capture `19_knock_white.png`. Top corners filled (user: "there a way to fix the top corners?"): the top strip runs on past each side as far as the side strips' plaster shows; 6 strips moved and saved. A capture after it came out with the walls hidden in the user's viewport (the walls are in the map), so not shown. **Then (user, with screenshots):** street lamps in balconies (the light fill's lamps over balcony blocks; all lamps removed and re-placed by the strict rule, plus lamps on the power poles; new check), inside walls showing on the outside (stopped at the outside wall's inner face) and a 1 cm wall sliver flickering through the upstairs floor under the knocked-through walls (removed). Row houses and lights synced and saved; the same two wall bugs then fixed in the map for the plywood rooms, the holding house and the trap house too (user: "Yes, apply them"): 26 pieces out, 180 moved, 1 in, none of them user-edited; saved. Then the recess where an upstairs floor meets a wall round a void (user: "the issue is that caved in bit on the wall", "messed up UVs on one side"): walls under a void edge rise through the slab, void slab edges faced in the wall render; in the generator, checks clean; synced once the user reopened `Lvl_01_Slum` after another session's rebuild: 11 walls raised, 20 facings, none user-edited; saved. Capture `22_stairwell_edge.png`. **Ground and objects** (user: "For S1 and S2, Do a ground and object pass (garbage cans, buckets etc)"): the arena's dirt, litter and props passes on the slum through `story_ground_dress` (open ground and surface heights), plus garbage drums (`PROP_DRUMS`); 268 pieces, checks clean, arena identical. **In the map** (the user reopened `Lvl_01_Slum`): all 268 placed by label with place_plan_ue's physics and weld handling (16 lids and plants welded), saved. Then the drums: 6 of 8 had been dropped as touching something (square bounds turned at random into the house linings, a curb's end, a grille), so they now turn square to the wall, need flat ground and plain walls; 6 placed by the pass. In the map: the old drum out, one moved, then the last three once the user left PIE: all 6 drums in, saved. Capture `23_ground_objects.png`. Not walked or shot at in PIE by me. Then: drums solid (`BlockAll`, on the nav mesh; map saved); E3's hollow-block yard wall along its whole north edge with a concrete cap (`PARAPET_FULL`; the cap in two layers so its sides don't streak; in the map and saved, capture `24_e3_wall.png`); the compound walls' caps in two layers too (10 caps moved onto 10 new bodies, none user-edited) and Plastic's impact sound to the Wood light hits in `DA_ImpactEffects` (user's asks): both applied and saved; the chairs' "glass" not found in the data (all Plastic, SurfaceType18; the impact table plays plastic VFX and light-metal clinks): asked the user what they saw. **Doorways fixed** (user: "I cant get thru the single doorway", "it blocks bullets too"): the jamb mesh's collision was one box over the whole doorway; it now collides with its own triangles (posts and head only). Not yet walked or shot through by the user; rebuild paths if the AI won't use the doors. **Swinging doors** (user: "Apply and build", a one-time permission: Claude wrote `Source/ProjectBopis/Gameplay/SwingDoor.h/.cpp` exactly as presented and rebuilt; "Result: Succeeded", DLL newer than the source, bridge answered): `BP_SwingDoor` (leaf Favela `SM_Door_01`). The jambs measured in the map: 105.8 cm clear, 215.7 cm to the head, all six alike, so the leaves are 103.8 x 213.7. 6 doors placed (`Slums/Interiors`, tag S4) and saved, the three right-hinged ones turned round so the handle stays on the free edge; capture `25_swingdoor.png`. Not yet walked through in PIE; no sounds set. **One per door type** (user: "I need multiple variants of swing doors, I would even go and make one for every door type we have"): 14 children of `BP_SwingDoor` in `/Game/ThirdPerson/Blueprints/SwingDoors/`: Favela blue, green and metal; Yakohama `SM_Door_01`, `SM_Door_02`, `SM_GlassDoor_02`; AsiaSlum `SM_HouseDoor_A_001`-`A_005` and `B_001`-`B_003`. Nine had the handle on the hinge edge, and the two MiddleEast doors are modelled along Y: `LeafQuarterTurns` added to `ASwingDoor` (user: "Apply and build" again, one-time: Claude wrote it as presented; "Result: Succeeded", DLL newer than the source, bridge answered), set to 2 on the nine, checked with test doors high over the arena (capture `26_swingdoor_variants.png`: handles on the free edge), test doors removed. The MiddleEast variants dropped (user: "forget the middle eastern variants actually"). The six placed doors (0 turns) are unchanged.
- **Not done:** the street lights carry the arena's values (bulb 4.5, tube 6, lamp 40 cd), unjudged at night; no ground dirt, litter or props here yet; not baked.

---

## 2026-11-08 — Generator split (levels as data); `Lvl_01_Slum` built
- **User:** "generator splits first, start a new session and try to build the map already, with what assets we currently have"; "LevelName is 01_Slum" (asked: `Lvl_01_Slum`). Plan item 50.
- **The split:** `Tools/LevelGen/gen_level.py` is a driver over `kit/core.py` (stateless), `passes/*.py` (the arena code, cut out unchanged, plus hooks) and `levels/*.py` (per-level data). `Lvl_BackAlleys_Arena`'s plan is byte-identical, plan and printout, checked after every change (`analysis/plan_identical.py`, 52 of 52 files). The arena wasn't re-placed.
- **New level:** `levels/linear_slums.py` + the `story_*` passes. Street houses come from the layout's mass through the arena's house passes; buildings you enter get rooms, the layout's openings, windows, slabs, stairwells, the H4 floor hole, stairs, rails, the mezzanine, the terrace and plank, metal roofs and night bulbs. Ground at its heights, the eskinita steps, the broken yard wall, the two lane gates, the garage roof. 8,495 pieces in 7 sections. `check_overlaps` and `check_dressing` clean on both levels (the checks now take a level name).
- **Built headless** (`Tools/LevelGen/build_story_ue.py`): `/Game/ThirdPerson/Lvl_01_Slum` (not World Partition) and `Lvl_01_Slum_S1..7_Art` / `_Gameplay` in `/Game/ThirdPerson/01_Slum/`, each piece in its section's `_Art`. The first run placed only lights and decals (`spawn_actor_from_object` returns None headless); fixed, rebuilt.
- **Night base** in the persistent map (`story_night_ue.py`): a Stationary moon (0.35 lux), a Stationary sky light (0.6) with a sky atmosphere, thin blue fog. Starting values, unbaked.
- **Seen in the editor** (user opened the map): captures in `Saved/LinearSlums/captures/` (main street, yard, courtyard, hall). Fixed after the first look and patched into the open map through the bridge: slab and ceiling streaks (now the pours' material), bulbs hanging from a missing ceiling under the hall. Saved. Not walked in PIE, nav not built, not baked.
- **User's first walk-through:** "some bits are blocked. Stairs are awful and the interiors are too tall", Section 1's 3-storey houses "unusually high", "look at Demomap_AsiaSlum ... The way you use the blocks for stair rails is absurd, remove immediately", sections 3-7 are "a single compound", "you are also using the wrong hollowblock material". Done: block balustrades removed from the map (82, saved) and the generator; kit stairs and rails as the demo; 3.5 m storeys; no third storeys facing the main street; plain compound houses; `MI_BackAlleys_HollowBlocks_World` (new, headless) on box walls. Checks clean, arena still identical. **Rebuilt** after the user closed the map (7,729 pieces, 0 failed, night re-added). The user then moved the row house's stair flights by hand: my flights were placed going uphill from the top end, in all four stairs. Fixed in the generator and all 12 flights set from the plan through the bridge, saved; seen right in a capture. The blocked spots weren't named yet.
- **Compound walls** (user, with screenshots of the yard and the alley to the bodega: "The yard should just be 1 storey walls around it, push these buildings back so they look like distant buildings"): a one-storey hollow-block wall round each open area of sections 3-7, 6 m of walled-off ground behind it, the buildings beyond. In the generator, checks clean, arena identical. **Rebuilt** (8,201 pieces, 0 failed, night re-added); captures of the yard and the alley to the bodega in `Saved/LinearSlums/captures/` (08-10) show the walls with the buildings set back.
- **Handcrafting from here** (user, end of day: "I think this is something beyond automated generation. I have to handcraft some of these. I'll start tomorrow"). The generator's map is the starting blockout. From now on `Lvl_01_Slum` is never rebuilt or re-placed from the generator without the user's say (`Claude-Rules.md` §8).
- **Docs:** LESSONS *Levels as data, and the first story level* and *The user's first walk-through*; README; spec *Linear levels → Built*; design notes (one compound); plan item 50.

---

## 2026-10-24/26 — Weapon wheel, impact sounds, female CC, LFS, music, level exit, waves, CC skin, dual reload, final weapons (fire anims, hands, mag drops)
- **User:** "This UI, I cant design it?" — it was drawn in code
  (`NativePaint`), so a Blueprint child showed an empty canvas. Now
  `UWeaponWheelWidget` keeps the logic (segments, key/pointer modes,
  cycling, hit-test) and drives **named widgets** in `WBP_WeaponWheel`:
  `Segment_0..5` tinted by state, `Icon_0..5` (brush + size at the icon's
  own ratio), `Count_0..5`, `NameText`, `AmmoText`; extras for Blueprint:
  `GetSegmentState`, `GetHoveredIndex`, `GetSegmentAngleDegrees`,
  `OnHoverChanged`. `NativePaint`, the fonts, `RingThickness`,
  `SegmentGapDegrees` and `SegmentImage` are gone. Applied by Claude ("apply
  and run"); built clean, bridge up, DLL newer than source.
- **Assets:** `/Game/UI/T_WheelSegment` (generated 56° ring wedge, UI
  compression, no mips); `/Game/UI/WBP_WeaponWheel` (parent
  `WeaponWheelWidget`) set as `WeaponWheelClass` on `BP_PlayerCharacter`
  (`BP_Player_CC` inherits). The bridge can't build widget trees and
  `BlueprintTools.create` takes the **parent class** as `asset_type` (passing
  `WidgetBlueprint` fails) — so the tree was generated as UMG clipboard text,
  `Tools/WBP_WeaponWheel_Tree.txt`, to paste into the empty Hierarchy.
  Spec: *Weapon wheel*.
- **Paste hit a name clash:** the class's private `NameText`/`AmmoText`
  members collided with the variables the Blueprint generates for the
  widgets of those names ("failed to find a property for it"). Members
  renamed `NameTextBlock`/`AmmoTextBlock` (applied by Claude, "go ahead");
  rebuilt clean, bridge up, DLL newer. The user saved the pasted tree
  before the rebuild; it's in the asset (all 26 widgets + `WheelCanvas`).
  Gotcha added to the plan.
- **Icons (user):** too gray — the generated tree had them at 35 %
  opacity (Claude's slip). Then: "for the dual weapons, stack 2 of the same
  icon together diagonally going right", and all icons the same height, the
  widest one (the AK) setting it. Built: `IconMaxWidth` 110 / `IconMaxHeight`
  50 / `DualIconOffset` (30, 14), `IconDual_0..5`, sizes via brush
  `ImageSize` (applied by Claude, "apply and run"; built clean, bridge up,
  DLL newer). Tree generator now `Tools/MakeWeaponWheelTree.ps1`; the user
  re-pastes the tree.
- **Bark volume (user picked the Sound Class route):** `/Game/Audio/SC_Barks`
  (duplicate of the engine `Voice` class, parent cleared so no engine asset
  changes) set as Sound Class on all 43 bark waves (7 English, 36 Tagalog),
  saved. Adjust: open `SC_Barks` → Properties → Volume.
- **Dual icons (user):** "one on top of each other to indicate dual, only
  offset on X and Y, like the second image shadowing the first" — the tree
  now draws `IconDual_N` behind `Icon_N`, and `DualIconOffset` defaults to
  (10, 8) (applied by Claude, "apply and run"; built clean, bridge up, DLL
  newer). The user's saved WBP still has the earlier paste (copy on top):
  re-paste, or swap the icon slots' ZOrder.
- **`.gitignore`:** `/Audio Processing/` (source recordings and edits). The
  14 files already tracked there stay tracked until
  `git rm -r --cached "Audio Processing"` (user's call, with a commit).
- **Tested (user, end of session):** "stuff is tested" — the designer wheel
  (shared icon height, widest icon deciding, accepted as is; dual shadow
  pair), bark volume via `SC_Barks`. Committed by the user as `ffcfde52`
  "Add Weapon Wheel and Bark Dialog Update". **Only `IA_WeaponWheelCycle`
  mapping is left** — tomorrow.
- **Bark pitch spread (user: random pitches could land almost the same):**
  `UBarkSubsystem::AssignPitch` / `ReleasePitch` + `FAssignedPitch` list;
  `UBarkVoice::PitchSpreadJitter` 0.3; `AEnemyBase::RollVoicePitch` asks the
  subsystem, `Die` releases. Applied by Claude ("apply and run"); built
  clean, bridge up, DLL newer. (A first patch script dropped its anchor
  lines; restored from backup and redone before building.) Spec: *Enemy
  barks → Pitch spread*.
  **Tested by the user: "pitch spread works".**
- **Shots on CC people (user: "they shoot each other again… bullet holes
  appear on the CC models"):** checked live in PIE first — collision hadn't
  changed (capsule Pawn; body the only bullet-blocking part; clothes/head no
  collision). Causes: (1) **no character had a physical material**, so body
  hits used `DA_ImpactEffects` Default = concrete + bullet hole, projected onto
  every CC piece; (2) **misses** (60–150 cm beside the player) leave the
  ally-check tube and, with friendly fire on, hit allies beside/behind the
  player. Fixes (applied by Claude, "apply and run"): Phys Material Override
  = `Blood` on the Mesh of `BP_EnemyBase` + `BP_PlayerCharacter` (bridge; CC
  children inherit; verified in PIE on `BP_Enemy_CC` and `BP_Player_CC`);
  `SpawnImpact` skips decals on characters; `AEnemyBase::IsAllyAlong` +
  `MissCarryDistance` 1500 — a miss checks its own path, mirrors to the other
  side or holds. Built clean, bridge up, DLL newer.
  **Tested by the user: "misses work".**
- **Bullet hit and near-miss sounds (plan item 26).** Real Recorded Guns
  cues wired into `DA_ImpactEffects`: per-surface `Sound` + `SoundVariants`
  (all 24 surfaces + Default), `HeadshotSounds` (bone `head`),
  `NearMissSounds`, `SoundAttenuation` = new `ATT_BulletImpact`.
  `PlayNearMiss` runs after every hitscan round. Applied by Claude ("apply
  and run"); built clean, bridge up, DLL newer; assets checked (every cue
  path exists, other DA fields unchanged) and saved. Spec: *Impact effects →
  Hit and near-miss sounds*.
  **Tested by the user: "sounds work".**
- **Female CC (user: "for civilians … and one story character").** Lore doc
  *Female characters* + spec note. **`ik_` bones on `CCMH_Body_Female`**
  (user): the copy/paste attempt misnamed a bone and Merge All tried to
  re-merge the male (failed, nothing saved); restarted without saving,
  `git restore`d the female mesh, then added the seven bones by hand →
  Merge. Verified: female has all seven, male + `CCMH_Skeleton` unchanged,
  no merge warnings. Gotcha in the plan. Next: head per gender, civilian
  preset, female clothing layers.
- **Female characters, rest of the list (user: "do all the fix in the
  checklist … including that one").** (1) `BuildCCCharacter` (enemy +
  player) takes body and head from the preset (`LoadAssetBlocking` + set);
  a first write bound the wrong getter class and resolved soft refs only —
  reverted unsaved, rewritten with `:self` + loads. Verified with a placed
  female (viewport capture: female body + head, hair) and male enemies +
  player in PIE. (2) `CCMH_Preset_PH_Female` + `DT_Outfits_PH_F` (8
  placeholder civilian outfits). (3) Female clothing layers: 67 MIs by path;
  the pass overwrote the **male** `MI_Shirt_01` (inner shirt of the female
  blazer) to 1 — caught on read-back and restored to 3; male-side values
  otherwise unchanged. Gotchas in the plan.
- **Git LFS (user: "mark it now before the repo gets bigger").** Claude wrote
  `.gitattributes` (Unreal binaries, source art/audio/video, fonts,
  archives); the user ran `git add --renormalize .` and committed
  `4ecf87a5` + `111a1187` (25,467 files now LFS pointers; checked: assets in
  `HEAD` start `version https://git-lfs…`). Push via GitKraken in progress at
  18:35 (~6 GB of LFS uploads, ~5 MB/s). History stays plain git (4.87 GiB).
  `.git` is 11 GB: the history plus a 6 GB LFS cache from an earlier
  abandoned attempt, and four index-less pack files (debris; cleanup later).
- **Remote work while the user was away (user: "do A and B now").**
  **B — audits**, report `Documentation/Reports/2026-10-24_Audit.md`: code
  review of the week's C++ (1 medium bug: dying with the keyboard wheel open
  leaves it up and a later click ends the death slow-mo early; plus lows),
  warnings (incremental builds clean; editor log: StateTree/navmesh noise at
  PIE shutdown, `[WeaponSound]` diagnostics still on, 3 ensures all explained
  — one was the in-memory skeleton break during the failed `ik_` merge),
  unused content (~2.4 GB of 6.5 GB never reached; CleanFlatIcons alone
  17,796 files), repo size (11 GB = 5 GB history + 6 GB LFS cache + ~86 MB
  orphan packs). **A — docs**: this log split (entries before 10-21 (3) →
  `ProgressLog_Archive.md`, one live RESUME list); the spec got a contents
  list, superseded notes on the five Aswang-era enemy sections, and the
  plan's 52 gotchas moved into *Engineering gotchas → Full list*; the plan
  groomed (items 23/24 closed, item 10 noted, phases 0–3 and 4.5 collapsed);
  the GDD (+ html) brought up to date in pitch language.
- **Weapon wheel: no cheesing the slow motion** (user: "remove the crosshair
  whenever the weapon wheel is open and dont allow looking around. they can
  cheese the game because of the dilation"). `LookInput` swallows look while
  the wheel is open (pointer mode still steers); `UReticleWidget` hides the
  dot by render opacity; `IsWeaponWheelOpen()` made public. Movement stays
  free. Applied by Claude ("apply and run"); built clean, bridge up, DLL
  newer.
- **Weapon wheel shuts on death** (audit #1; user: "apply and run"). `Die`
  closes an open wheel before `StopFocus` and clears `bWheelOwnsFocus`, so a
  click after death can't end the death slow-mo early or pick a weapon for a
  dead character. Built clean, bridge up, DLL newer.
- **Background music system** (user: "make a bgm system. one that plays
  background music, and can crossfade in a trigger" — "also does not get
  affected by time dilation"; "apply and run"). `UMusicSubsystem` (one track,
  equal-power crossfades) and `AMusicTrigger` (a blue box; `bPlayAtStart` for
  a level's opening music). Kept out of slow motion: the music is a UI sound,
  which the Focus's global pitch drop skips, and the engine's fades run on
  undilated time. Built clean, bridge up, DLL newer. Plan item 27; spec
  *Background music*.
- **Correction: no `[WeaponSound]` logging to remove** (user: "remove the
  logging now"). None in the source or its git history, and none in today's
  editor logs; the audit had counted 2,390 lines from `ProjectBopis_3.log`,
  a 10-23 log (last line 13:53) — the debug code came out before it was ever
  committed. Audit #5 corrected.
- **Level exit** (plan item 28, the slice brief's one required new code; user:
  "Go with exit trigger. Dont drop it on the map, thats a test for later";
  "apply and run"). `ALevelExitTrigger`, a green box: the player walks in →
  can't be hurt, input off, slow motion ended, HUD gone, fade to black with
  the music, an optional "level complete" widget, then `NextLevel` loads
  (None: this level restarts). Real seconds throughout. Built clean, bridge
  up, DLL newer. **Not placed in any level** (user's test for later).
- **Room cleared + waves** (plan item 29; user: "do the room cleared one,
  even better if you can set a wave spawning event system" → "do step 1 and
  2"). `AEncounterTrigger` now counts its room (placed, spawned-ahead and its
  own spawns, delayed ones too) and, when all are down, starts
  `EventsOnCleared`, fires `TriggersOnCleared` and broadcasts `OnCleared`.
  `Waves` follow the first spawns as the room thins out (`StartWhenAliveAtMost`
  + `Delay`, events per wave, `OnWaveStarted`). Applied by Claude; each step
  built clean, bridge up, DLL newer. Not tested.
- **CC skin seams and shading — fixed** (user, home: "I can see seams in all
  the cc models if they have their skin exposed"; 2026-10-25: "clothes
  fixed"). Two causes:
  - **Skin push lit wrongly.** The 10-22 clothing pushes on skin were Pixel
    Depth Offset, which also moves where a pixel is lit: bare skin shadowed
    itself (a line across the upper chest at the head/body join, one above
    the navel, orange forearms on the female). Confirmed by zeroing the
    biases ("seams gone"). Gating the push by the clothing masks was tried
    and dropped: on the head the body-layout masks lit random patches, and
    on the body they're too coarse (a one-piece swimsuit and dresses got
    holes at the waist). Final: the original always-on pushes, delivered as
    a WPO along the camera ray (like the garments' own push); PDO back to
    CC's. Recompiled clean, saved (`M_Skin_CCMH`; MIs unchanged at 2 / 3.5 /
    2).
  - **Head shadow cut off at the seam.** CC's `CC_SkelMesh` (heads, apparel,
    hair) had **Self Shadow Only** on; the user unticked it and saved.
  - Not a bug: the orange in the creator level is its body-selection
    highlight. Spec: *Skin push by WPO* and *CC parts cast shadows on each
    other*; two new gotchas.
- **Dual aim pose: set up, then rolled back** (user: the dual aim bends the
  jacket seams → "roll that back, actually. I think the pose is fine"). A
  dual-only `MM_Pistol_Idle_Dual_Aim` and its `bIsDualWield` branch in
  `ABP_Player` were added and removed again the same session; the clip is
  deleted, `ABP_Player` is functionally back to `111a1187` (re-saved).
- **Dual reload: torso and off-hand shoulder held** (user, with a screenshot:
  "This happens when reloading with dual. It does movement on the torso and
  the left hand armpit abnormally goes inside the body. I want no movement on
  lower to middle spine ... the shoulder on the left dips hard"; "apply and
  run"). The 10-05 accepted quirk. C++ `DualReloadHoldAlpha` (eased); two
  Layered Blend per Bone holds in `ABP_Player` — pelvis + `spine_01`–`03`
  after `DefaultSlot`, the off-hand collarbone after `OffhandSlot` — using
  negative blend depths to stop each filter below the wanted bones. Built
  clean, bridge up, DLL newer; AnimBP compiled clean and saved. **User-tested:
  "reload works"** (as built — `spine_04` left free).
- **Home test pass** (user, 2026-10-25): wheel lock (incl. dying with it
  open) ok, wheel cycling ok, female clothing layers ok, male tucks ok, enemy
  search with the gun down ok, overheard conversations stage 2 ok, background
  music ok, level exit ok, room cleared + waves ok. **Gunfire audio: "to
  refactored"** — consecutive shots still not right; plan item 31. Plan items
  10, 20, 28, 29 closed; the GDD's build list gained music, waves and the
  level ending.
- **One-handed pistol broken → back to the last push** (user, 10-25: "pull
  from the last push"). Local `main` = `origin/main` (`b3dac65c`), so the six
  assets saved in the editor since (`AM_Shotgun_Reload`, `MM_Shotgun_Reload`,
  `AM_Shotgun_Fire_Pump`, `CCMH_Body_Male`, `ABP_Player`, `MM_Rifle_Equip`)
  were backed up to the scratchpad and restored with `git restore` (editor
  closed). None of them were Claude's.
- **Procedural pump + grip curves, part 1** (plan item 32; "apply and
  run"). C++ built clean, bridge up, DLL newer. Bridge: both shotguns get
  `Slide_Bone`/8 cm (user: the semi-auto "does not pump. Pumps on the
  reload"). A pump-only reload montage was made, then dropped — the rack clip
  is additive and can't go in a full-pose montage, and both shotguns share
  `MM_Shotgun_Reload` anyway, so its End pumps by curves; the six character
  Blueprints' map entries were put back (the CC four hold their own copies).
  An AnimBP made by the bridge had no target skeleton and was deleted — the
  user makes it. Not tested.
- **No rack after a reload, for now** (user, on the reload's End: "better of
  not playing the end" → "Just dont rack it at all for now"; "apply and
  run"). `ABopisCharacterBase::bPlayReloadEnd` (default off): when loading
  stops, Loop's next section is `NAME_None`, so the montage ends with the
  last insert and blends out. Both shotguns. Built clean, bridge up, DLL
  newer. Not tested. The slide's AnimBP waits for the final shotgun model
  (`Shotgun_A` is a placeholder).
- **Final weapon assets planned** (user: "That looks better, but I think at
  this point I better add the final assets"): pump shotgun, SPAS-12 (replaces
  the semi-auto), single + dual Berettas (new), Micro Uzi (replaces the
  MAC-11), AR-15 (new model), AK-74u (new). Plan item 33; a reusable intake
  checklist in the spec (*Adding a weapon*). Four design calls asked.
- **9mm and .45 pistols** (user: "I will keep the mac-11. I have added the
  Beretta. Create a weapon and dual for it. Name it 9mm Pistol. Rename the
  current pistol to .45 Pistol"). Bridge: `BP_Pistol9mm` /
  `BP_DualPistol9mm` (copies of the .45 pair) on `SK_Beretta_92FS`,
  cross-linked single/dual/drop, animation-driven feedback off with
  `P_Pistol_MuzzleFlash_01` (no fire anim on that skeleton); display names
  ".45 Pistol" / "Dual .45 Pistols" and "9mm Pistol" / "Dual 9mm Pistols".
  Compiled, saved; then scaled 1.2 (user; the root mesh, the off-hand
  inherits). The Beretta needs its sockets before it's usable. Earlier:
  for a period-accurate dual SMG the "Ingram" (MAC-10/11, Danao copies)
  fits 2002 Philippine crime best — the user kept the MAC-11.
- **Weapon feedback standard proposed, on hold** (user: "We will use
  animation for the weapons for the weapon movements ... The notifies drive
  the sounds" → "hold of on this, I will replace all the weapons that uses
  silver"). Proposal in the spec (*Adding a weapon*); the silver-mesh guns
  listed in plan item 33. No code changed.
- **M1911 in for the .45s** (user: "reimported with -90 yaw, scale it 1.1 and
  swap it in, can you rig the slide?"). Bridge: `Rigged_M1911` on the .45
  pair and the enemy-only pistol, ×1.1, code flash, silver fire anim cleared;
  saved. The reimport's rotation didn't show (barrel still along X; file
  unchanged since the 18:52 import). Slide rigging can't be done over the
  bridge (no bone or weight tools).
- **M1911 swap reverted** (user: "revert that change to the pistol, put them
  back to the silver model ... We can use the new 1911 magazine instead for
  reloads"). The .45 pair and enemy-only pistol are back on `Pistols_A`
  (scale 1.0, `Fire_Pistol_W`, animation-driven feedback, no code flash; the
  ".45" names kept); saved. A magazine-in-hand proposal (a notify state +
  per-weapon magazine mesh) was set aside — "we do the magazine stuff later.
  I have my own ideas for that. Lets just update all of the weapon models for
  now". No code changed.
- **5.56 Assault Rifle + Mossberg material** (user: "BP_CloseRangeRifle Gets
  replaced as 5.56 Assault Rifle. Use the M4 Model form the FPS pack. I added
  a Mossberg Model ... Its material is not set up"). Bridge: the rifle
  renamed and on `SK_AR4`, with `MuzzleFlash`/`AmmoEject` sockets on its own
  bones; `MI_Mossberg500` (from `M_TacticalPistol`, BaseColor/Normal/ORM, black
  mask) on the Mossberg mesh, its ORM texture made linear; all saved. Open:
  the rifle is still the old projectile round (asked), its `LeftHandGrip`
  and grip offsets; the Mossberg goes onto a Blueprint next.
  Then the rifle scaled 1.2 (user: "AR scale is off" → "scale it 1.2"; its
  Blueprint had no scale — the M4 is 91 cm against the silver rifle's 97).
- **AR to 1.1; Mossberg pump bone** (user: "try 1.1 or the AR. The new
  mossberg has no pistol grip, and the left hand looks odd even after adding
  the lefthandgrip"). Rifle scale 1.1, saved (one save attempt returned a
  transient 'asset does not exist'; the retry worked). The user had put the
  Mossberg on `BP_PumpShotgun` with its sockets; its `PumpBoneName` was still
  the silver `Slide_Bone` (sideways pump offset) — now `pump`. The left-hand
  look is open: screenshot asked.
- **AR back to 1.2** (2026-10-26; user: "the problem is the extended stock").
  `SK_AR4_X` checked: the same M4 turned to +X, not a collapsed stock; the
  stock isn't rigged, so a collapsed one is a mesh edit (user).
- **Mossberg scaled 1.2** (user: "the mossberg is out of scale too, try 1.2
  aswell"). Set on `BP_PumpShotgun`'s root mesh and compiled, but the bridge
  wouldn't save it ('Asset does not exist', three tries, though `find_assets`
  lists it and the file is on disk) — the user saves it in the editor. Gotcha
  in the making: a bridge save right after a compile sometimes fails like
  this; a later standalone save worked once (the rifle), not here.
  (The user saved it afterwards: no longer dirty.)
- **Left hand locked to the gun** (user, Mossberg screenshot: "The left hand
  keeps rotating when looking around"; "go"). The left-hand Two Bone IK kept
  the animation's hand rotation (Take Rotation From Effector Space off,
  Maintain Effector Rel Rot on); flipped both, so the hand follows `ik_hand_l`
  on the gun. All two-handed guns. `ABP_Player` compiled, saved. Not tested.
  **Reverted** (user: "enemies hands twist ... Your current fix did not
  work"): back to Take Rotation off / Maintain on; the user saved
  `ABP_Player`. The Mossberg's hand is a reach problem — its `LeftHandGrip`
  (y 40) is farther forward than the M4's. Not fixed yet.
- **Mossberg fire animation (user).** After a walkthrough (Create Animation
  from the mesh, setting its length), the user made
  `/Game/Mossberg/Mossberg-500_Pump` on the Mossberg's skeleton, with Weapon
  Sound notifies.
- **Weapon feedback standard in code** (user: "It will now always play the
  Fire animation when firing. If it is none, it will not do it. We replace
  the notifies with our own ones so it does not double up"; "apply and
  run"). `bUseAnimationDrivenFeedback` / `UsesAnimationDrivenFeedback()`
  removed (`WeaponBase.h`); `Fire()` plays `FireAnimation` if set (its
  Weapon Sound notifies make the sounds), else the Fire sound from code, and
  always spawns `MuzzleFlash`; a comment in `BopisCharacterBase.cpp`. Bridge:
  `P_Pistol_MuzzleFlash_01` on the .45 pair and `BP_Pistol_EnemyOnly`;
  `BP_PumpShotgun`'s `FireAnimation` = `Mossberg-500_Pump`; compiled. The
  bridge save failed ('Asset does not exist' ×3) — the user saves. Built
  clean, bridge up, DLL newer. Not tested. Until `Fire_Pistol_W`,
  `Fire_Shotgun_NoDelay` and `Fire_SniperRifle_W` get a Fire notify (and lose
  their flash notifies), those guns fire silently.
- **Mossberg pump fixed (user).** "when he is pumping, it looks like hes
  pumping in the wrong direction ... like sideways": the old procedural pump
  (the `Pump` curve on `MM_PumpShotgun_Fire` → an offset along the `pump`
  bone's parent X) assumed `grip`'s X runs along the barrel; on the Mossberg
  it doesn't. The user set `PumpBoneName` None on `BP_PumpShotgun` and
  retimed `Mossberg-500_Pump` to match the body's fire animation: "Its fixed
  now". The pump moves only by the gun's animation; `LeftHandGrip` stays on
  the root bone. The procedural pump is now used only by `BP_Shotgun`
  (`Slide_Bone`; `MM_Shotgun_Fire` has a `Pump` curve), which the SPAS-12
  replaces.
- **Fire animations (user):** 9mm pair (`SK_Beretta_92FS_Fire`), MAC pair
  (`SK_SMG11_Nostock_Y_Skeleton_Fire`), the Mossberg (retimed) and the
  revolver (`_357Revolver_Fire`; "I cant spin the cylinder, bit ill leave
  that"), each with a Weapon Sound Fire notify, wired on their Blueprints by
  the user. **M4 hatch** closed by default and the user's edits "dont go
  thru": viewport bone moves are preview-only — the skeleton editing tool
  (Accept, save) or an M4 fire animation that ends with it open.
- **Lowered long-gun left hand** (user: "on jog and idle lowered, I edited
  the anim so the left hand is close to the weapon grip, but it does not
  follow it"; "apply and run"). `UProjectBopisAnimInstance`: the left-hand IK
  target is now `(bGunUp || !bIsPistolHold) && bTwoHanded && ...` — long guns
  keep the IK lowered; the two-handed pistol keeps the gun-up rule. Built
  clean, bridge up, DLL newer. Not tested.
- **Per-gun left-hand angle** (user, M4 jog: "the hand is the wrong angle and
  position. If i adjust the HandGrip for the jog, it becomes busted for the
  idle"; "apply and run"). Cause: the IK places only the wrist, and the hand
  keeps its angle to the forearm, which differs per clip. New
  `AWeaponBase::bLockLeftHandRotation` (off by default): the hand takes the
  `LeftHandGrip` socket's rotation. Anim instance: `LeftHandGripRotation`,
  `LeftHandGripRotationAlpha`, and the cheat CVar
  `Bopis.LeftHandGripCalibrate` (shows the socket rotation that matches the
  current hand). `ABP_Player`: Modify Bone `ik_hand_l` + Copy Bone →
  `hand_l` after `TwoBoneIK_0`; compiled, saved. Built clean, bridge up, DLL
  newer. Not tested; no gun locks yet.
- **Tested (user):** "lowered idle and jog is fine now. Mossberg hold is ok"
  — the Mossberg and the M4 lock the hand angle (sockets calibrated). Only
  issue: lying **backwards** (prone on the back after a shootdodge) the left
  hand can't reach the grip — "maybe fix this later but ignore for now".
  Committed and pushed by the user (`4103f1da`, "Added Some weapon anims. Fix
  on left hand grip for long guns").
- **Right-hand grip style** (user, Mossberg: "the normal right hand gun grip
  does not fit ... the thumb penetrates through the model becuase of the
  Straight Stock"; "apply and run"). `EWeaponGripStyle` + `GripStyle` on the
  weapon; `RightHandGripPoses` / `RightHandGripPose` /
  `RightHandGripPoseAlpha` + `UpdateRightHandGrip` on the anim instance;
  `ABP_Player`: a Layered Blend per Bone on the right thumb and finger chains
  (`LayeredBoneBlend_16` ← `SequenceEvaluator_0`) after the left-hand IK;
  compiled, saved. First rebuild timed out on the editor's save prompt; the
  rerun built clean, bridge up, DLL newer. The user made
  `/Game/StraightStockGripPose` (on `CCMH_Skeleton`, compatible with
  `SK_Mannequin` both ways); hooked up over the bridge: `ABP_Player`
  Right Hand Grip Poses `StraightStock` → it, `BP_PumpShotgun` Grip Style
  `StraightStock`; compiled, saved. **Bug, solved:** "all weapons are like
  way infront of the player like 5+ meters away" — the user had added a
  preview gun on `HandGrip_R` to pose against ("just added a preview asset
  is all"); dragging a preview asset moves its socket, here the CC body's
  mesh socket on `CCMH_Body_Male`, in memory only (file unchanged).
  Reloaded → "guns are back, grip works". Gotcha in the spec.
- **Magazine drops** (user: "next is mag drops on reloads"; "apply and
  run"). The Weapon Sound notify now calls `AWeaponBase::PlayWeaponEvent`:
  the sound, plus Mag Out → `DropMagazine` (an `AShellCasing` with
  `MagazineMesh` from the `Magazine` socket; the socket's bone hidden) and
  Mag In → shown again (also on `FinishReload` / `CancelReload`).
  `UShellCasingSubsystem` keeps magazines separately (16). First build failed
  — a `bHidden` parameter shadowed `AActor::bHidden` (C4458) → renamed
  `bHide` (presented, "apply and run"); built clean, bridge up, DLL newer.
  Bridge: `MagazineMesh` on eight Blueprints; compiled, saved. Not tested —
  needs the user's `Magazine` sockets.
- **Mag drops tested** (user: "mags drop, works"). Sockets on disk: `SK_AR4`,
  `SK_Beretta_92FS`; the MAC (`SK_SMG11_Nostock_Y`) and .45 (`Pistols_A`)
  were saved without one at first; then "already added and tested
  working" — the MAC's saved on its skeleton (19:03); the .45's still
  unsaved at 19:03 (user to save `Pistols_A`).
- **M4 hatch, in progress (user):** "the edit skeleton is not rotating the
  preview even when the value is changed" — the skeleton editing tool moves
  joints under the mesh (re-rigging), so it can't swing the hatch. Route: a
  one-frame "hatch open" pose on the M4 skeleton as the `WeaponMesh`'s own
  animation (Use Animation Asset), and/or a fire animation that ends open.
  GDD (+ `.html`): a 2026-10-26 line for the day's player-visible changes.
- **M4 hatch and fire animation done (user):** "made AR4_HatchOpen, made the
  fire anim and its set and working now". Asked what times casing ejection:
  `CasingEjectDelay` (0 = with the shot; pump 0.4 s), a timer in `Fire()`,
  not the animation — an Eject notify on fire animations offered, not built.
- **Eject notify** (user: "do the eject notify"; "apply and run"). New
  `EWeaponSound::Eject` (no sound): `PlayWeaponEvent` throws the casing; a
  gun whose fire animation has one (scanned at `BeginPlay`,
  `bFireAnimationEjects`) skips the ejection in `Fire()`. Built clean, bridge
  up, DLL newer. Not tested — needs the user's notifies.
- **Blood: size and floating chunks (user).** Blood's DA Scale → 0.5 did
  nothing visible (component scale doesn't reach these sprite sizes); the
  user trimmed `NS_ImpactBlood` in the Niagara editor instead. Its chunks
  then froze at the hit height on an invisible, raised copy of the floor.
  Tried: Distance Field collision (kept), small collision radius (no
  effect), a "Debris" trace channel + CPU ray trace (config, Blueprint
  responses, docs — **rolled back** at the user's call, verified: config
  back to HEAD, all six Blueprints' responses as before). **Fix: Local
  Space off on BloodChunks1** (user: "that fixed it"). Gotcha in the spec.
- **1911 kit extracted** (user: "extract the 1911 pistol model only … including
  variants"). From the UE 4.27 project `Pistol1911AnimSet` (since deleted by the user), file-copied (the
  same paths, so references hold; 5.8 loads 4.27 packages) into
  `Content/Pistol1911_Animation_Kit/`: 47 files, 237 MB.
  - **Both variants:** `SK_P1911` and `SK_P1911_M`, sharing
    `SK_P1911_M_Skeleton`.
  - **Mesh parts:** magazines `pistol1911_mag` and `SM_P1911_M_mag`, plus .45
    rounds (`45_shell` / `45_bullet` / `45_core`, `bullet_lp_uv`), with their
    materials and textures.
  - **Gun animations** (`WeaponAnimations/`: shot, shot empty, reloads, idle
    pose, `Anim_P1911_M_Shot_Montage`, `SK_P1911_M_AnimBP`).
  - **The 1911 shot sound** (`pistol_1911_shot_Cue` + 5 waves).
  - **Left out:**
    - the arms, arms animations, character, camera shakes, map and
      template Blueprints;
    - `Bullet_Emissive` / `projectile_glow` (the template projectile's);
    - the three reload montages, whose `ClipHideUnhide` notify drags in the
      kit's whole weapon framework (the sequences under them were copied).
  - All internal references resolve; LFS-tracked; loads in 5.8.
    `Anim_P1911_M_Shot` plays the shot cue through a PlaySound notify.
- **The .45s on the 1911** (user: "replace the .45s with the 1911";
  bridge).
  - **Blueprints:** `BP_Pistol`, `BP_DualPistols` (both meshes) and
    `BP_Pistol_EnemyOnly` → `SK_P1911_M`, `FireAnimation`
    `Anim_P1911_M_Shot`, `MagazineMesh` `SM_P1911_M_mag`.
  - **Then the black one** (user: "Use the black 1911 model"):
    `SK_P1911` on all four meshes, `MagazineMesh` `pistol1911_mag`; the
    shared skeleton keeps the animation, sockets and grips. Compiled, saved,
    binaries checked.
  - **Sockets:** muzzle and magazine use the kit's skeleton sockets,
    `muzzle_socket` and `clipSocket`. There's no ejection socket yet, so
    `AmmoEject` is the user's to add.
  - **Grip:** z −2 → +2.5, a starting point scaled from the Beretta's tuning.
    The 1911's root sits ~4 cm higher in the gun than `Pistols_A`'s; same
    axes.
  - **Built:** compiled, saved; the binaries no longer mention `Pistols_A`,
    `Fire_Pistol_W` or `/Game/M1911`.
  - **Not swappable over the bridge:** notifies can't be read, so the kit's
    PlaySound notify still sounds the shot. Details in the spec, *The .45s
    on the 1911*.
- **Old M1911 pack deleted** (user: "delete that so dereference any thing
  using those assets"). `/Game/M1911/` held 31 assets: a rigged and an
  unrigged M1911, its magazine and .45 round, textures, and a demo map.
  - **Only users:** the three .45 Blueprints, via `MagazineMesh` (found by a
    disk grep and by the asset registry's referencers check).
  - **Deleted** with `AssetTools.delete`; the folder is gone on disk and
    git shows 31 deletions (the rigged mesh's uncommitted socket edits go
    with it).
- **Docs repair.** Four stray `$1` lines, two in the spec and two here, came
  from earlier perl swaps that wrote a literal `$1` in place of the matched
  line. Each had dropped one line; all four were restored from the session's
  backups:
  - the M4 hatch bullet's ending;
  - "Not in scope: a fresh magazine in the hand";
  - the magazine-drops entry's ending;
  - the GDD note.
- **Fitted magazine** (user: "the 1911 does not have a mag in by default";
  "apply and run"). The black 1911's mesh has no magazine. The kit's
  Blueprint fitted `pistol1911_mag` at `clipSocket` instead.
  - **New:** `AWeaponBase::bShowMagazineMesh`, weapon-wide and off by
    default. `FitMagazine` seats `MagazineMesh` at the magazine socket at
    `BeginPlay`: a runtime `UStaticMeshComponent`, one per mesh for duals.
    `SetMagazineHidden` hides and shows it with the bone.
  - **Build:** rebuilt via the script (34 s); bridge up, `list_toolsets` OK;
    DLL 22:50:16 is newer than the source (22:48:49).
  - **Bridge:** ticked on `BP_Pistol`, `BP_DualPistols` and
    `BP_Pistol_EnemyOnly`; compiled, saved.
  - **Not tested.**
- **Lowered pistol grip** (user: "when using one handed pistols and not
  raised. The right hand is not using the gunhold"; "apply and run").
  - **Cause:** a lowered pistol plays Lyra's unarmed idle and jog, which
    have an open right hand, and the finger layer only applied grip styles
    that have their own pose.
  - **Fix:** `LoweredPistolGripPose` on the anim instance;
    `UpdateRightHandGrip` plays it while a pistol hold is down and not
    reloading. Set in `ABP_Player` to `MM_Pistol_Idle_Hipfire` (bridge;
    compiled, saved).
- **Slots and the launcher** (user: "Rifles are on selection 5 on the weapon
  wheel and keys"; "move snipers to 6"; the launcher out "completely" but "I
  did not want you to remove the grenade launcher BPs and code").
  - **Slots:** `BP_CloseRangeRifle` 4 → 5, `BP_BattleRifle` 5 → 6 (bridge;
    compiled, saved). The list of all weapons confirmed no other rifles or
    snipers.
  - **Launcher:** nothing gives it out, so it's out of the game as it
    stands, with nothing deleted. A deletion plan was proposed and dropped.
    Hand grenades are unchanged.
  - **Comments:** `WeaponSlot` and `NumSegments` updated.
- **Build:** one rebuild for both (22.8 s). The script stopped before opening
  the editor: `Select-Object -First` ends a PowerShell 5.1 pipeline and its
  script. A rerun built nothing and opened it. Bridge up, `list_toolsets`
  OK; DLL 23:20:28 is newer than the source (23:19:59). Restart the editor
  before testing the grip pose: it's an object reference set over the
  bridge.
- **Restarted** ("run the script"; nothing to build) **and tested** (user):
  "grip works, slots work".
- **Fitted magazine tested** (user): "mag fitted works".
- **Wheel icons fill their wedge** (user: "make the weapon icon as big as
  possible without going out of the section … not set. its based on what
  the icon is"; "apply and run").
  - **Change:** `UWeaponWheelWidget::FitIconHeight` fits each icon to its
    own wedge at its own proportions: the ring 165–295, a 56° wedge, a 6 px
    margin, and a dual pair's spread counted. `IconMaxWidth` /
    `IconMaxHeight` and the shared height are gone.
  - **Expected sizes:** flat top and bottom wedges much bigger; on the
    diagonal sides, a rifle about 116 × 33 and a pistol about 96 × 69.
  - **Build:** rebuilt (17 s); DLL 23:49:28 is newer than the source
    (23:48:54); bridge up, `list_toolsets` OK. No Blueprint change needed.
  - **Not tested.**
- **Wheel icons, handgun scale** (user: "The pistols are rendering too big
  right now. and the duals are mushed together too much … allow the weapons
  to go out of the section BUT, keep the handgun to fit nicely in the frame,
  then use that scale with everything else like before"; "apply and run").
  - **One height again:** the carried handguns' fit in their wedge ×
    `HandgunFill` 0.8 (`SharedIconHeight`; kept when no handgun is carried).
    Long guns may overrun their wedge.
  - **Duals:** `DualIconOffset` (pixels) became `DualIconSpread` (0.3, 0.25
    of the height). That's the same look as the (10, 8) the user approved
    at about 31 px.
  - **Build:** rebuilt (19 s); DLL 23:59:21 is newer than the source
    (23:58:44); bridge up, `list_toolsets` OK.
  - **Not tested.**
- **Dual icon separation** (2026-10-27, user: "more separation for the duals,
  where the top left corner of one is the center of the other"; "apply and
  run").
  - **Change:** `DualIconSpread` is now a fraction of the icon's own width
    and height, default (0.5, 0.5). The offset is `DualIconSpread * IconSize`,
    with `IconSize` = (`SharedIconHeight` × aspect, `SharedIconHeight`).
  - **Build:** rebuilt (18 s); DLL 00:03:20 is newer than the source
    (00:02:55); bridge up, `list_toolsets` OK.
  - **Tested (user):** "duals look good, wheel works".
- **Floating drops** (user, with a screenshot of a dropped Mossberg hanging
  above the floor: "the new shotgun and 1911 drops, they both end up like
  this sometimes"; "apply and run").
  - **Cause:** `AWeaponDrop::Launch` sized its box with
    `MeshComponent->CalcBounds`, which can come from the physics asset. Both
    guns have auto-generated capsule bodies; the silver guns, which drop
    fine, have boxes. So the box came out bigger than the gun, which hung
    inside it.
  - **Fix:** the box now uses `USkeletalMesh::GetImportedBounds()`.
  - **Build:** rebuilt (16 s); DLL 00:09:48 is newer than the source
    (00:09:20); bridge up.
  - **Bridge read:** both meshes' own bounds are tight, with no extensions.
    The physics bodies can't be read over the bridge.
  - **Tested (user):** "all fine".
  - **Noted:** dropped and picked-up 1911s show no magazine, because the
    fitted one is on the weapon actor. Offered, not built; the user's "all
    fine" taken as not wanted.
- **User items done and tested** ("all fine"): Eject notifies on the
  Mossberg, M4, 9mm and MAC fire animations; the 1911's `AmmoEject` socket,
  its shot notify (Fire + Eject) and grips.
- **Committed by Claude** (user: "you commit this time, briefly list the
  changes similar to my style"): `54daab6e` on `main` — 49 added, 34
  modified, 31 deleted (the old `M1911`); the 1911 kit's 47 files in LFS.
  Not pushed: the sandbox can't authenticate, so the user runs `git push`.
  Committing goes back to the user.
- **Docs:** this log's entries since the 1911 swap had been inserted inside
  that entry (after its "Then the black one" sub-bullet); moved back into
  order.
- **New fidelity target** (user): "Xbox 360 levels of fidelity IE max payne 3
  levels … on the Steam Deck", raised from Halo 1–2 "based on the assets we
  have been using".
  - **Targets (user's table):** 750 Ti 720p Low 30 (stretch), 1050 Ti 900p
    Low 60, **Steam Deck LCD 800p native 60 (primary baseline, High
    settings)**, **GTX 1650 1080p High 60 ("the real target")**, 1660 Super
    1080p High 120 (optional). Only a Deck to test on.
  - **Proposal agreed in outline, not yet built:** one baked-lighting
    renderer on every tier (no Lumen, Nanite or ray tracing); High tuned on
    the Deck with headroom, standing in for the 1650; Low for the older
    cards. Five steps (plan item 34).
  - **Findings:** Substrate is on (blendable GBuffer); AA was off
    (`AntiAliasingMethod=0`); the shader formats already include DX11 SM5;
    no groom hair in the project.
  - **Recorded:** design notes Part 4, spec *Rendering target* (rewritten),
    GDD fidelity paragraph + a 2026-10-27 line, plan item 34.
- **Step 1, renderer switch, applied** (user: "all my levels are currently
  direction light lit"; "go ahead").
  - **Config:** 11 lines in `DefaultEngine.ini`. GI none, reflections
    screen space, Lumen hardware ray tracing, ray tracing, its proxies and
    path tracing off, virtual shadow maps off, Nanite off, static lighting
    on, mesh distance fields off, TAA. Backup in the scratchpad; git has it
    too.
  - **Restart:** via the script. About 4,000 shaders recompiled in about 3
    minutes; bridge up, `list_toolsets` OK. The log confirms the settings,
    and its 14 warnings are all old ones (AmmoSet physics recompute etc.).
  - **Nanite meshes:** only 15, all greybox or unused.
  - **Blood chunks:** Collision Type Distance Field → Depth Buffer, left to
    the user.
  - **Levels:** each is one movable sun with sky light, atmosphere,
    volumetric clouds and fog. Flat in shade until the bake; clouds to go.
  - **Checked (user):** "blood fixed, levels look fine".
- **Step 2, quality tiers** ("present step 2"; "apply and run").
  - **New files:** `Config/DefaultScalability.ini`, with High at level 2
    and Low at level 0, overriding the engine only where needed.
    `UBopisGameInstance` (`BopisGameInstance.h/.cpp`), set as
    `GameInstanceClass`.
  - **First run:** on any machine, the benchmark picks the level. On the
    Steam Deck it then sets High, 1280×800, a 60 cap and VSync. Never runs
    in the editor.
  - **Build:** rebuilt (26 s); DLL 00:59:06 is newer than the source
    (00:58:20); bridge up, `list_toolsets` OK; no log errors.
  - **Suns' shadow distance:** both have a custom value that couldn't be
    read reliably from the files; the user sets 4000.
  - **Not tested.** The Deck path needs a packaged build (step 5).
- **Gamepad controls** set by the user in `IMC_Default` ("I did the control
  changes"). Claude had suggested RB shootdodge, R3 focus, X reload, B roll,
  Y grenade, L3 crouch.
- **Wheel, right stick** (user: "its not going to where I am moving it to";
  "just fix the wheel").
  - **Cause:** the stick went through `AddPointerDelta`, which adds input
    like a mouse; the pointer drifted on the sum.
  - **Fix:** `IA_Look` now binds to `StickLookInput` →
    `SetPointerFromStick`. The pointer goes straight to the rim in the
    stick's direction; below `StickDeadZone` 0.5 it holds.
  - **Build:** rebuilt (18 s); DLL 01:12:22 is newer than the source
    (01:11:52); bridge up, `list_toolsets` OK.
  - **Tested (user):** "its inverted up and down". **Flip Stick Y** is now
    off on `WBP_WeaponWheel` (bridge; compiled, saved; a bool, so no restart
    needed). The stick mapping already flips Y. Then: "stick works".
- **First Deck build** (user: "option 1" — the SteamOS Devkit Client over
  Wi-Fi; "apply and run").
  - **Packaging settings** added to `DefaultGame.ini`: Development, pak +
    IoStore, compressed, `MapsToCook` limited to `Lvl_Sandbox` and
    `Lvl_Linear` (there were no packaging settings before, so every map was
    cooked).
  - **Build:** `RunUAT BuildCookRun` started in the background, archiving
    to `ProjectBopis_Builds/DeckTest/`.
  - **User:** Deck Developer Mode, the Devkit Client, the upload, then the
    `stat unit` readings.
  - **First try** failed in seconds: "Unable to build while Live Coding is
    active" (editor open), so the retry used `-nocompileeditor`.
  - **Second try** cooked all 3,888 packages in about 10 min but failed on
    one logged error: the cook process's bridge plugin couldn't bind port
    8000, which the editor held. The user closed the editor; third run
    started.
  - **Third try: BUILD SUCCESSFUL** in 1 min 41 s (shaders cached), 0
    errors, 13 warnings. `ProjectBopis_Builds/DeckTest/Windows`, 2.3 GB with
    the Development debug files. Next: the user uploads with the Devkit
    Client and reads `stat unit`.
  - **On the Deck:** "visual c++ 2015-2022 redistributable required", from
    the top-level launcher's runtime check. Start command changed to
    the real binary, `ProjectBopis/Binaries/Win64/ProjectBopis.exe` plus the
    same arguments. Fallback if DLLs are really missing: include UE's
    prerequisite installer and rebuild.
- **First Deck measurement** (user: "it runs"):
  - **FPS:** "Mostly 60 but at level start and level load it drops"
    (to ~45); "drops to 50 ish mid fight primarily after a kill".
  - **Timings:** Game 8–18, Draw 5–18, GPU 12–20 ms (budgets ≈ 14 / — /
    ≈ 13).
  - **User's hunch:** "the npc loading is hitching the fps".
  - **Suspects in the code:** the director's immediate respawn on a kill
    (`TrySpawnOne`, a whole CC character in one frame, plus new materials'
    shaders), and the ragdoll's `SetPhysicsAsset(…, true)` rebuild at death.
  - **Next:** an Unreal Insights trace over Wi-Fi to confirm, then fix.
    PC 192.168.1.43; procedure in the spec, *First Deck measurement*. A
    trace server was started for it, then stopped at wrap-up (user: "im
    about to sleep now").
- **New issue (user, on the Deck):** "the clothes freak out when killing
  someone far away. I think its LOD related, because it fixes itself up
  close". Not investigated yet. Suspects: apparel following the body by
  leader pose while the ragdolling body sits at a lower LOD that drops
  bones, the clothes then reaching for missing bones; cloth simulation
  switching off at distance; update-rate optimisation on far meshes. The
  Deck's 800p shrinks screen size, so lower LODs come in sooner.
- **Design notes (user):** "we do not have level assets yet"; "walk around"
  parts with civilians you can interact with, "up to 12 NPC max on screen …
  But never for fights. Only 6 mooks per fight feels good at the moment".
  - **Recorded:** design notes Part 4 (targets, a new *Walk-around
    sections*), spec budgets, plan item 34, GDD.
  - **Consequences:** the ~12 ms quiet GPU is greybox, so fixed costs must
    come down before art; and a 12-civilian scene needs its own Deck test.
  - **Correction:** the director's replacements come 1–3 s after a death
    (`RespawnDelayMin`/`Max`), not in the same frame. Both suspects still
    fit "after a kill": the ragdoll rebuild at the kill, the spawn a moment
    later.
- **Render resolution** (user: "it rendered at 71%… I would prefer a clean
  image 100% render than any post processing stuff that would try to fake
  good graphics").
  - **Cause:** the first-run hardware benchmark sets `sg.ResolutionQuality`
    from the GPU index, and the Deck landed in the 71% band. Our High
    setting doesn't touch it.
  - **Fix:** `DefaultEngine.ini` `[SystemSettings] r.ScreenPercentage=100`,
    which outranks scalability and saved settings, so the Deck's saved 71%
    is overridden too.
  - **Build:** the Deck build was repackaged (editor closed).
  - **Open:** the anti-aliasing choice (TAA, FXAA or none) and which post
    effects stay. Recorded in the design notes and spec.
- **Clean image decided** (user: "does mp3 use taa?" — it didn't, FXAA/MSAA
  then; "go with FXAA, keep bloom and AO").
  - **Config:** `r.AntiAliasingMethod` 2 → 1, `r.ReflectionMethod` 2 → 0
    (captures only); the High SSR override removed from
    `DefaultScalability.ini`.
  - **Later, maybe:** MSAA via the forward renderer.
  - **Next:** repackage (editor closed), then the Deck trace.
- **Deck trace** (user: "done, trace captured"). 6 min, 766 MB; analysed
  with Insights' command-line exports. Detail in the spec, *First Deck
  trace*.
  - **GPU:** the volumetric clouds cost 6.1 ms a frame, the sky light's
    real-time capture 0.85 ms; the scene render is ~14 ms, the frame ~18 ms.
  - **Game thread:** each enemy spawn costs ~8–12 ms in one frame
    (construction script plus CC2 `Set Apparel`). That's the "after a kill"
    drop.
  - **Big freezes:** ~0.5 s level reloads on death (`RestartLevel` →
    `OpenLevel`).
  - **Ruled out:** the ragdoll swap (≤ 1.6 ms).
  - **Trace server:** `UnrealTraceServer fork` and `daemon` fail from
    Claude's shell (sponsor mode); opening Unreal Insights works.
- **Sky fix** (user: "do it over the bridge").
  - **Edits:** `VolumetricCloud_0` removed and the `SkyLight_0` real-time
    capture turned off, in both levels.
  - **`Lvl_Sandbox`** keeps one file per actor, which the bridge's
    `save_actor` can't save ("Asset does not exist"). The user pressed
    Ctrl+S; on disk, no cloud actor file is left and the sky light was
    saved at 21:00.
  - **`Lvl_Linear`** was saved over the bridge (21:00, no cloud in the
    map).
  - **Next:** repackage, re-measure on the Deck, then spawn pre-warming.
- **Deck re-measure after the sky fix** (user): "GPU 8-16, mostly on 12. Still
  hitches on new enemies" (was 12–20).
- **Clothing LOD** (user: "busted LOD on clothing when enemies are far
  away"; "I see the clothes busted on living enemies too"; "this only happens
  in the deck").
  - **Diagnosis:** leader-pose apparel is limited to its own LOD count.
    Bodies and heads had 5 LODs, most apparel 4. Bias test: "breaks at 4,
    shirt and pants".
  - **Fix (user):** LOD4 removed from both CC bodies; bridge check: 4 LODs,
    saved.
  - **Withdrawn:** a proposed death-only `SetForcedLOD` change, never
    applied.
  - **Open:** 3-LOD apparel at bias 3. Details in the spec, *CC clothing LOD
    fix*.
- **Spawn hitch: encounter reserves** (user: "you mean you spawn all the
  enemies in the level and just hide them?"; asked about memory for 50
  enemies, an estimated ~1–3 MB each; "this does not change how I set up
  the triggers and spawners yes?" — no; "apply and run").
  - **Change:** the director builds the rest of each fight asleep at level
    load and wakes one per respawn; `MaxReserves` 20.
  - **Build:** rebuilt (28 s); DLL 21:47:03 is newer than the source
    (21:46:22); bridge up.
  - **Deck-tested (second build, 2026-10-27):** "it stayed at 60 even after
    spawns". Details in the spec, *Encounter reserves*.
  - **Found on that run:** the level start ramps from 0 to 60 fps over about
    2 s. The user wants a black screen over it. Brown chinos break at
    distance (body LOD3, see below). The user wants wheel cycling on the face
    buttons, which do nothing while the wheel is open.
  - **Chinos fix:** the user set both bodies to 3 LODs. Bridge check: Male
    7,273 / 5,412 / 3,088 vertices, Female 7,241 / 5,367 / 3,043, saved
    22:51. The earlier sweep's counts still hold (5 LODs: 33, 4: 126, 3: 20,
    2: 2, 1: 2). The four pieces below 3 LODs (bikini, swim briefs, female
    sports jersey) stay out of NPC outfits.
  - **Level-start black screen** ("apply and run"): in
    `AProjectBopisPlayerController`. Black (Slate, over the HUD) and paused
    until frames stay steady for 0.5 s, within 0.5 to 3 s, then a 0.4 s
    fade-in. Rebuilt (27 s); DLL 22:55:03 is newer than the source
    (22:54:26); bridge up. **Not tested.**
  - **Third Deck build + trace (23:18):** steady 60 outside loads (p99
    20 ms); GPU scene about 9.6 ms; the level start settles within
    about 1 s, under the black screen. The remaining 34–66 ms hitches are
    `AEncounterTrigger` room waves building enemies when triggered; the
    reserves fix only covered `AEncounterDirector`. The spec has it under
    *Second Deck trace*. The user cleared about 22 GB of editor
    auto-traces; Insights must be closed after captures.
  - **Chinos:** Deck-tested, fixed.
  - **Trigger reserves** ("apply and run"): `AEncounterTrigger` builds
    every Spawns and Waves enemy asleep in `BeginPlay` and wakes it in
    `SpawnOne`. Rebuilt (27 s); DLL 23:51:28 is newer than the source
    (23:50:56); bridge up. **Not tested.**
  - **User test:** the sleepers showed at the triggers, one by one. CC2 un-hides
    its character once the outfit loads. **Fix** ("apply and run"):
    `AEnemyBase::SetActorHiddenInGame` override keeps sleepers hidden.
    Rebuilt (18 s); DLL 00:39:20 is newer than the source (00:38:55); bridge
    up. **Not tested.**
  - **`Lvl_Sandbox` first group not chasing:** caused by the navmesh's
    `bForceRebuildOnLoad` (full rebuild at load). The user unticked it,
    rebuilt and saved (00:33). **Not tested.**
- **Controller aiming** (user: "I need soft lock for controllers, Its hard to
  aim on controller at the moment. Also turning and aiming feels stiff").
  - **Choices (asked):** snap on aim, slowdown and follow; while aiming and
    in hip-fire; medium.
  - **Stiffness found:** the stick turned in degrees per frame through the
    legacy ×2.5 input scale.
  - **New:** `UGamepadAimComponent`, with stick turning in degrees per real
    second (curve, boost, slower while aiming) plus the soft lock. "apply
    and run".
  - **Build:** rebuilt (18 s); DLL 22:02:51 is newer than the source
    (22:01:57); bridge up.
  - **Tested in the editor:** "autoaim works". Mid-dive, LT snaps already
    (no zoom for pistols); the user turned down a dive lock and an
    automatic snap on diving, and left the magnifying guns' mid-dive zoom
    as is.
  - **User:** set the gamepad look mapping's Scalar to 1 if it has one.

- **Session end (2026-10-28, 01:45):** "lets do it tomorrow". Built and
  packaged today: encounter reserves (director and triggers), sleepers kept
  hidden against CC2, controller aiming, the level-start black screen, body
  LODs at 3, and the `Lvl_Sandbox` navmesh saved (user). Deck-confirmed:
  director spawn hitch, aiming, chinos. Waiting on the 01:16 build's
  results and a trace. Nothing committed since `6efc1724` (the user
  commits).

- **One-button roll / crouch, stick-release kneel (2026-10-28)** (user: the
  held roll button for the kneel is hard on a controller, since the right
  thumb is aiming; "I want the crouch and roll on the same button, If the
  player has no (use a threshold) input crouch, otherwise roll").
  - **Roll button:** rolls when the stick is past `RollInputThreshold` 0.3,
    otherwise acts as the crouch key.
  - **Kneel:** let go of the stick mid-roll to kneel; it stays down until
    the stick (after the slide), crouch, or another roll.
  - **Build:** "apply and run"; rebuilt (30 s); DLL 10:22:06 is newer than
    the source (10:21:20); bridge up. **Tested:** "roll works, kneel works".
  - **User:** in `IMC_Default`, Roll on one pad button; crouch can come
    off the pad.
- **Fire delay after a roll (2026-10-28)** (user: a couple of frames of shots
  into the ground as a roll hands back; "delay allowance to shoot a split
  second, or make tunable").
  - `URollComponent::FireDelayAfterRoll` 0.2 s (game time), set in `EndRoll`;
    `DoFire` checks `IsBlockingFire()`.
  - **Build:** "apply and run"; rebuilt (17 s); DLL 10:37:38 is newer than
    the source (10:37:13); bridge up. **Tested:** "no more ground shots but I
    tuned it". The user set their own `FireDelayAfterRoll` on the player
    Blueprint; the code default stays 0.2.

- **Fourth Deck build (10:59) + trace (11:15, 2026-10-28):** the room-spawn
  hitches are gone (no enemy built outside loads; 2 frames over 33 ms in
  3 min, worst 34). The death-restart load freeze is 800–830 ms on the old
  level's last frame; the fade-out before reload is now worth doing. Spec:
  *Third Deck trace*. Insights closed after export.

- **Black screen waits for the outfits (2026-10-28)** (user: the player popped
  in after the fade, the gun floating first).
  - **Cause:** the pause stalled the Character Customizer's Delay/timers,
    so outfits went on after the fade.
  - **Now:** no pause, the player's input off, and the fade waits for
    everyone shown with a body plus 0.5 s steady (cap 4 s).
  - **Build:** "apply and run". The first build failed on my lambda
    parameter shadowing `AController::Character`; renamed, rebuilt (6 s);
    DLL 11:26:45 is newer than the source (11:26:39); bridge up. **Not
    tested.**

- **Enemies held until the fade completes (2026-10-28)** (user: "they moved
  on me before the fade is done").
  - **New:** `ULevelStartSubsystem` hold, on from the player controller's
    `PostInitializeComponents` and off at the end of the fade. The AI
    behaviour start is queued; the enemy tick is skipped.
  - **Build:** "apply and run"; rebuilt (16 s); DLL 11:33:32 is newer than
    the source (11:33:05); bridge up. **Not tested.**

- **Uzi replaces the MAC-11 (2026-10-28)** (user: "I want to replace the
  Mac11 with an Uzi"; the MAC assets stay, unused, for now).
  - **Rig:** the CGTrader "rigged" FBX was loose parts with no skeleton.
    Rigged in Blender with `ArtSource/Weapons/Uzi/RigUzi.py`: 7 rigid bones,
    stock dropped (user).
  - **Assets:** imported over the bridge to `/Game/MicroUzi/` (`SK_Uzi`,
    `SM_Uzi_Mag`, `MI_Uzi`, textures at 1024). LODs 50/33/25 with Lock Mesh
    Edges, and the sockets, by the user.
  - **Blueprints:** `BP_Uzi` / `BP_DualUzi`, duplicated from the MACs. The
    grip rotation turns the +X barrel to the project's +Y; the intake
    checklist's "+X" was wrong and is corrected. Grips tuned, and
    `SK_Uzi_Fire` (Fire + Eject) added, by the user.
  - **Cleanup:** the folder's 13 unused first-import assets (12 loose parts
    and the `UZI` material) were deleted over the bridge (user: "delete
    anything that is not being used").
  - **Enemies:** `Lvl_Sandbox`'s `EncounterDirector` `WeaponPool` swapped
    `BP_MAC11` → `BP_Uzi` over the bridge, but **it is not on disk**. The
    actor's file (`__ExternalActors__/…/9/3Y/KJ4PQW6EIDQPYM8PA5TIB8`) is
    still the 10-23 version with the MAC, because the bridge's edit didn't
    dirty the package, so Save skipped it (same as the navmesh, spec
    *Gotchas*). **Fixed:** the user re-picked the entry and saved (17:52).
    The file now holds `BP_Uzi`, no MAC.
- **Ready pose and lock-back on empty (2026-10-28)** (user: "The default pose
  of the pistol should be hammer back"; slides lock back when empty).
  - **Code:** `ReadyPose` + `LastShotAnimation` on `AWeaponBase`. For duals
    the last-shot animation plays when the rounds left are fewer than the
    guns (the user's rule).
  - **Build:** "apply and run"; built clean; DLL 16:07:51 is newer than the
    source (16:06:27); bridge up.
  - **Wired over the bridge, tested by the user ("works"):**
    - the 1911 trio: `SK_P1911_ReadyPose` + the kit's
      `Anim_P1911_M_Shot_Empty`, with notifies added by the user;
    - the 9mm pair: `SK_Beretta_92FS_ReadyPose` +
      `SK_Beretta_92FS_FireEmpty`.
  - **Weapon picks (user):** a **Benelli M4** replaces the SPAS-12 plan,
    and an **SVD** is the sniper; both lock back. Not needed for the Uzi
    (closed bolt), the AK-74u, the Mossberg or the revolver. Spec: *Ready
    pose and lock-back on empty*.
- **Mossberg:** Eject notify added on `Mossberg-500_Pump` (user), so the
  casing is timed to the rack.
- **Pushed (2026-10-28, user):** `36bc08ba` "Weapon Updates. Roll Update" on
  `feature/HardwarTargetAdjust`. It holds all of the above plus the morning's
  roll/crouch, fire-delay and level-start work, and `.gitattributes` gains
  `*.blend` → LFS. The doc edits made after it (this entry, the director
  fix notes) are uncommitted.
- **Fifth build, `Lvl_Sandbox`, no trace (2026-10-28):** user: "Package me
  a build for Sandbox, no trace". Same packaging as before (editor closed,
  archived to `ProjectBopis_Builds/DeckTest/`); start command with
  `Lvl_Sandbox` and no `-trace`.
  - **Result:** BUILD SUCCESSFUL in 2 min 37 s; cook 0 errors and 13
    warnings, all old (unsaved ammo-pack meshes, a CC smartphone animation,
    two Blueprint member references, the MCP plugin notice); 2.23 GB. The
    editor was reopened afterwards.
  - **Shell note:** run `RunUAT.bat` from PowerShell (`& $uat @args`).
    Through Git Bash's `cmd //c` the quoted path breaks ("is not
    recognized").
- **First aid (2026-10-28)** (user: "Healing item, we only have one … heal on
  tap. Max 3, heals half health").
  - **Choice:** gin (user: "I dont want a drunkard label") and painkillers
    were dropped. The user chose "just use first aid then. No animation,
    just a sound cue and momentary white screen". Design notes Part 4,
    *Healing*.
  - **Build:** "apply and run"; rebuilt in 28 s; DLL newer; bridge up.
    Kits are an ammo-pool type, `EAmmoType::FirstAid`. Spec: *First aid*.
  - **Assets (bridge):** `IA_Heal`, `BP_FirstAidPickup` (the user's
    UltimateHealthPack `SM_FirstAidKit`), and the cap of 3 and `HealAction`
    on both player Blueprints.
  - **HUD:** the count moved off `UHealthWidget` to its own `UFirstAidWidget`
    (user: "Do not shove it into WBP Health"). "apply and run"; rebuilt in
    18 s; DLL newer; bridge up.
  - **User setup:**
    - `IA_Heal` mapped in `IMC_Default`;
    - `WBP_FirstAid` (parent `FirstAidWidget`) placed in `WBP_PlayerHUD`;
    - `FirstAidSound` set to the engine's `1kSineTonePing`, a placeholder;
    - `BP_FirstAidPickup`s placed in `Lvl_Linear`.
  - **Tested (user): "first aid tested, works".** Plan item 36 is done.
  - **Open:** a real heal sound; kit sources (placed only, or enemy drops
    too) and the starting count are design calls.

## 2026-10-29
- **Ammo split** (user: "the 9mm pistol and .45 pistol have split ammo";
  the Uzi is renamed Machine Pistol and a later MP5 is the Submachine Gun, with
  "Machine Pistol Ammo and Submachine Gun ammo" split; "add ammo for SVD
  sniper"). Plan item 37; spec *Ammo split*; design notes Part 4.
  - **Build:** "apply and run"; built in 28 s; DLL 21:16:56 is newer than the
    source (21:16:14); bridge up.
  - **Code:** `EAmmoType`: `Pistol` → `Pistol45`, `SMG` → `MachinePistol`;
    new `Pistol9mm` and `SubmachineGun`; defaults are `Pistol45`.
  - **Redirect:** an enum redirect in `DefaultEngine.ini` loaded the old
    names cleanly.
  - **Bridge, saved:**
    - the 9mm pair → `Pistol9mm`;
    - the Uzis, MAC-11s and SMG box → `MachinePistol`;
    - new `BP_AmmoPickup_9mm` (24) and `BP_AmmoPickup_Sniper` (12);
    - a `Pistol9mm` cap of 180 on both players. `BP_Player_CC` keeps its own
      cap map, so it needed setting separately.
  - **Checked:** no saved file still has the old names.
  - **Boxes (user: "do the renames, make the boxes too"):**
    - renamed to `BP_AmmoPickup_45` and `BP_AmmoPickup_MachinePistol`; the
      old paths are redirectors, used by six placed boxes in `Lvl_Sandbox`;
    - new rifle (30), auto shotgun (12) and pump shotgun (8) boxes;
    - every new box got an AmmoSet calibre mesh.
    No C++ was needed.
  - **Not yet tested by the user.**
- **Gameplay message feed** (user: "a general message UI like 'Picked up x
  ammo', 'Quick Saved' … stack … 5 messages at once"). Plan item 38; spec
  *Gameplay message feed*.
  - **Build:** "apply and run"; built in 21 s; DLL 21:47:12 is newer than the
    source (21:46:39); bridge up.
  - **Code:**
    - `UGameMessageSubsystem` on the local player: `ShowGameMessage`, 5 lines
      kept, 3 s each in real time;
    - `UGameMessageWidget`, which drives Text Blocks `Message_0`..`Message_4`
      and fades them out;
    - `AAmmoPickup::PickupMessage`.
  - **Bridge, saved:** messages on all 10 ammo boxes and the first-aid box.
  - **Merging** (user: "if the same message appears, i want it to update the
    number of the existing message … push it to the start of the stack").
    - **Build:** "apply and run"; built in 17 s; DLL 22:17:35 is newer than
      the source (22:17:09); bridge up.
    - **What it does:** `ShowCountedGameMessage` keys a line on its pattern
      and adds to the live total, moving the line to the newest place with
      its time reset. A repeated plain message refreshes its line.
    - **Pickups** use it.
  - **User:** "widget made, pickups tested, works".
  - **Weapon pickups** (user: "weapon pickup do not give me a message, if I
    already have the weapon it should give me the picked up ammo message as
    well").
    - **Build:** "apply and run"; built in 18 s; DLL 22:35:26 is newer than
      the source (22:34:58); bridge up.
    - **Messages:** "Picked up {DisplayName}" for a new gun or the dual
      unlock. A gun already carried gives the ammo message.
    - **Wording:** ammo wording moved to one table in code
      (`ShowAmmoMessage`), so box and gun lines merge. The per-box
      `PickupMessage` field was removed.
    - **Tested (user): "weapon pickups tested, works".** Plan item 38 is
      done; save messages wait for a save system.

## 2026-10-30
- **Benelli M4 skeletal mesh** (user: "I added the BenelliM4 but its all
  separate parts as well with no skeleton. See if you can build a skeletal
  mesh yourself please"). Plan item 33; spec *Benelli M4*.
  - **Rig:** `ArtSource/Weapons/BenelliM4/RigBenelli.py` (headless Blender,
    the Uzi's pattern) turns 28 loose parts with a shared pivot into
    `SK_Benelli`.
    - **Bones:** `root`, `bolt`, `trigger`, `carrier`, `shell`, placed from
      each part's shape.
    - **Mesh:** 3 slots, 31.5k triangles, 76 cm long.
    - **Checked:** renders at rest and posed.
  - **Textures:** `PackORM.py` packs AO, roughness and metallic into ORM
    maps.
  - **Bridge, saved:**
    - the import;
    - ORM texture settings;
    - normals green-flipped (they're OpenGL);
    - `MI_Benelli_Body/Stock/Shell` on `M_TacticalPistol`, assigned.
  - **User next:**
    - look it over;
    - LODs (31.5k triangles, Lock Mesh Edges);
    - the sockets;
    - keep or drop the side-saddle shells.
  - **Then (ask):** wire `BP_Shotgun`, and clean up the first-import
    assets.
  - **LOD0 (user):** reduced to about 8k triangles, "still looks ok". The
    side-saddle shells stay. On disk, `SK_Benelli` was still the 09:56
    import when this was noted, so it needed a save in the editor.
  - **Root moved into the pistol grip** (user). The script shifts the gun so
    the grip's middle is the origin.
  - **Pump: none.**
    - The user asked for a rigged forend, then: "No Pump, IF the M4 Super 90
      can function without pumping". It can, being gas-operated.
    - The forend bone was taken back out. Renders also showed the model has
      no room for a stroke and no tube under the forend.
  - **User next:** right-click `SK_Benelli` → Reimport (the 10:29 FBX), then
    save.
  - **User:** "reimported and saved, sockets added". On the mesh:
    - `MuzzleFlash` (55, 0, 8), `AmmoEject` (15, 0, 8) and `LeftHandGrip`
      (27, 0, 5), all on `root`;
    - 3 LODs.
  - **`BP_Shotgun` wired** (user: "wire up BP_Shotgun"; bridge, compiled,
    saved).
    - **Mesh:** `SK_Benelli` at scale 1.2, single-node mode.
    - **Fire animation:** cleared, which also fixes the placeholder's
      silent shot and double flash.
    - **Pump bone:** cleared.
    - **Grip:** (0, 0, 0) / (−8, 87, 0), the Uzi's rotation, as starting
      values.
    - **Not yet tested by the user.**
  - **Left hand like the pump shotgun and the M4** (user; bridge, saved).
    - The Mossberg's tuned `LeftHandGrip` was converted onto the Benelli:
      (18.6, −5.5, 7.5) / (−29, 61, 103), and `bLockLeftHandRotation` is on.
    - Its source FBX was read in Blender to confirm the `pump` bone's frame.
    - This replaced the user's in-progress socket at (26, −1, 7).
    - **Tested (user): "left hand tested, works".**
  - **Animations** (user: "do the animations").
    - **Script:** `AnimBenelli.py` keys the rig. `A_Benelli_Fire` (the
      bolt cycles 6 cm, the trigger pulls), `A_Benelli_LastShot` (the bolt
      held 5.5 cm back) and `A_Benelli_Ready` (the bind pose), at 60 fps.
    - **Import (bridge):** onto `SK_Benelli_Skeleton`. The importer needs a
      mesh in the FBX, so the spare meshes it made were deleted and the
      `_Anim` assets renamed.
    - **`ReadyPose`** is set on `BP_Shotgun`.
    - **Waiting on the user:** `Fire` + `Eject` notifies on the fire and
      last-shot animations. Then the bridge wires them; until then the shot
      sounds from code.
    - **User: "notifies added".** A byte check found `Fire` + `Eject` in
      both. The bridge set `FireAnimation` and `LastShotAnimation` on
      `BP_Shotgun` (saved 11:41).
    - **Tested (user): "tested, works".**
  - **Cleanup** (user: "do the cleanup"; bridge).
    - **Deleted:** 45 first-import assets (28 static parts, 5 Phong
      instances, 12 Metallic/AO/Roughness/Specular textures). The asset
      registry showed no outside referencers; none blocked, none failed.
    - **Left:** `/Game/BenelliM4/` is 17 assets, 71 MB (was 102 MB).
  - **Benelli M4 is done** (plan item 33). Open: an optional 2K reimport of
    the kept textures.
- **Magazines** (user: "Change pump to 6 shots, M4 to 8"; bridge, saved):
  `BP_Shotgun` (Benelli) 8, `BP_PumpShotgun` 6.
- **Gun animation pass** (user: "go through the animations I made for the
  pump, beretta 9mm, 1911 and M4 … and tweak them? Your anim changes on the
  Benelli looks more convincing").
  - **What's wired now:**
    - pump: `Mossberg-500_Pump`, 0.67 s, keyed in the editor;
    - Beretta: `SK_Beretta_92FS_Fire` and `_FireEmpty`, 0.23 s, editor;
    - 1911: `Anim_P1911_M_Shot` and `_Shot_Empty`, 0.75 s, from the kit,
      with the user's notifies;
    - M4: `SK_AR4_Fire`, 0.23 s, editor.
  - **Blocker:** the bridge can't read or write animation keys. Only the
    Mossberg's source rig is on disk; the Beretta, 1911 and AR4 sources are
    on the pack authors' machines.
  - **Plan:** the user exports the six animations to FBX. Blender reworks
    them in the Benelli's style (fast linear slam back, brief hold, quick
    return). The user reimports each onto its own asset (Reimport → new
    file), which keeps the notifies.
  - **Exports in** (`ArtSource/Weapons/AnimPass/`).
    - **Static exports:** the Beretta, AR4 and Mossberg came out static.
      Editor-keyed animations keep their keys in a layer the FBX export
      skips, so these three were rebuilt from the rest pose. The 1911 is the
      kit's FBX animation; its values were kept, but it's retimed with the
      shot on frame 0 and the tail cut.
    - **The reimport plan changed:** the new animations are new assets,
      because a reimport onto the old assets would have stacked the old
      editor layer on top.
  - **Built:** `AnimPass.py` made seven animations; each checked by
    re-import and renders.
    - The 1911 trigger is cut to 3.5 mm (it hid inside the frame).
    - The AR4 dust cover is 150° open on every frame.
  - **Imported (bridge, saved)** onto each gun's skeleton.
  - **Waiting on the user's notifies:** `Fire` f0 + `Eject` f2, and for the
    Mossberg `Fire` f0, `Pump` f5, `Eject` f11. Then the bridge wires them.
  - **Beretta barrel recoil kept** (user: "keep it").
  - **User: "notifies added".** Bytes show `Fire` + `Eject` on five. Wired
    (bridge, saved):
    - the 9mm pair: Fire, LastShot and `A_Beretta_Ready`;
    - the three 1911 Blueprints: Fire, LastShot;
    - `BP_CloseRangeRifle`: Fire.
  - **`A_Mossberg_Fire` had no notifies** (not on disk, nothing unsaved), so
    `BP_PumpShotgun` stays on `Mossberg-500_Pump`.
  - **Then:** the user saved `Fire` + `Eject` on it, and `BP_PumpShotgun`
    is wired (bridge, saved). No `Pump` notify shows in the file; the rack
    is silent until one is added at f5.
  - **`Pump` added** (bytes confirm `Fire`, `Pump`, `Eject`).
  - **Tested (user): "tested all, works".** The animation pass is done.
  - **Old animations deleted** (user: "delete the old animations"; bridge,
    referencer-checked): six went.
    - **Stuck:** `Anim_P1911_M_Shot` (held by the kit's unused montage,
      whose delete didn't take). The user can delete both in the Content
      Browser.
    - **`AR4HatchOpen` is in use** (the rifle mesh's Anim to Play). Kept,
      pending the user's call.
  - **Uzi** (user: "Check the Uzi anims too").
    - `SK_Uzi_Fire` ran 0.233 s against a 0.06 s fire rate, so bursts only
      showed its start.
    - `AnimUzi.py` → `A_Uzi_Fire`: 0.05 s, the bolt 4.5 cm back at f1 and
      home at f3. Render-checked and imported (bridge, saved).
    - **Waiting on the user:** `Fire` f0 + `Eject` f1. Then it's wired onto
      both Uzis and `SK_Uzi_Fire` is deleted.
    - **Done:** the user added the notifies; `BP_Uzi` + `BP_DualUzi` are
      wired (bridge, saved) and `SK_Uzi_Fire` is deleted.
    - **Tested (user): "tested, works".**
  - **`AR4HatchOpen` cleared and deleted** (user: "clear the hatch and
    delete it"; bridge, saved). The rifle spawns with the cover shut and
    the first shot opens it.
    - **Tested (user): "tested, works".**
- **`ArtSource/` and the repo** (user asked whether it goes in). It does:
  it's been tracked since `9f72cd7e` (2026-10-23).
  - **LFS:** `.fbx` (also `.FBX`, since `core.ignorecase` is true),
    `.blend` and `.png` go through LFS. The `.py` scripts are plain git.
  - **Not in the game:** it sits outside `Content/`, so it never ships.
  - **New today, untracked:** `ArtSource/Weapons/BenelliM4/`,
    `ArtSource/Weapons/AnimPass/`, `Uzi/AnimUzi.py`, `Uzi/A_Uzi_Fire.fbx`.
    About 28 MB for the whole folder.
  - **Gap:** `RigBenelli.py`, `PackORM.py` and the Mossberg check read
    sources in the user's Downloads (`Downloads/BenelliM4/`,
    `Downloads/Mossberg/`). Those aren't in the repo, so rebuilding the
    Benelli on another machine needs them copied into `ArtSource` first.
  - **Closed for the rig** (user: "copy the Benelli FBX into ArtSource"):
    `Shotgun+2.fbx` is in `ArtSource/Weapons/BenelliM4/Source/` (MD5
    matches). The texture PNGs stay in Downloads.
- **The last two 1911 assets deleted** (user: "can you delete those 2").
  - `Anim_P1911_M_Shot` went on the retry.
  - The montage's file survived two force deletes, as the editor was likely
    holding it. It was already gone from memory, so the orphaned `.uasset`
    was removed from disk.
  - git shows all three kit files deleted.
- **Long guns, left hand in the back dive and prone poses** (user: "left
  hand is not reaching the left hand grip"; the item deferred on 10-26).
  - **Cause:** the arm turns and the back lift turn each upper arm about its
    own shoulder, so off the shoulder line the grip drifts out of the left
    arm's reach. The IK then straightens the arm and stops short.
  - **First try, removed:** pulling the gun in toward the left shoulder (a
    Two Bone IK on `hand_r`). The left hand reached, but in those poses the
    shoulder is toward the head, so the stock went through the head.
  - **Fix:** `UpdateShootdodgeLeftHandSlide`. The gun stays put and the left
    hand's target slides back along the barrel (max 15 cm) until it's in
    reach. The dive's left-hand IK (`TwoBoneIK_3`) reads
    `ShootdodgeLeftHandGripLocation`. "apply and run": compiled, rewired and
    saved.
  - **Tested (user): "tested, works... not perfect but serviceable".**
    Tuning, if it's revisited: `LeftHandMaxSlide`, `LeftHandReachMargin`.
- **Reload speed follows Focus** (plan item 39; user: "When on focus, your
  reload speed is accelerated... should work both ways").
  - **Design change:** reloading no longer ends Focus. The lore notes and the
    GDD (md + html) are updated.
  - **Code** ("apply and run", built): `FocusReloadSpeed` 3. The player
    re-picks the reload speed every frame (air 3, Focus 3, else 1). A change
    mid-reload rescales what's left of the weapon timer and the montage
    together, from where they are.
  - **Tested (user): "tested, works".**
- **Dragunov from the sniper pack** (user: "the Rifle, mag and scope are
  separate meshes. Can you help normalize this to our specs?").
  - The user exported the three pieces to `ArtSource/Weapons/Dragunov/Source/`.
  - `RigDragunov.py` merges them where the pack's `BP_Sniper` holds them.
    The barrel was already +Y and cm; the root is in the pistol grip; bones
    `root, bolt, trigger, magazine`; slots `Body, Scope, Lens`. 26.8k
    triangles. Render-checked at rest and posed.
  - **In Unreal (bridge, saved):** `/Game/Dragunov/` has `SK_Dragunov`,
    three material instances on `M_TacticalPistol`, the textures (moved in,
    max 2048) and `SM_Dragunov_Mag` for the magazine drop.
  - **User:** LODs and sockets added. **`BP_BattleRifle` wired** (bridge,
    saved): `SK_Dragunov` at 0.93, magazine 10 with the magazine drop,
    left-hand lock (Mossberg rotation, socket moved beside the handguard),
    grip offset zeroed, fire animation cleared. The sniper box now gives 10.
    `Magazine` socket added. **Tested (user): "tested, works".**
  - **Animations** (user: "do the animations"): `AnimDragunov.py` →
    `A_Dragunov_Fire`, `A_Dragunov_LastShot` (bolt held at 7.5 cm) and
    `A_Dragunov_Ready`. Round-trip and render-checked, imported and saved.
    The user added `Fire` + `Eject`; **wired onto `BP_BattleRifle`**
    (bridge, saved). **Not yet tested.**
- **Weapon Blueprints renamed by role** (user: "rename all the Weapon
  Blueprint appropriately … Use By Role, Remove the Mac Already"). Eight
  renames, e.g. `BP_Shotgun` → `BP_AutoShotgun` and `BP_BattleRifle` →
  `BP_SniperRifle`; the map is in the spec, *Weapon Blueprint names*.
  Referencing Blueprints saved; the levels go through redirectors until a
  *Fix Up Redirectors*.
  - **MAC-11 removed:** both Blueprints and the bundle's `SMG11` assets.
    Three stayed loaded in the editor (user to delete).
  - **Design (user):** "The M4 Stays, that is the accurate rifle with less
    ROF, AK74u is fast fire rate, high damage but also inaccurate spread."
    Recorded in the lore notes and GDD.
  - **Next:** the AK-74u, from the FPS bundle ("can we make that next?").
- **AK-74u ammo and the carry caps** ("apply and run"; user: AK ammo "Its
  own"; "adjust the max ammo for all the weapons to be 5 magazines worth …
  use the Dual max as the mag … for uzis, use the dual as well").
  - **C++ (compiled):** `EAmmoType::Carbine` (5.45); the rifle message now
    says "5.56 rounds" and the carbine's "5.45 rounds".
  - **Bridge (saved):** both players' caps set to five magazines (table in
    the spec, e.g. .45 80, 9mm 160, Uzi 320, rifle and carbine 150, SVD
    50); new `BP_AmmoPickup_Carbine` (30).
  - **Not yet tested.** Next: `BP_AssaultCarbine`.
  - **"mag + 5x mag" (user):** already the case. The cap is on the reserve
    only, and the loaded magazine sits in the gun. Docs clarified, caps
    unchanged.
- **AK-74u built** (user: "go, make the AK-74u"; bridge, saved):
  - `BP_AssaultCarbine` on the bundle's `SK_KA74U_Y`.
  - **Sockets** carried over from the M4: same bundle, so the same bone
    frames.
  - **Magazine drop:** `SM_KA74U_Mag_Empty_X`, the variant built in the
    magazine bone's frame.
  - **Stats and ammo** as agreed; `Carbine` ammo.
  - **Sounds:** the AKM set. The shot cue got `ATT_Gunshot` and the voice
    limit.
  - **Test loadout:** added to `BP_Player_CC`.
  - **No fire animation:** the AK has no bolt bone.
  - **Found:** the M4's shot cue has no attenuation or voice limit; audit
    all fire cues.
  - **Not yet tested.**
- **AK made stockless** (user: "can we make the AK Stockless?"):
  - The user exported `SK_KA74U_Y`.
  - `StripStockAK.py` removed the stock and sling ring (1,175 vertices),
    leaving 50.3 cm and 8,927 triangles.
  - Imported as `/Game/AK74U/SK_KA74U_Stockless` on the same skeleton, with
    the sockets and materials copied, and swapped onto `BP_AssaultCarbine`
    (bridge, saved).
  - **Correction:** `b_gun_shelleject` is the bolt carrier with its
    charging handle, so a fire animation is possible.
  - **Tested** (user): "tested, works".
- **AK fire animation** (user: "do the fire animation"):
  - `ArtSource/Weapons/AK74U/AnimAK.py` → `A_AK74U_Fire`, 0.117 s. The
    carrier and charging handle go 8 cm back at frame 1 and are home by 4,
    inside the 4.5 frames between shots. The trigger is held to frame 5, so
    it doesn't flicker in a burst.
  - Checked by re-import (exact travel, nothing else moves) and renders
    (handle at the rear of the port, no clipping).
  - Imported (bridge, saved) to `/Game/AK74U/Animations/`.
  - **Gotcha:** the armature object is rotated, so the first test renders
    moved the carrier up. Pose in world space (spec *AK-74u*).
  - **Notified and wired** (user added `Fire` f0 + `Eject` f1, confirmed by
    bytes; "wire them up"): `BP_AssaultCarbine`'s `FireAnimation`
    (bridge, compiled, saved).
  - **Tested** (user): "tested, works".
- **In-game weapon names** (the user's table, "Real-world inspiration → In-game
  name"; bridge, compiled, saved):
  - .45 Pistol, 9mm Pistol, Pump-Action Shotgun, Semi-Auto Shotgun, AKS-74U,
    M4 Carbine, Sniper Rifle, Machine Pistol, .357 Revolver.
  - The dual pairs follow the "Dual … Pistols" pattern: Dual .45 Pistols,
    Dual 9mm Pistols, Dual Machine Pistols.
  - Canon in the lore notes, and the GDD (md + html) has the arsenal table.
    The spec maps each Blueprint to its name.
- **Pack cleanup** (user: "remove the unused assets in FPS pack except the
  knife. Remove the other unused assets in Sniper Pack"):
  - **What's used** came from a bridge-free reference scan of everything
    outside the packs: 41 of 273 assets.
  - **Deleted:** 232 assets, 573 MB.
    - The bridge took 199. The 33 still loaded (all git-tracked) were
      removed on disk after the user closed the editor.
    - All of `SniperRiflePack` is gone; the Dragunov never depended on it.
  - **Checked:** the bundle holds exactly the 41 used assets, with no broken
    references.
  - **Correction to what Claude first said:** most of it wasn't
    recoverable from git. The 199 the bridge deleted were never committed,
    so only Fab can bring them back.
- **Redirectors:** the user ran *Fix Up Redirectors* ("I did the redirection
  update already").
- **Kill cam** (user: "something similar to the kill cam in Max Payne 2 …
  if they are riddled state, you can keep shooting"; "slomo and flourish
  cam"; Claude given permission to build it "all the way to completion"):
  - `UKillCamComponent` on the player, compiled clean.
  - **When:** the player's kill that leaves its room done, with no one else
    alerted.
  - **What:** 0.15 slow motion while the camera swings round the body and
    pushes in. You can keep shooting: the shots go into the body and hold
    the cam.
  - **Spec:** *Kill cam*. Not yet tested.
  - **Build gotcha:** `IsActive()` clashes with `UActorComponent`'s, so it's
    `IsPlaying()`.
- **Damage flash** (user: "red screen flash on death and on damage that does
  more than 25% health in a short period"; "let me tweak the damage window
  and the Red color"):
  - Built with the kill cam, on the player under *Health|Damage Flash*.
  - Everything is editable, the colour as a black → red slider.
  - **Spec:** *Damage flash*. Not yet tested.
- **To do: MP5** (user: "Add MP5 SMG. A fast laser accuracy low damage
  SMG"). It's plan item 40, the Submachine Gun of the ammo split. Not built:
  there's no MP5 model in the project, so the user supplies one. Recorded in
  the lore notes, the GDD and the spec (*MP5 (planned)*).

## 2026-10-31
- **Kill cam and damage flash tested** (user: "tested, only issue is on the
  final event, where 2 enemies talk"). Plan items 41 and 42 are done.
- **The final talk's room never played the kill cam,** whether the talk was
  broken up or allowed to finish:
  - **Setup in `Lvl_Linear`:**
    - `EncounterTrigger4` spawns Goon1 and Goon2 as patrollers and hands
      them to `DoorTrigger2`.
    - `DoorTrigger` starts the talk.
    - The talk's last step sets off `DoorTrigger2`.
  - **Cause:** `DoorTrigger2` had a blank Spawns entry, with no class and no
    point. An unfired trigger with any Spawns never counts as done, and a
    broken-up talk never fires it.
  - **Fix:** the user removed the entry ("its doing it now"). No code
    changed. The diagnostic log Claude offered isn't wanted.
  - **How it was found:** read straight from the saved `.umap` with a
    throwaway Node parser, without the bridge.
  - **Also noticed:** the talk's 5th step is an empty Say Line with no
    speaker and no subtitle, so it's skipped. Left to the user.
- **Open design question, not decided:** a broken-up talk doesn't set off
  the fight it was leading to (spec *Kill cam*).
- **Kill cam camera guardrails** (user: "he penetrates through walls and
  sometimes goes into the enemy model … stop the spin and linger on the
  angle"):
  - Applied by Claude on the user's say-so ("apply it and run the script").
  - **Build:** compiled clean. The DLL (01:41:04) is newer than the source
    (01:39:23), the bridge answered, and the editor log is clean.
  - **The swing:** every frame the next spot must have room (12 cm clear of
    walls and the player) and a clear line to the body. The first blocked
    spot stops the swing for good, and the camera holds its last clear spot,
    still watching the body.
  - **The start:** it searches round the body for a clear spot. If there
    isn't one anywhere, there's no cam.
  - **Spec:** *Kill cam → Guardrails*.
- **Kill cam shot styles** (user: the current one "under 'Orbit Cam'",
  plus a "Reverse Shot Cam … from the Enemy Angle" and a "Steady Cam where
  you go to a higher angle, follow the enemy but no cam movement"; "add
  random option as well"; "pick on the cleared section of the trigger"):
  - Applied by Claude on the user's say-so ("go do it").
  - **Build:** compiled clean. The DLL (02:00:56) is newer than the source,
    the generated code has the enum and the trigger's settings, the bridge
    answered, and the log is clean.
  - **What's in:**
    - `EKillCamStyle`: Orbit / Reverse Shot / Steady / Random.
    - The player's `Style` is the default.
    - Each trigger has a ticked `KillCamStyle` under *Encounter|Cleared*.
    - A style with no clear spot plays as Orbit.
  - **Interpretation, open to change:** Claude built the Steady Cam as a
    still camera that only turns to follow the body.
  - **Docs:** recorded in the lore notes (*Kill cam*). The GDD (md + html)
    has the three shots and a changelog line. Spec: *Kill cam → Shot
    styles*.
- **Bug: diving into a reverse shot aimed the arms behind the player**
  (user: "the aim get steered to where the crosshair would have been
  instead of locking on to the enemy"):
  - **Cause:** the anim's aim corrections followed the camera's view, which
    is the kill cam's. That covers the dive, the duals' dive spread and the
    one-handed pistol.
  - **Fix:** while the cam plays, they aim from the player's own camera at
    the body (`GetCrosshairView`).
  - **Build:** applied by Claude on the user's say-so, compiled clean. The
    DLL (02:09:21) is newer than the source, the bridge answered, and the log
    is clean.
  - **Added beyond what was shown:** a forward declaration
    `class APlayerController;` in `ProjectBopisAnimInstance.h`, for the new
    reference parameter.
- **"The orbit cam cuts off sometimes."** Two of Claude's rules end it
  early:
  1. **Anyone alerted.** Gunfire alerts listeners within 30 m, including
     the kill shot and the shots fired during the cam. The user said "keep
     1", so it's unchanged.
  2. **A stopped swing that loses sight of the body.** Changed (user:
     "apply the suggested rule for 2, but instead of ending abruptly, try
     swinging the cam back the other way"):
     - It now waits 0.3 s, then swings back the other way once, from where
       it stopped.
     - Swinging back, it may be blind for up to 1 s.
     - Still shots get the same 0.3 s before ending.
  - **Build:** applied by Claude on the user's say-so, compiled clean. The
    DLL (02:32:59) is newer than the source, the bridge answered, and the
    log is clean.
  - **Spec:** *Kill cam → Guardrails*.
- **Kill cam for encounter directors** (user: "dos the encountermanager
  get a kill cam?" → "yes add it, with its own style pick"):
  - **When:** a director with `TotalEnemies` > 0 plays it on the last kill,
    once all its enemies have come in and are down and no one else is
    alerted. Endless directors never do.
  - **Settings:** the director has the same *Encounter|Cleared* settings as
    a trigger: `bKillCamOnClear`, and a ticked `KillCamStyle`.
  - **Build:** applied by Claude on the user's say-so, compiled clean. The
    DLL (02:41:09) is newer than the source, the generated code has the
    director's settings, the bridge answered, and the log is clean.
- **Kill cam tested** (user: "tested, works. put that in the docs"). That
  covers the guardrails, the three styles plus Random, the per-room and
  per-director picks, the reverse-shot aim fix and the orbit swing-back.
  Plan item 41 is done.
- **Dying bodies through walls and floating** (user: riddled enemies
  "goes thru walls", and "on a slope or if he gets thrown by the death anim
  off a platform, enemy would float in the air"):
  - **Cause:** the death animations have root motion off, and a dead body's
    capsule has neither collision nor movement.
  - **Fix:** `IsDyingBodyAdrift()` turns a dying body that crosses a wall,
    or is off the ground, into a ragdoll.
  - **Build:** applied by Claude on the user's say-so, compiled clean. The
    DLL (03:00:57) is newer than the source, the bridge answered, and the
    log is clean.
  - **Spec:** *Taking bullets and dying → Dying bodies adrift*.
  - **Tested** (user: "tested, works. put that in the docs"). Plan item 43
    is done.
- **HUD: cinematic minimal (plan item 44, started):**
  - **The look** (user: "I want the cinematic minimal UI from this image"):
    panel 1 of a GPT mockup. A white/gold accent, a red health bar over a
    shorter blue Focus bar, then weapon icon, ammo, first aid and grenades.
  - **The art is GPT's.** The user generated a sheet (composite | HEALTH |
    FOCUS | ACCENT | EMPTY), and Claude cut it with `CutHUDSheet.py` into
    `ArtSource/UI/HUD/`:
    - seamless bar tiles (health, focus, empty);
    - the accent;
    - all 4× Lanczos upscaled (user: "upscale the png so we can 100% prevent
      pixelation").
  - **Bars of any length** (user: "extend the length of the bars without it
    looking stretched"). `M_HUDBar` draws the 45° ends, the end outlines and
    the fill front in pixels and tiles the texture. The Custom node code is in
    `HUDBar_Custom.hlsl`. It was checked in a numpy preview at 180–480 px, and
    against GPT's composite.
  - **Built later the same day** (user: "lets do this now"). Spec: *HUD:
    cinematic minimal*.
    - textures imported, `M_HUDBar` + both instances built (bridge);
    - `UHUDBarWidget` C++, applied on "apply and run script", compiled
      clean; `WBP_Health` / `WBP_Focus` swapped to the `Bar` Image by the
      user (user: "Done, it works");
    - `BarCluster` layout pasted into `WBP_PlayerHUD` from
      `Tools/MakeHUDBarClusterTree.ps1` (user: "Looks right");
    - `Brightness` on `M_HUDBar` (user: "is it possible to let me adjust the
      brightness of the UI element");
    - GPT's background layer cut to `T_HUD_Background` (BC7, not upscaled),
      on the new `M_HUDImage` / `MI_HUD_Background` with Brightness and
      Opacity (user: "can you do a brightness thing for the background as
      well").
  - **Antonio font** (user: "I have an antonio font added to the project, can
    you try it on all the UI elements?"). The user imported it into
    `/Game/antonio/` as one Font per weight. Through the bridge, all 23 Text
    Blocks in the five text widgets (ammo, first aid, game messages,
    subtitle, weapon wheel) went from Roboto to Antonio of the same weight
    and size, compiled and saved. The wheel's paste script writes Antonio
    now too. Same sizes, checked in PIE (user: "Looks good").
  - **Item strip, started** (user: "here is the next thing we do", with
    GPT's weapon / first aid / grenade mockup). Spec: *HUD: cinematic minimal
    → Item strip*.
    - `CutHUDItems.py` cut the first-aid and grenade icons and measured the
      layout. The weapon icon is the equipped weapon's own.
    - `UAmmoWidget` now drives optional `WeaponIcon`, `MagazineText` and
      `ReserveText` itself (applied on "apply and run", compiled clean).
    - New `UHUDCountWidget` base (optional `Count` Text Block, virtual
      `GetCount`); `UFirstAidWidget` moved onto it and a new `UGrenadeWidget`
      added (applied on "apply and run", compiled clean).
    - Bridge: the two icons imported, `WBP_Grenades` created on
      `UGrenadeWidget`, compiled, saved. Paste-in trees for the three widgets
      (`Tools/MakeHUDItemTrees.ps1`) and `ItemStrip` in the cluster generator.
    - **Changed to separate pieces** (user: "I cant scale down the health and
      focus section uniformly?", "The weapon icon is the wrong size, I
      resized it myseld", then "just make separate widgets", "Each on its own
      piece. Also make the BarCluster a separate Widget that can be uniformly
      resized"; the user removed the old item widgets from the HUD, "You go
      and make them anew"). `WBP_WeaponIcon` (on `UAmmoWidget`) and
      `WBP_BarCluster` created through the bridge. Every piece's root is now a
      Scale Box, so its box in `WBP_PlayerHUD` sets its size. Both generators
      rewritten for the five widget trees. A generated starting layout for
      the HUD was offered and dropped (user: "Ill drag it by hand, forget
      this"). No C++ change was needed.
    - **Weapon icon: dual pistols + stroke** (user: "we need to indicate in
      the weapon icon that you are using dual pistols. Also can you add a
      stroke to the icon?"). A dual weapon shows its icon twice, the copy
      behind like on the wheel (`WeaponIconDual`, `DualIconSpread`); new UI
      material `M_HUDIcon` outlines any icon (`StrokeWidth` in screen px,
      `StrokeColor`), used by `MI_HUD_WeaponIcon`. C++ applied on "apply and
      run"; the first build failed (a parameter named `Padding` hid
      `UUserWidget::Padding`, renamed `SlotPadding`), the second compiled
      clean. The material's first compile failed too (`StrokeColor` wired
      from the RGB output; rewired to RGBA). `WBP_WeaponIcon` tree
      regenerated; the user re-pasted it.
    - **Stroke artifacts fixed** (user: "the stroke causes black artifacts",
      "no anti aliasing"). The Handcrafted weapon icons had no mipmaps and
      are drawn at ~1/10 of their size, so the icon and stroke aliased and
      faint specks became black dots. Mipmaps on for the 9 icons the
      weapons use (bridge, saved; UE 5.8 mips non-power-of-two textures
      without padding, so nothing else changes; the wheel benefits too), and
      the stroke now ignores faint alpha (`M_HUDIcon` updated, compiles
      clean). User: "it looks better with mip maps, but the black artifacts
      are still there": the icons were also set to Wrap, so each edge
      borrowed the gun from the opposite edge and the stroke outlined it.
      All 9 set to Clamp (bridge, saved). User: "that looks much better".
    - **One standard scale for the weapon icon** (user: "The long gun icon
      is tiny", then "let the long guns scale, pick a standard scale instead
      of resizing, just make sure it aligns, we will scale the whole UI so it
      all fits"). The Scale Box was fitting each icon inside the widget's
      box, so long guns shrank to its width. `WBP_WeaponIcon`'s Scale Box is
      now `Stretch` None: every gun 62 tall (`IconHeight`) at its own
      proportions, right-aligned and centred, long guns running left. No
      code change; generator updated, and the field set through the bridge
      (compiled, saved). Not yet checked in PIE.
    - **`WBP_ItemStrip`** (user: "I need to scale that entire section
      uniformly", "go do it via bridge"). Read the user's layout through the
      bridge: the bars at the left (already scalable on their own) and the six
      item pieces apart from them, further right. Those six became one widget
      with a Scale Box root, at the user's exact relative positions
      (generator: `MakeHUDItemTrees.ps1 -Clipboard ItemStrip`). The asset was
      created while PIE was running, so the bridge couldn't save it; the user
      saved it and pasted the tree.
    - **Pump shotgun icon swapped** by the user to `modern_shotgun__3_`. It
      got mipmaps + Clamp like the other weapon icons (the stroke needs
      nothing), and the old `ww1_shotgun__2_` went back to the pack's
      `NoMipmaps` / `Wrap` (user: "the old value rolled back"). Bridge, saved.
    - **AK74u icon swapped** by the user (`BP_AssaultCarbine` →
      `modern_rifle__3_`): mipmaps + Clamp (bridge, saved). The old
      `modern_rifle__12_` keeps its settings, since the assault rifle still
      uses it. Then swapped again to the user's own `T_Icon_AK74u` (RGBA,
      white on transparent, from `ArtSource/UI/Weapons/`): mipmaps + Clamp,
      and `modern_rifle__3_`, now unused, rolled back to `NoMipmaps` / `Wrap`
      (bridge, saved).
    - **Weapon wheel: mipmaps + stroke** (user: "Try to apply the mipmap and
      stroke to all the current possible icons on the weapon wheel"). The
      new melee icon `Fist` (the other session's quick-action segment) got
      mipmaps + Clamp. `UWeaponWheelWidget::ShowIcon` now feeds an
      `M_HUDIcon` brush through its `Texture` parameter, like the HUD's
      (applied on "apply and run", compiled clean; the other session was
      asked first and said it was done with the wheel files, and its changes
      were kept). `MI_HUD_WheelIcon` set on the wheel's 12 icon Images
      through the bridge, saved; `MakeWeaponWheelTree.ps1` matches. User
      checked it in PIE: "Looks right".
    - **Quick-action slot** (2026-11-01; user: "time to wire the selected
      item in 1 to reflect the item strip"). The strip's grenade piece now
      follows the wheel's slot-1 pick (`GetQuickAction()`, from the other
      session): grenade icon + count, or a melee icon with the count hidden.
      `UGrenadeWidget` C++ applied on "apply and run", compiled clean. New
      `T_HUD_Icon_Melee`, cut from the user's fist PNG by `CutHUDIcon.py`,
      imported; `WBP_Grenades`' `GrenadeIcon` / `MeleeIcon` set (bridge,
      saved). Also mipmaps (no stroke) on the HUD grenade and first-aid icons
      (user: "mipmap the grenade and first aid images too", "but dont
      stroke"). First PIE check: the icon didn't switch (user: "did not
      change the icon"); the copy of `WBP_Grenades` inside `WBP_ItemStrip`
      had kept empty icons when the defaults were set and compiled. Set on
      that copy too (bridge, saved). User: "Works now".
    - Dual pistol pair on the HUD checked (user: "dual pistols are fine in
      the HUD").
    - **Build break, from this session's edit:** `AmmoWidget.cpp` got its own
      file-local `IconAspect` (copied from `WeaponWheelWidget.cpp`'s). Once
      the user's commit put both files in the same unity-build file, the two
      same-named helpers collided (C2084), and the "Current Coding Work"
      session's rebuild failed with the editor closed. That session is
      proposing to rename the wheel's copy; this session agreed and held off
      rebuilding. Fixed by that session: the wheel's copy is now
      `WheelIconAspect` (`WeaponWheelWidget.cpp` only); built 00:36, the
      editor back up. Lesson: helpers in an
      anonymous namespace still clash across `.cpp` files that unity builds
      merge, so give them unique names or share one.
    - The GPT background is too short for the strip; it needs a longer one
      or stretching.
  - **Tried and dropped:**
    - a flag-triangle cap and a procedural grunge (files still in the folder,
      superseded);
    - Blender silhouette and line-art weapon icons (deleted; user: "Dont like
      em, lets use the icons instead" — the Handcrafted pack stays);
    - textured weapon renders through the editor viewport (user: "forget this
      actually"; deleted).
  - **Weapon icons in use** (listed for the user):
    - the revolver shares `modern_pistol__1_` with the enemy-only .45;
    - the rifle and the carbine share `modern_rifle__12_`.
  - **Bridge note:** this session's `unreal-mcp` tools dropped and didn't come
    back after a reconnect. Claude reached the editor's endpoint directly with
    a scratch client instead, which needs no repo files.
  - **Possible leftover:** `Lvl_Linear` may show unsaved changes from the
    render booth's spawn/remove. Its contents are unchanged, so save it or
    discard the changes.
- **Stiff pistol shoulder** (user: "when shooting pistols, I am not getting
  any motion on the shooting shoulder, it looks stiff"):
  - **Cause:** the blade's arm and hand aim corrections re-aimed the kicked
    pose at the crosshair every frame, so the kick was cancelled within
    about 0.1 s. The kick only ever bent the forearm.
  - **Fix:** the corrections hold while the recoil spring is up, and a
    one-handed shot now also lifts the arm at the shoulder
    (`BladeShoulderKick` 15°).
  - **Build:** applied by Claude on the user's say-so, compiled clean. The
    DLL (12:57:13) is newer than the source, the bridge answered, and the
    log is clean.
  - **Rolled back** (user: "The arm movement increased but I dont see the
    kick in the shoulder", "roll back the bladed fix"). Both anim instance
    files were restored from git; the change was never committed.
    - **What the user wants:** the shoulder itself (the clavicle) to move,
      not the arm.
    - **Deferred** (user: "dont fix the kick now").
    - **The editor DLL still has the rolled-back code until the next
      rebuild.**
- **Head bobbing on the bladed run** (user: "when running bladed raised,
  the head is bobbing up and down but the body is still"; "The bob is only
  for bladed stance").
  - **Not C++:** the blade's head turn is a constant, lean is off while
    raised, and head-look is for enemies.
  - **Bridge read of `ABP_Player`** (user: "go ahead with the bridge for
    the head bob"; read-only):
    - `LayeredBoneBlend_10` (`pelvis`) puts the mirrored strafe run on the
      whole body.
    - `TwoWayBlend_0` (by `StrafeBladeAlpha`) then picks `_13`: `spine_01`,
      mesh-space rotation, blend depth 3, laying the DefaultSlot hip-fire
      idle over everything from `spine_01` up.
    - Then the two aim offsets, the lean nodes `ModifyBone_36`–`38`
      (`spine_01`–`03`), and the blade turns: `_28`/`_29`
      (`spine_03`/`05`), `_30`/`_31` (`neck_01`/`head`), `_32`
      (`upperarm_r`), `_33` (`hand_r`).
    - Then the recoil nodes, the left-hand IK, the finger, free-arm and
      dual layers, `_4`, and Rotate Root.
    - Nothing after the blade layer moves the neck or head on its own.
  - **Bladed-only suspect:** `_13`'s blend depth 3 keeps about ⅔ and ⅓ of
    the run's sway on `spine_01`/`02`. (`_13` was made 2026-10-22 to spread
    the waist twist for the CC waistband.)
  - **Not the cause:** depth set 3 → 0 through the bridge and compiled.
    The user first reported "bob is gone, waist looks fine. saved it"
    (`ABP_Player` saved 13:44), then "bob is actually still there". The
    asset is saved at depth 0, and whether to put it back to 3 is open.
  - **Still open:** the graph shows no node that moves the head on its own
    in the bladed stance. Next: see it (a clip or screenshots), or test the
    CC head mesh's copied pose.
  - **Rebuild** (user: "run the script"): this clears the rolled-back kick
    code from the editor DLL. Compiled clean; the DLL (13:45:45) is newer
    than the restored source (13:29), the bridge answered, and the log is
    clean.

- **Bladed head bob, found** (user: "freearmphysics actually stopped it"):
  - **Cause:** `BP_Player_CC`'s head is a separate mesh copying the body's
    pose. When body bones simulate, the body's pose is only finished after
    the physics step, so the head copied last frame's and the neck
    stretched with every stride. The bladed stance is the free arm's case.
  - **Fix:** `ABopisCharacterBase::BeginPlay` puts the `Head`-tagged mesh in
    `TG_PostPhysics`. It also covers enemies' hit reactions and the
    riddled dance.
  - **Build:** applied by Claude on the user's say-so, compiled clean. The
    DLL (14:59:31) is newer than the source, the bridge answered, and the
    log is clean.
  - **Earlier tries that weren't it:** `_13` blend depth 0 (now back to 3),
    a neck freeze (removed) and a stride follow (rolled back).
  - **Tested** (user: "that looks fine now, put it back to 3"). `_13` is
    back to depth 3 through the bridge, compiled and saved.

- **Hit pulse** (user: "I need better feedback on when you are taking
  damage" → "do the hit pulse first"):
  - **What it does:** every hit reddens the screen's edges, more for a
    bigger hit, fading in 0.3 s real time.
  - **Material:** `M_HitPulse` (post process, a Custom node on the edge
    mask), built and saved through the bridge.
  - **Code:** a dynamic instance on the player camera's post-process
    blendables, driven by `PulseHit` and `Tick`.
  - **Assignment:** set on `BP_Player_CC` through the bridge, saved.
  - **Build:** applied by Claude on the user's say-so ("apply and run"),
    compiled clean. The DLL (15:49:43) is newer than the source, the bridge
    answered, and the log is clean.
  - **Spec:** *Damage flash → Hit pulse*. Recorded in the lore notes, and
    the GDD (md + html) has a sentence.

- **Damage feedback layers 2 and 3** (user: "do all the way up to 3"):
  - **Layer 2:** `HeavyDamageFraction` 0.15 and `HeavyDamageWindow` 0.5 on
    `BP_Player_CC` (bridge, saved).
  - **Layer 3:** below 30% health the edges stay red with a heartbeat throb
    (1→2 Hz) and the picture drains toward grey. `M_HitPulse` was extended
    through the bridge and saved, plus `UpdateLowHealth` in C++. The
    optional heartbeat sound has no asset yet.
  - **Build:** applied on the user's say-so ("apply and run"), compiled
    clean. The DLL (16:03:36) is newer than the source, the generated code
    has the new settings, the bridge answered, and the log is clean.

- **Low health at 20%, no heartbeat, out-of-combat recovery** (user: "no
  heartbeat sound. make the low health state at 20%, also gameplay change,
  if you go below 20% health and you go out of combat, recover health slowly
  up to 20% removing the low health state"; "need to be X amount of secons
  out of combat"; "use your shots, damage taken, and near misses instead"):
  - **Combat clock:** `NoteCombat()` is stamped by your shots, damage taken
    and near misses.
  - **Recovery:** after 5 s out of combat, health below 20% climbs at 2% per
    second, up to 20%, which fades the low-health look out.
  - **Build:** applied on the user's say-so ("apply and run"), compiled
    clean. The DLL (16:17:07) is newer than the source, the bridge
    answered, the log is clean, and `BP_Player_CC` was read back with the
    new defaults.

- **Low-health line to 30%** (user: "make the cap 30%"; "the low health
  status goes up as well"): `LowHealthFraction` 0.3 on `BP_Player_CC`
  (bridge, compiled, saved). The low-health look and the recovery cap share
  the line, so no code changed. The separate-cap code Claude presented was
  dropped before applying.

- **Recovery time doubled, damage feedback done** (user: "double the
  recovery time. And mark the task as done"):
  - `RecoverRate` 0.02 → 0.01 on `BP_Player_CC` (bridge, saved): 0 → 30%
    in 30 s.
  - Plan item 42b is done: hit pulse, heavy flash at 15%/0.5 s, low health at
    30%, out-of-combat recovery.

- **Pickups switch only to a better gun (plan item 46)** (user: "Only change
  the weapon when picking them up if they are better … determined by their
  number in the weapon selection and order in that particular section", plus
  the order per slot). `AWeaponBase::SlotOrder` + `RanksAbove`; the holder
  keeps `CarriedWeapons` sorted (`InsertCarried`), so the wheel and the slot
  keys follow the order too; `GiveWeapon` switches only to a higher rank.
  - Built on "apply and run": compiled clean, DLL 21:04:22.
  - `SlotOrder` on the 13 weapon Blueprints (bridge). The first save was
    refused while the editor was in Play, and redone after.
  - Not yet tested by the user.
- **New standing rule** (user: "coordiante with the other session to check if
  its safe to shut editor when you need to"): `Claude-Rules.md` §1. Before
  closing the editor, message the peer sessions and wait for their answer.
- **Melee and the slot 1 G-key switcher (plan item 47)** (user: "the 1 in the
  weapon wheel … will just be a switcher from melee and grenade"; "Propose a
  melee system"; "go with your picks, try to do it to completion, put a
  placeholder icon for now"; out of grenades "stay on grenade and do
  nothing").
  - **Built:** `EQuickAction` + `DoQuickAction` on G; wheel slot 1 flips
    Grenade/Melee; `DoMelee` plays Lyra's additive melee clips on the
    `Additive` slot at 1.5×; damage 35 + forced stagger (`UMeleeDamageType`);
    turn to the target; hit-stop; the trigger cuts the recovery after the
    blow lands. Spec: *Melee and the G key*.
  - **Build:** both peers said safe before the rebuild. Compiled clean on the
    first try (28 s), DLL 21:57:56, bridge up, log clean.
  - **Assets:** strikes on `BP_PlayerCharacter` + `BP_Player_CC`. The parent's
    values didn't reach the child, the known gotcha, so they were set on both.
    Wheel icons on `WBP_WeaponWheel`: the grenade, and a combat knife as the
    melee placeholder. All saved.
  - **First test** (user: "Needs sounds"; "I press 1 a couple of times then
    when I click, it shoots"; "I have fist image in /Game/UI/HUD"):
    - **Sounds:** the first cues were the pack's bullet whips and bullet
      body-hits. Now the knife swing and `Body_Flesh_1_Cue`, both 2D (bridge
      + code).
    - **Fire bug:** the picking click ran `DoFire` (closes the wheel) and
      `DoFireHeld` (fires) on the same frame. `bWheelPickHeld` +
      `DoFireReleased` swallow that click.
    - **Icon:** the melee icon is the user's `Fist`.
    - **Build:** the pistol-sounds session said wait (the user might have
      unsaved cue work), so the rebuild waited for the user's "saved, run the
      script". Compiled clean, DLL 22:43:27.
  - **Upper body only when moving** (user: "can you make it just do the upper
    body attack when moving?").
    - **C++:** `MeleeUpperBodyAlpha` on the anim instance, latched for the
      strike once the player moves.
    - **`ABP_Player`:** the `Additive` slot's input and output are cached, a
      `spine_01` layered blend makes the upper-body-only version, and a
      two-way blend by the alpha feeds the output.
    - **Build:** all three peer sessions said safe; DLL 23:05:17. The AnimBP
      compiled with a clean log and was saved.

- **2026-11-01: plan items 46 and 47 tested** (user: "46 and 47 are good").
- **2026-11-01: tap fire for the semi-autos (plan item 48).** User: "Let
  these weapons fire quicker than the firerate if the player pulls the
  trigger repeatedly faster than if you were holding the trigger"; "duals are
  included".
  - **Code:** `TapTimeBetweenShots` and a `bFreshPull` flag through
    `CanFire` / `Fire` / `FireEquippedWeapon`; `DoFire` → `PullTrigger(true)`,
    held → `PullTrigger(false)`.
  - **Values:** the user chose 0.6× the hold rate (.45 0.13, .45 duals 0.11,
    9mm 0.11, 9mm duals 0.09, revolver 0.27, Benelli 0.21) over a flat 0.06 s
    or an unlimited tap. Holds are unchanged (the user had read my first table
    as a change to them).
  - **Build:** the first rebuild **failed** and left the editor closed: a
    combined-file clash of two `IconAspect` helpers (`AmmoWidget.cpp`'s copy,
    from the HUD session, and the wheel's). With the user's OK, the wheel's
    copy was renamed `WheelIconAspect`; rebuilt clean (DLL 00:36:35), values
    set and saved. Both peers were warned while the editor was down and told
    when it was back. New gotcha in the spec.
  - **Tested** (user: "48 is good").
- **2026-11-01: Deck build, `Lvl_Sandbox`, no trace** (user: "make a
  steamdeck build, sandbox no trace").
  - **Packaging:** same as the fifth build. Both peers said safe, the editor
    was closed (`RebuildEditor.ps1 -NoLaunch`), then `BuildCookRun`
    (Development, pak + IoStore, compressed), archived to
    `ProjectBopis_Builds/DeckTest/`.
  - **Result:** BUILD SUCCESSFUL in 2 min 4 s; 3,877 packages cooked,
    0 errors, 20 warnings (old resave notices; new only `KnifeA_Swing_Cue`'s
    NodeGuid). The editor was reopened.
  - **Start command:** `ProjectBopis/Binaries/Win64/ProjectBopis.exe
    Lvl_Sandbox -ExecCmds="stat fps,stat unit"`.
  - **Perf suspects** added since the last Deck build: listed in the chat
    reply, with the hit-pulse post-process always on as the first candidate.
  - **User: "the sandbox drops to 42 fps"** (no `stat unit` numbers yet).
    First fix ("do the hit pulse fix"): the hit pulse is off the camera
    (weight 0) while idle. Applied on "apply and run", both peers said
    safe, compiled clean (DLL 01:14:46).
  - **Still to check:** Frame / Game / Draw / GPU at the drop, to tell GPU
    from game thread. Other suspects: the HUD icon outline (24 taps), the
    heads now updating after physics on every CC character, 4K gun
    textures, dying-body traces.

- **2026-11-01: Deck performance** (spec *Fourth*, *Fifth* and *Sixth Deck
  trace*, *Stationary lighting setup*).
  - **The question:** user: "the sandbox drops to 42 fps"; traced on the Deck.
  - **Finding:** GPU-bound. The drops are fight translucency (+5 ms), on top
    of a constant ~3.3 ms.
  - **The constant 3.3 ms:** found with `ProfileGPU` + material draw
    events. It was the player's sunglasses (creator `Sunglasses_01`; first
    mistaken for the aviators), whose translucent, refractive lenses ran a
    full-screen rough-refraction chain. Fixed in the creator's apparel
    tables with `MI_Glass_Dark_Opaque`: **−2.2 ms**, confirmed.
  - **Stationary lighting:** set up on both levels; `Lvl_Sandbox` baked
    with GPU Lightmass and clean. Ray and path tracing support are on for
    the editor only; `r.RayTracing.Enable=0` in the game, checked inside
    the shipped `.pak`.
  - **Its side effect:** the Stationary sun's per-object shadows cost about
    +2.5 ms, so the sixth trace isn't faster overall.
  - **Per shot (found):** muzzle flashes carry two smoke emitters and a
    light, and aren't pooled. Particle lights cost 1.3 ms average on fight
    frames, up to ~7 ms.
  - **Mistakes and gotchas:**
    - an engine mesh was edited and saved, then reverted;
    - Insights left open made the packaging run and editor record 1.4 GB
      (the store was wiped with `ClearTraces.ps1`);
    - in a one-file-per-actor level, bridge property edits don't mark the
      actor's file as changed.
  - **Deck packages:** five today, all 0 errors.
  - **60 fps:** Claude's view is that 60 is realistic calm, with a 40 fps
    Deck mode as the fallback. The user is testing dynamic resolution, 80%,
    and the particle-lighting and particle-light settings through the start
    command.
- **2026-11-01: muzzle flash** (spec *Muzzle flash*). Built by the
  "Current Coding Work" session; compiled at 13:08 and read back here. Not
  playtested yet.
  - Pooled spawn.
  - Smoke emitters at most every 0.35 s.
  - The five asset particle lights set to `spawnFraction` 0.
  - One code `MuzzleLight` per gun: 0.05 s, no shadows, no translucency.
  - Optimization handed over to this session.
- **2026-11-01: sun inset shadows off** in `Lvl_Sandbox`. A bridge session
  applied it and the user saved. Shell casings and all three pickup classes
  no longer cast shadows (Live Coding, compiled). Not traced yet.
- **2026-11-01: bridge across sessions** (spec, bridge gotchas):
  - several sessions can share the bridge;
  - a shell `cd` out of the project root unloads it for that session;
  - the proxy no longer treats the `server/discover` probe's 400 as a dead
    session.
- **2026-11-01: bullet-hole cap, bloom, SSAO** (spec, same name).
  - `UBulletHoleSubsystem` keeps the newest 48 holes.
  - High tier: bloom quality 3, SSAO max quality 50.
  - Rebuilt clean with `RebuildEditor` (seven sessions said safe; no reply
    from `projectbopis-f0`). Not traced yet.
- **2026-11-01: seventh Deck trace, glass refraction** (spec *Seventh Deck
  trace*).
  - **The trace:** user: "better fps, but some slowdown with multiple
    enemies on screen". 56% of seconds at ≥58 fps (was 29%); GPU p50
    16.7 ms. On fight frames: translucency 4.5 ms, and a refraction chain on
    16% of frames at 2.2 ms each.
  - **Wrong first guess:** the impact smoke and flecks. A bridge check found
    them already at refraction None, so nothing changed there.
  - **Cause:** the creator glass `M_Base_Material_Glass_Reflective`. The
    sunglasses fix only reached the male headwear tables; female enemies'
    glasses and one male pack row still refracted.
  - **Fix:** `RefractionMethod` None on that base material (bridge, saved
    16:28, `bUsesDistortion` gone from the file). Not yet traced.
- **2026-11-01: impact size and smoke interval** (spec *Seventh Deck
  trace*).
  - `EffectScale` 1.5 → 1.0 in `DA_ImpactEffects` (bridge, saved 16:43).
  - Smoke puffs: always one when none is alive, otherwise a random
    0.25–0.5 s apart, at most 8. User: "evenly distributed accross the whole
    burst".
  - Applied by Claude ("Apply it yourself"). Rebuilt clean with
    `RebuildEditor`; all peers were idle. Not yet playtested.
- **2026-11-01: `EFT_Impacts`** (spec *Seventh Deck trace*).
  - The systems already had the pack's `NFX_Impact`. My trace note said
    they had no effect type; it's corrected.
  - `EFT_Impacts` is a copy of it with tighter values: 40 m, 32 total, 16
    per system, off-screen cull at spawn.
  - On the 23 `DA_ImpactEffects` systems (bridge, saved 17:14). The pack
    asset is unchanged. Not yet traced.
  - Stray editor traces (16:28, 16:52) are in the Recycle Bin, so the
    store keeps 03:19 and trace 7 (15:04).
- **2026-11-01: eighth Deck trace** (spec *Eighth Deck trace*).
  - Fight translucency 4.5 → 1.75 ms, and the refraction chain is gone:
    −3.7 ms GPU.
  - The fight was heavier (+30% character work), so overall fps didn't
    rise: 48 fps in the slowest seconds, against 50.
  - New: fights are also game-thread-bound. World tick is ≈15 ms in the
    slowest seconds of both traces, from CC skinned meshes (167
    ticks/frame) and animation.
  - User's next idea: lower-resolution smoke and blood
    (`r.SeparateTranslucencyScreenPercentage`).
- **2026-11-01: ninth Deck trace, half-resolution translucency**
  (`20261101_174800`, 149 s; `r.SeparateTranslucencyScreenPercentage 50`
  in `-ExecCmds`, not in the ini).
  - Fight translucency 1.75 → 0.91 ms. Scene render in fights is about the
    same (18.98 → 18.95). The slowest 20% of seconds were 51 fps (48 in
    trace 8).
  - User saw "abnormal huge puffs of smoke". **Cause: `NS_ImpactConcrete`**
    (the greybox floors and walls are concrete). The user set its uniform
    scale from 1 to **0.25** in the editor (saved 18:01). It isn't in the
    Deck build yet; repackage to see it there.
  - Below 50%, translucency loses its nearest-depth upscale and falls back
    to bilinear halos, so 50 stays the floor.

- **2026-11-02: next-target batch** (user: "do all of them, I give you
  permissions"; spec *Next-target batch*).
  - `Lvl_Linear` sun inset shadows off (bridge, saved 09:48).
  - `r.TranslucencyLightingVolume=0` in the High tier.
  - Weapon meshes rest at a 0.25 s tick and wake for shots and rest poses;
    empty offhand meshes don't tick.
  - CC followers without cloth stop ticking (`StopIdlePartTicks`).
  - Rebuilt clean with `RebuildEditor` 09:53; bridge answers after.
    "Current Coding Work" was busy and said safe; it now owns the next
    edits to `WeaponBase` / `BopisCharacterBase` (M4 reload).
  - Bullet holes as meshes: **user: "Keep decals"**. Decals stay.
  - **Half-res translucency is now Deck-only:** out of the High ini, into
    `UBopisGameInstance::ApplyDeckOverrides` (`SteamDeck=1` or `-Deck`).
    Applied by Claude ("Apply it yourself"). Rebuilt clean with
    `RebuildEditor` (10:22; all peers idle; bridge answers). Not yet run on
    the Deck: add `-Deck` to the start command.
  - **Deck build 11:15** (`Tools/BuildDeck.ps1`, 2 min, exit 0). It holds
    the whole batch above, the Deck-only half res, and Current Coding
    Work's M4 reload (compiled 11:08). Not yet run on the Deck.
  - **Trace 18** (`20261102_112048`, Sandbox):
    - weapons −0.75 ms of game thread; lighting volume gone;
    - the CC part ticks didn't drop (164 → 180), because they ran before
      CC dressed the character;
    - overall fps about the same as trace 16, in a fight with more
      characters.
  - **CC part fix:** `StopIdlePartTicks` now runs from `Tick` once the
    character is dressed and shown. Rebuilt clean with `RebuildEditor`
    (11:32; all peers idle; bridge answers). In the Deck build of 11:38
    (`BuildDeck.ps1`, 2 min, exit 0).
  - **On the Deck the clothes didn't follow the body:** stopping
    leader-posed followers' ticks was wrong. They take the body's pose on
    screen in their own tick. Reverted to empty slots only (still run once
    dressed). Applied by Claude ("Apply it yourself"). **Code given, not
    yet compiled.** The 11:38 Deck build is broken; rebuild and repackage.
  - **Native 100% rescinded** (user: "go with what percentage the Deck
    deems ok"): `r.ScreenPercentage=100` is out of `DefaultEngine.ini`.
    The Deck's first run keeps the benchmark's resolution (71%) after
    setting High, which would have made it 87% (`BopisGameInstance.cpp`).
    On the Deck, delete `GameUserSettings.ini` once, and drop
    `scalability 2` from `-ExecCmds`.
  - **Rebuilt clean 11:52** (clothes revert + 71%; all peers idle; bridge
    answers). **Deck build 11:55** (`BuildDeck.ps1`, exit 0).
  - **Trace 19** (`20261102_120035`, Sandbox, 105 s, without
    `scalability 2`). User: "its rendering at 100%".
    - The trace shows Epic, not High: lighting volume 2.22 ms and SSS
      1.13 ms, both off on High.
    - So the first-run Deck code didn't apply. Either the saved
      `GameUserSettings.ini` was kept, or `SteamDeck=1` doesn't arrive
      (only `ApplyDeckOverrides` checks `-Deck`). The game used the engine
      default: Epic at 100%.
    - Even so: busiest 20% at 53 fps (48 in trace 18), 77% of seconds at
      58+ fps.
    - CC part ticks 180 → 145 (the empty-slot fix works once dressed);
      busy world tick 15.4 → 13.7 ms, with fewer characters moving
      (7.7 against 8.9).
    - **Fix:** `ApplyDeckOverrides` now sets High + 71%, 1280×800, 60 fps
      every start (`SteamDeck=1` or `-Deck`); the first-run Deck branch is
      gone. Applied by Claude ("Yes, apply it"). Rebuilt clean 12:08 (all
      peers idle; bridge answers); **Deck build 12:10** (exit 0).
    - **Run 12:12** (`20261102_121226`): user: "still at 100%". The trace
      is still Epic (lighting volume + SSS on), so `ApplyDeckOverrides`
      didn't take. Suspects: `-Deck` missing from the Devkit command, or an
      old upload.
    - **Debug:** a green on-screen message plus a log line, "Deck settings
      applied: effects quality N, screen N%", reading back
      `sg.EffectsQuality` and `r.ScreenPercentage` (non-Shipping only).
      Applied by Claude ("Yes, add it"). Rebuilt clean 12:16; **Deck build
      12:18** (game exe 12:17, exit 0).
    - **Deck run, user:** "effect quality 3, 100%". The code ran but didn't
      take.
    - **Cause:** `UGameUserSettings::ApplyNonResolutionSettings` only
      applies quality levels `if (GEngine->IsInitialized())`. `Init()` runs
      before that, so it was a silent no-op, and `SaveSettings` saved Epic
      back.
    - **Fix:** `ApplyDeckOverrides` now runs from `OnStart()`, after
      engine init. Applied by Claude ("Apply it yourself"). Rebuilt clean
      12:25; **Deck build 12:28** (game exe 12:26, exit 0).
    - **Confirmed on the Deck (user): "Quality 2, 71%".** High at 71% now
      applies every start.
  - **Trace 21** (`20261102_122946`, Sandbox, 126 s, High at 71%). User:
    "seems to have the same performance".
    - GPU scene all 13.95 → **12.23 ms** (calm 13.18 → 11.12), so 71% saves
      ≈1.7 ms of GPU.
    - Fights didn't speed up (busiest 20%: 46 fps; trace 18: 48) because
      they're **game-thread-bound**: busy `UWorld_Tick` 15.7 ms, frame tick
      28.8 ms.
    - Most of the world tick is the game thread waiting on parallel tick
      and anim tasks (`ProcessUntilTasksComplete` 9.9 incl,
      `WaitForTasks` 2.4).
    - CC part ticks are back to ≈183/frame (trace 19: 145), with 9.2
      characters moving.
  - **User: "Back to 100%".** `DeckResolutionScale` 71 → 100 (the Deck
    still forces High + the constant every start). Applied by Claude
    ("Apply it yourself"). **Code given, not yet compiled.** Next lever
    for fights: the game thread (characters).
  - Pushed by the user as `2fa1fdd3` "Optimization, M4 Reload fix". The
    100% change was still uncompiled.
  - **URO switchable** (user: "make the URO offable … so PC players can
    have full anims"):
    - a new cvar, `bopis.EnemyAnimRateOptimization` (bool, default
      **off**, `ECVF_Scalability`), in `EnemyBase.cpp`;
    - `AEnemyBase::Tick` enables URO only when it's on and no body
      simulates; the constructor no longer forces it;
    - `ApplyDeckOverrides` sets it on (`SetByCode`).
    - Live-toggleable from the console. Applied by Claude ("Apply it
      yourself"). **Code given, not yet compiled.**
  - Next: game-thread items 1–5 (spec *Game-thread targets*): Deck-only
    URO thresholds, HUD/Slate, impact particles on GPU, enemy movement,
    physical-animation tick.
  - **#1 applied:** `AnimRateScreenSizes` {0.5, 0.25} via
    `OnAnimUpdateRateParamsCreated` (Deck only, where URO is on). Applied by
    Claude ("Apply it yourself"). **Code given, not yet compiled.** Three
    changes wait on one rebuild: 100%, the URO switch, and #1.
  - **#2–#5** (user: "go finish up to #5 all the way"; spec *Game-thread
    targets*):
    - HUD text and bar material set only on a change;
    - `EFT_Impacts` mask fixed to include High (it was skipping the Deck
      entirely), saved 12:54;
    - enemy movement: no physics pushes, no floor check when still;
    - physical animation ticks only while simulating.
  - **All built:** 100%, URO switch, #1–#5. Rebuilt clean 12:55 (bridge
    answers); **Deck build 12:58** (game exe 12:57, exit 0). Not yet run
    on the Deck.
  - **Trace 22** (`20261102_130452`, Sandbox, only 31 s analysed, High
    100%, #1–#5):
    - **#3 worked:** `NS_ImpactConcrete` 1.59 → 0.60 ms,
      `ConcreteSmoke` 0.56 → 0.17 (all threads).
    - **#2 a little:** Slate tick and draw 0.88 / 0.88 → 0.81 / 0.80.
    - **#1 did nothing:** `ABP_Player_C` evaluations 13.0 → 12.8 per frame,
      `CharacterMesh0` 5.8 → 5.9 ms. `PhysicalAnimation` still ticked about
      9 times per frame under #5, which ticks it only while a body
      simulates. **Suspect: enemies always have some simulating body**,
      so `AEnemyBase::Tick`'s `!IsAnySimulatingPhysics()` keeps URO off
      permanently (it did before #1 too). To check in PIE.
    - Busiest 20%: 45 fps, `UWorld_Tick` 15.8 ms (trace 21: 46, 15.7).
  - **Bug (user): "when the player gets hit, the model spazzes out".**
    Cause: #5. The hit reaction starts simulating and applies
    physical-animation motors in the same frame, while the component's
    tick is still off. The limbs run unpowered until `Tick` turns it on.
    **Reverted #5** (Claude, "Apply it yourself"): `PhysicalAnimation`
    ticks every frame again. **Code given, not yet compiled.**
  - **Why #1 did nothing: free-arm physics.** Pistol enemies keep the left
    arm on physics all fight, so `IsAnySimulatingPhysics()` stays true and
    URO stays off.
    - **Fix:** `AEnemyBase::WantsFreeArmPhysics()` returns false while
      `bopis.EnemyAnimRateOptimization` is on (the Deck).
    - Applied by Claude ("Apply it yourself"). Rebuilt clean 13:16 along
      with the #5 revert ("Current Coding Work" was busy and said safe).
      **Deck build 13:17** (exit 0). Not yet run on the Deck.
  - **Trace 23** (`20261102_132154`, Sandbox, 235 s, High 100%, URO
    unblocked + #2–#4, #5 reverted), against trace 21:
    - **Busiest 20% of seconds: 53 fps** (46).
    - **Seconds at 58+ fps: 83%** (54%); under 50: 3% (8%).
    - Busy `UWorld_Tick` 13.6 ms (15.7); average 10.2 (11.8).
    - Enemy anim `CharacterMesh0` 5.8 → 4.9 ms; `ABP_Player_C` evaluations
      13.0 → 11.7 per frame.
    - Concrete impacts 1.59 → 0.44 ms; movement 1.26 → 0.97; Slate
      0.88 + 0.88 → 0.78 + 0.78.
    - About 10% fewer characters moving (8.3 against 9.2), so part of the
      gain is the fight.
    - **Playtested on the Deck (user): "Both look fine".** No hit spazz,
      and mid-range enemies don't look steppy.
  - **Trace store cleaned** (user: "clean up old and unneeded traces"):
    kept `20261102_122946` (trace 21, Sandbox baseline) and
    `20261102_000532` (`Lvl_Linear` baseline). 16 others (≈5.6 GB) are in
    the Recycle Bin.
  - **To check:** PIE (clothes follow far and dying enemies; gun fire and
    rest poses look right), then a Deck trace of both levels.
- **2026-11-02: M4 reload with a rear charging-handle pull.** User: "make an
  animation I can use for the M4 and MP5 (later on)"; "do the rear pull";
  "go with B". Spec: *Charging styles: the M4 reload*.
  - **Animation:** Lyra's rifle reload with its AK side pull (1.07–1.87 s)
    re-made in Blender by script. The gun comes off the cheek; the left hand
    goes over the top, hooks the T-handle and pulls it 7.5 cm back.
    Unchanged frames match the original exactly.
  - **New assets:** `MM_Rifle_Reload_M4`, `AM_Rifle_Reload_M4` (Chamber
    notify at 1.40 s), `A_AR4_Reload` (the gun's handle).
  - **Code** (applied by Claude, "apply and run"; rebuilt clean 10:38, all
    peers idle; the bridge answers):
    - `EChargingStyle` on the weapon;
    - `ChargingReloadMontages` on the character;
    - `AWeaponBase::ReloadAnimation` on the gun mesh.

    The first pass put the montage on the weapon, which breaks the *animator
    owns the clips* rule, so option B replaced it.
  - **Data:** `BP_AssaultRifle` (`RearHandle`, `A_AR4_Reload`).
    `BP_PlayerCharacter` / `BP_EnemyBase` map `RearHandle` →
    `AM_Rifle_Reload_M4`; the CC children inherit it. Saved and checked on
    disk.
  - **Scripts:** `Tools/AnimAuthoring/M4Reload/`.
  - **First PIE test failed:** the gun moved its handle, but the character
    played the AK reload. Bridge-set defaults don't reach spawned actors
    until the Blueprint compiles (spec gotcha). Compiling `BP_AssaultRifle`
    and the four CC Blueprints fixed it. **Tested (user: "your charge handle
    is in now").**
- **2026-11-02: silent taps fixed** (user: "issue with the sounds when single
  clicking some weapons over and over").
  - Cause: today's weapon-mesh tick throttling. `WakeMeshes()` set the
    interval with `SetComponentTickInterval`, which doesn't cut a running
    0.25 s cooldown short, so the shot animation and its `Fire` notify
    lagged and a quick second tap restarted it before the notify fired.
  - Fix: a resting mesh's tick is switched off and on (spec: the tick
    throttling notes).
  - Applied by Claude ("apply and run"); rebuilt clean 11:08, all peers idle,
    the bridge answers. **Tested in PIE (user: "thats working", 2026-11-02).**
- **2026-11-02: revolver reload, speedloader with a full flick.** User: "Can
  you help me make a revolver reload?", then "do the flick" (full flick).
  Spec: *Revolver reload: speedloader, full flick*.
  - **Animation (2.0 s):**
    - The wrist flicks the cylinder out.
    - Muzzle up: the left heel drives the ejector and the empties drop.
    - Muzzle down: speedloader from the belt, seated, pulled away and
      dropped.
    - The wrist flicks it shut, then back to aim.
  - **Imported and checked** (headless, after the Optimization thread's Deck
    build): `MM_Pistol_Reload_Revolver`, `AM_Pistol_Reload_Revolver`
    (MagOut 0.575, MagIn 1.27, Chamber 1.545) and `A_Revolver_Reload`. The
    body matches the original exactly; the gun matches its reference pose
    at frame 0.
  - **Code:** `EChargingStyle::SwingOutCylinder`. Applied by Claude ("apply
    and run"); rebuilt clean 13:37, all peers idle, the bridge answers.
  - **Wired:**
    - `BP_Revolver` (style, `A_Revolver_Reload`, `ReloadDuration` 2.6 →
      2.0).
    - `BP_PlayerCharacter` / `BP_EnemyBase` map it to the new montage.
    - All seven Blueprints compiled, CC children included; saved and checked
      on disk.
  - **First PIE test** (user): "it works but the player cant see the gun
    during the animation at all, hidden behind the body. Also he should pop
    the bullets out and it should fall".
  - **Round 2** ("apply and run"; rebuilt clean 13:53 with the editor kept
    closed, all peers idle; assets re-imported, then the editor reopened;
    the bridge answers):
    - **Restaged:** the work moved to the right side at shoulder height.
      The strike is beside the head, and the upper body turns 18° right.
      Checked from the game's own camera positions.
    - **Physics empties:** `ReloadCasingMesh` / `ReloadCasingBones` /
      `DropReloadCasings`.
    - An Eject notify at 0.60 s on `A_Revolver_Reload`. `BP_Revolver` uses
      `_357MagnumRound` × `Bullet1`–`6`.
    - **Tested** (user: "thats working").
  - **Round 3: the speedloader shows** (user: "now make the speedloader show
    during the reload"; "apply and run"; rebuilt clean 14:06, all peers
    idle, the bridge answers):
    - `AWeaponBase::ReloadMaterials` swaps a slot's material for the
      reload's length.
    - `BP_Revolver` maps the `Speedloader` slot (`TransparentMat` otherwise)
      to the pack's `Speedloader` material. Saved and checked on disk.
    - **Tested** (user: "thats working").
  - **Round 4: no drop.** User: "no drops to the floor please" (after
    "forget the speedloader actually", which called off a physics drop
    before any code).
    - The left hand now puts the empty loader back in the belt pouch
      (1.67 s), then returns to the grip.
    - Animation only. Re-imported with the editor closed (user: "do it"; all
      peers idle; the editor reopened 14:28; the bridge answers). The Eject
      notify was kept.
    - **Tested** (user: "thats working").
- **2026-11-02: shotgun rack after a reload from empty.** User: "make a pump
  only animation… after the shotgun reloads, we do not have a after load
  'pump'"; "I need it for the reload"; picked "only from empty". Spec:
  *Shotgun rack after a reload from empty*.
  - The pump shotgun is now the Mossberg (`BP_PumpShotgun`). Its pump moves
    through its own gun clip, and the left-hand grip socket rides that pump.
  - **Code** ("apply and run"; rebuilt clean 14:49 with the editor kept closed
    for the import, all peers idle; the bridge answers):
    - `EWeaponSound::Rack` + `RackAnimation`.
    - `bRackAfterEmptyReload` / `NeedsRackAfterReload()`.
    - The character plays the reload's End only when the gun needs it. The
      `bPlayReloadEnd` flag is removed.
  - **Assets:**
    - `MM_Shotgun_Reload_Pump`: End re-made as the rack, with a `HandGrip`
      curve.
    - `AM_Shotgun_Reload_Pump`: Rack notify at 1.55 s, blends out from
      ~2.0 s.
    - `A_Mossberg_Rack`: the pump stroke alone, with its Pump sound.
    - A first pass left the montage on the old sequence (Python struct
      copies). Fixed and checked.
  - **Data:** `BP_PumpShotgun` (rack on, `A_Mossberg_Rack`). Player, enemy
    and CC reload maps: `PumpShotgun` → the new montage. Compiled, saved,
    checked on disk. The Benelli is unchanged.
  - **Tested in PIE (user: "it works").**
  - **Scripts:** `Tools/AnimAuthoring/ShotgunRack/` (the revolver's are in
    `RevolverReload/`).
- **2026-11-02: AnimAuthoring cleaned up.** User: "can we clean up the tools
  section?"; scope "AnimAuthoring only". Spec: *Animation authoring scripts*;
  the folder's `README.md`.
  - `lib/animlib.py` (Blender) and `lib/uelib.py` (headless editor) now hold
    what the M4, revolver and shotgun projects had in triplicate. Each project
    keeps a `project.py` and its own motion.
  - New: `RunUnreal.ps1` / `RunBlender.ps1` runners, one `.gitignore`, and a
    README.
  - Removed: the three `bl_common.py` files and the per-project
    `.gitignore`s.
  - **Checked:** all three were regenerated from fresh exports through the
    new code. Every animation key matched the tested assets' sources (the
    revolver and the shotgun exactly, the M4 within 2e-6), and the gun FBXs
    came out the same.
  - The `import_ue.py` scripts weren't re-run (that would replace the live
    assets).
  - The M4's `export_ue.py` exports its FBX inputs again, as the other two do.
  - **Then the three project folders were deleted** (user: "keep the
    AnimAuthoring folder, remove the weapon and function specific folder
    scripts. Those are completed so no need for them").
    - Left: `lib/`, the runners, `.gitignore`, and a README rewritten as a
      template with a *Done so far* table.
    - The M4's scripts are in git history. The revolver's and shotgun's were
      only ever staged, so they're gone once the deletion is committed.
- **2026-11-02: `Lvl_BackAlleys`, a copy of the Sandbox for the back-alley
  arena.** User: "Duplicate the Sandbox level, we will work off of that, plan
  is to make a square arena similar to it. but make it look like backalleys";
  "I am praying that with the levels, we have shorter sight lines and less
  'mobbing'". MP5 deferred (user: "I'll add the MP5 later").
  - Duplicated in the editor (the Sandbox stores one file per actor, so
    copying files outside the editor would miss most of it) and saved: the
    umap plus all 86 actor files and 1 object, the same as the Sandbox.
  - It's open in the editor.
  - It has no baked lighting yet: the Sandbox's `_BuiltData` didn't copy, and
    the new geometry needs its own GPU Lightmass bake anyway.
  - Not in `MapsToCook` yet (`DefaultGame.ini`). Add it before its first Deck
    build.
  - **Waiting on:**
    - The user adds an environment art pack ("i havent added it yet").
      Review it before placing anything: collision, lightmap UVs, LODs,
      materials and physical materials, texture sizes, Deck cost.
    - The layout. The 2026-10-23 `Design Document/Arena_Slums_Layout.html`
      (48 × 40 m slum block, half-court, ring lanes, 8 eskinita spawn doors,
      +4 m gallery) fits the brief, but the user hasn't picked it.
- **2026-11-02: art packs analysed, prepped, and a kit list for the slum
  arena.** User: "analyze the models, see what we can use"; "also evaluate
  for performance"; "use the slum arena as basis and do a prepass"; "yep 1
  and 2" (the layout and the prep pass). The rest ran while the user was away
  ("keep going as far as you can"). Spec: *Environment art packs* and its
  three subsections.
  - **Layout picked:** `Arena_Slums_Layout.html`.
  - **Prep pass applied to all three packs** in a full editor, with every
    peer idle and the editor closed via `RebuildEditor.ps1 -NoLaunch`.
    - 0 errors, 1,333 assets saved.
    - LODs on 151 meshes, generated lightmap UVs on 85, higher lightmap
      resolution on 405.
    - Complex-as-simple collision on 295 architecture pieces, boxes on 45
      props.
    - Surface types on 604 materials.
  - **Textures, a second headless run:** 714 capped at 2K.
    - The full editor had read placeholder sizes and capped none.
    - The first headless run ran out of memory after 665. The re-run with
      garbage collection did the last 49.
  - **Read back headless:** everything matches. The exceptions:
    - 6 heavy grilles and balconies whose lowest LOD is still over 8k for
      collision. They're on the never-use list.
    - Lightmap UVs: the settings are right on all 85. The built channel only
      shows at the first bake (Map Check).
  - **The editor was reopened afterwards** (17:26).
  - **Finding:** AsiaSlum's Type prefabs are 21–45 m high-rises, with
    143–668 mesh components each. (These were first written doubled: the
    subobject gather lists each component twice.)
    - Don't place them.
    - Build the blocks from the modules, lane-facing sides only, and pack
      each into a Packed Level Actor.
    - The two DecoHouses (two storeys, 6 m) are the scale model.
  - **Kit list** for every layout element is in the spec. Gaps: **no
    jeepney, tricycle or basketball hoop** in any pack.
  - The packs (and so the prep) are still uncommitted.
- **2026-11-02: `Lvl_BackAlleys` built, first pass.** User: "blockout stand-ins
  for now, make the glass opaque, go build. The basketball court, I will add
  assets, hold on". Spec: *`Lvl_BackAlleys`: first build*.
  - **Glass:** `MI_Glass_A_001/002` are now opaque (`M_BaseMaterial` with
    `MI_Glass_A_003`'s values).
  - **Cleared:** the Sandbox blockout (65 meshes, 2 pickups).
  - **Built through the bridge from the layout** (peers idle; about 540
    actors, saved):
    - 8 blocks of AsiaSlum walls, two storeys, lane sides only;
    - 8 spawn-door end walls;
    - the +4 m gallery with both stairs (traced);
    - cover, the jeepney and tricycle stand-ins, and a built kiosk;
    - lids and dark cores (open windows read as dark rooms);
    - a first dressing pass: awnings, tin, cables, the wire web, laundry on
      a pole, roof tanks and antennas, garbage, the sari-sari front.
  - **Ground:** a 44 × 52 m floor with `MI_BackAlleys_Ground`. The nav and
    lightmass volumes were resized.
  - **Gameplay:**
    - The EncounterDirector uses 8 spawn points with `MaxAlive` 4.
      `TotalEnemies` stays at the Sandbox's 20: "goal or endless" is still
      open.
    - 11 pickups as the layout places them.
  - **Checked:**
    - Every spawn point and pickup has ground under it.
    - The lanes, stubs and gallery are clear.
    - Overhead dressing doesn't collide.
    - Four viewport captures.
  - **The court, same day** (the user's `BasketballCourt` pack, relayed by
    a peer session: "cut it in half… include it in the prep pass"):
    - The court quad was cut to a half with Geometry Script
      (`SM_BackAlleys_HalfCourt`) and placed at 0.8 scale in the layout's
      16 × 12 zone.
    - The hoop is full size. Two benches, two court lights, a bin and a
      ball were added.
    - The pack's prep went through the bridge with the editor open:
      - LODs on 14 meshes;
      - LOD thresholds keep the net at 22k and the rim at 24k;
      - the stand collides on its own triangles;
      - surface types and 2K caps.
    - The court is `MI_Court_1`, bright blue. There are 6 variants, the
      user's pick.
  - **Re-laid out, same day.** User: "the space between the court and the
    building need to be much wider. Put the court in 1.0 scale… try 2x the
    size of the jeepney placeholder"; then picked "2× its width: ~5 m".
    - Arena now 53 × 46 m.
    - Full-size court (19 × 16 m) with 5 m to the buildings and the gallery
      posts.
    - Rebuilt from one block table (`gen_level2.py`): 544 actors.
    - Added an invisible floor-collision slab: the template floor's
      collision didn't reach the door ends.
    - Saved.
  - **Redesign requested, same day.** User: "coordinate with the arena level
    design thread. Tell him to redesign, remove the court, make it
    exclusively alleys. The long sight lines are not great for arena level
    style"; then "also, remove the grenade launcher".
    - Both were passed to the "Arena Level Design: Slums" session, with the
      kit and build constraints and the block-table format the generator
      takes.
    - The launcher pickup and its ammo were removed from `Lvl_BackAlleys`
      (saved).
    - **Rebuilt from the new layout**
      (`Design Document/Arena_Slums_Layout.json`):
      - 54 × 48 m, 29 blocks, 4.5 m alleys;
      - longest sightline about 25 m;
      - no court, no launcher.
    - `gen_level3.py` places walls per storey wherever a block side faces
      open alley (blocks now touch).
    - 892 actors plus pickups and wander points. Traces check out. Saved.
  - **Goal decided** (user, through the design session): **"20 kills"**.
    The arena is cleared when the 20th gunman dies, 4 alive at a time;
    dying restarts it as now.
    - The live director already matches: `TotalEnemies` 20, `MaxAlive` 4,
      8 spawn points, `bKillCamOnClear` on. So the final kill plays the
      kill cam today.
    - **Still the user's call:** what happens after the clear: an exit, a
      message or a return to the menu. `ALevelExitTrigger` exists (not
      placed; `Fire()` is Blueprint-callable). Nothing calls it when a fight
      ends, so that needs a small hook, which is C++ to present first.
  - **Not done:**
    - a PIE test (nav mesh, spawns);
    - merging for draw calls;
    - lighting and mood;
    - the bake.
- **2026-11-03: Level-generation thread; generator moved into `Tools/LevelGen/`.**
  - **The generator:**
    - `gen_level.py` is `gen_level3.py` with repo-relative paths. Its output
      is byte-identical to the `plan3_*.json` the current level was built
      from, so the level already matches it.
    - The bridge placer was recovered by "Current Coding Work" and is now
      `place_plan_ue.py`.
    - There's a README, and **`LESSONS.md`**: the user's verdicts and
      reference-map patterns, read before every build. User: "can you learn
      by iteration what works for the level gen?" → yes, through that file
      plus rules in the code.
  - **Favela analysis** (user: "pick up patterns on how it makes buildings…
    textures, decals, window and door types, dressings"):
    - `analysis/dump_map_ue.py` (headless, read-only; no bridge) dumped
      Favela and the AsiaSlum demo map to `Saved/LevelGen/`.
    - `analysis/analyse_buildings.py` groups the dump into buildings.
    - The findings are in `LESSONS.md`:
      - 2.25 × 3 m tiles, stretched to fit;
      - slab and trim bands;
      - stepped-back roof terraces with parapets;
      - patchwork materials (plaster over brick, with openings in other
        brick);
      - grilles and canopies over openings;
      - grime decals in two height bands;
      - antennas.
  - **Built: Favela walls, 4 m storeys** (user's pick). Each storey is a
    3 m Favela tile, a 1 m concrete band and trims, with Favela doors and
    windows (opaque glass) and patchwork materials. There are 159 grime
    decals, 14 antennas and roof drums.
    - Placed through the bridge in 4 + 1 calls: 2,248 actors, 0 failures,
      903 old actors removed. Saved.
    - Traces OK. The nav mesh covers the deck and both stairs (checked in
      captures).
    - Spec: *Fourth build: Favela walls*.
  - **Revised** (user: "overlapping faces… corners"; "mostly the concrete
    material"; red brick → "non-red hollow blocks"):
    - **Corners:** fixed by `corner_adjust()`. Inside corners run 10 cm into
      the wall ahead; outside corners cut the north/south runs 20 cm and
      lengthen the east/west trims 7 cm.
    - **Materials:** five new MIs in `BackAlleys/Materials`, made headless:
      concrete over grey blocks, bare blocks, and paint accents. Walls are
      now about 80% concrete with no red brick.
    - Rebuilt: 2,242 actors, 0 failures. Saved.
    - Corner capture clean.
    - The block texture reads as stone, not true CHB; no pack has a CHB
      texture.
  - **Revision 2** (user: "Make a CHB material", "overlaps happens in the
    trims", "isolate any new materials… outside the external assets", "add
    ocasional air conditioners", "overlap the wall model, just make sure the
    faces dont overlap"):
    - **Material:** `M_BackAlleys_CHB`, procedural world-aligned hollow blocks
      with an optional chipped render, plus 6 instances. Our materials and
      13 texture copies live in `BackAlleys/Materials` and `/Textures`, with
      no pack dependency.
    - **Corners:** outside corners overlap 2 cm, with no shared faces. Trims
      no longer cross. Lids are inset.
    - **New check:** `check_overlaps.py`.
    - **AC units:** 12 added.
    - **Rebuilt:** 2,283 actors. Saved. Captures OK.
    - **Cleanup still open:** delete the 5 unused pack-parented MIs.
  - **Standing rule: building blockouts only** (user: "forget all the
    dressings… No other objects in the level besides building blockouts as
    a rule").
    - **Kept** (the user's pick): the buildings, the gameplay actors, the
      gallery and stairs.
    - **Removed:** cover, pickups, dressing, decals.
    - **Recorded in:** `Claude-Rules.md` §8, `LESSONS.md`, and the generator
      switches.
    - **Rebuilt:** 1,927 actors in `BackAlleys/`. Traces OK. Saved.
  - **More windows, as the default** (user): street floors 25%, upper floors
    40% (were 9% and 13%). 106 windows, up from 50. Rebuilt: 1,966 actors.
    Saved.
  - **One material per block face** (user): no more patchwork within a face.
    90 faces, 0 mixed. Rebuilt: 1,960 actors. Saved.
  - **Per storey, plus 14 colour variants** (user): upper storeys may differ
    from the ground floor. 10 pastel paints, warm and dark concrete, light
    and dark bare blocks.
    - Rebuilt: 1,958 actors. Saved.
    - The material script now creates missing assets only, after one run
      tried to rebuild a loaded asset (blocked by the editor's file lock, no
      damage).
  - **Corners and stains** (user):
    - **Corners:** 55 concrete corner columns at outside corners replace the
      2 cm overlap strip. The half tile's second material slot is now
      overridden, so no pack brick shows.
    - **Bands:** back to concrete.
    - **Stain decals:** on (200), the rule's first exception.
    - Rebuilt: 2,213 actors. Saved.
  - **Stains reworked** (user): Favela's decals are whole-wall layers.
    - Now only the `Dirt_06` drips, sized from the user's hand-placed
      decal: the edge behind the trim, full wall width, down to the floor.
    - On about a third of wall stretches: 98 decals.
    - Rebuilt: 2,111 actors. Saved.
  - **Grouped drips** (user): adjacent drips merge into one decal across up
    to 3 wall tiles. 121 decals. Only the decals were swapped. Saved.
  - **Single-tile drips shortened** to 3 m (user): the streaks end mid-wall.
    Decals swapped. Saved.
  - **Drips span up to 4 tiles, length by span** (user): 3 m for 1 tile up to
    5 m for 4. Decals swapped. Saved.
  - **Drips cover whole faces** (user): picked per wall run, over every
    tile including the end half block. My first take left the half blocks
    bare, which the user caught. 57 decals. Saved.
  - **Drips shortened again** (user): 2.3 m for 1 tile up to 3.8 m for 4
    (was 3–5 m). Saved.
  - **Decals dropped, then brought back as `Dirt_08`** (user). The generator
    is updated: 57 drips, same rules.
    - **Swapped in the level** once the user reopened it: 57 `Dirt_08` drips.
      Saved.
    - **Seen in a capture:** `Dirt_08`'s Decal Color (0.09, 0.08, 0.07) is
      very dark, so the drips barely show on dark concrete under the current
      flat lighting.
  - **One wall material** (user, "All of it"): every wall is
    `MI_BackAlleys_CHB_Concrete`. Rebuilt: 2,070 actors. Saved.
    - One extra actor in `Blocks` (1,731 vs 1,730) isn't from the
      generator; left alone.
  - **Studied Favela's "balcony with corrugated roof"** (user), offline from
    the dump.
    - It's a covered roof terrace: a lower roof slab with a low parapet,
      flat corrugated sheets about 2.75 m up resting on the walls, sometimes
      a plank frame, usually a water drum on a stand.
    - Numbers in `LESSONS.md`.
    - Fits the five 1-storey blocks.
  - **Built the covered roof terraces** (user: "Yes, build them") on B10,
    B17, B19, B21, B22: parapets, corrugated sheets and plank frames, 142
    pieces.
    - Rebuilt: 2,196 actors. Saved. The capture reads right.
    - The full rebuild removed the extra unknown `Blocks` actor.
  - **Balconies** (user): six 2-storey blocks now have a stepped-back upper
    storey with a 1.5 m covered balcony (B28, B3, B7, B26, B25, B8). Doors
    and windows open onto each.
    - Rebuilt: 2,409 actors. Saved. The capture reads right.
  - **Wide roof terraces from the user's reference picture:** 4 blocks lose
    half their upper storey (B20, B24, B18, B4). Each gets an open terrace
    with parapets and a sloped corrugated lean-to on floor posts. The
    narrow balconies are kept on 6 other blocks.
    - Rebuilt: 2,541 actors. Saved. The capture matches the reference.
    - Water tanks left out (dressing).
  - **Terrace edges** (user): stone parapets capped with `MainBorder`. Favela's
    window-frame banister (`SM_Window_Frame_02` panels) on about 40% of
    terraces as the variation. Rebuilt: 2,651 actors. Saved.
  - **Jalousie windows** (user's texture): imported as our own textures and
    material. All 98 windows are now a textured plane set into the opening.
    - It first faced into the wall; the user caught it ("flip it 180"),
      fixed to roll +90 in the level and the generator. Saved.
    - Texture size fix (power of two, 1024) saved; it applies on the next
      editor load.
    - **Then switched to the user's double-pane jalousie** (1024²):
      `MI_BackAlleys_JalousieDouble` on all 98 windows and in the generator.
      Saved.
  - **Doors → `SM_HouseDoor_B_003`** (user, "make sure it fits"): all 43
    doors, scaled exactly to the door opening; the old jambs are removed.
    Rebuilt: 2,608 actors. Saved. The capture shows a clean fit.
  - **Windows pushed out** to 2 cm deep (user: the sill's texture smeared at
    9 cm). All 98 were moved in place and the generator updated. Saved.
  - **Window style per house** (user): each house is all jalousie or all
    Favela pull windows (10 / 13 houses). The 98 windows were swapped.
    Saved.
  - **Wooden banister** (user: "was a wooden one"): the banister variation
    is now Favela's `SM_windows_06` wooden window (25 panels), replacing the
    metal frame. The `Terraces` folder was swapped (479). Saved.
  - **Plane doors** (user's zip of 5 textures): imported as our own textures
    plus 5 material instances (`create_doors_ue.py`; Wood or Metal surface
    type). All 43 wall doors are now a textured plane filling the slot, one
    of the five at random. Swapped in place and saved. The capture shows a
    clean, upright fit.
  - **Steel grilles** (user's screenshot, "doors 2 4 and 5"): the AsiaSlum
    grilles A_002/A_004/A_005 sit in front of about half the plane doors.
    The louvred B_003 is used alone in some slots.
    - Right-hand opening (planes mirrored).
    - In the level: 43 doors plus 25 grilles. Saved. The capture shows the
      grille fits.
    - Then the grilles were turned (user): hinges now on the inside face,
      still on the right. Swapped in place and saved.
  - **Philippine street look** (user's back-street photo, "All four at
    once"). The generator now:
    - splits long blocks into houses;
    - varies storey height (3.4-4.2 m), with some 3-storey houses and 4
      one-storey metal-roof houses;
    - sets street fronts back 0-0.6 m (inward only);
    - puts sloped corrugated metal roofs on most houses (never flat), with
      gable fills.
    - Deck, stair, spawn-door and shop-row houses stay at 4 m.
    - Wall exposure is now geometric and height-aware. New corner rules
      cover diagonal corners, lower in-line neighbours and junctions.
      `check_overlaps` is clean.
    - Rebuilt: 3,195 actors. Traces unchanged. Saved. Captures (aerial,
      street, a gable) look right.
  - **Not done:**
    - the user's PIE walk-through;
    - per-block merging (about 2,270 actors);
    - grilles and canopies;
    - the AsiaSlum demo map isn't analysed yet (dumped).
  - **Nav checked offline** (user: "Check nav"). The bridge can't switch on
    the Navigation show flag, so the check is the new
    `Tools/LevelGen/analysis/check_nav_roofs.py`. Results:
    - roofs, lids and terraces stay unreachable islands: none joins the
      ground, deck or stairs;
    - the B17 and B19 terraces meet the deck only diagonally at a corner,
      and banisters close them in;
    - the lowest roof piece is 3.22 m, well above the agent height;
    - the enemies only pick reachable points.
    Not checked: the nav mesh as built in the editor (press P in the
    viewport). The AssetGen manifest later confirmed that the banisters
    (`SM_windows_06`) block nav.
  - **Visual pass of the packs** (user: "analyze the whole Megapack,
    AsianSlum and Philippine Market models ... not just metadata"):
    - All 1,098 meshes were exported headless (`analysis/export_meshes_ue.py`)
      and rendered three ways in Blender 4.0
      (`analysis/render_meshes_blender.py`).
    - Tiled into sheets with the editor thumbnails in
      `Saved/LevelGen/visual/sheets/`.
    - The review is `Tools/LevelGen/VISUAL_CATALOGUE.md`, written by a side
      session. That session deleted the 2.2 GB FBX and texture exports
      because the disk is nearly full (25 GB free).
    - Also: Pinterest and Google Images are allowed for references
      (Claude-Rules §8).
  - **Metal roofs redone with a kisame** (user's shanty photo; "theres
    usually a kisame there", asked where, answered "Both"). In the generator:
    - mostly single slopes;
    - patchwork corrugated `SM_MetalPlate_A` sheets with real laps;
    - roof on a frame 42 cm above the flat ceiling;
    - timber fascia, level kisame boards under the overhangs, barge boards;
    - weatherboards closing the side gaps (one paint per house);
    - galvanised flashing against taller walls.
    - sheet finishes from AssetGen (galvanised, red-oxide, rust; a main
      finish per roof, 25% replacement sheets).
    3,876 items, overlap and nav checks clean. Details in LESSONS.
  - **Hollow-block walls mixed in** (user via the AssetGen thread: "mix the
    new hollow blocks in there, half and half, following the block texture
    rules"; then "use the hollow blocks 25% of the time only"). Each face
    and storey is concrete or `MI_BackAlleys_HollowBlocks`. It was 107/105
    faces at half and half; it's now 25%, with 52 of 212 faces (seed 109)
    in the generator. The level has the 25% mix too: re-applied in one pass
    (user: "Yes, re-apply"), with 1,289 overrides from the plan, 0 failures,
    saved. 139 of the 529 wall tiles are hollow block. The first try stopped
    on the level check because the user was in PIE; it ran once PIE ended.
    Capture `10_wall_mix_25_B12`: B12's north face has hollow block upstairs
    over concrete, next to B8's concrete wall.
    - The plan changed while the rebuild session was placing it. It
      finished, then re-applied the plan's wall materials (1,289 overrides,
      0 failures, saved). A mixed corner capture is good.
    - **Latest rule, replaces what follows** (user: "only use them on walls
      with no windows or doors. They are not to be used for whole houses",
      "the only mixing rule is not to mix on the same face"). 12 of the 52
      windowless faces were hollow block (36 tiles).
    - **30% of windowless faces** (user: "make it 30% of windowless faces,
      following the rules still"): 16 of 52 faces, 46 tiles (seed 107).
      Applied in the level (user: "Yes, apply"): 529 wall pieces, 0 failures,
      saved. Capture `17_hollow_30pct_B11_N`: B11's north face is hollow block
      on both storeys, with a concrete band and drip decals.
    - **Roof timber fixed** (user: "roof textures are busted too", a wedge in
      grey streaks). The pack wood textures are atlases with smeared padding.
      New world-mapped `M_BackAlleys_Boards` and `MI_BackAlleys_Flashing`,
      created headless.
    - **Both applied in the level** (user: "Yes, apply them"): 721 of 721
      pieces, 0 failures, saved. The materials compiled with no checker.
      Captures `14_flashing_B14_new` and `16_boards_wedge_B7`: planks run
      unbroken across each board and wedge, with no streaks, and the flashing
      is a clean grey strip meeting its upstand.
    - **Glass sound fixed (2026-11-04)** (user: "i hear the sound of glass
      when shooting the wall", "it should have been the other way around").
      Cause: `MI_BackAlleys_HollowBlocks` was a child of the Glass jalousie
      material, and its Concrete never applied because
      `bOverridePhysMaterial` was off. The five door MIs had the same bug.
      New concrete master `M_BackAlleys_HollowBlocks`; hollow blocks, jalousie
      (Glass override) and doors moved under it with the flag on; `Flashing`
      got the flag too. 8 of 8, 0 failures, saved, checked in the saved files.
      Capture `18_after_reparent_B11_N` renders normally. **Not tested by
      ear:** the user still has to shoot a wall in PIE.
    - **Per house** (user: "The hollow block placement is awful, it should
      never be beside concrete"). Each house is now one material throughout:
      10 of 41 houses are hollow block (seed 98), and the door end walls are
      concrete. The plan is regenerated and the overlap check is clean.
      **In the level too:** re-applied (user: "Yes, re-apply"): 1,289
      overrides, 0 failures, saved. Capture `11_wall_per_house_B8_B12_B11`:
      B8 and B12 are hollow block on both storeys, and B11 is concrete.
      - **Open:** a wall face to the right of the gallery stairs in that
        view renders saturated blue. It was blue in the 25% capture too.
        B11's east ground-floor tiles (the face that should be there) read
        back as `CHB_Concrete`, with no duplicate actors. So it's another
        actor; clicking it in the editor would show which.
      Touching houses may differ (user: "Yes, neighbours can differ"),
      which is how it's built.
  - **Wall seams fixed (2026-11-04)** (user: "I can see seams on the walls,
    right after the height and alignment parameter changes"). Rounding left
    gaps of up to 0.08 cm between fractionally scaled tiles. Tiles now overlap
    by `TILE_LAP` (0.4 cm); all 306 joints overlap. Applied in the level: 529
    tiles, 0 failures, saved; before/after captures `19_` and `21_joint_*`.
  - **Gallery stairs less steep (2026-11-04)** (user: "too steep and unnavigable",
    "or find a way to make it less steep"). 39 deg became about 30: two flights,
    7 m run, landing at 2 m. Trace: risers 13-17 cm, biggest step 23.7 cm. In the
    level and saved; capture in `Saved/BackAlleys/captures/2026-11-04_stairs/`.
    **Not walked in PIE**, and enemy pathing up them isn't tested.
  - **Bands, borders, hidden patterns (2026-11-04)** (user: "the bands have different
    paint jobs in some houses, try to avoid these", "have patterns in building but
    have the player not see patterns", "the building will either has 1. No borders,
    2. A border 3. A portruding band", "the band between the 1st and 2nd floor, not
    the top floor"). Bands match paint except on 6 of 21 painted houses. Of 31
    multi-storey buildings: 10 border, 12 none, 9 protruding (15 cm; at 5 cm the trims
    hid it). Same paint on wall and band means no border. Colours, grilles and the
    three treatments draw from shuffle bags. Applied and saved, 0 failures. Captures
    in `Saved/BackAlleys/captures/2026-11-04_bands/`.
  - **Drips follow the treatments (2026-11-04)** (user: "reevaluate the placements of
    Dirt decals, becuase of the new border and band rules"). The decal's hard top edge
    was tucked behind the border, which the treatments removed. Behind a protruding
    band now (15 moved); on no-border houses the lower floors' drips are gone (12) and
    those faces get top-floor drips (9). 66 drips, no edge exposed. Applied and saved.
    Captures in `Saved/BackAlleys/captures/2026-11-04_drips/`.
  - **Awnings, first try (2026-11-04)** (user's Manila street photo; "we place them in
    windows and doors", "you can use a base, then put a currogated roof on it", "make
    the awning house wide, If a house uses awnings in one window, then use it for all
    IN THAT FACE"). `SM_awning_base_01` plus a corrugated sheet. 56 awnings on 32 faces,
    all openings on a face or none. No collision. Applied and saved. Captures in
    `Saved/BackAlleys/captures/2026-11-04_awnings/`.
  - **Painted bands always match** (user: "when the face is painted, the band looks off
    if left unpainted. It works for hollow blocks but not for painted"). Treatments are
    now 6 border, 14 none, 11 protruding; 63 drips, no edge exposed. Applied and saved.
  - **Gallery rail swapped** (user: "The gallert rail is the wrong model too"). The solid
    plank is now `SM_Rail_A_001` steel bars at 1.05 m, six pieces. Traces hit the bars and
    top rail; not walked in PIE. Applied and saved. Captures in
    `Saved/BackAlleys/captures/2026-11-04_rail/`.
  - **Music in `Lvl_BackAlleys`** (user: "a bgm manager on the backalley too please"). A
    `Music_Start` trigger in `BackAlleys/Gameplay`: `DarkCrimes`, Play At Start, set like
    `Lvl_Linear`'s. In the plan too, so a rebuild keeps it. Saved; not heard in PIE yet.
  - **Building dressing** (user: "do downpipes and window air conditioning. and the
    overhang rooms, ply patches", "door steps and vent blocks too", "There are alot of
    blank face tiles so I want them to see more"). 149 of 235 blank tiles carry something.
    Rooms 11, downpipes 11, air conditioners 20, 52 plywood sheets in 25 groups and 15 single
    tin, vents on 50 tiles, steps on 19 of 22 doors. Hollow-block faces stay empty. Plywood and vent textures
    are our own, drawn by `make_dress_textures.py`. Traces: rooms' floor and panel and the air
    conditioners stop shots, patches don't. After the first look: patches now real sheet
    size (user: "scale them bigger"), vents one height per face (user: "atleast the same
    height"), thin walls get nothing (user: "a thin wall, not a house"), rooms have a door on
    the wall behind (user: "looks like nothing leads to their right now"). Then: nothing on the
    walls the stairs run against (user: "go into the stairs"), no two pipes close together and
    one per house (user: "never 2 on the same house"), wood sheets at least two side by side
    with tin single (user: "except the roof type, the wood one, yes do 2"). New
    `analysis/check_dressing.py` tests all of these.
  - **Laundry** (user: "start adding laundry hang, but keep it cheap if its far away", then
    "keep the laundry stuff on balconies , or near reach of a window on the second floor. or
    near the doors. never out across the street, if it crosses the street, then make sure its
    on the second floor"). Lines on 4 balcony strips and in 5 rooms, clothes on the gallery
    rail, racks under 6 second-floor windows and beside 5 ground doors, 3 street lines from
    second-floor windows only. Culled at 35 m, clothes with the pack's four LODs, lines as two
    cubes. All dressing applied and saved; overlap check clean, no new nav joins. Lighting not
    rebaked, not walked in PIE. Captures in `Saved/BackAlleys/captures/2026-11-04_dress/`.
  - **Window grilles (2026-11-04)** (user: "find an appropriate window grill and
    put it in the first floor windows", "more variation is appreciated"): 37
    ground-floor windows, five kinds dealt evenly per house. Applied: 37 placed,
    2,004 synced, 0 failures, saved. Captures in
    `Saved/BackAlleys/captures/2026-11-04_grilles/`.
  - **Painted houses (2026-11-04)** (user: "regenerate the level with the new
    paint rules", "One color per house, but some side can remain unpainted").
    21 of 41 houses painted; faces 42 painted, 16 hollow, 54 bare. Half the
    houses, half the windowless sides and unpainted hollow-block faces are
    defaults the user didn't choose. Applied in the level: 2,462 pieces, 0
    failures, saved. Captures `23_paint_aerial`, `24_paint_street`.
  - **Building floors (2026-11-04)** (user: "put the buildings on top of a
    "building floor""): 18 cm concrete slabs, buildings lifted, doors get a
    riser. 3,684 items; overlap and nav checks clean. Applied in the level with
    `sync_plan_ue.py`: 3,586 pieces moved, 82 placed, 0 failures, saved. Traces:
    spawns 0, stairs [400, 238, 74, 400, 74], deck 400, slab top 18. Capture
    `22_building_floor_door_B7`. **Baked lighting is now stale:** rebake.
    Not walked in PIE.
    - **The crash:** out of video memory in GPU Lightmass (`UEMinidump` in
      `Saved/Crashes/UECC-Windows-6DC581EA...`). The bake had 57.9 GB of UAV
      buffers against an 11.3 GB video and 15.5 GB system budget, with system
      memory at the limit. Cause of the size not investigated.
  - **Flashing fix** (from the rebuild captures): the strips sat 9–25 cm
    off the wall (`put_axes` anchor bug and too-short strips). Fixed in the
    generator; all 12 strips are now within 2 cm of their upstands. The
    user approved replacing them in the level ("Yes, replace them"). The
    rebuild session swapped the 25 `Flash_*` / `Ridge_*` pieces: removed
    25, placed 25 from plan chunks 19–25, 0 failures, saved. Capture
    `7_flashing_B14_fixed`: the strip now meets the upstand against the
    wall.
  - **Weatherboards: one board per side, sloping sides sealed.**
    - User: "the back of the roof has 5 wood pieces, use one scaled board
      instead". Then: "can you also make an effort to close the sides … i
      mean seal it".
    - **In the generator:**
      - Each side is one board scaled to its full height; the stacked 20 cm
        rows are gone.
      - A sloping side's board runs to the slope's lower end. An `SM_Ramp`
        wedge in the house's wood paint fills the triangle up to the sheets,
        with two wedges meeting at the ridge on two-slope roofs.
      - 441 boards became 114 boards and 53 wedges; the level is 3,602
        items. Overlap and nav checks are clean.
    - **In the level:** both pieces were swapped in place (the stepped
      boards, then the wedges re-oriented). 0 failures, saved.
    - **Captures:**
      - `8_sealed_side_B7`: no notches. The wedge reads darker and more
        mottled than the board, because its texture is magnified.
      - `9_one_board_back_B7`: a single board under the kisame.
      - The first try stood the wedges upright and their wood read as
        vertical streaks. Laid on its side, the grain runs horizontal.
    The sheets' face is settled: the AssetGen manifest shows they're
    modelled with both faces, and +Y (the wider pans) faces up.
  - **Rebuilt in the editor** (user: "Reconnected, rebuild"; run by a side
    session). Five placer calls (chunks 0–5 with clear, 6–11, 12–17, 18–23,
    24–27 + gameplay): removed 3,195, placed 3,876, **0 failures**, saved.
    Traces as before: stairs `[400, 238, 74, 400, 74]`, deck 400, every
    spawn ground 0 with clear head room.
    - **Wall materials re-applied:** the plan was regenerated at 19:07:58
      (hollow-block mix, seed 99) while the calls ran, 19:00–19:11. So the
      early chunks got the old walls. One fix-up pass:
      - mapped each label to its actor with `get_label` (2,190 actors);
      - set `OverrideMaterials` from the plan on all 1,289 `Blocks` and
        `SpawnDoors` items with `mats`, 0 failures;
      - saved.
      - The placer's actors aren't named by label (`StaticMeshActor_UAID_…`),
        and `find_actors` name-matches substrings.
      - Capture `6_hollowblock_corner_B23`: hollow block meets concrete
        cleanly, and the blocks render textured.
    - **Captures** (`Saved/BackAlleys/captures/2026-11-03_kisame/`), against
      the photo:
      - The three sheet finishes render; no default checker.
      - The patchwork reads right: columns, staggered end laps and
        replacement sheets.
      - The sheets sit on the fascia and barge boards, not through them.
      - Kisame boards are level under the overhangs, but they're in shadow
        and read near-black with preview lighting.
      - Barge and weatherboards (B7) work. Thin dark notches show where
        the stepped board ends meet the barge underside.
    - **Found:** on the 5 roofs whose high edge faces −X/−Y (negative pitch:
      B14, B15, B25h1, B25h2, B9h1), the flashing strip on the sheets sits
      25 cm down the slope. There's 33 cm of bare sheet between it and the
      upstand, where the other 7 have 9 cm. The strip is placed from the
      wrong end in the mirrored case. Seen on B14. Fixed and replaced in
      the level (*Flashing fix* above).
    - **Look vs the photo:** red-oxide is a bright orange; the photo's
      sheets are a dull brick-brown. A tone-down is the user's call.
    - **Capture gotcha, refined:** stale culling can repeat at the same
      transform. A second capture there returned the identical frame with
      B18 missing. A 30 cm move didn't help either. Every bad frame looked
      at yaw 45–80; frames at yaw 0–30, or pitched down onto roofs, came
      out clean. Change the view direction.
- **2026-11-03: Asset thread started; mesh manifest in `Tools/AssetGen/`.**
  The user asked for a separate asset-generation thread, which measures and
  preps the kit so the level generator stops guessing. The level-generation
  thread consumes its output.
  - **`Tools/AssetGen/measure_ue.py`** is headless and read-only: no bridge,
    nothing saved. It measures the 70 meshes `gen_level.py` places and
    writes `manifest/index.json` plus one file per pack. Fields are in
    `Tools/AssetGen/README.md`:
    - bounds, pivot, and which way each piece runs from it;
    - slots with blend mode, LODs, collision type and boxes, sockets;
    - open sides, the corrugation direction, and wedge corners;
    - the openings in wall and frame pieces, and the walk-surface profile
      of stairs and roofs.
  - **Checked:** the hand-measured values agree within 0.5 cm. That's
    `door_bounds_ue.py` and `check_overlaps.py` `LOCAL`.
  - **Answered for level-gen:**
    - `SM_windows_06` has its own-triangle collision with a closed top rail,
      so the banisters do block nav. Its four panes are 40 × 72 cm holes.
    - `SM_Stair_A_001`'s pivot is its top edge; it descends along +X.
    - `SM_Pillar_01` is centred, not min-corner.
    - `SM_Wooden_part_03/05` run along −X.
    - `SM_Slate_01`'s ridges run along its length.
  - **Budget finding:** `SM_MainBorder_04` is 918 placements × 2,510
    triangles = 2.3M, 73% of the level's 3.14M LOD0 triangles, with
    complex collision. `SM_Slate_01` adds 670k. The proposed fix is a
    low-poly trim and sheet of our own (Geometry Script, headless).
    **Not done:** it waits for the user's OK.
  - Found by the run: the mesh-description triangle winding is clockwise
    (spec, *Asset manifest*).
  - **Later the same day:**
    - The AsiaSlum roof sheets `SM_MetalPlate_A_001..004` and MiddleEast
      `SM_wooden_beams_01..05` were added to the manifest, for
      level-gen's metal-roof rebuild. That's 77 meshes now.
    - New fields: the UV direction, which gives the grain, and the
      material parameters. The sheets are modelled two-faced, so either
      side up works.
    - Exported `T_Bricks_01_BC` (the Favela red brick) to
      `Saved/AssetGen/export/` for the user to turn into a hollow-block
      texture with GPT.
  - **Painted roof sheets** (user: "Yes, make them"):
    - `M_BackAlleys_MetalSheet` and three instances, `_Galv`, `_RedOxide`
      and `_Rust`, all in `BackAlleys/` with copied textures.
    - The colours were tuned offline (`preview_metal_sheet.ps1`).
    - **Not yet seen lit in the editor.**
  - **Hollow-block texture** (user: "Here is the zip for the hollow
    blocks", made by GPT from the exported red brick):
    - GPT's mask had merged blocks wherever a joint was faint.
      `repair_chb_texture.ps1` rebuilt the joints from the source's grid
      and made a new normal map.
    - Imported as `MI_BackAlleys_HollowBlocks` (UV0, Concrete). The
      before/after image is `Saved/AssetGen/export/hollow_blocks_before_after.jpg`.
    - **Repair dropped** (user: "I dont want that" → "Use GPT's
      original"). The material now uses GPT's files unchanged.
      - Re-pointed through the bridge and saved alone.
      - The repaired textures are unused; delete them on the user's word.
    - **In the level** through level-gen: 25% of houses are all hollow
      blocks, picked per house.
- **2026-11-03: arena enemies sweep instead of standing around.** The user:
  "when the enemy loses sight… instead of standing around… go from one spawn
  point to the other picked randomly". Then: "I dont mean patrol patrol, I
  meant aggressive sweep to point". Design rule: once alerted, the calm
  patrol never comes back ("goes against the full action setting").
  - **The order:** chase, lose sight, go to the last known spot, wait
    `LeadGoneAfter` there, then sweep from spawn point to random spawn point,
    gun up, at `SweepSpeed 450`.
  - **Only director-spawned enemies** sweep: `AEncounterDirector` hands its
    `SpawnPoints` to each one. Linear-level enemies keep Search/Roam as
    before.
  - **Wrong, corrected 2026-11-04:** this said no `ST_Gunman` change was needed.
    The asset has no transition into Roam, so the sweep never runs. Spec:
    *Arena sweep*, *Roaming*.
  - **Applied by Claude** ("apply and run"). Built clean 18:48; bridge
    checked; DLL newer than source. **Not yet tested in PIE.**

- **2026-11-04: Paint materials from the Favela decals (asset thread).** User:
  "The decals look good becuase they have imperfections, ie concrete base color
  coming through. What I need a wall material based of the look of the decal
  paints, and variants of the decal of usual philippine house colors, so I can
  use it if I want the color change outside of the tile face boundaries."
  - **Made** (headless, in `BackAlleys/`; nothing depends on a pack):
    `M_BackAlleys_PaintedWall` and `M_BackAlleys_PaintDecal`, each with 12
    colour instances. Same colours in both, so they match. Spec: *Asset
    manifest*, *Paint materials*. How to place: `Tools/AssetGen/README.md`.
  - **Cost:** the wall material is slightly cheaper than `M_BackAlleys_CHB`
    (386 vs 408 pixel instructions). The decal adds 360 per covered pixel.
    Not measured on the Deck.
  - **Checked** in a new headless lit preview
    (`preview_painted_walls_ue.py`, shots in `Saved/AssetGen/preview/`).
    **Not yet seen in the level's lighting, and not placed:** §8 only allows
    `MI_Decal_Dirt_08` as a generated decal, and these are for the user to use.
  - **Open:** the 12 colours are from general knowledge, not reference photos.
    The user judges them.
- **2026-11-04: hair shine reduced for baked lighting.** User: "fix the hair
  shine"; "when lumen was on, they looked ok, ever since the switch to
  lightmaps, they behave different"; then "I would rather have a dry look than
  the shiny wet look"; then, with a screenshot, "shiny still" and "I think a
  material change is needed". Lower Specular and higher Roughness didn't get
  there, so `M_Hair_CCMH` and `M_Haircap` moved from the Hair shading model to
  Default Lit (Metallic and Normal pins disconnected), keeping the dry values.
  Saved through the bridge, those assets and the MIs only. **Not yet judged in
  game:** my one capture caught the enemy mid-shot, lit by its muzzle flash.
  Spec: *Hair shine under baked lighting*.
- **2026-11-04: `MaxSmokePuffs` back to 8** (user: "adjust smoke puff back to
  8"; `DA_ImpactEffects`, was 1). That asset's last commit is the 11-01 impact
  performance pass, so later Deck traces likely ran at 1. Not re-measured.
- **2026-11-04: sweep barks and a smaller muzzle light** (user: "apply and
  build"). Sweeping enemies try the Lost Sight bark every 8–15 s. `MuzzleLight`
  went to a quarter: 62.5 cm, 15 cd, read back on all 14 weapon Blueprints. Built
  clean 15:11; bridge checked; DLL newer than source. **Neither tested in PIE.**
- **2026-11-04: muzzle light radius restored, dimmer again** (user: "revert the
  changes to the muzzle light, only change the brightness, it need to be even
  lower than now, but roll back the radius"; "apply and build"). `MuzzleLight`
  is now 250 cm, 3 cd (was 62.5 cm, 15 cd; originally 250 cm, 60 cd). 3 cd because
  the restored radius alone would have made 15 cd about 3x brighter at 50 cm.
  Built clean 23:38; bridge checked; DLL newer than source; all 14 weapon
  Blueprints read back at 250 cm, 3 cd. **Not tested in PIE.**
- **2026-11-04: muzzle flash `Pop` sphere off** (user's screenshot of an orange
  disc at the muzzle; "go"). It wasn't the light: all five flash assets have a
  `Pop` emitter, a glowing sphere mesh. `DetailModeBitmask` 0 on each, saved
  through the bridge, those five only. A headless export confirms only the `Pop`
  emitters changed. **Not tested in PIE.** The sphere ignored the light settings,
  so 3 cd may now be too dim; the user judges. The falloff and specular change
  proposed for the light was dropped for now. Spec: *Muzzle flash*.
- **2026-11-04: `Pop` sphere back on** (user: "revert flash back to the original
  form", then "ok do it" to the option I recommended: `Pop` on, particle lights
  still off). Mask reset on all five, saved through the bridge; a headless export
  shows every emitter at its default. The disc is back. The five assets still show
  as modified in git because they were re-saved: don't commit them, restore with
  `git checkout` once the editor is closed. `MuzzleLight` stays 250 cm, 3 cd.
- **2026-11-05: muzzle flash reverted to the last push** (user: "revert the
  muzzleflash to the last push", `63cd3508`). The five flash assets already match
  it byte for byte. `MuzzleLight` is back to 62.5 cm, 15 cd in source, so
  `WeaponBase.cpp` matches the push. Built clean 01:39 ("run the script"); bridge
  checked; DLL newer than source.

- **2026-11-05: street dressing in the level generator.** User: "whats else can we add?", then "do
  all that and add it to the tool". A last pass in `gen_level.py`, 475 new actors, none of the 4,109
  before it moved: wires and meter boxes, water tanks and aerials, bulbs, tubes and street lamps with
  real Static lights, shutters, gates, tarps, blank signs, window sills, rebar, peeling paint. Our own
  sign and peel textures (`make_street_textures.py`, `create_street_materials_ue.py`). Checks clean,
  and `check_dressing.py` catches faults planted in the plan. Details in `Tools/LevelGen/LESSONS.md`.
  Placed and saved: 475 of 475, no failures. After the first captures: lights dimmed (they blew walls
  out), signs given a flat normal (they looked hammered), light colours fixed (capital keys were
  ignored). Captures in `Saved/BackAlleys/captures/2026-11-05_street/`. Not baked, not walked in PIE.

## 2026-11-05 — Lvl_BackAlleys: long signs only, more power lines
- **User:** "dont use the square signage, use the longer rectangular ones" and "add more power lines, power lines are a big identity show for the philippines" (with a Manila alley photo).
- **Signs:** the 5 square `SM_Sign_B_005` blade signs became long `SM_Sign_A_001` boards over doors and windows (`WallSign_*`). Shop signs are `SM_Sign_A_001` too. `check_dressing.py` fails on any sign under 2.6:1.
- **Power lines:** 84 wires in 22 spans and 13 wall runs (was 23, 11, 7), bundles of 2-6. The Wires folder went from 156 to 493 actors.
- **Applied** through the bridge to the open level: 12 street folders cleared and re-placed, counts match the plan, saved. Not looked at in the viewport. Lighting not rebaked (the static street lights were re-placed). Not traced on the Deck.

- **User, moved over from the Optimization thread:** "fetch those messages and work from here", on the power lines and the ads.
- **Low wires:** 116 more in 28 spans and 10 wall drapes, because from the ground the high ones weren't in frame. The Wires folder is 969 actors. Placed and saved; an earlier layout seen in captures.
- **Posters:** 101 sheets in 32 lots of the user's AI-generated placeholder images, 23 of 24, only candidates repeating ("only put together indentical posters for candidates type posters"), on `STREET_POSTERS`, with wear in a new material and the images untouched. Scale from the user's photo of a Manila wall: about 61 x 91 cm, in blocks up to the trim ("the posters are tiny atm"). Brightness capped ("bright even in shade"). Placed and saved; seen in captures in `Saved/BackAlleys/captures/2026-11-05_posters/`. Lighting not rebaked, not walked in PIE.
- **Edge rule:** posters, shutters, signs, meters, tarps and gates stay 40 cm from the ends of a face. `check_dressing.py` tests it.
- **The editor crashed** (21:55) as I changed the instances' parent through the bridge: a D3D12 access violation. Everything else had been saved. The change is done headless with the editor closed instead; see LESSONS.
- **New tools:** `plan_delta.py` and `apply_delta_ue.py`, to re-place only what changed.
- **Daylight:** user: "I will keep this level on daylight so the lights should be off". The light actors are gone; bulbs, tubes and street lamps stay as unlit fittings. `STREET_LIGHTS_ON` brings them back.

- **2026-11-06: Deck build, `Lvl_BackAlleys`** (user: "make a deck build, backalley level"). Added the level to `MapsToCook`; the peer was idle. `BuildDeck.ps1`, 5 min, exit 0: 4,414 packages cooked, 0 errors, 20 warnings (the old resave notices, none from the level). 3.1 GB, was 2.3. Its lighting data is in the package, but it's the 11-05 02:48 bake: 1,382 of 5,587 actor files were saved after it. Start command: `ProjectBopis/Binaries/Win64/ProjectBopis.exe Lvl_BackAlleys -ExecCmds="stat fps,stat unit"`. **Not yet run on the Deck.**
- **2026-11-06: power lines chained** (user: "try to chain connect powerlines"). A new last pass in `gen_level.py` (`STREET_CHAIN_WIRES`): 64 links, 142 wires, 21 new boxes; 73 separate hops became 30 groups, the biggest with 18 boxes. 561 actors placed and saved through the bridge, none moved or removed; the Wires folder is 1,530. `check_overlaps.py` and `check_dressing.py` are clean. Seen from the ground in one capture; not walked in PIE, not in the 00:30 Deck build. LESSONS: *Chained power lines*.
- **2026-11-06: open stalls closed, ground walls filled** (user, from PIE: "the wall if open. Try to not have any first floor walls featureless, except hollow block, which yu can put posters on"). B2's two visible stalls got a solid wall and a roll-up shutter; the third stands inside B6, so it got nothing. Posters now go on hollow-block faces, door end walls, B2's plain stretches and the wall under rooms: 258 sheets in 83 lots (204 election, 30 movie, 24 ad), up from 101; asked whether to thin them, the user said "Keep them". The level is 6,200 actors. Placed and saved, no failures; `check_overlaps` and `check_dressing` clean; seen in captures, not walked in PIE or rebaked. Bare ground wall left: two stair walls (exempt), two stretches of 1.6 and 2.2 m, and short returns. Details in `Tools/LevelGen/LESSONS.md`.
- **2026-11-06: posters under the vents** (user: "even this is bare, it has vents but needs something", of `B18`'s wall). Posters only fitted under the highest vents, so walls with vents stayed empty below them; my bare-wall measure missed it too, as one vent counted the whole wall as dressed. Two shorter poster bands; `check_dressing` now tests posters against vents. 300 sheets in 95 lots (240 election, 35 movie, 25 ad), and the level is 6,242 actors. Placed and saved, no failures, both checks clean, seen in captures. Longest bare stretch at eye level is now 2.3 m, apart from B11's stair walls.
- **2026-11-06: poles, tyres, water meters, graffiti** (user: "do the building centric ones first", "added 10 graffitits"). 7 power poles with their lines, 30 tyres on roofs, water meters and 16 graffiti decals from the user's masks, on their own switches and folders. Nothing already in the level moved. Then the water meters were spread out (user: "the water meter needs to be distributed more"): from 17 in 9 lots, bunched in the east, to 32 in 20 lots over the whole level, 7.6-11.3 m from the nearest other lot. The level is 6,707 actors. Placed and saved, no failures, all checks clean, seen in captures. Not walked in PIE, not baked. The Wires folder is now 1,828 actors, not traced on the Deck. New materials darken the tyre and turn the meter to brass; the pack's assets and the user's images are untouched. Details in `Tools/LevelGen/LESSONS.md`.
- **2026-11-06: big graffiti, the ground, bigger posters** (user: "yes do grafitti on hollow blocks, actually allowed to paint them big. Do the ground pass after"; then "The posters are generally tiny", "Ads and campaign material needs to be seen from further away", "there is no way he was able to stick that behind the post", "metal square grates are not common in the ph"). 6 big crew tags on the upper storeys of hollow-block walls. Ground: poured concrete bays and repairs over the old asphalt (`M_BackAlleys_GroundPour`), 139 ground decals (grime, grit, run-off, heaps, specks, 5 manholes), 129 litter props with no collision. Posters 1.8 times bigger where the wall allows: 300 sheets became 143, median 134 cm tall. 4 sheets behind a post removed, and both that and square grates are now failures in `check_dressing.py`. Checks clean; applied by delta and saved. The level is 6,899 actors. Seen in captures, not walked in PIE, not rebaked.
- **2026-11-06: dirt lined up with the houses** (user: "Your decal alignment for the Dirt decals to the edge of the houses are bad at the moment. They either go above to the floor lining OR they do not hit the edge at all"). The decal box was tall enough to smear up the lining, all 13 door decals stopped 12 cm short, and strips ran past the ends of walls. Now 2 cm deep, with the dense edge 1 cm under the lining's real edge on all 62 strips and door decals, placed from the floor slabs themselves and failed by `check_dressing.py` if not. New `M_BackAlleys_GroundGrime` fades strips' ends. Then (user: "1rst one overshoots the house", "the decal shoud be super thin and hit just about the surface of the road"): run-off and drip stains fitted to the lining too, so none runs past a corner; pours lowered to under 0.8 cm so decals can stop 1.1 cm above the road; pours cast no shadow, which removes a black line along their edges; finer asphalt grain on patches. Applied and saved, seen in captures at lining height and at a corner pipe.
- **2026-11-07: physical props, planned** (user: "I want bullets to affect them, some props like the filled bucket need to be static. weld them if they are separate pieces, dont affect navigation. as you suggested, only light things", then "make sure whatevr is a physical object does not overlap initially to any other object"). 30 light pieces physical (monobloc chairs, stools, the two-seat bench, empty buckets), 2 lids welded to their buckets, asleep until hit, out of the nav mesh, no overlap events. Every ground prop now tested against everything near it from measured bounds: 15 dropped, 178 props, checks clean. **Not placed:** the editor bridge dropped out of the session. **C++ given for bullets to push props, not yet typed or compiled.** Welding needs the bridge's attach call, to be found when it's back.
- **2026-11-07: physical props placed, lids welded, trash bags physical** (user, mid-task: "do the trash back with physcics as well if you are not already").
  - **Placed by delta, 0 failures, saved:** the 30 light props, and `Prop_Bucket_5_0`, which a bag used to block.
  - **Read back from the editor:** Movable, `PhysicsActor`, simulate on, asleep, mass overridden, no nav, no overlap events. `objectType` stays WorldStatic or WorldDynamic until the level reloads.
  - **Lid profile bug, fixed:** setting `Mobility` after `BodyInstance` reset the lids to `BlockAllDynamic`. All three placers now set `Mobility` first.
  - **Lids:** attached to their buckets with `ActorTools.set_parent_component` and not simulating. The engine's `bAutoWeld` welds them when play starts. Not checked in PIE.
  - **Trash bags:** 18 of the old 25 are physical. They had been lying inside each other, so they're now spaced in rows, and 7 didn't fit their stretch. They use project copies with simple collision (`SM_BackAlleys_GarbageBag_*`), weigh 1.6-4 kg and use Cloth. The 4 flattened boxes under them are out.
  - Captures are in `Saved/BackAlleys/captures/2026-11-07_physics/`. Not committed.
- **2026-11-07: wall patches play their own impact** (user: "the sheet metals and wood on the walls are not playing the correct impact").
  - **Cause:** all 67 patches (52 plywood, 15 tin) were placed with no collision, so a shot went through and played the wall behind.
  - **Fix:** they're now `IgnoreOnlyPawn` with a surface per piece (Wood for plywood, Metal for tin) and out of the nav mesh. Shots and props stop on them; pawns pass.
  - **Verified:** placed and saved. A trace stops on a plywood sheet at 60.0 cm, where the wall is 1–1.4 cm further back, and on tin at its front face. `check_dressing` tests it. Not committed.
- **2026-11-07: monobloc colour picked once** (user: "there are still issus with the monobloc MI, for the other stool 02", then "Can we actually just code the material so it does not regenerate the color if moved? only generate on spawn time?").
  - **Cause:** `MM_BasicProp`'s `Activate Random Color?` runs `MF_PerInstanceColor`. It looks the colour up in `TX_ColorVariation_BC_01`, a 4 × 4 palette, at the piece's world position × 10 per cm, so a moving piece flips colour every millimetre. 8 of the 11 monobloc instances had it on; only `Chair_01a`–`c` didn't.
  - **Fix:** `MF_PerInstanceColor` (pack) has a new switch, `Colour From Spawn Seed?`, off by default, so the rest of the pack is unchanged. When it's on, the palette cell comes from `Spawn Seed`, read from the piece's custom primitive data 0.
  - Four `*_SpawnColour` instances in `BackAlleys/Materials/Monobloc` turn it on. The generator gives each monobloc piece a seed and the placers write it. Table seats share their table's seed.
  - **Placed:** 20 pieces, saved. Seeds read back. A chair moved 40 cm kept its colour (captures `3_seed_chair_before`, `4_seed_chair_moved_40cm`).
  - The 64 baked fixed-colour instances from the first approach were deleted at the user's word ("Delete them"). Nothing referenced them, and only the four `_SpawnColour` instances remain. Not committed.
- **2026-11-07: bags fixed, pots physical, caps, chair colour** (user, from PIE: "the bags dont trigger physics. The pots dont get physics, the monobloc MI for chair 1 (not 1b) has code that changes his color in realtime, so you cant use that one. also the chairs go flying when you walk to them. cap their velocity", then "the pots and bags dont even collide").
  - **Bags:** the copies' hulls had never been cooked. Unreal skips the hull of a complex-as-simple mesh, and switching the flag by property doesn't re-cook it. `StaticMeshTools.generate_convex_collisions` (1 hull, 32 points) rebuilt them, and a physics overlap query now finds the bags.
  - **Pots:** 48 of 60 are physical: Clay for terracotta, Plastic for the coloured ones, Metal for tins, 1.7-12.4 kg. Their plants are attached with no collision. 10 balcony pots that touched a band, a pole, a post or another pot are out, with their plants.
  - **Caps on all 97 physical pieces:** pushed out of an overlap at 150 cm/s at most, spin capped at 720°/s.
  - **Chairs:** no chair uses `MI_Monobloc_Chair_01` any more.
  - Placed and saved: 136 placed, 39 attached, 0 failures. Read back from the editor. Not committed.
  - **Cause of the flying chairs:** the player's movement component pushes with the engine default of 750,000 whatever the mass, which on a 2.5 kg chair is about 50 m/s a frame. A body has no setting to cap its straight-line speed. **C++ applied by Claude on the user's OK ("Apply it yourself"): a mass-scaled push in `AProjectBopisCharacter`'s constructor (`bPushForceScaledToMass`, `InitialPushForceFactor` 150, `PushForceFactor` 1200). Built clean with `RebuildEditor` (26 s). After the rebuild the bridge answered `list_toolsets`, and the DLL (14:56:31) is newer than the source (14:53:28). Not yet tested in PIE.**
- **2026-11-07: the "backwards door" was a steel gate; business posters and lettered signs** (user: "this door is backwards and not in contact with the wall", then, mid-task, "Project_Bopis_Local_Business_Signs Added, use this for new posters (add, dont replace the ones already there), then add the signage to the apprpriate signboards").
  - **Gates:** the green door was `SM_Metal_Gate_01`, hung frame-out 8 cm off the wall. All 4 gates now show their plain sheet, with the frame against the wall. Traced and seen in captures.
  - **Posters:** the five business posters join the ads, and all 28 designs are in use. The poster lots were re-drawn: 139 posters, 19 graffiti. Their grime is turned down, as it showed as camouflage on white paper.
  - **Signs:** the five wall boards are on five of the ten signs, each once, sized to their image. Sari-sari, xerox and carinderia are over shutters; the barber and the tailor are over house doors with a clear view. Five signs stay blank. New: `M_BackAlleys_SignBoard` and 5 instances, plus 5 poster instances, made headless.
  - Checks clean. Applied in three deltas (173 out, 169 in) and saved; 7,098 actors. Seen in captures, not in PIE. Not committed.
- **2026-11-06: rice sacks up, plants by doors, a clean table** (user: "move the ricebags to the secured balconies, put some potted plants along the wall near doors where you can", "the table texture is a filthy texture, create a new instance of it where its not filthy", "one of the chairs is into the wall too"). 21 sacks on balcony floors, none on the street. 13 pots by doors. `MI_BackAlleys_Table_Clean` turns the pack material's wear down and makes its metal top matte; the pack's textures aren't touched. Furniture now can't stand in a wall: 5 pieces did, and generator and check both test footprints. Pots stay out from under tables, and table seats out of doorways. 188 props, 7,136 actors. Checks clean, applied and saved. Seen in captures, not in PIE.
- **2026-11-06: things people use** (user: "wooden bench-stools, plastic seats and tables in some areas. Buckets, potted plants on the balconies"). Then "monobloc stool 02 is a chair, not a table", "use the chairs near doors". 127 props: 4 wooden tables with 2-3 seats each, 7 seats by doors, 7 wooden benches and 6 stools, a two-seat monobloc bench, 11 buckets, 44 pots and 27 plants on balconies. No pack has a wooden stool or a plastic table: a squeezed AsiaSlum table makes the bench and stool, and the market pack's table stands in for plastic. Furniture stops shots but pawns walk through it, so fights and nav don't change. Checks clean, applied and saved. The level is 7,088 actors. Seen in captures, not in PIE.
- **2026-11-06: road repairs made dark** (user: "avoid these strips are too bright, if you are going to put something like this, then keep them darker"). All 6 are now one dark asphalt tone, darker than the road in sun as well as shade. Positions unchanged. Saved.
- **2026-11-06: concrete planes no longer overlap** (user: "theres a shimering overlap here when moving the camera, plane clipping I think Ground_3_0_0_0", "theres a couple of them actually"). 19 pairs overlapped, from a slip in the cut across wide stretches. Fixed: 132 bays and 6 repairs, none overlapping, and `check_overlaps.py` tests it. The level is 6,961 actors. Stills can't show shimmer, so the user judges it moving the camera.
- **2026-11-06: graffiti made solid** (user: "the warning and tag decals are to faded"). Stacked fades: the masks' ink samples at 0.75-0.95, Strength 0.92 and Wear 0.55. A new material, `M_BackAlleys_SprayDecal`, holds the ink at full with only a little wear, and the paints are stronger. All 16 decals swapped and saved, nothing else moved, seen in captures of a black tag and a white one. The user's images are untouched.
- **2026-11-06: stall overlaps fixed** (user: "Shop A 001, overlapping surfaces with wall"). Two causes, both mine: the first stall's closed wall sat exactly on its frame's plane, and a stall I'd called hidden stood 60 cm past `B6h2`, lapping the next stall. The wall now stands behind the frame, and that stall is out of the level (`B2_S0_1_1`). `check_overlaps.py` tests both, and caught both before the fix. Nothing else moved; the level is 6,706 actors. Seen in captures of both stalls.
- **2026-11-06: no tarps on doors** (user: "dont put a tarp on the doors"). The four door tarps are out of the level, saved, and nothing else moved: the three on plain wall stay. `check_dressing` now tests it; both checks clean. The level is 6,238 actors.
- **2026-11-06: the player's rounds fly 2x in Focus** (user: "can we 2x the bullet speed only for the player guns when in focus mode?", then "apply and build"; applied by Claude). `AProjectileBase::ApplyFocusSpeed` scales `MaxSpeed` and `Velocity` by `FocusSpeedMultiplier` (2, grenades 1), called from `FireProjectile`. Built clean 10:37; bridge checked; DLL newer than source; files read back; the round classes read back at 2, the two grenades at 1. **Not tested in PIE, not in the 00:30 Deck build.**
- **2026-11-06: music keeps its voice; `Lvl_BackAlleys` is the default map** (user: "BGM cuts off, seems to do it because of max sound stuff, happens often when i pull out the Machine Pistol and start spraying", then "apply and build, also set backalley as the default map"; applied by Claude). `UMusicSubsystem` sets `bAlwaysPlay` on the track. `DefaultEngine.ini`: `EditorStartupMap` and `GameDefaultMap`. Built clean; DLL newer than source. **Not tested in PIE.**
- **2026-11-06: dropped guns hold 1 to 1.5 magazines, tunable** (user: "change the drop rate, make it tunnable. For now set it to 1 mag + random(0, half mag)", then "change it so that extras dont stay on the ground", then "apply and build"; applied by Claude). `AWeaponPickup`: `BaseMagazines` 1, `RandomExtraMagazines` 0.5. A new gun takes a magazine and the rest goes to the pool; a gun already owned fills the pool and goes, leftovers lost. Built clean 12:53; bridge checked; DLL newer than source; all four pickup Blueprints read back at 1 and 0.5. No pickups are placed in the three levels, so only enemy drops use it. **Not tested in PIE.** The Deck build the user started was stopped first ("actually not yet"): not made.
- **2026-11-06: M4 stock collapsed** (user: "could you make the M4 compact the stock, its super extended at the moment and its cutting into the shoulder on aiming"). New mesh `SK_AR4_CompactStock` on the same skeleton, 9 cm shorter in the mesh and about 10 in game, on `BP_AssaultRifle` (bridge, saved; `SK_AR4` untouched). Spec: *5.56 Assault Rifle*. **Not seen on the shoulder yet:** the user aims with it in PIE.
- **2026-11-06: Deck build, no trace** (user: "make a deck build, no trace"). All six peers idle. `BuildDeck.ps1`, game exe 20:32, 3 min, exit 0: 4,493 packages cooked, 0 errors, 20 warnings. 3.1 GB. It holds the poster bits (`NS_ImpactPosterBits` is in the package), the collision and surface passes, and the 8 moved shutter sheets. Lighting is the 12:53 bake. Default map `Lvl_BackAlleys`; start command `ProjectBopis/Binaries/Win64/ProjectBopis.exe Lvl_BackAlleys -Deck -ExecCmds="stat fps,stat unit"`. Not yet run on the Deck.
- **2026-11-07: Deck build, no trace** (user: "Deck build no trace"). Both live peers idle, the third offline. `BuildDeck.ps1`, game exe 17:16, 7 min, exit 0: 4,756 packages cooked, 0 errors, 20 warnings (the old resave notices). 3.3 GB, was 3.1. It holds the day's physical props, wall-patch surfaces, monobloc colour, gates, and the business posters and signs (all 10 of the user's sign images are in the package). The lighting data was saved at 17:15, as the editor closed, and no actor file is newer; the file dates don't show whether that was a full rebake. Start command as before. Not yet run on the Deck.
- **2026-11-07: the arena reloads when cleared; `Lvl_BackAlleys` is now `Lvl_BackAlleys_Arena`** (user: "do a level reload after killing all the enemies in BackAlley, rename BackaAlley to have _Arena, this namiing convention is what we will use to split Story vs Arena levels", then "apply and build, do the rename during the restart"; applied by Claude).
  - **Code:** `AEncounterDirector::ExitOnCleared` and `ExitDelay` (1 s): when the set fight is done, after the kill cam and the delay, the director fires its exit. `ALevelExitTrigger::bWalkIn` (default on) turns walking in off. Rebuilt clean 17:58 (`RebuildEditor.ps1 -NoLaunch`; all peers idle); bridge answers; DLL newer than the source; files read back.
  - **Level:** `Exit_ArenaCleared` in `BackAlleys/Gameplay`, walk-in off, restarts the level; the director links to it (`TotalEnemies` 20). Saved and read back. Not yet play-tested.
  - **Rename:** done in the editor with the level open: 7,207 actor files, 46 object files and `_BuiltData` moved; no redirector; the old folders are gone. The first two tries were refused (the "may need Find/Replace" prompt cancels itself under the bridge) because editor settings named the level: the default maps (set in memory first) and two per-user entries in `EditorPerProjectUserSettings.ini` (removed while the editor was closed; backup in the session scratchpad). `DefaultEngine.ini` (startup and game maps), `DefaultGame.ini` (`MapsToCook`), the `Tools/LevelGen` scripts, the spec, `ProjectPlan`, `LESSONS` and `README` use the new name; older log entries keep the old one. Spec: *Levels*, *Level exit*. Rule: `Claude-Rules.md` §8 *Level names*.
  - **The lighting** moved with it: today's 17:11 GPU Lightmass bake (13:49 min, 7.7 MB; the 11-06 bake was 1.1 GB).
  - **Start command now:** `ProjectBopis/Binaries/Win64/ProjectBopis.exe Lvl_BackAlleys_Arena -Deck -ExecCmds="stat fps,stat unit"`. The 17:16 Deck build still has the old name inside.
- **2026-11-07: the cleared-arena reload taken out again** (user: "the level reset is not working. Also I dont want an exit trigger at all, the resets will be handled by the menu screen when it comes. I tested and killed all enemies but the level never restarted", then "apply and build"; applied by Claude). Why it didn't fire wasn't found: the editor log has no Play session after the 18:01 restart, so the test was probably the 17:16 Deck build, cooked before the change. Not looked into further, as the feature is gone.
  - **Level:** the director's `ExitOnCleared` cleared, `Exit_ArenaCleared` deleted (its file is gone), saved; only the director's file was written. The rename stays.
  - **Code:** the four files (`EncounterDirector`, `LevelExitTrigger`, `.h` and `.cpp`) restored from git, so `ExitOnCleared`, `ExitDelay` and `bWalkIn` are gone and they match the last commit. Rebuilt clean 19:34 (`RebuildEditor.ps1`; Main Menu work was busy and said "safe", the rest idle or offline); bridge answers; DLL 19:34:26 newer than the source 19:32:38.
  - **Rule:** arena levels get no exit or restart (`Claude-Rules.md` §8, spec *Level exit*). `ALevelExitTrigger` stays for story levels (`Lvl_Linear` has one). *Amended later the same day, below.*
- **2026-11-07: linear levels, suggestion given** (user: "Suggest how we handle linear levels. In theory the level should be able to handle 30 to 45 mins of gameplay without loading"). In chat only, not yet agreed: a chapter as a small persistent map (not World Partition) with classic streamed sublevels, two per section (`_Art`, `_Gameplay`), loaded at connectors and unloaded behind one-way points. Death respawns at a checkpoint by reloading only that section's `_Gameplay`, never the map. First a 3-section greybox measured on the Deck. Open design calls: checkpoint spacing, whether props reset, story moments at transitions, backtracking.
- **2026-11-07: a cleared arena restarts, through its director** (user: "The BackAlley Arena clear is not restarting after clearing", then "Restart, no exit actor" when asked, then "apply and build"; applied by Claude).
  - **Code:** `AEncounterDirector::bRestartOnCleared` (default off), `RestartDelay` 1 s, `RestartFadeTime` 1.5 s. After the kill cam and the delay, `ULevelTravelSubsystem::FadeAndOpenLevel` reloads this level, as the death restart does. Built clean 21:50 (`RebuildEditor.ps1`; all peers idle); bridge answers; DLL 21:50:22 newer than the source 21:49. It needs the Main Menu session's `LevelTravelSubsystem` files, which aren't committed yet.
  - **Level:** on for `Lvl_BackAlleys_Arena`'s director, saved (the file has it). No actor placed.
  - **Not tested in Play:** the bridge can't kill enemies (no console commands, and actors can't be removed during Play). The attempt only changed the Play copy, and Play was stopped; the editor's director reads back `TotalEnemies` 20.
  - **Rule amended:** no exit actor in arenas; the director restarts a cleared one until the menu screen does it (`Claude-Rules.md` §8, spec *Level exit*, plan *Main menu*).
- **2026-11-07: on the list, enemies path around physical props** (user: "The Enemy AI should be able to navigate around the physics objects, I think they get stuck and tries to push through them instead of around"). Plan item 49, with the cause (the props don't affect navigation, by the user's earlier call, for cost) and the options. Not started.
- **2026-11-07: linear slum level, paper layout** (user: "Linear Level Design: Slums"; "we have a slum generator already I think, is that usable?"; then the scenario, pasted; "the level gen tools will need to be able to generate interiors for the final compound bit, multi level trap house looking area"; "take that into account and produce a paper layout"; "take into account the section setup we were planning, break long sightlines if you can"; "We will also add new features, such as interactable inspects for story beats, ie the patrol car").
  - **Generator:** usable, but not as it is. `gen_level.py` reads its layout from JSON, but it assumes one arena rectangle, names arena blocks (`B2`/`B10`/`B11`) in code, expects one deck and spawn doors, and builds shells with no interiors.
  - **Scenario imported** into the lore notes (*LEVEL SCENARIO — THE MISSING PATROLMAN*). The protagonist's name, **Navarro**, is new canon. Summarised in the GDD (+ `.html`).
  - **Layout:** `Design Document/Linear_Slums_Layout.html` + `.json`, from `Tools/LevelGen/layout_linear_slums.mjs`.
    - Seven streamed sections: main street (walk-around, civilians), eskinita, the yard (patrol car), row houses, covered alley + bodega, holding house, trap house (3 levels).
    - 12 fights, 49 gunmen, 8 inspects, 8 checkpoints, 34-48 min.
    - The sightlines are measured by the script. The first draft had 28-38 m lines; bends, offset doors and tall pallets, crates and a van brought the longest in a fight space to 25.3 m.
    - Checked in the browser pane at desktop and phone width (no sideways page scroll).
  - The streaming plan is now the spec's *Linear levels* (the user took it up). Plan item 50. Nothing built; nothing committed.
  - Enemy weapons use the Uzi, not the old slice brief's MAC-11 (gone from the project since 10-30).
  - **Arms tweak, same day** (user: "Remove ammo drop and weapon suggestions. For Level 1, only .45 pistols and shotguns"). The layout now has:
    - no placed ammo, weapons or grenades, and no per-fight weapon lists;
    - first aid as the only pickup (3);
    - one rule for the level: .45 pistols, revolvers and shotguns only, for Navarro and the gunmen (revolvers added: "and revolvers actually").

    Enemy gun drops are unchanged. Regenerated, and checked in the browser pane.

- **2026-11-08: inspects proposed, first design answers** (user: "Propose the interaction inspect mechanic", then "1. Voice and subtitle, subtitle subject to settings. 2. Silent count, dont show it but will trigger achievements. Issue with MP3 is OCD guys will restart the level if they missed something. 3. move for them 4. What do you mean?"). The decisions went into the lore notes (*Inspects*), the spec (*Inspects*), the GDD (+ `.html`) and plan item 50. Nothing built. No crouch, reach or pick-up animations exist in the project.
- **2026-11-08: inspects as mini cutscenes; step 1 built** (user: "The inspect will be mini cutscenes essentially", then "lets do it", "apply and build"; applied by Claude). New: `IInteractable`, `UInteractSubsystem`, `UInteractComponent` (on the player), `UInteractPromptWidget`, a bare `AInspectPoint`; `InteractAction`, `DoInteract` and `IsOutOfCombat` on the character. Compiled clean 16:52 (the slum-build session was busy and said "safe"; the rest idle or offline); DLL 16:52:27 newer than the source; files read back. The relaunch briefly opened a second editor (it closed at 16:55; the bridge restarted at 16:56). `IA_Interact` (copy of `IA_Heal`) made and set on `BP_PlayerCharacter`, saved, on disk. Not tested in Play: the keys and the prompt widget are the user's. Spec: *Inspects*.
- **2026-11-08: the prompt's visibility binding** (user: "cant bind visibility to a bool", then "apply and build"; applied by Claude). `UInteractPromptWidget::GetPromptVisibility` (HitTestInvisible or Collapsed); `USubtitleWidget`'s comment no longer says to bind visibility to a bool. Built clean 17:11 (the slum-build session busy, said "safe"); DLL 17:11:33 newer than the source; bridge answers; one editor.
  - **`Tools/RebuildEditor.ps1`:** no longer opens a second editor if one is already open when the build ends. The last run left two: one opened elsewhere at 16:52:20, during the build, then the script's own at 16:52:28; they fought over the bridge port. It now says so and asks for a restart if that editor might have the old code.
- **2026-11-08: inspect cutscenes, step 2a built; a test sequence** (user: "cant we just cut into the clip instead of moving", then "can you build the level sequence?", "apply and build first, then try that"; applied by Claude). No walk-up: the press cuts into the sequence and Navarro is put on the inspect's `Mark` under the first shot. First build failed on my `bHidden` parameter (C4458; the editor stayed closed), renamed `bHide`, built clean 18:28 (the slum-build session asked to wait for its bridge script, then said "safe"); DLL 18:28:34 newer than the source; bridge answers; one editor. `LS_InspectTest` built headless (`Tools/Cinematics/make_inspect_test.py`) and set as `Cutscene` on `Lvl_01_Slum`'s `InspectPoint_1` (not saved: the user saves the map). Not tested in Play. Gotchas in the spec (*Inspects*): the bridge's `trace_world` is wrong for floors; Can Blend and easing can't be scripted. Spec: *Inspects*.
- **2026-11-08: inspect cutscenes play a double** (user: "fix the stand in first, put it as the player. Also dont use Navarro as a name yet", "The concern I have is the sequence fighting with ticking game code", "Can you just replace the model with a BP_Player_Cutscene?", then "apply and build"; applied by Claude).
  - **`BP_Player_Cutscene`** (bridge): `BP_Player_CC` copied and reparented to `Character`; no AI, movement off, no collision, the player's capsule and mesh offset copied back (the reparent had lost them). Compiled, saved.
  - **`LS_InspectTest`** rebuilt three times headless (the open editor's copy deleted through the bridge first each time): now the double on the Mark, tagged `Player`. Set on `InspectPoint_1` (the map was saved since, not by me).
  - **Code:** `AInspectPoint` hides the real player and his gun and takes him out of play; follows the double; puts him back where it finished. The rename (`PlayerTag`, `InspectingPlayer`) went in with it, plus `bTookPlayer` (not in what I presented: so a failed start can't touch the player). Built clean 20:18 (all peers idle); DLL 20:18:52 newer than the source.
  - **Rule:** no character names in code or assets (`Claude-Rules.md` §7).
  - **Guns in cutscenes:** proposed (`ACutsceneGun`), on the plan, not built.
- **2026-11-08: the double built ahead; the head glance** (user: "he appears after the cut, half a second too late" (the start, when asked), then "apply and build"; "implement the neck turn (look at inspectable)", then "apply and build"; both applied by Claude).
  - **Double built ahead:** each Inspect Point spawns its `DoubleClass` (`BP_Player_Cutscene`) at level start, hidden and still, on the floor under the Mark, and hands it to the sequence at the cut. Likely cause of the late pop: building the CC character at the cut, and the engine's default of not drawing a new mesh until its shaders are ready. Compiled clean 20:56 (the slum-build session said "safe"); one editor; bridge answers.
  - **Glance:** the player's head turns to the nearest usable inspectable within 4 m and 90° of his facing, through the existing head look; not with the gun up. Compiled clean 21:08 (all peers idle); DLL 21:08:59 newer than the source; one editor; bridge answers.
  - **Neither tested in Play.** Spec: *Inspects*.
  - **Then (user: "the double is in there spawned and A-posed"):** the Character Customizer shows its character itself once its clothes and hair have async-loaded (`UnhideCharacter`), which undid the waiting double's hide, and was the half-second pop all along. `AInspectPoint::WatchDouble` hides it again when that happens, then stops (30 s at most). Applied by Claude, "apply and build". The first rebuild stopped at a save prompt (120 s, never forced); the user saved and closed, then it built clean 21:22; DLL 21:22:02 newer than the source; one editor; bridge answers.
  - **Tested (user):** "looks good so far"; the double has his hair ("he HAS hair"). The glance isn't confirmed yet. **Parked** by the user: "park the cutscene bit for now. I actually want to test the level for playability first and foremost".

### ▶ RESUME HERE
- **Mission 2 layout (2026-11-13): drafted, waiting on the user.** `Design Document/Linear_Restaurant_Layout.html`. Their calls are its *Open* list (name, time of day, the restaurant, arms, the informant, who recognises him, the street before the fight, burning on a clock, the passport maker, the end). Lengthened to about 25-45 min with the back alleys and a safe house; no live civilians. Wave encounters need building (plan 52; share with the arena director, 51).
- **Impacts lit, per vertex (2026-11-12): accepted** (smoke "ok", blood tuned to 0.35, then "make all tests ok. I'll bring it up again if its broken"). Not traced on the Deck. Too dark: per-pixel lighting (`TLM_VolumetricNonDirectional`) or a little emissive back through `Unlit Brightness`. Deck cost estimated about 0.2 ms, not traced. Spec: *Unlit impact effects* → *Lit again, per vertex*.
- **Muzzle flash (2026-11-11): tested** (user: "tested, all good"). Our own mesh flash (`UMuzzleFlashComponent`, `M_MuzzleFlash`) on the pistols, revolver and shotguns (round base, `SM_MuzzleFlash`) and the M4 and AK (spiky star, `SM_MuzzleFlash_Star`); the pack keeps the smoke, streaks, sparks and embers. Tune on `MI_MuzzleFlash` / `MI_MuzzleFlash_Star`, sizes in each gun's `FlashSettings`, `SlowMotionMaxStretch` if it hangs in Focus. The sniper stays on its pack flash (user: "leave the sniper"); the grenade launcher is unchanged. Spec: *Muzzle flash mesh*.
- **Doorway aim (2026-11-11): tested** (user: "tested, all good").
- **Door nav links (2026-11-11): built 21:24, checked 2026-11-12.** The user ran Build Paths and saved; `Tools/LevelGen/analysis/check_door_nav_ue.py` found all 6 doors OK (240–246 cm, none partial). Accepted (user, 2026-11-12: "make all tests ok"). A door added later needs Build Paths and a save again. Spec: *Swinging doors* → *Nav link*.
- **Blood splash (2026-11-12): `Unlit Brightness` 0.35 on `M_ImpactSplashSubUV`** (1.0 glowed orange in shade, 0 read black, 0.15 "still too dark"). Accepted (user, 2026-11-12: "make all tests ok"). The aim, if it's off: dark red in shade, not black and not glowing. If the knob can't get there, make the blood colour lighter in `NS_ImpactBlood` instead. Orange rather than red: the particle colour in `NS_ImpactBlood`. Impacts stay lit (user: "keep the impact lit for now"; smoke "ok"). Spec: *Lit again, per vertex*.
- **Bodies through posts and walls (2026-11-12): built 15:25.** Accepted (user, 2026-11-12: "make all tests ok"). If it comes back: the body should drop on the near side, not wrap round the post. Tune `DyingWallMargin` (12 cm) if it drops too early beside walls. Spec: *Dying bodies adrift* → *Caught earlier, and CCD*.
- **Trigger finger tracks the trigger (2026-11-12): done, accepted** (user: "keep this fir now, make all tests ok. I'll bring it up again if its broken").
  - The Trigger Finger node curls the index about its own axis and rests the trigger on the middle segment, Contact Along 0.75 on both nodes in `ABP_Player` (C++ default 0.5), with the tip wrapped 40°. The M4 and pump triggers are further away, so the finger stays straight and the contact slides out along it. No press.
  - **If it's reported broken:** tune Contact Along / Tip Wrap on the nodes, or move a gun's `TriggerFinger` socket. Re-check offline with `Tools/AnimAuthoring/TriggerFinger/check_solve_bl.py` (its defaults match the game). Spec: *Trigger finger* → *Tracking the trigger*, step 7.
- **Shots past the character (2026-11-12): built 02:21.** Accepted (user, 2026-11-12: "make all tests ok"). If it breaks: a doorway shot (camera past the open leaf) should hit what the crosshair shows past him, not the leaf, and a wall about 1 m away should take the shot on the dot. Spec: *Trace source — two-stage*.
- **Enemy draw sound (2026-11-12): built 01:00.** Enemies skip the draw (`AEnemyBase::ShouldSkipEquipAnimation`). Accepted (user, 2026-11-12: "make all tests ok"). There's no draw delay now; raise `ReactionTimeMin/Max` if woken enemies fire too fast. Spec: *Encounter reserves* → *No draw on waking*.
- **Test starts (2026-11-11): built 20:22, working** (user: "thats good now"). In `Lvl_01_Slum`, a Player Start per section with **Player Start Tag** `S1`…`S7` (and the section in Actor Tags); the existing start stays untagged. Then `StartAt S3` in the console while playing (`StartAt off` to go back), or `Bopis.StartAt S3` before Play. Spec: *Test starts*. `AimMinReach` 150 on `ABP_Player`. Spec: *One-handed pistol* → *The aim point*.
- **Shoulder swap (2026-11-10):** works (V, D-pad Down). Spec: *Camera*.
- **Arm twist and Gun Upright (2026-11-11):** new `FAnimNode_UpperArmTwist` (+ editor node), built 13:45; Upper Arm Twist on both arms and Forearm Twist on the right placed after the head look (bridge, saved). User: "still an issue", so `FAnimNode_GunUpright` (+ editor node), built 14:07, angle fixed (it would have flipped an upright gun) and rebuilt 15:13; placed after the recoil, before `hand_r` → `ik_hand_gun`, Alpha ← `GunUprightAlpha` (bridge, saved). Tested (user, M4 firing): "looks good". Not covered: the duals' left gun. Spec: *Upper Arm Twist, and the right arm*, *Gun Upright*.
- **Duals' left trigger finger (2026-11-11):** built 01:48, the mirrored layer wired and saved (bridge). Superseded 2026-11-12: there's no press any more, and the left finger tracks its own gun's trigger (`TriggerFinger_1`). Accepted with the rest. Spec: *Trigger finger* → *Duals' left hand*.
- **AK left hand (2026-11-11):** user: "ak left hand is ok now". My proposal (socket rotation (58.45, 64.54, 80.91), lock on) wasn't applied; it stays in the spec (*AK-74u*) if wanted later.
- **Pickups at the hand's size (2026-11-11):** built 01:41 (pickups and drops copy the weapon mesh's scale; the drop→pickup swap spawns at unit scale). The user checks a placed pickup and an enemy's dropped gun (M4, .45, machine pistol) against the same gun in hand. Spec: *Gun scale vs the .45*.
- **Gun scale (2026-11-11):** M4 1.33 (offset (1.64, 1.47, −2.42)), the .45 1.1 (user's, offset unchanged), the dual machine pistol matched to the single (user's); user: "it looks ok without any adjustments". The trigger-finger poses were solved for a smaller M4: at 1.33 an L finger can't reach the trigger. Parked 2026-11-11, then resolved 2026-11-12 by the Trigger Finger node, which tracks each gun's own trigger; `Tools/AnimAuthoring/TriggerFinger/` now places the gun at its component scale. Spec: *Gun scale vs the .45*, *Trigger finger*.
- **Trigger finger (2026-11-10):** C++ built 23:10, the AnimGraph layer wired, the two poses made in Blender (`Tools/AnimAuthoring/TriggerFinger/`) and set under PistolGrip; all saved. Superseded 2026-11-12: the press is gone and the Trigger Finger node tracks the trigger. Spec: *Trigger finger*.
- **Forearm Twist (2026-11-10):** built 22:33; placed in `ABP_Player` through the bridge (user: "can you do that via bridge?") after `CopyBone_5` (Lower Arm `lowerarm_l`, Hand `hand_l`, Twist Bones `lowerarm_twist_01_l`/`_02_l`, Alpha ← `LeftHandIKAlpha`), compiled, saved 22:41. Tested (user): "looks good". Spec: *Forearm Twist*.
- **Trigger finger** (user: "can you help me curl the finger into a trigger press possition?"; picked "on trigger + squeeze" and "you pose it", then "apply and build"): `FTriggerFingerPoses` by grip style, `TriggerFingerAlpha` (gun up), `TriggerPressAlpha` (0.08 s after each shot), `AWeaponBase::GetTimeSinceLastShot`. Applied by Claude; built clean 23:10 (no busy peers); DLL 23:10:11 newer than the source; one editor; bridge answers. AnimGraph through the bridge: `LayeredBoneBlend_18` (index_01_r) after the grip layer, a Two-Way Blend of two Sequence Evaluators; compiled, links read back, saved. The user's hand-keyed poses came back wrong on reopening (bones rotated but not keyed are dropped; one key in World space); on "can you do it via blender yourslef?" the poses were solved in Blender onto the AR4's trigger blade and imported (other bones match the clip, worst 0.0004), the user's two deleted ("feel free to delete the ones I added"), and the pair set in `ABP_Player` (bridge, saved 23:44).
  - **2026-11-11, reshaped** (user, from a pistol in Play: "the finger doesnt go like an L shape, its more like a C shape"; "L or J shape"): the last joint now follows the middle at 0.15 instead of 0.65 (Rest: middle 76°, last 11.4°; Press 83.5° / 12.5°), pad within 3 mm. Old pair unset and deleted through the bridge, the new one imported headless under the same names (other bones match, worst 0.0004), set again, compiled, saved 00:22. Not seen in Play.
  - **Deeper** (user: "push _2 further into the trigger", then, stopping my middle-joint edit, "i need the tip further into the trigger"): the pad now aims 0.6 cm past the blade's line and at its front, so the end of the finger crosses the trigger (Rest: knuckle −10°/−9.5° tilt, middle 81°, last 12°; Press 86.5° / 13°). Swapped in the same way, saved. Not seen in Play.
- **Sensitivity settings (2026-11-09):** plan *Main menu*. Steps 1 and 2 built (13:27, 13:58). The user re-checks both menus (button code moved into `UMenuItemWidget`). Step 3: `WBP_SettingSlider` and `WBP_OptionsPage` made (bridge); the user pastes their trees (`Tools/MakeMenuTrees.ps1 -Clipboard SettingSlider`, then `OptionsPage`), adds a `WBP_OptionsPage` named `OptionsPage` to both menus' `Pages`, sets both Options buttons to OpenPage `OptionsPage`, then tests with mouse and pad. Spec: *Player settings*.
- **Metal smoke (2026-11-09):** the user scales `MetalSmoke` (and `WoodSmoke`, `GlassSmoke`) in the editor, as concrete. Spec: *Eighth Deck trace*.
- **Arena restart (2026-11-07):** built and on; the user clears `Lvl_BackAlleys_Arena`'s 20 in Play: the kill cam, 1 s, a 1.5 s fade, the reload. Commit `EncounterDirector` with the Main Menu session's `LevelTravelSubsystem`. Spec: *Level exit*.
- **Enemies stuck on physical props (2026-11-07):** plan item 49. The user chose the push ("do the push, but make sure the objects dont fly", enemies "almost not affected in terms of speed"). **C++ presented in chat, not applied or compiled:** `AEnemyBase` turns `bEnablePhysicsInteraction` back on (corpses, casings and drops all ignore pawns now, so only props get pushed), `RepulsionForce` 0, mass-scaled push applied low on the prop (`PushForcePointZOffsetFactor` -0.75), first touch at the enemy's own walk speed (`PropPushSpeedScale` 1, set each tick in `UpdateMovementMode`), then `PropPushAcceleration` 2000 cm/s² while touching. Waiting on "apply and build" or the user typing it.
- **Inspects (2026-11-08):** spec *Inspects*, plan item 50's inspect steps. User: voice plus subtitles (subtitles a setting), a silent count for achievements only, Navarro moves for them, and each one is a mini cutscene (a Level Sequence; a close-up is a shot in it).
  - **Step 1 built** (compiled clean 16:52): the Interact button, the prompt and a bare `InspectPoint`. **The user's part:** map `IA_Interact` in `IMC_Default` (E, gamepad bottom face button), make `WBP_InteractPrompt` in `WBP_PlayerHUD`, place an `InspectPoint` and test it (prompt shows near and facing it; press logs "inspected"; a shot hides the prompt for 5 s).
  - **Step 2a built** (compiled 18:28): the press cuts into the inspect's Level Sequence with the player as Navarro; Interact skips. **The user tests** with `LS_InspectTest` on `InspectPoint_1` in `Lvl_01_Slum` (set, map unsaved): two shots and a crouch, then control back. Watch for a one-frame glimpse of him on the mark before the first shot. For a blend back, tick the camera cut track's Can Blend and ease out its last section.
  - **Parked (2026-11-08, user: "park the cutscene bit for now"):** 2a and the pre-built double are tested and good (he has his hair); the glance isn't confirmed. When it resumes, next is step 2b, voice and subtitles cued from the sequence, and the subtitle setting. Animations for crouch, reach and pick-up don't exist yet; the user's call where they come from.
- **Linear slum level (2026-11-07):** paper layout done (`Design Document/Linear_Slums_Layout.html`, plan item 50). Edit `Tools/LevelGen/layout_linear_slums.mjs`, not the outputs.
  - **Revised 2026-11-08: no drops.** Every border is a door (or a bend), both ways; streaming loads either way. The three changes (yard door + landing + steps, H4's half-landing stair, the passage steps) **are not in `Lvl_01_Slum`**: it still has the wall drop, H4's floor hole and the passage drop. Into the map only by hand or on the user's say.
  - **The user's calls** (the layout's *Open* list): the patrolman's body, how Navarro arrives and what he carries, clue contents, lines at inspects, civilians, who the gunmen are, "drives off". (Level name settled 2026-11-08: `Lvl_01_Slum`.)
  - **Built (2026-11-08):** the generator split (arena identical) and `Lvl_01_Slum` with its 14 sublevels, headless. Regenerate with `python Tools/LevelGen/gen_level.py linear_slums`; rebuild with `build_story_ue.py` (REBUILD deletes only this level's maps, and only while the editor hasn't loaded them).
  - **Next (2026-11-09):** the user handcrafts parts of `Lvl_01_Slum`, starting from the generated blockout (compound walls, kit stairs, 3.5 m storeys, plain compound houses). **Don't rebuild or re-place it from the generator** (`build_story_ue.py` would wipe the handwork): generated additions go into new sublevels unless the user says otherwise. Still unnamed: the spots that were blocked on the first walk; tune the night and bake; then inspects, section streaming and checkpoints. The dressing passes are off for this level until each is checked for arena-only assumptions.
  - **Sections 1-2 (2026-11-09):** dressed, unaligned fronts, concrete street, sidewalk with a main-border-stone curb; swapped into the map with `swap_sections_ue.py` (never `build_story_ue.py`). **`Lvl_01_Slum` is one map now**, sections as actor tags `S1`-`S7`: new pieces go in through the bridge, tagged. The old sublevel files (`Content/ThirdPerson/01_Slum/`) are a pre-merge copy for the user to delete when happy. Open: the street lights' night values (arena's 4.5 / 6 / 40 cd, unjudged), the ground pass (dirt, litter, props) for sections 1-2, and the user's walk of the new street. **Even light (2026-11-09):** 8 lamps and 3 tubes from `story_light_fill` (33 pieces) placed and saved; the user judges the street at night. **Section 4 baseline (2026-11-09):** in the generator (one-leaf doors in jambs, framed windows, the user's steep stair; `FITTED`), checks clean, swapped into the map and saved. The knocked-through walls' rubble and broken edges are placed (white); the jamb collision is fixed: the user walks and shoots through a single doorway to confirm. **Swinging doors (2026-11-09):** `ASwingDoor` compiled, `BP_SwingDoor` and the 6 row-house doors placed and saved, 14 variants (one per door type) in `Blueprints/SwingDoors/`. Handles on the free edge for every variant (`LeafQuarterTurns`, compiled). Door sounds: stand-ins (user: "actually use the stand ins"), cues `SC_Door_Push` / `SC_Door_Shut_Wood` / `SC_Door_Shut_Metal` in `/Game/Audio/Doors/`, set on `BP_SwingDoor` and all 14 variants, read back and saved (the 6 placed doors still had none, user: "no sounds on the door"; set on them in the open map, not saved by Claude because the map had other unsaved changes: the user saves it); a CC0 door pack (OpenGameArt, rubberduck's 100 metal and wood SFX) can replace their waves later. Open: the user walks and shoots through the doors in PIE and listens to the stand-ins. **Row-house windows from inside (2026-11-09; user: "when i shoot the window, i hear wood", "its when im shooting from inside the building"):** Favela's window frame collided on its invisible glass panes (as Wood) and the jalousie planes can't take a shot from inside; the frame now collides as 8 boxes round its wood (asset saved), and the 9 S4 windows got a hidden Glass block between their two jalousies (`_WinGlass`, traced from both sides). In `story_interiors` too, not run (the layout JSON changed). Map saved (user: "Save it"); the 9 blocks read back BlockAll / Glass. **Light bake (2026-11-09; user: "my character is all black and S4 on did not bake the lights", "the lights are static, should they not be stationary?", "The orange light does not illuminate my character"):** the first GPU Lightmass bake (09:47) ran out of video memory and crashed the editor (RAM full too); two editors then reopened at once and each baked (54 and 44 min). The finished bake did give S4-S7 lightmaps, but `Volumetric lightmap NumTotalBricks = 0` (no baked light for anything that moves: the static orange lamps can't reach the player; only the Stationary moon, 0.35 lux, lights him) and `Skipping skylight with empty cubemap` (the sky light, `SkyLight_Night`, Stationary, had Real Time Capture on, which never bakes). S4-S7 have no lamps, so with no sky they stayed dark. Checked: the importance volume covers S1-S7, World Settings use volumetric lightmaps (200 cm), GPU Lightmass Full Bake, RTX 3080 Ti. Sky light Real Time Capture turned off (not saved: the map had other unsaved changes). Recommendation: lamps stay Static (Stationary local lights are live every frame and at most 4 may overlap; the fills double every fitting), moon and sky Stationary. Test bake at 12:09, after the sky light change: `NumTotalBricks = 403` (31.5 MB of bricks) and no skipped sky light, so both now bake. The empty volumetric lightmap came with the real-time-capture sky light (or the material recompiles at that bake's start); not proven which. That bake crashed the editor at 12:21 the same way as at 09:47 (out of video memory: the GPU's shared system budget full, 15.5 of 15.5 GB, and RAM 32 GB used with 0.3 GB free; the editor alone 19.3 GB, peak 25.6). The crash reporter again opened two editors. A retry at 12:29 hung the GPU at 12:39 (video memory 11.0 of 10.6 GB) and its volumetric lightmap was empty again. In every bake with 0 bricks (09:54, 10:58, 12:29) the log has "ray tracing scene is invalidated due to material changes" just before the volumetric lightmap step; the one bake with bricks (12:09, a second bake in that editor) doesn't. Each session `MI_BackAlleys_HollowBlocks_World` needed its base `M_BackAlleys_HollowBlocksWorld` set to "used with static lighting" as the bake began, never saved. Done (user: "Do both"): that flag set and saved headless (editor closed), and GPU Lightmass's Lightmap Tile Pool Size 55 -> 30 (map saved). A third bake (12:47, tile pool 30) crashed in the NVIDIA driver (access violation in `nvwgf2umx`) and again had 0 bricks. Measured: the generator's 1,734 `SM_Cube` boxes carry the mesh's 512 lightmap each, 74% of the map's 613 M lightmap texels; sizing them by area at 12 texels/m (16-256) would cut them 93%. The baked lighting was cleared before the user's push (user: "clear the Slum1 Lightmaps so It does not get commited"): `Lvl_01_Slum_BuiltData` (2.1 GB) deleted through the editor and the map saved without it. **Lightmap sizing, tried and reverted (2026-11-09 afternoon).** Boxes sized by area (12 texels/m, 16-256: 618 M -> 143 M texels) still crashed the bake: "Out of video memory" with the card's own memory fine (7.8 of 11.3 GB) and the GPU's shared system memory full (15.5 of 15.5 GB). Beams, roof sheets and wall tiles sized too (65 M): that bake finished (6:20 min, 403 bricks; start, cancel, start). It showed sections 4-7 unlit: the interiors' 65 bulb lights sit inside their `SM_Light_A_002` fittings, which cast shadows and blocked them whole (the street and fill passes' bulbs were already shadowless). With the fittings fixed, walls of the row house came out black with blocky patches (`ROW_F0_X66p00_66p00_Part_2`, `ROW_F0_X66p00_60p00_Part_0`: every one found faces +X), and walls built of several boxes showed bands where neighbouring pieces had different lightmap sizes. Ruled out: geometry over the face (none within 30 cm), the streaming pool (`r.Streaming.PoolSize 4000`, still black), the cube's normals, tangents and lightmap UVs (six equal charts, packed for 64). `SM_Cube`, `SM_Ramp`, `SM_Cylinder` have Nanite on while the project has it off (they draw their fallback); not shown to matter. `CaptureViewport` reuses the user's viewport occlusion, so anything hidden from the user's camera is culled in the capture: its "see-through walls" were not real. Cause of the black walls not found. User: "im reverting to the last commit. I think lowering the lightmap resolution messed up everything": the whole tree reset to `257fef50d` (lightmaps back to the meshes' own, the generator's sizing and the day's doc notes gone). Then (user: "Yes, after the revert") the bulb fix alone, on the reverted map: the 66 lit bulb fittings Cast Shadow off and volumetric, read back, saved 18:29, no baked data; in `story_interiors` (and the unused `story_lights`) a lit bulb is `noshadow` + `vol`. **Sky light Static (user: "can we globally reduce the lighmap size?", then "Yes, set it Static"):** Unreal has no setting that scales every lightmap (Static Lighting Level Scale changes sampling, not texels), and the full-size bakes that finished had all skipped the sky, so the first test is the sky: a Stationary sky light makes the bake keep sky occlusion for every texel (the `SkyOcclusion` textures), a Static one doesn't. `SkyLight_Night` Stationary -> Static (captured scene, 0.6, no real-time capture: unchanged), saved; the moon stays Stationary. The sky still bakes into walls and reaches characters through the volumetric lightmap; lost: its live reflection occlusion and changing it at run time. The full-size bake with the Static sky still ran out of memory (editor crash 18:58). **Then (user: "roll the sky back and half the resolution"), headless with the editor closed:** `SkyLight_Night` back to Stationary, and every lit static mesh's lightmap halved, one factor for all (its override, else the mesh's own, / 2; volumetric and movable pieces untouched): 8,653 pieces, 512 -> 256 (1,946, the boxes), 256 -> 128 (674), 128 -> 64 (3,137), 64 -> 32 (2,896); 617.6 M -> 154.4 M texels. Every one read back, map check clean, saved 19:01. The generator doesn't halve: a piece placed from a plan comes in at its mesh's own size. The bake at 154 M crashed too (user: "it crashed", "use a quarter"). **Quarter (19:29):** every lit piece at a quarter of its own lightmap (half of the halved: 256 -> 128 for the 1,946 boxes, 128 -> 64, 64 -> 32, 32 -> 16; 8,653 pieces), 154.4 M -> 38.6 M texels, set through the bridge in the user's open editor (a headless save failed: the editor had the map open and the file locked), 352 read back, saved. Sky light Stationary. The quarter bake finished (user saved it 19:36, `Lvl_01_Slum_BuiltData` 298 MB). **33% (user: "set it to 33%", then "do it"):** every lit piece at 33% of its own lightmap, rounded to a multiple of 4: 512 -> 168 (1,946 boxes), 256 -> 84 (674), 128 -> 44 (3,137), 64 -> 20 (2,896); 66.9 M texels (65 M baked fine earlier). Set through the bridge, 352 read back, map saved; the 19:36 baked data no longer matches the pieces. **Unseen geometry removed (20:16; user: "RULE: If you cant see it in gameplay, remove it from the level ... Any geometry that will not be visible, just remove it completely"; "None of them are to be entered"):** rule added to `Claude-Rules.md` §8. A line-of-sight test (`Tools/LevelGen/analysis/cull_unseen_ue.py`, read-only, in a windowless full editor: a commandlet world has no physics): the walkable area is the nav mesh joined by paths to 60 seeds from the layout's rooms and streets (505 points on a 2.5 m grid, every room and street covered); the camera at the pivot and at arm length for 4 yaws, level and 70 degrees down (up to ~4.5 m), 4,545 positions; 160 rays from each, then lines to points 4 cm off every face for whatever no ray hit. Windows, doors, hidden blockers and movables don't occlude; hidden-on-purpose pieces are never removed; unseen pawn blockers within 50 cm of the walkable area kept (3). 1,725 of 9,706 static meshes unseen: 374 roof sheets, ~750 back-wall tiles, trims and bands of the closed houses, 81 house-ground slabs, 75 lids, 52 cores, 37 floors, posts, beams, boards; also door steps sunk under the raised sidewalk, water meters on back walls. Map backed up (`Saved/Backups/Lvl_01_Slum_before_cull_20261109_2015.umap`), the 1,725 removed through the bridge (names sampled against labels), saved: 8,395 actors, 16.1 MB (was 19.2); measured after, 7,011 lit pieces and 55.8 M lightmap texels (66.9 M before the cut, 617.6 M at the commit). The user's open editor had unsaved changes before the removal; they went into the same save. The other 72 cores were seen (45 are the dark room behind windows, doors and grilles; 27 through gaps such as eave cavities) and stay (user: "Keep them as they are"); together about 2 M texels. **Volumetric lightmap only (user: "Is there a way we can get away from lightmaps without dropping performance too much", then "try 1. Using the original settings for baking. Keep the work for removing non-visible meshes"):** all 7,011 lit static pieces `LightmapType` ForceVolumetric and their lightmap-size overrides cleared (back to the meshes' own, for a return to lightmaps); 285 read back, saved. Bake settings unchanged (volumetric lightmap detail cell 200 cm, GPU Lightmass as before); the removed pieces stay removed. Nothing in the level has a surface lightmap now: everything takes the volumetric lightmap, so the bake has no lightmap texels at all. The volumetric-only bake ran (GPU Lightmass, 385 bricks, 5 s) and had no visible shadows (user: "no baked shadow"): a 2 m grid can't hold them. **Back to surface lightmaps at full size for a CPU Lightmass bake (user: "let me try the CPU lightmass", "Full size"):** the same 7,011 pieces `LightmapType` Default, no overrides (each at its mesh's own size: 515.6 M texels; the culled pieces stay gone, the 66 bulb fittings stay volumetric), 285 read back, saved. CPU Lightmass runs in its own process on CPU and RAM, so the GPU-shared-memory crash can't happen; expect hours at Production. **CPU Lightmass from now on (user: "ill use cpu lighmass from now on"):** spec updated; the GPU Lightmass workarounds (tile pool, start-cancel-start) no longer apply. Open: the user's CPU bake (Build > Lighting Quality, Build Lighting Only; a Swarm Agent window should appear); optional: turn off hardware ray tracing support and the GPU Lightmass plugin, which were on only for GPU Lightmass (fewer shaders, less editor memory). Open: the user's walk of every section for holes (restore from the backup if any); the bake (~54 M texels); whether walls show black +X faces or bands; the generator still makes these pieces (rerun the test after any regeneration); update the NVIDIA driver (621.01; one crash was inside it). **Drops to doors (2026-11-08, on hold):** the revised layout's three drop replacements (the 2→3 yard wall door, landing and steps; H4's inside stair; the 5→6 passage steps and doorless doorway), relayed by the "Linear Level Design: Slums" session as approved for the bridge, then held by the user: "leave it for now". **H4's stair done (2026-11-11; user: "the drop will now be stairs down. Work on it now"):** the floor hole replaced by the layout's half-landing stair, fitted to the 3.5 m storey: a solid landing block at +1.75 against the back and party walls (`ROW_Landing2` + finish plane, Y -192..8), the lower flight (`ROW_Stair2`, X -848..-675) down to the back door, the upper flight (`ROW_Stair3`, X -1020..-852, clear of the window frame) from the upper floor at Y 250; kit flights as the user's stair (FITTED/TRAP_Stair3), balusters and pipes on the open sides, AsiaSlum bar rails on the landing's room edge and round the new opening (X -1029..-675, Y -192..250) but where the stair arrives; 1 cm slab edges on its cut faces. Removed `ROW_Slab1_6`, the 4 old slab edges and floor planes `ROW_H4_UB_Floor1`/`3`; `ROW_Slab1_4` shortened to Y -192. 25 pieces, tagged S4, copied from the existing stair's materials and collision (`Tools/LevelGen/analysis/h4_back_stair.py` computes them). Traced: flights and landing where planned, headroom open to the roof; the saved nav mesh paths bedroom -> landing -> back room. The upper flight hides only the top corner of the back room's window nearest the landing. Map backed up (`Saved/Backups/Lvl_01_Slum_before_h4stair_20261111_2159.umap`) and saved 22:01. Open: the user's walk down it; the other two (yard door, passage steps) still on hold.
- **Slum layout, the way back (2026-11-12):** in the paper layout (`Design Document/Linear_Slums_Layout.html`), not in the map. To build when the user says: F13-F17 and CP9-CP13 as rough guides, I9 at the yard gate (the level exit moves there from I8), and encounter triggers armed by I8. It needs section memory (dead, doors, pickups) before it plays right. Open for the user and design partner: where the patrolman's body lies in the yard and when it's found, who comes on the way back, what happens with the cops. About 20-35 min against the 30-45 target: more loops (the new §8 rule) are the lever if it needs more.
- **Level renamed (2026-11-07):** other sessions' own scratch scripts may still name `/Game/ThirdPerson/Lvl_BackAlleys`; the shared `Tools/LevelGen` scripts are updated. The next Deck build cooks the new name.
- **Main menu (2026-11-07):** hub `Lvl_MainMenu` (empty, not World Partition), scene 1 `Lvl_MenuScene_BackAlley` (a copy of `Lvl_BackAlleys_Arena`, 18 gameplay actors removed) and `BP_MainMenuCamera` (CineCameraActor) are made and saved. Scenes load as Level Instances (user's pick). The user placed the camera in the scene map (saved 19:42, after the 19:34 editor restart, so the pre-strip copy wasn't in memory) and won't cut the scene down yet ("I wont cut it down yet"), so its bake waits too. A first attempt (a headless rename) lost the actor files; cleaned up, gotcha in the spec. The menu game mode and controller are built, their Blueprints made, the hub's GameMode Override set, and PIE works: the back alley loads into the hub and the view cuts to the user's camera (after a camera-search fix for World Partition scenes, applied on "apply and rebuild"). The user's call: the black bars beside the shot (CineCamera's Constrain Aspect Ratio). The reusable menu C++ (`UMenuWidget`, `UMenuButtonWidget`) is built (applied on "apply and rebuild"). `WBP_MenuButton` and `WBP_MainMenu` are made and hooked to the controller; the user pasted their trees and PIE shows the menu over the scene (Options greyed), no log warnings. The user's tweaks are built (2026-11-07, "apply and rebuild"): a prominent highlight that follows focus and the mouse, the menu only after the scene's fade and fading in, and `ULevelTravelSubsystem` fading to black before every level load (menu buttons, death restart). Tested in PIE 2026-11-07 (user: "Tested, all works"). The game now starts on `Lvl_MainMenu` (`GameDefaultMap`; the editor still opens the arena), both menu maps are in `MapsToCook`, and a Deck build is made (2026-11-07, BUILD SUCCESSFUL, 0 errors). The user ran it on the Deck (user: "Works on the Deck"). Main menu left: the scene's bake (once it is cut down). **Pause menu (2026-11-07):** C++ built (`UPauseMenuWidget`, `RestartLevel` action, `PauseAction` on the gameplay controller); Slate's focus ring replaced by a `FocusFrame` in `WBP_MenuButton` (`RenderFocusRule=Never`); `IA_Pause`, `WBP_PauseMenu` and the controller's settings made. The user: add `FocusFrame` to `WBP_MenuButton`, map `IA_Pause` to Escape and Gamepad Start in `IMC_Default`, paste the `WBP_PauseMenu` tree, then test. The arena's self-restart on clear stays for now (user, 2026-11-07: "The arena reset stays for now"). Done by the user since: `FocusFrame` added (frame seen in PIE on the hub), the pause tree pasted, `IA_Pause` on Gamepad Start; **Escape still to map**. Since: P closes it too (`ToggleAction`), the backdrop is a blur; tested 2026-11-07 (user: "Works"). Main menu left: the user bakes `Lvl_MenuScene_BackAlley` whole, no cut-down (2026-11-07: "I'll bake the lights, but wont cut the level"); bake with the scene map open, then check from the hub in PIE that the baked lighting shows through the level instance. Also: run the pause menu, `FocusFrame` and blur on the Deck with the next Deck build. Plan: *Main menu*.
- **Business signs and gates (2026-11-07):** placed and saved. The user's calls: the wall boards' import (UserInterface2D, 1850 × 500, no mipmaps, so they'll shimmer far off); more boards for the 5 blank signs, if wanted. The lettered signs are 150-191 cm wide, bounded by the shop fronts they sit over.
- **Physical props, bags and pots (2026-11-07):** 97 physical pieces placed and saved, settings read back. Still to do:
  - The mass-scaled push in `AProjectBopisCharacter`'s constructor is built (2026-11-07). The user types and compiles the bullet-push C++.
  - Reload the level before testing in PIE: collision presets only take after a reload (LESSONS).
  - In PIE, walk into a chair, then shoot a chair, a bag, a pot and the lidded bucket `Prop_Bucket_0_0`. Check that lids and plants ride along.
  - Trace the 97 sleeping bodies on the Deck, plus the dynamic shadows of 48 movable pots and 37 plants.
  - Calls for the user: bag and pot masses and surfaces; 18 bags where there were 25; 48 pots where there were 60.
- **Paper off posters (2026-11-06):** built clean, 300 posters on the `PosterPaper` preset, saved; the wall keeps its burst, sound and hole. The user shoots a poster to judge it. The sheets were too big ("I want bits of the poster"), so `PaperBurst` on `DA_ImpactEffects` is now `NS_ImpactPosterBits`, with the user's values; not seen in play. `NS_ImpactPaper` stays for stacks of paper. The 8 sheets on two shutters, which sat hidden behind the metal and threw paper, now sit in front of it (`B3_W0_0_1`, `B24h1_E0_0_0`); they use volumetric lighting, because their old lightmaps came out in black patches.
- **Collision and surfaces (2026-11-06):** `nocoll` really removes collision now, on 2,209 pieces including the wires; the 112 awning pieces stay solid by the user's choice. 45 material instances now report the right surface, the ground (Asphalt) among them. Verified by reload, traces and reading back from disk. Not played yet: the user checks hits and footsteps by ear, and that enemies still path. Offered, not done: the same override fix on the 374 pack instances this level doesn't use. `SM_HouseDoor_A_002` (6 doors) has an empty second slot on `WorldGridMaterial`: worth a look. Spec: *Impact effects*.
- **Focus bullet speed (2026-11-06):** built; the user judges it in play. Spec: *Focus (slow motion)*.
- **Music voice fix (2026-11-06):** the user sprays the Machine Pistol to confirm the music holds. Offered, not done: tick Looping on `DarkCrimes` (it ends at 4:50), and a limit of 8 on `M4_Single_Shot_Cue` and `Shotgun_Boom_101_Cue`.
- **Lvl_BackAlleys_Arena Game ms, 2026-11-06:** shell-casing and magazine fixes compiled and traced on the Deck (trace 26 = `20261106_030058`, about 5 minutes): fights at 54-60 fps, world tick 13-14 ms (was 34-48), and 26 corpse trims with no rebuild. **Left:** a one-frame hitch of about 50 ms when the player picks up a gun (4 in the trace): `SetStaticMesh` in `FitMagazine` adds the magazine to the navmesh before the flag is set, and 4 tiles rebuild (about 35 ms). **Fix applied and compiled 2026-11-06, no Deck build yet, not tested on the Deck:** `Magazine->SetCanEverAffectNavigation(false)` moved above `SetStaticMesh`. Fallback if spikes remain: `RuntimeGeneration=DynamicModifiersOnly`, which needs a saved navmesh. Details: spec, *Shell casings and the navmesh*. Uncommitted: `ShellCasing.cpp`, `WeaponDrop.cpp`, `ProjectileBase.cpp`, `WeaponBase.cpp`.
- **Lvl_BackAlleys_Arena, ground pass placed (2026-11-06):** the surfaces are in, so **the rebake can go ahead now**. The user judges the concrete tones after it: unbaked planes read brighter and bluer in shade than the baked road. Tints can be changed live (LESSONS). In PIE: litter has no collision, so see whether walking through bags bothers anyone. Big tags stay on the upper storeys and the ground-floor posters stay (user: "Leave them up"). The user's call: drains (square grates are out, and the packs have nothing else).
- **Lvl_BackAlleys_Arena, 2026-11-06:** rebake: the closed stalls, the posters, the poles and the ground all went in after the 00:30 bake. Trace the Wires folder (1,828 actors), the poster planes, the 140 ground decals and the litter and props (304 pieces, 45 of them masked plants) on the Deck; merge them if they cost too much.
- **Lvl_BackAlleys_Arena, the user's call:** whether tables and benches should be solid. Tables stay wooden (user: "Keep wooden tables"). They stop shots, but pawns walk through, so nothing about the fights has changed.
- **Ads, the user's call:** texture settings (no mipmaps, 10 uncompressed, `Puting_Araw` set up as a normal map, so skipped); the election posters say 2004 and Tibay Selyas 2003 in a 2002 game; three movie posters are 1:2 and look tall; whether posters and wires may go on hollow-block walls; whether the ads stay at all.
- **Cleanup once the editor has closed:** `M_BackAlleys_Poster` is unused too, replaced by `M_BackAlleys_PosterPaper`. So are `M_BackAlleys_GraffitiDecal` and its 20 `MI_BackAlleys_Graffiti_*`, replaced by `M_BackAlleys_SprayDecal` and `MI_BackAlleys_Spray_*`.
**A. Next up**
000001. **Hair shine (2026-11-04):** the user judges the Default Lit hair in
    game, ideally after a rebake. Too dark or too light: adjust the material.
    Undo is in the spec.
000000. **`Lvl_BackAlleys_Arena`, open from 2026-11-04:**
    - **Street dressing:** placed; the user judges it after the rebake. Light brightness needs another
      look then (bulb 4.5, tube 6, lamp 40 cd). Signs are blank until the user gives wording. In PIE,
      check that shutters and gates (which keep collision) don't catch the player or enemies.
    - **First:** rebake the lighting (the building floors moved everything). The
      last bake ran out of video memory in GPU Lightmass; cause not found.
    - **Building dressing and laundry:** the user judges them after the rebake: unbaked
      planes read too dark in shade. 86 of 235 blank tiles stay bare; rates are `P_PATCH_*`
      and `P_VENT_*`. Laundry's LOD switch sizes couldn't be read, and its 35 m cull isn't
      watched in PIE yet.
    - **Cleanup once the editor has closed:** delete six unused first-draft assets, locked
      while it's open, and don't commit them: `MI_BackAlleys_Plywood_Natural`, `_Weathered`,
      `_GreenPaint` in `BackAlleys/Materials`, and `T_BackAlleys_Plywood_Natural_BC`,
      `_Weathered_BC`, `_GreenPaint_BC` in `BackAlleys/Textures`. Keep
      `T_BackAlleys_Plywood_N`: the new plywood uses it. Also unused now:
      `T_BackAlleys_Sign_N`.
    - Walk it in PIE: the 18 cm slabs and the new stairs, player and enemies.
    - `Wander_R2` is inside B20b's footprint; move it before wiring wander points.
    - The user shoots a hollow-block wall, a door and a jalousie window in PIE
      to confirm the sounds (concrete, wood or metal, glass). Not tested by ear.
    - Red-oxide sheets look bright orange (AssetGen's material; user's call).
    - A bright blue wall right of the gallery stairs: not identified.
    - B8b's east wall looked yellow in capture `20_joint_overlap_B8b`, though
      its saved material is the right concrete: not explained.
    - The corner column edges (2 cm proud) still show as lines: the user may
      want them flush.
    - *(Done 2026-11-07, user: "the proxy is probably broken again. Fix it".)* The proxy fix for the "connected, 0 tools" hang: `tools/list` answers from the snapshot at once.
    - `M_BackAlleys_Jalousie` is unused; delete only if the user says so.
    - **Linear levels, deferred (user: "not yet"):** the builders can serve them
      once `gen_level.py` is split into a shared building library and per-level data.
      Tied to this arena: the single `arena` rectangle and its edge logic, hard-coded
      `B2`/`B10`/`B11`, one deck with fixed rail sides, stairs, and arena-only gameplay
      data. Walls only face N/S/E/W, and houses are shells with no interiors. The split
      must still generate the identical `Lvl_BackAlleys_Arena` plan. Don't start unasked.
0000000. **`Lvl_BackAlleys_Arena` kisame roofs (2026-11-03):** rebuilt (3,876 placed,
    0 failures, traces as before) and captured against the shanty photo.
    The flashing fix, one-board weatherboards, sealed sloping sides and the
    25% hollow-block wall mix are applied too. Left: the user's call on
    toning down red-oxide.
00000. **Back-alley arena (`Lvl_BackAlleys_Arena`, 2026-11-02).** The Sandbox copy is
    made. Next:
    1. *(Done 2026-11-02.)* Packs added (`Philippines_Markets`, `Megapack`,
       `AsiaSlum`) and analysed. Spec: *Environment art packs*. Use:
       - AsiaSlum for structure;
       - Philippines_Markets and Megapack Favela for dressing;
       - not MiddleEast's buildings, and not the Japanese-signage Yakohama
         pieces (MiddleEast's generic street props are fine).
    2. *(Done 2026-11-02.)* Layout: `Arena_Slums_Layout.html` ("yep 1 and
       2"). Prep pass applied to all three packs and read back. Kit list in
       the spec.
    3. *(Done 2026-11-02.)* The user's calls: stand-ins for the jeepney and
       tricycle, opaque glass, "go build". First build and dressing pass
       done (spec *`Lvl_BackAlleys_Arena`: first build*).
    4. **Next:**
       - **All-alleys layout built** (2026-11-02, `gen_level3.py` from
         `Arena_Slums_Layout.json`).
       - **Arena sweep connected (2026-11-04):** code built clean 14:20;
         `ST_Gunman` compiled with the `StateTreeCompileAll` commandlet and
         read back. **Not yet tested in PIE.** Check:
         - lose them, and they go to the last known spot, wait, then
           sweep spawn point to spawn point, gun up, at 450;
         - they turn along their path;
         - gunfire pulls them to the sound.
         Tune `SweepSpeed` and `LeadGoneAfter` on the enemy BP.
       - The 3 wander points are placed but not swept (they aren't spawn
         points). Keep, add to the sweep, or delete: the user's call.
       - The user walks it in PIE: nav mesh, spawns from the 8 doors, the
         gallery stairs (39°).
       - **The court is gone** (user: long sight lines are wrong for an
         arena). `SM_BackAlleys_HalfCourt` and the BasketballCourt pack
         are unused; keep or delete them, the user's call.
       - **Grenade launcher removed** from the pickups (user's call).
       - **Editor keeps reopening (user, end of day 2026-11-02).** Not
         solved yet. Found so far:
         - Every editor session today exited cleanly (`LogExit: Exiting.`),
           and each relaunch came 10–20 min later, so it isn't a crash
           auto-restart.
         - The open instance (started 21:35) has `explorer.exe` as its
           parent. That means a shortcut, a double-click or the shell.
           `RebuildEditor.ps1` uses `Start-Process`, which would give
           PowerShell as the parent, and the MCP proxy never launches the
           editor.
         - 5 crash folders today in `Saved/Crashes` (09:32, 09:33, 12:44,
           17:19, 17:22). The crash reporter's "Send and Restart" reopens
           the editor.
         - Next: ask what the user sees, whether it opens after closing
           it or at sign-in. Check the Windows setting "restart apps at
           sign-in", the Startup folder and Task Scheduler, and whether
           peer sessions run the rebuild script.
       - **Still open, the user's calls:**
         - *(Decided: "20 kills": `TotalEnemies` 20, `MaxAlive` 4.)* What
           happens on the clear: an exit, a message or the menu? That needs
           an "arena cleared" hook.
         - Keep the prep and level scripts (scratchpad: `prep_ue.py`,
           `texcap_ue.py`, `gen_level3.py`, `halfcourt_ue.py`) in `Tools/`?
           Backed up to `Saved/BackAlleys/scripts/`, since the scratchpad
           only lasts the session. `Saved/` isn't committed.
       - Lighting and mood: it's flat daytime now.
    5. **Performance:**
       - **Triangles first (asset thread, 2026-11-03):** `SM_MainBorder_04`
         is 73% of the level's LOD0 triangles. A low-poly trim and a
         low-poly `SM_Slate_01` of our own are proposed and wait for the
         user's OK. The level-generation thread switches `gen_level.py` to
         read sizes from `Tools/AssetGen/manifest/index.json`.
       - Merge each block (`merge_actors`) or pack each into a Packed Level
         Actor. The all-alleys build is about 890 actors, well over a
         thousand draws.
       - Bake with GPU Lightmass and check Map Check for lightmap-UV
         warnings.
       - Add it to `MapsToCook` and measure on the Deck.
0000. **Deck performance: PAUSED 2026-11-02** (user: "I think we pause the
    optimization for now").
    - **Where it stands:** trace 23 (`20261102_132154`, Sandbox, High
      100%): busiest 20% of seconds 53 fps, 83% of seconds at 58+ fps.
      Fights are game-thread-bound (busy `UWorld_Tick` 13.6 ms). Deck code
      in `UBopisGameInstance::OnStart` → `ApplyDeckOverrides`: High,
      `DeckResolutionScale` 100, half-res translucency, URO on. Spec:
      *Game-thread targets*.
    - **Uncommitted:** `EnemyBase`, `BopisGameInstance`,
      `BopisCharacterBase`, the HUD widgets, `EFT_Impacts`, the docs.
    - **If resumed, cheapest first** (estimates: spec *Enemy animation
      options*):
      - `AnimRateScreenSizes` 0.5/0.25 → 0.7/0.35 on `BP_EnemyBase` (no
        code; ≈0.6–0.8 ms frame);
      - LOD Threshold 1 on Leg IK / Stride Warping / Orientation Warping in
        `ABP_Player` (editor; ≈0.3–0.5 ms);
      - Animation Budget Allocator, Deck only (C++; up to ≈1–1.3 ms in the
        heaviest fights);
      - head as a leader-pose follower (≈0.4–0.5 ms; morphs need another
        route);
      - `ConcreteSmoke` to GPU sim (editor click);
      - an A/B of `Slate.EnableGlobalInvalidation 1`;
      - CC mesh merge (big).
    - Trace store: two baselines kept, `20261102_122946` and
      `20261102_000532` (plus traces 22 and 23).
    - The older steps below are mostly done; they're kept for the muzzle
      flash and smoke PIE checks.
    1. **Muzzle flash: built (2026-11-01), PIE test it.** Check:
       - strafing fire leaves at most one puff per 0.35 s;
       - each shot gives a brief, shadowless flash;
       - duals light the hand that fired;
       - rapid fire never stacks lights.

       If smoke still shows every shot, see the spec's *Muzzle flash* risk
       note. Then the content side: smoke size and lifetime, the shotgun's
       embers.
    2. **Sun shadows: done 2026-11-01** (inset shadows off; casings and
       pickups shadowless). Left: the same change on `Lvl_Linear`'s sun when
       it's baked.
    3. **The user's command-line tests:** `r.TranslucencyLightingVolume 0`
       (or `.Dim 32` + `.MarkVoxels 1`), `r.ParticleLightQuality 0`,
       `r.ScreenPercentage 80`. Make the ones the user likes permanent for
       the Deck.
    4. **Decal cap, bloom, SSAO: done 2026-11-01** (cap 48, bloom 3, SSAO
       max quality 50). Check in the re-trace whether decals drop below
       ~1.7 ms.
    4b. **Impact effects (trace 7, user: "impact particles first"):** glass
       refraction, `EffectScale` 1.0 and the smoke interval done 2026-11-01.
       **PIE test the smoke:** empty an SMG into a wall; expect one puff on
       the first hit, then puffs spread through the burst. `EFT_Impacts`
       done too. Then re-trace; after it, shorter or unlit smoke if still
       needed. After that, CC characters.
    5. **Re-trace.** Start the editor *before* opening Insights, then close
       Insights right after the run (spec gotcha).
    - **Later:**
      - bake `Lvl_Linear` (check its floor for a lightmap override first);
      - decide 60 vs a 40 fps Deck mode after the first real level;
      - **Verify the engine install** in the Epic launcher
        (`SM_Template_Map_Floor` was re-saved; see the spec).
000a. **Reloads, all tested 2026-11-02** (user: "thats working", confirmed
    as covering all of them):
    - The M4, including a reload cut short by a dive and an enemy M4.
    - The revolver: camera staging, physics empties, the speedloader shown
      and pouched, a dive reload.
    - The shotgun rack.
    - The tap sounds.

    - **Next, the MP5:** `EChargingStyle::HKSlap` and its own ending, once
      its mesh is in. Start from the shared library in
      `Tools/AnimAuthoring/` (see its README).
    - Optional: a sound slot for the revolver's open click
      (`Revolver_Open_Cue`).
000. *(Done 2026-11-01, user: "46 and 47 are good": the pickup switch and
    melee are tested.)* **Optional melee follow-ups:**
    - real blunt-hit sounds;
    - a camera shake asset for `MeleeHitShake`;
    - the red 0 on the grenade choice when out.
00. **HUD strip (plan item 44).** Spec: *HUD: cinematic minimal*. Bars,
    layout, background and the Antonio font are built.
    - **User check:** the `Background` Image in `BarCluster` uses
      `MI_HUD_Background` (the user sets the brush, or re-pastes the cluster).
    - **Next:** the item strip in plan item 44, now separate pieces. C++,
      icons, `WBP_Grenades` / `WBP_WeaponIcon` / `WBP_BarCluster` and the
      paste-in text are done. The user pastes the five widget trees and
      places the pieces in `WBP_PlayerHUD` by hand (spec *Item strip*;
      `WBP_WeaponIcon` re-pasted for the dual pair + stroke), then PIE test
      (a dual pistol pair too), cleanup (`UAmmoWidget::GetGrenadeCount`,
      `WBP_Ammo`'s old binding functions), background.
    - **Optional:** a full-size GPT sheet in the folder re-cuts with real 4K
      detail.
    - **Optional:** delete the superseded flag-cap and grunge files.
00b. **Shoulder kick, deferred** (user: "dont fix the kick now"). The user
    wants the shoulder itself (the clavicle) to move, not the arm.
0. **Deck testing is on hold** (user, 2026-10-28: "lets do the Deck test later.
   Lets keep building on the PC for now until I want to test it again"). Build
   and test in the editor only; package for the Deck only when the user asks.
   Batch these for the next Deck run:
   - the black screen waiting for dressed characters (no floating gun, no
     pop-in);
   - enemies held until the fade completes;
   - the death-restart freeze (800–830 ms in the third trace);
   - trace it (open Insights first, `Tools/ClearTraces.ps1` after).
1. **Test in the editor** (built 2026-10-28, not tested): the black screen waits
   for everyone dressed; enemies stand still through the black and the fade,
   then go (`Lvl_Sandbox` director group, `Lvl_Linear` rooms and patrols,
   restarts); player input returns as the fade starts.
   - **Suggested next:** a fade to black before a death restart, to hide the
     0.8 s freeze on the old level's last frame.
   - **Undecided:** should the dive button stand up from a kneel and dive?
   - **Still open (user):** both suns' Dynamic Shadow Distance (movable) →
     4000; editor Engine Scalability → High.
   - **Later (item 34):** step 3 bake once level art exists; merge the two
     `BuildEnemy` copies into `AEnemyBase`; build-on-approach reserves for
     multi-arena levels; GC and CC2 tick costs.
2. **Wheel cycle on the face buttons** (user, `IMC_Default`, no code):
   probably done. The saved `IMC_Default` no longer has D-pad keys and now
   has Face Button Left. Confirm it cycles both ways on the Deck.
3. **Gunfire audio refactor** (plan item 31; home test: "to refactored").
   First: what exactly goes wrong — shots cutting each other off, or *all*
   sound dropping during bursts (the mixer's 32-voice ceiling → sound
   priorities/concurrency)? Then rework the fire-sound path.
4. `SC_Music` sound class on `DarkCrimes` (bridge; plan item 27's last part).
5. **Pump + grip (plan item 32):** user draws `Pump` on `MM_PumpShotgun_Fire`
   (the rack) and `HandGrip` at the end of `MM_Rifle_Equip`; then test the
   pump fire, a shotgun reload (ends with the last shell — no rack for now)
   and the equip landing. The slide's AnimBP waits for the final model.
6. **Final weapons (plan item 33):**
   - **Uzi left:** pickups and the wheel icon. The MAC Blueprints are
     unused; delete them later.
   - **Next models:** the Benelli M4 (`BP_Shotgun`), the SVD
     (`BP_BattleRifle`), the AR-15, the AK-74u.
   - **Benelli (2026-10-30):** `SK_Benelli` is built and imported with its
     materials.
     - **Done:** LOD0 ~8k with the shells kept, reimported (root in the
       grip), sockets, `BP_Shotgun` wired.
     - **User:** test and tune the grip; check the left hand (converted from
       the Mossberg, lock on); decide the magazine size.
     - **Animations made** (`A_Benelli_Fire`, `_LastShot`, `_Ready`;
       ReadyPose wired).
     - **Done and tested** (2026-10-30): animations wired, first import
       cleaned up.
     - **Magazines (user):** Benelli 8, pump 6 (bridge, saved). The shotgun
       ammo boxes still give 12 and 8.
     - **Animation pass done and tested.** Old animations deleted, except
       `Anim_P1911_M_Shot` + its kit montage (the user deletes them in the
       Content Browser).
     - **Uzi animation** rebuilt and tested.
     - **`AR4HatchOpen`** cleared and deleted: the cover opens on the first
       shot (tested).
     - **Done:** the old 1911 shot and its kit montage are deleted, and the
       Benelli source FBX is in `ArtSource`.
   - **SVD (`BP_BattleRifle`), in progress 2026-10-30:** `SK_Dragunov` is
     built, imported and wired onto `BP_BattleRifle` (spec *Dragunov SVD*).
     The second silent placeholder (item 7) is gone with it.
     Tested. Animations made, notified (user) and wired. Now
     `BP_SniperRifle` (renamed 2026-10-30).
     **User next:** test the shot sound, casing, bolt cycle, lock-open on
     the last round and close on reload. (`DisplayName` is now "Sniper
     Rifle".) The sniper pack is deleted (pack cleanup).
   - **Renames (2026-10-30):** weapon Blueprints are named by role (spec
     *Weapon Blueprint names*). *Fix Up Redirectors* done by the user
     (2026-10-30). (The `SMG11` leftovers went in the pack cleanup.)
   - **Pack cleanup done (2026-10-30, spec *Pack cleanup*):**
     - `SniperRiflePack` is gone and `FPS_Weapon_Bundle` is down to its 41
       used assets.
     - **Reopen the editor** and check the M4, AK, grenade and knife still
       load.
     - Commit when ready. The 199 bridge-deleted assets were never in git;
       the 33 tracked deletions show as `D`.
     - **Done 2026-10-31** (user: "delete the orphanated demo"): the
       orphaned `__ExternalActors__/Demo` and `__ExternalObjects__/Demo`
       folders (17 git-tracked files; their map
       `/Game/Demo/ThirdPerson/Maps/ShowcaseMap` no longer exists) are
       deleted on disk. They show as `D` in git. Plan item 33.
   - **AK-74u built, stockless** (`BP_AssaultCarbine` on
     `SK_KA74U_Stockless`, spec *AK-74u*), in `BP_Player_CC`'s test
     loadout. Tested. **Fire animation** `A_AK74U_Fire` made, notified and
     wired (2026-10-30). In-game name "AKS-74U". **User next:**
     - (the fire animation is tested: "tested, works");
     - place `LeftHandGrip` on `b_gun_Root`, calibrate it
       (`Bopis.LeftHandGripCalibrate 1`, lock off) and tick
       `bLockLeftHandRotation`;
     - LODs and an AK icon (it has the M4's).
   - **To do: MP5 submachine gun** (plan item 40; user: "Add MP5 SMG. A
     fast laser accuracy low damage SMG"). It needs a model from you, since
     none is in the project. Then the usual intake, `SubmachineGun` ammo
     with a five-magazine cap and its box, and stats agreed with you. A dual
     pair is an open question.
   - **Fire-cue audit (deferred):** `M4_Single_Shot_Cue` has no
     `ATT_Gunshot` or voice limit, so it's full volume at any range. Check
     every gun's fire cue against the revolver's settings.
   - **For each:** import skeletal, barrel along **+Y**, moving parts as
     bones. Sockets and grips are yours; Blueprints and wiring are Claude's.
     Guns that lock back also get a `ReadyPose` + `LastShotAnimation`.
   - **Still to decide:** which rifle the AR-15 replaces. (AK-74u ammo:
     its own, decided 2026-10-30.)
     (.45 vs 9mm: split, 2026-10-29, item 37.)
7. **Silent placeholders:**
   - **`BP_Shotgun`: fixed 2026-10-30.** Its `FireAnimation` was cleared
     when the Benelli went on.
   - **`BP_BattleRifle`: fixed 2026-10-30.** Its `FireAnimation`
     (`Fire_SniperRifle_W`) was cleared when the Dragunov went on.
   - Then test every gun: one shot sound, one flash.
7b. **Focus reload speed: done 2026-10-30** (item 39, tested). Tune
   `FocusReloadSpeed` (3) on `BP_PlayerCharacter` if it's ever wanted
   faster; past 3 the montage blends start to smear the animation.
8. **Long guns, left hand in the back poses: done 2026-10-30** (the
   left-hand slide; user: "not perfect but serviceable"). If revisited, tune
   `LeftHandMaxSlide` (15) and `LeftHandReachMargin` (3) in the ABP's Class
   Defaults; don't go back to pulling the gun in.
9. **New long guns:** calibrate and tick `bLockLeftHandRotation`
   (`Bopis.LeftHandGripCalibrate 1` in the lowered idle, lock off).
10. **First aid follow-ups** (item 36 done and tested): swap the placeholder
    `1kSineTonePing` for a real heal sound; decide where kits come from
    (placed only, or enemy drops too) and the starting count.
11. **Ammo split (item 37):**
    - **Test:** the 1911 and Beretta don't share; Uzi ammo still works; the
      sniper box feeds `BP_BattleRifle`.
    - **Boxes done:** renamed, plus rifle and shotgun boxes. Optional:
      *Update Redirector References* on `Pickups/`. Levels with the Beretta
      need 9mm boxes placed; the 12-gauge boxes may need their height tuned.
12. **Message feed (item 38):** done and tested (boxes, guns, drops,
    merging). Later: save messages once saving exists. The ammo wording is
    the table in `GameMessageSubsystem.cpp`.

**B. Editor / git**
1. **Repo cleanup:** the LFS push finished (local `main` = `origin/main`, checked
   2026-10-24); run the cleanup
   in `Documentation/Reports/2026-10-24_Audit.md` §4 (`git lfs prune`, orphan
   packs).
2. **Unused content** (Audit §3): decide and delete in the Content Browser —
   `CleanFlatIcons` and `Weapons` first (nothing uses them), then demo folders.
3. **`AM_Pistol_Reload_Offhand`** → Chamber notify → tick **Offhand**, if not
   done yet.
4. **Git:** the user commits and pushes. Latest: `36bc08ba` "Weapon Updates.
   Roll Update" on `feature/HardwarTargetAdjust`, pushed 2026-10-28; the
   doc edits after it are uncommitted.

**C. Can be done remotely** (C++ — presented first, then "apply and run")
1. Optional: `DualLoweredPlayRate` → `LoweredJogPlayRate` rename.

**D. Ongoing**
- Footstep tuning (`DA_FootstepEffects`, `ATT_Footstep`); physical materials on
  level materials as levels get dressed.
- Sound polish (plan item 23 follow-ups): loudness match, per-gun clicks,
  variants, a Weapons sound class.
- CC2 remainder: a civilian Blueprint when civilians are designed, body
  sliders, the Deck perf test (later).
- CC skin, watch for: female A-pose forearms sit inside the waist band, so an
  arm very close in front of a jacket at the hip could tuck behind it —
  tighten `MF_ApparelWaistBand` if it shows.

---

## 2026-10-23 (2) — Weapon sound normalization
**Summary:**
- **One path for every weapon sound.** Before: six guns' shots came from
  their fire animation's notify (16-voice global limit → shots dropped under
  fire), five from code (`FireSound`); the Real_Recorded cues had no
  attenuation (full volume anywhere); the pistols' notify and `FireSound`
  were different files; reloads, draws and dry fire were silent. Now:
  `AWeaponBase::PlayWeaponSound(EWeaponSound)` plays every sound on the gun
  (per-gun voice limit), each weapon BP has a `Weapon|Sounds` slot per event,
  and `AN_WeaponSound` on a montage or weapon animation asks the gun in hand
  for that event — one `AM_Pistol_Reload` serves the hi-power's mags and the
  revolver's speedloader. Shared `ATT_Gunshot` (10 m full, 80 m silent,
  muffled far) / `ATT_WeaponFoley` (2 m / 15 m) under `/Game/Audio/Weapons/`.
  Spec: *Weapon sounds*.
- **Verified from the saved assets** (the bridge can't read notify arrays;
  parsed the export tables): each reload montage has Mag Out / Mag In /
  Chamber, the shotgun reload a Round In, the equips an Equip, the pump
  animation a Pump; the three gunshot notifies are gone. **One miss:**
  `AM_Pistol_Reload_Offhand`'s Chamber notify has Offhand unticked.

- **PIE test (user):** shots and the new reload/draw sounds play — but
  only after an editor restart; the first PIE after the bridge filled the
  slots and the user placed the notifies was silent for reloads/draws, with
  everything already saved on disk. Cause unknown; gotcha logged. Two
  temporary `UE_LOG(LogTemp)` lines (`[WeaponSound] …`) are still in
  `AnimNotify_WeaponSound.cpp` and `WeaponBase.cpp::PlayWeaponSound`.
- **From the test:** (a) consecutive shots "cut" the audio when looking
  around — taken to be the 4-voice stop-oldest chopping 2.7 s tails: gunshot
  cues now 8 voices + 0.25 s steal fade (not re-tested by the user); (b)
  MWS handling sounds changed volume with camera distance — `ATT_WeaponFoley`
  inner radius 200 → 500. The diagnostic log lines are removed again. The
  rest (notify timing, 3× reload bunching, loudness) is the user's tuning;
  the weapon models will be replaced, so no asset polish now.

- **Corpses on CC's constraints (later 10-23, compiled, not playtested):**
  `RagdollPhysicsAsset` on `ABopisCharacterBase`, swapped in by
  `StartRagdoll`; `BP_Enemy_CC` / `BP_Player_CC` → `CCMH_Body_Physics`
  (unchanged from the CC2 source). Alive physics stays on `PA_CCMH_Bopis` /
  `PA_CCMH_Player`. Spec: *NPC characters (CC2)* → Physics.

- **CC deaths playtested (user):** first "the CC constraints look better" —
  a false positive (placed enemies kept their own copy of the Blueprint
  default, so they still died on `PA_CCMH_Bopis`; after the editor restart
  CC's asset really ran and ragdolls stretched like a body stuck in a door,
  on flat ground). Swapping to `PA_CCMH_Player` instead was fine → the swap
  mechanism works, CC's `CCMH_Body_Physics` is a cloth-collision asset, not
  a ragdoll. `RagdollPhysicsAsset` cleared on both CC Blueprints; bodies
  back on `PA_CCMH_Bopis` / `PA_CCMH_Player`. **Gotcha:** a Blueprint default
  set through the bridge doesn't reach actors already placed in a level
  until the level reloads; spawned actors get it at once.
- **Slow motion off mid-dive (user: "works"):** the Focus key or
  the dive key during a dive now ends the slow motion — the dive's own free
  Focus, or the player's Focus it was holding (`UShootdodgeComponent::
  CancelSlowMotion`, called from `DoToggleFocus` / `DoShootdodge`); the dive
  carries on at full speed. Pressing Focus again afterwards starts the
  player's own Focus as usual. The old mid-dive "claim" (Focus key kept
  bullet time past landing) is gone for dives; a kill's slow motion outside a
  dive can still be claimed. Spec: *Shootdodge → Slow motion*.

- **Lean into turns (user: "works", defaults kept):** walking/jogging
  lowered, the torso banks by the actor's yaw rate (`UpdateLean`;
  `LeanPerYawRate` 0.1, `MaxLeanAngle` 15, `LeanFullSpeed` 500,
  `LeanInterpSpeed` 6, `LeanPerDegree` pitch 1 as the axis/sign escape
  hatch); three spine Modify Bones on the standing branch before the blade.
  Enemies too; never raised, crouched, diving, rolling or airborne. Spec:
  *Lean into turns*.

- **Footsteps (compiled + assets, not playtested):** the Lyra clips'
  `FootPlant_Left/Right` name notifies → `AnimNotify_FootPlant_*` on the
  anim instance → `ABopisCharacterBase::PlayFootstep` (foot trace with
  physical material) → `UFootstepEffectsData` (`DA_FootstepEffects`: 24
  surfaces from the Footstep_Casual pack, Default = Concrete; walk 0.6 /
  jog 1 / crouch 0.4). `ATT_Footstep` 3 m → 25 m, 2 voices per character
  (the sound is played with the character as owner). On `BP_PlayerCharacter`
  and `BP_EnemyBase`. Spec: *Footsteps*. Blockout floors have no physical
  material → all Default (**Stone**, user's pick) for now. **First test was
  silent:** the Lyra `FootPlant_*` names are sync markers, not notifies (the
  FootFX notifies are Lyra's `LyraContextEffects` class, absent here), so
  detection moved to the pose (`UpdateFootsteps`: foot ≥ 5 cm above its
  ref-pose height then back within 2 cm = a plant) — **works** (log: 2,352
  plants over 13 PIE runs, walk/jog volumes blending, 286 rejected in the
  air and 495 at a standstill; the user's wood patch read as Low Wood).
  Diagnostic logs removed again. Footstep patches: a
  Visibility-only Blocking Volume with a Phys Material Override from the
  ImpactsVFXVol1 pack's `Physical_Materials` (all 24 verified) — spec.

- **Thuds (user: "thuds work"):** dive landing, roll tumble (at 20 % of the
  roll) and falls onto the feet (by fall speed; enemies too), all
  surface-aware through `PlayThud` with CC's `Landing_Cue` layered under the
  body ones. User tuned the asset: dive 3, roll 2, fall 3 (C++ defaults
  1.5 / 1 / 1.2). Spec: *Footsteps → Thuds*.
- **Bark variation (user: "works", defaults kept):** each enemy rolls a pitch
  from its `UBarkVoice`'s `PitchMin`–`PitchMax` (0.92–1.08) when it gets the
  voice (BeginPlay / `SetBarkVoice`) and keeps it for every line — barks and
  scripted dialogue; each bark adds ±`PitchJitter` (3 %) and down to
  −`VolumeJitter` (15 %). `UBarkSubsystem::PlayVoice` takes pitch/volume.
  Spec: *Enemy barks → Variation*.
- **Weapon wheel (compiled + assets, not playtested):** first built with one
  segment per carried weapon; the user wants **GTA V**: six fixed segments
  by weapon type, counter-clockwise from the top, mouse wheel cycles within
  the hovered type, Tab blocks all other input and slows time, release
  equips — rebuilt that way the same evening (`UWeaponWheelWidget`,
  `WeaponWheelCycleAction`, input guards on every handler, free Focus for
  the slow motion). `DisplayName` + `Icon` on all 11 weapons (Handcrafted
  White set; revolver/MAC-11/launcher icons are guesses). **The IMC
  mappings can't be made by the bridge** (`Mappings` reads empty): the user
  mapped `IA_WeaponWheel` (Tab + LB); `IA_WeaponWheelCycle` (Mouse Wheel
  Axis, D-pad Up / Down-negated) is still to map. The first test showed the
  object-reference CDO gotcha again (`WeaponWheelAction` None in PIE until a
  restart — now a verified gotcha in the plan). Spec: *Weapon wheel*.

- **Slum respawning arena: paper layout only** (user: "I just want a Level
  Layout, not a thing in UE5"). `Design Document/Arena_Slums_Layout.html`:
  48 × 40 m, barangay half-court centre, ring lanes, jeepney/kiosk sightline
  breakers, plank gallery +4 m with two stairs on the east row house, 8 dead-
  end alleys with shanty doors as enemy entrances, 3 wander points. Open
  (user's): one-time vs. returning grenades/rockets; endless vs. a goal.

*(RESUME HERE moved to 2026-10-24.)*

### (old) RESUME HERE
1. **Fix (user, 10 s):** `AM_Pistol_Reload_Offhand` → the Chamber notify →
   tick **Offhand**, save.
2. **Weapon wheel, designer version:** in `WBP_WeaponWheel` delete
   `WheelCanvas`, Ctrl+V the tree from `Tools/MakeWeaponWheelTree.ps1
   -Clipboard` (adds `IconDual_N`, full-opacity icons), compile, save. Then
   the playtest (check a dual pair and the shared icon height): press
   1–6 → the wheel comes up with that type lit and stays; the same key (or
   the key of the gun in hand) steps the type's next weapon; other keys move
   the highlight; click → equip + close; combat keys dead while it's up
   (movement and camera free, user's call), time slow. Icons now at their own proportions on a fat ring. Swap
   guessed icons on the weapon BPs. Pad flow (hold LB, point, release) is
   there too; its cycle action `IA_WeaponWheelCycle` is unmapped (optional:
   Mouse Wheel Axis, D-pad Up / Down-negated).
3. **Commit (user):** `FootstepEffectsData.h/.cpp`, `BopisCharacterBase.h/.cpp`,
   `ProjectBopisCharacter.h/.cpp`, `ShootdodgeComponent.cpp`,
   `RollComponent.h/.cpp`, `BarkSet.h`, `BarkSubsystem.h/.cpp`,
   `EnemyBase.h/.cpp`, `EncounterEvent.cpp`, `DA_FootstepEffects`,
   `Landing_Cue`; wheel: `UI/WeaponWheelWidget.h/.cpp` (new),
   `WeaponBase.h`, `WeaponHolderComponent.h`, `ProjectBopisCharacter.h/.cpp`,
   `IA_WeaponWheel`, the 11 weapon BPs, `BP_PlayerCharacter`,
   `BP_Player_CC`, `IMC_Default` (after the mapping); docs.
3. **Footstep tuning (user):** `DA_FootstepEffects` (gait volumes,
   `VolumeScale`, per-surface sets) and `ATT_Footstep`; physical materials
   on level materials / patches as levels get dressed. Later: landing thud,
   jog as AI noise.
3. ~~Commit~~ — pushed by the user (2026-10-23, evening): footsteps, lean,
   slow-mo cancel, ragdoll slot, sounds. *(Old list:)* `Gameplay/FootstepEffectsData.h/.cpp` (new),
   `DA_FootstepEffects`, `/Game/Audio/Footsteps/`, 145 Footstep_Casual
   cues, `BP_PlayerCharacter`, `BP_EnemyBase`; plus: `ProjectBopisAnimInstance.h/.cpp`, `ABP_Player`,
   `ShootdodgeComponent.h/.cpp`, `ProjectBopisCharacter.cpp`,
   `BopisCharacterBase.h/.cpp`, `BP_Enemy_CC`, `BP_Player_CC`, docs.
3. **Re-check once:** consecutive shots while looking around (should no
   longer chop); if it still cuts *all* audio, it's the mixer's 32-source
   ceiling → sound priorities. Your tuning: notify timing, 3× reload.
3. **Commit (user):** `WeaponBase.h/.cpp`, `AnimNotify_WeaponSound.h/.cpp`;
   `/Game/Audio/Weapons/` (2 assets); the 11 weapon BPs; 7 montages; 3 MWS
   fire animations; ~37 sound cues (attenuation/concurrency); plus the
   still-uncommitted 10-22/10-23 items (ABP_Player, skin/apparel materials,
   36 garment MIs, MF_ApparelWaistBand, backups, docs).
4. Sound polish (plan item 23): pack loudness match, per-gun clicks,
   round-robin variants, Weapons sound class.
5. Carry-overs: clothing layers on the female MIs + tucked list review;
   optional `DualLoweredPlayRate` → `LoweredJogPlayRate` rename (user
   types); Git LFS as one deliberate commit; CC2 remainder (10-21 (3) list).

---

## 2026-10-23 — Lowered jog pace, blade double-speed legs
**Summary:**
- **Lowered jogs all at the dual pace.** The one-handed and long-gun lowered
  jogs ran at `LocomotionPlayRate` (0.75) while the duals got × 0.8 (0.6), and
  the dual's own Move-state jog was unwired at 1.0 — shown during a dual
  reload, since the reload drops the dual layer. The user wired all six Move
  lowered players to `GetDualLoweredPlayRate` (the bridge can't add nodes
  inside a state graph). One knob: `DualLoweredRateScale` (0.8).
- **Double-speed legs after shooting from a jog (one-handed):** my 10-22
  `LayeredBoneBlend_13` shared `LayeredBoneBlend_10` with `_0`, so the mirrored
  strafe player ticked twice a frame while the TwoWayBlend blended. Fixed with
  a Save Cached Pose `BladeLegs` (bridge) + two Use Cached Pose nodes (user —
  the bridge's node list doesn't show a cache made in the same session).
  User: "works now".

### (old) RESUME HERE
1. **Commit (user):** `ABP_Player`; the skin master + both skin MIs; CC's
   apparel master + 36 garment MIs; `MF_ApparelWaistBand`; both backups in
   `Content/Characters/CC/Backup/`; docs.
2. **Clothing layers, follow-ups:** review the tucked list (only Shirt_01 and
   the police shirts); female MIs not done. Tuning: `Layer Spacing` (apparel
   master, 1.5), body MI `Waist Layer Depth` (3.5 — keep above 3 × spacing −
   2). Optional: swap the WPO push for Pixel Depth Offset by hand.
3. **Optional C++ tidy (user types):** rename `DualLoweredPlayRate` /
   `DualLoweredRateScale` → `LoweredJogPlayRate` / `LoweredJogRateScale` with
   a property redirect, now that it drives every lowered jog.
4. Git LFS: when wanted, one deliberate `git add --renormalize .` commit from
   a terminal; decline GitKraken's LFS prompts until then.
5. Remaining CC2 items from the 10-21 (3) list below (female body, placeholder
   outfits, PA_CCMH_Player preview mesh, Deck test deferred).

---

## 2026-10-22 — CC2 skin clipping
**Summary:**
- **Skin through clothes — fixed by depth, not hiding.** `M_Skin_CCMH`
  (CC's skin master, backup `/Game/Characters/CC/Backup/M_Skin_CCMH_Original`)
  adds two PixelDepthOffset terms: `Clothing Depth Bias` × `Neck_Mask` (head
  MI = 2 cm — the head mesh's collarbones/upper chest/back were most of the
  clipping) and `Body Clothing Depth Bias` × max(`Depth Region` = CC's
  T-shirt mask, worn apparel masks) (body MI = 2 cm). User: "close enough".
  Details in the spec's *NPC characters (CC2)*.
- **Tried and rolled back:** hiding skin under clothing (masked opacity). Body
  masks cut holes at tank-top armholes; head hiding (`neck Shrink` is on/off
  per item) removed chest skin under open collars. Two custom tank-top masks
  also dropped. The user hard-reset the branch to `5429704d`; GitKraken had
  frozen on an untracked `.gitattributes` (LFS for all assets) and staged all
  24,889 assets as LFS pointers — `.gitattributes` deleted, index reset.
- **Bladed strafe waist twist:** the jeans showing over the shirt hem while
  strafing bladed was the anim — the whole hips-vs-torso twist sat on the
  pelvis → `spine_01` joint. `ABP_Player` now spreads it over
  `spine_01`–`03` while bladed (`LayeredBoneBlend_13` + `TwoWayBlend_0`, spec
  *Bladed stance*). User: "looks better, pants still poke a bit".
- **Clothing layer order at the waist (later 10-22):** every male garment MI
  has a `Layer Depth` (0 outer / 1 untucked / 2 pants / 3 tucked; tucked =
  `MI_Shirt_01`, `MI_Police_Shirt_01`, judged by rest-pose hem height), pushed
  back in a waist band (`MF_ApparelWaistBand`) by WPO along the view ray —
  the bridge can't connect `MP_PixelDepthOffset`. Skin at the waist goes
  deeper (`Waist Layer Depth` 3.5). User: "it will do for now — there are
  cases that clipping is unavoidable". Spec: *Clothing layer order at the
  waist*.

---

## 2026-10-21 (3) — CC2 integration, branch `feature/CC2_Integration`
**Summary** (done by Claude while the user was away; nothing playtested by the
user yet):
- **CharacterCustomizer2 analysed** (the user's purchase + apparel pack). The
  part we use is CCMH: male/female body + head, 35 head shape targets (19 face
  sliders, 4 ethnicity head shapes ×3 incl. `asian`/`mixed`), 5 skin-tone
  sets, mesh hair/beards (no strand grooms), ~85 male apparel items with
  colour/print options, 25 outfit definitions; a character = one
  `CC_Saved_Variables` struct; `CharacterCustomizer` component applies it
  (Randomize All, Random Outfit, save/load). Light: a dressed CC character is
  ~30k verts at LOD0 (Manny alone 48.7k), 4–5 LODs per part, ~12 draw calls.
- **User decision: Option B** — the CC body *is* the gameplay mesh (runs
  `ABP_Player`), not a skin over a hidden Manny. And keep CC's customizer for
  hero characters.
- **Migrated by disk copy** (same `/Game/CharacterCustomizer/...` paths):
  1,842 files, 1.6 GB — CCMH, CC core (incl. customizer pawn/widgets),
  Base_Materials, and the Components/Misc pieces they reference. Not copied:
  CC2's demo levels, architecture, MetaHuman example. Plugins enabled in the
  `.uproject`: **HairStrands** (CC's component uses the groom component type)
  and **FullBodyIK** (one CC Control Rig).
- **Skeleton:** CCMH has every UE5 Manny bone **except the `ik_` bones**.
  `CCMH_Skeleton` lists SK_Mannequin + the four anim packs' skeletons as
  compatible; SK_Mannequin lists CCMH_Skeleton back (**`SK_Mannequin.uasset`
  modified**).
- **Physics:** `/Game/Characters/CC/PA_CCMH_Bopis` (copy of our tuned
  `PA_Mannequin`) assigned to `CCMH_Body_Male` / `_Female`.
- **Test enemy `/Game/ThirdPerson/Blueprints/CC/BP_Enemy_CC`** (child of
  BP_EnemyBase): mesh = `CCMH_Body_Male` tagged `Character`, `ABP_Player`;
  `Preset` variable (default `CCMH_Preset_Male_01`); construction script →
  `BuildCCCharacter`: adds CC's QualityLevel + CharacterCustomizer + a head
  (`CC_SkelMesh` tagged `Head`, `CCMH_Head_AnimBP` copies the body's pose),
  skin MIDs, then applies the preset's default look. Verified: builds in the
  editor viewport (head, hair, underwear) and runs in PIE with a clean log.

### (old) RESUME HERE
0a. **Player + apparel (10-21, late):** `BP_Player_CC` (child of `BP_Kamz`, CC body, `PA_Kamz` physics) plays in `Lvl_Sandbox`; not the default pawn yet. The pack's clothing was missing from the creator because the six stock presets used the base tables — switched to the `+` tables; PH preset added to the customizer's preset list. `Lvl_Linear.umap` shows modified (not Claude).
0. **Update (later 10-21):** `ik_` bones done (user); grip sockets copied (guns were at the feet — enemies use `HandGrip_R/L`, not `hand_r`); neck-seam fix (head ticks after body) — re-check in motion; random looks (`RandomizeLook`, `CCMH_Preset_PH_Male`, `DT_Outfits_PH_M`, role BPs `BP_Enemy_CC_Thug`/`_Goon`); creator level `/Game/Characters/CC/Lvl_CharacterCreator` + hero copy/paste workflow (spec). Deck test deferred (user). Items 1–4 below are done except the female body; review the placeholder outfits.
1. **Manual step (user, ~5 min): add the `ik_` bones to `CCMH_Body_Male`**
   (bridge can't add bones). Skeletal Mesh Editor → Skeleton Editing tool:
   `ik_foot_root` (parent `root`, at origin) → `ik_foot_l`, `ik_foot_r` (at
   the feet); `ik_hand_root` (parent `root`) → `ik_hand_gun` (at `hand_r`) →
   `ik_hand_l`, `ik_hand_r` (at the hands). Apply, save. Same for the female
   body if used. Without them: no left-hand grip IK and no prone floor fix.
2. **Playtest `BP_Enemy_CC`:** locomotion/aim on CC proportions (stretched
   bones → set those bones to Skeleton translation retargeting), weapon grip
   offsets, death ragdoll and staggers on `PA_CCMH_Bopis` (bodies may need
   resizing), hit reactions.
3. **Deck perf test:** 8–10 `BP_Enemy_CC` vs Manny enemies in one room.
4. **Then:** hero looks (a `CC_Saved_Variables` "Look" variable per
   Blueprint, customize-in-editor), the creator level (CC's customizer pawn
   compiles now), random rules (Filipino look, per-role outfit lists — design
   input needed on roles/outfits), body proportion sliders (CC does them in its
   own body AnimBP, which Option B doesn't run).
5. **Commit (user):** the branch; consider Git LFS before adding 1.6 GB.
6. Earlier items (stage 2 events playtest, bark polish, Phase 6) unchanged —
   see the 10-21 (2) list in [ProgressLog_Archive.md](ProgressLog_Archive.md).


---

*Older entries: [ProgressLog_Archive.md](ProgressLog_Archive.md).*
