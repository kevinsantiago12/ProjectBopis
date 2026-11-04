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

### ▶ RESUME HERE
**A. Next up**
000001. **Hair shine (2026-11-04):** the user judges the Default Lit hair in
    game, ideally after a rebake. Too dark or too light: adjust the material.
    Undo is in the spec.
000000. **`Lvl_BackAlleys`, open from 2026-11-04:**
    - **First:** rebake the lighting (the building floors moved everything). The
      last bake ran out of video memory in GPU Lightmass; cause not found.
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
    - The proxy fix for the "connected, 0 tools" hang awaits the user's OK.
    - `M_BackAlleys_Jalousie` is unused; delete only if the user says so.
    - **Linear levels, deferred (user: "not yet"):** the builders can serve them
      once `gen_level.py` is split into a shared building library and per-level data.
      Tied to this arena: the single `arena` rectangle and its edge logic, hard-coded
      `B2`/`B10`/`B11`, one deck with fixed rail sides, stairs, and arena-only gameplay
      data. Walls only face N/S/E/W, and houses are shells with no interiors. The split
      must still generate the identical `Lvl_BackAlleys` plan. Don't start unasked.
0000000. **`Lvl_BackAlleys` kisame roofs (2026-11-03):** rebuilt (3,876 placed,
    0 failures, traces as before) and captured against the shanty photo.
    The flashing fix, one-board weatherboards, sealed sloping sides and the
    25% hollow-block wall mix are applied too. Left: the user's call on
    toning down red-oxide.
00000. **Back-alley arena (`Lvl_BackAlleys`, 2026-11-02).** The Sandbox copy is
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
       done (spec *`Lvl_BackAlleys`: first build*).
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
