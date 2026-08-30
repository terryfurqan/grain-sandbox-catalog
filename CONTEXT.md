# CONTEXT: GRAIN Sandbox Experiment Data Server

## 1. Domain & Background Context
Proyek ini adalah bagian dari ekosistem **GRAIN 2.0** (*Geological Analog Sandbox Modeling Research Suite*). Dalam pemodelan analog tektonik dan geologi, eksperimen menghasilkan ribuan frame time-lapse resolusi tinggi (RAW/JPG) dan rekaman video evolusi deformasi (MP4) berukuran puluhan hingga ratusan Gigabyte.

Untuk memfasilitasi akses katalog, preview video, dan eksplorasi data eksperimen oleh tim peneliti atau mahasiswa tanpa harus mendownload dataset raksasa ke harddisk lokal setiap saat, dibangun sistem **Web Server Katalog Berbasis Google Drive HDD**.

---

## 2. Arsitektur Teknis Sistem

```text
[ Browser Klien ]
       │
       ▼ (HTTP 1.1 / 2.0)
[ FastAPI Web Server (Port 8080) ]
  ├── SQLite Local Cache (catalog.db) ──> Metadata instan (0 ms latency)
  └── Smart Streaming Proxy (Byte-Range) ──> Google Drive API v3 (alt=media)
                                                    │
                                                    ▼ (OAuth2 JWT Service Account)
                                         [ Google Drive Cloud HDD ]
                                         (Penyimpanan Utama Dataset)
```

### Komponen Utama:
1. **Google Drive Cloud Storage**: Bertindak sebagai harddisk cloud. File video & foto tidak disimpan di disk server lokal.
2. **FastAPI Smart Streaming Proxy**:
   - Menerima request HTTP `Range: bytes=start-end` dari pemutar video browser.
   - Mengambil potongan byte langsung dari Google Drive API secara *on-the-fly* dan mengembalikan status code `206 Partial Content`.
   - Memungkinkan *seeking/scrubbing* maju-mundur video MP4 secara instan tanpa delay download keseluruhan file.
3. **SQLite Caching Engine (`catalog.db`)**:
   - Folder tingkat 1 di Google Drive diidentifikasi sebagai satu unit **Eksperimen**.
   - Subfolder dan file diindeks dalam database lokal untuk pencarian instan, filter tipe file, dan breadcrumbs folder explorer.
4. **Modern Responsive Frontend**:
   - Tailwind CSS + Alpine.js.
   - Dual View: **Card Grid per Eksperimen** dan **File Explorer / Split Tree View**.
   - Player video dengan kontrol kecepatan analisis geologi (**0.25x s.d. 2.0x**) dan Image Lightbox Zoom.

---

## 3. Repositori & Kredensial
- **GitHub Repository**: [https://github.com/terryfurqan/grain-sandbox-catalog](https://github.com/terryfurqan/grain-sandbox-catalog)
- **Branch**: `main`
- **Service Account Email**: `grain-catalog-reader@grain-sandbox-server.iam.gserviceaccount.com`
- **Admin PIN**: `123456` (dikonfigurasi via `.env` atau cloud environment variable)
- **Port Server**: `8080` (Localhost: `http://localhost:8080`, Setup: `http://localhost:8080/setup`)

---

## 4. Cara Menjalankan

### A. Di Komputer Lokal (Windows)
Cukup jalankan berkas batch:
```cmd
run_server.bat
```

### B. Di Cloud Gratis (Hugging Face Spaces)
1. Buat Space baru di [huggingface.co/new-space](https://huggingface.co/new-space) (Pilih SDK **Docker**).
2. Hubungkan repository GitHub: `https://github.com/terryfurqan/grain-sandbox-catalog`.
3. Tambahkan Secrets di tab Settings:
   - `GDRIVE_ROOT_FOLDER_ID`: (ID folder Google Drive data sandbox)
   - `ADMIN_PIN`: `123456`
   - `GDRIVE_SERVICE_ACCOUNT_RAW_JSON`: (Isi string `credentials.json`)

---

## 5. Ringkasan Pengujian (QA)
- Test suite: `tests/test_server.py`
- Framework: `pytest`
- Status: **24/24 Test Passed (100% Green)**
- Mencakup: HTTP 206 Partial Range Streaming, SQLite Database Indices, API Catalog, Search & Filtering, Onboarding Wizard Redirection.
