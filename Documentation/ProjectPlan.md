# ProjectBopis — Project Plan

> Ordered, incremental path from the current (mostly-empty) template state to
> a working vertical slice of the core combat loop. Broken into small phases
> so we can work through it bit by bit, one session/item at a time, rather
> than trying to build everything at once. Cross-reference
> `Design Document/GameDesignDocument.md` for the *why* behind each system;
> this file is the *in-what-order*.

Status legend: `[ ]` not started · `[~]` in progress · `[x]` done

---

## Phase 0 — Clear the ground
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

## Phase 1 — Weapon foundation ✅ COMPLETE (2026-08-11)
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

## Phase 2 — Bloom / accuracy system ✅ COMPLETE (2026-08-12)
Goal: the actual accuracy model from the design doc — this is the first
system where "correct" behavior really matters.

- [x] Bloom tuning parameters on `WeaponBase`: `BaseSpreadAngle`, `MaxSpreadAngle`, `BloomPerShot`, `BloomDecayRate`, `BloomDecayDelay`, `IntendedCadence`.
- [x] Live bloom drives the actual shot cone: `CurrentBloom`/`TimeSinceLastShot` runtime state, `FMath::Lerp` between base/max spread, `FMath::VRandCone` for the randomized direction, decay gated by `BloomDecayDelay` in `Tick`. Debug line's visual start point offset 150 units in front of the camera (separate from the real `TraceStart` used for the actual trace) since a line starting at the camera itself is nearly impossible to judge the angle of.
- [x] Cadence-penalty behavior: firing faster than `1/IntendedCadence` adds extra bloom proportional to how early the shot was, on top of the normal per-shot amount.
- [x] Temporary on-screen bloom readout via `GEngine->AddOnScreenDebugMessage`, refreshed every `Tick`.
- **Bug caught by code review, fixed:** `ApplyPointDamage` was reporting the un-deviated `TraceDirection` instead of the actual fired `SpreadDirection` — harmless today (nothing consumes the damage direction yet) but fixed for correctness.
- **Also fixed along the way:** `ProjectBopis.Build.cs` still listed include paths for the long-deleted `Variant_Horror`/`Variant_Shooter` `Source/` folders (leftover from Phase 0, never cleaned up) — was producing UBT warnings on every build. Trimmed to just `"ProjectBopis"`.

## Phase 3 — Reticle & aim/zoom UI ✅ COMPLETE (2026-08-17)
Goal: player-visible feedback for bloom, aim, and zoom — kept structurally
decoupled from accuracy per the design doc.

- [x] **Reticle widget foundation.** `UReticleWidget` (`Source/ProjectBopis/UI/ReticleWidget.h/.cpp`), a `UUserWidget` subclass exposing `GetCurrentBloom()` (`BlueprintPure`, chains Character → `WeaponHolder` → `EquippedWeapon` → `GetCurrentBloom()`, defensively returns `0.0f` if any link is null). `WBP_Reticle` created at `Content/UI/` (parent `ReticleWidget`), Image widget showing `icon_line_aim_8` from the `CleanFlatIcons` marketplace pack (`Content/CleanFlatIcons/`, ~17,800 files, left untouched in its own folder — same rule as `SciFiWeapDark`; one harmless leftover `FlatIcon_PNG_PSD.zip` sitting in that folder, safe to delete whenever). Added `ReticleWidgetClass` (`TSubclassOf<UReticleWidget>`) + a new `BeginPlay` override on `AProjectBopisCharacter` that `CreateWidget`s + `AddToViewport`s it for the locally controlled player. **Confirmed visible and working in PIE.**
- [x] **Aim input and state tracking.** New `AimAction` input, bound to both `ETriggerEvent::Started` (`DoAimStart`) and `ETriggerEvent::Completed` (`DoAimEnd`) — unlike `Fire`'s one-shot press, aiming is a held state, so it needs both edges. Simple `bool bIsAiming` + public `IsAiming()` getter on the character. Compiled clean, reviewed, correct.
- [x] **Zoom FOV gated per-weapon on aim.** `WeaponBase::HasZoom()`/`GetZoomedFOV()` getters + a `ZoomedFOV` tuning property. `DoAimStart` sets the camera's real `FieldOfView` (not `FirstPersonFieldOfView`, which is a separate property only governing the arms/weapon-mesh rendering pass — zoom should narrow what you see of the *world*, not distort the gun's own proportions) to the equipped weapon's `ZoomedFOV` if it has zoom; `DoAimEnd` unconditionally resets to a `DefaultFOV` cached once in `BeginPlay` (outside the reticle-widget `if` block — the two are unrelated, an early draft nearly coupled them, which would've left `DefaultFOV` stuck at `0.0f` whenever `ReticleWidgetClass` was unset).
- [x] **Sanity check.** Confirmed by construction, not just by testing: `WeaponBase::Fire()` has no code path that reads `bIsAiming`/`IsAiming()` at all — bloom/spread and aim state are fully separate systems that never cross. One real bug found and fixed along the way: `WeaponHolderComponent::CrosshairViewportPositionY` (the Halo-accurate "2/3 down the viewport" trace-source point from Phase 1) doesn't work once zoom is involved — `FieldOfView` always narrows around the camera's true optical center (50%), so an off-center aim point and zoom permanently disagreed on where "center" was, making zoomed shots land somewhere other than where the view visually centered. Fixed by simplifying `CrosshairViewportPositionY`'s default back to `0.5f` (true center) for both hip-fire and zoom, dropping the authentic Halo offset for now rather than building dynamic per-state repositioning — deliberate scope call, not an oversight.

**Dropped from this phase (2026-08-13):** "center dot visible while aiming" — never actually typed in, no revert needed. Reconsidered: the dot should instead be a **headshot-enabled marker** (Halo-style precision indicator), not an aim-state indicator. That needs a real target with a distinguishable head bone and a precision-damage system to check against (`HitResult.BoneName` from the existing trace can detect this once something exists to hit) — deferred until Phase 5 (enemies), not part of Phase 3.

**Known issue, deferred, not yet fixed:** the equipped pistol isn't correctly positioned/offset relative to the hand socket — likely `WeaponAttachSocketName` or a missing relative transform on the weapon mesh. Flagged 2026-08-12, not yet investigated.

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
- [~] **Placeholder hit-impact decal.** `HitDecalMaterial` (`UMaterialInterface`), `DecalSize`, `DecalLifeSpan` on `WeaponBase`; `Fire()`'s hit block restructured so decals spawn on *any* surface hit (`bHit`), not just hits with a valid damageable actor (`HitResult.GetActor()` — the old, narrower condition, which would've silently skipped decals on plain level geometry). Uses `HitResult.ImpactNormal.Rotation()` to orient the decal flush against whatever it hit. **Code given 2026-08-17, not yet typed/compiled** — resume here. Decal source: user imported `Content/UWC_Bullet_Holes/` (~564 files, real per-surface decal materials — Concrete/Bricks/Asphalt/Glass/Flesh/Fabric/Cracks/Generic/etc.); `Instances/Decals/Generic/MI_Generic_1` is the placeholder pick (no surface detection yet, deliberately). A different pack, `Content/ImpactsVFXVol1/` (Niagara-based surface-reactive *particle* impacts, paired with `UPhysicalMaterial` assets per surface), was imported by accident while looking for decals — kept, deferred to its own task rather than discarded, see the task list.
- [ ] `AProjectileBase` — a real projectile actor (movement + collision + on-hit damage, fragmenting on impact), for the **close-range rifle** specifically. **Reversed 2026-08-17** from the original call below — the pistol and battle rifle stay hitscan; the close-range rifle is the one real projectile weapon. Reasoning flipped: dodgeable travel time only matters at close range, where an enemy would otherwise have zero reaction window against an instant hit — at the battle rifle's mid-range engagement distance, perceptible travel time would just read as an aiming penalty. In-world justification is electromagnetic (coilgun), not plasma: muzzle velocity scales with coil-stage count/barrel length, so the compact close-range weapon is physically slower than the longer-barreled battle rifle. The round is saboted/pre-scored to fragment on impact, trading penetration for a shrapnel burst, so "slower" doesn't read as "weaker" — strong against close/grouped/exposed targets, weak against armor/hard cover, which is where the hitscan pistol and battle rifle stay relevant. Full writeup in `Design Document/GameDesignDocument.md`'s "Weapon tech" section. ~~The pistol and close-range rifle stay hitscan (matches how Halo's own BR/AR/Pistol actually work); the battle rifle is the one real projectile weapon, chosen because its mid-range/semi-auto/deliberate-shot identity is exactly where perceptible travel time reads as a feature rather than a liability.~~
- [ ] Fork `WeaponBase` to support firing a projectile instead of a hitscan trace, per-weapon.
- [ ] POV arms animation setup (idle/walk/fire/reload) for `FirstPersonMesh`, using `PistolAnimset`/`RifleAnimset` (not yet imported — user will add when this step is reached). **Scope note (revised 2026-08-12):** originally planned to also animate the third-person `Mesh` (body — how other actors would see the player) now, for future spectate/co-op. Walked back — that's deferred until spectate/co-op is actually being built, not done preemptively. `FirstPersonMesh`/`Mesh` stay architecturally separate as always (see Phase 0/1 notes above), just not both wired up yet.
- [ ] Configure `BP_Pistol` (semi-auto, hitscan, `Darkness_Pistol`).
- [ ] Configure the close-range full-auto rifle (full-auto, **projectile/fragmenting**, `Darkness_AssaultRifle` — reusing/renaming the existing `BP_TestWeapon`).
- [ ] Configure the mid-range battle rifle (semi-auto, **hitscan**, `Darkness_SniperRifle` assets tuned down).

## Phase 5 — Enemy archetype foundation
Goal: a minimal, composable enemy so combat can be tested against something
real instead of a static target.

Note: same caveat as Phase 1 — `ShooterNPC`/`ShooterAIController` are gone
with `Variant_Shooter`, so this is built fresh against the design doc's
archetype-composition idea, not extended from the old classes.

- [ ] New base synthetic enemy actor.
- [ ] Movement, attack behavior, and battlefield role as separate pieces that combine per archetype, rather than one class with type branches.
- [ ] One working archetype end-to-end (e.g. basic humanoid infantry) using StateTree, as proof of concept for the pattern.
- [ ] Basic spawn/placement so an enemy can exist in a test level.

## Phase 6 — First playable arena (vertical slice)
Goal: prove the "linear navigation, nonlinear combat" pillar in an actual
space, with real weapons and real enemies.

- [ ] Blockout one small arena with varied sightlines, corners, and cover (per the design doc's Levels section).
- [ ] Place 2+ enemy archetypes and at least one weapon pickup.
- [ ] Playtest question to answer: does the same room genuinely support both a close-range and a long-range approach?

## Phase 7 — Expand from the slice
Once Phase 6 validates the core loop, branch out: more weapons, more enemy
archetypes, ammo economy tuning, real HUD polish, a first real level. Left
deliberately open/undetailed until there's a working slice to expand from —
planning further than that now would be guessing.

---

## Gotchas learned the hard way
- **Live Coding cannot handle a member's *type* changing** (e.g. `WeaponMesh` going from `UStaticMeshComponent` to `USkeletalMeshComponent`). It'll report success but corrupt any Blueprint referencing that class — the class becomes unusable as a parent, and Blueprints built on it detach from it (confirmed 2026-08-12 via the engine's own log: `"Live coding succeeded, data type changes may cause packaging to fail if assets reference the new or updated data types"`). Fix requires a full Rebuild Solution (not another Live Coding patch) plus manually re-parenting any Blueprint that got detached. Rule: any change to an existing member's *type* (not just adding new members, or changing a default value) gets a full editor restart + rebuild, not Live Coding.

## Working agreement
- Tackle one phase (or even a single checklist item) at a time — this file
  is meant to be worked through incrementally, not all at once.
- Check items off here as they land; log anything notable in
  `Documentation/ProgressLog.md` at the end of a session.
- If a step needs a design decision to unblock it (carry limit, which
  weapons get zoom, enemy roster, etc.), flag it rather than guessing —
  that's design-owned per `CLAUDE.md`'s division of labor.

## Changelog
- 2026-08-09 — Created, after deciding to remove both template variants and start the gameplay systems from scratch.
- 2026-08-09 — Phase 1 mostly complete: `WeaponBase`, `WeaponHolderComponent` (add/equip/attach/fire), character input wiring, all compiling clean. Only the editor/content-side PIE test remains, to continue next session.
- 2026-08-11 — Phase 0 and Phase 1 fully complete and tested in PIE. Project pushed to GitHub (`github.com/kevinsantiago12/ProjectBopis`, `main` branch). Added and integrated the `SciFiWeapDark` marketplace weapon pack. Phase 2 (bloom) started; first step's code given, not yet compiled.
- 2026-08-12 — Phase 2 (bloom/accuracy) fully complete. Diagnosed and documented a real Live Coding gotcha (data-type changes corrupt Blueprints). Fixed stale `Variant_*` include paths in `ProjectBopis.Build.cs`. Phase 3 (reticle) started — C++ widget foundation done; `CleanFlatIcons` marketplace icon pack added for crosshair art.
- 2026-08-12 — Reticle widget confirmed showing on screen in PIE. Aim input/state tracking added and confirmed compiled. Center-dot visibility code given, not yet compiled.
- 2026-08-12 — Plan restructured: enemies deliberately deferred behind a new Phase 4 ("Weapon content & feel" — sound, muzzle flash, hit decals, one real projectile weapon, arms+body animation, three configured weapons). Enemy archetype foundation and the vertical slice both shifted one phase later (now Phase 5/6).
- 2026-08-17 — Reversed which weapon gets the real projectile: it's now the close-range rifle (electromagnetic coilgun, fragments on impact), not the battle rifle. Reasoning: dodgeable travel time only matters at close range; battle rifle and pistol stay hitscan. See Phase 4 and `GameDesignDocument.md`'s "Weapon tech" section.
- 2026-08-17 — Phase 3 (reticle/aim/zoom) fully complete, including a real bug fix (zoom vs. off-center trace-source disagreement — simplified `CrosshairViewportPositionY` back to true center). Phase 4 fire feedback (sound + muzzle flash) complete; hit-decal code given, not yet compiled. Task list and `Research.md` corrected to match this session's projectile-weapon reversal and phase renumbering, after discovering this file already had same-day edits from a separate/concurrent session — merged rather than overwritten.
