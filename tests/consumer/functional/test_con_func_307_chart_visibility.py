# tests/consumer/functional/test_con_func_307_chart_visibility.py
#
# A dataset's draft or unpublished chart must not be served to an anonymous caller.
# Own file so it gets a fresh dataset: the chart list is cached per dataset.
# Hard fail until the advisory GHSA-44hh-j78p-7387 is fixed.

import os

import pytest
import requests

from tests.api.publications import gql

pytestmark = [pytest.mark.functional]

ANON_CHARTS = "query($d: UUID!){ getChartData(datasetId:$d){ __typename ... on TypeResourceChartImage { id } ... on TypeResourceChart { id } } }"
PUBLISH = "mutation($i: UUID!){ publishResourceChartImage(resourceChartImageId:$i) }"
UNPUBLISH = "mutation($i: UUID!){ unpublishResourceChartImage(resourceChartImageId:$i) }"


def _anonymous_chart_ids(dataset_id):
    body = requests.post(f"{os.environ['API_BASE_URL'].rstrip('/')}/api/graphql",
                         json={"query": ANON_CHARTS, "variables": {"d": dataset_id}}, timeout=30).json()
    return {c["id"] for c in (body.get("data") or {}).get("getChartData") or [] if c.get("id")}


def test_con_func_307_draft_chart_is_not_served_to_anonymous_callers(published_dataset, image_chart):
    assert image_chart["id"] not in _anonymous_chart_ids(published_dataset["id"]), \
        "a draft chart is served to anonymous callers (GHSA-44hh-j78p-7387)"


def test_con_func_307_unpublished_chart_is_not_served_to_anonymous_callers(graphql_client, published_dataset, image_chart):
    gql(graphql_client, PUBLISH, {"i": image_chart["id"]})
    gql(graphql_client, UNPUBLISH, {"i": image_chart["id"]})
    assert image_chart["id"] not in _anonymous_chart_ids(published_dataset["id"]), \
        "an unpublished chart is still served to anonymous callers (GHSA-44hh-j78p-7387)"
