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
- **No character names in the build (2026-11-08):** "dont use Navarro as a name yet, that is
  subject to change still". Code, assets, tags, labels and bindings say `Player` (or describe the
  role), never the lead's name. The lore notes keep the name as design canon.

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
- **Building dressing (2026-11-04):** these now count as building: downpipes, wall
  air conditioners, overhanging rooms, plywood and tin patches, door steps and vent
  blocks ("There are alot of blank face tiles so I want them to see more"). "The
  hollow block faces can remain empty." Everything else stays out until asked for.
- **Patches (2026-11-04):** real sheet size, not small boards ("the patches look out of
  place, maybe if you scale them bigger"). Wood goes at least two side by side, tin can be
  single ("place atleast 2 beside each other", "except the roof type, the wood one, yes do 2").
- **Pipes (2026-11-04):** "for pipes, never 2 on the same house". Never overlapping another
  pipe ("theres also a pipe that overlaps with another pipe").
- **Stairs (2026-11-04):** no dressing on the walls the stairs run against ("some of your patch
  placements and vent placements go into the stairs").
- **Vents (2026-11-04):** same height across a face ("align them if they are on the same
  face", "atleast the same height").
- **Thin walls (2026-11-04):** no vents or air conditioners on them, and no other dressing
  ("this wall section needs no vents, its just a wall divider", "That bit is a thin wall,
  not a house").
- **Overhanging rooms (2026-11-04):** a door on the wall behind ("looks like nothing leads to
  their right now").
- **Laundry (2026-11-04):** now counts as building, and must stay cheap at a distance ("start
  adding laundry hang, but keep it cheap if its far away"). Only where somebody could reach it:
  "keep the laundry stuff on balconies , or near reach of a window on the second floor. or near
  the doors. never out across the street, if it crosses the street, then make sure its on the
  second floor".
- **Street dressing (2026-11-05):** now counts as building: wires, meter boxes, water tanks, aerials,
  bulbs, tubes and street lamps with their lights, shutters, gates, tarps, signs, window sills, rebar
  and peeling-paint decals ("do all that and add it to the tool"). The decal rule above now allows
  peeling paint too. Signs stay blank until the user gives wording. Loose props (plants, LPG tanks)
  stay out until asked for.
- **Fill under directional lights (2026-11-09):** "rule on directional lights, always put a point light that is shadowless, like ambient light
  around the source, light never just travels in one direction", "bonus if you can have it cast shadow but very very mild". Every spot light
  (any light that shines one way) gets a point light at its source: about 12% of its intensity, half its reach, a 40 cm source so its shadows
  are very soft and faint. Generated in `street.py` `_light()` (`FILL_*`); placed by hand lights need one too.
- **Signs (2026-11-05):** long rectangular boards only. "dont use the square signage, use the longer
  rectangular ones, square signage may fit chinese charachers but not alpha numberics".
- **Power lines (2026-11-05):** lots of them, in heavy bundles ("add more power lines, power lines are a
  big identity show for the philippines"; a photo of a Manila alley as the reference). They have to be seen
  from the ground, so a low layer crosses at the top of the ground floor, never under 3 m.
- **Daylight (2026-11-05):** "I will keep this level on daylight so the lights should be off". Bulbs, tubes and
  street lamps stay as fittings, unlit, with no light actors (`STREET_LIGHTS_ON`).
- **Posters (2026-11-05):** the user's 24 AI-generated images are placeholders ("I might decide to use them
  but we will see"), so they stay on one switch and in one folder, and the images are never edited. Scale from
  the user's photo of a Manila wall ("look at this scale, use this for the poster"; "the posters are tiny"):
  sheets about 61 x 91 cm, edge to edge in blocks up to the trim, never smaller, a little bigger now and then.
  "the material is bright even in shade": capped at the wall paints' brightness. Hollow-block faces take them
  (2026-11-06, below). Only candidates repeat: "only put together indentical posters for candidates type posters, you
  can put movie posters together side by side but not the same over and over, same goes for product ads".
- **Face edges (2026-11-05):** posters, shutters, signs, meters, tarps and gates stay 40 cm from the ends of a
  face ("some of your placements are too close to the edge of the face"; "Yes, apply it").
- **Door tarps (2026-11-06):** "dont put a tarp on the doors". Tarps go on plain wall only.
- **More building dressing (2026-11-06):** power poles and their lines, tyres on roofs and water meters at the foot of a wall now
  count as building ("do the building centric ones first"). Ground dirt, variations and dressing come next.
- **Water meters (2026-11-06):** spread across the whole level, not bunched ("the water meter needs to be distributed more").
- **Graffiti (2026-11-06):** only the user's own 10, in `/Game/Project_Bopis_Graffiti_Decals`, with the images untouched ("added 10
  graffitits"). The decal rule above now allows them. Not on thin walls, not over posters, doors or windows.
  Solid paint, not faded ("the warning and tag decals are to faded").
- **Ground-floor walls (2026-11-06):** "Try to not have any first floor walls featureless, except hollow block,
  which yu can put posters on." Hollow-block faces still take no other dressing, and stair walls and thin walls
  keep their own rules. No open shop fronts either ("the wall if open"). Vents up high don't count as dressing
  the wall: "even this is bare, it has vents but needs something".
- **Collision (2026-11-06):** "fix them all, but keep the awnings solid, wires stay no collision". Pieces marked
  `nocoll` have no collision, and awnings are solid. Posters block only the `Paper` trace, so a shot hits the wall
  behind ("use the wall's impact and sound"). Wall patches stop shots and play their own surface, wood or metal
  (2026-11-07: "the sheet metals and wood on the walls are not playing the correct impact").
- **Surfaces (2026-11-06):** "do a physics material pass, some of them are using the wrong materials from what I can
  see from sounds and impacts". A piece's surface follows what it looks like. Check what a material really reports, not
  its name or its own setting, and look at its texture by exact path before deciding.
- **Graffiti on hollow blocks (2026-11-06):** allowed, and big: "yes do grafitti on hollow blocks, actually allowed to paint them big". Crew tags on the
  bare upper storeys, as posters hold the ground floors.
- **Bigger posters (2026-11-06):** "The posters are generally tiny", "Ads and campaign material needs to be seen from further away", "find a way to scale the posters
  more". This replaces the 61 x 91 cm sheet as the size: that's now the floor, used only where a stretch of wall or a band can't take more.
- **Behind posts (2026-11-06):** nothing pasted or painted on a wall with a post standing close in front of it: "there is no way he was able to stick that behind the post".
- **The ground (2026-11-06):** surfaces, ground dirt decals and litter now count as building ("Next step is ground dirt, variations and dressings", "Do the ground pass after"). The
  decal rule above now allows ground dirt too. Litter has no collision, except the trash bags (2026-11-07, below). Plants and LPG tanks stay out until asked for.
- **Things people use (2026-11-06):** these now count too: "wooden bench-stools, plastic seats and tables in some areas. Buckets, potted plants on the balconies". In some areas, not everywhere. Pots go on balconies, and along walls near doors ("put some potted plants along the wall near doors where you can"). Rice sacks only on balconies ("move the ricebags to the secured balconies"). Furniture stays clear of walls ("one of the chairs is into the wall too").
  LPG tanks stay out until asked for. Seats go near doors: "monobloc stool 02 is a chair, not a table", "use the chairs near doors". No piece stands in for something it plainly isn't.
- **Physical props (2026-11-07):** light things only are physical, and bullets move them: "I want bullets to affect them, some props like the filled bucket need to be static. weld them if they are
  separate pieces, dont affect navigation. as you suggested, only light things". Nothing physical, and no prop at street level, starts touching anything else: "make sure whatevr is a physical
  object does not overlap initially to any other object, i saw a bucket overlapping pipes earilier". The trash bags are physical too: "do the trash back with physcics as well if you are not
  already" (2026-11-07). So are the pots, with their plants riding them: "The pots dont get physics", "the pots and bags dont even collide". Physical pieces are capped: "the chairs go
  flying when you walk to them. cap their velocity".
- **Chair colour (2026-11-07):** a monobloc piece's colour never changes as it moves: "the monobloc MI for chair 1 (not 1b) has code that changes his color in realtime, so you cant use that one";
  "code the material so it does not regenerate the color if moved? only generate on spawn time". The colour is picked once, from a seed stored on the piece.
- **Gates (2026-11-07):** "this door is backwards and not in contact with the wall", of a steel gate hung frame-out and off the wall. A gate shows its plain sheet to the
  street, with its frame against the wall.
- **Business signs (2026-11-07):** "Project_Bopis_Local_Business_Signs Added, use this for new posters (add, dont replace the ones already there), then add the signage to
  the apprpriate signboards". Its posters join the old ones in the poster pool. Its wall boards go on sign boards, each once, where the place fits the trade (shops over
  shutters, the barber and the tailor over house doors) and where they can be read. A sign with no board stays blank. The images are never edited.
- **Road repairs (2026-11-06):** darker than the road, never lighter: "avoid these strips are too bright, if you are going to put something like this, then keep them darker".
- **No square grates (2026-11-06):** "metal square grates are not common in the ph". No square drain plates or mesh plates. Round manholes stay.
- **Dirt against walls (2026-11-06):** "Your decal alignment for the Dirt decals to the edge of the houses are bad at the moment. They either go above to the floor lining OR they do not hit
  the edge at all"; "1rst one overshoots the house"; "the decal shoud be super thin and hit just about the surface of the road". A ground decal's dense edge lies just under the lining, only where
  there is lining, and its box stops about 1 cm above the road. The pours stay low enough for that.
- **Level names (2026-11-07):** arena levels end in `_Arena` ("this naming convention is what we will use to split Story vs Arena
  levels"). `Lvl_BackAlleys` is now `Lvl_BackAlleys_Arena`. A new arena level gets the suffix from the start.
- **No exits in arenas (2026-11-07):** "I dont want an exit trigger at all, the resets will be handled by the menu screen when
  it comes." No exit actor goes into an arena level. **Until the menu exists (2026-11-07):** a cleared arena restarts itself
  through its director ("Restart, no exit actor"), switched off once the menu screen handles resets.
- **Story levels (2026-11-08, `Lvl_01_Slum`):** the first one is `Lvl_01_Slum` ("LevelName is 01_Slum"; the `Lvl_` prefix was asked).
  - **Stair rails:** "The way you use the blocks for stair rails is absurd, remove immediately". No stacked blocks as stair balustrades.
  - **Interiors from the AsiaSlum demo:** "look at Demomap_AsiaSlum for interiors, it has a stair and rail setup". Stairs and rails
    follow that map's setup.
  - **Heights:** "the interiors are too tall (ceilings a bit too high)"; "The buildings in Section 1 have 3 storey levels which is
    unusually high".
  - **Hollow blocks:** "you are also using the wrong hollowblock material". Hollow blocks are always the user's texture
    (`MI_BackAlleys_HollowBlocks` on tiles, its world-mapped twin `MI_BackAlleys_HollowBlocks_World` on box walls), never the
    procedural `MI_BackAlleys_CHB_Bare`.
  - **One compound:** "this entire area, aside from Section 1 and 2 are all a single compound", "the slum generator is useless here
    besides those 2 sections", "keep those as houses. the compound starts where you drop from there". Slum houses only along the
    main street and the eskinita.
  - **Compound walls:** "The yard should just be 1 storey walls around it, push these buildings back so they look like distant
    buildings"; of the alleys, "we are inside the compound, It does not make sense to have residential houses leading into it".
    Inside the compound, open ground is walled (one storey), with the buildings set back behind the walls.
  - **Handcrafted from 2026-11-09:** "I think this is something beyond automated generation. I have to handcraft some of these."
    The user edits `Lvl_01_Slum` by hand from here. Never rebuild, re-place or delete it (or its `01_Slum` sublevels) from the
    generator (`build_story_ue.py`, REBUILD, bridge placers) without the user saying so for that change: it would wipe their work.
    Generated pieces go into new sublevels or a separate map unless asked otherwise.
  - **Sections 1-2 regenerated (2026-11-09, on the user's say):** "first do passes on Sections 1 and 2", and of the map "the only edit was
    the wall drop". Put in with `swap_sections_ue.py` (headless, editor closed), which touches only what it names.
  - **Unaligned houses:** "makes sure that each house is unaligned with the adjacent house". No slum house front lines up with its
    neighbour's.
  - **Streets:** "we need a curb and actual street". A concrete road in panels and a raised sidewalk along the house fronts, its curb
    capped ("cap the curb edge").
  - **One map, sections as tags (2026-11-09):** "I would rather not have them as sublevels at this point if you have to add them headless
    everytime", "only if we can still do Sections 1-7 split even without sublevles". `Lvl_01_Slum` is one map; every actor carries its
    section as a tag (`S1`-`S7`), so the map can be split by tag when streaming is built. Pieces go in through the bridge, tagged.
  - **Curb stones:** the main border stone (`SM_MainBorder_04`), not a box ("its too sharp edged, you should be using the main border stone").
  - **Main road clearance (2026-11-09):** "section 1 is a main road, it needs the power cables a bit higher. Trucks should be able to pass
    through". Nothing hangs under 5 m over the main road's carriageway (`ROAD_CLEAR`); the 3 m low layer stays in the eskinitas only.
  - **AsiaSlum cables (2026-11-09):** alongside the generated thin wires, never instead ("dont eliminate using the current ones, I just think
    those fit better in some instances"). Bundles on ring brackets along facades and across the street, trunks between poles.
  - **Ways through stay clear:** "your placement keeps blocking the drop so I cant proceed and you also added a wall at the entrance of
    the eskinita and I can't go through". Nothing across a drop, an alley mouth or any other way the player has to take.
  - **Section 4 baseline (2026-11-09):** "the doorways are two doors wide, I need it only 1 door wide except for the broken down
    wall". Doors are one leaf wide; knocked-through walls stay wide.
    - **Assets, not cubes:** "I also need sils or door frames, see if we have any assets that would work. You have been adding Cubes
      to fill the space, we should be using what assets we have instead". Frames, jambs and sills come from the packs.
    - **Jalousies:** "we need 2 of them facing both sides of the room, outisde and inside". Every jalousie shows on both faces.
    - **Stairs:** "I changed the stairs at the bottom of the last section, conform to that when making stairs for section 4". New
      stairs follow the user's `TRAP_Stair3`: steep kit flights, each one step down the last, anchored at the top.
    - **Doors swing both ways:** "Max Payne 1 system should work, it opens both ways, whichever side anyone is pushing through".
    - **Knocked-through walls:** rubble "around the door frame" ("Yes, dress them"): broken edges round the hole and a heap of
      debris at its foot on each side. White, not red ("make it white not red").
    - **Eskinita E3's wall (2026-11-09):** the hollow-block wall runs its whole north edge, capped ("extend the hollow block wall all
      the way", "put a cap on it too"). Garbage drums are solid ("drums have no collisions").
  - **Street lights (2026-11-09):** "Street lights are in someones balcony, that cannot happen". A lamp's arm reaches out over open
    ground only: never into a balcony, a terrace or over a lower roof. Lamps go on the power poles too ("reevaluate placement").
  - **Walls stay inside (2026-11-09):** no inside wall shows on the outside ("the inside walls ... penetrates to the outside yard"),
    and nothing from a lower storey shows through a floor ("the walls below are pushing through the cieling"). No recess where a
    floor meets a wall, and no streaked slab edges ("the cubes you are using has messed up UVs on one side").
- Read `Tools/LevelGen/LESSONS.md` before every level build. Run
  `Tools/LevelGen/analysis/check_overlaps.py` after every generator change
  (no coincident faces), and `analysis/check_dressing.py` after every dressing change.
