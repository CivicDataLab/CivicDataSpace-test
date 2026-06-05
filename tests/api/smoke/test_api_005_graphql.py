# tests/api/smoke/test_api_005_graphql.py
#
# Smoke tests for the Strawberry GraphQL endpoint (/api/graphql).
# Covers basic queries for datasets, usecases, and organizations.
#
# Note: Strawberry converts Python snake_case field names to camelCase in the schema.
#   Python: use_cases  →  GQL: useCases
#   Python: all_organizations  →  GQL: allOrganizations

import pytest


# ─── Introspection ──────────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.smoke
def test_graphql_introspection(graphql_client):
    """GraphQL introspection should succeed and return type information."""
    data = graphql_client.query("{ __typename }")
    assert "__typename" in data or data is not None


# ─── Dataset queries ─────────────────────────────────────────────────────────────

DATASETS_QUERY = """
query {
  datasets {
    id
    title
    status
    datasetType
    created
    modified
  }
}
"""

@pytest.mark.api
@pytest.mark.smoke
def test_graphql_datasets_query_returns_list(graphql_client):
    """datasets query should return a list (possibly empty)."""
    data = graphql_client.query(DATASETS_QUERY)
    assert "datasets" in data, f"Expected 'datasets' in response, got: {data}"
    assert isinstance(data["datasets"], list), (
        f"Expected datasets to be a list, got: {type(data['datasets'])}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_graphql_datasets_items_have_required_fields(graphql_client):
    """Each dataset item must have id, title, and status fields."""
    data = graphql_client.query(DATASETS_QUERY)
    datasets = data.get("datasets", [])
    if not datasets:
        pytest.skip("No datasets in the system — skipping field validation")
    first = datasets[0]
    assert "id" in first, f"Dataset missing 'id': {first}"
    assert "title" in first, f"Dataset missing 'title': {first}"
    assert "status" in first, f"Dataset missing 'status': {first}"


# ─── UseCase queries ──────────────────────────────────────────────────────────────

USE_CASES_QUERY = """
query {
  useCases {
    id
    title
    status
  }
}
"""

@pytest.mark.api
@pytest.mark.smoke
def test_graphql_usecases_query_returns_list(graphql_client):
    """useCases query should return a list (possibly empty)."""
    data = graphql_client.query(USE_CASES_QUERY)
    assert "useCases" in data, f"Expected 'useCases' in response, got: {data}"
    assert isinstance(data["useCases"], list), (
        f"Expected useCases to be a list, got: {type(data['useCases'])}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_graphql_usecases_items_have_required_fields(graphql_client):
    """Each use case must have id, title, and status fields."""
    data = graphql_client.query(USE_CASES_QUERY)
    use_cases = data.get("useCases", [])
    if not use_cases:
        pytest.skip("No use cases in the system — skipping field validation")
    first = use_cases[0]
    assert "id" in first, f"UseCase missing 'id': {first}"
    assert "title" in first, f"UseCase missing 'title': {first}"
    assert "status" in first, f"UseCase missing 'status': {first}"


# ─── Organization queries ─────────────────────────────────────────────────────────

ALL_ORGANIZATIONS_QUERY = """
query {
  allOrganizations {
    id
    name
    slug
  }
}
"""

@pytest.mark.api
@pytest.mark.smoke
def test_graphql_all_organizations_query_returns_list(graphql_client):
    """allOrganizations query should return a list (possibly empty)."""
    data = graphql_client.query(ALL_ORGANIZATIONS_QUERY)
    assert "allOrganizations" in data, (
        f"Expected 'allOrganizations' in response, got: {data}"
    )
    assert isinstance(data["allOrganizations"], list), (
        f"Expected allOrganizations to be a list, got: {type(data['allOrganizations'])}"
    )


@pytest.mark.api
@pytest.mark.smoke
def test_graphql_organizations_items_have_required_fields(graphql_client):
    """Each organization must have id, name, and slug fields."""
    data = graphql_client.query(ALL_ORGANIZATIONS_QUERY)
    orgs = data.get("allOrganizations", [])
    if not orgs:
        pytest.skip("No organizations in the system — skipping field validation")
    first = orgs[0]
    assert "id" in first, f"Organization missing 'id': {first}"
    assert "name" in first, f"Organization missing 'name': {first}"
    assert "slug" in first, f"Organization missing 'slug': {first}"


# ─── Published use cases (public query) ──────────────────────────────────────────

PUBLISHED_USE_CASES_QUERY = """
query {
  publishedUseCases {
    id
    title
    status
  }
}
"""

@pytest.mark.api
@pytest.mark.smoke
def test_graphql_published_usecases_query(graphql_client):
    """publishedUseCases query should return a list of published use cases."""
    data = graphql_client.query(PUBLISHED_USE_CASES_QUERY)
    assert "publishedUseCases" in data, (
        f"Expected 'publishedUseCases' in response, got: {data}"
    )
    assert isinstance(data["publishedUseCases"], list)
