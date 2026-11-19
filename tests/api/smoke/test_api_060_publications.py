# tests/api/smoke/test_api_060_publications.py
#
# Covers DataSpaceFrontend#543: adds the consumer-facing Publications feature
# (a new entity, distinct from datasets/use cases/collaboratives) — a listing
# page at /publications and a detail page at /publications/<slug>. Neither
# route existed before this PR (both files are new), so dev serving them with
# real content is the regression this guards: before #543, every one of
# these URLs 404'd because the route did not exist.
#
# Public and unauthenticated: the backend's `publications` query requires no
# auth, and the consumer pages require no login. Records are read from the
# live API, never hardcoded. deployed_pr skips it until the frontend under
# test serves #543.

import re

import pytest

pytestmark = [
    pytest.mark.api,
    pytest.mark.smoke,
    pytest.mark.deployed_pr("DataSpaceFrontend#543", site="HOME_URL_DEV"),
]

PUBLICATIONS_QUERY = (
    "query{publications(includePublic:true, filters:{status:PUBLISHED}){id urlSlug}}"
)

# Every page (including Next.js's built-in not-found boundary) ships with the
# literal strings "404" / "could not be found" somewhere in its inert client
# JS, so checking for their absence in resp.text is a false-positive trap —
# every real page on this site "contains" them. The <title> tag is the signal
# that actually distinguishes a rendered record from a not-found fallback,
# matching the convention test_api_049_page_titles.py already uses for the
# same reason.
TITLE_RE = re.compile(r"<title>([^<]*)</title>")


def _title(resp):
    m = TITLE_RE.search(resp.text)
    return m.group(1).strip() if m else ""


@pytest.fixture(scope="module")
def published_publication(anon_graphql_client):
    body = anon_graphql_client.query(PUBLICATIONS_QUERY)
    records = body.get("publications") or []
    for record in records:
        if record.get("urlSlug"):
            return record
    pytest.skip("no published publication with a urlSlug on dev to test against")


def test_publications_listing_page_loads(dev_frontend_client):
    """GET /en/publications must serve the new listing route, not a 404.

    Before DataSpaceFrontend#543 this file did not exist at all, so the route
    fell through to Next.js's not-found page instead.
    """
    resp = dev_frontend_client.get("/en/publications")
    assert resp.status_code == 200, f"/en/publications failed ({resp.status_code}): {resp.text[:300]}"
    title = _title(resp)
    assert "publication" in title.lower(), f"/en/publications has an unexpected <title>: {title!r}"


def test_publication_detail_page_loads_with_its_own_title(dev_frontend_client, published_publication):
    """GET /en/publications/<slug> for a real published record must render its
    own title, not fall through to the not-found page or the listing page's title.

    Before DataSpaceFrontend#543 this route did not exist, so every slug 404'd.
    """
    slug = published_publication["urlSlug"]
    resp = dev_frontend_client.get(f"/en/publications/{slug}")
    assert resp.status_code == 200, f"/en/publications/{slug} failed ({resp.status_code}): {resp.text[:300]}"
    title = _title(resp)
    assert title, f"/en/publications/{slug} has an empty or missing <title>"

    listing_title = _title(dev_frontend_client.get("/en/publications"))
    assert title != listing_title, (
        f"/en/publications/{slug} shares the listing page's title ({title!r}) "
        "instead of rendering its own record"
    )
