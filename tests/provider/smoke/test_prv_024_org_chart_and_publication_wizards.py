# tests/provider/smoke/test_prv_024_org_chart_and_publication_wizards.py
#
# One happy path through each of the two wizards that had no browser coverage
# (DataSpaceFrontend#504 chart wizard, #470 publication wizard), as the org's
# admin. What a run creates is deleted through the API by the `cleanup`
# fixture, published or not, and a delete that fails fails the run.

import uuid

import pytest

from pages.provider.chart_wizard_page import ChartWizardPage
from pages.provider.create_publication_page import CreatePublicationPage
from pages.provider.listing_table_page import ListingTablePage

YOUTUBE_URL = "https://www.youtube.com/watch?v=dQw4w9WgXcQ"


def _published_dataset_with_a_file(provider_api, org_name):
    """Title of one of the org's published data datasets that has a file to chart, or None."""
    body = provider_api.gql(
        '{ datasetsTable(limit: 100, filters: [{field: "status", condition: "exact", value: "PUBLISHED"}]) '
        "{ data { title datasetType resourceCount } } }",
        None, provider_api.org_slug(org_name),
    )
    rows = body["data"]["datasetsTable"]["data"]
    return next((r["title"] for r in rows if r["resourceCount"] > 0 and r["datasetType"] == "DATA"), None)


@pytest.mark.functional
@pytest.mark.smoke
def test_prv_024_org_chart_wizard_publishes_a_bar_chart(driver, open_listing, provider_api, cleanup, writable_org):
    """
    Test Case ID: test_prv_024_org_chart_wizard_publishes_a_bar_chart
    An org admin builds a bar chart from one of the org's datasets and publishes it.
    Steps:
      1. Pick one of the org's published datasets that has a file (skip if none)
      2. Charts -> Add Chart: choose the dataset, its first file, Bar, an X-axis
         field and a value field
      3. Continue to Review & Publish, name the chart and publish it
      4. The Charts listing shows the chart as Published
    """
    dataset = _published_dataset_with_a_file(provider_api, writable_org)
    if not dataset:
        pytest.skip(f"{writable_org} has no published dataset with a file to chart")
    cleanup.watch("chart", writable_org)
    name = f"zz-auto-chart-{uuid.uuid4().hex[:8]}"

    open_listing("org", "Charts")
    wizard = ChartWizardPage(driver).start()
    wizard.pick_dataset(dataset)
    wizard.choose_first_resource()
    wizard.choose_chart_type("Bar")
    wizard.fill_next_field()   # X-axis
    wizard.fill_next_field()   # Values (Y-axis)
    wizard.continue_to_review()
    wizard.name_chart(name)
    wizard.publish()

    table = ListingTablePage(driver).open_section("Charts")
    table.search(name)
    rows = table.wait_for_rows(lambda r: [x["title"] for x in r] == [name], f"The chart {name!r} is not listed")
    assert rows[0]["status"] == "Published", f"The chart is listed as {rows[0]['status']!r}, not Published"


@pytest.mark.functional
@pytest.mark.smoke
def test_prv_025_org_publication_wizard_publishes(driver, open_listing, provider_api, cleanup, writable_org, sector_name):
    """
    Test Case ID: test_prv_025_org_publication_wizard_publishes
    An org admin creates a publication from a YouTube link and publishes it.
    Steps:
      1. Publications -> Create Publication
      2. Files: add a YouTube video
      3. Details: name, description, date, resource type, a contributor, a sector and a geography
      4. Review & Publish: publish
      5. The Publications listing shows the publication as Published
    """
    me = provider_api.gql("{ me { firstName } }")["data"]["me"]["firstName"]
    cleanup.watch("publication", writable_org)
    name = f"zz-auto-pub-{uuid.uuid4().hex[:8]}"

    open_listing("org", "Publications")
    wizard = CreatePublicationPage(driver).start()
    wizard.add_youtube_video(YOUTUBE_URL)
    wizard.click_continue("details")

    wizard.enter_resource_name(name)
    wizard.enter_description(f"Created by an automated test {name}")
    wizard.enter_date("2024-01-01")
    wizard.choose_resource_type()
    wizard.add_contributor(me)
    wizard.select_field_options("Sector / Domain", [sector_name])
    wizard.select_geography("India")
    wizard.click_continue("publish")
    wizard.click_publish(name)

    assert wizard.is_published(), f"The publication {name!r} is not listed as Published after publishing"
