import bpy  # must be first
import bmesh  # noqa: F401
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 19,
    "name": "SM_Tool_PenebasGergajiGanda",
    "label": "Penebas gergaji ganda (twin-saw weed slasher)",
    "head_dir": "+Z",
    "palette": [
        ("#b8bec6", 0.9, 0.55),   # 0 aluminium drive shaft and gear head
        ("#1c1c1c", 0.0, 0.30),   # 1 black loop handle and grips
        ("#c62828", 0.2, 0.45),   # 2 red engine cover
        ("#2b2f33", 0.5, 0.35),   # 3 dark engine block and starter
        ("#e8b400", 0.0, 0.40),   # 4 yellow fuel tank
        ("#8c939b", 1.0, 0.65),   # 5 steel serrated blade bars
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


def _torus(major, minor, maj_seg, min_seg, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_torus_add(major_radius=major, minor_radius=minor,
                                     major_segments=maj_seg, minor_segments=min_seg,
                                     location=loc, rotation=rot)
    return bpy.context.object


def build():
    parts = []
    # 1.6 m aluminium drive shaft along Z, origin on the shaft
    parts.append(tc.tag(_cyl(12, 0.0125, 1.68, (0, 0, -0.02)), 0))
    for z in (-0.30, 0.30):
        parts.append(tc.tag(_cyl(12, 0.0155, 0.02, (0, 0, z)), 0))           # joint sleeves

    # loop (bike-style) handle hoop around the grip, with its clamp block
    parts.append(tc.tag(_torus(0.08, 0.008, 16, 5, (0, 0, 0), (0, radians(90), 0)), 1))
    parts.append(tc.tag(_box((0.03, 0.03, 0.05), (0, 0.0, 0.0)), 1))
    parts.append(tc.tag(_cyl(8, 0.008, 0.10, (0.0, 0.0, 0.10), (radians(90), 0, 0)), 1))

    # engine at the butt end (-Z): cover, fuel tank, starter knob, cylinder
    parts.append(tc.tag(_box((0.12, 0.14, 0.16), (0, 0, -0.94)), 2))
    parts.append(tc.tag(_cyl(12, 0.042, 0.08, (0, 0, -1.02)), 3))
    parts.append(tc.tag(_box((0.08, 0.05, 0.05), (0.09, 0.0, -0.92)), 4))
    parts.append(tc.tag(_cyl(10, 0.024, 0.02, (0, -0.085, -0.93), (radians(90), 0, 0)), 3))

    # gear head at +Z: housing and drive collar
    parts.append(tc.tag(_box((0.06, 0.08, 0.10), (0, 0, 0.88)), 0))
    parts.append(tc.tag(_cyl(10, 0.020, 0.03, (0, 0, 0.84)), 0))

    # two parallel reciprocating blade bars (0.5 m) running out along +Z
    for x in (-0.022, 0.022):
        parts.append(tc.tag(_box((0.012, 0.022, 0.50), (x, 0, 1.17)), 5))
        # zig-zag teeth alternating along the +Y and -Y edges of each bar
        for k in range(16):
            z = 0.94 + k * 0.03
            side = 0.012 if k % 2 == 0 else -0.012
            rot = (radians(90), 0, 0) if side > 0 else (radians(-90), 0, 0)
            parts.append(tc.tag(_cone(3, 0.008, 0.0, 0.010, (x, side, z), rot), 5))
    return parts
