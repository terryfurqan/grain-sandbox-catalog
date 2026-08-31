from pathlib import Path
from pydantic import Field, AliasChoices
from pydantic_settings import BaseSettings, SettingsConfigDict
import json
import os

BASE_DIR = Path(__file__).resolve().parent.parent

class Settings(BaseSettings):
    SERVER_HOST: str = "0.0.0.0"
    SERVER_PORT: int = Field(default=8080, validation_alias=AliasChoices("SERVER_PORT", "PORT"))
    GDRIVE_SERVICE_ACCOUNT_JSON: str = "credentials.json"
    GDRIVE_ROOT_FOLDER_ID: str = ""
    ADMIN_PIN: str = "123456"
    PORTAL_TITLE: str = "GRAIN Sandbox Experiment Data Server"
    PORTAL_SUBTITLE: str = "Analog Geological & Tectonic Modeling Video/Photo Catalog"
    GDRIVE_SERVICE_ACCOUNT_RAW_JSON: str = "" # Opsi raw JSON string untuk cloud deployment
    DATABASE_PATH: str = str(BASE_DIR / "catalog.db")

    # FinOps & Cost Defense Settings
    RATE_LIMIT_DEFAULT: str = "120/minute"
    RATE_LIMIT_STREAM: str = "30/minute"
    RATE_LIMIT_DOWNLOAD: str = "10/minute"
    CACHE_MAX_AGE_MEDIA: int = 604800  # 7 days browser cache
    APP_ACCESS_TOKEN: str = ""         # Optional token protection

    # Authentication & Session Security
    ADMIN_USERNAME: str = "terryfurqan"
    ADMIN_PASSWORD: str = "ifasayang123"
    SESSION_SECRET_KEY: str = "grain-sandbox-session-secret-key-terry-2026-auth"
    SESSION_COOKIE_NAME: str = "grain_session"
    SESSION_MAX_AGE: int = 604800      # 7 days session duration
    REQUIRE_AUTH: bool = False         # Lock entire catalog to logged-in users only
    REQUIRE_AUTH_FOR_SETUP: bool = True # Enforce login on setup and admin endpoints
    SECURE_COOKIE: bool = False        # Set True for HTTPS in production

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore"
    )

    @property
    def credentials_path(self) -> Path:
        p = Path(self.GDRIVE_SERVICE_ACCOUNT_JSON)
        if not p.is_absolute():
            p = BASE_DIR / p
        return p

    def get_service_account_dict(self) -> tuple[bool, str, dict]:
        # 1. Cek dari environment variable raw JSON string
        raw_json = self.GDRIVE_SERVICE_ACCOUNT_RAW_JSON.strip()
        if raw_json.startswith("{"):
            try:
                data = json.loads(raw_json)
                if data.get("type") == "service_account" and "client_email" in data and "private_key" in data:
                    return True, data.get("client_email", ""), data
            except Exception as e:
                return False, f"Format raw JSON error: {str(e)}", {}

        # 2. Cek dari file credentials
        path = self.credentials_path
        if not path.exists():
            # Cek fallback di /etc/secrets/credentials.json (Render secrets default)
            secret_path = Path("/etc/secrets/credentials.json")
            if secret_path.exists():
                path = secret_path
            else:
                return False, f"File credentials '{path.name}' tidak ditemukan.", {}

        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if data.get("type") != "service_account":
                return False, "File JSON bukan merupakan Service Account Google Cloud.", {}
            if "client_email" not in data or "private_key" not in data:
                return False, "File credentials JSON tidak memiliki 'client_email' atau 'private_key'.", {}
            return True, data.get("client_email", ""), data
        except Exception as e:
            return False, f"Format JSON error: {str(e)}", {}

    def is_service_account_valid(self) -> tuple[bool, str]:
        valid, info, _ = self.get_service_account_dict()
        return valid, info

    def is_configured(self) -> bool:
        valid, _ = self.is_service_account_valid()
        return valid and bool(self.GDRIVE_ROOT_FOLDER_ID.strip())

settings = Settings()
