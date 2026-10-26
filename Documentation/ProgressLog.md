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

## 2026-10-24/25 — Weapon wheel, impact sounds, female CC, LFS, music, level exit, waves, CC skin, dual reload
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
- **Blood: size and floating chunks (user).** Blood's DA Scale → 0.5 did
  nothing visible (component scale doesn't reach these sprite sizes); the
  user trimmed `NS_ImpactBlood` in the Niagara editor instead. Its chunks
  then froze at the hit height on an invisible, raised copy of the floor.
  Tried: Distance Field collision (kept), small collision radius (no
  effect), a "Debris" trace channel + CPU ray trace (config, Blueprint
  responses, docs — **rolled back** at the user's call, verified: config
  back to HEAD, all six Blueprints' responses as before). **Fix: Local
  Space off on BloodChunks1** (user: "that fixed it"). Gotcha in the spec.

### ▶ RESUME HERE
**A. Next up**
1. **Gunfire audio refactor** (plan item 31; home test: "to refactored").
   First: what exactly goes wrong — shots cutting each other off, or *all*
   sound dropping during bursts (the mixer's 32-voice ceiling → sound
   priorities/concurrency)? Then rework the fire-sound path.
2. `SC_Music` sound class on `DarkCrimes` (bridge; plan item 27's last part).
3. **Pump + grip (plan item 32):** user draws `Pump` on `MM_PumpShotgun_Fire`
   (the rack) and `HandGrip` at the end of `MM_Rifle_Equip`; then test the
   pump fire, a shotgun reload (ends with the last shell — no rack for now)
   and the equip landing. The slide's AnimBP waits for the final model.
4. **Final weapons (plan item 33):** 9mm pistols made — place `MuzzleFlash`
   and `AmmoEject` on `SK_Beretta_92FS`, then tune grips in PIE. Still to
   decide: AR-15 replaces which rifle; AK-74u ammo; .45 vs 9mm ammo. Then
   import one gun at a time (skeletal, +X barrel,
   moving parts as bones) — sockets and grip offsets are yours, Blueprints
   and wiring Claude's.
5. **Fire notifies (feedback standard, plan item 33):** on `Fire_Pistol_W`
   (.45s, enemy pistol), `Fire_Shotgun_NoDelay` (semi-auto shotgun) and
   `Fire_SniperRifle_W` (battle rifle), delete the flash notifies and add a
   Weapon Sound **Fire** notify at the shot; check `Mossberg-500_Pump` has a
   Fire notify and no flash. Then test every gun: one shot sound, one flash.
6. **M4 hatch** (`b_gun_shelleject_hatch`): skeleton editing tool or an M4
   fire animation.
7. **Deferred (user): prone on the back** after a shootdodge — the left hand
   can't reach `LeftHandGrip` ("maybe fix this later but ignore for now").
8. **New long guns:** calibrate and tick `bLockLeftHandRotation`
   (`Bopis.LeftHandGripCalibrate 1` in the lowered idle, lock off).

**B. Editor / git**
1. **Repo cleanup:** the LFS push finished (local `main` = `origin/main`, checked
   2026-10-24); run the cleanup
   in `Documentation/Reports/2026-10-24_Audit.md` §4 (`git lfs prune`, orphan
   packs).
2. **Unused content** (Audit §3): decide and delete in the Content Browser —
   `CleanFlatIcons` and `Weapons` first (nothing uses them), then demo folders.
3. **`AM_Pistol_Reload_Offhand`** → Chamber notify → tick **Offhand**, if not
   done yet.
4. **Committed and pushed** by the user (`f7611c2c`, `4103f1da`, 2026-10-26);
   working tree clean.

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
