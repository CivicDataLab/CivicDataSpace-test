# tests/consumer/smoke/test_con_auth_request_volume.py
#
# Guards against the NextAuth signout loop.
#
# On 2026-09-03 a single client issued 228,211 requests in a day - peaking at
# 6,230 per minute - to /api/auth/session, /api/auth/csrf and
# /api/auth/signout. It exhausted the backend's per-IP rate limit (1000/hour for
# non-GET) and returned 429s to every other user behind the same NAT address.
#
# The cause was a loop between two pieces of the frontend: the NextAuth jwt
# callback returned a token still carrying RefreshAccessTokenError and a stale
# expires_at, so every session fetch retried a refresh that could not succeed;
# and SessionGuard reacted to that error by calling signOut({redirect: false}),
# which triggered another session fetch. Nothing bounded it.
#
# No test caught this. Every page rendered correctly, every element was present,
# and no console error appeared - the damage was in the volume of requests, which
# nothing asserted on.
#
# Measured on a healthy dev, over a 12s window: 4 auth calls on the homepage,
# 1 on /datasets. The threshold below sits well above that and orders of
# magnitude below a loop.

import os
import tempfile
import time

import pytest
from selenium import webdriver

from utils.browser_network import count_requests, enable_network_logging

pytestmark = [pytest.mark.smoke, pytest.mark.regression]

BASE_URL = os.getenv("HOME_URL_DEV", "https://dev.civicdataspace.in")

# Healthy is 1-4. A loop produces hundreds to thousands. Anything in between is
# worth a human look, which is what this number is chosen to trigger.
MAX_AUTH_REQUESTS = 15

SETTLE_SECONDS = 12


@pytest.fixture
def network_driver():
    """A Chrome driver with the performance log enabled.

    Separate from the shared `driver` fixture on purpose: that one enables only
    the browser console log, and turning on performance logging for every test
    in the suite would add log volume that nothing else reads.
    """
    opts = webdriver.ChromeOptions()
    for flag in (
        "--headless=new",
        "--no-sandbox",
        "--disable-gpu",
        "--disable-dev-shm-usage",
        "--disable-extensions",
        "--window-size=1920,1080",
    ):
        opts.add_argument(flag)
    opts.add_argument(f"--user-data-dir={tempfile.mkdtemp(prefix='chrome-net-')}")
    enable_network_logging(opts)

    driver = webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(60)
    yield driver
    driver.quit()


@pytest.mark.parametrize("path", ["/", "/datasets"])
def test_page_load_does_not_loop_on_auth_requests(network_driver, path):
    """A page load must not issue a runaway number of NextAuth requests."""
    network_driver.get(f"{BASE_URL}{path}")
    # Deliberately generous: the loop was fastest right after load, so a short
    # window would miss it. This is long enough for a broken build to give itself
    # away.
    time.sleep(SETTLE_SECONDS)

    counts = count_requests(network_driver, "/api/auth/")
    total = sum(counts.values())

    assert total <= MAX_AUTH_REQUESTS, (
        f"{path} issued {total} /api/auth/ requests in {SETTLE_SECONDS}s "
        f"(limit {MAX_AUTH_REQUESTS}): {dict(counts)}. This is the NextAuth "
        "signout loop: SessionGuard signs out on RefreshAccessTokenError, the "
        "session refetches, the error is still there, and it signs out again. "
        "Left running it exhausts the backend's per-IP rate limit and returns "
        "429 to every user behind the same address."
    )


@pytest.mark.parametrize("path", ["/", "/datasets"])
def test_page_load_does_not_repeatedly_sign_out(network_driver, path):
    """Signing out is never part of loading a page anonymously.

    Split from the count above because it fails for a specific, unambiguous
    reason. A raised threshold could mask the count assertion; this one cannot -
    an anonymous page load has no session to end, so any signout at all is the
    bug.
    """
    network_driver.get(f"{BASE_URL}{path}")
    time.sleep(SETTLE_SECONDS)

    counts = count_requests(network_driver, "/api/auth/")
    signouts = counts.get("signout", 0)

    assert signouts == 0, (
        f"{path} issued {signouts} signout request(s) during an anonymous page "
        f"load: {dict(counts)}. Nothing should be signing out here."
    )
