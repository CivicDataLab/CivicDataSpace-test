# tests/api/functional/test_api_func_001_datasets.py
#
# Functional API tests for the full Dataset lifecycle via GraphQL:
#   1. Create a dataset (addDataset)
#   2. Update its metadata (addUpdateDatasetMetadata)
#   3. Verify it appears in the datasets query
#   4. Publish the dataset (publishDataset)
#   5. Verify published status
#   6. Unpublish and delete (cleanup)
#
# These tests run against real data — they create and delete actual records.

import time
from datetime import datetime

import pytest


# ─── Mutations ───────────────────────────────────────────────────────────────────

# addDataset / addUpdateDatasetMetadata return TypeDatasetMutationResponse
# { success, errors { ... }, data { ... } }
CREATE_DATASET_MUTATION = """
mutation CreateDataset($datasetType: DatasetType) {
  addDataset(createInput: { datasetType: $datasetType }) {
    success
    data {
      id
      status
      datasetType
    }
  }
}
"""

UPDATE_METADATA_MUTATION = """
mutation UpdateMetadata(
  $dataset: UUID!
  $description: String
  $tags: [String!]
  $accessType: DatasetAccessType
  $license: DatasetLicense
) {
  addUpdateDatasetMetadata(updateMetadataInput: {
    dataset: $dataset
    metadata: []
    description: $description
    tags: $tags
    accessType: $accessType
    license: $license
  }) {
    success
    data {
      id
      title
      description
      status
    }
  }
}
"""

# updateDataset / publishDataset / unPublishDataset return a union
# (TypeDataset | OperationInfo) — use inline fragments
UPDATE_DATASET_MUTATION = """
mutation UpdateDataset(
  $dataset: UUID!
  $title: String
  $description: String
  $tags: [String!]
  $accessType: DatasetAccessType
) {
  updateDataset(updateDatasetInput: {
    dataset: $dataset
    title: $title
    description: $description
    tags: $tags
    accessType: $accessType
  }) {
    ... on TypeDataset {
      id
      title
      description
      status
    }
    ... on OperationInfo {
      messages { message }
    }
  }
}
"""

PUBLISH_DATASET_MUTATION = """
mutation PublishDataset($datasetId: UUID!) {
  publishDataset(datasetId: $datasetId) {
    ... on TypeDataset {
      id
      status
    }
    ... on OperationInfo {
      messages { message }
    }
  }
}
"""

UNPUBLISH_DATASET_MUTATION = """
mutation UnpublishDataset($datasetId: UUID!) {
  unPublishDataset(datasetId: $datasetId) {
    ... on TypeDataset {
      id
      status
    }
    ... on OperationInfo {
      messages { message }
    }
  }
}
"""

# deleteDataset returns Boolean — no selection set
DELETE_DATASET_MUTATION = """
mutation DeleteDataset($datasetId: UUID!) {
  deleteDataset(datasetId: $datasetId)
}
"""

GET_DATASET_QUERY = """
query GetDataset($datasetId: UUID!) {
  getDataset(datasetId: $datasetId) {
    id
    title
    status
    description
  }
}
"""

DATASETS_QUERY = """
query {
  datasets {
    id
    title
    status
  }
}
"""


def _unique_title() -> str:
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    return f"API Automated Test Dataset — {timestamp}"


def _unique_description() -> str:
    return f"Created by API functional test at {datetime.now().isoformat()}"


# ─── Tests ───────────────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.functional
def test_create_dataset_returns_id_and_draft_status(graphql_client):
    """
    addDataset mutation must return a new dataset with DRAFT status.
    Cleans up the created dataset afterward.
    """
    data = graphql_client.query(CREATE_DATASET_MUTATION, {"datasetType": "DATA"})
    assert "addDataset" in data, f"Expected 'addDataset' in response: {data}"
    result = data["addDataset"]
    assert result.get("success"), f"addDataset returned success=False: {result}"
    dataset = result["data"]

    try:
        assert dataset.get("id"), "Created dataset has no id"
        assert dataset.get("status") == "DRAFT", (
            f"Expected DRAFT status, got: {dataset.get('status')}"
        )
    finally:
        if dataset.get("id"):
            graphql_client.query(DELETE_DATASET_MUTATION, {"datasetId": dataset["id"]})


@pytest.mark.api
@pytest.mark.functional
def test_dataset_full_lifecycle(graphql_client):
    """
    Full lifecycle: create → update title → publish → verify status → unpublish → delete.
    """
    # 1. Create
    create_data = graphql_client.query(CREATE_DATASET_MUTATION, {"datasetType": "DATA"})
    assert create_data["addDataset"]["success"], f"Create failed: {create_data}"
    dataset_id = create_data["addDataset"]["data"]["id"]
    assert dataset_id, "Dataset creation returned no id"

    try:
        title = _unique_title()
        description = _unique_description()

        # 2. Update title and description via updateDataset
        update_data = graphql_client.query(UPDATE_DATASET_MUTATION, {
            "dataset": dataset_id,
            "title": title,
            "description": description,
            "tags": ["automated-test"],
            "accessType": "PUBLIC",
        })
        updated = update_data.get("updateDataset", {})
        assert updated.get("title") == title, (
            f"Title mismatch: expected '{title}', got '{updated.get('title')}'"
        )

        # 3. Verify it appears in the datasets list
        list_data = graphql_client.query(DATASETS_QUERY)
        dataset_ids = [d["id"] for d in list_data.get("datasets", [])]
        assert dataset_id in dataset_ids, (
            f"Newly created dataset {dataset_id} not found in datasets list"
        )

        # 4. Publish
        publish_data = graphql_client.query(PUBLISH_DATASET_MUTATION, {"datasetId": dataset_id})
        published = publish_data.get("publishDataset", {})
        assert published.get("status") == "PUBLISHED", (
            f"Expected PUBLISHED status after publish, got: {published.get('status')}"
        )

        # 5. Verify published via getDataset
        get_data = graphql_client.query(GET_DATASET_QUERY, {"datasetId": dataset_id})
        fetched = get_data.get("getDataset", {})
        assert fetched.get("status") == "PUBLISHED", (
            f"getDataset shows status {fetched.get('status')} instead of PUBLISHED"
        )

        # 6. Unpublish before deletion
        graphql_client.query(UNPUBLISH_DATASET_MUTATION, {"datasetId": dataset_id})

    finally:
        graphql_client.query(DELETE_DATASET_MUTATION, {"datasetId": dataset_id})


@pytest.mark.api
@pytest.mark.functional
def test_get_dataset_returns_correct_fields(graphql_client):
    """
    getDataset query must return a dataset with the expected fields.
    Creates a temporary dataset for this test.
    """
    create_data = graphql_client.query(CREATE_DATASET_MUTATION, {"datasetType": "DATA"})
    assert create_data["addDataset"]["success"]
    dataset_id = create_data["addDataset"]["data"]["id"]

    try:
        get_data = graphql_client.query(GET_DATASET_QUERY, {"datasetId": dataset_id})
        dataset = get_data.get("getDataset", {})
        assert dataset.get("id") == dataset_id, "getDataset returned wrong id"
        assert "status" in dataset, "getDataset missing 'status' field"
    finally:
        graphql_client.query(DELETE_DATASET_MUTATION, {"datasetId": dataset_id})


@pytest.mark.api
@pytest.mark.functional
def test_delete_dataset_removes_from_list(graphql_client):
    """
    After deleteDataset, the dataset must no longer appear in the datasets list.
    """
    create_data = graphql_client.query(CREATE_DATASET_MUTATION, {"datasetType": "DATA"})
    assert create_data["addDataset"]["success"]
    dataset_id = create_data["addDataset"]["data"]["id"]

    # Delete it
    graphql_client.query(DELETE_DATASET_MUTATION, {"datasetId": dataset_id})

    # Verify it's gone from the list
    list_data = graphql_client.query(DATASETS_QUERY)
    dataset_ids = [d["id"] for d in list_data.get("datasets", [])]
    assert dataset_id not in dataset_ids, (
        f"Deleted dataset {dataset_id} still appears in datasets list"
    )


# ─── Search reflects publish / unpublish (DataSpaceBackend#193) ──────────────────
# Search results are cached for an hour under a version key that publishing bumps.
# Before #193 the bump ran before the Elasticsearch write, so a search right after
# publishing re-cached the old results under the new version for the full hour.

def _search_ids(anon_api_client) -> list[str]:
    """Ids of published datasets tagged automated-test, i.e. this suite's own.

    Filters on the tag (an exact keyword match) rather than a text query: title
    search runs a fuzzy term query against 4-gram tokens, so long queries match
    nothing.
    """
    resp = anon_api_client.get("/api/search/dataset/", params={"tags": "automated-test", "size": 100})
    assert resp.status_code == 200, f"dataset search failed ({resp.status_code}): {resp.text}"
    return [r["id"] for r in resp.json().get("results", [])]


def _create_titled_dataset(graphql_client, title: str) -> str:
    created = graphql_client.query(CREATE_DATASET_MUTATION, {"datasetType": "DATA"})
    assert created["addDataset"]["success"], f"Create failed: {created}"
    dataset_id = created["addDataset"]["data"]["id"]
    graphql_client.query(UPDATE_DATASET_MUTATION, {
        "dataset": dataset_id,
        "title": title,
        "description": _unique_description(),
        "tags": ["automated-test"],
        "accessType": "PUBLIC",
    })
    return dataset_id


def _wait_for(check, timeout: float = 20, interval: float = 2) -> bool:
    deadline = time.monotonic() + timeout
    while True:
        if check():
            return True
        if time.monotonic() >= deadline:
            return False
        time.sleep(interval)


@pytest.mark.api
@pytest.mark.functional
def test_published_dataset_is_searchable(graphql_client, anon_api_client):
    """Publishing makes a dataset findable in search; unpublishing removes it."""
    title = _unique_title()
    dataset_id = _create_titled_dataset(graphql_client, title)
    try:
        published = graphql_client.query(PUBLISH_DATASET_MUTATION, {"datasetId": dataset_id})
        assert published["publishDataset"]["status"] == "PUBLISHED", f"Publish failed: {published}"
        assert _wait_for(lambda: dataset_id in _search_ids(anon_api_client)), (
            f"Published dataset {dataset_id} ('{title}') never appeared in search"
        )

        graphql_client.query(UNPUBLISH_DATASET_MUTATION, {"datasetId": dataset_id})
        assert _wait_for(lambda: dataset_id not in _search_ids(anon_api_client)), (
            f"Unpublished dataset {dataset_id} ('{title}') is still in search"
        )
    finally:
        graphql_client.query(DELETE_DATASET_MUTATION, {"datasetId": dataset_id})


@pytest.mark.api
@pytest.mark.regression
def test_search_reflects_publish_without_waiting(graphql_client, anon_api_client):
    """Search is right the moment publish/unpublish returns, even for a cached query.

    The search before publishing caches an empty result for this exact query. If
    invalidation runs before the index write, or the write isn't refreshed, the
    reads below return that stale result: DataSpaceBackend#193.
    """
    title = _unique_title()
    dataset_id = _create_titled_dataset(graphql_client, title)
    try:
        assert dataset_id not in _search_ids(anon_api_client), (
            f"Draft dataset {dataset_id} is already in search before publishing"
        )

        graphql_client.query(PUBLISH_DATASET_MUTATION, {"datasetId": dataset_id})
        assert dataset_id in _search_ids(anon_api_client), (
            f"Search right after publishing is stale: {dataset_id} ('{title}') missing"
        )

        graphql_client.query(UNPUBLISH_DATASET_MUTATION, {"datasetId": dataset_id})
        assert dataset_id not in _search_ids(anon_api_client), (
            f"Search right after unpublishing is stale: {dataset_id} ('{title}') still listed"
        )
    finally:
        graphql_client.query(DELETE_DATASET_MUTATION, {"datasetId": dataset_id})
