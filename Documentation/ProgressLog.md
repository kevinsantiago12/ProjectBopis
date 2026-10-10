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

## 2026-10-09 (2)
**Summary:** **Phase 5 started: enemies.** Steps 1–3 are done and
user-confirmed in PIE:
- player and enemies share one character base, so the enemy inherits all the
  animation and weapon work;
- a test enemy stands, equips, raises its gun, patrols, and strafes while
  aiming at the player.

Detail in [TechnicalDesignSpec.md](TechnicalDesignSpec.md) (*Enemies → Built
so far*).

- **Design changes (user):**
  - **The Aswang are dropped.** Recorded in the lore notes' DISCARDED section.
    PART 1 and enemy composition are flagged `[UNDECIDED]`, and the spec's
    Aswang sections are flagged as not current.
  - **Build order:** animation + weapons → basic movement → taking bullets +
    ragdoll ("very important"). Enemy shooting comes later.
  - Projectile conversion of the remaining weapons is deferred as minor.
- **Step 1a:** `ABopisCharacterBase` extracted from the player (weapon holder,
  montage maps and playback, raise/aim/reload state, recoil hook). Blueprint
  values survived because property and subobject names were unchanged.
- **Step 1b:** the anim instance and weapon holder now cast to the base. The
  holder's crosshair fire path stays player-only.
- **Step 2:** `AEnemyBase` (auto-possessed `AAIController`, `SetAiming`,
  `bStartRaised`).
  - Bridge: `BP_EnemyBase` (player mesh, `ABP_Player`, montage maps copied,
    `BP_Pistol`).
  - `Enemy_Test` placed in `Lvl_Sandbox`.
- **Step 3:** test patrol (`PatrolPoints`, `PatrolWaitTime`) and
  `bAimAtPlayer` (focus → aim offset, raised strafe).
  - Turning: desired rotation when raised, orient-to-movement when lowered,
    `TurnRate` 360.
  - Speeds: lowered 300 / raised 250.
  - The user placed the NavMeshBoundsVolume and Target Points.
- **Code:** all applied by Claude on request, each built with the script.

*(RESUME HERE moved to 2026-10-10. Steps 1–3 were committed and pushed.)*

---

## 2026-10-10
**Summary:** **Phase 5 step 4a done: taking bullets and dying.** All
user-confirmed in PIE. Detail in the spec (*Enemies → Taking bullets and
dying*).

- **Design (user, during the step):**
  - Death plays an animation first; ragdoll only once the dying body takes X
    more damage.
  - Ragdolls fly on **every** bullet (Max Payne 2).
  - Once ragdolled, he should **stay standing about a second** so the player
    can unload into him: the riddled phase.
  - Shotguns go straight to ragdoll **only on a big overkill** (a partial blast
    can just riddle). The same rule lets magnums do it.
- **Built:**
  - per-bone hits (capsule ignores bullets; projectiles use the `Projectile`
    profile);
  - `UHealthComponent`, head ×4;
  - death animation in a new full-body `DeathSlot` (added by the user) → riddled
    (physical-animation motors on the upper body) → ragdoll launch scaled by
    damage;
  - overkill burst → instant ragdoll.
- **Bugs found on the way:**
  - My first version counted the killing blow's overkill toward the ragdoll,
    which skipped the animation. Removed, then reintroduced as the separate
    50-point instant-ragdoll rule.
  - **Death animation never played:** the placed instance had a stale empty
    `DeathAnimations`. Bridge CDO edits don't propagate to placed instances.
    Found with a temporary `[DeathDbg]` log (since removed). The user had me
    make **`BP_Enemy_Test`** (child of `BP_EnemyBase`), which now replaces
    `Enemy_Test`.
  - Shots passed through ragdolls: the `Ragdoll` profile ignores Visibility.
    Fixed by `UseRagdollCollision`.
  - `AddImpulse` on animated legs while riddled. Fixed by `KickBone`.
- **The user tuned some values on the Blueprints themselves.**
- **Code:** all applied by Claude on request, each built with the script.
  **Bridge:** `DeathAnimations`, `BP_Enemy_Test` + instance swap.
- **Riddled break (user):** 30+ damage within 0.1 s while riddled ends the
  dance straight into ragdoll (`RiddledBreakDamage`, reusing
  `OverkillWindow`). User-confirmed.
- **Starting loadout (user, for testing):** `StartingLoadout` +
  `bStartWithFullAmmo` on the weapon holder. Bridge: `BP_PlayerCharacter` gets
  all six weapons, duals in hand, full pools. User-confirmed.
- *(Committed and pushed by the user.)*
- **Step 4b, hit reactions (built while the user was away).** The user gave
  standing permission for this feature only: "make all the changes till you
  implement this to completion".
  - **Design (user):**
    - a light physics reaction on every surviving hit, feedback only;
    - a stagger from X damage in X time that roots the enemy riddled-style,
      re-triggerable to stun-lock;
    - durations tunable.
  - **C++ (applied by Claude, built with the script):**
    - `SimulateUpperBody` (shared with riddled);
    - `StartHitReaction`, `StartStagger`, `EndHitReactions`;
    - `PlayDirectionalAnimation` (shared with death);
    - stagger window accounting in `TakeDamage`;
    - the mesh ignores Pawn;
    - the enemy's Tick halts the AI while staggered.
  - **Bridge:** `StaggerAnimations` (Lyra hit-react Med/Hvy clips) on
    `BP_EnemyBase`, `BP_Enemy_Test` and both placed `BP_Enemy_Test` instances.
    The parent BP's value didn't propagate to the child: gotcha updated.
  - **User-confirmed in PIE** ("works now"). The level was saved by the user.
    Any tuning the user did lives on the BPs.
- **Step 4c part 1, corpse limit** (user-confirmed in PIE).
  - **Design (user):** 5 corpses by default, settable. With 6, the first one
    **out of view** is removed, however long it has lain there.
  - `MaxCorpses` / `CorpseCheckInterval` live on the game mode; the enemy's
    `Die` registers the body.
  - The holder's `EndPlay` destroys carried weapons.
  - **Bug:** the first visibility check (`GetLastRenderTimeOnScreen`) read every
    body as on screen, because Lumen and off-screen passes refresh it. Replaced
    with a camera-cone + line-of-sight test.
    - Diagnosed with a temporary `[CorpseDbg]` log, read through the bridge
      Logs toolset: the editor log file had stopped flushing, and the editor
      briefly showed Not Responding.
    - The logs were removed afterwards (user asked).
  - **Weapon drop design (user):** physics, but clamp the launch.

### ▶ RESUME HERE
1. **Commit:** steps 4b + 4c part 1 (C++, `BP_EnemyBase`, `BP_Enemy_Test`,
   level), docs.
2. **Phase 5 step 4c, the rest:**
   - **weapon drop:** detach on death, physics with a clamped launch
     (`MaxWeaponDropSpeed`), becomes a pickup (ammo if the weapon is owned,
     weapon + rounds if not; reuses `AWeaponPickup`). Plan already given to the
     user;
   - Focus `AddMeter(KillRefill)` on kills, then passive regen off.
3. **Design question (user + design partner):** the enemy roster now that the
   Aswang are gone. Humans only? Does horror stay in any form?
4. **Focus extras:** sounds when assets exist.
5. **Deferred (minor):**
   - convert the single pistol, battle rifle and both shotguns to projectiles
     (the shotguns need a pellet BP);
   - `BP_RifleProjectile` is unreferenced; delete it?
6. **Quick checks (user):** dual left-forearm recoil direction; recoil feel per
   weapon; dot readability.
7. **Exaggerated impacts, next passes:**
   - impact sounds;
   - boosted Niagara layers;
   - bigger in Focus;
   - debris and breakables.
8. **Later:**
   - the equip end pose;
   - ammo pickup BPs per type;
   - remappable keys;
   - player death (same base, needs its own `Die`: keep the camera);
   - high-powered pistol and dual SMG BPs;
   - foot sync markers;
   - enemy shooting (own aim source), StateTree behaviour, a shared montage-set
     data asset if the player and enemy copies drift.

---

## 2026-10-09
**Summary:** One-handed pistol polish. The stance is **flipped to right foot
forward**, and the free left arm now **swings procedurally in step with the
feet**. Both user-confirmed in PIE. Detail in
[TechnicalDesignSpec.md](TechnicalDesignSpec.md) (*One-handed pistol*).

- **Mirrored left strafe** (blend space per-sample Mirror + `MDT_Mannequin`,
  user): the torso over-twisted. Rolled back; recorded under *Decided
  against*.
- **Stance flip (user, in the AnimGraph):**
  - *Mirror with MDT_Mannequin* on the one-handed pistol's own **Idle-state**
    players, lowered and raised. Only the legs and pelvis flip, because the
    raised upper body is laid over in mesh space.
  - A first test on the top-level idle flipped only the duals, because that
    layer is the lowered-dual one.
  - A bladed stance was considered (procedural pelvis yaw, or an authored
    clip) and dropped in favour of the plain flip.
- **Free-arm swing:**
  - **Clip-based retry:** an unarmed jog as a sync-group follower didn't follow
    the feet. Cause: the Lyra pistol strafe clips have no foot sync markers. The
    pistol jog as the source was two-handed. Dropped, and the C++ removed.
  - **Procedural version (kept):** `UpdateFreeArmSwing` reads the fore-aft
    foot gap each frame and drives a component-space Modify Bone on
    `upperarm_l`.
  - **Strafe fix:** auto-gain (`FreeArmStridePeak`, floor `FreeArmMinStride`
    8). With a fixed 50 cm stride, strafing didn't swing.
  - **User tuning:** swing 10°.
- **Code:** applied by Claude on request, each built with the script.
  **Bridge:** the swing node (`ModifyBone_5`).

**Later the same day:**
- **Projectile groundwork (C++):**
  - fragment splash is now opt-in (default 0);
  - damage uses the firing weapon's falloff, measured from the spawn point, and
    `ApplyPointDamage`;
  - meshes are hidden unless world dilation < 0.9 (tracers stay visible).
- **Bullet speeds:** tried at 40k/90k cm/s, but the user preferred **9,000**,
  so the rounds read in bullet time. Radius is now 1.
- **Bullet time built:**
  - **Design (user):** Q toggle; 0.3× world with the player slowed too, aim
    normal; meter with kill refill / passive regen / infinite switches.
  - **Code:** `UBulletTimeComponent` and `UBulletTimeWidget`. My first names
    (`Activate` / `Deactivate` / `IsActive`) clashed with `UActorComponent`'s;
    renamed.
  - **Input:** `IA_BulletTime` on Q.
  - **HUD:** the user built the meter.
- **Feedback:**
  - unbound `FocusPostProcess` (desaturate 0.5, vignette 0.8, fringe 1.5) faded
    in real time;
  - global pitch 0.6;
  - empty enter / exit / loop sound slots.
- **"Rounds visible in real time":** a temporary `[BulletVis]` log showed every
  round fully hidden at spawn. The user had since rebuilt their projectiles
  (`BP_Cal45Bullet_Projectile`, `BP_RifleRound_Projectile`, bullet model +
  tracer) and confirmed they show only in slow motion.
  `bKeepEffectsVisible` now defaults to off. The log was removed.
- **Renamed "bullet time" → "Focus"** (user: the old name is trademarked).
  - Code: `UFocusComponent`, `UFocusWidget`, `FocusAction`, `DoToggleFocus`,
    `FocusPostProcess`, `FocusPitch`.
  - Assets: `IA_Focus` (Q), `WBP_Focus`.
  - `[CoreRedirects]` added to `DefaultEngine.ini`.
- **Rename hiccup:** I also redirected the two *component* members onto their
  old subobjects and saved `BP_PlayerCharacter`. That left duplicate
  components. The user reverted the Blueprint to the last commit; I re-set
  `FocusAction`, and only the new components remain. Lesson recorded in the
  spec.

**Later still — per-surface impacts** (user-confirmed in PIE). Detail in the
spec (*Impact effects*).
- **Questions answered:**
  - Niagara is scalable (effect types, pooling).
  - Mixing Cascade and Niagara is fine.
  - Niagara works with baked lighting.
- **Lighting policy changed (user):** dynamic lights are allowed. Static vs
  dynamic is decided per case.
- **Step 1:** 24 physical surface types named in `DefaultEngine.ini`; the
  Rubber physical material set to SurfaceType24.
- **Step 2:** effect type `NFX_Impact` created by the user; the bridge set it
  up and assigned it to all 26 `NS_Impact*` systems.
- **Step 3 (C++, applied by Claude on request, built with the script):**
  - `UImpactEffectsData`;
  - the `ImpactEffects` property on the weapon;
  - physical-material returns on the trace and the projectile sweep;
  - `Niagara` + `PhysicsCore` modules.
- **Step 4 (bridge):** `DA_ImpactEffects` filled (24 surfaces + Default) and
  assigned to all six weapons.
- **The user:** physical materials on the level materials. Anything unmapped
  falls back to Default (Concrete burst + generic hole).
- **Exaggeration pass 1** (John Woo style; user picked options 1 + 2 of 5):
  - **C++ (applied by Claude on request, built with the script):** per-surface
    `Scale`, `ExtraSystems`, `DecalVariants` (random pick + random spin),
    `Sound`, global `EffectScale`.
  - **Bridge:** every decal variant filled in; `EffectScale` 1.5. Sound
    skipped by the user.
  - User-confirmed in PIE.

*(RESUME HERE moved to 2026-10-09 (2). Focus, projectiles and impacts were
committed and pushed as "Added Particles".)*

---

## 2026-10-08 (2)
**Summary:** **Pickups done.** All user-confirmed in PIE ("works now"):
- shared ammo pool per type;
- ammo pickups;
- unlimited weapon carry;
- number-key weapon selection by category;
- weapon pickups, with dual unlock.

Detail in [TechnicalDesignSpec.md](TechnicalDesignSpec.md) (*Ammo* → *Shared ammo
pool*, *Pickups and the backpack*). Design imported into the lore notes and GDD
(+ `.html`).

- **Design (user):**
  - weapon drops: ammo if owned, weapon + rounds if not;
  - drop rounds fixed, or random from half a magazine to a full one;
  - no carry limit;
  - single and dual as separate selections (Max Payne 1);
  - number keys only, by category;
  - auto-equip on pickup as an option, default on;
  - shared ammo per type;
  - caps Pistol 180 / SMG 300 / Rifle 300.
- **Code** (applied by Claude on request, each built with the script):
  - shared pool on `UWeaponHolderComponent` (per-weapon reserve removed);
  - `AAmmoPickup`;
  - `WeaponSlot` + `SelectSlot` + `IA_WeaponSlot` bindings (`MaxCarriedWeapons`
    removed);
  - `AWeaponPickup` + `GiveWeapon` / `FindCarriedWeapon` / `bAutoEquipOnPickup`;
  - `DualWieldClass` / `SingleWieldClass`. Starting with duals also gives the
    single.
- **Bridge:**
  - `AmmoType` on 6 weapons;
  - caps on the holder;
  - `IA_WeaponSlot1–5` and keys 1–5 in `IMC_Default`;
  - slots on 6 weapons;
  - `DualWieldClass` / `SingleWieldClass` on the pistols;
  - `BP_AmmoPickup_Pistol` (open .45 box), `BP_WeaponPickup`, test pickups in
    `Lvl_Sandbox`. New level actors can't be saved through the bridge, so the
    user saved the level.

### ▶ RESUME HERE
1. **Dual lowered jog cadence — fixed and confirmed** (`DualLoweredRateScale`
   set to **0.8** on `ABP_Player`; 0.7 made the duals slightly slower than the
   one-handed jog):
   - **Cause:** the lowered-dual blend space's 0.7 was replaced by the global
     `LocomotionPlayRate` on 2026-10-07.
   - **Fix:** `DualLoweredPlayRate` = `LocomotionPlayRate` × `DualLoweredRateScale`
     (0.8 set, tunable on the AnimBP class defaults), wired to that player.
   - **Diagnosis:** a temporary on-screen readout (added, then removed) showed
     the layer active while jogging lowered. The user's 0.2 test had been on a
     state-machine player, which only shows while raised.
   - **Restored:** two test-edited state players (`MM_Unarmed_Jog_Fwd` in Move,
     `MM_Unarmed_Idle_Ready` in Idle) wired back to `LocomotionPlayRate`.
   - **Lesson:** AnimGraph pin watches show nothing, because getters there use
     the fast path and never execute. For live values, use an on-screen readout
     or the Rewind Debugger.
2. ~~Commit~~ — done: committed and pushed by the user (2026-10-08).
3. **Equip animation — done, user-confirmed:**
   - **Decisions (user):** fire blocked during equip; gun swaps instantly for
     now; pickups animate too.
   - **C++:** `EquipMontages` / `OffhandEquipMontages`, `PlayEquipAnimation`
     called from `EquipWeapon`, `IsEquipAnimating` gate in `DoFire`.
   - **Assets:** the user made `AM_Pistol_Equip`, `AM_Rifle_Equip` and
     `AM_Pistol_Equip_Offhand`; the bridge filled the maps.
   - **Left for later:** the clip ends with the gun pointed straight, then eases
     to lowered, which looks odd. Options are in the spec's *Equip animation*.
4. **Backlog — projectile bullets:** fragmentation opt-in, per-bullet
   speed/radius, falloff on projectiles, slow-motion-only visibility; then convert
   the remaining weapons.
5. **Quick checks (user):** dual left-forearm recoil direction; recoil feel per
   weapon; dot readability.
6. **Optional / later:**
   - pickup BPs per ammo type with AmmoSet meshes and sounds;
   - Player Mappable Key Settings on the slot actions;
   - starting loadout list;
   - high-powered pistol BP (`Pistol` anim type, HighPowerPistol ammo);
   - dual SMG BP;
   - remove the unused crosshair code.
7. **Then:** Phase 5 — enemy archetype foundation (enemy weapon drops will use
   `AWeaponPickup`).

---

## 2026-10-08
**Summary:** Short session. User decided **every weapon becomes a projectile
weapon**, with bullets **hidden at normal speed and shown in slow motion**
(for the future bullet time). First round built by the user. The engineering
follow-up is **on the backlog**; next session is ammo pickups.

- **`BP_Cal45Bullet`** (user): .45 projectile on `BP_DualPistols`, `cal45_Full`
  mesh. It left no decals because `HitDecalMaterial` lives on the projectile and
  defaults to none. User set it to `MI_Generic`; decals work.
- **Backlog** (ProjectPlan + spec *Projectile vs hitscan*): `AProjectileBase`
  defaults predate the decision:
  - every hit does a 150 cm / 10-damage fragment splash;
  - 30 m/s speed;
  - 5 cm collision radius;
  - no damage falloff on the projectile path (shotguns).

  Plus the planned visibility rule: `bShowOnlyInSlowMotion` driven by the
  projectile's time dilation, so bullet time needs no hook. Open: hide tracers
  too?
- **Folder rename (user):** `Content/FirstPerson/` → `Content/ThirdPerson/`.
  `CLAUDE.md` updated; older doc entries keep the old path.
- **Docs:** design decision imported into the lore notes + GDD (+ `.html`).

### ▶ RESUME HERE
1. **Commit**:
   - the dot crosshair (`WBP_Reticle`) and its docs;
   - the `FirstPerson` → `ThirdPerson` folder move (check `git status` shows
     the new folder fully added before committing);
   - `BP_Cal45Bullet`;
   - today's docs.
2. **Ammo pickups (next session), continuing the checklist:**
   - [x] 1. Debug lines removed (C done)
   - [x] 2. `EAmmoType` + `AmmoType` on the weapon (compiled 2026-10-06 20:07)
   - [ ] 3. Set `AmmoType` on the weapon BPs (Pistol/Duals → Pistol,
     CloseRangeRifle → Rifle, BattleRifle → Sniper, Shotgun → AutoShotgun,
     PumpShotgun → PumpShotgun) — user or bridge writes. Anim types differ
     from ammo types now (`BP_Pistol` → `PistolOneHanded`, duals → `Dual`).
     Blueprints now live in `Content/ThirdPerson/Blueprints/`
   - [ ] 4. `AAmmoPickup` C++ (walk-over, type + amount + mesh, take what fits,
     remainder stays) + a weapon-side `AddReserveAmmo` — present for review
   - [ ] 5. Pickup BPs per type with AmmoSet meshes; place in `Lvl_Sandbox`; test
3. **Backlog — projectile bullets** (when the user picks it up): fragmentation
   opt-in, per-bullet speed/radius, falloff on projectiles, slow-motion-only
   visibility; then convert the remaining weapons.
4. **Quick checks (user):** dual left-forearm recoil direction; recoil feel per
   weapon; dot readability on bright backgrounds.
5. **User's own work:** left-hand FK edits on lowered/hip-fire clips; shotgun
   tuning; magazine sizes; recoil angles.
6. **Optional:** `LeftHandGrip` socket on `Sniper_Rifle_A`; shotgun hip-fire
   idle; pistol kneeling crouch; per-weapon recoil data; dual SMG weapon BP;
   remove the unused crosshair C++/materials once the accuracy model is decided.
7. **Then:** Phase 5 — enemy archetype foundation.

---

## 2026-10-07 (3)
**Summary:** **Crosshair simplified to a static dot** (user decision: same dot
for every weapon, no bloom feedback). Built through the bridge and
user-confirmed in PIE. Detail in [TechnicalDesignSpec.md](TechnicalDesignSpec.md)
(*Combat: bloom accuracy model*); design noted in the lore notes and GDD
(+ `.html`).

- **`WBP_Reticle`** (bridge):
  - Brush: material removed, now a 6×6 fully rounded box (a solid white circle).
  - Canvas slot: 6×6, centred.
  - Event Tick chain (crosshair settings, material swap, bloom → radius) and
    `LastCrosshairMaterial` deleted.
- **Kept, unused:**
  - `FCrosshairSettings` and the reticle widget's bloom getters (C++);
  - `M_Reticle` / `M_Reticle_Corners`.

  The accuracy model is still open, so they wait for that decision.
- The spec's rule that bloom must visibly drive the reticle is marked
  suspended.

### ▶ RESUME HERE
1. **Commit** — the dot crosshair (`WBP_Reticle`) and these docs.
2. **Quick checks (user):** dual left-forearm recoil direction (`lowerarm_l`
   +20°, set by symmetry); recoil feel per weapon; dot readability on bright
   backgrounds (a 1 px dark outline is a one-field change if needed).
3. **Ammo pickups, continuing the checklist:**
   - [x] 1. Debug lines removed (C done)
   - [x] 2. `EAmmoType` + `AmmoType` on the weapon (compiled 2026-10-06 20:07)
   - [ ] 3. Set `AmmoType` on the 6 weapon BPs (Pistol/Duals → Pistol,
     CloseRangeRifle → Rifle, BattleRifle → Sniper, Shotgun → AutoShotgun,
     PumpShotgun → PumpShotgun) — user or 6 bridge writes. Anim types differ
     from ammo types now (`BP_Pistol` → `PistolOneHanded`, duals → `Dual`)
   - [ ] 4. `AAmmoPickup` C++ (walk-over, type + amount + mesh, take what fits,
     remainder stays) + a weapon-side `AddReserveAmmo` — present for review
   - [ ] 5. Pickup BPs per type with AmmoSet meshes; place in `Lvl_Sandbox`; test
4. **User's own work:** left-hand FK edits on lowered/hip-fire clips; shotgun
   tuning; magazine sizes; recoil angles.
5. **Optional:** `LeftHandGrip` socket on `Sniper_Rifle_A`; shotgun hip-fire
   idle; pistol kneeling crouch; per-weapon recoil data; dual SMG weapon BP;
   remove the unused crosshair C++/materials once the accuracy model is decided.
6. **Then:** Phase 5 — enemy archetype foundation.

---

## 2026-10-07 (2)
**Summary:** **Dual spread.** The left gun of a dual pair was hidden behind the
head when running and gunning. Duals now get their own anim type: spread when
firing on the move, the original narrow grip when aiming. User-confirmed in
PIE. Detail in [TechnicalDesignSpec.md](TechnicalDesignSpec.md) (*Dual spread*);
design imported into the lore notes and GDD (+ `.html`).

- **Rounds:**
  - **Procedural arm spread** (Modify Bone on `upperarm_l`): wrong sign first,
    then it deformed the shoulder. Removed.
  - **Runtime spread** (`DualRunGunAlpha` + the user's spread idle blended in):
    under the slots the shot montage pinched the arms in; after the slots it
    never showed. User reverted to the last push.
  - **Authored, by anim type (kept):**
    - `EWeaponAnimType::Dual` (dual pistols + planned dual SMGs).
    - Assets by the user: `MM_Pistol_Idle_Hipfire_Dual`; `MM_Pistol_Fire_Dual`
      (Local Animation Frame base; its upper arm is 5° off the idle, for
      movement between shots); `AM_Dual_Fire` / `_Offhand`.
    - Bridge: weapon type, montage maps, spread switches.
  - **Aiming back to the original** (user request):
    - `AimFireMontages` / `AimOffhandFireMontages` on the character.
    - `bDualSpread` (dual AND not aiming) drives both idle switches (0.2 s
      blend).
    - User recreated `AM_Pistol_Fire_Offhand` (in `Mannequins/Anims/Pistol`,
      on that folder's template `MM_Pistol_Fire`).
- **Finding:** Lyra's `MM_Pistol_Fire` has no additive base animation set, so
  its delta carries more than the kick and dragged the spread idle back each
  shot — likely what sank the runtime approach. Recorded as a gotcha.
- **Code** (applied by Claude on request, each built with the script):
  `Dual` enum value, `bIsDualWield` exposed, `bDualSpread`, the aim montage maps
  with a `TryMap` lookup.
- **Commits:** the spread itself was committed by the user; the aiming change
  and these docs are not.

### ▶ RESUME HERE
1. **Commit** — aimed-dual montages/idle (`AimFireMontages`, `bDualSpread`,
   `AM_Pistol_Fire_Offhand`) and these docs.
2. **Quick checks (user):** dual left-forearm recoil direction (`lowerarm_l`
   +20°, set by symmetry); recoil feel per weapon.
3. **Ammo pickups, continuing the checklist:**
   - [x] 1. Debug lines removed (C done)
   - [x] 2. `EAmmoType` + `AmmoType` on the weapon (compiled 2026-10-06 20:07)
   - [ ] 3. Set `AmmoType` on the 6 weapon BPs (Pistol/Duals → Pistol,
     CloseRangeRifle → Rifle, BattleRifle → Sniper, Shotgun → AutoShotgun,
     PumpShotgun → PumpShotgun) — user or 6 bridge writes. Anim types differ
     from ammo types now (`BP_Pistol` → `PistolOneHanded`, duals → `Dual`)
   - [ ] 4. `AAmmoPickup` C++ (walk-over, type + amount + mesh, take what fits,
     remainder stays) + a weapon-side `AddReserveAmmo` — present for review
   - [ ] 5. Pickup BPs per type with AmmoSet meshes; place in `Lvl_Sandbox`; test
4. **User's own work:** left-hand FK edits on lowered/hip-fire clips; shotgun
   tuning; magazine sizes; recoil angles.
5. **Optional:** `LeftHandGrip` socket on `Sniper_Rifle_A`; shotgun hip-fire
   idle; pistol kneeling crouch; per-weapon recoil data; dual SMG weapon BP
   (`AnimType Dual`, `bDualWield`, SMG ammo).
6. **Then:** Phase 5 — enemy archetype foundation.

---

## 2026-10-07
**Summary:** Animation feel pass. **One-handed single pistol**, **heavier gait**
(slower clips + stride warping), and **procedural recoil** that stacks under
rapid fire. All user-confirmed in PIE. Detail in
[TechnicalDesignSpec.md](TechnicalDesignSpec.md) (*Animation architecture* →
*One-handed pistol*, *Gait*, *Procedural recoil*). Design changes imported into
the lore notes and GDD (+ `.html`).

- **One-handed pistol** (user design: the free hand at the side; two-handed kept
  for the high-powered pistol):
  - **C++:** `PistolOneHanded` + `IsPistolAnimType`, `bIsPistolHold`,
    `FreeArmAlpha`.
  - **Assets:** user made `MM_Pistol_Idle_OneHanded` and added the enum pins.
  - **Bridge:** free-arm layer.
  - **Fix rounds:**
    - Arm stiff when shooting → tried branching at `upperarm_l`.
    - Arm followed the feet, not the aim → switched to local-space rotation.
    - Arm raised while strafing → back to `clavicle_l`.
    - Reload snapped the arm → `FreeArmReloadBlend` fade.
    - Lowering snapped → exempted from the two-handed snap rule.
  - **Free-arm jog swing:** tried, then removed at the user's request.
- **Gait** (Max Payne 1–2 reference):
  - `LocomotionPlayRate` (user set 0.75) wired into all 32 clip players. The
    bridge can't create nodes in states, so the user dropped one getter per
    state and the bridge wired the pins.
  - Stride Warping (Graph mode) + Leg IK added after Orientation Warping.
- **Recoil:**
  - **Diagnosis:** spam fire restarts the fire montage at frame 0, so the kick
    never shows.
  - **Ruled out:** fire-montage blend-in 0 — tried, looked worse, reverted.
  - **Built:** spring-driven recoil (`AddRecoil` from the fire code) into
    Transform (Modify) Bones on `spine_05` / `lowerarm_r` / `lowerarm_l`, plus
    the free arm.
  - **Debugging:** it "didn't work" for several rounds. The new nodes' Rotation
    pins (0,0,0) were overriding the settings. Found with a constant-alpha test;
    fixed by hiding the pins. Yaw turned out to be the bend axis.
- **Cleanup:** unused `StrideScale` and free-arm swing properties removed.
- **Process note:** I made one bridge edit (the `upperarm_l` filter) before
  asking. The user approved it after the fact.
- **Compiles:** all C++ was applied by Claude on request and built with the
  rebuild script.

### ▶ RESUME HERE
1. **Commit** — everything since the "one-handed pistol, slower gait" commit:
   recoil, the free-arm fixes, the cleanup, and these docs.
2. **Quick checks (user):** dual left-forearm recoil direction (`lowerarm_l`
   +20° is set by symmetry; flip if it dips); recoil feel per weapon (tuning is
   on the nodes and class defaults).
3. **Ammo pickups, continuing the checklist:**
   - [x] 1. Debug lines removed (C done)
   - [x] 2. `EAmmoType` + `AmmoType` on the weapon (compiled 2026-10-06 20:07)
   - [ ] 3. Set `AmmoType` on the 6 weapon BPs (Pistol/Duals → Pistol,
     CloseRangeRifle → Rifle, BattleRifle → Sniper, Shotgun → AutoShotgun,
     PumpShotgun → PumpShotgun) — user or 6 bridge writes. `BP_Pistol` is now
     anim type `PistolOneHanded`, but its ammo stays `Pistol`
   - [ ] 4. `AAmmoPickup` C++ (walk-over, type + amount + mesh, take what fits,
     remainder stays) + a weapon-side `AddReserveAmmo` — present for review
   - [ ] 5. Pickup BPs per type with AmmoSet meshes; place in `Lvl_Sandbox`; test
4. **User's own work:** left-hand FK edits on lowered/hip-fire clips; shotgun
   tuning; magazine sizes; recoil angles.
5. **Optional:** `LeftHandGrip` socket on `Sniper_Rifle_A`; shotgun hip-fire
   idle; pistol kneeling crouch; per-weapon recoil data.
6. **Then:** Phase 5 — enemy archetype foundation.

---

## 2026-10-06
**Summary:** Phase 4 backlog swept. **Shotgun polish** done: shells-per-load,
a pump-action variant, a looping per-round reload montage. **Left-hand IK
reworked** onto a weapon socket, ending up aim-only on long guns after several
rounds. **Rebuild script** added. All user-confirmed in PIE. Detail in
[TechnicalDesignSpec.md](TechnicalDesignSpec.md) (*Reload*, *Pellets*,
*Animation architecture* → *Left-hand IK history*, *Build tooling*).

- **Backlog sweep:** left-hand IK, TEMP timer, rifle grip ticked as
  done/superseded; muzzle-flash-north closed after the user's PIE check.
- **Shotgun design** (user, imported into the lore notes + GDD): two variants
  (semi-auto SPAS-style, pump-action), DOOM-style range, slow reload as the
  drawback. Tuning is the user's, later.
- **Code** (applied by Claude on request, each compiled via the script):
  - `RoundsPerLoad` on `AWeaponBase` (2 on both shotguns).
  - `EWeaponAnimType::PumpShotgun`; `BP_PumpShotgun` made via the bridge. The
    user added the enum pins in the AnimGraph (kept convention over a C++ remap).
  - Character `UpdateReloadMontage()`: crossfaded Loop restart, `End` via
    `Montage_SetNextSection`, `IsReloadAnimating()` keeps the IK off through
    the rack. Took three rounds: an inertialization request from Tick was a frame
    late; then `bStopAllMontages = false` left old copies looping forever.
  - Left-hand grip: `LeftHandGripLocation/Alpha` from the `LeftHandGrip` socket;
    IK only while aiming a long gun.
- **Assets:** user built `AM_Shotgun_Fire`, `AM_Shotgun_Fire_Pump`,
  `AM_Shotgun_Reload` (Start/Loop/End), the `LeftHandGrip` sockets (assault
  rifle, shotgun, pistol skeletons). Bridge: montage map entries, Inertialization
  node, Transform (Modify) Bone on `ik_hand_l`, `TurnThreshold` 45.
- **Left-hand IK rounds:** IK everywhere with socket position → wrist/drift
  issues; + rotation and attachment-chain offset → broke, rolled back; raised
  only → aim-offset issues; attachment offset alone → broke again; **final:
  aim-only, long guns, world-transform offset**, user edits lowered FK
  themselves. The shotgun pump left arm reach on left twists → `TurnThreshold`
  90 → 45.
- **`Tools/RebuildEditor.bat`:** close editor → UBT build → reopen. Rule added to
  `Claude-Rules.md` (run only when asked).
- **Crouch tweaks (PIE-confirmed):** guns looked raised and the crouch read as
  "sitting" — both from Lyra's weapon-up crouch idle. User swapped the long-gun
  crouch idle to the pack's `anim_shotgun_crouch_idle` (kneeling, gun neutral).
  Crouched duals no longer force the mirrored left arm up — the left hand comes
  from the crouch clip until raised (C++, applied on request).

- **Ammo (Phase 4 C–D) started.** C was already built (`WBP_Ammo` in the HUD,
  user confirmed) — only the per-frame `Bloom:`/`Ammo:` debug lines remained;
  deleted. User added the **AmmoSet** pack (calibre boxes: 12 ga, 9mm, .45,
  .500 S&W, .22, 5.45, 7.62, 20mm). Design agreed (imported into the lore notes):
  ammo **types** (pickup feeds the matching weapon), walk-over, take what fits,
  no respawn; separate ammo for auto/pump shotgun and rifle/sniper; hi-power
  pistol and SMG planned. `EAmmoType` + `AWeaponBase::AmmoType` compiled
  (applied by Claude on request). Mag sizes: user tunes later.

### ▶ RESUME HERE
1. **Ammo pickups, continuing the checklist:**
   - [x] 1. Debug lines removed (C done)
   - [x] 2. `EAmmoType` + `AmmoType` on the weapon (compiled 2026-10-06 20:07)
   - [ ] 3. Set `AmmoType` on the 6 weapon BPs (Pistol/Duals → Pistol,
     CloseRangeRifle → Rifle, BattleRifle → Sniper, Shotgun → AutoShotgun,
     PumpShotgun → PumpShotgun) — user or 6 bridge writes
   - [ ] 4. `AAmmoPickup` C++ (walk-over, type + amount + mesh, take what fits,
     remainder stays) + a weapon-side `AddReserveAmmo` — present for review
   - [ ] 5. Pickup BPs per type with AmmoSet meshes; place in `Lvl_Sandbox`; test
2. **Commit** — today's later work (crouch docs onward) isn't committed yet.
3. **User's own work:** left-hand FK edits on lowered/hip-fire clips; shotgun
   tuning; magazine sizes.
4. **Optional:** `LeftHandGrip` socket on `Sniper_Rifle_A`; shotgun hip-fire
   idle; pistol kneeling crouch.
5. **Then:** Phase 5 — enemy archetype foundation.

---

## 2026-10-05
**Summary:** Left-hand IK built, raised↔lowered transitions tuned, reload-end
ease, **turn-in-place built and working**, **pistol wrist twist fixed** with
the pistol aim offset. Later: **crouch redesigned as a stationary stance**,
lowering snap narrowed, **AnimBP logic moved to C++**. All user-confirmed in
PIE. Dual reload torso motion dropped as won't-fix. Full detail in [TechnicalDesignSpec.md](TechnicalDesignSpec.md)
→ *Animation architecture*.
**The aim → lowered "arm slides through the body" issue is FIXED** (user-confirmed).

- **Left-hand IK (Lyra style):** after the aim offset, CopyBone `hand_r` →
  `ik_hand_gun`, then TwoBoneIK on `hand_l` to `ik_hand_l` (joint target
  `lowerarm_l`). Alpha `LeftHandIKAlpha` = `UpperBodyAlpha` when two-handed
  and not reloading, otherwise 0. Raised only: always-on twisted the arm in
  the lowered clips. Shaped-IK and local-space variants were tried and rolled back.
- **Transitions:** `UpperBodyAlpha` / `LeftHandIKAlpha` **ease up** (FInterpTo
  12 / 10) and **snap down** (`Target < Current ? Target : FInterpTo`), so the
  lowered pose takes over at once instead of the arm sliding through the torso.
- **Reload-end fix:** the snap also fired when a montage ended while lowered, so
  the end of a reload popped. Added a `bEaseLowering` latch:
  `bEaseLowering = IsAnyMontagePlaying OR (bEaseLowering AND Target<Current)`;
  snap only when `Target<Current AND NOT bEaseLowering`. Releasing aim still
  snaps; a montage finishing eases down. **PIE-confirmed.** (Later the
  montage check became `IsSlotActive("DefaultSlot")` so turns don't trip it.)

**Dropped (user, 2026-10-05):** the dual reload spine/torso motion is accepted
as is — not a big issue, no fix planned.

### Turn-in-place (built via the bridge, PIE-confirmed)
Lyra approach in the AnimBP, no C++. Capsule still follows the camera; the mesh
lags via `RootYawOffset` → **Rotate Root Bone**, the aim offsets twist the torso
back to the camera, and past **90°** a 90° turn montage (`AM_Rifle_TurnLeft/Right_90`
in `TurnSlot`/`TurnGroup`, made by the user) plays while its `RemainingTurnYaw`
curve winds the offset back to 0. Only when raised, standing still, not
crouched. Three bugs found in testing:
- **Couldn't move during a turn** — the Lyra turn clips had *Enable Root Motion*
  on; user turned it off on both.
- **Turn didn't stop when moving** — `StopSlotAnimation` only stops dynamic
  montages; replaced with `Montage_StopGroupByName(TurnGroup, 0.2)`.
- **Would have cancelled fire/reload** — `Montage_Play` defaults
  `bStopAllMontages` to true; set false (caught before testing).
Threshold tried at 45° (with `TurnScale` so a turn closes exactly the gap) —
user rolled back to 90°; `TurnScale` stays (≈1 at 90°).

### Pistol wrist twist — fixed
Duals twisted their wrists when the aim offset yawed: everything used the
rifle AO. `AO_MM_Pistol_Idle_ADS` samples had the same missing base pose as the
rifle ones; user set base pose = `MM_Pistol_Idle_ADS_AO_CC` on all 15. AnimGraph
now chains rifle → pistol aim offsets with exclusive alphas by `AnimType`, and
the dual left arm uses the pistol AO (yaw sign flipped for the mirror).

*(Committed and pushed by the user mid-session.)*

### Crouch — redesigned as a stationary stance (PIE-confirmed)
**New design canon from the user** (imported into `Lore_And_Design_Notes.md`):
constant motion in fights; crouch is momentary cover or reload cover. So: no
crouch-walking, the camera doesn't move, crouch only applies standing still,
moving stands up and moves as standing (strafe if aiming), stopping
re-crouches. Slide-to-prone on crouch-while-moving is an **unconfirmed idea**.
- **C++ (applied by Claude on request):** `bCrouchRequested` + `UpdateCrouch()`;
  `bMovementCancelsCrouch` flag (default false = retain the request).
- **Camera bug:** the first version adjusted the boom in `OnStartCrouch`/
  `OnEndCrouch`; the engine's callbacks don't always pair, and the camera drifted
  out of the map. Now the boom Z is derived from the capsule's current size every
  frame, plus an optional eased `CrouchCameraOffset` (default 0).
- **AnimGraph:** top-level crouch branch (crouch idle / crouch walk per weapon);
  user built `BS_MM_Pistol_Crouch_Walk`. The walk is only a low-ceiling fallback now.
- Crouch blend times were silently 0.1 s — pin edits never reached the node
  settings; fixed via the `Node` struct (new gotcha).

### Lowering snap narrowed (PIE-confirmed)
User felt the raised→lowered snap everywhere. It now applies only to
**two-handed weapons, standing upright and still**; moving, crouched, duals and
post-montage drops ease. Crouched duals blend their arm layers via an eased
`DualCrouchBlend`, so standing up no longer snaps. Inertialization was
designed (spec → *Open*) and parked — not needed so far.

### AnimBP logic moved to C++ (PIE-confirmed: "roughly the same as before")
User was concerned the Event Graph had become a mess (~140 bridge-built
nodes). Option B, done by Claude on request: `UProjectBopisAnimInstance`
computes everything in `NativeUpdateAnimation`; `ABP_FirstPersonArms`
reparented, Event Graph emptied, no Blueprint variables left (including the
dead `bUseLoweredUpperBody`). Rehearsed on throwaway copies first — the first
rehearsal showed Blueprint/C++ variables only merge on exact type match, so the
AnimGraph-facing reals became `double`. Tuning values are now class defaults.
From here, anim logic changes are C++ edits the user can review in git.

*(Committed and pushed by the user.)*

### Clean-up and Step 8 (third-person conversion wrap-up)
- **Clean-up:** empty `Blueprint Update Animation` node deleted (the AnimBP's
  Event Graph is now completely empty). Leftover template assets
  `ABP_FP_Copy` + `CtrlRig_FPWarp` reference-checked by grep (used only by each
  other) and deleted via the bridge — the first delete of `ABP_FP_Copy` got
  reloaded by the editor, but it was gone from disk shortly after.
- **"FirstPerson" renamed out** (user did the editor renames + Fix Up
  Redirectors; `Content/FirstPerson/` folder name kept by choice):
  `ABP_Player`, `BP_PlayerCharacter`, `BP_GameMode`, `BP_PlayerController`,
  `MI_Colorway`, `Lvl_Sandbox` (external actors moved with it). A content-wide
  grep found no references to the old names — only stale compiled function
  names inside `ABP_Player`/`BP_PlayerCharacter`, cleared by compile + save
  (needed a node nudge to dirty them; compile alone didn't).
- **Config:** `DefaultEngine.ini` startup/default map → `Lvl_Sandbox`, default
  game mode → `BP_GameMode`; stale `[UnrealEd.SimpleMap]` removed from
  `DefaultEditor.ini`. Editor restart confirmed map and game mode work.
- **C++ comments** (applied by Claude on request, comment-only): four
  "first person" class comments and the stale `DoCrouchStart` comment.
- **Docs:** `CLAUDE.md` and the GDD (+ html) now say third-person; GDD "Where
  the build is" refreshed; spec gains *Character rig (third person)* with the
  first-person rig and projection principle kept as dated history, plus a
  refreshed *Current state*; `ProjectPlan` Phase 4.5 marked complete and
  synced; lore notes record the conversion as finished.

### Merged to main — third-person conversion closed
Work order deleted (in git history). `main` fast-forwarded to
`tps-conversion` locally (`git fetch . tps-conversion:main`, no checkout —
the user's attempt errored, likely from switching branches with the editor
open); the user pushed. **Phase 4 backlog swept** in `ProjectPlan`: left-hand
IK, TEMP timer and rifle grip ticked as done/superseded; muzzle-flash-north
left open pending a PIE look.

### ▶ RESUME HERE
1. ~~Commit the sweep~~ — done (user, 2026-10-06).
2. ~~Muzzle flash faces north~~ — checked in PIE 2026-10-06, fixed; closed.
3. **Ammo HUD + pickups (Phase 4 C–D)** — on hold by user choice; ask before
   starting.
4. **Phase 5 — enemy archetype foundation** is the next phase.
5. Optional polish carried forward: shotgun per-round reload loop (waits on
   the user's montage), 180°/crouched turn-in-place; design calls: reticle
   hiding in non-aim, shoulder swap.

---

## 2026-10-04
**Summary:** Big animation session. Hip-fire (weapon raised/lowered) compiled
and tested. Animation source moved **back to Lyra**. The AnimBP was rebuilt
into a layered architecture: strafe blend spaces, orientation warping,
upper-body montage layer, raised hip-fire pose, aim offset. **Dual pistols
built end to end for the demo.** Bridge proxy proven across six real editor
restarts (one of them a crash). Many bridge limits mapped.

### ▶ RESUME HERE
1. **Dual reload spine motion** (left as is by user choice). `AM_Pistol_Reload`
   leans/twists the torso for a two-handed reload; in the dual setup the right
   arm plays it from `spine_01` up, so the spine moves. Fix agreed but deferred:
   user makes a no-spine copy (`MM_Pistol_Reload_Dual` + `AM_Pistol_Reload_Dual`,
   offhand montage repointed to it), then option (B) — a `DualReloadMontages` map
   used instead of `ReloadMontages` when dual-wield (small C++, present for review).
2. **Next feature (Claude's suggestion): turn-in-place** for the raised/aim stance.
3. Remaining Step 7 items — see the work order.
4. Housekeeping: the editor's asset registry lost track of `BP_DualPistols` and
   (briefly) `ABP_FirstPersonArms` — bridge saves failed with "Asset does not
   exist" while the assets were loaded and working. An editor restart re-scans.

### Hip-fire (code compiled 2026-10-04 00:07, PIE-tested)
As designed in the 2026-10-04 spec section *Weapon raised vs lowered*: trigger
pull snaps yaw to camera, strafe stance, lowers after `LowerWeaponDelay`.
**Change during testing:** hip-fire strafes at **free-run speed (500)**, not
aiming speed — `MaxWalkSpeed` now follows the aim button only, set per frame.

### Animation direction — back to Lyra (user decision)
Shotgun Locomotion Pack quality judged below Lyra. Lyra is the source for all
weapons; from the pack only `anim_shotgun_stand_idle` (lowered shotgun idle) and
probably `anim_shotgun_aim_reload`. User authored `MF_Rifle_Idle_Lowered`,
`MM_Rifle_Jog_Fwd_Lowered`, and `MM_Unarmed_Idle_Ready_Rested` (unused now).

### AnimBP (`ABP_FirstPersonArms`) — built this session, mostly via the bridge
Full architecture in [TechnicalDesignSpec.md](TechnicalDesignSpec.md) →
*Animation architecture*. Highlights:
- **Event Graph:** pawn `IsValid` guard (killed the editor-preview "Accessed
  None" spam); `Speed`, `Direction`, `CardinalDirection` + `WarpAngle`,
  `AimPitch`, `bIsWeaponRaised`, `UpperBodyAlpha`, `LeftArmAlpha`,
  `DualLoweredAlpha`, `CurrentAnimType`.
- **Strafe:** user-built `BS_Rifle_Strafe` / `BS_Pistol_Strafe` (Direction ×
  Speed, Lyra 4-way walk/jog) in the Move state.
- **Diagonals:** forward-left / back-right scissored (Lyra side clips match only
  one diagonal pair). Fixed with **orientation warping** — Animation Warping
  plugin enabled; cardinal clip + leg rotation by `WarpAngle`.
- **Montages upper-body only:** fire/reload over a `spine_01` layer, legs keep
  full stride.
- **Raised hip-fire upper body:** hip-fire idle under the montage slot, weight
  `UpperBodyAlpha` (raised OR montage playing).
- **Aim offset** `AO_MM_Rifle_Idle_Hipfire`. Its 15 samples had **no base pose**
  (made the character giant); user set base = `MM_Rifle_Idle_Hipfire_AO_CC`.
- **Lowered shotgun idle** in the Idle state (user, by hand).

### Dual pistols (demo feature) — built end to end
- **Code (applied by Claude on request, compiled 15:15 + 18:11):** `AWeaponBase`
  gains an `OffhandMesh` component, `bDualWield`, off-hand grip offsets,
  alternating fire (muzzle/feedback per hand, `WasLastShotOffhand()`);
  `UWeaponHolderComponent` attaches it to `hand_l` and recovers it on unequip;
  character gains `OffhandFireMontages` and `OffhandReloadMontages`.
- **Design decisions (user):** alternate L/R fire; **reload normally**
  (supersedes the spec's "throw away when dry"); starting weapon for now.
- **`BP_DualPistols`:** mag 24 / reserve 120 (max 240), `AnimType Pistol`,
  off-hand grip tuned by user.
- **Raised:** mirrored pistol idle on the left arm (`MDT_Mannequin`, user-made;
  Mirror node; `clavicle_l` layer).
- **Left recoil + reload:** `OffhandSlot` (own slot group `OffhandGroup`, so it
  plays alongside the default slot) inside the mirrored branch;
  `AM_Pistol_Fire_Offhand`, `AM_Pistol_Reload_Offhand`.
- **Lowered:** whole body (pelvis-rooted layer) from the unarmed walk/jog with
  pistol finger grips; unarmed blend space play rate **0.7** (its cadence is
  naturally quicker than the pistol jog).

### Tried and rolled back
- **Shotgun upper-body layering via cached poses** — first attempt broken
  (byte-typed enum compare), second built with user-placed Use Cached Pose nodes,
  then judged "looks bad" and removed.
- **Sync groups** between in-state leg blend spaces and top-level arm players —
  never demonstrably worked (arms kept their own cadence). Whole-body unarmed for
  lowered duals made sync unnecessary.
- **One-handed single pistol** (free arm unarmed: swinging, still, reduced swing,
  rested pose over the midriff, synced swing) — all judged worse. **Single
  pistols stay two-handed.** Fully removed.

### Bridge findings (details in ProjectPlan Gotchas)
Can't create nodes in anim states (can set properties there); can't create Use
Cached Pose nodes; anim compile errors invisible; graph DSL read-back lossy;
array properties can't change size and contents in one write; blend space sample
writes crashed the editor on save; derived data unreadable; asset registry can
drop assets. **The stdio proxy reconnected after every restart, including a crash.**

---

## 2026-10-03
**Summary:** Editor bridge made restart-proof (stdio proxy). Conversion out of C++ entirely — Steps 1–6 done. Crouch brought
forward. Shotgun work started. A week-old bridge-reconnect belief corrected.

### ▶ RESUME HERE — next session, in this order

1. ~~**First thing: confirm the new bridge proxy is live.**~~ **Done 2026-10-04 — proxy confirmed live and restart-proof (six restarts, one a crash).** The stdio proxy
   (`.claude/unreal-mcp-proxy.mjs`) was set up 2026-10-03, but the session
   that built it stayed on the old direct-HTTP connection by choice, so it
   has **not yet run inside a real Claude Code session**. A fresh session
   picks it up automatically. **Ask the user before running any check**
   (standing rule — no MCP checks or changes without a yes). Checks to
   propose: `mcp__unreal-mcp__list_toolsets`
   responds; `claude mcp get unreal-mcp` shows `Type: stdio`, Connected.
   Then, at the next editor restart, confirm a call afterwards reconnects
   without `/mcp`. Evidence so far: in the 2026-10-03 session the bridge
   kept working across **two real editor restarts** with no `/mcp` — but that
   session may have been on the old direct-HTTP connection (Claude Code
   recovering it), so it is not proof the proxy path works.
   If anything fails, the old config is in the bridge Gotcha in
   [ProjectPlan.md](ProjectPlan.md). **Also: commit `.claude/` files** — the
   proxy script and `unreal-mcp-tools.json`, not `settings.local.json`.
2. ~~**Compatible Skeletons**~~ **Done** — verified in the saved
   `SK_Mannequin.uasset` (`CompatibleSkeletons` lists the pack's skeleton).
3. ~~**Rebuild.**~~ **Done** 19:20 — `EWeaponAnimType::Shotgun` compiled.
4. **Step 7 — animation.** Plan rewritten in
   [TPSConversion_WorkOrder.md](TPSConversion_WorkOrder.md).

### State of the conversion (branch `tps-conversion`)

Steps 1–6 complete and PIE-confirmed. Step 7 (animation) and Step 8 (docs +
merge) remain. **No C++ work left in the conversion.**

- **Step 4 — crouch, brought off the backlog and done.** Hold/toggle switch
  via `bCrouchIsToggle` (`BlueprintReadWrite`, so a future options menu can
  drive it). Both input edges bound to one action. `Crouch()`/`UnCrouch()` set
  `bWantsToCrouch` rather than changing height, so the component retries each
  frame — releasing under a low ceiling is safe.
- **Step 5 — muzzle obstruction added and confirmed.**
  `bBlockShotWhenMuzzleObstructed` traces actor-centre→muzzle and returns the
  new `EFireResult::Blocked`. **Planned refinement: lower the weapon instead of
  silently suppressing** — that moves the check from on-demand to per-frame
  state. See *Muzzle obstruction* in
  [TechnicalDesignSpec.md](TechnicalDesignSpec.md).
- **Step 6 — grip re-tune done** by hand for the three existing weapons.
  `BP_Shotgun` will need its own.

### Shotgun — started, not finished

- **`EWeaponAnimType::Shotgun` added** (code only, not compiled). Reverses an
  earlier call to skip it, which was made when Lyra had only three shotgun
  idle poses and no locomotion.
- **Shotgun Locomotion Pack added** at `Content/ShotgunLocomotionPack/`. Its
  bundled skeleton is a *copy of the stock UE5 mannequin* — bone sets verified
  identical including the full IK rig — so **no retargeting**, just Compatible
  Skeletons. 175 clips: authored 45° diagonals (true 8-way), sprint, 3×3 aim
  offset, turn-in-place in both stances, crouch, and stance transitions. Its
  aim/non-aim split maps **directly onto `EMovementStance`'s FreeRun/Aiming
  pair** already in code.
- **Open: can this pack serve the rifle too?** A shotgun and an assault rifle
  are held almost identically. If the pose reads with `Assault_Rifle_A`, one
  pack covers both with a better set than Lyra. Costs nothing to look.
- **Shotgun logic applied and compiled** (Claude wrote it, user-approved after
  review; rebuilt 19:46): pellets (`PelletsPerShot`, `PelletSpreadAngle`),
  range falloff (`FalloffStartRange`/`EndRange`/`MinDamageMultiplier`,
  hitscan only), and `EReloadStyle::PerRound` — round-by-round loading that
  firing interrupts. Shotgun is SPAS-style semi-auto, no pump. Details in
  [TechnicalDesignSpec.md](TechnicalDesignSpec.md) under *Reload* and
  *Pellets and damage falloff*. All defaults leave existing weapons unchanged.
- **`BP_Shotgun` tuned and made the starting weapon** (bridge, user-approved):
  Semi, `TimeBetweenShots 0.3` / `Intended 0.45`, 8 pellets × 12 dmg at 4°,
  falloff 600→1800 to 0.2×, `PerRound` reload 0.4s + 0.5s/round.
  `BP_FirstPersonCharacter`'s `StartingWeaponClass` was `BP_BattleRifle`,
  now `BP_Shotgun`. **Not yet PIE-tested.**
- **`BP_Shotgun` created** (via the bridge, user-approved) — duplicated from
  `BP_BattleRifle`, then re-pointed: `Shotgun_A`, `Fire_Shotgun_W`,
  `ShotgunA_Fire_Cue`, `P_Shotgun_MuzzleFlash_01` (socket `MuzzleFlash`,
  verified on the mesh). `AnimType Shotgun`, Semi, no zoom. **Placeholder
  stats:** 12 dmg (meant per pellet), 2500 range, `TimeBetweenShots 0.8` /
  `Intended 0.9`, spread 0→3°, `BloomPerShot 0.35`, mag 6 / reserve 24 (max
  48), reload 2.5s, reticle radius 0.16–0.30. **Grip offsets zeroed** — needs
  its own tune. **Not in the loadout** (`StartingWeaponClass` untouched). No
  Shotgun entries in `FireMontages`/`ReloadMontages` yet, so it fires with no
  body animation. The ABP's anim-type Blend Poses has no Shotgun pin either.
- **Caveat:** the shotgun cannot be *tuned* yet. Damage is still inert
  (nothing has `Health`) and there is no range falloff for any weapon, so it
  would be a sniper rifle that fires eight pellets.

### Corrected this session

- **The bridge does not need a fresh session.** `/mcp` reconnects it. The
  2026-09-28 note claiming otherwise was wrong and has been struck. Verified
  the editor was serving correctly the whole time — twice, on different PIDs.
- Earlier advice to skip `EWeaponAnimType::Shotgun` is reversed, per the pack.

### Working tree at session end (uncommitted)

`SciFiWeapDark` deleted (484 files). Modified: `SK_Mannequin`, the four weapon
BPs, `BP_FirstPersonCharacter`, `IMC_Default`, five source files, four docs.
New and untracked: `IA_Crouch`, `Content/ShotgunLocomotionPack/`, and the
`__ExternalActors__`/`__ExternalObjects__` folders the pack's demo maps
brought with them (`Demo/`, `ThirdPerson/`, `ShotgunLocomotionPack/`) — World
Partition data for maps we do not use, harmless but worth pruning if the pack
is ever trimmed.

### Still open from before

- `WBP_Ammo` text binding never verified in PIE — predates the conversion.
- ~~`SciFiWeapDark` still present.~~ **Deleted 2026-10-03** — all 484 files
  removed. `IA_Crouch` created and mapped in `IMC_Default` the same day.
- The branch carries the setting-change docs, the weapon pack swap and both
  lore imports alongside the conversion. Fine if it merges; worth deciding at
  Step 8 whether that happens then or sooner.
- Story rewrite is design-side and outstanding; PART 2 of the lore notes is
  `[PROVISIONAL]`. **The climax is the open question** — the coup was the
  event that ended the story, and a revelation is not an ending.

---

## 2026-09-30
**Summary:** Third-person conversion: four of six active steps landed and
tested. Two lore imports. Enemy and combat-ability specs written. One
long-standing bug proved to be a non-bug.

**Branch `tps-conversion`.** Created 2026-09-25 after an audit found
first-person assumptions confined to three files (`ProjectBopisCharacter`,
`WeaponHolderComponent::AttachWeaponToHand`, and one line of `WeaponBase`).
Work order at [TPSConversion_WorkOrder.md](TPSConversion_WorkOrder.md),
sequenced by rebuild boundary rather than topic.

**Steps landed, each confirmed in PIE:**
- **Step 1 — camera rig + mesh consolidation.** `FirstPersonMesh`,
  `HiddenFirstPersonBones` and `SetFirstPersonVisibility` deleted; spring arm
  + camera added; weapon attaches to `GetMesh()`. Atomic — deleting
  `GetFirstPersonMesh()` breaks the holder and both montage calls in the same
  compile.
- **Step 2 — GRB movement.** `DoMove` now derives axes from control-rotation
  yaw (was actor vectors, only ever correct in first person). `EMovementStance`
  + `ApplyMovementStance()` owns the mutually-exclusive rotation flag pair.
  Written with **three** states — `FreeRun`, `Aiming`, `AnimationDriven` — the
  third for the shootdodge's prone turn-in-place, so call sites need no revisit.
- **Step 3 — aim stance + camera move.** Implemented **pull-style**:
  `DoAimStart`/`DoAimEnd` set state only, and `UpdateCameraTransition()` derives
  boom length, socket offset and FOV from state every frame. Character now
  ticks; tick is load-bearing. Fixed a real bug in passing — aim was gated on
  `HasZoom()`, so unscoped weapons had no aim stance at all.
- **Step 5 — firing and aim source.** The only correctness fix in the
  conversion. Two-stage: camera trace decides *what* you hit, muzzle decides
  *where* the shot comes from. `GetMuzzleLocation()`/`GetMaxRange()` added to
  `AWeaponBase`; `MinConvergenceDistance` (200) clamps convergence so a
  near-wall hit can't aim the shot backwards. Confirmed: bullets now leave the
  barrel, and shooting through cover you're standing behind is fixed.

**Step 4 (crouch) moved to backlog** — deferred, not reversed. The stated
reason (a second full strafe blendspace) turned out to be **wrong**; see below.

**TEMP 5s timer removed — and it was never doing anything.** Deleted the
`FTimerHandle`, the `SetTimer` call and the dead include. Measured in PIE: the
weapon position is *identical* for a whole session with no change at the
five-second mark. `ProjectPlan.md` claimed the timer was "what makes the weapon
position correct"; that claim is now corrected, and the August mistimed-attach
diagnosis is downgraded to unproven.

**Lyra library inventory** (prompted by the Step 7 estimate). Aim offsets are
**already built** as `AimOffsetBlendSpace` assets with full 15-pose grids.
Complete strafe clip sets for Rifle and Pistol — Walk and Jog, four directions,
each with Start/Stop/Pivot — plus turn-in-place. Only three BlendSpaces are
assembled, so the standing strafe blendspaces need *assembly from existing
clips*, not authoring. **Step 7 revised from weeks to days.**

**Correction that changes a decision:** crouch was backlogged partly because I
said it dragged a crouched strafe set behind it. It doesn't — full crouch sets
exist for both weapons (entry, exit, idle, four-way walk with starts/stops/
pivots, crouch turn-in-place) and `BS_MM_Rifle_Crouch_Walk` is already
assembled. Crouch's animation cost is near zero; the C++ is an afternoon. Worth
reconsidering the deferral.

**Lore — two imports, gameplay content excluded by instruction.**
- `Project_Bopis_2003_Current_Lore.txt` — 2002→2003, real history →
  alternate history, femme fatale second lead, conspiracy, story spine.
- `Project_Bopis_Noir_Action_Horror_Direction.txt` — **genre pivot to noir
  action horror**. Aswang ruling class literally feeding on the people beneath
  them. Now PART 1 of the lore notes.
- Both sources say "first-person" in their *gameplay* sections, which the
  standing instruction excludes — so the third-person conversion is unaffected,
  and the reasoning is recorded so it isn't re-litigated.
- **The coup plot was dropped** in conversation: Plan A/Plan C, the generals,
  the Senator, the President and the military fragmentation are struck. PART 1's
  four-step ladder is the spine. **The climax is now an open question** — the
  coup was the *event* that ended the story, and a revelation is not an ending.
- Also decided: Aswang are Underworld-style (normal clothes, monstrous head and
  hands), do **not** transform mid-combat, are **not known to exist**, and the
  protagonist has **no human allies**. The story is being rewritten, so PART 2's
  plot sections are marked `[PROVISIONAL]`.

**Tech spec** gained a rewritten **Enemies** section (three families, two-layer
health so the resilience break produces an *event* and tankiness doesn't erode
the bloom skill test, vocalizations as state telemetry, readability layered by
distance) and a new **Combat abilities** section (dual pistols by pose
mirroring, shootdodge adapted from a two-handed pistol asset, prone as a
transient post-dive state, `CustomTimeDilation` for bullet-time).

**Next session:** Step 6 grip re-tune (data pass — offsets are meaningless
against a full body at world scale), then Step 7 animation. Open: whether to
bring crouch forward given the corrected cost, and the muzzle-inside-geometry
case from Step 5.

**Editor bridge:** not used this session. New standing rule — ask before any
`unreal-mcp` call; the responses are large. Grepping `.uasset` binaries for
`/Game/...` paths and listing asset folders covered everything needed here,
including the whole animation inventory.

---

## 2026-09-21
**Summary:** Weapon pack swapped to conventional firearms. Stale references
cleaned. No C++ changed.

**Pack swap.** User added `Content/MilitaryWeapSilver/` and re-pointed all
three weapon Blueprints: `BP_Pistol` → `Pistols_A` + `Fire_Pistol_W` +
`PistolA_Fire02`; `BP_CloseRangeRifle` → `Assault_Rifle_A` +
`P_AssaultRifle_MuzzleFlash` + `RifleA_Fire_Cue`; `BP_BattleRifle` →
`Sniper_Rifle_A` + `Fire_SniperRifle_W` + `P_SniperRifle_MuzzleFlash_01` +
`SniperRifleA_Fire_Cue`. `BP_FirstPersonCharacter` also modified (not yet
inspected). `SciFiWeapDark` to be deleted by the user from the Content
Browser.

**Reference audit** (grep of `.uasset`/`.umap`/source/config for
`SciFiWeapDark`) found two leftovers outside the pack itself:
- `BP_Pistol` — `WeaponMesh` component template's
  `AnimationData.AnimToPlay` still pointed at the old `Fire_Pistol_W`. Inert
  at runtime, but a hard reference. **Cleared via the bridge, compiled,
  saved**; asset registry now reports zero referencers on the old animation.
- `SK_Mannequin` (skeleton) — editor-only preview attachment of
  `Darkness_AssaultRifle` (from eyeballing the hand socket in Persona).
  Predates today. The bridge can't reach `PreviewAttachedAssetContainer`;
  **cleared by hand in the skeleton editor.**
Everything else clean: other Blueprints, all C++, all `Config/`. Docs
mention the old pack only historically.

**Docs:** `TechnicalDesignSpec.md` (implications section, lightmap-UV
gotcha, vendor list, changelog), `ProjectPlan.md` (setting-change note,
new Gotcha about hidden component-template references, changelog).

**Next:** unchanged — `WBP_Ammo` verification, then pickups, then weapon
switching. Grip offsets, muzzle socket names and the "faces north" bug all
need a re-look against the new meshes, since every socket and animation
notify is now a different asset.

---

## 2026-09-13
**Summary:** Setting change. Docs propagated. No code changed.

**The change.** User supplied `Project_Bopis_2002_Noir_Setting_Change.txt`
from the design side. The 2098 sci-fi/cyberpunk premise — synthetic enemies,
energy weapons, the AI-antagonist storyline, High/Low City, the neutral
player-projection protagonist — is discarded in full. The game is now a
**gritty noir first-person action shooter set in the Philippines, 2002**:
heavy noir narrative, John Woo / heroic-bloodshed action, Filipino crime
cinema as the identity source, and a **defined, authored protagonist** (male,
35+, cynical, tired, deliberately not Tequila). Human enemies. The explicit
goal is *not* "Max Payne in the Philippines." Old gameplay ideas (bloom,
hip-fire, linear structure, arenas, 10+ missions) are neither canon nor
obsolete — to be reconsidered individually. The story is the design side's
current task; not to be invented here. Protagonist name/history/profession/
motivation are `[UNDECIDED]`.

**Docs updated:**
- `Design Document/Lore_And_Design_Notes.md` — rewritten. New doc verbatim as
  PART 1 (canon). Old §2–5 gameplay sections + the readability principle
  preserved as PART 2, each tagged *under reconsideration*. Old world/lore
  sections dropped (they're in the discard list).
- `Design Document/GameDesignDocument.md` + `.html` — full rewrite for the
  new premise, still pitch-facing/non-technical. Three pillars derived
  strictly from the doc. Every `[UNDECIDED]` item is an **Open** callout; every
  carried-forward mechanic is an **Under reconsideration** callout. Fidelity
  target (Halo 1–2 era, baked lighting) kept — it fits 2002. HTML redesigned:
  newsprint ground, ink, tabloid-red accent, Oswald/Spectral/Courier Prime;
  tab JS unchanged.
- `Documentation/TechnicalDesignSpec.md` — new "Setting change — implications"
  section at the top (carried / superseded / new candidates / under
  reconsideration). Coilgun-fragmentation rationale removed from the
  projectile section (system kept, purpose open). Enemies human. Narrative
  "no conversation system" rule reopened. `SciFiWeapDark` marked placeholder.
- `Documentation/ProjectPlan.md` — dated note at top; Phase 5/6 reworded.
- `Documentation/Research.md` — Halo 2 AI notes annotated as still applicable.
- `CLAUDE.md` — opening paragraph rewritten.

**Code:** untouched. One comment (`ProjectBopisCharacter.cpp` "Halo-style
zoom") describes the mechanic accurately and was left alone.

**Flagged, not decided:**
- The three weapons' *roles* and *art* were designed for the old premise.
  Roles are open; art is placeholder. The 2002 arsenal is a design call.
- Pickups (next per the agreed Phase 4 order) — the "dropped weapons vs
  ammo pickups vs both" question should be answered against the new
  direction before building. John Woo gunfights suggest picking guns off
  the floor is on-theme, but that's an observation, not a decision.
- Dual-wield, slow-mo, dive/slide, destructibility are named in the action
  direction and unscheduled. Engineering notes for each in the tech spec.

**Next:** unchanged — HUD verification (`WBP_Ammo` binding, needs the
editor bridge back), then pickups, then weapon switching. Then Phase 5.

**Editor bridge:** disconnected this session (`unreal-mcp` connection
refused). None of this work needed it.

---

## 2026-08-31 (6)
**Summary:** Remaining Phase 4 order agreed, HUD C++ written (awaiting
review), and a fidelity target locked in.

**Order for the rest of Phase 4:** HUD → pickups → weapon switching →
everything else. Weapon switching sits after pickups deliberately:
`MaxCarriedWeapons` is already 2, but nothing can currently fill the second
slot, so switching has nothing to switch between until pickups exist.

**Ammo HUD, C++ side written.** Three `BlueprintPure` accessors on
`UReticleWidget` — `GetAmmoInMagazine`, `GetReserveAmmo`, `IsReloading` —
plus a `GetEquippedWeapon()` helper that collapses the Character →
WeaponHolder → Weapon walk the existing accessors were each repeating.
**Presented for review, not yet built.** The widget side is blocked on a
Text Block being placed by hand: the editor bridge has no UMG toolset, so it
can edit widget graphs and properties but cannot add widgets to the tree.

**Process correction.** The user reasserted: *always have me review any C++
code.* Over the preceding stretch they had repeatedly said "apply it
yourself", and I let that harden into a default rather than treating each as
a one-off. Memory updated — approval is per-instance and never carries
forward, and this applies to small changes too, not just substantial ones.

**Fidelity target decided: Halo 1–2. Baked lighting, minimal dynamic
lighting, fun over fidelity.** Briefly considered and dropped an
Xbox/PS2-era target before settling here. Rationale recorded in the design
document: performance headroom converts into more enemies on screen and a
steadier frame rate, both of which matter more to a firefight than surface
detail; the High City / Low City art direction reads on shape and colour
rather than micro-detail; and it keeps scope pointed at combat design.

**Found while recording it: the project is currently configured the exact
opposite way.** `r.AllowStaticLighting=False` (the UE5 default) means nothing
can bake lightmaps at all, alongside Lumen GI, Lumen reflections, ray tracing
and Nanite all enabled. Documented the full current-vs-target table and the
switching costs in `TechnicalDesignSpec.md` — notably that
`AllowStaticLighting` needs an editor restart, vendor meshes may lack
lightmap UVs, levels need relighting and a bake, and Nanite is a separate
call that shouldn't be bundled in. **No settings changed** — flagged for the
user's decision, since it's project-wide and disruptive.

Also noted for later: with this target, muzzle flashes and weapon fire should
not cast dynamic light — emissive materials and particles carry the read
instead, which is what the era did anyway.

---

## 2026-08-31 (5)
**Summary:** Built the bloom reticle for real — it had never actually been
wired — then replaced the texture crosshair with procedural materials and a
per-weapon crosshair system. All confirmed working in PIE.

**Found: the reticle never consumed bloom.** `UReticleWidget::GetCurrentBloom()`
has existed since Phase 3 and is `BlueprintPure`, but `WBP_ReticleWidget`'s
event graph contained exactly three nodes — `PreConstruct`, `Construct`,
`Tick` — **all with zero connected pins**. The crosshair was a static image.
Phase 3 was marked complete on "reticle confirmed visible in PIE", and the
expansion step was quietly assumed done. The design doc has always required
bloom to drive the spread *and* the reticle from the same number; only the
spread half existed. Not a regression — an unimplemented requirement.

**Why a material, not a scaled texture.** First pass drove
`SetRenderScale` from bloom. That works, but scaling a bitmap thickens the
stroke along with everything else — the user wanted the circle to grow at
constant line weight. Options weighed: (1) split into separate line images
and *move* them apart (what most shooters do, but can't produce a growing
circle), (2) a material with radius/thickness as parameters, (3) nine-slice
(fails on curved edges). **Chose (2).** Since the widget never scales,
`Thickness` stays constant in real pixels no matter how far `Radius` grows.

**Two materials built through the bridge**, both UI-domain translucent:
- **`M_Reticle`** — ring. `length(UV − 0.5)` compared against `Radius`, with
  a `Thickness` band, into Opacity; `Color` into Emissive.
- **`M_Reticle_Corners`** — rounded-square corner brackets. Distance is
  `lerp(max(|x|,|y|), length(p), Roundness)` — a squircle whose corner
  rounding is one dial. The brackets come from masking on
  `min(|x|,|y|)`: large only near corners, near zero at the middle of each
  side, so thresholding it cuts the sides away.

**Bug in the corner material, fixed.** `CornerCut` was an *absolute*
threshold (0.11) while idle `Radius` was 0.12 — so at rest the mask erased
almost the entire shape and the crosshair looked invisible with near-zero
thickness, then brackets appeared from nowhere as bloom grew. Thickness was
never actually changing; the mask was eating it. Fixed by making the
threshold **`Radius × CornerCut`**, so brackets hold the same proportion of
each side at any radius. `CornerCut` is now a fraction (0.55), not a
distance — old absolute values are meaningless.

**Per-weapon crosshairs.** New `FCrosshairSettings` USTRUCT on `WeaponBase`
(`Material`, `Size`, `MinRadius`, `MaxRadius`, `Thickness`, `Color`) plus
`GetCrosshairSettings()` on both `WeaponBase` and `UReticleWidget` (the
latter returning a default-constructed struct when nothing is equipped, so
the reticle never collapses to zero). A crosshair isn't skeleton-specific
the way a montage is, so it belongs on the weapon alongside `FireSound` and
`HitDecalMaterial`.
- **Convention:** every crosshair material exposes `Radius`, `Thickness`,
  `Color` by name. Materials may draw anything and ignore any of them —
  setting a parameter a material doesn't declare is a silent no-op — but
  this is what keeps the widget generic instead of knowing which weapon uses
  which material.
- Widget graph compares the weapon's `Material` against a new
  `LastCrosshairMaterial` variable and only calls `SetBrushFromMaterial`
  **on change**. Swapping every tick would rebuild the dynamic material
  instance each frame and discard the parameters written to the previous one.
  Because it keys off the equipped weapon rather than a swap event, it works
  for every acquisition path without any of them notifying the UI.
- `Size` drives the canvas slot each tick. Needed because `Radius` and
  `Thickness` are fractions of the widget — `Radius` can't exceed ~0.5
  without clipping outside it, so widget size is the only way to make the
  reticle physically bigger. Uniform scaling was chosen over
  pixel-constant thickness, so existing tuned values keep their meaning.
  Note this now overrides the designer's slot size at runtime, and a `Size`
  of 0 draws nothing.

**Final values:** pistol `M_Reticle_Corners` (thickness 0.05, user-set),
close-range rifle `M_Reticle` 0.16→0.44 / 0.022, battle rifle `M_Reticle`
0.08→0.26 / 0.014 — tighter and thinner reads as more precise.

**Bridge notes:** the material toolset turned out to be fully capable —
`create_material`, `add_expression`, `connect_expressions`,
`connect_to_output`, `recompile` were enough to author both materials
end to end. Two API details worth remembering: a Blueprint **variable needs a
compile before its getter/setter node types exist**, and overloaded nodes
(`SetScalarParameterValue`, `GetDynamicMaterial`, `SetBrushFromMaterial`)
need `declaring_class` to disambiguate — without it you get the
MaterialParameterCollection or by-ref-Brush variant instead.

**Recurring friction:** the `unreal-mcp` client caches a failed connection
and never re-probes, so once the editor closes mid-session the bridge stays
dead for that session even after the editor returns. Confirmed repeatedly by
curling the endpoint (HTTP 405 = listening) while the tools stayed
unavailable. ~~Only a fresh session clears it.~~ **Corrected 2026-10-03: type
`/mcp` in the session and reconnect it there.** No new session needed. The
in-app `reconnect_session_connector` tool does *not* work on it — that only
handles claude.ai connectors, and `unreal-mcp` is a project-scoped
`.mcp.json` server (kind `project`), which is the user's to reconnect via
`/mcp`.

---

## 2026-08-31 (4)
**Summary:** Ammo Phase B (reload) built, wired and **confirmed working in
PIE**. Also corrected a wrong call from earlier in the day about what the
editor bridge can build.

**Reload.** Timer-driven off `ReloadDuration`, not animation notifies —
deliberate, since a notify would put authoritative timing inside an asset
the weapon can't see and would break for any holder whose montage differs.
Partial magazines are kept rather than discarded. `EFireResult::Reloading`
added so firing mid-reload is distinguishable and silent. Reload cancels on
weapon swap, handled in `EquipWeapon`'s teardown — otherwise the timer fires
on a weapon no longer held. `bAutoReloadWhenEmpty` is data on the weapon but
acted on by the character, keeping the montage and the state change together.
The montage only plays if a reload actually started, so mashing the key on a
full magazine does nothing.

**Corrected an earlier wrong conclusion.** I'd said reload montages couldn't
be built through the bridge, because `SequenceLength` is read-only and a
montage duplicated from the 0.667s fire montage would truncate a 2s reload.
The first half was right; the conclusion wasn't. **Opening the asset editor
(`OpenEditorForAsset`) forces the recalculation.** Working method:
duplicate → repoint the `SlotAnimTracks` segment → open the asset editor →
save. Recorded as a Gotcha.

Built this way: `AM_Pistol_Reload` (2.0s) and `AM_Rifle_Reload` (2.2s). Also
went back and fixed `AM_Rifle_Fire`, which had been sitting inconsistent
since yesterday — segment 0.533s against a montage claiming 0.667s — so that
accepted tradeoff is gone too.

**Also done via the bridge:** `IA_Reload` created and mapped to `R` in
`IMC_Default`. Note UE 5.8 keeps mappings in `defaultKeyMappings`, not the
`Mappings` property, which reads as empty and will mislead. Writing that
array replaces all of it, so the asset was duplicated to
`IMC_Default_BACKUP` first; all 14 original entries survived with their
modifier sub-object references intact. **That backup is still present and
unsaved** — delete once movement is confirmed.

User assigned the Blueprint values (`ReloadAction`, `ReloadMontages`,
per-weapon `ReloadDuration`) directly.

**Still open:** ammo HUD (Phase C) and pickups (Phase D), per-weapon magazine
sizes (all three still on the `12/60/120` default), plus everything carried
from earlier entries — muzzle flash retest, the TEMP 5s timer, grip position,
ABP `Blend Poses by Enum`, left-hand IK.

---

## 2026-08-31 (3)
**Summary:** Documentation restructure, no code. Split the design document
in two: a pitch-facing non-technical piece and a new technical spec.

**Why:** `GameDesignDocument.md` had become a hybrid — plain-English design
rationale interleaved with parameter tables, class names, and a running
"where the codebase is" log. Fine for implementation, useless for a pitch.

**What changed:**
- **New `Documentation/TechnicalDesignSpec.md`** — everything
  implementation-facing: bloom and rate-of-fire parameters, the configured
  weapon values table, trace-source reasoning, weapon/ammo architecture,
  projectile spawn and self-collision rules, enemy composition approach,
  the three architecture principles (animation ownership, render-affecting
  setters, first-person projection), first-person rig layout, vendor-content
  policy, and a gotchas summary. Updated to current state while moving —
  the old doc still had `IntendedCadence` in shots-per-second and no ammo
  section at all.
- **`Design Document/GameDesignDocument.md` rewritten as a pitch document.**
  No code, no parameters, no jargon. Sections: Overview (with three pillars),
  Combat, Weapons, Enemies, World, Narrative, Scope. Undecided items are
  marked **Open** rather than silently omitted, which reads as deliberate
  rather than incomplete.
- **`Design Document/GameDesignDocument.html` rebuilt** as a tabbed document
  — one tab per section, deep-linkable by hash, keyboard-navigable with arrow
  keys, light and dark themes. Design: sunlit-composite neutrals with a warm
  amber accent (the flag's sun, and Low City's glow without resorting to
  neon-on-black cyberpunk cliché), teal reserved semantically for Open
  questions, Archivo/Newsreader/IBM Plex Mono. A layered-rule motif in the
  masthead echoes the High City / Low City elevation idea.
- **`CLAUDE.md` updated** — this matters for future sessions, since it
  previously pointed at `GameDesignDocument.md` as the file to work from for
  code decisions. Now points at `TechnicalDesignSpec.md`, and explicitly says
  to keep the design document non-technical.

**Constraint respected:** nothing was invented to fill the lore file's
`[UNDECIDED]` gaps. Those became the **Open** callouts — synthetic hostility
cause, protagonist background, Mindanao, corporations/factions, carry limit,
inciting incident, regulatory mechanism.

---

## 2026-08-31 (2)
**Summary:** Big feature session — battle rifle configured, Halo-style scoped
zoom, per-weapon animation selection, first/third-person mesh split, and
Phase A of the ammo system. Also several bridge-workflow lessons learned
the hard way.

**Battle rifle configured** — new `BP_BattleRifle` (`Darkness_SniperRifle`
mesh, `Fire_SniperRifle_W`, `SniperRifleA_Fire01`,
`P_SniperRifle_MuzzleFlash_Dark`, `MI_Generic_1` decal). 35 damage, 8000
range, `MaxSpreadAngle 4`, `BloomPerShot 0.18`, `TimeBetweenShots 0.2` /
`IntendedTimeBetweenShots 0.286`, Semi, zoom at FOV 30. That completes all
three weapon-configuration items in Phase 4. Left animation-driven since
its mesh and fire animation are the same asset family. **Note:** the live
instance reported its mesh as `Darkness_AssaultRifle`, not the
`Darkness_SniperRifle` set — unverified, likely the same missing-compile
issue described below.

**Halo-style scoped zoom.** Zoom previously narrowed world FOV only, and
the arms didn't change — which was the deliberate Phase 3 call
(`FirstPersonFieldOfView` is a separate projection from the main FOV, so
zooming wouldn't distort the gun). User wanted different behaviour;
options were (1) hide arms+weapon while scoped, Halo-style, (2) scale
`FirstPersonFieldOfView` too, (3) ADS-style reposition. **Chose (1)** —
matches the Bungie-era touchstone, avoids near-camera perspective
distortion, and sidesteps the untuned grip position entirely. New
`SetFirstPersonVisibility()` on the character, called from
`DoAimStart`/`DoAimEnd`, gated on `HasZoom()` going in but **restored
unconditionally** on aim-end so a weapon swap while zoomed can't strand
you with invisible arms. Still missing a scope overlay widget.

**Per-weapon animation selection (Option A of three).** Considered:
(A) weapon-type enum + Blend Poses by Enum, (B) Lyra-style Anim Layer
Interface with linked layers, (C) data asset of clips. **Chose A** — one
state machine, only the leaf clips swap, and adding a weapon is an enum
value rather than a graph restructure. B is genuinely better at ~5+
weapons or when weapons need distinct movesets, and A → B is a clean
migration later since the enum becomes the layer selector.
- New `EWeaponAnimType` (Pistol/Rifle) + `AnimType` property and a
  `BlueprintPure GetAnimType()` on `WeaponBase`. The weapon states only
  *which type it is* — consistent with the 2026-08-18 rule that the
  animator owns the clips.
- `FireMontage` on the character became
  `TMap<EWeaponAnimType, TObjectPtr<UAnimMontage>> FireMontages`. Required
  including `Weapons/WeaponBase.h` in the character header: UHT needs the
  complete enum type for reflection, so a forward declaration won't do.
- ABP graph work (enum variable + Blend Poses by Enum inside the existing
  Idle/Move states) is user-side and still in progress.

**Removed the `bUseAnimationDrivenFeedback` gate from the fire montage.**
That flag was governing two unrelated things: where the *weapon's* sound
and muzzle flash come from, and whether the *character* plays its arms
animation. Switching the close-range rifle to code-driven feedback
therefore silently disabled its arm animation. The arms montage now plays
for any weapon with one mapped, independent of the flag. This is a
narrower fix than the earlier proposal to split the flag in two, and
removes the conflation at its source.

**Muzzle flash position fix.** `SpawnEmitterAttached` returns a particle
component that renders in **normal world space**, while `WeaponMesh` is
tagged `FirstPersonPrimitiveType::FirstPerson` and renders through the FP
projection — so the flash drew at the gun's true world position while the
gun drew somewhere else on screen. Now calls
`SetFirstPersonPrimitiveType(FirstPerson)` on the spawned component.
**This may also be the answer to the standing "muzzle flash faces north"
bug** — a world-projected effect on an FP-projected gun would look both
misplaced and misaligned, which would explain why the Cascade local-space
check came up clean. Needs retesting to confirm.

**First/third-person mesh split — corrected mid-implementation.** First
pass removed `GetMesh()->SetOwnerNoSee(true)` and hid `spine_01` upward on
the body so the owner could see their own legs. **User corrected this:**
`FirstPersonMesh` is itself a full-body `SKM_Manny_Simple` positioned at
`(-15, 0, -155)` relative to the camera — standing under it, feet at
ground level — so *it* already provides the legs. `GetMesh()` never needed
to be owner-visible, and hiding `thigh_l`/`thigh_r` on the FP mesh would
have deleted exactly the legs wanted. Final shape: `SetOwnerNoSee(true)`
restored, `OwnerHiddenBodyBones` removed entirely, and a single
`HiddenFirstPersonBones` array (default `head`) trimming only what the
camera sits inside. Side benefit: no shadow stump, since the body mesh is
untouched.

**Ammo system — Phase A complete and tested.** Planned across four phases
(A: state + gating + dry fire, B: reload, C: HUD, D: pickups). Decisions
taken: **separate reserves per weapon** (not a shared pool),
**auto-reload off** by default, **reload cancels on swap**.
- New `EFireResult { Fired, RateLimited, Empty, NoWeapon }`. `Fire()` and
  `FireEquippedWeapon()` now return it instead of `bool`. **Key design
  point:** ammo was deliberately *not* folded into `CanFire()`, because
  rate-limited and empty need different responses — rate-limited must be
  silent, empty must click and (later) auto-reload. The enum widens the
  channel that already existed rather than adding a parallel one.
- `MagazineSize` / `StartingReserveAmmo` / `MaxReserveAmmo` /
  `bInfiniteReserve` / `DryFireSound` on `WeaponBase`, initialised in
  `BeginPlay` (not the constructor — per-Blueprint defaults aren't applied
  yet at construction).
- **Subtle bit:** the dry-fire path resets `TimeSinceLastShot`. Without
  it `CanFire()` stays true every frame and a held trigger machine-guns
  the click.
- Ammo gate lives in `Fire()`, so future AI inherits it; `bInfiniteReserve`
  is the opt-out.
- On-screen `Ammo: <mag> / <reserve>` debug readout added under the bloom
  line. **Confirmed working in PIE — fire stops when out of ammo.**

**Bridge workflow lessons (important, cost real time):**
- **A CDO read-back is not proof.** `AnimType` was set on the weapon CDOs
  and verified as `Rifle`, but only `BP_FirstPersonCharacter` was
  compiled — so spawned instances kept the C++ default (`Pistol`) and the
  ABP faithfully reported Pistol. **Rule: set → compile *that* Blueprint →
  save → verify against a live PIE instance, not the CDO.**
- `reset_properties` can return `true` without actually clearing the
  value; setting `"None"` explicitly worked where reset didn't.
- Verified `GripLocationOffset` *does* apply correctly (live instance
  matched `(0, -10, -2)`); it reads as "not changing" because the values
  are small, further reduced by `FirstPersonScale 0.6`, and because the
  offset is in **socket space** — X/Y/Z don't map to forward/right/up.
- Montage assets can be duplicated and repointed via the bridge, but
  `SequenceLength` is read-only and `CompositeSections` unreadable, so a
  duplicated montage ends up internally inconsistent. `AM_Rifle_Fire` was
  created this way and accepted as-is.

**Open / carried forward:**
- `TryGetPawnOwner` returns None every frame and floods the log. Fires
  even with PIE stopped, so it's an editor-side preview instance — almost
  certainly the ABP editor window being open. Harmless but buries real
  errors.
- Muzzle flash "faces north" — retest after the FP-tagging fix above.
- The TEMP 5s re-snap timer still needs deleting (measured as doing
  nothing).
- `GripLocationOffset` tuning — the rifle still renders far too close.
- Battle rifle mesh may be `Darkness_AssaultRifle` rather than the
  intended sniper mesh.
- Ammo Phase B (reload), C (HUD), D (pickups). Per-weapon magazine sizes
  not yet set — all three currently use the `12/60/120` C++ default.
  Rough proposal: pistol `12/60/120`, close-range rifle `32/160/320`,
  battle rifle `18/72/144`.

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
