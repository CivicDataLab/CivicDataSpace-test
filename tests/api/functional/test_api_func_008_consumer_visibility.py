# tests/api/functional/test_api_func_008_consumer_visibility.py
#
# Provider writes, consumer reads: a draft is invisible to anonymous visitors,
# the same record becomes readable once published (with the values the provider
# set), and it disappears again when unpublished. Covers datasets, use cases,
# collaboratives and AI models. Search indexing is checked with a polled wait.

import time
import uuid

import pytest

from tests.api.publications import gql

pytestmark = [pytest.mark.api, pytest.mark.functional]


def _errors(body):
    return [e["message"] for e in body.get("errors") or []]


def _wait(predicate, timeout=60, step=5):
    end = time.time() + timeout
    while time.time() < end:
        if predicate():
            return True
        time.sleep(step)
    return predicate()


# ─── Dataset ──────────────────────────────────────────────────────────────────

@pytest.fixture
def dataset(graphql_client):
    body = gql(graphql_client, "mutation{ addDataset(createInput:{datasetType: DATA}){ data { id } } }")
    dataset_id = body["data"]["addDataset"]["data"]["id"]
    title = f"[qa-matrix] visibility {uuid.uuid4().hex[:8]}"
    gql(graphql_client, "mutation($i: UpdateDatasetInput!){ updateDataset(updateDatasetInput:$i){ ... on TypeDataset { id } } }",
        {"i": {"dataset": dataset_id, "title": title, "description": "qa-matrix consumer check", "license": "CC0_1_0"}})
    yield dataset_id, title
    gql(graphql_client, "mutation($id: UUID!){ unPublishDataset(datasetId:$id){ ... on TypeDataset { id } } }", {"id": dataset_id})
    gql(graphql_client, "mutation($id: UUID!){ deleteDataset(datasetId:$id) }", {"id": dataset_id})


def test_dataset_draft_hidden_published_visible_unpublished_hidden(graphql_client, anon_graphql_client, dataset):
    dataset_id, title = dataset
    read = "query($id: UUID!){ getDataset(datasetId:$id){ title license status } }"

    assert _errors(gql(anon_graphql_client, read, {"id": dataset_id})), "anonymous visitor read a draft dataset"

    gql(graphql_client, "mutation($id: UUID!){ publishDataset(datasetId:$id){ ... on TypeDataset { status } } }", {"id": dataset_id})
    got = gql(anon_graphql_client, read, {"id": dataset_id})["data"]["getDataset"]
    assert (got["title"], got["license"], got["status"]) == (title, "CC0_1_0", "PUBLISHED")

    gql(graphql_client, "mutation($id: UUID!){ unPublishDataset(datasetId:$id){ ... on TypeDataset { status } } }", {"id": dataset_id})
    assert _errors(gql(anon_graphql_client, read, {"id": dataset_id})), "unpublished dataset still readable anonymously"


@pytest.mark.xfail(strict=True, reason="DataSpaceBackend#290: published datasets never reach the search index on dev")
def test_published_dataset_is_searchable_and_drops_out_when_unpublished(graphql_client, anon_api_client, dataset):
    dataset_id, title = dataset
    gql(graphql_client, "mutation($id: UUID!){ publishDataset(datasetId:$id){ ... on TypeDataset { status } } }", {"id": dataset_id})

    def found():
        resp = anon_api_client.get("/api/search/dataset/", params={"q": title})
        return dataset_id in resp.text

    assert _wait(found), f"published dataset {title!r} not in search after 60s"
    gql(graphql_client, "mutation($id: UUID!){ unPublishDataset(datasetId:$id){ ... on TypeDataset { status } } }", {"id": dataset_id})
    assert _wait(lambda: not found()), "unpublished dataset still in search after 60s"


# ─── Use case / collaborative ─────────────────────────────────────────────────

@pytest.mark.parametrize("kind", ["UseCase", "Collaborative"])
def test_published_list_shows_only_after_publish(graphql_client, anon_graphql_client, kind):
    lower = kind[0].lower() + kind[1:]
    arg = "useCaseId" if kind == "UseCase" else "collaborativeId"
    listing = "publishedUseCases" if kind == "UseCase" else "publishedCollaboratives"
    body = gql(graphql_client, "mutation{ add%s { ... on Type%s { id } } }" % (kind, kind))
    item_id = body["data"][f"add{kind}"]["id"]
    title = f"[qa-matrix] {kind} visibility {uuid.uuid4().hex[:6]}"
    try:
        gql(graphql_client, "mutation($d: %sInputPartial!){ update%s(data:$d){ id } }" % (kind, kind), {"d": {"id": item_id, "title": title}})

        def listed():
            items = gql(anon_graphql_client, "{ %s { id } }" % listing)["data"][listing]
            return item_id in [str(i["id"]) for i in items]

        assert not listed(), f"draft {kind} listed publicly"
        gql(graphql_client, "mutation($i: String!){ publish%s(%s:$i){ ... on Type%s { status } } }" % (kind, arg, kind), {"i": item_id})
        assert listed(), f"published {kind} not listed"
        gql(graphql_client, "mutation($i: String!){ unpublish%s(%s:$i){ ... on Type%s { status } } }" % (kind, arg, kind), {"i": item_id})
        assert not listed(), f"unpublished {kind} still listed"
    finally:
        gql(graphql_client, "mutation($i: String!){ delete%s(%s:$i) }" % (kind, arg), {"i": item_id})


# ─── AI model ─────────────────────────────────────────────────────────────────

@pytest.mark.parametrize("is_public,visible", [(False, False), (True, True)], ids=["private", "public"])
def test_ai_model_visibility_follows_is_public(graphql_client, anon_graphql_client, is_public, visible):
    body = gql(graphql_client, "mutation($i: CreateAIModelInput!){ createAiModel(input:$i){ success data { id } } }",
               {"i": {"modelType": "TEXT_GENERATION", "provider": "CUSTOM", "name": f"qa-matrix-vis-{uuid.uuid4().hex[:8]}",
                      "isPublic": is_public}})
    model_id = int(body["data"]["createAiModel"]["data"]["id"])
    try:
        got = gql(anon_graphql_client, "query($id: Int!){ getAiModel(modelId:$id){ id } }", {"id": model_id})
        assert ((got.get("data") or {}).get("getAiModel") is not None) == visible, got
    finally:
        gql(graphql_client, "mutation($id: Int!){ deleteAiModel(modelId:$id){ success } }", {"id": model_id})
