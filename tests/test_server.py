"""
Test Suite untuk Web Server GRAIN Sandbox Data Catalog
Menguji Database SQLite, Helper Utilities, FastAPI Routes, Admin Endpoints, dan Video Streaming Proxy.
"""

import io
import os
import sys
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock, AsyncMock

import httpx
from fastapi.testclient import TestClient

# Pastikan root workspace berada di sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import settings, Settings
from app.database import get_db, init_db, format_file_size, categorize_file
from app.auth import create_session_token
from app.main import app


class TestDatabaseAndHelpers(unittest.TestCase):
    """Pengujian inisialisasi SQLite database dan fungsi helper utilitas."""

    def setUp(self):
        # Buat temporary sqlite database untuk isolasi pengujian
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = Path(self.temp_dir.name) / "test_catalog.db"
        self.original_db_path = settings.DATABASE_PATH
        settings.DATABASE_PATH = str(self.db_path)

    def tearDown(self):
        settings.DATABASE_PATH = self.original_db_path
        self.temp_dir.cleanup()

    def test_init_db_creates_all_tables_and_indices(self):
        """Memastikan init_db() membuat tabel experiments, files, sync_logs, dan system_metadata beserta indeksnya."""
        init_db()

        self.assertTrue(self.db_path.exists(), "File database SQLite harus dibuat.")

        with get_db() as conn:
            cursor = conn.cursor()
            
            # Periksa tabel yang terbentuk
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = {row["name"] for row in cursor.fetchall()}
            
            expected_tables = {"experiments", "files", "sync_logs", "system_metadata"}
            self.assertTrue(
                expected_tables.issubset(tables),
                f"Tabel {expected_tables} harus ada di database. Ditemukan: {tables}"
            )

            # Periksa kolom tabel experiments
            cursor.execute("PRAGMA table_info(experiments);")
            exp_cols = {row["name"] for row in cursor.fetchall()}
            for col in ["id", "folder_id", "name", "description", "video_count", "photo_count", "total_size_bytes"]:
                self.assertIn(col, exp_cols, f"Kolom {col} harus ada di tabel experiments.")

            # Periksa kolom tabel files
            cursor.execute("PRAGMA table_info(files);")
            files_cols = {row["name"] for row in cursor.fetchall()}
            for col in ["id", "file_id", "parent_folder_id", "experiment_folder_id", "name", "mime_type", "file_type", "size_bytes"]:
                self.assertIn(col, files_cols, f"Kolom {col} harus ada di tabel files.")

            # Periksa kolom tabel sync_logs
            cursor.execute("PRAGMA table_info(sync_logs);")
            logs_cols = {row["name"] for row in cursor.fetchall()}
            for col in ["id", "status", "started_at", "finished_at", "total_files_scanned", "total_experiments_found"]:
                self.assertIn(col, logs_cols, f"Kolom {col} harus ada di tabel sync_logs.")

            # Periksa index
            cursor.execute("SELECT name FROM sqlite_master WHERE type='index';")
            indices = {row["name"] for row in cursor.fetchall()}
            self.assertIn("idx_files_parent", indices)
            self.assertIn("idx_files_exp", indices)
            self.assertIn("idx_files_type", indices)

    def test_format_file_size(self):
        """Memastikan format_file_size memformat ukuran byte menjadi string human-readable dengan presisi benar."""
        self.assertEqual(format_file_size(0), "0 B")
        self.assertEqual(format_file_size(500), "500.00 B")
        self.assertEqual(format_file_size(1024), "1.00 KB")
        self.assertEqual(format_file_size(1536), "1.50 KB")
        self.assertEqual(format_file_size(1024 * 1024), "1.00 MB")
        self.assertEqual(format_file_size(1024 * 1024 * 1024), "1.00 GB")
        self.assertEqual(format_file_size(1024 * 1024 * 1024 * 1024), "1.00 TB")

    def test_categorize_file(self):
        """Memastikan categorize_file mengklasifikasikan MIME type dan ekstensi file dengan akurat."""
        # Folder
        self.assertEqual(categorize_file("application/vnd.google-apps.folder", "Exp 01"), "folder")

        # Video
        self.assertEqual(categorize_file("video/mp4", "exp_timelapse.mp4"), "video")
        self.assertEqual(categorize_file("application/octet-stream", "exp_piv.mov"), "video")
        self.assertEqual(categorize_file("video/x-matroska", "record.mkv"), "video")
        self.assertEqual(categorize_file("application/octet-stream", "output.avi"), "video")
        self.assertEqual(categorize_file("video/webm", "preview.webm"), "video")

        # Image / Foto
        self.assertEqual(categorize_file("image/jpeg", "slice_co_01.jpg"), "image")
        self.assertEqual(categorize_file("image/png", "chart.png"), "image")
        self.assertEqual(categorize_file("image/tiff", "highres.tif"), "image")
        self.assertEqual(categorize_file("application/octet-stream", "slice.tiff"), "image")
        self.assertEqual(categorize_file("image/webp", "thumb.webp"), "image")

        # Dokumen
        self.assertEqual(categorize_file("application/pdf", "laporan_sbx.pdf"), "document")
        self.assertEqual(categorize_file("application/vnd.openxmlformats-officedocument.presentationml.presentation", "evolution.pptx"), "document")
        self.assertEqual(categorize_file("text/plain", "manifest.txt"), "document")
        self.assertEqual(categorize_file("text/csv", "strain_profile.csv"), "document")
        self.assertEqual(categorize_file("application/json", "meta.json"), "document")

        # Arsip & Kontainer GRAIN
        self.assertEqual(categorize_file("application/zip", "backup.zip"), "archive")
        self.assertEqual(categorize_file("application/octet-stream", "dataset.grainraw"), "archive")
        self.assertEqual(categorize_file("application/octet-stream", "vectors_pass3.npz"), "archive")
        self.assertEqual(categorize_file("application/x-tar", "data.tar"), "archive")
        self.assertEqual(categorize_file("application/x-7z-compressed", "data.7z"), "archive")

        # Other / Unknown
        self.assertEqual(categorize_file("application/octet-stream", "raw_firmware.bin"), "other")
        self.assertEqual(categorize_file("unknown/format", "unknown_file.xyz"), "other")


class TestFastAPIRoutes(unittest.TestCase):
    """Pengujian semua endpoint REST API dan HTML Views FastAPI."""

    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.TemporaryDirectory()
        cls.db_path = Path(cls.temp_dir.name) / "test_api_catalog.db"
        cls.original_db_path = settings.DATABASE_PATH
        settings.DATABASE_PATH = str(cls.db_path)
        
        # Inisialisasi DB dan seed dummy data
        init_db()
        cls.seed_dummy_data()

    @classmethod
    def tearDownClass(cls):
        settings.DATABASE_PATH = cls.original_db_path
        cls.temp_dir.cleanup()

    @classmethod
    def seed_dummy_data(cls):
        """Memasukkan data eksperimen dan file dummy untuk pengujian endpoint."""
        with get_db() as conn:
            cursor = conn.cursor()
            
            # Insert Experiment 1
            cursor.execute("""
                INSERT INTO experiments (folder_id, name, description, video_count, photo_count, other_count, total_size_bytes, cover_file_id)
                VALUES ('exp_folder_01', 'EXP-01 Tectonic Sandbox', 'Simulasi pemendekan kerak bumi', 2, 5, 1, 10485760, 'cover_01');
            """)

            # Insert Experiment 2
            cursor.execute("""
                INSERT INTO experiments (folder_id, name, description, video_count, photo_count, other_count, total_size_bytes, cover_file_id)
                VALUES ('exp_folder_02', 'EXP-02 Strike-Slip Basin', 'Model sesar geser analog', 1, 3, 0, 5242880, 'cover_02');
            """)

            # Insert Files for EXP-01
            cursor.execute("""
                INSERT INTO files (file_id, parent_folder_id, experiment_folder_id, name, mime_type, file_type, size_bytes, relative_path, is_folder)
                VALUES 
                ('vid_01', 'exp_folder_01', 'exp_folder_01', 'EXP01_velmag.mp4', 'video/mp4', 'video', 5242880, 'EXP-01/EXP01_velmag.mp4', 0),
                ('vid_02', 'exp_folder_01', 'exp_folder_01', 'EXP01_shearstrain.mp4', 'video/mp4', 'video', 3145728, 'EXP-01/EXP01_shearstrain.mp4', 0),
                ('img_01', 'exp_folder_01', 'exp_folder_01', 'slice_01.jpg', 'image/jpeg', 'image', 1048576, 'EXP-01/SLICES/slice_01.jpg', 0),
                ('doc_01', 'exp_folder_01', 'exp_folder_01', 'report.pdf', 'application/pdf', 'document', 524288, 'EXP-01/REPORTS/report.pdf', 0),
                ('sub_folder_01', 'exp_folder_01', 'exp_folder_01', 'SLICES', 'application/vnd.google-apps.folder', 'folder', 0, 'EXP-01/SLICES', 1);
            """)

            # Insert Root level items
            cursor.execute("""
                INSERT INTO files (file_id, parent_folder_id, experiment_folder_id, name, mime_type, file_type, size_bytes, relative_path, is_folder)
                VALUES 
                ('exp_folder_01', 'root_folder_id_test', 'exp_folder_01', 'EXP-01 Tectonic Sandbox', 'application/vnd.google-apps.folder', 'folder', 0, 'EXP-01', 1),
                ('exp_folder_02', 'root_folder_id_test', 'exp_folder_02', 'EXP-02 Strike-Slip Basin', 'application/vnd.google-apps.folder', 'folder', 0, 'EXP-02', 1);
            """)

            # Insert Sync Log
            cursor.execute("""
                INSERT INTO sync_logs (status, started_at, finished_at, total_files_scanned, total_experiments_found, message)
                VALUES ('COMPLETED', '2026-08-30 06:00:00', '2026-08-30 06:01:00', 7, 2, 'Sinkronisasi berhasil diselesaikan.');
            """)

    def setUp(self):
        self.client = TestClient(app)
        token = create_session_token(settings.ADMIN_USERNAME)
        self.client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    def test_get_root_redirects_when_not_configured(self):
        """GET / harus me-redirect ke /setup jika server belum dikonfigurasi."""
        with patch.object(Settings, "is_configured", return_value=False):
            res = self.client.get("/", follow_redirects=False)
            self.assertIn(res.status_code, [302, 307], "Harus redirect jika belum dikonfigurasi.")
            self.assertEqual(res.headers.get("location"), "/setup")

    def test_get_root_returns_200_html_when_configured(self):
        """GET / harus mengembalikan status 200 OK HTML jika server sudah dikonfigurasi."""
        with patch.object(Settings, "is_configured", return_value=True):
            res = self.client.get("/")
            self.assertEqual(res.status_code, 200)
            self.assertIn("text/html", res.headers.get("content-type", ""))
            self.assertIn(settings.PORTAL_TITLE, res.text)

    def test_get_setup_page(self):
        """GET /setup harus mengembalikan status 200 OK HTML halaman konfigurasi."""
        res = self.client.get("/setup")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers.get("content-type", ""))
        self.assertIn("Setup", res.text)

    def test_get_api_stats(self):
        """GET /api/stats harus mengembalikan statistik katalog dengan benar."""
        res = self.client.get("/api/stats")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        self.assertIn("total_experiments", data)
        self.assertIn("total_videos", data)
        self.assertIn("total_photos", data)
        self.assertIn("total_files", data)
        self.assertIn("total_size_bytes", data)
        self.assertIn("total_size_formatted", data)
        self.assertIn("last_sync", data)

        self.assertEqual(data["total_experiments"], 2)
        self.assertEqual(data["total_videos"], 2)
        self.assertEqual(data["total_photos"], 1)
        self.assertEqual(data["total_files"], 4)  # 4 non-folder files
        self.assertIsNotNone(data["last_sync"])
        self.assertEqual(data["last_sync"]["status"], "COMPLETED")

    def test_get_api_experiments(self):
        """GET /api/experiments harus mengembalikan daftar semua eksperimen dalam format JSON array."""
        res = self.client.get("/api/experiments")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 2)
        
        # Periksa field eksperimen pertama
        exp1 = data[0]
        self.assertEqual(exp1["folder_id"], "exp_folder_01")
        self.assertEqual(exp1["name"], "EXP-01 Tectonic Sandbox")
        self.assertIn("total_size_formatted", exp1)

    def test_get_api_experiment_detail_success_and_not_found(self):
        """GET /api/experiments/{folder_id} mengembalikan detail eksperimen dan file atau 404 jika tidak ada."""
        # Success case
        res = self.client.get("/api/experiments/exp_folder_01")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("experiment", data)
        self.assertIn("files", data)
        self.assertEqual(data["experiment"]["folder_id"], "exp_folder_01")
        self.assertEqual(len(data["files"]), 4)  # 4 non-folder files

        # 404 Not Found case
        res_404 = self.client.get("/api/experiments/non_existent_folder_id")
        self.assertEqual(res_404.status_code, 404)
        self.assertIn("detail", res_404.json())

    def test_get_api_folders_root_items(self):
        """GET /api/folders/root/items harus mengembalikan struktur folder root."""
        with patch.object(settings, "GDRIVE_ROOT_FOLDER_ID", "root_folder_id_test"):
            res = self.client.get("/api/folders/root/items")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            
            self.assertIn("current_folder", data)
            self.assertIn("breadcrumbs", data)
            self.assertIn("items", data)
            self.assertEqual(len(data["items"]), 2)
            self.assertEqual(data["items"][0]["name"], "EXP-01 Tectonic Sandbox")
            self.assertTrue(data["items"][0]["is_folder"])

    def test_get_api_folders_subfolder_items(self):
        """GET /api/folders/{subfolder_id}/items mengembalikan isi subfolder."""
        res = self.client.get("/api/folders/exp_folder_01/items")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("items", data)
        self.assertEqual(len(data["items"]), 5)

    def test_get_api_search(self):
        """GET /api/search?q=test harus mengembalikan hasil pencarian file yang cocok."""
        # Search by keyword 'velmag'
        res = self.client.get("/api/search?q=velmag")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIsInstance(data, list)
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]["file_id"], "vid_01")

        # Search with file_type filter
        res_type = self.client.get("/api/search?q=EXP01&file_type=video")
        self.assertEqual(res_type.status_code, 200)
        data_type = res_type.json()
        self.assertEqual(len(data_type), 2)
        for item in data_type:
            self.assertEqual(item["file_type"], "video")

    def test_get_api_admin_status(self):
        """GET /api/admin/status harus mengembalikan status konfigurasi admin."""
        res = self.client.get("/api/admin/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        
        self.assertIn("is_configured", data)
        self.assertIn("service_account_valid", data)
        self.assertIn("portal_title", data)
        self.assertIn("portal_subtitle", data)
        self.assertIn("connection_ok", data)

    def test_post_api_sync_trigger_invalid_pin(self):
        """POST /api/sync/trigger dengan PIN salah harus mengembalikan status HTTP 401."""
        res = self.client.post("/api/sync/trigger", json={"admin_pin": "wrong_pin_999"})
        self.assertEqual(res.status_code, 401)
        self.assertIn("PIN Admin salah", res.json().get("detail", ""))

    def test_post_api_sync_trigger_not_configured(self):
        """POST /api/sync/trigger dengan PIN benar tapi belum dikonfigurasi harus mengembalikan status HTTP 400."""
        with patch.object(Settings, "is_configured", return_value=False):
            res = self.client.post("/api/sync/trigger", json={"admin_pin": settings.ADMIN_PIN})
            self.assertEqual(res.status_code, 400)
            self.assertIn("Google Drive belum dikonfigurasi", res.json().get("detail", ""))

    def test_get_api_sync_status(self):
        """GET /api/sync/status harus mengembalikan status sinkronisasi aktif dan log terakhir."""
        res = self.client.get("/api/sync/status")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertIn("is_syncing", data)
        self.assertIn("current_scanned", data)
        self.assertIn("last_log", data)

    def test_post_api_admin_save_config(self):
        """POST /api/admin/save-config menyimpan konfigurasi baru dengan validasi PIN."""
        orig_root = settings.GDRIVE_ROOT_FOLDER_ID
        orig_pin = settings.ADMIN_PIN
        orig_title = settings.PORTAL_TITLE
        
        try:
            # Test dengan PIN salah jika ADMIN_PIN bukan default
            with patch.object(settings, "ADMIN_PIN", "secure_pin_777"):
                res_fail = self.client.post("/api/admin/save-config", json={
                    "root_folder_id": "new_root_123",
                    "admin_pin": "wrong_pin",
                    "portal_title": "Test Title"
                })
                self.assertEqual(res_fail.status_code, 401)

            # Test dengan PIN benar
            with patch("builtins.open", unittest.mock.mock_open()):
                res_ok = self.client.post("/api/admin/save-config", json={
                    "root_folder_id": "new_root_123",
                    "admin_pin": settings.ADMIN_PIN,
                    "portal_title": "Custom GRAIN Server"
                })
                self.assertEqual(res_ok.status_code, 200)
                self.assertEqual(res_ok.json().get("status"), "success")
        finally:
            settings.GDRIVE_ROOT_FOLDER_ID = orig_root
            settings.ADMIN_PIN = orig_pin
            settings.PORTAL_TITLE = orig_title

    def test_post_api_admin_upload_credentials_validation(self):
        """POST /api/admin/upload-credentials memvalidasi format JSON dan tipe service account."""
        # 1. Non-JSON file
        res_non_json = self.client.post(
            "/api/admin/upload-credentials",
            files={"file": ("test.txt", io.BytesIO(b"not json content"), "text/plain")}
        )
        self.assertEqual(res_non_json.status_code, 400)

        # 2. JSON bukan service account
        non_sa_json = json.dumps({"type": "user_oauth", "client_id": "123"}).encode("utf-8")
        res_non_sa = self.client.post(
            "/api/admin/upload-credentials",
            files={"file": ("creds.json", io.BytesIO(non_sa_json), "application/json")}
        )
        self.assertEqual(res_non_sa.status_code, 400)
        self.assertIn("bukan merupakan Google Cloud Service Account", res_non_sa.json().get("detail", ""))

    def test_get_api_admin_test_connection(self):
        """GET /api/admin/test-connection mengembalikan hasil uji koneksi ke Google Drive API."""
        with patch("app.routers.admin.gdrive_client.test_connection", return_value=(True, "Koneksi sukses", {"name": "Root Folder"})):
            res = self.client.get("/api/admin/test-connection")
            self.assertEqual(res.status_code, 200)
            data = res.json()
            self.assertTrue(data["connection_ok"])
            self.assertEqual(data["folder"]["name"], "Root Folder")


class TestMockVideoStreamingProxy(unittest.TestCase):
    """Pengujian Mock Streaming Video Proxy dengan HTTP Byte-Range Seeking."""

    def setUp(self):
        self.client = TestClient(app)

    def test_stream_video_with_byte_range_returns_206(self):
        """Memverifikasi bahwa GET /api/stream/video/{file_id} dengan header Range mengembalikan HTTP 206 Partial Content dan Content-Range."""
        mock_token = "mock-gdrive-access-token-xyz"
        mock_content = b"VIDEO_PARTIAL_BYTES_STREAM" * 10  # 260 bytes

        with patch("app.routers.stream.gdrive_client.get_access_token", return_value=mock_token):
            # Definisikan mock async send untuk httpx.AsyncClient
            async def mock_async_send(client_instance, request, *args, **kwargs):
                range_header = request.headers.get("range", "")
                self.assertEqual(range_header, "bytes=0-100", "Header Range harus diteruskan ke Google Drive API.")
                self.assertEqual(request.headers.get("authorization"), f"Bearer {mock_token}")
                
                return httpx.Response(
                    status_code=206,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Range": "bytes 0-100/10485760",
                        "Content-Length": "101",
                        "Accept-Ranges": "bytes"
                    },
                    content=mock_content[:101],
                    request=request
                )

            with patch.object(httpx.AsyncClient, "send", new=mock_async_send):
                response = self.client.get(
                    "/api/stream/video/mock_video_file_001",
                    headers={"Range": "bytes=0-100"}
                )

                self.assertEqual(response.status_code, 206, "Harus mengembalikan HTTP 206 Partial Content.")
                self.assertEqual(response.headers.get("content-range"), "bytes 0-100/10485760")
                self.assertEqual(response.headers.get("accept-ranges"), "bytes")
                self.assertEqual(response.headers.get("content-type"), "video/mp4")
                self.assertEqual(len(response.content), 101)

    def test_stream_video_full_content_returns_200(self):
        """Memverifikasi bahwa request video tanpa header Range mengembalikan HTTP 200 OK."""
        mock_token = "mock-gdrive-access-token-xyz"
        mock_content = b"FULL_VIDEO_FILE_BYTES" * 20

        with patch("app.routers.stream.gdrive_client.get_access_token", return_value=mock_token):
            async def mock_async_send(client_instance, request, *args, **kwargs):
                self.assertNotIn("range", request.headers)
                return httpx.Response(
                    status_code=200,
                    headers={
                        "Content-Type": "video/mp4",
                        "Content-Length": str(len(mock_content)),
                        "Accept-Ranges": "bytes"
                    },
                    content=mock_content,
                    request=request
                )

            with patch.object(httpx.AsyncClient, "send", new=mock_async_send):
                response = self.client.get("/api/stream/video/mock_video_file_002")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers.get("content-type"), "video/mp4")
                self.assertEqual(len(response.content), len(mock_content))

    def test_stream_video_error_handling(self):
        """Memverifikasi error handling jika token GDrive gagal didapatkan."""
        with patch("app.routers.stream.gdrive_client.get_access_token", side_effect=ValueError("Service Account credentials missing")):
            response = self.client.get("/api/stream/video/mock_err_vid")
            self.assertEqual(response.status_code, 500)
            self.assertIn("Gagal mengautentikasi ke Google Drive", response.json().get("detail", ""))

    def test_preview_image_proxy(self):
        """Memverifikasi proxy gambar /api/preview/image/{file_id} mengembalikan gambar dengan benar."""
        mock_image_bytes = b"\xff\xd8\xff\xe0" + b"\x00" * 50  # Simpel JPEG header + bytes

        with patch("app.routers.stream.gdrive_client.get_access_token", return_value="fake-token"):
            async def mock_async_send(client_instance, request, *args, **kwargs):
                return httpx.Response(
                    status_code=200,
                    headers={"Content-Type": "image/jpeg", "Content-Length": str(len(mock_image_bytes))},
                    content=mock_image_bytes,
                    request=request
                )

            with patch.object(httpx.AsyncClient, "send", new=mock_async_send):
                response = self.client.get("/api/preview/image/mock_img_001")
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.headers.get("content-type"), "image/jpeg")
                self.assertEqual(response.content, mock_image_bytes)

    def test_download_file_proxy(self):
        """Memverifikasi proxy download /api/download/{file_id} mengembalikan file attachment."""
        mock_download_bytes = b"DOWNLOADABLE_GRAIN_RAW_CONTAINER_DATA"

        with patch("app.routers.stream.gdrive_client.get_access_token", return_value="fake-token"):
            async def mock_async_send(client_instance, request, *args, **kwargs):
                return httpx.Response(
                    status_code=200,
                    headers={"Content-Type": "application/octet-stream", "Content-Length": str(len(mock_download_bytes))},
                    content=mock_download_bytes,
                    request=request
                )

            with patch.object(httpx.AsyncClient, "send", new=mock_async_send):
                response = self.client.get("/api/download/mock_raw_001?filename=exp01.grainraw")
                self.assertEqual(response.status_code, 200)
                self.assertIn('attachment; filename="exp01.grainraw"', response.headers.get("content-disposition", ""))
                self.assertEqual(response.content, mock_download_bytes)


if __name__ == "__main__":
    unittest.main(verbosity=2)
