# Pass `dressing_old`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# The first dressing pass (off since the blockouts rule; it still draws from rnd, so it runs).
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
_mark = len(items)
# --- Dressing -------------------------------------------------------------------------------------------------------------
DR = "BackAlleys/Dressing"
doors = 0
for label, kind, x, y, side, w in ground_pieces:   # awnings over shop fronts and every other door; tin patches
    (rx, ry), (nx, ny) = RUN[side], NORMAL[side]
    if kind == "shop":
        put(label + "_Awning", AS + "SM_Roof_A_002", x, y, 330.0, YAW[side], folder=DR, nocoll=True)
    elif kind == "door":
        doors += 1
        if doors % 2:
            put(label + "_Awning", AS + "SM_Roof_A_002", x, y, 270.0, YAW[side], (w / 300.0, 1, 1), folder=DR,
                nocoll=True)
    elif kind == "plain" and w >= 150 and rnd.random() < 0.15:
        s = rnd.uniform(20, w - 130)
        put(label + "_Tin", AS + rnd.choice(("SM_MetalPlate_A_001", "SM_MetalPlate_A_002")), x + rx * s + nx * 4,
            y + ry * s + ny * 4, 120.0, YAW[side], roll=rnd.uniform(-3, 3), folder=DR, nocoll=True)

# Wall grime (Favela: grime around openings at 0.9-2 m, dirt splash at the foot, streaks running down from the
# slab). Fewer than Favela's 0.6 per tile: each decal costs on the Deck, so doors and ground floors come first.
# A DecalActor's DecalSize is an extent (128, 256, 256): scale y is the height and z the width (roll 90), as Favela.
DC = "BackAlleys/Decals"
decals = []


def wall_decal(t, mat, along, h, sy, sz, depth=0.02):
    (nx, ny) = NORMAL[t["side"]]
    x, y = at(t["x"], t["y"], t["side"], along, 2)
    yaw = math.degrees(math.atan2(-ny, -nx))
    decals.append((t["label"] + "_Dcl%d" % len(decals), mat, x, y, t["z"] + h, yaw, (depth, sy, sz)))


order = sorted(wall_tiles, key=lambda t: (t["kind"] != "door", t["s"], rnd.random()))
for t in order:
    w = t["w"]
    if t["kind"] == "door" and rnd.random() < 0.8:
        wall_decal(t, rnd.choice(DECALS["grime"]), w / 2, rnd.uniform(120, 190), rnd.uniform(0.45, 0.65),
                   rnd.uniform(0.55, 0.75))
    if t["s"] == 0 and rnd.random() < 0.15:
        wall_decal(t, DECALS["dirt"][0], w / 2, 30, 0.2, w / 512.0, 0.03)
    if rnd.random() < 0.25:   # streaks running down from the band
        wall_decal(t, DECALS["dirt"][0], w / 2, 255, rnd.uniform(0.25, 0.4), w / 512.0 * 0.9, 0.03)
    if t["kind"] == "window" and rnd.random() < 0.5:   # streaks running down from the window sill
        wall_decal(t, DECALS["dirt"][0], 111 * t["w"] / TILE_W, 50, 0.2, 0.25, 0.03)
    if t["kind"] == "plain" and rnd.random() < 0.2:
        wall_decal(t, rnd.choice(DECALS["grime"] + DECALS["dirt"][1:]), rnd.uniform(60, w - 60),
                   rnd.choice((90, 200)), rnd.uniform(0.4, 0.6), rnd.uniform(0.45, 0.7))
# (placed after the dressing switch below, so they can be on while the rest of the dressing is off)

# Window-type air conditioners, now and then (user: "add ocasional air conditioners"): the AsiaSlum set as the pack's
# demo map mounts it, a bracket frame 10 cm off the wall face, the unit 10 cm further out and 10 cm lower, the fan
# grille 15 cm to the side. On plain tiles only, above head height on street floors.
acs = 0
for t in sorted((t for t in wall_tiles if t["kind"] == "plain" and t["w"] >= 150), key=lambda t: rnd.random()):
    if acs >= 12:
        break
    if rnd.random() > 0.5:
        continue
    acs += 1
    z = t["z"] + (230 if t["s"] == 0 else 150)
    along = t["w"] * rnd.uniform(0.35, 0.65)
    yaw = YAW[t["side"]]
    for part, ds, dn, dz in (("Frame", 0, 10, 0), ("Unit", 0, 20, -10), ("Fan", -15, 35, 37)):
        x, y = at(t["x"], t["y"], t["side"], along + ds, dn)
        put("AC_%d_%s" % (acs, part), AS + "SM_AirConditioner%s_A_001" % ("" if part == "Unit" else part),
            x, y, z + dz, yaw, folder=DR)

# TV antennas on wall brackets at parapet height, leaning (Favela: 2-4 per house, scale 0.42, roll -30).
ant = 0
for t in sorted((t for t in wall_tiles if t["top"] and t["s"] == 1), key=lambda t: rnd.random()):
    if ant >= 14:
        break
    ant += 1
    top = t["z"] + 400
    x, y = at(t["x"], t["y"], t["side"], t["w"] * rnd.uniform(0.3, 0.7), 0)
    yaw = YAW[t["side"]]
    put("Antenna_%d_Bracket" % ant, FV + "SM_AntennaSupportPart_02", x, y, top - 40, yaw, (0.42, 0.42, 0.42),
        folder=DR, nocoll=True)
    x, y = at(x, y, t["side"], 0, 30)
    put("Antenna_%d" % ant, FV + rnd.choice(("SM_Antenna_01", "SM_Antenna_02", "SM_Antenna_03")), x, y, top - 2,
        yaw - 40 + rnd.uniform(-15, 15), (0.42, 0.42, 0.42), folder=DR, roll=-30, nocoll=True)
for sp in spawns:   # two cables across each dead-end alley, and garbage by its side wall
    (cx, cy), (nx, ny), (rx, ry) = sp["door"], sp["n"], sp["run"]
    for k, dist in enumerate((200, 400)):
        put("Cable_%s_%d" % (sp["label"][-2:], k), AS + "SM_Cable_A_005", cx + nx * dist, cy + ny * dist, 660 + 70 * k,
            90 if rx == 0 else 0, (450 / 380.0, 1, 1), folder=DR, nocoll=True)
    gx, gy = cx + nx * 250 - rx * 170, cy + ny * 250 - ry * 170
    put("Garbage_%s_a" % sp["label"][-2:], ME + "MiddleEast/SM_Garbage_bag_01", gx, gy, 0, rnd.uniform(0, 360), folder=DR)
    put("Garbage_%s_b" % sp["label"][-2:], ME + "MiddleEast/SM_Garbage_bag_green_03", gx + nx * 60, gy + ny * 60, 0,
        rnd.uniform(0, 360), folder=DR)
    put("Garbage_%s_c" % sp["label"][-2:], PM + "CardboardSet_01/SM_CardboardBox_01", gx + nx * 120, gy + ny * 120, 0,
        rnd.uniform(0, 360), folder=DR)
CLOTHES = ["SM_clothes_A_02", "SM_clothes_A_03", "SM_clothes_A_04", "SM_clothes_A_05", "SM_clothes_B_01",
           "SM_clothes_B_02", "SM_clothes_B_03"]
lines = 0
for bid, side, a, c in upper_runs:   # laundry across alleys 3-6 m wide, from upper-floor faces
    if lines >= 7:
        break
    mx, my = (a[0] + c[0]) / 2, (a[1] + c[1]) / 2
    nlx, nly = LNORM[side]
    gap = next((g * 0.5 for g in range(1, 14) if solid(mx + nlx * g * 0.5, my + nly * g * 0.5, 1)), None)
    if not gap or not (3.0 <= gap <= 6.0) or rnd.random() < 0.35:
        continue
    lines += 1
    X, Y = ue(mx, my)
    nx, ny = NORMAL[side]
    yaw = 90 if side == "east" else 180
    put("Laundry_Line_%d" % lines, AS + "SM_Rope_A_001", X, Y, 520, yaw, (gap * 100 / 125.0, 1, 1), folder=DR, nocoll=True)
    for j in range(int((gap - 0.6) / 1.1) + 1):
        put("Laundry_%d_%d" % (lines, j), ME + "MiddleEast/" + rnd.choice(CLOTHES), X + nx * (70 + 110 * j),
            Y + ny * (70 + 110 * j), 515, yaw - 90, folder=DR, nocoll=True)
put("Wires_Web", ME + "MiddleEast/SM_Wires_01", -190, -1830, 50, 0, folder=DR, nocoll=True)
big = [b for b in BLOCKS.values() if b["storeys"] == 2 and (b["x1"] - b["x0"]) * (b["y1"] - b["y0"]) >= 30]
for k, b in enumerate(big[::2]):
    put("RoofTank_%d" % k, ME + "MiddleEast/SM_Water_Tank_0%d" % (k % 3 + 1),
        *ue((b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2), 800, rnd.uniform(0, 90), folder=DR)
for k, b in enumerate(big[1::3]):   # Favela's roof water drum on a stand
    X, Y = ue((b["x0"] + b["x1"]) / 2, (b["y0"] + b["y1"]) / 2)
    put("RoofDrum_%d_Stand" % k, FV + "SM_Stand_01", X, Y, 800, rnd.uniform(0, 90), folder=DR)
    put("RoofDrum_%d" % k, FV + "SM_Barrel_01", X, Y, 860, rnd.uniform(0, 360), folder=DR)
    put("RoofDrum_%d_Cap" % k, FV + "SM_Barrel_Cap_2", X, Y, 946, rnd.uniform(0, 360), folder=DR)
sx, _ = ue(0, 6)   # the sari-sari front on B2's south face, west part (x16.5-21)
put("SariSari_Sign", AS + "SM_Sign_A_001", sx - 10, ue(18, 0)[1], 300, 90, folder=DR, nocoll=True)
for k, (lx, z) in enumerate([(16.9, 0), (17.45, 0), (17.17, 33)]):
    put("SariSari_Crate_%d" % k, PM + "Plastic_Crate_Set_01/SM_Plastic_Crate_01", sx - 110, ue(lx, 0)[1], z, 0, folder=DR)
put("SariSari_Rice_0", PM + "RiceBags_01/SM_Rice_Bag_Full_01", sx - 110, ue(20.4, 0)[1], 0, 90, folder=DR)
put("SariSari_Chair", PM + "MonoBloc_Chairs_01/SM_Monobloc_Chair_01", sx - 170, ue(19.6, 0)[1], 0, 200, folder=DR)

if not DRESSING:
    del items[_mark:]
