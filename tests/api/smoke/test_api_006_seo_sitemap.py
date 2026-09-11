# tests/api/smoke/test_api_006_seo_sitemap.py
#
# Verify sitemap.xml / robots.txt structure, and that each dynamic child
# sitemap's <url> count matches the live backend count.
#
# Regression this guards: a prior bug swallowed GraphQL errors internally in
# the sitemap route handlers and silently defaulted the affected child
# sitemap to 0 urls instead of surfacing the failure.
#
# Backend cross-checks (GraphQL/REST count comparisons) only run against the
# environment API_BASE_URL actually points to (dev — see tests/api/conftest.py).
# Prod frontend coverage below is limited to structural/HTTP-level checks
# that don't require a prod backend URL, since none is configured in .env.

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

AI_MODELS_QUERY = "query{aiModels(filters:{isPublic:true,status:ACTIVE}){id}}"
PUBLISHED_USE_CASES_QUERY = "query{publishedUseCases{id}}"
PUBLISHED_COLLABORATIVES_QUERY = "query{publishedCollaboratives{id}}"
ACTIVE_SECTORS_QUERY = "query{activeSectors{id}}"
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
    """
    Every <url><loc> across ALL of an entity's child sitemaps.

    Counting only page 1 under-reports whenever the entity spans more than one
    page, which is the normal case on dev.
    """
    locs = []
    for page in _child_pages(index_xml, base_url).get(entity, []):
        resp = client.get(f"/sitemap/{entity}-{page}.xml")
        assert resp.status_code == 200, (
            f"{entity}-{page}.xml failed ({resp.status_code}): {resp.text}"
        )
        locs.extend(_url_locs(resp.text))
    return locs


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


# ─── sitemap.xml index (dev) ──────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.seo
def test_sitemap_index_returns_200(dev_frontend_client):
    """GET /sitemap.xml should return 200."""
    resp = dev_frontend_client.get("/sitemap.xml")
    assert resp.status_code == 200, f"sitemap.xml failed ({resp.status_code}): {resp.text}"


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_index_lists_expected_children(dev_frontend_client, frontend_base_url_dev):
    """
    sitemap.xml must start with static.xml, then cover every expected entity
    with contiguously numbered pages starting at 1.
    """
    resp = dev_frontend_client.get("/sitemap.xml")
    assert resp.status_code == 200
    _assert_index_shape(resp.text, frontend_base_url_dev)


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_legacy_main_redirects_to_index(dev_frontend_client):
    """GET /sitemap/main.xml (legacy path) must 308-redirect to /sitemap.xml."""
    resp = dev_frontend_client.get("/sitemap/main.xml", allow_redirects=False)
    assert resp.status_code == 308, f"Expected 308, got {resp.status_code}"
    assert resp.headers.get("Location", "").endswith("/sitemap.xml"), (
        f"Unexpected redirect target: {resp.headers.get('Location')}"
    )


# ─── static.xml (dev) ──────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.seo
def test_sitemap_static_urls_match_expected(dev_frontend_client, frontend_base_url_dev):
    """static.xml must contain exactly the 7 expected static page URLs."""
    resp = dev_frontend_client.get("/sitemap/static.xml")
    assert resp.status_code == 200, f"static.xml failed ({resp.status_code}): {resp.text}"
    locs = _url_locs(resp.text)
    expected = [f"{frontend_base_url_dev}{path}" for path in EXPECTED_STATIC_PATHS]
    assert locs == expected, f"static.xml URLs mismatch.\nGot:      {locs}\nExpected: {expected}"


# ─── robots.txt (dev) ──────────────────────────────────────────────────────────

@pytest.mark.api
@pytest.mark.seo
def test_robots_txt_references_sitemap(dev_frontend_client, frontend_base_url_dev):
    """robots.txt must contain a 'Sitemap: {base}/sitemap.xml' line."""
    resp = dev_frontend_client.get("/robots.txt")
    assert resp.status_code == 200, f"robots.txt failed ({resp.status_code}): {resp.text}"
    expected_line = f"Sitemap: {frontend_base_url_dev}/sitemap.xml"
    assert expected_line in resp.text, f"robots.txt missing '{expected_line}':\n{resp.text}"


# ─── dynamic sitemap counts vs. live backend (dev only) ───────────────────────
# API_BASE_URL in .env points at the dev backend, so these cross-checks can
# only be verified end-to-end against dev.

@pytest.mark.api
@pytest.mark.seo
@pytest.mark.xfail(
    strict=True,
    reason=(
        "DataSpaceFrontend#455 (closed won't-fix): on dev every aimodels-N.xml serves an "
        "empty urlset while the index advertises 5 pages, so all 21 public/active AI models "
        "are missing. Accepted because dev does not need SEO; prod is unaffected (15 urls) "
        "because it is unpaginated. strict=True on purpose — if this ever XPASSes, either "
        "dev was fixed or prod-like pagination changed, and both are worth knowing."
    ),
)
def test_sitemap_aimodels_count_matches_backend(dev_frontend_client, anon_graphql_client, frontend_base_url_dev):
    """Total aimodels sitemap urls must equal live count of public/active AI models."""
    index = dev_frontend_client.get("/sitemap.xml")
    assert index.status_code == 200
    locs = _all_entity_urls(dev_frontend_client, index.text, frontend_base_url_dev, "aimodels")
    backend_count = len(anon_graphql_client.query(AI_MODELS_QUERY).get("aiModels") or [])
    assert len(locs) == backend_count, (
        f"aimodels sitemaps have {len(locs)} urls across all pages, "
        f"backend has {backend_count} public/active AI models"
    )


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_usecases_count_matches_backend(dev_frontend_client, anon_graphql_client, frontend_base_url_dev):
    """Total usecases sitemap urls must equal live publishedUseCases count."""
    index = dev_frontend_client.get("/sitemap.xml")
    assert index.status_code == 200
    locs = _all_entity_urls(dev_frontend_client, index.text, frontend_base_url_dev, "usecases")
    backend_count = len(anon_graphql_client.query(PUBLISHED_USE_CASES_QUERY).get("publishedUseCases") or [])
    assert len(locs) == backend_count, (
        f"usecases sitemaps have {len(locs)} urls across all pages, "
        f"backend has {backend_count} published use cases"
    )


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_collaboratives_count_matches_backend(dev_frontend_client, anon_graphql_client, frontend_base_url_dev):
    """Total collaboratives sitemap urls must equal live publishedCollaboratives count."""
    index = dev_frontend_client.get("/sitemap.xml")
    assert index.status_code == 200
    locs = _all_entity_urls(dev_frontend_client, index.text, frontend_base_url_dev, "collaboratives")
    backend_count = len(
        anon_graphql_client.query(PUBLISHED_COLLABORATIVES_QUERY).get("publishedCollaboratives") or []
    )
    assert len(locs) == backend_count, (
        f"collaboratives sitemaps have {len(locs)} urls across all pages, "
        f"backend has {backend_count} published collaboratives"
    )


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_sectors_count_matches_backend(dev_frontend_client, anon_graphql_client, frontend_base_url_dev):
    """Total sectors sitemap urls must equal live activeSectors count."""
    index = dev_frontend_client.get("/sitemap.xml")
    assert index.status_code == 200
    locs = _all_entity_urls(dev_frontend_client, index.text, frontend_base_url_dev, "sectors")
    backend_count = len(anon_graphql_client.query(ACTIVE_SECTORS_QUERY).get("activeSectors") or [])
    assert len(locs) == backend_count, (
        f"sectors sitemaps have {len(locs)} urls across all pages, "
        f"backend has {backend_count} active sectors"
    )


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_organizations_and_users_counts_match_backend(
    dev_frontend_client, anon_graphql_client, frontend_base_url_dev
):
    """Total organizations/users sitemap urls must equal getPublishers split by __typename."""
    index = dev_frontend_client.get("/sitemap.xml")
    assert index.status_code == 200

    org_locs = _all_entity_urls(dev_frontend_client, index.text, frontend_base_url_dev, "organizations")
    user_locs = _all_entity_urls(dev_frontend_client, index.text, frontend_base_url_dev, "users")

    publishers = anon_graphql_client.query(PUBLISHERS_QUERY).get("getPublishers") or []
    org_backend_count = sum(1 for p in publishers if p.get("__typename") == "TypeOrganization")
    user_backend_count = sum(1 for p in publishers if p.get("__typename") == "TypeUser")

    assert len(org_locs) == org_backend_count, (
        f"organizations sitemaps have {len(org_locs)} urls across all pages, "
        f"backend has {org_backend_count} organizations"
    )
    assert len(user_locs) == user_backend_count, (
        f"users sitemaps have {len(user_locs)} urls across all pages, "
        f"backend has {user_backend_count} users"
    )


@pytest.mark.api
@pytest.mark.seo
def _dataset_search_total(anon_api_client):
    resp = anon_api_client.get(
        "/api/search/dataset/", params={"sort": "recent", "size": 1, "page": 1}
    )
    assert resp.status_code == 200, f"dataset search failed ({resp.status_code}): {resp.text}"
    return resp.json().get("total")


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_datasets_count_matches_backend(dev_frontend_client, anon_api_client, frontend_base_url_dev):
    """
    Total datasets sitemap urls must match the REST dataset search '.total'.

    Crawling ~28 child sitemaps takes several seconds and each one is a separate
    backend query, so a provider test creating or removing a dataset mid-crawl
    shifts the answer. Bracket the crawl with a total read before and after and
    require the url count to land inside that window: when the data is quiet the
    two reads are equal and this is an exact assertion, and when it is moving the
    test reports drift instead of failing on a race.
    """
    total_before = _dataset_search_total(anon_api_client)

    index = dev_frontend_client.get("/sitemap.xml")
    assert index.status_code == 200
    locs = _all_entity_urls(dev_frontend_client, index.text, frontend_base_url_dev, "datasets")

    total_after = _dataset_search_total(anon_api_client)
    low, high = min(total_before, total_after), max(total_before, total_after)

    assert len(set(locs)) == len(locs), (
        f"datasets sitemaps contain {len(locs) - len(set(locs))} duplicate url(s) across pages"
    )
    assert low <= len(locs) <= high, (
        f"datasets sitemaps have {len(locs)} urls across all pages, outside the backend "
        f"search total window [{low}, {high}] measured around the crawl"
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
