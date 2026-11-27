"""SM_Env_GunungSampah_3Tiers (Wesley) - terraced trash-mountain core, 2,500-4,000 tris.

One mesh is shared by the 3 gunung_node items (Barat / Puncak / Timur). MapJsonImporter
spawns it at groundY 0 and GunungNodeController shrinks transform.localScale.y as it is
dredged, so the pivot sits at the base centre (Y = 0) and a skirt runs down to -2.2 m to
hide the seam on the riverbed (-2.0) and on the banks (+1.40).

Shape: lobed outline, 3 terraces (ledges at ~4 m and ~8 m, peak ~12 m) with value-noise
lumps. Vertex colour R = 1 on clean slopes and drops to ~0.35 on the terrace ledges, so
SG_TrashTriplanar can darken the grime that collects where tiers meet. The visible detail
(JC's real trash props) is scattered on top in PF_Env_GunungSampah_3Tiers.
"""
import math

import bmesh
import bpy

from wesley_env.terrain import unity_to_blender

NAME = "SM_Env_GunungSampah_3Tiers"
TRI_BUDGET = (2500, 4000)
RX, RZ = 16.0, 9.5          # half footprint (m) - fits between the Barat/Puncak/Timur nodes
RINGS, SEGS = 26, 56
MATERIALS = (("M_Env_GunungSampah", (0.35, 0.29, 0.22, 1.0)),)

# (rho, height): piecewise profile from the rim (rho=1) to the summit (rho=0)
PROFILE = [(1.00, -2.2), (0.93, 0.2), (0.70, 4.0), (0.60, 4.4), (0.40, 8.0), (0.31, 8.4), (0.0, 12.0)]
LEDGES = ((0.70, 0.60), (0.40, 0.31))


def _hash(ix, iz, seed):
    h = (ix * 374761393 + iz * 668265263 + seed * 2147483647) & 0xFFFFFFFF
    h = (h ^ (h >> 13)) * 1274126177 & 0xFFFFFFFF
    return ((h ^ (h >> 16)) & 0xFFFF) / 65535.0


def _noise(x, z, seed=0):
    ix, iz = math.floor(x), math.floor(z)
    fx, fz = x - ix, z - iz
    fx, fz = fx * fx * (3 - 2 * fx), fz * fz * (3 - 2 * fz)
    a, b = _hash(ix, iz, seed), _hash(ix + 1, iz, seed)
    c, d = _hash(ix, iz + 1, seed), _hash(ix + 1, iz + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fz) + (c * (1 - fx) + d * fx) * fz


def _fbm(x, z, seed=0, octaves=4):
    s, amp, tot = 0.0, 1.0, 0.0
    for o in range(octaves):
        s += _noise(x * 2 ** o, z * 2 ** o, seed + o) * amp
        tot += amp
        amp *= 0.5
    return s / tot


def _profile(rho):
    for (r0, h0), (r1, h1) in zip(PROFILE, PROFILE[1:]):
        if r1 <= rho <= r0:
            t = (r0 - rho) / (r0 - r1)
            t = t * t * (3 - 2 * t) if h1 - h0 > 1.0 else t
            return h0 + (h1 - h0) * t
    return PROFILE[-1][1]


def _ledge_dirt(rho):
    d = 1.0
    for r0, r1 in LEDGES:
        mid, half = (r0 + r1) * 0.5, (r0 - r1) * 0.5 + 0.05
        d = min(d, 0.35 + 0.65 * min(1.0, abs(rho - mid) / half))
    return d


def build():
    verts, cols, faces = [], [], []
    for i in range(RINGS + 1):
        rho = i / RINGS
        ring = [0] if i == 0 else range(SEGS)
        for j in ring:
            th = 2 * math.pi * j / SEGS
            lobe = 1.0 + 0.10 * math.sin(3 * th + 0.7) + 0.06 * math.sin(5 * th + 2.1)
            x, z = rho * RX * lobe * math.cos(th), rho * RZ * lobe * math.sin(th)
            y = _profile(rho)
            if rho < 0.95:  # lumpy trash, strongest on the slopes
                y += (_fbm(x * 0.25, z * 0.25, 3) - 0.5) * 2.2 * (0.4 + 0.6 * math.sin(math.pi * min(rho, 0.93) / 0.93))
            verts.append(unity_to_blender(x, y, z))
            cols.append(_ledge_dirt(rho) * (0.85 + 0.15 * _fbm(x * 0.6, z * 0.6, 9)))
    for j in range(SEGS):  # summit fan
        faces.append((0, 1 + j, 1 + (j + 1) % SEGS))
    for i in range(1, RINGS):
        a0, b0 = 1 + (i - 1) * SEGS, 1 + i * SEGS
        for j in range(SEGS):
            j1 = (j + 1) % SEGS
            faces.append((a0 + j, b0 + j, b0 + j1, a0 + j1))

    old = bpy.data.objects.get(NAME)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    me = bpy.data.meshes.new(NAME)
    me.from_pydata(verts, [], faces)
    for mname, col in MATERIALS:
        mat = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
        mat.diffuse_color = col
        me.materials.append(mat)
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (-co.x / 4.0, -co.y / 4.0)   # Unity X/Z planar, 4 m tiles
    ca = me.color_attributes.new("Col", "BYTE_COLOR", "POINT")
    for k, r in enumerate(cols):
        ca.data[k].color = (r, r, r, 1.0)

    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    if sum(f.normal.z for f in bm.faces) < 0:      # open dome: make sure it faces up (+Z Blender = +Y Unity)
        bmesh.ops.reverse_faces(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = True
    me.update()
    ob = bpy.data.objects.new(NAME, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    zs = [v.co.z for v in me.vertices]
    lo, hi = TRI_BUDGET
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "in_budget": lo <= tris <= hi,
            "height_m": round(max(zs), 2), "faces_pointing_down": sum(1 for p in me.polygons if p.normal.z <= 0)}
