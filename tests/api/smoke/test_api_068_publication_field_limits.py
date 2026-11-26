# tests/api/smoke/test_api_068_publication_field_limits.py
#
# What the publication API accepts and refuses for the fields the wizard
# fills: the title length limit, which external links count as URLs, which
# dates are real dates, and what publishing needs once the text is only spaces.
# api_015 covers unknown ids and "not a url"; this covers the shapes around them.
# Writes to dev only: every draft is deleted in teardown.

import pytest

from tests.api import publications as pub

pytestmark = [pytest.mark.api, pytest.mark.smoke]

TITLE_LIMIT = 300


@pytest.fixture
def owner(graphql_client_for):
    return graphql_client_for(1)


@pytest.fixture
def drafts(owner):
    made = []

    def make(**fields):
        data = pub.create(owner, **fields)
        made.append(data["id"])
        return data

    yield make
    for publication_id in made:
        pub.delete(owner, publication_id)


def _saved(owner, publication_id):
    return pub.get(owner, publication_id)["data"]["getPublication"]


def test_title_may_be_300_characters_and_not_301(owner, drafts):
    data = drafts(title=pub.unique_title())
    keep = "t" * TITLE_LIMIT
    assert pub.update(owner, data["id"], title=keep)["success"], "A 300 character title was refused"
    assert _saved(owner, data["id"])["title"] == keep

    payload = pub.update(owner, data["id"], title="t" * (TITLE_LIMIT + 1))
    assert not payload["success"], "A 301 character title was accepted"
    assert any(str(TITLE_LIMIT) in m for ms in pub.errors_of(payload).values() for m in ms), payload["errors"]
    assert _saved(owner, data["id"])["title"] == keep, "A refused title replaced the saved one"


@pytest.mark.parametrize("link", [
    "javascript:alert(1)", "data:text/html,hi", "http//example.org", "http://exa mple.org", "//example.org",
    "https://example.org/" + "a" * 3000, "example.org",
], ids=["javascript", "data", "missing-colon", "space-in-host", "protocol-relative", "3000-chars", "no-scheme"])
def test_links_that_are_not_urls_are_refused(owner, drafts, link):
    data = drafts(title=pub.unique_title())
    payload = pub.update(owner, data["id"], externalSourceLink=link)
    assert not payload["success"], f"{link[:40]!r} was accepted as an external link"
    assert "Enter a valid URL." in pub.errors_of(payload).get("external_source_link", []), payload["errors"]


@pytest.mark.parametrize("link", ["http://example.org/a", "https://example.org/a/b?c=1#d", "HTTPS://EXAMPLE.ORG/PATH"])
def test_http_and_https_links_are_saved(owner, drafts, link):
    data = drafts(title=pub.unique_title())
    assert pub.update(owner, data["id"], externalSourceLink=link)["success"], f"{link!r} was refused"


@pytest.mark.parametrize("date", ["2024-02-30", "not-a-date", "2024-1-1", "2024-01-01T00:00:00", "01/02/2024"])
def test_dates_that_are_not_dates_are_rejected_and_nothing_changes(owner, drafts, date):
    title = pub.unique_title()
    data = drafts(title=title)
    with pytest.raises(AssertionError, match="Value cannot represent a Date|invalid value"):
        pub.update(owner, data["id"], title="changed", publicationDate=date)
    assert _saved(owner, data["id"])["title"] == title, "A rejected update was partly saved"


@pytest.mark.parametrize("fields, field, message", [
    ({"description": "   "}, "description", "Description is required."),
    ({"authors": ["  "]}, "authors", "At least one author is required."),
], ids=["spaces-only-description", "spaces-only-author"])
def test_publishing_needs_real_text_not_spaces(owner, drafts, fields, field, message):
    ready = pub.complete_fields(owner)
    ready["license"] = "CC_BY_4_0_ATTRIBUTION"
    data = drafts(**{**ready, **fields})
    pub.add_youtube(owner, data["id"], "https://youtu.be/dQw4w9WgXcQ")
    payload = pub.publish(owner, data["id"])
    assert not payload["success"], f"A publication with a spaces-only {field} was published"
    assert message in pub.errors_of(payload).get(field, []), payload["errors"]


def test_publishing_needs_a_real_title(owner, drafts):
    """DataSpaceBackend#324: a spaces-only title is stored empty and publishing refuses it.

    createPublication ignores `title` (the draft is named by the backend), so the title
    has to be set with updatePublication to reach the check.
    """
    ready = pub.complete_fields(owner)
    ready["license"] = "CC_BY_4_0_ATTRIBUTION"
    data = drafts(**ready)
    assert pub.update(owner, data["id"], title="   ")["success"], "A spaces-only title update was refused"
    assert _saved(owner, data["id"])["title"] == "", "The spaces-only title was not stored empty"
    pub.add_youtube(owner, data["id"], "https://youtu.be/dQw4w9WgXcQ")
    payload = pub.publish(owner, data["id"])
    assert not payload["success"], "A publication with a spaces-only title was published (DataSpaceBackend#324)"
    assert "Title is required." in pub.errors_of(payload).get("title", []), payload["errors"]
