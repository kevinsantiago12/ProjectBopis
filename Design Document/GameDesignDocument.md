# ProjectBopis — Game Design Document

> **A pitch-facing document.** No code, no parameters, no jargon. This is what
> the game *is* and why it works that way.
>
> Technical specifications live in
> [Documentation/TechnicalDesignSpec.md](../Documentation/TechnicalDesignSpec.md).
> Build sequence lives in [Documentation/ProjectPlan.md](../Documentation/ProjectPlan.md).
> Narrative and world canon is owned by the design side and lives in
> [Lore_And_Design_Notes.md](Lore_And_Design_Notes.md) — this document
> summarises it for pitch purposes and does not extend it.
>
> **Rewritten 2026-09-13** for the change of setting. The previous 2098
> cyberpunk premise is discarded in full.
>
> Sections marked **Open** are genuinely undecided, not omissions. Sections
> marked **Under reconsideration** are ideas from the previous version that
> are neither confirmed nor dropped yet.

---

## Overview

**A gritty, noir third-person action shooter set in the Philippines, 2002.**

The narrative is heavy noir: dark, brooding, cynical, crime-focused, built
on morally compromised institutions and a protagonist who is rarely sure
who to trust. The action is John Woo — heroic bloodshed, extravagant and
stylish, kinetic gunfights that escalate into large set-piece shootouts.
Those two things live together on purpose: **the story stays grim while the
combat is deliberately extravagant.**

The identity is Filipino. Classic Filipino crime and action cinema — the FPJ,
Rudy Fernandez, Lito Lapid, Phillip Salvador tradition — informs the
attitude, locations, villains, firearms and larger-than-life action, rather
than the game leaning only on Hong Kong or American references.

The explicit goal is **not** "Max Payne in the Philippines." Max Payne and
John Woo are useful reference points for translating noir and cinematic
gunplay into a shooter; the game develops its own Filipino crime-noir
identity from there.

### The three pillars

**Grim story, extravagant action.** The narrative is dark and grounded; the
gunfights are stylised and spectacular. Neither is toned down to meet the
other.

**Filipino crime-noir, not a transplant.** The setting, the villains, the
weapons, the locations and the attitude come from the Philippines and its
own cinema. Hong Kong and American references are tools, not the template.

**Overlapping interests, not one conspiracy.** The corruption the story
exposes is a web of favours, protection arrangements, debts and people
taking their cut — criminals, police, businessmen, fixers and politicians
each pursuing their own interest. Not a single centralised villain behind
everything.

### Fidelity target: fun over fidelity

The visual bar is **early-2000s, Halo 1–2 era** — a deliberate choice that
happens to sit naturally alongside a 2002 setting. Lighting is baked rather
than simulated in real time, with dynamic lights kept to a minimum.

It buys performance headroom, which for a game built on large escalating
shootouts converts directly into more enemies on screen and a steadier frame
rate. It suits the material — fluorescent interiors, wet concrete and neon
read on strong shapes and colour rather than surface detail. And it keeps
scope honest for a project whose bottleneck is combat and story, not
rendering.

The test for any visual work is whether it makes the game more fun to play,
not whether it looks more expensive.

---

## Combat

### Action direction

The primary inspiration is John Woo's heroic-bloodshed films — Hard Boiled,
The Killer, A Better Tomorrow. The action language the game is reaching for:

- Extremely kinetic gunfights
- Dual-wielded firearms
- Diving or sliding gunfire
- Slow motion / bullet-time-style mechanics, if appropriate
- Destructible-feeling environments — shattered glass, debris, sparks,
  furniture, environmental chaos
- Dramatic standoffs
- Large, escalating shootouts
- Close-range pistol combat
- Stylised cinematic violence
- **Strong choreography and movement rather than static cover shooting**

That last point is the organising principle. The player is meant to be
moving through a fight, not hiding from it.

Crouching follows from that. It's a momentary stance for ducking behind
something or reloading under cover — the character only crouches while
standing still, and the moment the player moves they're up and moving again.
There's no crouch-walking.

The character moves with weight. Movement is deliberately paced slower than
stock animation, with longer strides — closer to Max Payne than to an arcade
shooter — so constant motion reads as purposeful rather than frantic.

### Under reconsideration

The previous version of the game built its combat on a specific accuracy
model — no bonus for aiming down sights, hip-fire fully effective, accuracy
governed by how you pace your trigger rather than by a recoil pattern, with
the crosshair widening as you fire and tightening as you stop. That model is
built and working today — though the crosshair itself is now a simple dot,
so the widening is no longer shown on screen.

It is neither confirmed nor dropped for the new game. It's being reconsidered
against the John Woo direction — and it's worth noting that "hip-fire is the
default, movement over cover" is a natural fit for heroic bloodshed. But that
is a decision for design to make, not an assumption to carry forward.

### Open

- Dual-wielding is in (dual pistols, firing alternately — see Weapons). Which
  of dive/slide gunfire and slow motion make it in, and in what form, is still
  open.
- How "destructible-feeling" is delivered — cosmetic chaos versus mechanical
  destruction.
- Whether the existing accuracy model stays, changes, or goes.

---

## Weapons

### Direction

Firearms of the period, drawn from Filipino action cinema as much as from
Hong Kong or Hollywood. The direction names **close-range pistol combat**
and **dual-wielded firearms** specifically, which makes handguns the centre
of the arsenal rather than one option among many.

### What exists today

Three weapons are built and working as a test bed — a semi-automatic pistol,
a full-automatic close-range rifle, and a semi-automatic scoped rifle — with
distinct handling, ammunition and reloading. Their
current art is placeholder sci-fi and will be replaced. Their *roles* were
designed for the previous premise and are open to revision.

Two more now exist alongside them: **shotguns** — a semi-automatic one with
fast follow-up shots and a pump-action one, both loaded a couple of shells at a
time. In the spirit of DOOM's shotgun, they still hit at a distance; the price
is a very slow reload — and **dual pistols**. Dual pistols fire left, right, left, right with each trigger
pull, and both guns reload together. The character carries them very
differently from a single gun: arms down and loose at the sides when not
fighting, both guns up and pointed when shooting — spread wide apart when
firing on the move, drawn in tighter when taking careful aim. Dual submachine
guns are planned to be carried the same way.

Every gun fires real bullets that travel through the world. At normal speed
you don't see them; slow motion is where the rounds become visible in the air.

A single pistol is fired **one-handed**, the free hand hanging at the side;
the two-handed grip is saved for the heavier, high-powered pistol. Every shot
kicks visibly through the arm and shoulders, and rapid fire stacks the kick
rather than smoothing it away.

The previous version also had one weapon fire a visible, dodgeable
projectile, justified by future-tech physics. That justification is gone
with the setting. The projectile system itself is built and working and is
a natural fit for things like grenades or thrown weapons — but nothing in
the new direction has claimed it yet.

### Under reconsideration

Weapons encouraging playstyles rather than levels forcing them; a favourite
general-purpose weapon staying viable across most of the game; ammo as a
*soft* pressure that nudges you toward switching rather than stranding you.

### Open

- The actual weapon roster.
- How many weapons are carried at once.
- ~~Whether and how dual-wielding works mechanically.~~ Decided: dual pistols
  fire alternately and reload like any weapon (rather than being thrown away
  when empty). Whether other weapons, such as small submachine guns, can also
  be dual-wielded is open.
- What, if anything, uses the projectile system.

---

## Enemies

The enemies are people. Criminals, syndicate muscle, corrupt police,
private security, hired killers — the human fabric of a 2002 crime world.

That world, as the direction sketches it: kidnapping-for-ransom syndicates,
jueteng and illegal gambling networks tied to officials and law enforcement,
shabu trafficking and the wider drug trade, organised crime, vigilantism and
extrajudicial violence, and the post-EDSA political instability that sits
underneath all of it.

These are possible ingredients rather than a required roster — the game
doesn't need to reproduce specific real cases.

### Under reconsideration

The previous version's rule that enemies must **read at a glance** — distinct
silhouettes, behaviours and battlefield roles so the player can size up a
fight instantly. The synthetic premise it was written for is gone, but the
principle applies just as well to a syndicate enforcer versus a beat cop
versus a hired shooter.

### Open

- The enemy roster and how factions differ in play.
- Whether readability-at-a-glance stays a design requirement.

---

## World

### The Philippines, 2002

Not a stylised past — the real social, political, criminal and technological
atmosphere of the early-2000s Philippines. Real historical conditions form
the backdrop; the main plot stays fictional, so the game never has to rewrite
major events.

### Period texture

Nokia-era mobile phones and SMS culture, and everything that implies:
pre-smartphone communication, limited mobile internet, text messaging as a
tool for politics, rumours, threats, informants and criminal business.

CRT televisions and monitors. Jeepneys, buses, taxis, motorcycles and period
cars. Early-2000s Manila nightlife. Fluorescent interiors, concrete urban
spaces, rain and humid streets.

Karaoke bars, restaurants, hotels, warehouses, docks, police stations,
government offices, dense residential districts. Catholic imagery and other
distinctly Filipino environmental and cultural detail. Tabloids, radio and
television news. Political uncertainty and rumour. A mix of English and
Filipino/Tagalog where appropriate.

### The backdrop

Political instability after EDSA II and EDSA III. Public distrust of
politicians and institutions. Corruption and patronage networks. Police
corruption and criminal links. Military dissatisfaction and rumours of coup
plotting. Post-9/11 security anxiety, terrorism and insurgency in the
national atmosphere.

This is atmosphere and raw material, not a checklist the story must tick.

### Cinema references

For action language: John Woo — Hard Boiled, The Killer, A Better Tomorrow.
Max Payne, as a reference for translating noir and cinematic gunplay into a
shooter, not as a setting to copy.

For the Filipino identity: *On the Job* (crime, assassins, police, political
corruption, overlapping institutions), *BuyBust* (claustrophobic urban
combat in dense Filipino environments), *Metro Manila* (desperation, class,
crime, Manila), *Manila in the Claws of Light* (distinctly Filipino urban
darkness and noir foundations), and classic Filipino action cinema.

---

## Narrative

### Tone

Heavy noir. Dark, brooding, cynical, crime-focused. Morally compromised
institutions; betrayal, corruption and conflicting loyalties. The
protagonist is frequently unsure who can be trusted.

The story exposes **systems** of corruption rather than presenting good
against evil. The most believable version is an apparently ordinary crime —
a kidnapping, a murder, an organised-crime case — that gradually reveals
overlapping networks of criminals, police, businessmen, fixers and
politicians. Not one giant conspiracy: overlapping interests, favours,
protection arrangements, debts, and people taking their cut.

Humour can exist, but the lead is deliberately **not** Tequila from Hard
Boiled — no cheerful, cool swagger.

### The protagonist

A defined, authored character — the previous version's player-projection
protagonist is discarded.

Male, at least 35, preferably late 30s to early 40s. Dark, brooding, cynical.
Tired and experienced. Observant, suspicious, restrained. Dry or fatalistic
humour rather than playful banter.

Not a one-note angry tough guy: his darkness shows as quiet exhaustion,
distrust and resignation rather than shouting. He should keep some buried
moral line so the cynicism never becomes total nihilism — he expects
institutions and people to fail him, and still can't ignore innocent people
in danger.

### Open

- **The story.** This is the current major design task: a plot that grows
  from the older cynical protagonist, Philippine crime-noir conditions,
  overlapping criminal and institutional interests, a personal reason for
  him to keep digging, and a structure that naturally escalates into
  spectacular John Woo-style encounters.
- **The protagonist's** history, profession, name, exact age, personal
  tragedy or motivation, and his connection to the main crime plot.
- Whether dialogue choices exist. The previous version had none, tied to
  the neutral protagonist; with an authored lead, that's no longer settled
  either way.

---

## Scope

### Under reconsideration

The previous version's structure: a **linear campaign of at least ten
levels**, built on a repeating and escalating loop of encounter → sequence
→ level → campaign, with **linear navigation and nonlinear combat** —
mini-sandbox arenas where freedom comes from how you use the geometry rather
than from branching routes.

None of that is discarded. None of it is confirmed. Each piece gets weighed
against what a noir story and John Woo action actually need.

### Deliberately open

- **Vehicles** — never guaranteed, still not.
- **Mission count and campaign shape** — depends on the story, which doesn't
  exist yet.

### Where the build is

The combat foundation is real and playable, now in third person — an
over-the-shoulder camera that moves in closer when aiming, and a fully animated
character. Working today:

- A character who carries his weapon lowered and raises it to fire, strafes
  while shooting, turns on the spot to follow the aim, and crouches into cover
  when standing still
- Weapons that fire, with an accuracy model that loosens under sustained fire
- Configured test-bed weapons with distinct handling, plus a shotgun and dual
  pistols
- A one-handed pistol stance, a heavier walking gait, and a visible kick on
  every shot
- A working projectile weapon with fragmenting impact
- Fire rate limits, full-automatic fire, per-weapon fire animation
- Scoped zoom
- Ammunition with magazines, reserves and reloading
- A composable HUD — reticle and ammo readout as separate, mix-and-match
  elements
- A minimal dot crosshair
- Hit decals, muzzle flash, weapon sound

All of it was built under the old premise, and all of it is **implementation
state rather than canon** — the test bed the new direction gets evaluated
against. The systems are setting-agnostic; the art and the roles they were
tuned for are not.

Next: the story. Then enemies — which is when this becomes a game rather than
a shooting range.

---

## Document map

| Document | Purpose | Owner |
|---|---|---|
| **GameDesignDocument.md** | What the game is. Pitch-facing, non-technical. | Design |
| **Lore_And_Design_Notes.md** | Narrative and world canon. | Design |
| **TechnicalDesignSpec.md** | What the design asks of the codebase. | Implementation |
| **ProjectPlan.md** | Ordered build sequence. | Implementation |
| **ProgressLog.md** | Dated session history and decisions. | Implementation |

---

## Changelog

- 2026-08-09 — Initial skeleton created.
- 2026-08-09 — Rewritten against locked canon from `Lore_And_Design_Notes.md`.
- 2026-08-12 — Enemies deferred behind a weapon-focused phase.
- 2026-08-17 — Projectile-weapon assignment reversed to the close-range rifle.
- 2026-08-30 — First-person rig restructured; first weapon tuning pass.
- 2026-08-31 — **Rewritten as a non-technical pitch document.** Implementation
  detail moved to `TechnicalDesignSpec.md`. Fidelity target recorded.
- 2026-09-13 — **Rewritten for the change of setting: Philippines 2002,
  noir narrative, John Woo action, authored protagonist.** The 2098 cyberpunk
  premise, synthetic enemies and neutral protagonist are discarded. Previous
  gameplay ideas are marked *under reconsideration* rather than removed, per
  the new direction. Fidelity target retained — it sits naturally with a
  2002 setting.
- 2026-10-05 — **Now a third-person game.** Overview and "Where the build is"
  updated: over-the-shoulder camera, animated character, crouch as momentary
  cover.
- 2026-10-06 — Shotguns: semi-auto and pump-action variants, range with a slow
  reload as the drawback.
- 2026-10-07 — Single pistol fired one-handed (two-handed kept for the
  high-powered pistol); heavier, slower gait; visible recoil on every shot.
  Dual pistols spread apart when firing on the move, tighter when aiming; dual
  SMGs planned the same way. Crosshair simplified to a dot.
- 2026-10-08 — All guns to fire real, travelling bullets, visible only in slow
  motion.
