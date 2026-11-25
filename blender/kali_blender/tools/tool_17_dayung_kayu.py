import bpy  # must be first
import bmesh
from math import radians
from kali_blender import tools_common as tc

SPEC = {
    "index": 17,
    "name": "SM_Tool_DayungKayu",
    "label": "Dayung kayu (wooden paddle)",
    "head_dir": "+Z",
    "palette": [
        ("#b07a45", 0.0, 0.30),   # pale wood shaft / blade
        ("#6b4023", 0.0, 0.45),   # dark varnished ridge
        ("#202020", 0.0, 0.20),   # black tape wrap and T-grip
        ("#9aa1a8", 0.9, 0.50),   # aluminium ferrule
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


def _flat_plate(name, loop, half):
    """Flat outline (x, z) extruded symmetrically in Y by +/- half."""
    bm = bmesh.new()
    front = [bm.verts.new((x, half, z)) for x, z in loop]
    back = [bm.verts.new((x, -half, z)) for x, z in loop]
    bm.faces.new(front)
    bm.faces.new(back[::-1])
    n = len(loop)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((front[i], front[j], back[j], back[i]))
    bmesh.ops.triangulate(bm, faces=bm.faces[:])
    return _bm_obj(bm, name)


def _cyl(n, r, d, loc, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cylinder_add(vertices=n, radius=r, depth=d, location=loc, rotation=rot)
    return bpy.context.object


def _ball(r, loc):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=8, ring_count=6, radius=r, location=loc)
    return bpy.context.object


def _box(size, loc):
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=loc)
    obj = bpy.context.object
    obj.scale = size
    return obj


# Blade outline in (x, z): neck at z=0.55, rounded tip at z=1.05 (0.5 m long, 0.18 m wide).
# The right-hand top corner is chipped to show a worn tip.
BLADE_LOOP = [
    (-0.02, 0.55), (-0.06, 0.62), (-0.09, 0.72), (-0.09, 0.85), (-0.085, 0.95),
    (-0.07, 1.02), (-0.03, 1.05), (0.02, 1.04), (0.05, 1.00), (0.075, 0.97),
    (0.085, 0.90), (0.09, 0.80), (0.09, 0.72), (0.06, 0.62), (0.02, 0.55),
]


def build():
    parts = []
    # round shaft; grip at the origin, butt at z=-0.34
    parts.append(tc.tag(_cyl(12, 0.016, 0.90, (0, 0, 0.11)), 0))
    # flat blade with its neck inside the shaft top
    parts.append(tc.tag(_flat_plate("paddle_blade", BLADE_LOOP, 0.0125), 0))
    # raised ridge running down the blade face
    parts.append(tc.tag(_box((0.012, 0.006, 0.40), (0, 0.0155, 0.80)), 1))
    # black tape wrap around the hand grip
    parts.append(tc.tag(_cyl(12, 0.020, 0.10, (0, 0, 0)), 2))
    # aluminium ferrule where the blade meets the shaft
    parts.append(tc.tag(_cyl(12, 0.021, 0.02, (0, 0, 0.55)), 3))
    # T-grip at the butt: crossbar plus two rounded knobs
    parts.append(tc.tag(_cyl(10, 0.016, 0.16, (0, 0, -0.35), rot=(0, radians(90), 0)), 2))
    parts.append(tc.tag(_ball(0.022, (-0.08, 0, -0.35)), 2))
    parts.append(tc.tag(_ball(0.022, (0.08, 0, -0.35)), 2))
    return parts
