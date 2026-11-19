# tests/consumer/functional/test_con_func_301_published_dataset.py
#
# A dataset published through the API shows, to an anonymous visitor, exactly
# the values its provider set; /datasets lists and filters it; unpublishing
# takes it down. The last test unpublishes, so it must stay last in the file.

import datetime

import pytest

from pages.consumer.published_item_page import PublishedItemPage
from tests.api.publications import gql

pytestmark = [pytest.mark.functional]

@pytest.fixture
def page(driver):
    return PublishedItemPage(driver)


def _detail(page, base_url, ds):
    return page.open_detail(base_url, "dataset", ds["id"], ds["title"])


def test_detail_shows_provider_values(page, base_url, published_dataset):
    ds = published_dataset
    text = _detail(page, base_url, ds).text()
    for value in (ds["title"], ds["description"], "CC BY-SA 4.0",
                  datetime.date.today().strftime("%d %b %Y")):
        assert value in text, f"{value!r} missing from dataset detail"
    assert "https://creativecommons.org/licenses/by-sa/4.0/" in page.external_links()


def test_detail_shows_sector_and_geography(page, base_url, published_dataset):
    ds = published_dataset
    text = _detail(page, base_url, ds).text()
    for value in (ds["sector"]["name"], ds["geography"]["name"]):
        assert value in text, f"{value!r} missing from dataset detail"


def test_metadata_tab_shows_tag_and_access(page, base_url, published_dataset):
    ds = published_dataset
    _detail(page, base_url, ds).open_tab("Metadata")
    for value in (ds["tag"], "Open Access", "CC BY-SA 4.0"):
        assert page.shows(value), f"{value!r} missing from dataset Metadata tab"


def test_listing_search_finds_dataset(page, base_url, published_dataset):
    assert page.listing_shows(base_url, "datasets", published_dataset["title"], query=published_dataset["tag"])


def test_listing_sector_filter_includes_then_excludes(page, base_url, published_dataset):
    ds = published_dataset
    assert page.listing_shows(base_url, "datasets", ds["title"], sectors=ds["sector"]["name"], query=ds["tag"])
    assert page.listing_shows(base_url, "datasets", ds["title"], present=False,
                              sectors=ds["other_sector"]["name"], query=ds["tag"])


def test_unpublished_dataset_detail_is_gone(page, base_url, graphql_client, published_dataset):
    ds = published_dataset
    gql(graphql_client, "mutation($id: UUID!){ unPublishDataset(datasetId:$id){ ... on TypeDataset { id } } }", {"id": ds["id"]})
    _detail(page, base_url, ds)
    assert page.is_not_found() and ds["description"] not in page.text(), "unpublished dataset still served"
    assert page.listing_shows(base_url, "datasets", ds["title"], present=False, query=ds["tag"])
