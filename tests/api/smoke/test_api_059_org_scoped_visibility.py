# tests/api/smoke/test_api_059_org_scoped_visibility.py
#
# Covers DataSpaceBackend#307: an anonymous caller who sends an
# `organization` header must not see that organisation's AI models or
# collaboratives beyond what is public. Security context: GHSA-22r8-2cfx-mx8m.
# deployed_pr keeps it out of the prod gate until #307 reaches main.
#
# Read-only, anonymous. No mutation, no auth token.

import pytest


def _org_with_public_records(anon_graphql_client, query, list_key):
    """An org slug that owns at least one record visible with NO organization
    header, picked at runtime so this doesn't hardcode admin-managed data."""
    data = anon_graphql_client.query(query)
    for record in data[list_key]:
        org = record.get("organization")
        if org and org.get("slug"):
            return org["slug"], record
    return None, None


@pytest.fixture(scope="module")
def org_with_public_ai_model(anon_graphql_client):
    slug, _ = _org_with_public_records(
        anon_graphql_client,
        "{ aiModels { id organization { slug } } }",
        "aiModels",
    )
    if not slug:
        pytest.skip("No AI model with a public organization on this environment")
    return slug


@pytest.fixture(scope="module")
def org_with_public_collaborative(anon_graphql_client):
    slug, _ = _org_with_public_records(
        anon_graphql_client,
        "{ collaboratives { id organization { slug } } }",
        "collaboratives",
    )
    if not slug:
        pytest.skip("No collaborative with a public organization on this environment")
    return slug


def _anon_client_as_org(api_base_url, org_slug):
    """A fresh, unauthenticated GraphQLClient scoped to one org header.

    Deliberately not reusing the session-scoped `anon_graphql_client` fixture
    for this: that instance is shared by the whole test session, and setting
    a header on it would leak the `organization` header into every other
    test that runs after this one in the same worker.
    """
    from tests.api.client import GraphQLClient

    client = GraphQLClient(api_base_url)
    client.session.headers["organization"] = org_slug
    return client


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#307")
def test_anonymous_with_org_header_cannot_list_ai_models(
    api_base_url, anon_graphql_client, org_with_public_ai_model
):
    org_slug = org_with_public_ai_model
    scoped = _anon_client_as_org(api_base_url, org_slug)

    scoped_result = scoped.query("{ aiModels { id } }")
    assert scoped_result["aiModels"] == [], (
        f"anonymous caller + organization: {org_slug!r} header listed "
        f"{len(scoped_result['aiModels'])} AI model(s) without membership: "
        f"{scoped_result['aiModels']}"
    )

    # Sanity check the org slug is real and actually has models, so an empty
    # result above can't be mistaken for "this org has nothing anyway".
    unscoped_result = anon_graphql_client.query(
        "{ aiModels { id organization { slug } } }"
    )
    public_count = sum(
        1
        for m in unscoped_result["aiModels"]
        if (m.get("organization") or {}).get("slug") == org_slug
    )
    assert public_count > 0, (
        f"expected org {org_slug!r} to have at least one publicly-listed "
        f"AI model with no organization header; found {public_count}"
    )


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceBackend#307")
def test_anonymous_with_org_header_cannot_list_collaboratives(
    api_base_url, anon_graphql_client, org_with_public_collaborative
):
    org_slug = org_with_public_collaborative
    scoped = _anon_client_as_org(api_base_url, org_slug)

    scoped_result = scoped.query("{ collaboratives { id } }")
    assert scoped_result["collaboratives"] == [], (
        f"anonymous caller + organization: {org_slug!r} header listed "
        f"{len(scoped_result['collaboratives'])} collaborative(s) without "
        f"membership: {scoped_result['collaboratives']}"
    )

    unscoped_result = anon_graphql_client.query(
        "{ collaboratives { id organization { slug } } }"
    )
    public_count = sum(
        1
        for c in unscoped_result["collaboratives"]
        if (c.get("organization") or {}).get("slug") == org_slug
    )
    assert public_count > 0, (
        f"expected org {org_slug!r} to have at least one publicly-listed "
        f"collaborative with no organization header; found {public_count}"
    )
