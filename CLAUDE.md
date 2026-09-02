# ProjectBopis

Sci-fi cyberpunk FPS, set in the Philippines, 2098. Unreal Engine 5.8,
scaffolded from Epic's FPS template. The `Variant_Shooter` and
`Variant_Horror` template variants have been removed (2026-08-09) — all
gameplay systems (weapons, enemies, etc.) are being built from scratch
against the design doc, not adapted from template code. Only the base
`FirstPerson` scaffolding remains. Primary gameplay reference: Bungie-era
Halo.

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
