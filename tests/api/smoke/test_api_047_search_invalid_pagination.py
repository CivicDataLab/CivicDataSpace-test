# tests/api/smoke/test_api_047_search_invalid_pagination.py
#
# Invalid page/size values on the public search API must not crash it.
# A client that sends page=0, page=-1, page=9999 or size=abc should get a 4xx,
# or a 200 with the value clamped - never a 5xx. Today the dataset, usecase,
# collaborative and aimodel search endpoints answer 500 for all four, and the
# list pages then render blank (consumer issue C-001). publisher search already
# copes, so it is not listed.
#
# The bad-input test asserts the correct behaviour and is strict xfail: it keeps
# CI green while the bug exists and goes red (XPASS) once it is fixed, at which
# point the marker has to come off. The control test (page=1) must always pass.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.regression, pytest.mark.readonly]

ENTITIES = ["dataset", "usecase", "collaborative", "aimodel"]
BAD_PARAMS = [
    pytest.param({"page": 9999}, id="page-9999"),
    pytest.param({"page": 0}, id="page-0"),
    pytest.param({"page": -1}, id="page--1"),
    pytest.param({"size": "abc"}, id="size-abc"),
]


@pytest.mark.parametrize("entity", ENTITIES)
def test_search_valid_page_is_ok(anon_api_client, entity):
    """Control: a valid page returns 200, so the bad-input cases below fail for the right reason."""
    resp = anon_api_client.get(f"/api/search/{entity}/", params={"page": 1})
    assert resp.status_code == 200, f"{entity} search page=1 -> {resp.status_code}: {resp.text[:200]}"


@pytest.mark.xfail(
    strict=True,
    reason="consumer issue C-001: search API answers 500 for invalid page/size",
)
@pytest.mark.parametrize("params", BAD_PARAMS)
@pytest.mark.parametrize("entity", ENTITIES)
def test_search_invalid_pagination_is_not_a_server_error(anon_api_client, entity, params):
    """Invalid page/size gives a 4xx or a clamped 200, never a 5xx."""
    resp = anon_api_client.get(f"/api/search/{entity}/", params=params)
    assert resp.status_code < 500, (
        f"{entity} search {params} -> {resp.status_code}: {resp.text[:200]}"
    )
