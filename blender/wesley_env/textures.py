"""Procedural, seamlessly tiling textures for Wesley's environment (no downloads).

Style follows docs/DESIGN.md: weathered, humid kampung look (faded paint with rust
specks, stained concrete, wet river-stone masonry). Albedo maps are mostly light/neutral
so the URP material Base Color tint sets the final hue (one paint map -> blue & yellow).
"""
import os

import bpy
import numpy as np

SIZE = 512


def _value_noise(rng, size, cells):
    """Tileable smooth value noise in [0,1]."""
    g = rng.random((cells, cells))
    t = np.arange(size) * cells / size
    i0 = np.floor(t).astype(int)
    f = t - i0
    f = f * f * (3 - 2 * f)
    i1 = (i0 + 1) % cells
    a, b = g[np.ix_(i0, i0)], g[np.ix_(i0, i1)]
    c, d = g[np.ix_(i1, i0)], g[np.ix_(i1, i1)]
    fy, fx = f[:, None], f[None, :]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def _fbm(rng, size, base=4, octaves=5):
    out, amp, tot = np.zeros((size, size)), 1.0, 0.0
    for o in range(octaves):
        out += _value_noise(rng, size, base * 2 ** o) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def _voronoi(rng, size, n):
    """Tileable Voronoi: returns (cell id, F2-F1 edge distance in pixels)."""
    pts = rng.random((n, 2)) * size
    yy, xx = np.mgrid[0:size, 0:size].astype(np.float32)
    d1 = np.full((size, size), 1e9, np.float32)
    d2 = np.full((size, size), 1e9, np.float32)
    cid = np.zeros((size, size), np.int32)
    for k, (px, py) in enumerate(pts):
        dx = np.abs(xx - px)
        dy = np.abs(yy - py)
        dx = np.minimum(dx, size - dx)
        dy = np.minimum(dy, size - dy)
        d = np.sqrt(dx * dx + dy * dy)
        closer = d < d1
        d2 = np.where(closer, d1, np.minimum(d2, d))
        cid = np.where(closer, k, cid)
        d1 = np.where(closer, d, d1)
    return cid, d2 - d1


def batu_kali(seed=11):
    rng = np.random.default_rng(seed)
    cid, edge = _voronoi(rng, SIZE, 34)
    tone = rng.uniform(0.42, 0.68, 34)[cid]
    warm = rng.uniform(-0.04, 0.05, 34)[cid]
    grain = _fbm(rng, SIZE, 8, 4)
    stone = np.clip(tone + (grain - 0.5) * 0.18, 0, 1)
    t = np.clip((edge - 5.0) / 12.0, 0, 1)
    bevel = t * t * (3 - 2 * t)                          # rounded stone shoulder near the joint
    mortar = np.clip((edge - 3.0) / 2.5, 0, 1)           # 0 = thick dark mortar joint
    lum = stone * (0.62 + 0.38 * bevel)
    mortar_col = 0.24 + (grain - 0.5) * 0.08
    lum = lum * mortar + mortar_col * (1 - mortar)
    r, g, b = lum + warm, lum + warm * 0.6, lum - warm * 0.2
    return np.stack([r, g, b], -1)


def beton_kotor(seed=21):
    rng = np.random.default_rng(seed)
    base = 0.80 + (_fbm(rng, SIZE, 4, 6) - 0.5) * 0.18
    stains = np.clip((_fbm(rng, SIZE, 3, 4) - 0.55) * 3.0, 0, 1)   # damp moss/dirt patches
    pits = (rng.random((SIZE, SIZE)) > 0.996) * 0.25
    lum = np.clip(base - stains * 0.28 - pits, 0, 1)
    return np.stack([lum - stains * 0.02, lum + stains * 0.01, lum - stains * 0.06], -1)


def cat_karat(seed=31):
    """Faded paint (white, tinted by material colour) with rust specks + streaks."""
    rng = np.random.default_rng(seed)
    fade = 0.88 + (_fbm(rng, SIZE, 4, 5) - 0.5) * 0.14
    rust_mask = np.clip((_fbm(rng, SIZE, 6, 5) - 0.70) * 3.0, 0, 1) * 0.7
    specks = (rng.random((SIZE, SIZE)) > 0.996).astype(float) * 0.6
    rust_mask = np.clip(rust_mask + specks * 0.8, 0, 1)
    paint = np.stack([fade, fade, fade], -1)
    rust = np.array([0.62, 0.42, 0.30])                  # orange-brown oxidation (DESIGN 2.3)
    m = rust_mask[..., None]
    return np.clip(paint * (1 - m) + rust * m, 0, 1)


def _clutter(seed, n, palette, weights, shade=0.45, grime=0.25, cavity=1.0):
    """Packed debris: each Voronoi cell is one piece of junk in a palette colour."""
    rng = np.random.default_rng(seed)
    cid, edge = _voronoi(rng, SIZE, n)
    pick = rng.choice(len(palette), n, p=np.array(weights) / np.sum(weights))
    col = np.array(palette)[pick][cid]
    t = np.clip(edge / 5.0, 0, 1)
    rim = t * t * (3 - 2 * t)                            # crumpled edges fall into shadow
    dirt = _fbm(rng, SIZE, 6, 5)
    out = col * (1 - shade + shade * rim)[..., None]
    out *= (1 - grime * np.clip((dirt - 0.45) * 2.0, 0, 1))[..., None]
    lum = out.mean(-1, keepdims=True)
    out = out * 0.6 + lum * np.array([1.05, 0.95, 0.80]) * 0.4   # sun-faded, brown grime cast
    gloss = (rng.random(n)[cid] > 0.7) & (t > 0.6) & (_value_noise(rng, SIZE, 64) > 0.8)
    out = out * 0.92 + gloss[..., None] * 0.12
    lum2 = out.mean(-1, keepdims=True)
    return np.clip((out * 0.55 + lum2 * 0.45) * cavity, 0, 1)


def trash_lumpur(seed=41):
    """Bottom zone (< 0.8 m): black anaerobic silt #1C1917 with half-buried scraps."""
    rng = np.random.default_rng(seed)
    base = 0.09 + (_fbm(rng, SIZE, 5, 6) - 0.5) * 0.08
    mud = np.stack([base * 1.10, base, base * 0.88], -1)
    scraps = _clutter(seed + 1, 70, [(0.30, 0.27, 0.22), (0.22, 0.25, 0.28), (0.35, 0.30, 0.18)], [3, 2, 1], 0.5, 0.5)
    mask = np.clip((_fbm(rng, SIZE, 8, 4) - 0.58) * 6.0, 0, 1)[..., None]
    return mud * (1 - mask) + scraps * 0.55 * mask


def trash_kasur_medis(seed=51):
    """Middle zone (0.8-2.5 m): soggy kasur kapuk ticking + yellow B3 medical bags."""
    rng = np.random.default_rng(seed)
    pal = [(0.62, 0.55, 0.48), (0.55, 0.42, 0.40), (0.48, 0.50, 0.42),  # stained mattress fabric
           (0.80, 0.62, 0.10), (0.75, 0.58, 0.08),                     # hazard yellow #EAB308, faded
           (0.62, 0.16, 0.14), (0.28, 0.25, 0.22)]                     # red B3 stripe, dark rag
    out = _clutter(seed, 160, pal, [3, 2, 2, 2, 1, 1, 2], 0.25, 0.45, cavity=0.55)
    yy = np.arange(SIZE)[:, None] * np.ones((1, SIZE))
    stripes = ((yy // 10) % 2 == 0)[..., None] * 0.06                  # faded ticking stripes
    return np.clip(out - stripes, 0, 1)


def trash_plastik(seed=61):
    """Top zone (> 2.5 m): dry sun-faded PET bottles, kresek bags, sachets, styrofoam."""
    pal = [(0.80, 0.80, 0.76), (0.42, 0.58, 0.70), (0.38, 0.58, 0.40), (0.12, 0.12, 0.13),
           (0.70, 0.28, 0.24), (0.82, 0.74, 0.40), (0.55, 0.40, 0.62), (0.88, 0.86, 0.80)]
    return _clutter(seed, 280, pal, [6, 2, 1, 3, 1, 1, 0.5, 5], 0.25, 0.5, cavity=0.5)


def kayu_lapuk(seed=71):
    """Weathered teak/plank grain (light, tinted per material); grain runs along V."""
    rng = np.random.default_rng(seed)
    u = np.arange(SIZE)[None, :] / SIZE
    warp = (_fbm(rng, SIZE, 3, 4) - 0.5) * 0.08
    rings = np.sin((u + warp) * 2 * np.pi * 22) * 0.5 + 0.5
    fine = _fbm(rng, SIZE, 16, 3)
    lum = 0.78 + (rings - 0.5) * 0.14 + (fine - 0.5) * 0.12
    dry = np.clip((_fbm(rng, SIZE, 4, 5) - 0.55) * 3.0, 0, 1)          # sun-bleached / damp patches
    lum = lum * (1 - 0.18 * dry)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    for _ in range(3):                                                  # knots
        cx, cy, r = rng.integers(0, SIZE, 2).tolist() + [rng.integers(8, 16)]
        dx = np.minimum(np.abs(xx - cx), SIZE - np.abs(xx - cx))
        dy = np.minimum(np.abs(yy - cy), SIZE - np.abs(yy - cy))
        lum -= np.clip(1 - np.sqrt((dx * 1.6) ** 2 + dy ** 2) / r, 0, 1) * 0.35
    return np.clip(np.stack([lum, lum * 0.97, lum * 0.92], -1), 0, 1)


def tali(seed=81):
    """Twisted rope fibres (diagonal strands)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE] / SIZE
    strands = np.sin((xx + yy) * 2 * np.pi * 16) * 0.5 + 0.5
    fibres = _fbm(rng, SIZE, 32, 2)
    lum = 0.70 + (strands - 0.5) * 0.30 + (fibres - 0.5) * 0.15
    return np.clip(np.stack([lum, lum * 0.95, lum * 0.85], -1), 0, 1)


def trash_palette(seed=91):
    """4x4 colour swatches for SM_Env_TrashPieces (index layout matches trash_pieces.PALETTE)."""
    from wesley_env.trash_pieces import GRID, PALETTE
    rng = np.random.default_rng(seed)
    cell = SIZE // GRID
    out = np.zeros((SIZE, SIZE, 3))
    grain = 0.9 + (_fbm(rng, SIZE, 16, 3) - 0.5) * 0.2
    for idx, col in enumerate(PALETTE):
        cx, cy = idx % GRID, idx // GRID            # cy counts from the bottom (UV v)
        r0 = SIZE - (cy + 1) * cell
        out[r0:r0 + cell, cx * cell:(cx + 1) * cell] = col
    return np.clip(out * grain[..., None], 0, 1)


def seng_gelombang(seed=101):
    """Corrugated zinc sheet (light, tinted per material). Ribs vary along V so they run
    down the roof slope (MeshKit projects roof faces on XZ: u = across, v = along the ridge);
    16 ribs per tile = 12.5 cm pitch at the 2 m kit tile. Rust streaks drip along U."""
    rng = np.random.default_rng(seed)
    v = np.arange(SIZE)[:, None] / SIZE
    rib = np.sin(v * 2 * np.pi * 16)
    lum = 0.80 + rib * 0.13 + (np.abs(rib) > 0.96) * 0.04            # lit crest / shadowed valley
    lum = lum * (0.92 + (_fbm(rng, SIZE, 4, 4) - 0.5) * 0.12)
    streak = _value_noise(rng, SIZE, 32)                                # streaks: stretched along U
    streak = np.repeat(streak[:, ::8], 8, axis=1)
    rust_mask = np.clip((streak * _fbm(rng, SIZE, 3, 4) - 0.32) * 3.2, 0, 1) * 0.75
    lap = (np.arange(SIZE)[None, :] % (SIZE // 2) < 5) * 0.22           # sheet overlap seam every 1 m
    rust_mask = np.clip(rust_mask + lap * (0.4 + 0.6 * _fbm(rng, SIZE, 8, 3)), 0, 1)
    paint = np.repeat(lum[..., None], 3, -1)
    rust = np.array([0.56, 0.36, 0.24])
    m = rust_mask[..., None]
    return np.clip(paint * (1 - m) + rust * lum[..., None] * m, 0, 1)


def kawat_jaring(seed=111):
    """Welded wire mesh (RGBA, alpha-clipped): 16 cells per 2 m tile = 12.5 cm squares
    (open enough to read the sorted trash inside the Bank Sampah cage)."""
    rng = np.random.default_rng(seed)
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    cell = SIZE // 16
    wire = ((xx % cell) < 4) | ((yy % cell) < 4)
    lum = 0.62 + (_fbm(rng, SIZE, 8, 3) - 0.5) * 0.3
    rust = np.clip((_fbm(rng, SIZE, 5, 4) - 0.6) * 3.0, 0, 1)
    rgb = np.stack([lum, lum, lum * 1.02], -1) * (1 - rust[..., None] * 0.5) + \
        np.array([0.45, 0.28, 0.17]) * rust[..., None] * 0.5
    return np.concatenate([np.clip(rgb, 0, 1), wire[..., None].astype(float)], -1)


def ponton_hdpe(seed=121):
    """Floating HDPE dock cubes (marina pontoon, blue): 4 x 4 cubes of 0.5 m per 2 m tile,
    each with a soft bevelled top, a centre boss and corner lugs; algae grime in the seams."""
    rng = np.random.default_rng(seed)
    cell = SIZE // 4
    yy, xx = np.mgrid[0:SIZE, 0:SIZE]
    lx, ly = (xx % cell) - cell / 2, (yy % cell) - cell / 2
    edge = np.maximum(np.abs(lx), np.abs(ly)) / (cell / 2)          # 0 centre .. 1 seam
    lum = 0.78 + 0.22 * np.clip((0.97 - edge) / 0.25, 0, 1)         # bevel toward the seam
    lum = np.where(edge > 0.95, 0.35, lum)                          # dark seam
    boss = np.hypot(lx, ly) < cell * 0.14
    lum = np.where(boss, lum * 1.12, lum)
    for cx, cy in ((-1, -1), (-1, 1), (1, -1), (1, 1)):             # corner lugs
        lug = np.hypot(lx - cx * cell * 0.38, ly - cy * cell * 0.38) < cell * 0.055
        lum = np.where(lug, lum * 0.8, lum)
    lum = lum * (0.94 + (_fbm(rng, SIZE, 8, 3) - 0.5) * 0.12)
    blue = np.stack([0.16 * lum, 0.40 * lum, 0.78 * lum], -1)
    algae = np.clip((edge - 0.82) * 5, 0, 1) * np.clip(_fbm(rng, SIZE, 4, 4) * 1.4 - 0.35, 0, 1)
    m = algae[..., None] * 0.7
    return np.clip(blue * (1 - m) + np.array([0.20, 0.26, 0.14]) * m, 0, 1)


GENERATORS = {
    "T_Env_BatuKali": batu_kali,
    "T_Env_BetonKotor": beton_kotor,
    "T_Env_CatKarat": cat_karat,
    "T_Trash_Lumpur": trash_lumpur,
    "T_Trash_KasurMedis": trash_kasur_medis,
    "T_Trash_Plastik": trash_plastik,
    "T_Env_Kayu": kayu_lapuk,
    "T_Env_Tali": tali,
    "T_Env_TrashPalette": trash_palette,
    "T_Env_SengGelombang": seng_gelombang,
    "T_Env_KawatJaring": kawat_jaring,
    "T_Env_PontonHDPE": ponton_hdpe,
}


def save_png(name, rgb, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name + ".png")
    has_alpha = rgb.shape[-1] == 4
    img = bpy.data.images.new(name, SIZE, SIZE, alpha=has_alpha)
    rgba = np.clip(rgb, 0, 1) if has_alpha else np.concatenate([np.clip(rgb, 0, 1), np.ones((SIZE, SIZE, 1))], -1)
    img.pixels.foreach_set(rgba[::-1].astype(np.float32).ravel())   # Blender rows start at the bottom
    img.filepath_raw = path
    img.file_format = "PNG"
    if has_alpha:
        img.alpha_mode = "STRAIGHT"
    img.save()
    bpy.data.images.remove(img)
    return path


def build_all(out_dir):
    return [save_png(name, fn(), out_dir) for name, fn in GENERATORS.items()]
