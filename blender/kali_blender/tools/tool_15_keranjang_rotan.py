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
    "index": 15,
    "name": "SM_Tool_KeranjangRotan",
    "label": "Keranjang rotan (rattan basket)",
    "head_dir": "-Z",
    "palette": [
        ("#c8a06a", 0.0, 0.35),   # 0 woven rattan wall
        ("#9c6f3e", 0.0, 0.30),   # 1 ribs and arched handle
        ("#7a5230", 0.0, 0.30),   # 2 thick rim
        ("#d7b57f", 0.0, 0.40),   # 3 weave bands
    ],
}

# outer wall (bottom centre -> rim) and inner wall (rim -> floor centre)
OUTER = [(0.127, -0.44), (0.141, -0.425), (0.162, -0.31), (0.176, -0.19)]
INNER = [(0.169, -0.18), (0.155, -0.31), (0.134, -0.425), (0.0, -0.425)]


def _wall_r(z):
    """Outer wall radius at height z (linear between the outer profile points)."""
    for (r0, z0), (r1, z1) in zip(OUTER, OUTER[1:]):
        if z0 <= z <= z1:
            return r0 + (r1 - r0) * (z - z0) / (z1 - z0)
    return OUTER[-1][0]


def build():
    parts = []

    # arched rattan handle: half ellipse from the rim (x = +-0.18) up to the grip at origin
    bm = bmesh.new()
    pts = [Vector((0.18 * cos(pi * k / 8), 0.0, -0.152 + 0.152 * sin(pi * k / 8))) for k in range(9)]
    for a, b in zip(pts, pts[1:]):
        _rod(bm, a, b, 0.0105, sides=6)
    parts.append(_finish(bm, "keranjang_handle", 1))

    # woven body: flared shell with a closed floor
    bm = bmesh.new()
    _lathe(bm, [(0.0, -0.44)] + OUTER + INNER, segs=10, caps=False)
    parts.append(_finish(bm, "keranjang_body", 0))

    # thick rim at the top
    bm = bmesh.new()
    _lathe(bm, [(0.169, -0.184), (0.186, -0.184), (0.190, -0.168), (0.186, -0.152), (0.169, -0.152)],
           segs=10, caps=False)
    parts.append(_finish(bm, "keranjang_rim", 2))

    # horizontal weave bands (ring loops) around the wall
    bm = bmesh.new()
    for z in (-0.39, -0.33, -0.27, -0.22):
        rb = _wall_r(z)
        _lathe(bm, [(rb, z - 0.008), (rb + 0.006, z - 0.003), (rb + 0.006, z + 0.003), (rb, z + 0.008)],
               segs=10, caps=False)
    parts.append(_finish(bm, "keranjang_bands", 3))

    # vertical ribs running from the floor edge up to the rim
    bm = bmesh.new()
    for k in range(10):
        a = 2 * pi * k / 10 + 0.1
        r_bot, r_top = _wall_r(-0.43) + 0.004, _wall_r(-0.19) + 0.004
        _rod(bm, (r_bot * cos(a), r_bot * sin(a), -0.43), (r_top * cos(a), r_top * sin(a), -0.19),
             0.0045, 0.0040)
    parts.append(_finish(bm, "keranjang_ribs", 1))
    return parts
