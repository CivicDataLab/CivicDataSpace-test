# tests/consumer/smoke/test_con_events.py
#
# Events feature (DataSpaceFrontend PR #515 "Implement event management",
# #516 "Implement event management features including EventCard, EventCover,
# ..." and #517 "Replace Image component with MediaImage in EventCard", all
# merged into dev 2026-11-04). This is a brand-new consumer surface: a public
# /events listing and /events/<slug> detail page, with a Luma embed and
# EventCover/HostAvatar images driven by DataSpaceBackend#275's new
# cover_url search field.
#
# No existing Page Object covered /events, so this adds a minimal one
# (pages/consumer/events_page.py + locators/consumer/events_locators.py).
#
# Real events are picked from the backend at runtime, never hardcoded, so
# this keeps working as long as some published event exists on the
# environment under test. Because this is a brand-new page rather than a
# regression fix, there is no "broken" prior state to replay for red/green
# (see test file docstrings below for what was actually proven and how).

import os

import pytest
import requests

from pages.consumer.events_page import EventsPage

pytestmark = pytest.mark.smoke

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")
API_BASE_URL = os.getenv("API_BASE_URL", "https://dev.api.civicdataspace.in").rstrip("/")


@pytest.fixture(scope="module")
def published_events():
    resp = requests.get(f"{API_BASE_URL}/api/search/event/", params={"size": 200}, timeout=20)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        pytest.skip("no published events on this environment to test against")
    return results


def test_con_events_001_listing_shows_published_events(driver, published_events):
    """/events renders at least one card linking to a real event's detail
    page. Proven failable: a page that errored or stayed on a loading state
    would show zero matching links."""
    page = EventsPage(driver).load_listing(BASE_URL)
    links = {a.get_attribute("href") or "" for a in page.card_links()}
    assert links, "Con_EVENTS_001: /events rendered no event card links at all"

    expected_hrefs = {f"{BASE_URL.rstrip('/')}/events/{e['url_slug']}" for e in published_events}
    matched = links & expected_hrefs
    assert matched, (
        "Con_EVENTS_001: none of the rendered card links match a real "
        f"published event's url_slug. Rendered: {links}"
    )


def test_con_events_002_detail_page_loads_the_right_event(driver, published_events):
    """Opening a real event's /events/<slug> shows that event's own name as
    the page heading, not a generic error or another event's content."""
    event = published_events[0]
    page = EventsPage(driver).open_event(event["url_slug"], BASE_URL)
    header = page.detail_header_text()
    assert header.strip() == event["name"].strip(), (
        f"Con_EVENTS_002: expected detail-page heading {event['name']!r}, "
        f"got {header!r} for /events/{event['url_slug']}"
    )


def test_con_events_003_detail_page_embeds_the_right_luma_event(driver, published_events):
    """For an event with a Luma embed, the detail page's iframe points at
    that same event's Luma id -- not a different event's, and not missing.
    Ties the frontend detail page to a real backend record rather than
    just checking "some iframe exists"."""
    candidates = [e for e in published_events if e.get("cover_url")]
    if not candidates:
        pytest.skip("no published event on this environment has a resolvable Luma cover to check")
    event = candidates[0]

    # The event's own Luma embed id isn't in the search response, so look it
    # up directly from the public GraphQL event-by-slug query.
    query = (
        '{ eventBySlug(publicId: "%s") { lumaEmbed { src } } }' % event["url_slug"]
    )
    gql_resp = requests.post(f"{API_BASE_URL}/api/graphql", json={"query": query}, timeout=20)
    gql_resp.raise_for_status()
    body = gql_resp.json()
    assert not body.get("errors"), body["errors"]
    embed_src = ((body["data"].get("eventBySlug") or {}).get("lumaEmbed") or {}).get("src")
    if not embed_src:
        pytest.skip(f"event {event['url_slug']!r} has no lumaEmbed on the GraphQL side to compare against")

    page = EventsPage(driver).open_event(event["url_slug"], BASE_URL)
    assert page.has_luma_iframe(), (
        f"Con_EVENTS_003: /events/{event['url_slug']} has a resolvable "
        "Luma cover_url in search but no Luma iframe on its detail page"
    )
    rendered_src = page.luma_iframe_src() or ""
    import re

    expected_id = re.search(r"evt-[A-Za-z0-9]+", embed_src)
    assert expected_id and expected_id.group() in rendered_src, (
        f"Con_EVENTS_003: detail page's iframe src {rendered_src!r} does not "
        f"contain this event's own Luma id (from {embed_src!r})"
    )
