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
- **Produk bersih / clean products** (`SM_Product_*`, 150-400 tris each): the 9 parody brands new and intact, origin on the base.
  One shared atlas material `M_Products_Atlas`. Output: `unity/Assets/_Project/Props/Products/Meshes/`, `Props/Products/Textures/`,
  pack `blender/SM_Products_Pack.blend` (collection `Products_Preview`).
- **Peralatan lampu / lighting equipment** (`SM_Prop_*`, 150-400 tris each): warung roof lantern, Pintu Air warning beacon
  and its spinning rotor, clean, origin on the mount. Atlas `M_Equipment_Atlas` (+ Emission map). Output:
  `unity/Assets/_Project/Props/Equipment/Meshes/`, `Props/Equipment/Textures/`, pack `blender/SM_Equipment_Pack.blend`.
- **Rigging** (stage `rigging`): `SK_VillagerNPC` (kampung villager, 1200-1800 tris, Unity Humanoid bones,
  takes `Idle` / `ThrowTrash` / `CarryBin`), its props `SM_Villager_TrashBag` / `SM_Villager_Bin`, and
  `Anim_PlayerToolSwing` (Generic `ToolHolder` rig, takes `SerokanScoop` / `GancoHookSwing`).
  Output: `unity/Assets/_Project/Rigging/*.fbx`, `Rigging/Textures/T_Villager_Palette.png`,
  `blender/SK_VillagerNPC.blend`, `blender/Anim_PlayerToolSwing.blend`. NPC + interaction takes and `SM_Villager_FishingRod` come from `villager_clips.py`, body variants / accessories / per-NPC palettes from `villager_variants.py`, first-person arms (`SK_PlayerArms`) from `player_arms.py`. Unity usage: `unity/Assets/_Project/Rigging/README.md`.
  Animated FBX keep `bake_space_transform=False` (Apply Transform is unsafe with armature animation) and
  export one take per NLA strip, so take names are exact. QA: `blender -b --factory-startup -P blender/tests/qa_rigging_check.py`;
  renders: `blender -b --factory-startup -P blender/tests/render_rigging_qa.py -- OUT_DIR`.
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
Sebelas sampah kemasan Indonesia (9 + 2 air mineral AQUO dari prop lama), kotor dan lusuh tapi mereknya langsung terbaca. Eleven Indonesian packaging props (9 + 2 AQUO water bottles ported from the old props),
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
| 12 | `SM_Trash_AquaBottle_600ml` | Botol PET air mineral 600 ml, label parodi "AQUO", tutup biru, gepeng, penyok, rebah | 0.22 x 0.07 x 0.05 | 236 |
| 13 | `SM_Trash_AquaGalon_19L` | Galon polikarbonat biru 19 L, rib, stiker "AQUO", tutup putih, penyok, rebah (mengapung tinggi) | 0.48 x 0.27 x 0.27 | 332 |
| 14 | `SM_Trash_BiohazardDrum` | Drum B3 200 L ungu `#A855F7` + pita lime `#84CC16`, trefoil + stensil BIOHAZARD, penyok, bocor (cairan lime), rebah | 0.89 x 0.58 x 0.58 | 356 |

Prefab `PF_Trash_<nama>` dibuat dengan menu Unity yang sama (`KALI > JC > Build Trash Prefabs`).

## Peralatan lampu & sungai / Lighting and river equipment (equipment stage)
Mesh untuk prefab lampu (dibuat oleh `unity/Assets/_Project/Lighting/Editor/KaliLightingBuilder.cs`, menu
`KALI > Lighting > Build All Lighting Assets`). Meshes for the lighting prefabs; see `unity/Assets/_Project/Lighting/README.md`.
- Modul / modules: `kali_blender/equipment/` (`EQUIPMENT_MODULES` in `equipment_common.py`). Bersih (tanpa kotoran).
- Material `M_Equipment_Atlas`, atlas `T_Equipment_Atlas_{Albedo,Normal,Mask,Emission}.png` 2048. Swatch palet dengan nilai
  ke-4 `True` (bohlam, lensa) putih di peta Emission; Unity mewarnainya lewat `_EmissionColor`.
- **Pivot = titik pasang di lantai** (origin di dasar tiang / pelat / poros): importer menaruh origin prefab di atap.
  Origin = mount point on the floor plane; the importer drops the prefab origin on the roof top.

| Mesh | Benda / Object | Ukuran / Size (m) | Tris |
|---|---|---|---|
| `SM_Prop_LanternWarung` | Lampu warung: balok kaki, tiang bambu, lengan + penyangga, kap enamel hijau, bohlam (lampu 0.28 m ke depan, +Z Unity) | 0.16 x 0.42 x 0.56 | 306 |
| `SM_Prop_WarningBeacon` | Lampu rotator Pintu Air: pelat, rumah, kubah lensa amber, 4 batang pelindung | 0.16 x 0.16 x 0.21 | 214 |
| `SM_Prop_BeaconRotor` | Rotor: poros, hub motor, 2 reflektor krom saling membelakangi (origin = dasar poros) | 0.07 x 0.05 x 0.10 | 236 |
| `SM_Prop_TrashBoomSegment` | Segmen trash boom: pelampung oranye 2 bagian, rok hitam, braket + segel (shackle) di kedua ujung; pivot WATERLINE | 2.29 x 0.30 x 0.55 | 268 |
| `SM_Prop_RakitGabus` | Rakit gabus (perahu tier 1): 3 balok styrofoam, 4 bambu melintang, ikatan karet ban dalam; pivot WATERLINE | 1.81 x 1.40 x 0.37 | 704 |
| `SM_Prop_PerahuSampan` | Perahu sampan kayu 3.7 m (tier 2): papan dicat (ter, biru, putih, merah), 7 gading, 2 bangku, dayung di sandaran; pivot WATERLINE | 3.70 x 1.18 x 0.58 | 916 |
| `SM_Prop_TongSampahKampung` | Tong sampah kampung 200 L biru, stensil kuning SAMPAH ANORGANIK, tutup; pivot DASAR | 0.60 x 0.60 x 0.94 | 330 |

Budget per aset di SPEC (`tris`, `max_size`, `pivot`): lampu 150-400, boom 200-400, rakit 500-900, sampan 700-1200, tong 250-400.
Pivot WATERLINE = origin di permukaan air (importer menaruh `trash_boom` di y = 0), tengah x/y. Prefab `PF_Prop_*` untuk
boom / perahu / tong dibuat oleh `KALI > JC > Build Equipment Prefabs` (BoxCollider, tanpa Rigidbody); lampu/beacon oleh
`KALI > Lighting > Build All Lighting Assets`. Keduanya memakai satu material `Props/Equipment/Materials/M_Equipment_Atlas.mat`.

## Produk bersih / Clean products (products stage)
Versi BARU dan utuh dari 9 barang yang sama (merek parodi yang sama): segel rapat, penuh, label bersih
(`labels.render_label(..., dirty=False)`), tanpa kusut/sobek/penyok. Untuk toko / item dunia, bukan sampah mengapung.
The same 9 parody-brand items, NEW and intact (sealed, full, clean labels, no crumple/tears/dents): shop and world items.
- Modul / modules: `kali_blender/products/` (`PRODUCT_MODULES` in `products_common.py`); bentuk memakai ulang
  builder dan profil dari modul trash (`trash_shapes`, ring botol, tray styrofoam, shell kotak rokok).
- Material `M_Products_Atlas`, atlas `T_Products_Atlas_{Albedo,Normal,Mask}.png` 2048, skema sel sama dengan trash.
- Output: `unity/Assets/_Project/Props/Products/Meshes/SM_Product_*.fbx`, `Props/Products/Textures/`, `blender/SM_Products_Pack.blend`.
- Budget **150-400 tris**. **Pivot = tengah dasar bbox** (origin di lantai, tengah tapak): produk berdiri di rak / tanah.
  Origin = centre of the bbox BOTTOM, so a prefab dropped at shelf or floor height stands on it (tolerance 0.02 m).
- Berdiri tegak bila produk aslinya berdiri (botol, pouch, kotak rokok, kotak styrofoam); bungkus bantal, sachet dan roti
  tidur dengan label menghadap atas. Upright where the real product stands; pillow packs, sachet and bread lie print-up.
- Prefab `PF_Product_<nama>` dibuat di Unity: `KALI > JC > Build Product Prefabs` (BoxCollider padat, tanpa Rigidbody / RiverTrashItem).

| # | Mesh / Prefab | Benda / Object | Ukuran / Size (m) | Tris |
|---|---|---|---|---|
| 01 | `SM_Product_Indomy` | Bungkus mi goreng "Indomy", tersegel, tebal, rebah | 0.12 x 0.10 x 0.02 | 256 |
| 02 | `SM_Product_KecapBingo` | Pouch refill kecap manis "BINGO", penuh, berdiri, takik sobek | 0.17 x 0.07 x 0.25 | 176 |
| 03 | `SM_Product_Moli` | Sachet "MOLI" 22 g, tersegel, rebah | 0.10 x 0.10 x 0.01 | 168 |
| 04 | `SM_Product_Lifeman` | Botol sampo "Lifeman", tutup flip tertutup, berdiri | 0.06 x 0.04 x 0.20 | 260 |
| 05 | `SM_Product_SariBoti` | Roti sobek "SARI BOTI" dalam plastik (4 x 2 roti), rebah | 0.28 x 0.15 x 0.05 | 288 |
| 06 | `SM_Product_Risol` | Pouch deterjen "Risol", penuh, berdiri | 0.20 x 0.08 x 0.30 | 176 |
| 07 | `SM_Product_StyrofoamMakanan` | Kotak nasi styrofoam baru, tertutup | 0.19 x 0.18 x 0.10 | 194 |
| 08 | `SM_Product_Sprit` | Botol PET "Sprit" 1.5 L, penuh (badan hijau lebih tua di bawah garis isi), berdiri | 0.09 x 0.09 x 0.32 | 332 |
| 09 | `SM_Product_GudangGula` | Bungkus rokok "GUDANG GULA International", tertutup, berdiri | 0.06 x 0.02 x 0.09 | 168 |

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
blender -b --factory-startup -P blender/build_all.py -- --only products
blender -b --factory-startup -P blender/build_all.py -- --only equipment
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
- `kali_blender/products_common.py`, `kali_blender/products/`: produk bersih (stage `products`) / clean product props.
- `kali_blender/equipment_common.py`, `kali_blender/equipment/`: peralatan lampu (stage `equipment`) / lighting equipment meshes.
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
