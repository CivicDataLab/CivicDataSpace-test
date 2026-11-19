# tests/api/smoke/test_api_041_event_search_cover.py
#
# Covers DataSpaceBackend#275 (merge commit f2f18c357d596c2fe750f38d64d9e2d116a47fb6):
# /api/search/event/ (and unified search's "event" results) gained a
# `cover_url` field — the event's cover image pulled live from Luma, or null
# when the event has no Luma embed / Luma has no cover / Luma could not be
# reached. Nothing before this PR exposed any image for an event in search
# results at all.
#
# The whole /api/search/event/ endpoint does not exist on prod yet (the
# Events feature itself hasn't shipped to main), so prod gives a clean,
# genuine "before" state: a 404 on the endpoint. Marked `readonly` +
# `deployed_pr` so it skips on prod until the deploy serves this commit, and
# turns itself on automatically once it does.

import re

import pytest

_COVER_URL_RE = re.compile(r"^https://images\.lumacdn\.com/")


@pytest.fixture(scope="module")
def event_baseline(anon_api_client):
    """Unfiltered /api/search/event/ listing — the pool to find a real
    event with (and one without) a Luma cover from."""
    resp = anon_api_client.get("/api/search/event/", params={"size": 200})
    assert resp.status_code == 200, (
        f"event search failed ({resp.status_code}): {resp.text}"
    )
    body = resp.json()
    results = body.get("results", [])
    if not results:
        pytest.skip("no published events on this environment to search over")
    return results


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#275")
def test_event_search_exposes_cover_url_field(event_baseline):
    """Every event result carries a `cover_url` key (null is fine, missing
    is not) — the field genuinely exists in the response now."""
    for event in event_baseline:
        assert "cover_url" in event, (
            f"event {event.get('id')!r} ({event.get('name')!r}) has no "
            "cover_url key in its search result at all"
        )


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#275")
def test_event_with_luma_cover_returns_a_real_lumacdn_url(event_baseline):
    """At least one event's cover_url is a genuine, absolute
    https://images.lumacdn.com/... URL — not a placeholder, not the embed
    URL itself, not a bare path."""
    covers = [e["cover_url"] for e in event_baseline if e.get("cover_url")]
    if not covers:
        pytest.skip(
            "no event on this environment currently has a resolvable Luma "
            "cover (none has a Luma embed, or Luma has no image for any of "
            "them right now) — nothing to assert the URL shape on"
        )
    for cover in covers:
        assert _COVER_URL_RE.match(cover), (
            f"cover_url {cover!r} is not an absolute images.lumacdn.com URL"
        )


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#275")
def test_unified_search_event_results_also_carry_cover_url(anon_api_client, event_baseline):
    """The same field is wired into unified search's event branch, not just
    the dedicated event-search endpoint (search_unified.py's
    `result.setdefault("cover_url", None)` + the UserSerializer field)."""
    resp = anon_api_client.get(
        "/api/search/unified/", params={"types": "event", "size": 50}
    )
    assert resp.status_code == 200, (
        f"unified search failed ({resp.status_code}): {resp.text}"
    )
    results = [r for r in resp.json().get("results", []) if r.get("type") == "event"]
    if not results:
        pytest.skip("unified search returned no event-type results to check")
    for event in results:
        assert "cover_url" in event, (
            f"unified search event result {event.get('id')!r} is missing "
            "cover_url"
        )
