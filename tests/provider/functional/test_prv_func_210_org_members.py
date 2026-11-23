# tests/provider/functional/test_prv_func_210_org_members.py
#
# An organization admin adds a member, changes their role and removes them on
# the "Admin & Members" page. This writes to a shared organization, so it is
# fenced in:
#   - it runs in "my test org", which no account uses as its dedicated org, and
#     only when account 1 is its admin;
#   - the member it adds is account 3, who is not a member there, and nobody
#     already on the roster is touched;
#   - the roster is snapshotted first, the spare is removed at teardown whatever
#     happened, and the test fails if the roster differs from the snapshot.

import os

import pytest

from pages.provider.members_page import MembersPage

pytestmark = pytest.mark.functional

ORG = "my test org"
ROSTER = "{ userByOrganization { id email organizationMemberships { role { name } } } }"
ADD = "mutation($i: AddRemoveUserToOrganizationInput!){ addUserToOrganization(input:$i){ success errors { nonFieldErrors } } }"
REMOVE = "mutation($i: AddRemoveUserToOrganizationInput!){ removeUserFromOrganization(input:$i){ success } }"


@pytest.fixture
def team(provider_api, test_credentials):
    """The org's slug, the spare account's identity and the roster before the test; restores the roster after."""
    if test_credentials[0] != os.getenv("TEST_EMAIL_1"):
        pytest.skip("member changes run as account 1, the admin of the test org")
    spare_email, spare_password = os.getenv("TEST_EMAIL_3"), os.getenv("TEST_PASSWORD_3")
    if not (spare_email and spare_password):
        pytest.skip("TEST_EMAIL_3/TEST_PASSWORD_3 not set: no spare account to add as a member")
    from utils.provider_api import ProviderAPI
    spare = ProviderAPI(spare_email, spare_password)
    me = spare.gql("{ me { id email firstName lastName username } }")["data"]["me"]
    slug = provider_api.org_slug(ORG)

    def roster():
        rows = provider_api.gql(ROSTER, org=slug)["data"]["userByOrganization"]
        return {r["email"]: [m["role"]["name"] for m in r["organizationMemberships"]] for r in rows}

    before = roster()
    if spare_email in before or test_credentials[0] not in before:
        pytest.skip(f"{ORG!r} is not in the expected state: the spare is already a member or account 1 is not")
    roles = {r["name"]: r["id"] for r in provider_api.gql("{ roles { id name } }")["data"]["roles"]}
    yield {"me": me, "roster": roster, "before": before, "roles": roles, "slug": slug}
    after = roster()
    if spare_email in after:
        provider_api.gql(REMOVE, {"i": {"userId": me["id"], "roleId": roles["viewer"]}}, org=slug)
    assert roster() == before, f"The roster of {ORG!r} was not restored: {roster()} != {before}"


def _members_page(driver, logged_in_provider, rows):
    logged_in_provider.goto_organizations().select_org(ORG)
    page = MembersPage(driver).open()
    page.wait_for_rows(rows)
    return page


def test_prv_func_210a_add_edit_and_remove_a_member(driver, logged_in_provider, team):
    me, full_name = team["me"], f"{team['me']['firstName']} {team['me']['lastName']}".strip()
    page = _members_page(driver, logged_in_provider, len(team["before"]))

    page.open_add_dialog()
    assert page.dialog_title() == "Add Admin / Member"
    assert not page.is_submit_enabled("Add"), "Add was enabled with no user and no role"
    page.pick_user(me["username"].split("@")[0], full_name)  # the only user whose handle starts like that
    assert not page.is_submit_enabled("Add"), "Add was enabled with no role"
    page.pick_role("Editor")
    assert page.is_submit_enabled("Add"), "Add stayed disabled with a user and a role"
    page.submit("Add")
    assert page.toast_shown("User added successfully"), "No success toast after adding the member"
    rows = page.wait_for_rows(len(team["before"]) + 1)
    assert {r["email"]: r["role"] for r in rows}[me["email"]] == "Editor", f"The new row is wrong: {rows}"
    assert team["roster"]()[me["email"]] == ["editor"], "The backend did not record the editor role"

    page.row_action(me["email"], "Edit")
    assert page.dialog_title() == "Edit Admin / Member"
    page.pick_role("Viewer")
    page.submit("Update")
    assert page.toast_shown("User updated successfully"), "No success toast after changing the role"
    page.driver.refresh()
    rows = page.open().wait_for_rows(len(team["before"]) + 1)
    assert {r["email"]: r["role"] for r in rows}[me["email"]] == "Viewer", f"The role was not changed: {rows}"
    assert team["roster"]()[me["email"]] == ["viewer"], "The backend did not record the viewer role"

    page.row_action(me["email"], "Remove member")
    assert page.alert_title() == "Remove member?"
    page.answer_alert("Cancel")
    assert me["email"] in team["roster"](), "Cancel removed the member"
    page.row_action(me["email"], "Remove member")
    page.answer_alert("Remove member")
    assert page.toast_shown("User removed successfully"), "No success toast after removing the member"
    page.wait_for_rows(len(team["before"]))
    assert team["roster"]() == team["before"], "The roster was not restored by the removal"


def test_prv_func_210b_role_list_leaves_out_owner(driver, logged_in_provider, team):
    """Read-only: the Add dialog offers every role but Owner."""
    page = _members_page(driver, logged_in_provider, len(team["before"]))
    page.open_add_dialog()
    roles = page.role_options()
    assert "Owner" not in roles, f"Owner is offered as a role: {roles}"
    assert {"Admin", "Editor", "Viewer", "Auditor"} <= set(roles), f"A role is missing from {roles}"
