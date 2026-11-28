"""Instanced floating trash bundles for the million-piece river (plan.md, plan_jc R1-J1, plan_ivan R0-I2 / R1-I2).

The bundle field is drawn as INSTANCED data (Graphics.RenderMeshInstanced-style, thousands of copies), not one
GameObject per bundle, so these assets are deliberately tiny and uniform:
  * under 100 triangles each, one mesh per variant, flat colour swatches only;
  * ONE shared material M_Bundles_Atlas (T_Bundles_Atlas_*), built by KaliPropPrefabBuilder with
    enableInstancing = true, so every variant can be drawn in the same instanced batch family;
  * WATERLINE origin (the bundle floats on y = water), centred in x/z; ~0.6 m, loud colours for brown water;
  * prefabs PF_Trash_InstBundle_<Variant> carry only MeshFilter + MeshRenderer (no collider, Rigidbody,
    RiverFlowBuoyancy or RiverTrashItem): the field system owns position, pickup and waste class.
Variant names include the class keyword RiverTrashItem uses ("Medis" -> Medical, "Biohazard" -> Biohazard).

Output: unity/Assets/_Project/Props/Bundles/{Meshes,Textures} (kept out of Props/Trash/Meshes so the trash prefab
builder does not turn them into full floating trash), blender/SM_Bundles_Pack.blend.
"""
import importlib

import bpy  # noqa: F401

from kali_blender import tools_common as tc
from kali_blender import trash_common as trc

MATERIAL_NAME = "M_Bundles_Atlas"
ATLAS_FILES = {
    "albedo": "T_Bundles_Atlas_Albedo.png",
    "normal": "T_Bundles_Atlas_Normal.png",
    "mask": "T_Bundles_Atlas_Mask.png",
}
FBX_DIR = "unity/Assets/_Project/Props/Bundles/Meshes"
TEX_DIR = "unity/Assets/_Project/Props/Bundles/Textures"
BLEND_PATH = "blender/SM_Bundles_Pack.blend"
TRIS = (20, 100)

BUNDLE_MODULES = [
    "bundle_01_normal_kresek",
    "bundle_02_normal_botol",
    "bundle_03_normal_styrofoam",
    "bundle_04_normal_campur",
    "bundle_05_medis",
    "bundle_06_biohazard",
]


def load_bundle_module(mod_name):
    return importlib.import_module(f"kali_blender.bundles.{mod_name}")


def build_bundle(mod_name, collection=None):
    mod = load_bundle_module(mod_name)
    obj = tc.assemble(mod.SPEC, mod.build(), material_name=MATERIAL_NAME)
    obj.pop("kali_tool_index", None)
    obj.pop("kali_head_dir", None)
    obj["kali_bundle_index"] = mod.SPEC["index"]
    if collection is not None:
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def validate_bundle(obj, spec):
    return trc.validate_trash(obj, spec, material=MATERIAL_NAME, prefab_prefix="PF_Trash_InstBundle_",
                              pivot="waterline", tris_range=TRIS, max_size=1.0)
