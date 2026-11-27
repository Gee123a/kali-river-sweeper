"""Independent spec QA for the built assets. Run after build_all.py:
    python blender/tests/qa_spec_check.py
Prints PASS/FAIL lines; exit 1 on any FAIL."""
import sys, os, math, json
REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, REPO + "/blender")
import bpy
from mathutils import Vector, Matrix
from kali_blender import excavator_spec as S
from kali_blender import tools_common as tc
from kali_blender import trash_common as trc

fails = []
def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg, flush=True)
    if not cond: fails.append(msg)

def upd():
    from kali_blender import excavator_rig as R
    a = bpy.data.objects.get(S.ARMATURE_NAME)
    R.evaluate(a) if a else bpy.context.view_layer.update()

# ------------------------------------------------ excavator .blend
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, S.BLEND_PATH))
arm = bpy.data.objects.get(S.ARMATURE_NAME); mesh = bpy.data.objects.get(S.MESH_NAME)
check(arm is not None and arm.type == "ARMATURE", "armature object exists")
check(mesh is not None and mesh.type == "MESH", "mesh object exists")
bones = arm.data.bones
want = {b[0]: b for b in S.BONES}
check(set(bones.keys()) == set(want), f"bone set exact (extra={set(bones.keys())-set(want)}, missing={set(want)-set(bones.keys())})")
for name, head, tail, parent, deform in S.BONES:
    b = bones.get(name)
    if not b: continue
    ok = (b.head_local - Vector(head)).length < 1e-3 and (b.tail_local - Vector(tail)).length < 1e-3
    check(ok, f"{name} head/tail")
    check((b.parent.name if b.parent else None) == parent, f"{name} parent {parent}")
    check(b.use_deform == deform, f"{name} deform={deform}")
for o in (arm, mesh):
    check(tuple(o.location) == (0, 0, 0) and tuple(o.rotation_euler) == (0, 0, 0) and tuple(o.scale) == (1, 1, 1), f"{o.name} transforms applied")
pb = arm.pose.bones
ik = [c for c in pb["B_Arm_Stick"].constraints if c.type == "IK"]
check(len(ik) == 1, "one IK on B_Arm_Stick")
if ik:
    c = ik[0]
    check(c.target == arm and c.subtarget == "CTRL_IK_Bucket", "IK target CTRL_IK_Bucket")
    check(c.pole_target == arm and c.pole_subtarget == "POLE_Elbow_Target", "IK pole POLE_Elbow_Target")
    check(c.chain_count == 2, "IK chain length 2")
for suffix in S.PISTONS:
    base, rod = S.piston_bone_names(suffix)
    for a, b in ((base, rod), (rod, base)):
        dts = [c for c in pb[a].constraints if c.type == "DAMPED_TRACK"]
        check(len(dts) == 1 and dts[0].subtarget == b and dts[0].track_axis == "TRACK_Y", f"{a} Damped Track +Y -> {b}")
check(any(c.type == "COPY_ROTATION" and c.subtarget == "CTRL_IK_Bucket" for c in pb["B_Tool_Bucket"].constraints), "bucket Copy Rotation from CTRL")

def reset_pose():
    for p in pb:
        p.location = (0, 0, 0); p.rotation_mode = p.rotation_mode
        p.rotation_quaternion = (1, 0, 0, 0); p.rotation_euler = (0, 0, 0); p.scale = (1, 1, 1)
    upd()

reset_pose()
dev = max(max(abs(a - b) for ra, rb in zip(p.matrix, p.bone.matrix_local) for a, b in zip(ra, rb)) for p in pb)
check(dev < 2e-3, f"rest pose unchanged with constraints (max dev {dev:.5f})")

def piston_ok(tag):
    for suffix in S.PISTONS:
        base, rod = S.piston_bone_names(suffix)
        B, R = pb[base], pb[rod]
        bh, rh = B.head, R.head
        ang1 = math.degrees((B.tail - B.head).angle(rh - bh))
        ang2 = math.degrees((R.tail - R.head).angle(bh - rh))
        overl = (rh - bh).length < B.length + R.length
        check(ang1 < 0.5 and ang2 < 0.5 and overl, f"[{tag}] piston {suffix} aligned ({ang1:.2f},{ang2:.2f}) overlap={overl}")

piston_ok("rest")
ctrl = pb["CTRL_IK_Bucket"]
for i, (dy, dz) in enumerate([(-0.5, -0.8), (0.8, -1.5), (-0.3, 1.0)]):
    reset_pose()
    target = Vector(S.STICK_TAIL) + Vector((0, dy, dz))
    # convert world offset to bone local
    ctrl.location = ctrl.bone.matrix_local.to_3x3().inverted() @ Vector((0, dy, dz))
    upd()
    wrist = pb["B_Arm_Stick"].tail
    check((wrist - target).length < 0.02, f"IK pose {i}: wrist reaches target (err {(wrist-target).length:.4f})")
    piston_ok(f"ik{i}")
    # bucket follows controller rotation
reset_pose()
ctrl.rotation_mode = "XYZ"; ctrl.rotation_euler = (math.radians(40), 0, 0); upd()
d = max(abs(a - b) for ra, rb in zip(pb["B_Tool_Bucket"].matrix.to_3x3(), ctrl.matrix.to_3x3()) for a, b in zip(ra, rb))
check(d < 1e-3, "bucket rotation follows CTRL_IK_Bucket")
piston_ok("bucket40")
reset_pose()
t = pb["B_Turret_Slew"]
check(tuple(t.lock_rotation) == (True, False, True), "turret only rotates about its bone axis (world Z)")
t.rotation_mode = "XYZ"; t.rotation_euler = (0, math.radians(90), 0); upd()
exp = Matrix.Rotation(math.radians(90), 3, "Z") @ (Vector(S.BOOM_TAIL) - Vector((S.TURRET_HEAD[0], S.TURRET_HEAD[1], 0))) + Vector((S.TURRET_HEAD[0], S.TURRET_HEAD[1], 0))
got = pb["B_Arm_Boom"].tail
expn = Matrix.Rotation(math.radians(-90), 3, "Z") @ (Vector(S.BOOM_TAIL) - Vector((S.TURRET_HEAD[0], S.TURRET_HEAD[1], 0))) + Vector((S.TURRET_HEAD[0], S.TURRET_HEAD[1], 0))
check(min((got - exp).length, (got - expn).length) < 0.02 and abs(got.z - S.BOOM_TAIL[2]) < 1e-3, "turret slew rotates arm about world Z")
piston_ok("slew90")
reset_pose()
for k in S.SPUD_XY:
    p = pb[f"B_Spud_Leg_{k}"]
    p.location = (0, -10, 0); upd()
    dz = p.head.z - S.SPUD_BOTTOM_Z
    check(abs(dz + S.SPUD_DROP) < 1e-3 and abs(p.head.x - S.SPUD_XY[k][0]) < 1e-4, f"spud {k} drops exactly 3.5 m (dz={dz:.3f})")
    p.location = (0, 1, 0); upd()
    check(abs(p.head.z - S.SPUD_BOTTOM_Z) < 1e-3, f"spud {k} cannot rise")
    p.location = (0, 0, 0)
reset_pose()
# joint limits: drive IK far up / far down
def arm_angles():
    bd = pb["B_Arm_Boom"].tail - pb["B_Arm_Boom"].head
    sd = pb["B_Arm_Stick"].tail - pb["B_Arm_Stick"].head
    boom = math.degrees(math.atan2(bd.z, -bd.y))
    stick = math.degrees(math.atan2(sd.z, -sd.y)) - boom
    stick = (stick + 180) % 360 - 180
    return boom, stick
ikc = pb["B_Arm_Stick"].constraints["IK_Bucket"]
ikc.mute = True
for bone, deg in (("B_Arm_Boom", 70), ("B_Arm_Boom", -70), ("B_Arm_Stick", 40), ("B_Arm_Stick", -130)):
    reset_pose(); p = pb[bone]; p.rotation_mode = "XYZ"; p.rotation_euler = (math.radians(deg), 0, 0); upd()
    b, s = arm_angles()
    check(-16 <= b <= 76 and -111 <= s <= 11, f"FK limits clamp {bone} {deg}: boom {b:.1f} stick {s:.1f}")
ikc.mute = False
reset_pose()

# mesh
me = mesh.data
me.calc_loop_triangles(); tris = len(me.loop_triangles)
check(S.TRI_BUDGET[0] <= tris <= S.TRI_BUDGET[1], f"excavator tris {tris} in {S.TRI_BUDGET}")
check([m.name for m in me.materials] == S.MATERIAL_ORDER, f"material slots {[m.name for m in me.materials]}")
for m in me.materials:
    spec = S.MATERIALS[m.name]
    bsdf = next(n for n in m.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    col = tuple(bsdf.inputs["Base Color"].default_value)
    expc = S.hex_to_linear_rgba(spec["color_hex"])
    ok = all(abs(a - b) < 1e-3 for a, b in zip(col, expc)) and abs(bsdf.inputs["Metallic"].default_value - spec["metallic"]) < 1e-3 \
        and abs(bsdf.inputs["Roughness"].default_value - (1 - spec["smoothness"])) < 1e-3
    check(ok, f"material {m.name} PBR values")
used = {p.material_index for p in me.polygons}
check(used == {0, 1, 2}, f"all 3 material slots used {used}")
mods = [m for m in mesh.modifiers if m.type == "ARMATURE"]
check(len(mods) == 1 and mods[0].object == arm and mesh.parent == arm, "mesh skinned to armature")
gnames = {g.index: g.name for g in mesh.vertex_groups}
deform = {b[0] for b in S.BONES if b[4]}
check(set(gnames.values()) <= deform and not ({"CTRL_IK_Bucket", "POLE_Elbow_Target"} & set(gnames.values())), "vertex groups only deform bones")
bad = sum(1 for v in me.vertices if len(v.groups) != 1 or abs(v.groups[0].weight - 1) > 1e-6) if me.vertices else -1
check(bad == 0, f"rigid skin: every vertex 1 group weight 1 (bad={bad})")
counts = {n: 0 for n in gnames.values()}
for v in me.vertices:
    for g in v.groups: counts[gnames[g.group]] += 1
missing = [b for b in deform if counts.get(b, 0) < 8]
check(not missing, f"every deform bone owns geometry (missing {missing})")
xs = [v.co.x for v in me.vertices]; ys = [v.co.y for v in me.vertices]; zs = [v.co.z for v in me.vertices]
hull = [v.co for v in me.vertices if gnames[v.groups[0].group] == "B_Root_Hull"]
hx = max(c.x for c in hull) - min(c.x for c in hull); hy = max(c.y for c in hull) - min(c.y for c in hull)
check(abs(hx - 4.8) < 0.15 and abs(hy - 7.2) < 0.15, f"hull footprint {hx:.2f} x {hy:.2f} (want 4.8 x 7.2)")
bk = [v.co for v in me.vertices if gnames[v.groups[0].group] == "B_Tool_Bucket"]
bw = max(c.x for c in bk) - min(c.x for c in bk)
check(abs(bw - 1.4) < 0.15, f"bucket width {bw:.2f} (want 1.4)")

# ------------------------------------------------ excavator FBX reimport
bpy.ops.wm.read_factory_settings(use_empty=True)
fbx = os.path.join(REPO, S.FBX_PATH)
check(os.path.exists(fbx), "excavator FBX exists")
if os.path.exists(fbx):
    bpy.ops.import_scene.fbx(filepath=fbx)
    arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
    meshes = [o for o in bpy.data.objects if o.type == "MESH"]
    names = set(arms[0].data.bones.keys()) if arms else set()
    check(not [n for n in names if n.endswith("_end")], "FBX: no leaf bones")
    check(names == deform, f"FBX bones == deform bones (diff {names ^ deform})")
    check([m.name for m in meshes] == [S.MESH_NAME], f"FBX meshes {[m.name for m in meshes]}")
    if meshes:
        m = meshes[0]
        dims = m.dimensions
        check(max(dims) < 20 and max(dims) > 5, f"FBX reimport dims sane {tuple(round(d,2) for d in dims)}")

# ------------------------------------------------ tools
specs = []
for name in tc.TOOL_MODULES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        mod = tc.load_tool_module(name); obj = tc.build_tool(name)
        issues = tc.validate_tool(obj, mod.SPEC); specs.append(mod.SPEC)
        check(not issues, f"tool {name} validate {issues} tris={tc.tri_count(obj)}")
        check(mod.SPEC["index"] == tc.TOOL_MODULES.index(name) + 1, f"tool {name} index")
    except Exception as e:
        check(False, f"tool {name} builds ({e})")
        continue
    f = os.path.join(REPO, tc.FBX_DIR, mod.SPEC["name"] + ".fbx")
    check(os.path.exists(f), f"tool FBX {os.path.basename(f)} exists")
    if os.path.exists(f):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=f)
        ms = [o for o in bpy.data.objects if o.type == "MESH"]
        check(len(ms) == 1 and ms[0].name == mod.SPEC["name"], f"tool FBX contains only {mod.SPEC['name']}")
for k, fn in tc.ATLAS_FILES.items():
    p = os.path.join(REPO, tc.TEX_DIR, fn)
    ok = os.path.exists(p)
    if ok:
        img = bpy.data.images.load(p); ok = tuple(img.size) == (2048, 2048)
    check(ok, f"atlas {fn} 2048x2048")
check(len({s['name'] for s in specs}) == 20, "20 unique tool names")

# ------------------------------------------------ trash (Medical B3)
tspecs = []
for name in trc.TRASH_MODULES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        mod = trc.load_trash_module(name); obj = trc.build_trash(name)
        issues = trc.validate_trash(obj, mod.SPEC); tspecs.append(mod.SPEC)
        check(not issues, f"trash {name} validate {issues} tris={tc.tri_count(obj)}")
    except Exception as e:
        check(False, f"trash {name} builds ({e})"); continue
    f = os.path.join(REPO, trc.FBX_DIR, mod.SPEC["name"] + ".fbx")
    check(os.path.exists(f), f"trash FBX {os.path.basename(f)} exists")
check({s["prefab"] for s in tspecs} >= {"PF_Trash_MedicalBag", "PF_Trash_SyringeBox"}, "B3 prefab names PF_Trash_MedicalBag / PF_Trash_SyringeBox")
for k, fn in trc.ATLAS_FILES.items():
    p = os.path.join(REPO, trc.TEX_DIR, fn)
    ok = os.path.exists(p)
    if ok:
        img = bpy.data.images.load(p); ok = tuple(img.size) == (2048, 2048)
    check(ok, f"trash atlas {fn} 2048x2048")
# ------------------------------------------------ products (clean shop / world items, origin on the base)
from kali_blender import products_common as pc
pspecs = []
for name in pc.PRODUCT_MODULES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        mod = pc.load_product_module(name); obj = pc.build_product(name)
        issues = pc.validate_product(obj, mod.SPEC); pspecs.append(mod.SPEC)
        check(not issues, f"product {name} validate {issues} tris={tc.tri_count(obj)}")
        check(mod.SPEC["index"] == pc.PRODUCT_MODULES.index(name) + 1, f"product {name} index")
    except Exception as e:
        check(False, f"product {name} builds ({e})"); continue
    f = os.path.join(REPO, pc.FBX_DIR, mod.SPEC["name"] + ".fbx")
    check(os.path.exists(f), f"product FBX {os.path.basename(f)} exists")
    if os.path.exists(f):
        bpy.ops.wm.read_factory_settings(use_empty=True)
        bpy.ops.import_scene.fbx(filepath=f)
        ms = [o for o in bpy.data.objects if o.type == "MESH"]
        check(len(ms) == 1 and ms[0].name == mod.SPEC["name"], f"product FBX contains only {mod.SPEC['name']}")
        if ms:
            zmin = min((ms[0].matrix_world @ v.co).z for v in ms[0].data.vertices)
            check(abs(zmin) < 0.002, f"product FBX {mod.SPEC['name']} stands on its origin (min z {zmin:.4f})")
check(len({s["name"] for s in pspecs}) == len(pc.PRODUCT_MODULES) == 9, "9 unique product names")
check(all(s["prefab"] == s["name"].replace("SM_Product_", "PF_Product_") for s in pspecs), "product prefabs PF_Product_<variant>")
for k, fn in pc.ATLAS_FILES.items():
    p = os.path.join(REPO, pc.TEX_DIR, fn)
    ok = os.path.exists(p)
    if ok:
        img = bpy.data.images.load(p); ok = tuple(img.size) == (2048, 2048)
    check(ok, f"product atlas {fn} 2048x2048")
# ------------------------------------------------ lighting equipment (lantern, beacon, rotor; origin on the mount)
from kali_blender import equipment_common as ec
for name in ec.EQUIPMENT_MODULES:
    bpy.ops.wm.read_factory_settings(use_empty=True)
    try:
        mod = ec.load_equipment_module(name); obj = ec.build_equipment(name)
        check(not ec.validate_equipment(obj, mod.SPEC), f"equipment {name} validate {ec.validate_equipment(obj, mod.SPEC)} tris={tc.tri_count(obj)}")
    except Exception as e:
        check(False, f"equipment {name} builds ({e})"); continue
    f = os.path.join(REPO, ec.FBX_DIR, mod.SPEC["name"] + ".fbx")
    check(os.path.exists(f), f"equipment FBX {os.path.basename(f)} exists")
for k, fn in ec.ATLAS_FILES.items():
    p = os.path.join(REPO, ec.TEX_DIR, fn)
    ok = os.path.exists(p)
    if ok:
        img = bpy.data.images.load(p); ok = tuple(img.size) == (2048, 2048)
    check(ok, f"equipment atlas {fn} 2048x2048")
check(not os.path.exists(os.path.join(REPO, "unity/Assets/_Project/Art")), "no stale outputs under Art/ (JC folders are Props/, Rigging/)")
print(f"\n{len(fails)} FAIL(s)")
sys.exit(1 if fails else 0)
