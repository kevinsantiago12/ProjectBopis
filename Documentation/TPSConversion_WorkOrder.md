# TPS Conversion — Work Order

> **Branch-scoped working document.** Lives on `tps-conversion`; fold the
> outcome into [ProjectPlan.md](ProjectPlan.md) Phase 4.5 and delete this file
> on merge.
>
> Phase 4.5 in `ProjectPlan.md` is the **reference** checklist, organised by
> topic. This is the **execution** order: same work, sequenced by dependency
> and by rebuild boundary, with a playable state at the end of every step.
>
> Created 2026-09-25. Branch base: `321eb4a9` + uncommitted doc/pack work.

---

## Why this order

Two constraints drive the sequencing, not preference:

1. **Live Coding cannot handle structural changes** — new or renamed
   `UPROPERTY`/`UFUNCTION`, type changes, or component-hierarchy changes all
   need a full editor close + Rebuild Solution. Most of this conversion is
   structural, so steps are batched to minimise rebuild cycles. Each
   "🔁 REBUILD" marker is an editor close, a rebuild, and a reopen.
2. **Some changes cannot be split.** Deleting `FirstPersonMesh` breaks
   `WeaponHolderComponent` and the montage calls in the same compile. They
   ship together or nothing compiles.

Every step ends somewhere playable. On a branch that's the whole point — if
the conversion is abandoned, it's abandoned from a known-good state.

---

## Step 0 — Baseline (no code)

- [ ] Confirm the FPS build still runs in PIE on this branch before changing anything. The revert point is only useful if it's verified.
- [ ] Note the current `MuzzleSocketName` value per weapon and whether the socket actually exists on the `MilitaryWeapSilver` meshes. Step 5 depends on this and it's free to check now.
- [ ] Decide the two still-open questions, or accept defaults: **shoulder swap** (default: skip for now, cheap to add later) and whether intermediate steps get committed (default: yes, one commit per step — it's what makes the branch worth having).

---

## Step 1 — Camera rig + mesh consolidation ✅ DONE (2026-09-30)

**The atomic one.** These cannot be separated: removing `FirstPersonMesh`
deletes `GetFirstPersonMesh()`, which `WeaponHolderComponent` and both
montage calls depend on. All of it lands in one compile.

Files: `ProjectBopisCharacter.h/.cpp`, `WeaponHolderComponent.cpp`, `WeaponBase.cpp`

- [x] **Add** `USpringArmComponent` on the capsule + `UCameraComponent` on the arm. `bUsePawnControlRotation` moves to the arm.
- [x] **Delete** the first-person camera flags — `bEnableFirstPersonFieldOfView`, `bEnableFirstPersonScale`, `FirstPersonFieldOfView`, `FirstPersonScale` (`ProjectBopisCharacter.cpp:30-33`).
- [x] **Delete** `FirstPersonMesh` and everything downstream of it: the component (`.h:32`, `.cpp:39-43`), `HiddenFirstPersonBones` (`.h:59`), the `HideBoneByName` loop (`.cpp:69-72`), `SetFirstPersonVisibility()` (`.h:139`, `.cpp:287-304`), and `GetFirstPersonMesh()` (`.h:155`).
- [x] **Remove** `GetMesh()->SetOwnerNoSee(true)` and the `FirstPersonPrimitiveType` assignment (`.cpp:48-49`).
- [x] **Repoint** montage playback to `GetMesh()->GetAnimInstance()` (`.cpp:200`, `.cpp:233`).
- [x] **Repoint** `AttachWeaponToHand()` to `GetMesh()` (`WeaponHolderComponent.cpp:107`) and drop the `SetFirstPersonPrimitiveType` call (`:124`).
- [x] **Drop** the muzzle-flash `SetFirstPersonPrimitiveType` (`WeaponBase.cpp:127`).
- [x] **Rename** `GetFirstPersonCameraComponent()` → `GetCameraComponent()`. ⚠ Check Blueprint callers first — the ABP or HUD may bind it, and a rename breaks those silently at compile-time-for-BP, not for C++.
- [x] Editor side: `BP_FirstPersonCharacter` will need its ABP confirmed on the body mesh, and the spring arm tuned (`TargetArmLength`, `SocketOffset`, lag).

**Playable state:** third-person camera, body mesh visible, weapon attached
and firing. The weapon will be **positioned wrong** and the animations will
be first-person arms clips playing on a full body — both expected, both
fixed later. Don't chase them here.

**Outcome (confirmed in PIE 2026-09-30):** compiled and ran with no errors.
Third-person camera working, character navigates, weapon attached and firing.
Movement animations wrong — first-person arms clips playing on a full body,
exactly as expected. Deferred to Step 7.

**What should disappear on its own:** the stale render-proxy snap, the
FirstPerson tagging on spawned particles, and the muzzle flash rendering
through the wrong projection. If any survives, it wasn't a projection bug.

---

## Step 2 — Movement, GRB model ✅ DONE (2026-09-30)

New `UFUNCTION`s, so structural. Small batch though.

Files: `ProjectBopisCharacter.h/.cpp`

- [x] **Rewrite `DoMove`** (`.cpp:151-159`) to derive axes from `GetControlRotation()` yaw instead of `GetActorForwardVector()`/`GetActorRightVector()`. **This single change is the camera-relative model**, shared by both states.
- [x] Add `ApplyMovementMode(...)` — sets the flag pair and the speed together, in one place. **Three states, not two** (decided 2026-09-30): non-aim, aim, and prone-with-animation-authority. Prone arrives via the shootdodge and must hand rotation control to the animation, or the capsule snaps to camera yaw while the prone turn-in-place animates a slow rotation. See *Combat abilities* in [TechnicalDesignSpec.md](TechnicalDesignSpec.md) — cheaper to write as three now than to retrofit.
- [x] Non-aim: `bOrientRotationToMovement = true`, `bUseControllerRotationYaw = false`.
- [x] Aim: `bOrientRotationToMovement = false`, `bUseControllerRotationYaw = true`.
- [x] Call it from `DoAimStart`/`DoAimEnd`, and once in `BeginPlay` so the initial state is explicit rather than inherited from constructor defaults.
- [x] Tune `RotationRate` down from the `(0, 500, 0)` default.
- [x] Aim-state `MaxWalkSpeed` drop.

**Playable state:** walk around and the character turns to face travel; hold
aim and it strafes while facing the camera. Locomotion animation will be
wrong in the aim state — no strafe clips exist yet. Verify the *rotation
behaviour*, ignore the feet.

**Outcome (confirmed in PIE 2026-09-30):** rotation behaviour correct in both
stances. Implemented as `EMovementStance` + `ApplyMovementStance()` rather than
a bool, so the third (`AnimationDriven`) state exists for the shootdodge
without revisiting call sites. `MaxWalkSpeed` is now owned by the stance
switch — editing it on the Blueprint appears to do nothing; change
`FreeRunSpeed`/`AimingSpeed` instead.

**Watch for:** both rotation flags true at once. The symptom is a character
that jitters or fights itself when moving while aiming.

---

## Step 3 — Aim stance + camera move ✅ DONE (2026-09-30)

Files: `ProjectBopisCharacter.h/.cpp`

- [x] **Split the `HasZoom()` gate** (`.cpp:265`). Movement mode and camera shoulder-in happen for **every** weapon; `HasZoom()` keeps gating only the FOV/magnification. Without this, the pistol and close-range rifle never enter aim stance at all.
- [x] Replace the FOV swap with a spring-arm lerp — `TargetArmLength` and `SocketOffset` between hip and aim values, over a short blend.
- [x] Keep `DoAimEnd` unconditional in restoring state, same reasoning as the current code: a weapon swap mid-aim must never strand the player.
- [x] Decide **sprint breaks aim** here if sprint exists by now; otherwise note it and move on.

**Outcome (confirmed in PIE 2026-09-30):** all three weapons now enter an
over-shoulder aim stance; the battle rifle additionally magnifies.

**Implemented pull-style, not push.** `DoAimStart`/`DoAimEnd` set state only;
`UpdateCameraTransition()` derives boom length, socket offset and FOV from
`bIsAiming` + the equipped weapon every frame and eases with
`FInterpTo`/`VInterpTo`. This is why the character now ticks
(`PrimaryActorTick.bCanEverTick = true`) — tick is load-bearing, not
incidental. Five camera values are exposed on the Blueprint so tuning needs no
rebuild.

**Playable state:** all three weapons enter an over-shoulder aim stance; the
battle rifle additionally magnifies.

---

## Step 4 — Crouch ✅ DONE (2026-10-03)

> **Came off the backlog.** Deferred 2026-09-30 on the grounds that crouch
> dragged a second full strafe blendspace behind it — **that was wrong**. The
> 2026-09-30 library inventory found complete crouch sets for both Rifle and
> Pistol (entry, exit, idle, four-way walk with starts/stops/pivots, crouch
> turn-in-place) and `BS_MM_Rifle_Crouch_Walk` already assembled. Animation
> cost is near zero.
>
> Brought forward because it was the **last C++ block** in the conversion, and
> because Step 7 builds the AnimGraph — adding crouch states afterwards means
> reworking a graph that wasn't planned for them.
>
> **Outcome (confirmed in PIE 2026-10-03):** crouch works.
>
> **Built with a hold/toggle switch** beyond the original plan:
> `bCrouchIsToggle` (`EditAnywhere`, `BlueprintReadWrite`) picks the mode, with
> both `Started` and `Completed` bound on one action. Marked
> `BlueprintReadWrite` so a future options menu can drive it without a C++
> change — it belongs in player settings eventually.
>
> Note `Crouch()`/`UnCrouch()` set `bWantsToCrouch` rather than changing height
> directly, so the movement component retries each frame. Releasing under a low
> ceiling in hold mode is safe: the character stands up on its own once clear.
>
> Crouch animations are not wired — clips exist, Step 7 wires them.

Files: `ProjectBopisCharacter.h/.cpp`, new `IA_Crouch` asset

- [x] **`GetCharacterMovement()->NavAgentProps.bCanCrouch = true`** in the constructor. It is `false` by default and without it `Crouch()` silently does nothing — check this first if crouch appears broken.
- [x] Create `IA_Crouch`, bind in `SetupPlayerInputComponent`. **Toggle**, not hold.
- [x] `DoCrouchStart`/`DoCrouchEnd` calling `ACharacter::Crouch()`/`UnCrouch()`.
- [x] Set `MaxWalkSpeedCrouched`; decide whether crouch+aim takes the lower of the two speeds or its own value.
- [x] Leave `ApplyMovementMode` unaware of crouch — stance and aim are orthogonal, all four combinations legal.
- [x] Check for a camera pop on stance change. The capsule half-height snaps while the mesh interpolates; the spring arm's own lag may absorb it. **Look before fixing.**

**Playable state:** crouch works in all four stance/aim combinations. Poses
will be wrong until Step 7.

---

## Step 5 — Firing and aim source ✅ DONE (2026-09-30)

The correctness fix. Everything before this is cosmetic by comparison.

Files: `WeaponHolderComponent.cpp`

- [x] Two-stage aim: trace from camera through screen centre to find the **aim point**, then fire from the **muzzle** toward it. Camera decides what you hit; muzzle decides where the bullet comes from.
- [x] Verify `MuzzleSocketName` is correct on all three `MilitaryWeapSilver` meshes — this is the first time it becomes load-bearing. Projectiles currently spawn at `TraceStart` and the socket is decorative.
- [x] Handle the near field: aim trace hitting closer than the muzzle, or muzzle inside geometry. Minimum convergence distance, or a muzzle-blocked check that suppresses the shot.
- [x] Re-verify the reticle still reads true now that the camera is off-centre.

**Outcome (confirmed in PIE 2026-09-30):** shots now originate at the barrel.
`GetMuzzleLocation()` / `GetMaxRange()` added to `AWeaponBase`;
`FireEquippedWeapon` does the camera trace, clamps the converge distance by
`MinConvergenceDistance` (200, exposed on the BP), and fires muzzle→aim point.

**Aim offsets are not in yet** (Step 7), so the gun is held level regardless of
camera pitch. Note this is a *visual* mismatch only — the shot is still
correct, because `FireDirection` is computed from the muzzle's actual world
position to the aim point. Looking up means bullets leave a level-pointing gun
at an upward angle. It resolves itself when the aim offset lands.

**The muzzle-inside-geometry case is still open** — see the unchecked item
below. Deliberately left until the grip offsets are re-tuned, since how close
the character can stand to cover depends on where the gun actually sits.

**Playable state:** shots come from the gun and land on the crosshair, and
you can no longer shoot through the cover you're standing behind.

---

## Step 6 — Grip re-tune ✅ DONE (2026-10-03)

> Offsets are Blueprint data and need no rebuild. Deleting the TEMP timer
> removes a member variable, which changes class layout — **that part needs a
> full rebuild**, not Live Coding. Do the tuning first, then the deletion.

- [x] Re-tune `GripLocationOffset`/`GripRotationOffset` per weapon from scratch. Old values were fitted to the arms rig at first-person scale and are meaningless now. **Supersedes** the existing rifle-grip backlog item.
- [x] **Delete the TEMP 5s re-snap timer** — **done 2026-09-30, and it answered the question.** Removed the `FTimerHandle`, the `SetTimer` call and the dead `TimerManager.h` include. Verified in PIE: **the weapon position is identical for the whole session, with no change at the five-second mark.** The timer was doing nothing. `ProjectPlan.md`'s claim that it was "what makes the weapon position correct" was stale and has been corrected. (`WeaponHolderComponent.cpp:36-38`, handle `.h:51`). It was a first-person attach-timing band-aid. Verify the attach is correct without it before removing — if it's still needed, the underlying timing bug is real and separate.
- [x] Confirm `hand_r` is still the right socket on the body mesh.

---

## Step 7 — Animation (the long tail, no rebuild)

Asset and AnimGraph work. Weeks, not days. Nothing here needs C++.

- [x] Replace `FireMontages`/`ReloadMontages` contents with full-body clips. The **TMap architecture keyed by `EWeaponAnimType` is unchanged** — only the assets swap. Fix the two `UPROPERTY` comments that still say "played on FirstPersonMesh" (`.h:46`, `.h:52`).
- [x] Non-aim locomotion: forward-only set (idle/walk/jog). Cheap — the character always faces travel.
- [x] Aim locomotion: **8-way strafe blendspace**. The expensive half. *(2026-10-04: 4-way Lyra `BS_Rifle_Strafe`/`BS_Pistol_Strafe` + orientation warping for the diagonals.)*
- [ ] Crouched sets for both of the above. This roughly doubles the strafe authoring — it's the real cost of crouch.
- [x] **Aim offset** for pitch. *(2026-10-04: `AO_MM_Rifle_Idle_Hipfire`, sample base poses repaired.)* Mandatory now, wasn't in first person.
- [ ] **Turn-in-place** for the aim state, or the character skates when the camera swings while stationary.
- [x] Upper/lower body layering so firing and reloading play over locomotion. *(2026-10-04: `spine_01` montage layer + raised hip-fire pose.)*
- [ ] **Shotgun per-round reload montage with a looping section** (2026-10-04). Montage from the reload clip (pack `anim_shotgun_aim_reload`, user may tweak) split into sections `Start` → `Loop` ↺ → `End`; link Loop→Loop in Montage Sections so it repeats one shell-insert cycle. Code (present for review): character jumps the montage to `End` (`Montage_JumpToSection`) when the weapon stops reloading — simplest as a check in `Tick` (reload montage in `Loop` + `!IsReloading()`) — and stops it on weapon swap. Firing already cuts it (same slot). Sync: start by matching `TimePerRound`/`ReloadStartDelay` on `BP_Shotgun` to the section lengths (data only); optional later: drive montage play rate from `TimePerRound`. Waiting on the user making the montage (section names + lengths).
- [x] **Dual pistols** (demo, 2026-10-04) — code, `BP_DualPistols`, mirrored left arm, off-hand recoil and reload (`OffhandSlot` in `OffhandGroup`), lowered whole-body unarmed with finger grips. See the spec.
- [ ] **Dual reload torso motion** — `AM_Pistol_Reload` leans/twists the spine. Deferred fix: user-made no-spine clip + a `DualReloadMontages` map (small C++).
- [ ] **Clean-up:** delete the unused `bUseLoweredUpperBody`; the leg blend spaces' `Locomotion` sync-group settings are leftovers (harmless); restart the editor to clear the asset-registry dropout.
- [ ] **Per-weapon aim offset** — pistol AO samples likely need the same base-pose repair as the rifle ones.
### ⚠ Animation source changed again 2026-10-04 — back to Lyra

**User decision:** the Shotgun Locomotion Pack's quality is below Lyra's. **Lyra
is the animation source for all weapons, shotgun included.** From the pack,
only **`anim_shotgun_stand_idle`** (the lowered idle) is used, and probably
**`anim_shotgun_aim_reload`** (single clip — must be split into montage
sections Start / looping Insert / End for the per-round reload). The 2026-10-03
section below is **superseded** except for those two clips.

- Shotgun locomotion pins reuse the Lyra rifle clips. Keep `EWeaponAnimType::Shotgun`:
  it selects the shotgun fire montage, the per-round reload, and the lowered idle.
- Aim offset: Lyra `AO_MM_Rifle_Idle_Hipfire` (3×3).
- **Known issue:** lowered idle (gun down) vs Lyra jog (gun up) will lift the gun on
  every idle↔move transition while lowered. Fix: lowered-idle upper body over Lyra
  jog legs (Layered blend per bone) in the Move state.
- Fire: user may duplicate `MM_Rifle_Fire` and add a pump. **Open:** pump on every
  shot (pump-action, longer cadence) vs only chambering after a reload from empty
  (SPAS, matches the current semi-auto design).
- The pack (473 MB) is now mostly unused — trim via the editor (migrate/move the two
  clips first) when convenient.
- **Bridge limit found:** it can read anim *state* graphs but cannot create nodes in
  them (`Cannot cast type AnimStateNode to Blueprint`). In-state AnimBP work is manual.

### ⚠ Animation source changed 2026-10-03 — Shotgun Locomotion Pack

A **Shotgun Locomotion Pack** was added at `Content/ShotgunLocomotionPack/`.
It supersedes the Lyra-based plan below **for two-handed weapons**.

**Its skeleton is a non-issue.** The pack bundles its own
`Demo/Characters/Mannequins/Meshes/SK_Mannequin`, but that is a *copy of the
stock UE5 mannequin* — bone sets verified identical, including the 5-segment
spine and the full IK rig (`ik_hand_gun`, `ik_hand_l/r`, `ik_foot_root`).
**No retargeting.** Add the pack's `SK_Mannequin` to **Compatible Skeletons**
on `Content/Characters/Mannequins/Meshes/SK_Mannequin`. The property is
one-directional: it goes on *ours*, listing *theirs*. Leave the pack's
skeleton in place — its animations stay bound to it.

**What it contains (175 clips):** Jog and Walk at 27 each with **authored 45°
diagonals** (true 8-way, not blended), Aim 39 (aim variants of everything
including fire), AimOffset 9 (full 3×3 grid), TurnInPlace 8 (both stances),
Crouch 11, Sprint 13, Idle 9 including **stance transitions**
(aim↔stand, aim↔crouch), Jump 3, Loop_Root 29 (root-motion variants).

**Why it is better than the Lyra rifle set:** real diagonal clips rather than
blended ones, a sprint set Lyra's rifle locomotion lacks, and an aim/non-aim
split that maps **directly onto `EMovementStance`'s FreeRun/Aiming pair** —
`anim_shotgun_walk_*` for FreeRun, `anim_shotgun_aim_walk_*` for Aiming. The
stance system is already in code; this is that split pre-animated.

**`EWeaponAnimType::Shotgun` added 2026-10-03** (code only, not yet rebuilt).
Reversed an earlier call to skip it — that was made when only three shotgun
idle poses existed in Lyra and no locomotion.

- [ ] **Evaluate using this pack for the rifle too.** A shotgun and an assault
      rifle are held almost identically. If the pose reads acceptably with
      `Assault_Rifle_A`, one pack covers both weapon types with a better set
      than Lyra, and halves the remaining assembly. Costs nothing to look.
- [ ] Pistol stays on the Lyra pistol set regardless — one-handed pose.

### Lyra library inventory (2026-09-30) — still the source for pistol

- [x] **Library inventory done 2026-09-30.** Far better stocked than assumed — see below. Step 7 is **assembly and AnimGraph wiring, not authoring**; revised from weeks to days.

**What exists (`Content/Characters/Heroes/Mannequin/Animations/`):**
- **Aim offsets, built:** `AO_MM_Rifle_Idle_Hipfire`, `AO_MM_Pistol_Idle_ADS`,
  `AO_MM_Unarmed_Idle_Ready` — real `AimOffsetBlendSpace` assets, full 15-pose
  grids (3 pitch × 5 yaw). Plus simpler pitch-only `AO_Rifle` / `AO_Pistol` in
  the template tree at `Content/Characters/Mannequins/Anims/`.
  **Asymmetry to note:** rifle has a *hipfire* offset, pistol has an *ADS* one.
  Our two stances want both for each; component poses exist either way.
  `AO_MF_*` are Quinn — the rig already found to be unaligned. Use `MM_`.
- **Strafe clips, complete:** Rifle and Pistol each have Walk and Jog in
  Fwd/Bwd/Left/Right, every one with Start, Stop and Pivot variants.
- **Turn-in-place, complete:** `TurnLeft_90/180`, `TurnRight_90/180` for both.
- **Also there:** jump/fall sets, idle breaks, jog leans.
- **Only three BlendSpaces are assembled:** `BS_MM_Rifle_Crouch_Walk`,
  `BS_MM_Rifle_Jog_Leans`, `BS_MM_Unarmed_Jog_Walk`. The standing strafe
  blendspaces must be **assembled from existing clips** — editor work on a
  blendspace grid, not animation authoring.

**Verify before relying on it:** that these bind to the same skeleton as the
body mesh. Both trees are mannequin-based so almost certainly yes.
- [x] Folds in: the **ABP `Blend Poses by Enum`** backlog item, and **left-hand IK** (approach 2, per-weapon `LeftHandGrip` socket — now much more visible with the weapon on screen at full size). *(2026-10-05: done Lyra-style — `ik_hand_gun`/`ik_hand_l` + TwoBoneIK, raised only. Aim→lowered arm slide fixed with snap-down alphas; reload end eases via the `bEaseLowering` latch.)*

---

## Step 8 — Docs and merge

- [ ] `CLAUDE.md` — opening line says "first-person action shooter".
- [ ] `GameDesignDocument.md` + `.html` — first-person framing throughout Overview, Combat, Scope.
- [ ] `TechnicalDesignSpec.md` — rewrite the **First-person rig** section and the **first-person projection** architecture principle as third-person, keeping the old text as a dated note (it explains a lot of past decisions). Update the trace-source section for the two-stage model.
- [ ] `ProjectPlan.md` — tick Phase 4.5, fold in anything learned.
- [ ] `ProgressLog.md` — dated entry.
- [ ] Delete this file.
- [ ] Merge to `main`.

---

## Abandonment

If the conversion is dropped: `git switch main` and delete the branch.
Uncommitted working-tree changes follow you back; committed branch work does
not. Nothing in Steps 0–8 touches anything `main` depends on.
