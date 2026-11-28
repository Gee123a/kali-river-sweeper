"""SM_Env_TandaLayanan (Wesley) - service-point marks, Core Mechanics v2 spec A (docs/MECHANICS_SPEC.md).

Ivan's MapJsonImporter puts a 2 m trigger `<Station>_ServicePoint` in front of each counter; these
pieces show players where to stand. Unity coordinates, pivot = service-point centre on the ground,
local +X = toward the counter (EnvServicePointMarks aims it):
  SM_Env_TandaLantai              4.4 m painted floor decal (dashed ring on the 2.0 m radius,
                                  "BERDIRI DI SINI", [E] keycap, shoe prints). One quad, white
                                  worn paint (T_Env_TandaLantai); Unity tints it per station.
  SM_Env_PapanLayanan_<Station>   low post sign beside the ring (+Z side) facing the path (-X):
                                  station name + "[E] action" (T_Env_PapanLayanan row).
Signs read from both sides (the back face mirrors U).
"""
from wesley_env import papan_mesh as pm
from wesley_env.meshkit import MeshKit

FBX_NAME = "SM_Env_TandaLayanan"
NAME = "SM_Env_TandaLantai"
TRI_BUDGET = (2, 200)

TANDA, TIANG, PAPAN = range(3)
MATERIALS = (
    ("M_Env_TandaLantai", (1.0, 1.0, 1.0, 1.0)),
    ("M_Env_KayuTiang", (0.46, 0.31, 0.20, 1.0)),
    ("M_Env_PapanLayanan", (0.93, 0.93, 0.93, 1.0)),
)

STATIONS = ("BankSampah", "Kopdes", "Pengepul", "PosMedis", "Karantina")   # papan.LAYANAN_ROWS order
ROWS = {k: pm.px(0, i * 192, 1024, i * 192 + 176) for i, k in enumerate(STATIONS)}
EDGE = pm.px(0, 960, 256, 1024)

DECAL_HALF = 2.2
DECAL_Y = 0.03
SIGN_Z = 2.65          # beside the ring, clear of the 2.0 m trigger
SIGN_W, SIGN_H, SIGN_Y = 1.6, 0.275, 1.0


def lantai():
    k = MeshKit(uv_tile=1.0)
    h = DECAL_HALF
    # viewer stands in the ring facing +X (the counter): texture top at +X, texture right at -Z
    k._face([(-h, DECAL_Y, h), (-h, DECAL_Y, -h), (h, DECAL_Y, -h), (h, DECAL_Y, h)], TANDA, [])
    k.uvs[-1] = [(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0)]
    return k


def papan(key):
    k = MeshKit(uv_tile=1.0)
    z0, z1 = SIGN_Z - SIGN_W / 2, SIGN_Z + SIGN_W / 2
    for z in (z0 + 0.12, z1 - 0.12):
        k.box(0.03, 0.1, -0.25, SIGN_Y + SIGN_H + 0.06, z - 0.035, z + 0.035, TIANG)
    s = len(k.faces)
    pm.board(k, -0.02, 0.03, SIGN_Y, SIGN_Y + SIGN_H, z0, z1, PAPAN, "-x", ROWS[key], EDGE)
    u0, v0, u1, v1 = ROWS[key]
    k.uvs[s + pm.FACE["+x"]] = [(u1, v0), (u0, v0), (u0, v1), (u1, v1)]
    return k


PIECES = {"SM_Env_TandaLantai": lantai}
PIECES.update({f"SM_Env_PapanLayanan_{key}": (lambda key=key: papan(key)) for key in STATIONS})


def build():
    return [fn().build(name, MATERIALS) for name, fn in PIECES.items()]


def stats(obs):
    tris = {ob.name: sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in obs}
    lo, hi = TRI_BUDGET
    return {"name": FBX_NAME, "tris": tris, "in_budget": all(lo <= t <= hi for t in tris.values())}
