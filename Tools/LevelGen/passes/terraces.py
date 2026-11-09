# Pass `terraces`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Covered roof terraces on the 1-storey houses and balcony strips: parapets, banisters, lean-tos, plank frames.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# --- Covered roof terraces on the 1-storey blocks ---------------------------------------------------------------------
# User 2026-11-03: "study the balcony with currogated roof pattern in favela map", then "Yes, build them" (on the five
# 1-storey blocks). The Favela version (Tools/LevelGen/LESSONS.md): the flat roof of a lower part, a low parapet on its
# open sides, the taller wall behind, and flat corrugated sheets about 2.75 m up resting on the walls - with a plank
# frame (two planks back to back) where no wall carries them. Our 1-storey blocks are 1.5 m deep, so: one row of
# SM_Slate_01 lengthwise (1.54 m wide, about the depth), 30 cm end laps, 2 cm height steps; parapets (SM_Wall_14 in
# concrete, 1.06 m) on the sides open at storey 1; plank posts every <= 1.9 m on open long sides plus a beam under the
# sheet edge. The tin roof sheets are replaced. Water drums are dressing (the blockouts-only rule) and left out.
TER = "BackAlleys/Terraces"
WOOD = FV + "SM_Wooden_part_05"         # 190 x 4 x 16 cm, pivot at one end (the mesh runs along its local -X)
SHEET_UNDER = 275.0                    # sheet underside above the terrace floor (Favela median 276)
PARAPET_H = 106.0


def plank_pair(label, x, y, z, yaw, length, vertical):
    """The Favela plank member: two SM_Wooden_part_05 back to back (scale y +1 / -1). Vertical: a post standing up
    from (x, y, z) (pitch -90 turns the mesh's -X run upward); else a beam running length cm along yaw from (x, y, z)
    (turned 180, since the mesh runs along -X)."""
    for k, sy in enumerate((1.0, -1.0)):
        put("%s_%d" % (label, k), WOOD, x, y, z, yaw if vertical else yaw + 180, (length / 190.0, sy, 1), folder=TER)
        if vertical:
            items[-1]["rot"][0] = -90.0


AWN_D = 2.4          # m the lean-to awning reaches out from the taller wall
AWN_PITCH = 9.0      # degrees it falls outward
AWN_HIGH = 290.0     # sheet underside at the wall, above the terrace floor (under the upper storey's band)


def lean_to(bid, b, floor):
    """The reference picture's roof: corrugated sheets hung off the taller wall (the strip's inner edge, opposite its
    balcony side), running down the slope, side by side along the wall with 9 cm laps, held at the outer edge by plank
    posts standing on the terrace floor and a plank beam."""
    back = OPP[b["balcony"]]                               # the strip's side against the taller part of the block
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    ox, oy = LNORM[b["balcony"]]                           # outward, in layout terms
    if back in ("north", "south"):
        wall_y = y0 if back == "north" else y1
        p0, p1 = (x0, wall_y), (x1, wall_y)
    else:
        wall_x = x0 if back == "west" else x1
        p0, p1 = (wall_x, y0), (wall_x, y1)
    rl = abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])
    ux, uy = (p1[0] - p0[0]) / rl, (p1[1] - p0[1]) / rl
    depth = min(AWN_D, (abs(x1 - x0) if back in ("west", "east") else abs(y1 - y0)) - 0.6)
    tanp = math.tan(math.radians(AWN_PITCH))
    z_high = floor + AWN_HIGH
    yaw = math.degrees(math.atan2(ox, -oy))                # layout x -> UE +Y, layout y -> UE -X
    p = math.radians(-AWN_PITCH)
    sx, sy = (depth * 100 + 10) / 382.0, 1.0
    cov = rl * 100 - 20                                    # sheets stop 10 cm short of each end
    n = max(1, math.ceil((cov - 9) / 145.0))
    step = (cov - 154) / (n - 1) if n > 1 else 0.0
    for i in range(n):
        t = 10 + 77 + step * i if n > 1 else rl * 50       # cm along the wall to the sheet's centre
        lx = p0[0] + ux * t / 100 + ox * (depth / 2 + 0.05)
        ly = p0[1] + uy * t / 100 + oy * (depth / 2 + 0.05)
        cx, cy = ue(lx, ly)
        cz = z_high - tanp * (depth * 100 / 2) + 2 * (i % 2)
        vx, vy, vz = -2 * sx, -35 * sy, 72.0               # the sheet's underside centre in its local frame
        rx_ = vx * math.cos(p) - vz * math.sin(p)
        rz_ = vx * math.sin(p) + vz * math.cos(p)
        cyaw, syaw = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        put("Awning_%s_%d" % (bid, i), FV + "SM_Slate_01", cx - (rx_ * cyaw - vy * syaw), cy - (rx_ * syaw + vy * cyaw),
            cz - rz_, yaw, (sx, sy, 1), folder=TER)
        items[-1]["rot"][0] = -AWN_PITCH
    # posts and beam 15 cm inside the awning's outer edge
    out = depth - 0.15
    under = z_high - tanp * out * 100                      # sheet underside above the post line
    nposts = max(2, math.ceil((rl - 0.7) / 2.0) + 1)
    for i in range(nposts):
        f = 0.35 + (rl - 0.7) * i / (nposts - 1)        # 35 cm in from the ends: clear of side parapets
        X, Y = ue(p0[0] + ux * f + ox * out, p0[1] + uy * f + oy * out)
        plank_pair("AwnPost_%s_%d" % (bid, i), X, Y, floor, YAW[b["balcony"]], under - floor - 16, True)
    pieces = max(1, math.ceil(rl / 3.5))
    for i in range(pieces):
        X, Y = ue(p0[0] + ux * rl * i / pieces + ox * out, p0[1] + uy * rl * i / pieces + oy * out)
        X2, Y2 = ue(p0[0] + ux * rl * (i + 1) / pieces + ox * out, p0[1] + uy * rl * (i + 1) / pieces + oy * out)
        plank_pair("AwnBeam_%s_%d" % (bid, i), X, Y, under - 16, math.degrees(math.atan2(Y2 - Y, X2 - X)),
                   rl * 100 / pieces, False)


OPP = {"north": "south", "south": "north", "west": "east", "east": "west"}
BANISTER_SHARE = 0.4             # terraces edged with Favela's frame banister instead of the stone parapet
EDGE_RNG = random.Random(41)     # its own sequence


def spawn_wall_at(lx, ly, reach=0.8):
    """(lx, ly) is at a spawn door's end wall (2 storeys of 4 m across the alley end, 3.375 m either side of the
    door, on the arena edge) - within `reach` m of the edge line."""
    for d in L["doors"]:
        if d["face"] in ("N", "S") and abs(lx - d["x"]) <= 3.4 and abs(ly - d["y"]) <= reach:
            return True
        if d["face"] in ("E", "W") and abs(ly - d["y"]) <= 3.4 and abs(lx - d["x"]) <= reach:
            return True
    return False


def taller_at(lx, ly, z):
    """A house at least z (cm) tall covers (lx, ly), or a spawn door's end wall stands there - the bare arena edge
    doesn't count. (Was: a 2-storey block; the terraces pass their floor + 2 m since houses differ in height.)"""
    return spawn_wall_at(lx, ly) or any(b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] and
                                        b.get("z", 0.0) + b["storeys"] * b["sh"] - ZB >= z for b in BLOCKS.values()) or \
        any(e["x0"] < lx < e["x1"] and e["y0"] < ly < e["y1"] and e["top"] - ZB >= z for e in EXTRA_SOLID)


def twin_terrace_at(lx, ly, me):
    """Another terrace house of about the same height (within 60 cm) with a lower id covers (lx, ly): the parapet
    between the two is that house's, so the two caps don't cross."""
    return any(b is not me and b["roof"] == "terrace" and b["id"] < me["id"] and abs(b["sh"] - me["sh"]) < 60 and
               b["x0"] < lx < b["x1"] and b["y0"] < ly < b["y1"] for b in BLOCKS.values())

if TERRACES:
    for bid, b in BLOCKS.items():
        ZB = b.get("z", 0.0)
        if b["roof"] != "terrace":
            continue
        x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
        floor = b["sh"] - 5                                 # the lid's top
        zt = b["sh"] + 200.0                                # "taller": a wall at least 2 m over the terrace floor
        # Which sides are open at storey 1 (no taller neighbour or arena edge against them)?
        sides = {"north": ((x0, y0), (x1, y0)), "south": ((x0, y1), (x1, y1)), "west": ((x0, y0), (x0, y1)),
                 "east": ((x1, y0), (x1, y1))}
        open_runs = {}
        for side, (p0, p1) in sides.items():
            nlx, nly = LNORM[side]
            length = abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])
            ux, uy = (p1[0] - p0[0]) / length, (p1[1] - p0[1]) / length
            # open = no taller block there; the arena edge counts as open too, so terraces on edge blocks still
            # get a parapet on their outer side (visible from above)
            cells = [k for k in range(int(round(length / 1.5)))
                     if not taller_at(p0[0] + ux * (k + 0.5) * 1.5 + nlx * 0.75,
                                      p0[1] + uy * (k + 0.5) * 1.5 + nly * 0.75, zt) and
                     not twin_terrace_at(p0[0] + ux * (k + 0.5) * 1.5 + nlx * 0.75,
                                         p0[1] + uy * (k + 0.5) * 1.5 + nly * 0.75, b)]
            if cells:
                open_runs[side] = (p0, ux, uy, cells, length)
        # Edge style per terrace (user 2026-11-03: "use main border on top of a stone bannister. also the favela level
        # used a wooden window frame as banisters as well. Use that as variation"): a stone parapet capped with the
        # SM_MainBorder_04 trim, or (BANISTER_SHARE of them) Favela's frame banister.
        style = "banister" if EDGE_RNG.random() < BANISTER_SHARE else "parapet"
        # Parapets: per open run, SM_Wall_14 (runs along its local +Y, thickness inward), placed like the bands.
        # North/south parapets stop 20 cm short where an east/west side is open too (a butt joint: no coincident faces).
        for side, (p0, ux, uy, cells, f_len) in open_runs.items():
            runs = []
            for k in cells:
                if runs and runs[-1][1] == k:
                    runs[-1][1] = k + 1
                else:
                    runs.append([k, k + 1])
            for r, (k0, k1) in enumerate(runs):
                # A face off the 1.5 m grid (a strip a story level stepped back) ends where the face does, not a cell on.
                e1 = k1 * 1.5 if k1 * 1.5 - f_len <= 1e-6 else f_len
                a = (p0[0] + ux * k0 * 1.5, p0[1] + uy * k0 * 1.5)
                c = (p0[0] + ux * e1, p0[1] + uy * e1)
                A, C = ue(*a), ue(*c)
                rx, ry = RUN[side]
                start = A if (C[0] - A[0]) * rx + (C[1] - A[1]) * ry > 0 else C
                RL = (k1 - k0) * 150.0 if e1 == k1 * 1.5 else (e1 - k0 * 1.5) * 100.0
                # Each end: where a taller neighbour stands ahead (in front of the face, or in line behind it) run
                # 10 cm into its wall; where another parapet turns the corner, north/south parapets stop 20 cm short
                # (butt joint). Parapets sit 1 cm in from the face line, so running into an in-line neighbour never
                # puts the parapet's face in that neighbour's face.
                nlx, nly = LNORM[side]
                cuts = []
                for (ex, ey), (ox, oy) in ((a, (-ux, -uy)), (c, (ux, uy))):
                    # (taller_at, not solid: the arena edge is no wall to run into - the parapets turn the corner)
                    ahead_front = taller_at(ex + ox * 0.75 + nlx * 0.75, ey + oy * 0.75 + nly * 0.75, zt)
                    ahead_behind = taller_at(ex + ox * 0.75 - nlx * 0.75, ey + oy * 0.75 - nly * 0.75, zt)
                    if ahead_front or ahead_behind:
                        cuts.append(-10.0)
                    elif side in ("north", "south"):
                        cuts.append(20.0)
                    else:
                        cuts.append(0.0)
                cut_start, cut_end = cuts if start == A else cuts[::-1]
                start = (start[0] + rx * cut_start, start[1] + ry * cut_start)
                RL -= cut_start + cut_end
                inx, iny = NORMAL[side]
                if style == "banister":
                    # The wooden window as banister (user: "the banister window frame I was talking about was a wooden
                    # one"): Favela stands SM_windows_06 (172 x 12 x 80 cm, MI_Windows_02 wood) on the top of the wall
                    # below a roof edge (36 of its 40), at 1.66 / 1.66 / 1.24 - panels ~2.85 m wide, 1 m tall. Here:
                    # panels <= 2.85 m filling the run, 1 m tall, 12 cm deep. The mesh runs along its local -X with its
                    # depth on local -Y, so it turns 180 and its pivot sits 13 cm in (the panel fills 13 to 1 cm in).
                    n = max(1, math.ceil(RL / 285.0))
                    for i in range(n):
                        px = start[0] + rx * RL * i / n - inx * 13.0
                        py = start[1] + ry * RL * i / n - iny * 13.0
                        put("Banister_%s_%s%d_%d" % (bid, side[0].upper(), r, i), FV + "SM_windows_06", px, py,
                            b["sh"], YAW[side] + 180, (RL / n / 172.0, 1.0, 1.24), folder=TER)
                    continue
                pieces = max(1, math.ceil(RL / 200.0))
                for i in range(pieces):
                    px = start[0] + rx * RL * i / pieces - inx * 1.0
                    py = start[1] + ry * RL * i / pieces - iny * 1.0
                    put("Parapet_%s_%s%d_%d" % (bid, side[0].upper(), r, i), FV + "SM_Wall_14", px, py, b["sh"],
                        YAW[side] - 90, (1, RL / pieces / 200.0, 1), folder=TER, mats=[CONC])
                # The cap: SM_MainBorder_04 along the top, 5 cm in from the face (it spans 18 cm in to 8 cm out), as
                # Favela caps its parapets. At a corner where two parapets meet, the east/west cap runs 8 cm past
                # the corner and the north/south one (its parapet stopped 20 cm short) runs back 2 cm to meet it;
                # where the parapet runs into a neighbour's wall, the cap stops with it.
                ext = {20.0: 2.0, 0.0: 8.0, -10.0: 0.0}
                e0, e1 = ext[cut_start], ext[cut_end]
                for i in range(pieces):
                    seg = RL / pieces
                    t0 = e0 if i == 0 else 0.0
                    t1 = e1 if i == pieces - 1 else 0.0
                    px = start[0] + rx * (seg * i - t0) - inx * 5.0
                    py = start[1] + ry * (seg * i - t0) - iny * 5.0
                    put("ParapetCap_%s_%s%d_%d" % (bid, side[0].upper(), r, i), FV + "SM_MainBorder_04", px, py,
                        b["sh"] + PARAPET_H, YAW[side], ((seg + t0 + t1) / 150.0, 1, 1), folder=TER)
        if b.get("balcony") and min(x1 - x0, y1 - y0) >= 3.0:
            lean_to(bid, b, floor)
            continue
        # Sheets: one row along the long axis, the block's depth wide.
        along_x = (x1 - x0) >= (y1 - y0)
        RL, RD = ((x1 - x0), (y1 - y0)) if along_x else ((y1 - y0), (x1 - x0))
        n = max(1, math.ceil((RL * 100 + 20) / 350.0))
        seg = (RL * 100 + 20) / n                            # +10 cm overhang at each end
        sx = (seg + 30) / 382.0                              # 30 cm end laps
        sy = (RD * 100 + 10) / 154.0
        zp = floor + SHEET_UNDER - 72                        # SM_Slate_01's underside is 72 cm above its pivot
        yaw = 90 if along_x else 180                         # layout x runs along UE +Y, layout y along UE -X
        c, s_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        ox, oy = -2 * sx, -35 * sy                           # the sheet's centre, in its local frame, from the pivot
        for i in range(n):
            t = -0.1 + seg / 100.0 * (i + 0.5)               # m along the long axis from the block's start
            lx, ly = (x0 + t, (y0 + y1) / 2) if along_x else ((x0 + x1) / 2, y0 + t)
            cx, cy = ue(lx, ly)
            put("Sheet_%s_%d" % (bid, i), FV + "SM_Slate_01", cx - (ox * c - oy * s_), cy - (ox * s_ + oy * c),
                zp + 2 * (i % 2), yaw, (sx, sy, 1), folder=TER)
        # Plank frame along open long sides: posts on the parapet line every <= 1.9 m, a beam under the sheet edge.
        for side in (("north", "south") if along_x else ("west", "east")):
            if side not in open_runs:
                continue
            p0, ux, uy, cells, _len = open_runs[side]
            nlx, nly = LNORM[side]
            post_in = 0.20 if style == "banister" else 0.12      # over the parapet, or clear behind the banister
            ends = (p0[0] - nlx * post_in, p0[1] - nly * post_in)
            nposts = max(2, math.ceil(RL / 1.9) + 1)
            for i in range(nposts):
                f = 0.1 + (RL - 0.2) * i / (nposts - 1)
                X, Y = ue(ends[0] + ux * f, ends[1] + uy * f)
                base = floor if style == "banister" else b["sh"] + PARAPET_H   # behind a banister: on the floor
                plank_pair("Post_%s_%s%d" % (bid, side[0].upper(), i), X, Y, base, YAW[side],
                           floor + SHEET_UNDER - base, True)
            pieces = max(1, math.ceil(RL / 3.5))
            for i in range(pieces):
                X, Y = ue(ends[0] + ux * RL * i / pieces, ends[1] + uy * RL * i / pieces)
                X2, Y2 = ue(ends[0] + ux * RL * (i + 1) / pieces, ends[1] + uy * RL * (i + 1) / pieces)
                plank_pair("Beam_%s_%s%d" % (bid, side[0].upper(), i), X, Y, floor + SHEET_UNDER - 16,
                           math.degrees(math.atan2(Y2 - Y, X2 - X)), RL * 100 / pieces, False)
ZB = 0.0   # back to the ground after the per-house loops
