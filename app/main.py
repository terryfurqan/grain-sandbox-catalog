from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import logging

from app.config import settings, BASE_DIR
from app.database import init_db
from app.limiter import limiter
from app.auth import get_current_user
from app.routers import catalog, stream, sync, admin, auth

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

# FinOps Guardrails: SlowAPI Rate Limiter
app.state.limiter = limiter

@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    """Custom response untuk 429 Too Many Requests yang ramah pengguna."""
    return JSONResponse(
        status_code=429,
        content={
            "error": "Rate limit exceeded",
            "message": "Terlalu banyak permintaan dalam waktu singkat. Harap tunggu beberapa detik.",
            "detail": str(exc.detail)
        }
    )

app.add_middleware(SlowAPIMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# FinOps Guardrails: Static Asset Browser Caching Middleware
class StaticCacheMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)
        if request.url.path.startswith("/static/"):
            response.headers["Cache-Control"] = "public, max-age=86400, immutable"
        return response

app.add_middleware(StaticCacheMiddleware)

# Static files & Templates
STATIC_DIR = Path(__file__).resolve().parent / "static"
TEMPLATES_DIR = Path(__file__).resolve().parent / "templates"

STATIC_DIR.mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "css").mkdir(parents=True, exist_ok=True)
(STATIC_DIR / "js").mkdir(parents=True, exist_ok=True)

app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include API & Web Routers
app.include_router(auth.router)
app.include_router(catalog.router)
app.include_router(stream.router)
app.include_router(sync.router)
app.include_router(admin.router)

@app.get("/", response_class=HTMLResponse)
async def home_page(request: Request):
    user = get_current_user(request)
    if settings.REQUIRE_AUTH and not user:
        return RedirectResponse(url="/login?next=/", status_code=303)

    if not settings.is_configured():
        return RedirectResponse(url="/setup")
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={
            "title": settings.PORTAL_TITLE,
            "subtitle": settings.PORTAL_SUBTITLE,
            "configured": True,
            "user": user
        }
    )

@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request):
    user = get_current_user(request)
    if settings.REQUIRE_AUTH_FOR_SETUP and not user:
        return RedirectResponse(url="/login?next=/setup", status_code=303)

    sa_valid, sa_info = settings.is_service_account_valid()
    return templates.TemplateResponse(
        request=request,
        name="setup.html",
        context={
            "title": settings.PORTAL_TITLE,
            "sa_valid": sa_valid,
            "sa_info": sa_info,
            "root_folder_id": settings.GDRIVE_ROOT_FOLDER_ID,
            "admin_pin": settings.ADMIN_PIN,
            "user": user
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
