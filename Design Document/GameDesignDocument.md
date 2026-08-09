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
- The template already has `ShooterNPC` / `ShooterAIController` /
  `ShooterNPCSpawner` built on StateTree
  (`Source/ProjectBopis/Variant_Shooter/AI/`) — a reasonable foundation,
  but currently a single class rather than a composable one.
- Needs an archetype layer on top: movement type, attack behavior, and
  battlefield role (grunt / elite / support) as data-driven, combinable
  pieces, instead of one class accumulating `if (Type == Hover)`-style
  branches over time.
- Per-archetype StateTree assets are a more natural fit than one shared
  tree with branching conditions for every chassis.

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

Right now the project is still Epic's out-of-the-box FPS template, with
both a Shooter and a Horror variant included. None of the systems above
exist yet. The current weapon code is still running on the template's
stock aim-and-fire behavior, which I haven't checked yet — templates like
this commonly make aiming down sights more accurate by default, which
would directly break the "no aim bonus" rule if it's happening here. The
Horror variant doesn't have an obvious place in a cyberpunk sci-fi shooter
as currently planned; I'm leaving it alone rather than deleting it, in
case it turns out to be useful later, but right now it's just sitting
there unused.

## Engineering backlog
1. Check `ShooterWeapon` / `ShooterWeaponHolder` for template aim-accuracy behavior and remove it.
2. Build the bloom model above as a reusable weapon component, single source of truth for both shot resolution and reticle UI.
3. Reticle UI that reacts to live bloom + aim/zoom state.
4. Zoom as an independent per-weapon flag, not tied to the generic aim input.
5. Archetype layer on top of `ShooterNPC`/`ShooterAIController` for enemy chassis variety.
6. Revisit the Horror variant's fate once tone is confirmed.

## Changelog
- 2026-08-09 — Initial skeleton created.
- 2026-08-09 — Rewritten against locked canon from `Lore_And_Design_Notes.md`; added combat/bloom implementation spec and engineering backlog.
- 2026-08-09 — Converted to local HTML artifact, rendered from the Markdown source.
- 2026-08-09 — Reworded in full as an original implementation-design document, not a restructured summary of the lore notes.
- 2026-08-09 — Rewritten again to separate plain-English explanations from technical jargon, which is now confined to "Implementation notes" blocks.
