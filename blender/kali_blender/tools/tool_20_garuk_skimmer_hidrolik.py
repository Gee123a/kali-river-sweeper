import bpy  # must be first
import bmesh  # noqa: F401
from math import radians
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 20,
    "name": "SM_Tool_GarukSkimmerHidrolik",
    "label": "Garuk skimmer hidrolik (hydraulic bow skimmer rake)",
    "head_dir": "+Z",
    "palette": [
        ("#5b6670", 0.8, 0.40),   # 0 steel boom arms and crossbar
        ("#e5e8ec", 1.0, 0.90),   # 1 chrome hydraulic rods
        ("#d98e04", 0.3, 0.50),   # 2 orange hydraulic barrels
        ("#8a9299", 0.8, 0.30),   # 3 galvanised tines and mesh deflector
        ("#2b2f33", 0.6, 0.35),   # 4 dark hinge pin and brackets
    ],
}

HINGE = Vector((0.0, 0.0, 0.0))


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


def _seg(p0, p1, r, n=8):
    """Cylinder from point p0 to point p1 (boom arms, hydraulic cylinders, deflector wires)."""
    a, b = Vector(p0), Vector(p1)
    d = b - a
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=d.length, location=(a + b) / 2)
    obj = bpy.context.object
    obj.rotation_euler = d.to_track_quat("Z", "Y").to_euler()
    return obj


def _lerp(a, b, t):
    return a + (b - a) * t


def build():
    parts = []
    # hinge pin on the barge bow, along X through the origin, with two brackets
    parts.append(tc.tag(_cyl(10, 0.030, 0.50, (0, 0, 0), (0, radians(90), 0)), 4))
    for x in (-0.22, 0.22):
        parts.append(tc.tag(_box((0.05, 0.08, 0.10), (x, 0, 0.0)), 4))

    # two 2.8 m boom arms from the hinge along +Z, spreading slightly toward the head
    tips = {}
    for side in (-1, 1):
        root = Vector((side * 0.15, 0.0, 0.0))
        tip = Vector((side * 0.60, 0.0, 2.80))
        tips[side] = tip
        parts.append(tc.tag(_seg(root, tip, 0.035, 8), 0))
        # hydraulic cylinder on the outer side of each arm: barrel plus chrome rod
        off = Vector((side * 0.06, -0.06, 0.0))
        b0, b1 = _lerp(root, tip, 0.30) + off, _lerp(root, tip, 0.70) + off
        r1 = _lerp(root, tip, 0.95) + off
        parts.append(tc.tag(_seg(b0, b1, 0.030, 8), 2))
        parts.append(tc.tag(_seg(b1, r1, 0.014, 8), 1))
        parts.append(tc.tag(_box((0.05, 0.05, 0.05), (b0.x, b0.y, b0.z)), 4))  # cylinder end cap

    # rake head at the end of the arms: crossbar 1.8 m wide, with brackets to the arm tips
    cross_z = 2.85
    parts.append(tc.tag(_seg((-0.90, 0.0, cross_z), (0.90, 0.0, cross_z), 0.025, 8), 0))
    for side in (-1, 1):
        t = tips[side]
        parts.append(tc.tag(_seg(t, (t.x, 0.0, cross_z), 0.02, 6), 4))

    # 12 tines on the crossbar, reaching forward along +Z
    n = 12
    for k in range(n):
        x = -0.85 + k * (1.70 / (n - 1))
        parts.append(tc.tag(_cyl(6, 0.008, 0.16, (x, 0.0, cross_z + 0.08)), 3))

    # mesh deflector plate behind the tines: frame plus horizontal and vertical wires
    parts.append(tc.tag(_box((1.80, 0.012, 0.02), (0, -0.05, 2.70)), 3))
    parts.append(tc.tag(_box((1.80, 0.012, 0.02), (0, -0.05, 2.80)), 3))
    parts.append(tc.tag(_box((0.02, 0.012, 0.12), (-0.90, -0.05, 2.75)), 3))
    parts.append(tc.tag(_box((0.02, 0.012, 0.12), (0.90, -0.05, 2.75)), 3))
    for k in range(6):
        x = -0.75 + k * 0.30
        parts.append(tc.tag(_seg((x, -0.05, 2.70), (x, -0.05, 2.80), 0.004, 4), 3))
    return parts
