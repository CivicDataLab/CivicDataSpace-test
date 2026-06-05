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

import uuid
from datetime import datetime

import pytest


# ─── Mutations ───────────────────────────────────────────────────────────────────

CREATE_DATASET_MUTATION = """
mutation CreateDataset($datasetType: DatasetTypeENUM) {
  addDataset(createInput: { datasetType: $datasetType }) {
    id
    status
    datasetType
  }
}
"""

UPDATE_METADATA_MUTATION = """
mutation UpdateMetadata(
  $dataset: UUID!
  $title: String
  $description: String
  $tags: [String]
  $accessType: DatasetAccessTypeENUM
  $license: DatasetLicenseENUM
) {
  addUpdateDatasetMetadata(updateMetadataInput: {
    dataset: $dataset
    metadata: []
    description: $description
    tags: $tags
    accessType: $accessType
    license: $license
  }) {
    id
    title
    description
    status
  }
}
"""

UPDATE_DATASET_MUTATION = """
mutation UpdateDataset(
  $dataset: UUID!
  $title: String
  $description: String
  $tags: [String]
  $accessType: DatasetAccessTypeENUM
) {
  updateDataset(updateDatasetInput: {
    dataset: $dataset
    title: $title
    description: $description
    tags: $tags
    accessType: $accessType
  }) {
    id
    title
    description
    status
  }
}
"""

PUBLISH_DATASET_MUTATION = """
mutation PublishDataset($datasetId: UUID!) {
  publishDataset(datasetId: $datasetId) {
    id
    status
  }
}
"""

UNPUBLISH_DATASET_MUTATION = """
mutation UnpublishDataset($datasetId: UUID!) {
  unPublishDataset(datasetId: $datasetId) {
    id
    status
  }
}
"""

DELETE_DATASET_MUTATION = """
mutation DeleteDataset($datasetId: UUID!) {
  deleteDataset(datasetId: $datasetId) {
    id
  }
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
    dataset = data["addDataset"]

    try:
        assert dataset.get("id"), "Created dataset has no id"
        assert dataset.get("status") == "DRAFT", (
            f"Expected DRAFT status, got: {dataset.get('status')}"
        )
    finally:
        # Cleanup
        if dataset.get("id"):
            graphql_client.query(
                DELETE_DATASET_MUTATION,
                {"datasetId": dataset["id"]},
            )


@pytest.mark.api
@pytest.mark.functional
def test_dataset_full_lifecycle(graphql_client):
    """
    Full lifecycle: create → update title → publish → verify status → unpublish → delete.
    """
    # 1. Create
    create_data = graphql_client.query(
        CREATE_DATASET_MUTATION, {"datasetType": "DATA"}
    )
    dataset_id = create_data["addDataset"]["id"]
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
        publish_data = graphql_client.query(
            PUBLISH_DATASET_MUTATION, {"datasetId": dataset_id}
        )
        published = publish_data.get("publishDataset", {})
        assert published.get("status") == "PUBLISHED", (
            f"Expected PUBLISHED status after publish, got: {published.get('status')}"
        )

        # 5. Verify published via getDataset
        get_data = graphql_client.query(
            GET_DATASET_QUERY, {"datasetId": dataset_id}
        )
        fetched = get_data.get("getDataset", {})
        assert fetched.get("status") == "PUBLISHED", (
            f"getDataset shows status {fetched.get('status')} instead of PUBLISHED"
        )

        # 6. Unpublish before deletion
        graphql_client.query(
            UNPUBLISH_DATASET_MUTATION, {"datasetId": dataset_id}
        )

    finally:
        # Always clean up
        graphql_client.query(DELETE_DATASET_MUTATION, {"datasetId": dataset_id})


@pytest.mark.api
@pytest.mark.functional
def test_get_dataset_returns_correct_fields(graphql_client):
    """
    getDataset query must return a dataset with the expected fields.
    Creates a temporary dataset for this test.
    """
    create_data = graphql_client.query(
        CREATE_DATASET_MUTATION, {"datasetType": "DATA"}
    )
    dataset_id = create_data["addDataset"]["id"]

    try:
        get_data = graphql_client.query(
            GET_DATASET_QUERY, {"datasetId": dataset_id}
        )
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
    create_data = graphql_client.query(
        CREATE_DATASET_MUTATION, {"datasetType": "DATA"}
    )
    dataset_id = create_data["addDataset"]["id"]

    # Delete it
    graphql_client.query(DELETE_DATASET_MUTATION, {"datasetId": dataset_id})

    # Verify it's gone from the list
    list_data = graphql_client.query(DATASETS_QUERY)
    dataset_ids = [d["id"] for d in list_data.get("datasets", [])]
    assert dataset_id not in dataset_ids, (
        f"Deleted dataset {dataset_id} still appears in datasets list"
    )
