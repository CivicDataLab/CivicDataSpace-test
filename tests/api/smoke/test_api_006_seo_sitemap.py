# tests/api/smoke/test_api_006_seo_sitemap.py
#
# Prod: verify sitemap.xml / robots.txt structure and that pages are indexable.
# Dev: verify the site is hidden from search engines (DataSpaceFrontend#493):
# no sitemap, no Sitemap line in robots.txt, and an X-Robots-Tag noindex header.
#
# Dev sitemap <url> counts used to be cross-checked against the backend here;
# those checks went away with the dev sitemap. Prod has no backend URL
# configured in .env, so it only gets structural/HTTP-level checks.

import re
import xml.etree.ElementTree as ET

import pytest

pytestmark = pytest.mark.readonly

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

# The sitemap index is paginated: each entity is split into
# `FEATURE_SITEMAP_ITEMS_PER_PAGE`-sized child sitemaps named `<entity>-<n>.xml`,
# so the number of children per entity varies with the live data volume (dev
# currently runs a page size of 5, prod uses the 1000 default and so has a
# single page per entity). Assert the entity set and page contiguity, never a
# hardcoded file list.
EXPECTED_SITEMAP_ENTITIES = [
    "datasets",
    "aimodels",
    "usecases",
    "collaboratives",
    "organizations",
    "users",
    "sectors",
]

EXPECTED_STATIC_PATHS = ["", "/datasets", "/usecases", "/collaboratives", "/publishers", "/sectors", "/about-us"]

def _sitemap_locs(xml_text):
    """<sitemap><loc> entries from a sitemapindex document."""
    root = ET.fromstring(xml_text)
    return [el.text for el in root.findall("sm:sitemap/sm:loc", SITEMAP_NS)]


def _url_locs(xml_text):
    """<url><loc> entries from a urlset document."""
    root = ET.fromstring(xml_text)
    return [el.text for el in root.findall("sm:url/sm:loc", SITEMAP_NS)]


def _child_pages(index_xml, base_url):
    """
    Map entity name -> ordered page numbers, parsed from the sitemap index.

    "https://host/sitemap/datasets-3.xml" -> pages["datasets"] contains 3.
    static.xml is not an entity and is skipped.
    """
    pages = {}
    for loc in _sitemap_locs(index_xml):
        m = re.match(rf"^{re.escape(base_url)}/sitemap/([a-zA-Z0-9_]+)-(\d+)\.xml$", loc)
        if m:
            pages.setdefault(m.group(1), []).append(int(m.group(2)))
    return {k: sorted(v) for k, v in pages.items()}


def _assert_index_shape(index_xml, base_url):
    """static.xml first, every expected entity present, pages contiguous from 1."""
    locs = _sitemap_locs(index_xml)
    assert locs and locs[0] == f"{base_url}/sitemap/static.xml", (
        f"Expected static.xml first, got: {locs[:1]}"
    )

    pages = _child_pages(index_xml, base_url)
    assert sorted(pages) == sorted(EXPECTED_SITEMAP_ENTITIES), (
        f"Entity mismatch.\nGot:      {sorted(pages)}\nExpected: {sorted(EXPECTED_SITEMAP_ENTITIES)}"
    )
    for entity, nums in pages.items():
        assert nums == list(range(1, len(nums) + 1)), (
            f"{entity} pages are not contiguous from 1: {nums}"
        )


# ─── prod structural checks (no prod backend configured to cross-check counts) ─

@pytest.mark.api
@pytest.mark.seo
def test_prod_sitemap_index_returns_200(prod_frontend_client):
    """GET /sitemap.xml on prod should return 200."""
    resp = prod_frontend_client.get("/sitemap.xml")
    assert resp.status_code == 200, f"prod sitemap.xml failed ({resp.status_code}): {resp.text}"


@pytest.mark.api
@pytest.mark.seo
def test_prod_sitemap_index_lists_expected_children(prod_frontend_client, frontend_base_url_prod):
    """prod sitemap.xml must have the same shape: static.xml + contiguous entity pages."""
    resp = prod_frontend_client.get("/sitemap.xml")
    assert resp.status_code == 200
    _assert_index_shape(resp.text, frontend_base_url_prod)


@pytest.mark.api
@pytest.mark.seo
def test_prod_sitemap_legacy_main_redirects_to_index(prod_frontend_client):
    """GET /sitemap/main.xml (legacy path) on prod must 308-redirect to /sitemap.xml."""
    resp = prod_frontend_client.get("/sitemap/main.xml", allow_redirects=False)
    assert resp.status_code == 308, f"Expected 308, got {resp.status_code}"
    assert resp.headers.get("Location", "").endswith("/sitemap.xml"), (
        f"Unexpected redirect target: {resp.headers.get('Location')}"
    )


@pytest.mark.api
@pytest.mark.seo
def test_prod_sitemap_static_urls_match_expected(prod_frontend_client, frontend_base_url_prod):
    """prod static.xml must contain exactly the 7 expected static page URLs."""
    resp = prod_frontend_client.get("/sitemap/static.xml")
    assert resp.status_code == 200, f"prod static.xml failed ({resp.status_code}): {resp.text}"
    locs = _url_locs(resp.text)
    expected = [f"{frontend_base_url_prod}{path}" for path in EXPECTED_STATIC_PATHS]
    assert locs == expected, f"prod static.xml URLs mismatch.\nGot:      {locs}\nExpected: {expected}"


@pytest.mark.api
@pytest.mark.seo
def test_prod_robots_txt_references_sitemap(prod_frontend_client, frontend_base_url_prod):
    """prod robots.txt must contain a 'Sitemap: {base}/sitemap.xml' line."""
    resp = prod_frontend_client.get("/robots.txt")
    assert resp.status_code == 200, f"prod robots.txt failed ({resp.status_code}): {resp.text}"
    expected_line = f"Sitemap: {frontend_base_url_prod}/sitemap.xml"
    assert expected_line in resp.text, f"prod robots.txt missing '{expected_line}':\n{resp.text}"
