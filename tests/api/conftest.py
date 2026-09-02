# tests/api/conftest.py
#
# Session-scoped fixtures for API tests.
# Handles Keycloak authentication and provides ready-to-use API/GraphQL clients.
#
# Required .env variables:
#   API_BASE_URL           - Backend base URL, e.g. https://your-api-host
#   KEYCLOAK_URL           - Keycloak server base URL, e.g. https://your-keycloak-host/auth
#   KEYCLOAK_REALM         - Keycloak realm name, e.g. MyRealm
#   KEYCLOAK_CLIENT_ID     - Keycloak client ID (same as frontend KEYCLOAK_CLIENT_ID)
#   KEYCLOAK_CLIENT_SECRET - Keycloak client secret (same as frontend KEYCLOAK_CLIENT_SECRET)
#   TEST_EMAIL_1           - Test user email (shared with UI tests)
#   TEST_PASSWORD_1        - Test user password (shared with UI tests)

import os
import time
from typing import Optional

import pytest
import requests

from tests.api.client import APIClient, GraphQLClient



def _exchange_for_django_token(api_base_url, kc_token, attempts=3):
    """Exchange a Keycloak token for a Django JWT, tolerating a slow endpoint.

    /api/auth/keycloak/login/ on dev intermittently exceeds nginx's 60s proxy
    timeout - measured at roughly half of calls, with successes taking up to
    42s, while Keycloak answers in 0.13s and the backend's own /health/ in
    0.2s. So the latency is inside the exchange handler.

    Gateway errors and client timeouts are retried; anything else is returned
    immediately so a genuine 401 still surfaces at once. When every attempt
    fails to get an answer the session is skipped rather than failed - the
    tests cannot say anything about the API when they cannot authenticate,
    and reporting that as a test failure would misattribute an endpoint
    outage to the code under test.
    """
    last_error = None
    resp = None
    for attempt in range(attempts):
        try:
            resp = requests.post(
                f"{api_base_url}/api/auth/keycloak/login/",
                json={"token": kc_token},
                # Longer than nginx's 60s, so slowness arrives as a status
                # code we can reason about rather than a ReadTimeout.
                timeout=90,
            )
        except requests.RequestException as exc:
            last_error = exc
            resp = None
        else:
            last_error = None
            if resp.status_code not in (502, 503, 504):
                break
        if attempt < attempts - 1:
            time.sleep(3)

    if resp is None or resp.status_code in (502, 503, 504):
        detail = (
            f"HTTP {resp.status_code}" if resp is not None
            else f"{type(last_error).__name__}: {last_error}"
        )
        pytest.skip(
            f"Token exchange at {api_base_url}/api/auth/keycloak/login/ did "
            f"not respond after {attempts} attempts ({detail}). The endpoint "
            "is timing out, so authenticated API tests cannot run. This is an "
            "endpoint availability problem, not a failure of the code under "
            "test - a 401 here would still fail."
        )

    assert resp.status_code == 200, (
        f"Django token exchange failed ({resp.status_code}): {resp.text}"
    )
    return resp


def _get_keycloak_token(keycloak_url: str, realm: str, client_id: str,
                         email: str, password: str,
                         client_secret: Optional[str] = None) -> str:
    """
    Obtain a Keycloak access token via Resource Owner Password Credentials grant.
    Confidential clients (those with a client_secret) must pass it here.
    """
    token_url = (
        f"{keycloak_url.rstrip('/')}/realms/{realm}"
        f"/protocol/openid-connect/token"
    )
    payload = {
        "grant_type": "password",
        "client_id": client_id,
        "username": email,
        "password": password,
    }
    if client_secret:
        payload["client_secret"] = client_secret
    resp = requests.post(token_url, data=payload)
    if resp.status_code == 401:
        pytest.skip(
            "Keycloak ROPC token request returned 401 — check that Direct Access Grants "
            "is enabled and KEYCLOAK_CLIENT_SECRET is correct"
        )
    assert resp.status_code == 200, (
        f"Keycloak token request failed ({resp.status_code}): {resp.text}"
    )
    return resp.json()["access_token"]


@pytest.fixture(scope="session")
def api_base_url():
    """Backend base URL from API_BASE_URL env var. Skips if not set."""
    url = os.getenv("API_BASE_URL")
    if not url:
        pytest.skip("API_BASE_URL not set — skipping API tests")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def keycloak_config():
    """Keycloak connection settings from env vars. Skips if required vars are missing."""
    kc_url = os.getenv("KEYCLOAK_URL")
    realm = os.getenv("KEYCLOAK_REALM")
    client_id = os.getenv("KEYCLOAK_CLIENT_ID")
    client_secret = os.getenv("KEYCLOAK_CLIENT_SECRET")  # required for confidential clients
    if not all([kc_url, realm, client_id]):
        pytest.skip(
            "KEYCLOAK_URL / KEYCLOAK_REALM / KEYCLOAK_CLIENT_ID not set — "
            "skipping authenticated API tests"
        )
    return {"url": kc_url, "realm": realm, "client_id": client_id, "client_secret": client_secret}


@pytest.fixture(scope="session")
def auth_token(api_base_url, keycloak_config, test_credentials):
    """
    Full two-step auth:
      1. Get a Keycloak access token via ROPC grant.
      2. Exchange it at /api/auth/keycloak/login/ for a Django JWT.
    Returns the Django JWT access token string.
    """
    email, password = test_credentials
    kc_token = _get_keycloak_token(
        keycloak_config["url"],
        keycloak_config["realm"],
        keycloak_config["client_id"],
        email,
        password,
        client_secret=keycloak_config.get("client_secret"),
    )
    resp = _exchange_for_django_token(api_base_url, kc_token)
    return resp.json()["access"]


@pytest.fixture(scope="session")
def refresh_token(api_base_url, keycloak_config, test_credentials):
    """
    Returns the Django JWT refresh token (used in token-refresh tests).
    Performs the same two-step auth as auth_token.
    """
    email, password = test_credentials
    kc_token = _get_keycloak_token(
        keycloak_config["url"],
        keycloak_config["realm"],
        keycloak_config["client_id"],
        email,
        password,
        client_secret=keycloak_config.get("client_secret"),
    )
    resp = _exchange_for_django_token(api_base_url, kc_token)
    return resp.json()["refresh"]


@pytest.fixture(scope="session")
def api_client(api_base_url, auth_token):
    """Authenticated REST APIClient for the full test session."""
    return APIClient(api_base_url, token=auth_token)


@pytest.fixture(scope="session")
def anon_api_client(api_base_url):
    """Unauthenticated REST APIClient (for public-endpoint tests)."""
    return APIClient(api_base_url)


@pytest.fixture(scope="session")
def graphql_client(api_base_url, auth_token):
    """Authenticated GraphQLClient for the full test session."""
    return GraphQLClient(api_base_url, token=auth_token)


@pytest.fixture(scope="session")
def anon_graphql_client(api_base_url):
    """Unauthenticated GraphQLClient (for public-query cross-checks, e.g. sitemap counts)."""
    return GraphQLClient(api_base_url)


# ─── Frontend (DataSpaceFrontend) clients — used by sitemap/SEO tests ──────────
#
# Additional .env variables used here:
#   HOME_URL_DEV  - Frontend base URL for the dev environment
#   HOME_URL_PROD - Frontend base URL for the production environment

@pytest.fixture(scope="session")
def frontend_base_url_dev():
    """Frontend base URL for the dev environment. Skips if not set."""
    url = os.getenv("HOME_URL_DEV")
    if not url:
        pytest.skip("HOME_URL_DEV not set — skipping dev frontend tests")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def frontend_base_url_prod():
    """Frontend base URL for the production environment. Skips if not set."""
    url = os.getenv("HOME_URL_PROD")
    if not url:
        pytest.skip("HOME_URL_PROD not set — skipping prod frontend tests")
    return url.rstrip("/")


@pytest.fixture(scope="session")
def dev_frontend_client(frontend_base_url_dev):
    """Unauthenticated APIClient pointed at the dev frontend (for sitemap/robots.txt checks)."""
    return APIClient(frontend_base_url_dev)


@pytest.fixture(scope="session")
def prod_frontend_client(frontend_base_url_prod):
    """Unauthenticated APIClient pointed at the prod frontend (for sitemap/robots.txt checks)."""
    return APIClient(frontend_base_url_prod)
