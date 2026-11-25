import bpy  # must be first
import bmesh  # noqa: F401
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 17,
    "name": "SM_Tool_SenapanPanahTali",
    "label": "Senapan panah tali (pneumatic harpoon launcher)",
    "head_dir": "+Z",
    "palette": [
        ("#1f1f22", 0.0, 0.30),   # 0 black polymer grip, trigger guard and pump
        ("#b8bec6", 0.9, 0.60),   # 1 aluminium barrel and muzzle
        ("#2e5d7a", 0.5, 0.40),   # 2 blue painted air reservoir
        ("#d8d2c0", 0.0, 0.20),   # 3 fabric line
        ("#8c939b", 1.0, 0.70),   # 4 steel harpoon dart and barbs
        ("#e8702a", 0.0, 0.35),   # 5 orange reel spool
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
    obj.rotation_euler = rot
    return obj


def _cone(verts, r1, r2, depth, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cone_add(vertices=verts, radius1=r1, radius2=r2, depth=depth,
                                    location=loc, rotation=rot)
    return bpy.context.object


def _ball(seg, rings, r, loc):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=seg, ring_count=rings, radius=r, location=loc)
    return bpy.context.object


def _torus(major, minor, maj_seg, min_seg, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=maj_seg, minor_segments=min_seg,
                                     location=loc, rotation=rot)
    return bpy.context.object


def _seg(p0, p1, r, n=4):
    """Thin cylinder from point p0 to point p1 (the line from reel to dart)."""
    from mathutils import Vector
    a, b = Vector(p0), Vector(p1)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=d.length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return obj


def build():
    parts = []
    # pistol grip along Z, origin inside the grip
    parts.append(tc.tag(_cyl(12, 0.020, 0.14, (0, 0, -0.04)), 0))
    parts.append(tc.tag(_cyl(12, 0.021, 0.010, (0, 0, -0.105)), 0))       # grip butt cap
    # trigger guard: small loop in front of the grip
    parts.append(tc.tag(_torus(0.022, 0.0035, 10, 4, (0, 0.012, 0.005), (0, radians(90), 0)), 0))
    # barrel 0.9 m running to +Z, with aluminium muzzle collar
    parts.append(tc.tag(_cyl(12, 0.016, 0.90, (0, 0, 0.48)), 1))
    parts.append(tc.tag(_cyl(12, 0.020, 0.020, (0, 0, 0.14)), 1))         # receiver collar
    parts.append(tc.tag(_cyl(12, 0.020, 0.024, (0, 0, 0.93)), 1))         # muzzle collar
    # blue air reservoir tube underneath the barrel (-Y side), with end caps
    parts.append(tc.tag(_cyl(12, 0.020, 0.56, (0, -0.036, 0.42)), 2))
    parts.append(tc.tag(_ball(8, 4, 0.020, (0, -0.036, 0.14)), 2))
    parts.append(tc.tag(_ball(8, 4, 0.020, (0, -0.036, 0.70)), 2))
    # pump slide: rod across the barrel with a knob
    parts.append(tc.tag(_cyl(8, 0.006, 0.09, (0, -0.045, 0.56), (radians(90), 0, 0)), 0))
    parts.append(tc.tag(_box((0.03, 0.03, 0.04), (0, -0.095, 0.56)), 0))
    # rope reel spool on the +X side near the grip, with its bracket
    parts.append(tc.tag(_cyl(12, 0.012, 0.030, (0.040, 0, 0.09), (0, radians(90), 0)), 5))
    parts.append(tc.tag(_cyl(12, 0.026, 0.004, (0.060, 0, 0.09), (0, radians(90), 0)), 5))
    parts.append(tc.tag(_cyl(12, 0.026, 0.004, (0.020, 0, 0.09), (0, radians(90), 0)), 5))
    parts.append(tc.tag(_box((0.012, 0.008, 0.04), (0.024, 0, 0.05)), 0))
    # harpoon dart protruding from the muzzle with barbed tip
    parts.append(tc.tag(_cyl(6, 0.004, 0.16, (0, 0, 1.00)), 4))
    parts.append(tc.tag(_cone(8, 0.010, 0.0, 0.05, (0, 0, 1.11)), 4))
    parts.append(tc.tag(_cone(6, 0.008, 0.0, 0.02, (0.0, 0.0, 1.06), (radians(90), 0, 0)), 4))
    # fabric line from the reel to the dart
    parts.append(tc.tag(_seg((0.040, 0, 0.09), (0, 0, 1.00), 0.0015), 3))
    return parts
