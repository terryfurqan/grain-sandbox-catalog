from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from app.config import settings, BASE_DIR
from app.database import init_db
from app.routers import catalog, stream, sync, admin

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("server")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Inisialisasi database SQLite
    init_db()
    logger.info(f"Database SQLite terinisialisasi di {settings.DATABASE_PATH}")
    sa_ok, sa_msg = settings.is_service_account_valid()
    if sa_ok:
        logger.info(f"Service Account terdeteksi: {sa_msg}")
    else:
        logger.warning(f"Service Account belum siap: {sa_msg}")
    yield
    # Shutdown
    logger.info("Server dihentikan.")

app = FastAPI(
    title=settings.PORTAL_TITLE,
    description="Lightweight Web Server Catalog for Sandbox Geological Experiments (GDrive Backend)",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Static files & Templates
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API Routers
app.include_router(catalog.router)
app.include_router(stream.router)
app.include_router(sync.router)
app.include_router(admin.router)

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    if not settings.is_configured():
        return RedirectResponse(url="/setup")
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": settings.PORTAL_TITLE,
            "subtitle": settings.PORTAL_SUBTITLE,
            "configured": True
        }
    )

@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    sa_valid, sa_info = settings.is_service_account_valid()
    return templates.TemplateResponse(
        request=request,
        name="setup.html",
        context={
            "title": settings.PORTAL_TITLE,
            "sa_valid": sa_valid,
            "sa_info": sa_info,
            "root_folder_id": settings.GDRIVE_ROOT_FOLDER_ID,
            "admin_pin": settings.ADMIN_PIN
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.SERVER_HOST,
        port=settings.SERVER_PORT,
        reload=True
    )
