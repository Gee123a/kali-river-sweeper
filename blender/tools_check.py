"""Build + validate KALI tools in isolation and optionally render a preview PNG.

    python blender/tools_check.py tool_01_sendok_makan_bengkok [trash_01_medical_bag ...] [--render OUT_DIR]
    python blender/tools_check.py --all [--render OUT_DIR]
Prints one line per tool: PASS/FAIL, tri count, issues. Exit code 1 if any FAIL.
"""
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else sys.argv[1:]

import bpy  # noqa: E402
from mathutils import Vector  # noqa: E402
from kali_blender import tools_common as tc  # noqa: E402
from kali_blender import trash_common as trc  # noqa: E402


def render(obj, path):
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE" if bpy.data.images else "MATERIAL"
    scene.render.resolution_x = scene.render.resolution_y = 512
    scene.render.film_transparent = False
    xs = [obj.matrix_world @ Vector(c) for c in obj.bound_box]
    centre = sum(xs, Vector()) / 8
    size = max((a - b).length for a in xs for b in xs)
    cam_data = bpy.data.cameras.new("PreviewCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = size * 1.15
    cam = bpy.data.objects.new("PreviewCam", cam_data)
    scene.collection.objects.link(cam)
    d = Vector((1.0, -1.0, 0.45)).normalized()
    cam.location = centre + d * (size * 3)
    cam.rotation_euler = (-d).to_track_quat("-Z", "Y").to_euler()
    scene.camera = cam
    # origin marker so the grip point is visible
    bpy.ops.mesh.primitive_uv_sphere_add(radius=size * 0.02, location=(0, 0, 0))
    marker = bpy.context.object
    mat = bpy.data.materials.new("GripMarker"); mat.diffuse_color = (1, 0, 1, 1)
    marker.data.materials.append(mat)
    scene.render.filepath = path
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(marker); bpy.data.objects.remove(cam)


def main():
    out_dir = None
    if "--render" in argv:
        out_dir = argv[argv.index("--render") + 1]
    names = (tc.TOOL_MODULES + trc.TRASH_MODULES) if "--all" in argv else \
        [a for a in argv if a.startswith(("tool_", "trash_"))]
    failed = 0
    specs = []
    for name in names:
        bpy.ops.wm.read_factory_settings(use_empty=True)
        try:
            if name.startswith("trash_"):
                mod = trc.load_trash_module(name)
                obj = trc.build_trash(name)
                issues = trc.validate_trash(obj, mod.SPEC)
                files, mat = trc.ATLAS_FILES, trc.MATERIAL_NAME
            else:
                mod = tc.load_tool_module(name)
                obj = tc.build_tool(name)
                issues = tc.validate_tool(obj, mod.SPEC)
                files, mat = tc.ATLAS_FILES, tc.MATERIAL_NAME
            specs.append(mod.SPEC)
            tris = tc.tri_count(obj)
            if out_dir:
                os.makedirs(out_dir, exist_ok=True)
                paths = tc.write_atlas_images([mod.SPEC], os.path.join(out_dir, "_tex_" + name), files)
                tc.wire_atlas_material(paths, mat)
                render(obj, os.path.join(out_dir, name + ".png"))
        except Exception as exc:  # report and keep going
            import traceback; traceback.print_exc()
            issues, tris = [f"EXCEPTION {type(exc).__name__}: {exc}"], -1
        status = "PASS" if not issues else "FAIL"
        failed += bool(issues)
        print(f"{status} {name} tris={tris} issues={issues}", flush=True)
    sys.exit(1 if failed else 0)


main()
