"""Shared helpers for the 20 KALI trash-collecting tools (guide section 8).

Rules every tool follows (checked by validate_tool):
  * 300 - 1200 triangles.
  * Object origin (0,0,0) = the player's grip point; the mesh surface passes within
    GRIP_TOLERANCE of it. The handle / long axis runs along Z; SPEC["head_dir"] says
    whether the working end points to +Z (net, hook, broom...) or hangs to -Z (pail...).
  * Transforms applied (loc 0, rot 0, scale 1).
  * One material, M_Tools_Atlas, sharing one 2048x2048 atlas. The atlas is a 5x4 grid of
    cells (one per tool, index 1..20); each cell is a 4x4 grid of colour swatches
    (SPEC["palette"], up to 16 entries). Every part's UVs are box-projected into its swatch.
    A SPEC with "label_art" (branded trash) gives the bottom swatch rows of its cell to a printed
    label (labels.py); parts tagged "kali_label" keep their own label-space UVs (label_uv_rect).

Tool module contract (blender/kali_blender/tools/tool_XX_name.py):
    SPEC = {"index": 7, "name": "SM_Tool_SapuLidi", "label": "...", "head_dir": "+Z",
            "palette": [("#7c4a1e", 0.0, 0.25), ...]}   # (sRGB hex, metallic, smoothness)
    def build():      # creates parts in the current scene, returns [obj, ...]
        ...           # each part tagged with tag(obj, swatch_index)
"""
import importlib
import math

import bpy  # noqa: F401  (must be imported before bmesh in the bpy wheel)
import bmesh
from mathutils import Vector

ATLAS_SIZE = 2048
ATLAS_COLS = 5
ATLAS_ROWS = 4
SWATCH_GRID = 4             # 4x4 swatches per cell
SWATCH_MARGIN = 0.12        # fraction of a swatch kept empty on every side
TRI_MIN, TRI_MAX = 300, 1200
GRIP_TOLERANCE = 0.05       # metres from origin to nearest mesh surface
MATERIAL_NAME = "M_Tools_Atlas"
ATLAS_FILES = {
    "albedo": "T_Tools_Atlas_Albedo.png",
    "normal": "T_Tools_Atlas_Normal.png",
    "mask": "T_Tools_Atlas_Mask.png",
}
FBX_DIR = "unity/Assets/_Project/Props/Tools/Meshes"
TEX_DIR = "unity/Assets/_Project/Props/Tools/Textures"
BLEND_PATH = "blender/SM_Tools_Pack.blend"
MAX_SIZE = 5.0              # longest tool (#12 Serokan Jumbo) is 4.5 m

# Official 20-tool list: docs/PRD.md section 3 (index = PRD number).
TOOL_MODULES = [
    "tool_01_sendok_makan_bengkok", "tool_02_gayung_mandi", "tool_03_centong_nasi",
    "tool_04_garpu_taman", "tool_05_ember_cat_5l", "tool_06_gayung_saringan_bambu",
    "tool_07_serokan_waring_3m", "tool_08_ganco_besi_1_mata", "tool_09_ember_cat_20l",
    "tool_10_capitan_ular", "tool_11_arit_sabit_panjang", "tool_12_serokan_jumbo_4_5m",
    "tool_13_ganco_ganda_winch", "tool_14_jala_cincin_lempar", "tool_15_pompa_siphon_manual",
    "tool_16_blok_magnet_50kg", "tool_17_senapan_panah_tali", "tool_18_pompa_mesin_rumput_49cc",
    "tool_19_penebas_gergaji_ganda", "tool_20_garuk_skimmer_hidrolik",
]


def load_tool_module(mod_name):
    return importlib.import_module(f"kali_blender.tools.{mod_name}")


# ---------------------------------------------------------------- UV layout
def cell_rect(index):
    """UV rect (u0, v0, u1, v1) of tool `index` (1..20). Row 0 is the top of the image."""
    i = index - 1
    col, row = i % ATLAS_COLS, i // ATLAS_COLS
    w, h = 1.0 / ATLAS_COLS, 1.0 / ATLAS_ROWS
    u0 = col * w
    v1 = 1.0 - row * h
    return (u0, v1 - h, u0 + w, v1)


def swatch_rect(index, swatch, margin=True):
    u0, v0, u1, v1 = cell_rect(index)
    sw, sh = (u1 - u0) / SWATCH_GRID, (v1 - v0) / SWATCH_GRID
    sx, sy = swatch % SWATCH_GRID, swatch // SWATCH_GRID
    a0, b1 = u0 + sx * sw, v1 - sy * sh
    rect = (a0, b1 - sh, a0 + sw, b1)
    if not margin:
        return rect
    mu, mv = sw * SWATCH_MARGIN, sh * SWATCH_MARGIN
    return (rect[0] + mu, rect[1] + mv, rect[2] - mu, rect[3] - mv)


def label_box(index, rows):
    """Pixel box (x0, y0, x1, y1), end-exclusive, of a label region: the bottom `rows` swatch rows of the
    cell (swatches 0..4*(4-rows)-1 keep the rows above it)."""
    u0, v0, u1, v1 = cell_rect(index)
    top = v0 + (v1 - v0) * rows / SWATCH_GRID
    n = ATLAS_SIZE
    return (math.ceil(u0 * n - 1e-6), math.ceil(v0 * n - 1e-6), math.floor(u1 * n + 1e-6), math.floor(top * n + 1e-6))


def label_uv_rect(index, rows):
    """UV rect of the label region's pixel centres (label-space 0..1 maps onto it)."""
    x0, y0, x1, y1 = label_box(index, rows)
    n = ATLAS_SIZE
    return ((x0 + 0.5) / n, (y0 + 0.5) / n, (x1 - 0.5) / n, (y1 - 0.5) / n)


def _fit_label_uvs(obj, rect):
    """Part UVs were authored in label space (0..1): move them into the label region of the atlas cell."""
    u0, v0, u1, v1 = rect
    for d in obj.data.uv_layers.active.data:
        s, t = min(max(d.uv.x, 0.0), 1.0), min(max(d.uv.y, 0.0), 1.0)
        d.uv = (u0 + (u1 - u0) * s, v0 + (v1 - v0) * t)


# ---------------------------------------------------------------- parts
def tag(obj, swatch):
    """Mark a part object with the palette swatch it uses. Returns obj for chaining."""
    obj["kali_swatch"] = int(swatch)
    return obj


def _box_project_into(obj, rect):
    me = obj.data
    if not me.uv_layers:
        me.uv_layers.new(name="UVMap")
    bm = bmesh.new()
    bm.from_mesh(me)
    uv = bm.loops.layers.uv.verify()
    if not bm.verts:
        bm.free()
        return
    lo = Vector((min(v.co.x for v in bm.verts), min(v.co.y for v in bm.verts), min(v.co.z for v in bm.verts)))
    hi = Vector((max(v.co.x for v in bm.verts), max(v.co.y for v in bm.verts), max(v.co.z for v in bm.verts)))
    size = max((hi - lo).length, 1e-6)
    u0, v0, u1, v1 = rect
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda k: abs(n[k]))
        a, b = [k for k in range(3) if k != ax]
        for loop in f.loops:
            co = loop.vert.co
            s = (co[a] - lo[a]) / size
            t = (co[b] - lo[b]) / size
            loop[uv].uv = (u0 + (u1 - u0) * min(max(s, 0.0), 1.0),
                           v0 + (v1 - v0) * min(max(t, 0.0), 1.0))
    bm.to_mesh(me)
    bm.free()


def atlas_material(name=MATERIAL_NAME):
    mat = bpy.data.materials.get(name)
    if mat is None:
        mat = bpy.data.materials.new(name)
    return mat


def assemble(spec, parts, material_name=MATERIAL_NAME):
    """Join tagged parts into one finished tool object named spec['name']."""
    if not parts:
        raise ValueError(f"{spec['name']}: build() returned no parts")
    for p in parts:
        if "kali_label" in p:       # printed part: its own UVs, in label space (trash_shapes)
            if not spec.get("label_art"):
                raise ValueError(f"{spec['name']}: part {p.name} is a label part but SPEC has no label_art")
            continue
        if "kali_swatch" not in p:
            raise ValueError(f"{spec['name']}: part {p.name} not tagged with a swatch")
        if p["kali_swatch"] >= len(spec["palette"]):
            raise ValueError(f"{spec['name']}: part {p.name} uses swatch {p['kali_swatch']} "
                             f"but palette has {len(spec['palette'])} entries")
    bpy.ops.object.select_all(action="DESELECT")
    for p in parts:
        bpy.context.view_layer.objects.active = p
        p.select_set(True)
        bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
        p.select_set(False)
        p.data.materials.clear()
        if "kali_label" in p:
            _fit_label_uvs(p, label_uv_rect(spec["index"], spec["label_art"]["rows"]))
        else:
            _box_project_into(p, swatch_rect(spec["index"], p["kali_swatch"]))
    for p in parts:
        p.select_set(True)
    bpy.context.view_layer.objects.active = parts[0]
    if len(parts) > 1:
        bpy.ops.object.join()
    obj = bpy.context.view_layer.objects.active
    obj.name = spec["name"]
    obj.data.name = spec["name"]
    for k in list(obj.keys()):
        del obj[k]
    obj.data.materials.clear()
    obj.data.materials.append(atlas_material(material_name))
    for poly in obj.data.polygons:
        poly.material_index = 0
        poly.use_smooth = False
    obj.location = (0, 0, 0)
    obj.rotation_euler = (0, 0, 0)
    obj.scale = (1, 1, 1)
    obj["kali_tool_index"] = spec["index"]
    obj["kali_head_dir"] = spec["head_dir"]
    obj.select_set(False)
    return obj


def build_tool(mod_name, collection=None):
    """Import a tool module, build it, assemble it, link to `collection`. Returns object."""
    mod = load_tool_module(mod_name)
    parts = mod.build()
    obj = assemble(mod.SPEC, parts)
    if collection is not None:
        for c in list(obj.users_collection):
            c.objects.unlink(obj)
        collection.objects.link(obj)
    return obj


# ---------------------------------------------------------------- validation
def tri_count(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


def validate_tool(obj, spec):
    """Return a list of human-readable problems (empty list = passes)."""
    issues = []
    me = obj.data
    tris = tri_count(obj)
    if not TRI_MIN <= tris <= TRI_MAX:
        issues.append(f"tris {tris} outside {TRI_MIN}-{TRI_MAX}")
    if obj.name != spec["name"]:
        issues.append(f"name {obj.name} != {spec['name']}")
    if tuple(round(v, 6) for v in obj.location) != (0, 0, 0):
        issues.append(f"location {tuple(obj.location)} not applied")
    if any(abs(v) > 1e-6 for v in obj.rotation_euler):
        issues.append("rotation not applied")
    if any(abs(v - 1) > 1e-6 for v in obj.scale):
        issues.append("scale not applied")
    if len(me.materials) != 1 or me.materials[0] is None or me.materials[0].name != MATERIAL_NAME:
        issues.append(f"materials {[m.name if m else None for m in me.materials]} != [{MATERIAL_NAME}]")
    if not me.uv_layers:
        issues.append("no UV layer")
    else:
        u0, v0, u1, v1 = cell_rect(spec["index"])
        eps = 1e-5
        bad = sum(1 for d in me.uv_layers.active.data
                  if not (u0 - eps <= d.uv.x <= u1 + eps and v0 - eps <= d.uv.y <= v1 + eps))
        if bad:
            issues.append(f"{bad} UVs outside atlas cell {spec['index']}")
    if not me.vertices:
        issues.append("empty mesh")
        return issues
    # grip: nearest surface point to origin
    import mathutils.bvhtree as bvh
    tree = bvh.BVHTree.FromPolygons([v.co.copy() for v in me.vertices], [tuple(p.vertices) for p in me.polygons])
    hit = tree.find_nearest(Vector((0, 0, 0)))
    if hit[0] is None or hit[3] > GRIP_TOLERANCE:
        issues.append(f"grip: nearest surface {None if hit[0] is None else round(hit[3], 3)} m from origin "
                      f"(> {GRIP_TOLERANCE})")
    xs = [v.co.x for v in me.vertices]
    ys = [v.co.y for v in me.vertices]
    zs = [v.co.z for v in me.vertices]
    dx, dy, dz = max(xs) - min(xs), max(ys) - min(ys), max(zs) - min(zs)
    if dz < max(dx, dy):
        issues.append(f"long axis not Z (dims x{dx:.2f} y{dy:.2f} z{dz:.2f})")
    if not 0.12 <= max(dx, dy, dz) <= MAX_SIZE:
        issues.append(f"implausible size {max(dx, dy, dz):.2f} m")
    hd = spec.get("head_dir")
    if hd == "+Z" and max(zs) < -min(zs):
        issues.append("head_dir +Z but mesh extends further to -Z")
    if hd == "-Z" and -min(zs) < max(zs):
        issues.append("head_dir -Z but mesh extends further to +Z")
    if hd not in ("+Z", "-Z"):
        issues.append(f"head_dir {hd!r} must be '+Z' or '-Z'")
    if not 1 <= len(spec["palette"]) <= SWATCH_GRID * SWATCH_GRID:
        issues.append("palette must have 1-16 entries")
    return issues


# ---------------------------------------------------------------- atlas images
def _srgb(hexstr):
    h = hexstr.lstrip("#")
    return [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]


def write_atlas_images(specs, out_dir, files=ATLAS_FILES):
    """Paint albedo / flat normal / URP mask (R metal, G AO, B detail, A smoothness)."""
    import os
    import numpy as np
    os.makedirs(out_dir, exist_ok=True)
    n = ATLAS_SIZE
    albedo = np.zeros((n, n, 4), dtype=np.float32); albedo[..., 3] = 1.0
    albedo[..., :3] = 0.5
    normal = np.zeros((n, n, 4), dtype=np.float32); normal[...] = (0.5, 0.5, 1.0, 1.0)
    mask = np.zeros((n, n, 4), dtype=np.float32); mask[...] = (0.0, 1.0, 0.0, 0.3)
    emission = np.zeros((n, n, 4), dtype=np.float32); emission[..., 3] = 1.0   # only written if files has "emission"
    for spec in specs:
        for s, (hexstr, metal, smooth, *glow) in enumerate(spec["palette"]):
            u0, v0, u1, v1 = swatch_rect(spec["index"], s, margin=False)
            x0, x1 = int(math.floor(u0 * n)), int(math.ceil(u1 * n))
            y0, y1 = int(math.floor(v0 * n)), int(math.ceil(v1 * n))   # numpy row 0 = bottom (Blender)
            albedo[y0:y1, x0:x1, :3] = _srgb(hexstr)
            mask[y0:y1, x0:x1] = (metal, 1.0, 0.0, smooth)
            if glow and glow[0]:   # optional 4th palette value: swatch glows (white emission mask, tinted in Unity)
                emission[y0:y1, x0:x1, :3] = 1.0
        art = spec.get("label_art")
        if art:   # printed label (brand art + wear) in the bottom rows of the cell
            from kali_blender import labels
            x0, y0, x1, y1 = label_box(spec["index"], art["rows"])
            lab = labels.render_label(art["name"], x1 - x0, y1 - y0, dirty=art.get("dirty", True))
            albedo[y0:y1, x0:x1, :3] = lab["albedo"]
            normal[y0:y1, x0:x1, :3] = lab["normal"]
            mask[y0:y1, x0:x1, 0] = 0.0
            mask[y0:y1, x0:x1, 1] = 1.0
            mask[y0:y1, x0:x1, 2] = 0.0
            mask[y0:y1, x0:x1, 3] = lab["smooth"]
    paths = {}
    maps = [("albedo", albedo, "sRGB"), ("normal", normal, "Non-Color"), ("mask", mask, "Non-Color")]
    if "emission" in files:
        maps.append(("emission", emission, "sRGB"))
    for key, arr, colorspace in maps:
        name = files[key]
        img = bpy.data.images.get(name) or bpy.data.images.new(name, n, n, alpha=True)
        img.colorspace_settings.name = colorspace
        img.pixels.foreach_set(arr.ravel())
        path = os.path.join(out_dir, name)
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        paths[key] = path
    return paths


def wire_atlas_material(paths, material_name=MATERIAL_NAME):
    mat = atlas_material(material_name)
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(nd for nd in nt.nodes if nd.type == "BSDF_PRINCIPLED")
    tex = nt.nodes.get("Albedo") or nt.nodes.new("ShaderNodeTexImage")
    tex.name = "Albedo"
    tex.image = bpy.data.images.load(paths["albedo"], check_existing=True)
    tex.interpolation = "Closest"
    nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
    return mat
