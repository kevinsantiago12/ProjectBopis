# Pass `walls`, run by gen_level.py in the level's shared namespace (see levels/*.py for the order).
# Walls: the Favela tile kit (tiles, doors, windows, grilles, bands, trims), corner rules and columns, wall runs per
# storey on every side that shows, lids and cores.
# Split out of the one-file arena generator on 2026-11-08; the code is unchanged.
# --- Walls ----------------------------------------------------------------------------------------------------------
# Favela kit (user 2026-11-03: "Favela walls, 4 m storeys"; patterns in Tools/LevelGen/LESSONS.md). A storey is a 3 m
# wall tile, a 1 m concrete band (the floor beam, or the parapet on the top storey) and a trim over the seam between
# them, with a second trim capping the top. Tiles are 2.25 m (half 1.125 m), stretched to fit each run exactly, as
# Favela does. Shop fronts on B2 keep the AsiaSlum pieces (3 m modules, 4 m tall).
# User 2026-11-03: "use mostly the concrete material"; "red brick walls... need to be non-red hollow blocks".
# Our materials (Tools/LevelGen/create_materials_ue.py) swap Favela's red brick for MiddleEast's grey blocks.
# User: "Make a CHB material" -> M_BackAlleys_CHB (Tools/LevelGen/create_chb_material_ue.py): procedural 40 x 20 cm
# hollow blocks in world space, optionally under a chipped concrete or paint render. All ours, no pack materials.
# Picked once per block face (see favela_run): mostly concrete, some bare hollow block, a few paint accents.
# Picked per block face and storey (see the block loop). User 2026-11-03: "make more variant colors of
# MI_BackAlleys_CHB" -> concrete still leads (0.5), bare blocks 0.15, and 13 paint colours share 0.35.
PAINTS = ["White", "Yellow", "Blue", "Mint", "Pink", "SkyBlue", "Cream", "Peach", "Lime", "Lavender", "Teal", "Salmon",
          "PaleYellow"]
FACE_MATS = ([(BM + "MI_BackAlleys_CHB_Concrete", 0.24), (BM + "MI_BackAlleys_Concrete", 0.1),
              (BM + "MI_BackAlleys_CHB_ConcreteWarm", 0.08), (BM + "MI_BackAlleys_CHB_ConcreteDark", 0.08),
              (BM + "MI_BackAlleys_CHB_Bare", 0.07), (BM + "MI_BackAlleys_CHB_BareLight", 0.04),
              (BM + "MI_BackAlleys_CHB_BareDark", 0.04)] +
             [(BM + "MI_BackAlleys_CHB_Paint" + c, 0.35 / len(PAINTS)) for c in PAINTS])
SAME_AS_GROUND = 0.4      # chance an upper storey keeps the ground floor's material
# User 2026-11-03: "remove the material variation I asked you to do earlier" - asked which, "All of it: one material".
# Every wall face and storey uses WALL_MAT; the picks above still run (so the random sequence, and with it the window
# layout, stays the same) but their result is replaced. Set ONE_MATERIAL = False to bring the variation back.
ONE_MATERIAL = True
WALL_MAT = BM + "MI_BackAlleys_CHB_Concrete"
# Hollow blocks. User 2026-11-03: "only use them on walls with no windows or doors. They are not to be used for whole
# houses", "the only mixing rule is not to mix on the same face", and "make it 30% of windowless faces, following the
# rules still". A face is one side of a house, all its storeys, with its balcony strip's same side. A face with no door or
# window anywhere is hollow blocks P_HOLLOW of the time (see the pass before the chunks); everything else is WALL_MAT.
# Neighbouring faces may differ. Replaces the per-face-and-storey mixes and the per-house rule of the same day. Bands,
# parapets and columns stay concrete. Its own random sequence, so windows and doors don't move. (The texture sits on the
# Favela tiles' UV0, so it stretches with tile X scale.)
HOLLOW = BM + "MI_BackAlleys_HollowBlocks"
P_HOLLOW = 0.30
WALL_MIX_RNG = random.Random(107)   # 16 of 52 windowless faces (of seeds tried, the closest to 30%)
PLAIN_WALL = ("SM_Wall_Tile_01", "SM_Wall_Tile_Blue", "SM_Wall_Tile_03", "SM_Wall_14", "SM_MainBorder_04")
# Paint. User 2026-11-04: "One color per house, but some side can remain unpainted". P_PAINTED of the houses take one
# colour (MI_BackAlleys_PaintedWall_*, world-mapped, from the AssetGen thread). A face with a door or window always takes
# it; a windowless one takes it P_PAINT_SIDE of the time; hollow-block faces stay as they are. A face never mixes. Bands
# match the paint (user: "when the face is painted, the band looks off if left unpainted. It works for hollow blocks but
# not for painted"; P_BAND_CONTRAST, once 0.2 for variety, is off). Parapets follow
# their face, and a corner column takes the colour when both its faces have it. The door end walls, trims and timber
# don't change. The drip decals stay, over the paint.
PAINT_COLOURS = ("White", "Cream", "Yellow", "Peach", "Salmon", "Pink", "Mint", "AppleGreen", "SkyBlue", "Teal",
                 "Lavender", "Terracotta")
P_PAINTED, P_PAINT_SIDE = 0.5, 0.5
P_BAND_CONTRAST = 0.0
BAND_MIX_RNG = random.Random(137)
PAINT_RNG = random.Random(103)    # 21 of 41 houses (of seeds tried, the closest to half)
CONC = BM + "MI_BackAlleys_Concrete"
DOORS = [(FV + "SM_Door_01", FM + "MI_Door_01"), (FV + "SM_Door_01_Blue", FM + "MI_Door_Blue_01"),
         (FV + "SM_Door_01_Green", FM + "MI_Door_Green_01")]
# The user's five back-alley door textures (create_doors_ue.py), on planes in the wall door slots. Own random sequence.
PLANE_DOORS = ["MI_BackAlleys_Door_" + k for k in
               ("RoughTimber", "GreenPlywood", "BluePlywood", "CorrugatedMetal", "PaintedSteel")]
DOOR_RNG = random.Random(61)
# AsiaSlum steel doors fitted to the slot: local bounds (analysis/door_bounds_ue.py) and whether to turn them 180 so the
# hinges end up on the right seen from the alley ("right hand open") and inside ("make sure the hinges are on the
# inside"). B_003 (louvred, alone) already shows its hinges on the right; the grilles A_002/A_004/A_005 go in front of
# a plane door ("use that along with the metal doors in asian slums like so" ... "for doors 2 4 and 5").
STEEL_DOORS = {"SM_HouseDoor_B_003": ((-112.6, -8.9, 0.0), (2.3, 3.6, 228.0), False),
               "SM_HouseDoor_A_002": ((-114.2, -10.2, 5.2), (1.8, 4.2, 240.5), True),
               "SM_HouseDoor_A_004": ((-114.2, -10.2, 5.2), (1.8, 4.9, 240.5), True),
               "SM_HouseDoor_A_005": ((-160.0, -10.2, 0.0), (2.5, 4.9, 329.6), True)}
GRILLES = ["SM_HouseDoor_A_002", "SM_HouseDoor_A_004", "SM_HouseDoor_A_005"]
P_GRILLE = 0.5                                           # share of plane doors behind a grille
PLANE_HINGE_RIGHT = True                                 # the textures paint the hinges on the left: mirror them
TILE_W, HALF_W = 225.0, 112.5
TILE_LAP = 0.4                                              # cm; more than the plan's rounding, under 1 cm (check_overlaps)
HALF_MAX = 170.0                                            # narrower than this: the half tile, stretched
P_GROUND = {"door": 0.12, "window": 0.25}   # Favela: 12% doors, 9% windows; user 2026-11-03 "increase the number of windows"
P_UPPER = {"window": 0.40}                  # Favela 13%, raised (same request); no doors without a balcony
SPECIAL = getattr(LEVEL, "SPECIAL", {})   # arena: B2's AsiaSlum shop fronts
DECK_FACE = getattr(LEVEL, "DECK_FACE", None)               # arena: doors and windows onto the gallery deck, alternating
DOOR_FRAMES = ("SM_HouseWallDoorFrmae_A_001", "SM_HouseWallDoorFrmae_A_002")
DECALS = {"grime": [FM + "Decals/MI_Decal_02", FM + "Decals/MI_Decal_05", FM + "Decals/MI_Decal_08"],
          "dirt": [FM + "Decals/MI_Decal_Dirt_06", FM + "Decals/MI_Decal_Dirt_08"]}
DECAL_CAP = 200
BLK = "BackAlleys/Blocks"
ground_pieces, upper_runs, exposed_sides, wall_tiles = [], [], {}, []
wall_runs = []   # every visible wall run per storey: start (UE), length cm, side, base z; the stain decals cover these


def pick(weighted):
    r, acc = rnd.random(), 0.0
    if ONE_MATERIAL and weighted is FACE_MATS:
        return WALL_MAT                    # hollow blocks are chosen after the walls are built
    for v, w in weighted:
        acc += w
        if r < acc:
            return v
    return weighted[-1][0]


def at(px, py, side, s, n):
    """World point s cm along a piece's run and n cm along its outward normal."""
    (rx, ry), (nx, ny) = RUN[side], NORMAL[side]
    return px + rx * s + nx * n, py + ry * s + ny * n


def door_for(label, mesh, px, py, z, normal, folder):
    if mesh in DOOR_FRAMES:  # the AsiaSlum pack's own offset: frame-local (205, 5, 0)
        x, y = at(px, py, normal, 205, 5)
        put(label + "_Door", AS + "SM_HouseDoor_B_003", x, y, z, YAW[normal], folder=folder)   # (user: replaces A_004)


THIN_IDS = getattr(LEVEL, "THIN_IDS", ())   # arena: B10, the 1.5 m stub


def thin(b):
    if b.get("balcony"):
        return False   # a balcony strip's street wall keeps its doors and windows
    return min(b["x1"] - b["x0"], b["y1"] - b["y0"]) <= 1.5 or b["id"] in THIN_IDS


def fit(length_cm):
    """Half-tile count and stretch for a run: the count whose stretch is closest to 1 (Favela uses 0.82-1.29)."""
    u = length_cm / HALF_W
    h = min((k for k in (math.floor(u), math.ceil(u)) if k >= 1), key=lambda k: abs(math.log(u / k)))
    return h, u / h


# Window style per house (user 2026-11-03: "you can also use the old window as well, but make sure they are consistent
# house wise. IE all jalouse or all pull windows"): each block - its balcony/terrace strip ("<id>b") included - gets
# either the jalousie plane or Favela's SM_windows_02 insert on every window. Own random sequence, so nothing else moves.
WINDOW_JALOUSIE_SHARE = 0.5
WINDOW_RNG = random.Random(53)
_window_styles = {}



# Window grilles on the ground floor. User 2026-11-04: "find an appropriate window grill and put it in the first floor
# windows", "more variation is appreciated". One kind per house, so neighbours differ and a house matches itself. Fitted to
# the opening (112 x 128 cm, x the tile's stretch, centred 112 along and 156 up) with 5 cm on the wall around it, just off
# the face. Mesh: (local min, local max, the local axis it runs along, depth cm). No collision: they're thin and cheap.
WIN_GRILLES = {FV + "SM_Window_Frame_02": ((-109.9, -7.5, 0.0), (0.0, 0.0, 159.8), "x", 8.0),      # green steel bars
               ME + "MiddleEast/SM_Windows_grill_01": ((-0.5, 0.0, -0.5), (313.8, 11.6, 238.1), "x", 8.0),   # olive bars
               ME + "MiddleEast/SM_Windows_grill_02": ((-0.5, 0.0, -0.5), (313.8, 11.6, 238.1), "x", 8.0),   # dark grid
               ME + "MiddleEast/SM_metal_fence_01": ((5.6, -133.5, -0.5), (11.6, 0.5, 117.0), "y", 6.0),     # sparse bars
               AS + "SM_SecurityWinodw_A_001": ((-106.1, 2.7, -93.0), (106.1, 40.6, 93.2), "x", 14.0)}       # rusty, on brackets
_draw_grille = shuffle_bag(random.Random(127), sorted(WIN_GRILLES))
GRILLE_W, GRILLE_H, GRILLE_Z, GRILLE_OUT = 122.0, 138.0, 87.0, 0.5
BAND_OUT = 15.0
BAND_RNG = random.Random(131)
_house_grilles = {}


def window_grille(label, px, py, z, side, sx, folder):
    house = label.split("_")[0]
    house = house[:-1] if house.endswith("b") and house[:-1] in BLOCKS else house
    if house not in _house_grilles:                # a bag: a plain random pick came out 15 / 10 / 7 / 3 / 2
        _house_grilles[house] = _draw_grille()
    mesh = _house_grilles[house]
    (x0, y0, z0), (x1, y1, z1), axis, depth = WIN_GRILLES[mesh]
    w, s0 = GRILLE_W * sx, (112.0 - GRILLE_W / 2) * sx
    sz = GRILLE_H / (z1 - z0)
    if axis == "x":                                # local X along the run, local +Y outward
        sa, sd = w / (x1 - x0), depth / (y1 - y0)
        x, y = at(px, py, side, s0 - x0 * sa, GRILLE_OUT - y0 * sd)
        yaw_, scale = YAW[side], (sa, sd, sz)
    else:                                          # local Y along the run, local X inward (turned 90 less, as the bands)
        sa, sd = w / (y1 - y0), depth / (x1 - x0)
        x, y = at(px, py, side, s0 - y0 * sa, GRILLE_OUT + x1 * sd)
        yaw_, scale = YAW[side] - 90, (sd, sa, sz)
    put(label + "_Grill", mesh, x, y, z + GRILLE_Z - z0 * sz, yaw_, scale, folder=folder, nocoll=True)


def window_style(label):
    house = label.split("_")[0].rstrip("b")
    if house not in _window_styles:
        _window_styles[house] = "jalousie" if WINDOW_RNG.random() < WINDOW_JALOUSIE_SHARE else "insert"
    return _window_styles[house]


def steel_door(label, mesh, px, py, z, side, sx, front, folder):
    """An AsiaSlum steel door scaled to the Favela door slot (110 x 218 cm x the tile's stretch, centred 111 cm along),
    its front face `front` cm into the wall. Pivots sit at a bottom corner with the mesh along local -X and the outer
    face on local +Y. Turned ones (user 2026-11-03: "Turn the grilles", hinges to the inside) spin 180 and mirror
    along the run, so the hinges move to the inside face but stay on the right (right-hand). Returns the back face depth."""
    (x0, y0, z0), (x1, y1, z1), turn = STEEL_DOORS[mesh]
    sdx, sdz = 110.0 * sx / (x1 - x0), 218.0 / (z1 - z0)
    cx, cy, half = (x0 + x1) / 2 * sdx, (y0 + y1) / 2 * sdz, (y1 - y0) / 2 * sdz
    out = -(front + half)                                # bounds centre, outward from the wall face
    s = -1 if turn else 1                                # turned: local +Y points into the wall, local X still along
    x, y = at(px, py, side, 111 * sx - cx, out - s * cy)
    put(label, AS + mesh, x, y, z + 2 - z0 * sdz, YAW[side] + (180 if turn else 0), (s * sdx, sdz, sdz),
        folder=folder)
    return front + 2 * half


def favela_tile(label, kind, mat, px, py, z, side, sx, width, top, folder, t0=0.0, t1=0.0, sh=400.0, cover=0.0,
                j0=None, j1=None):
    """One storey of one tile: wall tile, opening parts, concrete band, trims. Pivot at the run start, bottom.
    t0/t1 lengthen the trims past the tile's start/end (outside corners, see corner_adjust). sh: storey height (cm) -
    the 3 m tile stays, the band above it takes the rest."""
    yaw = YAW[side]
    mesh = {"door": "SM_WallDoor_01", "window": "SM_Wall_Windows_01"}.get(kind) or \
        ("SM_Wall_Tile_03" if width < HALF_MAX else rnd.choice(("SM_Wall_Tile_Blue", "SM_Wall_Tile_01")))
    # SM_Wall_Tile_03 (the half tile) has two material slots; the second showed the pack's brick at corners (user
    # 2026-11-03 screenshot), so every slot gets the face material.
    # Each tile runs TILE_LAP past its slot, under the next one. Since houses left the 1.5 m grid (fractional widths),
    # plan rounding left gaps of up to 0.08 cm between tiles, seen as dark hairlines (user 2026-11-04: "seams on the
    # walls"). Half tile: its mesh is 112.5 wide; this was 113, which left it 0.5 cm short.
    put(label, FV + mesh, px, py, z, yaw, ((width + TILE_LAP) / (HALF_W if width < HALF_MAX else TILE_W), 1, 1),
        folder=folder,
        mats=[mat, mat] if mesh == "SM_Wall_Tile_03" else [mat])
    if kind == "door":
        # User 2026-11-03: "Heres a zip of 5 backalley "plane" doors" ... "get them in the game" (replacing the
        # SM_HouseDoor_B_003 mesh). The opening is what Favela's SM_Door_Jamb_01 filled: 110 x 218 cm (x the tile's
        # stretch), centred 111 cm along - the textures are 1:2 with their own frame, so the plane fills it exactly,
        # 2 cm in like the jalousie windows, set the same way (engine plane, roll +90). One of the five per door.
        rnd.choice(DOORS)                                   # keeps the random sequence (and the layout) as before
        door = DOOR_RNG.choice(PLANE_DOORS + [None])
        # User 2026-11-03: plane doors, some behind an AsiaSlum steel grille (A_002/004/005, the user's screenshot);
        # "you can still use the original door by itself" - None is the louvred SM_HouseDoor_B_003 alone.
        if door is None:
            steel_door(label + "_Door", "SM_HouseDoor_B_003", px, py, z, side, sx, 3.0, folder)
        else:
            depth = 2.0
            if DOOR_RNG.random() < P_GRILLE:
                depth = steel_door(label + "_Grille", DOOR_RNG.choice(GRILLES), px, py, z, side, sx, 2.0, folder) + 1
            x, y = at(px, py, side, 111 * sx, -depth)
            put(label + "_Door", "/Engine/BasicShapes/Plane", x, y, z + 109, yaw,
                ((-1.10 if PLANE_HINGE_RIGHT else 1.10) * sx, 2.18, 1), folder=folder, roll=90.0, mats=[BM + door])
    elif kind == "window":
        # User 2026-11-03: "Heres a Jalouse window texture, can you put it on a plane and use this instead of the mesh
        # window?" - the engine plane (1 x 1 m, facing +Z) with M_BackAlleys_Jalousie, in place of SM_windows_02: the
        # old insert's size (1.10 x 1.33 m) and centre (111 along, 0.9-2.2 m up), set 2 cm into the opening. Roll +90
        # stands it up facing out, so it shows from the alley only (-90 faced it into the wall: the user, "its facing
        # the wrong way", "flip it vertically 180 degrees"; checked in a capture).
        # 2 cm in, nearly flush (user: "push the windows more out, i can see some texture anomalies" - at 9 cm deep the
        # opening's sill showed, and the world-aligned wall material smears on horizontal faces)
        if window_style(label) == "jalousie":
            x, y = at(px, py, side, 111 * sx, -2)
            put(label + "_Win", "/Engine/BasicShapes/Plane", x, y, z + 90 + 66.5, yaw, (1.10 * sx, 1.33, 1),
                folder=folder, roll=90.0, mats=[BM + "MI_BackAlleys_JalousieDouble"])   # user: "Replace with this textures"
        else:   # Favela's own insert, where Favela puts it: 111 along, 11 in, 90 up, turned 180 (its frame covers the sill)
            x, y = at(px, py, side, 111 * sx, -11)
            put(label + "_Win", FV + "SM_windows_02", x, y, z + 90, yaw + 180, (sx, 1, 1), folder=folder,
                mats=[FM + "MI_Window_02", GLASS])
        if z == 0:
            window_grille(label, px, py, z, side, sx, folder)
    # Band: SM_Wall_14 runs along its local +Y with its thickness on local +X, so it turns 90 less than the tile.
    # Plain concrete here; the paint pass may recolour it (see P_BAND_CONTRAST).
    put(label + "_Band", FV + "SM_Wall_14", px, py, z + 300, yaw - 90,
        (1, (width + TILE_LAP) / 200.0, (sh - 300) / 106.0), folder=folder, mats=[CONC])
    items[-1]["band"] = (side, px, py, width, t0, t1, sh)     # for the protruding bands, in the pass before the chunks
    for zz in ((300, sh) if top else (300,)):
        if z + zz + 20 <= cover:   # inside the lower neighbour in front: it would only cross that house's trims
            continue
        # at a junction (see the wall loop): stop 17 cm short if the lower house's walls reach this trim's height
        e0 = t0 if j0 is None else (-17.0 if z + zz - 8 < j0 else 0.0)
        e1 = t1 if j1 is None else (-17.0 if z + zz - 8 < j1 else 0.0)
        x, y = at(px, py, side, -e0, -6)
        put(label + "_Trim%d" % (300 if zz == 300 else 400), FV + "SM_MainBorder_04", x, y, z + zz, yaw,
            ((width + e0 + e1) / 150.0, 1, 1), folder=folder)


COLUMNS = {}   # outside corners: (lx, ly) -> {"dirs": the two outward directions, "spans": [(z0, z1)] it covers}
COLUMN_PROUD = 0.02   # m the column stands out of each face


def solid_z(lx, ly, z1, me):
    """Something stands at (lx, ly) up to at least z1 (cm): the arena edge, or another house that tall."""
    return cover_top(lx, ly, me) >= z1 - 1


def _coplanar_ahead(behind, side, z0, z1, me):
    """At an inside corner, the house ahead (at `behind`, in line behind this face) has its own face on this same line,
    and builds it over part of this storey's height: what stands in front of it is lower than that storey's top. Running
    on 10 cm would lay this wall in that face (2026-11-08, the linear level: a 1-storey strip in front of two houses, and
    houses on different ground). It never happens in the arena (check_overlaps is clean there)."""
    zb = me.get("z", 0.0)
    for h in BLOCKS.values():
        if h is me or not (h["x0"] < behind[0] < h["x1"] and h["y0"] < behind[1] < h["y1"]):
            continue
        line_me = {"north": me["y0"], "south": me["y1"], "west": me["x0"], "east": me["x1"]}[side]
        line_h = {"north": h["y0"], "south": h["y1"], "west": h["x0"], "east": h["x1"]}[side]
        if abs(line_me - line_h) > 0.01:
            return False
        nlx, nly = LNORM[side]
        front = (behind[0] + nlx * 0.1, behind[1] + nly * 0.1)
        c = cover_top(*front, h)                  # from h's base
        hz = h.get("z", 0.0)
        for s2 in range(h["storeys"]):
            a_, b_ = hz + s2 * h["sh"], hz + (s2 + 1) * h["sh"]
            if min(b_, zb + z1) - max(a_, zb + z0) > 1.0 and c < (s2 + 1) * h["sh"] - 1:
                return True
        return False
    return False


def corner_adjust(side, s, end, outward, me, z0, z1):
    """How a run end meets its neighbours, in cm: (shorten the run by, lengthen the trim by).
    Wall pieces are 20 cm thick behind their face, so where two walls meet their end caps would sit in the other
    wall's face and z-fight (user 2026-11-03: "overlapping faces... corners of the buildings").
    - Inside corner (the cell ahead, in front of the face, is solid: a neighbour's wall or the end wall): run on 10 cm
      so the end cap is buried in that wall. The north/south trim stops 7 cm short of the wall ahead, at the front of
      its trim; the east/west trim runs on into the wall.
    - Outside corner (the cell ahead behind the face line is open too): a 20 x 20 cm concrete corner column, 2 cm
      proud of both faces, is recorded in COLUMNS; both runs stop 10 cm inside it, so each face's material ends at
      the column. The east/west trim crosses it to 7 cm past the corner; the north/south trim stops behind.
    - Otherwise a neighbour continues the face in line: nothing.
    Houses (2026-11-03) are off the 1.5 m grid where set back and differ in height, so the probes sit 5 cm off the
    corner and ask whether something stands there up to this piece's top (z1).
    - Diagonal (houses touching at a corner point only): ahead in front is solid but ahead behind is open - an
      outside corner of this house (a column), not an inside one: running on would poke out of its other face.
    - A lower house in line, ahead behind the face: still an outside corner above it, but both trims stop behind the
      column, since that house's trims can sit at the same height."""
    (ex, ey), (ox, oy) = end, outward
    nlx, nly = LNORM[side]
    behind = (ex + ox * 0.05 - nlx * 0.05, ey + oy * 0.05 - nly * 0.05)
    if solid_z(ex + ox * 0.05 + nlx * 0.05, ey + oy * 0.05 + nly * 0.05, z1, me) and solid_z(*behind, z1, me):
        # Both trims stand 7 cm proud, so at an inside corner they'd cross (user: "overlaps happens in the trims as
        # well"): the east/west trim runs into the wall ahead, the north/south one stops at its front.
        if _coplanar_ahead(behind, side, z0, z1, me):
            return 0.0, 0.0                   # the house ahead builds its own face on this line here: meet it flush
        return -10.0, (0.0 if side in ("east", "west") else -17.0)
    if not solid_z(*behind, z1, me):
        # User (screenshot): "This corner pattern is bad". Overlapping the walls 2 cm put one face's material on the
        # other face as a 20 cm strip. A corner column ends both faces cleanly, as on a real CHB house.
        # keyed by corner and its two outward directions: houses of different heights can share a corner point
        key = (round(ex, 3), round(ey, 3), tuple(sorted({(ox, oy), (nlx, nly)})))
        COLUMNS.setdefault(key, {"dirs": set(key[2]), "spans": []})["spans"].append((z0 + ZB, z1 + ZB) if ZB else (z0, z1))
        if side in ("north", "south") or cover_top(*behind, me) > z0 + 1:
            return 10.0, -9.0
        return 10.0, 17.0
    return 0.0, 0.0


def favela_run(bid, b, side, s, start, length_cm, name, face_mat, adj=((0.0, 0.0), (0.0, 0.0)), onto_balcony=False,
               buried=False, cover=0.0, junctions=(None, None)):
    """buried: a lower neighbour hides the bottom of this storey (it only shows above that roof) - plain wall, no
    openings, no stains. cover: the top (cm) of whatever stands in front, for trims hidden under it."""
    (cut0, ext0), (cut1, ext1) = adj
    rx, ry = RUN[side]
    start = (start[0] + rx * cut0, start[1] + ry * cut0)
    length_cm -= cut0 + cut1
    h, sx = fit(length_cm)
    widths = [TILE_W * sx] * (h // 2) + ([HALF_W * sx] if h % 2 else [])
    if not buried:
        wall_runs.append({"start": start, "len": length_cm, "side": side, "z": s * b["sh"] + ZB if ZB else s * b["sh"], "name": name,
                          "widths": widths})
    kinds = []
    for i, w in enumerate(widths):
        if thin(b) or w < HALF_MAX or buried:
            kinds.append("plain")
        elif (bid, side, s) == DECK_FACE or onto_balcony:
            kinds.append("door" if i % 2 == 0 else "window")
        else:
            r = rnd.random()
            p = b.get("p_open", (P_GROUND, P_UPPER))[0 if s == 0 else 1]     # a plain house has its own (levels/*.py)
            prev = kinds[-1] if kinds else None
            k = "plain"
            if r < p.get("door", 0) and prev != "door":
                k = "door"
            elif r < p.get("door", 0) + p.get("window", 0):
                k = "window"
            kinds.append(k)
    full = [i for i, w in enumerate(widths) if w >= HALF_MAX]
    if not thin(b) and not buried and not b.get("plain") and len(full) >= 3 and all(kinds[i] == "plain" for i in full):
        kinds[full[len(full) // 2]] = "window"            # a long blank run gets one window
    # One material for the whole block face, every storey and opening included (user 2026-11-03: "Keep the texturing
    # consistent per block face"). Favela's patchwork (patches, patched-in openings) is off.
    rx, ry = RUN[side]
    off = 0.0
    for i, (w, k) in enumerate(zip(widths, kinds)):
        mat = face_mat
        px, py = start[0] + rx * off, start[1] + ry * off
        label = "%s_%d" % (name, i)
        favela_tile(label, k, mat, px, py, s * b["sh"], side, sx, w, s == b["storeys"] - 1, BLK,
                    ext0 if i == 0 else 0.0, ext1 if i == len(widths) - 1 else 0.0, sh=b["sh"], cover=cover,
                    j0=junctions[0] if i == 0 else None, j1=junctions[1] if i == len(widths) - 1 else None)
        if not thin(b):
            wall_tiles.append({"label": label, "kind": k, "x": px, "y": py, "z": s * b["sh"] + ZB if ZB else s * b["sh"], "side": side, "w": w,
                               "s": s, "top": s == b["storeys"] - 1})
        if s == 0:
            ground_pieces.append((label, k, px, py, side, w))
        off += w


seed = 0
for bid, b in BLOCKS.items():
    ZB = b.get("z", 0.0)
    x0, y0, x1, y1 = b["x0"], b["y0"], b["x1"], b["y1"]
    sides = {"north": ((x0, y0), (x1, y0)), "south": ((x0, y1), (x1, y1)), "west": ((x0, y0), (x0, y1)),
             "east": ((x1, y0), (x1, y1))}
    # One material per block face and storey (user: "Keep the texturing consistent per block face"; "second floor
    # material can differ from ground floor"): an upper storey keeps the one below 40% of the time.
    face_mats = {}
    for side in sides:
        for s in range(b["storeys"]):
            below = face_mats.get((side, s - 1))
            face_mats[(side, s)] = below if below and rnd.random() < SAME_AS_GROUND else pick(FACE_MATS)
    for s in range(b["storeys"]):
        # A storey's wall shows wherever whatever stands outside it is lower than the storey's top; where that neighbour
        # still hides its bottom half metre or more ("buried"), it shows above that roof only and stays plain.
        z0, z1 = s * b["sh"], (s + 1) * b["sh"]
        for side, (p0, p1) in sides.items():
            nlx, nly = LNORM[side]
            length = abs(p1[0] - p0[0]) + abs(p1[1] - p0[1])
            ux, uy = (p1[0] - p0[0]) / length, (p1[1] - p0[1]) / length
            # Neighbouring pieces that both show make one run (two runs meeting in line would each turn a corner
            # there and cross their trims): buried if any of it is, `cover` the lowest roof in front of it.
            # Where a run that shows fully meets one that shows only above a lower roof, the wall is one plane:
            # the two meet flush (a "junction", no corner), and trims at the lower house's height stop short of its
            # wall there (its own trims sit at the same heights).
            runs = []
            for t0, t1, c in side_intervals(b, side, lambda c: c):
                st = "hidden" if c >= z1 - 1 else ("buried" if c > z0 + 50 else "open")
                if st == "hidden":
                    continue
                if runs and abs(runs[-1][1] - t0) < 1e-6 and runs[-1][3] == st:
                    runs[-1][1], runs[-1][2] = t1, min(runs[-1][2], c)
                else:
                    runs.append([t0, t1, c, st])
            for r, (k0, k1, cov, res) in enumerate(runs):
                j_a = max(cov, runs[r - 1][2]) if r > 0 and abs(runs[r - 1][1] - k0) < 1e-6 else None
                j_c = max(cov, runs[r + 1][2]) if r + 1 < len(runs) and abs(runs[r + 1][0] - k1) < 1e-6 else None
                exposed_sides.setdefault(bid, set()).add(side)
                a = (p0[0] + ux * k0, p0[1] + uy * k0)
                c = (p0[0] + ux * k1, p0[1] + uy * k1)
                A, C = ue(*a), ue(*c)
                rx, ry = RUN[side]
                start = A if (C[0] - A[0]) * rx + (C[1] - A[1]) * ry > 0 else C
                n = int(round((k1 - k0) / 1.5))   # 1.5 m cells (the shop row stays on the grid)
                name = "%s_%s%d_%d" % (bid, side[0].upper(), s, r)
                seq = SPECIAL.get((bid, side, s))
                if seq is None:
                    ua = (-ux, -uy)                                   # beyond the a end, and beyond the c end
                    adj_a = (0.0, 0.0) if j_a is not None else corner_adjust(side, s, a, ua, b, z0, z1)
                    adj_c = (0.0, 0.0) if j_c is not None else corner_adjust(side, s, c, (ux, uy), b, z0, z1)
                    mid = ((a[0] + c[0]) / 2 + nlx * 0.75, (a[1] + c[1]) / 2 + nly * 0.75)
                    favela_run(bid, b, side, s, start, (k1 - k0) * 100.0, name, face_mats[(side, s)],
                               (adj_a, adj_c) if start == A else (adj_c, adj_a),
                               onto_balcony=s == 1 and balcony_at(*mid), buried=res == "buried", cover=cov,
                               junctions=(j_a, j_c) if start == A else (j_c, j_a))
                else:   # AsiaSlum shop fronts: 3 m modules and 1.5 m halves fill the run exactly
                    pieces = [("full", i) for i in range(n // 2)] + ([("half", n // 2)] if n % 2 else [])
                    for kind, i in pieces:
                        px, py = start[0] + rx * 300 * i, start[1] + ry * 300 * i
                        if kind == "full":
                            mesh = seq[(i + seed) % len(seq)]
                            label = "%s_%d" % (name, i)
                            put(label, AS + mesh, px, py, s * 400.0, YAW[side], folder=BLK)
                            door_for(label, mesh, px, py, s * 400.0, side, BLK)
                            if s == 0:
                                ground_pieces.append((label, "shop" if mesh == "SM_Shop_A_001" else "asia", px, py,
                                                      side, 300.0))
                        else:
                            put("%s_half" % name, AS + "SM_HouseWall_A_001_HalfA", px, py, s * 400.0, YAW[side],
                                folder=BLK)
                if s == 1 and side in ("south", "east") and n >= 3:
                    upper_runs.append((bid, side, a, c))
                seed += 1


ZB = 0.0
# --- Corner columns at outside corners (see corner_adjust) ----------------------------------------------------------
for k, ((lx, ly, _dirs), col) in enumerate(sorted(COLUMNS.items())):
    (ax, ay), (bx, by) = sorted(col["dirs"])
    dx, dy = ax + bx, ay + by                     # the corner's outward diagonal, e.g. (1, -1)
    xa, xb = sorted((lx - dx * 0.2, lx + dx * COLUMN_PROUD))
    ya, yb = sorted((ly - dy * 0.2, ly + dy * COLUMN_PROUD))
    merged = []                                   # one piece per run of touching storeys
    for z0, z1 in sorted(col["spans"]):
        if merged and z0 <= merged[-1][1] + 1:
            merged[-1][1] = max(merged[-1][1], z1)
        else:
            merged.append([z0, z1])
    for s0, (z0, z1) in enumerate(merged):
        top = z1 + 5 + 2 * (k % 2)                # over the band's top; columns sharing a corner point differ
        X1, Y0 = ue(xa, ya)
        X0, Y1 = ue(xb, yb)
        put("Column_%d_%d" % (k, s0), CUBE, X0, Y0, z0, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, (top - z0) / 100.0),
            folder="BackAlleys/Blocks", mats=[CONC])

# --- Lids, cores, tin roofs on 1-storey blocks ------------------------------------------------------------------------
for bid, b in BLOCKS.items():
    ZB = b.get("z", 0.0)
    x0, y0, x1, y1, st = b["x0"], b["y0"], b["x1"], b["y1"], b["storeys"]
    ex = exposed_sides.get(bid, set())
    inset = 0.3 if thin(b) or min(x1 - x0, y1 - y0) < 4.5 else 1.5
    cx0 = x0 + (inset if "west" in ex else 0)
    cx1 = x1 - (inset if "east" in ex else 0)
    cy0 = y0 + (inset if "north" in ex else 0)
    cy1 = y1 - (inset if "south" in ex else 0)
    # The lid's top sits 5 cm under the parapet band's top, so the two never share a plane.
    # The lid is inset 5 cm, so its sides don't lie in the walls' outer faces.
    top = st * b["sh"]
    for kind, (a0, b0, a1, b1), z, h, mat in (("Lid", (x0 + 0.05, y0 + 0.05, x1 - 0.05, y1 - 0.05), top - 25,
                                               0.2, None),
                                              ("Core", (cx0, cy0, cx1, cy1), 0.0, top / 100.0 - 0.2, "interior")):
        X1, Y0 = ue(a0, b0)
        X0, Y1 = ue(a1, b1)
        terrace_floor = kind == "Lid" and b["roof"] == "terrace" and TERRACES   # plain concrete, UV-mapped
        put("%s_%s" % (kind, bid), CUBE, X0, Y0, z, 0, ((X1 - X0) / 100.0, (Y1 - Y0) / 100.0, h),
            folder="BackAlleys/Lids", mat=mat, mats=[FM + "MI_Concrete_01"] if terrace_floor else None)
    if st == 1 and not TERRACES:   # tin sheets on top (seen from the deck): SM_MetalPlate_C_001 is 2 x 3 m, pivot at its min corner
        w, d = x1 - x0, y1 - y0
        nx_, ny_ = max(1, math.ceil(w / 2.0)), max(1, math.ceil(d / 3.0))
        for i in range(nx_):
            for j in range(ny_):
                X1, Y0 = ue(x0 + i * w / nx_, y0 + j * d / ny_)
                # sheet local x -> UE X (north), local y -> UE Y (east): its min corner is the SW corner in layout terms
                put("Roof_%s_%d_%d" % (bid, i, j), AS + "SM_MetalPlate_C_001", X1 - (d / ny_) * 100, Y0, 405.0, 0,
                    ((d / ny_) * 100 / 200.0, (w / nx_) * 100 / 300.0, 1), folder="BackAlleys/Lids")
ZB = 0.0   # back to the ground after the per-house loops
