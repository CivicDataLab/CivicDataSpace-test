# tests/api/smoke/test_api_025_external_contributors.py
#
# Pending coverage for DataSpaceBackend#224 (open on `dev`, not merged yet):
# a new `ExternalContributor` model wired as M2M onto Publication, UseCase and
# Collaborative, exposed through a new `externalContributors` list field on
# each of their GraphQL types (TypePublication, TypeUseCase, TypeCollaborative).
#
# `externalContributors` does not exist on today's schema, so the schema
# itself is the red proof: querying it is a GraphQL "Cannot query field"
# error until #224 merges. This is `pending_pr`-gated (conftest.py) so it
# skips in CI until GitHub reports the PR merged, then runs like any other
# test with no follow-up edit.
#
# The green side (the actual privacy-mask behaviour: an unapproved
# contributor's name/email/designation/bio/image reading as "Anonymous"/null,
# an approved one showing real values) is NOT asserted here. DataSpaceBackend
# cannot be served in this environment (no Postgres/Redis/Keycloak), so that
# behaviour is UNVERIFIED -- see the PR body for what to re-run once #224 is
# on dev.

import pytest

pytestmark = [
    pytest.mark.api,
    pytest.mark.smoke,
    pytest.mark.pending_pr("DataSpaceBackend#224"),
]

EXTERNAL_CONTRIBUTORS_SHAPE = (
    "externalContributors { id hasApproved name email designation bio }"
)


def test_usecases_external_contributors_field_does_not_exist_yet(anon_graphql_client):
    """Today's schema has no `externalContributors` field on TypeUseCase.

    Red proof for DataSpaceBackend#224: an anonymous, unauthenticated query
    asking for the new field must fail with GraphQL's "Cannot query field"
    error, not any other error, and not succeed. Once #224 merges into dev,
    this field exists and the query below is expected to succeed instead --
    at that point this test should be rewritten to assert the privacy mask
    (unapproved -> name "Anonymous", email/designation/bio/image null;
    approved -> real values), which has not been verified anywhere in this
    environment.
    """
    query = (
        "{ useCases(pagination: {limit: 1}) { id title %s } }"
        % EXTERNAL_CONTRIBUTORS_SHAPE
    )
    resp = anon_graphql_client.session.post(
        anon_graphql_client.endpoint, json={"query": query}, timeout=60,
    )
    resp.raise_for_status()
    body = resp.json()

    assert body.get("data") is None, (
        f"Expected no data for an unknown field, got: {body.get('data')}"
    )
    errors = body.get("errors") or []
    assert errors, f"Expected a GraphQL error querying externalContributors, got none: {body}"
    message = errors[0].get("message", "")
    assert "Cannot query field 'externalContributors'" in message, (
        f"Expected a 'Cannot query field externalContributors' error, got: {message!r}"
    )


def test_collaboratives_external_contributors_field_does_not_exist_yet(anon_graphql_client):
    """Same red proof as above, for TypeCollaborative."""
    query = (
        "{ collaboratives(pagination: {limit: 1}) { id title %s } }"
        % EXTERNAL_CONTRIBUTORS_SHAPE
    )
    resp = anon_graphql_client.session.post(
        anon_graphql_client.endpoint, json={"query": query}, timeout=60,
    )
    resp.raise_for_status()
    body = resp.json()

    assert body.get("data") is None, (
        f"Expected no data for an unknown field, got: {body.get('data')}"
    )
    errors = body.get("errors") or []
    assert errors, f"Expected a GraphQL error querying externalContributors, got none: {body}"
    message = errors[0].get("message", "")
    assert "Cannot query field 'externalContributors'" in message, (
        f"Expected a 'Cannot query field externalContributors' error, got: {message!r}"
    )
