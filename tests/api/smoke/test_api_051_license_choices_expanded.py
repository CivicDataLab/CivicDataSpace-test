# tests/api/smoke/test_api_051_license_choices_expanded.py
#
# Covers DataSpaceBackend#269 (merge commit, migration 0056_update_license_choices):
# Dataset.license / Publication.license gained 55 new Creative-Commons-family
# choices (CC_PDM_1_0 through PDDL_1_0), on top of the original 5. Both model
# fields share the same `DatasetLicense` GraphQL enum, so one introspection
# query covers both.
#
# Unauthenticated and read-only: GraphQL schema introspection (`__type`) is a
# public query, no credentials needed, no mutation performed.
#
# `readonly` + `deployed_pr`: confirmed via `git merge-base --is-ancestor
# <merge-sha> origin/main` in DataSpaceBackend that #269 has not reached
# main/prod yet (prod's /api/graphql still reports only the original 5
# values - checked live, see PR body). Gated so this is safe to merge into
# CI now and turns itself on once prod serves the change.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#269")]

# A representative sample, not the full 55 - enough to prove the expansion
# happened and wasn't, say, a handful of typo'd additions. Chosen to span the
# whole migration: the first and last entries added, plus one with a
# version+jurisdiction suffix (the shape the frontend's new formatter
# (DataSpaceFrontend#513) has to get right) and one short public-domain code.
NEW_LICENSE_CHOICES = {
    "CC_PDM_1_0",
    "CC_BY_NC_SA_3_0_DE",
    "CC0_1_0",
    "PDDL_1_0",
}

# The five that existed before #269 - must still be there; the migration
# only adds `choices`, it must never drop one a dataset could already hold.
ORIGINAL_LICENSE_CHOICES = {
    "GOVERNMENT_OPEN_DATA_LICENSE",
    "CC_BY_4_0_ATTRIBUTION",
    "CC_BY_SA_4_0_ATTRIBUTION_SHARE_ALIKE",
    "OPEN_DATA_COMMONS_BY_ATTRIBUTION",
    "OPEN_DATABASE_LICENSE",
}


@pytest.mark.smoke
def test_dataset_license_enum_includes_new_cc_choices(anon_graphql_client):
    """The `DatasetLicense` enum (shared by Dataset.license and
    Publication.license) must include the new choices added in #269, and
    must keep the five pre-existing ones.

    Confirmed live: on prod (pre-#269, still main's commit) the identical
    query returns exactly the 5 original values and none of
    NEW_LICENSE_CHOICES - a real red. See PR body for the pasted run.
    """
    data = anon_graphql_client.query(
        '{ __type(name: "DatasetLicense") { enumValues { name } } }'
    )
    enum_type = data["__type"]
    assert enum_type is not None, "DatasetLicense enum type not found in the schema"
    names = {v["name"] for v in enum_type["enumValues"]}

    missing_new = NEW_LICENSE_CHOICES - names
    assert not missing_new, (
        f"DatasetLicense is missing choices added by #269: {sorted(missing_new)} "
        f"- got {len(names)} total values"
    )
    missing_original = ORIGINAL_LICENSE_CHOICES - names
    assert not missing_original, (
        f"DatasetLicense dropped pre-existing choices: {sorted(missing_original)}"
    )
    # Must genuinely be a bigger enum, not just the 5 originals re-reported -
    # a `<=` or an exact-set check on NEW_LICENSE_CHOICES alone would pass
    # even if the migration had only added a couple of the 55 by accident.
    assert len(names) >= len(ORIGINAL_LICENSE_CHOICES) + 50, (
        f"expected at least 50 new choices beyond the original "
        f"{len(ORIGINAL_LICENSE_CHOICES)}, got {len(names)} total"
    )
