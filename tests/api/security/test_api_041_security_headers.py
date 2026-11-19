# tests/api/security/test_api_041_security_headers.py
#
# Baseline browser-hardening response headers. Non-destructive: one GET each.
#
# A header that dev does not send today is a strict xfail with a neutral reason,
# not a weaker assertion: the day it is added the xfail turns XPASS and fails
# the run, which is the cue to delete the marker.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.security]

MISSING_ON_DEV = "not sent by the dev frontend at the time of writing"


def _framing(h):
    """X-Frame-Options, or a CSP frame-ancestors directive."""
    xfo = h.get("X-Frame-Options", "").upper()
    csp = h.get("Content-Security-Policy", "").lower()
    return xfo in ("DENY", "SAMEORIGIN") or "frame-ancestors" in csp


def _xfail(name):
    return pytest.mark.xfail(strict=True, reason=f"{name} {MISSING_ON_DEV}")


FRONTEND_CHECKS = [
    pytest.param(
        "Strict-Transport-Security",
        lambda h: "max-age" in h.get("Strict-Transport-Security", "").lower(),
        id="hsts", marks=_xfail("Strict-Transport-Security")),
    pytest.param(
        "X-Content-Type-Options",
        lambda h: h.get("X-Content-Type-Options", "").lower() == "nosniff",
        id="nosniff", marks=_xfail("X-Content-Type-Options")),
    pytest.param(
        "clickjacking protection (X-Frame-Options or CSP frame-ancestors)",
        _framing, id="framing", marks=_xfail("X-Frame-Options / frame-ancestors")),
    pytest.param(
        "Referrer-Policy",
        lambda h: bool(h.get("Referrer-Policy")),
        id="referrer", marks=_xfail("Referrer-Policy")),
]


@pytest.mark.parametrize("name,check", FRONTEND_CHECKS)
def test_frontend_sends_security_header(dev_frontend_client, name, check):
    resp = dev_frontend_client.get("/")
    assert resp.status_code == 200, f"frontend / returned {resp.status_code}"
    assert check(resp.headers), f"frontend / is missing {name}; headers: {sorted(resp.headers)}"


@pytest.mark.parametrize("name,check", [
    ("clickjacking protection (X-Frame-Options or CSP frame-ancestors)", _framing),
    ("Referrer-Policy", lambda h: bool(h.get("Referrer-Policy"))),
], ids=["framing", "referrer"])
def test_api_sends_security_header(anon_api_client, name, check):
    resp = anon_api_client.get("/health/")
    assert resp.status_code == 200, f"/health/ returned {resp.status_code}"
    assert check(resp.headers), f"API /health/ is missing {name}; headers: {sorted(resp.headers)}"
