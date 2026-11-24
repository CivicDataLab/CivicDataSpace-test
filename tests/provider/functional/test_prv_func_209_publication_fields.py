# tests/provider/functional/test_prv_func_209_publication_fields.py
#
# Every field the publication wizard (Files -> Details -> Review & Publish)
# touches, beyond the refusals 205 covers: what is saved and read back, what
# Review & Publish blocks on, whitespace-only text, external link schemes,
# the contributor picker, and which YouTube links and file types Files takes.
# Drafts come from the API and are deleted at teardown.

import uuid

import pytest

from locators.provider.create_publication_locators import CreatePublicationLocators as L
from pages.provider.create_publication_page import CreatePublicationPage
from tests.api import publications as P

pytestmark = pytest.mark.functional

LICENSE = "CC_BY_4_0_ATTRIBUTION"
YOUTUBE_ID = "dQw4w9WgXcQ"
READ = (
    "query($id: UUID!){ getPublication(publicationId:$id){ title description authors publicationDate license "
    "externalSourceLink resourceType { id } sectors { id } geographies { id } } }"
)


def _open(driver, open_listing, provider_api, cleanup, segment, **fields):
    """A draft with `fields` set, opened on `segment`, and the id it was created with."""
    stem = f"zz-auto-pf-{uuid.uuid4().hex[:8]}"
    pid = provider_api.create_draft("publication", stem)
    cleanup.track("publication", pid, None)
    if fields:
        P.update(provider_api.client, pid, **fields)
    table = open_listing("individual", "Publications")
    table.search(stem)
    table.wait_for_rows(lambda rows: [r["title"] for r in rows] == [stem], f"The draft {stem!r} is not listed")
    table.row_action(stem, "Edit")
    page = CreatePublicationPage(driver)
    page.wait_with_timeout(30).until(lambda d: "/publications/edit/" in d.current_url)
    return page.open_editor_step(segment), pid, stem


def _saved(provider_api, pid):
    body = provider_api.gql(READ, {"id": pid})
    return body["data"]["getPublication"]


def _my_name(provider_api):
    """(first name to search the picker with, the full name it lists the person under)."""
    me = provider_api.gql("{ me { firstName lastName } }")["data"]["me"]
    return me["firstName"], f"{me['firstName']} {me['lastName']}".strip()


def _complete(provider_api):
    fields = P.complete_fields(provider_api.client)
    fields["license"] = LICENSE
    return fields


# No case for usage rights: the backend defaults a licence (CC BY 4.0) on every draft and cannot clear it.
BLOCKERS = {
    "none": ({}, None),
    "name": ({"title": ""}, "Enter a resource name."),
    "description": ({"description": ""}, "Enter a description."),
    "contributor": ({"authors": []}, "Add at least one contributor."),
    "date": ({"publicationDate": None}, "Enter a date."),
    "resource type": ({"resourceTypeId": None}, "Select a resource type."),
    "sector": ({"sectorIds": []}, "Select at least one sector."),
    "geography": ({"geographyIds": []}, "Select at least one geography."),
}


@pytest.mark.parametrize("missing", BLOCKERS)
def test_prv_func_209a_review_blocks_publish_on_each_missing_field(driver, open_listing, provider_api, cleanup, missing):
    """A complete draft can be published; leaving any one field out says which and disables Publish."""
    clear, message = BLOCKERS[missing]
    page, pid, _ = _open(driver, open_listing, provider_api, cleanup, "details")
    P.update(provider_api.client, pid, **{**_complete(provider_api), **clear})
    P.add_youtube(provider_api.client, pid, f"https://youtu.be/{YOUTUBE_ID}")
    page.open_editor_step("publish")
    if message is None:
        assert page.is_publish_enabled(), "Publish stayed disabled on a complete draft"
        return
    assert page.is_text_shown(message), f"Review did not ask for the {missing}; shown: {page.page_text()[-700:]}"
    assert not page.is_publish_enabled(), f"Publish was enabled with no {missing}"


@pytest.mark.parametrize("field", ["name", "description"])
def test_prv_func_209b_whitespace_only_text_counts_as_empty(driver, open_listing, provider_api, cleanup, field):
    page, _, _ = _open(driver, open_listing, provider_api, cleanup, "details")
    page.type_blank(field)
    page.press_continue()
    message = "Enter a resource name." if field == "name" else "Enter a description."
    assert page.is_text_shown(message), f"A whitespace-only {field} was accepted; shown: {page.get_inline_errors()}"
    assert "/details" in driver.current_url, f"Continue left Details with a whitespace-only {field}"


@pytest.mark.parametrize("link", ["ftp://example.org/file", "javascript:alert(1)", "example.org/page", "http//example.org"])
def test_prv_func_209c_external_link_needs_http_or_https(driver, open_listing, provider_api, cleanup, link):
    page, pid, _ = _open(driver, open_listing, provider_api, cleanup, "details")
    page.enter_external_link(link)
    assert page.is_text_shown("Enter a valid URL."), f"{link!r} was not refused"
    page.press_continue()
    assert "/details" in driver.current_url, f"Continue left Details with the link {link!r}"


@pytest.mark.parametrize("link", ["http://example.org/a", "https://example.org/a/b?c=1#d"])
def test_prv_func_209d_external_link_is_saved(driver, open_listing, provider_api, cleanup, link):
    page, pid, _ = _open(driver, open_listing, provider_api, cleanup, "details")
    page.enter_external_link(link)
    page.wait_until_synced()
    assert not page.is_text_shown("Enter a valid URL.", timeout=2), f"{link!r} was refused"
    assert _saved(provider_api, pid)["externalSourceLink"] == link, "The link was not saved"
    page.reload()
    assert page.find(L.EXTERNAL_LINK_INPUT).get_attribute("value") == link, "The link was not shown after a reload"


def test_prv_func_209e_contributor_is_added_and_removed(driver, open_listing, provider_api, cleanup):
    first, me = _my_name(provider_api)
    page, pid, _ = _open(driver, open_listing, provider_api, cleanup, "details")
    page.add_contributor(first)
    assert page.is_connected("Contributors", me), f"{me!r} was not listed after being added"
    page.wait_until_synced()
    assert _saved(provider_api, pid)["authors"] == [me], "The contributor was not saved"

    page.remove_connected(me)
    assert page.is_text_shown("No contributors added yet."), "Removing the only contributor did not empty the list"
    page.wait_until_synced()
    assert _saved(provider_api, pid)["authors"] == [], "The removal was not saved"
    page.press_continue()
    assert page.is_text_shown("Add at least one contributor."), "Details did not ask for a contributor again"


def test_prv_func_209f_details_are_saved_and_shown_in_review(driver, open_listing, provider_api, cleanup, sector_name):
    first, me = _my_name(provider_api)
    name = f"zz-auto-pf-{uuid.uuid4().hex[:8]}"
    text = f"Written by an automated test {name}"
    page, pid, _ = _open(driver, open_listing, provider_api, cleanup, "details")
    page.enter_resource_name(name)
    page.enter_description(text)
    page.enter_date("2024-03-05")
    type_name = page.choose_resource_type()
    page.add_contributor(first)
    page.select_field_options("Sector / Domain", [sector_name])
    page.select_geography("India")
    page.enter_external_link("https://example.org/source")
    page.wait_until_synced()

    saved = _saved(provider_api, pid)
    assert (saved["title"], saved["description"], saved["publicationDate"], saved["authors"]) == (
        name, text, "2024-03-05", [me]), f"The API holds {saved}"
    assert saved["externalSourceLink"] == "https://example.org/source" and saved["license"], f"The API holds {saved}"
    assert saved["resourceType"] and len(saved["sectors"]) == 1 and len(saved["geographies"]) == 1, f"The API holds {saved}"

    page.open_editor_step("publish")
    shown = page.page_text()
    missing = [v for v in (name, text, me, sector_name, "India", type_name, "https://example.org/source") if v not in shown]
    assert not missing, f"Review & Publish does not show {missing}"


YOUTUBE_ACCEPTED = [
    f"https://www.youtube.com/watch?v={YOUTUBE_ID}",
    f"https://youtu.be/{YOUTUBE_ID}",
    f"https://m.youtube.com/watch?v={YOUTUBE_ID}",
    f"https://www.youtube.com/embed/{YOUTUBE_ID}",
    f"https://www.youtube.com/shorts/{YOUTUBE_ID}",
]
YOUTUBE_REFUSED = ["https://www.youtube.com/", "https://www.youtube.com/watch", "ftp://youtu.be/" + YOUTUBE_ID, "youtu.be/" + YOUTUBE_ID]


def test_prv_func_209g_every_youtube_link_form_is_accepted(driver, open_listing, provider_api, cleanup):
    page, pid, _ = _open(driver, open_listing, provider_api, cleanup, "files")
    for count, url in enumerate(YOUTUBE_ACCEPTED, start=1):
        page.try_youtube_video(url)
        page.wait_with_timeout(30).until(lambda d: page.file_count() == count, f"{url!r} was not added as file {count}")
    page.wait_until_synced()
    assert len(P.blocks(provider_api.client, pid)) == len(YOUTUBE_ACCEPTED), "Not every video was saved"


@pytest.mark.parametrize("url", YOUTUBE_REFUSED)
def test_prv_func_209h_youtube_links_without_a_video_are_refused(driver, open_listing, provider_api, cleanup, url):
    page, _, _ = _open(driver, open_listing, provider_api, cleanup, "files")
    page.try_youtube_video(url)
    assert page.toast_shown("Enter a valid YouTube URL."), f"{url!r} was not refused"
    assert page.file_count() == 0, f"{url!r} was added to the list"


def test_prv_func_209i_unsupported_file_type_is_ignored(driver, open_listing, provider_api, cleanup, tmp_path):
    """The drop zone takes a .txt silently: it never joins the list, a PDF attached after it does."""
    page, _, _ = _open(driver, open_listing, provider_api, cleanup, "files")
    note = tmp_path / "zz-auto-note.txt"
    note.write_text("not a document")
    page.attach_file(str(note))
    pdf = tmp_path / "zz-auto-doc.pdf"
    pdf.write_bytes(P.PDF_BYTES)
    page.attach_file(str(pdf))
    page.wait_with_timeout(30).until(lambda d: page.file_count() >= 1, "The control PDF was never added")
    assert page.file_count() == 1, "The .txt file was added to the list"


def test_prv_func_209j_adding_a_contributor_twice_keeps_one(driver, open_listing, provider_api, cleanup):
    """Hard fail until DataSpaceFrontend#560 is fixed: the second add of the same person is saved as a second author."""
    first, me = _my_name(provider_api)
    page, pid, _ = _open(driver, open_listing, provider_api, cleanup, "details")
    page.add_contributor(first)
    assert page.is_connected("Contributors", me), f"{me!r} was not listed after being added"
    try:
        page.add_contributor(first)
    except Exception:
        pass  # a picker that no longer offers the person is the same refusal
    page.wait_until_synced()
    assert _saved(provider_api, pid)["authors"] == [me], "The contributor was saved twice (DataSpaceFrontend#560)"
