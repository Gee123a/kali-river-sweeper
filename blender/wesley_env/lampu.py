"""SM_Env_Lampu (Wesley) - kampung lamps that switch on at night (EnvNightLamp).

One FBX, three objects (pivot = mount point, the arm reaches toward +X):
  SM_Env_LampuJalan   wooden lamp post from Wesley's reference: stepped timber plinth, iron
                      collar, cross arm with a diagonal brace and an iron strap, a short chain
                      and a rusty caged hurricane lantern (second reference) with a warm glass.
                      Pivot = bottom centre; the lantern glass centre is LANTERN_GLOW.
  SM_Env_LampuBohlam  wall lamp for the buildings: iron wall plate, bent pipe arm, green enamel
                      shade and a bare bulb ("lampu bohlam kampung"). Pivot = wall plate centre
                      (wall face at X = 0, arm out along +X); bulb centre is BOHLAM_GLOW.
  SM_Env_LampuPool    1 x 1 m ground quad (UV 0..1) for the KaliLightPool additive glow.
"""
import math

from wesley_env.meshkit import MeshKit

FBX_NAME = "SM_Env_Lampu"
NAME = "SM_Env_LampuJalan"
BOHLAM = "SM_Env_LampuBohlam"
POOL = "SM_Env_LampuPool"
TRI_BUDGET = (200, 900)

KAYU, BESI, KARAT, KACA, ENAMEL = range(5)
MATERIALS = (
    ("M_Env_KayuTiang", (0.46, 0.31, 0.20, 1.0)),
    ("M_Env_BesiGelap", (0.16, 0.17, 0.18, 1.0)),
    ("M_Env_BesiKarat", (0.50, 0.27, 0.17, 1.0)),
    ("M_Env_LampuKaca", (1.00, 0.80, 0.50, 1.0)),
    ("M_Env_BesiTeal", (0.18, 0.45, 0.40, 1.0)),
)

POST_TOP, ARM_Y, ARM_X = 3.55, 3.2, 1.05      # cross arm top / lantern hang point
LANTERN_GLOW = (ARM_X, 2.265, 0.0)             # glass centre = light position in the prefab
BOHLAM_GLOW = (0.44, -0.19, 0.0)


def frustum(k, cx, cy0, cz, r0, cy1, r1, mat, seg=8, caps=True, rot=math.pi / 8):
    """Octagonal (seg-sided) frustum along Y: radius r0 at cy0, r1 at cy1."""
    ring = lambda y, r: [(cx + r * math.cos(rot + 2 * math.pi * i / seg), y, cz + r * math.sin(rot + 2 * math.pi * i / seg)) for i in range(seg)]
    a, b = ring(cy0, r0), ring(cy1, r1)
    for i in range(seg):
        j = (i + 1) % seg
        k._face([a[i], a[j], b[j], b[i]], mat, [(i * 0.3, cy0), ((i + 1) * 0.3, cy0), ((i + 1) * 0.3, cy1), (i * 0.3, cy1)])
    if caps:
        if r1 > 1e-4:
            k._face(list(reversed(b)), mat, [(p[0], p[2]) for p in reversed(b)])
        if r0 > 1e-4:
            k._face(a, mat, [(p[0], p[2]) for p in a])


def lantern(k, x, top, z):
    """Caged hurricane lantern hanging from (x, top, z); returns the glass centre."""
    k.box(x - 0.012, x + 0.012, top - 0.12, top, z - 0.012, z + 0.012, BESI)                 # hook
    frustum(k, x, top - 0.24, z, 0.075, top - 0.12, 0.03, KARAT)                            # top knob cone
    frustum(k, x, top - 0.30, z, 0.21, top - 0.24, 0.085, KARAT)                            # flared cap
    frustum(k, x, top - 0.33, z, 0.21, top - 0.30, 0.21, KARAT)                             # cap rim
    g0, g1 = top - 0.66, top - 0.33
    frustum(k, x, g0, z, 0.115, g1, 0.15, KACA)                                             # glowing glass
    frustum(k, x, g0 - 0.09, z, 0.07, g0, 0.12, KARAT)                                      # base cup
    for i in range(4):                                                                     # 4 cage bars
        a = math.pi / 4 + i * math.pi / 2
        c, s = math.cos(a), math.sin(a)
        k.beam((x + 0.135 * c, g0 - 0.03, z + 0.135 * s), (x + 0.185 * c, g1, z + 0.185 * s), 0.011, KARAT)
    for y, r in ((g0 + 0.09, 0.158), (g1 - 0.1, 0.178)):                                    # 2 cage rings
        for i in range(8):
            a0, a1 = math.pi / 8 + i * math.pi / 4, math.pi / 8 + (i + 1) * math.pi / 4
            k.beam((x + r * math.cos(a0), y, z + r * math.sin(a0)), (x + r * math.cos(a1), y, z + r * math.sin(a1)), 0.009, KARAT)
    return (x, (g0 + g1) * 0.5, z)


def build_post():
    k = MeshKit(uv_tile=1.0)
    k.box(-0.32, 0.32, -0.25, 0.14, -0.32, 0.32, KAYU)                                      # plinth step
    pts = [(-0.28, 0.14, -0.28), (0.28, 0.14, -0.28), (0.28, 0.14, 0.28), (-0.28, 0.14, 0.28)]
    top = [(-0.15, 0.52, -0.15), (0.15, 0.52, -0.15), (0.15, 0.52, 0.15), (-0.15, 0.52, 0.15)]
    k.hexa(pts + top, KAYU)                                                                 # tapered foot
    k.box(-0.15, 0.15, 0.52, 0.6, -0.15, 0.15, KAYU)
    k.box(-0.165, 0.165, 0.6, 0.76, -0.165, 0.165, BESI)                                    # iron collar
    k.box(-0.13, 0.13, 0.76, POST_TOP, -0.13, 0.13, KAYU)                                   # post
    cap = [(-0.15, POST_TOP, -0.15), (0.15, POST_TOP, -0.15), (0.15, POST_TOP, 0.15), (-0.15, POST_TOP, 0.15)]
    k.hexa(cap + [(x * 0.45, POST_TOP + 0.1, z * 0.45) for x, _, z in cap], KAYU)           # bevelled top
    k.box(-0.34, ARM_X + 0.2, ARM_Y - 0.2, ARM_Y, -0.1, 0.1, KAYU)                          # cross arm
    k.beam((0.13, ARM_Y - 0.95, 0.0), (0.72, ARM_Y - 0.2, 0.0), 0.055, KAYU)                # diagonal brace
    k.box(ARM_X - 0.08, ARM_X + 0.08, ARM_Y - 0.23, ARM_Y + 0.03, -0.12, 0.12, BESI)        # iron strap
    for i in range(3):                                                                     # chain links
        y = ARM_Y - 0.23 - 0.07 * i
        w = 0.018 if i % 2 else 0.006
        k.box(ARM_X - w - 0.012, ARM_X + w + 0.012, y - 0.07, y, -0.006 - (0.012 - w), 0.006 + (0.012 - w), BESI)
    lantern(k, ARM_X, ARM_Y - 0.44, 0.0)
    return k


def build_bohlam():
    k = MeshKit(uv_tile=1.0)
    k.box(0.0, 0.03, -0.11, 0.11, -0.09, 0.09, BESI)                                        # wall plate
    k.beam((0.03, 0.0, 0.0), (0.26, 0.07, 0.0), 0.016, BESI)                                # bent pipe arm
    k.beam((0.26, 0.07, 0.0), (0.44, 0.04, 0.0), 0.016, BESI)
    k.beam((0.44, 0.05, 0.0), (0.44, -0.04, 0.0), 0.014, BESI)
    frustum(k, 0.44, -0.05, 0.0, 0.035, 0.0, 0.035, BESI)                                   # socket
    frustum(k, 0.44, -0.15, 0.0, 0.2, -0.05, 0.05, ENAMEL, seg=10)                          # enamel shade
    k.mats[-1] = BESI                                                                      # dark underside
    frustum(k, 0.44, -0.24, 0.0, 0.025, -0.19, 0.055, KACA)                                 # bulb (2 frusta)
    frustum(k, 0.44, -0.19, 0.0, 0.055, -0.13, 0.025, KACA)
    return k


def build_pool():
    k = MeshKit(uv_tile=1.0)
    k._face([(-0.5, 0.0, -0.5), (-0.5, 0.0, 0.5), (0.5, 0.0, 0.5), (0.5, 0.0, -0.5)], KACA,
            [(0.0, 0.0), (0.0, 1.0), (1.0, 1.0), (1.0, 0.0)])
    return k


def build():
    return [build_post().build(NAME, MATERIALS), build_bohlam().build(BOHLAM, MATERIALS),
            build_pool().build(POOL, MATERIALS)]


def stats(obs):
    tris = {ob.name: sum(len(p.vertices) - 2 for p in ob.data.polygons) for ob in obs}
    lo, hi = TRI_BUDGET
    return {"name": "SM_Env_Lampu", "tris": tris, "in_budget": all(lo <= t <= hi for n, t in tris.items() if n != POOL)}
