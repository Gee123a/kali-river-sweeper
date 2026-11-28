"""Pintu Air rotating warning beacon (0.21 m tall, 0.16 m plate): dark square mount plate, round housing,
amber dome lens (emissive swatch) with a dark top cap and a 4-bar guard cage. The spinning reflector is the
separate SM_Prop_BeaconRotor, mounted at HOUSING_TOP inside the lens by PF_WarningBeacon_PintuAir.

Origin = centre of the mount plate bottom: the importer drops the prefab origin on the sluice-gate top.
"""
import bpy  # must be first
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 2,
    "name": "SM_Prop_WarningBeacon",
    "prefab": "PF_WarningBeacon_PintuAir",
    "label": "Rotating warning beacon: mount plate, housing, amber dome lens, guard cage",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "palette": [
        ("#2b2e33", 0.3, 0.45),         # 0 dark mount plate / housing / cage
        ("#ffa31f", 0.0, 0.85, True),   # 1 amber lens (emissive)
    ],
}

HOUSING_TOP = 0.085                # rotor spin-axis bottom (Unity y)


def build():
    geo = ts.Geo()
    ts.box(geo, 0, (-0.08, -0.08, 0.0), (0.08, 0.08, 0.015))                            # mount plate
    ts.lathe(geo, [(0.015, 0.070, 0.070), (0.070, 0.068, 0.068), (HOUSING_TOP, 0.075, 0.075)], 12, lambda r: 0)
    ts.lathe(geo, [(HOUSING_TOP, 0.075, 0.075), (0.150, 0.070, 0.070), (0.185, 0.058, 0.058), (0.205, 0.035, 0.035)],
             12, lambda r: 1)                                                           # lens dome
    ts.lathe(geo, [(0.205, 0.035, 0.035), (0.212, 0.028, 0.028)], 12, lambda r: 0, cap1=0)                # top cap
    for x, y in ((0.074, 0.0), (-0.074, 0.0), (0.0, 0.074), (0.0, -0.074)):              # guard cage bars
        ts.box(geo, 0, (x - 0.004, y - 0.004, HOUSING_TOP), (x + 0.004, y + 0.004, 0.19))
    return geo.objects(SPEC["name"])
