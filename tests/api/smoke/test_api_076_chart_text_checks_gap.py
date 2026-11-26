# tests/api/smoke/test_api_076_chart_text_checks_gap.py
#
# DataSpaceBackend#329 (fixes #325): chart and chart-image names/descriptions
# are refused when blank or too long, with a fixed message, instead of
# Postgres' own "value too long for type character varying(50)" text.
#
# test_api_071_chart_negatives.py already covers editResourceChart's name
# checks (over-the-limit and whitespace-only) as hard assertions, added
# 2026-11-24 while #325 was still open -- they fail red against any backend
# that doesn't have #329 yet, and need no change here. This file covers what
# that one doesn't: createResourceChart's own checks, the chart description
# limit, and resource chart images (createResourceChartImage /
# updateResourceChartImage), which had no coverage at all before #329.
#
# One throwaway draft dataset with one resource, deleted at teardown.
#
# Needs an authenticated account (graphql_client_for) and writes to dev, so
# it could not be run in this environment -- no test credentials here. See
# the PR body.

import pytest

from tests.api.publications import gql
from tests.api.publish_ready import add_resource

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.deployed_pr("DataSpaceBackend#329")]

CHART = "... on TypeResourceChart { id name description } ... on OperationInfo { messages { message } }"
IMAGE = "... on TypeResourceChartImage { id name } ... on OperationInfo { messages { message } }"

CREATE_CHART = f"mutation($i: ResourceChartInput!){{ createResourceChart(chartInput:$i){{ {CHART} }} }}"
EDIT_CHART = f"mutation($i: ResourceChartInput!){{ editResourceChart(chartInput:$i){{ {CHART} }} }}"
CREATE_IMAGE = f"mutation($i: ResourceChartImageInput!){{ createResourceChartImage(input:$i){{ {IMAGE} }} }}"
UPDATE_IMAGE = f"mutation($i: ResourceChartImageInputPartial!){{ updateResourceChartImage(input:$i){{ {IMAGE} }} }}"
READ_CHART = "query($c: UUID!){ resourceChart(chartDetailsId:$c){ id name description } }"
READ_IMAGE = "query($i: UUID!){ resourceChartImage(imageId:$i){ id name } }"


@pytest.fixture(scope="module")
def owner(graphql_client_for):
    return graphql_client_for(1)


@pytest.fixture(scope="module")
def parts(owner):
    """A throwaway draft dataset with one resource and one chart."""
    dataset = gql(owner, "mutation{ addDataset(createInput:{datasetType: DATA}){ data { id } } }")["data"]["addDataset"]["data"]["id"]
    try:
        add_resource(owner, dataset)
        resource = gql(owner, "query($d: UUID!){ getDataset(datasetId:$d){ resources{ id } } }", {"d": dataset})["data"]["getDataset"]["resources"][0]["id"]
        chart = gql(owner, "mutation($r: UUID!){ addResourceChart(resource:$r){ ... on TypeResourceChart { id } } }", {"r": resource})["data"]["addResourceChart"]["id"]
        image = gql(owner, "mutation($d: UUID!){ addResourceChartImage(dataset:$d){ ... on TypeResourceChartImage { id } } }", {"d": dataset})["data"]["addResourceChartImage"]["id"]
        yield {"dataset": dataset, "resource": resource, "chart": chart, "image": image}
    finally:
        gql(owner, "mutation($id: UUID!){ deleteDataset(datasetId:$id) }", {"id": dataset})


def _error(body):
    assert body.get("errors"), f"expected an error, got {str(body)[:200]}"
    return body["errors"][0]["message"]


# ─── createResourceChart ────────────────────────────────────────────────────


def test_create_resource_chart_refuses_a_name_over_50_characters(owner, parts):
    """Same check as editResourceChart (#325), but on the create path, which
    test_api_071 doesn't exercise: createResourceChart builds the row itself
    rather than going through _update_chart_fields.
    """
    before = gql(owner, "query($d: UUID!){ chartsDetails(datasetId:$d){ id } }", {"d": parts["dataset"]})["data"]["chartsDetails"]
    message = _error(gql(owner, CREATE_CHART, {"i": {"resource": parts["resource"], "name": "n" * 51}}))
    assert message == "Chart name cannot be longer than 50 characters.", message
    after = gql(owner, "query($d: UUID!){ chartsDetails(datasetId:$d){ id } }", {"d": parts["dataset"]})["data"]["chartsDetails"]
    assert len(after) == len(before), "a refused create still created a chart"


def test_create_resource_chart_with_a_blank_name_gets_the_default_name(owner, parts):
    """Unchanged behaviour (PR body): a blank name on create is not refused,
    it gets the timestamped default -- only edit refuses a blank name.
    """
    body = gql(owner, CREATE_CHART, {"i": {"resource": parts["resource"], "name": "   "}})
    assert not body.get("errors"), body["errors"]
    created = body["data"]["createResourceChart"]
    assert created["name"].startswith("New chart "), created
    gql(owner, "mutation($c: UUID!){ deleteResourceChart(chartId:$c) }", {"c": created["id"]})


# ─── editResourceChart: description (not covered by test_api_071) ──────────


def test_edit_refuses_a_description_over_1000_characters(owner, parts):
    message = _error(gql(owner, EDIT_CHART, {"i": {"chartId": parts["chart"], "resource": parts["resource"], "description": "d" * 1001}}))
    assert message == "Chart description cannot be longer than 1000 characters.", message
    kept = gql(owner, READ_CHART, {"c": parts["chart"]})["data"]["resourceChart"]
    assert len(kept["description"] or "") <= 1000, kept


def test_edit_trims_the_name(owner, parts):
    body = gql(owner, EDIT_CHART, {"i": {"chartId": parts["chart"], "resource": parts["resource"], "name": "  Trimmed  "}})
    assert not body.get("errors"), body["errors"]
    assert gql(owner, READ_CHART, {"c": parts["chart"]})["data"]["resourceChart"]["name"] == "Trimmed"


# ─── createResourceChartImage / updateResourceChartImage: no coverage before #329 ──


def test_create_resource_chart_image_refuses_a_name_over_50_characters(owner, parts):
    message = _error(gql(owner, CREATE_IMAGE, {"i": {"dataset": parts["dataset"], "name": "n" * 51}}))
    assert message == "Chart name cannot be longer than 50 characters.", message


def test_create_resource_chart_image_with_a_blank_name_gets_the_default_name(owner, parts):
    body = gql(owner, CREATE_IMAGE, {"i": {"dataset": parts["dataset"], "name": "   "}})
    assert not body.get("errors"), body["errors"]
    created = body["data"]["createResourceChartImage"]
    assert created["name"].startswith("New resource_chart_image "), created
    gql(owner, "mutation($i: UUID!){ deleteResourceChartImage(resourceChartImageId:$i) }", {"i": created["id"]})


def test_update_resource_chart_image_refuses_a_name_over_50_characters(owner, parts):
    message = _error(gql(owner, UPDATE_IMAGE, {"i": {"id": parts["image"], "dataset": parts["dataset"], "name": "n" * 51}}))
    assert message == "Chart name cannot be longer than 50 characters.", message


@pytest.mark.parametrize("name", ["   ", ""])
def test_update_resource_chart_image_refuses_a_blank_name(owner, parts, name):
    """Images get the same blank-over-saved rule as charts (#325): the saved
    name here is addResourceChartImage's own default, which is non-blank, so
    sending a blank one must be refused rather than silently kept or saved.
    """
    message = _error(gql(owner, UPDATE_IMAGE, {"i": {"id": parts["image"], "dataset": parts["dataset"], "name": name}}))
    assert message == "Chart name cannot be blank.", message


def test_update_resource_chart_image_trims_the_name(owner, parts):
    body = gql(owner, UPDATE_IMAGE, {"i": {"id": parts["image"], "dataset": parts["dataset"], "name": "  Trimmed image  "}})
    assert not body.get("errors"), body["errors"]
    assert gql(owner, READ_IMAGE, {"i": parts["image"]})["data"]["resourceChartImage"]["name"] == "Trimmed image"
