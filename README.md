---
title: GRAIN Sandbox Experiment Data Server
emoji: 🏜️
colorFrom: indigo
colorTo: purple
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# 🏔️ GRAIN Sandbox Experiment Data Server

[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg?style=flat&logo=FastAPI&logoColor=white)](https://fastapi.tiangolo.com)
[![Hugging Face Spaces](https://img.shields.io/badge/🤗%20Hugging%20Face-Spaces-yellow.svg)](https://huggingface.co/spaces)
[![Python](https://img.shields.io/badge/Python-3.10%20%7C%203.11%20%7C%203.12-3776AB.svg?style=flat&logo=Python&logoColor=white)](https://www.python.org)
[![Google Drive API](https://img.shields.io/badge/Google%20Drive%20API-v3-4285F4.svg?style=flat&logo=googledrive&logoColor=white)](https://developers.google.com/drive)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

> **Bahasa Indonesia & English Documentation**  
> Server Katalog Data Eksperimen Pemodelan Analog Geologi & Tektonik (Sandbox Modeling) berbasis Web dengan Backend Google Drive sebagai **Cloud HDD** dan **Smart Streaming Proxy**.

---

## 📑 Daftar Isi / Table of Contents
- [🇮🇩 Panduan Bahasa Indonesia](#-panduan-bahasa-indonesia)
  - [1. Arsitektur Sistem](#1-arsitektur-sistem)
  - [2. Panduan Setup Google Drive Service Account](#2-panduan-setup-google-drive-service-account)
  - [3. Cara Menjalankan Server](#3-cara-menjalankan-server)
  - [4. Struktur Folder Eksperimen (GRAIN 2.0 Taxonomy)](#4-struktur-folder-eksperimen-grain-20-taxonomy)
  - [5. FAQ & Troubleshooting](#5-faq--troubleshooting)
- [🇬🇧 English Documentation](#-english-documentation)
  - [1. System Architecture](#1-system-architecture)
  - [2. Google Drive Service Account Setup Guide](#2-google-drive-service-account-setup-guide)
  - [3. How to Run the Server](#3-how-to-run-the-server)
  - [4. Experiment Folder Taxonomy (GRAIN 2.0)](#4-experiment-folder-taxonomy-grain-20)
  - [5. FAQ & Troubleshooting (EN)](#5-faq--troubleshooting-en)

---

# 🇮🇩 Panduan Bahasa Indonesia

## 1. Arsitektur Sistem

Server Data GRAIN dirancang khusus untuk memfasilitasi penjelajahan, pemutaran video ilmiah resolusi tinggi (MP4 timelapse, PIV Velocity Magnitude, Shear Strain), serta inspeksi foto RAW dari eksperimen pemodelan sandbox geologi tanpa perlu mendownload gigabyte/terabyte data ke komputer klien.

```
+-----------------------------------------------------------------------------+
|                            ARSITEKTUR GRAIN SERVER                          |
+-----------------------------------------------------------------------------+

 [ Klien / Browser ] 
        │
        │ HTTP Request (Range: bytes=0-1048575, Search, Filter)
        ▼
 +───────────────────────────────────────────────────────────────────────────+
 | FastAPI Web Application (Port 8000)                                       |
 |                                                                           |
 |  ├── [Web Catalog UI & Player] : TailwindCSS, Alpine.js, Responsive UI    |
 |  ├── [Local SQLite DB]         : Caching Metadata & Fast Hierarchy Index  |
 |  └── [Smart Streaming Proxy]   : Async HTTP Byte-Range Streamer (64KB)    |
 +───────────────────────────────────────────────────────────────────────────+
        │
        │ Google Drive API v3 (Service Account / OAuth Bearer Token)
        │ HTTP 206 Partial Content Stream (On-the-fly, No Local Storage)
        ▼
 [ Google Drive (Cloud HDD) ]
   └── Root Folder (Data Eksperimen Sandbox GRAIN 2.0)
```

### Keunggulan Arsitektur:
1. **Google Drive sebagai Cloud HDD**: Tidak membebani kapasitas penyimpanan lokal server. Seluruh video MP4 dan foto disimpan di cloud.
2. **FastAPI Smart Streaming Proxy**: Mendukung **HTTP Byte-Range Requests (RFC 7233)**. Saat pengguna melakukan *seeking* (memajukan/memundurkan durasi video di timeline browser), server hanya meminta potongan byte (chunk) yang diperlukan ke Google Drive dan mengembalikan header `HTTP 206 Partial Content`.
3. **Local SQLite Indexing**: Metadata struktur folder dan file di-cache ke dalam database lokal SQLite (`catalog.db`). Pencarian (*search*), pemfilteran jenis file, dan pembuatan pohon folder (*explorer*) berlangsung instan tanpa membebani kuota API Google Drive.
4. **Keamanan Tanpa Berbagi Publik**: File Google Drive tidak perlu diset "Public / Siapa saja yang memiliki tautan". Akses file dilakukan secara privat dan aman menggunakan kredensial **Service Account**.

---

## 2. Panduan Setup Google Drive Service Account

Untuk menghubungkan server dengan Google Drive Anda, ikuti langkah-langkah berikut:

### Langkah 1: Buat Project di Google Cloud Console
1. Buka [Google Cloud Console](https://console.cloud.google.com/).
2. Login dengan akun Google Anda.
3. Klik dropdown proyek di bagian atas, lalu klik **"New Project"** (Proyek Baru).
4. Beri nama proyek, contoh: `GRAIN-Sandbox-Server`, lalu klik **"Create"**.

### Langkah 2: Aktifkan Google Drive API
1. Pada menu navigasi sebelah kiri, buka **APIs & Services** > **Library** (Pustaka).
2. Cari `Google Drive API` di kolom pencarian.
3. Klik **Google Drive API** dan tekan tombol **"Enable"** (Aktifkan).

### Langkah 3: Buat Service Account & Unduh Key JSON
1. Buka **APIs & Services** > **Credentials** (Kredensial).
2. Klik tombol **"+ CREATE CREDENTIALS"** di bagian atas, pilih **"Service Account"**.
3. Isi detail Service Account:
   - **Service account name**: `grain-drive-bot`
   - **Service account ID**: (otomatis terisi)
   - Klik **"Create and Continue"**, lalu klik **"Done"**.
4. Di daftar *Service Accounts*, klik akun yang baru dibuat.
5. Masuk ke tab **"KEYS"** (Kunci).
6. Klik **"ADD KEY"** > **"Create new key"**, pilih format **JSON**, lalu klik **"Create"**.
7. File JSON akan otomatis terunduh ke komputer Anda.
8. Ganti nama file tersebut menjadi `credentials.json` dan letakkan di direktori utama server:
   ```
   c:\TERR\4. WORK\6. Server GRAIN\credentials.json
   ```
   *(Atau unggah langsung melalui Setup Wizard di browser pada halaman `http://localhost:8000/setup`)*.

### Langkah 4: Bagikan Folder Google Drive ke Service Account Email
1. Buka file `credentials.json` dengan text editor, lalu salin nilai dari `client_email`, misalnya:  
   `grain-drive-bot@grain-sandbox-server.iam.gserviceaccount.com`
2. Buka [Google Drive](https://drive.google.com) Anda.
3. Klik kanan pada **Folder Utama Eksperimen** (folder induk tempat semua folder eksperimen disimpan), pilih **Bagikan / Share**.
4. Tempelkan email Service Account tadi, set peran sebagai **Viewer / Pelihat**, hapus centang *Notify people*, lalu klik **Kirim / Share**.

### Langkah 5: Salin Root Folder ID
1. Buka folder utama eksperimen tersebut di browser Google Drive.
2. Lihat URL pada address bar browser:  
   `https://drive.google.com/drive/folders/1aBcDeFgHiJkLmNoPqRsTuVwXyZ12345`
3. Salin kode setelah `/folders/` (misalnya: `1aBcDeFgHiJkLmNoPqRsTuVwXyZ12345`).
4. Buka file `.env` di folder server dan isi:
   ```env
   GDRIVE_ROOT_FOLDER_ID=1aBcDeFgHiJkLmNoPqRsTuVwXyZ12345
   ```
   *(Atau simpan melalui Setup Wizard di `http://localhost:8000/setup`)*.

---

## 3. Cara Menjalankan Server

### Metode 1: Windows 1-Click (`run_server.bat`) — Direkomendasikan
Cukup klik ganda (double-click) file **`run_server.bat`**.

Batch script ini akan otomatis:
1. Memeriksa keberadaan Python 3.10+.
2. Memeriksa dan menginstal pustaka yang tertera di `requirements.txt`.
3. Mendeteksi IP jaringan LAN / Wi-Fi lokal.
4. Menampilkan banner status server.
5. Membuka browser secara otomatis ke `http://localhost:8000`.

### Metode 2: Melalui Terminal / Command Prompt
```bash
# 1. Pastikan dependensi terinstall
pip install -r requirements.txt

# 2. Jalankan server Uvicorn
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload
```

Akses portal melalui browser:
- **Lokal**: `http://localhost:8080`
- **Localhost URL**: `http://localhost:8080`
- **Setup & Onboarding Wizard**: `http://localhost:8080/setup`
- **Interactive Swagger API Docs**: `http://localhost:8080/docs`

### Metode 3: Menjalankan dengan Docker
```bash
# 1. Build image Docker
docker build -t grain-server .

# 2. Jalankan container dengan binding file konfigurasi & port 8000
docker run -d \
  --name grain-data-server \
  -p 8000:8000 \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/catalog.db:/app/catalog.db \
  grain-server
```

---

## 4. Struktur Folder Eksperimen (GRAIN 2.0 Taxonomy)

Server ini secara otomatis memetakan dan mengindeks struktur folder standar eksperimen analog geologi **GRAIN 2.0**:

```
📁 Root Folder GDrive (GDRIVE_ROOT_FOLDER_ID)
│
├── 📁 2026-03_EXP01_Extension_Basin_Graben/          <-- Level 1: Experiment Folder
│   ├── 📁 1.1. RAW - M/                             <-- Foto Master Camera
│   │   ├── DSC_0001.JPG
│   │   └── DSC_0002.JPG
│   ├── 📁 1.2. Resize - M - 3840x2160 px/           <-- Foto Resize / Crop
│   ├── 📁 2.1. RAW - P1/                            <-- Foto Profile Camera 1
│   ├── 📁 3.1. RAW - P2/                            <-- Foto Profile Camera 2
│   ├── 📁 4a.1. RAW - Slice M/                      <-- Irisan Serial (Master)
│   ├── 📁 4b.1. RAW - Slice P/                      <-- Irisan Serial (Profile)
│   ├── 📁 5.1. RAW - 3D/                            <-- Data 3D / Fotogrametri
│   └── 📁 OUTPUT/
│       ├── 📁 VIDEOS/                               <-- Video Ilmiah Eksperimen
│       │   ├── EXP01_timelapse_co_720p.mp4
│       │   ├── EXP01_velmag_jet_vectors.mp4
│       │   ├── EXP01_vmsst_split_screen.mp4
│       │   └── EXP01_shearstrain_norm.mp4
│       ├── 📁 QPIV/                                 <-- Data Vektor PIV (.npz, .csv)
│       ├── 📁 SLICES/                               <-- Komposit Penampang Slices
│       ├── 📁 REPORTS/                              <-- Slide Presentasi (.pptx, .pdf)
│       └── 📁 SCRIPTS/                              <-- Skrip Pengolahan
│
└── 📁 2026-04_EXP02_Inversion_Tectonic_Wedge/
    ├── ...
```

---

## 5. FAQ & Troubleshooting

### Q1: Video tidak bisa diputar atau error saat *seeking* (melompat durasi)?
* **Penyebab**: Browser meminta potongan byte tertentu (Range request). Jika metadata video (`moov atom`) berada di akhir file MP4, browser harus mengunduh seluruh file sebelum bisa diputar.
* **Solusi**: Pastikan video MP4 yang diunggah ke Google Drive sudah diekspor dengan opsi **Fast Start / Web Optimized** (`-movflags +faststart` pada FFmpeg). Server FastAPI sudah mendukung penuh respon `HTTP 206 Partial Content` untuk seeking mulus.

### Q2: Muncul error "Google Drive API error: 403 / 404" atau "File not found"?
* **Penyebab**: Service Account email belum diberi izin akses ke folder Google Drive atau Root Folder ID salah.
* **Solusi**: Pastikan Anda telah membagikan (*Share*) folder root Google Drive ke alamat email yang ada di dalam `credentials.json` (format: `...iam.gserviceaccount.com`) dengan status **Viewer**.

### Q3: Berapa batas kuota API Google Drive? Apakah aman untuk akses banyak pengguna?
* **Jawaban**: Google Cloud memberikan kuota gratis **20.000 request per 100 detik** untuk Google Drive API. Karena server GRAIN meng-cache seluruh struktur data ke dalam **SQLite lokal**, request ke API Google Drive hanya terjadi saat pemutaran stream/download video, sehingga sangat hemat kuota dan tidak mudah terkena *rate limit*.

### Q4: Bagaimana cara memperbarui data jika ada eksperimen atau video baru di Google Drive?
* **Jawaban**: Klik tombol **"Sync GDrive"** di pojok kanan atas portal web, masukkan PIN Admin (default: `123456`), lalu klik **"Mulai Sinkronisasi"**. Server akan memindai folder Google Drive di latar belakang dan memperbarui katalog SQLite.

---
---

# 🇬🇧 English Documentation

## 1. System Architecture

The GRAIN Data Server is built to streamline browsing, high-resolution scientific video playback (timelapse MP4, PIV Velocity Magnitude, Shear Strain fields), and RAW photo inspection from geological sandbox modeling experiments without requiring users to download massive datasets to their local workstations.

### Architectural Highlights:
1. **Google Drive as Cloud Storage Backend**: Acts as an unlimited cloud hard drive. No massive local disk storage required on the web server.
2. **FastAPI Smart Streaming Proxy**: Full support for **HTTP Byte-Range Requests (RFC 7233)**. When a user seeks through a video timeline, the proxy requests only the required byte chunks (64KB chunks) from the Google Drive API and streams them back with `HTTP 206 Partial Content`.
3. **Local SQLite Metadata Cache**: Folder hierarchies and file records are indexed locally in `catalog.db`. Searching, filtering by file type, and folder navigation are instant with zero Google Drive API overhead.
4. **Secure Service Account Access**: Files do not need to be shared publicly. All operations use a scoped Google Cloud Service Account.

---

## 2. Google Drive Service Account Setup Guide

### Step 1: Create a Google Cloud Project
1. Navigate to the [Google Cloud Console](https://console.cloud.google.com/).
2. Sign in with your Google account.
3. Click the project dropdown at the top and select **"New Project"**.
4. Name the project (e.g., `GRAIN-Sandbox-Server`) and click **"Create"**.

### Step 2: Enable Google Drive API
1. In the sidebar navigation, go to **APIs & Services** > **Library**.
2. Search for `Google Drive API`.
3. Click on **Google Drive API** and select **"Enable"**.

### Step 3: Create Service Account & Generate JSON Key
1. Go to **APIs & Services** > **Credentials**.
2. Click **"+ CREATE CREDENTIALS"** and choose **"Service Account"**.
3. Fill in the Service Account name (e.g., `grain-drive-bot`) and click **"Create and Continue"**, then **"Done"**.
4. Select the newly created Service Account from the list.
5. Go to the **"KEYS"** tab.
6. Click **"ADD KEY"** > **"Create new key"**, select **JSON**, and click **"Create"**.
7. The JSON key file will be downloaded to your computer.
8. Rename the file to `credentials.json` and place it in the root folder of this project:
   ```
   c:\TERR\4. WORK\6. Server GRAIN\credentials.json
   ```
   *(Or upload it directly via the Web Setup Wizard at `http://localhost:8000/setup`)*.

### Step 4: Share Google Drive Folder with the Service Account
1. Open `credentials.json` in a text editor and copy the `client_email` value (e.g., `grain-drive-bot@grain-sandbox-server.iam.gserviceaccount.com`).
2. Open [Google Drive](https://drive.google.com).
3. Right-click your **Root Experiment Folder** and select **Share**.
4. Paste the Service Account email address, assign the **Viewer** role, uncheck *Notify people*, and click **Share**.

### Step 5: Configure Root Folder ID
1. Open the shared experiment folder in Google Drive.
2. Copy the Folder ID from the address bar:  
   `https://drive.google.com/drive/folders/<GDRIVE_ROOT_FOLDER_ID>`
3. Set the ID in `.env` or in the Setup Wizard:
   ```env
   GDRIVE_ROOT_FOLDER_ID=your_extracted_folder_id_here
   ```

---

## 3. How to Run the Server

### Option A: Windows 1-Click (`run_server.bat`) — Recommended
Simply double-click `run_server.bat`. It will automatically:
- Verify Python 3.10+ installation.
- Check and install required packages from `requirements.txt`.
- Detect local LAN / Wi-Fi IP address.
- Launch the Uvicorn server with auto-reload.
- Automatically launch your default browser to `http://localhost:8000`.

### Option B: Terminal / Command Line
```bash
pip install -r requirements.txt
python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Option C: Docker Deployment
```bash
docker build -t grain-server .
docker run -d \
  --name grain-data-server \
  -p 8000:8000 \
  -v $(pwd)/credentials.json:/app/credentials.json \
  -v $(pwd)/.env:/app/.env \
  -v $(pwd)/catalog.db:/app/catalog.db \
  grain-server
```

---

## 4. Experiment Folder Taxonomy (GRAIN 2.0)

The server organizes experiments in conformance with the standard GRAIN 2.0 directory taxonomy:

* `1.1. RAW - M/`: Original Master camera timelapse frames.
* `1.2. Resize - M - <WxH> px/`: Color-corrected and cropped timelapse frames.
* `2.1. RAW - P1/` & `3.1. RAW - P2/`: Side profile camera series.
* `4a.1. RAW - Slice M/` & `4b.1. RAW - Slice P/`: Serial cross-section slices.
* `5.1. RAW - 3D/`: 3D photogrammetry surface scans.
* `OUTPUT/VIDEOS/`: Final scientific timelapses (Velocity Magnitude, Shear Strain, Side-by-side split screens).
* `OUTPUT/QPIV/`: Processed PIV displacement and strain archives (`.npz`, `.csv`).
* `OUTPUT/REPORTS/`: Auto-generated presentation slides (`.pptx`).

---

## 5. FAQ & Troubleshooting (EN)

### Q: Why do I get a 403 Forbidden error from Google Drive?
**A**: Ensure you have explicitly shared the root Google Drive folder with the Service Account email address (`...iam.gserviceaccount.com`) as a **Viewer**.

### Q: Video playback is choppy or seeking doesn't work.
**A**: Ensure your MP4 files were encoded with the `faststart` flag (`-movflags +faststart` in FFmpeg), which places the `moov` atom header at the beginning of the file.

### Q: How do I change the Admin PIN or listening port?
**A**: Edit the `.env` file or use the web interface at `http://localhost:8000/setup`.

---

## 📄 License
Released under the MIT License for academic and research workflows within the GRAIN 2.0 ecosystem.
