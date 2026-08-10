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
- **Implementation**: this is Claude's role. `Design Document/GameDesignDocument.md`
  is the implementation-facing translation of the lore canon into concrete
  systems specs (see especially its Combat System and Engineering Backlog
  sections) — that's the file to work from for code decisions.

## Session start
- Read [Documentation/ProgressLog.md](Documentation/ProgressLog.md) for
  current project state and open items before starting work.
- Read [Documentation/ProjectPlan.md](Documentation/ProjectPlan.md) for the
  ordered, phase-by-phase build sequence — this is the actual task list,
  worked one item at a time.
- Read [Design Document/GameDesignDocument.md](Design%20Document/GameDesignDocument.md)
  for implementation specs/constraints behind those tasks.

## Session end
- If meaningful progress or decisions were made, add a dated entry to
  `Documentation/ProgressLog.md`.
- Check off completed items in `Documentation/ProjectPlan.md` as they land.
- If new design/lore canon arrives from the user, import it into
  `Design Document/Lore_And_Design_Notes.md` and re-translate the relevant
  parts of `GameDesignDocument.md`.
- If implementation decisions were made, update `GameDesignDocument.md`
  accordingly (resolve `TBD`s).
