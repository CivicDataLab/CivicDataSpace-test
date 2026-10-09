"""
Fixtures and page inventory for the accessibility suite.

The root conftest.py supplies `driver`, `base_url`, `test_credentials` and the
provider login fixtures; this file only adds what the a11y tests need on top.
"""

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
