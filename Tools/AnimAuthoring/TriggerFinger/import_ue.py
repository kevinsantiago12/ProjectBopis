"""Headless Unreal import of the two trigger-finger poses (new assets: safe with the editor open), checked
against MM_Rifle_Idle_Hipfire's frame 0: every bone but the index finger should match."""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import project as P  # noqa: E402  (puts ../lib on the path)
import uelib as U  # noqa: E402
import unreal  # noqa: E402

FINGER = ["index_01_r", "index_02_r", "index_03_r"]
CHECK = ["pelvis", "spine_05", "clavicle_r", "upperarm_r", "lowerarm_r", "hand_r", "index_metacarpal_r",
         "middle_01_r", "thumb_02_r", "hand_l", "ik_hand_gun", "ik_hand_l"]


def body(info):
    U.use_legacy_fbx_import()
    clip = unreal.load_asset(P.CLIP_PATH)
    for name in ["TriggerRestPose", "TriggerPressPose"]:
        seq = U.import_anim(os.path.join(P.DIR, name + ".fbx"), P.DEST, name, P.SKELETON)
        r = {"path": U.path_of(seq)}
        U.attempt(r, "frames", lambda: unreal.AnimationLibrary.get_num_frames(seq))
        U.attempt(r, "length", lambda: seq.get_play_length())
        U.attempt(r, "unchanged_worst", lambda: U.worst(U.compare(clip, seq, CHECK, [0.0])))
        U.attempt(r, "finger_diff", lambda: U.compare(clip, seq, FINGER, [0.0]))
        info[name] = r


U.run("TRIGGER", os.path.join(P.DIR, "import_result.json"), body)
