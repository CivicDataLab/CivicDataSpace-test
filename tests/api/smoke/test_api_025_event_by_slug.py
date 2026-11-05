# tests/api/smoke/test_api_025_event_by_slug.py
#
# Covers the eventBySlug GraphQL query used by the public event detail page
# (DataSpaceFrontend#515, #516, #517 — "Implement event management").
#
# #516 renamed the query's variable from `slug` to `publicId` to match the
# backend's actual argument name; #515 shipped the page that calls it, #517
# is an unrelated image-component follow-up on the same branch. All three
# merged into dev within the same hour, so they are covered together here.
#
# Not marked `readonly`: the Event feature is not on main/prod yet (verified
# live — see the PR body). Leaving the marker off means this file is simply
# excluded from the prod gate (readonly is opt-in per pytest.ini), so no
# deployed_pr gating is needed.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke]

EVENT_BY_SLUG_QUERY = """
query($publicId: String!) {
  eventBySlug(publicId: $publicId) {
    id
    name
    urlSlug
  }
}
"""

# The pre-#516 shape: the frontend used to send the variable as `slug`,
# which the schema has never accepted under that name.
LEGACY_SLUG_QUERY = """
query($slug: String!) {
  eventBySlug(slug: $slug) {
    id
    name
  }
}
"""


@pytest.fixture(scope="module")
def published_event_slug(anon_api_client):
    """A real published event's url_slug, read live so this doesn't rot.

    The frontend links to /events/<url_slug> and the detail page then
    queries eventBySlug(publicId: <that same url_slug>).
    """
    resp = anon_api_client.session.get(
        f"{anon_api_client.base_url}/api/search/event/",
        params={"page": 1, "size": 20, "sort": "start_date", "order": "asc"},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"GET /api/search/event/ failed ({resp.status_code}): {resp.text[:300]}"
    )
    results = resp.json().get("results", [])
    for event in results:
        if event.get("url_slug"):
            return event["url_slug"]
    pytest.skip("No published event with a url_slug on dev — nothing to query")


def test_event_by_slug_resolves_with_public_id_argument(
    anon_graphql_client, published_event_slug
):
    """eventBySlug(publicId: ...) must resolve a real event with no errors.

    This is the current, correct call shape (post-#516).
    """
    data = anon_graphql_client.query(
        EVENT_BY_SLUG_QUERY, {"publicId": published_event_slug}
    )
    event = data.get("eventBySlug")
    assert event is not None, (
        f"eventBySlug(publicId={published_event_slug!r}) returned null for a "
        "url_slug just read from the live event search results"
    )
    assert event["urlSlug"] == published_event_slug


@pytest.mark.regression
def test_event_by_slug_unknown_id_returns_null_not_error(anon_graphql_client):
    """A slug that doesn't exist must resolve to null, not a GraphQL error.

    The detail page relies on this to render its own 404 (`notFound()`)
    instead of crashing on an unhandled GraphQL error.
    """
    data = anon_graphql_client.query(
        EVENT_BY_SLUG_QUERY, {"publicId": "does-not-exist-test-sync-probe"}
    )
    assert data.get("eventBySlug") is None


@pytest.mark.regression
def test_event_by_slug_rejects_the_pre_fix_slug_argument(
    anon_graphql_client, published_event_slug
):
    """Simulates reverting #516: calling with `slug` instead of `publicId`.

    Before #516 the frontend's generated query used `slug` as the variable
    name. The schema has only ever accepted `publicId`, so that shape fails
    GraphQL validation outright — this is the "red" state #516 fixed.
    """
    response = anon_graphql_client.session.post(
        anon_graphql_client.endpoint,
        json={
            "query": LEGACY_SLUG_QUERY,
            "variables": {"slug": published_event_slug},
        },
        timeout=30,
    )
    body = response.json()
    assert "errors" in body, (
        "Expected the legacy `slug` argument to be rejected by the schema, "
        f"got: {body}"
    )
    messages = " ".join(e.get("message", "") for e in body["errors"])
    assert "publicId" in messages or "slug" in messages, (
        f"Expected the error to name the argument mismatch, got: {messages}"
    )
