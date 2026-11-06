# tests/api/functional/test_api_func_004_collaborative_matrix.py
#
# Field-combination and edge-case coverage for Collaborative mutations. The slug
# is also the collaborative's subdomain, so its rules get the most cases: format,
# length, uniqueness, and that a typed slug is never silently rewritten.

import uuid

import pytest

from tests.api.publications import gql

pytestmark = [pytest.mark.api, pytest.mark.functional]

FIELDS = "id urlSlug title slug summary platformUrl startedOn completedOn status tags { value } sectors { id } sdgs { id } geographies { id }"
ADD = "mutation{ addCollaborative { ... on TypeCollaborative { id title } ... on OperationInfo { messages { message } } } }"
UPDATE = "mutation($d: CollaborativeInputPartial!){ updateCollaborative(data:$d){ %s } }" % FIELDS
METADATA = """mutation($i: UpdateCollaborativeMetadataInput!){ addUpdateCollaborativeMetadata(updateMetadataInput:$i){
  ... on TypeCollaborative { id } ... on OperationInfo { messages { message } } } }"""
READ = "query($p: ID!){ collaborative(pk:$p){ %s } }" % FIELDS
BY_SLUG = "query($s: String!){ collaborativeBySlug(slug:$s){ id } }"
PUBLISH = "mutation($i: String!){ publishCollaborative(collaborativeId:$i){ ... on TypeCollaborative { status } ... on OperationInfo { messages { message } } } }"
DELETE = "mutation($i: String!){ deleteCollaborative(collaborativeId:$i) }"


def _errors(body):
    return [e["message"] for e in body.get("errors") or []]


def _new(client):
    body = gql(client, ADD)
    assert not _errors(body), body
    return body["data"]["addCollaborative"]["id"]


def _update(client, cid, **fields):
    return gql(client, UPDATE, {"d": {"id": cid, **fields}})


def _read(client, cid):
    body = gql(client, READ, {"p": cid})
    assert not _errors(body), body
    return body["data"]["collaborative"]


def _slug():
    return f"qa-matrix-{uuid.uuid4().hex[:8]}"


@pytest.fixture(scope="module")
def taxonomy(graphql_client):
    return gql(graphql_client, "{ sectors { id } allSdgs { id } geographies { id } }")["data"]


@pytest.fixture(scope="module")
def draft(graphql_client):
    cid = _new(graphql_client)
    _update(graphql_client, cid, title=f"[qa-matrix] collaborative {uuid.uuid4().hex[:6]}")
    yield cid
    gql(graphql_client, DELETE, {"i": cid})


@pytest.fixture
def second(graphql_client):
    cid = _new(graphql_client)
    yield cid
    gql(graphql_client, DELETE, {"i": cid})


# ─── Slug (subdomain) ─────────────────────────────────────────────────────────

@pytest.mark.parametrize("slug", ["a", "qa-matrix-7", "x" * 75, "0-0-0"], ids=["one-char", "hyphen-digit", "max-75", "digits"])
def test_valid_slug_round_trips_and_resolves(graphql_client, draft, slug):
    slug = slug if slug != "a" else f"a{uuid.uuid4().hex[:5]}"
    slug = slug if slug != "x" * 75 else (_slug() + "x" * 75)[:75]
    body = _update(graphql_client, draft, slug=slug)
    assert not _errors(body), body
    assert _read(graphql_client, draft)["slug"] == slug
    assert gql(graphql_client, BY_SLUG, {"s": slug})["data"]["collaborativeBySlug"]["id"] == draft


@pytest.mark.parametrize("slug", [
    "Upper-Case", "has space", "under_score", "-leading", "trailing-", "double--hyphen", "dot.ted", "émoji-ü", "x" * 76,
])
def test_invalid_slug_is_refused_not_rewritten(graphql_client, draft, slug):
    before = _read(graphql_client, draft)["slug"]
    body = _update(graphql_client, draft, slug=slug)
    assert _errors(body), f"slug {slug!r} was accepted"
    assert _read(graphql_client, draft)["slug"] == before


def test_whitespace_slug_is_refused(graphql_client, draft):
    assert "Slug cannot be empty." in _errors(_update(graphql_client, draft, slug="   "))


def test_slug_taken_by_another_is_refused(graphql_client, draft, second):
    taken = _read(graphql_client, draft)["slug"]
    body = _update(graphql_client, second, slug=taken)
    assert _errors(body), "a second collaborative took an existing subdomain"
    assert _read(graphql_client, second)["slug"] != taken


def test_same_title_gets_its_own_slug(graphql_client, draft, second):
    title = _read(graphql_client, draft)["title"]
    body = _update(graphql_client, second, title=title)
    assert not _errors(body), body
    mine, theirs = _read(graphql_client, draft), _read(graphql_client, second)
    assert theirs["title"] == title
    assert theirs["urlSlug"] != mine["urlSlug"]


@pytest.mark.xfail(strict=True, reason="no reserved-subdomain list; 'www'/'api'/'admin' are accepted as collaborative slugs")
@pytest.mark.parametrize("slug", ["www", "api", "admin"])
def test_reserved_subdomain_is_refused(graphql_client, second, slug):
    assert _errors(_update(graphql_client, second, slug=slug))


# ─── Other fields ─────────────────────────────────────────────────────────────

@pytest.mark.parametrize("url", ["https://example.org", "http://example.org/path?q=1#x", "https://उदाहरण.भारत"])
def test_valid_platform_url_round_trips(graphql_client, draft, url):
    body = _update(graphql_client, draft, platformUrl=url)
    assert not _errors(body), body
    assert _read(graphql_client, draft)["platformUrl"] == url


@pytest.mark.parametrize("url", ["not a url", "javascript:alert(1)", "ftp//missing-colon"])
def test_invalid_platform_url_is_refused(graphql_client, draft, url):
    before = _read(graphql_client, draft)["platformUrl"]
    body = _update(graphql_client, draft, platformUrl=url)
    assert _errors(body), f"{url!r} accepted"
    assert _read(graphql_client, draft)["platformUrl"] == before


def test_every_sector_and_sdg_round_trips(graphql_client, draft, taxonomy):
    for sector, sdg in zip(taxonomy["sectors"] * 2, taxonomy["allSdgs"]):
        body = gql(graphql_client, METADATA, {"i": {
            "id": draft, "metadata": [], "tags": ["qa-matrix"], "sectors": [sector["id"]], "sdgs": [sdg["id"]], "geographies": None}})
        assert not _errors(body), body
        got = _read(graphql_client, draft)
        assert ([s["id"] for s in got["sectors"]], [s["id"] for s in got["sdgs"]]) == ([sector["id"]], [sdg["id"]])


def test_title_over_200_is_refused(graphql_client, draft):
    before = _read(graphql_client, draft)["title"]
    assert _errors(_update(graphql_client, draft, title="t" * 201))
    assert _read(graphql_client, draft)["title"] == before


def test_summary_over_200000_is_refused(graphql_client, draft):
    assert "Summary cannot exceed 200000 characters." in _errors(_update(graphql_client, draft, summary="s" * 200001))


@pytest.mark.xfail(strict=True, reason="no check that completedOn is on or after startedOn")
def test_completed_before_started_is_refused(graphql_client, draft):
    assert _errors(_update(graphql_client, draft, startedOn="2025-06-01", completedOn="2024-01-01"))


@pytest.mark.xfail(strict=True, reason="publishCollaborative has no required-field check; an empty draft publishes")
def test_empty_draft_cannot_publish(graphql_client, second):
    body = gql(graphql_client, PUBLISH, {"i": second})
    assert body["data"]["publishCollaborative"].get("status") != "PUBLISHED"


def test_unknown_slug_lookup_errors(graphql_client):
    body = gql(graphql_client, BY_SLUG, {"s": f"qa-matrix-missing-{uuid.uuid4().hex[:6]}"})
    assert any("does not exist" in m for m in _errors(body)), body
