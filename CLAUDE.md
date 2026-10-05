# ProjectBopis

Gritty, noir third-person action shooter set in the Philippines, **2002**.
Heavy noir narrative, John Woo / heroic-bloodshed action, Filipino
crime/action cinema as the identity. Authored protagonist (male, late 30s–
early 40s, cynical and tired — the opposite of Hard Boiled's Tequila).

**Setting changed 2026-09-13.** The previous 2098 sci-fi/cyberpunk premise,
synthetic enemies, and personality-neutral protagonist are all discarded —
see the DISCARDED section of `Design Document/Lore_And_Design_Notes.md` and
do not reintroduce any of it. The old *gameplay* ideas (bloom, hip-fire,
linear arenas, 10+ missions) are neither canon nor obsolete: each is to be
reconsidered individually against the new game. Primary action references:
John Woo (Hard Boiled, The Killer, A Better Tomorrow), Max Payne (as a
translation reference, not a template), and Filipino action cinema. The
old Bungie-era Halo reference is superseded.

Unreal Engine 5.8, scaffolded from Epic's FPS template and converted to
third person (decided 2026-09-25, built on `tps-conversion`, finished
2026-10-05). The `Variant_Shooter` and `Variant_Horror` template variants were
removed (2026-08-09) — all gameplay systems are built from scratch against
the design doc, not adapted from template code. The `Content/FirstPerson/`
folder name is a template leftover kept on purpose; the assets in it were
renamed (`BP_PlayerCharacter`, `BP_GameMode`, `BP_PlayerController`,
`ABP_Player`, level `Lvl_Sandbox`). Animation is Lyra's library on the same
skeleton. The weapon/ammo/reticle systems built under the old premise are
**implementation state**, not canon; they're the test bed the new direction
gets evaluated against.

## Division of labor
- **Design & lore**: owned by the user + their design partner (ChatGPT).
  Canon lives in `Design Document/Lore_And_Design_Notes.md` — treat it as
  source of truth for narrative/world/story content. Do not invent lore to
  fill its `[UNDECIDED]` gaps; ask or wait for design input instead.
- **Implementation**: this is Claude's role. `Documentation/TechnicalDesignSpec.md`
  is the implementation-facing translation of the design into concrete systems
  specs (bloom parameters, weapon/ammo architecture, architecture principles,
  gotchas) — that's the file to work from for code decisions.
- `Design Document/GameDesignDocument.md` is **pitch-facing and deliberately
  non-technical** as of 2026-08-31. Keep it that way: no code, no parameter
  names, no jargon. New technical detail belongs in `TechnicalDesignSpec.md`.

## Standing rules
The user's collaboration rules (C++ review flow, editor-bridge permissions,
checklist habits, git limits) live in `Claude-Rules.md` and are imported here.
They override default behaviour. Add new standing rules there, dated.

@Claude-Rules.md

## Session start
- Read [Documentation/ProgressLog.md](Documentation/ProgressLog.md) for
  current project state and open items before starting work.
- Read [Documentation/ProjectPlan.md](Documentation/ProjectPlan.md) for the
  ordered, phase-by-phase build sequence — this is the actual task list,
  worked one item at a time.
- Read [Documentation/TechnicalDesignSpec.md](Documentation/TechnicalDesignSpec.md)
  for implementation specs/constraints behind those tasks.

## Session end
- If meaningful progress or decisions were made, add a dated entry to
  `Documentation/ProgressLog.md`.
- Check off completed items in `Documentation/ProjectPlan.md` as they land.
- If new design/lore canon arrives from the user, import it into
  `Design Document/Lore_And_Design_Notes.md`, then re-translate the relevant
  parts into `Documentation/TechnicalDesignSpec.md` (systems) and summarise
  for pitch purposes in `Design Document/GameDesignDocument.md` (+ its `.html`
  twin, which has the same content as tabbed pages).
- If implementation decisions were made, update `TechnicalDesignSpec.md`
  accordingly (resolve `TBD`s).
