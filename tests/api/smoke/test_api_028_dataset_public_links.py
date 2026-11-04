# tests/api/smoke/test_api_028_dataset_public_links.py
#
# Covers DataSpaceBackend#273 (merge commit
# 0cf7ee80f6f1b69741eb314e29cd23ea96953cc6): "permanent public links".
# getDataset(publicId: ...) now resolves a dataset from either its raw
# public_id, or the full url_slug ("<title-slug>-<public_id>"), using only
# the trailing public_id code — the title/slug prefix is deliberately
# ignored. That's the whole point: a dataset keeps resolving at its old
# link even after it's renamed, which test_survives_a_renamed_title_prefix
# below proves directly, not just that "some string worked".
#
# Confirmed live: on prod (api.datakeep.civicdays.in — #273 hasn't reached
# `main` yet) the identical query against the identical dataset errors with
# "Unknown argument 'publicId' on field 'Query.getDataset'". See the PR body
# for the pasted red/green runs.
#
# Read-only, anonymous — getDataset is public for PUBLISHED datasets
# (AllowPublishedDatasets permission class).

import pytest


@pytest.fixture(scope="module")
def published_dataset(anon_graphql_client):
    """A real published dataset with a public_id, picked at runtime."""
    data = anon_graphql_client.query(
        "{ datasets(includePublic: true, pagination: {limit: 20}) "
        "{ id title publicId urlSlug status } }"
    )
    for d in data["datasets"]:
        if d["status"] == "PUBLISHED" and d.get("publicId"):
            return d
    pytest.skip("No published dataset with a publicId on this environment")


GET_BY_PUBLIC_ID = """
query($publicId: String!) { getDataset(publicId: $publicId) { id title } }
"""


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#273")
def test_get_dataset_by_raw_public_id(anon_graphql_client, published_dataset):
    data = anon_graphql_client.query(
        GET_BY_PUBLIC_ID, {"publicId": published_dataset["publicId"]}
    )
    assert data["getDataset"] is not None, (
        f"getDataset(publicId={published_dataset['publicId']!r}) returned null"
    )
    assert data["getDataset"]["id"] == published_dataset["id"]


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#273")
def test_get_dataset_by_full_url_slug(anon_graphql_client, published_dataset):
    data = anon_graphql_client.query(
        GET_BY_PUBLIC_ID, {"publicId": published_dataset["urlSlug"]}
    )
    assert data["getDataset"] is not None, (
        f"getDataset(publicId={published_dataset['urlSlug']!r}) returned null"
    )
    assert data["getDataset"]["id"] == published_dataset["id"]


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#273")
def test_get_dataset_survives_a_renamed_title_prefix(anon_graphql_client, published_dataset):
    """The whole point of a permanent link: a link built with a DIFFERENT,
    wrong title still resolves, because only the trailing public_id is used.
    A flipped-assertion-only test wouldn't catch a regression where the
    resolver started requiring the title prefix to match too — this does,
    by deliberately mismatching it."""
    fake_slug = f"this-title-was-renamed-away-{published_dataset['publicId']}"
    data = anon_graphql_client.query(GET_BY_PUBLIC_ID, {"publicId": fake_slug})
    assert data["getDataset"] is not None, (
        f"a link with the wrong title prefix ({fake_slug!r}) failed to resolve — "
        f"the permanent link is not actually surviving a rename"
    )
    assert data["getDataset"]["id"] == published_dataset["id"]


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#273")
def test_get_dataset_rejects_unresolvable_public_id(anon_graphql_client):
    """A string with no valid trailing public_id code must not resolve to
    any dataset — distinguishes 'found by code' from 'anything goes'.
    Bypasses the client's query() helper (it raises on any GraphQL error)
    because an anonymous caller gets an auth-required error alongside the
    null, per the resolver's permission check for a not-found id/code."""
    resp = anon_graphql_client.session.post(
        anon_graphql_client.endpoint,
        json={"query": GET_BY_PUBLIC_ID, "variables": {"publicId": "not-a-real-code-at-all"}},
    )
    resp.raise_for_status()
    body = resp.json()
    assert body["data"]["getDataset"] is None, (
        f"an unresolvable publicId unexpectedly resolved to a dataset: {body['data']}"
    )
