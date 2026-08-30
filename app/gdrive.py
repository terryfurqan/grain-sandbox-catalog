import json
import logging
from typing import Generator, AsyncGenerator, Dict, Any, List, Optional, Tuple
from google.oauth2 import service_account
import google.auth.transport.requests
from googleapiclient.discovery import build
import httpx
from app.config import settings
from app.database import get_db, categorize_file

logger = logging.getLogger("gdrive")
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]

class GDriveClient:
    def __init__(self):
        self._creds: Optional[service_account.Credentials] = None
        self._service = None

    def get_credentials(self) -> Optional[service_account.Credentials]:
        valid, _, sa_dict = settings.get_service_account_dict()
        if not valid:
            return None
        if self._creds is None:
            self._creds = service_account.Credentials.from_service_account_info(
                sa_dict,
                scopes=SCOPES
            )
        return self._creds

    def get_access_token(self) -> str:
        creds = self.get_credentials()
        if creds is None:
            raise ValueError("Credentials Service Account belum valid atau belum disetup.")
        if not creds.valid:
            req = google.auth.transport.requests.Request()
            creds.refresh(req)
        return creds.token

    def get_service(self):
        if self._service is None:
            creds = self.get_credentials()
            if creds is None:
                raise ValueError("Credentials Service Account tidak valid.")
            self._service = build("drive", "v3", credentials=creds, cache_discovery=False)
        return self._service

    def test_connection(self) -> Tuple[bool, str, Dict[str, Any]]:
        try:
            service = self.get_service()
            root_id = settings.GDRIVE_ROOT_FOLDER_ID.strip()
            if not root_id:
                return False, "GDRIVE_ROOT_FOLDER_ID belum diisi di konfigurasi.", {}
            
            folder = service.files().get(
                fileId=root_id,
                fields="id, name, mimeType, webViewLink",
                supportsAllDrives=True
            ).execute()
            
            return True, f"Koneksi sukses! Folder Root: {folder.get('name', root_id)}", folder
        except Exception as e:
            return False, f"Gagal terhubung ke Google Drive: {str(e)}", {}

    def scan_and_index_all(self, progress_callback=None) -> Dict[str, Any]:
        """
        Men-scan seluruh hirarki folder dari Root Folder ID ke SQLite database.
        Folder level 1 dianggap sebagai 'Experiments'.
        """
        service = self.get_service()
        root_id = settings.GDRIVE_ROOT_FOLDER_ID.strip()
        if not root_id:
            raise ValueError("Root Folder ID belum diset.")

        # Queue untuk traversal BFS: [(folder_id, parent_id, experiment_id, relative_path, level)]
        queue = [(root_id, "", "", "", 0)]
        
        all_experiments: Dict[str, Dict[str, Any]] = {}
        all_files: List[Dict[str, Any]] = []

        total_scanned = 0

        while queue:
            curr_folder_id, parent_id, exp_id, curr_path, level = queue.pop(0)
            
            # List items di dalam curr_folder_id
            page_token = None
            while True:
                query = f"'{curr_folder_id}' in parents and trashed = false"
                response = service.files().list(
                    q=query,
                    spaces='drive',
                    fields='nextPageToken, files(id, name, mimeType, size, md5Checksum, thumbnailLink, webViewLink, modifiedTime)',
                    pageToken=page_token,
                    pageSize=500,
                    supportsAllDrives=True,
                    includeItemsFromAllDrives=True
                ).execute()

                items = response.get('files', [])
                for item in items:
                    f_id = item['id']
                    f_name = item['name']
                    mime_type = item.get('mimeType', '')
                    is_dir = (mime_type == 'application/vnd.google-apps.folder')
                    f_size = int(item.get('size', 0)) if not is_dir else 0
                    f_type = categorize_file(mime_type, f_name)
                    item_rel_path = f"{curr_path}/{f_name}".strip("/") if curr_path else f_name

                    # Jika di Level 0 (langsung anak dari Root), dan merupakan folder => Ini adalah EXPERIMENT
                    if level == 0 and is_dir:
                        this_exp_id = f_id
                        all_experiments[f_id] = {
                            "folder_id": f_id,
                            "name": f_name,
                            "description": f"Experiment: {f_name}",
                            "video_count": 0,
                            "photo_count": 0,
                            "other_count": 0,
                            "total_size_bytes": 0,
                            "cover_file_id": None,
                            "last_modified": item.get('modifiedTime')
                        }
                    else:
                        this_exp_id = exp_id

                    # Catat metadata file/folder
                    file_record = {
                        "file_id": f_id,
                        "parent_folder_id": curr_folder_id,
                        "experiment_folder_id": this_exp_id,
                        "name": f_name,
                        "mime_type": mime_type,
                        "file_type": f_type,
                        "size_bytes": f_size,
                        "relative_path": item_rel_path,
                        "md5_checksum": item.get('md5Checksum'),
                        "thumbnail_link": item.get('thumbnailLink'),
                        "web_view_link": item.get('webViewLink'),
                        "last_modified": item.get('modifiedTime'),
                        "is_folder": 1 if is_dir else 0
                    }
                    all_files.append(file_record)
                    total_scanned += 1

                    # Update counter eksperimen jika berasosiasi
                    if this_exp_id and this_exp_id in all_experiments:
                        exp = all_experiments[this_exp_id]
                        exp["total_size_bytes"] += f_size
                        if f_type == "video":
                            exp["video_count"] += 1
                        elif f_type == "image":
                            exp["photo_count"] += 1
                            if not exp["cover_file_id"]:
                                exp["cover_file_id"] = f_id
                        elif not is_dir:
                            exp["other_count"] += 1

                    if is_dir:
                        queue.append((f_id, curr_folder_id, this_exp_id, item_rel_path, level + 1))

                page_token = response.get('nextPageToken')
                if not page_token:
                    break

            if progress_callback:
                progress_callback(total_scanned)

        # Simpan hasil scan ke database SQLite
        with get_db() as conn:
            cursor = conn.cursor()
            # Bersihkan index lama
            cursor.execute("DELETE FROM experiments;")
            cursor.execute("DELETE FROM files;")

            for exp in all_experiments.values():
                cursor.execute("""
                INSERT INTO experiments (folder_id, name, description, video_count, photo_count, other_count, total_size_bytes, cover_file_id, last_modified)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    exp["folder_id"], exp["name"], exp["description"],
                    exp["video_count"], exp["photo_count"], exp["other_count"],
                    exp["total_size_bytes"], exp["cover_file_id"], exp["last_modified"]
                ))

            for f in all_files:
                cursor.execute("""
                INSERT INTO files (file_id, parent_folder_id, experiment_folder_id, name, mime_type, file_type, size_bytes, relative_path, md5_checksum, thumbnail_link, web_view_link, last_modified, is_folder)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                """, (
                    f["file_id"], f["parent_folder_id"], f["experiment_folder_id"],
                    f["name"], f["mime_type"], f["file_type"], f["size_bytes"],
                    f["relative_path"], f["md5_checksum"], f["thumbnail_link"],
                    f["web_view_link"], f["last_modified"], f["is_folder"]
                ))

        return {
            "total_files": total_scanned,
            "total_experiments": len(all_experiments)
        }

    def get_file_metadata(self, file_id: str) -> Dict[str, Any]:
        # Cek dari local db dulu
        with get_db() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM files WHERE file_id = ?;", (file_id,))
            row = cursor.fetchone()
            if row:
                return row
        
        # Fallback ke Google Drive API langsung jika belum ada di database
        service = self.get_service()
        item = service.files().get(
            fileId=file_id,
            fields="id, name, mimeType, size, md5Checksum, thumbnailLink, webViewLink, modifiedTime",
            supportsAllDrives=True
        ).execute()
        return {
            "file_id": item["id"],
            "name": item["name"],
            "mime_type": item.get("mimeType", "application/octet-stream"),
            "size_bytes": int(item.get("size", 0)),
            "thumbnail_link": item.get("thumbnailLink"),
            "web_view_link": item.get("webViewLink"),
            "last_modified": item.get("modifiedTime")
        }

gdrive_client = GDriveClient()
