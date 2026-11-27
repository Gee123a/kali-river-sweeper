"""Shared helpers for JC's small lighting equipment props (warung lantern, Pintu Air warning beacon + rotor).
KaliLightingBuilder.cs (Unity, KALI > Lighting) wraps them into PF_Lantern_Warung / PF_WarningBeacon_PintuAir.

Same atlas scheme as the trash pack (5x4 cells, 4x4 colour swatches) with its own material and textures:
M_Equipment_Atlas + T_Equipment_Atlas_{Albedo,Normal,Mask,Emission}.png (2048x2048). Palette entries may add a
4th value True: that swatch is white in the Emission map, so one material glows only on the bulb / lens and
LanternFlicker / WarningBeaconRotator tint it through _EmissionColor.

Rules checked by validate_equipment (trash_common.validate_trash with pivot="floor"):
  * 150 - 400 triangles, transforms applied, one material M_Equipment_Atlas, UVs inside the prop's cell.
  * Origin (0,0,0) on the floor of the prop at its mount point: lantern = post base, beacon = base centre,
    rotor = spin-axis bottom. The importer places the prefab origin on the building's roof top.
  * Clean props (new equipment): flat swatches, no wear.
"""
import importlib

import bpy  # noqa: F401

from kali_blender import tools_common as tc
from kali_blender import trash_common as trc

MATERIAL_NAME = "M_Equipment_Atlas"
ATLAS_FILES = {
    "albedo": "T_Equipment_Atlas_Albedo.png",
    "normal": "T_Equipment_Atlas_Normal.png",
    "mask": "T_Equipment_Atlas_Mask.png",
    "emission": "T_Equipment_Atlas_Emission.png",
}
FBX_DIR = "unity/Assets/_Project/Props/Equipment/Meshes"
TEX_DIR = "unity/Assets/_Project/Props/Equipment/Textures"
BLEND_PATH = "blender/SM_Equipment_Pack.blend"

EQUIPMENT_MODULES = [
    "equip_01_lantern_warung",
    "equip_02_warning_beacon",
    "equip_03_beacon_rotor",
]


def load_equipment_module(mod_name):
    return importlib.import_module(f"kali_blender.equipment.{mod_name}")


def build_equipment(mod_name, collection=None):
    mod = load_equipment_module(mod_name)
    obj = tc.assemble(mod.SPEC, mod.build(), material_name=MATERIAL_NAME)
    obj.pop("kali_tool_index", None)
    obj.pop("kali_head_dir", None)
    obj["kali_equipment_index"] = mod.SPEC["index"]
    if collection is not None:
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


def validate_equipment(obj, spec):
    issues = trc.validate_trash(obj, spec, material=MATERIAL_NAME, prefab_prefix="PF_", pivot="floor")
    floor = [v.co for v in obj.data.vertices if abs(v.co.z) < 1e-4]
    if not floor or not (min(c.x for c in floor) <= 0 <= max(c.x for c in floor)
                         and min(c.y for c in floor) <= 0 <= max(c.y for c in floor)):
        issues.append("origin is not inside the mount footprint on the floor (z = 0)")
    return issues
