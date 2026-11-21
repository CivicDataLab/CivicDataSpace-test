# tests/provider/smoke/test_prv_028_unsaved_changes_badge.py
#
# DataSpaceFrontend#544: an editor's header says 'Unsaved changes' while a field
# holds text that has not been sent, and 'All changes saved' only once it is.
# Before it, the header said 'All changes saved' throughout, which is how
# DataSpaceFrontend#542 (a Source Website edit never sent) went unnoticed.

import uuid

import pytest

from pages.provider.create_ai_model_page import CreateAiModelPage
from pages.provider.create_collaborative_page import CreateCollaborativePage
from pages.provider.create_dataset_page import CreateDatasetPage
from pages.provider.create_usecase_page import CreateUsecasePage
from pages.provider.editor_wizard_page import EditorWizardPage

# kind: (listing section, page, step, read the field back, value typed)
EDITORS = {
    "dataset": ("Datasets", CreateDatasetPage, "metadata", "get_source_website_value", "https://example.com/{stem}"),
    "usecase": ("Use Cases", CreateUsecasePage, "builder", "get_subtitle_value", "Subtitle {stem}"),
    "collaborative": ("Collaboratives", CreateCollaborativePage, "about", "get_platform_url_value", "https://example.com/{stem}"),
    "aimodel": ("AI Models", CreateAiModelPage, "details", "get_intended_use_value", "Intended use {stem}"),
}


@pytest.mark.smoke
@pytest.mark.parametrize("kind", list(EDITORS))
def test_prv_028_header_reports_unsaved_changes(kind, driver, open_listing, provider_api, cleanup):
    """
    Test Case ID: test_prv_028_header_reports_unsaved_changes
    The header says 'Unsaved changes' while typed text is unsent, then saves it on leaving the field.
    Steps:
      1. Create a draft through the API and open it from the listing
      2. Type into a text field without leaving it: the header reads 'Unsaved changes'
      3. Leave the field: the header reads 'All changes saved'
      4. Reload from the backend: the field holds the typed text
    """
    section, page_cls, step, read_back, value = EDITORS[kind]
    stem = f"zz-auto-us-{uuid.uuid4().hex[:8]}"
    value = value.format(stem=stem)
    cleanup.track(kind, provider_api.create_draft(kind, stem, None), None)

    table = open_listing("individual", section)
    table.search(stem)
    table.wait_for_rows(lambda rows: [r["title"] for r in rows] == [stem], f"The draft {stem!r} is not listed")
    table.row_action(stem, "Edit")
    EditorWizardPage(driver).wait_for_editor()

    page = page_cls(driver).open_step(step)
    page.type_without_leaving(value)
    assert page.save_status() == "Unsaved changes", "The header does not flag text that has not been saved"

    page.wait_until_synced()
    assert getattr(page.reload(), read_back)() == value
