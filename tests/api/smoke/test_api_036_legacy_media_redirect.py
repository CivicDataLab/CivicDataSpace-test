# tests/api/smoke/test_api_036_legacy_media_redirect.py
#
# Covers DataSpaceBackend#249 (merge 42bfef40, live on dev): the old
# `/public/<name>` static-file route is replaced by `legacy_media_redirect`
# (api/views/legacy_media.py). A missing public file, or a name that
# normalizes outside the directory (path traversal), now 404s with a small
# JSON body (`{"error": "Not found"}`) instead of Django's HTML 404.
#
# Gated with `deployed_pr`, not `readonly`: it skips wherever the backend
# under test does not yet serve #249 (prod, until release).

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.deployed_pr("DataSpaceBackend#249")]


def test_missing_public_file_404s_as_json_not_django_html(anon_api_client):
    """A missing /public/<name> 404s as JSON from the legacy_media view."""
    resp = anon_api_client.get("/public/does-not-exist-pr249-probe.png")
    assert resp.status_code == 404, (
        f"expected 404 for a missing legacy media path, got {resp.status_code}: {resp.text[:200]}"
    )
    content_type = resp.headers.get("Content-Type", "")
    assert "application/json" in content_type, (
        "expected the new legacy_media view's JSON 404 "
        f"(Content-Type: application/json), got {content_type!r}. "
        "This is the pre-#249 Django static()/debug-404 page, not the PR's view."
    )
    assert resp.json() == {"error": "Not found"}, resp.text[:200]


def test_public_file_name_with_path_traversal_404s_as_json(anon_api_client):
    """A name that normalizes outside the directory must 404 as JSON too.

    `legacy_media_redirect` rejects any name whose `posixpath.normpath` isn't
    the name itself before ever touching storage (api/views/legacy_media.py).
    Uses a traversal payload nginx passes through unmodified (double-encoded
    dot-segments collapse at the edge before reaching Django on this stack,
    confirmed separately), so the check exercises the Django view, not nginx.
    """
    resp = anon_api_client.get("/public/..%252f..%252fetc%252fpasswd")
    assert resp.status_code == 404, (
        f"expected 404 for a path-traversal legacy media name, got {resp.status_code}: "
        f"{resp.text[:200]}"
    )
    content_type = resp.headers.get("Content-Type", "")
    assert "application/json" in content_type, (
        f"expected the new legacy_media view's JSON 404, got {content_type!r} "
        f"(body: {resp.text[:200]})"
    )
