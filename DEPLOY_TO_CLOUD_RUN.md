# ☁️ Panduan Deployment ke Google Cloud Run (GCP)
## Web Server GRAIN Sandbox Data Catalog (FastAPI + Docker)

Panduan ini memandu Anda langkah demi langkah untuk mempublikasikan Web Server **GRAIN Sandbox Experiment Data Catalog** ke **Google Cloud Run** dengan konfigurasi **FinOps Hard-Capped** (menjamin tagihan tetap Rp 0 / Free Tier dan bebas risiko lonjakan biaya).

---

## 🌟 Mengapa Google Cloud Run?

| Fitur / Parameter | Google Cloud Run (Free Tier) | Hugging Face Spaces |
|---|---|---|
| **Ekosistem & Latensi** | **1 Ekosistem dengan Google Drive** (Google Backbone Network, streaming ultra-cepat) | Terpisah (akses via internet publik) |
| **Batas Gratis (Free Tier)** | **2 Juta Request/Bulan GRATIS** + 360.000 GiB-detik RAM gratis | Gratis 24/7 (2 vCPU, 16 GB RAM) |
| **Scale-to-Zero** | ✅ Ya (Otomatis tidur saat tidak ada request, hemat biaya) | ❌ Selalu menyala (atau sleep mode) |
| **Proteksi FinOps** | ✅ Hard limits (`max-instances=1`, in-memory rate limiting, auto cleanup) | Kuota CPU/RAM bawaan |
| **HTTPS & Custom Domain** | ✅ Otomatis dapat URL HTTPS (`*.a.run.app`) + custom domain | ✅ Otomatis dapat URL HTTPS (`*.hf.space`) |

---

## 🛡️ Prinsip Zero-Cost & FinOps Guardrails

Proyek ini telah dikonfigurasi dengan perlindungan biaya berlapis:
1. **In-Memory Rate Limiting (SlowAPI)**: Mencegah bot/crawler luar menguras bandwidth streaming.
2. **HTTP 206 Caching (7 Hari)**: Browser pengguna menyimpan cache video/foto secara lokal sehingga seek/replay tidak menyedot egress cloud.
3. **Hard Cap `max-instances=1`**: Cloud Run tidak akan pernah auto-scale tak terbatas saat diserang traffic tinggi.
4. **Artifact Registry Auto Cleanup**: Hanya menyimpan 2 versi Docker image terakhir (`cleanup-policy.json`).
5. **Automated Kill-Switch**: Skrip pemutus otomatis jika budget mencapai $5 (Lihat [finops/FINOPS_GUARDRAILS_GUIDE.md](finops/FINOPS_GUARDRAILS_GUIDE.md)).

---

## ⚡ Pilihan 1: Deploy Otomatis 1-Klik (Disarankan)

### Untuk Pengguna Windows:
Cukup klik ganda file:
```cmd
deploy_cloud_run.bat
```
Masukkan Google Cloud Project ID Anda saat diminta. Script akan otomatis:
- Mengaktifkan API Cloud Run & Artifact Registry.
- Membuat repo Docker dan memasang *Cleanup Policy*.
- Melakukan build dan deploy dengan parameter hemat daya.

### Untuk Pengguna Linux / MacOS / Google Cloud Shell:
```bash
chmod +x deploy_cloud_run.sh
./deploy_cloud_run.sh
```

---

## 🚀 Pilihan 2: Deploy Lewat Web Console Google Cloud

Jika ingin melakukan setup manual melalui browser di Google Cloud Console:

### 1️⃣ Langkah 1: Buka Cloud Run di Google Cloud Console
1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Buka menu **Cloud Run** atau buka: **[console.cloud.google.com/run](https://console.cloud.google.com/run)**.
3. Klik tombol **+ CREATE SERVICE** (Buat Layanan).

---

### 2️⃣ Langkah 2: Hubungkan Repositori GitHub
1. Pada pilihan *Deployment platform*, pilih **Continuously deploy from a repository**.
2. Klik tombol **SET UP WITH CLOUD BUILD**.
3. Pilih penyedia Git: **GitHub**, pilih repositori `grain-sandbox-catalog`, branch `^main$`, dan Build Type `Dockerfile`.

---

### 3️⃣ Langkah 3: Konfigurasi Service Cloud Run (Wajib FinOps)
1. **Service name**: `grain-server`
2. **Region**: `asia-southeast2` (Jakarta) atau `asia-southeast1` (Singapura).
3. **Authentication**: **Allow unauthenticated invocations**.
4. **Autoscaling (PENTING)**:
   - **Minimum number of instances**: `0` (Tidur saat idle).
   - **Maximum number of instances**: `1` (Anti pembengkakan biaya).
5. **Ingress control**: All (Traffic publik diizinkan).
6. **CPU allocation**: **CPU is only allocated during request processing** (CPU throttling aktif).
7. **Concurrency**: `80` requests per instance.
8. **Container memory**: `512 MiB`, CPU: `1`.

---

### 4️⃣ Langkah 4: Tambahkan Environment Variables
Di tab **Container > Variables & Secrets**, tambahkan variabel berikut:

| Name | Value | Keterangan |
|---|---|---|
| `GDRIVE_ROOT_FOLDER_ID` | *(Folder ID Google Drive Anda)* | ID folder data sandbox dari URL Google Drive |
| `ADMIN_PIN` | `123456` | PIN admin untuk akses `/setup` & sync |
| `PORTAL_TITLE` | `GRAIN Sandbox Experiment Data Server` | Judul portal |
| `PORTAL_SUBTITLE` | `Analog Geological & Tectonic Modeling Video/Photo Catalog` | Subjudul portal |
| `GDRIVE_SERVICE_ACCOUNT_RAW_JSON` | *(String JSON dari credentials.json)* | Salin dari output `python generate_cloud_env.py` |
| `APP_ACCESS_TOKEN` | *(Opsional)* | Token shared internal jika ingin mengunci akses publik |

4. Klik **CREATE**.
5. Tunggu 1–2 menit hingga URL HTTPS aktif (misal: `https://grain-server-xxxxxxxx-as.a.run.app`).

---

## 🔒 Konfigurasi Izin Google Drive

Pastikan Service Account Anda telah diberi izin akses ke Folder Google Drive:
1. Buka [Google Drive](https://drive.google.com/).
2. Klik kanan folder data eksperimen sandbox -> **Share** (Bagikan).
3. Masukkan email Service Account:
   `grain-catalog-reader@grain-sandbox-server.iam.gserviceaccount.com` (atau email service account GCP Anda).
4. Berikan role **Viewer** (atau **Editor** jika ingin izin penuh).
5. Klik **Send** / **Save**.

---

## 🎯 Mengakses Web Server yang Telah Berjalan

Setelah deployment selesai:
1. Buka URL HTTPS yang diberikan oleh Cloud Run di browser.
2. Akses halaman wizard setup untuk validasi pertama kali di:
   `https://<url-cloud-run-anda>/setup`
3. Masukkan Admin PIN (`123456`) untuk memeriksa status koneksi Google Drive dan melakukan sinkronisasi awal metadata katalog (`catalog.db`).