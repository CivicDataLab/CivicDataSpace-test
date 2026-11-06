# tests/consumer/functional/test_con_func_303_published_collaborative.py
#
# A collaborative published through the API shows its provider's values on the
# public detail page and is listed on /collaboratives (its only filter is a
# client-side search box). The last test unpublishes, so it must stay last.

import datetime

import pytest

from pages.consumer.published_item_page import PublishedItemPage
from tests.consumer.functional.conftest import unpublish_kind

pytestmark = [pytest.mark.functional]


@pytest.fixture
def page(driver):
    return PublishedItemPage(driver)


def _detail(page, base_url, c):
    return page.open_detail(base_url, "collaborative", c["slug"], c["title"])


def test_detail_shows_provider_values(page, base_url, published_collaborative):
    c = published_collaborative
    text = _detail(page, base_url, c).text()
    today = datetime.date.today()
    for value in (c["title"], c["summary"], c["tag"], c["geography"]["name"],
                  f"{today:%B} {today.day}, {today.year}"):
        assert value in text, f"{value!r} missing from collaborative detail"
    alts = page.image_alts()
    assert c["sector"]["name"] in alts and c["sdg"]["name"] in alts, alts
    assert c["platform_url"] in page.external_links()


def test_listing_shows_card(page, base_url, published_collaborative):
    c = published_collaborative
    assert page.listing_shows(base_url, "collaboratives", c["title"])
    assert page.shows(c["summary"], timeout=3)


def test_unpublished_collaborative_leaves_listing(page, base_url, graphql_client, published_collaborative):
    c = published_collaborative
    unpublish_kind(graphql_client, "Collaborative", c["id"])
    assert page.listing_shows(base_url, "collaboratives", c["title"], present=False)
