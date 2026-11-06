# tests/api/functional/test_api_func_002_dataset_matrix.py
#
# Field-combination and edge-case coverage for Dataset mutations, mirroring the
# ParakhAI matrix tests: every enum value round-trips, boundaries either side
# of each length limit, and the negative paths return the documented error.
# One draft per module; every case updates it, so the dev write limiter
# (1000 non-GET/h per IP) is not a concern.

import itertools
import uuid

import pytest

from tests.api.publications import gql

pytestmark = [pytest.mark.api, pytest.mark.functional]

LICENSES = [
    "GOVERNMENT_OPEN_DATA_LICENSE", "CC_BY_4_0_ATTRIBUTION", "CC_BY_SA_4_0_ATTRIBUTION_SHARE_ALIKE",
    "OPEN_DATA_COMMONS_BY_ATTRIBUTION", "OPEN_DATABASE_LICENSE", "CC_PDM_1_0", "CC_BY_1_0", "CC_BY_2_0",
    "CC_BY_2_5_AU", "CC_BY_2_5", "CC_BY_3_0_AU", "CC_BY_3_0_AT", "CC_BY_3_0_DE", "CC_BY_3_0_IGO",
    "CC_BY_3_0_NL", "CC_BY_3_0_US", "CC_BY_3_0", "CC_BY_ND_1_0", "CC_BY_ND_2_0", "CC_BY_ND_2_5",
    "CC_BY_ND_3_0_DE", "CC_BY_ND_3_0", "CC_BY_ND_4_0", "CC_BY_NC_1_0", "CC_BY_NC_2_0", "CC_BY_NC_2_5",
    "CC_BY_NC_3_0_DE", "CC_BY_NC_3_0_IGO", "CC_BY_NC_3_0", "CC_BY_NC_4_0", "CC_BY_NC_ND_1_0",
    "CC_BY_NC_ND_2_0", "CC_BY_NC_ND_2_5", "CC_BY_NC_ND_3_0_DE", "CC_BY_NC_ND_3_0_IGO", "CC_BY_NC_ND_3_0",
    "CC_BY_NC_ND_4_0", "CC_BY_NC_SA_1_0", "CC_BY_NC_SA_2_0_UK", "CC_BY_NC_SA_2_0", "CC_BY_NC_SA_2_0_DE",
    "CC_BY_NC_SA_2_5", "CC_BY_NC_SA_3_0_DE", "CC_BY_NC_SA_3_0_IGO", "CC_BY_NC_SA_3_0", "CC_BY_NC_SA_4_0",
    "CC_BY_SA_1_0", "CC_BY_SA_2_0_UK", "CC_BY_SA_2_0", "CC_BY_SA_2_1_JP", "CC_BY_SA_2_5", "CC_BY_SA_3_0_AT",
    "CC_BY_SA_3_0_DE", "CC_BY_SA_3_0", "CC_BY_NC_SA_2_0_FR", "CC_BY_SA_3_0_IGO", "CC_PDDC", "CC_SA_1_0",
    "CC0_1_0", "PDDL_1_0",
]
ACCESS = ["PUBLIC", "PRIVATE", "RESTRICTED"]
# Every license once, access type cycling, so all 3 x pairs with a license are seen.
LICENSE_ACCESS = list(zip(LICENSES, itertools.cycle(ACCESS)))

UPDATE = """
mutation($i: UpdateDatasetInput!){ updateDataset(updateDatasetInput:$i){
  ... on TypeDataset { id title description license accessType tags { value } }
  ... on OperationInfo { messages { message } } } }"""
READ = "query($id: UUID!){ getDataset(datasetId:$id){ id title description license accessType status tags { value } } }"


def _update(client, dataset_id, **fields):
    return gql(client, UPDATE, {"i": {"dataset": dataset_id, **fields}})


def _read(client, dataset_id):
    body = gql(client, READ, {"id": dataset_id})
    assert "errors" not in body, body
    return body["data"]["getDataset"]


def _messages(body):
    msgs = [e["message"] for e in body.get("errors") or []]
    data = (body.get("data") or {}).get("updateDataset") or {}
    msgs += [m["message"] for m in data.get("messages") or []]
    return msgs


@pytest.fixture(scope="module")
def draft(graphql_client):
    body = gql(graphql_client, "mutation{ addDataset(createInput:{datasetType: DATA}){ success data { id } } }")
    dataset_id = body["data"]["addDataset"]["data"]["id"]
    _update(graphql_client, dataset_id, title=f"[qa-matrix] dataset {uuid.uuid4().hex[:6]}")
    yield dataset_id
    gql(graphql_client, "mutation($id: UUID!){ unPublishDataset(datasetId:$id){ ... on TypeDataset { id } } }", {"id": dataset_id})
    gql(graphql_client, "mutation($id: UUID!){ deleteDataset(datasetId:$id) }", {"id": dataset_id})


# ─── Positive: every license and access type round-trips ──────────────────────

@pytest.mark.parametrize("license_,access", LICENSE_ACCESS, ids=[l for l, _ in LICENSE_ACCESS])
def test_license_and_access_round_trip(graphql_client, draft, license_, access):
    body = _update(graphql_client, draft, license=license_, accessType=access)
    assert not _messages(body), _messages(body)
    got = _read(graphql_client, draft)
    assert (got["license"], got["accessType"]) == (license_, access)


# ─── Boundaries: title (300) and description (1000) ───────────────────────────

@pytest.mark.parametrize("field,limit", [("title", 300), ("description", 1000)])
def test_length_limit_is_accepted(graphql_client, draft, field, limit):
    value = ("[qa-matrix] " + "x" * limit)[:limit]
    body = _update(graphql_client, draft, **{field: value}, license="CC0_1_0")
    assert not _messages(body), _messages(body)
    assert _read(graphql_client, draft)[field] == value


@pytest.mark.parametrize("field,limit", [("title", 300), ("description", 1000)])
def test_one_over_the_limit_is_refused(graphql_client, draft, field, limit):
    before = _read(graphql_client, draft)[field]
    body = _update(graphql_client, draft, **{field: "y" * (limit + 1)}, license="CC0_1_0")
    # The refusal currently surfaces Postgres' own text ("value too long for type
    # character varying(N)") rather than the friendly field error; accept either.
    assert any(str(limit) in m and ("longer than" in m or "too long" in m) for m in _messages(body)), body
    assert _read(graphql_client, draft)[field] == before


def test_whitespace_title_is_refused(graphql_client, draft):
    body = _update(graphql_client, draft, title="   ", license="CC0_1_0")
    assert "Title cannot be empty." in _messages(body), body


@pytest.mark.parametrize("text", [
    "[qa-matrix] डेटासेट जनगणना २०२६",          # Devanagari
    "[qa-matrix] بيانات السكان",                 # RTL
    "[qa-matrix] 📊 data 🇮🇳 ✓",                  # emoji, flag sequence
    "[qa-matrix] <script>alert(1)</script> & \"quotes\" 'x'",  # stored verbatim, not executed
    "[qa-matrix]  leading and   inner  spaces",
], ids=["devanagari", "rtl", "emoji", "html", "spaces"])
def test_title_text_round_trips(graphql_client, draft, text):
    body = _update(graphql_client, draft, title=text, license="CC0_1_0")
    assert not _messages(body), _messages(body)
    assert _read(graphql_client, draft)["title"] == text


# ─── Tags ─────────────────────────────────────────────────────────────────────

def test_tags_dedupe_case_insensitively(graphql_client, draft):
    _update(graphql_client, draft, tags=["QA-Matrix", "qa-matrix", "Budget"], license="CC0_1_0")
    values = [t["value"].lower() for t in _read(graphql_client, draft)["tags"]]
    assert sorted(values) == sorted(set(values)), f"duplicate tags stored: {values}"


def test_tag_of_50_chars_is_accepted(graphql_client, draft):
    tag = "q" * 50
    body = _update(graphql_client, draft, tags=[tag], license="CC0_1_0")
    assert not _messages(body), _messages(body)
    assert tag in [t["value"] for t in _read(graphql_client, draft)["tags"]]


@pytest.mark.xfail(strict=True, reason="DataSpaceBackend#291: updateDataset saves title before a too-long tag fails (partial write)")
def test_too_long_tag_does_not_half_save(graphql_client, draft):
    marker = f"[qa-matrix] partial {uuid.uuid4().hex[:6]}"
    body = _update(graphql_client, draft, title=marker, tags=["t" * 51], license="CC0_1_0")
    assert _messages(body), "51-char tag was accepted"
    assert _read(graphql_client, draft)["title"] != marker


# ─── Defaults must not overwrite stored values ────────────────────────────────

@pytest.mark.xfail(strict=True, reason="DataSpaceBackend#291: UpdateDatasetInput defaults license/accessType, so omitting them resets both")
def test_update_without_license_keeps_license(graphql_client, draft):
    _update(graphql_client, draft, license="CC0_1_0", accessType="RESTRICTED")
    _update(graphql_client, draft, description="[qa-matrix] description only")
    got = _read(graphql_client, draft)
    assert (got["license"], got["accessType"]) == ("CC0_1_0", "RESTRICTED")


# ─── Not found ────────────────────────────────────────────────────────────────

def test_update_unknown_dataset_is_refused(graphql_client):
    body = _update(graphql_client, str(uuid.uuid4()), title="[qa-matrix] ghost")
    assert _messages(body), "update of a non-existent dataset returned no error"
