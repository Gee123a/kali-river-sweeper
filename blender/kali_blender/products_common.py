"""Shared helpers for the clean PRODUCT props (shop / world items): the same 9 parody brands as the branded
trash, but new and intact - sealed, full, clean labels (labels.render_label(dirty=False)), no crumple/tears.

Same atlas scheme as trash_common (5x4 cells, label in the bottom 3 swatch rows, 4 swatches on top) with its
own material / textures: M_Products_Atlas + T_Products_Atlas_{Albedo,Normal,Mask}.png (2048x2048).

Rules checked by validate_product (trash_common.validate_trash with pivot="base"):
  * 150 - 400 triangles.
  * Origin (0,0,0) = centre of the bbox BOTTOM: products stand on shelves / the ground, so a prefab dropped at
    floor height sits on it. Tolerance 0.02 m.
  * Transforms applied, one material M_Products_Atlas, UVs inside the product's atlas cell.

Product module contract (blender/kali_blender/products/product_XX_name.py):
    SPEC = {"index": 1, "name": "SM_Product_Indomy", "prefab": "PF_Product_Indomy", "label": "...",
            "head_dir": "-Z", "label_art": {"name": "indomy", "rows": 3, "dirty": False}, "palette": [...]}
    def build():  -> [part objects] (trash_shapes.Geo.objects(), recentred with base=True)
"""
import importlib

import bpy  # noqa: F401

from kali_blender import tools_common as tc
from kali_blender import trash_common as trc

TRI_MIN, TRI_MAX = trc.TRI_MIN, trc.TRI_MAX
MATERIAL_NAME = "M_Products_Atlas"
ATLAS_FILES = {
    "albedo": "T_Products_Atlas_Albedo.png",
    "normal": "T_Products_Atlas_Normal.png",
    "mask": "T_Products_Atlas_Mask.png",
}
FBX_DIR = "unity/Assets/_Project/Props/Products/Meshes"
TEX_DIR = "unity/Assets/_Project/Props/Products/Textures"
BLEND_PATH = "blender/SM_Products_Pack.blend"

PRODUCT_MODULES = [
    "product_01_indomy",
    "product_02_kecap_bingo",
    "product_03_moli",
    "product_04_lifeman",
    "product_05_sari_boti",
    "product_06_risol",
    "product_07_styrofoam_makanan",
    "product_08_sprit",
    "product_09_gudang_gula",
]


def load_product_module(mod_name):
    return importlib.import_module(f"kali_blender.products.{mod_name}")


def build_product(mod_name, collection=None):
    mod = load_product_module(mod_name)
    obj = tc.assemble(mod.SPEC, mod.build(), material_name=MATERIAL_NAME)
    obj.pop("kali_tool_index", None)
    obj.pop("kali_head_dir", None)
    obj["kali_product_index"] = mod.SPEC["index"]
    obj["kali_prefab"] = mod.SPEC["prefab"]
    if collection is not None:
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def validate_product(obj, spec):
    issues = trc.validate_trash(obj, spec, material=MATERIAL_NAME, prefab_prefix="PF_Product_", pivot="base")
    if spec.get("label_art", {}).get("dirty", True):
        issues.append("products use clean labels: label_art needs 'dirty': False")
    return issues
