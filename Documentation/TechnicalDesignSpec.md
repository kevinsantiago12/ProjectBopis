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
first-person rig, the rendering target, and every gotcha below. None of it is
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

Baked lighting means **muzzle flashes and weapon fire should not cast dynamic
light** by default — a per-shot point light is exactly the kind of cost this
target is avoiding. Impact and muzzle effects carry their read through
emissive materials and particles instead, which is also what the era did.

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

`AProjectileBase` (real movement + collision + on-hit damage) is currently
assigned to the **close-range rifle** as a test bed. Pistol and battle rifle
are hitscan.

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

---

## Ammo

Four phases: **A** state + gating + dry fire (done), **B** reload (done, needs
editor setup), **C** HUD readout, **D** pickups.

Design decisions: **separate reserves per weapon** rather than a shared pool,
**auto-reload off** by default, **reload cancels on weapon swap**.

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
`PerRound` waits `ReloadStartDelay`, then loads one round every
`TimePerRound` via a self-re-arming `LoadRound()` timer until full or the
reserve is dry. Each round is committed as it goes in. **Firing interrupts a
`PerRound` reload** when at least one round is loaded — `Fire()` cancels the
reload and shoots; with nothing loaded it still returns `Reloading`.
Animation sync is not wired: a per-round montage needs Start/Loop/End sections
driven by weapon state, which wants weapon delegates (`OnRoundLoaded`,
`OnReloadEnded`) — deferred to TPS Step 7. Not modelled: chambering after a
reload from empty.

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

The shotgun is SPAS-style: **semi-auto, no pump between shots** — just
`FireMode Semi` with a short `TimeBetweenShots`. A pump-action variant needs
no code (longer cadence, pump in the fire animation).

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

`ABP_FirstPersonArms` drives the third-person body. **Lyra is the animation
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
`UpdateLocomotion` → weapon state → `UpdateUpperBody` → `UpdateArmAlphas` →
`UpdateTurnInPlace`. With no pawn (AnimBP preview) everything stays at defaults.

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
| `UpperBodyAlpha` | target = 1 if raised OR `IsSlotActive("DefaultSlot")` (fire/reload), else 0. Eases up (`UpperBodyInterpSpeed` 12). **Snaps down only when two-handed AND standing upright AND `Speed < StationarySpeed` (10) AND not latched** — every other drop eases |
| `LeftArmAlpha` | duals only: `Lerp(UpperBodyAlpha, 1, DualCrouchBlend)` |
| `DualLoweredAlpha` | duals only: `(1 − UpperBodyAlpha) × (1 − DualCrouchBlend)` |
| `LeftHandIKAlpha` | target = `UpperBodyAlpha` if two-handed and not reloading, else 0; eases up (10), snaps down (the target itself eases whenever the layer does) |
| `RootYawOffset` | turn-in-place — see below |

Private state (no `UPROPERTY`): `bEaseLowering` (latch: `IsSlotActive(DefaultSlot)
OR (latch AND lowering)` — the drop after a montage ends eases), `bIsDualWield`,
`DualCrouchBlend` (eased `bIsCrouched` — crouched duals hold both guns up, since
the lowered-dual layer is a standing pose; easing it means standing up lowers
the guns smoothly), and the turn-in-place bookkeeping.

Tuning on the AnimBP class defaults: `UpperBodyInterpSpeed`,
`LeftHandIKInterpSpeed`, `RootYawRecoverySpeed`, `StationarySpeed`,
`TurnThreshold`, `MaxRootYawOffset`, `TurnLeftMontage`, `TurnRightMontage`.

**AnimGraph-facing reals are `double`.** Blueprint "Float" is double in UE5, and
on reparenting a Blueprint variable only merges into a same-named native
property of exactly the same type. Declared as `float`, the editor renamed the
Blueprint copies (`Speed_0`…) and the getters kept reading them.

**Why the snap, and why so narrow:** easing the raised layer out on a two-handed
grip moved the left arm through the torso. A snap hides that, but read as a pop
everywhere except standing still upright — so moving, crouched, duals and
post-montage drops all ease. `IsSlotActive("DefaultSlot")` (not
`IsAnyMontagePlaying`) so turn montages don't count as a fire/reload.

### AnimGraph (top level, in evaluation order)
1. **Locomotion state machine** (Idle/Move). Move: per-weapon Blend Poses →
   `BS_Rifle_Strafe` (rifle, shotgun) / `BS_Pistol_Strafe` (pistol), both
   Direction (X ← `CardinalDirection`) × Speed (Y). 4-way Lyra walk (250) / jog
   (500) / idle (0). Idle: per-weapon clips; shotgun lowered idle from the pack.
   **Crouch branch** (2026-10-05, top level — the bridge can't add nodes inside
   states): Blend by bool `bIsCrouched` (0.25 s; True ← crouch, False ← state
   machine) where crouch = Blend by bool `Speed > 10` (0.2 s) between crouch idle
   (`MM_Rifle/Pistol_Crouch_Idle`) and crouch walk (`BS_MM_Rifle_Crouch_Walk` /
   `BS_MM_Pistol_Crouch_Walk`, 1D, X ← `CardinalDirection`), each picked by
   `CurrentAnimType == Pistol`. Since crouch is stationary-only, the walk is a
   fallback for a ceiling blocking the uncrouch.
2. **Orientation warping:** Local→Component → `OrientationWarping` (Manual, angle
   ← `WarpAngle`, spine_01–05 distribute 0.5, IK foot root/feet) →
   Component→Local → **`TurnSlot`** (turn-in-place montages) → **Save Cached
   Pose `Loco`**. Plays the cardinal clip and
   rotates the legs by the remainder — fixes the forward-left/back-right
   scissoring that Lyra's side clips produce when blended (each side clip only
   matches one diagonal pair).
3. **Upper-body layer** (`spine_01`, mesh-space rotation): Base ← Use `Loco`;
   Blend ← **`DefaultSlot`** whose source is the hip-fire idle (bool: pistol ?
   `MM_Pistol_Idle_Hipfire` : `MM_Rifle_Idle_Hipfire`); weight `UpperBodyAlpha`.
   Montages are therefore upper-body only (legs keep stride), and the raised
   pose holds between shots.
4. **Aim offsets, chained** (2026-10-05): `AO_MM_Rifle_Idle_Hipfire` →
   `AO_MM_Pistol_Idle_ADS`. Both X (yaw) ← −`RootYawOffset`, Y ← `AimPitch`.
   Alphas are exclusive: rifle = `UpperBodyAlpha` unless `CurrentAnimType ==
   Pistol`, pistol = `UpperBodyAlpha` only for pistols. Chaining two players
   avoids needing a second Use Cached Pose. The rifle AO on pistol poses
   twisted the wrists.
5. **Left-hand IK** (Lyra style): Local→Component → CopyBone `hand_r` →
   `ik_hand_gun` → TwoBoneIK `hand_l` → effector `ik_hand_l` (bone space, take
   rotation), joint target `lowerarm_l`, alpha `LeftHandIKAlpha` →
   Component→Local. Raised only — always-on twisted the arm in lowered clips.
6. **Dual left-arm layer** (`clavicle_l`): Blend ← pistol idle → **`OffhandSlot`**
   → `AO_MM_Pistol_Idle_ADS` (X ← **+**`RootYawOffset`, the mirror flips it) →
   Mirror (`MDT_Mannequin`); weight `LeftArmAlpha`.
7. **Dual lowered layer** (`pelvis` — whole body): Blend ← unarmed walk/jog
   blend space (play rate **0.7**) / `MM_Unarmed_Idle_Ready` (bool Speed > 10)
   → finger layers (thumb + metacarpals: `_r` from pistol idle, `_l` from
   mirrored pistol idle — closed grips); weight `DualLoweredAlpha`.
8. **Rotate Root Bone** (Yaw ← `RootYawOffset`; a local-space node) → Output.

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
- **Trigger:** `|Offset| > 90` and `TurnSlot` inactive → `Montage_Play`
  (`AM_Rifle_TurnRight_90` if Offset < 0, else `AM_Rifle_TurnLeft_90`) with
  **`bStopAllMontages = false`** (the default would cancel fire/reload).
  `TurnScale = |Offset| / 90` is stored at trigger.
- **Wind-down:** `C = RemainingTurnYaw / TurnYawWeight` (when weight > 0.01);
  `Offset −= (C − PrevTurnYawCurve) × TurnScale` once a previous value exists.
  `TurnScale` makes a turn close exactly the gap that triggered it (≈1 at 90°;
  tried 45° — rolled back by user choice).
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
experiment; **sync to top-level arm players never demonstrably worked**. The
lowered-dual branch avoids the need by taking the whole body from one clip. The
settings are harmless; treat sync between in-state and top-level players as
unreliable.

### Decided against
- Shotgun upper body layered over Lyra legs (looked bad).
- One-handed single pistols with an unarmed free arm (every variant looked
  worse) — single pistols keep the two-handed grip.

### Open
- Turn-in-place extras: 180° turns, crouched turns (crouch clips exist),
  per-weapon turn sets.
- Inertialization for the remaining two-handed snap, if it ever reads badly:
  Inertialization node before the Output plus `RequestSlotGroupInertialization
  ("TurnGroup", 0.3)` on the snap frame (TurnSlot is always evaluated; a slot
  forwards requests even with nothing playing — checked in engine source).
- Strafe jog play rate / stride warping if feet slide at 500.
- Shotgun aim offset: uses the rifle AO (fine so far); unarmed AO samples
  probably have the same missing-base-pose fault if ever used.

## Combat abilities — dual-wield, shootdodge, bullet-time

Designed 2026-09-30. **Dual pistols built 2026-10-04**; shootdodge and bullet-time not built. Recorded because the animation
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
- `BP_DualPistols`: mag 24, reserve 120 (max 240), `AnimType Pistol`.

**Accepted quirk (2026-10-05, won't fix):** the reload montage leans/twists the
torso (authored for a two-handed reload). User judged it minor. If it's ever
revisited: a no-spine copy of the clip plus a `DualReloadMontages` map used
instead of `ReloadMontages` for dual weapons.

**Later:** dual-capable SMGs would want a weapon flag (e.g. `bOneHanded`) rather
than keying anything off `AnimType == Pistol`.

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

### Bullet-time — the counterintuitive part

Global time dilation slows **everything on world time**, which includes
`TimeBetweenShots`, `ReloadDuration` and bloom recovery. Naïve slow-motion
therefore slows *the player's own gun* along with the world — the opposite of
the intended feel.

Fix: `AActor::CustomTimeDilation` on the player, keeping them near normal
while the world crawls. Cheap to do, painful to discover late.

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

Applied as: `EWeaponAnimType` on the weapon; `FireMontages` and
`ReloadMontages` maps keyed by that enum on the character.

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

### First-person projection is a separate rendering path

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

## First-person rig

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
2026-08-31:

- **Phases 0–3 complete**: project cleanup, weapon foundation, bloom accuracy,
  reticle/aim/zoom.
- **Phase 4 (weapon content & feel)** nearly complete: fire feedback, hit
  decals, projectile system, all three weapons configured, fire-rate cap,
  full-auto, per-weapon animation selection, scoped zoom, ammo phases A–B.
  Outstanding: ABP graph work for per-weapon locomotion clips, grip position
  tuning, ammo HUD and pickups, left-hand IK.
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
(decals), `ImpactsVFXVol1` (Niagara impacts, imported by accident, deferred),
and the migrated Lyra animation library under `Content/Characters/Heroes/`.

Moving or renaming assets inside a pack breaks its internal cross-references —
treat them as read-only and reference them from our own Blueprints and data.

---

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

---

## Changelog

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
