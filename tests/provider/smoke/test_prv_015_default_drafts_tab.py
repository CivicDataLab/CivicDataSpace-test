# tests/provider/smoke/test_prv_015_default_drafts_tab.py
#
# Regression coverage for DataSpaceFrontend#471.
#
# The Use Cases and Collaboratives dashboard lists read their drafts/published
# tab from `?tab=`. With no `?tab` in the URL the tab started as null, and the
# empty-list branch only shows the "Add New ..." button when the tab is
# 'drafts'. An org with no drafts therefore showed "No Published ... yet." and
# no create button, so the create flow could not start (this is how
# test_prv_011 kept timing out). #471 makes 'drafts' the default.
#
# The bug only shows on an EMPTY drafts list, so the org is picked at runtime:
# one of this account's writable orgs with zero drafts of that kind. If none has
# zero, the test skips. It never creates anything to force the empty state.
#
# The Datasets list is not covered: its empty state shows the create button on
# either tab, so #471 did not change what it renders.

import os

import pytest
import requests

from pages.provider.collaboratives_list_page import CollaborativesListPage
from pages.provider.usecases_list_page import UseCasesListPage

pytestmark = pytest.mark.smoke

KINDS = {
    # URL segment: (GraphQL list field, filter type, list page object)
    "usecases": ("useCases", "UseCaseFilter", UseCasesListPage),
    "collaboratives": ("collaboratives", "CollaborativeFilter", CollaborativesListPage),
}


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


def _org_with_no_drafts(kind, test_credentials, org_add_permission):
    """Name of a writable org whose `kind` drafts list is empty, else None."""
    field, filter_type, _ = KINDS[kind]
    token = _access_token(*test_credentials)
    ids = {o["name"]: o["id"] for o in _graphql(token, "{ organizations { id name } }")["organizations"]}
    query = f"query($f: {filter_type}) {{ {field}(filters: $f) {{ id }} }}"
    for name in org_add_permission:
        if name not in ids:
            continue
        drafts = _graphql(token, query, {"f": {"status": "DRAFT"}}, {"organization": ids[name]})[field]
        if not drafts:
            return name
    return None


@pytest.mark.timeout(240)
@pytest.mark.parametrize("kind", list(KINDS))
def test_prv_015_empty_drafts_list_shows_create_button(
    kind, logged_in_provider, test_credentials, org_add_permission
):
    if not os.getenv("API_BASE_URL"):
        pytest.skip("API_BASE_URL not set -- cannot find an org with an empty drafts list")
    org = _org_with_no_drafts(kind, test_credentials, org_add_permission)
    if org is None:
        pytest.skip(
            f"None of {org_add_permission} has zero {kind} drafts, so the empty-list "
            f"path #471 fixed cannot be reached with this account's data"
        )

    org_dash = logged_in_provider.goto_organizations()
    org_dash.select_org(org)
    driver = org_dash.driver
    # select_org lands on /dashboard/organization/<slug>/dataset. Swap the last
    # segment and load it WITHOUT ?tab, which is where the null tab came from.
    base = driver.current_url.split("?")[0].rsplit("/", 1)[0]
    url = f"{base}/{kind}"
    driver.get(url)

    page = KINDS[kind][2](driver)
    state = page.view_state()
    if state == "rows":
        pytest.skip(f"{org} gained a {kind} draft during the test (a concurrent create flow)")

    assert state == "drafts_empty", (
        f"{url} (no ?tab) showed the '{state}' state for {org}'s empty {kind} drafts list; "
        f"expected the Drafts empty state with its 'Add New' button. "
        f"'published_empty' means the tab did not default to drafts (DataSpaceFrontend#471)."
    )
