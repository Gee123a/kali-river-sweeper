"""SM_Env_DropOffB3 (Wesley, plan Step 6C / playtest P2-7) - B3 drop-off kiosk next to Dermaga Tengah.

Playtest: the 60 s reward gaps come from long sorting trips to Pos Medis / Karantina. This small kiosk on
the bank by the middle dock gives Medical and Biohazard waste a closer home (Ivan wires the gameplay).
Unity coordinates, pivot = ground centre of the pad, FRONT = -X (the builder turns it to face the river):
  concrete pad, galvanised seng canopy on 4 steel posts, "DROP-OFF B3 [E]" hazard-striped header board,
  a yellow "LIMBAH MEDIS B3" bin with a needle slot (z < 0) and a purple "BIOHAZARD" locker with hazard
  band and padlock (z > 0). Every label reads from the front; the header reads from both sides.
DROP_SPOTS (local) are where Ivan's two triggers go (in front of each bin).
"""
from wesley_env import papan_mesh as pm
from wesley_env.meshkit import MeshKit

FBX_NAME = "SM_Env_DropOffB3"
NAME = "SM_Env_DropOffB3"
TRI_BUDGET = (100, 900)

SEMEN, BESI, SENG, PAPAN = range(4)
MATERIALS = (
    ("M_Env_TaludBeton", (0.62, 0.62, 0.60, 1.0)),
    ("M_Env_BesiGelap", (0.16, 0.17, 0.18, 1.0)),
    ("M_Env_SengGalvanis", (0.70, 0.72, 0.74, 1.0)),
    ("M_Env_PapanDropOff", (0.93, 0.93, 0.93, 1.0)),
)

R = {k: pm.px(*v) for k, v in {
    "header": (0, 0, 1024, 200), "medis": (0, 224, 512, 736), "bio": (512, 224, 1024, 736),
    "kuning": (0, 760, 256, 880), "ungu": (256, 760, 512, 880), "hazard": (512, 760, 1024, 880),
    "slot": (0, 904, 256, 1024), "putih": (256, 904, 512, 1024),
}.items()}

PAD_TOP = 0.12
DROP_SPOTS = {"Medis": (-1.6, 0.0, -0.72), "Biohazard": (-1.6, 0.0, 0.72)}


def solid(k, x0, x1, y0, y1, z0, z1, swatch):
    s = len(k.faces)
    k.box(x0, x1, y0, y1, z0, z1, PAPAN)
    pm.flat(k, s, R[swatch])


def kiosk():
    k = MeshKit(uv_tile=1.0)
    k.box(-1.3, 1.3, -0.15, PAD_TOP, -1.65, 1.65, SEMEN)                         # pad
    for x, h in ((-1.15, 2.62), (1.15, 2.36)):
        for z in (-1.48, 1.48):
            k.box(x - 0.04, x + 0.04, PAD_TOP, h, z - 0.04, z + 0.04, BESI)        # canopy posts
    k.box(-1.2, 1.2, 2.3, 2.38, -1.52, 1.52, BESI)                               # ring beam (back, low)
    pts = [(-1.5, 2.64, -1.8), (1.5, 2.36, -1.8), (1.5, 2.36, 1.8), (-1.5, 2.64, 1.8)]
    s = len(k.faces)
    k.hexa(pts + [(x, y + 0.04, z) for x, y, z in pts], SENG)                     # seng roof, falls to the back
    pm.swap_uv(k, s)
    # header board under the front eave, readable from both sides
    s = len(k.faces)
    pm.board(k, -1.22, -1.17, 2.02, 2.5, -1.35, 1.35, PAPAN, "-x", R["header"], R["slot"])
    u0, v0, u1, v1 = R["header"]
    k.uvs[s + pm.FACE["+x"]] = [(u1, v0), (u0, v0), (u0, v1), (u1, v1)]
    # yellow medical bin: feet, body with label, lid, needle slot
    for z in (-1.15, -0.3):
        solid(k, -0.35, 0.35, PAD_TOP, PAD_TOP + 0.08, z - 0.05, z + 0.05, "slot")
    pm.board(k, -0.4, 0.4, PAD_TOP + 0.08, 1.1, -1.25, -0.2, PAPAN, "-x", R["medis"], R["kuning"])
    solid(k, -0.45, 0.45, 1.1, 1.18, -1.3, -0.15, "kuning")
    solid(k, -0.46, -0.3, 1.12, 1.19, -0.95, -0.5, "slot")
    # purple biohazard locker: hazard band, label, lid, padlock
    s = len(k.faces)
    k.box(-0.42, 0.42, PAD_TOP, PAD_TOP + 0.16, 0.18, 1.27, PAPAN)
    pm.stretch(k, s, R["hazard"])
    pm.board(k, -0.4, 0.4, PAD_TOP + 0.16, 1.26, 0.2, 1.25, PAPAN, "-x", R["bio"], R["ungu"])
    solid(k, -0.43, 0.43, 1.26, 1.32, 0.17, 1.28, "ungu")
    k.box(-0.47, -0.41, 0.95, 1.07, 0.67, 0.77, BESI)                              # padlock hasp
    return k


def build():
    return kiosk().build(NAME, MATERIALS)


def stats(ob):
    tris = sum(len(p.vertices) - 2 for p in ob.data.polygons)
    lo, hi = TRI_BUDGET
    return {"name": FBX_NAME, "tris": tris, "in_budget": lo <= tris <= hi, "drop_spots": DROP_SPOTS}
