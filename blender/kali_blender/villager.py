"""SK_VillagerNPC: low-poly kampung villager (kaos oblong, celana pendek, sandal jepit, caping).

Built from lofted superellipse rings (no primitives), one palette material, Unity Humanoid
bone names, procedural per-ring skin weights and three baked takes (Idle, ThrowTrash, CarryBin).
Pivot: soles at z=0, centred on x/y; faces -Y in Blender (= Unity +Z).

Props (separate FBX, same palette): SM_Villager_TrashBag (thrown in ThrowTrash) and SM_Villager_Bin
(carried in CarryBin). Each prop's origin is its socket bone (Socket_RightHand / Socket_Carry); the
sockets have an identity frame in Unity at rest, so a prop parented with zero local transform fits.
"""
import math

import bpy  # noqa: F401
from mathutils import Matrix, Vector, geometry

from . import rigging_common as rc

NAME = "SK_VillagerNPC"
RIG_NAME = "VillagerRig"
FBX_PATH = rc.FBX_DIR + "/SK_VillagerNPC.fbx"
BLEND_PATH = "blender/SK_VillagerNPC.blend"
PALETTE_PNG = rc.TEX_DIR + "/T_Villager_Palette.png"
MATERIAL = "M_Villager_Palette"
PROP_BAG = "SM_Villager_TrashBag"
PROP_BIN = "SM_Villager_Bin"
TRI_BUDGET = (1200, 1800)
TAKES = {"Idle": 75, "ThrowTrash": 45, "CarryBin": 30}   # frames at 30 fps (last frame = first for loops)
RELEASE_FRAME = 16          # ThrowTrash: let go of the bag here (0.53 s)
CARRY_SPEED = 0.75          # m/s the CarryBin cycle is paced for (stride 0.37 m, 2 steps / s)

PALETTE = rc.Palette([
    ("skin", "#C98B5F"), ("hair", "#231C18"), ("shirt", "#B8483C"), ("shirt_trim", "#8C3229"),
    ("shorts", "#2F3B55"), ("sole", "#E6E1D5"), ("strap", "#2F6DB5"), ("straw", "#D2AE6C"),
    ("straw_dark", "#9C7742"), ("eye", "#17120F"), ("mouth", "#7A3A2C"), ("bin", "#3E8A4C"),
    ("bin_dark", "#2B6436"), ("bag", "#2A2A2E"), ("bag_knot", "#4A4A52"), ("skin_dark", "#A86F49"),
])

SIDES = (("Left", 1.0), ("Right", -1.0))
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))


def _bones():
    b = [
        ("Hips", (0, 0, 0.56), (0, 0, 0.66), None, True),
        ("Spine", (0, 0, 0.66), (0, 0, 0.78), "Hips", True),
        ("Chest", (0, 0, 0.78), (0, 0, 0.99), "Spine", True),
        ("Neck", (0, 0, 0.98), (0, 0, 1.04), "Chest", True),
        ("Head", (0, 0, 1.04), (0, 0, 1.39), "Neck", True),
    ]
    for S, s in SIDES:
        b += [
            (S + "Shoulder", (s * 0.03, 0, 0.915), (s * 0.15, 0, 0.925), "Chest", True),
            (S + "UpperArm", (s * 0.15, 0, 0.925), (s * 0.31, 0, 0.925), S + "Shoulder", True),
            (S + "LowerArm", (s * 0.31, 0, 0.925), (s * 0.44, 0, 0.925), S + "UpperArm", True),
            (S + "Hand", (s * 0.44, 0, 0.925), (s * 0.57, 0, 0.925), S + "LowerArm", True),
            (S + "UpperLeg", (s * 0.08, 0, 0.53), (s * 0.08, 0, 0.29), "Hips", True),
            (S + "LowerLeg", (s * 0.08, 0, 0.29), (s * 0.08, 0, 0.075), S + "UpperLeg", True),
            (S + "Foot", (s * 0.08, 0, 0.075), (s * 0.08, -0.10, 0.02), S + "LowerLeg", True),
        ]
    # Sockets point +Z with roll 0: identity frame in Unity at rest (see module docstring).
    b += [
        ("Socket_RightHand", (-0.495, 0, 0.900), (-0.495, 0, 0.950), "RightHand", False),
        ("Socket_Carry", (0, -0.24, 0.50), (0, -0.24, 0.55), "Chest", False),
    ]
    return b


BONES = _bones()
DEFORM_BONES = [b[0] for b in BONES if b[4]]
PROP_ROD = "SM_Villager_FishingRod"
SOCKETS = {PROP_BAG: "Socket_RightHand", PROP_BIN: "Socket_Carry", PROP_ROD: "Socket_RightHand"}


# ================================================================== mesh
def _w(**kw):
    return kw


def _torso(mb):
    n, p = 10, 2.2
    rows = [  # z, half-width, half-depth, y offset
        (0.535, 0.160, 0.115, 0.0), (0.565, 0.165, 0.118, 0.0), (0.640, 0.150, 0.108, 0.0),
        (0.730, 0.152, 0.110, -0.004), (0.840, 0.160, 0.106, -0.003), (0.905, 0.155, 0.099, 0.0),
        (0.972, 0.132, 0.086, 0.005), (0.998, 0.066, 0.058, 0.008),
    ]

    def shoulder_w(base, k):
        def f(co):
            w = dict(base)
            if abs(co.x) > 0.05:
                side = "Left" if co.x > 0 else "Right"
                w = {b: v * (1 - k) for b, v in w.items()}
                w[side + "Shoulder"] = k
            return w
        return f
    weights = [_w(Hips=0.7, Spine=0.3), _w(Hips=0.7, Spine=0.3), _w(Hips=0.3, Spine=0.7),
               _w(Spine=0.8, Chest=0.2), _w(Spine=0.2, Chest=0.8), shoulder_w(_w(Chest=1.0), 0.2),
               shoulder_w(_w(Chest=1.0), 0.3), _w(Chest=0.7, Neck=0.3)]
    rings = [rc.ring((0, yo, z), Z, X, a, Y, b, n, p) for z, a, b, yo in rows]
    cols = ["shirt_trim"] + ["shirt"] * 6
    mb.loft(rings, weights, cols, cap0="shirt_trim", cap1="shirt_trim")
    # shorts body (under the shirt hem)
    rows = [(0.44, 0.118, 0.085), (0.50, 0.150, 0.105), (0.58, 0.148, 0.104)]

    def crotch_w(co):
        if abs(co.x) < 0.03:
            return _w(Hips=1.0)
        return {"Hips": 0.6, ("Left" if co.x > 0 else "Right") + "UpperLeg": 0.4}
    rings = [rc.ring((0, 0, z), Z, X, a, Y, b, n, 2.2) for z, a, b in rows]
    mb.loft(rings, [crotch_w, _w(Hips=1.0), _w(Hips=1.0)], ["shorts"] * 2, cap0="shorts", cap1="shorts")
    # neck (both ends buried in collar / head)
    rings = [rc.ring((0, 0.008, 0.95), Z, X, 0.052, Y, 0.050, 8), rc.ring((0, 0.010, 1.08), Z, X, 0.050, Y, 0.048, 8)]
    mb.loft(rings, [_w(Chest=0.5, Neck=0.5), _w(Neck=0.3, Head=0.7)], ["skin"])


def _leg(mb, S, s):
    n, ph = 8, math.pi / 8
    cx = s * 0.08
    U, L = S + "UpperLeg", S + "LowerLeg"
    rows = [  # z, half-width, half-depth, y offset, weights
        (0.560, 0.072, 0.078, 0.0, {"Hips": 0.4, U: 0.6}),
        (0.460, 0.080, 0.085, 0.0, {U: 1.0}),
        (0.345, 0.077, 0.081, 0.0, {U: 1.0}),
        (0.340, 0.054, 0.056, 0.0, {U: 1.0}),
        (0.310, 0.052, 0.054, 0.0, {U: 0.7, L: 0.3}),
        (0.270, 0.052, 0.055, 0.003, {U: 0.3, L: 0.7}),
        (0.190, 0.054, 0.059, 0.008, {L: 1.0}),
        (0.085, 0.038, 0.040, 0.0, {L: 1.0}),
    ]
    rings = [rc.ring((cx, yo, z), -Z, X, a, Y, b, n, 2.0, ph) for z, a, b, yo, _w_ in rows]
    cols = ["shorts", "shorts", "shorts", "skin", "skin", "skin", "skin"]
    mb.loft(rings, [r[4] for r in rows], cols, cap0="shorts", cap1="skin")
    # foot (skin) with an inflated strap band, along -Y
    F = S + "Foot"
    rows = [  # y, half-width, half-height, z centre, colour of the band that follows
        (0.050, 0.034, 0.022, 0.040, "skin"), (0.015, 0.042, 0.036, 0.052, "skin"),
        (-0.035, 0.050, 0.034, 0.047, "strap"), (-0.062, 0.050, 0.031, 0.043, "skin"),
        (-0.105, 0.043, 0.019, 0.034, "skin"), (-0.125, 0.032, 0.012, 0.030, None),
    ]
    rings = [rc.ring((cx, y, zc), -Y, X, a, Z, b, 6, 2.2) for y, a, b, zc, _c in rows]
    mb.loft(rings, [{F: 1.0}] * len(rows), [r[4] for r in rows[:-1]], cap0="skin", cap1="skin")
    # sandal sole: white top / sides, blue underside
    rings = [rc.ring((cx, -0.038, z), Z, X, 0.053, Y, 0.098, 8, 3.0) for z in (0.0, 0.022)]
    mb.loft(rings, [{F: 1.0}] * 2, ["sole"], cap0="strap", cap1="sole")


def _arm(mb, S, s):
    n, ph = 8, math.pi / 8
    d = X * s
    Sh, U, L, H = S + "Shoulder", S + "UpperArm", S + "LowerArm", S + "Hand"
    rows = [  # x, half-depth (Y), half-height (Z), z offset, weights, band colour
        (0.085, 0.050, 0.048, 0.0, {Sh: 0.3, U: 0.7}, "shirt"),
        (0.240, 0.062, 0.059, 0.0, {U: 1.0}, "shirt_trim"),
        (0.245, 0.046, 0.045, 0.0, {U: 1.0}, "skin"),
        (0.290, 0.044, 0.043, 0.0, {U: 0.7, L: 0.3}, "skin"),
        (0.330, 0.042, 0.041, 0.0, {U: 0.3, L: 0.7}, "skin"),
        (0.425, 0.036, 0.032, 0.0, {L: 0.5, H: 0.5}, "skin"),
        (0.460, 0.048, 0.026, -0.004, {H: 1.0}, "skin"),
        (0.525, 0.050, 0.025, -0.004, {H: 1.0}, "skin"),
        (0.570, 0.030, 0.016, -0.006, {H: 1.0}, None),
    ]
    rings = [rc.ring((s * x, 0, 0.925 + dz), d, Y, a, Z, b, n, 2.0, ph) for x, a, b, dz, _w_, _c in rows]
    mb.loft(rings, [r[4] for r in rows], [r[5] for r in rows[:-1]], cap0="shirt", cap1="skin")
    # thumb, forward along the palm edge
    base = Vector((s * 0.462, -0.036, 0.917))
    td = Vector((s * 0.45, -0.80, -0.30)).normalized()
    e1 = td.cross(Z).normalized()
    e2 = td.cross(e1)
    rings = [rc.ring(base, td, e1, 0.016, e2, 0.013, 4, 2.0, math.pi / 4),
             rc.ring(base + td * 0.036, td, e1, 0.012, e2, 0.010, 4, 2.0, math.pi / 4)]
    mb.loft(rings, [{H: 1.0}] * 2, ["skin"], cap1="skin")


HEAD_C = Vector((0, 0.0, 1.205))
HEAD_R = (0.175, 0.162, 0.180)


def _head_ring(lat):
    s = math.cos(lat) ** 0.8
    jaw = max(0.0, -math.sin(lat))
    rx = HEAD_R[0] * s * (1 - 0.10 * jaw)
    ry = HEAD_R[1] * s * (1 - 0.05 * jaw)
    c = HEAD_C + Vector((0, 0.012 * jaw, HEAD_R[2] * math.sin(lat)))
    return rc.ring(c, Z, X, rx, Y, ry, 12, 2.3, math.pi / 12)


def _head(mb):
    lats = [math.radians(a) for a in (-62, -36, -12, 12, 36, 62)]
    f0 = len(mb.faces)
    ids = mb.loft([_head_ring(l) for l in lats], [_w(Head=1.0)] * 6, ["skin"] * 5)
    mb.fan(ids[0], HEAD_C + Vector((0, 0.012, -HEAD_R[2])), _w(Head=1.0), "skin", flip=True)
    mb.fan(ids[-1], HEAD_C + Vector((0, 0, HEAD_R[2])), _w(Head=1.0), "hair")
    head_faces = range(f0, len(mb.faces))
    # hair: crown, sides and back; forehead / face stay skin
    for fi in head_faces:
        c = sum((mb.verts[v] for v in mb.faces[fi]), Vector()) / len(mb.faces[fi]) - HEAD_C
        h = c.z / HEAD_R[2]
        hair = h > 0.62 or (h > 0.25 and c.y > -0.075) or (h > -0.15 and c.y > 0.035) or (h > -0.6 and c.y > 0.08)
        if hair:
            mb.fcol[fi] = "hair"
    tris = []
    for fi in head_faces:
        f = [mb.verts[v] for v in mb.faces[fi]]
        tris += [(f[0], f[i], f[i + 1]) for i in range(1, len(f) - 1)]

    def surface(x, z):
        """Front facet point and normal at (x, z): ray along +Y onto the low-poly head."""
        o = Vector((x, -1.0, z))
        hits = []
        for a, b, c in tris:
            hit = geometry.intersect_ray_tri(a, b, c, Y, o, True)
            if hit is not None:
                nrm = (b - a).cross(c - a).normalized()
                hits.append((hit.y, hit, nrm if nrm.y < 0 else -nrm))
        if not hits:
            raise RuntimeError(f"no head surface at {x}, {z}")
        return min(hits, key=lambda h: h[0])[1:]          # nearest hit = the face, not the back of the head

    def front_disc(x, z, hw, hh, n, col, bulge, back):
        p, nrm = surface(x, z)
        right = Z.cross(nrm).normalized()           # +X seen from the front
        up = nrm.cross(right).normalized()
        ring_pts = [p + nrm * 0.0015 + right * (hw * math.cos(2 * math.pi * i / n)) + up * (hh * math.sin(2 * math.pi * i / n))
                    for i in range(n)]
        ids = [mb.vert(q, _w(Head=1.0)) for q in ring_pts]
        apex = p + nrm * bulge
        mb.fan(ids, apex, _w(Head=1.0), col)
        if back:
            mb.face(ids[::-1], col)
        # winding check: fan faces must face away from the head
        f = mb.faces[-(n + (1 if back else 0))]
        a, b, c = (mb.verts[i] for i in f)
        if (b - a).cross(c - a).dot(nrm) < 0:
            raise RuntimeError("face feature winding inverted")
    for s in (1, -1):
        front_disc(s * 0.062, 1.188, 0.021, 0.030, 6, "eye", 0.004, True)
    front_disc(0.0, 1.150, 0.012, 0.011, 4, "skin_dark", 0.012, False)      # nose
    front_disc(0.0, 1.112, 0.017, 0.006, 4, "mouth", 0.002, False)          # mouth
    for s in (1, -1):    # ears: flat ovals just behind the cheek
        c = Vector((0, 0.016, 1.178))
        rings = [rc.ring((s * 0.150, c.y, c.z), X * s, Y, 0.018, Z, 0.028, 6),
                 rc.ring((s * 0.192, c.y + 0.006, c.z), X * s, Y, 0.017, Z, 0.032, 6)]
        mb.loft(rings, [_w(Head=1.0)] * 2, ["skin"], cap1="skin")


def _caping(mb):
    n = 12
    tilt = Matrix.Translation((0, 0, 1.295)) @ Matrix.Rotation(math.radians(-7), 4, "X") @ Matrix.Translation((0, 0, -1.295))
    rows = [(0.300, 1.290), (0.318, 1.293), (0.318, 1.307), (0.160, 1.390), (0.032, 1.453)]
    rings = [[tilt @ q for q in rc.ring((0, 0, z), Z, X, r, Y, r, n)] for r, z in rows]
    ids = mb.loft(rings, [_w(Head=1.0)] * 5, ["straw_dark", "straw_dark", "straw", "straw"])
    mb.fan(ids[0], tilt @ Vector((0, 0, 1.405)), _w(Head=1.0), "straw_dark", flip=True)
    mb.fan(ids[-1], tilt @ Vector((0, 0, 1.470)), _w(Head=1.0), "straw_dark")


def build_mesh(material):
    mb = rc.MeshBuilder(PALETTE)
    _torso(mb)
    for S, s in SIDES:
        _leg(mb, S, s)
        _arm(mb, S, s)
    _head(mb)
    _caping(mb)
    return mb.build(NAME, material, DEFORM_BONES)


def build_props(material):
    """SM_Villager_Bin (origin = bottom centre) and SM_Villager_TrashBag (origin = knot, hangs along -X)."""
    mb = rc.MeshBuilder(PALETTE)
    rows = [(0.100, 0.0), (0.122, 0.245), (0.134, 0.245), (0.134, 0.268), (0.114, 0.268), (0.104, 0.20)]
    rings = [rc.ring((0, 0, z), Z, X, r, Y, r, 12) for r, z in rows]
    ids = mb.loft(rings, [{}] * 6, ["bin", "bin_dark", "bin_dark", "bin_dark", "bin_dark"], cap0="bin_dark")
    mb.fan(ids[-1], Vector((0.01, -0.01, 0.255)), {}, "bag")          # heap of rubbish inside
    bin_obj = mb.build(PROP_BIN, material, None)

    mb = rc.MeshBuilder(PALETTE)
    rows = [(0.000, 0.010, 0.010), (-0.020, 0.016, 0.016), (-0.035, 0.022, 0.020), (-0.075, 0.070, 0.060),
            (-0.140, 0.092, 0.078), (-0.200, 0.080, 0.070), (-0.240, 0.040, 0.036)]
    rings = []
    for k, (x, a, b) in enumerate(rows):
        pts = rc.ring((x, 0, 0), -X, Y, a, Z, b, 8, 2.0, math.pi / 8)
        if 3 <= k <= 5:   # lumpy plastic: fixed pseudo-random bulges
            pts = [Vector((q.x, 0, 0)) + (q - Vector((q.x, 0, 0))) * (1 + 0.09 * math.sin(7.3 * k + 2.1 * i)) for i, q in enumerate(pts)]
        rings.append(pts)
    mb.loft(rings, [{}] * len(rows), ["bag_knot", "bag_knot", "bag", "bag", "bag", "bag"], cap0="bag_knot", cap1="bag")
    for s in (1, -1):     # tied handle ears
        base = Vector((-0.012, 0, 0))
        tip = Vector((0.018, s * 0.030, 0.022))
        e = Vector((0, 0, 0.008))
        ids = [mb.vert(q, {}) for q in (base + e, base - e, tip, base + Vector((0, s * 0.008, 0)))]
        for f in ((0, 1, 2), (1, 3, 2), (3, 0, 2), (0, 3, 1)):
            mb.face([ids[i] for i in (f if s > 0 else f[::-1])], "bag_knot")
    bag_obj = mb.build(PROP_BAG, material, None)
    return bag_obj, bin_obj


# ================================================================== rig + skin
def build_rig():
    return rc.build_armature(RIG_NAME, BONES)


def skin(mesh_obj, arm_obj):
    mesh_obj.parent = arm_obj
    mod = mesh_obj.modifiers.new("Armature", "ARMATURE")
    mod.object = arm_obj


# ================================================================== animation
def _mirror(xyz):
    return (xyz[0], -xyz[1], -xyz[2])


def _both(r, part, left_xyz):
    r["Left" + part] = tuple(left_xyz)
    r["Right" + part] = _mirror(left_xyz)


def _relaxed():
    r = {}
    _both(r, "UpperArm", (-4, 68, 0))
    _both(r, "LowerArm", (0, 0, -12))
    _both(r, "Hand", (0, 0, -4))
    return r


LEG_L1, LEG_L2 = 0.24, 0.215


def _crouch(r, a):
    """Bend both legs by `a` degrees with flat feet; returns the hip drop that keeps soles on the ground."""
    for S, _s in SIDES:
        x, y, z = r.get(S + "UpperLeg", (0, 0, 0))
        r[S + "UpperLeg"] = (x - a, y, z)
        r[S + "LowerLeg"] = (2 * a, 0, 0)
        r[S + "Foot"] = (-a, 0, 0)
    return -(LEG_L1 + LEG_L2) * (1 - math.cos(math.radians(a)))


def _to_pose(arm, rots, hips_dz=0.0, quats=None):
    out = {}
    for b in DEFORM_BONES:
        q = (quats or {}).get(b)
        out[b] = (q if q is not None else rc.local_quat(arm, b, rots.get(b, (0, 0, 0))), None)
    out["Hips"] = (out["Hips"][0], rc.local_offset(arm, "Hips", (0, 0, hips_dz)))
    return out


def idle_pose(arm, f):
    ph = 2 * math.pi * f / TAKES["Idle"]
    s = math.sin(ph)
    breath = 0.5 + 0.5 * s
    r = _relaxed()
    r["Hips"] = (0, 1.2 * s, 0)
    r["LeftUpperLeg"] = r["RightUpperLeg"] = (0, -1.2 * s, 0)   # legs stay vertical, feet planted
    r["Spine"] = (0.5 + 0.5 * s, -0.7 * s, 0)
    r["Chest"] = (-1.2 * s, -0.5 * s, 0)
    r["Neck"] = (0.4 * s, 0, 0)
    r["Head"] = (0.8 * math.sin(2 * ph), 0.6 * s, 3.0 * math.sin(ph + 0.8))
    _both(r, "Shoulder", (0, -1.8 * breath, 0))
    _both(r, "UpperArm", (-4 + 1.5 * math.sin(ph + 0.6), 68 - 1.2 * breath, 0))
    return _to_pose(arm, r)


def _throw_keys():
    base = _relaxed()

    def k(hips=(0, 0, 0), spine=(0, 0, 0), chest=(0, 0, 0), neck=(0, 0, 0), head=(0, 0, 0),
          rua=None, rla=None, rh=None, lua=None, lla=None, crouch=0.0):
        r = dict(base)
        r.update(Hips=hips, Spine=spine, Chest=chest, Neck=neck, Head=head)
        for name, v in (("RightUpperArm", rua), ("RightLowerArm", rla), ("RightHand", rh),
                        ("LeftUpperArm", lua), ("LeftLowerArm", lla)):
            if v is not None:
                r[name] = v
        r["LeftUpperLeg"] = r["RightUpperLeg"] = (0, 0, -hips[2])     # feet keep facing forward
        dz = _crouch(r, crouch)
        return r, dz
    return [
        (0, k()),
        (9, k(hips=(0, 0, -8), spine=(-2, 0, -7), chest=(-3, 1, -8), neck=(0, 0, 6), head=(0, 0, 10),
              rua=(42, -66, 0), rla=(0, 0, 26), rh=(12, 0, 8), lua=(-25, 68, 0), lla=(0, 0, -28), crouch=10)),
        (16, k(hips=(0, 0, 8), spine=(5, 0, 8), chest=(6, -2, 9), neck=(2, 0, -5), head=(-3, 0, -9),
               rua=(-105, -62, 0), rla=(0, 0, 8), rh=(-20, 0, 0), lua=(18, 70, 0), lla=(0, 0, -16), crouch=2)),
        (22, k(hips=(0, 0, 12), spine=(8, 0, 10), chest=(9, -3, 11), neck=(3, 0, -6), head=(2, 0, -12),
               rua=(-130, -58, 6), rla=(0, 0, 14), rh=(-28, 0, 0), lua=(22, 70, 0), lla=(0, 0, -14), crouch=6)),
        (32, k(hips=(0, 0, 4), spine=(2, 0, 3), chest=(2, 0, 3), head=(0, 0, -3),
               rua=(-35, -68, 0), rla=(0, 0, 18), rh=(0, 0, 4), lua=(-8, 68, 0), crouch=3)),
        (45, k()),
    ]


def throw_pose(arm, f, _keys=[]):
    if not _keys:
        _keys.extend(_throw_keys())
    names = DEFORM_BONES
    flat = [(t, tuple(c for b in names for c in r.get(b, (0, 0, 0))) + (dz,)) for t, (r, dz) in _keys]
    v = rc.hermite_keys(flat, f)
    rots = {b: v[3 * i:3 * i + 3] for i, b in enumerate(names)}
    return _to_pose(arm, rots, hips_dz=v[-1])


def _basis(d, p):
    x = d.normalized()
    y = (p - x * p.dot(x)).normalized()
    return Matrix((x, y, x.cross(y))).transposed()


def carry_arm_quats(arm):
    """Analytic 2-bone IK (rest chest) so both palms hold the bin rim at Socket_Carry; constant over the cycle."""
    out = {}
    for S, s in SIDES:
        bua, bla, bh = (arm.data.bones[S + n] for n in ("UpperArm", "LowerArm", "Hand"))
        sj = bua.head_local
        l1, l2 = bua.length, bla.length
        hand_dir = Vector((0, -0.8, -0.6)).normalized()
        wrist = Vector((s * 0.162, -0.24, 0.75)) - hand_dir * 0.05
        pole = sj + Vector((s * 0.25, 0.25, -0.15))
        d = (wrist - sj).length
        if d >= l1 + l2:
            raise RuntimeError("carry pose out of reach")
        u = (wrist - sj) / d
        v = (pole - sj) - u * (pole - sj).dot(u)
        v.normalize()
        a = (l1 * l1 - l2 * l2 + d * d) / (2 * d)
        elbow = sj + u * a + v * math.sqrt(l1 * l1 - a * a)
        r_ua, r_la, r_h = (b.matrix_local.to_3x3() for b in (bua, bla, bh))
        q1 = r_ua.col[1].rotation_difference(elbow - sj).to_matrix()
        q2 = (q1 @ r_la.col[1]).rotation_difference(wrist - elbow).to_matrix()
        cur = q2 @ q1 @ r_h
        rh = _basis(hand_dir, Vector((-s, 0, 0))) @ _basis(cur.col[1], q2 @ q1 @ -Z).transposed()
        out[S + "UpperArm"] = (r_ua.inverted() @ q1 @ r_ua).to_quaternion()
        out[S + "LowerArm"] = (r_la.inverted() @ q1.inverted() @ q2 @ q1 @ r_la).to_quaternion()
        out[S + "Hand"] = (r_h.inverted() @ (q2 @ q1).inverted() @ rh @ q2 @ q1 @ r_h).to_quaternion()
    return out


def carry_pose(arm, f, _arms={}):
    if not _arms:
        _arms.update(carry_arm_quats(arm))
    ph = 2 * math.pi * f / TAKES["CarryBin"]
    s, c = math.sin(ph), math.cos(ph)
    amp = 22.0
    r = {}
    ext = []
    for S, sgn in (("Left", 1.0), ("Right", -1.0)):
        th = -amp * s * sgn                                   # thigh pitch, legs in anti-phase
        cs = c * sgn
        knee = 6 + 40 * max(0.0, cs) ** 1.5                   # swing leg bends most when passing
        r[S + "UpperLeg"] = (th, 0, 0)
        r[S + "LowerLeg"] = (knee, 0, 0)
        r[S + "Foot"] = (-(th + knee) - 6 * max(0.0, cs), 0, 0)
        a1 = math.radians(th)
        ext.append(LEG_L1 * math.cos(a1) + LEG_L2 * math.cos(a1 + math.radians(knee)))
    dz = max(ext) - (LEG_L1 + LEG_L2)                         # stance foot stays on the ground
    yaw, roll = -4 * s, 3 * c
    r["Hips"] = (0, roll, yaw)
    for S in ("Left", "Right"):
        x, y, z = r[S + "UpperLeg"]
        r[S + "UpperLeg"] = (x, -roll, -yaw)
    r["Spine"] = (-4, -2 * c, 2.5 * s)                        # lean back against the load
    r["Chest"] = (-1 + 1.0 * math.sin(2 * ph), -1 * c, 2 * s)
    r["Neck"] = (2, 0, 0)
    r["Head"] = (1 - 1.0 * math.sin(2 * ph), 0, 0)
    return _to_pose(arm, r, hips_dz=dz, quats=_arms)


def build_actions(arm):
    rc.key_action(arm, "Idle", TAKES["Idle"], lambda f: idle_pose(arm, f))
    rc.key_action(arm, "ThrowTrash", TAKES["ThrowTrash"], lambda f: throw_pose(arm, f))
    rc.key_action(arm, "CarryBin", TAKES["CarryBin"], lambda f: carry_pose(arm, f))


def attach_props(arm, *objs):
    """Preview only (.blend): parent each prop to its socket bone. The offset comes from the REST pose
    (a BONE parent hangs off the bone tail), so it is right whatever pose is evaluated now."""
    for obj in objs:
        bone = arm.data.bones[SOCKETS[obj.name]]
        obj.parent = arm
        obj.parent_type = "BONE"
        obj.parent_bone = bone.name
        obj.matrix_parent_inverse = Matrix.Identity(4)
        tail = bone.matrix_local @ Matrix.Translation((0, bone.length, 0))
        obj.matrix_basis = tail.inverted() @ Matrix.Translation(bone.head_local)

