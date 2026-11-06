# tests/api/functional/test_api_func_003_usecase_matrix.py
#
# Field-combination and edge-case coverage for UseCase mutations: every running
# status and every sector / SDG round-trips, length limits either side, text
# encodings, dates and URLs, plus the documented negative paths. One draft per
# module (two for the duplicate-title case), deleted on teardown.

import uuid

import pytest

from tests.api.publications import gql

pytestmark = [pytest.mark.api, pytest.mark.functional]

RUNNING = ["INITIATED", "ON_GOING", "COMPLETED", "ON_HOLD", "CANCELLED"]
FIELDS = "id urlSlug title summary platformUrl runningStatus startedOn completedOn status tags { value } sectors { id } sdgs { id } geographies { id }"
ADD = "mutation{ addUseCase { ... on TypeUseCase { id title } ... on OperationInfo { messages { message } } } }"
UPDATE = "mutation($d: UseCaseInputPartial!){ updateUseCase(data:$d){ %s } }" % FIELDS
METADATA = """mutation($i: UpdateUseCaseMetadataInput!){ addUpdateUsecaseMetadata(updateMetadataInput:$i){
  ... on TypeUseCase { id } ... on OperationInfo { messages { message } } } }"""
READ = "query($p: ID!){ useCase(pk:$p){ %s } }" % FIELDS
PUBLISH = "mutation($i: String!){ publishUseCase(useCaseId:$i){ ... on TypeUseCase { status } ... on OperationInfo { messages { message } } } }"
DELETE = "mutation($i: String!){ deleteUseCase(useCaseId:$i) }"


def _errors(body):
    return [e["message"] for e in body.get("errors") or []]


def _new(client):
    body = gql(client, ADD)
    assert not _errors(body), body
    return body["data"]["addUseCase"]["id"]


def _update(client, uc_id, **fields):
    return gql(client, UPDATE, {"d": {"id": uc_id, **fields}})


def _read(client, uc_id):
    body = gql(client, READ, {"p": uc_id})
    assert not _errors(body), body
    return body["data"]["useCase"]


def _metadata(client, uc_id, **fields):
    return gql(client, METADATA, {"i": {"id": uc_id, "metadata": [], "tags": None, "sectors": [], **fields}})


@pytest.fixture(scope="module")
def taxonomy(graphql_client):
    body = gql(graphql_client, "{ sectors { id } allSdgs { id } geographies { id } }")
    return body["data"]


@pytest.fixture(scope="module")
def draft(graphql_client):
    uc_id = _new(graphql_client)
    _update(graphql_client, uc_id, title=f"[qa-matrix] usecase {uuid.uuid4().hex[:6]}")
    yield uc_id
    gql(graphql_client, DELETE, {"i": uc_id})


# ─── Positive ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("running", RUNNING)
def test_running_status_round_trips(graphql_client, draft, running):
    body = _update(graphql_client, draft, runningStatus=running)
    assert not _errors(body), body
    assert _read(graphql_client, draft)["runningStatus"] == running


def test_every_sector_round_trips(graphql_client, draft, taxonomy):
    for sector in taxonomy["sectors"]:
        body = _metadata(graphql_client, draft, sectors=[sector["id"]])
        assert not _errors(body), body
        assert [s["id"] for s in _read(graphql_client, draft)["sectors"]] == [sector["id"]]


def test_every_sdg_round_trips(graphql_client, draft, taxonomy):
    for sdg in taxonomy["allSdgs"]:
        body = _metadata(graphql_client, draft, sdgs=[sdg["id"]])
        assert not _errors(body), body
        assert [s["id"] for s in _read(graphql_client, draft)["sdgs"]] == [sdg["id"]]


def test_all_sectors_sdgs_and_geographies_together(graphql_client, draft, taxonomy):
    sectors = [s["id"] for s in taxonomy["sectors"]]
    sdgs = [s["id"] for s in taxonomy["allSdgs"]]
    geos = [int(g["id"]) for g in taxonomy["geographies"][:25]]
    body = _metadata(graphql_client, draft, sectors=sectors, sdgs=sdgs, geographies=geos, tags=["qa-matrix", "Budget"])
    assert not _errors(body), body
    got = _read(graphql_client, draft)
    assert sorted(s["id"] for s in got["sectors"]) == sorted(sectors)
    assert sorted(s["id"] for s in got["sdgs"]) == sorted(sdgs)
    assert sorted(int(g["id"]) for g in got["geographies"]) == sorted(geos)


def test_empty_sectors_clears_them(graphql_client, draft, taxonomy):
    _metadata(graphql_client, draft, sectors=[taxonomy["sectors"][0]["id"]])
    _metadata(graphql_client, draft, sectors=[])
    assert _read(graphql_client, draft)["sectors"] == []


def test_unknown_taxonomy_ids_are_dropped(graphql_client, draft):
    body = _metadata(graphql_client, draft, sectors=[str(uuid.uuid4())], sdgs=[str(uuid.uuid4())], geographies=[999999])
    assert not _errors(body), body
    got = _read(graphql_client, draft)
    assert (got["sectors"], got["sdgs"], got["geographies"]) == ([], [], [])


@pytest.mark.parametrize("text", [
    "[qa-matrix] उपयोग मामला",
    "[qa-matrix] حالة استخدام",
    "[qa-matrix] 🚑 108 ambulance ✓",
    "[qa-matrix] <img src=x onerror=alert(1)> & \"q\"",
], ids=["devanagari", "rtl", "emoji", "html"])
def test_title_text_round_trips(graphql_client, draft, text):
    body = _update(graphql_client, draft, title=text)
    assert not _errors(body), body
    assert _read(graphql_client, draft)["title"] == text


def test_dates_round_trip(graphql_client, draft):
    body = _update(graphql_client, draft, startedOn="2024-01-01", completedOn="2025-12-31", runningStatus="COMPLETED")
    assert not _errors(body), body
    got = _read(graphql_client, draft)
    assert (got["startedOn"], got["completedOn"]) == ("2024-01-01", "2025-12-31")


def test_summary_at_200000_chars_is_accepted(graphql_client, draft):
    summary = "s" * 200000
    body = _update(graphql_client, draft, summary=summary)
    assert not _errors(body), _errors(body)
    assert len(_read(graphql_client, draft)["summary"]) == 200000


def test_duplicate_title_is_allowed_with_distinct_url(graphql_client, draft):
    # Titles stopped being unique once links moved to public_id (urlSlug).
    mine = _read(graphql_client, draft)
    other = _new(graphql_client)
    try:
        body = _update(graphql_client, other, title=mine["title"])
        assert not _errors(body), body
        theirs = _read(graphql_client, other)
        assert theirs["title"] == mine["title"]
        assert theirs["urlSlug"] != mine["urlSlug"], "two use cases resolve to the same URL"
    finally:
        gql(graphql_client, DELETE, {"i": other})


# ─── Negative ─────────────────────────────────────────────────────────────────

def test_title_over_200_is_refused(graphql_client, draft):
    before = _read(graphql_client, draft)["title"]
    body = _update(graphql_client, draft, title="t" * 201)
    assert any("200" in m for m in _errors(body)), body
    assert _read(graphql_client, draft)["title"] == before


def test_whitespace_title_is_refused(graphql_client, draft):
    assert "Title cannot be empty." in _errors(_update(graphql_client, draft, title="   "))


def test_summary_over_200000_is_refused(graphql_client, draft):
    body = _update(graphql_client, draft, summary="s" * 200001)
    assert "Summary cannot exceed 200000 characters." in _errors(body), body


def test_bad_running_status_is_refused(graphql_client, draft):
    assert _errors(_update(graphql_client, draft, runningStatus="FINISHED"))


def test_unknown_use_case_is_refused(graphql_client):
    assert _errors(_update(graphql_client, "999999999", title="[qa-matrix] ghost"))


@pytest.mark.xfail(strict=True, reason="DataSpaceBackend#292: updateUseCase stores any platformUrl; URLField is never validated")
def test_invalid_platform_url_is_refused(graphql_client, draft):
    assert _errors(_update(graphql_client, draft, platformUrl="not a url"))


@pytest.mark.xfail(strict=True, reason="DataSpaceBackend#292: no check that completedOn is on or after startedOn")
def test_completed_before_started_is_refused(graphql_client, draft):
    assert _errors(_update(graphql_client, draft, startedOn="2025-06-01", completedOn="2024-01-01"))


@pytest.mark.xfail(strict=True, reason="DataSpaceBackend#291: runningStatus defaults to INITIATED, so any update that omits it resets it")
def test_update_without_running_status_keeps_it(graphql_client, draft):
    _update(graphql_client, draft, runningStatus="ON_HOLD")
    _update(graphql_client, draft, summary="[qa-matrix] summary only")
    assert _read(graphql_client, draft)["runningStatus"] == "ON_HOLD"


@pytest.mark.xfail(strict=True, reason="DataSpaceBackend#292: publishUseCase has no required-field check; an empty draft publishes")
def test_empty_draft_cannot_publish(graphql_client):
    uc_id = _new(graphql_client)
    try:
        body = gql(graphql_client, PUBLISH, {"i": uc_id})
        assert body["data"]["publishUseCase"].get("status") != "PUBLISHED"
    finally:
        gql(graphql_client, DELETE, {"i": uc_id})


def test_published_use_case_cannot_be_edited(graphql_client):
    uc_id = _new(graphql_client)
    try:
        gql(graphql_client, PUBLISH, {"i": uc_id})
        body = _update(graphql_client, uc_id, title=f"[qa-matrix] after publish {uuid.uuid4().hex[:4]}")
        assert any("not in draft status" in m for m in _errors(body)), body
    finally:
        gql(graphql_client, DELETE, {"i": uc_id})
