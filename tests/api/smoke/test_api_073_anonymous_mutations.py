# tests/api/smoke/test_api_073_anonymous_mutations.py
#
# Mutations that change the shared taxonomy must refuse an anonymous caller. Every
# attempt aims at the all-zero id, so nothing real is touched even if the API lets
# the call through. Hard fail until the advisory GHSA-jcj9-qw6c-98h3 is fixed.

import os

import pytest
import requests

pytestmark = [pytest.mark.api, pytest.mark.smoke]

ZERO = "00000000-0000-0000-0000-000000000000"
ATTEMPTS = {
    "update-sector": ("mutation($i: SectorInputPartial!){ updateSector(input:$i){ __typename } }", {"i": {"id": ZERO}}),
    "delete-sector": ("mutation($i: UUID!){ deleteSector(sectorId:$i) }", {"i": ZERO}),
    "update-sdg": ("mutation($i: SDGInputPartial!){ updateSdg(input:$i){ __typename } }", {"i": {"id": ZERO}}),
    "delete-sdg": ("mutation($i: UUID!){ deleteSdg(sdgId:$i) }", {"i": ZERO}),
}
REFUSAL = ("authenticat", "permission", "not allowed", "login", "unauthor", "forbidden")


@pytest.mark.parametrize("case", ATTEMPTS)
def test_api_073_anonymous_caller_is_refused(case):
    base = os.getenv("API_BASE_URL")
    if not base:
        pytest.skip("API_BASE_URL not set")
    query, variables = ATTEMPTS[case]
    body = requests.post(f"{base.rstrip('/')}/api/graphql", json={"query": query, "variables": variables}, timeout=30).json()
    message = " ".join(e.get("message", "") for e in body.get("errors") or []).lower()
    assert any(w in message for w in REFUSAL), f"{case}: an anonymous caller reached the resolver (GHSA-jcj9-qw6c-98h3): {message[:80]!r}"
