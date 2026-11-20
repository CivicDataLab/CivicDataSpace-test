# tests/provider/functional/test_prv_func_204_event_wizard_validation.py
#
# Event editor validation, from the rules in the frontend's events/model.ts:
# Location, dates and a Luma embed are required; the end date may not be before
# the start; the embed must be an https lu.ma / luma.com /embed/ URL or an iframe
# of one, with no script, event-handler attribute or credentials. Drafts come
# from the API and are deleted at teardown.

import uuid

import pytest

from pages.provider.editor_wizard_page import EditorWizardPage
from pages.provider.event_editor_page import EventEditorPage

pytestmark = pytest.mark.functional

EMBED_ERROR = "Paste a Luma embed iframe or an https://lu.ma/embed/ URL."
BAD_EMBEDS = {
    "http scheme": "http://lu.ma/embed/event/evt-zzauto/simple",
    "other host": "https://example.com/embed/event/evt-zzauto/simple",
    "not an embed path": "https://lu.ma/evt-zzauto",
    "credentials": "https://user:pass@lu.ma/embed/event/evt-zzauto/simple",
    "script": '<script>alert(1)</script><iframe src="https://lu.ma/embed/event/evt-zzauto/simple"></iframe>',
    "event handler": '<iframe src="https://lu.ma/embed/event/evt-zzauto/simple" onload="alert(1)"></iframe>',
}
GOOD_EMBEDS = {
    "lu.ma URL": "https://lu.ma/embed/event/evt-zzauto/simple",
    "luma.com iframe": '<iframe src="https://luma.com/embed/event/evt-zzauto/simple" width="600"></iframe>',
}


def _editor(driver, open_listing, provider_api, cleanup) -> EventEditorPage:
    stem = f"zz-auto-ev-{uuid.uuid4().hex[:8]}"
    cleanup.track("event", provider_api.create_draft("event", stem), None)
    table = open_listing("individual", "Events")
    table.search(stem)
    table.wait_for_rows(lambda rows: [r["title"] for r in rows] == [stem], f"The draft {stem!r} is not listed")
    table.row_action(stem, "Edit")
    EditorWizardPage(driver).wait_for_editor()
    return EventEditorPage(driver)


def test_prv_func_204a_required_fields_block_continue(driver, open_listing, provider_api, cleanup):
    page = _editor(driver, open_listing, provider_api, cleanup)
    page.press_continue()
    page.page_text_once_shown(["Location is required."])
    errors = page.get_inline_errors()
    assert errors == ["Location is required.", "Start date is required.", "End date is required.",
                      "A Luma embed is required."], errors
    assert "/details" in driver.current_url, "Continue left Details with every required field empty"
    assert "Incomplete" in page.get_step_text("Details")


def test_prv_func_204b_end_date_before_start_refused(driver, open_listing, provider_api, cleanup):
    page = _editor(driver, open_listing, provider_api, cleanup)
    page.fill(location="Online", start="2030-01-10", end="2030-01-09", embed=GOOD_EMBEDS["lu.ma URL"])
    page.press_continue()
    page.page_text_once_shown(["End date must be on or after the start date."])
    assert page.get_inline_errors() == ["End date must be on or after the start date."]
    assert "/details" in driver.current_url


def test_prv_func_204c_embed_shapes(driver, open_listing, provider_api, cleanup):
    """Each refused shape shows the embed error and keeps the step; each accepted one reaches the review."""
    page = _editor(driver, open_listing, provider_api, cleanup)
    page.fill(location="Online", start="2030-01-10", end="2030-01-10")
    accepted = []
    for label, embed in BAD_EMBEDS.items():
        page.fill(embed=embed).press_continue()
        if not page.is_text_shown(EMBED_ERROR, timeout=5) or "/details" not in driver.current_url:
            accepted.append(label)
    assert not accepted, f"Embeds accepted that the editor should refuse: {accepted}"

    for label, embed in GOOD_EMBEDS.items():
        page.fill(embed=embed).continue_to_review()
        assert page.readiness() == "Ready to publish", f"{label}: {page.get_page_text()}"
        page.open_step_url("details")


def test_prv_func_204d_incomplete_event_cannot_publish(driver, open_listing, provider_api, cleanup):
    page = _editor(driver, open_listing, provider_api, cleanup)
    page.open_step_url("preview")
    assert page.readiness() == "Needs attention"
    assert not page.is_publish_enabled(), "Publish is enabled for an event with no location, dates or embed"
