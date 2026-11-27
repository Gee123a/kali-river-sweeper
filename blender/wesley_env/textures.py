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


GENERATORS = {
    "T_Env_BatuKali": batu_kali,
    "T_Env_BetonKotor": beton_kotor,
    "T_Env_CatKarat": cat_karat,
}


def save_png(name, rgb, out_dir):
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name + ".png")
    img = bpy.data.images.new(name, SIZE, SIZE, alpha=False)
    rgba = np.concatenate([np.clip(rgb, 0, 1), np.ones((SIZE, SIZE, 1))], -1)
    img.pixels.foreach_set(rgba[::-1].astype(np.float32).ravel())   # Blender rows start at the bottom
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    return path


def build_all(out_dir):
    return [save_png(name, fn(), out_dir) for name, fn in GENERATORS.items()]
