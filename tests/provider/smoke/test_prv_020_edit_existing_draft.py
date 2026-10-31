# tests/provider/smoke/test_prv_020_edit_existing_draft.py
#
# Resuming an existing draft: open it from the listing's Edit action, change
# fields (the editor autosaves), reload from the backend and find them saved.
# The create tests only read back what they typed in the same session, which a
# form that never reached the backend would also pass.
#
# The draft comes from the API under a 'zz-auto-' name and is deleted by the
# `cleanup` fixture. Run the individual and the org cases with the account that
# owns them (TEST_USER_INDEX), e.g. `-k individual` / `-k org`.

import uuid

import pytest

from pages.provider.create_ai_model_page import CreateAiModelPage
from pages.provider.create_collaborative_page import CreateCollaborativePage
from pages.provider.create_dataset_page import CreateDatasetPage
from pages.provider.create_usecase_page import CreateUsecasePage
from pages.provider.editor_wizard_page import EditorWizardPage

SECTIONS = {
    "dataset": "Datasets",
    "usecase": "Use Cases",
    "collaborative": "Collaboratives",
    "aimodel": "AI Models",
}


def _edit_dataset(driver, sector, stem):
    """Metadata step: title, description, sector, source website."""
    page = CreateDatasetPage(driver).open_step("metadata")
    page.enter_title(f"{stem} renamed").wait_until_synced()
    page.enter_description(f"Edited description {stem}").wait_until_synced()
    page.select_sectors([sector]).wait_until_synced()
    page.enter_source_website("https://example.com/edited").wait_until_synced()

    def check():
        reloaded = page.reload()
        assert reloaded.get_title_value() == f"{stem} renamed"
        assert f"Edited description {stem}" in reloaded.get_description_value()
        assert sector in reloaded.get_selected_sectors()
        assert reloaded.get_source_website_value() == "https://example.com/edited"

    return check


def _edit_usecase(driver, sector, stem):
    """Builder: title, subtitle, a text block. Connect: sector."""
    page = CreateUsecasePage(driver).open_step("builder")
    page.enter_title(f"{stem} renamed").wait_until_synced()
    page.enter_subtitle(f"Edited subtitle {stem}").wait_until_synced()
    page.add_text_block(f"Edited block {stem}").done_editing().wait_until_synced()
    page.open_step("connect")  # Continue is blocked until a thumbnail is uploaded
    page.select_sectors([sector]).wait_until_synced()

    def check():
        assert sector in page.reload().get_selected_sectors()
        builder = page.open_step("builder")
        assert builder.get_title_value() == f"{stem} renamed"
        assert builder.get_subtitle_value() == f"Edited subtitle {stem}"
        assert builder.has_saved_text_block(f"Edited block {stem}"), "The text block was not saved"

    return check


def _edit_collaborative(driver, sector, stem):
    """About: name, description, platform link, sector."""
    page = CreateCollaborativePage(driver).open_step("about")
    page.edit_collaborative_name(f"{stem} renamed").wait_until_synced()
    page.enter_description(f"Edited description {stem}").wait_until_synced()
    page.enter_platform_url("https://example.com/edited").wait_until_synced()
    page.select_sectors([sector]).wait_until_synced()

    def check():
        reloaded = page.reload()
        assert reloaded.get_collaborative_name_value() == f"{stem} renamed"
        assert f"Edited description {stem}" in reloaded.get_description_value()
        assert reloaded.get_platform_url_value() == "https://example.com/edited"
        assert sector in reloaded.get_selected_sectors()

    return check


def _edit_aimodel(driver, sector, stem):
    """Model Information: name, description, intended use, sector."""
    page = CreateAiModelPage(driver).open_step("details")
    page.enter_model_name(f"{stem} renamed").wait_until_synced()
    page.enter_description(f"Edited description {stem}").wait_until_synced()
    page.enter_intended_use(f"Edited intended use {stem}").wait_until_synced()
    page.select_sectors([sector]).wait_until_synced()

    def check():
        reloaded = page.reload()
        assert reloaded.get_model_name_value() == f"{stem} renamed"
        assert f"Edited description {stem}" in reloaded.get_description_text()
        assert reloaded.get_intended_use_value() == f"Edited intended use {stem}"
        assert sector in reloaded.get_selected_sectors()

    return check


EDITORS = {
    "dataset": _edit_dataset,
    "usecase": _edit_usecase,
    "collaborative": _edit_collaborative,
    "aimodel": _edit_aimodel,
}

scopes = pytest.mark.parametrize(
    "scope",
    [pytest.param("individual", marks=pytest.mark.smoke), "org"],
)


@pytest.mark.functional
@scopes
@pytest.mark.parametrize("kind", list(EDITORS))
def test_prv_020_edit_existing_draft_persists(
    scope, kind, driver, open_listing, provider_api, cleanup, sector_name, request
):
    """
    Test Case ID: test_prv_020_edit_existing_draft_persists
    Edits made to an existing draft in its editor are still there after a reload.
    Steps:
      1. Create a draft through the API
      2. Open its listing, find the draft and press Edit
      3. Change its fields in the editor and wait for the autosave
      4. Reload from the backend and read every field back
    """
    org = request.getfixturevalue("writable_org") if scope == "org" else None
    stem = f"zz-auto-ed-{uuid.uuid4().hex[:8]}"
    cleanup.track(kind, provider_api.create_draft(kind, stem, org), org)

    table = open_listing(scope, SECTIONS[kind])
    table.search(stem)
    table.wait_for_rows(lambda rows: [r["title"] for r in rows] == [stem], f"The draft {stem!r} is not listed")
    table.row_action(stem, "Edit")
    EditorWizardPage(driver).wait_for_editor()

    EDITORS[kind](driver, sector_name, stem)()
