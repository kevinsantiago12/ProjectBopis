# Pass `story_dress_end` (story levels; 2026-11-09). What the dressing passes placed outside the dressed houses' sections (a roof tank
# on a compound house, a wire to its wall) comes out: by the house in the label when there is one, else by where it stands.
def _keep(p):
    for t in p["label"].split("_")[:3]:
        h = t[:-1] if t.endswith("b") and t[:-1] in BLOCKS else t
        if h in BLOCKS:
            return LEVEL.dress_house(BLOCKS[h])
    return LEVEL.dress_point(*lay(p["loc"][0], p["loc"][1]))


_dressed = items[_dress_start:]
# A wire's rods (<wire>_<k>) go together: kept if any of them is kept. Decided one by one, a wire leaving a pole on a section's edge lost its
# first rod (2026-11-09).
_wire_keep = {}
for p in _dressed:
    q = p["label"].rsplit("_", 1)
    if p["folder"] == DR_WIRES and p["asset"] == CUBE and len(q) == 2 and q[1].isdigit():
        _wire_keep[q[0]] = _wire_keep.get(q[0], False) or _keep(p)


def _keep2(p):
    q = p["label"].rsplit("_", 1)
    if p["folder"] == DR_WIRES and p["asset"] == CUBE and len(q) == 2 and q[0] in _wire_keep:
        return _wire_keep[q[0]]
    return _keep(p)


_kept = [p for p in _dressed if _keep2(p)]
items[_dress_start:] = _kept
print("dressing: %d placed, %d kept in the dressed sections" % (len(_dressed), len(_kept)))

# Posters behind a post come out, as in the arena (arena_report): the poles go in after them. User 2026-11-06: "there is no way he
# was able to stick that behind the post". A plane's normal is its local Z, its width along local X.
_behind_post = set()
for p in items[_dress_start:]:
    if p["folder"] != DR_POSTERS:
        continue
    pi_, ya_, ro_ = (math.radians(a_) for a_ in p["rot"])
    nx_ = -(math.cos(ro_) * math.sin(pi_) * math.cos(ya_) + math.sin(ro_) * math.sin(ya_))
    ny_ = math.cos(ya_) * math.sin(ro_) - math.cos(ro_) * math.sin(pi_) * math.sin(ya_)
    len_ = math.hypot(nx_, ny_) or 1.0
    if _post_in_front(p["loc"][0], p["loc"][1], nx_ / len_, ny_ / len_, abs(p["scale"][0]) * 50.0):
        _behind_post.add(p["label"])
items[_dress_start:] = [p for p in items[_dress_start:] if p["label"] not in _behind_post]
print("  posters behind a post, taken out:", len(_behind_post))
