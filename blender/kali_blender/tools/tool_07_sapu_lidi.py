import bpy  # must be first
import bmesh  # noqa: F401
from math import cos, pi, radians, sin
from kali_blender import tools_common as tc

SPEC = {
    "index": 7,
    "name": "SM_Tool_SapuLidi",
    "label": "Sapu lidi (palm-rib broom)",
    "head_dir": "+Z",
    "palette": [
        ("#c9a66b", 0.0, 0.35),   # 0 bamboo handle
        ("#6b4a2a", 0.0, 0.25),   # 1 dried coconut rib, light
        ("#4e3520", 0.0, 0.2),    # 2 dried coconut rib, dark
        ("#9c7a4a", 0.0, 0.15),   # 3 rope bindings
        ("#7d8590", 0.8, 0.45),   # 4 steel ferrule
    ],
}

RIB_LEN = 0.5
NECK = (0.0, 0.0, 0.6)


def _cyl(verts, radius, depth, loc, rot=(0.0, 0.0, 0.0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=verts, radius=radius, depth=depth,
                                        location=loc, rotation=rot)
    return bpy.context.object


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
    # 1.2 m bamboo handle: butt at z=-0.3, grip at origin, top runs up into the bundle
    parts.append(tc.tag(_cyl(12, 0.014, 1.2, (0, 0, 0.3)), 0))
    parts.append(tc.tag(_cyl(12, 0.016, 0.02, (0, 0, -0.29)), 1))          # dark butt cap
    # steel ferrule holding the bundle neck
    parts.append(tc.tag(_cyl(12, 0.020, 0.06, (0, 0, 0.58)), 4))
    # two rope bindings around the bundle neck
    parts.append(tc.tag(_torus(0.030, 0.005, 12, 4, (0, 0, 0.66)), 3))
    parts.append(tc.tag(_torus(0.050, 0.006, 12, 4, (0, 0, 0.76)), 3))

    # palm-rib bundle: 8 clusters of 3 tapered ribs fanning out from the neck
    for k in range(8):
        base_a = k * pi / 4
        for j, tilt in enumerate((0.22, 0.32, 0.42)):
            a = base_a + (j - 1) * radians(5)
            d = (sin(tilt) * cos(a), sin(tilt) * sin(a), cos(tilt))
            centre = (NECK[0] + d[0] * RIB_LEN / 2,
                      NECK[1] + d[1] * RIB_LEN / 2,
                      NECK[2] + d[2] * RIB_LEN / 2)
            swatch = 2 if j == 1 else 1
            parts.append(tc.tag(_cone(8, 0.013, 0.0, RIB_LEN, centre, (0, tilt, a)), swatch))
    return parts
