# tests/api/smoke/test_api_001_health.py
#
# Verify the backend health endpoint responds without authentication.

import os

import pytest

pytestmark = pytest.mark.readonly


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


@pytest.mark.api
@pytest.mark.smoke
def test_health_check_deployed_sha_matches(anon_api_client):
    """
    When EXPECTED_DEPLOYED_SHA is set (a CD pipeline verifying its own
    deploy), assert the live git_sha matches the commit that was just
    pushed -- proves the running code is actually the new code, not just
    that *a* container answered. Skips (not a silent pass) when unset,
    e.g. for ad-hoc/local runs with no specific commit to check against.
    """
    expected_sha = os.getenv("EXPECTED_DEPLOYED_SHA")
    if not expected_sha:
        pytest.skip("EXPECTED_DEPLOYED_SHA not set — skipping deployed-SHA check")

    resp = anon_api_client.get("/health/")
    assert resp.status_code in (200, 503), (
        f"Health check returned unexpected status {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    actual_sha = body.get("git_sha")
    assert actual_sha == expected_sha, (
        f"Deployed git_sha {actual_sha!r} does not match expected {expected_sha!r} "
        "-- the live container may be running stale code"
    )
