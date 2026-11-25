"""One-command build for the KALI Blender assets (excavator + 20 tools).

    /opt/bpyenv/bin/python blender/build_all.py [--only excavator|tools] [--repo ROOT]
    blender -b -P blender/build_all.py -- [--only excavator|tools] [--repo ROOT]
    Blender GUI: open this file in the Text Editor (saved, so __file__ is known) and press Run Script.

Outputs (paths relative to the repo root):
    excavator: S.BLEND_PATH, S.FBX_PATH
    tools:     tools_common.FBX_DIR/<SPEC name>.fbx, TEX_DIR textures, tools_common.BLEND_PATH
    report:    blender/build_report.json
Exit code 1 if any asset failed.
"""
import argparse
import datetime
import json
import os
import sys
import traceback

HERE = os.path.dirname(os.path.abspath(globals().get("__file__", os.path.join(os.getcwd(), "blender", "x"))))
sys.path.insert(0, HERE)

import bpy  # noqa: E402  (must be imported before bmesh / mathutils)
from kali_blender import excavator_spec as S  # noqa: E402
from kali_blender import tools_common as tc  # noqa: E402
from kali_blender.export_fbx import export_excavator, export_tool, verify_fbx  # noqa: E402

DEFAULT_ROOT = os.path.dirname(HERE)


def _argv():
    if "--" in sys.argv:
        return sys.argv[sys.argv.index("--") + 1:]
    return sys.argv[1:]


def _reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def _save_blend(path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=path)


def _rel(root, path):
    return os.path.relpath(path, root).replace(os.sep, "/")


def build_excavator(root, report):
    fbx_abs = os.path.join(root, S.FBX_PATH)
    blend_abs = os.path.join(root, S.BLEND_PATH)
    entry = {"asset": S.MESH_NAME, "kind": "excavator", "status": "FAIL", "tris": None,
             "issues": [], "error": None, "fbx": _rel(root, fbx_abs), "blend": _rel(root, blend_abs),
             "bones": [], "meshes": []}
    report["assets"].append(entry)
    try:
        from kali_blender.excavator_rig import build_rig
        from kali_blender.excavator_mesh import build_mesh
        _reset()
        rig = build_rig()
        mesh = build_mesh(rig)
        _save_blend(blend_abs)
        export_excavator(rig, mesh, fbx_abs)
        expected_bones = [name for (name, _h, _t, _p, deform) in S.BONES if deform]
        info = verify_fbx(fbx_abs, expected_bones=expected_bones, expected_meshes=[S.MESH_NAME])
        entry["bones"], entry["meshes"] = info["bones"], info["meshes"]
        entry["tris"] = tc.tri_count(mesh)
        lo, hi = S.TRI_BUDGET
        if not lo <= entry["tris"] <= hi:
            entry["issues"].append(f"tris {entry['tris']} outside budget {lo}-{hi}")
        entry["status"] = "FAIL" if entry["issues"] else "PASS"
        print(f"excavator: {entry['tris']} tris, {len(info['bones'])} deform bones")
    except Exception as exc:  # report and keep going
        traceback.print_exc()
        entry["error"] = f"{type(exc).__name__}: {exc}"
    return entry


def _layer_collection(layer, name):
    if layer.collection.name == name:
        return layer
    for child in layer.children:
        found = _layer_collection(child, name)
        if found is not None:
            return found
    return None


def _discard_collection(coll):
    for obj in list(coll.objects):
        bpy.data.objects.remove(obj, do_unlink=True)
    bpy.data.collections.remove(coll)


def build_tools(root, report):
    _reset()
    scene = bpy.context.scene
    specs = []            # every SPEC that loaded (drives the atlas, even if a build failed)
    built = []            # (grid slot, spec name, collection) for tools kept in the pack
    tex_dir = os.path.join(root, tc.TEX_DIR)
    for slot, mod_name in enumerate(tc.TOOL_MODULES):
        entry = {"asset": mod_name, "kind": "tool", "status": "FAIL", "tris": None, "issues": [],
                 "error": None, "fbx": None}
        report["assets"].append(entry)
        coll = None
        spec = None
        try:
            spec = tc.load_tool_module(mod_name).SPEC
            specs.append(spec)
            entry["asset"] = spec["name"]
            coll = bpy.data.collections.new(spec["name"])
            scene.collection.children.link(coll)
            obj = tc.build_tool(mod_name, collection=coll)
            entry["issues"] = tc.validate_tool(obj, spec)
            entry["tris"] = tc.tri_count(obj)
            fbx_abs = os.path.join(root, tc.FBX_DIR, spec["name"] + ".fbx")
            export_tool(obj, fbx_abs)
            entry["fbx"] = _rel(root, fbx_abs)
            verify_fbx(fbx_abs, expected_meshes=[spec["name"]])
            entry["status"] = "FAIL" if entry["issues"] else "PASS"
            built.append((slot, spec["name"], coll))
        except Exception as exc:  # broken / missing module: FAIL, keep looping
            traceback.print_exc()
            entry["error"] = f"{type(exc).__name__}: {exc}"
            if coll is not None:
                _discard_collection(coll)
        print(f"{entry['status']} {entry['asset']} tris={entry['tris']} issues={entry['issues']} "
              f"error={entry['error']}", flush=True)

    atlas = {"status": "FAIL", "paths": {}, "error": None}
    report["atlas"] = atlas
    try:
        paths = tc.write_atlas_images(specs, tex_dir)
        tc.wire_atlas_material(paths)
        atlas["paths"] = {k: _rel(root, v) for k, v in paths.items()}
        atlas["status"] = "PASS"
    except Exception as exc:
        traceback.print_exc()
        atlas["error"] = f"{type(exc).__name__}: {exc}"

    # Browsable pack: tool collections excluded from the view layer, instanced on a 5x4 grid.
    preview = bpy.data.collections.new("Tools_Preview")
    scene.collection.children.link(preview)
    for slot, name, coll in built:
        col, row = slot % tc.ATLAS_COLS, slot // tc.ATLAS_COLS
        inst = bpy.data.objects.new("PREVIEW_" + name, None)
        inst.instance_type = "COLLECTION"
        inst.instance_collection = coll
        inst.location = (col * 1.0, -row * 1.0, 0.0)
        preview.objects.link(inst)
        lc = _layer_collection(bpy.context.view_layer.layer_collection, coll.name)
        if lc is not None:
            lc.exclude = True
    blend_abs = os.path.join(root, tc.BLEND_PATH)
    _save_blend(blend_abs)
    report["tools_blend"] = _rel(root, blend_abs)
    return report


def _print_table(report):
    rows = [("ASSET", "KIND", "STATUS", "TRIS", "DETAIL")]
    for a in report["assets"]:
        detail = a["error"] or "; ".join(a["issues"]) or ""
        rows.append((a["asset"], a["kind"], a["status"],
                     "-" if a["tris"] is None else str(a["tris"]), detail[:90]))
    if "atlas" in report:
        at = report["atlas"]
        rows.append(("atlas", "texture", at["status"], "-", at["error"] or ""))
    widths = [max(len(str(r[i])) for r in rows) for i in range(5)]
    print()
    for r in rows:
        print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)).rstrip())
    print()


def main():
    parser = argparse.ArgumentParser(description="Build KALI excavator and tool assets.")
    parser.add_argument("--only", choices=["excavator", "tools"], default=None)
    parser.add_argument("--repo", default=DEFAULT_ROOT, help="repo root (default: parent of blender/)")
    args = parser.parse_args(_argv())
    root = os.path.abspath(args.repo)

    report = {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "repo": root,
        "blender_version": bpy.app.version_string,
        "only": args.only,
        "assets": [],
    }
    if args.only in (None, "excavator"):
        build_excavator(root, report)
    if args.only in (None, "tools"):
        build_tools(root, report)

    failed = any(a["status"] != "PASS" for a in report["assets"]) or \
        report.get("atlas", {}).get("status", "PASS") != "PASS"
    report["status"] = "FAIL" if failed else "PASS"
    report_path = os.path.join(root, "blender", "build_report.json")
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    _print_table(report)
    print(f"report: {report_path}")
    print("BUILD " + report["status"])
    if bpy.app.background:
        sys.exit(1 if failed else 0)


main()
