"""Anim_PlayerToolSwing: first-person tool swing clips for a ToolHolder under the Main Camera.

FBX = one armature `ToolSwingRig` with a single bone `ToolHolder`, two takes. The armature object
is rotated +90 deg about X (and the bone lies along its local +Y), which cancels the -Z forward /
Y up conversion: in Unity the rig root and ToolHolder have identity rest transforms, and the clips
animate ToolHolder's localPosition / localRotation in camera space (x right, y up, z forward).
Keys below are authored in that Unity space (metres, Unity Euler degrees).
"""
import math

import bpy  # noqa: F401
from mathutils import Matrix, Vector

from . import rigging_common as rc

NAME = "Anim_PlayerToolSwing"
RIG_NAME = "ToolSwingRig"
BONE = "ToolHolder"
FBX_PATH = rc.FBX_DIR + "/Anim_PlayerToolSwing.fbx"
BLEND_PATH = "blender/Anim_PlayerToolSwing.blend"
RIG_MATRIX = Matrix.Rotation(math.radians(90), 4, "X")
S_FLIP = Matrix(((-1, 0, 0), (0, 1, 0), (0, 0, 1)))

# (frame, (pos x, y, z), (euler x, y, z)) in Unity camera space. +X euler = pitch down.
KEYS = {
    "SerokanScoop": [          # 0.8 s: dip the net forward-down, drag, lift it out
        (0, (0, 0, 0), (0, 0, 0)),
        (5, (0, 0.04, -0.06), (-10, 0, 0)),
        (12, (0, -0.12, 0.18), (48, 3, -4)),
        (15, (-0.02, -0.14, 0.12), (52, 4, -6)),
        (20, (0, 0.06, -0.04), (-22, 0, 2)),
        (24, (0, 0, 0), (0, 0, 0)),
    ],
    "GancoHookSwing": [        # 0.7 s: raise overhead, strike forward-down, yank back
        (0, (0, 0, 0), (0, 0, 0)),
        (6, (-0.05, 0.22, -0.10), (-55, 0, 10)),
        (10, (-0.02, -0.10, 0.22), (50, -2, -6)),
        (12, (-0.02, -0.12, 0.24), (53, -2, -6)),
        (17, (0.02, -0.06, -0.14), (35, 0, 0)),
        (21, (0, 0, 0), (0, 0, 0)),
    ],
}
TAKES = {name: keys[-1][0] for name, keys in KEYS.items()}
# KaliPlayerController parents +Z-head tools with this localRotation (kept under ToolHolder).
TOOL_LOCAL_EULER = (65, -8, 0)
SOCKET_IN_CAMERA = (0.38, -0.32, 0.65)


def unity_bone_world(pos, euler):
    """Unity local (pos, Euler) of ToolHolder -> Blender world matrix of the bone."""
    # Unity reads a bone node as F * W * S (axis map F, right->left handed flip S on the local axes).
    m = (rc._F.inverted() @ rc.unity_euler_matrix(euler) @ S_FLIP).to_4x4()
    m.translation = rc.unity_to_blender_vec(pos)
    return m


def tool_world(holder_world, euler=TOOL_LOCAL_EULER):
    """World matrix of a tool mesh (Blender data, grip at origin) parented under ToolHolder in Unity."""
    m = (holder_world.to_3x3() @ S_FLIP @ rc.unity_euler_matrix(euler) @ rc._F).to_4x4()
    m.translation = holder_world.translation
    return m


def build_rig():
    return rc.build_armature(RIG_NAME, [(BONE, (0, 0, 0), (0, 0.15, 0), None, True)], matrix_world=RIG_MATRIX)


def pose_at(arm, take, f):
    keys = [(t, tuple(p) + tuple(e)) for t, p, e in KEYS[take]]
    v = rc.hermite_keys(keys, f)
    m = arm.matrix_world.inverted() @ unity_bone_world(v[:3], v[3:])
    basis = arm.data.bones[BONE].matrix_local.inverted() @ m
    return {BONE: (basis.to_quaternion(), basis.translation.copy())}


def build_actions(arm):
    for take, frames in TAKES.items():
        rc.key_action(arm, take, frames, lambda f, t=take: pose_at(arm, t, f))
