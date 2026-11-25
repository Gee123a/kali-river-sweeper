"""Shared helpers for floating trash props (docs/PRD.md section 4, AGENTS.md budgets).

Same atlas scheme as tools_common (5x4 cells, 4x4 colour swatches per cell) but its own
material / textures: M_Trash_Atlas + T_Trash_Atlas_{Albedo,Normal,Mask}.png (2048x2048).

Rules checked by validate_trash:
  * 150 - 400 triangles.
  * Object origin (0,0,0) = centre of the bounding box (rigidbody / buoyancy pivot), within 0.02 m.
  * Transforms applied, one material M_Trash_Atlas, UVs inside the prop's atlas cell.

Trash module contract (blender/kali_blender/trash/trash_XX_name.py):
    SPEC = {"index": 1, "name": "SM_Trash_MedicalBag", "prefab": "PF_Trash_MedicalBag",
            "label": "...", "palette": [("#eab308", 0.0, 0.4), ...]}
    def build():  -> [part objects tagged with tools_common.tag(obj, swatch)]
"""
import importlib

import bpy  # noqa: F401
from mathutils import Vector

from kali_blender import tools_common as tc

TRI_MIN, TRI_MAX = 150, 400
PIVOT_TOLERANCE = 0.02
MATERIAL_NAME = "M_Trash_Atlas"
ATLAS_FILES = {
    "albedo": "T_Trash_Atlas_Albedo.png",
    "normal": "T_Trash_Atlas_Normal.png",
    "mask": "T_Trash_Atlas_Mask.png",
}
FBX_DIR = "unity/Assets/_Project/Props/Trash/Meshes"
TEX_DIR = "unity/Assets/_Project/Props/Trash/Textures"
BLEND_PATH = "blender/SM_Trash_Pack.blend"

TRASH_MODULES = [
    "trash_01_medical_bag",
    "trash_02_syringe_box",
]


def load_trash_module(mod_name):
    return importlib.import_module(f"kali_blender.trash.{mod_name}")


def build_trash(mod_name, collection=None):
    mod = load_trash_module(mod_name)
    obj = tc.assemble(mod.SPEC, mod.build(), material_name=MATERIAL_NAME)
    obj.pop("kali_tool_index", None)
    obj.pop("kali_head_dir", None)
    obj["kali_trash_index"] = mod.SPEC["index"]
    obj["kali_prefab"] = mod.SPEC["prefab"]
    if collection is not None:
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def validate_trash(obj, spec):
    issues = []
    me = obj.data
    tris = tc.tri_count(obj)
    if not TRI_MIN <= tris <= TRI_MAX:
        issues.append(f"tris {tris} outside {TRI_MIN}-{TRI_MAX}")
    if obj.name != spec["name"]:
        issues.append(f"name {obj.name} != {spec['name']}")
    if not spec.get("prefab", "").startswith("PF_Trash_"):
        issues.append("SPEC['prefab'] must start with PF_Trash_")
    if any(abs(v) > 1e-6 for v in obj.location) or any(abs(v) > 1e-6 for v in obj.rotation_euler) \
            or any(abs(v - 1) > 1e-6 for v in obj.scale):
        issues.append("transforms not applied")
    if len(me.materials) != 1 or me.materials[0] is None or me.materials[0].name != MATERIAL_NAME:
        issues.append(f"materials {[m.name if m else None for m in me.materials]} != [{MATERIAL_NAME}]")
    if not me.uv_layers:
        issues.append("no UV layer")
    else:
        u0, v0, u1, v1 = tc.cell_rect(spec["index"])
        eps = 1e-5
        bad = sum(1 for d in me.uv_layers.active.data
                  if not (u0 - eps <= d.uv.x <= u1 + eps and v0 - eps <= d.uv.y <= v1 + eps))
        if bad:
            issues.append(f"{bad} UVs outside atlas cell {spec['index']}")
    if not me.vertices:
        return issues + ["empty mesh"]
    lo = Vector((min(v.co[i] for v in me.vertices) for i in range(3)))
    hi = Vector((max(v.co[i] for v in me.vertices) for i in range(3)))
    centre = (lo + hi) / 2
    if centre.length > PIVOT_TOLERANCE:
        issues.append(f"origin not at bbox centre (centre {tuple(round(c, 3) for c in centre)})")
    size = max(hi - lo)
    if not 0.05 <= size <= 1.5:
        issues.append(f"implausible size {size:.2f} m")
    return issues
