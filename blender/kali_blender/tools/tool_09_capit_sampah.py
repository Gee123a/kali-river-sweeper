import bpy  # must be first
import bmesh  # noqa: F401
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 9,
    "name": "SM_Tool_CapitSampah",
    "label": "Capit sampah (litter picker)",
    "head_dir": "+Z",
    "palette": [
        ("#b8c0c8", 0.9, 0.6),    # 0 aluminium tube
        ("#222426", 0.0, 0.35),   # 1 black plastic pistol grip
        ("#3a3a3a", 0.0, 0.2),    # 2 rubber cuff and jaw pads
        ("#e53935", 0.0, 0.4),    # 3 red trigger
        ("#8e969e", 0.9, 0.5),    # 4 steel jaw arms and pin
    ],
}


def _cyl(verts, radius, depth, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    return bpy.context.object


def _box(size, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.scale = size
    return obj


def _torus(major, minor, maj_seg, min_seg, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=maj_seg, minor_segments=min_seg,
                                     location=loc, rotation=rot)
    return bpy.context.object


def build():
    parts = []
    # 0.85 m aluminium shaft
    parts.append(tc.tag(_cyl(16, 0.011, 0.85, (0, 0, 0.425)), 0))
    # jaw housing with pull-rod sleeve at the top
    parts.append(tc.tag(_cyl(12, 0.014, 0.07, (0, 0, 0.885)), 0))

    # plastic pistol grip, angled, origin inside it
    parts.append(tc.tag(_cyl(16, 0.022, 0.14, (0, 0, 0), (0, radians(12), 0)), 1))
    # trigger with guard loop
    parts.append(tc.tag(_box((0.008, 0.012, 0.035), (0, -0.022, 0.01), (radians(-20), 0, 0)), 3))
    parts.append(tc.tag(_torus(0.02, 0.003, 12, 6, (0, -0.012, 0.03), (0, radians(90), 0)), 1))
    # rubber forearm cuff at the bottom with a rim
    parts.append(tc.tag(_cyl(16, 0.034, 0.05, (0, 0, -0.11)), 2))
    parts.append(tc.tag(_torus(0.034, 0.004, 16, 6, (0, 0, -0.085)), 2))

    # two steel jaw arms converging at +Z, each with a rubber pad on its inner face
    for side in (1, -1):
        tilt = (0, radians(-10 * side), 0)
        parts.append(tc.tag(_box((0.005, 0.012, 0.11), (side * 0.016, 0, 0.98), tilt), 4))
        parts.append(tc.tag(_box((0.007, 0.014, 0.04), (side * 0.012, 0, 1.00), tilt), 2))
    # hinge pin through the housing
    parts.append(tc.tag(_cyl(8, 0.003, 0.05, (0, 0, 0.93), (0, radians(90), 0)), 4))
    return parts
