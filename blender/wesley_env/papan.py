"""T_Env_PapanBankSampah - sign atlas for SM_Env_BankSampah (1024 x 1024, PIL).

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
OUT = os.path.join(ROOT, "unity", "Assets", "_Project", "Environment", "Textures", "T_Env_PapanBankSampah.png")

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


def main():
    img = Image.new("RGBA", (W, W), FRAME + (255,))
    board(img, (0, 0, 1024, 256), "BANK SAMPAH", "BERKAH")
    for (x, y), word in zip([(0, 256), (512, 256), (0, 384), (512, 384)], ["BOTOL", "PLASTIK", "KERTAS", "DAUN"]):
        board(img, (x, y, x + 512, y + 128), word)
    ledger(img, (0, 512, 768, 896))
    dial(img, (768, 512, 1024, 768))
    out = weather(img)
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    out.save(OUT, optimize=True)
    print(os.path.relpath(OUT, ROOT))


if __name__ == "__main__":
    main()
