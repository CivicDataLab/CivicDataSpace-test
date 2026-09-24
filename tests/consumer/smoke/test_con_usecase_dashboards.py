# tests/consumer/smoke/test_con_usecase_dashboards.py
#
# Use case detail page dashboards (DataSpaceFrontend PR #476): linked
# dashboards are embedded as iframes above "Datasets in this Use Case",
# Superset links get standalone=1, and links that aren't http(s) are dropped
# (hiding the whole section when none are left).
#
# Use cases are picked from the backend at runtime rather than hardcoded,
# so the same tests work against dev and prod data.

import os
from urllib.parse import parse_qs, urlsplit

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


def _published_ids(api):
    return [u["id"] for u in _gql(api, "{ useCases(pagination:{limit:500}){ id status } }")["useCases"]
            if u["status"] == "PUBLISHED"]


def _is_web_url(link):
    return urlsplit(link or "").scheme in ("http", "https")


@pytest.fixture(scope="module")
def dashboards_by_usecase():
    api = os.getenv("API_BASE_URL")
    if not api:
        pytest.skip("API_BASE_URL not set: cannot find use cases with dashboards")
    found = {}
    for uc_id in _published_ids(api):
        dash = _gql(api, "{ usecaseDashboards(usecaseId:%s){ id name link } }" % uc_id)["usecaseDashboards"]
        if dash:
            found[uc_id] = dash
    return found


@pytest.fixture(scope="module")
def superset_usecase(dashboards_by_usecase):
    for uc_id, dash in dashboards_by_usecase.items():
        superset = [d for d in dash if _is_web_url(d["link"]) and "/superset/" in urlsplit(d["link"]).path]
        if superset:
            return uc_id, superset[0]
    pytest.skip("No published use case links a Superset dashboard")


@pytest.fixture
def uc_page(driver):
    return UseCasePage(driver, timeout=30)


def test_superset_dashboard_is_embedded_standalone(uc_page, superset_usecase):
    uc_id, dashboard = superset_usecase
    uc_page.open_detail(BASE_URL, uc_id)

    frames = {f["title"]: f["src"] for f in uc_page.embedded_dashboards()}
    assert dashboard["name"] in frames, f"use case {uc_id}: no iframe titled {dashboard['name']!r}, got {list(frames)}"

    src, link = urlsplit(frames[dashboard["name"]]), urlsplit(dashboard["link"])
    assert (src.netloc, src.path) == (link.netloc, link.path), f"iframe src {src.geturl()} is not the dashboard {link.geturl()}"
    params = parse_qs(src.query)
    assert params.get("standalone") == ["1"], f"Superset iframe src lacks standalone=1: {src.geturl()}"
    for key, value in parse_qs(link.query).items():
        assert params.get(key) == value, f"iframe src dropped/changed ?{key}= from the dashboard link: {src.geturl()}"

    opens = [o for o in uc_page.dashboard_open_links() if o["href"] == src.geturl()]
    assert opens, f"no 'Open dashboard in a new tab' link pointing at {src.geturl()}"
    assert opens[0]["target"] == "_blank"
    assert "noreferrer" in (opens[0]["rel"] or "")


def test_dashboards_render_above_datasets(uc_page, superset_usecase):
    uc_id, _ = superset_usecase
    uc_page.open_detail(BASE_URL, uc_id)
    assert uc_page.has_dashboards_section(), f"use case {uc_id}: dashboards section missing"
    assert uc_page.dashboards_render_before_datasets(), (
        f"use case {uc_id}: 'Dashboards Linked to this Use Case' renders below 'Datasets in this Use Case'"
    )


@pytest.mark.parametrize("case", ["no_dashboards", "no_usable_link"])
def test_section_hidden_without_embeddable_dashboards(uc_page, dashboards_by_usecase, case):
    if case == "no_dashboards":
        ids = _published_ids(os.environ["API_BASE_URL"])
        uc_id = next((u for u in ids if u not in dashboards_by_usecase), None)
    else:
        uc_id = next((u for u, dash in dashboards_by_usecase.items()
                      if not any(_is_web_url(d["link"]) for d in dash)), None)
    if uc_id is None:
        pytest.skip(f"No published use case for case {case!r}")
    uc_page.open_detail(BASE_URL, uc_id)
    assert not uc_page.has_dashboards_section(timeout=8), (
        f"use case {uc_id} ({case}): dashboards section rendered with nothing embeddable to show"
    )
