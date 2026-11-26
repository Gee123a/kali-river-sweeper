#!/usr/bin/env python3
"""
Auto-syncs docs/KALI_Asset_Master_Tracker.tsv (and .xlsx if openpyxl is installed)
against real files in unity/Assets/_Project/ on main + all remote origin/* branches.
"""
from __future__ import annotations

import csv
import os
import re
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TSV_PATH = REPO_ROOT / "docs" / "KALI_Asset_Master_Tracker.tsv"
CSV_PATH = REPO_ROOT / "docs" / "KALI_Asset_Master_Tracker.csv"
XLSX_PATH = REPO_ROOT / "docs" / "KALI_Asset_Master_Tracker.xlsx"
UNITY_PROJECT_REL = "unity/Assets/_Project"

OFFICIAL_ADDITIONS = [
    ("KaliPropPrefabBuilder.cs", "Props - Editor", "Auto Prefab & 2048 Atlas Material Builder", "JC", "Assets/_Project/Props/Editor/", "C# Editor Tool", "N/A", "To Do", "Editor Menu", "Generates PF_Trash_* (Kinematic+BoxCollider) & PF_Tool_* via KALI > JC menu"),
    ("SM_Trash_MedicalBag", "Props - Trash", "Medical Biohazard Sack B3", "JC", "Assets/_Project/Props/Trash/Meshes/", "372 tris / 2048px Atlas", "Waterline", "To Do", "trash_pile (B3)", "Hazard yellow #EAB308 + red accents; secured safely via #10 Capitan Ular"),
    ("SM_Trash_SyringeBox", "Props - Trash", "Medical Sharps Container B3", "JC", "Assets/_Project/Props/Trash/Meshes/", "288 tris / 2048px Atlas", "Waterline", "To Do", "trash_pile (Medical)", "Medical waste trade-off target; prick chance drops to 0% with #10 Capitan Ular"),
    ("SM_Trash_BiohazardDrum", "Props - Trash", "Radioactive / Biohazard B3 Drum", "JC", "Assets/_Project/Props/Trash/Meshes/", "250-400 tris / 2048px Atlas", "Waterline", "To Do", "trash_pile (Biohazard)", "Deals continuous DoT if held in cargo too long; discard at Karantina Biohazard"),
    ("SM_Env_PosMedisB3", "Environment", "Medical Waste B3 Disposal Station", "Wesley", "Assets/_Project/Environment/Meshes/", "800-1400 tris", "Base", "To Do (Greybox in Map)", "pos_medis (1 node)", "Proper 100% Medical waste station; collider name must contain Pos Medis"),
    ("SM_Env_KarantinaBiohazard", "Environment", "Biohazard & Radioactive Quarantine Bunker", "Wesley", "Assets/_Project/Environment/Meshes/", "1000-1600 tris", "Base", "To Do (Greybox in Map)", "karantina_biohazard (1 node)", "Proper 100% Biohazard/Radioactive station; collider name must contain Karantina"),
    ("SM_Env_GudangPengepul", "Environment", "Informal Bulk Scrap Collector Warehouse", "Wesley", "Assets/_Project/Environment/Meshes/", "800-1200 tris", "Base", "To Do (Greybox in Map)", "pengepul (1 node)", "One-go 45% bulk dump near Spawn & Bank Sampah; collider name must contain Pengepul"),
    ("SM_Tool_SendokMakanBengkok", "Props - Tools", "#01 Bent Dining Spoon (Tier 0)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 0", "Holds 1 tiny item (0.05 kg)"),
    ("SM_Tool_GayungMandi", "Props - Tools", "#02 Bath Dipper (Tier 0)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 0", "Holds 2 items (0.3 kg)"),
    ("SM_Tool_CentongNasi", "Props - Tools", "#03 Rice Paddle (Tier 0)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 0", "Holds 1 flat item (0.1 kg)"),
    ("SM_Tool_GarpuTaman", "Props - Tools", "#04 Garden Hand Fork (Tier 0)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 0", "Holds 1 plastic bag (0.2 kg)"),
    ("SM_Tool_EmberCat5L", "Props - Tools", "#05 5L Paint Can (Tier 0)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 0", "Holds 3-4 items (1.0 kg)"),
    ("SM_Tool_GayungSaringanBambu", "Props - Tools", "#06 Perforated Dipper on Bamboo (Tier 1)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 1", "Holds 4 items (0.8 kg)"),
    ("SM_Tool_SerokanWaring3m", "Props - Tools", "#07 Bamboo Hand Net 3m (Tier 1)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 1", "Holds 8-10 items (2.0 kg)"),
    ("SM_Tool_GancoBesi1Mata", "Props - Tools", "#08 Single Spike Hook (Tier 1)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 1", "Holds 1 heavy debris item (150 kg)"),
    ("SM_Tool_EmberCat20L", "Props - Tools", "#09 Weighted 20L Bucket (Tier 1)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 1", "Holds 5-6 items (1.8 kg)"),
    ("SM_Tool_CapitanUlar", "Props - Tools", "#10 Snake Grabber (Tier 1 Biohazard)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 1 (B3)", "Mandatory for safely securing Medical Waste B3"),
    ("SM_Tool_AritSabitPanjang", "Props - Tools", "#11 Long Grass Sickle (Tier 2)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 2", "Holds 0.5 m2 weeds (10 kg)"),
    ("SM_Tool_SerokanJumbo4_5m", "Props - Tools", "#12 Jumbo Waring Net 4.5m (Tier 2)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 2", "Holds 15-18 items (4.0 kg)"),
    ("SM_Tool_GancoGandaWinch", "Props - Tools", "#13 Double Winch Hook (Tier 2)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 2", "Holds 1 massive item (400 kg)"),
    ("SM_Tool_JalaCincinLempar", "Props - Tools", "#14 Float Ring Cast Net (Tier 2)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 2", "Holds 15-20 items (5.0 kg)"),
    ("SM_Tool_PompaSiphonManual", "Props - Tools", "#15 Manual Bilge Siphon (Tier 2)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 2", "1.0 kg/sec riverbed sludge"),
    ("SM_Tool_BlokMagnet50kg", "Props - Tools", "#16 50kg Salvage Magnet (Tier 3)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 3", "Holds 2-3 metal scrap items (30 kg)"),
    ("SM_Tool_SenapanPanahTali", "Props - Tools", "#17 Harpoon Launcher (Tier 3)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 3", "Holds 1 buoyant item (25 kg)"),
    ("SM_Tool_PompaMesinRumput49cc", "Props - Tools", "#18 49cc Vacuum Impeller (Tier 3)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 3", "4.0 kg/sec continuous slurry"),
    ("SM_Tool_PenebasGergajiGanda", "Props - Tools", "#19 Twin Saw Weed Slasher (Tier 3)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 3", "3.0 m2/sec Eceng Gondok clearing"),
    ("SM_Tool_GarukSkimmerHidrolik", "Props - Tools", "#20 Hydraulic Bow Skimmer (Tier 3)", "JC", "Assets/_Project/Props/Tools/Meshes/", "364-1120 tris / 2048 Atlas", "Grip (0,0,0) +Z", "To Do", "Tool Tier 3", "Pushes 30-40 floating items per pass"),
]


def run_git(args: list[str]) -> str:
    return subprocess.check_output(["git", *args], cwd=REPO_ROOT, text=True)


def list_tree_files() -> tuple[set[str], set[str], dict[str, set[str]]]:
    """Returns (head_files, local_files, {branch_name: set_of_files}) relative to repo root."""
    head_out = run_git(["ls-tree", "-r", "--name-only", "HEAD", "--", UNITY_PROJECT_REL])
    head_files = set(head_out.splitlines())

    local_all = {
        str(p.relative_to(REPO_ROOT)).replace("\\", "/")
        for p in (REPO_ROOT / "unity" / "Assets" / "_Project").rglob("*")
        if p.is_file()
    }
    local_files = local_all - head_files

    branch_files: dict[str, set[str]] = {}
    refs = run_git(["for-each-ref", "--format=%(refname:short)", "refs/remotes/origin"]).splitlines()
    for ref in refs:
        if ref in ("origin", "origin/HEAD", "origin/main"):
            continue
        short = ref.removeprefix("origin/")
        out = run_git(["ls-tree", "-r", "--name-only", ref, "--", UNITY_PROJECT_REL])
        branch_files[short] = set(out.splitlines())
    return head_files, local_files, branch_files


def asset_variants(asset_id: str) -> tuple[list[str], list[str]]:
    """Returns (source_candidates, prefab_candidates) basenames without extension or full names."""
    stem = Path(asset_id).stem
    sources = [asset_id, stem]
    prefabs: list[str] = []
    if stem.startswith("SM_"):
        prefabs.append("PF_" + stem[3:])
    elif stem.startswith("SK_"):
        prefabs.append("PF_" + stem[3:])
    elif stem.startswith("PF_") or stem.startswith("Canvas_") or stem.startswith("VFX_"):
        prefabs.append(stem)
    if asset_id == "VFX_MonsoonRain":
        prefabs.append("PF_VFX_MonsoonRain")
    return sources, prefabs


def find_matches(candidates: list[str], file_set: set[str]) -> tuple[list[str], bool]:
    matched = []
    has_meta = False
    for path in file_set:
        if path.endswith(".meta"):
            continue
        name = Path(path).name
        stem = Path(path).stem
        if name in candidates or stem in candidates:
            matched.append(path)
            if (path + ".meta") in file_set:
                has_meta = True
    return matched, has_meta


def compute_status(asset_id: str, current_status: str, head_files: set[str], local_files: set[str], branch_files: dict[str, set[str]]) -> str:
    sources, prefabs = asset_variants(asset_id)

    # Canvas_HUD override
    if asset_id == "Canvas_HUD":
        head_src, _ = find_matches(sources, head_files)
        head_pf, head_pf_meta = find_matches(prefabs, head_files) if prefabs else ([], False)
        in_main = bool((head_pf and head_pf_meta) or head_src)
        if in_main:
            return "In Progress in main (Needs Dock & 720p QA)"
        niki_files = branch_files.get("niki-vfx", set())
        b_src, _ = find_matches(sources, niki_files)
        b_pf, b_pf_meta = find_matches(prefabs, niki_files) if prefabs else ([], False)
        if b_pf or b_src:
            return "In Progress in Branch (niki-vfx)"

    head_src, head_src_meta = find_matches(sources, head_files)
    head_pf, head_pf_meta = find_matches(prefabs, head_files) if prefabs else ([], False)

    if head_pf and head_pf_meta:
        return "DONE (Prefab + .meta in main)"
    if head_pf:
        return "Prefab in main (Missing .meta)"
    if head_src:
        ext = Path(head_src[0]).suffix.lower()
        if ext in (".cs", ".json", ".shadergraph", ".unity"):
            return "DONE (In main)"
        if ext == ".fbx":
            local_pf, local_pf_meta = find_matches(prefabs, local_files) if prefabs else ([], False)
            if local_pf and local_pf_meta:
                return "FBX in main (Local Prefab Pending Commit)"
            return "FBX in main (Needs Unity Prefab + .meta)"
        return "In main"

    # Check local disk untracked/uncommitted
    local_src, local_src_meta = find_matches(sources, local_files)
    local_pf, local_pf_meta = find_matches(prefabs, local_files) if prefabs else ([], False)

    if local_pf and local_pf_meta:
        return "Generated Locally (Pending Commit to main)"
    if local_src:
        ext = Path(local_src[0]).suffix.lower()
        if ext in (".cs", ".json", ".asset", ".shadergraph", ".unity"):
            return "Local Uncommitted (Pending Commit)"
        if ext == ".fbx":
            return "Local FBX (Pending Prefab & Commit)"

    # Check remote feature branches
    for branch, bfiles in sorted(branch_files.items()):
        b_src, _ = find_matches(sources, bfiles)
        b_pf, b_pf_meta = find_matches(prefabs, bfiles) if prefabs else ([], False)
        if b_pf and b_pf_meta:
            return f"DONE in Branch ({branch})"
        if b_pf:
            return f"Prefab in Branch ({branch} - Needs .meta)"
        if b_src:
            ext = Path(b_src[0]).suffix.lower()
            if ext == ".fbx":
                return f"In Branch ({branch}) - FBX Ready (Needs Prefab)"
            return f"In Branch ({branch}) - Scripted Ready"

    # Handle reverted branches
    if current_status.startswith(("In Branch (", "DONE in Branch (", "Prefab in Branch (", "In Progress in Branch (")):
        return "To Do (Reverted from Branch)"

    return current_status


def infer_owner_and_cat(rel_path: str) -> tuple[str, str]:
    p = rel_path.lower()
    if "/vfx/" in p:
        return "Niki", "VFX"
    if "/ui/" in p or "/audio/" in p:
        return "Niki", "UI & Audio"
    if "/environment/" in p:
        return "Wesley", "Environment"
    if "/shaders/" in p:
        return "Wesley", "Shaders"
    if "/props/" in p:
        if "/tools/" in p:
            return "JC", "Props - Tools"
        if "/trash/" in p:
            return "JC", "Props - Trash"
        if "/editor/" in p:
            return "JC", "Props - Editor"
        return "JC", "Props - Equipment"
    if "/rigging/" in p:
        return "JC", "Rigging & Animation"
    if "/lighting/" in p:
        return "JC", "Lighting"
    if "/scripts/" in p or "/data/" in p:
        return "Ivan (Lead)", "Core Code"
    return "Team", "Asset"


def sync_tracker() -> tuple[list[list[str]], int]:
    raw_lines = TSV_PATH.read_text(encoding="utf-8").splitlines()
    title_rows = [line.split("\t") for line in raw_lines[:2]]
    header = raw_lines[2].split("\t")
    rows = [line.split("\t") for line in raw_lines[3:] if line.strip()]

    # Pad any short rows cleanly to len(header)
    norm_rows: list[list[str]] = []
    seen_ids: dict[str, int] = {}
    for row in rows:
        padded = row + [""] * (len(header) - len(row))
        norm_rows.append(padded[: len(header)])
        seen_ids[padded[0]] = len(norm_rows) - 1

    # Inject official additions if missing
    for add in OFFICIAL_ADDITIONS:
        aid = add[0]
        if aid not in seen_ids:
            seen_ids[aid] = len(norm_rows)
            norm_rows.append(list(add))

    head_files, local_files, branch_files = list_tree_files()
    all_remote_files = set().union(*branch_files.values()) if branch_files else set()

    # Prune stale Auto-Discovered rows whose source no longer exists anywhere
    pruned_rows = []
    for row in norm_rows:
        if row[8] == "Auto-Discovered":
            notes = row[9]
            match = re.search(r"Detected at (.+)", notes)
            if match:
                rel_path = match.group(1).strip()
                exists = (rel_path in head_files) or (rel_path in local_files) or (rel_path in all_remote_files)
                if not exists:
                    continue
        pruned_rows.append(row)
    norm_rows = pruned_rows
    seen_ids = {r[0]: idx for idx, r in enumerate(norm_rows)}

    # Auto-discover unknown primary assets
    ignored_names = {"UnityEngine", "README.md", ".gitkeep"}
    all_asset_files = sorted(head_files.union(local_files, all_remote_files))
    for rel in all_asset_files:
        if rel.endswith((".meta", ".png", ".mat", ".md", ".blend", ".blend1")):
            continue
        name = Path(rel).name
        stem = Path(rel).stem
        if name in ignored_names or stem in seen_ids or name in seen_ids:
            continue
        if stem.startswith("PF_") and (("SM_" + stem[3:]) in seen_ids or ("SK_" + stem[3:]) in seen_ids):
            continue
        if stem.startswith("PF_VFX_") and (stem[3:] in seen_ids):
            continue
        owner, cat = infer_owner_and_cat(rel)
        asset_id = name if Path(rel).suffix in (".cs", ".json") else stem
        parent_dir = str(Path(rel).parent).replace("unity/", "") + "/"
        new_row = [asset_id, cat, stem.replace("_", " "), owner, parent_dir, Path(rel).suffix.upper().lstrip("."), "Auto", "To Do", "Auto-Discovered", f"Detected at {rel}"]
        seen_ids[asset_id] = len(norm_rows)
        norm_rows.append(new_row)

    updated_count = 0
    for row in norm_rows:
        old_status = row[7]
        new_status = compute_status(row[0], old_status, head_files, local_files, branch_files)

        if row[0] == "Canvas_HUD":
            if new_status == "In Progress in main (Needs Dock & 720p QA)":
                row[9] = "Sprites, contour map & chevron in main; wire BC_StationDockSheet to OnNearbyHubChanged & verify 1280x720"
            elif new_status == "In Progress in Branch (niki-vfx)":
                row[9] = "Prototype Canvas_HUD.prefab on niki-vfx; needs vellum/hatch sprites, contour minimap, [1][2][3][E] dock & 1280x720 QA"

        if row[8] == "Auto-Discovered":
            m = re.search(r"Detected at (.+)", row[9])
            if m:
                p_rel = m.group(1).strip()
                o_inf, c_inf = infer_owner_and_cat(p_rel)
                row[3] = o_inf
                row[1] = c_inf

        if row[0] == "SK_ExcavatorAmfibi" and "jc-excavator-tools" in new_status:
            row[5] = "4,298 tris / 3-Joint IK + Damped Track"
            row[9] = "Rigged in blender/build_all.py (0 _end leaf bones; 3 PBR slots)"
        if new_status != old_status:
            row[7] = new_status
            updated_count += 1

    all_rows = [*title_rows, header, *norm_rows]
    new_tsv = "\n".join("\t".join(r) for r in all_rows) + "\n"
    old_tsv = TSV_PATH.read_text(encoding="utf-8") if TSV_PATH.exists() else ""

    import io
    buf = io.StringIO()
    csv.writer(buf, lineterminator="\n").writerows(all_rows)
    new_csv = buf.getvalue()
    old_csv = CSV_PATH.read_text(encoding="utf-8") if CSV_PATH.exists() else ""

    if new_tsv != old_tsv or new_csv != old_csv or not XLSX_PATH.exists():
        TSV_PATH.write_text(new_tsv, encoding="utf-8")
        CSV_PATH.write_text(new_csv, encoding="utf-8")
        maybe_write_xlsx(title_rows, header, norm_rows)
    return norm_rows, updated_count


def status_style_hex(status: str) -> str:
    s = status.lower()
    if s.startswith("to do") or "not in repo" in s:
        return "FEE2E2"
    if s.startswith("done"):
        return "DCFCE7"
    if "branch" in s or "fbx in main" in s or "scripted" in s or "prefab" in s:
        return "DBEAFE"
    if "modeled" in s or "progress" in s:
        return "FEF9C3"
    return "FEE2E2"


def maybe_write_xlsx(title_rows: list[list[str]], header: list[str], rows: list[list[str]]) -> None:
    try:
        import openpyxl
        from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
    except ImportError:
        return

    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Asset Master Tracker"

    ws.cell(1, 1, title_rows[0][0]).font = Font(bold=True, size=14, color="0F172A")
    ws.cell(2, 1, title_rows[1][0]).font = Font(size=10, color="64748B")

    thin = Side(border_style="thin", color="CBD5E1")
    border = Border(left=thin, right=thin, top=thin, bottom=thin)

    for col_idx, col_name in enumerate(header, 1):
        c = ws.cell(4, col_idx, col_name)
        c.fill = PatternFill("solid", fgColor="1E293B")
        c.font = Font(bold=True, color="FFFFFF", size=10)
        c.alignment = Alignment(horizontal="left", vertical="center")
        c.border = border

    for r_offset, row in enumerate(rows):
        r_num = 5 + r_offset
        for c_idx, val in enumerate(row, 1):
            c = ws.cell(r_num, c_idx, val)
            c.font = Font(size=10, color="1E293B")
            c.border = border
            if c_idx == 8:
                c.fill = PatternFill("solid", fgColor=status_style_hex(val))
                c.font = Font(bold=True, size=10, color="0F172A")

    widths = [30, 18, 36, 12, 38, 28, 16, 40, 22, 52]
    for i, w in enumerate(widths, 1):
        ws.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    # Executive Summary sheet
    ws2 = wb.create_sheet("Executive Summary")
    ws2.cell(1, 1, "KALI: Indonesian River Sweeper - Asset Production Scorecard").font = Font(bold=True, size=14, color="0F172A")
    ws2.cell(2, 1, "Auto-calculated from Git repository files & branches").font = Font(size=10, color="64748B")

    sum_headers = ["Team Member", "Domain Ownership", "Total Assets", "DONE (In main)", "Active / In Branch", "To Do / Pending", "Progress %"]
    for i, h in enumerate(sum_headers, 1):
        c = ws2.cell(4, i, h)
        c.fill = PatternFill("solid", fgColor="1E293B")
        c.font = Font(bold=True, color="FFFFFF", size=10)

    owners_meta = [
        ("Ivan (Lead)", "Game Logic, C# Architecture, Buoyancy & Importer"),
        ("JC", "Props (Trash, 20 Tools, Medical B3), Rigging (Excavator IK), Lighting"),
        ("Wesley", "Environment Architecture (10 SM_Env_*) & URP Shaders"),
        ("Niki", "VFX Systems (4), UI Canvases (3) & Audio"),
    ]
    r_idx = 5
    for owner_key, domain in owners_meta:
        orows = [r for r in rows if r[3].lower().startswith(owner_key.split()[0].lower())]
        total = len(orows)
        done = sum(1 for r in orows if r[7].lower().startswith("done"))
        active = sum(1 for r in orows if (s := r[7].lower()) and not s.startswith("done") and not s.startswith("to do") and "not in repo" not in s and ("branch" in s or "modeled" in s or "scripted" in s or "fbx" in s or "local" in s or "progress" in s))
        todo = total - done - active
        pct = f"{round(((done + active * 0.6) / total) * 100)}%" if total else "0%"
        for c_idx, val in enumerate([owner_key, domain, total, done, active, todo, pct], 1):
            ws2.cell(r_idx, c_idx, val).border = border
        r_idx += 1

    for i, w in enumerate([20, 56, 14, 16, 18, 16, 14], 1):
        ws2.column_dimensions[openpyxl.utils.get_column_letter(i)].width = w

    wb.save(XLSX_PATH)


if __name__ == "__main__":
    rows, changed = sync_tracker()
    print(f"Synced {len(rows)} tracker rows ({changed} status changes updated).")
