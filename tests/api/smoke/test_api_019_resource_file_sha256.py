# tests/api/smoke/test_api_019_resource_file_sha256.py
#
# Covers DataSpaceBackend#212: a `sha256` on uploaded resource files, computed
# on save and exposed on GraphQL's `fileDetails`.
#
# - The field check is `readonly` + `deployed_pr`: an anonymous read, safe in
#   the prod gate, skipped wherever the backend doesn't serve #212 yet.
# - The hash check uploads a file to a draft dataset (deleted afterwards), so it
#   is a write test: never `readonly`, never run on prod.
#
# Files uploaded before #212 have no hash until `manage.py backfill_file_hashes`
# runs on that backend; on dev every older file was still null on 2026-10-06.

import hashlib
import json

import pytest
import requests

from tests.api.client import _request_with_retries

pytestmark = [pytest.mark.api, pytest.mark.deployed_pr("DataSpaceBackend#212")]

CSV = b"state,year,value\nAssam,2024,1\nBihar,2024,2\n"


@pytest.mark.smoke
@pytest.mark.readonly
def test_file_details_sha256_field_resolves(anon_graphql_client):
    """`fileDetails { sha256 }` is a real field, not a schema error.

    Without #212 Strawberry answers "Cannot query field 'sha256' on type
    'TypeFileDetails'", which a renamed or dropped field would also produce.
    """
    data = anon_graphql_client.query(
        "{ datasets(includePublic: true, pagination: {limit: 50}) { resources { type fileDetails { sha256 } } } }"
    )
    details = [
        res["fileDetails"] for row in data["datasets"] for res in row["resources"]
        if res["type"] == "FILE" and res.get("fileDetails")
    ]
    if not details:
        pytest.skip("no FILE resource with fileDetails on this backend")
    for d in details:
        assert d["sha256"] is None or isinstance(d["sha256"], str), d


@pytest.fixture
def draft_dataset_id(graphql_client):
    result = graphql_client.query(
        "mutation{ addDataset(createInput: {datasetType: DATA}){ success data { id } } }"
    )["addDataset"]
    assert result["success"], result
    yield result["data"]["id"]
    graphql_client.query("mutation($id: UUID!){ deleteDataset(datasetId: $id) }", {"id": result["data"]["id"]})


@pytest.mark.functional
def test_uploaded_file_stores_its_real_sha256(api_base_url, auth_token, graphql_client, draft_dataset_id):
    """A fresh upload is hashed on save, and the stored value is the file's real SHA-256."""
    operations = {
        "query": "mutation($i: CreateFileResourceInput!){ createFileResources(fileResourceInput: $i)"
                 "{ id fileDetails { sha256 } } }",
        "variables": {"i": {"dataset": draft_dataset_id, "files": [None]}},
    }
    resp = _request_with_retries(
        requests.post,
        f"{api_base_url}/api/graphql",
        headers={"Authorization": f"Bearer {auth_token}"},
        data={"operations": json.dumps(operations), "map": json.dumps({"0": ["variables.i.files.0"]})},
        files={"0": ("hash.csv", CSV, "text/csv")},
    )
    body = resp.json()
    assert "errors" not in body, body["errors"]
    expected = hashlib.sha256(CSV).hexdigest()
    assert body["data"]["createFileResources"][0]["fileDetails"]["sha256"] == expected, body

    stored = graphql_client.query(
        "query($id: UUID!){ getDataset(datasetId: $id){ resources { fileDetails { sha256 } } } }",
        {"id": draft_dataset_id},
    )["getDataset"]["resources"]
    assert [r["fileDetails"]["sha256"] for r in stored] == [expected]
