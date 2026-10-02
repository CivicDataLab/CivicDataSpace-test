# tests/api/smoke/test_api_018_platform_import_source.py
#
# Pending: covers open CivicDataLab/DataSpaceBackend#204 (head f7fe195a).
# Skipped in CI until it merges. Safe to merge before it.
#
# #204 adds link-only dataset import from Hugging Face, GitHub and Kaggle.
# Two read-only, unauthenticated-visible signals of the change reaching dev,
# neither of which needs an actual imported dataset to exist yet:
#
#   - GraphQL `TypeDataset` gains a nullable `source` field (provenance for
#     an imported dataset; null for every native one).
#   - `GET /api/search/dataset/` gains a `source_platform` terms-aggregation
#     bucket in the response's `aggregations` object, alongside the existing
#     dataset_type/sectors/tags/formats/geographies buckets.
#
# Never `readonly`: the backend `main` deploy gate runs `readonly` tests
# against prod, and this feature isn't on main yet (#204 isn't even merged
# to dev). Follow-up once it ships: add
# `deployed_pr("DataSpaceBackend#204")` + `readonly`, the same way #150/#151
# did for #214/#215 (see test_api_013_datasets_table.py /
# test_api_014_publication_blocks_schema.py).

import pytest

pytestmark = [
    pytest.mark.api,
    pytest.mark.smoke,
    pytest.mark.pending_pr("DataSpaceBackend#204"),
]


def test_graphql_dataset_source_field_exists(anon_graphql_client):
    """`datasets { source { platform } } }` should resolve once #204 ships.

    Pre-merge, the field doesn't exist at all: Strawberry returns a schema
    error ("Cannot query field 'source' on type 'TypeDataset'. Did you mean
    'resources'?"), which GraphQLClient.query() turns into an AssertionError
    -- captured live against dev on 2026-10-02 (see PR body).

    Every dataset on dev today was created natively (nothing has been
    imported from a platform yet), so once the field exists it must resolve
    to null for all of them rather than erroring.
    """
    data = anon_graphql_client.query(
        "{ datasets { id source { platform sourceUrl } } }"
    )
    assert "datasets" in data, f"Expected 'datasets' in response, got: {data}"
    for row in data["datasets"]:
        assert row["source"] is None, (
            f"Expected null source for a native dataset, got: {row}"
        )


def test_search_dataset_source_platform_aggregation_present(anon_api_client):
    """`GET /api/search/dataset/` should report a `source_platform` bucket.

    Pre-merge, `aggregations` only has dataset_type/sectors/tags/formats/
    geographies -- `source_platform` isn't in the aggregation config yet, so
    the key is absent, not merely empty. Captured live against dev on
    2026-10-02: aggregations.keys() ==
    ['dataset_type', 'sectors', 'tags', 'formats', 'geographies'].
    """
    resp = anon_api_client.get("/api/search/dataset/")
    assert resp.status_code == 200, (
        f"Dataset search failed ({resp.status_code}): {resp.text}"
    )
    aggregations = resp.json().get("aggregations", {})
    assert "source_platform" in aggregations, (
        f"Expected a 'source_platform' aggregation bucket once #204 ships, "
        f"got keys: {sorted(aggregations.keys())}"
    )
