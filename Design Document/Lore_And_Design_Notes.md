# PROJECT BOPIS — DESIGN & LORE NOTES

> Source: compiled by the user's design partner (ChatGPT), imported verbatim
> from `Project_Bopis_Design_and_Lore_Notes.txt` on 2026-08-09. This is the
> canonical design/lore reference. **Design and lore ownership sits with the
> user + ChatGPT** — Claude's role here is implementation, not authorship.
> Do not edit the canon sections below without the user importing an updated
> source doc; see `GameDesignDocument.md` for the implementation-facing
> translation of this material.

STATUS KEY
- CANON / LOCKED: Explicitly established in discussion.
- DIRECTION / TBD: Current preference or idea, but details are not final.

## 1. Core Identity
[CANON / LOCKED] Sci-fi cyberpunk FPS. Primary rule: RULE OF COOL > GENRE PURITY — cyberpunk conventions are a toolbox, not a constraint; anything consistent with Bopis and cool is fair game.

Primary gameplay inspiration: **Bungie-era Halo only** (CE, 2, 3, ODST, Reach). Later non-Bungie Halo titles are not a primary reference unless a specific feature is deliberately selected.

## 2. FPS Combat Philosophy
[CANON / LOCKED]
- Combat is fast-paced, NOT reliant on aiming down sights.
- **Hip-fire**: fully combat-effective, no arbitrary hip-fire accuracy penalty. Player fights normally while moving/strafing/switching targets/meleeing. A weapon's inherent accuracy does not improve just from aiming/zooming.
- **Aim**: available but does not mechanically improve accuracy — it's targeting-info / precision-placement only. Normal crosshair may have no center dot; aiming may add a center dot. Aim can change the reticle without changing actual weapon accuracy.
- **Zoom**: distinct from aim. Restricted to appropriate weapons (not every weapon magnifies). Improves visibility/target acquisition, not accuracy. Precision weapons can have magnification; others may only get an aim reticle.
- **Recoil/Bloom**: Halo: Reach-style bloom is the primary accuracy/recoil mechanic. Firing expands the reticle/firing cone; bloom recovers when firing stops or is paced. Sustained auto fire builds bloom. Semi-auto/precision weapons can punish firing faster than intended cadence. Reticle expansion communicates current bloom. Traditional camera-climb recoil is not the core skill test (visual kick/feedback can still exist). Aim/zoom does not remove bloom or grant accuracy bonus.
- Core skill: trigger discipline — firing as fast as possible while maintaining bloom suitable for engagement distance.

## 3. Campaign Structure
[CANON / LOCKED] Linear FPS campaign, minimum 10 levels, built around a repeatable/escalating "30 seconds of fun" loop: 30s of fun → combat encounter → encounter sequence → level → campaign. Core guaranteed gameplay is on-foot FPS combat.

[UNDECIDED] Vehicles are not guaranteed — don't design around them unless later added and proven fun.

## 4. Linear Levels, Mini-Sandbox Arenas
[CANON / LOCKED] Navigation is linear; arenas are mini-sandboxes. This does **not** mean branching routes (no separate sniper/shotgun/stealth paths) — everyone fights through the same map/path. Freedom comes from how the player uses the geometry within the arena (e.g. a BR-style weapon exploits a long central hallway; a shotgun exploits adjacent short-sightline hallways/corners — same space, different tactics).

Core rule: **linear navigation, nonlinear combat.** Arenas should support varied engagement distances/positioning via sightlines, corners, open/confined areas, cover, elevation, movement space, enemy positioning. A good arena stays fun with a different loadout.

## 5. Weapons Dictate Playstyle
[CANON / LOCKED] Weapons encourage playstyle; levels should not hard-force a weapon type. Philosophy mirrors Bungie-era Halo on standard difficulty: a liked general-purpose weapon (e.g. BR-equivalent) should be usable through much of the game if ammo is maintained. Ammo availability is a *soft* pressure on loadout, not a hard requirement. Avoid "this enemy/room requires this exact weapon" — aim for "this weapon gives another good way to solve it." Higher difficulty demands better positioning/target prioritization/bloom management/ammo management/weapon knowledge/arena use, not a single correct solution.

## 6. Protagonist & Narrative Viewpoint
[CANON / LOCKED] Protagonist has no strongly authored personality — protagonist IS the player. May have functional identity (why present, capabilities, role, equipment, possibly name/designation/background) but the game never states what the protagonist thinks/believes. **No dialogue choices.** Narrative viewpoints are projected through supporting characters, who can hold strong opinions, disagree, argue politics/corporations/AI/society, lie, misunderstand, be biased, be sincere-but-wrong. Protagonist doesn't declare a correct viewpoint; the player decides.

## 7. Setting
[CANON / LOCKED] Location: **The Philippines**. Year: **2098**. Must remain recognizably descended from the Philippines, not a generic cyberpunk city with Filipino signage — modern/historical Filipino culture, languages, institutions, architecture, communities, religion, urban patterns, social structures visibly survive, transformed by tech and economic development.

## 8. Global AI Background
[CANON / DIRECTION] Mid-to-late 21st century AI causes major political/economic/environmental problems (automation unemployment, data-center water/energy use, exploitative rare-earth mining, corporate data exploitation, AI arms races, autonomous weapons, great-power fear of rivals' AI advantage). International response is NOT a total ban — most of the world imposes **stopgaps/restrictions on frontier AI research**, while **commercial consumption of AI-derived products remains legal, profitable, encouraged** (hypercapitalist contradiction). Possible restriction types: compute thresholds, self-improving-system limits, synthetic-cognition limits, autonomous-weapons-research limits, licensing/inspection of large compute facilities, restrictions on specific AI classes — but certified commercial products can still be sold. **Research restricted, consumption encouraged.** A corporation may be barred from frontier research at home but can still import/sell a finished, certified product developed elsewhere.

## 9. The Philippine AI Loophole
[CANON / DIRECTION] The Philippine government spots the economic opportunity and creates a regulatory haven — international AI-development stopgaps don't meaningfully apply inside Philippine territory / designated zones (possible structure: "Special Autonomous Technology Economic Zones" or equivalent; exact legal mechanism TBD). Result: foreign corporations can legally do frontier AI research in the Philippines that's restricted elsewhere. Government accepts massive foreign investment, infrastructure, tech transfer, and political money/corruption. Not purely negative — decades of real economic growth, infrastructure modernization, tech-sector employment, engineers staying/moving in, domestic manufacturing/robotics/defense industry growth, globally important Filipino universities, powerful domestic tech companies, transformation into a major tech power. Legitimate Philippine counter-argument: wealthy nations benefited from AI then tried to pull up the ladder — why should the Philippines accept that? By 2098 the AI economy is too important to the world to simply shut down.

## 10. International Investment — US & China
[CANON / DIRECTION] Both American and Chinese investment shape the rise.
- **US**: early advantage from colonial history, cultural/military/economic ties, English proficiency, BPO/service legacy — expands into AI research, robotics, synthetic cognition, advanced campuses.
- **China**: geographic proximity, regional manufacturing/electronics/batteries/robotics/logistics/supply-chain ties.
The Philippines doesn't pick a side — plays competition between US, China, Japan, Korea, Europe, others ("why choose?"), turning regulatory arbitrage into national strategy. US/China rivalry also discourages either from shutting the system down (neither wants the other to dominate AI). Filipino companies eventually become major players themselves. By 2098 the tech doesn't read as simply "American" or "Chinese" — decades of import/localization/reverse-engineering/espionage/Filipino engineering/cross-company theft produce a distinct Philippine tech ecosystem.

## 11. Corporate Espionage
[CANON / LOCKED] Widespread, because many competing international AI/robotics research operations sit physically close together in the Philippines. Includes engineer poaching, prototype theft, industrial sabotage, mysterious facility fires, network attacks, neural/model-data theft, air-gapped-facility infiltration, bribery, stolen patents, reverse engineering, corporate security ops. Companies maintain powerful private security given the IP value. Espionage causes technological cross-pollination (Company A's locomotion + Company B's stolen cognition + Company C's theft of that + Filipino reverse-engineering of the combo) — eventually it's unclear who invented what. Explains why 2098 synthetic systems are extremely sophisticated and why no single corporation fully understands/controls the ecosystem.

## 12. Synthetics / Enemies
[CANON / LOCKED] Main combat enemies must be **non-human**. Leading direction: **synthetic AI** — "AI" is the intelligence, "synthetics" is the physical enemy force; the player fights machines/synthetic bodies controlled or inhabited by AI. Humans can still be corrupt/antagonistic/causal/manipulative/politically conflicting/responsible for dangerous tech, but primary FPS battlefield enemies are non-human. Synthetics don't need to all be humanoid — possible chassis: humanoid infantry, quadrupeds, hovering units, repurposed industrial machines, swarms, heavily armored elites, enormous combat platforms. Design should emphasize Halo-like combat readability: distinct silhouettes, behaviors, ranks, battlefield roles for fast situational reading.

[UNDECIDED] Why synthetics turn hostile is not established — avoid the default "AI becomes self-aware, decides humanity must die"; the cause should be specific to Bopis/2098 Philippines history.

## 13. Luzon — "The Factory"
[CANON / LOCKED] By 2098 Luzon is a vast continuous cyberpunk sprawl (Metro Manila / Central Luzon / CALABARZON / surrounding centers blurred together via expressways, rail, industrial corridors, logistics networks, corporate zones) — "the Sprawl" is much bigger than Manila. Flatlands are extensively converted to solar farms feeding AI compute, data centers, automated factories, synthetic production, industrial/urban/logistics systems. Between solar fields: data centers, automated factories, synthetic assembly plants, warehouses, worker cities, cooling infrastructure, corporate research campuses, logistics hubs. Old Philippine towns/communities survive embedded within — visual contrast encouraged (centuries-old church, ordinary neighborhood, sari-sari-style commerce, barangay basketball court beneath/alongside enormous futuristic industrial infrastructure).

## 14. High City / Low City
[CANON / LOCKED] Strong High City / Low City concept — not one Midgar-style plate, but the accumulated result of decades of building over existing infrastructure (new roads over old roads, rail over roads, corporate districts spanning older districts, artificial decks connecting towers). Many physical elevation layers can exist.

**High City** — visual inspiration: *Ghost in the Shell* anime/TV. Clean, orderly, modern, maintained, integrated, spacious, sunlit, landscaped, tech-sophisticated (clean concrete, glass, white/composite materials, modern towers, elevated highways, automated transit, restrained high-tech info systems, greenery, public spaces, corporate campuses, newer infrastructure). The future visibly works here; darkness is beneath the surface (corporate surveillance, sensors, private security, synthetic labor, biometric access, political influence, corporate ownership/control).

**Low City** — visual inspiration: *Cyberpunk 2077* Night City slums. Heavily the original ground-level Philippines buried beneath newer development. Dense, old concrete, repeated modifications, exposed cables, AC units, improvised connections, cheap holographic/neon ads, wet streets, graffiti, food stalls, repair shops, bars, synthetic chop shops, warehouses, packed apartments, old roads turned tunnel-like by structures above. Large portions get little/no direct sunlight (High City occupies the sky) — gives the neon look an environmental reason; some areas feel like evening even in daytime.

Low City is **not** universally poor — poor communities, established middle class, commercial districts, old wealthy enclaves, industrial businesses, communities that refused to leave; some genuinely prefer it. High City: planned/clean/corporate. Low City: chaotic/crowded/culturally alive. Both must stay recognizably Filipino, not copies of Tokyo or Night City.

## 15. Visayas
[CANON / LOCKED] By 2098 the entire Visayas region is effectively transformed into a vast resort/tourism region. Concept: **Luzon = Production/Factory, Visayas = Leisure/Resort.** Bigger than modern tourism — possible elements: tropical luxury destinations, nightlife, casinos, artificial reefs, extreme sports, luxury medical tourism, corporate retreats, synthetic entertainment, floating hotels, private/artificial islands, underwater hotels, huge entertainment districts, advanced resort infrastructure. Millions of Filipinos still live there (not emptied), but economy/infrastructure/land-use is heavily redesigned around tourism/visitors/wealthy residents/international consumption. Possible contrast: immaculate resort districts supported by worker communities/service infrastructure kept away from tourist-facing areas.

## 16. Mindanao
[CANON] TBD. Do not force an identity onto Mindanao just to complete a Luzon/Visayas/Mindanao trio — its role should emerge later from setting and story.

## 17. Overall Thematic / World Principles
2098 Philippines should not just be "modern Philippines + neon" — should feel transformed by decades of frontier AI research, foreign investment, hypercapitalism, corruption, genuine economic growth, robotics, industrialization, corporate competition, geopolitical rivalry, technological cross-pollination. World should contain contradictions (governments condemning frontier AI while importing its products; foreign critics economically dependent on Philippine tech; corrupt governments taking corporate money while the resulting boom genuinely improves the country; US/China exploited by PH politicians who are in turn exploited by them; High City offering a great standard of living while embodying surveillance/corporate power; Low City containing poverty/neglect while culturally vibrant and desirable to some).

Lore should provide context for the FPS, not overwhelm it. Player should grasp the immediate premise simply: "Hostile synthetics. Here's a gun." Deeper history/politics/competing interpretations come through supporting characters, environments, background details, optional lore, corporate/government messaging, visual storytelling. **The FPS comes first.**

## 18. Current Major Undecided Questions
- What specifically causes the synthetic/AI conflict in 2098?
- What is the protagonist's functional role/background/designation?
- What is Mindanao like in 2098?
- What are the major corporations/families/factions?
- What exact international AI accord/regulatory regime exists?
- What legal loophole/exemption did the Philippines use?
- How is the Philippine government structured in 2098?
- How independent/powerful are corporations relative to the state?
- What specific synthetic enemy hierarchy exists?
- What are the player's weapons?
- Is there a two-weapon carry limit?
- Are vehicles included at all?
- What is the inciting incident?
- Where does Level 1 begin?
- What is the minimum 10-level campaign sequence?
- How much of the campaign takes place in Luzon versus elsewhere?
- Does the AI crisis remain Philippine/local, or become global?
