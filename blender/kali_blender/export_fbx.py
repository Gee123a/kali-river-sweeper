"""FBX export helpers for KALI assets (Unity 2022.3 URP, metres, Y-up).

Every exporter applies transforms first, selects only what it exports, and uses the
single FBX_SETTINGS dict so the excavator and the tools are exported identically.
verify_fbx re-imports a written file into the open scene and removes everything the
import created, so the caller's scene is left as it was.
"""
import os
import re

import bpy  # noqa: F401  (must be imported before bmesh / mathutils in the bpy wheel)

FBX_SETTINGS = {
    "use_selection": True,
    "global_scale": 1.0,
    "apply_unit_scale": True,
    "apply_scale_options": "FBX_SCALE_ALL",
    "axis_forward": "-Z",
    "axis_up": "Y",
    "bake_space_transform": True,      # "Apply Transform"
    "mesh_smooth_type": "FACE",
    "use_mesh_modifiers": True,
    "add_leaf_bones": False,
    "primary_bone_axis": "Y",
    "secondary_bone_axis": "X",
    "path_mode": "COPY",
    "embed_textures": True,
    "bake_anim": False,
}

_TOL = 1e-5
# bpy.data collections that verify_fbx snapshots and cleans up.
_KINDS = ("objects", "meshes", "armatures", "materials", "actions", "images",
          "cameras", "lights", "collections")


def _ensure_object_mode():
    obj = bpy.context.object
    if obj is not None and obj.mode != "OBJECT":
        bpy.ops.object.mode_set(mode="OBJECT")


def _select_only(objects):
    """Select exactly `objects` (and make the first one active) in Object Mode."""
    _ensure_object_mode()
    view_layer = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    for o in objects:
        o.select_set(True)
    view_layer.objects.active = objects[0]
    missing = [o.name for o in objects if not o.select_get()]
    if missing:
        raise RuntimeError(f"could not select {missing} (hidden or not in the view layer?)")


def _assert_identity(o):
    loc = tuple(o.location)
    scale = tuple(o.scale)
    rot_angle = o.matrix_basis.to_quaternion().angle
    if any(abs(v) > _TOL for v in loc):
        raise RuntimeError(f"{o.name}: location {loc} not applied")
    if rot_angle > _TOL:
        raise RuntimeError(f"{o.name}: rotation not applied (angle {rot_angle:.6f} rad)")
    if any(abs(v - 1.0) > _TOL for v in scale):
        raise RuntimeError(f"{o.name}: scale {scale} not applied")


def apply_all_transforms(objects):
    """Ctrl+A > All Transforms on `objects`, parents before children.

    Each object is applied on its own so a skinned mesh's armature is applied first and
    the mesh's parent relationship (and world pose) is kept. Afterwards the selection is
    exactly `objects` again and every object is asserted to be at identity.
    """
    objects = list(objects)
    if not objects:
        raise ValueError("apply_all_transforms: no objects given")
    ordered = sorted(objects, key=lambda o: 0 if o.type == "ARMATURE" else 1)
    for o in ordered:
        _select_only([o])
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    for o in objects:
        _assert_identity(o)
    _select_only(objects)
    return objects


def _fbx_export(filepath, **extra):
    filepath = os.path.abspath(filepath)
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    kwargs = {**FBX_SETTINGS, **extra}
    bpy.ops.export_scene.fbx(filepath=filepath, **kwargs)
    return filepath


def export_excavator(armature_obj, mesh_obj, filepath):
    """Export the rigged excavator (armature + skinned mesh, deform bones only)."""
    apply_all_transforms([armature_obj, mesh_obj])
    _select_only([armature_obj, mesh_obj])
    return _fbx_export(filepath, object_types={"ARMATURE", "MESH"}, use_armature_deform_only=True)


def export_tool(obj, filepath):
    """Export one static tool mesh."""
    apply_all_transforms([obj])
    _select_only([obj])
    return _fbx_export(filepath, object_types={"MESH"})


def _snapshot():
    return {kind: {d.name for d in getattr(bpy.data, kind)} for kind in _KINDS}


def _new_datablocks(before):
    return {kind: [d for d in getattr(bpy.data, kind) if d.name not in before[kind]]
            for kind in _KINDS}


def _remove_new(before):
    new = _new_datablocks(before)
    for o in new["objects"]:
        bpy.data.objects.remove(o, do_unlink=True)
    for kind in ("meshes", "armatures", "materials", "actions", "images",
                 "cameras", "lights", "collections"):
        for d in new[kind]:
            if d.users == 0 or kind == "collections":
                getattr(bpy.data, kind).remove(d)


def _restore_selection(names, active_name):
    view_layer = bpy.context.view_layer
    bpy.ops.object.select_all(action="DESELECT")
    for name in names:
        o = view_layer.objects.get(name)
        if o is not None:
            o.select_set(True)
    o = view_layer.objects.get(active_name) if active_name else None
    view_layer.objects.active = o


def _unique_suffix_stripped(name, taken):
    m = re.fullmatch(r"(.+)\.\d{3}", name)
    if m and m.group(1) in taken:
        return m.group(1)
    return name


def verify_fbx(filepath, expected_bones=None, expected_meshes=None):
    """Import `filepath` and return its bones / mesh objects; raise on a bad export.

    Returns {"bones": [...], "meshes": [...], "leaf_bones": [...]}. The import's datablocks
    are removed again, and the previous selection / active object are restored.
    """
    filepath = os.path.abspath(filepath)
    if not os.path.isfile(filepath):
        raise FileNotFoundError(filepath)
    _ensure_object_mode()
    view_layer = bpy.context.view_layer
    prev_active = view_layer.objects.active.name if view_layer.objects.active else None
    prev_selected = {o.name for o in view_layer.objects if o.select_get()}
    before = _snapshot()
    try:
        bpy.ops.import_scene.fbx(filepath=filepath)
        new = _new_datablocks(before)
        bones = [b.name for arm in new["armatures"] for b in arm.bones]
        # The importer appends ".001" when a name is already taken in the open scene, so
        # compare against the name the file was exported with.
        taken = before["objects"]
        meshes = [_unique_suffix_stripped(o.name, taken) for o in new["objects"] if o.type == "MESH"]
    finally:
        _remove_new(before)
        _restore_selection(prev_selected, prev_active)

    leaf = [b for b in bones if b.endswith("_end")]
    if leaf:
        raise RuntimeError(f"{os.path.basename(filepath)}: leaf bones present {leaf}")
    if expected_bones is not None and sorted(bones) != sorted(expected_bones):
        raise RuntimeError(f"{os.path.basename(filepath)}: bones {sorted(bones)} != "
                           f"expected {sorted(expected_bones)}")
    if expected_meshes is not None and sorted(meshes) != sorted(expected_meshes):
        raise RuntimeError(f"{os.path.basename(filepath)}: meshes {sorted(meshes)} != "
                           f"expected {sorted(expected_meshes)}")
    return {"bones": bones, "meshes": meshes, "leaf_bones": leaf}
