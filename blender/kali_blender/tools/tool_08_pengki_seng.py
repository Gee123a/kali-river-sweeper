import bpy  # must be first
import bmesh  # noqa: F401
from math import cos, radians, sin
from mathutils import Euler, Matrix, Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 8,
    "name": "SM_Tool_PengkiSeng",
    "label": "Pengki seng (zinc dustpan)",
    "head_dir": "+Z",
    "palette": [
        ("#b9c2c9", 0.9, 0.55),   # 0 galvanised zinc sheet
        ("#8b5a2b", 0.0, 0.3),    # 1 round wooden handle
        ("#5a6168", 0.9, 0.4),    # 2 rivet heads and seams
        ("#9aa4ad", 0.85, 0.5),   # 3 riveted tin collar
    ],
}

# Handle axis is offset by its radius so the grip origin lies on the handle surface.
HX = -0.016
# Back-wall centre: where the handle enters the pan. Pan parts tilt about this point.
PIVOT = Vector((HX, 0.0, 0.25))
TILT = radians(-12)
_ROT = Matrix.Rotation(TILT, 3, "Y")


def _pan_place(loc, rot=(0.0, 0.0, 0.0)):
    off = _ROT @ (Vector(loc) - PIVOT)
    m = _ROT @ Euler(rot).to_matrix()
    return tuple(PIVOT + off), tuple(m.to_euler())


def _cyl(verts, radius, depth, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    return bpy.context.object


def _box(size, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.scale = size
    return obj


def _sphere(radius, loc):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=radius, location=loc)
    return bpy.context.object


def _pan_box(size, loc, rot=(0.0, 0.0, 0.0)):
    loc, rot = _pan_place(loc, rot)
    return _box(size, loc, rot)


def _pan_cyl(radius, depth, loc, rot=(0.0, 0.0, 0.0), verts=8):
    loc, rot = _pan_place(loc, rot)
    return _cyl(verts, radius, depth, loc, rot)


def build():
    parts = []
    # 0.35 m round wooden handle, z -0.10 .. 0.25, origin on its surface
    parts.append(tc.tag(_cyl(12, 0.016, 0.35, (HX, 0.0, 0.075)), 1))
    # tin collar where the handle enters the middle of the back wall
    parts.append(tc.tag(_cyl(16, 0.022, 0.06, (HX, 0.0, 0.25)), 3))
    for ang in (0, 90, 180, 270):
        x, y = HX + 0.022 * cos(radians(ang)), 0.022 * sin(radians(ang))
        parts.append(tc.tag(_sphere(0.004, (x, y, 0.262)), 2))

    # pan lies in line with the handle: floor extends from the back wall toward +Z
    parts.append(tc.tag(_pan_box((0.006, 0.30, 0.28), (0.0, 0.0, 0.39)), 0))       # floor
    for y in (-0.15, 0.15):                                                         # side walls
        parts.append(tc.tag(_pan_box((0.08, 0.006, 0.28), (0.04, y, 0.39)), 0))
    parts.append(tc.tag(_pan_box((0.08, 0.30, 0.006), (HX, 0.0, 0.25)), 0))        # back wall
    parts.append(tc.tag(_pan_cyl(0.006, 0.30, (0.0, 0.0, 0.53), (radians(90), 0, 0), 10), 2))  # open front lip

    # folded seams along the floor-wall junctions and the back wall
    for y in (-0.15, 0.15):
        parts.append(tc.tag(_pan_cyl(0.005, 0.28, (0.0, y, 0.39)), 2))
    parts.append(tc.tag(_pan_cyl(0.005, 0.30, (0.0, 0.0, 0.25), (radians(90), 0, 0)), 2))
    return parts
