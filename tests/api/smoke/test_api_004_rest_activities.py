# tests/api/smoke/test_api_004_rest_activities.py
#
# Verify the activity stream endpoints respond correctly.
# Both activity feeds require authentication: the global feed lists all platform
# activity, drafts included (DataSpaceBackend#302, decided by the backend team).

import pytest

pytestmark = pytest.mark.readonly


@pytest.mark.api
@pytest.mark.regression
def test_global_activities_requires_auth(anon_api_client):
    """GET /api/activities/global/ without a token must return 401 or 403."""
    resp = anon_api_client.get("/api/activities/global/")
    assert resp.status_code in (401, 403), (
        f"Expected 401/403 for unauthenticated global activities, got {resp.status_code}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_global_activities_returns_200_when_authenticated(api_client):
    """The refusal above is about the missing token: a signed-in caller reads the feed."""
    resp = api_client.get("/api/activities/global/")
    assert resp.status_code == 200, (
        f"Global activities failed ({resp.status_code}): {resp.text[:200]}"
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
