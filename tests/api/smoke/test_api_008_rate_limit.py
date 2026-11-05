# tests/api/smoke/test_api_008_rate_limit.py
#
# Guards the request budget an ordinary user needs.
#
# Rate limiting lives in api/middleware/rate_limit.py, not in Django REST
# Framework. DRF's DEFAULT_THROTTLE_RATES was set for a long time and did
# nothing at all - DEFAULT_THROTTLE_CLASSES was never configured, no view
# declared throttle_classes, and /api/graphql is a Strawberry view rather than a
# DRF one. During the 429 flood of 2026-09-03 that dead setting was found first
# and read as the cause. These tests exercise the limiter that actually runs.
#
# Limits at the time of writing: 5000/hour GET, 1000/hour non-GET, keyed on the
# client IP taken from X-Forwarded-For.
#
# The volumes here are deliberately small. A test that tried to *reach* the limit
# would spend the budget of every other client behind the same address - which is
# precisely the failure being guarded against.

import os

import pytest
import requests

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.regression, pytest.mark.readonly]

API_BASE_URL = os.getenv("API_BASE_URL", "https://dev.api.civicdataspace.in")

# One page view fires several GraphQL calls. A handful of page views must never
# be enough to get throttled.
BURST = 20
TIMEOUT = 30

MINIMAL_QUERY = {"query": "{ __typename }"}


def _post_graphql():
    return requests.post(
        f"{API_BASE_URL}/api/graphql",
        json=MINIMAL_QUERY,
        timeout=TIMEOUT,
        headers={"Content-Type": "application/json"},
    )


def test_ordinary_request_volume_is_not_rate_limited():
    """A small burst of GraphQL calls must not hit the limiter.

    The POST budget is shared per IP, so it is also shared by everyone behind a
    NAT gateway. If this starts failing, the limit has been set low enough that
    normal browsing from a shared office address breaks.
    """
    statuses = []
    for _ in range(BURST):
        resp = _post_graphql()
        statuses.append(resp.status_code)
        if resp.status_code == 429:
            break

    throttled = statuses.count(429)
    assert throttled == 0, (
        f"{throttled} of {len(statuses)} GraphQL requests returned 429. A burst "
        f"of {BURST} is a few page views' worth. The non-GET limit in "
        "api/middleware/rate_limit.py is too low for normal use, or something "
        "is consuming the shared per-IP budget."
    )


def test_graphql_endpoint_answers_normally():
    """The burst above is only meaningful if the endpoint works at all.

    Without this, a 500 on every request would produce zero 429s and the test
    above would pass while the API was broken.
    """
    resp = _post_graphql()
    assert resp.status_code == 200, (
        f"GraphQL returned {resp.status_code}: {resp.text[:300]}"
    )
    body = resp.json()
    assert "errors" not in body, f"GraphQL errors on a trivial query: {body}"
    assert body.get("data", {}).get("__typename"), f"Unexpected response: {body}"
