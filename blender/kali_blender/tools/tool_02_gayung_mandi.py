"""Gayung mandi - classic Indonesian plastic bath dipper.

Solid-walled cup (no holes) with a thick rolled rim. The cup axis is horizontal (opening
faces +Y). A straight plastic handle runs down along -Z from the cup's side wall, near the
rim, to a hollow-looking end ring. The cup sits at the +Z end, beside the handle top, with
its curved side wall tangent to the handle. Grip at the origin on the handle.
"""
import bpy  # must be first
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 2,
    "name": "SM_Tool_GayungMandi",
    "label": "Gayung mandi (bath dipper)",
    "head_dir": "+Z",
    "palette": [
        ("#2e6fb0", 0.0, 0.35),  # 0 blue plastic cup
        ("#1f4f8a", 0.0, 0.30),  # 1 darker handle and web
        ("#e6e3da", 0.0, 0.40),  # 2 off-white rim bead
    ],
}

CUP_R = 0.075
CUP_H = 0.13
HANDLE_R = 0.011
HANDLE_X, HANDLE_Y = 0.0, 0.03          # handle axis (near the rim side, within grip tolerance)
CUP_Z = 0.14                            # cup axis height
CUP_X = HANDLE_X + HANDLE_R + CUP_R     # cup wall tangent to the handle's outer side
H_BOT, H_TOP = -0.08, CUP_Z             # handle runs from the butt up to the cup side (0.22 m)


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def build():
    parts = []

    # cup wall: open tube with its axis along Y (opening faces +Y)
    wall = _add("cylinder", vertices=16, radius=CUP_R, depth=CUP_H, end_fill_type="NOTHING",
                location=(CUP_X, 0, CUP_Z), rotation=(radians(90), 0, 0))
    parts.append(tc.tag(wall, 0))

    # closed base of the cup (the -Y end)
    base = _add("cylinder", vertices=16, radius=CUP_R, depth=0.004,
                location=(CUP_X, -CUP_H / 2 + 0.002, CUP_Z), rotation=(radians(90), 0, 0))
    parts.append(tc.tag(base, 0))

    # thick rolled rim around the opening
    rim = _add("torus", major_segments=16, minor_segments=4, major_radius=CUP_R,
               minor_radius=0.0085, location=(CUP_X, CUP_H / 2, CUP_Z),
               rotation=(radians(90), 0, 0))
    parts.append(tc.tag(rim, 2))

    # straight plastic handle, vertical (Z), attached to the cup's side wall
    handle = _add("cylinder", vertices=10, radius=HANDLE_R, depth=H_TOP - H_BOT,
                  location=(HANDLE_X, HANDLE_Y, (H_TOP + H_BOT) / 2))
    parts.append(tc.tag(handle, 1))

    # hollow-looking end of the handle (ring)
    end_ring = _add("torus", major_segments=12, minor_segments=4, major_radius=0.0115,
                    minor_radius=0.003, location=(HANDLE_X, HANDLE_Y, H_BOT))
    parts.append(tc.tag(end_ring, 1))

    # reinforcing web under the handle joint, bridging handle side and cup underside
    web = _add("cube", size=2, location=(0.024, HANDLE_Y, 0.105))
    web.scale = (0.014, 0.016, 0.014)
    web.rotation_euler = (0, radians(45), 0)
    parts.append(tc.tag(web, 1))

    return parts
