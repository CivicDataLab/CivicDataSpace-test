# tests/consumer/functional/conftest.py
#
# API-side setup for the consumer published-values tests: each fixture creates
# an entity with distinctive values through GraphQL, publishes it, and
# unpublishes + deletes it on teardown. The browser then only reads.

import uuid

import pytest

from tests.api.conftest import (  # noqa: F401  (re-exported fixtures)
    anon_graphql_client, api_base_url, auth_token, graphql_client, keycloak_config,
)
from tests.api.publications import gql

TITLE_TAIL = "जल डेटा 🌊"


def _ok(body, name=None):
    assert "errors" not in body, body["errors"]
    data = body["data"][name] if name else body["data"]
    assert not (isinstance(data, dict) and data.get("messages")), data
    return data


@pytest.fixture(scope="module")
def taxonomy(graphql_client):
    """Two distinct sectors, one SDG and one geography, read live."""
    data = _ok(gql(graphql_client, "{ sectors { id name } allSdgs { id name code } geographies { id name } }"))
    sectors = sorted(data["sectors"], key=lambda s: s["name"])
    assert len(sectors) >= 2, "need two sectors for the exclude-filter case"
    return {
        "sector": sectors[0], "other_sector": sectors[1],
        "sdg": data["allSdgs"][0],
        "geography": sorted(data["geographies"], key=lambda g: g["name"])[0],
    }


def _title(kind):
    return f"[qa-matrix] {kind} {uuid.uuid4().hex[:6]} {TITLE_TAIL}"


@pytest.fixture(scope="module")
def published_dataset(graphql_client, taxonomy):
    ds_id = _ok(gql(graphql_client, "mutation{ addDataset(createInput:{datasetType: DATA}){ data { id } } }"),
                "addDataset")["data"]["id"]
    tag = f"qamatrix{uuid.uuid4().hex[:5]}"
    values = {"id": ds_id, "title": _title("dataset"), "license": "CC_BY_SA_4_0_ATTRIBUTION_SHARE_ALIKE",
              "tag": tag, "description": f"qa-matrix consumer values check {TITLE_TAIL}", **taxonomy}
    try:
        gql(graphql_client, "mutation($i: UpdateDatasetInput!){ updateDataset(updateDatasetInput:$i){ ... on TypeDataset { id } } }",
            {"i": {"dataset": ds_id, "title": values["title"], "description": values["description"],
                   "license": values["license"], "accessType": "PUBLIC", "tags": [tag]}})
        _ok(gql(graphql_client, "mutation($i: UpdateMetadataInput!){ addUpdateDatasetMetadata(updateMetadataInput:$i){ "
                "success data { id } } }",
            {"i": {"dataset": ds_id, "metadata": [], "description": values["description"], "tags": [tag],
                   "sectors": [taxonomy["sector"]["id"]], "geographies": [int(taxonomy["geography"]["id"])],
                   "license": values["license"], "accessType": "PUBLIC"}}), "addUpdateDatasetMetadata")
        _ok(gql(graphql_client, "mutation($id: UUID!){ publishDataset(datasetId:$id){ ... on TypeDataset { status } } }",
                {"id": ds_id}), "publishDataset")
        yield values
    finally:
        gql(graphql_client, "mutation($id: UUID!){ unPublishDataset(datasetId:$id){ ... on TypeDataset { id } } }", {"id": ds_id})
        gql(graphql_client, "mutation($id: UUID!){ deleteDataset(datasetId:$id) }", {"id": ds_id})


def _publish_kind(client, kind, arg, item_id):
    return _ok(gql(client, "mutation($i: String!){ publish%s(%s:$i){ ... on Type%s { status } ... on OperationInfo { messages { message } } } }"
                   % (kind, arg, kind), {"i": item_id}), f"publish{kind}")


def unpublish_kind(client, kind, item_id):
    arg = "useCaseId" if kind == "UseCase" else "collaborativeId"
    return gql(client, "mutation($i: String!){ unpublish%s(%s:$i){ ... on Type%s { status } } }" % (kind, arg, kind), {"i": item_id})


def _usecase_like(client, taxonomy, kind, metadata_mutation, metadata_input):
    """Create, fill and publish a UseCase or Collaborative; yields its values."""
    lower = "useCase" if kind == "UseCase" else "collaborative"
    arg = f"{lower}Id"
    item_id = _ok(gql(client, "mutation{ add%s { ... on Type%s { id } } }" % (kind, kind)), f"add{kind}")["id"]
    tag = f"qamatrix{uuid.uuid4().hex[:5]}"
    values = {"id": item_id, "title": _title(lower), "tag": tag,
              "summary": f"qa-matrix summary {TITLE_TAIL}", "platform_url": "https://example.org/qa-matrix",
              "started_on": "2024-01-15", "completed_on": "2025-06-30", **taxonomy}
    fields = {"id": item_id, "title": values["title"], "summary": values["summary"],
              "platformUrl": values["platform_url"], "startedOn": values["started_on"],
              "completedOn": values["completed_on"]}
    if kind == "UseCase":
        fields["runningStatus"] = "COMPLETED"
    try:
        _ok(gql(client, "mutation($d: %sInputPartial!){ update%s(data:$d){ id urlSlug } }" % (kind, kind), {"d": fields}))
        _ok(gql(client, "mutation($i: %s!){ %s(updateMetadataInput:$i){ ... on Type%s { id } ... on OperationInfo { messages { message } } } }"
                % (metadata_input, metadata_mutation, kind),
                {"i": {"id": item_id, "metadata": [], "tags": [tag], "sectors": [taxonomy["sector"]["id"]],
                       "sdgs": [taxonomy["sdg"]["id"]], "geographies": [int(taxonomy["geography"]["id"])]}}),
            metadata_mutation)
        _publish_kind(client, kind, arg, item_id)
        values["slug"] = _ok(gql(client, "query($p: ID!){ %s(pk:$p){ urlSlug } }" % lower, {"p": item_id}), lower)["urlSlug"]
        yield values
    finally:
        unpublish_kind(client, kind, item_id)
        gql(client, "mutation($i: String!){ delete%s(%s:$i) }" % (kind, arg), {"i": item_id})


@pytest.fixture(scope="module")
def published_usecase(graphql_client, taxonomy):
    yield from _usecase_like(graphql_client, taxonomy, "UseCase", "addUpdateUsecaseMetadata", "UpdateUseCaseMetadataInput")


@pytest.fixture(scope="module")
def published_collaborative(graphql_client, taxonomy):
    yield from _usecase_like(graphql_client, taxonomy, "Collaborative", "addUpdateCollaborativeMetadata",
                             "UpdateCollaborativeMetadataInput")


@pytest.fixture(scope="module")
def public_ai_model(graphql_client, taxonomy):
    tag = f"qamatrix{uuid.uuid4().hex[:5]}"
    values = {"name": f"qa-matrix-{uuid.uuid4().hex[:8]}", "title": _title("model"), "tag": tag,
              "description": f"qa-matrix model description {TITLE_TAIL}",
              "model_type": "SUMMARIZATION", "domain": "AGRICULTURE", **taxonomy}
    body = gql(graphql_client, "mutation($i: CreateAIModelInput!){ createAiModel(input:$i){ success errors { nonFieldErrors } data { id } } }",
               {"i": {"modelType": values["model_type"], "provider": "CUSTOM", "name": values["name"],
                      "displayName": values["title"], "description": values["description"], "domain": values["domain"],
                      "tags": [tag], "sectors": [taxonomy["sector"]["id"]],
                      "geographies": [int(taxonomy["geography"]["id"])], "isPublic": True}})
    created = _ok(body, "createAiModel")
    assert created["success"], created
    values["id"] = int(created["data"]["id"])
    try:
        yield values
    finally:
        gql(graphql_client, "mutation($id: Int!){ deleteAiModel(modelId:$id){ success } }", {"id": values["id"]})
