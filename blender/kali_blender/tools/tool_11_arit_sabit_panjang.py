"""Arit sabit panjang - long grass sickle: 1.5 m wooden pole, metal ferrule with rivets,
crescent steel blade at +Z whose plane contains the pole axis (XZ plane).

Grip at the origin (black wrap) ~0.4 m above the butt cap.
"""
import bpy  # must be first
import bmesh
from math import cos, radians, sin
from mathutils import Vector
from kali_blender import tools_common as tc

SPEC = {
    "index": 11,
    "name": "SM_Tool_AritSabitPanjang",
    "label": "Arit sabit panjang (long grass sickle)",
    "head_dir": "+Z",
    "palette": [
        ("#9a6b3a", 0.0, 0.35),   # 0 wooden pole
        ("#c8ced6", 1.0, 0.75),   # 1 polished steel blade
        ("#5a6068", 1.0, 0.45),   # 2 ferrule, rivets, butt cap
        ("#1e1e1e", 0.0, 0.30),   # 3 black grip wrap
    ],
}

POLE_BOT, POLE_TOP = -0.40, 1.10
BLADE_C = (-0.28, 0.70)     # centre of the crescent arcs (x, z)
BLADE_RO, BLADE_RI = 0.52, 0.42
HALF_T = 0.003              # half blade thickness along Y


def _add(op, **kw):
    getattr(bpy.ops.mesh, "primitive_%s_add" % op)(**kw)
    return bpy.context.object


def _cyl(loc, r, depth, verts, rot=(0, 0, 0)):
    return _add("cylinder", vertices=verts, radius=r, depth=depth, end_fill_type="NGON",
                location=loc, rotation=rot)


def _crescent(angles_deg):
    """Crescent polygon in the XZ plane: outer arc (spine) then inner arc (edge), back again."""
    cx, cz = BLADE_C
    outer = [(cx + BLADE_RO * cos(radians(a)), cz + BLADE_RO * sin(radians(a))) for a in angles_deg]
    inner = [(cx + BLADE_RI * cos(radians(a)), cz + BLADE_RI * sin(radians(a))) for a in reversed(angles_deg)]
    return outer + inner


def _prism(pts, half_t):
    """Extrude a closed XZ polygon symmetrically along Y into a solid mesh object."""
    bm = bmesh.new()
    front = [bm.verts.new((x, -half_t, z)) for x, z in pts]
    back = [bm.verts.new((x, half_t, z)) for x, z in pts]
    bm.faces.new(front)
    bm.faces.new(list(reversed(back)))
    n = len(pts)
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new([front[i], front[j], back[j], back[i]])
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new("AritBlade")
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new("AritBlade", me)
    bpy.context.scene.collection.objects.link(obj)
    return obj


def build():
    parts = []

    # wooden pole, butt at -0.4 m, grip ~0.4 m above it, top under the ferrule
    pole_len = POLE_TOP - POLE_BOT
    parts.append(tc.tag(_cyl((0, 0, (POLE_TOP + POLE_BOT) / 2), 0.017, pole_len, 12), 0))

    # black grip wrap around the origin (hand grip)
    parts.append(tc.tag(_cyl((0, 0, 0.01), 0.021, 0.12, 10), 3))

    # steel butt cap
    parts.append(tc.tag(_cyl((0, 0, POLE_BOT + 0.005), 0.019, 0.01, 10), 2))

    # metal ferrule wrapping the pole top where the blade is seated
    parts.append(tc.tag(_cyl((0, 0, 0.99), 0.024, 0.22, 10), 2))
    # two rivets through the ferrule, one each side of the blade seat
    for z in (0.94, 1.05):
        parts.append(tc.tag(_cyl((0.0, 0.0, z), 0.0045, 0.012, 6, rot=(0, radians(90), 0)), 2)
                     if False else tc.tag(_cyl((0.026, 0.0, z), 0.0045, 0.006, 6, rot=(0, radians(90), 0)), 2))
        parts.append(tc.tag(_cyl((-0.026, 0.0, z), 0.0045, 0.006, 6, rot=(0, radians(90), 0)), 2))

    # crescent steel blade, curving out from the ferrule and hooking back over the top
    blade_pts = _crescent(list(range(10, 91, 5)))
    blade = _prism(blade_pts, HALF_T)
    parts.append(tc.tag(blade, 1))
    return parts
