from fastapi import APIRouter, HTTPException, Query, Request
from typing import List, Optional, Dict, Any
from app.database import get_db, format_file_size
from app.config import settings
from app.limiter import limiter

router = APIRouter(prefix="/api", tags=["Catalog"])

@router.get("/stats")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def get_catalog_stats(request: Request):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as count, SUM(total_size_bytes) as total_size FROM experiments;")
        exp_row = cursor.fetchone()
        
        cursor.execute("SELECT COUNT(*) as count FROM files WHERE file_type = 'video';")
        vid_row = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) as count FROM files WHERE file_type = 'image';")
        img_row = cursor.fetchone()

        cursor.execute("SELECT COUNT(*) as count FROM files WHERE is_folder = 0;")
        file_row = cursor.fetchone()

        cursor.execute("SELECT * FROM sync_logs ORDER BY id DESC LIMIT 1;")
        last_sync = cursor.fetchone()

        total_bytes = exp_row["total_size"] or 0

        return {
            "total_experiments": exp_row["count"] or 0,
            "total_videos": vid_row["count"] or 0,
            "total_photos": img_row["count"] or 0,
            "total_files": file_row["count"] or 0,
            "total_size_bytes": total_bytes,
            "total_size_formatted": format_file_size(total_bytes),
            "last_sync": last_sync
        }

@router.get("/experiments")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def list_experiments(request: Request):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experiments ORDER BY name ASC;")
        rows = cursor.fetchall()
        for r in rows:
            r["total_size_formatted"] = format_file_size(r["total_size_bytes"])
        return rows

@router.get("/experiments/{folder_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def get_experiment_detail(folder_id: str, request: Request):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM experiments WHERE folder_id = ?;", (folder_id,))
        exp = cursor.fetchone()
        if not exp:
            raise HTTPException(status_code=404, detail="Eksperimen tidak ditemukan")
        
        exp["total_size_formatted"] = format_file_size(exp["total_size_bytes"])
        
        # Ambil semua video & foto untuk eksperimen ini
        cursor.execute("""
            SELECT * FROM files 
            WHERE experiment_folder_id = ? AND is_folder = 0
            ORDER BY file_type DESC, name ASC;
        """, (folder_id,))
        files = cursor.fetchall()
        for f in files:
            f["size_formatted"] = format_file_size(f["size_bytes"])
            f["is_folder"] = bool(f["is_folder"])

        return {
            "experiment": exp,
            "files": files
        }

@router.get("/folders/{folder_id}/items")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def get_folder_items(folder_id: str, request: Request):
    """
    Mengambil subfolder dan file yang langsung berada di bawah folder_id tertentu (untuk File Explorer / Tree).
    Jika folder_id == 'root', maka menggunakan GDRIVE_ROOT_FOLDER_ID.
    """
    target_id = settings.GDRIVE_ROOT_FOLDER_ID if folder_id == "root" else folder_id
    if not target_id:
        return {"current_folder": None, "breadcrumbs": [], "items": []}

    with get_db() as conn:
        cursor = conn.cursor()
        
        # Ambil info current folder
        current_folder = None
        if target_id == settings.GDRIVE_ROOT_FOLDER_ID:
            current_folder = {
                "file_id": target_id,
                "name": "Root Drive",
                "relative_path": ""
            }
        else:
            cursor.execute("SELECT * FROM files WHERE file_id = ? AND is_folder = 1;", (target_id,))
            current_folder = cursor.fetchone()

        # Ambil items langsung di bawah target_id
        cursor.execute("""
            SELECT * FROM files 
            WHERE parent_folder_id = ?
            ORDER BY is_folder DESC, name ASC;
        """, (target_id,))
        items = cursor.fetchall()
        for item in items:
            item["size_formatted"] = format_file_size(item["size_bytes"])
            item["is_folder"] = bool(item["is_folder"])

        # Bangun breadcrumbs
        breadcrumbs = [{"id": "root", "name": "Root"}]
        if current_folder and current_folder.get("relative_path"):
            parts = current_folder["relative_path"].split("/")
            accum_path = ""
            for p in parts:
                accum_path = f"{accum_path}/{p}".strip("/")
                cursor.execute("SELECT file_id, name FROM files WHERE relative_path = ? AND is_folder = 1 LIMIT 1;", (accum_path,))
                p_row = cursor.fetchone()
                if p_row:
                    breadcrumbs.append({"id": p_row["file_id"], "name": p_row["name"]})
                else:
                    breadcrumbs.append({"id": "", "name": p})

        return {
            "current_folder": current_folder,
            "breadcrumbs": breadcrumbs,
            "items": items
        }

@router.get("/search")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
def search_files(
    request: Request,
    q: str = Query("", description="Search keyword"),
    file_type: Optional[str] = Query(None, description="Filter type: video, image, document, archive"),
    experiment_id: Optional[str] = Query(None, description="Filter by experiment folder ID")
):
    with get_db() as conn:
        cursor = conn.cursor()
        sql = "SELECT * FROM files WHERE is_folder = 0"
        params = []

        if q.strip():
            sql += " AND (name LIKE ? OR relative_path LIKE ?)"
            params.extend([f"%{q.strip()}%", f"%{q.strip()}%"])

        if file_type:
            sql += " AND file_type = ?"
            params.append(file_type)

        if experiment_id:
            sql += " AND experiment_folder_id = ?"
            params.append(experiment_id)

        sql += " ORDER BY name ASC LIMIT 100;"
        cursor.execute(sql, tuple(params))
        rows = cursor.fetchall()
        for r in rows:
            r["size_formatted"] = format_file_size(r["size_bytes"])
            r["is_folder"] = False
        return rows
