# tests/api/smoke/test_api_001_health.py
#
# Verify the backend health endpoint responds without authentication.

import pytest


@pytest.mark.api
@pytest.mark.smoke
def test_health_check_returns_200(anon_api_client):
    """GET /health/ should return 200 without any auth token."""
    resp = anon_api_client.get("/health/")
    assert resp.status_code == 200, (
        f"Health check failed with status {resp.status_code}: {resp.text}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_health_check_response_is_json(anon_api_client):
    """GET /health/ response should be parseable JSON."""
    resp = anon_api_client.get("/health/")
    assert resp.status_code == 200
    # Should not raise
    body = resp.json()
    assert isinstance(body, dict), f"Expected dict response, got: {type(body)}"


@pytest.mark.api
@pytest.mark.smoke
def test_health_check_no_auth_required(anon_api_client):
    """Health endpoint must be publicly accessible (no 401/403)."""
    resp = anon_api_client.get("/health/")
    assert resp.status_code not in (401, 403), (
        "Health endpoint should not require authentication"
    )
