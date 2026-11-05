# tests/consumer/smoke/test_con_usecase_justicehub_embed.py
#
# Use case detail page: JusticeHub dashboard embed (DataSpaceFrontend PR #492).
#
# JusticeHub dashboards sometimes showed their logo broken/oversized because
# the iframe rendered before JusticeHub's public stylesheet and logo had
# loaded. For justicehub.in links only, the frontend now preloads that
# stylesheet/logo and hides the iframe behind a spinner (aria-busy) until it
# has actually loaded. Other dashboards (e.g. Superset, already covered by
# test_con_usecase_dashboards.py) are unchanged -- JusticeHubEmbed is only
# used when the link's hostname is justicehub.in / www.justicehub.in.
#
# The use case is picked from the backend at runtime (never hardcoded), so
# this keeps working as long as some published use case links a JusticeHub
# dashboard, on dev or prod alike.

import os
from urllib.parse import urlsplit

import pytest
import requests

from pages.consumer.usecase_page import UseCasePage

pytestmark = [pytest.mark.smoke, pytest.mark.readonly]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")


def _gql(api, query):
    r = requests.post(f"{api.rstrip('/')}/api/graphql", json={"query": query}, timeout=20)
    r.raise_for_status()
    body = r.json()
    assert not body.get("errors"), body["errors"]
    return body["data"]


def _is_justicehub(link):
    try:
        return urlsplit(link or "").hostname in ("justicehub.in", "www.justicehub.in")
    except ValueError:
        return False


@pytest.fixture(scope="module")
def justicehub_usecase():
    api = os.getenv("API_BASE_URL")
    if not api:
        pytest.skip("API_BASE_URL not set: cannot find a use case with a JusticeHub dashboard")
    published = [u["id"] for u in _gql(api, "{ useCases(pagination:{limit:500}){ id status } }")["useCases"]
                 if u["status"] == "PUBLISHED"]
    for uc_id in published:
        dash = _gql(api, "{ usecaseDashboards(usecaseId:%s){ id name link } }" % uc_id)["usecaseDashboards"]
        hit = next((d for d in dash if _is_justicehub(d["link"])), None)
        if hit:
            return uc_id, hit
    pytest.skip("No published use case currently links a JusticeHub (justicehub.in) dashboard")


@pytest.fixture
def uc_page(driver):
    return UseCasePage(driver, timeout=30)


def test_justicehub_dashboard_preloads_theme_assets(uc_page, justicehub_usecase):
    """The JusticeHub stylesheet/logo are preloaded before the iframe shows.

    Before #492 these <link> tags did not exist at all for this dashboard --
    a plain iframe was used, same as every other dashboard.
    """
    uc_id, dashboard = justicehub_usecase
    uc_page.open_detail(BASE_URL, uc_id)
    assert uc_page.has_dashboards_section(), f"use case {uc_id}: dashboards section missing"

    preloaded = uc_page.justicehub_theme_preloaded()
    assert preloaded == {"preconnect": True, "preload_css": True, "preload_logo": True}, (
        f"use case {uc_id} ({dashboard['link']}): JusticeHub theme preload links missing: {preloaded}"
    )


def test_justicehub_dashboard_is_still_embedded_and_becomes_ready(uc_page, justicehub_usecase):
    """The dashboard still renders as the right iframe, and the loading
    wrapper clears aria-busy instead of leaving the spinner up forever."""
    uc_id, dashboard = justicehub_usecase
    uc_page.open_detail(BASE_URL, uc_id)
    assert uc_page.has_dashboards_section(), f"use case {uc_id}: dashboards section missing"

    frames = {f["title"]: f["src"] for f in uc_page.embedded_dashboards()}
    assert dashboard["name"] in frames, f"use case {uc_id}: no iframe titled {dashboard['name']!r}, got {list(frames)}"
    assert frames[dashboard["name"]] == dashboard["link"], (
        f"use case {uc_id}: iframe src {frames[dashboard['name']]!r} does not match dashboard link {dashboard['link']!r}"
    )

    assert uc_page.justicehub_embed_becomes_ready(timeout=12), (
        f"use case {uc_id} ({dashboard['link']}): JusticeHub embed wrapper never cleared aria-busy"
    )
