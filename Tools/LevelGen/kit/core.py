"""The level generator's shared kit: asset roots, side tables, vector maths, the shuffle bag, the layout-to-Unreal frame
and the plan writer. Stateless, so any level script or pass can import it. Split out of gen_level.py on 2026-11-08; the
code below the frame is unchanged from the arena generator.

Layout metres: lx east, ly south, from the layout's NW corner. Unreal: X = (oy - ly) * 100, Y = (lx - ox) * 100, where
(ox, oy) is the layout point at the world origin (the level's ORIGIN)."""
import json
import math
import os


def frame(ox, oy):
    """ue(lx, ly) -> Unreal X, Y (cm) and its inverse lay(X, Y) -> layout metres, for a level whose layout point (ox, oy)
    sits at the world origin. The arena's is (27, 24)."""
    def ue(lx, ly):
        return (oy - ly) * 100.0, (lx - ox) * 100.0

    def lay(X, Y):
        return Y / 100.0 + ox, oy - X / 100.0
    return ue, lay


def write_plan(out, prefix, items, gameplay, chunk=140):
    """The plan as <prefix><n>.json chunks of `chunk` items (the bridge's read_file caps at 80 KB) and
    <prefix>gameplay.json. Old chunks with the same prefix are removed first. Returns the number of chunks."""
    os.makedirs(out, exist_ok=True)
    for f in os.listdir(out):
        if f.startswith(prefix):
            os.remove(os.path.join(out, f))
    chunks = [items[i:i + chunk] for i in range(0, len(items), chunk)]
    for i, c in enumerate(chunks):
        json.dump(c, open(os.path.join(out, prefix + "%d.json" % i), "w"), separators=(",", ":"))
    json.dump(gameplay, open(os.path.join(out, prefix + "gameplay.json"), "w"), separators=(",", ":"))
    return len(chunks)


AS, ME, PM = "/Game/AsiaSlum/FBX/", "/Game/Megapack/Meshes/", "/Game/Philippines_Markets/Props/"
CUBE = "/Game/LevelPrototyping/Meshes/SM_Cube"
RAMP = "/Game/LevelPrototyping/Meshes/SM_Ramp"   # min-corner pivot; 1 m tall at local y = 0, falling to 0 at y = 1 m
PK ="/Game/ThirdPerson/Blueprints/Pickups/"

YAW = {"east": 0, "west": 180, "north": -90, "south": 90}
RUN = {"east": (1, 0), "west": (-1, 0), "north": (0, -1), "south": (0, 1)}     # UE
NORMAL = {"east": (0, 1), "west": (0, -1), "north": (1, 0), "south": (-1, 0)}  # UE
LNORM = {"east": (1, 0), "west": (-1, 0), "north": (0, -1), "south": (0, 1)}   # layout
FACING = {"east": 90, "west": -90, "north": 0, "south": 180}
FACE = {"S": "south", "N": "north", "E": "east", "W": "west"}

FV = ME + "Favela/"
FM = "/Game/Megapack/Material/Favela/"
GLASS = "/Game/AsiaSlum/Material/MI_Glass_A_001"           # opaque since 2026-11-02; replaces the additive glass slots

BM = "/Game/ThirdPerson/BackAlleys/Materials/"
PHYS = "/Game/ImpactsVFXVol1/Materials/Physical_Materials/"

def shuffle_bag(rng, options):
    """Draws evenly from options in no fixed order: a shuffled bag, refilled when empty, never the same twice running.
    User 2026-11-04: "we are trying to have patterns in building but have the player not see patterns when playing"."""
    bag, last = [], [None]

    def draw():
        if not bag:
            bag.extend(rng.sample(list(options), len(options)))
            if bag[-1] == last[0]:
                bag[0], bag[-1] = bag[-1], bag[0]
        last[0] = bag.pop()
        return last[0]
    return draw


# Small vector kit for pieces that tilt in more than yaw (UE axes, cm).
def v_add(a, b, k=1.0):
    return (a[0] + k * b[0], a[1] + k * b[1], a[2] + k * b[2])


def v_cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def v_dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def v_rot(v, k, deg):
    """v rotated about the unit axis k (Rodrigues)."""
    c, s = math.cos(math.radians(deg)), math.sin(math.radians(deg))
    kv, kd = v_cross(k, v), v_dot(k, v)
    return tuple(v[i] * c + kv[i] * s + k[i] * kd * (1 - c) for i in range(3))


def ue_dir(a, b):
    """A layout direction (a east, b south) as a UE vector."""
    return (-float(b), float(a), 0.0)


def axes_rot(X, Y, Z):
    """The UE rotator [pitch, yaw, roll] whose local axes are X, Y, Z (FMatrix::Rotator)."""
    pitch = math.atan2(X[2], math.hypot(X[0], X[1]))
    yaw = math.atan2(X[1], X[0])
    sy_ = (-math.sin(yaw), math.cos(yaw), 0.0)     # the Y axis of (pitch, yaw, 0)
    roll = math.atan2(v_dot(Z, sy_), v_dot(Y, sy_))
    return [round(math.degrees(pitch), 3), round(math.degrees(yaw), 3), round(math.degrees(roll), 3)]

