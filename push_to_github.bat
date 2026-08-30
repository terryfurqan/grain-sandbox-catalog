@echo off
setlocal enabledelayedexpansion
title GRAIN Sandbox Data Catalog - Push to GitHub

echo ==============================================================================
echo        GRAIN SANDBOX DATA CATALOG - GITHUB REPOSITORY PUSHER
echo ==============================================================================
echo.

:: 1. Check Git availability
where git >nul 2>&1
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Git tidak ditemukan di PATH sistem Anda.
    echo Silakan install Git terlebih dahulu: https://git-scm.com/
    echo.
    pause
    exit /b 1
)

:: 2. Check if this is a git repo
if not exist ".git" (
    echo [INFO] Inisialisasi git repository lokal...
    git init
    git branch -M main
)

:: 3. Check existing remote
git remote get-url origin >nul 2>&1
if %ERRORLEVEL% EQU 0 (
    for /f "delims=" %%i in ('git remote get-url origin') do set CURRENT_REMOTE=%%i
    echo Remote 'origin' saat ini terdeteksi:
    echo   !CURRENT_REMOTE!
    echo.
    set /p "USE_EXISTING=Gunakan remote ini untuk push? (Y/n): "
    if /i "!USE_EXISTING!"=="n" (
        set /p "REPO_URL=Masukkan URL Repository GitHub baru: "
        if not "!REPO_URL!"=="" (
            git remote set-url origin !REPO_URL!
            echo Remote origin berhasil diperbarui ke: !REPO_URL!
        )
    )
) else (
    echo Remote 'origin' belum terkonfigurasi.
    echo.
    echo Contoh URL:
    echo   - HTTPS : https://github.com/USERNAME/grain-server.git
    echo   - SSH   : git@github.com:USERNAME/grain-server.git
    echo.
    set /p "REPO_URL=Masukkan URL Repository GitHub: "
    if "!REPO_URL!"=="" (
        echo [ERROR] URL repository tidak boleh kosong.
        echo.
        pause
        exit /b 1
    )
    git remote add origin !REPO_URL!
    echo Remote origin berhasil ditambahkan: !REPO_URL!
)

echo.
echo ------------------------------------------------------------------------------
echo Mempersiapkan push ke GitHub branch 'main'...
echo ------------------------------------------------------------------------------

:: 4. Ensure current branch is main
git branch -M main

:: 5. Stage & commit check
git status --porcelain >nul 2>&1
for /f "delims=" %%s in ('git status --porcelain') do (
    set UNCOMMITTED=1
)

if defined UNCOMMITTED (
    echo [INFO] Terdapat perubahan lokal yang belum di-commit.
    set /p "DO_COMMIT=Commit semua perubahan sekarang? (Y/n): "
    if /i not "!DO_COMMIT!"=="n" (
        git add .
        set /p "COMMIT_MSG=Pesan commit (Tekan Enter untuk default: 'update GRAIN server'): "
        if "!COMMIT_MSG!"=="" set "COMMIT_MSG=update GRAIN server"
        git commit -m "!COMMIT_MSG!"
    )
)

echo.
echo [INFO] Mengirim commit ke GitHub (git push -u origin main)...
git push -u origin main

if %ERRORLEVEL% EQU 0 (
    echo.
    echo ==============================================================================
    echo [SUKSES] Repository berhasil di-push ke GitHub!
    echo ==============================================================================
) else (
    echo.
    echo ==============================================================================
    echo [PERHATIAN] Push gagal atau membutuhkan autentikasi / penanganan conflict.
    echo - Jika repository di GitHub sudah memiliki README/commit lain, jalankan:
    echo     git pull origin main --allow-unrelated-histories --rebase
    echo     git push -u origin main
    echo - Pastikan Anda telah login ke GitHub CLI (gh auth login) atau Personal Access Token.
    echo ==============================================================================
)

echo.
pause
