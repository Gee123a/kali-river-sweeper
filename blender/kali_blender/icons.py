"""Tool role icons for the 4-slot hotbar (MECHANICS_SPEC C2, plan_jc 7B): T_Icon_Role_{Serok,Capit,Ganco,Garuk}.png,
256 x 256 RGBA, transparent background. Flat, high-contrast: a role-coloured disc with a dark rim, a white
pictogram and the role word, drawn with the labels.py rasteriser (no hand-painted files).

    from kali_blender import icons; icons.write_role_icons(out_dir)
"""
import math
import os

import bpy  # noqa: F401
import numpy as np

from kali_blender import labels

SIZE = 256
ROLES = {  # name: (disc colour, pictogram painter)
    "Serok": "#1d6fe1",   # blue: nets / scoops for Normal
    "Capit": "#eab308",   # yellow: grabbers / gloves for Medical
    "Ganco": "#a855f7",   # purple: hooks for Biohazard
    "Garuk": "#16a34a",   # green: rakes / pumps for the barrier pile
}
INK, RIM = "#ffffff", "#111827"


def _serok(c):
    """Scoop net: hoop with mesh lines and a handle."""
    hoop = c.ellipse(0, 18, 34, 30) & ~c.ellipse(0, 18, 27, 23)
    mesh = c.empty()
    for x in range(-24, 25, 8):
        mesh |= c.rect(x - 1.2, -6, x + 1.2, 40) & c.ellipse(0, 18, 28, 24)
    for y in range(0, 40, 8):
        mesh |= c.rect(-30, y - 1.2, 30, y + 1.2) & c.ellipse(0, 18, 28, 24)
    return hoop | mesh | c.stroke([(0, -12), (0, -46)], 9)


def _capit(c):
    """Grabber: two jaws closing on a dot, handle below."""
    jaws = c.stroke([(-6, -10), (-20, 18), (-8, 42)], 8) | c.stroke([(6, -10), (20, 18), (8, 42)], 8)
    return jaws | c.ellipse(0, 26, 7, 7) | c.stroke([(0, -10), (0, -46)], 9) | c.rect(-14, -16, 14, -8)


def _ganco(c):
    """Hook: shaft with a curled point."""
    shaft = c.stroke([(-14, -46), (-14, 26)], 9)
    hook = c.stroke([(-14, 26), (-8, 42), (8, 48), (24, 40), (28, 24)], 8)
    return shaft | hook | c.poly([(19, 26), (37, 26), (28, 6)])          # open crook ending in a barb


def _garuk(c):
    """Rake: fan of tines on a handle."""
    m = c.stroke([(0, -46), (0, 8)], 9) | c.rect(-34, 8, 34, 15)
    for k in range(7):
        x = -30 + k * 10
        m |= c.stroke([(x, 12), (x * 1.15, 44)], 5)
    return m


PICTO = {"Serok": _serok, "Capit": _capit, "Ganco": _ganco, "Garuk": _garuk}


def render_icon(role):
    c = labels.Canvas(SIZE, SIZE, "pack")
    c.panel("front", (160.0, 160.0))                        # design units, origin bottom-left
    c.rgb[...] = 0.0
    c.ox, c.oy = c.W / 2, c.H / 2                            # centre the design space
    disc = c.ellipse(0, 0, 72, 72)
    rim = c.grow(disc, 4) & ~disc
    c.paint(rim, RIM)
    c.paint(disc, ROLES[role])
    picto = PICTO[role](c) & disc
    c.paint(c.grow(picto, 2.5) & disc, RIM)
    c.paint(picto, INK)
    word = c.text(role.upper(), 0, -60, 12, "impact.ttf", max_w=80, spacing=1.1) & disc
    c.paint(word, INK)
    alpha = (disc | rim).astype(np.float32)
    rgb = c.result()
    a = alpha.reshape(SIZE, labels.SS, SIZE, labels.SS).mean(axis=(1, 3))
    out = np.zeros((SIZE, SIZE, 4), np.float32)
    out[..., :3] = np.where(a[..., None] > 0, rgb / np.maximum(a[..., None], 1e-6), 0.0).clip(0, 1)
    out[..., 3] = a
    return out


def write_role_icons(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    paths = []
    for role in ROLES:
        arr = render_icon(role)
        name = f"T_Icon_Role_{role}.png"
        img = bpy.data.images.new(name, SIZE, SIZE, alpha=True)
        img.pixels.foreach_set(arr.ravel())
        path = os.path.join(out_dir, name)
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        bpy.data.images.remove(img)
        paths.append(path)
    return paths
