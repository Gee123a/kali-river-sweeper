"""Sendok makan bengkok - bent stainless dining spoon used to flick caps and sachets.

Grip on the flat handle at the origin; the oval bowl sits at +Z after a ~25 deg bend.
"""
import bpy  # must be first
from math import radians, sin, cos
from kali_blender import tools_common as tc

SPEC = {
    "index": 1,
    "name": "SM_Tool_SendokMakanBengkok",
    "label": "Sendok makan bengkok (bent dining spoon)",
    "head_dir": "+Z",
    "palette": [
        ("#c9ced3", 1.0, 0.80),  # 0 stainless steel
        ("#c8402a", 0.0, 0.40),  # 1 red electrical tape
    ],
}

BEND = radians(25)
D = (sin(BEND), 0.0, cos(BEND))   # direction of the bent section (rotation about Y)
J = (0.0, 0.0, 0.01)              # bend joint, on the handle axis
BOWL_S = 0.065                    # distance from the joint to the bowl centre along D


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _flat_cyl(loc, rx, ry, depth, rot=(0, 0, 0), verts=8):
    """Cylinder with a flattened (elliptical) cross-section along local X/Y."""
    o = _add("cylinder", vertices=verts, radius=1.0, depth=depth, location=loc, rotation=rot)
    o.scale = (rx, ry, 1.0)
    return o


def build():
    parts = []

    # straight flat handle, grip (origin) runs through it
    parts.append(tc.tag(_flat_cyl((0, 0, (-0.075 + J[2]) / 2), 0.0075, 0.0028,
                                  J[2] + 0.075), 0))

    # bent section leading into the bowl (25 deg, in the X-Z plane)
    mid = tuple(J[i] + 0.0325 * D[i] for i in range(3))
    parts.append(tc.tag(_flat_cyl(mid, 0.0075, 0.0028, 0.065, rot=(0, BEND, 0)), 0))

    # small hanging eyelet at the butt end of the handle
    parts.append(tc.tag(_add("torus", major_segments=16, minor_segments=4, major_radius=0.008,
                             minor_radius=0.0022, location=(0, 0, -0.075),
                             rotation=(radians(90), 0, 0)), 0))

    # red electrical tape wrap on the straight handle
    parts.append(tc.tag(_flat_cyl((0, 0, -0.02), 0.0085, 0.0036, 0.03, verts=10), 1))

    # oval bowl (thin in Y, long along the bent direction)
    bowl_c = tuple(J[i] + BOWL_S * D[i] for i in range(3))
    bowl = _add("uv_sphere", segments=12, ring_count=6, radius=1.0, location=bowl_c,
                rotation=(0, BEND, 0))
    bowl.scale = (0.0175, 0.0065, 0.025)
    parts.append(tc.tag(bowl, 0))

    # slight rolled rim around the bowl outline
    rim = _add("torus", major_segments=16, minor_segments=4, major_radius=1.0, minor_radius=0.2,
               location=bowl_c, rotation=(radians(90), BEND, 0))
    rim.scale = (0.0175, 0.0255, 0.02)
    parts.append(tc.tag(rim, 0))

    return parts
