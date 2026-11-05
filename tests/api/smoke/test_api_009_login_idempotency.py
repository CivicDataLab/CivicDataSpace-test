# tests/api/smoke/test_api_009_login_idempotency.py
#
# Regression coverage for DataSpaceBackend#136, which stopped rewriting the
# user row on every login.
#
# Before that change, every authenticated request called an unconditional
# user.save(). #136 replaced it with a diff-then-write: build the desired field
# set, compare against the loaded row, and save(update_fields=changed) only
# when something actually differs.
#
# The failure mode that introduces is silent. If the comparison is wrong, a
# login either stops propagating real Keycloak changes, or starts returning an
# identity that does not match what a subsequent read reports. Neither shows up
# in the existing auth tests (test_api_002_auth.py), which log in exactly once
# and only check response shape.
#
# Marked `smoke` deliberately, not just `api`/`regression`: run-smoke.yml
# selects `-m "smoke"` on pull_request and `-m "smoke or functional"` on
# dispatch, so a regression-only test is never executed by CI on any event.

import pytest
import requests

from tests.api.conftest import _get_keycloak_token

pytestmark = pytest.mark.readonly


def _login(api_base_url, keycloak_config, email, password):
    """Exchange a fresh Keycloak token for a Django JWT, return the response body."""
    # client_secret is required: the realm's client is confidential, and
    # omitting it makes the ROPC request 401, which _get_keycloak_token turns
    # into a silent skip rather than a failure.
    kc_token = _get_keycloak_token(
        keycloak_config["url"],
        keycloak_config["realm"],
        keycloak_config["client_id"],
        email,
        password,
        client_secret=keycloak_config.get("client_secret"),
    )
    resp = requests.post(
        f"{api_base_url}/api/auth/keycloak/login/",
        json={"token": kc_token},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"Keycloak login failed ({resp.status_code}): {resp.text}"
    )
    return resp.json()


@pytest.fixture(scope="module")
def two_logins(api_base_url, keycloak_config, test_credentials):
    """Log in twice and hand both responses to every test in this module.

    Shared rather than per-test on purpose. The bug behind #136 was login
    itself exhausting the connection pool, so this suite should not add four
    logins per CI run to a shared dev backend when two prove the same thing.
    """
    email, password = test_credentials
    first = _login(api_base_url, keycloak_config, email, password)
    second = _login(api_base_url, keycloak_config, email, password)
    return first, second


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.regression
def test_repeated_login_returns_stable_identity(two_logins):
    """Logging in twice must return the same user row, not a second one.

    This is the direct regression guard for #136's conditional write. The
    second login takes the no-op path (nothing changed since the first), which
    is precisely the path that did not exist before the fix.
    """
    first, second = two_logins

    assert first["user"]["id"] == second["user"]["id"], (
        "Repeated login returned a different user id "
        f"({first['user']['id']} then {second['user']['id']}) — the login path "
        "is creating or resolving to a different row on the second call"
    )
    assert first["user"]["email"] == second["user"]["email"], (
        "Repeated login returned a different email "
        f"({first['user']['email']!r} then {second['user']['email']!r})"
    )


@pytest.mark.api
@pytest.mark.smoke
@pytest.mark.regression
def test_login_identity_matches_user_info_after_no_op_write(
    api_base_url, two_logins
):
    """What login returns must match what a subsequent read returns.

    #136 made the write conditional, so on a repeat login the row is not
    touched at all. This asserts the response is still built from the real
    persisted row rather than drifting from it — a stale or partially-applied
    update would show up here as a mismatch.
    """
    _, body = two_logins

    resp = requests.get(
        f"{api_base_url}/api/auth/user/info/",
        headers={"Authorization": f"Bearer {body['access']}"},
        timeout=30,
    )
    assert resp.status_code == 200, (
        f"User info request failed ({resp.status_code}): {resp.text}"
    )
    info = resp.json()

    assert str(info["id"]) == str(body["user"]["id"]), (
        f"user/info id {info['id']!r} does not match the id login returned "
        f"({body['user']['id']!r})"
    )
    assert info["email"] == body["user"]["email"], (
        f"user/info email {info['email']!r} does not match the email login "
        f"returned ({body['user']['email']!r})"
    )
