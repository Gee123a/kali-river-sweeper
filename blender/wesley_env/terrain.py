"""SM_Env_RiverValleyTerrain (Wesley) - generated from the exact RiverMath formula.

Mirrors RiverMath in unity/Assets/_Project/Scripts/Core/RiverFlowBuoyancy.cs and the
greybox heights in MapJsonImporter.cs (BankTopY 1.40, RiverbedTopY -2.0).
"""
import math

import bpy

MAP_SCALE, WORLD_W, WORLD_H = 0.125, 1040.0, 1440.0
BANK_Y, BED_Y = 1.40, -2.0          # tanggul +1.40 m, dasar sungai -2.0 m
SLOPE_IN, SLOPE_OUT = 2.0, 1.4      # talud 45 derajat, memotong Y=0 tepat di tepi sungai RiverMath
ROW_STEP = 2.0                      # jarak baris sepanjang Z (meter)
LAND_COLS = [0.0, 0.08, 0.2, 0.38, 0.6, 0.82, 1.0]
BED_COLS = 4
UV_TILE = 4.0                       # 1 tile tekstur = 4 m
NAME = "SM_Env_RiverValleyTerrain"

MATERIALS = (
    ("M_Env_TanahBantaran", (0.24, 0.31, 0.22, 1.0)),
    ("M_Env_TaludBeton", (0.45, 0.47, 0.46, 1.0)),
    ("M_Env_LumpurDasar", (0.18, 0.15, 0.11, 1.0)),
)


def center_map_x(map_y):
    return 520.0 + math.sin((map_y / WORLD_H) * math.pi * 1.6) * 58.0


def half_width_map(map_y, base=180.0):
    w = base
    if map_y < 320.0:
        w += max(0.0, min(1.0, (320.0 - map_y) / 200.0)) * 130.0
    choke = math.exp(-((map_y - 740.0) / 150.0) ** 2) * 28.0
    bay = math.exp(-((map_y - 1220.0) / 180.0) ** 2) * 22.0
    return (w - choke + bay) * 0.5


def row_profile(uz):
    """(unity_x, unity_y, zone) across one row. zone 0 = tanah, 2 = lumpur dasar."""
    map_y = uz / MAP_SCALE + WORLD_H * 0.5
    cx = (center_map_x(map_y) - WORLD_W * 0.5) * MAP_SCALE
    hw = half_width_map(map_y) * MAP_SCALE
    half = WORLD_W * MAP_SCALE * 0.5
    l_top, l_bed = cx - hw - SLOPE_OUT, cx - hw + SLOPE_IN
    r_bed, r_top = cx + hw - SLOPE_IN, cx + hw + SLOPE_OUT
    pts = [(-half + (l_top + half) * t, BANK_Y, 0) for t in LAND_COLS]
    pts += [(l_bed + (r_bed - l_bed) * i / BED_COLS, BED_Y, 2) for i in range(BED_COLS + 1)]
    pts += [(half - (half - r_top) * t, BANK_Y, 0) for t in reversed(LAND_COLS)]
    return pts


def unity_to_blender(ux, uy, uz):
    # FBX export (-Z Forward, Y Up) + Unity's X-flip on import  =>  Blender = (-x, -z, y)
    return (-ux, -uz, uy)


def build():
    """Create (or rebuild) the terrain object at the world origin and return it."""
    half_z = WORLD_H * MAP_SCALE * 0.5
    rows = int(round(2 * half_z / ROW_STEP))
    verts, zones = [], []
    for r in range(rows + 1):
        uz = -half_z + r * ROW_STEP
        for ux, uy, zone in row_profile(uz):
            verts.append(unity_to_blender(ux, uy, uz))
            zones.append(zone)
    cols = len(row_profile(0.0))

    faces, face_mat = [], []
    for r in range(rows):
        for c in range(cols - 1):
            a = r * cols + c
            b, d = a + 1, a + cols
            e = d + 1
            faces.append((a, b, e, d))
            zs = {zones[a], zones[b], zones[d], zones[e]}
            face_mat.append(2 if zs == {2} else (0 if zs == {0} else 1))  # 1 = talud

    old = bpy.data.objects.get(NAME)
    if old:
        old_mesh = old.data
        bpy.data.objects.remove(old, do_unlink=True)
        if old_mesh.users == 0:
            bpy.data.meshes.remove(old_mesh)

    me = bpy.data.meshes.new(NAME)
    me.from_pydata(verts, [], faces)
    me.update()

    for mname, col in MATERIALS:
        mat = bpy.data.materials.get(mname) or bpy.data.materials.new(mname)
        mat.diffuse_color = col
        bsdf = mat.node_tree.nodes.get("Principled BSDF") if mat.node_tree else None
        if bsdf:
            bsdf.inputs["Base Color"].default_value = col
            bsdf.inputs["Roughness"].default_value = 0.9
        me.materials.append(mat)
    for poly, m in zip(me.polygons, face_mat):
        poly.material_index = m

    # world-planar UV: U = Unity X / UV_TILE, V = Unity Z / UV_TILE
    uv = me.uv_layers.new(name="UVMap")
    for poly in me.polygons:
        for li in poly.loop_indices:
            co = me.vertices[me.loops[li].vertex_index].co
            uv.data[li].uv = (-co.x / UV_TILE, -co.y / UV_TILE)

    ob = bpy.data.objects.new(NAME, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def stats(ob):
    me = ob.data
    tris = sum(len(p.vertices) - 2 for p in me.polygons)
    down = sum(1 for p in me.polygons if p.normal.z <= 0.0)
    return {"name": ob.name, "verts": len(me.vertices), "tris": tris, "faces_pointing_down": down}
