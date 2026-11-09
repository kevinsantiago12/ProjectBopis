# Pass `story_resolve` (opt-in, story levels; 2026-11-08). The street houses' corner rules were made on the arena's
# geometry; on new ground they leave a few odd corners (a setback beside a neighbour's wall with its trim at the same
# height, back-to-back faces of houses on different storey heights). Rather than special cases in the arena's code, this
# finds what check_overlaps.py fails, among trims (SM_MainBorder_04) and bands (SM_Wall_14), and fixes it:
#   - two trims crossing, or two same-facing pieces overlapping: the one whose end pokes into the other is shortened past
#     it, by 1 cm more than the overlap;
#   - a band's end cap lying in another piece's face: that end moves 2 cm into the other piece's body.
# Prints what it changed. The arena doesn't run it (its plan must stay as it is). Needs: items.
_LOC = {"SM_MainBorder_04": (0, -13, -8, 150, 13, 8), "SM_Wall_14": (0, 0, 0, 20, 200, 106),
        "SM_Wall_Tile_Blue": (0, -20, 0, 225, 0, 300), "SM_Wall_Tile_01": (0, -20, 0, 225, 0, 300),
        "SM_Wall_Tile_03": (0, -20, 0, 112.5, 0, 300), "SM_WallDoor_01": (0, -20, 0, 225, 0, 300),
        "SM_Wall_Windows_01": (0, -20, 0, 225, 0, 300)}


def _rbox(p):
    b = _LOC[p["asset"].split("/")[-1]]
    x, y, z = p["loc"]
    yaw = math.radians(p["rot"][1])
    sx, sy, sz = p["scale"]
    c, s = round(math.cos(yaw)), round(math.sin(yaw))
    pts = [(x + (lx * sx) * c - (ly * sy) * s, y + (lx * sx) * s + (ly * sy) * c) for lx in (b[0], b[3]) for ly in (b[1], b[4])]
    xs, ys = [q[0] for q in pts], [q[1] for q in pts]
    return min(xs), min(ys), z + b[2] * sz, max(xs), max(ys), z + b[5] * sz


def _run(p):
    """(start, unit direction, length, scale index, native length) of a trim or band along its run, UE cm."""
    a = p["asset"].split("/")[-1]
    th = math.radians(p["rot"][1])
    if a == "SM_MainBorder_04":
        d, k, unit = (round(math.cos(th)), round(math.sin(th))), 0, 150.0
    elif a.startswith(("SM_Wall_Tile", "SM_WallDoor", "SM_Wall_Windows")):   # tiles run along local X too
        d, k, unit = (round(math.cos(th)), round(math.sin(th))), 0, (112.5 if a == "SM_Wall_Tile_03" else 225.0)
    else:
        d, k, unit = (-round(math.sin(th)), round(math.cos(th))), 1, 200.0
    return (p["loc"][0], p["loc"][1]), d, abs(p["scale"][k]) * unit, k, unit


def _set_run(p, start, d, length, k, unit):
    p["loc"][0], p["loc"][1] = round(start[0], 1), round(start[1], 1)
    p["scale"][k] = round(max(length, 1.0) / unit, 4)


def _yaw_face(p):
    y_ = round(p["rot"][1]) % 360
    return (y_ + 90) % 360 if p["asset"].split("/")[-1] == "SM_Wall_14" else y_


_fixed_n = {"shortened": 0, "caps moved": 0}
_gone = set()
for _outer in range(4):                          # each step can make work for the other: repeat until neither changes anything
    _before = dict(_fixed_n)
    for _round in range(400):
        if _gone:
            items[:] = [p for p in items if id(p) not in _gone]
            _fixed_n["removed"] = _fixed_n.get("removed", 0) + len(_gone)
            _gone.clear()
        ps = [p for p in items if p["asset"].split("/")[-1] in _LOC]
        bx = [_rbox(p) for p in ps]
        grid = {}
        for i, b in enumerate(bx):
            for gx in range(int(b[0] // 300), int(b[3] // 300) + 1):
                for gy in range(int(b[1] // 300), int(b[4] // 300) + 1):
                    grid.setdefault((gx, gy), []).append(i)
        changed = False
        done = set()
        for cell in grid.values():
            for a in cell:
                for b in cell:
                    if b <= a or (a, b) in done:
                        continue
                    done.add((a, b))
                    A, B = bx[a], bx[b]
                    ov = [min(A[k + 3], B[k + 3]) - max(A[k], B[k]) for k in range(3)]
                    if not all(o > 1.0 for o in ov):
                        continue
                    pa, pb = ps[a], ps[b]
                    ka, kb = pa["asset"].split("/")[-1], pb["asset"].split("/")[-1]
                    trims = ka == kb == "SM_MainBorder_04"
                    same = _yaw_face(pa) == _yaw_face(pb) and "SM_MainBorder_04" not in (ka, kb)
                    if not (trims or same):
                        continue
                    if pa["label"].split("_Trim")[0].split("_Band")[0] == pb["label"].split("_Trim")[0].split("_Band")[0]:
                        continue
                    for p, q, Q in ((pa, pb, B), (pb, pa, A)):
                        if p["asset"].split("/")[-1] not in ("SM_MainBorder_04", "SM_Wall_14"):
                            continue
                        st, d, L_, k, unit = _run(p)
                        en = (st[0] + d[0] * L_, st[1] + d[1] * L_)
                        ax = 0 if d[0] else 1
                        lo, hi = Q[ax], Q[ax + 3]
                        if lo - 0.5 <= en[ax] <= hi + 0.5:               # its far end is in the other: pull it back
                            cut = (en[ax] - lo) if d[ax] > 0 else (hi - en[ax])
                            if L_ - cut - 1.0 < 5.0:
                                _gone.add(id(p))                         # nothing worth keeping: a scrap of trim
                            else:
                                _set_run(p, st, d, L_ - cut - 1.0, k, unit)
                        elif lo - 0.5 <= st[ax] <= hi + 0.5:             # its start is: move the start on
                            cut = (hi - st[ax]) if d[ax] > 0 else (st[ax] - lo)
                            st2 = (st[0] + d[0] * (cut + 1.0), st[1] + d[1] * (cut + 1.0))
                            if L_ - cut - 1.0 < 5.0:
                                _gone.add(id(p))
                            else:
                                _set_run(p, st2, d, L_ - cut - 1.0, k, unit)
                        else:
                            continue
                        _fixed_n["shortened"] += 1
                        changed = True
                        break
                    if changed:
                        break
                if changed:
                    break
            if changed:
                break
        if not changed:
            break

    # Band end caps in another piece's face: 2 cm into that piece's body.
    for _round in range(20):
        ps = [p for p in items if p["asset"].split("/")[-1] in _LOC and p["asset"].split("/")[-1] != "SM_MainBorder_04"]
        bx = [_rbox(p) for p in ps]
        faces_ = []
        for p, b in zip(ps, bx):
            yaw = _yaw_face(p)
            x0, y0, z0, x1, y1, z1 = b
            if yaw in (0, 180):
                faces_.append((p, 1, y1 if yaw == 0 else y0, (x0, x1), (z0, z1), 1 if yaw == 0 else -1))
            else:
                faces_.append((p, 0, x1 if yaw == 270 else x0, (y0, y1), (z0, z1), 1 if yaw == 270 else -1))
        # As check_overlaps: a cap meeting another cap in its plane is a junction (sealed), and one inside a corner column
        # can't be seen. Neither is moved.
        caps_ = []
        for p, b in zip(ps, bx):
            st, d, L_, k, unit = _run(p)
            ax = 0 if d[0] else 1
            span = (b[1], b[4]) if ax == 0 else (b[0], b[3])
            for v in (b[ax], b[ax + 3]):
                caps_.append((p, ax, v, span, (b[2], b[5])))
        cols_ = [(c["loc"][0], c["loc"][1], c["loc"][2], c["loc"][0] + c["scale"][0] * 100, c["loc"][1] + c["scale"][1] * 100,
                  c["loc"][2] + c["scale"][2] * 100) for c in items if c["label"].startswith("Column_")]
        # The caps and faces by axis and plane (1 cm bins): a lookup only ever wants those within half a centimetre of a plane. The
        # candidates come back in their list order, so the first match (and so the result) is as a full scan's. (2026-11-09: the
        # full scans were 38 million comparisons a run.)
        _cap_ix, _face_ix = {}, {}
        for j_, c_ in enumerate(caps_):
            _cap_ix.setdefault((c_[1], math.floor(c_[2])), []).append(j_)
        for j_, f_ in enumerate(faces_):
            _face_ix.setdefault((f_[1], math.floor(f_[2])), []).append(j_)

        def _near(ix, ax, v):
            b_ = math.floor(v)
            return sorted(j_ for k_ in (b_ - 1, b_, b_ + 1) for j_ in ix.get((ax, k_), ()))

        def _sealed(p, ax, v, span, zs):
            return any(q is not p and qa == ax and abs(qv - v) < 0.5 and min(qs[1], span[1]) - max(qs[0], span[0]) > 0.5 and
                       min(qz[1], zs[1]) - max(qz[0], zs[0]) > 0.5 for q, qa, qv, qs, qz in (caps_[j_] for j_ in _near(_cap_ix, ax, v)))

        def _in_col(ax, v, lo, hi, z0, z1):
            for c in cols_:
                a0, a1 = (c[0], c[3]) if ax == 0 else (c[1], c[4])
                b0, b1 = (c[1], c[4]) if ax == 0 else (c[0], c[3])
                if a0 - 1 <= v <= a1 + 1 and b0 - 1 <= lo and hi <= b1 + 1 and c[2] - 1 <= z0 and z1 <= c[5] + 1:
                    return True
            return False
        moved = False
        for p, b in zip(ps, bx):
            tile_ = p["asset"].split("/")[-1] != "SM_Wall_14"
            if tile_ and not p["asset"].split("/")[-1].startswith(("SM_Wall_Tile", "SM_WallDoor", "SM_Wall_Windows")):
                continue
                continue
            st, d, L_, k, unit = _run(p)
            ax = 0 if d[0] else 1
            x0, y0, z0, x1, y1, z1 = b
            for end_v, is_start in ((st[ax], True), (st[ax] + d[ax] * L_, False)):
                for q, fax, plane, (lo, hi), (fz0, fz1), nsign in (faces_[j_] for j_ in _near(_face_ix, ax, end_v)):
                    if q is p or fax != ax or abs(plane - end_v) > 0.5:
                        continue
                    # A tile's end moves out of a band's or another tile's face, taking its own band and trims with it: moved alone (the
                    # first try) its band and trims were left behind, and 9 new caps came of 1.
                    span = (y0, y1) if ax == 0 else (x0, x1)
                    if _sealed(p, ax, end_v, span, (z0, z1)):
                        continue
                    o_lo, o_hi = max(lo, span[0]), min(hi, span[1])
                    if o_hi - o_lo > 0.5 and min(fz1, z1) - max(fz0, z0) > 0.5 and                         not _in_col(ax, end_v, o_lo, o_hi, max(fz0, z0), min(fz1, z1)):
                        into = -nsign                       # the other piece's body lies behind its face
                        mates = [p] + ([c for c in items if c["label"] in (p["label"] + "_Band", p["label"] + "_Trim300", p["label"] + "_Trim400")]
                                       if tile_ else [])
                        for c in mates:
                            cst, cd, cL, ck, cunit = _run(c)
                            cax = 0 if cd[0] else 1
                            if is_start:
                                if c is not p and abs(cst[cax] - end_v) > 2.0:
                                    continue                # this companion doesn't end here
                                delta = 2.0 * into * cd[cax]    # >0: the start moves on (shorter)
                                _set_run(c, (cst[0] + cd[0] * delta, cst[1] + cd[1] * delta), cd, cL - delta, ck, cunit)
                            else:
                                if c is not p and abs(cst[cax] + cd[cax] * cL - end_v) > 2.0:
                                    continue
                                _set_run(c, cst, cd, cL + 2.0 * into * cd[cax], ck, cunit)
                        _fixed_n["caps moved"] += 1
                        moved = True
                        break
                if moved:
                    break
            if moved:
                break
        if not moved:
            break
    if _fixed_n == _before:
        break
print("resolve:", _fixed_n)
