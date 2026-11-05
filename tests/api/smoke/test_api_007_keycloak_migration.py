# tests/api/smoke/test_api_007_keycloak_migration.py
#
# Keycloak migration regression coverage.
#
# The platform moved off the old Keycloak deployment
# (opub-kc.civicdatalab.in, which served every realm under an `/auth`
# path prefix) onto a new one (auth.civicdatalab.in) running a Keycloak
# version that dropped the `/auth` prefix entirely. Two things broke and
# are guarded here:
#
#   1. Any config still carrying the `/auth` segment now builds URLs that
#      404 — including this suite's own KEYCLOAK_URL, which had it.
#   2. Tokens minted by the old server are rejected by the backend, so the
#      frontend and the analytics app must both hand users off to the new
#      issuer, not the old one.
#
# The expected values below are asserted as literals on purpose: they are
# the migration target itself, so deriving them from the same env vars the
# app reads would make the test agree with whatever is misconfigured.

import os

import pytest
import requests

pytestmark = pytest.mark.readonly

KEYCLOAK_BASE = "https://auth.civicdatalab.in"
KEYCLOAK_REALM = "DataSpace"

REALM_URL = f"{KEYCLOAK_BASE}/realms/{KEYCLOAK_REALM}"
DISCOVERY_URL = f"{REALM_URL}/.well-known/openid-configuration"
# The pre-migration shape of the same URL. Must be gone.
LEGACY_DISCOVERY_URL = (
    f"{KEYCLOAK_BASE}/auth/realms/{KEYCLOAK_REALM}/.well-known/openid-configuration"
)
AUTH_ENDPOINT_PATH = f"/realms/{KEYCLOAK_REALM}/protocol/openid-connect/auth"

EXPECTED_CLIENT_ID = "dataspace"

ANALYTICS_LOGIN_URL = "https://dev.analytics.civicdataspace.in/login/keycloak"

# Some of these hosts reject the default python-requests/curl User-Agent
# with a 403, so every request here goes out looking like a browser.
BROWSER_UA = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36"
)

REQUEST_TIMEOUT = 30


def _browser_session() -> requests.Session:
    session = requests.Session()
    session.headers["User-Agent"] = BROWSER_UA
    return session


# ─── The Keycloak server itself ───────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
def test_keycloak_discovery_document_is_served_without_auth_prefix():
    """The migrated realm must publish OIDC discovery at /realms/<realm>/…"""
    resp = _browser_session().get(DISCOVERY_URL, timeout=REQUEST_TIMEOUT)
    assert resp.status_code == 200, (
        f"Keycloak discovery at {DISCOVERY_URL} failed "
        f"({resp.status_code}): {resp.text[:500]}"
    )
    issuer = resp.json().get("issuer")
    assert issuer == REALM_URL, (
        f"Expected issuer {REALM_URL!r}, got {issuer!r} — the realm is not "
        "the migrated one"
    )


@pytest.mark.api
@pytest.mark.regression
def test_keycloak_legacy_auth_path_is_gone():
    """
    The old `/auth`-prefixed realm path must 404. This is the exact breakage
    the migration introduced: config that kept `/auth` silently built URLs
    that no longer exist.
    """
    resp = _browser_session().get(LEGACY_DISCOVERY_URL, timeout=REQUEST_TIMEOUT)
    assert resp.status_code == 404, (
        f"Expected 404 for the legacy /auth realm path {LEGACY_DISCOVERY_URL}, "
        f"got {resp.status_code}: {resp.text[:500]}"
    )


@pytest.mark.api
@pytest.mark.regression
def test_configured_keycloak_url_resolves_to_a_live_realm():
    """
    KEYCLOAK_URL + KEYCLOAK_REALM (as this suite's own fixtures compose them
    in tests/api/conftest.py::_get_keycloak_token) must reach a live
    discovery document. Catches a .env / CI secret still pointing at the old
    server, or still carrying the `/auth` segment.
    """
    kc_url = os.getenv("KEYCLOAK_URL")
    realm = os.getenv("KEYCLOAK_REALM")
    if not (kc_url and realm):
        pytest.skip("KEYCLOAK_URL / KEYCLOAK_REALM not set — nothing to validate")

    url = (
        f"{kc_url.rstrip('/')}/realms/{realm}"
        f"/.well-known/openid-configuration"
    )
    resp = _browser_session().get(url, timeout=REQUEST_TIMEOUT)
    assert resp.status_code == 200, (
        f"Configured Keycloak discovery URL {url} failed ({resp.status_code}): "
        f"{resp.text[:500]} — check KEYCLOAK_URL (it must be the migrated host "
        "with no /auth path segment)"
    )

    # A 200 alone is NOT enough. The pre-migration server is still running and
    # still answers 200 under /auth, so a stale KEYCLOAK_URL resolves happily
    # and hides the misconfiguration. Pin the identity of the realm we reached:
    # tokens minted by any other issuer are rejected by the backend.
    issuer = resp.json().get("issuer")
    assert issuer == REALM_URL, (
        f"KEYCLOAK_URL={kc_url!r} resolves to issuer {issuer!r}, but this "
        f"deployment requires {REALM_URL!r}. Tokens from the wrong issuer are "
        "rejected by the backend, so every authenticated test would fail or "
        "silently skip. Update KEYCLOAK_URL in .env and the CI secret."
    )


# ─── Frontend sign-in hand-off ────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
def test_frontend_signin_redirects_to_migrated_keycloak(frontend_base_url_dev):
    """
    POST /api/auth/signin/keycloak (with a CSRF token from /api/auth/csrf)
    must 302 to the migrated Keycloak authorization endpoint, for the
    `dataspace` client, with a callback back to this frontend.
    """
    session = _browser_session()

    csrf_resp = session.get(
        f"{frontend_base_url_dev}/api/auth/csrf", timeout=REQUEST_TIMEOUT
    )
    assert csrf_resp.status_code == 200, (
        f"CSRF token request failed ({csrf_resp.status_code}): {csrf_resp.text[:500]}"
    )
    csrf_token = csrf_resp.json().get("csrfToken")
    assert csrf_token, f"No csrfToken in response: {csrf_resp.text[:500]}"

    resp = session.post(
        f"{frontend_base_url_dev}/api/auth/signin/keycloak",
        data={"csrfToken": csrf_token, "callbackUrl": frontend_base_url_dev},
        allow_redirects=False,
        timeout=REQUEST_TIMEOUT,
    )
    assert resp.status_code == 302, (
        f"Expected a 302 to Keycloak, got {resp.status_code}: {resp.text[:500]}"
    )

    location = resp.headers.get("Location", "")
    assert f"{KEYCLOAK_BASE}{AUTH_ENDPOINT_PATH}" in location, (
        f"Sign-in did not redirect to the migrated Keycloak authorization "
        f"endpoint. Location: {location!r}"
    )
    assert f"client_id={EXPECTED_CLIENT_ID}" in location, (
        f"Expected client_id={EXPECTED_CLIENT_ID} in redirect. Location: {location!r}"
    )
    expected_callback = f"{frontend_base_url_dev}/api/auth/callback/keycloak"
    assert requests.utils.unquote(location).find(expected_callback) != -1, (
        f"Expected redirect_uri {expected_callback!r} in redirect. "
        f"Location: {location!r}"
    )


# ─── Backend health after the migration ───────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
def test_backend_reports_core_services_healthy(anon_api_client):
    """
    /health/ must report overall "healthy" with database, elasticsearch and
    redis each healthy.

    `telemetry` is deliberately NOT asserted: dev reports "not_configured"
    (TELEMETRY_URL is unset there by design) while prod reports "healthy",
    so an assertion on it would fail on dev for a non-bug.
    """
    resp = anon_api_client.get("/health/")
    assert resp.status_code == 200, (
        f"Health check failed ({resp.status_code}): {resp.text}"
    )
    body = resp.json()
    assert body.get("status") == "healthy", (
        f"Expected overall status 'healthy', got {body.get('status')!r}: {resp.text}"
    )

    services = body.get("services", {})
    for name in ("database", "elasticsearch", "redis"):
        assert name in services, (
            f"Health response has no {name!r} service entry: {resp.text}"
        )
        status = services[name].get("status")
        assert status == "healthy", (
            f"Service {name!r} reported {status!r}, expected 'healthy': {resp.text}"
        )


# ─── Analytics app sign-in hand-off ───────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
def test_analytics_login_redirects_to_migrated_keycloak():
    """
    The dev analytics app must also hand off to the migrated Keycloak for
    the `dataspace` client. Redirects are not followed — the Location header
    is the assertion target.
    """
    resp = _browser_session().get(
        ANALYTICS_LOGIN_URL, allow_redirects=False, timeout=REQUEST_TIMEOUT
    )
    assert resp.status_code == 302, (
        f"Expected 302 from {ANALYTICS_LOGIN_URL}, got {resp.status_code}: "
        f"{resp.text[:500]}"
    )

    location = resp.headers.get("Location", "")
    assert f"{KEYCLOAK_BASE}{AUTH_ENDPOINT_PATH}" in location, (
        f"Analytics login did not redirect to the migrated Keycloak. "
        f"Location: {location!r}"
    )
    assert f"client_id={EXPECTED_CLIENT_ID}" in location, (
        f"Expected client_id={EXPECTED_CLIENT_ID} in redirect. Location: {location!r}"
    )
