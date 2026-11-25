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
    "index": 11,
    "name": "SM_Tool_Cangkul",
    "label": "Cangkul (cangkul / hoe)",
    "head_dir": "+Z",
    "palette": [
        ("#8b5a2b", 0.0, 0.30),   # 0 wood handle
        ("#5a5f66", 0.9, 0.40),   # 1 dark steel socket
        ("#a7adb4", 1.0, 0.65),   # 2 bright steel blade
        ("#2a2a2a", 0.0, 0.20),   # 3 rubber grip wrap
        ("#5c3a1e", 0.0, 0.25),   # 4 wedge (dark wood)
    ],
}


def _blade_outline():
    return [(-0.11, 0.02), (0.11, 0.02), (0.11, -0.12), (0.095, -0.18),
            (0.0, -0.20), (-0.095, -0.18), (-0.11, -0.12)]


def build():
    parts = []
    z0, thick = 0.795, 0.012

    def bend(y):  # blade edge curves slightly upward
        return 0.010 * ((-y) / 0.2) ** 2

    # handle: 1.1 m, grip at origin (0.35 m from butt), domed butt
    bm = bmesh.new()
    _lathe(bm, [(0.0, -0.35), (0.020, -0.35), (0.024, -0.34), (0.021, -0.32),
                (0.019, 0.0), (0.020, 0.36), (0.024, 0.62), (0.025, 0.70)], segs=12)
    parts.append(_finish(bm, "cangkul_handle", 0))

    # rubber grip wrap at the hand position
    bm = bmesh.new()
    _lathe(bm, [(0.024, -0.05), (0.0275, -0.045), (0.0275, 0.045), (0.024, 0.05)], segs=12)
    parts.append(_finish(bm, "cangkul_grip", 3))

    # eye socket at the +Z end
    bm = bmesh.new()
    _lathe(bm, [(0.030, 0.62), (0.034, 0.65), (0.034, 0.76), (0.031, 0.80)], segs=12)
    parts.append(_finish(bm, "cangkul_socket", 1))

    # wedge driven into the top of the socket
    bm = bmesh.new()
    _box(bm, (0.0, 0.0, 0.815), (0.014, 0.030, 0.050))
    parts.append(_finish(bm, "cangkul_wedge", 4))

    # heavy slightly curved blade, perpendicular to the handle
    bm = bmesh.new()
    out = _blade_outline()
    bottom = [Vector((x, y, z0 + bend(y))) for x, y in out]
    top = [Vector((x, y, z0 + thick + bend(y))) for x, y in out]
    _loft(bm, [bottom, top])
    parts.append(_finish(bm, "cangkul_blade", 2))
    return parts
