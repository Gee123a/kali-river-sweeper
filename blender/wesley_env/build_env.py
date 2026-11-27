"""Build Wesley's environment meshes headlessly (Blender 5.3 / bpy wheel).

    blender -b -P blender/wesley_env/build_env.py                      # everything
    blender -b -P blender/wesley_env/build_env.py -- pintu_air         # only re-export these FBX
    blender -b -P blender/wesley_env/build_env.py -- textures          # only regenerate textures

Every mesh is always rebuilt into blender/SM_Env_Pack.blend; only the selected assets are
re-exported (FBX files embed a timestamp, so untouched assets keep a clean git diff).

Outputs (repo-relative):
    unity/Assets/_Project/Environment/Meshes/SM_Env_*.fbx
    unity/Assets/_Project/Environment/Textures/T_Env_*.png
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
from wesley_env import gunung_sampah, jembatan, pintu_air, terrain, textures, trash_pieces  # noqa: E402

ENV_DIR = os.path.join(ROOT, "unity", "Assets", "_Project", "Environment")
MESH_DIR = os.path.join(ENV_DIR, "Meshes")
TEX_DIR = os.path.join(ENV_DIR, "Textures")
BLEND_PATH = os.path.join(BLENDER_DIR, "SM_Env_Pack.blend")

ASSETS = {
    "terrain": terrain,
    "pintu_air": pintu_air,
    "gunung_sampah": gunung_sampah,
    "jembatan": jembatan,
    "trash_pieces": trash_pieces,
}


def reset_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    bpy.context.scene.unit_settings.system = "METRIC"
    bpy.context.scene.unit_settings.scale_length = 1.0


def export(obs, name):
    """Export one object (or a list of objects) into <name>.fbx."""
    obs = obs if isinstance(obs, list) else [obs]
    bpy.ops.object.select_all(action="DESELECT")
    for ob in obs:
        ob.select_set(True)
    bpy.context.view_layer.objects.active = obs[0]
    bpy.ops.object.transform_apply(location=True, rotation=True, scale=True)  # Ctrl+A > All Transforms
    os.makedirs(MESH_DIR, exist_ok=True)
    path = os.path.join(MESH_DIR, name + ".fbx")
    bpy.ops.export_scene.fbx(filepath=path, **FBX_SETTINGS)
    return os.path.relpath(path, ROOT)


def main():
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    selected = set(args) or set(ASSETS) | {"textures"}
    reset_scene()
    report = []
    if "textures" in selected:
        report.append({"textures": [os.path.relpath(p, ROOT) for p in textures.build_all(TEX_DIR)]})
    for key, module in ASSETS.items():
        ob = module.build()
        info = module.stats(ob)
        if key in selected:
            info["fbx"] = export(ob, module.NAME)
        report.append(info)
    bpy.ops.wm.save_as_mainfile(filepath=BLEND_PATH)
    print(json.dumps(report, indent=2))


if __name__ == "__main__":
    main()
