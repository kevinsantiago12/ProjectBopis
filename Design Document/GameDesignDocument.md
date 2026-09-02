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
> Sections marked **Open** are genuinely undecided, not omissions.

---

## Overview

**A first-person shooter set in the Philippines, 2098.** Hostile synthetics
have turned on the country that built them. You have a gun.

The combat touchstone is Bungie-era Halo — the original trilogy, ODST, and
Reach. That is a deliberate, narrow reference, and it settles a lot of
questions before they're asked: fights are won by where you stand and how you
pace your trigger, not by holding a scope steady or memorising a recoil
pattern. No bullet-sponge enemies. No aim-down-sights bonus. A weapon you like
should stay useful for most of the campaign.

The setting is the part nobody else is making. Not "generic cyberpunk city with
Filipino signage" — a Philippines that is recognisably descended from the real
one, where modern and historical Filipino culture, languages, institutions,
architecture, religion and social structures visibly survive, transformed by
decades of technology and money.

### The three pillars

**Trigger discipline over twitch aim.** The core skill is firing as fast as
you can while keeping your accuracy suitable for the distance you're fighting
at. It's readable in the moment, it carries across every weapon in the game,
and it makes picking up an unfamiliar gun feel immediately usable.

**Linear navigation, nonlinear combat.** You go one way through the level.
Once you're in a fight, the space supports many approaches — not because
there are separate routes for separate playstyles, but because the geometry
itself rewards different weapons in different ways.

**The world is specific.** Every part of the setting should be somewhere you
couldn't set another game without changing it.

---

## Combat

### Accuracy comes from pacing, not from aiming

Most shooters handle gun accuracy one of three ways: aiming down sights makes
you accurate, the gun kicks in a pattern you fight, or the gun loses accuracy
the faster you fire and recovers when you ease off. That third one — Halo:
Reach called it **bloom** — is the model here, and the other two are ruled out
on purpose.

**Aiming for accuracy** rewards standing still and posting up, which fights
against a game that wants you moving, strafing and using cover creatively.

**A recoil pattern** turns skill into memorising how one specific gun kicks,
practised outside the fight. That suits some games; it doesn't suit fast,
improvised firefights meant to be won by reading the room.

**Bloom** ties accuracy to pacing, and you can read it in the moment by looking
at your crosshair — do I have time for another shot, or should I ease off?

The rule, stated plainly: **aiming changes what you see, never how accurate you
are.** Your crosshair widens as you fire and tightens as you stop. A first shot
from rest always goes exactly where you point it.

### Hip-fire is the default, not a penalty

You fight normally while moving, strafing, switching targets and meleeing.
There is no arbitrary hip-fire accuracy penalty. Aiming is available and does
something useful — it's targeting information and precision placement, and it
may change your reticle — but it does not make the gun shoot straighter.

**Zoom is a separate thing from aiming**, restricted to weapons that earn it.
It improves visibility and target acquisition. It does not improve accuracy.
When a scoped weapon zooms, the view magnifies cleanly and the weapon leaves
the screen — the Halo approach, rather than an over-the-shoulder sight picture.

### What this means at higher difficulty

Harder settings demand better positioning, target prioritisation, accuracy
management, ammo management, weapon knowledge and use of the arena — not a
single correct solution to each room.

---

## Weapons

Weapons encourage playstyles. Levels never hard-force a weapon type. The goal
is *"this weapon gives you another good way to solve this"*, never *"this room
requires this exact gun."*

Ammo availability is a **soft** pressure. Running low nudges you toward
switching or picking something up; it doesn't strand you.

### The starting three

**Pistol** — a precise semi-automatic sidearm. Reliable at range if you pace
your shots, punished if you spam them.

**Close-range rifle** — full-automatic, built for corners and short sightlines.
The one weapon that fires a *real projectile* rather than an instant hit.

**Battle rifle** — mid-range, semi-automatic, deliberate. The scoped weapon,
and the one most likely to become a player's favourite for a long stretch of
the campaign.

### Why one gun fires a real projectile

A travel-time projectile is only interesting if you can see it coming and
dodge it — and that only matters at **close range**, where an enemy would
otherwise have no reaction window at all against an instant hit. At the battle
rifle's engagement distance, visible travel time would just read as an aiming
penalty rather than a test of anyone's reflexes.

The in-world reason is electromagnetic, not exotic. These are coilguns: they
accelerate a solid slug through a sequence of magnetic stages, so muzzle
velocity scales with how much barrel you have. A compact close-range weapon
doesn't have room for enough stages to reach the speeds a longer weapon
manages. Short gun, slow round. Long gun, fast round. That rule holds if more
weapons get added later.

To stop "slow" reading as "weak", the close-range round is pre-scored to
fragment on impact — it trades penetration for a burst of shrapnel. Strongest
against close, grouped or exposed targets; weakest against armour and hard
cover, which is exactly where the other two stay relevant.

### Open

- **How many weapons you carry at once.** Two is the classic Halo answer.
  Not locked.
- **The full weapon roster** beyond these three.

---

## Enemies

The enemies are machines. Not people.

"AI" is the intelligence; **synthetics** are the physical force you fight —
machine bodies controlled or inhabited by it. Humans remain in the story as
corrupt, antagonistic, manipulative or simply responsible for dangerous
technology, but they are not what you shoot.

### Readability is the design requirement

You should be able to tell what you're dealing with instantly, the way you can
immediately clock an Elite from a Grunt in Halo. That instant read doesn't come
from one enemy reskinned several ways — a hovering drone and a four-legged war
machine shouldn't move or behave the same underneath.

So enemies are built from interchangeable pieces — how they move, how they
attack, what role they play in a fight — mixed and matched per type. Distinct
silhouettes, distinct behaviours, distinct battlefield roles.

Possible chassis: humanoid infantry, quadrupeds, hovering units, repurposed
industrial machines, swarms, heavily armoured elites, enormous combat
platforms.

### Open

- **Why the synthetics turned hostile.** Deliberately unresolved, and
  deliberately *not* the default "AI wakes up and decides humanity must die" —
  the cause should be specific to this world's history.
- **The synthetic hierarchy** — what ranks and roles exist.

---

## World

### The Philippines, 2098

The country spotted an opportunity. As the rest of the world responded to the
harms of frontier AI research with restrictions — while cheerfully continuing
to *buy* AI-derived products — the Philippines made itself the place where the
restricted work could legally happen.

The result is a genuine contradiction rather than a simple dystopia. Foreign
money poured in. So did infrastructure, tech transfer, industry and
corruption. Decades of real economic growth followed: modernised
infrastructure, a serious domestic robotics and defence industry, globally
important universities, powerful Filipino tech companies, engineers moving
*in* rather than out.

And the Filipino counter-argument is a good one: wealthy nations benefited
from this technology and then tried to pull the ladder up. By 2098 the AI
economy is too important to the world to simply switch off.

### Corporate espionage as a world engine

Because so many competing international research operations sit physically
close together, espionage is constant — poaching, prototype theft, sabotage,
convenient facility fires, infiltration, bribery, reverse engineering.

This matters beyond flavour: it explains why 2098 synthetics are so
sophisticated, and why **no single corporation fully understands or controls
the ecosystem**. One company's locomotion, another's stolen cognition, a
third's theft of that, all reverse-engineered locally. Eventually nobody can
say who invented what.

### Luzon — "The Factory"

A vast continuous sprawl, far bigger than Manila. Flatlands converted to solar
farms feeding compute. Between them: data centres, automated factories,
synthetic assembly plants, worker cities, cooling infrastructure, corporate
research campuses.

Old Philippine towns survive embedded inside it. The visual thesis is
contrast — a centuries-old church, an ordinary neighbourhood, sari-sari
commerce, a barangay basketball court, sitting beneath enormous futuristic
industrial infrastructure.

### High City and Low City

Not one Midgar-style plate, but the accumulated result of decades of building
over what was already there — new roads over old roads, rail over roads,
corporate districts spanning older ones, decks connecting towers.

**High City** is clean, orderly, maintained, spacious and sunlit. Glass,
composite, landscaping, automated transit, restrained high-tech. The future
visibly *works* here. The darkness is beneath the surface: surveillance,
sensors, private security, synthetic labour, biometric access, corporate
ownership.

**Low City** is the original ground-level Philippines, buried underneath.
Dense old concrete, endless modification, exposed cabling, cheap holographic
advertising, wet streets, food stalls, repair shops, synthetic chop shops.
Large parts get little direct sunlight because High City has the sky — which
gives the neon an environmental reason rather than a stylistic one.

Crucially, **Low City is not uniformly poor.** It holds poor communities, an
established middle class, commercial districts, old wealthy enclaves,
industrial businesses, and people who simply refused to leave. High City is
planned and corporate; Low City is chaotic and culturally alive. Both stay
recognisably Filipino — neither is Tokyo, neither is Night City.

### Visayas — "The Resort"

The counterpart to Luzon's industry: the entire region reshaped around
leisure and tourism. Luxury destinations, nightlife, artificial reefs, medical
tourism, corporate retreats, floating hotels, entertainment districts.

Millions still live there — it isn't emptied — but the economy and land use
are built around visitors, wealthy residents and international consumption.
The available contrast: immaculate resort districts supported by worker
communities deliberately kept out of sight.

### Open

- **Mindanao.** Left undefined on purpose rather than forced into a trio.
- **The major corporations, families and factions.**
- **The exact regulatory mechanism** the Philippines used.

---

## Narrative

### The protagonist is the player

There is no strongly authored personality. The protagonist may have a
functional identity — why they're there, what they can do, what they carry —
but the game never states what they think or believe.

**No dialogue choices.** Not a technical shortcut; a deliberate position on
whose viewpoint the story belongs to.

### Viewpoints come from everyone else

Supporting characters carry the opinions, and they're allowed to be
interesting: they disagree, they argue about corporations and AI and politics,
they lie, they misunderstand, they hold biases, and they can be sincere and
wrong at the same time.

The protagonist never declares which of them is correct. The player decides.

### Lore serves the shooter

The immediate premise has to land in one sentence: **hostile synthetics, here's
a gun.** Everything deeper — the history, the politics, the competing
interpretations of how the country got here — arrives through supporting
characters, environments, background detail, optional lore, and corporate and
government messaging.

The world contains contradictions on purpose. Governments condemn frontier AI
while importing its products. Foreign critics are economically dependent on
Philippine technology. Corrupt officials take corporate money, and the
resulting boom genuinely improves the country. High City offers a real
standard of living and embodies corporate surveillance. Low City suffers
neglect and is where the culture lives.

**The FPS comes first.**

### Open

- **The inciting incident.**
- **The protagonist's role, background and designation.**

---

## Scope

### Campaign shape

A **linear campaign, minimum ten levels**, built around a repeating and
escalating loop:

> 30 seconds of fun → a combat encounter → an encounter sequence → a level →
> the campaign

Core guaranteed gameplay is on-foot first-person combat. Everything else has
to earn its place.

### Arenas

Navigation is linear; arenas are mini-sandboxes. This explicitly **does not**
mean branching routes — there is no separate sniper path or stealth path.
Everyone fights through the same space.

Freedom comes from how you use the geometry. A battle-rifle player exploits a
long central hallway; a close-range player exploits the short-sightline
corners beside it. Same room, different tactics.

The test for a good arena: **it stays fun with a different loadout.**

### Deliberately out of scope

**Vehicles** are not guaranteed. Nothing is designed around them unless they're
added later and proven fun.

**Branching conversation** doesn't exist, because dialogue choices don't.

**Third-person and co-op** are not being built toward. Body animation for how
other players would see you is deferred until there's an actual reason.

### Where the build is

The combat foundation is real and playable, not planned. Working today:

- Weapons that fire, with the full bloom accuracy model driving both the shot
  and the reticle
- Three configured weapons — pistol, close-range rifle, battle rifle — with
  distinct roles and tuning
- A real projectile weapon with fragmenting impact
- Fire rate limits, full-automatic fire, and per-weapon fire animation
- Halo-style scoped zoom
- Ammunition with magazines, reserves and reloading
- Hit decals, muzzle flash, weapon sound

Next: enemies. That's the milestone where the combat loop becomes a *game*
rather than a shooting range — everything above currently has nothing to shoot
at.

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
- 2026-08-09 — Reworded as an original implementation-design document.
- 2026-08-09 — Restructured to separate plain-English explanations from
  technical jargon.
- 2026-08-12 — Enemies deferred behind a weapon-focused phase; backlog
  superseded by `ProjectPlan.md`.
- 2026-08-17 — Projectile-weapon assignment reversed to the close-range rifle;
  coilgun and fragmentation rationale added.
- 2026-08-18 — Animation-feedback ownership principle established.
- 2026-08-30 — First-person rig restructured; render-proxy rule documented;
  first weapon tuning pass recorded.
- 2026-08-31 — **Rewritten as a non-technical pitch document.** All
  implementation detail moved to
  [Documentation/TechnicalDesignSpec.md](../Documentation/TechnicalDesignSpec.md).
  Restructured into Overview / Combat / Weapons / Enemies / World / Narrative /
  Scope, with undecided items marked **Open** rather than silently omitted.
