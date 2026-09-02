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

### Trace source

The weapon's trace source is **not** camera-forward. Per a deliberate
Halo-accuracy request, `WeaponHolderComponent` deprojects a specific
screen-space point via `APlayerController::DeprojectScreenPositionToWorld`.

`CrosshairViewportPositionY` was originally `0.667` (horizontal centre, 2/3
down the viewport, matching Halo's actual reticle position), but that
permanently disagreed with zoom about where "centre" was — FOV always narrows
around the camera's true optical centre. Simplified back to `0.5` (true
centre) for both hip-fire and zoom rather than building dynamic per-state
repositioning. A deliberate scope call.

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

`AProjectileBase` (real movement + collision + on-hit damage) belongs to the
**close-range weapon**. Pistol and battle rifle stay hitscan.

On-hit behaviour expresses fragmentation as gameplay, not visual flavour — a
small-radius damage burst centred on the impact point rather than a single
point-damage hit.

Projectile defaults: 3000 u/s (~30 m/s, watchable and dodgeable at its 25m
range, which is the entire design premise), gravity disabled, 5s lifespan,
150-unit fragment radius at 10 damage.

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

---

## Enemies

- The template's `ShooterNPC`/`ShooterAIController` were removed with
  `Variant_Shooter` — this gets built fresh, not extended from that code.
- New base synthetic enemy actor, with movement type, attack behaviour, and
  battlefield role as data-driven, combinable pieces, instead of one class
  accumulating `if (Type == Hover)`-style branches.
- Per-archetype StateTree assets (the plugin is already enabled) are a better
  fit than one shared tree with branching conditions for every chassis.

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

No dialogue choices and no voiced protagonist opinions means **no branching
conversation system**, nothing to track about what the player "said", and no
save data for choices that were never made. Unless that changes, no
conversation system gets built.

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
  `TakeDamage` — finally does something.

### Vendor content

Marketplace packs live in their own top-level folders, **untouched**:
`SciFiWeapDark` (weapons), `CleanFlatIcons` (reticle art), `UWC_Bullet_Holes`
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

- 2026-08-31 — Created, by splitting the technical half out of
  `Design Document/GameDesignDocument.md` so that document could be rewritten
  as a non-technical pitch piece. Content updated to current state along the
  way: renamed cadence parameters, added the rate-of-fire and ammo sections,
  the first-person projection principle, the projectile spawn-origin and
  self-collision rules, and the current-state summary.
