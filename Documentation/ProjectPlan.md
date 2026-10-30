# ProjectBopis — Project Plan

> Ordered, incremental path from the current (mostly-empty) template state to
> a working vertical slice of the core combat loop. Broken into small phases
> so we can work through it bit by bit, one session/item at a time, rather
> than trying to build everything at once. Cross-reference
> `Design Document/GameDesignDocument.md` for the *why* behind each system;
> this file is the *in-what-order*.

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

> **Setting changed 2026-09-13.** The game is now a noir first-person action
> shooter set in the Philippines, 2002 (John Woo action, authored
> protagonist, human enemies). The 2098 sci-fi premise is discarded. Nothing
> in Phases 0–4 changes as a result — it's all setting-agnostic systems work
> — but the *rationale* recorded in some completed items (coilgun physics,
> synthetic enemies, Halo as primary touchstone) is now historical, not
> canon. Those entries are left as written because they're a record of what
> was decided at the time. Weapon art was swapped from `SciFiWeapDark` to
> `MilitaryWeapSilver` (conventional firearms) on 2026-09-21.
> Phases 5–7 are reworded below; their content is otherwise unchanged
> pending the new story, which is design's current task. See
> `Design Document/Lore_And_Design_Notes.md` PART 1 and the implications
> section at the top of [TechnicalDesignSpec.md](TechnicalDesignSpec.md).

---

## Phase 0 — Clear the ground

<details><summary>Done — 4 items (expand)</summary>

Goal: a clean, version-controlled project that boots with nothing left over
from the parts of the template we're not using.

- [x] Initialize git, baseline commit of the original template state.
- [x] Remove `Variant_Horror` and `Variant_Shooter` — both `Source/` and
      `Content/` sides fully removed (2026-08-10; content was locked by the
      editor initially, cleared once it wasn't holding those files open).
- [x] Confirm it compiles and loads `Lvl_FirstPerson` with no missing-asset
      errors. Verified 2026-08-10 via the running editor's own session log
      (`Saved/Logs/ProjectBopis.log`): `MapCheck: 0 Error(s), 0 Warning(s)`,
      no `Variant_Horror`/`Variant_Shooter` references anywhere, editor
      running stable. C++ side implicitly confirmed too, since this is the
      same session `WeaponBase`/`WeaponHolderComponent` were compiling in.
- [x] Confirm the base FirstPerson character/game mode/controller still
      work in actual Play-In-Editor — confirmed 2026-08-11 via the full
      Phase 1 PIE weapon test below (moving/looking/firing all work).
      **Phase 0 fully done.**

</details>

## Phase 1 — Weapon foundation ✅ COMPLETE (2026-08-11)

<details><summary>Done — 4 items (expand)</summary>

Goal: a single generic weapon the player can fire, hip-fire only, built to
later carry the bloom system.

Note: the original plan assumed extending the template's `ShooterWeapon`
class — that's gone now that `Variant_Shooter` is deleted, so this is a new
class written against the design doc's spec, not a refactor of old code.

- [x] New `WeaponBase` class (data-driven: fire mode, damage, range falloff, zoom flag — no per-weapon custom firing logic). `Source/ProjectBopis/Weapons/WeaponBase.h/.cpp`.
- [x] Weapon-holder component on the character with a **configurable** carry capacity (carry-limit is still a design-owned open question — defaults to 2, easily changed). `WeaponHolderComponent` at `Source/ProjectBopis/Weapons/WeaponHolderComponent.h/.cpp`: `AddWeapon`/`EquipWeapon` logic, equipped weapon attached to a hand socket on `FirstPersonMesh` and tagged `FirstPersonPrimitiveType::FirstPerson` so it renders through the same path as the arms. Wired onto `AProjectBopisCharacter` as a `WeaponHolder` member.
- [x] Basic fire implementation (hitscan). `AWeaponBase::Fire()` does a `LineTraceSingleByChannel` out to `MaxRange` and dispatches `UGameplayStatics::ApplyPointDamage` on a hit (currently a no-op gameplay-wise — nothing has `Health`/overrides `TakeDamage` yet; intentionally deferred to Phase 4). `AProjectBopisCharacter::DoFire()` bound to a `FireAction` input.
- [x] Test weapon fireable in PIE — **fully tested and confirmed working 2026-08-11.** Along the way:
  - The user added a marketplace asset pack, **`Content/SciFiWeapDark/`** (Infima Games-style "Darkness" sci-fi weapon bundle: 7 weapons incl. Pistol/AssaultRifle/Shotgun/SniperRifle/RocketLauncher/GrenadeLauncher/Knife, each with animated skeletal mesh, sounds, FX, pickup Blueprints). Decision: **left in its own top-level vendor folder, untouched** — moving/renaming `.uasset` files outside the editor (or even carelessly inside it) breaks their baked-in internal cross-references; standard practice for third-party content is to leave it as delivered and reference it from our own Blueprints/data.
  - `WeaponBase::WeaponMesh` changed from `UStaticMeshComponent` to `USkeletalMeshComponent` to support this pack's animated weapons (animations not wired up yet — mesh currently sits in bind pose). Test weapon (`BP_TestWeapon`) uses `Darkness_Pistol`.
  - `StartingWeaponClass` (`TSubclassOf<AWeaponBase>`, spawns a starting weapon in `BeginPlay`) was documented as done prematurely in an earlier pass before being typed/compiled — caused real confusion later ("no Starting Weapon Class in step 6"). Actually added and compiled 2026-08-11.
  - Trace source was refined twice: first from the raw camera transform, then — per a real Halo-accuracy request — reworked to use `APlayerController::DeprojectScreenPositionToWorld` at a specific screen-space point (horizontal center, **2/3 down the viewport**, `CrosshairViewportPositionY = 0.667` on `WeaponHolderComponent`) rather than an approximated rotation offset. This is now the permanent trace-source approach.

</details>

## Phase 2 — Bloom / accuracy system ✅ COMPLETE (2026-08-12)

<details><summary>Done — 4 items (expand)</summary>

> **Superseded 2026-10-15** by the Max Payne shooting model (Phase 5, item 8):
> bloom, the cadence penalty and Semi/Auto were removed. Kept as history.

Goal: the actual accuracy model from the design doc — this is the first
system where "correct" behavior really matters.

- [x] Bloom tuning parameters on `WeaponBase`: `BaseSpreadAngle`, `MaxSpreadAngle`, `BloomPerShot`, `BloomDecayRate`, `BloomDecayDelay`, `IntendedCadence`.
- [x] Live bloom drives the actual shot cone: `CurrentBloom`/`TimeSinceLastShot` runtime state, `FMath::Lerp` between base/max spread, `FMath::VRandCone` for the randomized direction, decay gated by `BloomDecayDelay` in `Tick`. Debug line's visual start point offset 150 units in front of the camera (separate from the real `TraceStart` used for the actual trace) since a line starting at the camera itself is nearly impossible to judge the angle of.
- [x] Cadence-penalty behavior: firing faster than `1/IntendedCadence` adds extra bloom proportional to how early the shot was, on top of the normal per-shot amount.
- [x] Temporary on-screen bloom readout via `GEngine->AddOnScreenDebugMessage`, refreshed every `Tick`.
- **Bug caught by code review, fixed:** `ApplyPointDamage` was reporting the un-deviated `TraceDirection` instead of the actual fired `SpreadDirection` — harmless today (nothing consumes the damage direction yet) but fixed for correctness.
- **Also fixed along the way:** `ProjectBopis.Build.cs` still listed include paths for the long-deleted `Variant_Horror`/`Variant_Shooter` `Source/` folders (leftover from Phase 0, never cleaned up) — was producing UBT warnings on every build. Trimmed to just `"ProjectBopis"`.

</details>

## Phase 3 — Reticle & aim/zoom UI ✅ COMPLETE (2026-08-17)

<details><summary>Done — 4 items (expand)</summary>

Goal: player-visible feedback for bloom, aim, and zoom — kept structurally
decoupled from accuracy per the design doc.

- [x] **Reticle widget foundation.** `UReticleWidget` (`Source/ProjectBopis/UI/ReticleWidget.h/.cpp`), a `UUserWidget` subclass exposing `GetCurrentBloom()` (`BlueprintPure`, chains Character → `WeaponHolder` → `EquippedWeapon` → `GetCurrentBloom()`, defensively returns `0.0f` if any link is null). `WBP_Reticle` created at `Content/UI/` (parent `ReticleWidget`), Image widget showing `icon_line_aim_8` from the `CleanFlatIcons` marketplace pack (`Content/CleanFlatIcons/`, ~17,800 files, left untouched in its own folder — same rule as `SciFiWeapDark`; one harmless leftover `FlatIcon_PNG_PSD.zip` sitting in that folder, safe to delete whenever). Added `ReticleWidgetClass` (`TSubclassOf<UReticleWidget>`) + a new `BeginPlay` override on `AProjectBopisCharacter` that `CreateWidget`s + `AddToViewport`s it for the locally controlled player. **Confirmed visible and working in PIE.**
- [x] **Aim input and state tracking.** New `AimAction` input, bound to both `ETriggerEvent::Started` (`DoAimStart`) and `ETriggerEvent::Completed` (`DoAimEnd`) — unlike `Fire`'s one-shot press, aiming is a held state, so it needs both edges. Simple `bool bIsAiming` + public `IsAiming()` getter on the character. Compiled clean, reviewed, correct.
- [x] **Zoom FOV gated per-weapon on aim.** `WeaponBase::HasZoom()`/`GetZoomedFOV()` getters + a `ZoomedFOV` tuning property. `DoAimStart` sets the camera's real `FieldOfView` (not `FirstPersonFieldOfView`, which is a separate property only governing the arms/weapon-mesh rendering pass — zoom should narrow what you see of the *world*, not distort the gun's own proportions) to the equipped weapon's `ZoomedFOV` if it has zoom; `DoAimEnd` unconditionally resets to a `DefaultFOV` cached once in `BeginPlay` (outside the reticle-widget `if` block — the two are unrelated, an early draft nearly coupled them, which would've left `DefaultFOV` stuck at `0.0f` whenever `ReticleWidgetClass` was unset).
- [x] **Sanity check.** Confirmed by construction, not just by testing: `WeaponBase::Fire()` has no code path that reads `bIsAiming`/`IsAiming()` at all — bloom/spread and aim state are fully separate systems that never cross. One real bug found and fixed along the way: `WeaponHolderComponent::CrosshairViewportPositionY` (the Halo-accurate "2/3 down the viewport" trace-source point from Phase 1) doesn't work once zoom is involved — `FieldOfView` always narrows around the camera's true optical center (50%), so an off-center aim point and zoom permanently disagreed on where "center" was, making zoomed shots land somewhere other than where the view visually centered. Fixed by simplifying `CrosshairViewportPositionY`'s default back to `0.5f` (true center) for both hip-fire and zoom, dropping the authentic Halo offset for now rather than building dynamic per-state repositioning — deliberate scope call, not an oversight.

**Dropped from this phase (2026-08-13):** "center dot visible while aiming" — never actually typed in, no revert needed. Reconsidered: the dot should instead be a **headshot-enabled marker** (Halo-style precision indicator), not an aim-state indicator. That needs a real target with a distinguishable head bone and a precision-damage system to check against (`HitResult.BoneName` from the existing trace can detect this once something exists to hit) — deferred until Phase 5 (enemies), not part of Phase 3.

**Known issue — status corrected 2026-08-30 (3).** The original entry ("the
equipped pistol isn't correctly positioned/offset relative to the hand
socket — likely `WeaponAttachSocketName` or a missing relative transform,"
flagged 2026-08-12) turned out to be **two unrelated problems wearing one
symptom**, and both have since been addressed in code:
1. **The rendering half — fixed 2026-08-30.** A stale render proxy caused by
   direct assignment to `FirstPersonPrimitiveType` instead of the setter.
   Full writeup in Gotchas below; this was the cause of the "correct after
   an editor restart, wrong after Stop→Play" behavior.
2. **The offset half — mechanism landed, values not yet tuned.**
   `WeaponBase` now carries `GripLocationOffset` (`FVector`) /
   `GripRotationOffset` (`FRotator`) as `EditDefaultsOnly` properties with
   getters, and `WeaponHolderComponent::EquipWeapon` applies them via
   `SetActorRelativeLocation`/`SetActorRelativeRotation` immediately after
   the socket attach. This is the per-weapon hook the original note was
   asking for — but **both default to zero and no weapon has tuned values
   yet**, so it's a mechanism, not a finished fix. Tuning is per-weapon
   Blueprint config work, folded into the three weapon-configuration tasks
   at the end of Phase 4.

</details>

## Phase 4 — Weapon content & feel
Goal: three real, fully-realized weapons — not enemies yet. Decided
2026-08-12: deliberately reordered ahead of the old Phase 4 (enemies,
now Phase 5), since there's more value in getting weapons feeling complete
before building something to shoot at with them.

The three weapons: a semi-auto pistol, a full-auto close-range rifle, and
a mid-range semi-auto battle rifle. Mapped to `SciFiWeapDark` assets:
`Darkness_Pistol` and `Darkness_AssaultRifle` directly; the battle rifle
reuses `Darkness_SniperRifle`'s mesh/anims tuned down (lower/no zoom,
different damage/range/bloom) rather than sourcing a new asset, since the
pack has no dedicated "battle rifle."

- [x] **Fire feedback: sound + muzzle flash.** `FireSound` (`USoundBase`), `MuzzleFlash` (`UParticleSystem` — legacy Cascade, matching `SciFiWeapDark`'s FX naming convention (`P_` prefix), not Niagara; avoided a new `Niagara` module dependency), and `MuzzleSocketName` (defaults to unverified guess `"Muzzle"`, same caveat as the hand socket) on `WeaponBase`, spawned attached in `Fire()`. Added `bUseAnimationDrivenFeedback` (single flag gating both sound and flash together, since this pack's fire animations drive both as a bundle) — defaults `false` (code-driven, current behavior for every weapon); flip per-weapon once its Fire animation is actually playing with a working notify (Phase 4's animation step). Compiled clean, reviewed, correct.
- [x] **Placeholder hit-impact decal.** `HitDecalMaterial` (`UMaterialInterface`), `DecalSize`, `DecalLifeSpan` on `WeaponBase`; `Fire()`'s hit block restructured so decals spawn on *any* surface hit (`bHit`), not just hits with a valid damageable actor (`HitResult.GetActor()` — the old, narrower condition, which would've silently skipped decals on plain level geometry). Uses `HitResult.ImpactNormal.Rotation()` to orient the decal flush against whatever it hit. Decal source: user imported `Content/UWC_Bullet_Holes/` (~564 files, real per-surface decal materials — Concrete/Bricks/Asphalt/Glass/Flesh/Fabric/Cracks/Generic/etc.); `Instances/Decals/Generic/MI_Generic_1` is the placeholder pick (no surface detection yet, deliberately). A different pack, `Content/ImpactsVFXVol1/` (Niagara-based surface-reactive *particle* impacts, paired with `UPhysicalMaterial` assets per surface), was imported by accident while looking for decals — kept, deferred to its own task rather than discarded, see the task list. **Follow-up fix:** decals weren't visible from a distance — `SpawnDecalAtLocation` doesn't expose `FadeScreenSize` (the built-in distance-based decal culling threshold) at the call site, so the returned `UDecalComponent` is captured and `SetFadeScreenSize(0.0f)` called on it to disable the cutoff. Also added a toggleable debug trace: `CVarShowWeaponTrace` (`Weapon.ShowTrace` in the in-game console), a file-scope `TAutoConsoleVariable<bool>` gating the existing `DrawDebugLine` call — global debug-visualization switch, not a per-weapon property, so a console variable rather than a `UPROPERTY` fits it better. Compiled clean, reviewed, correct.
- [x] `AProjectileBase` — a real projectile actor (movement + collision + on-hit damage, fragmenting on impact), for the **close-range rifle** specifically. **Reversed 2026-08-17** from the original call below — the pistol and battle rifle stay hitscan; the close-range rifle is the one real projectile weapon. Reasoning flipped: dodgeable travel time only matters at close range, where an enemy would otherwise have zero reaction window against an instant hit — at the battle rifle's mid-range engagement distance, perceptible travel time would just read as an aiming penalty. In-world justification is electromagnetic (coilgun), not plasma: muzzle velocity scales with coil-stage count/barrel length, so the compact close-range weapon is physically slower than the longer-barreled battle rifle. The round is saboted/pre-scored to fragment on impact, trading penetration for a shrapnel burst, so "slower" doesn't read as "weaker" — strong against close/grouped/exposed targets, weak against armor/hard cover, which is where the hitscan pistol and battle rifle stay relevant. Full writeup in `Design Document/GameDesignDocument.md`'s "Weapon tech" section. ~~The pistol and close-range rifle stay hitscan (matches how Halo's own BR/AR/Pistol actually work); the battle rifle is the one real projectile weapon, chosen because its mid-range/semi-auto/deliberate-shot identity is exactly where perceptible travel time reads as a feature rather than a liability.~~
  **Progress (2026-08-17):** shell built and confirmed compiling — `USphereComponent` root + `UProjectileMovementComponent` (gravity disabled, flat trajectory), `InitialLifeSpan` so stray misses don't linger forever, `OnComponentHit` bound in `BeginPlay` to a `UFUNCTION() OnHit` that applies direct damage via `GetInstigatorController()` (the same call `WeaponBase::Fire()` makes — will only resolve to something real once whoever spawns this sets `Instigator` at spawn time, next task's job). Fragmentation burst added on top (`FragmentRadius`/`FragmentDamage`, a zero-distance `SweepMultiByChannel` — a same-start-and-end sweep is a common idiom for "what overlaps this point" — against `ECC_Pawn`, excluding the directly-hit actor so the burst catches *other* nearby targets rather than double-dipping damage on the one already hit). Compiled clean, reviewed, correct — `AProjectileBase` is fully done.
- [x] Fork `WeaponBase` to support firing a projectile instead of a hitscan trace, per-weapon. Split `Fire()` into a shared prefix (feedback + bloom-driven spread direction) and shared suffix (cadence/bloom bookkeeping), with `FireHitscan`/`FireProjectile` handling only the differing "how does the shot resolve" middle. Also closed a long-standing gap: `EquipWeapon` now calls `SetInstigator`/`SetOwner` on the equipped weapon (character → weapon → projectile), so `GetInstigatorController()` — called since Phase 1 but always silently null — finally resolves to something real. `FireProjectile` relies on `UProjectileMovementComponent`'s default behavior (launch along the owning actor's local forward axis) rather than manually setting velocity, since the actor is spawned with `SpreadDirection.Rotation()`. Compiled clean, reviewed, correct.
- [~] POV arms animation setup (idle/walk/fire/reload) for `FirstPersonMesh`. **Source changed (2026-08-18):** originally planned as `PistolAnimset`/`RifleAnimset`; switched to migrating raw animation clips from Epic's **Lyra Starter Game** sample instead (via the editor's Migrate tool). Migrated the full `Content/Characters/Heroes/Mannequin/Animations/` library (454+ files — Lyra's real production locomotion set: 8-directional aim offsets, full walk/jog cycles with start/stop/pivot variants, crouch, jump, turns) — deliberately kept all of it on disk rather than pruning ("better to have them and not need 'em"), but only using a small subset. ~~Character's mesh is Quinn~~ **Correction (2026-08-30): the project doesn't use the Quinn model at all** — confirmed by the user while ruling out a skeleton-retargeting theory for an unrelated bug. Mesh is Manny throughout; Lyra's `MM_`-prefixed (Manny) clips are used as-is with no retargeting involved. The `MF_`/Quinn split mentioned below never actually applied here.
  **Progress (2026-08-18):** `ABP_FirstPersonArms` created (Manny's skeleton), `Speed` float variable updated every frame from `TryGetPawnOwner → GetVelocity → VectorLength`, a 2-state `Locomotion` state machine (Idle ↔ Move, transition threshold `Speed` vs. `10.0`) confirmed working in PIE for the pistol. Two real corrections made along the way: **`MM_Pistol_Jog_Fwd` visibly drops the weapon pose** (wrong clip for this context) — swapped to `MM_Pistol_Walk_Fwd` instead, which holds properly; and the `Play` animation nodes needed their **Loop** setting turned on explicitly in the state graphs (didn't default the way expected).
  **Fire Montage — architecture revised before landing (2026-08-18):** first pass put `FireMontage` directly on `WeaponBase`, triggered from inside `Fire()` by reaching into the owning character for `FirstPersonMesh`. User caught two real problems with that: (1) a weapon shouldn't need to know how to animate whoever's holding it, and (2) more importantly, an `UAnimMontage` is authored against one specific skeleton — a single `FireMontage` property on the weapon can only ever be correct for one skeleton, breaking the moment the same weapon is ever fired by a different one (e.g. a future AI enemy). **Resolved by moving `FireMontage` off the weapon entirely** — `WeaponBase` now only exposes `UsesAnimationDrivenFeedback()` (a pure bool signal), and `AProjectBopisCharacter` owns its own `FireMontage`, playing it on its own `FirstPersonMesh` from `DoFire()` after checking that signal. This establishes the actual future-proof pattern: each animator (player character, and later each enemy archetype) owns its own montage/skeleton-appropriate feedback, rather than the weapon dictating one answer for everyone. Compiled clean, reviewed, correct — **Fire Montage step done.** Along the way, found and fixed a typo (`UAnimaMontage`) left over from an earlier attempt that meant that version had never actually compiled. **Remaining for this checklist item:** Reload as an Anim Montage (blocked — no ammo/reload system exists yet, so this needs that built first, not just a montage), then repeating Idle/Move (and now Fire) for the rifle.
  **Fire Montage asset — resolved 2026-08-30 (4).** The 2026-08-30 (3) audit flagged this as a blocker: `Content/Characters/Mannequins/Anims/Pistol/MM_Pistol_Fire_Montage.uasset` (committed in `230e3228`) had been deleted with the deletion staged, and a project-wide search reported **no `AnimMontage` asset anywhere in `Content/`**. **That search was wrong.** The montage actually in use is `Content/Characters/Heroes/Mannequin/Animations/Actions/AM_Pistol_Fire.uasset` — it arrived with the Lyra migration and lives under the still-**untracked** `Content/Characters/Heroes/` tree, and the sweep only matched the `*_Montage` naming pattern, not Lyra's `AM_` prefix. User confirmed the deletion of `MM_Pistol_Fire_Montage` was **deliberate** — `AM_Pistol_Fire` supersedes it. So the C++ side and the asset side are both intact: `AProjectBopisCharacter::FireMontage` points at `AM_Pistol_Fire`, and `bUseAnimationDrivenFeedback = true` on `BP_Pistol` (as the queued weapon stat table specifies) is correct — no montage needs recreating. **Lesson:** search asset types by class, not by filename convention; vendor/migrated libraries don't follow our naming.
**Flagged for later (not now — 2026-08-30):** plan for full-body visibility.
`GetMesh()` (the full body) will get its own copied/tuned animation set
separate from `FirstPersonMesh`'s arms, and the intent is to let the owning
player see their own legs when looking down (immersion), while hiding
head/neck/upper-torso bones so the camera doesn't clip into own geometry.
This requires removing `GetMesh()->SetOwnerNoSee(true);`
([ProjectBopisCharacter.cpp:46](../Source/ProjectBopis/ProjectBopisCharacter.cpp#L46))
plus a bone-hiding step (`HideBoneByName` or a mesh/material-side mask) —
neither done yet, explicitly deferred until after the current weapon-config
push.

**Landed in code but undocumented until 2026-08-30 (3).** A doc-vs-code audit
found several real changes sitting in the working tree that no phase entry
described, plus one factual error in a previous entry. Recording them here so
the plan matches reality:
- **Camera/arms attachment hierarchy was inverted** relative to the FPS
  template. The template attached the camera to `FirstPersonMesh`'s `head`
  bone; it now goes the other way — `FirstPersonCameraComponent` attaches to
  the capsule at a fixed `(0, 0, 90)` offset, and `FirstPersonMesh` attaches
  to the *camera*. The point is that the arms rigidly follow camera pitch
  instead of needing skeletal aim-offset blending to fake it, which is what
  made the abandoned `Layered Blend Per Bone`/Aim Offset node in
  `ABP_FirstPersonArms` redundant (see the 2026-08-30 log entry, where
  removing that stale node was investigated as a possible bug cause).
  `FirstPersonMesh`'s relative transform is deliberately left at zero — the
  attachment relationship is new, so there's no prior tuned offset to carry
  over, and it needs tuning by eye in the editor.
- **Correction to the 2026-08-30 entry: `FirstPersonScale` is not `1.0f`.**
  That entry identified camera/arms clipping as unaddressed because
  `FirstPersonScale` was "currently `1.0f` (a no-op)" and
  `FirstPersonFieldOfView` "matches the general gameplay FOV," and
  recommended dropping the scale to ~0.5–0.65 as a next step. Both halves are
  wrong against the actual source, and were already wrong when written —
  these are committed values, not new work:
  [ProjectBopisCharacter.cpp:32-33](../Source/ProjectBopis/ProjectBopisCharacter.cpp#L32)
  sets `FirstPersonFieldOfView = 70.0f` and `FirstPersonScale = 0.6f`, with
  `bEnableFirstPersonFieldOfView`/`bEnableFirstPersonScale` both `true`. The
  camera's general `FieldOfView` is never assigned in the constructor, so it
  sits at the engine default of `90` — meaning the first-person pass is
  genuinely narrower than the world pass and the anti-clip mechanism **is**
  engaged. The recommended `0.5–0.65` range was already satisfied before it
  was recommended. If clipping is still visually wrong, the cause is
  something else and needs re-diagnosing from scratch — don't start by
  re-tuning these two values.
- **Leftover debug code to remove.** `WeaponBase::Tick` still prints the
  temporary `RelLoc`/`RelRot` on-screen readout added purely to diagnose the
  2026-08-30 render-proxy bug (debug message slot `2`, alongside the
  intentional bloom readout in slot `1`). The bug it was built for is fixed;
  this should come out. Note it dereferences `WeaponMesh` unguarded, so it
  would also crash on any weapon whose mesh component is somehow null.
- **None of Phase 4 is committed yet.** `ProjectileBase.h`/`.cpp` are
  untracked, and `WeaponBase`, `WeaponHolderComponent`, and
  `ProjectBopisCharacter` all have uncommitted modifications, as do
  `ABP_FirstPersonArms.uasset` and several other content assets. The last
  commit (`230e3228`, "Shooting Mechanics Added") predates the projectile
  fork, the grip offsets, the render-proxy fix, and the camera restructure.
  Worth a commit before the weapon-configuration work starts, so there's a
  clean point to return to.

- [x] Configure `BP_Pistol` (semi-auto, hitscan, `Darkness_Pistol`). **Done 2026-08-30 (5)**, created and configured directly through the UnrealMCP editor bridge (no editor-UI walkthrough needed — see the log entry for why that changed). `Content/FirstPerson/Blueprints/BP_Pistol.uasset`, parented to `AWeaponBase`, `WeaponMesh` → `Darkness_Pistol`, stat values per the table now recorded in `GameDesignDocument.md`'s Combat implementation notes. `MuzzleSocketName = "Muzzle"` **verified against the actual mesh** (`Darkness_Pistol` has exactly one socket, named `Muzzle`) — that closes the "unverified guess" caveat from the fire-feedback task, at least for this weapon. `HitDecalMaterial` and `FireSound` mirrored from `BP_TestWeapon` (`MI_Generic_1`, `PistolA_Fire01`); the sound is currently inert because `bUseAnimationDrivenFeedback = true` suppresses code-driven sound/flash, but it's set so flipping that flag needs no follow-up. Grip offsets left at zero — still untuned, and **PIE on 2026-08-30 (6) showed the weapon badly misaligned in the possessed first-person view** (oversized, barrel pointing screen-left, hand not on the grip). Important: `BP_TestWeapon` misaligns *identically*, so this is not caused by the pistol or its mesh — see log entry (6). Tuning these offsets is the open work. Also swapped the player's `StartingWeaponClass` (`BP_FirstPersonCharacter`'s `WeaponHolder`) from `BP_TestWeapon` to `BP_Pistol`, so the pistol is what actually spawns in hand; `BP_TestWeapon` was still on the template's `SKM_Pistol` mesh and is about to be repurposed as the rifle anyway.
- [x] **Configure the close-range full-auto rifle** (full-auto, **projectile/fragmenting**, `Darkness_AssaultRifle`). Done 2026-08-30 via the `unreal-mcp` editor bridge. `BP_TestWeapon` renamed to **`BP_CloseRangeRifle`** (nothing referenced it). New `BP_RifleProjectile` (`ProjectileBase` subclass) created and wired to `ProjectileClass`, keeping the C++ defaults — 3000 u/s (~30 m/s, watchable/dodgeable at its 25m range, which is the whole design premise), no gravity, 5s lifespan, 150-unit fragment burst at 10 damage. Mesh `Darkness_AssaultRifle`, `FireAnimation` `Fire_Rifle_W` (skeleton-matched — this matters, see the FireAnimation note below), `FireSound` `RifleA_Fire01`. Stats: 15 damage, 2500 range, `BaseSpreadAngle 0`, `MaxSpreadAngle 6`, `BloomPerShot 0.08`, `BloomDecayRate 0.5`, `BloomDecayDelay 0.2`, `TimeBetweenShots 0.083`, `IntendedTimeBetweenShots 0.1`, `FireMode Auto`. **Still needs its own arm animations** — currently plays the pistol's `AM_Pistol_Fire` montage since the character's `FireMontage` hasn't been made per-weapon yet.
- [x] **Configure the mid-range battle rifle** (semi-auto, **hitscan**, `Darkness_SniperRifle` tuned down). Done 2026-08-31 (2) via the editor bridge: `BP_BattleRifle` with `Fire_SniperRifle_W`, `SniperRifleA_Fire01`, `P_SniperRifle_MuzzleFlash_Dark`, `MI_Generic_1` decal. 35 damage, 8000 range, `MaxSpreadAngle 4`, `BloomPerShot 0.18`, `TimeBetweenShots 0.2` / `IntendedTimeBetweenShots 0.286`, Semi, zoom at FOV 30. Left animation-driven since mesh and fire animation are the same asset family. **All three weapons are now configured.** One thing to verify: the live instance reported its mesh as `Darkness_AssaultRifle` rather than the sniper mesh that was set.
- [x] **Halo-style scoped zoom** (2026-08-31 (2)). Zoom previously narrowed world FOV only and left the arms unchanged — the deliberate Phase 3 call, since `FirstPersonFieldOfView` is a separate projection and scaling it would distort the near-camera gun. Three options were weighed: hide arms+weapon while scoped (Halo), scale the first-person FOV too, or reposition ADS-style. **Chose hide** — matches the Bungie-era touchstone, avoids the distortion trap, and sidesteps the untuned grip position. New `AProjectBopisCharacter::SetFirstPersonVisibility()` called from `DoAimStart`/`DoAimEnd`, gated on `HasZoom()` going in but restored **unconditionally** on aim-end, so a weapon swap while zoomed can't strand the player with invisible arms. Still missing: a scope overlay widget.
- [x] **Per-weapon animation selection** (2026-08-31 (2)). New `EWeaponAnimType` (Pistol/Rifle) + `AnimType` property and `BlueprintPure GetAnimType()` on `WeaponBase`; the character's single `FireMontage` became `TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> FireMontages`. **Approach chosen from three:** (A) enum + `Blend Poses by Enum` inside the existing state machine, (B) Lyra-style Anim Layer Interface with linked layers, (C) data asset of clips. Picked **A** — one state machine, only leaf clips swap, adding a weapon is an enum value rather than a graph restructure. B is better at ~5+ weapons or when weapons need distinct movesets, and A → B is a clean migration since the enum becomes the layer selector. Consistent with the 2026-08-18 rule: the weapon states its *identity*, the animator owns the clips. Note this forced `Weapons/WeaponBase.h` into the character header — UHT needs the complete enum type for reflection, so a forward declaration won't do. **ABP graph work is user-side and still in progress.**
- [x] **Removed the `bUseAnimationDrivenFeedback` gate from the fire montage** (2026-08-31 (2)). That flag was quietly governing two unrelated things — where the *weapon's* sound and muzzle flash come from, and whether the *character* plays its arms animation — so switching the close-range rifle to code-driven feedback silently killed its arm animation. The montage now plays for any weapon with one mapped, independent of the flag. Narrower than the earlier proposal to split the flag in two, and removes the conflation at source.
- [x] **Muzzle flash rendered through the wrong projection** (2026-08-31 (2)). `SpawnEmitterAttached` returns a particle component that renders in normal world space, while `WeaponMesh` is tagged `FirstPersonPrimitiveType::FirstPerson` — so the flash drew at the gun's *true* world position while the gun drew somewhere else on screen. Fixed by calling `SetFirstPersonPrimitiveType(FirstPerson)` on the spawned component. **May also be the answer to the standing "muzzle flash faces north" bug** — a world-projected effect on an FP-projected gun looks both misplaced and misaligned, which would explain why the Cascade local-space check came up clean. Needs retesting.
- [x] **First/third-person mesh split** (2026-08-31 (2)). `HiddenFirstPersonBones` (`TArray<FName>`, default `head`) on the character, applied in `BeginPlay`. **Corrected mid-implementation:** the first pass removed `GetMesh()->SetOwnerNoSee(true)` and hid the body's upper bones so the owner could see their legs — wrong, because `FirstPersonMesh` is *itself* a full-body `SKM_Manny_Simple` at `(-15, 0, -155)` relative to the camera (standing under it, feet at ground level), so it already provides the legs. Hiding `thigh_l`/`thigh_r` on it would have deleted exactly what was wanted. Final shape: `SetOwnerNoSee(true)` restored, the body-bone array dropped entirely, and only what the camera sits inside is trimmed. Side benefit: no shadow stump, since the body mesh is untouched.
- [x] **Ammo system — Phase A** (2026-08-31 (2)): state, fire gating, dry fire. **Confirmed working in PIE.** Planned as four phases (A state/gating/dry-fire, B reload, C HUD, D pickups). Design decisions: **separate reserves per weapon** rather than a shared pool, **auto-reload off** by default, **reload cancels on swap**. New `EFireResult { Fired, RateLimited, Empty, NoWeapon }` returned by `Fire()` and `FireEquippedWeapon()` in place of `bool`. **Ammo was deliberately not folded into `CanFire()`** — rate-limited and empty need different responses (silent vs. click-and-later-auto-reload), so the enum widens the channel that already existed instead of adding a parallel one. `MagazineSize`/`StartingReserveAmmo`/`MaxReserveAmmo`/`bInfiniteReserve`/`DryFireSound` on `WeaponBase`, initialised in `BeginPlay` rather than the constructor (per-Blueprint defaults aren't applied yet at construction). **Subtle bit:** the dry-fire path resets `TimeSinceLastShot`, or `CanFire()` stays true every frame and a held trigger machine-guns the click. The gate lives in `Fire()` so future AI inherits it, with `bInfiniteReserve` as the opt-out. On-screen `Ammo: <mag> / <reserve>` debug readout added.
- [x] *(Done 2026-10-05 in Phase 4.5, approach (1) — Lyra-style `ik_hand_gun`/`ik_hand_l` + TwoBoneIK, raised only; approach (2) not needed so far. See the spec's* Animation architecture.*)* **BACKLOG — left-hand IK onto the weapon foregrip.** Raised 2026-08-31 (2), deliberately deferred until the weapon work is finished. Symptom: the left hand drifts off the barrel during motion, because without an IK pass it plays whatever the clip says — and the clip assumes the gun is where the animator put it, not where `HandGrip_R` + `GripLocationOffset` actually puts it, with a different mesh pivot per weapon. **The skeleton already has Epic's full IK rig** (`ik_hand_root`, `ik_hand_gun`, `ik_hand_r`, `ik_hand_l`) and the Lyra clips are authored against it, so `ik_hand_l` should already hold good per-pose data — this is AnimGraph work, not new animation, and needs no C++ either way. Two approaches: **(1)** standard Epic setup — `Copy Bone` `hand_r` → `ik_hand_gun` (component space, translation + rotation), then `Two Bone IK` on `hand_l` targeting the `ik_hand_l` bone with a joint target for elbow direction; must sit **after** the montage/`DefaultSlot` node or firing stomps the IK. Won't compensate for a large `GripLocationOffset`, since `ik_hand_gun` tracks the hand rather than the weapon. **(2)** more robust — add a `LeftHandGrip` socket to each weapon mesh and feed *that socket's* world transform into the Two Bone IK effector instead (`EquippedWeapon → WeaponMesh → GetSocketTransform`, all Blueprint-accessible since `WeaponMesh` is `BlueprintReadOnly`). Handles per-weapon mesh/pivot/offset differences properly. **Plan: do (1) first** — a couple of nodes, and it reveals how good the `ik_hand_l` data actually is — then move the effector source to a weapon socket if per-weapon variation is still visible. (1) → (2) only changes what feeds the effector pin, so nothing is wasted. Note this partly overlaps the `GripLocationOffset` tuning item: with (2) the left hand self-corrects, so that tuning becomes purely about where the gun sits in *view*.
- [x] **Ammo Phase B — reload** (2026-08-31 (4)). **Confirmed working in PIE.** `Reload()`/`CancelReload()`/`CanReload()`/`IsReloading()` on `WeaponBase`, timer-driven off `ReloadDuration` rather than animation notifies — a notify would put authoritative timing inside an asset the weapon can't see, and would break for any holder whose montage differs (enemies later). Partial magazines are **kept, not discarded**. `EFireResult::Reloading` added so firing mid-reload is distinguishable and silent. Reload **cancels on weapon swap**, in `EquipWeapon`'s teardown, or the timer fires on a weapon no longer held. `bAutoReloadWhenEmpty` is data on the weapon but acted on by the character, so the montage and the state change stay together. `ReloadMontages` keyed by `AnimType`, mirroring `FireMontages`. Montage only plays if a reload actually started, so mashing the key on a full magazine does nothing. Assets: `IA_Reload` mapped to `R`, `AM_Pistol_Reload` (2.0s) and `AM_Rifle_Reload` (2.2s), `ReloadDuration` matched per weapon.
- [x] **Bloom-driven reticle + per-weapon crosshairs** (2026-08-31 (5)). **Confirmed working in PIE.** Found that the reticle had *never* consumed bloom — `GetCurrentBloom()` existed and was `BlueprintPure`, but `WBP_ReticleWidget`'s graph had three default event nodes with zero connections. Phase 3 was closed on "confirmed visible in PIE" and the expansion step was assumed done; the design doc has always required bloom to drive spread *and* reticle from one number. Replaced the texture crosshair with **procedural materials**, since scaling a bitmap thickens the stroke — with a material the widget never scales, so `Thickness` stays constant in real pixels however far `Radius` grows. Considered and rejected: separate line images moved apart (can't make a growing circle) and nine-slicing (fails on curved edges). Built `M_Reticle` (ring) and `M_Reticle_Corners` (rounded-square corner brackets — a squircle via `lerp(max(|x|,|y|), length(p), Roundness)`, with sides cut away by thresholding `min(|x|,|y|)`, which is only large near corners). New `FCrosshairSettings` USTRUCT on `WeaponBase` (`Material`/`Size`/`MinRadius`/`MaxRadius`/`Thickness`/`Color`) with a matching getter on `UReticleWidget` that returns defaults when nothing is equipped. **Convention: all crosshair materials expose `Radius`, `Thickness`, `Color` by name** — that's what keeps the widget generic rather than knowing which weapon uses which material. The widget swaps the brush only when the material actually changes (see Gotchas), and drives the canvas slot from `Size`.
**Agreed order for the remaining Phase 4 work (2026-08-31 (6)):**
**1. Ammo HUD → 2. Pickups → 3. Weapon switching → 4. everything else**
(ABP locomotion blend, grip position, left-hand IK, the TEMP 5s timer,
muzzle-flash retest). Weapon switching is deliberately after pickups, since
pickups are what make a second carried weapon possible in the first place —
`MaxCarriedWeapons` is already 2 but nothing can fill the second slot.

- [x] **Focus (slow motion; formerly "bullet time", renamed for trademark)** (2026-10-09). Q toggle, world 0.3× with the player slowed too, aim unaffected; real-time meter (kill refill via `AddMeter`, passive regen and infinite switches); HUD meter. Screen effect + audio pitch drop done. See the spec's *Focus*.
- [x] **Per-surface impact effects** (2026-10-09). `UImpactEffectsData` (`DA_ImpactEffects`): Niagara burst + bullet-hole decal per physical surface, with a default fallback; used by hitscan and projectiles; on all six weapons. 24 surface types named in `DefaultEngine.ini`; `NFX_Impact` effect type for culling and pooling. See the spec's *Impact effects*.
- [x] **Exaggerated impacts — pass 1** (2026-10-09). Global `EffectScale` (1.5) + per-surface `Scale`, `ExtraSystems` layers, `Sound` slot, random decal variants with random spin. Open: impact sounds (no assets yet), boosted Niagara copies as layers, bigger in Focus.
- [~] *(2026-10-09: projectile groundwork done — splash opt-in, falloff, point damage, slow-motion-only visibility; .45 + rifle rounds at 9,000 cm/s. Remaining: convert the other weapons.)* **BACKLOG — every weapon fires projectiles; bullets visible only in slow motion** (decided 2026-10-08). `BP_Cal45Bullet` on the duals is the first (decals working). Before converting the rest, `AProjectileBase` needs: fragmentation opt-in (defaults to a 150 cm splash on every hit today), per-bullet speed (default 30 m/s) and ~1 cm collision radius, damage falloff passed from the weapon (shotguns lose it otherwise), and a time-dilation visibility rule (`bShowOnlyInSlowMotion`). Full list in the spec's *Projectile vs hitscan*. Open: hide tracers too?
- [ ] **BACKLOG — switch the project to baked lighting.** *(2026-10-27: folded into item 34, step 3. The target is now Xbox 360 / Max Payne 3 at 60 fps, Steam Deck High 800p, GTX 1650 1080p High.)* Decided 2026-08-31 (6): Halo 1–2 fidelity, baked lighting, minimal dynamic lighting, fun over fidelity. **Deliberately deferred until the test level is being relit**, so the settings change and the bake happen together rather than leaving the project in a half-converted state. Settings and full switching costs are tabled in [TechnicalDesignSpec.md](TechnicalDesignSpec.md)'s Rendering target section — the headline is `r.AllowStaticLighting=False` (UE5 default) meaning nothing can bake lightmaps at all until it's flipped, and that flipping it needs an editor restart. Nanite is a **separate** call, not part of this one. Related gameplay consequence: muzzle flashes and weapon fire should not cast dynamic light under this target — emissive materials and particles carry the read instead.
- [x] *(**Done 2026-10-08:** shared ammo pool per type, `AAmmoPickup`, unlimited carry, number-key slot selection, `AWeaponPickup` with dual unlock — see the spec's* Shared ammo pool *and* Pickups and the backpack*. Weapon switching, item 3 of the agreed order, landed with it.)* *(2026-10-06: **C done** — `WBP_Ammo` shows in the HUD, debug lines deleted. **D in progress** — `EAmmoType` + per-weapon `AmmoType` compiled; next: set types on the weapon BPs, `AAmmoPickup`, pickup BPs per type, place + test. Design in the spec's* Ammo *section.)* **Ammo Phases C–D** — HUD readout (currently only the on-screen debug line) and `AAmmoPickup`. Per-weapon magazine sizes also still unset; all three use the `12/60/120` C++ default. Rough proposal: pistol `12/60/120`, close-range rifle `32/160/320`, battle rifle `18/72/144`.
- [x] **One-handed pistol: right-foot-forward stance + procedural free-arm swing** (2026-10-09). Stance via Mirror nodes on the one-handed Idle-state players; the swing is read from the feet each frame (works for forward, backpedal and strafes). See the spec's *One-handed pistol*.
- [x] **Equip animation on weapon change** (2026-10-08). Lyra equip montages per anim type (+ off-hand for duals), played on every equip; firing blocked until it ends. Gun swaps instantly for now. Open polish: the clip's straight-ahead end pose before lowering. See the spec's *Equip animation*.
- [x] **One-handed single pistol** (2026-10-07). `PistolOneHanded` anim type on `BP_Pistol`; free left arm at the side while raised (`clavicle_l`, local space), eased out for reloads, no lowering snap. Two-handed `Pistol` kept for the high-powered pistol. See the spec's *One-handed pistol*.
- [x] **Heavier gait** (2026-10-07). `LocomotionPlayRate` (0.75) on every locomotion/idle player; Stride Warping (Graph mode) + Leg IK keep the feet planted. See the spec's *Gait*.
- [x] **Procedural recoil** (2026-10-07). Spring-driven kick on spine and forearms (+ the one-handed free arm), stacking under rapid fire where the fire montage only restarts. See the spec's *Procedural recoil*.
- [x] **Dot crosshair** (2026-10-07). `WBP_Reticle` simplified to a static 6 px white dot for every weapon; the bloom-driven reticle graph removed. Bloom still drives accuracy; the per-weapon `FCrosshairSettings` and reticle materials stay unused until the accuracy model is decided. See the spec's *Combat: bloom accuracy model*.
- [x] **Dual spread** (2026-10-07). Duals get their own anim type `Dual` (dual SMGs planned to share it); spread idle + fire for hip-fire/run-and-gun so the left gun clears the head, original poses and montages while aiming (`bDualSpread`, `AimFireMontages`). See the spec's *Dual spread*.
- [x] **Fire-rate cap + full-auto** (2026-08-30 (7)). Two deliberately separate properties on `WeaponBase`: `TimeBetweenShots` (hard mechanical cap, in seconds, enforced by a new `CanFire()` at the top of `Fire()`) and `IntendedTimeBetweenShots` (renamed from `IntendedCadence`, now also in seconds for consistency — the softer accuracy limit that triggers the bloom penalty). **These two must differ**: if the hard cap equals the intended interval, the bloom cadence penalty becomes unreachable dead code. The gap between them is the Reach-style window — you can fire faster than is comfortable and pay in accuracy, but never beyond the mechanical limit. The gate lives in `Fire()` rather than in the character, so every caller (including future AI) inherits it. Full-auto: `FireAction` now also binds `ETriggerEvent::Triggered` → `DoFireHeld()`, which early-returns unless `GetFireMode() == Auto` and otherwise just calls `DoFire()` every frame, letting the rate cap do the pacing — which is why the cap had to land first. The press frame fires both `Started` and `Triggered`; the second is harmlessly rejected by `CanFire()`. **Follow-up bug fixed the same session:** the gate stopped shots but not the animation, so rapid-tapping still *looked* like rapid fire — `AWeaponBase::Fire()` and `UWeaponHolderComponent::FireEquippedWeapon()` now return `bool` and the montage is gated on that, keeping `CanFire()` as the single source of truth rather than duplicating the timing check in the character.
- [x] **Weapon fire animation** (`FireAnimation` on `WeaponBase`, 2026-08-30 (7)). A `UAnimSequence` played on the weapon's *own* mesh via `WeaponMesh->PlayAnimation()` when `bUseAnimationDrivenFeedback` is true. **This does not violate the 2026-08-18 architecture rule** — that rule is about skeleton-specific data for *whoever holds* the weapon; an animation authored against the *weapon's own* skeleton is legitimately the weapon's own data. **Constraint learned the hard way:** mesh and animation must come from the same asset family. `BP_Pistol` only works because its mesh was switched to `Darkness_Pistol`, matching `Fire_Pistol_W`'s skeleton — pointing a SciFiWeapDark `_W` animation at an unrelated mesh does nothing at all.
- [x] **Projectile spawn origin fixed** (2026-08-30 (7)). `FireProjectile` was spawning at `TraceStart` — the deprojected screen point, i.e. the camera — so rounds visibly flew out of the player's face. Now spawns at the `Muzzle` socket and aims at the point the camera-based shot would have hit, so it still converges on the reticle instead of flying parallel to the view (plain muzzle-forward would drift off-crosshair, worst at close range, which is exactly this weapon's engagement distance). Falls back to the mesh origin if the socket doesn't exist, since `MuzzleSocketName` is per-weapon editable. Hitscan deliberately still uses `TraceStart` — that's what makes it land dead-on the crosshair.
- [x] **Muzzle flash always faces north** — *(Closed 2026-10-06: user checked in PIE on the third-person rig — fixed; it went with the first-person render path, as the 2026-08-31 entry above suspected.)* Open bug, deferred to 2026-08-31. Established: it is **not** from our C++ (both weapons have `MuzzleFlash: None` and `bUseAnimationDrivenFeedback: true`, so `SpawnEmitterAttached()` never runs) — the flash comes from an **AnimNotify** inside the SciFiWeapDark fire animation. "Use Local Space" is already enabled on all emitters (user checked), ruling out the usual Cascade explanation. **Next to check:** the notify's own **Attached** checkbox and **Socket Name** — an unattached `PlayParticleEffect` notify spawns at a world location with identity rotation, which matches the symptom exactly. Could not be inspected from the editor bridge (it exposes neither AnimSequence `Notifies` nor ParticleSystem `Emitters`). **Proposed fix if the notify checks out too:** split `bUseAnimationDrivenFeedback` into `bAnimationDrivenSound` and `bAnimationDrivenMuzzleFlash` — one flag currently governs two unrelated things, and the pack's animations drive sound well while its flash notify doesn't suit our rig. Discussed and agreed as the fallback, not yet implemented.
- [x] **Projectile self-collision + spawn origin + impact decals** (2026-08-31). Three related fixes. (1) **Projectiles no longer hit the firer**: an explicit `IgnoredActors` list + public `AddIgnoredActor()` on `AProjectileBase`, ignoring in **both** directions (the earlier one-way `IgnoreActorWhenMoving` was not enough — see Gotchas), called explicitly by `FireProjectile` at spawn rather than inferred from `Instigator`/`Owner`. (2) **Spawn origin moved to the crosshair**: `FireProjectile` now spawns at `TraceStart` — the same origin `FireHitscan` uses — so projectile and hitscan weapons agree exactly on where shots go and the weapon's grip orientation no longer affects trajectory at all. This reverses the 2026-08-30 muzzle-socket change and only became viable once self-collision was solved. (3) **Impact decals on `AProjectileBase`** (`HitDecalMaterial`/`DecalSize`/`DecalLifeSpan`, `Projectile|Impact` category), placed on the projectile rather than the weapon to match how `FragmentRadius`/`FragmentDamage` already live there. Needed a real bug fix to work — `Hit.ImpactPoint` vs `Hit.Location`, see Gotchas.
- [x] *(Deleted 2026-09-30, Phase 4.5 — confirmed it did nothing.)* **Replace the TEMP 5s re-snap timer with a real fix.** **Update 2026-08-31: measured in live PIE and the timer does nothing** — the rifle's world transform is identical before and after it fires (`yaw -71.97` → `-71.80`, within idle sway). So this is now a straight cleanup (delete the timer and its `FTimerHandle`), not a fix that needs replacing. The original mistimed-attach diagnosis is unconfirmed.
- [x] *(Superseded — a first-person problem; grip offsets re-tuned for the body mesh 2026-10-03, Phase 4.5 Step 6.)* **Tune `GripLocationOffset` on the rifle.** The rifle renders far too close to the camera and fills the screen — the weapon origin sits only ~31cm out. Separate knob from `GripRotationOffset`, which is correctly left at zero (see Gotchas — do not "correct" the 72° yaw). The hand pose also still doesn't grip the weapon properly, which is an animation problem offsets won't solve. ~~`UWeaponHolderComponent::BeginPlay` sets a 5-second timer that re-runs `AttachWeaponToHand()`, which is what makes the weapon position correct.~~ **Disproven and removed 2026-09-30.** The timer was deleted and the weapon position measured identical for a whole session, with no change at the five-second mark — it was doing nothing. Grip offsets still need re-tuning from scratch for the third-person body (the old values were fitted to first-person arms at 0.6 scale), but that is a data pass, not a timing bug.

## Phase 4.5 — Third-person conversion ✅ COMPLETE (2026-10-05)

Still open from this phase (deferred): hide the reticle in non-aim (design call); camera shoulder swap.

<details><summary>Done — 61 items (expand)</summary>

> Executed step by step via `TPSConversion_WorkOrder.md` (deleted 2026-10-05 —
> it's in git history) on branch `tps-conversion`. Checkboxes below synced from
> it on 2026-10-05; items resolved differently from how they were written carry
> a note. Open: two design calls (reticle hiding, shoulder swap). Optional
> animation polish carried forward: ~~shotgun per-round reload loop~~ (done
> 2026-10-06, with a pump-action variant and socket-driven left-hand IK), 180° and
> crouched turn-in-place. Current behaviour is documented in
> [TechnicalDesignSpec.md](TechnicalDesignSpec.md) (*Character rig*, *Crouch*,
> *Animation architecture*).

Goal: move the game from first-person to third-person, with **Ghost Recon:
Breakpoint** movement. Scoped 2026-09-25 after an audit of how much
first-person assumption is actually baked into the code — answer: very
little. Three files touch it, and one of them has a single line.

**Sits here deliberately, before enemies.** Phase 5 defines how AI aims,
moves and reads the player; doing that against a rig that's about to change
means doing it twice. The conversion is also cheapest now, while the only
thing animating is the player.

**Scope boundary — this is a camera and rig change, nothing more.** It does
not touch campaign structure, level design, world size, or what kind of game
this is. The structural questions carried forward from the setting change
(linear campaign, mission count, mini-sandbox arenas) stay exactly as open as
they were, and none of them are answered by this phase. An open-world /
GTA-PS2-era rescope was raised and **declined on 2026-09-25** — nothing
below assumes, enables, or leans toward it, and no item here should be read
as a step in that direction. Vehicles remain out of scope and unguaranteed.

**Movement model (GR: Breakpoint).** Two states off the existing `bIsAiming`
flag:
- **Non-aim** — full camera-relative motion. Input is transformed by camera
  yaw; the character *turns to face* where it's going. Camera looks around
  freely without turning the character.
- **Aim** — movement is relative to the aim direction: the character's yaw
  locks to the camera and it **strafes** instead of turning.

The input transform is **identical in both states** — camera-relative either
way. The only thing that changes is whether the character rotates to face
its velocity. That's one pair of mutually exclusive flags, not two movement
systems.

### Camera rig
- [x] Replace the first-person camera setup in `AProjectBopisCharacter`'s constructor (`ProjectBopisCharacter.cpp:26-33`) with a `USpringArmComponent` + `UCameraComponent` on the arm. `bUsePawnControlRotation` moves to the **spring arm**, not the camera. Delete `bEnableFirstPersonFieldOfView`, `bEnableFirstPersonScale`, `FirstPersonFieldOfView`, `FirstPersonScale`.
- [x] Add `Spring Arm` to `PublicDependencyModuleNames`? — **not needed**, `USpringArmComponent` is in `Engine`. No `Build.cs` change for the conversion at all.
- [x] Spring arm defaults: `bEnableCameraLag` / `bEnableCameraRotationLag` for weight, `SocketOffset` for the over-shoulder offset, `ProbeChannel`/`ProbeSize` for wall collision. Values are feel-tuning, do them in the BP not C++.
- [x] Revisit `AProjectBopisCameraManager`'s pitch limits (`-70`/`+80`). Those were picked for a head-mounted camera; a spring arm wants a narrower range or the arm swings through the floor.
- [x] `GetFirstPersonCameraComponent()` accessor renamed (`GetCameraComponent()`) — check Blueprint callers before renaming, the ABP or HUD may bind it.

### Mesh consolidation
- [x] Delete `FirstPersonMesh` entirely (`ProjectBopisCharacter.h:32`, constructor `:39-43`). The stock `ACharacter::GetMesh()` becomes the one visible mesh.
- [x] Delete `HiddenFirstPersonBones` (`:59`) and the `HideBoneByName` loop in `BeginPlay` (`:69-72`) — no camera inside the head any more.
- [x] Delete `SetFirstPersonVisibility()` (`.h:139`, `.cpp:287-304`).
- [x] Remove `GetMesh()->SetOwnerNoSee(true)` and the `FirstPersonPrimitiveType` assignment (`:48-49`).
- [x] Remove `SetFirstPersonPrimitiveType` on the muzzle flash (`Weapons/WeaponBase.cpp:127`) and on the weapon mesh (`Weapons/WeaponHolderComponent.cpp:124`).
- [x] **Expect a pile of bugs to vanish here**, not appear: the stale render-proxy snap, the FirstPerson tagging needed on every spawned particle, and the muzzle flash rendering through the wrong projection were all artefacts of the unified first-person path.

### Movement — the GRB model
- [x] **Rewrite `DoMove`** (`ProjectBopisCharacter.cpp:151-159`). It currently uses `GetActorRightVector()` / `GetActorForwardVector()`, which is only correct in first person where actor facing *is* view facing. Must become control-rotation-derived: take `GetControlRotation()`, zero pitch and roll, build the axes from `FRotationMatrix(YawRotation).GetUnitAxis(EAxis::X)` and `(EAxis::Y)`, and feed those to `AddMovementInput`. **This one change is the whole camera-relative model** and is shared by both states.
- [x] **Non-aim state:** `bOrientRotationToMovement = true` on the movement component, `bUseControllerRotationYaw = false` on the character. Character turns to face travel.
- [x] **Aim state:** `bOrientRotationToMovement = false`, `bUseControllerRotationYaw = true`. Character faces the camera and strafes.
- [x] These two flags are **mutually exclusive** — both true and they fight each other every frame (character snaps to control yaw, then movement tries to rotate it to velocity). Set them as a pair, never independently.
- [x] Consider `bUseControllerDesiredRotation = true` instead of `bUseControllerRotationYaw` for the aim state — it rotates *toward* control rotation at `RotationRate` rather than snapping, which reads better on the transition into aim. Try the hard lock first; it's one flag either way.
- [x] Hang the state switch off the existing `bIsAiming` — it's already set in `DoAimStart`/`DoAimEnd`. A small `ApplyMovementMode(...)` helper called from both keeps the flag pair in one place. **Three states, not two** (2026-09-30): non-aim, aim, and prone-with-animation-authority — see *Combat abilities* in [TechnicalDesignSpec.md](TechnicalDesignSpec.md).
- [x] `RotationRate` (movement component) governs how snappily the character turns to face travel in non-aim. Default `(0, 500, 0)` is twitchy for a tired 40-year-old; tune down.
- [x] `MaxWalkSpeed` drops in the aim state. Two values on the character, applied by the same helper.
- [x] Decide whether **sprint breaks aim** (GRB: it does). If yes, sprint input calls `DoAimEnd` rather than being blocked while aiming. *(No sprint exists yet — revisit if one is added.)*
- [x] **Crouch** (decided in, 2026-09-25). `ACharacter` already implements it — `Crouch()` / `UnCrouch()`, replicated `bIsCrouched`, `CrouchedHalfHeight`, `MaxWalkSpeedCrouched`. No custom state machine needed.
- [x] **`GetCharacterMovement()->NavAgentProps.bCanCrouch = true` is required** or `Crouch()` silently does nothing and `CanCrouch()` returns false with no warning. It is `false` by default. This is the single most common way crouch "doesn't work".
- [x] New `UInputAction` for crouch (`IA_Crouch`) — none exists today. Bind `Started`→`DoCrouchStart`, and `Completed`→`DoCrouchEnd` only if hold-to-crouch wins over toggle. **Recommend toggle** for a tired-protagonist feel and because it frees the key during sustained aiming.
- [x] Crouch is **orthogonal to the aim/non-aim pair** — all four combinations are legal (crouched or standing × aiming or not). Keep `ApplyMovementMode(bAiming)` unaware of crouch; let the movement component own stance and speed.
- [x] Crouched max speed via `MaxWalkSpeedCrouched`. Note this interacts with the aim-state `MaxWalkSpeed` drop — decide whether crouch+aim takes the lower of the two or its own value. *(Moot since 2026-10-05: moving stands the character up.)*
- [x] **Camera behaviour on crouch.** The spring arm is on the capsule, so it follows the half-height change automatically — but UE snaps capsule half-height instantly while the mesh interpolates, which reads as a camera pop. If it's visible, lerp the arm's relative Z rather than letting the capsule drive it directly. Check before fixing; the spring arm's own lag may absorb it.
- [x] Uncrouch must fail gracefully under low ceilings — `ACharacter` handles the overlap test itself, but confirm the character doesn't get stuck crouched with no feedback.

### Aim / ADS
- [x] **`DoAimStart` currently gates everything on `EquippedWeapon->HasZoom()`** (`:265`). In third person, aim is a *stance* every weapon has — only the scope magnification is weapon-specific. Split it: movement mode + camera shoulder-in happen unconditionally; `HasZoom()` keeps gating the FOV change and (later) a scope overlay.
- [x] Replace the FOV-swap zoom with a **camera move**: lerp spring arm `TargetArmLength` and `SocketOffset` between hip and aim values. `bHasZoom`/`ZoomedFOV` on `WeaponBase` still drive magnified optics on top.
- [x] `DoAimEnd` must stay unconditional in restoring state, same reasoning as today — a weapon swap mid-aim can't strand the player in aim stance.

### Weapon attachment
- [x] `AttachWeaponToHand()` (`Weapons/WeaponHolderComponent.cpp:107`) — `GetFirstPersonMesh()` becomes `GetMesh()`.
- [x] **Re-tune `GripLocationOffset` / `GripRotationOffset` per weapon from scratch.** Current values were fitted to the arms rig at first-person scale and are meaningless against the full body. The existing backlog item for rifle grip tuning is superseded by this.
- [x] Delete the **TEMP 5s re-snap timer** (`WeaponHolderComponent.cpp:36-38`, handle at `.h:51`). It was a band-aid for first-person attach timing; re-evaluate the attach on the new rig and it should simply be unnecessary. (Already on the backlog — this is where it dies.)
- [x] Confirm `WeaponAttachSocketName` (`hand_r`) is still right on the body mesh — likely yes, it's the same skeleton family.

### Firing and aim source
- [x] **The real problem of the conversion.** `FireEquippedWeapon()` (`WeaponHolderComponent.cpp:130-161`) deprojects screen centre and fires the shot *from the camera*. Correct in first person, wrong in third: the camera sits behind and off to one side, so a shot fired from the camera ray passes through cover the character is actually standing behind.
- [x] Fix is two-stage: **trace from the camera** to find the aim point, then **fire from the muzzle toward that point**. Camera trace decides *what you hit*; muzzle decides *where the bullet comes from*.
- [x] This finally makes `MuzzleSocketName` load-bearing. Right now projectiles spawn at `TraceStart` and the socket is decorative — verify it's correctly placed on all three `MilitaryWeapSilver` meshes before relying on it.
- [x] Decide the near-field behaviour: when the aim trace hits something closer than the muzzle, or the muzzle is inside geometry. Standard answers are a minimum convergence distance or a muzzle-blocked check that suppresses the shot.
- [x] `CrosshairViewportPositionY` is already `0.5` — no change, but confirm it still reads true once the camera is off-centre.
- [x] Bloom/spread is applied to `SpreadDirection` inside `WeaponBase::Fire` and is unaffected by any of this.

### Animation
- [x] **This is the actual cost of the conversion** — the C++ above is roughly a day; this is weeks.
- [x] `FireMontages` / `ReloadMontages` keyed by `EWeaponAnimType` **survive architecturally unchanged** — the character still owns montages for its own skeleton. Every *asset* in them is replaced with a full-body clip. Update the two `UPROPERTY` comments that say "played on FirstPersonMesh" (`ProjectBopisCharacter.h:46,52`).
- [x] Montages must now play on `GetMesh()`'s anim instance (`:200`, `:233`).
- [x] **Non-aim locomotion:** character always faces travel, so a forward-only set (idle / walk / jog / sprint) covers it. Cheap.
- [x] **Aim locomotion:** needs a full 8-way **strafe blendspace**, since the character moves in directions it isn't facing. This is the expensive half.
- [x] **Aim offset** for pitch — the body must point where the camera points. Not needed in first person, mandatory now.
- [x] **Turn-in-place** for the aim state, or the character skates when you swing the camera while stationary. *(2026-10-05)*
- [x] *(2026-10-05: superseded by design — crouch is a stationary stance, no crouch-walking; crouch idle per weapon built, crouch walk kept only as a low-ceiling fallback. See the spec's* Crouch *section.)* **Crouched locomotion, both states.** Crouch adds a second full set: a crouched forward-only set for non-aim, and a crouched 8-way strafe blendspace for aim. Budget for it — this is the real cost of crouch, and it roughly doubles the strafe authoring rather than adding a single idle pose.
- [x] *(2026-10-05)* Crouch stance must layer with firing and reloading the same way standing does, so the upper/lower split has to be in place before crouched clips are worth wiring.
- [x] No cover animation set is needed (cover declined 2026-09-25) — crouched stances carry the whole "taking cover" read.
- [x] Upper/lower body layering so firing and reloading play over locomotion instead of overriding it.
- [x] The migrated Lyra library under `Content/Characters/Heroes/` already contains strafe sets and aim offsets authored against this skeleton — check what's usable before authoring anything.
- [x] The existing **ABP `Blend Poses by Enum`** backlog item (per-weapon locomotion by `EWeaponAnimType`) folds into this work rather than preceding it.
- [x] **Left-hand IK** (backlog) becomes both more visible and more valuable — the weapon is now on screen constantly at full size. Approach (2) from that item, the per-weapon `LeftHandGrip` socket, is the one to do. *(Done differently 2026-10-05: Lyra-style `ik_hand_gun`/`ik_hand_l` + TwoBoneIK, no per-weapon socket.)*

### HUD
- [x] `UPlayerHUDElementWidget` / `UAmmoWidget` / `UReticleWidget` / `UPlayerHUDWidget` need **no code change** — they walk Character → WeaponHolder → Weapon and never touch the camera.
- [x] Reticle stays bloom-driven and screen-centred, and stays *truthful* provided the camera-trace-then-fire-from-muzzle model above is what ships. Re-verify on the new rig rather than assuming.
- [ ] Consider whether the reticle should hide in non-aim (GRB does). Design call, not a blocker.

### Documentation consequences
- [x] `CLAUDE.md` opening line says "first-person action shooter" — update on landing.
- [x] `Design Document/GameDesignDocument.md` + `.html` describe a first-person game throughout (Overview, Combat, and the "first-person" framing in Scope). Pitch-level rewrite of those references.
- [x] `TechnicalDesignSpec.md`'s **"First-person rig"** section and the **"First-person projection is a separate rendering path"** architecture principle become historical — rewrite as a third-person rig section, keep the old one as a dated note (it explains why a lot of past decisions look the way they do).
- [x] `TechnicalDesignSpec.md` trace-source section documents deprojection-from-camera as the permanent approach; that's now half the story.

### Decided 2026-09-25
- **Crouch: in. Prone: out.** One extra stance, not two. Crouch work is itemised under Movement and Animation above. **Deferred to backlog 2026-09-30, then built 2026-10-03 and redesigned as a stationary stance 2026-10-05** — still in as a decision, but not part of the third-person conversion sequence; it is purely additive and drags a second full strafe blendspace behind it. See Step 4 in `TPSConversion_WorkOrder.md` (deleted 2026-10-05 — in git history).
- **No stick-to-wall cover system.** No cover snapping, no cover-to-cover moves, no lean-from-cover. This follows the action direction's *strong choreography and movement rather than static cover shooting* — the player takes cover by standing behind things, not by entering a cover state.
  - **This is a statement about the player, not about level geometry.** Arenas still want cover to stand behind — sightlines, corners, waist-high obstacles — and Phase 5 enemies may still *use* cover as AI positioning. None of that is blocked by this decision; only a player cover-state mechanic is.
  - Practical consequence: no cover volumes/splines to author, no cover-entry animation set, and the aim-state strafe blendspace stays the whole of the aiming movement vocabulary.

### Open — decide before starting
- [ ] **Camera shoulder swap** (left/right). Cheap once `SocketOffset` is already being lerped. *(Deferred — default: skip for now.)*
- [x] Whether the conversion lands on `main` incrementally or on a branch. *(Branch `tps-conversion`, one commit per step.)* It's a large mechanical change with a clean revert point — a branch is cheap insurance.

---

</details>

## Phase 5 — Enemy archetype foundation
Goal: a minimal, composable enemy so combat can be tested against something
real instead of a static target.

Enemies are **human** as of the 2026-09-13 setting change — criminals,
syndicate muscle, corrupt police, hired shooters. The roster is design-open;
this phase builds the pattern, not the roster.

Note: same caveat as Phase 1 — `ShooterNPC`/`ShooterAIController` are gone
with `Variant_Shooter`, so this is built fresh against the design doc's
archetype-composition idea, not extended from the old classes.

**Build order (user, 2026-10-09):** animation + weapons first, then basic movement, then taking bullets + ragdoll. Enemy shooting is deliberately later. Aswang dropped the same day; the enemy roster is undecided.

- [x] *(Done 2026-10-09.)* **1. Shared character base.** `ABopisCharacterBase` between `ACharacter` and the player: weapon holder, raised/aim/reload state, montage maps and playback, recoil hook. The anim instance and holder cast to the base, so one AnimBP drives player and enemies. Pure refactor; the player must behave identically.
- [x] *(Done 2026-10-09: `BP_EnemyBase`, `Enemy_Test`.)* **2. `AEnemyBase` placed in the level**, holding a weapon, animated by the same AnimBP (idle, raised/lowered, equip).
- [x] *(Done 2026-10-09: test patrol + `bAimAtPlayer` strafe; placeholder until StateTree.)* **3. Basic movement** — AI controller + navmesh; walk/jog to points, face a target (drives the aim offset via control rotation).
- [x] *(Done 2026-10-10.)* **4. Taking bullets + ragdoll** — health, hit reactions, death → ragdoll. Very important (user).
  - [x] *(Done 2026-10-10.)* **4a.** Per-bone hits (capsule ignores bullets), `UHealthComponent`, head ×4; death animation → riddled hit-dance (upper body on physical-animation motors) → Max Payne launch ragdoll; overkill burst → instant ragdoll. See the spec's *Taking bullets and dying*.
  - [x] *(Done 2026-10-10.)* **Riddled break:** 30+ damage within 0.1 s while riddled → straight to ragdoll.
  - [x] *(Done 2026-10-10; built while the user was away, user-confirmed in PIE.)* **4b.** Hit reactions while alive: light physics flinch on every hit (feedback only), stagger on 60 damage within 0.5 s (rooted, reels, directional animation, re-triggerable for stun-lock). See the spec's *Hit reactions while alive*.
  - [x] **4c.** Weapon drop as a pickup, corpse cleanup, Focus refill on kills.
    - [x] *(Done 2026-10-10.)* Corpse limit: `MaxCorpses` 5 on the game mode; the oldest **out-of-view** body is removed (camera cone + line of sight), with its weapons.
    - [x] *(Done 2026-10-10.)* Weapon drop: `AWeaponDrop` tumbles on physics (throw capped at 400 cm/s), settles, becomes `BP_WeaponPickup`. Per-enemy weapons: `StartingWeaponClass` editable on placed actors.
    - [x] *(Done 2026-10-10.)* Focus refill on kills (`KillRefill` 20 when the player is the killer); passive regen turned off on `BP_PlayerCharacter`.
    - [x] *(Done 2026-10-10.)* Floating pickups fixed: settle needs 0.25 s at rest, drops ignore ragdolls, floor snap on becoming a pickup.
- [~] **Shootdodge** (user, 2026-10-10; a player feature, done here because the dodge pack arrived). See the spec's *Shootdodge*.
  - [x] *(Done 2026-10-10.)* 0. Asset prep: compatible skeleton; root motion off; Force Root Lock, Anim First Frame (Ref Pose for the End clips); Right clips fixed by the user.
  - [x] *(Done 2026-10-10.)* 1. Dive: Left Shift, camera-relative 8-way, Focus gate + cost, launch on press (lighter gravity, no air braking), Start from the push-off offset → Loop → Land from the impact offset with a slide → Prone → Getup on first move; per-type play rates.
  - [x] *(Done 2026-10-11.)* 2. In-air: Start/Loop/End directional blend spaces in an AnimBP state machine, keyed on dive direction relative to the body; the body eases toward the aim (no snap); fire freely; free slow motion after take-off, off on landing.
  - [x] *(Done 2026-10-11.)* 3. Prone: `BS_Shootdodge_Aim` (dive direction × aim pitch) after landing only; fire prone; get-up picked from how the body lies now.
  - [x] *(Done 2026-10-11.)* 4. Camera: boom lowered and eased while dodging (height −60, arm 300).
  - [x] *(Done 2026-10-11.)* 4b. No firing during the get-up; no reload in the dive; reload while prone → get up, then reload.
  - [x] *(Done 2026-10-11.)* 5. `FocusMaxBloomMultiplier` on the Focus component: scales bloom during Focus (manual or dive).
  - [x] *(Done 2026-10-11.)* 6. Recoil during the dive and prone: the shootdodge branch got its own copy of the three procedural recoil bones.
  - [x] *(Done 2026-10-11, "ok for now".)* 7. Legs through the floor: the prone pose holds the diagonal and transitions slowly (front: Fwd_Left/Right → Fwd within 10°; back sides: Bwd_Right/Left → Right/Left within 22.5°) with body/spine twist; a mid-swap torso lift (front) and foot IK; physics legs on landing. See the spec's *Step 7*.
  - [x] *(Done 2026-10-12.)* 8. Wind-up: from a held aim only, the first 0.2 s of a Lyra dash (per direction; mirrored left dash for the right) plays before the dive, momentum easing off, actions blocked; the dive itself unchanged. See the spec's *Step 8*.
  - [x] *(Done 2026-10-12.)* 9. Aim correction (pistol and duals; dive + prone): spine_03/05 turned so the muzzle points at the crosshair, self-correcting, capped 70°.
  - [x] *(Done 2026-10-13, "will work for now".)* 10. Capsules: the main capsule shrinks to 35 cm from take-off to get-up (headroom checked before standing); a body-shaped capsule *query* along the dive line keeps the body out of walls (velocity trim + push-out) and is exposed for other systems (`GetBodyShape`). No runtime collision component.
  - [x] *(Done 2026-10-13.)* 11. Sliding off a ledge: falls in the flight pose and lands again (full landing → prone).
  - [x] *(Done 2026-10-12.)* 12. Other weapon types: long guns dive with a layered rifle arm hold, foregrip IK and a chest/arms/head aim split; duals get their own mirrored left-arm hold and left-gun aim; back poses lift the pistols off the hips. See the spec.
- [x] *(Done 2026-10-13.)* **5. Enemy shooting:** sight from the head, the user's accuracy model (grows in sight, drains out of sight, cap and growth scaled by player speed), flattened miss disc sized at the player, bursts, no running dry. Player unkillable meanwhile; TEMP hit/accuracy debug. See the spec's *Enemy shooting*.
  - [ ] Accuracy amendments per player action (user, as development goes).
  - [x] *(Done 2026-10-13.)* Tuning: a hard cap, movement penalty by plain speed, misses sized in cm at the player (distance-independent: cover or constant motion), no player stagger.
  - [x] *(Done 2026-10-13.)* Tuning 2: running straight in/out counts at `RadialSpeedWeight` 0.3; close-range floor (85% within 5 m, gone by 12 m: moving up close gets you killed); dive cap 50% on shots, flight only (prone/get-up are the vulnerability window); `IsEvading()` hook for rolls.
  - [x] *(Done 2026-10-13.)* Tuning 3: no movement cap (moving only slows growth, ×0.33 at full speed); dive cap 25%; landing resets accuracy to 25%; enemies lead projectile shots (`LeadSkill` × shot accuracy).
  - [x] *(Done 2026-10-13, user-confirmed.)* **Shooting v2, the hit-chance model** (replaces the accuracy model; user: free-flowing, movement and dodges first, aiming fine but no camping; ≤6 mooks per fight): (1) per-shot hit roll = base 0.3 × distance × player state, random hit bones (60% torso / 15% arms / 20% legs / 5% head at normal damage on the player), placed near misses, no bloom on enemy shots; (2) camping heat on the player (shared); (3) attack tokens on the game mode (2 at a time, 3 s holds); (4) warning burst + 0.5 s post-hit grace. See the spec's *Enemy shooting v2*.
- [x] *(Done 2026-10-13.)* **Player death:** dive cancelled (mid-dive → ragdoll with its momentum), death slow motion, camera follows the body, look-only input, level reload after 3 real seconds. See the spec's *Player death*.
- [x] *(Done 2026-10-14; user: "plays pretty well".)* **6. Gunman behaviour v1** (user, 2026-10-13: real shootouts to judge feel and difficulty; aggressive mooks, sight + gunfire awareness, user blocks out the space). See the spec's *Gunman behaviour v1*.
  - [x] *(Done 2026-10-13.)* 1. Awareness: AI controller + perception (sight, hearing), unaware → alerted (seen / heard gunfire / hit), alert spreads to nearby allies, player gunfire as noise.
  - [x] *(Done 2026-10-13, user-confirmed.)* 2. StateTree scaffolding: C++ tasks (engage spot, move while shooting, hold, last known position) + `ST_Gunman`; replaces the test aim. *(2026-10-13: compiled; `ST_Gunman` built by the user and checked; behaviour check in shootouts pending.)*
  - [x] *(Done 2026-10-13.)* 2b. Follow-ups from the first shootouts: no x-ray aim (focus only while in sight, then the last known spot); suppressive fire at the last known spot for `SuppressFireDuration` 2 s (0 = trained, holds fire); down after a dive (landing, prone, get-up) builds accuracy at the moving rate.
  - [x] *(Done 2026-10-13, user-confirmed.)* 3. Pushing in: random (user: "we don't want the enemy to be too smart"), 20% per reposition, a spot 2–4.5 m from the player at 450 cm/s, firing on the way. Preferred range stays 6–15 m, tuned per enemy in play.
  - [x] *(Done 2026-10-13, user-confirmed.)* 3b. Hearing after the alert: the player's gunfire moves the last known spot; the enemy covers and searches it (no return fire at a sound), and the search follows each new sighting or sound.
  - [x] *(Done 2026-10-13, user-confirmed.)* 3c. Allies and the line of fire: hold every shot while a live ally's body is in a 20 cm tube from the muzzle to the player; reposition after 1 s blocked (Gunman Check *Line Of Fire Blocked*, Hold → Reposition in `ST_Gunman`); allies don't block sight; `bFriendlyFire` per enemy (the user set it on in `BP_EnemyBase`).
  - [x] *(Done 2026-10-14, user-confirmed.)* 4. Encounters: `AEncounterDirector` wave spawner (6 alive at once, 1–3 s replacements, spawn points ≥12 m away and preferably out of view, random weapon from a pool, spawned alerted).
  - [x] *(Done 2026-10-14, user-confirmed.)* 4b. Roaming when the lead goes cold: the furthest Target Point or a random reachable spot; `ST_Gunman` got the Roam state.
  - [x] *(Done 2026-10-14.)* TEMP shooting debug removed (`bDebugShooting`, `bShowHitsTaken`).
  - [x] *(Done 2026-10-15, compiled; not yet playtested.)* Attack tokens only held while usable (in sight, within `AttackTokenRange` 2500, gun up, not reloading, no ally in the line of fire); nearer enemies take a token from the farthest holder (`AttackTokenStealMargin` 300). User: the holders could be off away from the fight while the two in front couldn't kill you. **Then removed entirely the same day** (user): every enemy in sight can hit; `MaxHitChance` 0.5. User-confirmed: "more fair… forces the player to use all the moves and to keep moving".
  - [x] *(Done 2026-10-16, user: "looks good now".)* Camping climbs to a guaranteed hit (`CampedHitChance` 1.0 at full heat, ~5.5 s standing still).
- [x] *(Done 2026-10-14, user-confirmed.)* **Placeholder health bar:** `UHealthWidget` + the user's `WBP_Health` in `WBP_PlayerHUD`.
- [~] **7. More player moves** (user, 2026-10-14). See the spec's *Dodge roll and the moves around it*.
  - [x] *(Done 2026-10-14, user-confirmed.)* Dodge roll: `URollComponent`, own key (`IA_Roll`), 8-way camera-relative, squares up to the camera first, evasive, no firing, no Focus cost.
  - [x] *(Done 2026-10-14.)* Move-out: movement input from 60% of the roll cuts it short at run speed.
  - [x] *(Done 2026-10-14.)* Auto-reload, Focus ends on reload, prone reload on the floor (AnimBP cached-pose layer, `ProneReloadAlpha`), no torso bend during it. `DropAsClass` for enemy-only weapon variants.
  - [x] *(Done 2026-10-14.)* `EvadeLingerTime` 2 s of evasion after a dive lands or a roll ends.
  - [x] *(Done 2026-10-14.)* Roll Focus: 1 real second of free slow motion from 30% of the roll.
  - [x] *(2026-10-28, "apply and run"; tested, user: "roll works, kneel works, no more ground shots": the kneel is now triggered by letting go of the stick, stays down until the stick, crouch or a roll, and roll and crouch share one button by stick push; spec, *The kneel*.)*
  - [x] *(Done 2026-10-15, compiled; not yet playtested.)* The kneel (Vanquish): hold the roll button past `CrouchOutAfter` → cut into a crouch, held as long as the button is; no camping heat while knelt. Blend tuning is the user's (`CrouchOutAfter`, `CrouchOutBlendTime`).
  - [x] *(Done 2026-10-15, compiled; not yet playtested.)* Quick turn to aim (`AimTurnRate` 1080°/s) instead of the snap; crouched turn-in-place (crouch turn montages, root motion off on their clips).
  - [x] *(Done 2026-10-15, compiled; not yet playtested.)* Dual shootdodge arm spread (`DualDiveSpreadAngle` 20°); Inertialization node after the Shootdodge state machine (sporadic Land → Loop error).
  - [x] *(Done 2026-10-15.)* Kneel on/off (`bPostRollCrouch` now also stops the cut-in); crouch combat stance (weapon up, camera −40, `bCrouchCombatStance`).
  - Dropped: roll hold → prone slide, slide into the kneel, inertial roll-to-kneel blend, held roll Focus.
- [x] *(Done 2026-10-15, compiled; not yet playtested.)* **8. Shooting model → Max Payne 1/2** (user: "those were designed for FPS"). Supersedes Phase 2's bloom model. See the spec's *Combat: the shooting model*.
  - [x] 1. Hold to fire for every weapon at `TimeBetweenShots`; Semi/Auto, `IntendedTimeBetweenShots` and the cadence penalty removed; a held trigger doesn't break into a reload.
  - [x] 2. Spread replaces bloom: `Spread`, `MovingSpreadMultiplier` (not mid-dive), `SustainedSpread` burst wander, `FocusSpreadMultiplier`.
  - [x] 2b. Enemy firing pattern per weapon (`AIFiring`: bursts, interval, pause); `BurstShotsMultiplier` / `BurstPauseMultiplier` on the enemy for harder variants.
  - [x] 3. All seven weapon BPs retuned through the bridge.
  - [x] 4. Docs.
- [x] *(Done 2026-10-16, user-confirmed.)* **9. Feedback and fixes:** shell casings (physics, per-weapon `AmmoEject`, pump on the rack, `CasingScale`); directional hit indicator (red hits, grey near misses from rounds that actually pass, flood-controlled); navmesh reverting (`bForceRebuildOnLoad`); first-dive bug (Start blend space seeded in `NativeInitializeAnimation`); Focus dead on again; fast-gun recoil (montage keeps pace, kick scales).
- [x] *(Done; User-tested 2026-10-25.)* **10. Room encounters** (user, 2026-10-16: "The standard gameplay will be linear and not arena"). See the spec's *Room encounters*.
  - [x] *(Done 2026-10-16, compiled.)* Holding enemies (`bHoldsPosition`, `HoldRadius`; never search or roam), reaction beat on alert, `AEncounterTrigger`.
  - [x] *(Done 2026-10-16.)* Crouched holding (`bCrouchWhileHolding`); test room in `Lvl_Linear` playtested by the user. No cover behaviour (user: no whack-a-mole).
  - Tried and reverted: enemies aiming the gun at each shot's point (planned shots, aim flick, AI pitch override).
  - [x] *(Done 2026-10-17; User-tested 2026-10-25.)* Searching with the gun down: lowered after 4 s out of sight (not holders), head on the last known spot (`neck_01`/`head` look nodes in `ABP_Player`), a reaction beat on raising again.
- [~] **11. Movement and dive feel** (user, 2026-10-17). See the spec's shootdodge *Refinements (2026-10-17)*, *One-handed pistol* and *Dodge roll*.
  - [x] *(Done 2026-10-17, compiled.)* Camping waits only while evading (the kneel no longer stalls it); dive Focus drains as it goes and holds to landing.
  - [x] *(Done 2026-10-17, user: "looking good now".)* Flight limbs on physics: legs firm → loose over the Start, the one-handed pistol's left arm too; the back-dive Start clip edited by the user to open the legs.
  - [x] *(Done 2026-10-17, compiled.)* Free arm on physics with the one-handed pistol raised, on foot.
  - [x] *(Done 2026-10-17, compiled.)* Weapon pickup (or slot switch) mid-roll keeps the roll.
  - [x] *(Done 2026-10-17, compiled.)* Camera height re-applied on capsule resizes (crouch → dive flicker).
  - [x] *(Done 2026-10-17, compiled.)* The Start state on an evaluator driven from C++ (every dive starts at its own offset, the first included); `BackStartOffset`; jog dives jump forward, then turn and ease into the real direction.
  - [x] *(Done 2026-10-23, user: "works".)* Procedural lean into turns while walking/jogging lowered (`UpdateLean`, three spine Modify Bones); enemies too; never raised. See the spec's *Lean into turns*.
  - [x] *(Done 2026-10-23, user: "works".)* Slow motion can be switched off mid-dive with the Focus key or the dive key (`CancelSlowMotion`); the dive carries on at full speed. The old mid-dive "claim" is gone for dives.
  - Dropped: hips on physics; late limb physics at the push-off frame; turn-to-run and the strafe back-dive wind-up; the inertialized locomotion→dive blend; the two-evaluator crossfade.
- [x] *(Done 2026-10-18, user: "works".)* **12. Reload upgrades** (user, 2026-10-17). See the spec's *Reload upgrades* and *Dual pistols in the dive*.
  - [x] Reload carried through a roll: magazine guns at ≥1/3 are reloaded at the roll's end, else cancelled; the shotgun's cycle in progress goes in after the roll.
  - [x] Quick reload mid-dive (3×, auto-reload too, the dive's slow motion kept); quick draw mid-dive (3×, fire as soon as it ends); both shown over the dive pose.
  - [x] The left arm follows mid-dive gun switches (loose for the one-handed pistol, on the grip otherwise).
  - [x] Duals: standing left-gun recoil (node order fixed); mirrored off-hand reload/draw in the air and prone (`OffhandMirror` cache, new dive layer).
  - [x] Crash guard: mesh physics changes wait for the worker-thread animation evaluation.
- [x] *(Done 2026-10-18, user: "looks good".)* **13. Bladed one-handed pistol stance** (user, 2026-10-18). See the spec's *Bladed stance* and *Backsteps*.
  - [x] Mirrored lower body for the strafe (negated direction, so the steps go the right way).
  - [x] Chest turn, head back to target, arm from the shoulder at the aim, hand turn for the barrel; left arm re-authored by the user.
  - [x] Backsteps for any backward strafe, all weapons; the one-handed equip plays its own left arm.
- [x] *(Done 2026-10-19, user-set-up.)* **14. MAC-11 placeholder SMG** (user, 2026-10-18; an Uzi replaces it in production). See the spec's *MAC-11 placeholder*.
  - [x] `BP_MAC11` (one-handed) and `BP_DualMAC11`, SMG ammo, `BP_AmmoPickup_SMG`; mesh, sockets and grip set by the user.
  - [x] Bladed stance limited to the player (enemies aimed left).
  - [ ] Give it to enemies; place pickups.
- [x] *(Done 2026-10-19, user: "works" / "looks ok for now".)* **15. Grenades and the grenade launcher** (user, 2026-10-18): player only (scripted enemy throws later, shootable mid-air), 5 max, throwable mid-dive, slow motion on explosion kills, the existing additive toss animation. See the spec's *Explosives*.
  - [x] 1. Kill slow motion (`PlayKillSlowMotion`).
  - [x] 2. `AExplosion` / `BP_Explosion`.
  - [x] 3. `AGrenade`, thrown and launched rounds.
  - [x] 4. Quick throw on G (turn first, Max Payne 2 arc, additive toss, free arm and blade handled).
  - [x] 5. `BP_GrenadeLauncher` (slot 6, key 6). *(Out of the game since 2026-10-26 — nothing gives it out; kept for later.)*
  - [x] 6. Pickups, HUD grenade count.
- [x] *(Done 2026-10-19.)* **16. Revolver** (.357, two-handed, `HighPowerPistol` ammo, speedloader).
- [x] *(Done 2026-10-19.)* **17. Hand fixes:** left-hand IK for two-handed holds at the hip; hip aim hand turn for two-handed holds; blade turns corrected for the turn-in-place offset; IK keeps the pose's hand rotation.
- [x] *(Done 2026-10-19.)* Enemies no longer suppress blind on alerts they never saw (`bSeenSinceAlert`).
- [x] *(Done 2026-10-20, user-played.)* **18. Encounter triggers for the slice:** waiting enemies, ambush points, chargers, holders, patrollers, spawn-ahead lines; markers, labels, link lines, an Encounter tab in Place Actors, failed-move warnings.
- [x] *(Done 2026-10-21.)* **19. Polish from playtests:** patrol walk (walk/jog blend spaces), guns lowered against walls, body-shaped dive collision, prone reload fixes (flip on a side, forearm reload face-down, long-gun arm raise), silent face-down swaps.
- [x] *(Done 2026-10-21; stage 2 User-tested 2026-10-25.)* **20. Scripted events** (Max Payne overheard conversations). See the spec's *Scripted events*.
  - [x] Stage 1: Say Line, Wait, subtitles, interrupt with a reaction line.
  - [x] Spawned speakers by tag; talking/gesture montages looping for the step.
  - [x] Stage 2: Move To, Face To, Set Off Encounter, Start Event, finished/interrupted chains.
  - [x] *(User-tested 2026-10-25.)* Playtest stage 2.
- [x] *(Done 2026-10-21, user: "functional".)* **21. Enemy barks:** seven types, per-language voice sets, level-wide coordinator. See the spec's *Enemy barks*.
  - [x] *(Done 2026-10-23, user: "works".)* Programmatic variation: a pitch per enemy rolled from the voice's range (0.92–1.08) for every line it says, plus ±3 % pitch / −15 % volume jitter per bark (`UBarkVoice` → Variation). Scripted lines take the pitch, no jitter.
  - [x] *(Done 2026-10-24, user: "pitch spread works".)* **Pitch spread:** `UBarkSubsystem::AssignPitch` gives each new speaker of a voice the emptiest spot in its pitch range (ends, then widest-gap middles, ± `PitchSpreadJitter`), freed at death — no more near-identical pitches. See the spec's *Enemy barks → Pitch spread*.
  - [ ] Polish: mono clips, more lines, tuning, Tagalog set.
- [ ] **22. NPC characters from CharacterCustomizer2** (branch `feature/CC2_Integration`). See the spec's *NPC characters (CC2)*.
  - [x] Analysis, migration (disk copy, 1.6 GB), plugins, compatible skeletons, physics copy, `BP_Enemy_CC` test enemy (builds, clean PIE).
  - [x] `ik_` bones on the male body (user); grip sockets on both bodies.
  - [x] Grips playtested (user: looks ok). Neck seam: head ticks after the body (not yet re-checked).
  - [x] Hero looks (`bUseSavedLook` + `Look`, copy/paste from the creator) + creator level `Lvl_CharacterCreator`.
  - [x] Random rules: `RandomizeLook`, PH preset, role Blueprints Thug/Goon (outfit rows are placeholders for design).
  - [x] Player on CC (`BP_Player_CC`, child of `BP_PlayerCharacter`); apparel pack in the creator.
  - [x] Skin through clothing: head + body depth bias in `M_Skin_CCMH` (user: "close enough", 2026-10-22).
  - [x] Bladed strafe waist twist spread over `spine_01`–`03` (user: "looks better").
  - [x] Clothing layer order at the waist (`Layer Depth` per garment MI, tucked vs untucked; user: "it will do for now"). Male tucks re-checked after the female pass: User-tested 2026-10-25.
  - [x] Corpse physics-asset swap (`RagdollPhysicsAsset`, in `StartRagdoll`) — works, but CC's `CCMH_Body_Physics` is a cloth-collision asset and distorts under our death impulses; rejected, property left empty (2026-10-23). Bodies stay on `PA_CCMH_Bopis` / `PA_CCMH_Player`.
  - [x] *(Done 2026-10-24; clothing layers User-tested 2026-10-25.)* Female characters — **civilians plus one story character** (user, 2026-10-24):
    - [x] `ik_` bones on `CCMH_Body_Female` (user, 2026-10-24; merged into the shared `CCMH_Skeleton`, male untouched).
    - [x] Head (and body) from the preset in `BuildCCCharacter` (enemy + player); verified with a placed female.
    - [x] `CCMH_Preset_PH_Female` + `DT_Outfits_PH_F` (placeholder civilian outfits, design to tune).
    - [x] Clothing layer depth on the female MIs (67, by path).
    - [ ] A civilian Blueprint with female hair/outfit lists, when civilians are designed.
  - [x] *(Done 2026-10-25, user-tested: "clothes fixed".)* Skin seams and orange forearms on bare skin (user, 2026-10-24): the skin's clothing push moved from Pixel Depth Offset to a WPO along the camera ray (PDO was the cause, confirmed by zeroing it; a mask-gated version broke female garments). See the spec's *Skin push by WPO*.
  - [x] *(Done 2026-10-24 by the user.)* CC heads, clothes and hair cast shadows on each other: Self Shadow Only off on `CC_SkelMesh` (the head's shadow had stopped at the head/body seam).
  - [ ] Body proportion sliders under Option B.
  - [ ] Deck perf test — deferred to much later (user, 2026-10-21).
  - [x] *(Done 2026-10-24, user-tested: blood looks right, "misses work".)* Shots on CC people: bodies get the `Blood` physical material (blood burst, no hole; no decals on characters in code), and enemy misses check their own path for allies (mirrored or held). See the spec's *Impact effects → Characters* and *Allies and the line of fire*.
  - [x] Blood on CC people looks right (user, 2026-10-24): system trimmed by the user; BloodChunks1 Local Space off + Distance Field collision (chunks no longer float).
- [x] *(Done 2026-10-23, user: "The rest is my tuning".)* **23. Weapon sound normalization** (user, 2026-10-23: anim-notify shots cut off, code shots loud at any distance, reloads silent). See the spec's *Weapon sounds*.
  - [x] Shared `ATT_Gunshot` / `ATT_WeaponFoley` attenuation; gunshot cues 4 per shooter, stop oldest; the three pistols on one cue.
  - [x] Every shot from code (`PlayWeaponSound`); `EWeaponSound` slots per weapon; `AN_WeaponSound` notify. Slots filled on all 11 weapons; notifies placed on the 7 montages + the shotgun pump (user); gunshot notifies deleted from the 3 fire animations.
  - [x] Listen test: shots + reload/draw sounds play (after an editor restart).
  - [x] Cut-off on consecutive shots: gunshot cues 4 → 8 voices + 0.25 s steal fade; foley inner radius 200 → 500; diagnostic logs removed (2026-10-23).
  - [x] Polish — handed to the user (notify timing, 3× reload bunching, loudness); weapon models to be replaced later, so no asset polish now. Still open later: per-gun dry-fire clicks, cue variants, a Weapons sound class.
- [x] *(Done 2026-10-23, user-tested; level physical materials and AI noise remain as follow-ups below.)* **24. Footsteps** (user, 2026-10-23). See the spec's *Footsteps*.
  - [x] *(Done 2026-10-23, user-tested.)* Plants read off the pose (`UpdateFootsteps`: foot ≥ 5 cm above its ref-pose height, then back within 2 cm — the Lyra `FootPlant_*` names turned out to be sync markers) → `PlayFootstep`: foot trace with physical material, `UFootstepEffectsData` (`DA_FootstepEffects` from Footstep_Casual, 24 surfaces, Default Stone; user re-mapped Concrete→Stone, Tile/Glass→Concrete, wood→Low Wood), gait volumes, `ATT_Footstep`, 2 voices per character; on both base characters + the CC children. Gating verified in the log (none in the air or at a standstill).
  - [ ] Physical materials on level materials (every floor is the Default until then); footstep patches = Visibility-only Blocking Volumes with a Phys Material Override (user has one working).
  - [x] *(Done 2026-10-23, user: "thuds work"; volumes tuned to 3 / 2 / 3.)* Thuds: dive landing (pelvis, body thud), roll tumble (`RollThudAt` 0.2), fall onto the feet (by fall speed, enemies too) — all surface-aware via `PlayThud`; CC's `Landing_Cue` as the body layer.
  - [ ] Later: jog steps as AI noise.
- [x] *(Done 2026-10-24.)* **25. Weapon wheel** (user, 2026-10-23: a wheel to future-proof controllers; number keys stay on PC). See the spec's *Weapon wheel*.
  - [x] *(Done 2026-10-23, compiled; not yet playtested.)* GTA V-style `UWeaponWheelWidget` (code-drawn): six fixed segments by weapon type, counter-clockwise from the top, each showing the type's current weapon at the icon's own proportions on a fat ring; name + `k/n` + ammo in the centre. **Keyboard:** a number key opens it highlighted, more keys move it, the same type steps its weapons, the click equips and closes. **Pad:** hold to open, point, cycle, release. Combat input blocked (movement and camera free) and time slow while open (free Focus). `DisplayName`/`Icon` on weapons (Handcrafted White set).
  - [x] **User:** `IA_WeaponWheel` mapped (Tab + Gamepad Left Shoulder) — pad/held mode.
  - [x] *(Done 2026-10-24: compiled, tree pasted; tested by the user.)* **Look moved to the designer** (user: "I can't design it?"): `UWeaponWheelWidget` is logic only and drives named widgets in `/Game/UI/WBP_WeaponWheel` (`Segment_0..5`, `Icon_0..5`, `Count_0..5`, `NameText`, `AmmoText`), plus `GetSegmentState`/`GetHoveredIndex`/`GetSegmentAngleDegrees` and `OnHoverChanged` for Blueprint. `WBP_WeaponWheel` created (parent `WeaponWheelWidget`) and set as `WeaponWheelClass` on `BP_PlayerCharacter`; wedge texture `/Game/UI/T_WheelSegment`. **User:** paste `Tools/WBP_WeaponWheel_Tree.txt` into its empty Hierarchy (Ctrl+V), compile, save; restart the editor before the PIE test (object-reference gotcha).
  - [x] *(Done 2026-10-24, compiled, tested.)* Icons: **one shared height** (the widest carried icon fits `IconMaxWidth`, cap `IconMaxHeight`), own proportions; **dual-wield shows the icon twice**, the second copy behind the first like a shadow (`IconDual_N`, `DualIconOffset` 10, 8). The first tree had the icons at 35 % opacity (Claude's slip) — the regenerated tree (`Tools/MakeWeaponWheelTree.ps1`) fixes it. **User:** delete `WheelCanvas`, paste, compile, save.
  - [x] *(Built 2026-10-26, "apply and run".)* Icons **as big as fits each wedge** at their own proportions (`FitIconHeight`; replaces the shared height and `IconMaxWidth` / `IconMaxHeight`). Ring numbers `RingInnerRadius` 165, `RingOuterRadius` 295, `SegmentArcDegrees` 56, `IconMargin` 6.
  - [x] *(Built 2026-10-26, "apply and run"; replaces the per-wedge fit, user: "pistols are rendering too big… duals are mushed together".)* One icon height again, set by the handguns: their fit in the pistols' wedge × `HandgunFill` 0.8. Long guns may run past their wedge. Dual stacking scales with the icon (`DualIconSpread` 0.3, 0.25 of the height; then, 2026-10-27, user: "the top left corner of one is the center of the other", 0.5, 0.5 of the icon's own width and height — built, "apply and run").
  - [x] *(Tested 2026-10-27, user: "duals look good, wheel works".)* Handguns sit in their wedge; one height for every icon; duals corner-to-centre.
  - [x] *(Built 2026-10-27, user: "just fix the wheel".)* Right stick points the wheel directly (`StickLookInput` → `SetPointerFromStick`; `StickDeadZone` 0.5, `bFlipStickY` off on `WBP_WeaponWheel` — it came out inverted). *Tested (user): "stick works".*
  - [x] *(User, 2026-10-27.)* Gamepad controls in `IMC_Default` ("I did the control changes").
  - [x] *(Built 2026-10-27, "apply and run".)* Floating drops (the Mossberg and the 1911): `AWeaponDrop` sizes its box from the mesh's own imported bounds, not the physics asset's capsule.
  - [x] *(Tested 2026-10-27, user: "all fine".)* The Mossberg and 1911 drops lie on the floor. A fitted magazine on 1911 drops and pickups: not wanted ("all fine").
  - [x] Playtest the keyboard flow: 1–6 → wheel; same key steps the type; click equips; combat keys dead while up (movement and camera free); time slow. *(Tested by the user 2026-10-24.)*
  - [x] **User (2026-10-24):** `IA_WeaponWheelCycle` mapped in `IMC_Default` — Mouse Wheel Axis, Gamepad D-pad Up, D-pad Down (Negate) (seen in the asset). Cycling: User-tested 2026-10-25.
  - [x] Icons and wheel art: the user's, in the weapon BPs and `WBP_WeaponWheel` (signed off 2026-10-24: "only thing left is map IA_WeaponWheelCycle").
  - [x] *(Compiled 2026-10-24; User-tested 2026-10-25.)* No cheesing the slow motion (user: "they can cheese the game because of the dilation"): the camera holds still and the crosshair hides while the wheel is open; movement still free.
  - [x] *(Compiled 2026-10-24; User-tested 2026-10-25.)* Dying with the wheel open shuts it, and a later click no longer ends the death slow motion early (audit #1).
- [x] *(Done 2026-10-24, user: "sounds work".)* **26. Bullet hit and near-miss sounds** (user, 2026-10-24: "we have the assets, just need the system"). See the spec's *Impact effects → Hit and near-miss sounds*.
  - [x] *(Done 2026-10-24, user-tested.)* Per-surface hit sounds with random variations, headshot sounds, shared `ATT_BulletImpact`; near-miss flybys at the round's closest pass to the player's head (250 cm, one per 0.12 s). All on `DA_ImpactEffects`.
- [ ] **27. Background music** (user, 2026-10-24: "make a bgm system. one that plays background music, and can crossfade in a trigger" — "also does not get affected by time dilation"). See the spec's *Background music*.
  - [x] *(Compiled 2026-10-24.)* C++: `UMusicSubsystem` (one track at a time, equal-power crossfades in real seconds, out of slow motion's pitch drop) and `AMusicTrigger` (a box: the player walks in → crossfade to its track, or out to silence; `bPlayAtStart` for a level's opening music).
  - [ ] Assets: `SC_Music` sound class (a volume knob, like `SC_Barks`) on `/Game/Audio/BGM/DarkCrimes`; Looping checked on the wave.
  - [x] *(User-tested 2026-10-25.)* Test when home: a start trigger in `Lvl_Sandbox`, a second one that fades out (only one track so far); slow motion leaves the music alone.
- [x] *(Done 2026-10-24; User-tested 2026-10-25.)* **28. Level exit** (the slice brief's one required new code; user, 2026-10-24: "Go with exit trigger. Dont drop it on the map, thats a test for later."). See the spec's *Level exit*.
  - [x] *(Compiled 2026-10-24.)* C++: `ALevelExitTrigger` — the player walks in: can't be hurt, input off, slow motion ended, HUD gone, fade to black (music with it), an optional "level complete" widget, then `NextLevel` loads (None: this level restarts). Real seconds throughout.
  - [x] *(User-tested 2026-10-25.)* Test: placed in a level and played.
- [x] *(Done 2026-10-24; User-tested 2026-10-25.)* **29. Room cleared + waves** (user, 2026-10-24: "do the room cleared one, even better if you can set a wave spawning event system"). On `AEncounterTrigger`. See the spec's *Encounter triggers → Room cleared and waves*.
  - [x] *(Compiled 2026-10-24.)* Step 1, room cleared: the trigger counts every enemy it sets off or brings in (delayed spawns too, not ones handed to another trigger); when all are down → `EventsOnCleared`, `TriggersOnCleared`, the `OnCleared` Blueprint event; `IsCleared` / `GetAliveCount`. A room shot clear from the doorway counts.
  - [x] *(Compiled 2026-10-24.)* Step 2, waves: `Waves` after the first `Spawns` — each with its spawns, a start condition (alive at most N, then a delay) and events to start; cleared waits for the last wave; `OnWaveStarted`; link lines.
  - [x] *(User-tested 2026-10-25.)* Test: a room with a wave, then cleared → an event or the next trigger.
- [x] *(Done 2026-10-25, user: "reload works".)* **30. Dual reload holds the torso** (user, 2026-10-25: "This happens when reloading with dual ... I want no movement on lower to middle spine and ... the shoulder on the left dips hard"). See the spec's *Dual reload: torso and off-hand shoulder held*.
  - [x] *(Compiled 2026-10-25, "apply and run".)* `DualReloadHoldAlpha` (C++) and two Layered Blend per Bone holds in `ABP_Player`: pelvis + `spine_01`–`03`, and the off-hand collarbone.
  - [x] *(User-tested 2026-10-25.)* Test: dual reload from behind — no lean, the left shoulder stays up, the left arm clear of the body. Tune: `spine_04` too (filter → `spine_05`), `DualReloadHoldSpeed`.
- [ ] **31. Gunfire audio refactor** (user, 2026-10-25, home test of consecutive shots: "gunfire audio to refactored"). Item 23 raised the gunshot cues to 8 voices with a steal fade; the test still didn't pass. Next: pin down the symptom, then rework the fire-sound path (`AWeaponBase::PlayWeaponSound`, cue concurrency, sound priorities; the mixer's 32-voice ceiling if *all* audio cuts out).
- [ ] **32. Procedural pump + grip curves** (user, 2026-10-25: "lets go procedural" for a more prominent pump; the reload End should pump; "the equip anim ends with the hands not landing on the left grip"). See the spec's *Procedural pump and grip curves*.
  - [x] *(Compiled 2026-10-25, "apply and run".)* C++: `Pump`/`HandGrip` curves in `UProjectBopisAnimInstance`; `AWeaponBase` pump bone/travel/amount; `UWeaponAnimInstance`.
  - [x] *(Bridge, 2026-10-25.)* Both shotguns `Slide_Bone`/8 cm (the semi-auto pumps on reload only). Reload stays the shared `AM_Shotgun_Reload` (a pump-only copy was made and removed).
  - [ ] *(Deferred: `Shotgun_A` is a placeholder.)* With the final shotgun model: its pump bone + travel on both shotgun BPs, and a post-process AnimBP (parent `WeaponAnimInstance`, one Modify Bone on the slide) — user creates the asset, Claude wires it.
  - [x] *(Compiled 2026-10-25, "apply and run".)* No rack after a reload for now (user: "Just dont rack it at all for now"): `bPlayReloadEnd` (character, default off) — the montage ends with the last insert.
  - [ ] User: curves — `Pump` on `MM_PumpShotgun_Fire` (rack); `HandGrip` at the end of `MM_Rifle_Equip`.
  - [ ] Test: the pump fire (the hand rides back), shotgun reloads end after the last shell with no slap, equip lands on the grip (rifle and both shotguns).
- [ ] **33. Final weapon assets** (user, 2026-10-25: "replace the pump shotgun assets, replace the semi-shotgun with a spas-12. Add single and dual berettas (different from the pistol). Replace the mac with micro uzi. Add new Ar-15 model, Add AK74u"). Intake checklist: the spec's *Adding a weapon*.
  - [ ] Design calls (user): which rifle the AR-15 replaces (`BP_CloseRangeRifle` or `BP_BattleRifle`); AK-74u ammo (shared Rifle or its own); whether the .45 and 9mm share Pistol ammo. *(Decided 2026-10-25: the MAC-11 stays — Micro Uzi dropped; the Beretta is one-handed like the .45.)*
  - [ ] Pump shotgun — the Mossberg 500 (`/Game/Mossberg/Mossberg-5001`, material set up 2026-10-25: `MI_Mossberg500`) onto `BP_PumpShotgun`; its slide AnimBP on the `pump` bone (plan item 32's deferred part).
  - [x] **Benelli M4** — replaces `BP_Shotgun` (semi-auto). User, 2026-10-28: "im gonna use a Benelli M4 and an SVD" — replaces the SPAS-12 plan. Its bolt locks open on the last shell.
    - [x] Skeletal mesh (2026-10-30; user: "its all separate parts as well with no skeleton. See if you can build a skeletal mesh yourself"): `ArtSource/Weapons/BenelliM4/RigBenelli.py` + `PackORM.py`; bridge import of `SK_Benelli` (bones `root, bolt, trigger, carrier, shell`), ORM textures, `MI_Benelli_Body/Stock/Shell` on `M_TacticalPistol`. Spec: *Benelli M4*.
    - [x] User: LOD0 reduced to ~8k triangles ("still looks ok"); the side-saddle shells stay.
    - [x] Root moved into the pistol grip (rig script re-run 2026-10-30). No pump (M4 is gas-operated; user's call), so no forend bone.
    - [x] User: reimported, saved, 3 LODs; sockets `MuzzleFlash`, `AmmoEject`, `LeftHandGrip`.
    - [x] `BP_Shotgun` wired (bridge, 2026-10-30, saved): `SK_Benelli` at scale 1.2, single-node mode, `FireAnimation` cleared (sound and flash from code), pump bone cleared, grip (0,0,0) / (−8, 87, 0) as starting values.
    - [x] Left hand like the Mossberg and M4 (bridge, 2026-10-30): `LeftHandGrip` (18.6, −5.5, 7.5) / (−29, 61, 103), converted from the Mossberg's tuned socket; `bLockLeftHandRotation` on.
    - [ ] User test: grip location/rotation in play; the left hand on the forend (calibrate only if it looks off); muzzle flash and casing positions; `MagazineSize` (12 now, real 5–7 + 1).
    - [x] Left hand tested by the user ("works").
    - [x] Animations (2026-10-30): `AnimBenelli.py` → `A_Benelli_Fire`, `A_Benelli_LastShot`, `A_Benelli_Ready` in `/Game/BenelliM4/Animations/` (bridge, saved); `ReadyPose` set on `BP_Shotgun`.
    - [x] User: `Weapon Sound` notifies (`Fire`, `Eject`) on both. Claude (bridge, 2026-10-30, saved): `FireAnimation` = `A_Benelli_Fire`, `LastShotAnimation` = `A_Benelli_LastShot`.
    - [x] User test (2026-10-30: "tested, works").
    - [x] Cleanup (bridge, 2026-10-30): 45 first-import assets deleted (28 static parts, 5 Phong instances, 12 unused textures); no outside referencers. `/Game/BenelliM4/` is 17 assets, 71 MB.
    - [x] Magazine sizes (user, 2026-10-30: "Change pump to 6 shots, M4 to 8"; bridge, saved): `BP_Shotgun` 8, `BP_PumpShotgun` 6.
    - [ ] Open: optional 2K reimport of the six kept 4K textures; the shotgun ammo boxes still give 12 (auto) and 8 (pump).
  - [x] **Gun animation pass** (user, 2026-10-30: "go through the animations I made for the pump, beretta 9mm, 1911 and M4 animations and tweak them? Your anim changes on the Benelli looks more convincing"). Targets: `Mossberg-500_Pump` (0.67 s), `SK_Beretta_92FS_Fire` / `_FireEmpty` (0.23 s), `Anim_P1911_M_Shot` / `_Shot_Empty` (0.75 s), `SK_AR4_Fire` (0.23 s). Spec: *Gun animation pass*.
    - [x] User exports in `ArtSource/Weapons/AnimPass/`. The Beretta, AR4 and Mossberg exports came out static (editor keys don't export), so they're rebuilt; the 1911 keeps the kit's values.
    - [x] `AnimPass.py` → `A_Beretta_Fire/FireEmpty/Ready`, `A_P1911_Fire/FireEmpty`, `A_AR4_Fire`, `A_Mossberg_Fire`; checked by renders; imported (bridge, saved).
    - [x] User: notifies on the Beretta ×2, 1911 ×2 and AR4. Claude (bridge, 2026-10-30, saved): wired onto the 9mm pair (+ `A_Beretta_Ready`), the three 1911 Blueprints and `BP_CloseRangeRifle`.
    - [x] User: `Fire` + `Eject` on `A_Mossberg_Fire`. Claude (bridge, 2026-10-30, saved): `BP_PumpShotgun` wired.
    - [x] User: `Pump` notify on `A_Mossberg_Fire` (saved; bytes show `Fire`, `Pump`, `Eject`).
    - [x] User test (2026-10-30: "tested all, works").
    - [x] Old animations deleted (bridge, 2026-10-30): `Mossberg-500_Pump`, `SK_Beretta_92FS_Fire` / `_FireEmpty` / `_ReadyPose`, `SK_AR4_Fire`, `Anim_P1911_M_Shot_Empty`.
    - [x] `Anim_P1911_M_Shot` + the kit's unused `Anim_P1911_M_Shot_Montage` deleted (2026-10-30: bridge for the shot; the montage's orphaned file removed from disk after the editor's force delete left it).
    - [x] Benelli source `Shotgun+2.fbx` copied into `ArtSource/Weapons/BenelliM4/Source/`.
    - [x] `AR4HatchOpen` cleared from the rifle mesh and deleted (bridge, 2026-10-30): the cover is shut until the first shot. Tested by the user ("tested, works").
    - [x] Uzi: `AnimUzi.py` → `A_Uzi_Fire` (0.05 s, fits the 0.06 s fire rate), imported (bridge, saved).
    - [x] User: `Fire` + `Eject` on `A_Uzi_Fire`. Claude (bridge, 2026-10-30, saved): `BP_Uzi` + `BP_DualUzi` wired; `SK_Uzi_Fire` deleted (no referencers).
    - [x] User test: Uzi bursts ("tested, works").
  - [ ] **SVD** — the sniper; replaces `BP_BattleRifle`'s silver `Sniper_Rifle_A` (user, 2026-10-28). Its bolt locks back on empty, and pulling the charging handle releases it.
  - [x] *(Bridge, 2026-10-25.)* 9mm Pistol (Beretta 92FS) + Dual 9mm Pistols — `BP_Pistol9mm` / `BP_DualPistol9mm`; the old pistol renamed ".45 Pistol" / "Dual .45 Pistols".
  - [ ] 9mm: sockets on `SK_Beretta_92FS` (`MuzzleFlash`, `AmmoEject` — user), grip offsets (PIE), icon, pickup, loadout/enemy pools, LOD reduction.
  - [ ] **Uzi replaces the MAC-11** (user, 2026-10-28: "I want to replace the Mac11 with an Uzi"; this supersedes "I will keep the mac-11"). The model is a rigged CGTrader FBX with separate parts, about 10k vertices and 4K textures. Bring LOD0 to about 5–6k triangles with the LOD reduction, and set the textures' Maximum Texture Size to 1024. The MAC assets stay in the project unused for now ("we can remove stuff much later on"). Assumed: it replaces both the single and dual MAC, plus the enemies who carry it.
    - [x] **Rigged in Blender (2026-10-28).** The "rigged" FBX had no skeleton: 11 loose parts, ~12k triangles. `ArtSource/Weapons/Uzi/RigUzi.py` → `SK_Uzi.fbx` (7 bones since the stock came off, rigid, barrel +X, cm), `SM_Uzi_Mag.fbx` (drop mesh, pivot on `mag`), `SK_Uzi.blend`.
    - [x] Import (bridge, 2026-10-28): `SK_Uzi` (+ `SK_Uzi_Skeleton`, no physics asset), `SM_Uzi_Mag`, ORM → Masks, textures 1024, `MI_Uzi` (child of `M_TacticalPistol`) on both. Saved.
    - [x] Stock removed (user, 2026-10-28): dropped in `RigUzi.py`, reimported. 10,334 source triangles.
    - [x] LODs (user, mesh editor, 2026-10-28): 50% / 33% / 25%, plus **Lock Mesh Edges** on LOD1–2, because the loose shells opened holes. 5,279 / 2,217 / 1,813 vertices, LOD0 ~5.2k triangles. Saved.
    - [x] Sockets (user, 2026-10-28; checked over the bridge): `MuzzleFlash` and `AmmoEject` on `root`, `Magazine` on `mag` at 0. Saved.
    - [x] `BP_Uzi` / `BP_DualUzi` (bridge, 2026-10-28, compiled clean, saved): duplicated from the MACs, `SK_Uzi` at scale 1, `SM_Uzi_Mag`, cross-links, no fire animation, grip rotation (−8, 87, 0), offhand yaw 105 (the mesh is +X, the sockets +Y). Not yet tested in play.
    - [x] *(User, 2026-10-28: "grip tuning done".)* Grip tuning in play.
    - [x] *(User, 2026-10-28.)* Fire animation `SK_Uzi_Fire` (Fire + Eject notifies) on `BP_Uzi` / `BP_DualUzi`. Also: Eject notify on `Mossberg-500_Pump`.
    - [x] *(User, 2026-10-28 17:52.)* Saved for real: the first save skipped the director's file (the bridge's edit didn't dirty it). After the `WeaponPool` entry was re-picked, the file holds `BP_Uzi` and no MAC, and shows in git.
    - [x] Enemy pools (bridge, 2026-10-28; user: "remove any references to the Mac11 on the Enemies and the EncounterManager and replace them with the Uzis"): `Lvl_Sandbox`'s `EncounterDirector` `WeaponPool` `BP_MAC11` → `BP_Uzi` (same slot). It was the only enemy-side reference: no enemy Blueprint, other level, config or source file names a MAC, and `BP_Player_CC` no longer does. Set in the open level; see the unchecked item above.
    - [ ] Pickups, wheel icon.
  - [ ] **Ready pose and lock-back on empty** (user, 2026-10-28: "The default pose of the pistol should be hammer back"; slide back when out of ammo). It sends the slide forward at reload end (a notify can time it later) and leaves the dry-fire click as is.
    - [x] Code (compiled 2026-10-28, "apply and run"); spec: *Ready pose and lock-back on empty*.
    - [x] 1911 wired (bridge, 2026-10-28; compiled, saved): `ReadyPose` = the user's `SK_P1911_ReadyPose`, `LastShotAnimation` = the kit's `Anim_P1911_M_Shot_Empty`, on `BP_Pistol`, `BP_DualPistols`, `BP_Pistol_EnemyOnly`.
    - [x] *(User, 2026-10-28.)* Weapon Sound `Fire` + `Eject` notifies on `Anim_P1911_M_Shot_Empty`.
    - [x] *(Tested 2026-10-28, user: "1911 tested, works".)* Hammer back on draw, lock on the last shot, forward at reload end, duals.
    - [x] 9mm wired (bridge, 2026-10-28; compiled, saved): the user's `SK_Beretta_92FS_ReadyPose` and `SK_Beretta_92FS_FireEmpty` (Fire + Eject notifies) on `BP_Pistol9mm` / `BP_DualPistol9mm`.
    - [x] *(Tested 2026-10-28, user: "9mm tested, works".)* The 9mm, single + dual.
    - [ ] Beretta, then the M4, Benelli M4 and SVD as their models arrive.
    - Code: `ReadyPose` and `LastShotAnimation` on `AWeaponBase`. `ReadyPose` is applied at spawn and when a reload finishes. `LastShotAnimation` plays in place of `FireAnimation` when the rounds left after the shot are fewer than the number of guns (the user's rule for duals: each gun locks on its own last shot). Poses are also set from the round count at equip (0 rounds: both locked; 1 round on a dual: the gun that fires second is locked).
    - Assets (user, per gun): a one-frame ready pose, and a last-shot animation that ends locked back and carries its own Fire and Eject notifies.
    - Guns: the 1911 (and its enemy pistol), the Beretta, the M4 / AR-15 (if the mesh has a bolt bone), the Benelli M4, the SVD.
    - Not needed: the Uzi (closed bolt, no hold-open), the AK-74u, the Mossberg, the revolver, the launcher.
    - Open (user): when the slide goes forward in a reload (at reload end, or on a notify); whether a locked-back gun still plays the dry-fire click.
  - [ ] Replace every gun on a MilitaryWeapSilver mesh (user, 2026-10-25): .45 pair + `BP_Pistol_EnemyOnly` (`Pistols_A` — done 2026-10-26: the 1911), both shotguns (`Shotgun_A`), `BP_CloseRangeRifle` (`Assault_Rifle_A`), `BP_BattleRifle` (`Sniper_Rifle_A`), `BP_GrenadeLauncher`. The 9mm, revolver and MAC meshes aren't silver but borrow its muzzle flashes and sounds.
  - [x] *(Compiled 2026-10-26, "apply and run".)* Weapon feedback standard (user: "It will now always play the Fire animation when firing. If it is none, it will not do it. We replace the notifies with our own ones so it does not double up"): `bUseAnimationDrivenFeedback` removed; `Fire()` plays `FireAnimation` if set (its Weapon Sound notifies make the sounds), else the Fire sound from code; flash always from code. Bridge: `P_Pistol_MuzzleFlash_01` on the .45 pair + `BP_Pistol_EnemyOnly`; `BP_PumpShotgun` → `Mossberg-500_Pump`. Spec: *Adding a weapon*.
  - [ ] User: on `Fire_Shotgun_NoDelay`, `Fire_SniperRifle_W` (`Fire_Pistol_W` dropped 2026-10-26: the .45s moved to the 1911) — delete the flash (particle) notifies, add a Weapon Sound **Fire** notify at the shot; check `Mossberg-500_Pump` has a Fire notify and no flash. Until then those guns fire silently.
  - [ ] Test: every gun — one shot sound, one flash at the muzzle; the Mossberg pumps on fire.
  - [x] *(User, 2026-10-26.)* Mossberg pump: `PumpBoneName` None on `BP_PumpShotgun` (the procedural offset pushed the hand sideways — `grip`'s X isn't along the barrel); `Mossberg-500_Pump` retimed to the body's fire animation. Optional: `LeftHandGrip` onto `pump` so the hand rides it.
  - [x] *(User, 2026-10-26.)* Fire animations with Weapon Sound Fire notifies, wired: 9mm pair (`SK_Beretta_92FS_Fire`), MAC pair (`SK_SMG11_Nostock_Y_Skeleton_Fire`), revolver (`_357Revolver_Fire`; no cylinder turn yet).
  - [x] *(User, 2026-10-26: "set and working".)* M4 ejection hatch: `AR4_HatchOpen` (one frame) as `BP_CloseRangeRifle`'s `WeaponMesh` animation, plus an M4 fire animation. Also the launcher's fire animation.
  - [x] *(Compiled 2026-10-26, "apply and run".)* Casing ejection timed by an **Eject** Weapon Sound notify on the gun's fire animation (found at BeginPlay; replaces `CasingEjectDelay` for that gun).
  - [x] *(User; tested 2026-10-27: "all fine".)* Eject notifies on `Mossberg-500_Pump`, the M4, 9mm and MAC fire animations (not the revolver).
  - [x] *(Compiled 2026-10-26, "apply and run".)* Long guns keep the left-hand IK when lowered (user's lowered idle/jog clips bring the hand near the grip; the IK closes the gap). Two-handed pistol unchanged.
  - [x] *(Compiled 2026-10-26, "apply and run".)* Per-gun left-hand angle: `bLockLeftHandRotation` (weapon) + the `LeftHandGrip` socket's rotation; `Bopis.LeftHandGripCalibrate 1` shows the rotation for the current hand. AnimGraph: Modify Bone `ik_hand_l` + Copy Bone → `hand_l` after `TwoBoneIK_0`; saved.
  - [x] *(User, 2026-10-26.)* Calibrated and locked: `BP_PumpShotgun`, `BP_CloseRangeRifle`. Lock the silver placeholders' replacements as they arrive.
  - [x] *(Tested 2026-10-26, user: "lowered idle and jog is fine now".)* Lowered idle/jog — hand on the grip.
  - [x] *(User, 2026-10-26: "Mossberg hold is ok".)* Mossberg hold.
  - [x] *(Tested 2026-10-30, user: "tested, works... not perfect but serviceable".)* Lying backwards after a shootdodge (and the back diagonals, dive and prone), the left hand couldn't reach `LeftHandGrip`. Fixed with the left-hand slide: `ShootdodgeLeftHandGripLocation` on the dive's left-hand IK, see the spec's *Left-hand slide*. A first try that pulled the gun in put the stock through the head and was removed.
  - [x] *(Compiled 2026-10-26, "apply and run".)* Magazine drops: `PlayWeaponEvent` (Mag Out drops `MagazineMesh` from the `Magazine` socket and hides that bone; Mag In / reload end shows it); magazines capped at 16. Meshes set on the 5.56 rifle, MAC pair, 9mm pair, .45 pair + enemy pistol.
  - [x] *(Tested 2026-10-26, user: "mags drop, works".)* `Magazine` sockets on `SK_AR4` and `SK_Beretta_92FS`.
  - [x] *(User, 2026-10-26: "already added and tested working".)* MAC and .45 sockets. The .45's (`Pistols_A`) was unsaved at 19:03 — moot since the .45s moved to the 1911.
  - [ ] A mag-drop sound (`MagazineImpactSound`), if wanted.
  - [x] *(Compiled 2026-10-26, "apply and run".)* Right-hand grip style: `EWeaponGripStyle` on the weapon; `RightHandGripPoses` map on the anim instance; finger layer (`LayeredBoneBlend_16`) in `ABP_Player`; saved.
  - [x] *(User + bridge, 2026-10-26.)* `StraightStockGripPose` authored; `ABP_Player` Right Hand Grip Poses `StraightStock` → it; `BP_PumpShotgun` Grip Style `Straight Stock`. *Tested (user): "grip works".*
  - [x] *(Superseded 2026-10-26: the .45s moved to the 1911 kit, below.)* .45s: stay on the silver `Pistols_A` (user, 2026-10-25; an M1911 swap was reverted).
  - [x] *(2026-10-26, user: "extract the 1911 pistol model only".)* 1911 kit copied from the 4.27 `Pistol1911AnimSet` project (since deleted by the user) into `Content/Pistol1911_Animation_Kit/`. It has `SK_P1911` and `SK_P1911_M` on one skeleton, with mags, .45 rounds, the gun animations and the shot sound. The arms and template content were left out, and so were the three reload montages: their notify pulls in the kit's framework, and the sequences under them came across anyway.
  - [x] *(Bridge, 2026-10-26, user: "replace the .45s with the 1911".)* `BP_Pistol`, `BP_DualPistols` (both meshes) and `BP_Pistol_EnemyOnly` → `SK_P1911` (the black one — user: "Use the black 1911 model", after a first pass on the blued `SK_P1911_M`), `Anim_P1911_M_Shot`, `pistol1911_mag`. Muzzle and magazine use the kit's `muzzle_socket` and `clipSocket`; grip z −2 → +2.5. The old `/Game/M1911/` (31 assets) was dereferenced and deleted.
  - [x] *(Built 2026-10-26, "apply and run".)* `bShowMagazineMesh`: a gun whose mesh has no magazine (the black 1911) shows `MagazineMesh` fitted at the magazine socket, hidden and shown with the reload. Ticked on the three .45 Blueprints (bridge; compiled, saved). *Tested (user): "mag fitted works".*
  - [x] *(User; tested 2026-10-27: "all fine".)*
    - add an `AmmoEject` socket on `SK_P1911_M_Skeleton` (the slide's ejection port);
    - check that `muzzle_socket` points down the barrel and that the dropped magazine lines up at `clipSocket`;
    - on `Anim_P1911_M_Shot`, swap the PlaySound notify for a Weapon Sound **Fire** (+ **Eject**);
    - tune the grips in PIE (single, dual, enemy).
  - [x] *(Tested 2026-10-27: "all fine".)* One shot sound, flash at the muzzle, slide cycles, casing from the port, the magazine drops (and `mag_c`, the kit's second magazine, doesn't stay in the grip).
  - [x] *(Built 2026-10-26, "apply and run".)* Lowered pistol: `LoweredPistolGripPose` (`ABP_Player`: `MM_Pistol_Idle_Hipfire`) closes the right hand on the gun while a pistol is down. Its lowered clips are unarmed, with an open hand.
  - [x] *(Bridge, 2026-10-26.)* Slots: 4 SMGs, 5 rifles (`BP_CloseRangeRifle`), 6 snipers (`BP_BattleRifle`); the grenade launcher out of the game for now (kept, unobtainable).
  - [x] *(Tested 2026-10-26, user: "grip works, slots work".)* The lowered pistol's right hand grips the gun; keys 4–6 and the wheel's segments.
  - [x] *(Bridge, 2026-10-25.)* "5.56 Assault Rifle" — `BP_CloseRangeRifle` on the FPS pack's M4 (`SK_AR4`), sockets on its muzzle/eject bones. Still: `LeftHandGrip`, grip offsets, and hitscan vs the old projectile round (user's call).
  - [ ] AK-74u — new Blueprint (Rifle anim type).
  - [ ] Pickups, enemy weapon pools, the wheel's icons; old placeholders onto the unused-content list.
- [ ] **34. Fidelity and performance** (user, 2026-10-27: "dropping the fidelity … xbox360 levels of fidelity IE max payne 3 levels … on the Steam Deck"; targets table in the design notes, Part 4; "the 1650 is the real target"; only a Steam Deck to test on). See the spec's *Rendering target*.
  - [~] 1. *(Applied 2026-10-27, "go ahead"; editor restarted, settings confirmed in the log.)* Renderer switch: Lumen, ray/path tracing, virtual shadow maps, Nanite, mesh distance fields off; static lighting on; TAA. Nanite fallout: none (15 simple greybox/unused meshes).
    - [ ] User: `NS_ImpactBlood` → BloodChunks1 → Collision → Collision Type **Depth Buffer** (was Distance Field).
  - [~] 2. *(Built 2026-10-27, "apply and run".)* Scalability: High and Low values (`DefaultScalability.ini`); Deck first-run defaults in `UBopisGameInstance` (High, native 800p, 60 cap, VSync).
    - [ ] User: both suns' Dynamic Shadow Distance (movable) → 4000; editor Engine Scalability → High.
  - [ ] 3. Lighting: lightmap UVs, static/stationary lights, bake `Lvl_Sandbox` and `Lvl_Linear`, reflection captures, capsule shadows.
  - [ ] 4. Content budgets: CC characters, enemy animation budget, ragdoll cap, effects, Nanite/VT audit.
  - [~] 5. Deck build (Windows via Proton), PSO cache, benchmark map, measure; again after 3 and 4. *(2026-10-27: packaging settings in `DefaultGame.ini` — Development, our two maps only; first build done (2.3 GB, `ProjectBopis_Builds/DeckTest/Windows`); it runs (start the real binary `ProjectBopis/Binaries/Win64/ProjectBopis.exe` — the top-level launcher demands the VC++ redistributable under Proton). **First measurement:** mostly 60 fps; GPU 12–20, Game 8–18, Draw 5–18 ms; drops at level start and right after kills. **Trace done 2026-10-27** (spec, *First Deck trace*): volumetric clouds 6.1 ms GPU (+0.85 sky capture) is the main GPU cost; enemy spawns ~8–12 ms on the game thread each; big freezes are level reloads on death; the ragdoll swap is ruled out. Clouds removed and sky light real-time capture off in both levels (bridge + user Ctrl+S, 2026-10-27). Next: repackage and re-measure on the Deck, then spawn pre-warming.
  - Notes (user, 2026-10-27): **no level assets yet** (greybox). The bake is a pipeline test, and GPU is re-measured when art arrives. Fixed GPU costs come down first so art has room. **Character counts:** fights ≤ 6 enemies (`MaxAlive` 6); walk-around sections with interactable civilians ≤ 12 NPCs, never in fights.
  - [x] *(2026-10-27, user + bridge check.)* Far-away CC clothing breaking on the Deck: body LOD4 dropped bones the 4-LOD apparel still used (leader pose). LOD4 removed from `CCMH_Body_Male` / `_Female`. Then body LOD3 removed too (2026-10-27, second Deck run: `Chinos_01`, 3 LODs, broke; bridge check: 3 LODs each, saved; third Deck run, user: "chinos are fixed"). Rule: clothing needs as many LODs as the body; 4 pieces with fewer stay out of NPC outfits (spec, *CC clothing LOD fix*).
  - [x] *(Built 2026-10-27, "apply and run".)* Spawn hitch: `AEncounterDirector` builds the rest of each fight asleep at level load (`MaxReserves` 20) and wakes one per respawn (`AEnemyBase::Sleep` / `Wake`, `BuildEnemy`). Not tested yet.
  - [x] *(Built 2026-10-27, "apply and run"; not tested.)* Trigger reserves: `AEncounterTrigger` builds its Spawns and Waves asleep at level load and wakes them on spawn (second Deck trace: room spawns were the last 34–66 ms hitches in `Lvl_Linear`).
  - [ ] Later: build reserves per arena on approach for multi-arena levels.
  - [x] *(Built 2026-10-27, "apply and run"; not tested.)* Level-start black screen over the warm-up: `AProjectBopisPlayerController`, paused and black until frames run steady (0.5 to 3 s), then a 0.4 s fade-in. Spec: *Level-start black screen*.
  - [ ] A 12-civilian walk-around test scene on the Deck (draw calls, shadows, animation) once that content exists.
  - [x] *(2026-10-27, user: "a clean image 100% render".)* Native resolution forced: `[SystemSettings] r.ScreenPercentage=100` (the benchmark had picked 71% on the Deck). Deck build repackaged.
  - [x] *(2026-10-27, user: "go with FXAA, keep bloom and AO".)* FXAA (`r.AntiAliasingMethod` 1); bloom and SSAO kept; SSR off (`r.ReflectionMethod` 0, captures only). A forward-renderer + MSAA test is a possible later experiment. User: Deck Developer Mode + SteamOS Devkit Client, upload, read `stat unit` at three moments.)*
- [x] **35. Controller soft lock** *(Built 2026-10-27, "apply and run"; tested in the editor, user: "autoaim works". Deck next. `UGamepadAimComponent`. Stick turning in degrees per second with a curve and boost; snap on aim, slowdown and follow at medium, in aiming and hip-fire. Spec: *Controller aiming*.)* (user, 2026-10-27: "add controller soft lock to the things to do"). Aim help for gamepad play (the Deck). Design to agree with the user before building: how strong it is, which targets, and whether it's on in slow motion and shootdodges.
- [ ] Later: archetypes composed from data (harder variants now have the burst/pause multipliers and the hit-chance values to vary).
- [x] **36. First aid (healing)** (user, 2026-10-28: "Healing item, we only have one … heal on tap. Max 3, heals half health"; "just use first aid then. No animation, just a sound cue and momentary white screen"). Spec: *First aid*.
  - [x] C++ (compiled 2026-10-28, "apply and run"): `EAmmoType::FirstAid` (kits live in the ammo pool, like grenades); `UHealthComponent::Heal`; `DoHeal` on a `HealAction` (tap; refused at full health, dead or with the wheel open; works mid-roll and mid-dive since there's no animation); `FirstAidSound` (2D) and a white camera flash; `StartingFirstAidKits`. HUD count on its own `UFirstAidWidget` (compiled 2026-10-28; first put on `UHealthWidget`, moved at the user's call).
  - [x] Setup (bridge, 2026-10-28, saved): `IA_Heal` (copy of `IA_Grenade`); `HealAction` and `MaxAmmoByType` FirstAid = 3 on `BP_PlayerCharacter` and `BP_Player_CC`.
  - [x] Pickup (bridge, 2026-10-28, saved): `BP_FirstAidPickup`, a copy of `BP_AmmoPickup_Grenade`, set to FirstAid with Amount 1 and `SM_FirstAidKit`.
  - [x] User (2026-10-28): `IA_Heal` mapped in `IMC_Default`; `WBP_FirstAid` (parent `FirstAidWidget`) placed in `WBP_PlayerHUD`; `FirstAidSound` set to the engine's `1kSineTonePing` (placeholder until a real cue); `BP_FirstAidPickup`s placed in `Lvl_Linear`.
  - [x] Tested by the user (2026-10-28: "first aid tested, works").
  - [ ] Later: a real heal sound; where kits come from in levels (placed only, or enemy drops too) and the starting count — design call.
- [x] **37. Ammo split** (user, 2026-10-29: "the 9mm pistol and .45 pistol have split ammo"; Uzi → Machine Pistol, a later MP5 → Submachine Gun, "Machine Pistol Ammo and Submachine Gun ammo will split too"; "add ammo for SVD sniper"). Spec: *Ammo split*.
  - [x] C++ ("apply and run", built 2026-10-29): `EAmmoType` `Pistol` → `Pistol45`, `SMG` → `MachinePistol`, new `Pistol9mm` and `SubmachineGun`; defaults `Pistol45`; enum redirect in `DefaultEngine.ini`.
  - [x] Bridge (saved 2026-10-29): 9mm pair → `Pistol9mm`; Uzis, MAC-11s, `BP_AmmoPickup_SMG` → `MachinePistol`; new `BP_AmmoPickup_9mm` (24) and `BP_AmmoPickup_Sniper` (12, one `BP_BattleRifle` magazine); `Pistol9mm` cap 180 on both players. No old names left in the saved files.
  - [x] User test (2026-10-29: "pickups tested, works").
  - [x] Bridge (saved 2026-10-29, user: "do the renames, make the boxes too"): `BP_AmmoPickup_45` and `BP_AmmoPickup_MachinePistol` (renamed, redirectors left); new `BP_AmmoPickup_Rifle` (30), `_AutoShotgun` (12), `_PumpShotgun` (8); AmmoSet meshes on all the new boxes.
  - [ ] Later: the SVD's 10-round magazine (and the Benelli's) when the models arrive; a `SubmachineGun` cap with the MP5; optional *Update Redirector References* on `Pickups/`.
- [x] **38. Gameplay message feed** (user, 2026-10-29: "a general message UI like 'Picked up x ammo', 'Quick Saved' … It has to stack … 5 messages at once"). Spec: *Gameplay message feed*.
  - [x] C++ ("apply and run", built 2026-10-29): `UGameMessageSubsystem` (local player; `ShowGameMessage`, also a Blueprint node; 5 lines, 3 s each, real time); `UGameMessageWidget` (Text Blocks `Message_0`..`Message_4`, fade-out); `AAmmoPickup::PickupMessage` with `{Amount}`.
  - [x] Bridge (saved 2026-10-29): `PickupMessage` on all 10 ammo boxes and `BP_FirstAidPickup` (grenades and kits use plural forms).
  - [x] Merging (built 2026-10-29, "apply and run"; user: "update the number of the existing message instead of pushing another new message"): `ShowCountedGameMessage` adds to a live line with the same pattern and moves it to the newest place; a repeated plain message refreshes its line.
  - [x] User: `WBP_GameMessages` placed in `WBP_PlayerHUD`; ammo-box pickups tested (2026-10-29: "widget made, pickups tested, works").
  - [x] Weapon pickups and drops (built 2026-10-29, "apply and run"): "Picked up {DisplayName}" for a new gun or the dual unlock; the ammo message when already carried. Ammo wording moved to one table in code (`ShowAmmoMessage`), so boxes and guns merge; the per-box `PickupMessage` field was removed.
  - [x] User test (2026-10-29: "weapon pickups tested, works").
  - [ ] Later: save messages once a save system exists.
- [x] **39. Reload speed follows Focus** (user, 2026-10-30: "When on focus, your reload speed is accelerated. When in the middle of the reload and you get off focus, it should go back to normal speed from that frame … should work both ways"). Spec: *Focus reload speed*.
  - [x] C++ ("apply and run", built 2026-10-30): `FocusReloadSpeed` 3; `GetReloadSpeed` / `UpdateReloadSpeed` on the player; `AWeaponBase::SetReloadSpeed` (timer restarted with the remaining time scaled, `ReloadCycleStart` keeps the progress); `ABopisCharacterBase::SetReloadPlayRate`. `bStopFocusOnReload` removed: reloading no longer ends Focus (design change, lore notes + GDD updated).
  - [x] User test (2026-10-30: "tested, works"): Focus on → reload fast; off mid-reload → the rest at normal speed; on mid-reload → speeds up.

## Phase 6 — First playable slice
> **2026-10-16:** the game is **linear, with room encounters** (user; lore PART 4
> settled). The slice is a short linear run of rooms in `Lvl_Linear`, not an
> arena; the items below are to be rewritten against that when this phase starts.
>
> **2026-10-19:** draft brief in [Phase6_SliceBrief.md](Phase6_SliceBrief.md) (six beats,
> encounter table, build order) — awaiting the user's cut.
>
> **2026-10-23:** paper level layout for a **respawning slum arena** (user: a
> layout only, not built in UE5):
> [Design Document/Arena_Slums_Layout.html](../Design%20Document/Arena_Slums_Layout.html).
> 48 × 40 m, half-court + ring lanes + a +4 m gallery, 8 enemy-entrance alleys.

Goal: prove the core combat loop in an actual space, with real weapons and
real enemies. The "linear navigation, nonlinear combat" pillar this phase was
written around is *under reconsideration* since the setting change — the
slice should be built to answer what the John Woo direction needs (movement
over cover, escalating shootouts), and the arena-shape question can be
settled by playing it rather than decided up front.

- [ ] Blockout one small arena with varied sightlines, corners, and cover (per the design doc's Levels section).
- [ ] Place 2+ enemy archetypes and at least one weapon pickup.
- [ ] Playtest question to answer: does the same room genuinely support both a close-range and a long-range approach? (Kept from the old premise — still worth asking, but no longer the only question. Also: does the space push the player to keep moving?)

## Phase 7 — Expand from the slice
Once Phase 6 validates the core loop, branch out: more weapons, more enemy
archetypes, ammo economy tuning, real HUD polish, a first real level. Left
deliberately open/undetailed until there's a working slice to expand from —
planning further than that now would be guessing.

---

## Gotchas learned the hard way

Moved to [TechnicalDesignSpec.md](TechnicalDesignSpec.md) → *Engineering gotchas → Full list*
(2026-10-24), so every gotcha lives in one place. Add new ones there.

## Working agreement
- Tackle one phase (or even a single checklist item) at a time — this file
  is meant to be worked through incrementally, not all at once.
- Check items off here as they land; log anything notable in
  `Documentation/ProgressLog.md` at the end of a session.
- If a step needs a design decision to unblock it (carry limit, which
  weapons get zoom, enemy roster, etc.), flag it rather than guessing —
  that's design-owned per `CLAUDE.md`'s division of labor.

## Changelog

- 2026-10-25 (3) — Home test pass: items 10, 20, 28, 29 ticked; item 25's lock/death/cycling, item 22's clothing layers and item 27's test ticked (27 keeps the `SC_Music` asset open). Item 31 (gunfire audio refactor) added.
- 2026-10-25 (2) — Item 30 (dual reload holds the torso and off-hand shoulder) added, built and ticked (user-tested).
- 2026-10-25 — Item 22: bare-skin seams fixed (skin push moved to WPO) and CC parts shadow each other (Self Shadow Only off); both ticked. Items 27–29 (music, level exit, room cleared + waves) added on 2026-10-24, compiled, not yet tested.
- 2026-10-24 — Groomed: items 23 and 24 closed (signed off 2026-10-23), item 10 left open with a note; finished phases 0–3 and 4.5 collapsed; the gotcha list moved to the spec.
- 2026-10-21 — Phase 5 items 20 (scripted events) and 21 (enemy barks) added and ticked.
- 2026-10-18 (2) — Phase 5 item 13 (bladed one-handed pistol stance) added and ticked.
- 2026-10-18 — Phase 5 item 12 (reload upgrades) added and ticked.
- 2026-10-17 — Phase 5 item 10: searching with the gun down. Item 11 (movement and dive feel) added and ticked.
- 2026-10-16 (2) — Phase 5 items 9 (feedback and fixes) and 10 (room encounters) added; Phase 6 noted as a linear slice.
- 2026-10-16 — Camping to a guaranteed hit, token removal, crouch combat stance, kneel switch; leftovers cleaned up (crosshair code and materials, StateTree stop on death, stale roll comment).
- 2026-10-15 — Phase 5: attack-token fix; health bar; item 7 (more player moves: roll, move-out, auto/prone reload, evasion linger, roll Focus, kneel, aim turn, crouched turns, dual dive spread) and item 8 (Max Payne shooting model, increments 1–4) ticked. Phase 2 marked superseded.
- 2026-10-09 (2) — Bullet time ticked; projectile backlog partly done.
- 2026-10-09 — One-handed stance flip + procedural free-arm swing ticked.
- 2026-10-08 (3) — Equip animation ticked; AnimGraph pin-watch gotcha added.
- 2026-10-08 (2) — Ammo C–D ticked (pickups, shared pool, backpack, weapon switching).
- 2026-10-08 — Backlog: all-projectile weapons with slow-motion-only bullet visibility.
- 2026-10-07 (3) — Dot crosshair ticked.
- 2026-10-07 (2) — Dual spread ticked. New Gotcha: stock additive fire clip's base pose.
- 2026-10-07 — Phase 4: one-handed pistol, heavier gait (stride warping), procedural recoil ticked. Two new Gotchas (Modify Bone optional pins override node settings; bridge can wire in-state nodes it can't create).

- 2026-10-06 — Phase 4 backlog swept (left-hand IK, TEMP timer, rifle grip closed; muzzle-flash-north closed after a PIE check). Shotgun reload loop marked done. Three new Gotchas (montage sections don't blend; new anim-type wiring; sections invisible to the bridge); `bStopAllMontages` gotcha corrected.

- 2026-10-05 (3) — **Phase 4.5 complete**; checkboxes synced from the work order, notes on items resolved differently. **Assets renamed** (older entries keep the old names): `ABP_FirstPersonArms` → `ABP_Player`, `BP_FirstPersonCharacter` → `BP_PlayerCharacter`, `BP_FirstPersonGameMode` → `BP_GameMode`, `BP_FirstPersonPlayerController` → `BP_PlayerController`, `MI_FirstPersonColorway` → `MI_Colorway`, `Lvl_FirstPerson` → `Lvl_Sandbox`; the `Content/FirstPerson/` folder name was kept.

- 2026-10-05 (2) — Crouched-locomotion items closed (superseded by the stationary-crouch design). Three new Gotchas: anim-node pin values vs `Node` settings, unpaired crouch callbacks, reparent variable merging needs exact types.

- 2026-10-05 — Turn-in-place ticked. Three new Gotchas: montage Blueprint-node traps (`bStopAllMontages`, `StopSlotAnimation`, Lyra turn-clip root motion), Rotate Root Bone is local-space, pistol AO base poses.
- 2026-10-04 (2) — Phase 4.5 animation items ticked (aim/non-aim locomotion, aim offset, upper/lower layering, montages on the body mesh). Six new Gotchas: AnimBP bridge limits, array writes, derived-data assets (editor crash), missing AO base poses, asset-registry dropouts, montage slot groups.
- 2026-08-09 — Created, after deciding to remove both template variants and start the gameplay systems from scratch.
- 2026-08-09 — Phase 1 mostly complete: `WeaponBase`, `WeaponHolderComponent` (add/equip/attach/fire), character input wiring, all compiling clean. Only the editor/content-side PIE test remains, to continue next session.
- 2026-08-11 — Phase 0 and Phase 1 fully complete and tested in PIE. Project pushed to GitHub (`github.com/kevinsantiago12/ProjectBopis`, `main` branch). Added and integrated the `SciFiWeapDark` marketplace weapon pack. Phase 2 (bloom) started; first step's code given, not yet compiled.
- 2026-08-12 — Phase 2 (bloom/accuracy) fully complete. Diagnosed and documented a real Live Coding gotcha (data-type changes corrupt Blueprints). Fixed stale `Variant_*` include paths in `ProjectBopis.Build.cs`. Phase 3 (reticle) started — C++ widget foundation done; `CleanFlatIcons` marketplace icon pack added for crosshair art.
- 2026-08-12 — Reticle widget confirmed showing on screen in PIE. Aim input/state tracking added and confirmed compiled. Center-dot visibility code given, not yet compiled.
- 2026-08-12 — Plan restructured: enemies deliberately deferred behind a new Phase 4 ("Weapon content & feel" — sound, muzzle flash, hit decals, one real projectile weapon, arms+body animation, three configured weapons). Enemy archetype foundation and the vertical slice both shifted one phase later (now Phase 5/6).
- 2026-08-17 — Reversed which weapon gets the real projectile: it's now the close-range rifle (electromagnetic coilgun, fragments on impact), not the battle rifle. Reasoning: dodgeable travel time only matters at close range; battle rifle and pistol stay hitscan. See Phase 4 and `GameDesignDocument.md`'s "Weapon tech" section.
- 2026-08-17 — Phase 3 (reticle/aim/zoom) fully complete, including a real bug fix (zoom vs. off-center trace-source disagreement — simplified `CrosshairViewportPositionY` back to true center). Phase 4 fire feedback (sound + muzzle flash) complete; hit-decal code given, not yet compiled. Task list and `Research.md` corrected to match this session's projectile-weapon reversal and phase renumbering, after discovering this file already had same-day edits from a separate/concurrent session — merged rather than overwritten.
- 2026-08-17 — Placeholder hit-impact decal complete (`UWC_Bullet_Holes` pack, `FadeScreenSize` distance-culling fix), plus a toggleable debug trace via console variable (`Weapon.ShowTrace`). Phase 4 now two items in: fire feedback and hit decals both done.
- 2026-08-17 — `AProjectileBase` shell (movement/collision/direct-hit damage) built and compiled. Fragmentation burst code given, not yet compiled. Decal/sound variation arrays discussed and deliberately deferred (task #39).
- 2026-08-18 — `AProjectileBase` fragmentation compiled; closed the long-standing null-`Instigator` gap; forked `WeaponBase` into `FireHitscan`/`FireProjectile` — Phase 4's projectile system is fully wired end to end. Animation plan switched from generic animsets to migrating Lyra Starter Game clips; built a working Idle/Move state machine for the pistol.
- 2026-08-18 — Fire Montage architecture revised before landing: `FireMontage` moved off `WeaponBase` (skeleton-specific data doesn't belong on the weapon) onto the character, which now plays it after checking a new `WeaponBase::UsesAnimationDrivenFeedback()` signal. Establishes the pattern each future animator (including enemy archetypes) should follow. Compiled clean.
- 2026-08-30 — Fixed the pistol hand-grip/position bug (multi-session investigation): root cause was `WeaponHolderComponent::EquipWeapon` setting `FirstPersonPrimitiveType` via direct assignment instead of `SetFirstPersonPrimitiveType()`, leaving a stale render proxy. Two earlier hypotheses (stale Aim Offset blend node, Manny/Quinn retargeting mismatch) both ruled out along the way — see Gotchas and the Phase 4 checklist correction (project doesn't use Quinn). Camera/arms clipping discussed (fix: tune `FirstPersonScale` down from its current no-op `1.0f`) but not yet actioned. ~~The `FirstPersonScale` half of this entry is factually wrong — see the 2026-08-30 (3) audit below.~~
- 2026-08-30 (3) — **Doc-vs-code audit, no code changed.** Reconciled all three docs against the actual working tree before starting weapon configuration. Found: the grip-offset mechanism (`GripLocationOffset`/`GripRotationOffset`) had landed undocumented and partly closes the long-deferred hand-socket issue; the camera/arms attachment hierarchy had been inverted (camera → capsule, arms → camera) with no plan entry describing it; `FirstPersonScale` is `0.6f`, not the `1.0f` the previous entry claimed, so the camera-clipping "next step" was already satisfied before it was written; the `MM_Pistol_Fire_Montage` asset the completed Fire Montage work depends on has been deleted and no montage asset exists in `Content/` at all; a temporary debug readout is still live in `WeaponBase::Tick`; and none of Phase 4 is committed. Corrected the stale Phase 4/5 cross-references in `GameDesignDocument.md`'s backlog and brought the HTML twin back in sync (it was still carrying the pre-reversal claim that the battle rifle is the projectile weapon).
- 2026-08-30 (7) — **Big session.** First use of the `unreal-mcp` editor bridge, which changed the workflow: Blueprints are now created/configured directly instead of via editor-UI walkthroughs (known limits: it cannot reach ParticleSystem `Emitters` or AnimSequence `Notifies`). Weapon-position bug fixed for real — root cause was a **mistimed attach** in `BeginPlay`, not the render-proxy issue fixed earlier the same day; currently papered over by a TEMP 5s re-snap timer that still needs a proper fix. Built the fire-rate cap (`TimeBetweenShots` + `IntendedTimeBetweenShots`, both in seconds, deliberately distinct so the bloom penalty stays reachable) and implemented full-auto on top of it; also fixed the montage playing on rate-capped clicks by making `Fire()`/`FireEquippedWeapon()` return `bool`. Added `FireAnimation` (weapon-own-skeleton animation — does not violate the 2026-08-18 rule). Close-range rifle configured end to end: `BP_TestWeapon` → `BP_CloseRangeRifle`, new `BP_RifleProjectile`, full stat row. Fixed projectiles spawning at the camera instead of the muzzle. **Open bug for tomorrow: muzzle flash always faces north** — traced to an AnimNotify, not our code; "Use Local Space" already ruled out; next check is the notify's Attached/Socket Name, with a `bUseAnimationDrivenFeedback` split as the agreed fallback.
- 2026-08-31 — **Projectile polish.** Fixed projectiles hitting the firer (explicit two-way ignore list; the one-way `IgnoreActorWhenMoving` was insufficient). Moved the projectile spawn origin to the crosshair (`TraceStart`), reverting the muzzle-socket approach — this removes the weapon's grip orientation from trajectory entirely and matches hitscan exactly. Added impact decals to `AProjectileBase`, which needed a real fix: `Hit.ImpactPoint` not `Hit.Location` (swept-sphere hits report the sphere centre, one radius off the surface, so decals only landed on some surfaces). First session using **live PIE measurement** via the editor bridge — which disproved two standing theories: the TEMP 5s re-snap timer does nothing measurable, and "correcting" the weapon's 72° grip yaw is numerically clean but visually wrong. Three new Gotchas recorded.
- 2026-08-31 (2) — **Feature session.** Battle rifle configured, completing all three Phase 4 weapons. Halo-style scoped zoom (hide arms+weapon rather than magnify them). Per-weapon animation selection via a new `EWeaponAnimType` enum + `FireMontages` map on the character — chose the enum/Blend-Poses approach over Lyra-style linked anim layers, with a clean migration path if weapon count grows. Removed the `bUseAnimationDrivenFeedback` gate from the fire montage, which had been silently disabling arm animation for code-driven weapons. Fixed the muzzle flash rendering through the world projection instead of the first-person one (may also explain the standing "faces north" bug). First/third-person mesh split, corrected mid-way once it emerged that `FirstPersonMesh` is itself a full body and already supplies the legs. **Ammo system Phase A complete and tested** — `EFireResult` enum, magazine/reserve state, fire gating, dry fire; separate reserves per weapon, auto-reload off, reload cancels on swap. Three new Gotchas recorded, all about verifying through the editor bridge rather than trusting a read-back.
- 2026-08-31 (5) — **Bloom reticle built for real, plus per-weapon crosshairs.** Discovered the reticle had never consumed bloom despite Phase 3 being closed — the widget graph was empty. Replaced the texture crosshair with two procedural UI materials (`M_Reticle` ring, `M_Reticle_Corners` bracket), chosen because scaling a bitmap thickens the stroke while a material keeps line weight constant as radius grows. Added `FCrosshairSettings` on `WeaponBase` so each weapon carries its own material, size, radius range, thickness and colour, with a shared parameter-name convention keeping the widget generic. Fixed a corner-mask bug where an absolute threshold made the crosshair vanish at idle. Three new Gotchas, including two editor-bridge API details.
- 2026-09-13 — **Setting change.** 2098 sci-fi/cyberpunk → Philippines 2002 noir, John Woo action, authored protagonist. Dated note added at the top; Phases 5–6 reworded (human enemies; arena pillar under reconsideration). No task status changed. Design docs rewritten: `Lore_And_Design_Notes.md` (new canon as PART 1, old gameplay ideas as PART 2 for reconsideration), `GameDesignDocument.md` + `.html` (full rewrite), `TechnicalDesignSpec.md` (implications section, coilgun rationale removed, enemies human, conversation rule reopened), `CLAUDE.md`.
- 2026-09-21 — `SciFiWeapDark` replaced by `MilitaryWeapSilver`. Weapon Blueprints re-pointed to `Pistols_A` / `Assault_Rifle_A` / `Sniper_Rifle_A` and their animations/sounds/FX. Stale sci-fi references cleaned (see ProgressLog).
- 2026-09-25 — **Phase 4.5 added: third-person conversion.** Scoped after an audit found first-person assumptions confined to `ProjectBopisCharacter`, `WeaponHolderComponent::AttachWeaponToHand`, and one line of `WeaponBase`. Movement model specified as Ghost Recon: Breakpoint — camera-relative motion with the character facing travel when not aiming, yaw locked to camera with strafing when aiming. Gunplay inspiration is unchanged (John Woo action direction, free-aim). Placed before Phase 5 so enemy AI isn't built twice against two different player rigs. Added, reverted, then reinstated the same day; the intervening open-world/GTA-PS2 rescope was **declined** and is explicitly out of scope. Not started; several items still open for decision.
