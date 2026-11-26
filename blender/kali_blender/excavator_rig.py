"""SK_ExcavatorAmfibi armature (rig). All numbers come from excavator_spec.

build_rig() creates the armature object in the current scene and returns it.
Run inside bpy only (import bpy before mathutils, see tools_common.py).
"""
import math

import bpy  # noqa: F401  (must be imported before mathutils in the bpy wheel)
from mathutils import Vector  # noqa: E402

from kali_blender import excavator_spec as S  # noqa: E402

# Pole angle of the arm IK (degrees) that reproduces the rest pose exactly.
# Found by scanning -180..180 deg and refining (see blender/tests/test_excavator_rig.py).
POLE_ANGLE_DEG = -90.0

# Direction of rotation about local X: +1 if a positive pose rotation RAISES the joint's
# absolute angle (guide convention), -1 if it lowers it. Determined empirically.
BOOM_SIGN = -1
STICK_SIGN = -1

CONTROL_BONES = (S.IK_TARGET, S.IK_POLE)


def _pose_range(abs_range_deg, rest_abs_deg, sign):
    """Absolute joint-angle range (deg) -> pose-delta range (rad) about local X."""
    lo, hi = sorted(sign * (a - rest_abs_deg) for a in abs_range_deg)
    return math.radians(lo), math.radians(hi)


def _limit_joint(pb, rng):
    """IK limits + Limit Rotation (local X only) on an arm joint. rng = pose-delta (rad).

    LOCAL space for a bone is relative to its rest pose, so the Limit Rotation range is the
    same pose-delta range as the IK limit (no rest offset).
    """
    lo, hi = rng

    pb.use_ik_limit_x = True
    pb.ik_min_x = lo
    pb.ik_max_x = hi
    pb.lock_ik_y = True
    pb.lock_ik_z = True

    con = pb.constraints.new("LIMIT_ROTATION")
    con.name = "Limit Rotation"
    con.owner_space = "LOCAL"
    con.use_limit_x = True
    con.min_x = lo
    con.max_x = hi
    con.use_limit_y = True
    con.min_y = 0.0
    con.max_y = 0.0
    con.use_limit_z = True
    con.min_z = 0.0
    con.max_z = 0.0


def evaluate(arm_obj):
    """Re-evaluate the rig so pose matrices are settled.

    The Base/Rod Damped Track pairs of each hydraulic cylinder form a depsgraph cycle.
    A single view_layer.update() can leave a Rod aimed at the previous frame's Base
    position (about 7 deg off for B_Piston_Stick_Rod). Tagging the armature and
    updating twice gives the settled, correct pose.
    """
    for _ in range(2):
        arm_obj.update_tag(refresh={"OBJECT"})
        bpy.context.view_layer.update()


def build_rig(pole_angle_deg=POLE_ANGLE_DEG):
    arm_data = bpy.data.armatures.new(S.ARMATURE_NAME)
    obj = bpy.data.objects.new(S.ARMATURE_NAME, arm_data)
    bpy.context.scene.collection.objects.link(obj)
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)

    # ---- bones ----------------------------------------------------------
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = arm_data.edit_bones
    made = {}
    for name, head, tail, _parent, _deform in S.BONES:
        eb = ebs.new(name)
        eb.head = Vector(head)
        eb.tail = Vector(tail)
        eb.roll = 0.0
        eb.use_connect = False
        made[name] = eb
    for name, _head, _tail, parent, deform in S.BONES:
        eb = made[name]
        eb.parent = made[parent] if parent else None
        eb.use_deform = deform
    bpy.ops.object.mode_set(mode="OBJECT")

    # ---- bone collections -----------------------------------------------
    deform_coll = arm_data.collections.new("Deform")
    controls_coll = arm_data.collections.new("Controls")
    for bone in arm_data.bones:
        if bone.use_deform:
            deform_coll.assign(bone)
        if bone.name in CONTROL_BONES:
            controls_coll.assign(bone)

    pose = obj.pose.bones
    for pb in pose:
        pb.rotation_mode = "XYZ"

    # ---- arm IK ----------------------------------------------------------
    stick = pose[S.IK_OWNER]
    ik = stick.constraints.new("IK")
    ik.name = "IK_Bucket"
    ik.target = obj
    ik.subtarget = S.IK_TARGET
    ik.pole_target = obj
    ik.pole_subtarget = S.IK_POLE
    ik.chain_count = S.IK_CHAIN
    ik.use_tail = True
    ik.pole_angle = math.radians(pole_angle_deg)

    # ---- joint limits (guide absolute angles -> pose-delta about local X) --
    _limit_joint(pose["B_Arm_Boom"],
                 _pose_range(S.BOOM_LIMIT_DEG, S.BOOM_REST_DEG, BOOM_SIGN))
    _limit_joint(stick,
                 _pose_range(S.STICK_LIMIT_DEG, S.STICK_REST_DEG - S.BOOM_REST_DEG, STICK_SIGN))

    # ---- keep the animator's target inside the arm's reach ----------------
    # Without this the chain goes straight and the legacy solver flips (see report).
    ctrl = pose[S.IK_TARGET]
    ld = ctrl.constraints.new("LIMIT_DISTANCE")
    ld.name = "Limit Distance"
    ld.target = obj
    ld.subtarget = "B_Arm_Boom"
    ld.head_tail = 0.0
    ld.limit_mode = "LIMITDIST_INSIDE"
    ld.distance = 0.98 * (S.BOOM_LENGTH + S.STICK_LENGTH)
    ld.owner_space = "WORLD"
    ld.target_space = "WORLD"

    # ---- bucket follows the controller ----------------------------------
    bucket = pose["B_Tool_Bucket"]
    cr = bucket.constraints.new("COPY_ROTATION")
    cr.name = "Copy Rotation"
    cr.target = obj
    cr.subtarget = S.IK_TARGET
    cr.target_space = "WORLD"
    cr.owner_space = "WORLD"
    cr.mix_mode = "REPLACE"

    # ---- turret: free spin about world Z only ----------------------------
    turret = pose["B_Turret_Slew"]
    turret.lock_location = (True, True, True)
    turret.lock_rotation = (True, False, True)
    turret.lock_scale = (True, True, True)

    # ---- hydraulic cylinders: Base and Rod aim at each other -------------
    for key in S.PISTONS:
        base_name, rod_name = S.piston_bone_names(key)
        for owner, other in ((base_name, rod_name), (rod_name, base_name)):
            dt = pose[owner].constraints.new("DAMPED_TRACK")
            dt.name = "Damped Track"
            dt.target = obj
            dt.subtarget = other
            dt.track_axis = "TRACK_Y"

    # ---- spud legs: vertical travel along own bone axis only -------------
    for k in S.SPUD_XY:
        pb = pose[f"B_Spud_Leg_{k}"]
        pb.lock_location = (True, False, True)
        pb.lock_rotation = (True, True, True)
        pb.lock_scale = (True, True, True)
        ll = pb.constraints.new("LIMIT_LOCATION")
        ll.name = "Limit Location"
        ll.owner_space = "LOCAL"
        ll.use_min_y = True
        ll.min_y = -S.SPUD_DROP
        ll.use_max_y = True
        ll.max_y = 0.0
        ll.use_transform_limit = True

    bpy.ops.object.select_all(action="DESELECT")
    return obj
