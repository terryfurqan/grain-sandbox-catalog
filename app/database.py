import sqlite3
import contextlib
from pathlib import Path
from typing import Generator, List, Dict, Any, Optional
from app.config import settings

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@contextlib.contextmanager
def get_db() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(settings.DATABASE_PATH, timeout=30.0)
    conn.row_factory = dict_factory
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabel Experiments (Folder Level-1 di bawah Root)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS experiments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            folder_id TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            description TEXT DEFAULT '',
            video_count INTEGER DEFAULT 0,
            photo_count INTEGER DEFAULT 0,
            other_count INTEGER DEFAULT 0,
            total_size_bytes INTEGER DEFAULT 0,
            cover_file_id TEXT,
            last_modified TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

        # Tabel Files (Semua File & Folder yang di-scan dari GDrive)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS files (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_id TEXT UNIQUE NOT NULL,
            parent_folder_id TEXT NOT NULL,
            experiment_folder_id TEXT,
            name TEXT NOT NULL,
            mime_type TEXT NOT NULL,
            file_type TEXT NOT NULL, -- 'video', 'image', 'document', 'archive', 'folder', 'other'
            size_bytes INTEGER DEFAULT 0,
            relative_path TEXT DEFAULT '',
            md5_checksum TEXT,
            thumbnail_link TEXT,
            web_view_link TEXT,
            last_modified TEXT,
            is_folder INTEGER DEFAULT 0
        );
        """)

        # Index untuk query super cepat
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_parent ON files(parent_folder_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_exp ON files(experiment_folder_id);")
        cursor.execute("CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type);")

        # Tabel Sync Logs
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS sync_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            status TEXT NOT NULL, -- 'RUNNING', 'COMPLETED', 'FAILED'
            started_at TEXT NOT NULL,
            finished_at TEXT,
            total_files_scanned INTEGER DEFAULT 0,
            total_experiments_found INTEGER DEFAULT 0,
            message TEXT
        );
        """)

        # Tabel Settings Cache
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS system_metadata (
            key TEXT PRIMARY KEY,
            value TEXT,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """)

def format_file_size(size_in_bytes: int) -> str:
    if not size_in_bytes:
        return "0 B"
    units = ["B", "KB", "MB", "GB", "TB"]
    unit_index = 0
    size = float(size_in_bytes)
    while size >= 1024.0 and unit_index < len(units) - 1:
        size /= 1024.0
        unit_index += 1
    return f"{size:.2f} {units[unit_index]}"

def categorize_file(mime_type: str, file_name: str) -> str:
    name_lower = file_name.lower()
    if mime_type == "application/vnd.google-apps.folder":
        return "folder"
    if mime_type.startswith("video/") or name_lower.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
        return "video"
    if mime_type.startswith("image/") or name_lower.endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp")):
        return "image"
    if mime_type.startswith("text/") or name_lower.endswith((".pdf", ".pptx", ".ppt", ".docx", ".doc", ".xlsx", ".csv", ".txt", ".json", ".xml")):
        return "document"
    if name_lower.endswith((".zip", ".tar", ".gz", ".rar", ".7z", ".npz", ".grainraw")):
        return "archive"
    return "other"
