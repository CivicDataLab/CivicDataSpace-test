# tests/api/smoke/test_api_049_page_titles.py
#
# Every key page needs a non-empty <title> (WCAG 2.4.2), and detail pages should
# name the record they show, so two records of one kind have different titles.
# The titles are server-rendered, so plain HTTP is enough - no browser.
#
# Dataset and use case detail pages already do this. Collaborative and AI model
# detail pages use one generic title for every record (consumer issue C-016):
# those two cases assert the correct behaviour and are strict xfail, so CI stays
# green while the bug exists and goes red (XPASS) once it is fixed, at which
# point the marker has to come off.
#
# Records are picked at runtime from the public search API, never hardcoded.

import html
import re

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.regression, pytest.mark.readonly]

# search entity -> (frontend path template, record key in the search result)
DETAIL_ROUTES = {
    "dataset": ("/datasets/{}", "id"),
    "usecase": ("/usecases/{}", "id"),
    "collaborative": ("/collaboratives/{}", "slug"),
    "aimodel": ("/aimodels/{}", "id"),
}


def _title(frontend, path):
    resp = frontend.get(path)
    assert resp.status_code == 200, f"{path} -> {resp.status_code}"
    match = re.search(r"<title[^>]*>(.*?)</title>", resp.text, re.S | re.I)
    return html.unescape(match.group(1)).strip() if match else ""


@pytest.fixture(scope="module")
def detail_paths(anon_api_client):
    """Two detail-page paths per entity, from live search results."""
    paths = {}
    for entity, (template, key) in DETAIL_ROUTES.items():
        resp = anon_api_client.get(f"/api/search/{entity}/", params={"size": 2})
        assert resp.status_code == 200, f"{entity} search -> {resp.status_code}"
        keys = [r[key] for r in resp.json()["results"] if r.get(key) is not None]
        if len(keys) < 2:
            pytest.skip(f"fewer than two {entity} records with a {key} on this environment")
        paths[entity] = [template.format(k) for k in keys[:2]]
    return paths


@pytest.mark.parametrize("entity", [None, *DETAIL_ROUTES])
def test_page_title_is_not_empty(dev_frontend_client, detail_paths, entity):
    """Home and one detail page of each kind carry a non-empty <title>."""
    path = "/" if entity is None else detail_paths[entity][0]
    assert _title(dev_frontend_client, path), f"{path} has an empty or missing <title>"


def _generic(issue):
    return pytest.mark.xfail(
        strict=True, reason=f"consumer issue {issue}: every record shares one generic <title>"
    )


@pytest.mark.parametrize(
    "entity",
    [
        "dataset",
        "usecase",
        pytest.param("collaborative", marks=_generic("C-016")),
        pytest.param("aimodel", marks=_generic("C-016")),
    ],
)
def test_detail_titles_differ_between_records(dev_frontend_client, detail_paths, entity):
    """Two different records of one kind must not share a page title."""
    first, second = (_title(dev_frontend_client, p) for p in detail_paths[entity])
    assert first != second, f"{entity} pages {detail_paths[entity]} share the title {first!r}"
