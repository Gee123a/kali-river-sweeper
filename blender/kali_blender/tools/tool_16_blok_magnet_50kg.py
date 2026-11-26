import bpy  # must be first
import bmesh  # noqa: F401
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 16,
    "name": "SM_Tool_BlokMagnet50kg",
    "label": "Blok magnet 50kg (salvage pot magnet on rope)",
    "head_dir": "-Z",
    "palette": [
        ("#c9ccd1", 1.0, 0.80),   # 0 nickel-plated magnet pot
        ("#c62828", 0.0, 0.50),   # 1 red painted top housing
        ("#8b5a2b", 0.0, 0.30),   # 2 wooden T-toggle handle
        ("#d8c08a", 0.0, 0.15),   # 3 rope and knots
        ("#7d8590", 0.8, 0.50),   # 4 steel eyebolt and chamfer ring
    ],
}


def _cyl(verts, radius, depth, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    return bpy.context.object


def _cone(verts, r1, r2, depth, loc):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth, location=loc)
    return bpy.context.object


def _torus(major, minor, maj_seg, min_seg, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=maj_seg, minor_segments=min_seg,
                                     location=loc, rotation=rot)
    return bpy.context.object


def _ball(seg, rings, r, loc):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc)
    return bpy.context.object


def _seg(p0, p1, r, n=6):
    """Cylinder from point p0 to point p1 (used for the rope)."""
    from mathutils import Vector
    a, b = Vector(p0), Vector(p1)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=d.length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return obj


def build():
    parts = []
    # wooden T-toggle: shaft through the origin, crossbar along X above the grip
    parts.append(tc.tag(_cyl(10, 0.012, 0.08, (0, 0, -0.01)), 2))
    parts.append(tc.tag(_cyl(10, 0.011, 0.16, (0, 0, 0.03), (0, radians(90), 0)), 2))
    parts.append(tc.tag(_ball(8, 4, 0.012, (0.08, 0, 0.03)), 2))
    parts.append(tc.tag(_ball(8, 4, 0.012, (-0.08, 0, 0.03)), 2))
    # steel eyebolt at the bottom of the handle and the rope (0.45 m)
    parts.append(tc.tag(_torus(0.010, 0.003, 10, 4, (0, 0, -0.07), (radians(90), 0, 0)), 4))
    parts.append(tc.tag(_seg((0, 0, -0.08), (0, 0, -0.53), 0.0045, 6), 3))
    parts.append(tc.tag(_ball(8, 5, 0.009, (0, 0, -0.53)), 3))            # rope knot
    # eyebolt on top of the magnet
    parts.append(tc.tag(_torus(0.012, 0.003, 10, 4, (0, 0, -0.545), (radians(90), 0, 0)), 4))
    # magnet: red housing on top, nickel pot body, chamfered base, steel band
    parts.append(tc.tag(_cyl(16, 0.090, 0.020, (0, 0, -0.558)), 1))
    parts.append(tc.tag(_cyl(16, 0.100, 0.064, (0, 0, -0.600)), 0))
    parts.append(tc.tag(_cone(16, 0.085, 0.100, 0.012, (0, 0, -0.638)), 0))
    parts.append(tc.tag(_torus(0.100, 0.004, 16, 4, (0, 0, -0.600)), 4))
    return parts
