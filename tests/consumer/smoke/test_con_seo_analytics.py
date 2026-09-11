# tests/consumer/smoke/test_con_seo_analytics.py
#
# Google Analytics smoke checks.
#
# Prod (civicdataspace.in) must have GA fully wired up. Regression coverage:
# a prior bug had the GA measurement ID GitHub Actions secret stored *with*
# literal quotes ('G-XXXXXXXX'), which got baked into the built JS bundle as
# id='G-XXXXXXXX' and threw a real browser SyntaxError when Next.js tried to
# inject the inline gtag-init script.
#
# Dev (dev.civicdataspace.in) must have GA completely absent by design —
# NEXT_PUBLIC_GA_ID is deliberately unset for the dev build so QA/dev traffic
# doesn't pollute production analytics data. This is itself a regression
# test: if NEXT_PUBLIC_GA_ID is ever re-added to dev's GitHub Actions
# environment, this should catch it before it ships.

import os
import re
import time
from urllib.parse import urlparse

import pytest

PROD_URL = os.getenv("HOME_URL_PROD")
DEV_URL = os.getenv("HOME_URL_DEV")

GA_ID_RE = re.compile(r"^G-[A-Z0-9]+$")
QUOTE_ARTIFACTS = ("'", "%27", '"', "%22")

# Time to let gtag.js load + the inline config script run after page load.
GA_SETTLE_SECONDS = 3


def _ga_script_src(driver):
    scripts = driver.find_elements("css selector", 'script[src*="googletagmanager"]')
    return scripts[0].get_attribute("src") if scripts else None


def _syntax_errors_in_console(driver):
    """
    Console entries mentioning SyntaxError.

    Chrome is configured with `goog:loggingPrefs {"browser": "ALL"}` (conftest.py),
    so `get_log("browser")` must work there — a failure means that capability was
    dropped, and swallowing it into a skip would silently retire this check. Firefox
    genuinely does not implement the endpoint, so it keeps the skip.
    """
    try:
        logs = driver.get_log("browser")
    except Exception as exc:
        browser = (driver.capabilities or {}).get("browserName", "").lower()
        if browser and browser != "chrome":
            pytest.skip(f"{browser} does not expose browser console logs: {exc}")
        raise AssertionError(
            f"Chrome console logs unavailable despite goog:loggingPrefs being set in "
            f"conftest.py — the capability was likely dropped: {exc}"
        ) from exc
    return [entry for entry in logs if "SyntaxError" in entry.get("message", "")]


# ─── Prod: GA must be fully working ────────────────────────────────────────────

@pytest.mark.smoke
@pytest.mark.seo
def test_prod_ga_script_tag_has_clean_measurement_id(driver):
    """Prod must load the gtag.js script with a clean G-XXXX id (no stray quotes)."""
    if not PROD_URL:
        pytest.skip("HOME_URL_PROD not set")
    driver.get(PROD_URL)
    time.sleep(GA_SETTLE_SECONDS)

    src = _ga_script_src(driver)
    assert src, "No googletagmanager script tag found on prod homepage"

    match = re.search(r"[?&]id=([^&]+)", src)
    assert match, f"Could not find id= param in GA script src: {src}"
    ga_id = match.group(1)

    for artifact in QUOTE_ARTIFACTS:
        assert artifact not in ga_id, f"GA id contains stray quote artifact {artifact!r}: {ga_id}"
    assert GA_ID_RE.match(ga_id), f"GA id does not match ^G-[A-Z0-9]+$: {ga_id}"


@pytest.mark.smoke
@pytest.mark.seo
def test_prod_gtag_is_a_function(driver):
    """window.gtag must be defined as a function on prod after the page settles."""
    if not PROD_URL:
        pytest.skip("HOME_URL_PROD not set")
    driver.get(PROD_URL)
    time.sleep(GA_SETTLE_SECONDS)

    gtag_type = driver.execute_script("return typeof window.gtag;")
    assert gtag_type == "function", f"window.gtag is {gtag_type}, expected 'function'"


@pytest.mark.smoke
@pytest.mark.seo
def test_prod_no_syntax_errors_in_console(driver):
    """Prod page load must not throw a SyntaxError (regression: quoted GA id secret)."""
    if not PROD_URL:
        pytest.skip("HOME_URL_PROD not set")
    driver.get(PROD_URL)
    time.sleep(GA_SETTLE_SECONDS)

    errors = _syntax_errors_in_console(driver)
    assert not errors, f"SyntaxError(s) found in browser console: {errors}"


@pytest.mark.smoke
@pytest.mark.seo
def test_prod_data_layer_has_config_call(driver):
    """window.dataLayer must be a non-empty array containing at least one 'config' call."""
    if not PROD_URL:
        pytest.skip("HOME_URL_PROD not set")
    driver.get(PROD_URL)
    time.sleep(GA_SETTLE_SECONDS)

    data_layer = driver.execute_script("return window.dataLayer;")
    assert data_layer, "window.dataLayer is empty/undefined"
    assert isinstance(data_layer, list) and len(data_layer) > 0, (
        f"Expected a non-empty dataLayer array, got: {data_layer!r}"
    )
    has_config_call = any(
        isinstance(entry, list) and "config" in entry for entry in data_layer
    )
    assert has_config_call, f"No 'config' call found in dataLayer: {data_layer}"


# ─── Dev: GA must be completely absent ─────────────────────────────────────────

def _require_dev_target():
    # HOME_URL_DEV is whichever site the suite targets; prod deploys point it at prod.
    host = urlparse(DEV_URL or "").hostname or ""
    if not host.startswith("dev."):
        pytest.skip(f"HOME_URL_DEV targets '{host or 'nothing'}', not a dev host; GA-absent checks apply to dev only")


@pytest.mark.smoke
@pytest.mark.seo
def test_dev_ga_script_tag_absent(driver):
    """Dev must not load any googletagmanager script (GA intentionally disabled)."""
    _require_dev_target()
    driver.get(DEV_URL)
    time.sleep(GA_SETTLE_SECONDS)

    src = _ga_script_src(driver)
    assert src is None, f"Found googletagmanager script on dev (GA should be disabled): {src}"


@pytest.mark.smoke
@pytest.mark.seo
def test_dev_gtag_is_undefined(driver):
    """window.gtag must be undefined on dev (GA intentionally disabled)."""
    _require_dev_target()
    driver.get(DEV_URL)
    time.sleep(GA_SETTLE_SECONDS)

    gtag_type = driver.execute_script("return typeof window.gtag;")
    assert gtag_type == "undefined", f"window.gtag is {gtag_type}, expected 'undefined' on dev"
