"""SM_Env_PintuAirSiaga1 (Wesley) - downstream (+Z) sluice gate, 2,000-3,000 tris.

Look follows Wesley's reference: batu kali (river-stone masonry) abutments with white
concrete caps, a rounded concrete centre pier, two blue steel gate leaves in blue guide
frames with spindles + hand wheels, and a blue portal frame carrying a flat yellow roof.

Placement contract (MapJsonImporter): pivot = node "Pintu Air Siaga 1" at map (465, 1390)
-> Unity (-6.875, 0, 83.75), rot 0, groundY 0. The importer drops JC's
PF_WarningBeacon_PintuAir on (bounds.center.x, bounds.max.y, bounds.center.z), so the
mesh is symmetric around the river axis and the highest surface is the flat yellow roof.
"""
from wesley_env.meshkit import MeshKit
from wesley_env.terrain import MAP_SCALE, WORLD_H, WORLD_W, center_map_x, half_width_map

NAME = "SM_Env_PintuAirSiaga1"
NODE_MAP_X, NODE_MAP_Y = 465.0, 1390.0
BED_Y = -2.0
TRI_BUDGET = (2000, 3000)

STONE, CONCRETE, BLUE, YELLOW, DARK = range(5)
MATERIALS = (
    ("M_Env_BatuKali", (0.55, 0.55, 0.53, 1.0)),
    ("M_Env_BetonPutih", (0.86, 0.86, 0.83, 1.0)),
    ("M_Env_BesiBiru", (0.13, 0.36, 0.78, 1.0)),
    ("M_Env_AtapKuning", (0.95, 0.74, 0.16, 1.0)),
    ("M_Env_BesiGelap", (0.20, 0.21, 0.23, 1.0)),
)


def river_frame():
    """River centre (local X, relative to the node pivot) and half width at the gate."""
    cx_world = (center_map_x(NODE_MAP_Y) - WORLD_W * 0.5) * MAP_SCALE
    node_x = (NODE_MAP_X - WORLD_W * 0.5) * MAP_SCALE
    return cx_world - node_x, half_width_map(NODE_MAP_Y) * MAP_SCALE


def build():
    k = MeshKit(uv_tile=2.5)
    cx, hw = river_frame()               # cx ~ -0.3 m, hw ~ 12 m (water edge at Y=0)
    face = hw - 1.5                       # inner face of each abutment (covers the 45 deg talud)
    pier_hw = 1.0
    bay_in, bay_out = pier_hw + 0.15, face - 0.15

    for s in (-1, 1):
        # --- batu kali abutment + white cap ---
        x_in, x_out = cx + s * face, cx + s * (hw + 3.0)
        k.box(min(x_in, x_out), max(x_in, x_out), BED_Y, 2.0, -4.0, 4.0, STONE)
        k.box(min(x_in, x_out) - 0.15, max(x_in, x_out) + 0.15, 2.0, 2.3, -4.15, 4.15, CONCRETE)
        # --- wing walls flaring along the banks (upstream & downstream) ---
        for zs in (-1, 1):
            yaw = -s * zs * 25.0
            wx, wz = cx + s * (face + 1.6), zs * 6.6
            k.box_yaw(wx, wz, 0.6, 2.8, yaw, BED_Y, 1.8, STONE)
            k.box_yaw(wx, wz, 0.75, 2.85, yaw, 1.8, 2.05, CONCRETE)

        # --- blue steel gate leaf with stiffeners (one per bay) ---
        g0, g1 = sorted((cx + s * bay_in, cx + s * bay_out))
        k.box(g0, g1, BED_Y, 2.6, -0.15, 0.15, BLUE)
        for y in (-0.4, 0.9, 2.1):
            k.box(g0, g1, y, y + 0.18, 0.15, 0.32, BLUE)
        for gx in (g0 + 0.1, (g0 + g1) * 0.5 - 0.1, g1 - 0.3):
            k.box(gx, gx + 0.2, -1.0, 2.6, 0.15, 0.32, BLUE)

        # --- guide frame: two posts + lifting beam ---
        p0, p1 = sorted((cx + s * pier_hw, cx + s * face))
        k.box(p0, p0 + 0.4, -0.6, 4.6, -0.3, 0.3, BLUE)
        k.box(p1 - 0.4, p1, -0.6, 4.6, -0.3, 0.3, BLUE)
        k.box(p0, p1, 4.2, 4.6, -0.3, 0.3, BLUE)

        # --- spindles, gearboxes and hand wheels (2 per gate) ---
        for f in (0.3, 0.7):
            sx = g0 + (g1 - g0) * f
            k.cylinder(sx, 0.0, 0.07, 2.6, 5.8, DARK, seg=12)
            k.box(sx - 0.3, sx + 0.3, 4.6, 5.05, -0.25, 0.25, DARK)
            k.torus_y(sx, 5.35, 0.0, 0.38, 0.045, DARK, seg=16, ring=6)
            for a, b in ((-0.38, 0.38),):
                k.box(sx + a, sx + b, 5.32, 5.38, -0.025, 0.025, DARK)
                k.box(sx - 0.025, sx + 0.025, 5.32, 5.38, a, b, DARK)

        # --- catwalk (upstream of the gates) + railing ---
        k.box(g0, g1, 2.3, 2.5, -2.4, -0.6, CONCRETE)
        posts = 8
        for i in range(posts):
            px = g0 + 0.1 + (g1 - g0 - 0.2) * i / (posts - 1)
            k.box(px - 0.05, px + 0.05, 2.5, 3.5, -2.35, -2.25, BLUE)
        k.box(g0, g1, 3.42, 3.52, -2.36, -2.24, BLUE)
        k.box(g0, g1, 2.98, 3.04, -2.33, -2.27, BLUE)

        # --- small blue hand-rail on the abutment (as in the reference) ---
        rx = cx + s * (face + 1.2)
        for rz in (1.2, 3.4):
            k.box(rx - 0.05, rx + 0.05, 2.3, 3.3, rz - 0.05, rz + 0.05, BLUE)
        k.box(rx - 0.05, rx + 0.05, 3.2, 3.3, 1.15, 3.45, BLUE)

        # --- stairs from the bank (+1.40) up to the catwalk (+2.50), upstream side ---
        sx0 = cx + s * (face + 0.2)
        for i in range(5):
            y_top = 1.4 + 0.22 * (i + 1)
            z0 = -4.0 - 0.35 * (5 - i)
            a, b = sorted((sx0, sx0 + s * 1.4))
            k.box(a, b, 1.2, y_top, z0, z0 + 0.35, CONCRETE)

        # --- portal column on the abutment ---
        col = cx + s * (hw - 0.6)
        k.box(col - 0.3, col + 0.3, 2.3, 7.0, -0.3, 0.3, BLUE)
        k.box(col - 0.45, col + 0.45, 2.3, 2.5, -0.45, 0.45, BLUE)  # base plate

    # --- rounded concrete centre pier ---
    k.stadium(cx, 0.0, pier_hw, 2.2, BED_Y, 3.2, CONCRETE, seg=16)
    k.box(cx - 0.3, cx + 0.3, 3.2, 7.0, -0.3, 0.3, BLUE)          # centre portal column
    k.box(cx - 0.45, cx + 0.45, 3.2, 3.4, -0.45, 0.45, BLUE)

    # --- portal beam + flat yellow roof (beacon pad = roof centre) ---
    span = hw - 0.6 + 0.45
    k.box(cx - span, cx + span, 7.0, 7.6, -0.4, 0.4, BLUE)
    k.box(cx - span - 0.6, cx + span + 0.6, 7.6, 7.95, -1.7, 1.7, YELLOW)
    # roof edge lip (kept below the flat top so the beacon pad stays clear)
    k.box(cx - span - 0.65, cx + span + 0.65, 7.45, 7.6, -1.75, -1.6, YELLOW)
    k.box(cx - span - 0.65, cx + span + 0.65, 7.45, 7.6, 1.6, 1.75, YELLOW)
    k.box(cx - span - 0.65, cx - span - 0.5, 7.45, 7.6, -1.6, 1.6, YELLOW)
    k.box(cx + span + 0.5, cx + span + 0.65, 7.45, 7.6, -1.6, 1.6, YELLOW)

    ob = k.build(NAME, MATERIALS)
    return ob


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    lo, hi = TRI_BUDGET
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "in_budget": lo <= tris <= hi}
