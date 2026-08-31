from fastapi import APIRouter, Request, Response, Form, Depends, HTTPException, status
from fastapi.responses import HTMLResponse, RedirectResponse, JSONResponse
from fastapi.templating import Jinja2Templates
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse

from app.config import settings
from app.auth import (
    authenticate_admin,
    set_session_cookie,
    clear_session_cookie,
    get_current_user,
    is_authenticated,
)
from app.models import LoginRequest

router = APIRouter(tags=["Authentication"])

TEMPLATES_DIR = Path(__file__).resolve().parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


def _sanitize_next_url(next_url: Optional[str]) -> str:
    """Ensure redirect URL is a safe local relative path to avoid open redirects."""
    if not next_url:
        return "/"
    next_url = next_url.strip()
    # If URL contains scheme or netloc (e.g., https://evil.com), force default
    parsed = urlparse(next_url)
    if parsed.netloc or parsed.scheme:
        return "/"
    if not next_url.startswith("/"):
        return "/"
    return next_url


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request, next: str = "/"):
    """
    Render login page.
    If already authenticated, automatically redirect to next target or home.
    """
    safe_next = _sanitize_next_url(next)
    current_user = get_current_user(request)
    if current_user:
        return RedirectResponse(url=safe_next, status_code=status.HTTP_303_SEE_OTHER)

    return templates.TemplateResponse(
        request=request,
        name="login.html",
        context={
            "title": settings.PORTAL_TITLE,
            "subtitle": settings.PORTAL_SUBTITLE,
            "next": safe_next,
            "error": None,
            "username": "",
            "logged_out": request.query_params.get("logged_out") == "1",
            "configured": settings.is_configured(),
        }
    )


@router.post("/login")
async def login_submit(
    request: Request,
    username: Optional[str] = Form(None),
    password: Optional[str] = Form(None),
    next: Optional[str] = Form("/"),
):
    """
    Process login authentication.
    Supports both traditional Form POST and JSON API requests.
    """
    # 1. Check if request is JSON body
    content_type = request.headers.get("content-type", "")
    is_json = "application/json" in content_type

    if is_json:
        try:
            body = await request.json()
            username = body.get("username", "")
            password = body.get("password", "")
            next = body.get("next", "/")
        except Exception:
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"status": "error", "message": "Invalid JSON format"}
            )

    username = (username or "").strip()
    password = (password or "").strip()
    safe_next = _sanitize_next_url(next)

    # 2. Verify credentials
    if not authenticate_admin(username, password):
        if is_json:
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content={
                    "status": "error",
                    "message": "Username atau Password salah! Periksa kembali kredensial Anda."
                }
            )
        return templates.TemplateResponse(
            request=request,
            name="login.html",
            context={
                "title": settings.PORTAL_TITLE,
                "subtitle": settings.PORTAL_SUBTITLE,
                "next": safe_next,
                "error": "Username atau Password salah! Periksa kembali kredensial Anda.",
                "username": username,
                "logged_out": False,
                "configured": settings.is_configured(),
            },
            status_code=status.HTTP_401_UNAUTHORIZED
        )

    # 3. Successful Login -> Attach session cookie
    if is_json:
        json_resp = JSONResponse(
            content={
                "status": "success",
                "message": "Login berhasil! Mengalihkan...",
                "username": username,
                "redirect_url": safe_next
            }
        )
        set_session_cookie(json_resp, username)
        return json_resp

    redirect_resp = RedirectResponse(
        url=safe_next, 
        status_code=status.HTTP_303_SEE_OTHER
    )
    set_session_cookie(redirect_resp, username)
    return redirect_resp


@router.get("/logout")
@router.post("/logout")
async def logout(request: Request):
    """
    Clear session cookie and redirect to login page.
    """
    response = RedirectResponse(
        url="/login?logged_out=1",
        status_code=status.HTTP_303_SEE_OTHER
    )
    clear_session_cookie(response)
    return response


@router.get("/api/auth/me")
async def get_me(request: Request):
    """
    Check current authentication status and user details.
    """
    user = get_current_user(request)
    return {
        "authenticated": user is not None,
        "username": user,
        "role": "admin" if user else "guest"
    }
