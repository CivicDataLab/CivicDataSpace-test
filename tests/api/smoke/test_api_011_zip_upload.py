# tests/api/smoke/test_api_011_zip_upload.py
#
# Regression coverage for DataSpaceBackend#206: .zip data files were rejected.
#
# createFileResources accepts a file only when its extension and its sniffed
# MIME type map to the same format (file_validation in api/utils/file_utils.py).
# The sniff used magic.from_buffer, and the server's libmagic (5.46) reports a
# zip buffer as application/octet-stream, which maps to nothing, so every .zip
# upload failed with "Unsupported file format." #206 sniffs the stored file
# with magic.from_file instead, which reports application/zip.
#
# Writes: each test creates a draft dataset and deletes it afterwards, so these
# are deliberately NOT readonly and never run against production.

import io
import json
import zipfile

import pytest
import requests

from tests.api.client import _request_with_retries

CREATE_DATASET_MUTATION = """
mutation CreateDataset($datasetType: DatasetType) {
  addDataset(createInput: { datasetType: $datasetType }) {
    success
    data { id }
  }
}
"""

DELETE_DATASET_MUTATION = """
mutation DeleteDataset($datasetId: UUID!) {
  deleteDataset(datasetId: $datasetId)
}
"""

CREATE_FILE_RESOURCES_MUTATION = """
mutation CreateFileResources($fileResourceInput: CreateFileResourceInput!) {
  createFileResources(fileResourceInput: $fileResourceInput) {
    id
    name
    fileDetails { format }
  }
}
"""


def _zip_bytes() -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("data.csv", "state,year,value\nAssam,2024,1\nBihar,2024,2\n")
    return buf.getvalue()


@pytest.fixture
def draft_dataset_id(graphql_client):
    data = graphql_client.query(CREATE_DATASET_MUTATION, {"datasetType": "DATA"})
    result = data["addDataset"]
    assert result.get("success"), f"addDataset returned success=False: {result}"
    dataset_id = result["data"]["id"]
    yield dataset_id
    graphql_client.query(DELETE_DATASET_MUTATION, {"datasetId": dataset_id})


def _upload(api_base_url, auth_token, dataset_id, filename, content) -> dict:
    """POST a GraphQL multipart upload (the same request the dataset editor sends)."""
    operations = {
        "query": CREATE_FILE_RESOURCES_MUTATION,
        "variables": {"fileResourceInput": {"dataset": dataset_id, "files": [None]}},
    }
    resp = _request_with_retries(
        requests.post,
        f"{api_base_url.rstrip('/')}/api/graphql",
        headers={"Authorization": f"Bearer {auth_token}"},
        data={
            "operations": json.dumps(operations),
            "map": json.dumps({"0": ["variables.fileResourceInput.files.0"]}),
        },
        files={"0": (filename, content, "application/zip")},
    )
    assert resp.status_code == 200, (
        f"POST /api/graphql upload of {filename!r} returned {resp.status_code}: {resp.text[:500]}"
    )
    return resp.json()


@pytest.mark.api
@pytest.mark.smoke
def test_zip_datafile_is_accepted_as_zip(api_base_url, auth_token, draft_dataset_id):
    """A real .zip upload is stored as a resource with format ZIP."""
    body = _upload(api_base_url, auth_token, draft_dataset_id, "sample.zip", _zip_bytes())

    assert "errors" not in body, (
        f"createFileResources rejected a valid .zip on {api_base_url}: {body.get('errors')}"
    )
    resources = body["data"]["createFileResources"]
    assert len(resources) == 1, f"Expected 1 resource, got {resources}"
    fmt = (resources[0].get("fileDetails") or {}).get("format")
    assert fmt == "ZIP", f"Expected uploaded .zip to be stored with format 'ZIP', got {fmt!r}"


@pytest.mark.api
@pytest.mark.smoke
def test_zip_bytes_named_csv_are_rejected(api_base_url, auth_token, draft_dataset_id):
    """
    Control: the extension/content check still runs. Zip bytes named .csv must be
    refused, so the test above passes because zips are recognised, not because
    validation was skipped. This one also passed before #206.
    """
    body = _upload(api_base_url, auth_token, draft_dataset_id, "sample.csv", _zip_bytes())

    errors = body.get("errors") or []
    messages = " | ".join(e.get("message", "") for e in errors)
    assert "Unsupported file format" in messages, (
        f"Expected zip bytes named .csv to be rejected as 'Unsupported file format' "
        f"on {api_base_url}, got errors={errors!r} data={body.get('data')!r}"
    )
