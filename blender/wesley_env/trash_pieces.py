"""SM_Env_TrashPieces (Wesley) - low-poly trash chunks that dress PF_Env_GunungSampah_3Tiers.

Wesley's reference pile is dominated by plastic bags, bottles, jerry cans, cardboard and
sacks, which JC's 11 branded props do not cover. These are decoration-only meshes (no
collider, never spawned as pickups), modelled at game-readable size (~0.6-1.4 m) and UV
mapped onto single swatches of T_Env_TrashPalette (4x4 colour grid) so every piece shares
one material (M_Env_TrashPieces) and batches well.
One FBX holds every variant as its own object: SM_Env_TrashPiece_<Variant>.
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

NAME = "SM_Env_TrashPieces"
MAT = ("M_Env_TrashPieces", (0.7, 0.7, 0.7, 1.0))
GRID = 4  # palette is 4 x 4 swatches

# swatch index -> colour (also used by textures.trash_palette)
PALETTE = [
    (0.85, 0.84, 0.81), (0.61, 0.60, 0.58), (0.15, 0.15, 0.16), (0.66, 0.20, 0.17),
    (0.24, 0.44, 0.66), (0.66, 0.78, 0.81), (0.24, 0.49, 0.33), (0.18, 0.34, 0.63),
    (0.18, 0.39, 0.66), (0.85, 0.64, 0.12), (0.61, 0.48, 0.31), (0.81, 0.78, 0.71),
    (0.78, 0.41, 0.17), (0.24, 0.55, 0.53), (0.29, 0.23, 0.18), (0.79, 0.76, 0.71),
]


def _swatch_uv(bm, idx_for_face):
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        idx = idx_for_face(f)
        cu, cv = (idx % GRID + 0.5) / GRID, (idx // GRID + 0.5) / GRID
        for li, loop in enumerate(f.loops):
            a = 2 * math.pi * li / len(f.loops)
            loop[uv].uv = (cu + 0.08 / GRID * math.cos(a), cv + 0.08 / GRID * math.sin(a))


def _jitter(bm, rng, amount):
    for v in bm.verts:
        v.co += Vector((rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1))) * amount


def _finish(name, bm):
    me = bpy.data.meshes.new(name)
    bm.normal_update()
    bm.to_mesh(me)
    bm.free()
    mat = bpy.data.materials.get(MAT[0]) or bpy.data.materials.new(MAT[0])
    mat.diffuse_color = MAT[1]
    me.materials.append(mat)
    old = bpy.data.objects.get(name)
    if old:
        bpy.data.objects.remove(old, do_unlink=True)
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def kresek(variant, swatch, seed):
    """Knotted plastic bag: lumpy icosphere with two pulled-up handle ears."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
    bmesh.ops.scale(bm, vec=(1.0, 0.8, 0.75), verts=bm.verts)
    _jitter(bm, rng, 0.07)
    top = sorted(bm.verts, key=lambda v: -v.co.z)[:2]
    for v in top:
        v.co.z += 0.28
        v.co.x *= 0.5
    _swatch_uv(bm, lambda f: swatch)
    return _finish(f"{NAME[:-1]}_{variant}", bm)


def botol(variant, swatch, seed):
    """PET bottle lying on its side: 8-sided body, shoulder, neck and blue cap."""
    rng = random.Random(seed)
    bm = bmesh.new()
    rings = [(0.0, 0.17), (0.62, 0.17), (0.78, 0.08), (0.88, 0.06), (0.88, 0.065), (0.96, 0.065)]
    seg, loops = 8, []
    for x, r in rings:
        loops.append([bm.verts.new((x - 0.48, r * math.cos(2 * math.pi * i / seg), r * math.sin(2 * math.pi * i / seg)))
                      for i in range(seg)])
    for a, b in zip(loops, loops[1:]):
        for i in range(seg):
            bm.faces.new((a[i], a[(i + 1) % seg], b[(i + 1) % seg], b[i]))
    bm.faces.new(list(reversed(loops[0])))
    bm.faces.new(loops[-1])
    _jitter(bm, rng, 0.015)
    cap_x = 0.88 - 0.48 - 0.001
    _swatch_uv(bm, lambda f: 7 if f.calc_center_median().x > cap_x else swatch)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    return _finish(f"{NAME[:-1]}_{variant}", bm)


def jerigen(variant, swatch, seed):
    """Jerry can: slightly crushed box with a handle bridge and a spout."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.scale(bm, vec=(0.55, 0.32, 0.75), verts=bm.verts)
    handle = bmesh.ops.create_cube(bm, size=1.0)["verts"]
    bmesh.ops.scale(bm, vec=(0.34, 0.1, 0.1), verts=handle)
    bmesh.ops.translate(bm, vec=(-0.05, 0.0, 0.44), verts=handle)
    spout = bmesh.ops.create_cone(bm, cap_ends=True, segments=6, radius1=0.07, radius2=0.06, depth=0.14)["verts"]
    bmesh.ops.translate(bm, vec=(0.18, 0.0, 0.43), verts=spout)
    _jitter(bm, rng, 0.02)
    _swatch_uv(bm, lambda f: swatch)
    return _finish(f"{NAME[:-1]}_{variant}", bm)


def kardus(variant, swatch, seed):
    """Soggy cardboard box, subdivided once and crumpled."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    bmesh.ops.subdivide_edges(bm, edges=bm.edges[:], cuts=1, use_grid_fill=True)
    bmesh.ops.scale(bm, vec=(0.8, 0.55, 0.45), verts=bm.verts)
    _jitter(bm, rng, 0.05)
    _swatch_uv(bm, lambda f: swatch)
    return _finish(f"{NAME[:-1]}_{variant}", bm)


def karung(variant, swatch, seed):
    """Woven rice sack, stretched and tied at one end."""
    rng = random.Random(seed)
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=2, radius=0.5)
    bmesh.ops.scale(bm, vec=(1.3, 0.75, 0.6), verts=bm.verts)
    _jitter(bm, rng, 0.05)
    for v in bm.verts:
        if v.co.x > 0.5:
            v.co.y *= 0.45
            v.co.z *= 0.45
    _swatch_uv(bm, lambda f: swatch)
    return _finish(f"{NAME[:-1]}_{variant}", bm)


VARIANTS = [
    (kresek, "KresekPutih", 0), (kresek, "KresekAbu", 1), (kresek, "KresekHitam", 2),
    (kresek, "KresekMerah", 3), (kresek, "KresekBiru", 4),
    (botol, "BotolBening", 5), (botol, "BotolHijau", 6),
    (jerigen, "JerigenBiru", 8), (jerigen, "JerigenKuning", 9),
    (kardus, "Kardus", 10), (karung, "KarungPutih", 11), (karung, "KarungOranye", 12),
]


def build():
    return [fn(name, swatch, 100 + i) for i, (fn, name, swatch) in enumerate(VARIANTS)]


def stats(obs):
    tris = {o.name.split("_")[-1]: sum(len(p.vertices) - 2 for p in o.data.polygons) for o in obs}
    return {"name": NAME, "pieces": len(obs), "tris_each": tris}
