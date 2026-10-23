# tests/api/smoke/test_api_028_legacy_media_redirect.py
#
# Pending coverage for DataSpaceBackend#249 ("feat(storage): move media to S3
# and remove DVC versioning"), still open on `dev` as of this run.
#
# The PR replaces the old `/public/<name>` static-file route (Django's
# `static()`, serving MEDIA_ROOT off local disk, open in DEBUG) with a
# dedicated `legacy_media_redirect` view (api/views/legacy_media.py):
#   - A missing/non-existent public file now 404s with a small JSON body
#     (`{"error": "Not found"}`), not Django's HTML "technical 404" page.
#   - A name that normalizes to something outside the current directory
#     (path traversal) also 404s with that same JSON body, before storage
#     is ever consulted.
#
# Confirmed directly against the PR diff (DataSpace/urls.py,
# api/views/legacy_media.py, api/utils/storage.py) in DataSpaceBackend, not
# from the PR title/description.
#
# Gated with `pending_pr`: #249 is open, not merged, so this must not run
# unguarded. Never `readonly` — a pending test must not run in the prod gate.
#
# UNVERIFIED — green not executed anywhere: DataSpaceBackend cannot be run in
# this sandbox (no Postgres/Redis/Elasticsearch/Keycloak/S3 available), so the
# post-merge JSON-404 behaviour has only been read from the diff, never run.
# The red assertions below *were* executed, against the real dev backend,
# which still serves the pre-#249 code.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.pending_pr("DataSpaceBackend#249")]


def test_missing_public_file_404s_as_json_not_django_html(anon_api_client):
    """Pre-#249: a missing /public/<name> 404s with Django's HTML debug page.

    Post-#249 (UNVERIFIED — not executed, no deployable backend in this
    sandbox): legacy_media_redirect returns a small JSON 404 instead
    (`{"error": "Not found"}`), since the route no longer serves local disk.
    A human should re-run this once #249 is on dev and drop this comment.
    """
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
