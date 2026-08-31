"""
Test Suite untuk Sistem Autentikasi dan Session Guard GRAIN Sandbox Data Catalog.
Menguji Token Kriptografi, Login Page, Form & JSON Auth, Cookie Security, Route Protection, dan Logout.
"""

import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

# Pastikan root workspace berada di sys.path
BASE_DIR = Path(__file__).resolve().parent.parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))

from app.config import settings, Settings
from app.auth import (
    create_session_token,
    verify_session_token,
    authenticate_admin,
    set_session_cookie,
    clear_session_cookie,
    get_current_user,
    is_authenticated,
)
from app.main import app


class TestAuthTokensAndCrypto(unittest.TestCase):
    """Pengujian unit untuk modul kriptografi token sesi dan perbandingan kredensial."""

    def test_create_and_verify_session_token(self):
        """Membuat token sesi dan memverifikasinya kembali."""
        token = create_session_token("terryfurqan", expires_in=3600)
        self.assertIsInstance(token, str)
        self.assertIn(".", token)

        payload = verify_session_token(token)
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get("sub"), "terryfurqan")
        self.assertIn("iat", payload)
        self.assertIn("exp", payload)
        self.assertGreater(payload["exp"], payload["iat"])

    def test_verify_session_token_expired(self):
        """Token yang sudah kedaluwarsa harus ditolak (return None)."""
        # Buat token dengan expires_in negatif (-10 detik)
        token = create_session_token("terryfurqan", expires_in=-10)
        payload = verify_session_token(token)
        self.assertIsNone(payload, "Token kedaluwarsa harus ditolak.")

    def test_verify_session_token_tampered_signature(self):
        """Token dengan tanda tangan (signature) yang dimanipulasi harus ditolak."""
        token = create_session_token("terryfurqan", expires_in=3600)
        payload_b64, sig_b64 = token.rsplit(".", 1)

        # Ubah 1 karakter pada signature
        tampered_sig = ("A" if sig_b64[0] != "A" else "B") + sig_b64[1:]
        tampered_token = f"{payload_b64}.{tampered_sig}"

        self.assertIsNone(verify_session_token(tampered_token), "Signature yang diubah harus gagal verifikasi.")

    def test_verify_session_token_tampered_payload(self):
        """Token dengan payload yang dimanipulasi (walau signature lama) harus ditolak."""
        token = create_session_token("terryfurqan", expires_in=3600)
        payload_b64, sig_b64 = token.rsplit(".", 1)

        # Ubah payload
        fake_payload_b64 = "eyJzdWIiOiJoYWNrZXIifQ"
        tampered_token = f"{fake_payload_b64}.{sig_b64}"

        self.assertIsNone(verify_session_token(tampered_token), "Payload yang dimanipulasi harus gagal verifikasi.")

    def test_verify_session_token_invalid_format(self):
        """Token berformat tidak valid harus ditolak secara graceful."""
        self.assertIsNone(verify_session_token(""))
        self.assertIsNone(verify_session_token("invalid-format-without-dot"))
        self.assertIsNone(verify_session_token("abc.def.extra.dot"))

    def test_authenticate_admin_correct_credentials(self):
        """Kredensial admin default harus berhasil diautentikasi."""
        self.assertTrue(authenticate_admin("terryfurqan", "ifasayang123"))

    def test_authenticate_admin_wrong_username(self):
        """Username salah harus ditolak."""
        self.assertFalse(authenticate_admin("bukan_terry", "ifasayang123"))

    def test_authenticate_admin_wrong_password(self):
        """Password salah harus ditolak."""
        self.assertFalse(authenticate_admin("terryfurqan", "passwordsalah"))

    def test_authenticate_admin_empty_credentials(self):
        """Kredensial kosong harus ditolak."""
        self.assertFalse(authenticate_admin("", ""))
        self.assertFalse(authenticate_admin("terryfurqan", ""))
        self.assertFalse(authenticate_admin("", "ifasayang123"))


class TestAuthEndpoints(unittest.TestCase):
    """Pengujian integrasi endpoint login, logout, dan status session."""

    def setUp(self):
        self.client = TestClient(app)

    def test_get_login_page_renders_html(self):
        """GET /login harus merender halaman HTML login portal."""
        res = self.client.get("/login")
        self.assertEqual(res.status_code, 200)
        self.assertIn("text/html", res.headers.get("content-type", ""))
        self.assertIn("Portal Akses Admin", res.text)
        self.assertIn("Username", res.text)
        self.assertIn("Password", res.text)

    def test_get_login_page_redirects_if_already_logged_in(self):
        """GET /login saat user sudah login harus otomatis me-redirect ke target/home."""
        token = create_session_token("terryfurqan")
        self.client.cookies.set(settings.SESSION_COOKIE_NAME, token)

        res = self.client.get("/login?next=/setup", follow_redirects=False)
        self.assertEqual(res.status_code, 303)
        self.assertEqual(res.headers.get("location"), "/setup")

    def test_post_login_form_success(self):
        """POST /login dengan form data valid harus me-redirect (303) dan men-set session cookie."""
        res = self.client.post(
            "/login",
            data={"username": "terryfurqan", "password": "ifasayang123", "next": "/setup"},
            follow_redirects=False
        )
        self.assertEqual(res.status_code, 303)
        self.assertEqual(res.headers.get("location"), "/setup")

        # Periksa Cookie yang di-set
        cookie = res.cookies.get(settings.SESSION_COOKIE_NAME)
        self.assertIsNotNone(cookie, "Cookie session harus disertakan dalam response.")
        
        # Validasi token di dalam cookie
        payload = verify_session_token(cookie)
        self.assertIsNotNone(payload)
        self.assertEqual(payload.get("sub"), "terryfurqan")

    def test_post_login_form_invalid_password(self):
        """POST /login dengan password salah harus mengembalikan status 401 dan pesan error di halaman."""
        res = self.client.post(
            "/login",
            data={"username": "terryfurqan", "password": "wrong_password"},
            follow_redirects=False
        )
        self.assertEqual(res.status_code, 401)
        self.assertIn("Username atau Password salah", res.text)
        self.assertIsNone(res.cookies.get(settings.SESSION_COOKIE_NAME))

    def test_post_login_json_success(self):
        """POST /login dengan JSON payload valid harus mengembalikan 200 OK JSON dan session cookie."""
        res = self.client.post(
            "/login",
            json={"username": "terryfurqan", "password": "ifasayang123", "next": "/"},
            headers={"Accept": "application/json"}
        )
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertEqual(data.get("status"), "success")
        self.assertEqual(data.get("username"), "terryfurqan")
        self.assertEqual(data.get("redirect_url"), "/")

        # Periksa Cookie
        cookie = res.cookies.get(settings.SESSION_COOKIE_NAME)
        self.assertIsNotNone(cookie)

    def test_post_login_json_invalid_credentials(self):
        """POST /login dengan JSON salah harus mengembalikan HTTP 401 JSON error."""
        res = self.client.post(
            "/login",
            json={"username": "terryfurqan", "password": "wrong"},
            headers={"Accept": "application/json"}
        )
        self.assertEqual(res.status_code, 401)
        data = res.json()
        self.assertEqual(data.get("status"), "error")
        self.assertIn("Username atau Password salah", data.get("message", ""))

    def test_get_logout_clears_cookie_and_redirects(self):
        """GET /logout harus menghapus cookie session dan me-redirect ke /login."""
        token = create_session_token("terryfurqan")
        self.client.cookies.set(settings.SESSION_COOKIE_NAME, token)

        res = self.client.get("/logout", follow_redirects=False)
        self.assertEqual(res.status_code, 303)
        self.assertIn("/login", res.headers.get("location", ""))

        # Periksa bahwa cookie dihapus / max-age=0
        set_cookie_header = res.headers.get("set-cookie", "")
        self.assertIn(settings.SESSION_COOKIE_NAME, set_cookie_header)

    def test_post_logout_clears_cookie_and_redirects(self):
        """POST /logout harus menghapus cookie session dan me-redirect ke /login."""
        res = self.client.post("/logout", follow_redirects=False)
        self.assertEqual(res.status_code, 303)
        self.assertIn("/login", res.headers.get("location", ""))

    def test_get_auth_me_unauthenticated(self):
        """GET /api/auth/me saat unauthenticated harus mengembalikan status false."""
        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertFalse(data.get("authenticated"))
        self.assertIsNone(data.get("username"))
        self.assertEqual(data.get("role"), "guest")

    def test_get_auth_me_authenticated(self):
        """GET /api/auth/me saat authenticated harus mengembalikan username dan role admin."""
        token = create_session_token("terryfurqan")
        self.client.cookies.set(settings.SESSION_COOKIE_NAME, token)

        res = self.client.get("/api/auth/me")
        self.assertEqual(res.status_code, 200)
        data = res.json()
        self.assertTrue(data.get("authenticated"))
        self.assertEqual(data.get("username"), "terryfurqan")
        self.assertEqual(data.get("role"), "admin")


class TestRouteProtection(unittest.TestCase):
    """Pengujian proteksi route sensitif terhadap akses tanpa session cookie valid."""

    def setUp(self):
        self.client = TestClient(app)

    def test_setup_page_redirects_unauthenticated_user(self):
        """GET /setup tanpa cookie session harus di-redirect (303) ke /login?next=/setup."""
        res = self.client.get("/setup", follow_redirects=False)
        self.assertEqual(res.status_code, 303)
        self.assertIn("/login?next=/setup", res.headers.get("location", ""))

    def test_setup_page_accessible_with_valid_session_cookie(self):
        """GET /setup dengan cookie session valid harus mengembalikan status 200 OK."""
        token = create_session_token("terryfurqan")
        self.client.cookies.set(settings.SESSION_COOKIE_NAME, token)

        res = self.client.get("/setup", follow_redirects=False)
        self.assertEqual(res.status_code, 200)
        self.assertIn("Setup", res.text)
        self.assertIn("terryfurqan", res.text)

    def test_setup_page_rejects_tampered_session_cookie(self):
        """GET /setup dengan cookie yang di-tamper harus di-redirect ke /login."""
        self.client.cookies.set(settings.SESSION_COOKIE_NAME, "fake_tampered_token.12345")

        res = self.client.get("/setup", follow_redirects=False)
        self.assertEqual(res.status_code, 303)
        self.assertIn("/login?next=/setup", res.headers.get("location", ""))

    def test_require_auth_catalog_lock_mode(self):
        """Saat REQUIRE_AUTH=True, homepage / harus mengunci akses dan me-redirect unauthenticated user ke /login."""
        with patch.object(settings, "REQUIRE_AUTH", True):
            # 1. Unauthenticated request
            res_unauth = self.client.get("/", follow_redirects=False)
            self.assertEqual(res_unauth.status_code, 303)
            self.assertIn("/login?next=/", res_unauth.headers.get("location", ""))

            # 2. Authenticated request
            token = create_session_token("terryfurqan")
            self.client.cookies.set(settings.SESSION_COOKIE_NAME, token)
            with patch.object(Settings, "is_configured", return_value=True):
                res_auth = self.client.get("/", follow_redirects=False)
                self.assertEqual(res_auth.status_code, 200)
                self.assertIn("text/html", res_auth.headers.get("content-type", ""))
