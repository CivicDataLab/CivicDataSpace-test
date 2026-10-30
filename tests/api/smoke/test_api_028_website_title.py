# tests/api/smoke/test_api_028_website_title.py
#
# DataSpaceFrontend#470 ("Provider Flow Update") added a new, unauthenticated
# API route, GET /api/website-title?url=<url>, that fetches an arbitrary
# caller-supplied URL server-side and returns its <title>. It validates the
# `url` param (present, http/https only) before fetching.
#
# The two validation tests are `readonly`: `deployed_pr` skips them on any site
# whose X-Git-Sha doesn't include #470, so they sit in the prod gate safely and
# switch on once #470 ships. The title fetch stays out of the prod gate: it
# depends on example.com being reachable from the server.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke]


@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceFrontend#470", site="HOME_URL_DEV")
def test_website_title_rejects_missing_url(dev_frontend_client):
    """No `url` param must 400, not 500 or a silent null-title 200."""
    resp = dev_frontend_client.get("/api/website-title")
    assert resp.status_code == 400, (
        f"expected 400 for a missing url param, got {resp.status_code}: {resp.text}"
    )
    assert resp.json().get("title") is None


@pytest.mark.readonly
@pytest.mark.deployed_pr("DataSpaceFrontend#470", site="HOME_URL_DEV")
def test_website_title_rejects_non_http_protocol(dev_frontend_client):
    """A non-http(s) URL (e.g. javascript:) must 400, confirming the protocol check runs."""
    resp = dev_frontend_client.get(
        "/api/website-title", params={"url": "javascript:alert(1)"}
    )
    assert resp.status_code == 400, (
        f"expected 400 for a non-http(s) url, got {resp.status_code}: {resp.text}"
    )
    assert resp.json().get("title") is None


@pytest.mark.deployed_pr("DataSpaceFrontend#470", site="HOME_URL_DEV")
def test_website_title_fetches_a_real_page_title(dev_frontend_client):
    """A valid http(s) URL must 200 with the target page's actual <title>.

    This is the path that didn't exist before #470: proven red (404) against
    the pre-merge commit locally, see the PR body for both runs.
    """
    resp = dev_frontend_client.get(
        "/api/website-title", params={"url": "https://example.com"}
    )
    assert resp.status_code == 200, f"expected 200, got {resp.status_code}: {resp.text}"
    assert resp.json().get("title") == "Example Domain", (
        f"expected the fetched page's real title, got {resp.json()!r}"
    )
