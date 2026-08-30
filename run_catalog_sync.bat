@echo off
setlocal
title GRAIN Explorer - Catalog Sync Runner
echo =======================================================================
echo               GRAIN EXPLORER: 1-CLICK CATALOG SYNC
echo =======================================================================
echo Target Storage  : D:\999_GRAIN_EXPLORER\0010
echo Target Manifest : D:\999_GRAIN_EXPLORER\0000
echo.

python "%~dp0grain_catalog_indexer.py" --storage-dir "D:\999_GRAIN_EXPLORER\0010" --manifest-dir "D:\999_GRAIN_EXPLORER\0000"

if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [ERROR] Sinkronisasi katalog mengalami kegagalan.
) else (
    echo.
    echo [OK] Sinkronisasi katalog berhasil diperbarui!
)

echo.
pause
