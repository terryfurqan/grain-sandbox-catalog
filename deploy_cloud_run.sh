#!/usr/bin/env bash
# ==============================================================================
# GRAIN Server - Google Cloud Run Deployment Script (FinOps Hard-Capped)
# ==============================================================================
set -euo pipefail

echo "=============================================================================="
echo " 🚀 GRAIN Server - Google Cloud Run Deployment (FinOps Hard-Capped)"
echo "=============================================================================="

if [ -z "" ]; then
  read -rp "Masukkan Google Cloud Project ID: " PROJECT_ID
fi

REGION="asia-southeast2"
SERVICE_NAME="grain-server"

echo "[*] Mengaktifkan API yang dibutuhkan..."
gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --project=""

echo "[*] Memeriksa repository Artifact Registry..."
if ! gcloud artifacts repositories describe grain-repo --location="" --project="" >/dev/null 2>&1; then
  echo "[*] Membuat repository grain-repo di Artifact Registry..."
  gcloud artifacts repositories create grain-repo \
    --repository-format=docker \
    --location="" \
    --description="GRAIN Docker Repository" \
    --project=""
fi

echo "[*] Memasang FinOps Cleanup Policy ke Artifact Registry..."
gcloud artifacts repositories set-cleanup-policies grain-repo \
  --location="" \
  --project="" \
  --policy=cleanup-policy.json

echo "[*] Melakukan Build & Deploy ke Cloud Run dengan Hard Limits..."
gcloud run deploy "" \
  --source . \
  --project="" \
  --region="" \
  --platform=managed \
  --allow-unauthenticated \
  --min-instances=0 \
  --max-instances=1 \
  --concurrency=80 \
  --cpu=1 \
  --memory=512Mi \
  --timeout=60s \
  --cpu-throttling \
  --execution-environment=gen2

echo "=============================================================================="
echo " ✅ Deployment Selesai dengan Proteksi FinOps Aktif!"
echo "=============================================================================="
