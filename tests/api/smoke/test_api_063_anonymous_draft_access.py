# tests/api/smoke/test_api_063_anonymous_draft_access.py
#
# DataSpaceBackend#312 (DataSpace#352): use case and collaborative drafts are
# hidden from anonymous callers, and an anonymous update or delete is refused
# and changes nothing. test_api_056 covers signed-in roles; this is the caller
# with no account. Uses drafts this test creates; runs where #312 is deployed.

import os
import uuid

import pytest

from tests.api.publications import gql
from utils.provider_api import ProviderAPI

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.deployed_pr("DataSpaceBackend#312")]

OWNER = 4
KINDS = {
    "usecase": ("useCase", "mutation($i: UseCaseInputPartial!){ updateUseCase(data:$i){ id } }",
                "mutation($id: String!){ deleteUseCase(useCaseId:$id) }"),
    "collaborative": ("collaborative", "mutation($i: CollaborativeInputPartial!){ updateCollaborative(data:$i){ id } }",
                      "mutation($id: String!){ deleteCollaborative(collaborativeId:$id) }"),
}


@pytest.fixture(scope="module")
def owner():
    email, password = os.getenv(f"TEST_EMAIL_{OWNER}"), os.getenv(f"TEST_PASSWORD_{OWNER}")
    if not (email and password):
        pytest.skip(f"TEST_EMAIL_{OWNER}/TEST_PASSWORD_{OWNER} not set")
    return ProviderAPI(email, password)


@pytest.fixture(params=list(KINDS))
def draft(request, owner):
    kind = request.param
    title = f"zz-auto-anon-{uuid.uuid4().hex[:8]}"
    rid = str(owner.create_draft(kind, title))
    yield kind, rid, title
    owner.delete(kind, rid)


def _stored(owner, field, rid):
    body = owner.gql("query($id: ID!){ %s(pk:$id){ id title } }" % field, {"id": rid})
    assert "errors" not in body, body["errors"]
    return body["data"][field]


def test_anonymous_cannot_read_a_draft(draft, anon_graphql_client):
    kind, rid, _ = draft
    field = KINDS[kind][0]
    body = gql(anon_graphql_client, "query($id: ID!){ %s(pk:$id){ id title } }" % field, {"id": rid})
    assert not (body.get("data") or {}).get(field), f"an anonymous caller can read a {kind} draft"


def test_anonymous_update_and_delete_change_nothing(draft, owner, anon_graphql_client):
    kind, rid, title = draft
    field, update, delete = KINDS[kind]
    updated = gql(anon_graphql_client, update, {"i": {"id": rid, "title": "zz-auto-anon-changed"}})
    deleted = gql(anon_graphql_client, delete, {"id": rid})
    assert "errors" in updated and "errors" in deleted, f"anonymous {kind} update/delete not refused: {updated} {deleted}"
    stored = _stored(owner, field, rid)
    assert stored and stored["title"] == title, f"an anonymous caller changed the {kind} draft: {stored}"
