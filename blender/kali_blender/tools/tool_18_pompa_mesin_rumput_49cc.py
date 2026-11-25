import bpy  # must be first
import bmesh  # noqa: F401
from math import radians, cos, sin
from kali_blender import tools_common as tc

SPEC = {
    "index": 18,
    "name": "SM_Tool_PompaMesinRumput49cc",
    "label": "Pompa mesin rumput 49cc (49cc brush-cutter vacuum pump)",
    "head_dir": "-Z",
    "palette": [
        ("#c62828", 0.2, 0.45),   # 0 red cylinder head and fins
        ("#9aa3ab", 0.9, 0.55),   # 1 aluminium muffler, impeller housing, nozzle
        ("#1c1c1c", 0.0, 0.30),   # 2 black D-handle, trigger and starter knob
        ("#2b2f33", 0.5, 0.35),   # 3 dark crankcase and impeller
        ("#e8b400", 0.0, 0.40),   # 4 yellow fuel tank
        ("#2a2a2a", 0.0, 0.60),   # 5 corrugated rubber suction hose
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
    # D-shaped top grip: bar through the origin, two stubs down into the engine pod
    parts.append(tc.tag(_cyl(10, 0.014, 0.24, (0, 0, 0), (0, radians(90), 0)), 2))
    for x in (-0.12, 0.12):
        parts.append(tc.tag(_cyl(10, 0.013, 0.06, (x, 0, -0.03)), 2))
    parts.append(tc.tag(_box((0.03, 0.03, 0.05), (0, -0.03, -0.03)), 2))      # throttle trigger

    # 49cc engine pod: crankcase, red finned head, fuel tank, muffler, starter knob
    parts.append(tc.tag(_cyl(12, 0.042, 0.10, (0, 0, -0.21)), 3))
    parts.append(tc.tag(_cyl(12, 0.050, 0.06, (0, 0, -0.12)), 0))
    for z in (-0.10, -0.12, -0.14, -0.16):
        parts.append(tc.tag(_cyl(12, 0.062, 0.007, (0, 0, z)), 0))           # cooling fins
    parts.append(tc.tag(_box((0.09, 0.06, 0.06), (0.075, 0, -0.14)), 4))     # fuel tank
    parts.append(tc.tag(_cyl(10, 0.028, 0.05, (-0.06, 0.02, -0.17), (0, radians(90), 0)), 1))
    parts.append(tc.tag(_cyl(10, 0.010, 0.02, (0, -0.055, -0.23), (radians(90), 0, 0)), 2))

    # volute impeller housing (snail shape): main casing, offset scroll, outlet spout
    parts.append(tc.tag(_cyl(14, 0.072, 0.06, (0, 0, -0.33)), 1))
    parts.append(tc.tag(_cyl(14, 0.050, 0.06, (0.022, 0.0, -0.33)), 1))
    parts.append(tc.tag(_cyl(12, 0.010, 0.02, (0, 0, -0.27)), 3))            # impeller hub cap
    parts.append(tc.tag(_cyl(12, 0.011, 0.028, (0, 0, -0.31)), 3))
    parts.append(tc.tag(_cyl(10, 0.030, 0.012, (0, 0, -0.37)), 3))           # impeller rim
    parts.append(tc.tag(_cyl(10, 0.015, 0.04, (0.04, -0.03, -0.33), (0, radians(90), 0)), 1))

    # corrugated spiral suction hose: a helix of rings around a short core
    parts.append(tc.tag(_cyl(8, 0.013, 0.04, (0, 0, -0.41)), 5))             # hose neck
    z = -0.43
    i = 0
    while z > -1.12:
        theta = i * 0.9
        ox, oy = 0.012 * cos(theta), 0.012 * sin(theta)
        parts.append(tc.tag(_cyl(6, 0.019, 0.013, (round(ox, 4), round(oy, 4), round(z, 4))), 5))
        z -= 0.065
        i += 1

    # flared suction nozzle with a rolled lip at the bottom
    parts.append(tc.tag(_cone(12, 0.045, 0.016, 0.13, (0, 0, -1.22)), 1))
    parts.append(tc.tag(_torus(0.045, 0.005, 12, 4, (0, 0, -1.285)), 1))
    return parts
