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
- Commit only when asked. Narrate destructive operations (force-push, history
  rewrites) clearly before handing them off.
- Don't commit `.claude/settings.local.json`; it's machine-specific.

## 7. Design and lore

- Design and lore are owned by the user and their design partner. Never invent
  lore to fill `[UNDECIDED]` gaps; ask instead. *(see `CLAUDE.md`)*
- Don't reintroduce anything from the discarded 2098 sci-fi premise.
