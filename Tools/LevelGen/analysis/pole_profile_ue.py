"""Headless and read-only: where the power poles' crossarms and transformers are, and how the tyre and water meters lie. Vertices of each mesh by height,
with their spread across X and Y in each band, so wires can start at a crossarm and a head can be kept out of a wall.
Run: .\Tools\AnimAuthoring\RunUnreal.ps1 .\Tools\LevelGen\analysis\pole_profile_ue.py"""
import unreal

ME = "/Game/Megapack/Meshes/MiddleEast/"
PM = "/Game/Philippines_Markets/Props/Water_Meters_Set_01/"
for p, step in [(ME + "SM_Electric_Pole_0%d" % i, 40.0) for i in (1, 2, 3, 4)] + [(ME + "SM_wheel_01", 20.0), (PM + "SM_Water_Meter_Single_01", 3.0), (PM + "SM_Water_Meter_Single_02", 3.0)]:
    m = unreal.load_asset(p)
    d = m.get_static_mesh_description(0)
    pts = [d.get_vertex_position(unreal.VertexID(i)) for i in range(d.get_vertex_count())]
    bands = {}
    for v in pts:
        bands.setdefault(int(v.z // step), []).append(v)
    unreal.log_warning("[PROF] %s verts %d" % (p.split("/")[-1], len(pts)))
    for k in sorted(bands):
        vs = bands[k]
        unreal.log_warning("[PROF]   z %6.1f n %4d x %7.1f..%7.1f y %7.1f..%7.1f" % (k * step, len(vs), min(v.x for v in vs), max(v.x for v in vs), min(v.y for v in vs), max(v.y for v in vs)))
# The insulators: where the vertices of each pole's head bunch up, in 20 cm cells across X and Y, by 15 cm of height.
for i in (1, 2, 4):
    p = ME + "SM_Electric_Pole_0%d" % i
    m = unreal.load_asset(p)
    d = m.get_static_mesh_description(0)
    pts = [d.get_vertex_position(unreal.VertexID(k)) for k in range(d.get_vertex_count())]
    for z0 in range(740, 980, 15):
        cells = {}
        for v in pts:
            if z0 <= v.z < z0 + 15:
                cells[int(v.x // 20) * 20] = cells.get(int(v.x // 20) * 20, 0) + 1
        if cells:
            unreal.log_warning("[PROF] head %d z %d: %s" % (i, z0, sorted(cells.items())))
