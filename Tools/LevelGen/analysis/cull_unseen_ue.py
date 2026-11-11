"""Run it in a windowless FULL editor, not RunUnreal.ps1: a commandlet world has no physics, so no trace hits anything (2026-11-09).
  & "C:/Program Files/Epic Games/UE_5.8/Engine/Binaries/Win64/UnrealEditor.exe" "<project>/ProjectBopis.uproject"
    -ExecutePythonScript="<project>/Tools/LevelGen/analysis/cull_unseen_ue.py" -nullrhi -unattended -nosplash -nop4 -NoSound -abslog="<log>"
It never saves; it quits when done (~11 min for Lvl_01_Slum). Removing what it lists is a separate step (the bridge, by object name).

Headless, READ-ONLY (never saves): which static meshes in Lvl_01_Slum can be seen in gameplay (user 2026-11-09: "If you cant see it in
gameplay, remove it from the level").

1. Where the player can be: nav-mesh points on a 2.5 m grid, every layer, that a path joins to a seed. Seeds: the layout's areas (each
   room and street, by section and floor) and the player start. Unjoined nav (the closed houses' roofs, ground outside the level) isn't.
2. Where the camera can be: from each point, the camera pivot (1.66 m up) and the camera at arm length (3 m, 0.5 m right) for 4 yaws at
   pitch 0 and -70 (up to ~4.5 m high), pulled in where the arm hits something, as the spring arm does.
3. Pass A: 160 rays from every camera; whatever a ray hits first is seen.
4. Pass B, for the rest (and everything without collision, which rays can't hit): lines from cameras within 50 m to points 4 cm outside
   each face of its bounds (centres, corners, a grid on big faces). Any line that gets there clear, or reaches the piece, means seen.
Occluders are collision (complex). See-through things don't occlude: windows' glass planes and blockers, hidden pieces, doors, anything
movable. Kept whatever the result: hidden or not-in-game pieces (they're invisible on purpose), anything that isn't a StaticMeshActor,
and unseen pieces that block pawns within 50 cm of the walkable area (they may be what stops the player).
Writes Saved/LinearSlums/vis_report.json."""
import json
import math
import time
import unreal

MAP = '/Game/ThirdPerson/Lvl_01_Slum'
LAYOUT = 'C:/Users/kevin/Documents/Unreal Projects/ProjectBopis/Design Document/Linear_Slums_Layout.json'
OUT = 'C:/Users/kevin/Documents/Unreal Projects/ProjectBopis/Saved/LinearSlums/vis_report.json'
ORIGIN = (80.0, 60.0)
SEC_Z = {1: 0.0, 2: 180.0, 3: 0.0, 4: 0.0, 5: 0.0, 6: -180.0, 7: -180.0}
GRID, PIVOT, ARM, RIGHT = 250.0, 166.0, 300.0, 50.0
NRAYS, RAYLEN, PB_RANGE = 160, 8000.0, 5000.0
SEE_THROUGH = ('_WinGlass', '_WinIn', '_Win', 'Grill', 'Jalousie')
T0 = time.time()


def log(s):
    unreal.log('[VIS %5.0fs] %s' % (time.time() - T0, s))


def V(x, y, z):
    return unreal.Vector(x, y, z)


def ue(lx, ly):
    return (ORIGIN[1] - ly) * 100.0, (lx - ORIGIN[0]) * 100.0


def main():
    global world
    unreal.get_editor_subsystem(unreal.LevelEditorSubsystem).load_level(MAP)
    world = unreal.get_editor_subsystem(unreal.UnrealEditorSubsystem).get_editor_world()
    NS = unreal.NavigationSystemV1
    CH = unreal.TraceTypeQuery.TRACE_TYPE_QUERY1        # Visibility


    def trace(a, b):
        """The first blocking hit between a and b: (actor, distance) or None."""
        r = unreal.SystemLibrary.line_trace_single(world, a, b, CH, True, [], unreal.DrawDebugTrace.NONE, True)
        hr = r[1] if isinstance(r, tuple) else r
        if hr is None:
            return None
        t = hr.to_tuple()
        if not t[0]:
            return None
        act = next((x for x in t if isinstance(x, unreal.Actor)), None)
        dist = t[3] if isinstance(t[3], float) else None
        if dist is None:
            loc = next((x for x in t if isinstance(x, unreal.Vector)), None)
            dist = (loc - a).length() if loc is not None else 0.0
        return act, dist


    # --- what's in the level ------------------------------------------------------------------------------------------------------
    pieces, kept_reason, all_actors = {}, {}, unreal.GameplayStatics.get_all_actors_of_class(world, unreal.Actor)
    for a in all_actors:
        cls = a.get_class().get_name()
        lab = a.get_actor_label()
        comps = a.get_components_by_class(unreal.PrimitiveComponent)
        see_through = any(s in lab for s in SEE_THROUGH) or cls not in ('StaticMeshActor',)
        for c in comps:
            hidden = (not c.get_editor_property('visible')) or c.get_editor_property('hidden_in_game')
            movable = c.mobility != unreal.ComponentMobility.STATIC
            if see_through or hidden or movable:
                try:
                    c.set_collision_enabled(unreal.CollisionEnabled.NO_COLLISION)    # not an occluder (never saved)
                except Exception:       # noqa: BLE001
                    pass
        if cls != 'StaticMeshActor':
            continue
        c = a.static_mesh_component
        if c is None or c.static_mesh is None:
            continue
        if (not c.get_editor_property('visible')) or c.get_editor_property('hidden_in_game'):
            kept_reason[a.get_name()] = 'hidden on purpose'
            continue
        if c.mobility != unreal.ComponentMobility.STATIC:
            kept_reason[a.get_name()] = 'movable'
            continue
        o, e, _r = unreal.SystemLibrary.get_component_bounds(c)
        blocks_pawn = c.get_collision_enabled() in (unreal.CollisionEnabled.QUERY_AND_PHYSICS, unreal.CollisionEnabled.PHYSICS_ONLY) and \
            c.get_collision_response_to_channel(unreal.CollisionChannel.ECC_PAWN) == unreal.CollisionResponseType.ECR_BLOCK
        pieces[a.get_name()] = {'a': a, 'label': lab, 'mesh': c.static_mesh.get_name(), 'o': (o.x, o.y, o.z), 'e': (e.x, e.y, e.z),
                                'blocks_pawn': blocks_pawn, 'tags': [str(t) for t in a.get_editor_property('tags')]}
    log('%d static mesh pieces to test, %d kept as they are' % (len(pieces), len(kept_reason)))

    # --- 1. where the player can be ------------------------------------------------------------------------------------------------
    L = json.load(open(LAYOUT, encoding='utf-8'))
    nb = [a for a in all_actors if a.get_class().get_name() == 'NavMeshBoundsVolume'][0]
    bo, be = nb.get_actor_bounds(False)
    ext = V(80.0, 80.0, 120.0)


    def project(p, e=ext):
        try:
            r = NS.project_point_to_navigation(world, p, None, None, e)
        except Exception:       # noqa: BLE001
            return None
        if r is None:
            return None
        q = r[0] if isinstance(r, tuple) else r
        return None if (abs(q.x) < 1e-3 and abs(q.y) < 1e-3 and abs(q.z) < 1e-3) else q


    seeds = []
    ps = [a for a in all_actors if a.get_class().get_name() == 'PlayerStart']
    for a in ps:
        q = project(a.get_actor_location(), V(100, 100, 300))
        if q:
            seeds.append(q)
    for ar in L['areas']:
        cx, cy = (ar['x0'] + ar['x1']) / 2.0, (ar['y0'] + ar['y1']) / 2.0
        X, Y = ue(cx, cy)
        z = SEC_Z.get(ar['sec'], 0.0) + 400.0 * ar['f'] + 60.0
        q = project(V(X, Y, z), V(150, 150, 260))
        if q:
            seeds.append(q)
    log('%d seeds (%d areas)' % (len(seeds), len(L['areas'])))

    pts = {}
    x = bo.x - be.x
    while x <= bo.x + be.x:
        y = bo.y - be.y
        while y <= bo.y + be.y:
            z = bo.z - be.z
            while z <= bo.z + be.z:
                q = project(V(x, y, z))
                if q:
                    pts[(round(q.x / 50), round(q.y / 50), round(q.z / 50))] = q
                z += 200.0
            y += GRID
        x += GRID
    log('%d nav points on the grid' % len(pts))


    def path_ok(a, b):
        try:
            p = NS.find_path_to_location_synchronously(world, a, b)
        except Exception:       # noqa: BLE001
            return False
        if p is None or not p.is_valid() or p.is_partial():
            return False
        pp = p.get_editor_property('path_points')
        return bool(pp) and (pp[-1] - b).length() < 80.0


    reach = []
    for q in pts.values():
        near = sorted(seeds, key=lambda s: (s - q).length())[:3]
        if any(path_ok(s, q) for s in near):
            reach.append(q)
    log('%d reachable points' % len(reach))

    # --- 2. camera positions -------------------------------------------------------------------------------------------------------
    cams = []
    for q in reach:
        piv = V(q.x, q.y, q.z + PIVOT)
        cams.append(piv)
        for yaw in (0.0, 90.0, 180.0, 270.0):
            for pitch in (0.0, -70.0):
                cy_, sy_, cp_, sp_ = math.cos(math.radians(yaw)), math.sin(math.radians(yaw)), math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
                fwd = V(cp_ * cy_, cp_ * sy_, sp_)
                right = V(-sy_, cy_, 0.0)
                want = piv - fwd * ARM + right * RIGHT
                h = trace(piv, want)
                if h:
                    d = (want - piv)
                    n = d.length()
                    want = piv + d * (max(0.0, h[1] - 12.0) / n)
                cams.append(want)
    log('%d cameras' % len(cams))

    # --- 3. pass A: rays ------------------------------------------------------------------------------------------------------------
    dirs = []
    ga = math.pi * (3.0 - math.sqrt(5.0))
    for i in range(NRAYS):
        zz = 1.0 - 2.0 * (i + 0.5) / NRAYS
        r_ = math.sqrt(1.0 - zz * zz)
        dirs.append(V(math.cos(ga * i) * r_, math.sin(ga * i) * r_, zz))
    seen = set()
    for k, cpos in enumerate(cams):
        for d in dirs:
            h = trace(cpos, cpos + d * RAYLEN)
            if h and h[0] is not None:
                seen.add(h[0].get_name())
        if k % 2000 == 0:
            log('pass A %d/%d cameras, %d pieces seen' % (k, len(cams), len(seen & set(pieces))))
    log('pass A done: %d of %d pieces seen' % (len(seen & set(pieces)), len(pieces)))

    # --- 4. pass B: lines to the rest ---------------------------------------------------------------------------------------------------
    cell = 1000.0
    cgrid = {}
    for cpos in cams:
        cgrid.setdefault((int(cpos.x // cell), int(cpos.y // cell)), []).append(cpos)


    def targets(o, e):
        out = []
        for ax in range(3):
            for sgn in (-1.0, 1.0):
                n = [0.0, 0.0, 0.0]
                n[ax] = sgn
                u, w = [i for i in range(3) if i != ax]
                nu, nw = max(1, int(2 * e[u] // 150)), max(1, int(2 * e[w] // 150))
                for iu in range(nu + 1):
                    for iw in range(nw + 1):
                        p = [0.0, 0.0, 0.0]
                        p[ax] = o[ax] + sgn * (e[ax] + 4.0)
                        p[u] = o[u] - e[u] + 2 * e[u] * iu / nu if nu > 0 else o[u]
                        p[w] = o[w] - e[w] + 2 * e[w] * iw / nw if nw > 0 else o[w]
                        out.append((V(*p), n))
        return out


    rest = [n for n in pieces if n not in seen]
    unseen = []
    for k, name in enumerate(rest):
        pc = pieces[name]
        o, e = pc['o'], pc['e']
        tg = targets(o, e)
        gx, gy = int(o[0] // cell), int(o[1] // cell)
        span = int(PB_RANGE // cell) + 1
        near = []
        for ix in range(gx - span, gx + span + 1):
            for iy in range(gy - span, gy + span + 1):
                near.extend(cgrid.get((ix, iy), []))
        near.sort(key=lambda c: (c.x - o[0]) ** 2 + (c.y - o[1]) ** 2 + (c.z - o[2]) ** 2)
        vis = False
        for cpos in near[:900]:
            for p, n in tg:
                if (cpos.x - p.x) * n[0] + (cpos.y - p.y) * n[1] + (cpos.z - p.z) * n[2] <= 0.0:
                    continue        # the camera is behind this face
                h = trace(cpos, p)
                if h is None or (h[0] is not None and h[0].get_name() == name):
                    vis = True
                    break
            if vis:
                break
        if not vis:
            unseen.append(name)
        if k % 500 == 0:
            log('pass B %d/%d, %d unseen so far' % (k, len(rest), len(unseen)))

    # --- 5. keep unseen pawn blockers at the walkable edge -------------------------------------------------------------------------------
    rgrid = {}
    for q in reach:
        rgrid.setdefault((int(q.x // cell), int(q.y // cell)), []).append(q)
    remove, edge = [], []
    for name in unseen:
        pc = pieces[name]
        o, e = pc['o'], pc['e']
        close = False
        if pc['blocks_pawn']:
            gx, gy = int(o[0] // cell), int(o[1] // cell)
            for ix in range(gx - 2, gx + 3):
                for iy in range(gy - 2, gy + 3):
                    for q in rgrid.get((ix, iy), []):
                        dx = max(abs(q.x - o[0]) - e[0], 0.0)
                        dy = max(abs(q.y - o[1]) - e[1], 0.0)
                        dz = max(abs(q.z + 90.0 - o[2]) - e[2] - 90.0, 0.0)
                        if math.sqrt(dx * dx + dy * dy + dz * dz) < 50.0:
                            close = True
                            break
                    if close:
                        break
                if close:
                    break
        (edge if close else remove).append(name)

    rep = {'pieces': len(pieces), 'kept_as_is': len(kept_reason), 'seeds': len(seeds), 'nav_points': len(pts), 'reachable': len(reach),
           'cameras': len(cams), 'seen_pass_a': len(seen & set(pieces)), 'unseen': len(unseen), 'edge_kept': len(edge), 'remove_n': len(remove),
           'remove': [[n, pieces[n]['label'], pieces[n]['mesh'], [round(v) for v in pieces[n]['o']], [round(v) for v in pieces[n]['e']], pieces[n]['tags']] for n in remove],
           'edge': [[n, pieces[n]['label'], pieces[n]['mesh']] for n in edge],
           'cams_sample': [[round(c.x), round(c.y), round(c.z)] for c in cams[::50]],
           'reach_points': [[round(q.x), round(q.y), round(q.z)] for q in reach]}
    json.dump(rep, open(OUT, 'w'), indent=0)
    log('DONE ' + json.dumps({k: v for k, v in rep.items() if not isinstance(v, list)}))


try:
    main()
except Exception as _e:      # noqa: BLE001
    import traceback
    unreal.log_error('[VIS] FAILED ' + traceback.format_exc())
finally:
    unreal.SystemLibrary.quit_editor()
