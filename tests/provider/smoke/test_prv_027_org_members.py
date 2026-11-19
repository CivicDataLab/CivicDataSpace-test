# tests/provider/smoke/test_prv_027_org_members.py
#
# The organization's "Admin & Members" page (DataSpaceFrontend#547): every
# member the backend lists is shown with their role in title case, and
# "Remove member" is offered on every row except the signed-in admin's own.
# Before #547 each row, the admin's own included, had a remove button.
#
# Read-only: nothing is clicked beyond opening the page. Members and roles are
# read live from `userByOrganization`, never hardcoded.

import pytest

from pages.provider.members_page import MembersPage

pytestmark = [pytest.mark.smoke]

MEMBERS = "{ userByOrganization { email organizationMemberships { role { name } } } }"


@pytest.fixture
def expected_members(provider_api, writable_org):
    body = provider_api.gql(MEMBERS, org=provider_api.org_slug(writable_org))
    members = (body.get("data") or {}).get("userByOrganization")
    assert members, f"userByOrganization returned no members for {writable_org!r}: {body}"
    return {
        m["email"]: m["organizationMemberships"][0]["role"]["name"].title() for m in members
    }


def test_prv_027_members_page_lists_roles_and_hides_remove_on_own_row(
    driver, logged_in_provider, writable_org, test_credentials, expected_members
):
    """
    Test Case ID: test_prv_027_members_page_lists_roles_and_hides_remove_on_own_row
    Steps:
      1. Open the writable organization's "Admin & Members" page
      2. Compare each row's e-mail and role with userByOrganization
      3. Check the own row has no "Remove member" and every other row has one
    """
    own_email = test_credentials[0]
    assert own_email in expected_members, f"{own_email} is not a member of {writable_org!r}"
    assert len(expected_members) > 1, f"{writable_org!r} has no other member to compare the own row with"

    logged_in_provider.goto_organizations().select_org(writable_org)
    rows = MembersPage(driver).open().wait_for_rows(len(expected_members))

    shown = {r["email"]: r["role"] for r in rows}
    assert shown == expected_members, f"members page (left) differs from the API (right): {shown} != {expected_members}"

    own = [r for r in rows if r["email"] == own_email]
    others = [r for r in rows if r["email"] != own_email]
    assert "Remove member" not in own[0]["actions"], f"own row offers to remove yourself: {own[0]}"
    missing = [r["email"] for r in others if "Remove member" not in r["actions"]]
    assert not missing, f"no 'Remove member' on other members' rows: {missing}"
