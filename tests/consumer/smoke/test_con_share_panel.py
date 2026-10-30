# tests/consumer/smoke/test_con_share_panel.py
#
# Share actions on the dataset page (a popover on the cover) and the use case
# page (inline in the story rail), DataSpaceFrontend #512. Both render the same
# SharePanel, so every case runs on both pages.
#
# Not asserted: the clipboard contents. Reading the clipboard needs a permission
# prompt a headless run cannot answer, so the test checks that copying is
# acknowledged ("Link copied") instead.

import os
from urllib.parse import parse_qs, urlsplit

import pytest

from pages.consumer.dataset_detail_page import DatasetDetailPage
from pages.consumer.share_panel import SharePanel
from pages.consumer.usecase_page import UseCasePage
from utils.usecase_api import gql

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.readonly,
    pytest.mark.deployed_pr("DataSpaceFrontend#512", site="HOME_URL_DEV"),
]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in").rstrip("/")


@pytest.fixture(scope="module")
def pages_under_test():
    """{'dataset'|'usecase': (path, title)} for one published record of each kind."""
    api = os.getenv("API_BASE_URL")
    if not api:
        pytest.skip("API_BASE_URL not set: cannot pick a dataset and a use case")
    data = gql(api, "{ datasets(includePublic: true, pagination: {limit: 1}) { id title } useCases(pagination: {limit: 500}) { id title status } }")
    if not data["datasets"]:
        pytest.skip("no published dataset")
    use_case = next((u for u in data["useCases"] if u["status"] == "PUBLISHED" and u["title"].strip()), None)
    if use_case is None:
        pytest.skip("no published use case")
    ds = data["datasets"][0]
    return {
        "dataset": (f"/datasets/{ds['id']}", ds["title"].strip()),
        "usecase": (f"/usecases/{use_case['id']}", use_case["title"].strip()),
    }


@pytest.fixture
def share(driver, pages_under_test, request):
    """The SharePanel of the page named by the test's `surface` parameter, opened and ready."""
    surface = request.node.callspec.params["surface"]
    path, title = pages_under_test[surface]
    if surface == "dataset":
        DatasetDetailPage(driver, timeout=30).open(BASE_URL, path.rsplit("/", 1)[1])
        panel = SharePanel(driver, timeout=30).open_dataset_popover()
    else:
        UseCasePage(driver, timeout=30).open_detail(BASE_URL, path.rsplit("/", 1)[1])
        panel = SharePanel(driver, timeout=30)
    return panel, f"{BASE_URL}{path}", title


@pytest.mark.parametrize("surface", ["dataset", "usecase"])
def test_share_links_point_at_this_page(share, surface):
    panel, page_url, title = share
    links = panel.links()
    assert set(links) == {"Share on X", "Share on LinkedIn", "Share on Facebook", "Share by email"}, f"share links: {list(links)}"

    def target(label, host, path):
        url = urlsplit(links[label]["href"])
        assert (url.netloc, url.path) == (host, path), f"{label} goes to {links[label]['href']}"
        return parse_qs(url.query)

    assert target("Share on X", "twitter.com", "/intent/tweet") == {"url": [page_url], "text": [title]}
    assert target("Share on LinkedIn", "www.linkedin.com", "/sharing/share-offsite/") == {"url": [page_url]}
    assert target("Share on Facebook", "www.facebook.com", "/sharer/sharer.php") == {"u": [page_url]}
    for label in ("Share on X", "Share on LinkedIn", "Share on Facebook"):
        assert links[label]["target"] == "_blank" and "noopener" in (links[label]["rel"] or ""), f"{label} opens in this tab or leaks the opener: {links[label]}"

    mail = links["Share by email"]["href"]
    assert mail.startswith("mailto:?"), mail
    assert parse_qs(mail[len("mailto:?"):]) == {"subject": [title], "body": [page_url]}, f"email link: {mail}"


@pytest.mark.parametrize("surface", ["dataset", "usecase"])
def test_copy_link_is_acknowledged(share, surface):
    panel, _, _ = share
    assert panel.copy_link() == "Link copied", "copying did not report 'Link copied'"
    assert panel.copy_control_reads_copied(), "the copy control still reads 'Copy link' after copying"
