# HANDOFF: GRAIN Sandbox Data Catalog Web Server

Dokumen ini adalah ringkasan handoff untuk melanjutkan pengembangan atau pemeliharaan sistem di sesi berikutnya.

---

## 📌 Ringkasan Status Proyek
- **Status Pengembangan**: Selesai (Feature-Complete, Authenticated & Tested).
- **Status Repositori**: Git terinisialisasi dan ter-push ke GitHub: [terryfurqan/grain-sandbox-catalog](https://github.com/terryfurqan/grain-sandbox-catalog).
- **Status Cloud Deployment**: **LIVE DI GOOGLE CLOUD RUN** 🚀
  - **Live URL**: `https://grain-sandbox-catalog-46858144362.asia-southeast1.run.app`
  - **GCP Project**: `grain-sandbox-server` (Region: `asia-southeast1`)
  - **CI/CD Pipeline**: GitHub `main` -> Cloud Build -> Cloud Run Service.
- **Status Pengujian**: 50/50 unit, crypto, session guard, dan integration test lulus 100% (`py -3.12 -m pytest -v`).

---

## ☁️ Arsitektur & Aturan Main Google Cloud Run (PENTING UNTUK SESI BARU)

Setiap agen yang melanjutkan pekerjaan di sesi baru **WAJIB** memperhatikan aturan berikut:
1. **Continuous Deployment Otomatis**:
   - Setiap kali melakukan `git push origin main`, Google Cloud Build akan otomatis mengompilasi `Dockerfile` dan memperbarui container di Cloud Run.
   - **Aturan**: Selalu jalankan pengujian lokal (`pytest -v`) sebelum melakukan commit/push ke branch `main`.
2. **Karakteristik Stateless & Port Container**:
   - Cloud Run berjalan dalam mode stateless container dengan port dinamis yang di-inject melalui environment variable `$PORT` (default fallback 7860/8080).
   - Database SQLite `catalog.db` di-cache di dalam container. Sinkronisasi metadata awal atau update dilakukan melalui endpoint `/setup` atau tombol Sync di navbar.
3. **Environment Variables Aktif di Cloud Run**:
   - `GDRIVE_ROOT_FOLDER_ID`: `1u0Uv-L4w4nCUNGSm3tXNeK5L61jRijuC`
   - `ADMIN_PIN`: `123456`
   - `PORTAL_TITLE`: `GRAIN Sandbox Experiment Data Server`
   - `PORTAL_SUBTITLE`: `Analog Geological & Tectonic Modeling Video/Photo Catalog`
   - `GDRIVE_SERVICE_ACCOUNT_RAW_JSON`: (String JSON Kredensial Service Account)
4. **Prinsip FinOps & Zero-Cost**:
   - Server dikonfigurasi dengan *Scale-to-Zero* (0 instance saat idle) agar tetap berada di dalam kuota **Always Free Tier** Google Cloud.
   - Hindari memory leak, gunakan chunked streaming (64KB) untuk video partial content (HTTP 206), dan pastikan rate limiter tetap aktif.

---

## 📁 Peta Berkas Proyek

| Berkas / Direktori | Deskripsi & Tanggung Jawab |
| :--- | :--- |
| `app/main.py` | Entrypoint aplikasi FastAPI, lifecycle database, mounting routes (`auth`, `catalog`, `stream`, `sync`, `admin`), static assets, & session guard. |
| `app/config.py` | Pengaturan Pydantic Settings (`ADMIN_USERNAME`, `ADMIN_PASSWORD`, `SESSION_SECRET_KEY`, `REQUIRE_AUTH`, dll.). |
| `app/auth.py` | **Security Core**: HMAC-SHA256 session token generator/verifier, `secrets.compare_digest` timing-attack defense, HttpOnly cookie helpers, & `require_admin_login` dependency. |
| `app/routers/auth.py` | Endpoint autentikasi web & API (`GET /login`, `POST /login`, `GET /logout`, `GET /api/auth/me`). |
| `app/database.py` | Inisialisasi SQLite (`catalog.db`), skema tabel, dan fungsi kategorisasi file. |
| `app/gdrive.py` | Google Drive API v3 client, OAuth2 Service Account auth, crawler, & chunked stream. |
| `app/routers/catalog.py` | Endpoint REST API katalog (`/api/experiments`, `/api/folders/...`, `/api/search`). |
| `app/routers/stream.py` | **Smart Streaming Proxy**: Meneruskan HTTP Byte-Range (206 Partial Content) untuk video MP4. |
| `app/routers/sync.py` | Modul sinkronisasi latar belakang Google Drive yang diproteksi session admin & PIN. |
| `app/routers/admin.py` | Endpoint manajemen konfigurasi dan pengujian koneksi Google Drive. |
| `app/templates/login.html` | UI Portal Login Admin bernuansa Dark Slate / Indigo / Teal dengan Alpine.js (toggle password, dynamic error alerts, loading state). |
| `app/templates/index.html` | UI Dashboard utama dengan Tailwind CSS & Alpine.js (Card Grid & Folder Explorer) + User Badge di Navbar. |
| `app/templates/setup.html` | Setup & Onboarding Wizard interaktif untuk upload `credentials.json` dan input Folder ID (terproteksi login). |
| `app/templates/components/navbar.html` | Top Navbar dengan indikator status login user (`terryfurqan` / Admin) dan tombol Logout. |
| `app/static/js/app.js` | Logika reaktif Alpine.js, pencarian instan, filter kategori, dan player video. |
| `run_server.bat` | Skrip Windows 1-klik untuk menjalankan server di `http://localhost:8080`. |
| `generate_cloud_env.py` | Skrip ekstraktor otomatis isi `credentials.json` ke clipboard komputer. |
| `Dockerfile` & `render.yaml` | Konfigurasi kontainerisasi dan blueprint cloud deploy. |
| `tests/test_auth.py` | 23 Automated Security & Authentication Tests (Token signing, expiration, tampering, login/logout, route protection). |
| `tests/test_server.py` | 24 Automated Server & Integration Tests. |
| `tests/test_finops.py` | 3 Automated FinOps & Rate Limiting Tests. |
| `CONTEXT.md` & `README.md` | Dokumentasi arsitektur dan panduan pengguna. |

---

## 🔑 Kredensial & Autentikasi

### 1. Kredensial Administrator Web:
- **Username**: `terryfurqan`
- **Password**: `ifasayang123`
- **Session Cookie**: `grain_session` (Flags: `HttpOnly=True`, `SameSite=Lax`, `Max-Age=604800` / 7 hari).

### 2. Google Cloud Service Account:
- **Service Account Email**: `grain-catalog-reader@grain-sandbox-server.iam.gserviceaccount.com`
- **File Kredensial Lokal**: `credentials.json` (dilindungi oleh `.gitignore`).
- **PIN Admin Fallback**: `123456`.

---

## 🚀 Petunjuk Cepat Melanjutkan Pekerjaan

### 1. Menjalankan di Komputer Lokal:
```cmd
cd "c:\TERR\4. WORK\6. Server GRAIN"
run_server.bat
```
Akses web: `http://localhost:8080` (Login: `http://localhost:8080/login`, Setup: `http://localhost:8080/setup`).

### 2. Melakukan Sinkronisasi:
1. Login sebagai admin di `http://localhost:8080/login`.
2. Klik tombol **"Sync GDrive"** di navbar pojok kanan atas.
3. Semua video dan foto akan langsung terindeks dan dapat diputar seketika.

### 3. Menjalankan Uji Otomatis:
```cmd
py -3.12 -m pytest -v
```
Semua 50 test case akan berjalan dan terverifikasi 100% lulus.

