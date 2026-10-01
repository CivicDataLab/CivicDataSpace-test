# tests/api/smoke/test_api_015_publication_drafts.py
#
# Publication drafts (DataSpace#243, endpoints per anantjain341's notes there):
# create, update, field validation, who can read a draft, and what publishing
# a draft still needs. Writes to dev only: never `readonly`, and every draft is
# deleted in teardown.

import pytest

from tests.api import publications as pub

pytestmark = [pytest.mark.api, pytest.mark.functional]

ZERO_UUID = "00000000-0000-0000-0000-000000000000"


@pytest.fixture
def owner(graphql_client_for):
    return graphql_client_for(1)


@pytest.fixture
def drafts(owner):
    """Factory for drafts owned by account 1; deletes them all afterwards."""
    made = []

    def make(**fields):
        data = pub.create(owner, **fields)
        made.append(data["id"])
        return data

    yield make
    for publication_id in made:
        pub.delete(owner, publication_id)


@pytest.mark.smoke
def test_blank_draft_gets_a_generated_title(drafts):
    """Every field is optional: an empty draft saves, with a generated title."""
    data = drafts()
    assert data["status"] == "DRAFT", data
    assert data["title"].startswith("New publication "), data
    assert data["slug"], data
    assert data["license"] == "CC_BY_4_0_ATTRIBUTION", data


def test_update_leaves_omitted_fields_alone(owner, drafts):
    """Only the fields sent change; the rest keep their values."""
    title = pub.unique_title()
    data = drafts(title=title, description="first", authors=["A. Author"])

    payload = pub.update(owner, data["id"], description="second")
    assert payload["success"], payload["errors"]

    saved = pub.get(owner, data["id"])["data"]["getPublication"]
    assert (saved["title"], saved["description"], saved["authors"]) == (title, "second", ["A. Author"])


@pytest.mark.parametrize("fields, field, message", [
    ({"externalSourceLink": "not a url"}, "external_source_link", "Enter a valid URL."),
    ({"resourceTypeId": ZERO_UUID}, "resource_type", "Resource type does not exist."),
    ({"sectorIds": [ZERO_UUID]}, "sectors", "One or more sectors do not exist."),
    ({"geographyIds": [999999999]}, "geographies", "One or more geographies do not exist."),
], ids=["url", "resource_type", "sector", "geography"])
def test_invalid_values_are_rejected_and_nothing_changes(owner, drafts, fields, field, message):
    title = pub.unique_title()
    data = drafts(title=title)

    payload = pub.update(owner, data["id"], title="changed", **fields)
    assert not payload["success"], payload
    assert message in pub.errors_of(payload).get(field, []), payload["errors"]
    assert pub.get(owner, data["id"])["data"]["getPublication"]["title"] == title, "a rejected update was partly saved"


def test_publishing_an_empty_draft_lists_every_missing_field(owner, drafts):
    """Publish enforces the full field set and names each gap; the draft stays a draft.

    Title (generated) and licence (defaulted) are already filled on an empty draft.
    """
    data = drafts()
    payload = pub.publish(owner, data["id"])
    assert not payload["success"], payload
    assert set(pub.errors_of(payload)) == {
        "description", "authors", "publication_date", "resource_type", "sectors", "geographies",
    }, payload["errors"]
    assert pub.get(owner, data["id"])["data"]["getPublication"]["status"] == "DRAFT"


def test_draft_is_visible_to_its_owner_only(owner, drafts, anon_graphql_client, graphql_client_for):
    data = drafts(title=pub.unique_title())

    assert pub.get(owner, data["id"])["data"]["getPublication"]["id"] == data["id"]
    for who, client in (("anonymous", anon_graphql_client), ("account 3", graphql_client_for(3))):
        body = pub.get(client, data["id"])
        assert body["data"]["getPublication"] is None, f"{who} can read someone else's draft: {body}"
