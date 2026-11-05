# tests/api/smoke/test_api_021_publication_publish.py
#
# Publishing a publication (DataSpace#243): a complete draft publishes and
# becomes public, a published one can't be edited back into an incomplete
# state, unpublishing hides it again, deleting removes it, and search sees
# only published ones. Writes to dev only; deleted in teardown.
#
# Needs active resource types on the backend (seeded by DataSpaceBackend#223);
# skips with that reason where there are none.

import time

import pytest
import requests

from tests.api import publications as pub

pytestmark = [pytest.mark.api, pytest.mark.functional]


@pytest.fixture
def owner(graphql_client_for):
    return graphql_client_for(1)


@pytest.fixture
def published(owner):
    """A complete draft, published. Deleted afterwards."""
    data = pub.create(owner, **pub.complete_fields(owner))
    payload = pub.publish(owner, data["id"])
    assert payload["success"], f"a complete draft didn't publish: {payload['errors']}"
    yield data
    pub.delete(owner, data["id"])


def _search(api_base_url, query):
    resp = requests.get(
        f"{api_base_url}/api/search/publication/", params={"query": query, "page": 1, "size": 20}, timeout=30
    )
    resp.raise_for_status()
    return resp.json()


@pytest.mark.smoke
def test_complete_draft_publishes_and_anyone_can_read_it(published, anon_graphql_client):
    publication = pub.get(anon_graphql_client, published["id"])["data"]["getPublication"]
    assert publication and publication["status"] == "PUBLISHED", f"not publicly readable: {publication}"

    listed = pub.gql(
        anon_graphql_client, "{ publications(includePublic: true, pagination: {limit: 100}) { id } }"
    )["data"]["publications"]
    assert published["id"] in {p["id"] for p in listed}, "published, but missing from the public list"


def test_published_cannot_be_edited_back_into_a_draft_state(owner, published):
    payload = pub.update(owner, published["id"], description="")
    assert pub.errors_of(payload) == {"description": ["Description is required."]}, payload

    saved = pub.get(owner, published["id"])["data"]["getPublication"]
    assert (saved["status"], saved["description"]) == ("PUBLISHED", "Publication API test"), saved


def test_unpublish_hides_it_again(owner, published, anon_graphql_client):
    payload = pub.unpublish(owner, published["id"])
    assert payload["success"], payload["errors"]
    assert payload["data"]["status"] == "DRAFT", payload

    assert pub.get(anon_graphql_client, published["id"])["data"]["getPublication"] is None


def test_deleted_publication_is_gone(owner, anon_graphql_client):
    data = pub.create(owner, **pub.complete_fields(owner))
    pub.publish(owner, data["id"])
    try:
        assert pub.delete(owner, data["id"])["success"]
        for client in (owner, anon_graphql_client):
            assert pub.gql(client, "query($id: UUID!){ getPublication(publicationId:$id){ id } }",
                           {"id": data["id"]})["data"]["getPublication"] is None
    finally:
        pub.delete(owner, data["id"])  # no-op once it's gone


def _found(api_base_url, query, publication_id, tries=6):
    """Poll search: indexing is asynchronous (a new item showed up within 10s on dev)."""
    for attempt in range(tries):
        if publication_id in {r.get("id") for r in _search(api_base_url, query).get("results", [])}:
            return True
        if attempt < tries - 1:
            time.sleep(5)
    return False


def test_search_finds_published_publications_but_never_drafts(owner, api_base_url):
    """A word in the description: absent from search while a draft, present once published."""
    fields = pub.complete_fields(owner)
    word = "zq" + fields["title"].split()[-1]
    data = pub.create(owner, **{**fields, "description": f"Search check {word}"})
    try:
        assert not _found(api_base_url, word, data["id"], tries=1), "a draft publication is searchable"
        assert pub.publish(owner, data["id"])["success"]
        assert _found(api_base_url, word, data["id"]), "published, but not searchable by a word in its description"
    finally:
        pub.delete(owner, data["id"])


@pytest.mark.deployed_pr("DataSpaceBackend#231")
def test_search_finds_a_published_title_by_a_long_word(owner, api_base_url):
    fields = pub.complete_fields(owner)
    data = pub.create(owner, **{**fields, "title": f"Mangrove resilience {fields['title'].split()[-1]}"})
    try:
        assert pub.publish(owner, data["id"])["success"]
        assert _found(api_base_url, "Mangrove", data["id"]), f"{data['title']!r} not found by searching 'Mangrove'"
    finally:
        pub.delete(owner, data["id"])
