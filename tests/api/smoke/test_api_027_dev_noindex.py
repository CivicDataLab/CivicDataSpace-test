# tests/api/smoke/test_api_027_dev_noindex.py
#
# Dev must be hidden from search engines (DataSpaceFrontend#493): no sitemap,
# no Sitemap line in robots.txt, and an X-Robots-Tag noindex header.
#
# Deliberately NOT `readonly`: in the prod gate HOME_URL_DEV is set to the prod
# site, so these would assert noindex on prod (failed the 2026-10-09 release,
# DataSpaceFrontend run 37926239517). `smoke` runs them in dev gates instead.

import pytest

pytestmark = [pytest.mark.api, pytest.mark.smoke, pytest.mark.seo]


@pytest.mark.deployed_pr("DataSpaceFrontend#493", site="HOME_URL_DEV")
def test_dev_sends_noindex_header(dev_frontend_client):
    """Every dev page must carry X-Robots-Tag: noindex so search engines drop it."""
    resp = dev_frontend_client.get("/")
    tag = resp.headers.get("X-Robots-Tag", "")
    assert "noindex" in tag, f"dev / missing X-Robots-Tag noindex, got: {tag!r}"


@pytest.mark.deployed_pr("DataSpaceFrontend#493", site="HOME_URL_DEV")
def test_dev_sitemap_is_disabled(dev_frontend_client):
    """dev /sitemap.xml must 404 and robots.txt must not advertise a sitemap."""
    resp = dev_frontend_client.get("/sitemap.xml")
    assert resp.status_code == 404, f"dev sitemap.xml should be 404, got {resp.status_code}"

    robots = dev_frontend_client.get("/robots.txt")
    assert robots.status_code == 200, f"robots.txt failed ({robots.status_code}): {robots.text}"
    assert "Sitemap:" not in robots.text, f"dev robots.txt still advertises a sitemap:\n{robots.text}"
