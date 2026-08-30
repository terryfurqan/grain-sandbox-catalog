from pydantic import BaseModel
from typing import List, Optional

class FileItem(BaseModel):
    id: int
    file_id: str
    parent_folder_id: str
    experiment_folder_id: Optional[str] = None
    name: str
    mime_type: str
    file_type: str
    size_bytes: int
    size_formatted: str
    relative_path: str
    md5_checksum: Optional[str] = None
    thumbnail_link: Optional[str] = None
    web_view_link: Optional[str] = None
    last_modified: Optional[str] = None
    is_folder: bool

class ExperimentCard(BaseModel):
    id: int
    folder_id: str
    name: str
    description: str
    video_count: int
    photo_count: int
    other_count: int
    total_size_bytes: int
    total_size_formatted: str
    cover_file_id: Optional[str] = None
    last_modified: Optional[str] = None

class FolderTreeNode(BaseModel):
    folder_id: str
    name: str
    relative_path: str
    files_count: int
    subfolders: List['FolderTreeNode'] = []

class SyncRequest(BaseModel):
    admin_pin: str

class SyncStatusResponse(BaseModel):
    is_syncing: bool
    status: str
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    total_files_scanned: int
    total_experiments_found: int
    message: Optional[str] = None

class SetupConfigRequest(BaseModel):
    root_folder_id: str
    admin_pin: str
    portal_title: Optional[str] = None
    portal_subtitle: Optional[str] = None
