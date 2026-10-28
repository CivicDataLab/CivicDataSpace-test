# tests/api/smoke/test_api_032_change_password_redirect.py
#
# Covers the new `GET /api/auth/change-password` route (DataSpaceFrontend#506):
# it tells the profile page's "Change password" link where to send the
# caller -- the account's Keycloak security page when there is a valid
# session, else the login page. Before this route existed, a GET to this
# path fell through to NextAuth's own catch-all handler, which rejects GET
# entirely (400 "This action with HTTP GET is not supported by NextAuth.js").
#
# The rest of #506 (OrgProfile/UserProfile/ProfileLayout rework) is behind
# provider/org login and isn't exercised here -- see the PR body.
#
# `readonly`: GET-only, asserts nothing writes. `deployed_pr` with
# site="HOME_URL_DEV" follows the same pattern as test_api_027_dev_noindex.py:
# in the prod gate (the main-branch deploys), the caller rebinds the
# HOME_URL_DEV secret to the prod frontend, so this still checks whatever
# host dev_frontend_client actually reaches, and self-skips there until
# #506's merge commit is on prod.

import pytest

pytestmark = [
    pytest.mark.api,
    pytest.mark.smoke,
    pytest.mark.readonly,
    pytest.mark.deployed_pr("DataSpaceFrontend#506", site="HOME_URL_DEV"),
]


def test_signed_out_redirects_to_login(dev_frontend_client, frontend_base_url_dev):
    """No session: the route points at /login, not at Keycloak.

    Before #506, GET here never reached application code at all (NextAuth's
    catch-all rejects GET with a 400), so this also proves the route itself
    exists.
    """
    resp = dev_frontend_client.get("/api/auth/change-password")
    assert resp.status_code == 200, f"unexpected status {resp.status_code}: {resp.text}"
    body = resp.json()
    assert body.get("url") == f"{frontend_base_url_dev}/login", body
