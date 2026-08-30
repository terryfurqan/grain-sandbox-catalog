# CONTEXT: GRAIN Explorer Centralized Cataloguing System

## 1. Domain & Arsitektur Direktori

Sistem Katalogisasi GRAIN Explorer adalah infrastruktur pencatatan, pengindeksan, dan validasi data pemodelan analog tektonik (*Sand-box Analog Tectonic Modeling*) yang menghubungkan penyimpanan fisik lokal, backend manifest sentral, dan platform penampil web/cloud.

### Topologi Direktori:
```text
D:\999_GRAIN_EXPLORER\
├── 0000/                           # [BACKEND MANIFEST SENTRAL]
│   ├── catalog.db                  # Database SQLite (metadata instan, tabel experiments & files)
│   ├── manifest.json               # Master JSON Catalog manifest
│   ├── taxonomy_rules.json         # Aturan baku validasi mesin taksonomi
│   ├── audit_report.json           # Laporan audit integritas & kepatuhan folder
│   └── README.md                   # Spesifikasi data backend
│
└── 0010/                           # [EXPERIMENT VAULT - PROCESSED DATA]
    ├── TALAWANG - 300626 (EXP 1)/  # 1 Folder = 1 Eksperimen (Flat Direct Taxonomy)
    │   ├── 0.1. RAW - Trial M/
    │   ├── 1.1. RAW - M/
    │   ├── 1.2. Resize - M - .../
    │   ├── 4a.1. RAW - Slice M/
    │   ├── 4b.1. RAW - Slice P/
    │   ├── 5.1. RAW - 3D/
    │   └── OUTPUT/
    └── TALAWANG - 280826 (EXP 2)/
```

---

## 2. Peran Workspace `c:\TERR\4. WORK\7. CATALOGUING`

Folder ini berfungsi sebagai **Pusat Pengembangan & Otomasi Sinkronisasi Katalog**:
1. `TAXONOMY_RULES.md`: Standar taksonomi baku GRAIN 2.0.
2. `grain_catalog_indexer.py`: Script Python berkinerja tinggi untuk memindai `0010`, mengekstrak metadata gambar/video/QPIV/PIV, memvalidasi kepatuhan taksonomi, dan memperbarui `catalog.db` serta `manifest.json` di `0000`.
3. `run_catalog_sync.bat` / `run_catalog_sync.ps1`: Skrip 1-klik untuk menjalankan sinkronisasi katalog secara instan.
4. Git remote link ke repositori ekosistem: `https://github.com/terryfurqan/grain-sandbox-catalog.git`.

---

## 3. Alur Kerja Sinkronisasi (*Sync Workflow*)

1. **Scan & Parse**: Indexer mendeteksi semua folder eksperimen di `D:\999_GRAIN_EXPLORER\0010\`.
2. **Taxonomy Verification**: Setiap subfolder dipetakan terhadap aturan kode (`0.x` s.d. `5.x` dan `OUTPUT/`).
3. **Deep Metadata Extraction**:
   - Menghitung jumlah frame & ukuran file.
   - Mendeteksi kurva shortening QPIV & log frame pruning (`OUTPUT/QPIV/`).
   - Mendeteksi luaran video timelapse MP4 (`OUTPUT/VIDEOS/`).
   - Mendeteksi berkas presentasi akhir (`OUTPUT/REPORTS/*.pptx`).
   - Mendeteksi container biner `.grainraw` / `.npz` (`OUTPUT/GRAINRAW/` atau PIV).
4. **Database & JSON Generation**:
   - Menulis/memperbarui data secara atomic ke SQLite `D:\999_GRAIN_EXPLORER\0000\catalog.db`.
   - Mengompilasi `D:\999_GRAIN_EXPLORER\0000\manifest.json`.
   - Menerbitkan `D:\999_GRAIN_EXPLORER\0000\audit_report.json`.
