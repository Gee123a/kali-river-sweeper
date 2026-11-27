"""Beacon rotor (0.10 m tall): steel spindle on a motor hub carrying two back-to-back chrome reflector dishes
(open toward +Y and -Y), so the spinning pair throws the beam both ways. Symmetric about the spin axis.

Origin = spin-axis bottom; PF_WarningBeacon_PintuAir mounts it at the beacon's housing top and spins it.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 3,
    "name": "SM_Prop_BeaconRotor",
    "prefab": "PF_WarningBeacon_PintuAir",
    "label": "Beacon rotor: spindle, motor hub, twin chrome reflector dishes",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "palette": [
        ("#3a3d42", 0.4, 0.5),          # 0 motor hub
        ("#9aa0a6", 0.9, 0.7),          # 1 steel spindle
        ("#e4e8ec", 1.0, 0.92),         # 2 chrome reflector
    ],
}

DISH_Z = 0.055                     # dish centre height above the spin-axis bottom (beam height)


def build():
    geo = ts.Geo()
    ts.lathe(geo, [(0.0, 0.02, 0.02), (0.02, 0.02, 0.02)], 8, lambda r: 0, cap0=0, cap1=0)     # motor hub
    ts.lathe(geo, [(0.02, 0.006, 0.006), (0.10, 0.006, 0.006)], 6, lambda r: 1, cap1=1)        # spindle
    for angle, off in ((-90, 0.004), (90, -0.004)):           # dish opening toward +Y, then toward -Y
        geo.xform = Matrix.Translation((0, off, DISH_Z)) @ Matrix.Rotation(math.radians(angle), 4, "X")
        ts.lathe(geo, [(0.0, 0.008, 0.008), (0.012, 0.026, 0.026), (0.022, 0.035, 0.035)], 10, lambda r: 2, cap0=2)
        ts.lathe(geo, [(0.022, 0.035, 0.035), (0.012, 0.024, 0.024), (0.002, 0.007, 0.007)], 10, lambda r: 2, cap1=2)
    geo.xform = None
    return geo.objects(SPEC["name"])
