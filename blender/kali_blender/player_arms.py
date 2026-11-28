"""SK_PlayerArms: first-person forearms + fists that hold the equipped tool on ToolHolder.

Rig `PlayerArmsRig` (pre-rotated +90 deg X like Anim_PlayerToolSwing, so every rest frame is identity in
Unity) placed at the camera's ToolSocket:
    PlayerArmsRig > ToolHolder            same bone + same SerokanScoop / GancoHookSwing keys as Anim_PlayerToolSwing
                    ToolHolder > R_Hand, L_Hand   fists, fixed on the tool grip (+Z-head tools: right hand at the
                                                  grip, left hand 0.42 m up the shaft)
                    R_Arm, L_Arm                  forearm + rolled sleeve, re-aimed every frame from the wrist
                                                  toward a fixed shoulder point below the camera (off screen)
Takes: Idle_Hold (2 s loop), SerokanScoop, GancoHookSwing.
"""
import math

import bpy  # noqa: F401
from mathutils import Matrix, Vector

from . import rigging_common as rc
from . import tool_swing as T

NAME = "SK_PlayerArms"
RIG_NAME = "PlayerArmsRig"
FBX_PATH = rc.FBX_DIR + "/SK_PlayerArms.fbx"
BLEND_PATH = "blender/SK_PlayerArms.blend"
PALETTE_PNG = rc.TEX_DIR + "/T_PlayerArms_Palette.png"
MATERIAL = "M_PlayerArms_Palette"
TRI_BUDGET = (800, 1500)
PALETTE = rc.Palette([
    ("skin", "#C98B5F"), ("skin_dark", "#A86F49"), ("nail", "#E2B08A"), ("sleeve", "#F97316"),
    ("sleeve_dark", "#C2410C"), ("cuff", "#FDBA74"),
])
IDLE_FRAMES = 60
TAKES = {"Idle_Hold": IDLE_FRAMES, **T.TAKES}
LEFT_ON_SHAFT = 0.42                     # metres up the tool shaft from the grip
# shoulder points in ToolSocket space (Unity metres): camera-space (+-0.22, -0.30, -0.05) minus the socket
ANCHOR_U = {"R": (0.22 - T.SOCKET_IN_CAMERA[0], -0.30 - T.SOCKET_IN_CAMERA[1], -0.05 - T.SOCKET_IN_CAMERA[2]),
            "L": (-0.22 - T.SOCKET_IN_CAMERA[0], -0.30 - T.SOCKET_IN_CAMERA[1], -0.05 - T.SOCKET_IN_CAMERA[2])}
ARM_LEN = 0.90
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
IDLE_KEYS = [(0, (0, 0, 0), (0, 0, 0)), (30, (0.004, 0.010, 0.0), (-2.0, 1.0, 1.0)), (60, (0, 0, 0), (0, 0, 0))]


def _holder_world(pos, euler):
    return T.unity_bone_world(pos, euler)            # rig root = identity in Unity, at the socket


def _tool_frame():
    """Rest tool frame (Blender world): grip at origin, shaft along its +Z column."""
    return T.tool_world(_holder_world((0, 0, 0), (0, 0, 0)))


def _anchor(side):
    return rc.unity_to_blender_vec(ANCHOR_U[side])


def _hand_geom(mb, side, tool, grip_z, bone):
    """Fist wrapped around the shaft. Built in the tool frame then moved to world. Returns the wrist point."""
    m3 = tool.to_3x3()
    origin = tool.translation + m3 @ Vector((0, 0, grip_z))
    shaft = m3 @ Z
    to_sh = _anchor(side) - origin
    wdir = -(to_sh - shaft * to_sh.dot(shaft)).normalized()      # knuckles point away from the shoulder
    back = wdir.cross(shaft)
    if back.dot(_anchor(side) - origin) < 0:                      # back of the hand faces the camera side
        back = -back
    W = {bone: 1.0}
    # palm block (shaft runs through the base of the fingers)
    c = origin + back * 0.030 - wdir * 0.012
    rows = [(-0.046, 0.034, 0.016), (-0.040, 0.044, 0.022), (0.0, 0.048, 0.024), (0.040, 0.044, 0.022), (0.046, 0.034, 0.016)]
    rings = [rc.ring(c + shaft * dz, shaft, wdir, a, back, b, 10, 3.0) for dz, a, b in rows]
    mb.loft(rings, [W] * 5, ["skin"] * 4, cap0="skin", cap1="skin")
    # four fingers curling round the far side of the shaft, one thumb over the top
    def arc(z, r_tube, a0, a1, rad, n, col, tip):
        pts = []
        for k in range(n):
            t = a0 + (a1 - a0) * k / (n - 1)
            pts.append(origin + shaft * z + (back * math.cos(t) + wdir * math.sin(t)) * rad)
        rr = []
        for k, p in enumerate(pts):
            d = (pts[min(k + 1, n - 1)] - pts[max(k - 1, 0)]).normalized()
            e1 = shaft - d * shaft.dot(d)
            rr.append(rc.ring(p, d, e1.normalized(), r_tube * (1 - 0.15 * k / n), d.cross(e1).normalized(),
                              r_tube * 0.9 * (1 - 0.15 * k / n), 6))
        mb.loft(rr, [W] * n, ["skin"] * (n - 2) + [tip], cap1=tip)
    for i, z in enumerate((-0.033, -0.011, 0.011, 0.033)):
        arc(z, 0.0105 - 0.001 * abs(i - 1.5), math.radians(70), math.radians(255), 0.029, 5, "skin", "nail")
    arc(0.050, 0.011, math.radians(20), math.radians(-150), 0.026, 4, "skin", "nail")
    return origin + back * 0.034 - wdir * 0.058


def _arm_geom(mb, side, wrist, bone, hand_bone):
    a = (_anchor(side) - wrist).normalized()
    e1 = Z.cross(a).normalized()
    e2 = a.cross(e1)
    rows = [  # distance from wrist, half sizes, band colour, weights
        (-0.010, 0.026, 0.022, "skin", {hand_bone: 0.5, bone: 0.5}),
        (0.05, 0.031, 0.026, "skin", {bone: 1.0}),
        (0.18, 0.037, 0.032, "skin", {bone: 1.0}),
        (0.29, 0.040, 0.035, "cuff", {bone: 1.0}),
        (0.295, 0.050, 0.046, "sleeve", {bone: 1.0}),
        (0.350, 0.051, 0.047, "sleeve_dark", {bone: 1.0}),
        (0.356, 0.048, 0.044, "sleeve", {bone: 1.0}),
        (ARM_LEN, 0.060, 0.055, None, {bone: 1.0}),
    ]
    rings = [rc.ring(wrist + a * t, a, e1, r1, e2, r2, 12, 2.0) for t, r1, r2, _c, _w in rows]
    mb.loft(rings, [r[4] for r in rows], [r[3] for r in rows[:-1]], cap0="skin", cap1="sleeve_dark")


def _bones_world():
    """Rest bones in world space: (name, head, tail, parent)."""
    tool = _tool_frame()
    shaft = tool.to_3x3() @ Z
    out = [("ToolHolder", Vector((0, 0, 0)), Vector((0, 0, 0.15)), None)]
    for side, gz in (("R", 0.0), ("L", LEFT_ON_SHAFT)):
        grip = tool.translation + shaft * gz
        out.append((f"{side}_Hand", grip, grip + shaft * 0.08, "ToolHolder"))
    return out


def build(material):
    """Rig + skinned mesh at rest. Returns (rig, mesh)."""
    rig_inv = T.RIG_MATRIX.inverted()
    tool = _tool_frame()
    mb = rc.MeshBuilder(PALETTE)
    wrists = {}
    for side, gz in (("R", 0.0), ("L", LEFT_ON_SHAFT)):
        wrists[side] = _hand_geom(mb, side, tool, gz, f"{side}_Hand")
        _arm_geom(mb, side, wrists[side], f"{side}_Arm", f"{side}_Hand")
    bones = [(n, rig_inv @ h, rig_inv @ t, p, True) for n, h, t, p in _bones_world()]
    for side in ("R", "L"):
        w = wrists[side]
        bones.append((f"{side}_Arm", rig_inv @ w, rig_inv @ (w + (_anchor(side) - w).normalized() * 0.3), None, True))
    rig = rc.build_armature(RIG_NAME, bones, matrix_world=T.RIG_MATRIX)
    mesh = mb.build(NAME, material, [b[0] for b in bones])
    mesh.parent = rig
    mesh.matrix_parent_inverse = rig.matrix_world.inverted()
    mod = mesh.modifiers.new("Armature", "ARMATURE")
    mod.object = rig
    return rig, mesh


def pose_at(rig, keys, f):
    """ToolHolder from Unity-space keys; hands ride on it; arms re-aimed from the moved wrists."""
    v = rc.hermite_keys([(t, tuple(p) + tuple(e)) for t, p, e in keys], f)
    hw = _holder_world(v[:3], v[3:])
    out = {}
    arm_inv = rig.matrix_world.inverted()
    b = rig.data.bones["ToolHolder"]
    basis = b.matrix_local.inverted() @ (arm_inv @ hw)
    out["ToolHolder"] = (basis.to_quaternion(), basis.translation.copy())
    rest_hw = _holder_world((0, 0, 0), (0, 0, 0))
    delta = hw @ rest_hw.inverted()
    for side in ("R", "L"):
        out[f"{side}_Hand"] = ((1, 0, 0, 0), None)           # fixed on the holder
        ab = rig.data.bones[f"{side}_Arm"]
        rest_w = rig.matrix_world @ ab.matrix_local
        wrist = delta @ rest_w.translation
        new_dir = (_anchor(side) - wrist).normalized()
        r3 = rest_w.to_3x3()
        rot = r3.col[1].rotation_difference(new_dir).to_matrix() @ r3
        m = rot.to_4x4()
        m.translation = wrist
        basis = ab.matrix_local.inverted() @ (arm_inv @ m)
        out[f"{side}_Arm"] = (basis.to_quaternion(), basis.translation.copy())
    return out


def build_actions(rig):
    rc.key_action(rig, "Idle_Hold", IDLE_FRAMES, lambda f: pose_at(rig, IDLE_KEYS, f))
    for take in T.TAKES:
        rc.key_action(rig, take, T.TAKES[take], lambda f, k=T.KEYS[take]: pose_at(rig, k, f))
