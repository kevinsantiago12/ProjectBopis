# ProjectBopis — Implementation Design Document

> Local-only. Written by Claude, from the implementation side of this
> project. The narrative canon in [Lore_And_Design_Notes.md](Lore_And_Design_Notes.md)
> is authored by the user and their design partner (ChatGPT) — that file is
> the source of truth for story, world, and lore, and I'm not rewriting it
> or putting words in its mouth. What follows is my own read on what that
> design asks of the codebase.
>
> Each section leads with a plain-English explanation of the idea and why
> it matters. Where there's an actual technical spec, it's broken out into
> a separate **Implementation Notes** block — that's where the jargon lives.

## What kind of game this is, mechanically

ProjectBopis is a straight-line shooter campaign set in a cyberpunk
Philippines, but the setting isn't my department — that's the design side.
My job starts where the trigger gets pulled. The combat touchstone is
old-school Bungie Halo (the original trilogy, plus ODST and Reach), which
is a clear target: gunfights are won by where you stand and how you use
the trigger, not by staring down a scope or memorizing a pattern. That
rules a few things out right away — no bonus for aiming down sights, no
recoil pattern to practice, no bullet-sponge enemies — and gives the
combat a proven shape to build toward instead of an open-ended one.

## Combat: why "bloom" instead of the usual alternatives

Most shooters keep guns accurate one of three ways: you get more accurate
by aiming down sights, the gun kicks upward in a pattern you have to fight,
or the gun gets less accurate the longer you hold the trigger and recovers
once you ease off — that last one is what Halo: Reach called "bloom," and
it shows up as your crosshair visibly widening and shrinking. The design
rules out the first two, and I think that's the right call here, not just
because Reach did it:

- **Aiming for accuracy** rewards standing still and posting up, which
  fights against a game that wants you moving, strafing, and using cover
  creatively.
- **A recoil pattern** turns "skill" into memorizing how one specific gun
  kicks, practiced outside the fight. That's fine in some games, but it
  doesn't suit fast, improvised firefights that are supposed to be won by
  reading the room, not a known pattern.
- **Bloom** ties accuracy to pacing, and that's something you can read in
  the moment just by looking at your crosshair — do I have time for
  another shot, or should I ease off? That's a skill that carries over to
  every gun, which matters if picking up any weapon is supposed to feel
  immediately usable.

So the rule is simple: **aiming down sights only changes what you see, not
how accurate the gun is.** Accuracy comes from bloom, full stop. That has
to hold true everywhere the weapon code touches accuracy, or the whole
system quietly breaks back into "aiming is just better."

### Implementation notes
- Weapon accuracy is driven entirely by a bloom value, not by aim state.
- Aiming (right-click/LT) must not touch spread, cone angle, bloom
  growth/decay, or damage — it's purely a camera/UI state. It's allowed to
  add a center dot to the reticle, and to trigger a zoomed FOV *if the
  weapon has zoom*, but nothing that resolves the shot.
- Per-weapon data needed to drive bloom:

  | Parameter | What it controls |
  |---|---|
  | `BaseSpreadAngle` | Accuracy cone at zero bloom (best case). |
  | `MaxSpreadAngle` | Accuracy cone at full bloom (worst case). |
  | `BloomPerShot` | Bloom added per shot fired (0–1 scale). |
  | `BloomDecayRate` | Bloom recovered per second while not firing. |
  | `BloomDecayDelay` | Grace period after the last shot before decay starts. |
  | `IntendedCadence` | For semi-auto/precision weapons — firing faster than this adds an extra bloom penalty on top of the normal per-shot amount. |

- The live bloom value (0–1) must drive both the actual random spread used
  to resolve a shot *and* the reticle's visual expansion, from the same
  source number — if those two are ever computed separately, the reticle
  can lie about the gun's real accuracy, which breaks the whole premise.
- Zoom is a separate per-weapon flag from generic aim, so giving a weapon a
  scope can't accidentally also grant it better accuracy.

## Weapons should be tuning knobs, not one-off systems

If we want a favorite gun to stay useful for most of the game, weapons
can't each be their own special, hand-built system — they should mostly be
the same gun underneath, just tuned differently: how fast it fires, how
its accuracy behaves, how much damage it does, how far it reaches, whether
it zooms. Ammo should work the same way across guns too, rather than each
weapon having its own separate reload rules, so running low nudges you
toward switching weapons instead of forcing it.

One thing I can't decide myself: how many guns you can carry at once. Two
is the classic Halo answer, but design hasn't locked that in yet, so I'm
building things so that number can change later without a rebuild.

### Implementation notes
- Shared weapon base class, differentiated by data (fire mode, the bloom
  table above, damage, range falloff, zoom flag) rather than per-weapon
  custom firing code.
- Shared ammo-pool/pickup model rather than bespoke per-weapon reload
  logic.
- Weapon-holder component built with a **configurable** carry capacity
  (not hardcoded to 2), since the carry limit is still undecided.

## Weapon tech: why one gun is a real projectile, not hitscan

Three weapons, one of them a real travel-time projectile instead of an
instant hitscan trace — the design reason is dodgeability. A projectile is
only interesting if the player can actually see it coming and juke it, and
that only matters at **close range**, where an enemy would otherwise have
zero reaction window against an instant-hit weapon. So it's the
close-range weapon that gets the slow, visible round; the mid-range battle
rifle stays hitscan, because at its intended engagement distance a
perceptible travel time would just read as an aiming penalty, not a
dodge-skill test.

The in-world justification is electromagnetic, not plasma — coilguns
accelerate a solid slug through a sequence of magnetic coil stages, so
muzzle velocity scales with how many stages/how much barrel length the
weapon has. A compact close-range weapon simply doesn't have room for
enough stages to reach hitscan-equivalent speeds; the mid-range battle
rifle's longer barrel does. That's a physical reason for the split, not an
arbitrary gameplay carve-out, and it stays consistent if more coilgun-type
weapons get added later (short gun → slow, long gun → fast).

To avoid "slow" reading as "weak," the close-range weapon's round is a
saboted, pre-scored slug that fragments on impact — it trades penetration
for a burst of shrapnel, so a hit that's slower to land also dumps more
damage than a clean kinetic punch-through would. That gives it a real
niche instead of just being an inferior hitscan gun: strongest against
close/grouped/exposed targets, weaker against hard cover or armor plating,
which is where the hitscan pistol and battle rifle stay relevant instead.

### Implementation notes
- `AProjectileBase` (real movement + collision + on-hit damage) belongs to
  the **close-range weapon**, not the battle rifle. Pistol and battle
  rifle stay hitscan.
- On-hit behavior for the close-range projectile should express the
  fragmentation as gameplay, not just visual flavor — e.g. a small-radius
  damage burst / multi-trace spread centered on the impact point, rather
  than a single point-damage hit like the hitscan weapons use.

## Enemies should read at a glance, not just look different

The enemies are meant to be machines, not people, in a bunch of different
shapes and sizes — and the player should be able to tell what they're
dealing with instantly, the same way you can immediately clock an Elite
versus a Grunt in Halo. That kind of instant read doesn't come from one
generic enemy reskinned to look different — a floating drone and a
four-legged war machine shouldn't move or behave the same way underneath.
So rather than one catch-all enemy type with special cases bolted on over
time, enemies should be built from interchangeable pieces — how they move,
how they attack, what role they play in a fight — that get mixed and
matched per enemy type.

### Implementation notes
- The template's `ShooterNPC`/`ShooterAIController` classes were removed
  along with the rest of `Variant_Shooter` — this gets built fresh rather
  than extended from that code.
- New base synthetic enemy actor, with movement type, attack behavior, and
  battlefield role (grunt / elite / support) as data-driven, combinable
  pieces, instead of one class accumulating `if (Type == Hover)`-style
  branches over time.
- Per-archetype StateTree assets (the StateTree plugin is already enabled
  in the project) are a more natural fit than one shared tree with
  branching conditions for every chassis.

## What the level philosophy asks of the code

This part is mostly a level-design job, not a code job — a room's shape is
what makes a shotgun and a sniper rifle both work in the same space
without needing separate paths for each. But it does put one constraint on
the code: the system that decides where enemies spawn and when new waves
trigger can't assume anything about a room's layout — no hardcoded idea of
"the sniper lane" or "the flank route" — because the whole point is that
the *same* room supports different playstyles. Practically, that means
spawn points and encounter pacing should be data that whoever builds a
level places by hand, using a shared tool, rather than assumptions baked
into the game code itself.

## Narrative surface area stays small, on purpose

There are no dialogue choices and no voiced opinions from the main
character, which actually makes my job easier — no branching conversation
system to build, nothing to track about what the player "said," no save
data for choices that were never made. The story gets told one direction
only, through other characters, cutscenes, and things you notice in the
world. Unless that changes, I'm not building any kind of conversation
system.

## Where the codebase actually is right now

Both the Shooter and Horror template variants are being removed — decided
2026-08-09, we're building the gameplay systems from scratch rather than
adapting the template's versions. That means the weapon/AI classes this
document originally planned to audit and extend (`ShooterWeapon`,
`ShooterNPC`, etc.) no longer exist; the systems below get built fresh
against this doc's spec instead of grown out of template code. What
remains is the base `FirstPerson` scaffolding (character/game
mode/controller), which is still the project's default and still works.
See `Documentation/ProjectPlan.md` for the ordered, phase-by-phase build
sequence — this section just tracks current state, the plan tracks the
path.

As of 2026-08-11, Phase 1 (weapon foundation) is **fully complete and
tested working in PIE**: `AWeaponBase` (data-driven fire mode/damage/range/
zoom, a hitscan `Fire()` that dispatches real damage via
`UGameplayStatics::ApplyPointDamage`) and `UWeaponHolderComponent`
(carry/equip, hand-socket attachment onto `FirstPersonMesh`, screen-accurate
firing) both exist, compile, and work end to end. No accuracy model yet —
that's Phase 2, in progress. Things worth flagging for whoever picks this
up next:
- Damage correctly dispatches on hit, but nothing has a `Health`
  property or overrides `TakeDamage` yet, so it's currently inert —
  intentional, since Phase 4 (enemies) is what's meant to consume it.
- The weapon-holder's `StartingWeaponClass` (spawns a weapon at
  `BeginPlay`) is a deliberate placeholder for testing, not the intended
  final weapon-acquisition design — no pickup system exists yet.
- A marketplace weapon pack, `Content/SciFiWeapDark/` (7 animated
  weapons — Pistol/AssaultRifle/Shotgun/SniperRifle/RocketLauncher/
  GrenadeLauncher/Knife — with sounds, FX, pickup Blueprints), was added
  and is now the source for weapon meshes (currently `Darkness_Pistol`,
  unanimated for now). It's kept in its own top-level folder, untouched —
  moving/renaming assets inside a pack this size risks breaking its
  internal cross-references, so treat it as read-only vendor content and
  reference it from our own Blueprints/data rather than reorganizing it.
  This is also why `WeaponBase::WeaponMesh` is a `USkeletalMeshComponent`
  now, not `UStaticMeshComponent` — needed to use the pack's animated
  meshes.
- The weapon's trace source is **not** simple camera-forward. Per a
  deliberate Halo-accuracy request, `WeaponHolderComponent` deprojects a
  specific screen-space point (`CrosshairViewportPositionY = 0.667`,
  i.e. horizontal center, 2/3 down the viewport — matching Halo's actual
  reticle position) via `APlayerController::DeprojectScreenPositionToWorld`,
  rather than tracing from the raw camera transform. This is the
  intended permanent behavior, not a placeholder.

As of 2026-08-12, Phase 2 (bloom/accuracy) is also **fully complete**:
`WeaponBase` now has real bloom state (`CurrentBloom`/`TimeSinceLastShot`),
spread driven by `FMath::Lerp`/`FMath::VRandCone`, decay, and a cadence
penalty for firing faster than a weapon's intended pace — matching the
combat spec in full, not just planned. Phase 3 (reticle/aim/zoom UI) is
underway: `UReticleWidget` exists as the C++ foundation, and a second
marketplace pack, `Content/CleanFlatIcons/` (generic icon set, ~17,800
files), was added for crosshair art — same "leave vendor content in its
own folder, untouched" rule as `SciFiWeapDark`. The reticle is confirmed
showing on screen in PIE, and aim input/state (`AProjectBopisCharacter::IsAiming()`)
is wired up.

As of 2026-08-17, Phase 3 is **fully complete**: zoom FOV gating
(`WeaponBase::HasZoom()`/`GetZoomedFOV()`, camera `FieldOfView` — not
`FirstPersonFieldOfView`, a separate property that only governs the
arms/weapon rendering pass) and the sanity check both closed out, including
a real fix — zoom and the Halo-accurate off-center trace source
(`CrosshairViewportPositionY = 0.667`) permanently disagreed on where
"center" was once FOV actually changed, since FOV always narrows around
the camera's true optical center. Simplified back to `0.5f` (true center)
for both hip-fire and zoom rather than building dynamic per-state
repositioning — a deliberate scope call. Phase 4 fire feedback (per-weapon
`FireSound`/`MuzzleFlash`/`MuzzleSocketName`, plus a `bUseAnimationDrivenFeedback`
flag for once real fire animations exist) is also complete; the
hit-impact decal step is in progress using a newly imported pack,
`Content/UWC_Bullet_Holes/` (real per-surface decal materials).

**Scope decision (2026-08-12):** enemies (old Phase 4) are deliberately
deferred behind a new phase focused on getting three weapons fully
realized first — sound, muzzle flash, hit decals, a real projectile
weapon (the close-range rifle; pistol and battle rifle stay hitscan —
reversed from the original 2026-08-12 call, see the "Weapon tech" section
above for why), and proper POV arms animation. See `Documentation/ProjectPlan.md`
Phase 4 for the full breakdown. Animation scope was briefly considered for
*both* `FirstPersonMesh` (POV) and `Mesh` (the body — how any other actor
would see the player), reasoning that keeping both functional now would
avoid retrofitting for spectate/co-op later — but that was walked back to
just the arms; animating the body is deferred until spectate/co-op is
actually being built, not done preemptively.

**Engineering gotcha worth knowing before touching native classes again:**
Unreal's Live Coding cannot safely handle a class member's *type* changing
(confirmed 2026-08-12, via the engine's own log warning after `WeaponMesh`
went from `UStaticMeshComponent` to `USkeletalMeshComponent`) — it silently
corrupts any Blueprint built on that class rather than failing loudly. Any
change to an existing member's type needs a full editor restart + Rebuild
Solution, never a Live Coding patch. Full detail in `Documentation/ProjectPlan.md`'s
"Gotchas" section.

## Engineering backlog
Superseded by `Documentation/ProjectPlan.md`, which breaks this same work
into ordered phases meant to be tackled incrementally. Keeping a short
pointer here rather than a duplicate list:
1. Weapon foundation + bloom accuracy model (Project Plan Phases 1-2).
2. Reticle/aim/zoom UI (Phase 3).
3. Enemy archetype foundation (Phase 4).
4. First playable arena to validate the combat loop (Phase 5).

## Changelog
- 2026-08-09 — Initial skeleton created.
- 2026-08-09 — Rewritten against locked canon from `Lore_And_Design_Notes.md`; added combat/bloom implementation spec and engineering backlog.
- 2026-08-09 — Converted to local HTML artifact, rendered from the Markdown source.
- 2026-08-09 — Reworded in full as an original implementation-design document, not a restructured summary of the lore notes.
- 2026-08-09 — Rewritten again to separate plain-English explanations from technical jargon, which is now confined to "Implementation notes" blocks.
- 2026-08-09 — Both template variants removed (starting gameplay systems from scratch); engineering backlog superseded by `Documentation/ProjectPlan.md`.
- 2026-08-09 — Phase 1 weapon foundation (`WeaponBase`, `WeaponHolderComponent`, hitscan fire, input wiring) mostly implemented; noted as inert until Phase 4 adds a damage-consuming enemy.
- 2026-08-11 — Phase 1 fully complete and tested in PIE. Integrated the `SciFiWeapDark` marketplace weapon pack (weapon mesh is now skeletal, not static). Trace source reworked to deproject a Halo-accurate screen-space point rather than using raw camera-forward. Phase 2 (bloom) started.
- 2026-08-12 — Phase 2 (bloom/accuracy) fully complete and matches the combat spec. Diagnosed and documented a Live Coding data-type-change gotcha. Phase 3 (reticle UI) started; added the `CleanFlatIcons` marketplace pack for crosshair art.
- 2026-08-12 — Reticle confirmed visible in PIE; aim input/state tracking added and compiled.
- 2026-08-17 — Projectile-weapon assignment reversed: the close-range rifle is now the real-projectile weapon (electromagnetic coilgun, fragmenting round, dodgeable at close range by design); battle rifle and pistol stay hitscan. Added "Weapon tech" section explaining the coil-stage-length rule and fragmentation rationale.
