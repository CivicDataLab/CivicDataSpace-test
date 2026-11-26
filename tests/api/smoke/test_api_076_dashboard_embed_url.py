# tests/api/smoke/test_api_076_dashboard_embed_url.py
#
# DataSpaceBackend#322: usecase dashboard links are now checked on the backend, which
# also returns an `embedUrl` field (the link to put in the iframe, or null when the
# link's host may not be embedded) on `usecaseDashboards`/`usecaseDashboardsAll`.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.readonly, pytest.mark.deployed_pr("DataSpaceBackend#322")]

# The default allow-list this PR introduces (DASHBOARD_EMBED_ORIGINS), used only to
# pick existing dashboards that exercise each outcome - not to re-implement the check.
_ALLOWED_HOSTS = ("justicehub.in", "analytics.civicdataspace.in", "public.tableau.com")

QUERY = "{ usecaseDashboardsAll(filters:{}, order:{}, pagination:{limit: %d, offset: %d}) { id usecaseId link embedUrl } }"


def _host(link):
    from urllib.parse import urlsplit
    return (urlsplit(link).hostname or "").lower()


def _scan(anon_graphql_client):
    allowed, empty = None, None
    for offset in range(0, 1000, 100):
        rows = anon_graphql_client.query(QUERY % (100, offset))["usecaseDashboardsAll"]
        for row in rows:
            link = row["link"] or ""
            if not link and empty is None:
                empty = row
            elif link:
                host = _host(link)
                if allowed is None and any(host == h or host.endswith(f".{h}") for h in _ALLOWED_HOSTS):
                    allowed = row
        if allowed and empty:
            break
        if len(rows) < 100:
            break
    return allowed, empty


@pytest.fixture(scope="module")
def dashboards(anon_graphql_client):
    allowed, empty = _scan(anon_graphql_client)
    if allowed is None or empty is None:
        pytest.skip("need a published dashboard with an allowed-host link and one with an empty link")
    return {"allowed": allowed, "empty": empty}


@pytest.mark.smoke
@pytest.mark.regression
def test_embed_url_passes_through_an_allowed_host_link(dashboards):
    row = dashboards["allowed"]
    assert row["embedUrl"] == row["link"], (
        f"usecase {row['usecaseId']} dashboard {row['id']}: embedUrl {row['embedUrl']!r} != link {row['link']!r}"
    )


@pytest.mark.smoke
@pytest.mark.regression
def test_embed_url_is_null_for_an_empty_link(dashboards):
    row = dashboards["empty"]
    assert row["link"] == ""
    assert row["embedUrl"] is None, (
        f"usecase {row['usecaseId']} dashboard {row['id']}: embedUrl should be null for an empty link, got {row['embedUrl']!r}"
    )
