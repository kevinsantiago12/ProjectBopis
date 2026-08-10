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
- [~] After deletion, open the project and confirm it compiles and loads
      `Lvl_FirstPerson` with no missing-asset errors. **Action needed:**
      reload/restart the editor (it was already open when the content was
      deleted externally, so its in-memory state may not reflect the
      deletion yet) and check the Output Log / Content Browser for broken
      references.
- [ ] Confirm the base FirstPerson character/game mode/controller (the ones
      already set as project defaults) still work in Play-In-Editor.

## Phase 1 — Weapon foundation (no bloom yet)
Goal: a single generic weapon the player can fire, hip-fire only, built to
later carry the bloom system.

Note: the original plan assumed extending the template's `ShooterWeapon`
class — that's gone now that `Variant_Shooter` is deleted, so this is a new
class written against the design doc's spec, not a refactor of old code.

- [x] New `WeaponBase` class (data-driven: fire mode, damage, range falloff, zoom flag — no per-weapon custom firing logic). Class shell + tuning properties (`FireMode`, `BaseDamage`, `MaxRange`, `bHasZoom`) compiling clean at `Source/ProjectBopis/Weapons/WeaponBase.h/.cpp`.
- [x] Weapon-holder component on the character with a **configurable** carry capacity (carry-limit is still a design-owned open question — defaults to 2, easily changed). `WeaponHolderComponent` at `Source/ProjectBopis/Weapons/WeaponHolderComponent.h/.cpp`: `AddWeapon`/`EquipWeapon` logic, equipped weapon attached to a hand socket on `FirstPersonMesh` and tagged `FirstPersonPrimitiveType::FirstPerson` so it renders through the same path as the arms. Wired onto `AProjectBopisCharacter` as a `WeaponHolder` member.
- [x] Basic fire implementation (hitscan). `AWeaponBase::Fire()` does a `LineTraceSingleByChannel` out to `MaxRange` and dispatches `UGameplayStatics::ApplyPointDamage` on a hit; `WeaponHolderComponent::FireEquippedWeapon()` sources the trace from the character's first-person camera; `AProjectBopisCharacter::DoFire()` bound to a `FireAction` input. **Note:** damage dispatch is real but currently a no-op gameplay-wise — nothing overrides `TakeDamage`/has a `Health` property yet. That's intentionally deferred to Phase 4 (enemy archetype foundation), which is where something will actually exist to shoot.
- [~] One test weapon data asset, fireable in PIE, no accuracy model yet (flat spread). C++ side done: `StartingWeaponClass` (`TSubclassOf<AWeaponBase>`) on `WeaponHolderComponent`, spawned + added in `BeginPlay` as a stand-in for a real pickup system (not the final weapon-acquisition design). **Remaining — editor/content steps, not yet done:**
  1. Create `IA_Fire` Input Action (Digital/bool), add to the Input Mapping Context already used by `Move`/`Jump`, bound to Left Mouse Button.
  2. On `BP_FirstPersonCharacter`, set `Fire Action` = `IA_Fire`.
  3. Create `BP_TestWeapon` (Blueprint subclass of `WeaponBase`), assign a placeholder mesh.
  4. On `BP_FirstPersonCharacter`'s `WeaponHolder` component, set `Starting Weapon Class` = `BP_TestWeapon`.
  5. Verify `WeaponAttachSocketName` (currently defaults to the unverified guess `"hand_r"`) against the arms skeleton's actual socket name.
  6. Playtest in PIE; optionally add a temporary `UE_LOG` on hit in `Fire()` for visible confirmation since there's no damage feedback yet.

## Phase 2 — Bloom / accuracy system
Goal: the actual accuracy model from the design doc — this is the first
system where "correct" behavior really matters.

- [ ] Bloom struct/component: `BaseSpreadAngle`, `MaxSpreadAngle`, `BloomPerShot`, `BloomDecayRate`, `BloomDecayDelay`, `IntendedCadence`.
- [ ] Live bloom value drives the actual shot cone.
- [ ] Cadence-penalty behavior for precision/semi-auto fire mode.
- [ ] Temporary on-screen debug readout of current bloom (before real UI exists) so it's testable early.

## Phase 3 — Reticle & aim/zoom UI
Goal: player-visible feedback for bloom, aim, and zoom — kept structurally
decoupled from accuracy per the design doc.

- [ ] Reticle widget that expands/contracts with live bloom.
- [ ] Center dot appears on aim state only.
- [ ] Zoom FOV change gated by a per-weapon flag, independent of the generic aim input.
- [ ] Sanity check: confirm in a test build that aiming never changes actual accuracy, only what's drawn.

## Phase 4 — Enemy archetype foundation
Goal: a minimal, composable enemy so combat can be tested against something
real instead of a static target.

Note: same caveat as Phase 1 — `ShooterNPC`/`ShooterAIController` are gone
with `Variant_Shooter`, so this is built fresh against the design doc's
archetype-composition idea, not extended from the old classes.

- [ ] New base synthetic enemy actor.
- [ ] Movement, attack behavior, and battlefield role as separate pieces that combine per archetype, rather than one class with type branches.
- [ ] One working archetype end-to-end (e.g. basic humanoid infantry) using StateTree, as proof of concept for the pattern.
- [ ] Basic spawn/placement so an enemy can exist in a test level.

## Phase 5 — First playable arena (vertical slice)
Goal: prove the "linear navigation, nonlinear combat" pillar in an actual
space, with real weapons and real enemies.

- [ ] Blockout one small arena with varied sightlines, corners, and cover (per the design doc's Levels section).
- [ ] Place 2+ enemy archetypes and at least one weapon pickup.
- [ ] Playtest question to answer: does the same room genuinely support both a close-range and a long-range approach?

## Phase 6 — Expand from the slice
Once Phase 5 validates the core loop, branch out: more weapons, more enemy
archetypes, ammo economy tuning, real HUD polish, a first real level. Left
deliberately open/undetailed until there's a working slice to expand from —
planning further than that now would be guessing.

---

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
