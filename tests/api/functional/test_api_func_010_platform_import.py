# tests/api/functional/test_api_func_010_platform_import.py
#
# DataSpace#174 (#190 Hugging Face, #191 Kaggle, #192 GitHub), backend in
# DataSpaceBackend#204: preview a public dataset on each platform, import it as
# a draft that records where it came from, refuse a second import of the same
# dataset, and say clearly when a dataset does not exist.
#
# Functional, not smoke: it calls the three platforms live. Each import is a
# draft this test deletes.

import pytest

from tests.api.publications import gql

pytestmark = [pytest.mark.api, pytest.mark.functional, pytest.mark.deployed_pr("DataSpaceBackend#204")]

# Long-lived public datasets; preview needs no platform key.
DATASETS = {
    "HUGGINGFACE": ("stanfordnlp/imdb", "https://huggingface.co/datasets/stanfordnlp/imdb"),
    "GITHUB": ("datasets/covid-19", "https://github.com/datasets/covid-19"),
    "KAGGLE": ("zynicide/wine-reviews", "https://www.kaggle.com/datasets/zynicide/wine-reviews"),
}
PREVIEW = "query($p: ImportPlatform!, $i: String!){ previewPlatformDataset(platform:$p, identifier:$i){ title sourceUrl mappedLicense } }"
IMPORT = ("mutation($i: ImportPlatformDatasetInput!){ importPlatformDataset(importInput:$i){ success "
          "errors { fieldErrors { field messages } nonFieldErrors } data { id status source { platform sourceUrl } } } }")
OWN = "{ datasets(pagination:{limit:100}) { id source { platform sourceUrl } } }"
DELETE = "mutation($id: UUID!){ deleteDataset(datasetId:$id) }"

platforms = pytest.mark.parametrize("platform", list(DATASETS))


@platforms
def test_preview_reads_the_platform_metadata(graphql_client, platform):
    identifier, url = DATASETS[platform]
    body = gql(graphql_client, PREVIEW, {"p": platform, "i": identifier})
    assert "errors" not in body, f"{platform} preview of {identifier!r} failed: {body['errors']}"
    preview = body["data"]["previewPlatformDataset"]
    assert preview["title"] and preview["sourceUrl"] == url and preview["mappedLicense"], preview


def test_preview_of_a_missing_dataset_says_not_found(graphql_client):
    body = gql(graphql_client, PREVIEW, {"p": "HUGGINGFACE", "i": "zz-no-such/qa-missing-dataset"})
    message = " ".join(e["message"] for e in body.get("errors", []))
    assert "not found" in message.lower(), f"Expected a not-found message, got {body}"


@platforms
def test_import_creates_a_draft_once(graphql_client, platform):
    identifier, url = DATASETS[platform]
    own = gql(graphql_client, OWN)["data"]["datasets"]
    if any((d.get("source") or {}).get("sourceUrl") == url for d in own):
        pytest.skip(f"This account already holds an import of {url}; a second one is refused by design")

    first = gql(graphql_client, IMPORT, {"i": {"platform": platform, "identifier": identifier}})
    assert "errors" not in first, first["errors"]
    result = first["data"]["importPlatformDataset"]
    created = [(result.get("data") or {}).get("id")]
    try:
        assert result["success"], f"{platform} import failed: {result['errors']}"
        assert result["data"]["status"] == "DRAFT", result["data"]
        assert result["data"]["source"] == {"platform": platform, "sourceUrl": url}, result["data"]["source"]

        again = gql(graphql_client, IMPORT, {"i": {"platform": platform, "identifier": identifier}})
        created.append((((again.get("data") or {}).get("importPlatformDataset") or {}).get("data") or {}).get("id"))
        refused = "errors" in again or not again["data"]["importPlatformDataset"]["success"]
        assert refused, f"A second import of {identifier!r} was accepted: {again}"
    finally:
        for dataset_id in filter(None, created):
            gql(graphql_client, DELETE, {"id": dataset_id})
