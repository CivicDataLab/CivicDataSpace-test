"""
Fixtures and page inventory for the accessibility suite.

The root conftest.py supplies `driver`, `base_url`, `test_credentials` and the
provider login fixtures; this file only adds what the a11y tests need on top.
"""

import os

import pytest

from utils import a11y

# ─── Page inventory ────────────────────────────────────────────────────────────
#
# Public routes verified live against dev.civicdataspace.in. Kept as (id, path)
# so parametrised test ids read as the page name rather than "page0/page1".

PUBLIC_PAGES = [
    ("home", "/"),
    ("datasets", "/datasets"),
    ("sectors", "/sectors"),
    ("usecases", "/usecases"),
    ("collaboratives", "/collaboratives"),
    ("publishers", "/publishers"),
    ("about-us", "/about-us"),
]

# Provider sections live under /dashboard/<entityType>/<slug>/<path>. The slug
# differs per account, so tests derive the base from the logged-in URL.
PROVIDER_SECTIONS = [
    ("datasets", "dataset"),
    ("usecases", "usecases"),
    ("charts", "charts"),
    ("profile", "profile"),
]


@pytest.fixture
def goto(driver, base_url):
    """Navigate to a public path and wait for the app shell to settle.

    Next.js streams content in, so a bare driver.get() can hand back a page
    whose main region is still a loading placeholder — scanning that produces
    meaningless axe results.
    """
    from selenium.webdriver.support.ui import WebDriverWait

    def _goto(path: str):
        url = base_url.rstrip("/") + path
        driver.get(url)
        try:
            WebDriverWait(driver, 30).until(
                lambda d: d.execute_script("return document.readyState") == "complete"
            )
            WebDriverWait(driver, 30).until(
                lambda d: not d.execute_script(
                    "return /^\\s*Loading\\s*$/i.test((document.body.innerText||'').trim())"
                )
            )
        except Exception:
            # A slow/degraded backend shouldn't turn into a confusing timeout
            # deep inside a scan; let the test assert on what actually rendered.
            pass
        if path == "/":
            # The home page's stat cards (Datasets, Use cases, ...) render about a second after
            # load, from an API call. Scanning before they exist passed locally; scanning after
            # they exist fails contrast in CI. Always scan the full page.
            try:
                WebDriverWait(driver, 15).until(
                    lambda d: d.execute_script("return !!document.querySelector('a[data-tour=\"datasets-link\"]')")
                )
            except Exception:
                pass
        return url

    return _goto


@pytest.fixture(scope="session", autouse=True)
def _reset_a11y_findings(request):
    """Clear stale findings once per session, on the controller only.

    Under xdist each worker also runs session fixtures; if every worker cleared
    the directory they would delete each other's findings mid-run.
    """
    if not hasattr(request.config, "workerinput"):
        a11y.clear_findings()
    return None


# ─── Known failures ────────────────────────────────────────────────────────────
#
# Real accessibility defects on dev, each tracked by an issue. They run as strict
# xfails, so CI stays green while they exist and goes red the moment one is fixed
# (an unexpected pass): delete its entry then. A new failure not listed here fails.

FRONTEND = "DataSpaceFrontend"
KNOWN_FAILURES = {
    ("test_skip_to_content_mechanism_exists", p): f"{FRONTEND}#555: no skip-to-content link"
    for p in ("home", "datasets", "about-us")
}
KNOWN_FAILURES.update({
    (test, p): f"{FRONTEND}#556: text below the 4.5:1 contrast minimum"
    for test in ("test_public_page_has_no_critical_axe_violations", "test_text_meets_contrast_minimum")
    for p in ("home", "datasets", "sectors", "usecases", "collaboratives")
})
# Intermittent: the header row's width depends on when the Bhashini language widget
# finishes loading, so the same page overflows on one run and not the next (home failed in
# CI with datasets passing; the reverse happened locally). Not strict, or the passes go red.
# The profile section's unlabelled file input and low-contrast "Delete account" failed on every
# local run but passed once in CI (XPASS, run 45175986731), so it is not strict either.
INTERMITTENT_FAILURES = {
    ("test_text_resizes_to_200_percent", p): f"{FRONTEND}#557: header row overflows at 200% text, depending on load timing"
    for p in ("home", "datasets", "about-us")
}
INTERMITTENT_FAILURES[("test_provider_section_has_no_critical_axe_violations", "profile")] = (
    "DataSpace#218: unlabelled file input and low-contrast Delete account on Profile")
KNOWN_FAILURES.update({
    ("test_provider_section_has_no_critical_axe_violations", p): "DataSpace#218: invalid ARIA on the provider routes"
    for p in ("datasets", "usecases", "charts")
})


def pytest_collection_modifyitems(items):
    here = os.path.dirname(__file__)
    for item in items:
        if not str(item.fspath).startswith(here):
            continue
        callspec = getattr(item, "callspec", None)
        key = (item.originalname, callspec.id if callspec else None)
        if key in KNOWN_FAILURES:
            item.add_marker(pytest.mark.xfail(reason=KNOWN_FAILURES[key], strict=True, raises=AssertionError))
        elif key in INTERMITTENT_FAILURES:
            item.add_marker(pytest.mark.xfail(reason=INTERMITTENT_FAILURES[key], strict=False, raises=AssertionError))
