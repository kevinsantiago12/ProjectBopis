# Pass `arena_gameplay`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Arena only: pickups, wander points, music, the player start and the volumes (plan3_gameplay.json).
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# --- Gameplay -------------------------------------------------------------------------------------------------------
pickups = []
P = {"rifle": ("BP_WeaponPickup", 60, "/Game/ThirdPerson/Blueprints/BP_AssaultRifle"),
     "rifle ammo": ("BP_AmmoPickup_Rifle", 20, None), "shotgun": ("BP_PumpShotgun_Pickup", 60, None),
     "2x grenade": ("BP_AmmoPickup_Grenade", 20, None), ".45 ammo": ("BP_AmmoPickup_45", 20, None)}
counts = {}
for p in L["pickups"]:
    asset, z, weapon = P[p["what"]]
    base = p.get("z", 0) * 100.0
    n = 2 if p["what"] == "2x grenade" else 1
    for k in range(n):
        counts[p["what"]] = counts.get(p["what"], 0) + 1
        x, y = ue(p["x"] + 0.6 * k, p["y"])
        label = "Pickup_" + p["what"].replace(" ", "").replace(".", "").replace("2x", "") + "_%d" % counts[p["what"]]
        pickups.append({"label": label, "asset": PK + asset, "loc": [x, y, base + z], "weapon": weapon})
if not PICKUPS:
    pickups = []
wander = [{"label": "Wander_" + w["id"], "loc": list(ue(w["x"], w["y"])) + [100.0]} for w in L["wander"]]
# The level's opening music (user, 2026-11-04: "a bgm manager on the backalley too"): an AMusicTrigger that fires as the level
# starts, set like Lvl_Linear's. It stands in BackAlleys/Gameplay, which a rebuild keeps. Where it stands doesn't matter.
music = {"label": "Music_Start", "track": "/Game/Audio/BGM/DarkCrimes",
         "loc": list(ue(L["player_start"]["x"], L["player_start"]["y"])) + [100.0]}
gameplay = {"player_start": list(ue(L["player_start"]["x"], L["player_start"]["y"])) + [100.0], "spawns": spawns,
            "pickups": pickups, "wander": wander, "music": music,
            "floor": {"loc": [0, 0, 0], "scale": [5.6, 6.4, 1.0]},
            "nav": {"loc": [0, 0, 400], "scale": [1.272, 1.494, 1.0]},
            "lmv": {"loc": [0, 0, 400], "scale": [26.0, 29.0, 7.0]}}

