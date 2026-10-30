# tests/api/smoke/test_api_048_unknown_route_not_login.py
#
# An anonymous visitor who mistypes a public URL should get a 404, not be
# bounced to the Keycloak login (consumer issue C-005). Today dev answers
# 307 -> /login?callbackUrl=... for any path the app does not know.
#
# /terms, /contact and /accessibility behave the same way but whether those
# pages should exist is a product decision, so only invented paths are asserted.
#
# The unknown-path test asserts the correct behaviour and is strict xfail: CI
# stays green while the bug exists and goes red (XPASS) once it is fixed, at
# which point the marker has to come off. The control must always pass.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.regression, pytest.mark.readonly]


def test_known_public_page_is_not_redirected(dev_frontend_client):
    """Control: an existing public page answers 200 directly, so the redirect check below is meaningful."""
    resp = dev_frontend_client.get("/privacy", allow_redirects=False)
    assert resp.status_code == 200, f"/privacy -> {resp.status_code} {resp.headers.get('Location', '')}"


@pytest.mark.xfail(
    strict=True,
    reason="consumer issue C-005: unknown paths redirect anonymous visitors to /login",
)
@pytest.mark.parametrize("path", ["/no-such-page-zz", "/no-such-section-zz/no-such-child-zz"])
def test_unknown_path_is_404_not_login_redirect(dev_frontend_client, path):
    """Unknown paths return 404 for an anonymous visitor rather than redirecting to login."""
    resp = dev_frontend_client.get(path, allow_redirects=False)
    assert resp.status_code == 404, (
        f"{path} -> {resp.status_code}, Location: {resp.headers.get('Location', '-')}"
    )
