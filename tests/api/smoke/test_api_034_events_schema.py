# tests/api/smoke/test_api_034_events_schema.py
#
# Covers DataSpaceBackend#263 (merge commit 11a0f8d56161e779c3a2122c3ae600a85e04165e):
# a new Event model and GraphQL schema for event management (publishedEvents,
# eventsTable, event, createEvent/updateEvent/publishEvent/unpublishEvent/deleteEvent).
#
# Written by the cloud routine with no TEST_EMAIL_n/TEST_PASSWORD_n available,
# so the first two tests are unauthenticated-only. Two behaviours proven live
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
# The authenticated flows (create/update/publish/delete, eventsTable scoping,
# AllowPublishedEvents' draft branch) were added afterwards with real
# credentials; see the section at the bottom of this file. On an empty dev,
# the publishedEvents check below only proves the field exists and is public;
# test_draft_is_private_until_published is what proves drafts stay out.
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


# ─── Authenticated flows (added locally with TEST_EMAIL_3, 2026-10-30) ─────────
#
# Account 3 is admin of "test org name" (see org_add_permission in conftest.py;
# re-check before trusting). Every event is created as a draft and deleted in
# teardown. Writes to dev only: none of these are readonly.
#
# Not covered: an authenticated outsider (a logged-in non-member) reading or
# changing another account's draft. That needs a second account as creator;
# the anonymous branch of AllowPublishedEvents is covered below.

from tests.api import publications as pub  # noqa: E402  (generic gql/mutate/errors helpers)

ORG = "test org name"
EVENT_FIELDS = "id name status isIndividualEvent organization { slug }"
EVENT_RESULT = "success errors { fieldErrors { field messages } nonFieldErrors } data { %s }" % EVENT_FIELDS
COMPLETE = {
    "location": "Online",
    "startDate": "2030-01-01",
    "endDate": "2030-01-02",
    "lumaEmbed": "https://lu.ma/embed/event/evt-apitest/simple",
}
# Newest-modified first by default, so a just-created event is on the first page.
TABLE = "{ eventsTable(limit: 100) { data { id } } }"


def _create(client, org=None, **fields):
    payload = pub.mutate(
        client, "createEvent",
        "mutation($i: CreateEventInput!){ createEvent(input:$i){ %s } }" % EVENT_RESULT,
        {"i": {"name": pub.unique_title("api-test event"), **fields}}, org,
    )
    assert payload["success"], f"createEvent failed: {payload['errors']}"
    return payload["data"]


def _by_id(name, event_id, org=None):
    return lambda client: pub.mutate(
        client, name,
        "mutation($id: UUID!){ %s(eventId:$id){ %s } }"
        % (name, "success errors { fieldErrors { field messages } nonFieldErrors }"),
        {"id": event_id}, org,
    )


def _get(client, event_id):
    return pub.gql(client, "query($id: UUID!){ event(eventId:$id){ id status } }", {"id": event_id})


def _published_ids(client, event_id):
    body = pub.gql(
        client, "query($f: [FilterSpec!]){ publishedEvents(filters: $f){ data { id } } }",
        {"f": [{"field": "id", "value": event_id}]},
    )
    assert "errors" not in body, body
    return {e["id"] for e in body["data"]["publishedEvents"]["data"]}


def _table_ids(client, org=None):
    body = pub.gql(client, TABLE, org=org)
    assert "errors" not in body, body
    return {e["id"] for e in body["data"]["eventsTable"]["data"]}


@pytest.fixture
def owner(graphql_client_for):
    return graphql_client_for(3)


@pytest.fixture
def org_slug(owner):
    return pub.org_slug(owner, ORG)


@pytest.fixture
def own_event(owner):
    created = []

    def make(**fields):
        created.append(_create(owner, **fields))
        return created[-1]

    yield make
    for event in created:
        _by_id("deleteEvent", event["id"])(owner)


@pytest.fixture
def org_event(owner, org_slug):
    event = _create(owner, org=org_slug)
    yield event
    _by_id("deleteEvent", event["id"], org=org_slug)(owner)


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.deployed_pr("DataSpaceBackend#263")
def test_draft_is_private_until_published(owner, anon_graphql_client, own_event):
    """
    AllowPublishedEvents: a draft is visible to its owner and refused to an
    anonymous caller, by id and in publishedEvents. Publishing opens it up,
    unpublishing closes it again.
    """
    event = own_event(**COMPLETE)
    assert event["status"] == "DRAFT" and event["isIndividualEvent"] is True, event
    assert _get(owner, event["id"])["data"]["event"]["id"] == event["id"]

    anon = _get(anon_graphql_client, event["id"])
    assert anon["data"]["event"] is None, f"anonymous caller read a draft: {anon}"
    assert anon["errors"][0]["message"] == "You need to be authenticated to access non-published events", anon
    assert event["id"] not in _published_ids(anon_graphql_client, event["id"]), "publishedEvents listed a draft"

    payload = _by_id("publishEvent", event["id"])(owner)
    assert payload["success"], payload["errors"]
    assert _get(anon_graphql_client, event["id"])["data"]["event"] == {"id": event["id"], "status": "PUBLISHED"}
    assert event["id"] in _published_ids(anon_graphql_client, event["id"]), "published event missing from publishedEvents"

    payload = _by_id("unpublishEvent", event["id"])(owner)
    assert payload["success"], payload["errors"]
    assert _get(anon_graphql_client, event["id"])["data"]["event"] is None, "unpublished event still public"


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.deployed_pr("DataSpaceBackend#263")
def test_publish_refuses_an_incomplete_draft(owner, own_event):
    """assert_ready_to_publish: name alone isn't enough; location, dates and a Luma embed are required."""
    event = own_event()
    payload = _by_id("publishEvent", event["id"])(owner)
    assert payload["success"] is False, f"incomplete draft was published: {payload}"
    assert set(pub.errors_of(payload)) >= {"location", "start_date", "end_date", "luma_embed"}, payload["errors"]
    assert _get(owner, event["id"])["data"]["event"]["status"] == "DRAFT"


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.deployed_pr("DataSpaceBackend#263")
def test_owner_can_update_and_delete(owner):
    event = _create(owner)
    try:
        payload = pub.mutate(
            owner, "updateEvent",
            "mutation($i: UpdateEventInput!){ updateEvent(input:$i){ %s } }" % EVENT_RESULT,
            {"i": {"id": event["id"], "name": "renamed by api test"}},
        )
        assert payload["success"], payload["errors"]
        assert payload["data"]["name"] == "renamed by api test", payload
    finally:
        deleted = _by_id("deleteEvent", event["id"])(owner)
    assert deleted["success"], deleted["errors"]
    assert _get(owner, event["id"])["data"]["event"] is None, "deleted event still readable"


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.deployed_pr("DataSpaceBackend#263")
def test_events_table_is_scoped_to_the_context(owner, org_slug, own_event, org_event):
    """get_scoped_events: no header -> the caller's individual events; organization header -> that org's."""
    mine = own_event()
    personal, org = _table_ids(owner), _table_ids(owner, org=org_slug)
    assert mine["id"] in personal and org_event["id"] not in personal, personal
    assert org_event["id"] in org and mine["id"] not in org, org


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.deployed_pr("DataSpaceBackend#263")
@pytest.mark.xfail(
    strict=True,
    reason="eventsTable has no permission check: the organization header alone "
    "selects that org's events, drafts included, for any caller (anonymous too). "
    "Product bug in DataSpaceBackend#263's get_scoped_events; remove this xfail once fixed.",
)
def test_anonymous_cannot_list_an_orgs_drafts(anon_graphql_client, org_slug, org_event):
    leaked = _table_ids(anon_graphql_client, org=org_slug)
    assert org_event["id"] not in leaked, f"anonymous eventsTable listed {ORG!r}'s draft {org_event['id']}"
