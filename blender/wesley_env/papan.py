"""Sign atlases for Wesley's stations (1024 x 1024, PIL): every building gets readable
signage so players know what each station is for.
T_Env_PapanBankSampah (SM_Env_BankSampah), T_Env_PapanKopdes (SM_Env_KoperasiDesa),
T_Env_PapanPosMedis (SM_Env_PosMedisB3), T_Env_PapanKarantina (SM_Env_KarantinaBiohazard),
T_Env_PapanUmum (name boards on SM_Env_PintuAirSiaga1 + SM_Env_JembatanUtama).

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
    """T_Env_PapanUmum - name boards retro-fitted on Pintu Air and Jembatan Utama."""
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
    out = grime(img, [(0, 0, 1024, 160), (0, 176, 1024, 336)], 5)
    path = os.path.join(TEX, "T_Env_PapanUmum.png")
    out.save(path, optimize=True)
    return path


ATLASES = {"bank_sampah": bank_sampah, "kopdes": kopdes, "pos_medis": pos_medis, "karantina": karantina, "umum": umum}


def main():
    """python3 papan.py [bank_sampah] [kopdes] [pos_medis] [karantina] [umum] - Image.effect_noise is not seeded, so only
    regenerate the atlas you are changing to keep the others' git diff clean."""
    import sys
    for key in sys.argv[1:] or ATLASES:
        print(os.path.relpath(ATLASES[key](), ROOT))


if __name__ == "__main__":
    main()
