"""Low-poly shape builders for the branded trash props: sealed packs / pouches, lathed bottles, grid boxes.

Every prop is built into one Geo: a welded vertex list (coincident points share one vertex) plus faces
grouped by part key. Deformations (fold, crumple, dent, squash, bend) move geo.v in place, so every part
follows the same crease and the seams stay closed. Part key "label" carries UVs in LABEL space (0..1 over
the prop's label region, panels from labels.LAYOUTS); integer keys are palette swatches that
tools_common.assemble box-projects as usual.
"""
import math

import bpy  # noqa: F401  (must be imported before bmesh / mathutils in the bpy wheel)
from mathutils import Matrix, Vector, noise

from kali_blender import labels
from kali_blender import tools_common as tc


class Geo:
    def __init__(self):
        self.v = []
        self.faces = []          # (key, vertex indices, label uvs or None)
        self._weld = {}
        self.xform = None        # optional Matrix applied to new vertices (build a part already posed)

    def vert(self, co):
        co = Vector(co)
        if self.xform is not None:
            co = self.xform @ co
        k = tuple(round(c, 6) for c in co)
        if k not in self._weld:
            self._weld[k] = len(self.v)
            self.v.append(co)
        return self._weld[k]

    def face(self, key, idx, uv=None):
        idx, uv = list(idx), (list(uv) if uv else None)
        for n in range(len(idx) - 1, -1, -1):          # drop repeated corners (collapsed quad -> tri)
            if idx[n] == idx[n - 1] and len(idx) > 3:
                del idx[n]
                if uv:
                    del uv[n]
        if len(set(idx)) >= 3:
            self.faces.append((key, tuple(idx), uv))

    def select(self, pred):
        return [i for i, co in enumerate(self.v) if pred(co)]

    def deform(self, fn, sel=None):
        for i in (range(len(self.v)) if sel is None else sel):
            self.v[i] = Vector(fn(self.v[i]))

    def recentre(self, base=False, keep_z=False):
        """Origin to the bbox centre; base=True: centre of the bbox bottom (standing products); keep_z=True:
        centre in x/y only, heights kept (floating props modelled around their waterline z = 0)."""
        used = sorted({i for _, f, _ in self.faces for i in f})
        lo = Vector([min(self.v[i][a] for i in used) for a in range(3)])
        hi = Vector([max(self.v[i][a] for i in used) for a in range(3)])
        c = (lo + hi) / 2
        if base:
            c.z = lo.z
        if keep_z:
            c.z = 0.0
        for i in used:
            self.v[i] = self.v[i] - c
        return hi - lo

    def objects(self, name):
        """One mesh object per part key, linked to the active collection, tagged for tools_common.assemble."""
        parts = []
        for key in dict.fromkeys(k for k, _, _ in self.faces):
            fs = [(f, uv) for k, f, uv in self.faces if k == key]
            remap = {}
            for f, _ in fs:
                for i in f:
                    remap.setdefault(i, len(remap))
            me = bpy.data.meshes.new(f"{name}_{key}")
            me.from_pydata([self.v[i][:] for i in remap], [], [[remap[i] for i in f] for f, _ in fs])
            if key == "label":
                layer = me.uv_layers.new(name="UVMap")
                flat = [c for _, uv in fs for st in uv for c in st]
                layer.data.foreach_set("uv", flat)
            ob = bpy.data.objects.new(f"{name}_{key}", me)
            bpy.context.collection.objects.link(ob)
            if key == "label":
                ob["kali_label"] = 1
            else:
                tc.tag(ob, key)
            parts.append(ob)
        return parts


def panel_uv(layout, panel, s, t):
    """Map panel-local (s, t) in 0..1 to label space for one of labels.LAYOUTS."""
    x0, y0, x1, y1 = labels.LAYOUTS[layout][panel]
    return (x0 + (x1 - x0) * min(max(s, 0.0), 1.0), y0 + (y1 - y0) * min(max(t, 0.0), 1.0))


# ---------------------------------------------------------------- sealed packs / pouches
def _diag(corner, i, j, nx, nz):
    return {"tl": i + nz - j, "tr": nx - i + nz - j, "bl": i + j, "br": nx - i + j}[corner]


def pillow(geo, W, H, xf, zf, depth, open_edges=(), tear=None, split=None, gusset=False, inner=0):
    """Two printed sheets (front -Y, back +Y) sealed along the rim: sachet, pillow pack or pouch.

    xf, zf    grid fractions 0..1 across the width (x) and height (z); depth(u, v) -> half thickness (m).
    open_edges rim sides left open ("top", "bottom", "left", "right"): the front and back lips separate.
    tear      (corner, k): corner ("tl", "tr", "bl", "br") torn off along the index diagonal d == k, open.
    split     (corner, k): quads on that diagonal are cut along it, so a later fold() creases cleanly.
              Index diagonals are straight lines only where the grid cells near that corner are square.
    gusset    open bottom closed by a floor strip (stand-up pouch).
    inner     palette swatch for the inside of the sheets, added around every opening.
    Front faces take the "pack" label panel as printed; back faces mirror it so the print reads from behind.
    Returns {"F": F, "B": B, "nx": nx, "nz": nz} (vertex index grids for folds / lips).
    """
    nx, nz = len(xf) - 1, len(zf) - 1
    removed = lambda i, j: tear is not None and _diag(tear[0], i, j, nx, nz) < tear[1]

    def is_open(i, j):
        rim_end = i in (0, nx) and j in (0, nz)
        if tear is not None and _diag(tear[0], i, j, nx, nz) == tear[1]:
            return not (i in (0, nx) or j in (0, nz))
        if rim_end:
            return False
        return ((j == nz and "top" in open_edges) or (j == 0 and ("bottom" in open_edges or gusset))
                or (i == 0 and "left" in open_edges) or (i == nx and "right" in open_edges))

    F = [[None] * (nz + 1) for _ in range(nx + 1)]
    B = [[None] * (nz + 1) for _ in range(nx + 1)]
    opened = set()
    for i in range(nx + 1):
        for j in range(nz + 1):
            if removed(i, j):
                continue
            x, z = (xf[i] - 0.5) * W, (zf[j] - 0.5) * H
            rim = i in (0, nx) or j in (0, nz)
            t = depth(xf[i], zf[j]) if (not rim or is_open(i, j)) else 0.0
            if tear is not None and _diag(tear[0], i, j, nx, nz) == tear[1] and not is_open(i, j):
                t = 0.0
            F[i][j] = geo.vert((x, -t, z))
            B[i][j] = geo.vert((x, t, z))
            if is_open(i, j):
                opened.add((i, j))

    def split_diag(i, j):
        if split is None:
            return None
        c, k = split
        if c in ("tl", "br"):
            return "main" if _diag(c, i, j, nx, nz) == k and _diag(c, i + 1, j + 1, nx, nz) == k else None
        return "anti" if _diag(c, i + 1, j, nx, nz) == k and _diag(c, i, j + 1, nx, nz) == k else None

    near = {(i + di, j + dj) for i, j in opened for di in (-1, 0, 1) for dj in (-1, 0, 1)}
    for i in range(nx):
        for j in range(nz):
            quad = [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)]
            kept = [c for c in quad if not removed(*c)]
            if len(kept) < 3:
                continue
            sd = split_diag(i, j) if len(kept) == 4 else None
            if sd == "main":
                polys = [[quad[0], quad[1], quad[2]], [quad[0], quad[2], quad[3]]]
            elif sd == "anti":
                polys = [[quad[0], quad[1], quad[3]], [quad[1], quad[2], quad[3]]]
            else:
                polys = [kept]
            for poly in polys:
                fu = [(xf[a], zf[b]) for a, b in poly]
                bu = [(1 - xf[a], zf[b]) for a, b in reversed(poly)]
                fi = [F[a][b] for a, b in poly]
                bi = [B[a][b] for a, b in reversed(poly)]
                geo.face("label", fi, fu)
                geo.face("label", bi, bu)
                if inner is not None and any(c in near for c in poly):
                    geo.face(inner, list(reversed(fi)))
                    geo.face(inner, list(reversed(bi)))
    if gusset:
        for i in range(nx):
            geo.face("label", [F[i][0], B[i][0], B[i + 1][0], F[i + 1][0]],
                     [(xf[i], 0.004), (xf[i], 0.012), (xf[i + 1], 0.012), (xf[i + 1], 0.004)])
    return {"F": F, "B": B, "nx": nx, "nz": nz}


def box(geo, key, lo, hi, n=(1, 1, 1)):
    """Axis-aligned box from corner lo to corner hi (outward normals), in geo.xform space; n = cuts per axis
    (extra vertices for dents / crumple)."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    nx, ny, nz = n
    dx, dy, dz = (x1 - x0, 0, 0), (0, y1 - y0, 0), (0, 0, z1 - z0)
    grid(geo, key, (x0, y0, z0), dy, dx, ny, nx)                # bottom (-Z)
    grid(geo, key, (x0, y0, z1), dx, dy, nx, ny)                # top
    grid(geo, key, (x0, y0, z0), dx, dz, nx, nz)                # front (-Y)
    grid(geo, key, (x1, y1, z0), (x0 - x1, 0, 0), dz, nx, nz)   # back
    grid(geo, key, (x0, y1, z0), (0, y0 - y1, 0), dz, ny, nz)   # left (-X)
    grid(geo, key, (x1, y0, z0), dy, dz, ny, nz)                # right


def torus(geo, key, R, r, nu=8, nv=4):
    """Ring (shackle, chain link) of radius R and tube radius r around +Z, in geo.xform space."""
    pts = [[geo.vert(((R + r * math.cos(2 * math.pi * j / nv)) * math.cos(2 * math.pi * i / nu),
                      (R + r * math.cos(2 * math.pi * j / nv)) * math.sin(2 * math.pi * i / nu),
                      r * math.sin(2 * math.pi * j / nv))) for j in range(nv)] for i in range(nu)]
    for i in range(nu):
        for j in range(nv):
            i1, j1 = (i + 1) % nu, (j + 1) % nv
            geo.face(key, [pts[i][j], pts[i1][j], pts[i1][j1], pts[i][j1]])


def plateau(x, w):
    """0 at both ends of 0..1, rising smoothly to 1 within w: the flat-topped puff of a full pack."""
    t = min(max(min(x, 1 - x) / w, 0.0), 1.0)
    return t * t * (3 - 2 * t)


def corner_verts(grid, corner, k):
    """Vertex indices of a pack corner region (index diagonal d < k), both sheets."""
    nx, nz = grid["nx"], grid["nz"]
    out = set()
    for i in range(nx + 1):
        for j in range(nz + 1):
            if grid["F"][i][j] is not None and _diag(corner, i, j, nx, nz) < k:
                out.update((grid["F"][i][j], grid["B"][i][j]))
    return sorted(out)


# ---------------------------------------------------------------- lathe (bottles)
def lathe(geo, rings, segs, key, uv=None, cap0=None, cap1=None):
    """Revolve rings [(z, rx, ry)] bottom -> top. Vertex k sits at angle a = 2 pi k / segs, measured from the
    front (-Y) toward +X. key(r) -> part key of band r..r+1; uv(a_mid, a, z) -> label uv for "label" bands.
    cap0 / cap1: part key of the bottom / top cap ngon (None = open). Returns ring vertex index lists."""
    R = []
    for z, rx, ry in rings:
        R.append([geo.vert((rx * math.sin(2 * math.pi * k / segs), -ry * math.cos(2 * math.pi * k / segs), z))
                  for k in range(segs)])
    for r in range(len(rings) - 1):
        kk = key(r)
        for k in range(segs):
            k1 = (k + 1) % segs
            idx = [R[r][k], R[r][k1], R[r + 1][k1], R[r + 1][k]]
            if kk == "label":
                a0, a1 = 2 * math.pi * k / segs, 2 * math.pi * (k + 1) / segs
                am = (a0 + a1) / 2
                zs = (rings[r][0], rings[r][0], rings[r + 1][0], rings[r + 1][0])
                geo.face(kk, idx, [uv(am, a, z) for a, z in zip((a0, a1, a1, a0), zs)])
            else:
                geo.face(kk, idx)
    if cap0 is not None:
        geo.face(cap0, list(reversed(R[0])))
    if cap1 is not None:
        geo.face(cap1, R[-1])
    return R


def wrap_uv(z0, z1):
    """Bottle band on the "wrap" layout: front half (-90..90 deg) on the front panel, back half on the back."""
    def f(am, a, z):
        t = (z - z0) / (z1 - z0)
        front = math.cos(am) > 0
        start = -math.pi / 2 if front else math.pi / 2
        rel = (am - start) % (2 * math.pi) + (a - am)   # measured from the face middle: no wrap at seams
        return panel_uv("wrap", "front" if front else "back", rel / math.pi, t)
    return f


def pair_uv(z0, z1):
    """Flat-oval bottle on the "pair" layout: planar front / back projection (back mirrored to read)."""
    def f(am, a, z):
        t = (z - z0) / (z1 - z0)
        if math.cos(am) > 0:
            return panel_uv("pair", "front", (math.sin(a) + 1) / 2, t)
        return panel_uv("pair", "back", (1 - math.sin(a)) / 2, t)
    return f


# ---------------------------------------------------------------- grids (boxes, trays)
def grid(geo, key, origin, du, dv, nu, nv, uv=None):
    """Subdivided parallelogram origin + s*du + t*dv (s, t in 0..1), normal = du x dv. uv(s, t) -> label uv."""
    o, du, dv = Vector(origin), Vector(du), Vector(dv)
    idx = [[geo.vert(o + du * (a / nu) + dv * (b / nv)) for b in range(nv + 1)] for a in range(nu + 1)]
    for a in range(nu):
        for b in range(nv):
            st = [(a / nu, b / nv), ((a + 1) / nu, b / nv), ((a + 1) / nu, (b + 1) / nv), (a / nu, (b + 1) / nv)]
            geo.face(key, [idx[s][t] for s, t in ((a, b), (a + 1, b), (a + 1, b + 1), (a, b + 1))],
                     [uv(s, t) for s, t in st] if uv else None)
    return idx


# ---------------------------------------------------------------- deformations
def fold(geo, sel, a, b, angle_deg, toward=(0, -1, 0)):
    """Rotate the selected vertices about the line a - b by angle_deg - a crisp paper/film fold. The flap
    starts its swing in the `toward` direction (default: over the printed front, -Y)."""
    a, b = Vector(a), Vector(b)
    axis = (b - a).normalized()
    mid = sum((geo.v[i] for i in sel), Vector()) / max(len(sel), 1) - a
    arm = mid - axis * mid.dot(axis)
    if axis.cross(arm).dot(Vector(toward)) < 0:
        axis = -axis
    rot = Matrix.Rotation(math.radians(angle_deg), 3, axis)
    geo.deform(lambda co: a + rot @ (co - a), sel)


def crumple(geo, amp, freq, seed, sel=None, axes=(0.45, 1.0, 0.45)):
    """Smooth noise displacement (same field for front and back sheets, so they never cross)."""
    off = Vector((seed * 7.31, seed * 3.17, seed * 5.53))
    # one scalar noise per axis: noise.noise is reproducible, noise.noise_vector differs per Blender process
    shift = (Vector((0.0, 0.0, 0.0)), Vector((31.7, 0.0, 0.0)), Vector((0.0, 47.3, 0.0)))

    def f(co):
        p, q = co * freq + off, co * freq * 2.3 + off * 1.7
        n = [noise.noise(p + s) + noise.noise(q + s) * 0.45 for s in shift]
        return co + Vector((n[0] * axes[0], n[1] * axes[1], n[2] * axes[2])) * amp
    geo.deform(f, sel)


def dent(geo, centre, radius, push):
    """Push vertices near `centre` by vector `push`, smooth falloff (thumb dent, crushed corner)."""
    c, p = Vector(centre), Vector(push)

    def f(co):
        d = (co - c).length / radius
        return co + p * ((1 - d * d) ** 2 if d < 1 else 0.0)
    geo.deform(f)


def lay_flat(geo, tilt=(8.0, 5.0), on_side=False):
    """Floating pose (the game spawns trash with a random yaw only): printed front (-Y) turned up (+Z), then
    tilted by tilt degrees about X and Y. on_side: lay a standing bottle down first (long axis Z -> X)."""
    R = Matrix.Rotation(math.radians(tilt[1]), 3, "Y") @ Matrix.Rotation(math.radians(-90 + tilt[0]), 3, "X")
    if on_side:
        R = R @ Matrix.Rotation(math.radians(90), 3, "Y")
    geo.deform(lambda co: R @ co)


def bend(geo, axis, pivot, angle_deg, lo, hi, along=2):
    """Bend: vertices beyond `lo` along coordinate `along` rotate about `axis` through `pivot`, ramping to
    angle_deg at `hi` (keeps the low part straight)."""
    p, ax = Vector(pivot), Vector(axis).normalized()

    def f(co):
        t = min(max((co[along] - lo) / (hi - lo), 0.0), 1.0)
        return p + Matrix.Rotation(math.radians(angle_deg) * t, 3, ax) @ (co - p)
    geo.deform(f)
