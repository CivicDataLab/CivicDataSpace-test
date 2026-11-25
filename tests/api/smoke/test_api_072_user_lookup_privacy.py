# tests/api/smoke/test_api_072_user_lookup_privacy.py
#
# An anonymous caller must not read a user's e-mail address through user(id:).
# Hard fail until the advisory GHSA-v29h-63vw-gw4f is fixed.

import os

import pytest
import requests

from utils.provider_api import ProviderAPI

pytestmark = [pytest.mark.api, pytest.mark.smoke]


def test_api_072_anonymous_user_lookup_hides_the_email():
    base = os.getenv("API_BASE_URL")
    email, password = os.getenv("TEST_EMAIL_1"), os.getenv("TEST_PASSWORD_1")
    if not (base and email and password):
        pytest.skip("API_BASE_URL and TEST_EMAIL_1/TEST_PASSWORD_1 are needed")
    user_id = ProviderAPI(email, password).gql("{ me { id } }")["data"]["me"]["id"]
    body = requests.post(f"{base.rstrip('/')}/api/graphql", json={"query": "{ user(id: %s){ id email } }" % user_id}, timeout=30).json()
    user = (body.get("data") or {}).get("user") or {}
    leaked = bool(user.get("email"))
    assert not leaked, "an anonymous caller read a user's e-mail address (GHSA-v29h-63vw-gw4f)"
