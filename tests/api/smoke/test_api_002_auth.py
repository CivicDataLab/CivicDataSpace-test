# tests/api/smoke/test_api_002_auth.py
#
# Test the authentication endpoints:
#   POST /api/auth/keycloak/login/   — exchange Keycloak token for Django JWT
#   POST /api/auth/token/refresh/    — refresh expired Django JWT
#   GET  /api/auth/user/info/        — return current user's profile

import pytest


@pytest.mark.api
@pytest.mark.functional
def test_auth_token_has_required_fields(auth_token, api_base_url, keycloak_config, test_credentials):
    """
    The Keycloak → Django JWT exchange must return 'access', 'refresh',
    and a populated 'user' object with id/email fields.
    """
    import requests
    from tests.api.conftest import _get_keycloak_token

    email, password = test_credentials
    kc_token = _get_keycloak_token(
        keycloak_config["url"],
        keycloak_config["realm"],
        keycloak_config["client_id"],
        email,
        password,
        # `dataspace` is a confidential client: omitting the secret makes Keycloak
        # reject the ROPC request with 401, which _get_keycloak_token turns into a
        # skip — so this test silently never ran until 2026-09-09.
        client_secret=keycloak_config.get("client_secret"),
    )
    resp = requests.post(
        f"{api_base_url}/api/auth/keycloak/login/",
        json={"token": kc_token},
    )
    assert resp.status_code == 200, (
        f"Django token exchange failed ({resp.status_code}): {resp.text}"
    )
    body = resp.json()
    assert "access" in body, "Response missing 'access' token"
    assert "refresh" in body, "Response missing 'refresh' token"
    assert "user" in body, "Response missing 'user' object"
    user = body["user"]
    assert "id" in user, "User object missing 'id'"
    assert "email" in user, "User object missing 'email'"


@pytest.mark.api
@pytest.mark.regression
def test_auth_login_rejects_missing_token(anon_api_client):
    """POST /api/auth/keycloak/login/ without a token must return 400."""
    resp = anon_api_client.post("/api/auth/keycloak/login/", json={})
    assert resp.status_code == 400, (
        f"Expected 400 for missing token, got {resp.status_code}"
    )


@pytest.mark.api
@pytest.mark.regression
def test_auth_login_rejects_invalid_token(anon_api_client):
    """POST /api/auth/keycloak/login/ with a bogus token must return 401."""
    resp = anon_api_client.post(
        "/api/auth/keycloak/login/",
        json={"token": "this-is-not-a-valid-keycloak-token"},
    )
    assert resp.status_code == 401, (
        f"Expected 401 for invalid token, got {resp.status_code}"
    )


@pytest.mark.api
@pytest.mark.functional
def test_token_refresh_returns_new_access_token(api_base_url, refresh_token):
    """POST /api/auth/token/refresh/ must return a new 'access' token."""
    import requests

    resp = requests.post(
        f"{api_base_url}/api/auth/token/refresh/",
        json={"refresh": refresh_token},
    )
    assert resp.status_code == 200, (
        f"Token refresh failed ({resp.status_code}): {resp.text}"
    )
    body = resp.json()
    assert "access" in body, "Token refresh response missing 'access' field"


@pytest.mark.api
@pytest.mark.smoke
def test_user_info_returns_current_user(api_client):
    """GET /api/auth/user/info/ must return the authenticated user's profile."""
    resp = api_client.get("/api/auth/user/info/")
    assert resp.status_code == 200, (
        f"User info request failed ({resp.status_code}): {resp.text}"
    )
    body = resp.json()
    assert "id" in body, "User info missing 'id'"
    assert "email" in body, "User info missing 'email'"
    assert "organizations" in body, "User info missing 'organizations'"


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.xfail(reason="Backend returns 500 instead of 401 for unauthenticated /api/auth/user/info/")
def test_user_info_requires_auth(anon_api_client):
    """GET /api/auth/user/info/ without a token must return 401 or 403."""
    resp = anon_api_client.get("/api/auth/user/info/")
    assert resp.status_code in (401, 403), (
        f"Expected 401/403 for unauthenticated user info, got {resp.status_code}"
    )
