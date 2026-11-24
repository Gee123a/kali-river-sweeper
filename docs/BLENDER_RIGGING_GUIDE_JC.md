# KALI: Indonesian River Sweeper — Blender 5.3 Rigging & 3D Asset Spec

**Author / Architect**: Stevanus Ivan Santoso (Lead Technical Architect)  
**Target Lead**: Jason Christopher (3D Props, Rigging & Lighting Lead)  
**Engine Target**: Unity 2022.3.46f1 LTS (Universal Render Pipeline)  
**Software**: Blender 5.3.0+  
**Hero Rigged Asset**: `SK_ExcavatorAmfibi.fbx`  

---

## 1. Executive Summary & Deliverables for JC

Jason, ini panduan teknis dan blueprint rigging untuk hero asset utama game kita: **Ekskavator Amfibi Pengeruk Sungai (`SK_ExcavatorAmfibi`)** dan paket 20 perkakas sampah.

Semua penamaan bone, hierarki IK, dan constraint piston hidrolik dirancang agar **langsung plug-and-play di Unity URP** tanpa bug rotasi terbalik atau sumbu melenceng.

![Excavator Rigging Architecture Blueprint](/Users/mynamegee/kali-river-sweeper/docs/excavator_rigging_architecture_blueprint.png)

---

## 2. Struktur Anatomi & Ukuran Ekskavator Amfibi

* **Ponton Apung (Catamaran Hull)**:
  * Dimensi: Panjang 7.2m, Lebar 4.8m, Tinggi ponton 1.4m.
  * Dilengkapi 4 tiang pancang jangkar vertikal (*Spud Legs*) di tiap sudut untuk menancap ke dasar kali saat mengeruk sampah berat.
* **Rumah Mesin & Kabin (Turret Slew)**:
  * Berputar 360° horizontal pada sumbu Z di atas cincin bantalan (*slew ring*).
  * Dilengkapi kabin operator kaca, knalpot diesel hitam, dan counterweight pemberat di belakang.
* **Lengan Pengeruk 3-Segmen (Articulated Boom & Arm)**:
  * **Boom** (Lengan Utama): Panjang 4.2m, sudut angkat -15° s/d +75°.
  * **Stick / Dipper** (Lengan Depan): Panjang 2.8m, sudut tekuk -110° s/d +10°.
  * **Bucket / Keruk Gigi**: Lebar 1.4m dengan 5 gigi baja tahan aus dan capit hidrolik (*thumb attachment*) untuk menjepit kasur dan batang kayu.

---

## 3. Hierarki Armature & Standar Penamaan Bone

Gunakan format penamaan bone baku berikut di Blender:

```
B_Root_Hull (Root ponton kapal di permukaan air)
 ├── B_Turret_Slew (Rotasi horizontal kabin 360°)
 │    ├── B_Arm_Boom (Sendi engsel lengan utama)
 │    │    ├── B_Arm_Stick (Sendi lengan depan)
 │    │    │    └── B_Tool_Bucket (Sendi bucket pengeruk / capit)
 │    │    │
 │    │    ├── B_Piston_Stick_Base (Silinder hidrolik stick)
 │    │    └── B_Piston_Bucket_Base (Silinder hidrolik bucket)
 │    │
 │    └── B_Piston_Boom_Base_L / R (Silinder hidrolik boom ganda)
 │
 ├── B_Spud_Leg_FL (Tiang pancang kiri depan, translasi Z turun 3.5m)
 ├── B_Spud_Leg_FR (Tiang pancang kanan depan)
 ├── B_Spud_Leg_BL (Tiang pancang kiri belakang)
 └── B_Spud_Leg_BR (Tiang pancang kanan belakang)

[BONE CONTROLLER NON-DEFORM]
 ├── CTRL_IK_Bucket (Target controller yang digerakkan animator)
 └── POLE_Elbow_Target (Pole vector pengarah siku lengan)
```

> [!IMPORTANT]
> Pastikan bone controller (`CTRL_IK_Bucket` dan `POLE_Elbow_Target`) di-uncheck **"Deform"** di tab *Bone Properties -> Deform* agar tidak menarik vertex mesh secara salah!

---

## 4. Panduan Step-by-Step Setup IK (Inverse Kinematics)

1. Masuk ke **Pose Mode** pada Armature.
2. Pilih bone `B_Arm_Stick`.
3. Buka tab **Bone Constraints** (ikon rantai bertulang) $\to$ **Add Bone Constraint** $\to$ pilih **Inverse Kinematics**.
4. Atur properti IK Constraint:
   * **Target**: Pilih Armature ekskavator.
   * **Bone**: `CTRL_IK_Bucket`.
   * **Pole Target**: Pilih Armature ekskavator $\to$ Bone: `POLE_Elbow_Target`.
   * **Pole Angle**: Biasanya `90°` atau `-90°` (sesuaikan sampai posisi siku lengan lurus vertikal).
   * **Chain Length**: **2** *(Sangat penting! Nilai 2 mengunci IK hanya menggerakkan Stick dan Boom, tidak memutar Turret atau Hull)*.
5. Pada bone `B_Tool_Bucket`:
   * Tambahkan constraint **Copy Rotation** atau kontrol manual rotasi bucket dengan bone controller tersendiri agar operator bisa menciduk sampah secara independen.

---

## 5. Setup Piston Hidrolik Otomatis (Zero-Clipping Damped Track)

Untuk membuat silinder hidrolik otomatis memanjang dan memendek tanpa perlu di-keyframe manual:

```
[B_Piston_Cylinder (Tabung Luar)] ── Damped Track (+Y) ──> [B_Piston_Ram (Batang As)]
      (Parent: Turret)                                           (Parent: Boom)
```

1. **Tabung Silinder Luar (`B_Piston_Boom_Base`)**:
   * Letakkan Head bone di engsel pangkal pada Turret.
   * Tail bone mengarah ke engsel lengan Boom.
   * Parent: `B_Turret_Slew`.
   * Beri constraint: **Damped Track**.
   * Target: Armature $\to$ Bone: `B_Piston_Boom_Rod`.
   * Track Axis: `+Y`.
2. **Batang As Dalam (`B_Piston_Boom_Rod`)**:
   * Letakkan Head bone di engsel pada lengan Boom.
   * Tail bone mengarah balik ke engsel silinder di Turret.
   * Parent: `B_Arm_Boom`.
   * Beri constraint: **Damped Track**.
   * Target: Armature $\to$ Bone: `B_Piston_Boom_Base`.
   * Track Axis: `+Y`.
3. **Hasil**: Saat boom naik/turun, batang as chrome akan meluncur mulus keluar-masuk tabung silinder secara otomatis 100% presisi tanpa tembus atau melenceng.
4. Terapkan metode yang sama persis untuk hidrolik Stick dan hidrolik Bucket!

---

## 6. Aturan Material & Shading URP

Bagi model ekskavator menjadi **3 Material Slot** terpisah:

| Slot Material | Nama Material | Properti PBR | Elemen Model |
| :--- | :--- | :--- | :--- |
| **Slot 1** | `M_Excavator_Body` | Albedo: Kuning industri `#eab308`<br>Metallic: `0.15`<br>Smoothness: `0.45` | Bodi kabin, boom arm, stick arm, pelindung mesin. Tambahkan karat di tepian tajam. |
| **Slot 2** | `M_Hydraulic_Steel`| Albedo: Abu-abu chrome `#e2e8f0`<br>Metallic: `0.95`<br>Smoothness: `0.90` | Batang as silinder hidrolik yang mengkilap, pin engsel baja, kabel baja winch. |
| **Slot 3** | `M_Pontoon_Rubber` | Albedo: Hitam karet kusam `#1e293b`<br>Metallic: `0.0`<br>Smoothness: `0.20` | Bumper karet samping, tapak anti-selip, spud legs, lumpur dasar kali. |

---

## 7. Checklist Export FBX ke Unity 2022.3 LTS

Sebelum export ke `.fbx`, wajib jalankan checklist ini di Blender:

1. **Apply All Transforms**:
   * Di Object Mode, pilih mesh dan armature: tekan `Ctrl + A` $\to$ pilih **All Transforms**.
   * Pastikan di panel Transform (N): *Location: (0,0,0), Rotation: (0,0,0), Scale: (1,1,1)*.
2. **Pengaturan Dialog Export FBX**:
   * **Path Mode**: `Copy` (klik ikon embed texture di sebelahnya).
   * **Include**: Centang `Selected Objects` (pilih mesh + armature).
   * **Transform**:
     * Scale: `1.0`
     * Apply Scalings: `FBX All`
     * Forward: `-Z Forward`
     * Up: `Y Up`
     * Centang `Apply Unit` dan `Apply Transform`.
   * **Geometry**:
     * Smoothing: `Face` atau `Normals Only`.
   * **Armature**:
     * Centang `Only Deform Bones` (jika controller IK dibuat di luar).
     * **HAPUS CENTANG (UNCHECK) `Add Leaf Bones`** *(Wajib mati! Jika nyala, Blender akan membuat bone sampah di setiap ujung bone yang merusak rig Unity)*.
   * **Bake Animation**: Centang jika ada clip animasi idle/scoop yang sudah di-bake.
3. **Simpan File**:
   * Simpan di: `unity/Assets/_Project/Art/Props/Vehicles/SK_ExcavatorAmfibi.fbx`.

---

## 8. Panduan Modeling 20 Perkakas Sampah (Tools Catalog)

Untuk 20 perkakas sampah yang telah di-itemized (mulai dari sendok bengkok, gayung bolong, serokan bambu, ganco, ember cat, hingga pompa vakum 49cc):

* **Polycount Target**: 300 – 1.200 triangles per perkakas (sangat ramah performa).
* **Pivot Point**: Wajib berada tepat di **posisi genggaman tangan pemain** `(0, 0, 0)` dengan arah gagang menghadap `+Z` atau `+Y` agar saat di-attach ke socket tangan pemain di Unity, perkakas langsung terpegang pas tanpa offset rotasi aneh.
* **Atlas Tekstur**: Gabungkan 20 alat ke dalam 1 atau 2 lembar Texture Atlas 2048x2048 (`T_Tools_Atlas_Albedo.png`, `T_Tools_Atlas_Normal.png`, `T_Tools_Atlas_Mask.png`) agar menghemat draw call Unity.
