"""Procedural product labels (parody brand art: Indomy, BINGO, MOLI, Lifeman, SARI BOTI, Risol, Sprit,
GUDANG GULA) for the branded trash props and, later, clean product props.

Everything is painted in code, no photos and no hand-painted files:
  * a tiny numpy rasteriser fills polygons, ellipses, strokes and text at SS x supersampling;
  * text glyphs come from Blender's own font engine (TextCurve -> mesh triangles), using Windows
    fonts when present and Blender's built-in font otherwise (headless / Linux builds still work);
  * wear() adds the trash look: faded ink, crumple creases, mud / water stains, edge grime.
    dirty=False skips it, so the same art can be reused CLEAN for non-trash product props.

    out = render_label("indomy", w, h, dirty=True)
    out["albedo"] (h, w, 3) sRGB 0..1, out["normal"] (h, w, 3) tangent-space 0..1, out["smooth"] (h, w)

Row 0 is the BOTTOM of the label (Blender image order). Art is designed in centimetres of the real
print on one or more panels (rects of the label image); LAYOUTS says where each panel sits so the
prop modules can UV-map their faces onto it (see trash_shapes.panel_uv).
"""
import math
import os
import zlib

import bpy  # noqa: F401  (must be imported before bmesh / mathutils in the bpy wheel)
import numpy as np

SS = 3  # supersampling factor (anti-aliasing)
FONT_DIRS = ["C:/Windows/Fonts", "/usr/share/fonts/truetype/msttcorefonts", "/Library/Fonts"]

# Panel rects (x0, y0, x1, y1) as fractions of the label image, y up.
LAYOUTS = {
    "pack": {"front": (0.0, 0.0, 1.0, 1.0)},                                   # back faces mirror it
    "pair": {"front": (0.0, 0.0, 0.5, 1.0), "back": (0.5, 0.0, 1.0, 1.0)},    # side by side
    "wrap": {"front": (0.0, 0.5, 1.0, 1.0), "back": (0.0, 0.0, 1.0, 0.5)},    # bottle band halves
    "box": {"front": (0.0, 0.0, 0.5, 1.0), "side_l": (0.5, 0.0, 0.75, 1.0), "side_r": (0.75, 0.0, 1.0, 1.0)},
}


def hexc(h):
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)], np.float32)


# ---------------------------------------------------------------- fonts / glyphs
_FONT_CACHE, _GLYPH_CACHE = {}, {}
_LOADED = set()   # font datablocks this module created (removed again after each label)


def _font(fname):
    if fname not in _FONT_CACHE:
        _FONT_CACHE[fname] = None
        for d in FONT_DIRS:
            p = os.path.join(d, fname)
            if os.path.exists(p):
                before = set(bpy.data.fonts)
                font = bpy.data.fonts.load(p, check_existing=True)
                if font not in before:
                    _LOADED.add(font.name)
                _FONT_CACHE[fname] = font
                break
    return _FONT_CACHE[fname]


def _release_fonts():
    """Remove the system fonts loaded for glyphs, so they never end up saved in a .blend."""
    for name in _LOADED:
        font = bpy.data.fonts.get(name)
        if font is not None:
            bpy.data.fonts.remove(font)
    _LOADED.clear()
    _FONT_CACHE.clear()


def _glyphs(text, fname, shear, spacing):
    """Triangulated glyph outlines of `text` in font units: (points (n,2), tris (m,3))."""
    key = (text, fname, shear, spacing)
    if key not in _GLYPH_CACHE:
        cu = bpy.data.curves.new("_label_txt", "FONT")
        cu.body = text
        font = _font(fname) if fname else None
        if font is not None:
            cu.font = font
        cu.shear = shear
        cu.space_character = spacing
        cu.resolution_u = 5
        ob = bpy.data.objects.new("_label_txt", cu)
        me = bpy.data.meshes.new_from_object(ob)
        me.calc_loop_triangles()
        co = np.empty(len(me.vertices) * 3, np.float64)
        me.vertices.foreach_get("co", co)
        tri = np.empty(len(me.loop_triangles) * 3, np.int64)
        me.loop_triangles.foreach_get("vertices", tri)
        bpy.data.objects.remove(ob)
        bpy.data.curves.remove(cu)
        bpy.data.meshes.remove(me)
        _GLYPH_CACHE[key] = (co.reshape(-1, 3)[:, :2].copy(), tri.reshape(-1, 3))
    return _GLYPH_CACHE[key]


# ---------------------------------------------------------------- canvas
class Canvas:
    """Supersampled RGB canvas. Shapes return boolean coverage masks; paint() composites them."""

    def __init__(self, w, h, layout="pack"):
        self.w, self.h = w, h
        self.W, self.H = w * SS, h * SS
        self.rgb = np.ones((self.H, self.W, 3), np.float32)
        self.layout = LAYOUTS[layout]
        self.protect_px = []   # (x0, y0, x1, y1) final-res pixel rects where wear stays light
        self.panel_px = []     # final-res pixel rects of every panel (edge grime)
        for rect in self.layout.values():
            self.panel_px.append(tuple(int(round(v * s)) for v, s in zip(rect, (w, h, w, h))))
        self.ys = (np.arange(self.H) + 0.5)[:, None]
        self.xs = (np.arange(self.W) + 0.5)[None, :]

    # -- panel transform: design units (cm) -> supersampled pixels
    def panel(self, name, units):
        x0, y0, x1, y1 = self.layout[name]
        self.ox, self.oy = x0 * self.W, y0 * self.H
        self.sx, self.sy = (x1 - x0) * self.W / units[0], (y1 - y0) * self.H / units[1]
        self.units = units
        self.clip = (int(round(x0 * self.W)), int(round(y0 * self.H)), int(round(x1 * self.W)), int(round(y1 * self.H)))
        return self

    def px(self, pts):
        p = np.asarray(pts, np.float64).reshape(-1, 2)
        return np.stack([self.ox + p[:, 0] * self.sx, self.oy + p[:, 1] * self.sy], 1)

    def protect(self, x0, y0, x1, y1):
        a, b = self.px([(x0, y0), (x1, y1)]) / SS
        self.protect_px.append((int(a[0]), int(a[1]), int(math.ceil(b[0])), int(math.ceil(b[1]))))

    def _box(self, lo, hi):
        cx0, cy0, cx1, cy1 = self.clip
        x0, y0 = max(int(math.floor(lo[0])), cx0), max(int(math.floor(lo[1])), cy0)
        x1, y1 = min(int(math.ceil(hi[0])) + 1, cx1), min(int(math.ceil(hi[1])) + 1, cy1)
        return x0, y0, x1, y1

    def empty(self):
        return np.zeros((self.H, self.W), bool)

    def full(self):
        m = self.empty()
        x0, y0, x1, y1 = self.clip
        m[y0:y1, x0:x1] = True
        return m

    # -- shapes (design units)
    def poly(self, pts):
        """Even-odd filled polygon."""
        P = self.px(pts)
        m = self.empty()
        x0, y0, x1, y1 = self._box(P.min(0), P.max(0))
        if x1 <= x0 or y1 <= y0:
            return m
        X, Y = self.xs[:, x0:x1], self.ys[y0:y1]
        inside = np.zeros((y1 - y0, x1 - x0), bool)
        for i in range(len(P)):
            (ax, ay), (bx, by) = P[i], P[i - 1]
            if ay == by:
                continue
            inside ^= ((ay > Y) != (by > Y)) & (X < (bx - ax) * (Y - ay) / (by - ay) + ax)
        m[y0:y1, x0:x1] = inside
        return m

    def rect(self, x0, y0, x1, y1):
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)])

    def ellipse(self, cx, cy, rx, ry, rot=0.0):
        (pcx, pcy), = self.px([(cx, cy)])
        rxp, ryp = rx * self.sx, ry * self.sy
        R = max(rxp, ryp) * 1.01 + 1
        m = self.empty()
        x0, y0, x1, y1 = self._box((pcx - R, pcy - R), (pcx + R, pcy + R))
        if x1 <= x0 or y1 <= y0:
            return m
        dx, dy = self.xs[:, x0:x1] - pcx, self.ys[y0:y1] - pcy
        c, s = math.cos(math.radians(rot)), math.sin(math.radians(rot))
        u, v = (dx * c + dy * s) / max(rxp, 1e-6), (-dx * s + dy * c) / max(ryp, 1e-6)
        m[y0:y1, x0:x1] = u * u + v * v <= 1.0
        return m

    def rrect(self, cx, cy, w, h, r):
        """Rounded rectangle centred at (cx, cy)."""
        m = self.rect(cx - w / 2 + r, cy - h / 2, cx + w / 2 - r, cy + h / 2)
        m |= self.rect(cx - w / 2, cy - h / 2 + r, cx + w / 2, cy + h / 2 - r)
        for sx in (-1, 1):
            for sy in (-1, 1):
                m |= self.ellipse(cx + sx * (w / 2 - r), cy + sy * (h / 2 - r), r, r)
        return m

    def tris(self, P, T):
        """Rasterise triangles given in supersampled pixel coords."""
        m = self.empty()
        A, B, C = P[T[:, 0]], P[T[:, 1]], P[T[:, 2]]
        lo = np.minimum(np.minimum(A, B), C)
        hi = np.maximum(np.maximum(A, B), C)
        for a, b, c, l, h in zip(A, B, C, lo, hi):
            x0, y0, x1, y1 = self._box(l, h)
            if x1 <= x0 or y1 <= y0:
                continue
            X, Y = self.xs[:, x0:x1], self.ys[y0:y1]
            e0 = (b[0] - a[0]) * (Y - a[1]) - (b[1] - a[1]) * (X - a[0])
            e1 = (c[0] - b[0]) * (Y - b[1]) - (c[1] - b[1]) * (X - b[0])
            e2 = (a[0] - c[0]) * (Y - c[1]) - (a[1] - c[1]) * (X - c[0])
            m[y0:y1, x0:x1] |= ((e0 >= 0) & (e1 >= 0) & (e2 >= 0)) | ((e0 <= 0) & (e1 <= 0) & (e2 <= 0))
        return m

    def text(self, s, x, y, h, font="arialbd.ttf", max_w=None, shear=0.0, rot=0.0, spacing=1.0, stretch=1.0):
        """Text whose ink box is h tall (shrunk to fit max_w), centred on (x, y). Returns its mask."""
        pts, tri = _glyphs(s, font, shear, spacing)
        if not len(tri):
            return self.empty()
        lo, hi = pts.min(0), pts.max(0)
        k = h / max(hi[1] - lo[1], 1e-6)
        if max_w is not None:
            k = min(k, max_w / max((hi[0] - lo[0]) * stretch, 1e-6))
        p = (pts - (lo + hi) / 2) * k
        p[:, 0] *= stretch
        if rot:
            c, sn = math.cos(math.radians(rot)), math.sin(math.radians(rot))
            p = np.stack([p[:, 0] * c - p[:, 1] * sn, p[:, 0] * sn + p[:, 1] * c], 1)
        return self.tris(self.px(p + (x, y)), tri)

    def stroke(self, pts, width):
        """Polyline of constant width with round joints."""
        m = self.empty()
        r = width / 2
        for (ax, ay), (bx, by) in zip(pts[:-1], pts[1:]):
            dx, dy = bx - ax, by - ay
            L = math.hypot(dx, dy) or 1e-9
            nx, ny = -dy / L * r, dx / L * r
            m |= self.poly([(ax + nx, ay + ny), (bx + nx, by + ny), (bx - nx, by - ny), (ax - nx, ay - ny)])
        for (ax, ay) in pts:
            m |= self.ellipse(ax, ay, r, r)
        return m

    def grow(self, m, r):
        """Dilate a mask by r design units (octagonal), used for outlines."""
        nx, ny = max(1, int(round(r * self.sx))), max(1, int(round(r * self.sy)))
        out = m.copy()
        for i in range(max(nx, ny)):
            sx, sy = int(i < nx), int(i < ny)
            src = out.copy()
            if sx:
                out[:, 1:] |= src[:, :-1]
                out[:, :-1] |= src[:, 1:]
            if sy:
                out[1:] |= src[:-1]
                out[:-1] |= src[1:]
            if sx and sy and i % 2:
                out[1:, 1:] |= src[:-1, :-1]
                out[:-1, :-1] |= src[1:, 1:]
                out[1:, :-1] |= src[:-1, 1:]
                out[:-1, 1:] |= src[1:, :-1]
        return out

    def shift(self, m, dx, dy):
        ix, iy = int(round(dx * self.sx)), int(round(dy * self.sy))
        return np.roll(np.roll(m, iy, 0), ix, 1)

    # -- colour fields (full-size arrays) for gradients
    def vgrad(self, y0, y1, c0, c1):
        (_, a), (_, b) = self.px([(0, y0), (0, y1)])
        t = np.clip((self.ys - a) / (b - a), 0, 1)[..., None]
        return np.broadcast_to(hexc(c0) * (1 - t) + hexc(c1) * t, (self.H, self.W, 3))

    def rgrad(self, cx, cy, r, c0, c1):
        (pcx, pcy), = self.px([(cx, cy)])
        d = np.sqrt(((self.xs - pcx) / self.sx) ** 2 + ((self.ys - pcy) / self.sy) ** 2) / r
        t = np.clip(d, 0, 1)[..., None]
        return hexc(c0) * (1 - t) + hexc(c1) * t

    def paint(self, m, color, alpha=1.0):
        if isinstance(color, str):
            col = hexc(color)
            self.rgb[m] = self.rgb[m] * (1 - alpha) + col * alpha
        else:
            self.rgb[m] = self.rgb[m] * (1 - alpha) + np.asarray(color)[m] * alpha
        return m

    def outlined(self, m, fill, lines, shadow=None):
        """Paint mask m with stacked outlines: lines = [(colour, width), ...] outermost first."""
        if shadow:
            col, dx, dy, w = shadow
            self.paint(self.shift(self.grow(m, w), dx, dy), col)
        total = sum(w for _, w in lines)
        for col, w in lines:
            self.paint(self.grow(m, total), col)
            total -= w
        self.paint(m, fill)
        return m

    def result(self):
        r = self.rgb.reshape(self.h, SS, self.w, SS, 3).mean(axis=(1, 3))
        return np.clip(r, 0, 1)


# ---------------------------------------------------------------- noise / wear
def _value_noise(h, w, cell, rng):
    gh, gw = int(h / cell) + 2, int(w / cell) + 2
    g = rng.random((gh, gw)).astype(np.float32)
    ys, xs = np.arange(h) / cell, np.arange(w) / cell
    y0, x0 = ys.astype(int), xs.astype(int)
    fy, fx = ys - y0, xs - x0
    fy, fx = (fy * fy * (3 - 2 * fy))[:, None], (fx * fx * (3 - 2 * fx))[None, :]
    a, b = g[y0][:, x0], g[y0][:, x0 + 1]
    c, d = g[y0 + 1][:, x0], g[y0 + 1][:, x0 + 1]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(h, w, rng, base, octaves=4):
    out, amp, tot = np.zeros((h, w), np.float32), 1.0, 0.0
    for i in range(octaves):
        out += _value_noise(h, w, max(base / 2 ** i, 1.5), rng) * amp
        tot += amp
        amp *= 0.5
    return out / tot


def _smooth(x, a, b):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def _cells(h, w, n, rng):
    """Worley cells: (crease intensity 0..1, cell id) - the faceted crumple of plastic film."""
    pts = rng.random((n, 2)) * (w, h)
    ys, xs = np.mgrid[0:h, 0:w].astype(np.float32)
    d = np.sqrt((xs[..., None] - pts[:, 0]) ** 2 + (ys[..., None] - pts[:, 1]) ** 2)
    idx = np.argsort(d, axis=2)[..., :2]
    f1 = np.take_along_axis(d, idx[..., :1], 2)[..., 0]
    f2 = np.take_along_axis(d, idx[..., 1:2], 2)[..., 0]
    return np.clip(1 - (f2 - f1) / 1.3, 0, 1), idx[..., 0]


WEAR = {  # crease cells, crease tint, mud, fade, grime, normal tilt, base smoothness
    "film":   dict(cells=60, crease=0.65, crease_col="#f2f2ee", mud=0.55, fade=0.18, grime=0.45, tilt=0.22, smooth=0.55),
    "bottle": dict(cells=10, crease=0.35, crease_col="#ffffff", mud=0.32, fade=0.15, grime=0.35, tilt=0.10, smooth=0.60),
    "carton": dict(cells=8, crease=0.70, crease_col="#efe3d3", mud=0.45, fade=0.12, grime=0.55, tilt=0.15, smooth=0.35),
    "foam":   dict(cells=0, crease=0.0, crease_col="#ffffff", mud=0.45, fade=0.0, grime=0.55, tilt=0.0, smooth=0.25),
}
MUD = hexc("#664f2c")
GRIME = hexc("#3b3326")


def wear(rgb, kind, rng, panels, protect):
    """Trash look: fade, crumple creases, mud/water stains, edge grime. Returns (rgb, normal, smooth)."""
    p = WEAR[kind]
    h, w, _ = rgb.shape
    keep = np.ones((h, w), np.float32)      # 1 = full wear, lower inside the logo rects
    for x0, y0, x1, y1 in protect:
        keep[max(y0, 0):y1, max(x0, 0):x1] = 0.35
    nrm = np.zeros((h, w, 3), np.float32)
    nrm[...] = (0.5, 0.5, 1.0)
    # sun-faded ink: lift toward a pale, less saturated version
    lum = rgb.mean(2, keepdims=True)
    faded = (rgb * 0.6 + lum * 0.4) * 0.8 + 0.2
    f = (p["fade"] * (0.5 + fbm(h, w, rng, 90)))[..., None]
    rgb = rgb * (1 - f) + faded * f
    # crumple creases: Worley cell borders become light cracked-ink lines + faceted normals
    if p["cells"]:
        crease, cid = _cells(h, w, p["cells"], rng)
        crease *= _smooth(fbm(h, w, rng, 45), 0.42, 0.6)          # broken, not a full web
        a = (crease * p["crease"] * (0.55 + 0.45 * keep))[..., None]
        rgb = rgb * (1 - a) + hexc(p["crease_col"]) * a
        tilt = rng.normal(0, p["tilt"], (p["cells"], 2)).astype(np.float32)
        t = tilt[cid]
        nz = np.sqrt(np.clip(1 - (t ** 2).sum(-1), 0.2, 1))
        nrm = np.stack([t[..., 0], t[..., 1], nz], -1) * 0.5 + 0.5
        shade = (1 + (t[..., 0] - t[..., 1]) * 0.15)[..., None]   # baked facet light, reads at distance
        rgb = rgb * shade
    # mud / water stains: blotches with a darker tide line, heavier toward the bottom
    n = fbm(h, w, rng, 70)
    bottom = np.linspace(1.25, 0.75, h, dtype=np.float32)[:, None]
    blot = _smooth(n * bottom, 0.52, 0.62)
    tide = np.clip(1 - np.abs(n * bottom - 0.53) / 0.012, 0, 1) * 0.6
    m = (np.maximum(blot * 0.75, tide) * p["mud"] * keep)[..., None]
    rgb = rgb * (1 - m) + MUD * m
    # edge grime per panel + fine specks
    g = np.zeros((h, w), np.float32)
    for x0, y0, x1, y1 in panels:
        yy, xx = np.mgrid[y0:y1, x0:x1].astype(np.float32)
        d = np.minimum(np.minimum(xx - x0, x1 - 1 - xx), np.minimum(yy - y0, y1 - 1 - yy))
        g[y0:y1, x0:x1] = np.exp(-d / (0.07 * min(x1 - x0, y1 - y0)))
    g = (g * (0.55 + 0.45 * fbm(h, w, rng, 25)) * p["grime"])[..., None]
    rgb = rgb * (1 - g) + GRIME * g
    speck = (rng.random((h, w)) < 0.004)
    rgb[speck] = rgb[speck] * 0.55 + GRIME * 0.45
    dirt = np.clip(m[..., 0] + g[..., 0], 0, 1)
    smooth = p["smooth"] * (1 - 0.7 * dirt)
    return np.clip(rgb, 0, 1), nrm.astype(np.float32), smooth.astype(np.float32)


# ---------------------------------------------------------------- brand art
def _crimp(c, y0, y1, x0, x1, col, line_col):
    """Heat-sealed crimp strip: base colour with fine perpendicular serrations."""
    c.paint(c.rect(x0, y0, x1, y1), col)
    step = 0.22
    x = x0
    while x < x1:
        c.paint(c.rect(x, y0, x + step * 0.35, y1), line_col, 0.5)
        x += step


def _indomy(c):
    c.panel("front", (12.0, 10.0))
    c.paint(c.full(), "#f6f5ef")
    red = c.poly([(0.0, 1.3), (5.6, 1.3), (6.3, 3.9), (6.9, 9.15), (0.0, 9.15)])
    c.paint(red, "#e2231a")
    # yellow + green diagonal bands across the red block
    c.paint(c.poly([(0, 6.15), (8, 5.75), (8, 6.15), (0, 6.6)]) & red, "#ffc20e")
    c.paint(c.poly([(0, 5.2), (8, 4.8), (8, 5.75), (0, 6.15)]) & red, "#1a9a3d")
    c.outlined(c.text("Indomy", 3.45, 7.65, 1.75, "HARLOWSI.TTF", max_w=6.2, shear=0.05), "#ffffff",
               [("#ffffff", 0.08), ("#1d3c95", 0.22)], shadow=("#0e1f5a", 0.12, -0.14, 0.3))
    c.paint(c.text("Mi Instan", 3.3, 5.68, 0.55, "arialbd.ttf", max_w=4.0), "#ffffff")
    c.outlined(c.text("Mi", 1.55, 3.85, 1.25, "SCRIPTBL.TTF", max_w=2.5), "#ffd51c", [("#7d0d0d", 0.16)])
    c.outlined(c.text("goreng", 3.0, 2.45, 1.45, "SCRIPTBL.TTF", max_w=5.2), "#ffd51c", [("#7d0d0d", 0.16)])
    # black plate with fried noodles, fried egg, garnish, fork
    c.paint(c.ellipse(8.95, 4.75, 3.45, 3.35), "#1b1b1b")
    c.paint(c.ellipse(8.95, 4.75, 3.05, 2.95), "#2b2b2b")
    noodle = c.ellipse(8.9, 4.95, 2.6, 2.35)
    c.paint(noodle, "#c2832c")
    rng = np.random.default_rng(7)
    for _ in range(26):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(0, 2.0)
        x, y = 8.9 + r * math.cos(a), 4.95 + r * math.sin(a) * 0.9
        pts = [(x + 0.5 * math.cos(a + k), y + 0.35 * math.sin(a * 2 + k)) for k in (0, 0.8, 1.6)]
        c.paint(c.stroke(pts, 0.09) & noodle, "#7e4c16" if rng.random() < 0.5 else "#e6b45a")
    c.paint(c.poly([(8.95 + 1.5 * math.cos(t) * (1 + 0.12 * math.sin(5 * t)),
                     3.55 + 1.25 * math.sin(t) * (1 + 0.12 * math.sin(5 * t))) for t in np.linspace(0, 2 * math.pi, 28)]),
            "#fbfaf3")
    c.paint(c.ellipse(9.1, 3.65, 0.66, 0.6), "#f5a50c")
    c.paint(c.ellipse(8.92, 3.85, 0.18, 0.14), "#fff3c4")
    for gx, gy in ((10.9, 6.2), (11.4, 5.5), (10.5, 6.8)):
        c.paint(c.ellipse(gx, gy, 0.45, 0.35, 30), "#3c9a2c")
    c.paint(c.ellipse(11.1, 3.9, 0.7, 0.55), "#d23a22")
    c.paint(c.stroke([(9.6, 6.6), (11.95, 9.2)], 0.28), "#c9c9c9")
    for k in (-0.22, 0, 0.22):
        c.paint(c.stroke([(9.6 + k, 6.6 - k * 0.7), (9.0 + k, 5.9 - k * 0.7)], 0.08), "#c9c9c9")
    # crimped top / bottom seals with the red print running into them
    _crimp(c, 9.15, 10.0, 0, 12, "#f6f5ef", "#c8c8c0")
    _crimp(c, 0.0, 0.85, 0, 12, "#f6f5ef", "#c8c8c0")
    c.paint(c.rect(1.0, 9.35, 6.5, 9.8), "#e2231a", 0.8)
    c.paint(c.rect(2.0, 0.2, 7.5, 0.65), "#e2231a", 0.8)
    c.protect(0.2, 1.4, 7.0, 9.1)


def _bingo(c):
    c.panel("front", (16.5, 25.0))
    c.paint(c.full(), c.rgrad(8.25, 14.0, 13.0, "#26b3aa", "#0c827c"))
    cx, cy, R = 8.25, 15.4, 6.0
    c.paint(c.ellipse(cx, cy, R + 0.35, R + 0.35), "#ffffff")
    disc = c.ellipse(cx, cy, R, R)
    c.paint(disc, c.vgrad(cy + R, cy - R * 0.4, "#ffe04a", "#f07a18"))
    c.paint(c.poly([(1.5, 9), (1.5, 12.6), (4.0, 14.1), (6.0, 13.2), (8.6, 15.0), (11.2, 13.5), (15.0, 12.4), (15.0, 9)]) & disc, "#2f7fa3")
    c.paint(c.poly([(1.5, 9), (1.5, 11.6), (5.0, 12.9), (8.8, 11.7), (12.0, 12.6), (15.0, 11.2), (15.0, 9)]) & disc, "#155c61")
    # stork: white body, black wing / neck / head, red beak and legs
    c.paint(c.stroke([(7.6, 14.2), (7.45, 10.9)], 0.26), "#d8261e")
    c.paint(c.stroke([(8.3, 14.3), (9.7, 12.9), (8.2, 12.4)], 0.24), "#d8261e")
    c.paint(c.ellipse(7.5, 15.6, 3.0, 1.55, 18), "#ffffff")
    c.paint(c.poly([(3.9, 13.9), (6.0, 14.9), (8.9, 16.1), (9.4, 15.3), (7.2, 14.3), (5.0, 13.6)]), "#151515")
    c.paint(c.stroke([(9.3, 16.1), (10.1, 17.3), (10.1, 18.5), (10.8, 19.6)], 1.0), "#151515")
    c.paint(c.ellipse(11.05, 19.85, 0.9, 0.72), "#151515")
    c.paint(c.poly([(11.5, 20.25), (11.6, 19.55), (14.9, 18.0)]), "#e8452b")
    c.paint(c.ellipse(11.3, 20.05, 0.24, 0.24), "#ffffff")
    c.paint(c.ellipse(11.32, 20.05, 0.13, 0.13), "#d8261e")
    c.outlined(c.text("BINGO", 8.25, 7.85, 3.3, "BOOKOSB.TTF", max_w=14.2), "#dc1f1f",
               [("#ffffff", 0.35)], shadow=("#5e0b0b", 0.22, -0.28, 0.4))
    c.paint(c.text("Sejak 1982", 8.25, 5.6, 0.95, "MTCORSVA.TTF", max_w=6.0), "#ffffff")
    c.paint(c.rect(2.2, 5.55, 4.6, 5.65), "#ffffff")
    c.paint(c.rect(11.9, 5.55, 14.3, 5.65), "#ffffff")
    c.paint(c.text("KECAP MANIS", 8.25, 4.1, 0.95, "verdanab.ttf", max_w=11.0), "#ffffff")
    c.paint(c.ellipse(8.25, 1.9, 1.5, 1.25), "#1d2b2a")
    for bx, by in ((7.7, 1.7), (8.5, 2.2), (8.7, 1.4)):
        c.paint(c.ellipse(bx, by, 0.42, 0.3, 25), "#050505")
    # side seals and top seal
    for x0, x1 in ((0, 0.6), (15.9, 16.5)):
        c.paint(c.rect(x0, 0, x1, 25), "#0b7069")
    _crimp(c, 23.9, 25.0, 0, 16.5, "#0d7a73", "#0a5e59")
    c.protect(1.5, 3.4, 15.0, 21.6)


def _moli(c):
    c.panel("front", (10.0, 9.5))
    c.paint(c.full(), c.rgrad(4.0, 6.5, 8.0, "#14a046", "#05692b"))
    for k in range(4):
        c.paint(c.poly([(0, 1.6 + k * 1.9), (10, 0.7 + k * 1.9), (10, 1.0 + k * 1.9), (0, 1.9 + k * 1.9)]), "#2db35a", 0.35)
    c.paint(c.ellipse(5.2, 5.95, 4.25, 2.15, 6), "#c9a24a")
    c.paint(c.ellipse(5.2, 5.95, 4.08, 1.98, 6), "#ffffff")
    c.outlined(c.text("MOLI", 5.0, 5.75, 2.05, "ariblk.ttf", max_w=6.7, shear=0.22), "#4b230e",
               [("#ffffff", 0.06), ("#2a1306", 0.08)])
    # football boy swoosh, ball, Activ-Go badge, small print
    c.paint(c.poly([(0, 2.1), (3.0, 3.2), (6.5, 3.0), (10, 3.9), (10, 3.3), (6.5, 2.5), (3.0, 2.6), (0, 1.6)]), "#ffffff", 0.9)
    c.paint(c.ellipse(7.9, 1.75, 0.75, 0.75), "#ffffff")
    for a in range(5):
        t = a * 2 * math.pi / 5
        c.paint(c.ellipse(7.9 + 0.48 * math.cos(t), 1.75 + 0.48 * math.sin(t), 0.15, 0.15), "#222222")
    c.paint(c.ellipse(7.9, 1.75, 0.2, 0.2), "#222222")
    c.paint(c.ellipse(7.7, 4.45, 0.38, 0.38), "#f4c21b")
    for k in range(3):
        c.paint(c.rect(0.6, 1.0 + k * 0.28, 3.2 - k * 0.4, 1.1 + k * 0.28), "#e8f5ec", 0.7)
    _crimp(c, 8.9, 9.5, 0, 10, "#0a7a33", "#055c25")
    _crimp(c, 0.0, 0.6, 0, 10, "#0a7a33", "#055c25")
    c.protect(0.9, 3.8, 9.5, 8.1)


def _lifeman_logo(c, cx, cy, s):
    c.outlined(c.rect(cx - 0.42 * s, cy + 0.3 * s, cx + 0.42 * s, cy + 2.55 * s) |
               c.rect(cx - 1.1 * s, cy + 1.08 * s, cx + 1.1 * s, cy + 1.86 * s), "#e0251b", [("#ffffff", 0.14 * s)])
    c.outlined(c.rrect(cx, cy, 5.4 * s, 1.75 * s, 0.85 * s), "#d9211a", [("#ffffff", 0.12 * s), ("#b7b7b7", 0.04 * s)])
    c.paint(c.rrect(cx, cy - 0.35 * s, 5.0 * s, 0.7 * s, 0.35 * s), "#b0150f", 0.5)
    c.paint(c.text("Lifeman", cx, cy, 0.95 * s, "verdanaz.ttf", max_w=4.7 * s), "#ffffff")


def _lifeman(c):
    c.panel("front", (6.4, 15.0))
    c.paint(c.full(), c.vgrad(15, 0, "#f7f9fb", "#dfe9f4"))
    c.paint(c.rrect(3.2, 13.5, 5.0, 1.0, 0.2), "#1b3a8f")
    c.paint(c.text("EXTRA 20ML", 3.2, 13.5, 0.55, "arialbd.ttf", max_w=4.4), "#ffffff")
    _lifeman_logo(c, 3.2, 9.3, 1.08)
    c.paint(c.rect(0.4, 7.25, 6.0, 7.95), "#1f4fa6")
    c.paint(c.text("ANTI KETOMBE", 3.2, 7.6, 0.4, "arialbd.ttf", max_w=5.0), "#ffffff")
    for k in range(2):
        c.paint(c.rect(0.5, 6.4 - k * 0.4, 4.2 - k * 1.0, 6.6 - k * 0.4), "#56657a", 0.8)
    c.outlined(c.ellipse(1.4, 4.7, 0.8, 0.8), "#eaf2fb", [("#3d7fd1", 0.08)])
    c.paint(c.text("100%", 1.4, 4.75, 0.32, "arialbd.ttf", max_w=1.1), "#1f4fa6")
    bubble = c.ellipse(4.5, 3.6, 2.1, 2.1)
    c.paint(bubble, c.rgrad(4.2, 4.2, 2.4, "#ffffff", "#a9cbee"))
    for i in range(-2, 3):
        for j in range(-2, 3):
            hx, hy = 4.5 + i * 0.75 + (j % 2) * 0.37, 3.6 + j * 0.65
            c.paint(c.poly([(hx + 0.3 * math.cos(a), hy + 0.3 * math.sin(a)) for a in np.arange(6) * math.pi / 3]) & bubble,
                    "#5b9be0", 0.55)
    c.protect(0.2, 8.2, 6.2, 12.4)
    c.panel("back", (6.4, 15.0))
    c.paint(c.full(), c.vgrad(15, 0, "#f7f9fb", "#e3ecf5"))
    _lifeman_logo(c, 3.2, 11.6, 0.8)
    for k in range(10):
        c.paint(c.rect(0.6, 9.2 - k * 0.45, 5.8 - (k % 3) * 0.7, 9.4 - k * 0.45), "#6b7a8c", 0.7)
    c.paint(c.rect(1.6, 1.2, 4.8, 3.0), "#ffffff")
    for k in range(22):
        c.paint(c.rect(1.75 + k * 0.135, 1.45, 1.75 + k * 0.135 + (0.05 if k % 3 else 0.09), 2.8), "#111111")
    c.protect(0.4, 11.2, 6.0, 13.2)


def _sari_boti(c, full=False):
    c.panel("front", (28.0, 15.0))
    c.paint(c.full(), c.vgrad(15, 0, "#3a2418", "#21140d"))
    for k in range(5):
        x = 2 + k * 6
        c.paint(c.poly([(x, 0), (x + 1.2, 0), (x + 5.2, 15), (x + 4.0, 15)]), "#6b4a34", 0.25)
    # clear window bordered by gold stripes: empty milky plastic (trash) or the golden pull-apart rolls (full)
    win = c.poly([(19.5, 4.6), (25.5, 4.2), (25.8, 9.4), (19.3, 9.9)])
    c.paint(c.grow(win, 0.4), "#e7a51e")
    c.paint(c.grow(win, 0.16), "#2a1a12")
    if full:
        c.paint(win, c.vgrad(9.9, 4.2, "#e8b26a", "#b8742e"))
        for rx, ry in ((20.9, 8.2), (23.1, 8.1), (25.0, 8.0), (20.8, 5.8), (23.0, 5.6), (25.1, 5.5)):
            c.paint(c.ellipse(rx, ry, 1.0, 1.05) & win, "#9a5a22", 0.55)
            c.paint(c.ellipse(rx - 0.15, ry + 0.2, 0.75, 0.75) & win, "#f2c584", 0.7)
    else:
        c.paint(win, c.vgrad(9.9, 4.2, "#a9a49b", "#6f6a62"))
    c.paint(c.poly([(20.5, 4.5), (21.3, 4.5), (23.0, 9.8), (22.2, 9.8)]) & win, "#ffffff", 0.3)
    c.paint(c.poly([(0, 12.2), (28, 11.4), (28, 11.8), (0, 12.6)]), "#e7a51e")
    c.paint(c.poly([(0, 2.0), (28, 1.4), (28, 1.75), (0, 2.35)]), "#e7a51e")
    # logo: blue box with gold border, white serif SARI BOTI, white tag with script
    c.paint(c.rrect(11.0, 9.3, 11.6, 4.4, 0.7), "#e3a724")
    c.paint(c.rrect(11.0, 9.3, 10.9, 3.7, 0.5), "#ffffff")
    c.paint(c.rrect(11.0, 9.3, 10.5, 3.3, 0.45), "#1f3c8c")
    c.paint(c.text("SARI BOTI", 11.0, 9.35, 1.9, "timesbd.ttf", max_w=9.6), "#ffffff")
    c.paint(c.rrect(11.0, 6.15, 9.6, 1.9, 0.4), "#f4f1ea")
    c.paint(c.text("Roti Manis Lembut", 11.0, 6.15, 1.0, "MTCORSVA.TTF", max_w=8.6), "#1f3c8c")
    c.outlined(c.ellipse(17.6, 11.0, 1.05, 0.8), "#e3a724", [("#ffffff", 0.08)])
    c.paint(c.text("1999", 17.6, 11.0, 0.45, "arialbd.ttf", max_w=1.4), "#1f3c8c")
    c.outlined(c.ellipse(7.5, 3.4, 2.2, 1.05), "#5b2f1a", [("#f4f1ea", 0.12)])
    c.paint(c.text("Sobek", 7.5, 3.4, 0.95, "SCRIPTBL.TTF", max_w=3.4), "#ffffff")
    c.paint(c.text("Cokelat", 13.6, 3.3, 1.6, "SCRIPTBL.TTF", max_w=6.0), "#ffffff")
    for x0, x1 in ((0, 1.3), (26.7, 28)):
        _crimp(c, 0, 15, x0, x1, "#2a1a12", "#5a4232")
    c.protect(5.0, 5.0, 17.0, 11.6)


def _drop(c, cx, cy, ang, length, r, col):
    a = math.radians(ang)
    tip = (cx + length * math.cos(a), cy + length * math.sin(a))
    base = (cx + (length - r * 1.2) * math.cos(a), cy + (length - r * 1.2) * math.sin(a))
    n = (-math.sin(a) * r, math.cos(a) * r)
    m = c.poly([(cx, cy), (base[0] + n[0], base[1] + n[1]), (tip[0], tip[1]), (base[0] - n[0], base[1] - n[1])])
    m |= c.ellipse(base[0], base[1], r, r)
    return c.paint(m, col)


def _risol(c):
    c.panel("front", (20.0, 30.0))
    c.paint(c.full(), c.vgrad(16.5, 9.5, "#1f9a3e", "#5c1a6c"))
    c.paint(c.ellipse(8.5, 20.5, 7.5, 6.5), c.rgrad(8.5, 21.0, 7.5, "#f3fbf1", "#36a74c"), 0.85)
    for ang, ln, r, col in ((105, 7.0, 0.9, "#1866c9"), (40, 6.2, 0.8, "#2ea8f0"), (165, 6.0, 0.75, "#8cc63f"),
                            (215, 5.0, 0.6, "#1866c9"), (75, 5.4, 0.55, "#ffffff"), (135, 4.8, 0.5, "#2ea8f0")):
        _drop(c, 7.2, 20.8, ang, ln, r, col)
    for dx, dy, r in ((2.2, 26.0, 0.35), (12.0, 27.0, 0.3), (1.4, 22.5, 0.28), (12.6, 24.5, 0.4)):
        c.paint(c.ellipse(dx, dy, r, r), "#2ea8f0")
    c.outlined(c.text("Risol", 9.9, 17.6, 5.2, "ariblk.ttf", max_w=17.0), "#ffe100",
               [("#ffffff", 0.22), ("#064d1f", 0.42)])
    c.outlined(c.text("Anti Noda", 13.4, 13.6, 1.4, "arialbi.ttf", max_w=7.5), "#e2231a", [("#ffffff", 0.18)])
    c.paint(c.text("+", 6.9, 11.3, 1.8, "ariblk.ttf"), "#cfa6e0")
    c.paint(c.text("Molti", 12.0, 11.3, 1.7, "SCRIPTBL.TTF", max_w=6.5), "#ffffff")
    for k in range(6):
        a = k * math.pi / 3
        c.paint(c.ellipse(13.0 + 1.6 * math.cos(a), 4.8 + 1.6 * math.sin(a), 1.7, 1.1, math.degrees(a)), "#b3418f", 0.9)
    c.paint(c.ellipse(13.0, 4.8, 1.1, 1.1), "#e07ac0")
    c.paint(c.ellipse(13.0, 5.0, 0.55, 0.75), "#f2a30f")
    c.outlined(c.ellipse(16.8, 26.2, 1.6, 1.6), "#ffffff", [("#1866c9", 0.12)])
    c.paint(c.text("1X", 16.8, 26.5, 0.9, "ariblk.ttf"), "#e2231a")
    c.paint(c.text("KUCEK", 16.8, 25.5, 0.45, "arialbd.ttf", max_w=2.4), "#1866c9")
    for x0, x1 in ((0, 0.7), (19.3, 20)):
        c.paint(c.rect(x0, 0, x1, 30), "#000000", 0.18)
    _crimp(c, 28.6, 30.0, 0, 20, "#1b8a37", "#126b29")
    c.paint(c.rect(0, 0, 20, 1.2), "#3e0f4a")
    c.protect(1.0, 14.6, 19.0, 21.0)


def _sprit_face(c, big):
    c.paint(c.full(), c.vgrad(9.0, 0.0, "#0a9a48", "#00753a"))
    c.paint(c.rect(0, 8.3, 14.3, 9.0), "#005e2c")
    c.paint(c.rect(0, 0, 14.3, 0.7), "#005e2c")
    c.paint(c.rect(0, 8.15, 14.3, 8.3), "#c6e21a")
    c.paint(c.poly([(0, 2.0), (14.3, 5.2), (14.3, 6.2), (0, 3.0)]), "#2fbf63", 0.35)
    h = 3.4 if big else 2.4
    word = c.text("Sprit", 7.15, 5.0, h, "ariblk.ttf", max_w=11.8 if big else 8.5, shear=0.2)
    c.paint(c.shift(c.grow(word, 0.06), 0.12, -0.14), "#004d22")
    c.paint(word, "#ffffff")
    c.paint(c.text("DENGAN LEMON-LIME", 7.15, 2.45, 0.42, "arialbd.ttf", max_w=6.0), "#ffd400")


def _sprit(c):
    c.panel("front", (14.3, 9.0))
    _sprit_face(c, True)
    c.protect(0.8, 2.8, 13.5, 7.3)
    c.panel("back", (14.3, 9.0))
    _sprit_face(c, False)
    c.paint(c.rect(10.6, 1.4, 13.6, 3.6), "#ffffff")
    for k in range(20):
        c.paint(c.rect(10.8 + k * 0.13, 1.7, 10.8 + k * 0.13 + (0.05 if k % 3 else 0.09), 3.4), "#111111")
    for k in range(6):
        c.paint(c.rect(0.7, 6.6 - k * 0.5, 3.0, 6.75 - k * 0.5), "#e6f4ea", 0.8)
    c.protect(2.5, 3.6, 11.8, 6.4)


def _gg_border(c, w, h):
    for inset, lw in ((0.2, 0.06), (0.32, 0.03)):
        m = c.rect(inset, inset, w - inset, h - inset) & ~c.rect(inset + lw, inset + lw, w - inset - lw, h - inset - lw)
        c.paint(m, "#d9b35e")


def _gg_red(c, w, h):
    c.paint(c.full(), c.vgrad(h, 0, "#ad1a25", "#8c0f1a"))
    x = 0.0
    while x < w:
        c.paint(c.rect(x, 0, x + 0.04, h), "#6e0a13", 0.35)
        x += 0.12


def _gudang_gula(c):
    c.panel("front", (5.5, 8.8))
    _gg_red(c, 5.5, 8.8)
    _gg_border(c, 5.5, 8.8)
    c.paint(c.text("FILTER", 2.75, 8.0, 0.2, "timesbd.ttf", spacing=1.6), "#d9b35e")
    c.paint(c.rect(0.9, 7.5, 4.6, 7.55), "#d9b35e")
    # emblem: gold frame, dark green field, white warehouse with arches
    c.paint(c.rect(1.4, 4.85, 4.1, 6.65), "#e2c06a")
    c.paint(c.rect(1.55, 5.0, 3.95, 6.5), "#1d4a45")
    c.paint(c.poly([(1.75, 5.15), (3.75, 5.15), (3.75, 5.85), (2.75, 6.35), (1.75, 5.85)]), "#f1ead6")
    for k in range(5):
        ax = 1.97 + k * 0.39
        c.paint(c.rect(ax - 0.11, 5.15, ax + 0.11, 5.55) | c.ellipse(ax, 5.55, 0.11, 0.11), "#1d4a45")
    c.paint(c.stroke([(1.6, 5.88), (2.75, 6.42), (3.9, 5.88)], 0.07), "#e2c06a")
    c.paint(c.text("GUDANG", 2.75, 4.25, 0.34, "timesbd.ttf", max_w=3.4, spacing=1.4), "#e7cd8a")
    c.paint(c.text("GULA", 2.75, 3.4, 0.85, "timesbd.ttf", max_w=4.3), "#f2dfa8")
    c.paint(c.text("International", 2.75, 2.45, 0.55, "MTCORSVA.TTF", max_w=3.6), "#e2c06a")
    c.paint(c.text("MADE IN INDONESIA", 2.75, 0.8, 0.16, "arialbd.ttf", spacing=1.5), "#d9b35e")
    c.protect(0.9, 2.0, 4.6, 6.8)
    for side in ("side_l", "side_r"):
        c.panel(side, (2.2, 8.8))
        _gg_red(c, 2.2, 8.8)
        _gg_border(c, 2.2, 8.8)
        c.paint(c.text("GUDANG GULA", 1.1, 4.6, 0.55, "timesbd.ttf", max_w=6.6, rot=90), "#f2dfa8")


def _styrofoam(c, used=True):
    rng = np.random.default_rng(11)
    c.panel("front", (10.0, 10.0))   # inside: leftover rice, sambal, kecap and oil (used) or clean foam
    c.paint(c.full(), "#efece3")
    for _ in range(14):                                   # foam bead pattern
        c.paint(c.ellipse(rng.uniform(0, 10), rng.uniform(0, 10), 0.08, 0.08), "#d8d3c6", 0.6)
    if not used:
        c.panel("back", (10.0, 10.0))
        c.paint(c.full(), "#e9e6de")
        for _ in range(20):
            c.paint(c.ellipse(rng.uniform(0, 10), rng.uniform(0, 10), 0.08, 0.08), "#dedad0", 0.6)
        return
    for _ in range(7):                                    # grease yellowing
        x, y, r = rng.uniform(1, 9), rng.uniform(1, 9), rng.uniform(0.6, 1.8)
        c.paint(c.ellipse(x, y, r, r * rng.uniform(0.5, 1.0), rng.uniform(0, 180)), "#d9a42a", 0.22)
    for _ in range(2):                                    # sambal smears
        x, y, a = rng.uniform(2, 8), rng.uniform(2, 8), rng.uniform(0, 180)
        for k in range(6):
            r = rng.uniform(0.15, 0.4)
            c.paint(c.ellipse(x + k * 0.3 * math.cos(math.radians(a)), y + k * 0.3 * math.sin(math.radians(a)) + rng.uniform(-0.15, 0.15),
                              r, r * 0.6, a), "#b8391c", 0.35)
    for _ in range(2):                                    # kecap streak
        c.paint(c.ellipse(rng.uniform(2, 8), rng.uniform(2, 8), rng.uniform(0.8, 1.4), rng.uniform(0.12, 0.25), rng.uniform(0, 180)),
                "#4a2a14", 0.35)
    for _ in range(40):
        x, y, a = rng.uniform(0.5, 9.5), rng.uniform(0.5, 9.5), rng.uniform(0, 180)
        c.outlined(c.ellipse(x, y, 0.22, 0.09, a), "#fbfaf5", [("#b9b2a2", 0.02)])
    c.panel("back", (10.0, 10.0))     # outside: grubby white, a crack
    c.paint(c.full(), "#eeebe4")
    c.paint(c.stroke([(6.0, 10.0), (6.4, 8.6), (5.8, 7.5), (6.5, 6.1), (6.2, 5.2)], 0.07), "#4f4636")
    c.paint(c.stroke([(6.4, 8.6), (7.3, 8.1)], 0.05), "#4f4636")


def _aquo_face(c, w, h, big):
    """Parody mineral-water wrap: pale blue sky, two blue hill bands, white-outlined blue AQUO, top/bottom bars."""
    c.paint(c.full(), c.vgrad(h, 0, "#eef7fc", "#bfe0f2"))
    c.paint(c.poly([(0, 0), (0, h * 0.36), (w * 0.22, h * 0.6), (w * 0.4, h * 0.42), (w * 0.62, h * 0.68),
                    (w * 0.82, h * 0.46), (w, h * 0.56), (w, 0)]), "#8cc0ea")
    c.paint(c.poly([(0, 0), (0, h * 0.24), (w * 0.3, h * 0.4), (w * 0.55, h * 0.26), (w * 0.76, h * 0.42),
                    (w, h * 0.3), (w, 0)]), "#2f7fd0")
    c.paint(c.rect(0, h * 0.88, w, h), "#1f5fd6")
    c.paint(c.rect(0, 0, w, h * 0.07), "#1f5fd6")
    c.paint(c.rect(0, h * 0.86, w, h * 0.88), "#e2231a")
    word = c.text("AQUO", w / 2, h * 0.62, h * (0.36 if big else 0.26), "ariblk.ttf", max_w=w * (0.62 if big else 0.4), shear=0.1)
    c.outlined(word, "#1f5fd6", [("#ffffff", h * 0.035)])
    c.paint(c.text("AIR MINERAL", w / 2, h * 0.3, h * 0.085, "arialbd.ttf", max_w=w * 0.5), "#ffffff")


def _aquo(c, units):
    w, h = units
    c.panel("front", units)
    _aquo_face(c, w, h, True)
    c.protect(w * 0.15, h * 0.4, w * 0.85, h * 0.85)
    c.panel("back", units)
    _aquo_face(c, w, h, False)


ARTS = {
    "indomy": (_indomy, "pack", "film"),
    "bingo": (_bingo, "pack", "film"),
    "moli": (_moli, "pack", "film"),
    "lifeman": (_lifeman, "pair", "bottle"),
    "sari_boti": (_sari_boti, "pack", "film"),
    "risol": (_risol, "pack", "film"),
    "sprit": (_sprit, "wrap", "bottle"),
    "gudang_gula": (_gudang_gula, "box", "carton"),
    "styrofoam": (_styrofoam, "pair", "foam"),
    "aquo": (lambda c: _aquo(c, (10.0, 5.0)), "wrap", "bottle"),             # 600 ml bottle band (parody brand)
    "aquo_galon": (lambda c: _aquo(c, (42.0, 10.0)), "wrap", "bottle"),      # 19 L jug sticker band
    # clean product variants (render with dirty=False): bread in the window, unused foam
    "sari_boti_full": (lambda c: _sari_boti(c, full=True), "pack", "film"),
    "styrofoam_new": (lambda c: _styrofoam(c, used=False), "pair", "foam"),
}


def render_label(name, w, h, dirty=True):
    """Paint label `name` at w x h pixels. Returns {"albedo", "normal", "smooth"} (row 0 = bottom)."""
    draw, layout, kind = ARTS[name]
    c = Canvas(w, h, layout)
    try:
        draw(c)
    finally:
        _release_fonts()
    rgb = c.result()
    if not dirty:
        nrm = np.zeros((h, w, 3), np.float32)
        nrm[...] = (0.5, 0.5, 1.0)
        return {"albedo": rgb, "normal": nrm, "smooth": np.full((h, w), WEAR[kind]["smooth"], np.float32)}
    rng = np.random.default_rng(zlib.crc32(name.encode()))
    rgb, nrm, smooth = wear(rgb, kind, rng, c.panel_px, c.protect_px)
    return {"albedo": rgb, "normal": nrm, "smooth": smooth}
