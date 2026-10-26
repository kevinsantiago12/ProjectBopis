# ProjectBopis — Technical Design Spec

> The implementation-facing translation of the design. Split out of
> `Design Document/GameDesignDocument.md` on 2026-08-31, when that document
> was rewritten as a non-technical pitch piece. Everything here is jargon,
> parameters, and architecture — the *why* in plain English lives in the
> design document, and the *in-what-order* lives in
> [ProjectPlan.md](ProjectPlan.md).
>
> Three documents, three jobs:
> - **GameDesignDocument.md** — what the game is, for humans who don't read code.
> - **TechnicalDesignSpec.md** (this file) — what that asks of the codebase.
> - **ProjectPlan.md** — the ordered build sequence, worked one item at a time.
> - **ProgressLog.md** — dated session history and decisions.

---

## Contents

- [Setting change 2026-09-13 — implications](#setting-change-2026-09-13--implications)
- [Combat: the shooting model — Max Payne 1/2 (2026-10-15)](#combat-the-shooting-model--max-payne-12-2026-10-15)
  - [Firing — hold the trigger (increment 1)](#firing--hold-the-trigger-increment-1)
  - [Accuracy — spread (increment 2)](#accuracy--spread-increment-2)
  - [Enemy firing pattern — per weapon (increment 2b)](#enemy-firing-pattern--per-weapon-increment-2b)
  - [Configured values (2026-10-15, written through the bridge)](#configured-values-2026-10-15-written-through-the-bridge)
  - [Ammo values](#ammo-values)
  - [Trace source — two-stage (rewritten 2026-10-03)](#trace-source--two-stage-rewritten-2026-10-03)
  - [Weapon raised vs lowered — hip-fire (2026-10-04)](#weapon-raised-vs-lowered--hip-fire-2026-10-04)
  - [Crouch — a stationary stance (2026-10-05)](#crouch--a-stationary-stance-2026-10-05)
  - [Muzzle obstruction](#muzzle-obstruction)
- [Rendering target](#rendering-target)
  - [Current state vs. target](#current-state-vs-target)
  - [What switching actually costs](#what-switching-actually-costs)
  - [Implications for gameplay work](#implications-for-gameplay-work)
- [Weapons: data, not code](#weapons-data-not-code)
  - [Projectile vs hitscan](#projectile-vs-hitscan)
  - [Impact effects — per surface (2026-10-09)](#impact-effects--per-surface-2026-10-09)
  - [Weapon sounds (2026-10-23)](#weapon-sounds-2026-10-23)
  - [Footsteps (2026-10-23)](#footsteps-2026-10-23)
  - [Weapon wheel (2026-10-23)](#weapon-wheel-2026-10-23)
  - [Adding a weapon — intake checklist (2026-10-25)](#adding-a-weapon--intake-checklist-2026-10-25)
- [Ammo](#ammo)
  - [Shared ammo pool (2026-10-08)](#shared-ammo-pool-2026-10-08)
  - [Pickups and the backpack (2026-10-08)](#pickups-and-the-backpack-2026-10-08)
  - [Equip animation (2026-10-08)](#equip-animation-2026-10-08)
  - [Fire result](#fire-result)
  - [Reload](#reload)
  - [Directional hit indicator (2026-10-16)](#directional-hit-indicator-2026-10-16)
  - [Shell casings (2026-10-16)](#shell-casings-2026-10-16)
  - [Pellets and damage falloff (2026-10-03)](#pellets-and-damage-falloff-2026-10-03)
- [Explosives (2026-10-19)](#explosives-2026-10-19)
- [Encounter triggers, ambushes and spawning (2026-10-19)](#encounter-triggers-ambushes-and-spawning-2026-10-19)
- [Background music (2026-10-24)](#background-music-2026-10-24)
- [Level exit (2026-10-24)](#level-exit-2026-10-24)
- [NPC characters (CC2)](#npc-characters-cc2)
- [Enemies](#enemies)
  - [Built so far (2026-10-09) — steps 1–3, user-confirmed in PIE](#built-so-far-2026-10-09--steps-13-user-confirmed-in-pie)
  - [Taking bullets and dying — step 4a (2026-10-09/10, user-confirmed in PIE)](#taking-bullets-and-dying--step-4a-2026-10-0910-user-confirmed-in-pie)
  - [Hit reactions while alive — step 4b (2026-10-10, built while the user was away; user-confirmed in PIE)](#hit-reactions-while-alive--step-4b-2026-10-10-built-while-the-user-was-away-user-confirmed-in-pie)
  - [Corpse limit — step 4c, part 1 (2026-10-10, user-confirmed in PIE)](#corpse-limit--step-4c-part-1-2026-10-10-user-confirmed-in-pie)
  - [Weapon drop — step 4c, part 2 (2026-10-10, user-confirmed in PIE)](#weapon-drop--step-4c-part-2-2026-10-10-user-confirmed-in-pie)
  - [Focus refill on kills — step 4c, part 3 (2026-10-10)](#focus-refill-on-kills--step-4c-part-3-2026-10-10)
  - [Enemy shooting — step 5 (2026-10-13, user-confirmed in PIE)](#enemy-shooting--step-5-2026-10-13-user-confirmed-in-pie)
  - [Player death — Phase 5 (2026-10-13, user-confirmed in PIE)](#player-death--phase-5-2026-10-13-user-confirmed-in-pie)
  - [Enemy shooting v2 — the hit-chance model (2026-10-13, user-confirmed in PIE)](#enemy-shooting-v2--the-hit-chance-model-2026-10-13-user-confirmed-in-pie)
  - [Gunman behaviour v1 — work order (2026-10-13, done 2026-10-14)](#gunman-behaviour-v1--work-order-2026-10-13-done-2026-10-14)
  - [Room encounters — holding enemies (2026-10-16)](#room-encounters--holding-enemies-2026-10-16)
  - [Searching with the gun down (2026-10-17)](#searching-with-the-gun-down-2026-10-17)
  - [Three families](#three-families)
  - [What the design buys us](#what-the-design-buys-us)
  - [Two-layer health — required, not cosmetic](#two-layer-health--required-not-cosmetic)
  - [Vocalization system](#vocalization-system)
  - [Readability layers by distance](#readability-layers-by-distance)
- [Animation architecture (AnimBP) — 2026-10-04, logic moved to C++ 2026-10-05](#animation-architecture-animbp--2026-10-04-logic-moved-to-c-2026-10-05)
  - [Logic — UProjectBopisAnimInstance (C++, 2026-10-05)](#logic--uprojectbopisaniminstance-c-2026-10-05)
  - [AnimGraph (top level, in evaluation order)](#animgraph-top-level-in-evaluation-order)
  - [Left-hand IK history (2026-10-06)](#left-hand-ik-history-2026-10-06)
  - [One-handed pistol (2026-10-07)](#one-handed-pistol-2026-10-07)
  - [Lean into turns (2026-10-23)](#lean-into-turns-2026-10-23)
  - [Gait — slower cadence with stride warping (2026-10-07)](#gait--slower-cadence-with-stride-warping-2026-10-07)
  - [Procedural recoil (2026-10-07)](#procedural-recoil-2026-10-07)
  - [Turn-in-place (2026-10-05)](#turn-in-place-2026-10-05)
  - [Slots](#slots)
  - [Sync groups](#sync-groups)
  - [Decided against](#decided-against)
  - [Open](#open)
- [Combat abilities — dual-wield, shootdodge, Focus (slow motion)](#combat-abilities--dual-wield-shootdodge-focus-slow-motion)
  - [Dual pistols — built 2026-10-04 (demo)](#dual-pistols--built-2026-10-04-demo)
  - [Dual spread (2026-10-07)](#dual-spread-2026-10-07)
  - [Dual pistols in the dive: off-hand montages and recoil (2026-10-18, user-confirmed)](#dual-pistols-in-the-dive-off-hand-montages-and-recoil-2026-10-18-user-confirmed)
  - [Shootdodge](#shootdodge)
  - [Dodge roll and the moves around it (2026-10-14 / 15)](#dodge-roll-and-the-moves-around-it-2026-10-14--15)
  - [Prone as a transient state](#prone-as-a-transient-state)
  - [Focus (slow motion) — built 2026-10-09](#focus-slow-motion--built-2026-10-09)
- [Levels](#levels)
- [Narrative](#narrative)
- [Architecture principles](#architecture-principles)
  - [Animation feedback data belongs to the animator, not the weapon](#animation-feedback-data-belongs-to-the-animator-not-the-weapon)
  - [Render-affecting properties need their setters](#render-affecting-properties-need-their-setters)
  - [First-person projection is a separate rendering path — *historical*](#first-person-projection-is-a-separate-rendering-path--historical)
- [Character rig (third person, 2026-09-30 →)](#character-rig-third-person-2026-09-30-)
  - [Historical: the first-person rig (2026-08-30 → 2026-09-30)](#historical-the-first-person-rig-2026-08-30--2026-09-30)
- [Current state](#current-state)
  - [Vendor content](#vendor-content)
- [Build tooling](#build-tooling)
- [Engineering gotchas](#engineering-gotchas)
  - [Full list (from ProjectPlan.md, 2026-10-24)](#full-list-from-projectplanmd-2026-10-24)
- [Changelog](#changelog)

---

## Setting change 2026-09-13 — implications

The premise changed from 2098 sci-fi/cyberpunk to **Philippines, 2002, noir
narrative, John Woo action, authored protagonist**. Full canon is in
`Design Document/Lore_And_Design_Notes.md` PART 1. What that does to this file:

**Carried, unchanged.** Everything built so far is setting-agnostic systems
work and stays: `AWeaponBase` + data-driven weapons, the bloom model and its
parameters (replaced by the Max Payne shooting model 2026-10-15), fire-rate
cap, full-auto, per-weapon anim selection, ammo
(magazine/reserve/timer reload), `AProjectileBase`, the composable HUD, the
first-person rig (since replaced by the third-person one, 2026-09-30), the
rendering target, and every gotcha below. None of it is
*canon* any more — it's the test bed the new direction gets evaluated against
— but none of it needs to be torn out either.

**Superseded — rationale gone, code stays.**
- The close-range rifle's projectile was justified as a coilgun with
  fragmenting rounds. That justification is discarded. The projectile system
  is general and works; what (if anything) fires a visible projectile in 2002
  — grenades, thrown weapons, something else — is a design decision. Until
  then the close-range rifle keeps its projectile configuration as a test bed.
- Enemies are no longer synthetics. **Superseded again on 2026-09-28** by the
  horror pivot: they are now mature Aswang, ferals and (rarely) humans — see
  the Enemies section. The composable data-driven architecture applies
  throughout; the "emissive panels read against baked lighting" note does not.
- The "no conversation system" rule was derived from the neutral
  protagonist. The protagonist is now authored, and dialogue choices are
  design-open. Don't build a conversation system yet; don't rule it out.
- Weapon *assets* were re-pointed 2026-09-21 from `SciFiWeapDark` to
  `MilitaryWeapSilver` (conventional firearms: `Pistols_A`,
  `Assault_Rifle_A`, `Sniper_Rifle_A`, with matching `Fire_*_W` animations,
  sounds and muzzle-flash FX). The sci-fi pack is removed. Weapon *roles*
  (pistol / close-range full-auto / scoped semi-auto) were designed for the
  old premise and are still open to revision. The 2002 arsenal is a design
  decision; the military pack is what the test bed uses meanwhile.

**Action-direction candidates.** Dual-wielding, dive/slide gunfire and
bullet-time were **designed on 2026-09-30** — see *Combat abilities* below.
Still unscheduled, but no longer unexamined. The remainder:
- "Destructible-feeling" is cosmetic first (particles, decals, physics
  props) and only becomes a system if design asks for mechanical destruction.
- Large shootouts are the strongest argument for the baked-lighting target:
  enemy count is where the performance headroom gets spent.
- Standoffs are a scripting/encounter concern, not a system.

**Under reconsideration, per the design doc** (neither confirmed nor
dropped): hip-fire-first accuracy model, linear campaign structure,
mini-sandbox arenas, weapons-dictate-playstyle. The code makes no assumption
that depends on any of these being decided either way.

*Enemy readability-at-a-glance came off this list on 2026-09-28 — resolved,
see Enemies. The campaign's coup plot was dropped the same day; the story is
being rewritten, so nothing downstream of it should be planned yet.*

---

## Combat: the shooting model — Max Payne 1/2 (2026-10-15)

**User decision, 2026-10-15:** "I'm happy to rework the whole shooting model,
those were designed for FPS… make it more to fit a Max Payne 1, 2 type." The
Halo: Reach bloom model (trigger discipline as the skill) is **retired**; the
skill is now positioning, Focus and the dodges. Built in four increments, each
compiled; the values are Claude's proposal, approved by the user, not yet
playtested.

**Unchanged rules:**
- **Aiming never touches accuracy.** `bIsAiming` is a camera/speed state; zoom
  is a separate per-weapon flag (`bHasZoom`), so a scope can't grant accuracy.
- **Enemies don't use any of this.** Their shots are placed by the hit-chance
  model and fired with `Fire(…, bExact = true)`, which skips the spread (see
  *Enemy shooting v2*). Their timing comes from the weapon's `AIFiring` (below).
- **Reticle:** a static 6 px white dot (2026-10-07). `WBP_Reticle` draws a
  fixed *Rounded Box* brush, 6×6, centre-anchored; the Tick chain is gone.
  `UReticleWidget::GetCurrentBloom` was **removed** 2026-10-15 (nothing
  referenced it). **Removed 2026-10-16:** `FCrosshairSettings`, the weapons'
  `Crosshair` property, `AWeaponBase::` / `UReticleWidget::GetCrosshairSettings`
  and the `M_Reticle` / `M_Reticle_Corners` materials (deleted after the weapon
  BPs were re-saved and nothing referenced them). `UReticleWidget` stays as an
  empty parent class for `WBP_Reticle`.

### Firing — hold the trigger (increment 1)

- **Every weapon fires while the trigger is held**, at its
  **`TimeBetweenShots`** (the gun's rate of fire; 0 = no limit). Pulling
  faster gains nothing: `CanFire()` enforces it for taps and holds alike.
- **Removed:** `EWeaponFireMode` (Semi/Auto), `FireMode`,
  `IntendedTimeBetweenShots` and the over-cadence bloom penalty.
- **Input:** `FireAction` `Started` → `DoFire`, `Triggered` → `DoFireHeld`,
  which now just calls `DoFire` every frame; the weapon paces it. The press
  frame fires both events; the second is rejected by `CanFire()`.
- **A held trigger doesn't break into a reload** — `DoFireHeld` returns while
  the weapon `IsReloading()`. Only a fresh pull (`Started`) interrupts a
  `PerRound` reload; otherwise a tube-fed shotgun would fire each shell the
  moment it went in.
- **Dry fire** still resets `TimeSinceLastShot`, so an empty gun clicks at its
  rate, not every frame.

### Accuracy — spread (increment 2)

A shot goes out in a cone of `AWeaponBase::GetCurrentSpread()` degrees:

`(Spread + SustainedSpread × burst) × moving × Focus`

| Setting (`Weapon|Accuracy`) | Meaning |
|---|---|
| `Spread` | The base cone, degrees. Max Payne's guns are accurate: keep it small. |
| `MovingSpreadMultiplier` | ×1 standing still → this at `MovingSpreadFullSpeed` (400 cm/s; the run is 500), linear by the holder's 2D speed. **Not while a shootdodge `IsDodging()`**: a dive is as true as standing. |
| `SustainedSpread` / `SustainedSpreadTime` | Extra cone a long burst wanders to, reached after this long of unbroken fire. 0 for pistols and shotguns. |
| Focus `FocusSpreadMultiplier` | On the **Focus component** (renamed from `FocusMaxBloomMultiplier`); applies during any Focus, the dive's included. **Default 0 (2026-10-16): dead on in Focus** — the rename had dropped the user's BP value and left 1 (no effect); user: "It should hit where the crosshair is, like previously". |

- **Bursts:** `BurstTime` grows by `TimeSinceLastShot` while shots follow
  within `TimeBetweenShots + BurstBreakTime` (0.15 s, a file-scope constant);
  a longer gap (the trigger let go) resets it. Computed **before** the shot's
  spread, so the first shot of a burst is clean.
- **Pellets:** the spread moves the pattern's centre; `PelletSpreadAngle`
  fans the pellets around it at a fixed width.
- **Removed:** `BaseSpreadAngle`, `MaxSpreadAngle`, `BloomPerShot`,
  `BloomDecayRate`, `BloomDecayDelay`, `CurrentBloom` and its decay in `Tick`.

### Enemy firing pattern — per weapon (increment 2b)

User: enemy timing "should be based on weapon type, ie bursts of very fast
weapons, but constant shots on others", with room for **harder variants**
later ("bigger bursts, less pauses").

- **On the weapon:** `FAIFiringPattern AIFiring` (`Weapon|AI`):
  `BurstShotsMin/Max` (1–1 = single shots), `ShotInterval` (spacing inside a
  burst; 0 = the weapon's rate), `BurstPauseMin/Max` (after each burst, or
  each shot). C++ defaults are the old enemy pattern: 3–5, 0, 0.5–1.5 s.
- **On the enemy:** `BurstShotsMultiplier` and `BurstPauseMultiplier`
  (`Enemy|Shooting|Bursts`, both ×1) — the knobs for tougher variants. The
  burst multiplier is rounded and **only applies when the weapon's
  `BurstShotsMax` > 1**, so a pistol stays a single-shot gun.
- **`UpdateShooting`:** pause, then `ShotIntervalLeft`, then a new burst is
  rolled; after each fired shot, either the pause (× `BurstPauseMultiplier`)
  or the next interval. A shot still never beats the weapon's own
  `TimeBetweenShots`.
- The enemy's own `BurstShotsMin/Max` / `BurstPauseMin/Max` were **removed**
  (their values on `BP_EnemyBase` / `BP_Enemy_Test` were dropped).
- For a single-shot weapon the **warning burst** is one shot.

### Configured values (2026-10-15, written through the bridge)

Damage, magazines, ranges and pellet cones unchanged; Focus ×1.

| Weapon | Rate (s) | Spread | Moving × | Burst wander | Enemy: burst / interval / pause (s) |
|---|---|---|---|---|---|
| `BP_Pistol` | 0.22 | 0.4° | 1.5 | — | 1 / — / 0.35–0.8 |
| `BP_Pistol_EnemyOnly` | 0.22 | 0.4° | 1.5 | — | 1 / — / 0.35–0.8 |
| `BP_DualPistols` | 0.12 (alternating) | 0.7° | 1.5 | — | 2–4 / rate / 0.5–1.0 |
| `BP_Shotgun` (semi-auto) | 0.35 | 0.3° (+ 8 × 2°) | 1.5 | — | 1 / — / 0.6–1.1 |
| `BP_PumpShotgun` | 0.9 | 0.3° (+ 8 × 1.5°) | 1.5 | — | 1 / — / 1.0–1.6 |
| `BP_BattleRifle` (sniper slot) | 0.6 | 0.15° | 2.0 | — | 1 / — / 1.0–2.0 |
| `BP_CloseRangeRifle` (assault) | 0.10 | 0.6° | 1.5 | +2° over 1 s | 4–8 / rate / 0.6–1.2 |

Before this pass: pistol 0.30, enemy-only pistol 0.125, duals 0.15, shotgun
0.30, pump 1.0, battle rifle 0.20, assault rifle 0.12; every `Spread` at the
0.5° default.

**History:** Phase 2 (2026-08-12) built the Reach model — `BaseSpreadAngle`
→ `MaxSpreadAngle` by a 0–1 bloom, `BloomPerShot`, decay after a delay, and a
cadence penalty for firing inside `IntendedTimeBetweenShots` (the "two limits
must differ" rule). The Phase 2/3 entries in `ProjectPlan.md` describe it.

### Ammo values

First tuning pass by the user, 2026-08-31. Close-range rifle confirmed to
feel good in play; the other two are untested against real combat.

| Field | Pistol | Close-range rifle | Battle rifle |
|---|---|---|---|
| `MagazineSize` | 12 | 30 | 12 |
| `StartingReserveAmmo` | 60 | 60 | 60 |
| `MaxReserveAmmo` | 120 | 120 | 120 |
| `ReloadDuration` | 2.0 | 2.2 | 2.2 |
| `bAutoReloadWhenEmpty` | false | false | false |

`ReloadDuration` matches each weapon's montage — `AM_Pistol_Reload` is 2.0s,
`AM_Rifle_Reload` 2.2s. Keep them in step when either changes: the timer is
authoritative, so a shorter duration refills ammo before the hands finish and
a longer one leaves the weapon idle at the end of the animation.

### Trace source — two-stage (rewritten 2026-10-03)

**The camera decides WHAT you hit; the muzzle decides WHERE the shot comes
from.** Single-stage camera firing is correct in first person, where the camera
*is* the eye. In third person the camera sits behind and beside the character,
so firing along its ray sends shots through cover the character is standing
behind.

`UWeaponHolderComponent::FireEquippedWeapon`:

1. Deprojects screen centre via
   `APlayerController::DeprojectScreenPositionToWorld`.
2. Traces that ray to `AWeaponBase::GetMaxRange()` to find the aim point.
3. Clamps the converge distance to **`MinConvergenceDistance`** (200). Against
   a near wall the muzzle can sit *past* the hit point, and converging on it
   would aim the shot backwards. The point is taken along the ray rather than
   from `ImpactPoint` precisely so it can be clamped.
4. Checks the muzzle is where it looks — see below.
5. Fires `Fire(MuzzleLocation, (AimPoint - MuzzleLocation).Normalized)`.

Spread (bloom until 2026-10-15) applies to the handed-in direction, so it
works off the muzzle→aim line for free. Projectiles spawn at `TraceStart`, which is now the
muzzle, so they leave the barrel.

**This does not reintroduce the August muzzle-socket problem.** That revert was
because the weapon mesh's local axes are not reliably the barrel axis. Here
only the socket's *location* is used; direction comes from the aim point, and
nothing reads the weapon's rotation.

`CrosshairViewportPositionY` stays `0.5`. It was originally `0.667` (Halo's
reticle position) but that permanently disagreed with zoom about where "centre"
was, since FOV narrows around the camera's true optical centre.

### Weapon raised vs lowered — hip-fire (2026-10-04)

**Behaviour.** Not aiming and not firing: weapon **lowered**, character in
`FreeRun` (faces travel, jog locomotion). A trigger pull **raises** the
weapon: the character snaps its yaw to the camera *before* the shot leaves
(`SetActorRotation` in `DoFire` — snapped, not interpolated, because the
shot is that frame; rotating the actor moves the muzzle socket with it), and
switches to the `Aiming` stance (strafe). After `LowerWeaponDelay` seconds
(default 1.5) without a trigger pull, it lowers and returns to `FreeRun`.

**State.** `TimeUntilWeaponLowered` counts down in `Tick`; every trigger
pull with a weapon equipped resets it — including dry clicks, rate-limited
presses and pulls mid-reload (intent, not outcome). `IsWeaponRaised()` =
`bIsAiming || TimeUntilWeaponLowered > 0`, `BlueprintPure` alongside
`IsAiming()`. **The AnimBP's lowered/raised blend reads `IsWeaponRaised`;**
`IsAiming` is for camera/ADS-specific things.

**Stance is now pull-style**, like the camera: `UpdateMovementStance()` runs
every `Tick` and derives the stance from `IsWeaponRaised()`, applying it only
on change. `DoAimStart`/`DoAimEnd` just set `bIsAiming`. `AnimationDriven`
is never overridden by this — it's entered and left explicitly.

**Speed follows the aim button, not the stance.** `ApplyMovementStance` owns
rotation rules only; `MaxWalkSpeed` is set every frame from `bIsAiming`
(`AimingSpeed` 250 vs `FreeRunSpeed` 500). Hip-fire strafes at full speed.
Per-frame because aiming can start while already in the strafe stance, which
is no stance change.

**Camera:** unchanged by hip-fire — only `bIsAiming` moves/zooms it.

**Animation (built 2026-10-04).** Lowered: per-weapon locomotion facing travel. Raised (hip-fire or aim): strafe blend spaces with orientation warping, plus the hip-fire idle upper body under the montage slot (`UpperBodyAlpha`). Lyra 4-way jog clips at 500 for hip-fire strafing — the earlier plan to layer shotgun-pack upper bodies over Lyra legs was dropped with the move back to Lyra. Full graph in *Animation architecture*.

### Crouch — a stationary stance (2026-10-05)

Design (Lore notes, 2026-10-05): constant motion in fights; crouch is momentary
cover or reload cover. So crouch only applies while standing still.

- **Request vs state.** `DoCrouchStart`/`DoCrouchEnd` only set
  `bCrouchRequested` (toggle or hold per `bCrouchIsToggle`). `UpdateCrouch()`
  (Tick, before `UpdateMovementStance`) calls `Crouch()` when requested AND no
  movement input (`GetCurrentAcceleration()` ≈ 0 — input, not velocity, so it
  reacts the same frame) AND on the ground; otherwise `UnCrouch()`. Moving
  therefore always stands the character up and moves exactly as standing
  (free-run, or strafe while aiming); stopping re-crouches.
- **`bMovementCancelsCrouch`** (default false, `BlueprintReadWrite`): true makes
  moving clear the request, so stopping leaves the character standing — and a
  crouch press while moving does nothing, which is where a slide-to-prone would
  hook in if it's ever confirmed (`DoCrouchStart` with movement input).
- **Camera stays put.** Crouching shrinks the capsule and drops its centre; the
  boom rides the capsule. `UpdateCameraTransition` sets the boom Z every frame
  to `BoomBaseHeight + (DefaultCapsuleHalfHeight − current half-height) +
  CurrentCrouchCameraOffset` — the capsule part instant (else the camera dips
  and floats back), `CrouchCameraOffset` (default 0) eased at
  `CameraTransitionSpeed` for an optional deliberate lowering.
  **Not** via `OnStartCrouch`/`OnEndCrouch` deltas: the engine's early-out paths
  report 0 adjustments, so start/end don't always pair and accumulating them
  drifted the camera out of the map.
- `CrouchedSpeed` is now only used if a ceiling blocks the uncrouch (the
  movement component keeps retrying it).

### Muzzle obstruction

`bBlockShotWhenMuzzleObstructed` (default on) traces from the **actor centre**
to the muzzle and returns `EFireResult::Blocked` if that short path is
obstructed — stopping the player firing through a wall they are pressed
against. Traced from the actor rather than the camera deliberately: the camera
sits behind the character and would cross its own body and any cover, giving
constant false positives.

No consumer switches exhaustively on `EFireResult`, so `Blocked` falls through
silently wherever it is not explicitly handled.

**Planned refinement — lower the weapon instead of blocking (noted
2026-10-03).** Suppressing the shot is correct but gives the player no visible
reason. The better answer is the one most shooters use: lower or angle the
weapon when the muzzle is obstructed, so the block is *shown* rather than
merely felt.

That changes where the check lives. It currently runs **on demand, inside
`FireEquippedWeapon`**. A weapon-lower needs the obstruction known
**continuously**, so it would move to a per-frame (or throttled) check exposing
`bIsMuzzleObstructed` as state for the AnimGraph to blend a lowered pose from.
Keep the fire-time check as the authority regardless — the animation is
feedback, not the gate. Needs a lowered-weapon pose, so it is Step 7 territory
or later.

---

## Rendering target

**Decided 2026-08-31 (6): Halo 1–2 fidelity. Baked lighting, minimal dynamic
lighting, fun over fidelity.** The reasoning is in the design document; this
section covers what it asks of the project.

### Current state vs. target

The project is still on UE5 defaults, which are the opposite of this target:

| Setting | Current | Target | Note |
|---|---|---|---|
| `r.AllowStaticLighting` | `False` | `True` | **Nothing can bake lightmaps until this is True.** Off by default in UE5. |
| `r.DynamicGlobalIlluminationMethod` | `1` (Lumen) | `0` (None) | GI comes from lightmaps instead. |
| `r.ReflectionMethod` | `1` (Lumen) | Reflection captures | Era-appropriate and cheap. |
| `r.RayTracing` | `True` | `False` | Unused once Lumen is off. |
| `r.Nanite.ProjectEnabled` | `True` | Open question | See below. |

### What switching actually costs

- **`AllowStaticLighting` requires an editor restart** and changes how every
  existing asset is lit. It is not a reversible toggle mid-session.
- **Meshes need lightmap UVs.** Vendor content (`MilitaryWeapSilver`, and anything
  migrated from Lyra) was authored for dynamic lighting and may not have a
  second UV channel. Unreal can generate them on import, but quality varies.
- **Levels need relighting and a light build.** The FirstPerson template map
  is lit dynamically; it would need static lights and a bake.
- **Nanite and baked lighting coexist awkwardly.** Nanite geometry supports
  static lighting but not well, and Nanite mostly buys detail density that
  this target doesn't want. Probably worth disabling, but it's a separate
  call from the lighting one and shouldn't be bundled with it.

### Implications for gameplay work

**Policy change 2026-10-09 (user): dynamic lights are allowed.** The user
decides static vs dynamic **per case** as content is built, rather than
defaulting everything to baked. Niagara works with either: particles are lit
by whatever lighting exists, and baked lighting only constrains particles that
emit light themselves.

Still the default stance: muzzle flashes and impacts carry their read
through emissive materials and particles, which is also what the era did.
Use a per-shot point light only where it earns the cost.

The 2002 setting is a good fit: fluorescent interiors, wet concrete and neon
signage read on strong shapes and colour, which is exactly what baked
lighting plus emissive materials does well. If enemy readability-at-a-glance
survives reconsideration, it'll come from silhouette, costume and behaviour
rather than glow.

---

## Weapons: data, not code

Weapons are one class differentiated by data, not per-weapon custom firing
logic.

- Shared `AWeaponBase`, differentiated by fire mode, the bloom table, damage,
  range, zoom flag, ammo, and anim type.
- Shared ammo model rather than bespoke per-weapon reload logic.
- `UWeaponHolderComponent` built with a **configurable** carry capacity, not
  hardcoded to 2, since the carry limit is design-undecided.

### Projectile vs hitscan

**Direction change (user decision, 2026-10-08): every weapon becomes a
projectile weapon.** Bullets are hidden at normal speed and shown in slow
motion. Started: `BP_Cal45Bullet` (`Content/ThirdPerson/Blueprints/`, `cal45_Full`
mesh, decal `MI_Generic`) on `BP_DualPistols`. The other weapons are still
hitscan until the user converts them.

**Status 2026-10-09:**
- **Done:** items 1 (splash opt-in, default 0), 4 (`SetSourceWeapon` →
  `GetDamageAtDistance` from the spawn point; hits use `ApplyPointDamage`) and 5
  (`bShowOnlyInSlowMotion`, threshold 0.9, `bKeepEffectsVisible` on).
- **Speeds:** the user preferred **9,000 cm/s** over 40–90k, so the rounds read
  in bullet time.
- **Radius:** 1 on both bullet BPs.
- **Still to do:** convert the remaining weapons (single pistol, shotguns —
  pellets as projectiles — battle rifle).

**Original backlog list** — `AProjectileBase` defaults predated this decision:
1. **Fragmentation is on for every round.** The C++ default is 150 cm radius,
   10 damage, swept on every hit with no skip. Make it opt-in: defaults 0, skip
   when 0. `BP_RifleProjectile` relies on the defaults today.
2. **Speed default 3000 cm/s (30 m/s).** Bullets want realistic per-BP speeds:
   .45 ≈ 25,000 cm/s; rifles 70,000–90,000.
3. **Collision sphere radius 5.** Bullets want ≈1. The visual mesh should be
   *NoCollision*.
4. **Damage falloff exists only on the hitscan path.** Projectile pellets deal
   flat damage. The weapon should pass `FalloffStartRange`/`EndRange`/min
   fraction to the projectile at spawn, measured from the spawn point.
5. **Visibility rule.** `bShowOnlyInSlowMotion` + `SlowMotionThreshold`
   on the projectile:
   - visual components hidden while `GetActorTimeDilation()` ≥ threshold;
   - collision is never touched;
   - needs no link to the future bullet-time code, which slows the world and
     keeps the player at normal speed via `CustomTimeDilation`;
   - testable now with `slomo`.

   Open: whether tracers also hide at normal speed.

Previously: `AProjectileBase` (real movement + collision + on-hit damage) was
assigned to the **close-range rifle** as a test bed; pistol and battle rifle
were hitscan.

**Setting change note:** the original reason for a projectile here — a
coilgun firing fragmenting rounds — is discarded with the 2098 premise. The
system is kept because it works and because 2002 has obvious uses for it
(grenades, thrown weapons); which weapon, if any, uses it is a design
decision. Until that lands the configuration below stays so the system
keeps getting exercised.

On-hit behaviour is a small-radius damage burst centred on the impact point
rather than a single point-damage hit.

Projectile defaults: 3000 u/s (~30 m/s, watchable and dodgeable at 25m
range), gravity disabled, 5s lifespan, 150-unit burst radius at 10 damage.

**Spawn origin:** projectiles spawn at `TraceStart` — the deprojected
crosshair point, the same origin the hitscan trace uses. This makes projectile
and hitscan weapons agree exactly on where a shot goes, applies bloom
identically to both, and removes the weapon's grip orientation from the
trajectory entirely. An earlier muzzle-socket spawn was reverted: the weapon
mesh's local axes are not reliably the barrel axis, and deriving direction
from the actor transform produced shots 40+cm off-axis.

**Self-collision:** projectiles must never hit their firer. A one-way
`IgnoreActorWhenMoving` is **not sufficient** — both sides sweep, so the other
actor's movement can still generate the blocking hit. `AProjectileBase` keeps
an explicit `IgnoredActors` list, ignores in both directions, and is told who
to ignore explicitly by the weapon at spawn rather than inferring from
`Instigator`/`Owner`. `OnHit` returns before `Destroy()` for ignored actors,
so a stray self-hit doesn't consume the round.

### Impact effects — per surface (2026-10-09)

Every hit, hitscan or projectile, spawns a **Niagara burst + a bullet-hole
decal chosen by the physical surface struck**. User-confirmed in PIE.

- **Data:** `UImpactEffectsData` (`UDataAsset`, `Weapons/ImpactEffectsData.h`)
  - `Surfaces`: `TMap<EPhysicalSurface, FImpactEffect>`;
  - `Default`: used for unlisted surfaces and hits with no physical material;
  - `DecalLifeSpan` 10.
  - `FImpactEffect`: `System` (Niagara), `Decal` (material), `DecalSize` (5,5,5).
    Either part may be empty.
- **Spawn:** `SpawnImpact(WorldContext, Hit)`. `GetSurfaceType(Hit)`, then
  `SpawnSystemAtLocation` at `ImpactPoint`, rotated to `ImpactNormal`,
  **pooled** (`ENCPoolMethod::AutoRelease`). The decal gets
  `SetFadeScreenSize(0)` as before.
- **Wiring:**
  - `AWeaponBase::ImpactEffects` (`Weapon|Impact`, `GetImpactEffects()`).
  - Hitscan sets `bReturnPhysicalMaterial` on the trace.
  - Projectiles set `bReturnMaterialOnMove` on the collision sphere and use
    the **source weapon's** asset.
  - The old `HitDecalMaterial` (weapon and projectile) is now only the
    fallback when no asset is set.
- **Modules:** `Niagara` and `PhysicsCore` added to `ProjectBopis.Build.cs`.
- **Surface types:** `DefaultEngine.ini` → `[/Script/Engine.PhysicsSettings]`,
  SurfaceType1–24 named to match the `ImpactsVFXVol1` physical materials:
  Dirt, Rock, Sand, Water, Glass, Cloth, Metal, Wood, Grass, Carpet, Concrete,
  Snow, Tile, Asphalt, Brick, Cardboard, Clay, Plastic, Electronics, Sheetrock,
  Plaster, Leaves, Blood, Rubber. The pack's Rubber material was set to
  SurfaceType24.
- **Scalability:** `ImpactsVFXVol1/Niagara/NFX_Impact` is an effect type
  (cull distance 5000, max 40 instances, distance significance) assigned to
  all 26 `NS_Impact*` systems.
- **Asset:** `ThirdPerson/Blueprints/DA_ImpactEffects`, set on all six weapon
  BPs.
  - Each surface uses its matching `NS_Impact*` and the `_1` variant of the
    nearest `UWC_Bullet_Holes` folder.
  - Rubber uses the Plastic burst, because the pack has none.
  - Water, Glass, Snow, Leaves and Blood are burst only. The glass holes are
    mesh decals, and decals on skinned characters look wrong.
  - `Default` is the Concrete burst + `MI_Generic_1`.
- **Level side:** a surface reacts only once its material (or instance) has a
  **Phys Material**. Otherwise it gets `Default`.
- **Characters (2026-10-24):** the Mesh of `BP_EnemyBase` and
  `BP_PlayerCharacter` has **Phys Material Override = `ImpactsVFXVol1/…/Blood`**
  (SurfaceType23, friction 0.7, restitution 0.3); the CC children inherit it.
  A component override reaches every physics-asset body (engine:
  `FBodyInstance::GetSimplePhysicalMaterial` — body override > component
  override > body setup > material > default). So a hit on a person plays the
  Blood entry (`NS_ImpactBlood`, no decal, no sound yet; **Scale 0.5**,
  user 2026-10-24: "scale the blood particles down" — × the asset's
  `EffectScale` 1.5, tune it there live in PIE). Before, no character
  had a physical material: body hits got `Default` (concrete burst +
  `MI_Generic_1`), and the hole projected onto every CC piece (body, head,
  clothes all receive decals). Safety net in code: `SpawnImpact` never spawns a
  decal on an `ACharacter`. Set through the bridge (object reference →
  restart before PIE); verified live on `BP_Enemy_CC` and `BP_Player_CC`.
- **`NS_ImpactBlood`, trimmed by the user (2026-10-24).** Size: the DA
  Scale only scales the component, which this system's sprite sizes
  ignore, so the user cut emitters/modules in the Niagara editor instead
  (Blood's DA Scale stays 0.5). **Floating chunks:** BloodChunks1 froze at
  the hit height, on an invisible copy of the floor raised by that height
  (slopes too). Cause: the emitter simulated in **Local Space**, and its
  Collision module put particles in the wrong space; **Local Space off**
  fixed it (user-confirmed). Collision Type is **Distance Field**, which
  ignores skinned meshes, so chunks drop through people. Things tried and
  ruled out on the way: a fixed small collision radius, and a "Debris"
  trace channel with CPU ray-trace collision (built, then rolled back
  entirely: config, Blueprint responses and docs). **Gotcha:** a Niagara
  emitter with collision that behaves as if the world is offset by the
  spawn point → check Local Space first.
- **Hit and near-miss sounds (2026-10-24, user: "we have the assets, just
  need the system").** Pack: `Real_Recorded_Guns/Cues/Bullet_Imacts_Flybys`
  (one wave per cue, no attenuation of their own).
  - **Hits:** `FImpactEffect::Sound` + **`SoundVariants`**, one picked at
    random (`PickSound`, like the decal pool). A character hit on a bone in
    **`HeadBones`** (`head`; both CC physics assets have that body) plays
    one of **`HeadshotSounds`** instead. All impact sounds use
    **`SoundAttenuation`** = `/Game/Audio/Weapons/ATT_BulletImpact`
    (duplicate of `ATT_WeaponFoley`: full within 600 cm, silent by 3600)
    at **`SoundVolume`**.
  - **Mapping** (8 variations each, flesh 10): Concrete/Asphalt/Brick/
    Plaster/Default → Concrete; Rock/Tile → Rocks; Dirt/Sand → Dirt; Metal →
    Metal_hard; Plastic/Electronics → Metal_light; Wood → Wood_Hard;
    Cardboard/Sheetrock → Wood_Light; Cloth/Carpet/Clay/Rubber → Mud; Glass
    → Glass_Close; Grass/Leaves → Grass; Snow; Water; Blood → Body_Flesh.
    Unused for now: Body_armor (a future armoured enemy), Glass_far.
  - **Near misses:** `UImpactEffectsData::PlayNearMiss(From, To, Shooter,
    HitActor)`, called from `AWeaponBase::FireHitscan` after every round's
    trace. It takes the point of the round's path nearest the player's head
    (`GetPawnViewLocation`); only if the round got past him (not stopped
    short, not started beside him), wasn't his, didn't hit him, and passed
    within **`NearMissRadius`** 250 cm. Plays one of **`NearMissSounds`**
    (10 flybys) there, so it's directional, at **`NearMissVolume`**, at most
    once per **`NearMissMinInterval`** 0.12 s (platform time, shared by every
    weapon), so bursts and shotgun pellets don't stack. Hitscan only; rockets
    and grenades make none.
  - *(Tested by the user 2026-10-24: "sounds work".)*

**Exaggeration pass (2026-10-09, user-confirmed in PIE).** The goal is
John Woo-scale hits.
- `FImpactEffect` gains:
  - `ExtraSystems`: Niagara layers spawned with the main burst;
  - `Scale`: per surface;
  - `DecalVariants`: randomly picked together with `Decal`;
  - `Sound`: `PlaySoundAtLocation`, which follows Focus's global pitch drop.
- `UImpactEffectsData::EffectScale` multiplies every burst's scale.
- Decals get a **random roll** around the normal.
- The decal pool is a `TInlineAllocator<8>` local, so there's no heap
  allocation per hit.

**Data:**
- `EffectScale` **1.5**.
- `DecalVariants` cover every `UWC_Bullet_Holes` variant in each folder: 10
  for Wood, Concrete, Ceramics and Bricks, 5 elsewhere.
- Per-surface `Scale` is 1, `ExtraSystems` is empty, and there are no sounds.

**Open:**
- **Impact sounds:** no bullet-impact assets in the project yet. The only
  candidate is `Knife_ImpactSurface_Cue`; `ProjectileImpact_att` is the
  attenuation.
- **Boosted Niagara copies as layers:** duplicate the `NS_Impact*` systems into
  our own folder and raise counts, velocity and lifetime. Never edit the pack.
- `ExtraSystems` is Niagara-only. The weapon pack's Cascade
  `P_Impact_*_Large_01` effects would need it widened to `UFXSystemAsset`.
- Bigger impacts during Focus.

### Weapon sounds (2026-10-23)

One path for every sound a gun makes. **The animation marks when, the weapon
says which sound, the weapon plays it.**

- **`EWeaponSound`:** Fire, DryFire, MagOut, MagIn, Chamber (slide/bolt),
  RoundIn (one shell / speedloader), Pump, Equip. Each weapon BP has a slot
  per event under **Weapon|Sounds** (`FireSound`, `DryFireSound`,
  `MagOutSound` …); an empty slot is silent.
- **`AWeaponBase::PlayWeaponSound(Sound, bOffhand)`** spawns the slot's cue
  attached to the gun's mesh (the off-hand mesh for duals): shots and clicks
  from the `Muzzle` socket, handling from the mesh root. Attached to the gun
  = owned by the gun, so a cue's *limit to owner* concurrency counts per gun.
  **Since 2026-10-26** (the feedback standard, *Adding a weapon*): `Fire()`
  calls it only for guns **without** a `FireAnimation`; a gun with one sounds
  its shot from a `Fire` Weapon Sound notify on that animation. The pack fire
  animations' own gunshot notifies were deleted earlier, so `Fire_Pistol_W`,
  `Fire_SniperRifle_W` and `Fire_Shotgun_NoDelay` each need a `Fire` notify.
- **`UAnimNotify_WeaponSound`** ("Weapon Sound" in the notify menu): `Sound`
  + `bOffhand`. On a character montage it plays on the character's equipped
  weapon; on a gun's own animation, on that gun (and the hand whose mesh is
  playing it). So one montage serves every gun of that anim type: the
  revolver maps Mag Out / Mag In / Chamber to open / speedloader / close, the
  launcher to open / insert / close. Silent in the animation editor preview
  (no gun in hand).
  - Placed: `AM_Pistol_Reload` (+`_Offhand`, Offhand ticked), `AM_Rifle_Reload`:
    Mag Out, Mag In, Chamber. `AM_Shotgun_Reload`: Round In in the Loop
    section. `AM_Pistol_Equip` (+`_Offhand`), `AM_Rifle_Equip`: Equip.
    `Fire_Shotgun_NoDelay` (weapon anim): Pump, replacing the pack's
    `Shotgun_Reload_Cue` notify.
  - Quick reloads (dive 3×, roll) reuse the montages, so the notifies come
    along bunched; whether to skip them at speed is undecided (user wants
    to hear it first).
- **Shared assets, `/Game/Audio/Weapons/`:** `ATT_Gunshot` — logarithmic,
  full to 10 m, silent at 80 m, LPF to 3 kHz by 60 m, non-spatialized
  inside 1–3 m (own gun doesn't flip ears), reverb send on; `ATT_WeaponFoley`
  — full to 2 m, silent at 15 m. Both copied from the pack's
  `WeaponShot_att` (the bridge can't create sound assets from scratch).
  Gunshot cues (6 MWS + 2 Real_Recorded + the `PistolA_Fire02` wave) and the
  explosion use `ATT_Gunshot`; gunshots override concurrency to **8 per
  owner, stop oldest, 0.25 s steal fade** (was the pack's 16 global /
  prevent new — the cause of dropped shots; a first pass at 4 voices with a
  0.05 s fade chopped the 2.7 s tails audibly on fast guns). Handling cues
  (28), shell drops, bounce, pickups use `ATT_WeaponFoley` — inner radius
  **500** (the camera sits 3–4 m behind the gun, so the player's own
  handling stays at full volume; at 200 it changed with camera distance),
  silent at 18 m; the pump rack 2 per owner.
- **Picks:** pistols share `PistolA_Fire_Cue` + MWS eject/insert/raise + RRG
  `Pistol_01` cock; revolver and MAC-11 all RRG; rifles MWS reload/insert/raise
  + RRG cock; launcher RRG flare-gun open/insert/close; shotguns MWS in/rack/
  raise. Dry fire everywhere = RRG `Revolver_Hammer_Hit_Cue` (no pack has a
  per-gun click). Variants (`_2`, `_3`) unused; pack loudness unmatched; no
  Weapons sound class yet (nothing in the project to duplicate one from).
- **Gotchas:** sound waves have no `bOverrideAttenuation` (cues do);
  the bridge can't read `Notifies` on montages — verify by parsing the
  export table (scratchpad `notifycount.js`) or in the editor; the first
  PIE after filling the slots and placing the notifies played no handling
  sounds although everything was saved — an editor restart fixed it, cause
  unknown. "Replace with" on an existing Play Sound notify logs a harmless
  `Type mismatch in Sound` (its sound asset vs our event enum).
- **User's tuning (not Claude's):** notify timing on the montages, the 3×
  quick-reload bunching, pack loudness. The weapon models are to be
  replaced later, so no further asset polish now.

### Footsteps (2026-10-23)

Surface-aware steps for everyone on `ABP_Player`, driven by the notifies the
Lyra clips already carry.

- **Detection:** every Lyra locomotion clip (walk, jog, strafes, crouch
  walks, the Kamz pack) has `FootPlant_Left` / `FootPlant_Right` name
  notifies (no class); the engine calls `AnimNotify_<Name>` on the
  AnimInstance for those, so `UProjectBopisAnimInstance::AnimNotify_FootPlant_Left/Right`
  → `OnFootPlant` → `ABopisCharacterBase::PlayFootstep(bLeft)`. Gated to on
  the ground, moving (`Speed > StationarySpeed`), not `bShootdodging`: idles,
  turns in place, the dive's legs and the prone poses carry plants too.
  `MDT_Mannequin` maps the two names, so the blade's mirrored legs step
  correctly. The shotgun pack's start clips have none (fine — they're the
  dive's run-up).
- **Surface:** `PlayFootstep` traces 40 cm down (`FootstepTraceDistance`)
  from `foot_l` / `foot_r` (from 10 cm above the sole — on a step up the foot
  is already inside the ground), `bReturnPhysicalMaterial`, Visibility. No
  hit = no step (a foot over an edge). Skipped while `bIsRagdoll`.
- **`UFootstepEffectsData`** (`Gameplay/`, modelled on `UImpactEffectsData`):
  `Surfaces` map `EPhysicalSurface` → `FFootstepEffect` {`Sounds` (random,
  never the same twice running — the character keeps `LastFootstepSound`),
  optional `Dust` Niagara, `Volume`}, `Default`, gait volumes (`WalkVolume`
  0.6 at ≤ `WalkSpeed` 250, `JogVolume` 1 at ≥ `JogSpeed` 500, blended;
  `CrouchVolume` 0.4), `VolumeScale`. Played with `PlaySoundAtLocation` at
  the hit point **with the character as owning actor**, so the cues'
  per-owner limit counts per character.
- **Assets:** `DA_FootstepEffects` (`ThirdPerson/Blueprints/`, set on
  `BP_PlayerCharacter` and `BP_EnemyBase`; CC children inherit) from the
  **Footstep_Casual** pack (12 sets, 10–14 variations each). Mapping:
  (user's tuning 2026-10-23 — the pack's Concrete set is too high-pitched
  for most floors, so Stone is the workhorse and Concrete is kept for the
  genuinely bright surfaces): **Default, Concrete, Asphalt, Brick, Plaster,
  Sheetrock, Rock → Stone**; **Tile, Glass → Concrete**; Dirt/Clay → Earth;
  Grass/Leaves → Grass; **Wood, Cardboard, Carpet, Cloth, Rubber, Plastic →
  Low Wood**; Metal/Electronics → Metal; Sand; Snow; Water/Blood → Water.
  The pack's Mud, Normal Wood and Low Metal sets are unused. `/Game/Audio/Footsteps/ATT_Footstep`:
  full to 3 m, silent at 25 m, no LPF; all 145 cues on it, **2 per owner,
  stop oldest**.
- **Physical materials:** the blockout materials carry none, so every floor
  is the Default until level materials get one. **The set to assign is the
  ImpactsVFXVol1 pack's `Materials/Physical_Materials/<Name>`** — one per
  surface, all 24 verified against the project's surface table (the table
  was derived from them). No project copies needed.
  - **A footstep patch without replacing the floor:** a Blocking Volume over
    the area, top ~1 cm above the floor, collision Custom = WorldStatic,
    everything Ignore except **Visibility Block**, Phys Material Override =
    the surface's physical material. The foot trace (Visibility) hits it
    first; pawns pass through; bullets hitting that floor get the same
    surface, which is right. Cleaner later: a dedicated `Footstep` trace
    channel + a `BP_FootstepArea` volume that blocks only that channel.
- **Thuds (2026-10-23):** heavier ground contacts go through the same data.
  `UFootstepEffectsData::PlayThud` = the surface's step at a given volume,
  with `BodyThud` (CC's `Landing_Cue`, on `ATT_Footstep`) layered under it
  for body contacts. `ABopisCharacterBase::PlayGroundThud(Bone, trace,
  volume, bBody)` traces from the bone like a step. Three callers:
  - **Dive landing:** `UShootdodgeComponent::NotifyLanded` →
    `PlayDiveLandingThud` (from `ThudBone` = `pelvis`, 100 cm,
    `DiveLandingVolume` — C++ default 1.5, **3 on the asset**, body).
  - **Roll:** `URollComponent::TickComponent` once the montage passes
    `RollThudAt` (0.2) → `PlayRollThud` (`RollVolume` — default 1.0, **2 on
    the asset**, body); reset per roll like the roll's Focus.
  - **Fall onto the feet:** `ABopisCharacterBase::Landed` →
    `PlayFallThud(-Velocity.Z)` (the velocity is still the fall's at that
    point) → `FallVolume`: silent below `FallLandingMinSpeed` 300, half of
    `FallLandingVolume` (default 1.2, **3 on the asset**) there, full at
    `FallLandingFullSpeed` 1000 (a normal jump lands at ~600–900). Enemies
    too. Skipped when `LandsOnTheBody()` — the player's override returns
    true mid-dive, so the dive's own thud isn't doubled.
  - User-tested 2026-10-23 ("thuds work"); the volumes above are the user's
    tuning (steps stay at walk 0.6 / jog 1 / crouch 0.4, scale 1).
- Later: the player's jog as AI noise.

### Weapon wheel (2026-10-23)

A GTA V-style radial picker (user's spec, 2026-10-23): a fixed ring of
segments, **one per weapon type (`WeaponSlot` 1–6), counter-clockwise from
the top**; each shows the type's current weapon. While it's open **combat
input and the camera are blocked, the crosshair hides, and time runs slow; movement
stays free** (camera lock + hidden crosshair: user, 2026-10-24 — "they can cheese the
game because of the dilation"). *(Tested by the user 2026-10-24; only the `IA_WeaponWheelCycle` mapping is left.)* *(The first version had one
segment per carried weapon; replaced the same day.)*

- **Keyboard (key mode):** a number key brings the wheel up with that type
  highlighted and it **stays up until the fire click**; more keys move the
  highlight; the same type again — or the first press on the type of the gun
  in hand — steps to the type's next weapon (pistol → duals → revolver). The
  click equips the highlighted weapon and closes (no shot). The camera holds
  still (2026-10-24). `Holder->SelectSlot` is no longer called from the keys.
- **Pad / held key (pointer mode):** held open, look input steers a pointer,
  the cycle action steps the hovered type, release equips.

- **`UWeaponWheelWidget`** (`UI/`, on `UPlayerHUDElementWidget`) is logic
  only; **the look is `/Game/UI/WBP_WeaponWheel`**, built in the designer
  (2026-10-24, the user wanted to design it — the first versions were drawn
  in code with `NativePaint`). On initialise the class finds its widgets
  **by name** (`GetWidgetFromName`, every one optional) and pushes state into
  them while open: `Segment_0..5` (Image) tinted by state (`HoverColor`,
  `EquippedColor`, `SegmentColor`, `EmptyColor` for a type with nothing
  carried); `Icon_0..5` (Image) set to the type's current weapon's **`Icon`**
  (`AWeaponBase`, Weapon|UI) at **the texture's own proportions**, hidden
  when empty. **All icons share one height** (user, 2026-10-24): the most
  that lets every *carried* icon fit `IconMaxWidth` 110 (so the widest gun
  sets it), capped at `IconMaxHeight` 50 for when nothing long is carried —
  every carried weapon counts, not just those showing, so cycling never
  resizes; size goes through the brush's `ImageSize`. **Dual-wield**
  (`IsDualWield()`): the icon shows twice, `IconDual_0..5` drawing the
  second, the second copy **behind the first, like a shadow** (user,
  2026-10-24: "one on top of each other to indicate dual"), the pair offset by
  `DualIconOffset` (10, 8; was 30, 14) and centred on the single icon's spot by render translation; the
  pair's spread counts against `IconMaxWidth`;
  `Count_0..5` (TextBlock) `k/n` when the type holds several, else hidden;
  `NameText` / `AmmoText` — the hovered type's weapon, else the one in hand,
  and `mag / reserve`. Anything else in the tree (the `Key_0..5` slot
  numbers, backdrops) is the user's and isn't touched. For Blueprint use:
  `GetHoveredIndex`, `GetSegmentState(i)` (`EWheelSegmentState`
  Empty/Carried/Equipped/Hovered), `GetSegmentWeapon(i)`,
  `GetSegmentAngleDegrees(i)` (screen degrees, −90 = top), and the
  **`OnHoverChanged(Index)`** event for animation. Layout numbers that the
  hit-test needs stay on the class (`NumSegments` 6,
  `FirstSegmentAngleDegrees` −90, `bCounterClockwise`, `Radius` 230 = the
  designed ring's middle, `DeadZone`, `PointerScale`, `CycleRepeatDelay`) —
  keep `Radius` in step with the layout.
- **`WBP_WeaponWheel` as generated:** root `WheelCanvas`, everything
  anchored at the centre (anchor/alignment 0.5). Six `Segment_i` = one
  `/Game/UI/T_WheelSegment` (1024², a white 56° ring wedge pointing up,
  UI compression, no mips) at 592² rotated `−60·i`° (render transform) →
  ring 165–295 px, 4° gaps; `Icon_i` at 230 px along the segment's angle (a pistol icon as
  designer preview) with `IconDual_i` on the same spot, hidden,
  `Key_i` (static "1"–"6") at 149, `Count_i` at 314, the two centre texts at
  y −12 / +14. Generated as UMG clipboard text by `Tools/MakeWeaponWheelTree.ps1`
  (writes `Tools/WBP_WeaponWheel_Tree.txt`; `-Clipboard` copies it) and
  pasted into the empty tree — the
  bridge can't build widget trees.
  **Don't give the class a property named like one of these widgets**: the
  Blueprint's generated widget variable clashes with it (hence
  `NameTextBlock`/`AmmoTextBlock` for the members).
- **Model:** `Segments[type]` = carried weapons of that slot in pickup
  order (rebuilt every frame while open); `Selected[type]` = the type's
  current weapon, kept between openings; `Open()` points each type at the
  equipped weapon where it has it. `CycleHovered(±1)` wraps, with
  `CycleRepeatDelay` 0.15 s so a held D-pad steps rather than spins.
- **Pointing:** while open, `LookInput` feeds the wheel instead of the
  camera — `AddPointerDelta` accumulates look input (mouse delta or stick
  value × `PointerScale` 10, Y flipped by `bFlipPointerY`) and clamps to the
  rim; inside `DeadZone` (0.3 × Radius) nothing is hovered.
  `GetHoveredIndex` = angle from the first segment, the way the segments
  run.
- **Character:** `OpenWeaponWheel(bKeyMode)` / `CloseWeaponWheel(bEquip)`.
  Number keys → `DoSelectWeaponSlot` → open in key mode +
  `SelectType(slot − 1)`; `DoFire` with the key-mode wheel up →
  `CloseWeaponWheel(true)`. `WeaponWheelAction` (hold; Started →
  `DoWeaponWheelStart` = pointer mode, Completed/Canceled →
  `DoWeaponWheelEnd`, which only closes a pointer-mode wheel);
  `WeaponWheelCycleAction` (Axis1D, Triggered → `CycleHovered(sign)`, works
  in both modes); `WeaponWheelClass` (`WBP_WeaponWheel_C` on `BP_PlayerCharacter`, inherited by `BP_Player_CC`; the C++ default has no tree and would show nothing); the widget
  made on first use at Z 50. **Open:** slow motion via
  `Focus->BeginFreeFocus()` (`bWeaponWheelSlowMotion`; no meter cost;
  nothing if the player's own Focus is already on), ended on close when the
  wheel started it. **Blocked while open:** jump, fire-held, aim start,
  reload, crouch start, Focus, dive, roll, grenade — each handler returns
  on `IsWeaponWheelOpen()`; **movement stays free** (user, 2026-10-23) and
  aim/crouch *releases* still go through. **Look** is swallowed in key mode
  and steers the pointer in pointer mode (`LookInput`, 2026-10-24), and in
  pointer mode the number keys are blocked too. **Crosshair:**
  `UReticleWidget::NativeTick` sets its render opacity to 0 while
  `IsWeaponWheelOpen()` (now public on the character) — opacity, not
  visibility, so it can't fight `WBP_Reticle`.
  **On death** (2026-10-24, audit #1) `Die` shuts the wheel before
  `StopFocus` and clears `bWheelOwnsFocus` without `EndFreeFocus` — the
  death slow-mo is a free Focus too, and a later click would have ended it.
  *(Camera lock, hidden crosshair and the death fix: User-tested 2026-10-25.)*
  Equip → `DoSelectWeapon(pick)` → `Holder->EquipWeapon`, with the number
  keys' old gating (no swap mid-roll or in a dive wind-up).
  `UWeaponHolderComponent::GetCarriedWeapons()` exposes the list.
- **Assets:** `IA_WeaponWheel` (digital) and `IA_WeaponWheelCycle`
  (Axis1D) set on `BP_PlayerCharacter` and `BP_Player_CC`; the 11 weapons
  have `DisplayName` + an icon from the Handcrafted Weapon Icons **White**
  set (first-pass picks — the revolver, MAC-11 and launcher are guesses).
  **IMC mappings are the user's** (the bridge reads `IMC_Default.Mappings`
  as empty): `IA_WeaponWheel` ← Tab, Gamepad Left Shoulder;
  `IA_WeaponWheelCycle` ← Mouse Wheel Axis, Gamepad D-pad Up (+1) / Down
  (Negate).
- **Later:** the user's own wheel art (swap `T_WheelSegment` or the
  Segment images' brushes), the Black icon set if the HUD goes light.

---

### Adding a weapon — intake checklist (2026-10-25)
For the final weapon assets (plan item 33) and any gun after. Every system is
data-driven per weapon, so a new gun reuses an existing **anim type** (no new
montages) and needs:
- **Mesh:** a **skeletal** mesh (the weapon components are skeletal), barrel
  along **+X**, cm scale. Moving parts as their own bones (slide/pump, bolt,
  magazine) — the pump code (`PumpBoneName`; it assumes the pump bone's
  parent has X along the barrel) and any gun-side reload animation need them.
- **Budget** (provisional, 2026-10-25, until the deferred Steam Deck perf
  test; third-person camera, Halo 1–2 fidelity): LOD0 **3–6k triangles** for
  pistols/SMGs, **6–12k** for long guns; LOD1 ~50%, LOD2 ~25%; 1 material
  (2 at most); one texture set, 2K long guns / 1K pistols and SMGs; ~5–15
  bones, rigid skinning. A dressed CC character is ~30k verts and 12 draw
  calls, so guns at these numbers add ~15–30% per body. Bought packs are
  often 20–60k (first-person): bring LOD0 down with the skeletal-mesh LOD
  reduction rather than remodelling.
- **Sockets** (user, placed visually): `MuzzleFlash` (X out of the barrel),
  `AmmoEject`, and `LeftHandGrip` on long guns and two-handed pistols.
- **Blueprint** (bridge, from the matching existing one): mesh, `AnimType`,
  `AmmoType`, wheel `WeaponSlot`, `DisplayName` + icon, sound slots
  (`EWeaponSound`), `FireAnimation` if the gun animates itself, muzzle FX,
  shell casing, `PumpBoneName`/`PumpTravel` only for a pump gun with no fire animation of
  its own (None otherwise — its animation moves the pump); duals also the
  off-hand mesh and `OffhandGrip*` offsets.
- **Tuning** (user, in PIE): `GripLocationOffset`/`GripRotationOffset`
  (socket space of `HandGrip_R`), stats (damage, fire rate, magazine,
  reload, spread).
- **Around it:** a pickup Blueprint (ammo + weapon), enemy weapon pools /
  spawn entries if enemies carry it, and — for a pump gun with no fire animation — a post-process
  AnimBP on the mesh (parent `WeaponAnimInstance`, one Transform (Modify)
  Bone on the pump bone ← `PumpSlideOffset`, Parent Bone Space; the user
  creates the asset with the skeleton, Claude wires it).
- **After:** the replaced placeholder's assets go on the unused-content list.
- **Feedback standard — in code 2026-10-26** (user, 2026-10-25: "The
  animation drives only the movement and notifies. The notifies drive the
  sounds"; 2026-10-26: "It will now always play the Fire animation when
  firing. If it is none, it will not do it. We replace the notifies with our
  own ones so it does not double up"). `bUseAnimationDrivenFeedback` and
  `UsesAnimationDrivenFeedback()` are **removed**. `AWeaponBase::Fire()`:
  - `FireAnimation` set → it plays on the firing mesh every shot; it moves
    the gun's parts and its **Weapon Sound notifies make the sounds** (the
    shot is a `Fire` notify, so it still goes through `PlayWeaponSound` —
    same attenuation and per-shooter voice limit).
  - `FireAnimation` None → no animation; the `Fire` sound plays from code.
  - `MuzzleFlash` always spawns from code at `MuzzleSocketName`, every gun.
  - Dry fire stays in code.
  So a gun's fire animation carries **no flash or pack sound notifies** — the
  flash would double, and pack sounds would bypass the weapon's sound slots.
  New guns: author the fire anim with a `Fire` Weapon Sound notify (plus
  `Pump`/`Chamber` where the part moves). Bridge on the day: the .45 pair and
  `BP_Pistol_EnemyOnly` got `P_Pistol_MuzzleFlash_01` (their flash used to
  come from `Fire_Pistol_W`); `BP_PumpShotgun`'s `FireAnimation` is the
  user's `Mossberg-500_Pump`. Guns with a fire animation (and so silent until
  it has a `Fire` notify): the .45 pair + enemy pistol (`Fire_Pistol_W`),
  `BP_Shotgun` (`Fire_Shotgun_NoDelay`), `BP_BattleRifle`
  (`Fire_SniperRifle_W`), `BP_PumpShotgun` (`Mossberg-500_Pump`). Without
  one: the 9mm pair, MACs, revolver, 5.56 rifle, launcher.
  **User's fire animations (2026-10-26),** each with a Weapon Sound `Fire`
  notify and no flash, wired by the user: `SK_Beretta_92FS_Fire` (9mm pair),
  `SK_SMG11_Nostock_Y_Skeleton_Fire` (MAC pair; its Fire notify must sit
  before the next shot restarts the clip, ~0.05 s), `/Game/_357Revolver_Fire`
  (revolver; the cylinder doesn't turn — left for later), and
  `Mossberg-500_Pump`. Still without a fire animation: the 5.56 rifle and
  the launcher. **M4 hatch:** `SK_AR4`'s `b_gun_shelleject_hatch` is closed
  in the reference pose. Moving bones in the mesh editor's viewport is
  preview-only and isn't saved; either edit the reference pose with the
  Skeletal Mesh editor's skeleton editing tool (Accept, then save), or have
  an M4 fire animation open it and end open — a gun's fire animation holds
  its last frame, so it stays open after the first shot, like a real dust
  cover.

## Ammo

Four phases: **A** state + gating + dry fire (done), **B** reload (done),
**C** HUD readout (done — `WBP_Ammo` on `UAmmoWidget` inside `WBP_PlayerHUD`;
the on-screen `Bloom:`/`Ammo:` debug lines were deleted 2026-10-06), **D**
pickups (**done 2026-10-08**, see *Pickups and the backpack*).

Design decisions: **auto-reload off** by default, **reload cancels on weapon
swap**. **Superseded 2026-10-08:** "separate reserves per weapon" — the reserve
is now **one shared pool per ammo type**, held by the weapon holder (below).

### Shared ammo pool (2026-10-08)
Max Payne style: every carried weapon that takes a type reloads from the same
pool, so the single and dual pistols share their rounds.

- **`UWeaponHolderComponent`:**
  - `ReserveAmmo` (`TMap<EAmmoType,int32>`);
  - `AddAmmo(Type, Amount)` caps at the type's max and returns what was taken;
  - `TakeAmmo(Type, Wanted)` and `GetReserveAmmo(Type)`;
  - caps in `MaxAmmoByType` on `BP_PlayerCharacter` (Pistol **180**, SMG **300**,
    Rifle **300**, HighPowerPistol 60, Sniper 40, AutoShotgun 40,
    PumpShotgun 40), fallback `DefaultMaxAmmo` 240.
- **`AWeaponBase`:**
  - keeps its own **magazine**;
  - its reserve calls go through `ReserveSource` (set by the holder in
    `AddWeapon`);
  - `TakeReserve` returns everything asked for when `bInfiniteReserve` is on;
  - `MaxReserveAmmo` and the per-weapon `CurrentReserveAmmo` were removed;
  - `StartingReserveAmmo` is what a loadout weapon adds to the pool;
  - a weapon not carried has a reserve of 0.
- The HUD is unchanged: `GetReserveAmmo()` on the weapon now reports the pool.

**Ammo types (2026-10-06).** `EAmmoType { Pistol, HighPowerPistol, SMG, Rifle,
Sniper, AutoShotgun, PumpShotgun }`; each weapon sets `AmmoType` (default
Pistol, `GetAmmoType()`). Mapping: `BP_Pistol`/`BP_DualPistols` → Pistol,
`BP_CloseRangeRifle` → Rifle, `BP_BattleRifle` → Sniper (it becomes a sniper),
`BP_Shotgun` → AutoShotgun, `BP_PumpShotgun` → PumpShotgun. HighPowerPistol and
SMG are for weapons not built yet. Set on the Blueprints 2026-10-08. Anim type
and ammo type are independent (`BP_Pistol` is `PistolOneHanded`, duals `Dual`,
both Pistol ammo).

**.45 and 9mm pistols (2026-10-25).** User: "I have added the Beretta. Create
a weapon and dual for it. Name it 9mm Pistol. Rename the current pistol to .45
Pistol." `BP_Pistol9mm` / `BP_DualPistol9mm` are copies of `BP_Pistol` /
`BP_DualPistols` (`PistolOneHanded` / `Dual`, Pistol ammo, slot 2) on
`/Game/Tactical_SemiAuto_Pistol/SkeletalMesh/SK_Beretta_92FS` (main and
off-hand meshes), cross-linked (`DualWieldClass`, `SingleWieldClass`,
`DropAsClass` → the 9mm pair). The .45s' `Fire_Pistol_W` is on the old
skeleton, so the 9mm pair has no gun-side fire animation (`FireAnimation`
None — the shot sounds from code), with `P_Pistol_MuzzleFlash_01` at the `MuzzleFlash` socket
(the pack's `SK_Beretta_92FS_Anim`, 3.3 s, isn't a fire cycle). Display
names: ".45 Pistol" / "Dual .45 Pistols", "9mm Pistol" / "Dual 9mm Pistols".
**Scale 1.2** (user): the root `WeaponMesh`'s relative scale on both; the
dual's off-hand stays 1 and inherits it (the holder's attach rules keep world
scale), so it isn't doubled.
**The .45s stay on the silver model** (2026-10-25). An M1911
(`/Game/M1911/Meshes/SkeletalMesh/Rigged_M1911`) was swapped onto the .45
pair and the enemy-only pistol, then reverted at the user's call ("put them
back to the silver model"): `Pistols_A`, scale 1.0, `Fire_Pistol_W`, as
before (since 2026-10-26 with `P_Pistol_MuzzleFlash_01` from code; the flash
used to come from the animation). The silver pistol's problem is that it
has no magazine; the 1911 pack's `NonRigged_M1911_Magazine` is to supply one
for reloads — **the user's design, later** (a "Magazine In Hand" notify-state
proposal was set aside: "I have my own ideas for that"). Notes on the 1911
mesh for whenever it's used: barrel along X (the other pistols' along +Y; a
yaw −90 reimport didn't take), no slide bone, no sockets, 6 material slots,
11,474 verts, 1 LOD.

**5.56 Assault Rifle (2026-10-25).** `BP_CloseRangeRifle`, renamed, on the FPS
pack's M4 (`/Game/FPS_Weapon_Bundle/Weapons/Meshes/AR4/SK_AR4`; barrel +Y
like the silver rifle, 91 cm, 9,735 verts, 2 materials). **Scale 1.2** (user, after
trying 1.1 — about 109 cm in game; the root mesh). Its length is the
**extended stock** (user): the stock has no bone, and `SK_AR4_X` is the same
model turned to +X, not a collapsed variant — collapsing it means moving the
buttstock's vertices ~8 cm forward (Blender, or the skeletal-mesh modeling
tools) and reimporting. Sockets added on its
own bones: `MuzzleFlash` on `b_gun_muzzleflash`, `AmmoEject` on
`b_gun_shelleject` (zero offset — check the flash direction). Still needs a
`LeftHandGrip` and grip offsets. **Still a projectile weapon**
(`BP_RifleRound_Projectile`, the old setting's fragmenting round) — hitscan is
the user's call.

**Mossberg 500 material (2026-10-25).** Mesh `/Game/Mossberg/Mossberg-5001`
(the importer's `Mossberg-500` is a Phong material instance with no
roughness/metallic inputs — now unused). New `MI_Mossberg500` from
`M_TacticalPistol` (BaseColor / Normal / ORM, Tint white, Mask the engine's
black texture so nothing tints); the ORM texture switched to linear
(`SRGB` off, `TC_Masks`). Mesh: barrel +Y, 112 cm, 3,109 verts, bones
`grip`, `trigger`, `safety`, `pump` (child of `grip`), `ejectionport`, `shell`,
`muzzle`. **On `BP_PumpShotgun`** at root scale **1.2** (user, 2026-10-26; set up by the user with `GripLocationOffset` (0, 30, −3) and
`MuzzleFlash`, `AmmoEject`, `LeftHandGrip` sockets); `PumpBoneName` fixed from
the silver gun's `Slide_Bone` to `pump` — with a missing bone the pump offset
fell back to the component's axes, sideways on this model. Unverified: that
`grip`'s X runs along the barrel (the pump code's assumption). The model has a
straight stock, no pistol grip, so the shotgun hold poses (pistol-grip
wrist) don't fit its right hand.
**Fire animation (2026-10-26):** the user's `/Game/Mossberg/Mossberg-500_Pump`,
on the Mossberg's own skeleton, with Weapon Sound notifies. The old
`Fire_Shotgun_NoDelay` was on `Shotgun_A`'s skeleton (it wouldn't play on this
mesh), and the pump shotgun's old feedback switch was off anyway, so its fire
animation had never played. **Left hand:** the rotating/odd left hand is
reach, not rotation — its `LeftHandGrip` (y 40 on the root) sits farther
forward than the M4's, overextending the arm. Options: move the socket back,
put it on the `pump` bone (it then rides the pump), or a lower scale.
**Pump (2026-10-26, user).** With the gun's own fire animation playing, the
hand pumped **sideways**: the procedural pump (the `Pump` curve on
`MM_PumpShotgun_Fire` → an offset along the `pump` bone's parent X) assumed
`grip`'s X runs along the barrel, and on this model it doesn't. So
`PumpBoneName` is **None** on `BP_PumpShotgun`, and the pump moves only by
`Mossberg-500_Pump`, which the user retimed to match the body's
`MM_PumpShotgun_Fire` ("Its fixed now"). `LeftHandGrip` is still on the root
bone, so the hand holds the gun steady; to have it ride the pump, put the
socket on `pump`.
**Open:** the Beretta mesh has **no sockets yet** (`MuzzleFlash`, `AmmoEject`
— user); grip offsets are the .45's copy (tune in PIE); icon is the .45's;
no pickup or loadout entry yet; both pistols share Pistol ammo (design call:
`HighPowerPistol` exists for the .45 if they should differ); 7,552 verts and
1 LOD — over the pistol budget, reduce. The `Slide` bone could kick on fire
through the pump mechanism (a `Pump` curve on the fire montage) later.

**MAC-11 placeholder (2026-10-19).** `BP_MAC11` (`PistolOneHanded`) and
`BP_DualMAC11` (`Dual`), the first SMG-ammo weapons; an Uzi replaces them in
production. Mesh `/Game/FPS_Weapon_Bundle/.../SMG11/SK_SMG11_Nostock_Y` with
user-placed `MuzzleFlash`/`AmmoEject` sockets (X forward). Single 0.06 s,
12 damage, 32 rounds, reload 2.0, spread 1.2 → 1.5; dual 0.05 s, 64, 2.4,
1.6 → 1.8; reserve 128; AI bursts 4–8 / 6–12, pauses 0.6–1.2.
`BP_AmmoPickup_SMG` gives 32.

**Gunfire concurrency (2026-10-19).** Fire sounds have long tails (SMG 5.9 s,
sniper 5.3, shotgun 4.3), so rapid fire from several enemies ran out of voices.
Each fire sound overrides concurrency on the asset: `MaxCount` 3,
`bLimitToOwner` (the weapon actor, so a dual pair shares 3), `StopOldest`,
`VoiceStealReleaseTime` 0.05. A new weapon's fire sound needs the same.
Open: the player's own shots play 3D from the muzzle and shift as the camera
moves; likely 2D for the locally controlled player. **Gotcha:** the pack's sockets need the X axis
down the barrel; the bladed hand turn and the casings steer by the muzzle's X.

**Starting loadout (2026-10-10):** on `UWeaponHolderComponent`.
- `StartingWeaponClass` is spawned and equipped first.
- `StartingLoadout` (array) is added after it, hidden. Classes already carried
  are skipped, e.g. the single that the duals imply.
- `bStartWithFullAmmo` fills each carried type's pool to `GetMaxAmmo`.
- `BP_PlayerCharacter`: duals in hand, all six weapons, full ammo — a
  testing loadout, not a design decision. Enemies keep a single starting
  weapon.

### Pickups and the backpack (2026-10-08)
**No carry limit ("magic backpack").** `MaxCarriedWeapons` was removed;
`AddWeapon` refuses only null or already-carried weapons. Its
`bAddStartingReserve` parameter is false for pickups, which bring their own
rounds.

**Weapon selection — number keys by category (Max Payne 1):**
- Each weapon has a `WeaponSlot`: 2 pistols (single and duals), 3 shotguns,
  4 SMGs/rifles (close-range rifle), 5 sniper (battle rifle); 1 is kept free
  for melee.
- `SelectSlot(Slot)` equips the first carried weapon in that slot, or the next
  one if that slot is already equipped, wrapping in pickup order.
  (`InSlot.Find(Equipped)` returns −1 when not found, so +1 lands on index 0.)
- Input: `IA_WeaponSlot1`–`5` (copies of `IA_Reload`) on keys 1–5 in
  `IMC_Default`, listed in the character's `WeaponSlotActions`. Bound in a loop
  with the slot number as a delegate payload.
- Not set yet: *Player Mappable Key Settings* on the actions (an instanced
  object the bridge can't write). Add them in the editor when a rebinding
  screen exists.

**`AAmmoPickup`** (`Source/ProjectBopis/Pickups/`):
- Trigger sphere (60) + a static mesh with no collision; `AmmoType`, `Amount`
  (per placed instance), optional `PickupSound`.
- Walk-over → `Holder->AddAmmo`; what doesn't fit stays; destroyed when
  empty; never respawns.
- Works even with no weapon of that type carried (Max Payne style).
- Triggers once on entry: standing on a box with a full pool needs a step off
  and back on.
- `BP_AmmoPickup_Pistol` (`ThirdPerson/Blueprints/Pickups/`): the
  `cal45_PaperBoxOpen` mesh, offset −60 so it sits on the floor.

**`AWeaponPickup`:**
- Its own `WeaponClass`; the mesh is taken from the class's default object in
  `OnConstruction`, so no per-pickup mesh setup.
- `AmmoMode`: **Fixed** (`FixedRounds`) or **Random**, rolled in `BeginPlay`
  from half a magazine to a full one.
- On walk-over, in order:
  1. **Not carried:** `Holder->GiveWeapon(Class, Rounds)` spawns it hidden, loads
     the magazine with the rounds, adds it and equips it if `bAutoEquipOnPickup`
     (a player option, on by default). Consumed.
  2. **Carried, and its `DualWieldClass` isn't:** the dual version is unlocked
     the same way, and the single stays (separate selections, Max Payne 1).
     Consumed.
  3. **Otherwise:** rounds go to the pool; the remainder stays.
- `BP_WeaponPickup`: its mesh sits 50 units below the trigger centre.

**Single ↔ dual links on the weapon:**
- `DualWieldClass` (`BP_Pistol` → `BP_DualPistols`).
- `SingleWieldClass` (`BP_DualPistols` → `BP_Pistol`): adding a dual weapon also
  adds its single if missing. It's loaded from the pool, inserted ahead of the
  duals so slot 2 cycles single → duals, and doesn't take the equip. So starting
  with duals gives both.
- `FindCarriedWeapon` matches the **exact** class.

**Later:** enemy drops can spawn `AWeaponPickup`s, filling the rounds from the
enemy's magazine instead of Random.

### Equip animation (2026-10-08)
- **Trigger:** `UWeaponHolderComponent::EquipWeapon` ends by calling
  `AProjectBopisCharacter::PlayEquipAnimation(Weapon)`. That covers every
  equip: number keys, pickup auto-equip, the starting weapon. The holder still
  swaps the gun **instantly**; the animation plays over it (user decision for
  now — a mid-animation swap on a notify is the later upgrade).
- **Montages:**
  - `EquipMontages` / `OffhandEquipMontages`, keyed by anim type like fire and
    reload.
  - `AM_Pistol_Equip` (pistol, pistolOneHanded, dual) and `AM_Rifle_Equip`
    (rifle, shotgun, pumpShotgun) in `DefaultSlot`.
  - `AM_Pistol_Equip_Offhand` (dual) in `OffhandSlot`.
  - All in `Characters/Heroes/.../Actions/`, from Lyra's full-pose
    `MM_Pistol_Equip` / `MM_Rifle_Equip` (the `_Additive` variants are
    unused).
- **Fire is blocked during equip** (user decision): `DoFire` returns while
  `IsEquipAnimating()` (`ActiveEquipMontage` still playing). That covers
  full-auto, since `DoFireHeld` goes through `DoFire`. Aim, move and further
  switching aren't blocked.
- **Slot effects:** the equip montage, in `DefaultSlot`, cuts off the previous
  weapon's fire/reload montage. `ActiveReloadMontage` then clears itself in
  `UpdateReloadMontage`. While it plays it raises the upper body, then the drop
  eases back to lowered.
- **Known look issue (left for later):** Lyra's equip ends with the gun pointed
  straight ahead, then eases down to lowered, which reads oddly. Options:
  - blend the montage out early (`BlendOut` / `BlendOutTriggerTime`);
  - trim or re-author the clip to end near the lowered pose;
  - keep the weapon raised for a moment after equipping.

### Fire result

```
EFireResult { Fired, RateLimited, Empty, Reloading, NoWeapon }
```

Ammo is deliberately **not** folded into `CanFire()`. Rate-limited and empty
need different responses — rate-limited must be silent, empty must click and
optionally auto-reload — so the enum widens the channel that already existed
rather than adding a parallel one.

The dry-fire path resets `TimeSinceLastShot`. Without it `CanFire()` stays
true every frame and a held trigger machine-guns the click.

### Reload

Timer-driven via `ReloadDuration`, **not** notify-driven. A notify would put
authoritative timing inside an animation asset the weapon can't see, and would
break for any holder whose montage differs. The montage plays alongside as
feedback; `ReloadDuration` should be tuned to match it.

Partial magazines are **kept, not discarded** — the remainder stays in
reserve.

The ammo gate lives in `Fire()`, so future AI inherits it. `bInfiniteReserve`
is the opt-out.

**Reload styles (2026-10-03).** `EReloadStyle` on the weapon: `Magazine`
(default — the timer above) or `PerRound` for tube-fed shotguns.
`PerRound` waits `ReloadStartDelay`, then loads **`RoundsPerLoad`** rounds
(default 1; 2 on both shotguns, 2026-10-06) every `TimePerRound` via a
self-re-arming `LoadRound()` timer until full or the reserve is dry — a batch
stops short if the magazine fills or the reserve runs out mid-batch. Each
round is committed as it goes in. **Firing interrupts a `PerRound` reload**
when at least one round is loaded — `Fire()` cancels the reload and shoots;
with nothing loaded it still returns `Reloading`. Not modelled: chambering
after a reload from empty.

**Per-round reload animation (2026-10-06).** `AM_Shotgun_Reload` has sections
`Start` → `Loop` (one load cycle; linked `Loop → Loop` in the asset) and `End`
(the rack, unlinked). Timings match the sections: `ReloadStartDelay` = Start
length, `TimePerRound` = Loop length (user-set). The character drives it in
`UpdateReloadMontage()` (Tick), polling weapon state — no delegates needed:
- **Loop wrap:** section jumps inside a montage never blend, and the clip has no
  matching pose at the wrap, so it snapped. A blend-time (`ReloadLoopBlendTime`,
  0.15) before Loop's end, it re-plays the same montage from Loop's start via
  `Montage_PlayWithBlendIn(..., bStopAllMontages = true)` — the old copy fades
  out as the new one fades in. (`false` left the old copy looping underneath
  forever.)
- **End:** once the weapon stops reloading (full, dry, or swapped), Loop's next
  section is re-pointed to `End` (`Montage_SetNextSection`, this playthrough
  only) — the current insert finishes, then the rack plays. **Since
  2026-10-25 only with `bPlayReloadEnd`** (character, default **off**; user:
  "Just dont rack it at all for now"): otherwise Loop's next section is
  `NAME_None`, so the montage ends with the last insert and blends out.
- `ActiveReloadMontage` tracks the montage from `DoReload` until it stops;
  `IsReloadAnimating()` exposes that so the AnimBP keeps the left-hand IK off
  through the whole montage, rack included (the weapon's `IsReloading()` goes
  false before the rack).
- Montages without a `Loop` section (magazine reloads) are untouched.

**Reload upgrades (2026-10-17/18, user-confirmed):**
- **Through a roll:** at a roll's start, `HoldReloadForRoll` decides what
  happens to a reload in progress.
  - **Magazine reloads** at least `RollReloadKeepFraction` (1/3) done
    (`AWeaponBase::GetReloadProgress`) are cancelled and held. When the roll
    ends, `Reload()` + `CompleteReloadNow()` fill the magazine through the
    normal `FinishReload`, with no animation. Less than 1/3 done: cancelled.
  - **Per-round weapons** (shotgun): the cycle under way goes in after the
    roll (`CompleteReloadNow` loads `RoundsPerLoad` rounds), then loading
    stops.
  - The held reload belongs to the gun in hand (`RollHeldReloadWeapon`). A gun
    picked up mid-roll drops it.
- **Quick reload in the air:**
  - During a dive's flight (`IsAirborne()`), reload runs at `AirReloadSpeed`
    3×. `Reload(Speed)` divides the timers, and
    `PlayReloadAnimation(Weapon, PlayRate)` plays the montage(s) at the same
    rate (`ActiveReloadPlayRate`, kept for the Loop restarts).
  - It doesn't end the dive's slow motion (`bStopFocusOnReload` is skipped in
    the air).
  - Auto-reload works in the air too (`bAirAutoReload`).
  - The user found 3× readable. At 5× the montage blends, which don't scale
    with play rate, washed it out. Scaling the blends is noted for anything
    faster.
- **Quick draw in the air:** the virtual `GetEquipPlayRate()` returns
  `AirEquipSpeed` (3×) mid-flight. `PlayEquipAnimation` plays the equip
  montage(s) at that rate, and firing waits only on `IsEquipAnimating()`, so
  the gun is live as soon as it ends.
- **Seen in the dive branch:**
  - `ProneReloadAlpha` (the dive branch's upper-body montage layer) now
    rises for an equip as well as a reload.
  - The dive's aim correction lets go during either.
  - With duals, the left arm takes the **mirrored off-hand montage** there
    too. See *Dual pistols in the dive: off-hand montages and recoil*.
- **The left arm follows the gun mid-dive:** each frame of the flight and the
  landing, `SetLeftArmSimulating(FreesLeftArm(), …)` takes the loose left
  arm off physics when you switch to a two-handed gun, and puts it on for the
  one-handed pistol.
- Settings: `BP_PlayerCharacter`, *Combat|Reload*.

### Directional hit indicator (2026-10-16)

The user: "red on hit, maybe near miss too as grey, but we dont want the
screen flooded".
- **Events:** `AProjectBopisCharacter::AddHitIndicator(Source, bHit)`.
  **Red** from `TakeDamage` (damage > 0) toward the instigator's pawn, else
  the damage causer. **Grey** from the round itself: `AProjectileBase::CheckNearMiss`
  (Tick) reports once when someone else's round has **gone past** the player
  within `NearMissRadius` 150 cm (the closest point of this frame's path lies
  behind it). A round that hits is gone first (red only); one stopped by cover
  never comes near. *(First version marked every enemy miss at fire time —
  it showed behind walls; user: "only show when a bullet actually whizzed
  past".)*
- **Flood control** (character, `Combat|Hit Indicators`): directions
  bucketed into `HitIndicatorSectors` 12; one marker per sector and kind,
  refreshed rather than stacked; a hit removes the grey one there; grey is
  skipped where red shows, within `NearMissIndicatorCooldown` 0.5 s of the
  last, past `MaxNearMissIndicators` 3, and (`bNearMissOnlyOffScreen`) for
  shooters inside the camera's FOV. Fade: `HitIndicatorDuration` 1 s,
  `NearMissIndicatorDuration` 0.6 s, **real time**; expired in Tick. Switches:
  `bShowHitIndicators`, `bShowNearMissIndicators`.
- **`UHitIndicatorWidget`** (`UI/HitIndicatorWidget.h/.cpp`): `NativePaint`
  draws each marker as a 9-point arc (`FSlateDrawElement::MakeLines`) on a
  ring of `Radius` 160 px, `ArcDegrees` 30, `Thickness` 6, at the source's yaw
  relative to the camera's (recomputed each frame, so markers swing as you
  turn), alpha × the fade. `HitColor` red 0.9, `NearMissColor` grey 0.5.
  Needs `Slate`/`SlateCore` in `ProjectBopis.Build.cs` (private) — without
  them it links-fails on `MakeLines`.
- **Editor:** `WBP_HitIndicator` (parent `HitIndicatorWidget`), full-screen in
  `WBP_PlayerHUD`, *Not Hit-Testable*.

### Shell casings (2026-10-16)

The user's choices: **physics casings** (Max Payne 2), the **pump shotgun
throws its shell on the rack**, **player and enemies** eject, with variety in
the throw.

- **`AWeaponBase::Fire`**, on every shot that fires (enemies included), calls
  `EjectCasing(IsOffhandNext())` — duals eject from the gun that fired — at
  once, or after `CasingEjectDelay` on a timer (pump: 0.4 s).
- **`EjectCasing`:** from the mesh's **`AmmoEject`** socket (every
  MilitaryWeapSilver weapon has one). The throw is the gun's right
  (`Up × barrel`, the barrel from the muzzle socket's X) + up ×
  `CasingEjectUp` 0.6 − barrel × `CasingEjectBack` 0.2, then randomised:
  `VRandCone` within `CasingEjectSpread` 15°, speed `CasingEjectSpeed` 250
  ± `CasingSpeedVariation` 25%, plus the shooter's velocity; spin a random
  axis × `CasingSpin` 1080°/s × 0.5–1. Spawned along the barrel.
- **`AShellCasing`** (`Weapons/ShellCasing.h/.cpp`): a `UBoxComponent` body
  sized to the mesh's bounds (min 0.3 cm; the AmmoSet meshes have no simple
  collision), `PhysicsActor` profile ignoring Pawn / Camera / Visibility /
  Projectile / PhysicsBody (like `AWeaponDrop`), **CCD on**, hit events on.
  `CasingLifeSpan` 10 s. `CasingImpactSound` on up to 3 bounces (> 60 cm/s,
  0.15 s apart) — none set: the project has no casing sounds.
- **`UShellCasingSubsystem`** (world subsystem): at most **64** casings
  (`MaxCasings`), oldest destroyed first.
- **Meshes (AmmoSet, set via the bridge):** pistols and duals
  `cal9mm_Cartridge`; both shotguns `cal12Gauge_Used`; assault rifle
  `cal5_45_Cartrige`; battle rifle `cal__62_Cartrige`. (`_Cartridge` is the
  case, `_Bullet` the head, `_Full` the round.)
- **`CasingScale`** (per weapon, default 1, user-confirmed the casings look
  right): scales the mesh and its physics body together (2026-10-16).

### Pellets and damage falloff (2026-10-03)

`PelletsPerShot` (default 1) and `PelletSpreadAngle` (default 0). The shot's
spread (bloom until 2026-10-15) displaces the **pattern centre**; the pellet
cone spreads around it at a fixed width, a property of the gun. One pellet at
zero spread skips the second random draw, so single-shot weapons are
unchanged. Ammo, spread, sound and animation are per shot, not per pellet.
`BaseDamage` is per pellet.

Range falloff: `FalloffStartRange` → `FalloffEndRange` lerps damage from
100% to `MinDamageMultiplier`, measured from the muzzle (`TraceStart`).
Off unless End > Start. **Hitscan only** — projectile damage lives in
`AProjectileBase`. Open: each pellet is a separate `ApplyPointDamage`, so a
shot can produce up to N damage events on one target; aggregate per actor once
`Health` and hit reactions exist. The pattern is random (`VRandCone`); a
fixed authored pattern is a design question.

**Two shotguns (2026-10-06, design in the lore notes):** `BP_Shotgun`
(SPAS-style, semi-auto, no pump — standard `AM_Shotgun_Fire`) and
`BP_PumpShotgun` (`AnimType = PumpShotgun`, `AM_Shotgun_Fire_Pump` with the pump
at the end). Same mesh (`Shotgun_A`), same reload montage. Intent: DOOM-style
**range** (tighter `PelletSpreadAngle`, far falloff distances) with a **very
slow reload** as the main drawback — tuning is the user's, later. At the
current 0.3 s `TimeBetweenShots`, a quick follow-up cuts the pump animation
short; raise it to the pump length if the pump should always finish.
`PumpShotgun` exists only so the fire montage can differ — the AnimGraph's
per-weapon Blend Poses by Enum nodes got matching pins (user, by hand), and the
character's montage maps need an entry for it like any anim type.

**Procedural pump and grip curves (2026-10-25, in progress).** User: a more
prominent pump; the reload's End should pump, not slap the top; the equip
should end with the left hand on the grip. Findings: `Shotgun_A`'s
`Slide_Bone` (child of `Grip_Bone`; the barrel is `Grip_Bone` +X) never
moved — `Fire_Shotgun_NoDelay` has no slide track — and while raised the
left-hand IK pinned the hand to `LeftHandGrip`, which sits on `Clip_Bone`
(static), so the clip's own pump was overridden. Both shotguns shared
`AM_Shotgun_Reload` (End = a top slap, right for the semi-auto).
- **Curves on the clips** (read by `UProjectBopisAnimInstance`):
  **`Pump`** 0–1 (slide fully back at 1) and **`HandGrip`** 0–1 (left-hand
  IK on although a montage is playing: `LeftHandIKAlpha` = max(its usual
  value, the curve) for two-handed holds).
- **Slide:** `AWeaponBase::PumpBoneName` / `PumpTravel` (cm);
  `SetPumpAmount` each frame from the `Pump` curve (`UpdatePump`, which also
  zeroes a gun put away mid-pump); `GetPumpOffset()` = (−travel × amount,
  0, 0) in the slide's parent-bone space. `UWeaponAnimInstance` (base for a
  weapon mesh's **post-process AnimBP**, so it runs on top of whatever the
  gun plays) exposes it as `PumpSlideOffset` for a Transform (Modify) Bone
  on the slide (translation Add, Parent Bone Space). **Both shotguns**:
  `Slide_Bone`, 8 cm — the semi-auto doesn't pump when it fires (its fire
  clip has no `Pump` curve) but does at the end of a reload (user).
- **Hand:** `UpdateLeftHandGrip` adds the same offset (parent-bone space →
  world → `hand_r` space) to `LeftHandGripLocation`, so the IK'd hand rides
  the slide.
- **Reload:** both shotguns keep the shared `AM_Shotgun_Reload` (user: "both
  shotguns I plan are using the same anim sequence"). **No rack for now:**
  `bPlayReloadEnd` is off, so End (the slap) doesn't play. If a rack comes
  back, the plan was curves over `MM_Shotgun_Reload`'s End (`HandGrip` 1 for
  the hand on the grip, `Pump` for the slide), or End only after reloading
  from empty. The rack clip can't go into the montage anyway: `MM_PumpShotgun_Fire` is
  additive and the reload is a full pose — a montage track can't mix
  additive types ("AAT" error). A pump-only copy
  (`AM_PumpShotgun_ShellReload`) was made and removed the same day. Note:
  the four CC Blueprints each hold their own copy of `ReloadMontages`, so a
  change on `BP_PlayerCharacter` / `BP_EnemyBase` doesn't reach them.
- **Deferred until the final shotgun model** (user: `Shotgun_A` "is a place
  holder"): the post-process AnimBP that moves the slide (one Transform
  (Modify) Bone on the pump bone, `PumpSlideOffset`, Parent Bone Space; the
  user creates the asset with the skeleton — the bridge makes AnimBPs without
  one — and Claude wires it and sets the mesh's Post Process Anim Blueprint).
  The code assumes the pump bone's parent has X along the barrel; check that
  on the new rig. Until then the hand rides 8 cm along a still slide
  (`PumpTravel` 0 keeps it on the grip instead).
- **To do:** the curves
  (user): `Pump` on `MM_PumpShotgun_Fire` (its rack); `HandGrip` at the end
  of `MM_Rifle_Equip`.

---

## Explosives (2026-10-19)
Player only for now; enemy grenades are for scripted sets (e.g. shooting one
out of the air), which `AGrenade` already supports.
- **`AExplosion`** (`BP_Explosion`): spawned where something goes off, with
  its Instigator. Overlaps all dynamic objects in `Radius` (600); full
  `Damage` (250) inside `FullDamageRadius` (200), down to
  `EdgeDamageFraction` (0.2) at the edge; walls block (Visibility trace from
  20 cm up, everything caught ignored). Each victim gets point damage aimed out
  and up from the blast, so `TakeDamage`'s overkill/`LaunchBody` flings bodies.
  Loose physics gets a radial impulse. Full self-damage. Bodies it kills (or
  already dead in it) are thrown at once: `ABopisCharacterBase::BlastLaunch`
  goes limp and adds a velocity change of `ThrowSpeed` out + `LiftSpeed` up,
  scaled like the damage (bullet launches are capped per hit, so blasts need
  their own; tuned on `BP_Explosion` by the user). Effects
  `P_Grenade_Explosion_01`, `GrenadeLauncher_Explosion_Cue`, optional camera
  shake. A kill by the player's blast: `PlayKillSlowMotion(1.5)`.
- **Kill slow motion:** `UFocusComponent::PlayKillSlowMotion(RealDuration)` is
  a free Focus on a real-time timer; ignored if slow motion is already on. A
  later `BeginFreeFocus` (dive, roll) takes it over; pressing Focus claims it
  (outside a dive — mid-dive either key cancels it instead, see *Free Focus*).
- **`AGrenade`** (on `AProjectileBase`; `OnHit` is virtual): `FuseTime`
  (0 = none), `bExplodeOnImpact`, bounce sound above `MinBounceSoundSpeed`.
  Shot: goes off now and the shooter becomes the Instigator. Caught in a blast:
  goes off after `ChainDelay` (0.15 s). `Launch(Velocity)` for throws.
  `BP_Grenade_Thrown` (2.5 s fuse, bounces) and `BP_Grenade_Launched`
  (impact, 2500 cm/s, gravity 0.5).
- **Thrown grenades:** quick throw (not a weapon slot). `DoThrowGrenade` (G,
  `IA_Grenade`) works standing, prone and in the air, not mid-roll, reload or
  draw; `GrenadeThrowCooldown` 0.9 s. From the lowered stance it raises the gun
  and waits for the turn to the camera (`GrenadeFacingTolerance` 20°, at most
  `GrenadeMaxTurnWait` 0.35 s), then plays `AM_GrenadeToss` (additive, slot
  `Additive`, just before the Output Pose) and releases at
  `GrenadeReleaseTime` 0.35 s from `hand_l`. Max Payne 2 arc: control
  rotation lofted `GrenadeLoftAngle` (12°) × `GrenadeThrowSpeed` (1400) +
  `GrenadeInheritVelocity` (0.5) × the thrower's velocity.
  `IsThrowingGrenade()` (turning or mid-toss) keeps the free arm off physics,
  eases the blade's upper-body turns out (`ThrowAlpha`, legs stay) and brings
  the one-handed left arm back to the hand-forward hold (the toss is authored
  from it).
- **Count:** grenades are ammo, `EAmmoType::Grenade` (cap 5 in
  `MaxAmmoByType`, `StartingGrenades` 3), so ammo pickups refill them
  (`BP_AmmoPickup_Grenade`, 1). HUD: `UAmmoWidget::GetGrenadeCount`.
- **`BP_GrenadeLauncher`:** rifle hold, slot 6 (`IA_WeaponSlot6`, key 6;
  explosives), `LauncherGrenade` ammo (cap 12), 6 rounds + 6, 0.8 s, 3.0 s
  reload, fires `BP_Grenade_Launched`, no spread or casings, its own
  `LeftHandGrip`. Pickups `BP_GrenadeLauncher_Pickup`,
  `BP_AmmoPickup_LauncherGrenade` (3).

**Revolver (2026-10-19).** `BP_Revolver`: `Pistol` (two-handed) hold, slot 2,
no duals, `HighPowerPistol` (cap 60), 6 + 24, 60 damage, 0.45 s, 2.6 s
speedloader reload, no casings. Mesh `_357Revolver_Rig`: its bones carry a 100×
scale, so its sockets (`MuzzleFlash`, `LeftHandGrip`) are scaled 0.01. Grip
pitch 8 / yaw −93 (the mesh runs along X, the pistol family along Y).

**Hands (2026-10-19):**
- Left-hand IK (`TwoBoneIK_0`, on `ik_hand_l` moved to the `LeftHandGrip`
  socket) runs for every two-handed hold whenever the gun is up (aimed or
  raised for hip-fire) — **and for long guns lowered too, since 2026-10-26**
  (user: "on jog and idle lowered, I edited the anim so the left hand is close
  to the weapon grip, but it does not follow it"): the gun rides `hand_r` with
  each weapon's own grip offsets, so a lowered pose can only bring the hand
  near the grip. The two-handed pistol keeps the gun-up rule
  (`bIsPistolHold`). Not for the one-handed pistol or duals; lets go for
  reloads, draws and throws. It keeps the pose's hand rotation
  (`bTakeRotationFromEffectorSpace` off, `bMaintainEffectorRelRot` on): the
  rifle turn clips otherwise rolled the hand palm-up.
- Hip aim: for two-handed holds at the hip, the blade's hand turn (`hand_r`)
  points the barrel at the crosshair (`HipAimHandAlpha`; capped at
  `BladeHandMaxAngle`).
- `UpdateBlade` takes `RootYawOffset` back out of what it measures
  (`RotateRootBone` comes after its turns in the graph).

**Guns against walls (2026-10-20):** a raised gun whose space ahead is taken
(`ABopisCharacterBase::UpdateWeaponBlocked`: a WorldStatic/WorldDynamic trace
from `spine_05` along the control rotation, `LongGunWallDistance` 90 /
`PistolWallDistance` 55, +`WallClearMargin` 15 to unblock) is **blocked**: the
anim instance treats it as lowered and not aimed, the player's `DoFire` and the
enemy's `FireAt` don't fire. The raise timer keeps running, so it comes straight
back up. The trace ignores the gun's pose, so lowering can't un-block it.
Only hits that **block Visibility** and face sideways (`ImpactNormal.Z < 0.7`)
count: trigger boxes (WorldDynamic, overlap-only) and the floor when aiming
down made it lower constantly at first.
Dives are untouched.

**Prone reloads (2026-10-21):** lying on a side, the lower shoulder pinned an
arm in the dual reload, and face-down the arms went into the floor. **Duals and
long guns** reloading prone on a side (|direction| between `ProneFrontMaxAngle`
45 and `ProneSideMaxAngle` 150; face-down was tried and looked jarring) send the prone pose to the back-prone one (`PoseDirection` 180, at `ProneDualReloadSwapSpeed` 8) for the
reload; it returns at the normal swap speed after. The single pistols reload
where they lie. Under it the aim is ignored (`ProneNeutralAlpha`, eased at the same
speed): no spine counter-turn and no pitch, so it reloads looking along the
legs, then goes back to the aim. The dive branch's mirrored off-hand layer
(`LayeredBoneBlend_9`) now blends in **local** space (`bMeshSpaceRotationBlend`
off): in mesh space the left arm kept the standing reload's absolute angle and
twisted when lying down. **Face-down** (|direction| ≤ `ProneFrontMaxAngle`, eased into
`ProneFrontAlpha`) only the forearms and hands take the reload, the upper arms
staying forward: `LayeredBoneBlend_11` (`UpperBodySlot` from `lowerarm_l`/`_r`,
`ProneForearmReloadAlpha`) and `_12` (`OffhandMirror` from `lowerarm_l`,
`ProneForearmDualAlpha`) sit between `_7` and `_8`; `_8`/`_9` take
`ProneArmReloadAlpha`/`ProneDualOffhandAlpha` = the rest. Use Cached Pose nodes
`_3`/`_4` were placed by the user. Long guns face-down still reached the floor, so both upper arms
raise about the shoulders' line (`ProneLongGunArmRaise`,
`ProneLongGunArmRaiseAngle` 30, sign picked so the elbows rise) on
`upperarm_l`/`upperarm_r` (`ModifyBone_34/35`, between `_11` and `_22`). An
upper-back arch was tried first and rolled back.

**Silent swaps face-down (2026-10-21):** within `SilentEquipFaceDownAngle` (45)
of face-down while prone, `PlayEquipAnimation` plays no montage
(`ShouldSilentEquip`); `SilentEquipTimeLeft` runs for the montage's length (at the
equip play rate) instead. Firing, throws and auto-reload wait for it
(`IsSilentEquipping`), and the dive branch's long-gun and dual holds
(`ShootdodgeLongGunAlpha`, `ShootdodgeDualAlpha`) ease over in that same time. (A procedural chest roll was tried first and
dropped.) Long guns'
dive/prone left-hand hold (`ShootdodgeLeftHandAlpha`) now lets go for reloads,
draws and tosses.

**Gotchas (2026-10-19):** the player pawn is `BP_Kamz`, a child of
`BP_PlayerCharacter`; set player defaults on it (parent values set through the
bridge didn't carry over). The bridge's `set_socket_transform` resets the
fields you leave out.

## Encounter triggers, ambushes and spawning (2026-10-19)
User's use cases: enemies charging round a corner, or pouring out of the room
at the end of a hallway when the player is halfway down it; and enemies
spawned as the player goes rather than all placed up front.
- **Waiting:** `AEncounterTrigger::bEnemiesWaitForTrigger` (default on)
  makes its `Enemies` blind and deaf to the player and to allies' alerts
  (`AEnemyBase::bWaitingForTrigger`, checked in `Alert`) until it fires.
  Being shot still wakes one. Off: the old "make sure" trigger.
- **Ambush move** (`AEnemyBase`, Ambush category): `AmbushPoint` (run there
  first; a holder then holds there, `HomeLocation` moves) or
  `bRushOnTrigger` (first move is a push at the player). Made by the first
  `ChooseNextSpot` after `TriggerAmbush`. They move at once; the reaction
  beat only delays the first shot.
- **Spawns** (`FEncounterSpawn` list on the trigger, first firing only):
  class (or the trigger's `DefaultEnemyClass`), `SpawnPoint`, `Weapon`,
  `AmbushPoint`, `bRushOnTrigger`, `bHoldsPosition`, `Delay`. Spawned
  deferred (gun chosen before BeginPlay), stood on the point, skipped if the
  point is blocked. With `WaitForTrigger` set, the enemy spawns asleep and
  joins that trigger (`AddEnemy`; if it already fired, set off at once):
  the **spawn-ahead line**. Without it, it comes in set off.
- **Markers:** `AEncounterPoint` (a Target Point with `PointRole` Spawn/Ambush), as
  `BP_EnemySpawnPoint` (red) and `BP_AmbushPoint` (yellow) in
  `ThirdPerson/Blueprints/Encounter/`. Points and triggers carry an editor-only
  `UTextRenderComponent` label (role or TRIGGER, Outliner name, trigger counts),
  refreshed in `OnConstruction`; hidden in game, stripped from builds. (`Role`
  is taken by `AActor`, hence `PointRole`.)
- **Spawn entries also set** `HoldRadius` and `bCrouchWhileHolding` (holders), and
  `PatrolPoints`. An entry with no ambush point, no rush and no hold is a
  **patroller**: it spawns unalerted, senses on, walking its route (or standing).
  With `WaitForTrigger` it joins that trigger awake (`AddEnemy(Enemy, false)`), so
  the trigger still sets it off. Patrol stops are `BP_PatrolPoint` (green,
  `PointRole` Patrol).
- Triggers have an editor-only `S_Trigger` icon at their centre to click.
- **Ambush arrival:** `AmbushAcceptanceRadius` (enemy and spawn entry, 20 cm),
  measured to the centre (stop-on-overlap off) for the trip to the AmbushPoint
  only; `ChooseNextSpot` leaves it for the move task (`ConsumeAmbushAcceptance`).
  Other moves keep the StateTree task's 50 cm with stop-on-overlap.
- **Editor tools (2026-10-20):** a `ProjectBopisEditor` module (Editor type,
  PostEngineInit) registers an **Encounter** tab in Place Actors (trigger + the
  three point Blueprints). Triggers draw link lines in the editor viewport
  (`bDrawLinks`; enemies orange, spawn red, ambush yellow, patrol green, the
  awaited trigger a cyan arrow) by ticking in the editor only
  (`ShouldTickIfViewportsOnly`; tick off in play). Failed moves log a warning
  (`AEnemyBase::ReportUnreachable`, every 3 s at most).
- **Patrol speed:** `PatrolSpeed` 180 while unalerted with patrol points. The
  lowered Move poses are single jog clips (no walk), so a walk needs the
  ABP's lowered sequence players swapped for a walk/jog blend space by Speed
  (`BS_MM_Unarmed_Jog_Walk` exists: walk 200, jog 400).
- Not built: removing enemies behind the player (with level streaming, later).

**Room cleared and waves (2026-10-24, user: "do the room cleared one, even
better if you can set a wave spawning event system"):** on `AEncounterTrigger`.
- **Its room:** `Enemies` (placed, plus spawn-ahead enemies other triggers
  hand it via `AddEnemy`) and its own spawns, which `SpawnOne` now adds to
  `Enemies`. Entries with `WaitForTrigger` belong to that trigger's room
  instead. `PendingSpawns` counts delayed entries not yet in (decremented as
  each one's moment comes, spawned or not). `GetAliveCount()` = living
  `Enemies` + `PendingSpawns`.
- **Polled** by `UpdateRoom` on a 0.25 s looping world timer from
  `BeginPlay` (no death event to bind; the director polls the same way).
  From the start, so a room shot clear from the doorway before the player
  walks in counts.
- **Waves** (`Waves`, `FEncounterWave`): `Spawns` (the same entries; `Delay`
  is from the wave's start), `StartWhenAliveAtMost` (0 = everyone before it
  down), `Delay` 2 s, `EventsToStart`. Only after the trigger has fired, in
  order: the next one is due once the one before is all in
  (`PendingSpawns` 0) and the room is at or under its count, then comes
  `Delay` later (world time). `BringIn(WaveIndex)` spawns a list
  (`INDEX_NONE` = the first `Spawns`); `OnWaveStarted(Trigger, WaveIndex)`.
- **Cleared:** nothing left to bring in (fired, or no spawns and no waves),
  it has had someone (fired, or enemies listed), all waves started, and
  `GetAliveCount()` 0. Once: `EventsOnCleared` start, `TriggersOnCleared`
  `Fire()`, `OnCleared(Trigger)` broadcasts (Blueprint-assignable, for the
  Level Blueprint), timer stops; `IsCleared()`.
- **Editor:** wave spawn lines pink, a wave's events purple arrows, the
  cleared links white arrows; the label adds "Waves N (M spawns)".
- **Limits:** a delayed spawn-ahead from another trigger isn't counted until
  it arrives, so the room can clear early without it. The director
  (`AEncounterDirector`) is separate and doesn't count toward a room.
- *User-tested 2026-10-25* (a wave after thinning out, the cleared link, a room shot clear from
  outside its trigger).

**Scripted events, stage 1 (2026-10-21):** `AEncounterEvent` (Encounter tab;
editor label + note icon; purple lines to its speakers, and from triggers that
start it). Ordered `Steps` (`FEncounterEventStep`): **SayLine** (speaker enemy,
optional speaker name, sound, subtitle; length = `Duration` or the sound's, else a
reading time 1 s + 0.06 s/char; `PauseAfter` 0.3) and **Wait**. Started by a
trigger's `EventsToStart` (first firing) or `bStartOnBeginPlay`; runs once.
Voices play from the speaker's `head` with an attenuation override
(`VoiceFullRange` 400, `VoiceFalloff` 2500), so no attenuation asset is needed.
Subtitles via `AProjectBopisCharacter::ShowSubtitle` / `GetSubtitle` and the
`USubtitleWidget` HUD base (user-built widget), only within `SubtitleRange`
(3000; 0 = always). Any speaker alerted or killed stops it: the voice fades,
the subtitle clears, and an alerted (living) one says `InterruptSound` /
`InterruptSubtitle`. Speakers should keep their senses on (not on a waiting
trigger). **Spawned speakers:** a spawn entry's `Tag` goes on the enemy as an
actor tag; a Say Line with no `Speaker` uses `SpeakerTag` (the living enemy with
that tag, looked up when its line comes). A trigger spawns its immediate spawns
before starting its events. **Animations (2026-10-21):** a step's `Animation`
(montage on `DefaultSlot`, same as reloads) plays on the speaker — with a Say
Line it loops (its last section set to run into itself via
`Montage_SetNextSection`) until the line ends; a **PlayAnim** step plays one
without a line (`bWaitForAnim`: the next step waits for it, else runs
alongside; a set `Duration` loops it that long, 0 = plays once). An interrupt stops every
step's montage on every speaker.

**Scripted events, stage 2 (2026-10-21):** new step types —
**MoveTo** (`Target` actor, `bRun`, `AcceptanceRadius` 50, `bWaitForArrival`;
`AEnemyBase::ScriptedMoveTo` sets `bScriptedMove`, which pauses `UpdatePatrol`
and picks walk = `PatrolSpeed` / run = `LoweredSpeed`; the wait ends when the
AI's move goes Idle, then `PauseAfter`), **FaceTo** (`Target` or `TargetTag`;
`SetFaceTarget` snapshots a fixed `FacePoint` — the target's eyes if a pawn,
else its spot at own eye height — so a speaker who walks off isn't tracked;
calm and standing, the actor turns at `TurnRate`×0.5 and `GetHeadLookTarget`
aims the head at that point; empty = stop; instant step), **SetOffEncounter** (`Encounter`; calls the
new `AEncounterTrigger::Fire()`, which the overlap now goes through; sets
`bSetOff`, so speakers alerted afterwards *finish* the event instead of
interrupting it), **StartEvent** (`Event`; instant). Chains:
`EventsOnFinished` / `EventsOnInterrupted`. Ending either way (`EndRun`) stops
the event's montages and calls `EndScripted()` on living speakers (patrol
resumes, facing cleared); `Alert` also calls it. An interrupt with no
`InterruptSound`/subtitle falls back to the noticer's Spotted bark. Event voices
now play through `UBarkSubsystem::PlayVoice`. Link lines: speakers purple,
move/face targets green, set-off trigger orange, started/chained events white
(interrupted chain red). Not built: a Play Sound step. *(Stage 2: User-tested 2026-10-25.)*

**Enemy barks (2026-10-21):** seven types (`EBarkType`: Spotted, LostSight,
Reloading, Hurt, AllyDown, Grenade, Death). Data: `UBarkSet` (one voice, one
language: per type `FBarkLines` = sounds, `Chance`, `Cooldown`) grouped by
language code in a `UBarkVoice` (`Languages` map, falls back to `en`). An enemy's
`BarkVoice` (class default; a trigger spawn's `Voice` overrides). `UBarkSubsystem`
(world subsystem) gates every `AEnemyBase::Bark(Type)`: player within
`HearingRange` 3000 (out of earshot doesn't spend the cooldown), level-wide
per-type cooldown, chance, one bark per speaker (Death cuts it off), at most
`MaxConcurrent` 2 at once (Death always plays), no line twice running.
`SetLanguage(FName)` swaps language. No subtitles. Voice plays via the shared
static `UBarkSubsystem::PlayVoice` (head, 3D, 400/2500 falloff; takes a pitch
and a volume multiplier since 2026-10-23). **Variation (2026-10-23):** each
enemy gets a `VoicePitch` from its voice's `PitchMin`–`PitchMax` (0.92–1.08)
when it gets the voice (`BeginPlay`, `SetBarkVoice`) and keeps it for every
line — barks and scripted `AEncounterEvent::Say` lines — so one clip set
reads as several men and each stays himself; `TryBark` adds ±`PitchJitter`
(0.03) and down to −`VolumeJitter` (0.15) per bark so a repeated clip never
lands identically. Scripted lines take the pitch only. A pitch shift also
stretches the clip (0.92 ≈ 8 % longer), part of the effect. Clips: mono
WAV, 48 kHz 16-bit, silence trimmed. **Volume (2026-10-24):** every bark
line — the 7 English waves in `/Game/Audio` and the 36 Tagalog ones under
`/Game/Dialog/Tagalog` — uses Sound Class `/Game/Audio/SC_Barks` (a
standalone duplicate of the engine's `Voice`, no parent), so its *Volume* is
the one knob for all barks, multiplying each wave's own Volume. New bark
lines need the class set too (Property Matrix → Sound Class). Hooks built: Spotted (first sight after an
alert, re-armed after `WarningBurstResetTime` unseen; flag set even when the
coordinator drops it), Hurt (non-lethal damage), Death (`Die`), Reloading
(enemy reload start), LostSight (the moment the Spotted flag re-arms, only if
it had seen the player and the player isn't dead), AllyDown (`Die` → nearest
alerted ally within `AllyDownRadius` 1500 with eye-to-eye line of sight),
Grenade (a fused grenade's first bounce → nearest alerted enemy within
`AGrenade::WarnRadius` 800; impact rounds never warn). Barks are voice only;
no behaviour reacts to them. Test set: `/Game/Audio/ThugTest_BarkSet` +
`ThugTest_BarkVoice` on `BP_EnemyBase` (clips currently stereo; mix to mono
for proper 3D).

**Pitch spread (2026-10-24, user: random rolls could land two enemies on almost
the same pitch):** `UBarkSubsystem::AssignPitch(Speaker, Voice)` hands the
pitches out. It tracks each living speaker's pitch per voice asset
(`AssignedPitches`, weak pointers) and gives a new speaker the emptiest spot in
the range: the first is random, then the two ends, then the middle of the
widest gap, ± `PitchSpreadJitter` (0.3 of the clearance, on `UBarkVoice`) so the
spacing isn't mechanical. `AEnemyBase::RollVoicePitch` asks for it; `Die` calls
`ReleasePitch` after the death bark so respawns reuse the gaps; destroyed
speakers are pruned on the next release. Per voice, because only speakers
sharing a clip set can sound alike. Caveat: the per-bark `PitchJitter` (±0.03)
can blur neighbours once a voice has more than ~5 living speakers in the
0.16-wide range — widen the range or lower the jitter for crowds. *(Tested by the
user 2026-10-24.)*


## Background music (2026-10-24)

User: "make a bgm system. one that plays background music, and can crossfade
in a trigger" — "also does not get affected by time dilation". Code:
`Gameplay/MusicSubsystem.h/.cpp`, `Gameplay/MusicTrigger.h/.cpp`.

- **`UMusicSubsystem`** (world subsystem, one per level):
  `PlayMusic(Track, FadeTime = 2, Volume = 1)`, `StopMusic(FadeTime)`,
  `GetCurrentTrack()`, all Blueprint-callable. One track at a time: the
  playing one fades out (`FadeOut`, held in `FadingOut` until silent; each
  destroys itself) while the new one fades in from a fresh `CreateSound2D`,
  both on `EAudioFaderCurve::Sin` (equal power, no dip in the middle). The
  same track again carries on rather than restarting; None fades to
  silence; `FadeTime` 0 is a hard cut. A level reload (death) starts the
  music over.
- **Out of slow motion.** The Focus's slow-mo sound is
  `SetGlobalPitchModulation`, which every sound gets **except UI sounds**
  (`FSoundSource::UpdateCommon`, `Audio.cpp`). The music's components are
  `bIsUISound` — `CreateSound2D` already sets it; the code sets it again
  because it's the reason. Fades run on the audio device's
  `GetGameDeltaTime()` = `FApp::GetDeltaTime()`, which time dilation doesn't
  touch, so a crossfade takes the same real seconds in slow motion. Side
  effect: UI sounds play through pause, which suits music.
- **`AMusicTrigger`** — a blue box on the encounter-trigger pattern
  (`Trigger` profile, player pawn only, editor label "MUSIC" + track,
  audio-component sprite). `Track` (None: fade out), `FadeTime` 2,
  `TrackVolume` 1, `bTriggerOnce` (on), `bPlayAtStart` (fires in
  `BeginPlay`: a level's opening music). `Fire()` is Blueprint-callable for
  level scripts.
- **Assets:** tracks in `/Game/Audio/BGM` (`DarkCrimes` so far); tick
  Looping on a wave for music that carries on. Planned: an `SC_Music` sound
  class as the overall music level, like `SC_Barks`.
- **Later, if wanted:** a Play Music step for scripted events; combat /
  explore intensity layers; music that carries across level loads.
- *User-tested 2026-10-25* (start track, fade-out trigger, unaffected by slow motion).


## Level exit (2026-10-24)

The slice brief's one required new code (build order step 5). User: "Go with
exit trigger. Dont drop it on the map, thats a test for later." Code:
`Gameplay/LevelExitTrigger.h/.cpp`. Not placed in any level yet.

- **`ALevelExitTrigger`** — a green box on the encounter-trigger pattern
  (`Trigger` profile, player pawn only, editor label "EXIT" + where it goes).
  Once only; ignored if the player is already dead. `Fire()` is
  Blueprint-callable for level scripts.
- **On the way out:** `SetCanBeDamaged(false)` (the engine flag
  `ABopisCharacterBase::TakeDamage` already honours through `Super`), so a
  last bullet can't start the death restart; `DisableInput` on the pawn;
  the player's `UFocusComponent::StopFocus()`;
  `UWidgetLayoutLibrary::RemoveAllWidgets` (HUD, subtitles, an open weapon
  wheel); a camera fade to black over `FadeTime` 1.5 s, held; the music out
  over the same (`bFadeOutMusic`, through `UMusicSubsystem::StopMusic`);
  then `CompleteWidgetClass` (any UMG widget — a "level complete" card —
  drawn over the black, since the camera fade darkens only the 3D picture).
- **The load:** after `LoadDelay` 3 s (never before the fade ends), counted
  in real seconds on `FApp::GetDeltaTime()` like the death restart, then
  `OpenLevelBySoftObjectPtr(NextLevel)` — a `TSoftObjectPtr<UWorld>`, so
  the next level isn't loaded with this one — or, with none, this level
  again from the top.
- **Later, if wanted:** an exit that waits for the room to be cleared; a
  results card (time, kills); checkpoints (the brief: only if a restart
  from the top proves too punishing).
- *User-tested 2026-10-25.*


## NPC characters (CC2)

*(2026-10-21, branch `feature/CC2_Integration`.)* NPC looks come from
CharacterCustomizer2's **CCMH** set, migrated under `/Game/CharacterCustomizer/`.
**Option B (user):** the CC body is the gameplay mesh itself — `ABP_Player`,
hit bones, physics and weapon attachment all run on it.

- **Assembly** (`BP_Enemy_CC.BuildCCCharacter`, from the construction script):
  body = the character Mesh (`CCMH_Body_Male`, component tag **`Character`** —
  CC finds meshes by tag); adds CC's `QualityLevel` (CC's apparel/hair lookup
  returns nothing without one) and `CharacterCustomizer`; adds a head
  (`CC_SkelMesh`, tag **`Head`**, attached to the body, `CCMH_Head_AnimBP` =
  CopyPoseFromMesh from the attached parent + face poses); creates MIDs for
  head then body materials into the customizer's `Character Materials`; then
  `ApplyVariablesToCharacter(Preset.DefaultOptions)`. Apparel and hair
  components are created by CC (`Apparel_<slot>` / `Hair_<slot>` tags,
  leader-posed to the body). A property read on a literal object in a BP graph
  reads `self` — the preset must be a variable (`Preset`).
  **Body and head from the preset (2026-10-24):** `BuildCCCharacter` (both
  `BP_Enemy_CC` and `BP_Player_CC`) sets the body mesh to `Preset.Body` and
  the head to `Preset.Head` (`CC_Preset_DataAsset`'s soft references, loaded
  with `LoadAssetBlocking` first so they can't resolve to nothing), so a
  female preset makes a female character; the mesh set on the Blueprint is
  only the editor default. Verified: a placed `BP_Enemy_CC` with the female
  preset built `CCMH_Body_Female` + `CCMH_Head_Female` (viewport check), and
  male enemies and the player still build as before (PIE).
- **Skeleton:** `CCMH_Skeleton` ⊇ UE5 Manny's bones except `ik_*` (to add on
  the body meshes by hand). Compatible both ways with `SK_Mannequin`; CCMH also
  lists the Shotgun, Dodge, Dodge-Prone and Kamz pack skeletons
  (compatibility isn't transitive).
- **Sockets:** enemies attach guns to `HandGrip_R` / `HandGrip_L` (Manny mesh
  sockets, not `hand_r`); copied onto `CCMH_Body_Male` with Manny's transforms
  (+ `foot_l/r_Socket`). Without them the gun sits at the mesh origin (feet).
  `ik_*` bones added to `CCMH_Body_Male` by the user (2026-10-21).
- **Physics:** `PA_CCMH_Bopis` = copy of `PA_Mannequin` (bone names match)
  on the body meshes; the player's `PA_CCMH_Player` (copy of `PA_Kamz`) as a
  mesh override. **Corpse asset swap (2026-10-23, mechanism kept, unused):**
  `ABopisCharacterBase::RagdollPhysicsAsset` (Health|Riddled; **empty on
  every Blueprint**) is swapped in by `StartRagdoll` — `SetPhysicsAsset(…,
  true)` after the motors are cleared, before `SetSimulatePhysics` — so a
  corpse can ragdoll on a different asset than the one serving hits,
  staggers, the riddled upper body and the dive's limbs. Verified working
  with `PA_CCMH_Player` as the corpse asset. **CC's own `CCMH_Body_Physics`
  was tried and rejected:** it's a cloth-collision asset (18 bodies, toes
  but no feet, no clavicles, no projection or constraint profiles) and our
  impulse-driven deaths stretch it into the "stuck in a door" look on flat
  ground. The first "looks better" verdict was a false positive — placed
  enemies keep their own copy of a Blueprint default the bridge changes, so
  they were still dying on `PA_CCMH_Bopis` until the editor restarted.
- **Looks** (`BuildCCCharacter` → one of three): `bUseSavedLook` + `Look`
  (a `CC_Saved_Variables`, for heroes); `bRandomizeLook` → `RandomizeLook`;
  else `Preset.DefaultOptions`. The head ticks after the body
  (`AddTickPrerequisiteComponent`) so its copied pose doesn't lag a frame (the
  neck seam in motion).
- **Random rules** (`RandomizeLook`): CC's `RandomizeAll` (face sliders
  N(0,0.2), freckles, skin tint, lips), then all `shp_head_*` cleared → one
  `shp_head_asian_0[1-3]` at 1−m plus one `shp_head_mixed_0[1-3]` at m (m ≤
  `MixedShapeMax` 0.35); a skin set from the preset's `color Textures`; eye/hair
  colour from the preset's random picks; hair/brows from `Hairstyles` /
  `Eyebrows`, a beard from `Beards` at `BeardChance` 0.3; an outfit from
  `Outfits` (rows of the preset's outfit table) via CC's `RandomOutfit`.
  A **role = a child Blueprint** with its own defaults: `BP_Enemy_CC_Thug`
  (`PH_Street_Thug`), `BP_Enemy_CC_Goon` (`PH_Goon`).
- **Preset `CCMH_Preset_PH_Male`** (`/Game/Characters/CC/Presets/`): Asian;
  skin tones 03 (light tan) + 02 (medium brown) of the five; the apparel pack's
  `+` tables; hair blacklist (afros, bobs, female long/ponytail, `Short_01`);
  outfits `DT_Outfits_PH_M` = Formal, Police_Officer, Manual_Labor,
  Retail_Worker + placeholder `PH_Street_Thug` / `PH_Goon` (design to tune).
- **Preset `CCMH_Preset_PH_Female`** (2026-10-24; female civilians): copy of
  CC's `CCMH_Preset_Female_01` — female body/head, Asian, skin tones 03 + 02
  (the skin textures are shared between genders), the female `+` apparel
  tables, the stock female hair blacklist (no male styles, beards or afros),
  voice Female1. Outfits `DT_Outfits_PH_F` = `DT_Outfits_F+` minus
  Casual_Fall/Winter, Weatherproof (climate), Pyjamas, Beachwear, Club,
  Police_Officer (not a civilian): Casual_Spring/Summer, Street, Sporty,
  Formal, Corporate, Business_Casual, Retail_Worker, Medical_Staff — a
  placeholder set, design to tune. Its default face is the stock one;
  `RandomizeLook` applies the Asian head shapes. No civilian Blueprint yet:
  a civilian role needs its own female `Hairstyles`/`Eyebrows`/`Outfits`
  lists and `BeardChance` 0 (the role lists live on the Blueprint).
- **Creator level `/Game/Characters/CC/Lvl_CharacterCreator`** (from CC2's
  apparel demo level): GameMode override `CC_GameMode`, a TargetPoint tagged
  **`CC Start`** on the floor (z 50, yaw 0) where CC spawns its customizer pawn;
  `CC_Customizer_Pawn`'s Default Preset = the PH preset (CDO changed). Hero
  workflow: play it, customize, then (still playing) select *CC Customizable
  Character* → *Character Customizer* → right-click *CC Saved Variables* →
  Copy; stop; in the hero Blueprint set `bUseSavedLook`, paste into `Look`.
  (CC's own save slot is keyed by platform user / player id — one per user.)
- **Player `BP_Player_CC`** (child of `BP_PlayerCharacter`; Kamz is being
  retired, so his overrides were copied: Focus `MinMeterToActivate` 20,
  Shootdodge `DiveLift` 375, Roll `CrouchOutAfter` 0.475, Health `MaxHealth`
  150, WeaponHolder pistol start + 5-gun loadout, `bStartWithFullAmmo` off;
  no actor-level differences): mesh `CCMH_Body_Male` tagged `Character`,
  `PhysicsAssetOverride` = `/Game/Characters/CC/PA_CCMH_Player` (copy of
  `PA_Kamz`; its editor preview mesh still names `SKM_Kamz` — set it to
  `CCMH_Body_Male` in the Physics Asset editor); same `BuildCCCharacter` /
  `RandomizeLook` as the enemy; placeholder random look (`PH_Goon`, beard 50%)
  until the protagonist's `Look` is authored. Played in `Lvl_Sandbox`, clean.
  Not the default pawn — set `BP_GameMode` DefaultPawnClass to use it.
- **Skin through clothing:** CC hides the body under clothes by pushing skin
  inward (WPO) via per-slot `ApparelMask_<slot>` textures from each apparel
  row's `Mask` (open footwear has none). Our animations push poses further than
  CC's own, so `MI_Skin_Body_CCMH` push strengths were raised: **the head mesh has its own copy** (`MI_Skin_Face_CCMH` — the head
  carries the neck, upper chest and upper back, and gets the same masks), so
  both must be raised: Upper Body_Mask_Mult 3 → **7** on both; body Lower 3 →
  7, Footwear 1 → 2 (2026-10-21). The value is roughly cm of inward push: at
  15 the shoulders cross through and balloon out (tested live); keep ≤ ~8. `Tank_Top_01` / `Gym_Top_01` had no mask (skin through the
  tank top on ragdolls): now `T_ApparelMask_Top` (male `+` and base tables). Too high dents
  the skin at sleeve/hem edges.
- **Head skin pushed behind clothing by depth (2026-10-22):** most visible
  clipping is the head mesh below the neck (collarbones, upper chest/back).
  `M_Skin_CCMH` now runs its attributes through a Break → Make passthrough and
  adds **`Clothing Depth Bias`** (scalar, group Apparel, default 0) ×
  `Neck_Mask`.R to PixelDepthOffset: those pixels depth-test as if that many
  cm further from the camera, so cloth within that distance wins; nothing is
  hidden, so open collars can't show holes. `MI_Skin_Face_CCMH` = 2,
  `MI_Skin_Body_CCMH` = 0 explicitly (it inherits from the face MI, and the
  neck mask means nothing on the body's UVs). The body has its own term,
  **`Body Clothing Depth Bias`** × max(`Depth Region`, `ApparelMask_0/1/2`):
  `Depth Region` is a texture parameter defaulting to CC's
  `T_ApparelMask_TShirt` (torso + shoulder caps), so the torso is covered
  whatever is worn — tank tops included, whose own mask is near-empty — and
  the worn items' masks add legs/feet/sleeves. Body MI = 2, face MI = 0.
  Hands are deliberately outside it (a held gun would draw over the fingers).
  *(Since 2026-10-25 these are a WPO along the camera ray, not PDO — see
  "Skin push by WPO" below.)*
  Backup:
  `/Game/Characters/CC/Backup/M_Skin_CCMH_Original`.
- **Skin push by WPO, not Pixel Depth Offset (2026-10-24/25; user: "I can
  see seams in all the cc models if they have their skin exposed").** The
  three skin pushes below (head neck, body torso, waist band) were PDO.
  PDO also moves where a pixel is *lit* (deferred lighting rebuilds the
  position from depth), so pushed bare skin shadowed itself and its
  subsurface scattering showed through orange: a line where the head mesh
  meets the body across the upper chest, a line above the navel (the waist
  band's top), orange forearms on the female body (its A-pose forearms sit
  inside the waist band). Zeroing the biases removed all of it
  (user-tested). **Tried and dropped:** gating the pushes by the worn
  items' masks. On the head the body-layout masks read through the head's
  UV0 lit random areas (dark patches on the head's shoulders); a `Neck
  Shrink` gate fixed that. But on the body the masks are coarse (a one-piece
  swimsuit and the dresses use upper-body masks), and in the waist band
  every garment is pushed back 1.5–4.5 cm, so wherever a mask fell short the
  skin sorted in front and punched ragged holes through the garment (user
  screenshot). **Now:** the original always-on terms (`Depth Region`
  T-shirt mask on the torso, the band, `Neck_Mask` on the head; values face
  2, body 2 and 3.5) sum in `Add_1`→`Add_2`→`Add_4` and drive a **WPO along
  the camera ray** — `normalize(WorldPosition − CameraPositionWS)` × sum
  (`WorldPosition_1` set to exclude shader offsets, `Subtract_9`,
  `Normalize_0`, `Multiply_44`), added to CC's own WPO in `Add_5` → the
  Make node's WorldPositionOffset. WPO moves the surface itself in the
  shadow pass too, so lighting stays consistent while the sorting is the
  same as 2026-10-22's. The band comes straight from `MF_ApparelWaistBand`
  (vertex shader; `VertexInterpolator_0` unused). The Make node's
  PixelDepthOffset is CC's own again, through a ×1 `Multiply_45` (the bridge
  misreports every Make input fed by the Break node as "BaseColor"; a
  pass-through reads back reliably). Backups: git (`111a1187`, before any of
  this) and file copies. (The orange in the creator level is its
  body-selection highlight, not shading.) **Known leftover:** female
  forearms in the A-pose still fall inside the band, so an arm very close in
  front of a jacket at the hip could tuck behind it; tighten the band if it
  shows. **User-tested 2026-10-25:** seams and patches gone on bare skin,
  "clothes fixed".
- **CC parts cast shadows on each other (2026-10-24).** CC's component class
  `CharacterCustomizer_Core/Data/CC_SkelMesh` — the class CC creates heads,
  apparel and hair as (`CharacterCustomizer`, `BP_Enemy_CC`, `BP_Player_CC`
  are its only users) — had **Self Shadow Only** on, so each part shadowed
  only itself: the head's shadow stopped dead at the head/body seam on the
  shoulder (user screenshot), hair didn't shadow the face, clothes didn't
  shadow skin. Unticked on the class by the user and saved; the class
  default now reads off. Parts already built keep the old value until their
  character rebuilds (restart PIE, nudge a placed one).
- **Clothing layer order at the waist (2026-10-22):** every garment carries a
  **`Layer Depth`** index on its MI (CC's apparel master
  `M_Base_Material_Apparel`, group Layering, default 0): **0** outer (jackets,
  vests, waistcoat, apron, overalls, tie, open overshirt), **1** untucked top
  (and the inner tees of jackets), **2** pants/shorts/underwear, **3** tucked
  top (`MI_Shirt_01` — also the shirt under the waistcoat and suit jacket —
  and `MI_Police_Shirt_01`, both police shirts). Inside the waist band the
  garment is pushed `Layer Depth × Layer Spacing` (1.5 cm) away from the
  camera, so outer layers win close overlaps and tucked vs untucked is one
  number per item.
  - **Waist band** = `/Game/Characters/CC/Materials/MF_ApparelWaistBand`:
    rest-pose height 78–110 cm (fading to 0 at 70 / 118) × within 24 cm of
    the centre line (fading to 0 at 30), from PreSkinnedPosition, so A-pose
    cuffs and hands stay out and sleeve/ankle/neck hems over bare skin are
    untouched (a push there would let the skin draw over the hem).
  - **Push = WPO along the view ray** (`normalize(WorldPosition −
    CameraPositionWS)` × amount): moves each vertex straight away from the
    camera, so it lands on the same pixel with greater depth. Pixel Depth
    Offset was the plan, but the bridge can't connect `MP_PixelDepthOffset`
    (enum conversion bug); it could be swapped in by hand.
  - **Skin:** `M_Skin_CCMH` adds `Waist Layer Depth` × the band (through a
    VertexInterpolator — PreSkinnedPosition is vertex-only) to its PDO *(since
    2026-10-25: to its camera-ray WPO, straight from the function)*; body MI
    3.5 (+ its 2 = 5.5 > the tucked top's 4.5), face MI 0.
  - **Tucked classification:** rest-pose hem height vs the jeans' top (108.7
    cm): tucked tops end above it (Shirt_01 101, Police A 99, Police B 103),
    untucked ones hang to 79–93. New tops: check the same way.
  - **Female pass (2026-10-24):** same values by garment type, set by full
    asset path (male and female MIs share names: two `MI_Shirt_01`, two
    `MI_Jeans_Blue`…). Female waist = 103 cm (police pants 116). **0**
    jackets/cardigan/vest/blazers/apron/lab coat; **1** tees, sleeveless,
    turtleneck, sweater, pullover, hoodies, sweatshirt, jersey,
    tracksuit/pyjama/nurse tops, **dresses, swimsuits**; **2** everything in
    the lower-body table (pants, shorts, **skirts**, tights, underwear,
    bikini bottoms — it wins a material shared with a top); **3** Shirt_01,
    the bow blouse, police shirts, corset, crop tops, sports bra, strap tops
    (hems at or above the waist). Inner garments keep their own value — the
    female blazer wears the **male** `MI_Shirt_01`, which stays 3. 67 MIs;
    5 skipped because they aren't apparel-master children (lingerie
    pattern/trim, `MI_Dress_Ada`, pantyhose, torn denim).
  Backup:
    `/Game/Characters/CC/Backup/M_Base_Material_Apparel_Original`.
  **Rejected — hiding skin under clothing** (masked opacity from the apparel
  masks on the body / `Neck_Mask` × `Neck Shrink` on the head; tried and
  rolled back 2026-10-22): `neck Shrink` is per item on/off, so open-collar
  tops lost chest skin, and the body masks cut holes at tank-top armholes.
- **Apparel pack everywhere:** all six stock CC presets now use the pack's `+`
  apparel/outfit tables (the `+` apparel tables are supersets of the base ones;
  the base outfit rows Casual1–4/Formal2–4 are not in `+`). The customizer's
  Apparel menu lists the preset's `DT Apparel`. `CC_Customizable_Character`
  Presets list starts with `CCMH_Preset_PH_Male`.
- **Not yet:** body proportion sliders (CC drives them with ModifyBone in its
  `CCMH_Body_AnimBP`, unused under Option B); a civilian Blueprint for the female
  preset (female characters are civilians plus one story character — user,
  2026-10-24; lore doc *Female characters*). The female body, head, preset
  and clothing layers are done (2026-10-24).
- **Cost:** dressed character ≈ 30k verts LOD0 (body 7.3k, head 4.9k, items
  2.5–5.3k), 4–5 LODs per part, ~12 draw calls (head has 6 sections), 35 head
  shape targets; skin textures 4K (cap to 1–2K for the Deck).

## Enemies

Rewritten 2026-09-30 for the Aswang direction. *(The Aswang were dropped 2026-10-09: the five Aswang-specific
sections from "Three families" to "Readability layers by distance" are marked
superseded; the systems built since are for human enemies.)* Lore in
`Design Document/Lore_And_Design_Notes.md` PART 1; the decisions below came
out of a design conversation on 2026-09-28/30 and are implementation-side.

- The template's `ShooterNPC`/`ShooterAIController` were removed with
  `Variant_Shooter` — this gets built fresh, not extended from that code.
- New base enemy actor, with movement, attack behaviour and battlefield role
  as data-driven, combinable pieces, instead of one class accumulating
  `if (Type == Enforcer)`-style branches.
- Per-archetype StateTree assets (the plugin is already enabled) are a better
  fit than one shared tree with branching conditions for every archetype.
- Enemy *count* and aggressive positioning matter more than individual enemy
  sophistication. Halo 2's AI notes in [Research.md](Research.md) still apply
  — they're about readable behaviour, not about what the enemies are.

> ⚠ **2026-10-09: the Aswang are dropped (user).** The families, two-layer
> health rationale, vocalization and readability sections below were built on
> them and are **not current** until the new enemy design lands. The Phase 5
> build order (user, same day) does not depend on any of it:
> 1. a shared character base, so enemies inherit the player's animation and
>    weapons;
> 2. basic movement;
> 3. taking bullets and ragdolling.
>
> Enemy shooting comes later.

### Built so far (2026-10-09) — steps 1–3, user-confirmed in PIE

**Class tree**
```
ACharacter
 └─ ABopisCharacterBase      BopisCharacterBase.h
     ├─ AProjectBopisCharacter   the player
     └─ AEnemyBase               Enemies/EnemyBase.h
```

**`ABopisCharacterBase`** — everything the AnimBP and weapons need, shared by
player and enemies:
- `WeaponHolder` component;
- the 8 montage maps (fire / off-hand / aim-fire / aim-off-hand-fire, reload /
  off-hand reload, equip / off-hand equip);
- `bIsAiming` + `SetAiming(bool)`, `TimeUntilWeaponLowered` / `LowerWeaponDelay`,
  `IsWeaponRaised`, `IsReloadAnimating`;
- `PlayFireAnimation(Weapon)` (montage lookup + `AddRecoil`),
  `PlayReloadAnimation(Weapon)`, `PlayEquipAnimation`, `IsEquipAnimating`, the
  looping-reload driver `UpdateReloadMontage`;
- capsule 34×96 and `bCanCrouch`.

The player keeps camera, input, stances, crouch request, Focus and HUD.
`DoFire` / `DoReload` call the holder, then the base's `Play*Animation`.

**Refactor safety, worth remembering:** moving a `UPROPERTY` up into a parent
class keeps Blueprint values without redirects, because tagged-property
serialization matches by name across the hierarchy. `CreateDefaultSubobject`
moved to the parent constructor with the **same subobject name** keeps the
component. (Contrast the Focus rename, where names changed.)

**Who casts to what:**
- `UProjectBopisAnimInstance` → `ABopisCharacterBase`, so one `ABP_Player`
  drives every humanoid.
- `UWeaponHolderComponent` → `ABopisCharacterBase` (equip anim), `ACharacter`
  (attach to the mesh). `FireEquippedWeapon` stays **player-only**: it aims from
  the camera crosshair. Enemies need their own aim source when they shoot.
- Pickups and widgets stay on the player.

**`AEnemyBase`:**
- `AIControllerClass = AAIController`,
  `AutoPossessAI = PlacedInWorldOrSpawned`. Without this, a placed enemy has
  no controller.
- **Aim:** `bAimAtPlayer` → `SetFocus(PlayerPawn)` + `SetAiming(true)`.
  - The controller's focus drives the control rotation, pitch included when the
    focus is a pawn, so the AnimBP aim offset tracks with no extra code.
  - With no focus, `bSetControlRotationFromPawnOrientation` keeps control =
    facing.
  - `bStartRaised` (debug) raises the gun without focus.
- **Rotation:**
  - Raised → `bUseControllerDesiredRotation` (turn toward the aim at
    `TurnRate`, strafe).
  - Lowered → `bOrientRotationToMovement`.
  - `bUseControllerRotationYaw` stays off, because AI control rotation jumps
    instantly and would snap the body.
- **Speeds:** `LoweredSpeed` 300 / `RaisedSpeed` 250, `TurnRate` 360.
- **Test patrol** (placeholder until a StateTree):
  - `PatrolPoints` (EditInstanceOnly actors), `PatrolWaitTime` 1.
  - It polls `GetMoveStatus() == Idle`, then `MoveToActor(Point, 50)`.
  - `bCanStrafe` (default true) preserves the focus while moving.
  - A failed request logs a "no NavMeshBoundsVolume?" warning.

**Assets:**
- `BP_EnemyBase`: `SKM_Manny_Simple`, `ABP_Player`, mesh offset as the
  player, montage maps copied from `BP_PlayerCharacter`, `BP_Pistol`, the
  `HandGrip_R` / `L` sockets.
- `Enemy_Test` in `Lvl_Sandbox` with a NavMeshBoundsVolume + 3 Target Points
  (set up by the user).

**Known duplication:** the montage maps are per-Blueprint, so player and enemy
each hold a copy. If they drift, move them into a shared data asset.

### Taking bullets and dying — step 4a (2026-10-09/10, user-confirmed in PIE)

All of this lives on `ABopisCharacterBase`, so the player can die the same way
later. Values below are the C++ defaults; **the user tuned some of them on the
Blueprints**, so the BP values are the live ones.

**Hits land on bones, not the capsule.**
- The capsule ignores `ECC_Visibility` (hitscan) and `ECC_Projectile`
  (`#define ECC_Projectile ECC_GameTraceChannel1`, in `ProjectBopis.h`). The
  mesh blocks both.
- `AProjectileBase` uses the project's **`Projectile`** collision profile
  (was `BlockAllDynamic`).
- So every hit reports `BoneName` from the physics-asset body.

**Health:**
- `UHealthComponent` (`Gameplay/`), `MaxHealth` 100. `ApplyDamage` returns true
  only for the emptying blow.
- `BoneDamageMultipliers`: `head` ×4.
- `Super::TakeDamage` is called **only while alive**. On a simulating body,
  the engine would add its own `DamageImpulse` on top of ours.

**Death sequence** (`TakeDamage` routes by state):

| State | Entered when | What a hit does |
|---|---|---|
| Alive | — | Damage × bone multiplier. Health 0 → `Die`. |
| **Dying** | health hits 0 | `Die`: AI detached (`AEnemyBase` override), movement off, capsule `NoCollision`, directional death animation. Hits add to `PostDeathDamage`; ≥ `RagdollDamageThreshold` (30) → riddled. |
| **Riddled** | dying + threshold | The upper body (`RiddledRootBone` `spine_01` and below it in the hierarchy) simulates on `UPhysicalAnimationComponent` motors (world-space, strength `RiddledHoldStrength` 800, damping ×0.1). Legs stay animated; the death montage slows to `RiddledAnimRate` 0.2 and pauses short of its end. Each hit `KickBone`s the struck bone (×`RiddledKickScale` 1.5) and adds to `RiddledDamage`. After `RiddledDuration` (1 s, world time) → ragdoll launched with all of `RiddledDamage`. **Break:** damage within `OverkillWindow` (0.1 s; the triggering bullet opens the first window) ≥ `RiddledBreakDamage` (30) → ragdoll at once (a rifle round, a headshot, a blast; pistol 25 can't). |
| **Ragdoll** | riddled timeout; death anim ends; overkill | Motors cleared, full `SetSimulatePhysics`. Every hit `LaunchBody`s it. |

- **Death animation:** `DeathAnimations` (`FDirectionalAnimSet`: Front / Back /
  Left / Right arrays, random per side, Front as fallback).
  - The side comes from the shot direction in the body's frame.
  - Played with `PlaySlotAnimationAsDynamicMontage` in **`DeathSlot`**
    (`DeathGroup`), the **last node before Output Pose** in `ABP_Player` (added
    by the user), so it overrides every layer.
  - Clips: Lyra `MM_Death_*` from `Characters/Mannequins/Anims/Death/`.
  - Ending: the Tick catches it 0.1 s before its end and ragdolls, so it never
    blends back to the living pose.
- **Instant ragdoll by overkill:** the killing blow's spare damage plus every
  hit within `OverkillWindow` (0.1 s, world time, so pellets of one blast count
  even in Focus) is `BurstOverkill`. Reaching ≥ `InstantRagdollOverkill` (50)
  ragdolls straight away from any stage.
  - A full close shotgun blast or a heavy magnum kill ragdolls. A partial blast
    plays the death animation and may riddle.
  - The pistol (25) never reaches it.
  - Per-weapon instant ragdoll was considered and rejected in favour of this
    weapon-agnostic rule.
- **`LaunchBody` (Max Payne 2):** speed = `min(damage × LaunchSpeedPerDamage
  24, MaxLaunchSpeedPerHit 900)`.
  - **Whole body** (`AddImpulseToAllBodiesBelow`, velocity change) along the
    shot, plus `LaunchLift` 0.25 upward.
  - Plus the struck bone × `BoneKickScale` 1.
  - Pellets each launch, so shotguns add up.
- **`UseRagdollCollision`:** the `Ragdoll` profile, then re-block Visibility +
  Projectile.
- **`KickBone`:** impulses only reach simulating bodies. A hit on an animated
  pelvis or leg while riddled kicks `RiddledRootBone` instead.

**Assets:**
- `BP_Enemy_Test` (child of `BP_EnemyBase`) is the placed `Enemy_Test`. It
  replaced a plain `BP_EnemyBase` instance that held a stale empty
  `DeathAnimations` (see the gotcha below).
- `BP_EnemyBase` holds the death clips.

### Hit reactions while alive — step 4b (2026-10-10, built while the user was away; user-confirmed in PIE)

**Design (user):**
- **Light hit reaction** on every surviving hit: visual feedback only. The
  enemy keeps moving, aiming and (later) shooting.
- **Stagger:** X damage within X time roots the enemy in a riddled-like state,
  exposed to more fire. Retriggering restarts it, so one enemy can be
  **stun-locked**. Others can still kill you while you do it; that's the
  balance, not a rule in code.

**How:** same machinery as riddled.
- `SimulateUpperBody(HoldStrength)` puts `RiddledRootBone` (`spine_01`) and
  below it on physics with world-space motors. Riddled now uses it too.
- The legs stay animated.
- **Collision:** the living mesh is query-only (`CharacterMesh`), so
  reactions switch it to `QueryAndPhysics` and back. The mesh now ignores
  `ECC_Pawn`, so simulated bones aren't shoved by their own capsule.

| | Trigger | Body | Ends |
|---|---|---|---|
| **Hit reaction** | any surviving hit below the stagger threshold | motors at `HitReactHoldStrength` 2000 (stiff), kick ×`HitReactKickScale` 0.6. Every hit restarts it at full physics. | physics blend weight fades 1→0 over `HitReactDuration` (0.3 s), then bones back to animation |
| **Stagger** | ≥ `StaggerDamage` (60) within `StaggerWindow` (0.5 s, fixed window from the first hit; resets after each stagger) | motors at `StaggerHoldStrength` 600 (reeling), kick ×`StaggerKickScale` 1.2. `DisableMovement`; the enemy's Tick stops the AI move and skips aim / patrol. Directional `StaggerAnimations` in the full-body `DeathSlot`. | after `StaggerDuration` (0.8 s), fading over the last `HitReactDuration`; movement back to `MOVE_Walking` |

- **Interaction with death:** `Die` calls `EndHitReactions` first, so the
  death animation gets its bones back. Riddled and ragdoll then work as before.
- **Off switches:** `HitReactDuration` 0 turns light reactions off.
  `StaggerDuration` 0 turns staggers off.
- **`PlayDirectionalAnimation(Set, Dir)`:** shared by death and stagger.
  `DeathSlotName` is now the general full-body slot.
- **Stagger clips** (bridge, on `BP_EnemyBase`, `BP_Enemy_Test` and both
  placed instances): Lyra `Characters/Heroes/Mannequin/Animations/Actions/`.
  - Front: `MM_HitReact_Front_Hvy_01`, `Front_Med_01`, `_02`
  - Back: `Back_Med_01`
  - Left: `Left_Med_01`
  - Right: `Right_Med_01`
- **Expected tuning:**
  - The pistol (25) staggers on the 3rd quick round (75 ≥ 60 within 0.5 s).
  - A shotgun blast staggers alone.
  - The hold strengths are guesses until seen in PIE.

### Corpse limit — step 4c, part 1 (2026-10-10, user-confirmed in PIE)

**Rule (user):** at most `MaxCorpses` (default **5**) bodies. Past that, the
**oldest body that's out of view** is removed. Age alone never removes a body
the player can see.

- **Game mode:** `AProjectBopisGameMode`, set on `BP_GameMode`.
  - `RegisterCorpse(Actor)` is called from `AEnemyBase::Die`. Only enemies
    register, so a future player corpse won't vanish.
  - `TrimCorpses` walks oldest first and destroys out-of-view bodies until
    within the limit.
  - If every extra body is in view, a looping timer (`CorpseCheckInterval`
    0.5 s) retries, and stops once back within the limit.
  - The list holds `TWeakObjectPtr<AActor>`, so bodies destroyed elsewhere
    drop out.
- **"In view"** (`IsInView`, file-local):
  - the mesh's bounds centre is inside the player camera's cone, half the FOV
    plus the body's angular radius;
  - **and** a Visibility trace from the camera, ignoring the view target,
    reaches the body itself. Walls count as out of view.
  - **Decided against:** `GetLastRenderTimeOnScreen()`. In UE5 it kept updating
    for bodies behind the camera (Lumen and other off-screen passes), so every
    corpse read as on screen. Found with a temporary `[CorpseDbg]` log (since
    removed), read via the bridge Logs toolset because the log file had
    stopped flushing.
- **Weapons:** `UWeaponHolderComponent::EndPlay` destroys every carried weapon,
  so a removed corpse doesn't leave its guns behind. The coming weapon drop will
  take the dropped gun out of `CarriedWeapons` first.
- Removal is instant. Possible later polish: sink or fade.

### Weapon drop — step 4c, part 2 (2026-10-10, user-confirmed in PIE)

**Design (user):** the dead enemy's gun falls with **physics**, the launch is
**clamped**, and it becomes a pickup under the existing drop rule (ammo if
owned, weapon + rounds if not, duals unlocked by a second single).

- **`AEnemyBase::DropWeapon(ShotDirection)`**, from `Die`:
  - spawns an **`AWeaponDrop`** at the equipped gun's mesh transform (no
    scale, `AlwaysSpawn`);
  - throw velocity = shot direction × `WeaponDropSpeed` 250 + up × `WeaponDropLift`
    150, **`GetClampedToMaxSize(MaxWeaponDropSpeed 400)`**, spin `FMath::VRand()` ×
    `WeaponDropSpin` 360°/s;
  - the in-hand weapon is `SetActorHiddenInGame`; its actor stays with the
    corpse until corpse cleanup.
  - Empty `WeaponPickupClass` = enemies keep their guns. Set to
    `Pickups/BP_WeaponPickup` on `BP_EnemyBase`, `BP_Enemy_Test` and the placed
    instances.
- **`AWeaponDrop`** (`Pickups/WeaponDrop.h`):
  - root = `UBoxComponent` `Body`, `PhysicsActor` profile, ignoring
    Pawn / Camera / Visibility / Projectile, simulating;
  - `MeshComponent` takes the weapon's mesh from its class defaults;
  - **`Launch`** fits the box to the mesh's local bounds, centres it, and
    offsets the actor (`TeleportPhysics`) so the gun doesn't jump;
  - **settles** once its speed stays < `SettleSpeed` 20 for `SettleTime` 0.25 s
    in a row (after `MinFlightTime` 0.3 s), or at `MaxFlightTime` 3 s;
  - **ignores `ECC_PhysicsBody`**, so it never comes to rest on a ragdoll;
  - then **`BecomePickup`**: snaps to the floor, then
    `SpawnActorDeferred<AWeaponPickup>` at the mesh's transform, then
    `SetWeaponClass`, then `FinishSpawning` (so `OnConstruction` sees the
    class), then destroys itself.
    - The floor snap is a `LineTraceSingleByObjectType` (WorldStatic +
      WorldDynamic) down `FloorSnapDistance` 150 from the bounds centre. It
      lowers the pickup by `Hit.Z − Bounds.Min.Z`.
  - **Floating-pickup bug (fixed):** a single-frame speed check caught guns at
    the top of a bounce, and drops landed on corpses that later moved or were
    cleaned up. Pickups don't simulate, so either left them hanging.
- **Why a separate class:** physics needs the moving body as the actor's root.
  Re-rooting `AWeaponPickup` would move every placed pickup to the origin. The
  drop flies and hands over to an untouched pickup.
- **Rounds** follow the pickup's `AmmoMode` (BP default: random, half to full
  magazine). Duals drop as one pickup showing a single pistol mesh.
- **`DropAsClass` (2026-10-14):** what a weapon turns into when an enemy drops
  it (`Weapon|Drop`; empty = itself), read through
  `AWeaponBase::GetDropClass()` by `DropWeapon`. For enemy-only variants:
  `BP_Pistol_EnemyOnly` (the user's copy, differing only in `AnimType`) drops
  as `BP_Pistol`.
- **Per-enemy weapons:** `UWeaponHolderComponent::StartingWeaponClass` is now
  **`EditAnywhere`**. Select a placed enemy → WeaponHolder → Starting Weapon
  Class. The BP value is the default.
- The gun leaves the hand at the moment of death; the death animation plays
  empty-handed (the Max Payne convention).

### Focus refill on kills — step 4c, part 3 (2026-10-10)

- **`AEnemyBase::Die`:** if `Killer->GetPawn()` is an `AProjectBopisCharacter`,
  `GetFocus()->AddMeter(KillRefill)` (20, set on `BP_PlayerCharacter` → Focus).
  - The killer arrives through the damage chain: the holder sets the weapon's
    instigator, and hitscan and projectiles pass `GetInstigatorController()` to
    `ApplyPointDamage`.
  - Kills by other enemies won't refill anything once enemies shoot.
- **`bPassiveRegen` is now off** on `BP_PlayerCharacter` (bridge). Focus is
  earned by kills.
- `bInfinite` was **on** for the player (the user's testing setting). It must
  be off to see the refill.

**Step 4 is complete.** Player death followed on 2026-10-13 (see *Player
death* below).

### Enemy shooting — step 5 (2026-10-13, user-confirmed in PIE)

> ⚠ **The accuracy model below was replaced the same day by the hit-chance
> model** (*Enemy shooting v2*, after *Player death*).
> - **Replaced:** per-enemy accuracy build-up, growth scales, the
>   close-range floor, the dive cap and post-dive reset, and the miss disc.
> - **Still current from this section:** sight, the trigger (and suppressive
>   fire), the no-x-ray aim, leading, bursts, ammo, and the gotchas.

**Design (user's spec, "start with this"; amendments per player action to come):**
- Each enemy has an **accuracy**, 0..1:
  - it starts low;
  - with the player in sight, it grows the longer they stay visible;
  - out of sight ("breaking cover"), it drains gradually.
- **A moving player** slows the growth. It started as a lower cap plus slower
  growth. **Since 2026-10-13 there's no cap:** "the enemy can always get full
  100% accuracy, movement will just slow the accuracy increase (… 33%
  initially)."
- **Misses** are real bullets. "Variablize as much as possible."
- **The user later added:**
  - Misses are limited **vertically**, so the enemy doesn't shoot the ground
    in front of itself.
  - **The penalty for movement must be the same at any distance.** "The aim
    is to force the player either to find cover or be in constant motion."
  - **Running straight at or away from the enemy** makes you easier to hit
    than strafing.
  - **Close range is risky:** moving up close still gets you killed.
    "Shootdodging and rolling (later on) is the way to fight up close."
  - **The dive gets its own cap,** now 25%, for the flight only. "Lying
    prone for long periods will kill you, its the vulnerability window."
  - **Enemies lead their shots,** after "even at 100% I can still dodge
    bullets".
  - **Landing resets the enemy's accuracy to 25%:** "after the shootdodge,
    reset the accuracy to 25%".

**Code (`AEnemyBase::UpdateShooting`, each tick, alive and not staggered):**
- **Aim point:** the player's `GetMesh()` `spine_03`, or the actor location
  if the skeleton has no such bone.
- **Sight (`CanSeePlayer`):** a Visibility trace from the enemy's `head` to
  that point, ignoring itself and its weapon. It counts as seen if it reaches
  the player or hits nothing. **A dead player counts as unseen**, so enemies
  stop firing at the body.
- **Accuracy:**
  - **Effective speed** = sideways speed + `RadialSpeedWeight 0.3` ×
    straight-line speed. It uses the player's horizontal velocity relative to
    the enemy, split along the line between them, and has no distance term.
    The debug readout's cm/s is this number.
  - `GrowthScale = lerp(1, MovingGrowthScale 0.33,
    clamp(effectiveSpeed / MovingSpeedForFullPenalty 500))`;
  - **Seen:** `Accuracy = min(MaxAccuracy 1.0, Accuracy +
    AccuracyGrowthPerSecond 0.05 × GrowthScale × dt)`. There's no movement
    cap: moving only slows the build-up. Full speed takes about 55 s from 10%
    to 100%; standing still takes 18 s.
  - **Down after a dive** (the landing, prone and get-up phases:
    `IsBodyDown() && !IsAirborne()`, or `IsGettingUp()`): `GrowthScale =
    MovingGrowthScale`, even when the body is still. The user asked for it on
    2026-10-13: a low, small target is harder to settle on. The wind-up
    builds at the normal rate.
  - **Unseen:** − `AccuracyLossPerSecond 0.1`, down to `InitialAccuracy 0.1`.
    Accuracy is set to `InitialAccuracy` in `BeginPlay`.
  - **Not alerted:** it counts as unseen, so nothing builds (see *Gunman
    behaviour v1*).
  - **Landing from a dive:** when `IsEvading()` goes from true to false (the
    flight ended), `Accuracy = min(Accuracy, AccuracyAfterShootdodge 0.25)`.
    Every enemy ticking `UpdateShooting` does this, seen or not; a staggered
    one misses the frame. It's tracked with `bPlayerWasDodging`.
- **Shot accuracy** is worked out per tick from the stored accuracy. Neither
  rule below changes the build-up:
  - **Evading** (`AProjectBopisCharacter::IsEvading()`, currently
    `Shootdodge->IsAirborne()`, which means the Start/Loop flight):
    `min(Accuracy, ShootdodgeMaxAccuracy 0.25)`.
    - Wind-up, landing, prone and get-up are not evading: they're the
      vulnerability window.
    - Rolls go into `IsEvading()` when they exist.
  - **Otherwise:** `max(Accuracy, CloseRangeFloor)`. The floor is
    `CloseRangeAccuracy 0.85 × closeness`, where closeness is 1 within
    `CloseRange` (500 cm) and fades linearly to 0 at `CloseRangeFadeEnd`
    (1200 cm). The distance is measured from the enemy's actor to the aim
    point. All three values are per enemy, so a shotgunner can be short and
    brutal and a rifleman long and gentle.
  - The readout adds `CLOSE xx%` or `DIVE xx%` while either applies.
- **Trigger:** only with `bShootAtPlayer`, the enemy alerted, the player seen
  **or being suppressed**, the gun raised, and not equipping or reloading.
  (`bAimAtPlayer` was replaced by awareness on 2026-10-13.)
- **Suppressive fire** (user, 2026-10-13):
  - For `SuppressFireDuration 2` s after losing sight (`TimeSinceSeenPlayer`),
    it keeps firing bursts at `LastKnownPlayerLocation + 40` (chest height).
  - These shots use the stored, draining accuracy, with no lead and no
    close-range floor.
  - **0 turns it off:** "trained" enemies will hold fire instead.
  - Alerted by gunfire without seeing the player (`Alert` seeds the last
    known spot and the timer), it suppresses toward the noise for the same
    window.
  - The readout says `SUPPRESS`.
- **Aim (`UpdateAim`), no x-ray** (user, 2026-10-13: "aiming at me through
  the wall"):
  - `SetFocus(Player)` only while `TimeSinceSeenPlayer ≤
    TrackThroughCoverTime 0.3`.
  - After that, `SetFocalPoint(last known + 40)`, so it covers the corner
    where the player vanished.
  - Within 2 m of that spot (searching), the focus clears and it faces its
    travel, gun still up.
- **Hearing after the alert** (user-confirmed 2026-10-13; "you can shoot
  behind a wall and hes not gonna know that you are there"):
  - `ABopisAIController::OnTargetPerceived` calls
    `AEnemyBase::HearPlayer(Stimulus.StimulusLocation)` when the heard noise's
    actor is the player. Allies' gunfire only alerts the unaware.
  - `HearPlayer` (alerted, alive) sets `LastKnownPlayerLocation` to the
    sound. The aim then covers it, and searches go there.
  - **No return fire at a sound:** the user removed that ("remove the
    suppress bit, just search the area"). Suppression is after losing sight
    only.
  - **Gunman Move [Last Known Position]** with `bFollowNewInfo` (default on):
    - it stores its `Destination` and re-issues the move whenever the last
      known spot moves more than 2 m;
    - it **never finishes**: it stays on the spot listening, so `ST_Gunman`'s
      `Wait` state is no longer reached (harmless);
    - finding the player ends the search through the tree's transition.
- **Allies and the line of fire** (user-confirmed 2026-10-13; "they still
  end up killing each other"):
  - **Hold fire:** in `FireAt`, before every shot, `SweepMultiByObjectType`
    runs a **Pawn-object** sphere tube (`LineOfFireRadius 20` cm) from the
    **muzzle to the shot's target point**: the chosen bone, the chest, or the
    suppression spot, led as usual. It deliberately ignores the round's own
    near-miss offset.
    - Any live `AEnemyBase` in the tube means the shot is held (`FireAt`
      returns false). Hits and near misses alike, the burst isn't spent, and
      it retries next tick.
    - **Misses check their own path too (2026-10-24; user: "they shoot each
      other again" after the CC switch).** A near miss leaves the tube
      (`NearMissMin`–`Max` 60–150 cm beside the player) and carries on, so an
      ally beside or behind the player could take it — friendly fire is on
      in `BP_EnemyBase`. The tube sweep is now the helper
      `IsAllyAlong(From, To)`; a miss also sweeps its own direction out to
      `MissCarryDistance` (1500 cm) past the player. An ally on it mirrors the
      miss to the player's other side; both sides blocked holds the shot
      like the tube does. Collision was checked live and hadn't changed with
      CC: capsule Pawn 34 × 96 (ignores Visibility), body `CCMH_Body_Male`
      Pawn query-only (the only part bullets hit), head/hair/clothes
      (`CC_SkelMesh_C`) no collision, grooms PhysicsActor.
      *(Tested by the user 2026-10-24: "misses work".)*
  - **Reposition when blocked:** held time accumulates in
    `LineOfFireBlockedTime`; a fired shot or a new move
    (`ClearLineOfFireBlocked`) resets it.
    - Gunman Check **`LineOfFireBlocked`** is true at
      `RepositionWhenBlockedAfter 1` s.
    - `ST_Gunman`'s **Hold** has *On Tick → Reposition if Line Of Fire
      Blocked* (added by the user, checked via the bridge).
  - **Allies don't block sight:** `HasClearShot` ignores every enemy and
    their equipped weapons.
    - Without this, a buddy in between broke sight, the enemy dropped into
      suppression, and it fired at the last known spot through him.
    - Walls and cover still block sight.
  - **Friendly fire:** `bFriendlyFire`, per enemy; C++ default off, and the
    user turned it **on** in `BP_EnemyBase`.
    - Off: `AWeaponBase::GetFriendlyActors` lists every enemy, so hitscan
      ignores them and projectiles `AddIgnoredActor` them. Rounds pass
      through.
    - On: crossfire, rounds in flight and stray pellets can still hit
      allies, and hold-fire only stops deliberate shots through one.
  - **What was tried and dropped:**
    - a line trace, then a single sphere sweep on Visibility: the first hit
      was often the ally's *gun*, which isn't an `AEnemyBase`;
    - a tube along the round's own path to 1 m past the target: near misses
      offset past a friend still fired.
  - **A wrong lead, recorded so it isn't repeated:** the `.uasset` contains a
    `CharacterMesh` string, but the bridge read showed `BP_EnemyBase`,
    `BP_Enemy_Test` and `BP_PlayerCharacter` meshes are all **Custom** with
    Visibility and Projectile at Block. A name-table string is not an applied
    preset.
- **TEMP debug removed (2026-10-14):** `bDebugShooting` (the readout and
  shot lines) and the player's `bShowHitsTaken` are gone. If hit chances need
  showing again while tuning, put them behind a CVar.
- **Leading:** for projectile weapons
  (`AWeaponBase::GetProjectileSpeed()`, read from the projectile class's
  `InitialSpeed`; 0 for hitscan), the aim point moves ahead by `player
  velocity × flight time × LeadSkill 1.0 × ShotAccuracy`.
  - The flight time is a single estimate: muzzle-to-chest distance ÷ speed.
  - So a fresh enemy barely leads, a fully tracked one leads almost
    perfectly, and a mid-dive shot leads only 25%.
  - Without this, enemy rounds (30 m/s) landed behind a strafing player even
    at 100%.
  - **Bursts:** `BurstShotsMin/Max` 3–5, at the weapon's own `CanFire` rate,
    then a `BurstPauseMin/Max` 0.5–1.5 s pause.
  - **Empty magazine:** `ReloadEquippedWeapon` + its animation, or, with no
    reserve, `SetAmmoInMagazine(full)`. Enemies never run dry.
- **Shot (`FireAt`):** `Weapon->Fire(muzzle, dir)` + `PlayFireAnimation`.
  - `dir` aims at a point on a **flattened disc around the chest, sized in cm
    at the player**:
    - the radius is `lerp(MaxMissRadius 200, MinMissRadius 5, ShotAccuracy)` side
      to side, × `VerticalSpreadScale 0.3` up and down;
    - the point is sampled uniformly on the squashed disc.
  - The spread is `radius ÷ distance`, as a tangent, so accuracy alone sets
    the hit chance at any range.
  - It's limited to `MaxSpreadAngle 30°` from the barrel. That only matters
    within about 3.5 m at low accuracy, where point blank gets slightly easier.
  - The weapon's own bloom adds a little on top.
- **Getter:** `GetAccuracy()`.

**What was tried and dropped (2026-10-13):**
- **An angular cone** (`MaxSpreadAngle 12°`/`MinSpreadAngle 0.5°`): a fixed
  angle covers less ground up close, so walking up to an enemy made you
  easy to hit.
- **A penalty from the sweep across the enemy's view** (sideways speed ÷
  distance): fixed close range, but the penalty barely applied far away, or
  when running straight in, or when the enemy strafed alongside.
- **A soft cap** (draining at `AccuracyLossPerSecond` down to the cap): with
  the cap moving every frame, accuracy sat well above it.
- **Speed alone, with no direction:** running straight at an enemy protected
  you as much as strafing.
- **A distance-independent miss disc on its own:** you could dodge everything
  at point blank. That's why the close-range floor was added.
- **The dive cap as the build-up's cap, for the whole dive (wind-up to
  get-up):** it clamped the stored accuracy, so every dive reset the enemy,
  and lying prone stayed safe. It now applies to shots only, during the
  flight. The user later asked for a reset on **landing** instead, which is
  `AccuracyAfterShootdodge`.
- **A movement cap on accuracy**, hard or soft: replaced by growth-only
  slowing, at the user's request.

**Player (2026-10-13):**
- **The player never staggers:** `StaggerDuration = 0` in
  `AProjectBopisCharacter`'s constructor. Being rooted would also cut a dive
  short. The light flinch stays, for now.
- `UHealthComponent::bUnkillable` (health floors at 1) is still there for
  testing. **The user unticked it** on `BP_PlayerCharacter` once player death
  worked.
- **TEMP debug, to remove once tuned:**
  - `AProjectBopisCharacter::TakeDamage` prints `HIT -dmg (bone) health x/y`
    (`bShowHitsTaken`);
  - the enemy's `bDebugShooting` draws "unaware/SEES/lost acc% (growth ×n)
    speed cm/s [CLOSE/DIVE xx%]" above the head, plus a line per shot, red if it reaches the player and
    yellow if it misses, for 1 s.

**Gotchas found:**
- **`BP_PlayerCharacter`'s mesh was `NoCollision`** (a template leftover
  overriding the C++ responses), so no bullet or trace could hit the player.
  It's now set to the enemy's mesh collision (query-only Pawn: blocks
  Visibility and Projectile, ignores Pawn/Vehicle/Camera).
- **`BP_Kamz` is a child of `BP_PlayerCharacter`.** Values it overrides stay
  its own (the mesh collision had to be set on both). Values it doesn't
  override come from the parent: it inherited `bUnkillable`, which made
  "the player isn't dying".
- Tune the AnimBP's settings on **Class Defaults**; Preview-window edits
  aren't saved.

**Next (user, as development goes):** accuracy amendments per player action
(Focus, crouch, firing…), judged in real shootouts (*Gunman behaviour v1*).

### Player death — Phase 5 (2026-10-13, user-confirmed in PIE)

The user's choices:
- reload the level;
- the camera follows the body;
- dying mid-dive goes straight to ragdoll.

**Code:**
- **`AProjectBopisCharacter::Die`** (overrides the base's):
  - It reads `bDiedMidDive = Shootdodge->IsBodyDown()` (flying, landing or
    prone), then `DiveDeathVelocity` (the velocity at death).
  - It calls `UShootdodgeComponent::CancelForDeath()`. That stops the
    wind-up/get-up montages (restoring the root-motion mode), ends the dive's
    slow motion, clears the queued reload, sets the phase to `None`, and
    stops the component ticking. Nothing else is restored, because the
    ragdoll takes over.
  - It stops Focus, then starts **death slow motion**: `BeginFreeFocus()` (the
    Focus look and pitch) with the global dilation overridden to
    `DeathTimeDilation 0.2`.
  - It sets `bIsAiming = false`, then calls `Super::Die`.
  - Then it sets `bUseControllerRotationYaw = false` and
    `ClearActionEventBindings()`, and rebinds only Look/MouseLook. Look orbits
    the camera; nothing else responds.
- **No death animation mid-dive:**
  - `PlayDeathAnimation` is now `virtual` on `ABopisCharacterBase`. The
    player's override returns false when `bDiedMidDive`, so the base
    `TakeDamage` ragdolls at once.
  - The player's `TakeDamage` then adds `DiveDeathVelocity` to every body
    (`SetAllPhysicsLinearVelocity(..., true)`), so the dive's momentum
    carries into the ragdoll.
  - The player Blueprints have no `DeathAnimations` set, so every player death
    is a ragdoll for now.
- **`Tick` while dead** skips crouch, stances and camera framing:
  - `FollowBodyWithCamera` eases the boom's world location to the `pelvis` at
    `DeathCameraFollowSpeed 8`. The capsule stays where the player died.
  - `TimeSinceDeath` counts **real seconds** (`FApp::GetDeltaTime()`, from
    before any dilation). At `DeathSlowMoDuration 2` it calls
    `EndFreeFocus()`, and at `DeathRestartDelay 3` it calls `RestartLevel()`
    (`OpenLevel` with the current level's name).
  - A game-time `FTimerHandle` was used first and dropped: slow motion
    stretched it.

### Enemy shooting v2 — the hit-chance model (2026-10-13, user-confirmed in PIE)

**Why it was replaced:** the user said "It seems the mooks cant hit me up
close unless the accuracy thing goes up." What they want: "emphasis on
movement and using your 'dodges' and accuracy to survive gunfights, it should
be freeflowing… aiming and shooting is a valid strategy but we dont want them
camping out with it."
- The old accuracy number only sized a miss disc. 85% still missed about
  half the time, and every tweak was a patch on top.
- The new design is Claude's proposal, accepted: the cinematic-shooter
  approach (Max Payne 3 / Uncharted).
- The user caps fights at **about 6 mooks**.

**Each shot rolls to hit** (`AEnemyBase::UpdateShooting` / `FireAt`):
- `HitChance = Lerp(Normal, max(Normal, CampedHitChance), heat) × StateFactor`,
  where `Normal = min(MaxHitChance, BaseHitChance × DistanceFactor)`
  *(2026-10-16; before: `min(MaxHitChance, Base × Distance × State ×
  (1 + CampingHitBonus × heat))`)*. **Values (2026-10-15):** `BaseHitChance`
  **0.12**, `MaxHitChance` **0.5** — C++ defaults and both `BP_EnemyBase` and
  `BP_Enemy_Test` (the user had 0.12 / 0.75; the cap came down when the
  tokens went). Originally 0.3 / 0.9.
- **Distance:** ×`CloseHitMultiplier 2.3` within `CloseHitRange 300`, ×1 at
  `MidHitRange 1000`, ×`FarHitMultiplier 0.4` from `FarHitRange 2500`;
  linear in between (`GetMappedRangeValueClamped`).
- **State:**
  - mid-evasion (`IsEvading()`, the dive's flight): ×`EvadingHitMultiplier
    0.1`;
  - down after a dive (landing, prone, get-up): ×`DownHitMultiplier 1.0`;
  - otherwise speed: ×1 standing → ×`MovingHitMultiplier 0.6` at
    `MovingSpeedForFullPenalty 500` cm/s.
- **Camping** *(2026-10-16)*: the chance climbs in a straight line with the
  player's camping heat from `Normal` to **`CampedHitChance` 1.0** — a target
  that stays put is hit for certain at full heat (1.5 s grace + 4 s, so
  5.5 s), at any distance. The user: "the mooks seems so stupid right now that
  they cant hit a non moving target". The state factor comes last, so moving
  or diving out of the heat still counts; heat drains at 0.5/s after moving.
  `CampingHitBonus` was removed (its `BP_EnemyBase` value dropped). The cap
  now only limits the un-camped chance.
- **A hit also needs:**
  - the enemy can see the player;
  - it isn't in a **warning burst**;
  - the player isn't in **hit grace**.
- **Typical chances** at 0.12 / 0.5, standing still: fresh 3 m 28%, 5 m 23%,
  10 m 12%, 20 m 7%; at 5 m after 3 s 52%, 4.5 s 81%, 5.5 s+ 100% (every
  distance reaches 100% at full heat). Running ×0.6, evading ×0.1.
  *(At the original 0.3 / 0.9, fresh heat, standing / running / mid-dive:
  3 m 69/41/7%, 10 m 30/18/3%, 20 m 16/10/2%.)*

**Enemy aim at the shot point — tried and reverted (2026-10-16).** Planned
shots (decide each shot ahead: hit + bone or miss + side, odds reconciled at
the trigger), first aiming the gun at the planned point, then a steady chest
aim that flicked to each round's point for 0.15 s; plus an
`ABopisAIController::UpdateControlRotation` override, because the engine
zeroes the aim's pitch whenever the AI focuses a point instead of a pawn. The
user reverted all of it; enemies aim and place shots as below.

**Placement (`FireAt(Target, bHit)`):**
- **Hits** aim at a bone drawn from `HitBoneWeights`:
  - torso 60% (`spine_03` 25, `spine_05` 20, `pelvis` 15);
  - arms 15% (upper arms 4 each, lower arms 3.5 each);
  - legs 20% (thighs 6 each, calves 4 each);
  - head 5%.
  - Bones the player's mesh lacks are skipped. Scatter is `HitScatter 5` cm.
- **Near misses** pass 60–150 cm (`NearMissMin/Max`) to a random side, at
  −0.25..1 × `NearMissHeight 60` cm, so past the ear or over the shoulder,
  never into the floor.
- **Suppression** shots are near misses around the last known spot.
- **Leading:** both hits and misses are led by `velocity × flight time ×
  LeadSkill 1.0` for projectile weapons.
- **No spread:** `AWeaponBase::Fire(…, bExact = true)` skips the weapon's
  spread (bloom, before 2026-10-15), so a placed shot stays placed. Pellets
  still fan out; the player's own guns are unchanged.
- **Timing (2026-10-15):** bursts and pauses come from the weapon's
  `AIFiring`, scaled by the enemy's `BurstShotsMultiplier` /
  `BurstPauseMultiplier`. See *Combat → Enemy firing pattern*.
- **Player headshots do normal damage:** the player's constructor removes
  the `head` ×4 from `BoneDamageMultipliers`. Enemies keep ×4.

**Camping heat** (`AProjectBopisCharacter::UpdateCampingHeat`, on the
player, shared by all enemies):
- **Anchor:** staying within `CampRadius 250` cm of the anchor accumulates
  time there. Leaving re-anchors at the current spot and resets the time.
- **Heat:** the target is `clamp((time − CampGraceTime 1.5) /
  CampTimeToFullHeat 4)`. Heat rises to the target at once, and falls toward
  it at `CampHeatDrainPerSecond 0.5`.
- **Consequences:**
  - strafing inside the circle still counts as camping;
  - heat runs on game time, so it builds slower in slow motion;
  - it's read through `GetCampingHeat()`.

**Attack tokens — removed 2026-10-15.** The user: "I dont like the token idea
anymore, Id rather have them able to do damage to you at all times but reduce
the base and max accuracy." Every enemy in sight now rolls to hit; the cap
came down to 0.5 to compensate. What they were: `AProjectBopisGameMode`
handed out `MaxAttackTokens 2` (3 s holds, 1.5 s cooldown); only holders
could hit, the rest fired near misses. Earlier the same day they were limited
to enemies able to use them, nearer-first (`AttackTokenRange`,
`AttackTokenStealMargin`) — but a lone shotgunner point-blank still whiffed
through his hold cooldown, which is what ended them.

**Fairness:**
- **Warning burst:**
  - With `bWarningBurst` on, the first burst at a *seen* player after
    alerting, or after `WarningBurstResetTime 4` s unseen, is all misses.
  - A burst fired while suppressing doesn't use it up.
- **Hit grace:**
  - `AProjectBopisCharacter::IsInHitGrace()` holds for `HitGraceTime 0.5` s
    after damage was taken (stamped in `TakeDamage`).
  - It gates the roll, not damage, so rounds already in flight still land.

**Debug readout (TEMP):** `SEES hit xx% (dist ×, state ×, camp ×) cm/s` plus
the `PUSH` / `TOKEN` / `WARN` tags.

### Gunman behaviour v1 — work order (2026-10-13, done 2026-10-14)

**Why:** the user wants real shootouts, not test setups, to judge feel and
difficulty.

**The user's choices (2026-10-13):**
- **Aggressive mooks** (John Woo): alert, then keep shooting while
  repositioning near the player at a preferred range, sometimes pushing in.
  No cover system yet.
- **Awareness by sight + gunfire:** unaware until they see you or hear
  shots. An alerted enemy alerts others near it, so the player can start a
  fight on their own terms.
- **The user blocks out the test space.** Claude handles the enemy
  settings, navmesh notes and spawn logic.

**Architecture:**
- **`ABopisAIController`** (new) owns an `UAIPerceptionComponent` with sight
  and hearing.
- **The behaviour** is a per-archetype StateTree (`ST_Gunman`), run by the
  controller's StateTree AI component. The tasks are C++; the tree is
  assembled in the editor.
- **The enemy keeps the primitives** the tree drives: aim/focus, raise,
  move, and permission to fire. Accuracy and bursts stay in
  `UpdateShooting`.
- **Gunfire is a hearing noise** reported by `AWeaponBase::Fire`
  (`UAISense_Hearing::ReportNoiseEvent`), with a per-weapon range, so
  suppressed weapons later just get a shorter one.

**Order (one item at a time):**
1. **Awareness:**
   - the controller + perception;
   - an unaware → alerted state on the enemy (`Alert(Target)`): alerted by
     sight, by gunfire heard, or by being hit;
   - spreading the alert to allies within a radius, after a short delay;
   - player gunfire as noise.
   - Until the StateTree exists, an alerted enemy uses the old
     `bAimAtPlayer` behaviour as its engage. *(Done.)*
2. **StateTree scaffolding:**
   - C++ tasks: pick an engage spot (reachable, at the preferred range, with
     line of sight), move there while aiming and firing, hold and shoot for
     a while, then go again; go to the last known position when the player
     is lost.
   - `ST_Gunman` assembled in the editor.
   - It replaces the test patrol/aim (the patrol stays as the unaware
     state).
3. **Pushing in**, and tuning the preferred range.
4. **Encounters:** placing/spawning groups for the user's blockout (waves or
   triggers, as the space needs).

**Step 1, built (user-confirmed 2026-10-13):**
- **`ABopisAIController`** (`Enemies/BopisAIController.h/.cpp`) is the
  enemy's `AIControllerClass`.
  - **Sight:** 3000 cm, lost at 3500, 70° each side.
  - **Hearing:** range 10000 cm; the weapon's `NoiseRange` decides.
  - **Detection:** both senses detect every affiliation, since nothing has a
    team.
  - **`OnTargetPerceived`** (bound in `BeginPlay`) calls `Alert(player)` on
    sight of the player, or on any gunfire heard.
- **`AEnemyBase`:**
  - **Alerting:** `Alert(Target)` sets `bAlerted`, the alert target and the
    last known location, then spreads to every live enemy within
    `AlertAlliesRadius 1500` after `AlertAlliesDelay 0.5`. Each newly alerted
    enemy passes it on, so it ripples.
  - **Being hit** alerts it too (`TakeDamage` override → instigator's pawn).
  - **`bStartAlerted`** (default off) replaces the old `bAimAtPlayer` test
    flag.
  - **Unaware** means gun down, no shooting, no build-up, test patrol only.
- **Gunfire noise:** `AWeaponBase::Fire` calls
  `UAISense_Hearing::ReportNoiseEvent(muzzle, 1, owner, NoiseRange 3000)` on
  each shot; 0 makes the weapon silent.

**Step 2, built (user-confirmed 2026-10-13; `ST_Gunman` built by the user,
checked via the bridge). Follow-ups: no x-ray aim and suppressive fire (see
*Enemy shooting*).**
- **The controller runs the tree:**
  - It owns a `UStateTreeAIComponent` (`BrainComponent`) with
    start-automatically off.
  - `StartBehaviour()` (from `BeginPlay` if already possessed, or
    `OnPossess` mid-game) calls `SetStateTree(Enemy->GetBehaviour())` +
    `StartLogic()`.
  - The controller is destroyed with the body on death, so the tree goes
    with it.
- **`AEnemyBase`:**
  - **`Behaviour`:** the StateTree asset slot. `BP_EnemyBase` →
    `/Game/ThirdPerson/AI/ST_Gunman`.
  - **`FindSpot(range, around, radius)`** (it was `FindEngageSpot` until step
    3): `EngageSpotSamples 12` random reachable nav points within the radius
    of the sample centre, scored against the **last known** player spot:
    - −1 per cm outside the range band;
    - +1000 for a clear shot from eye height to the chest;
    - −500 per live ally within `AllySpacing 300`.
  - **`ChooseNextSpot`** (used by Gunman Move; step 3 below) either:
    - pushes in, or
    - looks for a normal engage spot in `PreferredRangeMin/Max 600–1500`
      within `RepositionRadius 800` of itself.
  - **Memory:** `LastKnownPlayerLocation` and `TimeSinceSeenPlayer` are
    updated in `UpdateShooting` and seeded by `Alert`.
  - **`HasClearShot`** is shared with `CanSeePlayer`.
  - **The test patrol** only runs while unaware.
  - The module gained the `NavigationSystem` dependency.

**Step 3, pushing in (user-confirmed 2026-10-13).** The user chose
**random**: "We don't want the enemy to be too smart. After all the idea is
to get as much stylish kills as possible."
- **Each Gunman Move [Engage Spot]** rolls `PushChance 0.2`.
- **On a hit:** `FindSpot(PushRangeMin/Max 200–450, around the last known
  player spot, radius PushRangeMax)`, and `bPushingIn` is set.
  - While it's set, `UpdateMovementMode` uses `PushSpeed 450` (normally
    `RaisedSpeed 250`). It keeps firing on the way.
  - The task's `ExitState` calls `EndPush()`, so after arriving it holds, and
    the next move rolls again.
  - The readout shows `PUSH`.
- **No coordination:** several enemies can push at once. A one-pusher-at-a-
  time cap would be pacing, not smarts, and can be added if it's too much.
- **A push lands it inside the close-range floor zone (<5 m):** dangerous for
  the player, and a mook in the open to dive at.
- **Preferred range:** the 600–1500 defaults are kept. It's per enemy, to be
  tuned in play.
- **Nodes** (`Enemies/GunmanStateTreeNodes.h/.cpp`; instance data with a
  `Context` AI controller, plus `Parameter`s):
  - **`FGunmanMoveTask` "Gunman Move":** goal is `EngageSpot` or
    `LastKnownPosition`; `MoveToLocation` with strafing (keeps the focus) and
    projection. Succeeds on arrival (move status idle), fails with no
    spot/path, and stops movement on early exit.
  - **`FGunmanCondition` "Gunman Check":** `IsAlerted` or `HasLostPlayer`
    (alerted and unseen for `LostForSeconds`), with `bInvert`.
- **`ST_Gunman`** (`StateTree AI Component` schema; the schema classes are
  left at AIController/Pawn, which works because the nodes cast for
  themselves):

```
Root
├─ Unaware        Delay (forever)           On Tick → Engage   if Is Alerted
├─ Engage                                   On Tick → Search   if Has Lost Player 3 s
│   ├─ Reposition Gunman Move [Engage Spot] On Completed → Hold
│   └─ Hold       Delay 2 ± 1               On Completed → Reposition
└─ Search                                   On Tick → Engage   if NOT Has Lost Player 3 s
    ├─ Go Look    Gunman Move [Last Known]  On Completed → Wait
    └─ Wait       Delay (forever)
```

- **The bridge can't author StateTrees:** there's no create-asset tool and no
  StateTree toolset. It **can read** them:
  - the editor data is `ST_X.ST_X:StateTreeEditorData_0`;
  - the states hang off its `subTrees`/`children`, each with `tasks`,
    `transitions` (`trigger`, `state.iD`, `conditions`) and
    `enterConditions`;
  - each node's `node`/`instance` `_structType` names the type.
  - Note the gotcha found while checking: a Delay's **Random Deviation**
    larger than its Duration can roll ≤ 0 and end at once.

**Step 4, encounters: the wave spawner (user-confirmed 2026-10-14).** The
user's call: "lets do waves… constantly spawn enemies so that there are always
6 at the same time, when we spawn we randomly assign a weapon to them." The
test map is a square arena.
- **`AEncounterDirector`** (`Gameplay/EncounterDirector.h/.cpp`) is placed
  one per arena.
  - **Settings:** `EnemyClass` (`BP_Enemy_Test`), `SpawnPoints` (Target
    Points, per instance), `WeaponPool`, `MaxAlive 6`, `RespawnDelayMin/Max
    1–3` s, `TotalEnemies` (0 = endless), `MinSpawnDistance 1200`,
    `bPreferOutOfView`, `bSpawnAlerted`.
  - **`BeginPlay`** fills to `MaxAlive`.
  - **`Tick`** (0.2 s) prunes the dead or destroyed from its weak `Alive`
    list. When short, it schedules a replacement after the random delay and
    keeps retrying while no point is free.
  - **`PickSpawnPoint`** skips points within `MinSpawnDistance` of the player
    or within 1.5 m of a live spawned enemy. It prefers points outside about
    60° either side of the player's view direction, falling back to any
    usable point.
  - **`TrySpawnOne`:**
    - `SpawnActorDeferred` at the point, lifted by the class CDO's capsule
      half-height, with `AdjustIfPossibleButDontSpawnIfColliding`;
    - `UWeaponHolderComponent::SetStartingWeaponClass` from the pool, which
      must happen **before** `FinishSpawning`, because the holder equips in
      `BeginPlay`;
    - `FinishSpawning`, then `Alert(player)` if `bSpawnAlerted`.
- **Patrol points** are the old test patrol for *unaware* placed enemies;
  every placed enemy shared one list. Spawned enemies start alerted and never
  use them.

**Roaming (user-confirmed 2026-10-14):** "roam when alerted but no vision and
does not have a last known position anymore… random spot on the map OR… the
target point (the furthest one)".
- **The lead goes cold:** `bLeadGone` is set once the enemy has stood within
  2.5 m of `LastKnownPlayerLocation` for `LeadGoneAfter 3` s while alerted
  and not seeing the player. Sight and `HearPlayer` reset it.
- **`ChooseRoamSpot`:** with `RoamToPointChance 0.5`, the **furthest
  `ATargetPoint`** in the level, which includes the spawn points; otherwise
  a random reachable nav point within `RoamRadius 3000`.
- **Aim while roaming:** with the lead gone, `UpdateAim` clears the focus, so
  the enemy looks where it's going, gun up.
- **Nodes:** Gunman Move goal **`Roam`** (finishes on arrival); Gunman Check
  **`LeadGone`**.
- **`ST_Gunman`** (edited by the user): Search gains *Go Look → Roam if Lead
  Gone*, plus a new state **Roam**: Gunman Move [Roam], *On Completed →
  Roam*, and *On Tick → Go Look if NOT Lead Gone*.

**Gunman behaviour v1 is complete.**

### Room encounters — holding enemies (2026-10-16)

**The user:** "The standard gameplay will be linear and not arena… 3 or 4
enemies waiting in the room, you jump in and do your moves to kill them all."
Choices: hold a small area; set off by sight/hearing, a trigger volume, and a
short reaction beat; out of sight, stay and cover the room.

1. **Holding (`bHoldsPosition`, `Enemy|Behaviour|Hold Position`):**
   `HomeLocation` is recorded in `BeginPlay`. `ChooseNextSpot` samples
   within `HoldRadius` 400 cm of home (the usual range/clear-shot/spacing
   score), never a push. The *Has Lost Player* check is always false for a
   holder, so `ST_Gunman` never sends it to Search/Roam: it stays in Engage,
   aims at the last known spot (`UpdateAim`), suppresses briefly, then holds.
   No StateTree change. Arena gunmen (off) are unchanged.
2. **Reaction beat (`ReactionTimeMin/Max` 0.3–0.8 s, `Enemy|Awareness`):**
   `Alert` rolls `ReactionTimeLeft`; `UpdateShooting` returns before the
   trigger check until it runs out — it still turns, tracks and moves. First
   alert only (Alert is a no-op once alerted). Applies to every enemy;
   0–0 fires at once.
3. **`AEncounterTrigger`** (`Gameplay/EncounterTrigger.h/.cpp`): a
   `UBoxComponent` (`Trigger` profile, orange, 4 × 4 × 2 m default); the
   player's begin-overlap calls `Alert(player)` on every enemy in its
   instance-set `Enemies` list, once (`bTriggerOnce`).
4. **Crouched holding (`bCrouchWhileHolding`, 2026-10-16):** a holder that
   crouches whenever its AI isn't moving (`GetMoveStatus() != Moving`) —
   waiting and fighting crouched — and stands to move between spots
   (`UpdateCrouch`, after `UpdateMovementMode`). Enemies now have
   `bCanCrouch`. Sight is from the head, so behind waist-high cover a crouched
   holder can't see (or shoot) the player. **No cover behaviour (user,
   2026-10-16):** "I dont want the enemy to explicitly take cover, I dont want
   whack a mole" — no pop-up shooting, no cover-seeking.
- **Setting up a room:** place `BP_Enemy_Test`s with `bHoldsPosition` on and
  `bStartAlerted` off; place an `EncounterTrigger` at the door and add them
  to its `Enemies`. Sight/hearing still alert them earlier, and
  `AlertAllies` spreads it.

### Searching with the gun down (2026-10-17)

The user: "when they are in a lowered stance and moving to look for me,
have their head look at the last known position within reasonable bounds…
It makes it more plausible."
- **Lowering:** after `LowerGunAfter` 4 s out of sight (not for holders,
  which keep covering the room), `UpdateAim` drops the aim and clears the
  focus. The lowered stance then turns the body to its travel direction at
  `LoweredSpeed` with the jog poses.
- **Raising:** seeing the player again raises the gun and rolls a fresh
  reaction beat (`ReactionTimeMin/Max`) before it can fire (`bGunLowered`).
- **Head look:**
  - `AEnemyBase::GetHeadLookTarget` returns the last known spot at head height
    while it's alerted, lowered and still has a lead, and is further than
    `HeadLookMinDistance` 3 m from that spot. It's a virtual on
    `ABopisCharacterBase`; the player returns false.
  - `UProjectBopisAnimInstance::UpdateHeadLook` turns the head toward it within
    `HeadLookMaxYaw` 70° and `HeadLookMaxPitch` 30°. A target past
    `HeadLookGiveUpAngle` 130° isn't looked at. The turn eases at
    `HeadLookSpeed` 5.
  - The result goes out as `HeadLookRotation`: half each on `neck_01` and
    `head`, via two Transform (Modify) Bone nodes (add to existing, component
    space) at the end of `ABP_Player`'s AnimGraph, after the DeathSlot.
- **Not yet:** hearing gunfire while lowered moves the search target but
  doesn't raise the gun.

### Three families

> ⚠ **Superseded 2026-10-09:** the Aswang are dropped (lore doc PART 1 — user:
> "Aswang is not a thing anymore"). Kept as history; the enemies built since are
> human (`BP_Enemy_CC` Thug/Goon).

| Family | Share | Behaviour | Build cost |
|---|---|---|---|
| **Mature Aswang** | The overwhelming majority | Gun users. Composed, clothed, armed. Always already in monstrous form when combat is possible. | The main enemy. Full ranged AI. |
| **Ferals** (newly turned) | Deliberately rare — ~3 encounters in the campaign | Mindless melee chargers. No firearms. | **Cheaper than a gun user**, not harder. |
| **Humans** | Kept rare and deliberate | Ordinary ranged enemies. | Reuses the Aswang rig. |

**Humans stay rare on purpose.** If almost nothing the player kills is human,
the few humans who are killed carry weight. This is a design rule, not a
content shortfall.

**Ferals are the cheap one.** A mindless charger needs no cover reasoning, no
line-of-sight firing logic, no aim, no engagement-range decisions — navigate
to player, attack in range. That is a markedly simpler StateTree than the
ranged Aswang. The cost sits in model and animation, which scripting the
encounters would not have avoided, so **build it properly rather than
scripting three one-offs**.

### What the design buys us

> ⚠ **Superseded 2026-10-09:** the Aswang are dropped (lore doc PART 1 — user:
> "Aswang is not a thing anymore"). Kept as history; the enemies built since are
> human (`BP_Enemy_CC` Thug/Goon).

- **No mid-combat transformation.** Aswang aware of a threat are already in
  monstrous form. The model/skeleton swap — previously the most expensive
  unknown here — is off the table.
- **Aswang and humans share a skeleton, rig and animation set.** They wear
  ordinary clothes and keep human proportions; the difference is head mesh,
  hands and materials. This makes the one-base-actor approach *more* valuable,
  not less.
- **No companion AI.** The protagonist has no human allies. The femme fatale
  is a scripted set-piece at most, never a general system. Companion AI is one
  of the most expensive things in a shooter and it is simply not needed.

### Two-layer health — required, not cosmetic

> ⚠ **Superseded 2026-10-09:** the Aswang are dropped (lore doc PART 1 — user:
> "Aswang is not a thing anymore"). Kept as history; the enemies built since are
> human (`BP_Enemy_CC` Thug/Goon).

Aswang are tanky and do not die to a single headshot. Implemented naïvely as a
larger `Health` number this **breaks the bloom skill test**: when everything
takes a magazine, shot placement stops mattering and the correct play becomes
holding the trigger, which is the opposite of what the accuracy model rewards.

Model it as Halo's shields instead — two distinct pools:

1. **Supernatural resilience** — the outer pool. Soaks punishment. Depleting
   it fires a **break event**.
2. **Mortal health** — underneath. Small, and precision matters again.

The break event is the point. A single sliding health value gives nothing to
react to; two pools produce a discrete transition that can be announced,
which is what tells the player *precision pays now*. Tankiness, preserved
trigger discipline, and a dramatic beat all fall out of one decision.

**Headshots:** no precision-damage system exists yet — deferred out of Phase 3.
"Doesn't die to one headshot" need not mean "headshots aren't special": a
heavy multiplier that isn't an instant kill still rewards placement.
`HitResult.BoneName` already comes back from the existing trace.

**Knock-on:** ammo values (pistol 12/60/120, close rifle 30/60/120, battle
12/60/120) were tuned against enemies that don't exist. Expect a retune once
something can actually die.

### Vocalization system

> ⚠ **Superseded 2026-10-09:** the Aswang are dropped (lore doc PART 1 — user:
> "Aswang is not a thing anymore"). Kept as history; the enemies built since are
> human (`BP_Enemy_CC` Thug/Goon).

Aswang must not read as reskinned human shooter enemies. Growls, screams and
animalistic gestures are **state telemetry**, not flavour — the Halo
precedent, where an Elite's shield breaking is announced audibly because the
player can't see a health bar across a firefight.

Triggers worth announcing:

| Trigger | Purpose |
|---|---|
| `Alert` | Spotted the player. |
| `ResilienceBroken` | The most important one — the only mid-fight state change the player must be told about. |
| `Enrage` | Only if behaviour *actually* changes. Announcing a state that plays identically trains players to ignore the audio. |
| `Pain` / `Death` | Cheap, high value. |
| `AmbientIdle` | The horror one. Fires **outside** combat, from somewhere unseen. |

Shape it like the systems already built: an enum plus
`TMap<EAswangVocalization, FAswangVocalization>` on the enemy, where the
struct pairs a sound with an optional montage so audio and body language fire
together. One `PlayVocalization(ETrigger)` entry point, called from the
StateTree and the damage handling. Same pattern as `FireMontages` /
`ReloadMontages` on the character.

Three things that bite if left late:
- **Throttling** — a pain grunt on every hit becomes comedy. Per-category
  cooldown plus priority (death > enrage > pain).
- **Concurrency** — eight Aswang roaring at once is mud. `USoundConcurrency`
  handles this as configuration, not code.
- **Attenuation** — for `AmbientIdle`, direction and distance *are* the
  mechanic.

**Design the base enemy with state-change broadcasts from day one.**
Retrofitting announcements onto a finished state machine is how transitions
end up silently doing nothing.

### Readability layers by distance

> ⚠ **Superseded 2026-10-09:** the Aswang are dropped (lore doc PART 1 — user:
> "Aswang is not a thing anymore"). Kept as history; the enemies built since are
> human (`BP_Enemy_CC` Thug/Goon).

The old tension (horror wants unreadable enemies, design wants legible ones)
is **resolved**: no mid-combat transformation means enemies in combat are
always revealed, and the "ordinary people may not be human" dread lives
outside combat. Full readability applies again.

One catch remains. Ordinary clothes and human proportions mean **silhouette
alone will not separate an Aswang from a human at range** — which is normally
where readability comes from. So it layers:

- **Close** — face, eyes, mouth, coloration, fingernails.
- **At range** — **motion**. Posture, gait, how they close and take cover.
  This makes animalistic locomotion a readability mechanism and it should be
  specced that way, not treated as set dressing.
- **Unseen** — vocalization as positional information.

---

## Animation architecture (AnimBP) — 2026-10-04, logic moved to C++ 2026-10-05

`ABP_Player` (named `ABP_FirstPersonArms` until 2026-10-05) drives the third-person body. **Lyra is the animation
source** for all weapons (Shotgun Locomotion Pack rejected on quality; only its
lowered shotgun idle is used). The AnimGraph was built mostly through the editor
bridge — see the ProjectPlan Gotchas for what the bridge can and can't do in
AnimBPs.

### Logic — `UProjectBopisAnimInstance` (C++, 2026-10-05)
The AnimBP's parent class. `NativeUpdateAnimation` computes every value the
AnimGraph reads; **the AnimBP's Event Graph is empty** and it has no variables of
its own. Previously ~140 Blueprint nodes, unreadable and undiffable; moved so
logic changes are code edits instead of bridge wiring.

Source: `Source/ProjectBopis/ProjectBopisAnimInstance.h/.cpp`. Steps per frame:
`UpdateLocomotion` → weapon state → `UpdateUpperBody` → `UpdateLeftHandGrip` →
`UpdateArmAlphas` → `UpdateRecoil` → `UpdateTurnInPlace`. With no pawn (AnimBP
preview) everything stays at defaults. The character calls the public
`AddRecoil(bool bOffhand)` on every shot that fires.

| Property (AnimGraph reads) | Value |
|---|---|
| `Speed` | velocity length |
| `Direction` | travel yaw relative to actor yaw, −180..180 |
| `CardinalDirection` | nearest of 0/−90/90/180; only switches when `Direction` is >55° from the current one (10° dead zone past each 45° boundary) |
| `WarpAngle` | `NormalizeAxis(Direction − CardinalDirection)` |
| `AimPitch` | normalized control pitch |
| `bIsCrouched` | character `bIsCrouched` |
| `bIsWeaponRaised` | character `IsWeaponRaised()` |
| `CurrentAnimType` | equipped weapon `AnimType` |
| `UpperBodyAlpha` | target = 1 if raised OR `IsSlotActive("DefaultSlot")` (fire/reload), else 0. Eases up (`UpperBodyInterpSpeed` 12). **Snaps down only with a shared grip (not dual, not `PistolOneHanded`) AND standing upright AND `Speed < StationarySpeed` (10) AND not latched** — every other drop eases |
| `bIsPistolHold` | `IsPistolAnimType(CurrentAnimType)` — Pistol or PistolOneHanded. Every pistol-vs-long-gun switch in the graph (aim offsets, hip-fire idle, crouch idle) reads this, not `== Pistol` (2026-10-07) |
| `bIsDualWield` | the weapon's `IsDualWield()` (exposed 2026-10-07; was private) |
| `bDualSpread` | `bIsDualWield AND NOT bIsAiming` — picks the spread dual idle (see *Dual spread*) |
| `FreeArmAlpha` | `PistolOneHanded` only: `UpperBodyAlpha × FreeArmReloadBlend` — the free-arm layer's weight. `FreeArmReloadBlend` eases 1 → 0 while reload-animating and back after (speed 12), so the two-handed reload blends in instead of snapping |
| `SpineRecoilAlpha` | `max(MainRecoil, OffhandRecoil)` — see *Procedural recoil* |
| `ArmRecoilAlpha` | `MainRecoil` on pistol holds, else 0 (two-handed guns kick through the torso so the grip doesn't split) |
| `OffhandArmRecoilAlpha` | `OffhandRecoil` on duals, else 0 |
| `FreeArmRecoilAlpha` | `PistolOneHanded` only: `MainRecoil × FreeArmAlpha` |
| `FreeArmSwingRotation` | procedural free-arm swing from the feet — see *One-handed pistol* |
| `DualLoweredPlayRate` | `LocomotionPlayRate × DualLoweredRateScale` — despite the name, **every lowered walk/jog** since 2026-10-23: the dual layer plus the Move state's six lowered players (`BS_MM_Unarmed_Jog_Walk` ×3, `BS_Rifle_Lowered_Jog_Walk` ×3; wired by the user — the bridge can't add nodes inside states). The dual's own Move player had been unwired at 1.0, so a dual reload (which drops the dual layer) sped the legs up. Raised strafes and idles stay on `LocomotionPlayRate` |
| `LeftArmAlpha` | duals only: `UpperBodyAlpha` (2026-10-06: crouched duals no longer force the arm up — lowered and crouched, the left hand comes from the crouch clip) |
| `DualLoweredAlpha` | duals only: `(1 − UpperBodyAlpha) × (1 − DualCrouchBlend)` |
| `LeftHandIKAlpha` | target = 1 **only while aiming (ADS) a long gun** (not Pistol, not dual) and not reload-animating, else 0; eases up (10), snaps down. Every other pose — lowered, hip-fire raised, moving, pistols — keeps the clip's hand-authored left hand (2026-10-06) |
| `LeftHandGripLocation`, `LeftHandGripAlpha` | the weapon's `LeftHandGrip` socket position relative to `hand_r` (from world transforms); alpha 1 if the weapon has the socket, else 0 (falls back to the clip's `ik_hand_l`) |
| `RootYawOffset` | turn-in-place — see below |

Private state (no `UPROPERTY`): `bEaseLowering` (latch: `IsSlotActive(DefaultSlot)
OR (latch AND lowering)` — the drop after a montage ends eases), `bIsDualWield`,
`DualCrouchBlend` (eased `bIsCrouched` — fades the standing lowered-dual layer
out while crouched, since it would stand the character back up; easing it
means standing up blends it back in), and the turn-in-place bookkeeping.

Tuning on the AnimBP class defaults: `UpperBodyInterpSpeed`,
`LeftHandIKInterpSpeed`, `RootYawRecoverySpeed`, `StationarySpeed`,
`TurnThreshold`, `MaxRootYawOffset`, `TurnLeftMontage`, `TurnRightMontage`,
**`LocomotionPlayRate`** (C++ default 0.8, **0.75 on `ABP_Player`**; clamp
0.5–1), **`DualLoweredRateScale`** (0.7 default, **0.8** set),
**`FreeArmSwingFull`** (roll 25 default, **10** set), **`FreeArmMinStride`** (8), **`RecoilImpulse`** (15), **`RecoilStiffness`** (150),
**`RecoilDamping`** (0.7).

**AnimGraph-facing reals are `double`.** Blueprint "Float" is double in UE5, and
on reparenting a Blueprint variable only merges into a same-named native
property of exactly the same type. Declared as `float`, the editor renamed the
Blueprint copies (`Speed_0`…) and the getters kept reading them.

**Why the snap, and why so narrow:** easing the raised layer out on a two-handed
grip moved the left arm through the torso. A snap hides that, but read as a pop
everywhere except standing still upright — so moving, crouched, duals, the
one-handed pistol (no shared grip, 2026-10-07) and post-montage drops all ease. `IsSlotActive("DefaultSlot")` (not
`IsAnyMontagePlaying`) so turn montages don't count as a fire/reload.

### AnimGraph (top level, in evaluation order)
1. **Locomotion state machine** (Idle/Move). Move: per-weapon Blend Poses →
   `BS_Rifle_Strafe` (rifle, shotgun) / `BS_Pistol_Strafe` (pistol), both
   Direction (X ← `CardinalDirection`) × Speed (Y). 4-way Lyra walk (250) / jog
   (500) / idle (0). Idle: per-weapon clips; shotgun lowered idle from the pack.
   **Crouch branch** (2026-10-05, top level — the bridge can't add nodes inside
   states): Blend by bool `bIsCrouched` (0.25 s; True ← crouch, False ← state
   machine) where crouch = Blend by bool `Speed > 10` (0.2 s) between crouch idle
   (long guns: **`anim_shotgun_crouch_idle`** from the Shotgun Locomotion Pack —
   a kneeling crouch with the gun at neutral, swapped in by the user 2026-10-06;
   Lyra's own crouch is weapon-up and sitting. Pistols: `MM_Pistol_Crouch_Idle`)
   and crouch walk (`BS_MM_Rifle_Crouch_Walk` /
   `BS_MM_Pistol_Crouch_Walk`, 1D, X ← `CardinalDirection`), each picked by
   `bIsPistolHold`. Since crouch is stationary-only, the walk is a
   fallback for a ceiling blocking the uncrouch. Each Blend Poses by Enum has
   `PumpShotgun` and `PistolOneHanded` pins (user-added). **Every clip player**
   — 20 inside the Idle/Move states, 12 at the top level — has its Play Rate
   pin wired to **`LocomotionPlayRate`** (2026-10-07, see *Gait*).
2. **Orientation + stride warping:** Local→Component → `OrientationWarping`
   (Manual, angle ← `WarpAngle`, spine_01–05 distribute 0.5, IK foot root/feet)
   → **`StrideWarping`** → **`LegIK`** → Component→Local → **`TurnSlot`**
   (turn-in-place montages) → **Save Cached Pose `Loco`**. Orientation warping
   plays the cardinal clip and rotates the legs by the remainder — fixes the
   forward-left/back-right scissoring that Lyra's side clips produce when
   blended (each side clip only matches one diagonal pair). Stride warping and
   Leg IK: see *Gait*.
3. **Upper-body layer** (`spine_01`, mesh-space rotation): Base ← Use `Loco`;
   Blend ← **`DefaultSlot`** whose source is the hip-fire idle — Blend by bool
   `bDualSpread` (0.2 s): True ← `MM_Pistol_Idle_Hipfire_Dual` (spread), False ←
   (bool: pistol ? `MM_Pistol_Idle_Hipfire` : `MM_Rifle_Idle_Hipfire`); weight
   `UpperBodyAlpha`.
   (`DefaultSlot` → dual-reload spine hold `LayeredBoneBlend_14` → cached
   pose; see *Dual reload*.)
   Montages are therefore upper-body only (legs keep stride), and the raised
   pose holds between shots.
4. **Aim offsets, chained** (2026-10-05): `AO_MM_Rifle_Idle_Hipfire` →
   `AO_MM_Pistol_Idle_ADS`. Both X (yaw) ← −`RootYawOffset`, Y ← `AimPitch`.
   Alphas are exclusive: rifle = `UpperBodyAlpha` unless `bIsPistolHold`,
   pistol = `UpperBodyAlpha` only for pistol holds. Chaining two players
   avoids needing a second Use Cached Pose. The rifle AO on pistol poses
   twisted the wrists.
5. **Recoil + left-hand IK**: Local→Component → **three recoil Transform
   (Modify) Bones** (`spine_05` / `lowerarm_r` / `lowerarm_l`, see *Procedural
   recoil*) → CopyBone `hand_r` → `ik_hand_gun` →
   **Transform (Modify) Bone `ik_hand_l`** (translation Replace, Parent Bone
   Space — the parent is `ik_hand_gun`, i.e. the hand; ← `LeftHandGripLocation`,
   alpha ← `LeftHandGripAlpha`; rotation Ignore) → TwoBoneIK `hand_l` → effector
   `ik_hand_l` (bone space, take rotation), joint target `lowerarm_l`, alpha
   `LeftHandIKAlpha` → **Modify Bone `ik_hand_l`** (rotation Replace, Parent
   Bone Space ← `LeftHandGripRotation`, alpha `LeftHandGripAlpha`) → **Copy
   Bone `ik_hand_l` → `hand_l`** (rotation only, component space, alpha
   `LeftHandGripRotationAlpha`; both 2026-10-26, see *Per-gun hand angle*) →
   Component→Local. The Modify Bone replaces the clip's
   `ik_hand_l` (which assumes Lyra's rifle) with the weapon's `LeftHandGrip`
   socket, so the hand lands on *our* foregrip/pump. Sockets on
   `Assault_Rifle_A`, `Shotgun_A`, `Pistols_A` skeletons; none yet on
   `Sniper_Rifle_A`. See *Left-hand IK history* below. Because the recoil nodes
   run before the CopyBone, the IK target follows the kicked hand.
6. **One-handed free arm** (2026-10-07): layered blend from **`clavicle_l`,
   local-space rotation**; Blend ← `MM_Pistol_Idle_OneHanded` (the user's copy
   of the hip-fire idle with the left arm at the side); weight `FreeArmAlpha`.
   → Local→Component → **Modify Bone `upperarm_l`** (procedural swing; additive,
   component space, rotation ← `FreeArmSwingRotation`, alpha `FreeArmAlpha`) →
   Transform (Modify) Bone `lowerarm_l` (yaw +15°, additive, bone space; alpha
   `FreeArmRecoilAlpha`) → Component→Local. The one-handed **Idle-state**
   players are mirrored (right foot forward). See *One-handed pistol*.
7. **Dual left-arm layer** (`clavicle_l`): Blend ← Blend by bool `bDualSpread`
   (0.2 s; True ← `MM_Pistol_Idle_Hipfire_Dual`, False ← `MM_Pistol_Idle_Hipfire`)
   → **`OffhandSlot`** → off-hand shoulder hold (`LayeredBoneBlend_15`, see
   *Dual reload*)
   → `AO_MM_Pistol_Idle_ADS` (X ← **+**`RootYawOffset`, the mirror flips it) →
   Mirror (`MDT_Mannequin`); weight `LeftArmAlpha`.
8. **Dual lowered layer** (`pelvis` — whole body): Blend ← unarmed walk/jog
   blend space (play rate **`DualLoweredPlayRate`** = `LocomotionPlayRate` ×
   `DualLoweredRateScale` — C++ default 0.7, **0.8 on `ABP_Player`** (matched to
   the one-handed jog by eye, 2026-10-08) — since its stride is quicker than the
   pistol jog's;
   restored 2026-10-08 after the gait wiring had replaced the old fixed 0.7 with
   the global rate) / `MM_Unarmed_Idle_Ready` (bool Speed > 10)
   → finger layers (thumb + metacarpals: `_r` from pistol idle, `_l` from
   mirrored pistol idle — closed grips); weight `DualLoweredAlpha`.
9. **Rotate Root Bone** (Yaw ← `RootYawOffset`; a local-space node) →
   **Inertialization** (2026-10-06; idle unless something requests a blend —
   kept for future use) → Output.

### Left-hand IK history (2026-10-06)
The clip-driven IK misaligned on our guns in every pose. What was tried:
1. Socket position, IK in **every** pose → hand on the grip, but wrist wrong at
   idle and slight drift moving/aiming.
2. + socket **rotation** and an **attachment-chain** offset (to remove the
   one-frame world-transform lag) → "all messed up"; rolled back.
3. Socket position, IK raised only → issues on the aim offset; the
   attachment-chain offset alone, retried → "bunch of issues"; rolled back.
4. **Final:** socket position (world-transform offset), IK **only while aiming a
   long gun**. Lowered/hip-fire hands are left to the animation (user edits the
   FK). The shotgun's pump went out of arm reach when the torso twisted left →
   **`TurnThreshold` 90 → 45** so the twist never gets that far.
5. **2026-10-19 → 2026-10-26:** widened to whenever the gun is up (aimed or
   raised), then to long guns lowered too — the user edited the lowered
   idle/jog clips' left hand near the grip, and the IK closes the gap.
6. **2026-10-26:** per-gun hand angle from the socket's rotation, opt-in
   (below) — the clips' wrists gave a different angle on the gun in each pose.
Open: the rotation route needs socket orientation tuned against `hand_l` axes;
the attachment-chain offset is mathematically sound but misbehaved here — the
cause wasn't isolated.

**Hand rotation lock — tried and reverted (2026-10-26).** The left-hand Two
Bone IK (`TwoBoneIK_0`, effector `ik_hand_l`, bone space) has **Take Rotation
From Effector Space off** and **Maintain Effector Rel Rot on**, so the hand
keeps its twist from the arm animation. Flipping both (the hand takes
`ik_hand_l`'s rotation, fixed to the gun) was tried for the Mossberg's
rotating hand (user: "The left hand keeps rotating when looking around"): it
twisted enemies' hands and didn't fix the Mossberg (user: "enemies hands
twist ... Your current fix did not work"), so it's back to off / on. The
M4's steady hand comes from a comfortable reach, not the node; the Mossberg's
problem is its `LeftHandGrip` reach (see *Mossberg 500*). (The AnimGraph
steps above say "take rotation"; the node is deliberately off.)

**Per-gun hand angle (2026-10-26).** The IK places only the wrist; with
Maintain Effector Rel Rot the hand keeps its angle to the *forearm*, so each
clip's elbow and wrist gave it a different angle on the gun (user, M4 jog:
"its just the hand is the wrong angle and position. If i adjust the HandGrip
for the jog, it becomes busted for the idle"). Now a weapon can lock the angle
to itself: **`AWeaponBase::bLockLeftHandRotation`** (default off) makes the
hand take the **`LeftHandGrip` socket's rotation**. `UpdateLeftHandGrip`
stores the socket's rotation relative to `hand_r` (`LeftHandGripRotation`,
from the same relative transform as the location);
`LeftHandGripRotationAlpha` = `LeftHandIKAlpha × LeftHandGripAlpha` for
locking weapons, else 0. AnimGraph, after `TwoBoneIK_0` (whose flags are
unchanged): Modify Bone `ik_hand_l` (`ModifyBone_39`) turns the effector to
that rotation in `ik_hand_gun`'s space (lag-free, like the location), then
Copy Bone (`CopyBone_5`) copies its component-space rotation onto `hand_l`.
Nothing downstream reads `ik_hand_l`/`hand_l` (checked). Clips now decide only
the elbow. **Calibration:** `Bopis.LeftHandGripCalibrate 1` (cheat CVar) shows
on screen the socket rotation (relative to the socket's bone, as X/Y/Z =
roll/pitch/yaw) that reproduces the player's current hand — read it with the
lock off where the hand looks right, type it into the socket, then tick the
lock. Unlike the reverted lock, the angle comes from our socket, not from
Lyra's `ik_hand_l` keys. Limit: only the hand turns, not the forearm twist, so
a clip whose forearm points far off can over-bend the wrist (fix the elbow).

### One-handed pistol (2026-10-07)
`EWeaponAnimType::PistolOneHanded` (appended; `BP_Pistol` uses it, duals stay
`Pistol`). `IsPistolAnimType()` in `WeaponBase.h` covers both pistol types.
The two-handed `Pistol` type is kept for the planned high-powered pistol.
Lowered locomotion is shared with `Pistol` (user's call). Raised, the pistol
clips are two-handed, so the **free-arm layer** replaces the left arm from
`clavicle_l` with `MM_Pistol_Idle_OneHanded`. Montage maps on
`BP_PlayerCharacter`: fire → `AM_Pistol_Fire`, reload → `AM_Pistol_Reload`
(two-handed; the free arm fades out for it).

How the layer settled:
- **Branch at `clavicle_l`, local-space rotation.** Mesh-space rotation pinned
  the arm to the mesh (feet) direction, so the aim-offset torso twist left it
  behind. With local space it rides the spine: it follows the twist and moves
  with the fire montage's torso motion.
- **Branching at `upperarm_l` was tried.** The clavicle then came from the
  two-handed clips and pulled the arm forward while strafing. Reverted.
- **Free-arm jog swing was tried twice** (2026-10-07 and 2026-10-09) and dropped.
  - **Setup:** a `MM_Unarmed_Jog_Fwd` player as an Always Follower in the
    `Locomotion` sync group, blended in by speed from `clavicle_l`.
  - **Why it never synced to the feet:** the raised legs come from
    `BS_Pistol_Strafe`, whose Lyra pistol clips have **no foot sync markers**
    (only `AN_FootPlant_*` notifies). `MM_Unarmed_Jog_Fwd` has a
    `FootSyncMarkers` track, so UE fell back to normalized-time sync and the
    swing ran out of phase.
  - **Swapping the swing source** to `MM_Pistol_Jog_Fwd` doesn't help: that
    clip is two-handed.
  - **If a clip-based swing ever comes back:** add sync markers (same names as
    the unarmed jog) to the pistol strafe clips first.
- **Procedural arm swing (2026-10-09, user-confirmed)** — replaces the
  clip-based attempts.
  - **C++ (`UpdateFreeArmSwing`):** each frame, the fore-aft gap between
    `foot_r` and `foot_l` along the **actor's forward** vector, read from last
    frame's pose. A + value means the right foot leads.
  - **Auto-gain:** the gap is divided by `FreeArmStridePeak`, the largest
    recent gap. The peak rises at once and falls back toward a floor over about
    a second; the floor is `FreeArmMinStride`, 8 cm. This lets small side-step
    gaps still give a full swing; with a fixed 50 cm stride, strafing barely
    swung.
  - **Smoothing:** the phase is smoothed (FInterpTo 12) and faded in by speed
    (full at 300).
  - **Output:** `FreeArmSwingRotation = FreeArmSwingFull × phase`. The user
    set `FreeArmSwingFull` to 10° (the C++ default is roll 25).
  - **Graph:** `ModifyBone_5` on `upperarm_l` — additive, **component
    space**, Rotation pin ← `FreeArmSwingRotation`, alpha `FreeArmAlpha`. It
    sits between the free-arm layer's Local→Component and the free-arm recoil
    node (`ModifyBone_4`).
  - **Why it works everywhere:** it reads the real feet, so it stays in step
    whatever clip drives the legs: forward, backpedal (the body-relative
    opposite-arm rule holds), both strafes, any gait rate.
- **Reload:** `FreeArmReloadBlend` eases the layer out and back in, instead of
  switching off.
- **Lowering:** the one-handed pistol is exempt from the raised-to-lowered snap.
- **Stance flipped to right foot forward** (user, 2026-10-09).
  - **How:** *Mirror with MDT_Mannequin* nodes on the one-handed pistol's
    **Idle-state** players — the lowered unarmed idle and the raised hip-fire
    idle — on their own players, so other anim types aren't flipped.
  - **Why the gun stays right:** only the legs and pelvis of the mirrored
    hip-fire clip survive. The raised upper-body layer replaces everything from
    `spine_01` up, blended in mesh space. The gun stays in the right hand and
    the torso doesn't flip.
  - **Not affected:** moving (Move state), crouch, duals.
  - **Considered and dropped:** a bladed stance, either a procedural pelvis yaw
    or an authored shoulder-forward clip. The plain flip looked better.
  - **A mirror on the top-level lowered-dual idle** flips only duals, since
    that layer is weighted by `DualLoweredAlpha`. It was tried and removed.

**Free arm on physics (2026-10-17):**
- **When:** with the one-handed pistol raised (not reloading or equipping),
  the free left arm (`upperarm_l` and below) goes on physics.
- **Behaviour:** the motors hold it toward the at-side pose and its
  procedural swing (`FreeArmHoldStrength` 600), so the arm lags turns, sways
  with strafing and settles after recoil. It blends on and off over
  `FreeArmBlendTime` 0.2 s.
- **Code:** `ABopisCharacterBase::UpdateFreeArmPhysics` and
  `WantsFreeArmPhysics()` (virtual; the player adds "not diving, not
  rolling"). Settings are under *Animation|Free Arm*, `bFreeArmPhysics`.
- **Yields:** to a dive's loose arm, a hit reaction, a stagger or death.
- **Enemies:** they share the base class, so one with a one-handed pistol
  gets it too.

**Bladed stance (2026-10-18, user: "looks good"):** a moderate one-hand
blade, right hand forward, for the one-handed pistol raised. **Player only
(2026-10-19):** the arm turn aims at the camera's crosshair, so AI got the chest
turn without the correction and aimed left; the condition now includes
`IsPlayerControlled()`. The reference was
Chow Yun-fat's one-hand stance, less side-on, and it has to work while
strafing.
- **Why it's needed:** the one-handed pistol's raised strafe is
  **`BS_Rifle_Strafe`** (the Move state's `EWeaponAnimType` blend, slot 4),
  bladed to the *right*. A right-hand-forward blade would twist the torso
  about 90°.
- **Lower body (mirrored):** at the top level, a second `BS_Rifle_Strafe`
  player is fed `CardinalDirectionMirrored` (= −`CardinalDirection`), so the
  mirrored feet step the way you're moving. Its Y is `Speed`, its play rate a
  fixed 0.75 (the ABP's `LocomotionPlayRate`; the pin isn't exposed). It goes
  through a Mirror (`MDT_Mannequin`), then **`LayeredBoneBlend_10`**: filter
  `pelvis`, weight `StrafeBladeAlpha`.
  - It reads the existing `Loco` cache as its base and feeds the upper-body
    layer `_0`. That layer blends from `spine_01` in **mesh space**, so the
    torso keeps its orientation over the mirrored hips.
  - `StrafeBladeAlpha` eases in with the one-handed pistol raised, standing,
    not diving. Switch it off with `bBladeStance`.
  - Known gap: the mirrored copy skips the Orientation and Stride Warping,
    which run before `Loco`.
  - **Waist twist spread (2026-10-22):** with `_0` taking over at `spine_01`,
    the whole hips-vs-torso difference sat on the pelvis → `spine_01` joint,
    which on CC characters swung the jeans' waistband out from under the shirt
    hem. `LayeredBoneBlend_13` is a copy of `_0` (same base, same
    `UpperBodyAlpha`, mesh-space rotation) with `spine_01` **blend depth 3**,
    so the torso fades in over `spine_01`/`02`/`03`; `TwoWayBlend_0` picks
    between `_0` (A) and `_13` (B) by `StrafeBladeAlpha` and feeds
    `RotationOffsetBlendSpace_0`. Other stances are untouched.
  - **`LayeredBoneBlend_10` goes through a Save Cached Pose `BladeLegs`**
    (2026-10-23), read by one Use Cached Pose each for `_0` and `_13`. Wired
    straight into both, its mirrored strafe player was updated twice a frame
    while the TwoWayBlend had both sides relevant: double-speed legs for the
    second or two `StrafeBladeAlpha` took to settle after a shot from a jog.
    **Rule: a pose feeding two parents goes through a cached pose.** (The
    bridge can't create a Use Cached Pose for a cache made in the same
    session — its node list doesn't refresh; the user placed them.)
- **Upper body (`UpdateBlade`):** weighted `StrafeBladeAlpha × (1 −
  ProneReloadAlpha)`, so it's off for reloads and draws.
  - **Chest:** `BladeAngle` (35°) about the vertical, half each on
    `spine_03`/`spine_05` (`BladeSpineTurn`).
  - **Head:** turns back by the same, half each on `neck_01`/`head`
    (`BladeHeadTurn`).
  - **Arm:** `upperarm_r` turns so the shoulder-to-hand line points at the
    camera-traced aim point (`BladeArmTurn`, cap `BladeArmMaxAngle` 60°).
  - **Hand:** `hand_r` then lines the barrel up with the crosshair
    (`BladeHandTurn`, cap `BladeHandMaxAngle` 45°).
  - Both corrections are worked out fresh each frame, with their own turn
    taken back out, as for the dive. They're Transform (Modify) Bone nodes on
    the standing branch (add, component space) after `LocalToComponentSpace_1`
    and before the spine recoil.
- **Tried and dropped:**
  - the arm turned from the shoulder to aim the *muzzle*: the hand stayed at
    the chest and the body hid the arm;
  - Two Bone IK on `hand_r` along the shoulder line: the arm didn't follow;
  - the hand turn alone, without the arm turn.
- **Left arm:** still the free-arm pose `MM_Pistol_Idle_OneHanded`, which the
  user re-authored for the blade. An unused `_Bladed` copy from 10-09 was
  deleted.
- **Equip:** the free arm now eases out for equip montages too
  (`bEquipAnimating`), so the one-handed draw plays its own left arm.

**Backsteps (2026-10-18):** `UpdateLocomotion` picks the strafe clip with
hysteresis (`CardinalSwitchAngle` 55°). Strafing right and then moving
back-right kept the forward-facing side clip, and Orientation Warping twisted
it about 45° toward the back: the torso over-twisted.
- Now travel at or past **`BackstepMinAngle`** (105°) from forward always
  picks the 180° backstep, whichever way the strafe came from. It stays there
  until the travel is `BackstepHysteresis` (10°) further forward.
- It covers every weapon's strafe, and the mirrored blade copy too.

### Lean into turns (2026-10-23)
Walking or jogging with the gun lowered, the torso banks into a turn by the
turn rate — the free run's own rotation toward the movement direction, so
enemies lean too. Never with the weapon raised (a strafe turn is the camera,
not the body), nor crouched, diving, rolling or in the air.
- **C++ (`UProjectBopisAnimInstance::UpdateLean`):** `YawRate` = the actor's
  yaw delta per second; `LeanAngle` eases (`LeanInterpSpeed` 6) toward
  `clamp(YawRate × LeanPerYawRate (0.1) × min(Speed / LeanFullSpeed (500), 1),
  ±MaxLeanAngle (15))`, or 0 when the gate fails. `LeanSpineRotation` =
  `LeanPerDegree × LeanAngle / 3`. `LeanPerDegree` (default pitch 1, i.e.
  about the component's Y = the body's forward axis, positive banking right)
  is the escape hatch if it banks the wrong way or axis — flip it on the ABP
  defaults, as with `FreeArmSwingFull`. `bLeanIntoTurns` switches it off.
- **Graph:** three Transform (Modify) Bone nodes (`ModifyBone_36/37/38`:
  `spine_01/02/03`, additive, component space, alpha 1, Rotation ←
  `LeanSpineRotation`) on the standing branch right after
  `LocalToComponentSpace_1`, before the blade's chest turn.

### Gait — slower cadence with stride warping (2026-10-07)
Lyra's locomotion was accurate but read as cartoonish; Max Payne 1–2 is the
reference. Every locomotion/idle clip player runs at `LocomotionPlayRate`
(0.75 on `ABP_Player`). Movement speeds are unchanged, so the feet would slide.
**Stride Warping** (Graph mode) lengthens each step to match the capsule speed:
- `LocomotionSpeed` ← `Speed`; it compares that against the clips' root-motion
  speed (Lyra clips carry root motion), so it compensates for the slower rate
  by itself.
- Stride-scale clamp 0.5–1.5. Pelvis `pelvis`, IK foot root `ik_foot_root`,
  feet `ik_foot_l/r` / `foot_l/r` / `thigh_l/r`.
- **Leg IK** (`ik_foot_*` → `foot_*`, 2 bones) then solves the legs onto the
  warped IK feet.

Graph mode was chosen over Manual: Manual needs a stride-direction vector in
component space from C++. A C++ `StrideScale` added for Manual mode was
removed unused. Keep `LocomotionPlayRate` ≥ 0.75; below that the stretched
strides show.

### Procedural recoil (2026-10-07)

**Fast guns (2026-10-16):** at the assault rifle's 0.1 s the fire montage
restarted mid-kick and the spring saturated, holding the gun up above where
the rounds go for a whole burst. `PlayFireAnimation` now plays the fire
montage at clip length ÷ `TimeBetweenShots` (1–`MaxFireMontageRate` 4×) and
scales the spring impulse by `TimeBetweenShots ÷ FullKickInterval` (0.25 s;
clamped 0.25–1) via `AddRecoil(bOffhand, Strength)`. Slow guns unchanged;
enemies share it. User-confirmed: "works".

**Why:** the fire montage restarts from frame 0 on every shot (`Montage_Play`,
0.25 s blend-in), so spam fire never reaches the kick — invisible while
strafing. Setting the fire montages' blend-in to 0 looked worse and was
reverted.

**How:**
- Two springs in `UProjectBopisAnimInstance`, main hand and off hand
  (`UKismetMathLibrary::FloatSpringInterp`, target 0, clamped 0..1).
- `AddRecoil` adds `RecoilImpulse` to the matching spring's **velocity**. Rapid
  shots stack up to 1 instead of restarting.
- Hitting a clamp zeroes the velocity, so the spring saturates at 1 and stops
  dead at 0 with no undershoot.
- One shot peaks at about 0.56 with the defaults.
- The fire montage still plays on top.

**AnimGraph** (step 5 above):
- Three Transform (Modify) Bones — rotation **Additive, bone space**,
  translation and scale Ignore.
- **Yaw is the bend axis** on these mannequin bones (found by testing).
- Full-kick angles, tuned on each node's Details:

| Bone | Yaw (full kick) | Alpha |
|---|---|---|
| `spine_05` | −6° (lean back) | `SpineRecoilAlpha` |
| `lowerarm_r` | +20° (forearm up) | `ArmRecoilAlpha` |
| `lowerarm_l` | +20° | `OffhandArmRecoilAlpha` |
| `lowerarm_l`, after the free-arm layer | +15° | `FreeArmRecoilAlpha` |

**Pins:** the Translation/Rotation/Scale pins are hidden on all four nodes —
see *Engineering gotchas*.

### Turn-in-place (2026-10-05)
Lyra approach; built in the AnimBP, now in `UpdateTurnInPlace` (C++). The capsule still follows the camera
(`bUseControllerRotationYaw`), so gameplay and aim are untouched; only the
visible mesh lags.

- **Can turn** = raised AND raised last frame (`bWasWeaponRaised` — the raise
  frame keeps the hip-fire yaw snap) AND `Speed < 5` AND NOT crouched.
- **Planted feet:** if can turn, `RootYawOffset = Clamp(NormalizeAxis(Offset −
  capsule yaw delta), ±120)`; otherwise FInterpTo → 0 (speed 10). Rotate Root
  Bone counter-rotates the body; the aim offsets twist the torso back to the
  camera.
- **Trigger:** `|Offset| > TurnThreshold` (**45** since 2026-10-06, was 90) and
  `TurnSlot` inactive → `Montage_Play` (`AM_Rifle_TurnRight_90` if Offset < 0,
  else `AM_Rifle_TurnLeft_90`) with `bStopAllMontages = false`. *(Correction
  2026-10-06: that flag only stops montages in the same slot group — here
  `TurnGroup` — not fire/reload, so `true` would also have been safe.)*
  `TurnScale = |Offset| / 90` is stored at trigger.
- **Wind-down:** `C = RemainingTurnYaw / TurnYawWeight` (when weight > 0.01);
  `Offset −= (C − PrevTurnYawCurve) × TurnScale` once a previous value exists.
  `TurnScale` makes a turn close exactly the gap that triggered it (≈0.5 at
  45°). 45° caps how far the aim offset twists the torso — the shotgun's pump
  went out of left-arm reach beyond that.
- **Cancel:** when turning isn't allowed → `Montage_StopGroupByName(TurnGroup,
  0.2)`. **Not** `StopSlotAnimation` — that only stops dynamic montages.
- **Clips:** `MM_Rifle_TurnLeft/Right_90` with **Enable Root Motion off** —
  with it on, the montage locked movement input until the turn ended. Rifle
  clips serve every weapon: when raised, the upper body comes from the
  hip-fire layer, so only legs/pelvis show the turn.
- **Crouched turns (2026-10-15).** "No leg movement when looking around on
  crouch": crouch was excluded from *can turn*, so the mesh turned rigidly with
  the capsule.
  - `CrouchTurnLeftMontage` / `CrouchTurnRightMontage` (Class Defaults → Turn
    In Place). With both set, *can turn* allows crouch and crouched turns play
    them; with either empty, crouch behaves as before.
  - Assets: `Pistol/AM_Pistol_Crouch_TurnLeft_90` / `_TurnRight_90`, made
    through the bridge by **duplicating** the rifle turn montages and pointing
    their segment at `MM_Pistol_Crouch_TurnLeft/Right_90` (same `TurnSlot`,
    blends, curves). The pistol crouch clips serve every weapon.
  - **The clips came with Enable Root Motion ON** (the rifle turn clips have
    it off): each step rotated the capsule while the Aiming stance snapped it
    back and turn-in-place counter-rotated the mesh — a constant re-stepping
    stutter. Turned off on both clips.
  - The Right montage's length first read the source's 1.70 s (clip 1.633 s);
    by 2026-10-16 it read 1.633 s — the editor recalculated it once the
    segment had changed. No fix needed.
- **Quick turn to aim (2026-10-15).** "When rolling and not facing forward
  then shooting, there is a snap to face forward, this needs a quick lerp."
  - Entering the Aiming stance with the body more than 1° off the camera sets
    `bTurningToAim` and leaves `bUseControllerRotationYaw` off;
    `UpdateAimTurn` (Tick, after `UpdateMovementStance`) turns the actor
    `FMath::FixedTurn` at **`AimTurnRate` 1080°/s** (world time), then locks to
    the camera. 0 = the old snap.
  - The fire code's instant `SetActorRotation` from the lowered stance was
    removed; the stance change does the turn. The first shot leaves mid-turn
    (under 0.17 s); it still goes to the crosshair.
  - **Turn-in-place sits the turn out:** the anim instance reads
    `IsTurningToAim()` and *can turn* requires it false. Otherwise it would
    counter-rotate the mesh and cancel the visible turn.

### Slots
`DefaultSlot` (DefaultGroup), **`OffhandSlot` in its own `OffhandGroup`**, and
**`TurnSlot` in its own `TurnGroup`** — separate groups so off-hand reloads and
turns can play alongside fire/reload montages (playing a montage stops others
in its group).

### Sync groups
Leg blend spaces in the Move state carry group `Locomotion` (CanBeLeader) from an
experiment; **sync to top-level arm players never demonstrably worked**. Cause
found 2026-10-09: the Lyra **pistol** locomotion clips have no foot sync markers
(the unarmed ones do), so a follower falls back to normalized-time sync and
drifts out of phase with the feet. The
lowered-dual branch avoids the need by taking the whole body from one clip. The
settings are harmless; treat sync between in-state and top-level players as
unreliable.

### Decided against
- Shotgun upper body layered over Lyra legs (looked bad).
- ~~One-handed single pistols with an unarmed free arm (every variant looked
  worse) — single pistols keep the two-handed grip.~~ **Reversed 2026-10-07** —
  built with a dedicated at-side pose; see *One-handed pistol*.
- Fire montage blend-in 0 (tried 2026-10-07 for rapid-fire recoil) — looked
  worse; procedural recoil instead.
- Free-arm jog swing on the one-handed pistol (2026-10-07) — removed by the user.
- Procedural dual arm spread, and a runtime run-and-gun spread alpha
  (2026-10-07) — see *Dual spread*.
- Left strafe as the right strafe mirrored, via the blend space's per-sample
  **Mirror** flag + `MDT_Mannequin` (tried by the user 2026-10-08, rolled back):
  the torso over-twisted. Likely cause: the mirrored clip also flips the
  pelvis/spine twist, and the raised layer blends from `spine_01` in mesh space
  over it. If it's revisited, mirror only the legs — a layered blend from
  `thigh_l`/`thigh_r` over a mirrored copy — rather than the whole sample.

### Open
- Turn-in-place extras: 180° turns, crouched turns (crouch clips exist),
  per-weapon turn sets.
- Inertialization for the remaining two-handed snap, if it ever reads badly:
  the node is now in place; request `RequestSlotGroupInertialization
  ("TurnGroup", 0.3)` on the snap frame (TurnSlot is always evaluated; a slot
  forwards requests even with nothing playing — checked in engine source).
  **Request from inside the anim update** (e.g. `NativeUpdateAnimation`) — from
  the character's Tick it lands a frame after the discontinuity and smooths
  nothing.
- Shotgun-specific idle: `MM_Shotgun_Idle_Hipfire` exists in the Lyra set and
  could replace the borrowed rifle hip-fire pose.
- ~~Strafe jog play rate / stride warping if feet slide at 500.~~ Done
  2026-10-07 (*Gait*).
- Recoil per weapon: angles and impulse are global today. They could move
  onto the weapon as data, as `AnimType` does, if pistols and shotguns need
  different kicks.
- Dual left-arm recoil sign (`lowerarm_l` +20°) is set by symmetry, not yet
  checked on duals.
- Shotgun aim offset: uses the rifle AO (fine so far); unarmed AO samples
  probably have the same missing-base-pose fault if ever used.

## Combat abilities — dual-wield, shootdodge, Focus (slow motion)

Designed 2026-09-30. **Dual pistols built 2026-10-04**; shootdodge not built; slow motion built 2026-10-09 as *Focus*. Recorded because the animation
constraints shape the code, and the approaches below were worked out against
what the project actually owns.

### Dual pistols — built 2026-10-04 (demo)

**One weapon, two meshes.** `AWeaponBase` has an `OffhandMesh` component
(present on every weapon, unused unless `bDualWield`), plus
`OffhandGripLocationOffset`/`RotationOffset`. The holder attaches it to
`OffhandAttachSocketName` (`hand_l`) on equip and re-attaches it to the weapon on
unequip (while equipped it lives on the character's skeleton). Ammo, bloom and
fire rate are one shared pool; the holder, fire input and HUD stay
single-weapon.

- **Alternate fire** (L/R): `GetFiringMesh()` picks the hand; `GetMuzzleLocation()`
  follows it, so the two-stage trace needs no change; sound/flash/weapon fire
  anim play on the firing mesh; `WasLastShotOffhand()` tells the character which
  arm to animate (`OffhandFireMontages`, falling back to `FireMontages`).
- **Reload normally** (user decision 2026-10-04) — **supersedes the earlier
  "throw them away when dry" design.** One reload timer refills the shared pool;
  the character plays `ReloadMontages[type]` plus, for dual weapons,
  `OffhandReloadMontages[type]` in `OffhandSlot` (own slot group).
- **Animation:** see *Animation architecture* — mirrored pistol idle on the left
  arm when raised, off-hand montages mirrored onto it, whole-body unarmed
  locomotion with finger grips when lowered.
- `BP_DualPistols`: mag 24, reserve 120 (max 240), **`AnimType Dual`** (was
  `Pistol` until 2026-10-07).

### Dual spread (2026-10-07)
**Problem:** from the right-shoulder camera, the mirrored left gun sat behind the
head while running and gunning.

**Final design — authored, keyed by anim type:**
- **`EWeaponAnimType::Dual`**, shared by dual pistols and the planned **dual
  SMGs**. `IsPistolAnimType` includes it, so every pistol-vs-long-gun switch
  treats duals as a pistol hold. Ammo stays per weapon (`AmmoType`).
- **Hip-fire and run-and-gun:** spread poses.
  - Idle: `MM_Pistol_Idle_Hipfire_Dual` (the user's copy with the right arm
    spread out; the Mirror makes the left arm match).
  - Fire: `AM_Dual_Fire` / `AM_Dual_Fire_Offhand`, on `MM_Pistol_Fire_Dual`.
    Its upper arm sits 5° off the idle's on purpose, so the arms visibly move
    between shots. Additive base: **Local Animation Frame, frame 0** (pure kick;
    see below).
- **Aiming:** the original narrow poses.
  - Idle: `bDualSpread` is false, so the graph's bools pick `MM_Pistol_Idle_Hipfire`.
  - Fire: the character's new **`AimFireMontages` / `AimOffhandFireMontages`**
    maps (`dual` → `AM_Pistol_Fire` / `AM_Pistol_Fire_Offhand`).
- **Montage lookup order** in the character's fire code: aimed off-hand →
  off-hand → aimed → plain (a `TryMap` lambda; the first entry found wins).
  Other anim types have no aim entries, so they're unchanged.
- **Asset locations:** the recreated `AM_Pistol_Fire_Offhand` lives in
  `Characters/Mannequins/Anims/Pistol/` and uses that folder's template
  `MM_Pistol_Fire` (Local Animation Frame base). The main-hand `AM_Pistol_Fire`
  uses Lyra's clip in `Characters/Heroes/.../Actions/`. The user is happy with
  the mix.

**Why the fire clip's base pose mattered:**
- Lyra's `MM_Pistol_Fire` is a mesh-space additive with base type *Selected
  animation frame*, but **no base animation set**. Engine source: that mode
  needs one. The delta was baked against some other pose.
- Layered over the spread idle, each shot dragged the arms back toward the
  narrow grip; they spread again once the montage ended.
- A base of the clip's own frame 0 makes the delta pure kick, so it rides on
  whatever pose is underneath.

**Tried and dropped:**
- Procedural `upperarm_l` spread (Modify Bone, pitch +20°) — deformed the
  shoulder.
- A dual-only aim pose clip (2026-10-25, for the jacket seams bending in the
  dual aim) — wired in, then rolled back before posing: the user judged the
  pose fine.
- Camera pull-in for duals — not pursued.
- A runtime run-and-gun alpha blending the spread clip under, then over, the
  slots — never held through shots (the base-pose problem above). Reverted.

The old note about dual SMGs needing a `bOneHanded` flag is superseded:
`AnimType Dual` covers them.

**Dual reload: torso and off-hand shoulder held (2026-10-25; was an accepted
quirk since 2026-10-05).** The reload montage, authored for a two-handed
reload, leaned and twisted the torso, dropped the left shoulder and pushed
the left armpit into the body (user: "I want no movement on lower to middle
spine ... the shoulder on the left dips hard"). Instead of the no-spine clip
copy considered then, the AnimGraph holds bones to the idle while duals
reload, by `UProjectBopisAnimInstance::DualReloadHoldAlpha` (FInterpTo toward
`bIsDualWield && bReloadAnimating`, `DualReloadHoldSpeed` 10):
- **Spine hold** — Layered Blend per Bone `LayeredBoneBlend_14` between
  `DefaultSlot` and `SaveCachedPose_1`: Base = the slot (montage), Blend =
  its own `MM_Pistol_Idle_Hipfire` player, filters **`pelvis` 0 +
  `spine_04` −1**, local space. A negative blend depth subtracts that
  branch's weight (`FAnimationRuntime::CreateMaskWeights` adds
  `(1/depth)·(depth+1)` per bone, clamped), so only the pelvis and
  `spine_01`–`03` are held; the upper chest and arms still reload. To hold
  `spine_04` too, change the −1 filter to `spine_05`. Everything reading
  that cached pose gets it.
- **Off-hand shoulder hold** — `LayeredBoneBlend_15` between `OffhandSlot`
  and its aim offset (pre-mirror): filters **`clavicle_r` 0 + `upperarm_r`
  −1**, so just the collarbone — mirrored, the left shoulder.
The dive/prone reloads use their own branch and are untouched.
**User-tested 2026-10-25:** "reload works" (spine hold as built, `spine_04`
free).

### Dual pistols in the dive: off-hand montages and recoil (2026-10-18, user-confirmed)

- **The off-hand montage reaches the dive branch:** the standing chain is
  Off-hand Slot → off-hand aim offset → `Mirror_0`, now saved as the cached
  pose **`OffhandMirror`**. It's read twice:
  - by the standing left-arm layer (`LayeredBoneBlend_1`, from `clavicle_l`);
  - by a new dive-branch layer, `LayeredBoneBlend_9`. It sits after the
    upper-body reload layer (`_8`), filters from `clavicle_l` with mesh-space
    rotation, and is weighted by `ProneDualOffhandAlpha`
    (`ProneReloadAlpha` while dual-wielding, else 0).
  - So dual reloads and draws in the air and prone mirror the right hand, not
    the two-handed pistol's left half.
- **Standing left-gun kick:** the duals' left-arm recoil (`ModifyBone_3`,
  `lowerarm_l`, weighted by `OffhandArmRecoilAlpha`) was before `_1` and got
  overwritten by the mirrored arm. It now sits after `_1` (L2C → recoil →
  C2L → `_4`), as the dive branch's `ModifyBone_8` already did.
- **Bridge limits hit here:**
  - a second Slot node with the same name is rejected ("SLOTNODE: 'OffhandSlot'
    … already exists"), and its montage never plays;
  - the bridge can create a Save Cached Pose, but not a Use Cached Pose for a
    new cache. The user placed those.

### Shootdodge

#### Built — step 1, the dive (2026-10-10, user-confirmed in PIE)

**Design (user):**
- **Left Shift**, action `IA_Shootdodge` (Shootdodge).
- Dive **in the movement input's direction relative to the camera**, in any
  stance. The body snaps to the camera first. No input = forward.
- **Focus:** needs ≥ `MinFocusToDive` (25) to start. *(Revised 2026-10-17; before,
  it spent `FocusCost` 25 once and the flight's slow motion was free.)* The
  slow motion now **drains `FocusDrainPerSecond` 5 per real second** from
  take-off to landing (`UFocusComponent::BeginFreeFocus(DrainWhileFree)`), and
  **running dry mid-dive doesn't end it**: `TakeOff` sets
  `Focus->SetHoldOnEmpty(true)`, `EndSlowMotion` clears it — which also keeps
  the player's own Focus (if it was on) from cutting out mid-dive. The user:
  "it drains continuous as the shootdodge is happening… running out will not
  stop the shootdodge focus". The roll's free moment and the death slow motion
  stay free (drain 0).
  Slow motion on after take-off and off on landing comes in step 2; a Focus
  already running stays on.
- Fire and aim freely; no supernatural speed-up of anything.
- Prone until the first movement input; can fire prone.
- **Pistol, one-handed pistol and duals only** (`IsPistolAnimType`).
- **No wind-up:** launch on the press.

**Asset: `Content/Dodge_Prone_Anim_Set/`** (re-imported 2026-10-10 after a
rollback, below). 131 clips, all `_P` (pistol).
- `Dodge/`:
  - `anim_Dodge_Start / Loop / End / Getup_<dir>_P` for 8 directions (Fwd,
    Fwd_Right, Right, Bwd_Right, Bwd, Bwd_Left, Left, Fwd_Left);
  - `anim_Dodge_Idle_P`;
  - `anim_Prone_<dir>_Aim_Up / Mid / Down_P`: 24 full poses, a 360° × pitch
    aim set for lying down (step 3's blend space).
- `Prone/`: crawl, transitions, prone fire, prone turn-in-place. Unused.
- **Clip setup:**
  - the pack ships with **root motion off**;
  - all 131 clips: **Force Root Lock on, `RootMotionRootLock` = Anim First
    Frame**;
  - **except the 8 `anim_Dodge_End_*_P` → Ref Pose**: their first frame is
    still airborne, so Anim First Frame floated the landing above the floor,
    then prone pulled it down;
  - the pack's `SK_Mannequin` is a Compatible Skeleton on ours;
  - **the Right clips' glitch** (a sudden shift at the peak, then a swing back)
    was **fixed by the user keying corrections on the track** (additive keys
    in the clip). The pack's Right set is authored separately from Left (e.g.
    Getup_Right is 2.63 s against Left's 1.77 s); no clip setting differed.

**`UShootdodgeComponent`** (`Gameplay/ShootdodgeComponent.h`) on the player:
- `TMap<EShootdodgeDirection, FShootdodgeAnims> Animations`:
  - `FShootdodgeAnims` = `Start`, `StartOffset`, `Loop`, `Land`, `LandOffset`,
    `Prone`, `Getup` (offsets −1 = use the component default);
  - enum order Forward, ForwardRight, …, ForwardLeft **is** the octant order;
  - bridge JSON keys are lower camel (`forward`, `forwardRight`, …).
- **`TryStart`:**
  - gates: on the ground, not crouched, not equipping, a pistol type, meter ≥
    min, a Loop clip present;
  - `PickDirection` takes `GetLastMovementInputVector()` in the camera's yaw
    frame and rounds to the nearest 45°;
  - `UFocusComponent::SpendMeter`;
  - snaps yaw to the camera, `SetAnimationDrivenRotation(true)` (stance
    `AnimationDriven`);
  - then **`TakeOff` immediately**.
- **`TakeOff`:**
  - saves, then overrides, on the movement component: `GravityScale` ×
    `DiveGravityScale` (0.6) and `BrakingDecelerationFalling` =
    `DiveAirBraking` (0). The player's 1500 air braking had stopped the dive
    mid-air.
  - `LaunchCharacter` along camera yaw + octant × 45°: `DiveSpeed` 650,
    `DiveLift` 450, both axes overridden. That's ~1.7 m peak, ~1.5 s up.
  - Plays Start from `StartClipOffset` (0.4 s, the push-off frame, in clip
    seconds), then Loop when it ends.
  - **First-dive bug — fixed 2026-10-16 (user-confirmed):** the very first
    dive of a session played the Start clip **from 0** — its standing
    wind-up, slow-motioned into seconds of "standing on one leg, arms out",
    which read as a hit reaction. The Start blend space reads its Start
    Position pin **once, when it initializes**, from the last value its
    exposed inputs saw; later dives inherit the previous dive's (correct)
    value, but the first saw the anim instance's default 0. The 10-12 attempt
    (setting the component's `PhaseStartPosition` in `BeginPlay`) couldn't
    work: the AnimBP initializes before the component's `BeginPlay`, and only
    copies the value per frame. **Fix:**
    `UShootdodgeComponent::GetRestStartPosition()` (the Forward clip's
    push-off, normalised, computed from the `Animations` defaults, so it's
    valid from construction) is read in the anim instance's
    `NativeInitializeAnimation` into `ShootdodgeStartPosition`. Found by
    stepping a screen recording frame by frame with `showdebug animation`
    on (Start state, P 0.36, body still at standing height).
- **`NotifyLanded`** (from `ACharacter::Landed`):
  - restores gravity and air braking;
  - **slide:** saves the walking braking settings, then sets
    `BrakingDecelerationWalking` = `LandSlideDeceleration` (800),
    `bUseSeparateBrakingFriction` true, `BrakingFriction` 0, and `Velocity.Z`
    0. Horizontal speed bleeds off at a constant rate: ~2.6 m.
  - Plays Land from `LandClipOffset` (0.5 s), skipping the clip's airborne
    lead-in so the impact lands at touchdown.
- **Then:** Prone (`Aim_Mid` pose, looped) → first movement input → Getup →
  `Finish`, which restores everything and returns to the FreeRun stance.
- **Play rates** (all directions): `StartPlayRate` 2, `LoopPlayRate`,
  `LandPlayRate`, `PronePlayRate`, `GetupPlayRate` 1. Offsets stay in clip
  seconds.
- Clips play as dynamic montages in `DeathSlot` (full body), with 0.1 s
  blends.
- **Player:**
  - `DoMove` routes to `NotifyMoveInput` while dodging (no air or slide
    steering);
  - `DoFire` doesn't snap yaw;
  - `UpdateCrouch` is skipped.
- **Known limits:**
  - sliding off a ledge while prone falls in the prone pose (the second landing
    isn't a dive landing);
  - arms follow the clips, not the aim, until step 2.

**Lessons from the first attempt (rolled back 2026-10-10, then re-applied):**
- A Ref Pose root lock on *all* clips flattened the dive into a slide. That
  needed the launch arc and lighter gravity, and it floated or misaligned
  some clips.
- The Lyra dash as a wind-up didn't match the pack.
- The Dodge Start clips are 1.2–1.4 s long, too slow as a wind-up. Hence
  "launch on the press, play Start from the push-off".
- Considered and set aside: **Motion Warping**, and **using the pack's root
  motion**. Root motion stays off; code drives the arc.

#### Built — steps 2–5 (2026-10-11, user-confirmed in PIE)

Some step 1 details above are superseded: the body no longer snaps to the
camera, and Start/Loop/Land/Prone are no longer dynamic montages.

**Design (user):**
- The dive's stages are **blend spaces** (Start, Loop, End), keyed on the dive
  direction relative to the body. The prone blend space is used **only after
  landing**. (My first version put the prone poses on an upper-body aim layer
  for the flight; the user corrected it.)
- **No snap on the press:** the body turns toward the camera smoothly.
- **Slow motion** after take-off, off on landing, free of meter cost.
- **Getting up is the drawback:** no firing during the get-up ("it gives you an
  extended focus but leaves you vulnerable on the ground").
- **No reload** in the dive's flight. ~~A reload press while prone gets you
  up~~ — superseded 2026-10-14: **reloading prone** happens on the floor (see
  *Dodge roll and the moves around it → Reloading*).
- **Focus Max Bloom Multiplier:** a tunable bloom scale during Focus (1
  normal, 0.5 half, 0 none). It replaced a "full accuracy in a shootdodge"
  request. Renamed **`FocusSpreadMultiplier`** 2026-10-15, and a dive is now
  exempt from the moving-spread penalty.

**Code:**
- **Direction:** `DiveYaw` = camera yaw + octant × 45°, fixed at take-off.
  `GetDirectionAngle()` = `NormalizeAxis(DiveYaw − actor yaw)`, −180..180.
  The blend spaces read it as `ShootdodgeDirection`.
- **Facing:** during Start/Loop/Land/Prone the tick `RInterpTo`s actor yaw
  toward camera yaw at `FaceAimSpeed` (10; 0 snaps). The flight path doesn't
  turn; the blend spaces swing the dive to match.
- **Phases:** `EShootdodgePhase` {None, Start, Loop, Land, Prone, GettingUp}.
  Start → Loop and Land → Prone on timers: the clip length minus the offset,
  over the play rate (`PhaseLength`). GettingUp ends when its montage ends.
- **AnimBP getters:** `GetPhasePlayRate()`; `GetPhaseStartPosition()`, the
  offset normalised 0..1 (blend space Start Position is normalised).
- **Anim instance vars:** `bShootdodging`, `ShootdodgePhase`,
  `ShootdodgeDirection`, `ShootdodgePlayRate`, `ShootdodgeStartPosition`,
  `ShootdodgeAimYaw`, `ShootdodgeAimPitch`.
- **Get-up:** still a dynamic montage in `DeathSlot` at `GetupPlayRate`. The
  clip is chosen from the octant the body lies in now
  (`OctantOf(GetDirectionAngle())`), because the player may have turned while
  down.
- **Free Focus:** `UFocusComponent::BeginFreeFocus` / `EndFreeFocus`
  (`bFree`).
  - No drain; ignores the meter.
  - Does nothing if Focus is already on.
  - A Toggle during free Focus claims it as the player's own — **except
    during a dive (2026-10-23):** `UShootdodgeComponent::CancelSlowMotion`,
    called first by `DoToggleFocus` and by `DoShootdodge` while
    `IsDodging()`, ends the slow motion instead (the dive's own via
    `EndFreeFocus`, or a Focus that was already on via `StopFocus`; the
    hold-on-empty is released); the dive carries on at full speed. With none
    running, the Focus key toggles the player's own Focus as usual and the
    dive key does nothing (`TryStart` refuses mid-dive). Landing's
    `EndSlowMotion` is a no-op after a cancel.
  - `TakeOff` begins it; `NotifyLanded` / `Finish` end it.
- **Get-up rules:**
  - `IsGettingUp()`: `DoFire` returns early (held fire goes through
    `DoFire`).
  - `RequestGetUp(bool bThenReload)`: `NotifyMoveInput` forwards to it.
  - *(Superseded 2026-10-14 by the prone reload: `DoReload` now reloads on
    the floor while `IsProne()`, and returns without reloading anywhere else
    in the dive.)* `DoReload` while `IsDodging()` calls `RequestGetUp(true)`
    and returns.
  - `Finish()` sets the phase to None first, then runs the queued reload via
    `AProjectBopisCharacter::ReloadAfterShootdodge()` (→ `DoReload`), so it
    can't re-queue.
  - An empty-magazine auto-reload while prone also gets you up (it goes
    through `DoReload`). *(Superseded the same way: it reloads prone.)*
- **Bloom** *(superseded 2026-10-15 — now `FocusSpreadMultiplier` /
  `GetSpreadMultiplier()`, applied in `AWeaponBase::GetCurrentSpread()`)*:
  `UFocusComponent::FocusMaxBloomMultiplier` (default 1, 0..1).
  - `GetBloomMultiplier()` returns it while active, otherwise 1.
  - `AWeaponBase::GetCurrentBloom()` (moved out of line) returns raw bloom ×
    the holder's multiplier, found with `FindComponentByClass`. It's used by
    `Fire`'s spread lerp and by the reticle.
  - Raw bloom still builds and decays during Focus.
  - Covers manual Focus and the dive (free Focus counts as active).
- **Camera:** while the phase isn't None or GettingUp, the boom eases to
  `ShootdodgeCameraHeight` (−60), `ShootdodgeArmLength` (300) and
  `ShootdodgeSocketOffset` (0, 50, 0), via `UpdateCameraTransition`.
- **User-tuned play rates:** Start 1.5, Loop 1, Land 1.5, Prone 1, Getup 3.

**Assets (`/Game/ThirdPerson/`):**
- `BS_Dodge_Start` / `BS_Dodge_Loop` / `BS_Dodge_End`: 1D, Direction
  −180..180, 9 samples (±180 both Backward); only Loop loops.
- `BS_Shootdodge_Aim`: the prone pose, 2D. X = dive direction, Y = aim pitch;
  27 poses. Weight interpolation set to 0.
- `ABP_Player`:
  - a user-built Shootdodge state machine (Start / Loop / Land / Prone, Always
    Reset on Entry), behind Blend Poses by bool `bShootdodging` (Reset Child
    on Activation);
  - each state's blend space takes X ← `ShootdodgeDirection`, PlayRate ←
    `ShootdodgePlayRate`, StartPosition ← `ShootdodgeStartPosition`; Prone's
    Y ← `ShootdodgeAimPitch`;
  - `DeathSlot` sits after it, for the get-up.

**Gotchas:**
- **A blend space written through the bridge doesn't build its sample grid**
  until it's opened, edited and saved in the editor. Until then it plays
  sample 0 only, so every dive started "forward".
- **A duplicated blend space keeps `TargetWeightInterpolationSpeedPerSec`.**
  `BS_Shootdodge_Aim` had 5, which lagged the pose; set it to 0.
- `ABP_Player` also runs on every enemy: a debug Print String in it fires per
  character (misread values came from enemies, not the player).
- The bridge can read state machine graphs but not create nodes inside
  states, and it can't see AnimBP compile errors.

**Step 6, recoil in the dive (2026-10-11, user-confirmed in PIE):**
- **Cause:** the Shootdodge state machine fed Blend Poses by bool's True pin
  directly, so the normal chain's recoil nodes never ran while dodging.
- **Fix (bridge):** the shootdodge branch has its own recoil:
  Shootdodge → Local to Component → Modify Bone `spine_05` / `lowerarm_r` /
  `lowerarm_l` (copies of the main chain's: additive, bone space, −6° / 20° /
  20°; alphas ← `SpineRecoilAlpha` / `ArmRecoilAlpha` /
  `OffhandArmRecoilAlpha`) → Component to Local → True.
  - The new nodes are `ModifyBone_6–8`, `LocalToComponentSpace_3` and
    `ComponentToLocalSpace_3`.
- The fire montage is deliberately left out: its upper body is the standing
  hip-fire pose.
- **Bridge gotcha:** a Transform (Modify) Bone created through the bridge
  exposes Translation/Rotation/Scale as pins. An unconnected pin overrides the
  node's value with 0. Hiding the pins (copying `showPinForProperties`) writes
  the pin defaults back into the node, so **set the rotation after hiding the
  pins**.

**Step 7, legs through the floor (2026-10-11, user: "looks ok for now"):**
- **Cause:** `BS_Shootdodge_Aim` blends each bone's local rotation. Between
  dissimilar lying-down poses that averaging sinks the legs: knees between Fwd
  and Fwd_Left/Right, legs lifting or feet sinking between Right/Left and
  Bwd_Right/Left. The forward landing clip itself also sinks the legs.
- **Fix 1, hold the pose, then transition**
  (`UProjectBopisAnimInstance::UpdateProneDirection`):
  - Prone's blend space X reads **`ProneBlendDirection`** instead of
    `ShootdodgeDirection`.
  - Front span (<45°): holds Fwd_Left/Right, swapping to Fwd within
    `ProneForwardSnapAngle` (10°).
  - Back-side span (90–135°): holds Bwd_Right/Left, swapping to Right/Left
    within `ProneSideSnapAngle` (22.5°).
  - `ProneForwardSnapHysteresis` (5°) applies to both.
  - Elsewhere the pose follows the direction.
  - The pose eases at `PronePoseSwapSpeed` (5) along the shorter arc,
    `NormalizeAxis` (easing the raw number across ±180° swept the pose
    through the front).
  - `ProneBodyTurn` turns `root` by the difference, so the body still lies
    along the dive. `ProneSpineCounterTurn` turns `spine_01` and `spine_03`
    back by half each, so the gun still points at the aim.
- **Fix 2, mid-swap leg fix** (`UpdateProneFeet`):
  - Weight `ProneFootIKAlpha = |sin 4θ|` of `ProneBlendDirection`, in those
    two spans only. It's 0 on every authored pose and peaks halfway, so held
    poses are untouched. Eased at 10.
  - Front: the pelvis lifts (`ProneHipLift`) by the lower knee's shortfall
    under `ProneKneeClearance` (7). The user accepts a torso lift
    mid-transition.
  - Both spans: foot IK targets = animated foot + max(hip lift, the foot's own
    shortfall under `ProneFootClearance` 10). Feet are only raised, never
    pulled down.
  - **Feedback-free reads:** Copy Bones write `foot_*` → `ik_foot_*` and
    `calf_*` → the spare `ik_hand_*` before the fix. Those bones hang off the
    root, so C++ reads the legs as animated.
    - `ik_hand_l/r` are free on the shootdodge branch: the hand-grip IK only
      lives on the normal branch, which rebuilds them.
- **Fix 3, physics legs on landing**
  (`ABopisCharacterBase::SimulateLegs` / `EndSimulatedLegs`):
  - `NotifyLanded` puts `thigh_l/r` and below on physics with world-space
    physical-animation motors (`LandingLegHoldStrength` 2000), and turns on
    mesh physics collision. The floor pushes back on sunk legs.
  - `EnterProne` (and `Finish`) fade the legs back over
    `LandingLegBlendOutTime` (0.25 s).
  - It doesn't switch mesh collision off underneath a running hit reaction,
    or the reverse.
  - Settings: `bLandingLegPhysics` and the other options are on the
    Shootdodge component (*Landing Legs*).
- **Shootdodge branch now:** SM → L2C → twist ×3 → recoil ×3 → Copy Bones ×4 →
  pelvis lift → Two Bone IK foot_l/r (effector component space, joint target
  calf bone space, no effector rotation) → C2L → True.
- **Tried and dropped (don't retry):**
  - Mesh-space blending on the blend space: no effect. It's still on, and
    harmless.
  - Always-on foot IK: it bent the authored poses.
  - A pelvis lift everywhere: the body floated. It also probably fed back on
    itself, because it read the rendered knee.
  - Knee pull-back from the rendered knee: it hunted and jittered.
  - An exact knee solve (bisection over the IK geometry): still jittered.
  - An inertialized pose swap: it snapped. The Blend Poses by bool request
    never reached the Inertialization node, or the setup was off; not
    pursued.
  - Physics legs through all of prone, or weighted across the front span:
    too much jitter.
  - Foot planting on the back poses: didn't work, and the back turned out not
    to be the problem span.
- **Bridge gotchas:**
  - Nodes can't be created inside a state, and an existing getter's variable
    can't be repointed. The user rewires state internals.
  - The rebuild script's editor close saves dirty assets. Bridge-built graph
    changes survive it, but so does anything half-done.

**Step 8, wind-up (2026-10-11/12, user: "all sorted"):**
- **Design (user):** Max Payne 3's step into the leap.
  - It's an extra animation **before** the shootdodge, not part of it: no
    Focus spent, no slow motion, no launch until it ends. The dive itself is
    unchanged.
  - It plays **only when diving from a held aim** (`IsAiming()`, the aim
    button). Otherwise the dive goes on the press.
  - The run keeps going and slows gradually.
  - No firing, reload, weapon switch or jump during it.
- **Clips:** the first `WindUpLength` (0.2 s) of a Lyra dash, as a dynamic
  montage in `DeathSlot` at `WindUpPlayRate`.
  - Forward and its diagonals: `WindUpForward` (the user set
    `Unarmed/Jump/MM_Dash`).
  - Right and Back-Right: `WindUpRight`. The user made `MM_Dash_LeftMirrored`
    with an animation modifier.
  - Left and Back-Left: `WindUpLeft` (`MM_Dash_Left`).
  - Straight back, the Backward octant within 22.5°: `WindUpBackward`
    (`MM_Dash_Backward`).
  - A missing clip dives straight away.
- **Code (`UShootdodgeComponent`):**
  - `EShootdodgePhase::WindUp` is added **last**, so the AnimBP's enum
    comparisons don't shift.
  - `TryStart` runs the checks, sets animation-driven rotation, then
    `BeginWindUp` or `Launch`.
  - `Launch` holds what `TryStart` used to do after its checks:
    `SpendMeter`, stop movement, `DiveYaw` from the camera **at launch**, then
    `TakeOff`.
  - **During the wind-up:**
    - the body eases toward the aim, as in the dive;
    - root motion is ignored (`SetRootMotionMode`, restored at launch);
    - the run bleeds off at `WindUpDeceleration` (800 cm/s²), with braking
      friction off, restored at launch. Without this, ignored movement input
      let the normal braking stop the character dead.
  - **At launch:** `Montage_Stop(WindUpBlendOutTime 0.08)`.
  - **`IsWindingUp()`** stays true until the wind-up montage is fully blended
    out (the tick clears `WindUpMontage` once `!Montage_IsActive`).
    - Slow motion starts at launch, so a 0.15 s blend-out ran about 0.5 s of
      real time with the dash still showing while bullets flew.
    - It guards `DoFire`, `DoJumpStart` and `DoSelectWeaponSlot`. Reload is
      already blocked, because a reload press outside prone does nothing.
  - The anim instance's `bShootdodging` and the dive camera both exclude
    `WindUp`.
- **Tried and dropped:** playing the Start clips' own skipped lead-in
  (0..`StartClipOffset`) as a push-off. The user wanted the Lyra dash's
  running wind-up; the Start clips have no running start.

**Aim correction (2026-10-12, user: "looks good"):**
- **Problem:** the dive and prone clips aim where they were authored, while
  the shots go to the crosshair.
- **Fix:** `UProjectBopisAnimInstance::UpdateShootdodgeAimCorrection`, active
  only while `bShootdodging`.
  - Traces the camera view to the crosshair target (`GetPlayerViewPoint`, out
    to the weapon's max range; it ignores the character and the weapon).
  - Compares the barrel (the `Muzzle` socket's X axis, from the new
    `AWeaponBase::GetMuzzleTransform`, main-hand mesh) with the direction to
    the target, in mesh space.
  - **Computed fresh each frame:** take the measured gun direction, remove the
    correction currently applied (`Applied.UnrotateVector(gun)`), and use
    `FindBetweenNormals(pose gun, wanted)` as the target.
    - The first version accumulated instead (`FindBetween(gun, wanted) ×
      current`). Roll about the barrel is invisible to aiming, so it piled up
      and twisted the torso, head and dual left wrist (2026-10-12, fixed).
    - The head and the off-hand arm use the same fresh measure.
  - Capped at `AimCorrectionMaxAngle` (70°), slerped at `AimCorrectionSpeed`
    (12), and eased back to identity outside the dive.
  - Output: `ShootdodgeAimCorrection`, half the total, applied to **both**
    `spine_03` and `spine_05` (Modify Bones 13/14, additive, component space).
    They sit after the twist nodes and before the recoil.
  - It needs no per-weapon aim poses, so it should carry over to other weapons.
- **Assumption confirmed in Play mode:** the pistol's `Muzzle` socket X axis
  runs down the barrel. Other weapon meshes need the same check.

**Long guns and duals (2026-10-12, user: "looks good"):**
- **Gate:** `bPistolsOnly` on the component (default off), so every weapon
  can dive. There are no long-gun dive clips; the pistol dive is reused.
- **Long guns:**
  - **Arm hold:** a Layered Blend per Bone (`clavicle_l` + `clavicle_r`, local
    space) over the dive SM with `MM_Rifle_Idle_Hipfire`, weight
    `ShootdodgeLongGunAlpha`.
  - **Left hand:** Two Bone IK `hand_l`, effector in **`hand_r` bone space**
    at `LeftHandGripLocation` (the standing grip offset; it moves with the gun,
    no lag), joint target `lowerarm_l`. Alpha `ShootdodgeLeftHandAlpha`.
  - **Aim split:** the rifle hold needs far more lift than the pistol arms;
    putting it all on the spine bent the back.
    - Each frame: `Whole` = the fresh turn from the gun with (Arm × Chest)
      removed; swing/twist about up.
    - The chest gets clamp(tilt, `LongGunMaxPitch` 20°) × clamp(yaw,
      `LongGunMaxYaw` 35°) on `spine_04/05`.
    - The arms get exactly the rest (`Whole × Chest⁻¹`, capped
      `LongGunArmMaxAngle` 60°) on `upperarm_l/r`.
    - A straight split, because an earlier version that switched the arms on
      at the chest limit jittered.
    - Lying back, a turn about the vertical is a sideways bend, hence the yaw
      cap.
  - **Head look:** `neck_01/head` (half each) turn the head's forward toward
    the target, capped `HeadLookMaxAngle` 60°. The head's forward is from the
    reference pose (`FAnimationRuntime::GetComponentSpaceTransformRefPose`;
    mesh +Y).
  - Pistols keep `spine_03/05`. The outputs cross-fade by
    `ShootdodgeLongGunAlpha`.
- **Duals:**
  - **Left arm:** the dive clips are two-handed, which clasped the left gun to
    the right one. A Layered Blend per Bone (`clavicle_l`) now takes
    `MM_Pistol_Idle_Hipfire` → Mirror (`MDT_Mannequin`), weight
    `ShootdodgeDualAlpha`.
  - **Left gun aim:** its own self-correcting aim on `upperarm_l` from the
    off-hand muzzle (`GetMuzzleTransform(true)`), capped `OffhandAimMaxAngle`
    60°.
- **Back-pose gun lift (pistols and duals):** the back poses held the guns at
  the hips, between the legs.
  - Both upper arms rotate by +θ, and both hands by −θ, about (gun × up), so
    the guns rise without changing aim.
  - θ = `BackGunLiftAngle` (35°) × clamp((|dir| − 90)/45), eased.
  - The nodes sit right after the twist, before the corrections.
- **Shootdodge branch order now:** SM → rifle arm layer → dual left-arm layer
  → L2C → twist ×3 → lift ×4 → pistol correction (spine_03/05) → long-gun
  chest/arms/head → off-hand `upperarm_l` → recoil ×3 → long-gun left-hand IK
  → leg-fix Copy Bones → pelvis → foot IK ×2 → C2L.
- **Open:** looking down through the legs on back dives. The lift seemed
  enough; a camera pitch clamp for back dives was proposed but not built.
  The wind-up still shows the dash's empty-handed arms with long guns.

**Capsules (2026-10-13, user: "will work for now"):**
- **Main capsule:** `ShrinkCapsule` at `TakeOff` brings it to
  `DiveCapsuleHalfHeight` (35).
  - The bottom stays put: actor down by the difference, mesh relative +Z by
    the same. The camera is re-derived from the capsule size every frame.
  - `RestoreCapsule` runs on `RequestGetUp`: an `OverlapBlockingTestByChannel`
    with the full capsule. If blocked, the get-up (and a reload-to-stand
    press) is refused and the body stays down. `Finish` also tries it.
- **Body shape (queries only, no component):** `GetBodyShape` gives a capsule
  laid flat along `DiveYaw`, centred on the actor, resting on the main
  capsule's bottom (`BodyCapsuleRadius` 18, `BodyCapsuleHalfLength` 90).
  **2026-10-21:** shaped from the body each frame instead: laid along feet→head
  (flattened), spanning the furthest of feet, head, hands and the muzzle along
  that line + `BodyEndMargin` 10, so turned bodies and outstretched guns are
  covered. The fixed length is the fallback without bones. Reading bones on the game thread
  crashed ("index 71 from an array of size 0", as on 10-18): it now waits for the
  parallel evaluation first (`HandleExistingParallelEvaluationTask`) and checks
  the bone buffer isn't empty; `UpdateWeaponBlocked` does the same. **Rule: any
  game-thread read of bone/socket positions outside the anim instance waits first.**
  - The body never turns from the dive line, so it's one fixed shape until
    standing (user's call: no pose sampling, no turn checks).
  - `KeepBodyOutOfWalls`, while `IsBodyDown()`:
    - sweeps it 2 cm off the floor by this frame's horizontal move (or a
      hair, lying still);
    - skips floor-like hits (normal Z ≥ 0.7);
    - if it starts inside a wall, pushes the actor out along the normal by
      the depth, capped `BodyPushOutPerFrame` (10);
    - removes the velocity into the wall.
  - `IsBodyDown()` / `GetBodyShape()` are public and Blueprint-callable, for
    explosions, melee and AI to query later.
- **Crash, two lessons:**
  - **Never `AddTickPrerequisiteComponent` from the character movement to
    this component.** It reorders the frame so the landing's `SimulateLegs`
    (called inside the movement update) races the mesh's worker-thread anim
    evaluation. Result: an engine-only crash, "Array index out of bounds: 71
    from an array of size 0", every landing. The wall trim takes effect one
    frame late instead.
  - The first body capsule was also a runtime-created `UCapsuleComponent` with
    overlap events, moved per frame. It was rolled back too, so queries only
    from here on.

**Ledges (2026-10-13, user: "falling works"):**
- `FallOffEdge` runs if the movement is falling during Land or Prone:
  - restores the walking braking first, so the next landing saves the real
    values (otherwise `Finish` would restore the slide's 800/friction 0 and
    leave movement slippery);
  - sets the air braking to `DiveAirBraking` (the slide's speed carries on);
  - gravity stays normal;
  - eases off the landing physics legs;
  - sets Phase = Loop.
- `NotifyLanded` (airborne = Start/Loop) then runs a full second landing.
- **AnimBP (user):** Land → Loop and Prone → Loop transitions in the
  Shootdodge state machine, rule `ShootdodgePhase == Loop`.

**Aim pitch clamp (2026-10-13, user request, Max Payne style):**
- The poses follow the aim up and down only within `ShootdodgeAimPitchMin` /
  `ShootdodgeAimPitchMax` (−35° / +45° from level).
- `ClampElevation` applies to the wanted direction for the right gun, the
  left gun and the head, and `ShootdodgeAimPitch` (the prone blend space's Y)
  is clamped too.
- Shots are unaffected: `FireEquippedWeapon` fires from the muzzle to the
  crosshair's aim point.
- This likely covers "looking down through the legs" on back dives as well.

**Follow-ups (2026-10-13, user-tuned, "works"):**
- **Pitch limits split:**
  - pistols/duals: `ShootdodgeAimPitchMin/Max` (user: −15/45);
  - long guns: `LongGunAimPitchMin/Max`;
  - picked by `AimPitchMin()/AimPitchMax()` on `bIsPistolHold`.
  - Tune on the ABP's Class Defaults: Preview-window edits aren't saved.
- **Back-pose lift, extended:**
  - Long guns use their own `LongGunBackLiftAngle`. The left hand follows the
    grip through its IK after the lift.
  - The duals' left arm lifts `BackOffhandExtraLift` further, about its own
    gun (`ShootdodgeArmLiftL` / `ShootdodgeHandCounterLiftL`, on the
    `upperarm_l`/`hand_l` lift nodes). Its one-handed hold sat lower and
    clipped the legs.

**Next:** the shootdodge list is done. Open extra: the long-gun wind-up
showing empty-handed dash arms.

#### Refinements (2026-10-17)

**Flight limbs on physics:** the legs (`thigh_l/r` and below) go on
physics from take-off to landing, using the landing legs' `SimulateLegs`
machinery. Settings are under *Shootdodge|Flight Legs*.
- **Firm, then loose:** `FlightLegStartHoldStrength` 6000 at take-off eases
  to `FlightLegHoldStrength` 800 over the Start phase
  (`ABopisCharacterBase::SetLegHoldStrength`, re-applied each tick). The firm
  start stops legs caught mid-stride from flopping into a split. The user:
  "there are some positions in the walk anim where if I trigger the
  shootdodge, he flops with the leg split".
- **Landing:** the legs firm up to `LandingLegHoldStrength`. `FallOffEdge`
  goes back to the flight strength.
- **One-handed pistol, left arm (`bFlightLeftArmPhysics`):** `upperarm_l` and
  below join the legs, easing from `FlightArmStartHoldStrength` 3000 to
  `FlightArmHoldStrength` 150. The motors pull toward the clip's two-handed
  clasp, so the flight strength stays low. `FreesLeftArm()` checks for
  `PistolOneHanded`.
- **Base-class plumbing:**
  - `SimulateLegs(Hold, bWithLeftArm, ArmHold)` keeps the limb roots in
    `SimulatedLimbs`, and the fade and stop loop over them
    (`StartLimb`/`StopLimb`).
  - `EndHitReactions` resets everything below `spine_01`, so it puts a loose
    dive arm straight back on.
- **Tried and dropped (don't retry):**
  - **Hips on physics:** the pelvis is the root body, so the torso has to be
    handed back to the animation, and the waist seams. User: "I dont think we
    can do that".
  - **Late start at the clip's push-off frame**, for back dives: the physics
    came on mid-swing and the legs twitched. The user opened the legs in the
    back-dive Start clip (`anim_Dodge_Start_Bwd_P`) instead. The firm motors
    follow the authored opening.

**The Start state runs on a Blend Space Evaluator:** a Blend Space Player
reads its `StartPosition` only when the state initializes, and at that
moment it still has the value from its last update.
- **The bug this caused:** every dive started from the previous dive's start
  point, and the first from the `NativeInitializeAnimation` seed. Before
  back dives got their own offset, every dive used the same one, so it never
  showed. Found with a temporary per-frame log (since removed).
- **The fix:** `BS_Dodge_Start` is now an evaluator in the Start state. Its X
  comes from `ShootdodgeDirection`; its **Normalized Time** comes from
  `ShootdodgeStartTime` (`UShootdodgeComponent::GetStartNormalizedTime()`:
  from `PhaseStartPosition` to 1 over the Start phase, then held at 1).
  Teleport To Normalized Time is on, so skipped frames fire no notifies.
  **Loop is off**, or the held 1.0 wraps to frame 0 during the blend into the
  Loop.
- **Land still uses a player**, reading `ShootdodgeStartPosition`, so the seed
  (`GetRestStartPosition`) stays for it.

**Back dives play their push-off:** `BackStartOffset` (Backward and its
diagonals, from any stance) replaces `StartOffset`/`StartClipOffset` for
those dives. The user set it to **0**: the whole crouch and push-off. Before,
the 0.4 s default cut the jump and he seemed to float off the ground.

**Jog dives jump forward, then spin:**
- **From a jog** (gun lowered, `bFromJog` at the press), with the body facing
  within `JogForwardStartMaxAngle` 90° of the dive, the Start is the
  **forward** clip. It plays at the forward offset, along the run.
- **The hold:** for `ForwardJumpHoldTime` 0.1 s, the body keeps its facing
  (`IsHoldingForwardJump`, which skips the face-aim turn) and the blend spaces
  get 0°.
- **After the hold:** the body turns to the aim, and `ShootdodgeDirection`
  eases from 0° to the live direction at the anim instance's
  `ShootdodgeDirectionCatchUpRate` 720°/s. Only after a forward jump
  (`EasesAnimDirection`); every other dive follows the live direction
  outright, as before.
- **A jog reversal** (facing more than 90° off) gets the real direction's
  Start.
- **Tried and dropped:**
  - turn-to-run before strafe back dives, then with a jog delay;
  - a back-dive wind-up from the strafe stance;
  - an inertialized locomotion→dive blend (B; it broke nothing, but wasn't
    needed);
  - a two-evaluator crossfade in place of the direction ease. The user
    preferred the ease.

**Camera on capsule resizes:** the boom height is re-applied the moment the
capsule changes (`AProjectBopisCharacter::ApplyCameraHeight`, called from
`OnStartCrouch`/`OnEndCrouch` and from `ShrinkCapsule`/`RestoreCapsule`), as
well as each tick. Both resizes happen after the character's tick, so the
camera used to show one frame at the old height: a flicker going from a
crouch into a dive.

#### Original plan (pre-asset)

An asset exists: a **two-handed pistol shootdodge that lands prone, with a
prone turn-in-place**. That is the full Max Payne loop — dive directionally,
land, reacquire, keep firing, get up.

**Adapting it to other weapons.** The dive's lower body and spine are
weapon-agnostic; only the arms differ.
- **Dual pistols** — the same mirror rig as the standing pose. Build it once,
  it serves both.
- **Rifles** — the **left-hand IK backlog item** (Two Bone IK onto the weapon
  foregrip) does most of the work: weapon stays on `hand_r` and follows the
  dive, left hand IKs to the foregrip. No rifle dive needs authoring. It won't
  be perfect — a pistol dive extends the arms further than a rifle grip wants
  — but a dive is the most forgiving place in the game for an approximate
  pose: one second, moving camera, and under slow-motion the player is
  watching the spectacle, not the elbow.

**Keying:** `TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> DodgeMontages` on
the character — same shape and lookup as `FireMontages`/`ReloadMontages`.
Because those already use "only play if a montage was found", **an empty
Rifle entry means rifles simply don't dodge, with no special-case code.**
Worth considering as a deliberate choice rather than a fallback: it reinforces
*weapons dictate playstyle* (pistols move-and-gun, rifles stand-and-fight) and
is honest about where the animation looks good.

**Directional dodge only makes sense while aiming.** In the aim state yaw is
locked to the camera and the character strafes, so "left" is unambiguous and
maps onto the strafe input already driving movement. In free-run the character
orients to its own velocity, so direction has no stable meaning. Rule:
**directional while aiming, forward-only or disabled while free-running** —
which also halves what the animation set must cover.

Before planning further, check the asset for: **root motion** (interacts with
the rotation-mode toggling), and **whether the right arm crosses the body**
(the one failure mode of the mirror trick — mirrored frames can clip the
torso).

### Dodge roll and the moves around it (2026-10-14 / 15)

**The user's ask (2026-10-14):** "more moves for the player", starting with a
dodge roll. Choices: the **Roll** animation set, its **own key** (`IA_Roll`),
**evasive** (enemies' ×`EvadingHitMultiplier`), **no firing** during it,
**no Focus cost**. All compiled; the kneel, the quick aim turn and crouch turns
are not yet playtested.

**`URollComponent`** (`Gameplay/RollComponent.h/.cpp`, on the player):
- **`TryRoll`** (from `DoRoll`): on the ground, not rolling, off `Cooldown`
  0.25 s, not dead, not in a shootdodge. Crouch doesn't block it.
  - Direction: 8-way from the movement input relative to the camera
    (`PickDirection`, the shootdodge's `EShootdodgeDirection` octants; no
    input = forward).
  - **The body squares up to the camera first** (`SetActorRotation` to the
    control yaw): the clips are picked camera-relative but play
    body-relative. *(User: "its rolling relative to the character front
    direction".)*
  - Plays a random clip from `Animations[direction].Clips` as a dynamic
    montage on **`DeathSlot`** (full body), `PlayRate` 1, blend 0.1 in / 0.2
    out. Root motion carries it; `SetAnimationDrivenRotation(true)` so
    turning the camera doesn't steer it.
- **`TickComponent`, in order:**
  1. **Roll Focus:** at `RollFocusStartAt` 0.3 of the clip, a free Focus
     (`BeginFreeFocus`, no cost) for `RollFocusDuration` **1 real second**
     (`FApp::GetDeltaTime`), once per roll; it runs its course even past the
     roll. *(User: "you cant shoot because you are in a roll, but you can line
     up shots".)* Skipped if the player's own Focus is on.
  2. **Kneel cut-in:** roll button still held at `CrouchOutAfter` 0.5 →
     `EndRoll`, `StartPostRollCrouch`, then `Montage_Stop(CrouchOutBlendTime
     0.15)` — in that order, so the roll blends out into a body that's already
     crouched (see the kneel).
  3. **Move-out:** movement input at `MoveOutAfter` 0.6 → `Montage_Stop
     (MoveOutBlendTime 0.15)`; with `bCarryMomentum` the velocity is set to
     full run speed the way the input points. *(User: "I need to be able to
     move immediately after the roll".)*
  4. **Played out:** ends as the blend-out starts.
- **`Cancel`** (death): stops the montage at once, ends the roll's Focus.
- **Guards** on the character while `IsRolling()`: fire, jump, weapon select,
  reload, crouch update, shootdodge. `DoRoll` itself clears a kneel and
  uncrouches first.

**Evasion linger** (`EvadeLingerTime` 2 s, `Combat|Evasion`):
`IsEvading()` = `IsEvadingNow()` (the dive's flight or a roll) **or** within
2 s of the last evading frame (`LastEvadingTime`, stamped in Tick). So a
landed dive and a finished roll stay evasive for 2 s. *(User: "Give a
timewindow where the effect of the accuracy reduction is maintained".)*

**The kneel — Vanquish's roll into a crouch** (character, `Combat|Roll`):
- **Trigger:** hold the roll button through the roll. At the roll's
  `CrouchOutAfter`, `URollComponent` cuts into the kneel. *(First built as
  "fire held as the roll ends, kneel for 2 s"; the user moved it to the roll
  button and a cut-in point the same session.)*
- **On/off:** `bPostRollCrouch`. The cut-in checks `CanPostRollCrouch()`
  (`bPostRollCrouch` and alive), so with it off a held roll plays out
  normally instead of being cut short (2026-10-15).
- **`StartPostRollCrouch`:** with `bPostRollCrouch`, sets
  `bPostRollCrouching` and calls `Crouch()` **at once** — waiting for the next
  `UpdateCrouch` let the roll blend into the standing pose first (the "stands
  up, then crouches" hitch).
- **Lasts while the roll button is held** — no timer (`PostRollCrouchTime`
  was removed). `UpdateCrouch` drops it the frame the button is up, and the
  normal crouch rule takes over (standing, unless crouch was toggled).
- **`bPostRollCrouchHoldsPosition`:** `DoMove` ignores input while knelt.
- **`IsRollHeld()`** / private **`IsInputHeld(Action)`**: the live Enhanced
  Input value (`UEnhancedInputLocalPlayerSubsystem::GetPlayerInput()->
  GetActionValue`), not the last event.
- **Camping heat:** *(revised 2026-10-17)* the clock no longer pauses for the
  kneel. It waits only **while evading** (`IsEvading()`: a dive or roll and
  its `EvadeLingerTime` linger), then runs as normal — knelt, crouched or
  standing. User: "After the linger, regardless if you are crouched or not.
  Build up camp as per the setting." (Before, a kneel never built heat, so it
  was never punished.) The user set `CampGraceTime` **1** and
  `CampTimeToFullHeat` **2** on `BP_PlayerCharacter`: 100% 3 s after stopping,
  5 s after a roll ends.
- **Evasion:** only the 2 s linger from the roll's end.
- **Blend tuning (no code):** `CrouchOutAfter` on the roll frame closest to a
  kneel; `CrouchOutBlendTime` ~0.2–0.3; the AnimBP's stand→crouch transition.

**Crouch combat stance** (2026-10-15, `bCrouchCombatStance`, category
*Crouch*, on by default): crouched (the kneel included), Tick keeps
`TimeUntilWeaponLowered` at `LowerWeaponDelay`, so the weapon stays raised —
the same Aiming stance as the aim button (body locked to the camera, feet
turning in place), with the hip-fire pose and no aim zoom. The camera eases
down by **`CrouchCameraOffset` −40 cm** (was 0; only applied in the stance).
Standing up, the gun lowers after `LowerWeaponDelay` (C++ 1.5 s; the user set
**4 s** on `BP_PlayerCharacter`, 2026-10-15, so the gun stays up through
corner peeks). Off: the old crouch.

**Reloading** (2026-10-14):
- **Auto-reload** (`bAutoReload`, `AutoReloadDelay` 0.2 s): an empty gun
  reloads by itself once the player is free to (standing or prone, not
  mid-dive or mid-roll, not equipping) — `UpdateAutoReload`, through
  `DoReload`.
- **Reloading ends Focus** (`bStopFocusOnReload`): a reload that actually
  starts calls `StopFocus`.
- **Prone reload:** lying prone after a dive, `DoReload` reloads on the floor
  instead of getting up; the rest of a dive (wind-up, flight, landing,
  get-up) refuses it.
- **AnimBP wiring (bridge):** `Slot_0` (DefaultSlot) → `SaveCachedPose`
  **"UpperBodySlot"**; `UseCachedPose_1` feeds the standing upper-body layer
  (`LayeredBoneBlend_0`) as before; a new **`LayeredBoneBlend_8`** (branch
  filters `clavicle_l` / `clavicle_r`, local space) after the shootdodge
  branch's `LayeredBoneBlend_7` lays `UseCachedPose_2` over it at
  **`ProneReloadAlpha`** (the anim instance eases it 0↔1 at
  `ProneReloadBlendSpeed` 6 on `bReloadAnimating`). Output →
  `LocalToComponentSpace_3`.
  - A second `DefaultSlot` node (the first attempt) warned about duplicate
    slots and made dive fire montages show the two-handed pose; the cached
    pose replaced it.
- **No torso bend during a prone reload:** the shootdodge aim correction lets
  go while `bReloadAnimating` (it was bending the torso to point a gun that's
  down by the chest at the crosshair).
- **A held trigger doesn't break into a reload** (2026-10-15; see *Combat →
  Firing*).

**Dual shootdodge arm spread** (2026-10-15): "the shootdodge duals are mostly
blocked by the players head or body". Both guns aim at one point, so from
behind the right shoulder they converge in front of the head and chest.
- Each arm swings out to its own side of the screen by
  **`DualDiveSpreadAngle`** 20° (anim instance Class Defaults, `Shootdodge`),
  about the **camera's up** axis in component space, eased by
  `ShootdodgeDualAlpha`; the hand turns back by the same, so the gun keeps
  pointing where it did.
- Folded into the existing lift rotators: `LiftFor` composes `Spread × Lift`
  for the arm and its inverse for the hand. No AnimGraph change. Single guns
  get the identity.

**Shootdodge state machine — Inertialization (2026-10-15):** a sporadic
`No Inertialization node found for request from transition 'Land' to 'Loop'
in state machine 'Shootdodge'`. All six Shootdodge transitions are Standard
Blend (0.2 s); the machine raises the request itself, most likely on a
Land → Loop re-entry while the Loop → Land crossfade is still running (a bump
on landing). The only Inertialization node was on the locomotion branch. Fix
(bridge): **`StateMachine_0` → `Inertialization_1` → `LayeredBoneBlend_6`**.

**Tried and reverted (2026-10-15):**
- **A slide into the kneel** (`CrouchSlideTime`: the roll's speed easing to a
  stop by the foot plant). The user preferred to fix the blend instead.
- **An inertial roll-to-kneel blend** (`Montage_StopWithBlendSettings` with
  `EMontageBlendMode::Inertialization` + an Inertialization node after
  `DeathSlot`). Reverted, node removed.
- **Held roll Focus** (Focus on the meter while the roll button stayed held
  after the roll). Removed entirely.
- **Roll hold → prone slide** (the user's first idea): dropped; holding roll
  now goes into the kneel.


**Weapon pickup mid-roll (2026-10-17):** rolling over a gun (or switching
slots mid-roll) no longer cuts the roll with the equip montage. The montage
shares the roll's slot group. Instead, `PlayEquipAnimation` returns early
while `ShouldSkipEquipAnimation()` is true (virtual; the player returns
`IsRolling()`). The gun is in the hand at once, and `IsEquipAnimating()`
stays false. The user: "just switch the weapon instantly… maintain the
roll".

### Prone as a transient state

The dive lands prone, but this does **not** reverse the no-prone decision of
2026-09-25. Two different things:

- **Prone as a stance** — ruled out. Needs standing→prone transitions,
  crawling, prone locomotion, getting up from arbitrary states.
- **Prone as a post-dive state** — what the asset gives. Entered only by
  diving, exited by getting up. No crawl, no prone-walk, no manual entry. A
  fraction of the cost, and the animations came with the pack.

Stance model: **standing, crouched (toggle — stationary only since 2026-10-05,
see *Crouch*), prone (transient, dive-only).**

Landing prone is also what makes the dive *cost* something. A dive that only
evades is free; one that puts you on the floor for a second is a trade. That
comes from the animation set rather than needing to be designed in.

**The rotation gotcha.** In the aim state `bUseControllerRotationYaw` snaps
capsule yaw to the camera instantly, while a prone turn-in-place animates a
slow rotation. Run both and the capsule spins while the body lags, firing
where the body isn't pointing. **Prone must hand rotation authority to the
animation** — disable controller yaw for the duration and let root motion or
the montage drive it.

Consequence for the TPS work: the `ApplyMovementMode` helper in
[ProjectPlan.md](ProjectPlan.md) Phase 4.5 is **three states, not two** —
non-aim, aim, and prone-with-animation-authority. Cheaper to write that way
than to retrofit.

Smaller ones: the crouch half-height is almost certainly fine as the prone
capsule for a two-second transient (don't build a second capsule config unless
it visibly floats), and the spring arm will need its own length/offset near
the floor or the camera looks at concrete.

### Focus (slow motion) — built 2026-10-09
**Name:** "Focus", **not "bullet time"** — that name is trademarked (Max
Payne). Renamed the same day: code, assets and docs. Older entries in this file
and the ProgressLog still say "bullet time".

**Design (user):**
- toggle on **Q**;
- the world runs at **0.3×** and the **player is slowed with it** (Max Payne),
  but **aiming stays normal**;
- a **meter**: refill on kills, an optional passive-regen switch, an infinite
  switch;
- default feedback: HUD meter, screen effect, audio;
- the shootdodge comes later, as a separate feature.

**`UFocusComponent`** (`Source/ProjectBopis/Gameplay/FocusComponent`), created
on the character as `Focus`:
- **Toggling:**
  - `Toggle()` → `StartFocus()` / `StopFocus()`, `IsFocusActive()` (not
    `Activate` / `Deactivate` / `IsActive` — `UActorComponent` already has
    those).
  - It refuses to start below `MinMeterToActivate` (10), to stop flicker.
  - It switches off by itself when the meter empties.
  - `EndPlay` restores normal time.
- **Slowing:** `UGameplayStatics::SetGlobalTimeDilation(WorldTimeDilation)`. The
  player isn't compensated. Mouse look stays responsive because it's applied
  per input event, not per second.
- **Meter (real seconds):** `RealDelta = DeltaTime / GlobalTimeDilation`.
  - `MaxMeter` 100, `DrainPerSecond` 15 (≈6.7 s).
  - `bPassiveRegen` (**on** until enemies exist) at `PassiveRegenPerSecond` 5.
  - `bInfinite`.
  - `AddMeter(Amount)` / `KillRefill` 20 — Phase 5 calls it on kills.
- **Input:** `IA_Focus` (a copy of `IA_Reload`) on **Q** in `IMC_Default`,
  bound by the character's `FocusAction` → `DoToggleFocus`.
- **HUD:** `UFocusWidget` (`GetMeterFraction`, `IsFocusActive`); the user's
  `WBP_Focus` progress bar sits in `WBP_PlayerHUD`.
- **Health bar (placeholder, 2026-10-14, user-confirmed):** `UHealthWidget`
  (`UI/HealthWidget.h/.cpp`, a `UPlayerHUDElementWidget`) exposes
  `GetHealthFraction()` (health ÷ max from the player's
  `UHealthComponent`; 0 with no character).
  - The user's `WBP_Health` has a red Progress Bar whose Percent is
    *bound* to it, which polls every frame. That's fine for a placeholder;
    the real HUD should update on change.
  - It sits in `WBP_PlayerHUD`.
- **Feedback:**
  - **Screen:** `FocusPostProcess`, an unbound `UPostProcessComponent` on the
    character. Defaults: saturation 0.5, vignette 0.8, scene fringe 1.5;
    tweak them on the Blueprint. Its `BlendWeight` is faded 0↔1 in **real**
    time over `FeedbackFadeTime` (0.25 s). `UFocusComponent` finds it with
    `FindComponentByClass`.
  - **Audio:** `SetGlobalPitchModulation(FocusPitch 0.6)` over the same fade,
    restored on stop and in `EndPlay`.
  - **Optional sounds** (empty — no assets yet): `EnterSound`, `ExitSound`,
    `LoopSound` (a 2D loop, faded out on stop).
- **Rename hygiene:** `[CoreRedirects]` in `DefaultEngine.ini` maps the old
  class, function and input-property names. **Don't** redirect a renamed
  *component* member onto its old subobject. Doing that made
  `BP_PlayerCharacter` keep the old `BulletTime` subobjects beside the new
  ones; the fix was reverting that Blueprint to before the feature and
  re-setting `FocusAction`.
- **What slows with it:** everything on game time — fire rate, reloads, the
  equip animation, the weapon lowering, camera blends.
- **Bullets** become visible automatically: `AProjectileBase` shows all its
  visuals below 0.9 dilation. `bKeepEffectsVisible` now defaults to **off**, so
  tracers hide too. A temporary `[BulletVis]` log confirmed every round is
  fully hidden at spawn at 1.0 dilation.
- **The user's rounds:** `BP_Cal45Bullet_Projectile` (a bullet model with a
  tracer) and `BP_RifleRound_Projectile` (faster). Both are hidden in real time
  and visible in Focus.

**Superseded:** the earlier plan to keep the player near normal speed with
`CustomTimeDilation`. The user chose a slowed player. A partial player speed-up
would be one line (`CustomTimeDilation` on the character) if ever wanted.

---

## Levels

Mostly a level-design job, but it puts one constraint on the code: the system
deciding where enemies spawn and when waves trigger **can't assume anything
about a room's layout** — no hardcoded "sniper lane" or "flank route" —
because the whole point is that the same room supports different playstyles.

Spawn points and encounter pacing should be data placed by hand using a shared
tool, not assumptions baked into game code.

---

## Narrative

The protagonist is now an **authored character** (2026-09-13). The previous
"no dialogue choices, no conversation system" rule was derived from the
neutral protagonist and is no longer settled either way — it's a design
question. Until it's decided: no conversation system gets built, and nothing
in the code should assume one won't exist. The story itself is the current
major design task and is not an engineering input yet.

---

## Architecture principles

### Animation feedback data belongs to the animator, not the weapon

Established 2026-08-18. The first pass put `FireMontage` directly on
`WeaponBase`. That broke under a simple test: an `UAnimMontage` is authored
against one specific skeleton, so a single montage property on the weapon
could only ever be correct for one skeleton — wrong the moment the same weapon
is fired by a different one (a future AI enemy).

The rule: a weapon may state its own *identity* (`AnimType`), but never
*what* the holder plays. (Until 2026-10-26 it could also say *whether* it
wanted animation-driven feedback; that switch is gone.) Each
animator — the player character now, each enemy archetype later — owns its own
skeleton-appropriate lookup.

Applied as: `EWeaponAnimType` on the weapon; `FireMontages`,
`OffhandFireMontages`, `AimFireMontages`, `AimOffhandFireMontages`,
`ReloadMontages` and `OffhandReloadMontages` maps keyed by that enum on the
character.

**Exception that proves the rule:** `FireAnimation` (the weapon's *own* mesh
animation — slide racking, bolt cycling) lives on the weapon, because it's
authored against the weapon's own skeleton. Weapon-skeleton data is the
weapon's; holder-skeleton data is the holder's.

### Render-affecting properties need their setters

Any `UPROPERTY` that affects how something renders should be set through its
paired setter, not assigned directly — the setter is what invalidates render
state. Learned from a bug where the equipped pistol rendered in the wrong
place, but only sometimes: correct on a fresh editor start, wrong after a
Stop→Play in the same session, different again between first-person and
external views. The transform data was correct the whole time;
`FirstPersonPrimitiveType` had been assigned directly instead of through
`SetFirstPersonPrimitiveType()`, leaving a stale render proxy.

This matters most at runtime; construction-time assignment is harmless, since
there's no proxy yet.

### First-person projection is a separate rendering path — *historical*

> **No longer applies (third person since 2026-09-30).** `FirstPersonMesh`,
> `FirstPersonPrimitiveType` tagging and the first-person FOV/scale are gone;
> every mesh renders through the normal projection. Kept because it explains
> several earlier bugs and decisions in the progress log.

Anything tagged `FirstPersonPrimitiveType::FirstPerson` renders through a
different projection (`FirstPersonFieldOfView`, `FirstPersonScale`) from
normal world-space primitives. Consequences:

- A world-space effect attached to a first-person mesh draws in the wrong
  place. Spawned muzzle flashes need
  `SetFirstPersonPrimitiveType(FirstPerson)` too.
- The gun's *apparent* on-screen position is not its true world transform, so
  reasoning about where the muzzle "looks" is unreliable.
- Zoom narrows the main `FieldOfView` only. `FirstPersonFieldOfView` is
  separate, which is why the arms don't magnify — and why scoped zoom hides
  them Halo-style instead.

---

## Character rig (third person, 2026-09-30 →)

- **One mesh.** `ACharacter::GetMesh()` — the full-body mannequin — is the only
  character mesh, visible to everyone including its owner. Animation:
  `ABP_Player` (parent class `UProjectBopisAnimInstance`; see *Animation
  architecture*), Lyra's library on the same skeleton.
- **Camera.** `CameraBoom` (`USpringArmComponent`) on the capsule owns control
  rotation (`bUsePawnControlRotation`) and wall collision; `FollowCamera` rides
  its end. `UpdateCameraTransition` pulls arm length, socket offset and FOV
  toward hip or aim values every frame (`HipArmLength`/`AimArmLength`,
  `HipSocketOffset`/`AimSocketOffset`, `CameraTransitionSpeed`; zoom FOV only
  for weapons with `HasZoom`), and sets the boom height from the capsule so
  crouching doesn't move the camera (see *Crouch*). Pitch limits −70/+80 in
  `AProjectBopisCameraManager`.
- **Rotation.** Stance-driven (`ApplyMovementStance`): free-run faces travel,
  aiming or a recent hip-fire faces the camera and strafes. Turn-in-place hides
  the capsule snapping when standing still.
- **Weapons.** Attached to `GetMesh()` at `WeaponAttachSocketName` (`hand_r`);
  dual-wield off-hand at `OffhandAttachSocketName` (`hand_l`).
  `GripLocationOffset`/`GripRotationOffset` are per-weapon corrections on
  equip, **in socket space** (hand-bone axes, so X/Y/Z are not
  forward/right/up); re-tuned for the body mesh 2026-10-03.
- **Shots** come from the camera trace and leave from the muzzle — see *Trace
  source — two-stage*.

### Historical: the first-person rig (2026-08-30 → 2026-09-30)

The camera and arms attach the opposite way round from the FPS template: the
camera hangs off the capsule, and `FirstPersonMesh` hangs off the *camera*, so
the arms rigidly follow where you're looking rather than needing skeletal
aim-offset blending to fake it.

`FirstPersonMesh` is a **full body** mesh positioned under the camera (feet at
ground level), so it supplies both arms and the legs you see looking down.
`GetMesh()` stays `SetOwnerNoSee(true)` — it's the world-space representation
for other viewers and shadows only. `HiddenFirstPersonBones` trims what the
camera physically sits inside (default: `head`).

`GripLocationOffset`/`GripRotationOffset` are per-weapon corrections applied on
equip, so a weapon whose mesh pivot doesn't line up with the hand socket can be
nudged from data. **Both are in socket space** — relative to `HandGrip_R`,
whose axes come from the hand bone — so X/Y/Z are not forward/right/up.

---

## Current state

See [ProgressLog.md](ProgressLog.md) for dated detail and
[ProjectPlan.md](ProjectPlan.md) for the phase breakdown.

**Update 2026-10-15:** Phase 5 has enemies that take bullets, die, shoot
(the hit-chance model, attack tokens) and fight in waves (gunman behaviour v1,
`AEncounterDirector`). The player has the shootdodge, Focus, death, a dodge
roll with a held-button kneel, auto/prone reload, crouched turn-in-place, and
the Max Payne shooting model (hold to fire, small per-weapon spread). Ammo HUD
and pickups were done 2026-10-08. The summary below is kept as of 2026-10-05.

Summary as of 2026-10-05:

- **Phases 0–3 complete**: project cleanup, weapon foundation, bloom accuracy,
  reticle/aim/zoom.
- **Phase 4 (weapon content & feel)** nearly complete: fire feedback, hit
  decals, projectile system, weapons configured (plus shotgun and dual
  pistols, 2026-10-03/04), fire-rate cap, full-auto, per-weapon animation,
  scoped zoom, ammo phases A–B. Outstanding: ammo HUD and pickups.
- **Phase 4.5 (third-person conversion) complete** 2026-10-05: spring-arm
  camera, stance-based movement, two-stage firing, hip-fire raise/lower, Lyra
  animation with strafing, aim offsets, left-hand IK, turn-in-place, dual
  pistols, stationary crouch, anim logic in C++. Optional polish left: shotgun
  per-round reload loop, 180°/crouched turns.
- **Phase 5 (enemies)** not started. This is when the damage code — dispatching
  correctly but inert since Phase 1, because nothing has `Health` or overrides
  `TakeDamage` — finally does something. Enemies will be human, per the
  setting change.
- **Setting changed 2026-09-13** — see the implications section at the top.
  No code changed as a result; the weapon art is now placeholder.

### Vendor content

Marketplace packs live in their own top-level folders, **untouched**:
`MilitaryWeapSilver` (weapons — conventional firearms, replaced
`SciFiWeapDark` on 2026-09-21), `CleanFlatIcons` (reticle art), `UWC_Bullet_Holes`
(decals), `ImpactsVFXVol1` (Niagara per-surface impacts, in use since 2026-10-09 — see *Impact effects*),
and the migrated Lyra animation library under `Content/Characters/Heroes/`.

Moving or renaming assets inside a pack breaks its internal cross-references —
treat them as read-only and reference them from our own Blueprints and data.

---

## Build tooling

**`Tools/RebuildEditor.bat`** (wrapper for `RebuildEditor.ps1`, 2026-10-06):
closes the editor that has `ProjectBopis.uproject` open (gracefully — save
prompts still appear; waits for exit), builds `ProjectBopisEditor Win64
Development` through UnrealBuildTool (the same build VS runs; picks up new
files without regenerating project files), and reopens the editor only if the
build succeeded. Flags: `-Clean` (full rebuild), `-NoLaunch`, `-Force` (kill
after `-TimeoutSeconds`, default 300). Engine path hard-coded to
`C:\Program Files\Epic Games\UE_5.8`. Kept pure ASCII — Windows PowerShell 5.1
misreads BOM-less UTF-8 (an em dash decodes into a curly quote that breaks
string parsing). Visual Studio still needs *Generate Visual Studio project
files* to *show* new source files.

## Engineering gotchas

The ones most likely to bite first; the **full list** with reproduction detail
follows below (moved here from ProjectPlan.md on 2026-10-24 — add new ones there).

- **A Blend Space (or Sequence) Player reads its `StartPosition` only when
  its state initializes, and with the value from its last update.** So a
  start point that changes per use lags one use behind, and the first use
  gets whatever was there at graph start. Drive the time every frame with an
  evaluator instead: the shootdodge Start, 2026-10-17.
- **Capsule resizes after the character's tick show one camera frame at the
  old height:** crouch (applied in the movement component) and the dive's
  capsule shrink. Re-apply anything derived from the capsule at the moment
  it changes (`ApplyCameraHeight`).
- **The Unreal MCP bridge can't create nodes inside an AnimBP state's graph**
  ("Cannot cast type 'AnimStateNode' to 'Blueprint'"). Reading, deleting,
  pin values and wiring there all work. New nodes inside a state are the
  user's to place.
- **"Array index out of bounds: 71/72 from an array of size 0" crashes:**
  the mesh's physics was changed while its animation was being evaluated on a
  worker thread. The changes in question: collision (QueryOnly ↔
  QueryAndPhysics can rebuild the bodies), simulate, blend weight, motors.
  Seen 2026-10-17 at 21:16 and 00:07, after the free arm and the
  limb-physics work added more such changes.
  - Every function that changes the mesh's physics now calls
    `ABopisCharacterBase::WaitForAnimEvaluation()` first
    (`HandleExistingParallelEvaluationTask(true, true)`). That's the limbs,
    the free arm, the left-arm switch, and hit reactions and staggers.
  - Keep doing that for anything new. Not proven fixed (sporadic, no call
    stack); watch `Saved/Crashes`.
- **Physics switched on mid-motion twitches.** The bodies start with none of
  the animation's speed, lag, then snap back. Start limb physics while the
  limb is still, or blend its weight in.

- **Bridge edits to a Blueprint's defaults don't reach instances already
  placed in the open level** (2026-10-09). The BP editor propagates; a direct
  CDO write doesn't. Saving the level then bakes the stale value into the
  instance as an override. Symptom: `DeathAnimations` empty on `Enemy_Test`
  even though `BP_EnemyBase` had them. Fix: reset-to-default on the instance,
  or re-place it. **This also hits child Blueprints:** setting a new value on
  `BP_EnemyBase` and compiling did *not* update `BP_Enemy_Test`'s defaults
  (2026-10-10). After a bridge CDO write, set the child BPs and every placed
  instance too, and check them.
- **`GetLastRenderTimeOnScreen()` is not a visibility test in UE5.** Lumen and
  other off-screen passes keep it current for meshes behind the camera. Use a
  camera-cone check plus a line trace. It was found because the editor log
  file stopped flushing mid-session: the bridge Logs toolset reads the live
  log instead.
- **The engine's `Ragdoll` collision profile ignores `Visibility`.** Hitscan
  and the camera aim trace pass through ragdolls (the aim converged on the
  wall behind). Re-block it after switching profiles (`UseRagdollCollision`).
- **`AddImpulse` on a kinematic bone** logs "has to have Simulate Physics
  enabled" and does nothing. With a partial simulation, check
  `GetBodyInstance(Bone)->IsInstanceSimulatingPhysics()` first.
- **Live Coding cannot handle structural changes.** New/renamed
  `UPROPERTY`/`UFUNCTION`, changed member types, or changed constructor
  attachment hierarchy all need a full editor close + Rebuild Solution. Live
  Coding reports success and then re-instances the class, producing failures
  the diff doesn't explain. Check the Output Log for `Re-instancing` before
  forming any other hypothesis.
- **A CDO read-back is not proof.** Setting a Blueprint default through the
  editor bridge and reading it back succeeds even when the value never reaches
  spawned instances. Set → compile *that* Blueprint → save → verify against a
  live PIE instance.
- **`FHitResult::Location` vs `ImpactPoint`.** For a swept shape, `Location` is
  the shape's centre at impact — one radius off the surface. Use `ImpactPoint`
  for anything placed *on* a surface (decals, impact FX).
- **IntelliSense false-positives on delegate macros** (`AddDynamic`). Trust the
  actual build over the editor squiggle.
- **A new Transform (Modify) Bone exposes Translation/Rotation/Scale as pins,
  and pin defaults override the node's own settings at compile** (2026-10-07).
  Writing `Node.rotation` did nothing — every recoil node applied (0,0,0), and
  the compile then copied the zeros back into `Node`. Hide the pins
  (`ShowPinForProperties`) **before** setting values, or wire/set the pin
  itself. Applies to any anim node with optional pins.
- **An additive clip's base pose decides what it carries** (2026-10-07). A
  fire clip measured against its own frame adds pure kick to whatever pose is
  underneath. One measured against a *different* pose also carries "the
  difference from that pose", and pulls a re-authored idle back toward the
  original every shot. Check *Additive Settings → Base Pose* before layering a
  stock additive over a custom pose.
- **Lyra turn clips differ on root motion** (2026-10-15). The rifle standing
  turns have *Enable Root Motion* off; the pistol **crouch** turns ship with it
  **on**. As a turn-in-place montage that rotates the capsule against the
  Aiming stance → a constant re-stepping stutter. Check the flag on any new
  turn clip.
- **A Standard Blend state machine can still request inertialization**
  (2026-10-15). The Shootdodge machine logged "No Inertialization node found
  for request from transition 'Land' to 'Loop'" with every transition on
  Standard Blend — the request comes from the machine itself (likely a
  re-entry mid-crossfade). An Inertialization node must sit **downstream of
  that machine**; one on another branch doesn't count.
- **`grep` on a `.uasset` shows FName bases, not full names** (2026-10-15).
  `AM_Rifle_TurnLeft_90` appears as `AM_Rifle_TurnLeft` (the `_90` is stored
  as the FName number), and a name-table entry doesn't tell you a property's
  value. Confirm through the bridge or the asset's own folder listing.
- **The bridge can't create montages or set `SequenceLength`** (2026-10-15).
  Duplicate an existing montage (`AssetTools.duplicate`) and rewrite its
  `SlotAnimTracks` segment (`animReference`, `animEndTime`,
  `cachedPlayLength`); the montage's own length stays the source's.
- **`ObjectTools.set_properties` takes `values` as a JSON string**, and struct
  fields use the lower-camel names `get_properties` returns (`burstShotsMin`,
  `slotName`). An unreadable/unsettable property aborts the whole script.
- **The World Partition navmesh never saved — it reverted on every restart**
  (found 2026-10-16). `Lvl_Sandbox`'s `RecastNavMesh-Default` (Dynamic, not
  world-partitioned, not spatially loaded; external package
  `__ExternalActors__/ThirdPerson/Lvl_Sandbox/1/AE/8NXSYG2EA3YFUOAUSHUREF`)
  was last written 10-09. *Build Paths* rebuilt it in memory without dirtying
  that package, so *Save All* only ever wrote the bounds volume; every load
  brought back the 10-09 tiles, and neither the editor's auto-update (dirty
  areas only) nor Dynamic generation (PIE copies the editor navmesh) rebuilt
  the rest. **Fix:** `bForceRebuildOnLoad` on that actor — a full rebuild at
  every load, editor and game — then Save All (now dirty, it saved).
  `RuntimeGeneration=Dynamic` stays in `DefaultEngine.ini`. The bridge's
  `save_actor` / `save_assets` can't save external-actor packages ("Asset does
  not exist"); use the editor's Save All. The `Unable to find RecastNavMesh
  instance … UCrowdManager` warning only appears while a PIE world tears down.
- **An anim node reads values it uses at initialization from its last update, not
  this frame's** (2026-10-16). A blend space's Start Position (bound to a
  variable) is taken when the node initializes — before that frame's exposed
  inputs are copied — so a branch's first-ever activation sees whatever the
  variable held at the graph's own start. Seed such variables in
  `NativeInitializeAnimation` (the AnimBP initializes before actor
  components' `BeginPlay`). The first-dive bug was this.
- **A Blueprint that only lost a removed property's value isn't dirty**
  (2026-10-16). Compiling and `save_assets` skip it, so the package keeps its
  old imports (`get_referencers` still lists it). Make any property write to
  dirty it (e.g. set a value to itself), then save.
- **Stop an AI's StateTree before unpossessing** (2026-10-16). Unpossess
  stops the brain with the pawn already gone, so `UStateTreeComponent::
  StopLogic` fails its context requirements and warns on every death.
  `AEnemyBase::Die` now calls `GetBrainComponent()->StopLogic("Died")` first;
  the later stop returns early (`bIsRunning` false).
- **Renaming or removing a `UPROPERTY` drops the values Blueprints stored for
  it** (2026-10-15: `FireMode`, `IntendedTimeBetweenShots`, the bloom fields,
  the enemy burst fields, `FocusMaxBloomMultiplier` on `BP_PlayerCharacter`).
  Read them through the bridge first if they matter (or add a CoreRedirect).

---

### Full list (from ProjectPlan.md, 2026-10-24)

Newest first, as they were recorded.

- **Pixel Depth Offset moves where a pixel is lit, not only its depth test
  (2026-10-24).** Deferred lighting rebuilds each pixel's position from the
  depth buffer, so PDO on visible skin made it shadow itself (and subsurface
  scattering bleed orange) wherever the offset changed. Use PDO only where
  the surface ends up hidden (here: skin under worn clothing).
  *(2026-10-25: or use WPO along the camera ray instead, which moves the
  surface in the shadow pass too — what the skin does now.)*
- **CC's apparel masks are coarse (2026-10-25).** A handful of generic
  shapes (Top, TShirt, ExposedChest…) shared by many garments; a one-piece
  swimsuit uses an upper-body mask. Don't gate anything that must cover a
  garment exactly by them, and they're in the body's UV layout — meaningless
  on the head mesh.
- **An anim pose feeding two parents gets updated twice a frame (2026-10-23).** A player wired straight into two nodes advances twice per frame whenever both are relevant — the bladed legs ran at double speed. Route it through a Save Cached Pose and read it with one Use Cached Pose per parent.
- **Bridge limits in AnimBPs/materials (2026-10-23):** it can't create nodes inside a state graph ("Cannot cast AnimStateNode to Blueprint"); its node list doesn't offer a Use Cached Pose for a cache made in the same session; and `MaterialTools` can't connect or read `MP_PixelDepthOffset` (enum conversion error) — go through Material Attributes, use a view-ray WPO, or have the user make the wire. `PreSkinnedPosition` is vertex-only: pass it through a VertexInterpolator for pixel outputs.
- **A Blueprint default set through the bridge doesn't reach actors already placed in the level, nor child Blueprints (2026-10-23).** Placed instances carry their own copy; they pick up the new default only when the level reloads (spawned actors get it at once). A PIE test on placed actors right after a bridge CDO edit tests the *old* value — the "CC ragdoll looks better" false positive. **Child Blueprints' defaults (`BP_Player_CC`, `BP_Enemy_CC`, `_Thug`, `_Goon`) also keep the old parent value until they reload** — no footsteps after setting `FootstepEffects` on the two base Blueprints only. Set the leaf Blueprints too, or restart; this is probably also the sound-slot case below.
- **An object reference set on a Blueprint default through the bridge doesn't reach PIE-spawned instances until the editor restarts (2026-10-23, verified).** The CDO reads as set and the package saves correctly, but a PIE instance reads `None` — seen with the weapon sound slots (silent reloads) and `WeaponWheelAction` (probed in PIE: CDO set, instance None; a sibling set in the editor was fine). Scalars/structs set the same way (ragdoll asset, footstep data on the CC children) did arrive. **After any bridge edit of an object-reference default, restart before judging a PIE test.**
- **A C++ property on a widget class must not share a name with a designer widget in its Blueprint (2026-10-24).** The Blueprint generates a variable per widget marked *Is Variable*; if the parent already has a property of that name (one not meant for `BindWidget`), compile fails with "has a generated variable for the widget [X] but we failed to find a property for it". Seen with the wheel's `NameText`/`AmmoText` members; renamed `…TextBlock`. Either name members differently or make them real `meta = (BindWidget)` / `BindWidgetOptional` slots.
- **Adding bones to a CC body: by hand, Merge only (2026-10-24).** Copy/paste of the `ik_` bones from `CCMH_Body_Male` in the Skeleton Editing tool produced a misnamed bone (`ik_handgun_r` as `ik_hand_r`'s parent, log: "Hierarchy does not match") and the merge failed ("Skeleton can't be modified"); **Merge All** then re-merges *every* mesh on the skeleton and failed on the male. Nothing reached disk; fixed by restarting without saving, `git restore` of the female mesh, and adding the seven bones by hand with the skeleton's exact names/parents, then **Merge** (Merge All off).
- **Bridge graph DSL: name the target, load soft refs (2026-10-24).** `(Class|CCPresetDataAsset|GetBody preset)` read back as `Class|WeaponDrop|GetBody` (the reader labels a getter by the first class with that property name; the node itself worked — verified by building a female). Pass the object as `:self` anyway, and wrap a soft reference in `Utilities|LoadAssetBlocking` before using it — the writer inserts `ResolveSoftReference`, which returns nothing for an unloaded asset.
- **CC apparel: male and female MIs share names (2026-10-24).** Set MI parameters by full path, never by name; and female garments use male MIs (the female blazer's inner shirt is the male `MI_Shirt_01`), so a pass over one gender can overwrite the other's values — check shared paths afterwards.
- **GitKraken + an untracked `.gitattributes` with LFS rules (2026-10-22)** froze it and staged every asset as an LFS pointer. Fix: delete `.gitattributes`, `git reset` (unstage). Adopt LFS only as one deliberate renormalize commit.
- **Git LFS adopted (2026-10-24).** `.gitattributes` tracks `*.uasset`, `*.umap`, source meshes (fbx/obj/abc/glb), images, audio, video, fonts and archives; code, config and docs stay plain git. Two commits by the user: `4ecf87a5` (the attributes) and `111a1187` (`git add --renormalize .` — 25,467 files to LFS pointers). History before them stays plain git (4.87 GiB packed); not rewritten. New clones need Git LFS installed. An earlier abandoned attempt had left a 6 GB local LFS cache in `.git/lfs` (reused by the renormalize); `git lfs prune` after the push frees what's unused.
- **Scanning `.uasset`s for `/Game/` references misses FName-numbered names (2026-10-21).** Unreal stores `Turn_Left_90` as name `Turn_Left` + number 90 (any trailing `_N` without a leading zero), so a text scan sees `Turn_Left`. The CC2 migration missed four turn animations this way and `CC_AnimBP` failed to compile. After a disk-copy migration, also copy same-folder siblings named `*_<N>` from the source.
- **Blueprint compile errors + PIE = a modal dialog that freezes the bridge; a forced kill = "Restore Packages" on the next launch (2026-10-21).** Both block the game thread (bridge times out). Slate dialogs have no UI Automation tree; Escape doesn't close Restore Packages. What worked: screenshot the window (PowerShell `CopyFromScreen`) and click *Skip Restore* by coordinates (`SetCursorPos` + `mouse_event`). Fix compile errors before PIE.
- **The editor bridge goes through a local stdio proxy — editor restarts no longer break it (2026-10-03; proven 2026-10-04 across six real restarts, one a crash).** `.mcp.json` launches `node .claude/unreal-mcp-proxy.mjs` instead of connecting to `http://127.0.0.1:8000/mcp` directly. Background: as a direct HTTP server, `unreal-mcp` was marked `failed` whenever a session started with the editor closed or the editor was closed mid-session for a rebuild, and only `/mcp` brought it back (retries didn't; `reconnect_session_connector` handles claude.ai connectors only). Claude Code can always start the proxy, because it's a local process. It answers `initialize`/`tools/list` itself, since the editor's tool list is three static meta-tools (`list_toolsets`, `describe_toolset`, `call_tool`). The list is snapshotted in `.claude/unreal-mcp-tools.json` and refreshed whenever the editor is reachable. The proxy opens the upstream session lazily, per call. When the editor restarts, its old session id gets a 404 "client should reinitialize"; the proxy opens a new session and retries once, invisibly. With the editor closed, a call returns a readable "not reachable" tool error, and works again as soon as the editor is up. Needs Node 18+ (global `fetch`); no dependencies. Tested against the live editor, a dead port, and a simulated restart. To check the editor's server itself, `netstat -ano | grep LISTEN | grep :8000` should still show `UnrealEditor.exe`. `claude mcp get unreal-mcp` health-checks the proxy. Old direct config, for reference: `{"type": "http", "url": "http://127.0.0.1:8000/mcp"}`.
- **Editor-bridge limits for AnimBlueprints (learned 2026-10-04).** (1) It **cannot create nodes inside anim state graphs** (Idle/Move) — `create_node` fails with `Cannot cast type 'AnimStateNode' to 'Blueprint'` — but it **can read them and set properties on existing in-state nodes** (sync groups were set that way). (2) In the top-level AnimGraph it creates **Save Cached Pose** but **not Use Cached Pose** nodes (never listed by `find_node_types`); designs needing pose reuse need the user to drop in the Use nodes, or avoid reuse (chain layers, give each branch its own source players). (3) **Anim compile errors are invisible** — `compile_blueprint` and the log both say `Compile Errors: []`; real messages are only in the AnimBP's Compiler Results panel. (4) **`read_graph_dsl` is lossy** — drops split rotator pins and the third input of a 3-input AND — so never round-trip a graph through `write_graph_dsl`; use `create_node`/`connect_pins`, and confirm wiring with `get_node_infos`. (5) A wildcard `Equal (==)` fed an enum specialises to a **byte** compare and broke the compile; use `Utilities|Enum|Equal(Enum)`. (6) Asset-specific node types appear only once the asset exists: `Mirror with <MDT>`, `BlendspacePlayer'<asset>'`, `AimOffsetPlayer'<asset>'`. (7) Blend Poses by Enum pins can't be added (`add_node_pin` unsupported, `VisibleEnumEntries` unreadable) — use Blend Poses by bool where two branches suffice. (8) Before risky AnimBP work, save a checkpoint (or note the autosave) — a broken graph got saved once, and rollback had to be done node by node.
- **Array properties can't change size and contents in one bridge write (2026-10-04).** `set_properties` rejects it ("ArrayRemove: elements changed alongside the size change"). Two writes: first shrink/grow without changing surviving elements (or clear to `[]`), then set contents at the final size. Hit on blend-space `SampleData` and layered-blend `BranchFilters`. Writing a struct like a node's `Node` block replaces every field, so always read it first and write it back whole with only the intended change.
- **Never write blend-space samples (or other derived-data assets) through the bridge (2026-10-04).** Writing `SampleData` on a duplicated blend space bypassed the editor's post-edit rebuild; the triangulation still indexed the old 27 samples, and **saving crashed the editor** (`Array index out of bounds: 18 into an array of size 15`). Derived data (`BlendSpaceData`, `GridSamples`) isn't readable either, so the rebuild can't be verified before saving. Same class of risk: AnimSequence additive settings (recompression), Mirror Data Tables (bone-index map), probably pose assets and aim offsets. Create/edit those in the editor; the bridge is fine for simple values read directly (BP defaults, node settings, wiring).
- **Lyra aim-offset samples in this project had no base pose (2026-10-04).** `MM_Rifle_Idle_Hipfire_AO_*` were `AAT_RotationOffsetMeshSpace` with `RefPoseType AnimFrame` but `RefPoseSeq None` — lost in migration — so the aim offset added whole-body offsets and made the character giant. Fixed by setting base pose = `MM_Rifle_Idle_Hipfire_AO_CC`, frame 0, on all 15. The pistol and unarmed AO samples probably have the same fault.
- **The editor's asset registry can lose track of a loaded asset (2026-10-04).** `BP_DualPistols`, later `ABP_FirstPersonArms`: bridge `save_assets`/`exists` reported "Asset does not exist" while the asset was loaded, editable and compiling, and its `.uasset` was on disk. Saving from the editor UI still worked. Restart the editor to re-scan; don't use the bridge's save-all-dirty mode as a workaround (it saves things the user hasn't chosen).
- **Playing a montage stops other montages in the same slot group.** Two montages meant to play at once (dual-pistol main + off-hand reload) need slots in **different groups** — `OffhandSlot` lives in its own `OffhandGroup`.
- **Montage Blueprint-node traps (2026-10-05).** (1) `Montage_Play`'s **`bStopAllMontages`** (default true) stops the montages already playing **in the same slot group** — *corrected 2026-10-06: not every montage*; a turn in `TurnGroup` never cancelled fire/reload. Set it **true** when re-playing a montage to crossfade (the old copy blends out over the new blend-in); `false` leaves the old copy playing underneath — it kept a reload loop running forever. (2) **`StopSlotAnimation` only stops dynamic montages** (from Play Slot Animation), silently ignoring montage assets; use `Montage_StopGroupByName` or `Montage_Stop` with the specific montage (`Montage_Stop` with no montage stops *all*). (3) Lyra's `MM_*_Turn*` clips ship with **Enable Root Motion on** — played as a montage, root motion overrides movement input and the character can't move until it ends. Turn it off; the turn is curve-driven.
- **Anim-node pin values don't always reach the node's settings (2026-10-05).** `set_pin_value` on a Blend Poses by bool's `BlendTime_0/1` pins read back fine on the pin, but the node's `Node.blendTime` stayed 0.1 — the crouch blend snapped. Set anim-node settings through the `Node` struct (`set_properties`, read it first and write it back whole), then read the struct back after compiling.
- **`OnStartCrouch`/`OnEndCrouch` adjustments don't always pair (2026-10-05).** The engine's early-out paths (capsule already at the target size) call them with 0. Accumulating `±ScaledHalfHeightAdjust` onto the camera boom drifted it a step per crouch until it left the map. Derive anything height-related from the capsule's *current* size each frame instead.
- **Reparenting a Blueprint onto a native class: variables merge only on an exact type match (2026-10-05).** Same-named bool/enum Blueprint variables merged into the C++ properties; `float` C++ vs Blueprint "Float" (which is double in UE5) did not — the editor renamed the Blueprint copies to `Speed_0` etc. and their getters kept reading them. Declare AnimGraph-facing reals as `double`. Rehearse a reparent on a duplicate first; the bridge has `set_parent`, and `ProgrammaticToolset.execute_tool_script` batches the cleanup (138 node deletions in one call).
- **Montage sections don't blend (2026-10-06).** Jumping between sections inside one montage — including a looping section wrapping to its own start — is an instant playhead move. A loop whose first and last poses differ snaps. Fix used: re-play the montage from the loop's start a blend-time early with `Montage_PlayWithBlendIn(..., bStopAllMontages = true)`. *Not* inertialization from the character's Tick: the wrap happens inside the anim update, so a request from Tick lands a frame late and smooths nothing.
- **A new `EWeaponAnimType` value needs wiring in three places (2026-10-06):** pins on every Blend Poses by Enum in the AnimGraph (otherwise the node falls back to its Default pose — the unarmed set), and entries in `FireMontages` / `ReloadMontages` on `BP_PlayerCharacter` (otherwise nothing plays, silently). Map keys serialize lower-camel-case through the bridge (`pumpShotgun`); write the whole map back.
- **Montage section data isn't visible to the bridge (2026-10-06):** `CompositeSections` can't be read or written — sections and their links are editor work. `Preview All Sections` ignores loop links; use the row's own Preview.
- **A new Transform (Modify) Bone's optional pins override its settings (2026-10-07).** Created nodes show Translation/Rotation/Scale as pins at their defaults, and at compile the pin value wins — so writing `Node.rotation` through the bridge did nothing, the compile copied (0,0,0) back into `Node`, and the recoil looked "not working" for several rounds (a twist seen during one test was the aim offset, not the node). Hide the pins via `ShowPinForProperties` **first**, then write `Node`, then compile and read `Node` back. A constant-alpha test (break the alpha link, set 1, look for a permanent offset) isolates "is the node applied" from "is the driver working".
- **A stock additive fire clip can drag a re-authored idle back to the original (2026-10-07).** Lyra's `MM_Pistol_Fire` is mesh-space additive with *Selected animation frame* but no base animation set (engine source: that mode needs one), so its delta was baked against some other pose. Layered over the spread dual idle, each shot pulled the arms back to the narrow grip until the montage ended. Moving the blend after the slot didn't help either, and cost a revert. Fix: a copy of the clip with base **Local Animation Frame, frame 0** — pure kick. Check a fire clip's base pose before layering it over a custom idle; change it in the editor (recompression), not through the bridge.
- **AnimGraph getter pins can't be watched (2026-10-08).** Getters feeding anim nodes are copied by the fast path and never execute as Blueprint, so *Watch This Value* shows an empty bubble. To see live AnimInstance values, use a temporary `GEngine->AddOnScreenDebugMessage` in `NativeUpdateAnimation` (fixed key, 0 s duration) or the Rewind Debugger. Also: a value typed into an anim node's Details does nothing while its pin is wired — the wire wins.
- **In-state nodes: the bridge can expose pins and connect, just not create (2026-10-07).** Extends the 2026-10-04 limit: `ShowPinForProperties` writes and `connect_pins` work inside Idle/Move, so the user drops one getter per state and the bridge wires every player to it (20 Play Rate pins done this way).
- **Rotate Root Bone is a local-space node** (2026-10-05) — wiring it between Local→Component / Component→Local fails with incompatible pins. Connect it directly in local space.
- **The pistol aim-offset samples (`MM_Pistol_Idle_ADS_AO_*`) had no base pose either** (2026-10-05) — same fault as the rifle set; fixed by setting base pose `_AO_CC`. A rifle AO on pistol poses twists the wrists when yaw is non-zero.
- **Swapping a weapon's mesh/animation in the Details panel leaves a hidden reference behind.** After `BP_Pistol` was re-pointed to `MilitaryWeapSilver`, its `WeaponMesh` component template still held `AnimationData.AnimToPlay = SciFiWeapDark/.../Fire_Pistol_W` — a leftover from previewing the animation on the component, never shown in the Blueprint's own properties and inert at runtime (`AnimationMode` is `AnimationBlueprint`), but a real hard reference that would have kept the old pack from deleting cleanly. Found 2026-09-21 by grepping the `.uasset` for `/Game/SciFiWeapDark`; confirmed and cleared via the bridge (`ObjectTools.get_properties` on `Default__BP_Pistol_C:WeaponMesh`, set `AnimationData.animToPlay` to `"None"`, compile, save). Rule: before deleting a vendor pack, grep the binaries for its `/Game/` path, not just the Blueprint Details panel — and check component templates, not only the CDO.
- **Searching for an asset by filename convention will miss vendor/migrated content.** The 2026-08-30 (3) audit concluded "no `AnimMontage` asset anywhere in `Content/`" and flagged a fabricated blocker on `BP_Pistol` as a result — but `AM_Pistol_Fire.uasset` was sitting in `Content/Characters/Heroes/Mannequin/Animations/Actions/` the whole time. Two compounding causes: the sweep matched our own `*_Montage` naming convention rather than the asset *class*, so Lyra's `AM_` prefix slipped past; and the Lyra tree is still **untracked** in git, so anything reasoning from `git ls-files` wouldn't see it either. Rule: search assets by type/class (the editor's Content Browser filter, or `.uasset` class inspection), never by filename pattern, and remember that untracked/vendor trees are invisible to git-based searches. Corrected 2026-08-30 (4).
- **The UnrealMCP bridge only auto-starts at editor launch, so ticking the setting mid-session does nothing.** The MCP server isn't a separate process — it's Epic's engine plugin `ModelContextProtocol` (`UE_5.8/Engine/Plugins/Experimental/`), enabled in `ProjectBopis.uproject`, serving on port `8000` at path `/mcp` (name `unreal-mcp`) — defaults that already match `.mcp.json`. Auto-start is gated on `bAutoStartServer` in `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini` but fires exactly once, at `PostEngineInit` (`ModelContextProtocolEditor.cpp:64`). So an editor instance that was already running when the box got ticked will never start the server, and Claude Code's connection is refused despite every setting looking correct. **Fix without restarting the editor:** run `ModelContextProtocol.StartServer` in the editor console (`.StopServer` and `.RefreshTools` also exist). Verify with `netstat -ano | grep :8000` — a bare `GET /mcp` returning **405** is healthy, not broken (streamable HTTP wants POST). **Separately (superseded 2026-10-03 by the stdio proxy above):** Claude Code only attaches MCP servers at its own startup, so with the old direct-HTTP config the server had to be up *before* Claude Code launched. Confirmed 2026-08-30 (4).
- **The weapon-firing pipeline currently assumes a player, not just a Pawn.** `WeaponHolderComponent::EquipWeapon`/`FireEquippedWeapon` both `Cast<AProjectBopisCharacter>(GetOwner())`, and `FireEquippedWeapon`'s aim source is `APlayerController::DeprojectScreenPositionToWorld` — an AI-controlled pawn has no `PlayerController`/viewport to deproject from at all. Confirmed 2026-08-18 while adding animation-driven fire feedback (the montage-playing code hit the same cast). Deliberately **not** fixed preemptively — `AWeaponBase`'s core firing logic (`FireHitscan`/`FireProjectile`, bloom, damage) is actually actor-agnostic and fine; it's specifically the holder/feedback layer that assumes a player. AI aiming can't reuse screen-deprojection anyway (no screen to deproject from — it'd need line-of-sight/perception-based targeting instead), so this was never going to be a small swap-a-cast-for-an-interface fix. Revisit when Phase 5 (enemies) actually defines how AI fires weapons, not before.
- **`WeaponBase::FireMontage` was skeleton-specific, which would've broken if the same weapon were ever fired by two different skeletons** (e.g. player + an enemy archetype) — an `UAnimMontage` is authored against one specific skeleton, so a single montage property on the weapon could only ever be correct for whichever skeleton it was set up for. Caught 2026-08-18 while discussing AI extensibility, **and actually fixed the same session** (see Phase 4's animation checklist item) rather than just logged: `FireMontage` moved off `WeaponBase` entirely onto `AProjectBopisCharacter`, which now plays it on its own mesh after checking `WeaponBase::UsesAnimationDrivenFeedback()` (a pure bool signal). The general lesson stands for next time this shape of problem shows up (Phase 5 enemies, most likely): the weapon shouldn't hold data about how to animate whoever's holding it — each animator should own its own lookup ("given this weapon's identity, what's *my* matching feedback"), not the weapon holding one hardcoded answer for everyone. When an enemy archetype needs its own fire animation, it should follow this same pattern (its own montage/feedback owned on the enemy class, triggered the same way), not extend `WeaponBase` with a per-consumer map.
- **IntelliSense false-positives on `AddDynamic` (and similar delegate macros).** `AddDynamic`/`RemoveDynamic` aren't real functions — they're macros doing compile-time template validation of the delegate signature, and Visual Studio's IntelliSense parser frequently can't follow that and shows a red squiggly "cannot find" error even when the actual build (via UnrealBuildTool) compiles it fine. Confirmed 2026-08-17 on `CollisionComponent->OnComponentHit.AddDynamic(...)`. Rule: if IntelliSense flags a delegate-binding line as an error, trust an actual build result over the editor's live squiggle before assuming the code is wrong.
- **Live Coding cannot handle structural changes to native classes** — confirmed for two distinct cases now. (1) A member's *type* changing (e.g. `WeaponMesh` going from `UStaticMeshComponent` to `USkeletalMeshComponent`): reports success but corrupts any Blueprint referencing that class — it becomes unusable as a parent, Blueprints built on it detach (2026-08-12, engine log: `"Live coding succeeded, data type changes may cause packaging to fail if assets reference the new or updated data types"`). (2) A constructor's component *attachment hierarchy* changing (2026-08-18: reordered `CreateDefaultSubobject` calls and changed `SetupAttachment` targets so the camera attaches to the capsule and the arms attach to the camera, instead of the reverse) — `BP_FirstPersonCharacter`'s Components panel kept showing the old hierarchy order until a full rebuild. Rule, broadened: any change to an existing member's *type*, or to *what attaches to what* in a constructor, needs a full editor restart + Rebuild Solution, not a Live Coding patch — and after rebuilding, also try closing/reopening the affected Blueprint if a Live-Coding-cached hierarchy still looks stale.
- **A rendering-affecting `UPROPERTY` set via direct assignment can leave a stale render proxy, even though the underlying data is correct.** `WeaponHolderComponent::EquipWeapon` set `MeshComp->FirstPersonPrimitiveType = EFirstPersonPrimitiveType::FirstPerson;` directly. Direct field assignment doesn't mark render state dirty, so the unified first-person render path could pick the primitive up with a stale/incorrect transform — inconsistent between "fresh PIE run after an editor restart" (correct) and "Stop→Play again in the same session" (wrong), and also explained why the weapon looked different in FPS view vs. external/spectator view (two separate rendering paths, one working off stale state). Confirmed 2026-08-30 via a debug readout showing the actual relative transform never changed between a "correct" and "wrong" run (ruling out the offset math), plus the tell: manually nudging the weapon's Scale in the Details panel during Play visually "fixed" it by incidentally forcing a render-state refresh. **Fix:** use the paired setter (`SetFirstPersonPrimitiveType()`) instead of raw field assignment. Rule: for any `UPROPERTY` that affects how a primitive renders (not just plain data), check for and prefer a setter function over direct assignment, especially when changing it at runtime (not just at construction) — the setter is usually the one that remembers to invalidate render state.

- **Attaching to a skeletal mesh socket in `BeginPlay` can snap to a stale socket transform.** `UWeaponHolderComponent::EquipWeapon` runs from `BeginPlay`, before the arms mesh's pose is evaluated, so `AttachToComponent(..., WeaponAttachSocketName)` resolves against a socket that isn't yet where it will end up — the weapon ends up visibly misplaced. Confirmed 2026-08-30 (7) by a deliberate test: re-running the identical attach 5 seconds after start corrects the position, proving the attach logic is right and only its *timing* is wrong. Note this is a **different root cause** from the stale-render-proxy bug logged the same day — that one was fixed with `SetFirstPersonPrimitiveType()` and the symptom still came back, which is what led here. Rule: don't assume a socket transform is valid during `BeginPlay`; attach after the mesh has initialized (or re-attach once it has). **Superseded 2026-09-30.** The TEMP 5s timer was removed and the weapon position proved *identical* across a full session — so the timer was never fixing anything, and the August conclusion above was wrong about the cause. Whether a mistimed attach ever existed is now unclear; the attach target also changed from the arms mesh to the body mesh in the third-person conversion. Treat the original diagnosis as unproven rather than settled.
- **The Output Log names the Live Coding failure directly — read it before theorizing.** 2026-08-30 (7): after a structural refactor, the weapon position fixed but *firing* broke, and nothing in the C++ diff explained a firing failure. The log said exactly what happened: `LogClass: UClass WeaponHolderComponent Reload.` / `Could not find existing class ... assuming new or modified class` / `Re-instancing WeaponHolderComponent after reload.` / `LogLiveCoding: Warning: Live coding succeeded, data type changes may cause packaging to fail...`. A full Rebuild Solution fixed it. Third occurrence of the same underlying Gotcha; the lesson added here is procedural — when behavior goes strange right after a Live Coding patch, check the Output Log for `Re-instancing` before forming any other hypothesis.

- **`FHitResult::Location` and `FHitResult::ImpactPoint` are not the same thing, and the difference only bites on swept shapes.** `ImpactPoint` is the point on the surface that was struck; `Location` is where the *querying shape's origin* ended up. For a line trace (zero-thickness ray) they coincide, so hitscan code never notices. For a **swept sphere** the shape stops when its surface touches, leaving its centre one radius out — with `AProjectileBase`'s `InitSphereRadius(5.0f)`, `Location` sits 5cm off the surface. Confirmed 2026-08-31: projectile impact decals appeared on only some surfaces while hitscan decals worked fine on the *same* surfaces. Cause: a decal is a **projection box** whose `DecalSize.X` is its projection depth — also 5 — so the box reached exactly as far as the gap and the surface sat right on the boundary, painting or not depending on angle, curvature, and float precision. Note how misleading the symptom was: it read as a decal *facing* bug, and the next instinct (per-mesh `bReceivesDecals`) was also wrong. The thing that actually cracked it was the observation that hitscan worked on the same surfaces, which isolated it to the code path. **Rule: use `ImpactPoint` for anything placed *on* a surface (decals, impact FX, scorch marks); reserve `Location` for where the moving object itself ended up (stuck projectiles, ricochet origins).**
- **A one-way collision ignore isn't enough to stop a projectile hitting its firer.** `IgnoreActorWhenMoving` on the projectile's own collision component, plus actor comparisons in `OnHit`, still let rounds detonate on the player (2026-08-31). Both sides sweep, so the *other* actor's movement can generate the blocking hit even when the projectile is told to ignore it. The working fix ignores in **both directions** — the projectile ignores the actor, and that actor's root component ignores the projectile — driven by an explicit `AddIgnoredActor()` the weapon calls at spawn rather than inferring from `Instigator`/`Owner` (which is a silent hole if either is unset). `OnHit`'s guard must also return **before `Destroy()`**, or a stray self-hit still consumes the round.
- **The weapon mesh's local +X is not necessarily its barrel axis — don't derive muzzle direction from the actor transform.** 2026-08-31: `Darkness_AssaultRifle` sits at ~72° world yaw off the camera facing with `GripRotationOffset` at zero. Setting the offset to +72 made the number look right (world yaw → `-0.06`) but was **visually wrong** — you ended up sighting down the side of the receiver. Reverted. Any muzzle-position maths derived from "rotate the socket offset by the actor's rotation" inherits the same bad assumption. If muzzle position is ever needed again, measure the socket's world transform directly rather than reconstructing it. This is also why the projectile spawn origin was moved to the crosshair (`TraceStart`) instead: it removes the weapon's orientation from the trajectory entirely.

- **A CDO read-back is not proof that a Blueprint default took effect.** 2026-08-31 (2): `AnimType` was set to `Rifle` on the weapon CDOs through the editor bridge and verified by reading it straight back — but only `BP_FirstPersonCharacter` was compiled afterwards, so the *spawned* weapon instances kept the C++ default (`Pistol`). The ABP then faithfully reported `Pistol` and the bug looked like a graph problem for far longer than it should have. **Rule: set → compile that specific Blueprint → save → verify against a live PIE instance, not the CDO.** Related: `reset_properties` can return `true` without actually clearing a value (setting `"None"` explicitly worked where reset didn't), so verify that too.
- **Grip offsets are in socket space, and the first-person projection shrinks what you see of them.** 2026-08-31 (2): `GripLocationOffset` was reported as "not changing position", but a live PIE read showed the weapon mesh exactly matching the configured `(0, -10, -2)` — it was applying correctly. Two things make small values read as no change: the offset is relative to the `HandGrip_R` socket, whose axes come from the hand bone (so X/Y/Z are *not* forward/right/up), and the weapon renders at `FirstPersonScale 0.6`, so a 10-unit move shows as roughly 6. Tune with large single-axis values first to learn the mapping, then refine. Same underlying trap as the grip-*rotation* mistake logged above.
- **A world-space effect attached to a first-person-projected mesh draws in the wrong place.** 2026-08-31 (2): `SpawnEmitterAttached` returns a particle component rendered through the normal world projection, while `WeaponMesh` is tagged `FirstPersonPrimitiveType::FirstPerson` — so the muzzle flash appeared detached from the barrel even though the socket was correct. Fix: call `SetFirstPersonPrimitiveType(FirstPerson)` on anything spawned onto a first-person primitive. Worth remembering for any future attached VFX (tracers, shell ejection, impact sparks on the weapon itself).

- **A montage's `SequenceLength` is read-only through the editor bridge, but opening the asset editor recalculates it.** 2026-08-31 (4): duplicating an existing montage and repointing its `SlotAnimTracks` segment to a different animation leaves `SequenceLength` stuck at the *source* montage's value — so a 2s reload built from a 0.667s fire montage would play only a third of the way through. Setting the property directly is rejected. The fix is `OpenEditorForAsset` on the montage, which forces the recalculation; then save. Full working method: **duplicate → repoint the segment → open the asset editor → save.** This was initially written off as impossible and the tradeoff accepted on `AM_Rifle_Fire` (which sat inconsistent for a day before being fixed the same way) — worth trying the open-the-editor trick before concluding an asset can't be built through the bridge.

- **A threshold compared against a value that changes must scale with it.** 2026-08-31 (5): `M_Reticle_Corners` masked its corner brackets by testing `min(|x|,|y|)` against an *absolute* `CornerCut` of 0.11, while the idle `Radius` was 0.12. At rest the mask erased nearly the whole shape, so the crosshair looked invisible with near-zero line thickness; as bloom grew `Radius` the brackets appeared from nowhere. Thickness was never actually changing — the mask was eating it, which made it look like a completely different bug. Fixed by making the threshold **`Radius × CornerCut`**, so the brackets hold the same proportion of each side at any radius. General shape of the mistake: any cutoff compared against an animated quantity has to be expressed relative to it, or the effect inverts at one end of the range.
- **Swapping a widget's brush material every tick destroys its dynamic material instance.** 2026-08-31 (5): `SetBrushFromMaterial` creates a fresh MID, so calling it unconditionally each frame throws away every parameter written to the previous one and churns garbage — the reticle would appear to ignore its `Radius`/`Thickness`/`Color`. The fix is a stored `LastCrosshairMaterial` variable and a branch that only swaps on change. Keying off the *equipped weapon* rather than a swap event also means every future acquisition path (pickups, weapon switching) works without notifying the UI.
- **Editor-bridge API details worth remembering** (2026-08-31 (5)): a Blueprint **variable's getter/setter node types don't exist until the Blueprint is compiled** — create the variable, compile, *then* create the nodes. And overloaded functions (`SetScalarParameterValue`, `GetDynamicMaterial`, `SetBrushFromMaterial`) need `declaring_class` passed to `create_node`, or you silently get the wrong variant — the MaterialParameterCollection version, or the by-ref-Brush one that can't take a widget.

## Changelog

- 2026-10-25 (3) — Home test pass: weapon wheel (camera lock, death, cycling), female and male clothing layers, enemy search with the gun down, scripted events stage 2, background music, level exit, room cleared + waves all user-tested. Gunfire audio is to be refactored.
- 2026-10-25 (2) — Dual reload holds the pelvis, `spine_01`–`03` and the off-hand collarbone (`DualReloadHoldAlpha`, two Layered Blend per Bone holds with negative-depth filters); user-tested. The 10-05 accepted quirk is closed.
- 2026-10-25 — CC skin: the clothing push on skin is a WPO along the camera ray instead of Pixel Depth Offset (PDO had made bare skin shadow itself — seams, orange); `CC_SkelMesh` Self Shadow Only off. Gotchas: PDO and lighting, CC's coarse apparel masks.
- 2026-10-24 — Contents list added; the Aswang-era enemy sections marked superseded; the plan's gotcha list (52 entries) moved into *Engineering gotchas → Full list*.
- 2026-10-16 (8) — Focus dead on again (`FocusSpreadMultiplier` default 0); fast-gun recoil (fire montage keeps pace, kick scales with fire rate), user-confirmed.
- 2026-10-16 (7) — Enemy aim at the shot point (planned shots, aim flick, pitch override) tried and reverted.
- 2026-10-16 (6) — First-dive bug fixed: the Start blend space's start position is seeded in `NativeInitializeAnimation` (`GetRestStartPosition`).
- 2026-10-16 (5) — Room encounters: `bHoldsPosition` + `HoldRadius`, reaction beat (`ReactionTimeMin/Max`), `AEncounterTrigger`.
- 2026-10-19 (2) — Explosives (AExplosion, AGrenade, kill slow motion, quick throw, grenade launcher, grenade ammo and HUD count); revolver; two-handed left-hand IK at hip, hip aim hand turn, blade turns minus the root offset; bSeenSinceAlert.
- 2026-10-19 — MAC-11 placeholder (single + dual, SMG ammo, `BP_AmmoPickup_SMG`); bladed stance player-only.
- 2026-10-18 (2) — Bladed stance for the one-handed pistol (mirrored `BS_Rifle_Strafe` lower body via `LayeredBoneBlend_10`; chest, head, arm-from-shoulder and hand turns in `UpdateBlade`). Backsteps for any backward strafe (`BackstepMinAngle`). One-handed equip plays its own left arm. Orphaned `MM_Pistol_Idle_OneHanded_Bladed` deleted.
- 2026-10-18 — Reload upgrades: carried through a roll (1/3 rule; the shotgun's cycle), quick reload and quick draw mid-dive (3×, shown over the dive pose), the left arm follows mid-dive gun switches. Duals: the standing left-gun recoil fixed (node order), the mirrored off-hand montage in the dive branch (`OffhandMirror` cache, `LayeredBoneBlend_9`, `ProneDualOffhandAlpha`). Crash guard `WaitForAnimEvaluation` before mesh physics changes; gotcha added.
- 2026-10-17 — Shootdodge refinements: flight limbs on physics (legs, plus the left arm with a one-handed pistol, easing from firm to loose); the Start state on a Blend Space Evaluator driven from C++ (`ShootdodgeStartTime`); `BackStartOffset`; jog dives jump forward then spin (`ForwardJumpHoldTime`, `ShootdodgeDirectionCatchUpRate`); dive Focus drains as it goes. Camera height re-applied on capsule resizes. Free arm on physics (one-handed pistol, on foot). Weapon pickup mid-roll keeps the roll. Enemies search with the gun down and the head on the last known spot. Camping waits only while evading. Clean-up: `SpendMeter` and a spare Inertialization node removed. Four new gotchas.
- 2026-10-16 (4) — Directional hit indicator: `AddHitIndicator`, sector-based flood control, `UHitIndicatorWidget` (code-drawn arcs); Slate/SlateCore added to the module.
- 2026-10-16 (3) — Shell casings: `AShellCasing` + `UShellCasingSubsystem`, per-weapon `Weapon|Casings` settings, meshes set on all seven weapons.
- 2026-10-16 (2) — Navmesh reverting solved: `bForceRebuildOnLoad` on `Lvl_Sandbox`'s RecastNavMesh, saved via Save All (gotcha added).
- 2026-10-16 — Camping now climbs the hit chance to `CampedHitChance` 1.0 at full heat (replaces `CampingHitBonus`; the cap only limits the un-camped chance). Attack tokens removed; `MaxHitChance` 0.5 on both enemy BPs. Crouch combat stance (`bCrouchCombatStance`, `CrouchCameraOffset` −40). Kneel on/off (`CanPostRollCrouch`). Cleanup: crosshair settings + reticle materials removed; enemy StateTree stopped before unpossess. Two new gotchas.
- 2026-10-15 — **Shooting model reworked to Max Payne 1/2:** hold to fire for every weapon at `TimeBetweenShots` (Semi/Auto, `IntendedTimeBetweenShots` and the cadence penalty removed); spread replaces bloom (`Spread`, moving ×, burst wander, `FocusSpreadMultiplier`); enemy firing pattern per weapon (`FAIFiringPattern AIFiring`) with `BurstShotsMultiplier` / `BurstPauseMultiplier` on the enemy; all seven weapon BPs retuned. Attack tokens only held while usable, nearer enemies take precedence — then **removed entirely** the same day (every enemy in sight can hit; `MaxHitChance` 0.5). New section *Dodge roll and the moves around it* (roll, roll Focus, evasion linger, the kneel, auto/prone reload, dual dive spread, the Shootdodge Inertialization node, reverted experiments). Turn-in-place: crouched turns, quick turn to aim (`AimTurnRate`). `DropAsClass`. Six new gotchas.

- 2026-10-09 (5) — Bullet time renamed **Focus** (trademark): `UFocusComponent`, `UFocusWidget`, `IA_Focus`, `WBP_Focus`, CoreRedirects. Focus feedback (post-process + pitch drop, optional sounds). Projectile effects hide by default.
- 2026-10-09 (4) — Bullet time built (`UBulletTimeComponent`, Q toggle, 0.3× world, slowed player, real-time meter with kill refill / passive regen / infinite, HUD widget). Projectiles: splash opt-in, falloff from the source weapon, point damage, hidden at normal speed; `BP_Cal45Bullet` / `BP_RifleProjectile` at 9,000 cm/s, radius 1.
- 2026-10-09 (3) — Procedural one-handed free-arm swing driven by the feet (`UpdateFreeArmSwing`, auto-gain stride peak, `ModifyBone_5` on `upperarm_l`).
- 2026-10-09 (2) — Free-arm jog swing retried and dropped again; cause recorded (no foot sync markers on the pistol strafe clips).
- 2026-10-09 — One-handed pistol stance flipped (right foot forward) via Mirror nodes in the Idle state; bladed stance dropped; mirrored-strafe attempt recorded under *Decided against*.
- 2026-10-08 (3) — Equip animation on weapon change (`EquipMontages` / `OffhandEquipMontages`, holder → `PlayEquipAnimation`, fire blocked while equipping); dual lowered jog rate scale (`DualLoweredPlayRate`, scale 0.8).
- 2026-10-08 (2) — Ammo phase D done: shared per-type ammo pool on the holder (per-weapon reserve removed, caps per type), `AAmmoPickup`, unlimited carry, number-key slot selection (`WeaponSlot`, `IA_WeaponSlot1–5`), `AWeaponPickup` (fixed/random rounds, acquire / unlock duals / ammo), auto-equip option, `DualWieldClass` / `SingleWieldClass`.
- 2026-10-08 — All weapons to become projectile weapons, bullets hidden at normal speed and shown in slow motion (user decision); projectile backlog recorded (fragmentation opt-in, speed, radius, falloff, visibility rule). Content folder renamed `FirstPerson` → `ThirdPerson`.
- 2026-10-07 (3) — Reticle simplified to a static centre dot; the "bloom drives the reticle" rule suspended; crosshair settings/materials kept unused.
- 2026-10-07 (2) — Dual spread: `EWeaponAnimType::Dual` (dual pistols + planned dual SMGs), `bIsDualWield` exposed, `bDualSpread`; spread idle/fire for hip-fire, original for aiming via `AimFireMontages`/`AimOffhandFireMontages`; AnimGraph steps 3 and 7 updated. New gotcha: additive base pose.
- 2026-10-07 — One-handed pistol (`PistolOneHanded`, `IsPistolAnimType`, `bIsPistolHold`, free-arm layer at `clavicle_l` local space, reload fade, snap exemption); gait (`LocomotionPlayRate` 0.75 on all 32 players, Stride Warping Graph mode + Leg IK); procedural recoil (springs, `AddRecoil`, four Modify Bone nodes, yaw = bend axis). AnimGraph steps renumbered. "One-handed pistols" rejection reversed. New gotcha: Modify Bone pins override node settings.
- 2026-10-06 (3) — Ammo: Phase C marked done (debug lines removed); `EAmmoType` + per-weapon `AmmoType`; pickup design recorded.
- 2026-10-06 (2) — Crouch: long-gun crouch idle is the pack's kneeling neutral clip; crouched duals take the left arm from the crouch clip (`LeftArmAlpha` no longer forced up).
- 2026-10-06 — Shotgun polish: `RoundsPerLoad`, `PumpShotgun` anim type + `BP_PumpShotgun`, per-round reload montage (Start/Loop/End, crossfaded Loop restart, End via SetNextSection), IK off through the rack. Left-hand IK reworked to the `LeftHandGrip` socket, aim-only on long guns (history recorded). `TurnThreshold` 45. Inertialization node added. `bStopAllMontages` note corrected (slot-group scoped). Build script noted.

- 2026-10-05 (3) — Third-person conversion wrap-up: new *Character rig (third person)* section, old first-person rig kept as a dated note; first-person projection principle marked historical; asset rename (`ABP_FirstPersonArms` → `ABP_Player` etc.); *Current state* refreshed.

- 2026-10-05 (2) — AnimBP logic moved to C++ (`UProjectBopisAnimInstance`; Event Graph empty); *Animation architecture* rewritten around it. New *Crouch — a stationary stance* section (request vs state, `bMovementCancelsCrouch`, capsule-derived boom height). Crouch branch added to the AnimGraph description. Snap narrowed to two-handed + upright + stationary. Inertialization noted as the parked fallback.

- 2026-10-05 — Animation architecture updated: snap-down alphas + `bEaseLowering` latch, left-hand IK, chained rifle/pistol aim offsets, new *Turn-in-place* subsection, `TurnSlot`/`TurnGroup`. Dual reload torso motion marked won't-fix.

- 2026-10-04 (2) — Added *Animation architecture* (AnimBP layers, Event Graph variables, slots, sync-group caveat, rejected approaches). Dual pistols section rewritten as built; "reload normally" supersedes "throw away when dry". Hip-fire animation paragraph updated.

- 2026-10-04 — Added weapon raised/lowered (hip-fire) section; stance now
  pull-style, speed decoupled from stance.

- 2026-10-03 — Added reload styles (`PerRound`, fire-interruptible) and the
  pellets/falloff section, for `BP_Shotgun`.

- 2026-08-31 — Created, by splitting the technical half out of
  `Design Document/GameDesignDocument.md` so that document could be rewritten
  as a non-technical pitch piece. Content updated to current state along the
  way: renamed cadence parameters, added the rate-of-fire and ammo sections,
  the first-person projection principle, the projectile spawn-origin and
  self-collision rules, and the current-state summary.
- 2026-09-13 — Setting change (2098 sci-fi → 2002 Philippines noir). Added
  the implications section; removed the coilgun/fragmentation rationale from
  the projectile section (system kept, purpose open); enemies reworded from
  synthetic to human; narrative "no conversation system" rule reopened;
  weapon art marked placeholder. No parameter or architecture changes.
- 2026-09-21 — Weapon pack swapped: `SciFiWeapDark` → `MilitaryWeapSilver`.
  All three weapon Blueprints re-pointed by the user; one stale
  `AnimationData.AnimToPlay` on `BP_Pistol`'s `WeaponMesh` template cleared
  via the editor bridge. `SK_Mannequin` still carries an editor-only preview
  attachment of the old rifle (bridge can't reach it; cleared by hand).
- 2026-09-28 — Horror pivot (Aswang). Enemies are no longer human-only.
- 2026-09-30 — **Enemies section rewritten** for the Aswang direction: three
  families, two-layer health (resilience over mortal, required so the break
  event exists and the bloom skill test survives tankiness), the vocalization
  system as state telemetry, and readability layered by distance. **New
  Combat abilities section** covering dual pistols via pose mirroring,
  shootdodge adapted from the two-handed pistol asset, prone as a transient
  post-dive state, and the `CustomTimeDilation` requirement for bullet-time.
  None of it is built; all of it is design worked out against assets the
  project actually owns.
