# tests/provider/functional/test_prv_func_212_individual_publication.py
#
# An individual account (no organization) creates a publication through the
# wizard and publishes it, the same flow 025 covers for an org admin. The
# published publication is then served to an anonymous visitor, and
# unpublishing it from the listing returns it to Draft. The draft is deleted at
# teardown whatever happened.

import uuid

import pytest
import requests

from pages.consumer.published_item_page import PublishedItemPage
from pages.provider.create_publication_page import CreatePublicationPage
from pages.provider.listing_table_page import ListingTablePage

pytestmark = pytest.mark.functional

YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


@pytest.mark.timeout(600)
def test_prv_func_212_individual_publishes_a_publication_and_it_is_public(
    driver, base_url, open_listing, provider_api, cleanup, sector_name
):
    me = provider_api.gql("{ me { firstName } }")["data"]["me"]["firstName"]
    cleanup.watch("publication")
    name = f"zz-auto-ind-pub-{uuid.uuid4().hex[:8]}"
    description = f"Created by an automated test {name}"

    open_listing("individual", "Publications")
    wizard = CreatePublicationPage(driver).start()
    wizard.add_youtube_video(YOUTUBE_URL)
    wizard.click_continue("details")
    wizard.enter_resource_name(name)
    wizard.enter_description(description)
    wizard.enter_date("2024-01-01")
    wizard.choose_resource_type()
    wizard.add_contributor(me)
    wizard.select_field_options("Sector / Domain", [sector_name])
    wizard.select_geography("India")
    wizard.click_continue("publish")
    wizard.click_publish(name)
    assert wizard.is_published(), f"The publication {name!r} is not listed as Published after publishing"

    dashboard = driver.current_url
    api_base = provider_api.client.endpoint.replace("/api/graphql", "")
    found = wizard.wait_with_timeout(60).until(
        lambda d: [p for p in requests.get(f"{api_base}/api/search/publication/", params={"size": 100, "search": name}, timeout=30).json()["results"]
                   if p["title"] == name] or False)
    page = PublishedItemPage(driver).open_detail(base_url, "publication", found[0]["id"], name)
    assert description in page.text(), f"The public page does not show the description: {page.text()[:300]}"

    driver.get(dashboard)
    table = ListingTablePage(driver).open_section("Publications")
    table.search(name)
    table.wait_for_rows(lambda r: [x["title"] for x in r] == [name], f"{name!r} is not listed")
    table.row_action(name, "Unpublish")
    table.answer_dialog("Unpublish")
    table.wait_for_rows(lambda r: [(x["title"], x["status"]) for x in r] == [(name, "Draft")], "The publication did not return to Draft")
