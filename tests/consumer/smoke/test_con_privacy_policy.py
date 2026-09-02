# tests/consumer/smoke/test_con_privacy_policy.py
#
# Privacy policy page smoke coverage (DataSpaceFrontend PR #444).
#
# /privacy is the canonical path: the locale-prefixed /en/privacy
# 307-redirects to it, so every assertion here targets /privacy.

import os

import pytest

from pages.consumer.privacy_page import PRIVACY_PATH, PrivacyPage

pytestmark = pytest.mark.smoke

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")

# Substrings any real privacy policy should contain somewhere in its body.
# Kept generic so ordinary copy edits don't break the test.
EXPECTED_KEYWORDS = ("privacy", "data")


@pytest.fixture
def privacy_page(driver):
    return PrivacyPage(driver).load(BASE_URL)


def test_privacy_page_loads(privacy_page):
    """/privacy must resolve without bouncing away to another route."""
    url = privacy_page.current_path()
    assert PRIVACY_PATH in url, (
        f"Expected to land on {PRIVACY_PATH}, ended up at {url!r}"
    )


def test_privacy_page_has_heading(privacy_page):
    """The page must render a non-empty top-level heading."""
    heading = privacy_page.heading_text()
    assert heading, (
        f"{BASE_URL}{PRIVACY_PATH} rendered no <h1> text — the page loaded "
        "but has no heading"
    )


def test_privacy_page_renders_meaningful_content(privacy_page):
    """
    The body must carry real policy copy, not an empty shell or an error
    page. Guards against the route existing but rendering nothing.
    """
    text = privacy_page.main_text()
    assert len(text) > 200, (
        f"{BASE_URL}{PRIVACY_PATH} main content is only {len(text)} chars — "
        f"expected substantial policy text. Got: {text[:200]!r}"
    )
    lowered = text.lower()
    missing = [kw for kw in EXPECTED_KEYWORDS if kw not in lowered]
    assert not missing, (
        f"Privacy policy content is missing expected keyword(s) {missing} — "
        f"got: {text[:300]!r}"
    )
