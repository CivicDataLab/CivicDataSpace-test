# tests/provider/smoke/test_prv_021_wizard_validation.py
#
# What each editor wizard step does when Continue is pressed with required
# fields missing: it must stay on the step, say what is missing, show that
# message where the user can see it, and tie each field error to its control.
#
# The messages are the product's own wording. Where the provider exploration
# found the behaviour wrong, the test states the CORRECT behaviour and is a
# strict xfail, so fixing the product turns it red until the marker is removed.
# The draft comes from the API ('zz-auto-' name) and the `cleanup` fixture
# deletes it.

import uuid

import pytest

from pages.provider.create_usecase_page import CreateUsecasePage
from pages.provider.editor_wizard_page import EditorWizardPage
from pages.provider.wizard_validation_page import WizardValidationPage

SECTIONS = {"dataset": "Datasets", "usecase": "Use Cases", "collaborative": "Collaboratives", "aimodel": "AI Models"}

# (kind, step) -> the messages the step shows when it is empty
MESSAGES = {
    ("dataset", "resources"): ["Add at least one dataset file to continue."],
    ("dataset", "metadata"): ["Description is required", "Sector is required", "Tags are required"],
    ("usecase", "builder"): ["Upload a thumbnail image"],
    ("usecase", "connect"): ["Select at least one SDG goal", "Select at least one sector", "Connect at least one dataset"],
    ("collaborative", "about"): ["Add a description to continue", "Select at least one sector", "Select at least one SDG goal"],
    ("aimodel", "versions"): ["Add a version to continue."],
    ("aimodel", "details"): ["Add a description of the model.", "Select at least one sector."],
}

NOT_IN_VIEW = pytest.mark.xfail(
    strict=True,
    reason="Exploration issue I-25: after a failed Continue the error stays outside the viewport, with no scroll or focus move",
)
NOT_ASSOCIATED = pytest.mark.xfail(
    strict=True,
    reason="Exploration issue I-8: field errors are not linked to their controls (aria-invalid / aria-describedby)",
)


def _open_step(kind, step, driver, open_listing, provider_api, cleanup):
    """Create a draft, open it from the listing and go to `step`."""
    stem = f"zz-auto-vd-{uuid.uuid4().hex[:8]}"
    cleanup.track(kind, provider_api.create_draft(kind, stem), None)
    table = open_listing("individual", SECTIONS[kind])
    table.search(stem)
    table.wait_for_rows(lambda rows: [r["title"] for r in rows] == [stem], f"The draft {stem!r} is not listed")
    table.row_action(stem, "Edit")
    EditorWizardPage(driver).wait_for_editor().open_step(step)
    return WizardValidationPage(driver)


@pytest.mark.functional
@pytest.mark.parametrize("kind,step", list(MESSAGES), ids=lambda v: v)
def test_prv_021_failed_continue_says_what_is_missing(kind, step, driver, open_listing, provider_api, cleanup):
    """
    Test Case ID: test_prv_021_failed_continue_says_what_is_missing
    Continue on an empty step stays put and lists every missing required field.
    Steps:
      1. Create a draft through the API, open it and go to the step
      2. Press Continue with nothing filled in
      3. The editor stays on the step and shows each required-field message
    """
    page = _open_step(kind, step, driver, open_listing, provider_api, cleanup)
    messages = MESSAGES[(kind, step)]
    page.press_continue(messages[0])
    missing = [m for m in messages if not page.has_message(m)]
    assert not missing, f"{kind}/{step}: no message for {missing}"


IN_VIEW_CASES = [
    pytest.param("dataset", "resources", id="dataset-resources"),
    pytest.param("dataset", "metadata", id="dataset-metadata", marks=NOT_IN_VIEW),
    pytest.param("usecase", "builder", id="usecase-builder", marks=NOT_IN_VIEW),
    pytest.param("usecase", "connect-sdg", id="usecase-connect-sdg-only", marks=NOT_IN_VIEW),
    pytest.param("aimodel", "details", id="aimodel-details", marks=NOT_IN_VIEW),
]


@pytest.mark.functional
@pytest.mark.parametrize("kind,step", IN_VIEW_CASES)
def test_prv_021_failed_continue_shows_an_error_in_view(kind, step, driver, open_listing, provider_api, cleanup, sector_name):
    """
    Test Case ID: test_prv_021_failed_continue_shows_an_error_in_view
    After a failed Continue at least one error is visible without scrolling.
    The 'connect-sdg' case has everything but the SDG goal filled in, so SDG is
    the only message there is.
    Steps:
      1. Create a draft, open it and go to the step (for connect-sdg, give it
         a sector and a dataset first)
      2. Press Continue
      3. One of the messages sits inside the visible part of the window
    """
    if step == "connect-sdg":
        page = _open_step(kind, "connect", driver, open_listing, provider_api, cleanup)
        usecase = CreateUsecasePage(driver)
        usecase.select_sectors([sector_name]).wait_until_synced()
        usecase.connect_first_dataset()
        usecase.wait_until_synced()
        messages = ["Select at least one SDG goal"]
    else:
        page = _open_step(kind, step, driver, open_listing, provider_api, cleanup)
        messages = MESSAGES[(kind, step)]
    page.press_continue(messages[0])
    assert any(page.is_in_view(m) for m in messages), (
        f"{kind}/{step}: none of {messages} is inside the visible window after Continue"
    )


ASSOCIATION_CASES = [
    pytest.param(kind, step, id=f"{kind}-{step}", marks=NOT_ASSOCIATED)
    for kind, step in [("dataset", "metadata"), ("usecase", "connect"), ("collaborative", "about"), ("aimodel", "details")]
]


@pytest.mark.functional
@pytest.mark.parametrize("kind,step", ASSOCIATION_CASES)
def test_prv_021_field_errors_are_linked_to_their_controls(kind, step, driver, open_listing, provider_api, cleanup):
    """
    Test Case ID: test_prv_021_field_errors_are_linked_to_their_controls
    Each field error belongs to a control marked aria-invalid whose
    aria-describedby names the error, so assistive technology can announce it.
    Steps:
      1. Create a draft, open it and go to the step
      2. Press Continue with nothing filled in
      3. No visible field error is left without a control pointing at it
    """
    page = _open_step(kind, step, driver, open_listing, provider_api, cleanup)
    page.press_continue(MESSAGES[(kind, step)][0])
    orphans = page.unassociated_errors()
    assert not orphans, f"{kind}/{step}: errors with no aria-invalid control pointing at them: {orphans}"
