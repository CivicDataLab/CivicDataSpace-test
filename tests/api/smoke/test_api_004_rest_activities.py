# tests/api/smoke/test_api_004_rest_activities.py
#
# Verify the activity stream endpoints respond correctly.
# Global activities are public; user activities require authentication.

import pytest


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.xfail(reason="/api/activities/global/ currently requires auth on dev (should be public)")
def test_global_activities_returns_200(anon_api_client):
    """GET /api/activities/global/ should return 200 without authentication."""
    resp = anon_api_client.get("/api/activities/global/")
    assert resp.status_code == 200, (
        f"Global activities failed ({resp.status_code}): {resp.text}"
    )


@pytest.mark.api
@pytest.mark.regression
@pytest.mark.xfail(reason="/api/activities/global/ currently requires auth on dev (should be public)")
def test_global_activities_response_is_list_or_dict(anon_api_client):
    """Global activities response should be a JSON list or dict."""
    resp = anon_api_client.get("/api/activities/global/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, (dict, list)), (
        f"Unexpected response type: {type(body)}"
    )


@pytest.mark.api
@pytest.mark.regression
def test_user_activities_requires_auth(anon_api_client):
    """GET /api/activities/user/ without a token must return 401 or 403."""
    resp = anon_api_client.get("/api/activities/user/")
    assert resp.status_code in (401, 403), (
        f"Expected 401/403 for unauthenticated user activities, got {resp.status_code}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_user_activities_returns_200_when_authenticated(api_client):
    """GET /api/activities/user/ with a valid token should return 200."""
    resp = api_client.get("/api/activities/user/")
    assert resp.status_code == 200, (
        f"User activities failed ({resp.status_code}): {resp.text}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_user_activities_response_is_list_or_dict(api_client):
    """Authenticated user activities response should be a JSON list or dict."""
    resp = api_client.get("/api/activities/user/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, (dict, list)), (
        f"Unexpected response type: {type(body)}"
    )
