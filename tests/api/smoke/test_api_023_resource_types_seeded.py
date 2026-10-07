# tests/api/smoke/test_api_023_resource_types_seeded.py
#
# Covers DataSpaceBackend#223: a data migration (0051_seed_resource_types)
# seeds the ten starting Resource Types on every environment. Before this,
# publishing a publication needed an active Resource Type but dev and prod
# had none (#217) — see the skip reason in tests/api/publications.py's
# `complete_fields` fixture, which this migration unblocks.
#
# Unauthenticated and read-only: `resourceTypes` is a public query, so the
# whole behaviour change is provable here without any test credentials.
#
# `readonly` + `deployed_pr`: confirmed via `git merge-base --is-ancestor
# <merge-sha> origin/main` in DataSpaceBackend that #223 has not reached
# main/prod yet. Gated so it's safe to merge into CI now and switches on by
# itself once prod serves the change.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#223")]

STARTING_RESOURCE_TYPES = {
    "Report", "Article", "Policy Brief", "Research Paper", "Case Study",
    "Guide", "Toolkit", "Presentation", "Fact Sheet", "Working Paper",
}


@pytest.mark.smoke
def test_starting_resource_types_are_seeded_and_active(anon_graphql_client):
    """All ten starting types exist and are active.

    Before #223, `resourceTypes` returned an empty list on dev and prod
    (confirmed live on prod in the PR body — this migration hasn't reached
    main yet). Any type missing or deactivated here means publishing is
    broken again for that type (#217).
    """
    data = anon_graphql_client.query("{ resourceTypes { name isActive } }")
    by_name = {rt["name"]: rt["isActive"] for rt in data["resourceTypes"]}
    missing = STARTING_RESOURCE_TYPES - set(by_name)
    assert not missing, f"missing starting resource types: {sorted(missing)} — got {sorted(by_name)}"
    inactive = {name for name in STARTING_RESOURCE_TYPES if not by_name[name]}
    assert not inactive, f"starting resource types deactivated: {sorted(inactive)}"
