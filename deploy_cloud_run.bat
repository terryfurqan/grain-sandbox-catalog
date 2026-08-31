@echo off
chcp 65001 >nul
echo ==============================================================================
echo  🚀 GRAIN Server - Google Cloud Run Deployment (FinOps Hard-Capped)
echo ==============================================================================
echo.

set /p PROJECT_ID="Masukkan Google Cloud Project ID: "
if "%PROJECT_ID%"=="" (
    echo [ERROR] Project ID tidak boleh kosong!
    pause
    exit /b 1
)

set REGION=asia-southeast2
set SERVICE_NAME=grain-server

echo.
echo [*] Mengaktifkan API yang dibutuhkan...
call gcloud services enable run.googleapis.com artifactregistry.googleapis.com cloudbuild.googleapis.com --project=%PROJECT_ID%

echo.
echo [*] Memastikan Repository Artifact Registry ada...
call gcloud artifacts repositories describe grain-repo --location=%REGION% --project=%PROJECT_ID% >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [*] Membuat repository grain-repo di Artifact Registry...
    call gcloud artifacts repositories create grain-repo --repository-format=docker --location=%REGION% --description="GRAIN Docker Repository" --project=%PROJECT_ID%
)

echo.
echo [*] Memasang FinOps Cleanup Policy ke Artifact Registry (Auto-delete old images)...
call gcloud artifacts repositories set-cleanup-policies grain-repo --location=%REGION% --project=%PROJECT_ID% --policy=cleanup-policy.json --no-user-output-enabled

echo.
echo [*] Melakukan Build & Deploy ke Cloud Run dengan Hard Limits:
echo     - Min Instances: 0 (Zero Idle Cost)
echo     - Max Instances: 1 (Anti Auto-scale Runaway)
echo     - Concurrency: 80
echo     - Memory: 512Mi, CPU: 1 (CPU Throttled)
echo.

call gcloud run deploy %SERVICE_NAME% ^
    --source . ^
    --project=%PROJECT_ID% ^
    --region=%REGION% ^
    --platform=managed ^
    --allow-unauthenticated ^
    --min-instances=0 ^
    --max-instances=1 ^
    --concurrency=80 ^
    --cpu=1 ^
    --memory=512Mi ^
    --timeout=60s ^
    --cpu-throttling ^
    --execution-environment=gen2

echo.
echo ==============================================================================
echo  ✅ Deployment Selesai dengan Proteksi FinOps Aktif!
echo ==============================================================================
pause
