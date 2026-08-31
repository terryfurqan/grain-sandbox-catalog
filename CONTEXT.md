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
- Sistem Autentikasi Admin terenkripsi (HMAC-SHA256 session cookie + `secrets.compare_digest`).

---

## 3. Repositori & Kredensial
- **GitHub Repository**: [https://github.com/terryfurqan/grain-sandbox-catalog](https://github.com/terryfurqan/grain-sandbox-catalog)
- **Branch**: `main`
- **Service Account Email**: `grain-catalog-reader@grain-sandbox-server.iam.gserviceaccount.com`
- **Admin Username / Password**: `terryfurqan` / `ifasayang123`
- **Admin PIN**: `123456`
- **Port Server**: `8080` (Localhost: `http://localhost:8080`, Login: `http://localhost:8080/login`, Setup: `http://localhost:8080/setup`)

---

## 4. Cara Menjalankan

### A. Di Komputer Lokal (Windows)
Cukup jalankan berkas batch:
```cmd
run_server.bat
```

### B. Di Production Cloud (Google Cloud Run - ACTIVE / LIVE 🚀)
- **Live URL**: `https://grain-sandbox-catalog-46858144362.asia-southeast1.run.app`
- **GCP Project**: `grain-sandbox-server` (Region: `asia-southeast1` - Singapore)
- **CI/CD Pipeline**: GitHub Continuous Deployment (`terryfurqan/grain-sandbox-catalog` branch `main`) -> Google Cloud Build -> Cloud Run.
- **Environment Variables Aktif di Cloud Run**:
  - `GDRIVE_ROOT_FOLDER_ID`: `1u0Uv-L4w4nCUNGSm3tXNeK5L61jRijuC`
  - `ADMIN_PIN`: `123456`
  - `PORTAL_TITLE`: `GRAIN Sandbox Experiment Data Server`
  - `PORTAL_SUBTITLE`: `Analog Geological & Tectonic Modeling Video/Photo Catalog`
  - `GDRIVE_SERVICE_ACCOUNT_RAW_JSON`: (JSON String Service Account)
- **Catatan Penting Pengembangan**:
  Setiap `git push` ke branch `main` akan memicu Google Cloud Build untuk otomatis meng-compile `Dockerfile` dan me-redeploy container ke Cloud Run. Selalu jalankan `pytest` sebelum melakukan push.

### C. Di Cloud Alternatif (Hugging Face Spaces)
1. Buat Space baru di [huggingface.co/new-space](https://huggingface.co/new-space) (Pilih SDK **Docker**).
2. Hubungkan repository GitHub: `https://github.com/terryfurqan/grain-sandbox-catalog`.
3. Tambahkan Secrets & Variables sesuai panduan `DEPLOY_TO_HUGGINGFACE.md`.

---

## 5. Ringkasan Pengujian (QA)
- Test suite: `pytest` (`py -3.12 -m pytest -v`)
- Status: **50/50 Test Passed (100% Green)**
- Mencakup: Session Security & Timing-Attack Defense, FinOps Rate Limiting, HTTP 206 Partial Range Streaming, SQLite Database Indices, API Catalog, Search & Filtering, Onboarding Wizard Redirection.
