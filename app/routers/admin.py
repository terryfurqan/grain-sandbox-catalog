from fastapi import APIRouter, HTTPException, UploadFile, File, Form
from pathlib import Path
import json
import os
from app.config import settings, BASE_DIR
from app.gdrive import gdrive_client
from app.models import SetupConfigRequest

router = APIRouter(prefix="/api/admin", tags=["Admin & Setup"])

@router.get("/status")
def get_admin_status():
    sa_valid, sa_email_or_err = settings.is_service_account_valid()
    conn_ok, conn_msg, folder_data = (False, "", {})
    if sa_valid and settings.GDRIVE_ROOT_FOLDER_ID.strip():
        conn_ok, conn_msg, folder_data = gdrive_client.test_connection()

    return {
        "is_configured": settings.is_configured(),
        "service_account_valid": sa_valid,
        "service_account_email": sa_email_or_err if sa_valid else None,
        "service_account_error": sa_email_or_err if not sa_valid else None,
        "credentials_file_name": settings.credentials_path.name,
        "root_folder_id": settings.GDRIVE_ROOT_FOLDER_ID,
        "portal_title": settings.PORTAL_TITLE,
        "portal_subtitle": settings.PORTAL_SUBTITLE,
        "connection_ok": conn_ok,
        "connection_message": conn_msg,
        "root_folder_name": folder_data.get("name") if conn_ok else None
    }

@router.post("/upload-credentials")
async def upload_credentials(file: UploadFile = File(...)):
    try:
        content = await file.read()
        data = json.loads(content.decode("utf-8"))
        if data.get("type") != "service_account":
            raise HTTPException(status_code=400, detail="File JSON bukan merupakan Google Cloud Service Account yang valid.")
        
        target_path = BASE_DIR / "credentials.json"
        with open(target_path, "wb") as f:
            f.write(content)

        # Reset client credentials cache
        gdrive_client._creds = None
        gdrive_client._service = None

        return {
            "status": "success",
            "message": "File credentials.json berhasil diunggah!",
            "client_email": data.get("client_email")
        }
    except HTTPException:
        raise
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="File yang diunggah bukan format JSON yang valid.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal menyimpan credentials: {str(e)}")

@router.post("/save-config")
def save_config(req: SetupConfigRequest):
    if req.admin_pin != settings.ADMIN_PIN and settings.ADMIN_PIN != "123456":
        # Allow default pin on first setup
        raise HTTPException(status_code=401, detail="PIN Admin salah!")

    env_path = BASE_DIR / ".env"
    
    # Read existing env or build new
    env_content = f"""# GRAIN Sandbox Experiment Server Config
SERVER_HOST={settings.SERVER_HOST}
SERVER_PORT={settings.SERVER_PORT}
GDRIVE_SERVICE_ACCOUNT_JSON=credentials.json
GDRIVE_ROOT_FOLDER_ID={req.root_folder_id.strip()}
ADMIN_PIN={req.admin_pin.strip()}
PORTAL_TITLE="{req.portal_title or settings.PORTAL_TITLE}"
PORTAL_SUBTITLE="{req.portal_subtitle or settings.PORTAL_SUBTITLE}"
"""
    with open(env_path, "w", encoding="utf-8") as f:
        f.write(env_content)

    # Update runtime settings
    settings.GDRIVE_ROOT_FOLDER_ID = req.root_folder_id.strip()
    settings.ADMIN_PIN = req.admin_pin.strip()
    if req.portal_title:
        settings.PORTAL_TITLE = req.portal_title
    if req.portal_subtitle:
        settings.PORTAL_SUBTITLE = req.portal_subtitle

    # Reset client
    gdrive_client._creds = None
    gdrive_client._service = None

    return {
        "status": "success",
        "message": "Konfigurasi berhasil disimpan!",
        "is_configured": settings.is_configured()
    }

@router.get("/test-connection")
def test_connection():
    conn_ok, conn_msg, folder_data = gdrive_client.test_connection()
    return {
        "connection_ok": conn_ok,
        "message": conn_msg,
        "folder": folder_data
    }
