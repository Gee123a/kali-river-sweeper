import bpy  # must be first
import bmesh
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 10,
    "name": "SM_Tool_SekopKecil",
    "label": "Sekop kecil (small shovel)",
    "head_dir": "+Z",
    "palette": [
        ("#9aa3ab", 0.9, 0.5),    # 0 steel blade
        ("#a0692c", 0.0, 0.3),    # 1 wooden shaft
        ("#7b848c", 0.9, 0.45),   # 2 steel socket
        ("#303030", 0.0, 0.3),    # 3 D-grip
        ("#4a4f55", 0.8, 0.35),   # 4 foot tread lip
    ],
}


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


def _blade(loc):
    """Upper half of a flattened sphere, tapered toward a point: a dished, pointed blade."""
    bpy.ops.mesh.primitive_uv_sphere_add(segments=16, ring_count=8, radius=1.0, location=loc)
    obj = bpy.context.object
    obj.scale = (0.09, 0.03, 0.14)
    me = obj.data
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if v.co.z < -1e-6], context="VERTS")
    for v in bm.verts:
        v.co.x *= 1.0 - 0.45 * v.co.z
    bm.to_mesh(me)
    bm.free()
    return obj


def build():
    parts = []
    # D-grip loop in the XZ plane, its top arc passing through the origin
    parts.append(tc.tag(_torus(0.055, 0.012, 12, 8, (0, 0, -0.055), (radians(90), 0, 0)), 3))
    # wooden shaft from the grip up to the socket
    parts.append(tc.tag(_cyl(14, 0.014, 0.50, (0, 0, 0.25)), 1))
    # tapered steel socket
    parts.append(tc.tag(_cone(12, 0.022, 0.016, 0.14, (0, 0, 0.55)), 2))
    # pointed dished blade at +Z
    parts.append(tc.tag(_blade((0, 0, 0.62)), 0))
    # foot tread lip across the blade shoulder
    parts.append(tc.tag(_cyl(12, 0.008, 0.18, (0, 0.035, 0.66), (0, radians(90), 0)), 4))
    return parts
