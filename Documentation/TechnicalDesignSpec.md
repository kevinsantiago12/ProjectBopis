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
| Focus `FocusSpreadMultiplier` | On the **Focus component** (renamed from `FocusMaxBloomMultiplier`); applies during any Focus, the dive's included. 1 = no effect. |

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

---

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
  only) — the current insert finishes, then the rack plays.
- `ActiveReloadMontage` tracks the montage from `DoReload` until it stops;
  `IsReloadAnimating()` exposes that so the AnimBP keeps the left-hand IK off
  through the whole montage, rack included (the weapon's `IsReloading()` goes
  false before the rack).
- Montages without a `Loop` section (magazine reloads) are untouched.

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

---

## Enemies

Rewritten 2026-09-30 for the Aswang direction. Lore in
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

### Three families

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
| `DualLoweredPlayRate` | `LocomotionPlayRate × DualLoweredRateScale` — the lowered-dual walk/jog rate |
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
   `LeftHandIKAlpha` → Component→Local. The Modify Bone replaces the clip's
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
   → **`OffhandSlot`**
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
Open: the rotation route needs socket orientation tuned against `hand_l` axes;
the attachment-chain offset is mathematically sound but misbehaved here — the
cause wasn't isolated.

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
- Camera pull-in for duals — not pursued.
- A runtime run-and-gun alpha blending the spread clip under, then over, the
  slots — never held through shots (the base-pose problem above). Reverted.

The old note about dual SMGs needing a `bOneHanded` flag is superseded:
`AnimType Dual` covers them.

**Accepted quirk (2026-10-05, won't fix):** the reload montage leans/twists the
torso (authored for a two-handed reload). User judged it minor. If it's ever
revisited: a no-spine copy of the clip plus a `DualReloadMontages` map used
instead of `ReloadMontages` for dual weapons.

### Shootdodge

#### Built — step 1, the dive (2026-10-10, user-confirmed in PIE)

**Design (user):**
- **Left Shift**, action `IA_Shootdodge` (Shootdodge).
- Dive **in the movement input's direction relative to the camera**, in any
  stance. The body snaps to the camera first. No input = forward.
- **Focus:** needs ≥ `MinFocusToDive` (25), spends `FocusCost` (25) once.
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
  - A Toggle during free Focus claims it as the player's own.
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
- **Camping heat doesn't build while knelt:** `UpdateCampingHeat` pauses the
  clock at the spot; heat already built holds (no drain).
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

The rule: a weapon may say *whether* it wants animation-driven feedback, and
may state its own *identity* (`AnimType`), but never *what* to play. Each
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

Full list with reproduction detail lives in
[ProjectPlan.md](ProjectPlan.md)'s "Gotchas learned the hard way" section. The
ones most likely to bite:

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

## Changelog

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
