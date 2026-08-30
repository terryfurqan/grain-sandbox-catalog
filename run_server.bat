@echo off
setlocal enabledelayedexpansion
title GRAIN Sandbox Data Catalog Server

:: Pindah ke direktori tempat batch script berada
cd /d "%~dp0"

echo ==============================================================================
echo   GRAIN SANDBOX EXPERIMENT DATA SERVER
echo   Analog Geological ^& Tectonic Modeling Video/Photo Catalog
echo ==============================================================================
echo.

:: 1. Cek apakah Python terinstall
echo [*] Memeriksa instalasi Python...
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan di sistem Anda!
    echo         Silakan install Python 3.10 atau versi lebih baru dari:
    echo         https://www.python.org/downloads/
    echo         Pastikan mencentang opsi "Add Python to PATH" saat instalasi.
    echo.
    pause
    exit /b 1
)

for /f "tokens=*" %%v in ('python --version 2^>^&1') do set PYTHON_VERSION=%%v
echo [+] Ditemukan: %PYTHON_VERSION%

:: 2. Cek dan install dependensi dari requirements.txt
if exist "requirements.txt" (
    echo [*] Memeriksa dan memperbarui dependensi pustaka...
    python -m pip install --quiet --disable-pip-version-check -r requirements.txt
    if %errorlevel% neq 0 (
        echo [WARNING] Ada kendala saat mengunduh paket dependensi.
        echo           Mencoba menjalankan server dengan pustaka yang ada...
    ) else (
        echo [+] Seluruh dependensi Python siap.
    )
) else (
    echo [!] File requirements.txt tidak ditemukan di direktori saat ini.
)

:: 3. Ambil IP LAN untuk akses lokal jaringan
set LAN_IP=127.0.0.1
for /f "tokens=*" %%a in ('powershell -NoProfile -Command "Get-NetIPAddress -AddressFamily IPv4 -InterfaceAlias 'Wi-Fi*','Ethernet*','vEthernet*' -ErrorAction SilentlyContinue | Where-Object {$_.IPAddress -notlike '127.*' -and $_.IPAddress -notlike '169.254.*'} | Select-Object -ExpandProperty IPAddress -First 1"') do (
    if not "%%a"=="" set LAN_IP=%%a
)

:: 4. Tampilkan Banner Informasi
echo.
echo ==============================================================================
echo                       SERVER GRAIN BERHASIL AKTIF
echo ==============================================================================
echo   Local Web URL    : http://localhost:8080
echo   LAN / Wi-Fi URL  : http://%LAN_IP%:8080
echo   Setup ^& Config   : http://localhost:8080/setup
echo   API Swagger Docs : http://localhost:8080/docs
echo ==============================================================================
echo   Tekan [CTRL + C] di jendela terminal ini untuk menghentikan server.
echo ==============================================================================
echo.

:: 5. Buka Web Browser secara otomatis setelah jeda singkat
start "" cmd /c "timeout /t 2 /nobreak >nul && start http://localhost:8080"

:: 6. Jalankan Uvicorn ASGI Server
python -m uvicorn app.main:app --host 0.0.0.0 --port 8080 --reload

pause
