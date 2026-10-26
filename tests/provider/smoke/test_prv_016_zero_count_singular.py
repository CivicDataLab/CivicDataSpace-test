# tests/provider/smoke/test_prv_016_zero_count_singular.py
#
# Regression coverage for DataSpaceFrontend#505 (and the #504 refactor that
# introduced the helper #505 fixes).
#
# #504 ("Refactor dataset listing styles and enhance DatasetPage
# functionality") introduced `formatCount()` in
# app/[locale]/dashboard/[entityType]/[entitySlug]/provider-flow/
# table-listing.ts, shared by the provider dashboard's Use Cases,
# Collaboratives and Datasets listing tables to render a related-item count
# ("N dataset(s)", "N use case(s)", "N file(s)"). As merged by #504, it read:
#
#     count === 1 ? singular : plural
#
# so a ZERO count rendered as the PLURAL form -- a use case with no datasets
# showed "0 datasets", a collaborative with no use cases showed "0 use
# cases". #505 ("Enhance dashboard styling and update dataset loading
# functionality") fixes this to:
#
#     count === 0 || count === 1 ? singular : plural
#
# so zero now reads as singular ("0 dataset" / "0 use case"), matching the
# grammar used everywhere else a count label appears in this app.
#
# Only the Use Cases and Collaboratives tables are covered here, reusing
# their existing Page Objects (UseCasesListPage, CollaborativesListPage).
# The Datasets table's "files" column (dataset.resourceCount) uses the same
# formatCount() fix, but there is no provider Datasets-*listing* Page Object
# yet -- pages/provider/dataset_detail_page.py is the published-dataset
# detail page, not the dashboard's Datasets table. That is a real gap, not
# something to paper over with a raw selector in this test; a human should
# add a DatasetsListPage (mirroring UseCasesListPage/CollaborativesListPage)
# and extend this file once one exists.
#
# UNVERIFIED -- not executed, no credentials in this environment (scheduled
# cloud routine run, no TEST_EMAIL_*/TEST_PASSWORD_* available). Collection
# was confirmed locally; the actual browser run, the red run against the
# pre-#505 formatCount, and the green run against dev all still need a human
# with real provider credentials. See the PR body for exact commands.

import os

import pytest
import requests

from pages.provider.collaboratives_list_page import CollaborativesListPage
from pages.provider.usecases_list_page import UseCasesListPage

pytestmark = pytest.mark.smoke


def _graphql(token, query, variables=None, headers=None):
    resp = requests.post(
        f"{os.environ['API_BASE_URL'].rstrip('/')}/api/graphql",
        json={"query": query, "variables": variables or {}},
        headers={"Authorization": f"Bearer {token}", **(headers or {})},
        timeout=60,
    )
    resp.raise_for_status()
    body = resp.json()
    assert "errors" not in body, f"GraphQL errors: {body['errors']}"
    return body["data"]


def _access_token(email, password):
    payload = {
        "grant_type": "password",
        "client_id": os.environ["KEYCLOAK_CLIENT_ID"],
        "username": email,
        "password": password,
    }
    if os.getenv("KEYCLOAK_CLIENT_SECRET"):
        payload["client_secret"] = os.environ["KEYCLOAK_CLIENT_SECRET"]
    resp = requests.post(
        f"{os.environ['KEYCLOAK_URL'].rstrip('/')}/realms/{os.environ['KEYCLOAK_REALM']}"
        "/protocol/openid-connect/token",
        data=payload,
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["access_token"]


def _draft_with_zero_related(token, org_ids, field, filter_type, count_field):
    """First (org name, title) whose DRAFT `field` has `count_field` == 0."""
    query = f"query($f: {filter_type}) {{ {field}(filters: $f) {{ id title {count_field} }} }}"
    for name, org_id in org_ids.items():
        rows = _graphql(token, query, {"f": {"status": "DRAFT"}}, {"organization": org_id})[field]
        for row in rows:
            if row.get(count_field, 0) == 0 and row.get("title"):
                return name, row["title"]
    return None, None


@pytest.mark.timeout(180)
def test_prv_016_usecase_zero_dataset_count_is_singular(
    logged_in_provider, test_credentials, org_add_permission
):
    if not os.getenv("API_BASE_URL"):
        pytest.skip("API_BASE_URL not set -- cannot find a draft use case with zero datasets")

    token = _access_token(*test_credentials)
    org_ids = {
        o["name"]: o["id"]
        for o in _graphql(token, "{ organizations { id name } }")["organizations"]
        if o["name"] in org_add_permission
    }
    org, title = _draft_with_zero_related(token, org_ids, "useCases", "UseCaseFilter", "datasetCount")
    if title is None:
        pytest.skip(
            f"None of {org_add_permission} has a draft use case with zero datasets "
            f"to exercise the #505 zero-count label"
        )

    org_dash = logged_in_provider.goto_organizations()
    org_dash.select_org(org)
    page: UseCasesListPage = org_dash.click_usecases_card()

    label = page.dataset_count_label(title)
    assert label == "0 dataset", (
        f"Use case '{title}' has zero datasets; the 'Datasets' column read '{label}', "
        f"expected singular '0 dataset' (DataSpaceFrontend#505's formatCount fix). "
        f"'0 datasets' means the pre-#505 plural-for-zero behavior is back."
    )


@pytest.mark.timeout(180)
def test_prv_016_collaborative_zero_usecase_count_is_singular(
    logged_in_provider, test_credentials, org_add_permission
):
    if not os.getenv("API_BASE_URL"):
        pytest.skip("API_BASE_URL not set -- cannot find a draft collaborative with zero use cases")

    token = _access_token(*test_credentials)
    org_ids = {
        o["name"]: o["id"]
        for o in _graphql(token, "{ organizations { id name } }")["organizations"]
        if o["name"] in org_add_permission
    }
    org, title = _draft_with_zero_related(token, org_ids, "collaboratives", "CollaborativeFilter", "useCaseCount")
    if title is None:
        pytest.skip(
            f"None of {org_add_permission} has a draft collaborative with zero use cases "
            f"to exercise the #505 zero-count label"
        )

    org_dash = logged_in_provider.goto_organizations()
    org_dash.select_org(org)
    page: CollaborativesListPage = org_dash.click_collaboratives_card()

    label = page.usecase_count_label(title)
    assert label == "0 use case", (
        f"Collaborative '{title}' has zero use cases; the 'Use Cases' column read '{label}', "
        f"expected singular '0 use case' (DataSpaceFrontend#505's formatCount fix)."
    )
