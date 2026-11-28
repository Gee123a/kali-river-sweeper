"""Solar river interceptor (5A, map type "interceptor"): 6.4 m catamaran barge on two pontoons, deck with safety-
yellow rails, inclined conveyor belt with cleats rising from the water at the bow, orange collection bin at the
stern, control cabinet, two guide-boom floats funnelling trash to the belt, and a canopy of solar panels on four
posts (cells + PENCEGAT SAMPAH hull sign painted procedurally, labels.py "solar_interceptor").

Origin = WATERLINE (centred, y = 0): the importer places water items at the river surface.
"""
import bpy  # must be first
import math
from mathutils import Matrix
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 16,
    "name": "SM_Prop_SolarInterceptor",
    "prefab": "PF_Prop_SolarInterceptor",
    "label": "Floating solar trash interceptor: pontoons, conveyor, bin, solar canopy",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "waterline",
    "tris": (1200, 3000),
    "max_size": 9.0,
    "label_art": {"name": "solar_interceptor", "rows": 2},
    "palette": [
        ("#2b3440", 0.3, 0.45),  # 0 dark hull / pontoons
        ("#f5c518", 0.1, 0.5),   # 1 safety yellow rails / frame
        ("#1a1a1a", 0.0, 0.3),   # 2 black conveyor belt
        ("#e8651d", 0.1, 0.45),  # 3 orange collection bin / boom floats
        ("#9aa0a6", 0.7, 0.45),  # 4 galvanised deck plate
        ("#d6d9dc", 0.2, 0.5),   # 5 white cabinet / canopy frame
        ("#38bdf8", 0.0, 0.8, True),  # 6 status light (emissive)
    ],
}

L, B = 6.4, 3.0              # length (x, bow at -x) and beam
DECK = 0.55                  # deck top above the waterline
POST_H = 2.5


def _panel_uv(s, t):
    return ts.panel_uv("pair", "front", s, t)


def _sign_uv(s, t):
    return ts.panel_uv("pair", "back", s, t)


def build():
    geo = ts.Geo()
    # pontoons (half submerged) along x
    for y in (-1.15, 1.15):
        geo.xform = Matrix.Translation((0, y, 0.0)) @ Matrix.Rotation(math.radians(90), 4, "Y")
        ts.lathe(geo, [(-3.2, 0.12, 0.12), (-3.05, 0.32, 0.30), (-2.7, 0.42, 0.40), (2.8, 0.42, 0.40),
                       (3.1, 0.36, 0.34), (3.2, 0.2, 0.2)], 16, lambda r: 0, cap0=0, cap1=0)
    geo.xform = None
    # deck + hull sign boards on both sides
    ts.box(geo, 4, (-2.6, -1.45, DECK - 0.12), (3.0, 1.45, DECK), n=(4, 2, 1))
    ts.grid(geo, "label", (-1.0, -1.46, DECK - 0.12), (3.6, 0, 0), (0, 0, 0.42), 1, 1, _sign_uv)
    ts.grid(geo, "label", (2.6, 1.46, DECK - 0.12), (-3.6, 0, 0), (0, 0, 0.42), 1, 1, _sign_uv)
    for x in (-2.0, 0.0, 2.0):                                          # cross beams between the pontoons
        ts.box(geo, 0, (x - 0.08, -1.2, 0.25), (x + 0.08, 1.2, DECK - 0.12))
    # conveyor: frame rails, belt, cleats, head roller - rising from the water at the bow
    pitch = math.atan2(DECK + 0.9, 2.6)
    geo.xform = Matrix.Translation((-3.3, 0, -0.35)) @ Matrix.Rotation(-pitch, 4, "Y")
    run = math.hypot(2.6, DECK + 0.9)
    for y in (-0.62, 0.62):
        ts.box(geo, 1, (0.0, y - 0.05, -0.06), (run, y + 0.05, 0.10))
    ts.grid(geo, 2, (0.0, -0.55, 0.06), (run, 0, 0), (0, 1.1, 0), 6, 1)
    for k in range(9):
        x = 0.15 + k * (run - 0.3) / 8
        ts.box(geo, 2, (x, -0.55, 0.06), (x + 0.035, 0.55, 0.13))
    geo.xform = Matrix.Translation((-3.3, 0, -0.35)) @ Matrix.Rotation(-pitch, 4, "Y") @ Matrix.Translation((run, 0, 0.02)) \
        @ Matrix.Rotation(math.radians(90), 4, "X")
    ts.lathe(geo, [(-0.6, 0.09, 0.09), (0.6, 0.09, 0.09)], 8, lambda r: 4, cap0=4, cap1=4)
    geo.xform = None
    # collection bin (open top, orange) and control cabinet with status light
    ts.box(geo, 3, (0.4, -1.0, DECK), (2.4, -0.98, DECK + 0.9))
    ts.box(geo, 3, (0.4, 0.98, DECK), (2.4, 1.0, DECK + 0.9))
    ts.box(geo, 3, (0.4, -1.0, DECK), (0.42, 1.0, DECK + 0.9))
    ts.box(geo, 3, (2.38, -1.0, DECK), (2.4, 1.0, DECK + 0.9))
    ts.box(geo, 5, (2.55, 0.55, DECK), (2.95, 1.3, DECK + 1.2))
    geo.xform = Matrix.Translation((2.75, 0.92, DECK + 1.2))
    ts.lathe(geo, [(0.0, 0.06, 0.06), (0.1, 0.05, 0.05)], 6, lambda r: 6, cap1=6)
    geo.xform = None
    # railings along both sides
    for y in (-1.42, 1.42):
        for x in (-2.5, -1.1, 0.3, 1.7, 2.9):
            ts.box(geo, 1, (x - 0.03, y - 0.03, DECK), (x + 0.03, y + 0.03, DECK + 0.9))
        ts.box(geo, 1, (-2.5, y - 0.03, DECK + 0.86), (2.9, y + 0.03, DECK + 0.92))
        ts.box(geo, 1, (-2.5, y - 0.025, DECK + 0.45), (2.9, y + 0.025, DECK + 0.5))
    # solar canopy: posts, frame, 2 x 4 panels (cells painted)
    for x in (-2.0, 1.8):
        for y in (-1.2, 1.2):
            geo.xform = Matrix.Translation((x, y, DECK))
            ts.lathe(geo, [(0.0, 0.05, 0.05), (POST_H, 0.05, 0.05)], 6, lambda r: 5)
    geo.xform = None
    ts.box(geo, 5, (-2.25, -1.45, DECK + POST_H), (2.05, 1.45, DECK + POST_H + 0.08))
    tilt = Matrix.Translation((0, 0, DECK + POST_H + 0.08)) @ Matrix.Rotation(math.radians(6), 4, "X")
    for i in range(4):
        for j in range(2):
            x0, y0 = -2.2 + i * 1.07, -1.4 + j * 1.42
            geo.xform = tilt
            ts.box(geo, 5, (x0, y0, 0.0), (x0 + 1.03, y0 + 1.38, 0.04))
            ts.grid(geo, "label", (x0 + 0.03, y0 + 0.03, 0.045), (0.97, 0, 0), (0, 1.32, 0), 1, 1, _panel_uv)
    geo.xform = None
    # guide booms: orange floats angled out ahead of the bow, funnelling trash to the belt
    for s in (-1, 1):
        geo.xform = Matrix.Translation((-3.2, s * 0.75, 0.0)) @ Matrix.Rotation(s * math.radians(-28), 4, "Z") \
            @ Matrix.Rotation(math.radians(-90), 4, "Y")
        ts.lathe(geo, [(0.0, 0.08, 0.08), (0.1, 0.13, 0.13), (2.2, 0.13, 0.13), (2.3, 0.08, 0.08)], 8, lambda r: 3,
                 cap0=3, cap1=3)
    geo.xform = None
    # working details: trash heap in the bin, bollards, stern ladder, canopy braces, lifebuoy, antenna mast
    geo.xform = Matrix.Translation((1.4, 0.0, DECK + 0.05)) @ Matrix.Scale(1.0, 4)
    ts.lathe(geo, [(0.0, 0.95, 0.9), (0.25, 0.85, 0.8), (0.45, 0.55, 0.5), (0.6, 0.2, 0.2)], 12,
             lambda r: (3, 2, 4)[r % 3], cap1=4)
    geo.xform = None
    for x, y in ((-2.45, -1.3), (-2.45, 1.3), (2.85, -1.3), (2.85, 1.3)):
        geo.xform = Matrix.Translation((x, y, DECK))
        ts.lathe(geo, [(0.0, 0.07, 0.07), (0.12, 0.06, 0.06), (0.16, 0.085, 0.085), (0.19, 0.085, 0.085)], 8,
                 lambda r: 0, cap1=0)
    geo.xform = None
    for y in (-0.25, 0.25):                                              # stern ladder rails + rungs
        ts.box(geo, 1, (3.02, y - 0.025, -0.3), (3.07, y + 0.025, DECK + 0.6))
    for k in range(5):
        z = -0.15 + k * 0.22
        ts.box(geo, 1, (3.02, -0.25, z), (3.07, 0.25, z + 0.04))
    for y in (-1.2, 1.2):                                                # canopy cross braces
        ts.box(geo, 5, (-2.0, y - 0.03, DECK + 1.3), (1.8, y + 0.03, DECK + 1.36))
    geo.xform = Matrix.Translation((0.3, -1.47, DECK + 0.6)) @ Matrix.Rotation(math.radians(90), 4, "X")
    ts.torus(geo, 3, 0.22, 0.05, 12, 4)                                  # lifebuoy on the rail
    geo.xform = Matrix.Translation((2.75, 1.15, DECK + 1.2))
    ts.lathe(geo, [(0.1, 0.02, 0.02), (1.4, 0.012, 0.012)], 6, lambda r: 5, cap1=5)   # antenna mast
    geo.xform = None
    geo.recentre(keep_z=True)
    return geo.objects(SPEC["name"])
