"""Stand-in tests for kali_blender.export_fbx (no real rig / mesh / tool modules needed).

Run:  /opt/bpyenv/bin/python blender/tests/test_export.py
Prints "ALL EXPORT TESTS PASSED" on success. Outputs go to a temp dir, never the repo.
"""
import os
import shutil
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.dirname(HERE)
sys.path.insert(0, BLENDER_DIR)

import bpy  # noqa: E402  (must come before bmesh / mathutils)
import bmesh  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from kali_blender import export_fbx as ef  # noqa: E402
from kali_blender import tools_common as tc  # noqa: E402

TMP = tempfile.mkdtemp(prefix="kali_export_test_")
EXPECTED_SETTINGS = {
    "use_selection": True,
    "global_scale": 1.0,
    "apply_unit_scale": True,
    "apply_scale_options": "FBX_SCALE_ALL",
    "axis_forward": "-Z",
    "axis_up": "Y",
    "bake_space_transform": True,
    "mesh_smooth_type": "FACE",
    "use_mesh_modifiers": True,
    "add_leaf_bones": False,
    "primary_bone_axis": "Y",
    "secondary_bone_axis": "X",
    "path_mode": "COPY",
    "embed_textures": True,
    "bake_anim": False,
}


def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def make_skinned(name, bones, nondeform=(), mesh_name=None):
    """Armature with `bones` (name, head, tail, parent, deform) + a cube skinned to the deform bones."""
    arm_data = bpy.data.armatures.new(name + "_Data")
    arm = bpy.data.objects.new(name, arm_data)
    bpy.context.scene.collection.objects.link(arm)
    bpy.context.view_layer.objects.active = arm
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = {}
    for bname, head, tail, parent, _deform in bones:
        eb = arm_data.edit_bones.new(bname)
        eb.head = Vector(head)
        eb.tail = Vector(tail)
        ebs[bname] = eb
    for bname, _h, _t, parent, _d in bones:
        if parent:
            ebs[bname].parent = ebs[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    for bname, _h, _t, _p, deform in bones:
        arm_data.bones[bname].use_deform = deform

    me = bpy.data.meshes.new((mesh_name or name) + "_Mesh")
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bm.to_mesh(me)
    bm.free()
    mesh = bpy.data.objects.new(mesh_name or name, me)
    bpy.context.scene.collection.objects.link(mesh)
    deform_names = [b[0] for b in bones if b[4]]
    for i, bname in enumerate(deform_names):
        vg = mesh.vertex_groups.new(name=bname)
        vg.add(list(range(len(me.vertices))), 1.0 if i == 0 else 0.5, "REPLACE")
    mod = mesh.modifiers.new("Armature", "ARMATURE")
    mod.object = arm
    mesh.parent = arm
    return arm, mesh


def world_coords(obj):
    return [obj.matrix_world @ v.co for v in obj.data.vertices]


def object_names():
    return sorted(o.name for o in bpy.data.objects)


def test_apply_all_transforms():
    reset()
    bones = [
        ("B_Root_Hull", (0, 0, 0), (0, 0, 1), None, True),
        ("B_Arm_Boom", (0, 0, 1), (0, 1, 1), "B_Root_Hull", True),
    ]
    arm, mesh = make_skinned("StandIn_Rig", bones, mesh_name="StandIn_Mesh")
    arm.location = (1.0, 2.0, 3.0)
    arm.rotation_euler = (0.0, 0.0, 0.5)
    arm.scale = (2.0, 2.0, 2.0)
    mesh.location = (0.5, 0.0, 0.0)
    mesh.rotation_euler = (0.2, 0.0, 0.0)
    mesh.scale = (1.0, 1.5, 1.0)
    bpy.context.view_layer.update()
    before_mesh = world_coords(mesh)
    before_bones = [arm.matrix_world @ b.head_local for b in arm.data.bones]

    ef.apply_all_transforms([arm, mesh])

    for o in (arm, mesh):
        assert tuple(round(v, 6) for v in o.location) == (0.0, 0.0, 0.0), (o.name, tuple(o.location))
        assert all(abs(v) < 1e-6 for v in o.rotation_euler), (o.name, tuple(o.rotation_euler))
        assert all(abs(v - 1) < 1e-6 for v in o.scale), (o.name, tuple(o.scale))
    assert mesh.parent is arm, "mesh lost its armature parent"
    assert mesh.modifiers["Armature"].object is arm, "armature modifier lost its target"
    bpy.context.view_layer.update()
    after_mesh = world_coords(mesh)
    for a, b in zip(before_mesh, after_mesh):
        assert (a - b).length < 1e-4, "skinned mesh moved in world space"
    after_bones = [arm.matrix_world @ b.head_local for b in arm.data.bones]
    for a, b in zip(before_bones, after_bones):
        assert (a - b).length < 1e-4, "bones moved in world space"
    print("  apply_all_transforms: identity transforms, parent kept, world pose unchanged")


def test_export_excavator_and_verify():
    reset()
    bones = [
        ("B_Root_Hull", (0, 0, 0), (0, 0, 1), None, True),
        ("B_Arm_Boom", (0, 0, 1), (0, 1, 1), "B_Root_Hull", True),
        ("B_Spud_Leg_FL", (1, 1, -0.6), (1, 1, 3.0), "B_Root_Hull", True),
        ("CTRL_IK_Bucket", (0, 2, 2), (0, 3, 2), "B_Root_Hull", False),
    ]
    arm, mesh = make_skinned("SK_Stand_Rig", bones, mesh_name="SK_Stand")
    arm.location = (0.0, 0.0, 0.5)
    mesh.scale = (1.0, 2.0, 1.0)
    path = os.path.join(TMP, "excavator", "SK_Stand.fbx")
    ef.export_excavator(arm, mesh, path)
    assert os.path.isfile(path), "FBX not written (parent dirs created?)"
    before = object_names()
    info = ef.verify_fbx(path, expected_bones=["B_Root_Hull", "B_Arm_Boom", "B_Spud_Leg_FL"],
                         expected_meshes=["SK_Stand"])
    assert object_names() == before, "verify_fbx left imported objects in the scene"
    assert info["leaf_bones"] == [], info
    assert not any(b.endswith("_end") for b in info["bones"]), info
    assert "CTRL_IK_Bucket" not in info["bones"], "non-deform bone exported"
    assert info["meshes"] == ["SK_Stand"], info
    print(f"  export_excavator + verify_fbx: bones={info['bones']} meshes={info['meshes']}")


def test_verify_rejects_leaf_bones():
    reset()
    bones = [("B_Root_Hull", (0, 0, 0), (0, 0, 1), None, True)]
    arm, mesh = make_skinned("Leaf_Rig", bones, mesh_name="Leaf_Mesh")
    ef.apply_all_transforms([arm, mesh])
    ef._select_only([arm, mesh])
    path = os.path.join(TMP, "leaf", "Leaf.fbx")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.export_scene.fbx(filepath=path, **{**ef.FBX_SETTINGS, "add_leaf_bones": True,
                                               "object_types": {"ARMATURE", "MESH"}})
    try:
        ef.verify_fbx(path)
    except RuntimeError as exc:
        assert "leaf" in str(exc), exc
    else:
        raise AssertionError("verify_fbx accepted an FBX with _end leaf bones")
    print("  verify_fbx: rejects FBX with _end leaf bones")


def test_export_tool_and_verify():
    reset()
    spec = {"index": 1, "name": "SM_Tool_Stand", "label": "stand-in", "head_dir": "+Z",
            "palette": [("#7c4a1e", 0.0, 0.25)]}
    cyl_parts = []
    bpy.ops.mesh.primitive_cylinder_add(vertices=128, radius=0.03, depth=1.2, location=(0, 0, 0))
    cyl = bpy.context.object
    cyl_parts.append(tc.tag(cyl, 0))
    obj = tc.assemble(spec, cyl_parts)
    issues = tc.validate_tool(obj, spec)
    assert issues == [], f"stand-in tool fails validate_tool: {issues}"
    path = os.path.join(TMP, "tools", "SM_Tool_Stand.fbx")
    ef.export_tool(obj, path)
    before = object_names()
    info = ef.verify_fbx(path, expected_meshes=["SM_Tool_Stand"])
    assert object_names() == before, "verify_fbx left imported objects in the scene"
    assert info["bones"] == [] and info["leaf_bones"] == [], info
    print(f"  export_tool + verify_fbx: meshes={info['meshes']}")


def test_fbx_settings():
    assert ef.FBX_SETTINGS == EXPECTED_SETTINGS, {
        k: (ef.FBX_SETTINGS.get(k), EXPECTED_SETTINGS.get(k))
        for k in set(ef.FBX_SETTINGS) | set(EXPECTED_SETTINGS)
        if ef.FBX_SETTINGS.get(k) != EXPECTED_SETTINGS.get(k)}
    print("  FBX_SETTINGS: exact match with spec")


def test_build_all_stages():
    import ast
    src = open(os.path.join(BLENDER_DIR, "build_all.py"), encoding="utf-8").read()
    stages = None
    for node in ast.parse(src).body:
        if isinstance(node, ast.Assign) and any(getattr(t, "id", None) == "STAGES" for t in node.targets):
            stages = ast.literal_eval(node.value)
    assert stages is not None, "build_all.py has no STAGES list"
    assert stages == ["excavator", "tools", "trash", "products", "equipment", "rigging", "bundles"], stages
    from kali_blender import trash_common as trc  # noqa: F401  (imports cleanly)
    assert trc.MATERIAL_NAME == "M_Trash_Atlas", trc.MATERIAL_NAME
    from kali_blender import products_common as pc
    assert pc.MATERIAL_NAME == "M_Products_Atlas", pc.MATERIAL_NAME
    print(f"  build_all stages: {stages}")


def main():
    try:
        test_fbx_settings()
        test_build_all_stages()
        test_apply_all_transforms()
        test_export_excavator_and_verify()
        test_verify_rejects_leaf_bones()
        test_export_tool_and_verify()
    finally:
        shutil.rmtree(TMP, ignore_errors=True)
    print("ALL EXPORT TESTS PASSED")


if __name__ == "__main__":
    main()
