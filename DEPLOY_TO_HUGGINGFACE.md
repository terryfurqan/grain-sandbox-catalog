# 🤗 Panduan Deployment ke Hugging Face Spaces
## Web Server GRAIN Sandbox Data Catalog (FastAPI + Docker)

Panduan ini memandu Anda langkah demi langkah untuk mempublikasikan Web Server **GRAIN Sandbox Experiment Data Catalog** secara gratis di **Hugging Face Spaces** menggunakan Docker SDK.

---

## 🌟 Mengapa Hugging Face Spaces?

| Keunggulan | Hugging Face Spaces (Free Tier) | Render.com (Free Tier) |
|---|---|---|
| **RAM (Memori)** | **16 GB RAM** | 512 MB RAM |
| **CPU** | **2 vCPU** | 0.1 CPU Shared |
| **Penyimpanan Cache**| 50 GB Ephemeral Disk | 1 GB Disk |
| **Performa Streaming Video** | **Sangat Cepat & Responsif** | Terbatas pada koneksi paralel |
| **Persyaratan Kartu Kredit** | **Tidak Perlu (100% Gratis)** | Tidak Perlu |

---

## 📋 Ringkasan Alur Deployment

```mermaid
flowchart TD
    A[Lokal: credentials.json] -->|python generate_cloud_env.py| B[Raw JSON String]
    B -->|Secret| C[Hugging Face Space Settings]
    D[Google Drive Folder ID] -->|Variable| C
    E[Kode Lokal / GitHub] -->|push_to_hf.bat / Git Push| F[Hugging Face Docker Space]
    F -->|Auto-Build Container| G[Live: https://hf.space/...]
```

---

## 🚀 Langkah Demi Langkah Deployment

### 1️⃣ Langkah 1: Buat Space Baru di Hugging Face

1. Buka browser dan login ke akun [Hugging Face](https://huggingface.co/).
2. Kunjungi halaman pembuatan Space: **[huggingface.co/new-space](https://huggingface.co/new-space)**.
3. Masukkan konfigurasi Space:
   - **Space name**: `grain-sandbox-catalog` (atau sesuai keinginan Anda).
   - **License**: `mit` (atau `apache-2.0`).
   - **Select the Space SDK**: Pilih **Docker** > pilih **Blank**.
   - **Space hardware**: Pilih **CPU basic • 2 vCPU • 16 GB • Free**.
   - **Visibility**: 
     - **Public**: Siapa saja dapat membuka katalog & streaming video eksperimen.
     - **Private**: Hanya akun Anda / organisasi yang dapat mengakses.
4. Klik **Create Space**.

---

### 2️⃣ Langkah 2: Buat Hugging Face User Access Token (Write)

Token ini digunakan sebagai password saat melakukan `git push` ke Hugging Face Space:

1. Buka **[huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)**.
2. Klik tombol **Create new token** (atau **New token**).
3. Beri nama token, misalnya: `grain-deploy-token`.
4. Pilih **Token type**: **`Write`** (atau permissions: *Write access to Spaces*).
5. Klik **Create token**, lalu **Salin (Copy)** token yang diawali `hf_...`. Simpan sementara di notepad.

---

### 3️⃣ Langkah 3: Ekstraksi Kredensial & Berbagi Google Drive

1. **Jalankan Helper Lokal**:
   Buka terminal di folder `c:\TERR\4. WORK\6. Server GRAIN` dan jalankan:
   ```bash
   python generate_cloud_env.py
   ```
   *Skrip akan menampilkan `Client Email` Service Account dan otomatis menyalin string raw JSON ke clipboard Anda.*

2. **Bagikan Folder Google Drive**:
   - Buka [Google Drive](https://drive.google.com/) di browser.
   - Klik kanan folder root eksperimen GRAIN Sandbox > **Bagikan (Share)**.
   - Masukkan email Service Account (contoh: `grain-catalog-reader@grain-sandbox-server.iam.gserviceaccount.com`).
   - Beri peran **Viewer** (Pelihat), lalu klik **Kirim / Bagikan**.

3. **Salin Folder ID Google Drive**:
   - Buka folder tersebut di browser, salin kode ID di ujung URL:
     `https://drive.google.com/drive/folders/`**`1aBcDeFgHiJkLmNoPqRsTuVwXyZ_12345`**

---

### 4️⃣ Langkah 4: Atur Secrets & Variables di Hugging Face Space

1. Di halaman Space Hugging Face Anda, klik tab **Settings** (ikon gerigi).
2. Scroll ke bagian **Variables and secrets**.

#### A. Tambahkan Secrets (Kredensial Sensitif):
Klik tombol **New secret**:
- **Key**: `GDRIVE_SERVICE_ACCOUNT_RAW_JSON`  
  **Value**: *Paste string raw JSON 1 baris hasil salinan dari `generate_cloud_env.py`*
- **Key**: `ADMIN_PIN`  
  **Value**: `123456` *(atau PIN rahasia pilihan Anda)*

#### B. Tambahkan Variables (Konfigurasi Publik):
Klik tombol **New variable**:
- **Key**: `GDRIVE_ROOT_FOLDER_ID`  
  **Value**: *ID folder Google Drive yang Anda salin pada Langkah 3*
- **Key**: `PORTAL_TITLE`  
  **Value**: `GRAIN Sandbox Experiment Data Server`
- **Key**: `PORTAL_SUBTITLE`  
  **Value**: `Analog Geological & Tectonic Modeling Video/Photo Catalog`

---

### 5️⃣ Langkah 5: Push Kode ke Hugging Face Space

Anda dapat memilih salah satu cara berikut:

#### ⚡ Opsi A: Menggunakan Skrip Otomatis (Direkomendasikan)
Dobel klik file **`push_to_hf.bat`** di folder `c:\TERR\4. WORK\6. Server GRAIN`.
- Masukkan URL Space Hugging Face Anda (misal: `https://huggingface.co/spaces/terryfurqan/grain-sandbox-catalog`).
- Saat diminta kredensial:
  - **Username**: Masukkan username akun Hugging Face Anda.
  - **Password**: Masukkan Access Token `hf_...` yang telah dibuat pada Langkah 2.
- Skrip akan otomatis mengompilasi commit dan melakukan push!

#### 💻 Opsi B: Menggunakan Perintah Git Terminal
Jalankan perintah berikut di PowerShell / Command Prompt:
```bash
# Tambahkan remote Hugging Face (ganti USERNAME dan SPACE_NAME)
git remote add space https://huggingface.co/spaces/USERNAME/SPACE_NAME

# Pastikan branch main siap
git add .
git commit -m "feat: deploy GRAIN catalog to Hugging Face Spaces"

# Push ke Space (force push untuk menimpa README default awal HF)
git push space main:main --force
```

---

### 6️⃣ Langkah 6: Verifikasi & Sinkronisasi Katalog Pertama

1. Kembali ke tab **App** di Space Hugging Face Anda.
2. Anda akan melihat proses **Building Docker Container** (~1-2 menit).
3. Setelah status menjadi **Running** (hijau), antarmuka web katalog GRAIN akan muncul!
4. **Lakukan Sinkronisasi Pertama**:
   - Klik tombol **Admin Panel** di pojok kanan atas (atau akses `/setup`).
   - Masukkan `ADMIN_PIN` Anda (`123456`).
   - Klik **"Test Connection"** untuk memverifikasi koneksi Google Drive.
   - Klik **"Trigger Manual Sync"** untuk memindai seluruh eksperimen dan menyimpannya ke database index.
   - Kembali ke beranda (`/`) dan nikmati penjelajahan katalog serta pemutaran video MP4 resolusi tinggi langsung dari cloud!

---

## 🔄 Sinkronisasi Otomatis dari GitHub (Opsional)

Jika repositori Anda sudah ada di GitHub (`github.com/terryfurqan/grain-sandbox-catalog`) dan ingin setiap kali melakukan `git push origin main` otomatis terupdate ke Hugging Face Spaces:

1. Di GitHub Repository > **Settings** > **Secrets and variables** > **Actions** > **New repository secret**.
   - Name: `HF_TOKEN`
   - Value: Token Hugging Face Anda (`hf_...`).
2. Buat file workflow `.github/workflows/sync_to_hf.yml`:
   ```yaml
   name: Sync to Hugging Face Spaces
   on:
     push:
       branches: [main]
   jobs:
     sync-to-hf:
       runs-on: ubuntu-latest
       steps:
         - uses: actions/checkout@v4
           with:
             fetch-depth: 0
             lfs: true
         - name: Push to Hugging Face
           env:
             HF_TOKEN: ${{ secrets.HF_TOKEN }}
           run: git push --force https://USER:$HF_TOKEN@huggingface.co/spaces/USERNAME/SPACE_NAME main:main
   ```

---

## 🛠️ Solusi Kendala Umum (Troubleshooting)

| Masalah | Penyebab | Solusi |
|---|---|---|
| **Git Push Ditolak: Invalid credentials** | Hugging Face tidak menerima password akun biasa | Gunakan Access Token (`hf_...`) dengan permission **Write** sebagai password. |
| **Error: non-fast-forward / reject** | Hugging Face Space memiliki commit awal dari web UI | Gunakan `git push space main:main --force`. |
| **Status Space: "Container Error" atau "Port unreachable"** | Port yang diexpose salah | Server telah dikonfigurasi untuk membaca `$PORT` dan port default `7860` yang sesuai dengan standar Hugging Face Docker Spaces. |
| **Status GDrive: "Unauthorized / 401"** | String JSON Kredensial terpotong | Jalankan ulang `python generate_cloud_env.py` lalu perbarui secret `GDRIVE_SERVICE_ACCOUNT_RAW_JSON` di Settings Space. |
| **Folder Eksperimen Tidak Terbaca** | Email service account belum diberi akses | Buka Google Drive > bagikan folder root eksperimen ke email service account dengan role **Viewer**. |
