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

## 2026-08-31
**Summary:** Projectile polish session — self-collision fixed properly,
projectile spawn origin moved to the crosshair, and impact decals added
(with a real bug found along the way). Also ran the first **live PIE
measurement** using the editor bridge, which disproved two standing
theories rather than confirming them.

**Live PIE measurement — a genuinely new capability.** The `unreal-mcp`
bridge can start/stop PIE (`StartPIE`/`StopPIE` with a warmup delay),
find actors in the running PIE world (`find_actors` — refPaths look like
`.../UEDPIE_0_Lvl_FirstPerson...`), read live actor transforms
(`get_actor_transform`), read socket transforms off mesh assets, and
capture the editor image. That means weapon-positioning questions can be
answered with **numbers instead of screenshot guesswork** — which is how
the earlier grip-offset attempts failed. Note `CaptureEditorImage`
returns base64 too large for a tool result; decode the saved result file
to a .png and read that instead.

**Theory disproven: the TEMP 5s re-snap timer is not causing weapon
misposition.** Measured the rifle's world transform ~1s into PIE and
again after the 5s timer fired: `(30.8, 13.0, 355.8) yaw -71.97` vs
`(31.2, 13.4, 356.4) yaw -71.80` — identical within idle-animation sway.
The re-snap changes nothing measurable. (The timer is still in
`BeginPlay` and still unnecessary; removing it is now a cleanup task, not
a fix.)

**Theory disproven: "correct the 72° grip yaw."** The weapon's world yaw
sits ~72° off the camera's facing with `GripRotationOffset` at zero. I
took that as an error, set `GripRotationOffset` yaw to 72, and measured
the result — world yaw went to `-0.06`, i.e. numerically "aligned". But
the user checked it visually and it was **wrong**: you ended up sighting
down the side of the receiver. Reverted to zero. **Lesson: the weapon
mesh's local +X is not its barrel axis**, so "align local +X with the
view" is not the same as "point the gun forward" — and by extension the
muzzle-position maths derived from that assumption was also wrong. Don't
re-derive muzzle position from the actor transform; measure the socket's
world transform directly if it's ever needed again.

**Fixed: projectiles hitting the firer.** First attempt used
`IgnoreActorWhenMoving` on the instigator/owner plus actor comparisons in
`OnHit` — **not sufficient**, rounds still detonated on the player.
Replaced with an explicit ignore list on `AProjectileBase`:
- New `IgnoredActors` array + public `AddIgnoredActor()`.
- `AddIgnoredActor` ignores **in both directions** — the projectile's own
  movement sweeps ignore that actor, *and* that actor's root component
  ignores the projectile. The one-way ignore was the hole: the other
  side's sweep could still generate the blocking hit.
- `AWeaponBase::FireProjectile` now calls `AddIgnoredActor` explicitly
  for instigator/owner/self right after spawning, so it doesn't depend on
  `Instigator` being wired correctly. `BeginPlay` still does its own pass.
- `OnHit` early-returns on ignored actors **before `Destroy()`**, so a
  stray self-hit passes through rather than consuming the round; the
  fragment burst consults the same list.

**Changed: projectile spawn origin → dead centre on the crosshair.**
Reverted the 2026-08-30 muzzle-socket spawn. `FireProjectile` now spawns
at `TraceStart` (the deprojected crosshair point) along `SpreadDirection`
— the same origin `FireHitscan` uses, so projectile and hitscan weapons
agree exactly on where shots go, bloom applies identically, and the
weapon's grip orientation stops mattering for trajectory entirely. This
only became viable once the self-collision fix landed, which was the
original objection to spawning at the camera. Visual tradeoff accepted:
rounds originate at the eye, not the barrel; if that ever reads badly the
fix is cosmetic (muzzle flash/tracer at the socket, real projectile on
the crosshair).

**New: projectile impact decals** — `HitDecalMaterial`, `DecalSize`,
`DecalLifeSpan` on `AProjectileBase` under a `Projectile|Impact`
category. Put on the projectile rather than passed down from the weapon,
matching how `FragmentRadius`/`FragmentDamage` already live there: the
projectile owns its impact behaviour.

**Real bug found and fixed: decals only appeared on some surfaces.**
Initially looked like a decal *facing* problem, and the first instinct
(surface `bReceivesDecals` settings) was wrong too — ruled out by the
user's observation that **hitscan decals worked fine on the same
surfaces**, so it had to be the code path. Root cause: the projectile
passed `Hit.Location` where it should pass `Hit.ImpactPoint`.
- `ImpactPoint` = the point on the surface that was struck.
- `Location` = where the *querying shape's origin* ended up.
- For a line trace (zero-thickness ray) these coincide — which is why
  hitscan was never affected.
- For a **swept sphere** the shape stops when its surface touches, so its
  centre is still one radius out. `CollisionComponent` is
  `InitSphereRadius(5.0f)`, so the decal spawned 5cm off the surface.
- A decal is a **projection box**, and `DecalSize.X` is its projection
  depth — also 5. So the box reached exactly as far as the gap, leaving
  the surface right on the boundary: whether it painted came down to
  angle, curvature, and float precision. Hence "only certain surfaces".
- **General rule:** use `ImpactPoint` for anything placed *on* a surface
  (decals, impact FX, scorch marks); reserve `Location` for where the
  moving object actually ended up (stuck projectiles, ricochet origins).

**Still open (carried forward):**
- **Muzzle flash always faces north** — untouched today. See the
  2026-08-30 (7) entry for everything already ruled out; next check is
  the AnimNotify's Attached/Socket Name.
- The TEMP 5s re-snap timer — now known to be doing nothing useful;
  remove it.
- Weapon grip position: the rifle renders far too close/large to the
  camera (weapon origin only ~31cm out), and the hand pose still doesn't
  grip properly. Untuned `GripLocationOffset`.
- Decal roll is undefined on floors (`FVector::Rotation()` gives an
  arbitrary yaw for a straight-up normal) — cosmetic, and worth solving
  together with decal variation (task #39) via a random roll.
- The fragment sweep still uses `Hit.Location`; harmless at a 150-unit
  radius, but `ImpactPoint` would be consistent.
- Rifle arm animations, battle rifle, reload/ammo system.

---

## 2026-08-30 (7)
**Summary:** Big session. Fixed the weapon-position bug for real (twice —
two genuinely different root causes), built a fire-rate system from
scratch, implemented full-auto, and configured the close-range rifle
end to end. First session using the `unreal-mcp` editor bridge, which
changed what's possible — Blueprint creation/configuration now happens
directly instead of via step-by-step editor instructions.

**New capability: the `unreal-mcp` editor bridge.** Earlier in this
session I told the user I *couldn't* configure `BP_Pistol` because
`.uasset` files are binary and no editor automation was connected. That
became wrong mid-session when the `unreal-mcp` server connected. It
exposes toolsets for Blueprints (create/compile/get CDO/set parent),
Objects (read/write properties incl. Blueprint class defaults), Assets
(find/move/save/referencers), SkeletalMesh (sockets/bones), Logs, and
more. **Known limits found by testing:** it can NOT reach a Cascade
particle system's `Emitters` array (so no access to per-emitter Required
modules / "Use Local Space"), and can NOT read an AnimSequence's
`Notifies` array. Editor-side work on those still has to be manual.

**Weapon position bug — root cause #2 (the real one this time).**
Entry (1) today logged the `SetFirstPersonPrimitiveType()` setter fix.
The symptom came back anyway. Diagnosis this time: a **mistimed attach** —
`EquipWeapon` runs from `BeginPlay`, before the arms mesh pose/socket
transform is valid, so the weapon snaps to a socket that isn't where it
ends up. Confirmed by a deliberate test the user proposed: re-run the
attach 5s after start and see if the position corrects. It did.
- Refactored the attach block out of `EquipWeapon` into a new
  `UWeaponHolderComponent::AttachWeaponToHand()` so the normal path and
  the test path run identical logic.
- **A TEMP debug timer in `BeginPlay` still calls it at 5s and is
  currently what makes the position correct.** This is a band-aid, not a
  fix — the weapon sits wrong for the first 5 seconds of every session.
  Proper fix (attach after mesh init rather than on a fixed delay) is
  still TODO.

**Live Coding bit us again, exactly as documented.** After the
`AttachWeaponToHand` refactor the position fixed but *firing broke*.
Log showed `LogClass: UClass WeaponHolderComponent Reload.` /
`Re-instancing WeaponHolderComponent after reload.` / the familiar
`LogLiveCoding: Warning: Live coding succeeded, data type changes...`.
The C++ diff didn't explain a firing failure; the re-instancing did. Full
Rebuild Solution fixed it. Reinforces the existing Gotcha — structural
changes need a rebuild, and the Output Log names the problem directly.

**New: weapon fire animation (`FireAnimation` on `WeaponBase`).** An
`UAnimSequence` played on the weapon's *own* mesh via
`WeaponMesh->PlayAnimation()` when `bUseAnimationDrivenFeedback` is true.
Checked against the 2026-08-18 architecture rule and it does **not**
violate it: that rule is about skeleton-specific data for *whoever holds*
the weapon; an animation authored against the *weapon's own* skeleton is
the weapon's own data. Requires mesh and animation to come from the same
family — `BP_Pistol` only works because its mesh was switched to
`Darkness_Pistol`, matching `Fire_Pistol_W`'s skeleton.

**New: fire-rate cap (the "I can rapid tap" fix).** Two properties now,
deliberately distinct:
- `TimeBetweenShots` — hard mechanical cap, seconds. Enforced by a new
  `CanFire()` checked at the top of `Fire()`.
- `IntendedTimeBetweenShots` — renamed from `IntendedCadence`, now also
  in seconds (user's call, for consistency). The softer accuracy limit;
  firing sooner adds the bloom penalty.
- **They must differ.** If the hard cap equals the intended interval the
  bloom cadence penalty becomes unreachable dead code. The gap between
  them is the Reach-style window: fire faster than comfortable, pay in
  accuracy, but never beyond the mechanical limit.
- Gate lives in `Fire()`, not in the character, so every caller
  (including future AI) inherits it.

**Follow-up bug: the gate stopped shots but not the animation.**
`DoFire()` played `FireMontage` unconditionally, so rapid-tapping still
*looked* like rapid fire. Fixed by making "did it actually fire?" flow
back up: `AWeaponBase::Fire()` and
`UWeaponHolderComponent::FireEquippedWeapon()` both now return `bool`,
and the montage is gated on that. `CanFire()` stays the single source of
truth — the character just asks whether the shot happened.

**New: full-auto.** `FireAction` now also binds `ETriggerEvent::Triggered`
→ new `DoFireHeld()`, which early-returns unless
`GetFireMode() == Auto` (new getter, `FireMode` was protected). It just
calls `DoFire()` every frame and lets the fire-rate cap do the pacing —
which is why the rate limiter had to land first. The press frame fires
both `Started` and `Triggered`; the second is harmlessly rejected by
`CanFire()`.

**Close-range rifle configured end to end (via the bridge).**
- Created `BP_RifleProjectile` (`ProjectileBase` subclass). Kept the C++
  defaults — 3000 u/s (~30 m/s, genuinely watchable/dodgeable at its 25m
  range), no gravity, 5s lifespan, 150-unit fragment burst at 10 damage.
- Renamed `BP_TestWeapon` → **`BP_CloseRangeRifle`** (nothing referenced
  it, so the rename was clean). Mesh `Darkness_AssaultRifle`,
  `FireAnimation` `Fire_Rifle_W` (skeleton-matched), `FireSound`
  `RifleA_Fire01`, `ProjectileClass` → `BP_RifleProjectile`, full stat
  row applied, `FireMode Auto`.
- Final values — pistol: `TimeBetweenShots 0.125` /
  `IntendedTimeBetweenShots 0.2`, Semi. Rifle: `0.083` / `0.1`, Auto,
  15 damage, 2500 range.
- `StartingWeaponClass` switched to `BP_CloseRangeRifle` for testing.

**Fixed: projectiles spawned from behind the player.** `FireProjectile`
was spawning at `TraceStart` — the deprojected screen point, i.e. the
camera — so rounds flew out of the player's face. Now spawns at the
`Muzzle` socket (verified to exist on `Darkness_AssaultRifle`) and aims
at the point the camera-based shot would have hit, so it still converges
on the reticle instead of flying parallel to the view. Hitscan
deliberately still uses `TraceStart` — that's what makes it land dead-on
the crosshair.

**OPEN BUG — for tomorrow: muzzle flash always faces north.**
Not yet fixed. What's established:
- It is **not** coming from our C++. Both weapons have `MuzzleFlash: None`
  and `bUseAnimationDrivenFeedback: true`, so `SpawnEmitterAttached()`
  never runs. The flash comes from an **AnimNotify** inside the
  SciFiWeapDark fire animation.
- **"Use Local Space" is already enabled** on all emitters — the user
  checked. So the usual Cascade explanation is ruled out.
- Next thing to check: the notify's own **Attached** checkbox and
  **Socket Name**. An unattached `PlayParticleEffect` notify spawns at a
  world location with identity rotation, which matches the symptom
  exactly.
- I could not inspect this myself — the bridge exposes neither
  AnimSequence `Notifies` nor ParticleSystem `Emitters`.
- **Proposed fix if the notify turns out to be correct too:** split
  `bUseAnimationDrivenFeedback` into `bAnimationDrivenSound` and
  `bAnimationDrivenMuzzleFlash`. One flag currently governs two unrelated
  things; the pack's animations drive sound well but its flash notify
  doesn't suit our rig. Splitting lets us keep the notify's sound and take
  code control of the flash, socket-attached and correctly oriented.
  Discussed and agreed as the fallback, not yet implemented.

**Also still open:**
- The TEMP 5s re-snap timer (above) needs replacing with a real fix.
- Rifle arm animations — the rifle currently plays `AM_Pistol_Fire` for
  the arms, since the character's `FireMontage` is still the pistol's.
  `MM_Rifle_Fire` exists in the Lyra set for this.
- Battle rifle not started.
- Stale constructor comment: `FirstPersonMesh`'s offsets are described as
  "intentionally left at zero... needs visual tuning," but
  `FirstPersonScale` is now `0.6f` — the clipping fix was applied at some
  point, so that comment may no longer be accurate.

---

## 2026-08-30 (6)
**Summary:** Investigated the returning "misaligned pistol" report. Found
one solid, checkable fact that changes the diagnosis, but **did not fix
it** — I could not converge on correct grip values by screenshot-driven
trial and error, and stopped rather than keep guessing. All experimental
changes reverted; the project is back to its post-(5) state.

**The finding that matters: this is not caused by the `BP_Pistol` swap.**
I put `BP_TestWeapon` back as `StartingWeaponClass` and played it — it
shows the **same** misalignment as `BP_Pistol` (weapon oversized, barrel
pointing screen-left instead of forward, hand not wrapped on the grip).
So swapping the starting weapon to a new mesh in entry (5) did not cause
this, and re-pointing `StartingWeaponClass` back at `BP_TestWeapon` will
not fix it. Whatever it is, both weapons have it.
Reference captures kept in the session scratchpad:
`ref_test_crop.png` (BP_TestWeapon) vs `fpflag_crop.png` (BP_Pistol) —
they are near-identical.

**Second finding, unverified but real: a first-person render-flag
asymmetry.** The arms (`First Person Mesh`) carry
`FirstPersonPrimitiveType = FirstPerson` **baked in as a component
default** on `BP_FirstPersonCharacter`. Both weapons' `WeaponMesh` default
to `None` and depend entirely on the runtime
`SetFirstPersonPrimitiveType()` call in
[`WeaponHolderComponent::EquipWeapon`](../Source/ProjectBopis/Weapons/WeaponHolderComponent.cpp#L97)
to join the first-person render path. That is exactly the fragility behind
the original 2026-08-30 render-proxy bug, and it is still structurally
present — the weapon reaches the FP path only if a runtime call lands at
the right moment, while the arms never depend on timing at all. Setting
the flag as a component default on the weapon Blueprints (pure data, no
code) would remove that dependency. **I did not leave this change in** —
it visibly altered the render but I could not demonstrate it was an
improvement, so it is reverted and left as a recommendation.

**What I could not settle.** The weapon's orientation relative to the hand.
`GripRotationOffset` is applied as a rotation relative to the *attach
socket's* axes, not world axes, so its `pitch`/`yaw`/`roll` do not map to
anything intuitive from a screenshot. Probes: `yaw 0` → barrel points
screen-left; `yaw +90` → points screen-right; `yaw +45` → still right;
`yaw -90` → still left. Never forward. `GripLocationOffset` was calibrated
though — **`+X` moves the weapon left/away from the hand, so `-X` brings it
toward the hand.**
Also checked and ruled out as the cause: the two meshes are not
interchangeable in size (`Darkness_Pistol` is ~1.6x `SKM_Pistol` by bounds,
and its geometry sits ~9.7cm further along +Y from its pivot), but since
`BP_TestWeapon` misaligns identically, mesh size is not the bug.

**Also learned:** `SKM_Manny_Simple` ships purpose-authored `HandGrip_R` /
`HandGrip_L` sockets (`HandGrip_R` is on `hand_r`, offset
`(-7.01, 2.05, 0)`, yaw `+90`). `WeaponAttachSocketName` defaults to the raw
`hand_r` **bone**, bypassing them. Attaching to `HandGrip_R` instead is a
one-property, no-code change and is worth trying, but it did not obviously
fix orientation in my tests, so it is reverted too.

**Open Questions / Next Steps:**
1. **Grip tuning is a by-eye job and should be done interactively** — drag
   the weapon's transform in the Details panel during PIE (the same way the
   scale-nudge test was done for the original render-proxy bug) rather than
   through blind offset guesses. Once values look right, put them in
   `BP_Pistol`'s `GripLocationOffset`/`GripRotationOffset`.
2. Worth answering first, since it reframes everything: **did
   `BP_TestWeapon` ever actually look correct in the possessed first-person
   view, or only when unpossessed?** If it never looked right possessed,
   this is not a regression at all — it is the untuned-grip work that Phase
   4 always had queued, and the "bug" framing is wrong.
3. Consider making `FirstPersonPrimitiveType = FirstPerson` a component
   default on the weapon Blueprints (see above).
4. Unchanged: `BP_Pistol` still not validated in PIE; debug `RelLoc`/`RelRot`
   readout still in `WeaponBase::Tick`; Phase 4 still uncommitted.

---

## 2026-08-30 (5)
**Summary:** `BP_Pistol` created and fully configured — the first Phase 4
weapon-config item is done. The headline is *how*: the UnrealMCP bridge
turns out to expose full editor control, so this was done directly rather
than as an editor-UI walkthrough.

**The MCP finding — supersedes the 2026-08-30 (3) note.** That entry
recorded that `unreal-mcp` "exposes only an `AgentSkillToolset` … no editor
or Blueprint control of any kind," and told future sessions not to switch
sessions expecting a different answer. **That is no longer true**, and the
reason is the (4) entry's own fix: the toolsets are registered by the
running editor, so with the server actually started (`ModelContextProtocol.StartServer`)
the bridge now lists 17 toolsets, including `BlueprintTools` (create,
set_parent, compile, CDO access, full graph editing), `ObjectTools`
(list/get/set properties on any object or CDO), `ActorTools` (components),
`AssetTools` (find/save/move/delete), `SkeletalMeshTools` (sockets, bones,
materials), plus scene, material, data-table and texture toolsets. In other
words `.uasset` configuration **is** scriptable from here. The (3)
conclusion was correct about what it saw and wrong about why — it was
reading a dead server, not a limited one.

**Done — `BP_Pistol` (`Content/FirstPerson/Blueprints/BP_Pistol.uasset`):**
- Created parented to `AWeaponBase`, `WeaponMesh` → `Darkness_Pistol`.
- Stats applied from the queued table: `BaseDamage` 25, `MaxRange` 5000,
  `FireMode` Semi, `bHasZoom`/`bIsProjectileWeapon` false,
  `bUseAnimationDrivenFeedback` true, and the bloom five —
  `BaseSpreadAngle` 0, `MaxSpreadAngle` 3.0, `BloomPerShot` 0.12,
  `BloomDecayRate` 0.8, `BloomDecayDelay` 0.25, `IntendedCadence` 5.
  Verified by reading them back off the CDO after compiling.
- `HitDecalMaterial` → `MI_Generic_1` and `FireSound` → `PistolA_Fire01`,
  both mirrored from `BP_TestWeapon`. The sound is inert while
  `bUseAnimationDrivenFeedback` is true (that flag suppresses code-driven
  sound *and* muzzle flash), but setting it now means flipping the flag
  later needs no second pass.
- **`MuzzleSocketName` is no longer a guess.** `Darkness_Pistol` has
  exactly one socket and it is named `Muzzle`, so the `WeaponBase` default
  is correct for this weapon. The other two weapons still need the same
  check against their own meshes.
- Compiled clean with `warnings_as_errors`, saved to disk.

**Also changed:** `BP_FirstPersonCharacter`'s `WeaponHolder.StartingWeaponClass`
swapped `BP_TestWeapon` → `BP_Pistol`, so the configured pistol is what
actually spawns in hand. `BP_TestWeapon` was still using the *template's*
`SKM_Pistol` mesh (not `Darkness_Pistol`), and it's slated to become the
close-range rifle next, at which point leaving it as the starting weapon
would hand the player a rifle with no rifle animations. One property,
trivially reversible.

**Decided:** the queued stat table is now recorded in
`GameDesignDocument.md`'s Combat implementation notes, explicitly marked
**Claude-proposed starting values, not design canon**. That closes open
question 1 from the (4) entry — not by getting design input, but by writing
the provisional numbers down where they can be argued with.

**Open Questions / Next Steps:**
1. **`BP_Pistol` has not been PIE-tested.** Everything above is verified by
   reading properties back, not by firing the gun. Worth a play test before
   moving on — specifically that the pistol appears in hand, that
   `AM_Pistol_Fire` plays on fire (the animation-driven feedback path), and
   that grip offsets need tuning (they're still zero).
2. Still open, unchanged: remove the debug `RelLoc`/`RelRot` readout in
   `WeaponBase::Tick` (slot `2`, dereferences `WeaponMesh` unguarded).
   Left for the user to type, per standing preference.
3. Still open: **none of Phase 4 is committed** — `ProjectileBase.h`/`.cpp`
   untracked, plus the new `BP_Pistol.uasset` and the modified
   `BP_FirstPersonCharacter.uasset` now on top of it.
4. Next plan item: repurpose `BP_TestWeapon` into the close-range rifle
   (`Darkness_AssaultRifle`, full-auto, `ProjectileClass` → `AProjectileBase`
   subclass). Now that the bridge works, this should be quick.

---

## 2026-08-30 (4)
**Summary:** Cleared both blockers standing in front of `BP_Pistol`
configuration — the "missing" fire montage (a false alarm) and the dead
UnrealMCP bridge. No code or Blueprint changes yet.

**Done:**
- **Fire Montage blocker closed — the 2026-08-30 (3) audit finding was
  wrong.** That audit reported "no `AnimMontage` asset anywhere in
  `Content/`" and flagged the staged deletion of
  `MM_Pistol_Fire_Montage.uasset` as needing a decision. The montage
  actually in use is
  `Content/Characters/Heroes/Mannequin/Animations/Actions/AM_Pistol_Fire.uasset`
  — it came in with the Lyra migration, under the still-untracked
  `Content/Characters/Heroes/` tree. The sweep only matched the
  `*_Montage` filename pattern and missed Lyra's `AM_` prefix. User
  confirmed the `MM_Pistol_Fire_Montage` deletion was **deliberate**;
  `AM_Pistol_Fire` supersedes it. `bUseAnimationDrivenFeedback = true` on
  `BP_Pistol` is correct as specced — nothing needs recreating.
  Corrected in `ProjectPlan.md:113`.
- **UnrealMCP bridge diagnosed and started.** It is *not* a separate
  Python server — it is Epic's engine plugin `ModelContextProtocol`
  (`UE_5.8/Engine/Plugins/Experimental/`), already enabled in
  `ProjectBopis.uproject`. Defaults (port `8000`, path `/mcp`, name
  `unreal-mcp`) already match `.mcp.json`, and
  `Saved/Config/WindowsEditor/EditorPerProjectUserSettings.ini:4382`
  already had `bAutoStartServer=True`. Root cause of the connection
  refusal: auto-start fires once at `PostEngineInit`
  (`ModelContextProtocolEditor.cpp:64`), so an editor instance already
  running when that setting was ticked never starts it. Fixed live with
  the console command `ModelContextProtocol.StartServer` — no editor
  restart needed. Verified listening on `127.0.0.1:8000`.

**Decided:**
- `AM_Pistol_Fire` is the canonical pistol fire montage.

**Open Questions / Next Steps:**
1. **No numeric weapon spec exists.** `ProjectPlan.md` refers to a "queued
   weapon stat table," but the GDD only has the *property glossary*
   (§64–69) explaining what `BaseSpreadAngle`/`BloomPerShot`/
   `IntendedCadence` mean. There are no numbers for any weapon. The pistol
   spec is currently qualitative only: semi-auto, hitscan
   (`bIsProjectileWeapon = false`), `Darkness_Pistol` mesh,
   `bUseAnimationDrivenFeedback = true` → `AM_Pistol_Fire`. Everything
   else (`BaseDamage`, `MaxRange`, the five bloom values,
   `IntendedCadence`, grip offsets) needs either design input or
   Claude-proposed starting values flagged as non-canon.
2. Still open from the (3) audit, unchanged: remove the debug
   `RelLoc`/`RelRot` readout in `WeaponBase::Tick` (slot `2`, dereferences
   `WeaponMesh` unguarded); none of Phase 4 is committed yet.

---

## 2026-08-30 (3)
**Summary:** Doc-vs-code audit before starting weapon configuration. No code
changed; all four docs (`ProjectPlan.md`, `GameDesignDocument.md` + `.html`,
and this file) reconciled against the actual working tree. Found five pieces
of drift, two of which would have caused real confusion during the weapon
config work.

**First, on the MCP switch:** the previous entry moved to a new session
hoping an Unreal editor bridge would let Blueprints be configured directly.
`unreal-mcp` *is* connected here, but it exposes only an
`AgentSkillToolset` (listing/reading/writing skill files) — no editor or
Blueprint control of any kind. So `.uasset` configuration is still an
editor-UI walkthrough. Worth recording so a future session doesn't switch
again expecting a different answer.

**Drift found, in rough order of how much it matters:**
1. **The Fire Montage asset is gone.** `MM_Pistol_Fire_Montage.uasset` was
   committed in `230e3228`, has since been deleted, and the deletion is
   staged. A project-wide search finds **no `AnimMontage` asset anywhere in
   `Content/`**. Both `ProjectPlan.md` and the previous log entry describe
   the Fire Montage step as done and confirmed in PIE, and the queued stat
   table sets the pistol's `bUseAnimationDrivenFeedback` to `true` on the
   strength of it. That flag suppresses code-driven sound and muzzle flash,
   so with no montage to play, configuring the pistol as planned would
   produce a gun that fires with **no feedback at all** — and it'd look like
   a config mistake rather than a missing asset. The C++ side is fine and
   the source clip (`MM_Pistol_Fire.uasset`) still exists, so the montage
   can be rebuilt. **Not treated as a bug** — the deletion may well have
   been deliberate; flagged for the user to confirm.
2. **`FirstPersonScale` was never `1.0f`.** The 2026-08-30 entry below
   diagnosed camera/arms clipping as unaddressed because `FirstPersonScale`
   was "currently `1.0f` (a no-op)" and `FirstPersonFieldOfView` "matches
   the general gameplay FOV," and recommended dropping the scale to
   ~0.5–0.65. Both halves are wrong against the source, and were already
   wrong when written — these are *committed* values, not something changed
   since:
   [ProjectBopisCharacter.cpp:32-33](../Source/ProjectBopis/ProjectBopisCharacter.cpp#L32)
   sets `FirstPersonFieldOfView = 70.0f` and `FirstPersonScale = 0.6f`, both
   enable-flags true, and the camera's general `FieldOfView` is never
   assigned so it stays at the engine default `90`. The anti-clip mechanism
   is engaged, and the recommended range was already satisfied. If clipping
   still looks wrong, it needs re-diagnosing from scratch rather than
   starting from those two values.
3. **The camera/arms hierarchy restructure was never written down as a
   landed change.** The camera now attaches to the capsule and
   `FirstPersonMesh` attaches to the camera — inverted from the template,
   so the arms rigidly follow camera pitch instead of needing aim-offset
   blending. It's referenced obliquely in two places (the "superseded by the
   camera-attachment hierarchy restructure" aside below, and the Live Coding
   gotcha) but no entry ever described the change itself or why. Now
   documented in both the plan and the design doc. `FirstPersonMesh`'s
   relative transform is deliberately still zero and wants tuning by eye.
4. **Grip offsets landed undocumented.** `WeaponBase` has
   `GripLocationOffset`/`GripRotationOffset` with getters, applied in
   `EquipWeapon` right after the socket attach. This is the per-weapon hook
   the long-deferred hand-socket issue (#21) was asking for — so that issue
   is now "mechanism done, values untuned" rather than "not yet
   investigated." Tuning folds naturally into the three weapon-config tasks.
5. **Smaller things:** the temporary `RelLoc`/`RelRot` debug readout added
   to diagnose the render-proxy bug is still live in `WeaponBase::Tick`
   (and dereferences `WeaponMesh` unguarded); `GameDesignDocument.md`'s
   backlog still numbered enemies as Phase 4 and the arena as Phase 5,
   stale since the 2026-08-12 renumbering; and **none of Phase 4 is
   committed** — `ProjectileBase.h/.cpp` are untracked and four other
   source files are modified, with the last commit predating the projectile
   fork, the grip offsets, the render fix, and the camera restructure.

**The HTML twin was the worst of it.** Flagged as needing a resync since
2026-08-17 and genuinely stale: missing the entire "Weapon tech" section,
missing all state after 2026-08-12, and — the part that actually mattered —
still asserting that the **battle rifle** is the projectile weapon, which
was reversed on 2026-08-17. Anyone reading that page for design intent would
have gotten the current call backwards. Now fully resynced: new section, new
TOC entry, corrected scope paragraph, 2026-08-30 state, corrected backlog,
changelog caught up.

**Next steps:** unchanged from the queued plan below — configure `BP_Pistol`
first — but two things to settle before starting: confirm whether the Fire
Montage deletion was deliberate (and rebuild it if not, since the pistol's
planned config depends on it), and consider committing the Phase 4 work so
there's a clean point to return to.

---

## 2026-08-30 (2)
**Summary:** Not yet done — this is the queued-up plan, written down because
the user is switching to a new session (via MCP) to actually carry it out.
No files changed in this entry.

**Note on why the switch:** this session was asked to configure `BP_Pistol`
directly and couldn't — `.uasset` Blueprint files are a binary/serialized
format, not plain text, so the file-editing tools available here can't
touch them, and there's no Unreal Editor automation bridge (Python remote
execution / Remote Control API) connected in this session to drive the
running editor. If the new MCP session has that kind of bridge, it may be
able to do this work directly instead of talking the user through the
editor UI step by step.

**Next up, in order:**
1. **Configure `BP_Pistol`** — new Blueprint, parent `WeaponBase`, mesh =
   `Darkness_Pistol`. Stat table (Halo: Reach-accurate bloom — first shot
   from full rest is always precise, so `BaseSpreadAngle` is `0°` on every
   weapon, not just the pistol):

   | Field | Pistol | Close-range rifle | Battle rifle |
   |---|---|---|---|
   | `BaseDamage` | 25 | 15 (+ fragment burst) | 35 |
   | `MaxRange` | 5000 | 2500 | 8000 |
   | `BaseSpreadAngle` | 0° | 0° | 0° |
   | `MaxSpreadAngle` | 3.0° | 6.0° | 4.0° |
   | `BloomPerShot` | 0.12 | 0.08 | 0.18 |
   | `BloomDecayRate` | 0.8 | 0.5 | 0.6 |
   | `BloomDecayDelay` | 0.25 | 0.2 | 0.35 |
   | `IntendedCadence` | 5 | 10 | 3.5 |
   | `FireMode` | Semi | Auto | Semi |
   | `bHasZoom` | false | false | **true** (`ZoomedFOV` ≈30) |
   | `bIsProjectileWeapon` | false | **true** (`ProjectileClass` = renamed `BP_TestWeapon`'s projectile) | false |
   | `bUseAnimationDrivenFeedback` | **true** (Fire Montage already works) | false (flip once rifle anims exist) | false (flip once its own anims exist) |

2. **Configure the close-range rifle** — rename/repurpose the existing
   `BP_TestWeapon` (already parented to `WeaponBase`), mesh =
   `Darkness_AssaultRifle`, wire `ProjectileClass` to the existing
   `AProjectileBase` subclass, apply the table above.
3. **Configure the battle rifle** — new Blueprint, mesh =
   `Darkness_SniperRifle` (tuned down per the design doc — lower/no extreme
   zoom, damage/range/bloom from the table above).
4. **Rifle arm animations** — mirror the pistol's `ABP_FirstPersonArms`
   pattern (Idle↔Move state machine on `Speed`, plus a Fire Montage) for
   the close-range and battle rifles, sourced from the same migrated Lyra
   `MM_`-prefixed clip library. Once each rifle's animation is in and
   confirmed in PIE, flip its `bUseAnimationDrivenFeedback` to `true`.
5. **Not yet started, blocked:** Reload as an Anim Montage — needs an
   ammo/reload system built first (doesn't exist yet).

Also still flagged, not part of this immediate push: camera/arms clipping
fix (tune `FirstPersonScale` down from its current no-op `1.0f`), and the
full-body-visibility/leg-visibility plan (see Phase 4 note in
`ProjectPlan.md` — requires removing `GetMesh()->SetOwnerNoSee(true);` plus
bone-hiding, deliberately deferred).

---

## 2026-08-30
**Summary:** Chased down a real, subtle rendering bug behind the pistol's
hand-grip looking wrong — three hypotheses in a row before landing on the
actual cause. No new features; pure bugfix + one doc correction.

**The bug:** pistol looked correctly gripped when ejected from possession
but wrong (dangling artifact, fingers not wrapped) while actively
possessing/controlling the character; separately reported as "wrong
position" and "looks different in FPS view vs. external view"; and finally
narrowed to "correct after an editor restart, wrong again after
Stop→Play in the same editor session" — all symptoms of the same root
cause, described from different angles across the session.

**Ruled out, in order:**
1. A leftover `Layered Blend Per Bone`/Aim Offset node in
   `ABP_FirstPersonArms`, left over from an abandoned earlier
   arms-follow-camera approach (superseded by the camera-attachment
   hierarchy restructure). User removed it — genuinely stale and worth
   cleaning up, but confirmed **not** the cause of this bug.
2. Manny vs. Quinn skeleton retargeting mismatch (animations are
   `MM_`-prefixed/Manny-authored). Looked plausible since the symptom
   pattern matched a proportion mismatch, but user confirmed **Quinn is
   never used** in this project — red herring. (This also corrects a
   stale claim in this file's Phase 4 checklist, written 2026-08-18, that
   the character's mesh is Quinn — it isn't; see correction there.)

**Actual root cause, found via a live debug readout:** added a temporary
on-screen `RelLoc`/`RelRot` printout of the weapon's transform
(`WeaponBase::Tick`) to compare values across a "correct" run vs. a
"wrong" run — values were identical either way, which ruled out the
transform/offset math entirely and pointed at rendering. Confirmed by the
user's own test: manually nudging the weapon's Scale in the Details panel
during Play (1 → 1.2 → 1, no other change) fixed the visual position
outright. That's the signature of a stale render proxy, not bad data.

Found it: [`WeaponHolderComponent.cpp`](../Source/ProjectBopis/Weapons/WeaponHolderComponent.cpp)'s
`EquipWeapon()` was setting `MeshComp->FirstPersonPrimitiveType` via
**direct property assignment** instead of the proper
`SetFirstPersonPrimitiveType()` setter. Direct assignment doesn't mark
render state dirty, so the unified first-person rendering path could
register/reproject the primitive using a stale transform — inconsistent
between PIE sessions depending on render-proxy timing, and explains the
FPS-view-vs-external-view mismatch too (two separate rendering paths, one
of them working off stale state). **Fix:** swapped to
`MeshComp->SetFirstPersonPrimitiveType(EFirstPersonPrimitiveType::FirstPerson)`.
User applied and confirmed it fixed the issue. Logged as a new Gotcha —
see `ProjectPlan.md`.

**Also discussed, not yet actioned:** camera/arms clipping. Root cause
identified — `FirstPersonScale` is currently `1.0f` (a no-op; doesn't
actually shrink first-person primitives at all) and `FirstPersonFieldOfView`
matches the general gameplay FOV, so the anti-clip mechanism the unified
first-person system is built around isn't actually engaged yet. Recommended
starting point next session: drop `FirstPersonScale` to ~0.5–0.65 and tune
by eye in PIE. **No code changed this session** — explicitly deferred.

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

## 2026-08-18 (2)
**Summary:** A genuinely valuable architecture discussion — the user
pressure-tested the fire-feedback design with a series of sharp questions
(does the weapon driving player animation make sense? does this work for
AI? what about different skeletons sharing a weapon?) that surfaced a real
design flaw before it shipped, and we fixed it the same session rather
than just logging it for later.

**Discussion, in order:**
- "The weapon drives the player animation?" — questioned whether
  `WeaponBase::Fire()` reaching into the character to play a montage was
  backwards. Concluded it was *consistent* with existing patterns
  (`FireSound`/`MuzzleFlash` already lived on the weapon) but not
  obviously the *only* correct answer.
- "This method should work for AI as well right?" — surfaced that
  `WeaponHolderComponent::EquipWeapon`/`FireEquippedWeapon` both hard-cast
  to `AProjectBopisCharacter`, and aiming goes through
  `APlayerController::DeprojectScreenPositionToWorld` (no viewport for an
  AI to deproject from at all). Logged as a gotcha, deliberately not
  fixed — AI aiming needs a genuinely different targeting method anyway
  (perception/line-of-sight, not screen-space), so this was never a small
  fix regardless.
- Follow-up clarified the question was about **extensibility**, not
  current functionality: is the coupling *narrow*, so a future fix is
  small? Answer: yes — the core firing logic (bloom/hitscan/projectile/
  damage) is already fully actor-agnostic; only the holder/feedback layer
  assumes a player, and that's a bounded, well-understood fix (an
  interface instead of a concrete-class cast) when it's actually needed.
- **The real catch**: "If the Player animation and Enemy Animation is
  different but using the same weapon, then you cant use the same
  weaponbase" — because `FireMontage` lived on `WeaponBase`, and an
  `UAnimMontage` is authored against one specific skeleton. A single
  property could only ever be correct for one skeleton. This is a
  dependency-direction problem, not a "which skeleton" problem: the
  weapon shouldn't need to know how to animate whoever's holding it.

**Fixed the same session (not deferred):**
- `FireMontage` removed from `WeaponBase` entirely. `WeaponBase` now only
  exposes `UsesAnimationDrivenFeedback()` (a pure bool signal it computes
  from its own existing flag).
- `AProjectBopisCharacter` gained its own `FireMontage` property, and
  `DoFire()` now plays it on its own `FirstPersonMesh` after checking that
  signal. `WeaponBase::Fire()` no longer references the character,
  animation, or montages at all — clean separation restored.
- This establishes the actual pattern for later: each animator (player
  now, each enemy archetype eventually) owns its own montage/feedback
  data, rather than the weapon holding one hardcoded answer — and
  explicitly *not* a `TMap` on the weapon keyed by consumer type, which
  would just be the same inverted dependency with extra steps.
- **User asked me to write the code directly this time** (rather than the
  usual type-it-yourself workflow) — did so for all four file edits.
  Caught a real bug while reading the files first: a leftover typo
  (`UAnimaMontage` vs `UAnimMontage`) meant the *original*
  weapon-owned-montage version had likely never actually compiled.
  Compiled clean after the fix, reviewed, correct.

**Next steps:** Reload as an Anim Montage is blocked on an ammo/reload
system that doesn't exist yet — not just a montage away. Next real steps:
rifle Idle/Move/Fire (mirroring what's proven for the pistol), then
configuring the three actual weapons. Still deferred: pistol hand-offset
(#21), headshot-marker reticle (#37), surface-reactive Niagara impacts
(#38), decal/sound variation arrays (#39), the AI-extensibility gotcha
(equip/aim layer, logged, not urgent).

---

## 2026-08-18
**Summary:** Finished the projectile system end-to-end (fragmentation
compiled, Instigator chain fixed, `WeaponBase` forked into hitscan/
projectile paths), then pivoted to POV arms animation using a Lyra
Starter Game migration instead of the original generic animset plan —
got a working Idle/Move state machine for the pistol in PIE by end of
session.

**Done:**
- `AProjectileBase` fragmentation burst compiled, reviewed, correct —
  closes out that checklist item entirely.
- Closed a long-standing gap: `WeaponHolderComponent::EquipWeapon` now
  calls `SetInstigator`/`SetOwner` on the equipped weapon, so
  `GetInstigatorController()` (called since Phase 1, always silently
  null) finally resolves to something real, all the way down the chain
  character → weapon → projectile.
- Forked `WeaponBase::Fire()` into a shared prefix/suffix (feedback,
  bloom-driven spread, cadence bookkeeping) with `FireHitscan`/
  `FireProjectile` handling just the differing resolution logic.
  `FireProjectile` relies on `UProjectileMovementComponent`'s default
  "launch along owning actor's local forward" behavior rather than
  manually setting velocity. Compiled clean, reviewed, correct — **Phase
  4's projectile system is now fully wired end to end**, though no
  weapon is actually configured to use it yet (that's the remaining
  "configure the three weapons" checklist items).
- **Animation source changed:** dropped the original `PistolAnimset`/
  `RifleAnimset` plan in favor of migrating raw clips from Epic's **Lyra
  Starter Game** sample via the editor's Migrate tool. Talked through the
  practical steps, the version-drift risk, and the two real scope forks
  (simple raw-clip reuse vs. adopting Lyra's actual layered-animation
  architecture) before the user committed to the simple path — matches
  this project's whole "Reach-style bloom over recoil systems" philosophy
  of not over-building.
- User migrated the **full** `Content/Characters/Heroes/Mannequin/Animations/`
  library (454+ files) rather than cherry-picking — deliberately kept the
  extras on disk ("better to have them and not need 'em") rather than
  pruning. Only a handful of clips actually in use.
- Worked out Lyra's `MM_`/`MF_` naming (Manny/Quinn mannequin variants) —
  character's mesh is Quinn, but Fire/Reload actions only exist as `MM_`
  (no Quinn-specific variant), so decided to just use `MM_` for
  everything now, deferring gender-variant branching to a follow-up in
  the ABP itself rather than designing it blind.
- Built `ABP_FirstPersonArms`: `Speed` float updated every frame via
  `TryGetPawnOwner → GetVelocity → VectorLength`, a 2-state `Locomotion`
  state machine (Idle ↔ Move, `Speed` vs. `10.0` transition threshold).
  Assigned as `FirstPersonMesh`'s Anim Class. **Confirmed working in
  PIE.** Two real fixes along the way: `MM_Pistol_Jog_Fwd` visibly drops
  the weapon pose (wrong clip for this context) — swapped to
  `MM_Pistol_Walk_Fwd`; and the `Play` animation nodes needed **Loop**
  turned on explicitly in each state's sub-graph.

**Open question — user explicitly asked to be asked again next session:**
build Fire/Reload as Anim Montages next (this is what `bUseAnimationDrivenFeedback`
on `WeaponBase` was built for — proves the pipeline end-to-end), or mirror
the Idle/Move setup to the rifle first before adding montages to either?
Not decided as of session end.

**Next steps:**
1. Answer the open question above first thing.
2. Fire/Reload Anim Montages (whichever weapon), wiring `Montage_Play` into `WeaponBase::Fire()`'s animation-driven path.
3. Rifle Idle/Move (mirror of pistol setup).
4. Then: configure the three actual weapons (`BP_Pistol`, close-range rifle as the projectile weapon, battle rifle as hitscan) — the projectile system built today has nothing using it yet.
5. Still deferred: pistol hand-offset (#21), headshot-marker reticle (#37), surface-reactive Niagara impacts (#38), decal/sound variation arrays (#39).

---

## 2026-08-17 (3)
**Summary:** Started `AProjectileBase` — shell compiled and confirmed,
fragmentation burst code given but not yet compiled.

**Done:**
- `AProjectileBase` shell: `USphereComponent` root, `UProjectileMovementComponent`
  (gravity off, flat trajectory), `InitialLifeSpan` so misses don't linger,
  `OnComponentHit` bound in `BeginPlay` to a `UFUNCTION() OnHit` applying
  direct damage via `GetInstigatorController()`. Compiled clean, reviewed,
  correct.
- Hit a scare mid-way: IntelliSense flagged `OnComponentHit.AddDynamic(...)`
  as an unresolved symbol. Turned out to be a well-known IntelliSense
  false-positive (it can't follow the template trickery `AddDynamic`'s
  macro does to validate delegate signatures) — the actual build compiled
  fine. Logged as a project gotcha so it doesn't cause a scare again.
- Added the fragmentation burst on top: `FragmentRadius`/`FragmentDamage`,
  a zero-distance `SweepMultiByChannel` (idiom for "what overlaps this
  point") against `ECC_Pawn`, excluding the directly-hit actor so the
  burst catches *other* nearby targets rather than stacking bonus damage
  on the one already hit — matches the design doc's "strong against
  grouped/exposed targets" intent. **Not yet compiled** — resume here.
- Discussed decal/sound variation arrays (picking a random decal/sound per
  shot instead of always the same one) — deliberately deferred rather than
  built now; parked as task #39. Worth noting: `SciFiWeapDark`'s Sound Cue
  assets likely already randomize internally between wav variants, so
  sound may not need a code-side array at all — check before duplicating
  that.

**Next steps:** compile the fragmentation code, then fork `WeaponBase` to
actually spawn an `AProjectileBase` for the close-range rifle instead of
tracing. Still deferred: pistol hand-offset (#21), headshot-marker reticle
(#37), surface-reactive Niagara impacts (#38), decal/sound variation
arrays (#39).

---

## 2026-08-17 (2)
**Summary:** Finished the hit-impact decal step (Phase 4's second item),
fixing a real distance-culling bug and adding a toggleable debug trace
along the way.

**Done:**
- `HitDecalMaterial`/`DecalSize`/`DecalLifeSpan` on `WeaponBase`, decals
  spawning on any surface hit via the restructured `Fire()` hit block,
  oriented correctly via `HitResult.ImpactNormal.Rotation()`. Compiled
  clean, reviewed, correct — closes out the decal step.
- **Bug found during testing:** decals weren't visible from a distance.
  Root cause: `UGameplayStatics::SpawnDecalAtLocation` doesn't expose
  `FadeScreenSize` (decals' built-in distance-based culling — they fade
  out once they'd render below a screen-size threshold) at the call site.
  Fixed by capturing the returned `UDecalComponent` and calling
  `SetFadeScreenSize(0.0f)` on it to disable the cutoff.
- Added a toggleable debug trace: `CVarShowWeaponTrace` (console command
  `Weapon.ShowTrace`), a file-scope `TAutoConsoleVariable<bool>` gating
  the existing `DrawDebugLine` call. Chose a CVar over a per-weapon
  `UPROPERTY` deliberately — this is a global debug-visualization switch,
  not something that varies by weapon identity, so it doesn't belong
  cluttering every weapon Blueprint's defaults.
- **Phase 4 now 2/8 items done:** fire feedback and hit decals.

**Next steps:** `AProjectileBase` actor class next (for the close-range
rifle, per the 2026-08-17 reversal), then forking `WeaponBase` for
projectile firing, then POV arms animation, then the three weapon
configs. Still deferred: pistol hand-offset (#21), headshot-marker
reticle (#37), surface-reactive Niagara impacts (#38).

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
