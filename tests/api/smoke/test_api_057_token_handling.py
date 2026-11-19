# tests/api/smoke/test_api_057_token_handling.py
#
# The API must treat a token it did not issue, or that has expired, exactly
# like no token. Each case alters this account's own valid access token and
# asks `me`; nothing is written. Dev only: it needs a signed-in test account.

import base64
import json

import pytest
import requests

pytestmark = [pytest.mark.api, pytest.mark.security, pytest.mark.smoke]

ME = {"query": "{ me { id } }"}


def _decode(part):
    return json.loads(base64.urlsafe_b64decode(part + "=" * (-len(part) % 4)))


def _encode(obj):
    return base64.urlsafe_b64encode(json.dumps(obj, separators=(",", ":")).encode()).rstrip(b"=").decode()


def _forge(token, case):
    header, payload, signature = token.split(".")
    claims = _decode(payload)
    if case == "tampered signature":
        return f"{header}.{payload}.{signature[:-4]}AAAA"
    if case == "another user's id, original signature":
        return f"{header}.{_encode({**claims, 'user_id': 1})}.{signature}"
    if case == "alg none, no signature":
        return f"{_encode({**_decode(header), 'alg': 'none'})}.{payload}."
    if case == "expiry moved, original signature":
        return f"{header}.{_encode({**claims, 'exp': claims['exp'] + 86400})}.{signature}"
    return "not.a.token"


def _me(api_base_url, token):
    resp = requests.post(f"{api_base_url}/api/graphql", json=ME,
                         headers={"Authorization": f"Bearer {token}"}, timeout=30)
    return resp.json()


def test_valid_token_is_accepted(api_base_url, auth_token):
    """The control: without it, every rejection below would prove nothing."""
    body = _me(api_base_url, auth_token)
    assert body.get("data") and body["data"]["me"]["id"], f"a valid token was refused: {body}"


@pytest.mark.parametrize("case", [
    "tampered signature",
    "another user's id, original signature",
    "alg none, no signature",
    "expiry moved, original signature",
    "garbage",
])
def test_forged_token_is_refused(api_base_url, auth_token, case):
    body = _me(api_base_url, _forge(auth_token, case))
    assert not body.get("data"), f"{case}: the API answered `me` with {body['data']}"
    message = body["errors"][0]["message"]
    assert message == "User is not authenticated", f"{case}: unexpected error {message!r}"


def test_refresh_token_is_not_an_access_token(api_base_url, refresh_token):
    body = _me(api_base_url, refresh_token)
    assert not body.get("data"), f"a refresh token was accepted as an access token: {body['data']}"


def test_forged_token_is_refused_by_rest(api_base_url, auth_token):
    resp = requests.get(f"{api_base_url}/api/auth/user/info/",
                        headers={"Authorization": f"Bearer {_forge(auth_token, 'tampered signature')}"}, timeout=30)
    assert resp.status_code in (401, 403), f"user info answered {resp.status_code} to a forged token"
