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

import xml.etree.ElementTree as ET

import pytest

SITEMAP_NS = {"sm": "http://www.sitemaps.org/schemas/sitemap/0.9"}

EXPECTED_CHILD_SITEMAPS = [
    "sitemap/static.xml",
    "sitemap/datasets-1.xml",
    "sitemap/aimodels-1.xml",
    "sitemap/usecases-1.xml",
    "sitemap/collaboratives-1.xml",
    "sitemap/organizations-1.xml",
    "sitemap/users-1.xml",
    "sitemap/sectors-1.xml",
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
    """sitemap.xml must list exactly the 8 expected child sitemaps, in order."""
    resp = dev_frontend_client.get("/sitemap.xml")
    assert resp.status_code == 200
    locs = _sitemap_locs(resp.text)
    expected = [f"{frontend_base_url_dev}/{path}" for path in EXPECTED_CHILD_SITEMAPS]
    assert locs == expected, f"Child sitemap list mismatch.\nGot:      {locs}\nExpected: {expected}"


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
def test_sitemap_aimodels_count_matches_backend(dev_frontend_client, anon_graphql_client):
    """aimodels-1.xml url count must equal live count of public/active AI models."""
    resp = dev_frontend_client.get("/sitemap/aimodels-1.xml")
    assert resp.status_code == 200, f"aimodels-1.xml failed ({resp.status_code}): {resp.text}"
    sitemap_count = len(_url_locs(resp.text))
    backend_count = len(anon_graphql_client.query(AI_MODELS_QUERY).get("aiModels") or [])
    assert sitemap_count == backend_count, (
        f"aimodels-1.xml has {sitemap_count} urls, backend has {backend_count} public/active AI models"
    )


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_usecases_count_matches_backend(dev_frontend_client, anon_graphql_client):
    """usecases-1.xml url count must equal live publishedUseCases count."""
    resp = dev_frontend_client.get("/sitemap/usecases-1.xml")
    assert resp.status_code == 200, f"usecases-1.xml failed ({resp.status_code}): {resp.text}"
    sitemap_count = len(_url_locs(resp.text))
    backend_count = len(anon_graphql_client.query(PUBLISHED_USE_CASES_QUERY).get("publishedUseCases") or [])
    assert sitemap_count == backend_count, (
        f"usecases-1.xml has {sitemap_count} urls, backend has {backend_count} published use cases"
    )


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_collaboratives_count_matches_backend(dev_frontend_client, anon_graphql_client):
    """collaboratives-1.xml url count must equal live publishedCollaboratives count."""
    resp = dev_frontend_client.get("/sitemap/collaboratives-1.xml")
    assert resp.status_code == 200, f"collaboratives-1.xml failed ({resp.status_code}): {resp.text}"
    sitemap_count = len(_url_locs(resp.text))
    backend_count = len(
        anon_graphql_client.query(PUBLISHED_COLLABORATIVES_QUERY).get("publishedCollaboratives") or []
    )
    assert sitemap_count == backend_count, (
        f"collaboratives-1.xml has {sitemap_count} urls, backend has {backend_count} published collaboratives"
    )


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_sectors_count_matches_backend(dev_frontend_client, anon_graphql_client):
    """sectors-1.xml url count must equal live activeSectors count."""
    resp = dev_frontend_client.get("/sitemap/sectors-1.xml")
    assert resp.status_code == 200, f"sectors-1.xml failed ({resp.status_code}): {resp.text}"
    sitemap_count = len(_url_locs(resp.text))
    backend_count = len(anon_graphql_client.query(ACTIVE_SECTORS_QUERY).get("activeSectors") or [])
    assert sitemap_count == backend_count, (
        f"sectors-1.xml has {sitemap_count} urls, backend has {backend_count} active sectors"
    )


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_organizations_and_users_counts_match_backend(dev_frontend_client, anon_graphql_client):
    """organizations-1.xml / users-1.xml url counts must equal getPublishers split by __typename."""
    org_resp = dev_frontend_client.get("/sitemap/organizations-1.xml")
    user_resp = dev_frontend_client.get("/sitemap/users-1.xml")
    assert org_resp.status_code == 200, f"organizations-1.xml failed ({org_resp.status_code}): {org_resp.text}"
    assert user_resp.status_code == 200, f"users-1.xml failed ({user_resp.status_code}): {user_resp.text}"

    org_sitemap_count = len(_url_locs(org_resp.text))
    user_sitemap_count = len(_url_locs(user_resp.text))

    publishers = anon_graphql_client.query(PUBLISHERS_QUERY).get("getPublishers") or []
    org_backend_count = sum(1 for p in publishers if p.get("__typename") == "TypeOrganization")
    user_backend_count = sum(1 for p in publishers if p.get("__typename") == "TypeUser")

    assert org_sitemap_count == org_backend_count, (
        f"organizations-1.xml has {org_sitemap_count} urls, backend has {org_backend_count} organizations"
    )
    assert user_sitemap_count == user_backend_count, (
        f"users-1.xml has {user_sitemap_count} urls, backend has {user_backend_count} users"
    )


@pytest.mark.api
@pytest.mark.seo
def test_sitemap_datasets_count_matches_backend(dev_frontend_client, anon_api_client):
    """datasets-1.xml url count must equal the REST dataset search '.total' field."""
    resp = dev_frontend_client.get("/sitemap/datasets-1.xml")
    assert resp.status_code == 200, f"datasets-1.xml failed ({resp.status_code}): {resp.text}"
    sitemap_count = len(_url_locs(resp.text))

    search_resp = anon_api_client.get(
        "/api/search/dataset/", params={"sort": "recent", "size": 1, "page": 1}
    )
    assert search_resp.status_code == 200, (
        f"dataset search failed ({search_resp.status_code}): {search_resp.text}"
    )
    backend_total = search_resp.json().get("total")
    assert sitemap_count == backend_total, (
        f"datasets-1.xml has {sitemap_count} urls, backend search total is {backend_total}"
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
    """prod sitemap.xml must list exactly the 8 expected child sitemaps, in order."""
    resp = prod_frontend_client.get("/sitemap.xml")
    assert resp.status_code == 200
    locs = _sitemap_locs(resp.text)
    expected = [f"{frontend_base_url_prod}/{path}" for path in EXPECTED_CHILD_SITEMAPS]
    assert locs == expected, f"Child sitemap list mismatch.\nGot:      {locs}\nExpected: {expected}"


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
