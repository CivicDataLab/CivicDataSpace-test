# tests/api/smoke/test_api_017_publication_access.py
#
# Who may change a publication (DataSpace#243). Accounts on dev, checked
# 2026-10-01 (re-check before trusting; provisioning has drifted before):
#   account 1 - admin of "test org 2", creates everything here
#   account 2 - admin of "test org 2"
#   account 3 - not a member of "test org 2"
#
# Not covered: a read-only role. No test account has the "viewer" role, and
# "auditor" (account 2 on CivicDataLab) has can_change, so it can edit.
# Writes to dev only; drafts are deleted in teardown.

import pytest

from tests.api import publications as pub

pytestmark = [pytest.mark.api, pytest.mark.functional]

ORG = "test org 2"
REFUSED = {
    "update": "You don't have permission to modify this resource",
    "publish": "You don't have permission to publish this resource",
    "delete": "You don't have permission to delete this resource",
}


@pytest.fixture
def creator(graphql_client_for):
    return graphql_client_for(1)


@pytest.fixture
def slug(creator):
    return pub.org_slug(creator, ORG)


@pytest.fixture
def org_draft(creator, slug):
    data = pub.create(creator, org=slug, title=pub.unique_title("access test"))
    yield data
    pub.delete(creator, data["id"], org=slug)


@pytest.fixture
def own_draft(creator):
    data = pub.create(creator, title=pub.unique_title("access test"))
    yield data
    pub.delete(creator, data["id"])


def _attempt(client, op, publication_id, org=None):
    if op == "update":
        return pub.update(client, publication_id, org=org, title="changed by someone else")
    return {"publish": pub.publish, "delete": pub.delete}[op](client, publication_id, org=org)


def test_org_header_makes_an_org_publication(org_draft):
    assert org_draft["isIndividualPublication"] is False, org_draft
    assert org_draft["organization"] == {"name": ORG}, org_draft


def test_org_admin_can_edit_a_colleagues_draft(graphql_client_for, org_draft, slug):
    payload = pub.update(graphql_client_for(2), org_draft["id"], org=slug, title="edited by colleague")
    assert payload["success"], payload["errors"]


@pytest.mark.parametrize("op", ["update", "publish", "delete"])
def test_non_member_is_refused(graphql_client_for, creator, org_draft, slug, op):
    outsider = graphql_client_for(3)
    payload = _attempt(outsider, op, org_draft["id"], org=slug)
    assert pub.errors_of(payload) == {None: [REFUSED[op]]}, payload
    saved = pub.get(creator, org_draft["id"])["data"]["getPublication"]
    assert saved and saved["title"] == org_draft["title"], f"{op} by a non-member changed the draft: {saved}"


@pytest.mark.parametrize("op", ["update", "publish", "delete"])
def test_another_user_cannot_touch_an_individual_draft(graphql_client_for, creator, own_draft, op):
    payload = _attempt(graphql_client_for(3), op, own_draft["id"])
    assert pub.errors_of(payload) == {None: [REFUSED[op]]}, payload
    saved = pub.get(creator, own_draft["id"])["data"]["getPublication"]
    assert saved and saved["title"] == own_draft["title"], f"{op} by another user changed the draft: {saved}"
