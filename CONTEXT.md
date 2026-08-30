# CONTEXT: GRAIN Explorer Centralized Cataloguing & Data Server System

## 1. Domain & Arsitektur Direktori

Sistem Katalogisasi **GRAIN Explorer** adalah infrastruktur pencatatan, pengindeksan, streaming, dan validasi data pemodelan analog tektonik (*Sand-box Analog Tectonic Modeling*) yang menghubungkan penyimpanan fisik lokal, backend manifest sentral, dan platform penampil web/cloud dalam ekosistem **GRAIN 2.0**.

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
    ├── [yymmdd-hhmmss] - [nama exp]/ # 1 Folder = 1 Eksperimen Mandiri
    │   ├── 1.1. RAW - M/
    │   ├── 1.2. Resize - M (CO)/
    │   ├── 4a.1. RAW - Slice M/
    │   ├── 4b.1. RAW - Slice P/
    │   └── OUTPUT/
    └── ...
```

---

## 2. Peran Workspace & Komponen Utama

### A. Workspace Katalogisasi (`c:\TERR\4. WORK\7. CATALOGUING`)
1. `TAXONOMY_RULES.md`: Standar taksonomi baku GRAIN 2.0 (5 Pilar).
2. `grain_catalog_indexer.py`: Script Python berkinerja tinggi untuk memindai `0010`, mengekstrak metadata gambar/video/QPIV/PIV, memvalidasi kepatuhan taksonomi, dan memperbarui `catalog.db` serta `manifest.json` di `0000`.
3. `run_catalog_sync.bat`: Skrip 1-klik untuk menjalankan sinkronisasi katalog secara instan.

### B. Web Data Server & Streaming Proxy (FastAPI & Google Drive Cloud HDD)
- FastAPI Web Server dengan dukungan HTTP 206 Partial Content (Byte-Range requests) untuk pemutaran video ilmiah instan tanpa lag.
- Dual View: Card Grid per Eksperimen dan Split Tree File Explorer.
- Kontrol kecepatan analisis geologi (0.25x s.d. 2.0x) dan Image Lightbox Zoom.

---

## 3. Repositori & Kredensial
- **GitHub Repository**: [https://github.com/terryfurqan/grain-sandbox-catalog](https://github.com/terryfurqan/grain-sandbox-catalog)
- **Branch**: `main`
- **Port Server**: `8080` (Localhost: `http://localhost:8080`, Setup: `http://localhost:8080/setup`)

