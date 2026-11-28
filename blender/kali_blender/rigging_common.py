"""Shared helpers for the rigging stage (SK_VillagerNPC, Anim_PlayerToolSwing).

* MeshBuilder: low-poly lofts (superellipse rings) with per-ring bone weights and a palette
  swatch per face, turned into one Blender mesh.
* Palette atlas: one small flat-colour texture, every face UV'd to the centre of its swatch
  (one material, one draw call, recolour a villager by swapping the PNG).
* Pose keying in armature axes, NLA takes (one strip per take, so FBX take names are exact)
  and the animated FBX export.

Axes: characters face -Y in Blender (= Unity +Z after the -Z forward / Y up export), their left is +X.
"""
import math
import os

import bpy  # noqa: F401  (must be imported before bmesh / mathutils in the bpy wheel)
from mathutils import Euler, Matrix, Quaternion, Vector

from .export_fbx import FBX_SETTINGS, _select_only, apply_all_transforms

FBX_DIR = "unity/Assets/_Project/Rigging"
TEX_DIR = "unity/Assets/_Project/Rigging/Textures"
FPS = 30

# Animated exports: "Apply Transform" (bake_space_transform) is documented as broken with
# armatures + animation, so rigs keep the plain axis conversion; takes come from NLA strips
# (take name = strip name, no "Armature|" prefix).
ANIM_FBX_OVERRIDES = {
    "bake_space_transform": False,
    "object_types": {"ARMATURE", "MESH"},
    "use_armature_deform_only": False,     # keep the non-deform socket bones
    "bake_anim": True,
    "bake_anim_use_all_bones": True,
    "bake_anim_use_nla_strips": True,
    "bake_anim_use_all_actions": False,
    "bake_anim_force_startend_keying": True,
    "bake_anim_step": 1.0,
    "bake_anim_simplify_factor": 0.0,
}


# ------------------------------------------------------------------ palette
def hex_srgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4))


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


class Palette:
    """GRID x GRID swatches of SWATCH px. colors: list of (key, sRGB hex)."""
    GRID = 4
    SWATCH = 16

    def __init__(self, colors):
        if len(colors) > self.GRID * self.GRID:
            raise ValueError("palette has more swatches than the grid")
        self.colors = list(colors)
        self.index = {k: i for i, (k, _h) in enumerate(self.colors)}

    def uv(self, key):
        i = self.index[key]
        return ((i % self.GRID + 0.5) / self.GRID, (i // self.GRID + 0.5) / self.GRID)

    def write_png(self, path):
        size = self.GRID * self.SWATCH
        px = [0.0] * (size * size * 4)
        for i, (_k, h) in enumerate(self.colors):
            r, g, b = hex_srgb(h)
            x0, y0 = (i % self.GRID) * self.SWATCH, (i // self.GRID) * self.SWATCH
            for y in range(y0, y0 + self.SWATCH):
                for x in range(x0, x0 + self.SWATCH):
                    o = (y * size + x) * 4
                    px[o:o + 4] = (r, g, b, 1.0)
        os.makedirs(os.path.dirname(path), exist_ok=True)
        name = os.path.splitext(os.path.basename(path))[0]
        img = bpy.data.images.get(name) or bpy.data.images.new(name, size, size, alpha=False)
        img.pixels[:] = px
        img.filepath_raw = path
        img.file_format = "PNG"
        img.save()
        return img

    def material(self, name, image, roughness=0.8):
        mat = bpy.data.materials.get(name) or bpy.data.materials.new(name)
        mat.use_nodes = True
        nt = mat.node_tree
        bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
        tex = nt.nodes.new("ShaderNodeTexImage")
        tex.image = image
        tex.interpolation = "Closest"
        nt.links.new(tex.outputs["Color"], bsdf.inputs["Base Color"])
        bsdf.inputs["Roughness"].default_value = roughness
        bsdf.inputs["Metallic"].default_value = 0.0
        return mat


# ------------------------------------------------------------------ mesh building
def _se(c, p):
    """Superellipse term: sign(c) * |c|^(2/p)."""
    return math.copysign(abs(c) ** (2.0 / p), c)


def ring(center, axis, e1, r1, e2, r2, n, p=2.0, phase=0.0):
    """n points of a superellipse around `axis`, CCW seen from the tip of `axis`.

    e1/e2 are the cross-section axes with half sizes r1/r2. They are swapped if needed so
    that e1 x e2 points along `axis`, which keeps loft faces facing outward.
    """
    c, d, e1, e2 = Vector(center), Vector(axis), Vector(e1), Vector(e2)
    if e1.cross(e2).dot(d) < 0:
        e1, r1, e2, r2 = e2, r2, e1, r1
    pts = []
    for i in range(n):
        t = phase + 2 * math.pi * i / n
        pts.append(c + e1 * (r1 * _se(math.cos(t), p)) + e2 * (r2 * _se(math.sin(t), p)))
    return pts


class MeshBuilder:
    def __init__(self, palette):
        self.palette = palette
        self.verts, self.weights = [], []
        self.faces, self.fcol = [], []

    def vert(self, co, w):
        self.verts.append(Vector(co))
        self.weights.append(w(co) if callable(w) else dict(w))
        return len(self.verts) - 1

    def face(self, idx, col):
        self.faces.append(tuple(idx))
        self.fcol.append(col)

    def loft(self, rings, weights, cols, cap0=None, cap1=None):
        """rings: point lists (same n, ordered along the loft axis); weights: one per ring
        (dict or callable(co)); cols: one swatch key per band; cap0/cap1: swatch key or None."""
        ids = [[self.vert(p, w) for p in r] for r, w in zip(rings, weights)]
        n = len(ids[0])
        for k in range(len(ids) - 1):
            a, b = ids[k], ids[k + 1]
            for i in range(n):
                j = (i + 1) % n
                self.face((a[i], a[j], b[j], b[i]), cols[k])
        if cap0:
            self.face(ids[0][::-1], cap0)
        if cap1:
            self.face(ids[-1], cap1)
        return ids

    def fan(self, ring_ids, apex_co, w, col, flip=False):
        """Close a ring with a pole vertex (apex beyond the ring along the loft direction)."""
        a = self.vert(apex_co, w)
        n = len(ring_ids)
        for i in range(n):
            j = (i + 1) % n
            self.face((ring_ids[i], ring_ids[j], a) if not flip else (ring_ids[j], ring_ids[i], a), col)
        return a

    def build(self, name, material, bone_names):
        me = bpy.data.meshes.new(name)
        me.from_pydata([tuple(v) for v in self.verts], [], self.faces)
        me.update()
        uv = me.uv_layers.new(name="UVMap")
        for poly, key in zip(me.polygons, self.fcol):
            u = self.palette.uv(key)
            for li in poly.loop_indices:
                uv.data[li].uv = u
        me.materials.append(material)
        me.set_sharp_from_angle(angle=math.radians(50))
        obj = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(obj)
        if bone_names:
            groups = {b: obj.vertex_groups.new(name=b) for b in bone_names}
            for vi, w in enumerate(self.weights):
                tot = sum(w.values())
                for b, val in w.items():
                    if val > 0:
                        groups[b].add([vi], val / tot, "REPLACE")
        return obj


# ------------------------------------------------------------------ armature
def build_armature(name, bones, matrix_world=None):
    """bones: [(name, head, tail, parent, deform)], roll 0. Returns the armature object."""
    arm = bpy.data.armatures.new(name)
    obj = bpy.data.objects.new(name, arm)
    bpy.context.scene.collection.objects.link(obj)
    if matrix_world is not None:
        obj.matrix_world = matrix_world
    _select_only([obj])
    bpy.ops.object.mode_set(mode="EDIT")
    for bname, head, tail, parent, deform in bones:
        eb = arm.edit_bones.new(bname)
        eb.head, eb.tail, eb.roll = head, tail, 0.0
        eb.use_deform = deform
        if parent:
            eb.parent = arm.edit_bones[parent]
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.display_type = "STICK"
    for pb in obj.pose.bones:
        pb.rotation_mode = "QUATERNION"
    return obj


def local_quat(arm_obj, bone, deg_xyz, order="YXZ"):
    """Rotation given in armature axes (degrees, Euler `order`) -> pose-bone local quaternion.
    Applied in the bone's own (posed) frame, so a child's hinge axis follows its parent."""
    R = arm_obj.data.bones[bone].matrix_local.to_3x3()
    Q = Euler([math.radians(a) for a in deg_xyz], order).to_matrix()
    return (R.inverted() @ Q @ R).to_quaternion()


def local_offset(arm_obj, bone, vec):
    R = arm_obj.data.bones[bone].matrix_local.to_3x3()
    return R.inverted() @ Vector(vec)


def key_action(arm_obj, action_name, frames, pose_fn):
    """Create `action_name`, sample pose_fn(frame) -> {bone: (quat or None, loc or None)} on every
    frame (quaternion signs kept continuous) and leave it as a muted-free NLA strip of its own."""
    ad = arm_obj.animation_data or arm_obj.animation_data_create()
    act = bpy.data.actions.new(action_name)
    act.use_fake_user = True
    ad.action = act
    prev = {}
    for f in range(frames + 1):
        for bname, (q, loc) in pose_fn(f).items():
            pb = arm_obj.pose.bones[bname]
            if q is not None:
                q = Quaternion(q)
                if bname in prev and q.dot(prev[bname]) < 0:
                    q.negate()
                prev[bname] = q
                pb.rotation_quaternion = q
                pb.keyframe_insert("rotation_quaternion", frame=f, group=bname)
            if loc is not None:
                pb.location = loc
                pb.keyframe_insert("location", frame=f, group=bname)
    ad.action = None
    track = ad.nla_tracks.new()
    track.name = action_name
    strip = track.strips.new(action_name, 0, act)
    strip.name = action_name
    if hasattr(strip, "action_slot") and act.slots:
        strip.action_slot = act.slots[0]
    for pb in arm_obj.pose.bones:      # back to rest
        pb.rotation_quaternion = (1, 0, 0, 0)
        pb.location = (0, 0, 0)
    return act


def action_fcurves(act):
    """All F-Curves of a (slotted, Blender 4.4+) action."""
    return [fc for layer in act.layers for strip in layer.strips for bag in strip.channelbags for fc in bag.fcurves]


def set_take(arm_obj, take):
    """Solo one NLA take (for previews / renders); take=None plays nothing (rest pose)."""
    for tr in arm_obj.animation_data.nla_tracks:
        tr.mute = tr.name != take
    arm_obj.animation_data.action = None


def unmute_all(arm_obj):
    for tr in arm_obj.animation_data.nla_tracks:
        tr.mute = False


# ------------------------------------------------------------------ interpolation
def hermite_keys(keys, f):
    """keys: [(frame, value tuple)], C1 Catmull-Rom style through every key, zero slope at the ends."""
    if f <= keys[0][0]:
        return keys[0][1]
    if f >= keys[-1][0]:
        return keys[-1][1]
    k = max(i for i in range(len(keys) - 1) if keys[i][0] <= f)
    (t0, p0), (t1, p1) = keys[k], keys[k + 1]

    def slope(i):
        if i == 0 or i == len(keys) - 1:
            return [0.0] * len(keys[i][1])
        (ta, pa), (tb, pb) = keys[i - 1], keys[i + 1]
        return [(b - a) / (tb - ta) for a, b in zip(pa, pb)]
    m0, m1 = slope(k), slope(k + 1)
    h = t1 - t0
    s = (f - t0) / h
    h00, h10, h01, h11 = 2 * s**3 - 3 * s**2 + 1, s**3 - 2 * s**2 + s, -2 * s**3 + 3 * s**2, s**3 - s**2
    return tuple(h00 * a + h10 * h * ma + h01 * b + h11 * h * mb for a, b, ma, mb in zip(p0, p1, m0, m1))


# ------------------------------------------------------------------ export
def export_animated(arm_obj, mesh_objs, filepath, apply_transforms=True):
    from .export_fbx import _fbx_export
    objs = [arm_obj] + list(mesh_objs)
    if apply_transforms:
        apply_all_transforms(objs)
    unmute_all(arm_obj)
    _select_only(objs)
    return _fbx_export(filepath, **ANIM_FBX_OVERRIDES)


def take_names_in_fbx(filepath):
    """AnimStack names written in a binary FBX (read straight from the file, no importer naming)."""
    import re
    data = open(filepath, "rb").read()
    names = re.findall(rb"([A-Za-z0-9_]+)\x00\x01AnimStack", data)
    return sorted({n.decode() for n in names})


def unity_to_blender_vec(u):
    """Unity (x right, y up, z forward) -> Blender (character/camera facing -Y)."""
    return Vector((-u[0], -u[2], u[1]))


_F = Matrix(((-1, 0, 0), (0, 0, 1), (0, -1, 0)))   # Blender -> Unity direction map


def unity_euler_matrix(deg_xyz):
    """Unity Quaternion.Euler(x, y, z) as a 3x3 matrix in Unity axes (applied Z, then X, then Y)."""
    x, y, z = (math.radians(a) for a in deg_xyz)
    return Matrix.Rotation(y, 3, "Y") @ Matrix.Rotation(x, 3, "X") @ Matrix.Rotation(z, 3, "Z")
