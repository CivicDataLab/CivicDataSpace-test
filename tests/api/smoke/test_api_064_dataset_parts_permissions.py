# tests/api/smoke/test_api_064_dataset_parts_permissions.py
#
# DataSpaceBackend#267 (DataSpace#324 charts, #325 chart images, #326 access
# models, #327 prompt file details): a draft dataset's files, charts, chart
# images and access models are visible only to people who can see the draft,
# and only people who can edit the dataset can change them.
#
# The owner (account 4) builds a draft with one file, chart, chart image and
# access model. An outsider (account 3, in none of 4's orgs) and an anonymous
# caller must read none of them and change none of them. The owner reading all
# of them is the control that makes the "sees nothing" checks mean something.
#
# Replaces the discovery in test_api_050, which can only find a leaking draft
# while the bug exists, so it skips now that the fix is live.

import json
import os
import uuid

import pytest
import requests

from tests.api.client import GraphQLClient, _request_with_retries
from utils.provider_api import ProviderAPI

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.deployed_pr("DataSpaceBackend#267")]

OWNER, OUTSIDER = 4, 3  # account 3 is in none of account 4's orgs (see test_api_056)
UPLOAD = "mutation($i: CreateFileResourceInput!){ createFileResources(fileResourceInput:$i){ id } }"
ACCESS_MODEL = """mutation($i: AccessModelInput!){ createAccessModel(accessModelInput:$i){
  __typename ... on TypeAccessModel { id } ... on OperationInfo { messages { message } } } }"""

READS = {
    "datasetResources": ("query($d: UUID!){ datasetResources(datasetId:$d){ id } }", "d", "dataset"),
    "resourceById": ("query($r: UUID!){ resourceById(resourceId:$r){ id promptDetails { promptCount } } }", "r", "resource"),
    "chartsDetails": ("query($d: UUID!){ chartsDetails(datasetId:$d){ id } }", "d", "dataset"),
    "resourceChart": ("query($c: UUID!){ resourceChart(chartDetailsId:$c){ id status } }", "c", "chart"),
    "datasetResourceCharts": ("query($d: UUID!){ datasetResourceCharts(datasetId:$d){ ... on TypeResourceChartImage { id } } }", "d", "dataset"),
    "resourceChartImage": ("query($i: UUID!){ resourceChartImage(imageId:$i){ id status } }", "i", "image"),
    "resourceChartImages": ("query($i: UUID!){ resourceChartImages(filters:{id:$i}){ id } }", "i", "image"),
    "accessModelResources": ("query($d: UUID!){ accessModelResources(datasetId:$d){ id } }", "d", "dataset"),
    "accessModel": ("query($a: UUID!){ accessModel(accessModelId:$a){ id name type } }", "a", "access_model"),
}
# What each read must return to the owner: the id of the part it is about.
EXPECTED = {"datasetResources": "resource", "resourceById": "resource", "chartsDetails": "chart", "resourceChart": "chart",
            "datasetResourceCharts": "image", "resourceChartImage": "image", "resourceChartImages": "image",
            "accessModelResources": "access_model", "accessModel": "access_model"}

# name -> (mutation, variables from ids, query the owner reruns to see the part is untouched)
WRITES = {
    "addResourceChart": ("mutation($r: UUID!){ addResourceChart(resource:$r){ __typename } }",
                         lambda p: {"r": p["resource"]}, "chartsDetails"),
    "publishResourceChart": ("mutation($c: UUID!){ publishResourceChart(chartId:$c) }",
                             lambda p: {"c": p["chart"]}, "resourceChart"),
    "deleteResourceChart": ("mutation($c: UUID!){ deleteResourceChart(chartId:$c) }",
                            lambda p: {"c": p["chart"]}, "resourceChart"),
    "addResourceChartImage": ("mutation($d: UUID!){ addResourceChartImage(dataset:$d){ __typename } }",
                              lambda p: {"d": p["dataset"]}, "datasetResourceCharts"),
    "unpublishResourceChartImage": ("mutation($i: UUID!){ unpublishResourceChartImage(resourceChartImageId:$i) }",
                                    lambda p: {"i": p["image"]}, "resourceChartImage"),
    "deleteResourceChartImage": ("mutation($i: UUID!){ deleteResourceChartImage(resourceChartImageId:$i) }",
                                 lambda p: {"i": p["image"]}, "resourceChartImage"),
    "createAccessModel": (ACCESS_MODEL, lambda p: {"i": {"dataset": p["dataset"], "name": "[qa] outsider", "description": "qa",
                                                         "type": "PUBLIC", "resources": []}}, "accessModelResources"),
    "editAccessModel": ("mutation($i: EditAccessModelInput!){ editAccessModel(accessModelInput:$i){ __typename } }",
                        lambda p: {"i": {"accessModelId": p["access_model"], "dataset": p["dataset"], "name": "[qa] hijacked",
                                         "description": "qa", "type": "PUBLIC", "resources": []}}, "accessModel"),
    "deleteAccessModel": ("mutation($a: UUID!){ deleteAccessModel(accessModelId:$a) }",
                          lambda p: {"a": p["access_model"]}, "accessModel"),
    "updatePromptResource": ("mutation($i: UpdatePromptResourceInput!){ updatePromptResource(updateInput:$i){ success } }",
                             lambda p: {"i": {"resource": p["resource"], "promptCount": 7}}, "resourceById"),
}


def _account(n):
    email, password = os.getenv(f"TEST_EMAIL_{n}"), os.getenv(f"TEST_PASSWORD_{n}")
    if not (email and password):
        pytest.skip(f"TEST_EMAIL_{n}/TEST_PASSWORD_{n} not set")
    return ProviderAPI(email, password)


def _data(body, name):
    assert "errors" not in body, body["errors"]
    return body["data"][name]


def _new_dataset(owner):
    return _data(owner.gql("mutation{ addDataset(createInput:{datasetType: DATA}){ data { id } } }"), "addDataset")["data"]["id"]


def _upload(owner, dataset_id, filename):
    operations = {"query": UPLOAD, "variables": {"i": {"dataset": dataset_id, "files": [None]}}}
    resp = _request_with_retries(
        requests.post, f"{os.environ['API_BASE_URL'].rstrip('/')}/api/graphql",
        headers={"Authorization": owner.client.session.headers["Authorization"]},
        data={"operations": json.dumps(operations), "map": json.dumps({"0": ["variables.i.files.0"]})},
        files={"0": (filename, b"state,year,value\nAssam,2024,1\nBihar,2024,2\n")},
    )
    assert resp.status_code == 200, resp.text[:300]
    return _data(resp.json(), "createFileResources")[0]["id"]


@pytest.fixture(scope="module")
def draft():
    owner = _account(OWNER)
    parts = {"dataset": _new_dataset(owner)}
    try:
        parts["resource"] = _upload(owner, parts["dataset"], f"qa-{uuid.uuid4().hex[:8]}.csv")
        parts["chart"] = _data(owner.gql("mutation($r: UUID!){ addResourceChart(resource:$r){ ... on TypeResourceChart { id } } }",
                                         {"r": parts["resource"]}), "addResourceChart")["id"]
        parts["image"] = _data(owner.gql("mutation($d: UUID!){ addResourceChartImage(dataset:$d){ ... on TypeResourceChartImage { id } } }",
                                         {"d": parts["dataset"]}), "addResourceChartImage")["id"]
        parts["access_model"] = _data(owner.gql(ACCESS_MODEL, {"i": {
            "dataset": parts["dataset"], "name": "[qa] owner", "description": "qa", "type": "PRIVATE",
            "resources": [{"resource": parts["resource"], "fields": []}]}}), "createAccessModel")["id"]
        yield owner, parts
    finally:
        owner.gql("mutation($id: UUID!){ deleteDataset(datasetId:$id) }", {"id": parts["dataset"]})


def _caller(who):
    return _account(OUTSIDER) if who == "outsider" else GraphQLClient(os.environ["API_BASE_URL"].rstrip("/"))


def _read(client, name, parts):
    query, var, part = READS[name]
    variables = {var: parts[part]}
    if isinstance(client, ProviderAPI):
        return client.gql(query, variables)
    return client.session.post(client.endpoint, json={"query": query, "variables": variables}, timeout=60).json()


def _write(client, name, parts):
    mutation, variables, _ = WRITES[name]
    if isinstance(client, ProviderAPI):
        return client.gql(mutation, variables(parts))
    return client.session.post(client.endpoint, json={"query": mutation, "variables": variables(parts)}, timeout=60).json()


@pytest.mark.parametrize("name", READS)
def test_owner_sees_the_draft_part(draft, name):
    owner, parts = draft
    body = _read(owner, name, parts)
    assert "errors" not in body, body["errors"]
    assert parts[EXPECTED[name]] in json.dumps(body["data"]), f"{name}: the owner cannot see their own draft's part: {body}"


@pytest.mark.parametrize("who", ["outsider", "anonymous"])
@pytest.mark.parametrize("name", READS)
def test_others_see_no_draft_part(draft, who, name):
    _, parts = draft
    body = _read(_caller(who), name, parts)
    assert parts[EXPECTED[name]] not in json.dumps(body.get("data")), f"{name} shows a draft dataset's part to {who}: {body}"


@pytest.mark.parametrize("who", ["outsider", "anonymous"])
@pytest.mark.parametrize("name", WRITES)
def test_others_cannot_change_draft_parts(draft, who, name):
    owner, parts = draft
    before = _read(owner, WRITES[name][2], parts)
    body = _write(_caller(who), name, parts)
    messages = " ".join(e["message"] for e in body.get("errors") or [])
    assert "permission" in messages, f"{name} by {who} was not refused: {body}"
    after = _read(owner, WRITES[name][2], parts)
    assert after == before, f"{name} by {who} was refused but still changed the draft: {before} -> {after}"


@pytest.mark.xfail(strict=True, reason="createAccessModel refuses another dataset's file ('Resource with ID ... does not exist') "
                                      "but still saves an empty access model on the dataset: the create is not atomic")
def test_access_model_cannot_take_another_datasets_file(draft):
    owner, parts = draft
    other = _new_dataset(owner)
    try:
        foreign = _upload(owner, other, "other.csv")
        body = owner.gql(ACCESS_MODEL, {"i": {"dataset": parts["dataset"], "name": "[qa] foreign file", "description": "qa",
                                              "type": "PRIVATE", "resources": [{"resource": foreign, "fields": []}]}})
        assert body.get("errors") or "messages" in json.dumps(body["data"]), f"An access model took another dataset's file: {body}"
        models = _data(_read(owner, "accessModelResources", parts), "accessModelResources")
        assert [m["id"] for m in models] == [parts["access_model"]], f"An extra access model was created: {models}"
    finally:
        owner.gql("mutation($id: UUID!){ deleteDataset(datasetId:$id) }", {"id": other})
