"""Small procedural-mesh toolkit for Wesley's environment meshes.

Geometry is authored in UNITY coordinates (X across, Y up, Z downstream) and converted
with terrain.unity_to_blender() when the mesh is created, so every number in the asset
modules can be compared 1:1 with RiverMath / node positions in the Unity scene.
UVs are planar in metres (u, v) / tile so tiling textures keep a constant world scale.
"""
import math

import bmesh
import bpy

from wesley_env.terrain import unity_to_blender


class MeshKit:
    def __init__(self, uv_tile=2.0):
        self.verts, self.faces, self.mats, self.uvs = [], [], [], []
        self.uv_tile = uv_tile

    # ---------------- primitives ----------------
    def _face(self, pts, mat, uv):
        base = len(self.verts)
        self.verts.extend(pts)
        self.faces.append(tuple(range(base, base + len(pts))))
        self.mats.append(mat)
        self.uvs.append([(a / self.uv_tile, b / self.uv_tile) for a, b in uv])

    def prism(self, poly_xz, y0, y1, mat, caps=True):
        """Extrude a convex XZ polygon (counter-clockwise seen from +Y) from y0 to y1."""
        n, dist = len(poly_xz), 0.0
        for i in range(n):
            (x0, z0), (x1, z1) = poly_xz[i], poly_xz[(i + 1) % n]
            seg = math.hypot(x1 - x0, z1 - z0)
            self._face([(x0, y0, z0), (x1, y0, z1), (x1, y1, z1), (x0, y1, z0)], mat,
                       [(dist, y0), (dist + seg, y0), (dist + seg, y1), (dist, y1)])
            dist += seg
        if caps:
            self._face([(x, y1, z) for x, z in poly_xz], mat, [(x, z) for x, z in poly_xz])
            self._face([(x, y0, z) for x, z in reversed(poly_xz)], mat, [(x, z) for x, z in reversed(poly_xz)])

    def box(self, x0, x1, y0, y1, z0, z1, mat):
        self.prism([(x0, z0), (x1, z0), (x1, z1), (x0, z1)], y0, y1, mat)

    def hexa(self, c, mat):
        """Closed 6-sided solid from 8 corners: c[0..3] bottom ring, c[4..7] top ring (same order)."""
        quads = [(0, 1, 2, 3), (7, 6, 5, 4), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
        for q in quads:
            pts = [c[i] for i in q]
            nx = abs((pts[1][1] - pts[0][1]) * (pts[2][2] - pts[0][2]) - (pts[1][2] - pts[0][2]) * (pts[2][1] - pts[0][1]))
            ny = abs((pts[1][2] - pts[0][2]) * (pts[2][0] - pts[0][0]) - (pts[1][0] - pts[0][0]) * (pts[2][2] - pts[0][2]))
            if ny >= nx:   # mostly horizontal face -> project on XZ, else on (X or Z, Y)
                uv = [(p[0], p[2]) for p in pts]
            else:
                uv = [(p[2] if abs(pts[1][0] - pts[0][0]) < 1e-6 else p[0], p[1]) for p in pts]
            self._face(pts, mat, uv)

    def beam(self, p0, p1, half, mat, up=(0.0, 1.0, 0.0)):
        """Square-section beam/rope from p0 to p1 (half = half thickness)."""
        d = [p1[i] - p0[i] for i in range(3)]
        ln = math.sqrt(sum(c * c for c in d)) or 1.0
        d = [c / ln for c in d]
        if abs(sum(d[i] * up[i] for i in range(3))) > 0.95:
            up = (1.0, 0.0, 0.0)
        s = [d[1] * up[2] - d[2] * up[1], d[2] * up[0] - d[0] * up[2], d[0] * up[1] - d[1] * up[0]]
        sl = math.sqrt(sum(c * c for c in s))
        s = [c / sl for c in s]
        u = [s[1] * d[2] - s[2] * d[1], s[2] * d[0] - s[0] * d[2], s[0] * d[1] - s[1] * d[0]]
        ring = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
        corner = lambda p, a, b: tuple(p[i] + (a * s[i] + b * u[i]) * half for i in range(3))
        self.hexa([corner(p0, a, b) for a, b in ring] + [corner(p1, a, b) for a, b in ring], mat)

    def box_yaw(self, cx, cz, half_x, half_z, yaw_deg, y0, y1, mat):
        """Box rotated around Y (yaw in degrees) centred at (cx, cz)."""
        a = math.radians(yaw_deg)
        ca, sa = math.cos(a), math.sin(a)
        corners = [(-half_x, -half_z), (half_x, -half_z), (half_x, half_z), (-half_x, half_z)]
        self.prism([(cx + x * ca - z * sa, cz + x * sa + z * ca) for x, z in corners], y0, y1, mat)

    def cylinder(self, cx, cz, r, y0, y1, mat, seg=8):
        self.prism([(cx + r * math.cos(2 * math.pi * i / seg), cz + r * math.sin(2 * math.pi * i / seg))
                    for i in range(seg)], y0, y1, mat)

    def stadium(self, cx, cz, half_w, half_len, y0, y1, mat, seg=8):
        """Pier footprint: straight sides along Z with semicircular ends (radius half_w)."""
        pts = []
        for i in range(seg + 1):  # downstream end (+Z)
            a = math.pi * i / seg
            pts.append((cx + half_w * math.cos(a), cz + half_len + half_w * math.sin(a)))
        for i in range(seg + 1):  # upstream end (-Z)
            a = math.pi + math.pi * i / seg
            pts.append((cx + half_w * math.cos(a), cz - half_len + half_w * math.sin(a)))
        self.prism(pts, y0, y1, mat)

    def torus_y(self, cx, cy, cz, big_r, small_r, mat, seg=12, ring=4):
        """Horizontal ring (hand wheel) around a vertical axis."""
        grid = []
        for i in range(seg):
            a = 2 * math.pi * i / seg
            row = []
            for j in range(ring):
                b = 2 * math.pi * j / ring
                rr = big_r + small_r * math.cos(b)
                row.append((cx + rr * math.cos(a), cy + small_r * math.sin(b), cz + rr * math.sin(a)))
            grid.append(row)
        for i in range(seg):
            for j in range(ring):
                p = [grid[i][j], grid[(i + 1) % seg][j], grid[(i + 1) % seg][(j + 1) % ring], grid[i][(j + 1) % ring]]
                self._face(p, mat, [(i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)])

    # ---------------- output ----------------
    def tris(self):
        return sum(len(f) - 2 for f in self.faces)

    def build(self, name, materials):
        """materials: list of (name, rgba). Returns the new Blender object at the origin."""
        old = bpy.data.objects.get(name)
        if old:
            bpy.data.objects.remove(old, do_unlink=True)
        me = bpy.data.meshes.new(name)
        me.from_pydata([unity_to_blender(*v) for v in self.verts], [], self.faces)
        for mname, col in materials:
            mat = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
            mat.diffuse_color = col
            me.materials.append(mat)
        uv = me.uv_layers.new(name="UVMap")
        for poly, m, fuv in zip(me.polygons, self.mats, self.uvs):
            poly.material_index = m
            for li, (u, v) in zip(poly.loop_indices, fuv):
                uv.data[li].uv = (u, v)
        # weld each primitive's coincident corners first so it becomes one closed solid;
        # only then can recalc_face_normals orient every face outward (loose faces get guessed)
        bm = bmesh.new()
        bm.from_mesh(me)
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        bm.to_mesh(me)
        bm.free()
        me.update()
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob
