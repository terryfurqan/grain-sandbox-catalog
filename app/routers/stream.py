from fastapi import APIRouter, Request, HTTPException, Response, Query
from fastapi.responses import StreamingResponse
import httpx
import logging
from typing import AsyncGenerator
from app.gdrive import gdrive_client
from app.config import settings
from app.limiter import limiter

router = APIRouter(prefix="/api", tags=["Streaming & Media Proxy"])
logger = logging.getLogger("stream")

DRIVE_MEDIA_URL = "https://www.googleapis.com/drive/v3/files/{file_id}?alt=media&supportsAllDrives=true"

def verify_optional_access(request: Request):
    """Verifikasi token akses opsional jika APP_ACCESS_TOKEN dikonfigurasi."""
    if not settings.APP_ACCESS_TOKEN:
        return True
    
    token = request.query_params.get("key") or request.headers.get("X-Access-Key")
    if token != settings.APP_ACCESS_TOKEN:
        raise HTTPException(
            status_code=401,
            detail="Akses ditolak. Token otorisasi tidak valid atau tidak disertakan."
        )
    return True

async def async_stream_generator(client: httpx.AsyncClient, response: httpx.Response) -> AsyncGenerator[bytes, None]:
    try:
        async for chunk in response.aiter_bytes(chunk_size=65536): # 64KB chunks for smooth buffering & low memory footprint
            yield chunk
    finally:
        await response.aclose()
        await client.aclose()

@router.get("/stream/video/{file_id}")
@limiter.limit(settings.RATE_LIMIT_STREAM)
async def stream_video(file_id: str, request: Request):
    """
    Smart Streaming Proxy untuk Video MP4 dengan dukungan HTTP Byte-Range (Seeking).
    Dilengkapi FinOps Guardrails: Cache-Control & SlowAPI Rate Limiting.
    """
    verify_optional_access(request)

    try:
        token = gdrive_client.get_access_token()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal mengautentikasi ke Google Drive: {str(e)}")

    url = DRIVE_MEDIA_URL.format(file_id=file_id)
    headers = {
        "Authorization": f"Bearer {token}"
    }

    # Teruskan header Range jika browser meminta partial content untuk seeking
    range_header = request.headers.get("range")
    if range_header:
        headers["Range"] = range_header

    client = httpx.AsyncClient(timeout=httpx.Timeout(connect=10.0, read=60.0, write=10.0, pool=30.0))
    
    try:
        req = client.build_request("GET", url, headers=headers)
        res = await client.send(req, stream=True)

        if res.status_code not in (200, 206):
            await res.aclose()
            await client.aclose()
            raise HTTPException(
                status_code=res.status_code, 
                detail=f"Google Drive API error: {res.status_code}"
            )

        # Siapkan header balasan untuk browser dengan proteksi Egress (Cache 7 hari)
        response_headers = {
            "Accept-Ranges": "bytes",
            "Content-Type": res.headers.get("Content-Type", "video/mp4"),
            "Cache-Control": f"public, max-age={settings.CACHE_MAX_AGE_MEDIA}, immutable",
        }

        if "Content-Range" in res.headers:
            response_headers["Content-Range"] = res.headers["Content-Range"]
        if "Content-Length" in res.headers:
            response_headers["Content-Length"] = res.headers["Content-Length"]

        return StreamingResponse(
            async_stream_generator(client, res),
            status_code=res.status_code,
            headers=response_headers,
            media_type=response_headers["Content-Type"]
        )

    except Exception as e:
        await client.aclose()
        if isinstance(e, HTTPException):
            raise e
        logger.error(f"Error streaming video {file_id}: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stream error: {str(e)}")

@router.get("/preview/image/{file_id}")
@limiter.limit(settings.RATE_LIMIT_DEFAULT)
async def preview_image(file_id: str, request: Request):
    """
    Image Proxy untuk menampilkan foto JPG/PNG full-resolution atau thumbnail dari Google Drive.
    Dilengkapi FinOps Guardrails: Cache-Control 7 hari & Rate Limiting.
    """
    verify_optional_access(request)

    try:
        token = gdrive_client.get_access_token()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal otentikasi Google Drive: {str(e)}")

    url = DRIVE_MEDIA_URL.format(file_id=file_id)
    headers = {"Authorization": f"Bearer {token}"}

    client = httpx.AsyncClient(timeout=30.0)
    try:
        req = client.build_request("GET", url, headers=headers)
        res = await client.send(req, stream=True)

        if res.status_code != 200:
            await res.aclose()
            await client.aclose()
            raise HTTPException(status_code=res.status_code, detail="Gagal mengambil gambar dari GDrive")

        response_headers = {
            "Content-Type": res.headers.get("Content-Type", "image/jpeg"),
            "Cache-Control": f"public, max-age={settings.CACHE_MAX_AGE_MEDIA}, immutable",
        }
        if "Content-Length" in res.headers:
            response_headers["Content-Length"] = res.headers["Content-Length"]

        return StreamingResponse(
            async_stream_generator(client, res),
            status_code=200,
            headers=response_headers,
            media_type=response_headers["Content-Type"]
        )
    except Exception as e:
        await client.aclose()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Image stream error: {str(e)}")

@router.get("/download/{file_id}")
@limiter.limit(settings.RATE_LIMIT_DOWNLOAD)
async def download_file(file_id: str, request: Request, filename: str = "file"):
    """
    Download file langsung dari Google Drive melalui proxy dengan header Content-Disposition.
    Dilengkapi FinOps Guardrails: Rate Limiting ketat (10 req/menit).
    """
    verify_optional_access(request)

    try:
        token = gdrive_client.get_access_token()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Gagal otentikasi Google Drive: {str(e)}")

    url = DRIVE_MEDIA_URL.format(file_id=file_id)
    headers = {"Authorization": f"Bearer {token}"}

    client = httpx.AsyncClient(timeout=60.0)
    try:
        req = client.build_request("GET", url, headers=headers)
        res = await client.send(req, stream=True)

        if res.status_code != 200:
            await res.aclose()
            await client.aclose()
            raise HTTPException(status_code=res.status_code, detail="Gagal mendownload file dari GDrive")

        response_headers = {
            "Content-Type": res.headers.get("Content-Type", "application/octet-stream"),
            "Content-Disposition": f'attachment; filename="{filename}"',
            "Cache-Control": f"public, max-age={settings.CACHE_MAX_AGE_MEDIA}, immutable",
        }
        if "Content-Length" in res.headers:
            response_headers["Content-Length"] = res.headers["Content-Length"]

        return StreamingResponse(
            async_stream_generator(client, res),
            status_code=200,
            headers=response_headers
        )
    except Exception as e:
        await client.aclose()
        if isinstance(e, HTTPException):
            raise e
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")
