"""
Authentication & Session Guard Module for GRAIN Sandbox Data Catalog.
Provides timing-attack safe credential verification, HMAC-SHA256 signed session tokens,
HttpOnly cookie management, and FastAPI route protection dependencies.
"""

import base64
import hashlib
import hmac
import json
import logging
import secrets
import time
from typing import Optional, Dict, Any
from urllib.parse import quote

from fastapi import Request, Response, HTTPException, status
from fastapi.responses import RedirectResponse

from app.config import settings

logger = logging.getLogger("auth")


def _b64encode(data: bytes) -> str:
    """Encode bytes to URL-safe base64 string without padding."""
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _b64decode(data_str: str) -> bytes:
    """Decode URL-safe base64 string with automatic padding restoration."""
    padding = 4 - (len(data_str) % 4)
    if padding < 4:
        data_str += "=" * padding
    return base64.urlsafe_b64decode(data_str.encode("utf-8"))


def create_session_token(username: str, expires_in: Optional[int] = None) -> str:
    """
    Generate a cryptographically signed, tamper-proof session token.
    Token structure: <base64url(payload)>.<base64url(signature)>
    """
    if expires_in is None:
        expires_in = settings.SESSION_MAX_AGE

    now = int(time.time())
    payload = {
        "sub": username,
        "iat": now,
        "exp": now + expires_in,
        "jti": secrets.token_hex(8)
    }

    payload_json = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    payload_b64 = _b64encode(payload_json)

    secret_key = settings.SESSION_SECRET_KEY.encode("utf-8")
    signature = hmac.new(secret_key, payload_b64.encode("utf-8"), hashlib.sha256).digest()
    signature_b64 = _b64encode(signature)

    return f"{payload_b64}.{signature_b64}"


def verify_session_token(token: str) -> Optional[Dict[str, Any]]:
    """
    Verify the cryptographic signature and expiration of a session token.
    Returns the payload dictionary if valid, otherwise None.
    """
    if not token or "." not in token:
        return None

    try:
        payload_b64, signature_b64 = token.rsplit(".", 1)

        secret_key = settings.SESSION_SECRET_KEY.encode("utf-8")
        expected_signature = hmac.new(secret_key, payload_b64.encode("utf-8"), hashlib.sha256).digest()
        provided_signature = _b64decode(signature_b64)

        # Constant-time comparison to prevent timing attacks
        if not secrets.compare_digest(expected_signature, provided_signature):
            logger.warning("Session token signature mismatch (tampered token).")
            return None

        payload_bytes = _b64decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))

        # Check token expiration
        now = int(time.time())
        if payload.get("exp", 0) < now:
            logger.debug(f"Session token expired for user: {payload.get('sub')}")
            return None

        return payload

    except Exception as e:
        logger.debug(f"Failed to decode or verify session token: {e}")
        return None


def authenticate_admin(username: str, password: str) -> bool:
    """
    Authenticate admin credentials using constant-time string comparison.
    Protects against timing attacks.
    """
    if not username or not password:
        return False

    valid_user = secrets.compare_digest(username.strip(), settings.ADMIN_USERNAME)
    valid_pass = secrets.compare_digest(password.strip(), settings.ADMIN_PASSWORD)

    return valid_user and valid_pass


def get_current_user(request: Request) -> Optional[str]:
    """
    Extract and validate authenticated user from Request:
    1. Session Cookie (`grain_session`)
    2. Authorization Header (`Bearer <token>`)
    3. App Access Token if configured
    """
    # 1. Check Session Cookie
    cookie_token = request.cookies.get(settings.SESSION_COOKIE_NAME)
    if cookie_token:
        payload = verify_session_token(cookie_token)
        if payload and payload.get("sub"):
            return payload.get("sub")

    # 2. Check Authorization Bearer header
    auth_header = request.headers.get("Authorization", "")
    if auth_header.startswith("Bearer "):
        bearer_token = auth_header[7:].strip()
        payload = verify_session_token(bearer_token)
        if payload and payload.get("sub"):
            return payload.get("sub")

    # 3. Check App Access Token if configured
    if settings.APP_ACCESS_TOKEN:
        token_query = request.query_params.get("access_token", "")
        if token_query and secrets.compare_digest(token_query, settings.APP_ACCESS_TOKEN):
            return settings.ADMIN_USERNAME

    return None


def is_authenticated(request: Request) -> bool:
    """Quick boolean check if current request has a valid admin session."""
    return get_current_user(request) is not None


def set_session_cookie(
    response: Response, 
    username: str, 
    max_age: Optional[int] = None
) -> None:
    """
    Attach secure session cookie to the HTTP Response.
    Flags: HttpOnly=True, SameSite=Lax, Secure=(configured)
    """
    if max_age is None:
        max_age = settings.SESSION_MAX_AGE

    token = create_session_token(username, expires_in=max_age)

    response.set_cookie(
        key=settings.SESSION_COOKIE_NAME,
        value=token,
        max_age=max_age,
        httponly=True,
        samesite="lax",
        secure=settings.SECURE_COOKIE,
        path="/"
    )


def clear_session_cookie(response: Response) -> None:
    """Delete session cookie from client browser."""
    response.delete_cookie(
        key=settings.SESSION_COOKIE_NAME,
        path="/"
    )


async def require_admin_login(request: Request) -> str:
    """
    FastAPI dependency to protect routes.
    If authenticated, returns the username.
    If unauthenticated:
      - Browser/HTML requests are redirected to `/login?next=...`
      - API/JSON requests receive HTTP 401 Unauthorized
    """
    user = get_current_user(request)
    if user:
        return user

    # Check if request is expecting HTML (browser navigation)
    accept = request.headers.get("accept", "")
    is_html_request = "text/html" in accept or request.url.path in ["/setup", "/admin"]

    if is_html_request:
        next_path = quote(request.url.path + (f"?{request.url.query}" if request.url.query else ""))
        raise HTTPException(
            status_code=status.HTTP_303_SEE_OTHER,
            detail="Authentication required",
            headers={"Location": f"/login?next={next_path}"}
        )

    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Autentikasi admin diperlukan. Silakan login terlebih dahulu."
    )
