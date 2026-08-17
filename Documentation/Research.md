# ProjectBopis — Research Notes

> External reference material (talks, articles, postmortems) worth keeping
> around because it directly informs a system we're building. Not canon,
> not a task list — background reading distilled into notes we can act on
> later. Cross-reference the relevant `Documentation/ProjectPlan.md` phase
> so it's obvious when a note becomes actionable.

---

## Halo 2 AI architecture — Damian Isla, GDC 2005
**"Managing Complexity in the Halo 2 AI System"**
Source: https://www.youtube.com/watch?v=m9W-hpxuApk
Relevant to: [Phase 5 — Enemy archetype foundation](ProjectPlan.md) (StateTree-based,
composable synthetic enemy archetypes; explicit Halo reference per `CLAUDE.md`).

### Core architecture
- **Behavior tree, really a DAG** — nodes ("behaviors") are temporal programs
  with start/end conditions that take control of the actor for a duration,
  not discrete one-shot actions. A behavior can appear in more than one
  place in the tree.
- **Binary relevancy, not analog scoring** — each behavior just says "I want
  to run" or "I don't." Deliberately chosen over floating-point
  utility/relevancy scoring because Bungie wanted decisions to snap
  discretely rather than blend subtly — subtlety reads as indecision to a
  player.
- **Impulses** — a free-floating trigger that references an *existing*
  behavior but places it at a different priority than its default slot.
  Solves the "priority isn't constant" problem: vehicle-entry is normally
  low priority, but a "player-just-drove-up" impulse makes it top priority
  in that one situation, without hardcoding a special case into the tree
  shape. Impulses are also used as a deliberate escape hatch for small
  ad-hoc logic ("hacks") — e.g. a crouch-on-danger or dive reaction — kept
  inside the same tracked system rather than freestanding code.
- **Behavior masking via metadata** — each behavior declares its execution
  conditions as a bit vector (vehicle status: driver/passenger/infantry,
  alert state, etc.), so entire branches get filtered out structurally
  instead of every node re-checking the same conditions every tick.
- **Variation from a stable base** — one generic tree covers shared
  structure; specific character types graft on custom branches (e.g.
  grunts get extra retreat impulses other types never evaluate) instead of
  duplicating the whole tree per type.
- **Stimulus-driven impulses** — event-driven triggers (e.g. "leader died →
  flee") get dynamically inserted into the tree with a lifetime, instead of
  every actor polling "did my leader die?" every single tick forever.
- **Joint/group behaviors** via either mutual invitation (both parties must
  accept, e.g. flipping a rolled vehicle together) or a blackboard-style
  "join anytime" model, depending on the behavior's shape.

### Memory model (three tiers)
1. **Behavior state** — short-term/volatile, exists only while that
   specific behavior is actively running; discarded on interrupt.
2. **Persistent-per-behavior** — small permanent slot on the actor for data
   a behavior needs across activations (e.g. last grenade-throw timestamp,
   for a "max once per 5s" rule).
3. **Persistent-per-target ("props")** — memory keyed to a specific target,
   not to a behavior. Example: search location belongs to the actor's
   *mental model of the target*, not to the search behavior — so if search
   is interrupted (target reacquired, then lost again) and resumed later,
   the correct search point survives even though the behavior itself was
   torn down and rebuilt in between. Props double as the perception cache,
   i.e. this is also where "what do I currently know about this object" is
   stored.

**Guiding rule:** when data feels like it belongs to a relationship with a
target rather than to the behavior currently running, put it in the
per-target memory, not the behavior. This is what keeps interrupted/resumed
actions coherent instead of buggy.

### Data-driven authoring
- **Character hierarchy** — character definitions are split into blocks
  (vitality, perception, search, weapon usage, etc.); child character
  variants inherit from a generic base and only override the deltas.
  Avoids having to hand-author every parameter for every variant from
  scratch (Halo 2 had ~64 variants; a flat-list approach would have meant
  ~15,000 authored floats).
- **Styles** — composable behavior masks + parameter bias (aggressive /
  defensive / cautious), stackable from multiple sources at once (the
  character itself, the vehicle seat it's in, the squad order it's under)
  onto the same underlying tree. Deliberately kept to a small handful of
  styles — players won't perceive subtler gradations anyway.
- **Squads / Zones / Orders** (dynamic, per-level control) — squads
  (actor groups) are given orders that map them to zones (areas) plus
  behavior direction (rules of engagement, vehicle allow/disallow, stealth
  on/off, follow-player). Entirely GUI-authored, no scripting required from
  designers. This tier is closer to Phase 6/7 (encounter/level design)
  than Phase 5.

### 5 stated design principles
1. Use multiple decision strategies together (prioritized list, sequence,
   random, etc.) rather than forcing one mechanism to fit every case.
2. Formalize complexity — don't hide two different triggers behind one
   merged relevancy function just because they happen to trigger the same
   behavior; keep them as separate, individually-tunable entities.
3. Embrace small ad-hoc hacks, but keep them inside a system that tracks
   and contains them (e.g. impulses), rather than freestanding.
4. Build variation from a stable, shared base instead of duplicating whole
   structures per variant.
5. Make your representations work well together — most systems here
   ultimately feed back into the same central decision structure, in
   principled rather than ad hoc ways.

### Mapping to UE5 StateTree (Phase 5)
Rough translation for when Phase 5 starts:
- Binary relevancy → StateTree transition conditions.
- Impulses (priority override) → global/linked state trees, or
  higher-priority transitions layered over a shared base tree.
- Behavior masking → StateTree Enter Conditions driven by
  schema/context parameters.
- Generic base + per-archetype grafted branches → a shared base StateTree
  (or shared states) with archetype-specific states/transitions added on
  top — lines up directly with the Phase 5 plan's "movement, attack,
  battlefield role as separate composable pieces" goal.
- Per-target memory ("props") → `AIPerceptionComponent` data plus a small
  custom per-target memory struct (e.g. keyed by target actor) rather than
  stuffing that state into StateTree instance data that gets torn down.

Not yet decided how much of this to adopt vs. simplify — ProjectBopis's
enemy roster is far smaller than Halo 2's, so some of this (the full
Squads/Zones/Orders layer especially) may be overkill until Phase 6/7 scope
is clearer. Revisit this note when Phase 5 actually starts.
