@echo off
setlocal enabledelayedexpansion
title GRAIN Sandbox Data Catalog - Push ke Hugging Face Spaces

echo ==============================================================================
echo        GRAIN SANDBOX DATA CATALOG - HUGGING FACE SPACES DEPLOYER
echo ==============================================================================
echo.

:: 1. Verifikasi Git
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git tidak ditemukan di PATH sistem Anda.
    echo Silakan install Git terlebih dahulu: https://git-scm.com/
    echo.
    pause
    exit /b 1
)

:: 2. Pastikan git repo terinisialisasi
if not exist ".git" (
    echo [INFO] Inisialisasi git repository lokal...
    git init
    git branch -M main
)

:: 3. Konfigurasi Remote 'space'
git remote get-url space >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "delims=" %%i in ('git remote get-url space') do set CURRENT_SPACE_REMOTE=%%i
    echo Remote 'space' (Hugging Face) saat ini:
    echo   !CURRENT_SPACE_REMOTE!
    echo.
    set /p "USE_EXISTING=Gunakan Space remote ini? (Y/n): "
    if /i "!USE_EXISTING!"=="n" (
        set /p "SPACE_URL=Masukkan URL Hugging Face Space baru (misal: https://huggingface.co/spaces/username/space-name): "
        if not "!SPACE_URL!"=="" (
            git remote set-url space !SPACE_URL!
            echo Remote 'space' berhasil diperbarui ke: !SPACE_URL!
        )
    )
) else (
    echo Remote 'space' belum terkonfigurasi.
    echo.
    echo Silakan buat Space baru di Hugging Face dengan SDK 'Docker' terlebih dahulu:
    echo   https://huggingface.co/new-space
    echo.
    echo Contoh URL Space:
    echo   https://huggingface.co/spaces/terryfurqan/grain-sandbox-catalog
    echo.
    set /p "SPACE_URL=Masukkan URL Hugging Face Space Anda: "
    if "!SPACE_URL!"=="" (
        echo [ERROR] URL Space tidak boleh kosong.
        echo.
        pause
        exit /b 1
    )
    git remote add space !SPACE_URL!
    echo Remote 'space' berhasil ditambahkan: !SPACE_URL!
)

echo.
echo ------------------------------------------------------------------------------
echo Mempersiapkan komit dan deploy ke Hugging Face Spaces...
echo ------------------------------------------------------------------------------

:: 4. Commit perubahan lokal jika ada
git add .
git status --porcelain >nul 2>&1
for /f "delims=" %%s in ('git status --porcelain') do (
    set UNCOMMITTED=1
)

if defined UNCOMMITTED (
    set /p "COMMIT_MSG=Pesan commit (Tekan Enter untuk: 'deploy: update for Hugging Face Spaces'): "
    if "!COMMIT_MSG!"=="" set "COMMIT_MSG=deploy: update for Hugging Face Spaces"
    git commit -m "!COMMIT_MSG!"
)

echo.
echo [INFO] Mengirim kode ke Hugging Face Spaces (git push space main:main)...
echo.
echo Catatan Autentikasi:
echo   - Username: Username Hugging Face Anda
echo   - Password: User Access Token (Write) dari https://huggingface.co/settings/tokens
echo.

git push space main:main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo [SUKSES] Aplikasi berhasil di-push ke Hugging Face Spaces!
    echo.
    echo Langkah selanjutnya:
    echo 1. Buka Space Anda di Hugging Face.
    echo 2. Masuk ke tab 'Settings' -> 'Variables and secrets'.
    echo 3. Pastikan Secret 'GDRIVE_SERVICE_ACCOUNT_RAW_JSON' dan Variable 'GDRIVE_ROOT_FOLDER_ID' sudah terisi.
    echo 4. Space akan melakukan build Docker dan Live dalam 1-2 menit!
    echo ==============================================================================
) else (
    echo.
    echo ==============================================================================
    echo [PERHATIAN] Push ke Space gagal atau tertahan.
    echo Tips Penanganan:
    echo - Jika Space baru dibuat dan sudah berisi README bawaan Hugging Face, jalankan:
    echo     git push space main:main --force
    echo - Pastikan Access Token memiliki izin 'Write' (Settings -> Access Tokens).
    echo ==============================================================================
)

echo.
pause
