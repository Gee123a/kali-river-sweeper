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
    "index": 13,
    "name": "SM_Tool_Golok",
    "label": "Golok (machete)",
    "head_dir": "+Z",
    "palette": [
        ("#7a4e26", 0.0, 0.30),   # 0 wooden handle
        ("#8d949b", 1.0, 0.50),   # 1 steel blade
        ("#5b6168", 0.9, 0.35),   # 2 thicker dark spine
        ("#c9a54a", 1.0, 0.70),   # 3 brass ferrule rings
    ],
}

BLADE = [(-0.010, 0.12), (0.022, 0.12), (0.040, 0.17), (0.050, 0.26),
         (0.046, 0.345), (0.022, 0.40), (0.002, 0.42), (-0.010, 0.36)]


def build():
    parts = []

    # wooden handle with flared pommel, centred on the origin (0.25 m long)
    bm = bmesh.new()
    _lathe(bm, [(0.0, -0.135), (0.026, -0.127), (0.028, -0.115), (0.020, -0.095),
                (0.019, 0.0), (0.019, 0.10), (0.017, 0.118)], segs=12)
    parts.append(_finish(bm, "golok_handle", 0))

    # brass ferrule rings at the top of the handle
    bm = bmesh.new()
    _lathe(bm, [(0.0195, 0.098), (0.0215, 0.101), (0.0215, 0.109), (0.0195, 0.112)], segs=12)
    _lathe(bm, [(0.0185, 0.114), (0.0205, 0.117), (0.0205, 0.121), (0.0185, 0.124)], segs=12)
    parts.append(_finish(bm, "golok_ferrules", 3))

    # broad blade in the XZ plane: flat faces, thinner towards the cutting edge
    bm = bmesh.new()
    bottom, top = [], []
    for x, z in BLADE:
        t = 0.0015 + 0.0035 * min(max((0.050 - x) / 0.060, 0.0), 1.0)
        bottom.append(Vector((x, -t, z)))
        top.append(Vector((x, t, z)))
    _loft(bm, [bottom, top])
    parts.append(_finish(bm, "golok_blade", 1))

    # thicker spine along the back of the blade
    bm = bmesh.new()
    _box(bm, (-0.009, 0.0, 0.245), (0.008, 0.012, 0.24))
    parts.append(_finish(bm, "golok_spine", 2))
    return parts
