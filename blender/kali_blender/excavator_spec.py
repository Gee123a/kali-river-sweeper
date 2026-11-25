"""Single source of truth for SK_ExcavatorAmfibi (docs/BLENDER_RIGGING_GUIDE_JC.md).

Units: metres. Blender axes: +Z up, the excavator FACES -Y (Blender "Front" view),
its left side (.L / FL / BL) is +X. Root origin (0,0,0) = waterline at hull centre.
Everything in this file is plain data/math - no bpy - so rig, mesh and QA all agree.
"""
from math import cos, sin, radians

ARMATURE_NAME = "SK_ExcavatorAmfibi_Rig"
MESH_NAME = "SK_ExcavatorAmfibi"

# ---- Hull (catamaran pontoon) ------------------------------------------
HULL_LENGTH = 7.2   # along Y
HULL_WIDTH = 4.8    # along X
HULL_HEIGHT = 1.4   # along Z
HULL_BOTTOM_Z = -0.6
HULL_DECK_Z = HULL_BOTTOM_Z + HULL_HEIGHT  # 0.8
SLEW_RING_TOP_Z = 1.4                       # pedestal + slew ring sits on deck

# ---- Arm lengths / limits ------------------------------------------------
BOOM_LENGTH = 4.2
STICK_LENGTH = 2.8
BUCKET_LENGTH = 1.0         # pivot -> tooth tip bone length
BUCKET_WIDTH = 1.4          # cutting edge width (X), 5 teeth + hydraulic thumb
BUCKET_TEETH = 5
BOOM_LIMIT_DEG = (-15.0, 75.0)
STICK_LIMIT_DEG = (-110.0, 10.0)
SPUD_DROP = 3.5             # spud legs translate down 0..3.5 m

# Rest-pose angles (degrees above horizontal, arm points toward -Y)
BOOM_REST_DEG = 35.0
STICK_REST_DEG = -60.0
BUCKET_REST_DEG = -60.0


def _add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def _scale(v, s):
    return tuple(x * s for x in v)


def _lerp(a, b, t):
    return tuple(x + (y - x) * t for x, y in zip(a, b))


def _dir(deg):
    """Unit vector in the YZ plane, pointing forward (-Y) and up by `deg`."""
    return (0.0, -cos(radians(deg)), sin(radians(deg)))


TURRET_HEAD = (0.0, 0.6, SLEW_RING_TOP_Z)
TURRET_TAIL = (0.0, 0.6, SLEW_RING_TOP_Z + 1.2)
BOOM_HEAD = (0.0, -0.6, 2.2)
BOOM_DIR = _dir(BOOM_REST_DEG)
BOOM_TAIL = _add(BOOM_HEAD, _scale(BOOM_DIR, BOOM_LENGTH))        # elbow
STICK_DIR = _dir(STICK_REST_DEG)
STICK_TAIL = _add(BOOM_TAIL, _scale(STICK_DIR, STICK_LENGTH))     # wrist
BUCKET_DIR = _dir(BUCKET_REST_DEG + -40.0)                         # -100 deg: curls back under
BUCKET_TAIL = _add(STICK_TAIL, _scale(BUCKET_DIR, BUCKET_LENGTH))  # tooth tip

# Spud legs: vertical poles through the 4 hull corners, bone points +Z.
SPUD_X = 2.1
SPUD_Y = 3.2
SPUD_BOTTOM_Z = HULL_BOTTOM_Z
SPUD_TOP_Z = 3.0
SPUD_RADIUS = 0.18
SPUD_XY = {
    "FL": (+SPUD_X, -SPUD_Y),   # front = -Y, left = +X
    "FR": (-SPUD_X, -SPUD_Y),
    "BL": (+SPUD_X, +SPUD_Y),
    "BR": (-SPUD_X, +SPUD_Y),
}

# ---- Hydraulic piston anchor pins ---------------------------------------
# Each cylinder = (Base bone: head on parent A, aims at Rod) + (Rod bone: head on
# parent B, aims back at Base). Bone tail = head + PISTON_BONE_FRACTION * (other - head),
# so the two bones always overlap (zero clipping) through the full motion range.
PISTON_BONE_FRACTION = 0.6
PISTONS = {
    # name suffix: (base_pin, base_parent, rod_pin, rod_parent)
    "Boom_L": ((+0.45, -0.1, 1.75), "B_Turret_Slew",
               _add(_lerp(BOOM_HEAD, BOOM_TAIL, 0.45), (+0.45, 0.0, -0.35)), "B_Arm_Boom"),
    "Boom_R": ((-0.45, -0.1, 1.75), "B_Turret_Slew",
               _add(_lerp(BOOM_HEAD, BOOM_TAIL, 0.45), (-0.45, 0.0, -0.35)), "B_Arm_Boom"),
    "Stick": (_add(_lerp(BOOM_HEAD, BOOM_TAIL, 0.30), (0.0, 0.0, 0.45)), "B_Arm_Boom",
              _add(BOOM_TAIL, _scale(STICK_DIR, -0.5)), "B_Arm_Stick"),
    "Bucket": (_add(_lerp(BOOM_TAIL, STICK_TAIL, 0.15), (0.0, -0.30, 0.18)), "B_Arm_Stick",
               _add(_add(STICK_TAIL, _scale(BUCKET_DIR, 0.3)), (0.0, -0.30, 0.17)), "B_Tool_Bucket"),
}


def piston_bone_names(suffix):
    """'Boom_L' -> ('B_Piston_Boom_Base_L', 'B_Piston_Boom_Rod_L'); 'Stick' -> (..._Base, ..._Rod)."""
    parts = suffix.split("_")
    if len(parts) == 2:
        return (f"B_Piston_{parts[0]}_Base_{parts[1]}", f"B_Piston_{parts[0]}_Rod_{parts[1]}")
    return (f"B_Piston_{suffix}_Base", f"B_Piston_{suffix}_Rod")


def _piston_bones():
    out = []
    for suffix, (base_pin, base_parent, rod_pin, rod_parent) in PISTONS.items():
        base_name, rod_name = piston_bone_names(suffix)
        out.append((base_name, base_pin, _lerp(base_pin, rod_pin, PISTON_BONE_FRACTION), base_parent, True))
        out.append((rod_name, rod_pin, _lerp(rod_pin, base_pin, PISTON_BONE_FRACTION), rod_parent, True))
    return out


# ---- Bone table: (name, head, tail, parent, deform) -----------------------
BONES = [
    ("B_Root_Hull", (0.0, 0.0, 0.0), (0.0, 0.0, 1.0), None, True),
    ("B_Turret_Slew", TURRET_HEAD, TURRET_TAIL, "B_Root_Hull", True),
    ("B_Arm_Boom", BOOM_HEAD, BOOM_TAIL, "B_Turret_Slew", True),
    ("B_Arm_Stick", BOOM_TAIL, STICK_TAIL, "B_Arm_Boom", True),
    ("B_Tool_Bucket", STICK_TAIL, BUCKET_TAIL, "B_Arm_Stick", True),
] + _piston_bones() + [
    (f"B_Spud_Leg_{k}", (x, y, SPUD_BOTTOM_Z), (x, y, SPUD_TOP_Z), "B_Root_Hull", True)
    for k, (x, y) in SPUD_XY.items()
] + [
    # Non-deform controllers. Parented to the turret so they swing with the slew.
    # CTRL_IK_Bucket sits on the wrist (bucket pivot) with the SAME orientation as
    # B_Tool_Bucket, so the bucket's Copy Rotation leaves the rest pose untouched.
    ("CTRL_IK_Bucket", STICK_TAIL, BUCKET_TAIL, "B_Turret_Slew", False),
    ("POLE_Elbow_Target", (0.0, BOOM_TAIL[1], 7.5), (0.0, BOOM_TAIL[1], 8.0), "B_Turret_Slew", False),
]

IK_OWNER = "B_Arm_Stick"
IK_TARGET = "CTRL_IK_Bucket"
IK_POLE = "POLE_Elbow_Target"
IK_CHAIN = 2

# ---- Materials (guide section 6) -----------------------------------------
MATERIALS = {
    "M_Excavator_Body":  {"color_hex": "#eab308", "metallic": 0.15, "smoothness": 0.45},
    "M_Hydraulic_Steel": {"color_hex": "#e2e8f0", "metallic": 0.95, "smoothness": 0.90},
    "M_Pontoon_Rubber":  {"color_hex": "#1e293b", "metallic": 0.0,  "smoothness": 0.20},
}
MATERIAL_ORDER = ["M_Excavator_Body", "M_Hydraulic_Steel", "M_Pontoon_Rubber"]
TRI_BUDGET = (4000, 6000)

# ---- Output paths (relative to repo root) --------------------------------
FBX_PATH = "unity/Assets/_Project/Art/Props/Vehicles/SK_ExcavatorAmfibi.fbx"
BLEND_PATH = "blender/SK_ExcavatorAmfibi.blend"


def hex_to_linear_rgba(h):
    h = h.lstrip("#")
    srgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    lin = [c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4 for c in srgb]
    return (*lin, 1.0)
