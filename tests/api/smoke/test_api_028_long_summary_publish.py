# tests/api/smoke/test_api_028_long_summary_publish.py
#
# Covers DataSpaceBackend#266 (fixed on dev by #278/#281, on main by #283) and
# the summary limit raise in #227 (10k -> 200k characters).
#
# Publishing a use case or collaborative indexes it in search. Its summary had a
# keyword-analyzed `raw` sub-field that turned the whole text into one token,
# and Elasticsearch refuses tokens over 32,766 bytes, so publishing anything
# with a long summary returned an error. Writes to dev only; deleted in teardown.

import uuid

import pytest

from tests.api import publications as pub

pytestmark = [pytest.mark.api, pytest.mark.smoke]

KINDS = {
    "usecase": {
        "add": "mutation{ addUseCase { ... on TypeUseCase { id } } }",
        "update": "mutation($d: UseCaseInputPartial!){ updateUseCase(data:$d){ ... on TypeUseCase { id } } }",
        "publish": "mutation($id: String!){ publishUseCase(useCaseId:$id){ ... on TypeUseCase { status } } }",
        "delete": "mutation($id: String!){ deleteUseCase(useCaseId:$id) }",
    },
    "collaborative": {
        "add": "mutation{ addCollaborative { ... on TypeCollaborative { id } } }",
        "update": (
            "mutation($d: CollaborativeInputPartial!)"
            "{ updateCollaborative(data:$d){ ... on TypeCollaborative { id } } }"
        ),
        "publish": (
            "mutation($id: String!){ publishCollaborative(collaborativeId:$id)"
            "{ ... on TypeCollaborative { status } } }"
        ),
        "delete": "mutation($id: String!){ deleteCollaborative(collaborativeId:$id) }",
    },
}


def _ok(body):
    assert not body.get("errors"), body["errors"]
    return body["data"]


@pytest.mark.parametrize("kind", KINDS)
def test_long_summary_publishes_and_is_searchable(graphql_client_for, anon_api_client, kind):
    q, owner = KINDS[kind], graphql_client_for(1)
    word = "longsum" + uuid.uuid4().hex[:10]
    summary = f"{word} " + "x" * 40_000  # one keyword token of ~40KB, over Lucene's 32,766-byte limit

    item_id = next(iter(_ok(pub.gql(owner, q["add"])).values()))["id"]
    try:
        _ok(pub.gql(owner, q["update"], {"d": {"id": item_id, "title": f"api test {word}", "summary": summary}}))

        published = next(iter(_ok(pub.gql(owner, q["publish"], {"id": item_id})).values()))
        assert published["status"] == "PUBLISHED", published

        resp = anon_api_client.get(f"/api/search/{kind}/", params={"query": word, "size": 10})
        assert resp.status_code == 200, resp.text
        ids = {str(r.get("id")) for r in resp.json().get("results", [])}
        assert item_id in ids, f"published {kind} with a 40KB summary is missing from search"
    finally:
        pub.gql(owner, q["delete"], {"id": item_id})
