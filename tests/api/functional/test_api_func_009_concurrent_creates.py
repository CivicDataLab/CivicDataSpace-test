# tests/api/functional/test_api_func_009_concurrent_creates.py
#
# Simultaneous creates must all succeed:
#   DataSpaceBackend#232 (fixed by #273): addDataset calls in the same second
#     picked the same "new-dataset-<date>-<time>-N" slug and one failed on
#     dataset_slug_0c6f9de7_uniq (dev 2026-10-06: 1 of 6 parallel creates).
#   DataSpaceBackend#229 (fixed by #276): uploads of the same file name at the
#     same moment failed on api_resource_slug_ad6fedeb_uniq.
#   DataSpaceBackend#323: addCollaborative calls in the same second got the
#     same default title ("New collaborative <date>-<time>") and only the
#     database-level slug collision was retried with a suffix -- one caught
#     by validation instead failed the whole create.
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
ADD_COLLABORATIVE = "mutation{ addCollaborative { ... on TypeCollaborative { id slug } ... on OperationInfo { messages { message } } } }"
DELETE_COLLABORATIVE = "mutation($i: String!){ deleteCollaborative(collaborativeId:$i) }"


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


@pytest.fixture
def created_collaboratives(graphql_client):
    ids = []
    yield ids
    for collaborative_id in ids:
        gql(graphql_client, DELETE_COLLABORATIVE, {"i": collaborative_id})


def test_simultaneous_add_collaborative_calls_all_succeed(graphql_client, created_collaboratives):
    """DataSpaceBackend#323: with no title given, every addCollaborative call
    gets the identical default title ("New collaborative <date>-<time>", to
    the second) and its slug comes from that title. Releasing several calls
    at the same instant forces the second one's validation to see the first
    one's slug as already taken before its own save commits -- the case the
    fix added a retry-with-suffix for. All calls must still succeed, each
    with a distinct slug.
    """
    results = _together(lambda i: graphql_client.query(ADD_COLLABORATIVE)["addCollaborative"])
    created_collaboratives += [r["id"] for r in results if "id" in r]
    failed = [r for r in results if "id" not in r]
    assert not failed, f"{len(failed)} of {PARALLEL} simultaneous addCollaborative calls failed: {failed}"
    slugs = [r["slug"] for r in results]
    assert len(set(slugs)) == PARALLEL, f"Expected {PARALLEL} distinct slugs, got {slugs}"
