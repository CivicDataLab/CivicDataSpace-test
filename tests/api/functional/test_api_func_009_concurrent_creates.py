# tests/api/functional/test_api_func_009_concurrent_creates.py
#
# Simultaneous creates must all succeed:
#   DataSpaceBackend#232 (fixed by #273): addDataset calls in the same second
#     picked the same "new-dataset-<date>-<time>-N" slug and one failed on
#     dataset_slug_0c6f9de7_uniq (dev 2026-10-06: 1 of 6 parallel creates).
#   DataSpaceBackend#229 (fixed by #276): uploads of the same file name at the
#     same moment failed on api_resource_slug_ad6fedeb_uniq.
# A barrier releases the requests together so they race on the backend.

import threading
from concurrent.futures import ThreadPoolExecutor

import pytest

from tests.api.functional.test_api_func_006_resource_upload_matrix import CSV, upload  # noqa: F401 (fixture)
from tests.api.publications import gql

pytestmark = [pytest.mark.api, pytest.mark.functional]

PARALLEL = 6
ADD = "mutation{ addDataset(createInput:{datasetType: DATA}){ success errors { fieldErrors { messages } } data { id } } }"
DELETE = "mutation($id: UUID!){ deleteDataset(datasetId:$id) }"


def _together(fn, n=PARALLEL):
    """Run fn(i) for i in range(n), released at the same instant."""
    gate = threading.Barrier(n)

    def run(i):
        gate.wait()
        return fn(i)

    with ThreadPoolExecutor(n) as pool:
        return list(pool.map(run, range(n)))


@pytest.fixture
def created(graphql_client):
    ids = []
    yield ids
    for dataset_id in ids:
        gql(graphql_client, DELETE, {"id": dataset_id})


def test_simultaneous_add_dataset_calls_all_succeed(graphql_client, created):
    results = _together(lambda i: graphql_client.query(ADD)["addDataset"])
    created += [r["data"]["id"] for r in results if r.get("data")]
    failed = [r["errors"] for r in results if not r.get("success")]
    assert not failed, f"{len(failed)} of {PARALLEL} simultaneous addDataset calls failed: {failed}"
    assert len(set(created)) == PARALLEL, f"Expected {PARALLEL} distinct datasets, got {created}"


def test_simultaneous_same_name_uploads_all_succeed(graphql_client, created, upload):
    for _ in range(PARALLEL):
        created.append(graphql_client.query(ADD)["addDataset"]["data"]["id"])
    bodies = _together(lambda i: upload(created[i], "data.csv", CSV))
    failed = [b.get("errors") for b in bodies if b.get("errors") or not (b.get("data") or {}).get("createFileResources")]
    assert not failed, f"{len(failed)} of {PARALLEL} simultaneous 'data.csv' uploads failed: {failed}"
