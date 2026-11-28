"""Ambient NPC takes for SK_VillagerNPC (KaliAmbientNpc roles), baked into the same FBX.

All takes are in place (Root Motion off) at 30 fps and match how KaliNpcBuilder / KaliAmbientNpc place
each role (clip space: root = the NPC GameObject before Ivan's offsets):
  * Seated fisher: root sits 0.42 m below the jetty top -> pelvis / thigh underside at ~0.42 m, thighs flat
    forward, shins hanging past the edge (knees at y = -0.24 m).
  * Crouched washer: root sits 0.215 m below the step -> soles at +0.215 m in clip space (feet planted on
    the step), deep squat, hands scrubbing just in front of the feet.
  * Kids, chatters, standing fisher: soles at 0.
Hands that must hit a point (rod grip, hip, scrub cloth) are solved with a 2-bone IK on the posed chest,
then baked as plain FK keys like the other takes.
"""
import math

import bpy  # noqa: F401
from mathutils import Matrix, Vector

from . import rigging_common as rc
from . import villager as V

TAKES = {
    "Anim_Fisher_SittingCast": 90,      # 3.0 s loop
    "Anim_Fisher_SittingIdle": 90,      # 3.0 s loop
    "Anim_Fisher_StandingIdle": 90,     # 3.0 s loop
    "Anim_Washer_CrouchedScrub": 60,    # 2.0 s loop, 4 scrub strokes
    "Anim_Kid_WadeShallow": 60,         # 2.0 s loop, 2 high steps
    "Anim_Kid_Splash": 40,              # 1.33 s loop, 2 splashes
    "Anim_Kid_JettyJump": 60,           # 2.0 s one-shot, frames 48..60 = holdable surface pose
    "Anim_Chatter_TalkingIdle": 120,    # 4.0 s loop
}
ALL_TAKES = {**V.TAKES, **TAKES}
SEAT_HIP_DROP = -0.025          # thigh underside at ~0.42 m = KaliAmbientNpc SeatedFisher pos.y -= 0.42
WASHER_FEET_Z = 0.215           # = KaliAmbientNpc CrouchedWasher pos.y -= 0.215
ROD_TIP = (0.0, -1.75, 0.0)     # rod tip in the Socket_RightHand frame (Blender); Unity local (0, 0, 1.75)

L1, L2 = V.LEG_L1, V.LEG_L2
Z = Vector((0, 0, 1))


def _upd():
    bpy.context.view_layer.update()


def _apply(arm, pose):
    for b, (q, loc) in pose.items():
        pb = arm.pose.bones[b]
        pb.rotation_quaternion = q
        pb.location = loc if loc is not None else (0, 0, 0)
    _upd()


def _aim(pb, direction):
    m = pb.matrix.copy()
    r = m.to_3x3()
    n = (r.col[1].rotation_difference(direction).to_matrix() @ r).to_4x4()
    n.translation = m.translation
    pb.matrix = n
    _upd()


def ik_arm(arm, side, wrist, hand_dir, palm, pole):
    """2-bone IK on the CURRENT posed chest; returns pose-local quats of UpperArm, LowerArm, Hand.
    wrist / pole in armature space; hand_dir = hand bone direction; palm = palm normal."""
    pbs = arm.pose.bones
    ua, la, h = (pbs[side + n] for n in ("UpperArm", "LowerArm", "Hand"))
    for pb in (ua, la, h):
        pb.rotation_quaternion = (1, 0, 0, 0)
    _upd()
    s0 = ua.head.copy()
    l1, l2 = ua.bone.length, la.bone.length
    w = Vector(wrist)
    d = max(min((w - s0).length, (l1 + l2) * 0.995), abs(l1 - l2) + 0.02)   # clamp out-of-reach targets
    u = (w - s0).normalized()
    w = s0 + u * d
    v = (Vector(pole) - s0) - u * (Vector(pole) - s0).dot(u)
    v.normalize()
    a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
    elbow = s0 + u * a + v * math.sqrt(max(0.0, l1 * l1 - a * a))
    _aim(ua, elbow - s0)
    _aim(la, w - la.head)
    m = h.matrix.copy()
    r = m.to_3x3()
    palm_local = h.bone.matrix_local.to_3x3().inverted() @ Vector((0, 0, -1))   # rest palm faces -Z
    rot = V._basis(Vector(hand_dir), Vector(palm)) @ V._basis(r.col[1], r @ palm_local).transposed()
    n = (rot @ r).to_4x4()
    n.translation = m.translation
    h.matrix = n
    _upd()
    return {pb.name: (pb.rotation_quaternion.copy(), None) for pb in (ua, la, h)}


def _rod_hand_dir(side, rod_dir, palm):
    """Fist direction for a rod held across the palm (thumb side points along the rod)."""
    t, n = Vector(rod_dir).normalized(), Vector(palm).normalized()
    return n.cross(t) if side == "Right" else t.cross(n)


def _pose(arm, rots, dz, ik=()):
    """FK body from `rots` (armature-axis Euler), then IK arms: ik = [(side, wrist, hand_dir, palm, pole_offset)]."""
    pose = V._to_pose(arm, rots, hips_dz=dz)
    if not ik:
        return pose
    _apply(arm, pose)
    for side, wrist, hand_dir, palm, pole in ik:
        s0 = arm.pose.bones[side + "UpperArm"].head
        pose.update(ik_arm(arm, side, wrist, hand_dir, palm, s0 + Vector(pole)))
    return pose


def _legs(r, thigh, knee, foot, side=None, splay=0.0):
    for S, s in V.SIDES:
        if side in (None, S):
            r[S + "UpperLeg"] = (thigh, 0, splay * s)
            r[S + "LowerLeg"] = (knee, 0, 0)
            r[S + "Foot"] = (foot, 0, 0)


def _squat_dz(a, feet_z=0.0):
    return -(L1 + L2) * (1 - math.cos(math.radians(a))) + feet_z


def _cyc(f, n):
    return 2 * math.pi * f / n


def _unit(*v):
    return Vector(v).normalized()


# ---------------------------------------------------------------- fishers
def _seated(r, ph):
    _legs(r, -86, 86, 14, splay=6)
    r["LeftLowerLeg"] = (86 + 7 * math.sin(ph), 0, 0)          # dangling, out of phase
    r["RightLowerLeg"] = (86 + 7 * math.sin(ph + 2.1), 0, 0)
    r["Hips"] = (-4, 0, 0)
    r["Spine"] = (10 + 0.6 * math.sin(ph), 0, 0)
    r["Chest"] = (6 - 1.2 * math.sin(ph), 0, 0)
    return SEAT_HIP_DROP


LAP_LEFT = ("Left", (0.13, -0.22, 0.66), _unit(0, -1, -0.25), (0, 0, -1), (0.30, 0.15, -0.25))


def sitting_idle(arm, f):
    n = TAKES["Anim_Fisher_SittingIdle"]
    ph = _cyc(f, n)
    r = {}
    dz = _seated(r, ph)
    r["Neck"] = (4, 0, 0)
    r["Head"] = (10 + 2 * math.sin(2 * ph), 0, 8 * math.sin(ph))
    rod = _unit(0, -0.89, 0.45 + 0.03 * math.sin(3 * ph))
    wrist = (-0.13, -0.24, 0.67 + 0.006 * math.sin(2 * ph))
    palm = (1, 0, 0)
    return _pose(arm, r, dz, [("Right", wrist, _rod_hand_dir("Right", rod, palm), palm, (-0.30, 0.15, -0.25)), LAP_LEFT])


CAST_KEYS = [  # frame, rod direction, right wrist
    (0, (0, -0.89, 0.45), (-0.13, -0.24, 0.67)),
    (22, (0, -0.88, 0.47), (-0.13, -0.24, 0.68)),
    (34, (0, 0.30, 0.95), (-0.22, -0.06, 1.02)),      # wind up: rod back over the shoulder
    (40, (0, -0.94, 0.34), (-0.14, -0.30, 0.76)),     # flick forward
    (48, (0, -0.97, 0.22), (-0.13, -0.28, 0.66)),     # follow through, rod low over the water
    (62, (0, -0.90, 0.43), (-0.13, -0.24, 0.67)),
    (90, (0, -0.89, 0.45), (-0.13, -0.24, 0.67)),
]


def sitting_cast(arm, f):
    n = TAKES["Anim_Fisher_SittingCast"]
    ph = _cyc(f, n)
    r = {}
    dz = _seated(r, ph)
    v = rc.hermite_keys([(t, tuple(rd) + tuple(w)) for t, rd, w in CAST_KEYS], f)
    lift = max(0.0, min(1.0, (v[5] - 0.67) / 0.35))                  # body follows the wind-up
    r["Chest"] = (r["Chest"][0] - 8 * lift, 0, -10 * lift)
    r["Neck"] = (4, 0, 0)
    r["Head"] = (10 - 8 * lift, 0, 4 * math.sin(ph))
    palm = (1, 0, 0)
    return _pose(arm, r, dz, [("Right", v[3:], _rod_hand_dir("Right", v[:3], palm), palm, (-0.30, 0.15, -0.25)), LAP_LEFT])


AKIMBO_LEFT = ("Left", (0.20, 0.03, 0.66), _unit(-0.2, 0.35, -1), (-1, 0, 0), (0.35, 0.10, 0.0))


def standing_idle(arm, f):
    n = TAKES["Anim_Fisher_StandingIdle"]
    ph = _cyc(f, n)
    s = math.sin(ph)
    r = V._relaxed()
    r["Hips"] = (0, 2.0 * s, 1.5 * math.sin(ph + 0.5))
    for S in ("Left", "Right"):
        r[S + "UpperLeg"] = (0, -2.0 * s, -1.5 * math.sin(ph + 0.5))
    r["Spine"] = (2, -1.0 * s, 0)
    r["Chest"] = (-1.2 * math.sin(2 * ph), -0.6 * s, 0)
    r["Head"] = (6 + 1.5 * math.sin(2 * ph), 0.8 * s, 6 * math.sin(ph + 1.0))
    rod = _unit(0, -0.85, 0.53 + 0.04 * math.sin(2 * ph))
    palm = (1, 0, 0)
    wrist = (-0.14, -0.17, 0.72 + 0.008 * math.sin(2 * ph))
    return _pose(arm, r, 0.0, [("Right", wrist, _rod_hand_dir("Right", rod, palm), palm, (-0.30, 0.10, -0.25)), AKIMBO_LEFT])


# ---------------------------------------------------------------- washer
def crouched_scrub(arm, f):
    n = TAKES["Anim_Washer_CrouchedScrub"]
    ph = _cyc(f, n)
    stroke = math.sin(4 * ph)                       # 4 strokes per loop
    a = 75
    r = {}
    _legs(r, -a, 2 * a, -a, splay=18)
    dz = _squat_dz(a, WASHER_FEET_Z) + 0.006 * abs(stroke)
    r["Hips"] = (4, 0, 1.5 * math.sin(ph))
    r["Spine"] = (30 + 1.5 * stroke, 0, 2 * stroke)
    r["Chest"] = (25, 0, 3 * stroke)
    r["Neck"] = (-8, 0, 0)
    r["Head"] = (-14 + 2 * math.sin(2 * ph), 0, 3 * math.sin(ph))
    palm = (0, 0, -1)
    hd = _unit(0, -1, -0.5)
    ik = [("Left", (0.07, -0.40 + 0.05 * stroke, 0.36), hd, palm, (0.30, 0.10, 0.0)),
          ("Right", (-0.07, -0.40 - 0.05 * stroke, 0.36), hd, palm, (-0.30, 0.10, 0.0))]
    return _pose(arm, r, dz, ik)


# ---------------------------------------------------------------- kids
def wade_shallow(arm, f):
    n = TAKES["Anim_Kid_WadeShallow"]
    ph = _cyc(f, n)
    r = {}
    for S, off in (("Left", 0.0), ("Right", math.pi)):
        lift = max(0.0, math.sin(ph + off)) ** 1.3
        r[S + "UpperLeg"] = (-52 * lift, 0, 0)
        r[S + "LowerLeg"] = (78 * lift, 0, 0)
        r[S + "Foot"] = (-12 * lift, 0, 0)
    roll = 3 * math.sin(ph)                         # lean over the stance leg
    r["Hips"] = (0, roll, -4 * math.sin(ph))
    r["LeftUpperLeg"] = (r["LeftUpperLeg"][0], -roll, 4 * math.sin(ph))
    r["RightUpperLeg"] = (r["RightUpperLeg"][0], -roll, 4 * math.sin(ph))
    r["Spine"] = (7, -roll * 0.6, 3 * math.sin(ph))
    r["Chest"] = (2 + 1.5 * math.sin(2 * ph), 0, 2 * math.sin(ph))
    r["Head"] = (6 - 2 * math.sin(2 * ph), 0, -4 * math.sin(ph))
    for S, s in V.SIDES:                            # arms held out for balance, swinging against the legs
        sw = 14 * math.sin(ph) * s
        r[S + "UpperArm"] = V._mirror((sw - 8, 48, 0)) if s < 0 else (sw - 8, 48, 0)
        r[S + "LowerArm"] = V._mirror((0, 0, -30)) if s < 0 else (0, 0, -30)
        r[S + "Hand"] = V._mirror((0, 0, -10)) if s < 0 else (0, 0, -10)
    return _pose(arm, r, 0.0)


SPLASH_KEYS = [  # frame in a 20-frame splash, wrist (left side, mirrored), hand dir, palm normal, hips dz
    (0, (0.17, -0.22, 0.66), (0, -1, -0.2), (0, 0.2, -1), 0.0),
    (7, (0.15, -0.30, 0.52), (0, -1, -0.6), (0, 0, -1), -0.03),   # slap the water
    (11, (0.20, -0.32, 0.92), (0, -0.6, 0.8), (0, -0.8, -0.5), 0.01),  # fling it up and forward
    (20, (0.17, -0.22, 0.66), (0, -1, -0.2), (0, 0.2, -1), 0.0),
]


def splash(arm, f):
    n = TAKES["Anim_Kid_Splash"]
    k = f % 20
    v = rc.hermite_keys([(t, tuple(w) + tuple(d) + tuple(p) + (z,)) for t, w, d, p, z in SPLASH_KEYS], k)
    a = 18
    r = {}
    _legs(r, -a, 2 * a, -a, splay=10)
    big = 1.0 if f < 20 else 1.25                   # second splash a bit wilder
    slap, fling = max(0.0, -v[-1]) / 0.03, max(0.0, v[-1]) / 0.01
    r["Spine"] = (18 + 8 * slap * big - 6 * fling, 0, 4 * math.sin(_cyc(f, n)))
    r["Chest"] = (8, 0, 0)
    r["Head"] = (-6 + 6 * slap - 10 * fling, 0, 5 * math.sin(_cyc(f, n)))
    dz = _squat_dz(a) + v[-1] * big
    ik = []
    for S, s, pole in (("Left", 1, (0.30, 0.10, -0.1)), ("Right", -1, (-0.30, 0.10, -0.1))):
        w = (v[0] * s, v[1], v[2])
        hd = (v[3] * s, v[4], v[5])
        palm = (v[6] * s, v[7], v[8])
        ik.append((S, w, Vector(hd).normalized(), Vector(palm).normalized(), pole))
    return _pose(arm, r, dz, ik)


def _jump_keys():
    base = V._relaxed()

    def k(dz=0.0, **bones):
        r = dict(base)
        for name, val in bones.items():
            if name.startswith("L_"):
                r["Left" + name[2:]] = val
                r["Right" + name[2:]] = V._mirror(val)
            else:
                r[name] = val
        return r, dz

    def run(lead):     # lead = side whose thigh is forward
        o = "Right" if lead == "Left" else "Left"
        r, _ = k(Spine=(10, 0, 0), Head=(-6, 0, 0))
        r[lead + "UpperLeg"], r[lead + "LowerLeg"], r[lead + "Foot"] = (-38, 0, 0), (62, 0, 0), (-10, 0, 0)
        r[o + "UpperLeg"], r[o + "LowerLeg"], r[o + "Foot"] = (12, 0, 0), (16, 0, 0), (8, 0, 0)
        for S, sgn in ((lead, -1), (o, 1)):          # opposite arm forward
            left = (sgn * 38, 62, 0)
            r[S + "UpperArm"] = left if S == "Left" else V._mirror(left)
            r[S + "LowerArm"] = (0, 0, -70) if S == "Left" else (0, 0, 70)
        return r, _squat_dz(12)

    crouch, _ = k(Spine=(24, 0, 0), Chest=(8, 0, 0), Head=(-14, 0, 0),
                  L_UpperArm=(55, 58, 0), L_LowerArm=(0, 0, -15))
    _legs(crouch, -36, 72, -36)
    keys = [
        (0, k()),
        (4, run("Left")), (8, run("Right")), (12, run("Left")), (16, run("Right")),
        (21, (crouch, _squat_dz(36))),
        (26, k(0.05, Spine=(-6, 0, 0), Head=(-10, 0, 0), L_UpperArm=(-155, 35, 0), L_LowerArm=(0, 0, -10))),
        (33, None),     # tuck, filled below
        (42, k(0.0, Spine=(2, 0, 0), Head=(-4, 0, 0), L_UpperArm=(-168, 22, 0), L_LowerArm=(0, 0, -5))),
        (48, None),     # surface
        (54, None),
        (60, None),
    ]
    tuck, _ = k(Spine=(26, 0, 0), Chest=(10, 0, 0), Head=(-12, 0, 0),
                L_UpperArm=(-62, 62, 0), L_LowerArm=(0, 0, -60))
    _legs(tuck, -82, 112, -20)
    keys[7] = (33, (tuck, 0.12))

    def surface(paddle):
        r, _ = k(Spine=(-4, 0, 0), Head=(-12, 0, 4 * paddle),
                 L_UpperArm=(-10 * paddle, 18, 0), L_LowerArm=(0, 0, -22))
        _legs(r, -28, 44, 12, splay=10)
        r["LeftUpperLeg"] = (-28 - 8 * paddle, 0, 10)
        r["RightUpperLeg"] = (-28 + 8 * paddle, 0, -10)
        return r, -0.04
    keys[9], keys[10], keys[11] = (48, surface(1)), (54, surface(-1)), (60, surface(1))
    return keys


def jetty_jump(arm, f, _keys=[]):
    if not _keys:
        _keys.extend(_jump_keys())
    names = V.DEFORM_BONES
    flat = [(t, tuple(c for b in names for c in r.get(b, (0, 0, 0))) + (dz,)) for t, (r, dz) in _keys]
    v = rc.hermite_keys(flat, f)
    return _pose(arm, {b: v[3 * i:3 * i + 3] for i, b in enumerate(names)}, v[-1])


# ---------------------------------------------------------------- chatter
TALK_KEYS = [  # frame, RightUpperArm, RightLowerArm, RightHand (right-side Euler, armature axes)
    (0, (-4, -68, 0), (0, 0, 12), (0, 0, 4)),
    (18, (-35, -62, 0), (0, 0, 85), (-50, 0, 0)),
    (28, (-30, -62, 0), (0, 0, 98), (-50, 0, 10)),
    (38, (-38, -60, -5), (0, 0, 80), (-55, 0, -5)),
    (55, (-10, -68, 0), (0, 0, 30), (-10, 0, 0)),
    (72, (-25, -48, -25), (0, 0, 70), (-60, 0, 0)),
    (84, (-28, -50, -20), (0, 0, 88), (-60, 0, 8)),
    (98, (-15, -62, -5), (0, 0, 40), (-20, 0, 0)),
    (120, (-4, -68, 0), (0, 0, 12), (0, 0, 4)),
]


def talking_idle(arm, f):
    n = TAKES["Anim_Chatter_TalkingIdle"]
    ph = _cyc(f, n)
    s = math.sin(ph)
    r = V._relaxed()
    r["Hips"] = (0, 1.8 * s, 2 * math.sin(ph + 0.4))
    for S in ("Left", "Right"):
        r[S + "UpperLeg"] = (0, -1.8 * s, -2 * math.sin(ph + 0.4))
    v = rc.hermite_keys([(t, ua + la + h) for t, ua, la, h in TALK_KEYS], f)
    r["RightUpperArm"], r["RightLowerArm"], r["RightHand"] = v[0:3], v[3:6], v[6:9]
    talk = max(0.0, min(1.0, (v[5] - 12) / 60))     # how animated the speaker is right now
    r["Spine"] = (1, -0.8 * s, -3 * talk)
    r["Chest"] = (-1.0 * math.sin(2 * ph), 0, -3 * talk)
    r["Neck"] = (2, 0, 0)
    r["Head"] = (3 + 5 * talk * math.sin(8 * ph), 3 * math.sin(2 * ph) * talk, 7 * math.sin(ph))
    return _pose(arm, r, 0.0, [AKIMBO_LEFT])


POSE_FNS = {
    "Anim_Fisher_SittingCast": sitting_cast,
    "Anim_Fisher_SittingIdle": sitting_idle,
    "Anim_Fisher_StandingIdle": standing_idle,
    "Anim_Washer_CrouchedScrub": crouched_scrub,
    "Anim_Kid_WadeShallow": wade_shallow,
    "Anim_Kid_Splash": splash,
    "Anim_Kid_JettyJump": jetty_jump,
    "Anim_Chatter_TalkingIdle": talking_idle,
}


def build_actions(arm):
    for take, frames in TAKES.items():
        rc.key_action(arm, take, frames, lambda f, fn=POSE_FNS[take]: fn(arm, f))


def build_rod(material):
    """SM_Villager_FishingRod: bamboo pole, origin = grip (Socket_RightHand), runs along -Y (Unity +Z)."""
    mb = rc.MeshBuilder(V.PALETTE)
    rows = [(0.30, 0.016), (0.06, 0.016), (-0.06, 0.015), (-0.60, 0.011), (-1.20, 0.008), (-1.75, 0.004)]
    rings = [rc.ring((0, y, 0), Vector((0, -1, 0)), Vector((1, 0, 0)), r, Z, r, 6) for y, r in rows]
    mb.loft(rings, [{}] * len(rows), ["straw_dark", "bag_knot", "straw", "straw_dark", "straw"],
            cap0="straw_dark", cap1="straw_dark")
    return mb.build(V.PROP_ROD, material, None)
