"""Sign atlases for Wesley's stations (1024 x 1024, PIL): every building gets readable
signage so players know what each station is for.
T_Env_PapanBankSampah (SM_Env_BankSampah), T_Env_PapanKopdes (SM_Env_KoperasiDesa),
T_Env_PapanPosMedis (SM_Env_PosMedisB3), T_Env_PapanKarantina (SM_Env_KarantinaBiohazard),
T_Env_PapanUmum (name boards on SM_Env_PintuAirSiaga1 + SM_Env_JembatanUtama),
T_Env_PapanWarung (SM_Env_WarungMadura), T_Env_PapanPengepul (SM_Env_GudangPengepul).

Run with any Python that has Pillow (not Blender):
    python3 blender/wesley_env/papan.py

Typeface is the team HUD face (Barlow Condensed, docs/DESIGN.md) so the world signs and
the UI speak with one voice. Colours: Bank Sampah token #22C55E on a dark-teal #134E4A
frame, chalk ledger on slate. Everything is lightly weathered (fade, grime, rust drips)
to sit in the humid kampung like the other SM_Env meshes.

Atlas layout (pixels, top-left origin) - must match bank_sampah.UV_*:
    (0,0)-(1024,256)      rooftop sign  "BANK SAMPAH / BERKAH"
    (0,256)-(1024,512)    4 bay signs   BOTOL | PLASTIK / KERTAS | DAUN   (512 x 128 each)
    (0,512)-(768,896)     chalk ledger  "SALDO NASABAH"
    (768,512)-(1024,768)  scale dial    0-100 kg
    (768,768)-(1024,1024) solid frame colour (board edges / backs)
"""
import math
import os
import random

from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(os.path.dirname(HERE))
FONTS = os.path.join(ROOT, "unity", "Assets", "_Project", "UI", "Fonts")
TEX = os.path.join(ROOT, "unity", "Assets", "_Project", "Environment", "Textures")
OUT = os.path.join(TEX, "T_Env_PapanBankSampah.png")

W = 1024
GREEN = (34, 197, 94)          # DESIGN 2.4 Bank Sampah sign
GREEN_DEEP = (22, 132, 66)
FRAME = (19, 78, 74)           # #134E4A dark teal
CREAM = (246, 242, 230)
SLATE = (36, 46, 41)
CHALK = (226, 228, 214)


def font(name, size):
    return ImageFont.truetype(os.path.join(FONTS, name), size)


def text_center(d, box, txt, f, fill, shadow=None, dy=0):
    x0, y0, x1, y1 = box
    l, t, r, b = d.textbbox((0, 0), txt, font=f)
    x = (x0 + x1 - (r - l)) / 2 - l
    y = (y0 + y1 - (b - t)) / 2 - t + dy
    if shadow:
        d.text((x + 3, y + 4), txt, font=f, fill=shadow)
    d.text((x, y), txt, font=f, fill=fill)


def fit_font(d, txt, name, max_w, max_h, start=200):
    size = start
    while size > 10:
        f = font(name, size)
        l, t, r, b = d.textbbox((0, 0), txt, font=f)
        if r - l <= max_w and b - t <= max_h:
            return f
        size -= 2
    return font(name, 10)


def leaf(d, cx, cy, s, fill):
    """Simple leaf emblem (two arcs + vein), like the faint motif on real Bank Sampah signs."""
    pts = []
    for i in range(25):
        a = math.pi * i / 24
        pts.append((cx + math.cos(a) * s, cy - math.sin(a) * s * 0.42))
    for i in range(25):
        a = math.pi * i / 24
        pts.append((cx - math.cos(a) * s, cy + math.sin(a) * s * 0.42))
    d.polygon(pts, fill=fill)
    d.line([(cx - s * 1.05, cy + s * 0.05), (cx + s * 0.9, cy - s * 0.03)], fill=(255, 255, 255, 22), width=max(2, int(s * 0.04)))


def board(img, box, title, sub=None, emblem=True):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=FRAME)
    m = max(8, (y1 - y0) // 14)
    inner = (x0 + m, y0 + m, x1 - m, y1 - m)
    d.rectangle(inner, fill=GREEN)
    ix0, iy0, ix1, iy1 = inner
    if emblem:
        lay = Image.new("RGBA", img.size, (0, 0, 0, 0))
        leaf(ImageDraw.Draw(lay), (ix0 + ix1) / 2, (iy0 + iy1) / 2, min((ix1 - ix0) * 0.3, (iy1 - iy0) * 1.05), (255, 255, 255, 30))
        img.alpha_composite(lay)
        d = ImageDraw.Draw(img)
    pad = (iy1 - iy0) * 0.08
    if sub:
        split = iy0 + (iy1 - iy0) * 0.66
        f = fit_font(d, title, "BarlowCondensed-Bold.ttf", (ix1 - ix0) * 0.86, (split - iy0) - pad)
        text_center(d, (ix0, iy0 + pad * 0.5, ix1, split), title, f, CREAM, shadow=GREEN_DEEP)
        f2 = fit_font(d, sub, "BarlowCondensed-SemiBold.ttf", (ix1 - ix0) * 0.5, (iy1 - split) - pad * 1.2)
        text_center(d, (ix0, split, ix1, iy1 - pad * 0.4), sub, f2, FRAME)
    else:
        f = fit_font(d, title, "BarlowCondensed-Bold.ttf", (ix1 - ix0) * 0.8, (iy1 - iy0) - pad * 2.2)
        text_center(d, inner, title, f, CREAM, shadow=GREEN_DEEP)


def ledger(img, box):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(104, 74, 48))                       # timber frame
    d.rectangle((x0 + 18, y0 + 18, x1 - 18, y1 - 18), fill=SLATE)
    chalk = Image.new("L", img.size, 0)
    c = ImageDraw.Draw(chalk)
    head = font("BarlowCondensed-Bold.ttf", 58)
    body = font("IBMPlexMono-SemiBold.ttf", 25)
    small = font("BarlowCondensed-SemiBold.ttf", 28)
    text_center(c, (x0, y0 + 26, x1, y0 + 90), "SALDO NASABAH", head, 255)
    c.line([(x0 + 60, y0 + 98), (x1 - 60, y0 + 98)], fill=230, width=3)
    rows = [("Bu Sri", "12,5 kg", "Rp 37.500"), ("Pak Darto", " 8,0 kg", "Rp 16.000"),
            ("Mbak Ina", " 4,2 kg", "Rp 12.600"), ("Dek Yanto", " 2,5 kg", "Rp  5.000"),
            ("Pak RT", " 6,8 kg", "Rp 20.400")]
    for i, (n, kg, rp) in enumerate(rows):
        y = y0 + 118 + i * 40
        c.text((x0 + 56, y), n, font=body, fill=235)
        c.text((x0 + 300, y), kg, font=body, fill=235)
        c.text((x0 + 486, y), rp, font=body, fill=235)
    c.line([(x0 + 60, y1 - 72), (x1 - 60, y1 - 72)], fill=200, width=2)
    text_center(c, (x0, y1 - 66, x1, y1 - 26), "HARGA/kg  PET 3.000  •  KARDUS 1.500  •  KRESEK 500", small, 235)
    rng = random.Random(5)
    grain = Image.effect_noise(img.size, 70).point(lambda v: 255 if v > 110 else int(v * 1.6))
    chalk = ImageChops.multiply(chalk, grain).filter(ImageFilter.GaussianBlur(0.6))
    smear = Image.new("L", img.size, 0)
    s = ImageDraw.Draw(smear)
    for _ in range(9):                                         # old erased chalk ghosts
        sx, sy = rng.randint(x0 + 40, x1 - 200), rng.randint(y0 + 110, y1 - 90)
        s.ellipse((sx, sy, sx + rng.randint(80, 200), sy + rng.randint(14, 30)), fill=rng.randint(18, 34))
    smear = smear.filter(ImageFilter.GaussianBlur(9))
    chalk = ImageChops.lighter(chalk, smear)
    img.paste(Image.new("RGBA", img.size, CHALK + (255,)), (0, 0), chalk)


def dial(img, box):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    cx, cy, r = (x0 + x1) / 2, (y0 + y1) / 2, (x1 - x0) / 2 * 0.94
    d.rectangle(box, fill=FRAME)
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(150, 34, 32))       # painted rim
    r2 = r * 0.84
    d.ellipse((cx - r2, cy - r2, cx + r2, cy + r2), fill=CREAM)
    f = font("BarlowCondensed-Bold.ttf", 22)
    for i in range(51):                                         # 0..100 kg over 300 degrees
        a = math.radians(240 - i * 6)
        long = i % 5 == 0
        ra = r2 * (0.78 if long else 0.86)
        d.line([(cx + math.cos(a) * r2 * 0.94, cy - math.sin(a) * r2 * 0.94),
                (cx + math.cos(a) * ra, cy - math.sin(a) * ra)], fill=(30, 30, 30), width=3 if long else 2)
        if i % 10 == 0:
            rt = r2 * 0.62
            text_center(d, (cx + math.cos(a) * rt - 20, cy - math.sin(a) * rt - 14,
                            cx + math.cos(a) * rt + 20, cy - math.sin(a) * rt + 14), str(i * 2), f, (30, 30, 30))
    text_center(d, (cx - 30, cy + r2 * 0.28, cx + 30, cy + r2 * 0.58), "kg", f, (150, 34, 32))
    a = math.radians(240 - 19 * 6)                              # needle at ~38 kg
    d.line([(cx, cy), (cx + math.cos(a) * r2 * 0.8, cy - math.sin(a) * r2 * 0.8)], fill=(200, 30, 30), width=6)
    d.ellipse((cx - 12, cy - 12, cx + 12, cy + 12), fill=(40, 40, 40))


def weather(img, seed=7):
    """Sun fade + grime at the bottom of each board + a few rust drips."""
    rng = random.Random(seed)
    base = img.convert("RGB")
    noise = Image.effect_noise((W // 4, W // 4), 40).resize((W, W), Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    grime = Image.new("L", (W, W), 0)
    g = ImageDraw.Draw(grime)
    for (bx0, by0, bx1, by1) in [(0, 0, 1024, 256), (0, 256, 512, 384), (512, 256, 1024, 384),
                                 (0, 384, 512, 512), (512, 384, 1024, 512)]:
        h = by1 - by0
        for i in range(18):
            yy = by1 - h * 0.34 + i * h * 0.34 / 18
            g.rectangle((bx0, yy, bx1, yy + h * 0.02), fill=int(4 + i * 3.2))
        for _ in range(4):
            dx = rng.randint(bx0 + 20, bx1 - 20)
            dy = rng.randint(by0 + int(h * 0.1), by0 + int(h * 0.3))
            g.rectangle((dx, dy, dx + rng.randint(3, 6), by1), fill=rng.randint(30, 60))
    grime = ImageChops.multiply(grime.filter(ImageFilter.GaussianBlur(2)), ImageChops.invert(noise).point(lambda v: min(255, v + 90)))
    dirt = Image.new("RGB", (W, W), (72, 52, 34))
    base = Image.composite(dirt, base, grime)
    fade = Image.new("RGB", (W, W), (236, 230, 214))
    base = Image.composite(fade, base, noise.point(lambda v: int(max(0, v - 120) * 0.35)))
    return base


RED = (196, 32, 38)
WALL_GREY = (128, 131, 134)
INK = (34, 34, 36)


def kopdes_emblem(d, cx, top, s):
    """Original co-op emblem: red house outline with a window grid and a red-white flag."""
    w, h = s, s * 0.82
    x0, x1, yb = cx - w / 2, cx + w / 2, top + h
    ridge = (cx, top + h * 0.12)
    lw = max(4, int(s * 0.07))
    d.line([(x0 - lw, top + h * 0.5), ridge, (x1 + lw, top + h * 0.5)], fill=RED, width=lw, joint="curve")
    d.line([(x0 + lw * 0.6, top + h * 0.45), (x0 + lw * 0.6, yb)], fill=RED, width=lw)
    d.line([(x0, yb), (x1, yb)], fill=RED, width=lw)
    g = s * 0.11
    for i in range(2):
        for j in range(2):
            gx, gy = x0 + w * 0.18 + i * (g + 6), top + h * 0.56 + j * (g + 6)
            d.rectangle((gx, gy, gx + g, gy + g), fill=RED)
    pole = (cx - w * 0.18, top - s * 0.05)
    d.line([pole, (pole[0], top + h * 0.2)], fill=INK, width=3)
    d.rectangle((pole[0], pole[1], pole[0] + s * 0.22, pole[1] + s * 0.07), fill=RED)
    d.rectangle((pole[0], pole[1] + s * 0.07, pole[0] + s * 0.22, pole[1] + s * 0.14), fill=(245, 245, 245))
    return x0 + w * 0.42, yb


def kopdes():
    img = Image.new("RGB", (W, W), WALL_GREY)
    noise = Image.effect_noise((W // 4, W // 4), 30).resize((W, W), Image.BICUBIC).filter(ImageFilter.GaussianBlur(4))
    img = Image.composite(Image.new("RGB", (W, W), (108, 110, 112)), img, noise.point(lambda v: int(max(0, v - 110) * 0.8)))
    d = ImageDraw.Draw(img)
    # ---- sign wall art (0,0)-(512,640): emblem + KOPDES, KOPERASI / MERAH PUTIH / DESA ----
    bx0, by0, bx1 = 0, 0, 512
    cx, top, size = 236, 150, 200
    kopdes_emblem(d, cx, top, size)
    fk = font("BarlowCondensed-Bold.ttf", 46)
    for i, word in enumerate(("KOP", "DES")):
        d.text((cx - 2, top + 64 + i * 44), word, font=fk, fill=RED)
    text_center(d, (bx0, 330, bx1, 372), "KOPERASI", font("BarlowCondensed-Bold.ttf", 44), INK)
    fm = font("BarlowCondensed-Bold.ttf", 76)
    l1 = d.textbbox((0, 0), "MERAH ", font=fm)
    l2 = d.textbbox((0, 0), "PUTIH", font=fm)
    wtot = (l1[2] - l1[0]) + (l2[2] - l2[0])
    x = (bx1 - wtot) / 2
    d.text((x, 368), "MERAH ", font=fm, fill=RED)
    d.text((x + (l1[2] - l1[0]), 368), "PUTIH", font=fm, fill=(250, 250, 248), stroke_width=2, stroke_fill=(96, 98, 100))
    text_center(d, (bx0, 466, bx1, 508), "DESA KALI BERSIH", font("BarlowCondensed-SemiBold.ttf", 40), INK)
    # ---- veranda banner (0,656)-(1024,728) ----
    d.rectangle((0, 656, 1024, 728), fill=(250, 248, 240))
    d.rectangle((0, 656, 1024, 668), fill=RED)
    d.rectangle((0, 716, 1024, 728), fill=RED)
    text_center(d, (0, 668, 1024, 716), "PERAHU  \u2022  TONG KAMPUNG  \u2022  TRASH BOOM  \u2022  ALAT", font("BarlowCondensed-Bold.ttf", 44), RED)
    # rain streaks + grime at the bottom of the wall art
    rng = random.Random(11)
    grime = Image.new("L", (W, W), 0)
    g = ImageDraw.Draw(grime)
    for i in range(30):
        g.rectangle((0, 560 + i * 2.6, 512, 563 + i * 2.6), fill=int(3 + i * 2.2))
    for _ in range(14):
        dx = rng.randint(10, 500)
        g.rectangle((dx, rng.randint(0, 60), dx + rng.randint(2, 5), rng.randint(200, 640)), fill=rng.randint(14, 34))
    grime = grime.filter(ImageFilter.GaussianBlur(2))
    img = Image.composite(Image.new("RGB", (W, W), (70, 62, 52)), img, grime)
    out = os.path.join(TEX, "T_Env_PapanKopdes.png")
    img.save(out, optimize=True)
    return out


def bank_sampah():
    img = Image.new("RGBA", (W, W), FRAME + (255,))
    board(img, (0, 0, 1024, 256), "BANK SAMPAH", "BERKAH")
    for (x, y), word in zip([(0, 256), (512, 256), (0, 384), (512, 384)], ["BOTOL", "PLASTIK", "KERTAS", "DAUN"]):
        board(img, (x, y, x + 512, y + 128), word)
    ledger(img, (0, 512, 768, 896))
    dial(img, (768, 512, 1024, 768))
    out = weather(img)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT, optimize=True)
    return OUT


# ---------------------------------------------------------------- hazard stations
HAZ_YELLOW = (234, 179, 8)     # DESIGN 2.4 #EAB308 (Pos Medis sign) / hazard yellow
CROSS_RED = (220, 38, 38)      # #DC2626 red cross
BIO_PURPLE = (168, 85, 247)    # #A855F7 Karantina accent
BIO_LIME = (132, 204, 22)      # #84CC16 Karantina accent
BLACK = (24, 24, 24)


def _mask_symbol(size, draw_fn):
    """Draw a symbol on a 4x supersampled L mask and return it at `size`."""
    ss = size * 4
    m = Image.new("L", (ss, ss), 0)
    draw_fn(ImageDraw.Draw(m), ss)
    return m.resize((size, size), Image.LANCZOS)


def biohazard_mask(size):
    """Standard biohazard trefoil built from circles (units: symbol radius = 1)."""
    def draw(d, ss):
        c, u = ss / 2, ss / 2 / 1.02

        def circ(cx, cy, r, fill):
            d.ellipse((c + (cx - r) * u, c + (cy - r) * u, c + (cx + r) * u, c + (cy + r) * u), fill=fill)
        dirs = [math.radians(a) for a in (-90, 30, 150)]          # top, lower-right, lower-left
        for a in dirs:                                            # three outer discs
            circ(math.cos(a) * 0.42, math.sin(a) * 0.42, 0.58, 255)
        for a in dirs:                                            # hollow cuts through the rim -> open horns
            circ(math.cos(a) * 0.68, math.sin(a) * 0.68, 0.44, 0)
        ring_o, ring_i = 0.70, 0.60                               # ring crossing every hollow
        d.ellipse((c - ring_o * u, c - ring_o * u, c + ring_o * u, c + ring_o * u), outline=255, width=int((ring_o - ring_i) * u))
        circ(0, 0, 0.12, 0)                                       # centre hole
        for a in dirs:                                            # thin gaps from the hole to each hollow
            x0, y0 = c + math.cos(a) * 0.05 * u, c + math.sin(a) * 0.05 * u
            x1, y1 = c + math.cos(a) * 0.3 * u, c + math.sin(a) * 0.3 * u
            d.line([(x0, y0), (x1, y1)], fill=0, width=int(0.06 * u))
    return _mask_symbol(size, draw)


def radiation_mask(size):
    def draw(d, ss):
        c, r = ss / 2, ss / 2
        d.ellipse((c - r * 0.18, c - r * 0.18, c + r * 0.18, c + r * 0.18), fill=255)
        for a0 in (-120, 0, 120):
            d.pieslice((c - r * 0.95, c - r * 0.95, c + r * 0.95, c + r * 0.95), a0 - 30 - 90 + 60, a0 + 30 - 90 + 60, fill=255)
        d.ellipse((c - r * 0.3, c - r * 0.3, c + r * 0.3, c + r * 0.3), fill=0)
        d.ellipse((c - r * 0.18, c - r * 0.18, c + r * 0.18, c + r * 0.18), fill=255)
    return _mask_symbol(size, draw)


def stamp(img, mask, xy, colour):
    img.paste(Image.new("RGB", mask.size, colour), (int(xy[0]), int(xy[1])), mask)


def red_cross(d, box, bg=(250, 250, 246)):
    x0, y0, x1, y1 = box
    d.rounded_rectangle(box, radius=(x1 - x0) * 0.12, fill=bg)
    w, h = x1 - x0, y1 - y0
    t = w * 0.24
    d.rectangle((x0 + w / 2 - t / 2, y0 + h * 0.16, x0 + w / 2 + t / 2, y1 - h * 0.16), fill=CROSS_RED)
    d.rectangle((x0 + w * 0.16, y0 + h / 2 - t / 2, x1 - w * 0.16, y0 + h / 2 + t / 2), fill=CROSS_RED)


def hazard_stripes(img, box, band=48):
    x0, y0, x1, y1 = box
    w, h = x1 - x0, y1 - y0
    tile = Image.new("RGB", (w, h), HAZ_YELLOW)
    td = ImageDraw.Draw(tile)
    for k in range(-(h // band) - 2, w // band + 2, 2):
        sx = k * band
        td.polygon([(sx, h), (sx + band, h), (sx + band + h, 0), (sx + h, 0)], fill=BLACK)
    img.paste(tile, (x0, y0))


def grime(img, boxes, seed):
    """Dirt gradient at the bottom of each board + drips, then a light sun fade."""
    rng = random.Random(seed)
    g = Image.new("L", img.size, 0)
    gd = ImageDraw.Draw(g)
    for (bx0, by0, bx1, by1) in boxes:
        h = by1 - by0
        for i in range(16):
            yy = by1 - h * 0.3 + i * h * 0.3 / 16
            gd.rectangle((bx0, yy, bx1, yy + h * 0.02), fill=int(3 + i * 3))
        for _ in range(3):
            dx = rng.randint(bx0 + 10, bx1 - 10)
            gd.rectangle((dx, by0 + rng.randint(0, h // 3), dx + rng.randint(2, 5), by1), fill=rng.randint(20, 45))
    g = g.filter(ImageFilter.GaussianBlur(2))
    img = Image.composite(Image.new("RGB", img.size, (70, 54, 38)), img, g)
    n = Image.effect_noise((W // 4, W // 4), 40).resize(img.size, Image.BICUBIC).filter(ImageFilter.GaussianBlur(3))
    return Image.composite(Image.new("RGB", img.size, (238, 232, 216)), img, n.point(lambda v: int(max(0, v - 125) * 0.3)))


def pos_medis():
    """T_Env_PapanPosMedis - must match pos_medis_b3.UV_*."""
    img = Image.new("RGB", (W, W), (46, 48, 52))
    d = ImageDraw.Draw(img)
    # main board (0,0)-(1024,224): yellow, red cross, POS MEDIS B3
    d.rectangle((0, 0, 1024, 224), fill=BLACK)
    d.rectangle((10, 10, 1014, 214), fill=HAZ_YELLOW)
    red_cross(d, (30, 30, 194, 194))
    text_center(d, (214, 22, 1004, 160), "POS MEDIS B3", fit_font(d, "POS MEDIS B3", "BarlowCondensed-Bold.ttf", 760, 132), BLACK)
    text_center(d, (214, 154, 1004, 206), "LIMBAH MEDIS  •  INFEKSIUS  •  JARUM SUNTIK", font("BarlowCondensed-SemiBold.ttf", 40), BLACK)
    # instruction board (0,240)-(512,752)
    bx0, by0 = 0, 240
    d.rectangle((bx0, by0, bx0 + 512, by0 + 512), fill=(248, 246, 238))
    d.rectangle((bx0, by0, bx0 + 512, by0 + 96), fill=HAZ_YELLOW)
    d.rectangle((bx0, by0 + 92, bx0 + 512, by0 + 100), fill=BLACK)
    text_center(d, (bx0, by0 + 8, bx0 + 512, by0 + 90), "SETOR LIMBAH MEDIS", font("BarlowCondensed-Bold.ttf", 64), BLACK)
    # icons: yellow medical bag + sharps box
    d.polygon([(70, by0 + 150), (170, by0 + 150), (186, by0 + 270), (54, by0 + 270)], fill=HAZ_YELLOW, outline=BLACK, width=4)
    d.line([(96, by0 + 150), (120, by0 + 128), (144, by0 + 150)], fill=BLACK, width=5)
    red_cross(d, (96, by0 + 182, 144, by0 + 230), bg=HAZ_YELLOW)
    d.rectangle((300, by0 + 160, 440, by0 + 270), fill=(240, 240, 236), outline=BLACK, width=4)
    d.rectangle((300, by0 + 140, 440, by0 + 166), fill=CROSS_RED, outline=BLACK, width=4)
    text_center(d, (300, by0 + 190, 440, by0 + 250), "JARUM", font("BarlowCondensed-Bold.ttf", 40), CROSS_RED)
    text_center(d, (20, by0 + 280, 230, by0 + 320), "KANTONG KUNING", font("BarlowCondensed-Bold.ttf", 34), BLACK)
    text_center(d, (280, by0 + 280, 470, by0 + 320), "KOTAK JARUM", font("BarlowCondensed-Bold.ttf", 34), BLACK)
    d.rectangle((bx0 + 24, by0 + 344, bx0 + 488, by0 + 420), fill=CROSS_RED)
    t = "WAJIB PAKAI CAPIT ULAR!"
    text_center(d, (bx0 + 24, by0 + 344, bx0 + 488, by0 + 420), t, fit_font(d, t, "BarlowCondensed-Bold.ttf", 420, 56, 60), (255, 255, 255))
    t = "Bukan sampah biasa • Denda bila salah setor"
    text_center(d, (bx0, by0 + 430, bx0 + 512, by0 + 500), t, fit_font(d, t, "BarlowCondensed-SemiBold.ttf", 440, 40, 40), INK)
    d.rectangle((bx0, by0, bx0 + 511, by0 + 511), outline=BLACK, width=8)
    # red-cross decal (528,240)-(784,496): bins + gable
    d.rectangle((528, 240, 784, 496), fill=HAZ_YELLOW)
    red_cross(d, (556, 268, 756, 468))
    # plain yellow (800,240)-(1008,448), edge dark (800,800)-(1000,1000)
    d.rectangle((800, 240, 1008, 448), fill=HAZ_YELLOW)
    out = grime(img, [(0, 0, 1024, 224), (0, 240, 512, 752), (528, 240, 784, 496)], 3)
    path = os.path.join(TEX, "T_Env_PapanPosMedis.png")
    out.save(path, optimize=True)
    return path


def karantina():
    """T_Env_PapanKarantina - must match karantina_biohazard.UV_*."""
    img = Image.new("RGB", (W, W), (90, 92, 94))
    d = ImageDraw.Draw(img)
    # main board (0,0)-(1024,180): yellow + trefoil + KARANTINA BIOHAZARD
    d.rectangle((0, 0, 1024, 180), fill=BLACK)
    d.rectangle((8, 8, 1016, 172), fill=HAZ_YELLOW)
    stamp(img, biohazard_mask(150), (22, 15), BLACK)
    d = ImageDraw.Draw(img)
    text_center(d, (190, 10, 1006, 128), "KARANTINA BIOHAZARD", fit_font(d, "KARANTINA BIOHAZARD", "BarlowCondensed-Bold.ttf", 800, 112), BLACK)
    text_center(d, (190, 124, 1006, 172), "SETOR DRUM BIOHAZARD & RADIOAKTIF DI SINI", font("BarlowCondensed-SemiBold.ttf", 38), BLACK)
    # fence warning sign (0,224)-(512,736)
    x0, y0 = 0, 224
    d.rectangle((x0, y0, x0 + 512, y0 + 512), fill=BLACK)
    d.rectangle((x0 + 14, y0 + 14, x0 + 498, y0 + 498), fill=HAZ_YELLOW)
    d.rectangle((x0 + 14, y0 + 14, x0 + 498, y0 + 112), fill=BLACK)
    text_center(d, (x0, y0 + 18, x0 + 512, y0 + 108), "PERINGATAN", font("BarlowCondensed-Bold.ttf", 84), HAZ_YELLOW)
    stamp(img, biohazard_mask(230), (x0 + 141, y0 + 128), BLACK)
    d = ImageDraw.Draw(img)
    d.rectangle((x0 + 14, y0 + 372, x0 + 498, y0 + 498), fill=BLACK)
    text_center(d, (x0, y0 + 374, x0 + 512, y0 + 440), "AREA KARANTINA", font("BarlowCondensed-Bold.ttf", 66), HAZ_YELLOW)
    text_center(d, (x0, y0 + 436, x0 + 512, y0 + 494), "DILARANG MASUK TANPA APD", font("BarlowCondensed-SemiBold.ttf", 40), HAZ_YELLOW)
    # radiation sign (528,224)-(784,480)
    d.rectangle((528, 224, 784, 480), fill=BLACK)
    d.rectangle((536, 232, 776, 472), fill=HAZ_YELLOW)
    stamp(img, radiation_mask(160), (576, 246), BLACK)
    d = ImageDraw.Draw(img)
    text_center(d, (528, 410, 784, 468), "RADIOAKTIF", font("BarlowCondensed-Bold.ttf", 50), BLACK)
    # hazard stripes (528,496)-(1024,752)
    hazard_stripes(img, (528, 496, 1024, 752), band=40)
    d = ImageDraw.Draw(img)
    # accents (800,800)-(900,900) purple, (900,800)-(1000,900) lime, (800,900)-(1000,1000) dark steel
    d.rectangle((800, 800, 900, 900), fill=BIO_PURPLE)
    d.rectangle((900, 800, 1000, 900), fill=BIO_LIME)
    d.rectangle((800, 900, 1000, 1000), fill=(52, 54, 58))
    out = grime(img, [(0, 0, 1024, 180), (0, 224, 512, 736), (528, 224, 784, 480)], 4)
    path = os.path.join(TEX, "T_Env_PapanKarantina.png")
    out.save(path, optimize=True)
    return path


def umum():
    """T_Env_PapanUmum - name boards on Pintu Air, Jembatan Utama and both Dermaga."""
    img = Image.new("RGB", (W, W), (40, 42, 46))
    d = ImageDraw.Draw(img)
    # PINTU AIR (0,0)-(1024,160): blue steel board like the gate, white + yellow text
    d.rectangle((0, 0, 1024, 160), fill=(14, 46, 104))
    d.rectangle((8, 8, 1016, 152), fill=(30, 84, 170))
    text_center(d, (8, 6, 1016, 112), "PINTU AIR", font("BarlowCondensed-Bold.ttf", 104), (250, 250, 246), shadow=(14, 46, 104))
    text_center(d, (8, 106, 1016, 152), "JANGAN BIARKAN SAMPAH MENYUMBAT  •  BANJIR!", font("BarlowCondensed-SemiBold.ttf", 38), HAZ_YELLOW)
    # JEMBATAN UTAMA (0,176)-(1024,336): carved wooden board
    d.rectangle((0, 176, 1024, 336), fill=(74, 50, 30))
    for i in range(4):
        d.rectangle((10, 186 + i * 36, 1014, 186 + i * 36 + 32), fill=(126 - i * 4, 88 - i * 3, 56))
    text_center(d, (10, 180, 1014, 336), "JEMBATAN UTAMA", font("BarlowCondensed-Bold.ttf", 112), (244, 230, 196), shadow=(58, 38, 22))
    # DERMAGA (0,352)-(1024,512): clean-river teal board + boarding hint (Ivan: [E] at a Dermaga)
    d.rectangle((0, 352, 1024, 512), fill=(16, 62, 70))
    d.rectangle((8, 360, 1016, 504), fill=(27, 107, 99))                 # DESIGN clean teal #1B6B63
    text_center(d, (8, 356, 1016, 460), "DERMAGA", font("BarlowCondensed-Bold.ttf", 104), (250, 250, 246), shadow=(16, 62, 70))
    text_center(d, (8, 452, 1016, 502), "NAIK & TURUN PERAHU DI SINI  \u2022  TEKAN [E]", font("BarlowCondensed-SemiBold.ttf", 40), HAZ_YELLOW)
    out = grime(img, [(0, 0, 1024, 160), (0, 176, 1024, 336), (0, 352, 1024, 512)], 5)
    path = os.path.join(TEX, "T_Env_PapanUmum.png")
    out.save(path, optimize=True)
    return path


# ---------------------------------------------------------------- warung madura + gudang pengepul
PACK = [(214, 40, 40), (247, 189, 30), (30, 110, 200), (40, 160, 80), (240, 120, 30), (250, 250, 245),
        (160, 40, 160), (20, 150, 190), (230, 70, 120), (120, 70, 40)]


def goods_shelf(img, box, seed, rows=5):
    """Shelves packed with colourful sembako: boxes, bottles, snack packs, jars."""
    rng = random.Random(seed)
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=(70, 46, 28))
    rh = (y1 - y0) / rows
    for r in range(rows):
        top, base = y0 + r * rh + 6, y0 + (r + 1) * rh - 10
        x = x0 + 6
        while x < x1 - 12:
            kind = rng.random()
            c = rng.choice(PACK)
            if kind < 0.35:                                   # carton box with label band
                w, h = rng.randint(22, 40), rng.uniform(0.55, 0.95) * (base - top)
                d.rectangle((x, base - h, x + w, base), fill=c)
                d.rectangle((x, base - h * 0.62, x + w, base - h * 0.42), fill=rng.choice(PACK))
            elif kind < 0.65:                                 # bottle
                w, h = rng.randint(10, 16), rng.uniform(0.6, 0.92) * (base - top)
                d.rectangle((x, base - h * 0.78, x + w, base), fill=c)
                d.rectangle((x + w * 0.3, base - h, x + w * 0.7, base - h * 0.78), fill=c)
                d.rectangle((x + w * 0.25, base - h, x + w * 0.75, base - h * 0.94), fill=(240, 240, 240))
            elif kind < 0.88:                                 # pillow snack pack
                w, h = rng.randint(24, 38), rng.uniform(0.5, 0.8) * (base - top)
                d.rounded_rectangle((x, base - h, x + w, base), radius=6, fill=c)
                d.ellipse((x + w * 0.25, base - h * 0.7, x + w * 0.75, base - h * 0.3), fill=rng.choice(PACK))
            else:                                             # glass jar of crackers
                w, h = rng.randint(26, 34), rng.uniform(0.55, 0.75) * (base - top)
                d.rectangle((x, base - h, x + w, base), fill=(200, 216, 214))
                d.rectangle((x + 3, base - h * 0.85, x + w - 3, base - 3), fill=(222, 170, 90))
                d.rectangle((x - 1, base - h - 6, x + w + 1, base - h), fill=(200, 40, 40))
            x += w + rng.randint(1, 4)
        d.rectangle((x0, base, x1, base + 10), fill=(150, 104, 62))       # shelf board
        d.rectangle((x0, base + 10, x1, base + 13), fill=(60, 40, 24))


def warung():
    """T_Env_PapanWarung - must match warung_madura.UV_*."""
    img = Image.new("RGB", (W, W), (60, 42, 28))
    d = ImageDraw.Draw(img)
    # main sign (0,0)-(1024,196): green frame, cream board, SEMBAKO / WARUNG MADURA
    d.rectangle((0, 0, 1024, 196), fill=(24, 120, 60))
    d.rectangle((12, 12, 1012, 184), fill=(250, 240, 205))
    for i, cx in enumerate((60, 964)):                                    # leaf corners like the reference
        leaf(d, cx, 98, 36, (44, 150, 70))
    text_center(d, (100, 14, 924, 58), "SEMBAKO  •  BUKA 24 JAM", font("BarlowCondensed-Bold.ttf", 40), (24, 120, 60))
    text_center(d, (100, 52, 924, 182), "WARUNG MADURA", fit_font(d, "WARUNG MADURA", "BarlowCondensed-Bold.ttf", 800, 122), (206, 30, 36),
                shadow=(120, 20, 20))
    # banner (0,212)-(1024,306)
    d.rectangle((0, 212, 1024, 306), fill=(247, 196, 30))
    d.rectangle((0, 212, 1024, 220), fill=(206, 30, 36))
    d.rectangle((0, 298, 1024, 306), fill=(206, 30, 36))
    t = "SEDIA PULSA • KUOTA • TOKEN LISTRIK • GAS • GALON • ES BATU"
    text_center(d, (8, 220, 1016, 298), t, fit_font(d, t, "BarlowCondensed-Bold.ttf", 990, 64, 70), (180, 20, 26))
    # goods shelf (0,320)-(512,832) and etalase (528,320)-(1024,576)
    goods_shelf(img, (0, 320, 512, 832), 21, rows=5)
    goods_shelf(img, (528, 320, 1024, 576), 22, rows=2)
    glass = Image.new("L", (496, 256), 0)
    gd = ImageDraw.Draw(glass)
    for k in range(4):                                                    # glass reflections
        gx = 40 + k * 130
        gd.polygon([(gx, 256), (gx + 40, 256), (gx + 140, 0), (gx + 100, 0)], fill=60)
    img.paste(Image.new("RGB", (496, 256), (235, 245, 250)), (528, 320), glass)
    d = ImageDraw.Draw(img)
    d.rectangle((528, 320, 1024, 576), outline=(150, 104, 62), width=10)
    # A-frame BUKA 24 JAM (528,592)-(784,976)
    d.rectangle((528, 592, 784, 976), fill=(206, 30, 36))
    d.rectangle((544, 608, 768, 960), fill=(250, 248, 240))
    text_center(d, (544, 620, 768, 720), "BUKA", font("BarlowCondensed-Bold.ttf", 92), (206, 30, 36))
    text_center(d, (544, 712, 768, 870), "24", font("BarlowCondensed-Bold.ttf", 170), (206, 30, 36))
    text_center(d, (544, 870, 768, 950), "JAM", font("BarlowCondensed-Bold.ttf", 80), (206, 30, 36))
    # awning stripes (800,592)-(1024,816): 8 red / white bands
    for i in range(8):
        d.rectangle((800 + i * 28, 592, 828 + i * 28, 816), fill=(214, 40, 40) if i % 2 == 0 else (250, 246, 236))
    # rencengan sachet strips (0,848)-(512,1024): 8 vertical strips of sachets
    rng = random.Random(9)
    for c in range(8):
        sx = c * 64
        d.rectangle((sx, 848, sx + 64, 1024), fill=(60, 42, 28))
        col = rng.choice(PACK)
        for r in range(5):
            sy = 852 + r * 34
            d.rectangle((sx + 8, sy, sx + 56, sy + 30), fill=col)
            d.rectangle((sx + 8, sy + 10, sx + 56, sy + 18), fill=rng.choice(PACK))
    # flat colours: LPG lime (800,832)-(900,932), dark wood (900,832)-(1000,932)
    d.rectangle((800, 832, 900, 932), fill=(146, 196, 60))
    d.rectangle((900, 832, 1000, 932), fill=(70, 46, 28))
    out = grime(img, [(0, 0, 1024, 196), (0, 212, 1024, 306), (528, 592, 784, 976)], 6)
    path = os.path.join(TEX, "T_Env_PapanWarung.png")
    out.save(path, optimize=True)
    return path


def bale_stack(img, box, seed, kind):
    """Stacked recyclables for the Gudang Pengepul racks: plastic bales, cardboard, sacks."""
    rng = random.Random(seed)
    ox, oy = box[0], box[1]
    tile = Image.new("RGB", (box[2] - box[0], box[3] - box[1]), (36, 30, 24))   # clip to the cell
    d = ImageDraw.Draw(tile)
    x0, y0, x1, y1 = 0, 0, tile.width, tile.height
    if kind == "plastik":
        bh = (y1 - y0) / 3
        for r in range(3):
            x = x0 + rng.randint(-30, 0)
            while x < x1:
                w = rng.randint(90, 130)
                by0, by1 = y0 + r * bh + 4, y0 + (r + 1) * bh - 4
                d.rectangle((x, by0, x + w, by1), fill=(150, 150, 146))
                for _ in range(int(w * (by1 - by0) / 70)):       # crushed bottles / film speckle
                    px, py = rng.uniform(x, x + w), rng.uniform(by0, by1)
                    c = rng.choice([(60, 120, 190), (220, 220, 215), (40, 140, 80), (200, 60, 50), (130, 190, 210), (240, 200, 60)])
                    d.rectangle((px, py, px + rng.randint(4, 12), py + rng.randint(3, 8)), fill=c)
                for sy in (0.3, 0.7):                             # wire straps
                    d.line([(x, by0 + (by1 - by0) * sy), (x + w, by0 + (by1 - by0) * sy)], fill=(60, 60, 60), width=3)
                x += w + 6
    elif kind == "kardus":
        y = y0
        while y < y1:
            h = rng.randint(8, 16)
            c = rng.choice([(170, 128, 80), (150, 110, 66), (186, 146, 98), (120, 90, 56)])
            d.rectangle((x0 + rng.randint(0, 8), y, x1 - rng.randint(0, 8), y + h), fill=c)
            y += h + 2
        for tx in range(int(x0) + 60, int(x1), 120):              # string ties
            d.rectangle((tx, y0, tx + 4, y1), fill=(220, 210, 180))
    else:                                                         # karung sacks
        bh = (y1 - y0) / 2
        for r in range(2):
            x = x0 + (40 if r else 0) - 40
            while x < x1:
                w = rng.randint(110, 140)
                c = rng.choice([(232, 228, 214), (220, 214, 196), (236, 236, 228), (200, 120, 60)])
                d.rounded_rectangle((x, y0 + r * bh + 4, x + w, y0 + (r + 1) * bh - 4), radius=30, fill=c)
                d.line([(x + 14, y0 + r * bh + bh * 0.5), (x + w - 14, y0 + r * bh + bh * 0.5)], fill=(180, 172, 150), width=3)
                x += w + 4
    img.paste(tile, (ox, oy))


def pengepul():
    """T_Env_PapanPengepul - must match gudang_pengepul.UV_*. Accent #A87018 (DESIGN 2.4)."""
    AMBER = (168, 112, 24)
    img = Image.new("RGB", (W, W), (36, 30, 24))
    d = ImageDraw.Draw(img)
    # main hand-painted board (0,0)-(1024,400)
    d.rectangle((0, 0, 1024, 400), fill=(92, 58, 20))
    d.rectangle((14, 14, 1010, 386), fill=AMBER)
    text_center(d, (20, 20, 1004, 140), "GUDANG", font("BarlowCondensed-Bold.ttf", 120), (250, 238, 210), shadow=(92, 58, 20))
    text_center(d, (20, 130, 1004, 270), "PENGEPUL", font("BarlowCondensed-Bold.ttf", 150), (250, 238, 210), shadow=(92, 58, 20))
    d.rectangle((60, 282, 964, 288), fill=(250, 238, 210))
    text_center(d, (20, 292, 1004, 380), "TERIMA SEMUA SAMPAH • SEKALI SETOR", font("BarlowCondensed-Bold.ttf", 64), (40, 26, 10))
    # price board (0,416)-(640,816)
    d.rectangle((0, 416, 640, 816), fill=(92, 58, 20))
    d.rectangle((12, 428, 628, 804), fill=(246, 238, 218))
    d.rectangle((12, 428, 628, 512), fill=AMBER)
    text_center(d, (12, 432, 628, 510), "HARGA BORONGAN", font("BarlowCondensed-Bold.ttf", 70), (250, 238, 210))
    rows = (("NORMAL", "Rp 2.000"), ("MEDIS", "Rp 3.000"), ("BIOHAZARD", "Rp 4.500"))
    for i, (k, v) in enumerate(rows):
        y = 524 + i * 64
        d.text((48, y), k, font=font("BarlowCondensed-Bold.ttf", 56), fill=(40, 26, 10))
        l, t, r, b = d.textbbox((0, 0), v, font=font("IBMPlexMono-Bold.ttf", 46))
        d.text((592 - (r - l), y + 6), v, font=font("IBMPlexMono-Bold.ttf", 46), fill=(40, 26, 10))
    d.rectangle((12, 724, 628, 804), fill=(206, 30, 36))
    t = "TANPA DENDA - TAPI WARGA KECEWA KALAU B3 DICAMPUR"
    text_center(d, (20, 728, 620, 800), t, fit_font(d, t, "BarlowCondensed-Bold.ttf", 590, 60, 50), (255, 255, 255))
    # rack stacks: plastic bales (656,416)-(1024,656), cardboard (656,672)-(1024,912), sacks (0,832)-(640,1024)
    bale_stack(img, (656, 416, 1024, 656), 31, "plastik")
    bale_stack(img, (656, 672, 1024, 912), 32, "kardus")
    bale_stack(img, (0, 832, 640, 1024), 33, "karung")
    d = ImageDraw.Draw(img)
    d.rectangle((656, 928, 1024, 1024), fill=(52, 38, 26))           # dark timber / edge
    out = grime(img, [(0, 0, 1024, 400), (0, 416, 640, 816)], 7)
    path = os.path.join(TEX, "T_Env_PapanPengepul.png")
    out.save(path, optimize=True)
    return path


# ---------------------------------------------------------------- quest landmarks + wayfinding (Priority 0)
WOOD_DARK, WOOD_MID, WOOD_LIGHT = (66, 44, 26), (124, 86, 52), (196, 160, 112)
TEAL = (27, 107, 99)
MEDIS_BLUE = (30, 84, 170)
BIO_PURPLE = (88, 28, 135)
LANDMARK_RECTS = {   # must match landmark.py (px boxes, top-left origin)
    "tangga": (0, 0, 1024, 160), "ronda": (0, 176, 1024, 336),
    "warung_barat": (0, 352, 512, 480), "warung_timur": (512, 352, 1024, 480),
    "arah_medis": (0, 496, 512, 624), "arah_karantina": (512, 496, 1024, 624),
    "arah_bank": (0, 640, 512, 768), "awas_tiang": (512, 640, 1024, 768),
    "pengumuman": (0, 784, 640, 1024),
    "edge_wood": (672, 784, 848, 904), "edge_dark": (848, 784, 1024, 904),
    "edge_cream": (672, 904, 848, 1024), "edge_white": (848, 904, 1024, 1024),
}


def plank_board(d, box, base=WOOD_MID, planks=3):
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=WOOD_DARK)
    h = (y1 - y0 - 12) / planks
    for i in range(planks):
        c = tuple(max(0, v - i * 6) for v in base)
        d.rectangle((x0 + 6, y0 + 6 + i * h, x1 - 6, y0 + 4 + (i + 1) * h), fill=c)


def arrow_board(img, box, title, colour, icon):
    """Wayfinding arrow: coloured station band with the icon on the left; the mesh cuts the
    pointed tip on the right, so the right 18 % stays plain colour."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    h = y1 - y0
    d.rectangle(box, fill=(250, 250, 244))
    d.rectangle((x0 + 6, y0 + 6, x1 - 6, y1 - 6), fill=colour)
    s = h - 32
    icon(img, (x0 + 18, y0 + 16, x0 + 18 + s, y0 + 16 + s))
    d = ImageDraw.Draw(img)
    f = fit_font(d, title, "BarlowCondensed-Bold.ttf", (x1 - x0) * 0.82 - s - 40, h * 0.62)
    text_center(d, (x0 + 30 + s, y0, x1 - (x1 - x0) * 0.18, y1), title, f, (250, 250, 246), shadow=tuple(v // 2 for v in colour))


def _icon_cross(img, b):
    red_cross(ImageDraw.Draw(img), b)


def _icon_bio(img, b):
    d = ImageDraw.Draw(img)
    d.ellipse(b, fill=HAZ_YELLOW)
    s = b[2] - b[0]
    stamp(img, biohazard_mask(int(s * 0.8)), (b[0] + s * 0.1, b[1] + s * 0.1), BLACK)


def _icon_leaf(img, b):
    """Leaf on a stem, tilted 40 deg so it reads as a leaf (Bank Sampah = organic / recycle)."""
    d = ImageDraw.Draw(img)
    d.ellipse(b, fill=(250, 250, 244))
    s = int(b[2] - b[0])
    lay = Image.new("RGBA", (s * 2, s * 2), (0, 0, 0, 0))
    ld = ImageDraw.Draw(lay)
    leaf(ld, s, s, s * 0.6, GREEN + (255,))
    ld.line([(s - s * 0.42, s), (s - s * 0.68, s)], fill=GREEN_DEEP + (255,), width=max(3, s // 16))
    ld.line([(s - s * 0.42, s), (s + s * 0.36, s - s * 0.01)], fill=(250, 250, 244, 200), width=max(2, s // 26))
    lay = lay.rotate(40, resample=Image.BICUBIC).resize((s, s), Image.LANCZOS)
    base = img.convert("RGBA"); base.alpha_composite(lay, (int(b[0]), int(b[1])))
    img.paste(base.convert("RGB"))


def notice_board(img, box):
    """Pak RT's cork notice board: kerja bakti flyer, ronda roster and a sorting poster that
    repeats the tutorial (3 stations)."""
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    d.rectangle(box, fill=WOOD_DARK)
    d.rectangle((x0 + 10, y0 + 10, x1 - 10, y1 - 10), fill=(176, 132, 84))          # cork
    rng = random.Random(9)
    for _ in range(900):
        px, py = rng.randint(x0 + 10, x1 - 10), rng.randint(y0 + 10, y1 - 10)
        d.point((px, py), fill=(150, 108, 66))
    # sorting poster (left, biggest): PILAH SAMPAHMU
    px0, py0, px1, py1 = x0 + 22, y0 + 20, x0 + 330, y1 - 18
    d.rectangle((px0, py0, px1, py1), fill=(250, 250, 244))
    text_center(d, (px0, py0 + 2, px1, py0 + 44), "PILAH SAMPAHMU!", font("BarlowCondensed-Bold.ttf", 40), INK)
    rows = [("BIASA", "BANK SAMPAH", GREEN, _icon_leaf), ("MEDIS B3", "POS MEDIS", MEDIS_BLUE, _icon_cross),
            ("BIOHAZARD", "KARANTINA", BIO_PURPLE, _icon_bio)]
    rh = (py1 - py0 - 56) / 3
    for i, (a, b, c, ic) in enumerate(rows):
        ry = py0 + 50 + i * rh
        d.rectangle((px0 + 8, ry, px1 - 8, ry + rh - 8), fill=c)
        sz = int(rh - 22)
        ic(img, (px0 + 16, ry + 7, px0 + 16 + sz, ry + 7 + sz))
        d = ImageDraw.Draw(img)
        line = a + "  \u00bb  " + b
        f = fit_font(d, line, "BarlowCondensed-Bold.ttf", px1 - px0 - sz - 44, rh - 20, start=40)
        text_center(d, (px0 + 26 + sz, ry, px1 - 12, ry + rh - 8), line, f, (250, 250, 246))
    # kerja bakti flyer (top right, yellow) + ronda roster (bottom right, white, slightly rotated)
    fl = Image.new("RGB", (270, 110), HAZ_YELLOW)
    fd = ImageDraw.Draw(fl)
    text_center(fd, (0, 4, 270, 56), "KERJA BAKTI", font("BarlowCondensed-Bold.ttf", 46), INK)
    text_center(fd, (0, 54, 270, 106), "MINGGU 07.00  •  KALI RT 05", font("BarlowCondensed-SemiBold.ttf", 26), INK)
    img.paste(fl.rotate(3, expand=True, fillcolor=(176, 132, 84)), (x0 + 345, y0 + 18))
    ro = Image.new("RGB", (250, 96), (246, 244, 236))
    rd = ImageDraw.Draw(ro)
    text_center(rd, (0, 2, 250, 40), "JADWAL RONDA", font("BarlowCondensed-Bold.ttf", 32), INK)
    for i, n in enumerate(("SEN  Pak Darto", "RAB  Pak RT")):
        rd.text((14, 42 + i * 26), n, font=font("BarlowCondensed-SemiBold.ttf", 24), fill=(60, 60, 64))
    img.paste(ro.rotate(-2, expand=True, fillcolor=(176, 132, 84)), (x0 + 355, y0 + 128))
    d = ImageDraw.Draw(img)
    for (cx, cy) in ((x0 + 300, y0 + 26), (x0 + 480, y0 + 24), (x0 + 480, y0 + 134)):
        d.ellipse((cx - 7, cy - 7, cx + 7, cy + 7), fill=CROSS_RED)                  # push pins


def landmark():
    """T_Env_PapanLandmark - quest landmarks (Tangga Cuci, Pos Ronda, warung stalls, snag
    warning) and the wayfinding arrows that point new players to the 3 stations."""
    img = Image.new("RGB", (W, W), (40, 42, 46))
    d = ImageDraw.Draw(img)
    R = LANDMARK_RECTS
    plank_board(d, R["tangga"])
    text_center(d, (8, 4, 1016, 112), "TANGGA CUCI", font("BarlowCondensed-Bold.ttf", 108), (246, 240, 224), shadow=WOOD_DARK)
    text_center(d, (8, 104, 1016, 156), "JAGA KALI TETAP BERSIH  •  AWAS JARUM BEKAS!", font("BarlowCondensed-SemiBold.ttf", 38), HAZ_YELLOW)
    x0, y0, x1, y1 = R["ronda"]
    d.rectangle(R["ronda"], fill=(14, 60, 56))
    d.rectangle((x0 + 8, y0 + 8, x1 - 8, y1 - 8), fill=TEAL)
    text_center(d, (x0, y0 + 2, x1, y0 + 112), "POS RONDA", font("BarlowCondensed-Bold.ttf", 108), (250, 250, 246), shadow=(14, 60, 56))
    text_center(d, (x0, y0 + 104, x1, y1 - 6), "RT 05 / RW 02  •  KAMPUNG KALI", font("BarlowCondensed-SemiBold.ttf", 38), HAZ_YELLOW)
    for key, title, sub, col in (("warung_barat", "WARUNG MBOK NAH", "ES TEH • KOPI • GORENGAN", (214, 40, 40)),
                                 ("warung_timur", "WARUNG KOPI", "NGOPI DULU, NAK!", (30, 110, 200))):
        x0, y0, x1, y1 = R[key]
        d.rectangle(R[key], fill=(250, 250, 244))
        d.rectangle((x0 + 6, y0 + 6, x1 - 6, y1 - 6), fill=col)
        text_center(d, (x0, y0 + 4, x1, y0 + 84), title, fit_font(d, title, "BarlowCondensed-Bold.ttf", 470, 74), (250, 250, 246), shadow=tuple(v // 2 for v in col))
        text_center(d, (x0, y0 + 80, x1, y1 - 8), sub, font("BarlowCondensed-SemiBold.ttf", 30), HAZ_YELLOW)
    arrow_board(img, R["arah_medis"], "POS MEDIS B3", MEDIS_BLUE, _icon_cross)
    arrow_board(img, R["arah_karantina"], "KARANTINA", BIO_PURPLE, _icon_bio)
    arrow_board(img, R["arah_bank"], "BANK SAMPAH", GREEN_DEEP, _icon_leaf)
    x0, y0, x1, y1 = R["awas_tiang"]
    hazard_stripes(img, R["awas_tiang"], band=36)
    d = ImageDraw.Draw(img)
    d.rectangle((x0 + 22, y0 + 20, x1 - 22, y1 - 20), fill=(250, 250, 244))
    msg = "AWAS! KAIL NYANGKUT"
    text_center(d, (x0 + 22, y0 + 18, x1 - 22, y1 - 20), msg, fit_font(d, msg, "BarlowCondensed-Bold.ttf", x1 - x0 - 80, y1 - y0 - 52), CROSS_RED)
    notice_board(img, R["pengumuman"])
    d = ImageDraw.Draw(img)
    for key, col in (("edge_wood", WOOD_MID), ("edge_dark", WOOD_DARK), ("edge_cream", (236, 228, 206)), ("edge_white", (250, 250, 244))):
        d.rectangle(R[key], fill=col)
    out = grime(img, [R[k] for k in ("tangga", "ronda", "warung_barat", "warung_timur", "arah_medis", "arah_karantina", "arah_bank", "awas_tiang", "pengumuman")], 11)
    path = os.path.join(TEX, "T_Env_PapanLandmark.png")
    out.save(path, optimize=True)
    return path


# ---------------------------------------------------------------- service-point marks (Core Mechanics v2, spec A)
LAYANAN_ROWS = [   # key, title, action line, board colour, text colour, icon; must match layanan.py
    ("BankSampah", "BANK SAMPAH", "[E]  SETOR SAMPAH BIASA", GREEN_DEEP, (250, 250, 246), "leaf"),
    ("Kopdes", "KOPDES", "[E]  BELI ALAT & UPGRADE", (217, 119, 6), (250, 250, 246), "kopdes"),
    ("Pengepul", "GUDANG PENGEPUL", "[E]  JUAL SEMUA SEKALIGUS", (168, 112, 24), (250, 250, 246), "rp"),
    ("PosMedis", "POS MEDIS B3", "[E]  SETOR LIMBAH MEDIS", HAZ_YELLOW, INK, "cross"),
    ("Karantina", "KARANTINA", "[E]  SETOR BIOHAZARD", BIO_PURPLE, (250, 250, 246), "bio"),
]
LAYANAN_ROW_H, LAYANAN_PITCH = 176, 192
LAYANAN_EDGE = {"wood": (0, 960, 256, 1024), "white": (256, 960, 512, 1024)}


def _icon_kopdes(img, b):
    d = ImageDraw.Draw(img)
    d.ellipse(b, fill=(250, 250, 244))
    s = b[2] - b[0]
    kopdes_emblem(d, (b[0] + b[2]) / 2, b[1] + s * 0.22, s * 0.62)


def _icon_rp(img, b):
    d = ImageDraw.Draw(img)
    d.ellipse(b, fill=(250, 250, 244))
    s = b[2] - b[0]
    d.ellipse((b[0] + s * 0.1, b[1] + s * 0.1, b[2] - s * 0.1, b[3] - s * 0.1), outline=(168, 112, 24), width=max(4, int(s * 0.06)))
    text_center(d, b, "Rp", font("BarlowCondensed-Bold.ttf", int(s * 0.46)), (120, 78, 14))


def layanan_board(img, box, title, sub, colour, ink, icon):
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    h = y1 - y0
    d.rectangle(box, fill=(250, 250, 244))
    d.rectangle((x0 + 8, y0 + 8, x1 - 8, y1 - 8), fill=colour)
    s = h - 40
    {"leaf": _icon_leaf, "kopdes": _icon_kopdes, "rp": _icon_rp, "cross": _icon_cross, "bio": _icon_bio}[icon](img, (x0 + 24, y0 + 20, x0 + 24 + s, y0 + 20 + s))
    d = ImageDraw.Draw(img)
    tx0 = x0 + 48 + s
    shadow = tuple(v // 2 for v in colour)
    f = fit_font(d, title, "BarlowCondensed-Bold.ttf", x1 - tx0 - 30, h * 0.52)
    text_center(d, (tx0, y0 + 10, x1 - 20, y0 + h * 0.62), title, f, ink, shadow=None if ink == INK else shadow)
    f2 = fit_font(d, sub, "BarlowCondensed-SemiBold.ttf", x1 - tx0 - 30, h * 0.26, start=60)
    text_center(d, (tx0, y0 + h * 0.6, x1 - 20, y1 - 14), sub, f2, ink)


def _foot(d, cx, cy, s, flip):
    """Painted shoe print: sole oval + heel, toe pointing up (toward the counter)."""
    k = -1 if flip else 1
    d.ellipse((cx - s * 0.34, cy - s, cx + s * 0.34, cy + s * 0.15), fill=255)
    d.ellipse((cx - s * 0.27 + k * s * 0.03, cy + s * 0.3, cx + s * 0.27 + k * s * 0.03, cy + s * 0.95), fill=255)


def tanda_lantai():
    """T_Env_TandaLantai: white worn paint (RGBA) tinted per station in Unity. 1024 px = 4.4 m, so the
    dashed ring sits on the 2.0 m service-point radius. Top of the texture faces the counter."""
    S = 1024
    a = Image.new("L", (S, S), 0)
    d = ImageDraw.Draw(a)
    c, r, wdt, n = S / 2, 2.0 / 4.4 * S, 30, 28
    for i in range(n):
        st = i * 360 / n
        d.arc((c - r, c - r, c + r, c + r), st, st + 360 / n * 0.62, fill=255, width=wdt)
    f = font("BarlowCondensed-Bold.ttf", 118)
    l, t, rr, b = d.textbbox((0, 0), "BERDIRI DI SINI", font=f)
    d.text(((S - (rr - l)) / 2 - l, 290 - (b - t) / 2 - t), "BERDIRI DI SINI", font=f, fill=255, stroke_width=4, stroke_fill=255)
    d.rounded_rectangle((c - 62, 380, c + 62, 504), radius=18, outline=255, width=14)
    text_center(d, (c - 62, 380, c + 62, 500), "E", font("BarlowCondensed-Bold.ttf", 96), 255)
    _foot(d, c - 70, 680, 120, False)
    _foot(d, c + 70, 680, 120, True)
    # worn paint: scuffs and specks knocked out of the alpha
    n1 = Image.effect_noise((S // 8, S // 8), 60).resize((S, S), Image.BICUBIC)
    n2 = Image.effect_noise((S, S), 70)
    wear = Image.composite(Image.new("L", (S, S), 0), Image.new("L", (S, S), 255), n1.point(lambda v: 255 if v > 196 else 0))
    wear = Image.composite(Image.new("L", (S, S), 0), wear, n2.point(lambda v: 255 if v > 228 else 0))
    a = ImageChops.multiply(a, wear.filter(ImageFilter.GaussianBlur(1.2)))
    img = Image.new("RGBA", (S, S), (255, 255, 255, 0))
    img.putalpha(a)
    out = os.path.join(TEX, "T_Env_TandaLantai.png")
    img.save(out, optimize=True)
    return out


def layanan():
    """T_Env_PapanLayanan (5 station boards for the service-point posts) + T_Env_TandaLantai."""
    img = Image.new("RGB", (W, W), (40, 42, 46))
    boxes = []
    for i, (key, title, sub, col, ink, icon) in enumerate(LAYANAN_ROWS):
        box = (0, i * LAYANAN_PITCH, W, i * LAYANAN_PITCH + LAYANAN_ROW_H)
        boxes.append(box)
        layanan_board(img, box, title, sub, col, ink, icon)
    d = ImageDraw.Draw(img)
    d.rectangle(LAYANAN_EDGE["wood"], fill=WOOD_MID)
    d.rectangle(LAYANAN_EDGE["white"], fill=(250, 250, 244))
    out = grime(img, boxes, 21)
    path = os.path.join(TEX, "T_Env_PapanLayanan.png")
    out.save(path, optimize=True)
    tanda_lantai()
    return path


ATLASES = {"bank_sampah": bank_sampah, "kopdes": kopdes, "pos_medis": pos_medis, "karantina": karantina, "umum": umum, "warung": warung, "pengepul": pengepul, "landmark": landmark, "layanan": layanan}


def main():
    """python3 papan.py [bank_sampah] [kopdes] [pos_medis] [karantina] [umum] [warung] [pengepul] - Image.effect_noise is not seeded, so only
    regenerate the atlas you are changing to keep the others' git diff clean."""
    import sys
    for key in sys.argv[1:] or ATLASES:
        print(os.path.relpath(ATLASES[key](), ROOT))


if __name__ == "__main__":
    main()
