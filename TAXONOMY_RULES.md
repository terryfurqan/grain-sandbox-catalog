# 🏛️ GRAIN 2.0 Sandbox Experiment Taxonomy & Folder Standards
*Flat Direct Taxonomy Rules for Centralized Cataloguing*

Aturan baku manajemen folder eksperimen pemodelan analog tektonik dan geologi (*Sand-Box Analog Tectonic Modeling*) yang terintegrasi pada repositori sentral `D:\999_GRAIN_EXPLORER` (Backend Manifest `0000` & Experiment Vault `0010`).

---

## 📂 1. Format Nama Folder Utama (Root Eksperimen)

Setiap eksperimen sandbox disimpan sebagai satu folder mandiri di dalam `D:\999_GRAIN_EXPLORER\0010\` dengan format baku:

$$\mathbf{[PROJECT] - [DDMMYY] \text{ (EXP [N])}}$$

- **`[PROJECT]`**: Nama formasi/proyek riset geologi (contoh: `TALAWANG`, `MAHAKAM`, `KUTAI`, `BARITO`).
- **`[DDMMYY]`**: Tanggal pelaksanaan eksperimen dalam 6 digit angka (contoh: `280826` untuk 28 Agustus 2026).
- **`(EXP [N])`**: Nomor urut eksperimen pada tanggal/sesi tersebut (contoh: `(EXP 1)`, `(EXP 2)`).

**Contoh Valid**:
- `TALAWANG - 280826 (EXP 2)`
- `TALAWANG - 300626 (EXP 1)`

---

## 🏷️ 2. Aturan Kode Prefiks Nomor & Kategori Sudut Pandang

Seluruh folder turunan diletakkan **langsung di root eksperimen** (*Flat Direct Hierarchy*) tanpa subfolder pengelompokan perantara:

| Kode Prefiks | Kategori / Sudut Pandang | Sub-tipe | Contoh Format Folder | Deskripsi Geologis |
| :--- | :--- | :--- | :--- | :--- |
| **`0.x`** | **Trial / Pre-run** | `0.1` RAW<br>`0.2+` Resize | `0.1. RAW - Trial M`<br>`0.2. Resize - Trial M - [W]x[H] px (CO)` | Uji coba pencahayaan/kamera sebelum motor penggerak sandbox aktif. |
| **`1.x`** | **Map View (Top View)** | `1.1` RAW<br>`1.2+` Resize<br>`1.4` Grayscale | `1.1. RAW - M`<br>`1.2. Resize - M - [W]x[H] px (CO)`<br>`1.3. Resize - M - [W]x[H] px (CO 1)`<br>`1.4. Resize - M - [W]x[H] px (Grayscale)` | Foto tampak atas time-lapse untuk analisis perambatan sesar & PIV. |
| **`2.x`** | **Profile View 1 (P1)** | `2.1` RAW<br>`2.2+` Resize | `2.1. RAW - P1`<br>`2.2. Resize - P1 - [W]x[H] px (Crop)` | Foto penampang samping/profil kamera 1. |
| **`3.x`** | **Profile View 2 (P2)** | `3.1` RAW<br>`3.2+` Resize | `3.1. RAW - P2`<br>`3.2. Resize - P2 - [W]x[H] px (Crop)` | Foto penampang samping/profil kamera 2. |
| **`4a.x`** | **Slice M (Irisan Map)** | `4a.1` RAW<br>`4a.2+` Resize | `4a.1. RAW - Slice M`<br>`4a.2. Resize - Slice M - [W]x[H] px (Crop)` | Foto irisan vertikal tampak atas serial setelah model diairi/dibekukan. |
| **`4b.x`** | **Slice P (Irisan Profil)** | `4b.1` RAW<br>`4b.2+` Resize | `4b.1. RAW - Slice P`<br>`4b.2. Resize - Slice P - [W]x[H] px (Crop)` | Foto penampang irisan samping serial. |
| **`5.x`** | **3D / Oblique View** | `5.1` RAW<br>`5.2+` Resize | `5.1. RAW - 3D`<br>`5.2. Resize - 3D - [W]x[H] px (CO)` | Sudut pandang miring / perspektif 3D morfologi model. |
| **`OUTPUT/`** | **Luaran & Analisis** | Sub-ekosistem | `OUTPUT/` | Folder terpadu hasil komputasi, PIV, video, dan laporan presentasi. |

---

## 📐 3. Konvensi Suffix & Label Tambahan

- **`[W]x[H] px`**: Dimensi resolusi piksel citra hasil olahan (misal: `4227x3171 px`, `4500x3243 px`).
- **`(CO)` / `(CO 1)`**: *Color Option* / koreksi warna (*contrast grading/white balance*).
- **`(Crop)`**: Citra yang telah dipotong sesuai batas *Region of Interest* (ROI) sandbox.
- **`(Grayscale)`**: Citra monokrom 8-bit untuk input algoritma komputasi cross-correlation PIV.

---

## 📁 4. Struktur Terpadu Folder `OUTPUT/`

```text
OUTPUT/
├── GRAINRAW/    # Wadah biner .grainraw & moving_frames_list.txt
├── QPIV/        # Log penapisan frame mati (pruning) & kurva shortening/strain
├── VIDEOS/      # Video MP4 time-lapse 720p/1080p + counter strain (%)
├── SLICES/      # Slide komparasi irisan vertikal serial (Slice M & P)
├── REPORTS/     # Slide PowerPoint komprehensif evolusi 5% (.pptx)
└── SCRIPTS/     # Skrip python otomasi & subfolder backup revision/
```

---

## 🔍 5. Standar Deduplikasi & Audit Integritas (MD5)

1. **MD5 Checksum Audit**: Setiap file foto dan video diaudit nilai hash-nya untuk mencegah duplikasi nama/isi file.
2. **Eliminasi File Redundan**: File salinan otomatis bertanda ` - Copy.jpg` atau folder subset sampling yang 100% identik dieleminasi.
3. **Zero Data Loss Guarantee**: Verifikasi integritas dilakukan sebelum proses pengarsipan atau katalogisasi manifest.

---

## 🧭 6. Standar Klasifikasi & Metadata Eksperimen (5 Pilar GRAIN 2.0)

Skema klasifikasi terstandarisasi untuk kategorisasi eksperimen analog tektonik:

### Pilar 1: Intent & Target Geologi
- **Intent**: `Research` (Riset akademis/internal) | `Project` (Studi komersial/klien/industri)
- **Project Name (Wajib jika Intent = Project)**: Nama kontrak/studi proyek spesifik (misal: `KUFPEC Kutai Study 2026`, `BP Berau Deepwater Inversion`, `Pertamina Hulu Mahakam Analog Sandbox`).
- **Research Topic (Opsional jika Intent = Research)**: Topik riset spesifik / hibah riset (misal: `Fundamental Salt Diapirism R&D`, `Thrust Wedge Taper Mechanics`).
- **Project/Basin Target**: Nama formasi atau cekungan geologi (misal: `TALAWANG`, `MAHAKAM`, `KUTAI`, `BARITO`, `OMBILIN`).
- **Target Gaya Struktur (*Target Structural Style*)**:
  - `Fold-and-Thrust Belt (FTB / Thrust Wedge)`
  - `Rift Graben / Half-Graben (Normal Faults)`
  - `Pull-Apart Basin (Transtensional)`
  - `Transpressional Pop-Up / Positive Flower`
  - `Inversion Anticline (Positive/Negative Inversion)`
  - `Salt/Ductile Tectonics (Diapir / Pillow / Canopy)`
  - `Delta Gravity-Driven / Toe-Thrust`
  - `Basement-Involved Fault-Propagation`

### Pilar 2: Kinematika & Mesin Penggerak
- **Jenis Sistem Tektonik**: `Extensional` | `Contractional` | `Strike Slip` | `Hybrid`
- **Mesin yang Dipakai**:
  - `IAGI - Dorong` | `IAGI - Tarik`
  - `BP - Dorong` | `BP - Tarik` | `BP - Dorong-Tarik`
  - `KUFPEC squeeze` | `KUFPEC base plate` | `KUFPEC mix`
- **Tipe Detachment / Kondisi Batas Alas**:
  - `Rigid Mobile Wall (Piston)`
  - `Basal Mylar/Sheet (Conveyor Pull)`
  - `Rubber Sheet (Elastic Stretching)`
  - `Basal Fault Ramp/Step`
  - `Dual Mobile Wall (Symmetric/Asymmetric)`
- **Kemiringan Basal Detachment**: Rentang sudut `-30°` (down-dip) s.d. `+30°` (up-dip)
- **Tahapan Deformasi**:
  - `Single Phase`
  - `Multi-Phase Inversion (Ext -> Comp)`
  - `Multi-Phase Reactivation (Comp -> Ext)`
  - `Transtension/Transpression Sequence`

### Pilar 3: Material & Stratigrafi Pasir
- **Ketebalan Total Pasir**: `< 1 cm`, `1 cm`, `2 cm`, `3 cm`, `4 cm`, `5 cm`, `6 cm`, `7 cm`, `8 cm`, `9 cm`, `10 cm`, `> 10 cm`
- **Material Campuran (Multi-select)**:
  - `Sand` (Pasir kuarsa kering)
  - `Gypsum` (Plaster rapuh)
  - `Beads (Microbeads / Glass beads)`
  - `Silicone/PDMS (Ductile Decollement / Salt Analogue)`
  - `Basement Involved (Rigid Pre-cut Block / Fault Step)`
- **Reuse Sand (Daur Ulang)**: `Yes` | `No`
- **Sedimentasi / Erosi Syn-kinematik**:
  - `None`
  - `Incremental Infill (Syn-kinematic Sedimentation)`
  - `Continuous Infill`
  - `Syn-kinematic Erosion`

### Pilar 4: Akuisisi Citra & PIV (Auto-Resolved)
- **Kamera & Optik (dari EXIF 1.1 RAW)**: Model kamera, Lensa, Focal Length, ISO, Shutter Speed, Aperture, Resolusi RAW, Pixel Scale (mm/px).
- **Sudut Pandang Tersedia (dari Taksonomi Folder)**: Map View (`1.x`), Profile P1 (`2.x`), Profile P2 (`3.x`), Slice M (`4a.x`), Slice P (`4b.x`), 3D Oblique (`5.x`).
- **Parameter PIV (dari .npz / JSON)**: Multi-pass sequence (misal `64 -> 32 -> 25 px`), Final IW (`25 px`), Overlap (`75%`), Continuous Window Shifting (CWS), Normalized Median Test outlier filter, Vector fields ($|V|, \gamma_{xy}, u, v$).

### Pilar 5: Luaran Analisis & Deliverables (Auto-Detected di `OUTPUT/`)
- `QPIV Shortening Curve & Pruning Log` (`OUTPUT/QPIV/`)
- `.grainraw Binary Container` (`OUTPUT/GRAINRAW/`)
- `Single Velmag MP4 Timelapse` (`OUTPUT/VIDEOS/`)
- `Dual Split-Screen VMSST MP4 Timelapse` (`OUTPUT/VIDEOS/`)
- `Normalized PIV MP4 Timelapse` (`OUTPUT/VIDEOS/`)
- `Serial Slice Comparison Slide` (`OUTPUT/SLICES/`)
- `Evolution 5% PowerPoint Report (.pptx)` (`OUTPUT/REPORTS/`)

