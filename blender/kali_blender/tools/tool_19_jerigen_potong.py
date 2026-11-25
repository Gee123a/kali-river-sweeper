import bpy  # must be first
import bmesh
from math import radians
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 19,
    "name": "SM_Tool_JerigenPotong",
    "label": "Jerigen potong (cut jerrycan scoop)",
    "head_dir": "-Z",
    "palette": [
        ("#b8322a", 0.0, 0.35),   # red HDPE can
        ("#ececec", 0.0, 0.50),   # white label panel
        ("#1d1d1d", 0.0, 0.30),   # black moulded handle
        ("#3a3d40", 0.0, 0.40),   # dark screw cap
    ],
}

# Can outer half-sizes (m) and centre height. Top at z=-0.02, bottom at z=-0.38.
HX, HY, HZ = 0.13, 0.08, 0.18
ZC = -0.20
WALL = 0.012          # wall thickness of the hollow can


def _bm_obj(bm, name):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    me.update()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def _cyl(n, r, d, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=d, location=loc, rotation=rot)
    return bpy.context.object


def _box(size, loc):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.scale = size
    return obj


def _add_shell(bm, hx, hy, hz, inward):
    """Add a bevelled box with half-sizes (hx, hy, hz). inward=True flips the normals so it
    reads as the inside surface of the can wall."""
    before = set(bm.faces)
    bmesh.ops.create_cube(bm, size=1.0)
    new_faces = [f for f in bm.faces if f not in before]
    new_verts = {v for f in new_faces for v in f.verts}
    for v in new_verts:
        v.co = Vector((v.co.x * 2 * hx, v.co.y * 2 * hy, v.co.z * 2 * hz + ZC))
    if inward:
        bmesh.ops.reverse_faces(bm, faces=new_faces)
    edges = list({e for f in new_faces for e in f.edges})
    bmesh.ops.bevel(bm, geom=edges, offset=0.010, segments=2, affect='EDGES')


def _can_body():
    """Hollow 20 L can with a diagonal scoop opening on the -Y face.

    The plane runs from the top front edge (y=-0.08, z=-0.02) down to the bottom
    at y=+0.04, and everything on the front-bottom side of it is removed from both the
    outer skin and the inner skin. The open edge is bridged by a rim band of wall thickness,
    so the cavity is visible through the opening."""
    bm = bmesh.new()
    _add_shell(bm, HX, HY, HZ, inward=False)
    _add_shell(bm, HX - WALL, HY - WALL, HZ - WALL, inward=True)
    normal = Vector((0.0, -0.36, -0.12)).normalized()
    origin = Vector((0.0, -0.08, -0.02))
    geom = list(bm.verts) + list(bm.edges) + list(bm.faces)
    bmesh.ops.bisect_plane(bm, geom=geom, plane_co=origin, plane_no=normal,
                           clear_outer=True)
    # bridge the outer and inner cut edges into a rim band
    bounds = [e for e in bm.edges if len(e.link_faces) == 1]
    if bounds:
        bmesh.ops.bridge_loops(bm, edges=bounds)
    return _bm_obj(bm, "jerigen_can")


def build():
    parts = []
    parts.append(tc.tag(_can_body(), 0))
    # white label on the +X side, which faces the preview camera
    parts.append(tc.tag(_box((0.004, 0.07, 0.06), (HX + 0.002, 0.0, ZC)), 1))
    # three short moulded ribs on the back half of the -X side (clear of the scoop cut)
    for z in (-0.12, -0.20, -0.28):
        parts.append(tc.tag(_box((0.006, 0.05, 0.012), (-0.134, 0.045, z)), 0))
    # moulded carry handle: bar along X at the origin, two posts into the can top
    parts.append(tc.tag(_cyl(12, 0.013, 0.20, (0, 0, 0.03), rot=(0, radians(90), 0)), 2))
    parts.append(tc.tag(_cyl(8, 0.011, 0.05, (-0.09, 0, 0.0)), 2))
    parts.append(tc.tag(_cyl(8, 0.011, 0.05, (0.09, 0, 0.0)), 2))
    # screw spout on the back (+Y) top corner, with its cap
    parts.append(tc.tag(_cyl(12, 0.016, 0.03, (0.07, 0.05, -0.005)), 0))
    parts.append(tc.tag(_cyl(12, 0.020, 0.014, (0.07, 0.05, 0.017)), 3))
    return parts
