# tests/api/smoke/test_api_054_export_urls.py
"""The URLs inside a metadata export must point at the environment that produced it."""

import pytest
import requests

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#211")]


# --- The URLs inside an export must point at the environment that produced it ---
#
# DataSpaceBackend#238: with PUBLIC_API_URL / PUBLIC_SITE_URL unset, the export
# falls back to https://api.civicdataspace.in, which does not resolve. The tests
# above only check the document's shape, so every download link was dead on dev
# and they stayed green. A failure here usually means the backend .env on the
# target box is missing those two variables.


@pytest.fixture(scope="module")
def dataset_with_resources_export(anon_graphql_client, anon_api_client):
    """DCAT JSON-LD export of a published dataset that has at least one resource."""
    rows = anon_graphql_client.query(
        "{ datasets(includePublic: true, pagination: {limit: 20}) { id resources { id } } }"
    )["datasets"]
    dataset_id = next((r["id"] for r in rows if r["resources"]), None)
    if not dataset_id:
        pytest.skip("no published dataset with resources on this backend to export")
    resp = anon_api_client.get(
        f"/api/datasets/{dataset_id}/export/",
        params={"standard": "dcat", "format": "jsonld"},
    )
    assert resp.status_code == 200, f"export returned {resp.status_code}: {resp.text}"
    return resp.json()


@pytest.mark.regression
def test_export_download_urls_resolve_on_this_backend(dataset_with_resources_export, api_base_url):
    """Every dcat:downloadURL is on the backend under test; the first few download."""
    dists = dataset_with_resources_export.get("dcat:distribution") or []
    urls = [d["dcat:downloadURL"]["@id"] for d in dists if d.get("dcat:downloadURL")]
    assert urls, f"export has no dcat:downloadURL: {dists}"
    for url in urls:
        assert url.startswith(f"{api_base_url}/"), (
            f"download URL {url} is not on the backend under test ({api_base_url})"
        )
    # A dataset can have hundreds of resources (327 on dev); fetching a few
    # proves the links resolve without a multi-minute download loop.
    for url in urls[:3]:
        try:
            resp = requests.get(url, stream=True, timeout=30)
            resp.close()
        except requests.RequestException as e:
            raise AssertionError(f"download URL {url} is unreachable: {e}") from e
        assert resp.status_code == 200, f"download URL {url} returned {resp.status_code}"


@pytest.mark.regression
def test_export_landing_page_is_on_this_frontend(dataset_with_resources_export, frontend_base_url_dev):
    """dcat:landingPage points at the frontend paired with this backend."""
    landing = (dataset_with_resources_export.get("dcat:landingPage") or {}).get("@id", "")
    assert landing.startswith(f"{frontend_base_url_dev}/"), (
        f"landing page {landing!r} is not on the frontend under test ({frontend_base_url_dev})"
    )
