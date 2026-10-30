# tests/api/security/test_api_043_cors_and_error_leakage.py
#
# CORS must not reflect an arbitrary Origin together with credentials, and
# error responses must not leak internals. Anonymous, read-only requests.

import re

import pytest
import requests

pytestmark = [pytest.mark.api, pytest.mark.security]

EVIL = "https://evil.example"
LEAK = re.compile(r"Traceback \(most recent|File \"/|\.py\", line|psycopg|sqlalchemy|SELECT .* FROM|django\.db|"
                  r"DEBUG = True|/home/|/app/|/usr/lib", re.I)


@pytest.mark.xfail(strict=True, reason="dev API echoes an arbitrary Origin with Allow-Credentials: true at the time of writing")
def test_cors_does_not_reflect_arbitrary_origin_with_credentials(api_base_url):
    resp = requests.post(
        f"{api_base_url}/api/graphql", json={"query": "{ __typename }"},
        headers={"Origin": EVIL}, timeout=30,
    )
    allow = resp.headers.get("Access-Control-Allow-Origin", "")
    creds = resp.headers.get("Access-Control-Allow-Credentials", "").lower() == "true"
    assert not (allow == EVIL and creds), (
        f"Origin {EVIL} reflected with credentials: ACAO={allow!r} ACAC={creds}"
    )


@pytest.mark.parametrize("method,path,kwargs", [
    pytest.param("post", "/api/graphql", {"json": {"query": "{ doesNotExist }"}}, id="unknown_field"),
    pytest.param("post", "/api/graphql", {"json": {"query": "{ datasets( "}}, id="syntax_error"),
    pytest.param("post", "/api/graphql", {"data": "not json", "headers": {"Content-Type": "application/json"}}, id="bad_json"),
    pytest.param("get", "/api/no-such-route-xyz/", {}, id="unknown_route", marks=pytest.mark.xfail(
        strict=True, reason="dev answers unknown routes with the framework's HTML debug 404 page at the time of writing")),
    pytest.param("post", "/api/auth/keycloak/login/", {"json": {"token": "not-a-token"}}, id="bad_token"),
])
def test_error_responses_do_not_leak_internals(api_base_url, method, path, kwargs):
    resp = getattr(requests, method)(f"{api_base_url}{path}", timeout=30, **kwargs)
    assert resp.status_code < 500, f"{path} answered {resp.status_code}, so the error path was not exercised"
    found = LEAK.search(resp.text)
    assert not found, f"{path} response leaks internals ({found.group(0)!r}): {resp.text[:300]}"
