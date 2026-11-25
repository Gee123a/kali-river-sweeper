"""Centong nasi - plastic rice paddle with a dimpled grid face for skimming lids and wrappers.

Grip on the slim handle at the origin; flat rounded-rectangle blade at +Z with a grid of
raised studs on its front face and a hanging hole at the handle end.
"""
import bpy  # must be first
import bmesh
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 3,
    "name": "SM_Tool_CentongNasi",
    "label": "Centong nasi (rice paddle)",
    "head_dir": "+Z",
    "palette": [
        ("#f3efe4", 0.0, 0.35),  # 0 cream plastic
        ("#b9a98a", 0.0, 0.30),  # 1 darker beige (hanging loop, stud accents)
    ],
}

BLADE_Z0, BLADE_Z1 = 0.10, 0.22
BLADE_W, BLADE_T = 0.08, 0.0032


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _blade():
    """Flat blade: cube scaled to the blade size, then the four edges parallel to Y rounded."""
    zc = (BLADE_Z0 + BLADE_Z1) / 2
    blade = _add("cube", size=1.0, location=(0, 0, zc))
    me = blade.data
    bm = bmesh.new()
    bm.from_mesh(me)
    for v in bm.verts:
        v.co.x *= BLADE_W
        v.co.y *= BLADE_T
        v.co.z *= (BLADE_Z1 - BLADE_Z0)
    edges = [e for e in bm.edges if abs(e.verts[0].co.y - e.verts[1].co.y) > 1e-6]
    bmesh.ops.bevel(bm, geom=edges, offset=0.012, segments=3, affect="EDGES")
    bm.to_mesh(me)
    bm.free()
    return blade


def build():
    parts = []

    # slim handle (origin on its axis)
    handle = _add("cylinder", vertices=8, radius=0.0085, depth=0.13, location=(0, 0, 0.045))
    parts.append(tc.tag(handle, 0))

    # rounded blade
    parts.append(tc.tag(_blade(), 0))

    # dimple grid of raised studs on the front (-Y) face of the blade
    zc = (BLADE_Z0 + BLADE_Z1) / 2
    for ix in (-0.024, 0.0, 0.024):
        for iz in (-0.03, -0.01, 0.01, 0.03):
            stud = _add("cylinder", vertices=6, radius=0.0035, depth=0.0015,
                        location=(ix, -BLADE_T / 2 - 0.0006, zc + iz),
                        rotation=(radians(90), 0, 0))
            parts.append(tc.tag(stud, 1))

    # hanging hole: small loop at the butt end of the handle
    loop = _add("torus", major_segments=12, minor_segments=4, major_radius=0.008,
                minor_radius=0.0022, location=(0, 0, -0.03), rotation=(radians(90), 0, 0))
    parts.append(tc.tag(loop, 1))

    return parts
