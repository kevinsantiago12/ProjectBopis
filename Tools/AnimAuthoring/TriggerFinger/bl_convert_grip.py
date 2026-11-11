"""Converts the M4's LeftHandGrip socket rotation (on its b_gun_Root) into the AK's b_gun_Root frame, so the
AK's left hand holds the same angle to the gun. Root frames are as read by bl_roots.py (FBX space)."""
import math
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project as P  # noqa: E402,F401  (puts ../lib on the path)
import animlib as A  # noqa: E402
from mathutils import Matrix  # noqa: E402

S = A.S.to_3x3()
ROOT_M4 = Matrix(((1, 0, 0), (0, 0, -1), (0, 1, 0)))
ROOT_AK = Matrix(((0, 0, -1), (-1, 0, 0), (0, 1, 0)))
M4_SOCKET = dict(pitch=13.0, yaw=151.0, roll=-167.0)


def ue_rotator_of(m_ue):
    """An Unreal FRotator (pitch, yaw, roll) from a rotation matrix in Unreal space (FMatrix::Rotator)."""
    x, y, z = m_ue.col[0], m_ue.col[1], m_ue.col[2]
    pitch = math.degrees(math.atan2(x.z, math.hypot(x.x, x.y)))
    yaw = math.degrees(math.atan2(x.y, x.x))
    p, yw = math.radians(pitch), math.radians(yaw)
    sy = (-math.sin(yw), math.cos(yw), 0.0)        # the Y axis of (pitch, yaw, 0)
    roll = math.degrees(math.atan2(z.x * sy[0] + z.y * sy[1] + z.z * sy[2], y.x * sy[0] + y.y * sy[1] + y.z * sy[2]))
    return pitch, yaw, roll


hand = ROOT_M4 @ A.ue_rotator(**M4_SOCKET).to_3x3()           # the hand's angle in component space (FBX)
ak_fbx = ROOT_AK.transposed() @ hand                          # ... in the AK root's frame
ak_ue = S @ ak_fbx @ S
pitch, yaw, roll = ue_rotator_of(ak_ue)
check = ROOT_AK @ A.ue_rotator(pitch, yaw, roll).to_3x3()
print("AK_SOCKET pitch %.2f yaw %.2f roll %.2f   check error %.6f" % (pitch, yaw, roll,
      max(abs(a - b) for ra, rb in zip(check, hand) for a, b in zip(ra, rb))))
