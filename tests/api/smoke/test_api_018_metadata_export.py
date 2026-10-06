# tests/api/smoke/test_api_018_metadata_export.py
#
# Covers DataSpaceBackend#211: per-dataset metadata export as DCAT, Croissant
# or Dublin Core, plus the options endpoint that lists them.
#
#   GET /api/metadata/export-options/
#   GET /api/datasets/<id>/export/?standard=<standard>&format=<format>
#
# Both are unauthenticated and read-only -- published datasets are exportable
# by anyone -- so this is readonly-safe. `readonly` + `deployed_pr` lets it
# merge now: it's skipped wherever the backend under test doesn't serve #211
# yet (prod, until the feature reaches main), and switches on by itself once
# it does, exactly like test_api_013_datasets_table.py did for #215.
#
# Not covered here (left for a credentialed, authenticated run): exporting a
# caller's own DRAFT dataset, and the `report=1` unmapped-field report.

import uuid

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#211")]


@pytest.fixture(scope="module")
def published_dataset_id(anon_graphql_client):
    """id of any published dataset on the target backend, read live."""
    # `datasets`, not `datasetsTable` (#215): it exists on every backend, so on one
    # without #211 the tests below fail at their own assertions, not in setup.
    rows = anon_graphql_client.query(
        "{ datasets(includePublic: true, pagination: {limit: 1}) { id } }"
    )["datasets"]
    if not rows:
        pytest.skip("no published dataset on this backend to export")
    return rows[0]["id"]


@pytest.mark.smoke
def test_export_options_lists_the_three_standards(anon_api_client):
    """`export-options` names dcat/croissant/dublin_core, Croissant JSON-LD only.

    Pre-#211 this path doesn't exist at all (404, see PR body / Gotchas): a
    regression that removed the view would show up the same way.
    """
    resp = anon_api_client.get("/api/metadata/export-options/")
    assert resp.status_code == 200, f"export-options returned {resp.status_code}: {resp.text}"
    standards = resp.json().get("standards", {})
    assert set(standards) == {"dcat", "croissant", "dublin_core"}, sorted(standards)
    assert standards["croissant"]["formats"] == ["jsonld"], (
        f"Croissant is documented as JSON-LD only, got {standards['croissant']['formats']}"
    )
    for name in ("dcat", "dublin_core"):
        assert "jsonld" in standards[name]["formats"], standards[name]


@pytest.mark.functional
def test_export_of_a_published_dataset_is_valid_dcat_jsonld(anon_api_client, published_dataset_id):
    """A real published dataset exports as a DCAT JSON-LD document naming it.

    Checks the mapping actually ran on real data, not just that the endpoint
    answers: the identifier must be *this* dataset's id, title must be
    non-empty, and the DCAT type/context must be present.
    """
    resp = anon_api_client.get(
        f"/api/datasets/{published_dataset_id}/export/",
        params={"standard": "dcat", "format": "jsonld"},
    )
    assert resp.status_code == 200, f"export returned {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("@type") == "dcat:Dataset", body
    assert body.get("dcterms:identifier") == published_dataset_id, body
    assert isinstance(body.get("dcterms:title"), str) and body["dcterms:title"].strip(), body


@pytest.mark.regression
def test_export_of_an_unknown_dataset_is_a_json_404_not_a_route_404(anon_api_client):
    """An unknown id 404s from the *view* (JSON body), not from a missing route.

    The distinction is the regression this guards: if the export route were
    ever removed, nginx/Django's own 404 comes back as `text/html` with no
    'error' key -- observed live on a backend that doesn't have #211 at all.
    A dataset genuinely not found must look different from the route itself
    being gone.
    """
    resp = anon_api_client.get(
        f"/api/datasets/{uuid.uuid4()}/export/",
        params={"standard": "dcat", "format": "jsonld"},
    )
    assert resp.status_code == 404, resp.status_code
    assert "json" in resp.headers.get("Content-Type", ""), (
        f"expected the export view's own JSON 404, got Content-Type "
        f"{resp.headers.get('Content-Type')!r} (looks like the route itself is missing)"
    )
    assert "error" in resp.json(), resp.text


@pytest.mark.regression
def test_export_rejects_an_unknown_standard(anon_api_client, published_dataset_id):
    """A standard outside the three documented ones is a client error, not a 500."""
    resp = anon_api_client.get(
        f"/api/datasets/{published_dataset_id}/export/",
        params={"standard": "not_a_real_standard", "format": "jsonld"},
    )
    assert resp.status_code == 400, (
        f"expected a 400 for an unknown standard, got {resp.status_code}: {resp.text}"
    )
