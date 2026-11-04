# Claude Rules — ProjectBopis

Standing rules the user has set for how Claude works on this project. Loaded
automatically at session start via an `@Claude-Rules.md` import in
`CLAUDE.md`. **These override default behaviour.** When the user sets a new
standing rule mid-session, add it here (with the date) in the same session.

Project-wide process (session start/end reading, which doc owns what, lore
canon) lives in `CLAUDE.md` and is not repeated here.

---

## 1. C++ code — the user types it

The user is learning C++ through this project (C# background) and wants the
hands-on practice.

- **Never write `Source/**` files directly.** Present C++ in chat for the user
  to type in. Applies to all C++ regardless of size, even a three-line getter.
  *(2026-08-09, reaffirmed 2026-08-31)*
- **Present → wait for approval → apply.** "Apply it yourself" is a
  **per-instance** permission, never a standing change. Approval for one change
  never carries to the next; go back to presenting afterwards. *(2026-08-31)*
- **"Show me the changes first" means stop and present**, even mid-apply.
  Re-present the full change set before touching files. *(2026-10-03)*
- **Small increments.** One checklist item per message: a cohesive chunk
  across however many files it needs. Don't bundle items.
- **Wait for compile confirmation** ("compiled clean", "rebuild done") before
  moving to the next item.
- **Read the files back after every compile confirmation** before moving on.
  This catches typos or divergence, and picks up the user's own added
  comments. *(2026-08-12)*
- **Never mark code done before it's confirmed compiled.** If a session ends
  first, log it as "code given, not yet compiled". *(2026-08-11)*
- Docs, config and project files are **not** covered by these rules: write
  them directly.
- **Rebuilds:** `Tools/RebuildEditor.bat` closes the editor, builds and reopens
  it. Run it only when the user asks ("run the script") — it closes their
  editor. After it, the usual post-rebuild check (§3) applies: wait for the
  bridge port, one `list_toolsets`, DLL timestamp. *(2026-10-06)*
- **Coordinate before closing the editor (2026-10-31):** other Claude sessions
  share this editor (`ListAgents` shows them). Before anything that closes it
  (the rebuild script, a restart), message each peer session that works in the
  editor (`SendMessage`), ask whether it's safe, and wait for their answer.
  If a peer is mid-edit or has unsaved work, hold off and tell the user.
- **Check silently (2026-11-01):** "do it silently so that the other threads
  dont show any notification unless theres a conflict." Messages make every
  peer show a notification. So check with `ListAgents` instead: an **idle**
  peer isn't mid-edit, so count it as safe without messaging it. Message
  only a peer that's **busy** (working right now), since that's a possible
  conflict, and wait for its answer. The rebuild script never force-closes:
  a save prompt makes it stop, which covers the user's own unsaved work.

## 2. Explaining things

- Use **C# analogies** where they clarify (GC vs `UPROPERTY`, attributes vs
  `UCLASS`/`UFUNCTION` macros, references vs `TObjectPtr`).
- Don't re-explain what transfers directly from C# or what's already been
  covered in this project. Spend explanation on what's actually new.

## 3. Unreal MCP editor bridge

- **Ask before ANY bridge action, every time.** This covers `list_toolsets`,
  `describe_toolset`, `call_tool`, and also anything *around* the bridge:
  HTTP probes of `127.0.0.1:8000/mcp`, `claude mcp get/list` health checks,
  edits to `.mcp.json` or `.claude/unreal-mcp-proxy.mjs`, and notes telling a
  future session to run bridge checks. *(2026-09-28, widened 2026-10-03)*
- **Why:** responses are huge and burn context. Say what calls are needed and
  why; when approved, batch the work so one yes covers the task.
- **Prefer bridge-free routes:** grep `.uasset` binaries
  (`grep -aoE "/Game/[A-Za-z0-9_/.]*" file.uasset`), read
  `Saved/Logs/ProjectBopis.log`, or ask the user to check something in the
  editor.
- **Fine without asking:** checking whether the editor is running (`tasklist`,
  `netstat -ano | grep :8000`), since that touches neither the bridge nor its config.
- **Exception: after every rebuild, test the connection.** Make one
  `list_toolsets` call without asking, plus a check that the DLL timestamp in
  `Binaries/Win64/` is newer than the edited source, and report both. Nothing
  beyond that one call is pre-approved. *(2026-10-03)*
- A request to make something through the bridge (e.g. "make a BP_Shotgun")
  approves the calls that task needs, not later tasks.
- **"Apply and run" includes the bridge (2026-10-18):** when the user says
  "apply and run" for a presented change, that also approves the bridge calls
  the change needs (AnimBP/Blueprint edits, compile, save), unless they
  explicitly say not to use it. It still covers only that presented change.

## 4. Checklist and progress

- Work from `Documentation/ProjectPlan.md` (and the active work order) **one
  item at a time**.
- **Re-show the checklist in chat after every completed item**, without being
  asked. *(2026-08-09)*
- When the user asks where things stand, give the checklist status.

## 5. Session wrap-up

When the user says something like "put that in the docs, I'll continue
tomorrow":
1. Add a dated entry to `Documentation/ProgressLog.md`, including an updated
   **RESUME HERE** list.
2. Sync `ProjectPlan.md` and work-order checkboxes.
3. Update `TechnicalDesignSpec.md` for implementation decisions. The GDD
   (+ `.html`) is pitch-facing and non-technical, so it gets design/state
   changes only.
4. Update this file with any new collaboration rules.

Tasks the user defers ("flag this for next session") go into the RESUME HERE
list, not just chat.

## 6. Git

- Local git (status, diff, branch, commit) is fine to run.
- **`push`/`fetch`/`pull` can't authenticate from this sandbox.** Don't retry.
  Prepare locally and hand the user the exact command to run in their own
  terminal.
- **The user commits (2026-10-16):** "I will commit from now on." Don't
  commit; when work is done, say what's uncommitted so they can. Local
  read-only git (status, diff, log) is still fine.
- Narrate destructive operations (force-push, history rewrites) clearly before
  handing them off.
- Don't commit `.claude/settings.local.json`; it's machine-specific.

## 7. Design and lore

- Design and lore are owned by the user and their design partner. Never invent
  lore to fill `[UNDECIDED]` gaps; ask instead. *(see `CLAUDE.md`)*
- Don't reintroduce anything from the discarded 2098 sci-fi premise.

## 8. Level generation

- **Building blockouts only (2026-11-03):** "forget all the dressings and,
  just make the building block outs. No other objects in the level besides
  building blockouts as a rule."
  - **Stays:** the buildings, the gameplay actors, and the gallery deck and
    stairs.
  - **Out:** cover, pickups, dressing and decals, until the user asks for
    them.
  - **Roof terraces (2026-11-03):** covered roof terraces on the 1-storey
    blocks (parapet, corrugated sheets, plank frame) count as building
    ("Yes, build them"). Their water drums don't.
  - **Decals (2026-11-03):** wall drip decals are allowed, `MI_Decal_Dirt_08`
    only. ("I want stain decals next"; withdrawn, then "actually, bring it
    back but use decal dirt 8".) The rest of the dressing stays off.
  - Details and the generator switches: `Tools/LevelGen/LESSONS.md`.
- **Analysing models (2026-11-03):** "I give you permission to analyze them …
  when you need to." When level work needs it, inspect the meshes (bounds,
  collision, renders) through headless scripts or Blender without asking
  first. Only when it's needed, never as a standing sweep. Bridge calls
  still follow §3.
  - **The user also asked for a one-off full analysis (2026-11-03)** of
    Megapack, AsiaSlum and Philippines_Markets: "the models themselves via
    editor or blender, not just metadata."
- **Reference images (2026-11-03):** Pinterest and Google Images in the
  built-in browser are allowed for references ("look at google images as
  well. So I allow you to do that"). Viewing only; ask before downloading.
- **Hollow blocks (2026-11-03):** "only use them on walls with no windows or
  doors. They are not to be used for whole houses"; "the only mixing rule is
  not to mix on the same face". Neighbouring faces may differ.
- **Paint (2026-11-04):** "One color per house, but some side can remain
  unpainted". Faces never mix. Keep the dirt decals ("keep the dirt decal
  placement there").
- **Window grilles (2026-11-04):** ground-floor windows get grilles, and they
  count as building ("find an appropriate window grill and put it in the first
  floor windows", "more variation is appreciated").
- **Hidden patterns (2026-11-04):** "we are trying to have patterns in building
  but have the player not see patterns when playing". Build from rules, but
  never let a rule read as a rule: no fixed cycles, keep exceptions.
- **Bands and borders (2026-11-04):** on a painted face the band always matches
  ("when the face is painted, the band looks off if left unpainted. It works for
  hollow blocks but not for painted"). Between the floors a building has one of three: "1. No
  borders, 2. A border 3. A portruding band". Same paint on wall and band means
  no border; the protruding band is "the band between the 1st and 2nd floor, not
  the top floor".
- **Drips (2026-11-04):** a dirt decal's hard top edge must hide behind a ledge
  (a border or a protruding band), never show on a clean wall ("reevaluate the
  placements of Dirt decals, becuase of the new border and band rules").
- Read `Tools/LevelGen/LESSONS.md` before every level build. Run
  `Tools/LevelGen/analysis/check_overlaps.py` after every generator change
  (no coincident faces).
