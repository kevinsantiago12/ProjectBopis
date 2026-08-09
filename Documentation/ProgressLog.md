# ProjectBopis — Progress Log

> Running record of project state and session-by-session progress, kept so
> context carries over between Claude Code sessions. Newest entry on top.
> Update this at the end of any session with meaningful progress or decisions.

## How to use this file
- Add a new dated entry for each session with notable work.
- Keep entries short: what changed, what was decided, what's next.
- Link to relevant files with `path:line` where useful.
- Move stale "Next Steps" into "Decided/Done" once complete.

---

## 2026-08-09 (3)
**Summary:** User added an Unreal MCP plugin to the project.

**Done:**
- Confirmed `ModelContextProtocol` plugin entry now present and enabled in
  `ProjectBopis.uproject`. No project-local `Plugins/` folder exists, so
  it's presumably coming from the engine install rather than a
  project-vendored plugin.
- Checked this Claude Code session's available tools — no Unreal-specific
  MCP tools are connected yet. The plugin exposes an MCP server from
  inside the Unreal Editor; this CLI needs to be separately configured
  (e.g. `claude mcp add`) to connect to it as a client, with the editor
  running.

**Open Questions / Next Steps:**
- Decide whether Claude Code should be wired up to the UnrealMCP server
  (would allow direct editor control/queries from these sessions), and if
  so, get the connection details (host/port or transport) from the plugin.

---

## 2026-08-09 (2)
**Summary:** Imported design/lore canon from the user's design partner (ChatGPT); rewrote GDD as an implementation spec.

**Done:**
- Confirmed division of labor: design/lore owned by user + ChatGPT; Claude's
  role is implementation/code.
- Imported `Project_Bopis_Design_and_Lore_Notes.txt` verbatim into
  `Design Document/Lore_And_Design_Notes.md` as the canonical lore/design
  reference.
- Rewrote `Design Document/GameDesignDocument.md` into an implementation-
  facing spec derived from that canon: sci-fi cyberpunk FPS, Bungie-era Halo
  combat reference, Philippines/2098 setting, hip-fire-first combat with
  Halo: Reach-style bloom (no ADS accuracy bonus), linear-nav/nonlinear-
  combat arena philosophy, synthetic (non-human) enemies, no dialogue-choice
  narrative system.
- Added an Engineering Backlog to the GDD (§9) as the concrete next-step
  list for code work.

**Decided:**
- Combat accuracy model: bloom-based (Halo: Reach), not ADS-accuracy and not
  camera-climb recoil. This is now the binding spec for weapon code.
- Genre/tone: sci-fi cyberpunk FPS is locked — `Variant_Horror` is likely to
  be pruned eventually, but holding off until design confirms no hybrid use.

**Open Questions / Next Steps (engineering):**
1. Audit `Source/ProjectBopis/Variant_Shooter/Weapons/ShooterWeapon.*` /
   `ShooterWeaponHolder.*` for template ADS-accuracy behavior to strip out.
2. Design + implement the bloom data model as a reusable weapon component.
3. Build bloom/aim-reactive reticle UI.
4. Implement zoom as a per-weapon flag independent of generic aim input.
5. Extend `ShooterNPC`/`ShooterAIController` (StateTree-based) into a
   data-driven synthetic-chassis archetype system.
6. Still open: whether/when to set up git version control.

---

## 2026-08-09 (1)
**Summary:** Project setup review + documentation scaffolding.

**Done:**
- Confirmed project state: UE 5.8 project (`ProjectBopis.uproject`), built
  from Epic's FPS template, containing both `Variant_Shooter` and
  `Variant_Horror` source (see `Source/ProjectBopis/`). No git repo yet.
- Created `Design Document/GameDesignDocument.md` — GDD skeleton (local-only,
  not published as a web artifact).
- Created `Documentation/ProgressLog.md` (this file).

**Open Questions / Next Steps:**
- Decide core direction: Shooter, Horror, or hybrid — fill in GDD Sections 1-3.
- Decide whether to set up git version control.
- Decide whether to prune the unused template variant.
