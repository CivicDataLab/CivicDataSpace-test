# tests/consumer/functional/test_con_func_306_published_chart.py
#
# The image-chart path end to end, seen by an anonymous visitor on the public
# dataset's Visualisations tab: a published chart is listed, renaming shows the
# new name (and drops the old), and a deleted chart is gone. One test, because
# each step depends on the last. Draft and unpublished charts are not asserted:
# the backend currently lists them publicly (held, see the PR body).

import time

import pytest

from pages.consumer.published_item_page import PublishedItemPage
from tests.api.publications import gql
from tests.consumer.functional.conftest import set_image_chart

pytestmark = [pytest.mark.functional]


def _chart_names(page, base_url, dataset):
    page.open_detail(base_url, "dataset", dataset["id"], dataset["title"]).open_tab("Visualisations")
    time.sleep(2)
    return page.text()


def _listed(page, base_url, dataset, name, present, attempts=4):
    for _ in range(attempts):
        if (name in _chart_names(page, base_url, dataset)) == present:
            return True
        time.sleep(5)
    return False


def test_image_chart_lifecycle_on_the_visualisations_tab(driver, base_url, graphql_client, published_dataset, image_chart):
    page = PublishedItemPage(driver)
    ds, chart = published_dataset, image_chart
    publish = "mutation($i: UUID!){ publishResourceChartImage(resourceChartImageId:$i) }"
    unpublish = "mutation($i: UUID!){ unpublishResourceChartImage(resourceChartImageId:$i) }"

    assert gql(graphql_client, publish, {"i": chart["id"]})["data"]["publishResourceChartImage"] is True
    assert _listed(page, base_url, ds, chart["name"], present=True), f"The published chart {chart['name']!r} is not on the Visualisations tab"

    renamed = chart["name"] + " renamed"
    gql(graphql_client, unpublish, {"i": chart["id"]})
    set_image_chart(graphql_client, ds["id"], chart["id"], renamed, "qa-matrix image chart")
    gql(graphql_client, publish, {"i": chart["id"]})
    assert _listed(page, base_url, ds, renamed, present=True), "The renamed chart is not shown"
    assert page.text().count(chart["name"]) == page.text().count(renamed), "The old name is still shown beside the new one"

    deleted = gql(graphql_client, "mutation($i: UUID!){ deleteResourceChartImage(resourceChartImageId:$i) }", {"i": chart["id"]})
    assert not deleted.get("errors") and deleted["data"]["deleteResourceChartImage"], deleted
    assert _listed(page, base_url, ds, renamed, present=False), "A deleted chart is still listed"
