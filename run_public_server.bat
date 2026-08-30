@echo off
setlocal enabledelayedexpansion
title GRAIN Sandbox Server - Public Cloudflare Tunnel

cd /d "%~dp0"

echo ==============================================================================
echo   GRAIN SANDBOX DATA SERVER - LAUNCHER PUBLIK CLOUDFLARE TUNNEL
echo ==============================================================================
echo.

where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [ERROR] Python tidak ditemukan di sistem Anda!
    pause
    exit /b 1
)

python launch_public_tunnel.py

pause
