# tests/provider/smoke/test_prv_029_event_lifecycle.py
#
# Provider events (Details -> Review & Publish), which had no UI test. An event
# draft is made through the API, completed in the editor, published, and then
# found on the public /events page. Fields save when Continue is pressed, not on
# blur. Deleted at teardown by `cleanup`.

import os
import uuid

import pytest

from pages.consumer.events_page import EventsPage
from pages.provider.editor_wizard_page import EditorWizardPage
from pages.provider.event_editor_page import EventEditorPage
from pages.provider.listing_table_page import ListingTablePage

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")
EMBED_SRC = "https://luma.com/embed/event/evt-zzauto/simple"


@pytest.mark.smoke
def test_prv_029_event_publish_and_public_page(driver, open_listing, provider_api, cleanup):
    """
    Test Case ID: test_prv_029_event_publish_and_public_page
    A completed event saves on Continue, survives a reload, publishes, and shows on /events.
    Steps:
      1. Create an event draft through the API and open it from the Events listing
      2. Fill location, dates and a Luma iframe; Continue to Review & Publish
      3. The review shows the values, 'Ready to publish' and the embed
      4. Back on Details after a reload, every value is still there
      5. Publish: the listing says Published and /events/<public link> shows the event
    """
    stem = f"zz-auto-ev-{uuid.uuid4().hex[:8]}"
    cleanup.track("event", provider_api.create_draft("event", stem), None)
    table = open_listing("individual", "Events")
    table.search(stem)
    table.wait_for_rows(lambda rows: [r["title"] for r in rows] == [stem], f"The draft {stem!r} is not listed")
    table.row_action(stem, "Edit")
    EditorWizardPage(driver).wait_for_editor()

    page = EventEditorPage(driver)
    page.fill(location="Online", start="2030-01-10", end="2030-01-11",
              embed=f'<iframe src="{EMBED_SRC}" width="600" height="450" allowfullscreen></iframe>')
    page.continue_to_review()

    assert page.readiness() == "Ready to publish", page.get_page_text()
    assert page.preview_value("LOCATION") == "Online"
    assert page.preview_value("START DATE") == "10 Jan 2030"
    assert page.preview_value("END DATE") == "11 Jan 2030"
    assert page.preview_iframe_src() == EMBED_SRC
    slug = page.preview_value("PUBLIC LINK")

    details = page.open_step_url("details")
    saved = details.values()
    assert {k: saved[k] for k in ("name", "location", "start", "end")} == {
        "name": stem, "location": "Online", "start": "2030-01-10", "end": "2030-01-11"}
    assert EMBED_SRC in saved["embed"], saved["embed"]

    details.open_step_url("preview").publish()
    table = ListingTablePage(driver).open_section("Events")
    table.search(stem)
    table.wait_for_rows(lambda rows: rows == [{"title": stem, "status": "Published"}], "The event is not listed as Published")

    public = EventsPage(driver).open_event(slug, BASE_URL)
    assert stem in public.detail_header_text()
    assert public.luma_iframe_src() == EMBED_SRC
