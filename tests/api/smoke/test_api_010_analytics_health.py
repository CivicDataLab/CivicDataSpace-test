# tests/api/smoke/test_api_010_analytics_health.py
#
# Coverage for the Analytics (dashboard-superset) deploy pipeline landed
# 2026-09-16 (dashboard-superset#5, closes the analytics leg of DataSpace#205).
# Both dev and prod went from "no CI pipeline at all" to a working one that
# night, so this suite exists to catch the pipeline silently deploying a
# broken or stale build in the future -- nothing here existed before.
#
# Every check is a plain unauthenticated GET. That's deliberate, not
# incidental: this repo's convention is read-only checks against prod,
# anything against dev -- and every assertion below happens to need nothing
# else anyway, so there's no write-vs-read split to maintain per environment.
#
# Parametrized across both environments explicitly (ANALYTICS_URL_DEV /
# ANALYTICS_URL_PROD, see conftest.py) rather than driven by a single
# API_BASE_URL -- analytics has two fixed, always-both-relevant targets, not
# one environment selected per CI run.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke]


@pytest.fixture(params=["dev", "prod"])
def analytics_client(request, dev_analytics_client, prod_analytics_client):
    """Runs the tests in this file against both environments, by name in -v output."""
    return {"dev": dev_analytics_client, "prod": prod_analytics_client}[request.param]


def test_health_endpoint_returns_ok(analytics_client):
    """Superset's built-in /health liveness check.

    This is the simplest possible thing that can be wrong after a deploy --
    if this doesn't return 200/"OK", nothing else on the box is worth
    checking. Confirmed live 2026-09-16 on both environments before writing
    this assertion.
    """
    resp = analytics_client.get("/health")
    assert resp.status_code == 200, (
        f"/health returned {resp.status_code}, expected 200: {resp.text[:200]}"
    )
    assert resp.text.strip() == "OK", (
        f"/health body was {resp.text[:200]!r}, expected exactly 'OK'"
    )


def test_login_page_reports_keycloak_oauth(analytics_client):
    """The login page's bootstrap payload must advertise Keycloak OAuth.

    Regression guard for the auth move referenced in dashboard-superset#5's
    own scope ("Analytics already moved to auth.civicdatalab.in in Sprint 3
    ... dashboard-superset#4"). AUTH_TYPE 4 is Superset's AUTH_OAUTH constant;
    a value of 1 (AUTH_DB, Superset's built-in username/password login) would
    mean OAuth silently fell back to local accounts -- exactly the kind of
    thing a config regression in a future deploy could cause without any
    other visible symptom.

    Doesn't assert the actual Keycloak issuer hostname: the login page's
    server-rendered HTML only names the provider, not the authorize URL
    (confirmed live -- /login/keycloak/, /oauth-authorize/keycloak, and
    /login/authorized/keycloak were all tried and all 404). Asserting a
    provider name we've actually seen beats guessing a redirect target we
    haven't.
    """
    resp = analytics_client.get("/login/")
    assert resp.status_code == 200, f"/login/ returned {resp.status_code}"

    bootstrap = _extract_bootstrap_json(resp.text)
    conf = bootstrap["common"]["conf"]

    assert conf.get("AUTH_TYPE") == 4, (
        f"AUTH_TYPE is {conf.get('AUTH_TYPE')!r}, expected 4 (AUTH_OAUTH) -- "
        "login may have fallen back to Superset's local username/password auth"
    )
    provider_names = [p.get("name") for p in conf.get("AUTH_PROVIDERS", [])]
    assert "keycloak" in provider_names, (
        f"AUTH_PROVIDERS was {provider_names}, expected 'keycloak' to be present"
    )


def test_reports_the_deployed_superset_version(analytics_client):
    """The deployed build must actually be the v6 image, not a stale fallback.

    Direct regression coverage for the exact thing the 2026-09-16 deploy
    pipeline work was verifying end to end: that a real, current image made
    it onto both boxes, not just that *a* container is running. version_string
    is Flask-AppBuilder's own reported app version, read from the same
    bootstrap payload as the auth check above.
    """
    resp = analytics_client.get("/login/")
    bootstrap = _extract_bootstrap_json(resp.text)
    version = bootstrap["common"]["menu_data"].get("navbar_right", {}).get("version_string", "")

    assert version.startswith("6."), (
        f"Reported Superset version is {version!r}, expected a 6.x release "
        "(akritisingh11/superset-custom:v6) -- the deploy may have rolled back "
        "to a stale image or pulled the wrong tag"
    )


def _extract_bootstrap_json(html: str) -> dict:
    """Pull Superset's `data-bootstrap="{...}"` attribute out of the raw page HTML.

    The value is server-side HTML-escaped (Flask/Jinja `|e`), not JS-escaped
    -- `html.unescape` before `json.loads`, not a JS string-literal decode.
    """
    import html as html_module
    import json
    import re

    match = re.search(r'data-bootstrap="([^"]*)"', html)
    assert match, "Could not find data-bootstrap attribute in the page HTML at all"
    return json.loads(html_module.unescape(match.group(1)))
