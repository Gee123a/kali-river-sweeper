"""Tests for blender/kali_blender/excavator_rig.py.

Run:  /opt/bpyenv/bin/python blender/tests/test_excavator_rig.py
Prints "ALL RIG TESTS PASSED" and exits 0, or raises AssertionError (non-zero exit).
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))  # blender/

import bpy  # noqa: E402  (must come before mathutils)
from mathutils import Vector  # noqa: E402

from kali_blender import excavator_spec as S  # noqa: E402
from kali_blender import excavator_rig as R  # noqa: E402

MAT_TOL = 1e-3
POS_TOL = 1e-4


def fresh():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    obj = R.build_rig()
    bpy.context.view_layer.update()
    return obj


def upd():
    """Evaluate the rig (re-tagged, settles the Base/Rod Damped Track cycle)."""
    R.evaluate(bpy.data.objects[S.ARMATURE_NAME])


def pb(obj, name):
    return obj.pose.bones[name]


def head(p):
    return p.matrix @ Vector((0.0, 0.0, 0.0))


def tail(p):
    return p.matrix @ Vector((0.0, p.bone.length, 0.0))


def ydir(p):
    return (p.matrix.to_3x3() @ Vector((0.0, 1.0, 0.0))).normalized()


def elev(d):
    """Elevation (deg) of a direction above the horizontal, arm forward = -Y."""
    return math.degrees(math.atan2(d.z, -d.y))


def boom_elev(obj):
    return elev(ydir(pb(obj, "B_Arm_Boom")))


def stick_rel(obj):
    return elev(ydir(pb(obj, S.IK_OWNER))) - boom_elev(obj)


def mats_close(a, b, tol=MAT_TOL):
    return all(abs(a[i][j] - b[i][j]) <= tol for i in range(4) for j in range(4))


def check(cond, msg):
    if not cond:
        raise AssertionError(msg)


def set_ctrl_world_head(obj, target):
    """Move CTRL_IK_Bucket (turret at identity pose) so its world head is `target`."""
    c = pb(obj, S.IK_TARGET)
    rest_rot = c.bone.matrix_local.to_3x3()
    delta = Vector(target) - c.bone.head_local
    c.location = rest_rot.transposed() @ delta
    upd()


def test_structure():
    obj = fresh()
    check(obj.name == S.ARMATURE_NAME, "armature object name")
    check(obj.name in bpy.context.scene.objects, "armature linked to scene")
    check(tuple(obj.location) == (0.0, 0.0, 0.0), "object location")
    check(tuple(obj.rotation_euler) == (0.0, 0.0, 0.0), "object rotation")
    check(tuple(obj.scale) == (1.0, 1.0, 1.0), "object scale")
    arm = obj.data
    check(len(arm.bones) == len(S.BONES), f"bone count {len(arm.bones)} != {len(S.BONES)}")
    for name, h, t, parent, deform in S.BONES:
        b = arm.bones.get(name)
        check(b is not None, f"missing bone {name}")
        check((b.head_local - Vector(h)).length < POS_TOL, f"{name} head")
        check((b.tail_local - Vector(t)).length < POS_TOL, f"{name} tail")
        check((b.parent.name if b.parent else None) == parent, f"{name} parent")
        check(b.use_deform == deform, f"{name} use_deform")
        check(not b.use_connect, f"{name} use_connect")
        check(abs(_roll_of(b)) < 1e-5, f"{name} roll != 0")
    coll = arm.collections
    deform_names = {b.name for b in arm.bones if b.use_deform}
    controls_names = {S.IK_TARGET, S.IK_POLE}
    check({b.name for b in coll["Deform"].bones} == deform_names, "Deform collection members")
    check({b.name for b in coll["Controls"].bones} == controls_names, "Controls collection members")
    print("  structure ok")


def _roll_of(bone):
    """Return 0 if the bone's X axis matches a roll-0 bone with the same head/tail, else 1."""
    tmp = bpy.data.armatures.new("__roll_probe")
    o = bpy.data.objects.new("__roll_probe", tmp)
    bpy.context.scene.collection.objects.link(o)
    bpy.context.view_layer.objects.active = o
    bpy.ops.object.mode_set(mode="EDIT")
    e = tmp.edit_bones.new("p")
    e.head = bone.head_local
    e.tail = bone.tail_local
    e.roll = 0.0
    ref_x = e.matrix.to_3x3().col[0].copy()
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.data.objects.remove(o)
    bpy.data.armatures.remove(tmp)
    diff = (ref_x - bone.matrix_local.to_3x3().col[0]).length
    return 0.0 if diff < 1e-3 else 1.0


def test_rest_pose_unchanged():
    obj = fresh()
    for p in obj.pose.bones:
        check(mats_close(p.matrix, p.bone.matrix_local), f"rest pose changed: {p.name}")
    print("  rest pose ok")


def test_ik_reach():
    obj = fresh()
    turret_rest = pb(obj, "B_Turret_Slew").matrix.copy()
    root_rest = pb(obj, "B_Root_Hull").matrix.copy()
    ctrl_head0 = pb(obj, S.IK_TARGET).bone.head_local.copy()
    target = ctrl_head0 + Vector((0.0, -0.5, -0.8))
    set_ctrl_world_head(obj, target)
    check((head(pb(obj, S.IK_TARGET)) - target).length < POS_TOL, "CTRL head not at target")
    err = (tail(pb(obj, S.IK_OWNER)) - target).length
    check(err < 0.01, f"IK tail error {err:.4f} m")
    check(mats_close(pb(obj, "B_Turret_Slew").matrix, turret_rest), "turret rotated under IK")
    check(mats_close(pb(obj, "B_Root_Hull").matrix, root_rest), "root moved under IK")
    print(f"  IK reach ok (tail error {err:.5f} m)")


def test_turret_slew():
    obj = fresh()
    t = pb(obj, "B_Turret_Slew")
    pivot = t.bone.head_local.copy()
    boom_tail0 = tail(pb(obj, "B_Arm_Boom"))
    t.rotation_euler = (0.0, math.radians(90.0), 0.0)
    upd()
    expected = pivot + Vector((-(boom_tail0 - pivot).y, (boom_tail0 - pivot).x, (boom_tail0 - pivot).z))
    got = tail(pb(obj, "B_Arm_Boom"))
    check((got - expected).length < 1e-3, f"turret 90 deg: got {tuple(got)} expected {tuple(expected)}")
    print("  turret slew ok")


def test_pistons():
    obj = fresh()
    poses = [None,
             (0.0, -5.94, 1.38),
             (0.0, -3.0, 5.0),
             (0.0, -6.5, 3.0)]
    for target in poses:
        if target is not None:
            set_ctrl_world_head(obj, target)
        for key in S.PISTONS:
            base_n, rod_n = S.piston_bone_names(key)
            base, rod = pb(obj, base_n), pb(obj, rod_n)
            bh, rh = head(base), head(rod)
            ang_b = math.degrees(ydir(base).angle(rh - bh))
            ang_r = math.degrees(ydir(rod).angle(bh - rh))
            check(ang_b < 0.5, f"{base_n} aim error {ang_b:.3f} deg at {target}")
            check(ang_r < 0.5, f"{rod_n} aim error {ang_r:.3f} deg at {target}")
            pin = (rh - bh).length
            limit = base.bone.length + rod.bone.length
            check(pin < limit, f"{key} pins {pin:.3f} m apart, bones sum {limit:.3f} m (gap)")
    print("  pistons ok")


def check_pistons(label):
    """Every piston pair aims at the other pin (<0.5 deg) and the bones overlap."""
    for key in S.PISTONS:
        base_n, rod_n = S.piston_bone_names(key)
        base, rod = pb(bpy.data.objects[S.ARMATURE_NAME], base_n), pb(bpy.data.objects[S.ARMATURE_NAME], rod_n)
        bh, rh = head(base), head(rod)
        ang_b = math.degrees(ydir(base).angle(rh - bh))
        ang_r = math.degrees(ydir(rod).angle(bh - rh))
        check(ang_b < 0.5, f"{base_n} aim error {ang_b:.3f} deg at {label}")
        check(ang_r < 0.5, f"{rod_n} aim error {ang_r:.3f} deg at {label}")
        pin = (rh - bh).length
        limit = base.bone.length + rod.bone.length
        check(pin < limit, f"{key} pins {pin:.3f} m apart, bones sum {limit:.3f} m at {label}")


# Controller targets, as world offsets from its rest head, all inside the arm workspace.
IK_WORKSPACE_OFFSETS = [(0.0, -1.5, -1.5), (0.0, 1.0, -1.0), (0.0, -0.5, 1.5),
                        (0.0, 1.5, 0.5), (0.0, -1.0, -2.5)]


def test_joint_limits_ik():
    """IK targets inside the workspace: wrist on target, joint angles in range (+-1 deg),
    piston pairs aligned."""
    obj = fresh()
    b_lo, b_hi = S.BOOM_LIMIT_DEG
    s_lo, s_hi = S.STICK_LIMIT_DEG
    tol = 1.0
    rest = pb(obj, S.IK_TARGET).bone.head_local.copy()
    # Closest wrist position the stick limit allows (stick folded to its minimum angle).
    interior = math.radians(180.0 + s_lo)
    d_min = math.sqrt(S.BOOM_LENGTH ** 2 + S.STICK_LENGTH ** 2
                      - 2.0 * S.BOOM_LENGTH * S.STICK_LENGTH * math.cos(interior))
    for off in IK_WORKSPACE_OFFSETS:
        target = rest + Vector(off)
        set_ctrl_world_head(obj, target)
        wrist = tail(pb(obj, S.IK_OWNER))
        dist = (target - head(pb(obj, "B_Arm_Boom"))).length
        if dist >= d_min + 0.01:
            err = (wrist - target).length
            check(err < 0.02, f"wrist {err:.4f} m from target at offset {off}")
        else:
            print(f"  note: offset {off} is {dist:.2f} m from the boom head, inside the "
                  f"{d_min:.2f} m minimum reach under the stick limit; wrist reach not checked")
        be, sr = boom_elev(obj), stick_rel(obj)
        check(b_lo - tol <= be <= b_hi + tol, f"boom elevation {be:.2f} outside {S.BOOM_LIMIT_DEG} at {off}")
        check(s_lo - tol <= sr <= s_hi + tol, f"stick angle {sr:.2f} outside {S.STICK_LIMIT_DEG} at {off}")
        check_pistons(f"offset {off}")
    print("  IK joint limits and pistons ok")


def test_far_target_clamped():
    """Pushing the controller far out must not extend the arm straight: the controller head
    stays inside the reach sphere (Limit Distance)."""
    obj = fresh()
    rest = pb(obj, S.IK_TARGET).bone.head_local.copy()
    set_ctrl_world_head(obj, rest + Vector((0.0, -6.0, 6.0)))
    boom_head = head(pb(obj, "B_Arm_Boom"))
    d = (head(pb(obj, S.IK_TARGET)) - boom_head).length
    limit = 0.98 * (S.BOOM_LENGTH + S.STICK_LENGTH) + 0.01
    check(d <= limit, f"controller {d:.3f} m from boom head, limit {limit:.3f}")
    print(f"  far target clamped ok ({d:.3f} m <= {limit:.3f} m)")


def test_joint_limits_fk():
    """FK posing (IK muted): Limit Rotation must hold the same ranges."""
    obj = fresh()
    b_lo, b_hi = S.BOOM_LIMIT_DEG
    s_lo, s_hi = S.STICK_LIMIT_DEG
    tol = 1.0
    pb(obj, S.IK_OWNER).constraints["IK_Bucket"].mute = True
    upd()
    check(abs(boom_elev(obj) - S.BOOM_REST_DEG) < tol, "rest boom elevation changed with IK muted")
    for boom_rot, stick_rot in ((90, 0), (-90, 0), (0, 90), (0, -90), (90, 90), (-90, -90)):
        pb(obj, "B_Arm_Boom").rotation_euler = (math.radians(boom_rot), 0.0, 0.0)
        pb(obj, S.IK_OWNER).rotation_euler = (math.radians(stick_rot), 0.0, 0.0)
        upd()
        be, sr = boom_elev(obj), stick_rel(obj)
        check(b_lo - tol <= be <= b_hi + tol, f"FK boom {be:.2f} outside range (rot {boom_rot})")
        check(s_lo - tol <= sr <= s_hi + tol, f"FK stick {sr:.2f} outside range (rot {stick_rot})")
    pb(obj, "B_Arm_Boom").rotation_euler = (math.radians(90), 0.0, 0.0)
    pb(obj, S.IK_OWNER).rotation_euler = (0.0, 0.0, 0.0)
    upd()
    check(abs(boom_elev(obj) - b_lo) < tol, f"boom not clamped at {b_lo}: {boom_elev(obj):.2f}")
    print("  FK joint limits ok")


def test_bucket_copy_rotation():
    obj = fresh()
    set_ctrl_world_head(obj, pb(obj, S.IK_TARGET).bone.head_local + Vector((0.0, -0.5, -0.8)))
    # bucket world Y must match controller world Y (copy rotation)
    check((ydir(pb(obj, "B_Tool_Bucket")) - ydir(pb(obj, S.IK_TARGET))).length < 1e-3, "bucket rotation not copied")
    print("  bucket copy rotation ok")


def test_spud_legs():
    obj = fresh()
    for k in S.SPUD_XY:
        p = pb(obj, f"B_Spud_Leg_{k}")
        z0 = head(p).z
        p.location = (0.0, -10.0, 0.0)
        upd()
        h = head(p)
        check(abs((z0 - h.z) - S.SPUD_DROP) < POS_TOL, f"{k} drop {z0 - h.z:.5f} != {S.SPUD_DROP}")
        check(abs(h.x - S.SPUD_XY[k][0]) < POS_TOL and abs(h.y - S.SPUD_XY[k][1]) < POS_TOL,
              f"{k} moved sideways")
        p.location = (0.0, 1.0, 0.0)
        upd()
        check(abs(head(p).z - z0) < POS_TOL, f"{k} moved up: {head(p).z - z0:.5f}")
        p.location = (0.0, 0.0, 0.0)
    print("  spud legs ok")


def test_root_no_constraints():
    obj = fresh()
    check(len(pb(obj, "B_Root_Hull").constraints) == 0, "root has constraints")
    print("  root ok")


def main():
    tests = [test_structure, test_rest_pose_unchanged, test_ik_reach, test_turret_slew,
             test_pistons, test_joint_limits_fk, test_joint_limits_ik, test_far_target_clamped,
             test_bucket_copy_rotation, test_spud_legs, test_root_no_constraints]
    for t in tests:
        print(t.__name__)
        t()
    print("ALL RIG TESTS PASSED")


if __name__ == "__main__":
    main()
