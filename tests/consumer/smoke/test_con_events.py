# tests/consumer/smoke/test_con_events.py
#
# Public Events pages smoke/functional coverage
# (DataSpaceFrontend#515 "Implement event management",
#  #516 eventBySlug publicId fix, #517 EventCard MediaImage follow-up —
#  all merged into dev within the same hour, covered together).
#
# Not marked `readonly`: /events 307s to /login on prod right now (the
# feature is only on dev). Leaving the marker off keeps this file out of
# the prod gate (readonly is opt-in per pytest.ini) until the feature ships
# — see the PR body for the live check.

import os

import pytest

from pages.consumer.events_page import EVENTS_PATH, EventDetailPage, EventsPage

pytestmark = pytest.mark.smoke

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")


@pytest.fixture
def events_page(driver):
    return EventsPage(driver).load(BASE_URL)


def test_events_page_loads(events_page):
    """/events must resolve without bouncing away to another route."""
    url = events_page.current_path()
    assert EVENTS_PATH in url, (
        f"Expected to land on {EVENTS_PATH}, ended up at {url!r}"
    )


def test_events_page_has_heading(events_page):
    heading = events_page.heading_text()
    assert heading == "Events", (
        f"{BASE_URL}{EVENTS_PATH} heading was {heading!r}, expected 'Events'"
    )


def test_events_page_lists_published_events(events_page):
    """
    The listing must render at least one real event card. Dev has published
    events in the live event search index (verified at run time, not
    hardcoded), so an empty listing here means the page, not the data, is
    broken.
    """
    hrefs = events_page.event_card_hrefs()
    assert hrefs, (
        f"{BASE_URL}{EVENTS_PATH} rendered no event cards, but the event "
        "search API has published events right now"
    )


@pytest.mark.functional
def test_event_detail_page_loads_from_listing(events_page, driver):
    """Clicking through from the listing must land on a working detail page."""
    hrefs = events_page.event_card_hrefs()
    if not hrefs:
        pytest.skip("No event cards rendered — see test_events_page_lists_published_events")
    detail = EventDetailPage(driver).load_href(hrefs[0], BASE_URL)
    heading = detail.heading_text()
    assert heading, (
        f"{hrefs[0]} rendered no heading — the event detail page loaded "
        "but has nothing in its <h1>"
    )


@pytest.mark.regression
def test_event_detail_page_404s_for_unknown_slug(driver):
    """An event slug that doesn't exist must 404 cleanly (notFound()), not error."""
    detail = EventDetailPage(driver).load_href(
        "/events/does-not-exist-test-sync-probe", BASE_URL
    )
    # Next.js's App Router notFound() renders the route's own not-found UI
    # without changing the URL, so the path itself still carries the slug.
    assert "/events/does-not-exist-test-sync-probe" in detail.current_path()
    body_text = driver.find_element("tag name", "body").text.lower()
    assert "404" in body_text or "not found" in body_text or "could not be found" in body_text, (
        f"Expected a 404/not-found page for an unknown event slug, got body "
        f"text starting: {body_text[:200]!r}"
    )
