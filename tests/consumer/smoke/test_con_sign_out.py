# tests/consumer/smoke/test_con_sign_out.py
#
# DataSpaceFrontend#552: after Log Out the session is gone for good. Before it,
# a dead session's cookie was saved again, so the profile chip came back on the
# next page, and overlapping refreshes could loop on /api/auth (see
# test_con_auth_request_volume.py).

import time

import pytest

from pages.home_page import HomePage
from utils.browser_network import count_requests

pytestmark = [pytest.mark.smoke, pytest.mark.real_login, pytest.mark.deployed_pr("DataSpaceFrontend#552", site="HOME_URL_DEV")]

MAX_AUTH_REQUESTS = 15  # healthy is a handful per page; a loop is hundreds
SETTLE_SECONDS = 5


def test_con_sign_out_stays_signed_out(logged_in_provider, driver, base_url):
    """
    Test Case ID: test_con_sign_out_stays_signed_out
    Steps:
      1. Sign in (a real Keycloak login) and open the homepage
      2. Log Out from the profile menu
      3. Reload the homepage and /datasets: no profile chip, LOGIN / SIGN UP shown,
         no session cookie, and only a handful of /api/auth requests
      4. /dashboard asks for a sign-in instead of opening
    """
    home = HomePage(driver, base_url)
    driver.get(base_url)
    home.sign_out()
    count_requests(driver, "/api/auth/")  # drain the log up to the sign-out

    for path in ("/", "/datasets"):
        driver.get(base_url.rstrip("/") + path)
        time.sleep(SETTLE_SECONDS)
        auth_calls = sum(count_requests(driver, "/api/auth/").values())
        assert not home.signed_in_chip_shown(), f"{path}: the profile chip is back after Log Out"
        assert not any("session-token" in c["name"] for c in driver.get_cookies()), f"{path}: the session cookie survived Log Out"
        assert auth_calls <= MAX_AUTH_REQUESTS, f"{path}: {auth_calls} /api/auth requests in {SETTLE_SECONDS}s after Log Out"

    driver.get(base_url.rstrip("/") + "/dashboard")
    home.wait_with_timeout(20).until(lambda d: "/dashboard" not in d.current_url,
                                     message="/dashboard opened after Log Out instead of asking for a sign-in")
