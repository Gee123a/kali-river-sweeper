"""Truk sampah (R3-J1 / plan_jc Task 7C): low-poly Indonesian three-wheel cargo motorbike (motor roda tiga) set up as
a kampung trash pickup, ~3.1 m long: single front wheel with fork and fender, headlight, handlebar, fuel tank and
seat on a red body, engine and exhaust, a sun canopy over the rider, steel ladder frame, and an open rear cargo bed
with green steel sides on two rear wheels, tail lights and mudguards. No rig, no physics, no wheel animation.

Origin = ground centre (base pivot, bbox centre in x/z, wheels on y = 0); forward = Unity +Z (Blender -Y).
Socket_Load: KaliPropPrefabBuilder adds an empty child "Socket_Load" at SOCKET_LOAD_UNITY (bed floor, centre) for
the trash heap. build() asserts the constant still matches the geometry, so the C# value cannot drift silently.
"""
import bpy  # must be first
import math
from mathutils import Matrix, Vector
from kali_blender import trash_shapes as ts

SPEC = {
    "index": 19,
    "name": "SM_Prop_TrukSampah",
    "prefab": "PF_Prop_TrukSampah",
    "label": "Three-wheel cargo motorbike trash pickup (motor roda tiga)",
    "head_dir": "-Z",  # not used; tools_common.assemble requires the key
    "pivot": "base",
    "tris": (800, 1500),
    "max_size": 3.5,
    "palette": [
        ("#c0392b", 0.2, 0.5),   # 0 red body / tank / fender
        ("#1c1c1c", 0.0, 0.35),  # 1 tyres, seat, handle grips
        ("#9aa0a6", 0.8, 0.5),   # 2 chrome / steel (fork, exhaust, hubs)
        ("#2f6b3a", 0.2, 0.45),  # 3 green steel cargo bed
        ("#3a3d42", 0.4, 0.45),  # 4 dark chassis / engine
        ("#f5f3d8", 0.0, 0.9),   # 5 headlight lens
        ("#e11d2a", 0.0, 0.8),   # 6 tail lights
        ("#d6d9dc", 0.1, 0.5),   # 7 canopy roof
        ("#7a5a3a", 0.0, 0.3),   # 8 wooden bed floor
    ],
}

FRONT_Y, REAR_Y = -1.25, 0.85          # wheel axles (Blender y; -Y is forward)
R_FRONT, R_REAR = 0.27, 0.29
BED = (-0.70, 0.75, 0.05, 1.50, 0.62)  # half width, ... y0, y1, floor top z
SOCKET_LOAD_UNITY = (0.0, 0.62, -0.76)  # PF_Prop_TrukSampah/Socket_Load local position (x, y, z) in Unity


def _wheel(geo, x, y, r, width):
    geo.xform = Matrix.Translation((x, y, r)) @ Matrix.Rotation(math.radians(90), 4, "Y")
    ts.lathe(geo, [(-width, r * 0.62, r * 0.62), (-width, r * 0.86, r * 0.86), (-width * 0.6, r, r), (width * 0.6, r, r),
                   (width, r * 0.86, r * 0.86), (width, r * 0.62, r * 0.62)], 12, lambda k: 1 if 0 < k < 4 else 2,
             cap0=2, cap1=2)
    geo.xform = None


def build():
    geo = ts.Geo()
    _wheel(geo, 0.0, FRONT_Y, R_FRONT, 0.06)
    for sx in (-1, 1):
        _wheel(geo, sx * 0.62, REAR_Y, R_REAR, 0.07)
    # front fork, fender, headlight, handlebar
    for sx in (-1, 1):
        a, b = Vector((sx * 0.07, FRONT_Y, R_FRONT)), Vector((sx * 0.07, FRONT_Y + 0.28, 1.0))
        d = b - a
        geo.xform = Matrix.Translation(a) @ Vector((0, 0, 1)).rotation_difference(d.normalized()).to_matrix().to_4x4()
        ts.lathe(geo, [(0.0, 0.022, 0.022), (d.length, 0.022, 0.022)], 6, lambda k: 2)
    geo.xform = None
    ts.box(geo, 0, (-0.09, FRONT_Y - 0.22, R_FRONT + 0.27), (0.09, FRONT_Y + 0.2, R_FRONT + 0.31))
    geo.xform = Matrix.Translation((0, FRONT_Y + 0.22, 0.92)) @ Matrix.Rotation(math.radians(90), 4, "X")
    ts.lathe(geo, [(0.0, 0.08, 0.08), (0.06, 0.09, 0.09), (0.09, 0.07, 0.07)], 10, lambda k: 0, cap0=5, cap1=0)
    geo.xform = Matrix.Translation((0, FRONT_Y + 0.32, 1.06)) @ Matrix.Rotation(math.radians(90), 4, "Y")
    ts.lathe(geo, [(-0.34, 0.016, 0.016), (-0.26, 0.018, 0.018), (-0.20, 0.014, 0.014), (0.20, 0.014, 0.014),
                   (0.26, 0.018, 0.018), (0.34, 0.016, 0.016)], 6, lambda k: 1 if k in (0, 4) else 2, cap0=1, cap1=1)
    geo.xform = None
    # body: fuel tank, seat, engine, exhaust, frame
    ts.box(geo, 0, (-0.16, FRONT_Y + 0.42, 0.68), (0.16, FRONT_Y + 0.92, 0.92), n=(2, 2, 1))
    ts.box(geo, 1, (-0.18, FRONT_Y + 0.92, 0.78), (0.18, FRONT_Y + 1.42, 0.88), n=(2, 2, 1))
    ts.box(geo, 4, (-0.18, FRONT_Y + 0.62, 0.30), (0.18, FRONT_Y + 1.12, 0.62), n=(1, 2, 1))
    geo.xform = Matrix.Translation((0.2, FRONT_Y + 0.9, 0.34)) @ Matrix.Rotation(math.radians(-90), 4, "X")
    ts.lathe(geo, [(0.0, 0.035, 0.035), (0.9, 0.035, 0.035), (0.95, 0.045, 0.045)], 8, lambda k: 2, cap1=4)
    geo.xform = None
    for sx in (-1, 1):
        ts.box(geo, 4, (sx * 0.5 - 0.03, BED[2] - 0.6, 0.38), (sx * 0.5 + 0.03, BED[3], 0.46))
    ts.box(geo, 4, (-0.06, FRONT_Y + 0.3, 0.38), (0.06, BED[2], 0.46))
    # sun canopy over the rider: 4 posts + roof
    for x, y in ((-0.25, FRONT_Y + 0.55), (0.25, FRONT_Y + 0.55), (-0.25, FRONT_Y + 1.5), (0.25, FRONT_Y + 1.5)):
        geo.xform = Matrix.Translation((x, y, 0.85))
        ts.lathe(geo, [(0.0, 0.018, 0.018), (0.95, 0.018, 0.018)], 6, lambda k: 4)
    geo.xform = None
    ts.box(geo, 7, (-0.36, FRONT_Y + 0.45, 1.8), (0.36, FRONT_Y + 1.62, 1.86), n=(2, 2, 1))
    # open cargo bed: wooden floor, green steel sides with slats, tail lights, mudguards
    hw, y0, y1, ztop = BED[1], BED[2], BED[3], BED[4]
    ts.box(geo, 8, (-hw, y0, ztop - 0.06), (hw, y1, ztop), n=(3, 3, 1))
    for sx in (-1, 1):
        ts.box(geo, 3, (sx * hw - 0.025, y0, ztop), (sx * hw + 0.025, y1, ztop + 0.45), n=(1, 3, 1))
    ts.box(geo, 3, (-hw, y0 - 0.025, ztop), (hw, y0 + 0.025, ztop + 0.55))                      # bulkhead
    ts.box(geo, 3, (-hw, y1 - 0.025, ztop), (hw, y1 + 0.025, ztop + 0.40))                      # tailgate
    for sx in (-1, 1):
        for z in (ztop + 0.15, ztop + 0.30):
            ts.box(geo, 3, (sx * (hw + 0.025), y0 + 0.05, z), (sx * (hw + 0.045), y1 - 0.05, z + 0.03))
        ts.box(geo, 6, (sx * 0.55 - 0.07, y1 + 0.025, ztop - 0.02), (sx * 0.55 + 0.07, y1 + 0.05, ztop + 0.06))
        ts.box(geo, 0, (sx * 0.62 - 0.1, REAR_Y - 0.32, R_REAR + 0.3), (sx * 0.62 + 0.1, REAR_Y + 0.32, R_REAR + 0.33))
    # Socket_Load check (Blender -> Unity: x, z, -y), relative to the base-centre origin set by recentre
    used = sorted({i for _, f, _ in geo.faces for i in f})
    lo = Vector([min(geo.v[i][a] for i in used) for a in range(3)])
    hi = Vector([max(geo.v[i][a] for i in used) for a in range(3)])
    c = (lo + hi) / 2
    socket = Vector((0.0 - c.x, (y0 + y1) / 2 - c.y, ztop - lo.z))
    unity = (round(socket.x, 2), round(socket.z, 2), round(-socket.y, 2))
    assert unity == SOCKET_LOAD_UNITY, f"update SOCKET_LOAD_UNITY and KaliPropPrefabBuilder.TrukSocketLoad: {unity}"
    geo.recentre(base=True)
    return geo.objects(SPEC["name"])
