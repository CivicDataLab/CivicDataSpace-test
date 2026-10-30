# tests/api/smoke/test_api_037_summary_length.py
#
# Use case / collaborative summary length (DataSpaceBackend#227). `summary` went
# from a 10,000-character varchar to a text column capped at 200,000, and the
# update mutations now reject longer text with a readable error instead of
# letting the database fail. Writes to dev only: never `readonly`; the draft
# created for each case is deleted in teardown.

import pytest

from tests.api.publications import gql

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.deployed_pr("DataSpaceBackend#227")]

OLD_LIMIT = 10_000
LIMIT = 200_000

# kind -> (add, update, delete, delete's id argument, single-record query, GraphQL type)
KINDS = {
    "usecase": ("addUseCase", "updateUseCase", "deleteUseCase", "useCaseId", "useCase", "TypeUseCase"),
    "collaborative": ("addCollaborative", "updateCollaborative", "deleteCollaborative", "collaborativeId", "collaborative", "TypeCollaborative"),
}


@pytest.fixture
def draft(graphql_client_for, request):
    """Factory for a draft of the requested kind owned by account 1; deleted afterwards."""
    client = graphql_client_for(1)
    made = []

    def make(kind):
        add, _, delete, arg, _, _ = KINDS[kind]
        body = gql(client, "mutation { %s { ... on %s { id } } }" % (add, KINDS[kind][5]))
        assert "errors" not in body, f"{add} failed: {body['errors']}"
        record_id = body["data"][add]["id"]
        made.append((delete, arg, record_id))
        return client, record_id

    yield make
    for delete, arg, record_id in made:
        body = gql(client, 'mutation { %s(%s: "%s") }' % (delete, arg, record_id))
        assert "errors" not in body, f"cleanup of {record_id} failed: {body['errors']}"


def _save(client, kind, record_id, summary):
    update = KINDS[kind][1]
    return gql(
        client,
        "mutation($d: %sInputPartial!){ %s(data:$d){ id } }" % ("UseCase" if kind == "usecase" else "Collaborative", update),
        {"d": {"id": record_id, "summary": summary}},
    )


def _stored_length(client, kind, record_id):
    query = KINDS[kind][4]
    body = gql(client, '{ %s(pk: "%s") { summary } }' % (query, record_id))
    assert "errors" not in body, f"reading the {kind} back failed: {body['errors']}"
    return len(body["data"][query]["summary"])


@pytest.mark.parametrize("kind", KINDS)
def test_summary_accepts_text_up_to_the_new_limit_and_rejects_beyond(draft, kind):
    client, record_id = draft(kind)

    for length in (OLD_LIMIT + 1, LIMIT):
        body = _save(client, kind, record_id, "x" * length)
        assert "errors" not in body, f"a {length}-character summary was rejected: {body['errors']}"
        assert _stored_length(client, kind, record_id) == length, f"a {length}-character summary was not stored whole"

    body = _save(client, kind, record_id, "x" * (LIMIT + 1))
    messages = " | ".join(e["message"] for e in body.get("errors", []))
    assert f"Summary cannot exceed {LIMIT} characters." in messages, f"over-limit summary not rejected cleanly: {body}"
    assert _stored_length(client, kind, record_id) == LIMIT, "a rejected summary overwrote the stored one"
