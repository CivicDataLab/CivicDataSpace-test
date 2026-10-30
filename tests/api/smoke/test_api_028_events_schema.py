# tests/api/smoke/test_api_028_events_schema.py
#
# Covers DataSpaceBackend#263 (merge commit 11a0f8d56161e779c3a2122c3ae600a85e04165e):
# a new Event model and GraphQL schema for event management (publishedEvents,
# eventsTable, event, createEvent/updateEvent/publishEvent/unpublishEvent/deleteEvent).
#
# Written by the cloud routine with no TEST_EMAIL_n/TEST_PASSWORD_n available,
# so both tests here are unauthenticated-only. Two behaviours proven live
# against dev on 2026-10-30:
#
#   - `publishedEvents` is a public, world-readable query. Before #263 the
#     field didn't exist at all: querying it against prod today returns
#     "Cannot query field 'publishedEvents' on type 'Query'." — a real red.
#   - `createEvent` enforces CreateEventPermission: an anonymous caller is
#     refused and nothing is created.
#     {"success": false, "errors": {"nonFieldErrors": ["You don't have
#     permission to create an event"]}}, and publishedEvents.totalItemsCount
#     stayed 0 before and after the probe.
#
# Not covered here (needs TEST_EMAIL_n/TEST_PASSWORD_n, unavailable to this
# cloud run): authenticated create/update/publish/delete flows, the
# organization-scoped `eventsTable` for a logged-in provider, and the
# AllowPublishedEvents draft-hides-from-outsiders path (no draft event exists
# on dev yet — publishedEvents.totalItemsCount was 0 at write time, so there
# is nothing to assert "excludes" against beyond the empty-list case covered
# below). A human with credentials should add those. UNVERIFIED — not
# executed, no credentials in this environment.
#
# `test_published_events_is_public_and_excludes_drafts` only queries, so it
# carries `readonly` and is safe in the prod gate once DataSpaceBackend#263
# reaches `main` (gated by `deployed_pr` until then).
# `test_anonymous_cannot_create_event` sends a mutation and is deliberately
# NOT marked readonly, so it never runs in the prod gate — DataSpaceBackend#263
# is not on `main` yet and prod's schema has no `createEvent` field at all;
# a mutation is never sent to prod regardless of the expected outcome.

import pytest

PUBLISHED_EVENTS_QUERY = (
    "{ publishedEvents(limit:10){ totalItemsCount data { id name status } } }"
)


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#263")
def test_published_events_is_public_and_excludes_drafts(anon_graphql_client):
    """
    `publishedEvents` must answer with no token, and every row it returns
    must be PUBLISHED — event_service.get_scoped_events / published_events
    filter anonymous callers to status=EventStatus.PUBLISHED, and a resolver
    that dropped that filter would leak drafts here.
    """
    data = anon_graphql_client.query(PUBLISHED_EVENTS_QUERY)["publishedEvents"]
    assert isinstance(data["totalItemsCount"], int) and data["totalItemsCount"] >= 0, data
    for event in data["data"]:
        assert event["status"] == "PUBLISHED", f"publishedEvents leaked a non-published event: {event}"


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.regression
@pytest.mark.deployed_pr("DataSpaceBackend#263")
def test_anonymous_cannot_create_event(anon_graphql_client):
    """
    CreateEventPermission must refuse an anonymous caller and create
    nothing. A resolver that forgot the permission check would return
    success=true and a new id instead.

    This cloud run has no dev credentials and never mutates the live
    deployment to force a failure, so the red side of this proof is the
    inverted assertion: `assert payload["success"] is False` fails at this
    exact line if flipped to `is True`, because the server's real answer is
    False — that divergence is what makes the check non-vacuous.
    """
    mutation = (
        "mutation($i: CreateEventInput!){ createEvent(input:$i){ "
        "success errors { nonFieldErrors } data { id } } }"
    )
    payload = anon_graphql_client.query(
        mutation, {"i": {"name": "api-test anon-probe"}}
    )["createEvent"]
    assert payload["success"] is False, f"anonymous createEvent should be refused: {payload}"
    assert payload["data"] is None, f"anonymous createEvent should create nothing: {payload}"
    assert payload["errors"]["nonFieldErrors"] == [
        "You don't have permission to create an event"
    ], payload["errors"]
