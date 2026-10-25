# Phase 6 — Graybox slice brief (draft, 2026-10-19)

> **2026-10-23:** to-scale blockout plan of these six beats in
> [Phase6_SliceLayout.html](Phase6_SliceLayout.html) (top-down plan, room 4/5
> sections, escalation chart). Still a draft for the user to cut.
> The same layout dressed for the settled setting, **Filipino slum alleyways**
> (user, 2026-10-23), is in
> [Design Document/Phase6_SliceLayout_Alleys.html](../Design%20Document/Phase6_SliceLayout_Alleys.html):
> eskinita, wash yard, covered alley, half-court, row-house yard, shanty stack.

Draft for the user to cut, reorder or replace. Gameplay layout only: the
slice's location, story beat and enemy identity are design-owned and left
open (see *Not decided here*).

## What the slice has to prove
One short, linear run of rooms in `Lvl_Linear` that plays like the game:
burst into a room, clear it with the moves, move on. It should answer:

1. **Does each room reward moving instead of camping?** (dive through the
   door, roll to a new angle, slow motion as the room-clearing tool).
2. **Does the same room work close and far?** A pistol rush and a rifle
   pick-off should both be possible, neither forced.
3. **Do the fights escalate** across the run (count, weapons, layout), so the
   last room feels like a shootout, not a repeat of the first?
4. **Does ammo stay a soft pressure?** You can keep a favourite gun going if
   you pick up what's dropped, but you're nudged to swap.
5. **Do explosives earn their place** without being the answer to every room?

## Rules it follows (settled design)
- **Linear, room encounters** (lore *Linear levels*, 2026-10-16): 3–4 enemies
  waiting per room, holding their ground, set off by being seen or heard, or by
  the player entering; a brief reaction beat. Out of sight they cover the room
  rather than hunt. Some wait crouched. **No cover-popping** ("no whack-a-mole").
- **Weapons don't get forced** by the level; ammo is a soft pressure.
- **Max Payne shooting model:** hip-fire fully effective; cover is something
  to dive past and break line of sight with, not to hide behind and peek.

## Toolbox (already built)
| Need | What exists |
|---|---|
| Room enemies | `BP_EnemyBase` with `bHoldsPosition` + `HoldRadius`, `bCrouchWhileHolding`, reaction beat, lowered search after 4 s out of sight, 2 s suppression only after a real sighting |
| Room start | `AEncounterTrigger` (volume + list of enemies, `bTriggerOnce`) |
| Waves | `AEncounterDirector` (`MaxAlive`, `TotalEnemies`, spawn points out of view, weapon pool, spawn alerted) |
| Enemy weapons | pistol, MAC-11 single/dual, rifles, shotguns (per-weapon burst patterns) |
| Player | dive, roll, Focus, quick throw, slots 2–6 (pistols/revolver, shotguns, SMG/rifle, sniper, launcher) |
| Pickups | weapon pickups (random/fixed rounds, unlocks duals), ammo per type, grenades (1), launcher rounds (3) |
| Dying | death slow motion, then the level restarts |

## Proposed run: six beats, about 5–8 minutes
Sizes are starting points in metres, to change once played. Doorways at least
**2 m wide**, ceilings at least **3.5 m** (dive camera), so a dive through a
door never clips.

**0. Entry corridor** (~4 × 20 m, no enemies)
Start with the pistol only. A pistol ammo box and one weapon pickup (the
duals, by picking up a second pistol). Room to try the dive and roll before
anyone shoots. Ends at a closed or narrow door into room 1.

**1. First room — "the burst"** (~10 × 12 m, 3 enemies, pistols)
The trigger is the doorway. Two standing, one crouched behind a low table.
A wide doorway invites a dive straight in. Tests the reaction beat, the dive
entry and slow motion on a small group. Drops: their pistols and ammo.

**2. Long hall — "near or far"** (~5 × 30 m, 3 enemies, rifle + pistols)
A long sightline with the enemies at the far end and one in a side doorway
halfway. A **rifle pickup** near the entrance for the long approach; low
pillars to dive between for the rush. Answers question 2 directly.

**3. Open room — "explosives"** (~15 × 15 m, 4 enemies clustered, one MAC-11)
Enemies bunched around a central feature (a desk island or crates). Two hand
grenades on the way in, launcher rounds only if the launcher is found.
Grenades are the efficient answer, not the only one. Tests kill slow motion and
flung bodies, and whether the MAC-11's spray changes your pace.

**4. Two-level room — "escalation"** (~15 × 20 m, a balcony at 4 m)
- First group: 3 on the floor, 1 crouched on the balcony.
- When the first group is down, an `AEncounterDirector` brings in 3 more
  (`TotalEnemies` 3, `MaxAlive` 3) through a door the player can't see.
  Dual MAC-11s and a shotgun among them.

Stairs or a ramp up to the balcony. This is the "keep moving" test: a second
wave from behind the player's position. The **grenade launcher** pickup is
here, on the balcony.

**5. Exit stairwell — "close quarters"** (~6 × 6 m footprint, 2–3 floors)
2–3 holders, crouched on the landings above, shotgun and pistols. Tight angles,
short sightlines: shotgun and revolver territory. The level ends at the top
(exit trigger).

**Optional scripted beat (new tech):** somewhere around room 3 or 4, one enemy
throws a grenade the player can shoot out of the air. `AGrenade` already
explodes when shot and credits the shooter. What's missing is a scripted
thrower (an enemy action, or a trigger-spawned grenade on a set arc). Small
work, but only if the design wants it in the slice.

## Encounter table
| Beat | Enemies | Weapons | Start | Pickups |
|---|---|---|---|---|
| 0 | — | — | — | pistol ammo, 2nd pistol (duals) |
| 1 | 3 (1 crouched) | pistols | doorway trigger | (drops) |
| 2 | 3 | rifle, pistols | sight / trigger | rifle |
| 3 | 4 | MAC-11, pistols | doorway trigger | 2 grenades |
| 4 | 4 + wave of 3 | dual MAC-11, shotgun, pistols | doorway; director after | grenade launcher, rifle ammo |
| 5 | 2–3 (crouched) | shotgun, pistols | stairwell trigger | shotgun shells, revolver |

## Build order (one item at a time)
0. **Test the encounter triggers first** (waiting enemies, ambush moves,
   spawns, spawn-ahead lines; see the spec). Every room below depends on
   them. Rooms can then be stocked by a spawn-ahead line placed before each
   one instead of placed enemies.
1. Blockout: rooms 0–5 as plain geometry (engine cubes or modeling tools),
   connected and walkable; a NavMesh bounds volume over all of it.
2. Room 1 fully set up (enemies, trigger, pickups) and played. The template for
   the rest.
3. Rooms 2–3; play.
4. Room 4 with the director wave; play.
5. Room 5 and the **level-end trigger** (new: a small "reached the exit"
   actor; restarting is fine for the slice).
6. A pass on lighting (basic, readable) and pickup placement.
7. Playtest against the five questions; tune counts, sizes and ammo.

New code the slice needs: only the **exit trigger** (small). *(Built 2026-10-24: `ALevelExitTrigger`, see the spec's "Level exit"; not placed yet.)* *(2026-10-24: triggers now have `Waves` and a room-cleared hook, so room 4's "wave of 3" can be a wave on its trigger instead of the director.)* Optional: the
**scripted grenade thrower**, and **checkpoints**, if a restart from the top
proves too punishing at 5–8 minutes.

## Not decided here (design-owned)
- **Where this is.** *Partly settled 2026-10-23:* Filipino slum alleyways
  (user). The district and whether it maps to a story arc are still open; the
  arc mapping is blocked (lore *Campaign structure*).
- **Who the enemies are.** The enemy composition is `[UNDECIDED]` since the
  Aswang were dropped (2026-10-09). The slice uses the existing human
  gunmen as placeholders.
- **Any story beat, dialogue or scripted moment content** beyond the
  mechanical ones above.
