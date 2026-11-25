import bpy  # must be first
import bmesh  # noqa: E402
from math import cos, sin, pi  # noqa: E402
from mathutils import Vector  # noqa: E402
from kali_blender import tools_common as tc  # noqa: E402


# ---- geometry helpers (bmesh, all in the same bmesh so a part can hold several pieces)
def _loft(bm, rings, caps=True):
    """Connect consecutive closed rings (equal length) with quads; optional end caps."""
    vs = [[bm.verts.new(p) for p in ring] for ring in rings]
    n = len(rings[0])
    for r in range(len(rings) - 1):
        a, b = vs[r], vs[r + 1]
        for i in range(n):
            j = (i + 1) % n
            bm.faces.new((a[i], a[j], b[j], b[i]))
    if caps:
        bm.faces.new(vs[0])
        bm.faces.new(vs[-1])


def _lathe(bm, profile, segs=12, caps=True):
    """Surface of revolution around Z. profile = [(radius, z), ...]; radius 0 = pole."""
    angles = [2 * pi * i / segs for i in range(segs)]
    rings = []
    for r, z in profile:
        if r <= 1e-9:
            rings.append([bm.verts.new((0.0, 0.0, z))])
        else:
            rings.append([bm.verts.new((r * cos(t), r * sin(t), z)) for t in angles])
    for k in range(len(rings) - 1):
        A, B = rings[k], rings[k + 1]
        if len(A) == 1 and len(B) == 1:
            continue
        for i in range(segs):
            j = (i + 1) % segs
            if len(A) == 1:
                bm.faces.new((A[0], B[j], B[i]))
            elif len(B) == 1:
                bm.faces.new((A[i], A[j], B[0]))
            else:
                bm.faces.new((A[i], A[j], B[j], B[i]))
    if caps:
        for ring in (rings[0], rings[-1]):
            if len(ring) > 1:
                bm.faces.new(ring)


def _rod(bm, a, b, r0, r1=None, sides=4, caps=True):
    """Straight tube/prism from point a to b with radius r0 at a and r1 at b."""
    a, b = Vector(a), Vector(b)
    r1 = r0 if r1 is None else r1
    d = (b - a).normalized()
    helper = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
    u = d.cross(helper).normalized()
    v = d.cross(u)

    def ring(c, r):
        return [c + (u * cos(2 * pi * i / sides) + v * sin(2 * pi * i / sides)) * r for i in range(sides)]

    _loft(bm, [ring(a, r0), ring(b, r1)], caps)


def _box(bm, c, size):
    """Axis-aligned box centred on c with size (sx, sy, sz)."""
    x, y, z = c
    sx, sy, sz = size[0] / 2, size[1] / 2, size[2] / 2
    rect = [(x - sx, y - sy), (x + sx, y - sy), (x + sx, y + sy), (x - sx, y + sy)]
    _loft(bm, [[Vector((px, py, z - sz)) for px, py in rect], [Vector((px, py, z + sz)) for px, py in rect]])


def _finish(bm, name, swatch):
    """Turn a bmesh into a tagged scene object (one part)."""
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces[:])
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    obj = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(obj)
    return tc.tag(obj, swatch)


SPEC = {
    "index": 12,
    "name": "SM_Tool_Garu",
    "label": "Garu (garu / rake)",
    "head_dir": "+Z",
    "palette": [
        ("#9a6a3a", 0.0, 0.30),   # 0 wooden handle
        ("#4e545b", 0.9, 0.40),   # 1 dark steel ferrule and bow arms
        ("#b4bac0", 1.0, 0.60),   # 2 bright steel crossbar and tines
        ("#222222", 0.0, 0.20),   # 3 black binding
    ],
}


def build():
    parts = []

    # 1.4 m wooden handle, grip at origin (0.4 m from butt)
    bm = bmesh.new()
    _lathe(bm, [(0.0, -0.40), (0.020, -0.40), (0.024, -0.39), (0.021, -0.37),
                (0.019, 0.0), (0.019, 0.90), (0.021, 0.94)], segs=12)
    parts.append(_finish(bm, "garu_handle", 0))

    # steel ferrule at the top of the handle
    bm = bmesh.new()
    _lathe(bm, [(0.0185, 0.92), (0.0215, 0.93), (0.0215, 0.97), (0.0185, 0.98)], segs=12)
    parts.append(_finish(bm, "garu_ferrule", 1))

    # black binding wrap just below the ferrule
    bm = bmesh.new()
    _lathe(bm, [(0.0195, 0.86), (0.0215, 0.865), (0.0215, 0.88), (0.0195, 0.885)], segs=12)
    parts.append(_finish(bm, "garu_binding", 3))

    # bow arms: from the ferrule out and up to the ends of the crossbar
    bm = bmesh.new()
    for s in (-1, 1):
        _rod(bm, (0.0, 0.0, 0.97), (s * 0.10, -0.02, 1.03), 0.0075)
        _rod(bm, (s * 0.10, -0.02, 1.03), (s * 0.20, 0.0, 1.10), 0.0075)
    parts.append(_finish(bm, "garu_bow", 1))

    # 0.40 m crossbar with 12 curved tines pointing up and forward
    bm = bmesh.new()
    _rod(bm, (-0.20, 0.0, 1.10), (0.20, 0.0, 1.10), 0.009)
    for i in range(12):
        x = -0.1833 + i * (0.3667 / 11)
        _rod(bm, (x, 0.0, 1.10), (x, -0.04, 1.16), 0.0045, 0.0040)
        _rod(bm, (x, -0.04, 1.16), (x, -0.09, 1.19), 0.0040, 0.0025)
    parts.append(_finish(bm, "garu_head", 2))
    return parts
