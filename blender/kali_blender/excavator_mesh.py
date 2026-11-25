"""SK_ExcavatorAmfibi low-poly mesh (task B).

build_mesh(armature_obj) builds the amphibious excavator in the rig's REST pose, using only
coordinates from excavator_spec, and skins it rigidly: every part belongs to one deform bone,
so each vertex sits in exactly one vertex group with weight 1.0 and the Armature modifier
moves each part together with its bone.

All geometry is made of closed solids (boxes, tapered beams, prisms, cylinders, rings,
pyramids) with outward winding, so the mesh has no holes and no loose verts or edges.
"""
import math

import bpy  # noqa: F401  (must be imported before bmesh / mathutils in the bpy wheel)
from mathutils import Matrix

from kali_blender import excavator_spec as S

BODY, STEEL, RUBBER = S.MATERIAL_ORDER
HULL = "B_Root_Hull"
TURRET = "B_Turret_Slew"
BOOM = "B_Arm_Boom"
STICK = "B_Arm_Stick"
BUCKET = "B_Tool_Bucket"
DEFORM_BONES = [name for name, _h, _t, _p, deform in S.BONES if deform]
X_AXIS = (1.0, 0.0, 0.0)

# Pontoon section (across X / Z) and the outer skin sits 0.06 m inside the hull edge.
PW2 = 0.55
PCH = 0.2
PX = S.HULL_WIDTH / 2 - 0.06 - PW2
ZC = (S.HULL_BOTTOM_Z + S.HULL_DECK_Z) / 2
PHH = (S.HULL_DECK_Z - S.HULL_BOTTOM_Z) / 2
Y_BOW_TIP = -S.HULL_LENGTH / 2
Y_BOW_END = Y_BOW_TIP + 0.8
Y_REAR = S.HULL_LENGTH / 2

BARREL_RADIUS = {"Boom_L": 0.11, "Boom_R": 0.11, "Stick": 0.09, "Bucket": 0.075}


# ---------------------------------------------------------------- vector helpers
def _add(a, b):
    return (a[0] + b[0], a[1] + b[1], a[2] + b[2])


def _sub(a, b):
    return (a[0] - b[0], a[1] - b[1], a[2] - b[2])


def _mul(a, s):
    return (a[0] * s, a[1] * s, a[2] * s)


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


def _cross(a, b):
    return (a[1] * b[2] - a[2] * b[1], a[2] * b[0] - a[0] * b[2], a[0] * b[1] - a[1] * b[0])


def _norm(a):
    return _mul(a, 1.0 / math.sqrt(_dot(a, a)))


def _mean(pts):
    n = len(pts)
    return (sum(p[0] for p in pts) / n, sum(p[1] for p in pts) / n, sum(p[2] for p in pts) / n)


def _lerp(a, b, t):
    return _add(a, _mul(_sub(b, a), t))


def _newell(pts):
    """Polygon normal (Newell's method); its direction follows the vertex winding."""
    nx = ny = nz = 0.0
    n = len(pts)
    for i in range(n):
        x1, y1, z1 = pts[i]
        x2, y2, z2 = pts[(i + 1) % n]
        nx += (y1 - y2) * (z1 + z2)
        ny += (z1 - z2) * (x1 + x2)
        nz += (x1 - x2) * (y1 + y2)
    return (nx, ny, nz)


def _ring(centre, axis, radius, n):
    d = _norm(axis)
    helper = (1.0, 0.0, 0.0) if abs(d[0]) < 0.9 else (0.0, 1.0, 0.0)
    u = _norm(_cross(d, helper))
    v = _cross(d, u)
    pts = []
    for i in range(n):
        t = 2.0 * math.pi * i / n
        pts.append(_add(centre, _add(_mul(u, radius * math.cos(t)), _mul(v, radius * math.sin(t)))))
    return pts


def _section(cx, cz, hw, hh, c, y, steps=4):
    """Rounded rectangle (4 * steps points, corner radius c) in the XZ plane at height y along Y."""
    pts = []
    corners = ((cx + hw - c, cz + hh - c, 0.0), (cx - hw + c, cz + hh - c, 90.0),
               (cx - hw + c, cz - hh + c, 180.0), (cx + hw - c, cz - hh + c, 270.0))
    for ox, oz, start in corners:
        for i in range(steps):
            t = math.radians(start + 90.0 * i / (steps - 1))
            pts.append((ox + c * math.cos(t), oz + c * math.sin(t)))
    return [(x, y, z) for x, z in pts]


# ---------------------------------------------------------------- geometry builder
class _Builder:
    """Accumulates closed solids. Every vertex belongs to one bone (its vertex group)."""

    def __init__(self):
        self.verts = []
        self.vert_bone = []
        self._key = {}
        self.faces = []
        self.face_mat = []
        self.face_part = []
        self._bone = None
        self._mat = 0
        self._part = -1

    def use(self, bone, material):
        """Start a new part owned by `bone` and made of `material` (a S.MATERIAL_ORDER name)."""
        self._bone = bone
        self._mat = S.MATERIAL_ORDER.index(material)
        self._part += 1

    def _vid(self, p):
        key = (self._bone, round(p[0], 6), round(p[1], 6), round(p[2], 6))
        idx = self._key.get(key)
        if idx is None:
            idx = len(self.verts)
            self.verts.append(tuple(p))
            self.vert_bone.append(self._bone)
            self._key[key] = idx
        return idx

    def _poly(self, pts, hint):
        """Add a face, reversing its winding if its normal does not point along `hint`."""
        pts = list(pts)
        if _dot(_newell(pts), hint) < 0.0:
            pts.reverse()
        self.faces.append(tuple(self._vid(p) for p in pts))
        self.face_mat.append(self._mat)
        self.face_part.append(self._part)

    def strip(self, rings, caps=(True, True), flip=False):
        """Tube through consecutive rings of equal length. caps closes the first / last ring."""
        n = len(rings[0])
        sign = -1.0 if flip else 1.0
        for k in range(len(rings) - 1):
            a, b = rings[k], rings[k + 1]
            centre = _mean(list(a) + list(b))
            for i in range(n):
                j = (i + 1) % n
                quad = [a[i], a[j], b[j], b[i]]
                self._poly(quad, _mul(_sub(_mean(quad), centre), sign))
        if caps[0]:
            self._poly(rings[0], _mul(_sub(_mean(rings[0]), _mean(rings[1])), sign))
        if caps[1]:
            self._poly(rings[-1], _mul(_sub(_mean(rings[-1]), _mean(rings[-2])), sign))

    def prism(self, poly, offset):
        """Extrude a planar convex polygon by `offset`."""
        self.strip([list(poly), [_add(p, offset) for p in poly]])

    def box(self, lo, hi):
        x0, y0, z0 = lo
        x1, y1, z1 = hi
        bottom = [(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0)]
        top = [(x, y, z1) for x, y, _z in bottom]
        self.strip([bottom, top])

    def cylinder(self, base, top, radius, n=10):
        axis = _sub(top, base)
        self.strip([_ring(base, axis, radius, n), _ring(top, axis, radius, n)])

    def pin(self, centre, axis, length, radius, n=10):
        half = _mul(_norm(axis), length / 2.0)
        self.cylinder(_sub(centre, half), _add(centre, half), radius, n)

    def annulus(self, base, top, r_out, r_in, n):
        axis = _sub(top, base)
        ax = _norm(axis)
        o0, o1 = _ring(base, axis, r_out, n), _ring(top, axis, r_out, n)
        i0, i1 = _ring(base, axis, r_in, n), _ring(top, axis, r_in, n)
        self.strip([o0, o1], caps=(False, False))
        self.strip([i0, i1], caps=(False, False), flip=True)
        for k in range(n):
            j = (k + 1) % n
            self._poly([o1[k], o1[j], i1[j], i1[k]], ax)
            self._poly([o0[k], o0[j], i0[j], i0[k]], _mul(ax, -1.0))

    def pyramid(self, base, apex):
        c = _mean(list(base) + [apex])
        self._poly(base, _sub(_mean(base), c))
        n = len(base)
        for i in range(n):
            j = (i + 1) % n
            tri = [base[i], base[j], apex]
            self._poly(tri, _sub(_mean(tri), c))

    def beam(self, p0, p1, width_axis, w0, h0, w1, h1):
        """Tapered rectangular beam from p0 to p1; w is measured along width_axis."""
        d = _norm(_sub(p1, p0))
        e1 = _norm(_sub(width_axis, _mul(d, _dot(width_axis, d))))
        e2 = _cross(e1, d)

        def rect(p, w, h):
            a = _mul(e1, w / 2.0)
            b = _mul(e2, h / 2.0)
            return [_add(p, _add(a, b)), _add(p, _add(_mul(a, -1.0), b)),
                    _add(p, _add(_mul(a, -1.0), _mul(b, -1.0))), _add(p, _add(a, _mul(b, -1.0)))]

        self.strip([rect(p0, w0, h0), rect(p1, w1, h1)])


# ---------------------------------------------------------------- parts
def _hull(b):
    hl = S.HULL_LENGTH / 2
    zb, zd = S.HULL_BOTTOM_Z, S.HULL_DECK_Z
    b.use(HULL, BODY)
    for cx in (-PX, PX):
        tip = _section(cx, ZC, PW2 * 0.45, PHH * 0.45, PCH * 0.45, Y_BOW_TIP)
        bow_end = _section(cx, ZC, PW2, PHH, PCH, Y_BOW_END)
        rear = _section(cx, ZC, PW2, PHH, PCH, Y_REAR)
        b.strip([tip, bow_end], caps=(True, False))       # tapered bow
        b.strip([bow_end, rear], caps=(False, True))      # float body
    b.box((-1.3, Y_BOW_END, zb + 1.0), (1.3, hl, zd))    # bridge deck between the floats
    b.use(HULL, STEEL)                                     # handrails on the float tops
    for cx in (-PX, PX):
        for y in (-2.6, -1.4, -0.2, 1.0, 2.2, 3.0):
            b.box((cx - 0.03, y - 0.03, zd), (cx + 0.03, y + 0.03, zd + 0.25))
        for z in (zd + 0.2, zd + 0.25):
            b.box((cx - 0.03, Y_BOW_END + 0.1, z - 0.02), (cx + 0.03, 3.0, z + 0.02))

    b.use(HULL, RUBBER)
    for sx in (-1.0, 1.0):                                # rubber bumper strips, flush with hull edge
        x0, x1 = sorted((sx * (S.HULL_WIDTH / 2 - 0.06), sx * S.HULL_WIDTH / 2))
        b.box((x0, -2.7, -0.1), (x1, 3.4, 0.3))
    b.box((-1.1, -2.6, zd), (1.1, 3.2, zd + 0.04))        # anti-slip tread plate
    for y in (-2.0, -1.0, 0.0, 1.0, 2.0):                 # tread ribs
        b.box((-1.0, y - 0.05, zd + 0.04), (1.0, y + 0.05, zd + 0.1))

    b.use(HULL, BODY)
    for x in (-0.75, 0.75):                               # fuel tanks on the deck
        b.cylinder((x, -2.2, zd + 0.22), (x, -0.4, zd + 0.22), 0.22, n=16)
    h, w = 0.3, 0.08
    for x, y in S.SPUD_XY.values():                       # hollow-looking spud guide sleeves
        z0, z1 = zb, zd + 0.2
        b.box((x - h, y - h, z0), (x - h + w, y + h, z1))
        b.box((x + h - w, y - h, z0), (x + h, y + h, z1))
        b.box((x - h + w, y - h, z0), (x + h - w, y - h + w, z1))
        b.box((x - h + w, y + h - w, z0), (x + h - w, y + h, z1))
    for x, y in S.SPUD_XY.values():
        b.annulus((x, y, zd + 0.2), (x, y, zd + 0.28), 0.28, 0.2, n=16)   # spud collar
    b.box((-0.75, 0.6 - 0.75, zd), (0.75, 0.6 + 0.75, 1.2))   # slew pedestal
    b.use(HULL, STEEL)
    b.annulus((0.0, 0.6, 1.2), (0.0, 0.6, S.SLEW_RING_TOP_Z), 1.0, 0.75, n=48)   # slew ring


def _turret(b):
    b.use(TURRET, BODY)
    b.cylinder((0.0, 0.6, S.SLEW_RING_TOP_Z), (0.0, 0.6, S.SLEW_RING_TOP_Z + 0.1), 0.95, n=24)
    b.box((-0.6, 0.2, 1.5), (0.6, 1.4, 2.3))              # engine house
    for sx in (-1.0, 1.0):                                # louvres on both flanks
        x0, x1 = sorted((sx * 0.6, sx * 0.66))
        for i in range(5):
            y = 0.35 + i * 0.2
            b.box((x0, y, 1.6), (x1, y + 0.08, 2.2))
    b.strip([_section(0.0, 1.75, 0.85, 0.25, 0.1, 1.35), _section(0.0, 1.75, 0.85, 0.25, 0.1, 1.95)])  # counterweight
    b.box((0.62, -0.5, 1.5), (1.0, 0.2, 2.5))              # operator cab
    b.box((0.6, -0.52, 2.5), (1.02, 0.22, 2.6))            # cab roof
    b.box((-0.6, 0.0, 2.3), (0.6, 0.2, 2.35))              # engine cover lip
    for x in (-0.45, -0.27, -0.09, 0.09, 0.27, 0.45):      # roof louvres
        b.box((x - 0.03, 0.3, 2.3), (x + 0.03, 1.3, 2.36))
    b.use(TURRET, BODY)
    b.box((0.68, -0.58, 2.38), (0.94, -0.5, 2.42))         # window frame bars
    b.box((0.68, -0.58, 1.78), (0.94, -0.5, 1.82))
    b.box((0.68, -0.58, 1.8), (0.72, -0.5, 2.4))
    b.box((0.9, -0.58, 1.8), (0.94, -0.5, 2.4))
    for x in (-0.6, -0.2, 0.2, 0.6):                       # counterweight grille bars
        b.box((x - 0.06, 1.95, 1.6), (x + 0.06, 1.99, 1.9))
    for sx in (-1.0, 1.0):                                 # boom foot bracket plates
        x0, x1 = sorted((sx * 0.21, sx * 0.29))
        b.box((x0, -0.9, 1.6), (x1, -0.3, 2.8))
    b.box((-0.25, -0.9, 2.6), (0.25, -0.3, 2.8))           # bracket crossbar

    b.use(TURRET, RUBBER)                                  # dark glass panels and exhaust
    b.box((0.72, -0.56, 1.82), (0.9, -0.5, 2.38))
    b.box((1.0, -0.4, 1.9), (1.03, 0.1, 2.35))
    b.cylinder((-0.35, 0.9, 2.3), (-0.35, 0.9, 3.1), 0.07, n=10)
    b.cylinder((-0.35, 0.9, 3.1), (-0.35, 0.9, 3.14), 0.1, n=10)


def _boom(b):
    b.use(BOOM, BODY)
    b.beam(S.BOOM_HEAD, S.BOOM_TAIL, X_AXIS, 0.34, 0.46, 0.24, 0.30)
    _side_ribs(b, S.BOOM_HEAD, S.BOOM_TAIL, (0.1, 0.3, 0.5, 0.7, 0.9), 0.16, 0.21, 0.08)
    b.use(BOOM, STEEL)
    b.pin(S.BOOM_HEAD, X_AXIS, 0.7, 0.06)
    b.pin(S.BOOM_TAIL, X_AXIS, 0.5, 0.06)


def _stick(b):
    rod_pin = S.PISTONS["Stick"][2]
    b.use(STICK, BODY)
    b.beam(S.BOOM_TAIL, S.STICK_TAIL, X_AXIS, 0.24, 0.30, 0.18, 0.22)
    b.beam(S.BOOM_TAIL, rod_pin, X_AXIS, 0.16, 0.16, 0.12, 0.12)   # lever behind the elbow
    _side_ribs(b, S.BOOM_TAIL, S.STICK_TAIL, (0.15, 0.4, 0.65, 0.9), 0.12, 0.17, 0.06)
    b.use(STICK, STEEL)
    b.pin(S.STICK_TAIL, X_AXIS, 0.46, 0.06)


def _side_ribs(b, head, tail, ts, x_in, x_out, half):
    for t in ts:
        c = _lerp(head, tail, t)
        for sx in (-1.0, 1.0):
            x0, x1 = sorted((sx * x_in, sx * x_out))
            b.box((x0, c[1] - half, c[2] - half), (x1, c[1] + half, c[2] + half))


def _bucket(b):
    origin = S.STICK_TAIL
    axis = _norm(_sub(S.BUCKET_TAIL, origin))
    side = _norm(_cross(X_AXIS, axis))

    def at(x, s, t):
        """Bucket-local point: x across the 1.4 m width, s along the bone, t out of the mouth."""
        return _add(origin, _add(_mul(X_AXIS, x), _add(_mul(axis, s), _mul(side, t))))

    b.use(BUCKET, BODY)
    rings = []
    for k in range(9):                                     # curved back plate
        s = k / 8.0
        t = -0.3 * math.sin(math.pi * s)
        rings.append([at(-0.7, s, t - 0.03), at(0.7, s, t - 0.03),
                      at(0.7, s, t + 0.03), at(-0.7, s, t + 0.03)])
    b.strip(rings)
    side_poly = [(0.0, 0.0), (0.5, -0.3), (1.0, 0.0), (1.0, 0.12), (0.0, 0.12)]
    for x, off in ((0.7, 0.04), (-0.7, -0.04)):           # side plates
        b.prism([at(x, s, t) for s, t in side_poly], _mul(X_AXIS, off))
    b.use(BUCKET, STEEL)
    b.beam(at(0.0, 0.9, -0.02), at(0.0, 1.02, 0.05), X_AXIS, 1.4, 0.1, 1.4, 0.1)   # cutting lip
    for x in (0.74, -0.74):                                # bolt heads on side plates
        for s, t in ((0.2, 0.0), (0.5, -0.1), (0.8, 0.0)):
            sx = 1.0 if x > 0 else -1.0
            b.cylinder(at(x, s, t), at(x + sx * 0.03, s, t), 0.03, n=8)
    for x in (-0.6, -0.3, 0.0, 0.3, 0.6):                  # five teeth
        base = [at(x - 0.05, 0.98, -0.06), at(x + 0.05, 0.98, -0.06),
                at(x + 0.05, 0.98, 0.06), at(x - 0.05, 0.98, 0.06)]
        b.pyramid(base, at(x, 1.15, 0.0))
    b.use(BUCKET, BODY)                                    # hydraulic thumb: two prongs
    for x in (-0.45, 0.45):
        b.beam(at(x, 0.25, -0.25), at(x, 0.85, 0.2), X_AXIS, 0.12, 0.08, 0.08, 0.05)


def _pistons(b):
    f = S.PISTON_BONE_FRACTION
    for suffix, (base_pin, _bp, rod_pin, _rp) in S.PISTONS.items():
        base_name, rod_name = S.piston_bone_names(suffix)
        r = BARREL_RADIUS[suffix]
        base_tail = _lerp(base_pin, rod_pin, f)
        rod_tail = _lerp(rod_pin, base_pin, f)
        ax = _norm(_sub(base_tail, base_pin))
        b.use(base_name, BODY)                             # barrel + gland collars
        b.cylinder(base_pin, base_tail, r, n=12)
        b.cylinder(base_pin, _add(base_pin, _mul(ax, 0.06)), r * 1.25, n=12)
        b.cylinder(_sub(base_tail, _mul(ax, 0.06)), base_tail, r * 1.25, n=12)
        b.use(rod_name, STEEL)                             # chrome rod + rod eye
        b.cylinder(rod_pin, rod_tail, 0.45 * r, n=12)
        b.cylinder(rod_pin, _add(rod_pin, _mul(ax, -0.05)), 0.45 * r * 1.6, n=12)
        b.cylinder(rod_tail, _sub(rod_tail, _mul(ax, 0.05)), 0.45 * r * 1.25, n=12)


def _spuds(b):
    for key, (x, y) in S.SPUD_XY.items():
        b.use(f"B_Spud_Leg_{key}", RUBBER)
        b.cylinder((x, y, S.SPUD_BOTTOM_Z), (x, y, S.SPUD_TOP_Z), S.SPUD_RADIUS, n=8)
        b.cylinder((x, y, S.SPUD_TOP_Z - 0.2), (x, y, S.SPUD_TOP_Z),
                   S.SPUD_RADIUS + 0.06, n=8)


def _construct(b):
    _hull(b)
    _turret(b)
    _boom(b)
    _stick(b)
    _bucket(b)
    _pistons(b)
    _spuds(b)


# ---------------------------------------------------------------- Blender objects
def _material(name):
    spec = S.MATERIALS[name]
    mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    rgba = S.hex_to_linear_rgba(spec["color_hex"])
    mat.use_nodes = True
    bsdf = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    bsdf.inputs["Base Color"].default_value = rgba
    bsdf.inputs["Metallic"].default_value = spec["metallic"]
    bsdf.inputs["Roughness"].default_value = 1.0 - spec["smoothness"]
    mat.diffuse_color = rgba
    return mat


def _project_uvs(me, face_part):
    """Per-part box projection: each part is unwrapped into [0, 1] from its own bounds."""
    pts = [tuple(v.co) for v in me.vertices]
    part_points = {}
    for poly in me.polygons:
        part_points.setdefault(face_part[poly.index], []).extend(pts[vi] for vi in poly.vertices)
    bounds = {}
    for part, plist in part_points.items():
        bounds[part] = ([min(p[k] for p in plist) for k in range(3)],
                        [max(p[k] for p in plist) for k in range(3)])
    uv_layer = me.uv_layers.get("UVMap") or me.uv_layers.new(name="UVMap")
    data = uv_layer.data
    for poly in me.polygons:
        lo, hi = bounds[face_part[poly.index]]
        span = max(max(hi[k] - lo[k] for k in range(3)), 1e-6)
        normal = _newell([pts[vi] for vi in poly.vertices])
        ax = max(range(3), key=lambda k: abs(normal[k]))
        a, c = [k for k in range(3) if k != ax]
        for k in range(poly.loop_total):
            p = pts[poly.vertices[k]]
            u = min(max((p[a] - lo[a]) / span, 0.0), 1.0)
            v = min(max((p[c] - lo[c]) / span, 0.0), 1.0)
            data[poly.loop_start + k].uv = (u, v)


def build_mesh(armature_obj):
    """Create (or replace) the SK_ExcavatorAmfibi mesh, parented and rigidly skinned to armature_obj."""
    builder = _Builder()
    _construct(builder)

    name = S.MESH_NAME
    for old in [o for o in bpy.data.objects if o.name == name]:
        bpy.data.objects.remove(old, do_unlink=True)
    old_mesh = bpy.data.meshes.get(name)
    if old_mesh is not None:
        bpy.data.meshes.remove(old_mesh)

    me = bpy.data.meshes.new(name)
    me.from_pydata(builder.verts, [], builder.faces)
    me.update()
    for mat_name in S.MATERIAL_ORDER:
        me.materials.append(_material(mat_name))
    for poly in me.polygons:
        poly.material_index = builder.face_mat[poly.index]
        poly.use_smooth = False
    _project_uvs(me, builder.face_part)

    obj = bpy.data.objects.new(name, me)
    targets = list(armature_obj.users_collection) or [bpy.context.scene.collection]
    for coll in targets:
        coll.objects.link(obj)

    for bone in DEFORM_BONES:
        idx = [i for i, owner in enumerate(builder.vert_bone) if owner == bone]
        if idx:
            group = obj.vertex_groups.new(name=bone)
            group.add(idx, 1.0, "REPLACE")

    mod = obj.modifiers.new(name="Armature", type="ARMATURE")
    mod.object = armature_obj
    mod.use_vertex_groups = True
    mod.use_bone_envelopes = False

    obj.parent = armature_obj
    obj.parent_type = "OBJECT"
    obj.matrix_parent_inverse = Matrix.Identity(4)
    obj.location = (0.0, 0.0, 0.0)
    obj.rotation_euler = (0.0, 0.0, 0.0)
    obj.scale = (1.0, 1.0, 1.0)
    return obj
