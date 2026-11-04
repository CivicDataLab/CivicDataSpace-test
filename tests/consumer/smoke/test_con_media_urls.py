# tests/consumer/smoke/test_con_media_urls.py
#
# mediaUrl()/MediaImage coverage (DataSpaceFrontend PR #514, merged into dev
# 2026-11-03).
#
# Since the S3 storage migration, the API's logo/profilePicture fields return
# ABSOLUTE CloudFront URLs. Before #514, several components still built the
# <img src> by string-concatenating NEXT_PUBLIC_BACKEND_URL in front of that
# field (`${NEXT_PUBLIC_BACKEND_URL}/${logo.url}`), which silently
# double-prefixes an already-absolute URL into something the browser can't
# load, e.g.:
#   https://dev.api.civicdataspace.in/https://d19...cloudfront.net/....png
# mediaUrl() (lib/utils.ts) fixes this: an absolute URL passes through
# unchanged. This checks a real collaborative's logo renders with that exact
# unchanged URL, not the old double-prefixed one.
#
# No existing Page Object covered the /collaboratives listing's images, so
# this adds a minimal one (pages/consumer/collaboratives_page.py +
# locators/consumer/collaboratives_locators.py) rather than put a raw
# selector in the test.

import os

import pytest

from pages.consumer.collaboratives_page import CollaborativesPage
from tests.api.client import GraphQLClient

pytestmark = pytest.mark.smoke

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")
API_BASE_URL = os.getenv("API_BASE_URL", "https://dev.api.civicdataspace.in").rstrip("/")

COLLABORATIVES_QUERY = """
{ publishedCollaboratives {
    slug
    logo { url }
    organization { logo { url } }
    user { profilePicture { url } }
} }
"""


@pytest.fixture(scope="module")
def expected_absolute_media_urls():
    """Every absolute http(s) logo/profile-picture URL the API currently
    returns for a published collaborative, across the three fields the
    listing can render (collaborative logo, org logo, contributor avatar).

    The listing is paginated, so no single item is guaranteed to be on the
    first page — we match against whatever the page actually rendered
    instead of assuming one specific item is visible.
    """
    client = GraphQLClient(API_BASE_URL)
    data = client.query(COLLABORATIVES_QUERY)
    urls = set()
    for item in data["publishedCollaboratives"]:
        for url in (
            (item.get("logo") or {}).get("url"),
            ((item.get("organization") or {}).get("logo") or {}).get("url"),
            ((item.get("user") or {}).get("profilePicture") or {}).get("url"),
        ):
            if url and url.startswith(("http://", "https://")):
                urls.add(url)
    if not urls:
        pytest.skip("No published collaborative has an absolute media URL on dev")
    return urls


def test_con_media_001_collaborative_logos_are_not_double_prefixed(
    driver, expected_absolute_media_urls
):
    page = CollaborativesPage(driver).load(BASE_URL)
    rendered_srcs = {img.get_attribute("src") for img in page.list_image_srcs()}

    # At least one rendered image must be a real API URL, passed through
    # unchanged by mediaUrl() — otherwise this proves nothing about the fix.
    matched = rendered_srcs & expected_absolute_media_urls
    assert matched, (
        "Con_MEDIA_001: no <img> on /collaboratives matched any of the "
        f"{len(expected_absolute_media_urls)} absolute media URLs the API "
        "returned — mediaUrl() may be mutating an already-absolute URL"
    )

    # The literal pre-#514 formula: NEXT_PUBLIC_BACKEND_URL + '/' + the field.
    # None of the API's absolute URLs should appear in that double-prefixed
    # form anywhere on the page.
    broken_variants = {f"{API_BASE_URL}/{u}" for u in expected_absolute_media_urls}
    broken_rendered = rendered_srcs & broken_variants
    assert not broken_rendered, (
        "Con_MEDIA_001: found the pre-#514 double-prefixed URL form rendered "
        f"on /collaboratives: {broken_rendered}"
    )
