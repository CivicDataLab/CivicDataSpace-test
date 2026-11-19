# tests/consumer/functional/test_con_func_302_published_usecase.py
#
# A use case published through the API shows its provider's values on the
# public detail page; /usecases lists it and its sector/tag/geography filters
# include or exclude it. The last test unpublishes, so it must stay last.

import datetime

import pytest

from pages.consumer.published_item_page import PublishedItemPage
from tests.consumer.functional.conftest import unpublish_kind

pytestmark = [pytest.mark.functional]


@pytest.fixture
def page(driver):
    return PublishedItemPage(driver)


def _detail(page, base_url, uc):
    return page.open_detail(base_url, "usecase", uc["slug"], uc["title"])


def test_detail_shows_provider_values(page, base_url, published_usecase):
    uc = published_usecase
    text = _detail(page, base_url, uc).text()
    for value in (uc["title"], uc["summary"], uc["tag"], uc["sector"]["name"], uc["geography"]["name"],
                  uc["sdg"]["name"], f"Published {datetime.date.today().strftime('%d %b %Y')}"):
        assert value in text, f"{value!r} missing from use case detail"


@pytest.mark.xfail(strict=True, reason="DataSpaceFrontend#527: Use case detail no longer renders platform URL, running status or start date "
                                       "(Metadata panel absent after the 2026-11 redesign)")
def test_detail_shows_platform_url_status_and_dates(page, base_url, published_usecase):
    uc = published_usecase
    _detail(page, base_url, uc)
    assert uc["platform_url"] in page.external_links()
    assert page.shows("COMPLETED", timeout=3) and page.shows("15 Jan 2024", timeout=3)


def test_listing_filters_by_tag_sector_and_geography(page, base_url, published_usecase):
    uc = published_usecase
    assert page.listing_shows(base_url, "usecases", uc["title"], tags=uc["tag"])
    assert page.listing_shows(base_url, "usecases", uc["title"], tags=uc["tag"], sectors=uc["sector"]["name"],
                              geographies=uc["geography"]["name"])


def test_listing_other_sector_excludes(page, base_url, published_usecase):
    uc = published_usecase
    assert page.listing_shows(base_url, "usecases", uc["title"], present=False,
                              tags=uc["tag"], sectors=uc["other_sector"]["name"])


def test_unpublished_usecase_leaves_detail_and_listing(page, base_url, graphql_client, published_usecase):
    uc = published_usecase
    unpublish_kind(graphql_client, "UseCase", uc["id"])
    _detail(page, base_url, uc)
    assert page.is_not_found() and uc["summary"] not in page.text(), "unpublished use case still served"
    assert page.listing_shows(base_url, "usecases", uc["title"], present=False, tags=uc["tag"])
