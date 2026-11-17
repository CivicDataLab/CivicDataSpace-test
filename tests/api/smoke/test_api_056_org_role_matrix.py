# tests/api/smoke/test_api_056_org_role_matrix.py
#
# Organisation roles, enforced by the API, for every kind of draft. Accounts on dev (set up 2026-11-17,
# re-check with userPermissions before trusting):
#   account 4 - admin of test_org_4, editor of test_org_5
#   account 5 - admin of test_org_5, viewer of test_org_4
#   account 3 - member of neither
#
# Roles as seeded (authorization/management/commands/init_roles.py):
#   editor: view, add, change; no delete.  viewer: view only.
# Each case states the correct behaviour. Writes go to dev test orgs only and
# every draft is deleted at teardown by the org's admin.

import os
import uuid

import pytest

from utils.provider_api import ProviderAPI

pytestmark = [pytest.mark.api, pytest.mark.smoke]

# role -> (caller slot, org, admin slot of that org)
ROLES = {
    "viewer": (5, "test_org_4", 4),
    "editor": (4, "test_org_5", 5),
    "outsider": (3, "test_org_4", 4),
}
EXPECT = {  # what each role may do with an org's drafts
    "viewer": {"create": False, "update": False, "delete": False, "list": True},
    "editor": {"create": True, "update": True, "delete": False, "list": True},
    "outsider": {"create": False, "update": False, "delete": False, "list": False},
}
UPDATE = {
    "dataset": ("mutation($i: UpdateDatasetInput!){ updateDataset(updateDatasetInput:$i){ __typename } }",
                lambda rid, title: {"i": {"dataset": rid, "title": title}}),
    "usecase": ("mutation($i: UseCaseInputPartial!){ updateUseCase(data:$i){ id } }",
                lambda rid, title: {"i": {"id": rid, "title": title}}),
    "collaborative": ("mutation($i: CollaborativeInputPartial!){ updateCollaborative(data:$i){ id } }",
                      lambda rid, title: {"i": {"id": rid, "title": title}}),
    "aimodel": ("mutation($i: UpdateAIModelInput!){ updateAiModel(input:$i){ success } }",
                lambda rid, title: {"i": {"id": int(rid), "displayName": title}}),
    "publication": ("mutation($i: UpdatePublicationInput!){ updatePublication(input:$i){ success } }",
                    lambda rid, title: {"i": {"id": rid, "title": title}}),
}
# Known product defects, tracked privately by the backend team.
BROKEN = {(k, "viewer", a) for k in ("usecase", "collaborative") for a in ("update", "delete")} | {
    (k, "outsider", a) for k in ("usecase", "collaborative") for a in ("update", "delete")} | {
    (k, "editor", "delete") for k in ("usecase", "collaborative")}


def _cases():
    for kind in UPDATE:
        for role in ROLES:
            for action in ("create", "update", "delete", "list"):
                marks = [pytest.mark.xfail(strict=True, reason="known product defect, tracked by the backend team")] \
                    if (kind, role, action) in BROKEN else []
                yield pytest.param(kind, role, action, id=f"{kind}-{role}-{action}", marks=marks)


@pytest.fixture(scope="module")
def accounts():
    if not os.getenv("API_BASE_URL"):
        pytest.skip("API_BASE_URL not set")
    out = {}
    for n in {slot for role in ROLES.values() for slot in (role[0], role[2])}:
        email, password = os.getenv(f"TEST_EMAIL_{n}"), os.getenv(f"TEST_PASSWORD_{n}")
        if not (email and password):
            pytest.skip(f"TEST_EMAIL_{n}/TEST_PASSWORD_{n} not set: the role matrix needs accounts 3, 4 and 5")
        out[n] = ProviderAPI(email, password)
    for caller, org, admin in ROLES.values():
        out[caller]._slugs[org] = out[admin].org_slug(org)  # an outsider cannot look the slug up itself
    return out


def _unique():
    return f"zz-auto-role-{uuid.uuid4().hex[:8]}"


@pytest.mark.parametrize("kind,role,action", _cases())
def test_api_056_org_role_matrix(accounts, kind, role, action):
    """
    Test Case ID: test_api_056_org_role_matrix
    A caller can do to an organisation's drafts exactly what its role allows.
    Steps:
      1. The org's admin creates a draft
      2. The caller tries `action` on it (or creates its own, for `create`)
      3. Read the result back as the admin
    """
    slot, org, admin_slot = ROLES[role]
    caller, admin = accounts[slot], accounts[admin_slot]
    made = [admin.create_draft(kind, _unique(), org)]
    try:
        if action == "create":
            try:
                made.append(caller.create_draft(kind, _unique(), org))
                allowed = True
            except AssertionError:
                allowed = False
        elif action == "update":
            renamed = _unique()
            query, variables = UPDATE[kind]
            caller.gql(query, variables(made[0], renamed), caller._owner(org))
            rows = admin.listing(kind, org)["data"]
            allowed = any(str(r["id"]) == made[0] and (r.get("title") or r.get("displayName")) == renamed for r in rows)
        elif action == "delete":
            allowed = caller.delete(kind, made[0], org) is None
        else:
            allowed = made[0] in {str(r["id"]) for r in caller.listing(kind, org)["data"]}
    finally:
        for rid in made:
            admin.delete(kind, rid, org)

    expected = EXPECT[role][action]
    assert allowed == expected, (
        f"{role} {'could not' if expected else 'could'} {action} a {kind} draft in {org}")
