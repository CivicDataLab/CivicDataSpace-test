# tests/api/smoke/test_api_067_org_member_permissions.py
#
# Only an organization's admin may add members, change roles or remove members;
# an editor, a viewer and an outsider are refused, and nothing changes. Accounts
# on dev (see api_056): 4 admin of test_org_4 and editor of test_org_5, 5 admin of
# test_org_5 and viewer of test_org_4, 3 member of neither.
#
# These are write mutations, so every attempt is fenced: the admin adds account 3
# as a viewer only where the test needs a member to aim at, the roster is read back
# through the admin, and teardown restores it (removes account 3, puts a changed
# role back) even when the API let the attempt through.

import os

import pytest

from utils.provider_api import ProviderAPI

pytestmark = [pytest.mark.api, pytest.mark.smoke]

CASES = {  # id -> (caller slot, org, admin slot, action)
    "viewer-adds-a-member": (5, "test_org_4", 4, "add"),
    "editor-adds-a-member": (4, "test_org_5", 5, "add"),
    "outsider-adds-themselves-as-admin": (3, "test_org_4", 4, "add-self-admin"),
    "viewer-makes-a-member-admin": (5, "test_org_4", 4, "assign-other"),
    "viewer-promotes-themselves": (5, "test_org_4", 4, "promote-self"),
    "viewer-removes-a-member": (5, "test_org_4", 4, "remove-other"),
    "editor-removes-a-member": (4, "test_org_5", 5, "remove-other"),
}
ROSTER = "{ userByOrganization { id organizationMemberships { organization { name } role { name } } } }"
ADD = "mutation($i: AddRemoveUserToOrganizationInput!){ addUserToOrganization(input:$i){ success } }"
REMOVE = "mutation($i: AddRemoveUserToOrganizationInput!){ removeUserFromOrganization(input:$i){ success } }"
ASSIGN = "mutation($i: AssignOrganizationRoleInput!){ assignOrganizationRole(input:$i){ success } }"


@pytest.fixture(scope="module")
def accounts():
    if not os.getenv("API_BASE_URL"):
        pytest.skip("API_BASE_URL not set")
    out = {}
    for n in (3, 4, 5):
        email, password = os.getenv(f"TEST_EMAIL_{n}"), os.getenv(f"TEST_PASSWORD_{n}")
        if not (email and password):
            pytest.skip(f"TEST_EMAIL_{n}/TEST_PASSWORD_{n} not set: the member permission cases need accounts 3, 4 and 5")
        out[n] = ProviderAPI(email, password)
    out["ids"] = {n: out[n].gql("{ me { id } }")["data"]["me"]["id"] for n in (3, 4, 5)}
    out["roles"] = {r["name"]: r["id"] for r in out[4].gql("{ roles { id name } }")["data"]["roles"]}
    return out


def _allowed(api, query, variables, org):
    """Whether the API let the mutation through (a refusal is an error or success=false)."""
    body = api.gql(query, variables, org=org)
    if body.get("errors") or not body.get("data"):
        return False
    return bool(next(iter(body["data"].values()))["success"])


@pytest.mark.parametrize("case", CASES)
def test_api_067_only_an_admin_manages_members(accounts, case):
    caller, org_name, admin, action = CASES[case]
    ids, roles = accounts["ids"], accounts["roles"]
    org = accounts[admin].org_slug(org_name)
    accounts[caller]._slugs[org_name] = org

    def roster():
        rows = accounts[admin].gql(ROSTER, org=org)["data"]["userByOrganization"]
        return {r["id"]: sorted(m["role"]["name"] for m in r["organizationMemberships"] if m["organization"]["name"] == org_name)
                for r in rows}

    before = roster()
    if action == "add-self-admin" and ids[3] in before:
        pytest.skip("account 3 is already a member of the org, so adding them proves nothing")
    seeded = action in ("assign-other", "remove-other")
    if seeded:
        assert _allowed(accounts[admin], ADD, {"i": {"userId": ids[3], "roleId": roles["viewer"]}}, org), \
            "the admin could not add the target member"
    expected = roster()
    try:
        if action == "add":
            attempt = (ADD, {"userId": ids[3], "roleId": roles["viewer"]})
        elif action == "add-self-admin":
            attempt = (ADD, {"userId": ids[3], "roleId": roles["admin"]})
        elif action == "assign-other":
            attempt = (ASSIGN, {"userId": ids[3], "roleId": roles["admin"]})
        elif action == "promote-self":
            attempt = (ASSIGN, {"userId": ids[caller], "roleId": roles["admin"]})
        else:
            attempt = (REMOVE, {"userId": ids[3], "roleId": roles["viewer"]})
        allowed = _allowed(accounts[caller], attempt[0], {"i": attempt[1]}, org)
        after = roster()
    finally:
        now = roster()
        if ids[3] in now and ids[3] not in before:
            accounts[admin].gql(REMOVE, {"i": {"userId": ids[3], "roleId": roles["viewer"]}}, org=org)
        if now.get(ids[caller]) != before.get(ids[caller]) and ids[caller] in before and action == "promote-self":
            original = before[ids[caller]][0]
            accounts[admin].gql(ASSIGN, {"i": {"userId": ids[caller], "roleId": roles[original]}}, org=org)
    assert not allowed, f"{case}: the API let a non-admin through"
    assert after == expected, f"{case}: the roster changed even though the call was refused: {after} != {expected}"
    assert roster() == before, f"{case}: the roster was not restored"
