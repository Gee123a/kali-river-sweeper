import bpy  # must be first
import bmesh  # noqa: F401
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 18,
    "name": "SM_Tool_TongkatMagnet",
    "label": "Tongkat magnet (telescopic magnet pickup)",
    "head_dir": "+Z",
    "palette": [
        ("#1f1f22", 0.0, 0.30),   # black foam handle
        ("#c3c7cc", 1.0, 0.75),   # polished steel tubes
        ("#4d535a", 0.6, 0.40),   # dark anodised collars and knuckle
        ("#c62828", 0.0, 0.45),   # red magnet disc
    ],
}


def _cyl(n, r, d, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=d, location=loc, rotation=rot)
    return bpy.context.object


def _ball(seg, rings, r, loc):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc)
    return bpy.context.object


def _ring(major, minor, z):
    bpy.ops.mesh.primitive_torus_add(major_segments=12, minor_segments=4,
                                     major_radius=major, minor_radius=minor, location=(0, 0, z))
    return bpy.context.object


def build():
    parts = []
    # foam handle with rounded butt; grip at the origin (handle centre)
    parts.append(tc.tag(_cyl(12, 0.022, 0.22, (0, 0, -0.01)), 0))
    parts.append(tc.tag(_ball(12, 6, 0.022, (0, 0, -0.12)), 0))
    # two grip ribs on the foam
    parts.append(tc.tag(_ring(0.023, 0.004, -0.06), 0))
    parts.append(tc.tag(_ring(0.023, 0.004, 0.04), 0))
    # three telescoping steel sections, decreasing radius upward
    parts.append(tc.tag(_cyl(12, 0.014, 0.26, (0, 0, 0.21)), 1))   # section A
    parts.append(tc.tag(_cyl(12, 0.0115, 0.22, (0, 0, 0.43)), 1))  # section B
    parts.append(tc.tag(_cyl(12, 0.009, 0.16, (0, 0, 0.60)), 1))   # section C
    # collar rings at the joints
    parts.append(tc.tag(_cyl(12, 0.0165, 0.012, (0, 0, 0.335)), 2))
    parts.append(tc.tag(_cyl(12, 0.0135, 0.012, (0, 0, 0.535)), 2))
    # pivot knuckle (axis along X), short neck, and red magnet disc on top
    parts.append(tc.tag(_cyl(10, 0.009, 0.026, (0, 0, 0.70), rot=(0, radians(90), 0)), 2))
    parts.append(tc.tag(_cyl(8, 0.006, 0.04, (0, 0, 0.72)), 2))
    parts.append(tc.tag(_cyl(16, 0.030, 0.016, (0, 0, 0.745)), 3))
    return parts
