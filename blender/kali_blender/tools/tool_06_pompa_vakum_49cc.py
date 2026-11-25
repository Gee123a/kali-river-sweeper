import bpy  # must be first
import bmesh  # noqa: F401
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 6,
    "name": "SM_Tool_PompaVakum49cc",
    "label": "Pompa vakum 49cc (49cc suction pump)",
    "head_dir": "-Z",
    "palette": [
        ("#c62828", 0.2, 0.45),   # 0 red cylinder head and fins
        ("#9aa3ab", 0.9, 0.55),   # 1 aluminium muffler, starter disc, nozzle
        ("#1c1c1c", 0.0, 0.3),    # 2 black grip and corrugated hose
        ("#2b2f33", 0.5, 0.35),   # 3 dark crankcase
        ("#e8b400", 0.0, 0.4),    # 4 yellow fuel tank
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
    # D-shaped top grip: bar through the origin, two short stubs down into the engine pod
    parts.append(tc.tag(_cyl(10, 0.014, 0.24, (0, 0, 0), (0, radians(90), 0)), 2))
    for x in (-0.12, 0.12):
        parts.append(tc.tag(_cyl(10, 0.013, 0.06, (x, 0, -0.03)), 2))
    # throttle trigger block under the grip
    parts.append(tc.tag(_box((0.03, 0.03, 0.05), (0, -0.03, -0.03)), 2))

    # 49cc engine pod: dark crankcase, red finned cylinder head, fuel tank, muffler, starter
    parts.append(tc.tag(_cyl(12, 0.042, 0.10, (0, 0, -0.21)), 3))          # crankcase
    parts.append(tc.tag(_cyl(12, 0.050, 0.06, (0, 0, -0.12)), 0))          # cylinder head
    for z in (-0.10, -0.12, -0.14, -0.16):
        parts.append(tc.tag(_cyl(12, 0.062, 0.007, (0, 0, z)), 0))         # cooling fins
    parts.append(tc.tag(_box((0.09, 0.06, 0.06), (0.075, 0, -0.14)), 4))   # fuel tank
    parts.append(tc.tag(_cyl(10, 0.028, 0.05, (-0.06, 0.02, -0.17), (0, radians(90), 0)), 1))  # muffler
    parts.append(tc.tag(_cyl(12, 0.040, 0.018, (0, -0.055, -0.23), (radians(90), 0, 0)), 1))  # starter disc

    # corrugated suction tube: smooth core plus ring segments
    parts.append(tc.tag(_cyl(8, 0.013, 0.90, (0, 0, -0.71)), 2))           # -0.26 .. -1.16
    z = -0.30
    while z > -1.12:
        parts.append(tc.tag(_cyl(8, 0.019, 0.014, (0, 0, round(z, 4))), 2))
        z -= 0.06

    # flared suction nozzle with a rolled lip at the bottom
    parts.append(tc.tag(_cone(12, 0.045, 0.016, 0.13, (0, 0, -1.22)), 1))  # -1.285 .. -1.155
    parts.append(tc.tag(_torus(0.045, 0.005, 12, 4, (0, 0, -1.285)), 1))
    return parts
