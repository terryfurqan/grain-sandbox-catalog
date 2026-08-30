from fastapi import APIRouter, HTTPException, BackgroundTasks, Depends
from datetime import datetime
import threading
import logging
from app.config import settings
from app.database import get_db
from app.gdrive import gdrive_client
from app.models import SyncRequest, SyncStatusResponse

router = APIRouter(prefix="/api/sync", tags=["Synchronization"])
logger = logging.getLogger("sync")

_sync_lock = threading.Lock()
_is_syncing = False
_current_scanned = 0

def execute_sync_background():
    global _is_syncing, _current_scanned
    started_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_id = None

    try:
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO sync_logs (status, started_at, message)
                VALUES ('RUNNING', ?, 'Sedang memindai folder Google Drive...');
            """, (started_at,))
            log_id = cursor.lastrowid

        def on_progress(count):
            global _current_scanned
            _current_scanned = count

        result = gdrive_client.scan_and_index_all(progress_callback=on_progress)
        finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                UPDATE sync_logs
                SET status = 'COMPLETED',
                    finished_at = ?,
                    total_files_scanned = ?,
                    total_experiments_found = ?,
                    message = 'Sinkronisasi berhasil diselesaikan.'
                WHERE id = ?;
            """, (finished_at, result["total_files"], result["total_experiments"], log_id))

        logger.info(f"Sync complete: {result['total_files']} files, {result['total_experiments']} experiments.")

    except Exception as e:
        logger.error(f"Sync failed: {str(e)}", exc_info=True)
        finished_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        if log_id:
            with get_db() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE sync_logs
                    SET status = 'FAILED',
                        finished_at = ?,
                        message = ?
                    WHERE id = ?;
                """, (finished_at, f"Error: {str(e)}", log_id))
    finally:
        _is_syncing = False
        _current_scanned = 0

@router.post("/trigger")
def trigger_sync(req: SyncRequest):
    global _is_syncing
    if req.admin_pin != settings.ADMIN_PIN:
        raise HTTPException(status_code=401, detail="PIN Admin salah!")

    if not settings.is_configured():
        raise HTTPException(
            status_code=400, 
            detail="Google Drive belum dikonfigurasi. Silakan lengkapi file credentials.json dan Root Folder ID."
        )

    with _sync_lock:
        if _is_syncing:
            return {"status": "already_running", "message": "Proses sinkronisasi sedang berjalan di latar belakang."}
        _is_syncing = True

    thread = threading.Thread(target=execute_sync_background, daemon=True)
    thread.start()

    return {"status": "started", "message": "Proses sinkronisasi katalog dimulai di latar belakang."}

@router.get("/status")
def get_sync_status():
    global _is_syncing, _current_scanned
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM sync_logs ORDER BY id DESC LIMIT 1;")
        last_log = cursor.fetchone()

    return {
        "is_syncing": _is_syncing,
        "current_scanned": _current_scanned,
        "last_log": last_log
    }
