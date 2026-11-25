# KALI Blender assets / Aset Blender KALI

Skrip ini membuat aset 3D untuk game Unity (2022.3 URP) dengan Blender 5.3.
These scripts build the 3D assets for the Unity 2022.3 URP game with Blender 5.3.

## Apa yang dibuat / What gets made
- **SK_ExcavatorAmfibi**: excavator amfibi (rig + skinned mesh), target 4000-6000 tris.
  Output: `blender/SK_ExcavatorAmfibi.blend`, `unity/Assets/_Project/Art/Props/Vehicles/SK_ExcavatorAmfibi.fbx`.
- **20 tool sampah / trash tools** (`SM_Tool_*`, 300-1200 tris each). One shared atlas material `M_Tools_Atlas`.
  Output: `unity/Assets/_Project/Art/Props/Tools/<SM_Tool_name>.fbx`,
  textures in `unity/Assets/_Project/Art/Props/Tools/Textures/` (albedo, normal, mask),
  pack `blender/SM_Tools_Pack.blend` (collection `Tools_Preview` shows all tools on a 5x4 grid, 1.0 m apart).
- **Report**: `blender/build_report.json` (status per asset, tri counts, validation issues, output paths).

## Cara menjalankan / How to run
Build all (headless, bpy wheel):
```
/opt/bpyenv/bin/python blender/build_all.py
/opt/bpyenv/bin/python blender/build_all.py --only excavator
/opt/bpyenv/bin/python blender/build_all.py --only tools
```
Build all (Blender headless):
```
blender -b -P blender/build_all.py -- --only tools
```
Blender 5.3 GUI: buka `blender/build_all.py` di tab **Scripting** (Open, lalu Run Script).
Open `build_all.py` in the **Scripting** tab (Open, then Run Script). Opens with `--only` unset = build everything.

Exit code `1` jika ada aset yang gagal (any asset FAIL). A broken or missing tool module is reported as FAIL and the rest still build.

Test (stand-in, tanpa rig/mesh/tool asli / no real rig or tool needed):
```
/opt/bpyenv/bin/python blender/tests/test_export.py     # prints ALL EXPORT TESTS PASSED
```

Cek satu tool / check one tool: `/opt/bpyenv/bin/python blender/tools_check.py tool_07_sapu_lidi --render /tmp/out`.

## Kontrol rig / Rig controls
- **CTRL_IK_Bucket**: pegang ini untuk menggerakkan ember. Posisinya di pergelangan (wrist), rotasinya sama dengan `B_Tool_Bucket`, jadi pose istirahat tidak berubah. Pose it to move the bucket (IK on `B_Arm_Stick`, 2 bones).
- **POLE_Elbow_Target**: pole target siku, mengatur arah lengan boom/stick saat IK. Elbow direction for the IK chain.
- **Turret slew**: `B_Turret_Slew` berputar terhadap sumbu Z (atas) pada `B_Root_Hull`. Rotates about +Z (world up).
- **Spud legs**: `B_Spud_Leg_FL/FR/BL/BR` turun 0 - 3.5 m (`SPUD_DROP`). Drop 0 to 3.5 m.
- Boom / stick batas sudut / limits: boom -15..75 deg, stick -110..10 deg.

Nilai ini berasal dari `kali_blender/excavator_spec.py` (sumber tunggal / single source of truth). Edit angka di sana, bukan di skrip build.

## Aturan tool / Tool rules
- **Pivot = grip**: origin (0,0,0) adalah titik pegang pemain; permukaan mesh harus berada dalam 0.05 m dari origin.
- **Handle along Z**: sumbu panjang di Z. `head_dir` = `+Z` (ujung kerja ke atas, mis. sapu, jaring) atau `-Z` (menggantung, mis. ember).
- Transform applied (lokasi 0, rotasi 0, skala 1). Satu material `M_Tools_Atlas`.
- **Atlas**: 2048x2048, grid 5x4 sel (satu sel per tool, index 1..20). Tiap sel dibagi grid 4x4 swatch warna (maks 16 warna per tool), dengan margin 12%.

## Pengaturan FBX / FBX settings
Semua ekspor memakai `FBX_SETTINGS` yang sama (`kali_blender/export_fbx.py`).
All exports share `FBX_SETTINGS` in `kali_blender/export_fbx.py`.

| Setting | Nilai / Value | Catatan / Note |
|---|---|---|
| use_selection | True | hanya objek terpilih / selected objects only |
| global_scale | 1.0 | |
| apply_unit_scale | True | |
| apply_scale_options | FBX_SCALE_ALL | |
| axis_forward / axis_up | -Z / Y | Unity: Y up |
| bake_space_transform | True | "Apply Transform" |
| mesh_smooth_type | FACE | |
| use_mesh_modifiers | True | |
| add_leaf_bones | False | tidak ada bone `_end` / no `_end` leaf bones |
| primary_bone_axis / secondary_bone_axis | Y / X | |
| path_mode | COPY | |
| embed_textures | True | |
| bake_anim | False | |
| object_types | excavator: ARMATURE, MESH; tool: MESH | excavator memakai `use_armature_deform_only=True` |

Sebelum ekspor, semua transform diterapkan (Ctrl+A). `verify_fbx` mengimpor ulang file, memeriksa bone dan mesh, lalu menghapus hasil impor, sehingga scene tidak berubah.
Before export, all transforms are applied. `verify_fbx` re-imports the file, checks bones and meshes, then removes the imported data again.

## Struktur file / Layout
- `build_all.py`: pipeline utama / main pipeline.
- `kali_blender/export_fbx.py`: ekspor FBX, apply transform, verifikasi / export, apply transforms, verify.
- `kali_blender/excavator_spec.py`, `kali_blender/tools_common.py`: data dan helper bersama / shared data and helpers.
- `tools_check.py`: cek dan render tool satu per satu / check and render tools one at a time.
- `tests/test_export.py`: tes ekspor dengan stand-in / export tests with stand-ins.
