"""Tests for kali_blender.excavator_mesh (SK_ExcavatorAmfibi mesh).

Run:  /opt/bpyenv/bin/python blender/tests/test_excavator_mesh.py
Prints "ALL MESH TESTS PASSED" and exits 0, or raises (non-zero exit) on the first failure.
The stand-in armature is built straight from excavator_spec.BONES, so the rig module is not needed.
"""
import math
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, os.pardir)))

import bpy  # noqa: E402  (must come before bmesh / mathutils in the bpy wheel)
import bmesh  # noqa: E402
from mathutils import Matrix  # noqa: E402

from kali_blender import excavator_spec as S  # noqa: E402
from kali_blender import excavator_mesh as M  # noqa: E402

TURRET = "B_Turret_Slew"
BOOM = "B_Arm_Boom"
HULL = "B_Root_Hull"
DEFORM = [n for n, _h, _t, _p, d in S.BONES if d]
CONTROLLERS = [n for n, _h, _t, _p, d in S.BONES if not d]
TOL = 1e-4


def dist(a, b):
    return math.sqrt(sum((x - y) ** 2 for x, y in zip(a, b)))


def stand_in_armature():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    arm_data = bpy.data.armatures.new(S.ARMATURE_NAME)
    arm = bpy.data.objects.new(S.ARMATURE_NAME, arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    arm.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = {}
    for name, head, tail, _parent, deform in S.BONES:
        eb = arm_data.edit_bones.new(name)
        eb.head = head
        eb.tail = tail
        eb.use_deform = deform
        ebs[name] = eb
    for name, _head, _tail, parent, _deform in S.BONES:
        if parent:
            ebs[name].parent = ebs[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    return arm


def group_names(obj):
    names = {g.index: g.name for g in obj.vertex_groups}
    out = []
    for v in obj.data.vertices:
        out.append([(names[g.group], g.weight) for g in v.groups])
    return out


def group_indices(obj, name):
    return [i for i, groups in enumerate(group_names(obj)) if any(n == name for n, _w in groups)]


def points(obj, idx):
    return [tuple(obj.data.vertices[i].co) for i in idx]


def nearest(pts, target):
    return min(dist(p, target) for p in pts)


# ---------------------------------------------------------------- requirement tests
def check_object_setup(arm, obj):
    # Req 1: one mesh object, identity transform, parented with one Armature modifier.
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    assert len(meshes) == 1 and meshes[0] is obj, "expected exactly one mesh object"
    assert obj.name == S.MESH_NAME and obj.data.name == S.MESH_NAME, (obj.name, obj.data.name)
    assert all(abs(v) < TOL for v in obj.location), obj.location
    assert all(abs(v) < TOL for v in obj.rotation_euler), obj.rotation_euler
    assert all(abs(v - 1.0) < TOL for v in obj.scale), obj.scale
    assert obj.parent is arm and obj.parent_type == "OBJECT", (obj.parent, obj.parent_type)
    ident = Matrix.Identity(4)
    assert all(abs(obj.matrix_parent_inverse[r][c] - ident[r][c]) < TOL for r in range(4) for c in range(4))
    mods = list(obj.modifiers)
    assert len(mods) == 1 and mods[0].type == "ARMATURE", [m.type for m in mods]
    assert mods[0].object is arm and mods[0].use_vertex_groups and not mods[0].use_bone_envelopes
    print("PASS req1 object setup")


def check_rest_pose(obj):
    # Req 2: geometry matches the spec coordinates in the rest pose.
    hull = points(obj, group_indices(obj, HULL))
    xs, ys, zs = zip(*hull)
    assert abs((max(xs) - min(xs)) - S.HULL_WIDTH) < 1e-3, (max(xs) - min(xs))
    assert abs((max(ys) - min(ys)) - S.HULL_LENGTH) < 1e-3, (max(ys) - min(ys))
    assert abs(min(zs) - S.HULL_BOTTOM_Z) < 1e-4, min(zs)
    assert abs(max(zs) - S.SLEW_RING_TOP_Z) < 1e-4, max(zs)
    turret = points(obj, group_indices(obj, TURRET))
    assert min(p[2] for p in turret) > S.SLEW_RING_TOP_Z - 1e-4
    boom = points(obj, group_indices(obj, BOOM))
    assert nearest(boom, S.BOOM_HEAD) < 0.35 and nearest(boom, S.BOOM_TAIL) < 0.35
    stick = points(obj, group_indices(obj, "B_Arm_Stick"))
    assert nearest(stick, S.STICK_TAIL) < 0.2
    bucket = points(obj, group_indices(obj, "B_Tool_Bucket"))
    assert nearest(bucket, S.BUCKET_TAIL) < 0.2
    for key, (x, y) in S.SPUD_XY.items():
        leg = points(obj, group_indices(obj, f"B_Spud_Leg_{key}"))
        assert nearest(leg, (x, y, S.SPUD_BOTTOM_Z)) < 0.2 and nearest(leg, (x, y, S.SPUD_TOP_Z)) < 0.2
    for suffix, (base_pin, _bp, rod_pin, _rp) in S.PISTONS.items():
        base_name, rod_name = S.piston_bone_names(suffix)
        base = points(obj, group_indices(obj, base_name))
        rod = points(obj, group_indices(obj, rod_name))
        assert nearest(base, base_pin) < 0.15, (base_name, nearest(base, base_pin))
        assert nearest(rod, rod_pin) < 0.15, (rod_name, nearest(rod, rod_pin))
    print("PASS req2 rest pose")


def check_skinning(obj):
    # Req 3: one group per deform bone that owns geometry, exact names, each vertex in exactly one group.
    names = {g.name for g in obj.vertex_groups}
    assert names == set(DEFORM), (sorted(set(DEFORM) - names), sorted(names - set(DEFORM)))
    for ctrl in CONTROLLERS:
        assert ctrl not in names, f"controller {ctrl} must not have a vertex group"
    for v, groups in zip(obj.data.vertices, group_names(obj)):
        assert len(groups) == 1, (v.index, groups)
        assert abs(groups[0][1] - 1.0) < 1e-6, (v.index, groups)
    print("PASS req3 rigid skinning (%d groups)" % len(names))


def check_triangles(obj):
    # Req 4: triangle budget.
    me = obj.data
    me.calc_loop_triangles()
    tris = len(me.loop_triangles)
    lo, hi = S.TRI_BUDGET
    assert lo <= tris <= hi, f"{tris} triangles outside {S.TRI_BUDGET}"
    print(f"PASS req4 triangles = {tris}")


def check_materials(obj):
    # Req 5: material slots in order, Principled values from the spec, every face on a used slot.
    me = obj.data
    slots = [m.name if m else None for m in me.materials]
    assert slots == S.MATERIAL_ORDER, slots
    for name in S.MATERIAL_ORDER:
        mat = bpy.data.materials[name]
        spec = S.MATERIALS[name]
        rgba = S.hex_to_linear_rgba(spec["color_hex"])
        assert mat.node_tree is not None, name
        bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
        base = tuple(bsdf.inputs["Base Color"].default_value)
        assert all(abs(a - b) < 1e-5 for a, b in zip(base, rgba)), (name, base, rgba)
        assert abs(bsdf.inputs["Metallic"].default_value - spec["metallic"]) < 1e-6, name
        assert abs(bsdf.inputs["Roughness"].default_value - (1.0 - spec["smoothness"])) < 1e-6, name
        assert all(abs(a - b) < 1e-5 for a, b in zip(tuple(mat.diffuse_color), rgba)), name
    used = set()
    for poly in me.polygons:
        assert 0 <= poly.material_index < len(S.MATERIAL_ORDER), poly.material_index
        used.add(poly.material_index)
    assert used == {0, 1, 2}, used
    print("PASS req5 materials")


def check_uvs(obj):
    # Req 6: a UVMap layer covering every loop, all inside 0..1.
    me = obj.data
    assert "UVMap" in me.uv_layers, list(me.uv_layers.keys())
    layer = me.uv_layers["UVMap"].data
    assert len(layer) == len(me.loops), (len(layer), len(me.loops))
    for d in layer:
        assert -TOL <= d.uv.x <= 1 + TOL and -TOL <= d.uv.y <= 1 + TOL, tuple(d.uv)
    print("PASS req6 UVs")


def check_no_loose_geometry(obj):
    # Req 7: no loose vertices or edges.
    bm = bmesh.new()
    bm.from_mesh(obj.data)
    loose_v = [v.index for v in bm.verts if not v.link_faces]
    loose_e = [e.index for e in bm.edges if not e.link_faces]
    bm.free()
    assert not loose_v and not loose_e, (loose_v[:5], loose_e[:5])
    print("PASS req7 no loose geometry")


def check_parts_and_closure(obj):
    # Req 8: every deform bone owns >= 8 verts; each group is a closed solid with outward winding.
    me = obj.data
    group_of_vert = [groups[0][0] for groups in group_names(obj)]
    for bone in DEFORM:
        count = sum(1 for g in group_of_vert if g == bone)
        assert count >= 8, (bone, count)
    volume = {bone: 0.0 for bone in DEFORM}
    for poly in me.polygons:
        vs = [tuple(me.vertices[i].co) for i in poly.vertices]
        owner = group_of_vert[poly.vertices[0]]
        for k in range(1, len(vs) - 1):
            a, b, c = vs[0], vs[k], vs[k + 1]
            volume[owner] += (a[0] * (b[1] * c[2] - b[2] * c[1]) - a[1] * (b[0] * c[2] - b[2] * c[0])
                              + a[2] * (b[0] * c[1] - b[1] * c[0])) / 6.0
    bad = [b for b, v in volume.items() if v <= 0.0]
    assert not bad, f"inside-out or open groups: {bad}"
    print("PASS req8 parts own geometry and are closed")


def check_deformation(arm, obj):
    # Req 9: rotate the turret 90 deg and the boom 20 deg about their bone axes (bone-local Y).
    pose = arm.pose.bones
    pose[TURRET].rotation_mode = "XYZ"
    pose[TURRET].rotation_euler = (0.0, math.radians(90.0), 0.0)
    pose[BOOM].rotation_mode = "XYZ"
    pose[BOOM].rotation_euler = (0.0, math.radians(20.0), 0.0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    ev = obj.evaluated_get(dg)
    me_def = ev.to_mesh()
    deformed = [tuple(v.co) for v in me_def.vertices]
    ev.to_mesh_clear()
    rest = [tuple(v.co) for v in obj.data.vertices]
    assert len(deformed) == len(rest), (len(deformed), len(rest))

    boom_idx = group_indices(obj, BOOM)
    assert len(boom_idx) >= 8
    moved = max(dist(rest[i], deformed[i]) for i in boom_idx)
    assert moved > 0.05, f"boom did not move ({moved:.4f} m)"
    for x, y in ((i, j) for x_i, i in enumerate(boom_idx) for j in boom_idx[x_i + 1:]):
        d_rest = dist(rest[x], rest[y])
        d_def = dist(deformed[x], deformed[y])
        assert abs(d_rest - d_def) < TOL, f"boom vertices {x},{y} not rigid: {d_rest} vs {d_def}"

    turret_idx = group_indices(obj, TURRET)
    tur_moved = max(dist(rest[i], deformed[i]) for i in turret_idx)
    assert tur_moved > 0.05, "turret did not rotate"

    hull_idx = group_indices(obj, HULL)
    hull_dev = max(dist(rest[i], deformed[i]) for i in hull_idx)
    assert hull_dev < 1e-5, f"hull moved by {hull_dev}"
    print(f"PASS req9 deformation (boom moved {moved:.3f} m, rigid; hull fixed)")


def main():
    arm = stand_in_armature()
    obj = M.build_mesh(arm)
    check_object_setup(arm, obj)
    check_rest_pose(obj)
    check_skinning(obj)
    check_triangles(obj)
    check_materials(obj)
    check_uvs(obj)
    check_no_loose_geometry(obj)
    check_parts_and_closure(obj)
    check_deformation(arm, obj)  # changes the pose, keep last
    print("ALL MESH TESTS PASSED")


if __name__ == "__main__":
    main()
