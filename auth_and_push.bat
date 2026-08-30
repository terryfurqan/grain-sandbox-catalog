@echo off
setlocal enabledelayedexpansion
title Otomatisasi GitHub & Cloud Deployment - GRAIN Server
cd /d "%~dp0"

echo ==============================================================================
echo   OTOMATISASI REPOSITORY GITHUB ^& CLOUD DEPLOYMENT
echo ==============================================================================
echo.

:: Tambahkan GitHub CLI ke PATH jika belum ada
set "PATH=%PATH%;C:\Program Files\GitHub CLI;C:\Users\Sandbox_Main\AppData\Local\Programs\GitHub CLI"

:: 1. Cek apakah gh sudah terinstall
where gh >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] GitHub CLI (gh) tidak ditemukan.
    pause
    exit /b 1
)

:: 2. Cek status login GitHub
echo [*] Memeriksa autentikasi akun GitHub...
gh auth status >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Akun GitHub Anda belum terhubung di terminal ini.
    echo [*] Membuka browser untuk otorisasi 1-klik ke GitHub...
    echo.
    gh auth login --web -p https -h github.com
)

echo.
echo [+] Autentikasi GitHub Terverifikasi!
echo.

:: 3. Buat repo di GitHub dan langsung push otomatis
echo [*] Membuat repository baru 'grain-sandbox-catalog' di akun GitHub Anda (Private)...
gh repo create grain-sandbox-catalog --private --source=. --remote=origin --push
if %errorlevel% neq 0 (
    echo [!] Mencoba push ke remote origin yang sudah ada...
    git push -u origin main
)

echo.
echo ==============================================================================
echo   BERHASIL! REPOSITORY GITHUB ANDA SUDAH AKTIF ^& TER-PUSH:
echo ==============================================================================
gh repo view --web
echo ==============================================================================
echo.
echo [*] Menyalin kredensial Service Account untuk Render.com...
python generate_cloud_env.py
echo.
pause
