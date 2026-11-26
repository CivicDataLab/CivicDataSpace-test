# tests/api/smoke/test_api_075_unified_search_publications.py
#
# DataSpaceBackend#330: unified search 500'd whenever a publication was in the
# results -- always with types=publication, and with several types as soon as
# a publication ranked onto the page (e.g. query=publish). Publication search
# documents have no `tags` field, and every unified result needs one;
# `_normalize_result` only filled defaults for events and publishers before
# #330. Fixed: publication hits get `tags: []`, and an empty title/description
# when missing, the same way event results already do.
#
#   GET /api/search/unified/
#
# Unauthenticated and read-only -- published publications are public -- so
# this is readonly-safe and runs in the prod gate too, once #330 reaches
# main. `deployed_pr` skips it wherever the backend under test doesn't serve
# #330 yet: on dev until the (currently failed) deploy succeeds, and on prod
# until the fix is promoted there.
#
# test_api_003_rest_search.py's test_search_unified_returns_200 hits the same
# endpoint with no params, so it only reproduces the bug if a publication
# happens to be on that unfiltered first page -- it isn't a reliable
# reproduction. types=publication alone 500s unconditionally (verified live
# against dev pre-fix, see PR body), so that's the test that actually proves
# the fix.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#330")]


@pytest.mark.smoke
def test_unified_search_types_publication_does_not_500(anon_api_client):
    """The reliable reproduction: types=publication alone was enough to 500,
    whether or not any publication actually matched the rest of the query.
    """
    resp = anon_api_client.get("/api/search/unified/", params={"types": "publication"})
    assert resp.status_code == 200, (
        f"unified search with types=publication failed ({resp.status_code}): {resp.text[:300]}"
    )
    body = resp.json()
    assert isinstance(body.get("results"), list), body


@pytest.mark.regression
def test_a_publication_result_carries_an_empty_tags_list_and_its_slug(anon_api_client):
    """Every publication result carries the `tags: []` the serializer
    requires (publication documents have no tags field at all), and the
    `url_slug` the frontend links through to /publications/<url_slug> (PR
    body).
    """
    resp = anon_api_client.get("/api/search/unified/", params={"types": "publication", "size": 20})
    assert resp.status_code == 200, f"{resp.status_code}: {resp.text[:300]}"
    publications = [r for r in resp.json().get("results", []) if r.get("type") == "publication"]
    if not publications:
        pytest.skip("no published publication on this backend to check the shape of")
    for row in publications:
        assert row.get("tags") == [], row
        assert row.get("url_slug"), row


@pytest.mark.regression
def test_unified_search_with_mixed_types_does_not_500_once_a_publication_ranks_in(anon_api_client):
    """The PR body's second failure mode: several types together, a
    publication ranking onto the page by relevance rather than by filter --
    query=publish is the PR's own example. If this backend's data doesn't
    rank a publication in for this word, this only shows the endpoint is
    healthy, not that a mixed page with one on it works; the types=publication
    test above is the test that reliably reproduces the bug either way.
    """
    resp = anon_api_client.get("/api/search/unified/", params={"query": "publish"})
    assert resp.status_code == 200, (
        f"unified search for 'publish' failed ({resp.status_code}): {resp.text[:300]}"
    )
