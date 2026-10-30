# tests/consumer/smoke/test_con_usecase_story_page.py
#
# Use case detail page as redesigned in DataSpaceFrontend #512: the cover, the
# story rail (Contents, Contributors), the "Datasets behind this story" cards
# and the topic chips at the bottom. Each part is checked against the same use
# case's public GraphQL record, so a dropped, reordered or mislinked entry
# fails. Dashboards and the share panel have their own files.
#
# Use cases are picked from the live catalogue by shape, never hardcoded; a
# shape nobody has is a skip with the reason.

import os
import re
from urllib.parse import parse_qs, unquote, urlsplit

import pytest

from pages.consumer.dataset_detail_page import DatasetDetailPage
from pages.consumer.usecase_page import UseCasePage
from utils.usecase_api import gql

pytestmark = [
    pytest.mark.smoke,
    pytest.mark.readonly,
    pytest.mark.deployed_pr("DataSpaceFrontend#512", site="HOME_URL_DEV"),
]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in").rstrip("/")

USECASES_QUERY = """
{ useCases(pagination: {limit: 500}) {
    id title status summary isIndividualUsecase
    tags { value } sdgs { code name } sectors { name } geographies { name }
    datasets { id title }
    contributors { id fullName }
    supportingOrganizations { id slug name }
    partnerOrganizations { id slug name }
    user { id fullName }
    organization { id name slug }
} }
"""
HEADING = re.compile(r"<h[1-3]\b", re.I)


def _org_path(org):
    return f"/publishers/organization/{(org['slug'] or org['name']).strip()}_{org['id']}"


def _rail(uc):
    """Contributors the way the rail lists them: people, then supporting and partner organisations, deduplicated."""
    rows = [(p["fullName"].strip(), f"/publishers/{p['fullName'].strip()}_{p['id']}") for p in uc["contributors"] if p["fullName"].strip()]
    rows += [(o["name"].strip(), _org_path(o)) for o in uc["supportingOrganizations"] + uc["partnerOrganizations"] if o["name"].strip()]
    seen, out = set(), []
    for name, path in rows:
        if path not in seen:
            seen.add(path)
            out.append((name, path))
    return out


@pytest.fixture(scope="module")
def published():
    api = os.getenv("API_BASE_URL")
    if not api:
        pytest.skip("API_BASE_URL not set: cannot pick use cases to check the page against")
    return [u for u in gql(api, USECASES_QUERY)["useCases"] if u["status"] == "PUBLISHED" and u["title"].strip()]


def _pick(published, what, predicate):
    uc = next((u for u in published if predicate(u)), None)
    if uc is None:
        pytest.skip(f"No published use case with {what}")
    return uc


@pytest.fixture
def uc_page(driver):
    return UseCasePage(driver, timeout=30)


@pytest.mark.parametrize("individual", [False, True], ids=["organisation", "individual"])
def test_cover_shows_title_publisher_and_place(uc_page, published, individual):
    uc = _pick(published, f"a geography and {'an individual' if individual else 'an organisation'} as publisher",
               lambda u: u["geographies"] and bool(u["isIndividualUsecase"]) == individual and (u["user"] if individual else u["organization"]))
    title = uc_page.open_detail(BASE_URL, uc["id"])
    cover = uc_page.cover()

    assert title == uc["title"].strip(), f"use case {uc['id']}: cover title {title!r}"
    assert urlsplit(cover["back"]).path == "/usecases", f"Back goes to {cover['back']}"
    if uc["isIndividualUsecase"]:
        expected = (uc["user"]["fullName"].strip(), "Individual", f"/publishers/{uc['user']['fullName'].strip()}_{uc['user']['id']}")
    else:
        expected = (uc["organization"]["name"].strip(), "Organisation", _org_path(uc["organization"]))
    shown = (cover["publisher"]["name"], cover["publisher"]["kind"], unquote(urlsplit(cover["publisher"]["href"]).path))
    assert shown == expected, f"use case {uc['id']}: publisher {shown}, expected {expected}"
    places = ", ".join(dict.fromkeys(g["name"].strip() for g in uc["geographies"] if g["name"].strip()))
    assert places in cover["meta"], f"use case {uc['id']}: cover meta {cover['meta']!r} lacks the geography {places!r}"
    assert "Published " in cover["meta"], f"use case {uc['id']}: cover meta {cover['meta']!r} has no publish date"


def test_contents_links_jump_to_their_headings(uc_page, published):
    uc = _pick(published, "story headings", lambda u: HEADING.search(u["summary"] or ""))
    uc_page.open_detail(BASE_URL, uc["id"])
    links = uc_page.contents_links()
    assert links, f"use case {uc['id']} has headings in its story but the Contents list is empty"
    assert len({href for _, href in links}) == len(links), f"Contents links share an anchor: {links}"
    for label, _ in links:
        target, heading_text = uc_page.jump_to_story_heading(label)
        assert heading_text == label, f"Contents entry {label!r} jumps to #{target}, which is {heading_text!r}"


def test_contributors_list_matches_the_use_case(uc_page, published):
    uc = _pick(published, "contributors or supporting organisations", lambda u: _rail(u))
    uc_page.open_detail(BASE_URL, uc["id"])
    shown = [(name, unquote(urlsplit(href).path)) for name, href in uc_page.contributors()]
    # The API does not promise an order within people / organisations, so compare as sets.
    assert sorted(shown) == sorted(_rail(uc)), f"use case {uc['id']}: contributors {shown}"
    assert len(shown) == len(set(shown)), f"use case {uc['id']}: a contributor is listed twice: {shown}"


def test_dataset_cards_match_the_use_cases_datasets(uc_page, published):
    uc = _pick(published, "datasets", lambda u: any(d["title"].strip() for d in u["datasets"]))
    uc_page.open_detail(BASE_URL, uc["id"])
    expected = {f"/datasets/{d['id']}": d["title"].strip() for d in uc["datasets"] if d["title"].strip()}
    cards = uc_page.dataset_cards()
    # One card per dataset; the API does not promise an order, so match by link.
    assert sorted(urlsplit(href).path for href, _ in cards) == sorted(expected), f"use case {uc['id']}: card links {cards}"
    for href, text in cards:
        title = expected[urlsplit(href).path]
        assert text.startswith(title), f"card {href} reads {text[:60]!r}, expected it to start with {title!r}"


def test_dataset_card_opens_that_dataset(driver, uc_page, published):
    uc = _pick(published, "datasets", lambda u: any(d["title"].strip() for d in u["datasets"]))
    titles = {f"/datasets/{d['id']}": d["title"].strip() for d in uc["datasets"] if d["title"].strip()}
    uc_page.open_detail(BASE_URL, uc["id"])
    opened = uc_page.open_dataset_card(0)
    path = urlsplit(opened).path
    assert DatasetDetailPage(driver, timeout=30).title() == titles[path], f"card {opened} of use case {uc['id']} opened {driver.current_url}"
    assert urlsplit(driver.current_url).path == path


@pytest.mark.parametrize("group,title,param", [("tags", "Tags", "tags"), ("sdgs", "SDG Goals", "sdgs"), ("sectors", "Sector", "sectors")])
def test_topic_chips_link_to_filtered_search(uc_page, published, group, title, param):
    uc = _pick(published, f"{group}", lambda u: u[group])
    uc_page.open_detail(BASE_URL, uc["id"])
    labels = [(t["value"] if group == "tags" else t["name"]).strip() for t in uc[group]]
    labels = list(dict.fromkeys(label for label in labels if label))
    chips = uc_page.topic_chips(title)
    # The API does not promise an order, so compare as sets.
    shown = {}
    for text, href in chips:
        url = urlsplit(href)
        assert url.path == "/search" and parse_qs(url.query).keys() == {param, "types"} and parse_qs(url.query)["types"] == ["usecase"], f"{title} chip {text!r} links to {href}"
        shown[parse_qs(url.query)[param][0]] = text
    assert sorted(shown) == sorted(labels), f"use case {uc['id']}: {title} chips filter on {sorted(shown)}, expected {sorted(labels)}"
    for label, text in shown.items():
        assert (text.endswith(label) if group == "sdgs" else text == label), f"{title} chip reads {text!r}, expected {label!r}"
