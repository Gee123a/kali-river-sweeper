import bpy  # must be first
import bmesh
from math import radians, cos, sin
from kali_blender import tools_common as tc

SPEC = {
    "index": 20,
    "name": "SM_Tool_GuntingDahan",
    "label": "Gunting dahan (lopper shears)",
    "head_dir": "+Z",
    "palette": [
        ("#9aa3ad", 1.0, 0.50),   # steel handles
        ("#1c1c1c", 0.0, 0.20),   # black rubber grips
        ("#4a4f55", 0.9, 0.40),   # pivot bolt and nuts
        ("#e6e9ec", 1.0, 0.90),   # bright cutting blade
        ("#6b7178", 1.0, 0.45),   # hooked anvil
    ],
}


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


def _box(size, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc, rotation=rot)
    obj = bpy.context.object
    obj.scale = size
    return obj


PIVOT = (0.0, 0.12)   # pivot bolt position in (x, z); bolt runs along Y


def _outline_plate(name, loop, y0, y1):
    """Flat outline (x, z) extruded along Y from y0 to y1."""
    bm = bmesh.new()
    front = [bm.verts.new((x, y1, z)) for x, z in loop]
    back = [bm.verts.new((x, y0, z)) for x, z in loop]
    bm.faces.new(front)
    bm.faces.new(back[::-1])
    n = len(loop)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return _bm_obj(bm, name)


# Hooked anvil: rises from the pivot and curls over to the right, its tip meeting the blade tip.
ANVIL_LOOP = [
    (-0.035, 0.12), (-0.030, 0.22), (-0.020, 0.30), (0.010, 0.340), (0.060, 0.350),
    (0.100, 0.335), (0.105, 0.315), (0.060, 0.322), (0.025, 0.308), (0.005, 0.275),
    (0.010, 0.200), (0.025, 0.120),
]


def _arc_plate(name, centre, r_in, r_out, a0, a1, y0, y1, steps=10):
    """Curved band of plate (arc between radii r_in/r_out, angles a0->a1 in degrees),
    extruded along Y from y0 to y1."""
    cx, cz = centre
    outer, inner = [], []
    for k in range(steps + 1):
        a = radians(a0 + (a1 - a0) * k / steps)
        outer.append((cx + r_out * cos(a), cz + r_out * sin(a)))
        inner.append((cx + r_in * cos(a), cz + r_in * sin(a)))
    loop = outer + inner[::-1]
    bm = bmesh.new()
    front = [bm.verts.new((x, y1, z)) for x, z in loop]
    back = [bm.verts.new((x, y0, z)) for x, z in loop]
    bm.faces.new(front)
    bm.faces.new(back[::-1])
    n = len(loop)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return _bm_obj(bm, name)


def build():
    parts = []
    # two long steel handles, closed and nearly parallel, pivoting at z=0.12
    parts.append(tc.tag(_cyl(10, 0.009, 0.44, (0, 0.025, -0.10)), 0))
    parts.append(tc.tag(_cyl(10, 0.009, 0.44, (0, -0.025, -0.10)), 0))
    # rubber grips; the origin sits on the grip at y=-0.025
    parts.append(tc.tag(_cyl(12, 0.017, 0.28, (0, 0.025, -0.14)), 1))
    parts.append(tc.tag(_cyl(12, 0.017, 0.28, (0, -0.025, -0.14)), 1))
    # pivot bolt through both handles, with hex nuts at each end
    parts.append(tc.tag(_cyl(10, 0.008, 0.07, (PIVOT[0], 0, PIVOT[1]),
                             rot=(radians(90), 0, 0)), 2))
    parts.append(tc.tag(_cyl(6, 0.011, 0.012, (PIVOT[0], 0.040, PIVOT[1]),
                             rot=(radians(90), 0, 0)), 2))
    parts.append(tc.tag(_cyl(6, 0.011, 0.012, (PIVOT[0], -0.040, PIVOT[1]),
                             rot=(radians(90), 0, 0)), 2))
    # curved cutting blade rising from the pivot to the right (arc centred at (0.20, 0.12))
    parts.append(tc.tag(_arc_plate("lopper_blade", (0.20, 0.12), 0.19, 0.24, 180, 95,
                                   0.002, 0.010), 3))
    # hooked anvil on the other side of the cut plane, tip curling over to meet the blade
    parts.append(tc.tag(_outline_plate("lopper_anvil", ANVIL_LOOP, -0.010, -0.002), 4))
    return parts
