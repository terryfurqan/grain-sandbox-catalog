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
