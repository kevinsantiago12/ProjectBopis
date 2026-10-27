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

The visual bar is **the Xbox 360 era — Max Payne 3** — raised from an
earlier early-2000s bar to match the art the game now uses. Lighting leans
baked, with real-time lights used where they earn their place, decided scene
by scene. It runs at **60 frames per second on a Steam Deck** at its native
resolution and high settings, and at 1080p on a modest gaming PC; lower
settings stretch it to older PCs.

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

### Shooting

Shooting feels like Max Payne 1 and 2. Hold the trigger and a gun keeps
firing at its own steady pace — pistols, duals and shotguns included — and
the guns are accurate: a bullet goes close to where you point. Running costs a
little accuracy, a dive costs none, and long bursts from automatic weapons
wander a little. Aiming brings the camera in but doesn't make you more
accurate; firing from the hip is fully effective. The skill is in moving,
diving and using slow motion, not in pacing the trigger.

Enemies fire each weapon its own way: short bursts from fast weapons, steady
single shots from the rest. Tougher enemies later fire longer bursts with
shorter pauses.

*Replaced (2026-10-15):* the previous accuracy model, where accuracy
loosened as you fired and the skill was pacing your trigger, came from the
game's earlier first-person design.

### Moves

- Dual-wielding is in (dual pistols, firing alternately — see Weapons), and so
  is slow motion (Focus). The **shootdodge** is playable with every gun type: a dive in any
  direction, the world slowing as you leave the ground, guns blazing, sliding
  to a stop on the floor where you keep firing — and reloading — until you
  choose to get up. Each dive costs Focus. The price is getting up: you can't
  shoot while scrambling to your feet.
- A **dodge roll** on its own key: a quick roll in any direction that enemies
  struggle to hit, with a moment of free slow motion partway through to line
  up the shots for coming out of it. You can't shoot mid-roll, but you can run
  straight out of the end of it.
- **The kneel**, borrowed from Vanquish: keep the roll button held and the
  roll ends in a crouch, firing from the knee for as long as you hold it.
- Dives and rolls stay hard to hit for a couple of seconds after you land.
- An empty gun reloads by itself, and reloading ends slow motion.

### Open

- How "destructible-feeling" is delivered — cosmetic chaos versus mechanical
  destruction.

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
is a very slow reload — and **dual pistols**. Dual pistols fire left, right, left, right for as long as
the trigger is held, and both guns reload together. The character carries them very
differently from a single gun: arms down and loose at the sides when not
fighting, both guns up and pointed when shooting — spread wide apart when
firing on the move, drawn in tighter when taking careful aim. Dual submachine
guns are planned to be carried the same way.

You keep every gun you find. Ammunition is shared by calibre, so the guns that
use the same rounds draw on one supply. A number key brings up a **weapon
wheel** — one slot per kind of gun — with that kind picked; the same key again
steps through the guns of that kind, and a click takes the one shown. The world
slows while the wheel is up, and you can keep moving. On a controller you hold
a button and point at a slot.
Weapons found on the ground give their ammunition if you already have that gun.
A second pistol puts a dual pair in your hands as its own selection, alongside
the single one. Drawing a gun takes a moment — you can't fire until it's up —
so switching weapons is a small commitment in a fight.

Every gun fires real bullets that travel through the world. At normal speed
you don't see them; slow motion is where the rounds become visible in the air.

**Focus** (the game's slow motion) is a toggle. The whole world — the hero included — drops to a crawl
while your aim stays quick, so you can place shots a normal-speed fight would
never allow. It runs on a meter that drains while it's on and refills as you
kill.

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

### How levels play

The game is **linear**, not built from open arenas. You move forward through
places, and the fights happen in **rooms set up as encounters**: a handful of
enemies waiting inside, holding their ground. You burst in and use everything
you have — the dive, the roll, slow motion — to take them all down. They react
when they see or hear you, or the moment you step into the room, with a beat
of surprise before they open fire.

### Under reconsideration

The previous version's structure: a **linear campaign of at least ten
levels**, built on a repeating and escalating loop of encounter → sequence
→ level → campaign, with **linear navigation and nonlinear combat** —
mini-sandbox arenas where freedom comes from how you use the geometry rather
than from branching routes. *(The arenas are settled — see above: linear, room by
room.)*

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
- Weapons that keep firing while the trigger is held, each at its own pace and
  accuracy (Max Payne 1 and 2 as the model)
- A dodge roll that can end in a kneel, and a shootdodge you can reload in
  while lying on the floor
- Configured test-bed weapons with distinct handling, plus a shotgun and dual
  pistols
- A one-handed pistol stance, a heavier walking gait, and a visible kick on
  every shot
- A working projectile weapon with fragmenting impact
- Per-weapon fire rates and fire animation
- Scoped zoom
- Ammunition with magazines, a shared supply per calibre, and reloading
- Weapon and ammunition pickups, an unlimited weapon backpack, number-key weapon
  selection
- A composable HUD — reticle and ammo readout as separate, mix-and-match
  elements
- A minimal dot crosshair
- A first test enemy that carries a gun, patrols, and turns to keep the player in
  its sights, moving with the same animation as the hero
- Deaths staged like the films: a death fall, a body that stays on its feet
  jerking under sustained fire, then flies off the final bullets; a big enough
  blast throws it at once
- Enemies that flinch at every hit, and reel helplessly under concentrated fire —
  pin one down and you can keep it staggering, while the rest keep shooting
- The dead drop their guns, which clatter to the floor and can be picked up for
  the weapon or its ammunition
- Bullet impacts that match what was hit — dust, sparks, splinters and bullet
  holes, and blood on people — each with its own sound; a headshot sounds
  different. Muzzle flash, weapon sound
- Scripted moments: enemies you overhear talking before they know you are
  there — they speak, gesture, walk and turn to each other, and either play
  the scene out or break off the moment they spot you; a scene can also start
  the fight on a line of dialogue
- Enemies that call out in a fight — spotting you, reloading, hurt, a friend
  down, a grenade at their feet — kept from talking over each other, with
  room for a Tagalog voice set alongside the English placeholders
- Rounds that miss you crack past your head, from the side they passed on
- Gunshots that carry and fade with distance; reloads and drawing a gun have
  their own sounds
- Footsteps that sound like the floor, and a thud when you land a dive, a roll
  or a fall
- The body leans into turns when running or walking; slow motion can be cut
  short mid-dive
- A weapon wheel for picking guns, with the world slowed while it's open
- People built from a character creator — varied Filipino faces, skin tones,
  hair and clothing, men and women — plus a creator for authoring the look
  of named characters. Women are planned as civilians and one story character
- Enemy voices that differ from man to man even when they share a set of lines
- Enemies who hold their fire rather than shoot through a friend in the way
- Music that sets the mood and changes as you move through a level, unaffected
  by slow motion
- Rooms that send in reinforcements in waves as a fight thins out
- A level ending: the screen fades out and the next level begins

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
  motion. Weapon and ammo pickups: carry everything, shared ammo per calibre,
  number keys by category, a second pistol unlocks duals. Drawing a gun
  animates and briefly blocks firing.
- 2026-10-09 — Focus (slow motion; not called "bullet time", a trademarked name): a toggle slowing the whole world (the hero too, aim
  stays quick), on a meter refilled by kills.
- 2026-10-14 — Player moves: a dodge roll with a moment of slow motion, the
  kneel (hold the roll button), evasion that lingers after a dive or roll,
  automatic reloads, reloading on the floor after a dive.
- 2026-10-15 — **Shooting reworked to feel like Max Payne 1 and 2:** every gun
  fires while the trigger is held, guns are accurate, running costs a little
  accuracy; enemies fire each weapon its own way. The earlier
  trigger-pacing accuracy model is retired.
- 2026-10-16 — The game is linear, with fights set up as room encounters
  (enemies waiting in rooms, set off when you enter). Hit indicators and shell
  casings added to the build.
- 2026-10-21 — Overheard enemy conversations (scripted scenes that can break
  off or start the fight) and enemy combat call-outs added to the build.
- 2026-10-24 — Weapon wheel; bullet, near-miss, footstep and landing sounds;
  blood on hits; people from a character creator, men and women (women planned
  as civilians and one story character); enemy voices that vary; enemies hold
  fire for their friends.
- 2026-10-25 — Music that changes through a level; reinforcements in waves; a
  level ending.
- 2026-10-26 — The first final gun models: a Mossberg pump shotgun, an M4
  rifle, Beretta 9mm pistols and 1911 .45 pistols. Guns move as they fire (slides, pumps), spent
  magazines drop to the floor on reloads, and hands hold each gun the way it's
  built. The number keys now run pistols, shotguns, SMGs, rifles and sniper
  rifles; the grenade launcher is set aside for now.
- 2026-10-27 — The visual target is raised to the Xbox 360 era (Max Payne 3),
  running at 60 frames per second on the Steam Deck. Planned: calmer
  walk-around stretches with civilians to interact with; fights stay at about
  six enemies at a time.
