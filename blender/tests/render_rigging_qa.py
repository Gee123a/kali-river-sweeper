"""QA renders for the rigging stage (run after build_all.py --only rigging):

    blender -b --factory-startup -P blender/tests/render_rigging_qa.py -- OUT_DIR

Writes villager_front/side/34/tpose.png, villager_strip_<Take>.png (4 frames each, the thrown bag
follows a ballistic arc after RELEASE_FRAME) and toolswing_strip_<Take>.png (real SM_Tool_* meshes on
ToolHolder, placed like KaliPlayerController does). Nothing in the repo is written.
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

OUT = os.path.abspath(sys.argv[sys.argv.index("--") + 1]) if "--" in sys.argv else os.path.join(REPO, "qa_out")
os.makedirs(OUT, exist_ok=True)


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


def show(*objs):
    for o in (bag, bin_obj):
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
