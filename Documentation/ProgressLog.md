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

## 2026-08-09 (5)
**Summary:** Phase 1 (weapon foundation) built out almost entirely, working
through `Documentation/ProjectPlan.md` checklist item by item with the user
typing all C++ themselves (learning C++, coming from C#).

**Done — all compiling clean:**
- `AWeaponBase` (`Source/ProjectBopis/Weapons/WeaponBase.h/.cpp`): actor
  with a `WeaponMesh` component and data-driven tuning properties
  (`EWeaponFireMode FireMode`, `BaseDamage`, `MaxRange`, `bHasZoom`), plus
  `Fire(TraceStart, TraceDirection)` — a hitscan `LineTraceSingleByChannel`
  out to `MaxRange` that dispatches `UGameplayStatics::ApplyPointDamage` on
  a hit.
- `UWeaponHolderComponent` (`Source/ProjectBopis/Weapons/WeaponHolderComponent.h/.cpp`):
  `AddWeapon`/`EquipWeapon` with a configurable `MaxCarriedWeapons` (default
  2), equips by attaching the weapon to a hand socket
  (`WeaponAttachSocketName`, currently an unverified guess of `"hand_r"`)
  on the character's `FirstPersonMesh` and tagging its mesh
  `FirstPersonPrimitiveType::FirstPerson` so it renders through the same
  path as the arms. `FireEquippedWeapon()` sources a trace from the
  character's first-person camera. `StartingWeaponClass`
  (`TSubclassOf<AWeaponBase>`) spawns/adds a starting weapon in
  `BeginPlay`, as a temporary test-only stand-in for a real pickup system.
- Wired onto `AProjectBopisCharacter`: `WeaponHolder` member + getter,
  `FireAction` input property, `DoFire()` handler bound via Enhanced Input
  (`ETriggerEvent::Started`, i.e. one shot per click for now — revisit once
  `FireMode` actually matters, in the bloom phase).
- **Deliberately not built yet:** any `Health`/`TakeDamage` handling.
  `ApplyPointDamage` correctly dispatches, but nothing consumes it — there's
  nothing to shoot yet. That's Phase 4's job (enemy archetype foundation).

**Not yet done:** the actual PIE playtest. C++ side is ready; remaining
work is pure editor/content (Input Action asset, mapping context entry,
`BP_TestWeapon` Blueprint, assigning `StartingWeaponClass`, verifying the
hand socket name, playtesting) — outlined step-by-step in
`Documentation/ProjectPlan.md`'s Phase 1 last item. User is continuing this
next session.

**Collaboration note for future sessions:** user writes all C++ by hand
(learning C++, C# background) — present code in chat, don't write
`Source/**` files directly. A live task checklist (TaskCreate/TaskUpdate)
mirrors `ProjectPlan.md`'s phases; re-show it in chat after every completed
item without being asked. See memory for full detail.

---

## 2026-08-09 (4)
**Summary:** Decided to remove both template variants and start gameplay
systems from scratch; git set up as a safety net; created a phased project
plan.

**Done:**
- Initialized git (with a `.gitignore` for `Binaries/`, `Intermediate/`,
  `DerivedDataCache/`, `Saved/`, `.vs/`, generated `.sln`/`.slnx`) and
  committed a baseline snapshot of the original template state before
  making any destructive changes.
- Removed `Source/ProjectBopis/Variant_Horror/` and
  `Source/ProjectBopis/Variant_Shooter/` entirely.
- Confirmed the project's default map/game mode already point at the base
  `FirstPerson` variant (`Config/DefaultEngine.ini`), so removing the two
  variants doesn't break project startup.
- **Blocked:** `Content/Variant_Horror/` and `Content/Variant_Shooter/`
  could not be deleted from outside the editor — `UnrealEditor.exe` was
  running and had the `.uasset`/`.umap` files locked ("Device or resource
  busy"). Needs to be deleted from inside the editor's Content Browser (or
  the editor closed so it can be removed externally).
- Updated `Design Document/GameDesignDocument.md` (and matching `.html`) to
  reflect that the systems it specs (weapons, enemy AI) will be built fresh
  rather than extended from the now-deleted template classes; its
  Engineering Backlog section now points to the new plan instead of
  duplicating it.
- Created `Documentation/ProjectPlan.md` — an ordered, phased build
  sequence (Phase 0 ground-clearing through Phase 5 first playable arena),
  meant to be worked through incrementally, one item at a time.
- Updated `CLAUDE.md` to point future sessions at the Project Plan as the
  actual task list.

**Open Questions / Next Steps:**
1. Delete `Content/Variant_Horror/` and `Content/Variant_Shooter/` (from
   inside the editor, once it's available) — Project Plan Phase 0.
2. Verify the project compiles/opens cleanly after that deletion.
3. Start Project Plan Phase 1 (weapon foundation).

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
