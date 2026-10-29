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

### ▶ RESUME HERE
**A. Next up**
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
   - **For each:** import skeletal, barrel along **+Y**, moving parts as
     bones. Sockets and grips are yours; Blueprints and wiring are Claude's.
     Guns that lock back also get a `ReadyPose` + `LastShotAnimation`.
   - **Still to decide:** which rifle the AR-15 replaces; AK-74u ammo.
     (.45 vs 9mm: split, 2026-10-29, item 37.)
7. **Silent placeholders:**
   - `BP_Shotgun` (`Fire_Shotgun_NoDelay`) and `BP_BattleRifle`
     (`Fire_SniperRifle_W`) have no Fire notify, and an old particle notify
     gives a second flash.
   - Suggested: clear their `FireAnimation` (bridge, ask first) so they
     sound from code until the Benelli and SVD replace them.
   - Then test every gun: one shot sound, one flash.
8. **Deferred (user): prone on the back** after a shootdodge — the left hand
   can't reach `LeftHandGrip` ("maybe fix this later but ignore for now").
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
