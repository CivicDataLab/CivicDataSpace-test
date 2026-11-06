# tests/provider/smoke/test_prv_017_change_password_signed_in.py
#
# Signed-in branch of `GET /api/auth/change-password` (DataSpaceFrontend#506).
# The profile page's "Change password" button fetches this route and follows
# the `url` it returns. With a valid NextAuth session that must be Keycloak's
# account security page; only a signed-out caller gets `/login`. The
# signed-out branch is test_api_032.
#
# The NextAuth session cookie is encrypted with the frontend's secret, so it
# can't be minted from a Keycloak token: log in through the browser, then send
# the browser's cookies with a plain request.

import os

import pytest
import requests

pytestmark = pytest.mark.smoke


def test_prv_017_change_password_signed_in(logged_in_provider, driver, base_url):
    issuer = f"{os.environ['KEYCLOAK_URL'].rstrip('/')}/realms/{os.environ['KEYCLOAK_REALM']}"
    cookies = {c["name"]: c["value"] for c in driver.get_cookies()}

    resp = requests.get(
        f"{base_url.rstrip('/')}/api/auth/change-password", cookies=cookies, timeout=30
    )

    assert resp.status_code == 200, f"unexpected status {resp.status_code}: {resp.text[:300]}"
    assert resp.json().get("url") == f"{issuer}/account/account-security/signing-in", resp.json()
