# Pass `story_sections` (story levels). Every piece gets the section (1..7) whose _Art sublevel it goes into (the spec's
# streaming plan: one persistent map, an _Art and a _Gameplay sublevel per section). A street house goes whole into the
# section of the ground it faces most; a building the player enters into its own (levels/*.py ENTERED); anything else by
# where it stands: the area it's in, or the nearest one. Run last.
# Needs: AREAS, BLOCKS, ENTERED, WOODEN (setup), lay, items.
_sec_of_bld = {e["id"]: e["sec"] for e in ENTERED}
_sec_of_bld[WOODEN["id"]] = WOODEN["sec"]
_area_by_id = {a["id"]: a for a in AREAS}


def _sec_at(lx, ly):
    best = None
    for a in AREAS:
        x0, y0, x1, y1 = a["r"]
        d = math.hypot(max(x0 - lx, 0.0, lx - x1), max(y0 - ly, 0.0, ly - y1))
        if best is None or d < best[0]:
            best = (d, a["sec"])
    return best[1]


_sec_of_house = {}
for bid, b in BLOCKS.items():
    votes = {}
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    for k in range(9):
        for lx, ly in ((x0 + (x1 - x0) * (k + 0.5) / 9, y0 - 0.4), (x0 + (x1 - x0) * (k + 0.5) / 9, y1 + 0.4),
                       (x0 - 0.4, y0 + (y1 - y0) * (k + 0.5) / 9), (x1 + 0.4, y0 + (y1 - y0) * (k + 0.5) / 9)):
            for a in AREAS:
                if a["r"][0] < lx < a["r"][2] and a["r"][1] < ly < a["r"][3]:
                    votes[a["sec"]] = votes.get(a["sec"], 0) + 1
    _sec_of_house[bid] = max(votes, key=lambda s_: (votes[s_], -s_)) if votes else _sec_at((x0 + x1) / 2, (y0 + y1) / 2)
for bid in list(_sec_of_house):                    # a balcony strip goes with its house
    if bid.endswith("b") and bid[:-1] in _sec_of_house:
        _sec_of_house[bid] = _sec_of_house[bid[:-1]]

_SPECIAL_SEC = {"GarageRoof": 3, "CoveredAlley": 5, "Step": 2}
_sec_n = {}
for p in items:
    toks = p["label"].split("_")
    sec = None
    for t in toks[:3]:
        if t in _sec_of_bld:
            sec = _sec_of_bld[t]
            break
        if t in _sec_of_house:
            sec = _sec_of_house[t]
            break
        if t in _SPECIAL_SEC:
            sec = _SPECIAL_SEC[t]
            break
    if sec is None and toks[0] in ("Ground", "YardWall") and len(toks) > 1 and toks[1] in _area_by_id:
        sec = _area_by_id[toks[1]]["sec"]
    if sec is None and toks[0] == "Gate":
        sec = 1 if toks[1] == "0" else 3
    if sec is None:
        sec = _sec_at(*lay(p["loc"][0], p["loc"][1]))
    p["sec"] = sec
    _sec_n[sec] = _sec_n.get(sec, 0) + 1
print("sections:", dict(sorted(_sec_n.items())))
# For the placers (written with the layout, <prefix>layout.json): each street house's section, and whether it takes the slum's
# dressing. swap_sections_ue.py swaps a dressed house whole, whichever section it went into.
# "r": the footprint before any setback, "rf" after it, layout metres; "top": the wall's top, cm.
L["houses"] = {bid: {"sec": _sec_of_house[bid], "dressed": bool(LEVEL.dress_house(b)),
                     "r": [b["x0"] - b.get("setback", {}).get("west", 0.0), b["y0"] - b.get("setback", {}).get("north", 0.0),
                           b["x1"] + b.get("setback", {}).get("east", 0.0), b["y1"] + b.get("setback", {}).get("south", 0.0)],
                     "rf": [b["x0"], b["y0"], b["x1"], b["y1"]], "top": FLOOR_H + b.get("z", 0.0) + b["storeys"] * b["sh"]}
               for bid, b in BLOCKS.items()}
L["buildings"] = sorted(_sec_of_bld)               # the entered buildings' ids
