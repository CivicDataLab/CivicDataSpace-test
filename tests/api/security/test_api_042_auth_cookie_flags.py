# tests/api/security/test_api_042_auth_cookie_flags.py
#
# Cookies the frontend's NextAuth layer sets for an anonymous visitor
# (/api/auth/csrf) must be Secure, HttpOnly and SameSite. No login needed.
# NEXT_LOCALE is a UI preference, not an auth cookie, and is excluded.

import pytest
import requests

pytestmark = [pytest.mark.api, pytest.mark.security]


def _auth_cookie_headers(base_url):
    resp = requests.get(f"{base_url}/api/auth/csrf", timeout=30)
    assert resp.status_code == 200, f"/api/auth/csrf returned {resp.status_code}"
    raw = resp.raw.headers.getlist("Set-Cookie")
    return [c for c in raw if "next-auth" in c.split("=", 1)[0].lower()]


def test_nextauth_cookies_are_secure_httponly_samesite(frontend_base_url_dev):
    cookies = _auth_cookie_headers(frontend_base_url_dev)
    assert cookies, "no next-auth cookie was set by /api/auth/csrf; the check would be vacuous"
    for c in cookies:
        name = c.split("=", 1)[0]
        flags = c.lower()
        assert "secure" in flags, f"{name} lacks Secure"
        assert "httponly" in flags, f"{name} lacks HttpOnly"
        assert "samesite=" in flags and "samesite=none" not in flags, f"{name} lacks a restrictive SameSite"
