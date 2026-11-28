"""SM_Env_Vegetasi (Wesley) - kampung riverside plants, textured to sit with the buildings.

One FBX, one object per plant (pivot = ground centre, Unity coordinates):
  SM_Env_PohonPisang    banana clump stem + 8 torn leaves, 2 dry hanging leaves, a fruit bunch
  SM_Env_PohonKelapa    leaning ringed trunk, 11 drooping fronds, coconut cluster (~8 m)
  SM_Env_PohonKetapang  ketapang (Terminalia) - the tiered "pagoda" shade tree of Indonesian
                        river banks: trunk + 3 horizontal leaf tiers (~6 m)
  SM_Env_Bambu          bamboo clump, 9 culms leaning out with leaf crowns (~7 m)
  SM_Env_Semak          shrub: leafy core + fluffy cards (~1 m)
  SM_Env_Rumput         wild grass tuft (3 crossed cards, 0.7 m)
  SM_Env_Alang          tall alang-alang / reeds for the river edge (1.4 m)
  SM_Env_RumputKering   dry, dusty grass near the Gunung Sampah
  SM_Env_Batu           two river boulders

Leaf cards use alpha-clipped double-sided materials; their normals are bent outward from
the crown centre (grass: straight up) so foliage shades like a volume instead of flat paper.
"""
import math
import random

from wesley_env.meshkit import MeshKit

FBX_NAME = "SM_Env_Vegetasi"
NAME = "SM_Env_PohonPisang"
TRI_BUDGET = (6, 2500)

KULIT, BATANG, PISANG, KELAPA, RIMBUN, RIMBUN_PADAT, RUMPUT, KERING, BAMBU, BATU, PISANG_KERING = range(11)
MATERIALS = (
    ("M_Env_KulitPohon", (0.42, 0.33, 0.25, 1.0)),
    ("M_Env_BatangPisang", (0.50, 0.55, 0.30, 1.0)),
    ("M_Env_DaunPisang", (1.0, 1.0, 1.0, 1.0)),
    ("M_Env_DaunKelapa", (1.0, 1.0, 1.0, 1.0)),
    ("M_Env_DaunRimbun", (1.0, 1.0, 1.0, 1.0)),
    ("M_Env_DaunRimbunPadat", (0.85, 0.85, 0.85, 1.0)),
    ("M_Env_Rumput", (1.0, 1.0, 1.0, 1.0)),
    ("M_Env_RumputKering", (0.85, 0.74, 0.52, 1.0)),
    ("M_Env_Bambu", (1.0, 1.0, 1.0, 1.0)),
    ("M_Env_BatuSungai", (0.42, 0.40, 0.36, 1.0)),
    ("M_Env_DaunPisangKering", (0.95, 0.70, 0.42, 1.0)),
)
CARDS = {PISANG, KELAPA, RIMBUN, RUMPUT, KERING, PISANG_KERING}
SMOOTH = {KULIT, BATANG, RIMBUN_PADAT, BAMBU, BATU}


class Plant(MeshKit):
    """MeshKit that remembers, per face, the point its card normals should bend away from."""

    def __init__(self):
        super().__init__(uv_tile=1.0)
        self.bend = []                      # per face: None (keep) / (x, y, z) centre / "up"

    def _face(self, pts, mat, uv):
        super()._face(pts, mat, uv)
        self.bend.append(None)

    def card(self, pts, mat, uv, bend):
        super()._face(pts, mat, [(0, 0)] * len(pts))
        self.uvs[-1] = list(uv)
        self.bend.append(bend)

    def build(self, name, materials):
        ob = super().build(name, materials)
        me = ob.data
        from wesley_env.terrain import unity_to_blender
        for p in me.polygons:
            p.use_smooth = p.material_index in SMOOTH
        me.update()
        normals = [tuple(n.vector) for n in me.corner_normals]
        bends = self._poly_bends(me)
        for p in me.polygons:
            b = bends.get(p.index)
            if b is None:
                continue
            for li in p.loop_indices:
                if b == "up":
                    n = (0.0, 0.0, 1.0)
                else:
                    c = unity_to_blender(*b)
                    v = me.vertices[me.loops[li].vertex_index].co
                    d = (v.x - c[0], v.y - c[1], (v.z - c[2]) + 0.35 * abs(v.z - c[2]) + 0.25)
                    ln = math.sqrt(sum(a * a for a in d)) or 1.0
                    n = tuple(a / ln for a in d)
                normals[li] = n
        me.normals_split_custom_set(normals)
        return ob

    def _poly_bends(self, me):
        """Match Blender polygons back to MeshKit faces by material order + centroid."""
        from wesley_env.terrain import unity_to_blender
        want = {}
        for f, b in enumerate(self.bend):
            if b is None:
                continue
            pts = [unity_to_blender(*self.verts[i]) for i in self.faces[f]]
            key = tuple(round(sum(p[a] for p in pts) / len(pts), 3) for a in range(3))
            want[key] = b
        out = {}
        for p in me.polygons:
            key = tuple(round(c, 3) for c in p.center)
            if key in want:
                out[p.index] = want[key]
        return out


# ---------------- shared pieces ----------------

def frustum(k, p0, r0, p1, r1, mat, seg=8, v0=0.0, v1=1.0, caps=False):
    """Tapered tube from p0 to p1 (any direction), UV u around, v along."""
    d = [p1[i] - p0[i] for i in range(3)]
    ln = math.sqrt(sum(c * c for c in d)) or 1.0
    d = [c / ln for c in d]
    up = (1.0, 0.0, 0.0) if abs(d[1]) > 0.95 else (0.0, 1.0, 0.0)
    s = [d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0]]
    sl = math.sqrt(sum(c * c for c in s))
    s = [c / sl for c in s]
    u = [s[1] * d[2] - s[2] * d[1], s[2] * d[0] - s[0] * d[2], s[0] * d[1] - s[1] * d[0]]
    ring = lambda p, r: [tuple(p[i] + r * (math.cos(2 * math.pi * j / seg) * s[i] + math.sin(2 * math.pi * j / seg) * u[i]) for i in range(3)) for j in range(seg)]
    a, b = ring(p0, r0), ring(p1, r1)
    for j in range(seg):
        j1 = (j + 1) % seg
        k._face([a[j], a[j1], b[j1], b[j]], mat, [(j / seg, v0), ((j + 1) / seg, v0), ((j + 1) / seg, v1), (j / seg, v1)])
    if caps:
        k._face(list(reversed(b)), mat, [(0.5, 0.5)] * seg)
        k._face(a, mat, [(0.5, 0.5)] * seg)


def blob(k, rng, c, r, mat, seg=8, rings=5, jitter=0.18, uv=(0.18, 0.18, 0.82, 0.82)):
    """Closed lumpy ellipsoid (leaf mass, rock, fruit). r = (rx, ry, rz)."""
    pts = []
    for i in range(1, rings):
        lat = -math.pi / 2 + math.pi * i / rings
        row = []
        for j in range(seg):
            lon = 2 * math.pi * (j + 0.5 * (i % 2)) / seg
            q = 1 + rng.uniform(-jitter, jitter)
            row.append((c[0] + r[0] * q * math.cos(lat) * math.cos(lon), c[1] + r[1] * q * math.sin(lat),
                        c[2] + r[2] * q * math.cos(lat) * math.sin(lon)))
        pts.append(row)
    bot, top = (c[0], c[1] - r[1], c[2]), (c[0], c[1] + r[1] * (1 + rng.uniform(-jitter, jitter) * 0.5), c[2])
    u0, v0, u1, v1 = uv
    U = lambda j: u0 + (u1 - u0) * (j % (seg + 1)) / seg
    V = lambda i: v0 + (v1 - v0) * i / rings
    for j in range(seg):
        j1 = (j + 1) % seg
        k._face([bot, pts[0][j1], pts[0][j]], mat, [])
        k.uvs[-1] = [(U(j + 0.5), V(0)), (U(j + 1), V(1)), (U(j), V(1))]
        for i in range(rings - 2):
            k._face([pts[i][j], pts[i][j1], pts[i + 1][j1], pts[i + 1][j]], mat, [])
            k.uvs[-1] = [(U(j), V(i + 1)), (U(j + 1), V(i + 1)), (U(j + 1), V(i + 2)), (U(j), V(i + 2))]
        k._face([pts[-1][j], pts[-1][j1], top], mat, [])
        k.uvs[-1] = [(U(j), V(rings - 1)), (U(j + 1), V(rings - 1)), (U(j + 0.5), V(rings))]


def leaf_strip(k, base, yaw, length, width, rise, droop, mat, bend, segs=4, fold=0.12, twist=0.0):
    """Arching leaf / frond card: rises from `base` along `yaw`, droops toward the tip,
    folded along its midrib (V shape) so it reads from every side."""
    cy, sy = math.cos(yaw), math.sin(yaw)
    side = (-sy, 0.0, cy)
    rows = []
    for i in range(segs + 1):
        t = i / segs
        out = length * t * (1 - 0.12 * t)
        y = base[1] + rise * math.sin(math.pi * 0.6 * t) - droop * t * t
        c = (base[0] + cy * out, y, base[2] + sy * out)
        w = width * 0.5 * math.sin(math.pi * min(1.0, 0.08 + t * 0.95)) ** 0.6
        tw = twist * t
        l = tuple(c[a] + side[a] * w for a in range(3))
        r = tuple(c[a] - side[a] * w for a in range(3))
        l = (l[0], l[1] - fold * w * 2 + tw * w, l[2])
        r = (r[0], r[1] - fold * w * 2 - tw * w, r[2])
        rows.append((l, c, r, t))
    for (l0, c0, r0, t0), (l1, c1, r1, t1) in zip(rows, rows[1:]):
        k.card([l0, c0, c1, l1], mat, [(0.0, t0), (0.5, t0), (0.5, t1), (0.0, t1)], bend)
        k.card([c0, r0, r1, c1], mat, [(0.5, t0), (1.0, t0), (1.0, t1), (0.5, t1)], bend)


def cross_cards(k, c, w, h, mat, n=3, rng=None, bend="up", tilt=0.0):
    """n vertical cards crossing at c (grass tufts, shrub fluff)."""
    for i in range(n):
        a = math.pi * i / n + (rng.uniform(-0.2, 0.2) if rng else 0.0)
        dx, dz = math.cos(a) * w / 2, math.sin(a) * w / 2
        tx, tz = math.cos(a + math.pi / 2) * tilt, math.sin(a + math.pi / 2) * tilt
        k.card([(c[0] - dx, c[1], c[2] - dz), (c[0] + dx, c[1], c[2] + dz),
                (c[0] + dx + tx, c[1] + h, c[2] + dz + tz), (c[0] - dx + tx, c[1] + h, c[2] - dz + tz)],
               mat, [(0, 0), (1, 0), (1, 1), (0, 1)], bend)


def canopy(k, rng, c, r, n_cards, card, mat=RIMBUN):
    """Leafy mass: opaque lumpy core + outward-facing alpha cards for a soft silhouette."""
    blob(k, rng, c, (r[0] * 0.8, r[1] * 0.8, r[2] * 0.8), RIMBUN_PADAT, seg=8, rings=5, jitter=0.2)
    for _ in range(n_cards):
        th, ph = rng.uniform(0, 2 * math.pi), rng.uniform(-0.25, 1.0)
        d = (math.cos(ph) * math.cos(th), math.sin(ph), math.cos(ph) * math.sin(th))
        p = (c[0] + d[0] * r[0] * 0.85, c[1] + d[1] * r[1] * 0.85, c[2] + d[2] * r[2] * 0.85)
        up = (0.0, 1.0, 0.0) if abs(d[1]) < 0.9 else (1.0, 0.0, 0.0)
        s = (up[1] * d[2] - up[2] * d[1], up[2] * d[0] - up[0] * d[2], up[0] * d[1] - up[1] * d[0])
        sl = math.sqrt(sum(a * a for a in s)) or 1.0
        s = tuple(a / sl for a in s)
        t = (d[1] * s[2] - d[2] * s[1], d[2] * s[0] - d[0] * s[2], d[0] * s[1] - d[1] * s[0])
        h = card * rng.uniform(0.8, 1.2) * 0.5
        q = [tuple(p[a] + (sx * s[a] + ty * t[a]) * h for a in range(3)) for sx, ty in ((-1, -1), (1, -1), (1, 1), (-1, 1))]
        k.card(q, mat, [(0, 0), (1, 0), (1, 1), (0, 1)], c)


# ---------------- plants ----------------

def pisang():
    k, rng = Plant(), random.Random(7)
    frustum(k, (0, -0.2, 0), 0.17, (0, 1.4, 0), 0.14, BATANG, seg=9, v1=1.4)
    frustum(k, (0, 1.4, 0), 0.14, (0.04, 2.9, 0.02), 0.1, BATANG, seg=9, v0=1.4, v1=2.9)
    frustum(k, (0.3, -0.2, 0.25), 0.08, (0.32, 0.9, 0.27), 0.06, BATANG, seg=6, v1=1.1)   # sucker shoot
    top = (0.04, 2.85, 0.02)
    for i in range(8):
        yaw = i * 2 * math.pi / 8 + rng.uniform(-0.25, 0.25)
        leaf_strip(k, top, yaw, rng.uniform(2.0, 2.5), rng.uniform(0.62, 0.75), rng.uniform(0.6, 1.0),
                   rng.uniform(1.2, 1.9), PISANG, (0.0, 2.6, 0.0), segs=4, fold=0.1, twist=rng.uniform(-0.15, 0.15))
    for i, yaw in enumerate((0.7, 3.6)):                                                    # dry leaves hanging down
        cy, sy = math.cos(yaw), math.sin(yaw)
        b = (0.12 * cy, 2.2, 0.12 * sy)
        w = 0.26
        for j in range(3):
            y0, y1 = 2.2 - j * 0.45, 2.2 - (j + 1) * 0.45
            o0, o1 = 0.12 + j * 0.05, 0.12 + (j + 1) * 0.05
            k.card([(o0 * cy - w * sy, y0, o0 * sy + w * cy), (o0 * cy + w * sy, y0, o0 * sy - w * cy),
                    (o1 * cy + w * sy, y1, o1 * sy - w * cy), (o1 * cy - w * sy, y1, o1 * sy + w * cy)],
                   PISANG_KERING, [(0.1, 1 - j / 3), (0.9, 1 - j / 3), (0.9, 1 - (j + 1) / 3), (0.1, 1 - (j + 1) / 3)], (0.0, 2.0, 0.0))
    frustum(k, (0.05, 2.4, 0.03), 0.025, (0.42, 2.05, 0.1), 0.02, BATANG, seg=5)             # bunch stalk
    blob(k, rng, (0.45, 1.85, 0.1), (0.17, 0.26, 0.17), BATANG, seg=7, rings=4, jitter=0.12)  # fruit bunch
    return k


def kelapa():
    k, rng = Plant(), random.Random(11)
    pts, lean = [], 1.3
    for i in range(7):
        t = i / 6
        pts.append((lean * t ** 1.6, -0.2 + 7.6 * t, 0.25 * math.sin(t * 2.0)))
    for i in range(6):
        frustum(k, pts[i], 0.2 - 0.012 * i, pts[i + 1], 0.2 - 0.012 * (i + 1), KULIT, seg=9, v0=i * 1.3, v1=(i + 1) * 1.3)
    crown = (pts[-1][0], pts[-1][1] + 0.05, pts[-1][2])
    blob(k, rng, (crown[0], crown[1] + 0.05, crown[2]), (0.22, 0.25, 0.22), BATANG, seg=8, rings=4, jitter=0.1)
    for i in range(11):
        yaw = i * 2 * math.pi / 11 + rng.uniform(-0.15, 0.15)
        up = i < 3
        leaf_strip(k, crown, yaw, rng.uniform(2.8, 3.4), 1.3, 0.9 if up else 0.45, 2.3 if up else 2.8,
                   KELAPA, (crown[0], crown[1] + 0.4, crown[2]), segs=5, fold=0.18)
    for i in range(5):                                                                     # coconuts
        a = i * 1.26
        blob(k, rng, (crown[0] + 0.24 * math.cos(a), crown[1] - 0.32, crown[2] + 0.24 * math.sin(a)),
             (0.14, 0.16, 0.14), BATANG, seg=6, rings=4, jitter=0.06)
    return k


def tier(k, rng, c, rad, thick, n_cards):
    """One flat ketapang leaf tier: wide flattened leaf mass + cards fanned around its rim and top."""
    blob(k, rng, c, (rad, thick, rad * 0.92), RIMBUN_PADAT, seg=10, rings=4, jitter=0.12)
    for i in range(n_cards):
        a = i * 2 * math.pi / n_cards + rng.uniform(-0.2, 0.2)
        rr = rad * rng.uniform(0.75, 1.0)
        p = (c[0] + rr * math.cos(a), c[1] + rng.uniform(-0.05, 0.15), c[2] + rr * math.sin(a))
        h = rng.uniform(0.7, 1.0)
        ca, sa = math.cos(a), math.sin(a)
        q = [(p[0] - sa * h - ca * h * 0.6, p[1] - 0.18, p[2] + ca * h - sa * h * 0.6),
             (p[0] + sa * h - ca * h * 0.6, p[1] - 0.18, p[2] - ca * h - sa * h * 0.6),
             (p[0] + sa * h + ca * h * 0.6, p[1] + 0.32, p[2] - ca * h + sa * h * 0.6),
             (p[0] - sa * h + ca * h * 0.6, p[1] + 0.32, p[2] + ca * h + sa * h * 0.6)]
        k.card(q, RIMBUN, [(0, 0), (1, 0), (1, 1), (0, 1)], (c[0], c[1] - 0.6, c[2]))
    for i in range(max(2, n_cards // 3)):                                                  # leaves on top of the tier
        a = rng.uniform(0, 2 * math.pi); rr = rad * rng.uniform(0.1, 0.55); h = 0.85
        p = (c[0] + rr * math.cos(a), c[1] + thick * 0.85, c[2] + rr * math.sin(a))
        k.card([(p[0] - h, p[1], p[2] - h), (p[0] + h, p[1], p[2] - h), (p[0] + h, p[1] + 0.15, p[2] + h), (p[0] - h, p[1] + 0.15, p[2] + h)],
               RIMBUN, [(0, 0), (1, 0), (1, 1), (0, 1)], (c[0], c[1] - 0.6, c[2]))


def ketapang():
    """Terminalia catappa: straight trunk, branches in horizontal whorls, flat leaf tiers."""
    k, rng = Plant(), random.Random(13)
    frustum(k, (0, -0.3, 0), 0.32, (0, 1.2, 0), 0.24, KULIT, seg=10, v1=1.5)
    frustum(k, (0, 1.2, 0), 0.24, (0.1, 5.7, 0.05), 0.1, KULIT, seg=10, v0=1.5, v1=5.9)
    for t_i, (y, rad) in enumerate(((3.1, 3.2), (4.45, 2.4), (5.65, 1.45))):
        n = 5 - t_i
        for b in range(n):                                                                 # whorl of branches
            a = b * 2 * math.pi / n + t_i * 0.6
            end = (rad * 0.8 * math.cos(a), y + 0.05, rad * 0.8 * math.sin(a))
            frustum(k, (0.05, y - 0.45, 0.02), 0.09, end, 0.035, KULIT, seg=6, v1=rad)
        tier(k, rng, (0.06 * t_i, y + 0.12, 0.03 * t_i), rad, 0.32, 10 - 2 * t_i)
    return k


def bambu():
    k, rng = Plant(), random.Random(17)
    for i in range(9):
        a = i * 2 * math.pi / 9 + rng.uniform(-0.2, 0.2)
        r0 = rng.uniform(0.08, 0.35)
        base = (r0 * math.cos(a), -0.3, r0 * math.sin(a))
        h, out = rng.uniform(5.5, 7.5), rng.uniform(1.2, 2.6)
        prev, rad = base, 0.07
        for s in range(4):
            t = (s + 1) / 4
            p = (base[0] + out * t * t * math.cos(a), -0.3 + h * t, base[2] + out * t * t * math.sin(a))
            frustum(k, prev, rad, p, rad * 0.85, BAMBU, seg=6, v0=s * h / 4 / 2.0, v1=(s + 1) * h / 4 / 2.0)
            prev, rad = p, rad * 0.85
        for j in range(4):                                                                 # feathery drooping leaf sprays
            t = 0.5 + 0.16 * j
            p = (base[0] + out * t * t * math.cos(a), -0.3 + h * t, base[2] + out * t * t * math.sin(a))
            for side in (-1, 1):
                leaf_strip(k, p, a + side * rng.uniform(0.6, 1.3), rng.uniform(1.2, 1.7), 0.75, 0.25, 0.9,
                           KELAPA, (0.0, h * 0.6, 0.0), segs=3, fold=0.1)
    return k


def semak():
    k, rng = Plant(), random.Random(19)
    for c, r in (((0.0, 0.45, 0.0), (0.55, 0.45, 0.5)), ((0.45, 0.32, 0.2), (0.38, 0.32, 0.36)), ((-0.35, 0.3, -0.25), (0.36, 0.3, 0.34))):
        canopy(k, rng, c, r, 4, 0.9)
    return k


def rumput(mat=RUMPUT, w=1.0, h=0.7, seed=23):
    k, rng = Plant(), random.Random(seed)
    cross_cards(k, (0.0, -0.05, 0.0), w, h, mat, n=3, rng=rng, tilt=0.05)
    return k


def batu():
    k, rng = Plant(), random.Random(29)
    blob(k, rng, (0.0, 0.15, 0.0), (0.7, 0.45, 0.55), BATU, seg=7, rings=4, jitter=0.16, uv=(0, 0, 1, 1))
    blob(k, rng, (0.85, 0.02, 0.4), (0.35, 0.22, 0.3), BATU, seg=6, rings=4, jitter=0.2, uv=(0, 0, 1, 1))
    return k


PLANTS = {
    "SM_Env_PohonPisang": pisang,
    "SM_Env_PohonKelapa": kelapa,
    "SM_Env_PohonKetapang": ketapang,
    "SM_Env_Bambu": bambu,
    "SM_Env_Semak": semak,
    "SM_Env_Rumput": lambda: rumput(),
    "SM_Env_Alang": lambda: rumput(RUMPUT, 1.3, 1.45, 31),
    "SM_Env_RumputKering": lambda: rumput(KERING, 1.1, 0.55, 37),
    "SM_Env_Batu": batu,
}


def build():
    return [fn().build(name, MATERIALS) for name, fn in PLANTS.items()]


def stats(obs):
    tris = {ob.name: sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in obs}
    lo, hi = TRI_BUDGET
    return {"name": FBX_NAME, "tris": tris, "in_budget": all(lo <= t <= hi for t in tris.values())}
