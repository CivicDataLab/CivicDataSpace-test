# tests/consumer/smoke/test_con_dataset_detail_tabs.py
#
# Public dataset page tabs (DataSpaceFrontend #512): Data, Visualisations,
# Metadata and Connected to. Every tab's content is checked against what the
# public GraphQL API says about the same dataset, so each assertion fails if the
# page shows the wrong record, drops a field or loses a row.
#
# Datasets are picked from the live catalogue by shape (several files, has
# charts, linked to a use case, ...) rather than hardcoded, so the tests follow
# dev and prod data. A shape nobody has is a skip with the reason.
#
# Not covered here: the share panel (test_con_dataset_share.py) and the
# "File details" sheet, which only restates the fact line asserted below.

import os
import re
from urllib.parse import parse_qs, quote, urlsplit

import pytest

from pages.consumer.dataset_detail_page import DatasetDetailPage
from utils.dataset_api import chart_names, load_catalogue

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.readonly,
    pytest.mark.deployed_pr("DataSpaceFrontend#512", site="HOME_URL_DEV"),
]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")

# Hash each tab writes to the URL (and reads back on a deep link).
TAB_HASH = {
    "data": "#dataset-files",
    "visualisations": "#dataset-visualisations",
    "metadata": "#dataset-metadata",
    "connected": "#dataset-connected",
}
ACCESS_LABEL = {"PUBLIC": "Open Access", "RESTRICTED": "Restricted Access", "PRIVATE": "Private"}


def _unique(values):
    seen = []
    for v in values:
        v = (v or "").strip()
        if v and v not in seen:
            seen.append(v)
    return seen


def _publisher(ds):
    owner = ds["user"] if ds["isIndividualDataset"] else ds["organization"]
    return ((owner or {}).get("fullName") or (owner or {}).get("name") or "").strip()


def _stored_name(resource):
    return (((resource.get("fileDetails") or {}).get("file") or {}).get("name") or "").replace("resources/", "", 1)


@pytest.fixture(scope="module")
def api():
    value = os.getenv("API_BASE_URL")
    if not value:
        pytest.skip("API_BASE_URL not set: cannot pick datasets to check the page against")
    return value.rstrip("/")


@pytest.fixture(scope="module")
def catalogue(api):
    return load_catalogue(api)


@pytest.fixture(scope="module")
def charts(api, catalogue):
    datasets, _ = catalogue
    return chart_names(api, [d["id"] for d in datasets if d["resources"]][:150])


@pytest.fixture(scope="module")
def metadata_dataset(catalogue):
    """A dataset whose Metadata tab shows every fact the test checks."""
    datasets, _ = catalogue
    ds = next((d for d in datasets
               if d["description"] and not re.search(r"<[a-z]", d["description"], re.I)
               and _unique(s["name"] for s in d["sectors"]) and _unique(g["name"] for g in d["geographies"])
               and _unique(t["value"] for t in d["tags"]) and _publisher(d) and d["downloadCount"] > 0), None)
    if ds is None:
        pytest.skip("No published dataset has a plain description, sector, geography, tags, publisher and downloads")
    return ds


@pytest.fixture(scope="module")
def files_dataset(catalogue):
    """A dataset with a few uniquely named files kept at the top level (no folders)."""
    datasets, _ = catalogue
    for d in datasets:
        names = [r["name"].strip() for r in d["resources"]]
        if (2 <= len(names) <= 8 and len(set(names)) == len(names) and all(names)
                and all("/" not in _stored_name(r) for r in d["resources"])):
            return d
    pytest.skip("No published dataset has 2-8 uniquely named top-level files")


@pytest.fixture
def page(driver):
    return DatasetDetailPage(driver, timeout=30)


# ── tab switching ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("tab,entry", [
    ("data", "deeplink"),
    ("visualisations", "click"), ("visualisations", "deeplink"),
    ("metadata", "click"), ("metadata", "deeplink"),
    ("connected", "click"), ("connected", "deeplink"),
])
def test_tab_shows_only_its_own_panel(page, metadata_dataset, tab, entry):
    """Selecting a tab (click or #hash deep link) selects it, shows its panel alone, and keeps the hash."""
    if entry == "deeplink":
        page.open(BASE_URL, metadata_dataset["id"], hash=TAB_HASH[tab])
    else:
        page.open(BASE_URL, metadata_dataset["id"])
        page.open_tab(tab)

    assert page.selected_tabs() == [tab], f"selected tabs after {entry} to {tab}: {page.selected_tabs()}"
    assert page.wait_for_panel_heading(tab), f"{tab} panel has no heading"
    assert page.visible_panels() == [tab], f"visible panels after {entry} to {tab}: {page.visible_panels()}"
    assert page.hash() == TAB_HASH[tab], f"URL hash after {entry} to {tab}: {page.hash()!r}"


# ── data tab ─────────────────────────────────────────────────────────────────

def test_data_tab_every_file_has_its_own_download(page, api, files_dataset):
    """Each file in the dataset is listed, and selecting it shows that file's name, row count and download."""
    ds = files_dataset
    page.open(BASE_URL, ds["id"])
    assert sorted(page.file_names()) == sorted(r["name"].strip() for r in ds["resources"]), (
        f"dataset {ds['id']}: file list does not match the dataset's resources"
    )
    for res in ds["resources"]:
        shown = page.select_file(res["name"].strip())
        expected = res["url"].strip() if res["type"] in ("API", "EXTERNAL") and res["url"] else f"{api}/api/download/resource/{res['id']}"
        assert shown["download"] == expected, f"file {res['name']!r}: Download points at {shown['download']}, expected {expected}"
        if res["noOfEntries"] is not None:
            assert f"{res['noOfEntries']:,} rows" in shown["facts"], f"file {res['name']!r}: fact line {shown['facts']!r} lacks {res['noOfEntries']:,} rows"


# ── visualisations tab ───────────────────────────────────────────────────────

@pytest.mark.parametrize("case", ["with_charts", "no_charts"])
def test_visualisations_tab_lists_the_datasets_charts(page, charts, case):
    if case == "with_charts":
        # Few charts keeps the page light; any dataset with charts proves the list.
        pick = min(((d, charts[d]) for d, names in charts.items() if names), key=lambda x: len(x[1]), default=None)
    else:
        pick = next(((d, names) for d, names in charts.items() if not names), None)
    if pick is None:
        pytest.skip(f"No published dataset for case {case!r}")
    dataset_id, names = pick

    page.open(BASE_URL, dataset_id)
    page.open_tab("visualisations")
    if case == "with_charts":
        assert sorted(page.chart_names()) == sorted(names), f"dataset {dataset_id}: chart cards do not match its charts {names}"
    else:
        assert page.has_no_charts_notice(), f"dataset {dataset_id} has no charts but the empty state is missing"


# ── metadata tab ─────────────────────────────────────────────────────────────

def test_metadata_tab_shows_the_datasets_record(page, metadata_dataset):
    ds = metadata_dataset
    page.open(BASE_URL, ds["id"])
    page.open_tab("metadata")

    assert page.about_text() == " ".join(ds["description"].split()), f"dataset {ds['id']}: 'About this dataset' differs from its description"

    facts = page.info_facts()
    expected = {
        "Sector": ", ".join(_unique(s["name"] for s in ds["sectors"])),
        "Geography": ", ".join(_unique(g["name"] for g in ds["geographies"])),
        "Publisher": _publisher(ds),
        "Downloads": f"{ds['downloadCount']:,}",
    }
    if ds["accessType"] in ACCESS_LABEL:
        expected["Access"] = ACCESS_LABEL[ds["accessType"]]
    for label, value in expected.items():
        assert facts.get(label) == value, f"dataset {ds['id']}: {label} shows {facts.get(label)!r}, expected {value!r} (facts: {facts})"

    tags = _unique(t["value"] for t in ds["tags"])
    links = page.tag_links()
    assert [label for label, _ in links] == tags, f"dataset {ds['id']}: tag chips {links} do not match tags {tags}"
    for label, href in links:
        query = parse_qs(urlsplit(href).query)
        assert query == {"types": ["dataset"], "tags": [label]}, f"tag {label!r} links to {href}"
        encoded = quote(label, safe="!~*'()")  # what encodeURIComponent produces
        assert href.endswith(f"tags={encoded}"), f"tag {label!r} href is not URL-encoded: {href}"


# ── connected tab ────────────────────────────────────────────────────────────

@pytest.mark.parametrize("case", ["linked", "unlinked"])
def test_connected_tab_lists_what_uses_the_dataset(page, catalogue, case):
    datasets, links = catalogue
    if case == "linked":
        ds = next((d for d in datasets if d["id"] in links["usecases"]), None)
    else:
        ds = next((d for d in datasets if d["id"] not in links["usecases"] and d["id"] not in links["collaboratives"]), None)
    if ds is None:
        pytest.skip(f"No published dataset for case {case!r}")
    use_cases = links["usecases"].get(ds["id"], [])
    collaboratives = links["collaboratives"].get(ds["id"], [])

    page.open(BASE_URL, ds["id"])
    page.open_tab("connected")

    if case == "unlinked":
        assert page.has_nothing_connected_notice(), f"dataset {ds['id']} is in no use case or collaborative but the empty state is missing"
        return

    expected_groups = ([f"Use cases · {len(use_cases)}"] if use_cases else []) + ([f"Collaboratives · {len(collaboratives)}"] if collaboratives else [])
    assert page.connected_group_titles() == expected_groups, f"dataset {ds['id']}: connected groups differ from the API's links"
    hrefs = page.wait_for_connected_cards(len(use_cases) + len(collaboratives))
    for uc in use_cases:
        assert any(h.endswith(f"/usecases/{uc['id']}") for h in hrefs), f"no card links to use case {uc['id']} ({uc['title']!r}): {hrefs}"

    page.click_filter("Use cases")
    assert page.hash() == "#dataset-connected-usecases", f"filter hash: {page.hash()!r}"
    assert page.connected_group_titles() == [f"Use cases · {len(use_cases)}"], "'Use cases' filter still shows other groups"
