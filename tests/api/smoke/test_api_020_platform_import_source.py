# tests/api/smoke/test_api_020_platform_import_source.py
#
# Covers DataSpaceBackend#204: link-only dataset import from Hugging Face,
# GitHub and Kaggle. Two anonymous, read-only signals that don't need an
# imported dataset to exist:
#
#   - `TypeDataset.source`: provenance of an imported dataset, null otherwise.
#   - `GET /api/search/dataset/`: a `source_platform` aggregation bucket.
#
# `readonly` + `deployed_pr`: safe in the prod gate, skipped wherever the
# backend doesn't serve #204 yet. Not covered: `previewPlatformDataset` /
# `importPlatformDataset` (login + live calls to the external platforms).

import pytest

pytestmark = [
    pytest.mark.api,
    pytest.mark.smoke,
    pytest.mark.readonly,
    pytest.mark.deployed_pr("DataSpaceBackend#204"),
]

PLATFORMS = {"HUGGINGFACE", "GITHUB", "KAGGLE"}


def test_dataset_source_resolves_for_public_datasets(anon_graphql_client):
    """`source` is queryable on public datasets: null, or a known platform with a URL.

    Without #204 the query fails: "Cannot query field 'source' on type 'TypeDataset'".
    """
    rows = anon_graphql_client.query(
        "{ datasets(includePublic: true, pagination: {limit: 100}) { id source { platform sourceUrl } } }"
    )["datasets"]
    assert rows, "no public datasets to read `source` from"
    for row in rows:
        source = row["source"]
        if source is not None:
            assert source["platform"] in PLATFORMS and source["sourceUrl"], row


def test_search_reports_a_source_platform_bucket(anon_api_client):
    """Dataset search aggregates by source platform (empty until something is imported)."""
    resp = anon_api_client.get("/api/search/dataset/")
    assert resp.status_code == 200, f"Dataset search failed ({resp.status_code}): {resp.text}"
    aggregations = resp.json().get("aggregations", {})
    assert "source_platform" in aggregations, (
        f"no 'source_platform' aggregation, got keys: {sorted(aggregations)}"
    )
