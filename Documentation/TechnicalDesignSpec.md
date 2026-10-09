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
parameters, fire-rate cap, full-auto, per-weapon anim selection, ammo
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

## Combat: bloom accuracy model

The design rules out ADS-for-accuracy and camera-climb recoil. Accuracy is
driven entirely by a bloom value.

- Weapon accuracy is driven entirely by bloom, **not** by aim state.
- Aiming must not touch spread, cone angle, bloom growth/decay, or damage —
  it is purely a camera/UI state. It may add a centre dot to the reticle and
  trigger a zoomed FOV *if the weapon has zoom*, but nothing that resolves
  the shot.
- The live bloom value (0–1) must drive both the random spread used to
  resolve a shot **and** the reticle's visual expansion, from the same source
  number. If those are ever computed separately the reticle can lie about the
  gun's real accuracy, which breaks the premise.
- Zoom is a separate per-weapon flag from generic aim, so giving a weapon a
  scope can't accidentally grant it better accuracy.

**Reticle is now a static dot (user decision, 2026-10-07).** `WBP_Reticle`
draws a fixed 6 px white circle at screen centre, the same for every weapon. The
bullet above about the reticle's visual expansion is **suspended**: bloom still
resolves every shot, but nothing shows it. Implementation:
- `Image_192`'s brush: no material, *Rounded Box*, 6×6, rounding
  `HalfHeightRadius` (corner radii 3).
- Canvas slot: 6×6, centre-anchored.
- Event Tick chain and `LastCrosshairMaterial` deleted.

Left in place, now unused, until the accuracy model is settled:
- `FCrosshairSettings` on the weapons;
- `UReticleWidget::GetCurrentBloom` / `GetCrosshairSettings`;
- `M_Reticle` / `M_Reticle_Corners`.

If bloom feedback comes back, those are the pieces to re-wire.

### Bloom parameters

| Parameter | What it controls |
|---|---|
| `BaseSpreadAngle` | Accuracy cone at zero bloom (best case). |
| `MaxSpreadAngle` | Accuracy cone at full bloom (worst case). |
| `BloomPerShot` | Bloom added per shot fired (0–1 scale). |
| `BloomDecayRate` | Bloom recovered per second while not firing. |
| `BloomDecayDelay` | Grace period after the last shot before decay starts. |
| `IntendedTimeBetweenShots` | Seconds between shots the weapon is "meant" to be fired at — firing sooner adds an extra bloom penalty. Renamed from `IntendedCadence` (shots/sec) on 2026-08-31. |

### Rate-of-fire parameters

Two deliberately separate limits:

| Parameter | Meaning |
|---|---|
| `TimeBetweenShots` | Hard mechanical cap, in seconds. Enforced by `CanFire()`. Tapping faster does nothing. |
| `IntendedTimeBetweenShots` | Soft accuracy limit. Firing sooner is allowed but adds bloom. |

**These two must differ.** If the hard cap equals the intended interval, the
bloom cadence penalty becomes unreachable dead code. The gap between them is
the Reach-style window: fire faster than is comfortable, pay in accuracy, but
never exceed the mechanical limit.

### Configured values

**Claude-proposed starting values, not design canon.** Chosen to be Halo:
Reach-accurate in shape — a first shot from full rest is always precise, so
`BaseSpreadAngle` is `0°` on every weapon. Expected to move once there's
something to shoot at.

| Field | Pistol | Close-range rifle | Battle rifle |
|---|---|---|---|
| `BaseDamage` | 25 | 15 (+ fragment burst) | 35 |
| `MaxRange` | 5000 | 2500 | 8000 |
| `BaseSpreadAngle` | 0° | 0° | 0° |
| `MaxSpreadAngle` | 3.0° | 6.0° | 4.0° |
| `BloomPerShot` | 0.12 | 0.08 | 0.18 |
| `BloomDecayRate` | 0.8 | 0.5 | 0.6 |
| `BloomDecayDelay` | 0.25 | 0.2 | 0.35 |
| `TimeBetweenShots` | 0.125 | 0.083 | 0.2 |
| `IntendedTimeBetweenShots` | 0.2 | 0.1 | 0.286 |
| `FireMode` | Semi | Auto | Semi |
| `bHasZoom` | false | false | true (`ZoomedFOV` 30) |
| `bIsProjectileWeapon` | false | true | false |
| `AnimType` | Pistol | Rifle | Rifle |

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

Bloom applies to the handed-in direction, so spread now works off the
muzzle→aim line for free. Projectiles spawn at `TraceStart`, which is now the
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

`PelletsPerShot` (default 1) and `PelletSpreadAngle` (default 0). Bloom
displaces the **pattern centre**; the pellet cone spreads around it at a fixed
width — width is a property of the gun, bloom stays the measure of
discipline. One pellet at zero spread skips the second random draw, so
single-shot weapons are unchanged. Ammo, bloom, sound and animation are
per shot, not per pellet. `BaseDamage` is per pellet.

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
[ProjectPlan.md](ProjectPlan.md) for the phase breakdown. Summary as of
2026-10-05:

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

---

## Changelog

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
