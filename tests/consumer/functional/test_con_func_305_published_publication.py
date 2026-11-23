# tests/consumer/functional/test_con_func_305_published_publication.py
#
# A publication published through the API shows, to an anonymous visitor, exactly
# the values its provider set; unpublishing takes it down. The last test
# unpublishes, so it must stay last in the file.

import pytest

from pages.consumer.published_item_page import PublishedItemPage
from tests.api import publications as pub

pytestmark = [pytest.mark.functional]


@pytest.fixture
def page(driver):
    return PublishedItemPage(driver)


def _detail(page, base_url, p):
    return page.open_detail(base_url, "publication", p["slug"], p["title"])


def test_detail_shows_provider_values(page, base_url, published_publication):
    p = published_publication
    text = _detail(page, base_url, p).text()
    for value in (p["title"], p["resource_type"]["name"], p["sector"]["name"], p["geography"]["name"],
                  "CC BY 4.0 (Attribution)", *p["authors"]):
        assert value in text, f"{value!r} missing from the publication detail"
    assert p["externalSourceLink"] in page.external_links(), "The source link is not offered"


def test_detail_lists_its_files_and_offers_a_citation(page, base_url, published_publication):
    p = published_publication
    text = _detail(page, base_url, p).text()
    assert "1 file" in text and "1 video" in text, f"The files summary is missing: {text[:600]}"
    assert "Cite this" in text and "Copy citation" in text, "The citation block is missing"
    assert p["title"] in text.split("Cite this", 1)[1], "The citation does not name the publication"


def test_unpublished_publication_content_is_no_longer_served(page, base_url, graphql_client, published_publication):
    p = published_publication
    assert page.open_detail(base_url, "publication", p["slug"], p["title"]).shows(p["title"]), "The publication was not served before it was unpublished"
    pub.unpublish(graphql_client, p["id"])
    text = page.open_detail(base_url, "publication", p["slug"], "\u0000never").text()
    assert p["title"] not in text and p["description"] not in text, "unpublished publication still served"
