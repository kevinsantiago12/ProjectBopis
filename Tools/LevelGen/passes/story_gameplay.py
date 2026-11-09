# Pass `story_gameplay` (story levels). Only what the first build needs (user 2026-11-08: buildings first; the layout's fights,
# inspects and checkpoints wait for their code): the player start, a nav mesh bounds volume and a Lightmass importance volume
# over the whole level. Written to <prefix>gameplay.json.
# Needs: LAYOUT_RAW, AREAS, BLOCKS, EXTRA_SOLID, ground_z, ue.
_xs = [a["r"][0] for a in AREAS] + [a["r"][2] for a in AREAS] + [b["x0"] for b in BLOCKS.values()] + [b["x1"] for b in BLOCKS.values()]
_ys = [a["r"][1] for a in AREAS] + [a["r"][3] for a in AREAS] + [b["y0"] for b in BLOCKS.values()] + [b["y1"] for b in BLOCKS.values()]
_bx0, _bx1, _by0, _by1 = min(_xs), max(_xs), min(_ys), max(_ys)
_X1, _Y0 = ue(_bx0, _by0)
_X0, _Y1 = ue(_bx1, _by1)
_sx, _sy = LAYOUT_RAW["start"]
_ps = list(ue(_sx, _sy)) + [ground_z(_sx, _sy) + 100.0]
gameplay = {
    "player_start": _ps, "player_yaw": 90.0,       # along the main street, east
    # boxes in cm, centre and full size: the placer sizes the volumes' brushes from these
    "nav": {"centre": [(_X0 + _X1) / 2, (_Y0 + _Y1) / 2, 450.0], "size": [_X1 - _X0 + 200.0, _Y1 - _Y0 + 200.0, 1500.0]},
    "lmv": {"centre": [(_X0 + _X1) / 2, (_Y0 + _Y1) / 2, 500.0], "size": [_X1 - _X0 + 400.0, _Y1 - _Y0 + 400.0, 1700.0]},
    "map": LEVEL.MAP,
}
print("story gameplay: start", [round(v) for v in _ps], "nav", [round(v) for v in gameplay["nav"]["size"]])
