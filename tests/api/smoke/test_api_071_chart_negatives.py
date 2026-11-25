# tests/api/smoke/test_api_071_chart_negatives.py
#
# Edge and negative cases for a dataset's built charts: another account and an
# anonymous caller can neither read a draft nor change, publish or delete it;
# unknown, malformed and out-of-enum inputs are refused with a readable error;
# publishing twice is harmless; a deleted chart cannot be deleted again. One
# throwaway draft dataset with one resource and one chart, deleted at teardown.

import uuid

import pytest

from tests.api.publications import gql
from tests.api.publish_ready import add_resource

pytestmark = [pytest.mark.api, pytest.mark.smoke]

EDIT = ("mutation($i: ResourceChartInput!){ editResourceChart(chartInput:$i){ ... on TypeResourceChart { id name } "
        "... on OperationInfo { messages { message } } } }")
READ = "query($c: UUID!){ resourceChart(chartDetailsId:$c){ id name status } }"
PUBLISH = "mutation($c: UUID!){ publishResourceChart(chartId:$c) }"
UNPUBLISH = "mutation($c: UUID!){ unpublishResourceChart(chartId:$c) }"
DELETE = "mutation($c: UUID!){ deleteResourceChart(chartId:$c) }"
DENIED = "permission to change this dataset's charts"


@pytest.fixture(scope="module")
def owner(graphql_client_for):
    return graphql_client_for(1)


@pytest.fixture(scope="module")
def parts(owner):
    dataset = gql(owner, "mutation{ addDataset(createInput:{datasetType: DATA}){ data { id } } }")["data"]["addDataset"]["data"]["id"]
    try:
        add_resource(owner, dataset)
        resource = gql(owner, "query($d: UUID!){ getDataset(datasetId:$d){ resources{ id } } }", {"d": dataset})["data"]["getDataset"]["resources"][0]["id"]
        chart = gql(owner, "mutation($r: UUID!){ addResourceChart(resource:$r){ ... on TypeResourceChart { id } } }", {"r": resource})["data"]["addResourceChart"]["id"]
        yield {"dataset": dataset, "resource": resource, "chart": chart}
    finally:
        gql(owner, "mutation($id: UUID!){ deleteDataset(datasetId:$id) }", {"id": dataset})


def _error(body):
    assert body.get("errors"), f"expected an error, got {str(body)[:200]}"
    return body["errors"][0]["message"]


@pytest.fixture(params=["outsider", "anonymous"])
def stranger(request, graphql_client_for, anon_graphql_client):
    return graphql_client_for(4) if request.param == "outsider" else anon_graphql_client


def test_a_stranger_cannot_read_a_draft_chart(stranger, parts):
    body = gql(stranger, READ, {"c": parts["chart"]})
    assert not (body.get("data") or {}).get("resourceChart"), f"a draft chart was readable: {str(body)[:200]}"
    assert "does not exist" in _error(body), "the refusal should not reveal that the chart exists"


@pytest.mark.parametrize("what", ["edit", "publish", "unpublish", "delete"])
def test_a_stranger_cannot_change_a_chart(stranger, owner, parts, what):
    query, variables = {
        "edit": (EDIT, {"i": {"chartId": parts["chart"], "resource": parts["resource"], "name": "hijacked"}}),
        "publish": (PUBLISH, {"c": parts["chart"]}), "unpublish": (UNPUBLISH, {"c": parts["chart"]}), "delete": (DELETE, {"c": parts["chart"]}),
    }[what]
    assert DENIED in _error(gql(stranger, query, variables))
    kept = gql(owner, READ, {"c": parts["chart"]})["data"]["resourceChart"]
    assert kept["name"] != "hijacked" and kept["status"] == "DRAFT", f"the chart changed anyway: {kept}"


@pytest.mark.parametrize("variables, expected", [
    ({"c": "not-a-uuid"}, "cannot represent a UUID"),
    ({"c": str(uuid.uuid4())}, "does not exist"),
], ids=["malformed-id", "unknown-id"])
def test_unknown_or_malformed_chart_ids_are_a_readable_error(owner, variables, expected):
    assert expected in _error(gql(owner, READ, variables))


def test_a_chart_type_outside_the_enum_is_refused(owner, parts):
    message = _error(gql(owner, EDIT, {"i": {"chartId": parts["chart"], "resource": parts["resource"], "type": "PIE"}}))
    assert "does not exist in 'ChartTypes'" in message


def test_a_chart_name_of_the_maximum_length_is_saved(owner, parts):
    name = "n" * 50
    body = gql(owner, EDIT, {"i": {"chartId": parts["chart"], "resource": parts["resource"], "name": name}})
    assert not body.get("errors"), body["errors"]
    assert gql(owner, READ, {"c": parts["chart"]})["data"]["resourceChart"]["name"] == name


def test_publishing_twice_is_harmless_and_unpublishing_returns_to_draft(owner, parts):
    for _ in range(2):
        assert gql(owner, PUBLISH, {"c": parts["chart"]})["data"]["publishResourceChart"] is True
    assert gql(owner, READ, {"c": parts["chart"]})["data"]["resourceChart"]["status"] == "PUBLISHED"
    assert gql(owner, UNPUBLISH, {"c": parts["chart"]})["data"]["unpublishResourceChart"] is True
    assert gql(owner, READ, {"c": parts["chart"]})["data"]["resourceChart"]["status"] == "DRAFT"


def test_a_deleted_chart_cannot_be_deleted_again(owner, parts):
    resource = parts["resource"]
    chart = gql(owner, "mutation($r: UUID!){ addResourceChart(resource:$r){ ... on TypeResourceChart { id } } }", {"r": resource})["data"]["addResourceChart"]["id"]
    assert gql(owner, DELETE, {"c": chart})["data"]["deleteResourceChart"] is True
    assert DENIED in _error(gql(owner, DELETE, {"c": chart}))
    assert "does not exist" in _error(gql(owner, READ, {"c": chart}))


def test_a_chart_name_over_the_limit_is_a_validation_error_not_a_database_error(owner, parts):
    """Hard fail until DataSpaceBackend#325 is fixed: the raw 'varying(50)' database error is returned."""
    body = gql(owner, EDIT, {"i": {"chartId": parts["chart"], "resource": parts["resource"], "name": "n" * 51}})
    assert "varying" not in str(body.get("errors")), f"the database error reaches the client (DataSpaceBackend#325): {body['errors'][0]['message'][:80]}"


def test_a_whitespace_only_chart_name_is_refused(owner, parts):
    """Hard fail until DataSpaceBackend#325 is fixed: a blank name is saved."""
    body = gql(owner, EDIT, {"i": {"chartId": parts["chart"], "resource": parts["resource"], "name": "   "}})
    assert body.get("errors"), "a whitespace-only chart name was saved (DataSpaceBackend#325)"
