"""QA renders for the rigging stage (run after build_all.py --only rigging):

    blender -b --factory-startup -P blender/tests/render_rigging_qa.py -- OUT_DIR

Writes villager_front/side/34/tpose.png, villager_strip_<Take>.png (4 frames each, the thrown bag
follows a ballistic arc after RELEASE_FRAME) and toolswing_strip_<Take>.png (real SM_Tool_* meshes on
ToolHolder, placed like KaliPlayerController does). Nothing in the repo is written.
Optional second dir: npc_strip_<Take>.png for every villager_clips take, variants_lineup.png (Task 6C
quest givers) and fparms_<Take>.png (SK_PlayerArms seen from the player camera) go there.
"""
import math
import os
import sys

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
sys.path.insert(0, os.path.join(REPO, "blender"))
import bpy  # noqa: E402
import numpy as np  # noqa: E402
from mathutils import Matrix, Vector  # noqa: E402

from kali_blender import rigging_common as rc  # noqa: E402
from kali_blender import tool_swing as T  # noqa: E402
from kali_blender import villager as V  # noqa: E402
from kali_blender import villager_clips as C  # noqa: E402
from kali_blender import villager_variants as VV  # noqa: E402
from kali_blender import player_arms as PA  # noqa: E402

OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else os.path.join(REPO, "qa_out")
os.makedirs(OUT, exist_ok=True)
_args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
CLIPS_OUT = os.path.abspath(_args[1]) if len(_args) > 1 else OUT
os.makedirs(CLIPS_OUT, exist_ok=True)


def setup_render(w, h):
    sc = bpy.context.scene
    for eng in ("BLENDER_EEVEE", "BLENDER_EEVEE_NEXT"):
        try:
            sc.render.engine = eng
            break
        except TypeError:
            pass
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.film_transparent = False
    try:
        sc.eevee.taa_render_samples = 16
    except AttributeError:
        pass
    sc.view_settings.view_transform = "Standard"
    world = sc.world or bpy.data.worlds.new("W")
    sc.world = world
    world.use_nodes = True
    bg = next(n for n in world.node_tree.nodes if n.type == "BACKGROUND")
    bg.inputs["Color"].default_value = (0.55, 0.60, 0.66, 1)
    bg.inputs["Strength"].default_value = 0.9
    sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
    sun.data.energy = 3.5
    sun.data.angle = math.radians(8)
    sun.rotation_euler = (math.radians(50), math.radians(-15), math.radians(-30))
    sc.collection.objects.link(sun)


def add_plane(z, size, color):
    me = bpy.data.meshes.new("Ground")
    s = size / 2
    me.from_pydata([(-s, -s, z), (s, -s, z), (s, s, z), (-s, s, z)], [], [(0, 1, 2, 3)])
    mat = bpy.data.materials.new("GroundMat")
    mat.use_nodes = True
    b = next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED")
    b.inputs["Base Color"].default_value = color
    b.inputs["Roughness"].default_value = 0.9
    me.materials.append(mat)
    ob = bpy.data.objects.new("Ground", me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def camera(loc, target, lens=50, ortho=None):
    cam = bpy.data.objects.get("QACam")
    if cam is None:
        cam = bpy.data.objects.new("QACam", bpy.data.cameras.new("QACam"))
        bpy.context.scene.collection.objects.link(cam)
    cam.location = loc
    cam.rotation_euler = (Vector(target) - Vector(loc)).to_track_quat("-Z", "Y").to_euler()
    cam.data.lens = lens
    cam.data.type = "ORTHO" if ortho else "PERSP"
    if ortho:
        cam.data.ortho_scale = ortho
    bpy.context.scene.camera = cam


def rest(rig):
    """Mute every take AND clear the pose (muting leaves the last evaluated pose on the bones)."""
    rc.set_take(rig, None)
    for pb in rig.pose.bones:
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    bpy.context.view_layer.update()


def render(path):
    bpy.context.scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    return path


def strip(paths, out):
    imgs = []
    for p in paths:
        im = bpy.data.images.load(p)
        w, h = im.size
        imgs.append(np.array(im.pixels[:], dtype=np.float32).reshape(h, w, 4))
        bpy.data.images.remove(im)
    gap = np.ones((imgs[0].shape[0], 6, 4), dtype=np.float32)
    row = np.concatenate(sum(([a, gap] for a in imgs), [])[:-1], axis=1)
    h, w = row.shape[:2]
    im = bpy.data.images.new(os.path.basename(out), w, h)
    im.pixels[:] = row.ravel()
    im.filepath_raw = out
    im.file_format = "PNG"
    im.save()
    for p in paths:
        os.remove(p)
    print("wrote", out)


# ------------------------------------------------------------------ villager
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, V.BLEND_PATH))
setup_render(520, 640)
add_plane(0.0, 8, (0.42, 0.36, 0.28, 1))
sc = bpy.context.scene
rig = bpy.data.objects[V.RIG_NAME]
bag, bin_obj = bpy.data.objects[V.PROP_BAG], bpy.data.objects[V.PROP_BIN]
rod = bpy.data.objects[V.PROP_ROD]
ground = bpy.data.objects["Ground"]


def show(*objs):
    for o in (bag, bin_obj, rod):
        o.hide_render = o not in objs


show()
rc.set_take(rig, "Idle")
sc.frame_set(0)
views = {"front": ((0, -6, 0.78), 1.75), "side": ((6, 0, 0.78), 1.75)}
for name, (loc, scale) in views.items():
    camera(loc, (0, 0, 0.78), ortho=scale)
    render(os.path.join(OUT, f"villager_{name}.png"))
camera((-2.3, -3.2, 1.6), (0, 0, 0.75), lens=55)
render(os.path.join(OUT, "villager_34.png"))
rest(rig)
camera((0, -6, 0.78), (0, 0, 0.78), ortho=1.75)
sc.render.resolution_x = 760
render(os.path.join(OUT, "villager_tpose.png"))
sc.render.resolution_x = 520

frames = {"Idle": [0, 19, 38, 56], "ThrowTrash": [0, 9, 16, 26], "CarryBin": [0, 8, 15, 23]}
cams = {"Idle": ((-2.3, -3.2, 1.6), (0, 0, 0.75)), "ThrowTrash": ((-2.6, -2.9, 1.5), (0, -0.25, 0.8)),
        "CarryBin": ((-3.4, -1.3, 1.2), (0, -0.05, 0.7))}
for take, fl in frames.items():
    rc.set_take(rig, take)
    show(bag) if take == "ThrowTrash" else show(bin_obj) if take == "CarryBin" else show()
    camera(*cams[take], lens=55)
    flight = None
    if take == "ThrowTrash":
        sc.frame_set(V.RELEASE_FRAME - 1)
        p0 = bag.matrix_world.translation.copy()
        sc.frame_set(V.RELEASE_FRAME)
        m_rel = bag.matrix_world.copy()
        flight = (m_rel, (m_rel.translation - p0) * rc.FPS)
    paths = []
    for f in fl:
        sc.frame_set(f)
        if flight and f > V.RELEASE_FRAME:
            dt = (f - V.RELEASE_FRAME) / rc.FPS
            m_rel, vel = flight
            pos = m_rel.translation + vel * dt + Vector((0, 0, -4.9 * dt * dt))
            bag.parent = None
            bag.matrix_world = Matrix.Translation(pos) @ Matrix.Rotation(-6 * dt, 4, "X") @ m_rel.to_3x3().to_4x4()
        paths.append(render(os.path.join(OUT, f"_tmp_{take}_{f}.png")))
    strip(paths, os.path.join(OUT, f"villager_strip_{take}.png"))
    if take == "ThrowTrash":       # back on the hand for later takes
        V.attach_props(rig, bag, bin_obj)

# ------------------------------------------------------------------ ambient NPC takes
def box(name, x0, x1, y0, y1, z0, z1, color):
    me = bpy.data.meshes.new(name)
    v = [(x, y, z) for z in (z0, z1) for y in (y0, y1) for x in (x0, x1)]
    me.from_pydata(v, [], [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)])
    mat = bpy.data.materials.new(name + "Mat")
    mat.use_nodes = True
    next(n for n in mat.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = color
    me.materials.append(mat)
    ob = bpy.data.objects.new(name, me)
    sc.collection.objects.link(ob)
    return ob


WOOD, STONE, WATER = (0.36, 0.24, 0.14, 1), (0.45, 0.44, 0.42, 1), (0.13, 0.33, 0.33, 1)
far = ((-2.9, -3.4, 1.5), (0, -0.55, 0.55))
near = ((-2.2, -2.6, 1.3), (0, -0.1, 0.6))
side = ((-3.0, -1.3, 1.1), (0, -0.1, 0.55))
clip_shots = {  # take: frames, camera, show rod, stage (boxes), ground visible
    "Anim_Fisher_SittingCast": ([0, 32, 38, 46], far, True, [("Jetty", -0.6, 0.6, -0.14, 0.7, 0.32, 0.42, WOOD),
                                                          ("River", -4, 4, -6, -0.14, -0.6, -0.5, WATER)], False),
    "Anim_Fisher_SittingIdle": ([0, 22, 45, 67], far, True, [("Jetty", -0.6, 0.6, -0.14, 0.7, 0.32, 0.42, WOOD),
                                                          ("River", -4, 4, -6, -0.14, -0.6, -0.5, WATER)], False),
    "Anim_Fisher_StandingIdle": ([0, 22, 45, 67], far, True, [], True),
    "Anim_Washer_CrouchedScrub": ([0, 4, 8, 12], near, False, [("Step", -0.5, 0.5, -0.62, 0.4, 0.0, 0.215, STONE)], True),
    "Anim_Kid_WadeShallow": ([0, 15, 30, 45], side, False, [("Water", -4, 4, -4, 4, 0.0, 0.22, WATER)], True),
    "Anim_Kid_Splash": ([0, 7, 11, 31], near, False, [("Water", -4, 4, -4, 4, 0.0, 0.30, WATER)], True),
    "Anim_Kid_JettyJump": ([8, 21, 33, 50], side, False, [], True),
    "Anim_Chatter_TalkingIdle": ([0, 20, 40, 75], near, False, [], True),
    "Talk_Gesture": ([0, 18, 37, 56], near, False, [], True),
    "Wave": ([0, 4, 11, 19], near, False, [], True),
    "Point_Forward": ([0, 12, 30, 52], near, False, [], True),
    "Cheer_Clap": ([0, 3, 5, 8], near, False, [], True),
    "Call_Out": ([0, 7, 15, 45], near, False, [], True),
    "Kid_Run": ([0, 5, 10, 15], side, False, [], True),
    "Kid_Celebrate": ([0, 6, 11, 17], near, False, [], True),
}
for name in list(VV.BODIES) + list(VV.ACCESSORIES):     # base villager only for the clip strips
    bpy.data.objects[name].hide_render = True
for take, (fl, cam, with_rod, stage, ground_on) in clip_shots.items():
    rest(rig)
    show(rod) if with_rod else show()
    ground.hide_render = not ground_on
    made = [box(*b) for b in stage]
    rc.set_take(rig, take)
    camera(*cam, lens=50)
    paths = []
    for f in fl:
        sc.frame_set(f)
        paths.append(render(os.path.join(CLIPS_OUT, f"_tmp_{take}_{f}.png")))
    strip(paths, os.path.join(CLIPS_OUT, f"npc_strip_{take}.png"))
    for o in made:
        bpy.data.objects.remove(o)
ground.hide_render = False

# quest-giver lineup: body variant + accessory + per-NPC palette, Idle frame 0
rest(rig)
show()
rc.set_take(rig, "Idle")
sc.frame_set(0)
main_body = bpy.data.objects[V.NAME]
bodies = [main_body] + [bpy.data.objects[n] for n in VV.BODIES]
accs = [bpy.data.objects[n] for n in VV.ACCESSORIES]
camera((-1.7, -3.6, 1.2), (0, 0, 0.72), lens=50)
paths = []
for npc, (body_name, acc_name, _over, scale) in VV.RECIPES.items():
    img = bpy.data.images.load(os.path.join(REPO, VV.png_path(npc)))
    mat = bpy.data.materials[V.MATERIAL].copy()
    next(n for n in mat.node_tree.nodes if n.type == "TEX_IMAGE").image = img
    for o in bodies + accs:
        o.hide_render = o.name not in (body_name, acc_name)
        o.hide_set(False)
        o.data.materials[0] = mat
    rig.scale = (scale,) * 3
    sc.frame_set(0)
    paths.append(render(os.path.join(CLIPS_OUT, f"_tmp_variant_{npc}.png")))
strip(paths, os.path.join(CLIPS_OUT, "variants_lineup.png"))

# ------------------------------------------------------------------ first-person arms
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, PA.BLEND_PATH))
setup_render(640, 400)
add_plane(0.35, 40, (0.16, 0.36, 0.34, 1))
sc = bpy.context.scene
rig = bpy.data.objects[PA.RIG_NAME]
eye = Vector((0, 0, 1.6))
rig.matrix_world = Matrix.Translation(eye + rc.unity_to_blender_vec(T.SOCKET_IN_CAMERA)) @ T.RIG_MATRIX
cam = bpy.data.objects.new("FPCam", bpy.data.cameras.new("FPCam"))
sc.collection.objects.link(cam)
cam.location = eye
cam.rotation_euler = (math.radians(90), 0, math.radians(180))      # looks along -Y (Unity +Z), up +Z
cam.data.sensor_fit = "VERTICAL"
cam.data.angle = math.radians(60)                                  # Unity Main Camera fov 60 (vertical)
sc.camera = cam
fp_shots = {"Idle_Hold": ("SM_Tool_SerokanWaring3m", [0, 15, 30, 45]),
            "SerokanScoop": ("SM_Tool_SerokanWaring3m", [0, 5, 12, 20]),
            "GancoHookSwing": ("SM_Tool_GancoBesi1Mata", [0, 6, 10, 17])}
for take, (tool_name, fl) in fp_shots.items():
    rest(rig)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, "unity/Assets/_Project/Props/Tools/Meshes", tool_name + ".fbx"))
    tool = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
    bpy.ops.object.select_all(action="DESELECT")
    tool.select_set(True)
    bpy.context.view_layer.objects.active = tool
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    holder = rig.data.bones["ToolHolder"]
    holder_rest = rig.matrix_world @ holder.matrix_local
    tool.parent = rig
    tool.parent_type = "BONE"
    tool.parent_bone = "ToolHolder"
    tool.matrix_world = T.tool_world(holder_rest)
    rc.set_take(rig, take)
    paths = []
    for f in fl:
        sc.frame_set(f)
        paths.append(render(os.path.join(CLIPS_OUT, f"_tmp_fp_{take}_{f}.png")))
    strip(paths, os.path.join(CLIPS_OUT, f"fparms_{take}.png"))
    bpy.data.objects.remove(tool)

# ------------------------------------------------------------------ tool swing
bpy.ops.wm.open_mainfile(filepath=os.path.join(REPO, T.BLEND_PATH))
setup_render(560, 520)
add_plane(0.35, 30, (0.16, 0.36, 0.34, 1))         # water below the boat-deck eye line
sc = bpy.context.scene
rig = bpy.data.objects[T.RIG_NAME]
eye = Vector((0, 0, 1.6))
rig.matrix_world = Matrix.Translation(eye + rc.unity_to_blender_vec(T.SOCKET_IN_CAMERA)) @ T.RIG_MATRIX
me = bpy.data.meshes.new("Eye")
import bmesh  # noqa: E402
bm = bmesh.new()
bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=8, radius=0.11)
bmesh.ops.create_cone(bm, cap_ends=True, segments=8, radius1=0.05, radius2=0.0, depth=0.18,
                      matrix=Matrix.Translation((0, -0.17, 0)) @ Matrix.Rotation(math.radians(90), 4, "X"))
bm.to_mesh(me)
eye_ob = bpy.data.objects.new("EyeMarker", me)
eye_ob.location = eye
sc.collection.objects.link(eye_ob)
tool_files = {"SerokanScoop": "SM_Tool_SerokanWaring3m", "GancoHookSwing": "SM_Tool_GancoBesi1Mata"}
frames = {"SerokanScoop": [0, 5, 12, 15, 20], "GancoHookSwing": [0, 6, 10, 12, 17]}
for take, tool_name in tool_files.items():
    rest(rig)
    before = set(bpy.data.objects)
    bpy.ops.import_scene.fbx(filepath=os.path.join(REPO, "unity/Assets/_Project/Props/Tools/Meshes", tool_name + ".fbx"))
    tool = next(o for o in bpy.data.objects if o not in before and o.type == "MESH")
    bpy.ops.object.select_all(action="DESELECT")
    tool.select_set(True)
    bpy.context.view_layer.objects.active = tool
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)
    holder_rest = rig.matrix_world @ rig.data.bones[T.BONE].matrix_local
    tool.parent = rig
    tool.parent_type = "BONE"
    tool.parent_bone = T.BONE
    tool.matrix_world = T.tool_world(holder_rest)
    tool.data.materials.clear()          # flat stand-in colour (the atlas is not needed to read the motion)
    tm = bpy.data.materials.new("ToolStandIn")
    tm.use_nodes = True
    next(n for n in tm.node_tree.nodes if n.type == "BSDF_PRINCIPLED").inputs["Base Color"].default_value = (0.35, 0.2, 0.08, 1)
    tool.data.materials.append(tm)
    rc.set_take(rig, take)
    camera((-2.6, 1.4, 2.4), (-0.4, -1.3, 1.0), lens=32)
    paths = []
    for f in frames[take]:
        sc.frame_set(f)
        paths.append(render(os.path.join(OUT, f"_tmp_{take}_{f}.png")))
    strip(paths, os.path.join(OUT, f"toolswing_strip_{take}.png"))
    bpy.data.objects.remove(tool)
print("QA RENDERS DONE")
