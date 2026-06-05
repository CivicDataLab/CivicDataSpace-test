# tests/api/smoke/test_api_003_rest_search.py
#
# Verify the Elasticsearch-backed search endpoints respond correctly.
# Search endpoints are publicly accessible (no auth required).

import pytest


@pytest.mark.api
@pytest.mark.smoke
def test_search_datasets_returns_200(anon_api_client):
    """GET /api/search/dataset/ should return 200."""
    resp = anon_api_client.get("/api/search/dataset/")
    assert resp.status_code == 200, (
        f"Dataset search failed ({resp.status_code}): {resp.text}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_search_datasets_response_structure(anon_api_client):
    """Dataset search response should be a JSON object (dict or list)."""
    resp = anon_api_client.get("/api/search/dataset/")
    assert resp.status_code == 200
    body = resp.json()
    assert isinstance(body, (dict, list)), (
        f"Unexpected response type: {type(body)}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_search_datasets_with_query_param(anon_api_client):
    """Dataset search with a ?q= query param should still return 200."""
    resp = anon_api_client.get("/api/search/dataset/", params={"q": "test"})
    assert resp.status_code == 200, (
        f"Dataset search with query param failed ({resp.status_code}): {resp.text}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_search_usecases_returns_200(anon_api_client):
    """GET /api/search/usecase/ should return 200."""
    resp = anon_api_client.get("/api/search/usecase/")
    assert resp.status_code == 200, (
        f"Usecase search failed ({resp.status_code}): {resp.text}"
    )


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.xfail(reason="Backend Elasticsearch InnerDoc serialization error on /api/search/aimodel/ (500)")
def test_search_aimodels_returns_200(anon_api_client):
    """GET /api/search/aimodel/ should return 200."""
    resp = anon_api_client.get("/api/search/aimodel/")
    assert resp.status_code == 200, (
        f"AI model search failed ({resp.status_code}): {resp.text}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_search_unified_returns_200(anon_api_client):
    """GET /api/search/unified/ should return 200."""
    resp = anon_api_client.get("/api/search/unified/")
    assert resp.status_code == 200, (
        f"Unified search failed ({resp.status_code}): {resp.text}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_search_publishers_returns_200(anon_api_client):
    """GET /api/search/publisher/ should return 200."""
    resp = anon_api_client.get("/api/search/publisher/")
    assert resp.status_code == 200, (
        f"Publisher search failed ({resp.status_code}): {resp.text}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_trending_datasets_returns_200(anon_api_client):
    """GET /api/trending/datasets/ should return 200."""
    resp = anon_api_client.get("/api/trending/datasets/")
    assert resp.status_code == 200, (
        f"Trending datasets failed ({resp.status_code}): {resp.text}"
    )
