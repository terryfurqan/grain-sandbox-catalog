# 🛡️ Panduan FinOps & Automated Kill-Switch GCP

Panduan ini berisi arsitektur dan langkah-langkah konkret untuk mengunci biaya operasional **GRAIN Server** pada batas **Rp 0 / Free Tier** dan mengaktifkan sakelar darurat otomatis (*Automated Kill-Switch*).

---

## 1. Arsitektur Pertahanan Biaya (Cost Defense Matrix)

```
                       [Pengguna / Bot Internet]
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │ Cloud Run Edge Handler  │
                     │  - Max Instances: 1     │ <─── Anti Auto-scale Runaway
                     │  - Concurrency: 80      │
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │  FastAPI Application    │
                     │  - SlowAPI Rate Limiter │ <─── Anti Scraping / Flooding
                     │  - Cache-Control 7 Hari │ <─── Anti Egress Drainage
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │ Google Drive API (Proxy)│
                     └─────────────────────────┘

                     ┌─────────────────────────┐
                     │ GCP Billing Alert ($5)  │
                     └────────────┬────────────┘
                                  │ (Trigger saat > $5)
                                  ▼
                     ┌─────────────────────────┐
                     │ Pub/Sub: billing-topic  │
                     └────────────┬────────────┘
                                  │
                                  ▼
                     ┌─────────────────────────┐
                     │ Cloud Function          │
                     │ (Kill-Switch Invoker)   │ ───► Cabut 'allUsers' dari Cloud Run
                     └─────────────────────────┘
```

---

## 2. Langkah Konfigurasi Budget Alert Bertingkat

### Lewat Google Cloud Console:
1. Buka [Google Cloud Console - Billing](https://console.cloud.google.com/billing).
2. Pilih **Budgets & alerts** di menu sebelah kiri.
3. Klik **+ CREATE BUDGET**.
4. Isi parameter:
   - **Scope**: Pilih project Anda.
   - **Target Amount**: Masukkan **$5.00** (atau Rp 80.000).
   - **Threshold Rules**:
     - `50%` ($2.50) -> Email alert
     - `80%` ($4.00) -> Email alert
     - `100%` ($5.00) -> Email alert + Pub/Sub notification
5. Di bagian **Manage notifications**:
   - Centang **Connect a Pub/Sub topic to this budget**.
   - Buat topic baru dengan nama: `billing-killswitch-topic`.
6. Klik **Save**.

---

## 3. Deploy Cloud Function Kill-Switch (Otomatis)

Jalankan perintah berikut di Cloud Shell atau terminal komputer lokal:

```bash
cd finops/killswitch

gcloud functions deploy grain-billing-killswitch \
    --runtime python312 \
    --trigger-topic billing-killswitch-topic \
    --entry-point billing_killswitch \
    --region asia-southeast2 \
    --set-env-vars SERVICE_NAME=grain-server,SERVICE_REGION=asia-southeast2 \
    --project=PROJECT_ID
```

Berikan role IAM ke service account Cloud Function agar dapat memodifikasi policy Cloud Run:
```bash
gcloud projects add-iam-policy-binding PROJECT_ID \
    --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
    --role="roles/run.admin"
```

---

## 4. Cara Mengaktifkan Kembali Service Setelah Terkunci

Jika kill-switch terpicu dan Anda ingin membuka kembali akses ke publik setelah audit selesai:

```bash
gcloud run services add-iam-policy-binding grain-server \
    --region=asia-southeast2 \
    --member="allUsers" \
    --role="roles/run.invoker" \
    --project=PROJECT_ID
```