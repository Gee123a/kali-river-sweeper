"""Sendok bengkok - bent stainless serving spoon (0.40 m), red tape grip, +Z head."""
import bpy  # must be first
from math import radians
from mathutils import Quaternion, Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 1,
    "name": "SM_Tool_SendokBengkok",
    "label": "Sendok bengkok (bent spoon)",
    "head_dir": "+Z",
    "palette": [
        ("#c9ccd1", 1.0, 0.80),  # 0 stainless steel
        ("#b3221f", 0.0, 0.30),  # 1 red electrical tape
        ("#4a0f0d", 0.0, 0.25),  # 2 tape edge bands
        ("#8d9299", 1.0, 0.45),  # 3 rivet
    ],
}

PIVOT = Vector((0.0, 0.0, 0.10))           # where the handle bends
TILT = Quaternion((1.0, 0.0, 0.0), radians(-25.0))  # neck leans toward +Y


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _tilt(local):
    """Point given relative to the bend pivot, rotated by the bend, in world space."""
    return PIVOT + TILT @ Vector(local)


def build():
    parts = []

    # flat steel handle, runs from -0.12 to the bend at +0.10
    handle = _add("cube", size=2, location=(0, 0, -0.01))
    handle.scale = (0.011, 0.0025, 0.11)
    parts.append(tc.tag(handle, 0))

    # neck: same flat section, leaning 25 deg from the handle
    neck = _add("cube", size=2, location=tuple(_tilt((0, 0, 0.05))))
    neck.scale = (0.011, 0.0025, 0.05)
    neck.rotation_mode = "QUATERNION"
    neck.rotation_quaternion = TILT
    parts.append(tc.tag(neck, 0))

    # oval bowl: flattened ellipsoid on the bent end
    bowl = _add("uv_sphere", segments=12, ring_count=6, radius=1.0,
                location=tuple(_tilt((0, 0, 0.15))))
    bowl.scale = (0.035, 0.012, 0.05)
    bowl.rotation_mode = "QUATERNION"
    bowl.rotation_quaternion = TILT
    parts.append(tc.tag(bowl, 0))

    # raised rim around the bowl (ring lying in the bowl's plane)
    rim = _add("torus", major_segments=14, minor_segments=5,
               major_radius=1.0, minor_radius=0.12, location=tuple(_tilt((0, 0, 0.15))))
    rim.scale = (0.035, 0.05, 0.04)
    rim.rotation_mode = "QUATERNION"
    rim.rotation_quaternion = TILT @ Quaternion((1.0, 0.0, 0.0), radians(90))
    parts.append(tc.tag(rim, 0))

    # rivet at the handle end (axis across the flat handle)
    rivet = _add("cylinder", vertices=8, radius=0.0045, depth=0.012,
                 location=(0, 0, -0.10), rotation=(radians(90), 0, 0))
    parts.append(tc.tag(rivet, 3))

    # red electrical tape wrap = grip, centred on the origin
    tape = _add("cylinder", vertices=12, radius=0.0140, depth=0.10, location=(0, 0, 0))
    parts.append(tc.tag(tape, 1))
    for z in (-0.05, 0.05):
        band = _add("cylinder", vertices=12, radius=0.0146, depth=0.005, location=(0, 0, z))
        parts.append(tc.tag(band, 2))

    return parts
