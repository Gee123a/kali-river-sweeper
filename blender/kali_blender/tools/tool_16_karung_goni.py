import bpy  # must be first
import bmesh  # noqa: F401
from math import pi, sin, cos
from kali_blender import tools_common as tc

SPEC = {
    "index": 16,
    "name": "SM_Tool_KarungGoni",
    "label": "Karung goni (burlap sack)",
    "head_dir": "-Z",
    "palette": [
        ("#a8895a", 0.0, 0.08),   # jute burlap
        ("#b0302a", 0.0, 0.20),   # red stencil band
        ("#6e5536", 0.0, 0.10),   # rope
    ],
}


def _mesh_obj(name, verts, faces):
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _lathe(name, profile, segs, lump=None, twist=None):
    """Closed surface of revolution. profile = [(radius, z), ...] bottom to top."""
    verts, faces, rings = [], [], []
    for r, z in profile:
        ring = []
        for i in range(segs):
            th = 2 * pi * i / segs
            rr = r * (lump(th, z) if lump else 1.0)
            tw = th + (twist(z) if twist else 0.0)
            ring.append(len(verts))
            verts.append((rr * cos(tw), rr * sin(tw), z))
        rings.append(ring)
    for a, b in zip(rings, rings[1:]):
        for i in range(segs):
            j = (i + 1) % segs
            faces.append((a[i], a[j], b[j], b[i]))
    for ring, z in ((rings[0], profile[0][1]), (rings[-1], profile[-1][1])):
        c = len(verts)
        verts.append((0.0, 0.0, z))
        for i in range(segs):
            faces.append((c, ring[i], ring[(i + 1) % segs]))
    return _mesh_obj(name, verts, faces)


def _lump(th, z):
    # irregular bulge of a stuffed sack
    return 1.0 + 0.05 * sin(3 * th + 9 * z) + 0.035 * cos(5 * th - 6 * z)


BODY_PROFILE = [
    (0.09, -0.70), (0.16, -0.675), (0.19, -0.62), (0.20, -0.54), (0.20, -0.44),
    (0.19, -0.33), (0.165, -0.22), (0.12, -0.13), (0.075, -0.07), (0.055, -0.035),
]
BAND_PROFILE = [(0.19, -0.47), (0.212, -0.455), (0.212, -0.405), (0.19, -0.39)]
NECK_PROFILE = [(0.05, -0.04), (0.035, 0.0), (0.025, 0.025), (0.018, 0.045)]


def build():
    parts = []
    # lumpy sack body, sitting below the grip
    parts.append(tc.tag(_lathe("sack_body", BODY_PROFILE, 12, lump=_lump), 0))
    # second-colour stencil band wrapped round the body
    parts.append(tc.tag(_lathe("sack_band", BAND_PROFILE, 12, lump=_lump), 1))
    # gathered neck, twisted, held at the origin
    parts.append(tc.tag(_lathe("sack_neck", NECK_PROFILE, 8,
                               twist=lambda z: 30.0 * (z + 0.04)), 0))
    # two rope turns tying the neck
    for z, major in ((-0.012, 0.041), (0.012, 0.031)):
        bpy.ops.mesh.primitive_torus_add(major_segments=12, minor_segments=4,
                                         major_radius=major, minor_radius=0.006,
                                         location=(0, 0, z))
        parts.append(tc.tag(bpy.context.object, 2))
    # loose rope tail sticking out of the knot
    bpy.ops.mesh.primitive_cylinder_add(vertices=6, radius=0.004, depth=0.07,
                                        location=(0.028, 0, 0.045), rotation=(0, 0.6, 0))
    parts.append(tc.tag(bpy.context.object, 2))
    return parts
