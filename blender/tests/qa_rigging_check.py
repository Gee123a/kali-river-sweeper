"""Spec QA for the rigging stage. Run after `build_all.py --only rigging`:
    blender -b --factory-startup -P blender/tests/qa_rigging_check.py
Prints PASS/FAIL lines; exit 1 on any FAIL."""
import math
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "blender"))
import bpy  # noqa: E402
from mathutils import Matrix  # noqa: E402

from kali_blender import rigging_common as rc  # noqa: E402
from kali_blender import tool_swing as T  # noqa: E402
from kali_blender import villager as V  # noqa: E402
from kali_blender import villager_clips as C  # noqa: E402
from kali_blender import villager_variants as VV  # noqa: E402
from kali_blender import player_arms as PA  # noqa: E402

fails = []


def check(cond, msg):
    print(("PASS " if cond else "FAIL ") + msg, flush=True)
    if not cond:
        fails.append(msg)


def skin_stats(obj, allowed):
    names = {g.index: g.name for g in obj.vertex_groups}
    unweighted = over4 = badsum = 0
    for v in obj.data.vertices:
        ws = [g.weight for g in v.groups if g.weight > 1e-6]
        if not ws:
            unweighted += 1
        if len(ws) > 4:
            over4 += 1
        if ws and abs(sum(ws) - 1) > 1e-3:
            badsum += 1
    stray = set(names.values()) - set(allowed)
    return unweighted, over4, badsum, stray


def tris(obj):
    obj.data.calc_loop_triangles()
    return len(obj.data.loop_triangles)


# ------------------------------------------------ villager .blend
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, V.BLEND_PATH))
rig, mesh = bpy.data.objects.get(V.RIG_NAME), bpy.data.objects.get(V.NAME)
check(rig is not None and rig.type == "ARMATURE" and mesh is not None, "villager rig + mesh exist")
n = tris(mesh)
check(V.TRI_BUDGET[0] <= n <= V.TRI_BUDGET[1], f"villager tris {n} in {V.TRI_BUDGET}")
want = [b[0] for b in V.BONES]
check(sorted(rig.data.bones.keys()) == sorted(want), "bone set exact (Unity Humanoid names + 2 sockets)")
check(all(rig.data.bones[b].use_deform for b in V.DEFORM_BONES) and
      not any(rig.data.bones[b].use_deform for b in V.SOCKETS.values()), "sockets non-deform, body bones deform")
un, o4, bs, stray = skin_stats(mesh, V.DEFORM_BONES)
check(un == 0, f"unweighted vertices = {un}")
check(o4 == 0 and bs == 0, f"<=4 influences ({o4} over) and normalised ({bs} off)")
check(not stray, f"vertex groups only deform bones (stray {stray})")
check(mesh.parent == rig and any(m.type == "ARMATURE" and m.object == rig for m in mesh.modifiers), "mesh skinned to rig")
for o in (rig, mesh):
    check(o.matrix_world == Matrix.Identity(4), f"{o.name} transforms applied")
zs = [v.co.z for v in mesh.data.vertices]
xs = [v.co.x for v in mesh.data.vertices]
check(abs(min(zs)) < 1e-4 and abs(max(xs) + min(xs)) < 1e-4, f"base pivot: soles at z=0 ({min(zs):.4f}), centred on x")
check(1.35 < max(zs) < 1.6, f"height {max(zs):.2f} m")
mat = mesh.data.materials
check(len(mat) == 1 and mat[0].name == V.MATERIAL, "one palette material")
head = [v.co for v in mesh.data.vertices if v.co.z > 1.08 and v.co.z < 1.3 and abs(v.co.x) < 0.05]
check(min(c.y for c in head) < -0.15, "face (nose / eyes) on -Y = Unity +Z")
for socket in V.SOCKETS.values():
    m = rig.data.bones[socket].matrix_local.to_3x3()
    dev = max(abs(a - b) for ra, rb in zip(m, Matrix.Rotation(math.radians(90), 3, "X")) for a, b in zip(ra, rb))
    check(dev < 1e-5, f"{socket} points +Z, roll 0 (identity frame in Unity)")
tracks = {t.name for t in rig.animation_data.nla_tracks}
check(tracks == set(C.ALL_TAKES), f"NLA takes ({len(tracks)}) {sorted(tracks)}")
for name, frames in C.ALL_TAKES.items():
    act = bpy.data.actions.get(name)
    check(act is not None and tuple(act.frame_range) == (0, frames), f"action {name} 0..{frames}")

# ------------------------------------------------ villager FBX re-import
fbx = os.path.join(REPO, V.FBX_PATH)
check(rc.take_names_in_fbx(fbx) == sorted(C.ALL_TAKES), f"FBX takes {rc.take_names_in_fbx(fbx)}")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
meshes = [o for o in bpy.data.objects if o.type == "MESH"]
bones = sorted(arms[0].data.bones.keys()) if arms else []
check(bones == sorted(want), f"FBX bones == spec ({len(bones)})")
check(not [b for b in bones if b.endswith("_end")], "FBX: no leaf bones")
check([m.name for m in meshes] == [V.NAME], f"FBX meshes {[m.name for m in meshes]}")
if meshes:
    m = meshes[0]
    check(V.TRI_BUDGET[0] <= tris(m) <= V.TRI_BUDGET[1], f"FBX tris {tris(m)}")
    un, o4, bs, stray = skin_stats(m, V.DEFORM_BONES)
    check(un == 0 and not stray, f"FBX unweighted vertices = {un}")
acts = {a.name: a for a in bpy.data.actions}
for name, frames in C.ALL_TAKES.items():
    hit = [a for k, a in acts.items() if name in k.split("|")]
    ok = bool(hit) and round(hit[0].frame_range[1] - hit[0].frame_range[0]) == frames
    check(ok, f"re-imported action for take {name} ({[a.name for a in hit]}, {frames} frames)")
for prop in V.SOCKETS:
    f = os.path.join(REPO, rc.FBX_DIR, prop + ".fbx")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ok = os.path.exists(f)
    if ok:
        bpy.ops.import_scene.fbx(filepath=f)
        ms = [o for o in bpy.data.objects if o.type == "MESH"]
        ok = len(ms) == 1 and ms[0].name == prop and tris(ms[0]) < 300
    check(ok, f"prop FBX {prop} (one mesh, < 300 tris)")

# ------------------------------------------------ tool swing
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, T.BLEND_PATH))
rig = bpy.data.objects.get(T.RIG_NAME)
check(rig is not None and list(rig.data.bones.keys()) == [T.BONE], "tool swing rig = ToolSwingRig / ToolHolder")
check(rig.matrix_world == T.RIG_MATRIX and rig.data.bones[T.BONE].matrix_local == Matrix.Identity(4),
      "rig +90 X with identity bone (Unity rest = identity)")
fbx = os.path.join(REPO, T.FBX_PATH)
check(rc.take_names_in_fbx(fbx) == sorted(T.TAKES), f"FBX takes {rc.take_names_in_fbx(fbx)}")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
check(len(arms) == 1 and list(arms[0].data.bones.keys()) == [T.BONE], "FBX bones == [ToolHolder]")
check(not [o for o in bpy.data.objects if o.type == "MESH"], "FBX has no mesh")
for name, frames in T.TAKES.items():
    hit = [a for a in bpy.data.actions if name in a.name.split("|")]
    moving = False
    if hit:
        for fc in rc.action_fcurves(hit[0]):
            vals = [k.co[1] for k in fc.keyframe_points]
            moving |= max(vals) - min(vals) > 0.05
    ok = bool(hit) and round(hit[0].frame_range[1] - hit[0].frame_range[0]) == frames and moving
    check(ok, f"re-imported take {name}: {frames} frames, ToolHolder animated")

# ------------------------------------------------ villager variety (Task 6C)
tri_of = {V.NAME: None}
for body in VV.BODIES:
    f = os.path.join(REPO, rc.FBX_DIR, body + ".fbx")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ok = os.path.exists(f)
    if ok:
        bpy.ops.import_scene.fbx(filepath=f)
        arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
        ms = [o for o in bpy.data.objects if o.type == "MESH"]
        ok = (len(ms) == 1 and ms[0].name == body and arms and sorted(arms[0].data.bones.keys()) == sorted(want)
              and skin_stats(ms[0], V.DEFORM_BONES)[0] == 0)
        tri_of[body] = tris(ms[0]) if ms else 0
        ok = ok and not rc.take_names_in_fbx(f)
    check(ok, f"body variant {body}: same 21 bones, unweighted 0, no takes ({tri_of.get(body)} tris)")
for acc in VV.ACCESSORIES:
    f = os.path.join(REPO, rc.FBX_DIR, acc + ".fbx")
    bpy.ops.wm.read_factory_settings(use_empty=True)
    ok = os.path.exists(f)
    if ok:
        bpy.ops.import_scene.fbx(filepath=f)
        ms = [o for o in bpy.data.objects if o.type == "MESH"]
        ok = len(ms) == 1 and ms[0].name == acc
        tri_of[acc] = tris(ms[0]) if ms else 0
        zs = [(ms[0].matrix_world @ v.co).z for v in ms[0].data.vertices] if ms else [0]
        ok = ok and -0.15 < min(zs) and max(zs) < 0.45          # origin at the Head bone head
    check(ok, f"accessory {acc} ({tri_of.get(acc)} tris, origin at Head bone)")
tri_of[V.NAME] = n
for npc in VV.RECIPES:
    t = VV.assembled_tris(npc, tri_of.get)
    check(V.TRI_BUDGET[0] <= t <= V.TRI_BUDGET[1], f"{npc} assembled {t} tris in {V.TRI_BUDGET}")
    pth = os.path.join(REPO, VV.png_path(npc))
    ok = os.path.exists(pth)
    if ok:
        img = bpy.data.images.load(pth)
        ok = tuple(img.size) == (64, 64)
    check(ok, f"palette {os.path.basename(pth)} 64x64")

# ------------------------------------------------ first-person arms
fbx = os.path.join(REPO, PA.FBX_PATH)
check(rc.take_names_in_fbx(fbx) == sorted(PA.TAKES), f"SK_PlayerArms takes {rc.take_names_in_fbx(fbx)}")
bpy.ops.wm.read_factory_settings(use_empty=True)
bpy.ops.import_scene.fbx(filepath=fbx)
arms = [o for o in bpy.data.objects if o.type == "ARMATURE"]
ms = [o for o in bpy.data.objects if o.type == "MESH"]
check(len(arms) == 1 and sorted(arms[0].data.bones.keys()) == sorted(["ToolHolder", "R_Hand", "L_Hand", "R_Arm", "L_Arm"]),
      "SK_PlayerArms bones ToolHolder, R/L_Hand, R/L_Arm")
check(len(ms) == 1 and PA.TRI_BUDGET[0] <= tris(ms[0]) <= PA.TRI_BUDGET[1], f"SK_PlayerArms tris {tris(ms[0]) if ms else None}")
check(bool(ms) and skin_stats(ms[0], ["ToolHolder", "R_Hand", "L_Hand", "R_Arm", "L_Arm"])[0] == 0, "SK_PlayerArms unweighted 0")
for name, frames in PA.TAKES.items():
    hit = [a for a in bpy.data.actions if name in a.name.split("|")]
    check(bool(hit) and round(hit[0].frame_range[1] - hit[0].frame_range[0]) == frames, f"arms take {name} {frames} frames")
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, PA.BLEND_PATH))
rig = bpy.data.objects[PA.RIG_NAME]
def _close(a, b):
    return max(abs(x - y) for ra, rb in zip(a, b) for x, y in zip(ra, rb)) < 1e-5


check(_close(rig.matrix_world, T.RIG_MATRIX) and _close(rig.data.bones["ToolHolder"].matrix_local, Matrix.Identity(4)),
      "arms rig +90 X, ToolHolder identity (same frame as Anim_PlayerToolSwing)")

print(f"\n{len(fails)} FAIL(s)")
sys.exit(1 if fails else 0)
