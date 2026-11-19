# tests/api/smoke/test_api_030_source_identifier_metadata.py
#
# Covers DataSpaceBackend#250: a data migration
# (0054_add_source_identifier_metadata) adds the "Source identifier" dataset
# metadata item. CivicDataLab's scrapers look this item up by its exact
# label, on datasets, while it is switched on, to avoid re-creating datasets
# they've already uploaded -- so a regression here (the item missing,
# renamed, or switched off) silently breaks that de-duplication, not any
# code path this repo already exercises.
#
# The migration itself is already covered thoroughly in-repo
# (DataSpaceBackend/tests/test_source_identifier_migration.py: missing,
# switched-off, idempotency, model isolation -- 4 tests). What's missing is
# a live check that the item actually exists, correctly, on real
# environments -- the same role test_api_023_resource_types_seeded.py plays
# for DataSpaceBackend#223's seed migration.
#
# `readonly`: `metadata` is an unauthenticated, public GraphQL query.
# `deployed_pr`: #250 has not reached `main`/prod yet (confirmed via
# `git merge-base --is-ancestor <merge-sha> origin/main` in DataSpaceBackend),
# so this is gated the same way #223/#245/#215 were.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#250")]

LABEL = "Source identifier"


@pytest.mark.smoke
def test_source_identifier_metadata_item_exists_and_is_enabled(anon_graphql_client):
    """The scrapers' exact lookup must keep matching: one DATASET item named
    "Source identifier", switched on.

    Scoped down from the live `metadata` query (which returns every model's
    items) to just this label/model pair, so a regression that adds a
    second same-named item (migration re-run without the get_or_create
    guard, or someone creating a duplicate by hand) is also caught.
    """
    rows = anon_graphql_client.query("{ metadata { label model enabled dataType type } }")[
        "metadata"
    ]
    matches = [r for r in rows if r["label"] == LABEL and r["model"] == "DATASET"]
    assert len(matches) == 1, (
        f"expected exactly one DATASET metadata item labelled {LABEL!r}, found {matches}"
    )
    item = matches[0]
    assert item["enabled"] is True, f"{LABEL!r} must stay switched on for the scrapers: {item}"
    assert item["dataType"] == "STRING", item
    assert item["type"] == "OPTIONAL", item
