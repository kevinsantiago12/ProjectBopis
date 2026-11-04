"""Headless, read-only: measures the kit meshes the level generator places and writes a manifest per pack.
Run: .\\Tools\\AnimAuthoring\\RunUnreal.ps1 .\\Tools\\AssetGen\\measure_ue.py
Writes Tools/AssetGen/manifest/<pack>.json and index.json (all packs, keyed by object path). Saves nothing in Content.

Everything is local and unscaled, in cm. Per mesh:
  bounds_min/max, size, pivot (per axis: min / centre / max / offset), long/thin axis;
  slots (name, material, blend mode, two-sided, triangle area share), tris / verts per LOD, nanite, lightmap;
  collision {trace_flag, type, shapes, boxes}, sockets;
  sides: per local side (+X..-Z), the triangles facing out of it and how much of that bounds face they cover,
         so open_faces lists the sides with no geometry (open backs, tops);
  normal_spread: area-weighted mean |normal| per axis (corrugation runs along the axis with the low value);
  corners: every distinct vertex, for meshes with 40 or fewer (wedges, cubes, planes);
  openings: for wall/frame pieces, holes through the face plane (bbox of each empty region, 4 cm grid).
"""
import json
import math
import os
import re
import unreal

AS, FV, ME, PM, LP = ("/Game/AsiaSlum/FBX/", "/Game/Megapack/Meshes/Favela/", "/Game/Megapack/Meshes/MiddleEast/",
                      "/Game/Philippines_Markets/Props/", "/Game/LevelPrototyping/Meshes/")
# Level-gen's first ask (2026-11-03) first, then everything else gen_level.py references.
MESHES = [FV + "SM_windows_06", AS + "SM_Stair_A_001", AS + "SM_Floor_A_001", FV + "SM_Wooden_part_03",
          FV + "SM_Wooden_part_05", FV + "SM_Pillar_01", FV + "SM_Slate_01",
          # Favela walls and openings
          FV + "SM_Wall_Tile_01", FV + "SM_Wall_Tile_Blue", FV + "SM_Wall_Tile_03", FV + "SM_WallDoor_01",
          FV + "SM_Wall_Windows_01", FV + "SM_Wall_14", FV + "SM_MainBorder_04", FV + "SM_windows_02",
          FV + "SM_Door_01", FV + "SM_Door_01_Blue", FV + "SM_Door_01_Green", FV + "SM_Door_Jamb_01",
          # AsiaSlum
          AS + "SM_HouseDoor_A_002", AS + "SM_HouseDoor_A_004", AS + "SM_HouseDoor_A_005", AS + "SM_HouseDoor_B_003",
          AS + "SM_HouseWall_A_001", AS + "SM_HouseWall_A_001_HalfA", AS + "SM_HouseWallDoorFrmae_A_001",
          AS + "SM_HouseWallDoorFrmae_A_002", AS + "SM_HouseWindow_A_001", AS + "SM_Shop_A_001", AS + "SM_Roof_A_002",
          AS + "SM_MetalPlate_A_001", AS + "SM_MetalPlate_A_002", AS + "SM_MetalPlate_C_001", AS + "SM_Sign_A_001",
          AS + "SM_Cable_A_005", AS + "SM_Rope_A_001", AS + "SM_AirConditioner_A_001",
          AS + "SM_AirConditionerFrame_A_001", AS + "SM_AirConditionerFan_A_001",
          # Favela dressing (off under the blockouts rule, measured for later)
          FV + "SM_Barrel_01", FV + "SM_Barrel_Cap_2", FV + "SM_Stand_01", FV + "SM_Antenna_01", FV + "SM_Antenna_02",
          FV + "SM_Antenna_03", FV + "SM_AntennaSupportPart_02",
          # MiddleEast
          ME + "SM_Concrete_Block_01", ME + "SM_Wires_01", ME + "SM_Water_Tank_01", ME + "SM_Water_Tank_02",
          ME + "SM_Water_Tank_03", ME + "SM_Garbage_bag_01", ME + "SM_Garbage_bag_green_03", ME + "SM_clothes_A_02",
          ME + "SM_clothes_A_03", ME + "SM_clothes_A_04", ME + "SM_clothes_A_05", ME + "SM_clothes_B_01",
          ME + "SM_clothes_B_02", ME + "SM_clothes_B_03",
          # Metal roof rebuild (level-gen, 2026-11-03): sheets, fascia / soffit / gable boards
          AS + "SM_MetalPlate_A_003", AS + "SM_MetalPlate_A_004", ME + "SM_wooden_beams_01", ME + "SM_wooden_beams_02",
          ME + "SM_wooden_beams_03", ME + "SM_wooden_beams_04", ME + "SM_wooden_beams_05",
          # Philippines_Markets
          PM + "Barrels_Set_01/SM_Barrel_01", PM + "Barrels_Set_01/SM_Barrel_02",
          PM + "CardboardSet_01/SM_CardboardBox_01", PM + "MonoBloc_Chairs_01/SM_Monobloc_Chair_01",
          PM + "Plastic_Crate_Set_01/SM_Plastic_Crate_01", PM + "RiceBags_01/SM_Rice_Bag_Full_01",
          # Prototyping and engine shapes
          LP + "SM_Ramp", LP + "SM_Cube", "/Engine/BasicShapes/Plane", "/Engine/BasicShapes/Cube"]
# Wall and frame pieces with holes through them: trace the openings.
OPENINGS = {FV + "SM_WallDoor_01", FV + "SM_Wall_Windows_01", AS + "SM_HouseWallDoorFrmae_A_001",
            AS + "SM_HouseWallDoorFrmae_A_002", AS + "SM_HouseWindow_A_001", AS + "SM_Shop_A_001",
            FV + "SM_windows_06", FV + "SM_windows_02", FV + "SM_Door_Jamb_01", AS + "SM_HouseDoor_A_002"}
# Walkable or sloped pieces: profile the top surface along the long axis.
PROFILE = {AS + "SM_Stair_A_001", AS + "SM_Floor_A_001", LP + "SM_Ramp", FV + "SM_Slate_01", AS + "SM_Roof_A_002",
           AS + "SM_MetalPlate_C_001", ME + "SM_Concrete_Block_01"}
BINS = 12
MAX_TRIS = 200000   # skip the per-triangle pass above this
GRID = 4.0          # cm, opening grid
SIDES = [("+X", 0, 1), ("-X", 0, -1), ("+Y", 1, 1), ("-Y", 1, -1), ("+Z", 2, 1), ("-Z", 2, -1)]
AX = "XYZ"
OUT = os.path.join(unreal.Paths.project_dir(), "Tools", "AssetGen", "manifest")


def log(msg):
    unreal.log_warning("[MEASURE] " + msg)


def r(v, n=1):
    return round(float(v), n)


def vec(v):
    return [r(v.x), r(v.y), r(v.z)]


def get(obj, name, default=None):
    try:
        return obj.get_editor_property(name)
    except Exception:
        return default


def base_flag(mi, name):
    """Blend mode or two-sided, following instance overrides up to the base material."""
    m = mi
    while m is not None and isinstance(m, unreal.MaterialInstance):
        o = get(m, "base_property_overrides")
        if o is not None and get(o, "override_" + name):
            return enum(get(o, name))
        m = get(m, "parent")
    return enum(get(m, name)) if m is not None else None


def pivot_note(lo, hi):
    out = []
    for i in range(3):
        a, b = lo[i], hi[i]
        tol = max(0.5, 0.01 * (b - a))
        if abs(a) <= tol:
            out.append(AX[i].lower() + ":min")
        elif abs(b) <= tol:
            out.append(AX[i].lower() + ":max")
        elif abs((a + b) / 2) <= tol:
            out.append(AX[i].lower() + ":centre")
        else:
            out.append(AX[i].lower() + ":offset")
    return " ".join(out)


def extends(lo, hi):
    """Which way the mesh runs from its pivot on each axis: '+X' (pivot at min), '-X' (at max), '±X' (around it)."""
    out = []
    for i in range(3):
        a, b = lo[i], hi[i]
        tol = max(0.5, 0.01 * (b - a))
        out.append(("+" if a >= -tol else "-" if b <= tol else "±") + AX[i])
    return " ".join(out)


def collision(mesh):
    bs = get(mesh, "body_setup")
    c = {"trace_flag": None, "type": "none", "shapes": 0, "boxes": [], "spheres": 0, "capsules": 0, "convex": 0}
    if bs is None:
        return c
    c["trace_flag"] = enum(get(bs, "collision_trace_flag"))
    agg = get(bs, "agg_geom")
    if agg is not None:
        for b in get(agg, "box_elems", []) or []:
            ctr, x, y, z = get(b, "center"), get(b, "x"), get(b, "y"), get(b, "z")
            rot = get(b, "rotation")
            c["boxes"].append({"min": [r(ctr.x - x / 2), r(ctr.y - y / 2), r(ctr.z - z / 2)],
                               "max": [r(ctr.x + x / 2), r(ctr.y + y / 2), r(ctr.z + z / 2)],
                               "rot": [r(rot.pitch), r(rot.yaw), r(rot.roll)] if rot else None})
        c["spheres"] = len(get(agg, "sphere_elems", []) or [])
        c["capsules"] = len(get(agg, "sphyl_elems", []) or [])
        convex = get(agg, "convex_elems", []) or []
        c["convex"] = len(convex)
        hulls = []
        for e in convex:
            pts = get(e, "vertex_data")
            if pts:
                hulls.append({"min": [r(min(p.x for p in pts)), r(min(p.y for p in pts)), r(min(p.z for p in pts))],
                              "max": [r(max(p.x for p in pts)), r(max(p.y for p in pts)), r(max(p.z for p in pts))]})
        if hulls:
            c["convex_boxes"] = hulls
    c["shapes"] = len(c["boxes"]) + c["spheres"] + c["capsules"] + c["convex"]
    if c["trace_flag"] == "CTF_USE_COMPLEX_AS_SIMPLE":
        c["type"] = "complex"
    elif c["shapes"]:
        c["type"] = "simple"
    else:
        c["type"] = "none"   # no simple shapes: traces may hit triangles, but pawns, physics and nav ignore it
    return c


def idint(x):
    """A mesh description element ID (VertexID, PolygonGroupID) as an int, however this build exposes it."""
    for f in (lambda: x.id_value, lambda: x.get_editor_property("id_value")):
        try:
            return int(f())
        except Exception:
            pass
    m = re.search(r"(-?\d+)\D*$", str(x))
    return int(m.group(1)) if m else None


def pick(result, kind):
    """The IDs of one kind out of a call's result, which this build may wrap in a tuple with the out-param."""
    out = []

    def walk(x):
        if isinstance(x, kind):
            out.append(x)
        elif isinstance(x, (list, tuple)) or (hasattr(x, "__iter__") and not isinstance(x, (str, bytes))):
            for y in x:
                walk(y)
    walk(result)
    return out


def enum(v):
    """'CTF_USE_COMPLEX_AS_SIMPLE' out of '<CollisionTraceFlag.CTF_USE_COMPLEX_AS_SIMPLE: 3>'."""
    m = re.search(r"([A-Z][A-Z0-9_]{2,})", str(v))
    return m.group(1) if m else str(v)


def uv_tangents(a, b, c, uvs, acc):
    """Which local axis U and V run along on this triangle (area-weighted |direction|), and cm per UV unit."""
    d1 = [b[i] - a[i] for i in range(3)]
    d2 = [c[i] - a[i] for i in range(3)]
    du1, dv1 = uvs[1].x - uvs[0].x, uvs[1].y - uvs[0].y
    du2, dv2 = uvs[2].x - uvs[0].x, uvs[2].y - uvs[0].y
    det = du1 * dv2 - du2 * dv1
    if abs(det) < 1e-12:
        return
    t = [(d1[i] * dv2 - d2[i] * dv1) / det for i in range(3)]   # d(position)/dU
    s = [(d2[i] * du1 - d1[i] * du2) / det for i in range(3)]   # d(position)/dV
    lt, ls = math.sqrt(sum(x * x for x in t)), math.sqrt(sum(x * x for x in s))
    cr = [d1[1] * d2[2] - d1[2] * d2[1], d1[2] * d2[0] - d1[0] * d2[2], d1[0] * d2[1] - d1[1] * d2[0]]
    w = math.sqrt(sum(x * x for x in cr)) / 2
    if lt < 1e-9 or ls < 1e-9 or w <= 0:
        return
    for i in range(3):
        acc["u"][i] += abs(t[i]) / lt * w
        acc["v"][i] += abs(s[i]) / ls * w
    acc["w"] += w
    acc["u_cm"].append(lt)
    acc["v_cm"].append(ls)


def params(mi):
    """A material's parameter names (and an instance's vector values): shows whether it can be tinted."""
    out = {}
    lib = unreal.MaterialEditingLibrary
    for kind, fn in (("vector", "get_vector_parameter_names"), ("scalar", "get_scalar_parameter_names"),
                     ("texture", "get_texture_parameter_names")):
        try:
            out[kind] = [str(n) for n in getattr(lib, fn)(mi)]
        except Exception:
            pass
    if isinstance(mi, unreal.MaterialInstance):
        vals = {}
        for n in out.get("vector", []):
            try:
                v = lib.get_material_instance_vector_parameter_value(mi, n)
                vals[n] = [r(v.r, 3), r(v.g, 3), r(v.b, 3), r(v.a, 3)]
            except Exception:
                pass
        if vals:
            out["vector_values"] = vals
        parent = get(mi, "parent")
        out["parent"] = parent.get_path_name().split(".")[0] if parent else None
    return out


def vpos(desc, vid):
    v = desc.get_vertex_position(vid)
    return (v.x, v.y, v.z)


def profile(ups, lo, hi, ext):
    """Top of the up-facing surface (normal z > 0.5) in bins along the long horizontal axis: where a stair or
    slope is high and low. Each bin: [from, to, top z] in local cm; top is None where nothing faces up."""
    ax = 0 if ext[0] >= ext[1] else 1
    w = ext[ax] / BINS
    top = [None] * BINS
    for cen, zmax in ups:
        i = min(BINS - 1, max(0, int((cen[ax] - lo[ax]) / w)))
        top[i] = zmax if top[i] is None else max(top[i], zmax)
    return {"along": AX[ax], "bins": [[r(lo[ax] + i * w), r(lo[ax] + (i + 1) * w), r(t) if t is not None else None]
                                      for i, t in enumerate(top)]}


def tri_pass(mesh, lo, hi, want_openings, want_profile=False):
    desc = mesh.get_static_mesh_description(0)
    ntri = desc.get_triangle_count()
    if ntri > MAX_TRIS:
        return {"skipped": "%d tris" % ntri}
    pos = {}
    for i in range(desc.get_vertex_count()):
        v = desc.get_vertex_position(unreal.VertexID(i))
        pos[i] = (v.x, v.y, v.z)
    ext = [hi[i] - lo[i] for i in range(3)]
    tol = [max(1.0, 0.02 * e) for e in ext]
    side_area = {s[0]: 0.0 for s in SIDES}
    side_tris = {s[0]: 0 for s in SIDES}
    face_area = {s[0]: 0.0 for s in SIDES}   # triangles facing that way anywhere
    spread = [0.0, 0.0, 0.0]
    group_area = {}
    total = 0.0
    tris, ups = [], []
    uv_ok = [True]
    uvacc = {"u": [0.0, 0.0, 0.0], "v": [0.0, 0.0, 0.0], "w": 0.0, "u_cm": [], "v_cm": []}
    for t in range(ntri):
        tid = unreal.TriangleID(t)
        vis = pick(desc.get_triangle_vertex_instances(tid), unreal.VertexInstanceID)
        if len(vis) == 3:
            vids = [desc.get_vertex_instance_vertex(vi) for vi in vis]
        else:
            vis, vids = [], pick(desc.get_triangle_vertices(tid), unreal.VertexID)
        if len(vids) != 3:
            raise RuntimeError("triangle %d has %d vertices" % (t, len(vids)))
        a, b, c = (pos.get(idint(v)) or vpos(desc, v) for v in vids)
        if vis and uv_ok[0]:
            try:
                uvs = [desc.get_vertex_instance_uv(vi, 0) for vi in vis]
                uv_tangents(a, b, c, uvs, uvacc)
            except Exception as ex:
                uv_ok[0] = False
                log("  no UVs: %s" % ex)
        e1 = (b[0] - a[0], b[1] - a[1], b[2] - a[2])
        e2 = (c[0] - a[0], c[1] - a[1], c[2] - a[2])
        n = (e1[1] * e2[2] - e1[2] * e2[1], e1[2] * e2[0] - e1[0] * e2[2], e1[0] * e2[1] - e1[1] * e2[0])
        ln = math.sqrt(n[0] ** 2 + n[1] ** 2 + n[2] ** 2)
        if ln < 1e-6:
            continue
        area = ln / 2
        n = (-n[0] / ln, -n[1] / ln, -n[2] / ln)   # Unreal winds front faces clockwise: (b-a)x(c-a) points inward
        total += area
        for i in range(3):
            spread[i] += abs(n[i]) * area
        try:
            g = idint(desc.get_triangle_polygon_group(tid))
        except Exception:
            g = 0
        group_area[g] = group_area.get(g, 0.0) + area
        cen = [(a[i] + b[i] + c[i]) / 3 for i in range(3)]
        for name, i, sgn in SIDES:
            if n[i] * sgn > 0.7:
                face_area[name] += area
                bound = hi[i] if sgn > 0 else lo[i]
                if abs(cen[i] - bound) <= tol[i]:
                    side_area[name] += area
                    side_tris[name] += 1
        if want_openings:
            tris.append((a, b, c, n))
        if want_profile and n[2] > 0.5:
            ups.append((cen, max(a[2], b[2], c[2])))
    sides = {}
    for name, i, sgn in SIDES:
        j, k = [q for q in range(3) if q != i]
        box = ext[j] * ext[k]
        sides[name] = {"tris_on_bound": side_tris[name], "cover": r(side_area[name] / box, 2) if box > 0 else 0,
                       "facing_area_m2": r(face_area[name] / 1e4, 2)}
    res = {"tris_lod0": ntri, "area_m2": r(total / 1e4, 2), "sides": sides,
           "open_faces": [s for s in sides if sides[s]["cover"] < 0.05],
           "normal_spread": [r(s / total, 2) if total else 0 for s in spread],
           "group_area_share": {str(g): r(a / total, 3) for g, a in sorted(group_area.items())} if total else {}}
    if len(pos) <= 40:
        res["corners"] = sorted({(r(p[0]), r(p[1]), r(p[2])) for p in pos.values()})
    if uvacc["w"] > 0:
        med = lambda xs: r(sorted(xs)[len(xs) // 2]) if xs else None
        res["uv0"] = {"u_along": [r(x / uvacc["w"], 2) for x in uvacc["u"]],
                      "v_along": [r(x / uvacc["w"], 2) for x in uvacc["v"]],
                      "cm_per_u": med(uvacc["u_cm"]), "cm_per_v": med(uvacc["v_cm"])}
    if want_openings:
        res["openings"] = openings(tris, lo, hi, ext)
    if want_profile:
        res["top_profile"] = profile(ups, lo, hi, ext)
    return res


def openings(tris, lo, hi, ext):
    """Holes through the face plane: rasterise every triangle facing along the thin axis onto a grid in the other two
    axes; connected empty regions are openings (or notches, if they touch the edge: see 'touches')."""
    thin = min(range(3), key=lambda i: ext[i])
    u, v = [q for q in range(3) if q != thin]
    nu, nv = max(1, int(math.ceil(ext[u] / GRID))), max(1, int(math.ceil(ext[v] / GRID)))
    cov = [[False] * nv for _ in range(nu)]
    for a, b, c, n in tris:
        if abs(n[thin]) < 0.7:
            continue
        pa, pb, pc = (a[u], a[v]), (b[u], b[v]), (c[u], c[v])
        i0 = max(0, int((min(pa[0], pb[0], pc[0]) - lo[u]) / GRID))
        i1 = min(nu - 1, int((max(pa[0], pb[0], pc[0]) - lo[u]) / GRID))
        j0 = max(0, int((min(pa[1], pb[1], pc[1]) - lo[v]) / GRID))
        j1 = min(nv - 1, int((max(pa[1], pb[1], pc[1]) - lo[v]) / GRID))
        d = (pb[1] - pc[1]) * (pa[0] - pc[0]) + (pc[0] - pb[0]) * (pa[1] - pc[1])
        if abs(d) < 1e-9:
            continue
        for i in range(i0, i1 + 1):
            x = lo[u] + (i + 0.5) * GRID
            for j in range(j0, j1 + 1):
                if cov[i][j]:
                    continue
                y = lo[v] + (j + 0.5) * GRID
                w1 = ((pb[1] - pc[1]) * (x - pc[0]) + (pc[0] - pb[0]) * (y - pc[1])) / d
                w2 = ((pc[1] - pa[1]) * (x - pc[0]) + (pa[0] - pc[0]) * (y - pc[1])) / d
                if w1 >= -1e-6 and w2 >= -1e-6 and w1 + w2 <= 1 + 1e-6:
                    cov[i][j] = True
    seen = [[False] * nv for _ in range(nu)]
    regions = []
    for i in range(nu):
        for j in range(nv):
            if cov[i][j] or seen[i][j]:
                continue
            stack, cells = [(i, j)], []
            seen[i][j] = True
            while stack:
                p, q = stack.pop()
                cells.append((p, q))
                for dp, dq in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    a2, b2 = p + dp, q + dq
                    if 0 <= a2 < nu and 0 <= b2 < nv and not cov[a2][b2] and not seen[a2][b2]:
                        seen[a2][b2] = True
                        stack.append((a2, b2))
            area = len(cells) * GRID * GRID
            if area < 400:   # under 20 x 20 cm: seams, not openings
                continue
            pmin, pmax = min(c[0] for c in cells), max(c[0] for c in cells)
            qmin, qmax = min(c[1] for c in cells), max(c[1] for c in cells)
            touches = [s for s, hit in (("-" + AX[u], pmin == 0), ("+" + AX[u], pmax == nu - 1),
                                        ("-" + AX[v], qmin == 0), ("+" + AX[v], qmax == nv - 1)) if hit]
            mn, mx = [0, 0, 0], [0, 0, 0]
            mn[u], mx[u] = lo[u] + pmin * GRID, lo[u] + (pmax + 1) * GRID
            mn[v], mx[v] = lo[v] + qmin * GRID, lo[v] + (qmax + 1) * GRID
            mn[thin], mx[thin] = lo[thin], hi[thin]
            regions.append({"min": [r(x) for x in mn], "max": [r(x) for x in mx], "area_m2": r(area / 1e4, 2),
                            "fill": r(area / ((mx[u] - mn[u]) * (mx[v] - mn[v])), 2), "touches": touches})
    regions.sort(key=lambda q: -q["area_m2"])
    return {"plane": AX[u] + AX[v], "through": AX[thin], "grid_cm": GRID, "regions": regions[:6]}


def measure(path):
    mesh = unreal.load_asset(path)
    if mesh is None or not isinstance(mesh, unreal.StaticMesh):
        return {"error": "not found"}
    bb = mesh.get_bounding_box()
    lo, hi = [bb.min.x, bb.min.y, bb.min.z], [bb.max.x, bb.max.y, bb.max.z]
    ext = [hi[i] - lo[i] for i in range(3)]
    e = {"bounds_min": [r(x) for x in lo], "bounds_max": [r(x) for x in hi], "size": [r(x) for x in ext],
         "pivot": pivot_note(lo, hi), "extends": extends(lo, hi), "long_axis": AX[max(range(3), key=lambda i: ext[i])],
         "thin_axis": AX[min(range(3), key=lambda i: ext[i])]}
    slots = []
    for i, sm in enumerate(mesh.static_materials):
        mi = sm.material_interface
        slots.append({"index": i, "name": str(sm.material_slot_name), "material": mi.get_path_name().split(".")[0] if mi else None,
                      "blend": base_flag(mi, "blend_mode") if mi else None,
                      "two_sided": base_flag(mi, "two_sided") if mi else None,
                      "params": params(mi) if mi else None})
    e["slots"] = slots
    lods = []
    try:
        for l in range(mesh.get_num_lods()):
            lods.append({"tris": mesh.get_num_triangles(l), "verts": mesh.get_num_vertices(l)})
    except Exception as ex:
        lods = "n/a (%s)" % ex
    e["lods"] = lods
    nan = get(mesh, "nanite_settings")
    e["nanite"] = bool(get(nan, "enabled")) if nan is not None else None
    e["lightmap"] = {"coord": get(mesh, "light_map_coordinate_index"), "res": get(mesh, "light_map_resolution")}
    e["collision"] = collision(mesh)
    e["sockets"] = [{"name": str(get(s, "socket_name")), "loc": vec(get(s, "relative_location")),
                     "rot": [r(get(s, "relative_rotation").pitch), r(get(s, "relative_rotation").yaw),
                             r(get(s, "relative_rotation").roll)]} for s in (get(mesh, "sockets") or [])]
    try:
        e.update(tri_pass(mesh, lo, hi, path in OPENINGS, path in PROFILE))
        share = e.pop("group_area_share", {})
        for s in slots:   # polygon group n is assumed to be material slot n (true for these imports)
            s["area_share"] = share.get(str(s["index"]))
    except Exception as ex:
        e["tri_pass_error"] = str(ex)
    return e


def pack_of(path):
    p = path.strip("/").split("/")
    if p[0] == "Engine":
        return "Engine"
    if p[1] == "Megapack" and len(p) > 3:
        return "Megapack_" + p[3]
    return p[1]


os.makedirs(OUT, exist_ok=True)
index, packs = {}, {}
for path in MESHES:
    try:
        e = measure(path)
    except Exception as ex:
        e = {"error": str(ex)}
    e["pack"] = pack_of(path)
    index[path] = e
    packs.setdefault(e["pack"], {})[path] = e
    log("%s %s size %s pivot %s tris %s coll %s open %s" % (
        "OK " if "error" not in e else "ERR", path.split("/")[-1], e.get("size"), e.get("pivot"), e.get("tris_lod0"),
        (e.get("collision") or {}).get("type"), e.get("open_faces")))
for name, d in packs.items():
    with open(os.path.join(OUT, name + ".json"), "w") as f:
        json.dump(d, f, indent=1)
with open(os.path.join(OUT, "index.json"), "w") as f:
    json.dump({"units": "cm, local, unscaled", "source": "Tools/AssetGen/measure_ue.py", "meshes": index}, f, indent=1)
log("wrote %d meshes in %d packs to %s" % (len(index), len(packs), OUT))
