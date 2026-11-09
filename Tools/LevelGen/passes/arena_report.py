# Pass `arena_report`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Arena only: dressing reports, posters behind posts and buried stalls taken out.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
print("street:", dict(sorted(_street_n.items())))
print("  bare ground tiles left:", sum(1 for t in _dress_tiles if t["s"] == 0 and not t["has"]))

_bare = [t for t in _dress_tiles if not t["has"]]
print("dressing: %d blank tiles (no hollow blocks), %d now have something, %d stay bare" % (
    len(_dress_tiles), len(_dress_tiles) - len(_bare), len(_bare)))
print("  rooms %d, downpipes %d, air conditioners %d, patches %s, vents on %d tiles, steps %s, laundry %s" % (
    _n_rooms, _n_pipes, _n_acs, _n_patch, _n_vents, _n_steps, _n_laundry))
# Posters behind a post come out here, as the poles go in after them. A plane's normal is its local Z, its width along local X.
_behind_post = set()
for p in items:
    if p["folder"] != DR_POSTERS:
        continue
    pi_, ya_, ro_ = (math.radians(a_) for a_ in p["rot"])
    nx_ = -(math.cos(ro_) * math.sin(pi_) * math.cos(ya_) + math.sin(ro_) * math.sin(ya_))
    ny_ = math.cos(ya_) * math.sin(ro_) - math.cos(ro_) * math.sin(pi_) * math.sin(ya_)
    len_ = math.hypot(nx_, ny_) or 1.0
    if _post_in_front(p["loc"][0], p["loc"][1], nx_ / len_, ny_ / len_, abs(p["scale"][0]) * 50.0):
        _behind_post.add(p["label"])
print("  posters behind a post, taken out:", len(_behind_post))
items[:] = [p for p in items if p["label"] not in _buried_stalls and p["label"] not in _behind_post]
