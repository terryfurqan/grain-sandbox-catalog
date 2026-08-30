# HANDOFF: GRAIN Sandbox Data Catalog Web Server

Dokumen ini adalah ringkasan handoff untuk melanjutkan pengembangan atau pemeliharaan sistem di sesi berikutnya.

---

## 📌 Ringkasan Status Proyek
- **Status Pengembangan**: Selesai (Feature-Complete & Tested).
- **Status Repositori**: Git terinisialisasi dan ter-push ke GitHub: [terryfurqan/grain-sandbox-catalog](https://github.com/terryfurqan/grain-sandbox-catalog).
- **Status Pengujian**: 24/24 unit & integration test lulus 100% (`pytest tests/`).

---

## 📁 Peta Berkas Proyek

| Berkas / Direktori | Deskripsi & Tanggung Jawab |
| :--- | :--- |
| `app/main.py` | Entrypoint aplikasi FastAPI, lifecycle database, mounting routes & static assets. |
| `app/config.py` | Pengaturan Pydantic, pembacaan `.env` dan raw JSON credentials. |
| `app/database.py` | Inisialisasi SQLite (`catalog.db`), skema tabel, dan fungsi kategorisasi file. |
| `app/gdrive.py` | Google Drive API v3 client, OAuth2 Service Account auth, crawler, & chunked stream. |
| `app/routers/catalog.py` | Endpoint REST API katalog (`/api/experiments`, `/api/folders/...`, `/api/search`). |
| `app/routers/stream.py` | **Smart Streaming Proxy**: Meneruskan HTTP Byte-Range (206 Partial Content) untuk video MP4. |
| `app/routers/sync.py` | Modul sinkronisasi latar belakang Google Drive yang diproteksi PIN Admin. |
| `app/routers/admin.py` | Endpoint manajemen konfigurasi dan pengujian koneksi Google Drive. |
| `app/templates/index.html` | UI Dashboard utama dengan Tailwind CSS & Alpine.js (Card Grid & Folder Explorer). |
| `app/templates/setup.html` | Setup & Onboarding Wizard interaktif untuk upload `credentials.json` dan input Folder ID. |
| `app/static/js/app.js` | Logika reaktif Alpine.js, pencarian instan, filter kategori, dan player video. |
| `run_server.bat` | Skrip Windows 1-klik untuk menjalankan server di `http://localhost:8080`. |
| `generate_cloud_env.py` | Skrip ekstraktor otomatis isi `credentials.json` ke clipboard komputer. |
| `Dockerfile` & `render.yaml` | Konfigurasi kontainerisasi dan blueprint cloud deploy. |
| `tests/test_server.py` | 24 Automated Unit & Integration Tests. |
| `CONTEXT.md` & `README.md` | Dokumentasi arsitektur dan panduan pengguna. |

---

## 🔑 Kredensial & Autentikasi
- **Service Account Email**: `grain-catalog-reader@grain-sandbox-server.iam.gserviceaccount.com`
- **File Kredensial Lokal**: `credentials.json` (dilindungi oleh `.gitignore`).
- **PIN Admin Default**: `123456`.

---

## 🚀 Petunjuk Cepat Melanjutkan Pekerjaan

### 1. Menjalankan di Komputer Lokal:
```cmd
cd "c:\TERR\4. WORK\6. Server GRAIN"
run_server.bat
```
Akses web: `http://localhost:8080` (Setup: `http://localhost:8080/setup`).

### 2. Melakukan Sinkronisasi Pertama:
1. Pastikan folder induk eksperimen di Google Drive sudah di-share ke email Service Account di atas sebagai **Viewer**.
2. Di web server, klik tombol **"Sync GDrive"** di pojok kanan atas &rarr; masukkan PIN `123456`.
3. Semua video dan foto akan langsung terindeks dan bisa diputar seketika.

### 3. Menjalankan Uji Otomatis:
```cmd
python -m pytest tests/ -v
```
