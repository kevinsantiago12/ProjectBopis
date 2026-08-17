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

## 2026-08-17
**Summary:** Reversed which weapon carries the real projectile, and locked
down the in-world justification for it. No code written — design/docs only.

**Decided:**
- **Projectile weapon flipped from battle rifle to close-range rifle.** The
  earlier 2026-08-12 call put the real projectile on the battle rifle;
  that's reversed now. Reasoning: dodgeable travel time is only meaningful
  at close range, where an enemy would otherwise have zero reaction window
  against an instant hitscan hit — at the battle rifle's mid-range
  engagement distance, perceptible travel time would just read as an
  aiming penalty, not a dodge-skill test. So: pistol and battle rifle stay
  hitscan; the close-range rifle gets `AProjectileBase`.
- **In-world justification: electromagnetic (coilgun), not plasma.**
  Muzzle velocity scales with coil-stage count/barrel length, so a compact
  close-range weapon is physically slower than the longer-barreled battle
  rifle — a hard-sci-fi reason for the split, not an arbitrary carve-out.
- **Round is saboted/pre-scored to fragment on impact**, trading
  penetration for a shrapnel burst, so the slower projectile doesn't read
  as weaker — strong vs. close/grouped/exposed targets, weak vs.
  armor/hard cover, which keeps the hitscan pistol and battle rifle
  relevant.
- Full writeup: `Design Document/GameDesignDocument.md`'s new "Weapon
  tech" section. Phase 4 checklist in `Documentation/ProjectPlan.md`
  updated to match (`AProjectileBase` now targets the close-range rifle;
  weapon configuration tasks swapped accordingly).

---

## 2026-08-17
**Summary:** Finished Phase 3 entirely (including a real zoom/trace-source
bug fix), completed Phase 4's fire-feedback step, got decal code ready to
compile — and discovered a separate/concurrent session had already been
working on this same project, with its own doc edits that needed merging
rather than overwriting.

**Discovered mid-session — important:** `Documentation/ProjectPlan.md`,
`Design Document/GameDesignDocument.md`, and a new
`Documentation/Research.md` already contained substantial content this
session never wrote: a full reversal of which weapon gets the real
projectile (now the **close-range rifle** — electromagnetic coilgun,
fragments on impact, dodgeable-at-close-range reasoning — not the battle
rifle as originally decided 2026-08-12), a new "Weapon tech" design
section explaining that reasoning in detail, and Halo 2 AI-architecture
research notes (Damian Isla's GDC talk) relevant to the future enemy
phase. All dated 2026-08-17, clearly from another session working on this
project in parallel. Also found `PhysicsSetup.ini` sitting at the project
**root** with `PhysicalSurfaces` definitions matching the deferred
`ImpactsVFXVol1` pack — **flagged as likely inert**, since Unreal only
reads physics surface-type settings from `Config/DefaultEngine.ini`'s
`[/Script/Engine.PhysicsSettings]` section, not a loose root-level file;
worth the user checking whether that was meant to take effect.
Treated all of this as authoritative current state — merged this session's
own updates around it rather than overwriting, fixed a stale Phase
4→5 cross-reference in `Research.md` left over from before the Phase
renumbering, and corrected this session's task list (weapon-assignment
descriptions on the projectile-related tasks) to match the reversal.

**This session's actual work:**
- **Phase 3 fully complete.** Zoom FOV gating: `WeaponBase::HasZoom()`/
  `GetZoomedFOV()`, `DoAimStart`/`DoAimEnd` change the camera's real
  `FieldOfView` (not `FirstPersonFieldOfView`, which only governs the
  arms/weapon rendering pass — a distinction worth remembering), reset to
  a `DefaultFOV` cached once in `BeginPlay`. Caught and fixed a real
  placement bug before it shipped: `DefaultFOV` caching was nearly nested
  inside the reticle-widget's `if` block, which would've left it stuck at
  `0.0f` whenever `ReticleWidgetClass` was unset.
- **Real bug found during the sanity-check step:** zoom and the Phase 1
  Halo-accurate off-center trace source (`CrosshairViewportPositionY =
  0.667`) permanently disagreed on "center" once FOV actually changed,
  since `FieldOfView` always narrows around the camera's true optical
  center (50%), not an arbitrary aim point. Fixed by simplifying back to
  `0.5f` for both hip-fire and zoom — deliberately dropping the authentic
  Halo offset rather than building dynamic per-state repositioning.
- **Phase 4 fire feedback complete:** `FireSound`/`MuzzleFlash`/
  `MuzzleSocketName` on `WeaponBase`. Used `UParticleSystem` (legacy
  Cascade) for muzzle flash, not Niagara — matches `SciFiWeapDark`'s `P_`-
  prefixed FX naming and avoided needing a new `Niagara` module
  dependency. User unified sound+flash under one `bUseAnimationDrivenFeedback`
  flag rather than two separate ones, since this pack's animations
  apparently drive both together — good simplification, matches the
  actual asset reality rather than over-engineering independent control
  nothing needs yet.
- **Hit-impact decal in progress:** user imported `Content/ImpactsVFXVol1/`
  by accident first (Niagara-based surface-reactive particle impacts,
  paired with `UPhysicalMaterial` assets — genuinely useful, deferred to
  its own task rather than discarded), then the correct pack,
  `Content/UWC_Bullet_Holes/` (~564 files, real per-surface decal
  materials). Gave the code (`HitDecalMaterial`/`DecalSize`/`DecalLifeSpan`,
  restructured `Fire()`'s hit block so decals spawn on any surface hit,
  not just hits with a damageable actor) — **not yet compiled**, resume
  here next.
- Discussed and deferred: animation-driven vs. code-driven fire feedback
  (parked on the animation task), Niagara's scalability tooling (informational).

**Next steps:**
1. Compile the hit-decal code, assign `MI_Generic_1` on `BP_TestWeapon`, test.
2. Continue Phase 4: `AProjectileBase`, forking `WeaponBase` for projectile fire (now for the **close-range rifle**), POV arms animation, then configuring the three weapons.
3. Still deferred: pistol hand-offset (#21), headshot-marker reticle (#37), surface-reactive Niagara impacts (#38).
4. Worth a look: whether `PhysicsSetup.ini` at the project root was meant to take effect (it currently won't, per the flag above), and whether the HTML twin of the design doc needs a full resync to catch up to the new "Weapon tech" section (patched the one paragraph this session touched, but the new section itself isn't mirrored yet).

---

## 2026-08-12 (3)
**Summary:** Major plan restructuring — deferred enemies in favor of a new
phase focused on getting three weapons fully realized (sound, muzzle
flash, decals, one real projectile weapon, POV animation). No code written
this segment, planning/docs only.

**Decided:**
- Enemies (old Phase 4) deliberately deferred behind a new **Phase 4 —
  Weapon content & feel**: fire sound + muzzle flash, placeholder
  hit-impact decals, a real `AProjectileBase` actor, forking `WeaponBase`
  to support projectile firing per-weapon, POV arms animation, and
  configuring three concrete weapons. Enemy archetype foundation and the
  vertical slice both shifted one phase later (now Phase 5/6).
- **The three weapons:** semi-auto pistol, full-auto close-range rifle,
  mid-range semi-auto battle rifle. Mapped to `SciFiWeapDark` assets —
  `Darkness_Pistol` and `Darkness_AssaultRifle` directly; the battle rifle
  reuses `Darkness_SniperRifle`'s mesh/anims tuned down (no/minimal zoom,
  different stats), since the pack has no dedicated "battle rifle."
- **Projectile scope, asked via explicit question rather than assumed:**
  one real weapon should actually fire a physical projectile now, not just
  a general future-facing capability. Landed on the **battle rifle**
  specifically (reasoning: pistol/close-range rifle both live in engagement
  ranges where instant hitscan feedback matters most; the battle rifle's
  mid-range/semi-auto/deliberate-shot identity is exactly where
  perceptible travel time reads as a feature, not a liability — and it
  keeps the pistol/AR pair matching how Halo's own weapons actually work,
  all hitscan).
- **Animation scope discussed, then deliberately walked back:** first
  considered animating both `FirstPersonMesh` (POV) and `Mesh` (the
  body/third-person representation — how other actors would see the
  player) now, reasoning it'd avoid retrofitting if spectate or co-op got
  added later. User reconsidered mid-discussion and scoped it down to
  **POV arms only** — body animation deferred until spectate/co-op is
  actually being built, not done preemptively. Both docs and the task
  list were corrected to match after the walk-back (worth double-checking
  this stayed consistent, since it was a live correction mid-edit).
- User has `PistolAnimset`/`RifleAnimset` ready but not yet imported —
  will add when that step is actually reached.
- Decal material for the placeholder hit-impact effect: **not yet
  sourced**, still an open item.

**Docs/tasks updated in real time this segment** (not deferred to an
end-of-session sync): `ProjectPlan.md` (full Phase 4 rewrite + renumbering
old Phase 4→5, 5→6, 6→7), `GameDesignDocument.md` + `.html` (scope-decision
note, corrected after the walk-back), and the task list (#15/#16 deleted,
tasks #27-36 created for the new Phase 4 breakdown + renumbered Phase 5/6
placeholders).

**Next steps:** still open whether to finish Phase 3's last two items
(zoom-gating, sanity check — center dot is mid-step, code given not yet
compiled) before starting Phase 4, or jump straight into Phase 4 and
circle back. Not yet decided as of session end.

---

## 2026-08-12 (2)
**Summary:** Got the reticle actually showing on screen and reacting to
aim input, continuing Phase 3.

**Done:**
- Created `WBP_Reticle` (`Content/UI/`, parent `ReticleWidget`), laid out
  the crosshair image (`icon_line_aim_8`) centered via Canvas Panel
  anchors/alignment. Minor hiccup along the way — Anchors weren't showing
  in Details at first (almost always means the widget isn't actually
  nested inside a Canvas Panel slot); resolved by the user without needing
  further help.
- Added `ReticleWidgetClass` + a `BeginPlay` override on
  `AProjectBopisCharacter` that `CreateWidget`s + `AddToViewport`s the
  reticle for the locally controlled player (`IsLocallyControlled()`
  guard). Compiled clean, reviewed, matches spec exactly. **Confirmed
  visible in PIE** — closes out the reticle widget foundation step.
- Added aim input: `AimAction`, bound to both `Started`
  (`DoAimStart`)/`Completed` (`DoAimEnd`) since aiming is a held state
  unlike `Fire`'s one-shot press. Simple `bIsAiming` bool + `IsAiming()`
  getter. Compiled clean, reviewed, correct. User also did the editor-side
  `IA_Aim` mapping.
- Gave the code for center-dot visibility
  (`ReticleWidget::GetCenterDotVisibility()`, returning `ESlateVisibility`
  directly so it can be wired via UMG's Bind feature with no extra graph
  logic) — **not yet typed in/compiled**, that's the actual next action.

**Next steps:**
1. Type in and compile `GetCenterDotVisibility()`.
2. Add a center-dot Image to `WBP_Reticle`, bind its Visibility to that function, confirm it only shows while aiming in PIE.
3. Zoom FOV gating per-weapon (`bHasZoom`), then the Phase 3 sanity check.
4. Still deferred: the pistol hand-attachment offset issue (#21).

---

## 2026-08-12
**Summary:** Finished Phase 2 (bloom/accuracy) completely, diagnosed a real
Live Coding data-corruption bug, cleaned up stale build config, and started
Phase 3 (reticle UI).

**Done:**
- **Diagnosed "shooting mechanics are gone" as a real Live Coding bug, not
  lost code.** Verified via file reads that all Phase 1 source was fully
  intact — the actual cause, confirmed via the engine's own log line
  (`"Live coding succeeded, data type changes may cause packaging to fail
  if assets reference the new or updated data types"`), was that changing
  `WeaponMesh`'s type (`UStaticMeshComponent` → `USkeletalMeshComponent`,
  done a session ago) had gone through Live Coding, which can't safely
  patch a data-layout change — it corrupted `BP_TestWeapon`'s link to
  `WeaponBase`. Fix: full Rebuild Solution (not Live Coding) + manually
  re-parenting the Blueprint. Documented as a standing rule in
  `ProjectPlan.md`'s new "Gotchas" section: type changes always get a full
  rebuild, never a Live Coding patch.
- Fixed real leftover cruft while investigating: `ProjectBopis.Build.cs`
  still listed `PublicIncludePaths` for the `Variant_Horror`/
  `Variant_Shooter` `Source/` folders deleted back in Phase 0 — trimmed to
  just `"ProjectBopis"`.
- **Phase 2 fully completed and compiled:**
  - Bloom tuning parameters, then live bloom driving actual shot spread
    (`FMath::Lerp` + `FMath::VRandCone`), decay gated by `BloomDecayDelay`.
  - Debug line's *visual* start point offset 150 units in front of the
    camera (separate from the real `TraceStart`) — a line starting right
    at the camera is nearly impossible to judge the angle of.
  - Cadence-penalty behavior for firing faster than a weapon's intended
    pace.
  - On-screen bloom readout via `GEngine->AddOnScreenDebugMessage`.
  - **New review habit paid off immediately:** the user asked for code to
    be reviewed after every compile confirmation (since they're now adding
    their own comments too) — first real review caught that the
    cadence-penalty code hadn't actually been typed in yet (still just the
    Step 2 version), avoiding a false "done." Second review caught a real
    bug: `ApplyPointDamage` was reporting `TraceDirection` instead of the
    actual fired `SpreadDirection` — fixed.
- **Phase 3 (reticle & aim/zoom UI) started,** broken into 5 steps:
  - `UReticleWidget` (`Source/ProjectBopis/UI/ReticleWidget.h/.cpp`) — a
    `UUserWidget` subclass exposing `GetCurrentBloom()` as
    `BlueprintPure`, so a Widget Blueprint can `Bind` visual properties
    directly to it. Compiled clean, reviewed, matches spec.
  - User added a second marketplace pack, `Content/CleanFlatIcons/`
    (~17,800-file generic icon set) for actual crosshair art —
    `icon_line_aim_8`. Same convention as `SciFiWeapDark`: left untouched
    in its own top-level folder. Minor housekeeping note: a leftover
    `FlatIcon_PNG_PSD.zip` sits uselessly in that folder, safe to delete
    whenever.
  - Not yet done: `WBP_Reticle` Widget Blueprint (parent `ReticleWidget`),
    actual visual layout, adding it to the viewport.
- **New known issue, deferred:** the equipped pistol isn't correctly
  positioned relative to the hand socket. Flagged, not yet investigated —
  tracked as its own task.

**Next steps:**
1. Create `WBP_Reticle`, lay out the crosshair image, add to viewport, bind to `GetCurrentBloom()`.
2. Add an Aim input + state (doesn't exist yet at all).
3. Center dot on aim, zoom-gating on aim, final Phase 3 sanity check.
4. Whenever convenient: the deferred pistol hand-offset issue.

---

## 2026-08-11
**Summary:** Finished Phase 0 and Phase 1 completely (tested working in PIE),
got the project onto GitHub, integrated a marketplace weapon pack, and
started Phase 2 (bloom).

**Done:**
- **Phase 0 closed out:** `Content/Variant_Horror`/`Variant_Shooter` fully
  deleted (editor released its lock on a later session). Verified clean via
  the editor's own log (`MapCheck: 0 Error(s), 0 Warning(s)`, no stale
  references) rather than needing manual inspection.
- **GitHub:** repo created at `github.com/kevinsantiago12/ProjectBopis`,
  pushed successfully. Non-trivial detour getting there — worth remembering
  for next time:
  - This sandbox has **no path to authenticate to GitHub at all** (HTTPS:
    no credential helper, no TTY for the prompt; SSH: the working key isn't
    reachable from here either). Every `git fetch`/`push` has to be run by
    the user in their own terminal, not through Claude's Bash tool.
  - First attempt went sideways: the user accidentally ran a clone-type
    command *inside* the project folder, creating a nested nested
    `ProjectBopis/ProjectBopis/.git` (a nearly-empty clone of a
    GitHub-initialized repo with just an auto-generated README). Cleaned
    up by renaming the local branch `master` → `main` and, once the user
    recreated a genuinely empty GitHub repo, a plain `git push -u origin
    main` worked with no merge/force needed.
  - Local repo is now on `main`, in sync with `origin/main`.
- **SciFiWeapDark marketplace pack added** (`Content/SciFiWeapDark/`) — an
  Infima Games-style "Darkness" sci-fi weapon bundle: 7 weapons (Pistol,
  AssaultRifle, Shotgun, SniperRifle, RocketLauncher, GrenadeLauncher,
  Knife), each with animated skeletal mesh + skeleton + physics asset,
  fire/reload/raise/lower animations, full sound design, FX, and pickup
  Blueprints. **Decision: left in its own top-level folder, untouched** —
  raw file moves (or careless in-editor moves) would break the pack's
  internal cross-references; standard practice for vendor content.
- **Phase 1 fully complete and tested:**
  - `WeaponBase::WeaponMesh` changed `UStaticMeshComponent` →
    `USkeletalMeshComponent` to use the new pack's animated weapons
    (animations not wired up yet — bind pose for now). Test weapon uses
    `Darkness_Pistol`.
  - Fixed a real process mistake: `StartingWeaponClass` had been marked
    "done" in `ProjectPlan.md` in an earlier session before the user had
    actually typed/compiled it, which caused a confusing "there's no
    Starting Weapon Class" moment later. Actually implemented and compiled
    this session. **Lesson: don't mark code as done in docs until the user
    has explicitly confirmed a successful compile** — see memory update.
  - Debugged a "not firing" issue methodically: unconditional `UE_LOG` to
    confirm the input chain reached `Fire()`, then `DrawDebugLine` to
    visualize the trace itself.
  - Real design refinement: the user wanted Halo-accurate trace behavior —
    not just "roughly lowered," but sourced from the *exact* screen-space
    point Halo's reticle sits at (horizontal center, ~2/3 down the
    viewport). Implemented properly via
    `APlayerController::DeprojectScreenPositionToWorld` at that screen
    position (`WeaponHolderComponent::CrosshairViewportPositionY = 0.667`),
    replacing an earlier, less accurate rotation-offset approach.
  - End-to-end confirmed working in PIE: weapon spawns, equips, attaches,
    fires, trace visibly lands where expected.
- **Phase 2 (bloom) started:** task list broken into 4 granular steps
  (mirroring Phase 1's approach). First step's code (six bloom tuning
  parameters on `WeaponBase`) was given but **not yet typed/compiled** —
  that's the actual next action, not yet a completed step despite being
  presented.

**Next steps:**
1. Type in and compile the bloom tuning parameters (Phase 2 step 1).
2. Then: runtime `CurrentBloom` state + decay via `WeaponBase::Tick`, the
   cadence-penalty behavior, and a temporary on-screen bloom readout.

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
