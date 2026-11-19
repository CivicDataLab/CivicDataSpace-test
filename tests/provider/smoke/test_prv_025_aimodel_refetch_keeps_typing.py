# tests/provider/smoke/test_prv_025_aimodel_refetch_keeps_typing.py
#
# DataSpaceFrontend#534: on an AI model's Model Information step, saving one
# field refetches the model, and the refetch used to refill the whole form from
# the backend, wiping text still being typed in another field.

import time
import uuid

import pytest

from pages.provider.create_ai_model_page import CreateAiModelPage
from pages.provider.editor_wizard_page import EditorWizardPage


@pytest.mark.smoke
def test_prv_025_aimodel_refetch_keeps_unsaved_text(driver, open_listing, provider_api, cleanup):
    """
    Test Case ID: test_prv_025_aimodel_refetch_keeps_unsaved_text
    Text typed into Intended Use survives the refetch that follows saving the name.
    Steps:
      1. Create an AI model draft through the API and open it from the listing
      2. Change the name, then type into Intended Use without leaving it
      3. Wait for the name's save and refetch to finish
      4. Intended Use still holds the typed text
    """
    stem = f"zz-auto-rf-{uuid.uuid4().hex[:8]}"
    cleanup.track("aimodel", provider_api.create_draft("aimodel", stem, None), None)

    table = open_listing("individual", "AI Models")
    table.search(stem)
    table.wait_for_rows(lambda rows: [r["title"] for r in rows] == [stem], f"The draft {stem!r} is not listed")
    table.row_action(stem, "Edit")
    EditorWizardPage(driver).wait_for_editor()

    page = CreateAiModelPage(driver).open_step("details")
    typed = f"Typed during a save {stem}"
    page.rename_then_type_intended_use(f"{stem} renamed", typed)
    page.wait_until_synced()

    for _ in range(25):  # a refetch can land a moment after the header says saved
        value = page.get_intended_use_value()
        assert value == typed, f"Intended Use was overwritten by the refetch: {value!r} (expected {typed!r})"
        time.sleep(0.2)
