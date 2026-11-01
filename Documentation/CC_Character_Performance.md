# CC character performance review (2026-11-01)

A bridge-free review of the Character Creator (CC2 / CCMH) characters for the
Steam Deck (1280×800, 60 fps, GPU-bound, with game-thread-bound fights) and
the GTX 1650 (1080p High). Sources:

- `.uasset` name tables and tagged properties, read with a small parser;
- the code in `Source/ProjectBopis/`;
- the Deck trace 6 exports (`20261101`, `Lvl_Sandbox`, 6,604 frames, about
  7.3 characters alive on average). These are the newest per-timer exports
  still on disk; trace 8's are gone.

Fixes already in before this review: the glass master's refraction is off,
the player's sunglasses are opaque, and the impact VFX were trimmed.
Spec context: *NPC characters (CC2)* and *CC clothing LOD fix* in
`TechnicalDesignSpec.md`.

---

## What a character is made of

| Part | Component | Sections / materials | LODs (screen size) | Notes |
|---|---|---|---|---|
| Body `CCMH_Body_Male/Female` | `CharacterMesh0` (ABP_Player) | 1, `M_Skin_CCMH` (Subsurface Profile, WPO) | 3 (1.0 / 0.4 / 0.15) | 7.3k / 5.4k / 3.1k verts. Fully drawn under the clothes. |
| Head `CCMH_Head_*` | `CC_SkelMesh`, own AnimBP (CopyPoseFromMesh + 2 PoseBlend) | **6**: skin (SSS), eyes (`MSM_Eye`), teeth (SSS), eyelashes (**translucent, lit**), eye water (**translucent, lit**), eye AO (translucent, unlit) | 5 (1.0 / 0.4 / 0.15 / 0.05 / 0.025) | 4.9k verts LOD0. 12 head-shape morphs (all races). |
| Apparel (top, bottom, shoes, hat, glasses) | `CC_SkelMesh`, leader-posed to the body | 1 each; layered tops 2–3 (jacket + inner tee, + tie) | 3–6 (they follow the body's LOD) | 2.5–5.3k verts each at LOD0. |
| Hair, beard | `CC_SkelMesh`, leader-posed | 1–2 (`M_Hair_CCMH`: **masked, two-sided, `MSM_Hair`**; caps `M_Haircap` likewise) | 4–5 | Beards are 8.5–9.2 MB assets (Beard_04: 3 MB), against 1.5–2.4 MB for haircuts. They're probably the densest part. |
| Empty slots | `CC_SkelMesh` with no mesh | – | – | Probably about 15 per character (see finding 2). |

**Draw calls:** about 12–18 sections per dressed character. Each one draws in
the depth prepass, the base pass, velocity, and 2 sun cascades, so that's
about 60–90 draws per character. Three of them are translucent and on every
head.

**Measured per frame** (trace 6, average over the run, ≈7.3 characters):

| Where | What | ms/frame |
|---|---|---|
| GPU | `SubsurfaceScattering` (skin + teeth, screen-space Burley) | **0.36** avg, 6.6 max; runs on 98% of frames |
| GPU | GPU skin cache (`UpdateSkinningBatches` + 62 dispatches/frame) | ~0.14–0.25 |
| GPU | Morph targets | ≈0 (282 updates in the whole run) |
| GPU | Virtual-texture update (all VT, not only CC) | 0.12 |
| GPU | `TranslucencyLightingVolume` (shared with the impact particles) | 0.98, every frame |
| GT | `CC_SkelMesh_C` ticks: **169 per frame** (≈23 per character), median 0 µs | 0.78 incl |
| GT | `USkinnedMeshComponent` ticks (165/frame) | 0.59 excl |
| GT | Body (`CharacterMesh0`: tick, anim, bones) | 1.71 incl |
| GT | Waiting on parallel anim evaluation (40/frame) | 0.94 |
| GT | Head AnimBP (`CCMH_Head_AnimBP`, **multithreaded update off**) | 0.16 |
| GT, spawn | `Set Hair` ≈1 ms × ~4.6, `Set Apparel` ≈0.9 ms × ~3.2 per build | per build, not per frame |

Trace 8's notes agree: fights average 167 skinned-mesh ticks and 47 anim
evaluations per frame, and `UWorld_Tick` is ~15 ms of a 20 ms frame in the
slowest seconds. Characters cost GPU skin cache 0.3 ms and base pass +0.2 ms
in busy frames.

---

## Findings, cheapest high-impact first

### 1. Enemy bodies animate at full rate at every distance, even off screen *(code, 1 line; game thread)*
- **What:** `AEnemyBase` never sets anything. The body keeps `ACharacter`'s
  defaults: `VisibilityBasedAnimTickOption` = AlwaysTickPoseAndRefreshBones
  and Update Rate Optimizations (URO) **off**.
  `BP_PlayerCharacter` sets the same tick option explicitly.
- **Cost:** the ABP_Player evaluation and bone refresh for every enemy, every
  frame (body 1.71 ms incl + 0.94 ms waiting on anim, at ~7 characters). The
  game thread is the fight bottleneck.
- **Fix:** turn on URO for enemies only, and keep the player at full rate.
  With URO a far or off-screen enemy updates every 2–4 frames and is
  interpolated in between, so bones (and the physics bodies bullets hit)
  still move every frame. The tick option stays Always, so an enemy behind
  the camera still refreshes its `head` socket for line-of-sight.
  - **Estimate:** −30–50% of enemy anim time in a typical fight (several
    enemies beyond ~10 m or off screen): roughly −0.5 to −1 ms game thread.
  - **Test:** watch for visible stepping on mid-distance enemies, and check
    that ragdolls and hit reactions still look right. If it steps, raise the
    thresholds (`AnimUpdateRateParams`) before dropping URO.
- **Related, content only:** CC ships a **`QualityLevel`** component (already
  on every CC character, `CharacterCustomizer_Core/Crowd/QualityLevel`). Its
  `Set Quality Level` event (levels 0–5) sets, on every skeletal mesh of the
  character, URO, `VisibilityBasedAnimTickOption`, Cast Shadow, collision,
  tick interval and the skip-bounds/kinematic flags, plus the actor's tick
  interval. Nothing in our game calls it with a distance. Read its switch in
  the editor before using it: it may also turn off collision, which hit
  detection needs.

### 2. Every CC slot is a ticking skeletal mesh component, filled or not *(code, small; game thread)*
- **What:** CC's tables have 21 apparel slots (Tops, Pants, Footwear,
  Headwear, Glasses, Jewelry, Ring, Hands, Backpack, Swimwear, Uniform…) and
  5 hair slots (Hair, Eyebrows, Eyelashes, Beard, Mustache). The trace counts
  **169 `CC_SkelMesh_C` ticks per frame at ~7.3 characters, about 23 each**,
  with a median of 0 µs. That fits a component created per slot, with only 5–8
  holding a mesh.
- **Not yet confirmed:** it's inferred from the trace. To confirm, select a
  running enemy in PIE and count its `CC_SkelMesh` components.
- **Cost:** each empty one is a tick function the task graph schedules every
  frame. About 0.1–0.3 ms of game thread at 7 characters, scaling with the
  count. Sleepers are already excluded.
- **Fix:** turn off tick on parts that have no mesh, once the character is
  built (CC creates them in the construction script, so they exist by
  `BeginPlay`). `Sleep()` only records components that are ticking, so they
  stay off after `Wake()`.
  - Don't turn off tick on parts that *have* a mesh. Followers keep their
    LOD in step with the body from their own tick. A stuck follower LOD is
    the bone mismatch from the *CC clothing LOD fix* (the "busted" clothes).
- **C++ to type** (`BopisCharacterBase.h` / `.cpp`):

```cpp
// BopisCharacterBase.h, private:
	/** CC makes a mesh component per apparel/hair slot; the empty ones still tick. */
	void StopEmptyPartTicks();
```

```cpp
// BopisCharacterBase.cpp, at the end of BeginPlay():
	StopEmptyPartTicks();

// new function:
void ABopisCharacterBase::StopEmptyPartTicks()
{
	TArray<USkeletalMeshComponent*> Parts;
	GetComponents(Parts);
	for (USkeletalMeshComponent* Part : Parts)
	{
		if (Part != GetMesh() && !Part->GetSkeletalMeshAsset())
		{
			Part->SetComponentTickEnabled(false);
		}
	}
}
```

  **Caveat:** if anything re-dresses a character at runtime (CC's
  `Set Apparel` into an empty slot), that part would stay without a tick.
  Today the look is only built at construction.

### 3. The head runs its own AnimBP on the game thread *(content, one checkbox; game thread)*
- **What:** `CCMH_Head_AnimBP` = CopyPoseFromMesh + two PoseBlend nodes (the
  ARKit and viseme pose assets), with `bUseMultiThreadedAnimationUpdate` =
  **false**. Its update runs on the game thread: 0.16 ms excl, 59k calls in
  the run. Nothing in the game drives face curves (no lip sync or ARKit).
- **Fix, step 1 (content):** in the head AnimBP, *Class Settings → Use
  Multi Threaded Animation Update* on (its event graph is empty, so it's
  safe). Set *LOD Threshold* 1 on both PoseBlend nodes, so faces past LOD0
  skip them.
  - **Estimate:** −0.1–0.15 ms game thread.
- **Step 2, later and bigger:** if faces never animate, the head could be a
  leader-pose follower of the body (no anim instance at all, like the
  clothes). Missing face bones would sit at the reference pose.
  - **Trade-offs:** morph targets set on a follower are reset by the leader
    each update, so the head-shape morphs would need another route (bake
    per-variant heads, or drive them as anim curves on the body).
  - It would also make the `TG_PostPhysics` head fix unnecessary.
  - Test before committing to it.

### 4. Subsurface scattering runs every frame *(config; GPU)*
- **What:** body, face and teeth use `MSM_SubsurfaceProfile` (`Skin_SS`),
  which needs the screen-space Burley pass whenever any skin is on screen.
  The player's skin always is.
- **Cost:** 0.36 ms average, up to 6.6 ms in close-ups (trace 6).
- **Fix:** A/B in `-ExecCmds` on the Deck first, then put the winner in
  `[EffectsQuality@2]` of `DefaultScalability.ini`:
  - `r.SSS.HalfRes 1`, then `r.SSS.Quality 0` (the cheapest real SSS);
  - `r.SubsurfaceScattering 0` as the floor. Skin then shades without the
    blur, which may suit the 360-era look.
  - **Estimate:** −0.15–0.25 ms average, and most of the close-up spikes.

### 5. Three translucent sections on every head *(content; GPU)*
- **What:**
  - eyelashes `MI_Eyelashes_LP` → `M_Simple_Translucent`: translucent,
    two-sided, lit with the default `TLM_VolumetricNonDirectional`;
  - eye water `MI_Eye_Water_Master`: translucent, lit, volumetric;
  - eye AO `M_Crowd_EyeOcclusion`: translucent, unlit.
- **Cost:** 3 sorted translucent draws per visible head. 7 characters on
  screen means 21. They're small on screen but tie the CC heads to the
  translucency lighting volume. The TLV runs every frame (0.98 ms in trace
  6), and it can only be switched off (`r.TranslucentLightingVolume 0`) once
  nothing on screen uses volumetric lit translucency. The impact particles
  are the other users.
- **Fix:**
  - In the head mesh's LOD settings, untick (disable) the eye water and eye
    AO sections at **LOD1 and up** (characters beyond about 4 m), and the
    eyelashes at **LOD2 and up**. At 800p they're a few pixels.
  - For LOD0, give the eyelashes a masked (dithered) or unlit MI instead of
    lit translucent.
  - Both are mesh/material settings.
  - **Estimate:** small alone, under 0.1 ms. It's a prerequisite for the TLV
    saving (~1 ms) if the impact materials ever go unlit or surface-lit.

### 6. LOD transitions *(config test; GPU, vertex and skin-cache load)*
- **What:** the body switches at 1.0 / 0.4 / 0.15. With this camera
  (90°, 16:10) that's LOD0 inside ≈4 m and LOD1 to ≈10.7 m. The head has its
  own 5 LODs, the clothes follow the body. Since the body was cut to 3 LODs,
  every clothing piece has at least as many LODs as the body, except the 4
  listed in the spec (keep them out of outfits).
- **Fix to test:** `r.SkeletalMeshLODBias 1` on the Deck only (an
  `-ExecCmds` A/B, then a Deck-specific ini).
  - A bias is now safe for the clothes, because LODs are clamped to the
    body's last LOD (2).
  - It drops LOD0 everywhere, the player included: check the player's
    close-up silhouette.
  - **Estimate:** about −25% skinned vertices per character (body 7.3k →
    5.4k). Skin cache, prepass, base pass, velocity and shadow vertex work
    scale with it. Roughly −0.1–0.2 ms in fights.

### 7. Shadow casting on parts that can't be seen in a shadow *(content; GPU)*
- **What:** every CC part casts sun shadows in both cascades. The class
  default no longer has *Self Shadow Only*, which is correct.
- **Fix:**
  - In the head mesh, untick **Cast Shadow** per section for eyes, teeth
    and eyelashes (the translucent eye water and AO don't cast anyway).
  - In the apparel rows, glasses, jewelry, rings and watches don't need to
    cast.
  - **Estimate:** a few draws per character per cascade: under 0.1 ms.

### 8. Glass master still uses the costliest translucent lighting *(content; GPU, future)*
- **What:** `M_Base_Material_Glass_Reflective` (refraction now off) is still
  `TLM_Surface` with **translucent SSR** on.
- **Who still uses it:** female `Glasses_Cat_Eyes` (in
  `DT_Outfits_PH_F`), the female glasses, scuba goggles and the female
  wristwatch.
- **Who doesn't:** the male enemy glasses (`MI_Glasses` / `MI_Simple_Masked`)
  and `Glasses_Agent` (`MI_Opaque_Glass`).
- **Fix, when female civilians arrive:** point those rows at CC's own
  `MI_Opaque_Glass`, as was done for the player's sunglasses. Or set the master
  to `TLM_SurfacePerPixelLighting` with SSR off.

### Measured vertex counts (bridge, 2026-11-01)
`SkeletalMeshTools.get_vertex_count` / `get_section_count`, LOD0 → last:
- **Body:** 7.3k / 5.4k / 3.1k.
- **Head:** 4.9k / 3.5k / 1.8k / 0.6k / 0.3k.
  - Sections: male 6/6/5/4/3, female 6/6/6/5/4. CC already drops some head
    sections at LOD2+.
- **Beards 01–03:** 5.2–5.3k at LOD0, but **5.0k at LOD1** (barely reduced),
  1.0–1.5k at LOD2. Beard_04 is 1.7k / 1.6k.
- **Haircuts:** 3.1–4.6k. The afros are 14–24k, but the PH presets already
  exclude them.
- **Male outfit pieces** (`DT_Outfits_PH_M`):
  - tops 1.3k (jersey) to 5.8k (waistcoat with tie), with 2–3 sections when
    layered;
  - pants 1.6–6.3k (police pants, 2 sections);
  - shoes 1.5–5.3k;
  - hats 0.7–2.8k;
  - glasses 2.9k (2 sections).
- **A dressed enemy at LOD0 ≈ 20–30k vertices; at LOD1 ≈ 14–20k** (what
  `r.SkeletalMeshLODBias 1` gives up close).

### 9. Beards and hair cards *(content; GPU)*
*(Updated after the counts above. Beards aren't the densest part, but
Beard_01–03 gain almost nothing at LOD1. Fix: LOD1 reduction to about 50% in
the mesh editor, or prefer Beard_04.)*
- **What:** all hair is masked, two-sided `MSM_Hair`. Masked geometry can't
  use early-Z and pays the clip in the prepass and both shadow cascades.
  Beards are 4–5× the asset size of a haircut.
- **Odds:** `BeardChance` is 0.3 for enemies, 0.5 for the placeholder player.
- **Fix:**
  - Get LOD0/LOD1 vertex counts first (see the bridge request below).
  - If a beard is over ~10k verts, prefer `Beard_04` (3 MB, 5 LODs) in the
    role lists, or lower `BeardChance`.
  - Make sure the hair LOD1+ sections are actually reduced.

### 10. Textures: 4K, virtual-texture streamed, not in character groups *(content; memory and disk)*
- **What:** 22 textures at 4K:
  - skin diffuse (5 head + 5 body tones);
  - normal maps head + body;
  - `T_RAOSSS` head + body;
  - 8 eyebrow sheets at 4096×1024.
- **Settings:**
  - skin and eyebrows are **VT-streamed** (`r.VirtualTextures` is on);
  - their groups are World / WorldNormalMap, so a Character group cap in a
    device profile wouldn't reach them;
  - 345 more at 2K, mostly apparel.
- **Unused tones:** the PH presets only use skin tones 02 and 03.
- **GPU cost:** small at 800p, because mips stream (VT update 0.12 ms for
  the whole scene).
- **Fix:**
  - *Maximum Texture Size* 2048 on the 4K skin, normal and RAOSSS textures
    (bulk edit). That's about 4× less memory and disk per texture, with no
    visible change at 800p or 1080p for characters that never fill the
    screen.
  - Optionally move them to `TEXTUREGROUP_Character` /
    `CharacterNormalMap` so device profiles can cap them.

### 11. Bigger structural options (only if 1–3 don't free enough game thread)
- **Merge each character's body and clothes into one skeletal mesh** at
  build time (`USkeletalMergingLibrary::MergeMeshes`, SkeletalMerging plugin).
  - **Gains:** 5–8 fewer components and skin-cache dispatches per
    character, and no follower LOD rule.
  - **Draw calls:** unchanged, since materials stay separate sections.
  - **Costs:** a merge at build (fine while reserves are built asleep);
    memory per unique merged mesh; a re-check of CC's per-material masks,
    DMIs and the clothing-layer WPO.
- **Body skin under clothing** is skinned, shaded and shadowed in full.
  Cutting it means per-outfit body variants or section masks, which is a
  CC-level change. Not worth it before the above.

---

## Not measured, and what would measure it

- **Per-part vertex counts** for the clothes, hair and beards at each LOD.
  The `.uasset` doesn't expose them without the bridge.
  `SkeletalMeshTools.get_vertex_count` / `get_lod_count` can.
- **Components per character:** inferred as ≈23 from the trace. Confirm in
  PIE by selecting an enemy and counting.
- **Head section setup per LOD:** which sections exist or are disabled at
  LOD1–4, and the per-section cast-shadow and runtime recompute-tangents
  flags. These are in binary render data. The editor's LOD section list
  shows them.
- **GPU cost per character pass:** the trace gives pass totals only (base
  pass, velocity, shadow depths, translucency). Per-character attribution
  needs a `ProfileGPU` capture with N vs N+4 enemies on screen.
- **The `QualityLevel` component's per-level values**: a Blueprint switch,
  not readable from the file. Open it in the editor.
- **The weapon meshes:** `AnimSingleNodeInstance` ×26 per frame, probably
  the skeletal weapon meshes. Not CC, so out of scope here; worth a look in
  the same pass as finding 1.

**One bridge batch would close the first and third items:**
`get_lod_count` + `get_vertex_count` for
- `Beard_01`…`04`;
- the hairstyles in the enemy role lists;
- the outfit pieces in `DT_Outfits_PH_M`;
- `CCMH_Head_Male`.

Plus, if the toolset exposes them, the head's per-LOD section list. Ask
before running it.

## Suggested order
1. Findings 3 and 4 (a checkbox and a cvar A/B), then 5–7 (mesh and
   material settings in the editor). All content or config. Re-trace.
2. Findings 1 and 2: present the C++ for the user to type, then build and
   re-trace a fight. Compare `UWorld_Tick` in the slowest 20% of seconds
   with trace 8.
3. Findings 9 and 10 once the bridge counts are in. Finding 8 when female
   civilians are added. Finding 11 only if the game thread is still over
   budget.
