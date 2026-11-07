# tests/api/smoke/test_api_026_publications_route_public.py
#
# The Resources (Publications) explore + detail pages (DataSpaceFrontend
# PR #420) are meant to be public, peer to /datasets, /usecases,
# /collaboratives and /aimodels -- all of which middleware.ts allowlists in
# `publicPages`. #420 adds the pages but, reading its real diff (not its
# description), never touches middleware.ts: /publications and
# /publications/<id> are NOT in that allowlist, so an anonymous visitor would
# be redirected to /login instead of seeing the page.
#
# pending_pr: dev does not have this route at all yet (#420 is still open),
# so dev correctly 307s to /login today -- that is the expected "not merged"
# state, not the bug. See this PR's body for the full finding: the same
# redirect currently also happens against PR #420's own head, because of the
# missing middleware.ts entries above. That is a real gap in #420 itself, not
# something fixable from this test repo -- flagged for the PR author/reviewer.

import pytest

pytestmark = [pytest.mark.smoke, pytest.mark.pending_pr("DataSpaceFrontend#420")]

REDIRECT_STATUSES = (301, 302, 303, 307, 308)


def test_publications_explore_page_is_reachable_without_login(dev_frontend_client):
    resp = dev_frontend_client.get("/publications", allow_redirects=False)
    assert resp.status_code not in REDIRECT_STATUSES, (
        f"/publications redirected ({resp.status_code} -> {resp.headers.get('location')}) "
        "instead of serving the page directly. If this points at /login, the Resources "
        "explore page is gated behind auth -- contradicting PR #420's own description "
        "of it as a public page (middleware.ts's publicPages list is missing the entry)."
    )
    assert resp.status_code == 200, f"/publications returned {resp.status_code}, not 200"
    assert "Resource" in resp.text, "expected Resources-listing content not found in the response"


def test_publications_detail_route_is_reachable_without_login(dev_frontend_client):
    # A nonexistent id is deliberate: this only checks the route isn't
    # auth-gated, not that any specific resource renders. A 404/not-found
    # page is fine; a redirect to /login is not.
    resp = dev_frontend_client.get("/publications/999999999", allow_redirects=False)
    assert resp.status_code not in REDIRECT_STATUSES, (
        f"/publications/<id> redirected ({resp.status_code} -> {resp.headers.get('location')}) "
        "instead of serving the page directly."
    )
