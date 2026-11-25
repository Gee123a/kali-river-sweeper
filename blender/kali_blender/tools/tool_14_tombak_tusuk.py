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
    "index": 14,
    "name": "SM_Tool_TombakTusuk",
    "label": "Tombak tusuk (litter spike stick)",
    "head_dir": "+Z",
    "palette": [
        ("#a8743f", 0.0, 0.30),   # 0 wooden staff
        ("#1c1c1c", 0.0, 0.25),   # 1 black rubber hand grip
        ("#7d848c", 1.0, 0.55),   # 2 steel ferrule
        ("#d0d5da", 1.0, 0.85),   # 3 bright steel spike
        ("#c83a2c", 0.0, 0.40),   # 4 red plastic stopper disc
    ],
}


def build():
    parts = []

    # 1.2 m wooden staff, centred on the origin
    bm = bmesh.new()
    _lathe(bm, [(0.012, -0.60), (0.012, 0.58)], segs=12)
    parts.append(_finish(bm, "tusuk_staff", 0))

    # rubber hand grip sleeve around the origin
    bm = bmesh.new()
    _lathe(bm, [(0.016, -0.07), (0.0185, -0.065), (0.0195, -0.05), (0.0195, 0.05),
                (0.0185, 0.065), (0.016, 0.07)], segs=12)
    parts.append(_finish(bm, "tusuk_grip", 1))

    # metal ferrule at the top of the staff
    bm = bmesh.new()
    _lathe(bm, [(0.0135, 0.58), (0.0145, 0.59), (0.0145, 0.61), (0.0135, 0.62)], segs=12)
    parts.append(_finish(bm, "tusuk_ferrule", 2))

    # 0.18 m sharp steel spike at +Z
    bm = bmesh.new()
    _lathe(bm, [(0.0065, 0.62), (0.0045, 0.70), (0.0, 0.80)], segs=12)
    parts.append(_finish(bm, "tusuk_spike", 3))

    # small stopper disc on the spike
    bm = bmesh.new()
    _lathe(bm, [(0.0075, 0.685), (0.030, 0.685), (0.033, 0.689), (0.030, 0.693), (0.0075, 0.693)], segs=12)
    parts.append(_finish(bm, "tusuk_stopper", 4))
    return parts
