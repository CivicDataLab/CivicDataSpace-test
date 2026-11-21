# tests/provider/functional/test_prv_func_205_publication_wizard_validation.py
#
# Publication wizard (Files -> Details -> Review & Publish) refusals, from the
# frontend's publications/model.ts and FilesStep: only pdf/doc/docx/ppt/pptx
# files, YouTube links must be YouTube, and Details requires a name,
# description, contributor, date, resource type, sector and geography, with a
# valid external link when one is given. (Usage rights is required too, but the
# form preselects CC BY 4.0, so it cannot be left empty.) Drafts come from the
# API and are deleted at teardown.

import uuid

import pytest

from pages.provider.create_publication_page import CreatePublicationPage

pytestmark = pytest.mark.functional

DETAILS_ERRORS = ["Enter a resource name.", "Enter a description.", "Enter a date.", "Select a resource type.", "Select at least one sector.",
                  "Select at least one geography."]


def _draft(driver, open_listing, provider_api, cleanup) -> CreatePublicationPage:
    stem = f"zz-auto-pb-{uuid.uuid4().hex[:8]}"
    cleanup.track("publication", provider_api.create_draft("publication", stem), None)
    table = open_listing("individual", "Publications")
    table.search(stem)
    table.wait_for_rows(lambda rows: [r["title"] for r in rows] == [stem], f"The draft {stem!r} is not listed")
    table.row_action(stem, "Edit")
    page = CreatePublicationPage(driver)
    page.wait_with_timeout(30).until(lambda d: "/publications/edit/" in d.current_url)
    return page


def test_prv_func_205a_file_type_and_size_limits(driver, open_listing, provider_api, cleanup, tmp_path):
    """Only office documents and PDFs are offered, and a PDF over 50 MB is refused before upload."""
    page = _draft(driver, open_listing, provider_api, cleanup).open_editor_step("files")
    assert page.accepted_file_types() == ".pdf,.doc,.docx,.ppt,.pptx"

    big = tmp_path / "zz-auto-big.pdf"
    with open(big, "wb") as f:
        f.truncate(51 * 1024 * 1024)
    page.attach_file(str(big))
    assert page.toast_shown("zz-auto-big.pdf is larger than the 50 MB limit."), "A 51 MB PDF was not refused"
    assert page.file_count() == 0, "The refused 51 MB PDF was added to the list"


def test_prv_func_205b_non_youtube_link_refused(driver, open_listing, provider_api, cleanup):
    page = _draft(driver, open_listing, provider_api, cleanup).open_editor_step("files")
    page.try_youtube_video("https://example.com/watch?v=dQw4w9WgXcQ")
    assert page.toast_shown("Enter a valid YouTube URL."), "A non-YouTube link was not refused"
    assert page.file_count() == 0, "The refused link was added to the list"


def test_prv_func_205c_details_required_fields(driver, open_listing, provider_api, cleanup):
    page = _draft(driver, open_listing, provider_api, cleanup).open_editor_step("details")
    page.clear_resource_name().press_continue()
    page.page_text_once_shown(DETAILS_ERRORS[1:2])
    shown = page.get_inline_errors()
    missing = [m for m in DETAILS_ERRORS if m not in shown]
    assert not missing, f"Details did not ask for {missing}; shown: {shown}"
    assert page.is_text_shown("Add at least one contributor."), "Details did not ask for a contributor"
    assert "/details" in driver.current_url, "Continue left Details with every required field empty"


def test_prv_func_205d_invalid_external_link_refused(driver, open_listing, provider_api, cleanup):
    page = _draft(driver, open_listing, provider_api, cleanup).open_editor_step("details")
    page.enter_external_link("not a url")
    page.press_continue()
    assert page.is_text_shown("Enter a valid URL.") or page.toast_shown("Enter a valid URL."), \
        "An external link of 'not a url' was not refused"
