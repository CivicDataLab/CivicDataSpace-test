# tests/api/smoke/test_api_053_external_contributors.py
#
# Pending coverage for DataSpaceBackend#224 (open on `dev`, not merged yet):
# a new `ExternalContributor` model wired as M2M onto Publication, UseCase and
# Collaborative, exposed through a new `externalContributors` list field on
# each of their GraphQL types (TypePublication, TypeUseCase, TypeCollaborative).
#
# TypeExternalContributor masks every field but id/hasApproved/timestamps
# until the contributor has approved: name -> "Anonymous", email, designation
# and bio -> null.
#
# `pending_pr`-gated (conftest.py): skips until GitHub reports #224 merged,
# then runs with no follow-up edit. Until then the field does not exist, so
# running it with the gate removed fails at the schema check (red proof).

import pytest

pytestmark = [
    pytest.mark.api,
    pytest.mark.smoke,
    pytest.mark.pending_pr("DataSpaceBackend#224"),
]

SHAPE = "externalContributors { id hasApproved name email designation bio }"


@pytest.mark.parametrize("listing", ["useCases", "collaboratives"])
def test_external_contributors_are_masked_until_approved(anon_graphql_client, listing):
    data = anon_graphql_client.query(
        "{ %s(pagination: {limit: 50}) { id %s } }" % (listing, SHAPE)
    )
    contributors = [c for row in data[listing] for c in row["externalContributors"]]
    pending = [c for c in contributors if not c["hasApproved"]]
    if not pending:
        pytest.skip(f"no unapproved external contributor on the first 50 {listing}")
    for c in pending:
        assert (c["name"], c["email"], c["designation"], c["bio"]) == ("Anonymous", None, None, None), (
            f"unapproved contributor {c['id']} leaks details: {c}"
        )
