"""Build Wesley's environment meshes headlessly (Blender 5.3 / bpy wheel).

    python blender/wesley_env/build_env.py            # bpy 5.3 wheel
    blender -b -P blender/wesley_env/build_env.py     # Blender app, no GUI

Outputs (repo-relative):
    unity/Assets/_Project/Environment/Meshes/SM_Env_RiverValleyTerrain.fbx
    blender/SM_Env_Pack.blend
"""
import json
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
BLENDER_DIR = os.path.dirname(HERE)
ROOT = os.path.dirname(BLENDER_DIR)
sys.path.insert(0, BLENDER_DIR)

import bpy  # noqa: E402  (must be imported before bmesh / mathutils)
from kali_blender.export_fbx import FBX_SETTINGS  # noqa: E402  same settings as JC's exports
from wesley_env import terrain  # noqa: E402

MESH_DIR = os.path.join(ROOT, "unity", "Assets", "_Project", "Environment", "Meshes")
BLEND_PATH = os.path.join(BLENDER_DIR, "SM_Env_Pack.blend")


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def export(ob):
    bpy.ops.object.select_all(action="DESELECT")
    ob.select_set(True)
    bpy.context.view_layer.objects.active = ob
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)  # Ctrl+A > All Transforms
    os.makedirs(MESH_DIR, exist_ok=True)
    path = os.path.join(MESH_DIR, ob.name + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, **FBX_SETTINGS)
    return os.path.relpath(path, ROOT)


def main():
    reset_scene()
    report = []
    ob = terrain.build()
    info = terrain.stats(ob)
    info["fbx"] = export(ob)
    report.append(info)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
