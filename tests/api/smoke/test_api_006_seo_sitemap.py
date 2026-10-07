# tests/api/smoke/test_api_006_seo_sitemap.py
#
# Prod: verify sitemap.xml / robots.txt structure and that pages are indexable.
# Dev: verify the site is hidden from search engines (DataSpaceFrontend#493):
# no sitemap, no Sitemap line in robots.txt, and an X-Robots-Tag noindex header.
#
# Each prod child sitemap's <url> count is cross-checked against the live prod
# backend (API_BASE_URL_PROD). Regression this guards: a prior bug swallowed
# GraphQL errors in the sitemap route handlers and silently served 0 urls.

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

PUBLISHERS_QUERY = (
    "query{getPublishers{__typename ... on TypeOrganization{id} ... on TypeUser{id}}}"
)

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


def _all_entity_urls(client, index_xml, base_url, entity):
    """Every <url><loc> across ALL of an entity's child sitemaps."""
    locs = []
    for page in _child_pages(index_xml, base_url).get(entity, []):
        resp = client.get(f"/sitemap/{entity}-{page}.xml")
        assert resp.status_code == 200, (
            f"{entity}-{page}.xml failed ({resp.status_code}): {resp.text}"
        )
        locs.extend(_url_locs(resp.text))
    return locs


def _dataset_search_total(api_client):
    resp = api_client.get("/api/search/dataset/", params={"sort": "recent", "size": 1, "page": 1})
    assert resp.status_code == 200, f"dataset search failed ({resp.status_code}): {resp.text}"
    return resp.json().get("total")


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


# ─── dev must not be indexed ──────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.seo
@pytest.mark.deployed_pr("DataSpaceFrontend#493", workflow="deploy-Dataspace.yml")
def test_dev_sends_noindex_header(dev_frontend_client):
    """Every dev page must carry X-Robots-Tag: noindex so search engines drop it."""
    resp = dev_frontend_client.get("/")
    tag = resp.headers.get("X-Robots-Tag", "")
    assert "noindex" in tag, f"dev / missing X-Robots-Tag noindex, got: {tag!r}"


@pytest.mark.api
@pytest.mark.seo
@pytest.mark.deployed_pr("DataSpaceFrontend#493", workflow="deploy-Dataspace.yml")
def test_dev_sitemap_is_disabled(dev_frontend_client):
    """dev /sitemap.xml must 404 and robots.txt must not advertise a sitemap."""
    resp = dev_frontend_client.get("/sitemap.xml")
    assert resp.status_code == 404, f"dev sitemap.xml should be 404, got {resp.status_code}"

    robots = dev_frontend_client.get("/robots.txt")
    assert robots.status_code == 200, f"robots.txt failed ({robots.status_code}): {robots.text}"
    assert "Sitemap:" not in robots.text, f"dev robots.txt still advertises a sitemap:\n{robots.text}"


# ─── prod structural checks (no prod backend configured to cross-check counts) ─

@pytest.mark.api
@pytest.mark.seo
def test_prod_is_indexable(prod_frontend_client):
    """prod must never send the noindex header that dev gets."""
    resp = prod_frontend_client.get("/")
    assert resp.status_code == 200, f"prod / failed ({resp.status_code})"
    tag = resp.headers.get("X-Robots-Tag", "")
    assert "noindex" not in tag, f"prod / is marked noindex: {tag!r}"


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


# ─── prod sitemap counts vs. live prod backend ────────────────────────────────

@pytest.mark.api
@pytest.mark.seo
@pytest.mark.parametrize("entity, query, key", [
    pytest.param(
        "aimodels", "query{aiModels(filters:{isPublic:true,status:ACTIVE}){id}}", "aiModels",
        # prod serves 0 aimodels urls until the numeric-id fix ships to prod
        marks=pytest.mark.deployed_pr("DataSpaceFrontend#495", workflow="deploy-Dataspace.yml", branch="main"),
    ),
    ("usecases", "query{publishedUseCases{id}}", "publishedUseCases"),
    ("collaboratives", "query{publishedCollaboratives{id}}", "publishedCollaboratives"),
    ("sectors", "query{activeSectors{id}}", "activeSectors"),
])
def test_prod_sitemap_count_matches_backend(
    entity, query, key, prod_frontend_client, frontend_base_url_prod, anon_graphql_client_prod
):
    """Total <entity> sitemap urls on prod must equal the live prod backend count."""
    index = prod_frontend_client.get("/sitemap.xml")
    assert index.status_code == 200
    locs = _all_entity_urls(prod_frontend_client, index.text, frontend_base_url_prod, entity)
    backend_count = len(anon_graphql_client_prod.query(query).get(key) or [])
    assert len(locs) == backend_count, (
        f"prod {entity} sitemaps have {len(locs)} urls, prod backend has {backend_count}"
    )


@pytest.mark.api
@pytest.mark.seo
def test_prod_sitemap_organizations_and_users_counts_match_backend(
    prod_frontend_client, frontend_base_url_prod, anon_graphql_client_prod
):
    """prod organizations/users sitemap urls must equal getPublishers split by __typename."""
    index = prod_frontend_client.get("/sitemap.xml")
    assert index.status_code == 200
    publishers = anon_graphql_client_prod.query(PUBLISHERS_QUERY).get("getPublishers") or []
    for entity, typename in (("organizations", "TypeOrganization"), ("users", "TypeUser")):
        locs = _all_entity_urls(prod_frontend_client, index.text, frontend_base_url_prod, entity)
        backend_count = sum(1 for p in publishers if p.get("__typename") == typename)
        assert len(locs) == backend_count, (
            f"prod {entity} sitemaps have {len(locs)} urls, prod backend has {backend_count}"
        )


@pytest.mark.api
@pytest.mark.seo
def test_prod_sitemap_datasets_count_matches_backend(
    prod_frontend_client, frontend_base_url_prod, anon_api_client_prod
):
    """
    prod datasets sitemap urls must match the prod REST dataset search '.total'.

    The total is read before and after the crawl, and the url count must land
    inside that window, so a dataset published mid-crawl reports drift instead
    of failing on a race.
    """
    total_before = _dataset_search_total(anon_api_client_prod)
    index = prod_frontend_client.get("/sitemap.xml")
    assert index.status_code == 200
    locs = _all_entity_urls(prod_frontend_client, index.text, frontend_base_url_prod, "datasets")
    total_after = _dataset_search_total(anon_api_client_prod)
    low, high = min(total_before, total_after), max(total_before, total_after)

    assert len(set(locs)) == len(locs), (
        f"prod datasets sitemaps contain {len(locs) - len(set(locs))} duplicate url(s)"
    )
    assert low <= len(locs) <= high, (
        f"prod datasets sitemaps have {len(locs)} urls, outside the backend search "
        f"total window [{low}, {high}] measured around the crawl"
    )
