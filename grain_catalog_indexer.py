#!/usr/bin/env python3
"""
GRAIN Explorer Catalog Indexer & Manifest Synchronizer
Ekosistem GRAIN 2.0 - Centralized Cataloguing Engine

Memindai eksperimen pemodelan sandbox di D:\\999_GRAIN_EXPLORER\\0010,
memvalidasi kepatuhan Flat Direct Taxonomy, dan memperbarui basis data
SQLite (catalog.db) serta manifest.json di D:\\999_GRAIN_EXPLORER\\0000.
"""

import os
import re
import sys
import json
import sqlite3
import hashlib
import mimetypes
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Any, Optional, Tuple

DEFAULT_BASE_DIR = Path("D:/999_GRAIN_EXPLORER")
DEFAULT_MANIFEST_DIR = DEFAULT_BASE_DIR / "0000"
DEFAULT_STORAGE_DIR = DEFAULT_BASE_DIR / "0010"

DB_SCHEMA = """
CREATE TABLE IF NOT EXISTS experiments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    folder_name TEXT UNIQUE NOT NULL,
    project TEXT NOT NULL,
    exp_date TEXT NOT NULL,
    exp_number INTEGER NOT NULL,
    total_shortening_pct REAL DEFAULT 0.0,
    total_frames INTEGER DEFAULT 0,
    total_files INTEGER DEFAULT 0,
    total_size_bytes INTEGER DEFAULT 0,
    has_grainraw INTEGER DEFAULT 0,
    has_piv INTEGER DEFAULT 0,
    has_videos INTEGER DEFAULT 0,
    has_slices INTEGER DEFAULT 0,
    has_reports INTEGER DEFAULT 0,
    cover_image_path TEXT,
    taxonomy_compliant INTEGER DEFAULT 1,
    last_indexed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER NOT NULL,
    prefix_code TEXT NOT NULL,
    category_name TEXT NOT NULL,
    subfolder_name TEXT NOT NULL,
    width_px INTEGER,
    height_px INTEGER,
    tag TEXT,
    file_count INTEGER DEFAULT 0,
    size_bytes INTEGER DEFAULT 0,
    FOREIGN KEY(experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    experiment_id INTEGER NOT NULL,
    relative_path TEXT NOT NULL,
    file_name TEXT NOT NULL,
    file_type TEXT NOT NULL,
    mime_type TEXT NOT NULL,
    size_bytes INTEGER DEFAULT 0,
    md5_hash TEXT,
    width_px INTEGER,
    height_px INTEGER,
    duration_sec REAL,
    last_modified TIMESTAMP,
    FOREIGN KEY(experiment_id) REFERENCES experiments(id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS sync_logs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    status TEXT NOT NULL,
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    finished_at TIMESTAMP,
    experiments_count INTEGER DEFAULT 0,
    files_count INTEGER DEFAULT 0,
    notes TEXT
);

CREATE INDEX IF NOT EXISTS idx_files_exp ON files(experiment_id);
CREATE INDEX IF NOT EXISTS idx_files_type ON files(file_type);
CREATE INDEX IF NOT EXISTS idx_cat_exp ON categories(experiment_id);
"""

# Regex Patterns
RE_EXP_ROOT = re.compile(r"^([A-Za-z0-9_\-\s]+)\s*-\s*(\d{6})\s*\(EXP\s*(\d+)\)$", re.IGNORECASE)
RE_DIMENSIONS = re.compile(r"(\d+)x(\d+)\s*px", re.IGNORECASE)
RE_TAG_CO = re.compile(r"\((CO(?:\s*\d+)?)\)", re.IGNORECASE)
RE_TAG_CROP = re.compile(r"\(Crop\)", re.IGNORECASE)
RE_TAG_GRAY = re.compile(r"\(Grayscale\)", re.IGNORECASE)

PREFIX_TAXONOMY_MAP = [
    (re.compile(r"^0\.1\.\s*RAW\s*-\s*Trial\s*M", re.I), "0.1", "Trial / Pre-run (RAW)"),
    (re.compile(r"^0\.[2-9]\.\s*Resize\s*-\s*Trial\s*M", re.I), "0.x", "Trial / Pre-run (Resize)"),
    (re.compile(r"^1\.1\.\s*RAW\s*-\s*M", re.I), "1.1", "Map View (RAW)"),
    (re.compile(r"^1\.[2-9]\.\s*Resize\s*-\s*M", re.I), "1.x", "Map View (Resize)"),
    (re.compile(r"^2\.1\.\s*RAW\s*-\s*P1", re.I), "2.1", "Profile View 1 (RAW)"),
    (re.compile(r"^2\.[2-9]\.\s*Resize\s*-\s*P1", re.I), "2.x", "Profile View 1 (Resize)"),
    (re.compile(r"^3\.1\.\s*RAW\s*-\s*P2", re.I), "3.1", "Profile View 2 (RAW)"),
    (re.compile(r"^3\.[2-9]\.\s*Resize\s*-\s*P2", re.I), "3.x", "Profile View 2 (Resize)"),
    (re.compile(r"^4a\.1\.\s*RAW\s*-\s*Slice\s*M", re.I), "4a.1", "Slice M (RAW)"),
    (re.compile(r"^4a\.[2-9]\.\s*Resize\s*-\s*Slice\s*M", re.I), "4a.x", "Slice M (Resize)"),
    (re.compile(r"^4b\.1\.\s*RAW\s*-\s*Slice\s*P", re.I), "4b.1", "Slice P (RAW)"),
    (re.compile(r"^4b\.[2-9]\.\s*Resize\s*-\s*Slice\s*P", re.I), "4b.x", "Slice P (Resize)"),
    (re.compile(r"^5\.1\.\s*RAW\s*-\s*3D", re.I), "5.1", "3D / Oblique View (RAW)"),
    (re.compile(r"^5\.[2-9]\.\s*Resize\s*-\s*3D", re.I), "5.x", "3D / Oblique View (Resize)"),
    (re.compile(r"^OUTPUT$", re.I), "OUTPUT", "Output Ecosystem"),
]


def format_bytes(size: int) -> str:
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"


def categorize_file(filename: str) -> str:
    fn = filename.lower()
    if fn.endswith((".mp4", ".mov", ".avi", ".mkv", ".webm")):
        return "video"
    if fn.endswith((".jpg", ".jpeg", ".png", ".tif", ".tiff", ".bmp", ".gif", ".webp")):
        return "image"
    if fn.endswith(".grainraw"):
        return "grainraw"
    if fn.endswith(".npz"):
        return "piv_npz"
    if fn.endswith((".pptx", ".ppt")):
        return "report_pptx"
    if fn.endswith((".py", ".bat", ".ps1", ".sh")):
        return "script"
    if fn.endswith((".txt", ".log", ".json", ".csv")):
        return "log"
    return "other"


def parse_subfolder(sub_name: str) -> Dict[str, Any]:
    prefix_code = "UNKNOWN"
    category_name = "Unknown Category"
    
    for regex, code, cat in PREFIX_TAXONOMY_MAP:
        if regex.search(sub_name):
            prefix_code = code
            category_name = cat
            break
            
    dim_match = RE_DIMENSIONS.search(sub_name)
    width = int(dim_match.group(1)) if dim_match else None
    height = int(dim_match.group(2)) if dim_match else None
    
    tag = None
    if RE_TAG_CO.search(sub_name):
        tag = RE_TAG_CO.search(sub_name).group(1)
    elif RE_TAG_CROP.search(sub_name):
        tag = "Crop"
    elif RE_TAG_GRAY.search(sub_name):
        tag = "Grayscale"
        
    return {
        "prefix_code": prefix_code,
        "category_name": category_name,
        "subfolder_name": sub_name,
        "width_px": width,
        "height_px": height,
        "tag": tag
    }


def scan_single_experiment(exp_dir: Path) -> Dict[str, Any]:
    folder_name = exp_dir.name
    match = RE_EXP_ROOT.match(folder_name)
    
    if match:
        project = match.group(1).strip()
        exp_date = match.group(2).strip()
        exp_number = int(match.group(3))
        is_naming_valid = True
    else:
        project = folder_name.split("-")[0].strip() if "-" in folder_name else folder_name
        exp_date = "UNKNOWN"
        exp_number = 1
        is_naming_valid = False

    categories = []
    files_list = []
    total_size = 0
    map_frames_count = 0
    shortening_pct = 0.0
    cover_image_rel = None
    
    has_grainraw = False
    has_piv = False
    has_videos = False
    has_slices = False
    has_reports = False
    
    missing_elements = []
    warnings = []
    
    if not is_naming_valid:
        warnings.append(f"Root naming does not strictly follow '[PROJECT] - [DDMMYY] (EXP [N])': '{folder_name}'")

    # Walk experiment directory
    subdirs = [d for d in exp_dir.iterdir() if d.is_dir()]
    root_files = [f for f in exp_dir.iterdir() if f.is_file()]
    
    # Process root files
    for rf in root_files:
        st = rf.stat()
        ftype = categorize_file(rf.name)
        mime, _ = mimetypes.guess_type(str(rf))
        files_list.append({
            "relative_path": rf.name,
            "file_name": rf.name,
            "file_type": ftype,
            "mime_type": mime or "application/octet-stream",
            "size_bytes": st.st_size,
            "last_modified": datetime.fromtimestamp(st.st_mtime).isoformat()
        })
        total_size += st.st_size
        if ftype == "report_pptx":
            has_reports = True

    # Process subfolders
    for sd in subdirs:
        sub_info = parse_subfolder(sd.name)
        sub_files = []
        sub_size = 0
        
        for root, _, fs in os.walk(sd):
            for f in fs:
                fpath = Path(root) / f
                rel_path = str(fpath.relative_to(exp_dir)).replace("\\", "/")
                st = fpath.stat()
                ftype = categorize_file(f)
                mime, _ = mimetypes.guess_type(str(fpath))
                
                sub_size += st.st_size
                total_size += st.st_size
                
                file_record = {
                    "relative_path": rel_path,
                    "file_name": f,
                    "file_type": ftype,
                    "mime_type": mime or "application/octet-stream",
                    "size_bytes": st.st_size,
                    "last_modified": datetime.fromtimestamp(st.st_mtime).isoformat()
                }
                sub_files.append(file_record)
                files_list.append(file_record)
                
                # Check specifics
                if ftype == "grainraw":
                    has_grainraw = True
                elif ftype == "piv_npz":
                    has_piv = True
                elif ftype == "video":
                    has_videos = True
                elif ftype == "report_pptx":
                    has_reports = True
                
                # Cover image candidate
                if not cover_image_rel and ftype == "image":
                    if "1.2" in rel_path or "1.1" in rel_path or "CO" in rel_path:
                        cover_image_rel = rel_path
        
        sub_info["file_count"] = len(sub_files)
        sub_info["size_bytes"] = sub_size
        categories.append(sub_info)
        
        # Count map frames
        if sub_info["prefix_code"] in ["1.1", "1.x"] and not map_frames_count:
            img_count = sum(1 for sf in sub_files if sf["file_type"] == "image")
            if img_count > map_frames_count:
                map_frames_count = img_count
                
        if sub_info["prefix_code"] in ["4a.1", "4a.x", "4b.1", "4b.x"]:
            has_slices = True
            
        # Check QPIV logs for shortening %
        if sd.name.upper() == "OUTPUT":
            qpiv_dir = sd / "QPIV"
            if qpiv_dir.exists():
                for qf in qpiv_dir.glob("*"):
                    if qf.is_file() and qf.suffix.lower() in [".txt", ".csv", ".json", ".log"]:
                        try:
                            txt = qf.read_text(errors="ignore")
                            # Look for strain/shortening patterns like "Shortening: 14.8%" or "Strain: 14.8"
                            m_strain = re.search(r"(?:shortening|strain|total_strain)\s*[:=]?\s*([\d\.]+)\s*%?", txt, re.I)
                            if m_strain:
                                shortening_pct = float(m_strain.group(1))
                        except Exception:
                            pass

    # Audit taxonomy compliance
    has_map_view = any(c["prefix_code"] in ["1.1", "1.x"] for c in categories)
    has_output = any(c["prefix_code"] == "OUTPUT" for c in categories)
    
    if not has_map_view:
        missing_elements.append("Map View (1.x)")
    if not has_output:
        missing_elements.append("OUTPUT/")
        
    is_compliant = is_naming_valid and has_map_view and has_output and (len(warnings) == 0)

    return {
        "folder_name": folder_name,
        "project": project,
        "exp_date": exp_date,
        "exp_number": exp_number,
        "total_shortening_pct": shortening_pct,
        "total_frames": map_frames_count,
        "total_files": len(files_list),
        "total_size_bytes": total_size,
        "total_size_formatted": format_bytes(total_size),
        "has_grainraw": 1 if has_grainraw else 0,
        "has_piv": 1 if has_piv else 0,
        "has_videos": 1 if has_videos else 0,
        "has_slices": 1 if has_slices else 0,
        "has_reports": 1 if has_reports else 0,
        "cover_image_path": cover_image_rel,
        "taxonomy_compliant": 1 if is_compliant else 0,
        "categories": categories,
        "files": files_list,
        "audit": {
            "is_compliant": is_compliant,
            "missing_elements": missing_elements,
            "warnings": warnings
        }
    }


def index_all_experiments(storage_dir: Path, manifest_dir: Path, dry_run: bool = False) -> Dict[str, Any]:
    storage_dir.mkdir(parents=True, exist_ok=True)
    manifest_dir.mkdir(parents=True, exist_ok=True)
    
    db_path = manifest_dir / "catalog.db"
    manifest_json_path = manifest_dir / "manifest.json"
    audit_json_path = manifest_dir / "audit_report.json"
    
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()
    cursor.executescript(DB_SCHEMA)
    
    started_at = datetime.now().isoformat()
    cursor.execute("INSERT INTO sync_logs (status, notes) VALUES ('RUNNING', 'Starting scan...');")
    log_id = cursor.lastrowid
    conn.commit()
    
    exp_folders = [d for d in storage_dir.iterdir() if d.is_dir()]
    results = []
    total_files_all = 0
    
    for exp_dir in exp_folders:
        exp_data = scan_single_experiment(exp_dir)
        results.append(exp_data)
        total_files_all += exp_data["total_files"]
        
        if not dry_run:
            # Upsert into experiments
            cursor.execute("""
                INSERT INTO experiments (
                    folder_name, project, exp_date, exp_number,
                    total_shortening_pct, total_frames, total_files, total_size_bytes,
                    has_grainraw, has_piv, has_videos, has_slices, has_reports,
                    cover_image_path, taxonomy_compliant, last_indexed_at
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(folder_name) DO UPDATE SET
                    project=excluded.project,
                    exp_date=excluded.exp_date,
                    exp_number=excluded.exp_number,
                    total_shortening_pct=excluded.total_shortening_pct,
                    total_frames=excluded.total_frames,
                    total_files=excluded.total_files,
                    total_size_bytes=excluded.total_size_bytes,
                    has_grainraw=excluded.has_grainraw,
                    has_piv=excluded.has_piv,
                    has_videos=excluded.has_videos,
                    has_slices=excluded.has_slices,
                    has_reports=excluded.has_reports,
                    cover_image_path=excluded.cover_image_path,
                    taxonomy_compliant=excluded.taxonomy_compliant,
                    last_indexed_at=CURRENT_TIMESTAMP;
            """, (
                exp_data["folder_name"], exp_data["project"], exp_data["exp_date"], exp_data["exp_number"],
                exp_data["total_shortening_pct"], exp_data["total_frames"], exp_data["total_files"], exp_data["total_size_bytes"],
                exp_data["has_grainraw"], exp_data["has_piv"], exp_data["has_videos"], exp_data["has_slices"], exp_data["has_reports"],
                exp_data["cover_image_path"], exp_data["taxonomy_compliant"]
            ))
            exp_id = cursor.lastrowid or cursor.execute("SELECT id FROM experiments WHERE folder_name = ?", (exp_data["folder_name"],)).fetchone()[0]
            
            # Refresh categories
            cursor.execute("DELETE FROM categories WHERE experiment_id = ?", (exp_id,))
            for cat in exp_data["categories"]:
                cursor.execute("""
                    INSERT INTO categories (
                        experiment_id, prefix_code, category_name, subfolder_name,
                        width_px, height_px, tag, file_count, size_bytes
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    exp_id, cat["prefix_code"], cat["category_name"], cat["subfolder_name"],
                    cat["width_px"], cat["height_px"], cat["tag"], cat["file_count"], cat["size_bytes"]
                ))
                
            # Refresh files (sample first 1000 or essential files to keep DB fast and compact)
            cursor.execute("DELETE FROM files WHERE experiment_id = ?", (exp_id,))
            for f in exp_data["files"]:
                cursor.execute("""
                    INSERT INTO files (
                        experiment_id, relative_path, file_name, file_type,
                        mime_type, size_bytes, last_modified
                    ) VALUES (?, ?, ?, ?, ?, ?, ?);
                """, (
                    exp_id, f["relative_path"], f["file_name"], f["file_type"],
                    f["mime_type"], f["size_bytes"], f["last_modified"]
                ))
                
    finished_at = datetime.now().isoformat()
    
    # Save master manifest.json
    manifest_payload = {
        "system": "GRAIN Explorer Central Manifest",
        "version": "2.0",
        "generated_at": finished_at,
        "storage_root": str(storage_dir),
        "total_experiments": len(results),
        "total_files": total_files_all,
        "experiments": [
            {
                "folder_name": r["folder_name"],
                "project": r["project"],
                "exp_date": r["exp_date"],
                "exp_number": r["exp_number"],
                "total_shortening_pct": r["total_shortening_pct"],
                "total_frames": r["total_frames"],
                "total_files": r["total_files"],
                "total_size_bytes": r["total_size_bytes"],
                "total_size_formatted": r["total_size_formatted"],
                "has_grainraw": bool(r["has_grainraw"]),
                "has_piv": bool(r["has_piv"]),
                "has_videos": bool(r["has_videos"]),
                "has_slices": bool(r["has_slices"]),
                "has_reports": bool(r["has_reports"]),
                "cover_image_path": r["cover_image_path"],
                "taxonomy_compliant": bool(r["taxonomy_compliant"]),
                "categories": r["categories"]
            }
            for r in results
        ]
    }
    
    if not dry_run:
        manifest_json_path.write_text(json.dumps(manifest_payload, indent=2), encoding="utf-8")
        
        # Save audit report
        audit_payload = {
            "audited_at": finished_at,
            "storage_root": str(storage_dir),
            "compliant_count": sum(1 for r in results if r["taxonomy_compliant"]),
            "non_compliant_count": sum(1 for r in results if not r["taxonomy_compliant"]),
            "details": [
                {
                    "folder_name": r["folder_name"],
                    "is_compliant": bool(r["taxonomy_compliant"]),
                    "missing_elements": r["audit"]["missing_elements"],
                    "warnings": r["audit"]["warnings"]
                }
                for r in results
            ]
        }
        audit_json_path.write_text(json.dumps(audit_payload, indent=2), encoding="utf-8")
        
        # Update log
        cursor.execute("""
            UPDATE sync_logs
            SET status = 'COMPLETED',
                finished_at = ?,
                experiments_count = ?,
                files_count = ?,
                notes = 'Cataloguing sync successfully completed.'
            WHERE id = ?;
        """, (finished_at, len(results), total_files_all, log_id))
        conn.commit()
        
    conn.close()
    
    return {
        "status": "success",
        "experiments_indexed": len(results),
        "total_files": total_files_all,
        "manifest_path": str(manifest_json_path),
        "database_path": str(db_path)
    }


def main():
    parser = argparse.ArgumentParser(description="GRAIN Explorer Catalog Indexer")
    parser.add_argument("--storage-dir", "-s", default=str(DEFAULT_STORAGE_DIR), help="Path to 0010 experiment storage")
    parser.add_argument("--manifest-dir", "-m", default=str(DEFAULT_MANIFEST_DIR), help="Path to 0000 backend manifest")
    parser.add_argument("--dry-run", action="store_true", help="Perform scan without writing to DB/manifest")
    args = parser.parse_args()
    
    print(f"=== GRAIN Explorer Catalog Indexer ===")
    print(f"Storage Dir  : {args.storage_dir}")
    print(f"Manifest Dir : {args.manifest_dir}")
    
    res = index_all_experiments(Path(args.storage_dir), Path(args.manifest_dir), dry_run=args.dry_run)
    print(f"\n[SUCCESS] Sync completed!")
    print(f"- Total Experiments Indexed: {res['experiments_indexed']}")
    print(f"- Total Files Scanned      : {res['total_files']}")
    print(f"- Manifest JSON Location   : {res['manifest_path']}")
    print(f"- SQLite Database Location : {res['database_path']}")


if __name__ == "__main__":
    main()
