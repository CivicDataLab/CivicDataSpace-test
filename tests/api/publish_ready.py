# tests/api/publish_ready.py
#
# Fill a draft with what DataSpaceBackend#310 requires before it may be
# published (api/services/publish_requirements.py on the backend). Tests that
# need a published record call these instead of publishing a bare draft.

import json

from tests.api.publications import gql

PNG_1PX = bytes.fromhex(
    "89504e470d0a1a0a0000000d4948445200000001000000010806000000"
    "1f15c4890000000d49444154789c6360000002000100e221bc330000000049454e44ae426082"
)
SUMMARY_BLOCKS = json.dumps({"version": 1, "blocks": [{"type": "text", "html": "<p>qa-matrix publish check</p>"}]})


def _ok(body, field):
    assert not body.get("errors") and body["data"][field] is not None, body
    return body["data"][field]


def _taxonomy(client):
    data = gql(client, "{ sectors { id } allSdgs { id } }")["data"]
    return data["sectors"][0]["id"], data["allSdgs"][0]["id"]


def _upload(client, query, variables, path, filename, content):
    """A GraphQL multipart upload: one file at `path` in the variables."""
    resp = client.session.post(
        client.endpoint,
        headers={"Content-Type": None},  # let requests set the multipart boundary
        data={"operations": json.dumps({"query": query, "variables": variables}), "map": json.dumps({"0": [path]})},
        files={"0": (filename, content)},
    )
    resp.raise_for_status()
    return resp.json()


def public_dataset_id(client):
    """Any published dataset, to connect a use case or collaborative to."""
    results = client.session.get(client.endpoint.replace("/api/graphql", "/api/search/dataset/"), params={"size": 1}).json()["results"]
    assert results, "no published dataset on this environment to connect"
    return results[0]["id"]


def add_resource(client, dataset_id):
    _ok(_upload(client, "mutation($i: CreateFileResourceInput!){ createFileResources(fileResourceInput:$i){ id } }",
                {"i": {"dataset": dataset_id, "files": [None]}}, "variables.i.files.0", "qa.csv", b"a,b\n1,2\n"),
        "createFileResources")


def add_logo(client, kind, item_id):
    """kind: "UseCase" or "Collaborative"."""
    _ok(_upload(client, "mutation($d: %sInputPartial!){ update%s(data:$d){ id } }" % (kind, kind),
                {"d": {"id": item_id, "logo": None}}, "variables.d.logo", "logo.png", PNG_1PX),
        f"update{kind}")


def connect_dataset(client, kind, item_id):
    """Link any published dataset to a use case or collaborative."""
    if kind == "UseCase":
        query, field = "mutation($i: String!, $d: [UUID!]!){ updateUsecaseDatasets(useCaseId:$i, datasetIds:$d){ __typename } }", "updateUsecaseDatasets"
    else:
        query, field = "mutation($i: String!, $d: [UUID!]!){ updateCollaborativeDatasets(collaborativeId:$i, datasetIds:$d){ __typename } }", "updateCollaborativeDatasets"
    _ok(gql(client, query, {"i": item_id, "d": [public_dataset_id(client)]}), field)


def make_dataset_publishable(client, dataset_id, tags=("qa-matrix",)):
    """Pass the caller's own tags: this replaces the dataset's tag list."""
    sector, _ = _taxonomy(client)
    add_resource(client, dataset_id)
    _ok(gql(client, "mutation($i: UpdateMetadataInput!){ addUpdateDatasetMetadata(updateMetadataInput:$i){ success } }",
            {"i": {"dataset": dataset_id, "metadata": [], "description": "qa-matrix publish check",
                   "tags": list(tags), "sectors": [sector], "license": "CC0_1_0"}}),
        "addUpdateDatasetMetadata")


def make_use_case_publishable(client, use_case_id):
    sector, sdg = _taxonomy(client)
    add_logo(client, "UseCase", use_case_id)
    _ok(gql(client, "mutation($d: UseCaseInputPartial!){ updateUseCase(data:$d){ id } }",
            {"d": {"id": use_case_id, "summary": SUMMARY_BLOCKS}}), "updateUseCase")
    _ok(gql(client, """mutation($i: UpdateUseCaseMetadataInput!){ addUpdateUsecaseMetadata(updateMetadataInput:$i){
              ... on TypeUseCase { id } } }""",
            {"i": {"id": use_case_id, "metadata": [], "tags": None, "sectors": [sector], "sdgs": [sdg], "geographies": []}}),
        "addUpdateUsecaseMetadata")
    connect_dataset(client, "UseCase", use_case_id)


def make_collaborative_publishable(client, collaborative_id):
    sector, sdg = _taxonomy(client)
    _ok(gql(client, "mutation($d: CollaborativeInputPartial!){ updateCollaborative(data:$d){ id } }",
            {"d": {"id": collaborative_id, "summary": "<p>qa-matrix publish check</p>"}}),
        "updateCollaborative")
    _ok(gql(client, """mutation($i: UpdateCollaborativeMetadataInput!){ addUpdateCollaborativeMetadata(updateMetadataInput:$i){
              ... on TypeCollaborative { id } } }""",
            {"i": {"id": collaborative_id, "metadata": [], "tags": None, "sectors": [sector], "sdgs": [sdg], "geographies": []}}),
        "addUpdateCollaborativeMetadata")
    connect_dataset(client, "Collaborative", collaborative_id)
