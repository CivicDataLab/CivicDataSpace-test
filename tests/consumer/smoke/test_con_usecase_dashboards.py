# tests/consumer/smoke/test_con_usecase_dashboards.py
#
# Use case detail page dashboards (DataSpaceFrontend PR #476, restyled by #512):
# linked dashboards are embedded as iframes under "Explore the data", above
# "Datasets behind this story". Superset links get standalone=1, and links that
# aren't http(s) are dropped (hiding the whole section when none are left).
#
# Use cases are picked from the backend at runtime rather than hardcoded,
# so the same tests work against dev and prod data.

import os
from urllib.parse import parse_qs, urlsplit

import pytest

from pages.consumer.usecase_page import UseCasePage
from utils.usecase_api import dashboards_by_usecase as _dashboards_by_usecase
from utils.usecase_api import gql, published_usecase_ids

# The section titles and layout asserted here are the #512 revamp; prod still
# renders the old page until that ships, so the file skips there.
pytestmark = [
    pytest.mark.smoke,
    pytest.mark.readonly,
    pytest.mark.deployed_pr("DataSpaceFrontend#512", site="HOME_URL_DEV"),
]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")


def _is_web_url(link):
    return urlsplit(link or "").scheme in ("http", "https")


@pytest.fixture(scope="module")
def dashboards_by_usecase():
    api = os.getenv("API_BASE_URL")
    if not api:
        pytest.skip("API_BASE_URL not set: cannot find use cases with dashboards")
    return _dashboards_by_usecase(api)


@pytest.fixture(scope="module")
def superset_usecase(dashboards_by_usecase):
    superset = [(uc_id, d) for uc_id, dash in dashboards_by_usecase.items() for d in dash
                if _is_web_url(d["link"]) and "/superset/" in urlsplit(d["link"]).path]
    if not superset:
        pytest.skip("No published use case links a Superset dashboard")
    # Prefer a link without standalone=1 so the test proves the frontend adds it.
    return next((s for s in superset if "standalone" not in parse_qs(urlsplit(s[1]["link"]).query)), superset[0])


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


def test_dashboards_render_above_datasets(uc_page, dashboards_by_usecase):
    api = os.environ["API_BASE_URL"]
    ids = [u for u, dash in dashboards_by_usecase.items() if any(_is_web_url(d["link"]) for d in dash)]
    fields = " ".join(f"u{i}: useCase(pk:{i}){{ datasets{{ id }} }}" for i in ids)
    counts = gql(api, "{ " + fields + " }") if ids else {}
    uc_id = next((i for i in ids if counts[f"u{i}"]["datasets"]), None)
    if uc_id is None:
        pytest.skip("No published use case has both an embeddable dashboard and datasets")
    uc_page.open_detail(BASE_URL, uc_id)
    assert uc_page.has_dashboards_section(), f"use case {uc_id}: 'Explore the data' section missing"
    assert uc_page.has_datasets_section(), f"use case {uc_id}: has datasets but 'Datasets behind this story' is missing"
    assert uc_page.dashboards_render_before_datasets(), (
        f"use case {uc_id}: 'Explore the data' renders below 'Datasets behind this story'"
    )


@pytest.mark.parametrize("case", ["no_dashboards", "no_usable_link"])
def test_section_hidden_without_embeddable_dashboards(uc_page, dashboards_by_usecase, case):
    if case == "no_dashboards":
        ids = published_usecase_ids(os.environ["API_BASE_URL"])
        uc_id = next((u for u in ids if u not in dashboards_by_usecase), None)
    else:
        uc_id = next((u for u, dash in dashboards_by_usecase.items()
                      if not any(_is_web_url(d["link"]) for d in dash)), None)
    if uc_id is None:
        pytest.skip(f"No published use case for case {case!r}")
    title = uc_page.open_detail(BASE_URL, uc_id)
    assert title.strip(), f"use case {uc_id}: page loaded without a title, so an absent section proves nothing"
    assert uc_page.dashboards_section_is_gone(), (
        f"use case {uc_id} ({case}): 'Explore the data' still rendered with nothing embeddable to show"
    )
