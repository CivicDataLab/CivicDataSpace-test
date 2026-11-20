# tests/consumer/smoke/test_con_publications.py
#
# The public /publications listing and detail pages, which had no test. The
# publication is picked from the search API at runtime; the test skips where
# nothing is published (prod had none on 2026-11-20).

import os

import pytest
import requests

from pages.consumer.publications_page import PublicationsPage

pytestmark = pytest.mark.smoke

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in").rstrip("/")
API_BASE_URL = os.getenv("API_BASE_URL", "https://dev.api.civicdataspace.in").rstrip("/")


@pytest.fixture(scope="module")
def published_publications():
    resp = requests.get(f"{API_BASE_URL}/api/search/publication/", params={"size": 100}, timeout=20)
    resp.raise_for_status()
    results = resp.json().get("results", [])
    if not results:
        pytest.skip("no published publications on this environment")
    return results


def test_con_pub_001_listing_links_to_published_publications(driver, published_publications):
    """Every card on /publications links to a publication the search API lists as published."""
    hrefs = PublicationsPage(driver).load_listing(BASE_URL).card_hrefs()
    known = {f"{BASE_URL}/publications/{p['url_slug'] or p['id']}" for p in published_publications}
    assert hrefs & known, f"No card links to a published publication. Cards: {sorted(hrefs)[:5]}"
    assert hrefs <= known, f"Cards link to publications the API does not list: {sorted(hrefs - known)}"


def test_con_pub_002_detail_page_shows_the_publication(driver, published_publications):
    """Opening a publication by its slug shows its own title."""
    pub = published_publications[0]
    page = PublicationsPage(driver).open_publication(pub["url_slug"] or pub["id"], BASE_URL)
    assert page.title() == pub["title"].strip(), f"{pub['url_slug']} shows {page.title()!r}, not {pub['title']!r}"
