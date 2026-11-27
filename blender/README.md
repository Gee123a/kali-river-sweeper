# KALI Blender assets / Aset Blender KALI

Skrip ini membuat aset 3D untuk game Unity (2022.3 URP) dengan Blender 5.3.
These scripts build the 3D assets for the Unity 2022.3 URP game with Blender 5.3.

## Apa yang dibuat / What gets made
- **SK_ExcavatorAmfibi**: excavator amfibi (rig + skinned mesh), target 4000-6000 tris.
  Output: `blender/SK_ExcavatorAmfibi.blend`, `unity/Assets/_Project/Rigging/SK_ExcavatorAmfibi.fbx`.
- **20 alat sampah / trash tools** (`SM_Tool_*`, 300-1200 tris each). One shared atlas material `M_Tools_Atlas`.
  Output: `unity/Assets/_Project/Props/Tools/Meshes/<SM_Tool_name>.fbx`,
  textures in `unity/Assets/_Project/Props/Tools/Textures/` (albedo, normal, mask),
  pack `blender/SM_Tools_Pack.blend` (collection `Tools_Preview` shows all tools on a 5x4 grid, 1.0 m apart).
- **Sampah sungai / river trash** (`SM_Trash_*`, 150-400 tris each): 2 B3 medical props + 9 branded Indonesian packs/bottles. One shared atlas material `M_Trash_Atlas`.
  Output: `unity/Assets/_Project/Props/Trash/Meshes/<SM_Trash_name>.fbx`,
  textures in `unity/Assets/_Project/Props/Trash/Textures/` (albedo, normal, mask),
  pack `blender/SM_Trash_Pack.blend` (collection `Trash_Preview`).
- **Report**: `blender/build_report.json` (status per asset, tri counts, validation issues, repo-relative output paths). Generated, git-ignored.

### Daftar 20 alat resmi / Official 20 tools (docs/PRD.md section 3)
Nomor = urutan di PRD / index from the PRD. Modul ada di `kali_blender/tools/` (`TOOL_MODULES` in `tools_common.py`).

| # | Nama / Name |
|---|---|
| 01 | Sendok Makan Bengkok |
| 02 | Gayung Mandi |
| 03 | Centong Nasi |
| 04 | Garpu Taman |
| 05 | Ember Cat 5L |
| 06 | Gayung Saringan Bambu |
| 07 | Serokan Waring 3m |
| 08 | Ganco Besi 1-Mata |
| 09 | Ember Cat 20L |
| 10 | Capitan Ular (untuk limbah medis B3 / for B3 medical waste) |
| 11 | Arit Sabit Panjang |
| 12 | Serokan Jumbo 4.5m |
| 13 | Ganco Ganda Winch |
| 14 | Jala Cincin Lempar |
| 15 | Pompa Siphon Manual |
| 16 | Blok Magnet 50kg |
| 17 | Senapan Panah Tali |
| 18 | Pompa Mesin Rumput 49cc |
| 19 | Penebas Gergaji Ganda |
| 20 | Garuk Skimmer Hidrolik |

## Limbah medis B3 / B3 medical waste (trash stage)
- Modul / modules: `kali_blender/trash/` (`TRASH_MODULES` in `trash_common.py`): `PF_Trash_MedicalBag` (`SM_Trash_MedicalBag`), `PF_Trash_SyringeBox` (`SM_Trash_SyringeBox`).
- Material `M_Trash_Atlas`, atlas 2048x2048, same 5x4 cell scheme as the tools. Warna hazard: kuning `#EAB308` dengan aksen merah.
- Budget **150-400 tris** per prop. **Pivot = pusat bounding box** (origin di tengah bbox, toleransi 0.02 m), untuk rigidbody dan buoyancy.
- Transform applied, satu material, UV di dalam sel atlasnya.
- Prefab **PF_Trash_MedicalBag** dan **PF_Trash_SyringeBox** dibuat di Unity lewat menu editor
  `KALI > JC > Build Trash Prefabs` (skrip: `unity/Assets/_Project/Props/Editor/KaliPropPrefabBuilder.cs`), bukan dari Blender.

## Sampah bermerek / Branded trash (trash stage)
Sembilan sampah kemasan Indonesia, kotor dan lusuh tapi mereknya langsung terbaca. Nine Indonesian packaging props,
dirty and worn, brand readable at a glance.
Semua merek adalah PARODI (nama diganti) agar aman hak cipta/merek. All brands are PARODIES (renamed) to avoid trademark strikes. Pose = posisi mengapung (label menghadap atas), karena spawner hanya memutar yaw.
Pose = floating pose (print facing up): the spawner only adds a random yaw.

| # | Mesh / Prefab | Benda / Object | Ukuran / Size (m) | Tris |
|---|---|---|---|---|
| 03 | `SM_Trash_BungkusIndomy` | Bungkus mi goreng "Indomy", sobek di atas, kusut, sudut terlipat | 0.12 x 0.09 x 0.05 | 256 |
| 04 | `SM_Trash_SachetKecapBingo` | Pouch refill kecap manis "BINGO", sudut digunting, terlipat | 0.17 x 0.25 x 0.06 | 270 |
| 05 | `SM_Trash_SachetMoli` | Sachet cokelat malt "MOLI" 22 g, sudut sobek, kusut | 0.10 x 0.09 x 0.04 | 188 |
| 06 | `SM_Trash_BotolLifeman` | Botol sampo "Lifeman", penyok, tutup flip terbuka | 0.06 x 0.22 x 0.06 | 296 |
| 07 | `SM_Trash_BungkusSariBoti` | Plastik roti sobek "SARI BOTI", ujung terpilin, ujung lain sobek | 0.28 x 0.15 x 0.11 | 220 |
| 08 | `SM_Trash_BungkusRisol` | Pouch deterjen "Risol", digunting di atas, kusut | 0.20 x 0.28 x 0.10 | 274 |
| 09 | `SM_Trash_StyrofoamMakanan` | Kotak nasi styrofoam, tutup terbuka, sudut patah, noda makanan | 0.19 x 0.29 x 0.21 | 194 |
| 10 | `SM_Trash_BotolSprit` | Botol PET soda lemon-lime "Sprit" 1.5 L, gepeng, penyok | 0.32 x 0.10 x 0.10 | 332 |
| 11 | `SM_Trash_KotakRokok` | Bungkus rokok "GUDANG GULA International", remuk, tutup terbuka sedikit | 0.06 x 0.10 x 0.04 | 220 |

Prefab `PF_Trash_<nama>` dibuat dengan menu Unity yang sama (`KALI > JC > Build Trash Prefabs`).

### Label (procedural)
- `kali_blender/labels.py`: semua seni label dibuat dengan kode (tanpa foto). Rasteriser numpy kecil (poligon, elips, garis,
  teks) dengan glyph dari mesin font Blender; font Windows (`C:/Windows/Fonts`) bila ada, font bawaan Blender bila tidak.
  `render_label(name, w, h, dirty=True)` -> albedo, normal, smoothness. `dirty=False` = label bersih untuk prop "produk" nanti.
  All label art is code: a small numpy rasteriser + Blender's font engine; `dirty` adds fade, crumple creases, mud/water
  stains and edge grime (`wear()`), lighter on the logo (`protect`).
- SPEC `"label_art": {"name": "indomy", "rows": 3}`: baris swatch bawah sel atlas (3 dari 4) berisi label; palet tinggal
  baris atas (maks 4 swatch). The bottom 3 swatch rows of the prop's cell hold the label, swatches keep the top row.
- `kali_blender/trash_shapes.py`: builder low-poly (kemasan bantal/pouch, botol lathe, kotak grid) dengan satu daftar vertex
  ter-weld; lipatan, kusut, penyok diterapkan ke semua part sekaligus. Part "label" membawa UV dalam ruang label.

## Cara menjalankan / How to run
Build all (headless, bpy wheel):
```
/opt/bpyenv/bin/python blender/build_all.py
/opt/bpyenv/bin/python blender/build_all.py --only excavator
/opt/bpyenv/bin/python blender/build_all.py --only tools
/opt/bpyenv/bin/python blender/build_all.py --only trash
```
Build all (Blender headless):
```
blender -b --factory-startup -P blender/build_all.py -- --only trash
```
`--factory-startup` dianjurkan: add-on pengguna (mis. ekstensi MCP) bisa membuat Blender crash saat build headless.
Recommended: a user add-on thread (e.g. an MCP extension) can crash headless builds (seen on Blender 5.2.1).
Blender 5.3 GUI: buka `blender/build_all.py` di tab **Scripting** (Open, lalu Run Script).
Open `build_all.py` in the **Scripting** tab (Open, then Run Script). Opens with `--only` unset = build everything.

Exit code `1` jika ada aset yang gagal (any asset FAIL). A broken or missing module is reported as FAIL and the rest still build.

Test (stand-in, tanpa rig/mesh/tool asli / no real rig or tool needed):
```
/opt/bpyenv/bin/python blender/tests/test_export.py     # prints ALL EXPORT TESTS PASSED
/opt/bpyenv/bin/python blender/tests/test_labels.py     # prints ALL LABEL TESTS PASSED (brand labels, atlas regions)
```

Cek satu tool / check one tool: `/opt/bpyenv/bin/python blender/tools_check.py tool_07_sapu_lidi --render /tmp/out`.

## Kontrol rig / Rig controls
- **CTRL_IK_Bucket**: pegang ini untuk menggerakkan ember. Posisinya di pergelangan (wrist), rotasinya sama dengan `B_Tool_Bucket`, jadi pose istirahat tidak berubah. Pose it to move the bucket (IK on `B_Arm_Stick`, 2 bones).
- **POLE_Elbow_Target**: pole target siku, mengatur arah lengan boom/stick saat IK. Elbow direction for the IK chain.
- **Turret slew**: `B_Turret_Slew` berputar terhadap sumbu Z (atas) pada `B_Root_Hull`. Rotates about +Z (world up).
- **Spud legs**: `B_Spud_Leg_FL/FR/BL/BR` turun 0 - 3.5 m (`SPUD_DROP`). Drop 0 to 3.5 m.
- Boom / stick batas sudut / limits: boom -15..75 deg, stick -110..10 deg.

Nilai ini berasal dari `kali_blender/excavator_spec.py` (sumber tunggal / single source of truth). Edit angka di sana, bukan di skrip build.

## Orientasi di Unity / Facing in Unity
- Ekskavator menghadap **-Y** di Blender (Blender "Front" view), sisi kirinya (`.L`, FL, BL) di **+X**.
- Ekspor memakai `-Z Forward` / `Y Up`, sehingga arah depan -Y di Blender menjadi **+Z (forward)** di Unity.
- Saat Play, pastikan panah biru (+Z) prefab root ekskavator menunjuk ke depan. Jika kebalik 180°, putar child mesh dengan Y = 180°.

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
| object_types | excavator: ARMATURE, MESH; tool dan trash: MESH | excavator memakai `use_armature_deform_only=True` |

Sebelum ekspor, semua transform diterapkan (Ctrl+A). `verify_fbx` mengimpor ulang file, memeriksa bone dan mesh, lalu menghapus hasil impor, sehingga scene tidak berubah.
Before export, all transforms are applied. `verify_fbx` re-imports the file, checks bones and meshes, then removes the imported data again.

## Struktur file / Layout
- `build_all.py`: pipeline utama, tiga tahap / main pipeline, three stages: `excavator`, `tools`, `trash`.
- `kali_blender/export_fbx.py`: ekspor FBX, apply transform, verifikasi / export, apply transforms, verify.
- `kali_blender/excavator_spec.py`, `kali_blender/tools_common.py`, `kali_blender/trash_common.py`: data dan helper bersama / shared data and helpers.
- `kali_blender/tools/`, `kali_blender/trash/`: modul per aset / one module per asset.
- `kali_blender/labels.py`, `kali_blender/trash_shapes.py`: label merek prosedural dan builder bentuk sampah / procedural brand labels and trash shape builders.
- `tools_check.py`: cek dan render tool satu per satu / check and render tools one at a time.
- `tests/test_export.py`: tes ekspor dengan stand-in / export tests with stand-ins.

## Catatan rig / Rig notes

- Batas sudut boom (-15..75 deg) dan stick (-110..+10 deg) dipasang sebagai Limit Rotation (FK) dan IK limits.
  Solver IK legacy Blender **mengabaikan IK limits kalau pole target dipakai** (diverifikasi: tanpa pole 0/357
  titik target melanggar, dengan pole 132/357). Pole `POLE_Elbow_Target` tetap dipakai karena diminta spec, jadi saat
  animasi pakai IK, jaga `CTRL_IK_Bucket` di area kerja wajar. Jarak maksimum controller dikunci Limit Distance (6.86 m).
- Pasangan Damped Track Base <-> Rod membentuk dependency cycle di depsgraph (sesuai spec). Untuk evaluasi lewat
  script panggil `excavator_rig.evaluate(armature)`; di viewport Blender cukup ganti frame / geser controller lagi.
- Constraint Blender tidak ikut ke Unity. Di Unity, gerakkan bone (atau bake animasi dengan `bake_anim`).
- QA lengkap: `python blender/tests/qa_spec_check.py` (setelah `build_all.py`).
