# tests/api/smoke/test_api_070_publication_field_combinations.py
#
# Every combination of the six fields publishing enforces (description,
# contributors, date, resource type, sectors, geographies; the title is generated
# and the licence defaulted): publishing a draft that has exactly that subset
# names exactly the others as missing and leaves it a draft, and only the full set
# publishes. 64 combinations on one draft, so it costs two calls each.
# `regression` is not selected by PR or default dispatch runs; use suite=full.

import itertools

import pytest

from tests.api import publications as pub

pytestmark = [pytest.mark.api, pytest.mark.regression]

FIELDS = ["description", "authors", "publication_date", "resource_type", "sectors", "geographies"]
CLEAR = {"description": "", "authors": [], "publication_date": None, "resource_type": None, "sectors": [], "geographies": []}
INPUT_KEY = {"description": "description", "authors": "authors", "publication_date": "publicationDate",
             "resource_type": "resourceTypeId", "sectors": "sectorIds", "geographies": "geographyIds"}


@pytest.fixture(scope="module")
def owner(graphql_client_for):
    return graphql_client_for(1)


@pytest.fixture(scope="module")
def draft(owner):
    ready = pub.complete_fields(owner)
    values = {"description": ready["description"], "authors": ready["authors"], "publication_date": ready["publicationDate"],
              "resource_type": ready["resourceTypeId"], "sectors": ready["sectorIds"], "geographies": ready["geographyIds"]}
    data = pub.create(owner, title=pub.unique_title("combo"))
    pub.add_youtube(owner, data["id"], "https://youtu.be/dQw4w9WgXcQ")
    yield data["id"], values
    pub.unpublish(owner, data["id"])
    pub.delete(owner, data["id"])


def _combinations():
    for size in range(len(FIELDS) + 1):
        for present in itertools.combinations(FIELDS, size):
            yield pytest.param(present, id="+".join(present) or "nothing")


@pytest.mark.parametrize("present", _combinations())
def test_api_070_publish_names_exactly_the_missing_fields(owner, draft, present):
    publication_id, values = draft
    fields = {INPUT_KEY[f]: (values[f] if f in present else CLEAR[f]) for f in FIELDS}
    assert pub.update(owner, publication_id, **fields)["success"], "the draft could not be set to this combination"

    payload = pub.publish(owner, publication_id)
    missing = {f for f in FIELDS if f not in present}
    if not missing:
        assert payload["success"], f"a complete draft was refused: {payload['errors']}"
        assert pub.unpublish(owner, publication_id)["success"]
        return
    assert not payload["success"], f"published with only {sorted(present)}"
    assert set(pub.errors_of(payload)) == missing, f"with {sorted(present)} it named {sorted(pub.errors_of(payload))}, not {sorted(missing)}"
    assert pub.get(owner, publication_id)["data"]["getPublication"]["status"] == "DRAFT"
