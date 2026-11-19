# tests/api/smoke/test_api_050_resource_permission_checks.py
#
# Pending coverage for DataSpaceBackend#267 (head fix/resource-permissions,
# open on dev since 2026-10-29, not yet merged): resources, charts, chart
# images and access models get no permission check of their own today --
# they belong to a dataset, but a resolver like `resourceById` or the global
# `resources` query never asks whether the caller may see that dataset.
# #267 closes that by routing every one of those reads through
# `can_view_dataset` (api/utils/dataset_access.py), the same any-grant rule
# `getDataset` already enforces for the dataset itself.
#
# Until #267 merges, dev still runs the old resolvers, so this is a live
# anonymous-caller gap today, not a hypothetical: anon can read `resources`,
# `datasetResources` and `resourceById` straight through for a dataset that
# `getDataset` itself already refuses to anon with "You need to be
# authenticated to access non-published datasets".
#
# `pending_pr`: skipped until GitHub reports DataSpaceBackend#267 merged.
# Never `readonly` -- see pr-test-sync SKILL.md §9 ("the gate opens on merge
# to dev, but prod-deploy gates run readonly, and the fix won't be on prod
# for a while after that merge").
#
# Discovery gap (see the PR body): the only way to find a *non-published*
# dataset's resource without credentials is to read it off the very query
# this PR locks down (the global, unfiltered `resources` list), cross-checked
# against `getDataset`'s existing, unrelated permission check. Once #267
# ships, `resources` stops leaking those rows to anon, so this discovery will
# likely find nothing any more -- the `pytest.skip` below firing from then on
# is the fix working, not a broken test. Durable coverage past that point
# needs an authenticated fixture that creates its own throwaway draft
# dataset+resource, which this cloud routine has no credentials to add.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.regression, pytest.mark.pending_pr("DataSpaceBackend#267")]

DATASET_RESOURCES = """
query ($datasetId: UUID!) {
  datasetResources(datasetId: $datasetId) { id name }
}
"""

RESOURCE_BY_ID = """
query ($resourceId: UUID!) {
  resourceById(resourceId: $resourceId) { id name }
}
"""

GET_DATASET = """
query ($datasetId: UUID!) {
  getDataset(datasetId: $datasetId) { id status }
}
"""


def _raw(client, query, variables):
    """POST without client.query()'s "no GraphQL errors" assertion.

    getDataset, and resourceById once #267 ships, both answer a hidden
    object with a top-level GraphQL error rather than null data. The
    discovery fixture and test_resource_by_id need the raw body to read
    `errors` instead of having GraphQLClient.query() raise on it.
    """
    response = client.session.post(client.endpoint, json={"query": query, "variables": variables})
    response.raise_for_status()
    return response.json()


@pytest.fixture(scope="module")
def hidden_resource(anon_graphql_client):
    """A resource whose dataset `getDataset` already refuses to anon.

    Scans the global, unfiltered `resources` query (today's gap) for a
    dataset `getDataset` (an unrelated, pre-existing check) says anon may
    not see, and returns the first one that has at least one resource.
    """
    data = anon_graphql_client.query("{ resources { id name dataset { pk } } }")
    checked = set()
    for row in data["resources"]:
        pk = row["dataset"]["pk"]
        if pk in checked:
            continue
        checked.add(pk)
        body = _raw(anon_graphql_client, GET_DATASET, {"datasetId": pk})
        errors = body.get("errors") or []
        if errors and "authenticated" in errors[0]["message"]:
            return {"dataset_id": pk, "resource_id": row["id"], "resource_name": row["name"]}
        if len(checked) >= 60:
            break
    pytest.skip(
        "could not find a non-published dataset exposed via the anonymous "
        "`resources` query on dev right now -- either dev currently has none "
        "with resources, or DataSpaceBackend#267's fix is already effectively "
        "live. See the PR body for the authenticated alternative this needs "
        "for durable coverage once that is the normal case."
    )


@pytest.mark.smoke
def test_dataset_resources_hides_a_nonpublished_dataset(anon_graphql_client, hidden_resource):
    """datasetResources(datasetId: <non-published dataset>) must return nothing to anon.

    Today it returns the dataset's resources outright -- #267 adds the
    `can_view_dataset` filter this asserts.
    """
    data = anon_graphql_client.query(DATASET_RESOURCES, {"datasetId": hidden_resource["dataset_id"]})
    assert data["datasetResources"] == [], (
        f"anon should not see resources of a non-published dataset via "
        f"datasetResources, got: {data['datasetResources']}"
    )


@pytest.mark.smoke
def test_resource_by_id_hides_a_nonpublished_dataset(anon_graphql_client, hidden_resource):
    """resourceById(resourceId: <resource of a non-published dataset>) must refuse anon.

    Today it returns the resource (name, dataset pk, ...) with no error at
    all. #267 makes a hidden resource answer the same as a missing one: a
    GraphQL error, not null data.
    """
    body = _raw(anon_graphql_client, RESOURCE_BY_ID, {"resourceId": hidden_resource["resource_id"]})
    assert body.get("errors"), (
        f"anon should get a GraphQL error fetching {hidden_resource['resource_name']!r} "
        f"(id {hidden_resource['resource_id']}) by id, since its dataset is non-published; "
        f"got: {body}"
    )
