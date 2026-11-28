"""Villager variety (plan_jc Task 6C): body variants + head accessories + per-NPC palettes.

Everything shares the SK_VillagerNPC rig (VillagerRig, same 21 bones) and the palette UV layout, so:
  * body variant = another skinned FBX (Humanoid) that plays the clips of SK_VillagerNPC.fbx,
  * accessory    = rigid SM_ mesh parented to the `Head` bone with zero local transform
                   (Head has an identity rest frame in Unity; origin = Head bone head),
  * colours      = T_Villager_Palette_<Npc>.png swapped per renderer with a MaterialPropertyBlock
                   (`_BaseMap`), on the body AND its accessory.
Swatches 11-12 ('bin', 'bin_dark') are the accessory colours (kerudung / cap) in the NPC palettes, and
'bag' is the sarung stripe; the default palette keeps them for the bin / bag props.
"""
import math

import bpy  # noqa: F401
from mathutils import Vector

from . import rigging_common as rc
from . import villager as V

BODIES = {   # name: build_mesh kwargs
    "SK_VillagerNPC_Bare": {"hat": False, "lower": "shorts"},
    "SK_VillagerNPC_Sarung": {"hat": False, "lower": "sarung"},
}
HEAD_ORIGIN = Vector((0, 0, 1.04))      # Head bone head = accessory origin

RECIPES = {  # quest giver: body, accessory, palette overrides (sRGB), uniform scale
    "PakRT": ("SK_VillagerNPC_Sarung", "SM_Villager_Hat_Peci",
              {"shirt": "#E8DEC2", "shirt_trim": "#B5A587", "shorts": "#2F5A3E", "bag": "#7E2A2A"}, 1.0),
    "BuSiti": ("SK_VillagerNPC_Bare", "SM_Villager_Hat_Kerudung",
               {"shirt": "#2E8B8B", "shirt_trim": "#1F6262", "shorts": "#5A2A3A", "bin": "#E58FB0",
                "bin_dark": "#B5607F"}, 1.0),
    "PakDarto": ("SK_VillagerNPC", None,
                 {"shirt": "#4F79A8", "shirt_trim": "#34557A", "shorts": "#8A7A55"}, 1.0),
    "Raka": ("SK_VillagerNPC_Bare", "SM_Villager_Hat_Topi",
             {"shirt": "#F2C230", "shirt_trim": "#C99A1A", "shorts": "#C0392B", "bin": "#2E86DE",
              "bin_dark": "#1F5FA0"}, 0.64),
    "MbokNah": ("SK_VillagerNPC_Sarung", "SM_Villager_Hair_Konde",
                {"shirt": "#E0782F", "shirt_trim": "#A8521C", "shorts": "#6B4226", "bag": "#D9A441"}, 0.97),
}
X, Y, Z = Vector((1, 0, 0)), Vector((0, 1, 0)), Vector((0, 0, 1))
W_HEAD = {"Head": 1.0}


def palette_for(npc):
    over = RECIPES[npc][2]
    return rc.Palette([(k, over.get(k, h)) for k, h in V.PALETTE.colors])


def png_path(npc):
    return V.PALETTE_PNG.replace(".png", f"_{npc}.png")


def _peci(mb):
    rows = [(1.284, 0.164, 0.153), (1.398, 0.154, 0.142)]
    rings = [rc.ring((0, 0.006, z), Z, X, a, Y, b, 12, 2.4) for z, a, b in rows]
    mb.loft(rings, [W_HEAD] * 2, ["hair"], cap0="hair", cap1="hair")


def _topi(mb):
    rows = [(1.268, 0.172, 0.162), (1.335, 0.162, 0.152), (1.382, 0.118, 0.110)]
    rings = [rc.ring((0, 0.004, z), Z, X, a, Y, b, 10, 2.2) for z, a, b in rows]
    ids = mb.loft(rings, [W_HEAD] * 3, ["bin", "bin"], cap0="bin_dark")
    mb.fan(ids[-1], (0, 0.004, 1.404), W_HEAD, "bin")
    # brim: front arc pushed forward, two-sided (top + bottom faces)
    arc = [i for i, q in enumerate(rings[0]) if q.y < -0.05]
    arc.sort(key=lambda i: rings[0][i].x)
    inner = [rings[0][i] + Vector((0, 0, 0.004)) for i in arc]
    outer = [Vector((q.x * 1.05, q.y - 0.075, q.z - 0.012)) for q in inner]
    top = [[mb.vert(q, W_HEAD) for q in row] for row in (inner, outer)]
    bot = [[mb.vert(q - Vector((0, 0, 0.008)), W_HEAD) for q in row] for row in (inner, outer)]
    for i in range(len(arc) - 1):
        mb.face((top[0][i], top[1][i], top[1][i + 1], top[0][i + 1]), "bin_dark")
        mb.face((bot[0][i + 1], bot[1][i + 1], bot[1][i], bot[0][i]), "bin_dark")
    for i in range(len(arc) - 1):        # front edge
        mb.face((top[1][i], bot[1][i], bot[1][i + 1], top[1][i + 1]), "bin_dark")


def _kerudung(mb):
    """Head scarf: a shell 1.6 cm off the head with the face left open, closing under the chin to the collar."""
    off = 0.016
    rings = []
    for lat in (62, 36, 12, -12, -36, -62):
        la = math.radians(lat)
        s = math.cos(la) ** 0.8
        jaw = max(0.0, -math.sin(la))
        rx = V.HEAD_R[0] * s * (1 - 0.10 * jaw) + off
        ry = V.HEAD_R[1] * s * (1 - 0.05 * jaw) + off
        c = V.HEAD_C + Vector((0, 0.012 * jaw, V.HEAD_R[2] * math.sin(la)))
        rings.append(rc.ring(c, -Z, X, rx, Y, ry, 12, 2.3, math.pi / 12))
    rings.append(rc.ring((0, 0.012, 1.005), -Z, X, 0.115, Y, 0.105, 12, 2.3, math.pi / 12))
    rings.append(rc.ring((0, 0.010, 0.975), -Z, X, 0.150, Y, 0.120, 12, 2.3, math.pi / 12))
    f0 = len(mb.faces)
    ids = mb.loft(rings, [W_HEAD] * len(rings), ["bin"] * (len(rings) - 1))
    mb.fan(ids[0], V.HEAD_C + Vector((0, 0, V.HEAD_R[2] + off)), W_HEAD, "bin", flip=True)
    keep_f, keep_c = [], []
    for fi in range(f0, len(mb.faces)):             # open the face window
        c = sum((mb.verts[v] for v in mb.faces[fi]), Vector()) / len(mb.faces[fi])
        if not (c.y < -0.05 and 1.07 < c.z < 1.30 and abs(c.x) < 0.14):
            keep_f.append(mb.faces[fi])
            keep_c.append("bin_dark" if (c.y < -0.03 and c.z > 1.06) else mb.fcol[fi])   # trim around the face
    del mb.faces[f0:], mb.fcol[f0:]
    mb.faces += keep_f
    mb.fcol += keep_c


def _konde(mb):
    c = Vector((0, 0.178, 1.235))
    rings = [rc.ring(c + Vector((0, 0, dz)), Z, X, a, Y, b, 8) for dz, a, b in
             ((-0.035, 0.032, 0.026), (0.0, 0.052, 0.042), (0.033, 0.034, 0.028))]
    ids = mb.loft(rings, [W_HEAD] * 3, ["hair", "hair"])
    mb.fan(ids[0], c + Vector((0, 0, -0.05)), W_HEAD, "hair", flip=True)
    mb.fan(ids[-1], c + Vector((0, 0, 0.048)), W_HEAD, "hair")


ACCESSORIES = {
    "SM_Villager_Hat_Peci": _peci,
    "SM_Villager_Hat_Topi": _topi,
    "SM_Villager_Hat_Kerudung": _kerudung,
    "SM_Villager_Hair_Konde": _konde,
}


def build_accessory(name, material):
    """Rigid accessory with its origin at the Head bone head (mesh data shifted, object at 0)."""
    mb = rc.MeshBuilder(V.PALETTE)
    ACCESSORIES[name](mb)
    mb.verts = [v - HEAD_ORIGIN for v in mb.verts]
    return mb.build(name, material, None)


def build_bodies(material, rig):
    out = {}
    for name, kw in BODIES.items():
        mesh = V.build_mesh(material, name=name, **kw)
        V.skin(mesh, rig)
        out[name] = mesh
    return out


def assembled_tris(npc, tri_of):
    """Triangles of a recipe; tri_of(name) -> tris of a body / accessory."""
    body, acc, _o, _s = RECIPES[npc]
    return tri_of(body) + (tri_of(acc) if acc else 0)


def attach_accessory(rig, obj):
    """Preview only: parent to the Head bone at rest (origin = bone head)."""
    bone = rig.data.bones["Head"]
    obj.parent = rig
    obj.parent_type = "BONE"
    obj.parent_bone = "Head"
    from mathutils import Matrix
    obj.matrix_parent_inverse = Matrix.Identity(4)
    tail = bone.matrix_local @ Matrix.Translation((0, bone.length, 0))
    obj.matrix_basis = tail.inverted() @ Matrix.Translation(bone.head_local)
