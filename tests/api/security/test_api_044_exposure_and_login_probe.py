# tests/api/security/test_api_044_exposure_and_login_probe.py
#
# Well-known sensitive paths must not be served (GET only, a fixed short list,
# no scanning), and the token-exchange endpoint rejects bad tokens under a
# tiny bounded probe.

import pytest
import requests

pytestmark = [pytest.mark.api, pytest.mark.security]

SENSITIVE_PATHS = ["/.env", "/.git/HEAD", "/.git/config", "/backup.zip", "/.DS_Store"]
PROBE_REQUESTS = 5  # hard bound; this is a presence check, not a load test


@pytest.mark.parametrize("path", SENSITIVE_PATHS)
@pytest.mark.parametrize("target", ["frontend", "api"])
def test_sensitive_paths_are_not_served(frontend_base_url_dev, api_base_url, target, path):
    base = frontend_base_url_dev if target == "frontend" else api_base_url
    resp = requests.get(f"{base}{path}", timeout=30, allow_redirects=False)
    assert resp.status_code in (403, 404), f"{target} {path} answered {resp.status_code}: {resp.text[:120]!r}"


def test_token_exchange_rejects_bad_tokens_in_bounded_probe(api_base_url):
    """Five invalid-token exchanges: every one 401, none 5xx, no session cookie issued.

    Five requests cannot prove a limiter exists (test_api_008 documents the real
    budget); they prove the endpoint answers an unauthenticated attacker's
    guesses uniformly and stops early if it starts throttling or erroring.
    """
    statuses = []
    for i in range(PROBE_REQUESTS):
        resp = requests.post(f"{api_base_url}/api/auth/keycloak/login/",
                             json={"token": f"invalid-{i}"}, timeout=30)
        statuses.append(resp.status_code)
        assert not resp.headers.get("Set-Cookie"), "bad token produced a cookie"
        if resp.status_code in (429, 500, 502, 503, 504):
            break
    assert statuses == [401] * PROBE_REQUESTS, f"bad-token probe statuses: {statuses}"
