# tests/api/smoke/test_api_052_event_search.py
#
# Covers DataSpaceBackend#270 (feat(api): add event search with filters and
# pagination), together with the two follow-up fixes it needed to actually
# work on a real deploy: #271 (create the `event` index on deploy, before
# populate) and #272 (one-time repair of an index guessed by Elasticsearch
# on the first, broken deploy). `/api/search/event/` returned 500 on dev
# between #270 and #271/#272 landing - see those PRs' bodies.
#
# Both tests pick their target record(s) from the live, unfiltered listing at
# runtime - never a hardcoded location or id - and require each filter to
# genuinely narrow the result set (some, not all, not none), per the
# "flipping the expected value is not enough" lesson from
# CivicDataSpace-test#150.
#
# Unauthenticated and read-only: both endpoints are public GETs, no
# credentials needed, no mutation performed.
#
# `readonly` + `deployed_pr`: confirmed via `git merge-base --is-ancestor
# <merge-sha> origin/main` in DataSpaceBackend that none of #270/#271/#272
# have reached main/prod yet (prod's /api/search/event/ returns 404 - checked
# live, see PR body). Gated on #272, the latest of the three and the one
# whose migration depends on the others already being in place, so the gate
# turns itself on only once the whole stack is actually deployed. Safe to
# merge into CI now.

from datetime import datetime, timezone

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#272")]


@pytest.fixture(scope="module")
def event_baseline(anon_api_client):
    """Unfiltered /api/search/event/ listing - the 'total' baseline and the
    pool to pick a genuinely-narrowing filter value from."""
    resp = anon_api_client.get("/api/search/event/", params={"size": 200})
    assert resp.status_code == 200, (
        f"baseline event search failed ({resp.status_code}): {resp.text}"
    )
    body = resp.json()
    if not body.get("results"):
        pytest.skip("no published events on this environment to search over")
    return body


@pytest.mark.smoke
def test_search_event_location_filter_narrows_results(anon_api_client, event_baseline):
    """?location=<value> must return only events at that location, and must
    narrow the result set (ruling out the filter being silently ignored and
    the endpoint just echoing everything back, which is what a 500-turned-
    empty-index would also have hidden).
    """
    baseline_results = event_baseline["results"]
    baseline_total = event_baseline["total"]

    by_location = {}
    for r in baseline_results:
        loc = r.get("location")
        if loc:
            by_location.setdefault(loc, []).append(r["id"])

    # Pick the rarest location that is not every event's location, so the
    # narrowing assertion (0 < filtered < total) can't pass by accident.
    candidates = {loc: ids for loc, ids in by_location.items() if len(ids) < baseline_total}
    if not candidates:
        pytest.skip(
            "every event on this environment shares the same location (or has "
            "none) - nothing to narrow against"
        )
    location, expected_ids = min(candidates.items(), key=lambda kv: len(kv[1]))

    resp = anon_api_client.get("/api/search/event/", params={"location": location, "size": 200})
    assert resp.status_code == 200, f"location search failed ({resp.status_code}): {resp.text}"
    body = resp.json()
    filtered_ids = {r["id"] for r in body["results"]}
    filtered_total = body["total"]

    assert set(expected_ids) <= filtered_ids, (
        f"location={location!r} did not return event id(s) {expected_ids}, "
        f"which the unfiltered listing reports at that location"
    )
    for r in body["results"]:
        assert r["location"] == location, (
            f"location={location!r} returned event {r['id']} at location "
            f"{r['location']!r} - filter leaked a non-matching row"
        )
    assert 0 < filtered_total < baseline_total, (
        f"location={location!r} returned {filtered_total} of {baseline_total} "
        f"total - expected a real subset, not everything or nothing"
    )


@pytest.mark.smoke
def test_search_event_timeframe_filter_separates_upcoming_from_past(
    anon_api_client, event_baseline
):
    """?timeframe=upcoming (not ended yet) and ?timeframe=past (already
    ended) must each narrow the baseline, and must not overlap: an event
    can't be both upcoming and past at once.
    """
    baseline_results = event_baseline["results"]
    baseline_total = event_baseline["total"]

    today = datetime.now(timezone.utc).date()

    def _event_date(r):
        """Mirror the view's own rule: end_date, falling back to start_date."""
        raw = r.get("end_date") or r.get("start_date")
        if not raw:
            return None
        return datetime.strptime(raw, "%Y-%m-%d").date()

    upcoming_ids = {r["id"] for r in baseline_results if (_event_date(r) or today) >= today}
    past_ids = {r["id"] for r in baseline_results if (_event_date(r) or today) < today}

    if not (0 < len(upcoming_ids) < baseline_total) and not (0 < len(past_ids) < baseline_total):
        pytest.skip(
            "every dated event on this environment falls on the same side of "
            "today - nothing to narrow upcoming vs. past against"
        )

    resp_upcoming = anon_api_client.get(
        "/api/search/event/", params={"timeframe": "upcoming", "size": 200}
    )
    resp_past = anon_api_client.get("/api/search/event/", params={"timeframe": "past", "size": 200})
    assert resp_upcoming.status_code == 200, (
        f"timeframe=upcoming failed ({resp_upcoming.status_code}): {resp_upcoming.text}"
    )
    assert resp_past.status_code == 200, (
        f"timeframe=past failed ({resp_past.status_code}): {resp_past.text}"
    )
    upcoming_body = resp_upcoming.json()
    past_body = resp_past.json()
    got_upcoming_ids = {r["id"] for r in upcoming_body["results"]}
    got_past_ids = {r["id"] for r in past_body["results"]}

    assert upcoming_ids <= got_upcoming_ids, (
        f"timeframe=upcoming is missing {upcoming_ids - got_upcoming_ids}, which "
        f"the baseline's own dates place today ({today}) or later"
    )
    assert past_ids <= got_past_ids, (
        f"timeframe=past is missing {past_ids - got_past_ids}, which the "
        f"baseline's own dates place before today ({today})"
    )
    assert not (got_upcoming_ids & got_past_ids), (
        f"timeframe=upcoming and timeframe=past both returned "
        f"{got_upcoming_ids & got_past_ids} - an event can't be both"
    )
    # At least one side must be a genuine, non-vacuous subset.
    assert upcoming_body["total"] < baseline_total or past_body["total"] < baseline_total, (
        "neither timeframe filter narrowed the baseline at all"
    )


@pytest.mark.smoke
def test_unified_search_counts_events_by_default(anon_api_client, event_baseline):
    """/api/search/unified/ with no `types` param must include `event` in its
    per-type aggregation, matching /api/search/event/'s own total. Before
    #270, `event` was not in the default type list (or the index) at all, so
    this key would be entirely absent.
    """
    resp = anon_api_client.get("/api/search/unified/", params={"size": 1})
    assert resp.status_code == 200, f"unified search failed ({resp.status_code}): {resp.text}"
    body = resp.json()
    type_counts = body.get("aggregations", {}).get("types", {})

    assert "event" in type_counts, (
        f"unified search's default type aggregation has no 'event' key - "
        f"got {sorted(type_counts)}"
    )
    assert type_counts["event"] == event_baseline["total"], (
        f"unified search counts {type_counts['event']} events, but "
        f"/api/search/event/ itself reports {event_baseline['total']}"
    )
