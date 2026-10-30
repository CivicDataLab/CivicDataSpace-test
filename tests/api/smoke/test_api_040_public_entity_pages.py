# tests/api/smoke/test_api_040_public_entity_pages.py
#
# Covers the redesigned public dataset and use-case pages (DataSpaceFrontend#512).
# Both pages are client-rendered: the HTML is a shell and everything the visitor
# sees comes from GraphQL. The redesign changed which fields those queries ask
# for (dataset: source, accessType, organization.description/location,
# user.bio/location, resources.noOfEntries; use case: trimmed field set) and
# added three new queries (chart count, published use cases, published
# collaboratives). If the backend drops or renames one of those fields the page
# renders "This dataset could not be loaded" while every API health check stays
# green, so these tests send the same documents the page sends.
#
# `readonly`: anonymous reads only, and the fields are not new on the backend,
# so it is safe in the prod gate too.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.readonly]

DATASET_QUERY = """
query getDataset($datasetId: UUID!) {
  getDataset(datasetId: $datasetId) {
    id title description downloadCount created modified isIndividualDataset
    license formats accessType
    user { fullName id bio location profilePicture { url } }
    tags { id value }
    metadata { metadataItem { id label dataType } value }
    source { sourceHomepage sourceUrl platform }
    resources { id noOfEntries }
    organization { name description location logo { url } slug id }
    sectors { name }
    geographies { name }
  }
}
"""

CHART_COUNT_QUERY = """
query datasetVisualisationCount($datasetId: UUID!) {
  getChartData(datasetId: $datasetId) {
    __typename
    ... on TypeResourceChart { id }
    ... on TypeResourceChartImage { id }
  }
}
"""

USECASE_QUERY = """
query UseCasedetails($pk: ID!) {
  useCase(pk: $pk) {
    id title summary created isIndividualUsecase
    user { fullName id profilePicture { url } }
    organization { name slug id logo { url } }
    sectors { id name }
    geographies { name }
    sdgs { id code name }
    tags { id value }
    logo { path }
    datasets {
      title id isIndividualDataset downloadCount description modified
      user { fullName profilePicture { url } }
      organization { name logo { url } }
      sectors { name }
      geographies { name }
    }
    contributors { id fullName profilePicture { url } }
    supportingOrganizations { id slug name logo { url } }
    partnerOrganizations { id slug name logo { url } }
  }
}
"""


@pytest.fixture(scope="module")
def dataset_id(anon_graphql_client):
    rows = anon_graphql_client.query(
        "{ datasets(includePublic: true, pagination: {limit: 1}) { id } }"
    )["datasets"]
    if not rows:
        pytest.skip("no published dataset on this backend")
    return rows[0]["id"]


@pytest.fixture(scope="module")
def usecase_links(anon_graphql_client):
    """The page's 'used in' lookup: published use cases with their dataset ids."""
    return anon_graphql_client.query(
        "query { publishedUseCases { id slug datasets { id } } }"
    )["publishedUseCases"]


def test_dataset_page_query_resolves_every_field_the_cover_reads(anon_graphql_client, dataset_id):
    """The dataset page's own getDataset document returns the record, not an error."""
    dataset = anon_graphql_client.query(DATASET_QUERY, {"datasetId": dataset_id})["getDataset"]
    assert dataset is not None, f"getDataset returned null for published dataset {dataset_id}"
    assert dataset["id"] == dataset_id, dataset["id"]
    assert dataset["title"], "cover has no title to show"
    for field in ("resources", "tags", "sectors", "geographies", "formats"):
        assert isinstance(dataset[field], list), f"{field} must be a list, got {dataset[field]!r}"
    assert all("noOfEntries" in r for r in dataset["resources"]), dataset["resources"]


def test_dataset_page_side_queries_return_lists(anon_graphql_client, dataset_id, usecase_links):
    """Chart count and the use case / collaborative lookups the summary card needs."""
    charts = anon_graphql_client.query(CHART_COUNT_QUERY, {"datasetId": dataset_id})["getChartData"]
    assert isinstance(charts, list), f"visualisation count needs a list, got {charts!r}"
    assert isinstance(usecase_links, list), usecase_links
    for row in usecase_links:
        assert isinstance(row["datasets"], list), f"use case {row['id']} has no datasets list"
    collabs = anon_graphql_client.query(
        "query { publishedCollaboratives { id slug datasets { id } } }"
    )["publishedCollaboratives"]
    assert isinstance(collabs, list), collabs


def test_usecase_page_query_resolves_for_a_published_use_case(anon_graphql_client, usecase_links):
    """The trimmed use-case document still resolves, with datasets for the related list."""
    if not usecase_links:
        pytest.skip("no published use case on this backend")
    pk = next((u["id"] for u in usecase_links if u["datasets"]), usecase_links[0]["id"])
    usecase = anon_graphql_client.query(USECASE_QUERY, {"pk": pk})["useCase"]
    assert usecase is not None, f"useCase returned null for published use case {pk}"
    assert usecase["title"], "use case page has no title to show"
    assert isinstance(usecase["datasets"], list), usecase["datasets"]


def test_dataset_and_usecase_pages_are_served(dev_frontend_client, dataset_id, usecase_links):
    """Both public routes answer 200 (the route resolves; content is client-rendered)."""
    resp = dev_frontend_client.get(f"/datasets/{dataset_id}")
    assert resp.status_code == 200, f"/datasets/{dataset_id} -> {resp.status_code}"
    if usecase_links:
        uid = usecase_links[0]["id"]
        resp = dev_frontend_client.get(f"/usecases/{uid}")
        assert resp.status_code == 200, f"/usecases/{uid} -> {resp.status_code}"
