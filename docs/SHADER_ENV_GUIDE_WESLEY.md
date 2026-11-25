# KALI: Indonesian River Sweeper — Environment & URP Shader Spec

**Author / Architect**: Stevanus Ivan Santoso (Lead Technical Architect)  
**Target Lead**: Wesley Goeinawan (Environment Architecture & Shaders Lead)  
**Engine Target**: Unity 2022.3.46f1 LTS (Universal Render Pipeline)  
**Deliverables**: 10 `SM_Env_*` Meshes + `SG_KaliWater` + `SG_TrashTriplanar`  

---

## 1. Sinkronisasi Kode C# (`RiverMath` & `RiverGameManager`)

Semua bangunan dan air sungai harus mengikuti angka koordinat asli di `RiverFlowBuoyancy.cs` dan `MapJsonImporter.cs` supaya tidak ada rumah melayang atau sungai tembus daratan:

* **Ukuran Peta World Unity**: `130m (X) × 180m (Z)` (`WorldW = 1040`, `WorldH = 1440`, `MapScale = 0.125`).
* **Rumus Lengkungan Sungai (`RiverMath`)**:
  * Pusat sungai: `CenterX = 520 + sin((mapY / 1440) * PI * 1.6) * 58`
  * Lebar normal: `22.5m` (`180 * 0.125`), menyempit di **Jembatan Utama (`mapY = 740`)**, melebar di **Teluk Hulu (`mapY < 320`)** dan **Teluk Selatan (`mapY = 1220`)**.
* **Arah Arus Sungai**: Mengalir menuju **`-Z`** ke arah **Pintu Air & Gunung Sampah**.

---

## 2. Daftar 10 Mesh Environment (`Assets/_Project/Environment/Meshes/`)

| Nama File FBX | Budget Tris | Jumlah Node | Detail Visual & Pivot Rules |
| :--- | :--- | :--- | :--- |
| `SM_Env_RiverValleyTerrain` | 3000–5000 | Terrain Root | Palung sungai S-curve 130m×180m sesuai `RiverMath`. Permukaan air di `Y = 0.0m`, daratan kampung di `Y = +0.8m` s/d `+2.0m`. |
| `SM_Env_GunungSampah_3Tiers` | 2500–4000 | 3 nodes | Gunungan sampah 3 lapis (raksasa) yang menyumbat Pintu Air; masing-masing tier bisa disembunyikan saat dikeruk. |
| `SM_Env_PintuAirSiaga1` | 2000–3000 | 1 node | Bendungan beton sluice gate dengan menara katrol manual (**sisakan atap menara untuk `PF_WarningBeacon_PintuAir`**). |
| `SM_Env_JembatanUtama` | 1200–2000 | 1 node | Jembatan beton kampung melintasi titik sempit (`choke point`) tengah sungai. |
| `SM_Env_BankSampah` | 1200–1800 | 1 node | Pos setor Bank Sampah Berkah: area drop-off, timbangan gantung, meja buku kas. |
| `SM_Env_PosSortir` | 1000–1500 | 1 node | Area sortir terbuka, rak botol PET, tempat pengepresan karung. |
| `SM_Env_RumahPanggung` | 800–1500 | 11 nodes | Rumah panggung bantaran kali: tiang bambu/kayu, papan lapuk, atap seng berkarat. |
| `SM_Env_TokoAlat` | 800–1200 | 1 node | Bengkel alat & perahu: rak bambu, sparepart baling-baling klotok, pompa rakitan. |
| `SM_Env_Warung` | 600–1000 | 7 nodes | Warung kopi & mie pinggir kali (**sisakan area atap depan untuk `PF_Lantern_Warung`**). |
| `SM_Env_Dermaga` | 400–800 | 2 nodes | Dermaga papan kayu + bumper ban bekas (**Pivot wajib di tepi permukaan air `Y = 0`**). |

**Aturan Export FBX (Blender -> Unity):**
* Apply All Transforms (`Ctrl + A -> All Transforms`, Scale `1.0`, Rot `0,0,0`).
* Transform: `-Z Forward`, `Y Up`.
* Pivot semua gedung diletakkan di **Bottom Center (`Y = 0`)** kecuali `SM_Env_Dermaga` di garis air (`Y = 0`).

---

## 3. Spesifikasi Shader 1: `SG_KaliWater` (`Assets/_Project/Shaders/`)

Shader air sungai ini **terhubung langsung ke script C# (`RiverGameManager.cs`)**:

1. **Hook Global Shader Float (WAJIB SAMA PERSIS)**:
   * Di Blackboard URP Shader Graph, buat property **Float** dengan **Reference Name**: `_WaterClarity` (huruf besar-kecil persis).
   * C# otomatis memanggil `Shader.SetGlobalFloat("_WaterClarity", waterClarity)` dari `0.12` (coklat keruh tercemar) ke `1.00` (hijau-biru jernih saat kali bersih).
2. **Beer-Lambert Depth Color Absorption**:
   * Hitung selisih kedalaman: `Scene Depth (Eye)` dikurangi `Screen Position (W)`.
   * Masukkan ke node `Lerp` antara warna air keruh/dangkal (`#3B2818`) dan air bersih (`#1B6B63`) dikendalikan oleh `_WaterClarity`.
3. **Dual-Flow Normal Panning (`-Z` Downstream)**:
   * Pakai 2 node `Sample Texture 2D (Normal)` dengan UV Tiling `(2, 8)` yang digeser searah `-V` (`Time * -0.15` dan `Time * -0.09`), lalu gabung dengan `Normal Blend`.
4. **Shoreline & Obstacle Foam**:
   * Pakai `Step(0.35, DepthDiff)` dikali `Simple Noise` untuk menghasilkan buih putih otomatis di tepian tanggul, tiang jembatan, dermaga, dan di sekitar `GunungSampah`.
5. **Sinkronisasi Ombak**:
   * Vertex displacement Sine ringan (`Amplitude 0.05m`) mengikuti `RiverFlowBuoyancy.bobAmplitude`.

---

## 4. Spesifikasi Shader 2: `SG_TrashTriplanar` (`Assets/_Project/Shaders/`)

Digunakan khusus pada `SM_Env_GunungSampah_3Tiers` agar tekstur gunungan sampah yang masif tidak pernah melar (*UV stretching*):

1. **World-Space Triplanar Mapping**: Gunakan node `Triplanar` memakai `Position (World)` (`Blend = 4.0`) untuk Albedo dan Normal.
2. **3-Band Height Blending (Y World Position)**:
   * `Y < 0.8m` (Garis air): Lumpur hitam basah mengkilap (`Smoothness 0.8`).
   * `0.8m – 2.5m` (Tengah): Kasur kapuk basah, kain kusut, dan kantong limbah medis kuning.
   * `Y > 2.5m` (Puncak): Botol plastik PET kering, kresek kusam, dan styrofoam (`Smoothness 0.2`).
3. **Vertex Color Dirt Mask**: Kalikan channel **Red** Vertex Color untuk menyamarkan sambungan antar tier tumpukan sampah secara natural.
