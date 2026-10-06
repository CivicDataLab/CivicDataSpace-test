# tests/api/smoke/test_api_022_publication_links.py
#
# Linking publications to use cases (DataSpace#243). Rules from the backend:
# only a published publication can be linked, only the use case's owner (or
# org editors) can change links, and a linked publication drops out of the use
# case while unpublished and comes back when republished.
#
# Link mutations return `TypeUseCase | OperationInfo`, and refusals arrive as
# top-level GraphQL errors, not the {success errors} payload other publication
# mutations use. Writes to dev only; everything is deleted in teardown.

import pytest

from tests.api import publications as pub

pytestmark = [pytest.mark.api, pytest.mark.functional]

USECASE = "... on TypeUseCase { id publications { id } } ... on OperationInfo { messages { message } }"
LINK = "mutation($u: String!, $p: UUID!){ addPublicationToUseCase(useCaseId:$u, publicationId:$p){ %s } }" % USECASE
UNLINK = "mutation($u: String!, $p: UUID!){ removePublicationFromUseCase(useCaseId:$u, publicationId:$p){ %s } }" % USECASE
REPLACE = (
    "mutation($u: String!, $p: [UUID!]!){ updateUsecasePublications(useCaseId:$u, publicationIds:$p){ %s } }" % USECASE
)


@pytest.fixture
def owner(graphql_client_for):
    return graphql_client_for(1)


@pytest.fixture
def usecase_id(owner):
    """A draft use case owned by account 1. Deleted afterwards."""
    uc = pub.gql(owner, "mutation{ addUseCase { ... on TypeUseCase { id status } } }")["data"]["addUseCase"]
    assert uc["status"] == "DRAFT", uc
    yield uc["id"]
    pub.gql(owner, "mutation($id: String!){ deleteUseCase(useCaseId:$id) }", {"id": uc["id"]})


@pytest.fixture
def publications(owner):
    """Factory: published (or, with publish=False, draft) publications. Deleted afterwards."""
    made = []

    def make(publish=True):
        data = pub.create(owner, **pub.complete_fields(owner))
        made.append(data["id"])
        if publish:
            assert pub.publish(owner, data["id"])["success"]
        return data["id"]

    yield make
    for publication_id in made:
        pub.delete(owner, publication_id)


def _linked(owner, usecase_id):
    return [p["id"] for p in pub.gql(owner, "query($pk: ID!){ useCase(pk:$pk){ publications { id } } }",
                                     {"pk": usecase_id})["data"]["useCase"]["publications"]]


def _error(body):
    return [e["message"] for e in body.get("errors") or []]


@pytest.mark.smoke
def test_published_publication_links_to_a_draft_use_case(owner, usecase_id, publications):
    pid = publications()
    body = pub.gql(owner, LINK, {"u": usecase_id, "p": pid})
    assert not body.get("errors"), body["errors"]
    assert _linked(owner, usecase_id) == [pid]

    assert not pub.gql(owner, UNLINK, {"u": usecase_id, "p": pid}).get("errors")
    assert _linked(owner, usecase_id) == []


def test_draft_publication_cannot_be_linked(owner, usecase_id, publications):
    body = pub.gql(owner, LINK, {"u": usecase_id, "p": publications(publish=False)})
    assert _error(body) == ["Only a published resource can be linked."], body
    assert _linked(owner, usecase_id) == []


def test_another_user_cannot_link_to_my_use_case(graphql_client_for, owner, usecase_id, publications):
    body = pub.gql(graphql_client_for(3), LINK, {"u": usecase_id, "p": publications()})
    assert _error(body) == ["You don't have permission to modify this."], body
    assert _linked(owner, usecase_id) == []


def test_unpublished_publication_drops_out_and_comes_back(owner, usecase_id, publications):
    pid = publications()
    pub.gql(owner, LINK, {"u": usecase_id, "p": pid})

    assert pub.unpublish(owner, pid)["success"]
    assert _linked(owner, usecase_id) == [], "an unpublished publication still shows on the use case"

    assert pub.publish(owner, pid)["success"]
    assert _linked(owner, usecase_id) == [pid], "republishing didn't bring the link back"


def test_replacing_the_list_drops_what_is_left_out(owner, usecase_id, publications):
    first, second = publications(), publications()
    pub.gql(owner, REPLACE, {"u": usecase_id, "p": [first, second]})
    assert sorted(_linked(owner, usecase_id)) == sorted([first, second])

    body = pub.gql(owner, REPLACE, {"u": usecase_id, "p": [second]})
    assert not body.get("errors"), body["errors"]
    assert _linked(owner, usecase_id) == [second]


def test_a_draft_use_case_is_not_counted_on_the_publication(owner, usecase_id, publications):
    """linkedCount / linkedUsecases name published use cases only, so a draft's title can't leak."""
    pid = publications()
    pub.gql(owner, LINK, {"u": usecase_id, "p": pid})
    links = pub.gql(owner, "query($id: UUID!){ getPublication(publicationId:$id){ linkedCount linkedUsecases { id } } }",
                    {"id": pid})["data"]["getPublication"]
    assert links == {"linkedCount": 0, "linkedUsecases": []}, links
