"""One-command build for the KALI Blender assets (excavator + 20 tools + trash props + clean products + rigging).

    /opt/bpyenv/bin/python blender/build_all.py [--only excavator|tools|trash|products|equipment|rigging] [--repo ROOT]
    blender -b --factory-startup -P blender/build_all.py -- [--only excavator|tools|trash|products|equipment|rigging] [--repo ROOT]
    Blender GUI: open this file in the Text Editor (saved, so __file__ is known) and press Run Script.

Outputs (paths relative to the repo root):
    excavator: S.BLEND_PATH, S.FBX_PATH (unity/Assets/_Project/Rigging/)
    tools:     tools_common.FBX_DIR/<SPEC name>.fbx, TEX_DIR textures, tools_common.BLEND_PATH
    trash:     trash_common.FBX_DIR/<SPEC name>.fbx, TEX_DIR textures, trash_common.BLEND_PATH
    products:  products_common.FBX_DIR/<SPEC name>.fbx, TEX_DIR textures, products_common.BLEND_PATH
    equipment: equipment_common.FBX_DIR/<SPEC name>.fbx, TEX_DIR textures (+ Emission), equipment_common.BLEND_PATH
    rigging:   unity/Assets/_Project/Rigging/{SK_VillagerNPC,SM_Villager_TrashBag,SM_Villager_Bin,SM_Villager_FishingRod,
               Anim_PlayerToolSwing,SK_PlayerArms,SK_VillagerNPC_{Bare,Sarung},SM_Villager_Hat_*,SM_Villager_Hair_Konde}.fbx,
               Rigging/Textures/T_Villager_Palette[_<Npc>].png, T_PlayerArms_Palette.png, blender/SK_PlayerArms.blend,
               blender/SK_VillagerNPC.blend, blender/Anim_PlayerToolSwing.blend
    report:    blender/build_report.json (repo-relative paths only)
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
from kali_blender import trash_common as trc  # noqa: E402
from kali_blender import products_common as pc  # noqa: E402
from kali_blender import bundles_common as bc  # noqa: E402
from kali_blender import equipment_common as ec  # noqa: E402
from kali_blender.export_fbx import export_excavator, export_tool, verify_fbx  # noqa: E402

DEFAULT_ROOT = os.path.dirname(HERE)
STAGES = ["excavator", "tools", "trash", "products", "equipment", "rigging", "bundles"]


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


def _rig_entry(report, root, name, fbx_rel, blend_rel):
    entry = {"asset": name, "kind": "rigging", "status": "FAIL", "tris": None, "issues": [], "error": None,
             "fbx": fbx_rel, "blend": blend_rel, "bones": [], "takes": []}
    report["assets"].append(entry)
    return entry


def build_rigging(root, report):
    """SK_VillagerNPC (+ its two socket props) and Anim_PlayerToolSwing, with baked takes."""
    from kali_blender import rigging_common as rc
    from kali_blender import tool_swing as T
    from kali_blender import villager as V
    from kali_blender import villager_clips as C
    from kali_blender import villager_variants as VV
    from kali_blender import player_arms as PA

    entry = _rig_entry(report, root, V.NAME, V.FBX_PATH, V.BLEND_PATH)
    try:
        _reset()
        bpy.context.scene.render.fps = rc.FPS
        img = V.PALETTE.write_png(os.path.join(root, V.PALETTE_PNG))
        mat = V.PALETTE.material(V.MATERIAL, img)
        bag, bin_obj = V.build_props(mat)
        rod = C.build_rod(mat)
        for prop in (bag, bin_obj, rod):
            path = os.path.join(root, rc.FBX_DIR, prop.name + ".fbx")
            export_tool(prop, path)
            verify_fbx(path, expected_meshes=[prop.name])
        rig = V.build_rig()
        mesh = V.build_mesh(mat)
        V.skin(mesh, rig)
        V.build_actions(rig)
        C.build_actions(rig)
        fbx_abs = os.path.join(root, V.FBX_PATH)
        rc.export_animated(rig, [mesh], fbx_abs)
        info = verify_fbx(fbx_abs, expected_bones=[b[0] for b in V.BONES], expected_meshes=[V.NAME])
        entry["bones"], entry["takes"] = info["bones"], rc.take_names_in_fbx(fbx_abs)
        entry["tris"] = tc.tri_count(mesh)
        lo, hi = V.TRI_BUDGET
        if not lo <= entry["tris"] <= hi:
            entry["issues"].append(f"tris {entry['tris']} outside budget {lo}-{hi}")
        if entry["takes"] != sorted(C.ALL_TAKES):
            entry["issues"].append(f"takes {entry['takes']} != {sorted(C.ALL_TAKES)}")
        # Task 6C variety: body variants (same rig, no takes), head accessories, per-NPC palettes
        bodies = VV.build_bodies(mat, rig)
        for name, body in bodies.items():
            path = os.path.join(root, rc.FBX_DIR, name + ".fbx")
            rc.export_skinned_static(rig, [body], path)
            verify_fbx(path, expected_bones=[b[0] for b in V.BONES], expected_meshes=[name])
        accs = {}
        for name in VV.ACCESSORIES:
            acc = VV.build_accessory(name, mat)
            path = os.path.join(root, rc.FBX_DIR, name + ".fbx")
            export_tool(acc, path)
            verify_fbx(path, expected_meshes=[name])
            accs[name] = acc
        for npc in VV.RECIPES:
            VV.palette_for(npc).write_png(os.path.join(root, VV.png_path(npc)))
        tris = {**{n: tc.tri_count(o) for n, o in {**bodies, **accs}.items()}, V.NAME: entry["tris"]}
        for npc in VV.RECIPES:
            t = VV.assembled_tris(npc, tris.get)
            entry.setdefault("variants", {})[npc] = t
            if not lo <= t <= hi:
                entry["issues"].append(f"{npc} assembled tris {t} outside {lo}-{hi}")
        V.attach_props(rig, bag, bin_obj, rod)
        for acc in accs.values():
            VV.attach_accessory(rig, acc)
            acc.hide_set(True)
        for body in bodies.values():
            body.hide_set(True)
        rc.set_take(rig, "Idle")
        _save_blend(os.path.join(root, V.BLEND_PATH))
        entry["status"] = "FAIL" if entry["issues"] else "PASS"
        print(f"villager: {entry['tris']} tris, {len(info['bones'])} bones, takes {entry['takes']}")
    except Exception as exc:
        traceback.print_exc()
        entry["error"] = f"{type(exc).__name__}: {exc}"

    entry = _rig_entry(report, root, T.NAME, T.FBX_PATH, T.BLEND_PATH)
    try:
        _reset()
        bpy.context.scene.render.fps = rc.FPS
        rig = T.build_rig()
        T.build_actions(rig)
        fbx_abs = os.path.join(root, T.FBX_PATH)
        # The +90 deg X on the rig object is intentional (cancels the axis conversion), so no apply.
        rc.export_animated(rig, [], fbx_abs, apply_transforms=False)
        info = verify_fbx(fbx_abs, expected_bones=[T.BONE], expected_meshes=[])
        entry["bones"], entry["takes"] = info["bones"], rc.take_names_in_fbx(fbx_abs)
        if entry["takes"] != sorted(T.TAKES):
            entry["issues"].append(f"takes {entry['takes']} != {sorted(T.TAKES)}")
        rc.set_take(rig, "SerokanScoop")
        _save_blend(os.path.join(root, T.BLEND_PATH))
        entry["status"] = "FAIL" if entry["issues"] else "PASS"
        print(f"tool swing: takes {entry['takes']}")
    except Exception as exc:
        traceback.print_exc()
        entry["error"] = f"{type(exc).__name__}: {exc}"

    entry = _rig_entry(report, root, PA.NAME, PA.FBX_PATH, PA.BLEND_PATH)
    try:
        _reset()
        bpy.context.scene.render.fps = rc.FPS
        img = PA.PALETTE.write_png(os.path.join(root, PA.PALETTE_PNG))
        mat = PA.PALETTE.material(PA.MATERIAL, img)
        rig, mesh = PA.build(mat)
        PA.build_actions(rig)
        fbx_abs = os.path.join(root, PA.FBX_PATH)
        rc.export_animated(rig, [mesh], fbx_abs, apply_transforms=False)
        info = verify_fbx(fbx_abs, expected_meshes=[PA.NAME])
        entry["bones"], entry["takes"] = info["bones"], rc.take_names_in_fbx(fbx_abs)
        entry["tris"] = tc.tri_count(mesh)
        lo, hi = PA.TRI_BUDGET
        if not lo <= entry["tris"] <= hi:
            entry["issues"].append(f"tris {entry['tris']} outside budget {lo}-{hi}")
        if entry["takes"] != sorted(PA.TAKES):
            entry["issues"].append(f"takes {entry['takes']} != {sorted(PA.TAKES)}")
        rc.set_take(rig, "Idle_Hold")
        _save_blend(os.path.join(root, PA.BLEND_PATH))
        entry["status"] = "FAIL" if entry["issues"] else "PASS"
        print(f"player arms: {entry['tris']} tris, bones {info['bones']}, takes {entry['takes']}")
    except Exception as exc:
        traceback.print_exc()
        entry["error"] = f"{type(exc).__name__}: {exc}"
    return report


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


def _pack_config(kind):
    """Settings for one prop pack. 'tools', 'trash' and 'products' share the same build/export/atlas flow."""
    if kind == "tools":
        return {
            "kind": "tool", "modules": tc.TOOL_MODULES + tc.STARTER_MODULES, "load": tc.load_tool_module,
            "build": lambda mod, coll: tc.build_tool(mod, collection=coll),
            "validate": tc.validate_tool, "fbx_dir": tc.FBX_DIR, "tex_dir": tc.TEX_DIR,
            "blend_path": tc.BLEND_PATH, "material": tc.MATERIAL_NAME, "atlas_files": tc.ATLAS_FILES,
            "preview": "Tools_Preview",
        }
    if kind == "bundles":
        return {
            "kind": "bundle", "modules": bc.BUNDLE_MODULES, "load": bc.load_bundle_module,
            "build": lambda mod, coll: bc.build_bundle(mod, collection=coll),
            "validate": bc.validate_bundle, "fbx_dir": bc.FBX_DIR, "tex_dir": bc.TEX_DIR,
            "blend_path": bc.BLEND_PATH, "material": bc.MATERIAL_NAME, "atlas_files": bc.ATLAS_FILES,
            "preview": "Bundles_Preview",
        }
    if kind == "products":
        return {
            "kind": "product", "modules": pc.PRODUCT_MODULES, "load": pc.load_product_module,
            "build": lambda mod, coll: pc.build_product(mod, collection=coll),
            "validate": pc.validate_product, "fbx_dir": pc.FBX_DIR, "tex_dir": pc.TEX_DIR,
            "blend_path": pc.BLEND_PATH, "material": pc.MATERIAL_NAME, "atlas_files": pc.ATLAS_FILES,
            "preview": "Products_Preview",
        }
    if kind == "equipment":
        return {
            "kind": "equipment", "modules": ec.EQUIPMENT_MODULES, "load": ec.load_equipment_module,
            "build": lambda mod, coll: ec.build_equipment(mod, collection=coll),
            "validate": ec.validate_equipment, "fbx_dir": ec.FBX_DIR, "tex_dir": ec.TEX_DIR,
            "blend_path": ec.BLEND_PATH, "material": ec.MATERIAL_NAME, "atlas_files": ec.ATLAS_FILES,
            "preview": "Equipment_Preview",
        }
    return {
        "kind": "trash", "modules": trc.TRASH_MODULES, "load": trc.load_trash_module,
        "build": lambda mod, coll: trc.build_trash(mod, collection=coll),
        "validate": trc.validate_trash, "fbx_dir": trc.FBX_DIR, "tex_dir": trc.TEX_DIR,
        "blend_path": trc.BLEND_PATH, "material": trc.MATERIAL_NAME, "atlas_files": trc.ATLAS_FILES,
        "preview": "Trash_Preview",
    }


def build_pack(root, report, kind):
    """Build every module of a prop pack, export each FBX, write its atlas and preview pack."""
    cfg = _pack_config(kind)
    _reset()
    scene = bpy.context.scene
    specs = []            # every SPEC that loaded (drives the atlas, even if a build failed)
    built = []            # (grid slot, spec name, collection) for assets kept in the pack
    tex_dir = os.path.join(root, cfg["tex_dir"])
    for slot, mod_name in enumerate(cfg["modules"]):
        entry = {"asset": mod_name, "kind": cfg["kind"], "status": "FAIL", "tris": None, "issues": [],
                 "error": None, "fbx": None}
        report["assets"].append(entry)
        coll = None
        try:
            spec = cfg["load"](mod_name).SPEC
            specs.append(spec)
            entry["asset"] = spec["name"]
            coll = bpy.data.collections.new(spec["name"])
            scene.collection.children.link(coll)
            obj = cfg["build"](mod_name, coll)
            entry["issues"] = cfg["validate"](obj, spec)
            entry["tris"] = tc.tri_count(obj)
            fbx_abs = os.path.join(root, cfg["fbx_dir"], spec["name"] + ".fbx")
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
    report["atlases"][kind] = atlas
    try:
        paths = tc.write_atlas_images(specs, tex_dir, files=cfg["atlas_files"])
        tc.wire_atlas_material(paths, material_name=cfg["material"])
        atlas["paths"] = {k: _rel(root, v) for k, v in paths.items()}
        atlas["status"] = "PASS"
    except Exception as exc:
        traceback.print_exc()
        atlas["error"] = f"{type(exc).__name__}: {exc}"

    # Browsable pack: asset collections excluded from the view layer, instanced on a 5x4 grid.
    preview = bpy.data.collections.new(cfg["preview"])
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
    blend_abs = os.path.join(root, cfg["blend_path"])
    _save_blend(blend_abs)
    report[f"{kind}_blend"] = _rel(root, blend_abs)
    return report


def _print_table(report):
    rows = [("ASSET", "KIND", "STATUS", "TRIS", "DETAIL")]
    for a in report["assets"]:
        detail = a["error"] or "; ".join(a["issues"]) or ""
        rows.append((a["asset"], a["kind"], a["status"],
                     "-" if a["tris"] is None else str(a["tris"]), detail[:90]))
    for kind, at in report.get("atlases", {}).items():
        rows.append((f"atlas-{kind}", "texture", at["status"], "-", at["error"] or ""))
    widths = [max(len(str(r[i])) for r in rows) for i in range(5)]
    print()
    for r in rows:
        print("  ".join(str(c).ljust(widths[i]) for i, c in enumerate(r)).rstrip())
    print()


def main():
    parser = argparse.ArgumentParser(description="Build KALI excavator, tool, trash, product and rigging assets.")
    parser.add_argument("--only", choices=STAGES, default=None)
    parser.add_argument("--repo", default=DEFAULT_ROOT, help="repo root (default: parent of blender/)")
    args = parser.parse_args(_argv())
    root = os.path.abspath(args.repo)

    report = {
        "generated": datetime.datetime.now(datetime.timezone.utc).isoformat(timespec="seconds"),
        "blender_version": bpy.app.version_string,
        "only": args.only,
        "assets": [],
        "atlases": {},
    }
    if args.only in (None, "excavator"):
        build_excavator(root, report)
    if args.only in (None, "tools"):
        build_pack(root, report, "tools")
    if args.only in (None, "trash"):
        build_pack(root, report, "trash")
    if args.only in (None, "products"):
        build_pack(root, report, "products")
    if args.only in (None, "equipment"):
        build_pack(root, report, "equipment")
    if args.only in (None, "rigging"):
        build_rigging(root, report)
    if args.only in (None, "bundles"):
        build_pack(root, report, "bundles")

    failed = any(a["status"] != "PASS" for a in report["assets"]) or \
        any(at["status"] != "PASS" for at in report["atlases"].values())
    report["status"] = "FAIL" if failed else "PASS"
    report_path = os.path.join(root, "blender", "build_report.json")
    with open(report_path, "w", encoding="utf-8") as fh:
        json.dump(report, fh, indent=2)
    _print_table(report)
    print(f"report: {_rel(root, report_path)}")
    print("BUILD " + report["status"])
    if bpy.app.background:
        sys.exit(1 if failed else 0)


main()
